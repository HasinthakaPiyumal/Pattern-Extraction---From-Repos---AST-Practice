# Cluster 0

@LOSSES.register_module()
class CrossEntropyLoss(nn.Module):

    def __init__(self, weight=None, size_average=None, reduce=None, reduction='mean', label_smoothing=0.0, loss_weight=1.0, ignore_index=255):
        super(CrossEntropyLoss, self).__init__()
        self.loss_weight = loss_weight
        self.loss = nn.CrossEntropyLoss(weight=weight, size_average=size_average, ignore_index=ignore_index, reduce=reduce, reduction=reduction, label_smoothing=label_smoothing)

    def forward(self, pred, target):
        return self.loss(pred, target) * self.loss_weight

def __init__(self, weight=None, size_average=None, reduce=None, reduction='mean', label_smoothing=0.0, loss_weight=1.0, ignore_index=255):
    super(CrossEntropyLoss, self).__init__()
    self.loss_weight = loss_weight
    self.loss = nn.CrossEntropyLoss(weight=weight, size_average=size_average, ignore_index=ignore_index, reduce=reduce, reduction=reduction, label_smoothing=label_smoothing)

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

def __init__(self, smoothing_ratio=0.1):
    super(SmoothCELoss, self).__init__()
    self.smoothing_ratio = smoothing_ratio

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

@SCHEDULERS.register_module()
class MultiStepLR(lr_scheduler.MultiStepLR):

    def __init__(self, optimizer, milestones, total_steps, gamma=0.1, last_epoch=-1, verbose=False):
        super().__init__(optimizer=optimizer, milestones=[rate * total_steps for rate in milestones], gamma=gamma, last_epoch=last_epoch, verbose=verbose)

def __init__(self, optimizer, milestones, total_steps, gamma=0.1, last_epoch=-1, verbose=False):
    super().__init__(optimizer=optimizer, milestones=[rate * total_steps for rate in milestones], gamma=gamma, last_epoch=last_epoch, verbose=verbose)

@SCHEDULERS.register_module()
class MultiStepWithWarmupLR(lr_scheduler.LambdaLR):

    def __init__(self, optimizer, milestones, total_steps, gamma=0.1, warmup_rate=0.05, warmup_scale=1e-06, last_epoch=-1, verbose=False):
        milestones = [rate * total_steps for rate in milestones]

        def multi_step_with_warmup(s):
            factor = 1.0
            for i in range(len(milestones)):
                if s < milestones[i]:
                    break
                factor *= gamma
            if s <= warmup_rate * total_steps:
                warmup_coefficient = 1 - (1 - s / warmup_rate / total_steps) * (1 - warmup_scale)
            else:
                warmup_coefficient = 1.0
            return warmup_coefficient * factor
        super().__init__(optimizer=optimizer, lr_lambda=multi_step_with_warmup, last_epoch=last_epoch, verbose=verbose)

def __init__(self, optimizer, milestones, total_steps, gamma=0.1, warmup_rate=0.05, warmup_scale=1e-06, last_epoch=-1, verbose=False):
    milestones = [rate * total_steps for rate in milestones]

    def multi_step_with_warmup(s):
        factor = 1.0
        for i in range(len(milestones)):
            if s < milestones[i]:
                break
            factor *= gamma
        if s <= warmup_rate * total_steps:
            warmup_coefficient = 1 - (1 - s / warmup_rate / total_steps) * (1 - warmup_scale)
        else:
            warmup_coefficient = 1.0
        return warmup_coefficient * factor
    super().__init__(optimizer=optimizer, lr_lambda=multi_step_with_warmup, last_epoch=last_epoch, verbose=verbose)

@SCHEDULERS.register_module()
class PolyLR(lr_scheduler.LambdaLR):

    def __init__(self, optimizer, total_steps, power=0.9, last_epoch=-1, verbose=False):
        super().__init__(optimizer=optimizer, lr_lambda=lambda s: (1 - s / (total_steps + 1)) ** power, last_epoch=last_epoch, verbose=verbose)

def __init__(self, optimizer, total_steps, power=0.9, last_epoch=-1, verbose=False):
    super().__init__(optimizer=optimizer, lr_lambda=lambda s: (1 - s / (total_steps + 1)) ** power, last_epoch=last_epoch, verbose=verbose)

@SCHEDULERS.register_module()
class ExpLR(lr_scheduler.LambdaLR):

    def __init__(self, optimizer, total_steps, gamma=0.9, last_epoch=-1, verbose=False):
        super().__init__(optimizer=optimizer, lr_lambda=lambda s: gamma ** (s / total_steps), last_epoch=last_epoch, verbose=verbose)

def __init__(self, optimizer, total_steps, gamma=0.9, last_epoch=-1, verbose=False):
    super().__init__(optimizer=optimizer, lr_lambda=lambda s: gamma ** (s / total_steps), last_epoch=last_epoch, verbose=verbose)

@SCHEDULERS.register_module()
class CosineAnnealingLR(lr_scheduler.CosineAnnealingLR):

    def __init__(self, optimizer, total_steps, eta_min=0, last_epoch=-1, verbose=False):
        super().__init__(optimizer=optimizer, T_max=total_steps, eta_min=eta_min, last_epoch=last_epoch, verbose=verbose)

def __init__(self, optimizer, total_steps, eta_min=0, last_epoch=-1, verbose=False):
    super().__init__(optimizer=optimizer, T_max=total_steps, eta_min=eta_min, last_epoch=last_epoch, verbose=verbose)

@SCHEDULERS.register_module()
class OneCycleLR(lr_scheduler.OneCycleLR):
    """
    torch.optim.lr_scheduler.OneCycleLR, Block total_steps
    """

    def __init__(self, optimizer, max_lr, total_steps=None, pct_start=0.3, anneal_strategy='cos', cycle_momentum=True, base_momentum=0.85, max_momentum=0.95, div_factor=25.0, final_div_factor=10000.0, three_phase=False, last_epoch=-1, verbose=False):
        super().__init__(optimizer=optimizer, max_lr=max_lr, total_steps=total_steps, pct_start=pct_start, anneal_strategy=anneal_strategy, cycle_momentum=cycle_momentum, base_momentum=base_momentum, max_momentum=max_momentum, div_factor=div_factor, final_div_factor=final_div_factor, three_phase=three_phase, last_epoch=last_epoch, verbose=verbose)

def __init__(self, optimizer, max_lr, total_steps=None, pct_start=0.3, anneal_strategy='cos', cycle_momentum=True, base_momentum=0.85, max_momentum=0.95, div_factor=25.0, final_div_factor=10000.0, three_phase=False, last_epoch=-1, verbose=False):
    super().__init__(optimizer=optimizer, max_lr=max_lr, total_steps=total_steps, pct_start=pct_start, anneal_strategy=anneal_strategy, cycle_momentum=cycle_momentum, base_momentum=base_momentum, max_momentum=max_momentum, div_factor=div_factor, final_div_factor=final_div_factor, three_phase=three_phase, last_epoch=last_epoch, verbose=verbose)

class ConfigDict(Dict):

    def __missing__(self, name):
        raise KeyError(name)

    def __getattr__(self, name):
        try:
            value = super(ConfigDict, self).__getattr__(name)
        except KeyError:
            ex = AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        except Exception as e:
            ex = e
        else:
            return value
        raise ex

def __getattr__(self, name):
    try:
        value = super(ConfigDict, self).__getattr__(name)
    except KeyError:
        ex = AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    except Exception as e:
        ex = e
    else:
        return value
    raise ex

class _ColorfulFormatter(logging.Formatter):

    def __init__(self, *args, **kwargs):
        self._root_name = kwargs.pop('root_name') + '.'
        super(_ColorfulFormatter, self).__init__(*args, **kwargs)

    def formatMessage(self, record):
        log = super(_ColorfulFormatter, self).formatMessage(record)
        if record.levelno == logging.WARNING:
            prefix = colored('WARNING', 'red', attrs=['blink'])
        elif record.levelno == logging.ERROR or record.levelno == logging.CRITICAL:
            prefix = colored('ERROR', 'red', attrs=['blink', 'underline'])
        else:
            return log
        return prefix + ' ' + log

def __init__(self, *args, **kwargs):
    self._root_name = kwargs.pop('root_name') + '.'
    super(_ColorfulFormatter, self).__init__(*args, **kwargs)

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

def build_scaler(self):
    scaler = torch.cuda.amp.GradScaler() if self.cfg.enable_amp else None
    return scaler

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

def __init__(self, twin_keys=('coord', 'normal', 'color'), twin_trans_cfg=None):
    self.twin_keys = twin_keys
    self.twin_trans = Compose(twin_trans_cfg)

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

def __init__(self, twin_keys=('coord', 'normal', 'color'), twin_trans_cfg=None):
    self.twin_keys = twin_keys
    self.twin_trans = Compose(twin_trans_cfg)

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

@DATASETS.register_module()
class ConcatDataset(Dataset):

    def __init__(self, datasets, loop=1):
        super(ConcatDataset, self).__init__()
        self.datasets = [build_dataset(dataset) for dataset in datasets]
        self.loop = loop
        self.data_list = self.get_data_list()
        logger = get_root_logger()
        logger.info('Totally {} x {} samples in the concat set.'.format(len(self.data_list), self.loop))

    def get_data_list(self):
        data_list = []
        for i in range(len(self.datasets)):
            data_list.extend(zip(np.ones(len(self.datasets[i]), dtype=np.long) * i, np.arange(len(self.datasets[i]))))
        return data_list

    def get_data(self, idx):
        dataset_idx, data_idx = self.data_list[idx % len(self.data_list)]
        return self.datasets[dataset_idx][data_idx]

    def get_data_name(self, idx):
        dataset_idx, data_idx = self.data_list[idx % len(self.data_list)]
        return self.datasets[dataset_idx].get_data_name(data_idx)

    def __getitem__(self, idx):
        return self.get_data(idx)

    def __len__(self):
        return len(self.data_list) * self.loop

def __init__(self, datasets, loop=1):
    super(ConcatDataset, self).__init__()
    self.datasets = [build_dataset(dataset) for dataset in datasets]
    self.loop = loop
    self.data_list = self.get_data_list()
    logger = get_root_logger()
    logger.info('Totally {} x {} samples in the concat set.'.format(len(self.data_list), self.loop))

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

@DATASETS.register_module()
class ModelNetDataset(Dataset):

    def __init__(self, split='train', data_root='data/modelnet40_normal_resampled', class_names=None, transform=None, cache_data=False, test_mode=False, test_cfg=None, loop=1):
        super(ModelNetDataset, self).__init__()
        self.data_root = data_root
        self.class_names = dict(zip(class_names, range(len(class_names))))
        self.split = split
        self.cache_data = cache_data
        self.transform = Compose(transform)
        self.loop = loop if not test_mode else 1
        self.test_mode = test_mode
        self.test_cfg = test_cfg if test_mode else None
        self.cache = {}
        if test_mode:
            pass
        self.data_list = [line.rstrip() for line in open(os.path.join(self.data_root, 'modelnet40_{}.txt'.format(self.split)))]
        logger = get_root_logger()
        logger.info('Totally {} x {} samples in {} set.'.format(len(self.data_idx), self.loop, split))

    def prepare_train_data(self, idx):
        data_idx = idx % len(self.data_list)
        if self.cache_data:
            coord, norm, label = self.cache[data_idx]
        else:
            data_shape = '_'.join(self.data_list[data_idx].split('_')[0:-1])
            data_path = os.path.join(self.data_root, data_shape, self.data_list[data_idx] + '.txt')
            data = np.loadtxt(data_path, delimiter=',').astype(np.float32)
            coord, norm = (data[:, 0:3], data[:, 3:6])
            label = np.array([self.class_names[data_shape]])
            if self.cache_data:
                self.cache[data_idx] = (coord, norm, label)
        data_dict = dict(coord=coord, norm=norm, label=label)
        data_dict = self.transform(data_dict)
        return data_dict

    def prepare_test_data(self, idx):
        assert idx < len(self.data_idx)
        data_idx = idx
        data_shape = '_'.join(self.data_list[data_idx].split('_')[0:-1])
        data_path = os.path.join(self.data_root, data_shape, self.data_list[data_idx] + '.txt')
        data = np.loadtxt(data_path, delimiter=',').astype(np.float32)
        coord, norm = (data[:, 0:3], data[:, 3:6])
        label = np.array([self.class_names[data_shape]])
        data_dict = dict(coord=coord, norm=norm, label=label)
        data_dict = self.transform(data_dict)
        return data_dict

    def get_data_name(self, idx):
        data_idx = idx % len(self.data_list)
        return self.data_list[data_idx]

    def __getitem__(self, idx):
        if self.test_mode:
            return self.prepare_test_data(idx)
        else:
            return self.prepare_train_data(idx)

    def __len__(self):
        return len(self.data_idx) * self.loop

def __init__(self, split='train', data_root='data/modelnet40_normal_resampled', class_names=None, transform=None, cache_data=False, test_mode=False, test_cfg=None, loop=1):
    super(ModelNetDataset, self).__init__()
    self.data_root = data_root
    self.class_names = dict(zip(class_names, range(len(class_names))))
    self.split = split
    self.cache_data = cache_data
    self.transform = Compose(transform)
    self.loop = loop if not test_mode else 1
    self.test_mode = test_mode
    self.test_cfg = test_cfg if test_mode else None
    self.cache = {}
    if test_mode:
        pass
    self.data_list = [line.rstrip() for line in open(os.path.join(self.data_root, 'modelnet40_{}.txt'.format(self.split)))]
    logger = get_root_logger()
    logger.info('Totally {} x {} samples in {} set.'.format(len(self.data_idx), self.loop, split))

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

class PlyParseError(Exception):
    """
    Raised when a PLY file cannot be parsed.

    The attributes `element', `row', `property', and `message' give
    additional information.

    """

    def __init__(self, message, element=None, row=None, prop=None):
        self.message = message
        self.element = element
        self.row = row
        self.prop = prop
        s = ''
        if self.element:
            s += 'element %r: ' % self.element.name
        if self.row is not None:
            s += 'row %d: ' % self.row
        if self.prop:
            s += 'property %r: ' % self.prop.name
        s += self.message
        Exception.__init__(self, s)

    def __repr__(self):
        return ('PlyParseError(%r, element=%r, row=%r, prop=%r)' % self.message, self.element, self.row, self.prop)

def __init__(self, message, element=None, row=None, prop=None):
    self.message = message
    self.element = element
    self.row = row
    self.prop = prop
    s = ''
    if self.element:
        s += 'element %r: ' % self.element.name
    if self.row is not None:
        s += 'row %d: ' % self.row
    if self.prop:
        s += 'property %r: ' % self.prop.name
    s += self.message
    Exception.__init__(self, s)

class PlyListProperty(PlyProperty):
    """
    PLY list property description.

    """

    def __init__(self, name, len_dtype, val_dtype):
        PlyProperty.__init__(self, name, val_dtype)
        self.len_dtype = len_dtype

    def _get_len_dtype(self):
        return self._len_dtype

    def _set_len_dtype(self, len_dtype):
        self._len_dtype = _data_types[_lookup_type(len_dtype)]
    len_dtype = property(_get_len_dtype, _set_len_dtype)

    def dtype(self, byte_order='='):
        """
        List properties always have a numpy dtype of "object".

        """
        return '|O'

    def list_dtype(self, byte_order='='):
        """
        Return the pair (len_dtype, val_dtype) (both numpy-friendly
        strings).

        """
        return (byte_order + self.len_dtype, byte_order + self.val_dtype)

    def _from_fields(self, fields):
        len_t, val_t = self.list_dtype()
        n = int(_np.dtype(len_t).type(next(fields)))
        data = _np.loadtxt(list(_islice(fields, n)), val_t, ndmin=1)
        if len(data) < n:
            raise StopIteration
        return data

    def _to_fields(self, data):
        """
        Return generator over the (numerical) PLY representation of the
        list data (length followed by actual data).

        """
        len_t, val_t = self.list_dtype()
        data = _np.asarray(data, dtype=val_t).ravel()
        yield _np.dtype(len_t).type(data.size)
        for x in data:
            yield x

    def _read_bin(self, stream, byte_order):
        len_t, val_t = self.list_dtype(byte_order)
        try:
            n = _np.fromfile(stream, len_t, 1)[0]
        except IndexError:
            raise StopIteration
        data = _np.fromfile(stream, val_t, n)
        if len(data) < n:
            raise StopIteration
        return data

    def _write_bin(self, data, stream, byte_order):
        """
        Write data to a binary stream.

        """
        len_t, val_t = self.list_dtype(byte_order)
        data = _np.asarray(data, dtype=val_t).ravel()
        _np.array(data.size, dtype=len_t).tofile(stream)
        data.tofile(stream)

    def __str__(self):
        len_str = _data_type_reverse[self.len_dtype]
        val_str = _data_type_reverse[self.val_dtype]
        return 'property list %s %s %s' % (len_str, val_str, self.name)

    def __repr__(self):
        return 'PlyListProperty(%r, %r, %r)' % (self.name, _lookup_type(self.len_dtype), _lookup_type(self.val_dtype))

def __init__(self, name, len_dtype, val_dtype):
    PlyProperty.__init__(self, name, val_dtype)
    self.len_dtype = len_dtype

class PointBatchNorm(nn.Module):

    def __init__(self, embed_channels):
        super().__init__()
        self.norm = nn.BatchNorm1d(embed_channels)
        nn.init.constant_(self.norm.weight, 1)
        nn.init.constant_(self.norm.bias, 0)

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        if input.dim() == 3:
            return self.norm(input.transpose(1, 2).contiguous()).transpose(1, 2).contiguous()
        elif input.dim() == 2:
            return self.norm(input)
        else:
            raise NotImplementedError

def __init__(self, embed_channels):
    super().__init__()
    self.norm = nn.BatchNorm1d(embed_channels)
    nn.init.constant_(self.norm.weight, 1)
    nn.init.constant_(self.norm.bias, 0)

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

class PointBatchNorm(nn.Module):
    """
    Batch Normalization for Point Clouds data in shape of [B*N, C], [B*N, L, C]
    """

    def __init__(self, embed_channels):
        super().__init__()
        self.norm = nn.BatchNorm1d(embed_channels)

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        if input.dim() == 3:
            return self.norm(input.transpose(1, 2).contiguous()).transpose(1, 2).contiguous()
        elif input.dim() == 2:
            return self.norm(input)
        else:
            raise NotImplementedError

def __init__(self, embed_channels):
    super().__init__()
    self.norm = nn.BatchNorm1d(embed_channels)

class GroupedVectorAttention(nn.Module):

    def __init__(self, embed_channels, groups, attn_drop_rate=0.0, qkv_bias=True, pe_multiplier=False, pe_bias=True):
        super(GroupedVectorAttention, self).__init__()
        self.embed_channels = embed_channels
        self.groups = groups
        assert embed_channels % groups == 0
        self.attn_drop_rate = attn_drop_rate
        self.qkv_bias = qkv_bias
        self.pe_multiplier = pe_multiplier
        self.pe_bias = pe_bias
        self.linear_q = nn.Sequential(nn.Linear(embed_channels, embed_channels, bias=qkv_bias), PointBatchNorm(embed_channels), nn.ReLU(inplace=True))
        self.linear_k = nn.Sequential(nn.Linear(embed_channels, embed_channels, bias=qkv_bias), PointBatchNorm(embed_channels), nn.ReLU(inplace=True))
        self.linear_v = nn.Linear(embed_channels, embed_channels, bias=qkv_bias)
        if self.pe_multiplier:
            self.linear_p_multiplier = nn.Sequential(nn.Linear(3, embed_channels), PointBatchNorm(embed_channels), nn.ReLU(inplace=True), nn.Linear(embed_channels, embed_channels))
        if self.pe_bias:
            self.linear_p_bias = nn.Sequential(nn.Linear(3, embed_channels), PointBatchNorm(embed_channels), nn.ReLU(inplace=True), nn.Linear(embed_channels, embed_channels))
        self.weight_encoding = nn.Sequential(GroupedLinear(embed_channels, groups, groups), PointBatchNorm(groups), nn.ReLU(inplace=True), nn.Linear(groups, groups))
        self.softmax = nn.Softmax(dim=1)
        self.attn_drop = nn.Dropout(attn_drop_rate)

    def forward(self, feat, coord, reference_index):
        query, key, value = (self.linear_q(feat), self.linear_k(feat), self.linear_v(feat))
        key = pointops.grouping(reference_index, key, coord, with_xyz=True)
        value = pointops.grouping(reference_index, value, coord, with_xyz=False)
        pos, key = (key[:, :, 0:3], key[:, :, 3:])
        relation_qk = key - query.unsqueeze(1)
        if self.pe_multiplier:
            pem = self.linear_p_multiplier(pos)
            relation_qk = relation_qk * pem
        if self.pe_bias:
            peb = self.linear_p_bias(pos)
            relation_qk = relation_qk + peb
            value = value + peb
        weight = self.weight_encoding(relation_qk)
        weight = self.attn_drop(self.softmax(weight))
        mask = torch.sign(reference_index + 1)
        weight = torch.einsum('n s g, n s -> n s g', weight, mask)
        value = einops.rearrange(value, 'n ns (g i) -> n ns g i', g=self.groups)
        feat = torch.einsum('n s g i, n s g -> n g i', value, weight)
        feat = einops.rearrange(feat, 'n g i -> n (g i)')
        return feat

def __init__(self, embed_channels, groups, attn_drop_rate=0.0, qkv_bias=True, pe_multiplier=False, pe_bias=True):
    super(GroupedVectorAttention, self).__init__()
    self.embed_channels = embed_channels
    self.groups = groups
    assert embed_channels % groups == 0
    self.attn_drop_rate = attn_drop_rate
    self.qkv_bias = qkv_bias
    self.pe_multiplier = pe_multiplier
    self.pe_bias = pe_bias
    self.linear_q = nn.Sequential(nn.Linear(embed_channels, embed_channels, bias=qkv_bias), PointBatchNorm(embed_channels), nn.ReLU(inplace=True))
    self.linear_k = nn.Sequential(nn.Linear(embed_channels, embed_channels, bias=qkv_bias), PointBatchNorm(embed_channels), nn.ReLU(inplace=True))
    self.linear_v = nn.Linear(embed_channels, embed_channels, bias=qkv_bias)
    if self.pe_multiplier:
        self.linear_p_multiplier = nn.Sequential(nn.Linear(3, embed_channels), PointBatchNorm(embed_channels), nn.ReLU(inplace=True), nn.Linear(embed_channels, embed_channels))
    if self.pe_bias:
        self.linear_p_bias = nn.Sequential(nn.Linear(3, embed_channels), PointBatchNorm(embed_channels), nn.ReLU(inplace=True), nn.Linear(embed_channels, embed_channels))
    self.weight_encoding = nn.Sequential(GroupedLinear(embed_channels, groups, groups), PointBatchNorm(groups), nn.ReLU(inplace=True), nn.Linear(groups, groups))
    self.softmax = nn.Softmax(dim=1)
    self.attn_drop = nn.Dropout(attn_drop_rate)

class Block(nn.Module):

    def __init__(self, embed_channels, groups, qkv_bias=True, pe_multiplier=False, pe_bias=True, attn_drop_rate=0.0, drop_path_rate=0.0, enable_checkpoint=False):
        super(Block, self).__init__()
        self.attn = GroupedVectorAttention(embed_channels=embed_channels, groups=groups, qkv_bias=qkv_bias, attn_drop_rate=attn_drop_rate, pe_multiplier=pe_multiplier, pe_bias=pe_bias)
        self.fc1 = nn.Linear(embed_channels, embed_channels, bias=False)
        self.fc3 = nn.Linear(embed_channels, embed_channels, bias=False)
        self.norm1 = PointBatchNorm(embed_channels)
        self.norm2 = PointBatchNorm(embed_channels)
        self.norm3 = PointBatchNorm(embed_channels)
        self.act = nn.ReLU(inplace=True)
        self.enable_checkpoint = enable_checkpoint
        self.drop_path = DropPath(drop_path_rate) if drop_path_rate > 0.0 else nn.Identity()

    def forward(self, points, reference_index):
        coord, feat, offset = points
        identity = feat
        feat = self.act(self.norm1(self.fc1(feat)))
        feat = self.attn(feat, coord, reference_index) if not self.enable_checkpoint else checkpoint(self.attn, feat, coord, reference_index)
        feat = self.act(self.norm2(feat))
        feat = self.norm3(self.fc3(feat))
        feat = identity + self.drop_path(feat)
        feat = self.act(feat)
        return [coord, feat, offset]

def __init__(self, embed_channels, groups, qkv_bias=True, pe_multiplier=False, pe_bias=True, attn_drop_rate=0.0, drop_path_rate=0.0, enable_checkpoint=False):
    super(Block, self).__init__()
    self.attn = GroupedVectorAttention(embed_channels=embed_channels, groups=groups, qkv_bias=qkv_bias, attn_drop_rate=attn_drop_rate, pe_multiplier=pe_multiplier, pe_bias=pe_bias)
    self.fc1 = nn.Linear(embed_channels, embed_channels, bias=False)
    self.fc3 = nn.Linear(embed_channels, embed_channels, bias=False)
    self.norm1 = PointBatchNorm(embed_channels)
    self.norm2 = PointBatchNorm(embed_channels)
    self.norm3 = PointBatchNorm(embed_channels)
    self.act = nn.ReLU(inplace=True)
    self.enable_checkpoint = enable_checkpoint
    self.drop_path = DropPath(drop_path_rate) if drop_path_rate > 0.0 else nn.Identity()

class BlockSequence(nn.Module):

    def __init__(self, depth, embed_channels, groups, neighbours=16, qkv_bias=True, pe_multiplier=False, pe_bias=True, attn_drop_rate=0.0, drop_path_rate=0.0, enable_checkpoint=False):
        super(BlockSequence, self).__init__()
        if isinstance(drop_path_rate, list):
            drop_path_rates = drop_path_rate
            assert len(drop_path_rates) == depth
        elif isinstance(drop_path_rate, float):
            drop_path_rates = [deepcopy(drop_path_rate) for _ in range(depth)]
        else:
            drop_path_rates = [0.0 for _ in range(depth)]
        self.neighbours = neighbours
        self.blocks = nn.ModuleList()
        for i in range(depth):
            block = Block(embed_channels=embed_channels, groups=groups, qkv_bias=qkv_bias, pe_multiplier=pe_multiplier, pe_bias=pe_bias, attn_drop_rate=attn_drop_rate, drop_path_rate=drop_path_rates[i], enable_checkpoint=enable_checkpoint)
            self.blocks.append(block)

    def forward(self, points):
        coord, feat, offset = points
        reference_index, _ = pointops.knn_query(self.neighbours, coord, offset)
        for block in self.blocks:
            points = block(points, reference_index)
        return points

def __init__(self, depth, embed_channels, groups, neighbours=16, qkv_bias=True, pe_multiplier=False, pe_bias=True, attn_drop_rate=0.0, drop_path_rate=0.0, enable_checkpoint=False):
    super(BlockSequence, self).__init__()
    if isinstance(drop_path_rate, list):
        drop_path_rates = drop_path_rate
        assert len(drop_path_rates) == depth
    elif isinstance(drop_path_rate, float):
        drop_path_rates = [deepcopy(drop_path_rate) for _ in range(depth)]
    else:
        drop_path_rates = [0.0 for _ in range(depth)]
    self.neighbours = neighbours
    self.blocks = nn.ModuleList()
    for i in range(depth):
        block = Block(embed_channels=embed_channels, groups=groups, qkv_bias=qkv_bias, pe_multiplier=pe_multiplier, pe_bias=pe_bias, attn_drop_rate=attn_drop_rate, drop_path_rate=drop_path_rates[i], enable_checkpoint=enable_checkpoint)
        self.blocks.append(block)

class GridPool(nn.Module):
    """
    Partition-based Pooling (Grid Pooling)
    """

    def __init__(self, in_channels, out_channels, grid_size, bias=False):
        super(GridPool, self).__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.grid_size = grid_size
        self.fc = nn.Linear(in_channels, out_channels, bias=bias)
        self.norm = PointBatchNorm(out_channels)
        self.act = nn.ReLU(inplace=True)

    def forward(self, points, start=None):
        coord, feat, offset = points
        batch = offset2batch(offset)
        feat = self.act(self.norm(self.fc(feat)))
        start = segment_csr(coord, torch.cat([batch.new_zeros(1), torch.cumsum(batch.bincount(), dim=0)]), reduce='min') if start is None else start
        cluster = voxel_grid(pos=coord - start[batch], size=self.grid_size, batch=batch, start=0)
        unique, cluster, counts = torch.unique(cluster, sorted=True, return_inverse=True, return_counts=True)
        _, sorted_cluster_indices = torch.sort(cluster)
        idx_ptr = torch.cat([counts.new_zeros(1), torch.cumsum(counts, dim=0)])
        coord = segment_csr(coord[sorted_cluster_indices], idx_ptr, reduce='mean')
        feat = segment_csr(feat[sorted_cluster_indices], idx_ptr, reduce='max')
        batch = batch[idx_ptr[:-1]]
        offset = batch2offset(batch)
        return ([coord, feat, offset], cluster)

def __init__(self, in_channels, out_channels, grid_size, bias=False):
    super(GridPool, self).__init__()
    self.in_channels = in_channels
    self.out_channels = out_channels
    self.grid_size = grid_size
    self.fc = nn.Linear(in_channels, out_channels, bias=bias)
    self.norm = PointBatchNorm(out_channels)
    self.act = nn.ReLU(inplace=True)

class UnpoolWithSkip(nn.Module):
    """
    Map Unpooling with skip connection
    """

    def __init__(self, in_channels, skip_channels, out_channels, bias=True, skip=True, backend='map'):
        super(UnpoolWithSkip, self).__init__()
        self.in_channels = in_channels
        self.skip_channels = skip_channels
        self.out_channels = out_channels
        self.skip = skip
        self.backend = backend
        assert self.backend in ['map', 'interp']
        self.proj = nn.Sequential(nn.Linear(in_channels, out_channels, bias=bias), PointBatchNorm(out_channels), nn.ReLU(inplace=True))
        self.proj_skip = nn.Sequential(nn.Linear(skip_channels, out_channels, bias=bias), PointBatchNorm(out_channels), nn.ReLU(inplace=True))

    def forward(self, points, skip_points, cluster=None):
        coord, feat, offset = points
        skip_coord, skip_feat, skip_offset = skip_points
        if self.backend == 'map' and cluster is not None:
            feat = self.proj(feat)[cluster]
        else:
            feat = pointops.interpolation(coord, skip_coord, self.proj(feat), offset, skip_offset)
        if self.skip:
            feat = feat + self.proj_skip(skip_feat)
        return [skip_coord, feat, skip_offset]

def __init__(self, in_channels, skip_channels, out_channels, bias=True, skip=True, backend='map'):
    super(UnpoolWithSkip, self).__init__()
    self.in_channels = in_channels
    self.skip_channels = skip_channels
    self.out_channels = out_channels
    self.skip = skip
    self.backend = backend
    assert self.backend in ['map', 'interp']
    self.proj = nn.Sequential(nn.Linear(in_channels, out_channels, bias=bias), PointBatchNorm(out_channels), nn.ReLU(inplace=True))
    self.proj_skip = nn.Sequential(nn.Linear(skip_channels, out_channels, bias=bias), PointBatchNorm(out_channels), nn.ReLU(inplace=True))

class Encoder(nn.Module):

    def __init__(self, depth, in_channels, embed_channels, groups, grid_size=None, neighbours=16, qkv_bias=True, pe_multiplier=False, pe_bias=True, attn_drop_rate=None, drop_path_rate=None, enable_checkpoint=False):
        super(Encoder, self).__init__()
        self.down = GridPool(in_channels=in_channels, out_channels=embed_channels, grid_size=grid_size)
        self.blocks = BlockSequence(depth=depth, embed_channels=embed_channels, groups=groups, neighbours=neighbours, qkv_bias=qkv_bias, pe_multiplier=pe_multiplier, pe_bias=pe_bias, attn_drop_rate=attn_drop_rate if attn_drop_rate is not None else 0.0, drop_path_rate=drop_path_rate if drop_path_rate is not None else 0.0, enable_checkpoint=enable_checkpoint)

    def forward(self, points):
        points, cluster = self.down(points)
        return (self.blocks(points), cluster)

def __init__(self, depth, in_channels, embed_channels, groups, grid_size=None, neighbours=16, qkv_bias=True, pe_multiplier=False, pe_bias=True, attn_drop_rate=None, drop_path_rate=None, enable_checkpoint=False):
    super(Encoder, self).__init__()
    self.down = GridPool(in_channels=in_channels, out_channels=embed_channels, grid_size=grid_size)
    self.blocks = BlockSequence(depth=depth, embed_channels=embed_channels, groups=groups, neighbours=neighbours, qkv_bias=qkv_bias, pe_multiplier=pe_multiplier, pe_bias=pe_bias, attn_drop_rate=attn_drop_rate if attn_drop_rate is not None else 0.0, drop_path_rate=drop_path_rate if drop_path_rate is not None else 0.0, enable_checkpoint=enable_checkpoint)

class Decoder(nn.Module):

    def __init__(self, in_channels, skip_channels, embed_channels, groups, depth, neighbours=16, qkv_bias=True, pe_multiplier=False, pe_bias=True, attn_drop_rate=None, drop_path_rate=None, enable_checkpoint=False, unpool_backend='map'):
        super(Decoder, self).__init__()
        self.up = UnpoolWithSkip(in_channels=in_channels, out_channels=embed_channels, skip_channels=skip_channels, backend=unpool_backend)
        self.blocks = BlockSequence(depth=depth, embed_channels=embed_channels, groups=groups, neighbours=neighbours, qkv_bias=qkv_bias, pe_multiplier=pe_multiplier, pe_bias=pe_bias, attn_drop_rate=attn_drop_rate if attn_drop_rate is not None else 0.0, drop_path_rate=drop_path_rate if drop_path_rate is not None else 0.0, enable_checkpoint=enable_checkpoint)

    def forward(self, points, skip_points, cluster):
        points = self.up(points, skip_points, cluster)
        return self.blocks(points)

def __init__(self, in_channels, skip_channels, embed_channels, groups, depth, neighbours=16, qkv_bias=True, pe_multiplier=False, pe_bias=True, attn_drop_rate=None, drop_path_rate=None, enable_checkpoint=False, unpool_backend='map'):
    super(Decoder, self).__init__()
    self.up = UnpoolWithSkip(in_channels=in_channels, out_channels=embed_channels, skip_channels=skip_channels, backend=unpool_backend)
    self.blocks = BlockSequence(depth=depth, embed_channels=embed_channels, groups=groups, neighbours=neighbours, qkv_bias=qkv_bias, pe_multiplier=pe_multiplier, pe_bias=pe_bias, attn_drop_rate=attn_drop_rate if attn_drop_rate is not None else 0.0, drop_path_rate=drop_path_rate if drop_path_rate is not None else 0.0, enable_checkpoint=enable_checkpoint)

class GVAPatchEmbed(nn.Module):

    def __init__(self, depth, in_channels, embed_channels, groups, neighbours=16, qkv_bias=True, pe_multiplier=False, pe_bias=True, attn_drop_rate=0.0, drop_path_rate=0.0, enable_checkpoint=False):
        super(GVAPatchEmbed, self).__init__()
        self.in_channels = in_channels
        self.embed_channels = embed_channels
        self.proj = nn.Sequential(nn.Linear(in_channels, embed_channels, bias=False), PointBatchNorm(embed_channels), nn.ReLU(inplace=True))
        self.blocks = BlockSequence(depth=depth, embed_channels=embed_channels, groups=groups, neighbours=neighbours, qkv_bias=qkv_bias, pe_multiplier=pe_multiplier, pe_bias=pe_bias, attn_drop_rate=attn_drop_rate, drop_path_rate=drop_path_rate, enable_checkpoint=enable_checkpoint)

    def forward(self, points):
        coord, feat, offset = points
        feat = self.proj(feat)
        return self.blocks([coord, feat, offset])

def __init__(self, depth, in_channels, embed_channels, groups, neighbours=16, qkv_bias=True, pe_multiplier=False, pe_bias=True, attn_drop_rate=0.0, drop_path_rate=0.0, enable_checkpoint=False):
    super(GVAPatchEmbed, self).__init__()
    self.in_channels = in_channels
    self.embed_channels = embed_channels
    self.proj = nn.Sequential(nn.Linear(in_channels, embed_channels, bias=False), PointBatchNorm(embed_channels), nn.ReLU(inplace=True))
    self.blocks = BlockSequence(depth=depth, embed_channels=embed_channels, groups=groups, neighbours=neighbours, qkv_bias=qkv_bias, pe_multiplier=pe_multiplier, pe_bias=pe_bias, attn_drop_rate=attn_drop_rate, drop_path_rate=drop_path_rate, enable_checkpoint=enable_checkpoint)

@MODELS.register_module('ptv2m1')
class PointTransformerV2(nn.Module):

    def __init__(self, in_channels, num_classes, patch_embed_depth=1, patch_embed_channels=48, patch_embed_groups=6, patch_embed_neighbours=8, enc_depths=(2, 2, 6, 2), enc_channels=(96, 192, 384, 512), enc_groups=(12, 24, 48, 64), enc_neighbours=(16, 16, 16, 16), dec_depths=(1, 1, 1, 1), dec_channels=(48, 96, 192, 384), dec_groups=(6, 12, 24, 48), dec_neighbours=(16, 16, 16, 16), grid_sizes=(0.06, 0.12, 0.24, 0.48), attn_qkv_bias=True, pe_multiplier=False, pe_bias=True, attn_drop_rate=0.0, drop_path_rate=0, enable_checkpoint=False, unpool_backend='map'):
        super(PointTransformerV2, self).__init__()
        self.in_channels = in_channels
        self.num_classes = num_classes
        self.num_stages = len(enc_depths)
        assert self.num_stages == len(dec_depths)
        assert self.num_stages == len(enc_channels)
        assert self.num_stages == len(dec_channels)
        assert self.num_stages == len(enc_groups)
        assert self.num_stages == len(dec_groups)
        assert self.num_stages == len(enc_neighbours)
        assert self.num_stages == len(dec_neighbours)
        assert self.num_stages == len(grid_sizes)
        self.patch_embed = GVAPatchEmbed(in_channels=in_channels, embed_channels=patch_embed_channels, groups=patch_embed_groups, depth=patch_embed_depth, neighbours=patch_embed_neighbours, qkv_bias=attn_qkv_bias, pe_multiplier=pe_multiplier, pe_bias=pe_bias, attn_drop_rate=attn_drop_rate, enable_checkpoint=enable_checkpoint)
        enc_dp_rates = [x.item() for x in torch.linspace(0, drop_path_rate, sum(enc_depths))]
        dec_dp_rates = [x.item() for x in torch.linspace(0, drop_path_rate, sum(dec_depths))]
        enc_channels = [patch_embed_channels] + list(enc_channels)
        dec_channels = list(dec_channels) + [enc_channels[-1]]
        self.enc_stages = nn.ModuleList()
        self.dec_stages = nn.ModuleList()
        for i in range(self.num_stages):
            enc = Encoder(depth=enc_depths[i], in_channels=enc_channels[i], embed_channels=enc_channels[i + 1], groups=enc_groups[i], grid_size=grid_sizes[i], neighbours=enc_neighbours[i], qkv_bias=attn_qkv_bias, pe_multiplier=pe_multiplier, pe_bias=pe_bias, attn_drop_rate=attn_drop_rate, drop_path_rate=enc_dp_rates[sum(enc_depths[:i]):sum(enc_depths[:i + 1])], enable_checkpoint=enable_checkpoint)
            dec = Decoder(depth=dec_depths[i], in_channels=dec_channels[i + 1], skip_channels=enc_channels[i], embed_channels=dec_channels[i], groups=dec_groups[i], neighbours=dec_neighbours[i], qkv_bias=attn_qkv_bias, pe_multiplier=pe_multiplier, pe_bias=pe_bias, attn_drop_rate=attn_drop_rate, drop_path_rate=dec_dp_rates[sum(dec_depths[:i]):sum(dec_depths[:i + 1])], enable_checkpoint=enable_checkpoint, unpool_backend=unpool_backend)
            self.enc_stages.append(enc)
            self.dec_stages.append(dec)
        self.seg_head = nn.Sequential(nn.Linear(dec_channels[0], dec_channels[0]), PointBatchNorm(dec_channels[0]), nn.ReLU(inplace=True), nn.Linear(dec_channels[0], num_classes)) if num_classes > 0 else nn.Identity()

    def forward(self, data_dict):
        coord = data_dict['coord']
        feat = data_dict['feat']
        offset = data_dict['offset'].int()
        points = [coord, feat, offset]
        points = self.patch_embed(points)
        skips = [[points]]
        for i in range(self.num_stages):
            points, cluster = self.enc_stages[i](points)
            skips[-1].append(cluster)
            skips.append([points])
        points = skips.pop(-1)[0]
        for i in reversed(range(self.num_stages)):
            skip_points, cluster = skips.pop(-1)
            points = self.dec_stages[i](points, skip_points, cluster)
        coord, feat, offset = points
        seg_logits = self.seg_head(feat)
        return seg_logits

def __init__(self, in_channels, num_classes, patch_embed_depth=1, patch_embed_channels=48, patch_embed_groups=6, patch_embed_neighbours=8, enc_depths=(2, 2, 6, 2), enc_channels=(96, 192, 384, 512), enc_groups=(12, 24, 48, 64), enc_neighbours=(16, 16, 16, 16), dec_depths=(1, 1, 1, 1), dec_channels=(48, 96, 192, 384), dec_groups=(6, 12, 24, 48), dec_neighbours=(16, 16, 16, 16), grid_sizes=(0.06, 0.12, 0.24, 0.48), attn_qkv_bias=True, pe_multiplier=False, pe_bias=True, attn_drop_rate=0.0, drop_path_rate=0, enable_checkpoint=False, unpool_backend='map'):
    super(PointTransformerV2, self).__init__()
    self.in_channels = in_channels
    self.num_classes = num_classes
    self.num_stages = len(enc_depths)
    assert self.num_stages == len(dec_depths)
    assert self.num_stages == len(enc_channels)
    assert self.num_stages == len(dec_channels)
    assert self.num_stages == len(enc_groups)
    assert self.num_stages == len(dec_groups)
    assert self.num_stages == len(enc_neighbours)
    assert self.num_stages == len(dec_neighbours)
    assert self.num_stages == len(grid_sizes)
    self.patch_embed = GVAPatchEmbed(in_channels=in_channels, embed_channels=patch_embed_channels, groups=patch_embed_groups, depth=patch_embed_depth, neighbours=patch_embed_neighbours, qkv_bias=attn_qkv_bias, pe_multiplier=pe_multiplier, pe_bias=pe_bias, attn_drop_rate=attn_drop_rate, enable_checkpoint=enable_checkpoint)
    enc_dp_rates = [x.item() for x in torch.linspace(0, drop_path_rate, sum(enc_depths))]
    dec_dp_rates = [x.item() for x in torch.linspace(0, drop_path_rate, sum(dec_depths))]
    enc_channels = [patch_embed_channels] + list(enc_channels)
    dec_channels = list(dec_channels) + [enc_channels[-1]]
    self.enc_stages = nn.ModuleList()
    self.dec_stages = nn.ModuleList()
    for i in range(self.num_stages):
        enc = Encoder(depth=enc_depths[i], in_channels=enc_channels[i], embed_channels=enc_channels[i + 1], groups=enc_groups[i], grid_size=grid_sizes[i], neighbours=enc_neighbours[i], qkv_bias=attn_qkv_bias, pe_multiplier=pe_multiplier, pe_bias=pe_bias, attn_drop_rate=attn_drop_rate, drop_path_rate=enc_dp_rates[sum(enc_depths[:i]):sum(enc_depths[:i + 1])], enable_checkpoint=enable_checkpoint)
        dec = Decoder(depth=dec_depths[i], in_channels=dec_channels[i + 1], skip_channels=enc_channels[i], embed_channels=dec_channels[i], groups=dec_groups[i], neighbours=dec_neighbours[i], qkv_bias=attn_qkv_bias, pe_multiplier=pe_multiplier, pe_bias=pe_bias, attn_drop_rate=attn_drop_rate, drop_path_rate=dec_dp_rates[sum(dec_depths[:i]):sum(dec_depths[:i + 1])], enable_checkpoint=enable_checkpoint, unpool_backend=unpool_backend)
        self.enc_stages.append(enc)
        self.dec_stages.append(dec)
    self.seg_head = nn.Sequential(nn.Linear(dec_channels[0], dec_channels[0]), PointBatchNorm(dec_channels[0]), nn.ReLU(inplace=True), nn.Linear(dec_channels[0], num_classes)) if num_classes > 0 else nn.Identity()

class PointBatchNorm(nn.Module):
    """
    Batch Normalization for Point Clouds data in shape of [B*N, C], [B*N, L, C]
    """

    def __init__(self, embed_channels):
        super().__init__()
        self.norm = nn.BatchNorm1d(embed_channels)

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        if input.dim() == 3:
            return self.norm(input.transpose(1, 2).contiguous()).transpose(1, 2).contiguous()
        elif input.dim() == 2:
            return self.norm(input)
        else:
            raise NotImplementedError

def __init__(self, embed_channels):
    super().__init__()
    self.norm = nn.BatchNorm1d(embed_channels)

class GroupedVectorAttention(nn.Module):

    def __init__(self, embed_channels, groups, attn_drop_rate=0.0, qkv_bias=True, pe_multiplier=False, pe_bias=True):
        super(GroupedVectorAttention, self).__init__()
        self.embed_channels = embed_channels
        self.groups = groups
        assert embed_channels % groups == 0
        self.attn_drop_rate = attn_drop_rate
        self.qkv_bias = qkv_bias
        self.pe_multiplier = pe_multiplier
        self.pe_bias = pe_bias
        self.linear_q = nn.Sequential(nn.Linear(embed_channels, embed_channels, bias=qkv_bias), PointBatchNorm(embed_channels), nn.ReLU(inplace=True))
        self.linear_k = nn.Sequential(nn.Linear(embed_channels, embed_channels, bias=qkv_bias), PointBatchNorm(embed_channels), nn.ReLU(inplace=True))
        self.linear_v = nn.Linear(embed_channels, embed_channels, bias=qkv_bias)
        if self.pe_multiplier:
            self.linear_p_multiplier = nn.Sequential(nn.Linear(3, embed_channels), PointBatchNorm(embed_channels), nn.ReLU(inplace=True), nn.Linear(embed_channels, embed_channels))
        if self.pe_bias:
            self.linear_p_bias = nn.Sequential(nn.Linear(3, embed_channels), PointBatchNorm(embed_channels), nn.ReLU(inplace=True), nn.Linear(embed_channels, embed_channels))
        self.weight_encoding = nn.Sequential(nn.Linear(embed_channels, groups), PointBatchNorm(groups), nn.ReLU(inplace=True), nn.Linear(groups, groups))
        self.softmax = nn.Softmax(dim=1)
        self.attn_drop = nn.Dropout(attn_drop_rate)

    def forward(self, feat, coord, reference_index):
        query, key, value = (self.linear_q(feat), self.linear_k(feat), self.linear_v(feat))
        key = pointops.grouping(reference_index, key, coord, with_xyz=True)
        value = pointops.grouping(reference_index, value, coord, with_xyz=False)
        pos, key = (key[:, :, 0:3], key[:, :, 3:])
        relation_qk = key - query.unsqueeze(1)
        if self.pe_multiplier:
            pem = self.linear_p_multiplier(pos)
            relation_qk = relation_qk * pem
        if self.pe_bias:
            peb = self.linear_p_bias(pos)
            relation_qk = relation_qk + peb
            value = value + peb
        weight = self.weight_encoding(relation_qk)
        weight = self.attn_drop(self.softmax(weight))
        mask = torch.sign(reference_index + 1)
        weight = torch.einsum('n s g, n s -> n s g', weight, mask)
        value = einops.rearrange(value, 'n ns (g i) -> n ns g i', g=self.groups)
        feat = torch.einsum('n s g i, n s g -> n g i', value, weight)
        feat = einops.rearrange(feat, 'n g i -> n (g i)')
        return feat

def __init__(self, embed_channels, groups, attn_drop_rate=0.0, qkv_bias=True, pe_multiplier=False, pe_bias=True):
    super(GroupedVectorAttention, self).__init__()
    self.embed_channels = embed_channels
    self.groups = groups
    assert embed_channels % groups == 0
    self.attn_drop_rate = attn_drop_rate
    self.qkv_bias = qkv_bias
    self.pe_multiplier = pe_multiplier
    self.pe_bias = pe_bias
    self.linear_q = nn.Sequential(nn.Linear(embed_channels, embed_channels, bias=qkv_bias), PointBatchNorm(embed_channels), nn.ReLU(inplace=True))
    self.linear_k = nn.Sequential(nn.Linear(embed_channels, embed_channels, bias=qkv_bias), PointBatchNorm(embed_channels), nn.ReLU(inplace=True))
    self.linear_v = nn.Linear(embed_channels, embed_channels, bias=qkv_bias)
    if self.pe_multiplier:
        self.linear_p_multiplier = nn.Sequential(nn.Linear(3, embed_channels), PointBatchNorm(embed_channels), nn.ReLU(inplace=True), nn.Linear(embed_channels, embed_channels))
    if self.pe_bias:
        self.linear_p_bias = nn.Sequential(nn.Linear(3, embed_channels), PointBatchNorm(embed_channels), nn.ReLU(inplace=True), nn.Linear(embed_channels, embed_channels))
    self.weight_encoding = nn.Sequential(nn.Linear(embed_channels, groups), PointBatchNorm(groups), nn.ReLU(inplace=True), nn.Linear(groups, groups))
    self.softmax = nn.Softmax(dim=1)
    self.attn_drop = nn.Dropout(attn_drop_rate)

class Block(nn.Module):

    def __init__(self, embed_channels, groups, qkv_bias=True, pe_multiplier=False, pe_bias=True, attn_drop_rate=0.0, drop_path_rate=0.0, enable_checkpoint=False):
        super(Block, self).__init__()
        self.attn = GroupedVectorAttention(embed_channels=embed_channels, groups=groups, qkv_bias=qkv_bias, attn_drop_rate=attn_drop_rate, pe_multiplier=pe_multiplier, pe_bias=pe_bias)
        self.fc1 = nn.Linear(embed_channels, embed_channels, bias=False)
        self.fc3 = nn.Linear(embed_channels, embed_channels, bias=False)
        self.norm1 = PointBatchNorm(embed_channels)
        self.norm2 = PointBatchNorm(embed_channels)
        self.norm3 = PointBatchNorm(embed_channels)
        self.act = nn.ReLU(inplace=True)
        self.enable_checkpoint = enable_checkpoint
        self.drop_path = DropPath(drop_path_rate) if drop_path_rate > 0.0 else nn.Identity()

    def forward(self, points, reference_index):
        coord, feat, offset = points
        identity = feat
        feat = self.act(self.norm1(self.fc1(feat)))
        feat = self.attn(feat, coord, reference_index) if not self.enable_checkpoint else checkpoint(self.attn, feat, coord, reference_index)
        feat = self.act(self.norm2(feat))
        feat = self.norm3(self.fc3(feat))
        feat = identity + self.drop_path(feat)
        feat = self.act(feat)
        return [coord, feat, offset]

def __init__(self, embed_channels, groups, qkv_bias=True, pe_multiplier=False, pe_bias=True, attn_drop_rate=0.0, drop_path_rate=0.0, enable_checkpoint=False):
    super(Block, self).__init__()
    self.attn = GroupedVectorAttention(embed_channels=embed_channels, groups=groups, qkv_bias=qkv_bias, attn_drop_rate=attn_drop_rate, pe_multiplier=pe_multiplier, pe_bias=pe_bias)
    self.fc1 = nn.Linear(embed_channels, embed_channels, bias=False)
    self.fc3 = nn.Linear(embed_channels, embed_channels, bias=False)
    self.norm1 = PointBatchNorm(embed_channels)
    self.norm2 = PointBatchNorm(embed_channels)
    self.norm3 = PointBatchNorm(embed_channels)
    self.act = nn.ReLU(inplace=True)
    self.enable_checkpoint = enable_checkpoint
    self.drop_path = DropPath(drop_path_rate) if drop_path_rate > 0.0 else nn.Identity()

class BlockSequence(nn.Module):

    def __init__(self, depth, embed_channels, groups, neighbours=16, qkv_bias=True, pe_multiplier=False, pe_bias=True, attn_drop_rate=0.0, drop_path_rate=0.0, enable_checkpoint=False):
        super(BlockSequence, self).__init__()
        if isinstance(drop_path_rate, list):
            drop_path_rates = drop_path_rate
            assert len(drop_path_rates) == depth
        elif isinstance(drop_path_rate, float):
            drop_path_rates = [deepcopy(drop_path_rate) for _ in range(depth)]
        else:
            drop_path_rates = [0.0 for _ in range(depth)]
        self.neighbours = neighbours
        self.blocks = nn.ModuleList()
        for i in range(depth):
            block = Block(embed_channels=embed_channels, groups=groups, qkv_bias=qkv_bias, pe_multiplier=pe_multiplier, pe_bias=pe_bias, attn_drop_rate=attn_drop_rate, drop_path_rate=drop_path_rates[i], enable_checkpoint=enable_checkpoint)
            self.blocks.append(block)

    def forward(self, points):
        coord, feat, offset = points
        reference_index, _ = pointops.knn_query(self.neighbours, coord, offset)
        for block in self.blocks:
            points = block(points, reference_index)
        return points

def __init__(self, depth, embed_channels, groups, neighbours=16, qkv_bias=True, pe_multiplier=False, pe_bias=True, attn_drop_rate=0.0, drop_path_rate=0.0, enable_checkpoint=False):
    super(BlockSequence, self).__init__()
    if isinstance(drop_path_rate, list):
        drop_path_rates = drop_path_rate
        assert len(drop_path_rates) == depth
    elif isinstance(drop_path_rate, float):
        drop_path_rates = [deepcopy(drop_path_rate) for _ in range(depth)]
    else:
        drop_path_rates = [0.0 for _ in range(depth)]
    self.neighbours = neighbours
    self.blocks = nn.ModuleList()
    for i in range(depth):
        block = Block(embed_channels=embed_channels, groups=groups, qkv_bias=qkv_bias, pe_multiplier=pe_multiplier, pe_bias=pe_bias, attn_drop_rate=attn_drop_rate, drop_path_rate=drop_path_rates[i], enable_checkpoint=enable_checkpoint)
        self.blocks.append(block)

class GridPool(nn.Module):
    """
    Partition-based Pooling (Grid Pooling)
    """

    def __init__(self, in_channels, out_channels, grid_size, bias=False):
        super(GridPool, self).__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.grid_size = grid_size
        self.fc = nn.Linear(in_channels, out_channels, bias=bias)
        self.norm = PointBatchNorm(out_channels)
        self.act = nn.ReLU(inplace=True)

    def forward(self, points, start=None):
        coord, feat, offset = points
        batch = offset2batch(offset)
        feat = self.act(self.norm(self.fc(feat)))
        start = segment_csr(coord, torch.cat([batch.new_zeros(1), torch.cumsum(batch.bincount(), dim=0)]), reduce='min') if start is None else start
        cluster = voxel_grid(pos=coord - start[batch], size=self.grid_size, batch=batch, start=0)
        unique, cluster, counts = torch.unique(cluster, sorted=True, return_inverse=True, return_counts=True)
        _, sorted_cluster_indices = torch.sort(cluster)
        idx_ptr = torch.cat([counts.new_zeros(1), torch.cumsum(counts, dim=0)])
        coord = segment_csr(coord[sorted_cluster_indices], idx_ptr, reduce='mean')
        feat = segment_csr(feat[sorted_cluster_indices], idx_ptr, reduce='max')
        batch = batch[idx_ptr[:-1]]
        offset = batch2offset(batch)
        return ([coord, feat, offset], cluster)

def __init__(self, in_channels, out_channels, grid_size, bias=False):
    super(GridPool, self).__init__()
    self.in_channels = in_channels
    self.out_channels = out_channels
    self.grid_size = grid_size
    self.fc = nn.Linear(in_channels, out_channels, bias=bias)
    self.norm = PointBatchNorm(out_channels)
    self.act = nn.ReLU(inplace=True)

class UnpoolWithSkip(nn.Module):
    """
    Map Unpooling with skip connection
    """

    def __init__(self, in_channels, skip_channels, out_channels, bias=True, skip=True, backend='map'):
        super(UnpoolWithSkip, self).__init__()
        self.in_channels = in_channels
        self.skip_channels = skip_channels
        self.out_channels = out_channels
        self.skip = skip
        self.backend = backend
        assert self.backend in ['map', 'interp']
        self.proj = nn.Sequential(nn.Linear(in_channels, out_channels, bias=bias), PointBatchNorm(out_channels), nn.ReLU(inplace=True))
        self.proj_skip = nn.Sequential(nn.Linear(skip_channels, out_channels, bias=bias), PointBatchNorm(out_channels), nn.ReLU(inplace=True))

    def forward(self, points, skip_points, cluster=None):
        coord, feat, offset = points
        skip_coord, skip_feat, skip_offset = skip_points
        if self.backend == 'map' and cluster is not None:
            feat = self.proj(feat)[cluster]
        else:
            feat = pointops.interpolation(coord, skip_coord, self.proj(feat), offset, skip_offset)
        if self.skip:
            feat = feat + self.proj_skip(skip_feat)
        return [skip_coord, feat, skip_offset]

def __init__(self, in_channels, skip_channels, out_channels, bias=True, skip=True, backend='map'):
    super(UnpoolWithSkip, self).__init__()
    self.in_channels = in_channels
    self.skip_channels = skip_channels
    self.out_channels = out_channels
    self.skip = skip
    self.backend = backend
    assert self.backend in ['map', 'interp']
    self.proj = nn.Sequential(nn.Linear(in_channels, out_channels, bias=bias), PointBatchNorm(out_channels), nn.ReLU(inplace=True))
    self.proj_skip = nn.Sequential(nn.Linear(skip_channels, out_channels, bias=bias), PointBatchNorm(out_channels), nn.ReLU(inplace=True))

class Encoder(nn.Module):

    def __init__(self, depth, in_channels, embed_channels, groups, grid_size=None, neighbours=16, qkv_bias=True, pe_multiplier=False, pe_bias=True, attn_drop_rate=None, drop_path_rate=None, enable_checkpoint=False):
        super(Encoder, self).__init__()
        self.down = GridPool(in_channels=in_channels, out_channels=embed_channels, grid_size=grid_size)
        self.blocks = BlockSequence(depth=depth, embed_channels=embed_channels, groups=groups, neighbours=neighbours, qkv_bias=qkv_bias, pe_multiplier=pe_multiplier, pe_bias=pe_bias, attn_drop_rate=attn_drop_rate if attn_drop_rate is not None else 0.0, drop_path_rate=drop_path_rate if drop_path_rate is not None else 0.0, enable_checkpoint=enable_checkpoint)

    def forward(self, points):
        points, cluster = self.down(points)
        return (self.blocks(points), cluster)

def __init__(self, depth, in_channels, embed_channels, groups, grid_size=None, neighbours=16, qkv_bias=True, pe_multiplier=False, pe_bias=True, attn_drop_rate=None, drop_path_rate=None, enable_checkpoint=False):
    super(Encoder, self).__init__()
    self.down = GridPool(in_channels=in_channels, out_channels=embed_channels, grid_size=grid_size)
    self.blocks = BlockSequence(depth=depth, embed_channels=embed_channels, groups=groups, neighbours=neighbours, qkv_bias=qkv_bias, pe_multiplier=pe_multiplier, pe_bias=pe_bias, attn_drop_rate=attn_drop_rate if attn_drop_rate is not None else 0.0, drop_path_rate=drop_path_rate if drop_path_rate is not None else 0.0, enable_checkpoint=enable_checkpoint)

class Decoder(nn.Module):

    def __init__(self, in_channels, skip_channels, embed_channels, groups, depth, neighbours=16, qkv_bias=True, pe_multiplier=False, pe_bias=True, attn_drop_rate=None, drop_path_rate=None, enable_checkpoint=False, unpool_backend='map'):
        super(Decoder, self).__init__()
        self.up = UnpoolWithSkip(in_channels=in_channels, out_channels=embed_channels, skip_channels=skip_channels, backend=unpool_backend)
        self.blocks = BlockSequence(depth=depth, embed_channels=embed_channels, groups=groups, neighbours=neighbours, qkv_bias=qkv_bias, pe_multiplier=pe_multiplier, pe_bias=pe_bias, attn_drop_rate=attn_drop_rate if attn_drop_rate is not None else 0.0, drop_path_rate=drop_path_rate if drop_path_rate is not None else 0.0, enable_checkpoint=enable_checkpoint)

    def forward(self, points, skip_points, cluster):
        points = self.up(points, skip_points, cluster)
        return self.blocks(points)

def __init__(self, in_channels, skip_channels, embed_channels, groups, depth, neighbours=16, qkv_bias=True, pe_multiplier=False, pe_bias=True, attn_drop_rate=None, drop_path_rate=None, enable_checkpoint=False, unpool_backend='map'):
    super(Decoder, self).__init__()
    self.up = UnpoolWithSkip(in_channels=in_channels, out_channels=embed_channels, skip_channels=skip_channels, backend=unpool_backend)
    self.blocks = BlockSequence(depth=depth, embed_channels=embed_channels, groups=groups, neighbours=neighbours, qkv_bias=qkv_bias, pe_multiplier=pe_multiplier, pe_bias=pe_bias, attn_drop_rate=attn_drop_rate if attn_drop_rate is not None else 0.0, drop_path_rate=drop_path_rate if drop_path_rate is not None else 0.0, enable_checkpoint=enable_checkpoint)

class GVAPatchEmbed(nn.Module):

    def __init__(self, depth, in_channels, embed_channels, groups, neighbours=16, qkv_bias=True, pe_multiplier=False, pe_bias=True, attn_drop_rate=0.0, drop_path_rate=0.0, enable_checkpoint=False):
        super(GVAPatchEmbed, self).__init__()
        self.in_channels = in_channels
        self.embed_channels = embed_channels
        self.proj = nn.Sequential(nn.Linear(in_channels, embed_channels, bias=False), PointBatchNorm(embed_channels), nn.ReLU(inplace=True))
        self.blocks = BlockSequence(depth=depth, embed_channels=embed_channels, groups=groups, neighbours=neighbours, qkv_bias=qkv_bias, pe_multiplier=pe_multiplier, pe_bias=pe_bias, attn_drop_rate=attn_drop_rate, drop_path_rate=drop_path_rate, enable_checkpoint=enable_checkpoint)

    def forward(self, points):
        coord, feat, offset = points
        feat = self.proj(feat)
        return self.blocks([coord, feat, offset])

def __init__(self, depth, in_channels, embed_channels, groups, neighbours=16, qkv_bias=True, pe_multiplier=False, pe_bias=True, attn_drop_rate=0.0, drop_path_rate=0.0, enable_checkpoint=False):
    super(GVAPatchEmbed, self).__init__()
    self.in_channels = in_channels
    self.embed_channels = embed_channels
    self.proj = nn.Sequential(nn.Linear(in_channels, embed_channels, bias=False), PointBatchNorm(embed_channels), nn.ReLU(inplace=True))
    self.blocks = BlockSequence(depth=depth, embed_channels=embed_channels, groups=groups, neighbours=neighbours, qkv_bias=qkv_bias, pe_multiplier=pe_multiplier, pe_bias=pe_bias, attn_drop_rate=attn_drop_rate, drop_path_rate=drop_path_rate, enable_checkpoint=enable_checkpoint)

@MODELS.register_module('ptv2m2')
class PointTransformerV2(nn.Module):

    def __init__(self, in_channels, num_classes, patch_embed_depth=1, patch_embed_channels=48, patch_embed_groups=6, patch_embed_neighbours=8, enc_depths=(2, 2, 6, 2), enc_channels=(96, 192, 384, 512), enc_groups=(12, 24, 48, 64), enc_neighbours=(16, 16, 16, 16), dec_depths=(1, 1, 1, 1), dec_channels=(48, 96, 192, 384), dec_groups=(6, 12, 24, 48), dec_neighbours=(16, 16, 16, 16), grid_sizes=(0.06, 0.12, 0.24, 0.48), attn_qkv_bias=True, pe_multiplier=False, pe_bias=True, attn_drop_rate=0.0, drop_path_rate=0, enable_checkpoint=False, unpool_backend='map'):
        super(PointTransformerV2, self).__init__()
        self.in_channels = in_channels
        self.num_classes = num_classes
        self.num_stages = len(enc_depths)
        assert self.num_stages == len(dec_depths)
        assert self.num_stages == len(enc_channels)
        assert self.num_stages == len(dec_channels)
        assert self.num_stages == len(enc_groups)
        assert self.num_stages == len(dec_groups)
        assert self.num_stages == len(enc_neighbours)
        assert self.num_stages == len(dec_neighbours)
        assert self.num_stages == len(grid_sizes)
        self.patch_embed = GVAPatchEmbed(in_channels=in_channels, embed_channels=patch_embed_channels, groups=patch_embed_groups, depth=patch_embed_depth, neighbours=patch_embed_neighbours, qkv_bias=attn_qkv_bias, pe_multiplier=pe_multiplier, pe_bias=pe_bias, attn_drop_rate=attn_drop_rate, enable_checkpoint=enable_checkpoint)
        enc_dp_rates = [x.item() for x in torch.linspace(0, drop_path_rate, sum(enc_depths))]
        dec_dp_rates = [x.item() for x in torch.linspace(0, drop_path_rate, sum(dec_depths))]
        enc_channels = [patch_embed_channels] + list(enc_channels)
        dec_channels = list(dec_channels) + [enc_channels[-1]]
        self.enc_stages = nn.ModuleList()
        self.dec_stages = nn.ModuleList()
        for i in range(self.num_stages):
            enc = Encoder(depth=enc_depths[i], in_channels=enc_channels[i], embed_channels=enc_channels[i + 1], groups=enc_groups[i], grid_size=grid_sizes[i], neighbours=enc_neighbours[i], qkv_bias=attn_qkv_bias, pe_multiplier=pe_multiplier, pe_bias=pe_bias, attn_drop_rate=attn_drop_rate, drop_path_rate=enc_dp_rates[sum(enc_depths[:i]):sum(enc_depths[:i + 1])], enable_checkpoint=enable_checkpoint)
            dec = Decoder(depth=dec_depths[i], in_channels=dec_channels[i + 1], skip_channels=enc_channels[i], embed_channels=dec_channels[i], groups=dec_groups[i], neighbours=dec_neighbours[i], qkv_bias=attn_qkv_bias, pe_multiplier=pe_multiplier, pe_bias=pe_bias, attn_drop_rate=attn_drop_rate, drop_path_rate=dec_dp_rates[sum(dec_depths[:i]):sum(dec_depths[:i + 1])], enable_checkpoint=enable_checkpoint, unpool_backend=unpool_backend)
            self.enc_stages.append(enc)
            self.dec_stages.append(dec)
        self.seg_head = nn.Sequential(nn.Linear(dec_channels[0], dec_channels[0]), PointBatchNorm(dec_channels[0]), nn.ReLU(inplace=True), nn.Linear(dec_channels[0], num_classes)) if num_classes > 0 else nn.Identity()

    def forward(self, data_dict):
        coord = data_dict['coord']
        feat = data_dict['feat']
        offset = data_dict['offset'].int()
        points = [coord, feat, offset]
        points = self.patch_embed(points)
        skips = [[points]]
        for i in range(self.num_stages):
            points, cluster = self.enc_stages[i](points)
            skips[-1].append(cluster)
            skips.append([points])
        points = skips.pop(-1)[0]
        for i in reversed(range(self.num_stages)):
            skip_points, cluster = skips.pop(-1)
            points = self.dec_stages[i](points, skip_points, cluster)
        coord, feat, offset = points
        seg_logits = self.seg_head(feat)
        return seg_logits

def __init__(self, in_channels, num_classes, patch_embed_depth=1, patch_embed_channels=48, patch_embed_groups=6, patch_embed_neighbours=8, enc_depths=(2, 2, 6, 2), enc_channels=(96, 192, 384, 512), enc_groups=(12, 24, 48, 64), enc_neighbours=(16, 16, 16, 16), dec_depths=(1, 1, 1, 1), dec_channels=(48, 96, 192, 384), dec_groups=(6, 12, 24, 48), dec_neighbours=(16, 16, 16, 16), grid_sizes=(0.06, 0.12, 0.24, 0.48), attn_qkv_bias=True, pe_multiplier=False, pe_bias=True, attn_drop_rate=0.0, drop_path_rate=0, enable_checkpoint=False, unpool_backend='map'):
    super(PointTransformerV2, self).__init__()
    self.in_channels = in_channels
    self.num_classes = num_classes
    self.num_stages = len(enc_depths)
    assert self.num_stages == len(dec_depths)
    assert self.num_stages == len(enc_channels)
    assert self.num_stages == len(dec_channels)
    assert self.num_stages == len(enc_groups)
    assert self.num_stages == len(dec_groups)
    assert self.num_stages == len(enc_neighbours)
    assert self.num_stages == len(dec_neighbours)
    assert self.num_stages == len(grid_sizes)
    self.patch_embed = GVAPatchEmbed(in_channels=in_channels, embed_channels=patch_embed_channels, groups=patch_embed_groups, depth=patch_embed_depth, neighbours=patch_embed_neighbours, qkv_bias=attn_qkv_bias, pe_multiplier=pe_multiplier, pe_bias=pe_bias, attn_drop_rate=attn_drop_rate, enable_checkpoint=enable_checkpoint)
    enc_dp_rates = [x.item() for x in torch.linspace(0, drop_path_rate, sum(enc_depths))]
    dec_dp_rates = [x.item() for x in torch.linspace(0, drop_path_rate, sum(dec_depths))]
    enc_channels = [patch_embed_channels] + list(enc_channels)
    dec_channels = list(dec_channels) + [enc_channels[-1]]
    self.enc_stages = nn.ModuleList()
    self.dec_stages = nn.ModuleList()
    for i in range(self.num_stages):
        enc = Encoder(depth=enc_depths[i], in_channels=enc_channels[i], embed_channels=enc_channels[i + 1], groups=enc_groups[i], grid_size=grid_sizes[i], neighbours=enc_neighbours[i], qkv_bias=attn_qkv_bias, pe_multiplier=pe_multiplier, pe_bias=pe_bias, attn_drop_rate=attn_drop_rate, drop_path_rate=enc_dp_rates[sum(enc_depths[:i]):sum(enc_depths[:i + 1])], enable_checkpoint=enable_checkpoint)
        dec = Decoder(depth=dec_depths[i], in_channels=dec_channels[i + 1], skip_channels=enc_channels[i], embed_channels=dec_channels[i], groups=dec_groups[i], neighbours=dec_neighbours[i], qkv_bias=attn_qkv_bias, pe_multiplier=pe_multiplier, pe_bias=pe_bias, attn_drop_rate=attn_drop_rate, drop_path_rate=dec_dp_rates[sum(dec_depths[:i]):sum(dec_depths[:i + 1])], enable_checkpoint=enable_checkpoint, unpool_backend=unpool_backend)
        self.enc_stages.append(enc)
        self.dec_stages.append(dec)
    self.seg_head = nn.Sequential(nn.Linear(dec_channels[0], dec_channels[0]), PointBatchNorm(dec_channels[0]), nn.ReLU(inplace=True), nn.Linear(dec_channels[0], num_classes)) if num_classes > 0 else nn.Identity()

class PointTransformerLayer(nn.Module):

    def __init__(self, in_planes, out_planes, share_planes=8, nsample=16):
        super().__init__()
        self.mid_planes = mid_planes = out_planes // 1
        self.out_planes = out_planes
        self.share_planes = share_planes
        self.nsample = nsample
        self.linear_q = nn.Linear(in_planes, mid_planes)
        self.linear_k = nn.Linear(in_planes, mid_planes)
        self.linear_v = nn.Linear(in_planes, out_planes)
        self.linear_p = nn.Sequential(nn.Linear(3, 3), LayerNorm1d(3), nn.ReLU(inplace=True), nn.Linear(3, out_planes))
        self.linear_w = nn.Sequential(LayerNorm1d(mid_planes), nn.ReLU(inplace=True), nn.Linear(mid_planes, out_planes // share_planes), LayerNorm1d(out_planes // share_planes), nn.ReLU(inplace=True), nn.Linear(out_planes // share_planes, out_planes // share_planes))
        self.softmax = nn.Softmax(dim=1)

    def forward(self, pxo) -> torch.Tensor:
        p, x, o = pxo
        x_q, x_k, x_v = (self.linear_q(x), self.linear_k(x), self.linear_v(x))
        x_k, idx = pointops.knn_query_and_group(x_k, p, o, new_xyz=p, new_offset=o, nsample=self.nsample, with_xyz=True)
        x_v, _ = pointops.knn_query_and_group(x_v, p, o, new_xyz=p, new_offset=o, idx=idx, nsample=self.nsample, with_xyz=False)
        p_r, x_k = (x_k[:, :, 0:3], x_k[:, :, 3:])
        p_r = self.linear_p(p_r)
        r_qk = x_k - x_q.unsqueeze(1) + einops.reduce(p_r, 'n ns (i j) -> n ns j', reduction='sum', j=self.mid_planes)
        w = self.linear_w(r_qk)
        w = self.softmax(w)
        x = torch.einsum('n t s i, n t i -> n s i', einops.rearrange(x_v + p_r, 'n ns (s i) -> n ns s i', s=self.share_planes), w)
        x = einops.rearrange(x, 'n s i -> n (s i)')
        return x

def __init__(self, in_planes, out_planes, share_planes=8, nsample=16):
    super().__init__()
    self.mid_planes = mid_planes = out_planes // 1
    self.out_planes = out_planes
    self.share_planes = share_planes
    self.nsample = nsample
    self.linear_q = nn.Linear(in_planes, mid_planes)
    self.linear_k = nn.Linear(in_planes, mid_planes)
    self.linear_v = nn.Linear(in_planes, out_planes)
    self.linear_p = nn.Sequential(nn.Linear(3, 3), LayerNorm1d(3), nn.ReLU(inplace=True), nn.Linear(3, out_planes))
    self.linear_w = nn.Sequential(LayerNorm1d(mid_planes), nn.ReLU(inplace=True), nn.Linear(mid_planes, out_planes // share_planes), LayerNorm1d(out_planes // share_planes), nn.ReLU(inplace=True), nn.Linear(out_planes // share_planes, out_planes // share_planes))
    self.softmax = nn.Softmax(dim=1)

class TransitionDown(nn.Module):

    def __init__(self, in_planes, out_planes, stride=1, nsample=16):
        super().__init__()
        self.stride, self.nsample = (stride, nsample)
        if stride != 1:
            self.linear = nn.Linear(3 + in_planes, out_planes, bias=False)
            self.pool = nn.MaxPool1d(nsample)
        else:
            self.linear = nn.Linear(in_planes, out_planes, bias=False)
        self.bn = nn.BatchNorm1d(out_planes)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, pxo):
        p, x, o = pxo
        if self.stride != 1:
            n_o, count = ([o[0].item() // self.stride], o[0].item() // self.stride)
            for i in range(1, o.shape[0]):
                count += (o[i].item() - o[i - 1].item()) // self.stride
                n_o.append(count)
            n_o = torch.cuda.IntTensor(n_o)
            idx = pointops.farthest_point_sampling(p, o, n_o)
            n_p = p[idx.long(), :]
            x, _ = pointops.knn_query_and_group(x, p, offset=o, new_xyz=n_p, new_offset=n_o, nsample=self.nsample, with_xyz=True)
            x = self.relu(self.bn(self.linear(x).transpose(1, 2).contiguous()))
            x = self.pool(x).squeeze(-1)
            p, o = (n_p, n_o)
        else:
            x = self.relu(self.bn(self.linear(x)))
        return [p, x, o]

def __init__(self, in_planes, out_planes, stride=1, nsample=16):
    super().__init__()
    self.stride, self.nsample = (stride, nsample)
    if stride != 1:
        self.linear = nn.Linear(3 + in_planes, out_planes, bias=False)
        self.pool = nn.MaxPool1d(nsample)
    else:
        self.linear = nn.Linear(in_planes, out_planes, bias=False)
    self.bn = nn.BatchNorm1d(out_planes)
    self.relu = nn.ReLU(inplace=True)

class TransitionUp(nn.Module):

    def __init__(self, in_planes, out_planes=None, num_shape_class=None):
        super().__init__()
        if out_planes is None:
            self.num_shape_class = num_shape_class
            if num_shape_class is not None:
                self.linear1 = nn.Sequential(nn.Linear(2 * in_planes + 1024, in_planes), nn.BatchNorm1d(in_planes), nn.ReLU(inplace=True))
            else:
                self.linear1 = nn.Sequential(nn.Linear(2 * in_planes, in_planes), nn.BatchNorm1d(in_planes), nn.ReLU(inplace=True))
            self.linear2 = nn.Sequential(nn.Linear(in_planes, in_planes), nn.ReLU(inplace=True))
            if num_shape_class is not None:
                self.linear3 = nn.Sequential(nn.Linear(num_shape_class, 1024), nn.ReLU(inplace=True))
        else:
            self.linear1 = nn.Sequential(nn.Linear(out_planes, out_planes), nn.BatchNorm1d(out_planes), nn.ReLU(inplace=True))
            self.linear2 = nn.Sequential(nn.Linear(in_planes, out_planes), nn.BatchNorm1d(out_planes), nn.ReLU(inplace=True))

    def forward(self, pxo1, pxo2=None, y=None):
        if pxo2 is None:
            _, x, o = pxo1
            x_tmp = []
            for i in range(o.shape[0]):
                if i == 0:
                    s_i, e_i, cnt = (0, o[0], o[0])
                else:
                    s_i, e_i, cnt = (o[i - 1], o[i], o[i] - o[i - 1])
                x_b = x[s_i:e_i, :]
                y_b = y[i].unsqueeze(-1).unsqueeze(-1).long()
                y_onehot = torch.zeros(1, self.num_shape_class).cuda()
                y_onehot.scatter_(1, y_b, 1)
                x_b = torch.cat((x_b, self.linear2(x_b.sum(0, True) / cnt).repeat(cnt, 1), self.linear3(y_onehot).repeat(cnt, 1)), dim=1)
                x_tmp.append(x_b)
            x = torch.cat(x_tmp, 0)
            x = self.linear1(x)
        else:
            p1, x1, o1 = pxo1
            p2, x2, o2 = pxo2
            x = self.linear1(x1) + pointops.interpolation(p2, p1, self.linear2(x2), o2, o1)
        return x

def __init__(self, in_planes, out_planes=None, num_shape_class=None):
    super().__init__()
    if out_planes is None:
        self.num_shape_class = num_shape_class
        if num_shape_class is not None:
            self.linear1 = nn.Sequential(nn.Linear(2 * in_planes + 1024, in_planes), nn.BatchNorm1d(in_planes), nn.ReLU(inplace=True))
        else:
            self.linear1 = nn.Sequential(nn.Linear(2 * in_planes, in_planes), nn.BatchNorm1d(in_planes), nn.ReLU(inplace=True))
        self.linear2 = nn.Sequential(nn.Linear(in_planes, in_planes), nn.ReLU(inplace=True))
        if num_shape_class is not None:
            self.linear3 = nn.Sequential(nn.Linear(num_shape_class, 1024), nn.ReLU(inplace=True))
    else:
        self.linear1 = nn.Sequential(nn.Linear(out_planes, out_planes), nn.BatchNorm1d(out_planes), nn.ReLU(inplace=True))
        self.linear2 = nn.Sequential(nn.Linear(in_planes, out_planes), nn.BatchNorm1d(out_planes), nn.ReLU(inplace=True))

class Bottleneck(nn.Module):
    expansion = 1

    def __init__(self, in_planes, planes, share_planes=8, nsample=16):
        super(Bottleneck, self).__init__()
        self.linear1 = nn.Linear(in_planes, planes, bias=False)
        self.bn1 = nn.BatchNorm1d(planes)
        self.transformer = PointTransformerLayer(planes, planes, share_planes, nsample)
        self.bn2 = nn.BatchNorm1d(planes)
        self.linear3 = nn.Linear(planes, planes * self.expansion, bias=False)
        self.bn3 = nn.BatchNorm1d(planes * self.expansion)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, pxo):
        p, x, o = pxo
        identity = x
        x = self.relu(self.bn1(self.linear1(x)))
        x = self.relu(self.bn2(self.transformer([p, x, o])))
        x = self.bn3(self.linear3(x))
        x += identity
        x = self.relu(x)
        return [p, x, o]

def __init__(self, in_planes, planes, share_planes=8, nsample=16):
    super(Bottleneck, self).__init__()
    self.linear1 = nn.Linear(in_planes, planes, bias=False)
    self.bn1 = nn.BatchNorm1d(planes)
    self.transformer = PointTransformerLayer(planes, planes, share_planes, nsample)
    self.bn2 = nn.BatchNorm1d(planes)
    self.linear3 = nn.Linear(planes, planes * self.expansion, bias=False)
    self.bn3 = nn.BatchNorm1d(planes * self.expansion)
    self.relu = nn.ReLU(inplace=True)

class PointTransformerSeg(nn.Module):

    def __init__(self, block, blocks, in_channels=6, num_classes=50, num_shape_classes=None):
        super().__init__()
        self.in_channels = in_channels
        self.num_classes = num_classes
        self.num_shape_classes = num_shape_classes
        self.in_planes, planes = (in_channels, [32, 64, 128, 256, 512])
        fpn_planes, fpnhead_planes, share_planes = (128, 64, 8)
        stride, nsample = ([1, 4, 4, 4, 4], [8, 16, 16, 16, 16])
        self.enc1 = self._make_enc(block, planes[0], blocks[0], share_planes, stride=stride[0], nsample=nsample[0])
        self.enc2 = self._make_enc(block, planes[1], blocks[1], share_planes, stride=stride[1], nsample=nsample[1])
        self.enc3 = self._make_enc(block, planes[2], blocks[2], share_planes, stride=stride[2], nsample=nsample[2])
        self.enc4 = self._make_enc(block, planes[3], blocks[3], share_planes, stride=stride[3], nsample=nsample[3])
        self.enc5 = self._make_enc(block, planes[4], blocks[4], share_planes, stride=stride[4], nsample=nsample[4])
        self.dec5 = self._make_dec(block, planes[4], 1, share_planes, num_shape_classes=num_shape_classes, nsample=nsample[4], is_head=True)
        self.dec4 = self._make_dec(block, planes[3], 1, share_planes, nsample=nsample[3])
        self.dec3 = self._make_dec(block, planes[2], 1, share_planes, nsample=nsample[2])
        self.dec2 = self._make_dec(block, planes[1], 1, share_planes, nsample=nsample[1])
        self.dec1 = self._make_dec(block, planes[0], 1, share_planes, nsample=nsample[0])
        self.cls = nn.Sequential(nn.Linear(planes[0], planes[0]), nn.BatchNorm1d(planes[0]), nn.ReLU(inplace=True), nn.Linear(planes[0], num_classes))

    def _make_enc(self, block, planes, blocks, share_planes=8, stride=1, nsample=16):
        layers = [TransitionDown(self.in_planes, planes * block.expansion, stride, nsample)]
        self.in_planes = planes * block.expansion
        for _ in range(blocks):
            layers.append(block(self.in_planes, self.in_planes, share_planes, nsample=nsample))
        return nn.Sequential(*layers)

    def _make_dec(self, block, planes, blocks, share_planes=8, num_shape_classes=None, nsample=16, is_head=False):
        layers = [TransitionUp(self.in_planes, None if is_head else planes * block.expansion, num_shape_classes)]
        self.in_planes = planes * block.expansion
        for _ in range(blocks):
            layers.append(block(self.in_planes, self.in_planes, share_planes, nsample=nsample))
        return nn.Sequential(*layers)

    def forward(self, input_dict):
        p0 = input_dict['coord']
        x0 = input_dict['feat']
        o0 = input_dict['offset'].int()
        if self.num_shape_classes is not None:
            y = input_dict['cls_token']
        p1, x1, o1 = self.enc1([p0, x0, o0])
        p2, x2, o2 = self.enc2([p1, x1, o1])
        p3, x3, o3 = self.enc3([p2, x2, o2])
        p4, x4, o4 = self.enc4([p3, x3, o3])
        p5, x5, o5 = self.enc5([p4, x4, o4])
        if self.num_shape_classes is not None:
            x5 = self.dec5[1:]([p5, self.dec5[0]([p5, x5, o5], y=y), o5])[1]
        else:
            x5 = self.dec5[1:]([p5, self.dec5[0]([p5, x5, o5]), o5])[1]
        x4 = self.dec4[1:]([p4, self.dec4[0]([p4, x4, o4], [p5, x5, o5]), o4])[1]
        x3 = self.dec3[1:]([p3, self.dec3[0]([p3, x3, o3], [p4, x4, o4]), o3])[1]
        x2 = self.dec2[1:]([p2, self.dec2[0]([p2, x2, o2], [p3, x3, o3]), o2])[1]
        x1 = self.dec1[1:]([p1, self.dec1[0]([p1, x1, o1], [p2, x2, o2]), o1])[1]
        x = self.cls(x1)
        return x

def __init__(self, block, blocks, in_channels=6, num_classes=50, num_shape_classes=None):
    super().__init__()
    self.in_channels = in_channels
    self.num_classes = num_classes
    self.num_shape_classes = num_shape_classes
    self.in_planes, planes = (in_channels, [32, 64, 128, 256, 512])
    fpn_planes, fpnhead_planes, share_planes = (128, 64, 8)
    stride, nsample = ([1, 4, 4, 4, 4], [8, 16, 16, 16, 16])
    self.enc1 = self._make_enc(block, planes[0], blocks[0], share_planes, stride=stride[0], nsample=nsample[0])
    self.enc2 = self._make_enc(block, planes[1], blocks[1], share_planes, stride=stride[1], nsample=nsample[1])
    self.enc3 = self._make_enc(block, planes[2], blocks[2], share_planes, stride=stride[2], nsample=nsample[2])
    self.enc4 = self._make_enc(block, planes[3], blocks[3], share_planes, stride=stride[3], nsample=nsample[3])
    self.enc5 = self._make_enc(block, planes[4], blocks[4], share_planes, stride=stride[4], nsample=nsample[4])
    self.dec5 = self._make_dec(block, planes[4], 1, share_planes, num_shape_classes=num_shape_classes, nsample=nsample[4], is_head=True)
    self.dec4 = self._make_dec(block, planes[3], 1, share_planes, nsample=nsample[3])
    self.dec3 = self._make_dec(block, planes[2], 1, share_planes, nsample=nsample[2])
    self.dec2 = self._make_dec(block, planes[1], 1, share_planes, nsample=nsample[1])
    self.dec1 = self._make_dec(block, planes[0], 1, share_planes, nsample=nsample[0])
    self.cls = nn.Sequential(nn.Linear(planes[0], planes[0]), nn.BatchNorm1d(planes[0]), nn.ReLU(inplace=True), nn.Linear(planes[0], num_classes))

@MODELS.register_module('PointTransformer-PartSeg26')
class PointTransformerSeg26(PointTransformerSeg):

    def __init__(self, **kwargs):
        super(PointTransformerSeg26, self).__init__(Bottleneck, [1, 1, 1, 1, 1], **kwargs)

def __init__(self, **kwargs):
    super(PointTransformerSeg26, self).__init__(Bottleneck, [1, 1, 1, 1, 1], **kwargs)

@MODELS.register_module('PointTransformer-PartSeg38')
class PointTransformerSeg38(PointTransformerSeg):

    def __init__(self, **kwargs):
        super(PointTransformerSeg38, self).__init__(Bottleneck, [1, 2, 2, 2, 2], **kwargs)

def __init__(self, **kwargs):
    super(PointTransformerSeg38, self).__init__(Bottleneck, [1, 2, 2, 2, 2], **kwargs)

@MODELS.register_module('PointTransformer-PartSeg50')
class PointTransformerSeg50(PointTransformerSeg):

    def __init__(self, **kwargs):
        super(PointTransformerSeg50, self).__init__(Bottleneck, [1, 2, 3, 5, 2], **kwargs)

def __init__(self, **kwargs):
    super(PointTransformerSeg50, self).__init__(Bottleneck, [1, 2, 3, 5, 2], **kwargs)

class PointTransformerLayer(nn.Module):

    def __init__(self, in_planes, out_planes, share_planes=8, nsample=16):
        super().__init__()
        self.mid_planes = mid_planes = out_planes // 1
        self.out_planes = out_planes
        self.share_planes = share_planes
        self.nsample = nsample
        self.linear_q = nn.Linear(in_planes, mid_planes)
        self.linear_k = nn.Linear(in_planes, mid_planes)
        self.linear_v = nn.Linear(in_planes, out_planes)
        self.linear_p = nn.Sequential(nn.Linear(3, 3), LayerNorm1d(3), nn.ReLU(inplace=True), nn.Linear(3, out_planes))
        self.linear_w = nn.Sequential(LayerNorm1d(mid_planes), nn.ReLU(inplace=True), nn.Linear(mid_planes, out_planes // share_planes), LayerNorm1d(out_planes // share_planes), nn.ReLU(inplace=True), nn.Linear(out_planes // share_planes, out_planes // share_planes))
        self.softmax = nn.Softmax(dim=1)

    def forward(self, pxo) -> torch.Tensor:
        p, x, o = pxo
        x_q, x_k, x_v = (self.linear_q(x), self.linear_k(x), self.linear_v(x))
        x_k, idx = pointops.knn_query_and_group(x_k, p, o, new_xyz=p, new_offset=o, nsample=self.nsample, with_xyz=True)
        x_v, _ = pointops.knn_query_and_group(x_v, p, o, new_xyz=p, new_offset=o, idx=idx, nsample=self.nsample, with_xyz=False)
        p_r, x_k = (x_k[:, :, 0:3], x_k[:, :, 3:])
        p_r = self.linear_p(p_r)
        r_qk = x_k - x_q.unsqueeze(1) + einops.reduce(p_r, 'n ns (i j) -> n ns j', reduction='sum', j=self.mid_planes)
        w = self.linear_w(r_qk)
        w = self.softmax(w)
        x = torch.einsum('n t s i, n t i -> n s i', einops.rearrange(x_v + p_r, 'n ns (s i) -> n ns s i', s=self.share_planes), w)
        x = einops.rearrange(x, 'n s i -> n (s i)')
        return x

def __init__(self, in_planes, out_planes, share_planes=8, nsample=16):
    super().__init__()
    self.mid_planes = mid_planes = out_planes // 1
    self.out_planes = out_planes
    self.share_planes = share_planes
    self.nsample = nsample
    self.linear_q = nn.Linear(in_planes, mid_planes)
    self.linear_k = nn.Linear(in_planes, mid_planes)
    self.linear_v = nn.Linear(in_planes, out_planes)
    self.linear_p = nn.Sequential(nn.Linear(3, 3), LayerNorm1d(3), nn.ReLU(inplace=True), nn.Linear(3, out_planes))
    self.linear_w = nn.Sequential(LayerNorm1d(mid_planes), nn.ReLU(inplace=True), nn.Linear(mid_planes, out_planes // share_planes), LayerNorm1d(out_planes // share_planes), nn.ReLU(inplace=True), nn.Linear(out_planes // share_planes, out_planes // share_planes))
    self.softmax = nn.Softmax(dim=1)

class TransitionDown(nn.Module):

    def __init__(self, in_planes, out_planes, stride=1, nsample=16):
        super().__init__()
        self.stride, self.nsample = (stride, nsample)
        if stride != 1:
            self.linear = nn.Linear(3 + in_planes, out_planes, bias=False)
            self.pool = nn.MaxPool1d(nsample)
        else:
            self.linear = nn.Linear(in_planes, out_planes, bias=False)
        self.bn = nn.BatchNorm1d(out_planes)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, pxo):
        p, x, o = pxo
        if self.stride != 1:
            n_o, count = ([o[0].item() // self.stride], o[0].item() // self.stride)
            for i in range(1, o.shape[0]):
                count += (o[i].item() - o[i - 1].item()) // self.stride
                n_o.append(count)
            n_o = torch.cuda.IntTensor(n_o)
            idx = pointops.farthest_point_sampling(p, o, n_o)
            n_p = p[idx.long(), :]
            x, _ = pointops.knn_query_and_group(x, p, offset=o, new_xyz=n_p, new_offset=n_o, nsample=self.nsample, with_xyz=True)
            x = self.relu(self.bn(self.linear(x).transpose(1, 2).contiguous()))
            x = self.pool(x).squeeze(-1)
            p, o = (n_p, n_o)
        else:
            x = self.relu(self.bn(self.linear(x)))
        return [p, x, o]

def __init__(self, in_planes, out_planes, stride=1, nsample=16):
    super().__init__()
    self.stride, self.nsample = (stride, nsample)
    if stride != 1:
        self.linear = nn.Linear(3 + in_planes, out_planes, bias=False)
        self.pool = nn.MaxPool1d(nsample)
    else:
        self.linear = nn.Linear(in_planes, out_planes, bias=False)
    self.bn = nn.BatchNorm1d(out_planes)
    self.relu = nn.ReLU(inplace=True)

class TransitionUp(nn.Module):

    def __init__(self, in_planes, out_planes=None):
        super().__init__()
        if out_planes is None:
            self.linear1 = nn.Sequential(nn.Linear(2 * in_planes, in_planes), nn.BatchNorm1d(in_planes), nn.ReLU(inplace=True))
            self.linear2 = nn.Sequential(nn.Linear(in_planes, in_planes), nn.ReLU(inplace=True))
        else:
            self.linear1 = nn.Sequential(nn.Linear(out_planes, out_planes), nn.BatchNorm1d(out_planes), nn.ReLU(inplace=True))
            self.linear2 = nn.Sequential(nn.Linear(in_planes, out_planes), nn.BatchNorm1d(out_planes), nn.ReLU(inplace=True))

    def forward(self, pxo1, pxo2=None):
        if pxo2 is None:
            _, x, o = pxo1
            x_tmp = []
            for i in range(o.shape[0]):
                if i == 0:
                    s_i, e_i, cnt = (0, o[0], o[0])
                else:
                    s_i, e_i, cnt = (o[i - 1], o[i], o[i] - o[i - 1])
                x_b = x[s_i:e_i, :]
                x_b = torch.cat((x_b, self.linear2(x_b.sum(0, True) / cnt).repeat(cnt, 1)), 1)
                x_tmp.append(x_b)
            x = torch.cat(x_tmp, 0)
            x = self.linear1(x)
        else:
            p1, x1, o1 = pxo1
            p2, x2, o2 = pxo2
            x = self.linear1(x1) + pointops.interpolation(p2, p1, self.linear2(x2), o2, o1)
        return x

def __init__(self, in_planes, out_planes=None):
    super().__init__()
    if out_planes is None:
        self.linear1 = nn.Sequential(nn.Linear(2 * in_planes, in_planes), nn.BatchNorm1d(in_planes), nn.ReLU(inplace=True))
        self.linear2 = nn.Sequential(nn.Linear(in_planes, in_planes), nn.ReLU(inplace=True))
    else:
        self.linear1 = nn.Sequential(nn.Linear(out_planes, out_planes), nn.BatchNorm1d(out_planes), nn.ReLU(inplace=True))
        self.linear2 = nn.Sequential(nn.Linear(in_planes, out_planes), nn.BatchNorm1d(out_planes), nn.ReLU(inplace=True))

class Bottleneck(nn.Module):
    expansion = 1

    def __init__(self, in_planes, planes, share_planes=8, nsample=16):
        super(Bottleneck, self).__init__()
        self.linear1 = nn.Linear(in_planes, planes, bias=False)
        self.bn1 = nn.BatchNorm1d(planes)
        self.transformer = PointTransformerLayer(planes, planes, share_planes, nsample)
        self.bn2 = nn.BatchNorm1d(planes)
        self.linear3 = nn.Linear(planes, planes * self.expansion, bias=False)
        self.bn3 = nn.BatchNorm1d(planes * self.expansion)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, pxo):
        p, x, o = pxo
        identity = x
        x = self.relu(self.bn1(self.linear1(x)))
        x = self.relu(self.bn2(self.transformer([p, x, o])))
        x = self.bn3(self.linear3(x))
        x += identity
        x = self.relu(x)
        return [p, x, o]

def __init__(self, in_planes, planes, share_planes=8, nsample=16):
    super(Bottleneck, self).__init__()
    self.linear1 = nn.Linear(in_planes, planes, bias=False)
    self.bn1 = nn.BatchNorm1d(planes)
    self.transformer = PointTransformerLayer(planes, planes, share_planes, nsample)
    self.bn2 = nn.BatchNorm1d(planes)
    self.linear3 = nn.Linear(planes, planes * self.expansion, bias=False)
    self.bn3 = nn.BatchNorm1d(planes * self.expansion)
    self.relu = nn.ReLU(inplace=True)

class PointTransformerSeg(nn.Module):

    def __init__(self, block, blocks, in_channels=6, num_classes=13):
        super().__init__()
        self.in_channels = in_channels
        self.in_planes, planes = (in_channels, [32, 64, 128, 256, 512])
        fpn_planes, fpnhead_planes, share_planes = (128, 64, 8)
        stride, nsample = ([1, 4, 4, 4, 4], [8, 16, 16, 16, 16])
        self.enc1 = self._make_enc(block, planes[0], blocks[0], share_planes, stride=stride[0], nsample=nsample[0])
        self.enc2 = self._make_enc(block, planes[1], blocks[1], share_planes, stride=stride[1], nsample=nsample[1])
        self.enc3 = self._make_enc(block, planes[2], blocks[2], share_planes, stride=stride[2], nsample=nsample[2])
        self.enc4 = self._make_enc(block, planes[3], blocks[3], share_planes, stride=stride[3], nsample=nsample[3])
        self.enc5 = self._make_enc(block, planes[4], blocks[4], share_planes, stride=stride[4], nsample=nsample[4])
        self.dec5 = self._make_dec(block, planes[4], 1, share_planes, nsample=nsample[4], is_head=True)
        self.dec4 = self._make_dec(block, planes[3], 1, share_planes, nsample=nsample[3])
        self.dec3 = self._make_dec(block, planes[2], 1, share_planes, nsample=nsample[2])
        self.dec2 = self._make_dec(block, planes[1], 1, share_planes, nsample=nsample[1])
        self.dec1 = self._make_dec(block, planes[0], 1, share_planes, nsample=nsample[0])
        self.cls = nn.Sequential(nn.Linear(planes[0], planes[0]), nn.BatchNorm1d(planes[0]), nn.ReLU(inplace=True), nn.Linear(planes[0], num_classes))

    def _make_enc(self, block, planes, blocks, share_planes=8, stride=1, nsample=16):
        layers = [TransitionDown(self.in_planes, planes * block.expansion, stride, nsample)]
        self.in_planes = planes * block.expansion
        for _ in range(blocks):
            layers.append(block(self.in_planes, self.in_planes, share_planes, nsample=nsample))
        return nn.Sequential(*layers)

    def _make_dec(self, block, planes, blocks, share_planes=8, nsample=16, is_head=False):
        layers = [TransitionUp(self.in_planes, None if is_head else planes * block.expansion)]
        self.in_planes = planes * block.expansion
        for _ in range(blocks):
            layers.append(block(self.in_planes, self.in_planes, share_planes, nsample=nsample))
        return nn.Sequential(*layers)

    def forward(self, input_dict):
        p0 = input_dict['coord']
        x0 = input_dict['feat']
        o0 = input_dict['offset'].int()
        p1, x1, o1 = self.enc1([p0, x0, o0])
        p2, x2, o2 = self.enc2([p1, x1, o1])
        p3, x3, o3 = self.enc3([p2, x2, o2])
        p4, x4, o4 = self.enc4([p3, x3, o3])
        p5, x5, o5 = self.enc5([p4, x4, o4])
        x5 = self.dec5[1:]([p5, self.dec5[0]([p5, x5, o5]), o5])[1]
        x4 = self.dec4[1:]([p4, self.dec4[0]([p4, x4, o4], [p5, x5, o5]), o4])[1]
        x3 = self.dec3[1:]([p3, self.dec3[0]([p3, x3, o3], [p4, x4, o4]), o3])[1]
        x2 = self.dec2[1:]([p2, self.dec2[0]([p2, x2, o2], [p3, x3, o3]), o2])[1]
        x1 = self.dec1[1:]([p1, self.dec1[0]([p1, x1, o1], [p2, x2, o2]), o1])[1]
        x = self.cls(x1)
        return x

def __init__(self, block, blocks, in_channels=6, num_classes=13):
    super().__init__()
    self.in_channels = in_channels
    self.in_planes, planes = (in_channels, [32, 64, 128, 256, 512])
    fpn_planes, fpnhead_planes, share_planes = (128, 64, 8)
    stride, nsample = ([1, 4, 4, 4, 4], [8, 16, 16, 16, 16])
    self.enc1 = self._make_enc(block, planes[0], blocks[0], share_planes, stride=stride[0], nsample=nsample[0])
    self.enc2 = self._make_enc(block, planes[1], blocks[1], share_planes, stride=stride[1], nsample=nsample[1])
    self.enc3 = self._make_enc(block, planes[2], blocks[2], share_planes, stride=stride[2], nsample=nsample[2])
    self.enc4 = self._make_enc(block, planes[3], blocks[3], share_planes, stride=stride[3], nsample=nsample[3])
    self.enc5 = self._make_enc(block, planes[4], blocks[4], share_planes, stride=stride[4], nsample=nsample[4])
    self.dec5 = self._make_dec(block, planes[4], 1, share_planes, nsample=nsample[4], is_head=True)
    self.dec4 = self._make_dec(block, planes[3], 1, share_planes, nsample=nsample[3])
    self.dec3 = self._make_dec(block, planes[2], 1, share_planes, nsample=nsample[2])
    self.dec2 = self._make_dec(block, planes[1], 1, share_planes, nsample=nsample[1])
    self.dec1 = self._make_dec(block, planes[0], 1, share_planes, nsample=nsample[0])
    self.cls = nn.Sequential(nn.Linear(planes[0], planes[0]), nn.BatchNorm1d(planes[0]), nn.ReLU(inplace=True), nn.Linear(planes[0], num_classes))

@MODELS.register_module('PointTransformer-Seg26')
class PointTransformerSeg26(PointTransformerSeg):

    def __init__(self, **kwargs):
        super(PointTransformerSeg26, self).__init__(Bottleneck, [1, 1, 1, 1, 1], **kwargs)

def __init__(self, **kwargs):
    super(PointTransformerSeg26, self).__init__(Bottleneck, [1, 1, 1, 1, 1], **kwargs)

@MODELS.register_module('PointTransformer-Seg38')
class PointTransformerSeg38(PointTransformerSeg):

    def __init__(self, **kwargs):
        super(PointTransformerSeg38, self).__init__(Bottleneck, [1, 2, 2, 2, 2], **kwargs)

def __init__(self, **kwargs):
    super(PointTransformerSeg38, self).__init__(Bottleneck, [1, 2, 2, 2, 2], **kwargs)

@MODELS.register_module('PointTransformer-Seg50')
class PointTransformerSeg50(PointTransformerSeg):

    def __init__(self, **kwargs):
        super(PointTransformerSeg50, self).__init__(Bottleneck, [1, 2, 3, 5, 2], **kwargs)

def __init__(self, **kwargs):
    super(PointTransformerSeg50, self).__init__(Bottleneck, [1, 2, 3, 5, 2], **kwargs)

class PointTransformerCls(nn.Module):

    def __init__(self, block, blocks, in_channels=6, num_classes=40):
        super().__init__()
        self.in_channels = in_channels
        self.in_planes, planes = (in_channels, [32, 64, 128, 256, 512])
        fpn_planes, fpnhead_planes, share_planes = (128, 64, 8)
        stride, nsample = ([1, 4, 4, 4, 4], [8, 16, 16, 16, 16])
        self.enc1 = self._make_enc(block, planes[0], blocks[0], share_planes, stride=stride[0], nsample=nsample[0])
        self.enc2 = self._make_enc(block, planes[1], blocks[1], share_planes, stride=stride[1], nsample=nsample[1])
        self.enc3 = self._make_enc(block, planes[2], blocks[2], share_planes, stride=stride[2], nsample=nsample[2])
        self.enc4 = self._make_enc(block, planes[3], blocks[3], share_planes, stride=stride[3], nsample=nsample[3])
        self.enc5 = self._make_enc(block, planes[4], blocks[4], share_planes, stride=stride[4], nsample=nsample[4])
        self.cls = nn.Sequential(nn.Linear(planes[4], 256), nn.BatchNorm1d(256), nn.ReLU(inplace=True), nn.Dropout(p=0.5), nn.Linear(256, 128), nn.BatchNorm1d(128), nn.ReLU(inplace=True), nn.Dropout(p=0.5), nn.Linear(128, num_classes))

    def _make_enc(self, block, planes, blocks, share_planes=8, stride=1, nsample=16):
        layers = [TransitionDown(self.in_planes, planes * block.expansion, stride, nsample)]
        self.in_planes = planes * block.expansion
        for _ in range(1, blocks):
            layers.append(block(self.in_planes, self.in_planes, share_planes, nsample=nsample))
        return nn.Sequential(*layers)

    def forward(self, input_dict):
        p0 = input_dict['coord']
        x0 = input_dict['feat']
        o0 = input_dict['offset'].int()
        x0 = p0 if self.in_channels == 3 else torch.cat((p0, x0), 1)
        p1, x1, o1 = self.enc1([p0, x0, o0])
        p2, x2, o2 = self.enc2([p1, x1, o1])
        p3, x3, o3 = self.enc3([p2, x2, o2])
        p4, x4, o4 = self.enc4([p3, x3, o3])
        p5, x5, o5 = self.enc5([p4, x4, o4])
        x = []
        for i in range(o5.shape[0]):
            if i == 0:
                s_i, e_i, cnt = (0, o5[0], o5[0])
            else:
                s_i, e_i, cnt = (o5[i - 1], o5[i], o5[i] - o5[i - 1])
            x_b = x5[s_i:e_i, :].sum(0, True) / cnt
            x.append(x_b)
        x = torch.cat(x, 0)
        x = self.cls(x)
        return x

def __init__(self, block, blocks, in_channels=6, num_classes=40):
    super().__init__()
    self.in_channels = in_channels
    self.in_planes, planes = (in_channels, [32, 64, 128, 256, 512])
    fpn_planes, fpnhead_planes, share_planes = (128, 64, 8)
    stride, nsample = ([1, 4, 4, 4, 4], [8, 16, 16, 16, 16])
    self.enc1 = self._make_enc(block, planes[0], blocks[0], share_planes, stride=stride[0], nsample=nsample[0])
    self.enc2 = self._make_enc(block, planes[1], blocks[1], share_planes, stride=stride[1], nsample=nsample[1])
    self.enc3 = self._make_enc(block, planes[2], blocks[2], share_planes, stride=stride[2], nsample=nsample[2])
    self.enc4 = self._make_enc(block, planes[3], blocks[3], share_planes, stride=stride[3], nsample=nsample[3])
    self.enc5 = self._make_enc(block, planes[4], blocks[4], share_planes, stride=stride[4], nsample=nsample[4])
    self.cls = nn.Sequential(nn.Linear(planes[4], 256), nn.BatchNorm1d(256), nn.ReLU(inplace=True), nn.Dropout(p=0.5), nn.Linear(256, 128), nn.BatchNorm1d(128), nn.ReLU(inplace=True), nn.Dropout(p=0.5), nn.Linear(128, num_classes))

@MODELS.register_module('PointTransformer-Cls26')
class PointTransformerCls26(PointTransformerCls):

    def __init__(self, **kwargs):
        super(PointTransformerCls26, self).__init__(Bottleneck, [1, 1, 1, 1, 1], **kwargs)

def __init__(self, **kwargs):
    super(PointTransformerCls26, self).__init__(Bottleneck, [1, 1, 1, 1, 1], **kwargs)

@MODELS.register_module('PointTransformer-Cls38')
class PointTransformerCls38(PointTransformerCls):

    def __init__(self, **kwargs):
        super(PointTransformerCls38, self).__init__(Bottleneck, [1, 2, 2, 2, 2], **kwargs)

def __init__(self, **kwargs):
    super(PointTransformerCls38, self).__init__(Bottleneck, [1, 2, 2, 2, 2], **kwargs)

@MODELS.register_module('PointTransformer-Cls50')
class PointTransformerCls50(PointTransformerCls):

    def __init__(self, **kwargs):
        super(PointTransformerCls50, self).__init__(Bottleneck, [1, 2, 3, 5, 2], **kwargs)

def __init__(self, **kwargs):
    super(PointTransformerCls50, self).__init__(Bottleneck, [1, 2, 3, 5, 2], **kwargs)

class BasicBlock(nn.Module):
    expansion = 1

    def __init__(self, inplanes, planes, stride=1, dilation=1, downsample=None, bn_momentum=0.1, dimension=-1):
        super(BasicBlock, self).__init__()
        assert dimension > 0
        self.conv1 = ME.MinkowskiConvolution(inplanes, planes, kernel_size=3, stride=stride, dilation=dilation, dimension=dimension)
        self.norm1 = ME.MinkowskiBatchNorm(planes, momentum=bn_momentum)
        self.conv2 = ME.MinkowskiConvolution(planes, planes, kernel_size=3, stride=1, dilation=dilation, dimension=dimension)
        self.norm2 = ME.MinkowskiBatchNorm(planes, momentum=bn_momentum)
        self.relu = ME.MinkowskiReLU(inplace=True)
        self.downsample = downsample

    def forward(self, x):
        residual = x
        out = self.conv1(x)
        out = self.norm1(out)
        out = self.relu(out)
        out = self.conv2(out)
        out = self.norm2(out)
        if self.downsample is not None:
            residual = self.downsample(x)
        out += residual
        out = self.relu(out)
        return out

def __init__(self, inplanes, planes, stride=1, dilation=1, downsample=None, bn_momentum=0.1, dimension=-1):
    super(BasicBlock, self).__init__()
    assert dimension > 0
    self.conv1 = ME.MinkowskiConvolution(inplanes, planes, kernel_size=3, stride=stride, dilation=dilation, dimension=dimension)
    self.norm1 = ME.MinkowskiBatchNorm(planes, momentum=bn_momentum)
    self.conv2 = ME.MinkowskiConvolution(planes, planes, kernel_size=3, stride=1, dilation=dilation, dimension=dimension)
    self.norm2 = ME.MinkowskiBatchNorm(planes, momentum=bn_momentum)
    self.relu = ME.MinkowskiReLU(inplace=True)
    self.downsample = downsample

class Bottleneck(nn.Module):
    expansion = 4

    def __init__(self, inplanes, planes, stride=1, dilation=1, downsample=None, bn_momentum=0.1, dimension=-1):
        super(Bottleneck, self).__init__()
        assert dimension > 0
        self.conv1 = ME.MinkowskiConvolution(inplanes, planes, kernel_size=1, dimension=dimension)
        self.norm1 = ME.MinkowskiBatchNorm(planes, momentum=bn_momentum)
        self.conv2 = ME.MinkowskiConvolution(planes, planes, kernel_size=3, stride=stride, dilation=dilation, dimension=dimension)
        self.norm2 = ME.MinkowskiBatchNorm(planes, momentum=bn_momentum)
        self.conv3 = ME.MinkowskiConvolution(planes, planes * self.expansion, kernel_size=1, dimension=dimension)
        self.norm3 = ME.MinkowskiBatchNorm(planes * self.expansion, momentum=bn_momentum)
        self.relu = ME.MinkowskiReLU(inplace=True)
        self.downsample = downsample

    def forward(self, x):
        residual = x
        out = self.conv1(x)
        out = self.norm1(out)
        out = self.relu(out)
        out = self.conv2(out)
        out = self.norm2(out)
        out = self.relu(out)
        out = self.conv3(out)
        out = self.norm3(out)
        if self.downsample is not None:
            residual = self.downsample(x)
        out += residual
        out = self.relu(out)
        return out

def __init__(self, inplanes, planes, stride=1, dilation=1, downsample=None, bn_momentum=0.1, dimension=-1):
    super(Bottleneck, self).__init__()
    assert dimension > 0
    self.conv1 = ME.MinkowskiConvolution(inplanes, planes, kernel_size=1, dimension=dimension)
    self.norm1 = ME.MinkowskiBatchNorm(planes, momentum=bn_momentum)
    self.conv2 = ME.MinkowskiConvolution(planes, planes, kernel_size=3, stride=stride, dilation=dilation, dimension=dimension)
    self.norm2 = ME.MinkowskiBatchNorm(planes, momentum=bn_momentum)
    self.conv3 = ME.MinkowskiConvolution(planes, planes * self.expansion, kernel_size=1, dimension=dimension)
    self.norm3 = ME.MinkowskiBatchNorm(planes * self.expansion, momentum=bn_momentum)
    self.relu = ME.MinkowskiReLU(inplace=True)
    self.downsample = downsample

class MinkUNetBase(nn.Module):
    BLOCK = None
    PLANES = None
    DILATIONS = (1, 1, 1, 1, 1, 1, 1, 1)
    LAYERS = (2, 2, 2, 2, 2, 2, 2, 2)
    PLANES = (32, 64, 128, 256, 256, 128, 96, 96)
    INIT_DIM = 32
    OUT_TENSOR_STRIDE = 1

    def __init__(self, in_channels, out_channels, dimension=3):
        super().__init__()
        self.D = dimension
        assert self.BLOCK is not None
        self.inplanes = self.INIT_DIM
        self.conv0p1s1 = ME.MinkowskiConvolution(in_channels, self.inplanes, kernel_size=5, dimension=self.D)
        self.bn0 = ME.MinkowskiBatchNorm(self.inplanes)
        self.conv1p1s2 = ME.MinkowskiConvolution(self.inplanes, self.inplanes, kernel_size=2, stride=2, dimension=self.D)
        self.bn1 = ME.MinkowskiBatchNorm(self.inplanes)
        self.block1 = self._make_layer(self.BLOCK, self.PLANES[0], self.LAYERS[0])
        self.conv2p2s2 = ME.MinkowskiConvolution(self.inplanes, self.inplanes, kernel_size=2, stride=2, dimension=self.D)
        self.bn2 = ME.MinkowskiBatchNorm(self.inplanes)
        self.block2 = self._make_layer(self.BLOCK, self.PLANES[1], self.LAYERS[1])
        self.conv3p4s2 = ME.MinkowskiConvolution(self.inplanes, self.inplanes, kernel_size=2, stride=2, dimension=self.D)
        self.bn3 = ME.MinkowskiBatchNorm(self.inplanes)
        self.block3 = self._make_layer(self.BLOCK, self.PLANES[2], self.LAYERS[2])
        self.conv4p8s2 = ME.MinkowskiConvolution(self.inplanes, self.inplanes, kernel_size=2, stride=2, dimension=self.D)
        self.bn4 = ME.MinkowskiBatchNorm(self.inplanes)
        self.block4 = self._make_layer(self.BLOCK, self.PLANES[3], self.LAYERS[3])
        self.convtr4p16s2 = ME.MinkowskiConvolutionTranspose(self.inplanes, self.PLANES[4], kernel_size=2, stride=2, dimension=self.D)
        self.bntr4 = ME.MinkowskiBatchNorm(self.PLANES[4])
        self.inplanes = self.PLANES[4] + self.PLANES[2] * self.BLOCK.expansion
        self.block5 = self._make_layer(self.BLOCK, self.PLANES[4], self.LAYERS[4])
        self.convtr5p8s2 = ME.MinkowskiConvolutionTranspose(self.inplanes, self.PLANES[5], kernel_size=2, stride=2, dimension=self.D)
        self.bntr5 = ME.MinkowskiBatchNorm(self.PLANES[5])
        self.inplanes = self.PLANES[5] + self.PLANES[1] * self.BLOCK.expansion
        self.block6 = self._make_layer(self.BLOCK, self.PLANES[5], self.LAYERS[5])
        self.convtr6p4s2 = ME.MinkowskiConvolutionTranspose(self.inplanes, self.PLANES[6], kernel_size=2, stride=2, dimension=self.D)
        self.bntr6 = ME.MinkowskiBatchNorm(self.PLANES[6])
        self.inplanes = self.PLANES[6] + self.PLANES[0] * self.BLOCK.expansion
        self.block7 = self._make_layer(self.BLOCK, self.PLANES[6], self.LAYERS[6])
        self.convtr7p2s2 = ME.MinkowskiConvolutionTranspose(self.inplanes, self.PLANES[7], kernel_size=2, stride=2, dimension=self.D)
        self.bntr7 = ME.MinkowskiBatchNorm(self.PLANES[7])
        self.inplanes = self.PLANES[7] + self.INIT_DIM
        self.block8 = self._make_layer(self.BLOCK, self.PLANES[7], self.LAYERS[7])
        self.final = ME.MinkowskiConvolution(self.PLANES[7] * self.BLOCK.expansion, out_channels, kernel_size=1, bias=True, dimension=self.D)
        self.relu = ME.MinkowskiReLU(inplace=True)
        self.weight_initialization()

    def weight_initialization(self):
        for m in self.modules():
            if isinstance(m, ME.MinkowskiConvolution):
                ME.utils.kaiming_normal_(m.kernel, mode='fan_out', nonlinearity='relu')
            if isinstance(m, ME.MinkowskiBatchNorm):
                nn.init.constant_(m.bn.weight, 1)
                nn.init.constant_(m.bn.bias, 0)

    def _make_layer(self, block, planes, blocks, stride=1, dilation=1, bn_momentum=0.1):
        downsample = None
        if stride != 1 or self.inplanes != planes * block.expansion:
            downsample = nn.Sequential(ME.MinkowskiConvolution(self.inplanes, planes * block.expansion, kernel_size=1, stride=stride, dimension=self.D), ME.MinkowskiBatchNorm(planes * block.expansion))
        layers = []
        layers.append(block(self.inplanes, planes, stride=stride, dilation=dilation, downsample=downsample, dimension=self.D))
        self.inplanes = planes * block.expansion
        for i in range(1, blocks):
            layers.append(block(self.inplanes, planes, stride=1, dilation=dilation, dimension=self.D))
        return nn.Sequential(*layers)

    def forward(self, input_dict):
        discrete_coord = input_dict['discrete_coord']
        feat = input_dict['feat']
        offset = input_dict['offset']
        batch = offset2batch(offset)
        in_field = ME.TensorField(feat, coordinates=torch.cat([batch.unsqueeze(-1).int(), discrete_coord.int()], dim=1), quantization_mode=ME.SparseTensorQuantizationMode.UNWEIGHTED_AVERAGE, minkowski_algorithm=ME.MinkowskiAlgorithm.SPEED_OPTIMIZED, device=feat.device)
        x = in_field.sparse()
        out = self.conv0p1s1(x)
        out = self.bn0(out)
        out_p1 = self.relu(out)
        out = self.conv1p1s2(out_p1)
        out = self.bn1(out)
        out = self.relu(out)
        out_b1p2 = self.block1(out)
        out = self.conv2p2s2(out_b1p2)
        out = self.bn2(out)
        out = self.relu(out)
        out_b2p4 = self.block2(out)
        out = self.conv3p4s2(out_b2p4)
        out = self.bn3(out)
        out = self.relu(out)
        out_b3p8 = self.block3(out)
        out = self.conv4p8s2(out_b3p8)
        out = self.bn4(out)
        out = self.relu(out)
        out = self.block4(out)
        out = self.convtr4p16s2(out)
        out = self.bntr4(out)
        out = self.relu(out)
        out = ME.cat(out, out_b3p8)
        out = self.block5(out)
        out = self.convtr5p8s2(out)
        out = self.bntr5(out)
        out = self.relu(out)
        out = ME.cat(out, out_b2p4)
        out = self.block6(out)
        out = self.convtr6p4s2(out)
        out = self.bntr6(out)
        out = self.relu(out)
        out = ME.cat(out, out_b1p2)
        out = self.block7(out)
        out = self.convtr7p2s2(out)
        out = self.bntr7(out)
        out = self.relu(out)
        out = ME.cat(out, out_p1)
        out = self.block8(out)
        return self.final(out).slice(in_field).F

def __init__(self, in_channels, out_channels, dimension=3):
    super().__init__()
    self.D = dimension
    assert self.BLOCK is not None
    self.inplanes = self.INIT_DIM
    self.conv0p1s1 = ME.MinkowskiConvolution(in_channels, self.inplanes, kernel_size=5, dimension=self.D)
    self.bn0 = ME.MinkowskiBatchNorm(self.inplanes)
    self.conv1p1s2 = ME.MinkowskiConvolution(self.inplanes, self.inplanes, kernel_size=2, stride=2, dimension=self.D)
    self.bn1 = ME.MinkowskiBatchNorm(self.inplanes)
    self.block1 = self._make_layer(self.BLOCK, self.PLANES[0], self.LAYERS[0])
    self.conv2p2s2 = ME.MinkowskiConvolution(self.inplanes, self.inplanes, kernel_size=2, stride=2, dimension=self.D)
    self.bn2 = ME.MinkowskiBatchNorm(self.inplanes)
    self.block2 = self._make_layer(self.BLOCK, self.PLANES[1], self.LAYERS[1])
    self.conv3p4s2 = ME.MinkowskiConvolution(self.inplanes, self.inplanes, kernel_size=2, stride=2, dimension=self.D)
    self.bn3 = ME.MinkowskiBatchNorm(self.inplanes)
    self.block3 = self._make_layer(self.BLOCK, self.PLANES[2], self.LAYERS[2])
    self.conv4p8s2 = ME.MinkowskiConvolution(self.inplanes, self.inplanes, kernel_size=2, stride=2, dimension=self.D)
    self.bn4 = ME.MinkowskiBatchNorm(self.inplanes)
    self.block4 = self._make_layer(self.BLOCK, self.PLANES[3], self.LAYERS[3])
    self.convtr4p16s2 = ME.MinkowskiConvolutionTranspose(self.inplanes, self.PLANES[4], kernel_size=2, stride=2, dimension=self.D)
    self.bntr4 = ME.MinkowskiBatchNorm(self.PLANES[4])
    self.inplanes = self.PLANES[4] + self.PLANES[2] * self.BLOCK.expansion
    self.block5 = self._make_layer(self.BLOCK, self.PLANES[4], self.LAYERS[4])
    self.convtr5p8s2 = ME.MinkowskiConvolutionTranspose(self.inplanes, self.PLANES[5], kernel_size=2, stride=2, dimension=self.D)
    self.bntr5 = ME.MinkowskiBatchNorm(self.PLANES[5])
    self.inplanes = self.PLANES[5] + self.PLANES[1] * self.BLOCK.expansion
    self.block6 = self._make_layer(self.BLOCK, self.PLANES[5], self.LAYERS[5])
    self.convtr6p4s2 = ME.MinkowskiConvolutionTranspose(self.inplanes, self.PLANES[6], kernel_size=2, stride=2, dimension=self.D)
    self.bntr6 = ME.MinkowskiBatchNorm(self.PLANES[6])
    self.inplanes = self.PLANES[6] + self.PLANES[0] * self.BLOCK.expansion
    self.block7 = self._make_layer(self.BLOCK, self.PLANES[6], self.LAYERS[6])
    self.convtr7p2s2 = ME.MinkowskiConvolutionTranspose(self.inplanes, self.PLANES[7], kernel_size=2, stride=2, dimension=self.D)
    self.bntr7 = ME.MinkowskiBatchNorm(self.PLANES[7])
    self.inplanes = self.PLANES[7] + self.INIT_DIM
    self.block8 = self._make_layer(self.BLOCK, self.PLANES[7], self.LAYERS[7])
    self.final = ME.MinkowskiConvolution(self.PLANES[7] * self.BLOCK.expansion, out_channels, kernel_size=1, bias=True, dimension=self.D)
    self.relu = ME.MinkowskiReLU(inplace=True)
    self.weight_initialization()

class BasicBlock(spconv.SparseModule):
    expansion = 1

    def __init__(self, in_channels, embed_channels, stride=1, norm_fn=None, indice_key=None, bias=False):
        super().__init__()
        assert norm_fn is not None
        if in_channels == embed_channels:
            self.proj = spconv.SparseSequential(nn.Identity())
        else:
            self.proj = spconv.SparseSequential(spconv.SubMConv3d(in_channels, embed_channels, kernel_size=1, bias=False), norm_fn(embed_channels))
        self.conv1 = spconv.SubMConv3d(in_channels, embed_channels, kernel_size=3, stride=stride, padding=1, bias=bias, indice_key=indice_key)
        self.bn1 = norm_fn(embed_channels)
        self.relu = nn.ReLU()
        self.conv2 = spconv.SubMConv3d(embed_channels, embed_channels, kernel_size=3, stride=stride, padding=1, bias=bias, indice_key=indice_key)
        self.bn2 = norm_fn(embed_channels)
        self.stride = stride

    def forward(self, x):
        residual = x
        out = self.conv1(x)
        out = out.replace_feature(self.bn1(out.features))
        out = out.replace_feature(self.relu(out.features))
        out = self.conv2(out)
        out = out.replace_feature(self.bn2(out.features))
        out = out.replace_feature(out.features + self.proj(residual).features)
        out = out.replace_feature(self.relu(out.features))
        return out

def __init__(self, in_channels, embed_channels, stride=1, norm_fn=None, indice_key=None, bias=False):
    super().__init__()
    assert norm_fn is not None
    if in_channels == embed_channels:
        self.proj = spconv.SparseSequential(nn.Identity())
    else:
        self.proj = spconv.SparseSequential(spconv.SubMConv3d(in_channels, embed_channels, kernel_size=1, bias=False), norm_fn(embed_channels))
    self.conv1 = spconv.SubMConv3d(in_channels, embed_channels, kernel_size=3, stride=stride, padding=1, bias=bias, indice_key=indice_key)
    self.bn1 = norm_fn(embed_channels)
    self.relu = nn.ReLU()
    self.conv2 = spconv.SubMConv3d(embed_channels, embed_channels, kernel_size=3, stride=stride, padding=1, bias=bias, indice_key=indice_key)
    self.bn2 = norm_fn(embed_channels)
    self.stride = stride

@MODELS.register_module()
class SpUNetBase(nn.Module):

    def __init__(self, in_channels, out_channels, base_channels=32, channels=(32, 64, 128, 256, 256, 128, 96, 96), layers=(2, 3, 4, 6, 2, 2, 2, 2)):
        super().__init__()
        assert len(layers) % 2 == 0
        assert len(layers) == len(channels)
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.base_channels = base_channels
        self.channels = channels
        self.layers = layers
        self.num_stages = len(layers) // 2
        norm_fn = partial(nn.BatchNorm1d, eps=0.001, momentum=0.01)
        block = BasicBlock
        self.conv_input = spconv.SparseSequential(spconv.SubMConv3d(in_channels, base_channels, kernel_size=5, padding=1, bias=False, indice_key='stem'), norm_fn(base_channels), nn.ReLU())
        enc_channels = base_channels
        dec_channels = channels[-1]
        self.down = nn.ModuleList()
        self.up = nn.ModuleList()
        self.enc = nn.ModuleList()
        self.dec = nn.ModuleList()
        for s in range(self.num_stages):
            self.down.append(spconv.SparseSequential(spconv.SparseConv3d(enc_channels, channels[s], kernel_size=2, stride=2, bias=False, indice_key=f'spconv{s + 1}'), norm_fn(channels[s]), nn.ReLU()))
            self.enc.append(spconv.SparseSequential(OrderedDict([(f'block{i}', block(channels[s], channels[s], norm_fn=norm_fn, indice_key=f'subm{s + 1}')) for i in range(layers[s])])))
            self.up.append(spconv.SparseSequential(spconv.SparseInverseConv3d(channels[len(channels) - s - 2], dec_channels, kernel_size=2, bias=False, indice_key=f'spconv{s + 1}'), norm_fn(dec_channels), nn.ReLU()))
            self.dec.append(spconv.SparseSequential(OrderedDict([(f'block{i}', block(dec_channels + enc_channels, dec_channels, norm_fn=norm_fn, indice_key=f'subm{s}')) if i == 0 else (f'block{i}', block(dec_channels, dec_channels, norm_fn=norm_fn, indice_key=f'subm{s}')) for i in range(layers[len(channels) - s - 1])])))
            enc_channels = channels[s]
            dec_channels = channels[len(channels) - s - 2]
        self.final = spconv.SubMConv3d(channels[-1], out_channels, kernel_size=1, padding=1, bias=True) if out_channels > 0 else spconv.Identity()
        self.apply(self._init_weights)

    @staticmethod
    def _init_weights(m):
        if isinstance(m, nn.Linear):
            trunc_normal_(m.weight, std=0.02)
            if m.bias is not None:
                nn.init.constant_(m.bias, 0)
        elif isinstance(m, spconv.SubMConv3d):
            trunc_normal_(m.weight, std=0.02)
            if m.bias is not None:
                nn.init.constant_(m.bias, 0)
        elif isinstance(m, nn.BatchNorm1d):
            nn.init.constant_(m.bias, 0)
            nn.init.constant_(m.weight, 1.0)

    def forward(self, input_dict):
        discrete_coord = input_dict['discrete_coord']
        feat = input_dict['feat']
        offset = input_dict['offset']
        batch = offset2batch(offset)
        sparse_shape = torch.add(torch.max(discrete_coord, dim=0).values, 1).tolist()
        x = spconv.SparseConvTensor(features=feat, indices=torch.cat([batch.unsqueeze(-1).int(), discrete_coord.int()], dim=1).contiguous(), spatial_shape=sparse_shape, batch_size=batch[-1].tolist() + 1)
        x = self.conv_input(x)
        skips = [x]
        for s in range(self.num_stages):
            x = self.down[s](x)
            x = self.enc[s](x)
            skips.append(x)
        x = skips.pop(-1)
        for s in reversed(range(self.num_stages)):
            x = self.up[s](x)
            skip = skips.pop(-1)
            x = x.replace_feature(torch.cat((x.features, skip.features), dim=1))
            x = self.dec[s](x)
        x = self.final(x)
        return x.features

def __init__(self, in_channels, out_channels, base_channels=32, channels=(32, 64, 128, 256, 256, 128, 96, 96), layers=(2, 3, 4, 6, 2, 2, 2, 2)):
    super().__init__()
    assert len(layers) % 2 == 0
    assert len(layers) == len(channels)
    self.in_channels = in_channels
    self.out_channels = out_channels
    self.base_channels = base_channels
    self.channels = channels
    self.layers = layers
    self.num_stages = len(layers) // 2
    norm_fn = partial(nn.BatchNorm1d, eps=0.001, momentum=0.01)
    block = BasicBlock
    self.conv_input = spconv.SparseSequential(spconv.SubMConv3d(in_channels, base_channels, kernel_size=5, padding=1, bias=False, indice_key='stem'), norm_fn(base_channels), nn.ReLU())
    enc_channels = base_channels
    dec_channels = channels[-1]
    self.down = nn.ModuleList()
    self.up = nn.ModuleList()
    self.enc = nn.ModuleList()
    self.dec = nn.ModuleList()
    for s in range(self.num_stages):
        self.down.append(spconv.SparseSequential(spconv.SparseConv3d(enc_channels, channels[s], kernel_size=2, stride=2, bias=False, indice_key=f'spconv{s + 1}'), norm_fn(channels[s]), nn.ReLU()))
        self.enc.append(spconv.SparseSequential(OrderedDict([(f'block{i}', block(channels[s], channels[s], norm_fn=norm_fn, indice_key=f'subm{s + 1}')) for i in range(layers[s])])))
        self.up.append(spconv.SparseSequential(spconv.SparseInverseConv3d(channels[len(channels) - s - 2], dec_channels, kernel_size=2, bias=False, indice_key=f'spconv{s + 1}'), norm_fn(dec_channels), nn.ReLU()))
        self.dec.append(spconv.SparseSequential(OrderedDict([(f'block{i}', block(dec_channels + enc_channels, dec_channels, norm_fn=norm_fn, indice_key=f'subm{s}')) if i == 0 else (f'block{i}', block(dec_channels, dec_channels, norm_fn=norm_fn, indice_key=f'subm{s}')) for i in range(layers[len(channels) - s - 1])])))
        enc_channels = channels[s]
        dec_channels = channels[len(channels) - s - 2]
    self.final = spconv.SubMConv3d(channels[-1], out_channels, kernel_size=1, padding=1, bias=True) if out_channels > 0 else spconv.Identity()
    self.apply(self._init_weights)

@MODELS.register_module()
class SpUNetNoSkipBase(nn.Module):

    def __init__(self, in_channels, out_channels, base_channels=32, channels=(32, 64, 128, 256, 256, 128, 96, 96), layers=(2, 3, 4, 6, 2, 2, 2, 2)):
        super().__init__()
        assert len(layers) % 2 == 0
        assert len(layers) == len(channels)
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.base_channels = base_channels
        self.channels = channels
        self.layers = layers
        self.num_stages = len(layers) // 2
        norm_fn = partial(nn.BatchNorm1d, eps=0.001, momentum=0.01)
        block = BasicBlock
        self.conv_input = spconv.SparseSequential(spconv.SubMConv3d(in_channels, base_channels, kernel_size=5, padding=1, bias=False, indice_key='stem'), norm_fn(base_channels), nn.ReLU())
        enc_channels = base_channels
        dec_channels = channels[-1]
        self.down = nn.ModuleList()
        self.up = nn.ModuleList()
        self.enc = nn.ModuleList()
        self.dec = nn.ModuleList()
        for s in range(self.num_stages):
            self.down.append(spconv.SparseSequential(spconv.SparseConv3d(enc_channels, channels[s], kernel_size=2, stride=2, bias=False, indice_key=f'spconv{s + 1}'), norm_fn(channels[s]), nn.ReLU()))
            self.enc.append(spconv.SparseSequential(OrderedDict([(f'block{i}', block(channels[s], channels[s], norm_fn=norm_fn, indice_key=f'subm{s + 1}')) for i in range(layers[s])])))
            self.up.append(spconv.SparseSequential(spconv.SparseInverseConv3d(channels[len(channels) - s - 2], dec_channels, kernel_size=2, bias=False, indice_key=f'spconv{s + 1}'), norm_fn(dec_channels), nn.ReLU()))
            self.dec.append(spconv.SparseSequential(OrderedDict([(f'block{i}', block(dec_channels, dec_channels, norm_fn=norm_fn, indice_key=f'subm{s}')) if i == 0 else (f'block{i}', block(dec_channels, dec_channels, norm_fn=norm_fn, indice_key=f'subm{s}')) for i in range(layers[len(channels) - s - 1])])))
            enc_channels = channels[s]
            dec_channels = channels[len(channels) - s - 2]
        self.final = spconv.SubMConv3d(channels[-1], out_channels, kernel_size=1, padding=1, bias=True) if out_channels > 0 else spconv.Identity()
        self.apply(self._init_weights)

    @staticmethod
    def _init_weights(m):
        if isinstance(m, nn.Linear):
            trunc_normal_(m.weight, std=0.02)
            if m.bias is not None:
                nn.init.constant_(m.bias, 0)
        elif isinstance(m, spconv.SubMConv3d):
            trunc_normal_(m.weight, std=0.02)
            if m.bias is not None:
                nn.init.constant_(m.bias, 0)
        elif isinstance(m, nn.BatchNorm1d):
            nn.init.constant_(m.bias, 0)
            nn.init.constant_(m.weight, 1.0)

    def forward(self, input_dict):
        discrete_coord = input_dict['discrete_coord']
        feat = input_dict['feat']
        offset = input_dict['offset']
        batch = offset2batch(offset)
        sparse_shape = torch.add(torch.max(discrete_coord, dim=0).values, 1).tolist()
        x = spconv.SparseConvTensor(features=feat, indices=torch.cat([batch.unsqueeze(-1).int(), discrete_coord.int()], dim=1).contiguous(), spatial_shape=sparse_shape, batch_size=batch[-1].tolist() + 1)
        x = self.conv_input(x)
        skips = [x]
        for s in range(self.num_stages):
            x = self.down[s](x)
            x = self.enc[s](x)
            skips.append(x)
        x = skips.pop(-1)
        for s in reversed(range(self.num_stages)):
            x = self.up[s](x)
            x = self.dec[s](x)
        x = self.final(x)
        return x.features

def __init__(self, in_channels, out_channels, base_channels=32, channels=(32, 64, 128, 256, 256, 128, 96, 96), layers=(2, 3, 4, 6, 2, 2, 2, 2)):
    super().__init__()
    assert len(layers) % 2 == 0
    assert len(layers) == len(channels)
    self.in_channels = in_channels
    self.out_channels = out_channels
    self.base_channels = base_channels
    self.channels = channels
    self.layers = layers
    self.num_stages = len(layers) // 2
    norm_fn = partial(nn.BatchNorm1d, eps=0.001, momentum=0.01)
    block = BasicBlock
    self.conv_input = spconv.SparseSequential(spconv.SubMConv3d(in_channels, base_channels, kernel_size=5, padding=1, bias=False, indice_key='stem'), norm_fn(base_channels), nn.ReLU())
    enc_channels = base_channels
    dec_channels = channels[-1]
    self.down = nn.ModuleList()
    self.up = nn.ModuleList()
    self.enc = nn.ModuleList()
    self.dec = nn.ModuleList()
    for s in range(self.num_stages):
        self.down.append(spconv.SparseSequential(spconv.SparseConv3d(enc_channels, channels[s], kernel_size=2, stride=2, bias=False, indice_key=f'spconv{s + 1}'), norm_fn(channels[s]), nn.ReLU()))
        self.enc.append(spconv.SparseSequential(OrderedDict([(f'block{i}', block(channels[s], channels[s], norm_fn=norm_fn, indice_key=f'subm{s + 1}')) for i in range(layers[s])])))
        self.up.append(spconv.SparseSequential(spconv.SparseInverseConv3d(channels[len(channels) - s - 2], dec_channels, kernel_size=2, bias=False, indice_key=f'spconv{s + 1}'), norm_fn(dec_channels), nn.ReLU()))
        self.dec.append(spconv.SparseSequential(OrderedDict([(f'block{i}', block(dec_channels, dec_channels, norm_fn=norm_fn, indice_key=f'subm{s}')) if i == 0 else (f'block{i}', block(dec_channels, dec_channels, norm_fn=norm_fn, indice_key=f'subm{s}')) for i in range(layers[len(channels) - s - 1])])))
        enc_channels = channels[s]
        dec_channels = channels[len(channels) - s - 2]
    self.final = spconv.SubMConv3d(channels[-1], out_channels, kernel_size=1, padding=1, bias=True) if out_channels > 0 else spconv.Identity()
    self.apply(self._init_weights)

class BasicConvolutionBlock(nn.Module):

    def __init__(self, inc, outc, ks=3, stride=1, dilation=1):
        super().__init__()
        self.net = nn.Sequential(spnn.Conv3d(inc, outc, kernel_size=ks, dilation=dilation, stride=stride), spnn.BatchNorm(outc), spnn.ReLU(True))

    def forward(self, x):
        out = self.net(x)
        return out

def __init__(self, inc, outc, ks=3, stride=1, dilation=1):
    super().__init__()
    self.net = nn.Sequential(spnn.Conv3d(inc, outc, kernel_size=ks, dilation=dilation, stride=stride), spnn.BatchNorm(outc), spnn.ReLU(True))

class BasicDeconvolutionBlock(nn.Module):

    def __init__(self, inc, outc, ks=3, stride=1):
        super().__init__()
        self.net = nn.Sequential(spnn.Conv3d(inc, outc, kernel_size=ks, stride=stride, transposed=True), spnn.BatchNorm(outc), spnn.ReLU(True))

    def forward(self, x):
        return self.net(x)

def __init__(self, inc, outc, ks=3, stride=1):
    super().__init__()
    self.net = nn.Sequential(spnn.Conv3d(inc, outc, kernel_size=ks, stride=stride, transposed=True), spnn.BatchNorm(outc), spnn.ReLU(True))

class ResidualBlock(nn.Module):

    def __init__(self, inc, outc, ks=3, stride=1, dilation=1):
        super().__init__()
        self.net = nn.Sequential(spnn.Conv3d(inc, outc, kernel_size=ks, dilation=dilation, stride=stride), spnn.BatchNorm(outc), spnn.ReLU(True), spnn.Conv3d(outc, outc, kernel_size=ks, dilation=dilation, stride=1), spnn.BatchNorm(outc))
        if inc == outc and stride == 1:
            self.downsample = nn.Identity()
        else:
            self.downsample = nn.Sequential(spnn.Conv3d(inc, outc, kernel_size=1, dilation=1, stride=stride), spnn.BatchNorm(outc))
        self.relu = spnn.ReLU(True)

    def forward(self, x):
        out = self.relu(self.net(x) + self.downsample(x))
        return out

def __init__(self, inc, outc, ks=3, stride=1, dilation=1):
    super().__init__()
    self.net = nn.Sequential(spnn.Conv3d(inc, outc, kernel_size=ks, dilation=dilation, stride=stride), spnn.BatchNorm(outc), spnn.ReLU(True), spnn.Conv3d(outc, outc, kernel_size=ks, dilation=dilation, stride=1), spnn.BatchNorm(outc))
    if inc == outc and stride == 1:
        self.downsample = nn.Identity()
    else:
        self.downsample = nn.Sequential(spnn.Conv3d(inc, outc, kernel_size=1, dilation=1, stride=stride), spnn.BatchNorm(outc))
    self.relu = spnn.ReLU(True)

@MODELS.register_module()
class SPVCNN(nn.Module):

    def __init__(self, in_channels, out_channels, base_channels=32, channels=(32, 64, 128, 256, 256, 128, 96, 96), layers=(2, 2, 2, 2, 2, 2, 2, 2)):
        super().__init__()
        assert len(layers) % 2 == 0
        assert len(layers) == len(channels)
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.base_channels = base_channels
        self.channels = channels
        self.layers = layers
        self.num_stages = len(layers) // 2
        self.stem = nn.Sequential(spnn.Conv3d(in_channels, base_channels, kernel_size=3, stride=1), spnn.BatchNorm(base_channels), spnn.ReLU(True), spnn.Conv3d(base_channels, base_channels, kernel_size=3, stride=1), spnn.BatchNorm(base_channels), spnn.ReLU(True))
        self.stage1 = nn.Sequential(*[BasicConvolutionBlock(base_channels, base_channels, ks=2, stride=2, dilation=1), ResidualBlock(base_channels, channels[0], ks=3, stride=1, dilation=1)] + [ResidualBlock(channels[0], channels[0], ks=3, stride=1, dilation=1) for _ in range(layers[0] - 1)])
        self.stage2 = nn.Sequential(*[BasicConvolutionBlock(channels[0], channels[0], ks=2, stride=2, dilation=1), ResidualBlock(channels[0], channels[1], ks=3, stride=1, dilation=1)] + [ResidualBlock(channels[1], channels[1], ks=3, stride=1, dilation=1) for _ in range(layers[1] - 1)])
        self.stage3 = nn.Sequential(*[BasicConvolutionBlock(channels[1], channels[1], ks=2, stride=2, dilation=1), ResidualBlock(channels[1], channels[2], ks=3, stride=1, dilation=1)] + [ResidualBlock(channels[2], channels[2], ks=3, stride=1, dilation=1) for _ in range(layers[2] - 1)])
        self.stage4 = nn.Sequential(*[BasicConvolutionBlock(channels[2], channels[2], ks=2, stride=2, dilation=1), ResidualBlock(channels[2], channels[3], ks=3, stride=1, dilation=1)] + [ResidualBlock(channels[3], channels[3], ks=3, stride=1, dilation=1) for _ in range(layers[3] - 1)])
        self.up1 = nn.ModuleList([BasicDeconvolutionBlock(channels[3], channels[4], ks=2, stride=2), nn.Sequential(*[ResidualBlock(channels[4] + channels[2], channels[4], ks=3, stride=1, dilation=1)] + [ResidualBlock(channels[4], channels[4], ks=3, stride=1, dilation=1) for _ in range(layers[4] - 1)])])
        self.up2 = nn.ModuleList([BasicDeconvolutionBlock(channels[4], channels[5], ks=2, stride=2), nn.Sequential(*[ResidualBlock(channels[5] + channels[1], channels[5], ks=3, stride=1, dilation=1)] + [ResidualBlock(channels[5], channels[5], ks=3, stride=1, dilation=1) for _ in range(layers[5] - 1)])])
        self.up3 = nn.ModuleList([BasicDeconvolutionBlock(channels[5], channels[6], ks=2, stride=2), nn.Sequential(*[ResidualBlock(channels[6] + channels[0], channels[6], ks=3, stride=1, dilation=1)] + [ResidualBlock(channels[6], channels[6], ks=3, stride=1, dilation=1) for _ in range(layers[6] - 1)])])
        self.up4 = nn.ModuleList([BasicDeconvolutionBlock(channels[6], channels[7], ks=2, stride=2), nn.Sequential(*[ResidualBlock(channels[7] + base_channels, channels[7], ks=3, stride=1, dilation=1)] + [ResidualBlock(channels[7], channels[7], ks=3, stride=1, dilation=1) for _ in range(layers[7] - 1)])])
        self.classifier = nn.Sequential(nn.Linear(channels[7], out_channels))
        self.point_transforms = nn.ModuleList([nn.Sequential(nn.Linear(base_channels, channels[3]), nn.BatchNorm1d(channels[3]), nn.ReLU(True)), nn.Sequential(nn.Linear(channels[3], channels[5]), nn.BatchNorm1d(channels[5]), nn.ReLU(True)), nn.Sequential(nn.Linear(channels[5], channels[7]), nn.BatchNorm1d(channels[7]), nn.ReLU(True))])
        self.weight_initialization()
        self.dropout = nn.Dropout(0.3, True)

    def weight_initialization(self):
        for m in self.modules():
            if isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)

    def forward(self, input_dict):
        discrete_coord = input_dict['discrete_coord']
        feat = input_dict['feat']
        offset = input_dict['offset']
        batch = offset2batch(offset)
        z = PointTensor(feat, torch.cat([discrete_coord.float(), batch.unsqueeze(-1).float()], dim=1).contiguous())
        x0 = initial_voxelize(z)
        x0 = self.stem(x0)
        z0 = voxel_to_point(x0, z, nearest=False)
        z0.F = z0.F
        x1 = point_to_voxel(x0, z0)
        x1 = self.stage1(x1)
        x2 = self.stage2(x1)
        x3 = self.stage3(x2)
        x4 = self.stage4(x3)
        z1 = voxel_to_point(x4, z0)
        z1.F = z1.F + self.point_transforms[0](z0.F)
        y1 = point_to_voxel(x4, z1)
        y1.F = self.dropout(y1.F)
        y1 = self.up1[0](y1)
        y1 = torchsparse.cat([y1, x3])
        y1 = self.up1[1](y1)
        y2 = self.up2[0](y1)
        y2 = torchsparse.cat([y2, x2])
        y2 = self.up2[1](y2)
        z2 = voxel_to_point(y2, z1)
        z2.F = z2.F + self.point_transforms[1](z1.F)
        y3 = point_to_voxel(y2, z2)
        y3.F = self.dropout(y3.F)
        y3 = self.up3[0](y3)
        y3 = torchsparse.cat([y3, x1])
        y3 = self.up3[1](y3)
        y4 = self.up4[0](y3)
        y4 = torchsparse.cat([y4, x0])
        y4 = self.up4[1](y4)
        z3 = voxel_to_point(y4, z2)
        z3.F = z3.F + self.point_transforms[2](z2.F)
        out = self.classifier(z3.F)
        return out

def __init__(self, in_channels, out_channels, base_channels=32, channels=(32, 64, 128, 256, 256, 128, 96, 96), layers=(2, 2, 2, 2, 2, 2, 2, 2)):
    super().__init__()
    assert len(layers) % 2 == 0
    assert len(layers) == len(channels)
    self.in_channels = in_channels
    self.out_channels = out_channels
    self.base_channels = base_channels
    self.channels = channels
    self.layers = layers
    self.num_stages = len(layers) // 2
    self.stem = nn.Sequential(spnn.Conv3d(in_channels, base_channels, kernel_size=3, stride=1), spnn.BatchNorm(base_channels), spnn.ReLU(True), spnn.Conv3d(base_channels, base_channels, kernel_size=3, stride=1), spnn.BatchNorm(base_channels), spnn.ReLU(True))
    self.stage1 = nn.Sequential(*[BasicConvolutionBlock(base_channels, base_channels, ks=2, stride=2, dilation=1), ResidualBlock(base_channels, channels[0], ks=3, stride=1, dilation=1)] + [ResidualBlock(channels[0], channels[0], ks=3, stride=1, dilation=1) for _ in range(layers[0] - 1)])
    self.stage2 = nn.Sequential(*[BasicConvolutionBlock(channels[0], channels[0], ks=2, stride=2, dilation=1), ResidualBlock(channels[0], channels[1], ks=3, stride=1, dilation=1)] + [ResidualBlock(channels[1], channels[1], ks=3, stride=1, dilation=1) for _ in range(layers[1] - 1)])
    self.stage3 = nn.Sequential(*[BasicConvolutionBlock(channels[1], channels[1], ks=2, stride=2, dilation=1), ResidualBlock(channels[1], channels[2], ks=3, stride=1, dilation=1)] + [ResidualBlock(channels[2], channels[2], ks=3, stride=1, dilation=1) for _ in range(layers[2] - 1)])
    self.stage4 = nn.Sequential(*[BasicConvolutionBlock(channels[2], channels[2], ks=2, stride=2, dilation=1), ResidualBlock(channels[2], channels[3], ks=3, stride=1, dilation=1)] + [ResidualBlock(channels[3], channels[3], ks=3, stride=1, dilation=1) for _ in range(layers[3] - 1)])
    self.up1 = nn.ModuleList([BasicDeconvolutionBlock(channels[3], channels[4], ks=2, stride=2), nn.Sequential(*[ResidualBlock(channels[4] + channels[2], channels[4], ks=3, stride=1, dilation=1)] + [ResidualBlock(channels[4], channels[4], ks=3, stride=1, dilation=1) for _ in range(layers[4] - 1)])])
    self.up2 = nn.ModuleList([BasicDeconvolutionBlock(channels[4], channels[5], ks=2, stride=2), nn.Sequential(*[ResidualBlock(channels[5] + channels[1], channels[5], ks=3, stride=1, dilation=1)] + [ResidualBlock(channels[5], channels[5], ks=3, stride=1, dilation=1) for _ in range(layers[5] - 1)])])
    self.up3 = nn.ModuleList([BasicDeconvolutionBlock(channels[5], channels[6], ks=2, stride=2), nn.Sequential(*[ResidualBlock(channels[6] + channels[0], channels[6], ks=3, stride=1, dilation=1)] + [ResidualBlock(channels[6], channels[6], ks=3, stride=1, dilation=1) for _ in range(layers[6] - 1)])])
    self.up4 = nn.ModuleList([BasicDeconvolutionBlock(channels[6], channels[7], ks=2, stride=2), nn.Sequential(*[ResidualBlock(channels[7] + base_channels, channels[7], ks=3, stride=1, dilation=1)] + [ResidualBlock(channels[7], channels[7], ks=3, stride=1, dilation=1) for _ in range(layers[7] - 1)])])
    self.classifier = nn.Sequential(nn.Linear(channels[7], out_channels))
    self.point_transforms = nn.ModuleList([nn.Sequential(nn.Linear(base_channels, channels[3]), nn.BatchNorm1d(channels[3]), nn.ReLU(True)), nn.Sequential(nn.Linear(channels[3], channels[5]), nn.BatchNorm1d(channels[5]), nn.ReLU(True)), nn.Sequential(nn.Linear(channels[5], channels[7]), nn.BatchNorm1d(channels[7]), nn.ReLU(True))])
    self.weight_initialization()
    self.dropout = nn.Dropout(0.3, True)

class Mlp(nn.Module):
    """ Multilayer perceptron."""

    def __init__(self, in_features, hidden_features=None, out_features=None, act_layer=nn.GELU, drop=0.0):
        super().__init__()
        out_features = out_features or in_features
        hidden_features = hidden_features or in_features
        self.fc1 = nn.Linear(in_features, hidden_features)
        self.act = act_layer()
        self.fc2 = nn.Linear(hidden_features, out_features)
        self.drop = nn.Dropout(drop, inplace=True)

    def forward(self, x):
        x = self.fc1(x)
        x = self.act(x)
        x = self.drop(x)
        x = self.fc2(x)
        x = self.drop(x)
        return x

def __init__(self, in_features, hidden_features=None, out_features=None, act_layer=nn.GELU, drop=0.0):
    super().__init__()
    out_features = out_features or in_features
    hidden_features = hidden_features or in_features
    self.fc1 = nn.Linear(in_features, hidden_features)
    self.act = act_layer()
    self.fc2 = nn.Linear(hidden_features, out_features)
    self.drop = nn.Dropout(drop, inplace=True)

class TransitionDown(nn.Module):

    def __init__(self, in_channels, out_channels, ratio, k, norm_layer=nn.LayerNorm):
        super().__init__()
        self.ratio = ratio
        self.k = k
        self.norm = norm_layer(in_channels) if norm_layer else None
        self.linear = nn.Linear(in_channels, out_channels, bias=False)
        self.pool = nn.MaxPool1d(k)

    def forward(self, feats, xyz, offset):
        n_offset, count = ([int(offset[0].item() * self.ratio) + 1], int(offset[0].item() * self.ratio) + 1)
        for i in range(1, offset.shape[0]):
            count += (offset[i].item() - offset[i - 1].item()) * self.ratio + 1
            n_offset.append(count)
        n_offset = torch.cuda.IntTensor(n_offset)
        idx = pointops.furthestsampling(xyz, offset, n_offset)
        n_xyz = xyz[idx.long(), :]
        feats = pointops.queryandgroup(self.k, xyz, n_xyz, feats, None, offset, n_offset, use_xyz=False)
        m, k, c = feats.shape
        feats = self.linear(self.norm(feats.view(m * k, c)).view(m, k, c)).transpose(1, 2).contiguous()
        feats = self.pool(feats).squeeze(-1)
        return (feats, n_xyz, n_offset)

def __init__(self, in_channels, out_channels, ratio, k, norm_layer=nn.LayerNorm):
    super().__init__()
    self.ratio = ratio
    self.k = k
    self.norm = norm_layer(in_channels) if norm_layer else None
    self.linear = nn.Linear(in_channels, out_channels, bias=False)
    self.pool = nn.MaxPool1d(k)

class WindowAttention(nn.Module):
    """ Window based multi-head self attention (W-MSA) module with relative position bias.
    It supports both of shifted and non-shifted window.

    Args:
        dim (int): Number of input channels.
        window_size (tuple[int]): The height and width of the window.
        num_heads (int): Number of attention heads.
        qkv_bias (bool, optional):  If True, add a learnable bias to query, key, value. Default: True
        qk_scale (float | None, optional): Override default qk scale of head_dim ** -0.5 if set
        attn_drop (float, optional): Dropout ratio of attention weight. Default: 0.0
        proj_drop (float, optional): Dropout ratio of output. Default: 0.0
    """

    def __init__(self, dim, window_size, num_heads, quant_size, rel_query=True, rel_key=False, rel_value=False, qkv_bias=True, qk_scale=None, attn_drop=0.0, proj_drop=0.0):
        super().__init__()
        self.dim = dim
        self.num_heads = num_heads
        head_dim = dim // num_heads
        self.scale = qk_scale or head_dim ** (-0.5)
        self.window_size = window_size
        self.quant_size = quant_size
        self.rel_query = rel_query
        self.rel_key = rel_key
        self.rel_value = rel_value
        quant_grid_length = int((2 * window_size + 0.0001) // quant_size)
        if rel_query:
            self.relative_pos_query_table = nn.Parameter(torch.zeros(2 * quant_grid_length, num_heads, head_dim, 3))
            trunc_normal_(self.relative_pos_query_table, std=0.02)
        if rel_key:
            self.relative_pos_key_table = nn.Parameter(torch.zeros(2 * quant_grid_length, num_heads, head_dim, 3))
            trunc_normal_(self.relative_pos_key_table, std=0.02)
        if rel_value:
            self.relative_pos_value_table = nn.Parameter(torch.zeros(2 * quant_grid_length, num_heads, head_dim, 3))
            trunc_normal_(self.relative_pos_value_table, std=0.02)
        self.quant_grid_length = quant_grid_length
        self.qkv = nn.Linear(dim, dim * 3, bias=qkv_bias)
        self.attn_drop = nn.Dropout(attn_drop, inplace=True)
        self.proj = nn.Linear(dim, dim)
        self.proj_drop = nn.Dropout(proj_drop, inplace=True)
        self.softmax = nn.Softmax(dim=-1)

    def forward(self, feats, xyz, index_0, index_1, index_0_offsets, n_max):
        """ Forward function.

        Args:
            feats: N, C
            xyz: N, 3
            index_0: M,
            index_1: M,
        """
        N, C = feats.shape
        M = index_0.shape[0]
        assert index_0.shape[0] == index_1.shape[0]
        qkv = self.qkv(feats).reshape(N, 3, self.num_heads, C // self.num_heads).permute(1, 0, 2, 3).contiguous()
        query, key, value = (qkv[0], qkv[1], qkv[2])
        query = query * self.scale
        attn_flat = pointops.attention_step1_v2(query.float(), key.float(), index_1.int(), index_0_offsets.int(), n_max)
        relative_position = xyz[index_0] - xyz[index_1]
        relative_position = torch.round(relative_position * 100000) / 100000
        relative_position_index = (relative_position + 2 * self.window_size - 0.0001) // self.quant_size
        assert (relative_position_index >= 0).all()
        assert (relative_position_index <= 2 * self.quant_grid_length - 1).all()
        assert self.rel_query and self.rel_key
        if self.rel_query and self.rel_key:
            relative_position_bias = pointops.dot_prod_with_idx_v3(query.float(), index_0_offsets.int(), n_max, key.float(), index_1.int(), self.relative_pos_query_table.float(), self.relative_pos_key_table.float(), relative_position_index.int())
        elif self.rel_query:
            relative_position_bias = pointops.dot_prod_with_idx(query.float(), index_0.int(), self.relative_pos_query_table.float(), relative_position_index.int())
        elif self.rel_key:
            relative_position_bias = pointops.dot_prod_with_idx(key.float(), index_1.int(), self.relative_pos_key_table.float(), relative_position_index.int())
        else:
            relative_position_bias = 0.0
        attn_flat = attn_flat + relative_position_bias
        softmax_attn_flat = scatter_softmax(src=attn_flat, index=index_0, dim=0)
        if self.rel_value:
            x = pointops.attention_step2_with_rel_pos_value_v2(softmax_attn_flat.float(), value.float(), index_0_offsets.int(), n_max, index_1.int(), self.relative_pos_value_table.float(), relative_position_index.int())
        else:
            x = pointops.attention_step2(softmax_attn_flat.float(), value.float(), index_0.int(), index_1.int())
        x = x.view(N, C)
        x = self.proj(x)
        x = self.proj_drop(x)
        return x

def __init__(self, dim, window_size, num_heads, quant_size, rel_query=True, rel_key=False, rel_value=False, qkv_bias=True, qk_scale=None, attn_drop=0.0, proj_drop=0.0):
    super().__init__()
    self.dim = dim
    self.num_heads = num_heads
    head_dim = dim // num_heads
    self.scale = qk_scale or head_dim ** (-0.5)
    self.window_size = window_size
    self.quant_size = quant_size
    self.rel_query = rel_query
    self.rel_key = rel_key
    self.rel_value = rel_value
    quant_grid_length = int((2 * window_size + 0.0001) // quant_size)
    if rel_query:
        self.relative_pos_query_table = nn.Parameter(torch.zeros(2 * quant_grid_length, num_heads, head_dim, 3))
        trunc_normal_(self.relative_pos_query_table, std=0.02)
    if rel_key:
        self.relative_pos_key_table = nn.Parameter(torch.zeros(2 * quant_grid_length, num_heads, head_dim, 3))
        trunc_normal_(self.relative_pos_key_table, std=0.02)
    if rel_value:
        self.relative_pos_value_table = nn.Parameter(torch.zeros(2 * quant_grid_length, num_heads, head_dim, 3))
        trunc_normal_(self.relative_pos_value_table, std=0.02)
    self.quant_grid_length = quant_grid_length
    self.qkv = nn.Linear(dim, dim * 3, bias=qkv_bias)
    self.attn_drop = nn.Dropout(attn_drop, inplace=True)
    self.proj = nn.Linear(dim, dim)
    self.proj_drop = nn.Dropout(proj_drop, inplace=True)
    self.softmax = nn.Softmax(dim=-1)

class SwinTransformerBlock(nn.Module):

    def __init__(self, dim, num_heads, window_size, quant_size, rel_query=True, rel_key=False, rel_value=False, drop_path=0.0, mlp_ratio=4.0, qkv_bias=True, qk_scale=None, act_layer=nn.GELU, norm_layer=nn.LayerNorm, mode=4):
        super().__init__()
        self.mode = mode
        self.norm1 = norm_layer(dim)
        self.attn = WindowAttention(dim, window_size, num_heads=num_heads, quant_size=quant_size, rel_query=rel_query, rel_key=rel_key, rel_value=rel_value, qkv_bias=qkv_bias, qk_scale=qk_scale)
        self.drop_path = DropPath(drop_path) if drop_path > 0.0 else nn.Identity()
        self.norm2 = norm_layer(dim)
        mlp_hidden_dim = int(dim * mlp_ratio)
        self.mlp = Mlp(in_features=dim, hidden_features=mlp_hidden_dim, act_layer=act_layer)

    def forward(self, feats, xyz, index_0, index_1, index_0_offsets, n_max):
        short_cut = feats
        feats = self.norm1(feats)
        feats = self.attn(feats, xyz, index_0, index_1, index_0_offsets, n_max)
        feats = short_cut + self.drop_path(feats)
        feats = feats + self.drop_path(self.mlp(self.norm2(feats)))
        return feats

def __init__(self, dim, num_heads, window_size, quant_size, rel_query=True, rel_key=False, rel_value=False, drop_path=0.0, mlp_ratio=4.0, qkv_bias=True, qk_scale=None, act_layer=nn.GELU, norm_layer=nn.LayerNorm, mode=4):
    super().__init__()
    self.mode = mode
    self.norm1 = norm_layer(dim)
    self.attn = WindowAttention(dim, window_size, num_heads=num_heads, quant_size=quant_size, rel_query=rel_query, rel_key=rel_key, rel_value=rel_value, qkv_bias=qkv_bias, qk_scale=qk_scale)
    self.drop_path = DropPath(drop_path) if drop_path > 0.0 else nn.Identity()
    self.norm2 = norm_layer(dim)
    mlp_hidden_dim = int(dim * mlp_ratio)
    self.mlp = Mlp(in_features=dim, hidden_features=mlp_hidden_dim, act_layer=act_layer)

class BasicLayer(nn.Module):

    def __init__(self, downsample_scale, depth, channel, num_heads, window_size, grid_size, quant_size, rel_query=True, rel_key=False, rel_value=False, drop_path=0.0, mlp_ratio=4.0, qkv_bias=True, qk_scale=None, norm_layer=nn.LayerNorm, downsample=None, ratio=0.25, k=16, out_channels=None):
        super().__init__()
        self.depth = depth
        self.grid_size = grid_size
        self.max_window_counts = 64
        self.window_size = window_size
        self.downsample_scale = downsample_scale
        self.blocks = nn.ModuleList([SwinTransformerBlock(channel, num_heads, window_size, quant_size, rel_query=rel_query, rel_key=rel_key, rel_value=rel_value, drop_path=drop_path[i] if isinstance(drop_path, list) else drop_path, mlp_ratio=mlp_ratio, qkv_bias=qkv_bias, qk_scale=qk_scale, norm_layer=norm_layer) for i in range(depth)])
        self.downsample = downsample(channel, out_channels, ratio, k) if downsample else None

    def forward(self, feats, xyz, offset):
        window_size = torch.tensor([self.window_size] * 3).type_as(xyz).to(xyz.device)
        offset_ = offset.clone()
        offset_[1:] = offset_[1:] - offset_[:-1]
        batch = torch.cat([torch.tensor([ii] * o) for ii, o in enumerate(offset_)], 0).long().cuda()
        v2p_map, p2v_map, counts = grid_sample(xyz, batch, window_size, start=None)
        shift_size = 1 / 2 * window_size
        shift_v2p_map, shift_p2v_map, shift_counts = grid_sample(xyz + shift_size, batch, window_size, start=xyz.min(0)[0])
        downsample_scale = self.downsample_scale
        new_offset, count = ([offset[0].item() // downsample_scale + 1], offset[0].item() // downsample_scale + 1)
        for i in range(1, offset.shape[0]):
            count += (offset[i].item() - offset[i - 1].item()) // downsample_scale + 1
            new_offset.append(count)
        new_offset = torch.cuda.IntTensor(new_offset)
        downsample_idx = pointops.furthestsampling(xyz, offset.int(), new_offset.int())
        new_window_size = 2 * torch.tensor([self.window_size] * 3).type_as(xyz).to(xyz.device)
        new_v2p_map, new_p2v_map, new_counts = grid_sample(xyz, batch, new_window_size, start=None)
        shift_size = 1 / 2 * new_window_size
        shift_new_v2p_map, shift_new_p2v_map, shift_new_counts = grid_sample(xyz + shift_size, batch, new_window_size, start=xyz.min(0)[0])
        for i, blk in enumerate(self.blocks):
            p2v_map_blk = p2v_map if i % 2 == 0 else shift_p2v_map
            counts_blk = counts if i % 2 == 0 else shift_counts
            new_p2v_map_blk = new_p2v_map if i % 2 == 0 else shift_new_p2v_map
            new_counts_blk = new_counts if i % 2 == 0 else shift_new_counts
            index_0, index_1 = get_indice_pairs(p2v_map_blk, counts_blk, new_p2v_map_blk, new_counts_blk, downsample_idx, batch, xyz, window_size, i)
            index_0, indices = torch.sort(index_0)
            index_1 = index_1[indices]
            index_0_counts = index_0.bincount()
            n_max = index_0_counts.max()
            index_0_offsets = index_0_counts.cumsum(dim=-1)
            index_0_offsets = torch.cat([torch.zeros(1, dtype=torch.long).cuda(), index_0_offsets], 0)
            feats = blk(feats, xyz, index_0, index_1, index_0_offsets, n_max)
        if self.downsample:
            feats_down, xyz_down, offset_down = self.downsample(feats, xyz, offset)
        else:
            feats_down, xyz_down, offset_down = (None, None, None)
        return (feats, xyz, offset, feats_down, xyz_down, offset_down)

def __init__(self, downsample_scale, depth, channel, num_heads, window_size, grid_size, quant_size, rel_query=True, rel_key=False, rel_value=False, drop_path=0.0, mlp_ratio=4.0, qkv_bias=True, qk_scale=None, norm_layer=nn.LayerNorm, downsample=None, ratio=0.25, k=16, out_channels=None):
    super().__init__()
    self.depth = depth
    self.grid_size = grid_size
    self.max_window_counts = 64
    self.window_size = window_size
    self.downsample_scale = downsample_scale
    self.blocks = nn.ModuleList([SwinTransformerBlock(channel, num_heads, window_size, quant_size, rel_query=rel_query, rel_key=rel_key, rel_value=rel_value, drop_path=drop_path[i] if isinstance(drop_path, list) else drop_path, mlp_ratio=mlp_ratio, qkv_bias=qkv_bias, qk_scale=qk_scale, norm_layer=norm_layer) for i in range(depth)])
    self.downsample = downsample(channel, out_channels, ratio, k) if downsample else None

class Upsample(nn.Module):

    def __init__(self, k, in_channels, out_channels, bn_momentum=0.02):
        super().__init__()
        self.k = k
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.linear1 = nn.Sequential(nn.LayerNorm(out_channels), nn.Linear(out_channels, out_channels))
        self.linear2 = nn.Sequential(nn.LayerNorm(in_channels), nn.Linear(in_channels, out_channels))

    def forward(self, feats, xyz, support_xyz, offset, support_offset, support_feats=None):
        feats = self.linear1(support_feats) + pointops.interpolation(xyz, support_xyz, self.linear2(feats), offset, support_offset)
        return (feats, support_xyz, support_offset)

def __init__(self, k, in_channels, out_channels, bn_momentum=0.02):
    super().__init__()
    self.k = k
    self.in_channels = in_channels
    self.out_channels = out_channels
    self.linear1 = nn.Sequential(nn.LayerNorm(out_channels), nn.Linear(out_channels, out_channels))
    self.linear2 = nn.Sequential(nn.LayerNorm(in_channels), nn.Linear(in_channels, out_channels))

class KPConvSimpleBlock(nn.Module):

    def __init__(self, in_channels, out_channels, prev_grid_size, sigma=1.0, negative_slope=0.2, bn_momentum=0.02):
        super().__init__()
        self.kpconv = KPConvLayer(in_channels, out_channels, point_influence=prev_grid_size * sigma, add_one=False)
        self.bn = FastBatchNorm1d(out_channels, momentum=bn_momentum)
        self.activation = nn.LeakyReLU(negative_slope=negative_slope)

    def forward(self, feats, xyz, batch, neighbor_idx):
        feats = self.kpconv(xyz, xyz, neighbor_idx, feats)
        feats = self.activation(self.bn(feats))
        return feats

def __init__(self, in_channels, out_channels, prev_grid_size, sigma=1.0, negative_slope=0.2, bn_momentum=0.02):
    super().__init__()
    self.kpconv = KPConvLayer(in_channels, out_channels, point_influence=prev_grid_size * sigma, add_one=False)
    self.bn = FastBatchNorm1d(out_channels, momentum=bn_momentum)
    self.activation = nn.LeakyReLU(negative_slope=negative_slope)

class KPConvResBlock(nn.Module):

    def __init__(self, in_channels, out_channels, prev_grid_size, sigma=1.0, negative_slope=0.2, bn_momentum=0.02):
        super().__init__()
        d_2 = out_channels // 4
        activation = nn.LeakyReLU(negative_slope=negative_slope)
        self.unary_1 = torch.nn.Sequential(nn.Linear(in_channels, d_2, bias=False), FastBatchNorm1d(d_2, momentum=bn_momentum), activation)
        self.unary_2 = torch.nn.Sequential(nn.Linear(d_2, out_channels, bias=False), FastBatchNorm1d(out_channels, momentum=bn_momentum), activation)
        self.kpconv = KPConvLayer(d_2, d_2, point_influence=prev_grid_size * sigma, add_one=False)
        self.bn = FastBatchNorm1d(out_channels, momentum=bn_momentum)
        self.activation = activation
        if in_channels != out_channels:
            self.shortcut_op = torch.nn.Sequential(nn.Linear(in_channels, out_channels, bias=False), FastBatchNorm1d(out_channels, momentum=bn_momentum))
        else:
            self.shortcut_op = nn.Identity()

    def forward(self, feats, xyz, batch, neighbor_idx):
        shortcut = feats
        feats = self.unary_1(feats)
        feats = self.kpconv(xyz, xyz, neighbor_idx, feats)
        feats = self.unary_2(feats)
        shortcut = self.shortcut_op(shortcut)
        feats += shortcut
        return feats

def __init__(self, in_channels, out_channels, prev_grid_size, sigma=1.0, negative_slope=0.2, bn_momentum=0.02):
    super().__init__()
    d_2 = out_channels // 4
    activation = nn.LeakyReLU(negative_slope=negative_slope)
    self.unary_1 = torch.nn.Sequential(nn.Linear(in_channels, d_2, bias=False), FastBatchNorm1d(d_2, momentum=bn_momentum), activation)
    self.unary_2 = torch.nn.Sequential(nn.Linear(d_2, out_channels, bias=False), FastBatchNorm1d(out_channels, momentum=bn_momentum), activation)
    self.kpconv = KPConvLayer(d_2, d_2, point_influence=prev_grid_size * sigma, add_one=False)
    self.bn = FastBatchNorm1d(out_channels, momentum=bn_momentum)
    self.activation = activation
    if in_channels != out_channels:
        self.shortcut_op = torch.nn.Sequential(nn.Linear(in_channels, out_channels, bias=False), FastBatchNorm1d(out_channels, momentum=bn_momentum))
    else:
        self.shortcut_op = nn.Identity()

@MODELS.register_module('stv1m1')
class StratifiedTransformer(nn.Module):

    def __init__(self, downsample_scale, depths, channels, num_heads, window_size, up_k, grid_sizes, quant_sizes, rel_query=True, rel_key=False, rel_value=False, drop_path_rate=0.2, num_layers=4, concat_xyz=False, num_classes=13, ratio=0.25, k=16, prev_grid_size=0.04, sigma=1.0, stem_transformer=False, kp_ball_radius=0.02 * 2.5, kp_max_neighbor=34):
        super().__init__()
        dpr = [x.item() for x in torch.linspace(0, drop_path_rate, sum(depths))]
        self.kp_ball_radius = kp_ball_radius
        self.kp_max_neighbor = kp_max_neighbor
        if stem_transformer:
            self.stem_layer = nn.ModuleList([KPConvSimpleBlock(3 if not concat_xyz else 6, channels[0], prev_grid_size, sigma=sigma)])
            self.layer_start = 0
        else:
            self.stem_layer = nn.ModuleList([KPConvSimpleBlock(3 if not concat_xyz else 6, channels[0], prev_grid_size, sigma=sigma), KPConvResBlock(channels[0], channels[0], prev_grid_size, sigma=sigma)])
            self.downsample = TransitionDown(channels[0], channels[1], ratio, k)
            self.layer_start = 1
        self.layers = nn.ModuleList([BasicLayer(downsample_scale, depths[i], channels[i], num_heads[i], window_size[i], grid_sizes[i], quant_sizes[i], rel_query=rel_query, rel_key=rel_key, rel_value=rel_value, drop_path=dpr[sum(depths[:i]):sum(depths[:i + 1])], downsample=TransitionDown if i < num_layers - 1 else None, ratio=ratio, k=k, out_channels=channels[i + 1] if i < num_layers - 1 else None) for i in range(self.layer_start, num_layers)])
        self.upsamples = nn.ModuleList([Upsample(up_k, channels[i], channels[i - 1]) for i in range(num_layers - 1, 0, -1)])
        self.classifier = nn.Sequential(nn.Linear(channels[0], channels[0]), nn.BatchNorm1d(channels[0]), nn.ReLU(inplace=True), nn.Linear(channels[0], num_classes))
        self.init_weights()

    def forward(self, input_dict):
        feats = input_dict['feat']
        xyz = input_dict['coord']
        offset = input_dict['offset'].int()
        batch = offset2batch(offset)
        neighbor_idx = tp.ball_query(self.kp_ball_radius, self.kp_max_neighbor, xyz, xyz, mode='partial_dense', batch_x=batch, batch_y=batch)[0]
        feats_stack = []
        xyz_stack = []
        offset_stack = []
        for i, layer in enumerate(self.stem_layer):
            feats = layer(feats, xyz, batch, neighbor_idx)
        feats = feats.contiguous()
        if self.layer_start == 1:
            feats_stack.append(feats)
            xyz_stack.append(xyz)
            offset_stack.append(offset)
            feats, xyz, offset = self.downsample(feats, xyz, offset)
        for i, layer in enumerate(self.layers):
            feats, xyz, offset, feats_down, xyz_down, offset_down = layer(feats, xyz, offset)
            feats_stack.append(feats)
            xyz_stack.append(xyz)
            offset_stack.append(offset)
            feats = feats_down
            xyz = xyz_down
            offset = offset_down
        feats = feats_stack.pop()
        xyz = xyz_stack.pop()
        offset = offset_stack.pop()
        for i, upsample in enumerate(self.upsamples):
            feats, xyz, offset = upsample(feats, xyz, xyz_stack.pop(), offset, offset_stack.pop(), support_feats=feats_stack.pop())
        out = self.classifier(feats)
        return out

    def init_weights(self):
        """Initialize the weights in backbone.
        """

        def _init_weights(m):
            if isinstance(m, nn.Linear):
                trunc_normal_(m.weight, std=0.02)
                if isinstance(m, nn.Linear) and m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.LayerNorm) or isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.bias, 0)
                nn.init.constant_(m.weight, 1.0)
        self.apply(_init_weights)

def __init__(self, downsample_scale, depths, channels, num_heads, window_size, up_k, grid_sizes, quant_sizes, rel_query=True, rel_key=False, rel_value=False, drop_path_rate=0.2, num_layers=4, concat_xyz=False, num_classes=13, ratio=0.25, k=16, prev_grid_size=0.04, sigma=1.0, stem_transformer=False, kp_ball_radius=0.02 * 2.5, kp_max_neighbor=34):
    super().__init__()
    dpr = [x.item() for x in torch.linspace(0, drop_path_rate, sum(depths))]
    self.kp_ball_radius = kp_ball_radius
    self.kp_max_neighbor = kp_max_neighbor
    if stem_transformer:
        self.stem_layer = nn.ModuleList([KPConvSimpleBlock(3 if not concat_xyz else 6, channels[0], prev_grid_size, sigma=sigma)])
        self.layer_start = 0
    else:
        self.stem_layer = nn.ModuleList([KPConvSimpleBlock(3 if not concat_xyz else 6, channels[0], prev_grid_size, sigma=sigma), KPConvResBlock(channels[0], channels[0], prev_grid_size, sigma=sigma)])
        self.downsample = TransitionDown(channels[0], channels[1], ratio, k)
        self.layer_start = 1
    self.layers = nn.ModuleList([BasicLayer(downsample_scale, depths[i], channels[i], num_heads[i], window_size[i], grid_sizes[i], quant_sizes[i], rel_query=rel_query, rel_key=rel_key, rel_value=rel_value, drop_path=dpr[sum(depths[:i]):sum(depths[:i + 1])], downsample=TransitionDown if i < num_layers - 1 else None, ratio=ratio, k=k, out_channels=channels[i + 1] if i < num_layers - 1 else None) for i in range(self.layer_start, num_layers)])
    self.upsamples = nn.ModuleList([Upsample(up_k, channels[i], channels[i - 1]) for i in range(num_layers - 1, 0, -1)])
    self.classifier = nn.Sequential(nn.Linear(channels[0], channels[0]), nn.BatchNorm1d(channels[0]), nn.ReLU(inplace=True), nn.Linear(channels[0], num_classes))
    self.init_weights()

def init_weights(self):
    """Initialize the weights in backbone.
        """

    def _init_weights(m):
        if isinstance(m, nn.Linear):
            trunc_normal_(m.weight, std=0.02)
            if isinstance(m, nn.Linear) and m.bias is not None:
                nn.init.constant_(m.bias, 0)
        elif isinstance(m, nn.LayerNorm) or isinstance(m, nn.BatchNorm1d):
            nn.init.constant_(m.bias, 0)
            nn.init.constant_(m.weight, 1.0)
    self.apply(_init_weights)

class WindowAttention(nn.Module):
    """ Window based multi-head self attention (W-MSA) module with relative position bias.
    It supports both of shifted and non-shifted window.
    """

    def __init__(self, embed_channels, num_heads, window_size, quant_size, attn_drop=0.0, proj_drop=0.0, scale=None, rel_query=True, rel_key=True, rel_value=True, qkv_bias=True):
        super().__init__()
        self.embed_channels = embed_channels
        self.head_channels = embed_channels // num_heads
        self.num_heads = num_heads
        self.scale = scale or self.head_channels ** (-0.5)
        self.window_size = window_size
        self.quant_size = quant_size
        self.rel_query = rel_query
        self.rel_key = rel_key
        self.rel_value = rel_value
        self.quant_grid_length = int((2 * window_size + 0.0001) // quant_size)
        assert self.rel_query and self.rel_key
        if rel_query:
            self.relative_pos_query_table = nn.Parameter(torch.zeros(2 * self.quant_grid_length, self.num_heads, self.head_channels, 3))
            trunc_normal_(self.relative_pos_query_table, std=0.02)
        if rel_key:
            self.relative_pos_key_table = nn.Parameter(torch.zeros(2 * self.quant_grid_length, self.num_heads, self.head_channels, 3))
            trunc_normal_(self.relative_pos_query_table, std=0.02)
        if rel_value:
            self.relative_pos_value_table = nn.Parameter(torch.zeros(2 * self.quant_grid_length, self.num_heads, self.head_channels, 3))
            trunc_normal_(self.relative_pos_query_table, std=0.02)
        self.qkv = nn.Linear(embed_channels, embed_channels * 3, bias=qkv_bias)
        self.attn_drop = nn.Dropout(attn_drop, inplace=True)
        self.proj = nn.Linear(embed_channels, embed_channels)
        self.proj_drop = nn.Dropout(proj_drop, inplace=True)
        self.softmax = nn.Softmax(dim=-1)

    def forward(self, feats, coords, index_0, index_1, index_0_offsets, n_max):
        n, c = feats.shape
        m = index_0.shape[0]
        assert index_0.shape[0] == index_1.shape[0]
        qkv = self.qkv(feats).reshape(n, 3, self.num_heads, c // self.num_heads).permute(1, 0, 2, 3).contiguous()
        query, key, value = (qkv[0], qkv[1], qkv[2])
        query = query * self.scale
        attn_flat = pointops.attention_step1_v2(query.float(), key.float(), index_1.int(), index_0_offsets.int(), n_max)
        relative_position = coords[index_0] - coords[index_1]
        relative_position = torch.round(relative_position * 100000) / 100000
        relative_position_index = torch.div(relative_position + 2 * self.window_size - 0.0001, self.quant_size, rounding_mode='trunc')
        assert (relative_position_index >= 0).all()
        assert (relative_position_index <= 2 * self.quant_grid_length - 1).all()
        if self.rel_query and self.rel_key:
            relative_position_bias = pointops.dot_prod_with_idx_v3(query.float(), index_0_offsets.int(), n_max, key.float(), index_1.int(), self.relative_pos_query_table.float(), self.relative_pos_key_table.float(), relative_position_index.int())
        elif self.rel_query:
            relative_position_bias = pointops.dot_prod_with_idx(query.float(), index_0.int(), self.relative_pos_query_table.float(), relative_position_index.int())
        elif self.rel_key:
            relative_position_bias = pointops.dot_prod_with_idx(key.float(), index_1.int(), self.relative_pos_key_table.float(), relative_position_index.int())
        else:
            relative_position_bias = 0.0
        attn_flat += relative_position_bias
        softmax_attn_flat = scatter_softmax(src=attn_flat, index=index_0, dim=0)
        if self.rel_value:
            x = pointops.attention_step2_with_rel_pos_value_v2(softmax_attn_flat.float(), value.float(), index_0_offsets.int(), n_max, index_1.int(), self.relative_pos_value_table.float(), relative_position_index.int())
        else:
            x = pointops.attention_step2(softmax_attn_flat.float(), value.float(), index_0.int(), index_1.int())
        x = x.view(n, c)
        x = self.proj(x)
        x = self.proj_drop(x)
        return x

def __init__(self, embed_channels, num_heads, window_size, quant_size, attn_drop=0.0, proj_drop=0.0, scale=None, rel_query=True, rel_key=True, rel_value=True, qkv_bias=True):
    super().__init__()
    self.embed_channels = embed_channels
    self.head_channels = embed_channels // num_heads
    self.num_heads = num_heads
    self.scale = scale or self.head_channels ** (-0.5)
    self.window_size = window_size
    self.quant_size = quant_size
    self.rel_query = rel_query
    self.rel_key = rel_key
    self.rel_value = rel_value
    self.quant_grid_length = int((2 * window_size + 0.0001) // quant_size)
    assert self.rel_query and self.rel_key
    if rel_query:
        self.relative_pos_query_table = nn.Parameter(torch.zeros(2 * self.quant_grid_length, self.num_heads, self.head_channels, 3))
        trunc_normal_(self.relative_pos_query_table, std=0.02)
    if rel_key:
        self.relative_pos_key_table = nn.Parameter(torch.zeros(2 * self.quant_grid_length, self.num_heads, self.head_channels, 3))
        trunc_normal_(self.relative_pos_query_table, std=0.02)
    if rel_value:
        self.relative_pos_value_table = nn.Parameter(torch.zeros(2 * self.quant_grid_length, self.num_heads, self.head_channels, 3))
        trunc_normal_(self.relative_pos_query_table, std=0.02)
    self.qkv = nn.Linear(embed_channels, embed_channels * 3, bias=qkv_bias)
    self.attn_drop = nn.Dropout(attn_drop, inplace=True)
    self.proj = nn.Linear(embed_channels, embed_channels)
    self.proj_drop = nn.Dropout(proj_drop, inplace=True)
    self.softmax = nn.Softmax(dim=-1)

class MLP(nn.Module):

    def __init__(self, in_channels, hidden_channels=None, out_channels=None, drop=0.0):
        super().__init__()
        out_channels = out_channels or in_channels
        hidden_channels = hidden_channels or in_channels
        self.fc1 = nn.Linear(in_channels, hidden_channels)
        self.act = nn.GELU()
        self.fc2 = nn.Linear(hidden_channels, out_channels)
        self.drop = nn.Dropout(drop, inplace=True)

    def forward(self, x):
        x = self.fc1(x)
        x = self.act(x)
        x = self.drop(x)
        x = self.fc2(x)
        x = self.drop(x)
        return x

def __init__(self, in_channels, hidden_channels=None, out_channels=None, drop=0.0):
    super().__init__()
    out_channels = out_channels or in_channels
    hidden_channels = hidden_channels or in_channels
    self.fc1 = nn.Linear(in_channels, hidden_channels)
    self.act = nn.GELU()
    self.fc2 = nn.Linear(hidden_channels, out_channels)
    self.drop = nn.Dropout(drop, inplace=True)

class Block(nn.Module):

    def __init__(self, embed_channels, num_heads, window_size, quant_size, mlp_expend_ratio=4.0, drop_path=0.0, qk_scale=None, rel_query=True, rel_key=True, rel_value=True, qkv_bias=True):
        super().__init__()
        self.norm1 = nn.LayerNorm(embed_channels)
        self.attn = WindowAttention(embed_channels, num_heads, window_size, quant_size, scale=qk_scale, rel_query=rel_query, rel_key=rel_key, rel_value=rel_value, qkv_bias=qkv_bias)
        self.drop_path = DropPath(drop_path) if drop_path > 0.0 else nn.Identity()
        self.norm2 = nn.LayerNorm(embed_channels)
        self.mlp = MLP(in_channels=embed_channels, hidden_channels=int(embed_channels * mlp_expend_ratio))

    def forward(self, feats, coords, index_0, index_1, index_0_offsets, n_max):
        short_cut = feats
        feats = self.norm1(feats)
        feats = self.attn(feats, coords, index_0, index_1, index_0_offsets, n_max)
        feats = short_cut + self.drop_path(feats)
        feats += self.drop_path(self.mlp(self.norm2(feats)))
        return feats

def __init__(self, embed_channels, num_heads, window_size, quant_size, mlp_expend_ratio=4.0, drop_path=0.0, qk_scale=None, rel_query=True, rel_key=True, rel_value=True, qkv_bias=True):
    super().__init__()
    self.norm1 = nn.LayerNorm(embed_channels)
    self.attn = WindowAttention(embed_channels, num_heads, window_size, quant_size, scale=qk_scale, rel_query=rel_query, rel_key=rel_key, rel_value=rel_value, qkv_bias=qkv_bias)
    self.drop_path = DropPath(drop_path) if drop_path > 0.0 else nn.Identity()
    self.norm2 = nn.LayerNorm(embed_channels)
    self.mlp = MLP(in_channels=embed_channels, hidden_channels=int(embed_channels * mlp_expend_ratio))

class BasicLayer(nn.Module):

    def __init__(self, embed_channels, out_channels, depth, num_heads, window_size, quant_size, mlp_expend_ratio=4.0, down_ratio=0.25, down_num_sample=16, drop_path=None, qk_scale=None, down=True, rel_query=True, rel_key=True, rel_value=True, qkv_bias=True):
        super().__init__()
        self.depth = depth
        self.window_size = window_size
        self.quant_size = quant_size
        self.down_ratio = down_ratio
        if isinstance(drop_path, list):
            drop_path = drop_path
            assert len(drop_path) == depth
        elif isinstance(drop_path, float):
            drop_path = [deepcopy(drop_path) for _ in range(depth)]
        else:
            drop_path = [0.0 for _ in range(depth)]
        self.blocks = nn.ModuleList()
        for i in range(depth):
            block = Block(embed_channels, num_heads, window_size, quant_size, mlp_expend_ratio=mlp_expend_ratio, drop_path=drop_path[i], qk_scale=qk_scale, rel_query=rel_query, rel_key=rel_key, rel_value=rel_value, qkv_bias=qkv_bias)
            self.blocks.append(block)
        self.down = TransitionDown(embed_channels, out_channels, down_ratio, down_num_sample) if down else None

    def forward(self, feats, coords, offset):
        window_size = torch.tensor([self.window_size] * 3, dtype=coords.dtype, device=coords.device)
        new_window_size = 2 * torch.tensor([self.window_size] * 3, dtype=coords.dtype, device=coords.device)
        batch = offset2batch(offset)
        new_offset = [int(offset[0].item() * self.down_ratio) + 1]
        count = int(offset[0].item() * self.down_ratio) + 1
        for i in range(1, offset.shape[0]):
            count += int((offset[i].item() - offset[i - 1].item()) * self.down_ratio) + 1
            new_offset.append(count)
        new_offset = torch.cuda.IntTensor(new_offset)
        down_idx = pointops.furthestsampling(coords, offset.int(), new_offset.int())
        coords_min = coords.min(0).values
        v2p_map, p2v_map, counts = grid_sample(coords, batch, window_size, start=None)
        shift_size = window_size * 1 / 2
        shift_v2p_map, shift_p2v_map, shift_counts = grid_sample(coords + shift_size, batch, window_size, start=coords_min)
        new_v2p_map, new_p2v_map, new_counts = grid_sample(coords, batch, new_window_size, start=None)
        shift_size = new_window_size * 1 / 2
        shift_new_v2p_map, shift_new_p2v_map, shift_new_counts = grid_sample(coords + shift_size, batch, new_window_size, start=coords_min)
        for i, blk in enumerate(self.blocks):
            p2v_map_blk = p2v_map if i % 2 == 0 else shift_p2v_map
            counts_blk = counts if i % 2 == 0 else shift_counts
            new_p2v_map_blk = new_p2v_map if i % 2 == 0 else shift_new_p2v_map
            new_counts_blk = new_counts if i % 2 == 0 else shift_new_counts
            n, k = p2v_map_blk.shape
            mask = torch.arange(k).unsqueeze(0).cuda() < counts_blk.unsqueeze(-1)
            mask_mat = mask.unsqueeze(-1) & mask.unsqueeze(-2)
            index_0 = p2v_map_blk.unsqueeze(-1).expand(-1, -1, k)[mask_mat]
            index_1 = p2v_map_blk.unsqueeze(1).expand(-1, k, -1)[mask_mat]
            down_mask = torch.zeros_like(batch).bool()
            down_mask[down_idx.long()] = True
            down_mask = down_mask[new_p2v_map_blk]
            n, k = new_p2v_map_blk.shape
            mask = torch.arange(k).unsqueeze(0).cuda() < new_counts_blk.unsqueeze(-1)
            down_mask = down_mask & mask
            mask_mat = mask.unsqueeze(-1) & down_mask.unsqueeze(-2)
            if i % 2 == 0:
                window_coord = torch.div(coords[new_p2v_map_blk] - coords_min, window_size, rounding_mode='trunc')
            else:
                window_coord = torch.div(coords[new_p2v_map_blk] - coords_min + 1 / 2 * window_size, window_size, rounding_mode='trunc')
            mask_mat_prev = (window_coord.unsqueeze(2) != window_coord.unsqueeze(1)).any(-1)
            mask_mat = mask_mat & mask_mat_prev
            new_index_0 = new_p2v_map_blk.unsqueeze(-1).expand(-1, -1, k)[mask_mat]
            new_index_1 = new_p2v_map_blk.unsqueeze(1).expand(-1, k, -1)[mask_mat]
            index_0 = torch.cat([index_0, new_index_0], 0)
            index_1 = torch.cat([index_1, new_index_1], 0)
            index_0, indices = torch.sort(index_0)
            index_1 = index_1[indices]
            index_0_counts = index_0.bincount()
            n_max = index_0_counts.max()
            index_0_offsets = index_0_counts.cumsum(dim=-1)
            index_0_offsets = torch.cat([torch.zeros(1, dtype=torch.long).cuda(), index_0_offsets], 0)
            feats = blk(feats, coords, index_0, index_1, index_0_offsets, n_max)
        if self.down:
            feats_down, coords_down, offset_down = self.down(feats, coords, offset)
        else:
            feats_down, coords_down, offset_down = (None, None, None)
        return (feats, coords, offset, feats_down, coords_down, offset_down)

def __init__(self, embed_channels, out_channels, depth, num_heads, window_size, quant_size, mlp_expend_ratio=4.0, down_ratio=0.25, down_num_sample=16, drop_path=None, qk_scale=None, down=True, rel_query=True, rel_key=True, rel_value=True, qkv_bias=True):
    super().__init__()
    self.depth = depth
    self.window_size = window_size
    self.quant_size = quant_size
    self.down_ratio = down_ratio
    if isinstance(drop_path, list):
        drop_path = drop_path
        assert len(drop_path) == depth
    elif isinstance(drop_path, float):
        drop_path = [deepcopy(drop_path) for _ in range(depth)]
    else:
        drop_path = [0.0 for _ in range(depth)]
    self.blocks = nn.ModuleList()
    for i in range(depth):
        block = Block(embed_channels, num_heads, window_size, quant_size, mlp_expend_ratio=mlp_expend_ratio, drop_path=drop_path[i], qk_scale=qk_scale, rel_query=rel_query, rel_key=rel_key, rel_value=rel_value, qkv_bias=qkv_bias)
        self.blocks.append(block)
    self.down = TransitionDown(embed_channels, out_channels, down_ratio, down_num_sample) if down else None

class TransitionDown(nn.Module):

    def __init__(self, in_channels, out_channels, ratio, k, norm_layer=nn.LayerNorm):
        super().__init__()
        self.ratio = ratio
        self.k = k
        self.norm = norm_layer(in_channels) if norm_layer else None
        self.linear = nn.Linear(in_channels, out_channels, bias=False)
        self.pool = nn.MaxPool1d(k)

    def forward(self, feats, coords, offset):
        new_offset, count = ([int(offset[0].item() * self.ratio) + 1], int(offset[0].item() * self.ratio) + 1)
        for i in range(1, offset.shape[0]):
            count += (offset[i].item() - offset[i - 1].item()) * self.ratio + 1
            new_offset.append(count)
        new_offset = torch.cuda.IntTensor(new_offset)
        idx = pointops.furthestsampling(coords, offset, new_offset)
        new_coords = coords[idx.long(), :]
        feats = pointops.queryandgroup(self.k, coords, new_coords, feats, None, offset, new_offset, use_xyz=False)
        m, k, c = feats.shape
        feats = self.linear(self.norm(feats.view(m * k, c)).view(m, k, c)).transpose(1, 2).contiguous()
        feats = self.pool(feats).squeeze(-1)
        return (feats, new_coords, new_offset)

def __init__(self, in_channels, out_channels, ratio, k, norm_layer=nn.LayerNorm):
    super().__init__()
    self.ratio = ratio
    self.k = k
    self.norm = norm_layer(in_channels) if norm_layer else None
    self.linear = nn.Linear(in_channels, out_channels, bias=False)
    self.pool = nn.MaxPool1d(k)

class TransitionUp(nn.Module):

    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.linear1 = nn.Sequential(nn.LayerNorm(out_channels), nn.Linear(out_channels, out_channels))
        self.linear2 = nn.Sequential(nn.LayerNorm(in_channels), nn.Linear(in_channels, out_channels))

    def forward(self, feats, coords, offset, skip_feats, skip_coords, skip_offset):
        feats = self.linear1(skip_feats) + pointops.interpolation(coords, skip_coords, self.linear2(feats), offset, skip_offset)
        return (feats, skip_coords, skip_offset)

def __init__(self, in_channels, out_channels):
    super().__init__()
    self.in_channels = in_channels
    self.out_channels = out_channels
    self.linear1 = nn.Sequential(nn.LayerNorm(out_channels), nn.Linear(out_channels, out_channels))
    self.linear2 = nn.Sequential(nn.LayerNorm(in_channels), nn.Linear(in_channels, out_channels))

class KPConvSimpleBlock(nn.Module):

    def __init__(self, in_channels, out_channels, prev_grid_size, sigma=1.0, negative_slope=0.2, bn_momentum=0.02):
        super().__init__()
        self.kpconv = KPConvLayer(in_channels, out_channels, point_influence=prev_grid_size * sigma, add_one=False)
        self.bn = FastBatchNorm1d(out_channels, momentum=bn_momentum)
        self.activation = nn.LeakyReLU(negative_slope=negative_slope)

    def forward(self, feats, xyz, batch, neighbor_idx):
        feats = self.kpconv(xyz, xyz, neighbor_idx, feats)
        feats = self.activation(self.bn(feats))
        return feats

def __init__(self, in_channels, out_channels, prev_grid_size, sigma=1.0, negative_slope=0.2, bn_momentum=0.02):
    super().__init__()
    self.kpconv = KPConvLayer(in_channels, out_channels, point_influence=prev_grid_size * sigma, add_one=False)
    self.bn = FastBatchNorm1d(out_channels, momentum=bn_momentum)
    self.activation = nn.LeakyReLU(negative_slope=negative_slope)

class KPConvResBlock(nn.Module):

    def __init__(self, in_channels, out_channels, prev_grid_size, sigma=1.0, negative_slope=0.2, bn_momentum=0.02):
        super().__init__()
        d_2 = out_channels // 4
        activation = nn.LeakyReLU(negative_slope=negative_slope)
        self.unary_1 = torch.nn.Sequential(nn.Linear(in_channels, d_2, bias=False), FastBatchNorm1d(d_2, momentum=bn_momentum), activation)
        self.unary_2 = torch.nn.Sequential(nn.Linear(d_2, out_channels, bias=False), FastBatchNorm1d(out_channels, momentum=bn_momentum), activation)
        self.kpconv = KPConvLayer(d_2, d_2, point_influence=prev_grid_size * sigma, add_one=False)
        self.bn = FastBatchNorm1d(out_channels, momentum=bn_momentum)
        self.activation = activation
        if in_channels != out_channels:
            self.shortcut_op = torch.nn.Sequential(nn.Linear(in_channels, out_channels, bias=False), FastBatchNorm1d(out_channels, momentum=bn_momentum))
        else:
            self.shortcut_op = nn.Identity()

    def forward(self, feats, xyz, batch, neighbor_idx):
        shortcut = feats
        feats = self.unary_1(feats)
        feats = self.kpconv(xyz, xyz, neighbor_idx, feats)
        feats = self.unary_2(feats)
        shortcut = self.shortcut_op(shortcut)
        feats += shortcut
        return feats

def __init__(self, in_channels, out_channels, prev_grid_size, sigma=1.0, negative_slope=0.2, bn_momentum=0.02):
    super().__init__()
    d_2 = out_channels // 4
    activation = nn.LeakyReLU(negative_slope=negative_slope)
    self.unary_1 = torch.nn.Sequential(nn.Linear(in_channels, d_2, bias=False), FastBatchNorm1d(d_2, momentum=bn_momentum), activation)
    self.unary_2 = torch.nn.Sequential(nn.Linear(d_2, out_channels, bias=False), FastBatchNorm1d(out_channels, momentum=bn_momentum), activation)
    self.kpconv = KPConvLayer(d_2, d_2, point_influence=prev_grid_size * sigma, add_one=False)
    self.bn = FastBatchNorm1d(out_channels, momentum=bn_momentum)
    self.activation = activation
    if in_channels != out_channels:
        self.shortcut_op = torch.nn.Sequential(nn.Linear(in_channels, out_channels, bias=False), FastBatchNorm1d(out_channels, momentum=bn_momentum))
    else:
        self.shortcut_op = nn.Identity()

@MODELS.register_module('stv1m2')
class StratifiedTransformer(nn.Module):

    def __init__(self, in_channels, num_classes, channels=(48, 96, 192, 384, 384), num_heads=(6, 12, 24, 24), depths=(3, 9, 3, 3), window_size=(0.2, 0.4, 0.8, 1.6), quant_size=(0.01, 0.02, 0.04, 0.08), mlp_expend_ratio=4.0, down_ratio=0.25, down_num_sample=16, kp_ball_radius=2.5 * 0.02, kp_max_neighbor=34, kp_grid_size=0.02, kp_sigma=1.0, drop_path_rate=0.2, rel_query=True, rel_key=True, rel_value=True, qkv_bias=True, stem=True):
        super().__init__()
        dpr = [x.item() for x in torch.linspace(0, drop_path_rate, sum(depths))]
        self.kp_ball_radius = kp_ball_radius
        self.kp_max_neighbor = kp_max_neighbor
        self.stem = stem
        if stem:
            self.point_embed = nn.ModuleList([KPConvSimpleBlock(in_channels, channels[0], kp_grid_size, sigma=kp_sigma), KPConvResBlock(channels[0], channels[0], kp_grid_size, sigma=kp_sigma)])
            self.down = TransitionDown(channels[0], channels[1], down_ratio, down_num_sample)
        else:
            assert channels[0] == channels[1]
            self.point_embed = nn.ModuleList([KPConvSimpleBlock(in_channels, channels[1], kp_grid_size, sigma=kp_sigma)])
        num_layers = len(depths)
        self.layers = nn.ModuleList()
        for i in range(num_layers):
            layer = BasicLayer(embed_channels=channels[i + 1], out_channels=channels[i + 2] if i < num_layers - 1 else channels[i + 1], depth=depths[i], num_heads=num_heads[i], window_size=window_size[i], quant_size=quant_size[i], mlp_expend_ratio=mlp_expend_ratio, down_ratio=down_ratio, down_num_sample=down_num_sample, drop_path=dpr[sum(depths[:i]):sum(depths[:i + 1])], rel_query=rel_query, rel_key=rel_key, rel_value=rel_value, qkv_bias=qkv_bias, down=True if i < num_layers - 1 else False)
            self.layers.append(layer)
        self.up = nn.ModuleList([TransitionUp(channels[i + 1], channels[i]) for i in reversed(range(1, num_layers))])
        if self.stem:
            self.up.append(TransitionUp(channels[1], channels[0]))
        self.classifier = nn.Sequential(nn.Linear(channels[0], channels[0]), nn.BatchNorm1d(channels[0]), nn.ReLU(inplace=True), nn.Linear(channels[0], num_classes))
        self.init_weights()

    def forward(self, input_dict):
        feats = input_dict['feat']
        coords = input_dict['coord']
        offset = input_dict['offset'].int()
        batch = offset2batch(offset)
        neighbor_idx = tp.ball_query(self.kp_ball_radius, self.kp_max_neighbor, coords, coords, mode='partial_dense', batch_x=batch, batch_y=batch)[0]
        feats_stack = []
        coords_stack = []
        offset_stack = []
        for i, layer in enumerate(self.point_embed):
            feats = layer(feats, coords, batch, neighbor_idx)
        feats = feats.contiguous()
        if self.stem:
            feats_stack.append(feats)
            coords_stack.append(coords)
            offset_stack.append(offset)
            feats, coords, offset = self.down(feats, coords, offset)
        for i, layer in enumerate(self.layers):
            feats, coords, offset, feats_down, coords_down, offset_down = layer(feats, coords, offset)
            feats_stack.append(feats)
            coords_stack.append(coords)
            offset_stack.append(offset)
            feats = feats_down
            coords = coords_down
            offset = offset_down
        feats = feats_stack.pop()
        coords = coords_stack.pop()
        offset = offset_stack.pop()
        for i, up in enumerate(self.up):
            feats, coords, offset = up(feats, coords, offset, feats_stack.pop(), coords_stack.pop(), offset_stack.pop())
        out = self.classifier(feats)
        return out

    def init_weights(self):
        """Initialize the weights in backbone.
        """

        def _init_weights(m):
            if isinstance(m, nn.Linear):
                trunc_normal_(m.weight, std=0.02)
                if isinstance(m, nn.Linear) and m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.LayerNorm) or isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.bias, 0)
                nn.init.constant_(m.weight, 1.0)
        self.apply(_init_weights)

def __init__(self, in_channels, num_classes, channels=(48, 96, 192, 384, 384), num_heads=(6, 12, 24, 24), depths=(3, 9, 3, 3), window_size=(0.2, 0.4, 0.8, 1.6), quant_size=(0.01, 0.02, 0.04, 0.08), mlp_expend_ratio=4.0, down_ratio=0.25, down_num_sample=16, kp_ball_radius=2.5 * 0.02, kp_max_neighbor=34, kp_grid_size=0.02, kp_sigma=1.0, drop_path_rate=0.2, rel_query=True, rel_key=True, rel_value=True, qkv_bias=True, stem=True):
    super().__init__()
    dpr = [x.item() for x in torch.linspace(0, drop_path_rate, sum(depths))]
    self.kp_ball_radius = kp_ball_radius
    self.kp_max_neighbor = kp_max_neighbor
    self.stem = stem
    if stem:
        self.point_embed = nn.ModuleList([KPConvSimpleBlock(in_channels, channels[0], kp_grid_size, sigma=kp_sigma), KPConvResBlock(channels[0], channels[0], kp_grid_size, sigma=kp_sigma)])
        self.down = TransitionDown(channels[0], channels[1], down_ratio, down_num_sample)
    else:
        assert channels[0] == channels[1]
        self.point_embed = nn.ModuleList([KPConvSimpleBlock(in_channels, channels[1], kp_grid_size, sigma=kp_sigma)])
    num_layers = len(depths)
    self.layers = nn.ModuleList()
    for i in range(num_layers):
        layer = BasicLayer(embed_channels=channels[i + 1], out_channels=channels[i + 2] if i < num_layers - 1 else channels[i + 1], depth=depths[i], num_heads=num_heads[i], window_size=window_size[i], quant_size=quant_size[i], mlp_expend_ratio=mlp_expend_ratio, down_ratio=down_ratio, down_num_sample=down_num_sample, drop_path=dpr[sum(depths[:i]):sum(depths[:i + 1])], rel_query=rel_query, rel_key=rel_key, rel_value=rel_value, qkv_bias=qkv_bias, down=True if i < num_layers - 1 else False)
        self.layers.append(layer)
    self.up = nn.ModuleList([TransitionUp(channels[i + 1], channels[i]) for i in reversed(range(1, num_layers))])
    if self.stem:
        self.up.append(TransitionUp(channels[1], channels[0]))
    self.classifier = nn.Sequential(nn.Linear(channels[0], channels[0]), nn.BatchNorm1d(channels[0]), nn.ReLU(inplace=True), nn.Linear(channels[0], num_classes))
    self.init_weights()

def init_weights(self):
    """Initialize the weights in backbone.
        """

    def _init_weights(m):
        if isinstance(m, nn.Linear):
            trunc_normal_(m.weight, std=0.02)
            if isinstance(m, nn.Linear) and m.bias is not None:
                nn.init.constant_(m.bias, 0)
        elif isinstance(m, nn.LayerNorm) or isinstance(m, nn.BatchNorm1d):
            nn.init.constant_(m.bias, 0)
            nn.init.constant_(m.weight, 1.0)
    self.apply(_init_weights)

