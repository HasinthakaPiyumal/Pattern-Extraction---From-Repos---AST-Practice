# Cluster 15

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

@TRANSFORMS.register_module()
class RandomColorGrayScale(object):

    def __init__(self, p):
        self.p = p

    @staticmethod
    def rgb_to_grayscale(color, num_output_channels=1):
        if color.shape[-1] < 3:
            raise TypeError('Input color should have at least 3 dimensions, but found {}'.format(color.shape[-1]))
        if num_output_channels not in (1, 3):
            raise ValueError('num_output_channels should be either 1 or 3')
        r, g, b = (color[..., 0], color[..., 1], color[..., 2])
        gray = (0.2989 * r + 0.587 * g + 0.114 * b).astype(color.dtype)
        gray = np.expand_dims(gray, axis=-1)
        if num_output_channels == 3:
            gray = np.broadcast_to(gray, color.shape)
        return gray

    def __call__(self, data_dict):
        if np.random.rand() < self.p:
            data_dict['color'] = self.rgb_to_grayscale(data_dict['color'], 3)
        return data_dict

@staticmethod
def rgb_to_grayscale(color, num_output_channels=1):
    if color.shape[-1] < 3:
        raise TypeError('Input color should have at least 3 dimensions, but found {}'.format(color.shape[-1]))
    if num_output_channels not in (1, 3):
        raise ValueError('num_output_channels should be either 1 or 3')
    r, g, b = (color[..., 0], color[..., 1], color[..., 2])
    gray = (0.2989 * r + 0.587 * g + 0.114 * b).astype(color.dtype)
    gray = np.expand_dims(gray, axis=-1)
    if num_output_channels == 3:
        gray = np.broadcast_to(gray, color.shape)
    return gray

def __call__(self, data_dict):
    if np.random.rand() < self.p:
        data_dict['color'] = self.rgb_to_grayscale(data_dict['color'], 3)
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

def read_plymesh(filepath):
    """Read ply file and return it as numpy array. Returns None if emtpy."""
    with open(filepath, 'rb') as f:
        plydata = plyfile.PlyData.read(f)
    if plydata.elements:
        vertices = pd.DataFrame(plydata['vertex'].data).values
        faces = np.stack(plydata['face'].data['vertex_indices'], axis=0)
        return (vertices, faces)

def read_plymesh(filepath):
    """Read ply file and return it as numpy array. Returns None if emtpy."""
    with open(filepath, 'rb') as f:
        plydata = plyfile.PlyData.read(f)
    if plydata.elements:
        vertices = pd.DataFrame(plydata['vertex'].data).values
        faces = np.stack(plydata['face'].data['vertex_indices'], axis=0)
        return (vertices, faces)

def _lookup_type(type_str):
    if type_str not in _data_type_reverse:
        try:
            type_str = _data_types[type_str]
        except KeyError:
            raise ValueError('field type %r not in %r' % (type_str, _types_list))
    return _data_type_reverse[type_str]

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

def _set_byte_order(self, byte_order):
    if byte_order not in ['<', '>', '=']:
        raise ValueError("byte order must be '<', '>', or '='")
    self._byte_order = byte_order

def _index(self):
    self._element_lookup = dict(((elt.name, elt) for elt in self._elements))
    if len(self._element_lookup) != len(self._elements):
        raise ValueError('two elements with same name')

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

def _check_sanity(self):
    for prop in self.properties:
        if prop.name not in self._data.dtype.fields:
            raise ValueError('dangling property %r' % prop.name)

def _index(self):
    self._property_lookup = dict(((prop.name, prop) for prop in self._properties))
    if len(self._property_lookup) != len(self._properties):
        raise ValueError('two properties with same name')

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

def _set_val_dtype(self, val_dtype):
    self._val_dtype = _data_types[_lookup_type(val_dtype)]

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

def __repr__(self):
    return 'PlyProperty(%r, %r)' % (self.name, _lookup_type(self.val_dtype))

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

def _set_len_dtype(self, len_dtype):
    self._len_dtype = _data_types[_lookup_type(len_dtype)]

def __repr__(self):
    return 'PlyListProperty(%r, %r, %r)' % (self.name, _lookup_type(self.len_dtype), _lookup_type(self.val_dtype))

