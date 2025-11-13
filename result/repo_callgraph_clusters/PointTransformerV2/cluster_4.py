# Cluster 4

def is_filepath(x):
    return is_str(x) or isinstance(x, Path)

def fopen(filepath, *args, **kwargs):
    if is_str(filepath):
        return open(filepath, *args, **kwargs)
    elif isinstance(filepath, Path):
        return filepath.open(*args, **kwargs)
    raise ValueError('`filepath` should be a string or a Path')

def mkdir_or_exist(dir_name, mode=511):
    if dir_name == '':
        return
    dir_name = osp.expanduser(dir_name)
    os.makedirs(dir_name, mode=mode, exist_ok=True)

def symlink(src, dst, overwrite=True, **kwargs):
    if os.path.lexists(dst) and overwrite:
        os.remove(dst)
    os.symlink(src, dst, **kwargs)

def scandir(dir_path, suffix=None, recursive=False, case_sensitive=True):
    """Scan a directory to find the interested files.

    Args:
        dir_path (str | obj:`Path`): Path of the directory.
        suffix (str | tuple(str), optional): File suffix that we are
            interested in. Default: None.
        recursive (bool, optional): If set to True, recursively scan the
            directory. Default: False.
        case_sensitive (bool, optional) : If set to False, ignore the case of
            suffix. Default: True.

    Returns:
        A generator for all the interested files with relative paths.
    """
    if isinstance(dir_path, (str, Path)):
        dir_path = str(dir_path)
    else:
        raise TypeError('"dir_path" must be a string or Path object')
    if suffix is not None and (not isinstance(suffix, (str, tuple))):
        raise TypeError('"suffix" must be a string or tuple of strings')
    if suffix is not None and (not case_sensitive):
        suffix = suffix.lower() if isinstance(suffix, str) else tuple((item.lower() for item in suffix))
    root = dir_path

    def _scandir(dir_path, suffix, recursive, case_sensitive):
        for entry in os.scandir(dir_path):
            if not entry.name.startswith('.') and entry.is_file():
                rel_path = osp.relpath(entry.path, root)
                _rel_path = rel_path if case_sensitive else rel_path.lower()
                if suffix is None or _rel_path.endswith(suffix):
                    yield rel_path
            elif recursive and os.path.isdir(entry.path):
                yield from _scandir(entry.path, suffix, recursive, case_sensitive)
    return _scandir(dir_path, suffix, recursive, case_sensitive)

def find_vcs_root(path, markers=('.git',)):
    """Finds the root directory (including itself) of specified markers.

    Args:
        path (str): Path of directory or file.
        markers (list[str], optional): List of file or directory names.

    Returns:
        The directory contained one of the markers or None if not found.
    """
    if osp.isfile(path):
        path = osp.dirname(path)
    prev, cur = (None, osp.abspath(osp.expanduser(path)))
    while cur != prev:
        if any((osp.exists(osp.join(cur, marker)) for marker in markers)):
            return cur
        prev, cur = (cur, osp.split(cur)[0])
    return None

class JSONWriter(EventWriter):
    """
    Write scalars to a json file.
    It saves scalars as one json per line (instead of a big json) for easy parsing.
    Examples parsing such a json file:
    ::
        $ cat metrics.json | jq -s '.[0:2]'
        [
          {
            "data_time": 0.008433341979980469,
            "iteration": 19,
            "loss": 1.9228371381759644,
            "loss_box_reg": 0.050025828182697296,
            "loss_classifier": 0.5316952466964722,
            "loss_mask": 0.7236229181289673,
            "loss_rpn_box": 0.0856662318110466,
            "loss_rpn_cls": 0.48198649287223816,
            "lr": 0.007173333333333333,
            "time": 0.25401854515075684
          },
          {
            "data_time": 0.007216215133666992,
            "iteration": 39,
            "loss": 1.282649278640747,
            "loss_box_reg": 0.06222952902317047,
            "loss_classifier": 0.30682939291000366,
            "loss_mask": 0.6970193982124329,
            "loss_rpn_box": 0.038663312792778015,
            "loss_rpn_cls": 0.1471673548221588,
            "lr": 0.007706666666666667,
            "time": 0.2490077018737793
          }
        ]
        $ cat metrics.json | jq '.loss_mask'
        0.7126231789588928
        0.689423680305481
        0.6776131987571716
        ...
    """

    def __init__(self, json_file, window_size=20):
        """
        Args:
            json_file (str): path to the json file. New data will be appended if the file exists.
            window_size (int): the window size of median smoothing for the scalars whose
                `smoothing_hint` are True.
        """
        self._file_handle = open(json_file, 'a')
        self._window_size = window_size
        self._last_write = -1

    def write(self):
        storage = get_event_storage()
        to_save = defaultdict(dict)
        for k, (v, iter) in storage.latest_with_smoothing_hint(self._window_size).items():
            if iter <= self._last_write:
                continue
            to_save[iter][k] = v
        if len(to_save):
            all_iters = sorted(to_save.keys())
            self._last_write = max(all_iters)
        for itr, scalars_per_iter in to_save.items():
            scalars_per_iter['iteration'] = itr
            self._file_handle.write(json.dumps(scalars_per_iter, sort_keys=True) + '\n')
        self._file_handle.flush()
        try:
            os.fsync(self._file_handle.fileno())
        except AttributeError:
            pass

    def close(self):
        self._file_handle.close()

def __init__(self, json_file, window_size=20):
    """
        Args:
            json_file (str): path to the json file. New data will be appended if the file exists.
            window_size (int): the window size of median smoothing for the scalars whose
                `smoothing_hint` are True.
        """
    self._file_handle = open(json_file, 'a')
    self._window_size = window_size
    self._last_write = -1

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

def reset_history(self, name):
    ret = self._history.get(name, None)
    if ret is None:
        raise KeyError('No history metric available for {}!'.format(name))
    ret.reset()

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

def median(self, window_size: int) -> float:
    """
        Return the median of the latest `window_size` values in the buffer.
        """
    return np.median([x[0] for x in self._data[-window_size:]])

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

def __missing__(self, name):
    raise KeyError(name)

def add_args(parser, cfg, prefix=''):
    for k, v in cfg.items():
        if isinstance(v, str):
            parser.add_argument('--' + prefix + k)
        elif isinstance(v, int):
            parser.add_argument('--' + prefix + k, type=int)
        elif isinstance(v, float):
            parser.add_argument('--' + prefix + k, type=float)
        elif isinstance(v, bool):
            parser.add_argument('--' + prefix + k, action='store_true')
        elif isinstance(v, dict):
            add_args(parser, v, prefix + k + '.')
        elif isinstance(v, abc.Iterable):
            parser.add_argument('--' + prefix + k, type=type(v[0]), nargs='+')
        else:
            print(f'cannot parse key {prefix + k} of type {type(v)}')
    return parser

class Config:
    """A facility for config and config files.

    It supports common file formats as configs: python/json/yaml. The interface
    is the same as a dict object and also allows access config values as
    attributes.

    Example:
        >>> cfg = Config(dict(a=1, b=dict(b1=[0, 1])))
        >>> cfg.a
        1
        >>> cfg.b
        {'b1': [0, 1]}
        >>> cfg.b.b1
        [0, 1]
        >>> cfg = Config.fromfile('tests/data/config/a.py')
        >>> cfg.filename
        "/home/kchen/projects/mmcv/tests/data/config/a.py"
        >>> cfg.item4
        'test'
        >>> cfg
        "Config [path: /home/kchen/projects/mmcv/tests/data/config/a.py]: "
        "{'item1': [1, 2], 'item2': {'a': 0}, 'item3': True, 'item4': 'test'}"
    """

    @staticmethod
    def _validate_py_syntax(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        try:
            ast.parse(content)
        except SyntaxError as e:
            raise SyntaxError(f'There are syntax errors in config file {filename}: {e}')

    @staticmethod
    def _substitute_predefined_vars(filename, temp_config_name):
        file_dirname = osp.dirname(filename)
        file_basename = osp.basename(filename)
        file_basename_no_extension = osp.splitext(file_basename)[0]
        file_extname = osp.splitext(filename)[1]
        support_templates = dict(fileDirname=file_dirname, fileBasename=file_basename, fileBasenameNoExtension=file_basename_no_extension, fileExtname=file_extname)
        with open(filename, 'r', encoding='utf-8') as f:
            config_file = f.read()
        for key, value in support_templates.items():
            regexp = '\\{\\{\\s*' + str(key) + '\\s*\\}\\}'
            value = value.replace('\\', '/')
            config_file = re.sub(regexp, value, config_file)
        with open(temp_config_name, 'w', encoding='utf-8') as tmp_config_file:
            tmp_config_file.write(config_file)

    @staticmethod
    def _pre_substitute_base_vars(filename, temp_config_name):
        """Substitute base variable placehoders to string, so that parsing
        would work."""
        with open(filename, 'r', encoding='utf-8') as f:
            config_file = f.read()
        base_var_dict = {}
        regexp = '\\{\\{\\s*' + BASE_KEY + '\\.([\\w\\.]+)\\s*\\}\\}'
        base_vars = set(re.findall(regexp, config_file))
        for base_var in base_vars:
            randstr = f'_{base_var}_{uuid.uuid4().hex.lower()[:6]}'
            base_var_dict[randstr] = base_var
            regexp = '\\{\\{\\s*' + BASE_KEY + '\\.' + base_var + '\\s*\\}\\}'
            config_file = re.sub(regexp, f'"{randstr}"', config_file)
        with open(temp_config_name, 'w', encoding='utf-8') as tmp_config_file:
            tmp_config_file.write(config_file)
        return base_var_dict

    @staticmethod
    def _substitute_base_vars(cfg, base_var_dict, base_cfg):
        """Substitute variable strings to their actual values."""
        cfg = copy.deepcopy(cfg)
        if isinstance(cfg, dict):
            for k, v in cfg.items():
                if isinstance(v, str) and v in base_var_dict:
                    new_v = base_cfg
                    for new_k in base_var_dict[v].split('.'):
                        new_v = new_v[new_k]
                    cfg[k] = new_v
                elif isinstance(v, (list, tuple, dict)):
                    cfg[k] = Config._substitute_base_vars(v, base_var_dict, base_cfg)
        elif isinstance(cfg, tuple):
            cfg = tuple((Config._substitute_base_vars(c, base_var_dict, base_cfg) for c in cfg))
        elif isinstance(cfg, list):
            cfg = [Config._substitute_base_vars(c, base_var_dict, base_cfg) for c in cfg]
        elif isinstance(cfg, str) and cfg in base_var_dict:
            new_v = base_cfg
            for new_k in base_var_dict[cfg].split('.'):
                new_v = new_v[new_k]
            cfg = new_v
        return cfg

    @staticmethod
    def _file2dict(filename, use_predefined_variables=True):
        filename = osp.abspath(osp.expanduser(filename))
        check_file_exist(filename)
        fileExtname = osp.splitext(filename)[1]
        if fileExtname not in ['.py', '.json', '.yaml', '.yml']:
            raise IOError('Only py/yml/yaml/json type are supported now!')
        with tempfile.TemporaryDirectory() as temp_config_dir:
            temp_config_file = tempfile.NamedTemporaryFile(dir=temp_config_dir, suffix=fileExtname)
            if platform.system() == 'Windows':
                temp_config_file.close()
            temp_config_name = osp.basename(temp_config_file.name)
            if use_predefined_variables:
                Config._substitute_predefined_vars(filename, temp_config_file.name)
            else:
                shutil.copyfile(filename, temp_config_file.name)
            base_var_dict = Config._pre_substitute_base_vars(temp_config_file.name, temp_config_file.name)
            if filename.endswith('.py'):
                temp_module_name = osp.splitext(temp_config_name)[0]
                sys.path.insert(0, temp_config_dir)
                Config._validate_py_syntax(filename)
                mod = import_module(temp_module_name)
                sys.path.pop(0)
                cfg_dict = {name: value for name, value in mod.__dict__.items() if not name.startswith('__')}
                del sys.modules[temp_module_name]
            elif filename.endswith(('.yml', '.yaml', '.json')):
                raise NotImplementedError
            temp_config_file.close()
        if DEPRECATION_KEY in cfg_dict:
            deprecation_info = cfg_dict.pop(DEPRECATION_KEY)
            warning_msg = f'The config file {filename} will be deprecated in the future.'
            if 'expected' in deprecation_info:
                warning_msg += f' Please use {deprecation_info['expected']} instead.'
            if 'reference' in deprecation_info:
                warning_msg += f' More information can be found at {deprecation_info['reference']}'
            warnings.warn(warning_msg)
        cfg_text = filename + '\n'
        with open(filename, 'r', encoding='utf-8') as f:
            cfg_text += f.read()
        if BASE_KEY in cfg_dict:
            cfg_dir = osp.dirname(filename)
            base_filename = cfg_dict.pop(BASE_KEY)
            base_filename = base_filename if isinstance(base_filename, list) else [base_filename]
            cfg_dict_list = list()
            cfg_text_list = list()
            for f in base_filename:
                _cfg_dict, _cfg_text = Config._file2dict(osp.join(cfg_dir, f))
                cfg_dict_list.append(_cfg_dict)
                cfg_text_list.append(_cfg_text)
            base_cfg_dict = dict()
            for c in cfg_dict_list:
                duplicate_keys = base_cfg_dict.keys() & c.keys()
                if len(duplicate_keys) > 0:
                    raise KeyError(f'Duplicate key is not allowed among bases. Duplicate keys: {duplicate_keys}')
                base_cfg_dict.update(c)
            cfg_dict = Config._substitute_base_vars(cfg_dict, base_var_dict, base_cfg_dict)
            base_cfg_dict = Config._merge_a_into_b(cfg_dict, base_cfg_dict)
            cfg_dict = base_cfg_dict
            cfg_text_list.append(cfg_text)
            cfg_text = '\n'.join(cfg_text_list)
        return (cfg_dict, cfg_text)

    @staticmethod
    def _merge_a_into_b(a, b, allow_list_keys=False):
        """merge dict ``a`` into dict ``b`` (non-inplace).

        Values in ``a`` will overwrite ``b``. ``b`` is copied first to avoid
        in-place modifications.

        Args:
            a (dict): The source dict to be merged into ``b``.
            b (dict): The origin dict to be fetch keys from ``a``.
            allow_list_keys (bool): If True, int string keys (e.g. '0', '1')
              are allowed in source ``a`` and will replace the element of the
              corresponding index in b if b is a list. Default: False.

        Returns:
            dict: The modified dict of ``b`` using ``a``.

        Examples:
            # Normally merge a into b.
            >>> Config._merge_a_into_b(
            ...     dict(obj=dict(a=2)), dict(obj=dict(a=1)))
            {'obj': {'a': 2}}

            # Delete b first and merge a into b.
            >>> Config._merge_a_into_b(
            ...     dict(obj=dict(_delete_=True, a=2)), dict(obj=dict(a=1)))
            {'obj': {'a': 2}}

            # b is a list
            >>> Config._merge_a_into_b(
            ...     {'0': dict(a=2)}, [dict(a=1), dict(b=2)], True)
            [{'a': 2}, {'b': 2}]
        """
        b = b.copy()
        for k, v in a.items():
            if allow_list_keys and k.isdigit() and isinstance(b, list):
                k = int(k)
                if len(b) <= k:
                    raise KeyError(f'Index {k} exceeds the length of list {b}')
                b[k] = Config._merge_a_into_b(v, b[k], allow_list_keys)
            elif isinstance(v, dict) and k in b and (not v.pop(DELETE_KEY, False)):
                allowed_types = (dict, list) if allow_list_keys else dict
                if not isinstance(b[k], allowed_types):
                    raise TypeError(f'{k}={v} in child config cannot inherit from base because {k} is a dict in the child config but is of type {type(b[k])} in base config. You may set `{DELETE_KEY}=True` to ignore the base config')
                b[k] = Config._merge_a_into_b(v, b[k], allow_list_keys)
            else:
                b[k] = v
        return b

    @staticmethod
    def fromfile(filename, use_predefined_variables=True, import_custom_modules=True):
        cfg_dict, cfg_text = Config._file2dict(filename, use_predefined_variables)
        if import_custom_modules and cfg_dict.get('custom_imports', None):
            import_modules_from_strings(**cfg_dict['custom_imports'])
        return Config(cfg_dict, cfg_text=cfg_text, filename=filename)

    @staticmethod
    def fromstring(cfg_str, file_format):
        """Generate config from config str.

        Args:
            cfg_str (str): Config str.
            file_format (str): Config file format corresponding to the
               config str. Only py/yml/yaml/json type are supported now!

        Returns:
            obj:`Config`: Config obj.
        """
        if file_format not in ['.py', '.json', '.yaml', '.yml']:
            raise IOError('Only py/yml/yaml/json type are supported now!')
        if file_format != '.py' and 'dict(' in cfg_str:
            warnings.warn('Please check "file_format", the file format may be .py')
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', suffix=file_format, delete=False) as temp_file:
            temp_file.write(cfg_str)
        cfg = Config.fromfile(temp_file.name)
        os.remove(temp_file.name)
        return cfg

    @staticmethod
    def auto_argparser(description=None):
        """Generate argparser from config file automatically (experimental)"""
        partial_parser = ArgumentParser(description=description)
        partial_parser.add_argument('config', help='config file path')
        cfg_file = partial_parser.parse_known_args()[0].config
        cfg = Config.fromfile(cfg_file)
        parser = ArgumentParser(description=description)
        parser.add_argument('config', help='config file path')
        add_args(parser, cfg)
        return (parser, cfg)

    def __init__(self, cfg_dict=None, cfg_text=None, filename=None):
        if cfg_dict is None:
            cfg_dict = dict()
        elif not isinstance(cfg_dict, dict):
            raise TypeError(f'cfg_dict must be a dict, but got {type(cfg_dict)}')
        for key in cfg_dict:
            if key in RESERVED_KEYS:
                raise KeyError(f'{key} is reserved for config file')
        super(Config, self).__setattr__('_cfg_dict', ConfigDict(cfg_dict))
        super(Config, self).__setattr__('_filename', filename)
        if cfg_text:
            text = cfg_text
        elif filename:
            with open(filename, 'r') as f:
                text = f.read()
        else:
            text = ''
        super(Config, self).__setattr__('_text', text)

    @property
    def filename(self):
        return self._filename

    @property
    def text(self):
        return self._text

    @property
    def pretty_text(self):
        indent = 4

        def _indent(s_, num_spaces):
            s = s_.split('\n')
            if len(s) == 1:
                return s_
            first = s.pop(0)
            s = [num_spaces * ' ' + line for line in s]
            s = '\n'.join(s)
            s = first + '\n' + s
            return s

        def _format_basic_types(k, v, use_mapping=False):
            if isinstance(v, str):
                v_str = f"'{v}'"
            else:
                v_str = str(v)
            if use_mapping:
                k_str = f"'{k}'" if isinstance(k, str) else str(k)
                attr_str = f'{k_str}: {v_str}'
            else:
                attr_str = f'{str(k)}={v_str}'
            attr_str = _indent(attr_str, indent)
            return attr_str

        def _format_list(k, v, use_mapping=False):
            if all((isinstance(_, dict) for _ in v)):
                v_str = '[\n'
                v_str += '\n'.join((f'dict({_indent(_format_dict(v_), indent)}),' for v_ in v)).rstrip(',')
                if use_mapping:
                    k_str = f"'{k}'" if isinstance(k, str) else str(k)
                    attr_str = f'{k_str}: {v_str}'
                else:
                    attr_str = f'{str(k)}={v_str}'
                attr_str = _indent(attr_str, indent) + ']'
            else:
                attr_str = _format_basic_types(k, v, use_mapping)
            return attr_str

        def _contain_invalid_identifier(dict_str):
            contain_invalid_identifier = False
            for key_name in dict_str:
                contain_invalid_identifier |= not str(key_name).isidentifier()
            return contain_invalid_identifier

        def _format_dict(input_dict, outest_level=False):
            r = ''
            s = []
            use_mapping = _contain_invalid_identifier(input_dict)
            if use_mapping:
                r += '{'
            for idx, (k, v) in enumerate(input_dict.items()):
                is_last = idx >= len(input_dict) - 1
                end = '' if outest_level or is_last else ','
                if isinstance(v, dict):
                    v_str = '\n' + _format_dict(v)
                    if use_mapping:
                        k_str = f"'{k}'" if isinstance(k, str) else str(k)
                        attr_str = f'{k_str}: dict({v_str}'
                    else:
                        attr_str = f'{str(k)}=dict({v_str}'
                    attr_str = _indent(attr_str, indent) + ')' + end
                elif isinstance(v, list):
                    attr_str = _format_list(k, v, use_mapping) + end
                else:
                    attr_str = _format_basic_types(k, v, use_mapping) + end
                s.append(attr_str)
            r += '\n'.join(s)
            if use_mapping:
                r += '}'
            return r
        cfg_dict = self._cfg_dict.to_dict()
        text = _format_dict(cfg_dict, outest_level=True)
        yapf_style = dict(based_on_style='pep8', blank_line_before_nested_class_or_def=True, split_before_expression_after_opening_paren=True)
        text, _ = FormatCode(text, style_config=yapf_style, verify=True)
        return text

    def __repr__(self):
        return f'Config (path: {self.filename}): {self._cfg_dict.__repr__()}'

    def __len__(self):
        return len(self._cfg_dict)

    def __getattr__(self, name):
        return getattr(self._cfg_dict, name)

    def __getitem__(self, name):
        return self._cfg_dict.__getitem__(name)

    def __setattr__(self, name, value):
        if isinstance(value, dict):
            value = ConfigDict(value)
        self._cfg_dict.__setattr__(name, value)

    def __setitem__(self, name, value):
        if isinstance(value, dict):
            value = ConfigDict(value)
        self._cfg_dict.__setitem__(name, value)

    def __iter__(self):
        return iter(self._cfg_dict)

    def __getstate__(self):
        return (self._cfg_dict, self._filename, self._text)

    def __setstate__(self, state):
        _cfg_dict, _filename, _text = state
        super(Config, self).__setattr__('_cfg_dict', _cfg_dict)
        super(Config, self).__setattr__('_filename', _filename)
        super(Config, self).__setattr__('_text', _text)

    def dump(self, file=None):
        cfg_dict = super(Config, self).__getattribute__('_cfg_dict').to_dict()
        if self.filename.endswith('.py'):
            if file is None:
                return self.pretty_text
            else:
                with open(file, 'w', encoding='utf-8') as f:
                    f.write(self.pretty_text)
        else:
            import mmcv
            if file is None:
                file_format = self.filename.split('.')[-1]
                return mmcv.dump(cfg_dict, file_format=file_format)
            else:
                mmcv.dump(cfg_dict, file)

    def merge_from_dict(self, options, allow_list_keys=True):
        """Merge list into cfg_dict.

        Merge the dict parsed by MultipleKVAction into this cfg.

        Examples:
            >>> options = {'models.backbone.depth': 50,
            ...            'models.backbone.with_cp':True}
            >>> cfg = Config(dict(models=dict(backbone=dict(type='ResNet'))))
            >>> cfg.merge_from_dict(options)
            >>> cfg_dict = super(Config, self).__getattribute__('_cfg_dict')
            >>> assert cfg_dict == dict(
            ...     models=dict(backbone=dict(depth=50, with_cp=True)))

            # Merge list element
            >>> cfg = Config(dict(pipeline=[
            ...     dict(type='LoadImage'), dict(type='LoadAnnotations')]))
            >>> options = dict(pipeline={'0': dict(type='SelfLoadImage')})
            >>> cfg.merge_from_dict(options, allow_list_keys=True)
            >>> cfg_dict = super(Config, self).__getattribute__('_cfg_dict')
            >>> assert cfg_dict == dict(pipeline=[
            ...     dict(type='SelfLoadImage'), dict(type='LoadAnnotations')])

        Args:
            options (dict): dict of configs to merge from.
            allow_list_keys (bool): If True, int string keys (e.g. '0', '1')
              are allowed in ``options`` and will replace the element of the
              corresponding index in the config if the config is a list.
              Default: True.
        """
        option_cfg_dict = {}
        for full_key, v in options.items():
            d = option_cfg_dict
            key_list = full_key.split('.')
            for subkey in key_list[:-1]:
                d.setdefault(subkey, ConfigDict())
                d = d[subkey]
            subkey = key_list[-1]
            d[subkey] = v
        cfg_dict = super(Config, self).__getattribute__('_cfg_dict')
        super(Config, self).__setattr__('_cfg_dict', Config._merge_a_into_b(option_cfg_dict, cfg_dict, allow_list_keys=allow_list_keys))

@staticmethod
def _validate_py_syntax(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    try:
        ast.parse(content)
    except SyntaxError as e:
        raise SyntaxError(f'There are syntax errors in config file {filename}: {e}')

@staticmethod
def _substitute_predefined_vars(filename, temp_config_name):
    file_dirname = osp.dirname(filename)
    file_basename = osp.basename(filename)
    file_basename_no_extension = osp.splitext(file_basename)[0]
    file_extname = osp.splitext(filename)[1]
    support_templates = dict(fileDirname=file_dirname, fileBasename=file_basename, fileBasenameNoExtension=file_basename_no_extension, fileExtname=file_extname)
    with open(filename, 'r', encoding='utf-8') as f:
        config_file = f.read()
    for key, value in support_templates.items():
        regexp = '\\{\\{\\s*' + str(key) + '\\s*\\}\\}'
        value = value.replace('\\', '/')
        config_file = re.sub(regexp, value, config_file)
    with open(temp_config_name, 'w', encoding='utf-8') as tmp_config_file:
        tmp_config_file.write(config_file)

@staticmethod
def _pre_substitute_base_vars(filename, temp_config_name):
    """Substitute base variable placehoders to string, so that parsing
        would work."""
    with open(filename, 'r', encoding='utf-8') as f:
        config_file = f.read()
    base_var_dict = {}
    regexp = '\\{\\{\\s*' + BASE_KEY + '\\.([\\w\\.]+)\\s*\\}\\}'
    base_vars = set(re.findall(regexp, config_file))
    for base_var in base_vars:
        randstr = f'_{base_var}_{uuid.uuid4().hex.lower()[:6]}'
        base_var_dict[randstr] = base_var
        regexp = '\\{\\{\\s*' + BASE_KEY + '\\.' + base_var + '\\s*\\}\\}'
        config_file = re.sub(regexp, f'"{randstr}"', config_file)
    with open(temp_config_name, 'w', encoding='utf-8') as tmp_config_file:
        tmp_config_file.write(config_file)
    return base_var_dict

@staticmethod
def _substitute_base_vars(cfg, base_var_dict, base_cfg):
    """Substitute variable strings to their actual values."""
    cfg = copy.deepcopy(cfg)
    if isinstance(cfg, dict):
        for k, v in cfg.items():
            if isinstance(v, str) and v in base_var_dict:
                new_v = base_cfg
                for new_k in base_var_dict[v].split('.'):
                    new_v = new_v[new_k]
                cfg[k] = new_v
            elif isinstance(v, (list, tuple, dict)):
                cfg[k] = Config._substitute_base_vars(v, base_var_dict, base_cfg)
    elif isinstance(cfg, tuple):
        cfg = tuple((Config._substitute_base_vars(c, base_var_dict, base_cfg) for c in cfg))
    elif isinstance(cfg, list):
        cfg = [Config._substitute_base_vars(c, base_var_dict, base_cfg) for c in cfg]
    elif isinstance(cfg, str) and cfg in base_var_dict:
        new_v = base_cfg
        for new_k in base_var_dict[cfg].split('.'):
            new_v = new_v[new_k]
        cfg = new_v
    return cfg

@staticmethod
def _file2dict(filename, use_predefined_variables=True):
    filename = osp.abspath(osp.expanduser(filename))
    check_file_exist(filename)
    fileExtname = osp.splitext(filename)[1]
    if fileExtname not in ['.py', '.json', '.yaml', '.yml']:
        raise IOError('Only py/yml/yaml/json type are supported now!')
    with tempfile.TemporaryDirectory() as temp_config_dir:
        temp_config_file = tempfile.NamedTemporaryFile(dir=temp_config_dir, suffix=fileExtname)
        if platform.system() == 'Windows':
            temp_config_file.close()
        temp_config_name = osp.basename(temp_config_file.name)
        if use_predefined_variables:
            Config._substitute_predefined_vars(filename, temp_config_file.name)
        else:
            shutil.copyfile(filename, temp_config_file.name)
        base_var_dict = Config._pre_substitute_base_vars(temp_config_file.name, temp_config_file.name)
        if filename.endswith('.py'):
            temp_module_name = osp.splitext(temp_config_name)[0]
            sys.path.insert(0, temp_config_dir)
            Config._validate_py_syntax(filename)
            mod = import_module(temp_module_name)
            sys.path.pop(0)
            cfg_dict = {name: value for name, value in mod.__dict__.items() if not name.startswith('__')}
            del sys.modules[temp_module_name]
        elif filename.endswith(('.yml', '.yaml', '.json')):
            raise NotImplementedError
        temp_config_file.close()
    if DEPRECATION_KEY in cfg_dict:
        deprecation_info = cfg_dict.pop(DEPRECATION_KEY)
        warning_msg = f'The config file {filename} will be deprecated in the future.'
        if 'expected' in deprecation_info:
            warning_msg += f' Please use {deprecation_info['expected']} instead.'
        if 'reference' in deprecation_info:
            warning_msg += f' More information can be found at {deprecation_info['reference']}'
        warnings.warn(warning_msg)
    cfg_text = filename + '\n'
    with open(filename, 'r', encoding='utf-8') as f:
        cfg_text += f.read()
    if BASE_KEY in cfg_dict:
        cfg_dir = osp.dirname(filename)
        base_filename = cfg_dict.pop(BASE_KEY)
        base_filename = base_filename if isinstance(base_filename, list) else [base_filename]
        cfg_dict_list = list()
        cfg_text_list = list()
        for f in base_filename:
            _cfg_dict, _cfg_text = Config._file2dict(osp.join(cfg_dir, f))
            cfg_dict_list.append(_cfg_dict)
            cfg_text_list.append(_cfg_text)
        base_cfg_dict = dict()
        for c in cfg_dict_list:
            duplicate_keys = base_cfg_dict.keys() & c.keys()
            if len(duplicate_keys) > 0:
                raise KeyError(f'Duplicate key is not allowed among bases. Duplicate keys: {duplicate_keys}')
            base_cfg_dict.update(c)
        cfg_dict = Config._substitute_base_vars(cfg_dict, base_var_dict, base_cfg_dict)
        base_cfg_dict = Config._merge_a_into_b(cfg_dict, base_cfg_dict)
        cfg_dict = base_cfg_dict
        cfg_text_list.append(cfg_text)
        cfg_text = '\n'.join(cfg_text_list)
    return (cfg_dict, cfg_text)

@staticmethod
def _merge_a_into_b(a, b, allow_list_keys=False):
    """merge dict ``a`` into dict ``b`` (non-inplace).

        Values in ``a`` will overwrite ``b``. ``b`` is copied first to avoid
        in-place modifications.

        Args:
            a (dict): The source dict to be merged into ``b``.
            b (dict): The origin dict to be fetch keys from ``a``.
            allow_list_keys (bool): If True, int string keys (e.g. '0', '1')
              are allowed in source ``a`` and will replace the element of the
              corresponding index in b if b is a list. Default: False.

        Returns:
            dict: The modified dict of ``b`` using ``a``.

        Examples:
            # Normally merge a into b.
            >>> Config._merge_a_into_b(
            ...     dict(obj=dict(a=2)), dict(obj=dict(a=1)))
            {'obj': {'a': 2}}

            # Delete b first and merge a into b.
            >>> Config._merge_a_into_b(
            ...     dict(obj=dict(_delete_=True, a=2)), dict(obj=dict(a=1)))
            {'obj': {'a': 2}}

            # b is a list
            >>> Config._merge_a_into_b(
            ...     {'0': dict(a=2)}, [dict(a=1), dict(b=2)], True)
            [{'a': 2}, {'b': 2}]
        """
    b = b.copy()
    for k, v in a.items():
        if allow_list_keys and k.isdigit() and isinstance(b, list):
            k = int(k)
            if len(b) <= k:
                raise KeyError(f'Index {k} exceeds the length of list {b}')
            b[k] = Config._merge_a_into_b(v, b[k], allow_list_keys)
        elif isinstance(v, dict) and k in b and (not v.pop(DELETE_KEY, False)):
            allowed_types = (dict, list) if allow_list_keys else dict
            if not isinstance(b[k], allowed_types):
                raise TypeError(f'{k}={v} in child config cannot inherit from base because {k} is a dict in the child config but is of type {type(b[k])} in base config. You may set `{DELETE_KEY}=True` to ignore the base config')
            b[k] = Config._merge_a_into_b(v, b[k], allow_list_keys)
        else:
            b[k] = v
    return b

@staticmethod
def fromfile(filename, use_predefined_variables=True, import_custom_modules=True):
    cfg_dict, cfg_text = Config._file2dict(filename, use_predefined_variables)
    if import_custom_modules and cfg_dict.get('custom_imports', None):
        import_modules_from_strings(**cfg_dict['custom_imports'])
    return Config(cfg_dict, cfg_text=cfg_text, filename=filename)

@staticmethod
def fromstring(cfg_str, file_format):
    """Generate config from config str.

        Args:
            cfg_str (str): Config str.
            file_format (str): Config file format corresponding to the
               config str. Only py/yml/yaml/json type are supported now!

        Returns:
            obj:`Config`: Config obj.
        """
    if file_format not in ['.py', '.json', '.yaml', '.yml']:
        raise IOError('Only py/yml/yaml/json type are supported now!')
    if file_format != '.py' and 'dict(' in cfg_str:
        warnings.warn('Please check "file_format", the file format may be .py')
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', suffix=file_format, delete=False) as temp_file:
        temp_file.write(cfg_str)
    cfg = Config.fromfile(temp_file.name)
    os.remove(temp_file.name)
    return cfg

def __init__(self, cfg_dict=None, cfg_text=None, filename=None):
    if cfg_dict is None:
        cfg_dict = dict()
    elif not isinstance(cfg_dict, dict):
        raise TypeError(f'cfg_dict must be a dict, but got {type(cfg_dict)}')
    for key in cfg_dict:
        if key in RESERVED_KEYS:
            raise KeyError(f'{key} is reserved for config file')
    super(Config, self).__setattr__('_cfg_dict', ConfigDict(cfg_dict))
    super(Config, self).__setattr__('_filename', filename)
    if cfg_text:
        text = cfg_text
    elif filename:
        with open(filename, 'r') as f:
            text = f.read()
    else:
        text = ''
    super(Config, self).__setattr__('_text', text)

def _format_basic_types(k, v, use_mapping=False):
    if isinstance(v, str):
        v_str = f"'{v}'"
    else:
        v_str = str(v)
    if use_mapping:
        k_str = f"'{k}'" if isinstance(k, str) else str(k)
        attr_str = f'{k_str}: {v_str}'
    else:
        attr_str = f'{str(k)}={v_str}'
    attr_str = _indent(attr_str, indent)
    return attr_str

def _format_list(k, v, use_mapping=False):
    if all((isinstance(_, dict) for _ in v)):
        v_str = '[\n'
        v_str += '\n'.join((f'dict({_indent(_format_dict(v_), indent)}),' for v_ in v)).rstrip(',')
        if use_mapping:
            k_str = f"'{k}'" if isinstance(k, str) else str(k)
            attr_str = f'{k_str}: {v_str}'
        else:
            attr_str = f'{str(k)}={v_str}'
        attr_str = _indent(attr_str, indent) + ']'
    else:
        attr_str = _format_basic_types(k, v, use_mapping)
    return attr_str

def _contain_invalid_identifier(dict_str):
    contain_invalid_identifier = False
    for key_name in dict_str:
        contain_invalid_identifier |= not str(key_name).isidentifier()
    return contain_invalid_identifier

def _format_dict(input_dict, outest_level=False):
    r = ''
    s = []
    use_mapping = _contain_invalid_identifier(input_dict)
    if use_mapping:
        r += '{'
    for idx, (k, v) in enumerate(input_dict.items()):
        is_last = idx >= len(input_dict) - 1
        end = '' if outest_level or is_last else ','
        if isinstance(v, dict):
            v_str = '\n' + _format_dict(v)
            if use_mapping:
                k_str = f"'{k}'" if isinstance(k, str) else str(k)
                attr_str = f'{k_str}: dict({v_str}'
            else:
                attr_str = f'{str(k)}=dict({v_str}'
            attr_str = _indent(attr_str, indent) + ')' + end
        elif isinstance(v, list):
            attr_str = _format_list(k, v, use_mapping) + end
        else:
            attr_str = _format_basic_types(k, v, use_mapping) + end
        s.append(attr_str)
    r += '\n'.join(s)
    if use_mapping:
        r += '}'
    return r

@property
def pretty_text(self):
    indent = 4

    def _indent(s_, num_spaces):
        s = s_.split('\n')
        if len(s) == 1:
            return s_
        first = s.pop(0)
        s = [num_spaces * ' ' + line for line in s]
        s = '\n'.join(s)
        s = first + '\n' + s
        return s

    def _format_basic_types(k, v, use_mapping=False):
        if isinstance(v, str):
            v_str = f"'{v}'"
        else:
            v_str = str(v)
        if use_mapping:
            k_str = f"'{k}'" if isinstance(k, str) else str(k)
            attr_str = f'{k_str}: {v_str}'
        else:
            attr_str = f'{str(k)}={v_str}'
        attr_str = _indent(attr_str, indent)
        return attr_str

    def _format_list(k, v, use_mapping=False):
        if all((isinstance(_, dict) for _ in v)):
            v_str = '[\n'
            v_str += '\n'.join((f'dict({_indent(_format_dict(v_), indent)}),' for v_ in v)).rstrip(',')
            if use_mapping:
                k_str = f"'{k}'" if isinstance(k, str) else str(k)
                attr_str = f'{k_str}: {v_str}'
            else:
                attr_str = f'{str(k)}={v_str}'
            attr_str = _indent(attr_str, indent) + ']'
        else:
            attr_str = _format_basic_types(k, v, use_mapping)
        return attr_str

    def _contain_invalid_identifier(dict_str):
        contain_invalid_identifier = False
        for key_name in dict_str:
            contain_invalid_identifier |= not str(key_name).isidentifier()
        return contain_invalid_identifier

    def _format_dict(input_dict, outest_level=False):
        r = ''
        s = []
        use_mapping = _contain_invalid_identifier(input_dict)
        if use_mapping:
            r += '{'
        for idx, (k, v) in enumerate(input_dict.items()):
            is_last = idx >= len(input_dict) - 1
            end = '' if outest_level or is_last else ','
            if isinstance(v, dict):
                v_str = '\n' + _format_dict(v)
                if use_mapping:
                    k_str = f"'{k}'" if isinstance(k, str) else str(k)
                    attr_str = f'{k_str}: dict({v_str}'
                else:
                    attr_str = f'{str(k)}=dict({v_str}'
                attr_str = _indent(attr_str, indent) + ')' + end
            elif isinstance(v, list):
                attr_str = _format_list(k, v, use_mapping) + end
            else:
                attr_str = _format_basic_types(k, v, use_mapping) + end
            s.append(attr_str)
        r += '\n'.join(s)
        if use_mapping:
            r += '}'
        return r
    cfg_dict = self._cfg_dict.to_dict()
    text = _format_dict(cfg_dict, outest_level=True)
    yapf_style = dict(based_on_style='pep8', blank_line_before_nested_class_or_def=True, split_before_expression_after_opening_paren=True)
    text, _ = FormatCode(text, style_config=yapf_style, verify=True)
    return text

def __setattr__(self, name, value):
    if isinstance(value, dict):
        value = ConfigDict(value)
    self._cfg_dict.__setattr__(name, value)

def __setitem__(self, name, value):
    if isinstance(value, dict):
        value = ConfigDict(value)
    self._cfg_dict.__setitem__(name, value)

def __setstate__(self, state):
    _cfg_dict, _filename, _text = state
    super(Config, self).__setattr__('_cfg_dict', _cfg_dict)
    super(Config, self).__setattr__('_filename', _filename)
    super(Config, self).__setattr__('_text', _text)

def dump(self, file=None):
    cfg_dict = super(Config, self).__getattribute__('_cfg_dict').to_dict()
    if self.filename.endswith('.py'):
        if file is None:
            return self.pretty_text
        else:
            with open(file, 'w', encoding='utf-8') as f:
                f.write(self.pretty_text)
    else:
        import mmcv
        if file is None:
            file_format = self.filename.split('.')[-1]
            return mmcv.dump(cfg_dict, file_format=file_format)
        else:
            mmcv.dump(cfg_dict, file)

def merge_from_dict(self, options, allow_list_keys=True):
    """Merge list into cfg_dict.

        Merge the dict parsed by MultipleKVAction into this cfg.

        Examples:
            >>> options = {'models.backbone.depth': 50,
            ...            'models.backbone.with_cp':True}
            >>> cfg = Config(dict(models=dict(backbone=dict(type='ResNet'))))
            >>> cfg.merge_from_dict(options)
            >>> cfg_dict = super(Config, self).__getattribute__('_cfg_dict')
            >>> assert cfg_dict == dict(
            ...     models=dict(backbone=dict(depth=50, with_cp=True)))

            # Merge list element
            >>> cfg = Config(dict(pipeline=[
            ...     dict(type='LoadImage'), dict(type='LoadAnnotations')]))
            >>> options = dict(pipeline={'0': dict(type='SelfLoadImage')})
            >>> cfg.merge_from_dict(options, allow_list_keys=True)
            >>> cfg_dict = super(Config, self).__getattribute__('_cfg_dict')
            >>> assert cfg_dict == dict(pipeline=[
            ...     dict(type='SelfLoadImage'), dict(type='LoadAnnotations')])

        Args:
            options (dict): dict of configs to merge from.
            allow_list_keys (bool): If True, int string keys (e.g. '0', '1')
              are allowed in ``options`` and will replace the element of the
              corresponding index in the config if the config is a list.
              Default: True.
        """
    option_cfg_dict = {}
    for full_key, v in options.items():
        d = option_cfg_dict
        key_list = full_key.split('.')
        for subkey in key_list[:-1]:
            d.setdefault(subkey, ConfigDict())
            d = d[subkey]
        subkey = key_list[-1]
        d[subkey] = v
    cfg_dict = super(Config, self).__getattribute__('_cfg_dict')
    super(Config, self).__setattr__('_cfg_dict', Config._merge_a_into_b(option_cfg_dict, cfg_dict, allow_list_keys=allow_list_keys))

class DictAction(Action):
    """
    argparse action to split an argument into KEY=VALUE form
    on the first = and append to a dictionary. List options can
    be passed as comma separated values, i.e 'KEY=V1,V2,V3', or with explicit
    brackets, i.e. 'KEY=[V1,V2,V3]'. It also support nested brackets to build
    list/tuple values. e.g. 'KEY=[(V1,V2),(V3,V4)]'
    """

    @staticmethod
    def _parse_int_float_bool(val):
        try:
            return int(val)
        except ValueError:
            pass
        try:
            return float(val)
        except ValueError:
            pass
        if val.lower() in ['true', 'false']:
            return True if val.lower() == 'true' else False
        return val

    @staticmethod
    def _parse_iterable(val):
        """Parse iterable values in the string.

        All elements inside '()' or '[]' are treated as iterable values.

        Args:
            val (str): Value string.

        Returns:
            list | tuple: The expanded list or tuple from the string.

        Examples:
            >>> DictAction._parse_iterable('1,2,3')
            [1, 2, 3]
            >>> DictAction._parse_iterable('[a, b, c]')
            ['a', 'b', 'c']
            >>> DictAction._parse_iterable('[(1, 2, 3), [a, b], c]')
            [(1, 2, 3), ['a', 'b'], 'c']
        """

        def find_next_comma(string):
            """Find the position of next comma in the string.

            If no ',' is found in the string, return the string length. All
            chars inside '()' and '[]' are treated as one element and thus ','
            inside these brackets are ignored.
            """
            assert string.count('(') == string.count(')') and string.count('[') == string.count(']'), f'Imbalanced brackets exist in {string}'
            end = len(string)
            for idx, char in enumerate(string):
                pre = string[:idx]
                if char == ',' and pre.count('(') == pre.count(')') and (pre.count('[') == pre.count(']')):
                    end = idx
                    break
            return end
        val = val.strip('\'"').replace(' ', '')
        is_tuple = False
        if val.startswith('(') and val.endswith(')'):
            is_tuple = True
            val = val[1:-1]
        elif val.startswith('[') and val.endswith(']'):
            val = val[1:-1]
        elif ',' not in val:
            return DictAction._parse_int_float_bool(val)
        values = []
        while len(val) > 0:
            comma_idx = find_next_comma(val)
            element = DictAction._parse_iterable(val[:comma_idx])
            values.append(element)
            val = val[comma_idx + 1:]
        if is_tuple:
            values = tuple(values)
        return values

    def __call__(self, parser, namespace, values, option_string=None):
        options = {}
        for kv in values:
            key, val = kv.split('=', maxsplit=1)
            options[key] = self._parse_iterable(val)
        setattr(namespace, self.dest, options)

@staticmethod
def _parse_int_float_bool(val):
    try:
        return int(val)
    except ValueError:
        pass
    try:
        return float(val)
    except ValueError:
        pass
    if val.lower() in ['true', 'false']:
        return True if val.lower() == 'true' else False
    return val

@staticmethod
def _parse_iterable(val):
    """Parse iterable values in the string.

        All elements inside '()' or '[]' are treated as iterable values.

        Args:
            val (str): Value string.

        Returns:
            list | tuple: The expanded list or tuple from the string.

        Examples:
            >>> DictAction._parse_iterable('1,2,3')
            [1, 2, 3]
            >>> DictAction._parse_iterable('[a, b, c]')
            ['a', 'b', 'c']
            >>> DictAction._parse_iterable('[(1, 2, 3), [a, b], c]')
            [(1, 2, 3), ['a', 'b'], 'c']
        """

    def find_next_comma(string):
        """Find the position of next comma in the string.

            If no ',' is found in the string, return the string length. All
            chars inside '()' and '[]' are treated as one element and thus ','
            inside these brackets are ignored.
            """
        assert string.count('(') == string.count(')') and string.count('[') == string.count(']'), f'Imbalanced brackets exist in {string}'
        end = len(string)
        for idx, char in enumerate(string):
            pre = string[:idx]
            if char == ',' and pre.count('(') == pre.count(')') and (pre.count('[') == pre.count(']')):
                end = idx
                break
        return end
    val = val.strip('\'"').replace(' ', '')
    is_tuple = False
    if val.startswith('(') and val.endswith(')'):
        is_tuple = True
        val = val[1:-1]
    elif val.startswith('[') and val.endswith(']'):
        val = val[1:-1]
    elif ',' not in val:
        return DictAction._parse_int_float_bool(val)
    values = []
    while len(val) > 0:
        comma_idx = find_next_comma(val)
        element = DictAction._parse_iterable(val[:comma_idx])
        values.append(element)
        val = val[comma_idx + 1:]
    if is_tuple:
        values = tuple(values)
    return values

def build_from_cfg(cfg, registry, default_args=None):
    """Build a module from configs dict.

    Args:
        cfg (dict): Config dict. It should at least contain the key "type".
        registry (:obj:`Registry`): The registry to search the type from.
        default_args (dict, optional): Default initialization arguments.

    Returns:
        object: The constructed object.
    """
    if not isinstance(cfg, dict):
        raise TypeError(f'cfg must be a dict, but got {type(cfg)}')
    if 'type' not in cfg:
        if default_args is None or 'type' not in default_args:
            raise KeyError(f'`cfg` or `default_args` must contain the key "type", but got {cfg}\n{default_args}')
    if not isinstance(registry, Registry):
        raise TypeError(f'registry must be an mmcv.Registry object, but got {type(registry)}')
    if not (isinstance(default_args, dict) or default_args is None):
        raise TypeError(f'default_args must be a dict or None, but got {type(default_args)}')
    args = cfg.copy()
    if default_args is not None:
        for name, value in default_args.items():
            args.setdefault(name, value)
    obj_type = args.pop('type')
    if isinstance(obj_type, str):
        obj_cls = registry.get(obj_type)
        if obj_cls is None:
            raise KeyError(f'{obj_type} is not in the {registry.name} registry')
    elif inspect.isclass(obj_type):
        obj_cls = obj_type
    else:
        raise TypeError(f'type must be a str or valid type, but got {type(obj_type)}')
    try:
        return obj_cls(**args)
    except Exception as e:
        raise type(e)(f'{obj_cls.__name__}: {e}')

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

def __contains__(self, key):
    return self.get(key) is not None

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

def _register(cls):
    self._register_module(module_class=cls, module_name=name, force=force)
    return cls

def make_dirs(dir_name):
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

def is_seq_of(seq, expected_type, seq_type=None):
    """Check whether it is a sequence of some type.

    Args:
        seq (Sequence): The sequence to be checked.
        expected_type (type): Expected type of sequence items.
        seq_type (type, optional): Expected sequence type.

    Returns:
        bool: Whether the sequence is valid.
    """
    if seq_type is None:
        exp_seq_type = abc.Sequence
    else:
        assert isinstance(seq_type, type)
        exp_seq_type = seq_type
    if not isinstance(seq, exp_seq_type):
        return False
    for item in seq:
        if not isinstance(item, expected_type):
            return False
    return True

def is_str(x):
    """Whether the input is an string instance.

    Note: This method is deprecated since python 2 is no longer supported.
    """
    return isinstance(x, str)

def import_modules_from_strings(imports, allow_failed_imports=False):
    """Import modules from the given list of strings.

    Args:
        imports (list | str | None): The given module names to be imported.
        allow_failed_imports (bool): If True, the failed imports will return
            None. Otherwise, an ImportError is raise. Default: False.

    Returns:
        list[module] | module | None: The imported modules.

    Examples:
        >>> osp, sys = import_modules_from_strings(
        ...     ['os.path', 'sys'])
        >>> import os.path as osp_
        >>> import sys as sys_
        >>> assert osp == osp_
        >>> assert sys == sys_
    """
    if not imports:
        return
    single_import = False
    if isinstance(imports, str):
        single_import = True
        imports = [imports]
    if not isinstance(imports, list):
        raise TypeError(f'custom_imports must be a list but got type {type(imports)}')
    imported = []
    for imp in imports:
        if not isinstance(imp, str):
            raise TypeError(f'{imp} is of type {type(imp)} and cannot be imported.')
        try:
            imported_tmp = import_module(imp)
        except ImportError:
            if allow_failed_imports:
                warnings.warn(f'{imp} failed to import and is ignored.', UserWarning)
                imported_tmp = None
            else:
                raise ImportError
        imported.append(imported_tmp)
    if single_import:
        imported = imported[0]
    return imported

def print_log(msg, logger=None, level=logging.INFO):
    """Print a log message.

    Args:
        msg (str): The message to be logged.
        logger (logging.Logger | str | None): The logger to be used.
            Some special loggers are:
            - "silent": no message will be printed.
            - other str: the logger obtained with `get_root_logger(logger)`.
            - None: The `print()` method will be used to print log messages.
        level (int): Logging level. Only available when `logger` is a Logger
            object or "root".
    """
    if logger is None:
        print(msg)
    elif isinstance(logger, logging.Logger):
        logger.log(level, msg)
    elif logger == 'silent':
        pass
    elif isinstance(logger, str):
        _logger = get_logger(logger)
        _logger.log(level, msg)
    else:
        raise TypeError(f'logger should be either a logging.Logger object, str, "silent" or None, but got {type(logger)}')

def get_root_logger(log_file=None, log_level=logging.INFO, file_mode='a'):
    """Get the root logger.

    The logger will be initialized if it has not been initialized. By default a
    StreamHandler will be added. If `log_file` is specified, a FileHandler will
    also be added. The name of the root logger is the top-level package name,
    e.g., "lseg3d".

    Args:
        log_file (str | None): The log filename. If specified, a FileHandler
            will be added to the root logger.
        log_level (int): The root logger level. Note that only the process of
            rank 0 is affected, while other processes will set the level to
            "Error" and be silent most of the time.
        file_mode (str): File Mode of logger. (w or a)

    Returns:
        logging.Logger: The root logger.
    """
    logger = get_logger(name='pcr', log_file=log_file, log_level=log_level, file_mode=file_mode)
    return logger

class TrainerBase:
    """
    Base class for iterative trainer with hooks.
    The only assumption we made here is: the training runs in a loop.
    A subclass can implement what the loop is.
    We made no assumptions about the existence of dataloader, optimizer, model, etc.
    Attributes:
        iter(int): the current iteration.
        start_iter(int): The iteration to start with.
            By convention the minimum possible value is 0.
        max_iter(int): The iteration to end training.
        storage(EventStorage): An EventStorage that's opened during the course of training.
    """

    def __init__(self) -> None:
        self._hooks: List[HookBase] = []
        self.iter: int = 0
        self.start_iter: int = 0
        self.max_iter: int
        self.storage: EventStorage
        _log_api_usage('trainer.' + self.__class__.__name__)

    def register_hooks(self, hooks: List[Optional[HookBase]]) -> None:
        """
        Register hooks to the trainer. The hooks are executed in the order
        they are registered.
        Args:
            hooks (list[Optional[HookBase]]): list of hooks
        """
        hooks = [h for h in hooks if h is not None]
        for h in hooks:
            assert isinstance(h, HookBase)
            h.trainer = weakref.proxy(self)
        self._hooks.extend(hooks)

    def train(self, start_iter: int, max_iter: int):
        """
        Args:
            start_iter, max_iter (int): See docs above
        """
        logger = logging.getLogger(__name__)
        logger.info('Starting training from iteration {}'.format(start_iter))
        self.iter = self.start_iter = start_iter
        self.max_iter = max_iter
        with EventStorage(start_iter) as self.storage:
            try:
                self.before_train()
                for self.iter in range(start_iter, max_iter):
                    self.before_step()
                    self.run_step()
                    self.after_step()
                self.iter += 1
            except Exception:
                logger.exception('Exception during training:')
                raise
            finally:
                self.after_train()

    def before_train(self):
        for h in self._hooks:
            h.before_train()

    def after_train(self):
        self.storage.iter = self.iter
        for h in self._hooks:
            h.after_train()

    def before_step(self):
        self.storage.iter = self.iter
        for h in self._hooks:
            h.before_step()

    def after_step(self):
        for h in self._hooks:
            h.after_step()

    def run_step(self):
        raise NotImplementedError

    def state_dict(self):
        ret = {'iteration': self.iter}
        hooks_state = {}
        for h in self._hooks:
            sd = h.state_dict()
            if sd:
                name = type(h).__qualname__
                if name in hooks_state:
                    continue
                hooks_state[name] = sd
        if hooks_state:
            ret['hooks'] = hooks_state
        return ret

    def load_state_dict(self, state_dict):
        logger = logging.getLogger(__name__)
        self.iter = state_dict['iteration']
        for key, value in state_dict.get('hooks', {}).items():
            for h in self._hooks:
                try:
                    name = type(h).__qualname__
                except AttributeError:
                    continue
                if name == key:
                    h.load_state_dict(value)
                    break
            else:
                logger.warning(f"Cannot find the hook '{key}', its state_dict is ignored.")

def state_dict(self):
    ret = {'iteration': self.iter}
    hooks_state = {}
    for h in self._hooks:
        sd = h.state_dict()
        if sd:
            name = type(h).__qualname__
            if name in hooks_state:
                continue
            hooks_state[name] = sd
    if hooks_state:
        ret['hooks'] = hooks_state
    return ret

def load_state_dict(self, state_dict):
    logger = logging.getLogger(__name__)
    self.iter = state_dict['iteration']
    for key, value in state_dict.get('hooks', {}).items():
        for h in self._hooks:
            try:
                name = type(h).__qualname__
            except AttributeError:
                continue
            if name == key:
                h.load_state_dict(value)
                break
        else:
            logger.warning(f"Cannot find the hook '{key}', its state_dict is ignored.")

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

def state_dict(self):
    ret = super().state_dict()
    ret['optimizer'] = self.optimizer.state_dict()
    return ret

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

def state_dict(self):
    ret = super().state_dict()
    ret['grad_scaler'] = self.grad_scaler.state_dict()
    return ret

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

def build_writer(self):
    writer = SummaryWriter(self.cfg.save_path) if comm.is_main_process() else None
    return writer

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

def get_data_list(self):
    data_list = []
    overlap_list = glob.glob(os.path.join(self.data_root, '*', 'pcd', 'overlap.txt'))
    for overlap_file in overlap_list:
        with open(overlap_file) as f:
            overlap = f.readlines()
        overlap = [pair.strip().split() for pair in overlap]
        data_list.extend([pair[:2] for pair in overlap if float(pair[2]) > self.overlap_threshold])
    return data_list

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

@TRANSFORMS.register_module()
class ToTensor(object):

    def __call__(self, data):
        if isinstance(data, Mapping):
            result = {sub_key: self(item) for sub_key, item in data.items()}
            return result
        elif isinstance(data, Sequence):
            result = [self(item) for item in data]
            return result
        elif isinstance(data, torch.Tensor):
            return data
        elif isinstance(data, str):
            return data
        elif isinstance(data, int):
            return torch.LongTensor([data])
        elif isinstance(data, float):
            return torch.FloatTensor([data])
        elif isinstance(data, np.ndarray) and np.issubdtype(data.dtype, np.int):
            return torch.from_numpy(data).long()
        elif isinstance(data, np.ndarray) and np.issubdtype(data.dtype, np.floating):
            return torch.from_numpy(data).float()
        else:
            raise TypeError(f'type {type(data)} cannot be converted to tensor.')

def __call__(self, data):
    if isinstance(data, Mapping):
        result = {sub_key: self(item) for sub_key, item in data.items()}
        return result
    elif isinstance(data, Sequence):
        result = [self(item) for item in data]
        return result
    elif isinstance(data, torch.Tensor):
        return data
    elif isinstance(data, str):
        return data
    elif isinstance(data, int):
        return torch.LongTensor([data])
    elif isinstance(data, float):
        return torch.FloatTensor([data])
    elif isinstance(data, np.ndarray) and np.issubdtype(data.dtype, np.int):
        return torch.from_numpy(data).long()
    elif isinstance(data, np.ndarray) and np.issubdtype(data.dtype, np.floating):
        return torch.from_numpy(data).float()
    else:
        raise TypeError(f'type {type(data)} cannot be converted to tensor.')

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

def __repr__(self):
    return 'RandomColorDrop(color_augment: {}, p: {})'.format(self.color_augment, self.p)

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

@DATASETS.register_module()
class ShapeNetPartDataset(Dataset):

    def __init__(self, split='train', data_root='data/shapenetcore_partanno_segmentation_benchmark_v0_normal', transform=None, test_mode=False, test_cfg=None, loop=1):
        super(ShapeNetPartDataset, self).__init__()
        self.data_root = data_root
        self.split = split
        self.transform = Compose(transform)
        self.loop = loop if not test_mode else 1
        self.test_mode = test_mode
        self.test_cfg = test_cfg if test_mode else None
        self.cache = {}
        self.categories = []
        self.category2part = {'Airplane': [0, 1, 2, 3], 'Bag': [4, 5], 'Cap': [6, 7], 'Car': [8, 9, 10, 11], 'Chair': [12, 13, 14, 15], 'Earphone': [16, 17, 18], 'Guitar': [19, 20, 21], 'Knife': [22, 23], 'Lamp': [24, 25, 26, 27], 'Laptop': [28, 29], 'Motorbike': [30, 31, 32, 33, 34, 35], 'Mug': [36, 37], 'Pistol': [38, 39, 40], 'Rocket': [41, 42, 43], 'Skateboard': [44, 45, 46], 'Table': [47, 48, 49]}
        self.token2category = {}
        with open(os.path.join(self.data_root, 'synsetoffset2category.txt'), 'r') as f:
            for line in f:
                ls = line.strip().split()
                self.token2category[ls[1]] = len(self.categories)
                self.categories.append(ls[0])
        if test_mode:
            self.post_transform = Compose(self.test_cfg.post_transform)
            self.aug_transform = [Compose(aug) for aug in self.test_cfg.aug_transform]
        if isinstance(self.split, str):
            self.data_list = self.load_data_list(self.split)
        elif isinstance(self.split, list):
            self.data_list = []
            for s in self.split:
                self.data_list += self.load_data_list(s)
        else:
            raise NotImplementedError
        logger = get_root_logger()
        logger.info('Totally {} x {} samples in {} set.'.format(len(self.data_idx), self.loop, split))

    def load_data_list(self, split):
        split_file = os.path.join(self.data_root, 'train_test_split', 'shuffled_{}_file_list.json'.format(split))
        if not os.path.isfile(split_file):
            raise RuntimeError('Split file do not exist: ' + split_file + '\n')
        with open(split_file, 'r') as f:
            data_list = [os.path.join(self.data_root, data[11:] + '.txt') for data in json.load(f)]
        return data_list

    def prepare_train_data(self, idx):
        data_idx = idx % len(self.data_list)
        if data_idx in self.cache:
            coord, norm, label, cls_token = self.cache[data_idx]
        else:
            data = np.loadtxt(self.data_list[data_idx]).astype(np.float32)
            cls_token = self.token2category[os.path.basename(os.path.dirname(self.data_list[data_idx]))]
            coord, norm, label = (data[:, :3], data[:, 3:6], data[:, 6].astype(np.int32))
            self.cache[data_idx] = (coord, norm, label, cls_token)
        data_dict = dict(coord=coord, norm=norm, label=label, cls_token=cls_token)
        data_dict = self.transform(data_dict)
        return data_dict

    def prepare_test_data(self, idx):
        data_idx = self.data_idx[idx % len(self.data_idx)]
        data = np.loadtxt(self.data_list[data_idx]).astype(np.float32)
        cls_token = self.token2category[os.path.basename(os.path.dirname(self.data_list[data_idx]))]
        coord, norm, label = (data[:, :3], data[:, 3:6], data[:, 6].astype(np.int32))
        data_dict = dict(coord=coord, norm=norm, cls_token=cls_token)
        data_dict = self.transform(data_dict)
        data_dict_list = []
        for aug in self.aug_transform:
            data_dict_list.append(self.post_transform(aug(deepcopy(data_dict))))
        return (data_dict_list, label)

    def get_data_name(self, idx):
        data_idx = self.data_idx[idx % len(self.data_idx)]
        return os.path.basename(self.data_list[data_idx]).split('.')[0]

    def __getitem__(self, idx):
        if self.test_mode:
            return self.prepare_test_data(idx)
        else:
            return self.prepare_train_data(idx)

    def __len__(self):
        return len(self.data_idx) * self.loop

def __init__(self, split='train', data_root='data/shapenetcore_partanno_segmentation_benchmark_v0_normal', transform=None, test_mode=False, test_cfg=None, loop=1):
    super(ShapeNetPartDataset, self).__init__()
    self.data_root = data_root
    self.split = split
    self.transform = Compose(transform)
    self.loop = loop if not test_mode else 1
    self.test_mode = test_mode
    self.test_cfg = test_cfg if test_mode else None
    self.cache = {}
    self.categories = []
    self.category2part = {'Airplane': [0, 1, 2, 3], 'Bag': [4, 5], 'Cap': [6, 7], 'Car': [8, 9, 10, 11], 'Chair': [12, 13, 14, 15], 'Earphone': [16, 17, 18], 'Guitar': [19, 20, 21], 'Knife': [22, 23], 'Lamp': [24, 25, 26, 27], 'Laptop': [28, 29], 'Motorbike': [30, 31, 32, 33, 34, 35], 'Mug': [36, 37], 'Pistol': [38, 39, 40], 'Rocket': [41, 42, 43], 'Skateboard': [44, 45, 46], 'Table': [47, 48, 49]}
    self.token2category = {}
    with open(os.path.join(self.data_root, 'synsetoffset2category.txt'), 'r') as f:
        for line in f:
            ls = line.strip().split()
            self.token2category[ls[1]] = len(self.categories)
            self.categories.append(ls[0])
    if test_mode:
        self.post_transform = Compose(self.test_cfg.post_transform)
        self.aug_transform = [Compose(aug) for aug in self.test_cfg.aug_transform]
    if isinstance(self.split, str):
        self.data_list = self.load_data_list(self.split)
    elif isinstance(self.split, list):
        self.data_list = []
        for s in self.split:
            self.data_list += self.load_data_list(s)
    else:
        raise NotImplementedError
    logger = get_root_logger()
    logger.info('Totally {} x {} samples in {} set.'.format(len(self.data_idx), self.loop, split))

def load_data_list(self, split):
    split_file = os.path.join(self.data_root, 'train_test_split', 'shuffled_{}_file_list.json'.format(split))
    if not os.path.isfile(split_file):
        raise RuntimeError('Split file do not exist: ' + split_file + '\n')
    with open(split_file, 'r') as f:
        data_list = [os.path.join(self.data_root, data[11:] + '.txt') for data in json.load(f)]
    return data_list

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

def parse_room(room, source_root, save_root, parse_normals=False):
    if isinstance(room, list):
        room, angle = room
    else:
        angle = None
    print('Parsing: {}'.format(room))
    classes = ['ceiling', 'floor', 'wall', 'beam', 'column', 'window', 'door', 'table', 'chair', 'sofa', 'bookcase', 'board', 'clutter']
    class2label = {cls: i for i, cls in enumerate(classes)}
    source_dir = os.path.join(source_root, room)
    save_path = os.path.join(save_root, room) + '.pth'
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    object_path_list = sorted(glob.glob(os.path.join(source_dir, 'Annotations/*.txt')))
    room_coords = []
    room_normals = []
    room_colors = []
    room_semantic_gt = []
    room_instance_gt = []
    for object_id, object_path in enumerate(object_path_list):
        object_name = os.path.basename(object_path).split('_')[0]
        obj = np.loadtxt(object_path)
        coords = obj[:, :3]
        colors = obj[:, 3:6]
        class_name = object_name if object_name in classes else 'clutter'
        semantic_gt = np.repeat(class2label[class_name], coords.shape[0])
        semantic_gt = semantic_gt.reshape([-1, 1])
        instance_gt = np.repeat(object_id, coords.shape[0])
        instance_gt = instance_gt.reshape([-1, 1])
        room_coords.append(coords)
        room_colors.append(colors)
        room_semantic_gt.append(semantic_gt)
        room_instance_gt.append(instance_gt)
        if parse_normals:
            object_norm_dir = os.path.join(source_dir, 'normals', object_name)
            normals = np.loadtxt(object_norm_dir)
            assert normals.shape[0] == coords.shape[0]
            room_normals.append(normals)
    room_coords = np.ascontiguousarray(np.vstack(room_coords))
    room_coords -= room_coords.mean(0)
    rot_t = None
    if angle is not None:
        angle = (2 - angle / 360) * np.pi
        rot_cos, rot_sin = (np.cos(angle), np.sin(angle))
        rot_t = np.array([[rot_cos, -rot_sin, 0], [rot_sin, rot_cos, 0], [0, 0, 1]])
        room_coords = room_coords @ np.transpose(rot_t)
    room_colors = np.ascontiguousarray(np.vstack(room_colors))
    room_semantic_gt = np.ascontiguousarray(np.vstack(room_semantic_gt))
    room_instance_gt = np.ascontiguousarray(np.vstack(room_instance_gt))
    save_dict = dict(coord=room_coords, color=room_colors, semantic_gt=room_semantic_gt, instance_gt=room_instance_gt)
    if parse_normals:
        room_normals = np.ascontiguousarray(np.vstack(room_normals))
        if rot_t is not None:
            room_normals = room_normals @ np.transpose(rot_t)
        save_dict['normal'] = room_normals
    torch.save(save_dict, save_path)

def parse_scene(scene_path, output_dir):
    print(f'Parsing scene {scene_path}')
    split = os.path.basename(os.path.dirname(os.path.dirname(scene_path)))
    scene_id = os.path.basename(os.path.dirname(scene_path))
    vertices, faces = read_plymesh(scene_path)
    coords = vertices[:, :3]
    colors = vertices[:, 3:6]
    data_dict = dict(coord=coords, color=colors, scene_id=scene_id)
    data_dict['normal'] = vertex_normal(coords, faces)
    torch.save(data_dict, os.path.join(output_dir, split, f'{scene_id}.pth'))

def handle_process(scene_path, output_path, labels_pd, train_scenes, val_scenes, parse_normals=True):
    scene_id = os.path.basename(scene_path)
    mesh_path = os.path.join(scene_path, f'{scene_id}{CLOUD_FILE_PFIX}.ply')
    segments_file = os.path.join(scene_path, f'{scene_id}{CLOUD_FILE_PFIX}{SEGMENTS_FILE_PFIX}')
    aggregations_file = os.path.join(scene_path, f'{scene_id}{AGGREGATIONS_FILE_PFIX}')
    info_file = os.path.join(scene_path, f'{scene_id}.txt')
    if scene_id in train_scenes:
        output_file = os.path.join(output_path, 'train', f'{scene_id}.pth')
        split_name = 'train'
    elif scene_id in val_scenes:
        output_file = os.path.join(output_path, 'val', f'{scene_id}.pth')
        split_name = 'val'
    else:
        output_file = os.path.join(output_path, 'test', f'{scene_id}.pth')
        split_name = 'test'
    print(f'Processing: {scene_id} in {split_name}')
    vertices, faces = read_plymesh(mesh_path)
    coords = vertices[:, :3]
    colors = vertices[:, 3:6]
    save_dict = dict(coord=coords, color=colors, scene_id=scene_id)
    if parse_normals:
        save_dict['normal'] = vertex_normal(coords, faces)
    if split_name != 'test':
        with open(segments_file) as f:
            segments = json.load(f)
            seg_indices = np.array(segments['segIndices'])
        with open(aggregations_file) as f:
            aggregation = json.load(f)
            seg_groups = np.array(aggregation['segGroups'])
        semantic_gt20 = np.ones((vertices.shape[0], 1)) * IGNORE_INDEX
        semantic_gt200 = np.ones((vertices.shape[0], 1)) * IGNORE_INDEX
        instance_ids = np.ones((vertices.shape[0], 1)) * IGNORE_INDEX
        for group in seg_groups:
            point_idx, label_id20, label_id200 = point_indices_from_group(seg_indices, group, labels_pd)
            semantic_gt20[point_idx] = label_id20
            semantic_gt200[point_idx] = label_id200
            instance_ids[point_idx] = group['id']
        semantic_gt20 = semantic_gt20.astype(int)
        semantic_gt200 = semantic_gt200.astype(int)
        instance_ids = instance_ids.astype(int)
        save_dict['semantic_gt20'] = semantic_gt20
        save_dict['semantic_gt200'] = semantic_gt200
        save_dict['instance_gt'] = instance_ids
        processed_vertices = np.hstack((semantic_gt200, instance_ids))
        if np.any(np.isnan(processed_vertices)) or not np.all(np.isfinite(processed_vertices)):
            raise ValueError(f'Find NaN in Scene: {scene_id}')
    torch.save(save_dict, output_file)

def reader(filename, output_path, frame_skip, export_color_images=False, export_depth_images=False, export_poses=False, export_intrinsics=False):
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    print('loading %s...' % filename)
    sd = SensorData(filename)
    if export_depth_images:
        sd.export_depth_images(os.path.join(output_path, 'depth'), frame_skip=frame_skip)
    if export_color_images:
        sd.export_color_images(os.path.join(output_path, 'color'), frame_skip=frame_skip)
    if export_poses:
        sd.export_poses(os.path.join(output_path, 'pose'), frame_skip=frame_skip)
    if export_intrinsics:
        sd.export_intrinsics(os.path.join(output_path, 'intrinsic'))

class PlyData(object):
    """
    PLY file header and data.

    A PlyData instance is created in one of two ways: by the static
    method PlyData.read (to read a PLY file), or directly from __init__
    given a sequence of elements (which can then be written to a PLY
    file).

    """

    def __init__(self, elements=[], text=False, byte_order='=', comments=[], obj_info=[]):
        """
        elements: sequence of PlyElement instances.

        text: whether the resulting PLY file will be text (True) or
            binary (False).

        byte_order: '<' for little-endian, '>' for big-endian, or '='
            for native.  This is only relevant if `text' is False.

        comments: sequence of strings that will be placed in the header
            between the 'ply' and 'format ...' lines.

        obj_info: like comments, but will be placed in the header with
            "obj_info ..." instead of "comment ...".

        """
        if byte_order == '=' and (not text):
            byte_order = _native_byte_order
        self.byte_order = byte_order
        self.text = text
        self.comments = list(comments)
        self.obj_info = list(obj_info)
        self.elements = elements

    def _get_elements(self):
        return self._elements

    def _set_elements(self, elements):
        self._elements = tuple(elements)
        self._index()
    elements = property(_get_elements, _set_elements)

    def _get_byte_order(self):
        return self._byte_order

    def _set_byte_order(self, byte_order):
        if byte_order not in ['<', '>', '=']:
            raise ValueError("byte order must be '<', '>', or '='")
        self._byte_order = byte_order
    byte_order = property(_get_byte_order, _set_byte_order)

    def _index(self):
        self._element_lookup = dict(((elt.name, elt) for elt in self._elements))
        if len(self._element_lookup) != len(self._elements):
            raise ValueError('two elements with same name')

    @staticmethod
    def _parse_header(stream):
        """
        Parse a PLY header from a readable file-like stream.

        """
        lines = []
        comments = {'comment': [], 'obj_info': []}
        while True:
            line = stream.readline().decode('ascii').strip()
            fields = _split_line(line, 1)
            if fields[0] == 'end_header':
                break
            elif fields[0] in comments.keys():
                lines.append(fields)
            else:
                lines.append(line.split())
        a = 0
        if lines[a] != ['ply']:
            raise PlyParseError("expected 'ply'")
        a += 1
        while lines[a][0] in comments.keys():
            comments[lines[a][0]].append(lines[a][1])
            a += 1
        if lines[a][0] != 'format':
            raise PlyParseError("expected 'format'")
        if lines[a][2] != '1.0':
            raise PlyParseError("expected version '1.0'")
        if len(lines[a]) != 3:
            raise PlyParseError("too many fields after 'format'")
        fmt = lines[a][1]
        if fmt not in _byte_order_map:
            raise PlyParseError("don't understand format %r" % fmt)
        byte_order = _byte_order_map[fmt]
        text = fmt == 'ascii'
        a += 1
        while a < len(lines) and lines[a][0] in comments.keys():
            comments[lines[a][0]].append(lines[a][1])
            a += 1
        return PlyData(PlyElement._parse_multi(lines[a:]), text, byte_order, comments['comment'], comments['obj_info'])

    @staticmethod
    def read(stream):
        """
        Read PLY data from a readable file-like object or filename.

        """
        must_close, stream = _open_stream(stream, 'read')
        try:
            data = PlyData._parse_header(stream)
            for elt in data:
                elt._read(stream, data.text, data.byte_order)
        finally:
            if must_close:
                stream.close()
        return data

    def write(self, stream):
        """
        Write PLY data to a writeable file-like object or filename.

        """
        must_close, stream = _open_stream(stream, 'write')
        try:
            stream.write(self.header.encode('ascii'))
            stream.write(b'\r\n')
            for elt in self:
                elt._write(stream, self.text, self.byte_order)
        finally:
            if must_close:
                stream.close()

    @property
    def header(self):
        """
        Provide PLY-formatted metadata for the instance.

        """
        lines = ['ply']
        if self.text:
            lines.append('format ascii 1.0')
        else:
            lines.append('format ' + _byte_order_reverse[self.byte_order] + ' 1.0')
        for c in self.comments:
            lines.append('comment ' + c)
        for c in self.obj_info:
            lines.append('obj_info ' + c)
        lines.extend((elt.header for elt in self.elements))
        lines.append('end_header')
        return '\r\n'.join(lines)

    def __iter__(self):
        return iter(self.elements)

    def __len__(self):
        return len(self.elements)

    def __contains__(self, name):
        return name in self._element_lookup

    def __getitem__(self, name):
        return self._element_lookup[name]

    def __str__(self):
        return self.header

    def __repr__(self):
        return 'PlyData(%r, text=%r, byte_order=%r, comments=%r, obj_info=%r)' % (self.elements, self.text, self.byte_order, self.comments, self.obj_info)

def _set_elements(self, elements):
    self._elements = tuple(elements)
    self._index()

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

def __init__(self, name, val_dtype):
    self._name = str(name)
    self._check_name()
    self.val_dtype = val_dtype

def compute_full_overlapping(data_root, scene_id, voxel_size=0.05):
    _points = [(pcd_name, make_open3d_point_cloud(torch.load(pcd_name)['coord'], voxel_size=voxel_size)) for pcd_name in glob.glob(os.path.join(data_root, scene_id, 'pcd', '*.pth'))]
    points = [(pcd_name, pcd) for pcd_name, pcd in _points if pcd is not None]
    print('load {} point clouds ({} invalid has been filtered), computing matching/overlapping'.format(len(points), len(_points) - len(points)))
    matching_matrix = np.zeros((len(points), len(points)))
    for i, (pcd0_name, pcd0) in enumerate(points):
        print('matching to...{}'.format(pcd0_name))
        pcd0_tree = o3d.geometry.KDTreeFlann(copy.deepcopy(pcd0))
        for j, (pcd1_name, pcd1) in enumerate(points):
            if i == j:
                continue
            matching_matrix[i, j] = float(len(get_matching_indices(pcd1, pcd0_tree, 1.5 * voxel_size, 1))) / float(len(pcd1.points))
    with open(os.path.join(data_root, scene_id, 'pcd', 'overlap.txt'), 'w') as f:
        for i, (pcd0_name, pcd0) in enumerate(points):
            for j, (pcd1_name, pcd1) in enumerate(points):
                if i < j:
                    overlap = max(matching_matrix[i, j], matching_matrix[j, i])
                    f.write('{} {} {}\n'.format(pcd0_name.replace(data_root, ''), pcd1_name.replace(data_root, ''), overlap))

class RGBDFrame:

    def load(self, file_handle):
        self.camera_to_world = np.asarray(struct.unpack('f' * 16, file_handle.read(16 * 4)), dtype=np.float32).reshape(4, 4)
        self.timestamp_color = struct.unpack('Q', file_handle.read(8))[0]
        self.timestamp_depth = struct.unpack('Q', file_handle.read(8))[0]
        self.color_size_bytes = struct.unpack('Q', file_handle.read(8))[0]
        self.depth_size_bytes = struct.unpack('Q', file_handle.read(8))[0]
        self.color_data = b''.join(struct.unpack('c' * self.color_size_bytes, file_handle.read(self.color_size_bytes)))
        self.depth_data = b''.join(struct.unpack('c' * self.depth_size_bytes, file_handle.read(self.depth_size_bytes)))

    def decompress_depth(self, compression_type):
        if compression_type == 'zlib_ushort':
            return self.decompress_depth_zlib()
        else:
            raise

    def decompress_depth_zlib(self):
        return zlib.decompress(self.depth_data)

    def decompress_color(self, compression_type):
        if compression_type == 'jpeg':
            return self.decompress_color_jpeg()
        else:
            raise

    def decompress_color_jpeg(self):
        return imageio.imread(self.color_data)

def load(self, file_handle):
    self.camera_to_world = np.asarray(struct.unpack('f' * 16, file_handle.read(16 * 4)), dtype=np.float32).reshape(4, 4)
    self.timestamp_color = struct.unpack('Q', file_handle.read(8))[0]
    self.timestamp_depth = struct.unpack('Q', file_handle.read(8))[0]
    self.color_size_bytes = struct.unpack('Q', file_handle.read(8))[0]
    self.depth_size_bytes = struct.unpack('Q', file_handle.read(8))[0]
    self.color_data = b''.join(struct.unpack('c' * self.color_size_bytes, file_handle.read(self.color_size_bytes)))
    self.depth_data = b''.join(struct.unpack('c' * self.depth_size_bytes, file_handle.read(self.depth_size_bytes)))

def decompress_color_jpeg(self):
    return imageio.imread(self.color_data)

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

def extractor(input_path, output_path):
    if not os.path.exists(output_path):
        os.mkdir(output_path)
    depth_intrinsic = np.loadtxt(input_path + '/intrinsic/intrinsic_depth.txt')
    print('Depth intrinsic: ')
    print(depth_intrinsic)
    poses = sorted(glob.glob(input_path + '/pose/*.txt'), key=lambda a: int(os.path.basename(a).split('.')[0]))
    depths = sorted(glob.glob(input_path + '/depth/*.png'), key=lambda a: int(os.path.basename(a).split('.')[0]))
    colors = sorted(glob.glob(input_path + '/color/*.png'), key=lambda a: int(os.path.basename(a).split('.')[0]))
    for ind, (pose, depth, color) in enumerate(zip(poses, depths, colors)):
        name = os.path.basename(pose).split('.')[0]
        if os.path.exists(output_path + '/{}.npz'.format(name)):
            continue
        try:
            print('=' * 50, ': {}'.format(pose))
            depth_img = cv2.imread(depth, -1)
            mask = depth_img != 0
            color_image = cv2.imread(color)
            color_image = cv2.resize(color_image, (640, 480))
            color_image = np.reshape(color_image[mask], [-1, 3])
            colors = np.zeros_like(color_image)
            colors[:, 0] = color_image[:, 2]
            colors[:, 1] = color_image[:, 1]
            colors[:, 2] = color_image[:, 0]
            pose = np.loadtxt(poses[ind])
            print('Camera pose: ')
            print(pose)
            depth_shift = 1000.0
            x, y = np.meshgrid(np.linspace(0, depth_img.shape[1] - 1, depth_img.shape[1]), np.linspace(0, depth_img.shape[0] - 1, depth_img.shape[0]))
            uv_depth = np.zeros((depth_img.shape[0], depth_img.shape[1], 3))
            uv_depth[:, :, 0] = x
            uv_depth[:, :, 1] = y
            uv_depth[:, :, 2] = depth_img / depth_shift
            uv_depth = np.reshape(uv_depth, [-1, 3])
            uv_depth = uv_depth[np.where(uv_depth[:, 2] != 0), :].squeeze()
            intrinsic_inv = np.linalg.inv(depth_intrinsic)
            fx = depth_intrinsic[0, 0]
            fy = depth_intrinsic[1, 1]
            cx = depth_intrinsic[0, 2]
            cy = depth_intrinsic[1, 2]
            bx = depth_intrinsic[0, 3]
            by = depth_intrinsic[1, 3]
            point_list = []
            n = uv_depth.shape[0]
            points = np.ones((n, 4))
            X = (uv_depth[:, 0] - cx) * uv_depth[:, 2] / fx + bx
            Y = (uv_depth[:, 1] - cy) * uv_depth[:, 2] / fy + by
            points[:, 0] = X
            points[:, 1] = Y
            points[:, 2] = uv_depth[:, 2]
            points_world = np.dot(points, np.transpose(pose))
            print(points_world.shape)
            pcd = dict(coord=points_world[:, :3], color=colors)
            torch.save(pcd, output_path + '/{}.pth'.format(name))
        except:
            continue

def main():
    overlaps = glob.glob(os.path.join(opt.target_dir, '*/pcd/overlap.txt'))
    with open(os.path.join(opt.target_dir, 'overlap30.txt'), 'w') as f:
        for fo in overlaps:
            for line in open(fo):
                pcd0, pcd1, op = line.strip().split()
                if float(op) >= 0.3:
                    print('{} {} {}'.format(pcd0, pcd1, op), file=f)
    print('done')

def parse_sens(sens_dir, output_dir):
    scene_id = os.path.basename(os.path.dirname(sens_dir))
    print(f'Parsing sens data{sens_dir}')
    reader(sens_dir, os.path.join(output_dir, scene_id), frame_skip, export_color_images=True, export_depth_images=True, export_poses=True, export_intrinsics=True)
    extractor(os.path.join(output_dir, scene_id), os.path.join(output_dir, scene_id, 'pcd'))
    compute_full_overlapping(output_dir, scene_id)

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

def extra_repr(self) -> str:
    return 'in_features={}, out_features={}, bias={}'.format(self.in_features, self.out_features, self.bias is not None)

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

def save_checkpoint(self):
    if comm.is_main_process():
        filename = os.path.join(self.cfg.save_path, 'model', 'model_last.pth')
        self.logger.info('Saving checkpoint to: ' + filename)
        torch.save({'epoch': self.epoch + 1, 'state_dict': self.model.state_dict(), 'optimizer': self.optimizer.state_dict(), 'scheduler': self.scheduler.state_dict(), 'scaler': self.scaler.state_dict() if self.cfg.enable_amp else None, 'best_metric_value': self.best_metric_value}, filename + '.tmp')
        os.replace(filename + '.tmp', filename)
        if self.cfg.save_freq and self.cfg.save_freq % (self.epoch + 1) == 0:
            shutil.copyfile(filename, os.path.join(self.cfg.save_path, 'model', f'epoch_{self.epoch + 1}.pth'))

