# Cluster 16

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

def __iter__(self):
    return iter(self._cfg_dict)

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

@property
def _data_loader_iter(self):
    if self._data_loader_iter_obj is None:
        self._data_loader_iter_obj = iter(self.data_loader)
    return self._data_loader_iter_obj

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

def __iter__(self):
    return iter(self.elements)

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

def _set_data(self, data):
    self._data = data
    self._count = len(data)
    self._check_sanity()

def _set_properties(self, properties):
    self._properties = tuple(properties)
    self._check_sanity()
    self._index()

def dtype(self, byte_order='='):
    """
        Return the numpy dtype of the in-memory representation of the
        data.  (If there are no list properties, and the PLY format is
        binary, then this also accurately describes the on-disk
        representation of the element.)

        """
    return [(prop.name, prop.dtype(byte_order)) for prop in self.properties]

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

