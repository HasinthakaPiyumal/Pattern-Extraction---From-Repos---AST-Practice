# Cluster 30

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

def extract_features(self, obs: th.Tensor) -> th.Tensor:
    """
        Preprocess the observation if needed and extract features.
        Overridden to skip pre-processing (for some reason it converts tensor to Float)

        :param obs:
        :return:
        """
    assert self.features_extractor is not None, 'No features extractor was set'
    return self.features_extractor(obs)

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

def extract_features(self, obs: th.Tensor) -> th.Tensor:
    """
        Preprocess the observation if needed and extract features.
        Overridden to skip pre-processing (for some reason it converts tensor to Float)

        :param obs:
        :return:
        """
    assert self.features_extractor is not None, 'No features extractor was set'
    return self.features_extractor(obs)

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

def extract_features(self, obs: th.Tensor) -> th.Tensor:
    """
        Preprocess the observation if needed and extract features.
        Overridden to skip pre-processing (for some reason it converts tensor to Float)

        :param obs:
        :return:
        """
    assert self.features_extractor is not None, 'No features extractor was set'
    return self.features_extractor(obs)

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

def extract_features(self, obs: th.Tensor) -> th.Tensor:
    """
        Preprocess the observation if needed and extract features.
        Overridden to skip pre-processing (for some reason it converts tensor to Float)

        :param obs:
        :return:
        """
    assert self.features_extractor is not None, 'No features extractor was set'
    return self.features_extractor(obs)

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

def extract_features(self, obs: th.Tensor) -> th.Tensor:
    """
        Preprocess the observation if needed and extract features.
        Overridden to skip pre-processing (for some reason it converts tensor to Float)

        :param obs:
        :return:
        """
    assert self.features_extractor is not None, 'No features extractor was set'
    return self.features_extractor(obs)

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

def extract_features(self, obs: th.Tensor) -> th.Tensor:
    """
        Preprocess the observation if needed and extract features.
        Overridden to skip pre-processing (for some reason it converts tensor to Float)

        :param obs:
        :return:
        """
    assert self.features_extractor is not None, 'No features extractor was set'
    return self.features_extractor(obs)

