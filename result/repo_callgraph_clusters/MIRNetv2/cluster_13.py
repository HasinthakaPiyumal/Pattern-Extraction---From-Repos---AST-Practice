# Cluster 13

class Dataset_PairedImage(data.Dataset):
    """Paired image dataset for image restoration.

    Read LQ (Low Quality, e.g. LR (Low Resolution), blurry, noisy, etc) and
    GT image pairs.

    There are three modes:
    1. 'lmdb': Use lmdb files.
        If opt['io_backend'] == lmdb.
    2. 'meta_info_file': Use meta information file to generate paths.
        If opt['io_backend'] != lmdb and opt['meta_info_file'] is not None.
    3. 'folder': Scan folders to generate paths.
        The rest.

    Args:
        opt (dict): Config for train datasets. It contains the following keys:
            dataroot_gt (str): Data root path for gt.
            dataroot_lq (str): Data root path for lq.
            meta_info_file (str): Path for meta information file.
            io_backend (dict): IO backend type and other kwarg.
            filename_tmpl (str): Template for each filename. Note that the
                template excludes the file extension. Default: '{}'.
            gt_size (int): Cropped patched size for gt patches.
            geometric_augs (bool): Use geometric augmentations.

            scale (bool): Scale, which will be added automatically.
            phase (str): 'train' or 'val'.
    """

    def __init__(self, opt):
        super(Dataset_PairedImage, self).__init__()
        self.opt = opt
        self.file_client = None
        self.io_backend_opt = opt['io_backend']
        self.mean = opt['mean'] if 'mean' in opt else None
        self.std = opt['std'] if 'std' in opt else None
        self.gt_folder, self.lq_folder = (opt['dataroot_gt'], opt['dataroot_lq'])
        if 'filename_tmpl' in opt:
            self.filename_tmpl = opt['filename_tmpl']
        else:
            self.filename_tmpl = '{}'
        if self.io_backend_opt['type'] == 'lmdb':
            self.io_backend_opt['db_paths'] = [self.lq_folder, self.gt_folder]
            self.io_backend_opt['client_keys'] = ['lq', 'gt']
            self.paths = paired_paths_from_lmdb([self.lq_folder, self.gt_folder], ['lq', 'gt'])
        elif 'meta_info_file' in self.opt and self.opt['meta_info_file'] is not None:
            self.paths = paired_paths_from_meta_info_file([self.lq_folder, self.gt_folder], ['lq', 'gt'], self.opt['meta_info_file'], self.filename_tmpl)
        else:
            self.paths = paired_paths_from_folder([self.lq_folder, self.gt_folder], ['lq', 'gt'], self.filename_tmpl)
        if self.opt['phase'] == 'train':
            self.geometric_augs = opt['geometric_augs']

    def __getitem__(self, index):
        if self.file_client is None:
            self.file_client = FileClient(self.io_backend_opt.pop('type'), **self.io_backend_opt)
        scale = self.opt['scale']
        index = index % len(self.paths)
        gt_path = self.paths[index]['gt_path']
        img_bytes = self.file_client.get(gt_path, 'gt')
        try:
            img_gt = imfrombytes(img_bytes, float32=True)
        except:
            raise Exception('gt path {} not working'.format(gt_path))
        lq_path = self.paths[index]['lq_path']
        img_bytes = self.file_client.get(lq_path, 'lq')
        try:
            img_lq = imfrombytes(img_bytes, float32=True)
        except:
            raise Exception('lq path {} not working'.format(lq_path))
        if self.opt['phase'] == 'train':
            gt_size = self.opt['gt_size']
            img_gt, img_lq = padding(img_gt, img_lq, gt_size)
            img_gt, img_lq = paired_random_crop(img_gt, img_lq, gt_size, scale, gt_path)
            if self.geometric_augs:
                img_gt, img_lq = random_augmentation(img_gt, img_lq)
        img_gt, img_lq = img2tensor([img_gt, img_lq], bgr2rgb=True, float32=True)
        if self.mean is not None or self.std is not None:
            normalize(img_lq, self.mean, self.std, inplace=True)
            normalize(img_gt, self.mean, self.std, inplace=True)
        return {'lq': img_lq, 'gt': img_gt, 'lq_path': lq_path, 'gt_path': gt_path}

    def __len__(self):
        return len(self.paths)

def __init__(self, opt):
    super(Dataset_PairedImage, self).__init__()
    self.opt = opt
    self.file_client = None
    self.io_backend_opt = opt['io_backend']
    self.mean = opt['mean'] if 'mean' in opt else None
    self.std = opt['std'] if 'std' in opt else None
    self.gt_folder, self.lq_folder = (opt['dataroot_gt'], opt['dataroot_lq'])
    if 'filename_tmpl' in opt:
        self.filename_tmpl = opt['filename_tmpl']
    else:
        self.filename_tmpl = '{}'
    if self.io_backend_opt['type'] == 'lmdb':
        self.io_backend_opt['db_paths'] = [self.lq_folder, self.gt_folder]
        self.io_backend_opt['client_keys'] = ['lq', 'gt']
        self.paths = paired_paths_from_lmdb([self.lq_folder, self.gt_folder], ['lq', 'gt'])
    elif 'meta_info_file' in self.opt and self.opt['meta_info_file'] is not None:
        self.paths = paired_paths_from_meta_info_file([self.lq_folder, self.gt_folder], ['lq', 'gt'], self.opt['meta_info_file'], self.filename_tmpl)
    else:
        self.paths = paired_paths_from_folder([self.lq_folder, self.gt_folder], ['lq', 'gt'], self.filename_tmpl)
    if self.opt['phase'] == 'train':
        self.geometric_augs = opt['geometric_augs']

class Dataset_DefocusDeblur_DualPixel_16bit(data.Dataset):

    def __init__(self, opt):
        super(Dataset_DefocusDeblur_DualPixel_16bit, self).__init__()
        self.opt = opt
        self.file_client = None
        self.io_backend_opt = opt['io_backend']
        self.mean = opt['mean'] if 'mean' in opt else None
        self.std = opt['std'] if 'std' in opt else None
        self.gt_folder, self.lqL_folder, self.lqR_folder = (opt['dataroot_gt'], opt['dataroot_lqL'], opt['dataroot_lqR'])
        if 'filename_tmpl' in opt:
            self.filename_tmpl = opt['filename_tmpl']
        else:
            self.filename_tmpl = '{}'
        self.paths = paired_DP_paths_from_folder([self.lqL_folder, self.lqR_folder, self.gt_folder], ['lqL', 'lqR', 'gt'], self.filename_tmpl)
        if self.opt['phase'] == 'train':
            self.geometric_augs = self.opt['geometric_augs']

    def __getitem__(self, index):
        if self.file_client is None:
            self.file_client = FileClient(self.io_backend_opt.pop('type'), **self.io_backend_opt)
        scale = self.opt['scale']
        index = index % len(self.paths)
        gt_path = self.paths[index]['gt_path']
        img_bytes = self.file_client.get(gt_path, 'gt')
        try:
            img_gt = imfrombytesDP(img_bytes, float32=True)
        except:
            raise Exception('gt path {} not working'.format(gt_path))
        lqL_path = self.paths[index]['lqL_path']
        img_bytes = self.file_client.get(lqL_path, 'lqL')
        try:
            img_lqL = imfrombytesDP(img_bytes, float32=True)
        except:
            raise Exception('lqL path {} not working'.format(lqL_path))
        lqR_path = self.paths[index]['lqR_path']
        img_bytes = self.file_client.get(lqR_path, 'lqR')
        try:
            img_lqR = imfrombytesDP(img_bytes, float32=True)
        except:
            raise Exception('lqR path {} not working'.format(lqR_path))
        if self.opt['phase'] == 'train':
            gt_size = self.opt['gt_size']
            img_lqL, img_lqR, img_gt = padding_DP(img_lqL, img_lqR, img_gt, gt_size)
            img_lqL, img_lqR, img_gt = paired_random_crop_DP(img_lqL, img_lqR, img_gt, gt_size, scale, gt_path)
            if self.geometric_augs:
                img_lqL, img_lqR, img_gt = random_augmentation(img_lqL, img_lqR, img_gt)
        img_lqL, img_lqR, img_gt = img2tensor([img_lqL, img_lqR, img_gt], bgr2rgb=True, float32=True)
        if self.mean is not None or self.std is not None:
            normalize(img_lqL, self.mean, self.std, inplace=True)
            normalize(img_lqR, self.mean, self.std, inplace=True)
            normalize(img_gt, self.mean, self.std, inplace=True)
        img_lq = torch.cat([img_lqL, img_lqR], 0)
        return {'lq': img_lq, 'gt': img_gt, 'lq_path': lqL_path, 'gt_path': gt_path}

    def __len__(self):
        return len(self.paths)

def __init__(self, opt):
    super(Dataset_DefocusDeblur_DualPixel_16bit, self).__init__()
    self.opt = opt
    self.file_client = None
    self.io_backend_opt = opt['io_backend']
    self.mean = opt['mean'] if 'mean' in opt else None
    self.std = opt['std'] if 'std' in opt else None
    self.gt_folder, self.lqL_folder, self.lqR_folder = (opt['dataroot_gt'], opt['dataroot_lqL'], opt['dataroot_lqR'])
    if 'filename_tmpl' in opt:
        self.filename_tmpl = opt['filename_tmpl']
    else:
        self.filename_tmpl = '{}'
    self.paths = paired_DP_paths_from_folder([self.lqL_folder, self.lqR_folder, self.gt_folder], ['lqL', 'lqR', 'gt'], self.filename_tmpl)
    if self.opt['phase'] == 'train':
        self.geometric_augs = self.opt['geometric_augs']

class PrefetchGenerator(threading.Thread):
    """A general prefetch generator.

    Ref:
    https://stackoverflow.com/questions/7323664/python-generator-pre-fetch

    Args:
        generator: Python generator.
        num_prefetch_queue (int): Number of prefetch queue.
    """

    def __init__(self, generator, num_prefetch_queue):
        threading.Thread.__init__(self)
        self.queue = Queue.Queue(num_prefetch_queue)
        self.generator = generator
        self.daemon = True
        self.start()

    def run(self):
        for item in self.generator:
            self.queue.put(item)
        self.queue.put(None)

    def __next__(self):
        next_item = self.queue.get()
        if next_item is None:
            raise StopIteration
        return next_item

    def __iter__(self):
        return self

def __init__(self, generator, num_prefetch_queue):
    threading.Thread.__init__(self)
    self.queue = Queue.Queue(num_prefetch_queue)
    self.generator = generator
    self.daemon = True
    self.start()

class PrefetchDataLoader(DataLoader):
    """Prefetch version of dataloader.

    Ref:
    https://github.com/IgorSusmelj/pytorch-styleguide/issues/5#

    TODO:
    Need to test on single gpu and ddp (multi-gpu). There is a known issue in
    ddp.

    Args:
        num_prefetch_queue (int): Number of prefetch queue.
        kwargs (dict): Other arguments for dataloader.
    """

    def __init__(self, num_prefetch_queue, **kwargs):
        self.num_prefetch_queue = num_prefetch_queue
        super(PrefetchDataLoader, self).__init__(**kwargs)

    def __iter__(self):
        return PrefetchGenerator(super().__iter__(), self.num_prefetch_queue)

def __init__(self, num_prefetch_queue, **kwargs):
    self.num_prefetch_queue = num_prefetch_queue
    super(PrefetchDataLoader, self).__init__(**kwargs)

def __iter__(self):
    return PrefetchGenerator(super().__iter__(), self.num_prefetch_queue)

class VideoRecurrentTestDataset(VideoTestDataset):
    """Video test dataset for recurrent architectures, which takes LR video
    frames as input and output corresponding HR video frames.

    Args:
        Same as VideoTestDataset.
        Unused opt:
            padding (str): Padding mode.

    """

    def __init__(self, opt):
        super(VideoRecurrentTestDataset, self).__init__(opt)
        self.folders = sorted(list(set(self.data_info['folder'])))

    def __getitem__(self, index):
        folder = self.folders[index]
        if self.cache_data:
            imgs_lq = self.imgs_lq[folder]
            imgs_gt = self.imgs_gt[folder]
        else:
            raise NotImplementedError('Without cache_data is not implemented.')
        return {'lq': imgs_lq, 'gt': imgs_gt, 'folder': folder}

    def __len__(self):
        return len(self.folders)

def __init__(self, opt):
    super(VideoRecurrentTestDataset, self).__init__(opt)
    self.folders = sorted(list(set(self.data_info['folder'])))

class MultiStepRestartLR(_LRScheduler):
    """ MultiStep with restarts learning rate scheme.

    Args:
        optimizer (torch.nn.optimizer): Torch optimizer.
        milestones (list): Iterations that will decrease learning rate.
        gamma (float): Decrease ratio. Default: 0.1.
        restarts (list): Restart iterations. Default: [0].
        restart_weights (list): Restart weights at each restart iteration.
            Default: [1].
        last_epoch (int): Used in _LRScheduler. Default: -1.
    """

    def __init__(self, optimizer, milestones, gamma=0.1, restarts=(0,), restart_weights=(1,), last_epoch=-1):
        self.milestones = Counter(milestones)
        self.gamma = gamma
        self.restarts = restarts
        self.restart_weights = restart_weights
        assert len(self.restarts) == len(self.restart_weights), 'restarts and their weights do not match.'
        super(MultiStepRestartLR, self).__init__(optimizer, last_epoch)

    def get_lr(self):
        if self.last_epoch in self.restarts:
            weight = self.restart_weights[self.restarts.index(self.last_epoch)]
            return [group['initial_lr'] * weight for group in self.optimizer.param_groups]
        if self.last_epoch not in self.milestones:
            return [group['lr'] for group in self.optimizer.param_groups]
        return [group['lr'] * self.gamma ** self.milestones[self.last_epoch] for group in self.optimizer.param_groups]

def __init__(self, optimizer, milestones, gamma=0.1, restarts=(0,), restart_weights=(1,), last_epoch=-1):
    self.milestones = Counter(milestones)
    self.gamma = gamma
    self.restarts = restarts
    self.restart_weights = restart_weights
    assert len(self.restarts) == len(self.restart_weights), 'restarts and their weights do not match.'
    super(MultiStepRestartLR, self).__init__(optimizer, last_epoch)

class LinearLR(_LRScheduler):
    """

    Args:
        optimizer (torch.nn.optimizer): Torch optimizer.
        milestones (list): Iterations that will decrease learning rate.
        gamma (float): Decrease ratio. Default: 0.1.
        last_epoch (int): Used in _LRScheduler. Default: -1.
    """

    def __init__(self, optimizer, total_iter, last_epoch=-1):
        self.total_iter = total_iter
        super(LinearLR, self).__init__(optimizer, last_epoch)

    def get_lr(self):
        process = self.last_epoch / self.total_iter
        weight = 1 - process
        return [weight * group['initial_lr'] for group in self.optimizer.param_groups]

def __init__(self, optimizer, total_iter, last_epoch=-1):
    self.total_iter = total_iter
    super(LinearLR, self).__init__(optimizer, last_epoch)

class VibrateLR(_LRScheduler):
    """

    Args:
        optimizer (torch.nn.optimizer): Torch optimizer.
        milestones (list): Iterations that will decrease learning rate.
        gamma (float): Decrease ratio. Default: 0.1.
        last_epoch (int): Used in _LRScheduler. Default: -1.
    """

    def __init__(self, optimizer, total_iter, last_epoch=-1):
        self.total_iter = total_iter
        super(VibrateLR, self).__init__(optimizer, last_epoch)

    def get_lr(self):
        process = self.last_epoch / self.total_iter
        f = 0.1
        if process < 3 / 8:
            f = 1 - process * 8 / 3
        elif process < 5 / 8:
            f = 0.2
        T = self.total_iter // 80
        Th = T // 2
        t = self.last_epoch % T
        f2 = t / Th
        if t >= Th:
            f2 = 2 - f2
        weight = f * f2
        if self.last_epoch < Th:
            weight = max(0.1, weight)
        return [weight * group['initial_lr'] for group in self.optimizer.param_groups]

def __init__(self, optimizer, total_iter, last_epoch=-1):
    self.total_iter = total_iter
    super(VibrateLR, self).__init__(optimizer, last_epoch)

class CosineAnnealingRestartLR(_LRScheduler):
    """ Cosine annealing with restarts learning rate scheme.

    An example of config:
    periods = [10, 10, 10, 10]
    restart_weights = [1, 0.5, 0.5, 0.5]
    eta_min=1e-7

    It has four cycles, each has 10 iterations. At 10th, 20th, 30th, the
    scheduler will restart with the weights in restart_weights.

    Args:
        optimizer (torch.nn.optimizer): Torch optimizer.
        periods (list): Period for each cosine anneling cycle.
        restart_weights (list): Restart weights at each restart iteration.
            Default: [1].
        eta_min (float): The mimimum lr. Default: 0.
        last_epoch (int): Used in _LRScheduler. Default: -1.
    """

    def __init__(self, optimizer, periods, restart_weights=(1,), eta_min=0, last_epoch=-1):
        self.periods = periods
        self.restart_weights = restart_weights
        self.eta_min = eta_min
        assert len(self.periods) == len(self.restart_weights), 'periods and restart_weights should have the same length.'
        self.cumulative_period = [sum(self.periods[0:i + 1]) for i in range(0, len(self.periods))]
        super(CosineAnnealingRestartLR, self).__init__(optimizer, last_epoch)

    def get_lr(self):
        idx = get_position_from_periods(self.last_epoch, self.cumulative_period)
        current_weight = self.restart_weights[idx]
        nearest_restart = 0 if idx == 0 else self.cumulative_period[idx - 1]
        current_period = self.periods[idx]
        return [self.eta_min + current_weight * 0.5 * (base_lr - self.eta_min) * (1 + math.cos(math.pi * ((self.last_epoch - nearest_restart) / current_period))) for base_lr in self.base_lrs]

def __init__(self, optimizer, periods, restart_weights=(1,), eta_min=0, last_epoch=-1):
    self.periods = periods
    self.restart_weights = restart_weights
    self.eta_min = eta_min
    assert len(self.periods) == len(self.restart_weights), 'periods and restart_weights should have the same length.'
    self.cumulative_period = [sum(self.periods[0:i + 1]) for i in range(0, len(self.periods))]
    super(CosineAnnealingRestartLR, self).__init__(optimizer, last_epoch)

class CosineAnnealingRestartCyclicLR(_LRScheduler):
    """ Cosine annealing with restarts learning rate scheme.
    An example of config:
    periods = [10, 10, 10, 10]
    restart_weights = [1, 0.5, 0.5, 0.5]
    eta_min=1e-7
    It has four cycles, each has 10 iterations. At 10th, 20th, 30th, the
    scheduler will restart with the weights in restart_weights.
    Args:
        optimizer (torch.nn.optimizer): Torch optimizer.
        periods (list): Period for each cosine anneling cycle.
        restart_weights (list): Restart weights at each restart iteration.
            Default: [1].
        eta_min (float): The mimimum lr. Default: 0.
        last_epoch (int): Used in _LRScheduler. Default: -1.
    """

    def __init__(self, optimizer, periods, restart_weights=(1,), eta_mins=(0,), last_epoch=-1):
        self.periods = periods
        self.restart_weights = restart_weights
        self.eta_mins = eta_mins
        assert len(self.periods) == len(self.restart_weights), 'periods and restart_weights should have the same length.'
        self.cumulative_period = [sum(self.periods[0:i + 1]) for i in range(0, len(self.periods))]
        super(CosineAnnealingRestartCyclicLR, self).__init__(optimizer, last_epoch)

    def get_lr(self):
        idx = get_position_from_periods(self.last_epoch, self.cumulative_period)
        current_weight = self.restart_weights[idx]
        nearest_restart = 0 if idx == 0 else self.cumulative_period[idx - 1]
        current_period = self.periods[idx]
        eta_min = self.eta_mins[idx]
        return [eta_min + current_weight * 0.5 * (base_lr - eta_min) * (1 + math.cos(math.pi * ((self.last_epoch - nearest_restart) / current_period))) for base_lr in self.base_lrs]

def __init__(self, optimizer, periods, restart_weights=(1,), eta_mins=(0,), last_epoch=-1):
    self.periods = periods
    self.restart_weights = restart_weights
    self.eta_mins = eta_mins
    assert len(self.periods) == len(self.restart_weights), 'periods and restart_weights should have the same length.'
    self.cumulative_period = [sum(self.periods[0:i + 1]) for i in range(0, len(self.periods))]
    super(CosineAnnealingRestartCyclicLR, self).__init__(optimizer, last_epoch)

class L1Loss(nn.Module):
    """L1 (mean absolute error, MAE) loss.

    Args:
        loss_weight (float): Loss weight for L1 loss. Default: 1.0.
        reduction (str): Specifies the reduction to apply to the output.
            Supported choices are 'none' | 'mean' | 'sum'. Default: 'mean'.
    """

    def __init__(self, loss_weight=1.0, reduction='mean'):
        super(L1Loss, self).__init__()
        if reduction not in ['none', 'mean', 'sum']:
            raise ValueError(f'Unsupported reduction mode: {reduction}. Supported ones are: {_reduction_modes}')
        self.loss_weight = loss_weight
        self.reduction = reduction

    def forward(self, pred, target, weight=None, **kwargs):
        """
        Args:
            pred (Tensor): of shape (N, C, H, W). Predicted tensor.
            target (Tensor): of shape (N, C, H, W). Ground truth tensor.
            weight (Tensor, optional): of shape (N, C, H, W). Element-wise
                weights. Default: None.
        """
        return self.loss_weight * l1_loss(pred, target, weight, reduction=self.reduction)

def __init__(self, loss_weight=1.0, reduction='mean'):
    super(L1Loss, self).__init__()
    if reduction not in ['none', 'mean', 'sum']:
        raise ValueError(f'Unsupported reduction mode: {reduction}. Supported ones are: {_reduction_modes}')
    self.loss_weight = loss_weight
    self.reduction = reduction

class MSELoss(nn.Module):
    """MSE (L2) loss.

    Args:
        loss_weight (float): Loss weight for MSE loss. Default: 1.0.
        reduction (str): Specifies the reduction to apply to the output.
            Supported choices are 'none' | 'mean' | 'sum'. Default: 'mean'.
    """

    def __init__(self, loss_weight=1.0, reduction='mean'):
        super(MSELoss, self).__init__()
        if reduction not in ['none', 'mean', 'sum']:
            raise ValueError(f'Unsupported reduction mode: {reduction}. Supported ones are: {_reduction_modes}')
        self.loss_weight = loss_weight
        self.reduction = reduction

    def forward(self, pred, target, weight=None, **kwargs):
        """
        Args:
            pred (Tensor): of shape (N, C, H, W). Predicted tensor.
            target (Tensor): of shape (N, C, H, W). Ground truth tensor.
            weight (Tensor, optional): of shape (N, C, H, W). Element-wise
                weights. Default: None.
        """
        return self.loss_weight * mse_loss(pred, target, weight, reduction=self.reduction)

def __init__(self, loss_weight=1.0, reduction='mean'):
    super(MSELoss, self).__init__()
    if reduction not in ['none', 'mean', 'sum']:
        raise ValueError(f'Unsupported reduction mode: {reduction}. Supported ones are: {_reduction_modes}')
    self.loss_weight = loss_weight
    self.reduction = reduction

class PSNRLoss(nn.Module):

    def __init__(self, loss_weight=1.0, reduction='mean', toY=False):
        super(PSNRLoss, self).__init__()
        assert reduction == 'mean'
        self.loss_weight = loss_weight
        self.scale = 10 / np.log(10)
        self.toY = toY
        self.coef = torch.tensor([65.481, 128.553, 24.966]).reshape(1, 3, 1, 1)
        self.first = True

    def forward(self, pred, target):
        assert len(pred.size()) == 4
        if self.toY:
            if self.first:
                self.coef = self.coef.to(pred.device)
                self.first = False
            pred = (pred * self.coef).sum(dim=1).unsqueeze(dim=1) + 16.0
            target = (target * self.coef).sum(dim=1).unsqueeze(dim=1) + 16.0
            pred, target = (pred / 255.0, target / 255.0)
            pass
        assert len(pred.size()) == 4
        return self.loss_weight * self.scale * torch.log(((pred - target) ** 2).mean(dim=(1, 2, 3)) + 1e-08).mean()

def __init__(self, loss_weight=1.0, reduction='mean', toY=False):
    super(PSNRLoss, self).__init__()
    assert reduction == 'mean'
    self.loss_weight = loss_weight
    self.scale = 10 / np.log(10)
    self.toY = toY
    self.coef = torch.tensor([65.481, 128.553, 24.966]).reshape(1, 3, 1, 1)
    self.first = True

def forward(self, pred, target):
    assert len(pred.size()) == 4
    if self.toY:
        if self.first:
            self.coef = self.coef.to(pred.device)
            self.first = False
        pred = (pred * self.coef).sum(dim=1).unsqueeze(dim=1) + 16.0
        target = (target * self.coef).sum(dim=1).unsqueeze(dim=1) + 16.0
        pred, target = (pred / 255.0, target / 255.0)
        pass
    assert len(pred.size()) == 4
    return self.loss_weight * self.scale * torch.log(((pred - target) ** 2).mean(dim=(1, 2, 3)) + 1e-08).mean()

class CharbonnierLoss(nn.Module):
    """Charbonnier Loss (L1)"""

    def __init__(self, loss_weight=1.0, reduction='mean', eps=0.001):
        super(CharbonnierLoss, self).__init__()
        self.eps = eps

    def forward(self, x, y):
        diff = x - y
        loss = torch.mean(torch.sqrt(diff * diff + self.eps * self.eps))
        return loss

def __init__(self, loss_weight=1.0, reduction='mean', eps=0.001):
    super(CharbonnierLoss, self).__init__()
    self.eps = eps

class SKFF(nn.Module):

    def __init__(self, in_channels, height=3, reduction=8, bias=False):
        super(SKFF, self).__init__()
        self.height = height
        d = max(int(in_channels / reduction), 4)
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.conv_du = nn.Sequential(nn.Conv2d(in_channels, d, 1, padding=0, bias=bias), nn.LeakyReLU(0.2))
        self.fcs = nn.ModuleList([])
        for i in range(self.height):
            self.fcs.append(nn.Conv2d(d, in_channels, kernel_size=1, stride=1, bias=bias))
        self.softmax = nn.Softmax(dim=1)

    def forward(self, inp_feats):
        batch_size = inp_feats[0].shape[0]
        n_feats = inp_feats[0].shape[1]
        inp_feats = torch.cat(inp_feats, dim=1)
        inp_feats = inp_feats.view(batch_size, self.height, n_feats, inp_feats.shape[2], inp_feats.shape[3])
        feats_U = torch.sum(inp_feats, dim=1)
        feats_S = self.avg_pool(feats_U)
        feats_Z = self.conv_du(feats_S)
        attention_vectors = [fc(feats_Z) for fc in self.fcs]
        attention_vectors = torch.cat(attention_vectors, dim=1)
        attention_vectors = attention_vectors.view(batch_size, self.height, n_feats, 1, 1)
        attention_vectors = self.softmax(attention_vectors)
        feats_V = torch.sum(inp_feats * attention_vectors, dim=1)
        return feats_V

def __init__(self, in_channels, height=3, reduction=8, bias=False):
    super(SKFF, self).__init__()
    self.height = height
    d = max(int(in_channels / reduction), 4)
    self.avg_pool = nn.AdaptiveAvgPool2d(1)
    self.conv_du = nn.Sequential(nn.Conv2d(in_channels, d, 1, padding=0, bias=bias), nn.LeakyReLU(0.2))
    self.fcs = nn.ModuleList([])
    for i in range(self.height):
        self.fcs.append(nn.Conv2d(d, in_channels, kernel_size=1, stride=1, bias=bias))
    self.softmax = nn.Softmax(dim=1)

class ContextBlock(nn.Module):

    def __init__(self, n_feat, bias=False):
        super(ContextBlock, self).__init__()
        self.conv_mask = nn.Conv2d(n_feat, 1, kernel_size=1, bias=bias)
        self.softmax = nn.Softmax(dim=2)
        self.channel_add_conv = nn.Sequential(nn.Conv2d(n_feat, n_feat, kernel_size=1, bias=bias), nn.LeakyReLU(0.2), nn.Conv2d(n_feat, n_feat, kernel_size=1, bias=bias))

    def modeling(self, x):
        batch, channel, height, width = x.size()
        input_x = x
        input_x = input_x.view(batch, channel, height * width)
        input_x = input_x.unsqueeze(1)
        context_mask = self.conv_mask(x)
        context_mask = context_mask.view(batch, 1, height * width)
        context_mask = self.softmax(context_mask)
        context_mask = context_mask.unsqueeze(3)
        context = torch.matmul(input_x, context_mask)
        context = context.view(batch, channel, 1, 1)
        return context

    def forward(self, x):
        context = self.modeling(x)
        channel_add_term = self.channel_add_conv(context)
        x = x + channel_add_term
        return x

def __init__(self, n_feat, bias=False):
    super(ContextBlock, self).__init__()
    self.conv_mask = nn.Conv2d(n_feat, 1, kernel_size=1, bias=bias)
    self.softmax = nn.Softmax(dim=2)
    self.channel_add_conv = nn.Sequential(nn.Conv2d(n_feat, n_feat, kernel_size=1, bias=bias), nn.LeakyReLU(0.2), nn.Conv2d(n_feat, n_feat, kernel_size=1, bias=bias))

class RCB(nn.Module):

    def __init__(self, n_feat, kernel_size=3, reduction=8, bias=False, groups=1):
        super(RCB, self).__init__()
        act = nn.LeakyReLU(0.2)
        self.body = nn.Sequential(nn.Conv2d(n_feat, n_feat, kernel_size=3, stride=1, padding=1, bias=bias, groups=groups), act, nn.Conv2d(n_feat, n_feat, kernel_size=3, stride=1, padding=1, bias=bias, groups=groups))
        self.act = act
        self.gcnet = ContextBlock(n_feat, bias=bias)

    def forward(self, x):
        res = self.body(x)
        res = self.act(self.gcnet(res))
        res += x
        return res

def __init__(self, n_feat, kernel_size=3, reduction=8, bias=False, groups=1):
    super(RCB, self).__init__()
    act = nn.LeakyReLU(0.2)
    self.body = nn.Sequential(nn.Conv2d(n_feat, n_feat, kernel_size=3, stride=1, padding=1, bias=bias, groups=groups), act, nn.Conv2d(n_feat, n_feat, kernel_size=3, stride=1, padding=1, bias=bias, groups=groups))
    self.act = act
    self.gcnet = ContextBlock(n_feat, bias=bias)

class Down(nn.Module):

    def __init__(self, in_channels, chan_factor, bias=False):
        super(Down, self).__init__()
        self.bot = nn.Sequential(nn.AvgPool2d(2, ceil_mode=True, count_include_pad=False), nn.Conv2d(in_channels, int(in_channels * chan_factor), 1, stride=1, padding=0, bias=bias))

    def forward(self, x):
        return self.bot(x)

def __init__(self, in_channels, chan_factor, bias=False):
    super(Down, self).__init__()
    self.bot = nn.Sequential(nn.AvgPool2d(2, ceil_mode=True, count_include_pad=False), nn.Conv2d(in_channels, int(in_channels * chan_factor), 1, stride=1, padding=0, bias=bias))

class DownSample(nn.Module):

    def __init__(self, in_channels, scale_factor, chan_factor=2, kernel_size=3):
        super(DownSample, self).__init__()
        self.scale_factor = int(np.log2(scale_factor))
        modules_body = []
        for i in range(self.scale_factor):
            modules_body.append(Down(in_channels, chan_factor))
            in_channels = int(in_channels * chan_factor)
        self.body = nn.Sequential(*modules_body)

    def forward(self, x):
        x = self.body(x)
        return x

def __init__(self, in_channels, scale_factor, chan_factor=2, kernel_size=3):
    super(DownSample, self).__init__()
    self.scale_factor = int(np.log2(scale_factor))
    modules_body = []
    for i in range(self.scale_factor):
        modules_body.append(Down(in_channels, chan_factor))
        in_channels = int(in_channels * chan_factor)
    self.body = nn.Sequential(*modules_body)

class Up(nn.Module):

    def __init__(self, in_channels, chan_factor, bias=False):
        super(Up, self).__init__()
        self.bot = nn.Sequential(nn.Conv2d(in_channels, int(in_channels // chan_factor), 1, stride=1, padding=0, bias=bias), nn.Upsample(scale_factor=2, mode='bilinear', align_corners=bias))

    def forward(self, x):
        return self.bot(x)

def __init__(self, in_channels, chan_factor, bias=False):
    super(Up, self).__init__()
    self.bot = nn.Sequential(nn.Conv2d(in_channels, int(in_channels // chan_factor), 1, stride=1, padding=0, bias=bias), nn.Upsample(scale_factor=2, mode='bilinear', align_corners=bias))

class UpSample(nn.Module):

    def __init__(self, in_channels, scale_factor, chan_factor=2, kernel_size=3):
        super(UpSample, self).__init__()
        self.scale_factor = int(np.log2(scale_factor))
        modules_body = []
        for i in range(self.scale_factor):
            modules_body.append(Up(in_channels, chan_factor))
            in_channels = int(in_channels // chan_factor)
        self.body = nn.Sequential(*modules_body)

    def forward(self, x):
        x = self.body(x)
        return x

def __init__(self, in_channels, scale_factor, chan_factor=2, kernel_size=3):
    super(UpSample, self).__init__()
    self.scale_factor = int(np.log2(scale_factor))
    modules_body = []
    for i in range(self.scale_factor):
        modules_body.append(Up(in_channels, chan_factor))
        in_channels = int(in_channels // chan_factor)
    self.body = nn.Sequential(*modules_body)

class MRB(nn.Module):

    def __init__(self, n_feat, height, width, chan_factor, bias, groups):
        super(MRB, self).__init__()
        self.n_feat, self.height, self.width = (n_feat, height, width)
        self.dau_top = RCB(int(n_feat * chan_factor ** 0), bias=bias, groups=groups)
        self.dau_mid = RCB(int(n_feat * chan_factor ** 1), bias=bias, groups=groups)
        self.dau_bot = RCB(int(n_feat * chan_factor ** 2), bias=bias, groups=groups)
        self.down2 = DownSample(int(chan_factor ** 0 * n_feat), 2, chan_factor)
        self.down4 = nn.Sequential(DownSample(int(chan_factor ** 0 * n_feat), 2, chan_factor), DownSample(int(chan_factor ** 1 * n_feat), 2, chan_factor))
        self.up21_1 = UpSample(int(chan_factor ** 1 * n_feat), 2, chan_factor)
        self.up21_2 = UpSample(int(chan_factor ** 1 * n_feat), 2, chan_factor)
        self.up32_1 = UpSample(int(chan_factor ** 2 * n_feat), 2, chan_factor)
        self.up32_2 = UpSample(int(chan_factor ** 2 * n_feat), 2, chan_factor)
        self.conv_out = nn.Conv2d(n_feat, n_feat, kernel_size=1, padding=0, bias=bias)
        self.skff_top = SKFF(int(n_feat * chan_factor ** 0), 2)
        self.skff_mid = SKFF(int(n_feat * chan_factor ** 1), 2)

    def forward(self, x):
        x_top = x.clone()
        x_mid = self.down2(x_top)
        x_bot = self.down4(x_top)
        x_top = self.dau_top(x_top)
        x_mid = self.dau_mid(x_mid)
        x_bot = self.dau_bot(x_bot)
        x_mid = self.skff_mid([x_mid, self.up32_1(x_bot)])
        x_top = self.skff_top([x_top, self.up21_1(x_mid)])
        x_top = self.dau_top(x_top)
        x_mid = self.dau_mid(x_mid)
        x_bot = self.dau_bot(x_bot)
        x_mid = self.skff_mid([x_mid, self.up32_2(x_bot)])
        x_top = self.skff_top([x_top, self.up21_2(x_mid)])
        out = self.conv_out(x_top)
        out = out + x
        return out

def __init__(self, n_feat, height, width, chan_factor, bias, groups):
    super(MRB, self).__init__()
    self.n_feat, self.height, self.width = (n_feat, height, width)
    self.dau_top = RCB(int(n_feat * chan_factor ** 0), bias=bias, groups=groups)
    self.dau_mid = RCB(int(n_feat * chan_factor ** 1), bias=bias, groups=groups)
    self.dau_bot = RCB(int(n_feat * chan_factor ** 2), bias=bias, groups=groups)
    self.down2 = DownSample(int(chan_factor ** 0 * n_feat), 2, chan_factor)
    self.down4 = nn.Sequential(DownSample(int(chan_factor ** 0 * n_feat), 2, chan_factor), DownSample(int(chan_factor ** 1 * n_feat), 2, chan_factor))
    self.up21_1 = UpSample(int(chan_factor ** 1 * n_feat), 2, chan_factor)
    self.up21_2 = UpSample(int(chan_factor ** 1 * n_feat), 2, chan_factor)
    self.up32_1 = UpSample(int(chan_factor ** 2 * n_feat), 2, chan_factor)
    self.up32_2 = UpSample(int(chan_factor ** 2 * n_feat), 2, chan_factor)
    self.conv_out = nn.Conv2d(n_feat, n_feat, kernel_size=1, padding=0, bias=bias)
    self.skff_top = SKFF(int(n_feat * chan_factor ** 0), 2)
    self.skff_mid = SKFF(int(n_feat * chan_factor ** 1), 2)

class RRG(nn.Module):

    def __init__(self, n_feat, n_MRB, height, width, chan_factor, bias=False, groups=1):
        super(RRG, self).__init__()
        modules_body = [MRB(n_feat, height, width, chan_factor, bias, groups) for _ in range(n_MRB)]
        modules_body.append(nn.Conv2d(n_feat, n_feat, kernel_size=3, stride=1, padding=1, bias=bias))
        self.body = nn.Sequential(*modules_body)

    def forward(self, x):
        res = self.body(x)
        res += x
        return res

def __init__(self, n_feat, n_MRB, height, width, chan_factor, bias=False, groups=1):
    super(RRG, self).__init__()
    modules_body = [MRB(n_feat, height, width, chan_factor, bias, groups) for _ in range(n_MRB)]
    modules_body.append(nn.Conv2d(n_feat, n_feat, kernel_size=3, stride=1, padding=1, bias=bias))
    self.body = nn.Sequential(*modules_body)

class MIRNet_v2(nn.Module):

    def __init__(self, inp_channels=3, out_channels=3, n_feat=80, chan_factor=1.5, n_RRG=4, n_MRB=2, height=3, width=2, scale=1, bias=False, task=None):
        super(MIRNet_v2, self).__init__()
        kernel_size = 3
        self.task = task
        self.conv_in = nn.Conv2d(inp_channels, n_feat, kernel_size=3, padding=1, bias=bias)
        modules_body = []
        modules_body.append(RRG(n_feat, n_MRB, height, width, chan_factor, bias, groups=1))
        modules_body.append(RRG(n_feat, n_MRB, height, width, chan_factor, bias, groups=2))
        modules_body.append(RRG(n_feat, n_MRB, height, width, chan_factor, bias, groups=4))
        modules_body.append(RRG(n_feat, n_MRB, height, width, chan_factor, bias, groups=4))
        self.body = nn.Sequential(*modules_body)
        self.conv_out = nn.Conv2d(n_feat, out_channels, kernel_size=3, padding=1, bias=bias)

    def forward(self, inp_img):
        shallow_feats = self.conv_in(inp_img)
        deep_feats = self.body(shallow_feats)
        if self.task == 'defocus_deblurring':
            deep_feats += shallow_feats
            out_img = self.conv_out(deep_feats)
        else:
            out_img = self.conv_out(deep_feats)
            out_img += inp_img
        return out_img

def __init__(self, inp_channels=3, out_channels=3, n_feat=80, chan_factor=1.5, n_RRG=4, n_MRB=2, height=3, width=2, scale=1, bias=False, task=None):
    super(MIRNet_v2, self).__init__()
    kernel_size = 3
    self.task = task
    self.conv_in = nn.Conv2d(inp_channels, n_feat, kernel_size=3, padding=1, bias=bias)
    modules_body = []
    modules_body.append(RRG(n_feat, n_MRB, height, width, chan_factor, bias, groups=1))
    modules_body.append(RRG(n_feat, n_MRB, height, width, chan_factor, bias, groups=2))
    modules_body.append(RRG(n_feat, n_MRB, height, width, chan_factor, bias, groups=4))
    modules_body.append(RRG(n_feat, n_MRB, height, width, chan_factor, bias, groups=4))
    self.body = nn.Sequential(*modules_body)
    self.conv_out = nn.Conv2d(n_feat, out_channels, kernel_size=3, padding=1, bias=bias)

class ResidualBlockNoBN(nn.Module):
    """Residual block without BN.

    It has a style of:
        ---Conv-ReLU-Conv-+-
         |________________|

    Args:
        num_feat (int): Channel number of intermediate features.
            Default: 64.
        res_scale (float): Residual scale. Default: 1.
        pytorch_init (bool): If set to True, use pytorch default init,
            otherwise, use default_init_weights. Default: False.
    """

    def __init__(self, num_feat=64, res_scale=1, pytorch_init=False):
        super(ResidualBlockNoBN, self).__init__()
        self.res_scale = res_scale
        self.conv1 = nn.Conv2d(num_feat, num_feat, 3, 1, 1, bias=True)
        self.conv2 = nn.Conv2d(num_feat, num_feat, 3, 1, 1, bias=True)
        self.relu = nn.ReLU(inplace=True)
        if not pytorch_init:
            default_init_weights([self.conv1, self.conv2], 0.1)

    def forward(self, x):
        identity = x
        out = self.conv2(self.relu(self.conv1(x)))
        return identity + out * self.res_scale

def __init__(self, num_feat=64, res_scale=1, pytorch_init=False):
    super(ResidualBlockNoBN, self).__init__()
    self.res_scale = res_scale
    self.conv1 = nn.Conv2d(num_feat, num_feat, 3, 1, 1, bias=True)
    self.conv2 = nn.Conv2d(num_feat, num_feat, 3, 1, 1, bias=True)
    self.relu = nn.ReLU(inplace=True)
    if not pytorch_init:
        default_init_weights([self.conv1, self.conv2], 0.1)

class Upsample(nn.Sequential):
    """Upsample module.

    Args:
        scale (int): Scale factor. Supported scales: 2^n and 3.
        num_feat (int): Channel number of intermediate features.
    """

    def __init__(self, scale, num_feat):
        m = []
        if scale & scale - 1 == 0:
            for _ in range(int(math.log(scale, 2))):
                m.append(nn.Conv2d(num_feat, 4 * num_feat, 3, 1, 1))
                m.append(nn.PixelShuffle(2))
        elif scale == 3:
            m.append(nn.Conv2d(num_feat, 9 * num_feat, 3, 1, 1))
            m.append(nn.PixelShuffle(3))
        else:
            raise ValueError(f'scale {scale} is not supported. Supported scales: 2^n and 3.')
        super(Upsample, self).__init__(*m)

def __init__(self, scale, num_feat):
    m = []
    if scale & scale - 1 == 0:
        for _ in range(int(math.log(scale, 2))):
            m.append(nn.Conv2d(num_feat, 4 * num_feat, 3, 1, 1))
            m.append(nn.PixelShuffle(2))
    elif scale == 3:
        m.append(nn.Conv2d(num_feat, 9 * num_feat, 3, 1, 1))
        m.append(nn.PixelShuffle(3))
    else:
        raise ValueError(f'scale {scale} is not supported. Supported scales: 2^n and 3.')
    super(Upsample, self).__init__(*m)

