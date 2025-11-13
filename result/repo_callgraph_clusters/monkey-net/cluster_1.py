# Cluster 1

class GeneratorFullModel(torch.nn.Module):
    """
    Merge all generator related updates into single model for better multi-gpu usage
    """

    def __init__(self, kp_extractor, generator, discriminator, train_params):
        super(GeneratorFullModel, self).__init__()
        self.kp_extractor = kp_extractor
        self.generator = generator
        self.discriminator = discriminator
        self.train_params = train_params

    def forward(self, x):
        kp_joined = self.kp_extractor(torch.cat([x['source'], x['video']], dim=2))
        generated = self.generator(x['source'], **split_kp(kp_joined, self.train_params['detach_kp_generator']))
        video_prediction = generated['video_prediction']
        video_deformed = generated['video_deformed']
        kp_dict = split_kp(kp_joined, False)
        discriminator_maps_generated = self.discriminator(video_prediction, **kp_dict)
        discriminator_maps_real = self.discriminator(x['video'], **kp_dict)
        generated.update(kp_dict)
        losses = generator_loss(discriminator_maps_generated=discriminator_maps_generated, discriminator_maps_real=discriminator_maps_real, video_deformed=video_deformed, loss_weights=self.train_params['loss_weights'])
        return tuple(losses) + (generated, kp_joined)

def __init__(self, kp_extractor, generator, discriminator, train_params):
    super(GeneratorFullModel, self).__init__()
    self.kp_extractor = kp_extractor
    self.generator = generator
    self.discriminator = discriminator
    self.train_params = train_params

class DiscriminatorFullModel(torch.nn.Module):
    """
    Merge all generator related updates into single model for better multi-gpu usage
    """

    def __init__(self, kp_extractor, generator, discriminator, train_params):
        super(DiscriminatorFullModel, self).__init__()
        self.kp_extractor = kp_extractor
        self.generator = generator
        self.discriminator = discriminator
        self.train_params = train_params

    def forward(self, x, kp_joined, generated):
        kp_dict = split_kp(kp_joined, self.train_params['detach_kp_discriminator'])
        discriminator_maps_generated = self.discriminator(generated['video_prediction'].detach(), **kp_dict)
        discriminator_maps_real = self.discriminator(x['video'], **kp_dict)
        loss = discriminator_loss(discriminator_maps_generated=discriminator_maps_generated, discriminator_maps_real=discriminator_maps_real, loss_weights=self.train_params['loss_weights'])
        return loss

def __init__(self, kp_extractor, generator, discriminator, train_params):
    super(DiscriminatorFullModel, self).__init__()
    self.kp_extractor = kp_extractor
    self.generator = generator
    self.discriminator = discriminator
    self.train_params = train_params

def generate(generator, appearance_image, kp_appearance, kp_video):
    out = {'video_prediction': [], 'video_deformed': []}
    for i in range(kp_video['mean'].shape[1]):
        kp_target = {k: v[:, i:i + 1] for k, v in kp_video.items()}
        kp_dict_part = {'kp_driving': kp_target, 'kp_source': kp_appearance}
        out_part = generator(appearance_image, **kp_dict_part)
        out['video_prediction'].append(out_part['video_prediction'])
        out['video_deformed'].append(out_part['video_deformed'])
    out['video_prediction'] = torch.cat(out['video_prediction'], dim=2)
    out['video_deformed'] = torch.cat(out['video_deformed'], dim=2)
    out['kp_driving'] = kp_video
    out['kp_source'] = kp_appearance
    return out

class Logger:

    def __init__(self, log_dir, log_file_name='log.txt', log_freq_iter=100, cpk_freq_epoch=100, zfill_num=8, visualizer_params=None):
        self.loss_list = []
        self.cpk_dir = log_dir
        self.visualizations_dir = os.path.join(log_dir, 'train-vis')
        if not os.path.exists(self.visualizations_dir):
            os.makedirs(self.visualizations_dir)
        self.log_file = open(os.path.join(log_dir, log_file_name), 'a')
        self.log_freq = log_freq_iter
        self.cpk_freq = cpk_freq_epoch
        self.zfill_num = zfill_num
        self.visualizer = Visualizer(**visualizer_params)
        self.epoch = 0
        self.it = 0

    def log_scores(self, loss_names):
        loss_mean = np.array(self.loss_list).mean(axis=0)
        loss_string = '; '.join(['%s - %.5f' % (name, value) for name, value in zip(loss_names, loss_mean)])
        loss_string = str(self.it).zfill(self.zfill_num) + ') ' + loss_string
        print(loss_string, file=self.log_file)
        self.loss_list = []
        self.log_file.flush()

    def visualize_rec(self, inp, out):
        image = self.visualizer.visualize_reconstruction(inp, out)
        imageio.mimsave(os.path.join(self.visualizations_dir, '%s-rec.gif' % str(self.it).zfill(self.zfill_num)), image)

    def save_cpk(self):
        cpk = {k: v.state_dict() for k, v in self.models.items()}
        cpk['epoch'] = self.epoch
        cpk['it'] = self.it
        torch.save(cpk, os.path.join(self.cpk_dir, '%s-checkpoint.pth.tar' % str(self.epoch).zfill(self.zfill_num)))

    @staticmethod
    def load_cpk(checkpoint_path, generator=None, discriminator=None, kp_detector=None, optimizer_generator=None, optimizer_discriminator=None, optimizer_kp_detector=None):
        checkpoint = torch.load(checkpoint_path)
        if generator is not None:
            generator.load_state_dict(checkpoint['generator'])
        if kp_detector is not None:
            kp_detector.load_state_dict(checkpoint['kp_detector'])
        if discriminator is not None:
            discriminator.load_state_dict(checkpoint['discriminator'])
        if optimizer_generator is not None:
            optimizer_generator.load_state_dict(checkpoint['optimizer_generator'])
        if optimizer_discriminator is not None:
            optimizer_discriminator.load_state_dict(checkpoint['optimizer_discriminator'])
        if optimizer_kp_detector is not None:
            optimizer_kp_detector.load_state_dict(checkpoint['optimizer_kp_detector'])
        return (checkpoint['epoch'], checkpoint['it'])

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if 'models' in self.__dict__:
            self.save_cpk()
        self.log_file.close()

    def log_iter(self, it, names, values, inp, out):
        self.it = it
        self.names = names
        self.loss_list.append(values)
        if it % self.log_freq == 0:
            self.log_scores(self.names)
            self.visualize_rec(inp, out)

    def log_epoch(self, epoch, models):
        self.epoch = epoch
        self.models = models
        if epoch % self.cpk_freq == 0:
            self.save_cpk()

def log_iter(self, it, names, values, inp, out):
    self.it = it
    self.names = names
    self.loss_list.append(values)
    if it % self.log_freq == 0:
        self.log_scores(self.names)
        self.visualize_rec(inp, out)

class SlavePipe(_SlavePipeBase):
    """Pipe for master-slave communication."""

    def run_slave(self, msg):
        self.queue.put((self.identifier, msg))
        ret = self.result.get()
        self.queue.put(True)
        return ret

def run_slave(self, msg):
    self.queue.put((self.identifier, msg))
    ret = self.result.get()
    self.queue.put(True)
    return ret

class SyncMaster(object):
    """An abstract `SyncMaster` object.

    - During the replication, as the data parallel will trigger an callback of each module, all slave devices should
    call `register(id)` and obtain an `SlavePipe` to communicate with the master.
    - During the forward pass, master device invokes `run_master`, all messages from slave devices will be collected,
    and passed to a registered callback.
    - After receiving the messages, the master device should gather the information and determine to message passed
    back to each slave devices.
    """

    def __init__(self, master_callback):
        """

        Args:
            master_callback: a callback to be invoked after having collected messages from slave devices.
        """
        self._master_callback = master_callback
        self._queue = queue.Queue()
        self._registry = collections.OrderedDict()
        self._activated = False

    def __getstate__(self):
        return {'master_callback': self._master_callback}

    def __setstate__(self, state):
        self.__init__(state['master_callback'])

    def register_slave(self, identifier):
        """
        Register an slave device.

        Args:
            identifier: an identifier, usually is the device id.

        Returns: a `SlavePipe` object which can be used to communicate with the master device.

        """
        if self._activated:
            assert self._queue.empty(), 'Queue is not clean before next initialization.'
            self._activated = False
            self._registry.clear()
        future = FutureResult()
        self._registry[identifier] = _MasterRegistry(future)
        return SlavePipe(identifier, self._queue, future)

    def run_master(self, master_msg):
        """
        Main entry for the master device in each forward pass.
        The messages were first collected from each devices (including the master device), and then
        an callback will be invoked to compute the message to be sent back to each devices
        (including the master device).

        Args:
            master_msg: the message that the master want to send to itself. This will be placed as the first
            message when calling `master_callback`. For detailed usage, see `_SynchronizedBatchNorm` for an example.

        Returns: the message to be sent back to the master device.

        """
        self._activated = True
        intermediates = [(0, master_msg)]
        for i in range(self.nr_slaves):
            intermediates.append(self._queue.get())
        results = self._master_callback(intermediates)
        assert results[0][0] == 0, 'The first result should belongs to the master.'
        for i, res in results:
            if i == 0:
                continue
            self._registry[i].result.put(res)
        for i in range(self.nr_slaves):
            assert self._queue.get() is True
        return results[0][1]

    @property
    def nr_slaves(self):
        return len(self._registry)

def __setstate__(self, state):
    self.__init__(state['master_callback'])

def run_master(self, master_msg):
    """
        Main entry for the master device in each forward pass.
        The messages were first collected from each devices (including the master device), and then
        an callback will be invoked to compute the message to be sent back to each devices
        (including the master device).

        Args:
            master_msg: the message that the master want to send to itself. This will be placed as the first
            message when calling `master_callback`. For detailed usage, see `_SynchronizedBatchNorm` for an example.

        Returns: the message to be sent back to the master device.

        """
    self._activated = True
    intermediates = [(0, master_msg)]
    for i in range(self.nr_slaves):
        intermediates.append(self._queue.get())
    results = self._master_callback(intermediates)
    assert results[0][0] == 0, 'The first result should belongs to the master.'
    for i, res in results:
        if i == 0:
            continue
        self._registry[i].result.put(res)
    for i in range(self.nr_slaves):
        assert self._queue.get() is True
    return results[0][1]

class _SynchronizedBatchNorm(_BatchNorm):

    def __init__(self, num_features, eps=1e-05, momentum=0.1, affine=True):
        super(_SynchronizedBatchNorm, self).__init__(num_features, eps=eps, momentum=momentum, affine=affine)
        self._sync_master = SyncMaster(self._data_parallel_master)
        self._is_parallel = False
        self._parallel_id = None
        self._slave_pipe = None

    def forward(self, input):
        if not (self._is_parallel and self.training):
            return F.batch_norm(input, self.running_mean, self.running_var, self.weight, self.bias, self.training, self.momentum, self.eps)
        input_shape = input.size()
        input = input.view(input.size(0), self.num_features, -1)
        sum_size = input.size(0) * input.size(2)
        input_sum = _sum_ft(input)
        input_ssum = _sum_ft(input ** 2)
        if self._parallel_id == 0:
            mean, inv_std = self._sync_master.run_master(_ChildMessage(input_sum, input_ssum, sum_size))
        else:
            mean, inv_std = self._slave_pipe.run_slave(_ChildMessage(input_sum, input_ssum, sum_size))
        if self.affine:
            output = (input - _unsqueeze_ft(mean)) * _unsqueeze_ft(inv_std * self.weight) + _unsqueeze_ft(self.bias)
        else:
            output = (input - _unsqueeze_ft(mean)) * _unsqueeze_ft(inv_std)
        return output.view(input_shape)

    def __data_parallel_replicate__(self, ctx, copy_id):
        self._is_parallel = True
        self._parallel_id = copy_id
        if self._parallel_id == 0:
            ctx.sync_master = self._sync_master
        else:
            self._slave_pipe = ctx.sync_master.register_slave(copy_id)

    def _data_parallel_master(self, intermediates):
        """Reduce the sum and square-sum, compute the statistics, and broadcast it."""
        intermediates = sorted(intermediates, key=lambda i: i[1].sum.get_device())
        to_reduce = [i[1][:2] for i in intermediates]
        to_reduce = [j for i in to_reduce for j in i]
        target_gpus = [i[1].sum.get_device() for i in intermediates]
        sum_size = sum([i[1].sum_size for i in intermediates])
        sum_, ssum = ReduceAddCoalesced.apply(target_gpus[0], 2, *to_reduce)
        mean, inv_std = self._compute_mean_std(sum_, ssum, sum_size)
        broadcasted = Broadcast.apply(target_gpus, mean, inv_std)
        outputs = []
        for i, rec in enumerate(intermediates):
            outputs.append((rec[0], _MasterMessage(*broadcasted[i * 2:i * 2 + 2])))
        return outputs

    def _compute_mean_std(self, sum_, ssum, size):
        """Compute the mean and standard-deviation with sum and square-sum. This method
        also maintains the moving average on the master device."""
        assert size > 1, 'BatchNorm computes unbiased standard-deviation, which requires size > 1.'
        mean = sum_ / size
        sumvar = ssum - sum_ * mean
        unbias_var = sumvar / (size - 1)
        bias_var = sumvar / size
        self.running_mean = (1 - self.momentum) * self.running_mean + self.momentum * mean.data
        self.running_var = (1 - self.momentum) * self.running_var + self.momentum * unbias_var.data
        return (mean, bias_var.clamp(self.eps) ** (-0.5))

def __init__(self, num_features, eps=1e-05, momentum=0.1, affine=True):
    super(_SynchronizedBatchNorm, self).__init__(num_features, eps=eps, momentum=momentum, affine=affine)
    self._sync_master = SyncMaster(self._data_parallel_master)
    self._is_parallel = False
    self._parallel_id = None
    self._slave_pipe = None

class DenseMotionModule(nn.Module):
    """
    Module that predicting a dense optical flow only from the displacement of a keypoints
    and the appearance of the first frame
    """

    def __init__(self, block_expansion, num_blocks, max_features, mask_embedding_params, num_kp, num_channels, kp_variance, use_correction, use_mask, bg_init=2, num_group_blocks=0, scale_factor=1):
        super(DenseMotionModule, self).__init__()
        self.mask_embedding = MovementEmbeddingModule(num_kp=num_kp, kp_variance=kp_variance, num_channels=num_channels, add_bg_feature_map=True, **mask_embedding_params)
        self.difference_embedding = MovementEmbeddingModule(num_kp=num_kp, kp_variance=kp_variance, num_channels=num_channels, add_bg_feature_map=True, use_difference=True, use_heatmap=False, use_deformed_source_image=False)
        group_blocks = []
        for i in range(num_group_blocks):
            group_blocks.append(SameBlock3D(self.mask_embedding.out_channels, self.mask_embedding.out_channels, groups=num_kp + 1, kernel_size=(1, 1, 1), padding=(0, 0, 0)))
        self.group_blocks = nn.ModuleList(group_blocks)
        self.hourglass = Hourglass(block_expansion=block_expansion, in_features=self.mask_embedding.out_channels, out_features=(num_kp + 1) * use_mask + 2 * use_correction, max_features=max_features, num_blocks=num_blocks)
        self.hourglass.decoder.conv.weight.data.zero_()
        bias_init = ([bg_init] + [0] * num_kp) * use_mask + [0, 0] * use_correction
        self.hourglass.decoder.conv.bias.data.copy_(torch.tensor(bias_init, dtype=torch.float))
        self.num_kp = num_kp
        self.use_correction = use_correction
        self.use_mask = use_mask
        self.scale_factor = scale_factor

    def forward(self, source_image, kp_driving, kp_source):
        if self.scale_factor != 1:
            source_image = F.interpolate(source_image, scale_factor=(1, self.scale_factor, self.scale_factor))
        prediction = self.mask_embedding(source_image, kp_driving, kp_source)
        for block in self.group_blocks:
            prediction = block(prediction)
            prediction = F.leaky_relu(prediction, 0.2)
        prediction = self.hourglass(prediction)
        bs, _, d, h, w = prediction.shape
        if self.use_mask:
            mask = prediction[:, :self.num_kp + 1]
            mask = F.softmax(mask, dim=1)
            mask = mask.unsqueeze(2)
            difference_embedding = self.difference_embedding(source_image, kp_driving, kp_source)
            difference_embedding = difference_embedding.view(bs, self.num_kp + 1, 2, d, h, w)
            deformations_relative = (difference_embedding * mask).sum(dim=1)
        else:
            deformations_relative = 0
        if self.use_correction:
            correction = prediction[:, -2:]
        else:
            correction = 0
        deformations_relative = deformations_relative + correction
        deformations_relative = deformations_relative.permute(0, 2, 3, 4, 1)
        coordinate_grid = make_coordinate_grid((h, w), type=deformations_relative.type())
        coordinate_grid = coordinate_grid.view(1, 1, h, w, 2)
        deformation = deformations_relative + coordinate_grid
        z_coordinate = torch.zeros(deformation.shape[:-1] + (1,)).type(deformation.type())
        return torch.cat([deformation, z_coordinate], dim=-1)

def __init__(self, block_expansion, num_blocks, max_features, mask_embedding_params, num_kp, num_channels, kp_variance, use_correction, use_mask, bg_init=2, num_group_blocks=0, scale_factor=1):
    super(DenseMotionModule, self).__init__()
    self.mask_embedding = MovementEmbeddingModule(num_kp=num_kp, kp_variance=kp_variance, num_channels=num_channels, add_bg_feature_map=True, **mask_embedding_params)
    self.difference_embedding = MovementEmbeddingModule(num_kp=num_kp, kp_variance=kp_variance, num_channels=num_channels, add_bg_feature_map=True, use_difference=True, use_heatmap=False, use_deformed_source_image=False)
    group_blocks = []
    for i in range(num_group_blocks):
        group_blocks.append(SameBlock3D(self.mask_embedding.out_channels, self.mask_embedding.out_channels, groups=num_kp + 1, kernel_size=(1, 1, 1), padding=(0, 0, 0)))
    self.group_blocks = nn.ModuleList(group_blocks)
    self.hourglass = Hourglass(block_expansion=block_expansion, in_features=self.mask_embedding.out_channels, out_features=(num_kp + 1) * use_mask + 2 * use_correction, max_features=max_features, num_blocks=num_blocks)
    self.hourglass.decoder.conv.weight.data.zero_()
    bias_init = ([bg_init] + [0] * num_kp) * use_mask + [0, 0] * use_correction
    self.hourglass.decoder.conv.bias.data.copy_(torch.tensor(bias_init, dtype=torch.float))
    self.num_kp = num_kp
    self.use_correction = use_correction
    self.use_mask = use_mask
    self.scale_factor = scale_factor

class PredictionModule(nn.Module):
    """
    RNN for predicting kp movement
    """

    def __init__(self, num_kp=10, kp_variance=0.01, num_features=1024, num_layers=1, dropout=0.5):
        super(PredictionModule, self).__init__()
        input_size = num_kp * (2 + 4 * (kp_variance == 'matrix'))
        self.rnn = nn.GRU(input_size=input_size, hidden_size=num_features, num_layers=num_layers, dropout=dropout, batch_first=True)
        self.linear = nn.Linear(num_features, input_size)

    def net(self, input, h=None):
        output, h = self.rnn(input, h)
        init_shape = output.shape
        output = output.contiguous().view(-1, output.shape[-1])
        output = self.linear(output)
        return (output.view(init_shape[0], init_shape[1], output.shape[-1]), h)

    def forward(self, kp_batch):
        bs, d, num_kp, _ = kp_batch['mean'].shape
        inputs = [kp_batch['mean'].contiguous().view(bs, d, -1)]
        if 'var' in kp_batch:
            inputs.append(kp_batch['var'].contiguous().view(bs, d, -1))
        input = torch.cat(inputs, dim=-1)
        output, h = self.net(input)
        output = output.view(bs, d, num_kp, -1)
        mean = torch.tanh(output[:, :, :, :2])
        kp_array = {'mean': mean}
        if 'var' in kp_batch:
            var = output[:, :, :, 2:]
            var = var.view(bs, d, num_kp, 2, 2)
            var = torch.matmul(var.permute(0, 1, 2, 4, 3), var)
            kp_array['var'] = var
        return kp_array

def __init__(self, num_kp=10, kp_variance=0.01, num_features=1024, num_layers=1, dropout=0.5):
    super(PredictionModule, self).__init__()
    input_size = num_kp * (2 + 4 * (kp_variance == 'matrix'))
    self.rnn = nn.GRU(input_size=input_size, hidden_size=num_features, num_layers=num_layers, dropout=dropout, batch_first=True)
    self.linear = nn.Linear(num_features, input_size)

class KPDetector(nn.Module):
    """
    Detecting a keypoints. Return keypoint position and variance.
    """

    def __init__(self, block_expansion, num_kp, num_channels, max_features, num_blocks, temperature, kp_variance, scale_factor=1, clip_variance=None):
        super(KPDetector, self).__init__()
        self.predictor = Hourglass(block_expansion, in_features=num_channels, out_features=num_kp, max_features=max_features, num_blocks=num_blocks)
        self.temperature = temperature
        self.kp_variance = kp_variance
        self.scale_factor = scale_factor
        self.clip_variance = clip_variance

    def forward(self, x):
        if self.scale_factor != 1:
            x = F.interpolate(x, scale_factor=(1, self.scale_factor, self.scale_factor))
        heatmap = self.predictor(x)
        final_shape = heatmap.shape
        heatmap = heatmap.view(final_shape[0], final_shape[1], final_shape[2], -1)
        heatmap = F.softmax(heatmap / self.temperature, dim=3)
        heatmap = heatmap.view(*final_shape)
        out = gaussian2kp(heatmap, self.kp_variance, self.clip_variance)
        return out

def __init__(self, block_expansion, num_kp, num_channels, max_features, num_blocks, temperature, kp_variance, scale_factor=1, clip_variance=None):
    super(KPDetector, self).__init__()
    self.predictor = Hourglass(block_expansion, in_features=num_channels, out_features=num_kp, max_features=max_features, num_blocks=num_blocks)
    self.temperature = temperature
    self.kp_variance = kp_variance
    self.scale_factor = scale_factor
    self.clip_variance = clip_variance

class DownBlock3D(nn.Module):
    """
    Simple block for processing video (encoder).
    """

    def __init__(self, in_features, out_features, norm=False, kernel_size=4):
        super(DownBlock3D, self).__init__()
        ka = kernel_size // 2
        kb = ka - 1 if kernel_size % 2 == 0 else ka
        self.conv = nn.Conv3d(in_channels=in_features, out_channels=out_features, kernel_size=(1, kernel_size, kernel_size))
        if norm:
            self.norm = nn.InstanceNorm3d(out_features, affine=True)
        else:
            self.norm = None

    def forward(self, x):
        out = x
        out = self.conv(out)
        if self.norm:
            out = self.norm(out)
        out = F.leaky_relu(out, 0.2)
        out = F.avg_pool3d(out, (1, 2, 2))
        return out

def __init__(self, in_features, out_features, norm=False, kernel_size=4):
    super(DownBlock3D, self).__init__()
    ka = kernel_size // 2
    kb = ka - 1 if kernel_size % 2 == 0 else ka
    self.conv = nn.Conv3d(in_channels=in_features, out_channels=out_features, kernel_size=(1, kernel_size, kernel_size))
    if norm:
        self.norm = nn.InstanceNorm3d(out_features, affine=True)
    else:
        self.norm = None

class Discriminator(nn.Module):
    """
    Discriminator similar to Pix2Pix
    """

    def __init__(self, num_channels=3, num_kp=10, kp_variance=0.01, scale_factor=1, block_expansion=64, num_blocks=4, max_features=512, kp_embedding_params=None):
        super(Discriminator, self).__init__()
        if kp_embedding_params is not None:
            self.kp_embedding = MovementEmbeddingModule(num_kp=num_kp, kp_variance=kp_variance, num_channels=num_channels, **kp_embedding_params)
            embedding_channels = self.kp_embedding.out_channels
        else:
            self.kp_embedding = None
            embedding_channels = 0
        down_blocks = []
        for i in range(num_blocks):
            down_blocks.append(DownBlock3D(num_channels + embedding_channels if i == 0 else min(max_features, block_expansion * 2 ** i), min(max_features, block_expansion * 2 ** (i + 1)), norm=i != 0, kernel_size=4))
        self.down_blocks = nn.ModuleList(down_blocks)
        self.conv = nn.Conv3d(self.down_blocks[-1].conv.out_channels, out_channels=1, kernel_size=1)
        self.scale_factor = scale_factor

    def forward(self, x, kp_driving, kp_source):
        out_maps = [x]
        if self.scale_factor != 1:
            x = F.interpolate(x, scale_factor=(1, self.scale_factor, self.scale_factor))
        if self.kp_embedding:
            heatmap = self.kp_embedding(x, kp_driving, kp_source)
            out = torch.cat([x, heatmap], dim=1)
        else:
            out = x
        for down_block in self.down_blocks:
            out_maps.append(down_block(out))
            out = out_maps[-1]
        out = self.conv(out)
        out_maps.append(out)
        return out_maps

def __init__(self, num_channels=3, num_kp=10, kp_variance=0.01, scale_factor=1, block_expansion=64, num_blocks=4, max_features=512, kp_embedding_params=None):
    super(Discriminator, self).__init__()
    if kp_embedding_params is not None:
        self.kp_embedding = MovementEmbeddingModule(num_kp=num_kp, kp_variance=kp_variance, num_channels=num_channels, **kp_embedding_params)
        embedding_channels = self.kp_embedding.out_channels
    else:
        self.kp_embedding = None
        embedding_channels = 0
    down_blocks = []
    for i in range(num_blocks):
        down_blocks.append(DownBlock3D(num_channels + embedding_channels if i == 0 else min(max_features, block_expansion * 2 ** i), min(max_features, block_expansion * 2 ** (i + 1)), norm=i != 0, kernel_size=4))
    self.down_blocks = nn.ModuleList(down_blocks)
    self.conv = nn.Conv3d(self.down_blocks[-1].conv.out_channels, out_channels=1, kernel_size=1)
    self.scale_factor = scale_factor

class MovementEmbeddingModule(nn.Module):
    """
    Produce a keypoint representation that will be further used by other modules
    """

    def __init__(self, num_kp, kp_variance, num_channels, use_deformed_source_image=False, use_difference=False, use_heatmap=True, add_bg_feature_map=False, heatmap_type='gaussian', norm_const='sum', scale_factor=1):
        super(MovementEmbeddingModule, self).__init__()
        assert heatmap_type in ['gaussian', 'difference']
        assert int(use_heatmap) + int(use_deformed_source_image) + int(use_difference) >= 1
        self.out_channels = (1 * use_heatmap + 2 * use_difference + num_channels * use_deformed_source_image) * (num_kp + add_bg_feature_map)
        self.kp_variance = kp_variance
        self.heatmap_type = heatmap_type
        self.use_difference = use_difference
        self.use_deformed_source_image = use_deformed_source_image
        self.use_heatmap = use_heatmap
        self.add_bg_feature_map = add_bg_feature_map
        self.norm_const = norm_const
        self.scale_factor = scale_factor

    def normalize_heatmap(self, heatmap):
        if self.norm_const == 'sum':
            heatmap_shape = heatmap.shape
            heatmap = heatmap.view(heatmap_shape[0], heatmap_shape[1], heatmap_shape[2], -1)
            heatmap = heatmap / heatmap.sum(dim=3, keepdim=True)
            return heatmap.view(*heatmap_shape)
        else:
            return heatmap / self.norm_const

    def forward(self, source_image, kp_driving, kp_source):
        if self.scale_factor != 1:
            source_image = F.interpolate(source_image, scale_factor=(1, self.scale_factor, self.scale_factor))
        spatial_size = source_image.shape[3:]
        bs, _, _, h, w = source_image.shape
        _, d, num_kp, _ = kp_driving['mean'].shape
        inputs = []
        if self.use_heatmap:
            heatmap = self.normalize_heatmap(kp2gaussian(kp_driving, spatial_size=spatial_size, kp_variance=self.kp_variance))
            if self.heatmap_type == 'difference':
                heatmap_appearance = self.normalize_heatmap(kp2gaussian(kp_source, spatial_size=spatial_size, kp_variance=self.kp_variance))
                heatmap = heatmap - heatmap_appearance
            if self.add_bg_feature_map:
                zeros = torch.zeros(bs, d, 1, h, w).type(heatmap.type())
                heatmap = torch.cat([zeros, heatmap], dim=2)
            heatmap = heatmap.unsqueeze(3)
            inputs.append(heatmap)
        num_kp += self.add_bg_feature_map
        if self.use_difference or self.use_deformed_source_image:
            kp_video_diff = kp_source['mean'] - kp_driving['mean']
            if self.add_bg_feature_map:
                zeros = torch.zeros(bs, d, 1, 2).type(kp_video_diff.type())
                kp_video_diff = torch.cat([zeros, kp_video_diff], dim=2)
            kp_video_diff = kp_video_diff.view((bs, d, num_kp, 2, 1, 1)).repeat(1, 1, 1, 1, h, w)
        if self.use_difference:
            inputs.append(kp_video_diff)
        if self.use_deformed_source_image:
            appearance_repeat = source_image.unsqueeze(1).unsqueeze(1).repeat(1, d, num_kp, 1, 1, 1, 1)
            appearance_repeat = appearance_repeat.view(bs * d * num_kp, -1, h, w)
            deformation_approx = kp_video_diff.view((bs * d * num_kp, -1, h, w)).permute(0, 2, 3, 1)
            coordinate_grid = make_coordinate_grid((h, w), type=deformation_approx.type())
            coordinate_grid = coordinate_grid.view(1, h, w, 2)
            deformation_approx = coordinate_grid + deformation_approx
            appearance_approx_deform = F.grid_sample(appearance_repeat, deformation_approx)
            appearance_approx_deform = appearance_approx_deform.view((bs, d, num_kp, -1, h, w))
            inputs.append(appearance_approx_deform)
        movement_encoding = torch.cat(inputs, dim=3)
        movement_encoding = movement_encoding.view(bs, d, -1, h, w)
        return movement_encoding.permute(0, 2, 1, 3, 4)

def __init__(self, num_kp, kp_variance, num_channels, use_deformed_source_image=False, use_difference=False, use_heatmap=True, add_bg_feature_map=False, heatmap_type='gaussian', norm_const='sum', scale_factor=1):
    super(MovementEmbeddingModule, self).__init__()
    assert heatmap_type in ['gaussian', 'difference']
    assert int(use_heatmap) + int(use_deformed_source_image) + int(use_difference) >= 1
    self.out_channels = (1 * use_heatmap + 2 * use_difference + num_channels * use_deformed_source_image) * (num_kp + add_bg_feature_map)
    self.kp_variance = kp_variance
    self.heatmap_type = heatmap_type
    self.use_difference = use_difference
    self.use_deformed_source_image = use_deformed_source_image
    self.use_heatmap = use_heatmap
    self.add_bg_feature_map = add_bg_feature_map
    self.norm_const = norm_const
    self.scale_factor = scale_factor

class ResBlock3D(nn.Module):
    """
    Res block, preserve spatial resolution.
    """

    def __init__(self, in_features, kernel_size, padding):
        super(ResBlock3D, self).__init__()
        self.conv1 = nn.Conv3d(in_channels=in_features, out_channels=in_features, kernel_size=kernel_size, padding=padding)
        self.conv2 = nn.Conv3d(in_channels=in_features, out_channels=in_features, kernel_size=kernel_size, padding=padding)
        self.norm1 = BatchNorm3d(in_features, affine=True)
        self.norm2 = BatchNorm3d(in_features, affine=True)

    def forward(self, x):
        out = x
        out = self.norm1(x)
        out = F.relu(out)
        out = self.conv1(out)
        out = self.norm2(out)
        out = F.relu(out)
        out = self.conv2(out)
        out += x
        return out

def __init__(self, in_features, kernel_size, padding):
    super(ResBlock3D, self).__init__()
    self.conv1 = nn.Conv3d(in_channels=in_features, out_channels=in_features, kernel_size=kernel_size, padding=padding)
    self.conv2 = nn.Conv3d(in_channels=in_features, out_channels=in_features, kernel_size=kernel_size, padding=padding)
    self.norm1 = BatchNorm3d(in_features, affine=True)
    self.norm2 = BatchNorm3d(in_features, affine=True)

class UpBlock3D(nn.Module):
    """
    Simple block for processing video (decoder).
    """

    def __init__(self, in_features, out_features, kernel_size=3, padding=1):
        super(UpBlock3D, self).__init__()
        self.conv = nn.Conv3d(in_channels=in_features, out_channels=out_features, kernel_size=kernel_size, padding=padding)
        self.norm = BatchNorm3d(out_features, affine=True)

    def forward(self, x):
        out = F.interpolate(x, scale_factor=(1, 2, 2))
        out = self.conv(out)
        out = self.norm(out)
        out = F.relu(out)
        return out

def __init__(self, in_features, out_features, kernel_size=3, padding=1):
    super(UpBlock3D, self).__init__()
    self.conv = nn.Conv3d(in_channels=in_features, out_channels=out_features, kernel_size=kernel_size, padding=padding)
    self.norm = BatchNorm3d(out_features, affine=True)

class DownBlock3D(nn.Module):
    """
    Simple block for processing video (encoder).
    """

    def __init__(self, in_features, out_features, kernel_size=3, padding=1):
        super(DownBlock3D, self).__init__()
        self.conv = nn.Conv3d(in_channels=in_features, out_channels=out_features, kernel_size=kernel_size, padding=padding)
        self.norm = BatchNorm3d(out_features, affine=True)
        self.pool = nn.AvgPool3d(kernel_size=(1, 2, 2))

    def forward(self, x):
        out = self.conv(x)
        out = self.norm(out)
        out = F.relu(out)
        out = self.pool(out)
        return out

def __init__(self, in_features, out_features, kernel_size=3, padding=1):
    super(DownBlock3D, self).__init__()
    self.conv = nn.Conv3d(in_channels=in_features, out_channels=out_features, kernel_size=kernel_size, padding=padding)
    self.norm = BatchNorm3d(out_features, affine=True)
    self.pool = nn.AvgPool3d(kernel_size=(1, 2, 2))

class SameBlock3D(nn.Module):
    """
    Simple block with group convolution.
    """

    def __init__(self, in_features, out_features, groups=None, kernel_size=3, padding=1):
        super(SameBlock3D, self).__init__()
        self.conv = nn.Conv3d(in_channels=in_features, out_channels=out_features, kernel_size=kernel_size, padding=padding, groups=groups)
        self.norm = BatchNorm3d(out_features, affine=True)

    def forward(self, x):
        out = self.conv(x)
        out = self.norm(out)
        out = F.relu(out)
        return out

def __init__(self, in_features, out_features, groups=None, kernel_size=3, padding=1):
    super(SameBlock3D, self).__init__()
    self.conv = nn.Conv3d(in_channels=in_features, out_channels=out_features, kernel_size=kernel_size, padding=padding, groups=groups)
    self.norm = BatchNorm3d(out_features, affine=True)

class Encoder(nn.Module):
    """
    Hourglass Encoder
    """

    def __init__(self, block_expansion, in_features, num_blocks=3, max_features=256, temporal=False):
        super(Encoder, self).__init__()
        down_blocks = []
        kernel_size = (3, 3, 3) if temporal else (1, 3, 3)
        padding = (1, 1, 1) if temporal else (0, 1, 1)
        for i in range(num_blocks):
            down_blocks.append(DownBlock3D(in_features if i == 0 else min(max_features, block_expansion * 2 ** i), min(max_features, block_expansion * 2 ** (i + 1)), kernel_size=kernel_size, padding=padding))
        self.down_blocks = nn.ModuleList(down_blocks)

    def forward(self, x):
        outs = [x]
        for down_block in self.down_blocks:
            outs.append(down_block(outs[-1]))
        return outs

def __init__(self, block_expansion, in_features, num_blocks=3, max_features=256, temporal=False):
    super(Encoder, self).__init__()
    down_blocks = []
    kernel_size = (3, 3, 3) if temporal else (1, 3, 3)
    padding = (1, 1, 1) if temporal else (0, 1, 1)
    for i in range(num_blocks):
        down_blocks.append(DownBlock3D(in_features if i == 0 else min(max_features, block_expansion * 2 ** i), min(max_features, block_expansion * 2 ** (i + 1)), kernel_size=kernel_size, padding=padding))
    self.down_blocks = nn.ModuleList(down_blocks)

class Decoder(nn.Module):
    """
    Hourglass Decoder
    """

    def __init__(self, block_expansion, in_features, out_features, num_blocks=3, max_features=256, temporal=False, additional_features_for_block=0, use_last_conv=True):
        super(Decoder, self).__init__()
        kernel_size = (3, 3, 3) if temporal else (1, 3, 3)
        padding = (1, 1, 1) if temporal else (0, 1, 1)
        up_blocks = []
        for i in range(num_blocks)[::-1]:
            up_blocks.append(UpBlock3D((1 if i == num_blocks - 1 else 2) * min(max_features, block_expansion * 2 ** (i + 1)) + additional_features_for_block, min(max_features, block_expansion * 2 ** i), kernel_size=kernel_size, padding=padding))
        self.up_blocks = nn.ModuleList(up_blocks)
        if use_last_conv:
            self.conv = nn.Conv3d(in_channels=block_expansion + in_features + additional_features_for_block, out_channels=out_features, kernel_size=kernel_size, padding=padding)
        else:
            self.conv = None

    def forward(self, x):
        out = x.pop()
        for up_block in self.up_blocks:
            out = up_block(out)
            out = torch.cat([out, x.pop()], dim=1)
        if self.conv is not None:
            return self.conv(out)
        else:
            return out

def __init__(self, block_expansion, in_features, out_features, num_blocks=3, max_features=256, temporal=False, additional_features_for_block=0, use_last_conv=True):
    super(Decoder, self).__init__()
    kernel_size = (3, 3, 3) if temporal else (1, 3, 3)
    padding = (1, 1, 1) if temporal else (0, 1, 1)
    up_blocks = []
    for i in range(num_blocks)[::-1]:
        up_blocks.append(UpBlock3D((1 if i == num_blocks - 1 else 2) * min(max_features, block_expansion * 2 ** (i + 1)) + additional_features_for_block, min(max_features, block_expansion * 2 ** i), kernel_size=kernel_size, padding=padding))
    self.up_blocks = nn.ModuleList(up_blocks)
    if use_last_conv:
        self.conv = nn.Conv3d(in_channels=block_expansion + in_features + additional_features_for_block, out_channels=out_features, kernel_size=kernel_size, padding=padding)
    else:
        self.conv = None

class Hourglass(nn.Module):
    """
    Hourglass architecture.
    """

    def __init__(self, block_expansion, in_features, out_features, num_blocks=3, max_features=256, temporal=False):
        super(Hourglass, self).__init__()
        self.encoder = Encoder(block_expansion, in_features, num_blocks, max_features, temporal=temporal)
        self.decoder = Decoder(block_expansion, in_features, out_features, num_blocks, max_features, temporal=temporal)

    def forward(self, x):
        return self.decoder(self.encoder(x))

def __init__(self, block_expansion, in_features, out_features, num_blocks=3, max_features=256, temporal=False):
    super(Hourglass, self).__init__()
    self.encoder = Encoder(block_expansion, in_features, num_blocks, max_features, temporal=temporal)
    self.decoder = Decoder(block_expansion, in_features, out_features, num_blocks, max_features, temporal=temporal)

class MotionTransferGenerator(nn.Module):
    """
    Motion transfer generator. That Given a keypoints and an appearance trying to reconstruct the target frame.
    Produce 2 versions of target frame, one warped with predicted optical flow and other refined.
    """

    def __init__(self, num_channels, num_kp, kp_variance, block_expansion, max_features, num_blocks, num_refinement_blocks, dense_motion_params=None, kp_embedding_params=None, interpolation_mode='nearest'):
        super(MotionTransferGenerator, self).__init__()
        self.appearance_encoder = Encoder(block_expansion, in_features=num_channels, max_features=max_features, num_blocks=num_blocks)
        if kp_embedding_params is not None:
            self.kp_embedding_module = MovementEmbeddingModule(num_kp=num_kp, kp_variance=kp_variance, num_channels=num_channels, **kp_embedding_params)
            embedding_features = self.kp_embedding_module.out_channels
        else:
            self.kp_embedding_module = None
            embedding_features = 0
        if dense_motion_params is not None:
            self.dense_motion_module = DenseMotionModule(num_kp=num_kp, kp_variance=kp_variance, num_channels=num_channels, **dense_motion_params)
        else:
            self.dense_motion_module = IdentityDeformation()
        self.video_decoder = Decoder(block_expansion=block_expansion, in_features=num_channels, out_features=num_channels, max_features=max_features, num_blocks=num_blocks, additional_features_for_block=embedding_features, use_last_conv=False)
        self.refinement_module = torch.nn.Sequential()
        in_features = block_expansion + num_channels + embedding_features
        for i in range(num_refinement_blocks):
            self.refinement_module.add_module('r' + str(i), ResBlock3D(in_features, kernel_size=(1, 3, 3), padding=(0, 1, 1)))
        self.refinement_module.add_module('conv-last', nn.Conv3d(in_features, num_channels, kernel_size=1, padding=0))
        self.interpolation_mode = interpolation_mode

    def deform_input(self, inp, deformations_absolute):
        bs, d, h_old, w_old, _ = deformations_absolute.shape
        _, _, _, h, w = inp.shape
        deformations_absolute = deformations_absolute.permute(0, 4, 1, 2, 3)
        deformation = F.interpolate(deformations_absolute, size=(d, h, w), mode=self.interpolation_mode)
        deformation = deformation.permute(0, 2, 3, 4, 1)
        deformed_inp = F.grid_sample(inp, deformation)
        return deformed_inp

    def forward(self, source_image, kp_driving, kp_source):
        appearance_skips = self.appearance_encoder(source_image)
        deformations_absolute = self.dense_motion_module(source_image=source_image, kp_driving=kp_driving, kp_source=kp_source)
        deformed_skips = [self.deform_input(skip, deformations_absolute) for skip in appearance_skips]
        if self.kp_embedding_module is not None:
            d = kp_driving['mean'].shape[1]
            movement_embedding = self.kp_embedding_module(source_image=source_image, kp_driving=kp_driving, kp_source=kp_source)
            kp_skips = [F.interpolate(movement_embedding, size=(d,) + skip.shape[3:], mode=self.interpolation_mode) for skip in appearance_skips]
            skips = [torch.cat([a, b], dim=1) for a, b in zip(deformed_skips, kp_skips)]
        else:
            skips = deformed_skips
        video_deformed = self.deform_input(source_image, deformations_absolute)
        video_prediction = self.video_decoder(skips)
        video_prediction = self.refinement_module(video_prediction)
        video_prediction = torch.sigmoid(video_prediction)
        return {'video_prediction': video_prediction, 'video_deformed': video_deformed}

def __init__(self, num_channels, num_kp, kp_variance, block_expansion, max_features, num_blocks, num_refinement_blocks, dense_motion_params=None, kp_embedding_params=None, interpolation_mode='nearest'):
    super(MotionTransferGenerator, self).__init__()
    self.appearance_encoder = Encoder(block_expansion, in_features=num_channels, max_features=max_features, num_blocks=num_blocks)
    if kp_embedding_params is not None:
        self.kp_embedding_module = MovementEmbeddingModule(num_kp=num_kp, kp_variance=kp_variance, num_channels=num_channels, **kp_embedding_params)
        embedding_features = self.kp_embedding_module.out_channels
    else:
        self.kp_embedding_module = None
        embedding_features = 0
    if dense_motion_params is not None:
        self.dense_motion_module = DenseMotionModule(num_kp=num_kp, kp_variance=kp_variance, num_channels=num_channels, **dense_motion_params)
    else:
        self.dense_motion_module = IdentityDeformation()
    self.video_decoder = Decoder(block_expansion=block_expansion, in_features=num_channels, out_features=num_channels, max_features=max_features, num_blocks=num_blocks, additional_features_for_block=embedding_features, use_last_conv=False)
    self.refinement_module = torch.nn.Sequential()
    in_features = block_expansion + num_channels + embedding_features
    for i in range(num_refinement_blocks):
        self.refinement_module.add_module('r' + str(i), ResBlock3D(in_features, kernel_size=(1, 3, 3), padding=(0, 1, 1)))
    self.refinement_module.add_module('conv-last', nn.Conv3d(in_features, num_channels, kernel_size=1, padding=0))
    self.interpolation_mode = interpolation_mode

