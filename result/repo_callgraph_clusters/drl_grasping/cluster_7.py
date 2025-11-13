# Cluster 7

def sample_sac_params(trial: optuna.Trial, octree_observations: bool=True, octree_depth: int=4, octree_full_depth: int=2, octree_channels_in: int=7, octree_fast_conv: bool=True, octree_batch_norm: bool=True) -> Dict[str, Any]:
    """
    Sampler for SAC hyperparameters
    """
    buffer_size = 150000
    learning_starts = 5000
    batch_size = trial.suggest_categorical('batch_size', [32, 64, 128])
    learning_rate = trial.suggest_float('learning_rate', low=1e-06, high=0.001, log=True)
    gamma = trial.suggest_float('gamma', low=0.98, high=1.0, log=True)
    tau = trial.suggest_float('tau', low=0.001, high=0.025, log=True)
    ent_coef = 'auto_0.5_0.1'
    target_entropy = 'auto'
    noise_std = trial.suggest_float('noise_std', low=0.01, high=0.2, log=True)
    action_noise = NormalActionNoise(mean=np.zeros(trial.n_actions), sigma=np.ones(trial.n_actions) * noise_std)
    train_freq = 1
    gradient_steps = trial.suggest_categorical('gradient_steps', [1, 2])
    policy_kwargs = dict()
    net_arch = trial.suggest_categorical('net_arch', ['small [256, 128]', 'medium [384, 256]', 'big [512, 384]'])
    policy_kwargs['net_arch'] = {'small [256, 128]': [256, 128], 'medium [384, 256]': [384, 256], 'big [512, 384]': [512, 384]}[net_arch]
    if octree_observations:
        features_extractor_kwargs = dict()
        features_extractor_kwargs['depth'] = octree_depth
        features_extractor_kwargs['full_depth'] = octree_full_depth
        features_extractor_kwargs['channels_in'] = octree_channels_in
        features_extractor_kwargs['channel_multiplier'] = trial.suggest_categorical('channel_multiplier', [8, 16, 32, 64])
        features_extractor_kwargs['features_dim'] = trial.suggest_categorical('features_dim', [256, 512, 768])
        features_extractor_kwargs['fast_conv'] = octree_fast_conv
        features_extractor_kwargs['batch_normalization'] = octree_batch_norm
        policy_kwargs['features_extractor_kwargs'] = features_extractor_kwargs
    return {'buffer_size': buffer_size, 'learning_starts': learning_starts, 'batch_size': batch_size, 'learning_rate': learning_rate, 'gamma': gamma, 'tau': tau, 'ent_coef': ent_coef, 'target_entropy': target_entropy, 'action_noise': action_noise, 'train_freq': train_freq, 'gradient_steps': gradient_steps, 'policy_kwargs': policy_kwargs}

def sample_td3_params(trial: optuna.Trial, octree_observations: bool=True, octree_depth: int=4, octree_full_depth: int=2, octree_channels_in: int=7, octree_fast_conv: bool=True, octree_batch_norm: bool=True) -> Dict[str, Any]:
    """
    Sampler for TD3 hyperparameters
    """
    buffer_size = 150000
    learning_starts = 5000
    batch_size = trial.suggest_categorical('batch_size', [32, 64, 128])
    learning_rate = trial.suggest_float('learning_rate', low=1e-06, high=0.001, log=True)
    gamma = trial.suggest_float('gamma', low=0.98, high=1.0, log=True)
    tau = trial.suggest_float('tau', low=0.001, high=0.025, log=True)
    target_policy_noise = trial.suggest_float('target_policy_noise', low=0.0, high=0.5, log=True)
    target_noise_clip = 0.5
    noise_std = trial.suggest_float('noise_std', low=0.025, high=0.5, log=True)
    action_noise = NormalActionNoise(mean=np.zeros(trial.n_actions), sigma=np.ones(trial.n_actions) * noise_std)
    train_freq = 1
    gradient_steps = trial.suggest_categorical('gradient_steps', [1, 2])
    policy_kwargs = dict()
    net_arch = trial.suggest_categorical('net_arch', ['small [256, 128]', 'medium [384, 256]', 'big [512, 384]'])
    policy_kwargs['net_arch'] = {'small [256, 128]': [256, 128], 'medium [384, 256]': [384, 256], 'big [512, 384]': [512, 384]}[net_arch]
    if octree_observations:
        features_extractor_kwargs = dict()
        features_extractor_kwargs['depth'] = octree_depth
        features_extractor_kwargs['full_depth'] = octree_full_depth
        features_extractor_kwargs['channels_in'] = octree_channels_in
        features_extractor_kwargs['channel_multiplier'] = trial.suggest_categorical('channel_multiplier', [8, 16, 32, 64])
        features_extractor_kwargs['features_dim'] = trial.suggest_categorical('features_dim', [256, 512, 768])
        features_extractor_kwargs['fast_conv'] = octree_fast_conv
        features_extractor_kwargs['batch_normalization'] = octree_batch_norm
        policy_kwargs['features_extractor_kwargs'] = features_extractor_kwargs
    return {'buffer_size': buffer_size, 'learning_starts': learning_starts, 'batch_size': batch_size, 'learning_rate': learning_rate, 'gamma': gamma, 'tau': tau, 'target_policy_noise': target_policy_noise, 'target_noise_clip': target_noise_clip, 'action_noise': action_noise, 'train_freq': train_freq, 'gradient_steps': gradient_steps, 'policy_kwargs': policy_kwargs}

def sample_tqc_params(trial: optuna.Trial, octree_observations: bool=True, octree_depth: int=4, octree_full_depth: int=2, octree_channels_in: int=7) -> Dict[str, Any]:
    """
    Sampler for TQC hyperparameters
    """
    buffer_size = 25000
    learning_starts = 0
    batch_size = 32
    learning_rate = trial.suggest_float('learning_rate', low=2.5e-05, high=0.00075, log=True)
    gamma = 1.0 - trial.suggest_float('gamma', low=0.0001, high=0.025, log=True)
    tau = trial.suggest_float('tau', low=0.0005, high=0.025, log=True)
    ent_coef = 'auto_0.1_0.05'
    target_entropy = 'auto'
    noise_std = trial.suggest_float('noise_std', low=0.01, high=0.1, log=True)
    action_noise = NormalActionNoise(mean=np.zeros(trial.n_actions), sigma=np.ones(trial.n_actions) * noise_std)
    train_freq = 1
    gradient_steps = trial.suggest_categorical('gradient_steps', [1, 2])
    policy_kwargs = dict()
    net_arch = trial.suggest_categorical('net_arch', [128, 256, 384, 512])
    policy_kwargs['net_arch'] = [net_arch] * 2
    policy_kwargs['n_quantiles'] = trial.suggest_int('n_quantiles', low=20, high=40)
    top_quantiles_to_drop_per_net = round(0.08 * policy_kwargs['n_quantiles'])
    policy_kwargs['n_critics'] = trial.suggest_categorical('n_critics', [2, 3])
    if octree_observations:
        features_extractor_kwargs = dict()
        features_extractor_kwargs['depth'] = octree_depth
        features_extractor_kwargs['full_depth'] = octree_full_depth
        features_extractor_kwargs['channels_in'] = octree_channels_in
        features_extractor_kwargs['channel_multiplier'] = trial.suggest_categorical('channel_multiplier', [8, 16, 32])
        features_extractor_kwargs['full_depth_channels'] = trial.suggest_categorical('full_depth_channels', [4, 8, 16])
        features_extractor_kwargs['features_dim'] = trial.suggest_categorical('features_dim', [64, 128, 256])
        features_extractor_kwargs['batch_normalization'] = trial.suggest_categorical('batch_normalization', [True, False])
        policy_kwargs['features_extractor_kwargs'] = features_extractor_kwargs
    return {'buffer_size': buffer_size, 'learning_starts': learning_starts, 'batch_size': batch_size, 'learning_rate': learning_rate, 'gamma': gamma, 'tau': tau, 'ent_coef': ent_coef, 'target_entropy': target_entropy, 'top_quantiles_to_drop_per_net': top_quantiles_to_drop_per_net, 'action_noise': action_noise, 'train_freq': train_freq, 'gradient_steps': gradient_steps, 'policy_kwargs': policy_kwargs}

class ExperimentManager(object):
    """
    Experiment manager: read the hyperparameters,
    preprocess them, create the environment and the RL model.

    Please take a look at `train.py` to have the details for each argument.
    """

    def __init__(self, args: argparse.Namespace, algo: str, env_id: str, log_folder: str, tensorboard_log: str='', n_timesteps: int=0, eval_freq: int=10000, n_eval_episodes: int=5, save_freq: int=-1, hyperparams: Optional[Dict[str, Any]]=None, env_kwargs: Optional[Dict[str, Any]]=None, trained_agent: str='', optimize_hyperparameters: bool=False, storage: Optional[str]=None, study_name: Optional[str]=None, n_trials: int=1, n_jobs: int=1, sampler: str='tpe', pruner: str='median', optimization_log_path: Optional[str]=None, n_startup_trials: int=0, n_evaluations: int=1, truncate_last_trajectory: bool=False, uuid_str: str='', seed: int=0, log_interval: int=0, save_replay_buffer: bool=False, preload_replay_buffer: str='', verbose: int=1, vec_env_type: str='dummy', n_eval_envs: int=1, no_optim_plots: bool=False):
        super(ExperimentManager, self).__init__()
        self.algo = algo
        self.env_id = env_id
        self.custom_hyperparams = hyperparams
        self.env_kwargs = {} if env_kwargs is None else env_kwargs
        self.n_timesteps = n_timesteps
        self.normalize = False
        self.normalize_kwargs = {}
        self.env_wrapper = None
        self.frame_stack = None
        self.seed = seed
        self.optimization_log_path = optimization_log_path
        self.vec_env_class = {'dummy': DummyVecEnv, 'subproc': SubprocVecEnv}[vec_env_type]
        self.vec_env_kwargs = {}
        self.specified_callbacks = []
        self.callbacks = []
        self.save_freq = save_freq
        self.eval_freq = eval_freq
        self.n_eval_episodes = n_eval_episodes
        self.n_eval_envs = n_eval_envs
        self.n_envs = 1
        self.n_actions = None
        self._hyperparams = {}
        self.trained_agent = trained_agent
        self.continue_training = trained_agent.endswith('.zip') and os.path.isfile(trained_agent)
        self.truncate_last_trajectory = truncate_last_trajectory
        self.preload_replay_buffer = preload_replay_buffer
        self._is_atari = self.is_atari(env_id)
        self._is_gazebo_env = self.is_gazebo_env(env_id)
        self.optimize_hyperparameters = optimize_hyperparameters
        self.storage = storage
        self.study_name = study_name
        self.no_optim_plots = no_optim_plots
        self.n_trials = n_trials
        self.n_jobs = n_jobs
        self.sampler = sampler
        self.pruner = pruner
        self.n_startup_trials = n_startup_trials
        self.n_evaluations = n_evaluations
        self.deterministic_eval = not self.is_atari(self.env_id)
        self.log_folder = log_folder
        self.tensorboard_log = None if tensorboard_log == '' else os.path.join(tensorboard_log, env_id)
        self.verbose = verbose
        self.args = args
        self.log_interval = log_interval
        self.save_replay_buffer = save_replay_buffer
        self.log_path = f'{log_folder}/{self.algo}/'
        self.save_path = os.path.join(self.log_path, f'{self.env_id}_{get_latest_run_id(self.log_path, self.env_id) + 1}{uuid_str}')
        self.params_path = f'{self.save_path}/{self.env_id}'

    def setup_experiment(self) -> Optional[BaseAlgorithm]:
        """
        Read hyperparameters, pre-process them (create schedules, wrappers, callbacks, action noise objects)
        create the environment and possibly the model.

        :return: the initialized RL model
        """
        hyperparams, saved_hyperparams = self.read_hyperparameters()
        hyperparams, self.env_wrapper, self.callbacks = self._preprocess_hyperparams(hyperparams)
        self._env = self.create_envs(self.n_envs, no_log=False)
        self.create_log_folder()
        self.create_callbacks()
        self._hyperparams = self._preprocess_action_noise(hyperparams, self._env)
        if self.continue_training:
            model = self._load_pretrained_agent(self._hyperparams, self._env)
        elif self.optimize_hyperparameters:
            return None
        else:
            model = ALGOS[self.algo](env=self._env, tensorboard_log=self.tensorboard_log, seed=self.seed, verbose=self.verbose, **self._hyperparams)
        if self.preload_replay_buffer:
            if self.preload_replay_buffer.endswith('.pkl'):
                replay_buffer_path = self.preload_replay_buffer
            else:
                replay_buffer_path = os.path.join(self.preload_replay_buffer, 'replay_buffer.pkl')
            if os.path.exists(replay_buffer_path):
                print('Pre-loading replay buffer')
                if self.algo == 'her':
                    model.load_replay_buffer(replay_buffer_path, self.truncate_last_trajectory)
                else:
                    model.load_replay_buffer(replay_buffer_path)
            else:
                raise Exception(f'Replay buffer {replay_buffer_path} does not exist')
        self._save_config(saved_hyperparams)
        return model

    def learn(self, model: BaseAlgorithm) -> None:
        """
        :param model: an initialized RL model
        """
        kwargs = {}
        if self.log_interval > -1:
            kwargs = {'log_interval': self.log_interval}
        if len(self.callbacks) > 0:
            kwargs['callback'] = self.callbacks
        if self.continue_training:
            kwargs['reset_num_timesteps'] = False
            model.env.reset()
        try:
            model.learn(self.n_timesteps, **kwargs)
        except Exception as e:
            print(f'Caught an exception during training of the model: {e}')
            self.save_trained_model(model)
        finally:
            try:
                model.env.close()
            except EOFError:
                pass

    def save_trained_model(self, model: BaseAlgorithm) -> None:
        """
        Save trained model optionally with its replay buffer
        and ``VecNormalize`` statistics

        :param model:
        """
        print(f'Saving to {self.save_path}')
        model.save(f'{self.save_path}/{self.env_id}')
        if hasattr(model, 'save_replay_buffer') and self.save_replay_buffer:
            print('Saving replay buffer')
            model.save_replay_buffer(os.path.join(self.save_path, 'replay_buffer.pkl'))
        if self.normalize:
            model.get_vec_normalize_env().save(os.path.join(self.params_path, 'vecnormalize.pkl'))

    def _save_config(self, saved_hyperparams: Dict[str, Any]) -> None:
        """
        Save unprocessed hyperparameters, this can be use later
        to reproduce an experiment.

        :param saved_hyperparams:
        """
        with open(os.path.join(self.params_path, 'config.yml'), 'w') as f:
            yaml.dump(saved_hyperparams, f)
        with open(os.path.join(self.params_path, 'args.yml'), 'w') as f:
            ordered_args = OrderedDict([(key, vars(self.args)[key]) for key in sorted(vars(self.args).keys())])
            yaml.dump(ordered_args, f)
        print(f'Log path: {self.save_path}')

    def read_hyperparameters(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        hyperparams_dir = os.path.abspath(os.path.join(os.path.realpath(__file__), *3 * [os.path.pardir], 'hyperparams'))
        with open(f'{hyperparams_dir}/{self.algo}.yml', 'r') as f:
            hyperparams_dict = yaml.safe_load(f)
            if self.env_id in list(hyperparams_dict.keys()):
                hyperparams = hyperparams_dict[self.env_id]
            elif self._is_atari:
                hyperparams = hyperparams_dict['atari']
            else:
                raise ValueError(f'Hyperparameters not found for {self.algo}-{self.env_id}')
        if self.custom_hyperparams is not None:
            hyperparams.update(self.custom_hyperparams)
        saved_hyperparams = OrderedDict([(key, hyperparams[key]) for key in sorted(hyperparams.keys())])
        if self.verbose > 0:
            print('Default hyperparameters for environment (ones being tuned will be overridden):')
            pprint(saved_hyperparams)
        return (hyperparams, saved_hyperparams)

    @staticmethod
    def _preprocess_schedules(hyperparams: Dict[str, Any]) -> Dict[str, Any]:
        for key in ['learning_rate', 'clip_range', 'clip_range_vf']:
            if key not in hyperparams:
                continue
            if isinstance(hyperparams[key], str):
                schedule, initial_value = hyperparams[key].split('_')
                initial_value = float(initial_value)
                hyperparams[key] = linear_schedule(initial_value)
            elif isinstance(hyperparams[key], (float, int)):
                if hyperparams[key] < 0:
                    continue
                hyperparams[key] = constant_fn(float(hyperparams[key]))
            else:
                raise ValueError(f'Invalid value for {key}: {hyperparams[key]}')
        return hyperparams

    def _preprocess_normalization(self, hyperparams: Dict[str, Any]) -> Dict[str, Any]:
        if 'normalize' in hyperparams.keys():
            self.normalize = hyperparams['normalize']
            if isinstance(self.normalize, str):
                self.normalize_kwargs = eval(self.normalize)
                self.normalize = True
            if 'gamma' in hyperparams:
                self.normalize_kwargs['gamma'] = hyperparams['gamma']
            del hyperparams['normalize']
        return hyperparams

    def _preprocess_hyperparams(self, hyperparams: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[Callable], List[BaseCallback]]:
        self.n_envs = hyperparams.get('n_envs', 1)
        if self.verbose > 0:
            print(f'Using {self.n_envs} environments')
        hyperparams = self._preprocess_schedules(hyperparams)
        if 'train_freq' in hyperparams and isinstance(hyperparams['train_freq'], list):
            hyperparams['train_freq'] = tuple(hyperparams['train_freq'])
        if self.n_timesteps > 0:
            if self.verbose:
                print(f'Overwriting n_timesteps with n={self.n_timesteps}')
        else:
            self.n_timesteps = int(hyperparams['n_timesteps'])
        hyperparams = self._preprocess_normalization(hyperparams)
        for kwargs_key in {'policy_kwargs', 'replay_buffer_class', 'replay_buffer_kwargs'}:
            if kwargs_key in hyperparams.keys() and isinstance(hyperparams[kwargs_key], str):
                hyperparams[kwargs_key] = eval(hyperparams[kwargs_key])
        if 'n_envs' in hyperparams.keys():
            del hyperparams['n_envs']
        del hyperparams['n_timesteps']
        if 'frame_stack' in hyperparams.keys():
            self.frame_stack = hyperparams['frame_stack']
            del hyperparams['frame_stack']
        env_wrapper = get_wrapper_class(hyperparams)
        if 'env_wrapper' in hyperparams.keys():
            del hyperparams['env_wrapper']
        callbacks = get_callback_list(hyperparams)
        if 'callback' in hyperparams.keys():
            self.specified_callbacks = hyperparams['callback']
            del hyperparams['callback']
        return (hyperparams, env_wrapper, callbacks)

    def _preprocess_action_noise(self, hyperparams: Dict[str, Any], env: VecEnv) -> Dict[str, Any]:
        if hyperparams.get('noise_type') is not None:
            noise_type = hyperparams['noise_type'].strip()
            noise_std = hyperparams['noise_std']
            self.n_actions = env.action_space.shape[0]
            if 'normal' in noise_type:
                hyperparams['action_noise'] = NormalActionNoise(mean=np.zeros(self.n_actions), sigma=noise_std * np.ones(self.n_actions))
            elif 'ornstein-uhlenbeck' in noise_type:
                hyperparams['action_noise'] = OrnsteinUhlenbeckActionNoise(mean=np.zeros(self.n_actions), sigma=noise_std * np.ones(self.n_actions))
            else:
                raise RuntimeError(f'Unknown noise type "{noise_type}"')
            print(f'Applying {noise_type} noise with std {noise_std}')
            del hyperparams['noise_type']
            del hyperparams['noise_std']
        return hyperparams

    def create_log_folder(self):
        os.makedirs(self.params_path, exist_ok=True)

    def create_callbacks(self):
        if self.save_freq > 0:
            self.save_freq = max(self.save_freq // self.n_envs, 1)
            self.callbacks.append(CheckpointCallbackWithReplayBuffer(save_freq=self.save_freq, save_path=self.save_path, name_prefix='rl_model', save_replay_buffer=self.save_replay_buffer, verbose=self.verbose))
        if self.eval_freq > 0 and (not self.optimize_hyperparameters):
            self.eval_freq = max(self.eval_freq // self.n_envs, 1)
            if self.verbose > 0:
                print('Creating test environment')
            save_vec_normalize = SaveVecNormalizeCallback(save_freq=1, save_path=self.params_path)
            eval_callback = EvalCallback(eval_env=self._env, callback_on_new_best=save_vec_normalize, best_model_save_path=self.save_path, n_eval_episodes=self.n_eval_episodes, log_path=self.save_path, eval_freq=self.eval_freq, deterministic=self.deterministic_eval)
            self.callbacks.append(eval_callback)

    @staticmethod
    def is_atari(env_id: str) -> bool:
        entry_point = gym.envs.registry.env_specs[env_id].entry_point
        return 'AtariEnv' in str(entry_point)

    @staticmethod
    def is_bullet(env_id: str) -> bool:
        entry_point = gym.envs.registry.env_specs[env_id].entry_point
        return 'pybullet_envs' in str(entry_point)

    @staticmethod
    def is_robotics_env(env_id: str) -> bool:
        entry_point = gym.envs.registry.env_specs[env_id].entry_point
        return 'gym.envs.robotics' in str(entry_point) or 'panda_gym.envs' in str(entry_point)

    @staticmethod
    def is_gazebo_env(env_id: str) -> bool:
        return 'Gazebo' in gym.envs.registry.env_specs[env_id].entry_point

    def _maybe_normalize(self, env: VecEnv, eval_env: bool) -> VecEnv:
        """
        Wrap the env into a VecNormalize wrapper if needed
        and load saved statistics when present.

        :param env:
        :param eval_env:
        :return:
        """
        path_ = os.path.join(os.path.dirname(self.trained_agent), self.env_id)
        path_ = os.path.join(path_, 'vecnormalize.pkl')
        if os.path.exists(path_):
            print('Loading saved VecNormalize stats')
            env = VecNormalize.load(path_, env)
            if eval_env:
                env.training = False
                env.norm_reward = False
        elif self.normalize:
            local_normalize_kwargs = self.normalize_kwargs.copy()
            if eval_env:
                if len(local_normalize_kwargs) > 0:
                    local_normalize_kwargs['norm_reward'] = False
                else:
                    local_normalize_kwargs = {'norm_reward': False}
            if self.verbose > 0:
                if len(local_normalize_kwargs) > 0:
                    print(f'Normalization activated: {local_normalize_kwargs}')
                else:
                    print('Normalizing input and reward')
            env.num_envs = self.n_envs
            env = VecNormalize(env, **local_normalize_kwargs)
        return env

    def create_envs(self, n_envs: int, eval_env: bool=False, no_log: bool=False) -> VecEnv:
        """
        Create the environment and wrap it if necessary.

        :param n_envs:
        :param eval_env: Whether is it an environment used for evaluation or not
        :param no_log: Do not log training when doing hyperparameter optim
            (issue with writing the same file)
        :return: the vectorized environment, with appropriate wrappers
        """
        log_dir = None if eval_env or no_log else self.save_path
        monitor_kwargs = {}
        if 'Neck' in self.env_id or self.is_robotics_env(self.env_id) or 'parking-v0' in self.env_id:
            monitor_kwargs = dict(info_keywords=('is_success',))
        env = make_vec_env(env_id=self.env_id, n_envs=n_envs, seed=self.seed, env_kwargs=self.env_kwargs, monitor_dir=log_dir, wrapper_class=self.env_wrapper, vec_env_cls=self.vec_env_class, vec_env_kwargs=self.vec_env_kwargs, monitor_kwargs=monitor_kwargs)
        env = self._maybe_normalize(env, eval_env)
        if self.frame_stack is not None:
            n_stack = self.frame_stack
            env = VecFrameStack(env, n_stack)
            if self.verbose > 0:
                print(f'Stacking {n_stack} frames')
        if not is_vecenv_wrapped(env, VecTransposeImage):
            wrap_with_vectranspose = False
            if isinstance(env.observation_space, gym.spaces.Dict):
                for space in env.observation_space.spaces.values():
                    wrap_with_vectranspose = wrap_with_vectranspose or (is_image_space(space) and (not is_image_space_channels_first(space)))
            else:
                wrap_with_vectranspose = is_image_space(env.observation_space) and (not is_image_space_channels_first(env.observation_space))
            if wrap_with_vectranspose:
                if self.verbose >= 1:
                    print('Wrapping the env in a VecTransposeImage.')
                env = VecTransposeImage(env)
        return env

    def _load_pretrained_agent(self, hyperparams: Dict[str, Any], env: VecEnv) -> BaseAlgorithm:
        print(f"Loading pretrained agent '{self.trained_agent}' to continue its training")
        del hyperparams['policy']
        if 'policy_kwargs' in hyperparams.keys():
            del hyperparams['policy_kwargs']
        model = ALGOS[self.algo].load(self.trained_agent, env=env, seed=self.seed, tensorboard_log=self.tensorboard_log, verbose=self.verbose, **hyperparams)
        replay_buffer_path = os.path.join(os.path.dirname(self.trained_agent), 'replay_buffer.pkl')
        if not self.preload_replay_buffer and os.path.exists(replay_buffer_path):
            print('Loading replay buffer')
            model.load_replay_buffer(replay_buffer_path, truncate_last_traj=self.truncate_last_trajectory)
        return model

    def _create_sampler(self, sampler_method: str) -> BaseSampler:
        if sampler_method == 'random':
            sampler = RandomSampler(seed=self.seed)
        elif sampler_method == 'tpe':
            sampler = TPESampler(n_startup_trials=self.n_startup_trials, seed=self.seed)
        elif sampler_method == 'skopt':
            sampler = SkoptSampler(skopt_kwargs={'base_estimator': 'GP', 'acq_func': 'gp_hedge'})
        else:
            raise ValueError(f'Unknown sampler: {sampler_method}')
        return sampler

    def _create_pruner(self, pruner_method: str) -> BasePruner:
        if pruner_method == 'halving':
            pruner = SuccessiveHalvingPruner(min_resource=1, reduction_factor=4, min_early_stopping_rate=0)
        elif pruner_method == 'median':
            pruner = MedianPruner(n_startup_trials=self.n_startup_trials, n_warmup_steps=self.n_evaluations // 3)
        elif pruner_method == 'none':
            pruner = NopPruner()
        else:
            raise ValueError(f'Unknown pruner: {pruner_method}')
        return pruner

    def objective(self, trial: optuna.Trial) -> float:
        kwargs = self._hyperparams.copy()
        trial.model_class = None
        trial.n_actions = self._env.action_space.shape[0]
        if kwargs.get('replay_buffer_class') == HerReplayBuffer:
            trial.her_kwargs = kwargs.get('replay_buffer_kwargs', {})
        kwargs.update(HYPERPARAMS_SAMPLER[self.algo](trial))
        print(f'\nRunning a new trial with hyperparameters: {kwargs}')
        trial_params_path = os.path.join(self.params_path, 'optimization')
        os.makedirs(trial_params_path, exist_ok=True)
        with open(os.path.join(trial_params_path, f'hyperparameters_trial_{trial.number}.yml'), 'w') as f:
            yaml.dump(kwargs, f)
        model = ALGOS[self.algo](env=self._env, tensorboard_log=self.tensorboard_log, seed=self.seed, verbose=self.verbose, **kwargs)
        if self.preload_replay_buffer:
            if self.preload_replay_buffer.endswith('.pkl'):
                replay_buffer_path = self.preload_replay_buffer
            else:
                replay_buffer_path = os.path.join(self.preload_replay_buffer, 'replay_buffer.pkl')
            if os.path.exists(replay_buffer_path):
                print('Pre-loading replay buffer')
                if self.algo == 'her':
                    model.load_replay_buffer(replay_buffer_path, self.truncate_last_trajectory)
                else:
                    model.load_replay_buffer(replay_buffer_path)
            else:
                raise Exception(f'Replay buffer {replay_buffer_path} does not exist')
        model.trial = trial
        eval_freq = int(self.n_timesteps / self.n_evaluations)
        eval_freq_ = max(eval_freq // model.get_env().num_envs, 1)
        callbacks = get_callback_list({'callback': self.specified_callbacks})
        path = None
        if self.optimization_log_path is not None:
            path = os.path.join(self.optimization_log_path, f'trial_{str(trial.number)}')
        eval_callback = TrialEvalCallback(model.env, model.trial, best_model_save_path=path, log_path=path, n_eval_episodes=self.n_eval_episodes, eval_freq=eval_freq_, deterministic=self.deterministic_eval, verbose=self.verbose)
        callbacks.append(eval_callback)
        try:
            model.learn(self.n_timesteps, callback=callbacks)
            self._env.reset()
        except AssertionError as e:
            self._env.reset()
            print('Trial stopped:', e)
            raise optuna.exceptions.TrialPruned()
        except Exception as err:
            exception_type = type(err).__name__
            print('Trial stopped due to raised exception:', exception_type, err)
            raise optuna.exceptions.TrialPruned()
        is_pruned = eval_callback.is_pruned
        reward = eval_callback.last_mean_reward
        print(f'\nFinished a trial with reward={reward}, is_pruned={is_pruned} for hyperparameters: {kwargs}')
        del model
        if is_pruned:
            raise optuna.exceptions.TrialPruned()
        return reward

    def hyperparameters_optimization(self) -> None:
        if self.verbose > 0:
            print('Optimizing hyperparameters')
        if self.storage is not None and self.study_name is None:
            warnings.warn(f'You passed a remote storage: {self.storage} but no `--study-name`.The study name will be generated by Optuna, make sure to re-use the same study name when you want to do distributed hyperparameter optimization.')
        if self.tensorboard_log is not None:
            warnings.warn('Tensorboard log is deactivated when running hyperparameter optimization')
            self.tensorboard_log = None
        sampler = self._create_sampler(self.sampler)
        pruner = self._create_pruner(self.pruner)
        if self.verbose > 0:
            print(f'Sampler: {self.sampler} - Pruner: {self.pruner}')
        study = optuna.create_study(sampler=sampler, pruner=pruner, storage=self.storage, study_name=self.study_name, load_if_exists=True, direction='maximize')
        try:
            study.optimize(self.objective, n_trials=self.n_trials, n_jobs=self.n_jobs, gc_after_trial=True, show_progress_bar=True)
        except KeyboardInterrupt:
            pass
        print('Number of finished trials: ', len(study.trials))
        print('Best trial:')
        trial = study.best_trial
        print('Value: ', trial.value)
        print('Params: ')
        for key, value in trial.params.items():
            print(f'    {key}: {value}')
        report_name = f'report_{self.env_id}_{self.n_trials}-trials-{self.n_timesteps}-{self.sampler}-{self.pruner}_{int(time.time())}'
        log_path = os.path.join(self.log_folder, self.algo, report_name)
        if self.verbose:
            print(f'Writing report to {log_path}')
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        study.trials_dataframe().to_csv(f'{log_path}.csv')
        with open(f'{log_path}.pkl', 'wb+') as f:
            pkl.dump(study, f)
        if self.no_optim_plots:
            return
        try:
            fig1 = plot_optimization_history(study)
            fig2 = plot_param_importances(study)
            fig1.show()
            fig2.show()
        except (ValueError, ImportError, RuntimeError):
            pass

    def collect_demonstration(self, model):
        action = np.array([model.env.action_space.sample()])
        obs = model.env.reset()
        for i in range(model.replay_buffer.buffer_size):
            next_obs, rewards, dones, infos = model.env.unwrapped.step(action)
            actual_actions = [info['actual_actions'] for info in infos]
            model.replay_buffer.add(obs, next_obs, actual_actions, rewards, dones)
            obs = next_obs
        print('Saving replay buffer')
        model.save_replay_buffer(os.path.join(self.save_path, 'replay_buffer.pkl'))
        model.env.close()
        exit

def _preprocess_action_noise(self, hyperparams: Dict[str, Any], env: VecEnv) -> Dict[str, Any]:
    if hyperparams.get('noise_type') is not None:
        noise_type = hyperparams['noise_type'].strip()
        noise_std = hyperparams['noise_std']
        self.n_actions = env.action_space.shape[0]
        if 'normal' in noise_type:
            hyperparams['action_noise'] = NormalActionNoise(mean=np.zeros(self.n_actions), sigma=noise_std * np.ones(self.n_actions))
        elif 'ornstein-uhlenbeck' in noise_type:
            hyperparams['action_noise'] = OrnsteinUhlenbeckActionNoise(mean=np.zeros(self.n_actions), sigma=noise_std * np.ones(self.n_actions))
        else:
            raise RuntimeError(f'Unknown noise type "{noise_type}"')
        print(f'Applying {noise_type} noise with std {noise_std}')
        del hyperparams['noise_type']
        del hyperparams['noise_std']
    return hyperparams

def transform_to_matrix(transform: geometry_msgs.msg.Transform) -> numpy.ndarray:
    transform_matrix = numpy.zeros((4, 4))
    transform_matrix[3, 3] = 1.0
    transform_matrix[0:3, 0:3] = open3d.geometry.get_rotation_matrix_from_quaternion([transform.rotation.w, transform.rotation.x, transform.rotation.y, transform.rotation.z])
    transform_matrix[0, 3] = transform.translation.x
    transform_matrix[1, 3] = transform.translation.y
    transform_matrix[2, 3] = transform.translation.z
    return transform_matrix

class OctreeCreator:

    def __init__(self, node: Node, tf2_listener: Tf2Listener, reference_frame_id: str, min_bound: Tuple[float, float, float]=(-1.0, -1.0, -1.0), max_bound: Tuple[float, float, float]=(1.0, 1.0, 1.0), include_color: bool=False, include_intensity: bool=False, depth: int=4, full_depth: int=2, adaptive: bool=False, adp_depth: int=4, normals_radius: float=0.05, normals_max_nn: int=10, node_dis: bool=True, node_feature: bool=False, split_label: bool=False, th_normal: float=0.1, th_distance: float=2.0, extrapolate: bool=False, save_pts: bool=False, key2xyz: bool=False, debug_draw: bool=False, debug_write_octree: bool=False):
        self._node = node
        self.__tf2_listener = tf2_listener
        self._reference_frame_id = reference_frame_id
        self._min_bound = min_bound
        self._max_bound = max_bound
        self._include_color = include_color
        self._include_intensity = include_intensity
        self._normals_radius = normals_radius
        self._normals_max_nn = normals_max_nn
        self._debug_draw = debug_draw
        self._debug_write_octree = debug_write_octree
        self._points_to_octree = ocnn.Points2Octree(depth=depth, full_depth=full_depth, node_dis=node_dis, node_feature=node_feature, split_label=split_label, adaptive=adaptive, adp_depth=adp_depth, th_normal=th_normal, th_distance=th_distance, extrapolate=extrapolate, save_pts=save_pts, key2xyz=key2xyz, bb_min=min_bound, bb_max=max_bound)

    def __call__(self, ros_point_cloud2: PointCloud2) -> torch.Tensor:
        open3d_point_cloud = conversions.pointcloud2_to_open3d(ros_point_cloud2=ros_point_cloud2, include_color=self._include_color, include_intensity=self._include_intensity)
        open3d_point_cloud = self.preprocess_point_cloud(open3d_point_cloud=open3d_point_cloud, camera_frame_id=ros_point_cloud2.header.frame_id, reference_frame_id=self._reference_frame_id, min_bound=self._min_bound, max_bound=self._max_bound, normals_radius=self._normals_radius, normals_max_nn=self._normals_max_nn)
        if self._debug_draw:
            open3d.visualization.draw_geometries([open3d_point_cloud, open3d.geometry.TriangleMesh.create_coordinate_frame(size=0.2, origin=[0.0, 0.0, 0.0])], point_show_normal=True)
        octree = self.construct_octree(open3d_point_cloud, include_color=self._include_color, include_intensity=self._include_intensity)
        if self._debug_write_octree:
            ocnn.write_octree(octree, 'octree.octree')
        return octree

    def preprocess_point_cloud(self, open3d_point_cloud: open3d.geometry.PointCloud, camera_frame_id: str, reference_frame_id: str, min_bound: List[float], max_bound: List[float], normals_radius: float, normals_max_nn: int) -> open3d.geometry.PointCloud:
        if not open3d_point_cloud.has_points():
            self._node.get_logger().warn('Point cloud has no points. Pre-processing skipped.')
            return open3d_point_cloud
        if camera_frame_id != reference_frame_id:
            transform = self.__tf2_listener.lookup_transform_sync(target_frame=reference_frame_id, source_frame=camera_frame_id)
            transform_mat = conversions.transform_to_matrix(transform=transform)
            open3d_point_cloud = open3d_point_cloud.transform(transform_mat)
        open3d_point_cloud = open3d_point_cloud.crop(bounding_box=open3d.geometry.AxisAlignedBoundingBox(min_bound=min_bound, max_bound=max_bound))
        if not open3d_point_cloud.has_points():
            self._node.get_logger().warn('Point cloud has no points after cropping it to the workspace volume.')
            return open3d_point_cloud
        open3d_point_cloud.estimate_normals(search_param=open3d.geometry.KDTreeSearchParamHybrid(radius=normals_radius, max_nn=normals_max_nn), fast_normal_computation=True)
        open3d_point_cloud.orient_normals_towards_camera_location(camera_location=transform_mat[0:3, 3])
        return open3d_point_cloud

    def construct_octree(self, open3d_point_cloud: open3d.geometry.PointCloud, include_color: bool, include_intensity: bool) -> torch.Tensor:
        if not open3d_point_cloud.has_points():
            open3d_point_cloud.points.append(((self._min_bound[0] + self._max_bound[0]) / 2, (self._min_bound[1] + self._max_bound[1]) / 2, (self._min_bound[2] + self._max_bound[2]) / 2))
            open3d_point_cloud.normals.append((0.0, 0.0, 0.0))
            if include_color or include_intensity:
                open3d_point_cloud.colors.append((0.0, 0.0, 0.0))
        octree_points = conversions.open3d_point_cloud_to_octree_points(open3d_point_cloud=open3d_point_cloud, include_color=include_color, include_intensity=include_intensity)
        octree_points_ndarray = np.frombuffer(np.copy(octree_points.buffer()), np.uint8)
        octree_points_tensor = torch.from_numpy(octree_points_ndarray)
        return self._points_to_octree(octree_points_tensor)

def preprocess_point_cloud(self, open3d_point_cloud: open3d.geometry.PointCloud, camera_frame_id: str, reference_frame_id: str, min_bound: List[float], max_bound: List[float], normals_radius: float, normals_max_nn: int) -> open3d.geometry.PointCloud:
    if not open3d_point_cloud.has_points():
        self._node.get_logger().warn('Point cloud has no points. Pre-processing skipped.')
        return open3d_point_cloud
    if camera_frame_id != reference_frame_id:
        transform = self.__tf2_listener.lookup_transform_sync(target_frame=reference_frame_id, source_frame=camera_frame_id)
        transform_mat = conversions.transform_to_matrix(transform=transform)
        open3d_point_cloud = open3d_point_cloud.transform(transform_mat)
    open3d_point_cloud = open3d_point_cloud.crop(bounding_box=open3d.geometry.AxisAlignedBoundingBox(min_bound=min_bound, max_bound=max_bound))
    if not open3d_point_cloud.has_points():
        self._node.get_logger().warn('Point cloud has no points after cropping it to the workspace volume.')
        return open3d_point_cloud
    open3d_point_cloud.estimate_normals(search_param=open3d.geometry.KDTreeSearchParamHybrid(radius=normals_radius, max_nn=normals_max_nn), fast_normal_computation=True)
    open3d_point_cloud.orient_normals_towards_camera_location(camera_location=transform_mat[0:3, 3])
    return open3d_point_cloud

def construct_octree(self, open3d_point_cloud: open3d.geometry.PointCloud, include_color: bool, include_intensity: bool) -> torch.Tensor:
    if not open3d_point_cloud.has_points():
        open3d_point_cloud.points.append(((self._min_bound[0] + self._max_bound[0]) / 2, (self._min_bound[1] + self._max_bound[1]) / 2, (self._min_bound[2] + self._max_bound[2]) / 2))
        open3d_point_cloud.normals.append((0.0, 0.0, 0.0))
        if include_color or include_intensity:
            open3d_point_cloud.colors.append((0.0, 0.0, 0.0))
    octree_points = conversions.open3d_point_cloud_to_octree_points(open3d_point_cloud=open3d_point_cloud, include_color=include_color, include_intensity=include_intensity)
    octree_points_ndarray = np.frombuffer(np.copy(octree_points.buffer()), np.uint8)
    octree_points_tensor = torch.from_numpy(octree_points_ndarray)
    return self._points_to_octree(octree_points_tensor)

class ModelCollectionRandomizer:
    _class_model_paths = None
    __sdf_base_name = 'model.sdf'
    __configured_sdf_base_name = 'model_modified.sdf'
    __blacklisted_base_name = 'BLACKLISTED'
    __collision_mesh_dir = 'meshes/collision/'
    __collision_mesh_file_type = 'stl'
    __original_scale_base_name = 'original_scale.txt'

    def __init__(self, model_paths=None, owner='GoogleResearch', collection='Google Scanned Objects', server='https://fuel.ignitionrobotics.org', server_version='1.0', unique_cache=False, reset_collection=False, enable_blacklisting=True, np_random: Optional[RandomState]=None):
        self._unique_cache = unique_cache
        self._enable_blacklisting = enable_blacklisting
        if reset_collection and (not self._unique_cache):
            self._class_model_paths = None
        if model_paths is not None:
            if self._unique_cache:
                self._model_paths = model_paths
            else:
                self._class_model_paths = model_paths
        elif self._unique_cache:
            self._model_paths = self.get_collection_paths(owner=owner, collection=collection, server=server, server_version=server_version)
        elif self._class_model_paths is None:
            self._class_model_paths = self.get_collection_paths(owner=owner, collection=collection, server=server, server_version=server_version)
        if np_random is not None:
            self.np_random = np_random
        else:
            self.np_random = np.random.default_rng()

    @classmethod
    def get_collection_paths(cls, owner='GoogleResearch', collection='Google Scanned Objects', server='https://fuel.ignitionrobotics.org', server_version='1.0', model_name: str='') -> List[str]:
        model_paths = scenario_gazebo.get_local_cache_model_paths(owner=owner, name=model_name)
        if len(model_paths) > 0:
            return model_paths
        if collection:
            download_uri = '%s/%s/%s/collections/%s' % (server, server_version, owner, collection)
        elif model_name:
            download_uri = '%s/%s/%s/models/%s' % (server, server_version, owner, model_name)
        download_command = 'ign fuel download -v 3 -t model -j %s -u "%s"' % (os.cpu_count(), download_uri)
        os.system(download_command)
        model_paths = scenario_gazebo.get_local_cache_model_paths(owner=owner, name=model_name)
        if 0 == len(model_paths):
            logger.error('URI "%s" is not valid and does not contain any models that are                           owned by the owner of the collection' % download_uri)
            pass
        return model_paths

    def random_model(self, min_scale=0.125, max_scale=0.175, min_mass=0.05, max_mass=0.25, min_friction=0.75, max_friction=1.5, decimation_fraction_of_visual=0.25, decimation_min_faces=40, decimation_max_faces=200, max_faces=40000, max_vertices=None, component_min_faces_fraction=0.1, component_max_volume_fraction=0.35, fix_mtl_texture_paths=True, skip_blacklisted=True, return_sdf_path=True) -> str:
        while True:
            model_path = self.get_random_model_path()
            if skip_blacklisted and self.is_blacklisted(model_path):
                continue
            if self.is_configured(model_path):
                break
            if self.process_model(model_path, decimation_fraction_of_visual=decimation_fraction_of_visual, decimation_min_faces=decimation_min_faces, decimation_max_faces=decimation_max_faces, max_faces=max_faces, max_vertices=max_vertices, component_min_faces_fraction=component_min_faces_fraction, component_max_volume_fraction=component_max_volume_fraction, fix_mtl_texture_paths=fix_mtl_texture_paths):
                break
        self.randomize_configured_model(model_path, min_scale=min_scale, max_scale=max_scale, min_friction=min_friction, max_friction=max_friction, min_mass=min_mass, max_mass=max_mass)
        if return_sdf_path:
            return self.get_configured_sdf_path(model_path)
        else:
            return model_path

    def process_all_models(self, decimation_fraction_of_visual=0.025, decimation_min_faces=8, decimation_max_faces=400, max_faces=40000, max_vertices=None, component_min_faces_fraction=0.1, component_max_volume_fraction=0.35, fix_mtl_texture_paths=True):
        if self._unique_cache:
            model_paths = self._model_paths
        else:
            model_paths = self._class_model_paths
        blacklist_model_counter = 0
        for i in range(len(model_paths)):
            if not self.process_model(model_paths[i], decimation_fraction_of_visual=decimation_fraction_of_visual, decimation_min_faces=decimation_min_faces, decimation_max_faces=decimation_max_faces, max_faces=max_faces, max_vertices=max_vertices, component_min_faces_fraction=component_min_faces_fraction, component_max_volume_fraction=component_max_volume_fraction, fix_mtl_texture_paths=fix_mtl_texture_paths):
                blacklist_model_counter += 1
            print('Processed model %i/%i "%s"' % (i, len(model_paths), model_paths[i]))
        print('Number of blacklisted models: %i' % blacklist_model_counter)

    def process_model(self, model_path, decimation_fraction_of_visual=0.25, decimation_min_faces=40, decimation_max_faces=200, max_faces=40000, max_vertices=None, component_min_faces_fraction=0.1, component_max_volume_fraction=0.35, fix_mtl_texture_paths=True) -> bool:
        sdf = parse_sdf(self.get_sdf_path(model_path))
        for model in sdf.models:
            for link in model.links:
                link.collisions.clear()
                total_mass = 0.0
                total_inertia = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
                common_centre_of_mass = [0.0, 0.0, 0.0]
                for visual in link.visuals:
                    mesh_path = self.get_mesh_path(model_path, visual)
                    if fix_mtl_texture_paths:
                        self.fix_mtl_texture_paths(model_path, mesh_path, model.attributes['name'])
                    mesh = trimesh.load(mesh_path, force='mesh', skip_materials=True)
                    if not self.check_excessive_geometry(mesh, model_path, max_faces=max_faces, max_vertices=max_vertices):
                        return False
                    if not self.check_disconnected_components(mesh, model_path, component_min_faces_fraction=component_min_faces_fraction, component_max_volume_fraction=component_max_volume_fraction):
                        return False
                    total_mass, total_inertia, common_centre_of_mass = self.sum_inertial_properties(mesh, total_mass, total_inertia, common_centre_of_mass)
                    self.add_collision(mesh, link, model_path, fraction_of_visual=decimation_fraction_of_visual, min_faces=decimation_min_faces, max_faces=decimation_max_faces)
                    self.write_original_scale(mesh, model_path)
                if not self.check_inertial_properties(model_path, total_mass, total_inertia):
                    return False
                self.write_inertial_properties(link, total_mass, total_inertia, common_centre_of_mass)
        sdf.export_xml(self.get_configured_sdf_path(model_path))
        return True

    def add_collision(self, mesh, link, model_path, fraction_of_visual=0.05, min_faces=8, max_faces=750, friction=1.0):
        collision_name = link.attributes['name'] + '_collision_' + str(len(link.collisions))
        collision_mesh_path = self.get_collision_mesh_path(model_path, collision_name)
        face_count = min(max(fraction_of_visual * len(mesh.faces), min_faces), max_faces)
        collision_mesh = mesh.simplify_quadratic_decimation(face_count)
        os.makedirs(os.path.dirname(collision_mesh_path), exist_ok=True)
        collision_mesh.export(collision_mesh_path, file_type=self.__collision_mesh_file_type)
        collision = create_sdf_element('collision')
        collision.geometry.mesh = create_sdf_element('mesh')
        collision.geometry.mesh.uri = os.path.relpath(collision_mesh_path, start=model_path)
        collision.surface = create_sdf_element('surface')
        collision.surface.friction = create_sdf_element('friction', 'surface')
        collision.surface.friction.ode = create_sdf_element('ode', 'collision')
        collision.surface.friction.ode.mu = friction
        collision.surface.friction.ode.mu2 = friction
        collision_name = os.path.basename(collision_mesh_path).split('.')[0]
        link.add_collision(collision_name, collision)

    def sum_inertial_properties(self, mesh, total_mass, total_inertia, common_centre_of_mass, density=1.0) -> Tuple[float, float, float]:
        mesh.density = density
        mass_of_others = total_mass
        total_mass += mesh.mass
        total_inertia += mesh.moment_inertia
        common_centre_of_mass = [mass_of_others * common_centre_of_mass[0] + mesh.mass * mesh.center_mass[0], mass_of_others * common_centre_of_mass[1] + mesh.mass * mesh.center_mass[1], mass_of_others * common_centre_of_mass[2] + mesh.mass * mesh.center_mass[2]] / total_mass
        return (total_mass, total_inertia, common_centre_of_mass)

    def randomize_configured_model(self, model_path, min_scale=0.05, max_scale=0.25, min_mass=0.1, max_mass=3.0, min_friction=0.75, max_friction=1.5):
        configured_sdf_path = self.get_configured_sdf_path(model_path)
        sdf = parse_sdf(configured_sdf_path)
        for model in sdf.models:
            for link in model.links:
                self.randomize_scale(model_path, link, min_scale=min_scale, max_scale=max_scale)
                self.randomize_inertial(link, min_mass=min_mass, max_mass=max_mass)
                self.randomize_friction(link, min_friction=min_friction, max_friction=max_friction)
        sdf.export_xml(configured_sdf_path)

    def randomize_scale(self, model_path, link, min_scale=0.05, max_scale=0.25):
        if len(link.visuals) > 1:
            return False
        random_scale = self.np_random.uniform(min_scale, max_scale)
        original_mesh_scale = self.read_original_scale(model_path)
        scale_factor = random_scale / original_mesh_scale
        current_scale = link.visuals[0].geometry.mesh.scale.value[0]
        inertial_scale_factor = scale_factor / current_scale
        link.visuals[0].geometry.mesh.scale = [scale_factor] * 3
        link.collisions[0].geometry.mesh.scale = [scale_factor] * 3
        link.inertial.pose.x *= inertial_scale_factor
        link.inertial.pose.y *= inertial_scale_factor
        link.inertial.pose.z *= inertial_scale_factor
        link.mass = link.mass.value * inertial_scale_factor ** 3
        inertial_scale_factor_n5 = inertial_scale_factor ** 5
        link.inertia.ixx = link.inertia.ixx.value * inertial_scale_factor_n5
        link.inertia.iyy = link.inertia.iyy.value * inertial_scale_factor_n5
        link.inertia.izz = link.inertia.izz.value * inertial_scale_factor_n5
        link.inertia.ixy = link.inertia.ixy.value * inertial_scale_factor_n5
        link.inertia.ixz = link.inertia.ixz.value * inertial_scale_factor_n5
        link.inertia.iyz = link.inertia.iyz.value * inertial_scale_factor_n5

    def randomize_inertial(self, link, min_mass=0.1, max_mass=3.0) -> Tuple[float, float]:
        random_mass = self.np_random.uniform(min_mass, max_mass)
        mass_scale_factor = random_mass / link.mass.value
        link.mass = random_mass
        link.inertia.ixx = link.inertia.ixx.value * mass_scale_factor
        link.inertia.iyy = link.inertia.iyy.value * mass_scale_factor
        link.inertia.izz = link.inertia.izz.value * mass_scale_factor
        link.inertia.ixy = link.inertia.ixy.value * mass_scale_factor
        link.inertia.ixz = link.inertia.ixz.value * mass_scale_factor
        link.inertia.iyz = link.inertia.iyz.value * mass_scale_factor

    def randomize_friction(self, link, min_friction=0.75, max_friction=1.5):
        for collision in link.collisions:
            random_friction = self.np_random.uniform(min_friction, max_friction)
            collision.surface.friction.ode.mu = random_friction
            collision.surface.friction.ode.mu2 = random_friction

    def write_inertial_properties(self, link, mass, inertia, centre_of_mass):
        link.mass = mass
        link.inertia.ixx = inertia[0][0]
        link.inertia.iyy = inertia[1][1]
        link.inertia.izz = inertia[2][2]
        link.inertia.ixy = inertia[0][1]
        link.inertia.ixz = inertia[0][2]
        link.inertia.iyz = inertia[1][2]
        link.inertial.pose = [centre_of_mass[0], centre_of_mass[1], centre_of_mass[2], 0.0, 0.0, 0.0]

    def write_original_scale(self, mesh, model_path):
        file = open(self.get_original_scale_path(model_path), 'w')
        file.write(str(mesh.scale))
        file.close()

    def read_original_scale(self, model_path) -> float:
        file = open(self.get_original_scale_path(model_path), 'r')
        original_scale = file.read()
        file.close()
        return float(original_scale)

    def check_excessive_geometry(self, mesh, model_path, max_faces=40000, max_vertices=None) -> bool:
        if max_faces is not None:
            num_faces = len(mesh.faces)
            if num_faces > max_faces:
                self.blacklist_model(model_path, reason='Excessive geometry (%d faces)' % num_faces)
                return False
        if max_vertices is not None:
            num_vertices = len(mesh.vertices)
            if num_vertices > max_vertices:
                self.blacklist_model(model_path, reason='Excessive geometry (%d vertices)' % num_vertices)
                return False
        return True

    def check_disconnected_components(self, mesh, model_path, component_min_faces_fraction=0.05, component_max_volume_fraction=0.1) -> bool:
        min_faces = round(component_min_faces_fraction * len(mesh.faces))
        connected_components = trimesh.graph.connected_components(mesh.face_adjacency, min_len=min_faces)
        if len(connected_components) > 1:
            total_volume = mesh.volume
            large_component_counter = 0
            for component in connected_components:
                submesh = mesh.copy()
                mask = np.zeros(len(mesh.faces), dtype=np.bool)
                mask[component] = True
                submesh.update_faces(mask)
                volume_fraction = submesh.volume / total_volume
                if volume_fraction > component_max_volume_fraction:
                    large_component_counter += 1
                if large_component_counter > 1:
                    self.blacklist_model(model_path, reason='Disconnected components (%d instances)' % len(connected_components))
                    return False
        return True

    def check_inertial_properties(self, model_path, mass, inertia) -> bool:
        if mass < 1e-10 or inertia[0][0] < 1e-10 or inertia[1][1] < 1e-10 or (inertia[2][2] < 1e-10):
            self.blacklist_model(model_path, reason='Invalid inertial properties')
            return False
        return True

    def get_random_model_path(self) -> str:
        if self._unique_cache:
            return self.np_random.choice(self._model_paths)
        else:
            return self.np_random.choice(self._class_model_paths)

    def get_collision_mesh_path(self, model_path, collision_name) -> str:
        return os.path.join(model_path, self.__collision_mesh_dir, collision_name + '.' + self.__collision_mesh_file_type)

    def get_sdf_path(self, model_path) -> str:
        return os.path.join(model_path, self.__sdf_base_name)

    def get_configured_sdf_path(self, model_path) -> str:
        return os.path.join(model_path, self.__configured_sdf_base_name)

    def get_blacklisted_path(self, model_path) -> str:
        return os.path.join(model_path, self.__blacklisted_base_name)

    def get_mesh_path(self, model_path, visual_or_collision) -> str:
        mesh_uri = visual_or_collision.geometry.mesh.uri.value
        return os.path.join(model_path, mesh_uri)

    def get_original_scale_path(self, model_path) -> str:
        return os.path.join(model_path, self.__original_scale_base_name)

    def blacklist_model(self, model_path, reason='Unknown'):
        if self._enable_blacklisting:
            bl_file = open(self.get_blacklisted_path(model_path), 'w')
            bl_file.write(reason)
            bl_file.close()
        logger.warn('%s model "%s". Reason: %s.' % ('Blacklisting' if self._enable_blacklisting else 'Skipping', model_path, reason))

    def is_blacklisted(self, model_path) -> bool:
        return os.path.isfile(self.get_blacklisted_path(model_path))

    def is_configured(self, model_path) -> bool:
        return os.path.isfile(self.get_configured_sdf_path(model_path))

    def fix_mtl_texture_paths(self, model_path, mesh_path, model_name):
        if mesh_path.endswith('.obj'):
            texture_files = glob.glob(os.path.join(model_path, '**', 'textures', '*.*'))
            mtllib_file = None
            with open(mesh_path, 'r') as file:
                for line in file:
                    if 'mtllib' in line:
                        mtllib_file = line.split(' ')[-1].strip()
                        break
            if mtllib_file is not None:
                mtllib_file = os.path.join(os.path.dirname(mesh_path), mtllib_file)
                fin = open(mtllib_file, 'r')
                data = fin.read()
                for line in data.splitlines():
                    if 'map_' in line:
                        map_file = line.split(' ')[-1].strip()
                        for texture_file in texture_files:
                            if os.path.basename(texture_file) == map_file or os.path.basename(texture_file) == os.path.basename(map_file):
                                if model_name in texture_file:
                                    new_texture_file_name = texture_file
                                else:
                                    new_texture_file_name = texture_file.replace(map_file, model_name + '_' + map_file)
                                os.rename(texture_file, new_texture_file_name)
                                data = data.replace(map_file, os.path.relpath(new_texture_file_name, start=os.path.dirname(mesh_path)))
                                break
                fin.close()
                fout = open(mtllib_file, 'w')
                fout.write(data)
                fout.close()

def check_excessive_geometry(self, mesh, model_path, max_faces=40000, max_vertices=None) -> bool:
    if max_faces is not None:
        num_faces = len(mesh.faces)
        if num_faces > max_faces:
            self.blacklist_model(model_path, reason='Excessive geometry (%d faces)' % num_faces)
            return False
    if max_vertices is not None:
        num_vertices = len(mesh.vertices)
        if num_vertices > max_vertices:
            self.blacklist_model(model_path, reason='Excessive geometry (%d vertices)' % num_vertices)
            return False
    return True

def check_disconnected_components(self, mesh, model_path, component_min_faces_fraction=0.05, component_max_volume_fraction=0.1) -> bool:
    min_faces = round(component_min_faces_fraction * len(mesh.faces))
    connected_components = trimesh.graph.connected_components(mesh.face_adjacency, min_len=min_faces)
    if len(connected_components) > 1:
        total_volume = mesh.volume
        large_component_counter = 0
        for component in connected_components:
            submesh = mesh.copy()
            mask = np.zeros(len(mesh.faces), dtype=np.bool)
            mask[component] = True
            submesh.update_faces(mask)
            volume_fraction = submesh.volume / total_volume
            if volume_fraction > component_max_volume_fraction:
                large_component_counter += 1
            if large_component_counter > 1:
                self.blacklist_model(model_path, reason='Disconnected components (%d instances)' % len(connected_components))
                return False
    return True

def check_inertial_properties(self, model_path, mass, inertia) -> bool:
    if mass < 1e-10 or inertia[0][0] < 1e-10 or inertia[1][1] < 1e-10 or (inertia[2][2] < 1e-10):
        self.blacklist_model(model_path, reason='Invalid inertial properties')
        return False
    return True

