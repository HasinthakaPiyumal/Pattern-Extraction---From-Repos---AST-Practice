# Cluster 7

class Criteria(object):

    def __init__(self, cfg=None):
        self.cfg = cfg if cfg is not None else []
        self.criteria = []
        for loss_cfg in self.cfg:
            self.criteria.append(LOSSES.build(cfg=loss_cfg))

    def __call__(self, pred, target):
        if len(self.criteria) == 0:
            return pred
        loss = 0
        for c in self.criteria:
            loss += c(pred, target)
        return loss

def __init__(self, cfg=None):
    self.cfg = cfg if cfg is not None else []
    self.criteria = []
    for loss_cfg in self.cfg:
        self.criteria.append(LOSSES.build(cfg=loss_cfg))

def check_file_exist(filename, msg_tmpl='file "{}" does not exist'):
    if not osp.isfile(filename):
        raise FileNotFoundError(msg_tmpl.format(filename))

def build_optimizer(cfg, model, params_dicts=None):
    if params_dicts is None:
        cfg.params = model.parameters()
    else:
        cfg.params = [dict(params=[])]
        for i in range(len(params_dicts)):
            cfg.params.append(dict(params=[], lr=params_dicts[i].lr_scale * cfg.lr))
        for n, p in model.named_parameters():
            flag = False
            for i in range(len(params_dicts)):
                if params_dicts[i].keyword in n:
                    cfg.params[i + 1]['params'].append(p)
                    flag = True
                    break
            if not flag:
                cfg.params[0]['params'].append(p)
    return OPTIMIZERS.build(cfg=cfg)

def set_seed(seed=None):
    if seed is None:
        seed = get_random_seed()
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    cudnn.benchmark = False
    cudnn.deterministic = True
    os.environ['PYTHONHASHSEED'] = str(seed)

def build_scheduler(cfg, optimizer):
    cfg.optimizer = optimizer
    return SCHEDULERS.build(cfg=cfg)

class TensorboardXWriter(EventWriter):
    """
    Write all scalars to a tensorboard file.
    """

    def __init__(self, log_dir: str, window_size: int=20, **kwargs):
        """
        Args:
            log_dir (str): the directory to save the output events
            window_size (int): the scalars will be median-smoothed by this window size
            kwargs: other arguments passed to `torch.utils.tensorboard.SummaryWriter(...)`
        """
        self._window_size = window_size
        from torch.utils.tensorboard import SummaryWriter
        self._writer = SummaryWriter(log_dir, **kwargs)
        self._last_write = -1

    def write(self):
        storage = get_event_storage()
        new_last_write = self._last_write
        for k, (v, iter) in storage.latest_with_smoothing_hint(self._window_size).items():
            if iter > self._last_write:
                self._writer.add_scalar(k, v, iter)
                new_last_write = max(new_last_write, iter)
        self._last_write = new_last_write
        if len(storage._vis_data) >= 1:
            for img_name, img, step_num in storage._vis_data:
                self._writer.add_image(img_name, img, step_num)
            storage.clear_images()
        if len(storage._histograms) >= 1:
            for params in storage._histograms:
                self._writer.add_histogram_raw(**params)
            storage.clear_histograms()

    def close(self):
        if hasattr(self, '_writer'):
            self._writer.close()

def close(self):
    if hasattr(self, '_writer'):
        self._writer.close()

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

def load_state_dict(self, state_dict):
    super().load_state_dict(state_dict)
    self.optimizer.load_state_dict(state_dict['optimizer'])

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

def load_state_dict(self, state_dict):
    super().load_state_dict(state_dict)
    self.grad_scaler.load_state_dict(state_dict['grad_scaler'])

def worker_init_fn(worker_id, num_workers, rank, seed):
    """Worker init func for dataloader.

    The seed of each worker equals to num_worker * rank + worker_id + user_seed

    Args:
        worker_id (int): Worker id.
        num_workers (int): Number of workers.
        rank (int): The rank of current process.
        seed (int): The random seed to use.
    """
    worker_seed = num_workers * rank + worker_id + seed
    set_seed(worker_seed)

def default_config_parser(file_path, options):
    if os.path.isfile(file_path):
        cfg = Config.fromfile(file_path)
    else:
        sep = file_path.find('-')
        cfg = Config.fromfile(os.path.join(file_path[:sep], file_path[sep + 1:]))
    if options is not None:
        cfg.merge_from_dict(options)
    if cfg.seed is None:
        cfg.seed = get_random_seed()
    cfg.data.train.loop = cfg.epoch // cfg.eval_epoch
    os.makedirs(os.path.join(cfg.save_path, 'model'), exist_ok=True)
    if not cfg.resume:
        cfg.dump(os.path.join(cfg.save_path, 'config.py'))
    return cfg

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

def build_model(self):
    model = build_model(self.cfg.model)
    if self.cfg.sync_bn:
        model = nn.SyncBatchNorm.convert_sync_batchnorm(model)
    n_parameters = sum((p.numel() for p in model.parameters() if p.requires_grad))
    self.logger.info(f'Num params: {n_parameters}')
    model = create_ddp_model(model.cuda(), broadcast_buffers=False, find_unused_parameters=self.cfg.find_unused_parameters)
    return model

def build_criteria(self):
    return build_criteria(self.cfg.criteria)

def build_optimizer(self):
    return build_optimizer(self.cfg.optimizer, self.model, self.cfg.param_dicts)

def build_scheduler(self):
    assert hasattr(self, 'optimizer')
    assert hasattr(self, 'train_loader')
    self.cfg.scheduler.total_steps = len(self.train_loader) * self.cfg.eval_epoch
    return build_scheduler(self.cfg.scheduler, self.optimizer)

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

class Compose(object):

    def __init__(self, cfg=None):
        self.cfg = cfg if cfg is not None else []
        self.transforms = []
        for t_cfg in self.cfg:
            self.transforms.append(TRANSFORMS.build(t_cfg))

    def __call__(self, data_dict):
        for t in self.transforms:
            data_dict = t(data_dict)
        return data_dict

def __init__(self, cfg=None):
    self.cfg = cfg if cfg is not None else []
    self.transforms = []
    for t_cfg in self.cfg:
        self.transforms.append(TRANSFORMS.build(t_cfg))

def build_dataset(cfg):
    """Build test_datasets."""
    return DATASETS.build(cfg)

def make2d(array, cols=None, dtype=None):
    """
    Make a 2D array from an array of arrays.  The `cols' and `dtype'
    arguments can be omitted if the array is not empty.

    """
    if (cols is None or dtype is None) and (not len(array)):
        raise RuntimeError('cols and dtype must be specified for empty array')
    if cols is None:
        cols = len(array[0])
    if dtype is None:
        dtype = array[0].dtype
    return _np.fromiter(array, [('_', dtype, (cols,))], count=len(array))['_']

def _open_stream(stream, read_or_write):
    if hasattr(stream, read_or_write):
        return (False, stream)
    try:
        return (True, open(stream, read_or_write[0] + 'b'))
    except TypeError:
        raise RuntimeError('expected open file or filename')

class PlyElement(object):
    """
    PLY file element.

    A client of this library doesn't normally need to instantiate this
    directly, so the following is only for the sake of documenting the
    internals.

    Creating a PlyElement instance is generally done in one of two ways:
    as a byproduct of PlyData.read (when reading a PLY file) and by
    PlyElement.describe (before writing a PLY file).

    """

    def __init__(self, name, properties, count, comments=[]):
        """
        This is not part of the public interface.  The preferred methods
        of obtaining PlyElement instances are PlyData.read (to read from
        a file) and PlyElement.describe (to construct from a numpy
        array).

        """
        self._name = str(name)
        self._check_name()
        self._count = count
        self._properties = tuple(properties)
        self._index()
        self.comments = list(comments)
        self._have_list = any((isinstance(p, PlyListProperty) for p in self.properties))

    @property
    def count(self):
        return self._count

    def _get_data(self):
        return self._data

    def _set_data(self, data):
        self._data = data
        self._count = len(data)
        self._check_sanity()
    data = property(_get_data, _set_data)

    def _check_sanity(self):
        for prop in self.properties:
            if prop.name not in self._data.dtype.fields:
                raise ValueError('dangling property %r' % prop.name)

    def _get_properties(self):
        return self._properties

    def _set_properties(self, properties):
        self._properties = tuple(properties)
        self._check_sanity()
        self._index()
    properties = property(_get_properties, _set_properties)

    def _index(self):
        self._property_lookup = dict(((prop.name, prop) for prop in self._properties))
        if len(self._property_lookup) != len(self._properties):
            raise ValueError('two properties with same name')

    def ply_property(self, name):
        return self._property_lookup[name]

    @property
    def name(self):
        return self._name

    def _check_name(self):
        if any((c.isspace() for c in self._name)):
            msg = 'element name %r contains spaces' % self._name
            raise ValueError(msg)

    def dtype(self, byte_order='='):
        """
        Return the numpy dtype of the in-memory representation of the
        data.  (If there are no list properties, and the PLY format is
        binary, then this also accurately describes the on-disk
        representation of the element.)

        """
        return [(prop.name, prop.dtype(byte_order)) for prop in self.properties]

    @staticmethod
    def _parse_multi(header_lines):
        """
        Parse a list of PLY element definitions.

        """
        elements = []
        while header_lines:
            elt, header_lines = PlyElement._parse_one(header_lines)
            elements.append(elt)
        return elements

    @staticmethod
    def _parse_one(lines):
        """
        Consume one element definition.  The unconsumed input is
        returned along with a PlyElement instance.

        """
        a = 0
        line = lines[a]
        if line[0] != 'element':
            raise PlyParseError("expected 'element'")
        if len(line) > 3:
            raise PlyParseError("too many fields after 'element'")
        if len(line) < 3:
            raise PlyParseError("too few fields after 'element'")
        name, count = (line[1], int(line[2]))
        comments = []
        properties = []
        while True:
            a += 1
            if a >= len(lines):
                break
            if lines[a][0] == 'comment':
                comments.append(lines[a][1])
            elif lines[a][0] == 'property':
                properties.append(PlyProperty._parse_one(lines[a]))
            else:
                break
        return (PlyElement(name, properties, count, comments), lines[a:])

    @staticmethod
    def describe(data, name, len_types={}, val_types={}, comments=[]):
        """
        Construct a PlyElement from an array's metadata.

        len_types and val_types can be given as mappings from list
        property names to type strings (like 'u1', 'f4', etc., or
        'int8', 'float32', etc.). These can be used to define the length
        and value types of list properties.  List property lengths
        always default to type 'u1' (8-bit unsigned integer), and value
        types default to 'i4' (32-bit integer).

        """
        if not isinstance(data, _np.ndarray):
            raise TypeError('only numpy arrays are supported')
        if len(data.shape) != 1:
            raise ValueError('only one-dimensional arrays are supported')
        count = len(data)
        properties = []
        descr = data.dtype.descr
        for t in descr:
            if not isinstance(t[1], str):
                raise ValueError('nested records not supported')
            if not t[0]:
                raise ValueError('field with empty name')
            if len(t) != 2 or t[1][1] == 'O':
                if t[1][1] == 'O':
                    if len(t) != 2:
                        raise ValueError('non-scalar object fields not supported')
                len_str = _data_type_reverse[len_types.get(t[0], 'u1')]
                if t[1][1] == 'O':
                    val_type = val_types.get(t[0], 'i4')
                    val_str = _lookup_type(val_type)
                else:
                    val_str = _lookup_type(t[1][1:])
                prop = PlyListProperty(t[0], len_str, val_str)
            else:
                val_str = _lookup_type(t[1][1:])
                prop = PlyProperty(t[0], val_str)
            properties.append(prop)
        elt = PlyElement(name, properties, count, comments)
        elt.data = data
        return elt

    def _read(self, stream, text, byte_order):
        """
        Read the actual data from a PLY file.

        """
        if text:
            self._read_txt(stream)
        elif self._have_list:
            self._read_bin(stream, byte_order)
        else:
            self._data = _np.fromfile(stream, self.dtype(byte_order), self.count)
        if len(self._data) < self.count:
            k = len(self._data)
            del self._data
            raise PlyParseError('early end-of-file', self, k)
        self._check_sanity()

    def _write(self, stream, text, byte_order):
        """
        Write the data to a PLY file.

        """
        if text:
            self._write_txt(stream)
        elif self._have_list:
            self._write_bin(stream, byte_order)
        else:
            self.data.astype(self.dtype(byte_order), copy=False).tofile(stream)

    def _read_txt(self, stream):
        """
        Load a PLY element from an ASCII-format PLY file.  The element
        may contain list properties.

        """
        self._data = _np.empty(self.count, dtype=self.dtype())
        k = 0
        for line in _islice(iter(stream.readline, b''), self.count):
            fields = iter(line.strip().split())
            for prop in self.properties:
                try:
                    self._data[prop.name][k] = prop._from_fields(fields)
                except StopIteration:
                    raise PlyParseError('early end-of-line', self, k, prop)
                except ValueError:
                    raise PlyParseError('malformed input', self, k, prop)
            try:
                next(fields)
            except StopIteration:
                pass
            else:
                raise PlyParseError('expected end-of-line', self, k)
            k += 1
        if k < self.count:
            del self._data
            raise PlyParseError('early end-of-file', self, k)

    def _write_txt(self, stream):
        """
        Save a PLY element to an ASCII-format PLY file.  The element may
        contain list properties.

        """
        for rec in self.data:
            fields = []
            for prop in self.properties:
                fields.extend(prop._to_fields(rec[prop.name]))
            _np.savetxt(stream, [fields], '%.18g', newline='\r\n')

    def _read_bin(self, stream, byte_order):
        """
        Load a PLY element from a binary PLY file.  The element may
        contain list properties.

        """
        self._data = _np.empty(self.count, dtype=self.dtype(byte_order))
        for k in _range(self.count):
            for prop in self.properties:
                try:
                    self._data[prop.name][k] = prop._read_bin(stream, byte_order)
                except StopIteration:
                    raise PlyParseError('early end-of-file', self, k, prop)

    def _write_bin(self, stream, byte_order):
        """
        Save a PLY element to a binary PLY file.  The element may
        contain list properties.

        """
        for rec in self.data:
            for prop in self.properties:
                prop._write_bin(rec[prop.name], stream, byte_order)

    @property
    def header(self):
        """
        Format this element's metadata as it would appear in a PLY
        header.

        """
        lines = ['element %s %d' % (self.name, self.count)]
        for c in self.comments:
            lines.append('comment ' + c)
        lines.extend(list(map(str, self.properties)))
        return '\r\n'.join(lines)

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __str__(self):
        return self.header

    def __repr__(self):
        return 'PlyElement(%r, %r, count=%d, comments=%r)' % (self.name, self.properties, self.count, self.comments)

def _check_name(self):
    if any((c.isspace() for c in self._name)):
        msg = 'element name %r contains spaces' % self._name
        raise ValueError(msg)

class PlyProperty(object):
    """
    PLY property description.  This class is pure metadata; the data
    itself is contained in PlyElement instances.

    """

    def __init__(self, name, val_dtype):
        self._name = str(name)
        self._check_name()
        self.val_dtype = val_dtype

    def _get_val_dtype(self):
        return self._val_dtype

    def _set_val_dtype(self, val_dtype):
        self._val_dtype = _data_types[_lookup_type(val_dtype)]
    val_dtype = property(_get_val_dtype, _set_val_dtype)

    @property
    def name(self):
        return self._name

    def _check_name(self):
        if any((c.isspace() for c in self._name)):
            msg = 'Error: property name %r contains spaces' % self._name
            raise RuntimeError(msg)

    @staticmethod
    def _parse_one(line):
        assert line[0] == 'property'
        if line[1] == 'list':
            if len(line) > 5:
                raise PlyParseError("too many fields after 'property list'")
            if len(line) < 5:
                raise PlyParseError("too few fields after 'property list'")
            return PlyListProperty(line[4], line[2], line[3])
        else:
            if len(line) > 3:
                raise PlyParseError("too many fields after 'property'")
            if len(line) < 3:
                raise PlyParseError("too few fields after 'property'")
            return PlyProperty(line[2], line[1])

    def dtype(self, byte_order='='):
        """
        Return the numpy dtype description for this property (as a tuple
        of strings).

        """
        return byte_order + self.val_dtype

    def _from_fields(self, fields):
        """
        Parse from generator.  Raise StopIteration if the property could
        not be read.

        """
        return _np.dtype(self.dtype()).type(next(fields))

    def _to_fields(self, data):
        """
        Return generator over one item.

        """
        yield _np.dtype(self.dtype()).type(data)

    def _read_bin(self, stream, byte_order):
        """
        Read data from a binary stream.  Raise StopIteration if the
        property could not be read.

        """
        try:
            return _np.fromfile(stream, self.dtype(byte_order), 1)[0]
        except IndexError:
            raise StopIteration

    def _write_bin(self, data, stream, byte_order):
        """
        Write data to a binary stream.

        """
        _np.dtype(self.dtype(byte_order)).type(data).tofile(stream)

    def __str__(self):
        val_str = _data_type_reverse[self.val_dtype]
        return 'property %s %s' % (val_str, self.name)

    def __repr__(self):
        return 'PlyProperty(%r, %r)' % (self.name, _lookup_type(self.val_dtype))

def _check_name(self):
    if any((c.isspace() for c in self._name)):
        msg = 'Error: property name %r contains spaces' % self._name
        raise RuntimeError(msg)

def build_model(cfg):
    """Build test_datasets."""
    return MODELS.build(cfg)

def main():
    args = get_parser()
    cfg = Config.fromfile(args.config_file)
    if args.options is not None:
        cfg.merge_from_dict(args.options)
    if cfg.seed is None:
        cfg.seed = get_random_seed()
    os.makedirs(cfg.save_path, exist_ok=True)
    set_seed(cfg.seed)
    cfg.batch_size_val_per_gpu = cfg.batch_size_test
    cfg.num_worker_per_gpu = cfg.num_worker
    weight_name = os.path.basename(cfg.weight).split('.')[0]
    logger = get_root_logger(log_file=os.path.join(cfg.save_path, 'test-{}.log'.format(weight_name)))
    logger.info('=> Loading config ...')
    logger.info(f'Save path: {cfg.save_path}')
    logger.info(f'Config:\n{cfg.pretty_text}')
    logger.info('=> Building model ...')
    model = build_model(cfg.model).cuda()
    n_parameters = sum((p.numel() for p in model.parameters() if p.requires_grad))
    logger.info(f'Num params: {n_parameters}')
    logger.info('=> Building test dataset & dataloader ...')
    test_dataset = build_dataset(cfg.data.test)
    test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=cfg.batch_size_val_per_gpu, shuffle=False, num_workers=cfg.num_worker_per_gpu, pin_memory=True, collate_fn=collate_fn)
    if os.path.isfile(cfg.weight):
        checkpoint = torch.load(cfg.weight)
        state_dict = checkpoint['state_dict']
        new_state_dict = collections.OrderedDict()
        for k, v in state_dict.items():
            name = k[7:]
            new_state_dict[name] = v
        model.load_state_dict(new_state_dict, strict=True)
        logger.info("=> loaded weight '{}' (epoch {})".format(cfg.weight, checkpoint['epoch']))
        cfg.epochs = checkpoint['epoch']
    else:
        raise RuntimeError("=> no checkpoint found at '{}'".format(cfg.weight))
    TEST.build(cfg.test)(cfg, test_loader, model)

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

