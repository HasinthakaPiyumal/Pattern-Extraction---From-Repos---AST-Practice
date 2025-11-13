# Cluster 11

def get_module_name(callback_name):
    return '.'.join(callback_name.split('.')[:-1])

def get_class_name(callback_name):
    return callback_name.split('.')[-1]

def linear_schedule(initial_value: Union[float, str]) -> Callable[[float], float]:
    """
    Linear learning rate schedule.

    :param initial_value: (float or str)
    :return: (function)
    """
    if isinstance(initial_value, str):
        initial_value = float(initial_value)

    def func(progress_remaining: float) -> float:
        """
        Progress will decrease from 1 (beginning) to 0
        :param progress_remaining: (float)
        :return: (float)
        """
        return progress_remaining * initial_value
    return func

def get_latest_run_id(log_path: str, env_id: str) -> int:
    """
    Returns the latest run number for the given log name and log path,
    by finding the greatest number in the directories.

    :param log_path: path to log folder
    :param env_id:
    :return: latest run number
    """
    max_run_id = 0
    for path in glob.glob(os.path.join(log_path, env_id + '_[0-9]*')):
        file_name = os.path.basename(path)
        ext = file_name.split('_')[-1]
        if env_id == '_'.join(file_name.split('_')[:-1]) and ext.isdigit() and (int(ext) > max_run_id):
            max_run_id = int(ext)
    return max_run_id

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

def _init_callback(self) -> None:
    if self.save_path is not None:
        os.makedirs(self.save_path, exist_ok=True)

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

def create_log_folder(self):
    os.makedirs(self.params_path, exist_ok=True)

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

class Tf2Broadcaster:

    def __init__(self, node: Node):
        self._node = node
        self.__tf2_broadcaster = StaticTransformBroadcaster(node=self._node)
        self._transform_stamped = TransformStamped()

    def broadcast_tf(self, parent_frame_id: str, child_frame_id: str, translation: Tuple[float, float, float], rotation: Tuple[float, float, float, float], xyzw: bool=True):
        """
        Broadcast transformation of the camera
        """
        self._transform_stamped.header.frame_id = parent_frame_id
        self._transform_stamped.child_frame_id = child_frame_id
        self._transform_stamped.header.stamp = self._node.get_clock().now().to_msg()
        self._transform_stamped.transform.translation.x = float(translation[0])
        self._transform_stamped.transform.translation.y = float(translation[1])
        self._transform_stamped.transform.translation.z = float(translation[2])
        if xyzw:
            self._transform_stamped.transform.rotation.x = float(rotation[0])
            self._transform_stamped.transform.rotation.y = float(rotation[1])
            self._transform_stamped.transform.rotation.z = float(rotation[2])
            self._transform_stamped.transform.rotation.w = float(rotation[3])
        else:
            self._transform_stamped.transform.rotation.w = float(rotation[0])
            self._transform_stamped.transform.rotation.x = float(rotation[1])
            self._transform_stamped.transform.rotation.y = float(rotation[2])
            self._transform_stamped.transform.rotation.z = float(rotation[3])
        self.__tf2_broadcaster.sendTransform(self._transform_stamped)

def broadcast_tf(self, parent_frame_id: str, child_frame_id: str, translation: Tuple[float, float, float], rotation: Tuple[float, float, float, float], xyzw: bool=True):
    """
        Broadcast transformation of the camera
        """
    self._transform_stamped.header.frame_id = parent_frame_id
    self._transform_stamped.child_frame_id = child_frame_id
    self._transform_stamped.header.stamp = self._node.get_clock().now().to_msg()
    self._transform_stamped.transform.translation.x = float(translation[0])
    self._transform_stamped.transform.translation.y = float(translation[1])
    self._transform_stamped.transform.translation.z = float(translation[2])
    if xyzw:
        self._transform_stamped.transform.rotation.x = float(rotation[0])
        self._transform_stamped.transform.rotation.y = float(rotation[1])
        self._transform_stamped.transform.rotation.z = float(rotation[2])
        self._transform_stamped.transform.rotation.w = float(rotation[3])
    else:
        self._transform_stamped.transform.rotation.w = float(rotation[0])
        self._transform_stamped.transform.rotation.x = float(rotation[1])
        self._transform_stamped.transform.rotation.y = float(rotation[2])
        self._transform_stamped.transform.rotation.z = float(rotation[3])
    self.__tf2_broadcaster.sendTransform(self._transform_stamped)

class RealEvaluationRuntime(Runtime):
    """
    Implementation of :py:class:`~gym_ignition.base.runtime.Runtime` for execution
    of trained agents on real robots (evaluation only).

    It is assumed that the task has an interface that is invariant to sim/real domain for both actions and observations (e.g. ROS 2 middleware).

    This runtime requires manual reset of the workspace as well as manual logging
    of success rate.

    Enable `manual_stepping` to manually step through the execution (safe mode).
    """

    def __init__(self, task_cls: type, agent_rate: float, manual_stepping: bool=True, **kwargs):
        task = task_cls(agent_rate=agent_rate, **kwargs)
        if not isinstance(task, Task):
            raise RuntimeError('The task is not compatible with the runtime')
        super().__init__(task=task, agent_rate=agent_rate)
        self.action_space, self.observation_space = self.task.create_spaces()
        self.task.action_space = self.action_space
        self.task.observation_space = self.observation_space
        self.seed()
        self._manual_stepping = manual_stepping
        if manual_stepping:
            print("Safety feature for manual stepping is enabled. 'Enter' must be pressed to perform each step.")
        print("Press 'ESC' to terminate.")
        print("Press 'd' once episode is done (either success of failure). Success rate must be logged manually.")
        self._manual_done = False
        self._manual_terminate = False
        listener = keyboard.Listener(on_press=self.on_press)
        listener.start()
        self.running_time = 0.0
        self.start_time = time.time()

    def timestamp(self, running_time: bool=True) -> float:
        if running_time:
            return self.running_time
        else:
            return time.time() - self.start_time

    def step(self, action: Action) -> State:
        if self._manual_stepping:
            input('Press a key to continue...')
        pre_step_time = time.time()
        if self._manual_terminate:
            print('Terminating...')
            sys.exit()
        if not self._manual_done:
            if not self.action_space.contains(action):
                logger.warn('The action does not belong to the action space')
            print('Performing action...')
            self.task.set_action(action)
            if isinstance(self.task, Manipulation):
                print('Waiting until the action is executed...')
                self.task.wait_until_action_executed()
        observation = self.task.get_observation()
        assert isinstance(observation, np.ndarray)
        if not self.observation_space.contains(observation):
            logger.warn('The observation does not belong to the observation space')
        reward = 0.0
        done = self._manual_done
        info = {}
        self.running_time += time.time() - pre_step_time
        return State((Observation(observation), Reward(reward), Done(done), Info(info)))

    def reset(self) -> Observation:
        input('Episode done, please reset the workspace for a new episode. Once the workspace is reset, press any key.')
        print('After 5 seconds, the robot will move to its initial joint configuration. Be ready...')
        time.sleep(5.0)
        if isinstance(self.task, Manipulation):
            print('Moving to the initial joint configuration...')
            self.task.move_to_initial_joint_configuration()
        input('Press any key to confirm that robot and workspace are reset...')
        self._manual_done = False
        self.task.reset_task()
        observation = self.task.get_observation()
        assert isinstance(observation, np.ndarray)
        if not self.observation_space.contains(observation):
            logger.warn('The observation does not belong to the observation space')
        return Observation(observation)

    def seed(self, seed: Optional[int]=None) -> SeedList:
        seed = self.task.seed_task(seed)
        return seed

    def render(self, mode: str='human'):
        pass

    def close(self):
        pass

    def on_press(self, key: keyboard.KeyCode):
        print('')
        if keyboard.KeyCode.from_char('d') == key:
            print("'d' pressed: This episode is now considered to be finished. Please log whether it was success or failure.")
            self._manual_done = True
        elif keyboard.Key.esc == key:
            print("'ESC' pressed: Termination signal received...")
            self._manual_terminate = True

def timestamp(self, running_time: bool=True) -> float:
    if running_time:
        return self.running_time
    else:
        return time.time() - self.start_time

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

def set_action(self, action: Action):
    self.get_logger().debug(f'action: {action}')
    if self._use_servo:
        linear = action[0:3]
        self.servo(linear=linear)
    else:
        position = self.get_relative_ee_position(action[0:3])
        quat_xyzw = (1.0, 0.0, 0.0, 0.0)
        self.moveit2.move_to_pose(position=position, quat_xyzw=quat_xyzw)

class SuccessRateImpl:
    """
    Moving average over the success rate of last N episodes.
    """
    INFO_CURRICULUM_PREFIX: str = 'curriculum/'

    def __init__(self, initial_success_rate: float=0.0, rolling_average_n: int=100, **kwargs):
        self.__success_rate = initial_success_rate
        self.__rolling_average_n = rolling_average_n
        self.__previous_success_rate_weight: int = 0
        self.__collected_samples: int = 0

    def get_info(self) -> Dict:
        info = {f'{self.INFO_CURRICULUM_PREFIX}_success_rate': self.__success_rate}
        return info

    def update_success_rate(self, is_success: bool):
        if self.__collected_samples < self.__rolling_average_n:
            self.__previous_success_rate_weight = self.__collected_samples
            self.__collected_samples += 1
        self.__success_rate = (self.__previous_success_rate_weight * self.__success_rate + float(is_success)) / self.__collected_samples

    @property
    def success_rate(self) -> float:
        return self.__success_rate

def update_success_rate(self, is_success: bool):
    if self.__collected_samples < self.__rolling_average_n:
        self.__previous_success_rate_weight = self.__collected_samples
        self.__collected_samples += 1
    self.__success_rate = (self.__previous_success_rate_weight * self.__success_rate + float(is_success)) / self.__collected_samples

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

def write_original_scale(self, mesh, model_path):
    file = open(self.get_original_scale_path(model_path), 'w')
    file.write(str(mesh.scale))
    file.close()

def read_original_scale(self, model_path) -> float:
    file = open(self.get_original_scale_path(model_path), 'r')
    original_scale = file.read()
    file.close()
    return float(original_scale)

def blacklist_model(self, model_path, reason='Unknown'):
    if self._enable_blacklisting:
        bl_file = open(self.get_blacklisted_path(model_path), 'w')
        bl_file.write(reason)
        bl_file.close()
    logger.warn('%s model "%s". Reason: %s.' % ('Blacklisting' if self._enable_blacklisting else 'Skipping', model_path, reason))

def is_blacklisted(self, model_path) -> bool:
    return os.path.isfile(self.get_blacklisted_path(model_path))

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

def xacro2sdf(input_file_path: str, mappings: Dict, model_path_remap: Optional[Tuple[str, str]]) -> str:
    """Convert xacro (URDF variant) with given arguments to SDF and return as a string."""
    for keys, values in mappings.items():
        mappings[keys] = str(values)
    urdf_xml = xacro.process(input_file_name=input_file_path, mappings=mappings)
    with tempfile.NamedTemporaryFile() as tmp_urdf:
        with open(tmp_urdf.name, 'w') as urdf_file:
            urdf_file.write(urdf_xml)
        result = subprocess.run(['ign', 'sdf', '-p', tmp_urdf.name], stdout=subprocess.PIPE)
        sdf_xml = result.stdout.decode('utf-8')
        if model_path_remap is not None:
            sdf_xml = sdf_xml.replace(model_path_remap[0], model_path_remap[1])
        return sdf_xml

