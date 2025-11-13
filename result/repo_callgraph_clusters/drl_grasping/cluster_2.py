# Cluster 2

def flatten_dict_observations(env: gym.Env) -> gym.Env:
    assert isinstance(env.observation_space, gym.spaces.Dict)
    try:
        return gym.wrappers.FlattenObservation(env)
    except AttributeError:
        keys = env.observation_space.spaces.keys()
        return gym.wrappers.FlattenDictWrapper(env, dict_keys=list(keys))

def get_wrapper_class(hyperparams: Dict[str, Any]) -> Optional[Callable[[gym.Env], gym.Env]]:
    """
    Get one or more Gym environment wrapper class specified as a hyper parameter
    "env_wrapper".
    e.g.
    env_wrapper: gym_minigrid.wrappers.FlatObsWrapper

    for multiple, specify a list:

    env_wrapper:
        - utils.wrappers.PlotActionWrapper
        - utils.wrappers.TimeFeatureWrapper


    :param hyperparams:
    :return: maybe a callable to wrap the environment
        with one or multiple gym.Wrapper
    """

    def get_module_name(wrapper_name):
        return '.'.join(wrapper_name.split('.')[:-1])

    def get_class_name(wrapper_name):
        return wrapper_name.split('.')[-1]
    if 'env_wrapper' in hyperparams.keys():
        wrapper_name = hyperparams.get('env_wrapper')
        if wrapper_name is None:
            return None
        if not isinstance(wrapper_name, list):
            wrapper_names = [wrapper_name]
        else:
            wrapper_names = wrapper_name
        wrapper_classes = []
        wrapper_kwargs = []
        for wrapper_name in wrapper_names:
            if isinstance(wrapper_name, dict):
                assert len(wrapper_name) == 1, f'You have an error in the formatting of your YAML file near {wrapper_name}. You should check the indentation.'
                wrapper_dict = wrapper_name
                wrapper_name = list(wrapper_dict.keys())[0]
                kwargs = wrapper_dict[wrapper_name]
            else:
                kwargs = {}
            wrapper_module = importlib.import_module(get_module_name(wrapper_name))
            wrapper_class = getattr(wrapper_module, get_class_name(wrapper_name))
            wrapper_classes.append(wrapper_class)
            wrapper_kwargs.append(kwargs)

        def wrap_env(env: gym.Env) -> gym.Env:
            """
            :param env:
            :return:
            """
            for wrapper_class, kwargs in zip(wrapper_classes, wrapper_kwargs):
                env = wrapper_class(env, **kwargs)
            return env
        return wrap_env
    else:
        return None

def get_callback_list(hyperparams: Dict[str, Any]) -> List[BaseCallback]:
    """
    Get one or more Callback class specified as a hyper-parameter
    "callback".
    e.g.
    callback: stable_baselines3.common.callbacks.CheckpointCallback

    for multiple, specify a list:

    callback:
        - utils.callbacks.PlotActionWrapper
        - stable_baselines3.common.callbacks.CheckpointCallback

    :param hyperparams:
    :return:
    """

    def get_module_name(callback_name):
        return '.'.join(callback_name.split('.')[:-1])

    def get_class_name(callback_name):
        return callback_name.split('.')[-1]
    callbacks = []
    if 'callback' in hyperparams.keys():
        callback_name = hyperparams.get('callback')
        if callback_name is None:
            return callbacks
        if not isinstance(callback_name, list):
            callback_names = [callback_name]
        else:
            callback_names = callback_name
        for callback_name in callback_names:
            if isinstance(callback_name, dict):
                assert len(callback_name) == 1, f'You have an error in the formatting of your YAML file near {callback_name}. You should check the indentation.'
                callback_dict = callback_name
                callback_name = list(callback_dict.keys())[0]
                kwargs = callback_dict[callback_name]
            else:
                kwargs = {}
            callback_module = importlib.import_module(get_module_name(callback_name))
            callback_class = getattr(callback_module, get_class_name(callback_name))
            callbacks.append(callback_class(**kwargs))
    return callbacks

def str2bool(value: Union[str, bool]) -> bool:
    """
    Convert logical string to boolean. Can be used as argparse type.
    """
    if isinstance(value, bool):
        return value
    if value.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif value.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

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

def step(self, action):
    self.signal.append(action)
    filtered = np.zeros_like(action)
    for i in range(self.action_space.shape[0]):
        smoothed_action = lowpass(np.array(self.signal)[:, i], freq=self.freq, df=self.df)
        filtered[i] = smoothed_action[-1]
    return self.env.step(filtered)

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

def _create_obs_from_history(self):
    return np.concatenate((self.obs_history, self.action_history))

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

def _create_obs_from_history(self):
    return np.concatenate((self.obs_history, self.action_history))

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

def __init___with_checking_for_stacked_images_and_octrees(self, buffer_size: int, observation_space: spaces.Space, action_space: spaces.Space, device: Union[th.device, str]='cpu', n_envs: int=1, optimize_memory_usage: bool=False, separate_networks_for_stacks: bool=True):
    __old__init__(self, buffer_size=buffer_size, observation_space=observation_space, action_space=action_space, device=device, n_envs=n_envs, optimize_memory_usage=optimize_memory_usage)
    self.contains_octree_obs = False
    self.contains_stacked_image_obs = False
    if isinstance(observation_space, spaces.Box) and len(observation_space.shape) == 2:
        if np.uint8 == observation_space.dtype and np.all(0 == observation_space.low) and np.all(255 == observation_space.high):
            self.contains_octree_obs = True
            self._separate_networks_for_stacks = separate_networks_for_stacks
        elif np.float32 == observation_space.dtype and np.all(-1.0 == observation_space.low) and np.all(1.0 == observation_space.high):
            self.contains_stacked_image_obs = True
            self._separate_networks_for_stacks = separate_networks_for_stacks

def _get_samples_with_support_for_octree(self, batch_inds: np.ndarray, env: Optional[VecNormalize]=None) -> ReplayBufferSamples:
    if self.contains_octree_obs:
        obs = self.observations[batch_inds, 0, :]
        obs = preprocess_stacked_octree_batch(obs, self.device, separate_batches=self._separate_networks_for_stacks)
        if self.optimize_memory_usage:
            next_obs = self.observations[(batch_inds + 1) % self.buffer_size, 0, :]
        else:
            next_obs = self.next_observations[batch_inds, 0, :]
        next_obs = preprocess_stacked_octree_batch(next_obs, self.device, separate_batches=self._separate_networks_for_stacks)
        return ReplayBufferSamples(observations=obs, actions=self.to_torch(self.actions[batch_inds, 0, :]), next_observations=next_obs, dones=self.to_torch(self.dones[batch_inds]), rewards=self.to_torch(self._normalize_reward(self.rewards[batch_inds], env)))
    elif self.contains_stacked_image_obs:
        obs = self.observations[batch_inds, 0, :]
        obs = preprocess_stacked_depth_image_batch(obs, self.device, separate_batches=self._separate_networks_for_stacks)
        if self.optimize_memory_usage:
            next_obs = self.observations[(batch_inds + 1) % self.buffer_size, 0, :]
        else:
            next_obs = self.next_observations[batch_inds, 0, :]
        next_obs = preprocess_stacked_depth_image_batch(next_obs, self.device, separate_batches=self._separate_networks_for_stacks)
        return ReplayBufferSamples(observations=obs, actions=self.to_torch(self.actions[batch_inds, 0, :]), next_observations=next_obs, dones=self.to_torch(self.dones[batch_inds]), rewards=self.to_torch(self._normalize_reward(self.rewards[batch_inds], env)))
    else:
        return __old_get_samples__(self, batch_inds=batch_inds, env=env)

def pointcloud2_to_open3d(ros_point_cloud2: sensor_msgs.msg.PointCloud2, include_color: bool=False, include_intensity: bool=False, fix_rgb_channel_order: bool=False) -> open3d.geometry.PointCloud:
    open3d_pc = open3d.geometry.PointCloud()
    size = ros_point_cloud2.width * ros_point_cloud2.height
    xyz_dtype = '>f4' if ros_point_cloud2.is_bigendian else '<f4'
    xyz = numpy.ndarray(shape=(size, 3), dtype=xyz_dtype, buffer=ros_point_cloud2.data, offset=0, strides=(ros_point_cloud2.point_step, 4))
    valid_points = numpy.isfinite(xyz).any(axis=1)
    open3d_pc.points = open3d.utility.Vector3dVector(xyz[valid_points].astype(numpy.float64))
    if include_color or include_intensity:
        if len(ros_point_cloud2.fields) > 3:
            bgr = numpy.ndarray(shape=(size, 3), dtype=numpy.uint8, buffer=ros_point_cloud2.data, offset=ros_point_cloud2.fields[3].offset, strides=(ros_point_cloud2.point_step, 1))
            if fix_rgb_channel_order:
                bgr[:, 0], bgr[:, 2] = (bgr[:, 2], bgr[:, 0].copy())
            open3d_pc.colors = open3d.utility.Vector3dVector((bgr[valid_points] / 255).astype(numpy.float64))
        else:
            open3d_pc.colors = open3d.utility.Vector3dVector(numpy.zeros((len(valid_points), 3), dtype=numpy.float64))
    return open3d_pc

def open3d_point_cloud_to_octree_points(open3d_point_cloud: open3d.geometry.PointCloud, include_color: bool=False, include_intensity: bool=False) -> pyoctree.Points:
    octree_points = pyoctree.Points()
    if include_color:
        features = numpy.reshape(numpy.asarray(open3d_point_cloud.colors), -1)
    elif include_intensity:
        features = numpy.asarray(open3d_point_cloud.colors)[:, 0]
    else:
        features = []
    octree_points.set_points(numpy.reshape(numpy.asarray(open3d_point_cloud.points), -1), numpy.reshape(numpy.asarray(open3d_point_cloud.normals), -1), features, [])
    return octree_points

def quat_to_wxyz(xyzw: Union[numpy.ndarray, Tuple[float, float, float, float]]) -> numpy.ndarray:
    if isinstance(xyzw, tuple):
        return (xyzw[3], xyzw[0], xyzw[1], xyzw[2])
    return xyzw[[3, 0, 1, 2]]

def quat_to_xyzw(wxyz: Union[numpy.ndarray, Tuple[float, float, float, float]]) -> numpy.ndarray:
    if isinstance(wxyz, tuple):
        return (wxyz[1], wxyz[2], wxyz[3], wxyz[0])
    return wxyz[[1, 2, 3, 0]]

def set_log_level(log_level: Union[int, str]):
    """
    Set log level for (Gym) Ignition.
    """
    if not isinstance(log_level, int):
        log_level = str(log_level).upper()
        if 'WARNING' == log_level:
            log_level = 'WARN'
        elif not log_level in ['DEBUG', 'INFO', 'WARN', 'ERROR', 'DISABLED']:
            log_level = 'DISABLED'
        log_level = getattr(gym_logger, log_level)
    gym_ign_logger.set_level(level=log_level, scenario_level=log_level)

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

class CameraSubscriber:

    def __init__(self, node: Node, topic: str, is_point_cloud: bool, callback_group: Optional[CallbackGroup]=None):
        self._node = node
        if is_point_cloud:
            camera_msg_type = PointCloud2
        else:
            camera_msg_type = Image
        self.__observation = camera_msg_type()
        self._node.create_subscription(msg_type=camera_msg_type, topic=topic, callback=self.observation_callback, qos_profile=QoSProfile(reliability=QoSReliabilityPolicy.RELIABLE, durability=QoSDurabilityPolicy.VOLATILE, history=QoSHistoryPolicy.KEEP_LAST, depth=1), callback_group=callback_group)
        self.__observation_mutex = Lock()
        self.__new_observation_available = False

    def observation_callback(self, msg):
        """
        Callback for getting observation.
        """
        self.__observation_mutex.acquire()
        self.__observation = msg
        self.__new_observation_available = True
        self._node.get_logger().debug('New observation received.')
        self.__observation_mutex.release()

    def get_observation(self) -> Union[PointCloud2, Image]:
        """
        Get the last received observation.
        """
        self.__observation_mutex.acquire()
        observation = self.__observation
        self.__observation_mutex.release()
        return observation

    def reset_new_observation_checker(self):
        """
        Reset checker of new observations, i.e. `self.new_observation_available()`
        """
        self.__observation_mutex.acquire()
        self.__new_observation_available = False
        self.__observation_mutex.release()

    @property
    def new_observation_available(self):
        """
        Check if new observation is available since `self.reset_new_observation_checker()` was called
        """
        return self.__new_observation_available

def observation_callback(self, msg):
    """
        Callback for getting observation.
        """
    self.__observation_mutex.acquire()
    self.__observation = msg
    self.__new_observation_available = True
    self._node.get_logger().debug('New observation received.')
    self.__observation_mutex.release()

def get_observation(self) -> Union[PointCloud2, Image]:
    """
        Get the last received observation.
        """
    self.__observation_mutex.acquire()
    observation = self.__observation
    self.__observation_mutex.release()
    return observation

def reset_new_observation_checker(self):
    """
        Reset checker of new observations, i.e. `self.new_observation_available()`
        """
    self.__observation_mutex.acquire()
    self.__new_observation_available = False
    self.__observation_mutex.release()

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

def check_all_objects_outside_workspace(self, object_positions: Dict[str, Tuple[float, float, float]]) -> bool:
    """
        Returns true if all objects are outside the workspace
        """
    return all([self.check_object_outside_workspace(object_position) for object_position in object_positions.values()])

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

def get_observation(self) -> Observation:
    image = self.camera_sub.get_observation()
    depth_image = np.frombuffer(image.data, dtype=np.float32).reshape(self._camera_height, self._camera_width, 1)
    depth_image[depth_image == np.inf] = 0.0
    observation = Observation(depth_image)
    self.get_logger().debug(f'\nobservation: {observation}')
    return observation

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

