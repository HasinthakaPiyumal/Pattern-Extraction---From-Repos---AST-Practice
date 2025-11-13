# Cluster 5

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

def __call__(self, pred, target):
    if len(self.criteria) == 0:
        return pred
    loss = 0
    for c in self.criteria:
        loss += c(pred, target)
    return loss

def save_point_cloud(coord, color=None, file_path='pc.ply', logger=None):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    coord = to_numpy(coord)
    if color is not None:
        color = to_numpy(color)
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(coord)
    pcd.colors = o3d.utility.Vector3dVector(np.ones_like(coord) if color is None else color)
    o3d.io.write_point_cloud(file_path, pcd)
    if logger is not None:
        logger.info(f'Save Point Cloud to: {file_path}')

def save_bounding_boxes(bboxes_corners, color=(1.0, 0.0, 0.0), file_path='bbox.ply', logger=None):
    bboxes_corners = to_numpy(bboxes_corners)
    points = bboxes_corners.reshape(-1, 3)
    box_lines = np.array([[0, 1], [1, 2], [2, 3], [3, 0], [4, 5], [5, 6], [6, 7], [7, 0], [0, 4], [1, 5], [2, 6], [3, 7]])
    lines = []
    for i, _ in enumerate(bboxes_corners):
        lines.append(box_lines + i * 8)
    lines = np.concatenate(lines)
    color = np.array([color for _ in range(len(lines))])
    line_set = o3d.geometry.LineSet()
    line_set.points = o3d.utility.Vector3dVector(points)
    line_set.lines = o3d.utility.Vector2iVector(lines)
    line_set.colors = o3d.utility.Vector3dVector(color)
    o3d.io.write_line_set(file_path, line_set)
    if logger is not None:
        logger.info(f'Save Boxes to: {file_path}')

def save_lines(points, lines, color=(1.0, 0.0, 0.0), file_path='lines.ply', logger=None):
    points = to_numpy(points)
    lines = to_numpy(lines)
    colors = np.array([color for _ in range(len(lines))])
    line_set = o3d.geometry.LineSet()
    line_set.points = o3d.utility.Vector3dVector(points)
    line_set.lines = o3d.utility.Vector2iVector(lines)
    line_set.colors = o3d.utility.Vector3dVector(colors)
    o3d.io.write_line_set(file_path, line_set)
    if logger is not None:
        logger.info(f'Save Lines to: {file_path}')

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

def get_event_storage():
    """
    Returns:
        The :class:`EventStorage` object that's currently being used.
        Throws an error if no :class:`EventStorage` is currently enabled.
    """
    assert len(_CURRENT_STORAGE_STACK), "get_event_storage() has to be called inside a 'with EventStorage(...)' context!"
    return _CURRENT_STORAGE_STACK[-1]

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

def __exit__(self, exc_type, exc_val, exc_tb):
    assert _CURRENT_STORAGE_STACK[-1] == self
    _CURRENT_STORAGE_STACK.pop()

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

def _indent(s_, num_spaces):
    s = s_.split('\n')
    if len(s) == 1:
        return s_
    first = s.pop(0)
    s = [num_spaces * ' ' + line for line in s]
    s = '\n'.join(s)
    s = first + '\n' + s
    return s

def __len__(self):
    return len(self._cfg_dict)

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

def __call__(self, parser, namespace, values, option_string=None):
    options = {}
    for kv in values:
        key, val = kv.split('=', maxsplit=1)
        options[key] = self._parse_iterable(val)
    setattr(namespace, self.dest, options)

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

def __len__(self):
    return len(self._module_dict)

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

def __len__(self):
    return len(self.data_list) * self.loop

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

def get_data_name(self, idx):
    return self.data_list[self.data_list[idx % len(self.data_list)]]

def __len__(self):
    return len(self.data_list) * self.loop

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

def __len__(self):
    return len(self.data_list) * self.loop

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

def __len__(self):
    return len(self.data_list) * self.loop

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

def __len__(self):
    return len(self.data_list) * self.loop

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

def __len__(self):
    return len(self.data_idx) * self.loop

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

def __len__(self):
    return len(self.data_idx) * self.loop

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

def __len__(self):
    return len(self.data_list) * self.loop

def parse_object(room_mesh, object_dir, output_dir):
    object_coords = np.loadtxt(object_dir)[:, :3]
    closest_points, distances, face_id = room_mesh.nearest.on_surface(object_coords)
    point_normals = room_mesh.face_normals[face_id]
    np.savetxt(os.path.join(output_dir, os.path.basename(object_dir)), point_normals)

def point_indices_from_group(seg_indices, group, labels_pd):
    group_segments = np.array(group['segments'])
    label = group['label']
    label_id20 = labels_pd[labels_pd['raw_category'] == label]['nyu40id']
    label_id20 = int(label_id20.iloc[0]) if len(label_id20) > 0 else 0
    label_id200 = labels_pd[labels_pd['raw_category'] == label]['id']
    label_id200 = int(label_id200.iloc[0]) if len(label_id200) > 0 else 0
    if label_id20 in CLASS_IDS20:
        label_id20 = CLASS_IDS20.index(label_id20)
    else:
        label_id20 = IGNORE_INDEX
    if label_id200 in CLASS_IDS200:
        label_id200 = CLASS_IDS200.index(label_id200)
    else:
        label_id200 = IGNORE_INDEX
    point_idx = np.where(np.isin(seg_indices, group_segments))[0]
    return (point_idx, label_id20, label_id200)

def _split_line(line, n):
    fields = line.split(None, n)
    if len(fields) == n:
        fields.append('')
    assert len(fields) == n + 1
    return fields

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

def __len__(self):
    return len(self.elements)

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

def make_open3d_point_cloud(xyz, color=None, voxel_size=None):
    if np.isnan(xyz).any():
        return None
    xyz = xyz[:, :3]
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(xyz)
    if color is not None:
        pcd.colors = o3d.utility.Vector3dVector(color)
    if voxel_size is not None:
        pcd = pcd.voxel_down_sample(voxel_size)
    return pcd

def compute_overlap_ratio(pcd0, pcd1, voxel_size):
    pcd0_down = pcd0.voxel_down_sample(voxel_size)
    pcd1_down = pcd1.voxel_down_sample(voxel_size)
    matching01 = get_matching_indices(pcd0_down, pcd1_down, voxel_size * 1.5, 1)
    matching10 = get_matching_indices(pcd1_down, pcd0_down, voxel_size * 1.5, 1)
    overlap0 = float(len(matching01)) / float(len(pcd0_down.points))
    overlap1 = float(len(matching10)) / float(len(pcd1_down.points))
    return max(overlap0, overlap1)

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

def save_mat_to_file(self, matrix, filename):
    with open(filename, 'w') as f:
        for line in matrix:
            np.savetxt(f, line[np.newaxis], fmt='%f')

