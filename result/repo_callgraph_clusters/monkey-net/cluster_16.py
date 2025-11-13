# Cluster 16

class Visualizer:

    def __init__(self, kp_size=2, draw_border=False, colormap='gist_rainbow'):
        self.kp_size = kp_size
        self.draw_border = draw_border
        self.colormap = plt.get_cmap(colormap)

    def draw_video_with_kp(self, video, kp_array):
        video_array = np.copy(video)
        spatial_size = np.array(video_array.shape[2:0:-1])[np.newaxis, np.newaxis]
        kp_array = spatial_size * (kp_array + 1) / 2
        num_kp = kp_array.shape[1]
        for i in range(len(video_array)):
            for kp_ind, kp in enumerate(kp_array[i]):
                rr, cc = circle(kp[1], kp[0], self.kp_size, shape=video_array.shape[1:3])
                video_array[i][rr, cc] = np.array(self.colormap(kp_ind / num_kp))[:3]
        return video_array

    def create_video_column_with_kp(self, video, kp):
        video_array = np.array([self.draw_video_with_kp(v, k) for v, k in zip(video, kp)])
        return self.create_video_column(video_array)

    def create_video_column(self, videos):
        if self.draw_border:
            videos = np.copy(videos)
            videos[:, :, [0, -1]] = (1, 1, 1)
            videos[:, :, :, [0, -1]] = (1, 1, 1)
        return np.concatenate(list(videos), axis=1)

    def create_image_grid(self, *args):
        out = []
        for arg in args:
            if type(arg) == tuple:
                out.append(self.create_video_column_with_kp(arg[0], arg[1]))
            else:
                out.append(self.create_video_column(arg))
        return np.concatenate(out, axis=2)

    def visualize_transfer(self, driving_video, source_image, out):
        out_video_batch = out['video_prediction'].data.cpu().numpy()
        appearance_deformed_batch = out['video_deformed'].data.cpu().numpy()
        motion_video_batch = driving_video.data.cpu().numpy()
        appearance_video_batch = source_image[:, :, 0:1].data.cpu().repeat(1, 1, out_video_batch.shape[2], 1, 1).numpy()
        video_first_frame = driving_video[:, :, 0:1].data.cpu().repeat(1, 1, out_video_batch.shape[2], 1, 1).numpy()
        kp_video = out['kp_driving']['mean'].data.cpu().numpy()
        kp_appearance = out['kp_source']['mean'].data.cpu().repeat(1, out_video_batch.shape[2], 1, 1).numpy()
        kp_norm = out['kp_norm']['mean'].data.cpu().numpy()
        kp_video_first = out['kp_driving']['mean'][:, :1].data.cpu().repeat(1, out_video_batch.shape[2], 1, 1).numpy()
        video_first_frame = np.transpose(video_first_frame, [0, 2, 3, 4, 1])
        out_video_batch = np.transpose(out_video_batch, [0, 2, 3, 4, 1])
        motion_video_batch = np.transpose(motion_video_batch, [0, 2, 3, 4, 1])
        appearance_video_batch = np.transpose(appearance_video_batch, [0, 2, 3, 4, 1])
        appearance_deformed_batch = np.transpose(appearance_deformed_batch, [0, 2, 3, 4, 1])
        image = self.create_image_grid((appearance_video_batch, kp_appearance), (video_first_frame, kp_video_first), (motion_video_batch, kp_video), (out_video_batch, kp_norm), out_video_batch, appearance_deformed_batch)
        image = (255 * image).astype(np.uint8)
        return image

    def visualize_reconstruction(self, inp, out):
        out_video_batch = out['video_prediction'].data.cpu().numpy()
        if 'driving' in inp:
            gt_video_batch = inp['driving'].data.cpu().numpy()
        else:
            gt_video_batch = inp['video'].data.cpu().numpy()
        appearance_deformed_batch = out['video_deformed'].data.cpu().numpy()
        appearance_video_batch = inp['source'].data.cpu().repeat(1, 1, out_video_batch.shape[2], 1, 1).numpy()
        kp_video = out['kp_driving']['mean'].data.cpu().numpy()
        kp_appearance = out['kp_source']['mean'].data.cpu().repeat(1, out_video_batch.shape[2], 1, 1).numpy()
        out_video_batch = np.transpose(out_video_batch, [0, 2, 3, 4, 1])
        gt_video_batch = np.transpose(gt_video_batch, [0, 2, 3, 4, 1])
        appearance_video_batch = np.transpose(appearance_video_batch, [0, 2, 3, 4, 1])
        appearance_deformed_batch = np.transpose(appearance_deformed_batch, [0, 2, 3, 4, 1])
        image = self.create_image_grid((appearance_video_batch, kp_appearance), (gt_video_batch, kp_video), out_video_batch, appearance_deformed_batch, gt_video_batch)
        image = (255 * image).astype(np.uint8)
        return image

def create_video_column_with_kp(self, video, kp):
    video_array = np.array([self.draw_video_with_kp(v, k) for v, k in zip(video, kp)])
    return self.create_video_column(video_array)

def execute_replication_callbacks(modules):
    """
    Execute an replication callback `__data_parallel_replicate__` on each module created by original replication.

    The callback will be invoked with arguments `__data_parallel_replicate__(ctx, copy_id)`

    Note that, as all modules are isomorphism, we assign each sub-module with a context
    (shared among multiple copies of this module on different devices).
    Through this context, different copies can share some information.

    We guarantee that the callback on the master copy (the first copy) will be called ahead of calling the callback
    of any slave copies.
    """
    master_copy = modules[0]
    nr_modules = len(list(master_copy.modules()))
    ctxs = [CallbackContext() for _ in range(nr_modules)]
    for i, module in enumerate(modules):
        for j, m in enumerate(module.modules()):
            if hasattr(m, '__data_parallel_replicate__'):
                m.__data_parallel_replicate__(ctxs[j], i)

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

def generator_loss_names(loss_weights):
    loss_names = []
    if loss_weights['reconstruction_deformed'] != 0:
        loss_names.append('rec_def')
    if loss_weights['reconstruction'] is not None:
        for i, _ in enumerate(loss_weights['reconstruction']):
            if loss_weights['reconstruction'][i] == 0:
                continue
            loss_names.append('layer-%s_rec' % i)
    loss_names.append('gen_gan')
    return loss_names

def generator_loss(discriminator_maps_generated, discriminator_maps_real, video_deformed, loss_weights):
    loss_values = []
    if loss_weights['reconstruction_deformed'] != 0:
        loss_values.append(reconstruction_loss(discriminator_maps_real[0], video_deformed, loss_weights['reconstruction_deformed']))
    if loss_weights['reconstruction'] != 0:
        for i, (a, b) in enumerate(zip(discriminator_maps_real[:-1], discriminator_maps_generated[:-1])):
            if loss_weights['reconstruction'][i] == 0:
                continue
            loss_values.append(reconstruction_loss(b, a, weight=loss_weights['reconstruction'][i]))
    loss_values.append(generator_gan_loss(discriminator_maps_generated, weight=loss_weights['generator_gan']))
    return loss_values

