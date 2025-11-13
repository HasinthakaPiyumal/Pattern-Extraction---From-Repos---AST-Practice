# Cluster 19

def get_state_dict(net_type: str='alex', version: str='0.1'):
    url = 'https://raw.githubusercontent.com/richzhang/PerceptualSimilarity/' + f'master/lpips/weights/v{version}/{net_type}.pth'
    old_state_dict = torch.hub.load_state_dict_from_url(url, progress=True, map_location=None if torch.cuda.is_available() else torch.device('cpu'))
    new_state_dict = OrderedDict()
    for key, val in old_state_dict.items():
        new_key = key
        new_key = new_key.replace('lin', '')
        new_key = new_key.replace('model.', '')
        new_state_dict[new_key] = val
    return new_state_dict

class SpectralNorm(object):
    _version = 1

    def __init__(self, name='weight', n_power_iterations=1, dim=0, eps=1e-12):
        self.name = name
        self.dim = dim
        if n_power_iterations <= 0:
            raise ValueError('Expected n_power_iterations to be positive, but got n_power_iterations={}'.format(n_power_iterations))
        self.n_power_iterations = n_power_iterations
        self.eps = eps

    def reshape_weight_to_matrix(self, weight):
        weight_mat = weight
        if self.dim != 0:
            weight_mat = weight_mat.permute(self.dim, *[d for d in range(weight_mat.dim()) if d != self.dim])
        height = weight_mat.size(0)
        return weight_mat.reshape(height, -1)

    def compute_weight(self, module, do_power_iteration):
        weight = getattr(module, self.name + '_orig')
        u = getattr(module, self.name + '_u')
        v = getattr(module, self.name + '_v')
        weight_mat = self.reshape_weight_to_matrix(weight)
        if do_power_iteration:
            with torch.no_grad():
                for _ in range(self.n_power_iterations):
                    v = normalize(torch.mv(weight_mat.t(), u), dim=0, eps=self.eps, out=v)
                    u = normalize(torch.mv(weight_mat, v), dim=0, eps=self.eps, out=u)
                if self.n_power_iterations > 0:
                    u = u.clone()
                    v = v.clone()
        sigma = torch.dot(u, torch.mv(weight_mat, v))
        weight = weight / sigma
        return weight

    def remove(self, module):
        with torch.no_grad():
            weight = self.compute_weight(module, do_power_iteration=False)
        delattr(module, self.name)
        delattr(module, self.name + '_u')
        delattr(module, self.name + '_v')
        delattr(module, self.name + '_orig')
        module.register_parameter(self.name, torch.nn.Parameter(weight.detach()))

    def __call__(self, module, inputs):
        setattr(module, self.name, self.compute_weight(module, do_power_iteration=module.training))

    def _solve_v_and_rescale(self, weight_mat, u, target_sigma):
        v = torch.chain_matmul(weight_mat.t().mm(weight_mat).pinverse(), weight_mat.t(), u.unsqueeze(1)).squeeze(1)
        return v.mul_(target_sigma / torch.dot(u, torch.mv(weight_mat, v)))

    @staticmethod
    def apply(module, name, n_power_iterations, dim, eps):
        for k, hook in module._forward_pre_hooks.items():
            if isinstance(hook, SpectralNorm) and hook.name == name:
                raise RuntimeError('Cannot register two spectral_norm hooks on the same parameter {}'.format(name))
        fn = SpectralNorm(name, n_power_iterations, dim, eps)
        weight = module._parameters[name]
        with torch.no_grad():
            weight_mat = fn.reshape_weight_to_matrix(weight)
            h, w = weight_mat.size()
            u = normalize(weight.new_empty(h).normal_(0, 1), dim=0, eps=fn.eps)
            v = normalize(weight.new_empty(w).normal_(0, 1), dim=0, eps=fn.eps)
        delattr(module, fn.name)
        module.register_parameter(fn.name + '_orig', weight)
        setattr(module, fn.name, weight.data)
        module.register_buffer(fn.name + '_u', u)
        module.register_buffer(fn.name + '_v', v)
        module.register_forward_pre_hook(fn)
        module._register_state_dict_hook(SpectralNormStateDictHook(fn))
        module._register_load_state_dict_pre_hook(SpectralNormLoadStateDictPreHook(fn))
        return fn

def __init__(self, name='weight', n_power_iterations=1, dim=0, eps=1e-12):
    self.name = name
    self.dim = dim
    if n_power_iterations <= 0:
        raise ValueError('Expected n_power_iterations to be positive, but got n_power_iterations={}'.format(n_power_iterations))
    self.n_power_iterations = n_power_iterations
    self.eps = eps

def reshape_weight_to_matrix(self, weight):
    weight_mat = weight
    if self.dim != 0:
        weight_mat = weight_mat.permute(self.dim, *[d for d in range(weight_mat.dim()) if d != self.dim])
    height = weight_mat.size(0)
    return weight_mat.reshape(height, -1)

def fn_wrapper(pretrained=False, **kwargs):
    model = fn()
    if pretrained:
        model_name = fn.__name__
        assert model_name in _provided_checkpoints, f'Sorry that the checkpoint `{model_name}` is not provided yet.'
        url = _checkpoint_url_format.format(_provided_checkpoints[model_name])
        checkpoint = torch.hub.load_state_dict_from_url(url=url, map_location='cpu', check_hash=False)
        model.load_state_dict(checkpoint['model'])
    return model

class SimpleImageSquareMaskDataset(Dataset):

    def __init__(self, dataset):
        self.dataset = dataset
        self.mask = torch.FloatTensor(create_rectangle_mask(*self.dataset.image_size))
        self.model = Model()

    def __getitem__(self, index):
        img = self.dataset[index]
        mask = self.mask.clone()
        inpainted = self.model(img[None, ...], mask[None, ...])
        return dict(image=img, mask=mask, inpainted=inpainted)

    def __len__(self):
        return len(self.dataset)

def __init__(self, dataset):
    self.dataset = dataset
    self.mask = torch.FloatTensor(create_rectangle_mask(*self.dataset.image_size))
    self.model = Model()

def main(args):
    config = load_yaml(args.config)
    dataset = PrecomputedInpaintingResultsDataset(args.datadir, args.predictdir, **config.dataset_kwargs)
    metrics = {'ssim': SSIMScore(), 'lpips': LPIPSScore(), 'fid': FIDScore()}
    enable_segm = config.get('segmentation', dict(enable=False)).get('enable', False)
    if enable_segm:
        weights_path = os.path.expandvars(config.segmentation.weights_path)
        metrics.update(dict(segm_stats=SegmentationClassStats(weights_path=weights_path), segm_ssim=SegmentationAwareSSIM(weights_path=weights_path), segm_lpips=SegmentationAwareLPIPS(weights_path=weights_path), segm_fid=SegmentationAwareFID(weights_path=weights_path)))
    evaluator = InpaintingEvaluator(dataset, scores=metrics, integral_title='lpips_fid100_f1', integral_func=lpips_fid100_f1, **config.evaluator_kwargs)
    os.makedirs(os.path.dirname(args.outpath), exist_ok=True)
    results = evaluator.evaluate()
    results = pd.DataFrame(results).stack(1).unstack(0)
    results.dropna(axis=1, how='all', inplace=True)
    results.to_csv(args.outpath, sep='\t', float_format='%.4f')
    if enable_segm:
        only_short_results = results[[c for c in results.columns if not c[0].startswith('segm_')]].dropna(axis=1, how='all')
        only_short_results.to_csv(args.outpath + '_short', sep='\t', float_format='%.4f')
        print(only_short_results)
        segm_metrics_results = results[['segm_ssim', 'segm_lpips', 'segm_fid']].dropna(axis=1, how='all').transpose().unstack(0).reorder_levels([1, 0], axis=1)
        segm_metrics_results.drop(['mean', 'std'], axis=0, inplace=True)
        segm_stats_results = results['segm_stats'].dropna(axis=1, how='all').transpose()
        segm_stats_results.index = pd.MultiIndex.from_tuples((n.split('/') for n in segm_stats_results.index))
        segm_stats_results = segm_stats_results.unstack(0).reorder_levels([1, 0], axis=1)
        segm_stats_results.sort_index(axis=1, inplace=True)
        segm_stats_results.dropna(axis=0, how='all', inplace=True)
        segm_results = pd.concat([segm_metrics_results, segm_stats_results], axis=1, sort=True)
        segm_results.sort_values(('mask_freq', 'total'), ascending=False, inplace=True)
        segm_results.to_csv(args.outpath + '_segm', sep='\t', float_format='%.4f')
    else:
        print(results)

def get_ramp(kind='ladder', **kwargs):
    if kind == 'linear':
        return LinearRamp(**kwargs)
    if kind == 'ladder':
        return LadderRamp(**kwargs)
    raise ValueError(f'Unexpected ramp kind: {kind}')

def make_discrim_loss(kind, **kwargs):
    if kind == 'r1':
        return NonSaturatingWithR1(**kwargs)
    elif kind == 'bce':
        return BCELoss(**kwargs)
    raise ValueError(f'Unknown adversarial loss kind {kind}')

def make_mask_distance_weighter(kind='none', **kwargs):
    if kind == 'none':
        return dummy_distance_weighter
    if kind == 'blur':
        return BlurMask(**kwargs)
    if kind == 'edt':
        return EmulatedEDTMask(**kwargs)
    if kind == 'pps':
        return PropagatePerceptualSim(**kwargs)
    raise ValueError(f'Unknown mask distance weighter kind {kind}')

def make_optimizer(parameters, kind='adamw', **kwargs):
    if kind == 'adam':
        optimizer_class = torch.optim.Adam
    elif kind == 'adamw':
        optimizer_class = torch.optim.AdamW
    else:
        raise ValueError(f'Unknown optimizer kind {kind}')
    return optimizer_class(parameters, **kwargs)

def get_training_model_class(kind):
    if kind == 'default':
        return DefaultInpaintingTrainingModule
    raise ValueError(f'Unknown trainer module {kind}')

def get_conv_block_ctor(kind='default'):
    if not isinstance(kind, str):
        return kind
    if kind == 'default':
        return nn.Conv2d
    if kind == 'depthwise':
        return DepthWiseSeperableConv
    if kind == 'multidilated':
        return MultidilatedConv
    raise ValueError(f'Unknown convolutional block kind {kind}')

def get_norm_layer(kind='bn'):
    if not isinstance(kind, str):
        return kind
    if kind == 'bn':
        return nn.BatchNorm2d
    if kind == 'in':
        return nn.InstanceNorm2d
    raise ValueError(f'Unknown norm block kind {kind}')

def make_generator(config, kind, **kwargs):
    logging.info(f'Make generator {kind}')
    if kind == 'pix2pixhd_multidilated':
        return MultiDilatedGlobalGenerator(**kwargs)
    if kind == 'pix2pixhd_global':
        return GlobalGenerator(**kwargs)
    if kind == 'ffc_resnet':
        return FFCResNetGenerator(**kwargs)
    raise ValueError(f'Unknown generator kind {kind}')

def make_discriminator(kind, **kwargs):
    logging.info(f'Make discriminator {kind}')
    if kind == 'pix2pixhd_nlayer_multidilated':
        return MultidilatedNLayerDiscriminator(**kwargs)
    if kind == 'pix2pixhd_nlayer':
        return NLayerDiscriminator(**kwargs)
    raise ValueError(f'Unknown discriminator kind {kind}')

class GlobalGeneratorFromSuperChannels(nn.Module):

    def __init__(self, input_nc, output_nc, n_downsampling, n_blocks, super_channels, norm_layer='bn', padding_type='reflect', add_out_act=True):
        super().__init__()
        self.n_downsampling = n_downsampling
        norm_layer = get_norm_layer(norm_layer)
        if type(norm_layer) == functools.partial:
            use_bias = norm_layer.func == nn.InstanceNorm2d
        else:
            use_bias = norm_layer == nn.InstanceNorm2d
        channels = self.convert_super_channels(super_channels)
        self.channels = channels
        model = [nn.ReflectionPad2d(3), nn.Conv2d(input_nc, channels[0], kernel_size=7, padding=0, bias=use_bias), norm_layer(channels[0]), nn.ReLU(True)]
        for i in range(n_downsampling):
            mult = 2 ** i
            model += [nn.Conv2d(channels[0 + i], channels[1 + i], kernel_size=3, stride=2, padding=1, bias=use_bias), norm_layer(channels[1 + i]), nn.ReLU(True)]
        mult = 2 ** n_downsampling
        n_blocks1 = n_blocks // 3
        n_blocks2 = n_blocks1
        n_blocks3 = n_blocks - n_blocks1 - n_blocks2
        for i in range(n_blocks1):
            c = n_downsampling
            dim = channels[c]
            model += [ResnetBlock(dim, padding_type=padding_type, norm_layer=norm_layer)]
        for i in range(n_blocks2):
            c = n_downsampling + 1
            dim = channels[c]
            kwargs = {}
            if i == 0:
                kwargs = {'in_dim': channels[c - 1]}
            model += [ResnetBlock(dim, padding_type=padding_type, norm_layer=norm_layer, **kwargs)]
        for i in range(n_blocks3):
            c = n_downsampling + 2
            dim = channels[c]
            kwargs = {}
            if i == 0:
                kwargs = {'in_dim': channels[c - 1]}
            model += [ResnetBlock(dim, padding_type=padding_type, norm_layer=norm_layer, **kwargs)]
        for i in range(n_downsampling):
            mult = 2 ** (n_downsampling - i)
            model += [nn.ConvTranspose2d(channels[n_downsampling + 3 + i], channels[n_downsampling + 3 + i + 1], kernel_size=3, stride=2, padding=1, output_padding=1, bias=use_bias), norm_layer(channels[n_downsampling + 3 + i + 1]), nn.ReLU(True)]
        model += [nn.ReflectionPad2d(3)]
        model += [nn.Conv2d(channels[2 * n_downsampling + 3], output_nc, kernel_size=7, padding=0)]
        if add_out_act:
            model.append(get_activation('tanh' if add_out_act is True else add_out_act))
        self.model = nn.Sequential(*model)

    def convert_super_channels(self, super_channels):
        n_downsampling = self.n_downsampling
        result = []
        cnt = 0
        if n_downsampling == 2:
            N1 = 10
        elif n_downsampling == 3:
            N1 = 13
        else:
            raise NotImplementedError
        for i in range(0, N1):
            if i in [1, 4, 7, 10]:
                channel = super_channels[cnt] * 2 ** cnt
                config = {'channel': channel}
                result.append(channel)
                logging.info(f'Downsample channels {result[-1]}')
                cnt += 1
        for i in range(3):
            for counter, j in enumerate(range(N1 + i * 3, N1 + 3 + i * 3)):
                if len(super_channels) == 6:
                    channel = super_channels[3] * 4
                else:
                    channel = super_channels[i + 3] * 4
                config = {'channel': channel}
                if counter == 0:
                    result.append(channel)
                    logging.info(f'Bottleneck channels {result[-1]}')
        cnt = 2
        for i in range(N1 + 9, N1 + 21):
            if i in [22, 25, 28]:
                cnt -= 1
                if len(super_channels) == 6:
                    channel = super_channels[5 - cnt] * 2 ** cnt
                else:
                    channel = super_channels[7 - cnt] * 2 ** cnt
                result.append(int(channel))
                logging.info(f'Upsample channels {result[-1]}')
        return result

    def forward(self, input):
        return self.model(input)

def convert_super_channels(self, super_channels):
    n_downsampling = self.n_downsampling
    result = []
    cnt = 0
    if n_downsampling == 2:
        N1 = 10
    elif n_downsampling == 3:
        N1 = 13
    else:
        raise NotImplementedError
    for i in range(0, N1):
        if i in [1, 4, 7, 10]:
            channel = super_channels[cnt] * 2 ** cnt
            config = {'channel': channel}
            result.append(channel)
            logging.info(f'Downsample channels {result[-1]}')
            cnt += 1
    for i in range(3):
        for counter, j in enumerate(range(N1 + i * 3, N1 + 3 + i * 3)):
            if len(super_channels) == 6:
                channel = super_channels[3] * 4
            else:
                channel = super_channels[i + 3] * 4
            config = {'channel': channel}
            if counter == 0:
                result.append(channel)
                logging.info(f'Bottleneck channels {result[-1]}')
    cnt = 2
    for i in range(N1 + 9, N1 + 21):
        if i in [22, 25, 28]:
            cnt -= 1
            if len(super_channels) == 6:
                channel = super_channels[5 - cnt] * 2 ** cnt
            else:
                channel = super_channels[7 - cnt] * 2 ** cnt
            result.append(int(channel))
            logging.info(f'Upsample channels {result[-1]}')
    return result

def make_visualizer(kind, **kwargs):
    logging.info(f'Make visualizer {kind}')
    if kind == 'directory':
        return DirectoryVisualizer(**kwargs)
    if kind == 'noop':
        return NoopVisualizer()
    raise ValueError(f'Unknown visualizer kind {kind}')

def make_evaluator(kind='default', ssim=True, lpips=True, fid=True, integral_kind=None, **kwargs):
    logging.info(f'Make evaluator {kind}')
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    metrics = {}
    if ssim:
        metrics['ssim'] = SSIMScore()
    if lpips:
        metrics['lpips'] = LPIPSScore()
    if fid:
        metrics['fid'] = FIDScore().to(device)
    if integral_kind is None:
        integral_func = None
    elif integral_kind == 'ssim_fid100_f1':
        integral_func = ssim_fid100_f1
    elif integral_kind == 'lpips_fid100_f1':
        integral_func = lpips_fid100_f1
    else:
        raise ValueError(f'Unexpected integral_kind={integral_kind}')
    if kind == 'default':
        return InpaintingEvaluatorOnline(scores=metrics, integral_func=integral_func, integral_title=integral_kind, **kwargs)

def fid_inception_v3():
    """Build pretrained Inception model for FID computation

    The Inception model for FID computation uses a different set of weights
    and has a slightly different structure than torchvision's Inception.

    This method first constructs torchvision's Inception and then patches the
    necessary parts that are different in the FID Inception model.
    """
    LOGGER.info('fid_inception_v3 called')
    inception = models.inception_v3(num_classes=1008, aux_logits=False, pretrained=False)
    LOGGER.info('models.inception_v3 done')
    inception.Mixed_5b = FIDInceptionA(192, pool_features=32)
    inception.Mixed_5c = FIDInceptionA(256, pool_features=64)
    inception.Mixed_5d = FIDInceptionA(288, pool_features=64)
    inception.Mixed_6b = FIDInceptionC(768, channels_7x7=128)
    inception.Mixed_6c = FIDInceptionC(768, channels_7x7=160)
    inception.Mixed_6d = FIDInceptionC(768, channels_7x7=160)
    inception.Mixed_6e = FIDInceptionC(768, channels_7x7=192)
    inception.Mixed_7b = FIDInceptionE_1(1280)
    inception.Mixed_7c = FIDInceptionE_2(2048)
    LOGGER.info('fid_inception_v3 patching done')
    state_dict = load_state_dict_from_url(FID_WEIGHTS_URL, progress=True)
    LOGGER.info('fid_inception_v3 weights downloaded')
    inception.load_state_dict(state_dict)
    LOGGER.info('fid_inception_v3 weights loaded into model')
    return inception

class SegmentationModule(nn.Module):

    def __init__(self, weights_path, num_classes=150, arch_encoder='resnet50dilated', drop_last_conv=False, net_enc=None, net_dec=None, encode=None, use_default_normalization=False, return_feature_maps=False, return_feature_maps_level=3, return_feature_maps_only=True, **kwargs):
        super().__init__()
        self.weights_path = weights_path
        self.drop_last_conv = drop_last_conv
        self.arch_encoder = arch_encoder
        if self.arch_encoder == 'resnet50dilated':
            self.arch_decoder = 'ppm_deepsup'
            self.fc_dim = 2048
        elif self.arch_encoder == 'mobilenetv2dilated':
            self.arch_decoder = 'c1_deepsup'
            self.fc_dim = 320
        else:
            raise NotImplementedError(f'No such arch_encoder={self.arch_encoder}')
        model_builder_kwargs = dict(arch_encoder=self.arch_encoder, arch_decoder=self.arch_decoder, fc_dim=self.fc_dim, drop_last_conv=drop_last_conv, weights_path=self.weights_path)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.encoder = ModelBuilder.get_encoder(**model_builder_kwargs) if net_enc is None else net_enc
        self.decoder = ModelBuilder.get_decoder(**model_builder_kwargs) if net_dec is None else net_dec
        self.use_default_normalization = use_default_normalization
        self.default_normalization = NormalizeTensor(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        self.encode = encode
        self.return_feature_maps = return_feature_maps
        assert 0 <= return_feature_maps_level <= 3
        self.return_feature_maps_level = return_feature_maps_level

    def normalize_input(self, tensor):
        if tensor.min() < 0 or tensor.max() > 1:
            raise ValueError('Tensor should be 0..1 before using normalize_input')
        return self.default_normalization(tensor)

    @property
    def feature_maps_channels(self):
        return 256 * 2 ** self.return_feature_maps_level

    def forward(self, img_data, segSize=None):
        if segSize is None:
            raise NotImplementedError('Please pass segSize param. By default: (300, 300)')
        fmaps = self.encoder(img_data, return_feature_maps=True)
        pred = self.decoder(fmaps, segSize=segSize)
        if self.return_feature_maps:
            return (pred, fmaps)
        return pred

    def multi_mask_from_multiclass(self, pred, classes):

        def isin(ar1, ar2):
            return (ar1[..., None] == ar2).any(-1).float()
        return isin(pred, torch.LongTensor(classes).to(self.device))

    @staticmethod
    def multi_mask_from_multiclass_probs(scores, classes):
        res = None
        for c in classes:
            if res is None:
                res = scores[:, c]
            else:
                res += scores[:, c]
        return res

    def predict(self, tensor, imgSizes=(-1,), segSize=None):
        """Entry-point for segmentation. Use this methods instead of forward
        Arguments:
            tensor {torch.Tensor} -- BCHW
        Keyword Arguments:
            imgSizes {tuple or list} -- imgSizes for segmentation input.
                default: (300, 450)
                original implementation: (300, 375, 450, 525, 600)

        """
        if segSize is None:
            segSize = tensor.shape[-2:]
        segSize = (tensor.shape[2], tensor.shape[3])
        with torch.no_grad():
            if self.use_default_normalization:
                tensor = self.normalize_input(tensor)
            scores = torch.zeros(1, NUM_CLASS, segSize[0], segSize[1]).to(self.device)
            features = torch.zeros(1, self.feature_maps_channels, segSize[0], segSize[1]).to(self.device)
            result = []
            for img_size in imgSizes:
                if img_size != -1:
                    img_data = F.interpolate(tensor.clone(), size=img_size)
                else:
                    img_data = tensor.clone()
                if self.return_feature_maps:
                    pred_current, fmaps = self.forward(img_data, segSize=segSize)
                else:
                    pred_current = self.forward(img_data, segSize=segSize)
                result.append(pred_current)
                scores = scores + pred_current / len(imgSizes)
                if self.return_feature_maps:
                    features = features + F.interpolate(fmaps[self.return_feature_maps_level], size=segSize) / len(imgSizes)
            _, pred = torch.max(scores, dim=1)
            if self.return_feature_maps:
                return features
            return (pred, result)

    def get_edges(self, t):
        edge = torch.cuda.ByteTensor(t.size()).zero_()
        edge[:, :, :, 1:] = edge[:, :, :, 1:] | (t[:, :, :, 1:] != t[:, :, :, :-1])
        edge[:, :, :, :-1] = edge[:, :, :, :-1] | (t[:, :, :, 1:] != t[:, :, :, :-1])
        edge[:, :, 1:, :] = edge[:, :, 1:, :] | (t[:, :, 1:, :] != t[:, :, :-1, :])
        edge[:, :, :-1, :] = edge[:, :, :-1, :] | (t[:, :, 1:, :] != t[:, :, :-1, :])
        if True:
            return edge.half()
        return edge.float()

def normalize_input(self, tensor):
    if tensor.min() < 0 or tensor.max() > 1:
        raise ValueError('Tensor should be 0..1 before using normalize_input')
    return self.default_normalization(tensor)

class SynchronizedBatchNorm1d(_SynchronizedBatchNorm):
    """Applies Synchronized Batch Normalization over a 2d or 3d input that is seen as a
    mini-batch.

    .. math::

        y = \\frac{x - mean[x]}{ \\sqrt{Var[x] + \\epsilon}} * gamma + beta

    This module differs from the built-in PyTorch BatchNorm1d as the mean and
    standard-deviation are reduced across all devices during training.

    For example, when one uses `nn.DataParallel` to wrap the network during
    training, PyTorch's implementation normalize the tensor on each device using
    the statistics only on that device, which accelerated the computation and
    is also easy to implement, but the statistics might be inaccurate.
    Instead, in this synchronized version, the statistics will be computed
    over all training samples distributed on multiple devices.
    
    Note that, for one-GPU or CPU-only case, this module behaves exactly same
    as the built-in PyTorch implementation.

    The mean and standard-deviation are calculated per-dimension over
    the mini-batches and gamma and beta are learnable parameter vectors
    of size C (where C is the input size).

    During training, this layer keeps a running estimate of its computed mean
    and variance. The running sum is kept with a default momentum of 0.1.

    During evaluation, this running mean/variance is used for normalization.

    Because the BatchNorm is done over the `C` dimension, computing statistics
    on `(N, L)` slices, it's common terminology to call this Temporal BatchNorm

    Args:
        num_features: num_features from an expected input of size
            `batch_size x num_features [x width]`
        eps: a value added to the denominator for numerical stability.
            Default: 1e-5
        momentum: the value used for the running_mean and running_var
            computation. Default: 0.1
        affine: a boolean value that when set to ``True``, gives the layer learnable
            affine parameters. Default: ``True``

    Shape:
        - Input: :math:`(N, C)` or :math:`(N, C, L)`
        - Output: :math:`(N, C)` or :math:`(N, C, L)` (same shape as input)

    Examples:
        >>> # With Learnable Parameters
        >>> m = SynchronizedBatchNorm1d(100)
        >>> # Without Learnable Parameters
        >>> m = SynchronizedBatchNorm1d(100, affine=False)
        >>> input = torch.autograd.Variable(torch.randn(20, 100))
        >>> output = m(input)
    """

    def _check_input_dim(self, input):
        if input.dim() != 2 and input.dim() != 3:
            raise ValueError('expected 2D or 3D input (got {}D input)'.format(input.dim()))
        super(SynchronizedBatchNorm1d, self)._check_input_dim(input)

def _check_input_dim(self, input):
    if input.dim() != 2 and input.dim() != 3:
        raise ValueError('expected 2D or 3D input (got {}D input)'.format(input.dim()))
    super(SynchronizedBatchNorm1d, self)._check_input_dim(input)

class SynchronizedBatchNorm2d(_SynchronizedBatchNorm):
    """Applies Batch Normalization over a 4d input that is seen as a mini-batch
    of 3d inputs

    .. math::

        y = \\frac{x - mean[x]}{ \\sqrt{Var[x] + \\epsilon}} * gamma + beta

    This module differs from the built-in PyTorch BatchNorm2d as the mean and
    standard-deviation are reduced across all devices during training.

    For example, when one uses `nn.DataParallel` to wrap the network during
    training, PyTorch's implementation normalize the tensor on each device using
    the statistics only on that device, which accelerated the computation and
    is also easy to implement, but the statistics might be inaccurate.
    Instead, in this synchronized version, the statistics will be computed
    over all training samples distributed on multiple devices.
    
    Note that, for one-GPU or CPU-only case, this module behaves exactly same
    as the built-in PyTorch implementation.

    The mean and standard-deviation are calculated per-dimension over
    the mini-batches and gamma and beta are learnable parameter vectors
    of size C (where C is the input size).

    During training, this layer keeps a running estimate of its computed mean
    and variance. The running sum is kept with a default momentum of 0.1.

    During evaluation, this running mean/variance is used for normalization.

    Because the BatchNorm is done over the `C` dimension, computing statistics
    on `(N, H, W)` slices, it's common terminology to call this Spatial BatchNorm

    Args:
        num_features: num_features from an expected input of
            size batch_size x num_features x height x width
        eps: a value added to the denominator for numerical stability.
            Default: 1e-5
        momentum: the value used for the running_mean and running_var
            computation. Default: 0.1
        affine: a boolean value that when set to ``True``, gives the layer learnable
            affine parameters. Default: ``True``

    Shape:
        - Input: :math:`(N, C, H, W)`
        - Output: :math:`(N, C, H, W)` (same shape as input)

    Examples:
        >>> # With Learnable Parameters
        >>> m = SynchronizedBatchNorm2d(100)
        >>> # Without Learnable Parameters
        >>> m = SynchronizedBatchNorm2d(100, affine=False)
        >>> input = torch.autograd.Variable(torch.randn(20, 100, 35, 45))
        >>> output = m(input)
    """

    def _check_input_dim(self, input):
        if input.dim() != 4:
            raise ValueError('expected 4D input (got {}D input)'.format(input.dim()))
        super(SynchronizedBatchNorm2d, self)._check_input_dim(input)

def _check_input_dim(self, input):
    if input.dim() != 4:
        raise ValueError('expected 4D input (got {}D input)'.format(input.dim()))
    super(SynchronizedBatchNorm2d, self)._check_input_dim(input)

class SynchronizedBatchNorm3d(_SynchronizedBatchNorm):
    """Applies Batch Normalization over a 5d input that is seen as a mini-batch
    of 4d inputs

    .. math::

        y = \\frac{x - mean[x]}{ \\sqrt{Var[x] + \\epsilon}} * gamma + beta

    This module differs from the built-in PyTorch BatchNorm3d as the mean and
    standard-deviation are reduced across all devices during training.

    For example, when one uses `nn.DataParallel` to wrap the network during
    training, PyTorch's implementation normalize the tensor on each device using
    the statistics only on that device, which accelerated the computation and
    is also easy to implement, but the statistics might be inaccurate.
    Instead, in this synchronized version, the statistics will be computed
    over all training samples distributed on multiple devices.
    
    Note that, for one-GPU or CPU-only case, this module behaves exactly same
    as the built-in PyTorch implementation.

    The mean and standard-deviation are calculated per-dimension over
    the mini-batches and gamma and beta are learnable parameter vectors
    of size C (where C is the input size).

    During training, this layer keeps a running estimate of its computed mean
    and variance. The running sum is kept with a default momentum of 0.1.

    During evaluation, this running mean/variance is used for normalization.

    Because the BatchNorm is done over the `C` dimension, computing statistics
    on `(N, D, H, W)` slices, it's common terminology to call this Volumetric BatchNorm
    or Spatio-temporal BatchNorm

    Args:
        num_features: num_features from an expected input of
            size batch_size x num_features x depth x height x width
        eps: a value added to the denominator for numerical stability.
            Default: 1e-5
        momentum: the value used for the running_mean and running_var
            computation. Default: 0.1
        affine: a boolean value that when set to ``True``, gives the layer learnable
            affine parameters. Default: ``True``

    Shape:
        - Input: :math:`(N, C, D, H, W)`
        - Output: :math:`(N, C, D, H, W)` (same shape as input)

    Examples:
        >>> # With Learnable Parameters
        >>> m = SynchronizedBatchNorm3d(100)
        >>> # Without Learnable Parameters
        >>> m = SynchronizedBatchNorm3d(100, affine=False)
        >>> input = torch.autograd.Variable(torch.randn(20, 100, 35, 45, 10))
        >>> output = m(input)
    """

    def _check_input_dim(self, input):
        if input.dim() != 5:
            raise ValueError('expected 5D input (got {}D input)'.format(input.dim()))
        super(SynchronizedBatchNorm3d, self)._check_input_dim(input)

def _check_input_dim(self, input):
    if input.dim() != 5:
        raise ValueError('expected 5D input (got {}D input)'.format(input.dim()))
    super(SynchronizedBatchNorm3d, self)._check_input_dim(input)

def get_ramp(kind='ladder', **kwargs):
    if kind == 'linear':
        return LinearRamp(**kwargs)
    if kind == 'ladder':
        return LadderRamp(**kwargs)
    raise ValueError(f'Unexpected ramp kind: {kind}')

def make_discrim_loss(kind, **kwargs):
    if kind == 'r1':
        return NonSaturatingWithR1(**kwargs)
    elif kind == 'bce':
        return BCELoss(**kwargs)
    raise ValueError(f'Unknown adversarial loss kind {kind}')

def make_mask_distance_weighter(kind='none', **kwargs):
    if kind == 'none':
        return dummy_distance_weighter
    if kind == 'blur':
        return BlurMask(**kwargs)
    if kind == 'edt':
        return EmulatedEDTMask(**kwargs)
    if kind == 'pps':
        return PropagatePerceptualSim(**kwargs)
    raise ValueError(f'Unknown mask distance weighter kind {kind}')

class RandomIrregularMaskGenerator:

    def __init__(self, max_angle=4, max_len=60, max_width=20, min_times=0, max_times=10, ramp_kwargs=None, draw_method=DrawMethod.LINE):
        self.max_angle = max_angle
        self.max_len = max_len
        self.max_width = max_width
        self.min_times = min_times
        self.max_times = max_times
        self.draw_method = draw_method
        self.ramp = LinearRamp(**ramp_kwargs) if ramp_kwargs is not None else None

    def __call__(self, img, iter_i=None, raw_image=None):
        coef = self.ramp(iter_i) if self.ramp is not None and iter_i is not None else 1
        cur_max_len = int(max(1, self.max_len * coef))
        cur_max_width = int(max(1, self.max_width * coef))
        cur_max_times = int(self.min_times + 1 + (self.max_times - self.min_times) * coef)
        return make_random_irregular_mask(img.shape[1:], max_angle=self.max_angle, max_len=cur_max_len, max_width=cur_max_width, min_times=self.min_times, max_times=cur_max_times, draw_method=self.draw_method)

def __init__(self, max_angle=4, max_len=60, max_width=20, min_times=0, max_times=10, ramp_kwargs=None, draw_method=DrawMethod.LINE):
    self.max_angle = max_angle
    self.max_len = max_len
    self.max_width = max_width
    self.min_times = min_times
    self.max_times = max_times
    self.draw_method = draw_method
    self.ramp = LinearRamp(**ramp_kwargs) if ramp_kwargs is not None else None

class RandomRectangleMaskGenerator:

    def __init__(self, margin=10, bbox_min_size=30, bbox_max_size=100, min_times=0, max_times=3, ramp_kwargs=None):
        self.margin = margin
        self.bbox_min_size = bbox_min_size
        self.bbox_max_size = bbox_max_size
        self.min_times = min_times
        self.max_times = max_times
        self.ramp = LinearRamp(**ramp_kwargs) if ramp_kwargs is not None else None

    def __call__(self, img, iter_i=None, raw_image=None):
        coef = self.ramp(iter_i) if self.ramp is not None and iter_i is not None else 1
        cur_bbox_max_size = int(self.bbox_min_size + 1 + (self.bbox_max_size - self.bbox_min_size) * coef)
        cur_max_times = int(self.min_times + (self.max_times - self.min_times) * coef)
        return make_random_rectangle_mask(img.shape[1:], margin=self.margin, bbox_min_size=self.bbox_min_size, bbox_max_size=cur_bbox_max_size, min_times=self.min_times, max_times=cur_max_times)

def __init__(self, margin=10, bbox_min_size=30, bbox_max_size=100, min_times=0, max_times=3, ramp_kwargs=None):
    self.margin = margin
    self.bbox_min_size = bbox_min_size
    self.bbox_max_size = bbox_max_size
    self.min_times = min_times
    self.max_times = max_times
    self.ramp = LinearRamp(**ramp_kwargs) if ramp_kwargs is not None else None

def get_transforms(transform_variant, out_size):
    if transform_variant == 'default':
        transform = A.Compose([A.RandomScale(scale_limit=0.2), A.PadIfNeeded(min_height=out_size, min_width=out_size), A.RandomCrop(height=out_size, width=out_size), A.HorizontalFlip(), A.CLAHE(), A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2), A.HueSaturationValue(hue_shift_limit=5, sat_shift_limit=30, val_shift_limit=5), A.ToFloat()])
    elif transform_variant == 'distortions':
        transform = A.Compose([IAAPerspective2(scale=(0.0, 0.06)), IAAAffine2(scale=(0.7, 1.3), rotate=(-40, 40), shear=(-0.1, 0.1)), A.PadIfNeeded(min_height=out_size, min_width=out_size), A.OpticalDistortion(), A.RandomCrop(height=out_size, width=out_size), A.HorizontalFlip(), A.CLAHE(), A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2), A.HueSaturationValue(hue_shift_limit=5, sat_shift_limit=30, val_shift_limit=5), A.ToFloat()])
    elif transform_variant == 'distortions_scale05_1':
        transform = A.Compose([IAAPerspective2(scale=(0.0, 0.06)), IAAAffine2(scale=(0.5, 1.0), rotate=(-40, 40), shear=(-0.1, 0.1), p=1), A.PadIfNeeded(min_height=out_size, min_width=out_size), A.OpticalDistortion(), A.RandomCrop(height=out_size, width=out_size), A.HorizontalFlip(), A.CLAHE(), A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2), A.HueSaturationValue(hue_shift_limit=5, sat_shift_limit=30, val_shift_limit=5), A.ToFloat()])
    elif transform_variant == 'distortions_scale03_12':
        transform = A.Compose([IAAPerspective2(scale=(0.0, 0.06)), IAAAffine2(scale=(0.3, 1.2), rotate=(-40, 40), shear=(-0.1, 0.1), p=1), A.PadIfNeeded(min_height=out_size, min_width=out_size), A.OpticalDistortion(), A.RandomCrop(height=out_size, width=out_size), A.HorizontalFlip(), A.CLAHE(), A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2), A.HueSaturationValue(hue_shift_limit=5, sat_shift_limit=30, val_shift_limit=5), A.ToFloat()])
    elif transform_variant == 'distortions_scale03_07':
        transform = A.Compose([IAAPerspective2(scale=(0.0, 0.06)), IAAAffine2(scale=(0.3, 0.7), rotate=(-40, 40), shear=(-0.1, 0.1), p=1), A.PadIfNeeded(min_height=out_size, min_width=out_size), A.OpticalDistortion(), A.RandomCrop(height=out_size, width=out_size), A.HorizontalFlip(), A.CLAHE(), A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2), A.HueSaturationValue(hue_shift_limit=5, sat_shift_limit=30, val_shift_limit=5), A.ToFloat()])
    elif transform_variant == 'distortions_light':
        transform = A.Compose([IAAPerspective2(scale=(0.0, 0.02)), IAAAffine2(scale=(0.8, 1.8), rotate=(-20, 20), shear=(-0.03, 0.03)), A.PadIfNeeded(min_height=out_size, min_width=out_size), A.RandomCrop(height=out_size, width=out_size), A.HorizontalFlip(), A.CLAHE(), A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2), A.HueSaturationValue(hue_shift_limit=5, sat_shift_limit=30, val_shift_limit=5), A.ToFloat()])
    elif transform_variant == 'non_space_transform':
        transform = A.Compose([A.CLAHE(), A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2), A.HueSaturationValue(hue_shift_limit=5, sat_shift_limit=30, val_shift_limit=5), A.ToFloat()])
    elif transform_variant == 'no_augs':
        transform = A.Compose([A.ToFloat()])
    else:
        raise ValueError(f'Unexpected transform_variant {transform_variant}')
    return transform

def make_default_train_dataloader(indir, kind='default', out_size=512, mask_gen_kwargs=None, transform_variant='default', mask_generator_kind='mixed', dataloader_kwargs=None, ddp_kwargs=None, **kwargs):
    LOGGER.info(f'Make train dataloader {kind} from {indir}. Using mask generator={mask_generator_kind}')
    mask_generator = get_mask_generator(kind=mask_generator_kind, kwargs=mask_gen_kwargs)
    transform = get_transforms(transform_variant, out_size)
    if kind == 'default':
        dataset = InpaintingTrainDataset(indir=indir, mask_generator=mask_generator, transform=transform, **kwargs)
    elif kind == 'default_web':
        dataset = InpaintingTrainWebDataset(indir=indir, mask_generator=mask_generator, transform=transform, **kwargs)
    elif kind == 'img_with_segm':
        dataset = ImgSegmentationDataset(indir=indir, mask_generator=mask_generator, transform=transform, out_size=out_size, **kwargs)
    else:
        raise ValueError(f'Unknown train dataset kind {kind}')
    if dataloader_kwargs is None:
        dataloader_kwargs = {}
    is_dataset_only_iterable = kind in ('default_web',)
    if ddp_kwargs is not None and (not is_dataset_only_iterable):
        dataloader_kwargs['shuffle'] = False
        dataloader_kwargs['sampler'] = DistributedSampler(dataset, **ddp_kwargs)
    if is_dataset_only_iterable and 'shuffle' in dataloader_kwargs:
        with open_dict(dataloader_kwargs):
            del dataloader_kwargs['shuffle']
    dataloader = DataLoader(dataset, **dataloader_kwargs)
    return dataloader

def make_default_val_dataset(indir, kind='default', out_size=512, transform_variant='default', **kwargs):
    if OmegaConf.is_list(indir) or isinstance(indir, (tuple, list)):
        return ConcatDataset([make_default_val_dataset(idir, kind=kind, out_size=out_size, transform_variant=transform_variant, **kwargs) for idir in indir])
    LOGGER.info(f'Make val dataloader {kind} from {indir}')
    mask_generator = get_mask_generator(kind=kwargs.get('mask_generator_kind'), kwargs=kwargs.get('mask_gen_kwargs'))
    if transform_variant is not None:
        transform = get_transforms(transform_variant, out_size)
    if kind == 'default':
        dataset = InpaintingEvaluationDataset(indir, **kwargs)
    elif kind == 'our_eval':
        dataset = OurInpaintingEvaluationDataset(indir, **kwargs)
    elif kind == 'img_with_segm':
        dataset = ImgSegmentationDataset(indir=indir, mask_generator=mask_generator, transform=transform, out_size=out_size, **kwargs)
    elif kind == 'online':
        dataset = InpaintingEvalOnlineDataset(indir=indir, mask_generator=mask_generator, transform=transform, out_size=out_size, **kwargs)
    else:
        raise ValueError(f'Unknown val dataset kind {kind}')
    return dataset

def make_optimizer(parameters, kind='adamw', **kwargs):
    if kind == 'adam':
        optimizer_class = torch.optim.Adam
    elif kind == 'adamw':
        optimizer_class = torch.optim.AdamW
    else:
        raise ValueError(f'Unknown optimizer kind {kind}')
    return optimizer_class(parameters, **kwargs)

def get_training_model_class(kind):
    if kind == 'default':
        return DefaultInpaintingTrainingModule
    raise ValueError(f'Unknown trainer module {kind}')

def get_conv_block_ctor(kind='default'):
    if not isinstance(kind, str):
        return kind
    if kind == 'default':
        return nn.Conv2d
    if kind == 'depthwise':
        return DepthWiseSeperableConv
    if kind == 'multidilated':
        return MultidilatedConv
    raise ValueError(f'Unknown convolutional block kind {kind}')

def get_norm_layer(kind='bn'):
    if not isinstance(kind, str):
        return kind
    if kind == 'bn':
        return nn.BatchNorm2d
    if kind == 'in':
        return nn.InstanceNorm2d
    raise ValueError(f'Unknown norm block kind {kind}')

def make_generator(config, kind, **kwargs):
    logging.info(f'Make generator {kind}')
    if kind == 'pix2pixhd_multidilated':
        return MultiDilatedGlobalGenerator(**kwargs)
    if kind == 'pix2pixhd_global':
        return GlobalGenerator(**kwargs)
    if kind == 'ffc_resnet':
        return FFCResNetGenerator(**kwargs)
    raise ValueError(f'Unknown generator kind {kind}')

def make_discriminator(kind, **kwargs):
    logging.info(f'Make discriminator {kind}')
    if kind == 'pix2pixhd_nlayer_multidilated':
        return MultidilatedNLayerDiscriminator(**kwargs)
    if kind == 'pix2pixhd_nlayer':
        return NLayerDiscriminator(**kwargs)
    raise ValueError(f'Unknown discriminator kind {kind}')

class GlobalGeneratorFromSuperChannels(nn.Module):

    def __init__(self, input_nc, output_nc, n_downsampling, n_blocks, super_channels, norm_layer='bn', padding_type='reflect', add_out_act=True):
        super().__init__()
        self.n_downsampling = n_downsampling
        norm_layer = get_norm_layer(norm_layer)
        if type(norm_layer) == functools.partial:
            use_bias = norm_layer.func == nn.InstanceNorm2d
        else:
            use_bias = norm_layer == nn.InstanceNorm2d
        channels = self.convert_super_channels(super_channels)
        self.channels = channels
        model = [nn.ReflectionPad2d(3), nn.Conv2d(input_nc, channels[0], kernel_size=7, padding=0, bias=use_bias), norm_layer(channels[0]), nn.ReLU(True)]
        for i in range(n_downsampling):
            mult = 2 ** i
            model += [nn.Conv2d(channels[0 + i], channels[1 + i], kernel_size=3, stride=2, padding=1, bias=use_bias), norm_layer(channels[1 + i]), nn.ReLU(True)]
        mult = 2 ** n_downsampling
        n_blocks1 = n_blocks // 3
        n_blocks2 = n_blocks1
        n_blocks3 = n_blocks - n_blocks1 - n_blocks2
        for i in range(n_blocks1):
            c = n_downsampling
            dim = channels[c]
            model += [ResnetBlock(dim, padding_type=padding_type, norm_layer=norm_layer)]
        for i in range(n_blocks2):
            c = n_downsampling + 1
            dim = channels[c]
            kwargs = {}
            if i == 0:
                kwargs = {'in_dim': channels[c - 1]}
            model += [ResnetBlock(dim, padding_type=padding_type, norm_layer=norm_layer, **kwargs)]
        for i in range(n_blocks3):
            c = n_downsampling + 2
            dim = channels[c]
            kwargs = {}
            if i == 0:
                kwargs = {'in_dim': channels[c - 1]}
            model += [ResnetBlock(dim, padding_type=padding_type, norm_layer=norm_layer, **kwargs)]
        for i in range(n_downsampling):
            mult = 2 ** (n_downsampling - i)
            model += [nn.ConvTranspose2d(channels[n_downsampling + 3 + i], channels[n_downsampling + 3 + i + 1], kernel_size=3, stride=2, padding=1, output_padding=1, bias=use_bias), norm_layer(channels[n_downsampling + 3 + i + 1]), nn.ReLU(True)]
        model += [nn.ReflectionPad2d(3)]
        model += [nn.Conv2d(channels[2 * n_downsampling + 3], output_nc, kernel_size=7, padding=0)]
        if add_out_act:
            model.append(get_activation('tanh' if add_out_act is True else add_out_act))
        self.model = nn.Sequential(*model)

    def convert_super_channels(self, super_channels):
        n_downsampling = self.n_downsampling
        result = []
        cnt = 0
        if n_downsampling == 2:
            N1 = 10
        elif n_downsampling == 3:
            N1 = 13
        else:
            raise NotImplementedError
        for i in range(0, N1):
            if i in [1, 4, 7, 10]:
                channel = super_channels[cnt] * 2 ** cnt
                config = {'channel': channel}
                result.append(channel)
                logging.info(f'Downsample channels {result[-1]}')
                cnt += 1
        for i in range(3):
            for counter, j in enumerate(range(N1 + i * 3, N1 + 3 + i * 3)):
                if len(super_channels) == 6:
                    channel = super_channels[3] * 4
                else:
                    channel = super_channels[i + 3] * 4
                config = {'channel': channel}
                if counter == 0:
                    result.append(channel)
                    logging.info(f'Bottleneck channels {result[-1]}')
        cnt = 2
        for i in range(N1 + 9, N1 + 21):
            if i in [22, 25, 28]:
                cnt -= 1
                if len(super_channels) == 6:
                    channel = super_channels[5 - cnt] * 2 ** cnt
                else:
                    channel = super_channels[7 - cnt] * 2 ** cnt
                result.append(int(channel))
                logging.info(f'Upsample channels {result[-1]}')
        return result

    def forward(self, input):
        return self.model(input)

def convert_super_channels(self, super_channels):
    n_downsampling = self.n_downsampling
    result = []
    cnt = 0
    if n_downsampling == 2:
        N1 = 10
    elif n_downsampling == 3:
        N1 = 13
    else:
        raise NotImplementedError
    for i in range(0, N1):
        if i in [1, 4, 7, 10]:
            channel = super_channels[cnt] * 2 ** cnt
            config = {'channel': channel}
            result.append(channel)
            logging.info(f'Downsample channels {result[-1]}')
            cnt += 1
    for i in range(3):
        for counter, j in enumerate(range(N1 + i * 3, N1 + 3 + i * 3)):
            if len(super_channels) == 6:
                channel = super_channels[3] * 4
            else:
                channel = super_channels[i + 3] * 4
            config = {'channel': channel}
            if counter == 0:
                result.append(channel)
                logging.info(f'Bottleneck channels {result[-1]}')
    cnt = 2
    for i in range(N1 + 9, N1 + 21):
        if i in [22, 25, 28]:
            cnt -= 1
            if len(super_channels) == 6:
                channel = super_channels[5 - cnt] * 2 ** cnt
            else:
                channel = super_channels[7 - cnt] * 2 ** cnt
            result.append(int(channel))
            logging.info(f'Upsample channels {result[-1]}')
    return result

def make_visualizer(kind, **kwargs):
    logging.info(f'Make visualizer {kind}')
    if kind == 'directory':
        return DirectoryVisualizer(**kwargs)
    if kind == 'noop':
        return NoopVisualizer()
    raise ValueError(f'Unknown visualizer kind {kind}')

def make_evaluator(kind='default', ssim=True, lpips=True, fid=True, integral_kind=None, **kwargs):
    logging.info(f'Make evaluator {kind}')
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    metrics = {}
    if ssim:
        metrics['ssim'] = SSIMScore()
    if lpips:
        metrics['lpips'] = LPIPSScore()
    if fid:
        metrics['fid'] = FIDScore().to(device)
    if integral_kind is None:
        integral_func = None
    elif integral_kind == 'ssim_fid100_f1':
        integral_func = ssim_fid100_f1
    elif integral_kind == 'lpips_fid100_f1':
        integral_func = lpips_fid100_f1
    else:
        raise ValueError(f'Unexpected integral_kind={integral_kind}')
    if kind == 'default':
        return InpaintingEvaluatorOnline(scores=metrics, integral_func=integral_func, integral_title=integral_kind, **kwargs)

def fid_inception_v3():
    """Build pretrained Inception model for FID computation

    The Inception model for FID computation uses a different set of weights
    and has a slightly different structure than torchvision's Inception.

    This method first constructs torchvision's Inception and then patches the
    necessary parts that are different in the FID Inception model.
    """
    LOGGER.info('fid_inception_v3 called')
    inception = models.inception_v3(num_classes=1008, aux_logits=False, pretrained=False)
    LOGGER.info('models.inception_v3 done')
    inception.Mixed_5b = FIDInceptionA(192, pool_features=32)
    inception.Mixed_5c = FIDInceptionA(256, pool_features=64)
    inception.Mixed_5d = FIDInceptionA(288, pool_features=64)
    inception.Mixed_6b = FIDInceptionC(768, channels_7x7=128)
    inception.Mixed_6c = FIDInceptionC(768, channels_7x7=160)
    inception.Mixed_6d = FIDInceptionC(768, channels_7x7=160)
    inception.Mixed_6e = FIDInceptionC(768, channels_7x7=192)
    inception.Mixed_7b = FIDInceptionE_1(1280)
    inception.Mixed_7c = FIDInceptionE_2(2048)
    LOGGER.info('fid_inception_v3 patching done')
    state_dict = load_state_dict_from_url(FID_WEIGHTS_URL, progress=True)
    LOGGER.info('fid_inception_v3 weights downloaded')
    inception.load_state_dict(state_dict)
    LOGGER.info('fid_inception_v3 weights loaded into model')
    return inception

class SegmentationModule(nn.Module):

    def __init__(self, weights_path, num_classes=150, arch_encoder='resnet50dilated', drop_last_conv=False, net_enc=None, net_dec=None, encode=None, use_default_normalization=False, return_feature_maps=False, return_feature_maps_level=3, return_feature_maps_only=True, **kwargs):
        super().__init__()
        self.weights_path = weights_path
        self.drop_last_conv = drop_last_conv
        self.arch_encoder = arch_encoder
        if self.arch_encoder == 'resnet50dilated':
            self.arch_decoder = 'ppm_deepsup'
            self.fc_dim = 2048
        elif self.arch_encoder == 'mobilenetv2dilated':
            self.arch_decoder = 'c1_deepsup'
            self.fc_dim = 320
        else:
            raise NotImplementedError(f'No such arch_encoder={self.arch_encoder}')
        model_builder_kwargs = dict(arch_encoder=self.arch_encoder, arch_decoder=self.arch_decoder, fc_dim=self.fc_dim, drop_last_conv=drop_last_conv, weights_path=self.weights_path)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.encoder = ModelBuilder.get_encoder(**model_builder_kwargs) if net_enc is None else net_enc
        self.decoder = ModelBuilder.get_decoder(**model_builder_kwargs) if net_dec is None else net_dec
        self.use_default_normalization = use_default_normalization
        self.default_normalization = NormalizeTensor(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        self.encode = encode
        self.return_feature_maps = return_feature_maps
        assert 0 <= return_feature_maps_level <= 3
        self.return_feature_maps_level = return_feature_maps_level

    def normalize_input(self, tensor):
        if tensor.min() < 0 or tensor.max() > 1:
            raise ValueError('Tensor should be 0..1 before using normalize_input')
        return self.default_normalization(tensor)

    @property
    def feature_maps_channels(self):
        return 256 * 2 ** self.return_feature_maps_level

    def forward(self, img_data, segSize=None):
        if segSize is None:
            raise NotImplementedError('Please pass segSize param. By default: (300, 300)')
        fmaps = self.encoder(img_data, return_feature_maps=True)
        pred = self.decoder(fmaps, segSize=segSize)
        if self.return_feature_maps:
            return (pred, fmaps)
        return pred

    def multi_mask_from_multiclass(self, pred, classes):

        def isin(ar1, ar2):
            return (ar1[..., None] == ar2).any(-1).float()
        return isin(pred, torch.LongTensor(classes).to(self.device))

    @staticmethod
    def multi_mask_from_multiclass_probs(scores, classes):
        res = None
        for c in classes:
            if res is None:
                res = scores[:, c]
            else:
                res += scores[:, c]
        return res

    def predict(self, tensor, imgSizes=(-1,), segSize=None):
        """Entry-point for segmentation. Use this methods instead of forward
        Arguments:
            tensor {torch.Tensor} -- BCHW
        Keyword Arguments:
            imgSizes {tuple or list} -- imgSizes for segmentation input.
                default: (300, 450)
                original implementation: (300, 375, 450, 525, 600)

        """
        if segSize is None:
            segSize = tensor.shape[-2:]
        segSize = (tensor.shape[2], tensor.shape[3])
        with torch.no_grad():
            if self.use_default_normalization:
                tensor = self.normalize_input(tensor)
            scores = torch.zeros(1, NUM_CLASS, segSize[0], segSize[1]).to(self.device)
            features = torch.zeros(1, self.feature_maps_channels, segSize[0], segSize[1]).to(self.device)
            result = []
            for img_size in imgSizes:
                if img_size != -1:
                    img_data = F.interpolate(tensor.clone(), size=img_size)
                else:
                    img_data = tensor.clone()
                if self.return_feature_maps:
                    pred_current, fmaps = self.forward(img_data, segSize=segSize)
                else:
                    pred_current = self.forward(img_data, segSize=segSize)
                result.append(pred_current)
                scores = scores + pred_current / len(imgSizes)
                if self.return_feature_maps:
                    features = features + F.interpolate(fmaps[self.return_feature_maps_level], size=segSize) / len(imgSizes)
            _, pred = torch.max(scores, dim=1)
            if self.return_feature_maps:
                return features
            return (pred, result)

    def get_edges(self, t):
        edge = torch.cuda.ByteTensor(t.size()).zero_()
        edge[:, :, :, 1:] = edge[:, :, :, 1:] | (t[:, :, :, 1:] != t[:, :, :, :-1])
        edge[:, :, :, :-1] = edge[:, :, :, :-1] | (t[:, :, :, 1:] != t[:, :, :, :-1])
        edge[:, :, 1:, :] = edge[:, :, 1:, :] | (t[:, :, 1:, :] != t[:, :, :-1, :])
        edge[:, :, :-1, :] = edge[:, :, :-1, :] | (t[:, :, 1:, :] != t[:, :, :-1, :])
        if True:
            return edge.half()
        return edge.float()

def normalize_input(self, tensor):
    if tensor.min() < 0 or tensor.max() > 1:
        raise ValueError('Tensor should be 0..1 before using normalize_input')
    return self.default_normalization(tensor)

class SynchronizedBatchNorm1d(_SynchronizedBatchNorm):
    """Applies Synchronized Batch Normalization over a 2d or 3d input that is seen as a
    mini-batch.

    .. math::

        y = \\frac{x - mean[x]}{ \\sqrt{Var[x] + \\epsilon}} * gamma + beta

    This module differs from the built-in PyTorch BatchNorm1d as the mean and
    standard-deviation are reduced across all devices during training.

    For example, when one uses `nn.DataParallel` to wrap the network during
    training, PyTorch's implementation normalize the tensor on each device using
    the statistics only on that device, which accelerated the computation and
    is also easy to implement, but the statistics might be inaccurate.
    Instead, in this synchronized version, the statistics will be computed
    over all training samples distributed on multiple devices.
    
    Note that, for one-GPU or CPU-only case, this module behaves exactly same
    as the built-in PyTorch implementation.

    The mean and standard-deviation are calculated per-dimension over
    the mini-batches and gamma and beta are learnable parameter vectors
    of size C (where C is the input size).

    During training, this layer keeps a running estimate of its computed mean
    and variance. The running sum is kept with a default momentum of 0.1.

    During evaluation, this running mean/variance is used for normalization.

    Because the BatchNorm is done over the `C` dimension, computing statistics
    on `(N, L)` slices, it's common terminology to call this Temporal BatchNorm

    Args:
        num_features: num_features from an expected input of size
            `batch_size x num_features [x width]`
        eps: a value added to the denominator for numerical stability.
            Default: 1e-5
        momentum: the value used for the running_mean and running_var
            computation. Default: 0.1
        affine: a boolean value that when set to ``True``, gives the layer learnable
            affine parameters. Default: ``True``

    Shape:
        - Input: :math:`(N, C)` or :math:`(N, C, L)`
        - Output: :math:`(N, C)` or :math:`(N, C, L)` (same shape as input)

    Examples:
        >>> # With Learnable Parameters
        >>> m = SynchronizedBatchNorm1d(100)
        >>> # Without Learnable Parameters
        >>> m = SynchronizedBatchNorm1d(100, affine=False)
        >>> input = torch.autograd.Variable(torch.randn(20, 100))
        >>> output = m(input)
    """

    def _check_input_dim(self, input):
        if input.dim() != 2 and input.dim() != 3:
            raise ValueError('expected 2D or 3D input (got {}D input)'.format(input.dim()))
        super(SynchronizedBatchNorm1d, self)._check_input_dim(input)

def _check_input_dim(self, input):
    if input.dim() != 2 and input.dim() != 3:
        raise ValueError('expected 2D or 3D input (got {}D input)'.format(input.dim()))
    super(SynchronizedBatchNorm1d, self)._check_input_dim(input)

class SynchronizedBatchNorm2d(_SynchronizedBatchNorm):
    """Applies Batch Normalization over a 4d input that is seen as a mini-batch
    of 3d inputs

    .. math::

        y = \\frac{x - mean[x]}{ \\sqrt{Var[x] + \\epsilon}} * gamma + beta

    This module differs from the built-in PyTorch BatchNorm2d as the mean and
    standard-deviation are reduced across all devices during training.

    For example, when one uses `nn.DataParallel` to wrap the network during
    training, PyTorch's implementation normalize the tensor on each device using
    the statistics only on that device, which accelerated the computation and
    is also easy to implement, but the statistics might be inaccurate.
    Instead, in this synchronized version, the statistics will be computed
    over all training samples distributed on multiple devices.
    
    Note that, for one-GPU or CPU-only case, this module behaves exactly same
    as the built-in PyTorch implementation.

    The mean and standard-deviation are calculated per-dimension over
    the mini-batches and gamma and beta are learnable parameter vectors
    of size C (where C is the input size).

    During training, this layer keeps a running estimate of its computed mean
    and variance. The running sum is kept with a default momentum of 0.1.

    During evaluation, this running mean/variance is used for normalization.

    Because the BatchNorm is done over the `C` dimension, computing statistics
    on `(N, H, W)` slices, it's common terminology to call this Spatial BatchNorm

    Args:
        num_features: num_features from an expected input of
            size batch_size x num_features x height x width
        eps: a value added to the denominator for numerical stability.
            Default: 1e-5
        momentum: the value used for the running_mean and running_var
            computation. Default: 0.1
        affine: a boolean value that when set to ``True``, gives the layer learnable
            affine parameters. Default: ``True``

    Shape:
        - Input: :math:`(N, C, H, W)`
        - Output: :math:`(N, C, H, W)` (same shape as input)

    Examples:
        >>> # With Learnable Parameters
        >>> m = SynchronizedBatchNorm2d(100)
        >>> # Without Learnable Parameters
        >>> m = SynchronizedBatchNorm2d(100, affine=False)
        >>> input = torch.autograd.Variable(torch.randn(20, 100, 35, 45))
        >>> output = m(input)
    """

    def _check_input_dim(self, input):
        if input.dim() != 4:
            raise ValueError('expected 4D input (got {}D input)'.format(input.dim()))
        super(SynchronizedBatchNorm2d, self)._check_input_dim(input)

def _check_input_dim(self, input):
    if input.dim() != 4:
        raise ValueError('expected 4D input (got {}D input)'.format(input.dim()))
    super(SynchronizedBatchNorm2d, self)._check_input_dim(input)

class SynchronizedBatchNorm3d(_SynchronizedBatchNorm):
    """Applies Batch Normalization over a 5d input that is seen as a mini-batch
    of 4d inputs

    .. math::

        y = \\frac{x - mean[x]}{ \\sqrt{Var[x] + \\epsilon}} * gamma + beta

    This module differs from the built-in PyTorch BatchNorm3d as the mean and
    standard-deviation are reduced across all devices during training.

    For example, when one uses `nn.DataParallel` to wrap the network during
    training, PyTorch's implementation normalize the tensor on each device using
    the statistics only on that device, which accelerated the computation and
    is also easy to implement, but the statistics might be inaccurate.
    Instead, in this synchronized version, the statistics will be computed
    over all training samples distributed on multiple devices.
    
    Note that, for one-GPU or CPU-only case, this module behaves exactly same
    as the built-in PyTorch implementation.

    The mean and standard-deviation are calculated per-dimension over
    the mini-batches and gamma and beta are learnable parameter vectors
    of size C (where C is the input size).

    During training, this layer keeps a running estimate of its computed mean
    and variance. The running sum is kept with a default momentum of 0.1.

    During evaluation, this running mean/variance is used for normalization.

    Because the BatchNorm is done over the `C` dimension, computing statistics
    on `(N, D, H, W)` slices, it's common terminology to call this Volumetric BatchNorm
    or Spatio-temporal BatchNorm

    Args:
        num_features: num_features from an expected input of
            size batch_size x num_features x depth x height x width
        eps: a value added to the denominator for numerical stability.
            Default: 1e-5
        momentum: the value used for the running_mean and running_var
            computation. Default: 0.1
        affine: a boolean value that when set to ``True``, gives the layer learnable
            affine parameters. Default: ``True``

    Shape:
        - Input: :math:`(N, C, D, H, W)`
        - Output: :math:`(N, C, D, H, W)` (same shape as input)

    Examples:
        >>> # With Learnable Parameters
        >>> m = SynchronizedBatchNorm3d(100)
        >>> # Without Learnable Parameters
        >>> m = SynchronizedBatchNorm3d(100, affine=False)
        >>> input = torch.autograd.Variable(torch.randn(20, 100, 35, 45, 10))
        >>> output = m(input)
    """

    def _check_input_dim(self, input):
        if input.dim() != 5:
            raise ValueError('expected 5D input (got {}D input)'.format(input.dim()))
        super(SynchronizedBatchNorm3d, self)._check_input_dim(input)

def _check_input_dim(self, input):
    if input.dim() != 5:
        raise ValueError('expected 5D input (got {}D input)'.format(input.dim()))
    super(SynchronizedBatchNorm3d, self)._check_input_dim(input)

class Tracker:
    """Wraps the tracker for evaluation and running purposes.
    args:
        name: Name of tracking method.
        parameter_name: Name of parameter file.
        run_id: The run id.
        display_name: Name to be displayed in the result plots.
    """

    def __init__(self, name: str, parameter_name: str, dataset_name: str, run_id: int=None, display_name: str=None, result_only=False):
        assert run_id is None or isinstance(run_id, int)
        self.name = name
        self.parameter_name = parameter_name
        self.dataset_name = dataset_name
        self.run_id = run_id
        self.display_name = display_name
        tracker_module_abspath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tracker', '%s.py' % self.name))
        if os.path.isfile(tracker_module_abspath):
            tracker_module = importlib.import_module('lib.test.tracker.{}'.format(self.name))
            self.tracker_class = tracker_module.get_tracker_class()
        else:
            self.tracker_class = None

    def create_tracker(self, params):
        tracker = self.tracker_class(params, self.dataset_name)
        return tracker

    def run_sequence(self, seq, debug=None):
        """Run tracker on sequence.
        args:
            seq: Sequence to run the tracker on.
            visualization: Set visualization flag (None means default value specified in the parameters).
            debug: Set debug level (None means default value specified in the parameters).
            multiobj_mode: Which mode to use for multiple objects.
        """
        params = self.get_parameters()
        debug_ = debug
        if debug is None:
            debug_ = getattr(params, 'debug', 0)
        params.debug = debug_
        init_info = seq.init_info()
        tracker = self.create_tracker(params)
        output = self._track_sequence(tracker, seq, init_info)
        return output

    def _track_sequence(self, tracker, seq, init_info):
        output = {'target_bbox': [], 'time': []}
        if tracker.params.save_all_boxes:
            output['all_boxes'] = []
            output['all_scores'] = []

        def _store_outputs(tracker_out: dict, defaults=None):
            defaults = {} if defaults is None else defaults
            for key in output.keys():
                val = tracker_out.get(key, defaults.get(key, None))
                if key in tracker_out or val is not None:
                    output[key].append(val)
        image = self._read_image(seq.frames[0])
        start_time = time.time()
        out = tracker.initialize(image, init_info)
        if out is None:
            out = {}
        prev_output = OrderedDict(out)
        init_default = {'target_bbox': init_info.get('init_bbox'), 'time': time.time() - start_time}
        if tracker.params.save_all_boxes:
            init_default['all_boxes'] = out['all_boxes']
            init_default['all_scores'] = out['all_scores']
        _store_outputs(out, init_default)
        for frame_num, frame_path in enumerate(seq.frames[1:], start=1):
            image = self._read_image(frame_path)
            start_time = time.time()
            info = seq.frame_info(frame_num)
            info['previous_output'] = prev_output
            if len(seq.ground_truth_rect) > 1:
                info['gt_bbox'] = seq.ground_truth_rect[frame_num]
            out = tracker.track(image, info)
            prev_output = OrderedDict(out)
            _store_outputs(out, {'time': time.time() - start_time})
        for key in ['target_bbox', 'all_boxes', 'all_scores']:
            if key in output and len(output[key]) <= 1:
                output.pop(key)
        return output

    def run_video(self, videofilepath, optional_box=None, debug=None, visdom_info=None, save_results=False):
        """Run the tracker with the vieofile.
        args:
            debug: Debug level.
        """
        params = self.get_parameters()
        debug_ = debug
        if debug is None:
            debug_ = getattr(params, 'debug', 0)
        params.debug = debug_
        params.tracker_name = self.name
        params.param_name = self.parameter_name
        multiobj_mode = getattr(params, 'multiobj_mode', getattr(self.tracker_class, 'multiobj_mode', 'default'))
        if multiobj_mode == 'default':
            tracker = self.create_tracker(params)
        elif multiobj_mode == 'parallel':
            tracker = MultiObjectWrapper(self.tracker_class, params, self.visdom, fast_load=True)
        else:
            raise ValueError('Unknown multi object mode {}'.format(multiobj_mode))
        assert os.path.isfile(videofilepath), 'Invalid param {}'.format(videofilepath)
        ', videofilepath must be a valid videofile'
        output_boxes = []
        cap = cv.VideoCapture(videofilepath)
        display_name = 'Display: ' + tracker.params.tracker_name
        cv.namedWindow(display_name, cv.WINDOW_NORMAL | cv.WINDOW_KEEPRATIO)
        cv.resizeWindow(display_name, 960, 720)
        success, frame = cap.read()
        cv.imshow(display_name, frame)

        def _build_init_info(box):
            return {'init_bbox': box}
        if success is not True:
            print('Read frame from {} failed.'.format(videofilepath))
            exit(-1)
        if optional_box is not None:
            assert isinstance(optional_box, (list, tuple))
            assert len(optional_box) == 4, "valid box's foramt is [x,y,w,h]"
            tracker.initialize(frame, _build_init_info(optional_box))
            output_boxes.append(optional_box)
        else:
            while True:
                frame_disp = frame.copy()
                cv.putText(frame_disp, 'Select target ROI and press ENTER', (20, 30), cv.FONT_HERSHEY_COMPLEX_SMALL, 1.5, (0, 0, 0), 1)
                x, y, w, h = cv.selectROI(display_name, frame_disp, fromCenter=False)
                init_state = [x, y, w, h]
                tracker.initialize(frame, _build_init_info(init_state))
                output_boxes.append(init_state)
                break
        while True:
            ret, frame = cap.read()
            if frame is None:
                break
            frame_disp = frame.copy()
            out = tracker.track(frame)
            state = [int(s) for s in out['target_bbox']]
            output_boxes.append(state)
            cv.rectangle(frame_disp, (state[0], state[1]), (state[2] + state[0], state[3] + state[1]), (0, 255, 0), 5)
            font_color = (0, 0, 0)
            cv.putText(frame_disp, 'Tracking!', (20, 30), cv.FONT_HERSHEY_COMPLEX_SMALL, 1, font_color, 1)
            cv.putText(frame_disp, 'Press r to reset', (20, 55), cv.FONT_HERSHEY_COMPLEX_SMALL, 1, font_color, 1)
            cv.putText(frame_disp, 'Press q to quit', (20, 80), cv.FONT_HERSHEY_COMPLEX_SMALL, 1, font_color, 1)
            cv.imshow(display_name, frame_disp)
            key = cv.waitKey(1)
            if key == ord('q'):
                break
            elif key == ord('r'):
                ret, frame = cap.read()
                frame_disp = frame.copy()
                cv.putText(frame_disp, 'Select target ROI and press ENTER', (20, 30), cv.FONT_HERSHEY_COMPLEX_SMALL, 1.5, (0, 0, 0), 1)
                cv.imshow(display_name, frame_disp)
                x, y, w, h = cv.selectROI(display_name, frame_disp, fromCenter=False)
                init_state = [x, y, w, h]
                tracker.initialize(frame, _build_init_info(init_state))
                output_boxes.append(init_state)
        cap.release()
        cv.destroyAllWindows()
        if save_results:
            if not os.path.exists(self.results_dir):
                os.makedirs(self.results_dir)
            video_name = Path(videofilepath).stem
            base_results_path = os.path.join(self.results_dir, 'video_{}'.format(video_name))
            tracked_bb = np.array(output_boxes).astype(int)
            bbox_file = '{}.txt'.format(base_results_path)
            np.savetxt(bbox_file, tracked_bb, delimiter='\t', fmt='%d')

    def get_parameters(self):
        """Get parameters."""
        param_module = importlib.import_module('lib.test.parameter.{}'.format(self.name))
        params = param_module.parameters(self.parameter_name)
        return params

    def _read_image(self, image_file: str):
        if isinstance(image_file, str):
            im = cv.imread(image_file)
            return cv.cvtColor(im, cv.COLOR_BGR2RGB)
        elif isinstance(image_file, list) and len(image_file) == 2:
            return decode_img(image_file[0], image_file[1])
        else:
            raise ValueError('type of image_file should be str or list')

def _read_image(self, image_file: str):
    if isinstance(image_file, str):
        im = cv.imread(image_file)
        return cv.cvtColor(im, cv.COLOR_BGR2RGB)
    elif isinstance(image_file, list) and len(image_file) == 2:
        return decode_img(image_file[0], image_file[1])
    else:
        raise ValueError('type of image_file should be str or list')

def imresize(img, scale, antialiasing=True):
    need_squeeze = True if img.dim() == 2 else False
    if need_squeeze:
        img.unsqueeze_(0)
    in_C, in_H, in_W = img.size()
    out_C, out_H, out_W = (in_C, math.ceil(in_H * scale), math.ceil(in_W * scale))
    kernel_width = 4
    kernel = 'cubic'
    weights_H, indices_H, sym_len_Hs, sym_len_He = calculate_weights_indices(in_H, out_H, scale, kernel, kernel_width, antialiasing)
    weights_W, indices_W, sym_len_Ws, sym_len_We = calculate_weights_indices(in_W, out_W, scale, kernel, kernel_width, antialiasing)
    img_aug = torch.FloatTensor(in_C, in_H + sym_len_Hs + sym_len_He, in_W)
    img_aug.narrow(1, sym_len_Hs, in_H).copy_(img)
    sym_patch = img[:, :sym_len_Hs, :]
    inv_idx = torch.arange(sym_patch.size(1) - 1, -1, -1).long()
    sym_patch_inv = sym_patch.index_select(1, inv_idx)
    img_aug.narrow(1, 0, sym_len_Hs).copy_(sym_patch_inv)
    sym_patch = img[:, -sym_len_He:, :]
    inv_idx = torch.arange(sym_patch.size(1) - 1, -1, -1).long()
    sym_patch_inv = sym_patch.index_select(1, inv_idx)
    img_aug.narrow(1, sym_len_Hs + in_H, sym_len_He).copy_(sym_patch_inv)
    out_1 = torch.FloatTensor(in_C, out_H, in_W)
    kernel_width = weights_H.size(1)
    for i in range(out_H):
        idx = int(indices_H[i][0])
        for j in range(out_C):
            out_1[j, i, :] = img_aug[j, idx:idx + kernel_width, :].transpose(0, 1).mv(weights_H[i])
    out_1_aug = torch.FloatTensor(in_C, out_H, in_W + sym_len_Ws + sym_len_We)
    out_1_aug.narrow(2, sym_len_Ws, in_W).copy_(out_1)
    sym_patch = out_1[:, :, :sym_len_Ws]
    inv_idx = torch.arange(sym_patch.size(2) - 1, -1, -1).long()
    sym_patch_inv = sym_patch.index_select(2, inv_idx)
    out_1_aug.narrow(2, 0, sym_len_Ws).copy_(sym_patch_inv)
    sym_patch = out_1[:, :, -sym_len_We:]
    inv_idx = torch.arange(sym_patch.size(2) - 1, -1, -1).long()
    sym_patch_inv = sym_patch.index_select(2, inv_idx)
    out_1_aug.narrow(2, sym_len_Ws + in_W, sym_len_We).copy_(sym_patch_inv)
    out_2 = torch.FloatTensor(in_C, out_H, out_W)
    kernel_width = weights_W.size(1)
    for i in range(out_W):
        idx = int(indices_W[i][0])
        for j in range(out_C):
            out_2[j, :, i] = out_1_aug[j, :, idx:idx + kernel_width].mv(weights_W[i])
    if need_squeeze:
        out_2.squeeze_()
    return out_2

def imresize_np(img, scale, antialiasing=True):
    img = torch.from_numpy(img)
    need_squeeze = True if img.dim() == 2 else False
    if need_squeeze:
        img.unsqueeze_(2)
    in_H, in_W, in_C = img.size()
    out_C, out_H, out_W = (in_C, math.ceil(in_H * scale), math.ceil(in_W * scale))
    kernel_width = 4
    kernel = 'cubic'
    weights_H, indices_H, sym_len_Hs, sym_len_He = calculate_weights_indices(in_H, out_H, scale, kernel, kernel_width, antialiasing)
    weights_W, indices_W, sym_len_Ws, sym_len_We = calculate_weights_indices(in_W, out_W, scale, kernel, kernel_width, antialiasing)
    img_aug = torch.FloatTensor(in_H + sym_len_Hs + sym_len_He, in_W, in_C)
    img_aug.narrow(0, sym_len_Hs, in_H).copy_(img)
    sym_patch = img[:sym_len_Hs, :, :]
    inv_idx = torch.arange(sym_patch.size(0) - 1, -1, -1).long()
    sym_patch_inv = sym_patch.index_select(0, inv_idx)
    img_aug.narrow(0, 0, sym_len_Hs).copy_(sym_patch_inv)
    sym_patch = img[-sym_len_He:, :, :]
    inv_idx = torch.arange(sym_patch.size(0) - 1, -1, -1).long()
    sym_patch_inv = sym_patch.index_select(0, inv_idx)
    img_aug.narrow(0, sym_len_Hs + in_H, sym_len_He).copy_(sym_patch_inv)
    out_1 = torch.FloatTensor(out_H, in_W, in_C)
    kernel_width = weights_H.size(1)
    for i in range(out_H):
        idx = int(indices_H[i][0])
        for j in range(out_C):
            out_1[i, :, j] = img_aug[idx:idx + kernel_width, :, j].transpose(0, 1).mv(weights_H[i])
    out_1_aug = torch.FloatTensor(out_H, in_W + sym_len_Ws + sym_len_We, in_C)
    out_1_aug.narrow(1, sym_len_Ws, in_W).copy_(out_1)
    sym_patch = out_1[:, :sym_len_Ws, :]
    inv_idx = torch.arange(sym_patch.size(1) - 1, -1, -1).long()
    sym_patch_inv = sym_patch.index_select(1, inv_idx)
    out_1_aug.narrow(1, 0, sym_len_Ws).copy_(sym_patch_inv)
    sym_patch = out_1[:, -sym_len_We:, :]
    inv_idx = torch.arange(sym_patch.size(1) - 1, -1, -1).long()
    sym_patch_inv = sym_patch.index_select(1, inv_idx)
    out_1_aug.narrow(1, sym_len_Ws + in_W, sym_len_We).copy_(sym_patch_inv)
    out_2 = torch.FloatTensor(out_H, out_W, in_C)
    kernel_width = weights_W.size(1)
    for i in range(out_W):
        idx = int(indices_W[i][0])
        for j in range(out_C):
            out_2[:, i, j] = out_1_aug[:, idx:idx + kernel_width, j].mv(weights_W[i])
    if need_squeeze:
        out_2.squeeze_()
    return out_2.numpy()

def avg_pool_nd(dims, *args, **kwargs):
    """
    Create a 1D, 2D, or 3D average pooling module.
    """
    if dims == 1:
        return nn.AvgPool1d(*args, **kwargs)
    elif dims == 2:
        return nn.AvgPool2d(*args, **kwargs)
    elif dims == 3:
        return nn.AvgPool3d(*args, **kwargs)
    raise ValueError(f'unsupported dimensions: {dims}')

