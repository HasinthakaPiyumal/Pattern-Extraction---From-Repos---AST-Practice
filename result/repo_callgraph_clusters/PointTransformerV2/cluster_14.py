# Cluster 14

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

def close(self):
    self._file_handle.close()

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

def find_free_port():
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port

def _find_free_port():
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port

def default_argument_parser(epilog=None):
    parser = argparse.ArgumentParser(epilog=epilog or f'\n    Examples:\n    Run on single machine:\n        $ {sys.argv[0]} --num-gpus 8 --config-file cfg.yaml\n    Change some config options:\n        $ {sys.argv[0]} --config-file cfg.yaml MODEL.WEIGHTS /path/to/weight.pth SOLVER.BASE_LR 0.001\n    Run on multiple machines:\n        (machine0)$ {sys.argv[0]} --machine-rank 0 --num-machines 2 --dist-url <URL> [--other-flags]\n        (machine1)$ {sys.argv[0]} --machine-rank 1 --num-machines 2 --dist-url <URL> [--other-flags]\n    ', formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--config-file', default='', metavar='FILE', help='path to config file')
    parser.add_argument('--num-gpus', type=int, default=1, help='number of gpus *per machine*')
    parser.add_argument('--num-machines', type=int, default=1, help='total number of machines')
    parser.add_argument('--machine-rank', type=int, default=0, help='the rank of this machine (unique per machine)')
    parser.add_argument('--dist-url', default='auto', help='initialization URL for pytorch distributed backend. See https://pytorch.org/docs/stable/distributed.html for details.')
    parser.add_argument('--options', nargs='+', action=DictAction, help='custom options')
    return parser

def main_process():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset_root', type=str, default='/home/gofinge/Documents/datasets/Stanford3dDataset_v1.2_Aligned_Version')
    parser.add_argument('--output_root', type=str, default='/home/gofinge/Documents/datasets/processed/s3dis')
    parser.add_argument('--parse_normals', action='store_true')
    opt = parser.parse_args()
    room_list = []
    for i in range(1, 7):
        if 'Aligned_Version' in opt.dataset_root:
            area_dir = os.path.join(opt.dataset_root, 'Area_{}'.format(i))
            room_name_list = os.listdir(area_dir)
            room_name_list = [room_name for room_name in room_name_list if room_name != '.DS_Store' and '.txt' not in room_name]
            room_list += [os.path.join('Area_{}'.format(i), room_name) for room_name in room_name_list]
        else:
            area_dir = os.path.join(opt.dataset_root, 'Area_{}'.format(i))
            align_dir = os.path.join(area_dir, 'Area_{}_alignmentAngle.txt'.format(i))
            room_name_list = np.loadtxt(align_dir, dtype=str)
            room_list += [[os.path.join('Area_{}'.format(i), room_name[0]), int(room_name[1])] for room_name in room_name_list]
    pool = mp.Pool(processes=mp.cpu_count())
    pool.starmap(parse_room, [(room, opt.dataset_root, opt.save_root, opt.parse_normals) for room in room_list])
    pool.close()
    pool.join()

def align_area5b():
    mesh_dir_a = '/home/gofinge/Documents/datasets/Stanford2d3dDataset_noXYZ/area_5a/3d/rgb.obj'
    mesh_dir_b = '/home/gofinge/Documents/datasets/Stanford2d3dDataset_noXYZ/area_5b/3d/rgb.obj'
    mesh_a = open3d.io.read_triangle_mesh(mesh_dir_a)
    mesh_a.triangle_uvs.clear()
    mesh_b = open3d.io.read_triangle_mesh(mesh_dir_b)
    mesh_b.triangle_uvs.clear()
    mesh_b = mesh_b.transform(np.array([[0, 0, -1, -4.09703582], [0, 1, 0, 0], [1, 0, 0, -6.22617759], [0, 0, 0, 1]]))
    os.makedirs('tmp/area_5/3d', exist_ok=True)
    open3d.io.write_triangle_mesh('tmp/area_5/3d/rgb_a.obj', mesh_a)
    open3d.io.write_triangle_mesh('tmp/area_5/3d/rgb_b.obj', mesh_b)
    print('Done')

def main_process():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_area', help='number of s3dis data area', default='1')
    parser.add_argument('--raw_data_root', type=str, default='/home/gofinge/Documents/datasets/Stanford2d3dDataset_noXYZ')
    parser.add_argument('--s3dis_data_root', type=str, default='/home/gofinge/Documents/datasets/Stanford3dDataset_v1.2')
    parser.add_argument('--output_root', type=str, default='/home/gofinge/Documents/datasets/Stanford3dDataset_v1.2_normals')
    opt = parser.parse_args()
    mesh_dir = os.path.join(opt.raw_data_root, 'area_{}'.format(opt.data_area), '3d', 'rgb.obj')
    mesh = open3d.io.read_triangle_mesh(mesh_dir)
    mesh.triangle_uvs.clear()
    room_name_list = os.listdir(os.path.join(opt.s3dis_data_root, 'Area_{}'.format(opt.data_area)))
    room_name_list = [room_name for room_name in room_name_list if room_name != '.DS_Store' and '.txt' not in room_name]
    bar = tqdm.tqdm(room_name_list)
    pool = mp.Pool(processes=mp.cpu_count())
    for room_name in bar:
        bar.set_postfix_str(room_name)
        room_dir = os.path.join(opt.s3dis_data_root, 'Area_{}'.format(opt.data_area), room_name)
        output_dir = os.path.join(room_dir.replace(opt.s3dis_data_root, opt.output_root), 'Normals')
        os.makedirs(output_dir, exist_ok=True)
        room_coords = np.loadtxt(os.path.join(room_dir, '{}.txt'.format(room_name)))[:, :3]
        x_min, z_max, y_min = room_coords.min(axis=0)
        x_max, z_min, y_max = room_coords.max(axis=0)
        z_max = -z_max
        z_min = -z_min
        max_bound = np.array([x_max, y_max, z_max]) + 0.1
        min_bound = np.array([x_min, y_min, z_min]) - 0.1
        bbox = open3d.geometry.AxisAlignedBoundingBox(min_bound=min_bound, max_bound=max_bound)
        room = mesh.crop(bbox).transform(np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]]))
        vertices = np.array(room.vertices)
        faces = np.array(room.triangles)
        vertex_normals = np.array(room.vertex_normals)
        room = trimesh.Trimesh(vertices=vertices, faces=faces, vertex_normals=vertex_normals)
        object_dir_list = glob.glob(os.path.join(room_dir, 'Annotations', '*.txt'))
        pool.starmap(parse_object, [(room, object_dir, output_dir) for object_dir in object_dir_list])
    pool.close()
    pool.join()

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

def main():
    args = default_argument_parser().parse_args()
    cfg = default_config_parser(args.config_file, args.options)
    launch(main_worker, num_gpus_per_machine=args.num_gpus, num_machines=args.num_machines, machine_rank=args.machine_rank, dist_url=args.dist_url, cfg=(cfg,))

def get_parser():
    parser = argparse.ArgumentParser(description='PCR Test Process')
    parser.add_argument('--config-file', default='', metavar='FILE', help='path to config file')
    parser.add_argument('--options', nargs='+', action=DictAction, help='custom options')
    args = parser.parse_args()
    return args

def main():
    args = default_argument_parser().parse_args()
    cfg = default_config_parser(args.config_file, args.options)
    launch(main_worker, num_gpus_per_machine=args.num_gpus, num_machines=args.num_machines, machine_rank=args.machine_rank, dist_url=args.dist_url, cfg=(cfg,))

