# Cluster 33

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

def orientation_6d_to_quat(v1: Tuple[float, float, float], v2: Tuple[float, float, float]) -> Tuple[float, float, float, float]:
    col1 = v1 / numpy.linalg.norm(v1)
    col2 = v2 / numpy.linalg.norm(v2)
    col3 = numpy.cross(col1, col2)
    quat_xyzw = Rotation.from_matrix(numpy.array([col1, col2, col3]).T).as_quat()
    return quat_xyzw

def orientation_quat_to_6d(quat_xyzw: Tuple[float, float, float, float]) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
    rot_mat = Rotation.from_quat(quat_xyzw).as_matrix()
    return (tuple(rot_mat[:, 0]), tuple(rot_mat[:, 1]))

def transform_move_to_model_pose(world: World, position: Tuple[float, float, float], quat: Tuple[float, float, float, float], target_model: Union[ModelWrapper, str], target_link: Union[Link, str, None]=None, xyzw: bool=False) -> Tuple[Tuple[float, float, float], Tuple[float, float, float, float]]:
    """
    Transform such that original `position` and `quat` are represented with respect to `target_model::target_link`.
    The resulting pose is still represented in world coordinate system.
    """
    target_frame_position, target_frame_quat = get_model_pose(world, model=target_model, link=target_link, xyzw=True)
    transformed_position = Rotation.from_quat(target_frame_quat).apply(position)
    transformed_position = (transformed_position[0] + target_frame_position[0], transformed_position[1] + target_frame_position[1], transformed_position[2] + target_frame_position[2])
    if not xyzw:
        target_frame_quat = quat_to_wxyz(target_frame_quat)
    transformed_quat = quat_mul(quat, target_frame_quat, xyzw=xyzw)
    return (transformed_position, transformed_quat)

def transform_move_to_model_position(world: World, position: Tuple[float, float, float], target_model: Union[ModelWrapper, str], target_link: Union[Link, str, None]=None) -> Tuple[Tuple[float, float, float], Tuple[float, float, float, float]]:
    target_frame_position, target_frame_quat_xyzw = get_model_pose(world, model=target_model, link=target_link, xyzw=True)
    transformed_position = Rotation.from_quat(target_frame_quat_xyzw).apply(position)
    transformed_position = (target_frame_position[0] + transformed_position[0], target_frame_position[1] + transformed_position[1], target_frame_position[2] + transformed_position[2])
    return transformed_position

def transform_move_to_model_orientation(world: World, quat: Tuple[float, float, float, float], target_model: Union[ModelWrapper, str], target_link: Union[Link, str, None]=None, xyzw: bool=False) -> Tuple[Tuple[float, float, float], Tuple[float, float, float, float]]:
    target_frame_quat = get_model_orientation(world, model=target_model, link=target_link, xyzw=xyzw)
    transformed_quat = quat_mul(quat, target_frame_quat, xyzw=xyzw)
    return transformed_quat

def transform_change_reference_frame_pose(world: World, position: Tuple[float, float, float], quat: Tuple[float, float, float, float], target_model: Union[ModelWrapper, str], target_link: Union[Link, str, None]=None, xyzw: bool=False) -> Tuple[Tuple[float, float, float], Tuple[float, float, float, float]]:
    """
    Change reference frame of original `position` and `quat` from world coordinate system to `target_model::target_link` coordinate system.
    """
    target_frame_position, target_frame_quat = get_model_pose(world, model=target_model, link=target_link, xyzw=True)
    transformed_position = (position[0] - target_frame_position[0], position[1] - target_frame_position[1], position[2] - target_frame_position[2])
    transformed_position = Rotation.from_quat(target_frame_quat).apply(transformed_position, inverse=True)
    if not xyzw:
        target_frame_quat = quat_to_wxyz(target_frame_quat)
    transformed_quat = quat_mul(target_frame_quat, quat, xyzw=xyzw)
    return (tuple(transformed_position), transformed_quat)

def transform_change_reference_frame_position(world: World, position: Tuple[float, float, float], target_model: Union[ModelWrapper, str], target_link: Union[Link, str, None]=None) -> Tuple[Tuple[float, float, float], Tuple[float, float, float, float]]:
    target_frame_position, target_frame_quat_xyzw = get_model_pose(world, model=target_model, link=target_link, xyzw=True)
    transformed_position = (position[0] - target_frame_position[0], position[1] - target_frame_position[1], position[2] - target_frame_position[2])
    transformed_position = Rotation.from_quat(target_frame_quat_xyzw).apply(transformed_position, inverse=True)
    return tuple(transformed_position)

def transform_change_reference_frame_orientation(world: World, quat: Tuple[float, float, float, float], target_model: Union[ModelWrapper, str], target_link: Union[Link, str, None]=None, xyzw: bool=False) -> Tuple[Tuple[float, float, float], Tuple[float, float, float, float]]:
    target_frame_quat = get_model_orientation(world, model=target_model, link=target_link, xyzw=xyzw)
    transformed_quat = quat_mul(target_frame_quat, quat, xyzw=xyzw)
    return transformed_quat

def distance_to_nearest_point(origin: Tuple[float, float, float], points: List[Tuple[float, float, float]]) -> float:
    return np.linalg.norm(np.array(points) - np.array(origin), axis=1).min()

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

def get_random_camera_pose_sample_process(self, centre: Tuple[float, float, float], position: Tuple[float, float, float], focal_point_z_offset: float) -> Tuple[Tuple[float, float, float], Tuple[float, float, float, float]]:
    rpy = [0.0, np.arctan2(position[2] - focal_point_z_offset, np.linalg.norm((position[0] - centre[0], position[1] - centre[1]), 2)), np.arctan2(position[1] - centre[1], position[0] - centre[0]) + np.pi]
    quat_xyzw = Rotation.from_euler('xyz', rpy).as_quat()
    return (position, quat_xyzw)

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

def restrict_position_goal_to_workspace(self, position: Tuple[float, float, float]) -> Tuple[float, float, float]:
    return (min(self.workspace_max_bound[0], max(self.workspace_min_bound[0], position[0])), min(self.workspace_max_bound[1], max(self.workspace_min_bound[1], position[1])), min(self.workspace_max_bound[2], max(self.workspace_min_bound[2], position[2])))

def restrict_servo_translation_to_workspace(self, translation: Tuple[float, float, float]) -> Tuple[float, float, float]:
    current_ee_position = self.get_ee_position()
    translation = tuple((0.0 if current_ee_position[i] > self.workspace_max_bound[i] and translation[i] > 0.0 or (current_ee_position[i] < self.workspace_min_bound[i] and translation[i] < 0.0) else translation[i] for i in range(3)))
    return translation

def add_parameter_overrides(self, parameter_overrides: Dict[str, any]):
    self.add_task_parameter_overrides(parameter_overrides)
    self.add_randomizer_parameter_overrides(parameter_overrides)

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

def get_reward(self) -> Reward:
    return self.curriculum.get_reward()

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

def get_distance_to_target(self) -> Tuple[float, float, float]:
    ee_position = self.get_ee_position()
    object_position = self.get_object_position(object_model=self.object_names[0])
    return distance_to_nearest_point(origin=ee_position, points=[object_position])

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

def get_reward(self) -> Reward:
    if self.__enable_stage_reward_curriculum:
        return StageRewardCurriculum.get_reward(self, ee_position=self.__task.get_ee_position(), object_positions=self.__task.get_object_positions(), touched_objects=self.__task.get_touched_objects(), grasped_objects=self.__task.get_grasped_objects())
    else:
        return StageRewardCurriculum.get_reward(self, only_last_stage=True, object_positions=self.__task.get_object_positions(), grasped_objects=self.__task.get_grasped_objects())

class WorkspaceScaleCurriculum:
    """
    Curriculum that increases the workspace size as the success rate increases.
    """
    INFO_CURRICULUM_PREFIX: str = 'curriculum/'

    def __init__(self, task: Task, success_rate_impl: SuccessRateImpl, min_workspace_scale: float, max_workspace_volume: Tuple[float, float, float], max_workspace_scale_success_rate_threshold: float, **kwargs):
        self.__task = task
        self.__success_rate_impl = success_rate_impl
        self.__min_workspace_scale = min_workspace_scale
        self.__max_workspace_volume = max_workspace_volume
        self.__max_workspace_scale_success_rate_threshold = max_workspace_scale_success_rate_threshold

    def get_info(self) -> Dict:
        info = {f'{self.INFO_CURRICULUM_PREFIX}{INFO_MEAN_EPISODE_KEY}workspace_scale': self.__workspace_scale}
        return info

    def reset_task(self):
        self.__update_workspace_size()

    def __update_workspace_size(self):
        self.__workspace_scale = min(1.0, max(self.__min_workspace_scale, self.__success_rate_impl.success_rate / self.__max_workspace_scale_success_rate_threshold))
        workspace_volume_new = (self.__workspace_scale * self.__max_workspace_volume[0], self.__workspace_scale * self.__max_workspace_volume[1], self.__max_workspace_volume[2])
        workspace_volume_half_new = (workspace_volume_new[0] / 2, workspace_volume_new[1] / 2, workspace_volume_new[2] / 2)
        workspace_min_bound_new = (self.__task.workspace_centre[0] - workspace_volume_half_new[0], self.__task.workspace_centre[1] - workspace_volume_half_new[1], self.__task.workspace_centre[2] - workspace_volume_half_new[2])
        workspace_max_bound_new = (self.__task.workspace_centre[0] + workspace_volume_half_new[0], self.__task.workspace_centre[1] + workspace_volume_half_new[1], self.__task.workspace_centre[2] + workspace_volume_half_new[2])
        self.__task.add_task_parameter_overrides({'workspace_volume': workspace_volume_new, 'workspace_min_bound': workspace_min_bound_new, 'workspace_max_bound': workspace_max_bound_new})

def __update_workspace_size(self):
    self.__workspace_scale = min(1.0, max(self.__min_workspace_scale, self.__success_rate_impl.success_rate / self.__max_workspace_scale_success_rate_threshold))
    workspace_volume_new = (self.__workspace_scale * self.__max_workspace_volume[0], self.__workspace_scale * self.__max_workspace_volume[1], self.__max_workspace_volume[2])
    workspace_volume_half_new = (workspace_volume_new[0] / 2, workspace_volume_new[1] / 2, workspace_volume_new[2] / 2)
    workspace_min_bound_new = (self.__task.workspace_centre[0] - workspace_volume_half_new[0], self.__task.workspace_centre[1] - workspace_volume_half_new[1], self.__task.workspace_centre[2] - workspace_volume_half_new[2])
    workspace_max_bound_new = (self.__task.workspace_centre[0] + workspace_volume_half_new[0], self.__task.workspace_centre[1] + workspace_volume_half_new[1], self.__task.workspace_centre[2] + workspace_volume_half_new[2])
    self.__task.add_task_parameter_overrides({'workspace_volume': workspace_volume_new, 'workspace_min_bound': workspace_min_bound_new, 'workspace_max_bound': workspace_max_bound_new})

class ObjectSpawnVolumeScaleCurriculum:
    """
    Curriculum that increases the object spawn volume as the success rate increases.
    """
    INFO_CURRICULUM_PREFIX: str = 'curriculum/'

    def __init__(self, task: Task, success_rate_impl: SuccessRateImpl, min_object_spawn_volume_scale: float, max_object_spawn_volume: Tuple[float, float, float], max_object_spawn_volume_scale_success_rate_threshold: float, **kwargs):
        self.__task = task
        self.__success_rate_impl = success_rate_impl
        self.__min_object_spawn_volume_scale = min_object_spawn_volume_scale
        self.__max_object_spawn_volume = max_object_spawn_volume
        self.__max_object_spawn_volume_scale_success_rate_threshold = max_object_spawn_volume_scale_success_rate_threshold

    def get_info(self) -> Dict:
        info = {f'{self.INFO_CURRICULUM_PREFIX}{INFO_MEAN_EPISODE_KEY}object_spawn_volume_scale': self.__object_spawn_volume_scale}
        return info

    def reset_task(self):
        self.__update_object_spawn_volume_size()

    def __update_object_spawn_volume_size(self):
        self.__object_spawn_volume_scale = min(1.0, max(self.__min_object_spawn_volume_scale, self.__success_rate_impl.success_rate / self.__max_object_spawn_volume_scale_success_rate_threshold))
        object_spawn_volume_volume_new = (self.__object_spawn_volume_scale * self.__max_object_spawn_volume[0], self.__object_spawn_volume_scale * self.__max_object_spawn_volume[1], self.__object_spawn_volume_scale * self.__max_object_spawn_volume[2])
        self.__task.add_randomizer_parameter_overrides({'object_random_spawn_volume': object_spawn_volume_volume_new})

def __update_object_spawn_volume_size(self):
    self.__object_spawn_volume_scale = min(1.0, max(self.__min_object_spawn_volume_scale, self.__success_rate_impl.success_rate / self.__max_object_spawn_volume_scale_success_rate_threshold))
    object_spawn_volume_volume_new = (self.__object_spawn_volume_scale * self.__max_object_spawn_volume[0], self.__object_spawn_volume_scale * self.__max_object_spawn_volume[1], self.__object_spawn_volume_scale * self.__max_object_spawn_volume[2])
    self.__task.add_randomizer_parameter_overrides({'object_random_spawn_volume': object_spawn_volume_volume_new})

class ObjectCountCurriculum:
    """
    Curriculum that increases the number of objects as the success rate increases.
    """
    INFO_CURRICULUM_PREFIX: str = 'curriculum/'

    def __init__(self, task: Task, success_rate_impl: SuccessRateImpl, object_count_min: int, object_count_max: int, max_object_count_success_rate_threshold: float, **kwargs):
        self.__task = task
        self.__success_rate_impl = success_rate_impl
        self.__object_count_min = object_count_min
        self.__object_count_max = object_count_max
        self.__max_object_count_success_rate_threshold = max_object_count_success_rate_threshold
        self.__object_count_min_max_diff = object_count_max - object_count_min
        if self.__object_count_min_max_diff < 0:
            raise Exception("'object_count_min' cannot be larger than 'object_count_max'")

    def get_info(self) -> Dict:
        info = {f'{self.INFO_CURRICULUM_PREFIX}object_count': self.__object_count}
        return info

    def reset_task(self):
        self.__update_object_count()

    def __update_object_count(self):
        self.__object_count = min(self.__object_count_max, math.floor(self.__object_count_min + self.__success_rate_impl.success_rate / self.__max_object_count_success_rate_threshold * self.__object_count_min_max_diff))
        self.__task.add_randomizer_parameter_overrides({'object_count': self.__object_count})

def __init__(self, task: Task, success_rate_impl: SuccessRateImpl, object_count_min: int, object_count_max: int, max_object_count_success_rate_threshold: float, **kwargs):
    self.__task = task
    self.__success_rate_impl = success_rate_impl
    self.__object_count_min = object_count_min
    self.__object_count_max = object_count_max
    self.__max_object_count_success_rate_threshold = max_object_count_success_rate_threshold
    self.__object_count_min_max_diff = object_count_max - object_count_min
    if self.__object_count_min_max_diff < 0:
        raise Exception("'object_count_min' cannot be larger than 'object_count_max'")

def __update_object_count(self):
    self.__object_count = min(self.__object_count_max, math.floor(self.__object_count_min + self.__success_rate_impl.success_rate / self.__max_object_count_success_rate_threshold * self.__object_count_min_max_diff))
    self.__task.add_randomizer_parameter_overrides({'object_count': self.__object_count})

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

def __get_arm_joint_positions(self) -> Optional[np.ndarray[float]]:
    joint_state = self.__task.moveit2.joint_state
    if joint_state is None:
        return None
    if self.__arm_joint_indices is None:
        self.__arm_joint_indices = [i for i, joint_name in enumerate(joint_state.name) if joint_name in self.__task.robot_arm_joint_names]
    return np.take(joint_state.position, self.__arm_joint_indices)

class AttributeCurriculum:
    """
    Curriculum that increases the value of an attribute (e.g. requirement) as the success rate increases.
    Currently support only attributes that are increasing.
    """
    INFO_CURRICULUM_PREFIX: str = 'curriculum/'

    def __init__(self, success_rate_impl: SuccessRateImpl, attribute_owner: Type, attribute_name: str, initial_value: float, target_value: float, target_value_threshold: float, **kwargs):
        self.__success_rate_impl = success_rate_impl
        self.__attribute_owner = attribute_owner
        self.__attribute_name = attribute_name
        self.__initial_value = initial_value
        self.__target_value_threshold = target_value_threshold
        self.__current_value = initial_value
        self.__value_diff = target_value - initial_value

    def get_info(self) -> Dict:
        info = {f'{self.INFO_CURRICULUM_PREFIX}{self.__attribute_name}': self.__current_value}
        return info

    def reset_task(self):
        self.__update_attribute()

    def __update_attribute(self):
        scale = min(1.0, max(self.__initial_value, self.__success_rate_impl.success_rate / self.__target_value_threshold))
        self.__current_value = self.__initial_value + scale * self.__value_diff
        if hasattr(self.__attribute_owner, self.__attribute_name):
            setattr(self.__attribute_owner, self.__attribute_name, self.__current_value)
        elif hasattr(self.__attribute_owner, f'_{self.__attribute_name}'):
            setattr(self.__attribute_owner, f'_{self.__attribute_name}', self.__current_value)
        elif hasattr(self.__attribute_owner, f'__{self.__attribute_name}'):
            setattr(self.__attribute_owner, f'__{self.__attribute_name}', self.__current_value)
        else:
            raise Exception(f"Attribute owner '{self.__attribute_owner}' does not have any attribute named {self.__attribute_name}.")

def __update_attribute(self):
    scale = min(1.0, max(self.__initial_value, self.__success_rate_impl.success_rate / self.__target_value_threshold))
    self.__current_value = self.__initial_value + scale * self.__value_diff
    if hasattr(self.__attribute_owner, self.__attribute_name):
        setattr(self.__attribute_owner, self.__attribute_name, self.__current_value)
    elif hasattr(self.__attribute_owner, f'_{self.__attribute_name}'):
        setattr(self.__attribute_owner, f'_{self.__attribute_name}', self.__current_value)
    elif hasattr(self.__attribute_owner, f'__{self.__attribute_name}'):
        setattr(self.__attribute_owner, f'__{self.__attribute_name}', self.__current_value)
    else:
        raise Exception(f"Attribute owner '{self.__attribute_owner}' does not have any attribute named {self.__attribute_name}.")

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

class RandomSun(model_wrapper.ModelWrapper):

    def __init__(self, world: scenario.World, name: str='sun', minmax_elevation: Tuple[float, float]=(-0.15, -0.65), distance: float=800.0, visual: bool=True, radius: float=20.0, color_minmax_r: Tuple[float, float]=(1.0, 1.0), color_minmax_g: Tuple[float, float]=(1.0, 1.0), color_minmax_b: Tuple[float, float]=(1.0, 1.0), specular: float=1.0, attenuation_minmax_range: Tuple[float, float]=(750.0, 15000.0), attenuation_minmax_constant: Tuple[float, float]=(0.5, 1.0), attenuation_minmax_linear: Tuple[float, float]=(0.001, 0.1), attenuation_minmax_quadratic: Tuple[float, float]=(0.0001, 0.01), np_random: Optional[RandomState]=None, **kwargs):
        if np_random is None:
            np_random = np.random.default_rng()
        model_name = get_unique_model_name(world, name)
        direction = np_random.uniform(-1.0, 1.0, (2,))
        direction = direction / np.linalg.norm(direction)
        direction = np.append(direction, np_random.uniform(minmax_elevation[0], minmax_elevation[1]))
        direction = direction / np.linalg.norm(direction)
        initial_pose = scenario.Pose((-direction[0] * distance, -direction[1] * distance, -direction[2] * distance), (1, 0, 0, 0))
        sdf = self.get_sdf(model_name=model_name, direction=direction, visual=visual, radius=radius, color_minmax_r=color_minmax_r, color_minmax_g=color_minmax_g, color_minmax_b=color_minmax_b, attenuation_minmax_range=attenuation_minmax_range, attenuation_minmax_constant=attenuation_minmax_constant, attenuation_minmax_linear=attenuation_minmax_linear, attenuation_minmax_quadratic=attenuation_minmax_quadratic, specular=specular, np_random=np_random)
        ok_model = world.to_gazebo().insert_model_from_string(sdf, initial_pose, model_name)
        if not ok_model:
            raise RuntimeError('Failed to insert ' + model_name)
        model = world.get_model(model_name)
        model_wrapper.ModelWrapper.__init__(self, model=model)

    @classmethod
    def get_sdf(self, model_name: str, direction: Tuple[float, float, float], visual: bool, radius: float, color_minmax_r: Tuple[float, float], color_minmax_g: Tuple[float, float], color_minmax_b: Tuple[float, float], attenuation_minmax_range: Tuple[float, float], attenuation_minmax_constant: Tuple[float, float], attenuation_minmax_linear: Tuple[float, float], attenuation_minmax_quadratic: Tuple[float, float], specular: float, np_random: RandomState) -> str:
        color_r = np_random.uniform(color_minmax_r[0], color_minmax_r[1])
        color_g = np_random.uniform(color_minmax_g[0], color_minmax_g[1])
        color_b = np_random.uniform(color_minmax_b[0], color_minmax_b[1])
        attenuation_range = np_random.uniform(attenuation_minmax_range[0], attenuation_minmax_range[1])
        attenuation_constant = np_random.uniform(attenuation_minmax_constant[0], attenuation_minmax_constant[1])
        attenuation_linear = np_random.uniform(attenuation_minmax_linear[0], attenuation_minmax_linear[1])
        attenuation_quadratic = np_random.uniform(attenuation_minmax_quadratic[0], attenuation_minmax_quadratic[1])
        return f'<sdf version="1.9">\n                <model name="{model_name}">\n                    <static>true</static>\n                    <link name="{model_name}_link">\n                        <light type="directional" name="{model_name}_light">\n                            <direction>{direction[0]} {direction[1]} {direction[2]}</direction>\n                            <attenuation>\n                                <range>{attenuation_range}</range>\n                                <constant>{attenuation_constant}</constant>\n                                <linear>{attenuation_linear}</linear>\n                                <quadratic>{attenuation_quadratic}</quadratic>\n                            </attenuation>\n                            <diffuse>{color_r} {color_g} {color_b} 1</diffuse>\n                            <specular>{specular * color_r} {specular * color_g} {specular * color_b} 1</specular>\n                            <cast_shadows>true</cast_shadows>\n                        </light>\n                        {(f'\n                        <visual name="{model_name}_visual">\n                            <geometry>\n                                <sphere>\n                                    <radius>{radius}</radius>\n                                </sphere>\n                            </geometry>\n                            <material>\n                                <emissive>{color_r} {color_g} {color_b} 1</emissive>\n                            </material>\n                            <cast_shadows>false</cast_shadows>\n                        </visual>\n                        ' if visual else '')}\n                    </link>\n                </model>\n            </sdf>'

@classmethod
def get_sdf(self, model_name: str, direction: Tuple[float, float, float], visual: bool, radius: float, color_minmax_r: Tuple[float, float], color_minmax_g: Tuple[float, float], color_minmax_b: Tuple[float, float], attenuation_minmax_range: Tuple[float, float], attenuation_minmax_constant: Tuple[float, float], attenuation_minmax_linear: Tuple[float, float], attenuation_minmax_quadratic: Tuple[float, float], specular: float, np_random: RandomState) -> str:
    color_r = np_random.uniform(color_minmax_r[0], color_minmax_r[1])
    color_g = np_random.uniform(color_minmax_g[0], color_minmax_g[1])
    color_b = np_random.uniform(color_minmax_b[0], color_minmax_b[1])
    attenuation_range = np_random.uniform(attenuation_minmax_range[0], attenuation_minmax_range[1])
    attenuation_constant = np_random.uniform(attenuation_minmax_constant[0], attenuation_minmax_constant[1])
    attenuation_linear = np_random.uniform(attenuation_minmax_linear[0], attenuation_minmax_linear[1])
    attenuation_quadratic = np_random.uniform(attenuation_minmax_quadratic[0], attenuation_minmax_quadratic[1])
    return f'<sdf version="1.9">\n                <model name="{model_name}">\n                    <static>true</static>\n                    <link name="{model_name}_link">\n                        <light type="directional" name="{model_name}_light">\n                            <direction>{direction[0]} {direction[1]} {direction[2]}</direction>\n                            <attenuation>\n                                <range>{attenuation_range}</range>\n                                <constant>{attenuation_constant}</constant>\n                                <linear>{attenuation_linear}</linear>\n                                <quadratic>{attenuation_quadratic}</quadratic>\n                            </attenuation>\n                            <diffuse>{color_r} {color_g} {color_b} 1</diffuse>\n                            <specular>{specular * color_r} {specular * color_g} {specular * color_b} 1</specular>\n                            <cast_shadows>true</cast_shadows>\n                        </light>\n                        {(f'\n                        <visual name="{model_name}_visual">\n                            <geometry>\n                                <sphere>\n                                    <radius>{radius}</radius>\n                                </sphere>\n                            </geometry>\n                            <material>\n                                <emissive>{color_r} {color_g} {color_b} 1</emissive>\n                            </material>\n                            <cast_shadows>false</cast_shadows>\n                        </visual>\n                        ' if visual else '')}\n                    </link>\n                </model>\n            </sdf>'

