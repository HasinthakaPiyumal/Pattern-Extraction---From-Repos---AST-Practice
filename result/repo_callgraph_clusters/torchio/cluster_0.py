# Cluster 0

def plot_batch(sampler):
    queue = tio.Queue(dataset, max_queue_length, patches_per_volume, sampler)
    loader = tio.SubjectsLoader(queue, batch_size=16)
    batch = tio.utils.get_first_item(loader)
    _, axes = plt.subplots(4, 4, figsize=(12, 10))
    for ax, im in zip(axes.flatten(), batch['t1']['data']):
        ax.imshow(im.squeeze(), cmap='gray')
    plt.suptitle(sampler.__class__.__name__)
    plt.tight_layout()

def _update_frame(num):
    frame = get_frame(image, num)
    im.set_data(frame)
    return

def plot_gif(image):

    def _update_frame(num):
        frame = get_frame(image, num)
        im.set_data(frame)
        return

    def get_frame(image, i):
        return image.data[..., i].permute(1, 2, 0).byte()
    plt.rcParams['animation.embed_limit'] = 25
    fig, ax = plt.subplots()
    im = ax.imshow(get_frame(image, 0))
    return animation.FuncAnimation(fig, _update_frame, repeat_delay=image['delay'], frames=image.shape[-1])

def main():
    num_epochs = 20
    patch_size = 128
    queue_length = 100
    patches_per_volume = 5
    batch_size = 2
    one_subject = Subject(T1=ScalarImage('../BRATS2018_crop_renamed/LGG75_T1.nii.gz'), T2=ScalarImage('../BRATS2018_crop_renamed/LGG75_T2.nii.gz'), label=LabelMap('../BRATS2018_crop_renamed/LGG75_Label.nii.gz'))
    another_subject = Subject(T1=ScalarImage('../BRATS2018_crop_renamed/LGG74_T1.nii.gz'), label=LabelMap('../BRATS2018_crop_renamed/LGG74_Label.nii.gz'))
    subjects = [one_subject, another_subject]
    subjects_dataset = SubjectsDataset(subjects)
    queue_dataset = Queue(subjects_dataset, queue_length, patches_per_volume, UniformSampler(patch_size))
    batch_loader = tio.SubjectsLoader(queue_dataset, batch_size=batch_size, collate_fn=lambda x: x)
    model = nn.Identity()
    for epoch_index in range(num_epochs):
        logging.info('Epoch %s', epoch_index)
        for batch in batch_loader:
            logits = model(batch)
            logging.info([batch[idx].keys() for idx in range(batch_size)])
            logging.info(logits.shape)
    logging.info('')

def plot_volume(image: Image, radiological=True, channel=None, axes=None, cmap=None, output_path=None, show=True, xlabels=True, percentiles: tuple[float, float]=(0, 100), figsize=None, title=None, reorient=True, indices=None, rgb=True, savefig_kwargs: dict[str, Any] | None=None, **imshow_kwargs) -> Figure | None:
    _, plt = import_mpl_plt()
    fig: Figure | None = None
    if axes is None:
        fig, axes = plt.subplots(1, 3, figsize=figsize)
    if reorient:
        image = ToCanonical()(image)
    is_label = isinstance(image, LabelMap)
    if is_label:
        data = image.data[np.newaxis, -1]
    elif rgb and image.num_channels == 3:
        data = image.data
    elif channel is None:
        data = image.data[0:1]
    else:
        data = image.data[np.newaxis, channel]
    data = rearrange(data, 'c x y z -> x y z c')
    data_numpy: np.ndarray = data.cpu().numpy()
    if indices is None:
        indices = np.array(data_numpy.shape[:3]) // 2
    i, j, k = indices
    slice_x = rotate(data_numpy[i, :, :], radiological=radiological)
    slice_y = rotate(data_numpy[:, j, :], radiological=radiological)
    slice_z = rotate(data_numpy[:, :, k], radiological=radiological)
    if isinstance(cmap, dict):
        slices = (slice_x, slice_y, slice_z)
        slice_x, slice_y, slice_z = color_labels(slices, cmap)
    else:
        boundary_norm = None
        if cmap is None:
            if is_label:
                cmap, boundary_norm = _create_categorical_colormap(data)
            else:
                cmap = 'gray'
        imshow_kwargs['cmap'] = cmap
        imshow_kwargs['norm'] = boundary_norm
    if is_label:
        imshow_kwargs['interpolation'] = 'none'
    elif 'interpolation' not in imshow_kwargs:
        imshow_kwargs['interpolation'] = 'bicubic'
    imshow_kwargs['origin'] = 'lower'
    if not is_label:
        displayed_data = np.concatenate([slice_x.flatten(), slice_y.flatten(), slice_z.flatten()])
        p1, p2 = np.percentile(displayed_data, percentiles)
        if 'vmin' not in imshow_kwargs:
            imshow_kwargs['vmin'] = p1
        if 'vmax' not in imshow_kwargs:
            imshow_kwargs['vmax'] = p2
    spacing_r, spacing_a, spacing_s = image.spacing
    sag_axis, cor_axis, axi_axis = axes
    slices_dict = {'Sagittal': {'aspect': spacing_s / spacing_a, 'slice': slice_x, 'xlabel': 'A', 'ylabel': 'S', 'axis': sag_axis}, 'Coronal': {'aspect': spacing_s / spacing_r, 'slice': slice_y, 'xlabel': 'R', 'ylabel': 'S', 'axis': cor_axis}, 'Axial': {'aspect': spacing_a / spacing_r, 'slice': slice_z, 'xlabel': 'R', 'ylabel': 'A', 'axis': axi_axis}}
    for axis_title, info in slices_dict.items():
        axis = info['axis']
        axis.imshow(info['slice'], aspect=info['aspect'], **imshow_kwargs)
        if xlabels:
            axis.set_xlabel(info['xlabel'])
        axis.set_ylabel(info['ylabel'])
        axis.invert_xaxis()
        axis.set_title(axis_title)
    plt.tight_layout()
    if title is not None:
        plt.suptitle(title)
    if output_path is not None and fig is not None:
        if savefig_kwargs is None:
            savefig_kwargs = {}
        fig.savefig(output_path, **savefig_kwargs)
    if show:
        plt.show()
    return fig

def plot_subject(subject: Subject, cmap_dict=None, show=True, output_path=None, figsize=None, clear_axes=True, **plot_volume_kwargs):
    _, plt = import_mpl_plt()
    num_images = len(subject)
    many_images = num_images > 2
    subplots_kwargs = {'figsize': figsize}
    try:
        if clear_axes:
            subject.check_consistent_spatial_shape()
            subplots_kwargs['sharex'] = 'row' if many_images else 'col'
            subplots_kwargs['sharey'] = 'row' if many_images else 'col'
    except RuntimeError:
        pass
    args = (3, num_images) if many_images else (num_images, 3)
    fig, axes = plt.subplots(*args, **subplots_kwargs)
    axes = axes.T if many_images else axes.reshape(-1, 3)
    iterable = enumerate(subject.get_images_dict(intensity_only=False).items())
    axes_names = ('sagittal', 'coronal', 'axial')
    for image_index, (name, image) in iterable:
        image_axes = axes[image_index]
        cmap = None
        if cmap_dict is not None and name in cmap_dict:
            cmap = cmap_dict[name]
        last_row = image_index == len(axes) - 1
        plot_volume(image, axes=image_axes, show=False, cmap=cmap, xlabels=last_row, **plot_volume_kwargs)
        for axis, axis_name in zip(image_axes, axes_names):
            axis.set_title(f'{name} ({axis_name})')
    plt.tight_layout()
    if output_path is not None:
        fig.savefig(output_path)
    if show:
        plt.show()

def plot_histogram(x: np.ndarray, show=True, **kwargs) -> None:
    _, plt = import_mpl_plt()
    plt.hist(x, bins=get_num_bins(x), **kwargs)
    plt.xlabel('Intensity')
    density = kwargs.pop('density', False)
    ylabel = 'Density' if density else 'Frequency'
    plt.ylabel(ylabel)
    if show:
        plt.show()

def color_labels(arrays, cmap_dict):
    results = []
    for slice_array in arrays:
        si, sj, _ = slice_array.shape
        rgb = np.zeros((si, sj, 3), dtype=np.uint8)
        for label, color in cmap_dict.items():
            if isinstance(color, str):
                mpl, _ = import_mpl_plt()
                color = mpl.colors.to_rgb(color)
                color = [255 * n for n in color]
            rgb[slice_array[..., 0] == label] = color
        results.append(rgb)
    return results

class Image(dict):
    """TorchIO image.

    For information about medical image orientation, check out `NiBabel docs`_,
    the `3D Slicer wiki`_, `Graham Wideman's website`_, `FSL docs`_ or
    `SimpleITK docs`_.

    Args:
        path: Path to a file or sequence of paths to files that can be read by
            :mod:`SimpleITK` or :mod:`nibabel`, or to a directory containing
            DICOM files. If :attr:`tensor` is given, the data in
            :attr:`path` will not be read.
            If a sequence of paths is given, data
            will be concatenated on the channel dimension so spatial
            dimensions must match.
        type: Type of image, such as :attr:`torchio.INTENSITY` or
            :attr:`torchio.LABEL`. This will be used by the transforms to
            decide whether to apply an operation, or which interpolation to use
            when resampling. For example, `preprocessing`_ and `augmentation`_
            intensity transforms will only be applied to images with type
            :attr:`torchio.INTENSITY`. Spatial transforms will be applied to
            all types, and nearest neighbor interpolation is always used to
            resample images with type :attr:`torchio.LABEL`.
            The type :attr:`torchio.SAMPLING_MAP` may be used with instances of
            :class:`~torchio.data.sampler.weighted.WeightedSampler`.
        tensor: If :attr:`path` is not given, :attr:`tensor` must be a 4D
            :class:`torch.Tensor` or NumPy array with dimensions
            :math:`(C, W, H, D)`.
        affine: :math:`4 \\times 4` matrix to convert voxel coordinates to world
            coordinates. If ``None``, an identity matrix will be used. See the
            `NiBabel docs on coordinates`_ for more information.
        check_nans: If ``True``, issues a warning if NaNs are found
            in the image. If ``False``, images will not be checked for the
            presence of NaNs.
        reader: Callable object that takes a path and returns a 4D tensor and a
            2D, :math:`4 \\times 4` affine matrix. This can be used if your data
            is saved in a custom format, such as ``.npy`` (see example below).
            If the affine matrix is ``None``, an identity matrix will be used.
        **kwargs: Items that will be added to the image dictionary, e.g.
            acquisition parameters or image ID.
        verify_path: If ``True``, the path will be checked to see if it exists. If
            ``False``, the path will not be verified. This is useful when it is
            expensive to check the path, e.g., when reading a large dataset from a
            mounted drive.

    TorchIO images are `lazy loaders`_, i.e. the data is only loaded from disk
    when needed.

    Example:
        >>> import torchio as tio
        >>> import numpy as np
        >>> image = tio.ScalarImage('t1.nii.gz')  # subclass of Image
        >>> image  # not loaded yet
        ScalarImage(path: t1.nii.gz; type: intensity)
        >>> times_two = 2 * image.data  # data is loaded and cached here
        >>> image
        ScalarImage(shape: (1, 256, 256, 176); spacing: (1.00, 1.00, 1.00); orientation: PIR+; memory: 44.0 MiB; type: intensity)
        >>> image.save('doubled_image.nii.gz')
        >>> def numpy_reader(path):
        ...     data = np.load(path).as_type(np.float32)
        ...     affine = np.eye(4)
        ...     return data, affine
        >>> image = tio.ScalarImage('t1.npy', reader=numpy_reader)

    .. _lazy loaders: https://en.wikipedia.org/wiki/Lazy_loading
    .. _preprocessing: https://docs.torchio.org/transforms/preprocessing.html#intensity
    .. _augmentation: https://docs.torchio.org/transforms/augmentation.html#intensity
    .. _NiBabel docs: https://nipy.org/nibabel/image_orientation.html
    .. _NiBabel docs on coordinates: https://nipy.org/nibabel/coordinate_systems.html#the-affine-matrix-as-a-transformation-between-spaces
    .. _3D Slicer wiki: https://www.slicer.org/wiki/Coordinate_systems
    .. _FSL docs: https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/Orientation%20Explained
    .. _SimpleITK docs: https://simpleitk.readthedocs.io/en/master/fundamentalConcepts.html
    .. _Graham Wideman's website: http://www.grahamwideman.com/gw/brain/orientation/orientterms.htm
    """

    def __init__(self, path: TypePath | Sequence[TypePath] | None=None, type: str | None=None, tensor: TypeData | None=None, affine: TypeData | None=None, check_nans: bool=False, reader: Callable[[TypePath], TypeDataAffine]=read_image, verify_path: bool=True, **kwargs: dict[str, Any]):
        self.check_nans = check_nans
        self.reader = reader
        if type is None:
            warnings.warn('Not specifying the image type is deprecated and will be mandatory in the future. You can probably use tio.ScalarImage or tio.LabelMap instead', FutureWarning, stacklevel=2)
            type = INTENSITY
        if path is None and tensor is None:
            raise ValueError('A value for path or tensor must be given')
        self._loaded = False
        tensor = self._parse_tensor(tensor)
        affine = self._parse_affine(affine)
        if tensor is not None:
            self.set_data(tensor)
            self.affine = affine
            self._loaded = True
        for key in PROTECTED_KEYS:
            if key in kwargs:
                message = f'Key "{key}" is reserved. Use a different one'
                raise ValueError(message)
        if 'channels_last' in kwargs:
            message = 'The "channels_last" keyword argument is deprecated after https://github.com/TorchIO-project/torchio/pull/685 and will be removed in the future'
            warnings.warn(message, FutureWarning, stacklevel=2)
        super().__init__(**kwargs)
        self.path = self._parse_path(path, verify=verify_path)
        self[PATH] = '' if self.path is None else str(self.path)
        self[STEM] = '' if self.path is None else get_stem(self.path)
        self[TYPE] = type

    def __repr__(self):
        properties = []
        properties.extend([f'shape: {self.shape}', f'spacing: {self.get_spacing_string()}', f'orientation: {self.orientation_str}+'])
        if self._loaded:
            properties.append(f'dtype: {self.data.type()}')
            natural = humanize.naturalsize(self.memory, binary=True)
            properties.append(f'memory: {natural}')
        else:
            properties.append(f'path: "{self.path}"')
        properties = '; '.join(properties)
        string = f'{self.__class__.__name__}({properties})'
        return string

    def __getitem__(self, item):
        if isinstance(item, (slice, int, tuple)):
            return self._crop_from_slices(item)
        if item in (DATA, AFFINE):
            if item not in self:
                self.load()
        return super().__getitem__(item)

    def __array__(self):
        return self.data.numpy()

    def __copy__(self):
        kwargs = {TYPE: self.type, PATH: self.path}
        if self._loaded:
            kwargs[TENSOR] = self.data
            kwargs[AFFINE] = self.affine
        for key, value in self.items():
            if key in PROTECTED_KEYS:
                continue
            kwargs[key] = value
        new_image_class = type(self)
        new_image = new_image_class(check_nans=self.check_nans, reader=self.reader, **kwargs)
        return new_image

    @property
    def data(self) -> torch.Tensor:
        """Tensor data (same as :class:`Image.tensor`)."""
        return self[DATA]

    @data.setter
    @deprecated(version='0.18.16', reason=deprecation_message)
    def data(self, tensor: TypeData):
        self.set_data(tensor)

    def set_data(self, tensor: TypeData):
        """Store a 4D tensor in the :attr:`data` key and attribute.

        Args:
            tensor: 4D tensor with dimensions :math:`(C, W, H, D)`.
        """
        self[DATA] = self._parse_tensor(tensor, none_ok=False)
        self._loaded = True

    @property
    def tensor(self) -> torch.Tensor:
        """Tensor data (same as :class:`Image.data`)."""
        return self.data

    @property
    def affine(self) -> np.ndarray:
        """Affine matrix to transform voxel indices into world coordinates."""
        is_custom_reader = self.reader is not read_image
        if self._loaded or self._is_dir() or self._is_multipath() or is_custom_reader:
            affine = self[AFFINE]
        else:
            assert self.path is not None
            assert isinstance(self.path, (str, Path))
            affine = read_affine(self.path)
        return affine

    @affine.setter
    def affine(self, matrix):
        self[AFFINE] = self._parse_affine(matrix)

    @property
    def type(self) -> str:
        return self[TYPE]

    @property
    def shape(self) -> TypeQuartetInt:
        """Tensor shape as :math:`(C, W, H, D)`."""
        custom_reader = self.reader is not read_image
        multipath = self._is_multipath()
        if isinstance(self.path, Path):
            is_dir = self.path.is_dir()
        shape: TypeQuartetInt
        if self._loaded or custom_reader or multipath or is_dir:
            channels, si, sj, sk = self.data.shape
            shape = (channels, si, sj, sk)
        else:
            assert isinstance(self.path, (str, Path))
            shape = read_shape(self.path)
        return shape

    @property
    def spatial_shape(self) -> TypeTripletInt:
        """Tensor spatial shape as :math:`(W, H, D)`."""
        return self.shape[1:]

    def check_is_2d(self) -> None:
        if not self.is_2d():
            message = f'Image is not 2D. Spatial shape: {self.spatial_shape}'
            raise RuntimeError(message)

    @property
    def height(self) -> int:
        """Image height, if 2D."""
        self.check_is_2d()
        return self.spatial_shape[1]

    @property
    def width(self) -> int:
        """Image width, if 2D."""
        self.check_is_2d()
        return self.spatial_shape[0]

    @property
    def orientation(self) -> tuple[str, str, str]:
        """Orientation codes."""
        return nib.orientations.aff2axcodes(self.affine)

    @property
    def orientation_str(self) -> str:
        """Orientation as a string."""
        return ''.join(self.orientation)

    @property
    def direction(self) -> TypeDirection3D:
        _, _, direction = get_sitk_metadata_from_ras_affine(self.affine, lps=False)
        return direction

    @property
    def spacing(self) -> tuple[float, float, float]:
        """Voxel spacing in mm."""
        _, spacing = get_rotation_and_spacing_from_affine(self.affine)
        sx, sy, sz = spacing
        return (float(sx), float(sy), float(sz))

    @property
    def origin(self) -> tuple[float, float, float]:
        """Center of first voxel in array, in mm."""
        ox, oy, oz = self.affine[:3, 3]
        return (ox, oy, oz)

    @property
    def itemsize(self):
        """Element size of the data type."""
        return self.data.element_size()

    @property
    def memory(self) -> float:
        """Number of Bytes that the tensor takes in the RAM."""
        return np.prod(self.shape) * self.itemsize

    @property
    def bounds(self) -> np.ndarray:
        """Position of centers of voxels in smallest and largest indices."""
        ini = (0, 0, 0)
        fin = np.array(self.spatial_shape) - 1
        point_ini = apply_affine(self.affine, ini)
        point_fin = apply_affine(self.affine, fin)
        return np.array((point_ini, point_fin))

    @property
    def num_channels(self) -> int:
        """Get the number of channels in the associated 4D tensor."""
        return len(self.data)

    def axis_name_to_index(self, axis: str) -> int:
        """Convert an axis name to an axis index.

        Args:
            axis: Possible inputs are ``'Left'``, ``'Right'``, ``'Anterior'``,
                ``'Posterior'``, ``'Inferior'``, ``'Superior'``. Lower-case
                versions and first letters are also valid, as only the first
                letter will be used.

        .. note:: If you are working with animals, you should probably use
            ``'Superior'``, ``'Inferior'``, ``'Anterior'`` and ``'Posterior'``
            for ``'Dorsal'``, ``'Ventral'``, ``'Rostral'`` and ``'Caudal'``,
            respectively.

        .. note:: If your images are 2D, you can use ``'Top'``, ``'Bottom'``,
            ``'Left'`` and ``'Right'``.
        """
        if not isinstance(axis, str):
            raise ValueError('Axis must be a string')
        axis = axis[0].upper()
        if axis in 'TB':
            return -2
        else:
            try:
                index = self.orientation.index(axis)
            except ValueError:
                index = self.orientation.index(self.flip_axis(axis))
            index = -3 + index
            return index

    @staticmethod
    def flip_axis(axis: str) -> str:
        """Return the opposite axis label. For example, ``'L'`` -> ``'R'``.

        Args:
            axis: Axis label, such as ``'L'`` or ``'left'``.
        """
        labels = 'LRPAISTBDV'
        first = labels[::2]
        last = labels[1::2]
        flip_dict = dict(zip(first + last, last + first))
        axis = axis[0].upper()
        flipped_axis = flip_dict.get(axis)
        if flipped_axis is None:
            values = ', '.join(labels)
            message = f'Axis not understood. Please use one of: {values}'
            raise ValueError(message)
        return flipped_axis

    def get_spacing_string(self) -> str:
        strings = [f'{n:.2f}' for n in self.spacing]
        string = f'({', '.join(strings)})'
        return string

    def get_bounds(self) -> TypeBounds:
        """Get minimum and maximum world coordinates occupied by the image."""
        first_index = 3 * (-0.5,)
        last_index = np.array(self.spatial_shape) - 0.5
        first_point = apply_affine(self.affine, first_index)
        last_point = apply_affine(self.affine, last_index)
        array = np.array((first_point, last_point))
        bounds_x, bounds_y, bounds_z = array.T.tolist()
        return (bounds_x, bounds_y, bounds_z)

    def _parse_single_path(self, path: TypePath, *, verify: bool=True) -> Path:
        if isinstance(path, (torch.Tensor, np.ndarray)):
            class_name = self.__class__.__name__
            message = f'Expected type str or Path but found a tensor/array. Instead of {class_name}(your_tensor), use {class_name}(tensor=your_tensor).'
            raise TypeError(message)
        try:
            path = Path(path).expanduser()
        except TypeError as err:
            message = f'Expected type str or Path but found an object with type {type(path)} instead'
            raise TypeError(message) from err
        except RuntimeError as err:
            message = f'Conversion to path not possible for variable: {path}'
            raise RuntimeError(message) from err
        if not verify:
            return path
        if not (path.is_file() or path.is_dir()):
            raise FileNotFoundError(f'File not found: "{path}"')
        return path

    def _parse_path(self, path: TypePath | Sequence[TypePath] | None, *, verify: bool=True) -> Path | list[Path] | None:
        if path is None:
            return None
        elif isinstance(path, dict):
            raise TypeError('The path argument cannot be a dictionary')
        elif self._is_paths_sequence(path):
            return [self._parse_single_path(p, verify=verify) for p in path]
        else:
            return self._parse_single_path(path, verify=verify)

    def _parse_tensor(self, tensor: TypeData | None, none_ok: bool=True) -> torch.Tensor | None:
        if tensor is None:
            if none_ok:
                return None
            else:
                raise RuntimeError('Input tensor cannot be None')
        if isinstance(tensor, np.ndarray):
            tensor = check_uint_to_int(tensor)
            tensor = torch.as_tensor(tensor)
        elif not isinstance(tensor, torch.Tensor):
            message = f'Input tensor must be a PyTorch tensor or NumPy array, but type "{type(tensor)}" was found'
            raise TypeError(message)
        ndim = tensor.ndim
        if ndim != 4:
            raise ValueError(f'Input tensor must be 4D, but it is {ndim}D')
        if tensor.dtype == torch.bool:
            tensor = tensor.to(torch.uint8)
        if self.check_nans and torch.isnan(tensor).any():
            warnings.warn('NaNs found in tensor', RuntimeWarning, stacklevel=2)
        return tensor

    @staticmethod
    def _parse_tensor_shape(tensor: torch.Tensor) -> TypeData:
        return ensure_4d(tensor)

    @staticmethod
    def _parse_affine(affine: TypeData | None) -> np.ndarray:
        if affine is None:
            return np.eye(4)
        if isinstance(affine, torch.Tensor):
            affine = affine.numpy()
        if not isinstance(affine, np.ndarray):
            bad_type = type(affine)
            raise TypeError(f'Affine must be a NumPy array, not {bad_type}')
        if affine.shape != (4, 4):
            bad_shape = affine.shape
            raise ValueError(f'Affine shape must be (4, 4), not {bad_shape}')
        return affine.astype(np.float64)

    @staticmethod
    def _is_paths_sequence(path: TypePath | Sequence[TypePath] | None) -> bool:
        is_not_string = not isinstance(path, str)
        return is_not_string and is_iterable(path)

    def _is_multipath(self) -> bool:
        return self._is_paths_sequence(self.path)

    def _is_dir(self) -> bool:
        is_sequence = self._is_multipath()
        if is_sequence:
            return False
        elif self.path is None:
            return False
        else:
            assert isinstance(self.path, Path)
            return self.path.is_dir()

    def load(self) -> None:
        """Load the image from disk.

        Returns:
            Tuple containing a 4D tensor of size :math:`(C, W, H, D)` and a 2D
            :math:`4 \\times 4` affine matrix to convert voxel indices to world
            coordinates.
        """
        if self._loaded:
            return
        paths: list[Path]
        if self._is_multipath():
            paths = self.path
        else:
            paths = [self.path]
        tensor, affine = self.read_and_check(paths[0])
        tensors = [tensor]
        for path in paths[1:]:
            new_tensor, new_affine = self.read_and_check(path)
            if not np.array_equal(affine, new_affine):
                message = f'Files have different affine matrices.\nMatrix of {paths[0]}:\n{affine}\nMatrix of {path}:\n{new_affine}'
                warnings.warn(message, RuntimeWarning, stacklevel=2)
            if not tensor.shape[1:] == new_tensor.shape[1:]:
                message = f'Files shape do not match, found {tensor.shape}and {new_tensor.shape}'
                raise RuntimeError(message)
            tensors.append(new_tensor)
        tensor = torch.cat(tensors)
        self.set_data(tensor)
        self.affine = affine
        self._loaded = True

    def unload(self) -> None:
        """Unload the image from memory.

        Raises:
            RuntimeError: If the images has not been loaded yet or if no path
                is available.
        """
        if not self._loaded:
            message = 'Image cannot be unloaded as it has not been loaded yet'
            raise RuntimeError(message)
        if self.path is None:
            message = 'Cannot unload image as no path is available from where the image could be loaded again'
            raise RuntimeError(message)
        self[DATA] = None
        self[AFFINE] = None
        self._loaded = False

    def read_and_check(self, path: TypePath) -> TypeDataAffine:
        tensor, affine = self.reader(path)
        if self.reader is not read_image and isinstance(tensor, np.ndarray):
            tensor = check_uint_to_int(tensor)
        tensor = self._parse_tensor_shape(tensor)
        tensor = self._parse_tensor(tensor)
        affine = self._parse_affine(affine)
        if self.check_nans and torch.isnan(tensor).any():
            warnings.warn(f'NaNs found in file "{path}"', RuntimeWarning, stacklevel=2)
        return (tensor, affine)

    def save(self, path: TypePath, squeeze: bool | None=None) -> None:
        """Save image to disk.

        Args:
            path: String or instance of :class:`pathlib.Path`.
            squeeze: Whether to remove singleton dimensions before saving.
                If ``None``, the array will be squeezed if the output format is
                JP(E)G, PNG, BMP or TIF(F).
        """
        write_image(self.data, self.affine, path, squeeze=squeeze)

    def is_2d(self) -> bool:
        return self.shape[-1] == 1

    def numpy(self) -> np.ndarray:
        """Get a NumPy array containing the image data."""
        return np.asarray(self)

    def as_sitk(self, **kwargs) -> sitk.Image:
        """Get the image as an instance of :class:`sitk.Image`."""
        return nib_to_sitk(self.data, self.affine, **kwargs)

    @classmethod
    def from_sitk(cls, sitk_image):
        """Instantiate a new TorchIO image from a :class:`sitk.Image`.

        Example:
            >>> import torchio as tio
            >>> import SimpleITK as sitk
            >>> sitk_image = sitk.Image(20, 30, 40, sitk.sitkUInt16)
            >>> tio.LabelMap.from_sitk(sitk_image)
            LabelMap(shape: (1, 20, 30, 40); spacing: (1.00, 1.00, 1.00); orientation: LPS+; memory: 93.8 KiB; dtype: torch.IntTensor)
            >>> sitk_image = sitk.Image((224, 224), sitk.sitkVectorFloat32, 3)
            >>> tio.ScalarImage.from_sitk(sitk_image)
            ScalarImage(shape: (3, 224, 224, 1); spacing: (1.00, 1.00, 1.00); orientation: LPS+; memory: 588.0 KiB; dtype: torch.FloatTensor)
        """
        tensor, affine = sitk_to_nib(sitk_image)
        return cls(tensor=tensor, affine=affine)

    def as_pil(self, transpose=True):
        """Get the image as an instance of :class:`PIL.Image`.

        .. note:: Values will be clamped to 0-255 and cast to uint8.

        .. note:: To use this method, Pillow needs to be installed:
            ``pip install Pillow``.
        """
        try:
            from PIL import Image as ImagePIL
        except ModuleNotFoundError as e:
            message = 'Please install Pillow to use Image.as_pil(): pip install Pillow'
            raise RuntimeError(message) from e
        self.check_is_2d()
        tensor = self.data
        if len(tensor) not in (1, 3, 4):
            raise NotImplementedError('Only 1, 3 or 4 channels are supported for conversion to Pillow image')
        if len(tensor) == 1:
            tensor = torch.cat(3 * [tensor])
        if transpose:
            tensor = tensor.permute(3, 2, 1, 0)
        else:
            tensor = tensor.permute(3, 1, 2, 0)
        array = tensor.clamp(0, 255).numpy()[0]
        return ImagePIL.fromarray(array.astype(np.uint8))

    def to_gif(self, axis: int, duration: float, output_path: TypePath, loop: int=0, rescale: bool=True, optimize: bool=True, reverse: bool=False) -> None:
        """Save an animated GIF of the image.

        Args:
            axis: Spatial axis (0, 1 or 2).
            duration: Duration of the full animation in seconds.
            output_path: Path to the output GIF file.
            loop: Number of times the GIF should loop.
                ``0`` means that it will loop forever.
            rescale: Use :class:`~torchio.transforms.preprocessing.intensity.rescale.RescaleIntensity`
                to rescale the intensity values to :math:`[0, 255]`.
            optimize: If ``True``, attempt to compress the palette by
                eliminating unused colors. This is only useful if the palette
                can be compressed to the next smaller power of 2 elements.
            reverse: Reverse the temporal order of frames.
        """
        from ..visualization import make_gif
        make_gif(self.data, axis, duration, output_path, loop=loop, rescale=rescale, optimize=optimize, reverse=reverse)

    def to_ras(self) -> Image:
        if self.orientation_str != 'RAS':
            from ..transforms.preprocessing.spatial.to_canonical import ToCanonical
            return ToCanonical()(self)
        return self

    def get_center(self, lps: bool=False) -> TypeTripletFloat:
        """Get image center in RAS+ or LPS+ coordinates.

        Args:
            lps: If ``True``, the coordinates will be in LPS+ orientation, i.e.
                the first dimension grows towards the left, etc. Otherwise, the
                coordinates will be in RAS+ orientation.
        """
        size = np.array(self.spatial_shape)
        center_index = (size - 1) / 2
        r, a, s = apply_affine(self.affine, center_index)
        if lps:
            return (-r, -a, s)
        else:
            return (r, a, s)

    def set_check_nans(self, check_nans: bool) -> None:
        self.check_nans = check_nans

    def plot(self, **kwargs) -> None:
        """Plot image."""
        if self.is_2d():
            self.as_pil().show()
        else:
            from ..visualization import plot_volume
            plot_volume(self, **kwargs)

    def show(self, viewer_path: TypePath | None=None) -> None:
        """Open the image using external software.

        Args:
            viewer_path: Path to the application used to view the image. If
                ``None``, the value of the environment variable
                ``SITK_SHOW_COMMAND`` will be used. If this variable is also
                not set, TorchIO will try to guess the location of
                `ITK-SNAP <http://www.itksnap.org/pmwiki/pmwiki.php>`_ and
                `3D Slicer <https://www.slicer.org/>`_.

        Raises:
            RuntimeError: If the viewer is not found.
        """
        sitk_image = self.as_sitk()
        image_viewer = sitk.ImageViewer()
        if self.__class__.__name__ == 'LabelMap':
            image_viewer.SetFileExtension('.seg.nrrd')
        if viewer_path is not None:
            image_viewer.SetApplication(str(viewer_path))
        try:
            image_viewer.Execute(sitk_image)
        except RuntimeError as e:
            viewer_path = guess_external_viewer()
            if viewer_path is None:
                message = 'No external viewer has been found. Please set the environment variable SITK_SHOW_COMMAND to a viewer of your choice'
                raise RuntimeError(message) from e
            image_viewer.SetApplication(str(viewer_path))
            image_viewer.Execute(sitk_image)

    def _crop_from_slices(self, slices: TypeSlice | tuple[TypeSlice, ...]) -> Image:
        from ..transforms import Crop
        slices_tuple = to_tuple(slices)
        cropping: list[int] = []
        for dim, slice_ in enumerate(slices_tuple):
            if isinstance(slice_, slice):
                pass
            elif slice_ is Ellipsis:
                message = 'Ellipsis slicing is not supported yet'
                raise NotImplementedError(message)
            elif isinstance(slice_, int):
                slice_ = slice(slice_, slice_ + 1)
            else:
                message = f'Slice type not understood: "{type(slice_)}"'
                raise TypeError(message)
            shape_dim = self.spatial_shape[dim]
            assert isinstance(slice_, slice)
            start, stop, step = slice_.indices(shape_dim)
            if step != 1:
                message = 'Slicing with steps different from 1 is not supported yet. Use the Crop transform instead'
                raise ValueError(message)
            crop_ini = start
            crop_fin = shape_dim - stop
            cropping.extend([crop_ini, crop_fin])
        while dim < 2:
            cropping.extend([0, 0])
            dim += 1
        w_ini, w_fin, h_ini, h_fin, d_ini, d_fin = cropping
        cropping_arg = (w_ini, w_fin, h_ini, h_fin, d_ini, d_fin)
        return Crop(cropping_arg)(self)

def plot(self, **kwargs) -> None:
    """Plot image."""
    if self.is_2d():
        self.as_pil().show()
    else:
        from ..visualization import plot_volume
        plot_volume(self, **kwargs)

class EPISURG(SubjectsDataset):
    """
    `EPISURG <https://doi.org/10.5522/04/9996158.v1>`_ is a clinical dataset of
    :math:`T_1`-weighted MRI from 430 epileptic patients who underwent
    resective brain surgery at the National Hospital of Neurology and
    Neurosurgery (Queen Square, London, United Kingdom) between 1990 and 2018.

    The dataset comprises 430 postoperative MRI. The corresponding preoperative
    MRI is present for 268 subjects.

    Three human raters segmented the resection cavity on partially overlapping
    subsets of EPISURG.

    If you use this dataset for your research, you agree with the *Data use
    agreement* presented at the EPISURG entry on the `UCL Research Data
    Repository <https://doi.org/10.5522/04/9996158.v1>`_ and you must cite the
    corresponding publications.

    Args:
        root: Root directory to which the dataset will be downloaded.
        transform: An instance of
            :class:`~torchio.transforms.transform.Transform`.
        download: If set to ``True``, will download the data into :attr:`root`.

    .. warning:: The size of this dataset is multiple GB.
        If you set :attr:`download` to ``True``, it will take some time
        to be downloaded if it is not already present.
    """
    data_url = 'https://s3-eu-west-1.amazonaws.com/pstorage-ucl-2748466690/26153588/EPISURG.zip'
    md5 = '5ec5831a2c6fbfdc8489ba2910a6504b'

    def __init__(self, root: TypePath, transform: Transform | None=None, download: bool=False, **kwargs):
        root = Path(root).expanduser().absolute()
        if download:
            self._download(root)
        subjects_list = self._get_subjects_list(root)
        self.kwargs = kwargs
        super().__init__(subjects_list, transform=transform, **kwargs)

    @staticmethod
    def _check_exists(root, modalities):
        for modality in modalities:
            modality_dir = root / modality
            if not modality_dir.is_dir():
                exists = False
                break
        else:
            exists = True
        return exists

    @staticmethod
    def _get_subjects_list(root):
        episurg_dir = root / 'EPISURG'
        subjects_dir = episurg_dir / 'subjects'
        csv_path = episurg_dir / 'subjects.csv'
        with open(csv_path) as csvfile:
            reader = csv.DictReader(csvfile)
            subjects = []
            for row in reader:
                subject_id = row['Subject']
                subject_dir = subjects_dir / subject_id
                subject_dict = {'subject_id': subject_id, 'hemisphere': row['Hemisphere'], 'surgery_type': row['Type']}
                preop_dir = subject_dir / 'preop'
                preop_paths = list(preop_dir.glob('*preop*'))
                assert len(preop_paths) <= 1
                if preop_paths:
                    subject_dict['preop_mri'] = ScalarImage(preop_paths[0])
                postop_dir = subject_dir / 'postop'
                postop_path = list(postop_dir.glob('*postop-t1mri*'))[0]
                subject_dict['postop_mri'] = ScalarImage(postop_path)
                for seg_path in postop_dir.glob('*seg*'):
                    seg_id = seg_path.name[-8]
                    subject_dict[f'seg_{seg_id}'] = LabelMap(seg_path)
                subjects.append(Subject(**subject_dict))
        return subjects

    def _download(self, root: Path):
        """Download the EPISURG data if it does not exist already."""
        if (root / 'EPISURG').is_dir():
            return
        root.mkdir(exist_ok=True, parents=True)
        download_and_extract_archive(self.data_url, download_root=root, md5=self.md5)
        (root / 'EPISURG.zip').unlink()

    def _glob_subjects(self, string):
        subjects = []
        for subject in self._subjects:
            for image_name in subject:
                if string in image_name:
                    subjects.append(subject)
                    break
        return subjects

    def _get_labeled_subjects(self):
        return self._glob_subjects('seg')

    def _get_paired_subjects(self):
        return self._glob_subjects('preop')

    def _get_subset(self, subjects):
        dataset = SubjectsDataset(subjects, transform=self._transform, **self.kwargs)
        return dataset

    def get_labeled(self) -> SubjectsDataset:
        """Get dataset from subjects with manual annotations."""
        return self._get_subset(self._get_labeled_subjects())

    def get_unlabeled(self) -> SubjectsDataset:
        """Get dataset from subjects without manual annotations."""
        subjects = [s for s in self._subjects if s not in self._get_labeled_subjects()]
        return self._get_subset(subjects)

    def get_paired(self) -> SubjectsDataset:
        """Get dataset from subjects with pre- and post-op MRI."""
        return self._get_subset(self._get_paired_subjects())

def _get_subset(self, subjects):
    dataset = SubjectsDataset(subjects, transform=self._transform, **self.kwargs)
    return dataset

def mask(tensor: torch.Tensor, mask: torch.Tensor, outside_value: float) -> torch.Tensor:
    array = tensor.clone()
    num_channels_array = array.shape[0]
    num_channels_mask = mask.shape[0]
    if num_channels_array != num_channels_mask:
        assert num_channels_mask == 1
        message = f'Expanding mask with shape {mask.shape} to match shape {array.shape} of input image'
        warnings.warn(message, RuntimeWarning, stacklevel=2)
        mask = mask.expand(*array.shape)
    array[~mask] = outside_value
    return array

class TestUtils(TorchioTestCase):
    """Tests for `utils` module."""

    def test_to_tuple(self):
        assert tio.utils.to_tuple(1) == (1,)
        assert tio.utils.to_tuple((1,)) == (1,)
        assert tio.utils.to_tuple(1, length=3) == (1, 1, 1)
        assert tio.utils.to_tuple((1, 2)) == (1, 2)
        assert tio.utils.to_tuple((1, 2), length=3) == (1, 2)
        assert tio.utils.to_tuple([1, 2], length=3) == (1, 2)

    def test_get_stem(self):
        assert tio.utils.get_stem('/home/image.nii.gz') == 'image'
        assert tio.utils.get_stem('/home/image.nii') == 'image'
        assert tio.utils.get_stem('/home/image.nrrd') == 'image'

    def test_guess_type(self):
        assert tio.utils.guess_type('None') is None
        assert isinstance(tio.utils.guess_type('1'), int)
        assert isinstance(tio.utils.guess_type('1.5'), float)
        assert isinstance(tio.utils.guess_type('(1, 3, 5)'), tuple)
        assert isinstance(tio.utils.guess_type('(1,3,5)'), tuple)
        assert isinstance(tio.utils.guess_type('[1,3,5]'), list)
        assert isinstance(tio.utils.guess_type('test'), str)

    def test_apply_transform_to_file(self):
        transform = tio.RandomFlip()
        tio.utils.apply_transform_to_file(self.get_image_path('input'), transform, self.get_image_path('output'), verbose=True)

    def test_subjects_from_batch(self):
        dataset = tio.SubjectsDataset(4 * [self.sample_subject])
        loader = tio.SubjectsLoader(dataset, batch_size=4)
        batch = tio.utils.get_first_item(loader)
        subjects = tio.utils.get_subjects_from_batch(batch)
        assert isinstance(subjects[0], tio.Subject)

    def test_subjects_from_batch_with_string_metadata(self):
        subject_c_with_string_metadata = tio.Subject(name='John Doe', label=tio.LabelMap(self.get_image_path('label_c', binary=True)))
        dataset = tio.SubjectsDataset(4 * [subject_c_with_string_metadata])
        loader = tio.SubjectsLoader(dataset, batch_size=4)
        batch = tio.utils.get_first_item(loader)
        subjects = tio.utils.get_subjects_from_batch(batch)
        assert isinstance(subjects[0], tio.Subject)
        assert 'label' in subjects[0]
        assert 'name' in subjects[0]

    def test_subjects_from_batch_with_int_metadata(self):
        subject_c_with_int_metadata = tio.Subject(age=45, label=tio.LabelMap(self.get_image_path('label_c', binary=True)))
        dataset = tio.SubjectsDataset(4 * [subject_c_with_int_metadata])
        loader = tio.SubjectsLoader(dataset, batch_size=4)
        batch = tio.utils.get_first_item(loader)
        subjects = tio.utils.get_subjects_from_batch(batch)
        assert isinstance(subjects[0], tio.Subject)
        assert 'label' in subjects[0]
        assert 'age' in subjects[0]

    def test_add_images_from_batch(self):
        subject = copy.deepcopy(self.sample_subject)
        subjects = 4 * [subject]
        preds = torch.rand(4, *subject.shape)
        tio.utils.add_images_from_batch(subjects, preds)

    def test_empty_batch(self):
        with pytest.raises(RuntimeError):
            tio.utils.get_batch_images_and_size({})

def test_subjects_from_batch(self):
    dataset = tio.SubjectsDataset(4 * [self.sample_subject])
    loader = tio.SubjectsLoader(dataset, batch_size=4)
    batch = tio.utils.get_first_item(loader)
    subjects = tio.utils.get_subjects_from_batch(batch)
    assert isinstance(subjects[0], tio.Subject)

def test_subjects_from_batch_with_string_metadata(self):
    subject_c_with_string_metadata = tio.Subject(name='John Doe', label=tio.LabelMap(self.get_image_path('label_c', binary=True)))
    dataset = tio.SubjectsDataset(4 * [subject_c_with_string_metadata])
    loader = tio.SubjectsLoader(dataset, batch_size=4)
    batch = tio.utils.get_first_item(loader)
    subjects = tio.utils.get_subjects_from_batch(batch)
    assert isinstance(subjects[0], tio.Subject)
    assert 'label' in subjects[0]
    assert 'name' in subjects[0]

def test_subjects_from_batch_with_int_metadata(self):
    subject_c_with_int_metadata = tio.Subject(age=45, label=tio.LabelMap(self.get_image_path('label_c', binary=True)))
    dataset = tio.SubjectsDataset(4 * [subject_c_with_int_metadata])
    loader = tio.SubjectsLoader(dataset, batch_size=4)
    batch = tio.utils.get_first_item(loader)
    subjects = tio.utils.get_subjects_from_batch(batch)
    assert isinstance(subjects[0], tio.Subject)
    assert 'label' in subjects[0]
    assert 'age' in subjects[0]

class TestSubjectsDataset(TorchioTestCase):

    def test_indexing_nonint(self):
        dset = tio.SubjectsDataset(self.subjects_list)
        dset[torch.tensor(0)]

    def test_images(self):
        self.iterate_dataset(self.subjects_list)

    def test_empty_subjects_list(self):
        with pytest.raises(ValueError):
            self.iterate_dataset([])

    def test_empty_subjects_tuple(self):
        with pytest.raises(ValueError):
            self.iterate_dataset(())

    def test_wrong_subjects_type(self):
        with pytest.raises(TypeError):
            self.iterate_dataset(0)

    def test_wrong_subject_type_int(self):
        with pytest.raises(TypeError):
            self.iterate_dataset([0])

    def test_wrong_subject_type_dict(self):
        with pytest.raises(TypeError):
            self.iterate_dataset([{}])

    def test_wrong_index(self):
        with pytest.raises(ValueError):
            self.dataset[:3]

    def test_wrong_transform_init(self):
        with pytest.raises(ValueError):
            tio.SubjectsDataset(self.subjects_list, transform={})

    def test_wrong_transform_arg(self):
        with pytest.raises(ValueError):
            self.dataset.set_transform(1)

    @staticmethod
    def iterate_dataset(subjects_list):
        dataset = tio.SubjectsDataset(subjects_list)
        for _ in dataset:
            pass

    def test_from_batch(self):
        dataset = tio.SubjectsDataset([self.sample_subject])
        loader = tio.SubjectsLoader(dataset)
        batch = tio.utils.get_first_item(loader)
        new_dataset = tio.SubjectsDataset.from_batch(batch)
        self.assert_tensor_equal(dataset[0].t1.data, new_dataset[0].t1.data)

def test_wrong_transform_init(self):
    with pytest.raises(ValueError):
        tio.SubjectsDataset(self.subjects_list, transform={})

@staticmethod
def iterate_dataset(subjects_list):
    dataset = tio.SubjectsDataset(subjects_list)
    for _ in dataset:
        pass

def test_from_batch(self):
    dataset = tio.SubjectsDataset([self.sample_subject])
    loader = tio.SubjectsLoader(dataset)
    batch = tio.utils.get_first_item(loader)
    new_dataset = tio.SubjectsDataset.from_batch(batch)
    self.assert_tensor_equal(dataset[0].t1.data, new_dataset[0].t1.data)

class TestQueue(TorchioTestCase):
    """Tests for `queue` module."""

    def setUp(self):
        super().setUp()
        self.subjects_list = create_dummy_dataset(num_images=10, size_range=(10, 20), directory=self.dir, suffix='.nii', force=False)

    def run_queue(self, num_workers=0, **kwargs):
        subjects_dataset = tio.SubjectsDataset(self.subjects_list)
        patch_size = 10
        sampler = UniformSampler(patch_size)
        queue_dataset = tio.Queue(subjects_dataset, max_length=6, samples_per_volume=2, sampler=sampler, num_workers=num_workers, **kwargs)
        _ = str(queue_dataset)
        batch_loader = tio.SubjectsLoader(queue_dataset, batch_size=4)
        for batch in batch_loader:
            _ = batch['one_modality'][tio.DATA]
            _ = batch['segmentation'][tio.DATA]
        return queue_dataset

    def test_queue(self):
        self.run_queue(num_workers=0)

    @pytest.mark.skipif(sys.platform == 'darwin', reason='Takes too long on macOS')
    def test_queue_multiprocessing(self):
        self.run_queue(num_workers=2)

    def test_queue_no_start_background(self):
        self.run_queue(num_workers=0, start_background=False)

    @parameterized.expand([(11,), (12,)])
    def test_different_samples_per_volume(self, max_length):
        image2 = tio.ScalarImage(tensor=2 * torch.ones(1, 1, 1, 1))
        image10 = tio.ScalarImage(tensor=10 * torch.ones(1, 1, 1, 1))
        subject2 = tio.Subject(im=image2, num_samples=2)
        subject10 = tio.Subject(im=image10, num_samples=10)
        dataset = tio.SubjectsDataset([subject2, subject10])
        patch_size = 1
        sampler = UniformSampler(patch_size)
        queue_dataset = tio.Queue(dataset, max_length=max_length, samples_per_volume=3, sampler=sampler, shuffle_patches=False)
        batch_loader = tio.SubjectsLoader(queue_dataset, batch_size=6)
        tensors = [batch['im'][tio.DATA] for batch in batch_loader]
        all_numbers = torch.stack(tensors).flatten().tolist()
        assert all_numbers.count(10) == 10
        assert all_numbers.count(2) == 2

    def test_get_memory_string(self):
        queue = self.run_queue()
        memory_string = queue.get_max_memory_pretty()
        assert isinstance(memory_string, str)

def run_queue(self, num_workers=0, **kwargs):
    subjects_dataset = tio.SubjectsDataset(self.subjects_list)
    patch_size = 10
    sampler = UniformSampler(patch_size)
    queue_dataset = tio.Queue(subjects_dataset, max_length=6, samples_per_volume=2, sampler=sampler, num_workers=num_workers, **kwargs)
    _ = str(queue_dataset)
    batch_loader = tio.SubjectsLoader(queue_dataset, batch_size=4)
    for batch in batch_loader:
        _ = batch['one_modality'][tio.DATA]
        _ = batch['segmentation'][tio.DATA]
    return queue_dataset

@parameterized.expand([(11,), (12,)])
def test_different_samples_per_volume(self, max_length):
    image2 = tio.ScalarImage(tensor=2 * torch.ones(1, 1, 1, 1))
    image10 = tio.ScalarImage(tensor=10 * torch.ones(1, 1, 1, 1))
    subject2 = tio.Subject(im=image2, num_samples=2)
    subject10 = tio.Subject(im=image10, num_samples=10)
    dataset = tio.SubjectsDataset([subject2, subject10])
    patch_size = 1
    sampler = UniformSampler(patch_size)
    queue_dataset = tio.Queue(dataset, max_length=max_length, samples_per_volume=3, sampler=sampler, shuffle_patches=False)
    batch_loader = tio.SubjectsLoader(queue_dataset, batch_size=6)
    tensors = [batch['im'][tio.DATA] for batch in batch_loader]
    all_numbers = torch.stack(tensors).flatten().tolist()
    assert all_numbers.count(10) == 10
    assert all_numbers.count(2) == 2

class TestSubject(TorchioTestCase):
    """Tests for `Subject`."""

    def test_positional_args(self):
        with pytest.raises(ValueError):
            tio.Subject(0)

    def test_input_dict(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            input_dict = {'image': tio.ScalarImage(f.name)}
            tio.Subject(input_dict)
            tio.Subject(**input_dict)

    def test_no_sample(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            input_dict = {'image': tio.ScalarImage(f.name)}
            subject = tio.Subject(input_dict)
            with pytest.raises(RuntimeError):
                with pytest.warns(UserWarning):
                    tio.RandomFlip()(subject)

    def test_history(self):
        transformed = tio.RandomGamma()(self.sample_subject)
        assert len(transformed.history) == 1

    def test_inconsistent_shape(self):
        subject = tio.Subject(a=tio.ScalarImage(tensor=torch.rand(1, 2, 3, 4)), b=tio.ScalarImage(tensor=torch.rand(2, 2, 3, 4)))
        _ = subject.spatial_shape
        with pytest.raises(RuntimeError):
            _ = subject.shape

    def test_inconsistent_spatial_shape(self):
        subject = tio.Subject(a=tio.ScalarImage(tensor=torch.rand(1, 3, 3, 4)), b=tio.ScalarImage(tensor=torch.rand(2, 2, 3, 4)))
        with pytest.raises(RuntimeError):
            _ = subject.spatial_shape

    @pytest.mark.slow
    @pytest.mark.skipif(sys.platform == 'win32', reason='Unstable on Windows')
    def test_plot(self):
        self.sample_subject.plot(show=False, output_path=self.dir / 'figure.png', cmap_dict={'t2': 'viridis', 'label': {0: 'yellow', 1: 'blue'}})

    @pytest.mark.slow
    @pytest.mark.skipif(sys.platform == 'win32', reason='Unstable on Windows')
    def test_plot_one_image(self):
        path = self.get_image_path('t1_plot')
        subject = tio.Subject(t1=tio.ScalarImage(path))
        subject.plot(show=False)

    def test_same_space(self):
        affine1 = np.array([[4.27109375e-14, -0.00871264808, 0.999876633, -33.9850907], [-0.5546875, -2.71630469e-12, 8.75148028e-17, 162.28293], [2.71575e-12, -0.55461907, -0.0157073092, 228.515784], [0.0, 0.0, 0.0, 1.0]])
        affine2 = np.array([[3.67499773e-08, -0.00871257665, 0.999876635, -33.9850922], [-0.5546875, 3.67499771e-08, 6.73024385e-08, 162.282928], [-3.73318194e-08, -0.554619071, -0.0157071802, 228.515778], [0.0, 0.0, 0.0, 1.0]])
        t = torch.rand(1, 2, 3, 4)
        subject = tio.Subject(im1=tio.ScalarImage(tensor=t, affine=affine1), im2=tio.ScalarImage(tensor=t, affine=affine2))
        subject.check_consistent_space()

    def test_delete_image(self):
        subject = copy.deepcopy(self.sample_subject)
        subject.remove_image('t1')
        with pytest.raises(KeyError):
            subject['t1']
        with pytest.raises(AttributeError):
            _ = subject.t1

    def test_2d(self):
        subject = self.make_2d(self.sample_subject)
        assert subject.is_2d()

    def test_different_non_numeric(self):
        with pytest.raises(RuntimeError):
            self.sample_subject.check_consistent_attribute('path')

    def test_bad_arg(self):
        with pytest.raises(ValueError):
            tio.Subject(0)

    def test_no_images(self):
        with pytest.raises(TypeError):
            tio.Subject(a=0)

    def test_copy_subject(self):
        sub_copy = copy.copy(self.sample_subject)
        assert isinstance(sub_copy, tio.data.Subject)
        sub_deep_copy = copy.deepcopy(self.sample_subject)
        assert isinstance(sub_deep_copy, tio.data.Subject)

    def test_copy_subclass(self):

        class DummySubjectSubClass(tio.data.Subject):

            def __init__(self, **kwargs):
                super().__init__(**kwargs)
        dummy_sub = DummySubjectSubClass(attr_1='abcd', attr_2=tio.ScalarImage(tensor=torch.zeros(1, 1, 1, 1)))
        sub_copy = copy.copy(dummy_sub)
        assert isinstance(sub_copy, tio.data.Subject)
        assert isinstance(sub_copy, DummySubjectSubClass)
        sub_deep_copy = copy.deepcopy(dummy_sub)
        assert isinstance(sub_deep_copy, tio.data.Subject)
        assert isinstance(sub_deep_copy, DummySubjectSubClass)

    def test_load_unload(self):
        self.sample_subject.load()
        for image in self.sample_subject.get_images(intensity_only=False):
            assert image._loaded
        self.sample_subject.unload()
        for image in self.sample_subject.get_images(intensity_only=False):
            assert not image._loaded

    def test_subjects_batch(self):
        subjects = tio.SubjectsDataset(10 * [self.sample_subject])
        loader = tio.SubjectsLoader(subjects, batch_size=4)
        batch = next(iter(loader))
        assert batch.__class__ is dict

    def test_deep_copy_subject(self):
        sub_copy = copy.deepcopy(self.sample_subject)
        assert isinstance(sub_copy, tio.data.Subject)
        new_tensor = torch.ones_like(sub_copy['t1'].data)
        sub_copy['t1'].set_data(new_tensor)
        assert not torch.allclose(sub_copy['t1'].data, self.sample_subject['t1'].data)

    def test_shallow_copy_subject(self):
        copy_original_subj = copy.deepcopy(self.sample_subject)
        sub_copy = copy.copy(copy_original_subj)
        assert isinstance(sub_copy, tio.data.Subject)
        new_tensor = torch.ones_like(sub_copy['t1'].data)
        sub_copy['t1'].set_data(new_tensor)
        assert torch.allclose(sub_copy['t1'].data, copy_original_subj['t1'].data)
        assert not torch.allclose(sub_copy['t1'].data, self.sample_subject['t1'].data)
        assert not torch.allclose(copy_original_subj['t1'].data, self.sample_subject['t1'].data)

def test_subjects_batch(self):
    subjects = tio.SubjectsDataset(10 * [self.sample_subject])
    loader = tio.SubjectsLoader(subjects, batch_size=4)
    batch = next(iter(loader))
    assert batch.__class__ is dict

class TestImage(TorchioTestCase):
    """Tests for `Image`."""

    def test_image_not_found(self):
        with pytest.raises(FileNotFoundError):
            tio.ScalarImage('nopath')

    @pytest.mark.skipif(sys.platform == 'win32', reason='Path not valid')
    def test_wrong_path_value(self):
        with pytest.raises(RuntimeError):
            tio.ScalarImage('~&./@#"!?X7=+')

    def test_wrong_path_type(self):
        with pytest.raises(TypeError):
            tio.ScalarImage(5)

    def test_wrong_affine(self):
        with pytest.raises(TypeError):
            tio.ScalarImage(5, affine=1)

    def test_tensor_flip(self):
        sample_input = torch.ones((4, 30, 30, 30))
        tio.RandomFlip()(sample_input)

    def test_tensor_affine(self):
        sample_input = torch.ones((4, 10, 10, 10))
        tio.RandomAffine()(sample_input)

    def test_wrong_scalar_image_type(self):
        data = torch.ones((1, 10, 10, 10))
        with pytest.raises(ValueError):
            tio.ScalarImage(tensor=data, type=tio.LABEL)

    def test_wrong_label_map_type(self):
        data = torch.ones((1, 10, 10, 10))
        with pytest.raises(ValueError):
            tio.LabelMap(tensor=data, type=tio.INTENSITY)

    def test_no_input(self):
        with pytest.raises(ValueError):
            tio.ScalarImage()

    def test_bad_key(self):
        with pytest.raises(ValueError):
            tio.ScalarImage(path='', data=5)

    def test_repr(self):
        subject = tio.Subject(t1=tio.ScalarImage(self.get_image_path('repr_test')))
        assert 'memory' not in repr(subject['t1'])
        subject.load()
        assert 'memory' in repr(subject['t1'])

    def test_data_tensor(self):
        subject = copy.deepcopy(self.sample_subject)
        subject.load()
        assert subject.t1.data is subject.t1.tensor

    def test_bad_affine(self):
        with pytest.raises(ValueError):
            tio.ScalarImage(tensor=torch.rand(1, 2, 3, 4), affine=np.eye(3))

    def test_nans_tensor(self):
        tensor = np.random.rand(1, 2, 3, 4)
        tensor[0, 0, 0, 0] = np.nan
        with pytest.warns(RuntimeWarning):
            image = tio.ScalarImage(tensor=tensor, check_nans=True)
        image.set_check_nans(False)

    def test_get_center(self):
        tensor = torch.rand(1, 3, 3, 3)
        image = tio.ScalarImage(tensor=tensor)
        ras = image.get_center()
        lps = image.get_center(lps=True)
        assert ras == (1, 1, 1)
        assert lps == (-1, -1, 1)

    def test_with_list_of_missing_files(self):
        with pytest.raises(FileNotFoundError):
            tio.ScalarImage(path=['nopath', 'error'])

    def test_with_sequences_of_paths(self):
        shape = (5, 5, 5)
        path1 = self.get_image_path('path1', shape=shape)
        path2 = self.get_image_path('path2', shape=shape)
        paths_tuple = (path1, path2)
        paths_list = list(paths_tuple)
        for sequence in (paths_tuple, paths_list):
            image = tio.ScalarImage(path=sequence)
            assert image.shape == (2, 5, 5, 5)
            assert image[tio.STEM] == ['path1', 'path2']

    def test_with_a_list_of_images_with_different_shapes(self):
        path1 = self.get_image_path('path1', shape=(5, 5, 5))
        path2 = self.get_image_path('path2', shape=(7, 5, 5))
        image = tio.ScalarImage(path=[path1, path2])
        with pytest.raises(RuntimeError):
            image.load()

    def test_with_a_list_of_images_with_different_affines(self):
        path1 = self.get_image_path('path1', spacing=(1, 1, 1))
        path2 = self.get_image_path('path2', spacing=(1, 2, 1))
        image = tio.ScalarImage(path=[path1, path2])
        with pytest.warns(RuntimeWarning):
            image.load()

    def test_with_a_list_of_2d_paths(self):
        shape = (5, 6)
        path1 = self.get_image_path('path1', shape=shape, suffix='.nii')
        path2 = self.get_image_path('path2', shape=shape, suffix='.img')
        path3 = self.get_image_path('path3', shape=shape, suffix='.hdr')
        image = tio.ScalarImage(path=[path1, path2, path3])
        assert image.shape == (3, 5, 6, 1)
        assert image[tio.STEM] == ['path1', 'path2', 'path3']

    def test_axis_name_2d(self):
        path = self.get_image_path('im2d', shape=(5, 6))
        image = tio.ScalarImage(path)
        height_idx = image.axis_name_to_index('t')
        width_idx = image.axis_name_to_index('l')
        assert image.height == image.shape[height_idx]
        assert image.width == image.shape[width_idx]

    def test_different_shape(self):
        path_1 = self.get_image_path('im_shape1', shape=(5, 5, 5))
        path_2 = self.get_image_path('im_shape2', shape=(7, 5, 5))
        image = tio.ScalarImage([path_1, path_2])
        with pytest.raises(RuntimeError):
            image.load()

    @pytest.mark.slow
    @pytest.mark.skipif(sys.platform == 'win32', reason='Unstable on Windows')
    def test_plot(self):
        image = self.sample_subject.t1
        image.plot(show=False, output_path=self.dir / 'image.png')

    def test_data_type_uint16_array(self):
        tensor = np.random.rand(1, 3, 3, 3).astype(np.uint16)
        image = tio.ScalarImage(tensor=tensor)
        assert image.data.dtype == torch.int32

    def test_data_type_uint32_array(self):
        tensor = np.random.rand(1, 3, 3, 3).astype(np.uint32)
        image = tio.ScalarImage(tensor=tensor)
        assert image.data.dtype == torch.int64

    def test_save_image_with_data_type_boolean(self):
        tensor = np.random.rand(1, 3, 3, 3).astype(bool)
        image = tio.ScalarImage(tensor=tensor)
        image.save(self.dir / 'image.nii')

    def test_load_uint(self):
        affine = np.eye(4)
        for dtype in (np.uint16, np.uint32):
            data = np.ones((3, 3, 3), dtype=dtype)
            img = nib.Nifti1Image(data, affine)
            with tempfile.NamedTemporaryFile(suffix='.nii', delete=False) as f:
                nib.save(img, f.name)
                tio.ScalarImage(f.name).load()

    def test_pil_3d(self):
        with pytest.raises(RuntimeError):
            tio.ScalarImage(tensor=torch.rand(1, 2, 3, 4)).as_pil()

    def test_pil_1(self):
        tio.ScalarImage(tensor=torch.rand(1, 2, 3, 1)).as_pil()

    def test_pil_2(self):
        with pytest.raises(RuntimeError):
            tio.ScalarImage(tensor=torch.rand(2, 2, 3, 1)).as_pil()

    def test_pil_3(self):
        tio.ScalarImage(tensor=torch.rand(3, 2, 3, 1)).as_pil()

    def test_set_data(self):
        im = self.sample_subject.t1
        with pytest.deprecated_call():
            im.data = im.data

    def test_no_type(self):
        with pytest.warns(FutureWarning):
            tio.Image(tensor=torch.rand(1, 2, 3, 4))

    def test_custom_reader(self):
        path = self.dir / 'im.npy'

        def numpy_reader(path):
            return (np.load(path), np.eye(4))

        def assert_shape(shape_in, shape_out):
            np.save(path, np.random.rand(*shape_in))
            image = tio.ScalarImage(path, reader=numpy_reader)
            assert image.shape == shape_out
        assert_shape((5, 5), (1, 5, 5, 1))
        assert_shape((5, 5, 3), (3, 5, 5, 1))
        assert_shape((3, 5, 5), (3, 5, 5, 1))
        assert_shape((5, 5, 5), (1, 5, 5, 5))
        assert_shape((1, 5, 5, 5), (1, 5, 5, 5))
        assert_shape((4, 5, 5, 5), (4, 5, 5, 5))

    def test_fast_gif(self):
        with pytest.warns(RuntimeWarning):
            with tempfile.NamedTemporaryFile(suffix='.gif', delete=False) as f:
                self.sample_subject.t1.to_gif(0, 0.0001, f.name)

    def test_gif_rgb(self):
        with tempfile.NamedTemporaryFile(suffix='.gif', delete=False) as f:
            tio.ScalarImage(tensor=torch.rand(3, 4, 5, 6)).to_gif(0, 1, f.name)

    @pytest.mark.slow
    def test_hist(self):
        self.sample_subject.t1.hist(density=False, show=False)
        self.sample_subject.t1.hist(density=True, show=False)

    def test_count(self):
        image = self.sample_subject.label
        max_n = image.data.numel()
        nonzero = image.count_nonzero()
        assert 0 <= nonzero <= max_n
        counts = image.count_labels()
        assert tuple(counts) == (0, 1)
        assert 0 <= counts[0] <= max_n
        assert 0 <= counts[1] <= max_n

    def test_affine_multipath(self):
        path1 = self.get_image_path('multi1')
        path2 = self.get_image_path('multi2')
        paths = (path1, path2)
        image = tio.ScalarImage(paths)
        self.assert_tensor_equal(image.affine, np.eye(4))

    def test_bad_numpy_type_reader(self):

        def numpy_reader(path):
            return (np.load(path), np.eye(4))
        tensor = np.random.rand(1, 2, 3, 4).astype(np.uint16)
        test_path = self.dir / 'test_image.npy'
        np.save(test_path, tensor)
        image = tio.ScalarImage(test_path, reader=numpy_reader)
        image.load()

    def test_load_unload(self):
        path = self.get_image_path('unload')
        image = tio.ScalarImage(path)
        with self.assertRaises(RuntimeError):
            image.unload()
        image.load()
        assert image._loaded
        image.unload()
        assert not image._loaded
        assert image[tio.DATA] is None
        assert image[tio.AFFINE] is None
        assert not image._loaded

    def test_unload_no_path(self):
        tensor = torch.rand(1, 2, 3, 4)
        image = tio.ScalarImage(tensor=tensor)
        with self.assertRaises(RuntimeError):
            image.unload()

    def test_copy_no_data(self):
        path = self.get_image_path('im_copy')
        my_image = tio.LabelMap(path)
        assert not my_image._loaded
        new_image = copy.copy(my_image)
        assert not my_image._loaded
        assert not new_image._loaded
        my_image.load()
        new_image = copy.copy(my_image)
        assert my_image._loaded
        assert new_image._loaded

    def test_slicing(self):
        path = self.get_image_path('im_slicing')
        image = tio.ScalarImage(path)
        assert image.shape == (1, 10, 20, 30)
        cropped = image[0]
        assert cropped.shape == (1, 1, 20, 30)
        cropped = image[:, 2:-3]
        assert cropped.shape == (1, 10, 15, 30)
        cropped = image[-5:, 5:]
        assert cropped.shape == (1, 5, 15, 30)
        with pytest.raises(NotImplementedError):
            image[..., 5]
        with pytest.raises(ValueError):
            image[0:8:-1]
        with pytest.raises(ValueError):
            image[3::-1]

    def test_verify_path(self):
        path = Path(self.get_image_path('im_verify'))
        image = tio.ScalarImage(path, verify_path=False)
        assert image.path == path
        image = tio.ScalarImage(path, verify_path=True)
        assert image.path == path
        fake_path = Path('fake_path.nii')
        image = tio.ScalarImage(fake_path, verify_path=False)
        assert image.path == fake_path
        with pytest.raises(FileNotFoundError):
            tio.ScalarImage(fake_path, verify_path=True)

@pytest.mark.slow
def test_hist(self):
    self.sample_subject.t1.hist(density=False, show=False)
    self.sample_subject.t1.hist(density=True, show=False)

class TestGridSampler(TorchioTestCase):
    """Tests for `GridSampler`."""

    def test_locations(self):
        patch_size = (5, 20, 20)
        patch_overlap = (2, 4, 6)
        sampler = tio.GridSampler(subject=self.sample_subject, patch_size=patch_size, patch_overlap=patch_overlap)
        fixture = [[0, 0, 0, 5, 20, 20], [0, 0, 10, 5, 20, 30], [3, 0, 0, 8, 20, 20], [3, 0, 10, 8, 20, 30], [5, 0, 0, 10, 20, 20], [5, 0, 10, 10, 20, 30]]
        locations = sampler.locations.tolist()
        assert locations == fixture

    def test_generate_patches(self):
        patch_size = (5, 15, 15)
        sampler = tio.GridSampler(self.sample_subject, patch_size)
        for patch in sampler():
            assert patch.spatial_shape == patch_size

    def test_large_patch(self):
        with pytest.raises(ValueError):
            tio.GridSampler(self.sample_subject, (5, 21, 5), (0, 2, 0))

    def test_large_overlap(self):
        with pytest.raises(ValueError):
            tio.GridSampler(self.sample_subject, (5, 20, 5), (2, 4, 6))

    def test_odd_overlap(self):
        with pytest.raises(ValueError):
            tio.GridSampler(self.sample_subject, (5, 20, 5), (2, 4, 3))

    def test_single_location(self):
        sampler = tio.GridSampler(self.sample_subject, (10, 20, 30), 0)
        fixture = [[0, 0, 0, 10, 20, 30]]
        assert sampler.locations.tolist() == fixture

    def test_subject_shape(self):
        patch_size = (5, 20, 20)
        patch_overlap = (2, 4, 6)
        initial_shape = copy(self.sample_subject.shape)
        tio.GridSampler(self.sample_subject, patch_size, patch_overlap, padding_mode='reflect')
        final_shape = self.sample_subject.shape
        assert initial_shape == final_shape

def test_locations(self):
    patch_size = (5, 20, 20)
    patch_overlap = (2, 4, 6)
    sampler = tio.GridSampler(subject=self.sample_subject, patch_size=patch_size, patch_overlap=patch_overlap)
    fixture = [[0, 0, 0, 5, 20, 20], [0, 0, 10, 5, 20, 30], [3, 0, 0, 8, 20, 20], [3, 0, 10, 8, 20, 30], [5, 0, 0, 10, 20, 20], [5, 0, 10, 10, 20, 30]]
    locations = sampler.locations.tolist()
    assert locations == fixture

def test_generate_patches(self):
    patch_size = (5, 15, 15)
    sampler = tio.GridSampler(self.sample_subject, patch_size)
    for patch in sampler():
        assert patch.spatial_shape == patch_size

def test_large_patch(self):
    with pytest.raises(ValueError):
        tio.GridSampler(self.sample_subject, (5, 21, 5), (0, 2, 0))

def test_large_overlap(self):
    with pytest.raises(ValueError):
        tio.GridSampler(self.sample_subject, (5, 20, 5), (2, 4, 6))

def test_odd_overlap(self):
    with pytest.raises(ValueError):
        tio.GridSampler(self.sample_subject, (5, 20, 5), (2, 4, 3))

def test_single_location(self):
    sampler = tio.GridSampler(self.sample_subject, (10, 20, 30), 0)
    fixture = [[0, 0, 0, 10, 20, 30]]
    assert sampler.locations.tolist() == fixture

class TestAggregator(TorchioTestCase):
    """Tests for `aggregator` module."""

    def aggregate(self, mode, fixture):
        image_shape = (1, 1, 4, 4)
        tensor = torch.ones(image_shape)
        fixture = torch.as_tensor(fixture).reshape(image_shape)
        image_name = 'img'
        subject = tio.Subject({image_name: tio.ScalarImage(tensor=tensor)})
        patch_size = (1, 3, 3)
        patch_overlap = (0, 2, 2)
        sampler = tio.data.GridSampler(subject, patch_size, patch_overlap)
        aggregator = tio.data.GridAggregator(sampler, overlap_mode=mode)
        loader = tio.SubjectsLoader(sampler, batch_size=3)
        values_dict = {(0, 0): 0, (0, 1): 2, (1, 0): 4, (1, 1): 6}
        for batch in loader:
            iterable = zip(batch[tio.LOCATION], batch[image_name][tio.DATA])
            for location, data in iterable:
                coords_2d = tuple(location[1:3].tolist())
                data *= values_dict[coords_2d]
            batch_data = batch[image_name][tio.DATA]
            aggregator.add_batch(batch_data, batch[tio.LOCATION])
        output = aggregator.get_output_tensor()
        self.assert_tensor_equal(output, fixture)

    def test_overlap_crop(self):
        fixture = ((0, 0, 2, 2), (0, 0, 2, 2), (4, 4, 6, 6), (4, 4, 6, 6))
        self.aggregate('crop', fixture)

    def test_overlap_average(self):
        fixture = ((0, 1, 1, 2), (2, 3, 3, 4), (2, 3, 3, 4), (4, 5, 5, 6))
        self.aggregate('average', fixture)

    def test_overlap_hann(self):
        fixture = ((0 / 3, 2 / 3, 4 / 3, 6 / 3), (4 / 3, 6 / 3, 8 / 3, 10 / 3), (8 / 3, 10 / 3, 12 / 3, 14 / 3), (12 / 3, 14 / 3, 16 / 3, 18 / 3))
        self.aggregate('hann', fixture)

    def run_sampler_aggregator(self, overlap_mode='crop'):
        patch_size = 10
        patch_overlap = 2
        grid_sampler = tio.inference.GridSampler(self.sample_subject, patch_size, patch_overlap)
        patch_loader = tio.SubjectsLoader(grid_sampler)
        aggregator = tio.inference.GridAggregator(grid_sampler, overlap_mode=overlap_mode)
        for batch in patch_loader:
            data = batch['t1'][tio.DATA].long()
            aggregator.add_batch(data, batch[tio.LOCATION])
        return aggregator

    def test_warning_int64(self):
        aggregator = self.run_sampler_aggregator()
        with pytest.warns(RuntimeWarning):
            aggregator.get_output_tensor()

    def run_patch_crop_issue(self, *, padding_mode):
        pao, pas, ims, bb1, bb2 = (4, 102, 320, 100, 120)
        patch_overlap = (pao, 0, 0)
        patch_size = (pas, 1, 1)
        img = torch.zeros((1, ims, 1, 1))
        bbox = [bb1, bb2]
        img[:, bbox[0]:bbox[1]] = 1
        image = tio.LabelMap(tensor=img)
        subject = tio.Subject(image=image)
        grid_sampler = tio.inference.GridSampler(subject, patch_size, patch_overlap)
        patch_loader = tio.SubjectsLoader(grid_sampler)
        aggregator = tio.inference.GridAggregator(grid_sampler)
        for patches_batch in patch_loader:
            input_tensor = patches_batch['image'][tio.DATA]
            locations = patches_batch[tio.LOCATION]
            aggregator.add_batch(input_tensor, locations)
        output_tensor = aggregator.get_output_tensor()
        self.assert_tensor_equal(image.tensor, output_tensor)

    def test_patch_crop_issue_no_padding(self):
        self.run_patch_crop_issue(padding_mode=None)

    def test_patch_crop_issue_padding(self):
        self.run_patch_crop_issue(padding_mode='constant')

    def test_bad_aggregator_shape(self):
        tensor = torch.ones(1, 40, 40, 40)
        image_name = 'img'
        subject = tio.Subject({image_name: tio.ScalarImage(tensor=tensor)})
        patch_size = 40
        patch_overlap = 30
        sampler = tio.data.GridSampler(subject, patch_size, patch_overlap, padding_mode='edge')
        aggregator = tio.data.GridAggregator(sampler)
        loader = tio.SubjectsLoader(sampler, batch_size=3)
        for batch in loader:
            input_batch = batch[image_name][tio.DATA]
            crop = tio.CropOrPad(12)
            patches = [crop(patch) for patch in input_batch]
            inference_batch = torch.stack(patches)
            with pytest.raises(RuntimeError):
                aggregator.add_batch(inference_batch, batch[tio.LOCATION])

def aggregate(self, mode, fixture):
    image_shape = (1, 1, 4, 4)
    tensor = torch.ones(image_shape)
    fixture = torch.as_tensor(fixture).reshape(image_shape)
    image_name = 'img'
    subject = tio.Subject({image_name: tio.ScalarImage(tensor=tensor)})
    patch_size = (1, 3, 3)
    patch_overlap = (0, 2, 2)
    sampler = tio.data.GridSampler(subject, patch_size, patch_overlap)
    aggregator = tio.data.GridAggregator(sampler, overlap_mode=mode)
    loader = tio.SubjectsLoader(sampler, batch_size=3)
    values_dict = {(0, 0): 0, (0, 1): 2, (1, 0): 4, (1, 1): 6}
    for batch in loader:
        iterable = zip(batch[tio.LOCATION], batch[image_name][tio.DATA])
        for location, data in iterable:
            coords_2d = tuple(location[1:3].tolist())
            data *= values_dict[coords_2d]
        batch_data = batch[image_name][tio.DATA]
        aggregator.add_batch(batch_data, batch[tio.LOCATION])
    output = aggregator.get_output_tensor()
    self.assert_tensor_equal(output, fixture)

def run_sampler_aggregator(self, overlap_mode='crop'):
    patch_size = 10
    patch_overlap = 2
    grid_sampler = tio.inference.GridSampler(self.sample_subject, patch_size, patch_overlap)
    patch_loader = tio.SubjectsLoader(grid_sampler)
    aggregator = tio.inference.GridAggregator(grid_sampler, overlap_mode=overlap_mode)
    for batch in patch_loader:
        data = batch['t1'][tio.DATA].long()
        aggregator.add_batch(data, batch[tio.LOCATION])
    return aggregator

def test_warning_int64(self):
    aggregator = self.run_sampler_aggregator()
    with pytest.warns(RuntimeWarning):
        aggregator.get_output_tensor()

def run_patch_crop_issue(self, *, padding_mode):
    pao, pas, ims, bb1, bb2 = (4, 102, 320, 100, 120)
    patch_overlap = (pao, 0, 0)
    patch_size = (pas, 1, 1)
    img = torch.zeros((1, ims, 1, 1))
    bbox = [bb1, bb2]
    img[:, bbox[0]:bbox[1]] = 1
    image = tio.LabelMap(tensor=img)
    subject = tio.Subject(image=image)
    grid_sampler = tio.inference.GridSampler(subject, patch_size, patch_overlap)
    patch_loader = tio.SubjectsLoader(grid_sampler)
    aggregator = tio.inference.GridAggregator(grid_sampler)
    for patches_batch in patch_loader:
        input_tensor = patches_batch['image'][tio.DATA]
        locations = patches_batch[tio.LOCATION]
        aggregator.add_batch(input_tensor, locations)
    output_tensor = aggregator.get_output_tensor()
    self.assert_tensor_equal(image.tensor, output_tensor)

def test_bad_aggregator_shape(self):
    tensor = torch.ones(1, 40, 40, 40)
    image_name = 'img'
    subject = tio.Subject({image_name: tio.ScalarImage(tensor=tensor)})
    patch_size = 40
    patch_overlap = 30
    sampler = tio.data.GridSampler(subject, patch_size, patch_overlap, padding_mode='edge')
    aggregator = tio.data.GridAggregator(sampler)
    loader = tio.SubjectsLoader(sampler, batch_size=3)
    for batch in loader:
        input_batch = batch[image_name][tio.DATA]
        crop = tio.CropOrPad(12)
        patches = [crop(patch) for patch in input_batch]
        inference_batch = torch.stack(patches)
        with pytest.raises(RuntimeError):
            aggregator.add_batch(inference_batch, batch[tio.LOCATION])

class TestInference(TorchioTestCase):
    """Tests for `inference` module."""

    def test_inference_no_padding(self):
        self.try_inference(None)

    def test_inference_padding(self):
        self.try_inference(3)

    def try_inference(self, padding_mode):
        for n in (17, 27):
            patch_size = (10, 15, n)
            patch_overlap = (4, 6, 8)
            batch_size = 6
            grid_sampler = GridSampler(self.sample_subject, patch_size, patch_overlap, padding_mode=padding_mode)
            aggregator = GridAggregator(grid_sampler)
            patch_loader = tio.SubjectsLoader(grid_sampler, batch_size=batch_size)
            for patches_batch in patch_loader:
                input_tensor = patches_batch['t1'][DATA]
                locations = patches_batch[LOCATION]
                logits = model(input_tensor)
                outputs = logits
                aggregator.add_batch(outputs, locations)
            output = aggregator.get_output_tensor()
            assert (output == -5).all()
            assert output.shape == self.sample_subject.t1.shape

def try_inference(self, padding_mode):
    for n in (17, 27):
        patch_size = (10, 15, n)
        patch_overlap = (4, 6, 8)
        batch_size = 6
        grid_sampler = GridSampler(self.sample_subject, patch_size, patch_overlap, padding_mode=padding_mode)
        aggregator = GridAggregator(grid_sampler)
        patch_loader = tio.SubjectsLoader(grid_sampler, batch_size=batch_size)
        for patches_batch in patch_loader:
            input_tensor = patches_batch['t1'][DATA]
            locations = patches_batch[LOCATION]
            logits = model(input_tensor)
            outputs = logits
            aggregator.add_batch(outputs, locations)
        output = aggregator.get_output_tensor()
        assert (output == -5).all()
        assert output.shape == self.sample_subject.t1.shape

class TestCollate(TorchioTestCase):

    def get_heterogeneous_dataset(self):
        transform_no = tio.RandomElasticDeformation(p=0, max_displacement=1)
        transform_yes = tio.RandomElasticDeformation(p=1, max_displacement=1)
        sample_no = transform_no(self.sample_subject)
        sample_yes = transform_yes(self.sample_subject)
        data = (sample_no, sample_yes)

        class Dataset:

            def __init__(self, data):
                self.data = data

            def __len__(self):
                return len(self.data)

            def __getitem__(self, index):
                return self.data[index]
        return Dataset(data)

    def test_collate(self):
        loader = tio.SubjectsLoader(self.get_heterogeneous_dataset(), batch_size=2)
        tio.utils.get_first_item(loader)

    def test_history_collate(self):
        loader = tio.SubjectsLoader(self.get_heterogeneous_dataset(), batch_size=4, collate_fn=tio.utils.history_collate)
        batch = tio.utils.get_first_item(loader)
        empty_history, one_history = batch['history']
        assert not empty_history
        assert len(one_history) == 1

def test_collate(self):
    loader = tio.SubjectsLoader(self.get_heterogeneous_dataset(), batch_size=2)
    tio.utils.get_first_item(loader)

def test_history_collate(self):
    loader = tio.SubjectsLoader(self.get_heterogeneous_dataset(), batch_size=4, collate_fn=tio.utils.history_collate)
    batch = tio.utils.get_first_item(loader)
    empty_history, one_history = batch['history']
    assert not empty_history
    assert len(one_history) == 1

class TestTransform(TorchioTestCase):

    def test_abstract_transform(self):
        with pytest.raises(TypeError):
            tio.Transform()

    def test_arguments_are_not_dict(self):
        transform = tio.Noise(0, 1, 0)
        assert not transform.arguments_are_dict()

    def test_arguments_are_dict(self):
        transform = tio.Noise({'im': 0}, {'im': 1}, {'im': 0})
        assert transform.arguments_are_dict()

    def test_arguments_are_and_are_not_dict(self):
        transform = tio.Noise(0, {'im': 1}, {'im': 0})
        with pytest.raises(ValueError):
            transform.arguments_are_dict()

    def test_bad_over_max(self):
        transform = tio.RandomNoise()
        with pytest.raises(ValueError):
            transform._parse_range(2, 'name', max_constraint=1)

    def test_bad_over_max_range(self):
        transform = tio.RandomNoise()
        with pytest.raises(ValueError):
            transform._parse_range((0, 2), 'name', max_constraint=1)

    def test_bad_type(self):
        transform = tio.RandomNoise()
        with pytest.raises(ValueError):
            transform._parse_range(2.5, 'name', type_constraint=int)

    def test_no_numbers(self):
        transform = tio.RandomNoise()
        with pytest.raises(ValueError):
            transform._parse_range('j', 'name')

    def test_apply_transform_missing(self):

        class T(tio.Transform):
            pass
        with pytest.raises(TypeError):
            T().apply_transform(0)

    def test_non_invertible(self):
        transform = tio.RandomBlur()
        with pytest.raises(RuntimeError):
            transform.inverse()

    def test_batch_history(self):
        subject = self.sample_subject
        transform = tio.Compose([tio.RandomAffine(), tio.CropOrPad(5), tio.OneHot()])
        dataset = tio.SubjectsDataset([subject], transform=transform)
        loader = tio.SubjectsLoader(dataset, collate_fn=tio.utils.history_collate)
        batch = tio.utils.get_first_item(loader)
        transformed: tio.Subject = tio.utils.get_subjects_from_batch(batch)[0]
        inverse = transformed.apply_inverse_transform()
        images1 = subject.get_images(intensity_only=False)
        images2 = inverse.get_images(intensity_only=False)
        for image1, image2 in zip(images1, images2):
            assert image1.shape == image2.shape

    def test_bad_bounds_mask(self):
        transform = tio.ZNormalization(masking_method='test')
        with pytest.raises(ValueError):
            transform(self.sample_subject)

    def test_bounds_mask(self):
        transform = tio.ZNormalization()
        with pytest.raises(ValueError):
            transform.get_mask_from_anatomical_label('test', 0)
        tensor = torch.rand((1, 2, 2, 2))

        def get_mask(label):
            mask = transform.get_mask_from_anatomical_label(label, tensor)
            return mask
        left = get_mask('Left')
        assert left[:, 0].sum() == 4 and left[:, 1].sum() == 0
        right = get_mask('Right')
        assert right[:, 1].sum() == 4 and right[:, 0].sum() == 0
        posterior = get_mask('Posterior')
        assert posterior[:, :, 0].sum() == 4 and posterior[:, :, 1].sum() == 0
        anterior = get_mask('Anterior')
        assert anterior[:, :, 1].sum() == 4 and anterior[:, :, 0].sum() == 0
        inferior = get_mask('Inferior')
        assert inferior[..., 0].sum() == 4 and inferior[..., 1].sum() == 0
        superior = get_mask('Superior')
        assert superior[..., 1].sum() == 4 and superior[..., 0].sum() == 0
        mask = transform.get_mask_from_bounds(3 * (0, 1), tensor)
        assert mask[0, 0, 0, 0] == 1
        assert mask.sum() == 1

    def test_label_keys(self):
        size = (1, 10, 10, 10)
        image = torch.rand(size)
        num_classes = 2
        label = torch.randint(num_classes + 1, size)
        data_dict = {'image': image, 'label': label}
        transform = tio.RandomAffine(include=['image', 'label'], label_keys=['label'])
        transformed_label = transform(data_dict)['label']
        num_unique_values = len(torch.unique(transformed_label))
        assert num_unique_values <= num_classes + 1

    def test_nibabel_input(self):
        image = self.sample_subject.t1
        image_nib = Nifti1Image(image.data[0].numpy(), image.affine)
        transformed = tio.RandomAffine()(image_nib)
        transformed.get_fdata()
        _ = transformed.affine
        image = self.subject_4d.t1
        tensor_5d = image.data[np.newaxis].permute(2, 3, 4, 0, 1)
        image_nib = Nifti1Image(tensor_5d.numpy(), image.affine)
        transformed = tio.RandomAffine()(image_nib)
        transformed.get_fdata()
        _ = transformed.affine

    def test_bad_shape(self):
        tensor = torch.rand(1, 2, 3)
        with pytest.raises(ValueError, match='must be a 4D tensor'):
            tio.RandomAffine()(tensor)

    def test_bad_keys_type(self):
        with self.assertRaises(ValueError):
            tio.RandomAffine(include='t1')

    def test_init_args(self):
        transform = tio.Compose([tio.RandomNoise()])
        base_args = transform.get_base_args()
        assert 'parse_input' not in base_args
        transform = tio.OneOf([tio.RandomNoise()])
        base_args = transform.get_base_args()
        assert 'parse_input' not in base_args
        transform = tio.RandomNoise()
        base_args = transform.get_base_args()
        assert all((arg in base_args for arg in ['copy', 'include', 'exclude', 'keep', 'parse_input', 'label_keys']))

def test_batch_history(self):
    subject = self.sample_subject
    transform = tio.Compose([tio.RandomAffine(), tio.CropOrPad(5), tio.OneHot()])
    dataset = tio.SubjectsDataset([subject], transform=transform)
    loader = tio.SubjectsLoader(dataset, collate_fn=tio.utils.history_collate)
    batch = tio.utils.get_first_item(loader)
    transformed: tio.Subject = tio.utils.get_subjects_from_batch(batch)[0]
    inverse = transformed.apply_inverse_transform()
    images1 = subject.get_images(intensity_only=False)
    images2 = inverse.get_images(intensity_only=False)
    for image1, image2 in zip(images1, images2):
        assert image1.shape == image2.shape

