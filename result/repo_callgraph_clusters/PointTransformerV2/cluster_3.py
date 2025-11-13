# Cluster 3

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

def __enter__(self):
    _CURRENT_STORAGE_STACK.append(self)
    return self

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

def intersection_and_union_gpu(output, target, k, ignore_index=255):
    assert output.dim() in [1, 2, 3]
    assert output.shape == target.shape
    output = output.view(-1)
    target = target.view(-1)
    output[target == ignore_index] = ignore_index
    intersection = output[output == target]
    area_intersection = torch.histc(intersection, bins=k, min=0, max=k - 1)
    area_output = torch.histc(output, bins=k, min=0, max=k - 1)
    area_target = torch.histc(target, bins=k, min=0, max=k - 1)
    area_union = area_output + area_target - area_intersection
    return (area_intersection, area_union, area_target)

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

def collate_fn(batch):
    """
    collate function for point cloud which support dict and list,
    'coord' is necessary to determine 'offset'
    """
    if not isinstance(batch, Sequence):
        raise TypeError(f'{batch.dtype} is not supported.')
    if isinstance(batch[0], torch.Tensor):
        return torch.cat(list(batch))
    elif isinstance(batch[0], Sequence):
        for data in batch:
            data.append(torch.tensor([data[0].shape[0]]))
        batch = [collate_fn(samples) for samples in zip(*batch)]
        batch[-1] = torch.cumsum(batch[-1], dim=0).int()
        return batch
    elif isinstance(batch[0], Mapping):
        batch = {key: collate_fn([d[key] for d in batch]) for key in batch[0]}
        for key in batch.keys():
            if 'offset' in key:
                batch[key] = torch.cumsum(batch[key], dim=0)
        return batch
    else:
        return default_collate(batch)

def point_collate_fn(batch, max_batch_points=10000000000.0, mix_prob=0):
    assert isinstance(batch[0], Mapping)
    batch = collate_fn(batch)
    if 'offset' in batch.keys():
        assert batch['offset'][0] <= max_batch_points
        for i in range(len(batch['offset']) - 1):
            if batch['offset'][i + 1] > max_batch_points:
                batch['offset'] = batch['offset'][:i + 1]
                for key in batch.keys():
                    if key != 'offset':
                        batch[key] = batch[key][:batch['offset'][-1]]
                break
        if random.random() < mix_prob:
            batch['offset'] = torch.cat([batch['offset'][1:-1:2], batch['offset'][-1].unsqueeze(0)], dim=0)
    return batch

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

def get_data_list(self):
    data_list = []
    for i in range(len(self.datasets)):
        data_list.extend(zip(np.ones(len(self.datasets[i]), dtype=np.long) * i, np.arange(len(self.datasets[i]))))
    return data_list

def vertex_normal(vertex, face):
    nf, area = face_normal(vertex, face)
    nf = nf * area
    nv = np.zeros_like(vertex)
    for i in range(face.shape[0]):
        nv[face[i]] += nf[i]
    length = np.sqrt(np.sum(nv ** 2, axis=1, keepdims=True)) + 1e-08
    nv = nv / length
    return nv

def vertex_normal(vertex, face):
    nf, area = face_normal(vertex, face)
    nf = nf * area
    nv = np.zeros_like(vertex)
    for i in range(face.shape[0]):
        nv[face[i]] += nf[i]
    length = np.sqrt(np.sum(nv ** 2, axis=1, keepdims=True)) + 1e-08
    nv = nv / length
    return nv

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

def get_matching_indices(source, pcd_tree, search_voxel_size, K=None):
    match_inds = []
    for i, point in enumerate(source.points):
        [_, idx, _] = pcd_tree.search_radius_vector_3d(point, search_voxel_size)
        if K is not None:
            idx = idx[:K]
        for j in idx:
            match_inds.append((i, j))
    return match_inds

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

def forward(self, input: torch.Tensor) -> torch.Tensor:
    if input.dim() == 3:
        return self.norm(input.transpose(1, 2).contiguous()).transpose(1, 2).contiguous()
    elif input.dim() == 2:
        return self.norm(input)
    else:
        raise NotImplementedError

def offset2batch(offset):
    return torch.cat([torch.tensor([i] * (o - offset[i - 1])) if i > 0 else torch.tensor([i] * o) for i, o in enumerate(offset)], dim=0).long().to(offset.device)

def batch2offset(batch):
    return torch.cumsum(batch.bincount(), dim=0).long()

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

def forward(self, input: torch.Tensor) -> torch.Tensor:
    return (input * self.weight).reshape(list(input.shape[:-1]) + [self.groups, input.shape[-1] // self.groups]).sum(-1)

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

def forward(self, input: torch.Tensor) -> torch.Tensor:
    if input.dim() == 3:
        return self.norm(input.transpose(1, 2).contiguous()).transpose(1, 2).contiguous()
    elif input.dim() == 2:
        return self.norm(input)
    else:
        raise NotImplementedError

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

def forward(self, points):
    coord, feat, offset = points
    reference_index, _ = pointops.knn_query(self.neighbours, coord, offset)
    for block in self.blocks:
        points = block(points, reference_index)
    return points

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

def forward(self, input: torch.Tensor) -> torch.Tensor:
    if input.dim() == 3:
        return self.norm(input.transpose(1, 2).contiguous()).transpose(1, 2).contiguous()
    elif input.dim() == 2:
        return self.norm(input)
    else:
        raise NotImplementedError

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

def forward(self, points):
    coord, feat, offset = points
    reference_index, _ = pointops.knn_query(self.neighbours, coord, offset)
    for block in self.blocks:
        points = block(points, reference_index)
    return points

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

class LayerNorm1d(nn.BatchNorm1d):

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        return super().forward(input.transpose(1, 2).contiguous()).transpose(1, 2).contiguous()

def forward(self, input: torch.Tensor) -> torch.Tensor:
    return super().forward(input.transpose(1, 2).contiguous()).transpose(1, 2).contiguous()

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

def _make_enc(self, block, planes, blocks, share_planes=8, stride=1, nsample=16):
    layers = [TransitionDown(self.in_planes, planes * block.expansion, stride, nsample)]
    self.in_planes = planes * block.expansion
    for _ in range(1, blocks):
        layers.append(block(self.in_planes, self.in_planes, share_planes, nsample=nsample))
    return nn.Sequential(*layers)

def offset2batch(offset):
    return torch.cat([torch.tensor([i] * (o - offset[i - 1])) if i > 0 else torch.tensor([i] * o) for i, o in enumerate(offset)], dim=0).long().to(offset.device)

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

def offset2batch(offset):
    return torch.cat([torch.tensor([i] * (o - offset[i - 1])) if i > 0 else torch.tensor([i] * o) for i, o in enumerate(offset)], dim=0).long().to(offset.device)

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

def offset2batch(offset):
    return torch.cat([torch.tensor([i] * (o - offset[i - 1])) if i > 0 else torch.tensor([i] * o) for i, o in enumerate(offset)], dim=0).long().to(offset.device)

def get_indice_pairs(p2v_map, counts, new_p2v_map, new_counts, downsample_idx, batch, xyz, window_size, i):
    n, k = p2v_map.shape
    mask = torch.arange(k).unsqueeze(0).cuda() < counts.unsqueeze(-1)
    mask_mat = mask.unsqueeze(-1) & mask.unsqueeze(-2)
    index_0 = p2v_map.unsqueeze(-1).expand(-1, -1, k)[mask_mat]
    index_1 = p2v_map.unsqueeze(1).expand(-1, k, -1)[mask_mat]
    downsample_mask = torch.zeros_like(batch).bool()
    downsample_mask[downsample_idx.long()] = True
    downsample_mask = downsample_mask[new_p2v_map]
    n, k = new_p2v_map.shape
    mask = torch.arange(k).unsqueeze(0).cuda() < new_counts.unsqueeze(-1)
    downsample_mask = downsample_mask & mask
    mask_mat = mask.unsqueeze(-1) & downsample_mask.unsqueeze(-2)
    xyz_min = xyz.min(0)[0]
    if i % 2 == 0:
        window_coord = (xyz[new_p2v_map] - xyz_min) // window_size
    else:
        window_coord = (xyz[new_p2v_map] + 1 / 2 * window_size - xyz_min) // window_size
    mask_mat_prev = (window_coord.unsqueeze(2) != window_coord.unsqueeze(1)).any(-1)
    mask_mat = mask_mat & mask_mat_prev
    new_index_0 = new_p2v_map.unsqueeze(-1).expand(-1, -1, k)[mask_mat]
    new_index_1 = new_p2v_map.unsqueeze(1).expand(-1, k, -1)[mask_mat]
    index_0 = torch.cat([index_0, new_index_0], 0)
    index_1 = torch.cat([index_1, new_index_1], 0)
    return (index_0, index_1)

def grid_sample(pos, batch, size, start, return_p2v=True):
    cluster = voxel_grid(pos, batch, size, start=start)
    if return_p2v == False:
        unique, cluster = torch.unique(cluster, sorted=True, return_inverse=True)
        return cluster
    unique, cluster, counts = torch.unique(cluster, sorted=True, return_inverse=True, return_counts=True)
    n = unique.shape[0]
    k = counts.max().item()
    p2v_map = cluster.new_zeros(n, k)
    mask = torch.arange(k).cuda().unsqueeze(0) < counts.unsqueeze(-1)
    p2v_map[mask] = torch.argsort(cluster)
    return (cluster, p2v_map, counts)

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

def forward(self, feats, xyz, support_xyz, offset, support_offset, support_feats=None):
    feats = self.linear1(support_feats) + pointops.interpolation(xyz, support_xyz, self.linear2(feats), offset, support_offset)
    return (feats, support_xyz, support_offset)

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

def offset2batch(offset):
    return torch.cat([torch.tensor([i] * (o - offset[i - 1])) if i > 0 else torch.tensor([i] * o) for i, o in enumerate(offset)], dim=0).long().to(offset.device)

def grid_sample(coords, batch, size, start, return_p2v=True):
    cluster = voxel_grid(coords, batch, size, start=start)
    if not return_p2v:
        unique, cluster = torch.unique(cluster, sorted=True, return_inverse=True)
        return cluster
    else:
        unique, cluster, counts = torch.unique(cluster, sorted=True, return_inverse=True, return_counts=True)
        n = unique.shape[0]
        k = counts.max().item()
        p2v_map = cluster.new_zeros(n, k)
        mask = torch.arange(k).cuda().unsqueeze(0) < counts.unsqueeze(-1)
        p2v_map[mask] = torch.argsort(cluster)
        return (cluster, p2v_map, counts)

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

def forward(self, feats, coords, offset, skip_feats, skip_coords, skip_offset):
    feats = self.linear1(skip_feats) + pointops.interpolation(coords, skip_coords, self.linear2(feats), offset, skip_offset)
    return (feats, skip_coords, skip_offset)

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

def grouping(idx, feat, xyz, new_xyz=None, with_xyz=False):
    if new_xyz is None:
        new_xyz = xyz
    assert xyz.is_contiguous() and feat.is_contiguous()
    m, nsample, c = (idx.shape[0], idx.shape[1], feat.shape[1])
    xyz = torch.cat([xyz, torch.zeros([1, 3]).to(xyz.device)], dim=0)
    feat = torch.cat([feat, torch.zeros([1, c]).to(feat.device)], dim=0)
    grouped_feat = feat[idx.view(-1).long(), :].view(m, nsample, c)
    if with_xyz:
        assert new_xyz.is_contiguous()
        mask = torch.sign(idx + 1)
        grouped_xyz = xyz[idx.view(-1).long(), :].view(m, nsample, 3) - new_xyz.unsqueeze(1)
        grouped_xyz = torch.einsum('n s c, n s -> n s c', grouped_xyz, mask)
        return torch.cat((grouped_xyz, grouped_feat), -1)
    else:
        return grouped_feat

def knn_query_and_group(feat, xyz, offset=None, new_xyz=None, new_offset=None, idx=None, nsample=None, with_xyz=False):
    if idx is None:
        assert nsample is not None
        idx, _ = knn_query(nsample, xyz, offset, new_xyz, new_offset)
    return (grouping(idx, feat, xyz, new_xyz, with_xyz), idx)

def ball_query_and_group(feat, xyz, offset=None, new_xyz=None, new_offset=None, idx=None, max_radio=None, min_radio=0, nsample=None, with_xyz=False):
    if idx is None:
        assert nsample is not None and offset is not None
        assert max_radio is not None and min_radio is not None
        idx, _ = ball_query(nsample, max_radio, min_radio, xyz, offset, new_xyz, new_offset)
    return (grouping(idx, feat, xyz, new_xyz, with_xyz), idx)

def query_and_group(nsample, xyz, new_xyz, feat, idx, offset, new_offset, dilation=0, with_feat=True, with_xyz=True):
    """
    input: coords: (n, 3), new_xyz: (m, 3), color: (n, c), idx: (m, nsample), offset: (b), new_offset: (b)
    output: new_feat: (m, nsample, c+3), grouped_idx: (m, nsample)
    """
    assert xyz.is_contiguous() and new_xyz.is_contiguous() and feat.is_contiguous()
    if new_xyz is None:
        new_xyz = xyz
    if idx is None:
        num_samples_total = 1 + (nsample - 1) * (dilation + 1)
        idx_no_dilation, _ = knn_query(num_samples_total, xyz, offset, new_xyz, new_offset)
        idx = []
        batch_end = offset.tolist()
        batch_start = [0] + batch_end[:-1]
        new_batch_end = new_offset.tolist()
        new_batch_start = [0] + new_batch_end[:-1]
        for i in range(offset.shape[0]):
            if batch_end[i] - batch_start[i] < num_samples_total:
                soft_dilation = (batch_end[i] - batch_start[i] - 1) / (nsample - 1) - 1
            else:
                soft_dilation = dilation
            idx.append(idx_no_dilation[new_batch_start[i]:new_batch_end[i], [int((soft_dilation + 1) * i) for i in range(nsample)]])
        idx = torch.cat(idx, dim=0)
    if not with_feat:
        return idx
    n, m, c = (xyz.shape[0], new_xyz.shape[0], feat.shape[1])
    grouped_xyz = xyz[idx.view(-1).long(), :].view(m, nsample, 3)
    grouped_xyz -= new_xyz.unsqueeze(1)
    grouped_feat = feat[idx.view(-1).long(), :].view(m, nsample, c)
    if with_xyz:
        return (torch.cat((grouped_xyz, grouped_feat), -1), idx)
    else:
        return (grouped_feat, idx)

def offset2batch(offset):
    return torch.cat([torch.tensor([i] * (o - offset[i - 1])) if i > 0 else torch.tensor([i] * o) for i, o in enumerate(offset)], dim=0).long().to(offset.device)

def batch2offset(batch):
    return torch.cumsum(batch.bincount(), dim=0).int()

def interpolation(xyz, new_xyz, feat, offset, new_offset, k=3):
    """
    input: coords: (m, 3), new_xyz: (n, 3), color: (m, c), offset: (b), new_offset: (b)
    output: (n, c)
    """
    assert xyz.is_contiguous() and new_xyz.is_contiguous() and feat.is_contiguous()
    idx, dist = knn_query(k, xyz, offset, new_xyz, new_offset)
    dist_recip = 1.0 / (dist + 1e-08)
    norm = torch.sum(dist_recip, dim=1, keepdim=True)
    weight = dist_recip / norm
    new_feat = torch.cuda.FloatTensor(new_xyz.shape[0], feat.shape[1]).zero_()
    for i in range(k):
        new_feat += feat[idx[:, i].long(), :] * weight[:, i].unsqueeze(-1)
    return new_feat

def queryandgroup(nsample, xyz, new_xyz, feat, idx, offset, new_offset, use_xyz=True, return_indx=False):
    """
    input: xyz: (n, 3), new_xyz: (m, 3), feat: (n, c), idx: (m, nsample), offset: (b), new_offset: (b)
    output: new_feat: (m, c+3, nsample), grouped_idx: (m, nsample)
    """
    assert xyz.is_contiguous() and new_xyz.is_contiguous() and feat.is_contiguous()
    if new_xyz is None:
        new_xyz = xyz
    if idx is None:
        idx, _ = knnquery(nsample, xyz, new_xyz, offset, new_offset)
    n, m, c = (xyz.shape[0], new_xyz.shape[0], feat.shape[1])
    grouped_xyz = xyz[idx.view(-1).long(), :].view(m, nsample, 3)
    grouped_xyz -= new_xyz.unsqueeze(1)
    grouped_feat = feat[idx.view(-1).long(), :].view(m, nsample, c)
    if use_xyz:
        if return_indx:
            return (torch.cat((grouped_xyz, grouped_feat), -1), idx)
        else:
            return torch.cat((grouped_xyz, grouped_feat), -1)
    elif return_indx:
        return (grouped_feat, idx)
    else:
        return grouped_feat

def Divide2Patch(nsample, xyz, offset, return_offset=False, anchor_scale=None):
    downsample_scale = anchor_scale or nsample
    new_offset, count = ([offset[0].item() // downsample_scale], offset[0].item() // downsample_scale)
    for i in range(1, offset.shape[0]):
        count += (offset[i].item() - offset[i - 1].item()) // downsample_scale
        new_offset.append(count)
    new_offset = torch.cuda.IntTensor(new_offset)
    idx = furthestsampling(xyz, offset, new_offset)
    new_xyz = xyz[idx.long()]
    p_idx, _ = knnquery(nsample, xyz, new_xyz, offset, new_offset)
    if return_offset:
        return (p_idx, new_offset)
    else:
        return p_idx

def interpolation(xyz, new_xyz, feat, offset, new_offset, k=3):
    """
    input: xyz: (m, 3), new_xyz: (n, 3), feat: (m, c), offset: (b), new_offset: (b)
    output: (n, c)
    """
    assert xyz.is_contiguous() and new_xyz.is_contiguous() and feat.is_contiguous()
    idx, dist = knnquery(k, xyz, new_xyz, offset, new_offset)
    dist_recip = 1.0 / (dist + 1e-08)
    norm = torch.sum(dist_recip, dim=1, keepdim=True)
    weight = dist_recip / norm
    new_feat = torch.cuda.FloatTensor(new_xyz.shape[0], feat.shape[1]).zero_()
    for i in range(k):
        new_feat += feat[idx[:, i].long(), :] * weight[:, i].unsqueeze(-1)
    return new_feat

def interpolation_v2(xyz, new_xyz, feat, offset, new_offset, k=3):
    """
    input: xyz: (m, 3), new_xyz: (n, 3), feat: (m, c), offset: (b), new_offset: (b)
    output: (n, c)
    """
    assert xyz.is_contiguous() and new_xyz.is_contiguous() and feat.is_contiguous()
    idx, _ = knnquery(k, xyz, new_xyz, offset, new_offset)
    dist = torch.sqrt(((new_xyz.unsqueeze(1) - xyz[idx.long()]) ** 2).sum(-1) + 1e-08)
    dist_recip = 1.0 / (dist + 1e-08)
    norm = torch.sum(dist_recip, dim=1, keepdim=True)
    weight = dist_recip / norm
    new_feat = torch.cuda.FloatTensor(new_xyz.shape[0], feat.shape[1]).zero_()
    for i in range(k):
        new_feat += feat[idx[:, i].long(), :] * weight[:, i].unsqueeze(-1)
    return new_feat

def queryandgroup(nsample, xyz, new_xyz, feat, idx, offset, new_offset, use_xyz=True):
    """
    input: xyz: (n, 3), new_xyz: (m, 3), feat: (n, c), idx: (m, nsample), offset: (b), new_offset: (b)
    output: new_feat: (m, c+3, nsample), grouped_idx: (m, nsample)
    """
    assert xyz.is_contiguous() and new_xyz.is_contiguous() and feat.is_contiguous()
    if new_xyz is None:
        new_xyz = xyz
    if idx is None:
        idx, _ = knnquery(nsample, xyz, new_xyz, offset, new_offset)
    n, m, c = (xyz.shape[0], new_xyz.shape[0], feat.shape[1])
    grouped_xyz = xyz[idx.view(-1).long(), :].view(m, nsample, 3)
    grouped_xyz -= new_xyz.unsqueeze(1)
    grouped_feat = feat[idx.view(-1).long(), :].view(m, nsample, c)
    if use_xyz:
        return torch.cat((grouped_xyz, grouped_feat), -1)
    else:
        return grouped_feat

def interpolation(xyz, new_xyz, feat, offset, new_offset, k=3):
    """
    input: xyz: (m, 3), new_xyz: (n, 3), feat: (m, c), offset: (b), new_offset: (b)
    output: (n, c)
    """
    assert xyz.is_contiguous() and new_xyz.is_contiguous() and feat.is_contiguous()
    idx, dist = knnquery(k, xyz, new_xyz, offset, new_offset)
    dist_recip = 1.0 / (dist + 1e-08)
    norm = torch.sum(dist_recip, dim=1, keepdim=True)
    weight = dist_recip / norm
    new_feat = torch.cuda.FloatTensor(new_xyz.shape[0], feat.shape[1]).zero_()
    for i in range(k):
        new_feat += feat[idx[:, i].long(), :] * weight[:, i].unsqueeze(-1)
    return new_feat

def queryandgroup(nsample, xyz, new_xyz, feat, idx, offset, new_offset, use_xyz=True, relative=True):
    """
    input: xyz: (n, 3), new_xyz: (m, 3), feat: (n, c), idx: (m, nsample), offset: (b), new_offset: (b)
    output: new_feat: (m, c+3, nsample), grouped_idx: (m, nsample)
    """
    assert xyz.is_contiguous() and new_xyz.is_contiguous() and feat.is_contiguous()
    if new_xyz is None:
        new_xyz = xyz
    if idx is None:
        idx, _ = knnquery(nsample, xyz, new_xyz, offset, new_offset)
    n, m, c = (xyz.shape[0], new_xyz.shape[0], feat.shape[1])
    grouped_xyz = xyz[idx.view(-1).long(), :].view(m, nsample, 3)
    if relative:
        grouped_xyz -= new_xyz.unsqueeze(1)
    grouped_feat = feat[idx.view(-1).long(), :].view(m, nsample, c)
    if use_xyz:
        return torch.cat((grouped_xyz, grouped_feat), -1)
    else:
        return grouped_feat

def interpolation(xyz, new_xyz, feat, offset, new_offset, k=3):
    """
    input: xyz: (m, 3), new_xyz: (n, 3), feat: (m, c), offset: (b), new_offset: (b)
    output: (n, c)
    """
    assert xyz.is_contiguous() and new_xyz.is_contiguous() and feat.is_contiguous()
    idx, dist = knnquery(k, xyz, new_xyz, offset, new_offset)
    dist_recip = 1.0 / (dist + 1e-08)
    norm = torch.sum(dist_recip, dim=1, keepdim=True)
    weight = dist_recip / norm
    new_feat = torch.cuda.FloatTensor(new_xyz.shape[0], feat.shape[1]).zero_()
    for i in range(k):
        new_feat += feat[idx[:, i].long(), :] * weight[:, i].unsqueeze(-1)
    return new_feat

