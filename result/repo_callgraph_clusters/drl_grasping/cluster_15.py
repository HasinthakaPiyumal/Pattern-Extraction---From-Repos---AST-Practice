# Cluster 15

def _setup_model_with_separate_octree_batches_for_stacks(self) -> None:
    self._setup_lr_schedule()
    self.set_random_seed(self.seed)
    if 'separate_networks_for_stacks' in self.policy_kwargs:
        self.replay_buffer = ReplayBuffer(self.buffer_size, self.observation_space, self.action_space, self.device, optimize_memory_usage=self.optimize_memory_usage, separate_networks_for_stacks=self.policy_kwargs['separate_networks_for_stacks'])
    else:
        self.replay_buffer = ReplayBuffer(self.buffer_size, self.observation_space, self.action_space, self.device, optimize_memory_usage=self.optimize_memory_usage)
    self.policy = self.policy_class(self.observation_space, self.action_space, self.lr_schedule, **self.policy_kwargs)
    self.policy = self.policy.to(self.device)
    self._convert_train_freq()

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

def make_actor(self, features_extractor: Optional[BaseFeaturesExtractor]=None) -> Actor:
    actor_kwargs = self._update_features_extractor(self.actor_kwargs, features_extractor)
    return ActorWithoutPreprocessing(**actor_kwargs).to(self.device)

def make_critic(self, features_extractor: Optional[BaseFeaturesExtractor]=None) -> ContinuousCritic:
    critic_kwargs = self._update_features_extractor(self.critic_kwargs, features_extractor)
    return ContinuousCriticWithoutPreprocessing(**critic_kwargs).to(self.device)

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

def make_actor(self, features_extractor: Optional[BaseFeaturesExtractor]=None) -> Actor:
    actor_kwargs = self._update_features_extractor(self.actor_kwargs, features_extractor)
    return ActorWithoutPreprocessing(**actor_kwargs).to(self.device)

def make_critic(self, features_extractor: Optional[BaseFeaturesExtractor]=None) -> ContinuousCritic:
    critic_kwargs = self._update_features_extractor(self.critic_kwargs, features_extractor)
    return ContinuousCriticWithoutPreprocessing(**critic_kwargs).to(self.device)

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

def make_actor(self, features_extractor: Optional[BaseFeaturesExtractor]=None) -> Actor:
    actor_kwargs = self._update_features_extractor(self.actor_kwargs, features_extractor)
    return ActorWithoutPreprocessing(**actor_kwargs).to(self.device)

def make_critic(self, features_extractor: Optional[BaseFeaturesExtractor]=None) -> Critic:
    critic_kwargs = self._update_features_extractor(self.critic_kwargs, features_extractor)
    return CriticWithoutPreprocessing(**critic_kwargs).to(self.device)

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

def make_actor(self, features_extractor: Optional[BaseFeaturesExtractor]=None) -> Actor:
    actor_kwargs = self._update_features_extractor(self.actor_kwargs, features_extractor)
    return ActorWithoutPreprocessing(**actor_kwargs).to(self.device)

def make_critic(self, features_extractor: Optional[BaseFeaturesExtractor]=None) -> Critic:
    critic_kwargs = self._update_features_extractor(self.critic_kwargs, features_extractor)
    return CriticWithoutPreprocessing(**critic_kwargs).to(self.device)

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

def make_actor(self, features_extractor: Optional[BaseFeaturesExtractor]=None) -> Actor:
    actor_kwargs = self._update_features_extractor(self.actor_kwargs, features_extractor)
    return ActorWithoutPreprocessing(**actor_kwargs).to(self.device)

def make_critic(self, features_extractor: Optional[BaseFeaturesExtractor]=None) -> ContinuousCritic:
    critic_kwargs = self._update_features_extractor(self.critic_kwargs, features_extractor)
    return ContinuousWithoutPreprocessing(**critic_kwargs).to(self.device)

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

def make_actor(self, features_extractor: Optional[BaseFeaturesExtractor]=None) -> Actor:
    actor_kwargs = self._update_features_extractor(self.actor_kwargs, features_extractor)
    return ActorWithoutPreprocessing(**actor_kwargs).to(self.device)

def make_critic(self, features_extractor: Optional[BaseFeaturesExtractor]=None) -> ContinuousCritic:
    critic_kwargs = self._update_features_extractor(self.critic_kwargs, features_extractor)
    return ContinuousWithoutPreprocessing(**critic_kwargs).to(self.device)

def preprocess_stacked_octree_batch(observation: th.Tensor, device, separate_batches: bool=True, include_aux_obs: bool=True) -> Dict[str, th.Tensor]:
    if not separate_batches:
        octrees = []
        for octree in observation.reshape(-1, observation.shape[-1]):
            octree_size = np.frombuffer(buffer=octree[-4:], dtype=np.uint32, count=1)
            octrees.append(th.tensor(octree[:octree_size[0]], requires_grad=False))
        octree_batches = ocnn.octree_batch(octrees).to(device)
    else:
        octree_batches = []
        for octree_batch in np.split(observation, observation.shape[1], axis=1):
            octrees = []
            for octree in octree_batch:
                octree_size = np.frombuffer(buffer=octree[-4:], dtype=np.uint32, count=1)
                octrees.append(th.tensor(octree[:octree_size[0]], requires_grad=False))
            octree_batches.append(ocnn.octree_batch(octrees).to(device))
    if include_aux_obs:
        n_aux_obs_f32 = int(np.frombuffer(buffer=observation[0, 0, -8:-4], dtype=np.uint32, count=1))
        aux_obs = th.tensor(np.frombuffer(buffer=observation[:, :, -(4 * n_aux_obs_f32 + 8):-8].reshape(-1), dtype=np.float32, count=n_aux_obs_f32 * observation.shape[0] * observation.shape[1]).reshape(observation.shape[:2] + (n_aux_obs_f32,)), requires_grad=False).to(device)
    else:
        aux_obs = None
    return (octree_batches, aux_obs)

def preprocess_stacked_depth_image_batch(observation: th.Tensor, device, separate_batches: bool=True, image_width=128, image_height=128, include_aux_obs=True) -> Dict[str, th.Tensor]:
    number_of_pixels = image_width * image_height
    if observation.shape[2] >= 4 * number_of_pixels:
        contains_rgb = True
        contains_intensity = False
        num_channels = 4
    elif observation.shape[2] >= 2 * number_of_pixels:
        contains_rgb = False
        contains_intensity = True
        num_channels = 2
    else:
        contains_rgb = False
        contains_intensity = False
        num_channels = 1
    if include_aux_obs:
        n_aux_obs = int(np.round(np.frombuffer(buffer=observation[0, 0, -1], dtype=np.float32, count=1)))
        aux_obs = th.tensor(observation[:, :, -(n_aux_obs + 1):-1].reshape(observation.shape[:2] + (n_aux_obs,)), requires_grad=False).to(device)
    else:
        aux_obs = None
    if not separate_batches:
        image_batches = []
        for image in observation.reshape(-1, observation.shape[-1]):
            if contains_rgb or contains_intensity:
                _depth_image, color_image = np.split(image[:4 * number_of_pixels], [number_of_pixels])
                if contains_intensity:
                    depth_image = np.empty((2 * number_of_pixels,), dtype=_depth_image.dtype)
                    depth_image[0::2] = color_image[:number_of_pixels]
                    depth_image[1::2] = _depth_image
                else:
                    depth_image = np.empty((4 * number_of_pixels,), dtype=_depth_image.dtype)
                    depth_image[0::4] = color_image[0::3]
                    depth_image[1::4] = color_image[1::3]
                    depth_image[2::4] = color_image[2::3]
                    depth_image[3::4] = _depth_image
            else:
                depth_image = image[:number_of_pixels]
            depth_image = depth_image.reshape(-1, num_channels, image_height, image_width)
            image_batches.append(th.tensor(depth_image, requires_grad=False).to(device))
        image_batches = th.stack(image_batches)
        image_batches = image_batches.view(-1, num_channels, image_height, image_width)
    else:
        image_batches = []
        for image_batch in np.split(observation, observation.shape[1], axis=1):
            images = []
            for image in image_batch:
                if contains_rgb or contains_intensity:
                    _depth_image, color_image = np.split(image[:, :4 * number_of_pixels], [number_of_pixels], axis=1)
                    if contains_intensity:
                        depth_image = np.empty((_depth_image.shape[0], 2 * number_of_pixels), dtype=_depth_image.dtype)
                        depth_image[:, 0::2] = color_image
                        depth_image[:, 1::2] = _depth_image
                    else:
                        depth_image = np.empty((_depth_image.shape[0], 4 * number_of_pixels), dtype=_depth_image.dtype)
                        depth_image[:, 0::4] = color_image[:, 0::3]
                        depth_image[:, 1::4] = color_image[:, 1::3]
                        depth_image[:, 2::4] = color_image[:, 2::3]
                        depth_image[:, 3::4] = _depth_image
                else:
                    depth_image = image[:, :number_of_pixels]
                depth_image = depth_image.reshape(-1, image_height, image_width)
                images.append(th.tensor(depth_image, requires_grad=False))
            image_batches.append(th.stack(images).to(device))
    return (image_batches, aux_obs)

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

