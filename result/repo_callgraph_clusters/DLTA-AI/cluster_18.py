# Cluster 18

class ColoredLogger(logging.Logger):
    FORMAT = '[%(levelname2)s] %(module2)s:%(funcName2)s:%(lineno2)s - %(message2)s'

    def __init__(self, name):
        logging.Logger.__init__(self, name, logging.INFO)
        color_formatter = ColoredFormatter(self.FORMAT)
        console = logging.StreamHandler()
        console.setFormatter(color_formatter)
        self.addHandler(console)
        return

def __init__(self, name):
    logging.Logger.__init__(self, name, logging.INFO)
    color_formatter = ColoredFormatter(self.FORMAT)
    console = logging.StreamHandler()
    console.setFormatter(color_formatter)
    self.addHandler(console)
    return

def get_root_logger(log_file=None, log_level=logging.INFO):
    """Get root logger.

    Args:
        log_file (str, optional): File path of log. Defaults to None.
        log_level (int, optional): The level of logger.
            Defaults to logging.INFO.

    Returns:
        :obj:`logging.Logger`: The obtained logger
    """
    logger = get_logger(name='mmdet', log_file=log_file, log_level=log_level)
    return logger

class EvalHook(BaseEvalHook):

    def __init__(self, *args, dynamic_intervals=None, **kwargs):
        super(EvalHook, self).__init__(*args, **kwargs)
        self.latest_results = None
        self.use_dynamic_intervals = dynamic_intervals is not None
        if self.use_dynamic_intervals:
            self.dynamic_milestones, self.dynamic_intervals = _calc_dynamic_intervals(self.interval, dynamic_intervals)

    def _decide_interval(self, runner):
        if self.use_dynamic_intervals:
            progress = runner.epoch if self.by_epoch else runner.iter
            step = bisect.bisect(self.dynamic_milestones, progress + 1)
            self.interval = self.dynamic_intervals[step - 1]

    def before_train_epoch(self, runner):
        """Evaluate the model only at the start of training by epoch."""
        self._decide_interval(runner)
        super().before_train_epoch(runner)

    def before_train_iter(self, runner):
        self._decide_interval(runner)
        super().before_train_iter(runner)

    def _do_evaluate(self, runner):
        """perform evaluation and save ckpt."""
        if not self._should_evaluate(runner):
            return
        from mmdet.apis import single_gpu_test
        results = single_gpu_test(runner.model, self.dataloader, show=False)
        self.latest_results = results
        runner.log_buffer.output['eval_iter_num'] = len(self.dataloader)
        key_score = self.evaluate(runner, results)
        if self.save_best and key_score:
            self._save_ckpt(runner, key_score)

def before_train_epoch(self, runner):
    """Evaluate the model only at the start of training by epoch."""
    self._decide_interval(runner)
    super().before_train_epoch(runner)

def before_train_iter(self, runner):
    self._decide_interval(runner)
    super().before_train_iter(runner)

class DistEvalHook(BaseDistEvalHook):

    def __init__(self, *args, dynamic_intervals=None, **kwargs):
        super(DistEvalHook, self).__init__(*args, **kwargs)
        self.latest_results = None
        self.use_dynamic_intervals = dynamic_intervals is not None
        if self.use_dynamic_intervals:
            self.dynamic_milestones, self.dynamic_intervals = _calc_dynamic_intervals(self.interval, dynamic_intervals)

    def _decide_interval(self, runner):
        if self.use_dynamic_intervals:
            progress = runner.epoch if self.by_epoch else runner.iter
            step = bisect.bisect(self.dynamic_milestones, progress + 1)
            self.interval = self.dynamic_intervals[step - 1]

    def before_train_epoch(self, runner):
        """Evaluate the model only at the start of training by epoch."""
        self._decide_interval(runner)
        super().before_train_epoch(runner)

    def before_train_iter(self, runner):
        self._decide_interval(runner)
        super().before_train_iter(runner)

    def _do_evaluate(self, runner):
        """perform evaluation and save ckpt."""
        if self.broadcast_bn_buffer:
            model = runner.model
            for name, module in model.named_modules():
                if isinstance(module, _BatchNorm) and module.track_running_stats:
                    dist.broadcast(module.running_var, 0)
                    dist.broadcast(module.running_mean, 0)
        if not self._should_evaluate(runner):
            return
        tmpdir = self.tmpdir
        if tmpdir is None:
            tmpdir = osp.join(runner.work_dir, '.eval_hook')
        from mmdet.apis import multi_gpu_test
        results = multi_gpu_test(runner.model, self.dataloader, tmpdir=tmpdir, gpu_collect=self.gpu_collect)
        self.latest_results = results
        if runner.rank == 0:
            print('\n')
            runner.log_buffer.output['eval_iter_num'] = len(self.dataloader)
            key_score = self.evaluate(runner, results)
            if self.save_best and key_score:
                self._save_ckpt(runner, key_score)

def before_train_epoch(self, runner):
    """Evaluate the model only at the start of training by epoch."""
    self._decide_interval(runner)
    super().before_train_epoch(runner)

def before_train_iter(self, runner):
    self._decide_interval(runner)
    super().before_train_iter(runner)

@patch('torch.__version__', torch_version)
def test_adaptive_avg_pool2d():
    x_empty = torch.randn(0, 3, 4, 5)
    wrapper_out = adaptive_avg_pool2d(x_empty, (2, 2))
    assert wrapper_out.shape == (0, 3, 2, 2)
    wrapper_out = adaptive_avg_pool2d(x_empty, 2)
    assert wrapper_out.shape == (0, 3, 2, 2)
    x_normal = torch.randn(3, 3, 4, 5)
    wrapper_out = adaptive_avg_pool2d(x_normal, (2, 2))
    ref_out = F.adaptive_avg_pool2d(x_normal, (2, 2))
    assert wrapper_out.shape == (3, 3, 2, 2)
    assert torch.equal(wrapper_out, ref_out)
    wrapper_out = adaptive_avg_pool2d(x_normal, 2)
    ref_out = F.adaptive_avg_pool2d(x_normal, 2)
    assert wrapper_out.shape == (3, 3, 2, 2)
    assert torch.equal(wrapper_out, ref_out)

@patch('torch.__version__', torch_version)
def test_AdaptiveAvgPool2d():
    x_empty = torch.randn(0, 3, 4, 5)
    wrapper = AdaptiveAvgPool2d((2, 2))
    wrapper_out = wrapper(x_empty)
    assert wrapper_out.shape == (0, 3, 2, 2)
    wrapper = AdaptiveAvgPool2d(2)
    wrapper_out = wrapper(x_empty)
    assert wrapper_out.shape == (0, 3, 2, 2)
    wrapper = AdaptiveAvgPool2d((None, 2))
    wrapper_out = wrapper(x_empty)
    assert wrapper_out.shape == (0, 3, 4, 2)
    wrapper = AdaptiveAvgPool2d((2, None))
    wrapper_out = wrapper(x_empty)
    assert wrapper_out.shape == (0, 3, 2, 5)
    x_normal = torch.randn(3, 3, 4, 5)
    wrapper = AdaptiveAvgPool2d((2, 2))
    ref = nn.AdaptiveAvgPool2d((2, 2))
    wrapper_out = wrapper(x_normal)
    ref_out = ref(x_normal)
    assert wrapper_out.shape == (3, 3, 2, 2)
    assert torch.equal(wrapper_out, ref_out)
    wrapper = AdaptiveAvgPool2d(2)
    ref = nn.AdaptiveAvgPool2d(2)
    wrapper_out = wrapper(x_normal)
    ref_out = ref(x_normal)
    assert wrapper_out.shape == (3, 3, 2, 2)
    assert torch.equal(wrapper_out, ref_out)
    wrapper = AdaptiveAvgPool2d((None, 2))
    ref = nn.AdaptiveAvgPool2d((None, 2))
    wrapper_out = wrapper(x_normal)
    ref_out = ref(x_normal)
    assert wrapper_out.shape == (3, 3, 4, 2)
    assert torch.equal(wrapper_out, ref_out)
    wrapper = AdaptiveAvgPool2d((2, None))
    ref = nn.AdaptiveAvgPool2d((2, None))
    wrapper_out = wrapper(x_normal)
    ref_out = ref(x_normal)
    assert wrapper_out.shape == (3, 3, 2, 5)
    assert torch.equal(wrapper_out, ref_out)

def _build_demo_runner_without_hook(runner_type='EpochBasedRunner', max_epochs=1, max_iters=None, multi_optimziers=False):

    class Model(nn.Module):

        def __init__(self):
            super().__init__()
            self.linear = nn.Linear(2, 1)
            self.conv = nn.Conv2d(3, 3, 3)

        def forward(self, x):
            return self.linear(x)

        def train_step(self, x, optimizer, **kwargs):
            return dict(loss=self(x))

        def val_step(self, x, optimizer, **kwargs):
            return dict(loss=self(x))
    model = Model()
    if multi_optimziers:
        optimizer = {'model1': torch.optim.SGD(model.linear.parameters(), lr=0.02, momentum=0.95), 'model2': torch.optim.SGD(model.conv.parameters(), lr=0.01, momentum=0.9)}
    else:
        optimizer = torch.optim.SGD(model.parameters(), lr=0.02, momentum=0.95)
    tmp_dir = tempfile.mkdtemp()
    runner = build_runner(dict(type=runner_type), default_args=dict(model=model, work_dir=tmp_dir, optimizer=optimizer, logger=logging.getLogger(), max_epochs=max_epochs, max_iters=max_iters))
    return runner

def _build_demo_runner(runner_type='EpochBasedRunner', max_epochs=1, max_iters=None, multi_optimziers=False):
    log_config = dict(interval=1, hooks=[dict(type='TextLoggerHook')])
    runner = _build_demo_runner_without_hook(runner_type, max_epochs, max_iters, multi_optimziers)
    runner.register_checkpoint_hook(dict(interval=1))
    runner.register_logger_hooks(log_config)
    return runner

@pytest.mark.parametrize('multi_optimziers', (True, False))
def test_yolox_lrupdater_hook(multi_optimziers):
    """xdoctest -m tests/test_hooks.py test_cosine_runner_hook."""
    YOLOXLrUpdaterHook(0, min_lr_ratio=0.05)
    sys.modules['pavi'] = MagicMock()
    loader = DataLoader(torch.ones((10, 2)))
    runner = _build_demo_runner(multi_optimziers=multi_optimziers)
    hook_cfg = dict(type='YOLOXLrUpdaterHook', warmup='exp', by_epoch=False, warmup_by_epoch=True, warmup_ratio=1, warmup_iters=5, num_last_epochs=15, min_lr_ratio=0.05)
    runner.register_hook_from_cfg(hook_cfg)
    runner.register_hook_from_cfg(dict(type='IterTimerHook'))
    runner.register_hook(IterTimerHook())
    hook = PaviLoggerHook(interval=1, add_graph=False, add_last_ckpt=True)
    runner.register_hook(hook)
    runner.run([loader], [('train', 1)])
    shutil.rmtree(runner.work_dir)
    assert hasattr(hook, 'writer')
    if multi_optimziers:
        calls = [call('train', {'learning_rate/model1': 8.000000000000001e-06, 'learning_rate/model2': 4.000000000000001e-06, 'momentum/model1': 0.95, 'momentum/model2': 0.9}, 1), call('train', {'learning_rate/model1': 0.00039200000000000004, 'learning_rate/model2': 0.00019600000000000002, 'momentum/model1': 0.95, 'momentum/model2': 0.9}, 7), call('train', {'learning_rate/model1': 0.0008000000000000001, 'learning_rate/model2': 0.0004000000000000001, 'momentum/model1': 0.95, 'momentum/model2': 0.9}, 10)]
    else:
        calls = [call('train', {'learning_rate': 8.000000000000001e-06, 'momentum': 0.95}, 1), call('train', {'learning_rate': 0.00039200000000000004, 'momentum': 0.95}, 7), call('train', {'learning_rate': 0.0008000000000000001, 'momentum': 0.95}, 10)]
    hook.writer.add_scalars.assert_has_calls(calls, any_order=True)

def test_sync_norm_hook():
    SyncNormHook()
    loader = DataLoader(torch.ones((5, 2)))
    runner = _build_demo_runner()
    runner.register_hook_from_cfg(dict(type='SyncNormHook'))
    runner.run([loader, loader], [('train', 1), ('val', 1)])
    shutil.rmtree(runner.work_dir)

def test_sync_random_size_hook():
    SyncRandomSizeHook()

    class DemoDataset(Dataset):

        def __getitem__(self, item):
            return torch.ones(2)

        def __len__(self):
            return 5

        def update_dynamic_scale(self, dynamic_scale):
            pass
    loader = DataLoader(DemoDataset())
    runner = _build_demo_runner()
    runner.register_hook_from_cfg(dict(type='SyncRandomSizeHook', device='cpu'))
    runner.run([loader, loader], [('train', 1), ('val', 1)])
    shutil.rmtree(runner.work_dir)
    if torch.cuda.is_available():
        runner = _build_demo_runner()
        runner.register_hook_from_cfg(dict(type='SyncRandomSizeHook', device='cuda'))
        runner.run([loader, loader], [('train', 1), ('val', 1)])
        shutil.rmtree(runner.work_dir)

@pytest.mark.parametrize('set_loss', [dict(set_loss_nan=False, set_loss_inf=False), dict(set_loss_nan=True, set_loss_inf=False), dict(set_loss_nan=False, set_loss_inf=True)])
def test_check_invalid_loss_hook(set_loss):

    class DemoModel(nn.Module):

        def __init__(self, set_loss_nan=False, set_loss_inf=False):
            super().__init__()
            self.set_loss_nan = set_loss_nan
            self.set_loss_inf = set_loss_inf
            self.linear = nn.Linear(2, 1)

        def forward(self, x):
            return self.linear(x)

        def train_step(self, x, optimizer, **kwargs):
            if self.set_loss_nan:
                return dict(loss=torch.tensor(float('nan')))
            elif self.set_loss_inf:
                return dict(loss=torch.tensor(float('inf')))
            else:
                return dict(loss=self(x))
    loader = DataLoader(torch.ones((5, 2)))
    runner = _build_demo_runner()
    demo_model = DemoModel(**set_loss)
    runner.model = demo_model
    runner.register_hook_from_cfg(dict(type='CheckInvalidLossHook', interval=1))
    if not set_loss['set_loss_nan'] and (not set_loss['set_loss_inf']):
        runner.run([loader], [('train', 1)])
    else:
        with pytest.raises(AssertionError):
            runner.run([loader], [('train', 1)])
    shutil.rmtree(runner.work_dir)

def test_set_epoch_info_hook():
    """Test SetEpochInfoHook."""

    class DemoModel(nn.Module):

        def __init__(self):
            super().__init__()
            self.epoch = 0
            self.linear = nn.Linear(2, 1)

        def forward(self, x):
            return self.linear(x)

        def train_step(self, x, optimizer, **kwargs):
            return dict(loss=self(x))

        def set_epoch(self, epoch):
            self.epoch = epoch
    loader = DataLoader(torch.ones((5, 2)))
    runner = _build_demo_runner(max_epochs=3)
    demo_model = DemoModel()
    runner.model = demo_model
    runner.register_hook_from_cfg(dict(type='SetEpochInfoHook'))
    runner.run([loader], [('train', 1)])
    assert demo_model.epoch == 2

def test_memory_profiler_hook():
    from collections import namedtuple
    with pytest.raises(ImportError):
        from mmdet.core.hook import MemoryProfilerHook
        MemoryProfilerHook(1)
    sys.modules['psutil'] = MagicMock()
    with pytest.raises(ImportError):
        from mmdet.core.hook import MemoryProfilerHook
        MemoryProfilerHook(1)
    sys.modules['memory_profiler'] = MagicMock()

    def _mock_virtual_memory():
        virtual_memory_type = namedtuple('virtual_memory', ['total', 'available', 'percent', 'used'])
        return virtual_memory_type(total=270109085696, available=250416816128, percent=7.3, used=17840881664)

    def _mock_swap_memory():
        swap_memory_type = namedtuple('swap_memory', ['total', 'used', 'percent'])
        return swap_memory_type(total=8589930496, used=0, percent=0.0)

    def _mock_memory_usage():
        return [40.22265625]
    mock_virtual_memory = Mock(return_value=_mock_virtual_memory())
    mock_swap_memory = Mock(return_value=_mock_swap_memory())
    mock_memory_usage = Mock(return_value=_mock_memory_usage())

    @patch('psutil.swap_memory', mock_swap_memory)
    @patch('psutil.virtual_memory', mock_virtual_memory)
    @patch('memory_profiler.memory_usage', mock_memory_usage)
    def _test_memory_profiler_hook():
        from mmdet.core.hook import MemoryProfilerHook
        hook = MemoryProfilerHook(1)
        runner = _build_demo_runner()
        assert not mock_memory_usage.called
        assert not mock_swap_memory.called
        assert not mock_memory_usage.called
        hook.after_iter(runner)
        assert mock_memory_usage.called
        assert mock_swap_memory.called
        assert mock_memory_usage.called
    _test_memory_profiler_hook()

@patch('psutil.swap_memory', mock_swap_memory)
@patch('psutil.virtual_memory', mock_virtual_memory)
@patch('memory_profiler.memory_usage', mock_memory_usage)
def _test_memory_profiler_hook():
    from mmdet.core.hook import MemoryProfilerHook
    hook = MemoryProfilerHook(1)
    runner = _build_demo_runner()
    assert not mock_memory_usage.called
    assert not mock_swap_memory.called
    assert not mock_memory_usage.called
    hook.after_iter(runner)
    assert mock_memory_usage.called
    assert mock_swap_memory.called
    assert mock_memory_usage.called

@pytest.mark.skipif(not torch.cuda.is_available(), reason='requires CUDA support')
@patch('mmdet.apis.single_gpu_test', MagicMock)
@patch('mmdet.apis.multi_gpu_test', MagicMock)
@pytest.mark.parametrize('EvalHookCls', (EvalHook, DistEvalHook))
def test_eval_hook(EvalHookCls):
    with pytest.raises(TypeError):
        test_dataset = ExampleDataset()
        data_loader = [DataLoader(test_dataset, batch_size=1, sampler=None, num_worker=0, shuffle=False)]
        EvalHookCls(data_loader)
    with pytest.raises(KeyError):
        test_dataset = ExampleDataset()
        data_loader = DataLoader(test_dataset, batch_size=1, sampler=None, num_workers=0, shuffle=False)
        EvalHookCls(data_loader, save_best='auto', rule='unsupport')
    with pytest.raises(ValueError):
        test_dataset = ExampleDataset()
        data_loader = DataLoader(test_dataset, batch_size=1, sampler=None, num_workers=0, shuffle=False)
        EvalHookCls(data_loader, save_best='unsupport')
    optimizer_cfg = dict(type='SGD', lr=0.01, momentum=0.9, weight_decay=0.0001)
    test_dataset = ExampleDataset()
    loader = DataLoader(test_dataset, batch_size=1)
    model = ExampleModel()
    optimizer = build_optimizer(model, optimizer_cfg)
    data_loader = DataLoader(test_dataset, batch_size=1)
    eval_hook = EvalHookCls(data_loader, save_best=None)
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = get_logger('test_eval')
        runner = EpochBasedRunner(model=model, batch_processor=None, optimizer=optimizer, work_dir=tmpdir, logger=logger)
        runner.register_hook(eval_hook)
        runner.run([loader], [('train', 1)], 1)
        assert runner.meta is None or 'best_score' not in runner.meta['hook_msgs']
        assert runner.meta is None or 'best_ckpt' not in runner.meta['hook_msgs']
    loader = DataLoader(EvalDataset(), batch_size=1)
    model = ExampleModel()
    data_loader = DataLoader(EvalDataset(), batch_size=1)
    eval_hook = EvalHookCls(data_loader, interval=1, save_best='auto')
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = get_logger('test_eval')
        runner = EpochBasedRunner(model=model, batch_processor=None, optimizer=optimizer, work_dir=tmpdir, logger=logger)
        runner.register_checkpoint_hook(dict(interval=1))
        runner.register_hook(eval_hook)
        runner.run([loader], [('train', 1)], 8)
        real_path = osp.join(tmpdir, 'best_mAP_epoch_4.pth')
        assert runner.meta['hook_msgs']['best_ckpt'] == osp.realpath(real_path)
        assert runner.meta['hook_msgs']['best_score'] == 0.7
    loader = DataLoader(EvalDataset(), batch_size=1)
    model = ExampleModel()
    data_loader = DataLoader(EvalDataset(), batch_size=1)
    eval_hook = EvalHookCls(data_loader, interval=1, save_best='mAP')
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = get_logger('test_eval')
        runner = EpochBasedRunner(model=model, batch_processor=None, optimizer=optimizer, work_dir=tmpdir, logger=logger)
        runner.register_checkpoint_hook(dict(interval=1))
        runner.register_hook(eval_hook)
        runner.run([loader], [('train', 1)], 8)
        real_path = osp.join(tmpdir, 'best_mAP_epoch_4.pth')
        assert runner.meta['hook_msgs']['best_ckpt'] == osp.realpath(real_path)
        assert runner.meta['hook_msgs']['best_score'] == 0.7
    data_loader = DataLoader(EvalDataset(), batch_size=1)
    eval_hook = EvalHookCls(data_loader, interval=1, save_best='score', rule='greater')
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = get_logger('test_eval')
        runner = EpochBasedRunner(model=model, batch_processor=None, optimizer=optimizer, work_dir=tmpdir, logger=logger)
        runner.register_checkpoint_hook(dict(interval=1))
        runner.register_hook(eval_hook)
        runner.run([loader], [('train', 1)], 8)
        real_path = osp.join(tmpdir, 'best_score_epoch_4.pth')
        assert runner.meta['hook_msgs']['best_ckpt'] == osp.realpath(real_path)
        assert runner.meta['hook_msgs']['best_score'] == 0.7
    data_loader = DataLoader(EvalDataset(), batch_size=1)
    eval_hook = EvalHookCls(data_loader, save_best='mAP', rule='less')
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = get_logger('test_eval')
        runner = EpochBasedRunner(model=model, batch_processor=None, optimizer=optimizer, work_dir=tmpdir, logger=logger)
        runner.register_checkpoint_hook(dict(interval=1))
        runner.register_hook(eval_hook)
        runner.run([loader], [('train', 1)], 8)
        real_path = osp.join(tmpdir, 'best_mAP_epoch_6.pth')
        assert runner.meta['hook_msgs']['best_ckpt'] == osp.realpath(real_path)
        assert runner.meta['hook_msgs']['best_score'] == 0.05
    data_loader = DataLoader(EvalDataset(), batch_size=1)
    eval_hook = EvalHookCls(data_loader, save_best='mAP')
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = get_logger('test_eval')
        runner = EpochBasedRunner(model=model, batch_processor=None, optimizer=optimizer, work_dir=tmpdir, logger=logger)
        runner.register_checkpoint_hook(dict(interval=1))
        runner.register_hook(eval_hook)
        runner.run([loader], [('train', 1)], 2)
        real_path = osp.join(tmpdir, 'best_mAP_epoch_2.pth')
        assert runner.meta['hook_msgs']['best_ckpt'] == osp.realpath(real_path)
        assert runner.meta['hook_msgs']['best_score'] == 0.4
        resume_from = osp.join(tmpdir, 'latest.pth')
        loader = DataLoader(ExampleDataset(), batch_size=1)
        eval_hook = EvalHookCls(data_loader, save_best='mAP')
        runner = EpochBasedRunner(model=model, batch_processor=None, optimizer=optimizer, work_dir=tmpdir, logger=logger)
        runner.register_checkpoint_hook(dict(interval=1))
        runner.register_hook(eval_hook)
        runner.resume(resume_from)
        runner.run([loader], [('train', 1)], 8)
        real_path = osp.join(tmpdir, 'best_mAP_epoch_4.pth')
        assert runner.meta['hook_msgs']['best_ckpt'] == osp.realpath(real_path)
        assert runner.meta['hook_msgs']['best_score'] == 0.7

def _check_numclasscheckhook(detector, config_mod):
    dummy_runner = Mock()
    dummy_runner.model = detector

    def get_dataset_name_classes(dataset):
        if isinstance(dataset, (list, tuple)):
            dataset = dataset[0]
        while 'dataset' in dataset:
            dataset = dataset['dataset']
            if isinstance(dataset, (list, tuple)):
                dataset = dataset[0]
        return (dataset['type'], dataset.get('classes', None))
    compatible_check = NumClassCheckHook()
    dataset_name, CLASSES = get_dataset_name_classes(config_mod['data']['train'])
    if CLASSES is None:
        CLASSES = DATASETS.get(dataset_name).CLASSES
    dummy_runner.data_loader.dataset.CLASSES = CLASSES
    compatible_check.before_train_epoch(dummy_runner)
    dummy_runner.data_loader.dataset.CLASSES = None
    compatible_check.before_train_epoch(dummy_runner)
    dataset_name, CLASSES = get_dataset_name_classes(config_mod['data']['val'])
    if CLASSES is None:
        CLASSES = DATASETS.get(dataset_name).CLASSES
    dummy_runner.data_loader.dataset.CLASSES = CLASSES
    compatible_check.before_val_epoch(dummy_runner)
    dummy_runner.data_loader.dataset.CLASSES = None
    compatible_check.before_val_epoch(dummy_runner)

@patch('mmdet.apis.single_gpu_test', MagicMock)
@patch('mmdet.apis.multi_gpu_test', MagicMock)
@pytest.mark.parametrize('EvalHookParam', (EvalHook, DistEvalHook))
def test_evaluation_hook(EvalHookParam):
    dataloader = DataLoader(torch.ones((5, 2)))
    with pytest.raises(TypeError):
        EvalHookParam(dataloader=MagicMock(), interval=-1)
    with pytest.raises(ValueError):
        EvalHookParam(dataloader, interval=-1)
    runner = _build_demo_runner()
    evalhook = EvalHookParam(dataloader, interval=1)
    evalhook.evaluate = MagicMock()
    runner.register_hook(evalhook)
    runner.run([dataloader], [('train', 1)], 2)
    assert evalhook.evaluate.call_count == 2
    runner = _build_demo_runner()
    evalhook = EvalHookParam(dataloader, start=1, interval=1)
    evalhook.evaluate = MagicMock()
    runner.register_hook(evalhook)
    runner.run([dataloader], [('train', 1)], 2)
    assert evalhook.evaluate.call_count == 2
    runner = _build_demo_runner()
    evalhook = EvalHookParam(dataloader, interval=2)
    evalhook.evaluate = MagicMock()
    runner.register_hook(evalhook)
    runner.run([dataloader], [('train', 1)], 2)
    assert evalhook.evaluate.call_count == 1
    runner = _build_demo_runner()
    evalhook = EvalHookParam(dataloader, start=1, interval=2)
    evalhook.evaluate = MagicMock()
    runner.register_hook(evalhook)
    runner.run([dataloader], [('train', 1)], 3)
    assert evalhook.evaluate.call_count == 2
    runner = _build_demo_runner()
    evalhook = EvalHookParam(dataloader, start=0)
    evalhook.evaluate = MagicMock()
    runner.register_hook(evalhook)
    runner.run([dataloader], [('train', 1)], 2)
    assert evalhook.evaluate.call_count == 3
    runner = _build_demo_runner()
    evalhook = EvalHookParam(dataloader, start=0, interval=2, dynamic_intervals=[(3, 1)])
    evalhook.evaluate = MagicMock()
    runner.register_hook(evalhook)
    runner.run([dataloader], [('train', 1)], 4)
    assert evalhook.evaluate.call_count == 3
    runner = _build_demo_runner()
    with pytest.raises(ValueError):
        EvalHookParam(dataloader, start=-2)
    evalhook = EvalHookParam(dataloader, start=0)
    evalhook.evaluate = MagicMock()
    runner.register_hook(evalhook)
    runner.run([dataloader], [('train', 1)], 2)
    assert evalhook.evaluate.call_count == 3
    runner = _build_demo_runner()
    evalhook = EvalHookParam(dataloader, start=1)
    evalhook.evaluate = MagicMock()
    runner.register_hook(evalhook)
    runner._epoch = 2
    runner.run([dataloader], [('train', 1)], 3)
    assert evalhook.evaluate.call_count == 2
    runner = _build_demo_runner()
    evalhook = EvalHookParam(dataloader, start=2)
    evalhook.evaluate = MagicMock()
    runner.register_hook(evalhook)
    runner._epoch = 1
    runner.run([dataloader], [('train', 1)], 3)
    assert evalhook.evaluate.call_count == 2

def _build_demo_runner():

    class Model(nn.Module):

        def __init__(self):
            super().__init__()
            self.linear = nn.Linear(2, 1)

        def forward(self, x):
            return self.linear(x)

        def train_step(self, x, optimizer, **kwargs):
            return dict(loss=self(x))

        def val_step(self, x, optimizer, **kwargs):
            return dict(loss=self(x))
    model = Model()
    tmp_dir = tempfile.mkdtemp()
    runner = EpochBasedRunner(model=model, work_dir=tmp_dir, logger=logging.getLogger())
    return runner

@patch('mmdet.datasets.CocoDataset.load_annotations', MagicMock())
@patch('mmdet.datasets.CustomDataset.load_annotations', MagicMock())
@patch('mmdet.datasets.XMLDataset.load_annotations', MagicMock())
@patch('mmdet.datasets.CityscapesDataset.load_annotations', MagicMock())
@patch('mmdet.datasets.CocoDataset._filter_imgs', MagicMock)
@patch('mmdet.datasets.CustomDataset._filter_imgs', MagicMock)
@patch('mmdet.datasets.XMLDataset._filter_imgs', MagicMock)
@patch('mmdet.datasets.CityscapesDataset._filter_imgs', MagicMock)
@pytest.mark.parametrize('dataset', ['CocoDataset', 'VOCDataset', 'CityscapesDataset'])
def test_custom_classes_override_default(dataset):
    dataset_class = DATASETS.get(dataset)
    if dataset in ['CocoDataset', 'CityscapesDataset']:
        dataset_class.coco = MagicMock()
        dataset_class.cat_ids = MagicMock()
    original_classes = dataset_class.CLASSES
    custom_dataset = dataset_class(ann_file=MagicMock(), pipeline=[], classes=('bus', 'car'), test_mode=True, img_prefix='VOC2007' if dataset == 'VOCDataset' else '')
    assert custom_dataset.CLASSES != original_classes
    assert custom_dataset.CLASSES == ('bus', 'car')
    print(custom_dataset)
    custom_dataset = dataset_class(ann_file=MagicMock(), pipeline=[], classes=['bus', 'car'], test_mode=True, img_prefix='VOC2007' if dataset == 'VOCDataset' else '')
    assert custom_dataset.CLASSES != original_classes
    assert custom_dataset.CLASSES == ['bus', 'car']
    print(custom_dataset)
    custom_dataset = dataset_class(ann_file=MagicMock(), pipeline=[], classes=['foo'], test_mode=True, img_prefix='VOC2007' if dataset == 'VOCDataset' else '')
    assert custom_dataset.CLASSES != original_classes
    assert custom_dataset.CLASSES == ['foo']
    print(custom_dataset)
    custom_dataset = dataset_class(ann_file=MagicMock(), pipeline=[], classes=None, test_mode=True, img_prefix='VOC2007' if dataset == 'VOCDataset' else '')
    assert custom_dataset.CLASSES == original_classes
    print(custom_dataset)
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        path = tmpdir + 'classes.txt'
        with open(path, 'w') as f:
            f.write('bus\ncar\n')
    custom_dataset = dataset_class(ann_file=MagicMock(), pipeline=[], classes=path, test_mode=True, img_prefix='VOC2007' if dataset == 'VOCDataset' else '')
    assert custom_dataset.CLASSES != original_classes
    assert custom_dataset.CLASSES == ['bus', 'car']
    print(custom_dataset)

def get_logger(name='root'):
    formatter = logging.Formatter(fmt='%(asctime)s [%(levelname)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    return logger

