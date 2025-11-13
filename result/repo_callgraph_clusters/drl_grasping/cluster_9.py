# Cluster 9

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

def _train_thread(self) -> None:
    self._model.train(gradient_steps=self.gradient_steps, batch_size=self.batch_size)
    self._model_ready = True

def _on_rollout_end(self) -> None:
    if self._model_ready:
        self._model.replay_buffer = deepcopy(self.model.replay_buffer)
        self.model.set_parameters(deepcopy(self._model.get_parameters()))
        self.model.actor = self.model.policy.actor
        if self.num_timesteps >= self._model.learning_starts:
            self.train()

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

def randomize_configured_model(self, model_path, min_scale=0.05, max_scale=0.25, min_mass=0.1, max_mass=3.0, min_friction=0.75, max_friction=1.5):
    configured_sdf_path = self.get_configured_sdf_path(model_path)
    sdf = parse_sdf(configured_sdf_path)
    for model in sdf.models:
        for link in model.links:
            self.randomize_scale(model_path, link, min_scale=min_scale, max_scale=max_scale)
            self.randomize_inertial(link, min_mass=min_mass, max_mass=max_mass)
            self.randomize_friction(link, min_friction=min_friction, max_friction=max_friction)
    sdf.export_xml(configured_sdf_path)

def is_configured(self, model_path) -> bool:
    return os.path.isfile(self.get_configured_sdf_path(model_path))

