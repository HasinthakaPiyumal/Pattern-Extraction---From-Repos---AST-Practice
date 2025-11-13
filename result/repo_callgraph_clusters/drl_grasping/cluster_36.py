# Cluster 36

class StoreDict(argparse.Action):
    """
    Custom argparse action for storing dict.

    In: args1:0.0 args2:"dict(a=1)"
    Out: {'args1': 0.0, arg2: dict(a=1)}
    """

    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        self._nargs = nargs
        super(StoreDict, self).__init__(option_strings, dest, nargs=nargs, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        arg_dict = {}
        if hasattr(namespace, self.dest):
            current_arg = getattr(namespace, self.dest)
            if isinstance(current_arg, Dict):
                arg_dict = getattr(namespace, self.dest)
        for arguments in values:
            if not arguments:
                continue
            key = arguments.split(':')[0]
            value = ':'.join(arguments.split(':')[1:])
            arg_dict[key] = eval(value)
        setattr(namespace, self.dest, arg_dict)

def __init__(self, option_strings, dest, nargs=None, **kwargs):
    self._nargs = nargs
    super(StoreDict, self).__init__(option_strings, dest, nargs=nargs, **kwargs)

class TrialEvalCallback(EvalCallback):
    """
    Callback used for evaluating and reporting a trial.
    """

    def __init__(self, eval_env: VecEnv, trial: optuna.Trial, n_eval_episodes: int=5, eval_freq: int=10000, deterministic: bool=True, verbose: int=0, best_model_save_path: Optional[str]=None, log_path: Optional[str]=None):
        super(TrialEvalCallback, self).__init__(eval_env=eval_env, n_eval_episodes=n_eval_episodes, eval_freq=eval_freq, deterministic=deterministic, verbose=verbose, best_model_save_path=best_model_save_path, log_path=log_path)
        self.trial = trial
        self.eval_idx = 0
        self.is_pruned = False

    def _on_step(self) -> bool:
        if self.eval_freq > 0 and self.n_calls % self.eval_freq == 0:
            print('Evaluating trial')
            super(TrialEvalCallback, self)._on_step()
            self.eval_idx += 1
            self.trial.report(self.last_mean_reward, self.eval_idx)
            if self.trial.should_prune():
                self.is_pruned = True
                return False
        return True

def __init__(self, eval_env: VecEnv, trial: optuna.Trial, n_eval_episodes: int=5, eval_freq: int=10000, deterministic: bool=True, verbose: int=0, best_model_save_path: Optional[str]=None, log_path: Optional[str]=None):
    super(TrialEvalCallback, self).__init__(eval_env=eval_env, n_eval_episodes=n_eval_episodes, eval_freq=eval_freq, deterministic=deterministic, verbose=verbose, best_model_save_path=best_model_save_path, log_path=log_path)
    self.trial = trial
    self.eval_idx = 0
    self.is_pruned = False

class ParallelTrainCallback(BaseCallback):
    """
    Callback to explore (collect experience) and train (do gradient steps)
    at the same time using two separate threads.
    Normally used with off-policy algorithms and `train_freq=(1, "episode")`.

    - blocking mode: wait for the model to finish updating the policy before collecting new experience
        at the end of a rollout
    - force sync mode: stop training to update to the latest policy for collecting
        new experience

    :param gradient_steps: Number of gradient steps to do before
        sending the new policy
    :param verbose: Verbosity level
    :param sleep_time: Limit the fps in the thread collecting experience.
    """

    def __init__(self, gradient_steps: int=100, verbose: int=0, sleep_time: float=0.0):
        super(ParallelTrainCallback, self).__init__(verbose)
        self.batch_size = 0
        self._model_ready = True
        self._model = None
        self.gradient_steps = gradient_steps
        self.process = None
        self.model_class = None
        self.sleep_time = sleep_time

    def _init_callback(self) -> None:
        temp_file = tempfile.TemporaryFile()
        if os.name == 'nt':
            temp_file = os.path.join('logs', 'model_tmp.zip')
        self.model.save(temp_file)
        for model_class in [SAC, TQC]:
            if isinstance(self.model, model_class):
                self.model_class = model_class
                break
        assert self.model_class is not None, f'{self.model} is not supported for parallel training'
        self._model = self.model_class.load(temp_file)
        self.batch_size = self._model.batch_size

        def patch_train(function):

            @wraps(function)
            def wrapper(*args, **kwargs):
                return
            return wrapper
        self._model.set_logger(self.model.logger)
        self.model.train = patch_train(self.model.train)

        def patch_save(function):

            @wraps(function)
            def wrapper(*args, **kwargs):
                return self._model.save(*args, **kwargs)
            return wrapper
        self.model.save = patch_save(self.model.save)

    def train(self) -> None:
        self._model_ready = False
        self.process = Thread(target=self._train_thread, daemon=True)
        self.process.start()

    def _train_thread(self) -> None:
        self._model.train(gradient_steps=self.gradient_steps, batch_size=self.batch_size)
        self._model_ready = True

    def _on_step(self) -> bool:
        if self.sleep_time > 0:
            time.sleep(self.sleep_time)
        return True

    def _on_rollout_end(self) -> None:
        if self._model_ready:
            self._model.replay_buffer = deepcopy(self.model.replay_buffer)
            self.model.set_parameters(deepcopy(self._model.get_parameters()))
            self.model.actor = self.model.policy.actor
            if self.num_timesteps >= self._model.learning_starts:
                self.train()

    def _on_training_end(self) -> None:
        if self.process is not None:
            if self.verbose > 0:
                print('Waiting for training thread to terminate')
            self.process.join()

def __init__(self, gradient_steps: int=100, verbose: int=0, sleep_time: float=0.0):
    super(ParallelTrainCallback, self).__init__(verbose)
    self.batch_size = 0
    self._model_ready = True
    self._model = None
    self.gradient_steps = gradient_steps
    self.process = None
    self.model_class = None
    self.sleep_time = sleep_time

class SaveVecNormalizeCallback(BaseCallback):
    """
    Callback for saving a VecNormalize wrapper every ``save_freq`` steps

    :param save_freq: (int)
    :param save_path: (str) Path to the folder where ``VecNormalize`` will be saved, as ``vecnormalize.pkl``
    :param name_prefix: (str) Common prefix to the saved ``VecNormalize``, if None (default)
        only one file will be kept.
    """

    def __init__(self, save_freq: int, save_path: str, name_prefix: Optional[str]=None, verbose: int=0):
        super(SaveVecNormalizeCallback, self).__init__(verbose)
        self.save_freq = save_freq
        self.save_path = save_path
        self.name_prefix = name_prefix

    def _init_callback(self) -> None:
        if self.save_path is not None:
            os.makedirs(self.save_path, exist_ok=True)

    def _on_step(self) -> bool:
        if self.n_calls % self.save_freq == 0:
            if self.name_prefix is not None:
                path = os.path.join(self.save_path, f'{self.name_prefix}_{self.num_timesteps}_steps.pkl')
            else:
                path = os.path.join(self.save_path, 'vecnormalize.pkl')
            if self.model.get_vec_normalize_env() is not None:
                self.model.get_vec_normalize_env().save(path)
                if self.verbose > 1:
                    print(f'Saving VecNormalize to {path}')
        return True

def __init__(self, save_freq: int, save_path: str, name_prefix: Optional[str]=None, verbose: int=0):
    super(SaveVecNormalizeCallback, self).__init__(verbose)
    self.save_freq = save_freq
    self.save_path = save_path
    self.name_prefix = name_prefix

class CheckpointCallbackWithReplayBuffer(CheckpointCallback):
    """
    Callback for saving a model every ``save_freq`` steps
    :param save_freq:
    :param save_path: Path to the folder where the model will be saved.
    :param name_prefix: Common prefix to the saved models
    :param save_replay_buffer: If enabled, save replay buffer together with model (if supported by algorithm).
    :param verbose:
    """

    def __init__(self, save_freq: int, save_path: str, name_prefix: str='rl_model', save_replay_buffer: bool=False, verbose: int=0):
        super(CheckpointCallbackWithReplayBuffer, self).__init__(save_freq, save_path, name_prefix, verbose)
        self.save_replay_buffer = save_replay_buffer

    def _on_step(self) -> bool:
        if self.n_calls % self.save_freq == 0:
            path = os.path.join(self.save_path, f'{self.name_prefix}_{self.num_timesteps}_steps')
            self.model.save(path)
            if self.verbose > 0:
                print(f'Saving model checkpoint to {path}')
            if self.save_replay_buffer:
                path_replay_buffer = os.path.join(self.save_path, 'replay_buffer.pkl')
                self.model.save_replay_buffer(path_replay_buffer)
                if self.verbose > 0:
                    print(f'Saving model checkpoint to {path_replay_buffer}')
        return True

def __init__(self, save_freq: int, save_path: str, name_prefix: str='rl_model', save_replay_buffer: bool=False, verbose: int=0):
    super(CheckpointCallbackWithReplayBuffer, self).__init__(save_freq, save_path, name_prefix, verbose)
    self.save_replay_buffer = save_replay_buffer

class CurriculumLoggerCallback(BaseCallback):
    """
    Custom callback for logging curriculum values.
    """

    def __init__(self, verbose=0):
        super(CurriculumLoggerCallback, self).__init__(verbose)

    def _on_step(self) -> bool:
        for infos in self.locals['infos']:
            for info_key, info_value in infos.items():
                if not (info_key.startswith('curriculum') and info_key.count('__mean_step__')):
                    continue
                self.logger.record_mean(key=info_key.replace('__mean_step__', ''), value=info_value)
        return True

    def _on_rollout_end(self) -> None:
        for infos in self.locals['infos']:
            for info_key, info_value in infos.items():
                if not info_key.startswith('curriculum'):
                    continue
                if info_key.count('__mean_step__'):
                    continue
                if info_key.count('__mean_episode__'):
                    self.logger.record_mean(key=info_key.replace('__mean_episode__', ''), value=info_value)
                else:
                    if isinstance(info_value, str):
                        exclude = 'tensorboard'
                    else:
                        exclude = None
                    self.logger.record(key=info_key, value=info_value, exclude=exclude)

def __init__(self, verbose=0):
    super(CurriculumLoggerCallback, self).__init__(verbose)

class DoneOnSuccessWrapper(gym.Wrapper):
    """
    Reset on success and offsets the reward.
    Useful for GoalEnv.
    """

    def __init__(self, env: gym.Env, reward_offset: float=0.0, n_successes: int=1):
        super(DoneOnSuccessWrapper, self).__init__(env)
        self.reward_offset = reward_offset
        self.n_successes = n_successes
        self.current_successes = 0

    def reset(self):
        self.current_successes = 0
        return self.env.reset()

    def step(self, action):
        obs, reward, done, info = self.env.step(action)
        if info.get('is_success', False):
            self.current_successes += 1
        else:
            self.current_successes = 0
        done = done or self.current_successes >= self.n_successes
        reward += self.reward_offset
        return (obs, reward, done, info)

    def compute_reward(self, achieved_goal, desired_goal, info):
        reward = self.env.compute_reward(achieved_goal, desired_goal, info)
        return reward + self.reward_offset

def __init__(self, env: gym.Env, reward_offset: float=0.0, n_successes: int=1):
    super(DoneOnSuccessWrapper, self).__init__(env)
    self.reward_offset = reward_offset
    self.n_successes = n_successes
    self.current_successes = 0

class ActionNoiseWrapper(gym.Wrapper):
    """
    Add gaussian noise to the action (without telling the agent),
    to test the robustness of the control.

    :param env: (gym.Env)
    :param noise_std: (float) Standard deviation of the noise
    """

    def __init__(self, env, noise_std=0.1):
        super(ActionNoiseWrapper, self).__init__(env)
        self.noise_std = noise_std

    def step(self, action):
        noise = np.random.normal(np.zeros_like(action), np.ones_like(action) * self.noise_std)
        noisy_action = action + noise
        return self.env.step(noisy_action)

def __init__(self, env, noise_std=0.1):
    super(ActionNoiseWrapper, self).__init__(env)
    self.noise_std = noise_std

class LowPassFilterWrapper(gym.Wrapper):
    """
    Butterworth-Lowpass

    :param env: (gym.Env)
    :param freq: Filter corner frequency.
    :param df: Sampling rate in Hz.
    """

    def __init__(self, env, freq=5.0, df=25.0):
        super(LowPassFilterWrapper, self).__init__(env)
        self.freq = freq
        self.df = df
        self.signal = []

    def reset(self):
        self.signal = []
        return self.env.reset()

    def step(self, action):
        self.signal.append(action)
        filtered = np.zeros_like(action)
        for i in range(self.action_space.shape[0]):
            smoothed_action = lowpass(np.array(self.signal)[:, i], freq=self.freq, df=self.df)
            filtered[i] = smoothed_action[-1]
        return self.env.step(filtered)

def __init__(self, env, freq=5.0, df=25.0):
    super(LowPassFilterWrapper, self).__init__(env)
    self.freq = freq
    self.df = df
    self.signal = []

class ActionSmoothingWrapper(gym.Wrapper):
    """
    Smooth the action using exponential moving average.

    :param env: (gym.Env)
    :param smoothing_coef: (float) Smoothing coefficient (0 no smoothing, 1 very smooth)
    """

    def __init__(self, env, smoothing_coef: float=0.0):
        super(ActionSmoothingWrapper, self).__init__(env)
        self.smoothing_coef = smoothing_coef
        self.smoothed_action = None

    def reset(self):
        self.smoothed_action = None
        return self.env.reset()

    def step(self, action):
        if self.smoothed_action is None:
            self.smoothed_action = np.zeros_like(action)
        self.smoothed_action = self.smoothing_coef * self.smoothed_action + (1 - self.smoothing_coef) * action
        return self.env.step(self.smoothed_action)

def __init__(self, env, smoothing_coef: float=0.0):
    super(ActionSmoothingWrapper, self).__init__(env)
    self.smoothing_coef = smoothing_coef
    self.smoothed_action = None

class DelayedRewardWrapper(gym.Wrapper):
    """
    Delay the reward by `delay` steps, it makes the task harder but more realistic.
    The reward is accumulated during those steps.

    :param env: (gym.Env)
    :param delay: (int) Number of steps the reward should be delayed.
    """

    def __init__(self, env, delay=10):
        super(DelayedRewardWrapper, self).__init__(env)
        self.delay = delay
        self.current_step = 0
        self.accumulated_reward = 0.0

    def reset(self):
        self.current_step = 0
        self.accumulated_reward = 0.0
        return self.env.reset()

    def step(self, action):
        obs, reward, done, info = self.env.step(action)
        self.accumulated_reward += reward
        self.current_step += 1
        if self.current_step % self.delay == 0 or done:
            reward = self.accumulated_reward
            self.accumulated_reward = 0.0
        else:
            reward = 0.0
        return (obs, reward, done, info)

def __init__(self, env, delay=10):
    super(DelayedRewardWrapper, self).__init__(env)
    self.delay = delay
    self.current_step = 0
    self.accumulated_reward = 0.0

class HistoryWrapper(gym.Wrapper):
    """
    Stack past observations and actions to give an history to the agent.

    :param env: (gym.Env)
    :param horizon: (int) Number of steps to keep in the history.
    """

    def __init__(self, env: gym.Env, horizon: int=5):
        assert isinstance(env.observation_space, gym.spaces.Box)
        wrapped_obs_space = env.observation_space
        wrapped_action_space = env.action_space
        low_obs = np.repeat(wrapped_obs_space.low, horizon, axis=-1)
        high_obs = np.repeat(wrapped_obs_space.high, horizon, axis=-1)
        low_action = np.repeat(wrapped_action_space.low, horizon, axis=-1)
        high_action = np.repeat(wrapped_action_space.high, horizon, axis=-1)
        low = np.concatenate((low_obs, low_action))
        high = np.concatenate((high_obs, high_action))
        env.observation_space = gym.spaces.Box(low=low, high=high, dtype=wrapped_obs_space.dtype)
        super(HistoryWrapper, self).__init__(env)
        self.horizon = horizon
        self.low_action, self.high_action = (low_action, high_action)
        self.low_obs, self.high_obs = (low_obs, high_obs)
        self.low, self.high = (low, high)
        self.obs_history = np.zeros(low_obs.shape, low_obs.dtype)
        self.action_history = np.zeros(low_action.shape, low_action.dtype)

    def _create_obs_from_history(self):
        return np.concatenate((self.obs_history, self.action_history))

    def reset(self):
        self.obs_history[...] = 0
        self.action_history[...] = 0
        obs = self.env.reset()
        self.obs_history[..., -obs.shape[-1]:] = obs
        return self._create_obs_from_history()

    def step(self, action):
        obs, reward, done, info = self.env.step(action)
        last_ax_size = obs.shape[-1]
        self.obs_history = np.roll(self.obs_history, shift=-last_ax_size, axis=-1)
        self.obs_history[..., -obs.shape[-1]:] = obs
        self.action_history = np.roll(self.action_history, shift=-action.shape[-1], axis=-1)
        self.action_history[..., -action.shape[-1]:] = action
        return (self._create_obs_from_history(), reward, done, info)

def __init__(self, env: gym.Env, horizon: int=5):
    assert isinstance(env.observation_space, gym.spaces.Box)
    wrapped_obs_space = env.observation_space
    wrapped_action_space = env.action_space
    low_obs = np.repeat(wrapped_obs_space.low, horizon, axis=-1)
    high_obs = np.repeat(wrapped_obs_space.high, horizon, axis=-1)
    low_action = np.repeat(wrapped_action_space.low, horizon, axis=-1)
    high_action = np.repeat(wrapped_action_space.high, horizon, axis=-1)
    low = np.concatenate((low_obs, low_action))
    high = np.concatenate((high_obs, high_action))
    env.observation_space = gym.spaces.Box(low=low, high=high, dtype=wrapped_obs_space.dtype)
    super(HistoryWrapper, self).__init__(env)
    self.horizon = horizon
    self.low_action, self.high_action = (low_action, high_action)
    self.low_obs, self.high_obs = (low_obs, high_obs)
    self.low, self.high = (low, high)
    self.obs_history = np.zeros(low_obs.shape, low_obs.dtype)
    self.action_history = np.zeros(low_action.shape, low_action.dtype)

class HistoryWrapperObsDict(gym.Wrapper):
    """
    History Wrapper for dict observation.

    :param env: (gym.Env)
    :param horizon: (int) Number of steps to keep in the history.
    """

    def __init__(self, env, horizon=5):
        assert isinstance(env.observation_space.spaces['observation'], gym.spaces.Box)
        wrapped_obs_space = env.observation_space.spaces['observation']
        wrapped_action_space = env.action_space
        low_obs = np.repeat(wrapped_obs_space.low, horizon, axis=-1)
        high_obs = np.repeat(wrapped_obs_space.high, horizon, axis=-1)
        low_action = np.repeat(wrapped_action_space.low, horizon, axis=-1)
        high_action = np.repeat(wrapped_action_space.high, horizon, axis=-1)
        low = np.concatenate((low_obs, low_action))
        high = np.concatenate((high_obs, high_action))
        env.observation_space.spaces['observation'] = gym.spaces.Box(low=low, high=high, dtype=wrapped_obs_space.dtype)
        super(HistoryWrapperObsDict, self).__init__(env)
        self.horizon = horizon
        self.low_action, self.high_action = (low_action, high_action)
        self.low_obs, self.high_obs = (low_obs, high_obs)
        self.low, self.high = (low, high)
        self.obs_history = np.zeros(low_obs.shape, low_obs.dtype)
        self.action_history = np.zeros(low_action.shape, low_action.dtype)

    def _create_obs_from_history(self):
        return np.concatenate((self.obs_history, self.action_history))

    def reset(self):
        self.obs_history[...] = 0
        self.action_history[...] = 0
        obs_dict = self.env.reset()
        obs = obs_dict['observation']
        self.obs_history[..., -obs.shape[-1]:] = obs
        obs_dict['observation'] = self._create_obs_from_history()
        return obs_dict

    def step(self, action):
        obs_dict, reward, done, info = self.env.step(action)
        obs = obs_dict['observation']
        last_ax_size = obs.shape[-1]
        self.obs_history = np.roll(self.obs_history, shift=-last_ax_size, axis=-1)
        self.obs_history[..., -obs.shape[-1]:] = obs
        self.action_history = np.roll(self.action_history, shift=-action.shape[-1], axis=-1)
        self.action_history[..., -action.shape[-1]:] = action
        obs_dict['observation'] = self._create_obs_from_history()
        return (obs_dict, reward, done, info)

def __init__(self, env, horizon=5):
    assert isinstance(env.observation_space.spaces['observation'], gym.spaces.Box)
    wrapped_obs_space = env.observation_space.spaces['observation']
    wrapped_action_space = env.action_space
    low_obs = np.repeat(wrapped_obs_space.low, horizon, axis=-1)
    high_obs = np.repeat(wrapped_obs_space.high, horizon, axis=-1)
    low_action = np.repeat(wrapped_action_space.low, horizon, axis=-1)
    high_action = np.repeat(wrapped_action_space.high, horizon, axis=-1)
    low = np.concatenate((low_obs, low_action))
    high = np.concatenate((high_obs, high_action))
    env.observation_space.spaces['observation'] = gym.spaces.Box(low=low, high=high, dtype=wrapped_obs_space.dtype)
    super(HistoryWrapperObsDict, self).__init__(env)
    self.horizon = horizon
    self.low_action, self.high_action = (low_action, high_action)
    self.low_obs, self.high_obs = (low_obs, high_obs)
    self.low, self.high = (low, high)
    self.obs_history = np.zeros(low_obs.shape, low_obs.dtype)
    self.action_history = np.zeros(low_action.shape, low_action.dtype)

class PlotActionWrapper(gym.Wrapper):
    """
    Wrapper for plotting the taken actions.
    Only works with 1D actions for now.
    Optionally, it can be used to plot the observations too.

    :param env: (gym.Env)
    :param plot_freq: (int) Plot every `plot_freq` episodes
    """

    def __init__(self, env, plot_freq=5):
        super(PlotActionWrapper, self).__init__(env)
        self.plot_freq = plot_freq
        self.current_episode = 0
        self.actions = []

    def reset(self):
        self.current_episode += 1
        if self.current_episode % self.plot_freq == 0:
            self.plot()
            self.actions = []
        obs = self.env.reset()
        self.actions.append([])
        return obs

    def step(self, action):
        obs, reward, done, info = self.env.step(action)
        self.actions[-1].append(action)
        return (obs, reward, done, info)

    def plot(self):
        actions = self.actions
        x = np.arange(sum([len(episode) for episode in actions]))
        plt.figure('Actions')
        plt.title('Actions during exploration', fontsize=14)
        plt.xlabel('Timesteps', fontsize=14)
        plt.ylabel('Action', fontsize=14)
        start = 0
        for i in range(len(self.actions)):
            end = start + len(self.actions[i])
            plt.plot(x[start:end], self.actions[i])
            start = end
        plt.show()

def __init__(self, env, plot_freq=5):
    super(PlotActionWrapper, self).__init__(env)
    self.plot_freq = plot_freq
    self.current_episode = 0
    self.actions = []

class FeatureExtractorFreezeParammetersWrapper(gym.Wrapper):
    """
    Freezes parameters of the feature extractor.
    """

    def __init__(self, env: gym.Env):
        super(FeatureExtractorFreezeParammetersWrapper, self).__init__(env)
        for param in self.feature_extractor.parameters():
            param.requires_grad = False

def __init__(self, env: gym.Env):
    super(FeatureExtractorFreezeParammetersWrapper, self).__init__(env)
    for param in self.feature_extractor.parameters():
        param.requires_grad = False

class ActorWithoutPreprocessing(Actor):
    """
    Actor network (policy) for SAC.
    Overridden to not preprocess observations (unnecessary conversion into float)

    :param observation_space: Obervation space
    :param action_space: Action space
    :param net_arch: Network architecture
    :param features_extractor: Network to extract features
        (a CNN when using images, a nn.Flatten() layer otherwise)
    :param features_dim: Number of features
    :param activation_fn: Activation function
    :param use_sde: Whether to use State Dependent Exploration or not
    :param log_std_init: Initial value for the log standard deviation
    :param full_std: Whether to use (n_features x n_actions) parameters
        for the std instead of only (n_features,) when using gSDE.
    :param sde_net_arch: Network architecture for extracting features
        when using gSDE. If None, the latent features from the policy will be used.
        Pass an empty list to use the states as features.
    :param use_expln: Use ``expln()`` function instead of ``exp()`` when using gSDE to ensure
        a positive standard deviation (cf paper). It allows to keep variance
        above zero and prevent it from growing too fast. In practice, ``exp()`` is usually enough.
    :param clip_mean: Clip the mean output when using gSDE to avoid numerical instability.
    :param normalize_images: Whether to normalize images or not,
         dividing by 255.0 (True by default)
    """

    def __init__(self, observation_space: gym.spaces.Space, action_space: gym.spaces.Space, net_arch: List[int], features_extractor: nn.Module, features_dim: int, activation_fn: Type[nn.Module]=nn.ReLU, use_sde: bool=False, log_std_init: float=-3, full_std: bool=True, sde_net_arch: Optional[List[int]]=None, use_expln: bool=False, clip_mean: float=2.0, normalize_images: bool=True):
        super(ActorWithoutPreprocessing, self).__init__(observation_space=observation_space, action_space=action_space, net_arch=net_arch, features_extractor=features_extractor, features_dim=features_dim, activation_fn=activation_fn, use_sde=use_sde, log_std_init=log_std_init, full_std=full_std, sde_net_arch=sde_net_arch, use_expln=use_expln, clip_mean=clip_mean, normalize_images=normalize_images)

    def extract_features(self, obs: th.Tensor) -> th.Tensor:
        """
        Preprocess the observation if needed and extract features.
        Overridden to skip pre-processing (for some reason it converts tensor to Float)

        :param obs:
        :return:
        """
        assert self.features_extractor is not None, 'No features extractor was set'
        return self.features_extractor(obs)

def __init__(self, observation_space: gym.spaces.Space, action_space: gym.spaces.Space, net_arch: List[int], features_extractor: nn.Module, features_dim: int, activation_fn: Type[nn.Module]=nn.ReLU, use_sde: bool=False, log_std_init: float=-3, full_std: bool=True, sde_net_arch: Optional[List[int]]=None, use_expln: bool=False, clip_mean: float=2.0, normalize_images: bool=True):
    super(ActorWithoutPreprocessing, self).__init__(observation_space=observation_space, action_space=action_space, net_arch=net_arch, features_extractor=features_extractor, features_dim=features_dim, activation_fn=activation_fn, use_sde=use_sde, log_std_init=log_std_init, full_std=full_std, sde_net_arch=sde_net_arch, use_expln=use_expln, clip_mean=clip_mean, normalize_images=normalize_images)

class ContinuousCriticWithoutPreprocessing(ContinuousCritic):
    """
    Critic network(s) for DDPG/SAC/TD3.
    Overridden to not preprocess observations (unnecessary conversion into float)

    It represents the action-state value function (Q-value function).
    Compared to A2C/PPO critics, this one represents the Q-value
    and takes the continuous action as input. It is concatenated with the state
    and then fed to the network which outputs a single value: Q(s, a).
    For more recent algorithms like SAC/TD3, multiple networks
    are created to give different estimates.

    By default, it creates two critic networks used to reduce overestimation
    thanks to clipped Q-learning (cf TD3 paper).

    :param observation_space: Obervation space
    :param action_space: Action space
    :param net_arch: Network architecture
    :param features_extractor: Network to extract features
        (a CNN when using images, a nn.Flatten() layer otherwise)
    :param features_dim: Number of features
    :param activation_fn: Activation function
    :param normalize_images: Whether to normalize images or not,
         dividing by 255.0 (True by default)
    :param n_critics: Number of critic networks to create.
    :param share_features_extractor: Whether the features extractor is shared or not
        between the actor and the critic (this saves computation time)
    """

    def __init__(self, observation_space: gym.spaces.Space, action_space: gym.spaces.Space, net_arch: List[int], features_extractor: nn.Module, features_dim: int, activation_fn: Type[nn.Module]=nn.ReLU, normalize_images: bool=True, n_critics: int=2, share_features_extractor: bool=True):
        super().__init__(observation_space=observation_space, action_space=action_space, net_arch=net_arch, features_extractor=features_extractor, features_dim=features_dim, activation_fn=activation_fn, normalize_images=normalize_images, n_critics=n_critics, share_features_extractor=share_features_extractor)

    def extract_features(self, obs: th.Tensor) -> th.Tensor:
        """
        Preprocess the observation if needed and extract features.
        Overridden to skip pre-processing (for some reason it converts tensor to Float)

        :param obs:
        :return:
        """
        assert self.features_extractor is not None, 'No features extractor was set'
        return self.features_extractor(obs)

def __init__(self, observation_space: gym.spaces.Space, action_space: gym.spaces.Space, net_arch: List[int], features_extractor: nn.Module, features_dim: int, activation_fn: Type[nn.Module]=nn.ReLU, normalize_images: bool=True, n_critics: int=2, share_features_extractor: bool=True):
    super().__init__(observation_space=observation_space, action_space=action_space, net_arch=net_arch, features_extractor=features_extractor, features_dim=features_dim, activation_fn=activation_fn, normalize_images=normalize_images, n_critics=n_critics, share_features_extractor=share_features_extractor)

class OctreeCnnPolicy(SACPolicy):
    """
    Policy class (with both actor and critic) for SAC.

    :param observation_space: Observation space
    :param action_space: Action space
    :param lr_schedule: Learning rate schedule (could be constant)
    :param net_arch: The specification of the policy and value networks.
    :param activation_fn: Activation function
    :param use_sde: Whether to use State Dependent Exploration or not
    :param log_std_init: Initial value for the log standard deviation
    :param sde_net_arch: Network architecture for extracting features
        when using gSDE. If None, the latent features from the policy will be used.
        Pass an empty list to use the states as features.
    :param use_expln: Use ``expln()`` function instead of ``exp()`` when using gSDE to ensure
        a positive standard deviation (cf paper). It allows to keep variance
        above zero and prevent it from growing too fast. In practice, ``exp()`` is usually enough.
    :param clip_mean: Clip the mean output when using gSDE to avoid numerical instability.
    :param features_extractor_class: Features extractor to use (``OctreeCnnFeaturesExtractor``).
    :param normalize_images: Whether to normalize images or not,
         dividing by 255.0 (True by default)
    :param optimizer_class: The optimizer to use,
        ``th.optim.Adam`` by default
    :param optimizer_kwargs: Additional keyword arguments,
        excluding the learning rate, to pass to the optimizer
    :param n_critics: Number of critic networks to create.
    :param share_features_extractor: Whether to share or not the features extractor
        between the actor and the critic (this saves computation time)
    """

    def __init__(self, observation_space: gym.spaces.Space, action_space: gym.spaces.Space, lr_schedule, net_arch: Optional[Union[List[int], Dict[str, List[int]]]]=None, activation_fn: Type[nn.Module]=nn.ReLU, use_sde: bool=False, log_std_init: float=-3, sde_net_arch: Optional[List[int]]=None, use_expln: bool=False, clip_mean: float=2.0, features_extractor_class: Type[BaseFeaturesExtractor]=OctreeCnnFeaturesExtractor, features_extractor_kwargs: Optional[Dict[str, Any]]=None, normalize_images: bool=True, optimizer_class: Type[th.optim.Optimizer]=th.optim.Adam, optimizer_kwargs: Optional[Dict[str, Any]]=None, n_critics: int=2, share_features_extractor: bool=True, separate_networks_for_stacks: bool=True, debug_write_octree: bool=False):
        features_extractor_kwargs.update({'separate_networks_for_stacks': separate_networks_for_stacks})
        super(OctreeCnnPolicy, self).__init__(observation_space, action_space, lr_schedule, net_arch, activation_fn, use_sde, log_std_init, sde_net_arch, use_expln, clip_mean, features_extractor_class, features_extractor_kwargs, normalize_images, optimizer_class, optimizer_kwargs, n_critics, share_features_extractor)
        self._separate_networks_for_stacks = separate_networks_for_stacks
        self._debug_write_octree = debug_write_octree

    def make_actor(self, features_extractor: Optional[BaseFeaturesExtractor]=None) -> Actor:
        actor_kwargs = self._update_features_extractor(self.actor_kwargs, features_extractor)
        return ActorWithoutPreprocessing(**actor_kwargs).to(self.device)

    def make_critic(self, features_extractor: Optional[BaseFeaturesExtractor]=None) -> ContinuousCritic:
        critic_kwargs = self._update_features_extractor(self.critic_kwargs, features_extractor)
        return ContinuousCriticWithoutPreprocessing(**critic_kwargs).to(self.device)

    def predict(self, observation: np.ndarray, state: Optional[np.ndarray]=None, mask: Optional[np.ndarray]=None, deterministic: bool=False) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Overridden to create proper Octree batch.
        Get the policy action and state from an observation (and optional state).

        :param observation: the input observation
        :param state: The last states (can be None, used in recurrent policies)
        :param mask: The last masks (can be None, used in recurrent policies)
        :param deterministic: Whether or not to return deterministic actions.
        :return: the model's action and the next state
            (used in recurrent policies)
        """
        if not isinstance(observation, dict):
            observation = np.array(observation)
        vectorized_env = is_vectorized_observation(observation, self.observation_space)
        if self._debug_write_octree:
            ocnn.write_octree(th.from_numpy(observation[-1]), 'octree.octree')
        octree_batch = preprocess_stacked_octree_batch(observation, self.device, separate_batches=self._separate_networks_for_stacks)
        with th.no_grad():
            actions = self._predict(octree_batch, deterministic=deterministic)
        actions = actions.cpu().numpy()
        if isinstance(self.action_space, gym.spaces.Box):
            if self.squash_output:
                actions = self.unscale_action(actions)
            else:
                actions = np.clip(actions, self.action_space.low, self.action_space.high)
        if not vectorized_env:
            if state is not None:
                raise ValueError('Error: The environment must be vectorized when using recurrent policies.')
            actions = actions[0]
        return (actions, state)

def __init__(self, observation_space: gym.spaces.Space, action_space: gym.spaces.Space, lr_schedule, net_arch: Optional[Union[List[int], Dict[str, List[int]]]]=None, activation_fn: Type[nn.Module]=nn.ReLU, use_sde: bool=False, log_std_init: float=-3, sde_net_arch: Optional[List[int]]=None, use_expln: bool=False, clip_mean: float=2.0, features_extractor_class: Type[BaseFeaturesExtractor]=OctreeCnnFeaturesExtractor, features_extractor_kwargs: Optional[Dict[str, Any]]=None, normalize_images: bool=True, optimizer_class: Type[th.optim.Optimizer]=th.optim.Adam, optimizer_kwargs: Optional[Dict[str, Any]]=None, n_critics: int=2, share_features_extractor: bool=True, separate_networks_for_stacks: bool=True, debug_write_octree: bool=False):
    features_extractor_kwargs.update({'separate_networks_for_stacks': separate_networks_for_stacks})
    super(OctreeCnnPolicy, self).__init__(observation_space, action_space, lr_schedule, net_arch, activation_fn, use_sde, log_std_init, sde_net_arch, use_expln, clip_mean, features_extractor_class, features_extractor_kwargs, normalize_images, optimizer_class, optimizer_kwargs, n_critics, share_features_extractor)
    self._separate_networks_for_stacks = separate_networks_for_stacks
    self._debug_write_octree = debug_write_octree

class DepthImageCnnPolicy(SACPolicy):
    """
    Policy class (with both actor and critic) for SAC.

    :param observation_space: Observation space
    :param action_space: Action space
    :param lr_schedule: Learning rate schedule (could be constant)
    :param net_arch: The specification of the policy and value networks.
    :param activation_fn: Activation function
    :param use_sde: Whether to use State Dependent Exploration or not
    :param log_std_init: Initial value for the log standard deviation
    :param sde_net_arch: Network architecture for extracting features
        when using gSDE. If None, the latent features from the policy will be used.
        Pass an empty list to use the states as features.
    :param use_expln: Use ``expln()`` function instead of ``exp()`` when using gSDE to ensure
        a positive standard deviation (cf paper). It allows to keep variance
        above zero and prevent it from growing too fast. In practice, ``exp()`` is usually enough.
    :param clip_mean: Clip the mean output when using gSDE to avoid numerical instability.
    :param features_extractor_class: Features extractor to use (``OctreeCnnFeaturesExtractor``).
    :param normalize_images: Whether to normalize images or not,
         dividing by 255.0 (True by default)
    :param optimizer_class: The optimizer to use,
        ``th.optim.Adam`` by default
    :param optimizer_kwargs: Additional keyword arguments,
        excluding the learning rate, to pass to the optimizer
    :param n_critics: Number of critic networks to create.
    :param share_features_extractor: Whether to share or not the features extractor
        between the actor and the critic (this saves computation time)
    """

    def __init__(self, observation_space: gym.spaces.Space, action_space: gym.spaces.Space, lr_schedule, net_arch: Optional[Union[List[int], Dict[str, List[int]]]]=None, activation_fn: Type[nn.Module]=nn.ReLU, use_sde: bool=False, log_std_init: float=-3, sde_net_arch: Optional[List[int]]=None, use_expln: bool=False, clip_mean: float=2.0, features_extractor_class: Type[BaseFeaturesExtractor]=ImageCnnFeaturesExtractor, features_extractor_kwargs: Optional[Dict[str, Any]]=None, normalize_images: bool=True, optimizer_class: Type[th.optim.Optimizer]=th.optim.Adam, optimizer_kwargs: Optional[Dict[str, Any]]=None, n_critics: int=2, share_features_extractor: bool=True, separate_networks_for_stacks: bool=True):
        features_extractor_kwargs.update({'separate_networks_for_stacks': separate_networks_for_stacks})
        super(OctreeCnnPolicy, self).__init__(observation_space, action_space, lr_schedule, net_arch, activation_fn, use_sde, log_std_init, sde_net_arch, use_expln, clip_mean, features_extractor_class, features_extractor_kwargs, normalize_images, optimizer_class, optimizer_kwargs, n_critics, share_features_extractor)
        self._separate_networks_for_stacks = separate_networks_for_stacks

    def make_actor(self, features_extractor: Optional[BaseFeaturesExtractor]=None) -> Actor:
        actor_kwargs = self._update_features_extractor(self.actor_kwargs, features_extractor)
        return ActorWithoutPreprocessing(**actor_kwargs).to(self.device)

    def make_critic(self, features_extractor: Optional[BaseFeaturesExtractor]=None) -> ContinuousCritic:
        critic_kwargs = self._update_features_extractor(self.critic_kwargs, features_extractor)
        return ContinuousCriticWithoutPreprocessing(**critic_kwargs).to(self.device)

    def predict(self, observation: np.ndarray, state: Optional[np.ndarray]=None, mask: Optional[np.ndarray]=None, deterministic: bool=False) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Overridden to create proper Octree batch.
        Get the policy action and state from an observation (and optional state).

        :param observation: the input observation
        :param state: The last states (can be None, used in recurrent policies)
        :param mask: The last masks (can be None, used in recurrent policies)
        :param deterministic: Whether or not to return deterministic actions.
        :return: the model's action and the next state
            (used in recurrent policies)
        """
        if not isinstance(observation, dict):
            observation = np.array(observation)
        vectorized_env = is_vectorized_observation(observation, self.observation_space)
        octree_batch = preprocess_stacked_depth_image_batch(observation, self.device, separate_batches=self._separate_networks_for_stacks)
        with th.no_grad():
            actions = self._predict(octree_batch, deterministic=deterministic)
        actions = actions.cpu().numpy()
        if isinstance(self.action_space, gym.spaces.Box):
            if self.squash_output:
                actions = self.unscale_action(actions)
            else:
                actions = np.clip(actions, self.action_space.low, self.action_space.high)
        if not vectorized_env:
            if state is not None:
                raise ValueError('Error: The environment must be vectorized when using recurrent policies.')
            actions = actions[0]
        return (actions, state)

def __init__(self, observation_space: gym.spaces.Space, action_space: gym.spaces.Space, lr_schedule, net_arch: Optional[Union[List[int], Dict[str, List[int]]]]=None, activation_fn: Type[nn.Module]=nn.ReLU, use_sde: bool=False, log_std_init: float=-3, sde_net_arch: Optional[List[int]]=None, use_expln: bool=False, clip_mean: float=2.0, features_extractor_class: Type[BaseFeaturesExtractor]=ImageCnnFeaturesExtractor, features_extractor_kwargs: Optional[Dict[str, Any]]=None, normalize_images: bool=True, optimizer_class: Type[th.optim.Optimizer]=th.optim.Adam, optimizer_kwargs: Optional[Dict[str, Any]]=None, n_critics: int=2, share_features_extractor: bool=True, separate_networks_for_stacks: bool=True):
    features_extractor_kwargs.update({'separate_networks_for_stacks': separate_networks_for_stacks})
    super(OctreeCnnPolicy, self).__init__(observation_space, action_space, lr_schedule, net_arch, activation_fn, use_sde, log_std_init, sde_net_arch, use_expln, clip_mean, features_extractor_class, features_extractor_kwargs, normalize_images, optimizer_class, optimizer_kwargs, n_critics, share_features_extractor)
    self._separate_networks_for_stacks = separate_networks_for_stacks

class ActorWithoutPreprocessing(Actor):
    """
    Actor network (policy) for TQC.
    Overridden to not preprocess observations (unnecessary conversion into float)

    :param observation_space: Obervation space
    :param action_space: Action space
    :param net_arch: Network architecture
    :param features_extractor: Network to extract features
        (a CNN when using images, a nn.Flatten() layer otherwise)
    :param features_dim: Number of features
    :param activation_fn: Activation function
    :param use_sde: Whether to use State Dependent Exploration or not
    :param log_std_init: Initial value for the log standard deviation
    :param full_std: Whether to use (n_features x n_actions) parameters
        for the std instead of only (n_features,) when using gSDE.
    :param sde_net_arch: Network architecture for extracting features
        when using gSDE. If None, the latent features from the policy will be used.
        Pass an empty list to use the states as features.
    :param use_expln: Use ``expln()`` function instead of ``exp()`` when using gSDE to ensure
        a positive standard deviation (cf paper). It allows to keep variance
        above zero and prevent it from growing too fast. In practice, ``exp()`` is usually enough.
    :param clip_mean: Clip the mean output when using gSDE to avoid numerical instability.
    :param normalize_images: Whether to normalize images or not,
         dividing by 255.0 (True by default)
    """

    def __init__(self, observation_space: gym.spaces.Space, action_space: gym.spaces.Space, net_arch: List[int], features_extractor: nn.Module, features_dim: int, activation_fn: Type[nn.Module]=nn.ReLU, use_sde: bool=False, log_std_init: float=-3, full_std: bool=True, sde_net_arch: Optional[List[int]]=None, use_expln: bool=False, clip_mean: float=2.0, normalize_images: bool=True):
        super(ActorWithoutPreprocessing, self).__init__(observation_space=observation_space, action_space=action_space, net_arch=net_arch, features_extractor=features_extractor, features_dim=features_dim, activation_fn=activation_fn, use_sde=use_sde, log_std_init=log_std_init, full_std=full_std, sde_net_arch=sde_net_arch, use_expln=use_expln, clip_mean=clip_mean, normalize_images=normalize_images)

    def extract_features(self, obs: th.Tensor) -> th.Tensor:
        """
        Preprocess the observation if needed and extract features.
        Overridden to skip pre-processing (for some reason it converts tensor to Float)

        :param obs:
        :return:
        """
        assert self.features_extractor is not None, 'No features extractor was set'
        return self.features_extractor(obs)

def __init__(self, observation_space: gym.spaces.Space, action_space: gym.spaces.Space, net_arch: List[int], features_extractor: nn.Module, features_dim: int, activation_fn: Type[nn.Module]=nn.ReLU, use_sde: bool=False, log_std_init: float=-3, full_std: bool=True, sde_net_arch: Optional[List[int]]=None, use_expln: bool=False, clip_mean: float=2.0, normalize_images: bool=True):
    super(ActorWithoutPreprocessing, self).__init__(observation_space=observation_space, action_space=action_space, net_arch=net_arch, features_extractor=features_extractor, features_dim=features_dim, activation_fn=activation_fn, use_sde=use_sde, log_std_init=log_std_init, full_std=full_std, sde_net_arch=sde_net_arch, use_expln=use_expln, clip_mean=clip_mean, normalize_images=normalize_images)

class CriticWithoutPreprocessing(Critic):
    """
    Critic network (q-value function) for TQC.
    Overridden to not preprocess observations (unnecessary conversion into float)

    :param observation_space: Obervation space
    :param action_space: Action space
    :param net_arch: Network architecture
    :param features_extractor: Network to extract features
        (a CNN when using images, a nn.Flatten() layer otherwise)
    :param features_dim: Number of features
    :param activation_fn: Activation function
    :param normalize_images: Whether to normalize images or not,
         dividing by 255.0 (True by default)
    :param share_features_extractor: Whether the features extractor is shared or not
        between the actor and the critic (this saves computation time)
    """

    def __init__(self, observation_space: gym.spaces.Space, action_space: gym.spaces.Space, net_arch: List[int], features_extractor: nn.Module, features_dim: int, activation_fn: Type[nn.Module]=nn.ReLU, normalize_images: bool=True, n_quantiles: int=25, n_critics: int=2, share_features_extractor: bool=True):
        super(CriticWithoutPreprocessing, self).__init__(observation_space=observation_space, action_space=action_space, net_arch=net_arch, features_extractor=features_extractor, features_dim=features_dim, activation_fn=activation_fn, normalize_images=normalize_images, n_quantiles=n_quantiles, n_critics=n_critics, share_features_extractor=share_features_extractor)

    def extract_features(self, obs: th.Tensor) -> th.Tensor:
        """
        Preprocess the observation if needed and extract features.
        Overridden to skip pre-processing (for some reason it converts tensor to Float)

        :param obs:
        :return:
        """
        assert self.features_extractor is not None, 'No features extractor was set'
        return self.features_extractor(obs)

def __init__(self, observation_space: gym.spaces.Space, action_space: gym.spaces.Space, net_arch: List[int], features_extractor: nn.Module, features_dim: int, activation_fn: Type[nn.Module]=nn.ReLU, normalize_images: bool=True, n_quantiles: int=25, n_critics: int=2, share_features_extractor: bool=True):
    super(CriticWithoutPreprocessing, self).__init__(observation_space=observation_space, action_space=action_space, net_arch=net_arch, features_extractor=features_extractor, features_dim=features_dim, activation_fn=activation_fn, normalize_images=normalize_images, n_quantiles=n_quantiles, n_critics=n_critics, share_features_extractor=share_features_extractor)

class OctreeCnnPolicy(TQCPolicy):
    """
    Policy class (with both actor and critic) for TQC.

    :param observation_space: Observation space
    :param action_space: Action space
    :param lr_schedule: Learning rate schedule (could be constant)
    :param net_arch: The specification of the policy and value networks.
    :param activation_fn: Activation function
    :param use_sde: Whether to use State Dependent Exploration or not
    :param log_std_init: Initial value for the log standard deviation
    :param sde_net_arch: Network architecture for extracting features
        when using gSDE. If None, the latent features from the policy will be used.
        Pass an empty list to use the states as features.
    :param use_expln: Use ``expln()`` function instead of ``exp()`` when using gSDE to ensure
        a positive standard deviation (cf paper). It allows to keep variance
        above zero and prevent it from growing too fast. In practice, ``exp()`` is usually enough.
    :param clip_mean: Clip the mean output when using gSDE to avoid numerical instability.
    :param features_extractor_class: Features extractor to use.
    :param features_extractor_kwargs: Keyword arguments
        to pass to the feature extractor.
    :param normalize_images: Whether to normalize images or not,
         dividing by 255.0 (True by default)
    :param optimizer_class: The optimizer to use,
        ``th.optim.Adam`` by default
    :param optimizer_kwargs: Additional keyword arguments,
        excluding the learning rate, to pass to the optimizer
    :param share_features_extractor: Whether to share or not the features extractor
        between the actor and the critic (this saves computation time)
    """

    def __init__(self, observation_space: gym.spaces.Space, action_space: gym.spaces.Space, lr_schedule, net_arch: Optional[List[int]]=None, activation_fn: Type[nn.Module]=nn.ReLU, use_sde: bool=False, log_std_init: float=-3, sde_net_arch: Optional[List[int]]=None, use_expln: bool=False, clip_mean: float=2.0, features_extractor_class: Type[BaseFeaturesExtractor]=OctreeCnnFeaturesExtractor, features_extractor_kwargs: Optional[Dict[str, Any]]=None, normalize_images: bool=True, optimizer_class: Type[th.optim.Optimizer]=th.optim.Adam, optimizer_kwargs: Optional[Dict[str, Any]]=None, n_quantiles: int=25, n_critics: int=2, share_features_extractor: bool=True, separate_networks_for_stacks: bool=True, debug_write_octree: bool=False):
        features_extractor_kwargs.update({'separate_networks_for_stacks': separate_networks_for_stacks})
        super(OctreeCnnPolicy, self).__init__(observation_space=observation_space, action_space=action_space, lr_schedule=lr_schedule, net_arch=net_arch, activation_fn=activation_fn, use_sde=use_sde, log_std_init=log_std_init, sde_net_arch=sde_net_arch, use_expln=use_expln, clip_mean=clip_mean, features_extractor_class=features_extractor_class, features_extractor_kwargs=features_extractor_kwargs, normalize_images=normalize_images, optimizer_class=optimizer_class, optimizer_kwargs=optimizer_kwargs, n_quantiles=n_quantiles, n_critics=n_critics, share_features_extractor=share_features_extractor)
        self._separate_networks_for_stacks = separate_networks_for_stacks
        self._debug_write_octree = debug_write_octree

    def make_actor(self, features_extractor: Optional[BaseFeaturesExtractor]=None) -> Actor:
        actor_kwargs = self._update_features_extractor(self.actor_kwargs, features_extractor)
        return ActorWithoutPreprocessing(**actor_kwargs).to(self.device)

    def make_critic(self, features_extractor: Optional[BaseFeaturesExtractor]=None) -> Critic:
        critic_kwargs = self._update_features_extractor(self.critic_kwargs, features_extractor)
        return CriticWithoutPreprocessing(**critic_kwargs).to(self.device)

    def predict(self, observation: np.ndarray, state: Optional[np.ndarray]=None, mask: Optional[np.ndarray]=None, deterministic: bool=False) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Overridden to create proper Octree batch.
        Get the policy action and state from an observation (and optional state).

        :param observation: the input observation
        :param state: The last states (can be None, used in recurrent policies)
        :param mask: The last masks (can be None, used in recurrent policies)
        :param deterministic: Whether or not to return deterministic actions.
        :return: the model's action and the next state
            (used in recurrent policies)
        """
        if not isinstance(observation, dict):
            observation = np.array(observation)
        vectorized_env = is_vectorized_observation(observation, self.observation_space)
        if self._debug_write_octree:
            ocnn.write_octree(th.from_numpy(observation[-1]), 'octree.octree')
        octree_batch = preprocess_stacked_octree_batch(observation, self.device, separate_batches=self._separate_networks_for_stacks)
        with th.no_grad():
            actions = self._predict(octree_batch, deterministic=deterministic)
        actions = actions.cpu().numpy()
        if isinstance(self.action_space, gym.spaces.Box):
            if self.squash_output:
                actions = self.unscale_action(actions)
            else:
                actions = np.clip(actions, self.action_space.low, self.action_space.high)
        if not vectorized_env:
            if state is not None:
                raise ValueError('Error: The environment must be vectorized when using recurrent policies.')
            actions = actions[0]
        return (actions, state)

def __init__(self, observation_space: gym.spaces.Space, action_space: gym.spaces.Space, lr_schedule, net_arch: Optional[List[int]]=None, activation_fn: Type[nn.Module]=nn.ReLU, use_sde: bool=False, log_std_init: float=-3, sde_net_arch: Optional[List[int]]=None, use_expln: bool=False, clip_mean: float=2.0, features_extractor_class: Type[BaseFeaturesExtractor]=OctreeCnnFeaturesExtractor, features_extractor_kwargs: Optional[Dict[str, Any]]=None, normalize_images: bool=True, optimizer_class: Type[th.optim.Optimizer]=th.optim.Adam, optimizer_kwargs: Optional[Dict[str, Any]]=None, n_quantiles: int=25, n_critics: int=2, share_features_extractor: bool=True, separate_networks_for_stacks: bool=True, debug_write_octree: bool=False):
    features_extractor_kwargs.update({'separate_networks_for_stacks': separate_networks_for_stacks})
    super(OctreeCnnPolicy, self).__init__(observation_space=observation_space, action_space=action_space, lr_schedule=lr_schedule, net_arch=net_arch, activation_fn=activation_fn, use_sde=use_sde, log_std_init=log_std_init, sde_net_arch=sde_net_arch, use_expln=use_expln, clip_mean=clip_mean, features_extractor_class=features_extractor_class, features_extractor_kwargs=features_extractor_kwargs, normalize_images=normalize_images, optimizer_class=optimizer_class, optimizer_kwargs=optimizer_kwargs, n_quantiles=n_quantiles, n_critics=n_critics, share_features_extractor=share_features_extractor)
    self._separate_networks_for_stacks = separate_networks_for_stacks
    self._debug_write_octree = debug_write_octree

class DepthImageCnnPolicy(TQCPolicy):
    """
    Policy class (with both actor and critic) for TQC.

    :param observation_space: Observation space
    :param action_space: Action space
    :param lr_schedule: Learning rate schedule (could be constant)
    :param net_arch: The specification of the policy and value networks.
    :param activation_fn: Activation function
    :param use_sde: Whether to use State Dependent Exploration or not
    :param log_std_init: Initial value for the log standard deviation
    :param sde_net_arch: Network architecture for extracting features
        when using gSDE. If None, the latent features from the policy will be used.
        Pass an empty list to use the states as features.
    :param use_expln: Use ``expln()`` function instead of ``exp()`` when using gSDE to ensure
        a positive standard deviation (cf paper). It allows to keep variance
        above zero and prevent it from growing too fast. In practice, ``exp()`` is usually enough.
    :param clip_mean: Clip the mean output when using gSDE to avoid numerical instability.
    :param features_extractor_class: Features extractor to use.
    :param features_extractor_kwargs: Keyword arguments
        to pass to the feature extractor.
    :param normalize_images: Whether to normalize images or not,
         dividing by 255.0 (True by default)
    :param optimizer_class: The optimizer to use,
        ``th.optim.Adam`` by default
    :param optimizer_kwargs: Additional keyword arguments,
        excluding the learning rate, to pass to the optimizer
    :param share_features_extractor: Whether to share or not the features extractor
        between the actor and the critic (this saves computation time)
    """

    def __init__(self, observation_space: gym.spaces.Space, action_space: gym.spaces.Space, lr_schedule, net_arch: Optional[List[int]]=None, activation_fn: Type[nn.Module]=nn.ReLU, use_sde: bool=False, log_std_init: float=-3, sde_net_arch: Optional[List[int]]=None, use_expln: bool=False, clip_mean: float=2.0, features_extractor_class: Type[BaseFeaturesExtractor]=ImageCnnFeaturesExtractor, features_extractor_kwargs: Optional[Dict[str, Any]]=None, normalize_images: bool=True, optimizer_class: Type[th.optim.Optimizer]=th.optim.Adam, optimizer_kwargs: Optional[Dict[str, Any]]=None, n_quantiles: int=25, n_critics: int=2, share_features_extractor: bool=True, separate_networks_for_stacks: bool=True):
        features_extractor_kwargs.update({'separate_networks_for_stacks': separate_networks_for_stacks})
        super(DepthImageCnnPolicy, self).__init__(observation_space=observation_space, action_space=action_space, lr_schedule=lr_schedule, net_arch=net_arch, activation_fn=activation_fn, use_sde=use_sde, log_std_init=log_std_init, sde_net_arch=sde_net_arch, use_expln=use_expln, clip_mean=clip_mean, features_extractor_class=features_extractor_class, features_extractor_kwargs=features_extractor_kwargs, normalize_images=normalize_images, optimizer_class=optimizer_class, optimizer_kwargs=optimizer_kwargs, n_quantiles=n_quantiles, n_critics=n_critics, share_features_extractor=share_features_extractor)
        self._separate_networks_for_stacks = separate_networks_for_stacks

    def make_actor(self, features_extractor: Optional[BaseFeaturesExtractor]=None) -> Actor:
        actor_kwargs = self._update_features_extractor(self.actor_kwargs, features_extractor)
        return ActorWithoutPreprocessing(**actor_kwargs).to(self.device)

    def make_critic(self, features_extractor: Optional[BaseFeaturesExtractor]=None) -> Critic:
        critic_kwargs = self._update_features_extractor(self.critic_kwargs, features_extractor)
        return CriticWithoutPreprocessing(**critic_kwargs).to(self.device)

    def predict(self, observation: np.ndarray, state: Optional[np.ndarray]=None, mask: Optional[np.ndarray]=None, deterministic: bool=False) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Overridden to create proper Octree batch.
        Get the policy action and state from an observation (and optional state).

        :param observation: the input observation
        :param state: The last states (can be None, used in recurrent policies)
        :param mask: The last masks (can be None, used in recurrent policies)
        :param deterministic: Whether or not to return deterministic actions.
        :return: the model's action and the next state
            (used in recurrent policies)
        """
        if not isinstance(observation, dict):
            observation = np.array(observation)
        vectorized_env = is_vectorized_observation(observation, self.observation_space)
        image_batch = preprocess_stacked_depth_image_batch(observation, self.device, separate_batches=self._separate_networks_for_stacks)
        with th.no_grad():
            actions = self._predict(image_batch, deterministic=deterministic)
        actions = actions.cpu().numpy()
        if isinstance(self.action_space, gym.spaces.Box):
            if self.squash_output:
                actions = self.unscale_action(actions)
            else:
                actions = np.clip(actions, self.action_space.low, self.action_space.high)
        if not vectorized_env:
            if state is not None:
                raise ValueError('Error: The environment must be vectorized when using recurrent policies.')
            actions = actions[0]
        return (actions, state)

def __init__(self, observation_space: gym.spaces.Space, action_space: gym.spaces.Space, lr_schedule, net_arch: Optional[List[int]]=None, activation_fn: Type[nn.Module]=nn.ReLU, use_sde: bool=False, log_std_init: float=-3, sde_net_arch: Optional[List[int]]=None, use_expln: bool=False, clip_mean: float=2.0, features_extractor_class: Type[BaseFeaturesExtractor]=ImageCnnFeaturesExtractor, features_extractor_kwargs: Optional[Dict[str, Any]]=None, normalize_images: bool=True, optimizer_class: Type[th.optim.Optimizer]=th.optim.Adam, optimizer_kwargs: Optional[Dict[str, Any]]=None, n_quantiles: int=25, n_critics: int=2, share_features_extractor: bool=True, separate_networks_for_stacks: bool=True):
    features_extractor_kwargs.update({'separate_networks_for_stacks': separate_networks_for_stacks})
    super(DepthImageCnnPolicy, self).__init__(observation_space=observation_space, action_space=action_space, lr_schedule=lr_schedule, net_arch=net_arch, activation_fn=activation_fn, use_sde=use_sde, log_std_init=log_std_init, sde_net_arch=sde_net_arch, use_expln=use_expln, clip_mean=clip_mean, features_extractor_class=features_extractor_class, features_extractor_kwargs=features_extractor_kwargs, normalize_images=normalize_images, optimizer_class=optimizer_class, optimizer_kwargs=optimizer_kwargs, n_quantiles=n_quantiles, n_critics=n_critics, share_features_extractor=share_features_extractor)
    self._separate_networks_for_stacks = separate_networks_for_stacks

class ActorWithoutPreprocessing(Actor):
    """
    Actor network (policy) for TD3.
    Overridden to not preprocess observations (unnecessary conversion into float)

    :param observation_space: Obervation space
    :param action_space: Action space
    :param net_arch: Network architecture
    :param features_extractor: Network to extract features
        (a CNN when using images, a nn.Flatten() layer otherwise)
    :param features_dim: Number of features
    :param activation_fn: Activation function
    :param normalize_images: Whether to normalize images or not,
         dividing by 255.0 (True by default)
    """

    def __init__(self, observation_space: gym.spaces.Space, action_space: gym.spaces.Space, net_arch: List[int], features_extractor: nn.Module, features_dim: int, activation_fn: Type[nn.Module]=nn.ReLU, normalize_images: bool=True):
        super(ActorWithoutPreprocessing, self).__init__(observation_space=observation_space, action_space=action_space, net_arch=net_arch, features_extractor=features_extractor, features_dim=features_dim, activation_fn=activation_fn, normalize_images=normalize_images)

    def extract_features(self, obs: th.Tensor) -> th.Tensor:
        """
        Preprocess the observation if needed and extract features.
        Overridden to skip pre-processing (for some reason it converts tensor to Float)

        :param obs:
        :return:
        """
        assert self.features_extractor is not None, 'No features extractor was set'
        return self.features_extractor(obs)

def __init__(self, observation_space: gym.spaces.Space, action_space: gym.spaces.Space, net_arch: List[int], features_extractor: nn.Module, features_dim: int, activation_fn: Type[nn.Module]=nn.ReLU, normalize_images: bool=True):
    super(ActorWithoutPreprocessing, self).__init__(observation_space=observation_space, action_space=action_space, net_arch=net_arch, features_extractor=features_extractor, features_dim=features_dim, activation_fn=activation_fn, normalize_images=normalize_images)

class ContinuousWithoutPreprocessing(ContinuousCritic):
    """
    Critic network(s) for DDPG/SAC/TD3.
    Overridden to not preprocess observations (unnecessary conversion into float)

    It represents the action-state value function (Q-value function).
    Compared to A2C/PPO critics, this one represents the Q-value
    and takes the continuous action as input. It is concatenated with the state
    and then fed to the network which outputs a single value: Q(s, a).
    For more recent algorithms like SAC/TD3, multiple networks
    are created to give different estimates.

    By default, it creates two critic networks used to reduce overestimation
    thanks to clipped Q-learning (cf TD3 paper).

    :param observation_space: Obervation space
    :param action_space: Action space
    :param net_arch: Network architecture
    :param features_extractor: Network to extract features
        (a CNN when using images, a nn.Flatten() layer otherwise)
    :param features_dim: Number of features
    :param activation_fn: Activation function
    :param normalize_images: Whether to normalize images or not,
         dividing by 255.0 (True by default)
    :param n_critics: Number of critic networks to create.
    :param share_features_extractor: Whether the features extractor is shared or not
        between the actor and the critic (this saves computation time)
    """

    def __init__(self, observation_space: gym.spaces.Space, action_space: gym.spaces.Space, net_arch: List[int], features_extractor: nn.Module, features_dim: int, activation_fn: Type[nn.Module]=nn.ReLU, normalize_images: bool=True, n_critics: int=2, share_features_extractor: bool=True):
        super().__init__(observation_space=observation_space, action_space=action_space, net_arch=net_arch, features_extractor=features_extractor, features_dim=features_dim, activation_fn=activation_fn, normalize_images=normalize_images, n_critics=n_critics, share_features_extractor=share_features_extractor)

    def extract_features(self, obs: th.Tensor) -> th.Tensor:
        """
        Preprocess the observation if needed and extract features.
        Overridden to skip pre-processing (for some reason it converts tensor to Float)

        :param obs:
        :return:
        """
        assert self.features_extractor is not None, 'No features extractor was set'
        return self.features_extractor(obs)

def __init__(self, observation_space: gym.spaces.Space, action_space: gym.spaces.Space, net_arch: List[int], features_extractor: nn.Module, features_dim: int, activation_fn: Type[nn.Module]=nn.ReLU, normalize_images: bool=True, n_critics: int=2, share_features_extractor: bool=True):
    super().__init__(observation_space=observation_space, action_space=action_space, net_arch=net_arch, features_extractor=features_extractor, features_dim=features_dim, activation_fn=activation_fn, normalize_images=normalize_images, n_critics=n_critics, share_features_extractor=share_features_extractor)

class OctreeCnnPolicy(TD3Policy):
    """
    Policy class (with both actor and critic) for TD3.

    :param observation_space: Observation space
    :param action_space: Action space
    :param lr_schedule: Learning rate schedule (could be constant)
    :param net_arch: The specification of the policy and value networks.
    :param activation_fn: Activation function
    :param features_extractor_class: Features extractor to use.
    :param features_extractor_kwargs: Keyword arguments
        to pass to the features extractor.
    :param normalize_images: Whether to normalize images or not,
         dividing by 255.0 (True by default)
    :param optimizer_class: The optimizer to use,
        ``th.optim.Adam`` by default
    :param optimizer_kwargs: Additional keyword arguments,
        excluding the learning rate, to pass to the optimizer
    :param n_critics: Number of critic networks to create.
    :param share_features_extractor: Whether to share or not the features extractor
        between the actor and the critic (this saves computation time)
    """

    def __init__(self, observation_space: gym.spaces.Space, action_space: gym.spaces.Space, lr_schedule, net_arch: Optional[Union[List[int], Dict[str, List[int]]]]=None, activation_fn: Type[nn.Module]=nn.ReLU, features_extractor_class: Type[BaseFeaturesExtractor]=OctreeCnnFeaturesExtractor, features_extractor_kwargs: Optional[Dict[str, Any]]=None, normalize_images: bool=True, optimizer_class: Type[th.optim.Optimizer]=th.optim.Adam, optimizer_kwargs: Optional[Dict[str, Any]]=None, n_critics: int=2, share_features_extractor: bool=True, separate_networks_for_stacks: bool=True, debug_write_octree: bool=False):
        features_extractor_kwargs.update({'separate_networks_for_stacks': separate_networks_for_stacks})
        super(OctreeCnnPolicy, self).__init__(observation_space, action_space, lr_schedule, net_arch, activation_fn, features_extractor_class, features_extractor_kwargs, normalize_images, optimizer_class, optimizer_kwargs, n_critics, share_features_extractor)
        self._separate_networks_for_stacks = separate_networks_for_stacks
        self._debug_write_octree = debug_write_octree

    def make_actor(self, features_extractor: Optional[BaseFeaturesExtractor]=None) -> Actor:
        actor_kwargs = self._update_features_extractor(self.actor_kwargs, features_extractor)
        return ActorWithoutPreprocessing(**actor_kwargs).to(self.device)

    def make_critic(self, features_extractor: Optional[BaseFeaturesExtractor]=None) -> ContinuousCritic:
        critic_kwargs = self._update_features_extractor(self.critic_kwargs, features_extractor)
        return ContinuousWithoutPreprocessing(**critic_kwargs).to(self.device)

    def predict(self, observation: np.ndarray, state: Optional[np.ndarray]=None, mask: Optional[np.ndarray]=None, deterministic: bool=False) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Overridden to create proper Octree batch.
        Get the policy action and state from an observation (and optional state).

        :param observation: the input observation
        :param state: The last states (can be None, used in recurrent policies)
        :param mask: The last masks (can be None, used in recurrent policies)
        :param deterministic: Whether or not to return deterministic actions.
        :return: the model's action and the next state
            (used in recurrent policies)
        """
        if not isinstance(observation, dict):
            observation = np.array(observation)
        vectorized_env = is_vectorized_observation(observation, self.observation_space)
        if self._debug_write_octree:
            ocnn.write_octree(th.from_numpy(observation[-1]), 'octree.octree')
        octree_batch = preprocess_stacked_octree_batch(observation, self.device, separate_batches=self._separate_networks_for_stacks)
        with th.no_grad():
            actions = self._predict(octree_batch, deterministic=deterministic)
        actions = actions.cpu().numpy()
        if isinstance(self.action_space, gym.spaces.Box):
            if self.squash_output:
                actions = self.unscale_action(actions)
            else:
                actions = np.clip(actions, self.action_space.low, self.action_space.high)
        if not vectorized_env:
            if state is not None:
                raise ValueError('Error: The environment must be vectorized when using recurrent policies.')
            actions = actions[0]
        return (actions, state)

def __init__(self, observation_space: gym.spaces.Space, action_space: gym.spaces.Space, lr_schedule, net_arch: Optional[Union[List[int], Dict[str, List[int]]]]=None, activation_fn: Type[nn.Module]=nn.ReLU, features_extractor_class: Type[BaseFeaturesExtractor]=OctreeCnnFeaturesExtractor, features_extractor_kwargs: Optional[Dict[str, Any]]=None, normalize_images: bool=True, optimizer_class: Type[th.optim.Optimizer]=th.optim.Adam, optimizer_kwargs: Optional[Dict[str, Any]]=None, n_critics: int=2, share_features_extractor: bool=True, separate_networks_for_stacks: bool=True, debug_write_octree: bool=False):
    features_extractor_kwargs.update({'separate_networks_for_stacks': separate_networks_for_stacks})
    super(OctreeCnnPolicy, self).__init__(observation_space, action_space, lr_schedule, net_arch, activation_fn, features_extractor_class, features_extractor_kwargs, normalize_images, optimizer_class, optimizer_kwargs, n_critics, share_features_extractor)
    self._separate_networks_for_stacks = separate_networks_for_stacks
    self._debug_write_octree = debug_write_octree

class DepthImageCnnPolicy(TD3Policy):
    """
    Policy class (with both actor and critic) for TD3.

    :param observation_space: Observation space
    :param action_space: Action space
    :param lr_schedule: Learning rate schedule (could be constant)
    :param net_arch: The specification of the policy and value networks.
    :param activation_fn: Activation function
    :param features_extractor_class: Features extractor to use.
    :param features_extractor_kwargs: Keyword arguments
        to pass to the features extractor.
    :param normalize_images: Whether to normalize images or not,
         dividing by 255.0 (True by default)
    :param optimizer_class: The optimizer to use,
        ``th.optim.Adam`` by default
    :param optimizer_kwargs: Additional keyword arguments,
        excluding the learning rate, to pass to the optimizer
    :param n_critics: Number of critic networks to create.
    :param share_features_extractor: Whether to share or not the features extractor
        between the actor and the critic (this saves computation time)
    """

    def __init__(self, observation_space: gym.spaces.Space, action_space: gym.spaces.Space, lr_schedule, net_arch: Optional[Union[List[int], Dict[str, List[int]]]]=None, activation_fn: Type[nn.Module]=nn.ReLU, features_extractor_class: Type[BaseFeaturesExtractor]=ImageCnnFeaturesExtractor, features_extractor_kwargs: Optional[Dict[str, Any]]=None, normalize_images: bool=True, optimizer_class: Type[th.optim.Optimizer]=th.optim.Adam, optimizer_kwargs: Optional[Dict[str, Any]]=None, n_critics: int=2, share_features_extractor: bool=True, separate_networks_for_stacks: bool=True):
        features_extractor_kwargs.update({'separate_networks_for_stacks': separate_networks_for_stacks})
        super(OctreeCnnPolicy, self).__init__(observation_space, action_space, lr_schedule, net_arch, activation_fn, features_extractor_class, features_extractor_kwargs, normalize_images, optimizer_class, optimizer_kwargs, n_critics, share_features_extractor)
        self._separate_networks_for_stacks = separate_networks_for_stacks

    def make_actor(self, features_extractor: Optional[BaseFeaturesExtractor]=None) -> Actor:
        actor_kwargs = self._update_features_extractor(self.actor_kwargs, features_extractor)
        return ActorWithoutPreprocessing(**actor_kwargs).to(self.device)

    def make_critic(self, features_extractor: Optional[BaseFeaturesExtractor]=None) -> ContinuousCritic:
        critic_kwargs = self._update_features_extractor(self.critic_kwargs, features_extractor)
        return ContinuousWithoutPreprocessing(**critic_kwargs).to(self.device)

    def predict(self, observation: np.ndarray, state: Optional[np.ndarray]=None, mask: Optional[np.ndarray]=None, deterministic: bool=False) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Overridden to create proper Octree batch.
        Get the policy action and state from an observation (and optional state).

        :param observation: the input observation
        :param state: The last states (can be None, used in recurrent policies)
        :param mask: The last masks (can be None, used in recurrent policies)
        :param deterministic: Whether or not to return deterministic actions.
        :return: the model's action and the next state
            (used in recurrent policies)
        """
        if not isinstance(observation, dict):
            observation = np.array(observation)
        vectorized_env = is_vectorized_observation(observation, self.observation_space)
        octree_batch = preprocess_stacked_depth_image_batch(observation, self.device, separate_batches=self._separate_networks_for_stacks)
        with th.no_grad():
            actions = self._predict(octree_batch, deterministic=deterministic)
        actions = actions.cpu().numpy()
        if isinstance(self.action_space, gym.spaces.Box):
            if self.squash_output:
                actions = self.unscale_action(actions)
            else:
                actions = np.clip(actions, self.action_space.low, self.action_space.high)
        if not vectorized_env:
            if state is not None:
                raise ValueError('Error: The environment must be vectorized when using recurrent policies.')
            actions = actions[0]
        return (actions, state)

def __init__(self, observation_space: gym.spaces.Space, action_space: gym.spaces.Space, lr_schedule, net_arch: Optional[Union[List[int], Dict[str, List[int]]]]=None, activation_fn: Type[nn.Module]=nn.ReLU, features_extractor_class: Type[BaseFeaturesExtractor]=ImageCnnFeaturesExtractor, features_extractor_kwargs: Optional[Dict[str, Any]]=None, normalize_images: bool=True, optimizer_class: Type[th.optim.Optimizer]=th.optim.Adam, optimizer_kwargs: Optional[Dict[str, Any]]=None, n_critics: int=2, share_features_extractor: bool=True, separate_networks_for_stacks: bool=True):
    features_extractor_kwargs.update({'separate_networks_for_stacks': separate_networks_for_stacks})
    super(OctreeCnnPolicy, self).__init__(observation_space, action_space, lr_schedule, net_arch, activation_fn, features_extractor_class, features_extractor_kwargs, normalize_images, optimizer_class, optimizer_kwargs, n_critics, share_features_extractor)
    self._separate_networks_for_stacks = separate_networks_for_stacks

class OctreeConvRelu(torch.nn.Module):

    def __init__(self, depth, channel_in, channel_out, kernel_size=[3], stride=1):
        super(OctreeConvRelu, self).__init__()
        self.conv = ocnn.OctreeConv(depth, channel_in, channel_out, kernel_size, stride)
        self.relu = torch.nn.ReLU(inplace=True)

    def forward(self, data_in, octree):
        out = self.conv(data_in, octree)
        out = self.relu(out)
        return out

def __init__(self, depth, channel_in, channel_out, kernel_size=[3], stride=1):
    super(OctreeConvRelu, self).__init__()
    self.conv = ocnn.OctreeConv(depth, channel_in, channel_out, kernel_size, stride)
    self.relu = torch.nn.ReLU(inplace=True)

class OctreeConvBnRelu(torch.nn.Module):

    def __init__(self, depth, channel_in, channel_out, kernel_size=[3], stride=1, bn_eps=1e-05, bn_momentum=0.01):
        super(OctreeConvBnRelu, self).__init__()
        self.conv = ocnn.OctreeConv(depth, channel_in, channel_out, kernel_size, stride)
        self.bn = torch.nn.BatchNorm2d(channel_out, bn_eps, bn_momentum)
        self.relu = torch.nn.ReLU(inplace=True)

    def forward(self, data_in, octree):
        out = self.conv(data_in, octree)
        out = self.bn(out)
        out = self.relu(out)
        return out

def __init__(self, depth, channel_in, channel_out, kernel_size=[3], stride=1, bn_eps=1e-05, bn_momentum=0.01):
    super(OctreeConvBnRelu, self).__init__()
    self.conv = ocnn.OctreeConv(depth, channel_in, channel_out, kernel_size, stride)
    self.bn = torch.nn.BatchNorm2d(channel_out, bn_eps, bn_momentum)
    self.relu = torch.nn.ReLU(inplace=True)

class OctreeConvFastRelu(torch.nn.Module):

    def __init__(self, depth, channel_in, channel_out, kernel_size=[3], stride=1):
        super(OctreeConvFastRelu, self).__init__()
        self.conv = ocnn.OctreeConvFast(depth, channel_in, channel_out, kernel_size, stride)
        self.relu = torch.nn.ReLU(inplace=True)

    def forward(self, data_in, octree):
        out = self.conv(data_in, octree)
        out = self.relu(out)
        return out

def __init__(self, depth, channel_in, channel_out, kernel_size=[3], stride=1):
    super(OctreeConvFastRelu, self).__init__()
    self.conv = ocnn.OctreeConvFast(depth, channel_in, channel_out, kernel_size, stride)
    self.relu = torch.nn.ReLU(inplace=True)

class OctreeConvFastBnRelu(torch.nn.Module):

    def __init__(self, depth, channel_in, channel_out, kernel_size=[3], stride=1, bn_eps=1e-05, bn_momentum=0.01):
        super(OctreeConvFastBnRelu, self).__init__()
        self.conv = ocnn.OctreeConvFast(depth, channel_in, channel_out, kernel_size, stride)
        self.bn = torch.nn.BatchNorm2d(channel_out, bn_eps, bn_momentum)
        self.relu = torch.nn.ReLU(inplace=True)

    def forward(self, data_in, octree):
        out = self.conv(data_in, octree)
        out = self.bn(out)
        out = self.relu(out)
        return out

def __init__(self, depth, channel_in, channel_out, kernel_size=[3], stride=1, bn_eps=1e-05, bn_momentum=0.01):
    super(OctreeConvFastBnRelu, self).__init__()
    self.conv = ocnn.OctreeConvFast(depth, channel_in, channel_out, kernel_size, stride)
    self.bn = torch.nn.BatchNorm2d(channel_out, bn_eps, bn_momentum)
    self.relu = torch.nn.ReLU(inplace=True)

class OctreeConv1x1Relu(torch.nn.Module):

    def __init__(self, channel_in, channel_out, use_bias=True):
        super(OctreeConv1x1Relu, self).__init__()
        self.conv1x1 = ocnn.OctreeConv1x1(channel_in, channel_out, use_bias)
        self.relu = torch.nn.ReLU(inplace=True)

    def forward(self, data_in):
        out = self.conv1x1(data_in)
        out = self.relu(out)
        return out

def __init__(self, channel_in, channel_out, use_bias=True):
    super(OctreeConv1x1Relu, self).__init__()
    self.conv1x1 = ocnn.OctreeConv1x1(channel_in, channel_out, use_bias)
    self.relu = torch.nn.ReLU(inplace=True)

class OctreeConv1x1BnRelu(torch.nn.Module):

    def __init__(self, channel_in, channel_out, use_bias=True, bn_eps=1e-05, bn_momentum=0.01):
        super(OctreeConv1x1BnRelu, self).__init__()
        self.conv1x1 = ocnn.OctreeConv1x1(channel_in, channel_out, use_bias)
        self.bn = torch.nn.BatchNorm2d(channel_out, bn_eps, bn_momentum)
        self.relu = torch.nn.ReLU(inplace=True)

    def forward(self, data_in):
        out = self.conv1x1(data_in)
        out = self.bn(out)
        out = self.relu(out)
        return out

def __init__(self, channel_in, channel_out, use_bias=True, bn_eps=1e-05, bn_momentum=0.01):
    super(OctreeConv1x1BnRelu, self).__init__()
    self.conv1x1 = ocnn.OctreeConv1x1(channel_in, channel_out, use_bias)
    self.bn = torch.nn.BatchNorm2d(channel_out, bn_eps, bn_momentum)
    self.relu = torch.nn.ReLU(inplace=True)

class LinearRelu(torch.nn.Module):

    def __init__(self, channel_in, channel_out, use_bias=True):
        super(LinearRelu, self).__init__()
        self.fc = torch.nn.Linear(channel_in, channel_out, use_bias)
        self.relu = torch.nn.ReLU(inplace=True)

    def forward(self, data_in):
        out = self.fc(data_in)
        out = self.relu(out)
        return out

def __init__(self, channel_in, channel_out, use_bias=True):
    super(LinearRelu, self).__init__()
    self.fc = torch.nn.Linear(channel_in, channel_out, use_bias)
    self.relu = torch.nn.ReLU(inplace=True)

class LinearBnRelu(torch.nn.Module):

    def __init__(self, channel_in, channel_out, use_bias=True, bn_eps=1e-05, bn_momentum=0.01):
        super(LinearBnRelu, self).__init__()
        self.fc = torch.nn.Linear(channel_in, channel_out, use_bias)
        self.bn = torch.nn.BatchNorm1d(channel_out, bn_eps, bn_momentum)
        self.relu = torch.nn.ReLU(inplace=True)

    def forward(self, data_in):
        out = self.fc(data_in)
        out = self.bn(out)
        out = self.relu(out)
        return out

def __init__(self, channel_in, channel_out, use_bias=True, bn_eps=1e-05, bn_momentum=0.01):
    super(LinearBnRelu, self).__init__()
    self.fc = torch.nn.Linear(channel_in, channel_out, use_bias)
    self.bn = torch.nn.BatchNorm1d(channel_out, bn_eps, bn_momentum)
    self.relu = torch.nn.ReLU(inplace=True)

class ImageConvRelu(torch.nn.Module):

    def __init__(self, channel_in, channel_out, kernel_size=3, stride=1, padding=1):
        super(ImageConvRelu, self).__init__()
        self.conv = torch.nn.Conv2d(channel_in, channel_out, kernel_size, stride, padding)
        self.relu = torch.nn.ReLU(inplace=True)

    def forward(self, data_in):
        out = self.conv(data_in)
        out = self.relu(out)
        return out

def __init__(self, channel_in, channel_out, kernel_size=3, stride=1, padding=1):
    super(ImageConvRelu, self).__init__()
    self.conv = torch.nn.Conv2d(channel_in, channel_out, kernel_size, stride, padding)
    self.relu = torch.nn.ReLU(inplace=True)

class OctreeCnnFeaturesExtractor(BaseFeaturesExtractor):
    """
    :param observation_space:
    :param depth: Depth of input octree.
    :param full_depth: Depth at which convolutions stop and the octree is turned into voxel grid and flattened into output feature vector.
    :param channels_in: Number of input channels.
    :param channel_multiplier: Multiplier for the number of channels after each pooling.
                               With this parameter set to 1, the channels are [1, 2, 4, 8, ...] for [depth, depth-1, ..., full_depth].
    :param features_dim: Dimension of output feature vector. Note that this number is multiplied by the number of stacked octrees inside one observation.
    """

    def __init__(self, observation_space: gym.spaces.Box, depth: int=5, full_depth: int=2, channels_in: int=4, channel_multiplier: int=16, full_depth_conv1d: bool=False, full_depth_channels: int=8, features_dim: int=128, aux_obs_dim: int=0, aux_obs_features_dim: int=10, separate_networks_for_stacks: bool=True, fast_conv: bool=True, batch_normalization: bool=True, bn_eps: float=1e-05, bn_momentum: float=0.01, verbose: bool=False):
        self._depth = depth
        self._channels_in = channels_in
        self._aux_obs_dim = aux_obs_dim
        self._aux_obs_features_dim = aux_obs_features_dim
        self._separate_networks_for_stacks = separate_networks_for_stacks
        self._verbose = verbose
        if fast_conv:
            if batch_normalization:
                OctreeConv = OctreeConvFastBnRelu
                OctreeConv1D = OctreeConv1x1BnRelu
            else:
                OctreeConv = OctreeConvFastRelu
                OctreeConv1D = OctreeConv1x1Relu
        elif batch_normalization:
            OctreeConv = OctreeConvBnRelu
            OctreeConv1D = OctreeConv1x1BnRelu
        else:
            OctreeConv = OctreeConvRelu
            OctreeConv1D = OctreeConv1x1Relu
        OctreePool = ocnn.OctreeMaxPool
        bn_kwargs = {}
        if batch_normalization:
            bn_kwargs.update({'bn_eps': bn_eps, 'bn_momentum': bn_momentum})
        self._n_stacks = observation_space.shape[0]
        super(OctreeCnnFeaturesExtractor, self).__init__(observation_space, self._n_stacks * (features_dim + aux_obs_features_dim))
        self._n_convs = depth - full_depth
        channels = [channel_multiplier * 2 ** i for i in range(self._n_convs)]
        channels.insert(0, channels_in)
        full_depth_voxel_count = 2 ** (3 * full_depth)
        flatten_dim = full_depth_channels * full_depth_voxel_count
        if not self._separate_networks_for_stacks:
            self.convs = torch.nn.ModuleList([OctreeConv(depth - i, channels[i], channels[i + 1], **bn_kwargs) for i in range(self._n_convs)])
            self.pools = torch.nn.ModuleList([OctreePool(depth - i) for i in range(self._n_convs)])
            self._full_depth_conv1d = full_depth_conv1d
            if self._full_depth_conv1d:
                self.full_depth_conv = OctreeConv1D(channels[-1], full_depth_channels, **bn_kwargs)
            else:
                self.full_depth_conv = OctreeConv(full_depth, channels[-1], full_depth_channels, **bn_kwargs)
            self.octree2voxel = ocnn.FullOctree2Voxel(full_depth)
            self.flatten = torch.nn.Flatten()
            self.linear = LinearRelu(flatten_dim, features_dim)
            if self._aux_obs_dim != 0:
                self.aux_obs_linear = LinearRelu(self._aux_obs_dim, aux_obs_features_dim)
        else:
            self.convs = torch.nn.ModuleList([torch.nn.ModuleList([OctreeConv(depth - i, channels[i], channels[i + 1], **bn_kwargs) for i in range(self._n_convs)]) for _ in range(self._n_stacks)])
            self.pools = torch.nn.ModuleList([torch.nn.ModuleList([OctreePool(depth - i) for i in range(self._n_convs)]) for _ in range(self._n_stacks)])
            self._full_depth_conv1d = full_depth_conv1d
            if self._full_depth_conv1d:
                self.full_depth_conv = torch.nn.ModuleList([OctreeConv1D(channels[-1], full_depth_channels, **bn_kwargs) for _ in range(self._n_stacks)])
            else:
                self.full_depth_conv = torch.nn.ModuleList([OctreeConv(full_depth, channels[-1], full_depth_channels, **bn_kwargs) for _ in range(self._n_stacks)])
            self.octree2voxel = torch.nn.ModuleList([ocnn.FullOctree2Voxel(full_depth) for _ in range(self._n_stacks)])
            self.flatten = torch.nn.ModuleList([torch.nn.Flatten() for _ in range(self._n_stacks)])
            self.linear = torch.nn.ModuleList([LinearRelu(flatten_dim, features_dim) for _ in range(self._n_stacks)])
            if self._aux_obs_dim != 0:
                self.aux_obs_linear = torch.nn.ModuleList([LinearRelu(self._aux_obs_dim, aux_obs_features_dim) for _ in range(self._n_stacks)])
        number_of_learnable_parameters = sum((p.numel() for p in self.parameters() if p.requires_grad))
        print(f'Initialised OctreeCnnFeaturesExtractor with {number_of_learnable_parameters} parameters')
        if verbose:
            print(self)

    def forward(self, obs):
        """
        Note: input octree must be batch of octrees (created with ocnn)
        """
        octree = obs[0]
        aux_obs = obs[1]
        if not self._separate_networks_for_stacks:
            data = ocnn.octree_property(octree, 'feature', self._depth)
            assert data.size(1) == self._channels_in, f'Input octree has invalid number of channels. Got {data.size(1)}, expected {self._channels_in}'
            for i in range(self._n_convs):
                data = self.convs[i](data, octree)
                data = self.pools[i](data, octree)
            if self._full_depth_conv1d:
                data = self.full_depth_conv(data)
            else:
                data = self.full_depth_conv(data, octree)
            data = self.octree2voxel(data)
            data = self.flatten(data)
            data = self.linear(data)
            data = data.view(-1, self._n_stacks * data.shape[-1])
            if self._aux_obs_dim != 0:
                aux_data = self.aux_obs_linear(aux_obs.view(-1, self._aux_obs_dim))
                aux_data = aux_data.view(-1, self._n_stacks * self._aux_obs_features_dim)
                data = torch.cat((data, aux_data), dim=1)
        else:
            data = [ocnn.octree_property(octree[i], 'feature', self._depth) for i in range(self._n_stacks)]
            for i in range(self._n_stacks):
                for j in range(self._n_convs):
                    data[i] = self.convs[i][j](data[i], octree[i])
                    data[i] = self.pools[i][j](data[i], octree[i])
                if self._full_depth_conv1d:
                    data[i] = self.full_depth_conv[i](data[i])
                else:
                    data[i] = self.full_depth_conv[i](data[i], octree[i])
                data[i] = self.octree2voxel[i](data[i])
                data[i] = self.flatten[i](data[i])
                data[i] = self.linear[i](data[i])
                if self._aux_obs_dim != 0:
                    aux_data = self.aux_obs_linear[i](aux_obs[:, i, :])
                    data[i] = torch.cat((data[i], aux_data), dim=1)
            data = torch.cat(data, dim=1)
        return data

def __init__(self, observation_space: gym.spaces.Box, depth: int=5, full_depth: int=2, channels_in: int=4, channel_multiplier: int=16, full_depth_conv1d: bool=False, full_depth_channels: int=8, features_dim: int=128, aux_obs_dim: int=0, aux_obs_features_dim: int=10, separate_networks_for_stacks: bool=True, fast_conv: bool=True, batch_normalization: bool=True, bn_eps: float=1e-05, bn_momentum: float=0.01, verbose: bool=False):
    self._depth = depth
    self._channels_in = channels_in
    self._aux_obs_dim = aux_obs_dim
    self._aux_obs_features_dim = aux_obs_features_dim
    self._separate_networks_for_stacks = separate_networks_for_stacks
    self._verbose = verbose
    if fast_conv:
        if batch_normalization:
            OctreeConv = OctreeConvFastBnRelu
            OctreeConv1D = OctreeConv1x1BnRelu
        else:
            OctreeConv = OctreeConvFastRelu
            OctreeConv1D = OctreeConv1x1Relu
    elif batch_normalization:
        OctreeConv = OctreeConvBnRelu
        OctreeConv1D = OctreeConv1x1BnRelu
    else:
        OctreeConv = OctreeConvRelu
        OctreeConv1D = OctreeConv1x1Relu
    OctreePool = ocnn.OctreeMaxPool
    bn_kwargs = {}
    if batch_normalization:
        bn_kwargs.update({'bn_eps': bn_eps, 'bn_momentum': bn_momentum})
    self._n_stacks = observation_space.shape[0]
    super(OctreeCnnFeaturesExtractor, self).__init__(observation_space, self._n_stacks * (features_dim + aux_obs_features_dim))
    self._n_convs = depth - full_depth
    channels = [channel_multiplier * 2 ** i for i in range(self._n_convs)]
    channels.insert(0, channels_in)
    full_depth_voxel_count = 2 ** (3 * full_depth)
    flatten_dim = full_depth_channels * full_depth_voxel_count
    if not self._separate_networks_for_stacks:
        self.convs = torch.nn.ModuleList([OctreeConv(depth - i, channels[i], channels[i + 1], **bn_kwargs) for i in range(self._n_convs)])
        self.pools = torch.nn.ModuleList([OctreePool(depth - i) for i in range(self._n_convs)])
        self._full_depth_conv1d = full_depth_conv1d
        if self._full_depth_conv1d:
            self.full_depth_conv = OctreeConv1D(channels[-1], full_depth_channels, **bn_kwargs)
        else:
            self.full_depth_conv = OctreeConv(full_depth, channels[-1], full_depth_channels, **bn_kwargs)
        self.octree2voxel = ocnn.FullOctree2Voxel(full_depth)
        self.flatten = torch.nn.Flatten()
        self.linear = LinearRelu(flatten_dim, features_dim)
        if self._aux_obs_dim != 0:
            self.aux_obs_linear = LinearRelu(self._aux_obs_dim, aux_obs_features_dim)
    else:
        self.convs = torch.nn.ModuleList([torch.nn.ModuleList([OctreeConv(depth - i, channels[i], channels[i + 1], **bn_kwargs) for i in range(self._n_convs)]) for _ in range(self._n_stacks)])
        self.pools = torch.nn.ModuleList([torch.nn.ModuleList([OctreePool(depth - i) for i in range(self._n_convs)]) for _ in range(self._n_stacks)])
        self._full_depth_conv1d = full_depth_conv1d
        if self._full_depth_conv1d:
            self.full_depth_conv = torch.nn.ModuleList([OctreeConv1D(channels[-1], full_depth_channels, **bn_kwargs) for _ in range(self._n_stacks)])
        else:
            self.full_depth_conv = torch.nn.ModuleList([OctreeConv(full_depth, channels[-1], full_depth_channels, **bn_kwargs) for _ in range(self._n_stacks)])
        self.octree2voxel = torch.nn.ModuleList([ocnn.FullOctree2Voxel(full_depth) for _ in range(self._n_stacks)])
        self.flatten = torch.nn.ModuleList([torch.nn.Flatten() for _ in range(self._n_stacks)])
        self.linear = torch.nn.ModuleList([LinearRelu(flatten_dim, features_dim) for _ in range(self._n_stacks)])
        if self._aux_obs_dim != 0:
            self.aux_obs_linear = torch.nn.ModuleList([LinearRelu(self._aux_obs_dim, aux_obs_features_dim) for _ in range(self._n_stacks)])
    number_of_learnable_parameters = sum((p.numel() for p in self.parameters() if p.requires_grad))
    print(f'Initialised OctreeCnnFeaturesExtractor with {number_of_learnable_parameters} parameters')
    if verbose:
        print(self)

class ImageCnnFeaturesExtractor(BaseFeaturesExtractor):
    """
    :param observation_space:
    :param channels_in: Number of input channels.
    :param channel_multiplier: Multiplier for the number of channels after each pooling.
                               With this parameter set to 1, the channels are [1, 2, 4, 8, ...] for [depth, depth-1, ..., full_depth].
    :param features_dim: Dimension of output feature vector. Note that this number is multiplied by the number of stacked inside one observation.
    """

    def __init__(self, observation_space: gym.spaces.Box, channels_in: int=3, width: int=128, height: int=128, channel_multiplier: int=40, full_depth_conv1d: bool=True, full_depth_channels: int=8, features_dim: int=96, aux_obs_dim: int=10, aux_obs_features_dim: int=16, max_pool_kernel: int=4, separate_networks_for_stacks: bool=True, verbose: bool=False):
        self._channels_in = channels_in
        self._aux_obs_dim = aux_obs_dim
        self._aux_obs_features_dim = aux_obs_features_dim
        self._separate_networks_for_stacks = separate_networks_for_stacks
        self._verbose = verbose
        self._width = width
        self._height = height
        self._features_dim = features_dim
        self._n_stacks = observation_space.shape[0]
        super(ImageCnnFeaturesExtractor, self).__init__(observation_space, self._n_stacks * (features_dim + aux_obs_features_dim))
        resolution = width * height
        flatten_dim = resolution // (max_pool_kernel ** 2) ** 2 * full_depth_channels
        if not self._separate_networks_for_stacks:
            self.conv1 = ImageConvRelu(channels_in, channel_multiplier)
            self.pool1 = nn.MaxPool2d(max_pool_kernel)
            self.conv2 = ImageConvRelu(channel_multiplier, 2 * channel_multiplier)
            self.pool2 = nn.MaxPool2d(max_pool_kernel)
            self.full_depth_conv = ImageConvRelu(2 * channel_multiplier, full_depth_channels, kernel_size=1 if full_depth_conv1d else 3, padding=0)
            self.flatten = torch.nn.Flatten()
            self.linear = LinearRelu(flatten_dim, features_dim)
            if self._aux_obs_dim != 0:
                self.aux_obs_linear = LinearRelu(self._aux_obs_dim, aux_obs_features_dim)
        else:
            self.conv1 = torch.nn.ModuleList([ImageConvRelu(channels_in, channel_multiplier) for _ in range(self._n_stacks)])
            self.pool1 = torch.nn.ModuleList([nn.MaxPool2d(max_pool_kernel) for _ in range(self._n_stacks)])
            self.conv2 = torch.nn.ModuleList([ImageConvRelu(channel_multiplier, 2 * channel_multiplier) for _ in range(self._n_stacks)])
            self.pool2 = torch.nn.ModuleList([nn.MaxPool2d(max_pool_kernel) for _ in range(self._n_stacks)])
            self.full_depth_conv = torch.nn.ModuleList([ImageConvRelu(2 * channel_multiplier, full_depth_channels, kernel_size=1 if full_depth_conv1d else 3, padding=0) for _ in range(self._n_stacks)])
            self.flatten = torch.nn.ModuleList([torch.nn.Flatten() for _ in range(self._n_stacks)])
            self.linear = torch.nn.ModuleList([LinearRelu(flatten_dim, features_dim) for _ in range(self._n_stacks)])
            if self._aux_obs_dim != 0:
                self.aux_obs_linear = torch.nn.ModuleList([LinearRelu(self._aux_obs_dim, aux_obs_features_dim) for _ in range(self._n_stacks)])
        number_of_learnable_parameters = sum((p.numel() for p in self.parameters() if p.requires_grad))
        print(f'Initialised ImageCnnFeaturesExtractor with {number_of_learnable_parameters} parameters')
        if verbose:
            print(self)

    def forward(self, obs):
        data = copy.deepcopy(obs[0])
        aux_obs = obs[1]
        if not self._separate_networks_for_stacks:
            data = self.conv1(data)
            data = self.pool1(data)
            data = self.conv2(data)
            data = self.pool2(data)
            data = self.full_depth_conv(data)
            data = self.flatten(data)
            data = self.linear(data)
            data = data.view(-1, self._n_stacks * data.shape[-1])
            if self._aux_obs_dim != 0:
                aux_data = self.aux_obs_linear(aux_obs.view(-1, self._aux_obs_dim))
                aux_data = aux_data.view(-1, self._n_stacks * self._aux_obs_features_dim)
                data = torch.cat((data, aux_data), dim=1)
        else:
            for i in range(self._n_stacks):
                data[i] = self.conv1[i](data[i])
                data[i] = self.pool1[i](data[i])
                data[i] = self.conv2[i](data[i])
                data[i] = self.pool2[i](data[i])
                data[i] = self.full_depth_conv[i](data[i])
                data[i] = self.flatten[i](data[i])
                data[i] = self.linear[i](data[i])
                if self._aux_obs_dim != 0:
                    aux_data = self.aux_obs_linear[i](aux_obs[:, i, :])
                    data[i] = torch.cat((data[i], aux_data), dim=1)
            data = torch.cat(data, dim=1)
        return data

def __init__(self, observation_space: gym.spaces.Box, channels_in: int=3, width: int=128, height: int=128, channel_multiplier: int=40, full_depth_conv1d: bool=True, full_depth_channels: int=8, features_dim: int=96, aux_obs_dim: int=10, aux_obs_features_dim: int=16, max_pool_kernel: int=4, separate_networks_for_stacks: bool=True, verbose: bool=False):
    self._channels_in = channels_in
    self._aux_obs_dim = aux_obs_dim
    self._aux_obs_features_dim = aux_obs_features_dim
    self._separate_networks_for_stacks = separate_networks_for_stacks
    self._verbose = verbose
    self._width = width
    self._height = height
    self._features_dim = features_dim
    self._n_stacks = observation_space.shape[0]
    super(ImageCnnFeaturesExtractor, self).__init__(observation_space, self._n_stacks * (features_dim + aux_obs_features_dim))
    resolution = width * height
    flatten_dim = resolution // (max_pool_kernel ** 2) ** 2 * full_depth_channels
    if not self._separate_networks_for_stacks:
        self.conv1 = ImageConvRelu(channels_in, channel_multiplier)
        self.pool1 = nn.MaxPool2d(max_pool_kernel)
        self.conv2 = ImageConvRelu(channel_multiplier, 2 * channel_multiplier)
        self.pool2 = nn.MaxPool2d(max_pool_kernel)
        self.full_depth_conv = ImageConvRelu(2 * channel_multiplier, full_depth_channels, kernel_size=1 if full_depth_conv1d else 3, padding=0)
        self.flatten = torch.nn.Flatten()
        self.linear = LinearRelu(flatten_dim, features_dim)
        if self._aux_obs_dim != 0:
            self.aux_obs_linear = LinearRelu(self._aux_obs_dim, aux_obs_features_dim)
    else:
        self.conv1 = torch.nn.ModuleList([ImageConvRelu(channels_in, channel_multiplier) for _ in range(self._n_stacks)])
        self.pool1 = torch.nn.ModuleList([nn.MaxPool2d(max_pool_kernel) for _ in range(self._n_stacks)])
        self.conv2 = torch.nn.ModuleList([ImageConvRelu(channel_multiplier, 2 * channel_multiplier) for _ in range(self._n_stacks)])
        self.pool2 = torch.nn.ModuleList([nn.MaxPool2d(max_pool_kernel) for _ in range(self._n_stacks)])
        self.full_depth_conv = torch.nn.ModuleList([ImageConvRelu(2 * channel_multiplier, full_depth_channels, kernel_size=1 if full_depth_conv1d else 3, padding=0) for _ in range(self._n_stacks)])
        self.flatten = torch.nn.ModuleList([torch.nn.Flatten() for _ in range(self._n_stacks)])
        self.linear = torch.nn.ModuleList([LinearRelu(flatten_dim, features_dim) for _ in range(self._n_stacks)])
        if self._aux_obs_dim != 0:
            self.aux_obs_linear = torch.nn.ModuleList([LinearRelu(self._aux_obs_dim, aux_obs_features_dim) for _ in range(self._n_stacks)])
    number_of_learnable_parameters = sum((p.numel() for p in self.parameters() if p.requires_grad))
    print(f'Initialised ImageCnnFeaturesExtractor with {number_of_learnable_parameters} parameters')
    if verbose:
        print(self)

class ManipulationGazeboEnvRandomizer(gazebo_env_randomizer.GazeboEnvRandomizer, randomizers.abc.PhysicsRandomizer, randomizers.abc.TaskRandomizer, abc.ABC):
    """
    Basic randomizer of environments for robotic manipulation inside Ignition Gazebo. This randomizer
    also populates the simulated world with robot, terrain, lighting and other entities.
    """
    POST_RANDOMIZATION_MAX_STEPS = 50

    def __init__(self, env: MakeEnvCallable, physics_rollouts_num: int=0, gravity: Tuple[float, float, float]=(0.0, 0.0, -9.80665), gravity_std: Tuple[float, float, float]=(0.0, 0.0, 0.0232), plugin_scene_broadcaster: bool=False, plugin_user_commands: bool=False, plugin_sensors_render_engine: str='ogre2', robot_spawn_position: Tuple[float, float, float]=(0.0, 0.0, 0.0), robot_spawn_quat_xyzw: Tuple[float, float, float, float]=(0.0, 0.0, 0.0, 1.0), robot_random_pose: bool=False, robot_random_spawn_volume: Tuple[float, float, float]=(1.0, 1.0, 0.0), robot_random_joint_positions: bool=False, robot_random_joint_positions_std: float=0.1, robot_random_joint_positions_above_object_spawn: bool=False, robot_random_joint_positions_above_object_spawn_elevation: float=0.2, robot_random_joint_positions_above_object_spawn_xy_randomness: float=0.2, camera_enable: bool=True, camera_type: str='rgbd_camera', camera_relative_to: str='base_link', camera_width: int=128, camera_height: int=128, camera_image_format: str='R8G8B8', camera_update_rate: int=10, camera_horizontal_fov: float=np.pi / 3.0, camera_vertical_fov: float=np.pi / 3.0, camera_clip_color: Tuple[float, float]=(0.01, 1000.0), camera_clip_depth: Tuple[float, float]=(0.05, 10.0), camera_noise_mean: float=None, camera_noise_stddev: float=None, camera_publish_color: bool=False, camera_publish_depth: bool=False, camera_publish_points: bool=False, camera_spawn_position: Tuple[float, float, float]=(0, 0, 1), camera_spawn_quat_xyzw: Tuple[float, float, float, float]=(0, 0.70710678118, 0, 0.70710678118), camera_random_pose_rollouts_num: int=1, camera_random_pose_mode: str='orbit', camera_random_pose_orbit_distance: float=1.0, camera_random_pose_orbit_height_range: Tuple[float, float]=(0.1, 0.7), camera_random_pose_orbit_ignore_arc_behind_robot: float=np.pi / 8, camera_random_pose_select_position_options: List[Tuple[float, float, float]]=[], camera_random_pose_focal_point_z_offset: float=0.0, terrain_enable: bool=True, terrain_type: str='flat', terrain_spawn_position: Tuple[float, float, float]=(0, 0, 0), terrain_spawn_quat_xyzw: Tuple[float, float, float, float]=(0, 0, 0, 1), terrain_size: Tuple[float, float]=(1.0, 1.0), terrain_model_rollouts_num: int=1, light_enable: bool=True, light_type: str='sun', light_direction: Tuple[float, float, float]=(0.5, -0.25, -0.75), light_random_minmax_elevation: Tuple[float, float]=(-0.15, -0.65), light_color: Tuple[float, float, float, float]=(1.0, 1.0, 1.0, 1.0), light_distance: float=1000.0, light_visual: bool=True, light_radius: float=25.0, light_model_rollouts_num: int=1, object_enable: bool=True, object_type: str='box', objects_relative_to: str='base_link', object_static: bool=False, object_collision: bool=True, object_visual: bool=True, object_color: Tuple[float, float, float, float]=(0.8, 0.8, 0.8, 1.0), object_dimensions: List[float]=[0.05, 0.05, 0.05], object_mass: float=0.1, object_count: int=1, object_randomize_count: bool=False, object_spawn_position: Tuple[float, float, float]=(0.0, 0.0, 0.0), object_random_pose: bool=True, object_random_spawn_position_segments: List[Tuple[float, float, float]]=[], object_random_spawn_position_update_workspace_centre: bool=False, object_random_spawn_volume: Tuple[float, float, float]=(0.5, 0.5, 0.5), object_models_rollouts_num: int=1, underworld_collision_plane: bool=True, boundary_collision_walls: bool=False, collision_plane_offset: float=1.0, visualise_workspace: bool=False, visualise_spawn_volume: bool=False, **kwargs):
        if physics_rollouts_num != 0:
            raise TypeError('Proper physics randomization at each reset is not yet implemented. Please set `physics_rollouts_num=0`.')
        kwargs.update({'camera_type': camera_type, 'camera_width': camera_width, 'camera_height': camera_height})
        randomizers.abc.TaskRandomizer.__init__(self)
        randomizers.abc.PhysicsRandomizer.__init__(self, randomize_after_rollouts_num=physics_rollouts_num)
        gazebo_env_randomizer.GazeboEnvRandomizer.__init__(self, env=env, physics_randomizer=self, **kwargs)
        self._gravity = gravity
        self._gravity_std = gravity_std
        self._plugin_scene_broadcaster = plugin_scene_broadcaster
        self._plugin_user_commands = plugin_user_commands
        self._plugin_sensors_render_engine = plugin_sensors_render_engine
        self._robot_spawn_position = robot_spawn_position
        self._robot_spawn_quat_xyzw = robot_spawn_quat_xyzw
        self._robot_random_pose = robot_random_pose
        self._robot_random_spawn_volume = robot_random_spawn_volume
        self._robot_random_joint_positions = robot_random_joint_positions
        self._robot_random_joint_positions_std = robot_random_joint_positions_std
        self._robot_random_joint_positions_above_object_spawn = robot_random_joint_positions_above_object_spawn
        self._robot_random_joint_positions_above_object_spawn_elevation = robot_random_joint_positions_above_object_spawn_elevation
        self._robot_random_joint_positions_above_object_spawn_xy_randomness = robot_random_joint_positions_above_object_spawn_xy_randomness
        self._camera_enable = camera_enable
        self._camera_type = camera_type
        self._camera_relative_to = camera_relative_to
        self._camera_width = camera_width
        self._camera_height = camera_height
        self._camera_image_format = camera_image_format
        self._camera_update_rate = camera_update_rate
        self._camera_horizontal_fov = camera_horizontal_fov
        self._camera_vertical_fov = camera_vertical_fov
        self._camera_clip_color = camera_clip_color
        self._camera_clip_depth = camera_clip_depth
        self._camera_noise_mean = camera_noise_mean
        self._camera_noise_stddev = camera_noise_stddev
        self._camera_publish_color = camera_publish_color
        self._camera_publish_depth = camera_publish_depth
        self._camera_publish_points = camera_publish_points
        self._camera_spawn_position = camera_spawn_position
        self._camera_spawn_quat_xyzw = camera_spawn_quat_xyzw
        self._camera_random_pose_rollouts_num = camera_random_pose_rollouts_num
        self._camera_random_pose_mode = camera_random_pose_mode
        self._camera_random_pose_orbit_distance = camera_random_pose_orbit_distance
        self._camera_random_pose_orbit_height_range = camera_random_pose_orbit_height_range
        self._camera_random_pose_orbit_ignore_arc_behind_robot = camera_random_pose_orbit_ignore_arc_behind_robot
        self._camera_random_pose_select_position_options = camera_random_pose_select_position_options
        self._camera_random_pose_focal_point_z_offset = camera_random_pose_focal_point_z_offset
        self._terrain_enable = terrain_enable
        self._terrain_spawn_position = terrain_spawn_position
        self._terrain_spawn_quat_xyzw = terrain_spawn_quat_xyzw
        self._terrain_size = terrain_size
        self._terrain_model_rollouts_num = terrain_model_rollouts_num
        self._light_enable = light_enable
        self._light_direction = light_direction
        self._light_random_minmax_elevation = light_random_minmax_elevation
        self._light_color = light_color
        self._light_distance = light_distance
        self._light_visual = light_visual
        self._light_radius = light_radius
        self._light_model_rollouts_num = light_model_rollouts_num
        self._object_enable = object_enable
        self._objects_relative_to = objects_relative_to
        self._object_static = object_static
        self._object_collision = object_collision
        self._object_visual = object_visual
        self._object_color = object_color
        self._object_dimensions = object_dimensions
        self._object_mass = object_mass
        self._object_count = object_count
        self._object_randomize_count = object_randomize_count
        self._object_spawn_position = object_spawn_position
        self._object_random_pose = object_random_pose
        self._object_random_spawn_position_segments = object_random_spawn_position_segments
        self._object_random_spawn_position_update_workspace_centre = object_random_spawn_position_update_workspace_centre
        self._object_random_spawn_volume = object_random_spawn_volume
        self._object_models_rollouts_num = object_models_rollouts_num
        self._underworld_collision_plane = underworld_collision_plane
        self._boundary_collision_walls = boundary_collision_walls
        self._collision_plane_offset = collision_plane_offset
        if self._collision_plane_offset < 0.0:
            self._collision_plane_offset *= -1.0
        self._visualise_workspace = visualise_workspace
        self._visualise_spawn_volume = visualise_spawn_volume
        self.__terrain_model_class = models.get_terrain_model_class(terrain_type)
        self.__is_terrain_type_randomizable = models.is_terrain_type_randomizable(terrain_type)
        self.__light_model_class = models.get_light_model_class(light_type)
        self.__is_light_type_randomizable = models.is_light_type_randomizable(light_type)
        self.__object_model_class = models.get_object_model_class(object_type)
        self.__is_object_type_randomizable = models.is_object_type_randomizable(object_type)
        if self._object_randomize_count:
            self.__object_max_count = self._object_count
        self.__camera_pose_rollout_counter = camera_random_pose_rollouts_num
        self.__terrain_model_rollout_counter = terrain_model_rollouts_num
        self.__light_model_rollout_counter = light_model_rollouts_num
        self.__object_models_rollout_counter = object_models_rollouts_num
        self.__is_camera_attached = False
        self.__env_initialised = False
        self.__object_positions = {}

    def init_physics_preset(self, task: SupportedTasks):
        self.set_gravity(task=task)

    def randomize_physics(self, task: SupportedTasks, **kwargs):
        self.set_gravity(task=task)

    def set_gravity(self, task: SupportedTasks):
        if not task.world.to_gazebo().set_gravity((task.np_random.normal(loc=self._gravity[0], scale=self._gravity_std[0]), task.np_random.normal(loc=self._gravity[1], scale=self._gravity_std[1]), task.np_random.normal(loc=self._gravity[2], scale=self._gravity_std[2]))):
            raise RuntimeError('Failed to set the gravity')

    def get_engine(self):
        return scenario.PhysicsEngine_dart

    def randomize_task(self, task: SupportedTasks, **kwargs):
        """
        Randomization of the task, which is called on each reset of the environment.
        Note that this randomizer reset is called before `reset_task()`.
        """
        if 'gazebo' not in kwargs:
            raise ValueError('Randomizer does not have access to the gazebo interface')
        gazebo = kwargs['gazebo']
        self.internal_overrides(task=task)
        self.external_overrides(task=task)
        if not self.__env_initialised:
            self.init_env(task=task, gazebo=gazebo)
            self.__env_initialised = True
        self.pre_randomization(task=task)
        self.randomize_models(task=task, gazebo=gazebo)
        self.post_randomization(task, gazebo)

    def init_env(self, task: SupportedTasks, gazebo: scenario.GazeboSimulator):
        """
        Initialise an instance of the environment before the very first iteration
        """
        set_log_level(log_level=task.get_logger().get_effective_level().name)
        if not gazebo.run(paused=True):
            raise RuntimeError('Failed to execute a paused Gazebo run')
        self._object_spawn_position = (self._object_spawn_position[0], self._object_spawn_position[1], self._object_spawn_position[2] + task.robot_model_class.BASE_LINK_Z_OFFSET)
        self._camera_random_pose_focal_point_z_offset += task.robot_model_class.BASE_LINK_Z_OFFSET
        self._camera_relative_to = task.substitute_special_frame(self._camera_relative_to)
        self._objects_relative_to = task.substitute_special_frame(self._objects_relative_to)
        self.init_physics_preset(task=task)
        self.init_world_plugins(task=task, gazebo=gazebo)
        self.init_models(task=task, gazebo=gazebo)

    def init_world_plugins(self, task: SupportedTasks, gazebo: scenario.GazeboSimulator):
        if self._plugin_scene_broadcaster:
            if not gazebo.scene_broadcaster_active(task.substitute_special_frame('world')):
                task.get_logger().info('Inserting world plugins for broadcasting scene to GUI clients...')
                task.world.to_gazebo().insert_world_plugin('ignition-gazebo-scene-broadcaster-system', 'ignition::gazebo::systems::SceneBroadcaster')
                if not gazebo.run(paused=True):
                    raise RuntimeError('Failed to execute a paused Gazebo run')
        if self._plugin_user_commands:
            task.get_logger().info('Inserting world plugins to enable user commands...')
            task.world.to_gazebo().insert_world_plugin('ignition-gazebo-user-commands-system', 'ignition::gazebo::systems::UserCommands')
            if not gazebo.run(paused=True):
                raise RuntimeError('Failed to execute a paused Gazebo run')
        if self._camera_enable:
            task.get_logger().info(f'Inserting world plugins for sensors with {self._plugin_sensors_render_engine} rendering engine...')
            task.world.to_gazebo().insert_world_plugin('libignition-gazebo-sensors-system.so', 'ignition::gazebo::systems::Sensors', f"<sdf version='1.9'><render_engine>{self._plugin_sensors_render_engine}</render_engine></sdf>")
            if not gazebo.run(paused=True):
                raise RuntimeError('Failed to execute a paused Gazebo run')

    def init_models(self, task: SupportedTasks, gazebo: scenario.GazeboSimulator):
        """
        Initialise all models that are persistent throughout the entire training (they do not need to be re-spawned).
        All other models that need to be re-spawned on each reset are ignored here
        """
        model_names = task.world.to_gazebo().model_names()
        if len(model_names) > 0:
            task.get_logger().warn(f'Before initialisation, the world already contains the following models:\n\t{model_names}')
        if self._light_enable and (not self.__light_model_randomizer_enabled()):
            task.get_logger().info('Inserting default light into the environment...')
            self.add_default_light(task=task, gazebo=gazebo)
        if self._terrain_enable and (not self.__terrain_model_randomizer_enabled()):
            task.get_logger().info('Inserting default terrain into the environment...')
            self.add_default_terrain(task=task, gazebo=gazebo)
        task.get_logger().info('Inserting robot into the environment...')
        self.add_robot(task=task, gazebo=gazebo)
        if self._camera_enable:
            task.get_logger().info('Inserting camera into the environment...')
            self.add_camera(task=task, gazebo=gazebo)
        if self._object_enable and (not self.__object_models_randomizer_enabled()):
            task.get_logger().info('Inserting default objects into the environment...')
            self.add_default_objects(task=task, gazebo=gazebo)
        if self._underworld_collision_plane:
            task.get_logger().info('Inserting invisible plane below the terrain into the environment...')
            self.add_underworld_collision_plane(task=task, gazebo=gazebo)
        if self._boundary_collision_walls:
            task.get_logger().info('Inserting invisible planes around the terrain into the environment...')
            self.add_boundary_collision_walls(task=task, gazebo=gazebo)
        if self._visualise_workspace:
            self.visualise_workspace(task=task, gazebo=gazebo)
        if self._visualise_spawn_volume:
            self.visualise_spawn_volume(task=task, gazebo=gazebo)

    def add_robot(self, task: SupportedTasks, gazebo: scenario.GazeboSimulator):
        """
        Configure and insert robot into the simulation
        """
        self.robot = task.robot_model_class(world=task.world, name=task.robot_name, prefix=task.robot_prefix, position=self._robot_spawn_position, orientation=quat_to_wxyz(self._robot_spawn_quat_xyzw), initial_arm_joint_positions=task.initial_arm_joint_positions, initial_gripper_joint_positions=task.initial_gripper_joint_positions)
        task.robot_name = self.robot.name()
        robot_gazebo = self.robot.to_gazebo()
        for gripper_link_name in self.robot.gripper_link_names:
            finger = robot_gazebo.get_link(link_name=gripper_link_name)
            finger.enable_contact_detection(True)
        if self.robot.is_mobile:
            for wheel_link_name in self.robot.wheel_link_names:
                wheel = robot_gazebo.get_link(link_name=wheel_link_name)
                wheel.enable_contact_detection(True)
        if not gazebo.run(paused=True):
            raise RuntimeError('Failed to execute a paused Gazebo run')
        self.reset_robot_joint_positions(task=task, gazebo=gazebo, above_object_spawn=False, randomize=False)

    def add_camera(self, task: SupportedTasks, gazebo: scenario.GazeboSimulator):
        """
        Configure and insert camera into the simulation. Camera is places with respect to the robot
        """
        if task.world.to_gazebo().name() == self._camera_relative_to:
            camera_position = self._camera_spawn_position
            camera_quat_wxyz = quat_to_wxyz(self._camera_spawn_quat_xyzw)
        else:
            camera_position, camera_quat_wxyz = transform_move_to_model_pose(world=task.world, position=self._camera_spawn_position, quat=quat_to_wxyz(self._camera_spawn_quat_xyzw), target_model=self.robot, target_link=self._camera_relative_to, xyzw=False)
        self.camera = models.Camera(world=task.world, position=camera_position, orientation=camera_quat_wxyz, camera_type=self._camera_type, width=self._camera_width, height=self._camera_height, image_format=self._camera_image_format, update_rate=self._camera_update_rate, horizontal_fov=self._camera_horizontal_fov, vertical_fov=self._camera_vertical_fov, clip_color=self._camera_clip_color, clip_depth=self._camera_clip_depth, noise_mean=self._camera_noise_mean, noise_stddev=self._camera_noise_stddev, ros2_bridge_color=self._camera_publish_color, ros2_bridge_depth=self._camera_publish_depth, ros2_bridge_points=self._camera_publish_points)
        if not gazebo.run(paused=True):
            raise RuntimeError('Failed to execute a paused Gazebo run')
        if task.world.to_gazebo().name() != self._camera_relative_to:
            if not self.robot.to_gazebo().attach_link(self._camera_relative_to, self.camera.name(), self.camera.link_name):
                raise Exception('Cannot attach camera link to robot')
            self.__is_camera_attached = True
            if not gazebo.run(paused=True):
                raise RuntimeError('Failed to execute a paused Gazebo run')
        task.tf2_broadcaster.broadcast_tf(parent_frame_id=self._camera_relative_to, child_frame_id=self.camera.frame_id, translation=self._camera_spawn_position, rotation=self._camera_spawn_quat_xyzw, xyzw=True)

    def add_default_terrain(self, task: SupportedTasks, gazebo: scenario.GazeboSimulator):
        """
        Configure and insert default terrain into the simulation
        """
        self.terrain = self.__terrain_model_class(world=task.world, position=self._terrain_spawn_position, orientation=quat_to_wxyz(self._terrain_spawn_quat_xyzw), size=self._terrain_size, np_random=task.np_random)
        task.terrain_name = self.terrain.name()
        for link_name in self.terrain.link_names():
            link = self.terrain.to_gazebo().get_link(link_name=link_name)
            link.enable_contact_detection(True)
        if not gazebo.run(paused=True):
            raise RuntimeError('Failed to execute a paused Gazebo run')

    def add_default_light(self, task: SupportedTasks, gazebo: scenario.GazeboSimulator):
        """
        Configure and insert default light into the simulation
        """
        self.light = self.__light_model_class(world=task.world, direction=self._light_direction, minmax_elevation=self._light_random_minmax_elevation, color=self._light_color, distance=self._light_distance, visual=self._light_visual, radius=self._light_radius, np_random=task.np_random)
        if not gazebo.run(paused=True):
            raise RuntimeError('Failed to execute a paused Gazebo run')

    def add_default_objects(self, task: SupportedTasks, gazebo: scenario.GazeboSimulator):
        """
        Configure and insert default object into the simulation
        """
        while len(self.task.object_names) < self._object_count:
            if self._object_count > 1:
                object_position, object_quat_wxyz = self.get_random_object_pose(task=task, centre=self._object_spawn_position, volume=self._object_random_spawn_volume)
            else:
                object_position = self._object_spawn_position
                object_quat_wxyz = (1.0, 0.0, 0.0, 0.0)
                if task.world.to_gazebo().name() != self._objects_relative_to:
                    object_position, object_quat_wxyz = transform_move_to_model_pose(world=task.world, position=object_position, quat=object_quat_wxyz, target_model=self.robot, target_link=self._objects_relative_to, xyzw=False)
            try:
                object_model = self.__object_model_class(world=task.world, position=object_position, orientation=object_quat_wxyz, size=self._object_dimensions, radius=self._object_dimensions[0], length=self._object_dimensions[1], mass=self._object_mass, collision=self._object_collision, visual=self._object_visual, static=self._object_static, color=self._object_color)
                model_name = object_model.name()
                task.object_names.append(model_name)
                for link_name in object_model.link_names():
                    link = object_model.to_gazebo().get_link(link_name=link_name)
                    link.enable_contact_detection(True)
            except Exception as ex:
                task.get_logger().warn(f'Model could not be inserted. Reason: {ex}')
        if not gazebo.run(paused=True):
            raise RuntimeError('Failed to execute a paused Gazebo run')

    def add_underworld_collision_plane(self, task: SupportedTasks, gazebo: scenario.GazeboSimulator):
        """
        Add an infinitely large collision plane below the terrain in order to prevent object from falling into the abyss forever
        """
        models.Plane(name='_collision_plane_B', world=task.world, position=(0.0, 0.0, self._terrain_spawn_position[2] - self._collision_plane_offset), orientation=(1.0, 0.0, 0.0, 0.0), direction=(0.0, 0.0, 1.0), visual=False, collision=True, friction=1000.0)
        if not gazebo.run(paused=True):
            raise RuntimeError('Failed to execute a paused Gazebo run')

    def add_boundary_collision_walls(self, task: SupportedTasks, gazebo: scenario.GazeboSimulator):
        """
        Add an infinitely large collision planes around the terrain in order to prevent object from going into the abyss forever
        """
        models.Plane(name='_collision_plane_N', world=task.world, position=(self._terrain_spawn_position[0] + self._terrain_size[0] / 2 + self._collision_plane_offset, 0.0, 0.0), orientation=(1.0, 0.0, 0.0, 0.0), direction=(-1.0, 0.0, 0.0), visual=False, collision=True, friction=1000.0)
        models.Plane(name='_collision_plane_S', world=task.world, position=(self._terrain_spawn_position[0] - self._terrain_size[0] / 2 - self._collision_plane_offset, 0.0, 0.0), orientation=(1.0, 0.0, 0.0, 0.0), direction=(1.0, 0.0, 0.0), visual=False, collision=True, friction=1000.0)
        models.Plane(name='_collision_plane_E', world=task.world, position=(0.0, self._terrain_spawn_position[1] + self._terrain_size[1] / 2 + self._collision_plane_offset, 0.0), orientation=(1.0, 0.0, 0.0, 0.0), direction=(0.0, -1.0, 0.0), visual=False, collision=True, friction=1000.0)
        models.Plane(name='_collision_plane_W', world=task.world, position=(0.0, self._terrain_spawn_position[1] - self._terrain_size[1] / 2 - self._collision_plane_offset, 0.0), orientation=(1.0, 0.0, 0.0, 0.0), direction=(0.0, 1.0, 0.0), visual=False, collision=True, friction=1000.0)
        if not gazebo.run(paused=True):
            raise RuntimeError('Failed to execute a paused Gazebo run')

    def randomize_models(self, task: SupportedTasks, gazebo: scenario.GazeboSimulator):
        """
        Randomize models if needed
        """
        if self._light_enable and self._light_model_expired():
            self.randomize_light(task=task, gazebo=gazebo)
        if self.robot.is_mobile:
            self.reset_robot_pose(task=task, gazebo=gazebo, randomize=self._robot_random_pose)
        self.reset_robot_joint_positions(task=task, gazebo=gazebo, above_object_spawn=self._robot_random_joint_positions_above_object_spawn, randomize=self._robot_random_joint_positions)
        if self._camera_enable and self._camera_pose_expired():
            self.randomize_camera_pose(task=task, gazebo=gazebo, mode=self._camera_random_pose_mode)
        if self._object_enable:
            self.__object_positions.clear()
            if self._object_models_expired():
                self.randomize_object_models(task=task, gazebo=gazebo)
            elif self._object_random_pose:
                self.object_random_pose(task=task, gazebo=gazebo)
            else:
                self.reset_default_object_pose(task=task, gazebo=gazebo)
        if self._terrain_enable and self._terrain_model_expired():
            self.randomize_terrain(task=task, gazebo=gazebo)

    def reset_robot_pose(self, task: SupportedTasks, gazebo: scenario.GazeboSimulator, randomize: bool=False):
        if randomize:
            position = [self._robot_spawn_position[0] + task.np_random.uniform(-self._robot_random_spawn_volume[0] / 2, self._robot_random_spawn_volume[0] / 2), self._robot_spawn_position[1] + task.np_random.uniform(-self._robot_random_spawn_volume[1] / 2, self._robot_random_spawn_volume[1] / 2), self._robot_spawn_position[2] + task.np_random.uniform(-self._robot_random_spawn_volume[2] / 2, self._robot_random_spawn_volume[2] / 2)]
            quat_xyzw = Rotation.from_euler('xyz', (0, 0, task.np_random.uniform(-np.pi, np.pi))).as_quat()
        else:
            position = self._robot_spawn_position
            quat_xyzw = self._robot_spawn_quat_xyzw
        gazebo_robot = self.robot.to_gazebo()
        gazebo_robot.reset_base_pose(position, quat_to_wxyz(quat_xyzw))
        gazebo_robot.reset_base_world_velocity([0.0, 0.0, 0.0], [0.0, 0.0, 0.0])
        if not gazebo.run(paused=True):
            raise RuntimeError('Failed to execute a paused Gazebo run')

    def reset_robot_joint_positions(self, task: SupportedTasks, gazebo: scenario.GazeboSimulator, above_object_spawn: bool=False, randomize: bool=False):
        if task._use_servo:
            if task.servo.is_enabled:
                task.servo.servo()
                task.servo.disable(sync=True)
        gazebo_robot = self.robot.to_gazebo()
        if above_object_spawn:
            if randomize:
                rnd_displacement = self._robot_random_joint_positions_above_object_spawn_xy_randomness * task.np_random.uniform((-self._object_random_spawn_volume[0], -self._object_random_spawn_volume[1]), self._object_random_spawn_volume[:2])
                position = (self._object_spawn_position[0] + rnd_displacement[0], self._object_spawn_position[1] + rnd_displacement[1], self._object_spawn_position[2] + self._robot_random_joint_positions_above_object_spawn_elevation)
                quat_xyzw = Rotation.from_euler('xyz', (0, np.pi, task.np_random.uniform(-np.pi, np.pi))).as_quat()
            else:
                position = (self._object_spawn_position[0], self._object_spawn_position[1], self._object_spawn_position[2] + self._robot_random_joint_positions_above_object_spawn_elevation)
                quat_xyzw = (1.0, 0.0, 0.0, 0.0)
            joint_configuration = task.moveit2.compute_ik(position=position, quat_xyzw=quat_xyzw, start_joint_state=task.initial_arm_joint_positions)
            if joint_configuration is not None:
                arm_joint_positions = joint_configuration.position[:len(task.initial_arm_joint_positions)]
            else:
                task.get_logger().warn('Robot configuration could not be reset above the object spawn. Using initial arm joint positions instead.')
                arm_joint_positions = task.initial_arm_joint_positions
        else:
            arm_joint_positions = task.initial_arm_joint_positions
        if randomize:
            for joint_position in arm_joint_positions:
                joint_position += task.np_random.normal(loc=0.0, scale=self._robot_random_joint_positions_std)
        if not gazebo_robot.reset_joint_positions(arm_joint_positions, self.robot.arm_joint_names):
            raise RuntimeError('Failed to reset robot joint positions')
        if not gazebo_robot.reset_joint_velocities([0.0] * len(self.robot.arm_joint_names), self.robot.arm_joint_names):
            raise RuntimeError('Failed to reset robot joint velocities')
        if task._enable_gripper and self.robot.gripper_joint_names:
            if not gazebo_robot.reset_joint_positions(task.initial_gripper_joint_positions, self.robot.gripper_joint_names):
                raise RuntimeError('Failed to reset gripper joint positions')
            if not gazebo_robot.reset_joint_velocities([0.0] * len(self.robot.gripper_joint_names), self.robot.gripper_joint_names):
                raise RuntimeError('Failed to reset gripper joint velocities')
        if self.robot.passive_joint_names:
            if not gazebo_robot.reset_joint_velocities([0.0] * len(self.robot.passive_joint_names), self.robot.passive_joint_names):
                raise RuntimeError('Failed to reset passive joint velocities')
        if not gazebo.step():
            raise RuntimeError('Failed to execute an unpaused Gazebo step')
        task.moveit2.force_reset_executing_state()
        task.moveit2.reset_controller(joint_state=arm_joint_positions)
        if task._enable_gripper:
            if self.robot.CLOSED_GRIPPER_JOINT_POSITIONS == task.initial_gripper_joint_positions:
                task.gripper.close()
            else:
                task.gripper.open()

    def randomize_camera_pose(self, task: SupportedTasks, gazebo: scenario.GazeboSimulator, mode: str):
        if 'orbit' == mode:
            camera_position, camera_quat_xyzw = self.get_random_camera_pose_orbit(task=task, centre=self._object_spawn_position, distance=self._camera_random_pose_orbit_distance, height=self._camera_random_pose_orbit_height_range, ignore_arc_behind_robot=self._camera_random_pose_orbit_ignore_arc_behind_robot, focal_point_z_offset=self._camera_random_pose_focal_point_z_offset)
        elif 'select_random' == mode:
            camera_position, camera_quat_xyzw = self.get_random_camera_pose_sample_random(task=task, centre=self._object_spawn_position, options=self._camera_random_pose_select_position_options)
        elif 'select_nearest' == mode:
            camera_position, camera_quat_xyzw = self.get_random_camera_pose_sample_nearest(centre=self._object_spawn_position, options=self._camera_random_pose_select_position_options)
        else:
            raise TypeError('Invalid mode for camera pose randomization.')
        if task.world.to_gazebo().name() == self._camera_relative_to:
            transformed_camera_position = camera_position
            transformed_camera_quat_wxyz = quat_to_wxyz(camera_quat_xyzw)
        else:
            transformed_camera_position, transformed_camera_quat_wxyz = transform_move_to_model_pose(world=task.world, position=camera_position, quat=quat_to_wxyz(camera_quat_xyzw), target_model=self.robot, target_link=self._camera_relative_to, xyzw=False)
        if self.__is_camera_attached:
            if not self.robot.to_gazebo().detach_link(self._camera_relative_to, self.camera.name(), self.camera.link_name):
                raise Exception('Cannot detach camera link from robot')
            if not gazebo.run(paused=True):
                raise RuntimeError('Failed to execute a paused Gazebo run')
        camera_gazebo = self.camera.to_gazebo()
        camera_gazebo.reset_base_pose(transformed_camera_position, transformed_camera_quat_wxyz)
        if not gazebo.run(paused=True):
            raise RuntimeError('Failed to execute a paused Gazebo run')
        if self.__is_camera_attached:
            if not self.robot.to_gazebo().attach_link(self._camera_relative_to, self.camera.name(), self.camera.link_name):
                raise Exception('Cannot attach camera link to robot')
            if not gazebo.run(paused=True):
                raise RuntimeError('Failed to execute a paused Gazebo run')
        task.tf2_broadcaster.broadcast_tf(parent_frame_id=self._camera_relative_to, child_frame_id=self.camera.frame_id, translation=camera_position, rotation=camera_quat_xyzw, xyzw=True)

    def get_random_camera_pose_orbit(self, task: SupportedTasks, centre: Tuple[float, float, float], distance: float, height: Tuple[float, float], ignore_arc_behind_robot: float, focal_point_z_offset: float) -> Tuple[Tuple[float, float, float], Tuple[float, float, float, float]]:
        while True:
            position = task.np_random.uniform(low=(-1.0, -1.0, height[0]), high=(1.0, 1.0, height[1]))
            position /= np.linalg.norm(position)
            if abs(np.arctan2(position[0], position[1]) + np.pi / 2) > ignore_arc_behind_robot:
                break
        rpy = [0.0, np.arctan2(position[2] - focal_point_z_offset, np.linalg.norm(position[:2], 2)), np.arctan2(position[1], position[0]) + np.pi]
        quat_xyzw = Rotation.from_euler('xyz', rpy).as_quat()
        position *= distance
        position[:2] += centre[:2]
        return (position, quat_xyzw)

    def get_random_camera_pose_sample_random(self, task: SupportedTasks, centre: Tuple[float, float, float], options: List[Tuple[float, float, float]]) -> Tuple[Tuple[float, float, float], Tuple[float, float, float, float]]:
        selection = options[task.np_random.randint(len(options))]
        return self.get_random_camera_pose_sample_process(centre=centre, position=selection, focal_point_z_offset=self._camera_random_pose_focal_point_z_offset)

    def get_random_camera_pose_sample_nearest(self, centre: Tuple[float, float, float], options: List[Tuple[float, float, float]]) -> Tuple[Tuple[float, float, float], Tuple[float, float, float, float]]:
        dist_sqr = np.sum((np.array(options) - np.array(centre)) ** 2, axis=1)
        nearest = options[np.argmin(dist_sqr)]
        return self.get_random_camera_pose_sample_process(centre=centre, position=nearest, focal_point_z_offset=self._camera_random_pose_focal_point_z_offset)

    def get_random_camera_pose_sample_process(self, centre: Tuple[float, float, float], position: Tuple[float, float, float], focal_point_z_offset: float) -> Tuple[Tuple[float, float, float], Tuple[float, float, float, float]]:
        rpy = [0.0, np.arctan2(position[2] - focal_point_z_offset, np.linalg.norm((position[0] - centre[0], position[1] - centre[1]), 2)), np.arctan2(position[1] - centre[1], position[0] - centre[0]) + np.pi]
        quat_xyzw = Rotation.from_euler('xyz', rpy).as_quat()
        return (position, quat_xyzw)

    def randomize_terrain(self, task: SupportedTasks, gazebo: scenario.GazeboSimulator):
        if hasattr(self, 'terrain'):
            if not task.world.to_gazebo().remove_model(self.terrain.name()):
                raise RuntimeError(f'Failed to remove {self.terrain.name()}')
        orientation = [(1, 0, 0, 0), (0, 0, 0, 1), (0.70710678118, 0, 0, 0.70710678118), (0.70710678118, 0, 0, -0.70710678118)][task.np_random.randint(4)]
        self.terrain = self.__terrain_model_class(world=task.world, position=self._terrain_spawn_position, orientation=orientation, size=self._terrain_size, np_random=task.np_random)
        task.terrain_name = self.terrain.name()
        for link_name in self.terrain.link_names():
            link = self.terrain.to_gazebo().get_link(link_name=link_name)
            link.enable_contact_detection(True)
        if not gazebo.step():
            raise RuntimeError('Failed to execute an unpaused Gazebo run')

    def randomize_light(self, task: SupportedTasks, gazebo: scenario.GazeboSimulator):
        if hasattr(self, 'light'):
            if not task.world.to_gazebo().remove_model(self.light.name()):
                raise RuntimeError(f'Failed to remove {self.light.name()}')
        self.light = self.__light_model_class(world=task.world, direction=self._light_direction, minmax_elevation=self._light_random_minmax_elevation, color=self._light_color, distance=self._light_distance, visual=self._light_visual, radius=self._light_radius, np_random=task.np_random)
        if not gazebo.run(paused=True):
            raise RuntimeError('Failed to execute a paused Gazebo run')

    def reset_default_object_pose(self, task: SupportedTasks, gazebo: scenario.GazeboSimulator):
        assert len(task.object_names) == 1
        obj = task.world.to_gazebo().get_model(task.object_names[0]).to_gazebo()
        obj.reset_base_pose(self._object_spawn_position, (1.0, 0.0, 0.0, 0.0))
        obj.reset_base_world_velocity([0.0, 0.0, 0.0], [0.0, 0.0, 0.0])
        if not gazebo.run(paused=True):
            raise RuntimeError('Failed to execute a paused Gazebo run')

    def randomize_object_models(self, task: SupportedTasks, gazebo: scenario.GazeboSimulator):
        if len(self.task.object_names) > 0:
            for object_name in self.task.object_names:
                if not task.world.to_gazebo().remove_model(object_name):
                    raise RuntimeError(f'Failed to remove {object_name}')
            self.task.object_names.clear()
        while len(self.task.object_names) < self._object_count:
            position, quat_random = self.get_random_object_pose(task=task, centre=self._object_spawn_position, volume=self._object_random_spawn_volume)
            try:
                model = self.__object_model_class(world=task.world, position=position, orientation=quat_random, np_random=task.np_random)
                model_name = model.name()
                self.task.object_names.append(model_name)
                self.__object_positions[model_name] = position
                for link_name in model.link_names():
                    link = model.to_gazebo().get_link(link_name=link_name)
                    link.enable_contact_detection(True)
            except Exception as ex:
                task.get_logger().warn(f'Model could not be inserted: {ex}')
        if not gazebo.run(paused=True):
            raise RuntimeError('Failed to execute a paused Gazebo run')

    def object_random_pose(self, task: SupportedTasks, gazebo: scenario.GazeboSimulator):
        for object_name in self.task.object_names:
            position, quat_random = self.get_random_object_pose(task=task, centre=self._object_spawn_position, volume=self._object_random_spawn_volume)
            obj = task.world.to_gazebo().get_model(object_name).to_gazebo()
            obj.reset_base_pose(position, quat_random)
            obj.reset_base_world_velocity([0.0, 0.0, 0.0], [0.0, 0.0, 0.0])
            self.__object_positions[object_name] = position
        if not gazebo.run(paused=True):
            raise RuntimeError('Failed to execute a paused Gazebo run')

    def get_random_object_pose(self, task: SupportedTasks, centre: Tuple[float, float, float], volume: Tuple[float, float, float], name: str='', min_distance_to_other_objects: float=0.2, min_distance_decay_factor: float=0.95):
        is_too_close = True
        while is_too_close:
            object_position = [centre[0] + task.np_random.uniform(-volume[0] / 2, volume[0] / 2), centre[1] + task.np_random.uniform(-volume[1] / 2, volume[1] / 2), centre[2] + task.np_random.uniform(-volume[2] / 2, volume[2] / 2)]
            if task.world.to_gazebo().name() != self._objects_relative_to:
                object_position = transform_move_to_model_position(world=task.world, position=object_position, target_model=self.robot, target_link=self._objects_relative_to)
            is_too_close = False
            for existing_object_name, existing_object_position in self.__object_positions.items():
                if existing_object_name == name:
                    continue
                if distance.euclidean(object_position, existing_object_position) < min_distance_to_other_objects:
                    min_distance_to_other_objects *= min_distance_decay_factor
                    is_too_close = True
                    break
        quat = task.np_random.uniform(-1, 1, 4)
        quat /= np.linalg.norm(quat)
        return (object_position, quat)

    def internal_overrides(self, task: SupportedTasks):
        """
        Perform internal overrides if parameters
        """
        if self._object_randomize_count:
            self._object_count = task.np_random.randint(low=1, high=self.__object_max_count + 1)

    def external_overrides(self, task: SupportedTasks):
        """
        Perform external overrides from either task level or environment before initialising/randomising the task.
        """
        self.__consume_parameter_overrides(task=task)

    def pre_randomization(self, task: SupportedTasks):
        """
        Perform steps that are required before randomization is performed.
        """
        segments_len = len(self._object_random_spawn_position_segments)
        if segments_len > 1:
            start_index = task.np_random.randint(segments_len - 1)
            segment = (self._object_random_spawn_position_segments[start_index], self._object_random_spawn_position_segments[start_index + 1])
            intersect = task.np_random.random()
            direction = (segment[1][0] - segment[0][0], segment[1][1] - segment[0][1], segment[1][2] - segment[0][2])
            self._object_spawn_position = (segment[0][0] + intersect * direction[0], segment[0][1] + intersect * direction[1], segment[0][2] + intersect * direction[2])
            if self._object_random_spawn_position_update_workspace_centre:
                task.workspace_centre = (self._object_spawn_position[0], self._object_spawn_position[1], task.workspace_centre[2])
                workspace_volume_half = (task.workspace_volume[0] / 2, task.workspace_volume[1] / 2, task.workspace_volume[2] / 2)
                task.workspace_min_bound = (task.workspace_centre[0] - workspace_volume_half[0], task.workspace_centre[1] - workspace_volume_half[1], task.workspace_centre[2] - workspace_volume_half[2])
                task.workspace_max_bound = (task.workspace_centre[0] + workspace_volume_half[0], task.workspace_centre[1] + workspace_volume_half[1], task.workspace_centre[2] + workspace_volume_half[2])

    def post_randomization(self, task: SupportedTasks, gazebo: scenario.GazeboSimulator):
        """
        Perform steps that are required once randomization is complete and the simulation can be stepped a few times unpaused.
        """
        attempts = 0
        object_overlapping_ok = False
        if self.robot.is_mobile:
            try:
                robot_gazebo = self.robot.to_gazebo()
                wheel_links = [robot_gazebo.get_link(link_name=wheel_link_name) for wheel_link_name in self.robot.wheel_link_names]
                is_robot_in_contact_with_terrain = False
                while not is_robot_in_contact_with_terrain and attempts < self.POST_RANDOMIZATION_MAX_STEPS:
                    for wheel_link in wheel_links:
                        wheel_contacts = wheel_link.contacts()
                        if wheel_contacts:
                            break
                    for contact in wheel_contacts:
                        if f'{task.terrain_name}::' in contact.body_b:
                            is_robot_in_contact_with_terrain = True
                            break
                        elif '_collision_plane_B::' in contact.body_b:
                            attempts += 1
                            if self._terrain_enable:
                                self.randomize_terrain(task=task, gazebo=gazebo)
                            self.reset_robot_pose(task=task, gazebo=gazebo, randomize=self._robot_random_pose)
                            if self._object_enable:
                                if self._object_random_pose:
                                    self.object_random_pose(task=task, gazebo=gazebo)
                                else:
                                    self.reset_default_object_pose(task=task, gazebo=gazebo)
                            break
                    object_overlapping_ok = self.check_object_overlapping(task=task)
                    if not gazebo.step():
                        raise RuntimeError('Failed to execute an unpaused Gazebo step')
            except Exception as e:
                task.get_logger().error(f'Wheel contacts could not be checked due to an unexpected error: {e}')
        if self.POST_RANDOMIZATION_MAX_STEPS == attempts:
            task.get_logger().error('Robot keeps falling through the terrain. There is something wrong...')
            return
        while not object_overlapping_ok and attempts < self.POST_RANDOMIZATION_MAX_STEPS:
            attempts += 1
            task.get_logger().info('Objects overlapping, trying new positions')
            object_overlapping_ok = self.check_object_overlapping(task=task)
            if not gazebo.step():
                raise RuntimeError('Failed to execute an unpaused Gazebo step')
        if self.POST_RANDOMIZATION_MAX_STEPS == attempts:
            task.get_logger().warn('Objects could not be spawned without any overlapping. The workspace might be too crowded!')
            return
        observations_ready = False
        task.moveit2.reset_new_joint_state_checker()
        if task._enable_gripper:
            task.gripper.reset_new_joint_state_checker()
        if hasattr(task, 'camera_sub'):
            task.camera_sub.reset_new_observation_checker()
        while not observations_ready:
            attempts += 1
            if 0 == attempts % self.POST_RANDOMIZATION_MAX_STEPS:
                task.get_logger().warn(f'Waiting for new joint state after reset. Iteration #{attempts}...')
            else:
                task.get_logger().debug('Waiting for new joint state after reset.')
            if not gazebo.step():
                raise RuntimeError('Failed to execute an unpaused Gazebo step')
            if not task.moveit2.new_joint_state_available:
                continue
            if task._enable_gripper:
                if not task.gripper.new_joint_state_available:
                    continue
            if hasattr(task, 'camera_sub'):
                if not task.camera_sub.new_observation_available:
                    continue
            observations_ready = True
        if self.POST_RANDOMIZATION_MAX_STEPS == attempts:
            task.get_logger().error('Cannot obtain new observation.')
            return

    def check_object_overlapping(self, task: SupportedTasks, allowed_penetration_depth: float=0.001, terrain_allowed_penetration_depth: float=0.002) -> bool:
        """
        Go through all objects and make sure that none of them are overlapping.
        If an object is overlapping, reset its position.
        Positions are reset also if object is in collision with robot right after reset.
        Collisions/overlaps with terrain are ignored.
        Returns True if all objects are okay, false if they had to be reset
        """
        for object_name in self.task.object_names:
            model = task.world.get_model(object_name).to_gazebo()
            self.__object_positions[object_name] = model.get_link(link_name=model.link_names()[0]).position()
        for object_name in self.task.object_names:
            obj = task.world.get_model(object_name).to_gazebo()
            if task.check_object_outside_workspace(self.__object_positions[object_name]):
                position, quat_random = self.get_random_object_pose(task=task, centre=self._object_spawn_position, volume=self._object_random_spawn_volume, name=object_name)
                obj.reset_base_pose(position, quat_random)
                obj.reset_base_world_velocity([0.0, 0.0, 0.0], [0.0, 0.0, 0.0])
                return False
            try:
                for contact in obj.contacts():
                    depth = np.mean([point.depth for point in contact.points])
                    if self.terrain.name() in contact.body_b and depth < terrain_allowed_penetration_depth:
                        continue
                    if task.robot_name in contact.body_b or depth > allowed_penetration_depth:
                        position, quat_random = self.get_random_object_pose(task=task, centre=self._object_spawn_position, volume=self._object_random_spawn_volume, name=object_name)
                        obj.reset_base_pose(position, quat_random)
                        obj.reset_base_world_velocity([0.0, 0.0, 0.0], [0.0, 0.0, 0.0])
                        return False
            except Exception as e:
                task.get_logger().error(f'Runtime error encountered while checking objects intersections: {e}')
        return True

    def __camera_pose_randomizer_enabled(self) -> bool:
        """
        Checks if camera pose randomizer is enabled.

        Return:
            True if enabled, false otherwise
        """
        if self._camera_random_pose_rollouts_num == 0:
            return False
        else:
            return True

    def _camera_pose_expired(self) -> bool:
        """
        Checks if camera pose needs to be randomized.

        Return:
            True if expired, false otherwise
        """
        if not self.__camera_pose_randomizer_enabled():
            return False
        self.__camera_pose_rollout_counter += 1
        if self.__camera_pose_rollout_counter >= self._camera_random_pose_rollouts_num:
            self.__camera_pose_rollout_counter = 0
            return True
        return False

    def __terrain_model_randomizer_enabled(self) -> bool:
        """
        Checks if terrain randomizer is enabled.

        Return:
            True if enabled, false otherwise
        """
        if self._terrain_model_rollouts_num == 0:
            return False
        else:
            return self.__is_terrain_type_randomizable

    def _terrain_model_expired(self) -> bool:
        """
        Checks if terrain model needs to be randomized.

        Return:
            True if expired, false otherwise
        """
        if not self.__terrain_model_randomizer_enabled():
            return False
        self.__terrain_model_rollout_counter += 1
        if self.__terrain_model_rollout_counter >= self._terrain_model_rollouts_num:
            self.__terrain_model_rollout_counter = 0
            return True
        return False

    def __light_model_randomizer_enabled(self) -> bool:
        """
        Checks if light model randomizer is enabled.

        Return:
            True if enabled, false otherwise
        """
        if self._light_model_rollouts_num == 0:
            return False
        else:
            return self.__is_light_type_randomizable

    def _light_model_expired(self) -> bool:
        """
        Checks if light models need to be randomized.

        Return:
            True if expired, false otherwise
        """
        if not self.__light_model_randomizer_enabled():
            return False
        self.__light_model_rollout_counter += 1
        if self.__light_model_rollout_counter >= self._light_model_rollouts_num:
            self.__light_model_rollout_counter = 0
            return True
        return False

    def __object_models_randomizer_enabled(self) -> bool:
        """
        Checks if object model randomizer is enabled.

        Return:
            True if enabled, false otherwise
        """
        if self._object_models_rollouts_num == 0:
            return False
        else:
            return self.__is_object_type_randomizable

    def _object_models_expired(self) -> bool:
        """
        Checks if object models need to be randomized.

        Return:
            True if expired, false otherwise
        """
        if not self.__object_models_randomizer_enabled():
            return False
        self.__object_models_rollout_counter += 1
        if self.__object_models_rollout_counter >= self._object_models_rollouts_num:
            self.__object_models_rollout_counter = 0
            return True
        return False

    def __consume_parameter_overrides(self, task: SupportedTasks):
        for key, value in task._randomizer_parameter_overrides.items():
            if hasattr(self, key):
                setattr(self, key, value)
            elif hasattr(self, f'_{key}'):
                setattr(self, f'_{key}', value)
            elif hasattr(self, f'__{key}'):
                setattr(self, f'__{key}', value)
            else:
                task.get_logger().error(f"Override '{key}' is not supperted by the randomizer.")
        task._randomizer_parameter_overrides.clear()

    def visualise_workspace(self, task: SupportedTasks, gazebo: scenario.GazeboSimulator, color: Tuple[float, float, float, float]=(0, 1, 0, 0.8)):
        models.Box(world=task.world, name='_workspace_volume', position=self._object_spawn_position, orientation=(0, 0, 0, 1), size=task.workspace_volume, collision=False, visual=True, gui_only=True, static=True, color=color)
        if not gazebo.run(paused=True):
            raise RuntimeError('Failed to execute a paused Gazebo run')

    def visualise_spawn_volume(self, task: SupportedTasks, gazebo: scenario.GazeboSimulator, color: Tuple[float, float, float, float]=(0, 0, 1, 0.8), color_with_height: Tuple[float, float, float, float]=(1, 0, 1, 0.7)):
        models.Box(world=task.world, name='_object_random_spawn_volume', position=self._object_spawn_position, orientation=(0, 0, 0, 1), size=self._object_random_spawn_volume, collision=False, visual=True, gui_only=True, static=True, color=color)
        models.Box(world=task.world, name='_object_random_spawn_volume_with_height', position=self._object_spawn_position, orientation=(0, 0, 0, 1), size=self._object_random_spawn_volume, collision=False, visual=True, gui_only=True, static=True, color=color_with_height)
        if not gazebo.run(paused=True):
            raise RuntimeError('Failed to execute a paused Gazebo run')

def init_env(self, task: SupportedTasks, gazebo: scenario.GazeboSimulator):
    """
        Initialise an instance of the environment before the very first iteration
        """
    set_log_level(log_level=task.get_logger().get_effective_level().name)
    if not gazebo.run(paused=True):
        raise RuntimeError('Failed to execute a paused Gazebo run')
    self._object_spawn_position = (self._object_spawn_position[0], self._object_spawn_position[1], self._object_spawn_position[2] + task.robot_model_class.BASE_LINK_Z_OFFSET)
    self._camera_random_pose_focal_point_z_offset += task.robot_model_class.BASE_LINK_Z_OFFSET
    self._camera_relative_to = task.substitute_special_frame(self._camera_relative_to)
    self._objects_relative_to = task.substitute_special_frame(self._objects_relative_to)
    self.init_physics_preset(task=task)
    self.init_world_plugins(task=task, gazebo=gazebo)
    self.init_models(task=task, gazebo=gazebo)

class Manipulation(Task, Node, abc.ABC):
    _ids = count(0)

    def __init__(self, agent_rate: float, robot_model: str, workspace_frame_id: str, workspace_centre: Tuple[float, float, float], workspace_volume: Tuple[float, float, float], ignore_new_actions_while_executing: bool, use_servo: bool, scaling_factor_translation: float, scaling_factor_rotation: float, restrict_position_goal_to_workspace: bool, enable_gripper: bool, num_threads: int, **kwargs):
        self.id = next(self._ids)
        Task.__init__(self, agent_rate=agent_rate)
        try:
            rclpy.init()
        except Exception as e:
            if not rclpy.ok():
                sys.exit(f'ROS 2 context could not be initialised: {e}')
        Node.__init__(self, f'drl_grasping_{self.id}')
        self._callback_group = ReentrantCallbackGroup()
        if num_threads == 1:
            executor = SingleThreadedExecutor()
        elif num_threads > 1:
            executor = MultiThreadedExecutor(num_threads=num_threads)
        else:
            executor = MultiThreadedExecutor(num_threads=multiprocessing.cpu_count())
        executor.add_node(self)
        self._executor_thread = Thread(target=executor.spin, daemon=True, args=())
        self._executor_thread.start()
        self.robot_model_class = get_robot_model_class(robot_model)
        self.workspace_centre = (workspace_centre[0], workspace_centre[1], workspace_centre[2] + self.robot_model_class.BASE_LINK_Z_OFFSET)
        self.workspace_volume = workspace_volume
        self._restrict_position_goal_to_workspace = restrict_position_goal_to_workspace
        self._use_servo = use_servo
        self.__scaling_factor_translation = scaling_factor_translation
        self.__scaling_factor_rotation = scaling_factor_rotation
        self._enable_gripper = enable_gripper
        workspace_volume_half = (workspace_volume[0] / 2, workspace_volume[1] / 2, workspace_volume[2] / 2)
        self.workspace_min_bound = (self.workspace_centre[0] - workspace_volume_half[0], self.workspace_centre[1] - workspace_volume_half[1], self.workspace_centre[2] - workspace_volume_half[2])
        self.workspace_max_bound = (self.workspace_centre[0] + workspace_volume_half[0], self.workspace_centre[1] + workspace_volume_half[1], self.workspace_centre[2] + workspace_volume_half[2])
        self.robot_prefix = self.robot_model_class.DEFAULT_PREFIX
        if 0 == self.id:
            self.robot_name = self.robot_model_class.ROBOT_MODEL_NAME
        else:
            self.robot_name = f'{self.robot_model_class.ROBOT_MODEL_NAME}{self.id}'
            if self.robot_prefix.endswith('_'):
                self.robot_prefix = f'{self.robot_prefix[:-1]}{self.id}_'
            elif self.robot_prefix.empty():
                self.robot_prefix = f'robot{self.id}_'
        self.robot_base_link_name = self.robot_model_class.get_robot_base_link_name(self.robot_prefix)
        self.robot_arm_base_link_name = self.robot_model_class.get_arm_base_link_name(self.robot_prefix)
        self.robot_ee_link_name = self.robot_model_class.get_ee_link_name(self.robot_prefix)
        self.robot_arm_link_names = self.robot_model_class.get_arm_link_names(self.robot_prefix)
        self.robot_gripper_link_names = self.robot_model_class.get_gripper_link_names(self.robot_prefix)
        self.robot_arm_joint_names = self.robot_model_class.get_arm_joint_names(self.robot_prefix)
        self.robot_gripper_joint_names = self.robot_model_class.get_gripper_joint_names(self.robot_prefix)
        self.workspace_frame_id = self.substitute_special_frame(workspace_frame_id)
        self.initial_arm_joint_positions = self.robot_model_class.DEFAULT_ARM_JOINT_POSITIONS
        self.initial_gripper_joint_positions = self.robot_model_class.DEFAULT_GRIPPER_JOINT_POSITIONS
        self.terrain_name = 'terrain'
        self.object_names = []
        self.tf2_listener = Tf2Listener(node=self)
        self.tf2_broadcaster = Tf2Broadcaster(node=self)
        self.moveit2 = MoveIt2(node=self, joint_names=self.robot_arm_joint_names, base_link_name=self.robot_arm_base_link_name, end_effector_name=self.robot_ee_link_name, execute_via_moveit=False, ignore_new_calls_while_executing=ignore_new_actions_while_executing, callback_group=self._callback_group)
        if self._use_servo:
            self.servo = MoveIt2Servo(node=self, frame_id=self.robot_arm_base_link_name, linear_speed=scaling_factor_translation, angular_speed=scaling_factor_rotation, callback_group=self._callback_group)
        self.gripper = MoveIt2Gripper(node=self, gripper_joint_names=self.robot_gripper_joint_names, open_gripper_joint_positions=self.robot_model_class.OPEN_GRIPPER_JOINT_POSITIONS, closed_gripper_joint_positions=self.robot_model_class.CLOSED_GRIPPER_JOINT_POSITIONS, skip_planning=True, ignore_new_calls_while_executing=ignore_new_actions_while_executing, callback_group=self._callback_group)
        self.__task_parameter_overrides: Dict[str, any] = {}
        self._randomizer_parameter_overrides: Dict[str, any] = {}

    def create_spaces(self) -> Tuple[ActionSpace, ObservationSpace]:
        action_space = self.create_action_space()
        observation_space = self.create_observation_space()
        return (action_space, observation_space)

    def create_action_space(self) -> ActionSpace:
        raise NotImplementedError()

    def create_observation_space(self) -> ObservationSpace:
        raise NotImplementedError()

    def set_action(self, action: Action):
        raise NotImplementedError()

    def get_observation(self) -> Observation:
        raise NotImplementedError()

    def get_reward(self) -> Reward:
        raise NotImplementedError()

    def is_done(self) -> bool:
        raise NotImplementedError()

    def reset_task(self):
        self.__consume_parameter_overrides()

    def get_relative_ee_position(self, translation: Tuple[float, float, float]) -> Tuple[float, float, float]:
        translation = self.scale_relative_translation(translation)
        current_position = self.get_ee_position()
        target_position = (current_position[0] + translation[0], current_position[1] + translation[1], current_position[2] + translation[2])
        if self._restrict_position_goal_to_workspace:
            target_position = self.restrict_position_goal_to_workspace(target_position)
        return target_position

    def get_relative_ee_orientation(self, rotation: Union[float, Tuple[float, float, float, float], Tuple[float, float, float, float, float, float]], representation: str='quat') -> Tuple[float, float, float, float]:
        current_quat_xyzw = self.get_ee_orientation()
        if 'z' == representation:
            current_yaw = Rotation.from_quat(current_quat_xyzw).as_euler('xyz')[2]
            current_quat_xyzw = Rotation.from_euler('xyz', [np.pi, 0, current_yaw]).as_quat()
        relative_quat_xyzw = None
        if 'quat' == representation:
            relative_quat_xyzw = rotation
        elif '6d' == representation:
            vectors = tuple((rotation[x:x + 3] for x, _ in enumerate(rotation) if x % 3 == 0))
            relative_quat_xyzw = orientation_6d_to_quat(vectors[0], vectors[1])
        elif 'z' == representation:
            rotation = self.scale_relative_rotation(rotation)
            relative_quat_xyzw = Rotation.from_euler('xyz', [0, 0, rotation]).as_quat()
        target_quat_xyzw = quat_mul(current_quat_xyzw, relative_quat_xyzw)
        target_quat_xyzw /= np.linalg.norm(target_quat_xyzw)
        return target_quat_xyzw

    def scale_relative_translation(self, translation: Tuple[float, float, float]) -> Tuple[float, float, float]:
        return (self.__scaling_factor_translation * translation[0], self.__scaling_factor_translation * translation[1], self.__scaling_factor_translation * translation[2])

    def scale_relative_rotation(self, rotation: Union[float, Tuple[float, float, float], np.floating, np.ndarray]) -> float:
        if not hasattr(rotation, '__len__'):
            return self.__scaling_factor_rotation * rotation
        else:
            return (self.__scaling_factor_rotation * rotation[0], self.__scaling_factor_rotation * rotation[1], self.__scaling_factor_rotation * rotation[2])

    def restrict_position_goal_to_workspace(self, position: Tuple[float, float, float]) -> Tuple[float, float, float]:
        return (min(self.workspace_max_bound[0], max(self.workspace_min_bound[0], position[0])), min(self.workspace_max_bound[1], max(self.workspace_min_bound[1], position[1])), min(self.workspace_max_bound[2], max(self.workspace_min_bound[2], position[2])))

    def restrict_servo_translation_to_workspace(self, translation: Tuple[float, float, float]) -> Tuple[float, float, float]:
        current_ee_position = self.get_ee_position()
        translation = tuple((0.0 if current_ee_position[i] > self.workspace_max_bound[i] and translation[i] > 0.0 or (current_ee_position[i] < self.workspace_min_bound[i] and translation[i] < 0.0) else translation[i] for i in range(3)))
        return translation

    def get_ee_pose(self) -> Optional[Tuple[Tuple[float, float, float], Tuple[float, float, float, float]]]:
        """
        Return the current pose of the end effector with respect to arm base link.
        """
        try:
            robot_model = self.world.to_gazebo().get_model(self.robot_name).to_gazebo()
            ee_position, ee_quat_xyzw = get_model_pose(world=self.world, model=robot_model, link=self.robot_ee_link_name, xyzw=True)
            return transform_change_reference_frame_pose(world=self.world, position=ee_position, quat=ee_quat_xyzw, target_model=robot_model, target_link=self.robot_arm_base_link_name, xyzw=True)
        except Exception as e:
            self.get_logger().warn(f'Cannot get end effector pose from Gazebo ({e}), using tf2...')
            transform = self.tf2_listener.lookup_transform_sync(source_frame=self.robot_ee_link_name, target_frame=self.robot_arm_base_link_name, retry=False)
            if transform is not None:
                return ((transform.translation.x, transform.translation.y, transform.translation.z), (transform.rotation.x, transform.rotation.y, transform.rotation.z, transform.rotation.w))
            else:
                self.get_logger().error('Cannot get pose of the end effector (default values are returned)')
                return ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0))

    def get_ee_position(self) -> Tuple[float, float, float]:
        """
        Return the current position of the end effector with respect to arm base link.
        """
        try:
            robot_model = self.world.to_gazebo().get_model(self.robot_name).to_gazebo()
            ee_position = get_model_position(world=self.world, model=robot_model, link=self.robot_ee_link_name)
            return transform_change_reference_frame_position(world=self.world, position=ee_position, target_model=robot_model, target_link=self.robot_arm_base_link_name)
        except Exception as e:
            self.get_logger().warn(f'Cannot get end effector position from Gazebo ({e}), using tf2...')
            transform = self.tf2_listener.lookup_transform_sync(source_frame=self.robot_ee_link_name, target_frame=self.robot_arm_base_link_name, retry=False)
            if transform is not None:
                return (transform.translation.x, transform.translation.y, transform.translation.z)
            else:
                self.get_logger().error('Cannot get position of the end effector (default values are returned)')
                return (0.0, 0.0, 0.0)

    def get_ee_orientation(self) -> Tuple[float, float, float, float]:
        """
        Return the current xyzw quaternion of the end effector with respect to arm base link.
        """
        try:
            robot_model = self.world.to_gazebo().get_model(self.robot_name).to_gazebo()
            ee_quat_xyzw = get_model_orientation(world=self.world, model=robot_model, link=self.robot_ee_link_name, xyzw=True)
            return transform_change_reference_frame_orientation(world=self.world, quat=ee_quat_xyzw, target_model=robot_model, target_link=self.robot_arm_base_link_name, xyzw=True)
        except Exception as e:
            self.get_logger().warn(f'Cannot get end effector orientation from Gazebo ({e}), using tf2...')
            transform = self.tf2_listener.lookup_transform_sync(source_frame=self.robot_ee_link_name, target_frame=self.robot_arm_base_link_name, retry=False)
            if transform is not None:
                return (transform.rotation.x, transform.rotation.y, transform.rotation.z, transform.rotation.w)
            else:
                self.get_logger().error('Cannot get orientation of the end effector (default values are returned)')
                return (0.0, 0.0, 0.0, 1.0)

    def get_object_position(self, object_model: Union[ModelWrapper, str]) -> Tuple[float, float, float]:
        """
        Return the current position of an object with respect to arm base link.
        Note: Only simulated objects are currently supported.
        """
        try:
            object_position = get_model_position(world=self.world, model=object_model)
            return transform_change_reference_frame_position(world=self.world, position=object_position, target_model=self.robot_name, target_link=self.robot_arm_base_link_name)
        except Exception as e:
            self.get_logger().error(f'Cannot get position of {object_model} object (default values are returned): {e}')
            return (0.0, 0.0, 0.0)

    def get_object_positions(self) -> Dict[str, Tuple[float, float, float]]:
        """
        Return the current position of all objects with respect to arm base link.
        Note: Only simulated objects are currently supported.
        """
        object_positions = {}
        try:
            robot_model = self.world.to_gazebo().get_model(self.robot_name).to_gazebo()
            robot_arm_base_link = robot_model.get_link(link_name=self.robot_arm_base_link_name)
            for object_name in self.object_names:
                object_position = get_model_position(world=self.world, model=object_name)
                object_positions[object_name] = transform_change_reference_frame_position(world=self.world, position=object_position, target_model=robot_model, target_link=robot_arm_base_link)
        except Exception as e:
            self.get_logger().error(f'Cannot get positions of all objects (empty Dict is returned): {e}')
        return object_positions

    def substitute_special_frame(self, frame_id: str) -> str:
        if 'arm_base_link' == frame_id:
            return self.robot_arm_base_link_name
        elif 'base_link' == frame_id:
            return self.robot_base_link_name
        elif 'end_effector' == frame_id:
            return self.robot_ee_link_name
        elif 'world' == frame_id:
            try:
                return self.world.to_gazebo().name()
            except Exception as e:
                self.get_logger().warn(f'')
                return 'drl_grasping_world'
        else:
            return frame_id

    def wait_until_action_executed(self):
        if self._use_servo:
            rate = self.create_rate(self.agent_rate)
            try:
                if rclpy.ok():
                    rate.sleep()
            except KeyboardInterrupt:
                pass
        self.moveit2.wait_until_executed()
        if self._enable_gripper:
            self.gripper.wait_until_executed()

    def move_to_initial_joint_configuration(self):
        self.moveit2.move_to_configuration(self.initial_arm_joint_positions)
        if self.robot_model_class.CLOSED_GRIPPER_JOINT_POSITIONS == self.initial_gripper_joint_positions:
            self.gripper.reset_close()
        else:
            self.gripper.reset_open()

    def check_terrain_collision(self) -> bool:
        """
        Returns true if robot links are in collision with the ground.
        """
        robot_name_len = len(self.robot_name)
        for contact in self.world.get_model(self.terrain_name).contacts():
            if len(contact.body_b) > robot_name_len:
                if contact.body_b[:robot_name_len] == self.robot_name:
                    link = contact.body_b[len(self.robot_name) + 2:]
                    if not self.robot_base_link_name == link and (link in self.robot_arm_link_names or link in self.robot_gripper_link_names):
                        return True
        return False

    def check_all_objects_outside_workspace(self, object_positions: Dict[str, Tuple[float, float, float]]) -> bool:
        """
        Returns true if all objects are outside the workspace
        """
        return all([self.check_object_outside_workspace(object_position) for object_position in object_positions.values()])

    def check_object_outside_workspace(self, object_position: Tuple[float, float, float]) -> bool:
        """
        Returns true if the object is outside the workspace
        """
        return object_position[0] < self.workspace_min_bound[0] or object_position[1] < self.workspace_min_bound[1] or object_position[2] < self.workspace_min_bound[2] or (object_position[0] > self.workspace_max_bound[0]) or (object_position[1] > self.workspace_max_bound[1]) or (object_position[2] > self.workspace_max_bound[2])

    def add_parameter_overrides(self, parameter_overrides: Dict[str, any]):
        self.add_task_parameter_overrides(parameter_overrides)
        self.add_randomizer_parameter_overrides(parameter_overrides)

    def add_task_parameter_overrides(self, parameter_overrides: Dict[str, any]):
        self.__task_parameter_overrides.update(parameter_overrides)

    def add_randomizer_parameter_overrides(self, parameter_overrides: Dict[str, any]):
        self._randomizer_parameter_overrides.update(parameter_overrides)

    def __consume_parameter_overrides(self):
        for key, value in self.__task_parameter_overrides.items():
            if hasattr(self, key):
                setattr(self, key, value)
            elif hasattr(self, f'_{key}'):
                setattr(self, f'_{key}', value)
            elif hasattr(self, f'__{key}'):
                setattr(self, f'__{key}', value)
            else:
                self.get_logger().error(f"Override '{key}' is not supperted by the task.")
        self.__task_parameter_overrides.clear()

def add_task_parameter_overrides(self, parameter_overrides: Dict[str, any]):
    self.__task_parameter_overrides.update(parameter_overrides)

def add_randomizer_parameter_overrides(self, parameter_overrides: Dict[str, any]):
    self._randomizer_parameter_overrides.update(parameter_overrides)

class GraspPlanetaryDepthImage(GraspPlanetary, abc.ABC):

    def __init__(self, depth_max_distance: float, image_include_color: bool, image_include_intensity: bool, image_n_stacked: int, proprioceptive_observations: bool, camera_type: str='rgbd_camera', camera_width: int=128, camera_height: int=128, **kwargs):
        GraspPlanetary.__init__(self, **kwargs)
        self.camera_sub = CameraSubscriber(node=self, topic=Camera.get_depth_topic(camera_type), is_point_cloud=False, callback_group=self._callback_group)
        if image_include_color or image_include_intensity:
            assert camera_type == 'rgbd_camera'
            self.camera_sub_color = CameraSubscriber(node=self, topic=Camera.get_color_topic(camera_type), is_point_cloud=False, callback_group=self._callback_group)
        self._camera_width = camera_width
        self._camera_height = camera_height
        self._depth_max_distance = depth_max_distance
        self._image_n_stacked = image_n_stacked
        self._image_include_color = image_include_color
        self._image_include_intensity = image_include_intensity
        self._proprioceptive_observations = proprioceptive_observations
        self._num_pixels = camera_height * camera_width
        self.__stacked_images = deque([], maxlen=self._image_n_stacked)

    def create_observation_space(self) -> ObservationSpace:
        size = self._num_pixels
        if self._image_include_color:
            size += 3 * self._num_pixels
        elif self._image_include_intensity:
            size += self._num_pixels
        if self._proprioceptive_observations:
            size += 11
        return gym.spaces.Box(low=-1.0, high=1.0, shape=(self._image_n_stacked, size), dtype=np.float32)

    def get_observation(self) -> Observation:
        depth_image_msg = self.camera_sub.get_observation()
        img_res = depth_image_msg.height * depth_image_msg.width
        if 2 * img_res == len(depth_image_msg.data):
            depth_data_type = np.float16
        else:
            depth_data_type = np.float32
        if depth_image_msg.height != self._camera_width or depth_image_msg.width != self._camera_height:
            import cv2
            depth_image = np.ndarray(buffer=depth_image_msg.data, dtype=depth_data_type, shape=(depth_image_msg.height, depth_image_msg.width)).astype(dtype=np.float32)
            if depth_image_msg.height > depth_image_msg.width:
                diff = depth_image_msg.height - depth_image_msg.width
                diff_2 = diff // 2
                depth_image = depth_image[diff_2:-diff_2, :]
            elif depth_image_msg.height < depth_image_msg.width:
                diff = depth_image_msg.width - depth_image_msg.height
                diff_2 = diff // 2
                depth_image = depth_image[:, diff_2:-diff_2]
            depth_image = cv2.resize(depth_image, dsize=(self._camera_height, self._camera_width), interpolation=cv2.INTER_CUBIC).reshape(self._num_pixels)
        else:
            depth_image = np.ndarray(buffer=depth_image_msg.data, dtype=depth_data_type, shape=(self._num_pixels,)).astype(dtype=np.float32)
        np.nan_to_num(depth_image, copy=False, nan=0.0, posinf=0.0, neginf=0.0)
        depth_image[depth_image > self._depth_max_distance] = self._depth_max_distance
        depth_image = depth_image / self._depth_max_distance
        if self._image_include_color or self._image_include_intensity:
            color_image_msg = self.camera_sub_color.get_observation()
            if color_image_msg.height != self._camera_width or color_image_msg.width != self._camera_height:
                import cv2
                color_image = np.ndarray(buffer=color_image_msg.data, dtype=np.uint8, shape=(color_image_msg.height, color_image_msg.width, 3))
                if color_image_msg.height > color_image_msg.width:
                    diff = color_image_msg.height - color_image_msg.width
                    diff_2 = diff // 2
                    color_image = color_image[diff_2:-diff_2, :, :]
                elif color_image_msg.height < color_image_msg.width:
                    diff = color_image_msg.width - color_image_msg.height
                    diff_2 = diff // 2
                    color_image = color_image[:, diff_2:-diff_2, :]
                color_image = cv2.resize(color_image, dsize=(self._camera_width, self._camera_height), interpolation=cv2.INTER_CUBIC).reshape(3 * self._num_pixels)
            else:
                color_image = np.ndarray(buffer=color_image_msg.data, dtype=np.uint8, shape=(3 * self._num_pixels,))
            if self._image_include_intensity:
                color_image = color_image.reshape(self._camera_width, self._camera_height, 3)[:, :, 0].reshape(-1)
            color_image.astype(dtype=np.float32)
            color_image = color_image / 255.0
            depth_image = np.concatenate((depth_image, color_image))
        if self._proprioceptive_observations:
            depth_image = np.pad(depth_image, (0, 11), 'constant', constant_values=0)
            depth_image[-1] = np.array(10, dtype=np.float32)
            ee_position, ee_orientation = self.get_ee_pose()
            ee_orientation = orientation_quat_to_6d(quat_xyzw=ee_orientation)
            aux_obs = (1.0 if self.gripper.is_open else -1.0,) + ee_position + ee_orientation[0] + ee_orientation[1]
            depth_image[-11:-1] = np.array(aux_obs, dtype=np.float32)
        self.__stacked_images.append(depth_image)
        while not self._image_n_stacked == len(self.__stacked_images):
            self.__stacked_images.append(depth_image)
        observation = Observation(np.array(self.__stacked_images, dtype=np.uint8))
        self.get_logger().debug(f'\nobservation: {observation}')
        return observation

    def reset_task(self):
        self.__stacked_images.clear()
        GraspPlanetary.reset_task(self)

def __init__(self, depth_max_distance: float, image_include_color: bool, image_include_intensity: bool, image_n_stacked: int, proprioceptive_observations: bool, camera_type: str='rgbd_camera', camera_width: int=128, camera_height: int=128, **kwargs):
    GraspPlanetary.__init__(self, **kwargs)
    self.camera_sub = CameraSubscriber(node=self, topic=Camera.get_depth_topic(camera_type), is_point_cloud=False, callback_group=self._callback_group)
    if image_include_color or image_include_intensity:
        assert camera_type == 'rgbd_camera'
        self.camera_sub_color = CameraSubscriber(node=self, topic=Camera.get_color_topic(camera_type), is_point_cloud=False, callback_group=self._callback_group)
    self._camera_width = camera_width
    self._camera_height = camera_height
    self._depth_max_distance = depth_max_distance
    self._image_n_stacked = image_n_stacked
    self._image_include_color = image_include_color
    self._image_include_intensity = image_include_intensity
    self._proprioceptive_observations = proprioceptive_observations
    self._num_pixels = camera_height * camera_width
    self.__stacked_images = deque([], maxlen=self._image_n_stacked)

class GraspPlanetaryOctree(GraspPlanetary, abc.ABC):

    def __init__(self, octree_reference_frame_id: str, octree_min_bound: Tuple[float, float, float], octree_max_bound: Tuple[float, float, float], octree_depth: int, octree_full_depth: int, octree_include_color: bool, octree_include_intensity: bool, octree_n_stacked: int, octree_max_size: int, proprioceptive_observations: bool, camera_type: str='rgbd_camera', **kwargs):
        GraspPlanetary.__init__(self, **kwargs)
        self.camera_sub = CameraSubscriber(node=self, topic=Camera.get_points_topic(camera_type), is_point_cloud=True, callback_group=self._callback_group)
        octree_min_bound = (octree_min_bound[0], octree_min_bound[1], octree_min_bound[2] + self.robot_model_class.BASE_LINK_Z_OFFSET)
        octree_max_bound = (octree_max_bound[0], octree_max_bound[1], octree_max_bound[2] + self.robot_model_class.BASE_LINK_Z_OFFSET)
        self.octree_creator = OctreeCreator(node=self, tf2_listener=self.tf2_listener, reference_frame_id=self.substitute_special_frame(octree_reference_frame_id), min_bound=octree_min_bound, max_bound=octree_max_bound, include_color=octree_include_color, include_intensity=octree_include_intensity, depth=octree_depth, full_depth=octree_full_depth)
        self._octree_n_stacked = octree_n_stacked
        self._octree_max_size = octree_max_size
        self._proprioceptive_observations = proprioceptive_observations
        self.__stacked_octrees = deque([], maxlen=self._octree_n_stacked)

    def create_observation_space(self) -> ObservationSpace:
        return gym.spaces.Box(low=0, high=255, shape=(self._octree_n_stacked, self._octree_max_size), dtype=np.uint8)

    def get_observation(self) -> Observation:
        point_cloud = self.camera_sub.get_observation()
        octree = self.octree_creator(point_cloud).numpy()
        octree_size = octree.shape[0]
        if octree_size > self._octree_max_size:
            self.get_logger().error(f'Octree is larger than the maximum allowed size of {self._octree_max_size} (exceeded with {octree_size})')
        octree = np.pad(octree, (0, self._octree_max_size - octree_size), 'constant', constant_values=0)
        octree[-4:] = np.ndarray(buffer=np.array([octree_size], dtype=np.uint32).tobytes(), shape=(4,), dtype=np.uint8)
        if self._proprioceptive_observations:
            octree[-8:-4] = np.ndarray(buffer=np.array([10], dtype=np.uint32).tobytes(), shape=(4,), dtype=np.uint8)
            ee_position, ee_orientation = self.get_ee_pose()
            ee_orientation = orientation_quat_to_6d(quat_xyzw=ee_orientation)
            aux_obs = (1.0 if self.gripper.is_open else -1.0,) + ee_position + ee_orientation[0] + ee_orientation[1]
            octree[-48:-8] = np.ndarray(buffer=np.array(aux_obs, dtype=np.float32).tobytes(), shape=(40,), dtype=np.uint8)
        self.__stacked_octrees.append(octree)
        while not self._octree_n_stacked == len(self.__stacked_octrees):
            self.__stacked_octrees.append(octree)
        observation = Observation(np.array(self.__stacked_octrees, dtype=np.uint8))
        self.get_logger().debug(f'\nobservation: {observation}')
        return observation

    def reset_task(self):
        self.__stacked_octrees.clear()
        GraspPlanetary.reset_task(self)

def __init__(self, octree_reference_frame_id: str, octree_min_bound: Tuple[float, float, float], octree_max_bound: Tuple[float, float, float], octree_depth: int, octree_full_depth: int, octree_include_color: bool, octree_include_intensity: bool, octree_n_stacked: int, octree_max_size: int, proprioceptive_observations: bool, camera_type: str='rgbd_camera', **kwargs):
    GraspPlanetary.__init__(self, **kwargs)
    self.camera_sub = CameraSubscriber(node=self, topic=Camera.get_points_topic(camera_type), is_point_cloud=True, callback_group=self._callback_group)
    octree_min_bound = (octree_min_bound[0], octree_min_bound[1], octree_min_bound[2] + self.robot_model_class.BASE_LINK_Z_OFFSET)
    octree_max_bound = (octree_max_bound[0], octree_max_bound[1], octree_max_bound[2] + self.robot_model_class.BASE_LINK_Z_OFFSET)
    self.octree_creator = OctreeCreator(node=self, tf2_listener=self.tf2_listener, reference_frame_id=self.substitute_special_frame(octree_reference_frame_id), min_bound=octree_min_bound, max_bound=octree_max_bound, include_color=octree_include_color, include_intensity=octree_include_intensity, depth=octree_depth, full_depth=octree_full_depth)
    self._octree_n_stacked = octree_n_stacked
    self._octree_max_size = octree_max_size
    self._proprioceptive_observations = proprioceptive_observations
    self.__stacked_octrees = deque([], maxlen=self._octree_n_stacked)

class GraspPlanetaryColorImage(GraspPlanetary, abc.ABC):

    def __init__(self, camera_width: int, camera_height: int, camera_type: str='camera', monochromatic: bool=False, **kwargs):
        GraspPlanetary.__init__(self, **kwargs)
        self._camera_width = camera_width
        self._camera_height = camera_height
        self._monochromatic = monochromatic
        self.camera_sub = CameraSubscriber(node=self, topic=Camera.get_color_topic(camera_type), is_point_cloud=False, callback_group=self._callback_group)

    def create_observation_space(self) -> ObservationSpace:
        return gym.spaces.Box(low=0, high=255, shape=(self._camera_height, self._camera_width, 1 if self._monochromatic else 3), dtype=np.uint8)

    def get_observation(self) -> Observation:
        image = self.camera_sub.get_observation()
        assert image.width == self._camera_width and image.height == self._camera_height, f'Error: Resolution of the input image does not match the configured observation space. ({image.width}x{image.height} instead of {self._camera_width}x{self._camera_height})'
        color_image = np.array(image.data, dtype=np.uint8).reshape(self._camera_height, self._camera_width, 3)
        if self._monochromatic:
            observation = Observation(color_image[:, :, 0])
        else:
            observation = Observation(color_image)
        self.get_logger().debug(f'\nobservation: {observation}')
        return observation

def __init__(self, camera_width: int, camera_height: int, camera_type: str='camera', monochromatic: bool=False, **kwargs):
    GraspPlanetary.__init__(self, **kwargs)
    self._camera_width = camera_width
    self._camera_height = camera_height
    self._monochromatic = monochromatic
    self.camera_sub = CameraSubscriber(node=self, topic=Camera.get_color_topic(camera_type), is_point_cloud=False, callback_group=self._callback_group)

class GraspPlanetary(Grasp, abc.ABC):

    def __init__(self, **kwargs):
        Grasp.__init__(self, **kwargs)
        if LunalabSummitXlGen == self.robot_model_class:
            self.initial_arm_joint_positions = [0.0, 2.356194490192345, 0.0, 4.71238898038469, 0.0, 2.356194490192345, 0.0]

def __init__(self, **kwargs):
    Grasp.__init__(self, **kwargs)
    if LunalabSummitXlGen == self.robot_model_class:
        self.initial_arm_joint_positions = [0.0, 2.356194490192345, 0.0, 4.71238898038469, 0.0, 2.356194490192345, 0.0]

class GraspOctree(Grasp, abc.ABC):

    def __init__(self, octree_reference_frame_id: str, octree_min_bound: Tuple[float, float, float], octree_max_bound: Tuple[float, float, float], octree_depth: int, octree_full_depth: int, octree_include_color: bool, octree_include_intensity: bool, octree_n_stacked: int, octree_max_size: int, proprioceptive_observations: bool, camera_type: str='rgbd_camera', **kwargs):
        Grasp.__init__(self, **kwargs)
        self.camera_sub = CameraSubscriber(node=self, topic=Camera.get_points_topic(camera_type), is_point_cloud=True, callback_group=self._callback_group)
        octree_min_bound = (octree_min_bound[0], octree_min_bound[1], octree_min_bound[2] + self.robot_model_class.BASE_LINK_Z_OFFSET)
        octree_max_bound = (octree_max_bound[0], octree_max_bound[1], octree_max_bound[2] + self.robot_model_class.BASE_LINK_Z_OFFSET)
        self.octree_creator = OctreeCreator(node=self, tf2_listener=self.tf2_listener, reference_frame_id=self.substitute_special_frame(octree_reference_frame_id), min_bound=octree_min_bound, max_bound=octree_max_bound, include_color=octree_include_color, include_intensity=octree_include_intensity, depth=octree_depth, full_depth=octree_full_depth)
        self._octree_n_stacked = octree_n_stacked
        self._octree_max_size = octree_max_size
        self._proprioceptive_observations = proprioceptive_observations
        self.__stacked_octrees = deque([], maxlen=self._octree_n_stacked)

    def create_observation_space(self) -> ObservationSpace:
        return gym.spaces.Box(low=0, high=255, shape=(self._octree_n_stacked, self._octree_max_size), dtype=np.uint8)

    def get_observation(self) -> Observation:
        point_cloud = self.camera_sub.get_observation()
        octree = self.octree_creator(point_cloud).numpy()
        octree_size = octree.shape[0]
        if octree_size > self._octree_max_size:
            self.get_logger().error(f'Octree is larger than the maximum allowed size of {self._octree_max_size} (exceeded with {octree_size})')
        octree = np.pad(octree, (0, self._octree_max_size - octree_size), 'constant', constant_values=0)
        octree[-4:] = np.ndarray(buffer=np.array([octree_size], dtype=np.uint32).tobytes(), shape=(4,), dtype=np.uint8)
        if self._proprioceptive_observations:
            octree[-8:-4] = np.ndarray(buffer=np.array([10], dtype=np.uint32).tobytes(), shape=(4,), dtype=np.uint8)
            ee_position, ee_orientation = self.get_ee_pose()
            ee_orientation = orientation_quat_to_6d(quat_xyzw=ee_orientation)
            aux_obs = (1.0 if self.gripper.is_open else -1.0,) + ee_position + ee_orientation[0] + ee_orientation[1]
            octree[-48:-8] = np.ndarray(buffer=np.array(aux_obs, dtype=np.float32).tobytes(), shape=(40,), dtype=np.uint8)
        self.__stacked_octrees.append(octree)
        while not self._octree_n_stacked == len(self.__stacked_octrees):
            self.__stacked_octrees.append(octree)
        observation = Observation(np.array(self.__stacked_octrees, dtype=np.uint8))
        self.get_logger().debug(f'\nobservation: {observation}')
        return observation

    def reset_task(self):
        self.__stacked_octrees.clear()
        Grasp.reset_task(self)

def __init__(self, octree_reference_frame_id: str, octree_min_bound: Tuple[float, float, float], octree_max_bound: Tuple[float, float, float], octree_depth: int, octree_full_depth: int, octree_include_color: bool, octree_include_intensity: bool, octree_n_stacked: int, octree_max_size: int, proprioceptive_observations: bool, camera_type: str='rgbd_camera', **kwargs):
    Grasp.__init__(self, **kwargs)
    self.camera_sub = CameraSubscriber(node=self, topic=Camera.get_points_topic(camera_type), is_point_cloud=True, callback_group=self._callback_group)
    octree_min_bound = (octree_min_bound[0], octree_min_bound[1], octree_min_bound[2] + self.robot_model_class.BASE_LINK_Z_OFFSET)
    octree_max_bound = (octree_max_bound[0], octree_max_bound[1], octree_max_bound[2] + self.robot_model_class.BASE_LINK_Z_OFFSET)
    self.octree_creator = OctreeCreator(node=self, tf2_listener=self.tf2_listener, reference_frame_id=self.substitute_special_frame(octree_reference_frame_id), min_bound=octree_min_bound, max_bound=octree_max_bound, include_color=octree_include_color, include_intensity=octree_include_intensity, depth=octree_depth, full_depth=octree_full_depth)
    self._octree_n_stacked = octree_n_stacked
    self._octree_max_size = octree_max_size
    self._proprioceptive_observations = proprioceptive_observations
    self.__stacked_octrees = deque([], maxlen=self._octree_n_stacked)

class Grasp(Manipulation, abc.ABC):

    def __init__(self, gripper_dead_zone: float, full_3d_orientation: bool, obs_n_stacked: int=1, preload_replay_buffer: bool=False, **kwargs):
        Manipulation.__init__(self, **kwargs)
        self.curriculum = GraspCurriculum(task=self, **kwargs)
        self.__gripper_dead_zone = gripper_dead_zone
        self.__full_3d_orientation = full_3d_orientation
        self.__preload_replay_buffer = preload_replay_buffer
        self._obs_n_stacked = obs_n_stacked
        self.__stacked_obs = deque([], maxlen=self._obs_n_stacked)

    def create_action_space(self) -> ActionSpace:
        if self.__full_3d_orientation:
            if self._use_servo:
                return gym.spaces.Box(low=-1.0, high=1.0, shape=(7,), dtype=np.float32)
            else:
                return gym.spaces.Box(low=-1.0, high=1.0, shape=(10,), dtype=np.float32)
        else:
            return gym.spaces.Box(low=-1.0, high=1.0, shape=(5,), dtype=np.float32)

    def create_observation_space(self) -> ObservationSpace:
        return gym.spaces.Box(low=np.array((-1.0, -np.inf, -np.inf, -np.inf, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -np.inf, -np.inf, -np.inf) * self._obs_n_stacked), high=np.array((1.0, np.inf, np.inf, np.inf, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, np.inf, np.inf, np.inf) * self._obs_n_stacked), shape=(13 * self._obs_n_stacked,), dtype=np.float32)

    def set_action(self, action: Action):
        if self.__preload_replay_buffer:
            action = self._demonstrate_action()
        self.get_logger().debug(f'action: {action}')
        gripper_action = action[0]
        if gripper_action < -self.__gripper_dead_zone:
            self.gripper.close()
        elif gripper_action > self.__gripper_dead_zone:
            self.gripper.open()
        else:
            pass
        if self._use_servo:
            linear = action[1:4]
            if self._restrict_position_goal_to_workspace:
                linear = self.restrict_servo_translation_to_workspace(linear)
            if self.__full_3d_orientation:
                angular = action[4:7]
            else:
                angular = [0.0, 0.0, action[4]]
            self.servo(linear=linear, angular=angular)
        else:
            position = self.get_relative_ee_position(action[1:4])
            if self.__full_3d_orientation:
                quat_xyzw = self.get_relative_ee_orientation(rotation=action[4:10], representation='6d')
            else:
                quat_xyzw = self.get_relative_ee_orientation(rotation=action[4], representation='z')
            self.moveit2.move_to_pose(position=position, quat_xyzw=quat_xyzw)

    def get_observation(self) -> Observation:
        ee_position, ee_orientation = self.get_ee_pose()
        ee_position = np.array(ee_position, dtype=np.float32)
        ee_orientation = np.array(orientation_quat_to_6d(quat_xyzw=ee_orientation), dtype=np.float32)
        object_positions = np.array(tuple(self.get_object_positions().values()), dtype=np.float32)
        nearest_object_position = get_nearest_point(origin=ee_position, points=object_positions)
        obs = np.concatenate([(1.0 if self.gripper.is_open else -1.0,), ee_position, ee_orientation[0], ee_orientation[1], nearest_object_position], dtype=np.float32)
        if self._obs_n_stacked > 1:
            self.__stacked_obs.append(obs)
            while not self._obs_n_stacked == len(self.__stacked_obs):
                self.__stacked_obs.append(obs)
            observation = Observation(np.concatenate(self.__stacked_obs, dtype=np.float32))
        else:
            observation = Observation(obs)
        self.get_logger().debug(f'\nobservation: {observation}')
        return observation

    def get_reward(self) -> Reward:
        return self.curriculum.get_reward()

    def is_done(self) -> bool:
        return self.curriculum.is_done()

    def get_info(self) -> Dict:
        info = self.curriculum.get_info()
        if self.__preload_replay_buffer:
            info.update({'actual_actions': self.__actual_actions})
        return info

    def reset_task(self):
        Manipulation.reset_task(self)
        self.curriculum.reset_task()

    def get_touched_objects(self) -> List[str]:
        """
        Returns list of all objects that are in contact with any finger.
        """
        robot = self.world.get_model(self.robot_name).to_gazebo()
        touched_objects = []
        for gripper_link_name in self.robot_gripper_link_names:
            finger = robot.get_link(link_name=gripper_link_name)
            finger_contacts = finger.contacts()
            for contact in finger_contacts:
                model_name = contact.body_b.split('::', 1)[0]
                if model_name not in touched_objects and any((object_name in model_name for object_name in self.object_names)):
                    touched_objects.append(model_name)
        return touched_objects

    def get_grasped_objects(self, min_angle_between_two_contact: float=np.pi / 8) -> List[str]:
        """
        Returns list of all currently grasped objects.
        Grasped object must be in contact with all gripper links (fingers) and their contact normals must be dissimilar.
        """
        if self.gripper.is_open:
            return []
        robot = self.world.get_model(self.robot_name)
        grasp_candidates = {}
        for gripper_link_name in self.robot_gripper_link_names:
            finger = robot.to_gazebo().get_link(link_name=gripper_link_name)
            finger_contacts = finger.contacts()
            if 0 == len(finger_contacts):
                continue
            for contact in finger_contacts:
                model_name = contact.body_b.split('::', 1)[0]
                if any((object_name in model_name for object_name in self.object_names)):
                    if model_name not in grasp_candidates:
                        grasp_candidates[model_name] = []
                    grasp_candidates[model_name].append(contact.points)
        grasped_objects = []
        for model_name, contact_points_list in grasp_candidates.items():
            if len(contact_points_list) < 2:
                continue
            average_normals = []
            for contact_points in contact_points_list:
                average_normal = np.array([0.0, 0.0, 0.0])
                for point in contact_points:
                    average_normal += point.normal
                average_normal /= np.linalg.norm(average_normal)
                average_normals.append(average_normal)
            normal_angles = []
            for n1, n2 in itertools.combinations(average_normals, 2):
                normal_angles.append(np.arccos(np.clip(np.dot(n1, n2), -1.0, 1.0)))
            sufficient_angle = min_angle_between_two_contact
            for angle in normal_angles:
                if angle > sufficient_angle:
                    grasped_objects.append(model_name)
                    break
        return grasped_objects

    def _demonstrate_action(self) -> np.ndarray:
        self.__actual_actions = np.zeros(self.action_space.shape)
        ee_position, ee_orientation = self.get_ee_pose()
        ee_position = np.array(ee_position)
        ee_orientation = np.array(ee_orientation)
        object_position = np.array(self.get_object_position(self.object_names[0]))
        distance = object_position - ee_position
        distance_mag = np.linalg.norm(distance)
        if distance_mag < 0.02:
            if self.gripper.is_open:
                self.__actual_actions[0] = -1.0
                self.__actual_actions[1:4] = np.zeros((3,))
            else:
                self.__actual_actions[0] = -1.0
                self.__actual_actions[1:4] = np.array((0.0, 0.0, 1.0))
            if self.__full_3d_orientation:
                pass
            else:
                self.__actual_actions[4] = 0.0
        else:
            self.__actual_actions[0] = 1.0
            if distance_mag > self._relative_position_scaling_factor:
                relative_position = distance / distance_mag
            else:
                relative_position = distance / self._relative_position_scaling_factor
            self.__actual_actions[1:4] = relative_position
            distance_mag_xy = np.linalg.norm(distance[:2])
            if distance_mag_xy > 0.01 and ee_position[2] < 0.1:
                self.__actual_actions[3] = max(0.0, self.__actual_actions[3])
            object_orientation = quat_to_xyzw(np.array(self.get_object_orientation(self.object_names[0])))
            if self.__full_3d_orientation:
                pass
            else:
                current_ee_yaw = Rotation.from_quat(ee_orientation).as_euler('xyz')[2]
                current_object_yaw = Rotation.from_quat(object_orientation).as_euler('xyz')[2]
                yaw_diff = current_object_yaw - current_ee_yaw
                if yaw_diff > np.pi:
                    yaw_diff -= np.pi / 2
                elif yaw_diff < -np.pi:
                    yaw_diff += np.pi / 2
                yaw_diff = min(1.0, 1.0 / (self._z_relative_orientation_scaling_factor / yaw_diff))
                self.__actual_actions[4] = yaw_diff
        if ee_position[2] < 0.025:
            self.__actual_actions[3] = max(0.0, self.__actual_actions[3])
        return self.__actual_actions

def __init__(self, gripper_dead_zone: float, full_3d_orientation: bool, obs_n_stacked: int=1, preload_replay_buffer: bool=False, **kwargs):
    Manipulation.__init__(self, **kwargs)
    self.curriculum = GraspCurriculum(task=self, **kwargs)
    self.__gripper_dead_zone = gripper_dead_zone
    self.__full_3d_orientation = full_3d_orientation
    self.__preload_replay_buffer = preload_replay_buffer
    self._obs_n_stacked = obs_n_stacked
    self.__stacked_obs = deque([], maxlen=self._obs_n_stacked)

def get_info(self) -> Dict:
    info = self.curriculum.get_info()
    if self.__preload_replay_buffer:
        info.update({'actual_actions': self.__actual_actions})
    return info

class ReachOctree(Reach, abc.ABC):
    _octree_min_bound: Tuple[float, float, float] = (0.15, -0.3, 0.0)
    _octree_max_bound: Tuple[float, float, float] = (0.75, 0.3, 0.6)

    def __init__(self, octree_reference_frame_id: str, octree_min_bound: Tuple[float, float, float], octree_max_bound: Tuple[float, float, float], octree_depth: int, octree_full_depth: int, octree_include_color: bool, octree_include_intensity: bool, octree_n_stacked: int, octree_max_size: int, camera_type: str='rgbd_camera', **kwargs):
        Reach.__init__(self, **kwargs)
        self._octree_n_stacked = octree_n_stacked
        self._octree_max_size = octree_max_size
        self.camera_sub = CameraSubscriber(node=self, topic=Camera.get_points_topic(camera_type), is_point_cloud=True, callback_group=self._callback_group)
        octree_min_bound = (octree_min_bound[0], octree_min_bound[1], octree_min_bound[2] + self.robot_model_class.BASE_LINK_Z_OFFSET)
        octree_max_bound = (octree_max_bound[0], octree_max_bound[1], octree_max_bound[2] + self.robot_model_class.BASE_LINK_Z_OFFSET)
        self.octree_creator = OctreeCreator(node=self, tf2_listener=self.tf2_listener, reference_frame_id=self.substitute_special_frame(octree_reference_frame_id), min_bound=octree_min_bound, max_bound=octree_max_bound, include_color=octree_include_color, include_intensity=octree_include_intensity, depth=octree_depth, full_depth=octree_full_depth)
        self.__stacked_octrees = deque([], maxlen=self._octree_n_stacked)

    def create_observation_space(self) -> ObservationSpace:
        return gym.spaces.Box(low=0, high=255, shape=(self._octree_n_stacked, self._octree_max_size), dtype=np.uint8)

    def get_observation(self) -> Observation:
        point_cloud = self.camera_sub.get_observation()
        octree = self.octree_creator(point_cloud).numpy()
        octree_size = octree.shape[0]
        if octree_size > self._octree_max_size:
            self.get_logger().error(f'Octree is larger than the maximum allowed size of {self._octree_max_size} (exceeded with {octree_size})')
        octree = np.pad(octree, (0, self._octree_max_size - octree_size), 'constant', constant_values=0)
        octree[-4:] = np.ndarray(buffer=np.array([octree_size], dtype=np.uint32).tobytes(), shape=(4,), dtype=np.uint8)
        self.__stacked_octrees.append(octree)
        while not self._octree_n_stacked == len(self.__stacked_octrees):
            self.__stacked_octrees.append(octree)
        observation = Observation(np.array(self.__stacked_octrees, dtype=np.uint8))
        self.get_logger().debug(f'\nobservation: {observation}')
        return observation

    def reset_task(self):
        self.__stacked_octrees.clear()
        Reach.reset_task(self)

def __init__(self, octree_reference_frame_id: str, octree_min_bound: Tuple[float, float, float], octree_max_bound: Tuple[float, float, float], octree_depth: int, octree_full_depth: int, octree_include_color: bool, octree_include_intensity: bool, octree_n_stacked: int, octree_max_size: int, camera_type: str='rgbd_camera', **kwargs):
    Reach.__init__(self, **kwargs)
    self._octree_n_stacked = octree_n_stacked
    self._octree_max_size = octree_max_size
    self.camera_sub = CameraSubscriber(node=self, topic=Camera.get_points_topic(camera_type), is_point_cloud=True, callback_group=self._callback_group)
    octree_min_bound = (octree_min_bound[0], octree_min_bound[1], octree_min_bound[2] + self.robot_model_class.BASE_LINK_Z_OFFSET)
    octree_max_bound = (octree_max_bound[0], octree_max_bound[1], octree_max_bound[2] + self.robot_model_class.BASE_LINK_Z_OFFSET)
    self.octree_creator = OctreeCreator(node=self, tf2_listener=self.tf2_listener, reference_frame_id=self.substitute_special_frame(octree_reference_frame_id), min_bound=octree_min_bound, max_bound=octree_max_bound, include_color=octree_include_color, include_intensity=octree_include_intensity, depth=octree_depth, full_depth=octree_full_depth)
    self.__stacked_octrees = deque([], maxlen=self._octree_n_stacked)

class ReachColorImage(Reach, abc.ABC):

    def __init__(self, camera_width: int, camera_height: int, camera_type: str='camera', monochromatic: bool=False, **kwargs):
        Reach.__init__(self, **kwargs)
        self._camera_width = camera_width
        self._camera_height = camera_height
        self._monochromatic = monochromatic
        self.camera_sub = CameraSubscriber(node=self, topic=Camera.get_color_topic(camera_type), is_point_cloud=False, callback_group=self._callback_group)

    def create_observation_space(self) -> ObservationSpace:
        return gym.spaces.Box(low=0, high=255, shape=(self._camera_height, self._camera_width, 1 if self._monochromatic else 3), dtype=np.uint8)

    def get_observation(self) -> Observation:
        image = self.camera_sub.get_observation()
        assert image.width == self._camera_width and image.height == self._camera_height, f'Error: Resolution of the input image does not match the configured observation space. ({image.width}x{image.height} instead of {self._camera_width}x{self._camera_height})'
        color_image = np.array(image.data, dtype=np.uint8).reshape(self._camera_height, self._camera_width, 3)
        if self._monochromatic:
            observation = Observation(color_image[:, :, 0])
        else:
            observation = Observation(color_image)
        self.get_logger().debug(f'\nobservation: {observation}')
        return observation

def __init__(self, camera_width: int, camera_height: int, camera_type: str='camera', monochromatic: bool=False, **kwargs):
    Reach.__init__(self, **kwargs)
    self._camera_width = camera_width
    self._camera_height = camera_height
    self._monochromatic = monochromatic
    self.camera_sub = CameraSubscriber(node=self, topic=Camera.get_color_topic(camera_type), is_point_cloud=False, callback_group=self._callback_group)

class Reach(Manipulation, abc.ABC):

    def __init__(self, sparse_reward: bool, act_quick_reward: float, required_accuracy: float, **kwargs):
        Manipulation.__init__(self, **kwargs)
        self._sparse_reward: bool = sparse_reward
        self._act_quick_reward = act_quick_reward if act_quick_reward >= 0.0 else -act_quick_reward
        self._required_accuracy: float = required_accuracy
        self._is_done: bool = False
        self._previous_distance: float = None
        self.initial_gripper_joint_positions = self.robot_model_class.CLOSED_GRIPPER_JOINT_POSITIONS

    def create_action_space(self) -> ActionSpace:
        return gym.spaces.Box(low=-1.0, high=1.0, shape=(3,), dtype=np.float32)

    def create_observation_space(self) -> ObservationSpace:
        return gym.spaces.Box(low=-np.inf, high=np.inf, shape=(6,), dtype=np.float32)

    def set_action(self, action: Action):
        self.get_logger().debug(f'action: {action}')
        if self._use_servo:
            linear = action[0:3]
            self.servo(linear=linear)
        else:
            position = self.get_relative_ee_position(action[0:3])
            quat_xyzw = (1.0, 0.0, 0.0, 0.0)
            self.moveit2.move_to_pose(position=position, quat_xyzw=quat_xyzw)

    def get_observation(self) -> Observation:
        ee_position = self.get_ee_position()
        target_position = self.get_object_position(object_model=self.object_names[0])
        observation = Observation(np.concatenate([ee_position, target_position], dtype=np.float32))
        self.get_logger().debug(f'\nobservation: {observation}')
        return observation

    def get_reward(self) -> Reward:
        reward = 0.0
        current_distance = self.get_distance_to_target()
        if current_distance < self._required_accuracy:
            self._is_done = True
            if self._sparse_reward:
                reward += 1.0
        if not self._sparse_reward:
            reward += self._previous_distance - current_distance
            self._previous_distance = current_distance
        reward -= self._act_quick_reward
        self.get_logger().debug(f'reward: {reward}')
        return Reward(reward)

    def is_done(self) -> bool:
        done = self._is_done
        self.get_logger().debug(f'done: {done}')
        return done

    def reset_task(self):
        Manipulation.reset_task(self)
        self._is_done = False
        if not self._sparse_reward:
            self._previous_distance = self.get_distance_to_target()
        self.get_logger().debug(f'\ntask reset')

    def get_distance_to_target(self) -> Tuple[float, float, float]:
        ee_position = self.get_ee_position()
        object_position = self.get_object_position(object_model=self.object_names[0])
        return distance_to_nearest_point(origin=ee_position, points=[object_position])

def __init__(self, sparse_reward: bool, act_quick_reward: float, required_accuracy: float, **kwargs):
    Manipulation.__init__(self, **kwargs)
    self._sparse_reward: bool = sparse_reward
    self._act_quick_reward = act_quick_reward if act_quick_reward >= 0.0 else -act_quick_reward
    self._required_accuracy: float = required_accuracy
    self._is_done: bool = False
    self._previous_distance: float = None
    self.initial_gripper_joint_positions = self.robot_model_class.CLOSED_GRIPPER_JOINT_POSITIONS

class ReachDepthImage(Reach, abc.ABC):

    def __init__(self, camera_width: int, camera_height: int, camera_type: str='depth_camera', **kwargs):
        Reach.__init__(self, **kwargs)
        self._camera_width = camera_width
        self._camera_height = camera_height
        self.camera_sub = CameraSubscriber(node=self, topic=Camera.get_depth_topic(camera_type), is_point_cloud=False, callback_group=self._callback_group)

    def create_observation_space(self) -> ObservationSpace:
        return gym.spaces.Box(low=0, high=np.inf, shape=(self._camera_height, self._camera_width, 1), dtype=np.float32)

    def get_observation(self) -> Observation:
        image = self.camera_sub.get_observation()
        depth_image = np.frombuffer(image.data, dtype=np.float32).reshape(self._camera_height, self._camera_width, 1)
        depth_image[depth_image == np.inf] = 0.0
        observation = Observation(depth_image)
        self.get_logger().debug(f'\nobservation: {observation}')
        return observation

def __init__(self, camera_width: int, camera_height: int, camera_type: str='depth_camera', **kwargs):
    Reach.__init__(self, **kwargs)
    self._camera_width = camera_width
    self._camera_height = camera_height
    self.camera_sub = CameraSubscriber(node=self, topic=Camera.get_depth_topic(camera_type), is_point_cloud=False, callback_group=self._callback_group)

class GraspCurriculum(StageRewardCurriculum, SuccessRateImpl, WorkspaceScaleCurriculum, ObjectSpawnVolumeScaleCurriculum, ObjectCountCurriculum, ArmStuckChecker):
    """
    Curriculum learning implementation for grasp task that provides termination (success/fail) and reward for each stage of the task.
    """

    def __init__(self, task: Task, stages_base_reward: float, reach_required_distance: float, lift_required_height: float, persistent_reward_each_step: float, persistent_reward_terrain_collision: float, persistent_reward_all_objects_outside_workspace: float, persistent_reward_arm_stuck: float, enable_stage_reward_curriculum: bool, enable_workspace_scale_curriculum: bool, enable_object_spawn_volume_scale_curriculum: bool, enable_object_count_curriculum: bool, reach_required_distance_min: Optional[float]=None, reach_required_distance_max: Optional[float]=None, reach_required_distance_max_threshold: Optional[float]=None, lift_required_height_min: Optional[float]=None, lift_required_height_max: Optional[float]=None, lift_required_height_max_threshold: Optional[float]=None, **kwargs):
        StageRewardCurriculum.__init__(self, curriculum_stage=GraspStage, **kwargs)
        SuccessRateImpl.__init__(self, **kwargs)
        WorkspaceScaleCurriculum.__init__(self, task=task, success_rate_impl=self, **kwargs)
        ObjectSpawnVolumeScaleCurriculum.__init__(self, task=task, success_rate_impl=self, **kwargs)
        ObjectCountCurriculum.__init__(self, task=task, success_rate_impl=self, **kwargs)
        ArmStuckChecker.__init__(self, task=task, **kwargs)
        self.__task = task
        self.__stages_base_reward = stages_base_reward
        self.reach_required_distance = reach_required_distance
        self.lift_required_height = lift_required_height
        self.__persistent_reward_each_step = persistent_reward_each_step
        self.__persistent_reward_terrain_collision = persistent_reward_terrain_collision
        self.__persistent_reward_all_objects_outside_workspace = persistent_reward_all_objects_outside_workspace
        self.__persistent_reward_arm_stuck = persistent_reward_arm_stuck
        self.__enable_stage_reward_curriculum = enable_stage_reward_curriculum
        self.__enable_workspace_scale_curriculum = enable_workspace_scale_curriculum
        self.__enable_object_spawn_volume_scale_curriculum = enable_object_spawn_volume_scale_curriculum
        self.__enable_object_count_curriculum = enable_object_count_curriculum
        if self.__persistent_reward_each_step > 0.0:
            self.__persistent_reward_each_step *= -1.0
        if self.__persistent_reward_terrain_collision > 0.0:
            self.__persistent_reward_terrain_collision *= -1.0
        if self.__persistent_reward_all_objects_outside_workspace > 0.0:
            self.__persistent_reward_all_objects_outside_workspace *= -1.0
        if self.__persistent_reward_arm_stuck > 0.0:
            self.__persistent_reward_arm_stuck *= -1.0
        reach_required_distance_min = reach_required_distance_min if reach_required_distance_min is not None else reach_required_distance
        reach_required_distance_max = reach_required_distance_max if reach_required_distance_max is not None else reach_required_distance
        reach_required_distance_max_threshold = reach_required_distance_max_threshold if reach_required_distance_max_threshold is not None else 0.5
        self.__reach_required_distance_curriculum_enabled = not reach_required_distance_min == reach_required_distance_max
        if self.__reach_required_distance_curriculum_enabled:
            self.__reach_required_distance_curriculum = AttributeCurriculum(success_rate_impl=self, attribute_owner=self, attribute_name='reach_required_distance', initial_value=reach_required_distance_min, target_value=reach_required_distance_max, target_value_threshold=reach_required_distance_max_threshold)
        lift_required_height_min = lift_required_height_min if lift_required_height_min is not None else lift_required_height
        lift_required_height_max = lift_required_height_max if lift_required_height_max is not None else lift_required_height
        lift_required_height_max_threshold = lift_required_height_max_threshold if lift_required_height_max_threshold is not None else 0.5
        lift_required_height += task.robot_model_class.BASE_LINK_Z_OFFSET
        lift_required_height_min += task.robot_model_class.BASE_LINK_Z_OFFSET
        lift_required_height_max += task.robot_model_class.BASE_LINK_Z_OFFSET
        lift_required_height_max_threshold += task.robot_model_class.BASE_LINK_Z_OFFSET
        self.__lift_required_height_curriculum_enabled = not lift_required_height_min == lift_required_height_max
        if self.__lift_required_height_curriculum_enabled:
            self.__lift_required_height_curriculum = AttributeCurriculum(success_rate_impl=self, attribute_owner=self, attribute_name='lift_required_height', initial_value=lift_required_height_min, target_value=lift_required_height_max, target_value_threshold=lift_required_height_max_threshold)

    def get_reward(self) -> Reward:
        if self.__enable_stage_reward_curriculum:
            return StageRewardCurriculum.get_reward(self, ee_position=self.__task.get_ee_position(), object_positions=self.__task.get_object_positions(), touched_objects=self.__task.get_touched_objects(), grasped_objects=self.__task.get_grasped_objects())
        else:
            return StageRewardCurriculum.get_reward(self, only_last_stage=True, object_positions=self.__task.get_object_positions(), grasped_objects=self.__task.get_grasped_objects())

    def is_done(self) -> bool:
        return StageRewardCurriculum.is_done(self)

    def get_info(self) -> Dict:
        info = StageRewardCurriculum.get_info(self)
        info.update(SuccessRateImpl.get_info(self))
        if self.__enable_workspace_scale_curriculum:
            info.update(WorkspaceScaleCurriculum.get_info(self))
        if self.__enable_object_spawn_volume_scale_curriculum:
            info.update(ObjectSpawnVolumeScaleCurriculum.get_info(self))
        if self.__enable_object_count_curriculum:
            info.update(ObjectCountCurriculum.get_info(self))
        if self.__persistent_reward_arm_stuck:
            info.update(ArmStuckChecker.get_info(self))
        if self.__reach_required_distance_curriculum_enabled:
            info.update(self.__reach_required_distance_curriculum.get_info())
        if self.__lift_required_height_curriculum_enabled:
            info.update(self.__lift_required_height_curriculum.get_info())
        return info

    def reset_task(self):
        StageRewardCurriculum.reset_task(self)
        if self.__enable_workspace_scale_curriculum:
            WorkspaceScaleCurriculum.reset_task(self)
        if self.__enable_object_spawn_volume_scale_curriculum:
            ObjectSpawnVolumeScaleCurriculum.reset_task(self)
        if self.__enable_object_count_curriculum:
            ObjectCountCurriculum.reset_task(self)
        if self.__persistent_reward_arm_stuck:
            ArmStuckChecker.reset_task(self)
        if self.__reach_required_distance_curriculum_enabled:
            self.__reach_required_distance_curriculum.reset_task()
        if self.__lift_required_height_curriculum_enabled:
            self.__lift_required_height_curriculum.reset_task()

    def on_episode_success(self):
        self.update_success_rate(is_success=True)

    def on_episode_failure(self):
        self.update_success_rate(is_success=False)

    def on_episode_timeout(self):
        self.update_success_rate(is_success=False)

    def get_reward_REACH(self, ee_position: Tuple[float, float, float], object_positions: Dict[str, Tuple[float, float, float]], **kwargs) -> float:
        if not object_positions:
            return 0.0
        nearest_object_distance = distance_to_nearest_point(origin=ee_position, points=list(object_positions.values()))
        self.__task.get_logger().debug(f'[Curriculum] Distance to nearest object: {nearest_object_distance}')
        if nearest_object_distance < self.reach_required_distance:
            self.__task.get_logger().info(f'[Curriculum] An object is now closer than the required distance of {self.reach_required_distance}')
            self.stages_completed_this_episode[GraspStage.REACH] = True
            return self.__stages_base_reward
        else:
            return 0.0

    def get_reward_TOUCH(self, touched_objects: List[str], **kwargs) -> float:
        if touched_objects:
            self.__task.get_logger().info(f'[Curriculum] Touched objects: {touched_objects}')
            self.stages_completed_this_episode[GraspStage.TOUCH] = True
            return self.__stages_base_reward
        else:
            return 0.0

    def get_reward_GRASP(self, grasped_objects: List[str], **kwargs) -> float:
        if grasped_objects:
            self.__task.get_logger().info(f'[Curriculum] Grasped objects: {grasped_objects}')
            self.stages_completed_this_episode[GraspStage.GRASP] = True
            return self.__stages_base_reward
        else:
            return 0.0

    def get_reward_LIFT(self, object_positions: Dict[str, Tuple[float, float, float]], grasped_objects: List[str], **kwargs) -> float:
        if not (grasped_objects or object_positions):
            return 0.0
        for grasped_object in grasped_objects:
            grasped_object_height = object_positions[grasped_object][2]
            self.__task.get_logger().debug(f"[Curriculum] Height of grasped object '{grasped_objects}': {grasped_object_height}")
            if grasped_object_height > self.lift_required_height:
                self.__task.get_logger().info(f'[Curriculum] Lifted object: {grasped_object}')
                self.stages_completed_this_episode[GraspStage.LIFT] = True
                return self.__stages_base_reward
        return 0.0

    def get_persistent_reward(self, object_positions: Dict[str, Tuple[float, float, float]], **kwargs) -> float:
        reward = self.__persistent_reward_each_step
        if self.__persistent_reward_terrain_collision:
            if self.__task.check_terrain_collision():
                self.__task.get_logger().info('[Curriculum] Robot collided with the terrain')
                reward += self.__persistent_reward_terrain_collision
        if self.__persistent_reward_all_objects_outside_workspace:
            if self.__task.check_all_objects_outside_workspace(object_positions=object_positions):
                self.__task.get_logger().warn('[Curriculum] All objects are outside of the workspace')
                reward += self.__persistent_reward_all_objects_outside_workspace
                self.episode_failed = True
        if self.__persistent_reward_arm_stuck:
            if ArmStuckChecker.is_robot_stuck(self):
                self.__task.get_logger().error(f'[Curriculum] Robot appears to be stuck, resetting...')
                reward += self.__persistent_reward_arm_stuck
                self.episode_failed = True
        return reward

def __init__(self, task: Task, stages_base_reward: float, reach_required_distance: float, lift_required_height: float, persistent_reward_each_step: float, persistent_reward_terrain_collision: float, persistent_reward_all_objects_outside_workspace: float, persistent_reward_arm_stuck: float, enable_stage_reward_curriculum: bool, enable_workspace_scale_curriculum: bool, enable_object_spawn_volume_scale_curriculum: bool, enable_object_count_curriculum: bool, reach_required_distance_min: Optional[float]=None, reach_required_distance_max: Optional[float]=None, reach_required_distance_max_threshold: Optional[float]=None, lift_required_height_min: Optional[float]=None, lift_required_height_max: Optional[float]=None, lift_required_height_max_threshold: Optional[float]=None, **kwargs):
    StageRewardCurriculum.__init__(self, curriculum_stage=GraspStage, **kwargs)
    SuccessRateImpl.__init__(self, **kwargs)
    WorkspaceScaleCurriculum.__init__(self, task=task, success_rate_impl=self, **kwargs)
    ObjectSpawnVolumeScaleCurriculum.__init__(self, task=task, success_rate_impl=self, **kwargs)
    ObjectCountCurriculum.__init__(self, task=task, success_rate_impl=self, **kwargs)
    ArmStuckChecker.__init__(self, task=task, **kwargs)
    self.__task = task
    self.__stages_base_reward = stages_base_reward
    self.reach_required_distance = reach_required_distance
    self.lift_required_height = lift_required_height
    self.__persistent_reward_each_step = persistent_reward_each_step
    self.__persistent_reward_terrain_collision = persistent_reward_terrain_collision
    self.__persistent_reward_all_objects_outside_workspace = persistent_reward_all_objects_outside_workspace
    self.__persistent_reward_arm_stuck = persistent_reward_arm_stuck
    self.__enable_stage_reward_curriculum = enable_stage_reward_curriculum
    self.__enable_workspace_scale_curriculum = enable_workspace_scale_curriculum
    self.__enable_object_spawn_volume_scale_curriculum = enable_object_spawn_volume_scale_curriculum
    self.__enable_object_count_curriculum = enable_object_count_curriculum
    if self.__persistent_reward_each_step > 0.0:
        self.__persistent_reward_each_step *= -1.0
    if self.__persistent_reward_terrain_collision > 0.0:
        self.__persistent_reward_terrain_collision *= -1.0
    if self.__persistent_reward_all_objects_outside_workspace > 0.0:
        self.__persistent_reward_all_objects_outside_workspace *= -1.0
    if self.__persistent_reward_arm_stuck > 0.0:
        self.__persistent_reward_arm_stuck *= -1.0
    reach_required_distance_min = reach_required_distance_min if reach_required_distance_min is not None else reach_required_distance
    reach_required_distance_max = reach_required_distance_max if reach_required_distance_max is not None else reach_required_distance
    reach_required_distance_max_threshold = reach_required_distance_max_threshold if reach_required_distance_max_threshold is not None else 0.5
    self.__reach_required_distance_curriculum_enabled = not reach_required_distance_min == reach_required_distance_max
    if self.__reach_required_distance_curriculum_enabled:
        self.__reach_required_distance_curriculum = AttributeCurriculum(success_rate_impl=self, attribute_owner=self, attribute_name='reach_required_distance', initial_value=reach_required_distance_min, target_value=reach_required_distance_max, target_value_threshold=reach_required_distance_max_threshold)
    lift_required_height_min = lift_required_height_min if lift_required_height_min is not None else lift_required_height
    lift_required_height_max = lift_required_height_max if lift_required_height_max is not None else lift_required_height
    lift_required_height_max_threshold = lift_required_height_max_threshold if lift_required_height_max_threshold is not None else 0.5
    lift_required_height += task.robot_model_class.BASE_LINK_Z_OFFSET
    lift_required_height_min += task.robot_model_class.BASE_LINK_Z_OFFSET
    lift_required_height_max += task.robot_model_class.BASE_LINK_Z_OFFSET
    lift_required_height_max_threshold += task.robot_model_class.BASE_LINK_Z_OFFSET
    self.__lift_required_height_curriculum_enabled = not lift_required_height_min == lift_required_height_max
    if self.__lift_required_height_curriculum_enabled:
        self.__lift_required_height_curriculum = AttributeCurriculum(success_rate_impl=self, attribute_owner=self, attribute_name='lift_required_height', initial_value=lift_required_height_min, target_value=lift_required_height_max, target_value_threshold=lift_required_height_max_threshold)

def get_info(self) -> Dict:
    info = StageRewardCurriculum.get_info(self)
    info.update(SuccessRateImpl.get_info(self))
    if self.__enable_workspace_scale_curriculum:
        info.update(WorkspaceScaleCurriculum.get_info(self))
    if self.__enable_object_spawn_volume_scale_curriculum:
        info.update(ObjectSpawnVolumeScaleCurriculum.get_info(self))
    if self.__enable_object_count_curriculum:
        info.update(ObjectCountCurriculum.get_info(self))
    if self.__persistent_reward_arm_stuck:
        info.update(ArmStuckChecker.get_info(self))
    if self.__reach_required_distance_curriculum_enabled:
        info.update(self.__reach_required_distance_curriculum.get_info())
    if self.__lift_required_height_curriculum_enabled:
        info.update(self.__lift_required_height_curriculum.get_info())
    return info

class ArmStuckChecker:
    """
    Checker for arm getting stuck.
    """
    INFO_CURRICULUM_PREFIX: str = 'curriculum/'

    def __init__(self, task: Task, arm_stuck_n_steps: int, arm_stuck_min_joint_difference_norm: float, **kwargs):
        self.__task = task
        self.__arm_stuck_min_joint_difference_norm = arm_stuck_min_joint_difference_norm
        self.__previous_joint_positions: Deque[np.ndarray] = deque([], maxlen=arm_stuck_n_steps)
        self.__robot_stuck_total_counter: int = 0
        self.__arm_joint_indices = None

    def get_info(self) -> Dict:
        info = {f'{self.INFO_CURRICULUM_PREFIX}robot_stuck_count': self.__robot_stuck_total_counter}
        return info

    def reset_task(self):
        self.__previous_joint_positions.clear()
        joint_positions = self.__get_arm_joint_positions()
        if joint_positions is not None:
            self.__previous_joint_positions.append(joint_positions)

    def is_robot_stuck(self) -> bool:
        current_joint_positions = self.__get_arm_joint_positions()
        if current_joint_positions is not None:
            self.__previous_joint_positions.append(current_joint_positions)
        if len(self.__previous_joint_positions) < self.__previous_joint_positions.maxlen:
            return False
        if len(current_joint_positions) != len(self.__previous_joint_positions[0]):
            return False
        joint_difference_norm = np.linalg.norm(current_joint_positions - self.__previous_joint_positions[0])
        if joint_difference_norm > self.__arm_stuck_min_joint_difference_norm:
            return False
        joint_difference_norms = np.linalg.norm(current_joint_positions - list(itertools.islice(self.__previous_joint_positions, 1, None)), axis=1)
        is_stuck = all(joint_difference_norms < self.__arm_stuck_min_joint_difference_norm)
        self.__robot_stuck_total_counter += int(is_stuck)
        return is_stuck

    def __get_arm_joint_positions(self) -> Optional[np.ndarray[float]]:
        joint_state = self.__task.moveit2.joint_state
        if joint_state is None:
            return None
        if self.__arm_joint_indices is None:
            self.__arm_joint_indices = [i for i, joint_name in enumerate(joint_state.name) if joint_name in self.__task.robot_arm_joint_names]
        return np.take(joint_state.position, self.__arm_joint_indices)

def __init__(self, task: Task, arm_stuck_n_steps: int, arm_stuck_min_joint_difference_norm: float, **kwargs):
    self.__task = task
    self.__arm_stuck_min_joint_difference_norm = arm_stuck_min_joint_difference_norm
    self.__previous_joint_positions: Deque[np.ndarray] = deque([], maxlen=arm_stuck_n_steps)
    self.__robot_stuck_total_counter: int = 0
    self.__arm_joint_indices = None

class Camera(model_wrapper.ModelWrapper):

    def __init__(self, world: scenario.World, name: Union[str, None]=None, position: List[float]=(0, 0, 0), orientation: List[float]=(1, 0, 0, 0), static: bool=True, camera_type: str='rgbd_camera', width: int=212, height: int=120, image_format: str='R8G8B8', update_rate: int=15, horizontal_fov: float=1.567821, vertical_fov: float=1.022238, clip_color: List[float]=(0.02, 1000.0), clip_depth: List[float]=(0.02, 10.0), noise_mean: float=None, noise_stddev: float=None, ros2_bridge_color: bool=False, ros2_bridge_depth: bool=False, ros2_bridge_points: bool=False, visibility_mask: int=0, visual: Optional[str]=None):
        if name is not None:
            model_name = get_unique_model_name(world, name)
        else:
            model_name = get_unique_model_name(world, camera_type)
        self._model_name = model_name
        initial_pose = scenario.Pose(position, orientation)
        if visual:
            use_mesh: bool = False
            if 'intel_realsense_d435' == visual:
                use_mesh = True
                model_path = ModelCollectionRandomizer.get_collection_paths(owner='OpenRobotics', collection='', model_name='Intel RealSense D435')[0]
                mesh_dir = os.path.join(model_path, 'meshes')
                texture_dir = os.path.join(model_path, 'materials', 'textures')
                mesh_path_visual = os.path.join(mesh_dir, 'realsense.dae')
                if not os.path.exists(mesh_path_visual):
                    raise ValueError(f"Visual mesh '{mesh_path_visual}' for Camera model is not a valid file.")
                albedo_map = None
                normal_map = None
                roughness_map = None
                metalness_map = None
                if texture_dir:
                    texture_files = os.listdir(texture_dir)
                    for texture in texture_files:
                        texture_lower = texture.lower()
                        if 'basecolor' in texture_lower or 'albedo' in texture_lower:
                            albedo_map = os.path.join(texture_dir, texture)
                        elif 'normal' in texture_lower:
                            normal_map = os.path.join(texture_dir, texture)
                        elif 'roughness' in texture_lower:
                            roughness_map = os.path.join(texture_dir, texture)
                        elif 'specular' in texture_lower or 'metalness' in texture_lower:
                            metalness_map = os.path.join(texture_dir, texture)
                if not (albedo_map and normal_map and roughness_map and metalness_map):
                    raise ValueError(f'Not all textures for Camera model were found.')
        sdf = f'<sdf version="1.9">\n            <model name="{model_name}">\n                <static>{static}</static>\n                <link name="{self.link_name}">\n                    <sensor name="camera" type="{camera_type}">\n                        <topic>{model_name}</topic>\n                        <always_on>true</always_on>\n                        <update_rate>{update_rate}</update_rate>\n                        <camera name="{model_name}_camera">\n                            <image>\n                                <width>{width}</width>\n                                <height>{height}</height>\n                                <format>{image_format}</format>\n                            </image>\n                            <horizontal_fov>{horizontal_fov}</horizontal_fov>\n                            <vertical_fov>{vertical_fov}</vertical_fov>\n                            <clip>\n                                <near>{clip_color[0]}</near>\n                                <far>{clip_color[1]}</far>\n                            </clip>\n                            {(f'<depth_camera>\n                                <clip>\n                                    <near>{clip_depth[0]}</near>\n                                    <far>{clip_depth[1]}</far>\n                                </clip>\n                            </depth_camera>' if 'rgbd' in model_name else '')}\n                            {(f'<noise>\n                                <type>gaussian</type>\n                                <mean>{noise_mean}</mean>\n                                <stddev>{noise_stddev}</stddev>\n                            </noise>' if noise_mean is not None and noise_stddev is not None else '')}\n                            <visibility_mask>{visibility_mask}</visibility_mask>\n                        </camera>\n                        <visualize>true</visualize>\n                    </sensor>\n                    {(f'\n                        <visual name="{model_name}_visual_lens">\n                            <pose>-0.01 0 0 0 1.5707963 0</pose>\n                            <geometry>\n                                <cylinder>\n                                    <radius>0.02</radius>\n                                    <length>0.02</length>\n                                </cylinder>\n                            </geometry>\n                            <material>\n                                <ambient>0.0 0.8 0.0</ambient>\n                                <diffuse>0.0 0.8 0.0</diffuse>\n                                <specular>0.0 0.8 0.0</specular>\n                            </material>\n                        </visual>\n                        <visual name="{model_name}_visual_body">\n                            <pose>-0.05 0 0 0 0 0</pose>\n                            <geometry>\n                                <box>\n                                    <size>0.06 0.05 0.05</size>\n                                </box>\n                            </geometry>\n                            <material>\n                                <ambient>0.0 0.8 0.0</ambient>\n                                <diffuse>0.0 0.8 0.0</diffuse>\n                                <specular>0.0 0.8 0.0</specular>\n                            </material>\n                        </visual>\n                        ' if visual and (not use_mesh) else '')}\n                        {(f'\n                        <inertial>\n                            <mass>0.0615752</mass>\n                            <inertia>\n                                <ixx>9.108e-05</ixx>\n                                <ixy>0.0</ixy>\n                                <ixz>0.0</ixz>\n                                <iyy>2.51e-06</iyy>\n                                <iyz>0.0</iyz>\n                                <izz>8.931e-05</izz>\n                            </inertia>\n                        </inertial>\n                        <visual name="{model_name}_visual">\n                            <pose>0 0 0 0 0 1.5707963</pose>\n                            <geometry>\n                                <mesh>\n                                    <uri>{mesh_path_visual}</uri>\n                                    <submesh>\n                                        <name>RealSense</name>\n                                        <center>false</center>\n                                    </submesh>\n                                </mesh>\n                            </geometry>\n                            <material>\n                                <diffuse>1 1 1 1</diffuse>\n                                <specular>1 1 1 1</specular>\n                                <pbr>\n                                    <metal>\n                                        <albedo_map>{albedo_map}</albedo_map>\n                                        <normal_map>{normal_map}</normal_map>\n                                        <roughness_map>{roughness_map}</roughness_map>\n                                        <metalness_map>{metalness_map}</metalness_map>\n                                    </metal>\n                                </pbr>\n                            </material>\n                        </visual>\n                        ' if visual and use_mesh else '')}\n                </link>\n            </model>\n        </sdf>'
        ok_model = world.to_gazebo().insert_model_from_string(sdf, initial_pose, model_name)
        if not ok_model:
            raise RuntimeError('Failed to insert ' + model_name)
        model = world.get_model(model_name)
        model_wrapper.ModelWrapper.__init__(self, model=model)
        if ros2_bridge_color or ros2_bridge_depth or ros2_bridge_points:
            self.__threads = []
            if ros2_bridge_color:
                self.__threads.append(Thread(target=self.construct_ros2_bridge, args=(self.color_topic, 'sensor_msgs/msg/Image', 'ignition.msgs.Image'), daemon=True))
            if ros2_bridge_depth:
                self.__threads.append(Thread(target=self.construct_ros2_bridge, args=(self.depth_topic, 'sensor_msgs/msg/Image', 'ignition.msgs.Image'), daemon=True))
            if ros2_bridge_points:
                self.__threads.append(Thread(target=self.construct_ros2_bridge, args=(self.points_topic, 'sensor_msgs/msg/PointCloud2', 'ignition.msgs.PointCloudPacked'), daemon=True))
            for thread in self.__threads:
                thread.start()

    def __del__(self):
        if hasattr(self, '__threads'):
            for thread in self.__threads:
                thread.join()

    @classmethod
    def construct_ros2_bridge(self, topic: str, ros_msg: str, ign_msg: str):
        node_name = 'parameter_bridge' + topic.replace('/', '_')
        command = f'ros2 run ros_ign_bridge parameter_bridge {topic}@{ros_msg}[{ign_msg} ' + f'--ros-args --remap __node:={node_name} --ros-args -p use_sim_time:=true'
        os.system(command)

    @classmethod
    def get_frame_id(cls, model_name: str) -> str:
        return f'{model_name}/{model_name}_link/camera'

    @property
    def frame_id(self) -> str:
        return self.get_frame_id(self._model_name)

    @classmethod
    def get_color_topic(cls, model_name: str) -> str:
        return f'/{model_name}/image' if 'rgbd' in model_name else f'/{model_name}'

    @property
    def color_topic(self) -> str:
        return self.get_color_topic(self._model_name)

    @classmethod
    def get_depth_topic(cls, model_name: str) -> str:
        return f'/{model_name}/depth_image' if 'rgbd' in model_name else f'/{model_name}'

    @property
    def depth_topic(self) -> str:
        return self.get_depth_topic(self._model_name)

    @classmethod
    def get_points_topic(cls, model_name: str) -> str:
        return f'/{model_name}/points'

    @property
    def points_topic(self) -> str:
        return self.get_points_topic(self._model_name)

    @classmethod
    def get_link_name(cls, model_name: str) -> str:
        return f'{model_name}_link'

    @property
    def link_name(self) -> str:
        return self.get_link_name(self._model_name)

@property
def color_topic(self) -> str:
    return self.get_color_topic(self._model_name)

@property
def depth_topic(self) -> str:
    return self.get_depth_topic(self._model_name)

@property
def points_topic(self) -> str:
    return self.get_points_topic(self._model_name)

