# Cluster 12

class EventStorage:
    """
    The user-facing class that provides metric storage functionalities.
    In the future we may add support for storing / logging other types of data if needed.
    """

    def __init__(self, start_iter=0):
        """
        Args:
            start_iter (int): the iteration number to start with
        """
        self._history = defaultdict(AverageMeter)
        self._smoothing_hints = {}
        self._latest_scalars = {}
        self._iter = start_iter
        self._current_prefix = ''
        self._vis_data = []
        self._histograms = []

    def put_scalar(self, name, value, n=1, smoothing_hint=False):
        """
        Add a scalar `value` to the `HistoryBuffer` associated with `name`.
        Args:
            smoothing_hint (bool): a 'hint' on whether this scalar is noisy and should be
                smoothed when logged. The hint will be accessible through
                :meth:`EventStorage.smoothing_hints`.  A writer may ignore the hint
                and apply custom smoothing rule.
                It defaults to True because most scalars we save need to be smoothed to
                provide any useful signal.
        """
        name = self._current_prefix + name
        history = self._history[name]
        history.update(value, n)
        self._latest_scalars[name] = (value, self._iter)
        existing_hint = self._smoothing_hints.get(name)
        if existing_hint is not None:
            assert existing_hint == smoothing_hint, 'Scalar {} was put with a different smoothing_hint!'.format(name)
        else:
            self._smoothing_hints[name] = smoothing_hint

    def history(self, name):
        """
        Returns:
            AverageMeter: the history for name
        """
        ret = self._history.get(name, None)
        if ret is None:
            raise KeyError('No history metric available for {}!'.format(name))
        return ret

    def histories(self):
        """
        Returns:
            dict[name -> HistoryBuffer]: the HistoryBuffer for all scalars
        """
        return self._history

    def latest(self):
        """
        Returns:
            dict[str -> (float, int)]: mapping from the name of each scalar to the most
                recent value and the iteration number its added.
        """
        return self._latest_scalars

    def latest_with_smoothing_hint(self, window_size=20):
        """
        Similar to :meth:`latest`, but the returned values
        are either the un-smoothed original latest value,
        or a median of the given window_size,
        depend on whether the smoothing_hint is True.
        This provides a default behavior that other writers can use.
        """
        result = {}
        for k, (v, itr) in self._latest_scalars.items():
            result[k] = (self._history[k].median(window_size) if self._smoothing_hints[k] else v, itr)
        return result

    def smoothing_hints(self):
        """
        Returns:
            dict[name -> bool]: the user-provided hint on whether the scalar
                is noisy and needs smoothing.
        """
        return self._smoothing_hints

    def step(self):
        """
        User should either: (1) Call this function to increment storage.iter when needed. Or
        (2) Set `storage.iter` to the correct iteration number before each iteration.
        The storage will then be able to associate the new data with an iteration number.
        """
        self._iter += 1

    @property
    def iter(self):
        """
        Returns:
            int: The current iteration number. When used together with a trainer,
                this is ensured to be the same as trainer.iter.
        """
        return self._iter

    @iter.setter
    def iter(self, val):
        self._iter = int(val)

    @property
    def iteration(self):
        return self._iter

    def __enter__(self):
        _CURRENT_STORAGE_STACK.append(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        assert _CURRENT_STORAGE_STACK[-1] == self
        _CURRENT_STORAGE_STACK.pop()

    @contextmanager
    def name_scope(self, name):
        """
        Yields:
            A context within which all the events added to this storage
            will be prefixed by the name scope.
        """
        old_prefix = self._current_prefix
        self._current_prefix = name.rstrip('/') + '/'
        yield
        self._current_prefix = old_prefix

    def clear_images(self):
        """
        Delete all the stored images for visualization. This should be called
        after images are written to tensorboard.
        """
        self._vis_data = []

    def clear_histograms(self):
        """
        Delete all the stored histograms for visualization.
        This should be called after histograms are written to tensorboard.
        """
        self._histograms = []

    def reset_history(self, name):
        ret = self._history.get(name, None)
        if ret is None:
            raise KeyError('No history metric available for {}!'.format(name))
        ret.reset()

    def reset_histories(self):
        for name in self._history.keys():
            self._history[name].reset()

@iter.setter
def iter(self, val):
    self._iter = int(val)

@TRANSFORMS.register_module()
class NormalizeCoord(object):

    def __call__(self, data_dict):
        if 'coord' in data_dict.keys():
            centroid = np.mean(data_dict['coord'], axis=0)
            data_dict['coord'] -= centroid
            m = np.max(np.sqrt(np.sum(data_dict['coord'] ** 2, axis=1)))
            data_dict['coord'] = data_dict['coord'] / m
        return data_dict

def __call__(self, data_dict):
    if 'coord' in data_dict.keys():
        centroid = np.mean(data_dict['coord'], axis=0)
        data_dict['coord'] -= centroid
        m = np.max(np.sqrt(np.sum(data_dict['coord'] ** 2, axis=1)))
        data_dict['coord'] = data_dict['coord'] / m
    return data_dict

@TRANSFORMS.register_module()
class RandomColorJitter(object):
    """
    Random Color Jitter for 3D point cloud (refer torchvision)
    """

    def __init__(self, brightness=0, contrast=0, saturation=0, hue=0, p=0.95):
        self.brightness = self._check_input(brightness, 'brightness')
        self.contrast = self._check_input(contrast, 'contrast')
        self.saturation = self._check_input(saturation, 'saturation')
        self.hue = self._check_input(hue, 'hue', center=0, bound=(-0.5, 0.5), clip_first_on_zero=False)
        self.p = p

    @staticmethod
    def _check_input(value, name, center=1, bound=(0, float('inf')), clip_first_on_zero=True):
        if isinstance(value, numbers.Number):
            if value < 0:
                raise ValueError('If {} is a single number, it must be non negative.'.format(name))
            value = [center - float(value), center + float(value)]
            if clip_first_on_zero:
                value[0] = max(value[0], 0.0)
        elif isinstance(value, (tuple, list)) and len(value) == 2:
            if not bound[0] <= value[0] <= value[1] <= bound[1]:
                raise ValueError('{} values should be between {}'.format(name, bound))
        else:
            raise TypeError('{} should be a single number or a list/tuple with length 2.'.format(name))
        if value[0] == value[1] == center:
            value = None
        return value

    @staticmethod
    def blend(color1, color2, ratio):
        ratio = float(ratio)
        bound = 255.0
        return (ratio * color1 + (1.0 - ratio) * color2).clip(0, bound).astype(color1.dtype)

    @staticmethod
    def rgb2hsv(rgb):
        r, g, b = (rgb[..., 0], rgb[..., 1], rgb[..., 2])
        maxc = np.max(rgb, axis=-1)
        minc = np.min(rgb, axis=-1)
        eqc = maxc == minc
        cr = maxc - minc
        s = cr / (np.ones_like(maxc) * eqc + maxc * (1 - eqc))
        cr_divisor = np.ones_like(maxc) * eqc + cr * (1 - eqc)
        rc = (maxc - r) / cr_divisor
        gc = (maxc - g) / cr_divisor
        bc = (maxc - b) / cr_divisor
        hr = (maxc == r) * (bc - gc)
        hg = ((maxc == g) & (maxc != r)) * (2.0 + rc - bc)
        hb = ((maxc != g) & (maxc != r)) * (4.0 + gc - rc)
        h = hr + hg + hb
        h = (h / 6.0 + 1.0) % 1.0
        return np.stack((h, s, maxc), axis=-1)

    @staticmethod
    def hsv2rgb(hsv):
        h, s, v = (hsv[..., 0], hsv[..., 1], hsv[..., 2])
        i = np.floor(h * 6.0)
        f = h * 6.0 - i
        i = i.astype(np.int32)
        p = np.clip(v * (1.0 - s), 0.0, 1.0)
        q = np.clip(v * (1.0 - s * f), 0.0, 1.0)
        t = np.clip(v * (1.0 - s * (1.0 - f)), 0.0, 1.0)
        i = i % 6
        mask = np.expand_dims(i, axis=-1) == np.arange(6)
        a1 = np.stack((v, q, p, p, t, v), axis=-1)
        a2 = np.stack((t, v, v, q, p, p), axis=-1)
        a3 = np.stack((p, p, t, v, v, q), axis=-1)
        a4 = np.stack((a1, a2, a3), axis=-1)
        return np.einsum('...na, ...nab -> ...nb', mask.astype(hsv.dtype), a4)

    def adjust_brightness(self, color, brightness_factor):
        if brightness_factor < 0:
            raise ValueError('brightness_factor ({}) is not non-negative.'.format(brightness_factor))
        return self.blend(color, np.zeros_like(color), brightness_factor)

    def adjust_contrast(self, color, contrast_factor):
        if contrast_factor < 0:
            raise ValueError('contrast_factor ({}) is not non-negative.'.format(contrast_factor))
        mean = np.mean(RandomColorGrayScale.rgb_to_grayscale(color))
        return self.blend(color, mean, contrast_factor)

    def adjust_saturation(self, color, saturation_factor):
        if saturation_factor < 0:
            raise ValueError('saturation_factor ({}) is not non-negative.'.format(saturation_factor))
        gray = RandomColorGrayScale.rgb_to_grayscale(color)
        return self.blend(color, gray, saturation_factor)

    def adjust_hue(self, color, hue_factor):
        if not -0.5 <= hue_factor <= 0.5:
            raise ValueError('hue_factor ({}) is not in [-0.5, 0.5].'.format(hue_factor))
        orig_dtype = color.dtype
        hsv = self.rgb2hsv(color / 255.0)
        h, s, v = (hsv[..., 0], hsv[..., 1], hsv[..., 2])
        h = (h + hue_factor) % 1.0
        hsv = np.stack((h, s, v), axis=-1)
        color_hue_adj = (self.hsv2rgb(hsv) * 255.0).astype(orig_dtype)
        return color_hue_adj

    @staticmethod
    def get_params(brightness, contrast, saturation, hue):
        fn_idx = torch.randperm(4)
        b = None if brightness is None else np.random.uniform(brightness[0], brightness[1])
        c = None if contrast is None else np.random.uniform(contrast[0], contrast[1])
        s = None if saturation is None else np.random.uniform(saturation[0], saturation[1])
        h = None if hue is None else np.random.uniform(hue[0], hue[1])
        return (fn_idx, b, c, s, h)

    def __call__(self, data_dict):
        fn_idx, brightness_factor, contrast_factor, saturation_factor, hue_factor = self.get_params(self.brightness, self.contrast, self.saturation, self.hue)
        for fn_id in fn_idx:
            if fn_id == 0 and brightness_factor is not None and (np.random.rand() < self.p):
                data_dict['color'] = self.adjust_brightness(data_dict['color'], brightness_factor)
            elif fn_id == 1 and contrast_factor is not None and (np.random.rand() < self.p):
                data_dict['color'] = self.adjust_contrast(data_dict['color'], contrast_factor)
            elif fn_id == 2 and saturation_factor is not None and (np.random.rand() < self.p):
                data_dict['color'] = self.adjust_saturation(data_dict['color'], saturation_factor)
            elif fn_id == 3 and hue_factor is not None and (np.random.rand() < self.p):
                data_dict['color'] = self.adjust_hue(data_dict['color'], hue_factor)
        return data_dict

@staticmethod
def get_params(brightness, contrast, saturation, hue):
    fn_idx = torch.randperm(4)
    b = None if brightness is None else np.random.uniform(brightness[0], brightness[1])
    c = None if contrast is None else np.random.uniform(contrast[0], contrast[1])
    s = None if saturation is None else np.random.uniform(saturation[0], saturation[1])
    h = None if hue is None else np.random.uniform(hue[0], hue[1])
    return (fn_idx, b, c, s, h)

def face_normal(vertex, face):
    v01 = vertex[face[:, 1]] - vertex[face[:, 0]]
    v02 = vertex[face[:, 2]] - vertex[face[:, 0]]
    vec = np.cross(v01, v02)
    length = np.sqrt(np.sum(vec ** 2, axis=1, keepdims=True)) + 1e-08
    nf = vec / length
    area = length * 0.5
    return (nf, area)

def face_normal(vertex, face):
    v01 = vertex[face[:, 1]] - vertex[face[:, 0]]
    v02 = vertex[face[:, 2]] - vertex[face[:, 0]]
    vec = np.cross(v01, v02)
    length = np.sqrt(np.sum(vec ** 2, axis=1, keepdims=True)) + 1e-08
    nf = vec / length
    area = length * 0.5
    return (nf, area)

def norm_cdf(x):
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

class GroupedLinear(nn.Module):
    __constants__ = ['in_features', 'out_features', 'groups']
    in_features: int
    out_features: int
    groups: int
    weight: torch.Tensor

    def __init__(self, in_features: int, out_features: int, groups: int, device=None, dtype=None) -> None:
        factory_kwargs = {'device': device, 'dtype': dtype}
        super(GroupedLinear, self).__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.groups = groups
        assert in_features & groups == 0
        assert out_features % groups == 0
        assert out_features == groups
        self.weight = nn.Parameter(torch.empty((1, in_features), **factory_kwargs))
        self.reset_parameters()

    def reset_parameters(self) -> None:
        nn.init.kaiming_uniform_(self.weight, a=math.sqrt(5))

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        return (input * self.weight).reshape(list(input.shape[:-1]) + [self.groups, input.shape[-1] // self.groups]).sum(-1)

    def extra_repr(self) -> str:
        return 'in_features={}, out_features={}, bias={}'.format(self.in_features, self.out_features, self.bias is not None)

def reset_parameters(self) -> None:
    nn.init.kaiming_uniform_(self.weight, a=math.sqrt(5))

class Grouping(Function):

    @staticmethod
    def forward(ctx, input, idx):
        """
        input: input: (n, c), idx : (m, nsample)
        output: (m, nsample, c)
        """
        assert input.is_contiguous() and idx.is_contiguous()
        m, nsample, n, c = (idx.shape[0], idx.shape[1], input.shape[0], input.shape[1])
        output = torch.cuda.FloatTensor(m, nsample, c)
        grouping_forward_cuda(m, nsample, c, input, idx, output)
        ctx.n = n
        ctx.save_for_backward(idx)
        return output

    @staticmethod
    def backward(ctx, grad_output):
        """
        input: grad_out: (m, c, nsample)
        output: (n, c), None
        """
        n = ctx.n
        idx, = ctx.saved_tensors
        m, nsample, c = grad_output.shape
        grad_input = torch.cuda.FloatTensor(n, c).zero_()
        grouping_backward_cuda(m, nsample, c, grad_output, idx, grad_input)
        return (grad_input, None)

@staticmethod
def forward(ctx, input, idx):
    """
        input: input: (n, c), idx : (m, nsample)
        output: (m, nsample, c)
        """
    assert input.is_contiguous() and idx.is_contiguous()
    m, nsample, n, c = (idx.shape[0], idx.shape[1], input.shape[0], input.shape[1])
    output = torch.cuda.FloatTensor(m, nsample, c)
    grouping_forward_cuda(m, nsample, c, input, idx, output)
    ctx.n = n
    ctx.save_for_backward(idx)
    return output

@staticmethod
def backward(ctx, grad_output):
    """
        input: grad_out: (m, c, nsample)
        output: (n, c), None
        """
    n = ctx.n
    idx, = ctx.saved_tensors
    m, nsample, c = grad_output.shape
    grad_input = torch.cuda.FloatTensor(n, c).zero_()
    grouping_backward_cuda(m, nsample, c, grad_output, idx, grad_input)
    return (grad_input, None)

class Subtraction(Function):

    @staticmethod
    def forward(ctx, input1, input2, idx):
        """
        input: input1: (n, c), input2: (n, c), idx: (n, nsample)
        output:  (n, nsample, c)
        """
        assert input1.is_contiguous() and input2.is_contiguous()
        n, c = input1.shape
        nsample = idx.shape[-1]
        output = torch.cuda.FloatTensor(n, nsample, c).zero_()
        subtraction_forward_cuda(n, nsample, c, input1, input2, idx, output)
        ctx.save_for_backward(idx)
        return output

    @staticmethod
    def backward(ctx, grad_output):
        """
        input: grad_out: (n, nsample, c)
        output: grad_input1: (n, c), grad_input2: (n, c)
        """
        idx, = ctx.saved_tensors
        n, nsample, c = grad_output.shape
        grad_input1 = torch.cuda.FloatTensor(n, c).zero_()
        grad_input2 = torch.cuda.FloatTensor(n, c).zero_()
        subtraction_backward_cuda(n, nsample, c, idx, grad_output, grad_input1, grad_input2)
        return (grad_input1, grad_input2, None)

@staticmethod
def forward(ctx, input1, input2, idx):
    """
        input: input1: (n, c), input2: (n, c), idx: (n, nsample)
        output:  (n, nsample, c)
        """
    assert input1.is_contiguous() and input2.is_contiguous()
    n, c = input1.shape
    nsample = idx.shape[-1]
    output = torch.cuda.FloatTensor(n, nsample, c).zero_()
    subtraction_forward_cuda(n, nsample, c, input1, input2, idx, output)
    ctx.save_for_backward(idx)
    return output

@staticmethod
def backward(ctx, grad_output):
    """
        input: grad_out: (n, nsample, c)
        output: grad_input1: (n, c), grad_input2: (n, c)
        """
    idx, = ctx.saved_tensors
    n, nsample, c = grad_output.shape
    grad_input1 = torch.cuda.FloatTensor(n, c).zero_()
    grad_input2 = torch.cuda.FloatTensor(n, c).zero_()
    subtraction_backward_cuda(n, nsample, c, idx, grad_output, grad_input1, grad_input2)
    return (grad_input1, grad_input2, None)

class Aggregation(Function):

    @staticmethod
    def forward(ctx, input, position, weight, idx):
        """
        input: input: (n, c), position: (n, nsample, c), weight : (n, nsample, c'), idx: (n, nsample)
        output: (n, c)
        """
        assert input.is_contiguous() and position.is_contiguous() and weight.is_contiguous()
        n, nsample, c = position.shape
        w_c = weight.shape[-1]
        output = torch.cuda.FloatTensor(n, c).zero_()
        aggregation_forward_cuda(n, nsample, c, w_c, input, position, weight, idx, output)
        ctx.save_for_backward(input, position, weight, idx)
        return output

    @staticmethod
    def backward(ctx, grad_output):
        """
        input: grad_out: (n, c)
        output: grad_input: (n, c), grad_position: (n, nsample, c), grad_weight : (n, nsample, c')
        """
        input, position, weight, idx = ctx.saved_tensors
        n, nsample, c = position.shape
        w_c = weight.shape[-1]
        grad_input = torch.cuda.FloatTensor(n, c).zero_()
        grad_position = torch.cuda.FloatTensor(n, nsample, c).zero_()
        grad_weight = torch.cuda.FloatTensor(n, nsample, w_c).zero_()
        aggregation_backward_cuda(n, nsample, c, w_c, input, position, weight, idx, grad_output, grad_input, grad_position, grad_weight)
        return (grad_input, grad_position, grad_weight, None)

@staticmethod
def forward(ctx, input, position, weight, idx):
    """
        input: input: (n, c), position: (n, nsample, c), weight : (n, nsample, c'), idx: (n, nsample)
        output: (n, c)
        """
    assert input.is_contiguous() and position.is_contiguous() and weight.is_contiguous()
    n, nsample, c = position.shape
    w_c = weight.shape[-1]
    output = torch.cuda.FloatTensor(n, c).zero_()
    aggregation_forward_cuda(n, nsample, c, w_c, input, position, weight, idx, output)
    ctx.save_for_backward(input, position, weight, idx)
    return output

@staticmethod
def backward(ctx, grad_output):
    """
        input: grad_out: (n, c)
        output: grad_input: (n, c), grad_position: (n, nsample, c), grad_weight : (n, nsample, c')
        """
    input, position, weight, idx = ctx.saved_tensors
    n, nsample, c = position.shape
    w_c = weight.shape[-1]
    grad_input = torch.cuda.FloatTensor(n, c).zero_()
    grad_position = torch.cuda.FloatTensor(n, nsample, c).zero_()
    grad_weight = torch.cuda.FloatTensor(n, nsample, w_c).zero_()
    aggregation_backward_cuda(n, nsample, c, w_c, input, position, weight, idx, grad_output, grad_input, grad_position, grad_weight)
    return (grad_input, grad_position, grad_weight, None)

class KNNQuery(Function):

    @staticmethod
    def forward(ctx, nsample, xyz, offset, new_xyz=None, new_offset=None):
        """
        input: coords: (n, 3), new_xyz: (m, 3), offset: (b), new_offset: (b)
        output: idx: (m, nsample) -1 is placeholder, dist2: (m, nsample)
        """
        if new_xyz is None or new_offset is None:
            new_xyz = xyz
            new_offset = offset
        assert xyz.is_contiguous() and new_xyz.is_contiguous()
        m = new_xyz.shape[0]
        idx = torch.cuda.IntTensor(m, nsample).zero_()
        dist2 = torch.cuda.FloatTensor(m, nsample).zero_()
        knn_query_cuda(m, nsample, xyz, new_xyz, offset.int(), new_offset.int(), idx, dist2)
        return (idx, torch.sqrt(dist2))

@staticmethod
def forward(ctx, nsample, xyz, offset, new_xyz=None, new_offset=None):
    """
        input: coords: (n, 3), new_xyz: (m, 3), offset: (b), new_offset: (b)
        output: idx: (m, nsample) -1 is placeholder, dist2: (m, nsample)
        """
    if new_xyz is None or new_offset is None:
        new_xyz = xyz
        new_offset = offset
    assert xyz.is_contiguous() and new_xyz.is_contiguous()
    m = new_xyz.shape[0]
    idx = torch.cuda.IntTensor(m, nsample).zero_()
    dist2 = torch.cuda.FloatTensor(m, nsample).zero_()
    knn_query_cuda(m, nsample, xyz, new_xyz, offset.int(), new_offset.int(), idx, dist2)
    return (idx, torch.sqrt(dist2))

class RandomBallQuery(Function):
    """Random Ball Query.

    Find nearby points in spherical space.
    """

    @staticmethod
    def forward(ctx, nsample, max_radius, min_radius, xyz, offset, new_xyz=None, new_offset=None):
        """
        input: coords: (n, 3), new_xyz: (m, 3), offset: (b), new_offset: (b)
        output: idx: (m, nsample), dist2: (m, nsample)
        """
        if new_xyz is None or new_offset is None:
            new_xyz = xyz
            new_offset = offset
        assert xyz.is_contiguous() and new_xyz.is_contiguous()
        assert min_radius < max_radius
        m = new_xyz.shape[0]
        order = []
        for k in range(offset.shape[0]):
            s_k, e_k = (0, offset[0]) if k == 0 else (offset[k - 1], offset[k])
            order.append(torch.randperm(e_k - s_k, dtype=torch.int32, device=offset.device) + s_k)
        order = torch.cat(order, dim=0)
        idx = torch.cuda.IntTensor(m, nsample).zero_()
        dist2 = torch.cuda.FloatTensor(m, nsample).zero_()
        random_ball_query_cuda(m, nsample, min_radius, max_radius, order, xyz, new_xyz, offset.int(), new_offset.int(), idx, dist2)
        return (idx, torch.sqrt(dist2))

@staticmethod
def forward(ctx, nsample, max_radius, min_radius, xyz, offset, new_xyz=None, new_offset=None):
    """
        input: coords: (n, 3), new_xyz: (m, 3), offset: (b), new_offset: (b)
        output: idx: (m, nsample), dist2: (m, nsample)
        """
    if new_xyz is None or new_offset is None:
        new_xyz = xyz
        new_offset = offset
    assert xyz.is_contiguous() and new_xyz.is_contiguous()
    assert min_radius < max_radius
    m = new_xyz.shape[0]
    order = []
    for k in range(offset.shape[0]):
        s_k, e_k = (0, offset[0]) if k == 0 else (offset[k - 1], offset[k])
        order.append(torch.randperm(e_k - s_k, dtype=torch.int32, device=offset.device) + s_k)
    order = torch.cat(order, dim=0)
    idx = torch.cuda.IntTensor(m, nsample).zero_()
    dist2 = torch.cuda.FloatTensor(m, nsample).zero_()
    random_ball_query_cuda(m, nsample, min_radius, max_radius, order, xyz, new_xyz, offset.int(), new_offset.int(), idx, dist2)
    return (idx, torch.sqrt(dist2))

class BallQuery(Function):
    """Ball Query.

    Find nearby points in spherical space.
    """

    @staticmethod
    def forward(ctx, nsample, max_radius, min_radius, xyz, offset, new_xyz=None, new_offset=None):
        """
        input: coords: (n, 3), new_xyz: (m, 3), offset: (b), new_offset: (b)
        output: idx: (m, nsample), dist2: (m, nsample)
        """
        if new_xyz is None or new_offset is None:
            new_xyz = xyz
            new_offset = offset
        assert xyz.is_contiguous() and new_xyz.is_contiguous()
        assert min_radius < max_radius
        m = new_xyz.shape[0]
        idx = torch.cuda.IntTensor(m, nsample).zero_()
        dist2 = torch.cuda.FloatTensor(m, nsample).zero_()
        ball_query_cuda(m, nsample, min_radius, max_radius, xyz, new_xyz, offset.int(), new_offset.int(), idx, dist2)
        return (idx, torch.sqrt(dist2))

@staticmethod
def forward(ctx, nsample, max_radius, min_radius, xyz, offset, new_xyz=None, new_offset=None):
    """
        input: coords: (n, 3), new_xyz: (m, 3), offset: (b), new_offset: (b)
        output: idx: (m, nsample), dist2: (m, nsample)
        """
    if new_xyz is None or new_offset is None:
        new_xyz = xyz
        new_offset = offset
    assert xyz.is_contiguous() and new_xyz.is_contiguous()
    assert min_radius < max_radius
    m = new_xyz.shape[0]
    idx = torch.cuda.IntTensor(m, nsample).zero_()
    dist2 = torch.cuda.FloatTensor(m, nsample).zero_()
    ball_query_cuda(m, nsample, min_radius, max_radius, xyz, new_xyz, offset.int(), new_offset.int(), idx, dist2)
    return (idx, torch.sqrt(dist2))

class AttentionRelationStep(Function):

    @staticmethod
    def forward(ctx, query, key, weight, index_target, index_refer):
        """
        input - query: (n, g, c), key: (n, g, c), weight: (c)  1_c for scatter attention,
                index_target: (m), index_refer: (m)
        output - relation: (M, g)
        """
        assert query.is_contiguous() and key.is_contiguous() and index_target.is_contiguous() and index_refer.is_contiguous() and weight.is_contiguous()
        assert index_target.shape[0] == index_refer.shape[0]
        _, g, c = query.shape
        m = index_target.shape[0]
        output = torch.cuda.FloatTensor(m, g).zero_()
        attention_relation_step_forward_cuda(m, g, c, query, key, weight, index_target.int(), index_refer.int(), output)
        ctx.save_for_backward(query, key, weight, index_target, index_refer)
        return output

    @staticmethod
    def backward(ctx, grad_output):
        query, key, weight, index_target, index_refer = ctx.saved_tensors
        n, g, c = query.shape
        m = index_target.shape[0]
        grad_query = torch.cuda.FloatTensor(n, g, c).zero_()
        grad_key = torch.cuda.FloatTensor(n, g, c).zero_()
        grad_weight = torch.cuda.FloatTensor(c).zero_()
        attention_relation_step_backward_cuda(m, g, c, query, grad_query, key, grad_key, weight, grad_weight, index_target.int(), index_refer.int(), grad_output)
        return (grad_query, grad_key, None, None, None)

@staticmethod
def forward(ctx, query, key, weight, index_target, index_refer):
    """
        input - query: (n, g, c), key: (n, g, c), weight: (c)  1_c for scatter attention,
                index_target: (m), index_refer: (m)
        output - relation: (M, g)
        """
    assert query.is_contiguous() and key.is_contiguous() and index_target.is_contiguous() and index_refer.is_contiguous() and weight.is_contiguous()
    assert index_target.shape[0] == index_refer.shape[0]
    _, g, c = query.shape
    m = index_target.shape[0]
    output = torch.cuda.FloatTensor(m, g).zero_()
    attention_relation_step_forward_cuda(m, g, c, query, key, weight, index_target.int(), index_refer.int(), output)
    ctx.save_for_backward(query, key, weight, index_target, index_refer)
    return output

@staticmethod
def backward(ctx, grad_output):
    query, key, weight, index_target, index_refer = ctx.saved_tensors
    n, g, c = query.shape
    m = index_target.shape[0]
    grad_query = torch.cuda.FloatTensor(n, g, c).zero_()
    grad_key = torch.cuda.FloatTensor(n, g, c).zero_()
    grad_weight = torch.cuda.FloatTensor(c).zero_()
    attention_relation_step_backward_cuda(m, g, c, query, grad_query, key, grad_key, weight, grad_weight, index_target.int(), index_refer.int(), grad_output)
    return (grad_query, grad_key, None, None, None)

class AttentionFusionStep(Function):

    @staticmethod
    def forward(ctx, weight, value, index_target, index_refer):
        """
        input - weight: (m, g), value: (n, g, c)
                index_target: (m), index_value: (m)
        output - output: (n, g, c)
        """
        assert weight.is_contiguous() and value.is_contiguous() and index_target.is_contiguous() and index_refer.is_contiguous() and weight.is_contiguous()
        assert index_target.shape[0] == index_refer.shape[0]
        n, g, c = value.shape
        m = index_refer.shape[0]
        output = torch.cuda.FloatTensor(n, g, c).zero_()
        attention_fusion_step_forward_cuda(m, g, c, weight, value, index_target.int(), index_refer.int(), output)
        ctx.save_for_backward(weight, value, index_target, index_refer)
        return output

    @staticmethod
    def backward(ctx, grad_output):
        """
        input: grad_output: (n, g, c)
        output: grad_weight: (m, g), grad_value: (n, g, c), none, none
        """
        weight, value, index_target, index_refer = ctx.saved_tensors
        n, g, c = value.shape
        m = index_target.shape[0]
        grad_weight = torch.cuda.FloatTensor(m, g).zero_()
        grad_value = torch.cuda.FloatTensor(n, g, c).zero_()
        attention_fusion_step_backward_cuda(m, g, c, weight, grad_weight, value, grad_value, index_target.int(), index_refer.int(), grad_output)
        return (grad_weight, grad_value, None, None)

@staticmethod
def forward(ctx, weight, value, index_target, index_refer):
    """
        input - weight: (m, g), value: (n, g, c)
                index_target: (m), index_value: (m)
        output - output: (n, g, c)
        """
    assert weight.is_contiguous() and value.is_contiguous() and index_target.is_contiguous() and index_refer.is_contiguous() and weight.is_contiguous()
    assert index_target.shape[0] == index_refer.shape[0]
    n, g, c = value.shape
    m = index_refer.shape[0]
    output = torch.cuda.FloatTensor(n, g, c).zero_()
    attention_fusion_step_forward_cuda(m, g, c, weight, value, index_target.int(), index_refer.int(), output)
    ctx.save_for_backward(weight, value, index_target, index_refer)
    return output

@staticmethod
def backward(ctx, grad_output):
    """
        input: grad_output: (n, g, c)
        output: grad_weight: (m, g), grad_value: (n, g, c), none, none
        """
    weight, value, index_target, index_refer = ctx.saved_tensors
    n, g, c = value.shape
    m = index_target.shape[0]
    grad_weight = torch.cuda.FloatTensor(m, g).zero_()
    grad_value = torch.cuda.FloatTensor(n, g, c).zero_()
    attention_fusion_step_backward_cuda(m, g, c, weight, grad_weight, value, grad_value, index_target.int(), index_refer.int(), grad_output)
    return (grad_weight, grad_value, None, None)

class FarthestPointSampling(Function):

    @staticmethod
    def forward(ctx, xyz, offset, new_offset):
        """
        input: coords: (n, 3), offset: (b), new_offset: (b)
        output: idx: (m)
        """
        assert xyz.is_contiguous()
        n, b, n_max = (xyz.shape[0], offset.shape[0], offset[0])
        for i in range(1, b):
            n_max = max(offset[i] - offset[i - 1], n_max)
        idx = torch.cuda.IntTensor(new_offset[b - 1].item()).zero_()
        tmp = torch.cuda.FloatTensor(n).fill_(10000000000.0)
        farthest_point_sampling_cuda(b, n_max, xyz, offset.int(), new_offset.int(), tmp, idx)
        del tmp
        return idx

@staticmethod
def forward(ctx, xyz, offset, new_offset):
    """
        input: coords: (n, 3), offset: (b), new_offset: (b)
        output: idx: (m)
        """
    assert xyz.is_contiguous()
    n, b, n_max = (xyz.shape[0], offset.shape[0], offset[0])
    for i in range(1, b):
        n_max = max(offset[i] - offset[i - 1], n_max)
    idx = torch.cuda.IntTensor(new_offset[b - 1].item()).zero_()
    tmp = torch.cuda.FloatTensor(n).fill_(10000000000.0)
    farthest_point_sampling_cuda(b, n_max, xyz, offset.int(), new_offset.int(), tmp, idx)
    del tmp
    return idx

class Interpolation(Function):

    @staticmethod
    def forward(ctx, xyz, new_xyz, input, offset, new_offset, k=3):
        """
        input: coords: (m, 3), new_xyz: (n, 3), input: (m, c), offset: (b), new_offset: (b)
        output: (n, c)
        """
        assert xyz.is_contiguous() and new_xyz.is_contiguous() and input.is_contiguous()
        idx, dist = knn_query(k, xyz, offset, new_xyz, new_offset)
        dist_recip = 1.0 / (dist + 1e-08)
        norm = torch.sum(dist_recip, dim=1, keepdim=True)
        weight = dist_recip / norm
        n, c, m = (new_xyz.shape[0], input.shape[1], input.shape[0])
        output = torch.cuda.FloatTensor(n, c).zero_()
        interpolation_forward_cuda(n, c, k, input, idx, weight, output)
        ctx.m, ctx.k = (m, k)
        ctx.save_for_backward(idx, weight)
        return output

    @staticmethod
    def backward(ctx, grad_output):
        """
        input: coords: (m, 3), new_xyz: (n, 3), input: (m, c), offset: (b), new_offset: (b)
        output: (n, c)
        """
        m, k = (ctx.m, ctx.k)
        idx, weight = ctx.saved_tensors
        n, c = grad_output.shape
        grad_input = torch.cuda.FloatTensor(m, c).zero_()
        interpolation_backward_cuda(n, c, k, grad_output, idx, weight, grad_input)
        return (None, None, grad_input, None, None, None)

@staticmethod
def forward(ctx, xyz, new_xyz, input, offset, new_offset, k=3):
    """
        input: coords: (m, 3), new_xyz: (n, 3), input: (m, c), offset: (b), new_offset: (b)
        output: (n, c)
        """
    assert xyz.is_contiguous() and new_xyz.is_contiguous() and input.is_contiguous()
    idx, dist = knn_query(k, xyz, offset, new_xyz, new_offset)
    dist_recip = 1.0 / (dist + 1e-08)
    norm = torch.sum(dist_recip, dim=1, keepdim=True)
    weight = dist_recip / norm
    n, c, m = (new_xyz.shape[0], input.shape[1], input.shape[0])
    output = torch.cuda.FloatTensor(n, c).zero_()
    interpolation_forward_cuda(n, c, k, input, idx, weight, output)
    ctx.m, ctx.k = (m, k)
    ctx.save_for_backward(idx, weight)
    return output

@staticmethod
def backward(ctx, grad_output):
    """
        input: coords: (m, 3), new_xyz: (n, 3), input: (m, c), offset: (b), new_offset: (b)
        output: (n, c)
        """
    m, k = (ctx.m, ctx.k)
    idx, weight = ctx.saved_tensors
    n, c = grad_output.shape
    grad_input = torch.cuda.FloatTensor(m, c).zero_()
    interpolation_backward_cuda(n, c, k, grad_output, idx, weight, grad_input)
    return (None, None, grad_input, None, None, None)

class FurthestSampling(Function):

    @staticmethod
    def forward(ctx, xyz, offset, new_offset):
        """
        input: xyz: (n, 3), offset: (b), new_offset: (b)
        output: idx: (m)
        """
        assert xyz.is_contiguous()
        n, b, n_max = (xyz.shape[0], offset.shape[0], offset[0])
        for i in range(1, b):
            n_max = max(offset[i] - offset[i - 1], n_max)
        idx = torch.cuda.IntTensor(new_offset[b - 1].item()).zero_()
        tmp = torch.cuda.FloatTensor(n).fill_(10000000000.0)
        pointops_cuda.furthestsampling_cuda(b, n_max, xyz, offset, new_offset, tmp, idx)
        del tmp
        return idx

@staticmethod
def forward(ctx, xyz, offset, new_offset):
    """
        input: xyz: (n, 3), offset: (b), new_offset: (b)
        output: idx: (m)
        """
    assert xyz.is_contiguous()
    n, b, n_max = (xyz.shape[0], offset.shape[0], offset[0])
    for i in range(1, b):
        n_max = max(offset[i] - offset[i - 1], n_max)
    idx = torch.cuda.IntTensor(new_offset[b - 1].item()).zero_()
    tmp = torch.cuda.FloatTensor(n).fill_(10000000000.0)
    pointops_cuda.furthestsampling_cuda(b, n_max, xyz, offset, new_offset, tmp, idx)
    del tmp
    return idx

class KNNQuery(Function):

    @staticmethod
    def forward(ctx, nsample, xyz, new_xyz, offset, new_offset):
        """
        input: xyz: (n, 3), new_xyz: (m, 3), offset: (b), new_offset: (b)
        output: idx: (m, nsample), dist2: (m, nsample)
        """
        if new_xyz is None:
            new_xyz = xyz
        assert xyz.is_contiguous() and new_xyz.is_contiguous()
        m = new_xyz.shape[0]
        idx = torch.cuda.IntTensor(m, nsample).zero_()
        dist2 = torch.cuda.FloatTensor(m, nsample).zero_()
        pointops_cuda.knnquery_cuda(m, nsample, xyz, new_xyz, offset, new_offset, idx, dist2)
        return (idx, torch.sqrt(dist2))

@staticmethod
def forward(ctx, nsample, xyz, new_xyz, offset, new_offset):
    """
        input: xyz: (n, 3), new_xyz: (m, 3), offset: (b), new_offset: (b)
        output: idx: (m, nsample), dist2: (m, nsample)
        """
    if new_xyz is None:
        new_xyz = xyz
    assert xyz.is_contiguous() and new_xyz.is_contiguous()
    m = new_xyz.shape[0]
    idx = torch.cuda.IntTensor(m, nsample).zero_()
    dist2 = torch.cuda.FloatTensor(m, nsample).zero_()
    pointops_cuda.knnquery_cuda(m, nsample, xyz, new_xyz, offset, new_offset, idx, dist2)
    return (idx, torch.sqrt(dist2))

class Grouping(Function):

    @staticmethod
    def forward(ctx, input, idx):
        """
        input: input: (n, c), idx : (m, nsample)
        output: (m, nsample, c)
        """
        assert input.is_contiguous() and idx.is_contiguous()
        m, nsample, n, c = (idx.shape[0], idx.shape[1], input.shape[0], input.shape[1])
        output = torch.cuda.FloatTensor(m, nsample, c)
        pointops_cuda.grouping_forward_cuda(m, nsample, c, input, idx, output)
        ctx.n = n
        ctx.save_for_backward(idx)
        return output

    @staticmethod
    def backward(ctx, grad_output):
        """
        input: grad_out: (m, c, nsample)
        output: (n, c), None
        """
        n = ctx.n
        idx, = ctx.saved_tensors
        m, nsample, c = grad_output.shape
        grad_input = torch.cuda.FloatTensor(n, c).zero_()
        pointops_cuda.grouping_backward_cuda(m, nsample, c, grad_output, idx, grad_input)
        return (grad_input, None)

@staticmethod
def forward(ctx, input, idx):
    """
        input: input: (n, c), idx : (m, nsample)
        output: (m, nsample, c)
        """
    assert input.is_contiguous() and idx.is_contiguous()
    m, nsample, n, c = (idx.shape[0], idx.shape[1], input.shape[0], input.shape[1])
    output = torch.cuda.FloatTensor(m, nsample, c)
    pointops_cuda.grouping_forward_cuda(m, nsample, c, input, idx, output)
    ctx.n = n
    ctx.save_for_backward(idx)
    return output

@staticmethod
def backward(ctx, grad_output):
    """
        input: grad_out: (m, c, nsample)
        output: (n, c), None
        """
    n = ctx.n
    idx, = ctx.saved_tensors
    m, nsample, c = grad_output.shape
    grad_input = torch.cuda.FloatTensor(n, c).zero_()
    pointops_cuda.grouping_backward_cuda(m, nsample, c, grad_output, idx, grad_input)
    return (grad_input, None)

class AttentionStep1(Function):

    @staticmethod
    def forward(ctx, q, k, index0, index1):
        """
        input: q: (N, h, C//h), k: (N, h, C//h), index0: (M), index1: (M)
        output: output: [N, h, C//h]
        """
        assert q.is_contiguous() and k.is_contiguous() and index0.is_contiguous() and index1.is_contiguous()
        N_q, h, C_div_h = q.shape
        N_k = k.shape[0]
        M = index0.shape[0]
        C = int(C_div_h * h)
        output = torch.cuda.FloatTensor(M, h).zero_()
        pointops_cuda.attention_step1_forward_cuda(N_k, M, h, C, q, k, index0, index1, output)
        ctx.N_q = N_q
        ctx.N_k = N_k
        ctx.C = C
        ctx.save_for_backward(q, k, index0, index1)
        return output

    @staticmethod
    def backward(ctx, grad_output):
        """
        input: grad_output: (N, h, C//h)
        output: (M, h), (N, h, C//h), None, None
        """
        N_q = ctx.N_q
        N_k = ctx.N_k
        C = ctx.C
        q, k, index0, index1 = ctx.saved_tensors
        M, h = grad_output.shape
        grad_output = grad_output.contiguous()
        assert q.is_contiguous() and k.is_contiguous() and index0.is_contiguous() and index1.is_contiguous() and grad_output.is_contiguous()
        grad_q = torch.cuda.FloatTensor(N_q, h, C // h).zero_()
        grad_k = torch.cuda.FloatTensor(N_k, h, C // h).zero_()
        pointops_cuda.attention_step1_backward_cuda(N_q, M, h, C, grad_output, index0, index1, q, k, grad_q, grad_k)
        return (grad_q, grad_k, None, None)

@staticmethod
def forward(ctx, q, k, index0, index1):
    """
        input: q: (N, h, C//h), k: (N, h, C//h), index0: (M), index1: (M)
        output: output: [N, h, C//h]
        """
    assert q.is_contiguous() and k.is_contiguous() and index0.is_contiguous() and index1.is_contiguous()
    N_q, h, C_div_h = q.shape
    N_k = k.shape[0]
    M = index0.shape[0]
    C = int(C_div_h * h)
    output = torch.cuda.FloatTensor(M, h).zero_()
    pointops_cuda.attention_step1_forward_cuda(N_k, M, h, C, q, k, index0, index1, output)
    ctx.N_q = N_q
    ctx.N_k = N_k
    ctx.C = C
    ctx.save_for_backward(q, k, index0, index1)
    return output

@staticmethod
def backward(ctx, grad_output):
    """
        input: grad_output: (N, h, C//h)
        output: (M, h), (N, h, C//h), None, None
        """
    N_q = ctx.N_q
    N_k = ctx.N_k
    C = ctx.C
    q, k, index0, index1 = ctx.saved_tensors
    M, h = grad_output.shape
    grad_output = grad_output.contiguous()
    assert q.is_contiguous() and k.is_contiguous() and index0.is_contiguous() and index1.is_contiguous() and grad_output.is_contiguous()
    grad_q = torch.cuda.FloatTensor(N_q, h, C // h).zero_()
    grad_k = torch.cuda.FloatTensor(N_k, h, C // h).zero_()
    pointops_cuda.attention_step1_backward_cuda(N_q, M, h, C, grad_output, index0, index1, q, k, grad_q, grad_k)
    return (grad_q, grad_k, None, None)

class AttentionStep1_v2(Function):

    @staticmethod
    def forward(ctx, q, k, index1, index0_offsets, n_max):
        """
        input: q: (N, h, C//h), k: (N, h, C//h), index0: (M), index1: (M)
        output: output: [N, h, C//h]
        """
        assert q.is_contiguous() and k.is_contiguous() and index0_offsets.is_contiguous() and index1.is_contiguous()
        assert n_max <= 1024
        N_q, h, C_div_h = q.shape
        N_k = k.shape[0]
        M = index1.shape[0]
        C = int(C_div_h * h)
        output = torch.cuda.FloatTensor(M, h).zero_()
        pointops_cuda.attention_step1_forward_cuda_v2(N_k, M, h, C, n_max, q, k, index0_offsets, index1, output)
        ctx.N_q = N_q
        ctx.N_k = N_k
        ctx.C = C
        ctx.n_max = n_max
        ctx.save_for_backward(q, k, index0_offsets, index1)
        return output

    @staticmethod
    def backward(ctx, grad_output):
        """
        input: grad_output: (N, h, C//h)
        output: (M, h), (N, h, C//h), None, None
        """
        N_q = ctx.N_q
        N_k = ctx.N_k
        C = ctx.C
        n_max = ctx.n_max
        q, k, index0_offsets, index1 = ctx.saved_tensors
        M, h = grad_output.shape
        grad_output = grad_output.contiguous()
        assert q.is_contiguous() and k.is_contiguous() and index0_offsets.is_contiguous() and index1.is_contiguous() and grad_output.is_contiguous()
        grad_q = torch.cuda.FloatTensor(N_q, h, C // h).zero_()
        grad_k = torch.cuda.FloatTensor(N_k, h, C // h).zero_()
        pointops_cuda.attention_step1_backward_cuda_v2(N_q, M, h, C, n_max, grad_output, index0_offsets, index1, q, k, grad_q, grad_k)
        return (grad_q, grad_k, None, None, None)

@staticmethod
def forward(ctx, q, k, index1, index0_offsets, n_max):
    """
        input: q: (N, h, C//h), k: (N, h, C//h), index0: (M), index1: (M)
        output: output: [N, h, C//h]
        """
    assert q.is_contiguous() and k.is_contiguous() and index0_offsets.is_contiguous() and index1.is_contiguous()
    assert n_max <= 1024
    N_q, h, C_div_h = q.shape
    N_k = k.shape[0]
    M = index1.shape[0]
    C = int(C_div_h * h)
    output = torch.cuda.FloatTensor(M, h).zero_()
    pointops_cuda.attention_step1_forward_cuda_v2(N_k, M, h, C, n_max, q, k, index0_offsets, index1, output)
    ctx.N_q = N_q
    ctx.N_k = N_k
    ctx.C = C
    ctx.n_max = n_max
    ctx.save_for_backward(q, k, index0_offsets, index1)
    return output

@staticmethod
def backward(ctx, grad_output):
    """
        input: grad_output: (N, h, C//h)
        output: (M, h), (N, h, C//h), None, None
        """
    N_q = ctx.N_q
    N_k = ctx.N_k
    C = ctx.C
    n_max = ctx.n_max
    q, k, index0_offsets, index1 = ctx.saved_tensors
    M, h = grad_output.shape
    grad_output = grad_output.contiguous()
    assert q.is_contiguous() and k.is_contiguous() and index0_offsets.is_contiguous() and index1.is_contiguous() and grad_output.is_contiguous()
    grad_q = torch.cuda.FloatTensor(N_q, h, C // h).zero_()
    grad_k = torch.cuda.FloatTensor(N_k, h, C // h).zero_()
    pointops_cuda.attention_step1_backward_cuda_v2(N_q, M, h, C, n_max, grad_output, index0_offsets, index1, q, k, grad_q, grad_k)
    return (grad_q, grad_k, None, None, None)

class AttentionStep2(Function):

    @staticmethod
    def forward(ctx, attn, v, index0, index1):
        """
        input: attn: (M, h), v: (N, h, C//h), index0: (M), index1: (M)
        output: output: [N, h, C//h]
        """
        assert attn.is_contiguous() and v.is_contiguous() and index0.is_contiguous() and index1.is_contiguous()
        M, h = attn.shape
        N_q = index0.max().item() + 1
        N_v, h, C_div_h = v.shape
        C = int(C_div_h * h)
        output = torch.cuda.FloatTensor(N_q, h, C // h).zero_()
        pointops_cuda.attention_step2_forward_cuda(N_q, M, h, C, attn, v, index0, index1, output)
        ctx.M = M
        ctx.save_for_backward(attn, v, index0, index1)
        return output

    @staticmethod
    def backward(ctx, grad_output):
        """
        input: grad_output: (N, h, C//h)
        output: (M, h), (N, h, C//h), None, None
        """
        M = ctx.M
        attn, v, index0, index1 = ctx.saved_tensors
        N_v = v.shape[0]
        N_q, h, C_div_h = grad_output.shape
        C = h * C_div_h
        grad_output = grad_output.contiguous()
        assert attn.is_contiguous() and v.is_contiguous() and index0.is_contiguous() and index1.is_contiguous() and grad_output.is_contiguous()
        grad_attn = torch.cuda.FloatTensor(M, h).zero_()
        grad_v = torch.cuda.FloatTensor(N_v, h, C // h).zero_()
        pointops_cuda.attention_step2_backward_cuda(N_q, M, h, C, grad_output, index0, index1, attn, v, grad_attn, grad_v)
        return (grad_attn, grad_v, None, None)

@staticmethod
def forward(ctx, attn, v, index0, index1):
    """
        input: attn: (M, h), v: (N, h, C//h), index0: (M), index1: (M)
        output: output: [N, h, C//h]
        """
    assert attn.is_contiguous() and v.is_contiguous() and index0.is_contiguous() and index1.is_contiguous()
    M, h = attn.shape
    N_q = index0.max().item() + 1
    N_v, h, C_div_h = v.shape
    C = int(C_div_h * h)
    output = torch.cuda.FloatTensor(N_q, h, C // h).zero_()
    pointops_cuda.attention_step2_forward_cuda(N_q, M, h, C, attn, v, index0, index1, output)
    ctx.M = M
    ctx.save_for_backward(attn, v, index0, index1)
    return output

@staticmethod
def backward(ctx, grad_output):
    """
        input: grad_output: (N, h, C//h)
        output: (M, h), (N, h, C//h), None, None
        """
    M = ctx.M
    attn, v, index0, index1 = ctx.saved_tensors
    N_v = v.shape[0]
    N_q, h, C_div_h = grad_output.shape
    C = h * C_div_h
    grad_output = grad_output.contiguous()
    assert attn.is_contiguous() and v.is_contiguous() and index0.is_contiguous() and index1.is_contiguous() and grad_output.is_contiguous()
    grad_attn = torch.cuda.FloatTensor(M, h).zero_()
    grad_v = torch.cuda.FloatTensor(N_v, h, C // h).zero_()
    pointops_cuda.attention_step2_backward_cuda(N_q, M, h, C, grad_output, index0, index1, attn, v, grad_attn, grad_v)
    return (grad_attn, grad_v, None, None)

class AttentionStep2_v2(Function):

    @staticmethod
    def forward(ctx, attn, v, index0, index1):
        """
        input: attn: (M, h), v: (N, h, C//h), index0: (M), index1: (M)
        output: output: [L, h, C//h]
        """
        assert attn.is_contiguous() and v.is_contiguous() and index0.is_contiguous() and index1.is_contiguous()
        L = int(index0.max().item()) + 1
        M, h = attn.shape
        N, h, C_div_h = v.shape
        C = int(C_div_h * h)
        output = torch.cuda.FloatTensor(L, h, C // h).zero_()
        pointops_cuda.attention_step2_forward_cuda(N, M, h, C, attn, v, index0, index1, output)
        ctx.M = M
        ctx.save_for_backward(attn, v, index0, index1)
        return output

    @staticmethod
    def backward(ctx, grad_output):
        """
        input: grad_output: (L, h, C//h)
        output: (M, h), (N, h, C//h), None, None
        """
        M = ctx.M
        attn, v, index0, index1 = ctx.saved_tensors
        L, h, C_div_h = grad_output.shape
        N = v.shape[0]
        C = h * C_div_h
        grad_output = grad_output.contiguous()
        assert attn.is_contiguous() and v.is_contiguous() and index0.is_contiguous() and index1.is_contiguous() and grad_output.is_contiguous()
        grad_attn = torch.cuda.FloatTensor(M, h).zero_()
        grad_v = torch.cuda.FloatTensor(N, h, C // h).zero_()
        pointops_cuda.attention_step2_backward_cuda(N, M, h, C, grad_output, index0, index1, attn, v, grad_attn, grad_v)
        return (grad_attn, grad_v, None, None)

@staticmethod
def forward(ctx, attn, v, index0, index1):
    """
        input: attn: (M, h), v: (N, h, C//h), index0: (M), index1: (M)
        output: output: [L, h, C//h]
        """
    assert attn.is_contiguous() and v.is_contiguous() and index0.is_contiguous() and index1.is_contiguous()
    L = int(index0.max().item()) + 1
    M, h = attn.shape
    N, h, C_div_h = v.shape
    C = int(C_div_h * h)
    output = torch.cuda.FloatTensor(L, h, C // h).zero_()
    pointops_cuda.attention_step2_forward_cuda(N, M, h, C, attn, v, index0, index1, output)
    ctx.M = M
    ctx.save_for_backward(attn, v, index0, index1)
    return output

@staticmethod
def backward(ctx, grad_output):
    """
        input: grad_output: (L, h, C//h)
        output: (M, h), (N, h, C//h), None, None
        """
    M = ctx.M
    attn, v, index0, index1 = ctx.saved_tensors
    L, h, C_div_h = grad_output.shape
    N = v.shape[0]
    C = h * C_div_h
    grad_output = grad_output.contiguous()
    assert attn.is_contiguous() and v.is_contiguous() and index0.is_contiguous() and index1.is_contiguous() and grad_output.is_contiguous()
    grad_attn = torch.cuda.FloatTensor(M, h).zero_()
    grad_v = torch.cuda.FloatTensor(N, h, C // h).zero_()
    pointops_cuda.attention_step2_backward_cuda(N, M, h, C, grad_output, index0, index1, attn, v, grad_attn, grad_v)
    return (grad_attn, grad_v, None, None)

class DotProdWithIdx(Function):

    @staticmethod
    def forward(ctx, q, index, table, rel_idx):
        """
        input: q: (N, h, hdim), index: (M), table: (L, h, hdim, 3), rel_idx: (M, 3)
        output: output: [M, h]
        """
        assert q.is_contiguous() and index.is_contiguous() and table.is_contiguous() and rel_idx.is_contiguous()
        N, h, hdim = q.shape
        M = index.shape[0]
        output = torch.cuda.FloatTensor(M, h).zero_()
        pointops_cuda.dot_prod_with_idx_forward_cuda(N, M, h, hdim, q, index, table, rel_idx, output)
        ctx.save_for_backward(q, index, table, rel_idx)
        return output

    @staticmethod
    def backward(ctx, grad_output):
        """
        input: grad_output: [M, h]
        output: (N, h, hdim), None, (L, h, hdim, 3), None
        """
        q, index, table, rel_idx = ctx.saved_tensors
        M, h = grad_output.shape
        N, _, hdim = q.shape
        L = table.shape[0]
        grad_output = grad_output.contiguous()
        assert q.is_contiguous() and index.is_contiguous() and table.is_contiguous() and rel_idx.is_contiguous() and grad_output.is_contiguous()
        grad_q = torch.cuda.FloatTensor(N, h, hdim).zero_()
        grad_table = torch.cuda.FloatTensor(L, h, hdim, 3).zero_()
        pointops_cuda.dot_prod_with_idx_backward_cuda(N, M, h, hdim, grad_output, q, index, table, rel_idx, grad_q, grad_table)
        return (grad_q, None, grad_table, None)

@staticmethod
def forward(ctx, q, index, table, rel_idx):
    """
        input: q: (N, h, hdim), index: (M), table: (L, h, hdim, 3), rel_idx: (M, 3)
        output: output: [M, h]
        """
    assert q.is_contiguous() and index.is_contiguous() and table.is_contiguous() and rel_idx.is_contiguous()
    N, h, hdim = q.shape
    M = index.shape[0]
    output = torch.cuda.FloatTensor(M, h).zero_()
    pointops_cuda.dot_prod_with_idx_forward_cuda(N, M, h, hdim, q, index, table, rel_idx, output)
    ctx.save_for_backward(q, index, table, rel_idx)
    return output

@staticmethod
def backward(ctx, grad_output):
    """
        input: grad_output: [M, h]
        output: (N, h, hdim), None, (L, h, hdim, 3), None
        """
    q, index, table, rel_idx = ctx.saved_tensors
    M, h = grad_output.shape
    N, _, hdim = q.shape
    L = table.shape[0]
    grad_output = grad_output.contiguous()
    assert q.is_contiguous() and index.is_contiguous() and table.is_contiguous() and rel_idx.is_contiguous() and grad_output.is_contiguous()
    grad_q = torch.cuda.FloatTensor(N, h, hdim).zero_()
    grad_table = torch.cuda.FloatTensor(L, h, hdim, 3).zero_()
    pointops_cuda.dot_prod_with_idx_backward_cuda(N, M, h, hdim, grad_output, q, index, table, rel_idx, grad_q, grad_table)
    return (grad_q, None, grad_table, None)

class DotProdWithIdx_v2(Function):

    @staticmethod
    def forward(ctx, q, index_q, k, index_k, table_q, table_k, rel_idx):
        """
        input: q: (N, h, hdim), index_q: (M), k: (N, h, hdim), index_k: (M), table_q: (L, h, hdim, 3), table_k: (L, h, hdim, 3), rel_idx: (M, 3)
        output: output: [M, h]
        """
        assert q.is_contiguous() and index_q.is_contiguous() and k.is_contiguous() and index_k.is_contiguous() and table_q.is_contiguous() and table_k.is_contiguous() and rel_idx.is_contiguous()
        N, h, hdim = q.shape
        M = index_q.shape[0]
        L = table_q.shape[0]
        assert table_k.shape[0] == L and index_k.shape[0] == M
        rel_idx_merge = rel_idx[:, 0] + rel_idx[:, 1] * L + rel_idx[:, 2] * L ** 2
        sorted_values, sort_indices = torch.sort(rel_idx_merge)
        _, counts = torch.unique_consecutive(sorted_values, return_counts=True)
        rel_idx_offsets = torch.cumsum(counts, dim=-1)
        rel_idx_offsets = torch.cat([torch.zeros(1, dtype=torch.long).cuda(), rel_idx_offsets], 0)
        n_max = counts.max()
        T = counts.shape[0]
        output = torch.cuda.FloatTensor(M, h).zero_()
        pointops_cuda.dot_prod_with_idx_forward_cuda_v2(N, M, h, hdim, n_max, T, q, index_q, k, index_k, table_q, table_k, rel_idx, rel_idx_offsets.int(), sort_indices.int(), output)
        ctx.n_max = n_max
        ctx.T = T
        ctx.save_for_backward(q, index_q, k, index_k, table_q, table_k, rel_idx, rel_idx_offsets, sort_indices)
        return output

    @staticmethod
    def backward(ctx, grad_output):
        """
        input: grad_output: [M, h]
        output: (N, h, hdim), None, (L, h, hdim, 3), None
        """
        q, index_q, k, index_k, table_q, table_k, rel_idx, rel_idx_offsets, sort_indices = ctx.saved_tensors
        M, h = grad_output.shape
        N, _, hdim = q.shape
        L = table_q.shape[0]
        T, n_max = (ctx.T, ctx.n_max)
        grad_output = grad_output.contiguous()
        assert q.is_contiguous() and index_q.is_contiguous() and k.is_contiguous() and index_k.is_contiguous() and table_q.is_contiguous() and table_k.is_contiguous() and rel_idx.is_contiguous() and rel_idx_offsets.is_contiguous() and sort_indices.is_contiguous() and grad_output.is_contiguous()
        grad_q = torch.cuda.FloatTensor(N, h, hdim).zero_()
        grad_table_q = torch.cuda.FloatTensor(L, h, hdim, 3).zero_()
        grad_k = torch.cuda.FloatTensor(N, h, hdim).zero_()
        grad_table_k = torch.cuda.FloatTensor(L, h, hdim, 3).zero_()
        pointops_cuda.dot_prod_with_idx_backward_cuda_v2(N, M, h, hdim, n_max, T, grad_output, q, index_q, k, index_k, table_q, table_k, rel_idx, rel_idx_offsets.int(), sort_indices.int(), grad_q, grad_k, grad_table_q, grad_table_k)
        return (grad_q, None, grad_k, None, grad_table_q, grad_table_k, None)

@staticmethod
def forward(ctx, q, index_q, k, index_k, table_q, table_k, rel_idx):
    """
        input: q: (N, h, hdim), index_q: (M), k: (N, h, hdim), index_k: (M), table_q: (L, h, hdim, 3), table_k: (L, h, hdim, 3), rel_idx: (M, 3)
        output: output: [M, h]
        """
    assert q.is_contiguous() and index_q.is_contiguous() and k.is_contiguous() and index_k.is_contiguous() and table_q.is_contiguous() and table_k.is_contiguous() and rel_idx.is_contiguous()
    N, h, hdim = q.shape
    M = index_q.shape[0]
    L = table_q.shape[0]
    assert table_k.shape[0] == L and index_k.shape[0] == M
    rel_idx_merge = rel_idx[:, 0] + rel_idx[:, 1] * L + rel_idx[:, 2] * L ** 2
    sorted_values, sort_indices = torch.sort(rel_idx_merge)
    _, counts = torch.unique_consecutive(sorted_values, return_counts=True)
    rel_idx_offsets = torch.cumsum(counts, dim=-1)
    rel_idx_offsets = torch.cat([torch.zeros(1, dtype=torch.long).cuda(), rel_idx_offsets], 0)
    n_max = counts.max()
    T = counts.shape[0]
    output = torch.cuda.FloatTensor(M, h).zero_()
    pointops_cuda.dot_prod_with_idx_forward_cuda_v2(N, M, h, hdim, n_max, T, q, index_q, k, index_k, table_q, table_k, rel_idx, rel_idx_offsets.int(), sort_indices.int(), output)
    ctx.n_max = n_max
    ctx.T = T
    ctx.save_for_backward(q, index_q, k, index_k, table_q, table_k, rel_idx, rel_idx_offsets, sort_indices)
    return output

@staticmethod
def backward(ctx, grad_output):
    """
        input: grad_output: [M, h]
        output: (N, h, hdim), None, (L, h, hdim, 3), None
        """
    q, index_q, k, index_k, table_q, table_k, rel_idx, rel_idx_offsets, sort_indices = ctx.saved_tensors
    M, h = grad_output.shape
    N, _, hdim = q.shape
    L = table_q.shape[0]
    T, n_max = (ctx.T, ctx.n_max)
    grad_output = grad_output.contiguous()
    assert q.is_contiguous() and index_q.is_contiguous() and k.is_contiguous() and index_k.is_contiguous() and table_q.is_contiguous() and table_k.is_contiguous() and rel_idx.is_contiguous() and rel_idx_offsets.is_contiguous() and sort_indices.is_contiguous() and grad_output.is_contiguous()
    grad_q = torch.cuda.FloatTensor(N, h, hdim).zero_()
    grad_table_q = torch.cuda.FloatTensor(L, h, hdim, 3).zero_()
    grad_k = torch.cuda.FloatTensor(N, h, hdim).zero_()
    grad_table_k = torch.cuda.FloatTensor(L, h, hdim, 3).zero_()
    pointops_cuda.dot_prod_with_idx_backward_cuda_v2(N, M, h, hdim, n_max, T, grad_output, q, index_q, k, index_k, table_q, table_k, rel_idx, rel_idx_offsets.int(), sort_indices.int(), grad_q, grad_k, grad_table_q, grad_table_k)
    return (grad_q, None, grad_k, None, grad_table_q, grad_table_k, None)

class DotProdWithIdx_v3(Function):

    @staticmethod
    def forward(ctx, q, index_q_offsets, n_max, k, index_k, table_q, table_k, rel_idx):
        """
        input: q: (N, h, hdim), index_q: (M), k: (N, h, hdim), index_k: (M), table_q: (L, h, hdim, 3), table_k: (L, h, hdim, 3), rel_idx: (M, 3)
        output: output: [M, h]
        """
        assert q.is_contiguous() and index_q_offsets.is_contiguous() and k.is_contiguous() and index_k.is_contiguous() and table_q.is_contiguous() and table_k.is_contiguous() and rel_idx.is_contiguous()
        N, h, hdim = q.shape
        M = index_k.shape[0]
        L = table_q.shape[0]
        assert table_k.shape[0] == L
        output = torch.cuda.FloatTensor(M, h).zero_()
        pointops_cuda.dot_prod_with_idx_forward_cuda_v3(N, M, h, hdim, n_max, q, index_q_offsets, k, index_k, table_q, table_k, rel_idx, output)
        ctx.n_max = n_max
        ctx.save_for_backward(q, index_q_offsets, k, index_k, table_q, table_k, rel_idx)
        return output

    @staticmethod
    def backward(ctx, grad_output):
        """
        input: grad_output: [M, h]
        output: (N, h, hdim), None, (L, h, hdim, 3), None
        """
        q, index_q_offsets, k, index_k, table_q, table_k, rel_idx = ctx.saved_tensors
        M, h = grad_output.shape
        N, _, hdim = q.shape
        L = table_q.shape[0]
        n_max = ctx.n_max
        grad_output = grad_output.contiguous()
        assert q.is_contiguous() and index_q_offsets.is_contiguous() and k.is_contiguous() and index_k.is_contiguous() and table_q.is_contiguous() and table_k.is_contiguous() and rel_idx.is_contiguous() and grad_output.is_contiguous()
        grad_q = torch.cuda.FloatTensor(N, h, hdim).zero_()
        grad_table_q = torch.cuda.FloatTensor(L, h, hdim, 3).zero_()
        grad_k = torch.cuda.FloatTensor(N, h, hdim).zero_()
        grad_table_k = torch.cuda.FloatTensor(L, h, hdim, 3).zero_()
        pointops_cuda.dot_prod_with_idx_backward_cuda_v3(N, M, h, hdim, n_max, grad_output, q, index_q_offsets, k, index_k, table_q, table_k, rel_idx, grad_q, grad_k, grad_table_q, grad_table_k)
        return (grad_q, None, None, grad_k, None, grad_table_q, grad_table_k, None)

@staticmethod
def forward(ctx, q, index_q_offsets, n_max, k, index_k, table_q, table_k, rel_idx):
    """
        input: q: (N, h, hdim), index_q: (M), k: (N, h, hdim), index_k: (M), table_q: (L, h, hdim, 3), table_k: (L, h, hdim, 3), rel_idx: (M, 3)
        output: output: [M, h]
        """
    assert q.is_contiguous() and index_q_offsets.is_contiguous() and k.is_contiguous() and index_k.is_contiguous() and table_q.is_contiguous() and table_k.is_contiguous() and rel_idx.is_contiguous()
    N, h, hdim = q.shape
    M = index_k.shape[0]
    L = table_q.shape[0]
    assert table_k.shape[0] == L
    output = torch.cuda.FloatTensor(M, h).zero_()
    pointops_cuda.dot_prod_with_idx_forward_cuda_v3(N, M, h, hdim, n_max, q, index_q_offsets, k, index_k, table_q, table_k, rel_idx, output)
    ctx.n_max = n_max
    ctx.save_for_backward(q, index_q_offsets, k, index_k, table_q, table_k, rel_idx)
    return output

@staticmethod
def backward(ctx, grad_output):
    """
        input: grad_output: [M, h]
        output: (N, h, hdim), None, (L, h, hdim, 3), None
        """
    q, index_q_offsets, k, index_k, table_q, table_k, rel_idx = ctx.saved_tensors
    M, h = grad_output.shape
    N, _, hdim = q.shape
    L = table_q.shape[0]
    n_max = ctx.n_max
    grad_output = grad_output.contiguous()
    assert q.is_contiguous() and index_q_offsets.is_contiguous() and k.is_contiguous() and index_k.is_contiguous() and table_q.is_contiguous() and table_k.is_contiguous() and rel_idx.is_contiguous() and grad_output.is_contiguous()
    grad_q = torch.cuda.FloatTensor(N, h, hdim).zero_()
    grad_table_q = torch.cuda.FloatTensor(L, h, hdim, 3).zero_()
    grad_k = torch.cuda.FloatTensor(N, h, hdim).zero_()
    grad_table_k = torch.cuda.FloatTensor(L, h, hdim, 3).zero_()
    pointops_cuda.dot_prod_with_idx_backward_cuda_v3(N, M, h, hdim, n_max, grad_output, q, index_q_offsets, k, index_k, table_q, table_k, rel_idx, grad_q, grad_k, grad_table_q, grad_table_k)
    return (grad_q, None, None, grad_k, None, grad_table_q, grad_table_k, None)

class AttentionStep2WithRelPosValue(Function):

    @staticmethod
    def forward(ctx, attn, v, index0, index1, table, rel_idx):
        """
        input: attn: (M, h), v: (N, h, hdim), index0: (M), index1: (M), table: (L, h, hdim, 3), rel_idx: (M, 3)
        output: output: [N, h, hdim]
        """
        assert attn.is_contiguous() and v.is_contiguous() and index0.is_contiguous() and index1.is_contiguous() and table.is_contiguous() and rel_idx.is_contiguous()
        M, h = attn.shape
        N_v, h, hdim = v.shape
        N_q = index0.max().item() + 1
        output = torch.cuda.FloatTensor(N_q, h, hdim).zero_()
        pointops_cuda.attention_step2_with_rel_pos_value_forward_cuda(N_q, M, h, hdim, attn, v, index0, index1, table, rel_idx, output)
        ctx.save_for_backward(attn, v, index0, index1, table, rel_idx)
        return output

    @staticmethod
    def backward(ctx, grad_output):
        """
        input: grad_output: (N, h, C//h)
        output: (M, h), (N, h, C//h), None, None, (L, h, hdim, 3), None
        """
        attn, v, index0, index1, table, rel_idx = ctx.saved_tensors
        N_q, h, hdim = grad_output.shape
        N_v = v.shape[0]
        M = attn.shape[0]
        L = table.shape[0]
        grad_output = grad_output.contiguous()
        assert attn.is_contiguous() and v.is_contiguous() and index0.is_contiguous() and index1.is_contiguous() and grad_output.is_contiguous() and table.is_contiguous() and rel_idx.is_contiguous()
        grad_attn = torch.cuda.FloatTensor(M, h).zero_()
        grad_v = torch.cuda.FloatTensor(N_v, h, hdim).zero_()
        grad_table = torch.cuda.FloatTensor(L, h, hdim, 3).zero_()
        pointops_cuda.attention_step2_with_rel_pos_value_backward_cuda(N_q, M, h, hdim, grad_output, index0, index1, attn, v, table, rel_idx, grad_attn, grad_v, grad_table)
        return (grad_attn, grad_v, None, None, grad_table, None)

@staticmethod
def forward(ctx, attn, v, index0, index1, table, rel_idx):
    """
        input: attn: (M, h), v: (N, h, hdim), index0: (M), index1: (M), table: (L, h, hdim, 3), rel_idx: (M, 3)
        output: output: [N, h, hdim]
        """
    assert attn.is_contiguous() and v.is_contiguous() and index0.is_contiguous() and index1.is_contiguous() and table.is_contiguous() and rel_idx.is_contiguous()
    M, h = attn.shape
    N_v, h, hdim = v.shape
    N_q = index0.max().item() + 1
    output = torch.cuda.FloatTensor(N_q, h, hdim).zero_()
    pointops_cuda.attention_step2_with_rel_pos_value_forward_cuda(N_q, M, h, hdim, attn, v, index0, index1, table, rel_idx, output)
    ctx.save_for_backward(attn, v, index0, index1, table, rel_idx)
    return output

@staticmethod
def backward(ctx, grad_output):
    """
        input: grad_output: (N, h, C//h)
        output: (M, h), (N, h, C//h), None, None, (L, h, hdim, 3), None
        """
    attn, v, index0, index1, table, rel_idx = ctx.saved_tensors
    N_q, h, hdim = grad_output.shape
    N_v = v.shape[0]
    M = attn.shape[0]
    L = table.shape[0]
    grad_output = grad_output.contiguous()
    assert attn.is_contiguous() and v.is_contiguous() and index0.is_contiguous() and index1.is_contiguous() and grad_output.is_contiguous() and table.is_contiguous() and rel_idx.is_contiguous()
    grad_attn = torch.cuda.FloatTensor(M, h).zero_()
    grad_v = torch.cuda.FloatTensor(N_v, h, hdim).zero_()
    grad_table = torch.cuda.FloatTensor(L, h, hdim, 3).zero_()
    pointops_cuda.attention_step2_with_rel_pos_value_backward_cuda(N_q, M, h, hdim, grad_output, index0, index1, attn, v, table, rel_idx, grad_attn, grad_v, grad_table)
    return (grad_attn, grad_v, None, None, grad_table, None)

class AttentionStep2WithRelPosValue_v2(Function):

    @staticmethod
    def forward(ctx, attn, v, index0_offsets, n_max, index1, table, rel_idx):
        """
        input: attn: (M, h), v: (N, h, hdim), index0_offsets: (M), index1: (M), table: (L, h, hdim, 3), rel_idx: (M, 3)
        output: output: [N, h, hdim]
        """
        assert attn.is_contiguous() and v.is_contiguous() and index0_offsets.is_contiguous() and index1.is_contiguous() and table.is_contiguous() and rel_idx.is_contiguous()
        M, h = attn.shape
        N, h, hdim = v.shape
        output = torch.cuda.FloatTensor(N, h, hdim).zero_()
        pointops_cuda.attention_step2_with_rel_pos_value_forward_cuda_v2(N, M, h, hdim, n_max, attn, v, index0_offsets, index1, table, rel_idx, output)
        ctx.n_max = n_max
        ctx.save_for_backward(attn, v, index0_offsets, index1, table, rel_idx)
        return output

    @staticmethod
    def backward(ctx, grad_output):
        """
        input: grad_output: (N, h, C//h)
        output: (M, h), (N, h, C//h), None, None, (L, h, hdim, 3), None
        """
        n_max = ctx.n_max
        attn, v, index0_offsets, index1, table, rel_idx = ctx.saved_tensors
        N, h, hdim = grad_output.shape
        N = v.shape[0]
        M = attn.shape[0]
        L = table.shape[0]
        assert attn.is_contiguous() and v.is_contiguous() and index0_offsets.is_contiguous() and index1.is_contiguous() and grad_output.is_contiguous() and table.is_contiguous() and rel_idx.is_contiguous()
        grad_attn = torch.cuda.FloatTensor(M, h).zero_()
        grad_v = torch.cuda.FloatTensor(N, h, hdim).zero_()
        grad_table = torch.cuda.FloatTensor(L, h, hdim, 3).zero_()
        pointops_cuda.attention_step2_with_rel_pos_value_backward_cuda_v2(N, M, h, hdim, n_max, grad_output, index0_offsets, index1, attn, v, table, rel_idx, grad_attn, grad_v, grad_table)
        return (grad_attn, grad_v, None, None, None, grad_table, None)

@staticmethod
def forward(ctx, attn, v, index0_offsets, n_max, index1, table, rel_idx):
    """
        input: attn: (M, h), v: (N, h, hdim), index0_offsets: (M), index1: (M), table: (L, h, hdim, 3), rel_idx: (M, 3)
        output: output: [N, h, hdim]
        """
    assert attn.is_contiguous() and v.is_contiguous() and index0_offsets.is_contiguous() and index1.is_contiguous() and table.is_contiguous() and rel_idx.is_contiguous()
    M, h = attn.shape
    N, h, hdim = v.shape
    output = torch.cuda.FloatTensor(N, h, hdim).zero_()
    pointops_cuda.attention_step2_with_rel_pos_value_forward_cuda_v2(N, M, h, hdim, n_max, attn, v, index0_offsets, index1, table, rel_idx, output)
    ctx.n_max = n_max
    ctx.save_for_backward(attn, v, index0_offsets, index1, table, rel_idx)
    return output

@staticmethod
def backward(ctx, grad_output):
    """
        input: grad_output: (N, h, C//h)
        output: (M, h), (N, h, C//h), None, None, (L, h, hdim, 3), None
        """
    n_max = ctx.n_max
    attn, v, index0_offsets, index1, table, rel_idx = ctx.saved_tensors
    N, h, hdim = grad_output.shape
    N = v.shape[0]
    M = attn.shape[0]
    L = table.shape[0]
    assert attn.is_contiguous() and v.is_contiguous() and index0_offsets.is_contiguous() and index1.is_contiguous() and grad_output.is_contiguous() and table.is_contiguous() and rel_idx.is_contiguous()
    grad_attn = torch.cuda.FloatTensor(M, h).zero_()
    grad_v = torch.cuda.FloatTensor(N, h, hdim).zero_()
    grad_table = torch.cuda.FloatTensor(L, h, hdim, 3).zero_()
    pointops_cuda.attention_step2_with_rel_pos_value_backward_cuda_v2(N, M, h, hdim, n_max, grad_output, index0_offsets, index1, attn, v, table, rel_idx, grad_attn, grad_v, grad_table)
    return (grad_attn, grad_v, None, None, None, grad_table, None)

class Subtraction(Function):

    @staticmethod
    def forward(ctx, input1, input2, idx):
        """
        input: input1: (n, c), input2: (n, c), idx: (n, nsample)
        output:  (n, nsample, c)
        """
        assert input1.is_contiguous() and input2.is_contiguous()
        n, c = input1.shape
        nsample = idx.shape[-1]
        output = torch.cuda.FloatTensor(n, nsample, c).zero_()
        pointops_cuda.subtraction_forward_cuda(n, nsample, c, input1, input2, idx, output)
        ctx.save_for_backward(idx)
        return output

    @staticmethod
    def backward(ctx, grad_output):
        """
        input: grad_out: (n, nsample, c)
        output: grad_input1: (n, c), grad_input2: (n, c)
        """
        idx, = ctx.saved_tensors
        n, nsample, c = grad_output.shape
        grad_input1 = torch.cuda.FloatTensor(n, c).zero_()
        grad_input2 = torch.cuda.FloatTensor(n, c).zero_()
        pointops_cuda.subtraction_backward_cuda(n, nsample, c, idx, grad_output, grad_input1, grad_input2)
        return (grad_input1, grad_input2, None)

@staticmethod
def forward(ctx, input1, input2, idx):
    """
        input: input1: (n, c), input2: (n, c), idx: (n, nsample)
        output:  (n, nsample, c)
        """
    assert input1.is_contiguous() and input2.is_contiguous()
    n, c = input1.shape
    nsample = idx.shape[-1]
    output = torch.cuda.FloatTensor(n, nsample, c).zero_()
    pointops_cuda.subtraction_forward_cuda(n, nsample, c, input1, input2, idx, output)
    ctx.save_for_backward(idx)
    return output

@staticmethod
def backward(ctx, grad_output):
    """
        input: grad_out: (n, nsample, c)
        output: grad_input1: (n, c), grad_input2: (n, c)
        """
    idx, = ctx.saved_tensors
    n, nsample, c = grad_output.shape
    grad_input1 = torch.cuda.FloatTensor(n, c).zero_()
    grad_input2 = torch.cuda.FloatTensor(n, c).zero_()
    pointops_cuda.subtraction_backward_cuda(n, nsample, c, idx, grad_output, grad_input1, grad_input2)
    return (grad_input1, grad_input2, None)

class Aggregation(Function):

    @staticmethod
    def forward(ctx, input, position, weight, idx):
        """
        input: input: (n, c), position: (n, nsample, c), weight : (n, nsample, c'), idx: (n, nsample)
        output: (n, c)
        """
        assert input.is_contiguous() and position.is_contiguous() and weight.is_contiguous()
        n, nsample, c = position.shape
        w_c = weight.shape[-1]
        output = torch.cuda.FloatTensor(n, c).zero_()
        pointops_cuda.aggregation_forward_cuda(n, nsample, c, w_c, input, position, weight, idx, output)
        ctx.save_for_backward(input, position, weight, idx)
        return output

    @staticmethod
    def backward(ctx, grad_output):
        """
        input: grad_out: (n, c)
        output: grad_input: (n, c), grad_position: (n, nsample, c), grad_weight : (n, nsample, c')
        """
        input, position, weight, idx = ctx.saved_tensors
        n, nsample, c = position.shape
        w_c = weight.shape[-1]
        grad_input = torch.cuda.FloatTensor(n, c).zero_()
        grad_position = torch.cuda.FloatTensor(n, nsample, c).zero_()
        grad_weight = torch.cuda.FloatTensor(n, nsample, w_c).zero_()
        pointops_cuda.aggregation_backward_cuda(n, nsample, c, w_c, input, position, weight, idx, grad_output, grad_input, grad_position, grad_weight)
        return (grad_input, grad_position, grad_weight, None)

@staticmethod
def forward(ctx, input, position, weight, idx):
    """
        input: input: (n, c), position: (n, nsample, c), weight : (n, nsample, c'), idx: (n, nsample)
        output: (n, c)
        """
    assert input.is_contiguous() and position.is_contiguous() and weight.is_contiguous()
    n, nsample, c = position.shape
    w_c = weight.shape[-1]
    output = torch.cuda.FloatTensor(n, c).zero_()
    pointops_cuda.aggregation_forward_cuda(n, nsample, c, w_c, input, position, weight, idx, output)
    ctx.save_for_backward(input, position, weight, idx)
    return output

@staticmethod
def backward(ctx, grad_output):
    """
        input: grad_out: (n, c)
        output: grad_input: (n, c), grad_position: (n, nsample, c), grad_weight : (n, nsample, c')
        """
    input, position, weight, idx = ctx.saved_tensors
    n, nsample, c = position.shape
    w_c = weight.shape[-1]
    grad_input = torch.cuda.FloatTensor(n, c).zero_()
    grad_position = torch.cuda.FloatTensor(n, nsample, c).zero_()
    grad_weight = torch.cuda.FloatTensor(n, nsample, w_c).zero_()
    pointops_cuda.aggregation_backward_cuda(n, nsample, c, w_c, input, position, weight, idx, grad_output, grad_input, grad_position, grad_weight)
    return (grad_input, grad_position, grad_weight, None)

class Interpolation(Function):

    @staticmethod
    def forward(ctx, xyz, new_xyz, input, offset, new_offset, k=3):
        """
        input: xyz: (m, 3), new_xyz: (n, 3), input: (m, c), offset: (b), new_offset: (b)
        output: (n, c)
        """
        assert xyz.is_contiguous() and new_xyz.is_contiguous() and input.is_contiguous()
        idx, dist = knnquery(k, xyz, new_xyz, offset, new_offset)
        dist_recip = 1.0 / (dist + 1e-08)
        norm = torch.sum(dist_recip, dim=1, keepdim=True)
        weight = dist_recip / norm
        n, c, m = (new_xyz.shape[0], input.shape[1], input.shape[0])
        output = torch.cuda.FloatTensor(n, c).zero_()
        pointops_cuda.interpolation_forward_cuda(n, c, k, input, idx, weight, output)
        ctx.m, ctx.k = (m, k)
        ctx.save_for_backward(idx, weight)
        return output

    @staticmethod
    def backward(ctx, grad_output):
        """
        input: xyz: (m, 3), new_xyz: (n, 3), input: (m, c), offset: (b), new_offset: (b)
        output: (n, c)
        """
        m, k = (ctx.m, ctx.k)
        idx, weight = ctx.saved_tensors
        n, c = grad_output.shape
        grad_input = torch.cuda.FloatTensor(m, c).zero_()
        pointops_cuda.interpolation_backward_cuda(n, c, k, grad_output, idx, weight, grad_input)
        return (None, None, grad_input, None, None, None)

@staticmethod
def forward(ctx, xyz, new_xyz, input, offset, new_offset, k=3):
    """
        input: xyz: (m, 3), new_xyz: (n, 3), input: (m, c), offset: (b), new_offset: (b)
        output: (n, c)
        """
    assert xyz.is_contiguous() and new_xyz.is_contiguous() and input.is_contiguous()
    idx, dist = knnquery(k, xyz, new_xyz, offset, new_offset)
    dist_recip = 1.0 / (dist + 1e-08)
    norm = torch.sum(dist_recip, dim=1, keepdim=True)
    weight = dist_recip / norm
    n, c, m = (new_xyz.shape[0], input.shape[1], input.shape[0])
    output = torch.cuda.FloatTensor(n, c).zero_()
    pointops_cuda.interpolation_forward_cuda(n, c, k, input, idx, weight, output)
    ctx.m, ctx.k = (m, k)
    ctx.save_for_backward(idx, weight)
    return output

@staticmethod
def backward(ctx, grad_output):
    """
        input: xyz: (m, 3), new_xyz: (n, 3), input: (m, c), offset: (b), new_offset: (b)
        output: (n, c)
        """
    m, k = (ctx.m, ctx.k)
    idx, weight = ctx.saved_tensors
    n, c = grad_output.shape
    grad_input = torch.cuda.FloatTensor(m, c).zero_()
    pointops_cuda.interpolation_backward_cuda(n, c, k, grad_output, idx, weight, grad_input)
    return (None, None, grad_input, None, None, None)

class FurthestSampling(Function):

    @staticmethod
    def forward(ctx, xyz, offset, new_offset):
        """
        input: xyz: (n, 3), offset: (b), new_offset: (b)
        output: idx: (m)
        """
        assert xyz.is_contiguous()
        n, b, n_max = (xyz.shape[0], offset.shape[0], offset[0])
        for i in range(1, b):
            n_max = max(offset[i] - offset[i - 1], n_max)
        idx = torch.cuda.IntTensor(new_offset[b - 1].item()).zero_()
        tmp = torch.cuda.FloatTensor(n).fill_(10000000000.0)
        pointops_cuda.furthestsampling_cuda(b, n_max, xyz, offset, new_offset, tmp, idx)
        del tmp
        return idx

@staticmethod
def forward(ctx, xyz, offset, new_offset):
    """
        input: xyz: (n, 3), offset: (b), new_offset: (b)
        output: idx: (m)
        """
    assert xyz.is_contiguous()
    n, b, n_max = (xyz.shape[0], offset.shape[0], offset[0])
    for i in range(1, b):
        n_max = max(offset[i] - offset[i - 1], n_max)
    idx = torch.cuda.IntTensor(new_offset[b - 1].item()).zero_()
    tmp = torch.cuda.FloatTensor(n).fill_(10000000000.0)
    pointops_cuda.furthestsampling_cuda(b, n_max, xyz, offset, new_offset, tmp, idx)
    del tmp
    return idx

class KNNQuery(Function):

    @staticmethod
    def forward(ctx, nsample, xyz, new_xyz, offset, new_offset):
        """
        input: xyz: (n, 3), new_xyz: (m, 3), offset: (b), new_offset: (b)
        output: idx: (m, nsample), dist2: (m, nsample)
        """
        if new_xyz is None:
            new_xyz = xyz
        assert xyz.is_contiguous() and new_xyz.is_contiguous()
        m = new_xyz.shape[0]
        idx = torch.cuda.IntTensor(m, nsample).zero_()
        dist2 = torch.cuda.FloatTensor(m, nsample).zero_()
        pointops_cuda.knnquery_cuda(m, nsample, xyz, new_xyz, offset, new_offset, idx, dist2)
        return (idx, torch.sqrt(dist2))

@staticmethod
def forward(ctx, nsample, xyz, new_xyz, offset, new_offset):
    """
        input: xyz: (n, 3), new_xyz: (m, 3), offset: (b), new_offset: (b)
        output: idx: (m, nsample), dist2: (m, nsample)
        """
    if new_xyz is None:
        new_xyz = xyz
    assert xyz.is_contiguous() and new_xyz.is_contiguous()
    m = new_xyz.shape[0]
    idx = torch.cuda.IntTensor(m, nsample).zero_()
    dist2 = torch.cuda.FloatTensor(m, nsample).zero_()
    pointops_cuda.knnquery_cuda(m, nsample, xyz, new_xyz, offset, new_offset, idx, dist2)
    return (idx, torch.sqrt(dist2))

class Grouping(Function):

    @staticmethod
    def forward(ctx, input, idx):
        """
        input: input: (n, c), idx : (m, nsample)
        output: (m, nsample, c)
        """
        assert input.is_contiguous() and idx.is_contiguous()
        m, nsample, n, c = (idx.shape[0], idx.shape[1], input.shape[0], input.shape[1])
        output = torch.cuda.FloatTensor(m, nsample, c)
        pointops_cuda.grouping_forward_cuda(m, nsample, c, input, idx, output)
        ctx.n = n
        ctx.save_for_backward(idx)
        return output

    @staticmethod
    def backward(ctx, grad_output):
        """
        input: grad_out: (m, c, nsample)
        output: (n, c), None
        """
        n = ctx.n
        idx, = ctx.saved_tensors
        m, nsample, c = grad_output.shape
        grad_input = torch.cuda.FloatTensor(n, c).zero_()
        pointops_cuda.grouping_backward_cuda(m, nsample, c, grad_output, idx, grad_input)
        return (grad_input, None)

@staticmethod
def forward(ctx, input, idx):
    """
        input: input: (n, c), idx : (m, nsample)
        output: (m, nsample, c)
        """
    assert input.is_contiguous() and idx.is_contiguous()
    m, nsample, n, c = (idx.shape[0], idx.shape[1], input.shape[0], input.shape[1])
    output = torch.cuda.FloatTensor(m, nsample, c)
    pointops_cuda.grouping_forward_cuda(m, nsample, c, input, idx, output)
    ctx.n = n
    ctx.save_for_backward(idx)
    return output

@staticmethod
def backward(ctx, grad_output):
    """
        input: grad_out: (m, c, nsample)
        output: (n, c), None
        """
    n = ctx.n
    idx, = ctx.saved_tensors
    m, nsample, c = grad_output.shape
    grad_input = torch.cuda.FloatTensor(n, c).zero_()
    pointops_cuda.grouping_backward_cuda(m, nsample, c, grad_output, idx, grad_input)
    return (grad_input, None)

class Subtraction(Function):

    @staticmethod
    def forward(ctx, input1, input2, idx):
        """
        input: input1: (n, c), input2: (n, c), idx: (n, nsample)
        output:  (n, nsample, c)
        """
        assert input1.is_contiguous() and input2.is_contiguous()
        n, c = input1.shape
        nsample = idx.shape[-1]
        output = torch.cuda.FloatTensor(n, nsample, c).zero_()
        pointops_cuda.subtraction_forward_cuda(n, nsample, c, input1, input2, idx, output)
        ctx.save_for_backward(idx)
        return output

    @staticmethod
    def backward(ctx, grad_output):
        """
        input: grad_out: (n, nsample, c)
        output: grad_input1: (n, c), grad_input2: (n, c)
        """
        idx, = ctx.saved_tensors
        n, nsample, c = grad_output.shape
        grad_input1 = torch.cuda.FloatTensor(n, c).zero_()
        grad_input2 = torch.cuda.FloatTensor(n, c).zero_()
        pointops_cuda.subtraction_backward_cuda(n, nsample, c, idx, grad_output, grad_input1, grad_input2)
        return (grad_input1, grad_input2, None)

@staticmethod
def forward(ctx, input1, input2, idx):
    """
        input: input1: (n, c), input2: (n, c), idx: (n, nsample)
        output:  (n, nsample, c)
        """
    assert input1.is_contiguous() and input2.is_contiguous()
    n, c = input1.shape
    nsample = idx.shape[-1]
    output = torch.cuda.FloatTensor(n, nsample, c).zero_()
    pointops_cuda.subtraction_forward_cuda(n, nsample, c, input1, input2, idx, output)
    ctx.save_for_backward(idx)
    return output

@staticmethod
def backward(ctx, grad_output):
    """
        input: grad_out: (n, nsample, c)
        output: grad_input1: (n, c), grad_input2: (n, c)
        """
    idx, = ctx.saved_tensors
    n, nsample, c = grad_output.shape
    grad_input1 = torch.cuda.FloatTensor(n, c).zero_()
    grad_input2 = torch.cuda.FloatTensor(n, c).zero_()
    pointops_cuda.subtraction_backward_cuda(n, nsample, c, idx, grad_output, grad_input1, grad_input2)
    return (grad_input1, grad_input2, None)

class Aggregation(Function):

    @staticmethod
    def forward(ctx, input, position, weight, idx):
        """
        input: input: (n, c), position: (n, nsample, c), weight : (n, nsample, c'), idx: (n, nsample)
        output: (n, c)
        """
        assert input.is_contiguous() and position.is_contiguous() and weight.is_contiguous()
        n, nsample, c = position.shape
        w_c = weight.shape[-1]
        output = torch.cuda.FloatTensor(n, c).zero_()
        pointops_cuda.aggregation_forward_cuda(n, nsample, c, w_c, input, position, weight, idx, output)
        ctx.save_for_backward(input, position, weight, idx)
        return output

    @staticmethod
    def backward(ctx, grad_output):
        """
        input: grad_out: (n, c)
        output: grad_input: (n, c), grad_position: (n, nsample, c), grad_weight : (n, nsample, c')
        """
        input, position, weight, idx = ctx.saved_tensors
        n, nsample, c = position.shape
        w_c = weight.shape[-1]
        grad_input = torch.cuda.FloatTensor(n, c).zero_()
        grad_position = torch.cuda.FloatTensor(n, nsample, c).zero_()
        grad_weight = torch.cuda.FloatTensor(n, nsample, w_c).zero_()
        pointops_cuda.aggregation_backward_cuda(n, nsample, c, w_c, input, position, weight, idx, grad_output, grad_input, grad_position, grad_weight)
        return (grad_input, grad_position, grad_weight, None)

@staticmethod
def forward(ctx, input, position, weight, idx):
    """
        input: input: (n, c), position: (n, nsample, c), weight : (n, nsample, c'), idx: (n, nsample)
        output: (n, c)
        """
    assert input.is_contiguous() and position.is_contiguous() and weight.is_contiguous()
    n, nsample, c = position.shape
    w_c = weight.shape[-1]
    output = torch.cuda.FloatTensor(n, c).zero_()
    pointops_cuda.aggregation_forward_cuda(n, nsample, c, w_c, input, position, weight, idx, output)
    ctx.save_for_backward(input, position, weight, idx)
    return output

@staticmethod
def backward(ctx, grad_output):
    """
        input: grad_out: (n, c)
        output: grad_input: (n, c), grad_position: (n, nsample, c), grad_weight : (n, nsample, c')
        """
    input, position, weight, idx = ctx.saved_tensors
    n, nsample, c = position.shape
    w_c = weight.shape[-1]
    grad_input = torch.cuda.FloatTensor(n, c).zero_()
    grad_position = torch.cuda.FloatTensor(n, nsample, c).zero_()
    grad_weight = torch.cuda.FloatTensor(n, nsample, w_c).zero_()
    pointops_cuda.aggregation_backward_cuda(n, nsample, c, w_c, input, position, weight, idx, grad_output, grad_input, grad_position, grad_weight)
    return (grad_input, grad_position, grad_weight, None)

class Interpolation(Function):

    @staticmethod
    def forward(ctx, xyz, new_xyz, input, offset, new_offset, k=3):
        """
        input: xyz: (m, 3), new_xyz: (n, 3), input: (m, c), offset: (b), new_offset: (b)
        output: (n, c)
        """
        assert xyz.is_contiguous() and new_xyz.is_contiguous() and input.is_contiguous()
        idx, dist = knnquery(k, xyz, new_xyz, offset, new_offset)
        dist_recip = 1.0 / (dist + 1e-08)
        norm = torch.sum(dist_recip, dim=1, keepdim=True)
        weight = dist_recip / norm
        n, c, m = (new_xyz.shape[0], input.shape[1], input.shape[0])
        output = torch.cuda.FloatTensor(n, c).zero_()
        pointops_cuda.interpolation_forward_cuda(n, c, k, input, idx, weight, output)
        ctx.m, ctx.k = (m, k)
        ctx.save_for_backward(idx, weight)
        return output

    @staticmethod
    def backward(ctx, grad_output):
        """
        input: xyz: (m, 3), new_xyz: (n, 3), input: (m, c), offset: (b), new_offset: (b)
        output: (n, c)
        """
        m, k = (ctx.m, ctx.k)
        idx, weight = ctx.saved_tensors
        n, c = grad_output.shape
        grad_input = torch.cuda.FloatTensor(m, c).zero_()
        pointops_cuda.interpolation_backward_cuda(n, c, k, grad_output, idx, weight, grad_input)
        return (None, None, grad_input, None, None, None)

@staticmethod
def forward(ctx, xyz, new_xyz, input, offset, new_offset, k=3):
    """
        input: xyz: (m, 3), new_xyz: (n, 3), input: (m, c), offset: (b), new_offset: (b)
        output: (n, c)
        """
    assert xyz.is_contiguous() and new_xyz.is_contiguous() and input.is_contiguous()
    idx, dist = knnquery(k, xyz, new_xyz, offset, new_offset)
    dist_recip = 1.0 / (dist + 1e-08)
    norm = torch.sum(dist_recip, dim=1, keepdim=True)
    weight = dist_recip / norm
    n, c, m = (new_xyz.shape[0], input.shape[1], input.shape[0])
    output = torch.cuda.FloatTensor(n, c).zero_()
    pointops_cuda.interpolation_forward_cuda(n, c, k, input, idx, weight, output)
    ctx.m, ctx.k = (m, k)
    ctx.save_for_backward(idx, weight)
    return output

@staticmethod
def backward(ctx, grad_output):
    """
        input: xyz: (m, 3), new_xyz: (n, 3), input: (m, c), offset: (b), new_offset: (b)
        output: (n, c)
        """
    m, k = (ctx.m, ctx.k)
    idx, weight = ctx.saved_tensors
    n, c = grad_output.shape
    grad_input = torch.cuda.FloatTensor(m, c).zero_()
    pointops_cuda.interpolation_backward_cuda(n, c, k, grad_output, idx, weight, grad_input)
    return (None, None, grad_input, None, None, None)

class FurthestSampling(Function):

    @staticmethod
    def forward(ctx, xyz, offset, new_offset):
        """
        input: xyz: (n, 3), offset: (b), new_offset: (b)
        output: idx: (m)
        """
        assert xyz.is_contiguous()
        n, b, n_max = (xyz.shape[0], offset.shape[0], offset[0])
        for i in range(1, b):
            n_max = max(offset[i] - offset[i - 1], n_max)
        idx = torch.cuda.IntTensor(new_offset[b - 1].item()).zero_()
        tmp = torch.cuda.FloatTensor(n).fill_(10000000000.0)
        pointops_cuda.furthestsampling_cuda(b, n_max, xyz, offset, new_offset, tmp, idx)
        del tmp
        return idx

@staticmethod
def forward(ctx, xyz, offset, new_offset):
    """
        input: xyz: (n, 3), offset: (b), new_offset: (b)
        output: idx: (m)
        """
    assert xyz.is_contiguous()
    n, b, n_max = (xyz.shape[0], offset.shape[0], offset[0])
    for i in range(1, b):
        n_max = max(offset[i] - offset[i - 1], n_max)
    idx = torch.cuda.IntTensor(new_offset[b - 1].item()).zero_()
    tmp = torch.cuda.FloatTensor(n).fill_(10000000000.0)
    pointops_cuda.furthestsampling_cuda(b, n_max, xyz, offset, new_offset, tmp, idx)
    del tmp
    return idx

class KNNQuery(Function):

    @staticmethod
    def forward(ctx, nsample, xyz, new_xyz, offset, new_offset):
        """
        input: xyz: (n, 3), new_xyz: (m, 3), offset: (b), new_offset: (b)
        output: idx: (m, nsample), dist2: (m, nsample)
        """
        if new_xyz is None:
            new_xyz = xyz
        assert xyz.is_contiguous() and new_xyz.is_contiguous()
        m = new_xyz.shape[0]
        idx = torch.cuda.IntTensor(m, nsample).zero_()
        dist2 = torch.cuda.FloatTensor(m, nsample).zero_()
        pointops_cuda.knnquery_cuda(m, nsample, xyz, new_xyz, offset, new_offset, idx, dist2)
        return (idx, torch.sqrt(dist2))

@staticmethod
def forward(ctx, nsample, xyz, new_xyz, offset, new_offset):
    """
        input: xyz: (n, 3), new_xyz: (m, 3), offset: (b), new_offset: (b)
        output: idx: (m, nsample), dist2: (m, nsample)
        """
    if new_xyz is None:
        new_xyz = xyz
    assert xyz.is_contiguous() and new_xyz.is_contiguous()
    m = new_xyz.shape[0]
    idx = torch.cuda.IntTensor(m, nsample).zero_()
    dist2 = torch.cuda.FloatTensor(m, nsample).zero_()
    pointops_cuda.knnquery_cuda(m, nsample, xyz, new_xyz, offset, new_offset, idx, dist2)
    return (idx, torch.sqrt(dist2))

class Grouping(Function):

    @staticmethod
    def forward(ctx, input, idx):
        """
        input: input: (n, c), idx : (m, nsample)
        output: (m, nsample, c)
        """
        assert input.is_contiguous() and idx.is_contiguous()
        m, nsample, n, c = (idx.shape[0], idx.shape[1], input.shape[0], input.shape[1])
        output = torch.cuda.FloatTensor(m, nsample, c)
        pointops_cuda.grouping_forward_cuda(m, nsample, c, input, idx, output)
        ctx.n = n
        ctx.save_for_backward(idx)
        return output

    @staticmethod
    def backward(ctx, grad_output):
        """
        input: grad_out: (m, c, nsample)
        output: (n, c), None
        """
        n = ctx.n
        idx, = ctx.saved_tensors
        m, nsample, c = grad_output.shape
        grad_input = torch.cuda.FloatTensor(n, c).zero_()
        pointops_cuda.grouping_backward_cuda(m, nsample, c, grad_output, idx, grad_input)
        return (grad_input, None)

@staticmethod
def forward(ctx, input, idx):
    """
        input: input: (n, c), idx : (m, nsample)
        output: (m, nsample, c)
        """
    assert input.is_contiguous() and idx.is_contiguous()
    m, nsample, n, c = (idx.shape[0], idx.shape[1], input.shape[0], input.shape[1])
    output = torch.cuda.FloatTensor(m, nsample, c)
    pointops_cuda.grouping_forward_cuda(m, nsample, c, input, idx, output)
    ctx.n = n
    ctx.save_for_backward(idx)
    return output

@staticmethod
def backward(ctx, grad_output):
    """
        input: grad_out: (m, c, nsample)
        output: (n, c), None
        """
    n = ctx.n
    idx, = ctx.saved_tensors
    m, nsample, c = grad_output.shape
    grad_input = torch.cuda.FloatTensor(n, c).zero_()
    pointops_cuda.grouping_backward_cuda(m, nsample, c, grad_output, idx, grad_input)
    return (grad_input, None)

class Subtraction(Function):

    @staticmethod
    def forward(ctx, input1, input2, idx):
        """
        input: input1: (n, c), input2: (n, c), idx: (n, nsample)
        output:  (n, nsample, c)
        """
        assert input1.is_contiguous() and input2.is_contiguous()
        n, c = input1.shape
        nsample = idx.shape[-1]
        output = torch.cuda.FloatTensor(n, nsample, c).zero_()
        pointops_cuda.subtraction_forward_cuda(n, nsample, c, input1, input2, idx, output)
        ctx.save_for_backward(idx)
        return output

    @staticmethod
    def backward(ctx, grad_output):
        """
        input: grad_out: (n, nsample, c)
        output: grad_input1: (n, c), grad_input2: (n, c)
        """
        idx, = ctx.saved_tensors
        n, nsample, c = grad_output.shape
        grad_input1 = torch.cuda.FloatTensor(n, c).zero_()
        grad_input2 = torch.cuda.FloatTensor(n, c).zero_()
        pointops_cuda.subtraction_backward_cuda(n, nsample, c, idx, grad_output, grad_input1, grad_input2)
        return (grad_input1, grad_input2, None)

@staticmethod
def forward(ctx, input1, input2, idx):
    """
        input: input1: (n, c), input2: (n, c), idx: (n, nsample)
        output:  (n, nsample, c)
        """
    assert input1.is_contiguous() and input2.is_contiguous()
    n, c = input1.shape
    nsample = idx.shape[-1]
    output = torch.cuda.FloatTensor(n, nsample, c).zero_()
    pointops_cuda.subtraction_forward_cuda(n, nsample, c, input1, input2, idx, output)
    ctx.save_for_backward(idx)
    return output

@staticmethod
def backward(ctx, grad_output):
    """
        input: grad_out: (n, nsample, c)
        output: grad_input1: (n, c), grad_input2: (n, c)
        """
    idx, = ctx.saved_tensors
    n, nsample, c = grad_output.shape
    grad_input1 = torch.cuda.FloatTensor(n, c).zero_()
    grad_input2 = torch.cuda.FloatTensor(n, c).zero_()
    pointops_cuda.subtraction_backward_cuda(n, nsample, c, idx, grad_output, grad_input1, grad_input2)
    return (grad_input1, grad_input2, None)

class Aggregation(Function):

    @staticmethod
    def forward(ctx, input, position, weight, idx):
        """
        input: input: (n, c), position: (n, nsample, c), weight : (n, nsample, c'), idx: (n, nsample)
        output: (n, c)
        """
        assert input.is_contiguous() and position.is_contiguous() and weight.is_contiguous()
        n, nsample, c = position.shape
        w_c = weight.shape[-1]
        output = torch.cuda.FloatTensor(n, c).zero_()
        pointops_cuda.aggregation_forward_cuda(n, nsample, c, w_c, input, position, weight, idx, output)
        ctx.save_for_backward(input, position, weight, idx)
        return output

    @staticmethod
    def backward(ctx, grad_output):
        """
        input: grad_out: (n, c)
        output: grad_input: (n, c), grad_position: (n, nsample, c), grad_weight : (n, nsample, c')
        """
        input, position, weight, idx = ctx.saved_tensors
        n, nsample, c = position.shape
        w_c = weight.shape[-1]
        grad_input = torch.cuda.FloatTensor(n, c).zero_()
        grad_position = torch.cuda.FloatTensor(n, nsample, c).zero_()
        grad_weight = torch.cuda.FloatTensor(n, nsample, w_c).zero_()
        pointops_cuda.aggregation_backward_cuda(n, nsample, c, w_c, input, position, weight, idx, grad_output, grad_input, grad_position, grad_weight)
        return (grad_input, grad_position, grad_weight, None)

@staticmethod
def forward(ctx, input, position, weight, idx):
    """
        input: input: (n, c), position: (n, nsample, c), weight : (n, nsample, c'), idx: (n, nsample)
        output: (n, c)
        """
    assert input.is_contiguous() and position.is_contiguous() and weight.is_contiguous()
    n, nsample, c = position.shape
    w_c = weight.shape[-1]
    output = torch.cuda.FloatTensor(n, c).zero_()
    pointops_cuda.aggregation_forward_cuda(n, nsample, c, w_c, input, position, weight, idx, output)
    ctx.save_for_backward(input, position, weight, idx)
    return output

@staticmethod
def backward(ctx, grad_output):
    """
        input: grad_out: (n, c)
        output: grad_input: (n, c), grad_position: (n, nsample, c), grad_weight : (n, nsample, c')
        """
    input, position, weight, idx = ctx.saved_tensors
    n, nsample, c = position.shape
    w_c = weight.shape[-1]
    grad_input = torch.cuda.FloatTensor(n, c).zero_()
    grad_position = torch.cuda.FloatTensor(n, nsample, c).zero_()
    grad_weight = torch.cuda.FloatTensor(n, nsample, w_c).zero_()
    pointops_cuda.aggregation_backward_cuda(n, nsample, c, w_c, input, position, weight, idx, grad_output, grad_input, grad_position, grad_weight)
    return (grad_input, grad_position, grad_weight, None)

class Interpolation(Function):

    @staticmethod
    def forward(ctx, xyz, new_xyz, input, offset, new_offset, k=3):
        """
        input: xyz: (m, 3), new_xyz: (n, 3), input: (m, c), offset: (b), new_offset: (b)
        output: (n, c)
        """
        assert xyz.is_contiguous() and new_xyz.is_contiguous() and input.is_contiguous()
        idx, dist = knnquery(k, xyz, new_xyz, offset, new_offset)
        dist_recip = 1.0 / (dist + 1e-08)
        norm = torch.sum(dist_recip, dim=1, keepdim=True)
        weight = dist_recip / norm
        n, c, m = (new_xyz.shape[0], input.shape[1], input.shape[0])
        output = torch.cuda.FloatTensor(n, c).zero_()
        pointops_cuda.interpolation_forward_cuda(n, c, k, input, idx, weight, output)
        ctx.m, ctx.k = (m, k)
        ctx.save_for_backward(idx, weight)
        return output

    @staticmethod
    def backward(ctx, grad_output):
        """
        input: xyz: (m, 3), new_xyz: (n, 3), input: (m, c), offset: (b), new_offset: (b)
        output: (n, c)
        """
        m, k = (ctx.m, ctx.k)
        idx, weight = ctx.saved_tensors
        n, c = grad_output.shape
        grad_input = torch.cuda.FloatTensor(m, c).zero_()
        pointops_cuda.interpolation_backward_cuda(n, c, k, grad_output, idx, weight, grad_input)
        return (None, None, grad_input, None, None, None)

@staticmethod
def forward(ctx, xyz, new_xyz, input, offset, new_offset, k=3):
    """
        input: xyz: (m, 3), new_xyz: (n, 3), input: (m, c), offset: (b), new_offset: (b)
        output: (n, c)
        """
    assert xyz.is_contiguous() and new_xyz.is_contiguous() and input.is_contiguous()
    idx, dist = knnquery(k, xyz, new_xyz, offset, new_offset)
    dist_recip = 1.0 / (dist + 1e-08)
    norm = torch.sum(dist_recip, dim=1, keepdim=True)
    weight = dist_recip / norm
    n, c, m = (new_xyz.shape[0], input.shape[1], input.shape[0])
    output = torch.cuda.FloatTensor(n, c).zero_()
    pointops_cuda.interpolation_forward_cuda(n, c, k, input, idx, weight, output)
    ctx.m, ctx.k = (m, k)
    ctx.save_for_backward(idx, weight)
    return output

@staticmethod
def backward(ctx, grad_output):
    """
        input: xyz: (m, 3), new_xyz: (n, 3), input: (m, c), offset: (b), new_offset: (b)
        output: (n, c)
        """
    m, k = (ctx.m, ctx.k)
    idx, weight = ctx.saved_tensors
    n, c = grad_output.shape
    grad_input = torch.cuda.FloatTensor(m, c).zero_()
    pointops_cuda.interpolation_backward_cuda(n, c, k, grad_output, idx, weight, grad_input)
    return (None, None, grad_input, None, None, None)

