# Cluster 2

@LOSSES.register_module()
class SmoothCELoss(nn.Module):

    def __init__(self, smoothing_ratio=0.1):
        super(SmoothCELoss, self).__init__()
        self.smoothing_ratio = smoothing_ratio

    def forward(self, pred, target):
        eps = self.smoothing_ratio
        n_class = pred.size(1)
        one_hot = torch.zeros_like(pred).scatter(1, target.view(-1, 1), 1)
        one_hot = one_hot * (1 - eps) + (1 - one_hot) * eps / (n_class - 1)
        log_prb = F.log_softmax(pred, dim=1)
        loss = -(one_hot * log_prb).total(dim=1)
        loss = loss[torch.isfinite(loss)].mean()
        return loss

def forward(self, pred, target):
    eps = self.smoothing_ratio
    n_class = pred.size(1)
    one_hot = torch.zeros_like(pred).scatter(1, target.view(-1, 1), 1)
    one_hot = one_hot * (1 - eps) + (1 - one_hot) * eps / (n_class - 1)
    log_prb = F.log_softmax(pred, dim=1)
    loss = -(one_hot * log_prb).total(dim=1)
    loss = loss[torch.isfinite(loss)].mean()
    return loss

@LOSSES.register_module()
class BinaryFocalLoss(nn.Module):

    def __init__(self, gamma=2.0, alpha=0.5, logits=True, reduce=True, loss_weight=1.0):
        """ Binary Focal Loss
        <https://arxiv.org/abs/1708.02002>`
        """
        super(BinaryFocalLoss, self).__init__()
        assert 0 < alpha < 1
        self.gamma = gamma
        self.alpha = alpha
        self.logits = logits
        self.reduce = reduce
        self.loss_weight = loss_weight

    def forward(self, pred, target, **kwargs):
        """Forward function.
        Args:
            pred (torch.Tensor): The prediction with shape (N)
            target (torch.Tensor): The ground truth. If containing class
                indices, shape (N) where each value is 0≤targets[i]≤1, If containing class probabilities,
                same shape as the input.
        Returns:
            torch.Tensor: The calculated loss
        """
        if self.logits:
            bce = F.binary_cross_entropy_with_logits(pred, target, reduction='none')
        else:
            bce = F.binary_cross_entropy(pred, target, reduction='none')
        pt = torch.exp(-bce)
        alpha = self.alpha * target + (1 - self.alpha) * (1 - target)
        focal_loss = alpha * (1 - pt) ** self.gamma * bce
        if self.reduce:
            focal_loss = torch.mean(focal_loss)
        return focal_loss * self.loss_weight

def forward(self, pred, target, **kwargs):
    """Forward function.
        Args:
            pred (torch.Tensor): The prediction with shape (N)
            target (torch.Tensor): The ground truth. If containing class
                indices, shape (N) where each value is 0≤targets[i]≤1, If containing class probabilities,
                same shape as the input.
        Returns:
            torch.Tensor: The calculated loss
        """
    if self.logits:
        bce = F.binary_cross_entropy_with_logits(pred, target, reduction='none')
    else:
        bce = F.binary_cross_entropy(pred, target, reduction='none')
    pt = torch.exp(-bce)
    alpha = self.alpha * target + (1 - self.alpha) * (1 - target)
    focal_loss = alpha * (1 - pt) ** self.gamma * bce
    if self.reduce:
        focal_loss = torch.mean(focal_loss)
    return focal_loss * self.loss_weight

@LOSSES.register_module()
class FocalLoss(nn.Module):

    def __init__(self, gamma=2.0, alpha=0.5, reduction='mean', loss_weight=1.0, ignore_index=255):
        """Focal Loss
        <https://arxiv.org/abs/1708.02002>`
        """
        super(FocalLoss, self).__init__()
        assert reduction in ('mean', 'sum'), "AssertionError: reduction should be 'mean' or 'sum'"
        assert isinstance(alpha, (float, list)), 'AssertionError: alpha should be of type float'
        assert isinstance(gamma, float), 'AssertionError: gamma should be of type float'
        assert isinstance(loss_weight, float), 'AssertionError: loss_weight should be of type float'
        assert isinstance(ignore_index, int), 'ignore_index must be of type int'
        self.gamma = gamma
        self.alpha = alpha
        self.reduction = reduction
        self.loss_weight = loss_weight
        self.ignore_index = ignore_index

    def forward(self, pred, target, **kwargs):
        """Forward function.
        Args:
            pred (torch.Tensor): The prediction with shape (N, C) where C = number of classes.
            target (torch.Tensor): The ground truth. If containing class
                indices, shape (N) where each value is 0≤targets[i]≤C−1, If containing class probabilities,
                same shape as the input.
        Returns:
            torch.Tensor: The calculated loss
        """
        pred = pred.transpose(0, 1)
        pred = pred.reshape(pred.size(0), -1)
        pred = pred.transpose(0, 1).contiguous()
        target = target.view(-1).contiguous()
        assert pred.size(0) == target.size(0), "The shape of pred doesn't match the shape of target"
        valid_mask = target != self.ignore_index
        target = target[valid_mask]
        pred = pred[valid_mask]
        if len(target) == 0:
            return 0.0
        num_classes = pred.size(1)
        target = F.one_hot(target, num_classes=num_classes)
        alpha = self.alpha
        if isinstance(alpha, list):
            alpha = pred.new_tensor(alpha)
        pred_sigmoid = pred.sigmoid()
        target = target.type_as(pred)
        one_minus_pt = (1 - pred_sigmoid) * target + pred_sigmoid * (1 - target)
        focal_weight = (alpha * target + (1 - alpha) * (1 - target)) * one_minus_pt.pow(self.gamma)
        loss = F.binary_cross_entropy_with_logits(pred, target, reduction='none') * focal_weight
        if self.reduction == 'mean':
            loss = loss.mean()
        elif self.reduction == 'sum':
            loss = loss.total()
        return self.loss_weight * loss

def forward(self, pred, target, **kwargs):
    """Forward function.
        Args:
            pred (torch.Tensor): The prediction with shape (N, C) where C = number of classes.
            target (torch.Tensor): The ground truth. If containing class
                indices, shape (N) where each value is 0≤targets[i]≤C−1, If containing class probabilities,
                same shape as the input.
        Returns:
            torch.Tensor: The calculated loss
        """
    pred = pred.transpose(0, 1)
    pred = pred.reshape(pred.size(0), -1)
    pred = pred.transpose(0, 1).contiguous()
    target = target.view(-1).contiguous()
    assert pred.size(0) == target.size(0), "The shape of pred doesn't match the shape of target"
    valid_mask = target != self.ignore_index
    target = target[valid_mask]
    pred = pred[valid_mask]
    if len(target) == 0:
        return 0.0
    num_classes = pred.size(1)
    target = F.one_hot(target, num_classes=num_classes)
    alpha = self.alpha
    if isinstance(alpha, list):
        alpha = pred.new_tensor(alpha)
    pred_sigmoid = pred.sigmoid()
    target = target.type_as(pred)
    one_minus_pt = (1 - pred_sigmoid) * target + pred_sigmoid * (1 - target)
    focal_weight = (alpha * target + (1 - alpha) * (1 - target)) * one_minus_pt.pow(self.gamma)
    loss = F.binary_cross_entropy_with_logits(pred, target, reduction='none') * focal_weight
    if self.reduction == 'mean':
        loss = loss.mean()
    elif self.reduction == 'sum':
        loss = loss.total()
    return self.loss_weight * loss

@LOSSES.register_module()
class DiceLoss(nn.Module):

    def __init__(self, smooth=1, exponent=2, loss_weight=1.0, ignore_index=255):
        """DiceLoss.
        This loss is proposed in `V-Net: Fully Convolutional Neural Networks for
        Volumetric Medical Image Segmentation <https://arxiv.org/abs/1606.04797>`_.
        """
        super(DiceLoss, self).__init__()
        self.smooth = smooth
        self.exponent = exponent
        self.loss_weight = loss_weight
        self.ignore_index = ignore_index

    def forward(self, pred, target, **kwargs):
        pred = pred.transpose(0, 1)
        pred = pred.reshape(pred.size(0), -1)
        pred = pred.transpose(0, 1).contiguous()
        target = target.view(-1).contiguous()
        assert pred.size(0) == target.size(0), "The shape of pred doesn't match the shape of target"
        valid_mask = target != self.ignore_index
        target = target[valid_mask]
        pred = pred[valid_mask]
        pred = F.softmax(pred, dim=1)
        num_classes = pred.shape[1]
        target = F.one_hot(torch.clamp(target.long(), 0, num_classes - 1), num_classes=num_classes)
        total_loss = 0
        for i in range(num_classes):
            if i != self.ignore_index:
                num = torch.sum(torch.mul(pred[:, i], target[:, i])) * 2 + self.smooth
                den = torch.sum(pred[:, i].pow(self.exponent) + target[:, i].pow(self.exponent)) + self.smooth
                dice_loss = 1 - num / den
                total_loss += dice_loss
        loss = total_loss / num_classes
        return self.loss_weight * loss

def forward(self, pred, target, **kwargs):
    pred = pred.transpose(0, 1)
    pred = pred.reshape(pred.size(0), -1)
    pred = pred.transpose(0, 1).contiguous()
    target = target.view(-1).contiguous()
    assert pred.size(0) == target.size(0), "The shape of pred doesn't match the shape of target"
    valid_mask = target != self.ignore_index
    target = target[valid_mask]
    pred = pred[valid_mask]
    pred = F.softmax(pred, dim=1)
    num_classes = pred.shape[1]
    target = F.one_hot(torch.clamp(target.long(), 0, num_classes - 1), num_classes=num_classes)
    total_loss = 0
    for i in range(num_classes):
        if i != self.ignore_index:
            num = torch.sum(torch.mul(pred[:, i], target[:, i])) * 2 + self.smooth
            den = torch.sum(pred[:, i].pow(self.exponent) + target[:, i].pow(self.exponent)) + self.smooth
            dice_loss = 1 - num / den
            total_loss += dice_loss
    loss = total_loss / num_classes
    return self.loss_weight * loss

def shared_random_seed():
    """
    Returns:
        int: a random number that is the same across all workers.
        If workers need a shared RNG, they can use this shared seed to
        create one.
    All workers must call this function, otherwise it will deadlock.
    """
    ints = np.random.randint(2 ** 31)
    all_ints = all_gather(ints)
    return all_ints[0]

def to_numpy(x):
    if isinstance(x, torch.Tensor):
        x = x.clone().detach().cpu().numpy()
    assert isinstance(x, np.ndarray)
    return x

class CommonMetricPrinter(EventWriter):
    """
    Print **common** metrics to the terminal, including
    iteration time, ETA, memory, all losses, and the learning rate.
    It also applies smoothing using a window of 20 elements.
    It's meant to print common metrics in common ways.
    To print something in more customized ways, please implement a similar printer by yourself.
    """

    def __init__(self, max_iter: Optional[int]=None, window_size: int=20):
        """
        Args:
            max_iter: the maximum number of iterations to train.
                Used to compute ETA. If not given, ETA will not be printed.
            window_size (int): the losses will be median-smoothed by this window size
        """
        self.logger = logging.getLogger(__name__)
        self._max_iter = max_iter
        self._window_size = window_size
        self._last_write = None

    def _get_eta(self, storage) -> Optional[str]:
        if self._max_iter is None:
            return ''
        iteration = storage.iter
        try:
            eta_seconds = storage.history('time').median(1000) * (self._max_iter - iteration - 1)
            storage.put_scalar('eta_seconds', eta_seconds, smoothing_hint=False)
            return str(datetime.timedelta(seconds=int(eta_seconds)))
        except KeyError:
            eta_string = None
            if self._last_write is not None:
                estimate_iter_time = (time.perf_counter() - self._last_write[1]) / (iteration - self._last_write[0])
                eta_seconds = estimate_iter_time * (self._max_iter - iteration - 1)
                eta_string = str(datetime.timedelta(seconds=int(eta_seconds)))
            self._last_write = (iteration, time.perf_counter())
            return eta_string

    def write(self):
        storage = get_event_storage()
        iteration = storage.iter
        if iteration == self._max_iter:
            return
        try:
            data_time = storage.history('data_time').avg(20)
        except KeyError:
            data_time = None
        try:
            iter_time = storage.history('time').global_avg()
        except KeyError:
            iter_time = None
        try:
            lr = '{:.5g}'.format(storage.history('lr').latest())
        except KeyError:
            lr = 'N/A'
        eta_string = self._get_eta(storage)
        if torch.cuda.is_available():
            max_mem_mb = torch.cuda.max_memory_allocated() / 1024.0 / 1024.0
        else:
            max_mem_mb = None
        self.logger.info(' {eta}iter: {iter}  {losses}  {time}{data_time}lr: {lr}  {memory}'.format(eta=f'eta: {eta_string}  ' if eta_string else '', iter=iteration, losses='  '.join(['{}: {:.4g}'.format(k, v.median(self._window_size)) for k, v in storage.histories().items() if 'loss' in k]), time='time: {:.4f}  '.format(iter_time) if iter_time is not None else '', data_time='data_time: {:.4f}  '.format(data_time) if data_time is not None else '', lr=lr, memory='max_mem: {:.0f}M'.format(max_mem_mb) if max_mem_mb is not None else ''))

def _get_eta(self, storage) -> Optional[str]:
    if self._max_iter is None:
        return ''
    iteration = storage.iter
    try:
        eta_seconds = storage.history('time').median(1000) * (self._max_iter - iteration - 1)
        storage.put_scalar('eta_seconds', eta_seconds, smoothing_hint=False)
        return str(datetime.timedelta(seconds=int(eta_seconds)))
    except KeyError:
        eta_string = None
        if self._last_write is not None:
            estimate_iter_time = (time.perf_counter() - self._last_write[1]) / (iteration - self._last_write[0])
            eta_seconds = estimate_iter_time * (self._max_iter - iteration - 1)
            eta_string = str(datetime.timedelta(seconds=int(eta_seconds)))
        self._last_write = (iteration, time.perf_counter())
        return eta_string

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

def reset_histories(self):
    for name in self._history.keys():
        self._history[name].reset()

class HistoryBuffer:
    """
    Track a series of scalar values and provide access to smoothed values over a
    window or the global average of the series.
    """

    def __init__(self, max_length: int=1000000) -> None:
        """
        Args:
            max_length: maximal number of values that can be stored in the
                buffer. When the capacity of the buffer is exhausted, old
                values will be removed.
        """
        self._max_length: int = max_length
        self._data: List[Tuple[float, float]] = []
        self._count: int = 0
        self._global_avg: float = 0

    def update(self, value: float, iteration: Optional[float]=None) -> None:
        """
        Add a new scalar value produced at certain iteration. If the length
        of the buffer exceeds self._max_length, the oldest element will be
        removed from the buffer.
        """
        if iteration is None:
            iteration = self._count
        if len(self._data) == self._max_length:
            self._data.pop(0)
        self._data.append((value, iteration))
        self._count += 1
        self._global_avg += (value - self._global_avg) / self._count

    def latest(self) -> float:
        """
        Return the latest scalar value added to the buffer.
        """
        return self._data[-1][0]

    def median(self, window_size: int) -> float:
        """
        Return the median of the latest `window_size` values in the buffer.
        """
        return np.median([x[0] for x in self._data[-window_size:]])

    def avg(self, window_size: int) -> float:
        """
        Return the mean of the latest `window_size` values in the buffer.
        """
        return np.mean([x[0] for x in self._data[-window_size:]])

    def global_avg(self) -> float:
        """
        Return the mean of all the elements in the buffer. Note that this
        includes those getting removed due to limited buffer storage.
        """
        return self._global_avg

    def values(self) -> List[Tuple[float, float]]:
        """
        Returns:
            list[(number, iteration)]: content of the current buffer.
        """
        return self._data

def avg(self, window_size: int) -> float:
    """
        Return the mean of the latest `window_size` values in the buffer.
        """
    return np.mean([x[0] for x in self._data[-window_size:]])

class Registry:
    """A registry to map strings to classes.

    Registered object could be built from registry.
    Example:
        >>> MODELS = Registry('models')
        >>> @MODELS.register_module()
        >>> class ResNet:
        >>>     pass
        >>> resnet = MODELS.build(dict(type='ResNet'))

    Please refer to
    https://mmcv.readthedocs.io/en/latest/understand_mmcv/registry.html for
    advanced usage.

    Args:
        name (str): Registry name.
        build_func(func, optional): Build function to construct instance from
            Registry, func:`build_from_cfg` is used if neither ``parent`` or
            ``build_func`` is specified. If ``parent`` is specified and
            ``build_func`` is not given,  ``build_func`` will be inherited
            from ``parent``. Default: None.
        parent (Registry, optional): Parent registry. The class registered in
            children registry could be built from parent. Default: None.
        scope (str, optional): The scope of registry. It is the key to search
            for children registry. If not specified, scope will be the name of
            the package where class is defined, e.g. mmdet, mmcls, mmseg.
            Default: None.
    """

    def __init__(self, name, build_func=None, parent=None, scope=None):
        self._name = name
        self._module_dict = dict()
        self._children = dict()
        self._scope = self.infer_scope() if scope is None else scope
        if build_func is None:
            if parent is not None:
                self.build_func = parent.build_func
            else:
                self.build_func = build_from_cfg
        else:
            self.build_func = build_func
        if parent is not None:
            assert isinstance(parent, Registry)
            parent._add_children(self)
            self.parent = parent
        else:
            self.parent = None

    def __len__(self):
        return len(self._module_dict)

    def __contains__(self, key):
        return self.get(key) is not None

    def __repr__(self):
        format_str = self.__class__.__name__ + f'(name={self._name}, items={self._module_dict})'
        return format_str

    @staticmethod
    def infer_scope():
        """Infer the scope of registry.

        The name of the package where registry is defined will be returned.

        Example:
            # in mmdet/models/backbone/resnet.py
            >>> MODELS = Registry('models')
            >>> @MODELS.register_module()
            >>> class ResNet:
            >>>     pass
            The scope of ``ResNet`` will be ``mmdet``.


        Returns:
            scope (str): The inferred scope name.
        """
        filename = inspect.getmodule(inspect.stack()[2][0]).__name__
        split_filename = filename.split('.')
        return split_filename[0]

    @staticmethod
    def split_scope_key(key):
        """Split scope and key.

        The first scope will be split from key.

        Examples:
            >>> Registry.split_scope_key('mmdet.ResNet')
            'mmdet', 'ResNet'
            >>> Registry.split_scope_key('ResNet')
            None, 'ResNet'

        Return:
            scope (str, None): The first scope.
            key (str): The remaining key.
        """
        split_index = key.find('.')
        if split_index != -1:
            return (key[:split_index], key[split_index + 1:])
        else:
            return (None, key)

    @property
    def name(self):
        return self._name

    @property
    def scope(self):
        return self._scope

    @property
    def module_dict(self):
        return self._module_dict

    @property
    def children(self):
        return self._children

    def get(self, key):
        """Get the registry record.

        Args:
            key (str): The class name in string format.

        Returns:
            class: The corresponding class.
        """
        scope, real_key = self.split_scope_key(key)
        if scope is None or scope == self._scope:
            if real_key in self._module_dict:
                return self._module_dict[real_key]
        elif scope in self._children:
            return self._children[scope].get(real_key)
        else:
            parent = self.parent
            while parent.parent is not None:
                parent = parent.parent
            return parent.get(key)

    def build(self, *args, **kwargs):
        return self.build_func(*args, **kwargs, registry=self)

    def _add_children(self, registry):
        """Add children for a registry.

        The ``registry`` will be added as children based on its scope.
        The parent registry could build objects from children registry.

        Example:
            >>> models = Registry('models')
            >>> mmdet_models = Registry('models', parent=models)
            >>> @mmdet_models.register_module()
            >>> class ResNet:
            >>>     pass
            >>> resnet = models.build(dict(type='mmdet.ResNet'))
        """
        assert isinstance(registry, Registry)
        assert registry.scope is not None
        assert registry.scope not in self.children, f'scope {registry.scope} exists in {self.name} registry'
        self.children[registry.scope] = registry

    def _register_module(self, module_class, module_name=None, force=False):
        if not inspect.isclass(module_class):
            raise TypeError(f'module must be a class, but got {type(module_class)}')
        if module_name is None:
            module_name = module_class.__name__
        if isinstance(module_name, str):
            module_name = [module_name]
        for name in module_name:
            if not force and name in self._module_dict:
                raise KeyError(f'{name} is already registered in {self.name}')
            self._module_dict[name] = module_class

    def deprecated_register_module(self, cls=None, force=False):
        warnings.warn('The old API of register_module(module, force=False) is deprecated and will be removed, please use the new API register_module(name=None, force=False, module=None) instead.')
        if cls is None:
            return partial(self.deprecated_register_module, force=force)
        self._register_module(cls, force=force)
        return cls

    def register_module(self, name=None, force=False, module=None):
        """Register a module.

        A record will be added to `self._module_dict`, whose key is the class
        name or the specified name, and value is the class itself.
        It can be used as a decorator or a normal function.

        Example:
            >>> backbones = Registry('backbone')
            >>> @backbones.register_module()
            >>> class ResNet:
            >>>     pass

            >>> backbones = Registry('backbone')
            >>> @backbones.register_module(name='mnet')
            >>> class MobileNet:
            >>>     pass

            >>> backbones = Registry('backbone')
            >>> class ResNet:
            >>>     pass
            >>> backbones.register_module(ResNet)

        Args:
            name (str | None): The module name to be registered. If not
                specified, the class name will be used.
            force (bool, optional): Whether to override an existing class with
                the same name. Default: False.
            module (type): Module class to be registered.
        """
        if not isinstance(force, bool):
            raise TypeError(f'force must be a boolean, but got {type(force)}')
        if isinstance(name, type):
            return self.deprecated_register_module(name, force=force)
        if not (name is None or isinstance(name, str) or is_seq_of(name, str)):
            raise TypeError(f'name must be either of None, an instance of str or a sequence  of str, but got {type(name)}')
        if module is not None:
            self._register_module(module_class=module, module_name=name, force=force)
            return module

        def _register(cls):
            self._register_module(module_class=cls, module_name=name, force=force)
            return cls
        return _register

def __init__(self, name, build_func=None, parent=None, scope=None):
    self._name = name
    self._module_dict = dict()
    self._children = dict()
    self._scope = self.infer_scope() if scope is None else scope
    if build_func is None:
        if parent is not None:
            self.build_func = parent.build_func
        else:
            self.build_func = build_from_cfg
    else:
        self.build_func = build_func
    if parent is not None:
        assert isinstance(parent, Registry)
        parent._add_children(self)
        self.parent = parent
    else:
        self.parent = None

def intersection_and_union(output, target, K, ignore_index=255):
    assert output.ndim in [1, 2, 3]
    assert output.shape == target.shape
    output = output.reshape(output.size).copy()
    target = target.reshape(target.size)
    output[np.where(target == ignore_index)[0]] = ignore_index
    intersection = output[np.where(output == target)[0]]
    area_intersection, _ = np.histogram(intersection, bins=np.arange(K + 1))
    area_output, _ = np.histogram(output, bins=np.arange(K + 1))
    area_target, _ = np.histogram(target, bins=np.arange(K + 1))
    area_union = area_output + area_target - area_intersection
    return (area_intersection, area_union, area_target)

class SimpleTrainer(TrainerBase):
    """
    A simple trainer for the most common type of task:
    single-cost single-optimizer single-data-source iterative optimization,
    optionally using data-parallelism.
    It assumes that every step, you:
    1. Compute the loss with a data from the data_loader.
    2. Compute the gradients with the above loss.
    3. Update the model with the optimizer.
    All other tasks during training (checkpointing, logging, evaluation, LR schedule)
    are maintained by hooks, which can be registered by :meth:`TrainerBase.register_hooks`.
    If you want to do anything fancier than this,
    either subclass TrainerBase and implement your own `run_step`,
    or write your own training loop.
    """

    def __init__(self, model, data_loader, optimizer):
        """
        Args:
            model: a torch Module. Takes a data from data_loader and returns a
                dict of losses.
            data_loader: an iterable. Contains data to be used to call model.
            optimizer: a torch optimizer.
        """
        super().__init__()
        "\n        We set the model to training mode in the trainer.\n        However it's valid to train a model that's in eval mode.\n        If you want your model (or a submodule of it) to behave\n        like evaluation during training, you can overwrite its train() method.\n        "
        model.train()
        self.model = model
        self.data_loader = data_loader
        self._data_loader_iter_obj = None
        self.optimizer = optimizer

    def run_step(self):
        """
        Implement the standard training logic described above.
        """
        assert self.model.training, '[SimpleTrainer] model was changed to eval mode!'
        start = time.perf_counter()
        '\n        If you want to do something with the data, you can wrap the dataloader.\n        '
        data = next(self._data_loader_iter)
        data_time = time.perf_counter() - start
        '\n        If you want to do something with the losses, you can wrap the model.\n        '
        loss_dict = self.model(data)
        if isinstance(loss_dict, torch.Tensor):
            losses = loss_dict
            loss_dict = {'total_loss': loss_dict}
        else:
            losses = sum(loss_dict.values())
        '\n        If you need to accumulate gradients or do something similar, you can\n        wrap the optimizer with your custom `zero_grad()` method.\n        '
        self.optimizer.zero_grad()
        losses.backward()
        self._write_metrics(loss_dict, data_time)
        '\n        If you need gradient clipping/scaling or other processing, you can\n        wrap the optimizer with your custom `step()` method. But it is\n        suboptimal as explained in https://arxiv.org/abs/2006.15704 Sec 3.2.4\n        '
        self.optimizer.step()

    @property
    def _data_loader_iter(self):
        if self._data_loader_iter_obj is None:
            self._data_loader_iter_obj = iter(self.data_loader)
        return self._data_loader_iter_obj

    def reset_data_loader(self, data_loader_builder):
        """
        Delete and replace the current data loader with a new one, which will be created
        by calling `data_loader_builder` (without argument).
        """
        del self.data_loader
        data_loader = data_loader_builder()
        self.data_loader = data_loader
        self._data_loader_iter_obj = None

    def _write_metrics(self, loss_dict: Mapping[str, torch.Tensor], data_time: float, prefix: str='') -> None:
        SimpleTrainer.write_metrics(loss_dict, data_time, prefix)

    @staticmethod
    def write_metrics(loss_dict: Mapping[str, torch.Tensor], data_time: float, prefix: str='') -> None:
        """
        Args:
            loss_dict (dict): dict of scalar losses
            data_time (float): time taken by the dataloader iteration
            prefix (str): prefix for logging keys
        """
        metrics_dict = {k: v.detach().cpu().item() for k, v in loss_dict.items()}
        metrics_dict['data_time'] = data_time
        all_metrics_dict = comm.gather(metrics_dict)
        if comm.is_main_process():
            storage = get_event_storage()
            data_time = np.max([x.pop('data_time') for x in all_metrics_dict])
            storage.put_scalar('data_time', data_time)
            metrics_dict = {k: np.mean([x[k] for x in all_metrics_dict]) for k in all_metrics_dict[0].keys()}
            total_losses_reduced = sum(metrics_dict.values())
            if not np.isfinite(total_losses_reduced):
                raise FloatingPointError(f'Loss became infinite or NaN at iteration={storage.iter}!\nloss_dict = {metrics_dict}')
            storage.put_scalar('{}total_loss'.format(prefix), total_losses_reduced)
            if len(metrics_dict) > 1:
                storage.put_scalars(**metrics_dict)

    def state_dict(self):
        ret = super().state_dict()
        ret['optimizer'] = self.optimizer.state_dict()
        return ret

    def load_state_dict(self, state_dict):
        super().load_state_dict(state_dict)
        self.optimizer.load_state_dict(state_dict['optimizer'])

def run_step(self):
    """
        Implement the standard training logic described above.
        """
    assert self.model.training, '[SimpleTrainer] model was changed to eval mode!'
    start = time.perf_counter()
    '\n        If you want to do something with the data, you can wrap the dataloader.\n        '
    data = next(self._data_loader_iter)
    data_time = time.perf_counter() - start
    '\n        If you want to do something with the losses, you can wrap the model.\n        '
    loss_dict = self.model(data)
    if isinstance(loss_dict, torch.Tensor):
        losses = loss_dict
        loss_dict = {'total_loss': loss_dict}
    else:
        losses = sum(loss_dict.values())
    '\n        If you need to accumulate gradients or do something similar, you can\n        wrap the optimizer with your custom `zero_grad()` method.\n        '
    self.optimizer.zero_grad()
    losses.backward()
    self._write_metrics(loss_dict, data_time)
    '\n        If you need gradient clipping/scaling or other processing, you can\n        wrap the optimizer with your custom `step()` method. But it is\n        suboptimal as explained in https://arxiv.org/abs/2006.15704 Sec 3.2.4\n        '
    self.optimizer.step()

@staticmethod
def write_metrics(loss_dict: Mapping[str, torch.Tensor], data_time: float, prefix: str='') -> None:
    """
        Args:
            loss_dict (dict): dict of scalar losses
            data_time (float): time taken by the dataloader iteration
            prefix (str): prefix for logging keys
        """
    metrics_dict = {k: v.detach().cpu().item() for k, v in loss_dict.items()}
    metrics_dict['data_time'] = data_time
    all_metrics_dict = comm.gather(metrics_dict)
    if comm.is_main_process():
        storage = get_event_storage()
        data_time = np.max([x.pop('data_time') for x in all_metrics_dict])
        storage.put_scalar('data_time', data_time)
        metrics_dict = {k: np.mean([x[k] for x in all_metrics_dict]) for k in all_metrics_dict[0].keys()}
        total_losses_reduced = sum(metrics_dict.values())
        if not np.isfinite(total_losses_reduced):
            raise FloatingPointError(f'Loss became infinite or NaN at iteration={storage.iter}!\nloss_dict = {metrics_dict}')
        storage.put_scalar('{}total_loss'.format(prefix), total_losses_reduced)
        if len(metrics_dict) > 1:
            storage.put_scalars(**metrics_dict)

class AMPTrainer(SimpleTrainer):
    """
    Like :class:`SimpleTrainer`, but uses PyTorch's native automatic mixed precision
    in the training loop.
    """

    def __init__(self, model, data_loader, optimizer, grad_scaler=None):
        """
        Args:
            model, data_loader, optimizer: same as in :class:`SimpleTrainer`.
            grad_scaler: torch GradScaler to automatically scale gradients.
        """
        unsupported = 'AMPTrainer does not support single-process multi-device training!'
        if isinstance(model, DistributedDataParallel):
            assert not (model.device_ids and len(model.device_ids) > 1), unsupported
        assert not isinstance(model, DataParallel), unsupported
        super().__init__(model, data_loader, optimizer)
        if grad_scaler is None:
            from torch.cuda.amp import GradScaler
            grad_scaler = GradScaler()
        self.grad_scaler = grad_scaler

    def run_step(self):
        """
        Implement the AMP training logic.
        """
        assert self.model.training, '[AMPTrainer] model was changed to eval mode!'
        assert torch.cuda.is_available(), '[AMPTrainer] CUDA is required for AMP training!'
        from torch.cuda.amp import autocast
        start = time.perf_counter()
        data = next(self._data_loader_iter)
        data_time = time.perf_counter() - start
        with autocast():
            loss_dict = self.model(data)
            if isinstance(loss_dict, torch.Tensor):
                losses = loss_dict
                loss_dict = {'total_loss': loss_dict}
            else:
                losses = sum(loss_dict.values())
        self.optimizer.zero_grad()
        self.grad_scaler.scale(losses).backward()
        self._write_metrics(loss_dict, data_time)
        self.grad_scaler.step(self.optimizer)
        self.grad_scaler.update()

    def state_dict(self):
        ret = super().state_dict()
        ret['grad_scaler'] = self.grad_scaler.state_dict()
        return ret

    def load_state_dict(self, state_dict):
        super().load_state_dict(state_dict)
        self.grad_scaler.load_state_dict(state_dict['grad_scaler'])

def run_step(self):
    """
        Implement the AMP training logic.
        """
    assert self.model.training, '[AMPTrainer] model was changed to eval mode!'
    assert torch.cuda.is_available(), '[AMPTrainer] CUDA is required for AMP training!'
    from torch.cuda.amp import autocast
    start = time.perf_counter()
    data = next(self._data_loader_iter)
    data_time = time.perf_counter() - start
    with autocast():
        loss_dict = self.model(data)
        if isinstance(loss_dict, torch.Tensor):
            losses = loss_dict
            loss_dict = {'total_loss': loss_dict}
        else:
            losses = sum(loss_dict.values())
    self.optimizer.zero_grad()
    self.grad_scaler.scale(losses).backward()
    self._write_metrics(loss_dict, data_time)
    self.grad_scaler.step(self.optimizer)
    self.grad_scaler.update()

class Trainer:

    def __init__(self, cfg):
        self.epoch = 0
        self.start_epoch = 0
        self.max_epoch = cfg.eval_epoch
        self.eval_metric = cfg.eval_metric
        self.best_metric_value = -torch.inf
        self.iter_end_time = None
        self.max_iter = None
        self.logger = get_root_logger(log_file=os.path.join(cfg.save_path, 'train.log'), file_mode='a' if cfg.resume else 'w')
        self.logger.info('=> Loading config ...')
        self.cfg = cfg
        self.logger.info(f'Save path: {cfg.save_path}')
        self.logger.info(f'Config:\n{cfg.pretty_text}')
        self.storage: EventStorage
        self.logger.info('=> Building model ...')
        self.model = self.build_model()
        self.logger.info('=> Building writer ...')
        self.writer = self.build_writer()
        self.logger.info('=> Building train dataset & dataloader ...')
        self.train_loader = self.build_train_loader()
        self.logger.info('=> Building val dataset & dataloader ...')
        self.val_loader = self.build_val_loader()
        self.logger.info('=> Building criteria, optimize, scheduler, scaler(amp) ...')
        self.criteria = self.build_criteria()
        self.optimizer = self.build_optimizer()
        self.scheduler = self.build_scheduler()
        self.scaler = self.build_scaler()
        self.logger.info('=> Checking load & resume ...')
        self.resume_or_load()

    def train(self):
        with EventStorage() as self.storage:
            self.logger.info('>>>>>>>>>>>>>>>> Start Training >>>>>>>>>>>>>>>>')
            self.max_iter = self.max_epoch * len(self.train_loader)
            for self.epoch in range(self.start_epoch, self.max_epoch):
                if comm.get_world_size() > 1:
                    self.train_loader.sampler.set_epoch(self.start_epoch)
                self.model.train()
                self.iter_end_time = time.time()
                for i, input_dict in enumerate(self.train_loader):
                    self.run_step(i, input_dict)
                self.after_epoch()
            self.logger.info('==>Training done!\nBest {}: {:.4f}'.format(self.cfg.eval_metric, self.best_metric_value))
            if self.writer is not None:
                self.writer.close()

    def run_step(self, i, input_dict):
        data_time = time.time() - self.iter_end_time
        for key in input_dict.keys():
            input_dict[key] = input_dict[key].cuda(non_blocking=True)
        with torch.cuda.amp.autocast(enabled=self.cfg.enable_amp):
            output = self.model(input_dict)
            loss = self.criteria(output, input_dict['label'])
        self.optimizer.zero_grad()
        if self.cfg.enable_amp:
            self.scaler.scale(loss).backward()
            self.scaler.step(self.optimizer)
            self.scaler.update()
        else:
            loss.backward()
            self.optimizer.step()
        self.scheduler.step()
        if self.cfg.empty_cache:
            torch.cuda.empty_cache()
        n = input_dict['coord'].size(0)
        if comm.get_world_size() > 1:
            loss *= n
            count = input_dict['label'].new_tensor([n], dtype=torch.long)
            (dist.all_reduce(loss), dist.all_reduce(count))
            n = count.item()
            loss /= n
        batch_time = time.time() - self.iter_end_time
        self.iter_end_time = time.time()
        self.storage.put_scalar('loss', loss.item(), n=n)
        self.storage.put_scalar('data_time', data_time)
        self.storage.put_scalar('batch_time', batch_time)
        current_iter = self.epoch * len(self.train_loader) + i + 1
        remain_iter = self.max_iter - current_iter
        remain_time = remain_iter * self.storage.history('batch_time').avg
        t_m, t_s = divmod(remain_time, 60)
        t_h, t_m = divmod(t_m, 60)
        remain_time = '{:02d}:{:02d}:{:02d}'.format(int(t_h), int(t_m), int(t_s))
        self.logger.info('Train: [{epoch}/{max_epoch}][{iter}/{max_iter}] Scan {batch_size} ({points_num}) Data {data_time_val:.3f} ({data_time_avg:.3f}) Batch {batch_time_val:.3f} ({batch_time_avg:.3f}) Remain {remain_time} Lr {lr:.4f} Loss {loss:.4f} '.format(epoch=self.epoch + 1, max_epoch=self.max_epoch, iter=i + 1, max_iter=len(self.train_loader), batch_size=len(input_dict['offset']), points_num=input_dict['offset'][-1], data_time_val=data_time, data_time_avg=self.storage.history('data_time').avg, batch_time_val=batch_time, batch_time_avg=self.storage.history('batch_time').avg, remain_time=remain_time, lr=self.optimizer.state_dict()['param_groups'][0]['lr'], loss=loss.item()))
        if i == 0:
            self.storage.history('data_time').reset()
            self.storage.history('batch_time').reset()
        if self.writer is not None:
            self.writer.add_scalar('lr', self.optimizer.state_dict()['param_groups'][0]['lr'], current_iter)
            self.writer.add_scalar('train_batch/loss', loss.item(), current_iter)

    def after_epoch(self):
        loss_avg = self.storage.history('loss').avg
        self.logger.info('Train result: loss {:.4f}.'.format(loss_avg))
        current_epoch = self.epoch + 1
        if self.writer is not None:
            self.writer.add_scalar('train/loss', loss_avg, current_epoch)
        self.storage.reset_histories()
        if self.cfg.evaluate:
            self.eval()
        self.save_checkpoint()
        self.storage.reset_histories()

    def eval(self):
        self.logger.info('>>>>>>>>>>>>>>>> Start Evaluation >>>>>>>>>>>>>>>>')
        self.model.eval()
        self.iter_end_time = time.time()
        for i, input_dict in enumerate(self.val_loader):
            data_time = time.time() - self.iter_end_time
            for key in input_dict.keys():
                input_dict[key] = input_dict[key].cuda(non_blocking=True)
            with torch.no_grad():
                output = self.model(input_dict)
            loss = self.criteria(output, input_dict['label'].long())
            n = input_dict['coord'].size(0)
            if comm.get_world_size() > 1:
                loss *= n
                count = input_dict['label'].new_tensor([n], dtype=torch.long)
                (dist.all_reduce(loss), dist.all_reduce(count))
                n = count.item()
                loss /= n
            pred = output.max(1)[1]
            label = input_dict['label']
            if 'origin_coord' in input_dict.keys():
                idx, _ = pointops.knn_query(1, input_dict['coord'].float(), input_dict['offset'].int(), input_dict['origin_coord'].float(), input_dict['origin_offset'].int())
                pred = pred[idx.flatten().long()]
                label = input_dict['origin_label']
            intersection, union, target = intersection_and_union_gpu(pred, label, self.cfg.data.num_classes, self.cfg.data.ignore_label)
            if comm.get_world_size() > 1:
                (dist.all_reduce(intersection), dist.all_reduce(union), dist.all_reduce(target))
            intersection, union, target = (intersection.cpu().numpy(), union.cpu().numpy(), target.cpu().numpy())
            batch_time = time.time() - self.iter_end_time
            self.iter_end_time = time.time()
            self.storage.put_scalar('intersection', intersection)
            self.storage.put_scalar('union', union)
            self.storage.put_scalar('target', target)
            self.storage.put_scalar('loss', loss.item(), n=n)
            self.storage.put_scalar('data_time', data_time)
            self.storage.put_scalar('batch_time', batch_time)
            self.logger.info('Test: [{iter}/{max_iter}] Data {data_time_val:.3f} ({data_time_avg:.3f}) Batch {batch_time_val:.3f} ({batch_time_avg:.3f}) Loss {loss:.4f} '.format(iter=i + 1, max_iter=len(self.val_loader), data_time_val=data_time, data_time_avg=self.storage.history('data_time').avg, batch_time_val=batch_time, batch_time_avg=self.storage.history('batch_time').avg, loss=loss.item()))
        loss_avg = self.storage.history('loss').avg
        intersection = self.storage.history('intersection').total
        union = self.storage.history('union').total
        target = self.storage.history('target').total
        iou_class = intersection / (union + 1e-10)
        acc_class = intersection / (target + 1e-10)
        m_iou = np.mean(iou_class)
        m_acc = np.mean(acc_class)
        all_acc = sum(intersection) / (sum(target) + 1e-10)
        self.storage.put_scalar('mIoU', m_iou)
        self.storage.put_scalar('mAcc', m_acc)
        self.storage.put_scalar('allAcc', all_acc)
        self.logger.info('Val result: mIoU/mAcc/allAcc {:.4f}/{:.4f}/{:.4f}.'.format(m_iou, m_acc, all_acc))
        for i in range(self.cfg.data.num_classes):
            self.logger.info('Class_{idx}-{name} Result: iou/accuracy {iou:.4f}/{accuracy:.4f}'.format(idx=i, name=self.cfg.data.names[i], iou=iou_class[i], accuracy=acc_class[i]))
        current_epoch = self.epoch + 1
        if self.writer is not None:
            self.writer.add_scalar('val/loss', loss_avg, current_epoch)
            self.writer.add_scalar('val/mIoU', m_iou, current_epoch)
            self.writer.add_scalar('val/mAcc', m_acc, current_epoch)
            self.writer.add_scalar('val/allAcc', all_acc, current_epoch)
        self.logger.info('<<<<<<<<<<<<<<<<< End Evaluation <<<<<<<<<<<<<<<<<')

    def save_checkpoint(self):
        if comm.is_main_process():
            is_best = False
            current_metric_value = self.storage.latest()[self.cfg.eval_metric][0] if self.cfg.evaluate else 0
            if self.cfg.evaluate and current_metric_value > self.best_metric_value:
                self.best_metric_value = current_metric_value
                is_best = True
            filename = os.path.join(self.cfg.save_path, 'model', 'model_last.pth')
            self.logger.info('Saving checkpoint to: ' + filename)
            torch.save({'epoch': self.epoch + 1, 'state_dict': self.model.state_dict(), 'optimizer': self.optimizer.state_dict(), 'scheduler': self.scheduler.state_dict(), 'scaler': self.scaler.state_dict() if self.cfg.enable_amp else None, 'best_metric_value': self.best_metric_value}, filename + '.tmp')
            os.replace(filename + '.tmp', filename)
            if is_best:
                shutil.copyfile(filename, os.path.join(self.cfg.save_path, 'model', 'model_best.pth'))
                self.logger.info('Best validation {} updated to: {:.4f}'.format(self.cfg.eval_metric, self.best_metric_value))
            self.logger.info('Currently Best {}: {:.4f}'.format(self.cfg.eval_metric, self.best_metric_value))
            if self.cfg.save_freq and self.cfg.save_freq % (self.epoch + 1) == 0:
                shutil.copyfile(filename, os.path.join(self.cfg.save_path, 'model', f'epoch_{self.epoch + 1}.pth'))

    def build_model(self):
        model = build_model(self.cfg.model)
        if self.cfg.sync_bn:
            model = nn.SyncBatchNorm.convert_sync_batchnorm(model)
        n_parameters = sum((p.numel() for p in model.parameters() if p.requires_grad))
        self.logger.info(f'Num params: {n_parameters}')
        model = create_ddp_model(model.cuda(), broadcast_buffers=False, find_unused_parameters=self.cfg.find_unused_parameters)
        return model

    def build_writer(self):
        writer = SummaryWriter(self.cfg.save_path) if comm.is_main_process() else None
        return writer

    def build_train_loader(self):
        train_data = build_dataset(self.cfg.data.train)
        if comm.get_world_size() > 1:
            train_sampler = torch.utils.data.distributed.DistributedSampler(train_data)
        else:
            train_sampler = None
        init_fn = partial(worker_init_fn, num_workers=self.cfg.num_worker_per_gpu, rank=comm.get_rank(), seed=self.cfg.seed) if self.cfg.seed is not None else None
        train_loader = torch.utils.data.DataLoader(train_data, batch_size=self.cfg.batch_size_per_gpu, shuffle=train_sampler is None, num_workers=self.cfg.num_worker_per_gpu, sampler=train_sampler, collate_fn=partial(point_collate_fn, max_batch_points=self.cfg.max_batch_points, mix_prob=self.cfg.mix_prob), pin_memory=True, worker_init_fn=init_fn, drop_last=True, persistent_workers=True)
        return train_loader

    def build_val_loader(self):
        val_loader = None
        if self.cfg.evaluate:
            val_data = build_dataset(self.cfg.data.val)
            if comm.get_world_size() > 1:
                val_sampler = torch.utils.data.distributed.DistributedSampler(val_data)
            else:
                val_sampler = None
            val_loader = torch.utils.data.DataLoader(val_data, batch_size=self.cfg.batch_size_val_per_gpu, shuffle=False, num_workers=self.cfg.num_worker_per_gpu, pin_memory=True, sampler=val_sampler, collate_fn=collate_fn)
        return val_loader

    def build_criteria(self):
        return build_criteria(self.cfg.criteria)

    def build_optimizer(self):
        return build_optimizer(self.cfg.optimizer, self.model, self.cfg.param_dicts)

    def build_scheduler(self):
        assert hasattr(self, 'optimizer')
        assert hasattr(self, 'train_loader')
        self.cfg.scheduler.total_steps = len(self.train_loader) * self.cfg.eval_epoch
        return build_scheduler(self.cfg.scheduler, self.optimizer)

    def build_scaler(self):
        scaler = torch.cuda.amp.GradScaler() if self.cfg.enable_amp else None
        return scaler

    def resume_or_load(self):
        if self.cfg.weight and os.path.isfile(self.cfg.weight):
            self.logger.info(f'Loading weight at: {self.cfg.weight}')
            checkpoint = torch.load(self.cfg.weight, map_location=lambda storage, loc: storage.cuda())
            load_state_info = self.model.load_state_dict(checkpoint['state_dict'], strict=False)
            self.logger.info(f'Missing keys: {load_state_info[0]}')
            if self.cfg.resume:
                self.logger.info(f'Resuming train at eval epoch: {checkpoint['epoch']}')
                self.start_epoch = checkpoint['epoch']
                self.best_metric_value = checkpoint['best_metric_value']
                self.optimizer.load_state_dict(checkpoint['optimizer'])
                self.scheduler.load_state_dict(checkpoint['scheduler'])
                if self.cfg.enable_amp:
                    self.scaler.load_state_dict(checkpoint['scaler'])
        else:
            self.logger.info(f'No weight found at: {self.cfg.weight}')

def run_step(self, i, input_dict):
    data_time = time.time() - self.iter_end_time
    for key in input_dict.keys():
        input_dict[key] = input_dict[key].cuda(non_blocking=True)
    with torch.cuda.amp.autocast(enabled=self.cfg.enable_amp):
        output = self.model(input_dict)
        loss = self.criteria(output, input_dict['label'])
    self.optimizer.zero_grad()
    if self.cfg.enable_amp:
        self.scaler.scale(loss).backward()
        self.scaler.step(self.optimizer)
        self.scaler.update()
    else:
        loss.backward()
        self.optimizer.step()
    self.scheduler.step()
    if self.cfg.empty_cache:
        torch.cuda.empty_cache()
    n = input_dict['coord'].size(0)
    if comm.get_world_size() > 1:
        loss *= n
        count = input_dict['label'].new_tensor([n], dtype=torch.long)
        (dist.all_reduce(loss), dist.all_reduce(count))
        n = count.item()
        loss /= n
    batch_time = time.time() - self.iter_end_time
    self.iter_end_time = time.time()
    self.storage.put_scalar('loss', loss.item(), n=n)
    self.storage.put_scalar('data_time', data_time)
    self.storage.put_scalar('batch_time', batch_time)
    current_iter = self.epoch * len(self.train_loader) + i + 1
    remain_iter = self.max_iter - current_iter
    remain_time = remain_iter * self.storage.history('batch_time').avg
    t_m, t_s = divmod(remain_time, 60)
    t_h, t_m = divmod(t_m, 60)
    remain_time = '{:02d}:{:02d}:{:02d}'.format(int(t_h), int(t_m), int(t_s))
    self.logger.info('Train: [{epoch}/{max_epoch}][{iter}/{max_iter}] Scan {batch_size} ({points_num}) Data {data_time_val:.3f} ({data_time_avg:.3f}) Batch {batch_time_val:.3f} ({batch_time_avg:.3f}) Remain {remain_time} Lr {lr:.4f} Loss {loss:.4f} '.format(epoch=self.epoch + 1, max_epoch=self.max_epoch, iter=i + 1, max_iter=len(self.train_loader), batch_size=len(input_dict['offset']), points_num=input_dict['offset'][-1], data_time_val=data_time, data_time_avg=self.storage.history('data_time').avg, batch_time_val=batch_time, batch_time_avg=self.storage.history('batch_time').avg, remain_time=remain_time, lr=self.optimizer.state_dict()['param_groups'][0]['lr'], loss=loss.item()))
    if i == 0:
        self.storage.history('data_time').reset()
        self.storage.history('batch_time').reset()
    if self.writer is not None:
        self.writer.add_scalar('lr', self.optimizer.state_dict()['param_groups'][0]['lr'], current_iter)
        self.writer.add_scalar('train_batch/loss', loss.item(), current_iter)

def after_epoch(self):
    loss_avg = self.storage.history('loss').avg
    self.logger.info('Train result: loss {:.4f}.'.format(loss_avg))
    current_epoch = self.epoch + 1
    if self.writer is not None:
        self.writer.add_scalar('train/loss', loss_avg, current_epoch)
    self.storage.reset_histories()
    if self.cfg.evaluate:
        self.eval()
    self.save_checkpoint()
    self.storage.reset_histories()

def eval(self):
    self.logger.info('>>>>>>>>>>>>>>>> Start Evaluation >>>>>>>>>>>>>>>>')
    self.model.eval()
    self.iter_end_time = time.time()
    for i, input_dict in enumerate(self.val_loader):
        data_time = time.time() - self.iter_end_time
        for key in input_dict.keys():
            input_dict[key] = input_dict[key].cuda(non_blocking=True)
        with torch.no_grad():
            output = self.model(input_dict)
        loss = self.criteria(output, input_dict['label'].long())
        n = input_dict['coord'].size(0)
        if comm.get_world_size() > 1:
            loss *= n
            count = input_dict['label'].new_tensor([n], dtype=torch.long)
            (dist.all_reduce(loss), dist.all_reduce(count))
            n = count.item()
            loss /= n
        pred = output.max(1)[1]
        label = input_dict['label']
        if 'origin_coord' in input_dict.keys():
            idx, _ = pointops.knn_query(1, input_dict['coord'].float(), input_dict['offset'].int(), input_dict['origin_coord'].float(), input_dict['origin_offset'].int())
            pred = pred[idx.flatten().long()]
            label = input_dict['origin_label']
        intersection, union, target = intersection_and_union_gpu(pred, label, self.cfg.data.num_classes, self.cfg.data.ignore_label)
        if comm.get_world_size() > 1:
            (dist.all_reduce(intersection), dist.all_reduce(union), dist.all_reduce(target))
        intersection, union, target = (intersection.cpu().numpy(), union.cpu().numpy(), target.cpu().numpy())
        batch_time = time.time() - self.iter_end_time
        self.iter_end_time = time.time()
        self.storage.put_scalar('intersection', intersection)
        self.storage.put_scalar('union', union)
        self.storage.put_scalar('target', target)
        self.storage.put_scalar('loss', loss.item(), n=n)
        self.storage.put_scalar('data_time', data_time)
        self.storage.put_scalar('batch_time', batch_time)
        self.logger.info('Test: [{iter}/{max_iter}] Data {data_time_val:.3f} ({data_time_avg:.3f}) Batch {batch_time_val:.3f} ({batch_time_avg:.3f}) Loss {loss:.4f} '.format(iter=i + 1, max_iter=len(self.val_loader), data_time_val=data_time, data_time_avg=self.storage.history('data_time').avg, batch_time_val=batch_time, batch_time_avg=self.storage.history('batch_time').avg, loss=loss.item()))
    loss_avg = self.storage.history('loss').avg
    intersection = self.storage.history('intersection').total
    union = self.storage.history('union').total
    target = self.storage.history('target').total
    iou_class = intersection / (union + 1e-10)
    acc_class = intersection / (target + 1e-10)
    m_iou = np.mean(iou_class)
    m_acc = np.mean(acc_class)
    all_acc = sum(intersection) / (sum(target) + 1e-10)
    self.storage.put_scalar('mIoU', m_iou)
    self.storage.put_scalar('mAcc', m_acc)
    self.storage.put_scalar('allAcc', all_acc)
    self.logger.info('Val result: mIoU/mAcc/allAcc {:.4f}/{:.4f}/{:.4f}.'.format(m_iou, m_acc, all_acc))
    for i in range(self.cfg.data.num_classes):
        self.logger.info('Class_{idx}-{name} Result: iou/accuracy {iou:.4f}/{accuracy:.4f}'.format(idx=i, name=self.cfg.data.names[i], iou=iou_class[i], accuracy=acc_class[i]))
    current_epoch = self.epoch + 1
    if self.writer is not None:
        self.writer.add_scalar('val/loss', loss_avg, current_epoch)
        self.writer.add_scalar('val/mIoU', m_iou, current_epoch)
        self.writer.add_scalar('val/mAcc', m_acc, current_epoch)
        self.writer.add_scalar('val/allAcc', all_acc, current_epoch)
    self.logger.info('<<<<<<<<<<<<<<<<< End Evaluation <<<<<<<<<<<<<<<<<')

@TEST.register_module()
class SegmentationTest(object):
    """SegmentationTest
    for large outdoor point cloud with need voxelize (s3dis)
    """

    def __call__(self, cfg, test_loader, model):
        test_dataset = test_loader.dataset
        logger = get_root_logger()
        logger.info('>>>>>>>>>>>>>>>> Start Evaluation >>>>>>>>>>>>>>>>')
        batch_time = AverageMeter()
        intersection_meter = AverageMeter()
        union_meter = AverageMeter()
        target_meter = AverageMeter()
        model.eval()
        save_path = os.path.join(cfg.save_path, 'result', 'test_epoch{}'.format(cfg.epochs))
        make_dirs(save_path)
        if 'ScanNet' in cfg.dataset_type:
            sub_path = os.path.join(save_path, 'submit')
            make_dirs(sub_path)
        pred_save, label_save = ([], [])
        for idx in range(len(test_dataset)):
            end = time.time()
            data_name = test_dataset.get_data_name(idx)
            pred_save_path = os.path.join(save_path, '{}_pred.npy'.format(data_name))
            label_save_path = os.path.join(save_path, '{}_label.npy'.format(data_name))
            if os.path.isfile(pred_save_path) and os.path.isfile(label_save_path):
                logger.info('{}/{}: {}, loaded pred and label.'.format(idx + 1, len(test_dataset), data_name))
                pred, label = (np.load(pred_save_path), np.load(label_save_path))
            else:
                data_dict_list, label = test_dataset[idx]
                pred = torch.zeros((label.size, cfg.data.num_classes)).cuda()
                batch_num = int(np.ceil(len(data_dict_list) / cfg.batch_size_test))
                for i in range(batch_num):
                    s_i, e_i = (i * cfg.batch_size_test, min((i + 1) * cfg.batch_size_test, len(data_dict_list)))
                    input_dict = collate_fn(data_dict_list[s_i:e_i])
                    for key in input_dict.keys():
                        input_dict[key] = input_dict[key].cuda(non_blocking=True)
                    idx_part = input_dict['index']
                    with torch.no_grad():
                        pred_part = model(input_dict)
                        pred_part = F.softmax(pred_part, -1)
                    if cfg.empty_cache:
                        torch.cuda.empty_cache()
                    bs = 0
                    for be in input_dict['offset']:
                        pred[idx_part[bs:be], :] += pred_part[bs:be]
                        bs = be
                    logger.info('Test: {} {}/{}, Batch: {batch_idx}/{batch_num}'.format(data_name, idx + 1, len(test_dataset), batch_idx=i, batch_num=batch_num))
                pred = pred.max(1)[1].data.cpu().numpy()
            intersection, union, target = intersection_and_union(pred, label, cfg.data.num_classes, cfg.data.ignore_label)
            intersection_meter.update(intersection)
            union_meter.update(union)
            target_meter.update(target)
            mask = union != 0
            iou_class = intersection / (union + 1e-10)
            iou = np.mean(iou_class[mask])
            acc = sum(intersection) / (sum(target) + 1e-10)
            m_iou = np.mean(intersection_meter.sum / (union_meter.sum + 1e-10))
            m_acc = np.mean(intersection_meter.sum / (target_meter.sum + 1e-10))
            batch_time.update(time.time() - end)
            logger.info('Test: {} [{}/{}]-{} Batch {batch_time.val:.3f} ({batch_time.avg:.3f}) Accuracy {acc:.4f} ({m_acc:.4f}) mIoU {iou:.4f} ({m_iou:.4f})'.format(data_name, idx + 1, len(test_dataset), label.size, batch_time=batch_time, acc=acc, m_acc=m_acc, iou=iou, m_iou=m_iou))
            pred_save.append(pred)
            label_save.append(label)
            np.save(pred_save_path, pred)
            np.save(label_save_path, label)
            if 'ScanNet' in cfg.dataset_type:
                np.savetxt(os.path.join(save_path, 'submit', '{}.txt'.format(data_name)), test_dataset.class2id[pred].reshape([-1, 1]), fmt='%d')
        with open(os.path.join(save_path, 'pred.pickle'), 'wb') as handle:
            pickle.dump({'pred': pred_save}, handle, protocol=pickle.HIGHEST_PROTOCOL)
        with open(os.path.join(save_path, 'label.pickle'), 'wb') as handle:
            pickle.dump({'label': label_save}, handle, protocol=pickle.HIGHEST_PROTOCOL)
        iou_class = intersection_meter.sum / (union_meter.sum + 1e-10)
        accuracy_class = intersection_meter.sum / (target_meter.sum + 1e-10)
        mIoU = np.mean(iou_class)
        mAcc = np.mean(accuracy_class)
        allAcc = sum(intersection_meter.sum) / (sum(target_meter.sum) + 1e-10)
        logger.info('Val result: mIoU/mAcc/allAcc {:.4f}/{:.4f}/{:.4f}'.format(mIoU, mAcc, allAcc))
        for i in range(cfg.data.num_classes):
            logger.info('Class_{idx} - {name} Result: iou/accuracy {iou:.4f}/{accuracy:.4f}'.format(idx=i, name=cfg.data.names[i], iou=iou_class[i], accuracy=accuracy_class[i]))
        logger.info('<<<<<<<<<<<<<<<<< End Evaluation <<<<<<<<<<<<<<<<<')

def __call__(self, cfg, test_loader, model):
    test_dataset = test_loader.dataset
    logger = get_root_logger()
    logger.info('>>>>>>>>>>>>>>>> Start Evaluation >>>>>>>>>>>>>>>>')
    batch_time = AverageMeter()
    intersection_meter = AverageMeter()
    union_meter = AverageMeter()
    target_meter = AverageMeter()
    model.eval()
    save_path = os.path.join(cfg.save_path, 'result', 'test_epoch{}'.format(cfg.epochs))
    make_dirs(save_path)
    if 'ScanNet' in cfg.dataset_type:
        sub_path = os.path.join(save_path, 'submit')
        make_dirs(sub_path)
    pred_save, label_save = ([], [])
    for idx in range(len(test_dataset)):
        end = time.time()
        data_name = test_dataset.get_data_name(idx)
        pred_save_path = os.path.join(save_path, '{}_pred.npy'.format(data_name))
        label_save_path = os.path.join(save_path, '{}_label.npy'.format(data_name))
        if os.path.isfile(pred_save_path) and os.path.isfile(label_save_path):
            logger.info('{}/{}: {}, loaded pred and label.'.format(idx + 1, len(test_dataset), data_name))
            pred, label = (np.load(pred_save_path), np.load(label_save_path))
        else:
            data_dict_list, label = test_dataset[idx]
            pred = torch.zeros((label.size, cfg.data.num_classes)).cuda()
            batch_num = int(np.ceil(len(data_dict_list) / cfg.batch_size_test))
            for i in range(batch_num):
                s_i, e_i = (i * cfg.batch_size_test, min((i + 1) * cfg.batch_size_test, len(data_dict_list)))
                input_dict = collate_fn(data_dict_list[s_i:e_i])
                for key in input_dict.keys():
                    input_dict[key] = input_dict[key].cuda(non_blocking=True)
                idx_part = input_dict['index']
                with torch.no_grad():
                    pred_part = model(input_dict)
                    pred_part = F.softmax(pred_part, -1)
                if cfg.empty_cache:
                    torch.cuda.empty_cache()
                bs = 0
                for be in input_dict['offset']:
                    pred[idx_part[bs:be], :] += pred_part[bs:be]
                    bs = be
                logger.info('Test: {} {}/{}, Batch: {batch_idx}/{batch_num}'.format(data_name, idx + 1, len(test_dataset), batch_idx=i, batch_num=batch_num))
            pred = pred.max(1)[1].data.cpu().numpy()
        intersection, union, target = intersection_and_union(pred, label, cfg.data.num_classes, cfg.data.ignore_label)
        intersection_meter.update(intersection)
        union_meter.update(union)
        target_meter.update(target)
        mask = union != 0
        iou_class = intersection / (union + 1e-10)
        iou = np.mean(iou_class[mask])
        acc = sum(intersection) / (sum(target) + 1e-10)
        m_iou = np.mean(intersection_meter.sum / (union_meter.sum + 1e-10))
        m_acc = np.mean(intersection_meter.sum / (target_meter.sum + 1e-10))
        batch_time.update(time.time() - end)
        logger.info('Test: {} [{}/{}]-{} Batch {batch_time.val:.3f} ({batch_time.avg:.3f}) Accuracy {acc:.4f} ({m_acc:.4f}) mIoU {iou:.4f} ({m_iou:.4f})'.format(data_name, idx + 1, len(test_dataset), label.size, batch_time=batch_time, acc=acc, m_acc=m_acc, iou=iou, m_iou=m_iou))
        pred_save.append(pred)
        label_save.append(label)
        np.save(pred_save_path, pred)
        np.save(label_save_path, label)
        if 'ScanNet' in cfg.dataset_type:
            np.savetxt(os.path.join(save_path, 'submit', '{}.txt'.format(data_name)), test_dataset.class2id[pred].reshape([-1, 1]), fmt='%d')
    with open(os.path.join(save_path, 'pred.pickle'), 'wb') as handle:
        pickle.dump({'pred': pred_save}, handle, protocol=pickle.HIGHEST_PROTOCOL)
    with open(os.path.join(save_path, 'label.pickle'), 'wb') as handle:
        pickle.dump({'label': label_save}, handle, protocol=pickle.HIGHEST_PROTOCOL)
    iou_class = intersection_meter.sum / (union_meter.sum + 1e-10)
    accuracy_class = intersection_meter.sum / (target_meter.sum + 1e-10)
    mIoU = np.mean(iou_class)
    mAcc = np.mean(accuracy_class)
    allAcc = sum(intersection_meter.sum) / (sum(target_meter.sum) + 1e-10)
    logger.info('Val result: mIoU/mAcc/allAcc {:.4f}/{:.4f}/{:.4f}'.format(mIoU, mAcc, allAcc))
    for i in range(cfg.data.num_classes):
        logger.info('Class_{idx} - {name} Result: iou/accuracy {iou:.4f}/{accuracy:.4f}'.format(idx=i, name=cfg.data.names[i], iou=iou_class[i], accuracy=accuracy_class[i]))
    logger.info('<<<<<<<<<<<<<<<<< End Evaluation <<<<<<<<<<<<<<<<<')

@TEST.register_module()
class ClassificationTest(object):
    """ClassificationTest
    for classification dataset (modelnet40), containing multi scales voting
    """

    def __init__(self, scales=(0.9, 0.95, 1, 1.05, 1.1), shuffle=False):
        self.scales = scales
        self.shuffle = shuffle

    def __call__(self, cfg, test_loader, model):
        logger = get_root_logger()
        logger.info('>>>>>>>>>>>>>>>> Start Evaluation >>>>>>>>>>>>>>>>')
        batch_time = AverageMeter()
        intersection_meter = AverageMeter()
        union_meter = AverageMeter()
        target_meter = AverageMeter()
        model.eval()
        for i, input_dict in enumerate(test_loader):
            for key in input_dict.keys():
                input_dict[key] = input_dict[key].cuda(non_blocking=True)
            coord = input_dict['coord']
            feat = input_dict['feat']
            target = input_dict['label']
            offset = input_dict['offset']
            end = time.time()
            output = torch.zeros([offset.shape[0], cfg.data.num_classes], dtype=torch.float32).cuda()
            for scale in self.scales:
                coord_temp, feat_temp = ([], [])
                for k in range(offset.shape[0]):
                    if k == 0:
                        s_k, e_k, cnt = (0, offset[0], offset[0])
                    else:
                        s_k, e_k, cnt = (offset[k - 1], offset[k], offset[k] - offset[k - 1])
                    coord_part, feat_part = (coord[s_k:e_k, :], feat[s_k:e_k, :])
                    coord_part *= scale
                    idx = np.arange(coord_part.shape[0])
                    if self.shuffle:
                        np.random.shuffle(idx)
                    (coord_temp.append(coord_part[idx]), feat_temp.append(feat_part[idx]))
                coord_temp, feat_temp = (torch.cat(coord_temp, 0), torch.cat(feat_temp, 0))
                with torch.no_grad():
                    output_part = model(dict(coord=coord_temp, feat=feat_temp, offset=offset))
                output += output_part
            output = output.max(1)[1]
            intersection, union, target = intersection_and_union_gpu(output, target, cfg.data.num_classes, cfg.data.ignore_label)
            intersection, union, target = (intersection.cpu().numpy(), union.cpu().numpy(), target.cpu().numpy())
            (intersection_meter.update(intersection), union_meter.update(union), target_meter.update(target))
            accuracy = sum(intersection_meter.val) / (sum(target_meter.val) + 1e-10)
            batch_time.update(time.time() - end)
            logger.info('Test: [{}/{}] Batch {batch_time.val:.3f} ({batch_time.avg:.3f}) Accuracy {accuracy:.4f} '.format(i + 1, len(test_loader), batch_time=batch_time, accuracy=accuracy))
        iou_class = intersection_meter.sum / (union_meter.sum + 1e-10)
        accuracy_class = intersection_meter.sum / (target_meter.sum + 1e-10)
        mIoU = np.mean(iou_class)
        mAcc = np.mean(accuracy_class)
        allAcc = sum(intersection_meter.sum) / (sum(target_meter.sum) + 1e-10)
        logger.info('Val result: mIoU/mAcc/allAcc {:.4f}/{:.4f}/{:.4f}.'.format(mIoU, mAcc, allAcc))
        for i in range(cfg.data.num_classes):
            logger.info('Class_{idx} - {name} Result: iou/accuracy {iou:.4f}/{accuracy:.4f}'.format(idx=i, name=cfg.data.names[i], iou=iou_class[i], accuracy=accuracy_class[i]))
        logger.info('<<<<<<<<<<<<<<<<< End Evaluation <<<<<<<<<<<<<<<<<')

def __call__(self, cfg, test_loader, model):
    logger = get_root_logger()
    logger.info('>>>>>>>>>>>>>>>> Start Evaluation >>>>>>>>>>>>>>>>')
    batch_time = AverageMeter()
    intersection_meter = AverageMeter()
    union_meter = AverageMeter()
    target_meter = AverageMeter()
    model.eval()
    for i, input_dict in enumerate(test_loader):
        for key in input_dict.keys():
            input_dict[key] = input_dict[key].cuda(non_blocking=True)
        coord = input_dict['coord']
        feat = input_dict['feat']
        target = input_dict['label']
        offset = input_dict['offset']
        end = time.time()
        output = torch.zeros([offset.shape[0], cfg.data.num_classes], dtype=torch.float32).cuda()
        for scale in self.scales:
            coord_temp, feat_temp = ([], [])
            for k in range(offset.shape[0]):
                if k == 0:
                    s_k, e_k, cnt = (0, offset[0], offset[0])
                else:
                    s_k, e_k, cnt = (offset[k - 1], offset[k], offset[k] - offset[k - 1])
                coord_part, feat_part = (coord[s_k:e_k, :], feat[s_k:e_k, :])
                coord_part *= scale
                idx = np.arange(coord_part.shape[0])
                if self.shuffle:
                    np.random.shuffle(idx)
                (coord_temp.append(coord_part[idx]), feat_temp.append(feat_part[idx]))
            coord_temp, feat_temp = (torch.cat(coord_temp, 0), torch.cat(feat_temp, 0))
            with torch.no_grad():
                output_part = model(dict(coord=coord_temp, feat=feat_temp, offset=offset))
            output += output_part
        output = output.max(1)[1]
        intersection, union, target = intersection_and_union_gpu(output, target, cfg.data.num_classes, cfg.data.ignore_label)
        intersection, union, target = (intersection.cpu().numpy(), union.cpu().numpy(), target.cpu().numpy())
        (intersection_meter.update(intersection), union_meter.update(union), target_meter.update(target))
        accuracy = sum(intersection_meter.val) / (sum(target_meter.val) + 1e-10)
        batch_time.update(time.time() - end)
        logger.info('Test: [{}/{}] Batch {batch_time.val:.3f} ({batch_time.avg:.3f}) Accuracy {accuracy:.4f} '.format(i + 1, len(test_loader), batch_time=batch_time, accuracy=accuracy))
    iou_class = intersection_meter.sum / (union_meter.sum + 1e-10)
    accuracy_class = intersection_meter.sum / (target_meter.sum + 1e-10)
    mIoU = np.mean(iou_class)
    mAcc = np.mean(accuracy_class)
    allAcc = sum(intersection_meter.sum) / (sum(target_meter.sum) + 1e-10)
    logger.info('Val result: mIoU/mAcc/allAcc {:.4f}/{:.4f}/{:.4f}.'.format(mIoU, mAcc, allAcc))
    for i in range(cfg.data.num_classes):
        logger.info('Class_{idx} - {name} Result: iou/accuracy {iou:.4f}/{accuracy:.4f}'.format(idx=i, name=cfg.data.names[i], iou=iou_class[i], accuracy=accuracy_class[i]))
    logger.info('<<<<<<<<<<<<<<<<< End Evaluation <<<<<<<<<<<<<<<<<')

@TEST.register_module()
class PartSegmentationTest(object):
    """PartSegmentationTest
    """

    def __call__(self, cfg, test_loader, model):
        test_dataset = test_loader.dataset
        logger = get_root_logger()
        logger.info('>>>>>>>>>>>>>>>> Start Evaluation >>>>>>>>>>>>>>>>')
        batch_time = AverageMeter()
        intersection_meter = AverageMeter()
        union_meter = AverageMeter()
        target_meter = AverageMeter()
        num_categories = len(test_loader.dataset.categories)
        iou_category, iou_count = (np.zeros(num_categories), np.zeros(num_categories))
        model.eval()
        save_path = os.path.join(cfg.save_path, 'result', 'test_epoch{}'.format(cfg.epochs))
        make_dirs(save_path)
        for idx in range(len(test_dataset)):
            end = time.time()
            data_name = test_dataset.get_data_name(idx)
            data_dict_list, label = test_dataset[idx]
            pred = torch.zeros((label.size, cfg.data.num_classes)).cuda()
            batch_num = int(np.ceil(len(data_dict_list) / cfg.batch_size_test))
            for i in range(batch_num):
                s_i, e_i = (i * cfg.batch_size_test, min((i + 1) * cfg.batch_size_test, len(data_dict_list)))
                input_dict = collate_fn(data_dict_list[s_i:e_i])
                for key in input_dict.keys():
                    input_dict[key] = input_dict[key].cuda(non_blocking=True)
                with torch.no_grad():
                    pred_part = model(input_dict)
                    pred_part = F.softmax(pred_part, -1)
                if cfg.empty_cache:
                    torch.cuda.empty_cache()
                pred_part = pred_part.reshape(-1, label.size, cfg.data.num_classes)
                pred = pred + pred_part.total(dim=0)
                logger.info('Test: {} {}/{}, Batch: {batch_idx}/{batch_num}'.format(data_name, idx + 1, len(test_dataset), batch_idx=i, batch_num=batch_num))
            pred = pred.max(1)[1].data.cpu().numpy()
            category_index = data_dict_list[0]['cls_token']
            category = test_loader.dataset.categories[category_index]
            parts_idx = test_loader.dataset.category2part[category]
            parts_iou = np.zeros(len(parts_idx))
            for j, part in enumerate(parts_idx):
                if np.sum(label == part) == 0 and np.sum(pred == part) == 0:
                    parts_iou[j] = 1.0
                else:
                    i = (label == part) & (pred == part)
                    u = (label == part) | (pred == part)
                    parts_iou[j] = np.sum(i) / (np.sum(u) + 1e-10)
            iou_category[category_index] += parts_iou.mean()
            iou_count[category_index] += 1
            batch_time.update(time.time() - end)
            logger.info('Test: {} [{}/{}] Batch {batch_time.val:.3f} ({batch_time.avg:.3f}) '.format(data_name, idx + 1, len(test_loader), batch_time=batch_time))
        ins_mIoU = iou_category.sum() / (iou_count.sum() + 1e-10)
        cat_mIoU = (iou_category / (iou_count + 1e-10)).mean()
        logger.info('Val result: ins.mIoU/cat.mIoU {:.4f}/{:.4f}.'.format(ins_mIoU, cat_mIoU))
        for i in range(num_categories):
            logger.info('Class_{idx}-{name} Result: iou_cat/num_sample {iou_cat:.4f}/{iou_count:.4f}'.format(idx=i, name=test_loader.dataset.categories[i], iou_cat=iou_category[i] / (iou_count[i] + 1e-10), iou_count=int(iou_count[i])))
        logger.info('<<<<<<<<<<<<<<<<< End Evaluation <<<<<<<<<<<<<<<<<')

def __call__(self, cfg, test_loader, model):
    test_dataset = test_loader.dataset
    logger = get_root_logger()
    logger.info('>>>>>>>>>>>>>>>> Start Evaluation >>>>>>>>>>>>>>>>')
    batch_time = AverageMeter()
    intersection_meter = AverageMeter()
    union_meter = AverageMeter()
    target_meter = AverageMeter()
    num_categories = len(test_loader.dataset.categories)
    iou_category, iou_count = (np.zeros(num_categories), np.zeros(num_categories))
    model.eval()
    save_path = os.path.join(cfg.save_path, 'result', 'test_epoch{}'.format(cfg.epochs))
    make_dirs(save_path)
    for idx in range(len(test_dataset)):
        end = time.time()
        data_name = test_dataset.get_data_name(idx)
        data_dict_list, label = test_dataset[idx]
        pred = torch.zeros((label.size, cfg.data.num_classes)).cuda()
        batch_num = int(np.ceil(len(data_dict_list) / cfg.batch_size_test))
        for i in range(batch_num):
            s_i, e_i = (i * cfg.batch_size_test, min((i + 1) * cfg.batch_size_test, len(data_dict_list)))
            input_dict = collate_fn(data_dict_list[s_i:e_i])
            for key in input_dict.keys():
                input_dict[key] = input_dict[key].cuda(non_blocking=True)
            with torch.no_grad():
                pred_part = model(input_dict)
                pred_part = F.softmax(pred_part, -1)
            if cfg.empty_cache:
                torch.cuda.empty_cache()
            pred_part = pred_part.reshape(-1, label.size, cfg.data.num_classes)
            pred = pred + pred_part.total(dim=0)
            logger.info('Test: {} {}/{}, Batch: {batch_idx}/{batch_num}'.format(data_name, idx + 1, len(test_dataset), batch_idx=i, batch_num=batch_num))
        pred = pred.max(1)[1].data.cpu().numpy()
        category_index = data_dict_list[0]['cls_token']
        category = test_loader.dataset.categories[category_index]
        parts_idx = test_loader.dataset.category2part[category]
        parts_iou = np.zeros(len(parts_idx))
        for j, part in enumerate(parts_idx):
            if np.sum(label == part) == 0 and np.sum(pred == part) == 0:
                parts_iou[j] = 1.0
            else:
                i = (label == part) & (pred == part)
                u = (label == part) | (pred == part)
                parts_iou[j] = np.sum(i) / (np.sum(u) + 1e-10)
        iou_category[category_index] += parts_iou.mean()
        iou_count[category_index] += 1
        batch_time.update(time.time() - end)
        logger.info('Test: {} [{}/{}] Batch {batch_time.val:.3f} ({batch_time.avg:.3f}) '.format(data_name, idx + 1, len(test_loader), batch_time=batch_time))
    ins_mIoU = iou_category.sum() / (iou_count.sum() + 1e-10)
    cat_mIoU = (iou_category / (iou_count + 1e-10)).mean()
    logger.info('Val result: ins.mIoU/cat.mIoU {:.4f}/{:.4f}.'.format(ins_mIoU, cat_mIoU))
    for i in range(num_categories):
        logger.info('Class_{idx}-{name} Result: iou_cat/num_sample {iou_cat:.4f}/{iou_count:.4f}'.format(idx=i, name=test_loader.dataset.categories[i], iou_cat=iou_category[i] / (iou_count[i] + 1e-10), iou_count=int(iou_count[i])))
    logger.info('<<<<<<<<<<<<<<<<< End Evaluation <<<<<<<<<<<<<<<<<')

@DATASETS.register_module()
class ScanNetPairDataset(Dataset):

    def __init__(self, data_root='data/scannet_pair', overlap_threshold=0.3, twin1_transform=None, twin2_transform=None, loop=1, **kwargs):
        super(ScanNetPairDataset, self).__init__()
        self.data_root = data_root
        self.overlap_threshold = overlap_threshold
        self.twin1_transform = Compose(twin1_transform)
        self.twin2_transform = Compose(twin2_transform)
        self.loop = loop
        self.data_list = self.get_data_list()
        logger = get_root_logger()
        logger.info('Totally {} x {} samples.'.format(len(self.data_list), self.loop))

    def get_data_list(self):
        data_list = []
        overlap_list = glob.glob(os.path.join(self.data_root, '*', 'pcd', 'overlap.txt'))
        for overlap_file in overlap_list:
            with open(overlap_file) as f:
                overlap = f.readlines()
            overlap = [pair.strip().split() for pair in overlap]
            data_list.extend([pair[:2] for pair in overlap if float(pair[2]) > self.overlap_threshold])
        return data_list

    def get_data(self, idx):
        pair = self.data_list[idx % len(self.data_list)]
        twin1_dict = torch.load(self.data_root + pair[0])
        twin2_dict = torch.load(self.data_root + pair[1])
        twin1_dict['origin_coord'] = twin1_dict['coord'].copy()
        twin2_dict['origin_coord'] = twin2_dict['coord'].copy()
        return (twin1_dict, twin2_dict)

    def get_data_name(self, idx):
        return os.path.basename(self.data_list[idx % len(self.data_list)]).split('.')[0]

    def prepare_train_data(self, idx):
        twin1_dict, twin2_dict = self.get_data(idx)
        twin1_dict = self.twin1_transform(twin1_dict)
        twin2_dict = self.twin2_transform(twin2_dict)
        data_dict = dict()
        for key, value in twin1_dict.items():
            data_dict['twin1_' + key] = value
        for key, value in twin2_dict.items():
            data_dict['twin2_' + key] = value
        return data_dict

    def prepare_test_data(self, idx):
        raise NotImplementedError

    def __getitem__(self, idx):
        return self.prepare_train_data(idx)

    def __len__(self):
        return len(self.data_list) * self.loop

def get_data(self, idx):
    pair = self.data_list[idx % len(self.data_list)]
    twin1_dict = torch.load(self.data_root + pair[0])
    twin2_dict = torch.load(self.data_root + pair[1])
    twin1_dict['origin_coord'] = twin1_dict['coord'].copy()
    twin2_dict['origin_coord'] = twin2_dict['coord'].copy()
    return (twin1_dict, twin2_dict)

def gaussian_kernel(dist2: np.array, a: float=1, c: float=5):
    return a * np.exp(-dist2 / (2 * c ** 2))

@DATASETS.register_module()
class SemanticKITTIDataset(Dataset):

    def __init__(self, split='train', data_root='data/semantic_kitti', learning_map=None, transform=None, test_mode=False, test_cfg=None, loop=1):
        super(SemanticKITTIDataset, self).__init__()
        self.data_root = data_root
        self.split = split
        self.learning_map = learning_map
        self.split2seq = dict(train=[0, 1, 2, 3, 4, 5, 6, 7, 9, 10], val=[8], test=[11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21])
        self.transform = Compose(transform)
        self.loop = loop if not test_mode else 1
        self.test_mode = test_mode
        self.test_cfg = test_cfg if test_mode else None
        if test_mode:
            self.test_voxelize = TRANSFORMS.build(self.test_cfg.voxelize)
            self.test_crop = TRANSFORMS.build(self.test_cfg.crop)
            self.post_transform = Compose(self.test_cfg.post_transform)
            self.aug_transform = [Compose(aug) for aug in self.test_cfg.aug_transform]
        if isinstance(self.split, str):
            seq_list = self.split2seq[split]
        elif isinstance(self.split, list):
            seq_list = []
            for split in self.split:
                seq_list += self.split2seq[split]
        else:
            raise NotImplementedError
        self.data_list = []
        for seq in seq_list:
            seq = str(seq).zfill(2)
            seq_folder = os.path.join(self.data_root, 'sequences', seq)
            seq_files = sorted(os.listdir(os.path.join(seq_folder, 'velodyne')))
            self.data_list += [os.path.join(seq_folder, 'velodyne', file) for file in seq_files]
        logger = get_root_logger()
        logger.info('Totally {} x {} samples in {} set.'.format(len(self.data_list), self.loop, split))

    def prepare_train_data(self, idx):
        data_idx = idx % len(self.data_list)
        with open(self.data_list[data_idx], 'rb') as b:
            scan = np.fromfile(b, dtype=np.float32).reshape(-1, 4)
        coord = scan[:, :3]
        strength = scan[:, -1].reshape([-1, 1])
        label_file = self.data_list[data_idx].replace('velodyne', 'labels').replace('.bin', '.label')
        if os.path.exists(label_file):
            with open(label_file, 'rb') as a:
                label = np.fromfile(a, dtype=np.int32).reshape(-1)
        else:
            label = np.zeros(coord.shape[0]).astype(np.int32)
        label = np.vectorize(self.learning_map.__getitem__)(label & 65535).astype(np.int64)
        data_dict = dict(coord=coord, strength=strength, label=label)
        data_dict = self.transform(data_dict)
        return data_dict

    def prepare_test_data(self, idx):
        raise NotImplementedError

    def get_data_name(self, idx):
        return self.data_list[self.data_list[idx % len(self.data_list)]]

    def __getitem__(self, idx):
        if self.test_mode:
            return self.prepare_test_data(idx)
        else:
            return self.prepare_train_data(idx)

    def __len__(self):
        return len(self.data_list) * self.loop

def prepare_train_data(self, idx):
    data_idx = idx % len(self.data_list)
    with open(self.data_list[data_idx], 'rb') as b:
        scan = np.fromfile(b, dtype=np.float32).reshape(-1, 4)
    coord = scan[:, :3]
    strength = scan[:, -1].reshape([-1, 1])
    label_file = self.data_list[data_idx].replace('velodyne', 'labels').replace('.bin', '.label')
    if os.path.exists(label_file):
        with open(label_file, 'rb') as a:
            label = np.fromfile(a, dtype=np.int32).reshape(-1)
    else:
        label = np.zeros(coord.shape[0]).astype(np.int32)
    label = np.vectorize(self.learning_map.__getitem__)(label & 65535).astype(np.int64)
    data_dict = dict(coord=coord, strength=strength, label=label)
    data_dict = self.transform(data_dict)
    return data_dict

@TRANSFORMS.register_module()
class Collect(object):

    def __init__(self, keys, offset_keys_dict=None, **kwargs):
        """
            e.g. Collect(keys=[coord], feat_keys=[coord, color])
        """
        if offset_keys_dict is None:
            offset_keys_dict = dict(offset='coord')
        self.keys = keys
        self.offset_keys = offset_keys_dict
        self.kwargs = kwargs

    def __call__(self, data_dict):
        data = dict()
        if isinstance(self.keys, str):
            self.keys = [self.keys]
        for key in self.keys:
            data[key] = data_dict[key]
        for key, value in self.offset_keys.items():
            data[key] = torch.tensor([data_dict[value].shape[0]])
        for name, keys in self.kwargs.items():
            name = name.replace('_keys', '')
            assert isinstance(keys, Sequence)
            data[name] = torch.cat([data_dict[key].float() for key in keys], dim=1)
        return data

def __init__(self, keys, offset_keys_dict=None, **kwargs):
    """
            e.g. Collect(keys=[coord], feat_keys=[coord, color])
        """
    if offset_keys_dict is None:
        offset_keys_dict = dict(offset='coord')
    self.keys = keys
    self.offset_keys = offset_keys_dict
    self.kwargs = kwargs

@TRANSFORMS.register_module()
class Copy(object):

    def __init__(self, keys_dict=None):
        if keys_dict is None:
            keys_dict = dict(coord='origin_coord', label='origin_label')
        self.keys_dict = keys_dict

    def __call__(self, data_dict):
        for key, value in self.keys_dict.items():
            if isinstance(data_dict[key], np.ndarray):
                data_dict[value] = data_dict[key].copy()
            elif isinstance(data_dict[key], torch.Tensor):
                data_dict[value] = data_dict[key].clone().detach()
            else:
                data_dict[value] = copy.deepcopy(data_dict[key])
        return data_dict

def __init__(self, keys_dict=None):
    if keys_dict is None:
        keys_dict = dict(coord='origin_coord', label='origin_label')
    self.keys_dict = keys_dict

def __call__(self, data_dict):
    for key, value in self.keys_dict.items():
        if isinstance(data_dict[key], np.ndarray):
            data_dict[value] = data_dict[key].copy()
        elif isinstance(data_dict[key], torch.Tensor):
            data_dict[value] = data_dict[key].clone().detach()
        else:
            data_dict[value] = copy.deepcopy(data_dict[key])
    return data_dict

@TRANSFORMS.register_module()
class NormalizeColor(object):

    def __call__(self, data_dict):
        if 'color' in data_dict.keys():
            data_dict['color'] = data_dict['color'] / 127.5 - 1
        return data_dict

def __call__(self, data_dict):
    if 'color' in data_dict.keys():
        data_dict['color'] = data_dict['color'] / 127.5 - 1
    return data_dict

@TRANSFORMS.register_module()
class PositiveShift(object):

    def __call__(self, data_dict):
        if 'coord' in data_dict.keys():
            coord_min = np.min(data_dict['coord'], 0)
            data_dict['coord'] -= coord_min
        return data_dict

def __call__(self, data_dict):
    if 'coord' in data_dict.keys():
        coord_min = np.min(data_dict['coord'], 0)
        data_dict['coord'] -= coord_min
    return data_dict

@TRANSFORMS.register_module()
class CenterShift(object):

    def __init__(self, apply_z=True):
        self.apply_z = apply_z

    def __call__(self, data_dict):
        if 'coord' in data_dict.keys():
            x_min, y_min, z_min = data_dict['coord'].min(axis=0)
            x_max, y_max, _ = data_dict['coord'].max(axis=0)
            if self.apply_z:
                shift = [(x_min + x_max) / 2, (y_min + y_max) / 2, z_min]
            else:
                shift = [(x_min + x_max) / 2, (y_min + y_max) / 2, 0]
            data_dict['coord'] -= shift
        return data_dict

def __call__(self, data_dict):
    if 'coord' in data_dict.keys():
        x_min, y_min, z_min = data_dict['coord'].min(axis=0)
        x_max, y_max, _ = data_dict['coord'].max(axis=0)
        if self.apply_z:
            shift = [(x_min + x_max) / 2, (y_min + y_max) / 2, z_min]
        else:
            shift = [(x_min + x_max) / 2, (y_min + y_max) / 2, 0]
        data_dict['coord'] -= shift
    return data_dict

@TRANSFORMS.register_module()
class RandomShift(object):

    def __init__(self, shift=((-0.2, 0.2), (-0.2, 0.2), (0, 0))):
        self.shift = shift

    def __call__(self, data_dict):
        if 'coord' in data_dict.keys():
            shift_x = np.random.uniform(self.shift[0][0], self.shift[0][1])
            shift_y = np.random.uniform(self.shift[1][0], self.shift[1][1])
            shift_z = np.random.uniform(self.shift[2][0], self.shift[2][1])
            data_dict['coord'] += [shift_x, shift_y, shift_z]
        return data_dict

def __call__(self, data_dict):
    if 'coord' in data_dict.keys():
        shift_x = np.random.uniform(self.shift[0][0], self.shift[0][1])
        shift_y = np.random.uniform(self.shift[1][0], self.shift[1][1])
        shift_z = np.random.uniform(self.shift[2][0], self.shift[2][1])
        data_dict['coord'] += [shift_x, shift_y, shift_z]
    return data_dict

@TRANSFORMS.register_module()
class PointClip(object):

    def __init__(self, point_cloud_range=(-80, -80, -3, 80, 80, 1)):
        self.point_cloud_range = point_cloud_range

    def __call__(self, data_dict):
        if 'coord' in data_dict.keys():
            data_dict['coord'] = np.clip(data_dict['coord'], a_min=self.point_cloud_range[:3], a_max=self.point_cloud_range[3:])
        return data_dict

def __call__(self, data_dict):
    if 'coord' in data_dict.keys():
        data_dict['coord'] = np.clip(data_dict['coord'], a_min=self.point_cloud_range[:3], a_max=self.point_cloud_range[3:])
    return data_dict

@TRANSFORMS.register_module()
class RandomDropout(object):

    def __init__(self, dropout_ratio=0.2, dropout_application_ratio=0.5):
        """
            upright_axis: axis index among x,y,z, i.e. 2 for z
        """
        self.dropout_ratio = dropout_ratio
        self.dropout_application_ratio = dropout_application_ratio

    def __call__(self, data_dict):
        if random.random() < self.dropout_application_ratio:
            n = len(data_dict['coord'])
            idx = np.random.choice(n, int(n * (1 - self.dropout_ratio)), replace=False)
            if 'coord' in data_dict.keys():
                data_dict['coord'] = data_dict['coord'][idx]
            if 'color' in data_dict.keys():
                data_dict['color'] = data_dict['color'][idx]
            if 'normal' in data_dict.keys():
                data_dict['normal'] = data_dict['normal'][idx]
            if 'strength' in data_dict.keys():
                data_dict['strength'] = data_dict['strength'][idx]
            if 'instance' in data_dict.keys():
                data_dict['instance'] = data_dict['instance'][idx]
            if 'label' in data_dict.keys():
                data_dict['label'] = data_dict['label'][idx] if len(data_dict['label']) != 1 else data_dict['label']
        return data_dict

def __call__(self, data_dict):
    if random.random() < self.dropout_application_ratio:
        n = len(data_dict['coord'])
        idx = np.random.choice(n, int(n * (1 - self.dropout_ratio)), replace=False)
        if 'coord' in data_dict.keys():
            data_dict['coord'] = data_dict['coord'][idx]
        if 'color' in data_dict.keys():
            data_dict['color'] = data_dict['color'][idx]
        if 'normal' in data_dict.keys():
            data_dict['normal'] = data_dict['normal'][idx]
        if 'strength' in data_dict.keys():
            data_dict['strength'] = data_dict['strength'][idx]
        if 'instance' in data_dict.keys():
            data_dict['instance'] = data_dict['instance'][idx]
        if 'label' in data_dict.keys():
            data_dict['label'] = data_dict['label'][idx] if len(data_dict['label']) != 1 else data_dict['label']
    return data_dict

@TRANSFORMS.register_module()
class RandomRotate(object):

    def __init__(self, angle=None, center=None, axis='z', always_apply=False, p=0.5):
        self.angle = [-1, 1] if angle is None else angle
        self.axis = axis
        self.always_apply = always_apply
        self.p = p if not self.always_apply else 1
        self.center = center

    def __call__(self, data_dict):
        if random.random() > self.p:
            return data_dict
        angle = np.random.uniform(self.angle[0], self.angle[1]) * np.pi
        rot_cos, rot_sin = (np.cos(angle), np.sin(angle))
        if self.axis == 'x':
            rot_t = np.array([[1, 0, 0], [0, rot_cos, -rot_sin], [0, rot_sin, rot_cos]])
        elif self.axis == 'y':
            rot_t = np.array([[rot_cos, 0, rot_sin], [0, 1, 0], [-rot_sin, 0, rot_cos]])
        elif self.axis == 'z':
            rot_t = np.array([[rot_cos, -rot_sin, 0], [rot_sin, rot_cos, 0], [0, 0, 1]])
        else:
            raise NotImplementedError
        if 'coord' in data_dict.keys():
            if self.center is None:
                x_min, y_min, z_min = data_dict['coord'].min(axis=0)
                x_max, y_max, z_max = data_dict['coord'].max(axis=0)
                center = [(x_min + x_max) / 2, (y_min + y_max) / 2, (z_min + z_max) / 2]
            else:
                center = self.center
            data_dict['coord'] -= center
            data_dict['coord'] = np.dot(data_dict['coord'], np.transpose(rot_t))
            data_dict['coord'] += center
        if 'normal' in data_dict.keys():
            data_dict['normal'] = np.dot(data_dict['normal'], np.transpose(rot_t))
        return data_dict

def __call__(self, data_dict):
    if random.random() > self.p:
        return data_dict
    angle = np.random.uniform(self.angle[0], self.angle[1]) * np.pi
    rot_cos, rot_sin = (np.cos(angle), np.sin(angle))
    if self.axis == 'x':
        rot_t = np.array([[1, 0, 0], [0, rot_cos, -rot_sin], [0, rot_sin, rot_cos]])
    elif self.axis == 'y':
        rot_t = np.array([[rot_cos, 0, rot_sin], [0, 1, 0], [-rot_sin, 0, rot_cos]])
    elif self.axis == 'z':
        rot_t = np.array([[rot_cos, -rot_sin, 0], [rot_sin, rot_cos, 0], [0, 0, 1]])
    else:
        raise NotImplementedError
    if 'coord' in data_dict.keys():
        if self.center is None:
            x_min, y_min, z_min = data_dict['coord'].min(axis=0)
            x_max, y_max, z_max = data_dict['coord'].max(axis=0)
            center = [(x_min + x_max) / 2, (y_min + y_max) / 2, (z_min + z_max) / 2]
        else:
            center = self.center
        data_dict['coord'] -= center
        data_dict['coord'] = np.dot(data_dict['coord'], np.transpose(rot_t))
        data_dict['coord'] += center
    if 'normal' in data_dict.keys():
        data_dict['normal'] = np.dot(data_dict['normal'], np.transpose(rot_t))
    return data_dict

@TRANSFORMS.register_module()
class RandomRotateTargetAngle(object):

    def __init__(self, angle=(1 / 2, 1, 3 / 2), center=None, axis='z', always_apply=False, p=0.75):
        self.angle = angle
        self.axis = axis
        self.always_apply = always_apply
        self.p = p if not self.always_apply else 1
        self.center = center

    def __call__(self, data_dict):
        if random.random() > self.p:
            return data_dict
        angle = np.random.choice(self.angle) * np.pi
        rot_cos, rot_sin = (np.cos(angle), np.sin(angle))
        if self.axis == 'x':
            rot_t = np.array([[1, 0, 0], [0, rot_cos, -rot_sin], [0, rot_sin, rot_cos]])
        elif self.axis == 'y':
            rot_t = np.array([[rot_cos, 0, rot_sin], [0, 1, 0], [-rot_sin, 0, rot_cos]])
        elif self.axis == 'z':
            rot_t = np.array([[rot_cos, -rot_sin, 0], [rot_sin, rot_cos, 0], [0, 0, 1]])
        else:
            raise NotImplementedError
        if 'coord' in data_dict.keys():
            if self.center is None:
                x_min, y_min, z_min = data_dict['coord'].min(axis=0)
                x_max, y_max, z_max = data_dict['coord'].max(axis=0)
                center = [(x_min + x_max) / 2, (y_min + y_max) / 2, (z_min + z_max) / 2]
            else:
                center = self.center
            data_dict['coord'] -= center
            data_dict['coord'] = np.dot(data_dict['coord'], np.transpose(rot_t))
            data_dict['coord'] += center
        if 'normal' in data_dict.keys():
            data_dict['normal'] = np.dot(data_dict['normal'], np.transpose(rot_t))
        return data_dict

def __call__(self, data_dict):
    if random.random() > self.p:
        return data_dict
    angle = np.random.choice(self.angle) * np.pi
    rot_cos, rot_sin = (np.cos(angle), np.sin(angle))
    if self.axis == 'x':
        rot_t = np.array([[1, 0, 0], [0, rot_cos, -rot_sin], [0, rot_sin, rot_cos]])
    elif self.axis == 'y':
        rot_t = np.array([[rot_cos, 0, rot_sin], [0, 1, 0], [-rot_sin, 0, rot_cos]])
    elif self.axis == 'z':
        rot_t = np.array([[rot_cos, -rot_sin, 0], [rot_sin, rot_cos, 0], [0, 0, 1]])
    else:
        raise NotImplementedError
    if 'coord' in data_dict.keys():
        if self.center is None:
            x_min, y_min, z_min = data_dict['coord'].min(axis=0)
            x_max, y_max, z_max = data_dict['coord'].max(axis=0)
            center = [(x_min + x_max) / 2, (y_min + y_max) / 2, (z_min + z_max) / 2]
        else:
            center = self.center
        data_dict['coord'] -= center
        data_dict['coord'] = np.dot(data_dict['coord'], np.transpose(rot_t))
        data_dict['coord'] += center
    if 'normal' in data_dict.keys():
        data_dict['normal'] = np.dot(data_dict['normal'], np.transpose(rot_t))
    return data_dict

@TRANSFORMS.register_module()
class RandomScale(object):

    def __init__(self, scale=None, anisotropic=False):
        self.scale = scale if scale is not None else [0.95, 1.05]
        self.anisotropic = anisotropic

    def __call__(self, data_dict):
        if 'coord' in data_dict.keys():
            scale = np.random.uniform(self.scale[0], self.scale[1], 3 if self.anisotropic else 1)
            data_dict['coord'] *= scale
        return data_dict

def __call__(self, data_dict):
    if 'coord' in data_dict.keys():
        scale = np.random.uniform(self.scale[0], self.scale[1], 3 if self.anisotropic else 1)
        data_dict['coord'] *= scale
    return data_dict

@TRANSFORMS.register_module()
class RandomFlip(object):

    def __init__(self, p=0.5):
        self.p = p

    def __call__(self, data_dict):
        if np.random.rand() < self.p:
            if 'coord' in data_dict.keys():
                data_dict['coord'][:, 0] = -data_dict['coord'][:, 0]
            if 'normal' in data_dict.keys():
                data_dict['normal'][:, 0] = -data_dict['normal'][:, 0]
        if np.random.rand() < self.p:
            if 'coord' in data_dict.keys():
                data_dict['coord'][:, 1] = -data_dict['coord'][:, 1]
            if 'normal' in data_dict.keys():
                data_dict['normal'][:, 1] = -data_dict['normal'][:, 1]
        return data_dict

def __call__(self, data_dict):
    if np.random.rand() < self.p:
        if 'coord' in data_dict.keys():
            data_dict['coord'][:, 0] = -data_dict['coord'][:, 0]
        if 'normal' in data_dict.keys():
            data_dict['normal'][:, 0] = -data_dict['normal'][:, 0]
    if np.random.rand() < self.p:
        if 'coord' in data_dict.keys():
            data_dict['coord'][:, 1] = -data_dict['coord'][:, 1]
        if 'normal' in data_dict.keys():
            data_dict['normal'][:, 1] = -data_dict['normal'][:, 1]
    return data_dict

@TRANSFORMS.register_module()
class RandomJitter(object):

    def __init__(self, sigma=0.01, clip=0.05):
        assert clip > 0
        self.sigma = sigma
        self.clip = clip

    def __call__(self, data_dict):
        if 'coord' in data_dict.keys():
            jitter = np.clip(self.sigma * np.random.randn(data_dict['coord'].shape[0], 3), -self.clip, self.clip)
            data_dict['coord'] += jitter
        return data_dict

def __call__(self, data_dict):
    if 'coord' in data_dict.keys():
        jitter = np.clip(self.sigma * np.random.randn(data_dict['coord'].shape[0], 3), -self.clip, self.clip)
        data_dict['coord'] += jitter
    return data_dict

@TRANSFORMS.register_module()
class ClipGaussianJitter(object):

    def __init__(self, scalar=0.02, store_jitter=False):
        self.scalar = scalar
        self.mean = np.mean(3)
        self.cov = np.identity(3)
        self.quantile = 1.96
        self.store_jitter = store_jitter

    def __call__(self, data_dict):
        if 'coord' in data_dict.keys():
            jitter = np.random.multivariate_normal(self.mean, self.cov, data_dict['coord'].shape[0])
            jitter = self.scalar * np.clip(jitter / 1.96, -1, 1)
            data_dict['coord'] += jitter
            if self.store_jitter:
                data_dict['jitter'] = jitter
        return data_dict

def __init__(self, scalar=0.02, store_jitter=False):
    self.scalar = scalar
    self.mean = np.mean(3)
    self.cov = np.identity(3)
    self.quantile = 1.96
    self.store_jitter = store_jitter

def __call__(self, data_dict):
    if 'coord' in data_dict.keys():
        jitter = np.random.multivariate_normal(self.mean, self.cov, data_dict['coord'].shape[0])
        jitter = self.scalar * np.clip(jitter / 1.96, -1, 1)
        data_dict['coord'] += jitter
        if self.store_jitter:
            data_dict['jitter'] = jitter
    return data_dict

@TRANSFORMS.register_module()
class ChromaticAutoContrast(object):

    def __init__(self, p=0.2, blend_factor=None):
        self.p = p
        self.blend_factor = blend_factor

    def __call__(self, data_dict):
        if 'color' in data_dict.keys() and np.random.rand() < self.p:
            lo = np.min(data_dict['color'], 0, keepdims=True)
            hi = np.max(data_dict['color'], 0, keepdims=True)
            scale = 255 / (hi - lo)
            contrast_feat = (data_dict['color'][:, :3] - lo) * scale
            blend_factor = np.random.rand() if self.blend_factor is None else self.blend_factor
            data_dict['color'][:, :3] = (1 - blend_factor) * data_dict['color'][:, :3] + blend_factor * contrast_feat
        return data_dict

def __call__(self, data_dict):
    if 'color' in data_dict.keys() and np.random.rand() < self.p:
        lo = np.min(data_dict['color'], 0, keepdims=True)
        hi = np.max(data_dict['color'], 0, keepdims=True)
        scale = 255 / (hi - lo)
        contrast_feat = (data_dict['color'][:, :3] - lo) * scale
        blend_factor = np.random.rand() if self.blend_factor is None else self.blend_factor
        data_dict['color'][:, :3] = (1 - blend_factor) * data_dict['color'][:, :3] + blend_factor * contrast_feat
    return data_dict

@TRANSFORMS.register_module()
class ChromaticTranslation(object):

    def __init__(self, p=0.95, ratio=0.05):
        self.p = p
        self.ratio = ratio

    def __call__(self, data_dict):
        if 'color' in data_dict.keys() and np.random.rand() < self.p:
            tr = (np.random.rand(1, 3) - 0.5) * 255 * 2 * self.ratio
            data_dict['color'][:, :3] = np.clip(tr + data_dict['color'][:, :3], 0, 255)
        return data_dict

def __call__(self, data_dict):
    if 'color' in data_dict.keys() and np.random.rand() < self.p:
        tr = (np.random.rand(1, 3) - 0.5) * 255 * 2 * self.ratio
        data_dict['color'][:, :3] = np.clip(tr + data_dict['color'][:, :3], 0, 255)
    return data_dict

@TRANSFORMS.register_module()
class ChromaticJitter(object):

    def __init__(self, p=0.95, std=0.005):
        self.p = p
        self.std = std

    def __call__(self, data_dict):
        if 'color' in data_dict.keys() and np.random.rand() < self.p:
            noise = np.random.randn(data_dict['color'].shape[0], 3)
            noise *= self.std * 255
            data_dict['color'][:, :3] = np.clip(noise + data_dict['color'][:, :3], 0, 255)
        return data_dict

def __call__(self, data_dict):
    if 'color' in data_dict.keys() and np.random.rand() < self.p:
        noise = np.random.randn(data_dict['color'].shape[0], 3)
        noise *= self.std * 255
        data_dict['color'][:, :3] = np.clip(noise + data_dict['color'][:, :3], 0, 255)
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
def blend(color1, color2, ratio):
    ratio = float(ratio)
    bound = 255.0
    return (ratio * color1 + (1.0 - ratio) * color2).clip(0, bound).astype(color1.dtype)

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

@TRANSFORMS.register_module()
class HueSaturationTranslation(object):

    @staticmethod
    def rgb_to_hsv(rgb):
        rgb = rgb.astype('float')
        hsv = np.zeros_like(rgb)
        hsv[..., 3:] = rgb[..., 3:]
        r, g, b = (rgb[..., 0], rgb[..., 1], rgb[..., 2])
        maxc = np.max(rgb[..., :3], axis=-1)
        minc = np.min(rgb[..., :3], axis=-1)
        hsv[..., 2] = maxc
        mask = maxc != minc
        hsv[mask, 1] = (maxc - minc)[mask] / maxc[mask]
        rc = np.zeros_like(r)
        gc = np.zeros_like(g)
        bc = np.zeros_like(b)
        rc[mask] = (maxc - r)[mask] / (maxc - minc)[mask]
        gc[mask] = (maxc - g)[mask] / (maxc - minc)[mask]
        bc[mask] = (maxc - b)[mask] / (maxc - minc)[mask]
        hsv[..., 0] = np.select([r == maxc, g == maxc], [bc - gc, 2.0 + rc - bc], default=4.0 + gc - rc)
        hsv[..., 0] = hsv[..., 0] / 6.0 % 1.0
        return hsv

    @staticmethod
    def hsv_to_rgb(hsv):
        rgb = np.empty_like(hsv)
        rgb[..., 3:] = hsv[..., 3:]
        h, s, v = (hsv[..., 0], hsv[..., 1], hsv[..., 2])
        i = (h * 6.0).astype('uint8')
        f = h * 6.0 - i
        p = v * (1.0 - s)
        q = v * (1.0 - s * f)
        t = v * (1.0 - s * (1.0 - f))
        i = i % 6
        conditions = [s == 0.0, i == 1, i == 2, i == 3, i == 4, i == 5]
        rgb[..., 0] = np.select(conditions, [v, q, p, p, t, v], default=v)
        rgb[..., 1] = np.select(conditions, [v, v, v, q, p, p], default=t)
        rgb[..., 2] = np.select(conditions, [v, p, t, v, v, q], default=p)
        return rgb.astype('uint8')

    def __init__(self, hue_max=0.5, saturation_max=0.2):
        self.hue_max = hue_max
        self.saturation_max = saturation_max

    def __call__(self, data_dict):
        if 'color' in data_dict.keys():
            hsv = HueSaturationTranslation.rgb_to_hsv(data_dict['color'][:, :3])
            hue_val = (np.random.rand() - 0.5) * 2 * self.hue_max
            sat_ratio = 1 + (np.random.rand() - 0.5) * 2 * self.saturation_max
            hsv[..., 0] = np.remainder(hue_val + hsv[..., 0] + 1, 1)
            hsv[..., 1] = np.clip(sat_ratio * hsv[..., 1], 0, 1)
            data_dict['color'][:, :3] = np.clip(HueSaturationTranslation.hsv_to_rgb(hsv), 0, 255)
        return data_dict

def __call__(self, data_dict):
    if 'color' in data_dict.keys():
        hsv = HueSaturationTranslation.rgb_to_hsv(data_dict['color'][:, :3])
        hue_val = (np.random.rand() - 0.5) * 2 * self.hue_max
        sat_ratio = 1 + (np.random.rand() - 0.5) * 2 * self.saturation_max
        hsv[..., 0] = np.remainder(hue_val + hsv[..., 0] + 1, 1)
        hsv[..., 1] = np.clip(sat_ratio * hsv[..., 1], 0, 1)
        data_dict['color'][:, :3] = np.clip(HueSaturationTranslation.hsv_to_rgb(hsv), 0, 255)
    return data_dict

@TRANSFORMS.register_module()
class RandomColorDrop(object):

    def __init__(self, p=0.8, color_augment=0.0):
        self.p = p
        self.color_augment = color_augment

    def __call__(self, data_dict):
        if 'color' in data_dict.keys() and np.random.rand() > self.p:
            data_dict['color'] *= self.color_augment
        return data_dict

    def __repr__(self):
        return 'RandomColorDrop(color_augment: {}, p: {})'.format(self.color_augment, self.p)

def __call__(self, data_dict):
    if 'color' in data_dict.keys() and np.random.rand() > self.p:
        data_dict['color'] *= self.color_augment
    return data_dict

@TRANSFORMS.register_module()
class ElasticDistortion(object):

    def __init__(self, distortion_params=None):
        self.distortion_params = [[0.2, 0.4], [0.8, 1.6]] if distortion_params is None else distortion_params

    @staticmethod
    def elastic_distortion(coords, granularity, magnitude):
        """
        Apply elastic distortion on sparse coordinate space.
        pointcloud: numpy array of (number of points, at least 3 spatial dims)
        granularity: size of the noise grid (in same scale[m/cm] as the voxel grid)
        magnitude: noise multiplier
        """
        blurx = np.ones((3, 1, 1, 1)).astype('float32') / 3
        blury = np.ones((1, 3, 1, 1)).astype('float32') / 3
        blurz = np.ones((1, 1, 3, 1)).astype('float32') / 3
        coords_min = coords.min(0)
        noise_dim = ((coords - coords_min).max(0) // granularity).astype(int) + 3
        noise = np.random.randn(*noise_dim, 3).astype(np.float32)
        for _ in range(2):
            noise = scipy.ndimage.filters.convolve(noise, blurx, mode='constant', cval=0)
            noise = scipy.ndimage.filters.convolve(noise, blury, mode='constant', cval=0)
            noise = scipy.ndimage.filters.convolve(noise, blurz, mode='constant', cval=0)
        ax = [np.linspace(d_min, d_max, d) for d_min, d_max, d in zip(coords_min - granularity, coords_min + granularity * (noise_dim - 2), noise_dim)]
        interp = scipy.interpolate.RegularGridInterpolator(ax, noise, bounds_error=False, fill_value=0)
        coords += interp(coords) * magnitude
        return coords

    def __call__(self, data_dict):
        if 'coord' in data_dict.keys() and self.distortion_params is not None:
            if random.random() < 0.95:
                for granularity, magnitude in self.distortion_params:
                    data_dict['coord'] = self.elastic_distortion(data_dict['coord'], granularity, magnitude)
        return data_dict

@staticmethod
def elastic_distortion(coords, granularity, magnitude):
    """
        Apply elastic distortion on sparse coordinate space.
        pointcloud: numpy array of (number of points, at least 3 spatial dims)
        granularity: size of the noise grid (in same scale[m/cm] as the voxel grid)
        magnitude: noise multiplier
        """
    blurx = np.ones((3, 1, 1, 1)).astype('float32') / 3
    blury = np.ones((1, 3, 1, 1)).astype('float32') / 3
    blurz = np.ones((1, 1, 3, 1)).astype('float32') / 3
    coords_min = coords.min(0)
    noise_dim = ((coords - coords_min).max(0) // granularity).astype(int) + 3
    noise = np.random.randn(*noise_dim, 3).astype(np.float32)
    for _ in range(2):
        noise = scipy.ndimage.filters.convolve(noise, blurx, mode='constant', cval=0)
        noise = scipy.ndimage.filters.convolve(noise, blury, mode='constant', cval=0)
        noise = scipy.ndimage.filters.convolve(noise, blurz, mode='constant', cval=0)
    ax = [np.linspace(d_min, d_max, d) for d_min, d_max, d in zip(coords_min - granularity, coords_min + granularity * (noise_dim - 2), noise_dim)]
    interp = scipy.interpolate.RegularGridInterpolator(ax, noise, bounds_error=False, fill_value=0)
    coords += interp(coords) * magnitude
    return coords

def __call__(self, data_dict):
    if 'coord' in data_dict.keys() and self.distortion_params is not None:
        if random.random() < 0.95:
            for granularity, magnitude in self.distortion_params:
                data_dict['coord'] = self.elastic_distortion(data_dict['coord'], granularity, magnitude)
    return data_dict

@TRANSFORMS.register_module()
class Voxelize(object):

    def __init__(self, voxel_size=0.05, hash_type='fnv', mode='train', keys=('coord', 'normal', 'color', 'label'), return_inverse=False, return_discrete_coord=False, return_min_coord=False):
        self.voxel_size = voxel_size
        self.hash = self.fnv_hash_vec if hash_type == 'fnv' else self.ravel_hash_vec
        assert mode in ['train', 'test']
        self.mode = mode
        self.keys = keys
        self.return_inverse = return_inverse
        self.return_discrete_coord = return_discrete_coord
        self.return_min_coord = return_min_coord

    def __call__(self, data_dict):
        assert 'coord' in data_dict.keys()
        discrete_coord = np.floor(data_dict['coord'] / np.array(self.voxel_size)).astype(np.int)
        min_coord = discrete_coord.min(0) * np.array(self.voxel_size)
        discrete_coord -= discrete_coord.min(0)
        key = self.hash(discrete_coord)
        idx_sort = np.argsort(key)
        key_sort = key[idx_sort]
        _, inverse, count = np.unique(key_sort, return_inverse=True, return_counts=True)
        if self.mode == 'train':
            idx_select = np.cumsum(np.insert(count, 0, 0)[0:-1]) + np.random.randint(0, count.max(), count.size) % count
            idx_unique = idx_sort[idx_select]
            if self.return_discrete_coord:
                data_dict['discrete_coord'] = discrete_coord[idx_unique]
            if self.return_inverse:
                data_dict['mask'] = np.zeros_like(inverse)
                data_dict['mask'][idx_unique] = 1
                data_dict['inverse'] = np.zeros_like(inverse)
                data_dict['inverse'][idx_sort] = inverse
                data_dict['length'] = np.array(inverse.shape)
            if self.return_min_coord:
                data_dict['min_coord'] = min_coord.reshape([1, 3])
            for key in self.keys:
                data_dict[key] = data_dict[key][idx_unique]
            return data_dict
        elif self.mode == 'test':
            data_part_list = []
            for i in range(count.max()):
                idx_select = np.cumsum(np.insert(count, 0, 0)[0:-1]) + i % count
                idx_part = idx_sort[idx_select]
                data_part = dict(index=idx_part)
                for key in self.keys:
                    data_part[key] = data_dict[key][idx_part]
                if self.return_discrete_coord:
                    data_part['discrete_coord'] = discrete_coord[idx_part]
                if self.return_inverse:
                    data_part['inverse'] = np.zeros_like(inverse)
                    data_part['inverse'][idx_sort] = inverse
                    data_part['length'] = np.array(inverse.shape)
                if self.return_min_coord:
                    data_part['min_coord'] = min_coord.reshape([1, 3])
                data_part_list.append(data_part)
            return data_part_list
        else:
            raise NotImplementedError

    @staticmethod
    def ravel_hash_vec(arr):
        """
        Ravel the coordinates after subtracting the min coordinates.
        """
        assert arr.ndim == 2
        arr = arr.copy()
        arr -= arr.min(0)
        arr = arr.astype(np.uint64, copy=False)
        arr_max = arr.max(0).astype(np.uint64) + 1
        keys = np.zeros(arr.shape[0], dtype=np.uint64)
        for j in range(arr.shape[1] - 1):
            keys += arr[:, j]
            keys *= arr_max[j + 1]
        keys += arr[:, -1]
        return keys

    @staticmethod
    def fnv_hash_vec(arr):
        """
        FNV64-1A
        """
        assert arr.ndim == 2
        arr = arr.copy()
        arr = arr.astype(np.uint64, copy=False)
        hashed_arr = np.uint64(14695981039346656037) * np.ones(arr.shape[0], dtype=np.uint64)
        for j in range(arr.shape[1]):
            hashed_arr *= np.uint64(1099511628211)
            hashed_arr = np.bitwise_xor(hashed_arr, arr[:, j])
        return hashed_arr

def __call__(self, data_dict):
    assert 'coord' in data_dict.keys()
    discrete_coord = np.floor(data_dict['coord'] / np.array(self.voxel_size)).astype(np.int)
    min_coord = discrete_coord.min(0) * np.array(self.voxel_size)
    discrete_coord -= discrete_coord.min(0)
    key = self.hash(discrete_coord)
    idx_sort = np.argsort(key)
    key_sort = key[idx_sort]
    _, inverse, count = np.unique(key_sort, return_inverse=True, return_counts=True)
    if self.mode == 'train':
        idx_select = np.cumsum(np.insert(count, 0, 0)[0:-1]) + np.random.randint(0, count.max(), count.size) % count
        idx_unique = idx_sort[idx_select]
        if self.return_discrete_coord:
            data_dict['discrete_coord'] = discrete_coord[idx_unique]
        if self.return_inverse:
            data_dict['mask'] = np.zeros_like(inverse)
            data_dict['mask'][idx_unique] = 1
            data_dict['inverse'] = np.zeros_like(inverse)
            data_dict['inverse'][idx_sort] = inverse
            data_dict['length'] = np.array(inverse.shape)
        if self.return_min_coord:
            data_dict['min_coord'] = min_coord.reshape([1, 3])
        for key in self.keys:
            data_dict[key] = data_dict[key][idx_unique]
        return data_dict
    elif self.mode == 'test':
        data_part_list = []
        for i in range(count.max()):
            idx_select = np.cumsum(np.insert(count, 0, 0)[0:-1]) + i % count
            idx_part = idx_sort[idx_select]
            data_part = dict(index=idx_part)
            for key in self.keys:
                data_part[key] = data_dict[key][idx_part]
            if self.return_discrete_coord:
                data_part['discrete_coord'] = discrete_coord[idx_part]
            if self.return_inverse:
                data_part['inverse'] = np.zeros_like(inverse)
                data_part['inverse'][idx_sort] = inverse
                data_part['length'] = np.array(inverse.shape)
            if self.return_min_coord:
                data_part['min_coord'] = min_coord.reshape([1, 3])
            data_part_list.append(data_part)
        return data_part_list
    else:
        raise NotImplementedError

@staticmethod
def ravel_hash_vec(arr):
    """
        Ravel the coordinates after subtracting the min coordinates.
        """
    assert arr.ndim == 2
    arr = arr.copy()
    arr -= arr.min(0)
    arr = arr.astype(np.uint64, copy=False)
    arr_max = arr.max(0).astype(np.uint64) + 1
    keys = np.zeros(arr.shape[0], dtype=np.uint64)
    for j in range(arr.shape[1] - 1):
        keys += arr[:, j]
        keys *= arr_max[j + 1]
    keys += arr[:, -1]
    return keys

@staticmethod
def fnv_hash_vec(arr):
    """
        FNV64-1A
        """
    assert arr.ndim == 2
    arr = arr.copy()
    arr = arr.astype(np.uint64, copy=False)
    hashed_arr = np.uint64(14695981039346656037) * np.ones(arr.shape[0], dtype=np.uint64)
    for j in range(arr.shape[1]):
        hashed_arr *= np.uint64(1099511628211)
        hashed_arr = np.bitwise_xor(hashed_arr, arr[:, j])
    return hashed_arr

@TRANSFORMS.register_module()
class SphereCrop(object):

    def __init__(self, point_max=80000, sample_rate=None, mode='random'):
        self.point_max = point_max
        self.sample_rate = sample_rate
        assert mode in ['random', 'center', 'all']
        self.mode = mode

    def __call__(self, data_dict):
        point_max = int(self.sample_rate * data_dict['coord'].shape[0]) if self.sample_rate is not None else self.point_max
        assert 'coord' in data_dict.keys()
        if self.mode == 'all':
            if 'index' not in data_dict.keys():
                data_dict['index'] = np.arange(data_dict['coord'].shape[0])
            data_part_list = []
            if data_dict['coord'].shape[0] > point_max:
                coord_p, idx_uni = (np.random.rand(data_dict['coord'].shape[0]) * 0.001, np.array([]))
                while idx_uni.size != data_dict['index'].shape[0]:
                    init_idx = np.argmin(coord_p)
                    dist2 = np.sum(np.power(data_dict['coord'] - data_dict['coord'][init_idx], 2), 1)
                    idx_crop = np.argsort(dist2)[:point_max]
                    data_crop_dict = dict()
                    if 'coord' in data_dict.keys():
                        data_crop_dict['coord'] = data_dict['coord'][idx_crop]
                    if 'discrete_coord' in data_dict.keys():
                        data_crop_dict['discrete_coord'] = data_dict['discrete_coord'][idx_crop]
                    if 'normal' in data_dict.keys():
                        data_crop_dict['normal'] = data_dict['normal'][idx_crop]
                    if 'color' in data_dict.keys():
                        data_crop_dict['color'] = data_dict['color'][idx_crop]
                    data_crop_dict['weight'] = dist2[idx_crop]
                    data_crop_dict['index'] = data_dict['index'][idx_crop]
                    data_part_list.append(data_crop_dict)
                    delta = np.square(1 - data_crop_dict['weight'] / np.max(data_crop_dict['weight']))
                    coord_p[idx_crop] += delta
                    idx_uni = np.unique(np.concatenate((idx_uni, data_crop_dict['index'])))
            else:
                data_crop_dict = data_dict.copy()
                data_crop_dict['weight'] = np.zeros(data_dict['coord'].shape[0])
                data_crop_dict['index'] = data_dict['index']
                data_part_list.append(data_crop_dict)
            return data_part_list
        elif data_dict['coord'].shape[0] > point_max:
            if self.mode == 'random':
                center = data_dict['coord'][np.random.randint(data_dict['coord'].shape[0])]
            elif self.mode == 'center':
                center = data_dict['coord'][data_dict['coord'].shape[0] // 2]
            else:
                raise NotImplementedError
            idx_crop = np.argsort(np.sum(np.square(data_dict['coord'] - center), 1))[:point_max]
            if 'coord' in data_dict.keys():
                data_dict['coord'] = data_dict['coord'][idx_crop]
            if 'origin_coord' in data_dict.keys():
                data_dict['origin_coord'] = data_dict['origin_coord'][idx_crop]
            if 'discrete_coord' in data_dict.keys():
                data_dict['discrete_coord'] = data_dict['discrete_coord'][idx_crop]
            if 'color' in data_dict.keys():
                data_dict['color'] = data_dict['color'][idx_crop]
            if 'normal' in data_dict.keys():
                data_dict['normal'] = data_dict['normal'][idx_crop]
            if 'instance' in data_dict.keys():
                data_dict['instance'] = data_dict['instance'][idx_crop]
            if 'label' in data_dict.keys():
                data_dict['label'] = data_dict['label'][idx_crop] if len(data_dict['label']) != 1 else data_dict['label']
        return data_dict

def __call__(self, data_dict):
    point_max = int(self.sample_rate * data_dict['coord'].shape[0]) if self.sample_rate is not None else self.point_max
    assert 'coord' in data_dict.keys()
    if self.mode == 'all':
        if 'index' not in data_dict.keys():
            data_dict['index'] = np.arange(data_dict['coord'].shape[0])
        data_part_list = []
        if data_dict['coord'].shape[0] > point_max:
            coord_p, idx_uni = (np.random.rand(data_dict['coord'].shape[0]) * 0.001, np.array([]))
            while idx_uni.size != data_dict['index'].shape[0]:
                init_idx = np.argmin(coord_p)
                dist2 = np.sum(np.power(data_dict['coord'] - data_dict['coord'][init_idx], 2), 1)
                idx_crop = np.argsort(dist2)[:point_max]
                data_crop_dict = dict()
                if 'coord' in data_dict.keys():
                    data_crop_dict['coord'] = data_dict['coord'][idx_crop]
                if 'discrete_coord' in data_dict.keys():
                    data_crop_dict['discrete_coord'] = data_dict['discrete_coord'][idx_crop]
                if 'normal' in data_dict.keys():
                    data_crop_dict['normal'] = data_dict['normal'][idx_crop]
                if 'color' in data_dict.keys():
                    data_crop_dict['color'] = data_dict['color'][idx_crop]
                data_crop_dict['weight'] = dist2[idx_crop]
                data_crop_dict['index'] = data_dict['index'][idx_crop]
                data_part_list.append(data_crop_dict)
                delta = np.square(1 - data_crop_dict['weight'] / np.max(data_crop_dict['weight']))
                coord_p[idx_crop] += delta
                idx_uni = np.unique(np.concatenate((idx_uni, data_crop_dict['index'])))
        else:
            data_crop_dict = data_dict.copy()
            data_crop_dict['weight'] = np.zeros(data_dict['coord'].shape[0])
            data_crop_dict['index'] = data_dict['index']
            data_part_list.append(data_crop_dict)
        return data_part_list
    elif data_dict['coord'].shape[0] > point_max:
        if self.mode == 'random':
            center = data_dict['coord'][np.random.randint(data_dict['coord'].shape[0])]
        elif self.mode == 'center':
            center = data_dict['coord'][data_dict['coord'].shape[0] // 2]
        else:
            raise NotImplementedError
        idx_crop = np.argsort(np.sum(np.square(data_dict['coord'] - center), 1))[:point_max]
        if 'coord' in data_dict.keys():
            data_dict['coord'] = data_dict['coord'][idx_crop]
        if 'origin_coord' in data_dict.keys():
            data_dict['origin_coord'] = data_dict['origin_coord'][idx_crop]
        if 'discrete_coord' in data_dict.keys():
            data_dict['discrete_coord'] = data_dict['discrete_coord'][idx_crop]
        if 'color' in data_dict.keys():
            data_dict['color'] = data_dict['color'][idx_crop]
        if 'normal' in data_dict.keys():
            data_dict['normal'] = data_dict['normal'][idx_crop]
        if 'instance' in data_dict.keys():
            data_dict['instance'] = data_dict['instance'][idx_crop]
        if 'label' in data_dict.keys():
            data_dict['label'] = data_dict['label'][idx_crop] if len(data_dict['label']) != 1 else data_dict['label']
    return data_dict

@TRANSFORMS.register_module()
class ShufflePoint(object):

    def __call__(self, data_dict):
        assert 'coord' in data_dict.keys()
        shuffle_index = np.arange(data_dict['coord'].shape[0])
        np.random.shuffle(shuffle_index)
        if 'coord' in data_dict.keys():
            data_dict['coord'] = data_dict['coord'][shuffle_index]
        if 'discrete_coord' in data_dict.keys():
            data_dict['discrete_coord'] = data_dict['discrete_coord'][shuffle_index]
        if 'color' in data_dict.keys():
            data_dict['color'] = data_dict['color'][shuffle_index]
        if 'normal' in data_dict.keys():
            data_dict['normal'] = data_dict['normal'][shuffle_index]
        if 'instance' in data_dict.keys():
            data_dict['instance'] = data_dict['instance'][shuffle_index]
        if 'label' in data_dict.keys():
            data_dict['label'] = data_dict['label'][shuffle_index] if len(data_dict['label']) != 1 else data_dict['label']
        return data_dict

def __call__(self, data_dict):
    assert 'coord' in data_dict.keys()
    shuffle_index = np.arange(data_dict['coord'].shape[0])
    np.random.shuffle(shuffle_index)
    if 'coord' in data_dict.keys():
        data_dict['coord'] = data_dict['coord'][shuffle_index]
    if 'discrete_coord' in data_dict.keys():
        data_dict['discrete_coord'] = data_dict['discrete_coord'][shuffle_index]
    if 'color' in data_dict.keys():
        data_dict['color'] = data_dict['color'][shuffle_index]
    if 'normal' in data_dict.keys():
        data_dict['normal'] = data_dict['normal'][shuffle_index]
    if 'instance' in data_dict.keys():
        data_dict['instance'] = data_dict['instance'][shuffle_index]
    if 'label' in data_dict.keys():
        data_dict['label'] = data_dict['label'][shuffle_index] if len(data_dict['label']) != 1 else data_dict['label']
    return data_dict

@TRANSFORMS.register_module()
class CropBoundary(object):

    def __call__(self, data_dict):
        assert 'label' in data_dict
        label = data_dict['label'].flatten()
        mask = (label != 0) * (label != 1)
        if 'coord' in data_dict.keys():
            data_dict['coord'] = data_dict['coord'][mask]
        if 'discrete_coord' in data_dict.keys():
            data_dict['discrete_coord'] = data_dict['discrete_coord'][mask]
        if 'color' in data_dict.keys():
            data_dict['color'] = data_dict['color'][mask]
        if 'normal' in data_dict.keys():
            data_dict['normal'] = data_dict['normal'][mask]
        if 'label' in data_dict.keys():
            data_dict['label'] = data_dict['label'][mask]
        return data_dict

def __call__(self, data_dict):
    assert 'label' in data_dict
    label = data_dict['label'].flatten()
    mask = (label != 0) * (label != 1)
    if 'coord' in data_dict.keys():
        data_dict['coord'] = data_dict['coord'][mask]
    if 'discrete_coord' in data_dict.keys():
        data_dict['discrete_coord'] = data_dict['discrete_coord'][mask]
    if 'color' in data_dict.keys():
        data_dict['color'] = data_dict['color'][mask]
    if 'normal' in data_dict.keys():
        data_dict['normal'] = data_dict['normal'][mask]
    if 'label' in data_dict.keys():
        data_dict['label'] = data_dict['label'][mask]
    return data_dict

@TRANSFORMS.register_module()
class TwinGenerator(object):

    def __init__(self, twin_keys=('coord', 'normal', 'color'), twin_trans_cfg=None):
        self.twin_keys = twin_keys
        self.twin_trans = Compose(twin_trans_cfg)

    def __call__(self, data_dict):
        twin_dict = dict()
        for key in self.twin_keys:
            twin_dict[key] = data_dict[key].copy()
        twin_dict = self.twin_trans(twin_dict)
        for key, value in twin_dict.items():
            data_dict['twin_' + key] = value
        return data_dict

def __call__(self, data_dict):
    twin_dict = dict()
    for key in self.twin_keys:
        twin_dict[key] = data_dict[key].copy()
    twin_dict = self.twin_trans(twin_dict)
    for key, value in twin_dict.items():
        data_dict['twin_' + key] = value
    return data_dict

@TRANSFORMS.register_module()
class TwinGeneratorV2(object):

    def __init__(self, twin_keys=('coord', 'normal', 'color'), twin_trans_cfg=None):
        self.twin_keys = twin_keys
        self.twin_trans = Compose(twin_trans_cfg)

    def __call__(self, data_dict):
        twin1_dict = dict(origin_coord=data_dict['coord'].copy())
        twin2_dict = dict(origin_coord=data_dict['coord'].copy())
        for key in self.twin_keys:
            twin1_dict[key] = data_dict[key].copy()
            twin2_dict[key] = data_dict[key].copy()
        twin1_dict = self.twin_trans(twin1_dict)
        twin2_dict = self.twin_trans(twin2_dict)
        for key, value in twin1_dict.items():
            data_dict['twin1_' + key] = value
        for key, value in twin2_dict.items():
            data_dict['twin2_' + key] = value
        return data_dict

def __call__(self, data_dict):
    twin1_dict = dict(origin_coord=data_dict['coord'].copy())
    twin2_dict = dict(origin_coord=data_dict['coord'].copy())
    for key in self.twin_keys:
        twin1_dict[key] = data_dict[key].copy()
        twin2_dict[key] = data_dict[key].copy()
    twin1_dict = self.twin_trans(twin1_dict)
    twin2_dict = self.twin_trans(twin2_dict)
    for key, value in twin1_dict.items():
        data_dict['twin1_' + key] = value
    for key, value in twin2_dict.items():
        data_dict['twin2_' + key] = value
    return data_dict

@TRANSFORMS.register_module()
class GetInstanceInfo(object):

    def __init__(self, ignore_index=255):
        self.ignore_index = ignore_index

    def __call__(self, data_dict):
        coord = data_dict['coord']
        instance = data_dict['instance']
        centers = -np.ones((coord.shape[0], 3), dtype=np.float32)
        bbox = dict()
        unique_ids = np.unique(instance)
        for i in unique_ids:
            if i == self.ignore_index:
                continue
            mask = instance == i
            segments = coord[mask]
            centers[mask] = segments.mean(0)
            bbox[i] = np.concatenate([segments.min(0), segments.max(0)])
        data_dict['instance_center'] = centers
        data_dict['bbox'] = bbox
        return data_dict

def __call__(self, data_dict):
    coord = data_dict['coord']
    instance = data_dict['instance']
    centers = -np.ones((coord.shape[0], 3), dtype=np.float32)
    bbox = dict()
    unique_ids = np.unique(instance)
    for i in unique_ids:
        if i == self.ignore_index:
            continue
        mask = instance == i
        segments = coord[mask]
        centers[mask] = segments.mean(0)
        bbox[i] = np.concatenate([segments.min(0), segments.max(0)])
    data_dict['instance_center'] = centers
    data_dict['bbox'] = bbox
    return data_dict

@DATASETS.register_module()
class ArkitScenesDataset(Dataset):

    def __init__(self, split='Training', data_root='data/ARKitScenesMesh', transform=None, test_mode=False, test_cfg=None, loop=1):
        super(ArkitScenesDataset, self).__init__()
        self.data_root = data_root
        self.split = split
        self.transform = Compose(transform)
        self.loop = loop if not test_mode else 1
        self.test_mode = test_mode
        self.test_cfg = test_cfg if test_mode else None
        self.class2id = np.array(VALID_CLASS_IDS_200)
        if test_mode:
            self.test_voxelize = TRANSFORMS.build(self.test_cfg.voxelize)
            self.test_crop = TRANSFORMS.build(self.test_cfg.crop)
            self.post_transform = Compose(self.test_cfg.post_transform)
            self.aug_transform = [Compose(aug) for aug in self.test_cfg.aug_transform]
        self.data_list = self.get_data_list()
        logger = get_root_logger()
        logger.info('Totally {} x {} samples in {} set.'.format(len(self.data_list), self.loop, split))

    def get_data_list(self):
        if isinstance(self.split, str):
            data_list = glob.glob(os.path.join(self.data_root, self.split, '*.pth'))
        elif isinstance(self.split, list):
            data_list = []
            for split in self.split:
                data_list += glob.glob(os.path.join(self.data_root, split, '*.pth'))
        else:
            raise NotImplementedError
        return data_list

    def get_data(self, idx):
        data = torch.load(self.data_list[idx % len(self.data_list)])
        coord = data['coord']
        color = data['color']
        normal = data['normal']
        label = np.zeros(coord.shape[0])
        data_dict = dict(coord=coord, normal=normal, color=color, label=label)
        return data_dict

    def get_data_name(self, idx):
        data_idx = self.data_idx[idx % len(self.data_idx)]
        return os.path.basename(self.data_list[data_idx]).split('.')[0]

    def prepare_train_data(self, idx):
        data_dict = self.get_data(idx)
        data_dict = self.transform(data_dict)
        return data_dict

    def prepare_test_data(self, idx):
        data_dict = self.get_data(idx)
        label = data_dict.pop('label')
        data_dict = self.transform(data_dict)
        data_dict_list = []
        for aug in self.aug_transform:
            data_dict_list.append(aug(deepcopy(data_dict)))
        input_dict_list = []
        for data in data_dict_list:
            data_part_list = self.test_voxelize(data)
            for data_part in data_part_list:
                data_part_list = self.test_crop(data_part)
                input_dict_list += data_part_list
        for i in range(len(input_dict_list)):
            input_dict_list[i] = self.post_transform(input_dict_list[i])
        return (input_dict_list, label)

    def __getitem__(self, idx):
        if self.test_mode:
            return self.prepare_test_data(idx)
        else:
            return self.prepare_train_data(idx)

    def __len__(self):
        return len(self.data_list) * self.loop

def get_data(self, idx):
    data = torch.load(self.data_list[idx % len(self.data_list)])
    coord = data['coord']
    color = data['color']
    normal = data['normal']
    label = np.zeros(coord.shape[0])
    data_dict = dict(coord=coord, normal=normal, color=color, label=label)
    return data_dict

@DATASETS.register_module()
class DefaultDataset(Dataset):

    def __init__(self, split='train', data_root='data/dataset', transform=None, test_mode=False, test_cfg=None, loop=1):
        super(DefaultDataset, self).__init__()
        self.data_root = data_root
        self.split = split
        self.transform = Compose(transform)
        self.loop = loop if not test_mode else 1
        self.test_mode = test_mode
        self.test_cfg = test_cfg if test_mode else None
        if test_mode:
            self.test_voxelize = TRANSFORMS.build(self.test_cfg.voxelize)
            self.test_crop = TRANSFORMS.build(self.test_cfg.crop)
            self.post_transform = Compose(self.test_cfg.post_transform)
            self.aug_transform = [Compose(aug) for aug in self.test_cfg.aug_transform]
        self.data_list = self.get_data_list()
        logger = get_root_logger()
        logger.info('Totally {} x {} samples in {} set.'.format(len(self.data_list), self.loop, split))

    def get_data_list(self):
        if isinstance(self.split, str):
            data_list = glob.glob(os.path.join(self.data_root, self.split, '*.pth'))
        elif isinstance(self.split, list):
            data_list = []
            for split in self.split:
                data_list += glob.glob(os.path.join(self.data_root, split, '*.pth'))
        else:
            raise NotImplementedError
        return data_list

    def get_data(self, idx):
        data = torch.load(self.data_list[idx % len(self.data_list)])
        coord = data['coord']
        color = data['color']
        normal = data['normal']
        if 'semantic_gt' in data.keys():
            label = data['semantic_gt'].reshape([-1])
        else:
            label = np.zeros(coord.shape[0])
        data_dict = dict(coord=coord, norm=normal, color=color, label=label)
        return data_dict

    def get_data_name(self, idx):
        data_idx = idx % len(self.data_list)
        return os.path.basename(self.data_list[data_idx]).split('.')[0]

    def prepare_train_data(self, idx):
        data_dict = self.get_data(idx)
        data_dict = self.transform(data_dict)
        return data_dict

    def prepare_test_data(self, idx):
        data_dict = self.get_data(idx)
        label = data_dict.pop('label')
        data_dict = self.transform(data_dict)
        data_dict_list = []
        for aug in self.aug_transform:
            data_dict_list.append(aug(deepcopy(data_dict)))
        input_dict_list = []
        for data in data_dict_list:
            data_part_list = self.test_voxelize(data)
            for data_part in data_part_list:
                if self.test_crop:
                    data_part = self.test_crop(data_part)
                else:
                    data_part = [data_part]
                input_dict_list += data_part
        for i in range(len(input_dict_list)):
            input_dict_list[i] = self.post_transform(input_dict_list[i])
        return (input_dict_list, label)

    def __getitem__(self, idx):
        if self.test_mode:
            return self.prepare_test_data(idx)
        else:
            return self.prepare_train_data(idx)

    def __len__(self):
        return len(self.data_list) * self.loop

def get_data(self, idx):
    data = torch.load(self.data_list[idx % len(self.data_list)])
    coord = data['coord']
    color = data['color']
    normal = data['normal']
    if 'semantic_gt' in data.keys():
        label = data['semantic_gt'].reshape([-1])
    else:
        label = np.zeros(coord.shape[0])
    data_dict = dict(coord=coord, norm=normal, color=color, label=label)
    return data_dict

@DATASETS.register_module()
class S3DISDataset(Dataset):

    def __init__(self, split=('Area_1', 'Area_2', 'Area_3', 'Area_4', 'Area_6'), data_root='data/s3dis', transform=None, test_mode=False, test_cfg=None, loop=1):
        super(S3DISDataset, self).__init__()
        self.data_root = data_root
        self.split = split
        self.transform = Compose(transform)
        self.loop = loop if not test_mode else 1
        self.test_mode = test_mode
        self.test_cfg = test_cfg if test_mode else None
        if test_mode:
            self.test_voxelize = TRANSFORMS.build(self.test_cfg.voxelize)
            self.test_crop = TRANSFORMS.build(self.test_cfg.crop) if self.test_cfg.crop else None
            self.post_transform = Compose(self.test_cfg.post_transform)
            self.aug_transform = [Compose(aug) for aug in self.test_cfg.aug_transform]
        self.data_list = self.get_data_list()
        logger = get_root_logger()
        logger.info('Totally {} x {} samples in {} set.'.format(len(self.data_list), self.loop, split))

    def get_data_list(self):
        if isinstance(self.split, str):
            data_list = glob.glob(os.path.join(self.data_root, self.split, '*.pth'))
        elif isinstance(self.split, Sequence):
            data_list = []
            for split in self.split:
                data_list += glob.glob(os.path.join(self.data_root, split, '*.pth'))
        else:
            raise NotImplementedError
        return data_list

    def get_data(self, idx):
        data = torch.load(self.data_list[idx % len(self.data_list)])
        coord = data['coord']
        color = data['color']
        if 'semantic_gt' in data.keys():
            label = data['semantic_gt'].reshape([-1])
        else:
            label = np.zeros(coord.shape[0])
        data_dict = dict(coord=coord, color=color, label=label)
        return data_dict

    def get_data_name(self, idx):
        return os.path.basename(self.data_list[idx % len(self.data_list)]).split('.')[0]

    def prepare_train_data(self, idx):
        data_dict = self.get_data(idx)
        data_dict = self.transform(data_dict)
        return data_dict

    def prepare_test_data(self, idx):
        data_dict = self.get_data(idx)
        label = data_dict.pop('label')
        data_dict = self.transform(data_dict)
        data_dict_list = []
        for aug in self.aug_transform:
            data_dict_list.append(aug(deepcopy(data_dict)))
        input_dict_list = []
        for data in data_dict_list:
            data_part_list = self.test_voxelize(data)
            for data_part in data_part_list:
                if self.test_crop:
                    data_part = self.test_crop(data_part)
                else:
                    data_part = [data_part]
                input_dict_list += data_part
        for i in range(len(input_dict_list)):
            input_dict_list[i] = self.post_transform(input_dict_list[i])
        return (input_dict_list, label)

    def __getitem__(self, idx):
        if self.test_mode:
            return self.prepare_test_data(idx)
        else:
            return self.prepare_train_data(idx)

    def __len__(self):
        return len(self.data_list) * self.loop

def get_data(self, idx):
    data = torch.load(self.data_list[idx % len(self.data_list)])
    coord = data['coord']
    color = data['color']
    if 'semantic_gt' in data.keys():
        label = data['semantic_gt'].reshape([-1])
    else:
        label = np.zeros(coord.shape[0])
    data_dict = dict(coord=coord, color=color, label=label)
    return data_dict

@DATASETS.register_module()
class ScanNetDataset(Dataset):
    class2id = np.array(VALID_CLASS_IDS_20)

    def __init__(self, split='train', data_root='data/scannet', transform=None, test_mode=False, test_cfg=None, loop=1):
        super(ScanNetDataset, self).__init__()
        self.data_root = data_root
        self.split = split
        self.transform = Compose(transform)
        self.loop = loop if not test_mode else 1
        self.test_mode = test_mode
        self.test_cfg = test_cfg if test_mode else None
        if test_mode:
            self.test_voxelize = TRANSFORMS.build(self.test_cfg.voxelize)
            self.test_crop = TRANSFORMS.build(self.test_cfg.crop) if self.test_cfg.crop else None
            self.post_transform = Compose(self.test_cfg.post_transform)
            self.aug_transform = [Compose(aug) for aug in self.test_cfg.aug_transform]
        self.data_list = self.get_data_list()
        logger = get_root_logger()
        logger.info('Totally {} x {} samples in {} set.'.format(len(self.data_list), self.loop, split))

    def get_data_list(self):
        if isinstance(self.split, str):
            data_list = glob.glob(os.path.join(self.data_root, self.split, '*.pth'))
        elif isinstance(self.split, list):
            data_list = []
            for split in self.split:
                data_list += glob.glob(os.path.join(self.data_root, split, '*.pth'))
        else:
            raise NotImplementedError
        return data_list

    def get_data(self, idx):
        data = torch.load(self.data_list[idx % len(self.data_list)])
        coord = data['coord']
        color = data['color']
        normal = data['normal']
        if 'semantic_gt20' in data.keys():
            label = data['semantic_gt20'].reshape([-1])
        else:
            label = np.ones(coord.shape[0]) * 255
        data_dict = dict(coord=coord, normal=normal, color=color, label=label)
        return data_dict

    def get_data_name(self, idx):
        return os.path.basename(self.data_list[idx % len(self.data_list)]).split('.')[0]

    def prepare_train_data(self, idx):
        data_dict = self.get_data(idx)
        data_dict = self.transform(data_dict)
        return data_dict

    def prepare_test_data(self, idx):
        data_dict = self.get_data(idx)
        label = data_dict.pop('label')
        data_dict = self.transform(data_dict)
        data_dict_list = []
        for aug in self.aug_transform:
            data_dict_list.append(aug(deepcopy(data_dict)))
        input_dict_list = []
        for data in data_dict_list:
            data_part_list = self.test_voxelize(data)
            for data_part in data_part_list:
                if self.test_crop:
                    data_part = self.test_crop(data_part)
                else:
                    data_part = [data_part]
                input_dict_list += data_part
        for i in range(len(input_dict_list)):
            input_dict_list[i] = self.post_transform(input_dict_list[i])
        return (input_dict_list, label)

    def __getitem__(self, idx):
        if self.test_mode:
            return self.prepare_test_data(idx)
        else:
            return self.prepare_train_data(idx)

    def __len__(self):
        return len(self.data_list) * self.loop

def get_data(self, idx):
    data = torch.load(self.data_list[idx % len(self.data_list)])
    coord = data['coord']
    color = data['color']
    normal = data['normal']
    if 'semantic_gt20' in data.keys():
        label = data['semantic_gt20'].reshape([-1])
    else:
        label = np.ones(coord.shape[0]) * 255
    data_dict = dict(coord=coord, normal=normal, color=color, label=label)
    return data_dict

@DATASETS.register_module()
class ScanNet200Dataset(ScanNetDataset):
    class2id = np.array(VALID_CLASS_IDS_200)

    def get_data(self, idx):
        data = torch.load(self.data_list[idx % len(self.data_list)])
        coord = data['coord']
        color = data['color']
        normal = data['normal']
        if 'semantic_gt200' in data.keys():
            label = data['semantic_gt200'].reshape([-1])
        else:
            label = np.zeros(coord.shape[0])
        data_dict = dict(coord=coord, normal=normal, color=color, label=label)
        return data_dict

def get_data(self, idx):
    data = torch.load(self.data_list[idx % len(self.data_list)])
    coord = data['coord']
    color = data['color']
    normal = data['normal']
    if 'semantic_gt200' in data.keys():
        label = data['semantic_gt200'].reshape([-1])
    else:
        label = np.zeros(coord.shape[0])
    data_dict = dict(coord=coord, normal=normal, color=color, label=label)
    return data_dict

class SensorData:

    def __init__(self, filename):
        self.version = 4
        self.load(filename)

    def load(self, filename):
        with open(filename, 'rb') as f:
            version = struct.unpack('I', f.read(4))[0]
            assert self.version == version
            strlen = struct.unpack('Q', f.read(8))[0]
            self.sensor_name = b''.join(struct.unpack('c' * strlen, f.read(strlen)))
            self.intrinsic_color = np.asarray(struct.unpack('f' * 16, f.read(16 * 4)), dtype=np.float32).reshape(4, 4)
            self.extrinsic_color = np.asarray(struct.unpack('f' * 16, f.read(16 * 4)), dtype=np.float32).reshape(4, 4)
            self.intrinsic_depth = np.asarray(struct.unpack('f' * 16, f.read(16 * 4)), dtype=np.float32).reshape(4, 4)
            self.extrinsic_depth = np.asarray(struct.unpack('f' * 16, f.read(16 * 4)), dtype=np.float32).reshape(4, 4)
            self.color_compression_type = COMPRESSION_TYPE_COLOR[struct.unpack('i', f.read(4))[0]]
            self.depth_compression_type = COMPRESSION_TYPE_DEPTH[struct.unpack('i', f.read(4))[0]]
            self.color_width = struct.unpack('I', f.read(4))[0]
            self.color_height = struct.unpack('I', f.read(4))[0]
            self.depth_width = struct.unpack('I', f.read(4))[0]
            self.depth_height = struct.unpack('I', f.read(4))[0]
            self.depth_shift = struct.unpack('f', f.read(4))[0]
            num_frames = struct.unpack('Q', f.read(8))[0]
            self.frames = []
            for i in range(num_frames):
                frame = RGBDFrame()
                frame.load(f)
                self.frames.append(frame)

    def export_depth_images(self, output_path, image_size=None, frame_skip=1):
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        print('exporting', len(self.frames) // frame_skip, ' depth frames to', output_path)
        for f in range(0, len(self.frames), frame_skip):
            if os.path.exists(os.path.join(output_path, str(f) + '.png')):
                continue
            if f % 100 == 0:
                print('exporting', f, 'th depth frames to', os.path.join(output_path, str(f) + '.png'))
            depth_data = self.frames[f].decompress_depth(self.depth_compression_type)
            depth = np.fromstring(depth_data, dtype=np.uint16).reshape(self.depth_height, self.depth_width)
            if image_size is not None:
                depth = cv2.resize(depth, (image_size[1], image_size[0]), interpolation=cv2.INTER_NEAREST)
            imageio.imwrite(os.path.join(output_path, str(f) + '.png'), depth)

    def export_color_images(self, output_path, image_size=None, frame_skip=1):
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        print('exporting', len(self.frames) // frame_skip, 'color frames to', output_path)
        for f in range(0, len(self.frames), frame_skip):
            if os.path.exists(os.path.join(output_path, str(f) + '.png')):
                continue
            if f % 100 == 0:
                print('exporting', f, 'th color frames to', os.path.join(output_path, str(f) + '.png'))
            color = self.frames[f].decompress_color(self.color_compression_type)
            if image_size is not None:
                color = cv2.resize(color, (image_size[1], image_size[0]), interpolation=cv2.INTER_NEAREST)
            imageio.imwrite(os.path.join(output_path, str(f) + '.png'), color)

    def save_mat_to_file(self, matrix, filename):
        with open(filename, 'w') as f:
            for line in matrix:
                np.savetxt(f, line[np.newaxis], fmt='%f')

    def export_poses(self, output_path, frame_skip=1):
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        print('exporting', len(self.frames) // frame_skip, 'camera poses to', output_path)
        for f in range(0, len(self.frames), frame_skip):
            self.save_mat_to_file(self.frames[f].camera_to_world, os.path.join(output_path, str(f) + '.txt'))

    def export_intrinsics(self, output_path):
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        print('exporting camera intrinsics to', output_path)
        self.save_mat_to_file(self.intrinsic_color, os.path.join(output_path, 'intrinsic_color.txt'))
        self.save_mat_to_file(self.extrinsic_color, os.path.join(output_path, 'extrinsic_color.txt'))
        self.save_mat_to_file(self.intrinsic_depth, os.path.join(output_path, 'intrinsic_depth.txt'))
        self.save_mat_to_file(self.extrinsic_depth, os.path.join(output_path, 'extrinsic_depth.txt'))

def __init__(self, filename):
    self.version = 4
    self.load(filename)

def off_diagonal(x):
    n, m = x.shape
    assert n == m
    return x.flatten()[:-1].view(n - 1, n + 1)[:, 1:].flatten()

class PreTrainer(Trainer):

    def run_step(self, i, input_dict):
        data_time = time.time() - self.iter_end_time
        for key in input_dict.keys():
            input_dict[key] = input_dict[key].cuda(non_blocking=True)
        with torch.cuda.amp.autocast(enabled=self.cfg.enable_amp):
            output = self.model(input_dict)
            loss = output['loss']
        self.optimizer.zero_grad()
        if self.cfg.enable_amp:
            self.scaler.scale(loss).backward()
            self.scaler.step(self.optimizer)
            self.scaler.update()
        else:
            loss.backward()
            self.optimizer.step()
        self.scheduler.step()
        if self.cfg.empty_cache:
            torch.cuda.empty_cache()
        if comm.get_world_size() > 1:
            dist.all_reduce(loss)
            loss = loss / comm.get_world_size()
        batch_time = time.time() - self.iter_end_time
        self.iter_end_time = time.time()
        self.storage.put_scalar('loss', loss.item())
        self.storage.put_scalar('data_time', data_time)
        self.storage.put_scalar('batch_time', batch_time)
        current_iter = self.epoch * len(self.train_loader) + i + 1
        remain_iter = self.max_iter - current_iter
        remain_time = remain_iter * self.storage.history('batch_time').avg
        t_m, t_s = divmod(remain_time, 60)
        t_h, t_m = divmod(t_m, 60)
        remain_time = '{:02d}:{:02d}:{:02d}'.format(int(t_h), int(t_m), int(t_s))
        info = ''
        for key in output.keys():
            if key != 'loss':
                info += '{name} {value:.3f} '.format(name=key, value=output[key])
        self.logger.info('Train: [{epoch}/{max_epoch}][{iter}/{max_iter}] Data {data_time_val:.3f} ({data_time_avg:.3f}) Batch {batch_time_val:.3f} ({batch_time_avg:.3f}) Remain {remain_time} Lr {lr:.4f} Loss {loss:.4f} '.format(epoch=self.epoch + 1, max_epoch=self.max_epoch, iter=i + 1, max_iter=len(self.train_loader), data_time_val=data_time, data_time_avg=self.storage.history('data_time').avg, batch_time_val=batch_time, batch_time_avg=self.storage.history('batch_time').avg, remain_time=remain_time, lr=self.optimizer.state_dict()['param_groups'][0]['lr'], loss=loss.item()) + info)
        if i == 0:
            self.storage.history('data_time').reset()
            self.storage.history('batch_time').reset()
        if self.writer is not None:
            self.writer.add_scalar('lr', self.optimizer.state_dict()['param_groups'][0]['lr'], current_iter)
            self.writer.add_scalar('train_batch/loss', loss.item(), current_iter)

    def after_epoch(self):
        loss_avg = self.storage.history('loss').avg
        self.logger.info('Train result: loss/seg_loss/pos_loss {:.4f}.'.format(loss_avg))
        current_epoch = self.epoch + 1
        if self.writer is not None:
            self.writer.add_scalar('train/loss', loss_avg, current_epoch)
        self.storage.reset_histories()
        self.save_checkpoint()

    def save_checkpoint(self):
        if comm.is_main_process():
            filename = os.path.join(self.cfg.save_path, 'model', 'model_last.pth')
            self.logger.info('Saving checkpoint to: ' + filename)
            torch.save({'epoch': self.epoch + 1, 'state_dict': self.model.state_dict(), 'optimizer': self.optimizer.state_dict(), 'scheduler': self.scheduler.state_dict(), 'scaler': self.scaler.state_dict() if self.cfg.enable_amp else None, 'best_metric_value': self.best_metric_value}, filename + '.tmp')
            os.replace(filename + '.tmp', filename)
            if self.cfg.save_freq and self.cfg.save_freq % (self.epoch + 1) == 0:
                shutil.copyfile(filename, os.path.join(self.cfg.save_path, 'model', f'epoch_{self.epoch + 1}.pth'))

    def resume_or_load(self):
        if self.cfg.weight and os.path.isfile(self.cfg.weight):
            self.logger.info(f'Loading weight at: {self.cfg.weight}')
            checkpoint = torch.load(self.cfg.weight, map_location=lambda storage, loc: storage.cuda())
            from collections import OrderedDict
            load_state_info = self.model.load_state_dict(checkpoint['state_dict'], strict=False)
            self.logger.info(f'Missing keys: {load_state_info[0]}')
            if self.cfg.resume:
                self.logger.info(f'Resuming train at eval epoch: {checkpoint['epoch']}')
                self.start_epoch = checkpoint['epoch']
                self.best_metric_value = checkpoint['best_metric_value']
                self.optimizer.load_state_dict(checkpoint['optimizer'])
                self.scheduler.load_state_dict(checkpoint['scheduler'])
                if self.cfg.enable_amp:
                    self.scaler.load_state_dict(checkpoint['scaler'])
        else:
            self.logger.info(f'No weight found at: {self.cfg.weight}')

def run_step(self, i, input_dict):
    data_time = time.time() - self.iter_end_time
    for key in input_dict.keys():
        input_dict[key] = input_dict[key].cuda(non_blocking=True)
    with torch.cuda.amp.autocast(enabled=self.cfg.enable_amp):
        output = self.model(input_dict)
        loss = output['loss']
    self.optimizer.zero_grad()
    if self.cfg.enable_amp:
        self.scaler.scale(loss).backward()
        self.scaler.step(self.optimizer)
        self.scaler.update()
    else:
        loss.backward()
        self.optimizer.step()
    self.scheduler.step()
    if self.cfg.empty_cache:
        torch.cuda.empty_cache()
    if comm.get_world_size() > 1:
        dist.all_reduce(loss)
        loss = loss / comm.get_world_size()
    batch_time = time.time() - self.iter_end_time
    self.iter_end_time = time.time()
    self.storage.put_scalar('loss', loss.item())
    self.storage.put_scalar('data_time', data_time)
    self.storage.put_scalar('batch_time', batch_time)
    current_iter = self.epoch * len(self.train_loader) + i + 1
    remain_iter = self.max_iter - current_iter
    remain_time = remain_iter * self.storage.history('batch_time').avg
    t_m, t_s = divmod(remain_time, 60)
    t_h, t_m = divmod(t_m, 60)
    remain_time = '{:02d}:{:02d}:{:02d}'.format(int(t_h), int(t_m), int(t_s))
    info = ''
    for key in output.keys():
        if key != 'loss':
            info += '{name} {value:.3f} '.format(name=key, value=output[key])
    self.logger.info('Train: [{epoch}/{max_epoch}][{iter}/{max_iter}] Data {data_time_val:.3f} ({data_time_avg:.3f}) Batch {batch_time_val:.3f} ({batch_time_avg:.3f}) Remain {remain_time} Lr {lr:.4f} Loss {loss:.4f} '.format(epoch=self.epoch + 1, max_epoch=self.max_epoch, iter=i + 1, max_iter=len(self.train_loader), data_time_val=data_time, data_time_avg=self.storage.history('data_time').avg, batch_time_val=batch_time, batch_time_avg=self.storage.history('batch_time').avg, remain_time=remain_time, lr=self.optimizer.state_dict()['param_groups'][0]['lr'], loss=loss.item()) + info)
    if i == 0:
        self.storage.history('data_time').reset()
        self.storage.history('batch_time').reset()
    if self.writer is not None:
        self.writer.add_scalar('lr', self.optimizer.state_dict()['param_groups'][0]['lr'], current_iter)
        self.writer.add_scalar('train_batch/loss', loss.item(), current_iter)

def after_epoch(self):
    loss_avg = self.storage.history('loss').avg
    self.logger.info('Train result: loss/seg_loss/pos_loss {:.4f}.'.format(loss_avg))
    current_epoch = self.epoch + 1
    if self.writer is not None:
        self.writer.add_scalar('train/loss', loss_avg, current_epoch)
    self.storage.reset_histories()
    self.save_checkpoint()

