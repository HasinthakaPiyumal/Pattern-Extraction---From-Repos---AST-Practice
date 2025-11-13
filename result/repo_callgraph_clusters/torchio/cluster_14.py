# Cluster 14

def get_num_bins(x: np.ndarray) -> int:
    """Get the optimal number of bins for a histogram.

    This method uses the Freedman–Diaconis rule to compute the histogram that
    minimizes "the integral of the squared difference between the histogram
    (i.e., relative frequency density) and the density of the theoretical
    probability distribution" (`Wikipedia <https://en.wikipedia.org/wiki/Freedman%E2%80%93Diaconis_rule>`_).

    Args:
        x: Input values.
    """
    q25, q75 = np.percentile(x, [25, 75])
    bin_width = 2 * (q75 - q25) * len(x) ** (-1 / 3)
    bins = round((x.max() - x.min()) / bin_width)
    return bins

def make_video(image: ScalarImage, output_path: TypePath, seconds: float | None=None, frame_rate: float | None=None, direction: str='I', verbosity: str='error') -> None:
    ffmpeg = get_ffmpeg()
    if seconds is None and frame_rate is None:
        message = 'Either seconds or frame_rate must be provided.'
        raise ValueError(message)
    if seconds is not None and frame_rate is not None:
        message = 'Provide either seconds or frame_rate, not both.'
        raise ValueError(message)
    if image.num_channels > 1:
        message = 'Only single-channel tensors are supported for video output for now.'
        raise ValueError(message)
    tmin, tmax = (image.data.min(), image.data.max())
    if tmin < 0 or tmax > 255:
        message = 'The tensor must be in the range [0, 256) for video output. The image data will be rescaled to this range.'
        warnings.warn(message, RuntimeWarning, stacklevel=2)
        image = RescaleIntensity((0, 255))(image)
    if image.data.dtype != torch.uint8:
        message = 'Only uint8 tensors are supported for video output. The image data will be cast to uint8.'
        warnings.warn(message, RuntimeWarning, stacklevel=2)
        image = To(torch.uint8)(image)
    direction = direction.upper()
    if direction == 'I':
        target = 'IPL'
    elif direction == 'S':
        target = 'SPL'
    elif direction == 'A':
        target = 'AIL'
    elif direction == 'P':
        target = 'PIL'
    elif direction == 'R':
        target = 'RIP'
    elif direction == 'L':
        target = 'LIP'
    else:
        message = f'Direction must be one of "I", "S", "P", "A", "R" or "L". Got {direction!r}.'
        raise ValueError(message)
    image = ToOrientation(target)(image)
    spacing_f, spacing_h, spacing_w = image.spacing
    if spacing_h != spacing_w:
        message = f'The height and width spacings should be the same video output. Got {spacing_h:.2f} and {spacing_w:.2f}. Resampling both to {spacing_f:.2f}.'
        warnings.warn(message, RuntimeWarning, stacklevel=2)
        spacing_iso = min(spacing_h, spacing_w)
        target_spacing = (spacing_f, spacing_iso, spacing_iso)
        image = Resample(target_spacing)(image)
    num_frames, height, width = image.spatial_shape
    if height % 2 != 0 or width % 2 != 0:
        message = f'The height ({height}) and width ({width}) must be even. The image will be cropped to the nearest even number.'
        warnings.warn(message, RuntimeWarning, stacklevel=2)
        image = EnsureShapeMultiple((1, 2, 2), method='crop')(image)
    if seconds is not None:
        frame_rate = num_frames / seconds
    output_path = Path(output_path)
    if output_path.suffix.lower() != '.mp4':
        message = 'Only .mp4 files are supported for video output.'
        raise NotImplementedError(message)
    frames = image.numpy()[0]
    first = frames[0]
    height, width = first.shape
    process = ffmpeg.input('pipe:', format='rawvideo', pix_fmt='gray', s=f'{width}x{height}', framerate=frame_rate).output(str(output_path), vcodec='libx265', pix_fmt='yuv420p', loglevel=verbosity, **{'x265-params': f'log-level={verbosity}'}).overwrite_output().run_async(pipe_stdin=True)
    for array in frames:
        buffer = array.tobytes()
        process.stdin.write(buffer)
    process.stdin.close()
    process.wait()

def _to_itk_convention(matrix: TypeData) -> np.ndarray:
    """RAS to LPS."""
    if isinstance(matrix, torch.Tensor):
        matrix = matrix.numpy()
    matrix = np.dot(FLIPXY_44, matrix)
    matrix = np.dot(matrix, FLIPXY_44)
    matrix = np.linalg.inv(matrix)
    return matrix

def _from_itk_convention(matrix: TypeData) -> np.ndarray:
    """LPS to RAS."""
    matrix = np.dot(matrix, FLIPXY_44)
    matrix = np.dot(FLIPXY_44, matrix)
    matrix = np.linalg.inv(matrix)
    return matrix

def _read_niftyreg_matrix(trsf_path: TypePath) -> torch.Tensor:
    """Read a NiftyReg matrix and return it as a NumPy array."""
    read_matrix = np.loadtxt(trsf_path).astype(np.float64)
    inverted = np.linalg.inv(read_matrix)
    return torch.from_numpy(inverted)

def _write_niftyreg_matrix(matrix: TypeData, txt_path: TypePath) -> None:
    """Write an affine transform in NiftyReg's .txt format (ref -> flo)"""
    matrix = np.linalg.inv(matrix)
    np.savetxt(txt_path, matrix, fmt='%.8f')

def get_sitk_metadata_from_ras_affine(affine: np.ndarray, is_2d: bool=False, lps: bool=True) -> tuple[TypeTripletFloat, TypeTripletFloat, TypeDirection]:
    direction_ras, spacing_array = get_rotation_and_spacing_from_affine(affine)
    origin_ras = affine[:3, 3]
    origin_lps = np.dot(FLIPXY_33, origin_ras)
    direction_lps = np.dot(FLIPXY_33, direction_ras)
    if is_2d:
        direction_lps = np.diag((-1, -1)).astype(np.float64)
        direction_ras = np.diag((1, 1)).astype(np.float64)
    origin_array = origin_lps if lps else origin_ras
    direction_array = direction_lps if lps else direction_ras
    direction_array = direction_array.flatten()
    ox, oy, oz = origin_array
    sx, sy, sz = spacing_array
    direction: TypeDirection
    if is_2d:
        d1, d2, d3, d4 = direction_array
        direction = (d1, d2, d3, d4)
    else:
        d1, d2, d3, d4, d5, d6, d7, d8, d9 = direction_array
        direction = (d1, d2, d3, d4, d5, d6, d7, d8, d9)
    origin = (ox, oy, oz)
    spacing = (sx, sy, sz)
    return (origin, spacing, direction)

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

def __array__(self):
    return self.data.numpy()

@property
def orientation(self) -> tuple[str, str, str]:
    """Orientation codes."""
    return nib.orientations.aff2axcodes(self.affine)

@property
def spacing(self) -> tuple[float, float, float]:
    """Voxel spacing in mm."""
    _, spacing = get_rotation_and_spacing_from_affine(self.affine)
    sx, sy, sz = spacing
    return (float(sx), float(sy), float(sz))

class ScalarImage(Image):
    """Image whose pixel values represent scalars.

    Example:
        >>> import torch
        >>> import torchio as tio
        >>> # Loading from a file
        >>> t1_image = tio.ScalarImage('t1.nii.gz')
        >>> dmri = tio.ScalarImage(tensor=torch.rand(32, 128, 128, 88))
        >>> image = tio.ScalarImage('safe_image.nrrd', check_nans=False)
        >>> data, affine = image.data, image.affine
        >>> affine.shape
        (4, 4)
        >>> image.data is image[tio.DATA]
        True
        >>> image.data is image.tensor
        True
        >>> type(image.data)
        torch.Tensor

    See :class:`~torchio.Image` for more information.
    """

    def __init__(self, *args, **kwargs):
        if 'type' in kwargs and kwargs['type'] != INTENSITY:
            raise ValueError('Type of ScalarImage is always torchio.INTENSITY')
        kwargs.update({'type': INTENSITY})
        super().__init__(*args, **kwargs)

    def hist(self, **kwargs) -> None:
        """Plot histogram."""
        from ..visualization import plot_histogram
        x = self.data.flatten().numpy()
        plot_histogram(x, **kwargs)

    def to_video(self, output_path: TypePath, frame_rate: float | None=15, seconds: float | None=None, direction: str='I', verbosity: str='error') -> None:
        """Create a video showing all image slices along a specified direction.

        Args:
            output_path: Path to the output video file.
            frame_rate: Number of frames per second (FPS).
            seconds: Target duration of the full video.
            direction:
            verbosity:

        .. note:: Only ``frame_rate`` or ``seconds`` may (and must) be specified.
        """
        from ..visualization import make_video
        make_video(self.to_ras(), output_path, frame_rate=frame_rate, seconds=seconds, direction=direction, verbosity=verbosity)

def hist(self, **kwargs) -> None:
    """Plot histogram."""
    from ..visualization import plot_histogram
    x = self.data.flatten().numpy()
    plot_histogram(x, **kwargs)

class LabelSampler(WeightedSampler):
    """Extract random patches with labeled voxels at their center.

    This sampler yields patches whose center value is greater than 0
    in the :attr:`label_name`.

    Args:
        patch_size: See :class:`~torchio.data.PatchSampler`.
        label_name: Name of the label image in the subject that will be used to
            generate the sampling probability map. If ``None``, the first image
            of type :attr:`torchio.LABEL` found in the subject subject will be
            used.
        label_probabilities: Dictionary containing the probability that each
            class will be sampled. Probabilities do not need to be normalized.
            For example, a value of ``{0: 0, 1: 2, 2: 1, 3: 1}`` will create a
            sampler whose patches centers will have 50% probability of being
            labeled as ``1``, 25% of being ``2`` and 25% of being ``3``.
            If ``None``, the label map is binarized and the value is set to
            ``{0: 0, 1: 1}``.
            If the input has multiple channels, a value of
            ``{0: 0, 1: 2, 2: 1, 3: 1}`` will create a
            sampler whose patches centers will have 50% probability of being
            taken from a non zero value of channel ``1``, 25% from channel
            ``2`` and 25% from channel ``3``.

    Example:
        >>> import torchio as tio
        >>> subject = tio.datasets.Colin27()
        >>> subject
        Colin27(Keys: ('t1', 'head', 'brain'); images: 3)
        >>> probabilities = {0: 0.5, 1: 0.5}
        >>> sampler = tio.data.LabelSampler(
        ...     patch_size=64,
        ...     label_name='brain',
        ...     label_probabilities=probabilities,
        ... )
        >>> generator = sampler(subject)
        >>> for patch in generator:
        ...     print(patch.shape)

    If you want a specific number of patches from a volume, e.g. 10:

        >>> generator = sampler(subject, num_patches=10)
        >>> for patch in iterator:
        ...     print(patch.shape)
    """

    def __init__(self, patch_size: TypeSpatialShape, label_name: str | None=None, label_probabilities: dict[int, float] | None=None):
        super().__init__(patch_size, probability_map=label_name)
        self.label_probabilities_dict = label_probabilities

    def get_probability_map_image(self, subject: Subject) -> Image:
        if self.probability_map_name is None:
            for image in subject.get_images(intensity_only=False):
                if image[TYPE] == LABEL:
                    label_map = image
                    break
            else:
                images = subject.get_images(intensity_only=False)
                message = f'No label maps found in subject {subject} with image paths {[image.path for image in images]}'
                raise RuntimeError(message)
        elif self.probability_map_name in subject:
            label_map = subject[self.probability_map_name]
        else:
            message = f'Image "{self.probability_map_name}" not found in subject subject: {subject}'
            raise KeyError(message)
        return label_map

    def get_probability_map(self, subject: Subject) -> torch.Tensor:
        label_map_tensor = self.get_probability_map_image(subject).data.float()
        if self.label_probabilities_dict is None:
            return label_map_tensor > 0
        probability_map = self.get_probabilities_from_label_map(label_map_tensor, self.label_probabilities_dict, self.patch_size)
        return probability_map

    @staticmethod
    def get_probabilities_from_label_map(label_map: torch.Tensor, label_probabilities_dict: dict[int, float], patch_size: np.ndarray) -> torch.Tensor:
        """Create probability map according to label map probabilities."""
        patch_size = patch_size.astype(int)
        ini_i, ini_j, ini_k = patch_size // 2
        spatial_shape = np.array(label_map.shape[1:])
        if np.any(patch_size > spatial_shape):
            message = f'Patch size {patch_size}larger than label map {spatial_shape}'
            raise RuntimeError(message)
        crop_fin_i, crop_fin_j, crop_fin_k = crop_fin = (patch_size - 1) // 2
        fin_i, fin_j, fin_k = spatial_shape - crop_fin
        label_map = label_map[:, ini_i:fin_i, ini_j:fin_j, ini_k:fin_k]
        multichannel = label_map.shape[0] > 1
        probability_map = torch.zeros_like(label_map)
        label_probs = torch.Tensor(list(label_probabilities_dict.values()))
        normalized_probs = label_probs / label_probs.sum()
        iterable = zip(label_probabilities_dict, normalized_probs)
        for label, label_probability in iterable:
            if multichannel:
                mask = label_map[label]
            else:
                mask = label_map == label
            label_size = mask.sum()
            if not label_size:
                continue
            prob_voxels = label_probability / label_size
            if multichannel:
                probability_map[label] = prob_voxels * mask
            else:
                probability_map[mask] = prob_voxels
        if multichannel:
            probability_map = probability_map.sum(dim=0, keepdim=True)
        padding = (ini_k, crop_fin_k, ini_j, crop_fin_j, ini_i, crop_fin_i)
        probability_map = torch.nn.functional.pad(probability_map, padding)
        return probability_map

def get_probability_map(self, subject: Subject) -> torch.Tensor:
    label_map_tensor = self.get_probability_map_image(subject).data.float()
    if self.label_probabilities_dict is None:
        return label_map_tensor > 0
    probability_map = self.get_probabilities_from_label_map(label_map_tensor, self.label_probabilities_dict, self.patch_size)
    return probability_map

class WeightedSampler(RandomSampler):
    """Randomly extract patches from a volume given a probability map.

    The probability of sampling a patch centered on a specific voxel is the
    value of that voxel in the probability map. The probabilities need not be
    normalized. For example, voxels can have values 0, 1 and 5. Voxels with
    value 0 will never be at the center of a patch. Voxels with value 5 will
    have 5 times more chance of being at the center of a patch that voxels
    with a value of 1.

    Args:
        patch_size: See :class:`~torchio.data.PatchSampler`.
        probability_map: Name of the image in the input subject that will be
            used as a sampling probability map.

    Raises:
        RuntimeError: If the probability map is empty.

    Example:
        >>> import torchio as tio
        >>> subject = tio.Subject(
        ...     t1=tio.ScalarImage('t1_mri.nii.gz'),
        ...     sampling_map=tio.Image('sampling.nii.gz', type=tio.SAMPLING_MAP),
        ... )
        >>> patch_size = 64
        >>> sampler = tio.data.WeightedSampler(patch_size, 'sampling_map')
        >>> for patch in sampler(subject):
        ...     print(patch[tio.LOCATION])

    .. note:: The index of the center of a patch with even size :math:`s` is
        arbitrarily set to :math:`s/2`. This is an implementation detail that
        will typically not make any difference in practice.

    .. note:: Values of the probability map near the border will be set to 0 as
        the center of the patch cannot be at the border (unless the patch has
        size 1 or 2 along that axis).
    """

    def __init__(self, patch_size: TypeSpatialShape, probability_map: str | None):
        super().__init__(patch_size)
        self.probability_map_name = probability_map
        self.cdf = None

    def _generate_patches(self, subject: Subject, num_patches: int | None=None) -> Generator[Subject]:
        probability_map = self.get_probability_map(subject)
        probability_map_array = self.process_probability_map(probability_map, subject)
        cdf = self.get_cumulative_distribution_function(probability_map_array)
        patches_left = num_patches if num_patches is not None else True
        while patches_left:
            yield self.extract_patch(subject, probability_map_array, cdf)
            if num_patches is not None:
                patches_left -= 1

    def get_probability_map_image(self, subject: Subject) -> Image:
        assert self.probability_map_name is not None
        if self.probability_map_name in subject:
            return subject[self.probability_map_name]
        else:
            message = f'Image "{self.probability_map_name}" not found in subject: {subject}'
            raise KeyError(message)

    def get_probability_map(self, subject: Subject) -> torch.Tensor:
        data = self.get_probability_map_image(subject).data
        if torch.any(data < 0):
            message = f'Negative values found in probability map "{self.probability_map_name}"'
            raise ValueError(message)
        return data

    def process_probability_map(self, probability_map: torch.Tensor, subject: Subject) -> np.ndarray:
        data = probability_map[0].numpy().astype(np.float64)
        assert data.ndim == 3
        self.clear_probability_borders(data, self.patch_size)
        total = data.sum()
        if total == 0:
            half_patch_size = tuple((n // 2 for n in self.patch_size))
            message = f'Empty probability map found: {self.get_probability_map_image(subject).path}\nVoxels with positive probability might be near the image border.\nIf you suspect that this is the case, try adding a padding transform\nwith half the patch size: torchio.Pad({half_patch_size})'
            raise RuntimeError(message)
        data /= total
        return data

    @staticmethod
    def clear_probability_borders(probability_map: np.ndarray, patch_size: np.ndarray) -> None:
        crop_ini = patch_size // 2
        crop_fin = (patch_size - 1) // 2
        crop_i, crop_j, crop_k = crop_ini
        probability_map[:crop_i, :, :] = 0
        probability_map[:, :crop_j, :] = 0
        probability_map[:, :, :crop_k] = 0
        crop_i, crop_j, crop_k = crop_fin.tolist()
        if crop_i:
            probability_map[-crop_i:, :, :] = 0
        if crop_j:
            probability_map[:, -crop_j:, :] = 0
        if crop_k:
            probability_map[:, :, -crop_k:] = 0

    @staticmethod
    def get_cumulative_distribution_function(probability_map: np.ndarray) -> np.ndarray:
        """Return the cumulative distribution function of a probability map."""
        flat_map = probability_map.flatten()
        flat_map_normalized = flat_map / flat_map.sum()
        cdf = np.cumsum(flat_map_normalized)
        return cdf

    def extract_patch(self, subject: Subject, probability_map: np.ndarray, cdf: np.ndarray) -> Subject:
        i, j, k = self.get_random_index_ini(probability_map, cdf)
        index_ini = (i, j, k)
        si, sj, sk = self.patch_size
        patch_size = (int(si), int(sj), int(sk))
        cropped_subject = self.crop(subject, index_ini, patch_size)
        return cropped_subject

    def get_random_index_ini(self, probability_map: np.ndarray, cdf: np.ndarray) -> np.ndarray:
        center = self.sample_probability_map(probability_map, cdf)
        assert np.all(center >= 0)
        index_ini = center - self.patch_size // 2
        assert np.all(index_ini >= 0)
        return index_ini

    @classmethod
    def sample_probability_map(cls, probability_map: np.ndarray, cdf: np.ndarray) -> np.ndarray:
        """Inverse transform sampling.

        Example:
            >>> probability_map = np.array(
            ...    ((0,0,1,1,5,2,1,1,0),
            ...     (2,2,2,2,2,2,2,2,2)))
            >>> probability_map
            array([[0, 0, 1, 1, 5, 2, 1, 1, 0],
                   [2, 2, 2, 2, 2, 2, 2, 2, 2]])
            >>> histogram = np.zeros_like(probability_map)
            >>> for _ in range(100000):
            ...     histogram[WeightedSampler.sample_probability_map(probability_map, cdf)] += 1  # doctest:+SKIP
            ...
            >>> histogram  # doctest:+SKIP
            array([[    0,     0,  3479,  3478, 17121,  7023,  3355,  3378,     0],
                   [ 6808,  6804,  6942,  6809,  6946,  6988,  7002,  6826,  7041]])
        """
        random_number = max(MIN_FLOAT_32, torch.rand(1).item()) * cdf[-1]
        random_location_index = np.searchsorted(cdf, random_number)
        center = np.unravel_index(random_location_index, probability_map.shape)
        probability = probability_map[center]
        if probability <= 0:
            message = 'Error retrieving probability in weighted sampler. Please report this issue at https://github.com/TorchIO-project/torchio/issues/new?labels=bug&template=bug_report.md'
            raise RuntimeError(message)
        return np.array(center)

def get_probability_map(self, subject: Subject) -> torch.Tensor:
    data = self.get_probability_map_image(subject).data
    if torch.any(data < 0):
        message = f'Negative values found in probability map "{self.probability_map_name}"'
        raise ValueError(message)
    return data

def process_probability_map(self, probability_map: torch.Tensor, subject: Subject) -> np.ndarray:
    data = probability_map[0].numpy().astype(np.float64)
    assert data.ndim == 3
    self.clear_probability_borders(data, self.patch_size)
    total = data.sum()
    if total == 0:
        half_patch_size = tuple((n // 2 for n in self.patch_size))
        message = f'Empty probability map found: {self.get_probability_map_image(subject).path}\nVoxels with positive probability might be near the image border.\nIf you suspect that this is the case, try adding a padding transform\nwith half the patch size: torchio.Pad({half_patch_size})'
        raise RuntimeError(message)
    data /= total
    return data

class GridAggregator:
    """Aggregate patches for dense inference.

    This class is typically used to build a volume made of patches after
    inference of batches extracted by a :class:`~torchio.data.GridSampler`.

    Args:
        sampler: Instance of :class:`~torchio.data.GridSampler` used to
            extract the patches.
        overlap_mode: If ``'crop'``, the overlapping predictions will be
            cropped. If ``'average'``, the predictions in the overlapping areas
            will be averaged with equal weights. If ``'hann'``, the predictions
            in the overlapping areas will be weighted with a Hann window
            function. See the `grid aggregator tests`_ for a raw visualization
            of the three modes.

    .. _grid aggregator tests: https://github.com/TorchIO-project/torchio/blob/main/tests/data/inference/test_aggregator.py

    .. note:: Adapted from NiftyNet. See `this NiftyNet tutorial
        <https://niftynet.readthedocs.io/en/dev/window_sizes.html>`_ for more
        information about patch-based sampling.
    """

    def __init__(self, sampler: GridSampler, overlap_mode: str='crop'):
        subject = sampler.subject
        self.volume_padded = sampler.padding_mode is not None
        self.spatial_shape = subject.spatial_shape
        self._output_tensor: torch.Tensor | None = None
        self.patch_overlap = sampler.patch_overlap
        self.patch_size = sampler.patch_size
        self._parse_overlap_mode(overlap_mode)
        self.overlap_mode = overlap_mode
        self._avgmask_tensor: torch.Tensor | None = None
        self._hann_window: torch.Tensor | None = None

    @staticmethod
    def _parse_overlap_mode(overlap_mode):
        if overlap_mode not in ('crop', 'average', 'hann'):
            message = f'Overlap mode must be "crop", "average" or "hann" but  "{overlap_mode}" was passed'
            raise ValueError(message)

    def _crop_patch(self, patch: torch.Tensor, location: np.ndarray, overlap: np.ndarray) -> tuple[torch.Tensor, np.ndarray]:
        half_overlap = overlap // 2
        index_ini, index_fin = (location[:3], location[3:])
        crop_ini: np.ndarray = half_overlap.copy()
        crop_fin: np.ndarray = half_overlap.copy()
        if self.volume_padded:
            pass
        else:
            crop_ini *= index_ini > 0
            crop_fin *= index_fin != self.spatial_shape
        new_index_ini = index_ini + crop_ini
        new_index_fin = index_fin - crop_fin
        new_location = np.hstack((new_index_ini, new_index_fin))
        patch_size = np.asarray(patch.shape[-3:], dtype=int)
        crop_fin = crop_fin.astype(int)
        i_ini, j_ini, k_ini = crop_ini
        i_fin, j_fin, k_fin = patch_size - crop_fin
        i_ini = int(i_ini)
        j_ini = int(j_ini)
        k_ini = int(k_ini)
        i_fin = int(i_fin)
        j_fin = int(j_fin)
        k_fin = int(k_fin)
        cropped_patch = patch[:, i_ini:i_fin, j_ini:j_fin, k_ini:k_fin]
        return (cropped_patch, new_location)

    def _initialize_output_tensor(self, batch: torch.Tensor) -> None:
        if self._output_tensor is not None:
            return
        num_channels = batch.shape[CHANNELS_DIMENSION]
        self._output_tensor = torch.zeros(num_channels, *self.spatial_shape, dtype=batch.dtype)

    def _initialize_avgmask_tensor(self, batch: torch.Tensor) -> None:
        if self._avgmask_tensor is not None:
            return
        num_channels = batch.shape[CHANNELS_DIMENSION]
        self._avgmask_tensor = torch.zeros(num_channels, *self.spatial_shape, dtype=batch.dtype)

    @staticmethod
    def _get_hann_window(patch_size) -> torch.Tensor:
        hann_window_3d = torch.as_tensor([1])
        for spatial_dim, size in enumerate(patch_size):
            window_shape = np.ones_like(patch_size)
            window_shape[spatial_dim] = size
            hann_window_1d = torch.hann_window(size + 2, periodic=False)
            hann_window_1d = hann_window_1d[1:-1].view(*window_shape)
            hann_window_3d = hann_window_3d * hann_window_1d
        return hann_window_3d

    def _initialize_hann_window(self) -> None:
        if self._hann_window is not None:
            return
        self._hann_window = self._get_hann_window(self.patch_size)

    def add_batch(self, batch_tensor: torch.Tensor, locations: torch.Tensor) -> None:
        """Add batch processed by a CNN to the output prediction volume.

        Args:
            batch_tensor: 5D tensor, typically the output of a convolutional
                neural network, e.g. ``batch['image'][torchio.DATA]``.
            locations: 2D tensor with shape :math:`(B, 6)` representing the
                patch indices in the original image. They are typically
                extracted using ``batch[torchio.LOCATION]``.
        """
        batch = batch_tensor.cpu()
        locations_array = locations.cpu().numpy()
        patch_sizes = locations_array[:, 3:] - locations_array[:, :3]
        assert len(np.unique(patch_sizes, axis=0)) == 1
        input_spatial_shape = tuple(batch.shape[-3:])
        target_spatial_shape = tuple(patch_sizes[0])
        if input_spatial_shape != target_spatial_shape:
            message = f'The shape of the input batch, {input_spatial_shape}, does not match the shape of the target location, which is {target_spatial_shape}'
            raise RuntimeError(message)
        self._initialize_output_tensor(batch)
        assert isinstance(self._output_tensor, torch.Tensor)
        if self.overlap_mode == 'crop':
            for patch, location in zip(batch, locations_array):
                cropped_patch, new_location = self._crop_patch(patch, location, self.patch_overlap)
                i_ini, j_ini, k_ini, i_fin, j_fin, k_fin = new_location
                self._output_tensor[:, i_ini:i_fin, j_ini:j_fin, k_ini:k_fin] = cropped_patch
        elif self.overlap_mode == 'average':
            self._initialize_avgmask_tensor(batch)
            assert isinstance(self._avgmask_tensor, torch.Tensor)
            for patch, location in zip(batch, locations):
                i_ini, j_ini, k_ini, i_fin, j_fin, k_fin = location
                self._output_tensor[:, i_ini:i_fin, j_ini:j_fin, k_ini:k_fin] += patch
                self._avgmask_tensor[:, i_ini:i_fin, j_ini:j_fin, k_ini:k_fin] += 1
        elif self.overlap_mode == 'hann':
            self._initialize_avgmask_tensor(batch)
            self._initialize_hann_window()
            if self._output_tensor.dtype != torch.float32:
                self._output_tensor = self._output_tensor.float()
            assert isinstance(self._avgmask_tensor, torch.Tensor)
            if self._avgmask_tensor.dtype != torch.float32:
                self._avgmask_tensor = self._avgmask_tensor.float()
            for patch, location in zip(batch, locations):
                i_ini, j_ini, k_ini, i_fin, j_fin, k_fin = location
                patch = patch * self._hann_window
                self._output_tensor[:, i_ini:i_fin, j_ini:j_fin, k_ini:k_fin] += patch
                assert self._hann_window is not None
                self._avgmask_tensor[:, i_ini:i_fin, j_ini:j_fin, k_ini:k_fin] += self._hann_window

    def get_output_tensor(self) -> torch.Tensor:
        """Get the aggregated volume after dense inference."""
        assert isinstance(self._output_tensor, torch.Tensor)
        if self._output_tensor.dtype == torch.int64:
            message = 'Medical image frameworks such as ITK do not support int64. Casting to int32...'
            warnings.warn(message, RuntimeWarning, stacklevel=2)
            self._output_tensor = self._output_tensor.type(torch.int32)
        if self.overlap_mode in ['average', 'hann']:
            assert isinstance(self._avgmask_tensor, torch.Tensor)
            output = torch.true_divide(self._output_tensor, self._avgmask_tensor)
        else:
            output = self._output_tensor
        if self.volume_padded:
            from ...transforms import Crop
            border = self.patch_overlap // 2
            cropping = border.repeat(2)
            crop = Crop(cropping)
            return crop(output)
        else:
            return output

def add_batch(self, batch_tensor: torch.Tensor, locations: torch.Tensor) -> None:
    """Add batch processed by a CNN to the output prediction volume.

        Args:
            batch_tensor: 5D tensor, typically the output of a convolutional
                neural network, e.g. ``batch['image'][torchio.DATA]``.
            locations: 2D tensor with shape :math:`(B, 6)` representing the
                patch indices in the original image. They are typically
                extracted using ``batch[torchio.LOCATION]``.
        """
    batch = batch_tensor.cpu()
    locations_array = locations.cpu().numpy()
    patch_sizes = locations_array[:, 3:] - locations_array[:, :3]
    assert len(np.unique(patch_sizes, axis=0)) == 1
    input_spatial_shape = tuple(batch.shape[-3:])
    target_spatial_shape = tuple(patch_sizes[0])
    if input_spatial_shape != target_spatial_shape:
        message = f'The shape of the input batch, {input_spatial_shape}, does not match the shape of the target location, which is {target_spatial_shape}'
        raise RuntimeError(message)
    self._initialize_output_tensor(batch)
    assert isinstance(self._output_tensor, torch.Tensor)
    if self.overlap_mode == 'crop':
        for patch, location in zip(batch, locations_array):
            cropped_patch, new_location = self._crop_patch(patch, location, self.patch_overlap)
            i_ini, j_ini, k_ini, i_fin, j_fin, k_fin = new_location
            self._output_tensor[:, i_ini:i_fin, j_ini:j_fin, k_ini:k_fin] = cropped_patch
    elif self.overlap_mode == 'average':
        self._initialize_avgmask_tensor(batch)
        assert isinstance(self._avgmask_tensor, torch.Tensor)
        for patch, location in zip(batch, locations):
            i_ini, j_ini, k_ini, i_fin, j_fin, k_fin = location
            self._output_tensor[:, i_ini:i_fin, j_ini:j_fin, k_ini:k_fin] += patch
            self._avgmask_tensor[:, i_ini:i_fin, j_ini:j_fin, k_ini:k_fin] += 1
    elif self.overlap_mode == 'hann':
        self._initialize_avgmask_tensor(batch)
        self._initialize_hann_window()
        if self._output_tensor.dtype != torch.float32:
            self._output_tensor = self._output_tensor.float()
        assert isinstance(self._avgmask_tensor, torch.Tensor)
        if self._avgmask_tensor.dtype != torch.float32:
            self._avgmask_tensor = self._avgmask_tensor.float()
        for patch, location in zip(batch, locations):
            i_ini, j_ini, k_ini, i_fin, j_fin, k_fin = location
            patch = patch * self._hann_window
            self._output_tensor[:, i_ini:i_fin, j_ini:j_fin, k_ini:k_fin] += patch
            assert self._hann_window is not None
            self._avgmask_tensor[:, i_ini:i_fin, j_ini:j_fin, k_ini:k_fin] += self._hann_window

class MedMNIST(SubjectsDataset):
    """3D MedMNIST v2 datasets.

    Datasets from `MedMNIST v2: A Large-Scale Lightweight Benchmark for 2D and
    3D Biomedical Image Classification <https://arxiv.org/abs/2110.14795>`_.

    Please check the `MedMNIST website <https://medmnist.com/>`_ for more
    information, inclusing the license.

    Args:
        split: Dataset split. Should be ``'train'``, ``'val'`` or ``'test'``.
    """
    BASE_URL = 'https://zenodo.org/record/5208230/files'
    SPLITS = ('train', 'training', 'val', 'validation', 'test', 'testing')

    def __init__(self, split, **kwargs):
        if split not in self.SPLITS:
            raise ValueError(f'The split must be one of {self.SPLITS}')
        split = 'train' if split == 'training' else split
        split = 'val' if split == 'validation' else split
        split = 'test' if split == 'testing' else split
        url = f'{self.BASE_URL}/{self.filename}?download=1'
        download_root = get_torchio_cache_dir() / 'MedMNIST'
        download_url(url, download_root, filename=self.filename)
        path = download_root / self.filename
        npz_file = np.load(path)
        images = npz_file[f'{split}_images']
        labels = npz_file[f'{split}_labels']
        subjects = []
        for image, label in zip(images, labels):
            image = ScalarImage(tensor=image[np.newaxis])
            subject = Subject(image=image, labels=torch.from_numpy(label))
            subjects.append(subject)
        super().__init__(subjects, **kwargs)

    @property
    def filename(self):
        return f'{self.__class__.__name__.lower()}.npz'

@property
def filename(self):
    return f'{self.__class__.__name__.lower()}.npz'

class Transform(ABC):
    """Abstract class for all TorchIO transforms.

    When called, the input can be an instance of
    :class:`torchio.Subject`,
    :class:`torchio.Image`,
    :class:`numpy.ndarray`,
    :class:`torch.Tensor`,
    :class:`SimpleITK.Image`,
    or :class:`dict` containing 4D tensors as values.

    All subclasses must overwrite
    :meth:`~torchio.transforms.Transform.apply_transform`,
    which takes an instance of :class:`~torchio.Subject`,
    modifies it and returns the result.

    Args:
        p: Probability that this transform will be applied.
        copy: Make a deep copy of the input before applying the transform.
        include: Sequence of strings with the names of the only images to which
            the transform will be applied.
            Mandatory if the input is a :class:`dict`.
        exclude: Sequence of strings with the names of the images to which the
            the transform will not be applied, apart from the ones that are
            excluded because of the transform type.
            For example, if a subject includes an MRI, a CT and a label map,
            and the CT is added to the list of exclusions of an intensity
            transform such as :class:`~torchio.transforms.RandomBlur`,
            the transform will be only applied to the MRI, as the label map is
            excluded by default by spatial transforms.
        keep: Dictionary with the names of the input images that will be kept
            in the output and their new names. For example:
            ``{'t1': 't1_original'}``. This might be useful for autoencoders
            or registration tasks.
        parse_input: If ``True``, the input will be converted to an instance of
            :class:`~torchio.Subject`. This is used internally by some special
            transforms like
            :class:`~torchio.transforms.augmentation.composition.Compose`.
        label_keys: If the input is a dictionary, names of images that
            correspond to label maps.
    """

    def __init__(self, p: float=1, copy: bool=True, include: TypeKeys=None, exclude: TypeKeys=None, keys: TypeKeys=None, keep: dict[str, str] | None=None, parse_input: bool=True, label_keys: TypeKeys=None):
        self.probability = self.parse_probability(p)
        self.copy = copy
        if keys is not None:
            message = 'The "keys" argument is deprecated and will be removed in the future. Use "include" instead'
            warnings.warn(message, FutureWarning, stacklevel=2)
            include = keys
        self.include, self.exclude = self.parse_include_and_exclude_keys(include, exclude, label_keys)
        self.keep = keep
        self.parse_input = parse_input
        self.label_keys = label_keys
        self.args_names: list[str] = []

    def __call__(self, data: InputType) -> InputType:
        """Transform data and return a result of the same type.

        Args:
            data: Instance of :class:`torchio.Subject`, 4D
                :class:`torch.Tensor` or :class:`numpy.ndarray` with dimensions
                :math:`(C, W, H, D)`, where :math:`C` is the number of channels
                and :math:`W, H, D` are the spatial dimensions. If the input is
                a tensor, the affine matrix will be set to identity. Other
                valid input types are a SimpleITK image, a
                :class:`torchio.Image`, a NiBabel Nifti1 image or a
                :class:`dict`. The output type is the same as the input type.
        """
        if torch.rand(1).item() > self.probability:
            return data
        if self.parse_input:
            data_parser = DataParser(data, keys=self.include, label_keys=self.label_keys)
            subject = data_parser.get_subject()
        else:
            subject = data
        if self.keep is not None:
            images_to_keep = {}
            for name, new_name in self.keep.items():
                images_to_keep[new_name] = copy.deepcopy(subject[name])
        if self.copy:
            subject = copy.deepcopy(subject)
        with np.errstate(all='raise', under='ignore'):
            transformed = self.apply_transform(subject)
        if self.keep is not None:
            for name, image in images_to_keep.items():
                transformed.add_image(image, name)
        if self.parse_input:
            self.add_transform_to_subject_history(transformed)
            for image in transformed.get_images(intensity_only=False):
                ndim = image.data.ndim
                assert ndim == 4, f'Output of {self.name} is {ndim}D'
            output = data_parser.get_output(transformed)
        else:
            output = transformed
        return output

    def __repr__(self):
        if hasattr(self, 'args_names'):
            names = self.args_names
            args_strings = [f'{arg}={getattr(self, arg)}' for arg in names]
            if hasattr(self, 'invert_transform') and self.invert_transform:
                args_strings.append('invert=True')
            args_string = ', '.join(args_strings)
            return f'{self.name}({args_string})'
        else:
            return super().__repr__()

    def get_base_args(self) -> dict:
        """Provides easy access to the arguments used to instantiate the base class
        (:class:`~torchio.transforms.transform.Transform`) of any transform.

        This method is particularly useful when a new transform can be represented as a variant
        of an existing transform (e.g. all random transforms), allowing for seamless instantiation
        of the existing transform with the same arguments as the new transform during `apply_transform`.

        Note: The `p` argument (probability of applying the transform) is excluded to avoid
        multiplying the probability of both existing and new transform.
        """
        return {'copy': self.copy, 'include': self.include, 'exclude': self.exclude, 'keep': self.keep, 'parse_input': self.parse_input, 'label_keys': self.label_keys}

    def add_base_args(self, arguments, overwrite_on_existing: bool=False):
        """Add the init args to existing arguments"""
        for key, value in self.get_base_args().items():
            if key in arguments and (not overwrite_on_existing):
                continue
            arguments[key] = value
        return arguments

    @property
    def name(self):
        return self.__class__.__name__

    @abstractmethod
    def apply_transform(self, subject: Subject) -> Subject:
        raise NotImplementedError

    def add_transform_to_subject_history(self, subject):
        from . import Compose
        from . import CropOrPad
        from . import EnsureShapeMultiple
        from . import OneOf
        from .augmentation import RandomTransform
        from .preprocessing import Resize
        from .preprocessing import SequentialLabels
        call_others = (RandomTransform, Compose, OneOf, CropOrPad, EnsureShapeMultiple, SequentialLabels, Resize)
        if not isinstance(self, call_others):
            subject.add_transform(self, self._get_reproducing_arguments())

    @staticmethod
    def to_range(n, around):
        if around is None:
            return (0, n)
        else:
            return (around - n, around + n)

    def parse_params(self, params, around, name, make_ranges=True, **kwargs):
        params = to_tuple(params)
        if len(params) == 1 or (len(params) == 2 and make_ranges):
            params *= 3
        if len(params) == 3 and make_ranges:
            items = [self.to_range(n, around) for n in params]
            params = [n for prange in items for n in prange]
        if make_ranges:
            if len(params) != 6:
                message = f'If "{name}" is a sequence, it must have length 2, 3 or 6, not {len(params)}'
                raise ValueError(message)
            for param_range in zip(params[::2], params[1::2]):
                self._parse_range(param_range, name, **kwargs)
        return tuple(params)

    @staticmethod
    def _parse_range(nums_range: TypeNumber | tuple[TypeNumber, TypeNumber], name: str, min_constraint: TypeNumber | None=None, max_constraint: TypeNumber | None=None, type_constraint: type | None=None) -> tuple[TypeNumber, TypeNumber]:
        """Adapted from :class:`torchvision.transforms.RandomRotation`.

        Args:
            nums_range: Tuple of two numbers :math:`(n_{min}, n_{max})`,
                where :math:`n_{min} \\leq n_{max}`.
                If a single positive number :math:`n` is provided,
                :math:`n_{min} = -n` and :math:`n_{max} = n`.
            name: Name of the parameter, so that an informative error message
                can be printed.
            min_constraint: Minimal value that :math:`n_{min}` can take,
                default is None, i.e. there is no minimal value.
            max_constraint: Maximal value that :math:`n_{max}` can take,
                default is None, i.e. there is no maximal value.
            type_constraint: Precise type that :math:`n_{max}` and
                :math:`n_{min}` must take.

        Returns:
            A tuple of two numbers :math:`(n_{min}, n_{max})`.

        Raises:
            ValueError: if :attr:`nums_range` is negative
            ValueError: if :math:`n_{max}` or :math:`n_{min}` is not a number
            ValueError: if :math:`n_{max} \\lt n_{min}`
            ValueError: if :attr:`min_constraint` is not None and
                :math:`n_{min}` is smaller than :attr:`min_constraint`
            ValueError: if :attr:`max_constraint` is not None and
                :math:`n_{max}` is greater than :attr:`max_constraint`
            ValueError: if :attr:`type_constraint` is not None and
                :math:`n_{max}` and :math:`n_{max}` are not of type
                :attr:`type_constraint`.
        """
        if isinstance(nums_range, numbers.Number):
            if nums_range < 0:
                raise ValueError(f'If {name} is a single number, it must be positive, not {nums_range}')
            if min_constraint is not None and nums_range < min_constraint:
                raise ValueError(f'If {name} is a single number, it must be greater than {min_constraint}, not {nums_range}')
            if max_constraint is not None and nums_range > max_constraint:
                raise ValueError(f'If {name} is a single number, it must be smaller than {max_constraint}, not {nums_range}')
            if type_constraint is not None:
                if not isinstance(nums_range, type_constraint):
                    raise ValueError(f'If {name} is a single number, it must be of type {type_constraint}, not {nums_range}')
            min_range = -nums_range if min_constraint is None else nums_range
            return (min_range, nums_range)
        try:
            min_value, max_value = nums_range
        except (TypeError, ValueError) as err:
            message = f'If {name} is not a single number, it must be a sequence of len 2, not {nums_range}'
            raise ValueError(message) from err
        min_is_number = isinstance(min_value, numbers.Number)
        max_is_number = isinstance(max_value, numbers.Number)
        if not min_is_number or not max_is_number:
            message = f'{name} values must be numbers, not {nums_range}'
            raise ValueError(message)
        if min_value > max_value:
            raise ValueError(f'If {name} is a sequence, the second value must be equal or greater than the first, but it is {nums_range}')
        if min_constraint is not None and min_value < min_constraint:
            raise ValueError(f'If {name} is a sequence, the first value must be greater than {min_constraint}, but it is {min_value}')
        if max_constraint is not None and max_value > max_constraint:
            raise ValueError(f'If {name} is a sequence, the second value must be smaller than {max_constraint}, but it is {max_value}')
        if type_constraint is not None:
            min_type_ok = isinstance(min_value, type_constraint)
            max_type_ok = isinstance(max_value, type_constraint)
            if not min_type_ok or not max_type_ok:
                raise ValueError(f'If "{name}" is a sequence, its values must be of type "{type_constraint}", not "{type(nums_range)}"')
        return nums_range

    @staticmethod
    def parse_interpolation(interpolation: str) -> str:
        if not isinstance(interpolation, str):
            itype = type(interpolation)
            raise TypeError(f'Interpolation must be a string, not {itype}')
        interpolation = interpolation.lower()
        is_string = isinstance(interpolation, str)
        supported_values = [key.name.lower() for key in Interpolation]
        is_supported = interpolation.lower() in supported_values
        if is_string and is_supported:
            return interpolation
        message = f'Interpolation "{interpolation}" of type {type(interpolation)} must be a string among the supported values: {supported_values}'
        raise ValueError(message)

    @staticmethod
    def parse_probability(probability: float) -> float:
        is_number = isinstance(probability, numbers.Number)
        if not (is_number and 0 <= probability <= 1):
            message = f'Probability must be a number in [0, 1], not {probability}'
            raise ValueError(message)
        return probability

    @staticmethod
    def parse_include_and_exclude_keys(include: TypeKeys, exclude: TypeKeys, label_keys: TypeKeys) -> tuple[TypeKeys, TypeKeys]:
        if include is not None and exclude is not None:
            raise ValueError('Include and exclude cannot both be specified')
        Transform.validate_keys_sequence(include, 'include')
        Transform.validate_keys_sequence(exclude, 'exclude')
        Transform.validate_keys_sequence(label_keys, 'label_keys')
        return (include, exclude)

    @staticmethod
    def validate_keys_sequence(keys: TypeKeys, name: str) -> None:
        """Ensure that the input is not a string but a sequence of strings."""
        if keys is None:
            return
        if isinstance(keys, str):
            message = f'"{name}" must be a sequence of strings, not a string "{keys}"'
            raise ValueError(message)
        if not is_iterable(keys):
            message = f'"{name}" must be a sequence of strings, not {type(keys)}'
            raise ValueError(message)

    @staticmethod
    def nib_to_sitk(data: TypeData, affine: TypeData) -> sitk.Image:
        return nib_to_sitk(data, affine)

    @staticmethod
    def sitk_to_nib(image: sitk.Image) -> TypeDataAffine:
        return sitk_to_nib(image)

    def _get_reproducing_arguments(self):
        """Return a dictionary with the arguments that would be necessary to
        reproduce the transform exactly."""
        reproducing_arguments = {'include': self.include, 'exclude': self.exclude, 'copy': self.copy}
        args_names = {name: getattr(self, name) for name in self.args_names}
        reproducing_arguments.update(args_names)
        return reproducing_arguments

    def is_invertible(self):
        return hasattr(self, 'invert_transform')

    def inverse(self):
        if not self.is_invertible():
            raise RuntimeError(f'{self.name} is not invertible')
        new = copy.deepcopy(self)
        new.invert_transform = not self.invert_transform
        return new

    @staticmethod
    @contextmanager
    def _use_seed(seed):
        """Perform an operation using a specific seed for the PyTorch RNG."""
        torch_rng_state = torch.random.get_rng_state()
        torch.manual_seed(seed)
        yield
        torch.random.set_rng_state(torch_rng_state)

    @staticmethod
    def get_sitk_interpolator(interpolation: str) -> int:
        return get_sitk_interpolator(interpolation)

    @staticmethod
    def parse_bounds(bounds_parameters: TypeBounds) -> TypeSixBounds | None:
        if bounds_parameters is None:
            return None
        try:
            bounds_parameters = tuple(bounds_parameters)
        except TypeError:
            bounds_parameters = (bounds_parameters,)
        for number in bounds_parameters:
            if not isinstance(number, (int, np.integer)) or number < 0:
                message = f'Bounds values must be integers greater or equal to zero, not "{bounds_parameters}" of type {type(number)}'
                raise ValueError(message)
        bounds_parameters_tuple = tuple((int(n) for n in bounds_parameters))
        bounds_parameters_length = len(bounds_parameters_tuple)
        if bounds_parameters_length == 6:
            return bounds_parameters_tuple
        if bounds_parameters_length == 1:
            return 6 * bounds_parameters_tuple
        if bounds_parameters_length == 3:
            repeat = np.repeat(bounds_parameters_tuple, 2).tolist()
            return tuple(repeat)
        message = f'Bounds parameter must be an integer or a tuple of 3 or 6 integers, not {bounds_parameters_tuple}'
        raise ValueError(message)

    @staticmethod
    def ones(tensor: torch.Tensor) -> torch.Tensor:
        return torch.ones_like(tensor, dtype=torch.bool)

    @staticmethod
    def mean(tensor: torch.Tensor) -> torch.Tensor:
        mask = tensor > tensor.float().mean()
        return mask

    def get_mask_from_masking_method(self, masking_method: TypeMaskingMethod, subject: Subject, tensor: torch.Tensor, labels: Sequence[int] | None=None) -> torch.Tensor:
        if masking_method is None:
            return self.ones(tensor)
        elif callable(masking_method):
            return masking_method(tensor)
        elif type(masking_method) is str:
            in_subject = masking_method in subject
            if in_subject and isinstance(subject[masking_method], LabelMap):
                if labels is None:
                    return subject[masking_method].data.bool()
                else:
                    mask_data = subject[masking_method].data
                    volumes = [mask_data == label for label in labels]
                    return torch.stack(volumes).sum(0).bool()
            possible_axis = masking_method.capitalize()
            if possible_axis in ANATOMICAL_AXES:
                return self.get_mask_from_anatomical_label(possible_axis, tensor)
        elif type(masking_method) in (tuple, list, int):
            return self.get_mask_from_bounds(masking_method, tensor)
        first_anat_axes = tuple((s[0] for s in ANATOMICAL_AXES))
        message = f'Masking method must be one of:\n 1) A callable object, such as a function\n 2) The name of a label map in the subject ({subject.get_images_names()})\n 3) An anatomical label {ANATOMICAL_AXES + first_anat_axes}\n 4) A bounds parameter (int, tuple of 3 ints, or tuple of 6 ints)\n The passed value, "{masking_method}", of type "{type(masking_method)}", is not valid'
        raise ValueError(message)

    @staticmethod
    def get_mask_from_anatomical_label(anatomical_label: str, tensor: torch.Tensor) -> torch.Tensor:
        anatomical_label = anatomical_label.capitalize()
        if anatomical_label not in ANATOMICAL_AXES:
            message = f'Anatomical label must be one of {ANATOMICAL_AXES} not {anatomical_label}'
            raise ValueError(message)
        mask = torch.zeros_like(tensor, dtype=torch.bool)
        _, width, height, depth = tensor.shape
        if anatomical_label == 'Right':
            mask[:, width // 2:] = True
        elif anatomical_label == 'Left':
            mask[:, :width // 2] = True
        elif anatomical_label == 'Anterior':
            mask[:, :, height // 2:] = True
        elif anatomical_label == 'Posterior':
            mask[:, :, :height // 2] = True
        elif anatomical_label == 'Superior':
            mask[:, :, :, depth // 2:] = True
        elif anatomical_label == 'Inferior':
            mask[:, :, :, :depth // 2] = True
        return mask

    def get_mask_from_bounds(self, bounds_parameters: TypeBounds, tensor: torch.Tensor) -> torch.Tensor:
        bounds_parameters = self.parse_bounds(bounds_parameters)
        assert bounds_parameters is not None
        low = bounds_parameters[::2]
        high = bounds_parameters[1::2]
        i0, j0, k0 = low
        i1, j1, k1 = np.array(tensor.shape[1:]) - high
        mask = torch.zeros_like(tensor, dtype=torch.bool)
        mask[:, i0:i1, j0:j1, k0:k1] = True
        return mask

@staticmethod
def mean(tensor: torch.Tensor) -> torch.Tensor:
    mask = tensor > tensor.float().mean()
    return mask

class RandomTransform(Transform):
    """Base class for stochastic augmentation transforms.

    Args:
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def parse_degrees(self, degrees: TypeRangeFloat) -> tuple[float, float]:
        return self._parse_range(degrees, 'degrees')

    def parse_translation(self, translation: TypeRangeFloat) -> tuple[float, float]:
        return self._parse_range(translation, 'translation')

    @staticmethod
    def sample_uniform(a: float, b: float) -> float:
        return torch.FloatTensor(1).uniform_(a, b).item()

    @staticmethod
    def _get_random_seed() -> int:
        """Generate a random seed.

        Returns:
            A random seed as an int.
        """
        return int(torch.randint(0, 2 ** 31, (1,)).item())

    @staticmethod
    def sample_uniform_sextet(params: TypeSextetFloat) -> TypeTripletFloat:
        results = []
        for a, b in zip(params[::2], params[1::2]):
            results.append(RandomTransform.sample_uniform(a, b))
        sx, sy, sz = results
        return (sx, sy, sz)

@staticmethod
def sample_uniform(a: float, b: float) -> float:
    return torch.FloatTensor(1).uniform_(a, b).item()

class Affine(SpatialTransform):
    """Apply affine transformation.

    Args:
        scales: Tuple :math:`(s_1, s_2, s_3)` defining the
            scaling values along each dimension.
        degrees: Tuple :math:`(\\theta_1, \\theta_2, \\theta_3)` defining the
            rotation around each axis.
        translation: Tuple :math:`(t_1, t_2, t_3)` defining the
            translation in mm along each axis.
        center: If ``'image'``, rotations and scaling will be performed around
            the image center. If ``'origin'``, rotations and scaling will be
            performed around the origin in world coordinates.
        default_pad_value: As the image is rotated, some values near the
            borders will be undefined.
            If ``'minimum'``, the fill value will be the image minimum.
            If ``'mean'``, the fill value is the mean of the border values.
            If ``'otsu'``, the fill value is the mean of the values at the
            border that lie under an
            `Otsu threshold <https://ieeexplore.ieee.org/document/4310076>`_.
            If it is a number, that value will be used.
            This parameter applies to intensity images only.
        default_pad_label: As the label map is rotated, some values near the
            borders will be undefined. This numeric value will be used to fill
            those undefined regions. This parameter applies to label maps only.
        image_interpolation: See :ref:`Interpolation`.
        label_interpolation: See :ref:`Interpolation`.
        check_shape: If ``True`` an error will be raised if the images are in
            different physical spaces. If ``False``, :attr:`center` should
            probably not be ``'image'`` but ``'center'``.
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.
    """

    def __init__(self, scales: TypeTripletFloat, degrees: TypeTripletFloat, translation: TypeTripletFloat, center: str='image', default_pad_value: str | float='minimum', default_pad_label: int | float=0, image_interpolation: str='linear', label_interpolation: str='nearest', check_shape: bool=True, **kwargs):
        super().__init__(**kwargs)
        self.scales = self.parse_params(scales, None, 'scales', make_ranges=False, min_constraint=0)
        self.degrees = self.parse_params(degrees, None, 'degrees', make_ranges=False)
        self.translation = self.parse_params(translation, None, 'translation', make_ranges=False)
        if center not in ('image', 'origin'):
            message = f'Center argument must be "image" or "origin", not "{center}"'
            raise ValueError(message)
        self.center = center
        self.use_image_center = center == 'image'
        self.default_pad_value = _parse_default_value(default_pad_value)
        if not isinstance(default_pad_label, (int, float)):
            message = 'default_pad_label must be a number, '
            message += f'but it is "{default_pad_label}"'
            raise ValueError(message)
        self.default_pad_label = float(default_pad_label)
        self.image_interpolation = self.parse_interpolation(image_interpolation)
        self.label_interpolation = self.parse_interpolation(label_interpolation)
        self.invert_transform = False
        self.check_shape = check_shape
        self.args_names = ['scales', 'degrees', 'translation', 'center', 'default_pad_value', 'default_pad_label', 'image_interpolation', 'label_interpolation', 'check_shape']

    @staticmethod
    def _get_scaling_transform(scaling_params: Sequence[float], center_lps: TypeTripletFloat | None=None) -> sitk.ScaleTransform:
        transform = sitk.ScaleTransform(3)
        scaling_params_array = np.array(scaling_params).astype(float)
        transform.SetScale(scaling_params_array)
        if center_lps is not None:
            transform.SetCenter(center_lps)
        return transform

    @staticmethod
    def _get_rotation_transform(degrees: Sequence[float], translation: Sequence[float], center_lps: TypeTripletFloat | None=None) -> sitk.Euler3DTransform:

        def ras_to_lps(triplet: Sequence[float]):
            return np.array((-1, -1, 1), dtype=float) * np.asarray(triplet)
        transform = sitk.Euler3DTransform()
        radians = np.radians(degrees).tolist()
        radians_lps = ras_to_lps(radians)
        translation_lps = ras_to_lps(translation)
        transform.SetRotation(*radians_lps)
        transform.SetTranslation(translation_lps)
        if center_lps is not None:
            transform.SetCenter(center_lps)
        return transform

    def get_affine_transform(self, image):
        scaling = np.asarray(self.scales).copy()
        rotation = np.asarray(self.degrees).copy()
        translation = np.asarray(self.translation).copy()
        if image.is_2d():
            scaling[2] = 1
            rotation[:-1] = 0
        if self.use_image_center:
            center_lps = image.get_center(lps=True)
        else:
            center_lps = None
        scaling_transform = self._get_scaling_transform(scaling, center_lps=center_lps)
        rotation_transform = self._get_rotation_transform(rotation, translation, center_lps=center_lps)
        sitk_major_version = get_major_sitk_version()
        if sitk_major_version == 1:
            transform = sitk.Transform(3, sitk.sitkComposite)
            transform.AddTransform(scaling_transform)
            transform.AddTransform(rotation_transform)
        elif sitk_major_version == 2:
            transforms = [scaling_transform, rotation_transform]
            transform = sitk.CompositeTransform(transforms)
        transform = transform.GetInverse()
        if self.invert_transform:
            transform = transform.GetInverse()
        return transform

    def get_default_pad_value(self, tensor: torch.Tensor, sitk_image: sitk.Image) -> float:
        default_value: float
        if self.default_pad_value == 'minimum':
            default_value = tensor.min().item()
        elif self.default_pad_value == 'mean':
            default_value = get_borders_mean(sitk_image, filter_otsu=False)
        elif self.default_pad_value == 'otsu':
            default_value = get_borders_mean(sitk_image, filter_otsu=True)
        else:
            assert isinstance(self.default_pad_value, Number)
            default_value = float(self.default_pad_value)
        return default_value

    def apply_transform(self, subject: Subject) -> Subject:
        if self.check_shape:
            subject.check_consistent_spatial_shape()
        default_value: float
        for image in self.get_images(subject):
            transform = self.get_affine_transform(image)
            transformed_tensors = []
            for tensor in image.data:
                sitk_image = nib_to_sitk(tensor[np.newaxis], image.affine, force_3d=True)
                if image[TYPE] != INTENSITY:
                    interpolation = self.label_interpolation
                    default_value = self.default_pad_label
                else:
                    interpolation = self.image_interpolation
                    default_value = self.get_default_pad_value(tensor, sitk_image)
                transformed_tensor = self.apply_affine_transform(sitk_image, transform, interpolation, default_value)
                transformed_tensors.append(transformed_tensor)
            image.set_data(torch.stack(transformed_tensors))
        return subject

    def apply_affine_transform(self, sitk_image: sitk.Image, transform: sitk.Transform, interpolation: str, default_value: float) -> torch.Tensor:
        floating = reference = sitk_image
        resampler = sitk.ResampleImageFilter()
        resampler.SetInterpolator(self.get_sitk_interpolator(interpolation))
        resampler.SetReferenceImage(reference)
        resampler.SetDefaultPixelValue(float(default_value))
        resampler.SetOutputPixelType(sitk.sitkFloat32)
        resampler.SetTransform(transform)
        resampled = resampler.Execute(floating)
        np_array = sitk.GetArrayFromImage(resampled)
        np_array = np_array.transpose()
        tensor = torch.as_tensor(np_array)
        return tensor

def get_default_pad_value(self, tensor: torch.Tensor, sitk_image: sitk.Image) -> float:
    default_value: float
    if self.default_pad_value == 'minimum':
        default_value = tensor.min().item()
    elif self.default_pad_value == 'mean':
        default_value = get_borders_mean(sitk_image, filter_otsu=False)
    elif self.default_pad_value == 'otsu':
        default_value = get_borders_mean(sitk_image, filter_otsu=True)
    else:
        assert isinstance(self.default_pad_value, Number)
        default_value = float(self.default_pad_value)
    return default_value

def _flip_image(image, axes):
    spatial_axes = np.array(axes, int) + 1
    data = image.numpy()
    data = np.flip(data, axis=spatial_axes)
    data = np.ascontiguousarray(data)
    data = torch.as_tensor(data)
    image.set_data(data)

class RandomMotion(RandomTransform, IntensityTransform, FourierTransform):
    """Add random MRI motion artifact.

    Magnetic resonance images suffer from motion artifacts when the subject
    moves during image acquisition. This transform follows
    `Shaw et al., 2019 <http://proceedings.mlr.press/v102/shaw19a.html>`_ to
    simulate motion artifacts for data augmentation.

    Args:
        degrees: Tuple :math:`(a, b)` defining the rotation range in degrees of
            the simulated movements. The rotation angles around each axis are
            :math:`(\\theta_1, \\theta_2, \\theta_3)`,
            where :math:`\\theta_i \\sim \\mathcal{U}(a, b)`.
            If only one value :math:`d` is provided,
            :math:`\\theta_i \\sim \\mathcal{U}(-d, d)`.
            Larger values generate more distorted images.
        translation: Tuple :math:`(a, b)` defining the translation in mm of
            the simulated movements. The translations along each axis are
            :math:`(t_1, t_2, t_3)`,
            where :math:`t_i \\sim \\mathcal{U}(a, b)`.
            If only one value :math:`t` is provided,
            :math:`t_i \\sim \\mathcal{U}(-t, t)`.
            Larger values generate more distorted images.
        num_transforms: Number of simulated movements.
            Larger values generate more distorted images.
        image_interpolation: See :ref:`Interpolation`.
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.

    .. warning:: Large numbers of movements lead to longer execution times for
        3D images.
    """

    def __init__(self, degrees: Union[float, tuple[float, float]]=10, translation: Union[float, tuple[float, float]]=10, num_transforms: int=2, image_interpolation: str='linear', **kwargs):
        super().__init__(**kwargs)
        self.degrees_range = self.parse_degrees(degrees)
        self.translation_range = self.parse_translation(translation)
        if num_transforms < 1 or not isinstance(num_transforms, int):
            message = f'Number of transforms must be a strictly positive naturalnumber, not {num_transforms}'
            raise ValueError(message)
        self.num_transforms = num_transforms
        self.image_interpolation = self.parse_interpolation(image_interpolation)

    def apply_transform(self, subject: Subject) -> Subject:
        images_dict = self.get_images_dict(subject)
        if not images_dict:
            return subject
        arguments: dict[str, dict] = defaultdict(dict)
        for name, image in images_dict.items():
            params = self.get_params(self.degrees_range, self.translation_range, self.num_transforms, is_2d=image.is_2d())
            times_params, degrees_params, translation_params = params
            arguments['times'][name] = times_params
            arguments['degrees'][name] = degrees_params
            arguments['translation'][name] = translation_params
            arguments['image_interpolation'][name] = self.image_interpolation
        transform = Motion(**self.add_base_args(arguments))
        transformed = transform(subject)
        assert isinstance(transformed, Subject)
        return transformed

    def get_params(self, degrees_range: tuple[float, float], translation_range: tuple[float, float], num_transforms: int, perturbation: float=0.3, is_2d: bool=False) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        degrees_params = self.get_params_array(degrees_range, num_transforms)
        translation_params = self.get_params_array(translation_range, num_transforms)
        if is_2d:
            degrees_params[:, :-1] = 0
            translation_params[:, 2] = 0
        step = 1 / (num_transforms + 1)
        times = torch.arange(0, 1, step)[1:]
        noise = torch.FloatTensor(num_transforms)
        noise.uniform_(-step * perturbation, step * perturbation)
        times += noise
        times_params = times.numpy()
        return (times_params, degrees_params, translation_params)

    @staticmethod
    def get_params_array(nums_range: tuple[float, float], num_transforms: int):
        tensor = torch.FloatTensor(num_transforms, 3).uniform_(*nums_range)
        return tensor.numpy()

def get_params(self, degrees_range: tuple[float, float], translation_range: tuple[float, float], num_transforms: int, perturbation: float=0.3, is_2d: bool=False) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    degrees_params = self.get_params_array(degrees_range, num_transforms)
    translation_params = self.get_params_array(translation_range, num_transforms)
    if is_2d:
        degrees_params[:, :-1] = 0
        translation_params[:, 2] = 0
    step = 1 / (num_transforms + 1)
    times = torch.arange(0, 1, step)[1:]
    noise = torch.FloatTensor(num_transforms)
    noise.uniform_(-step * perturbation, step * perturbation)
    times += noise
    times_params = times.numpy()
    return (times_params, degrees_params, translation_params)

@staticmethod
def get_params_array(nums_range: tuple[float, float], num_transforms: int):
    tensor = torch.FloatTensor(num_transforms, 3).uniform_(*nums_range)
    return tensor.numpy()

class Motion(IntensityTransform, FourierTransform):
    """Add MRI motion artifact.

    Magnetic resonance images suffer from motion artifacts when the subject
    moves during image acquisition. This transform follows
    `Shaw et al., 2019 <http://proceedings.mlr.press/v102/shaw19a.html>`_ to
    simulate motion artifacts for data augmentation.

    Args:
        degrees: Sequence of rotations :math:`(\\theta_1, \\theta_2, \\theta_3)`.
        translation: Sequence of translations :math:`(t_1, t_2, t_3)` in mm.
        times: Sequence of times from 0 to 1 at which the motions happen.
        image_interpolation: See :ref:`Interpolation`.
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.
    """

    def __init__(self, degrees: Union[TypeTripletFloat, dict[str, TypeTripletFloat]], translation: Union[TypeTripletFloat, dict[str, TypeTripletFloat]], times: Union[Sequence[float], dict[str, Sequence[float]]], image_interpolation: Union[Sequence[str], dict[str, Sequence[str]]], **kwargs):
        super().__init__(**kwargs)
        self.degrees = degrees
        self.translation = translation
        self.times = times
        self.image_interpolation = image_interpolation
        self.args_names = ['degrees', 'translation', 'times', 'image_interpolation']

    def apply_transform(self, subject: Subject) -> Subject:
        degrees = self.degrees
        translation = self.translation
        times = self.times
        image_interpolation = self.image_interpolation
        for image_name, image in self.get_images_dict(subject).items():
            if self.arguments_are_dict():
                assert isinstance(self.degrees, dict)
                assert isinstance(self.translation, dict)
                assert isinstance(self.times, dict)
                assert isinstance(self.image_interpolation, dict)
                degrees = self.degrees[image_name]
                translation = self.translation[image_name]
                times = self.times[image_name]
                image_interpolation = self.image_interpolation[image_name]
            result_arrays = []
            for channel in image.data:
                sitk_image = nib_to_sitk(channel[np.newaxis], image.affine, force_3d=True)
                transforms = self.get_rigid_transforms(np.asarray(degrees), np.asarray(translation), sitk_image)
                assert isinstance(image_interpolation, str)
                transformed_channel = self.add_artifact(sitk_image, transforms, np.asarray(times), image_interpolation)
                result_arrays.append(transformed_channel)
            result = np.stack(result_arrays)
            image.set_data(torch.as_tensor(result))
        return subject

    def get_rigid_transforms(self, degrees_params: np.ndarray, translation_params: np.ndarray, image: sitk.Image) -> list[sitk.Euler3DTransform]:
        center_ijk = np.array(image.GetSize()) / 2
        center_lps = image.TransformContinuousIndexToPhysicalPoint(center_ijk)
        identity = np.eye(4)
        matrices = [identity]
        for degrees, translation in zip(degrees_params, translation_params):
            radians = np.radians(degrees).tolist()
            motion = sitk.Euler3DTransform()
            motion.SetCenter(center_lps)
            motion.SetRotation(*radians)
            motion.SetTranslation(translation.tolist())
            motion_matrix = self.transform_to_matrix(motion)
            matrices.append(motion_matrix)
        transforms = [self.matrix_to_transform(m) for m in matrices]
        return transforms

    @staticmethod
    def transform_to_matrix(transform: sitk.Euler3DTransform) -> np.ndarray:
        matrix = np.eye(4)
        rotation = np.array(transform.GetMatrix()).reshape(3, 3)
        matrix[:3, :3] = rotation
        matrix[:3, 3] = transform.GetTranslation()
        return matrix

    @staticmethod
    def matrix_to_transform(matrix: np.ndarray) -> sitk.Euler3DTransform:
        transform = sitk.Euler3DTransform()
        rotation = matrix[:3, :3].flatten().tolist()
        transform.SetMatrix(rotation)
        transform.SetTranslation(matrix[:3, 3])
        return transform

    def resample_images(self, image: sitk.Image, transforms: Sequence[sitk.Euler3DTransform], interpolation: str) -> list[sitk.Image]:
        floating = reference = image
        default_value = np.float64(sitk.GetArrayViewFromImage(image).min())
        transforms = transforms[1:]
        images = [image]
        for transform in transforms:
            interpolator = self.get_sitk_interpolator(interpolation)
            resampler = sitk.ResampleImageFilter()
            resampler.SetInterpolator(interpolator)
            resampler.SetReferenceImage(reference)
            resampler.SetOutputPixelType(sitk.sitkFloat32)
            resampler.SetDefaultPixelValue(default_value)
            resampler.SetTransform(transform)
            resampled = resampler.Execute(floating)
            images.append(resampled)
        return images

    @staticmethod
    def sort_spectra(spectra: list[torch.Tensor], times: np.ndarray):
        """Use original spectrum to fill the center of k-space."""
        num_spectra = len(spectra)
        if np.any(times > 0.5):
            index = np.where(times > 0.5)[0].min()
        else:
            index = num_spectra - 1
        spectra[0], spectra[index] = (spectra[index], spectra[0])

    def add_artifact(self, image: sitk.Image, transforms: Sequence[sitk.Euler3DTransform], times: np.ndarray, interpolation: str):
        images = self.resample_images(image, transforms, interpolation)
        spectra = []
        for image in images:
            array = sitk.GetArrayFromImage(image).transpose()
            spectrum = self.fourier_transform(torch.from_numpy(array))
            spectra.append(spectrum)
        self.sort_spectra(spectra, times)
        result_spectrum = torch.empty_like(spectra[0])
        last_index = result_spectrum.shape[2]
        indices_array = (last_index * times).astype(int)
        indices: list[int] = indices_array.tolist()
        indices.append(last_index)
        ini = 0
        for spectrum, fin in zip(spectra, indices):
            result_spectrum[..., ini:fin] = spectrum[..., ini:fin]
            ini = fin
        result_image = self.inv_fourier_transform(result_spectrum).real.float()
        return result_image

def add_artifact(self, image: sitk.Image, transforms: Sequence[sitk.Euler3DTransform], times: np.ndarray, interpolation: str):
    images = self.resample_images(image, transforms, interpolation)
    spectra = []
    for image in images:
        array = sitk.GetArrayFromImage(image).transpose()
        spectrum = self.fourier_transform(torch.from_numpy(array))
        spectra.append(spectrum)
    self.sort_spectra(spectra, times)
    result_spectrum = torch.empty_like(spectra[0])
    last_index = result_spectrum.shape[2]
    indices_array = (last_index * times).astype(int)
    indices: list[int] = indices_array.tolist()
    indices.append(last_index)
    ini = 0
    for spectrum, fin in zip(spectra, indices):
        result_spectrum[..., ini:fin] = spectrum[..., ini:fin]
        ini = fin
    result_image = self.inv_fourier_transform(result_spectrum).real.float()
    return result_image

class Ghosting(IntensityTransform, FourierTransform):
    """Add MRI ghosting artifact.

    Discrete "ghost" artifacts may occur along the phase-encode direction
    whenever the position or signal intensity of imaged structures within the
    field-of-view vary or move in a regular (periodic) fashion. Pulsatile flow
    of blood or CSF, cardiac motion, and respiratory motion are the most
    important patient-related causes of ghost artifacts in clinical MR imaging
    (from `mriquestions.com`_).

    .. _mriquestions.com: http://mriquestions.com/why-discrete-ghosts.html

    Args:
        num_ghosts: Number of 'ghosts' :math:`n` in the image.
        axes: Axis along which the ghosts will be created.
        intensity: Positive number representing the artifact strength
            :math:`s` with respect to the maximum of the :math:`k`-space.
            If ``0``, the ghosts will not be visible.
        restore: Number between ``0`` and ``1`` indicating how much of the
            :math:`k`-space center should be restored after removing the planes
            that generate the artifact. If ``None``, only the central slice
            will be restored.
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.

    .. note:: The execution time of this transform does not depend on the
        number of ghosts.
    """

    def __init__(self, num_ghosts: int | dict[str, int], axis: int | dict[str, int], intensity: float | dict[str, float], restore: float | None | dict[str, float | None], **kwargs):
        super().__init__(**kwargs)
        self.axis = axis
        self.num_ghosts = num_ghosts
        self.intensity = intensity
        self.restore = restore
        self.args_names = ['num_ghosts', 'axis', 'intensity', 'restore']

    def apply_transform(self, subject: Subject) -> Subject:
        axis: int | dict[str, int]
        num_ghosts: int | dict[str, int]
        intensity: float | dict[str, float]
        restore: float | None | dict[str, float | None]
        for name, image in self.get_images_dict(subject).items():
            if self.arguments_are_dict():
                assert isinstance(self.axis, dict)
                assert isinstance(self.num_ghosts, dict)
                assert isinstance(self.intensity, dict)
                assert isinstance(self.restore, dict)
                axis = self.axis[name]
                num_ghosts = self.num_ghosts[name]
                intensity = self.intensity[name]
                restore = self.restore[name]
            else:
                axis = self.axis
                num_ghosts = self.num_ghosts
                intensity = self.intensity
                restore = self.restore
            transformed_tensors = []
            for tensor in image.data:
                assert isinstance(num_ghosts, int)
                assert isinstance(axis, int)
                assert isinstance(intensity, (int, float))
                if restore is not None:
                    assert isinstance(restore, float)
                transformed_tensor = self.add_artifact(tensor, num_ghosts, axis, intensity, restore)
                transformed_tensors.append(transformed_tensor)
            image.set_data(torch.stack(transformed_tensors))
        return subject

    def add_artifact(self, tensor: torch.Tensor, num_ghosts: int, axis: int, intensity: float, restore_center: float | None):
        if not num_ghosts or not intensity:
            return tensor
        spectrum = self.fourier_transform(tensor)
        planes = self._get_planes_to_modify(spectrum, axis, num_ghosts)
        tensor_restore, slices = self._get_slices_to_restore(spectrum, axis, restore_center)
        tensor_restore = tensor_restore.clone()
        planes *= 1 - intensity
        spectrum[slices] = tensor_restore
        tensor_ghosts = self.inv_fourier_transform(spectrum)
        return tensor_ghosts.real.float()

    @staticmethod
    def _get_planes_to_modify(spectrum: torch.Tensor, axis: int, num_ghosts: int) -> torch.Tensor:
        slices = [slice(None)] * spectrum.ndim
        slices[axis] = slice(None, None, num_ghosts)
        slices_tuple = tuple(slices)
        return spectrum[slices_tuple]

    @staticmethod
    def _get_slices_to_restore(spectrum: torch.Tensor, axis: int, restore_center: float | None) -> tuple[torch.Tensor, tuple[slice, ...]]:
        dim_shape = spectrum.shape[axis]
        mid_idx = dim_shape // 2
        slices = [slice(None)] * spectrum.ndim
        if restore_center is None:
            slice_ = slice(mid_idx, mid_idx + 1)
        else:
            size_restore = int(np.round(restore_center * dim_shape))
            slice_ = slice(mid_idx - size_restore // 2, mid_idx + size_restore // 2)
        slices[axis] = slice_
        slices_tuple = tuple(slices)
        restore_tensor = spectrum[slices_tuple]
        return (restore_tensor, slices_tuple)

def add_artifact(self, tensor: torch.Tensor, num_ghosts: int, axis: int, intensity: float, restore_center: float | None):
    if not num_ghosts or not intensity:
        return tensor
    spectrum = self.fourier_transform(tensor)
    planes = self._get_planes_to_modify(spectrum, axis, num_ghosts)
    tensor_restore, slices = self._get_slices_to_restore(spectrum, axis, restore_center)
    tensor_restore = tensor_restore.clone()
    planes *= 1 - intensity
    spectrum[slices] = tensor_restore
    tensor_ghosts = self.inv_fourier_transform(spectrum)
    return tensor_ghosts.real.float()

def power(tensor, gamma):
    if tensor.min() < 0:
        output = tensor.sign() * tensor.abs() ** gamma
    else:
        output = tensor ** gamma
    return output

class Spike(IntensityTransform, FourierTransform):
    """Add MRI spike artifacts.

    Also known as `Herringbone artifact
    <https://radiopaedia.org/articles/herringbone-artifact>`_,
    crisscross artifact or corduroy artifact, it creates stripes in different
    directions in image space due to spikes in k-space.

    Args:
        spikes_positions:
        intensity: Ratio :math:`r` between the spike intensity and the maximum
            of the spectrum.
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.

    .. note:: The execution time of this transform does not depend on the
        number of spikes.
    """

    def __init__(self, spikes_positions: Union[np.ndarray, dict[str, np.ndarray]], intensity: Union[float, dict[str, float]], **kwargs):
        super().__init__(**kwargs)
        self.spikes_positions = spikes_positions
        self.intensity = intensity
        self.args_names = ['spikes_positions', 'intensity']
        self.invert_transform = False

    def apply_transform(self, subject: Subject) -> Subject:
        spikes_positions = self.spikes_positions
        intensity = self.intensity
        for image_name, image in self.get_images_dict(subject).items():
            if self.arguments_are_dict():
                spikes_positions = self.spikes_positions[image_name]
                assert isinstance(self.intensity, dict)
                intensity = self.intensity[image_name]
            transformed_tensors = []
            for channel in image.data:
                assert isinstance(intensity, Number)
                transformed_tensor = self.add_artifact(channel, np.asarray(spikes_positions), intensity)
                transformed_tensors.append(transformed_tensor)
            image.set_data(torch.stack(transformed_tensors))
        return subject

    def add_artifact(self, tensor: torch.Tensor, spikes_positions: np.ndarray, intensity_factor: float):
        if intensity_factor == 0 or len(spikes_positions) == 0:
            return tensor
        spectrum = self.fourier_transform(tensor)
        shape = np.array(spectrum.shape)
        mid_shape = shape // 2
        indices = np.floor(spikes_positions * shape).astype(int)
        for index in indices:
            diff = index - mid_shape
            i, j, k = mid_shape + diff
            artifact = spectrum.cpu().numpy().max() * intensity_factor
            if self.invert_transform:
                spectrum[i, j, k] -= artifact
            else:
                spectrum[i, j, k] += artifact
        result = self.inv_fourier_transform(spectrum).real.float()
        return result

def add_artifact(self, tensor: torch.Tensor, spikes_positions: np.ndarray, intensity_factor: float):
    if intensity_factor == 0 or len(spikes_positions) == 0:
        return tensor
    spectrum = self.fourier_transform(tensor)
    shape = np.array(spectrum.shape)
    mid_shape = shape // 2
    indices = np.floor(spikes_positions * shape).astype(int)
    for index in indices:
        diff = index - mid_shape
        i, j, k = mid_shape + diff
        artifact = spectrum.cpu().numpy().max() * intensity_factor
        if self.invert_transform:
            spectrum[i, j, k] -= artifact
        else:
            spectrum[i, j, k] += artifact
    result = self.inv_fourier_transform(spectrum).real.float()
    return result

class Crop(BoundsTransform):
    """Crop an image.

    Args:
        cropping: Tuple
            :math:`(w_{ini}, w_{fin}, h_{ini}, h_{fin}, d_{ini}, d_{fin})`
            defining the number of values cropped from the edges of each axis.
            If the initial shape of the image is
            :math:`W \\times H \\times D`, the final shape will be
            :math:`(- w_{ini} + W - w_{fin}) \\times (- h_{ini} + H - h_{fin})
            \\times (- d_{ini} + D - d_{fin})`.
            If only three values :math:`(w, h, d)` are provided, then
            :math:`w_{ini} = w_{fin} = w`,
            :math:`h_{ini} = h_{fin} = h` and
            :math:`d_{ini} = d_{fin} = d`.
            If only one value :math:`n` is provided, then
            :math:`w_{ini} = w_{fin} = h_{ini} = h_{fin}
            = d_{ini} = d_{fin} = n`.
        copy: If ``True``, each image will be cropped and the patch copied to a new
            subject. If ``False``, each image will be cropped in place. This transform
            overwrites the copy argument of the base transform and copies only the
            cropped patch instead of the whole image. This can provide a significant
            speedup when cropping small patches from large images.
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.

    .. seealso:: If you want to pass the output shape instead, please use
        :class:`~torchio.transforms.CropOrPad` instead.
    """

    def __init__(self, cropping: TypeBounds, copy=True, **kwargs):
        self._copy_patch = copy
        super().__init__(cropping, copy=False, **kwargs)
        self.cropping = cropping
        self.args_names = ['cropping']

    def apply_transform(self, subject: Subject) -> Subject:
        assert self.bounds_parameters is not None
        low = self.bounds_parameters[::2]
        high = self.bounds_parameters[1::2]
        index_ini = low
        index_fin = np.array(subject.spatial_shape) - high
        if self._copy_patch:
            cropped_subject = subject.__class__.__new__(subject.__class__)
            image_keys_to_crop = subject.get_images_dict(intensity_only=False, include=self.include, exclude=self.exclude).keys()
            keys_to_expose = subject.keys()
            for key, value in subject.__dict__.items():
                if key not in image_keys_to_crop:
                    copied_value = deepcopy(value)
                    if key in keys_to_expose:
                        cropped_subject[key] = copied_value
                    cropped_subject.__dict__[str(key)] = copied_value
                else:
                    cropped_subject[key] = self._crop_image(value, index_ini, index_fin, copy_patch=self._copy_patch)
            cropped_subject.update_attributes()
            return cropped_subject
        else:
            for image in self.get_images(subject):
                self._crop_image(image, index_ini, index_fin, copy_patch=self._copy_patch)
            return subject

    @staticmethod
    def _crop_image(image: Image, index_ini: tuple, index_fin: tuple, *, copy_patch: bool) -> Image:
        new_origin = apply_affine(image.affine, index_ini)
        new_affine = image.affine.copy()
        new_affine[:3, 3] = new_origin
        i0, j0, k0 = index_ini
        i1, j1, k1 = index_fin
        if copy_patch:
            cropped_data = image.data[:, i0:i1, j0:j1, k0:k1].clone()
            new_image = type(image)(tensor=cropped_data, affine=new_affine, type=image.type, path=image.path)
            return new_image
        else:
            image.set_data(image.data[:, i0:i1, j0:j1, k0:k1].clone())
            image.affine = new_affine
            return image

    def inverse(self):
        from .pad import Pad
        return Pad(self.cropping)

@staticmethod
def _crop_image(image: Image, index_ini: tuple, index_fin: tuple, *, copy_patch: bool) -> Image:
    new_origin = apply_affine(image.affine, index_ini)
    new_affine = image.affine.copy()
    new_affine[:3, 3] = new_origin
    i0, j0, k0 = index_ini
    i1, j1, k1 = index_fin
    if copy_patch:
        cropped_data = image.data[:, i0:i1, j0:j1, k0:k1].clone()
        new_image = type(image)(tensor=cropped_data, affine=new_affine, type=image.type, path=image.path)
        return new_image
    else:
        image.set_data(image.data[:, i0:i1, j0:j1, k0:k1].clone())
        image.affine = new_affine
        return image

class ToOrientation(SpatialTransform):
    """Reorient the data to a specified orientation.

    This transform reorders the voxels and modifies the affine matrix to match
    the specified orientation code.
    The image intensity values are not modified, and the sample locations in
    the scanner space are preserved.

    Common orientation codes include:

    - ``'RAS'`` (neurological convention):
        - The first axis goes from Left to Right (R).
        - The second axis goes from Posterior to Anterior (A).
        - The third axis goes from Inferior to Superior (S).
    - ``'LAS'`` (radiological convention):
        - The first axis goes from Right to Left (L).
        - The second axis goes from Posterior to Anterior (A).
        - The third axis goes from Inferior to Superior (S).

    See `NiBabel docs about image orientation`_ for more information.

    Args:
        orientation: A three-letter orientation code. Examples: ``'RAS'``,
            ``'LAS'``, ``'LPS'``, ``'PLS'``, ``'SLP'``. The code must contain
            one character for each axis direction: R or L, A or P, and S or I.
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.

    .. _NiBabel docs about image orientation: https://nipy.org/nibabel/image_orientation.html
    """

    def __init__(self, orientation: str='RAS', **kwargs):
        super().__init__(**kwargs)
        if not isinstance(orientation, str) or len(orientation) != 3:
            message = f'Orientation must be a 3-letter string, got "{orientation}"'
            raise ValueError(message)
        valid_codes = set('RLAPIS')
        orientation = orientation.upper()
        all_valid = all((axis in valid_codes for axis in orientation))
        if not all_valid:
            message = f'Orientation code must be composed of three distinct characters in {valid_codes} but got "{orientation}"'
            raise ValueError(message)
        has_sagittal = 'R' in orientation or 'L' in orientation
        has_coronal = 'A' in orientation or 'P' in orientation
        has_axial = 'S' in orientation or 'I' in orientation
        has_all = has_sagittal and has_coronal and has_axial
        if not has_all:
            message = f'Orientation code must include one character for each axis direction: R or L, A or P, and S or I, but got "{orientation}"'
            raise ValueError(message)
        self.orientation = orientation
        self.args_names = ['orientation']

    def apply_transform(self, subject: Subject) -> Subject:
        for image in subject.get_images(intensity_only=False):
            current_orientation = ''.join(nib.orientations.aff2axcodes(image.affine))
            if current_orientation == self.orientation:
                continue
            array = rearrange(image.numpy(), 'C W H D -> W H D 1 C')
            nii = nib.nifti1.Nifti1Image(array, image.affine)
            current_orientation = orientations.io_orientation(nii.affine)
            target_orientation = orientations.axcodes2ornt(tuple(self.orientation))
            transform = orientations.ornt_transform(current_orientation, target_orientation)
            reoriented_array = orientations.apply_orientation(nii.dataobj, transform)
            reoriented_array = rearrange(reoriented_array, 'W H D 1 C -> C W H D')
            reoriented_affine = nii.affine @ orientations.inv_ornt_aff(transform, nii.shape)
            reoriented_array = np.ascontiguousarray(reoriented_array)
            tensor = torch.from_numpy(reoriented_array)
            image.set_data(tensor)
            image.affine = reoriented_affine
        return subject

def apply_transform(self, subject: Subject) -> Subject:
    for image in subject.get_images(intensity_only=False):
        current_orientation = ''.join(nib.orientations.aff2axcodes(image.affine))
        if current_orientation == self.orientation:
            continue
        array = rearrange(image.numpy(), 'C W H D -> W H D 1 C')
        nii = nib.nifti1.Nifti1Image(array, image.affine)
        current_orientation = orientations.io_orientation(nii.affine)
        target_orientation = orientations.axcodes2ornt(tuple(self.orientation))
        transform = orientations.ornt_transform(current_orientation, target_orientation)
        reoriented_array = orientations.apply_orientation(nii.dataobj, transform)
        reoriented_array = rearrange(reoriented_array, 'W H D 1 C -> C W H D')
        reoriented_affine = nii.affine @ orientations.inv_ornt_aff(transform, nii.shape)
        reoriented_array = np.ascontiguousarray(reoriented_array)
        tensor = torch.from_numpy(reoriented_array)
        image.set_data(tensor)
        image.affine = reoriented_affine
    return subject

class Pad(BoundsTransform):
    """Pad an image.

    Args:
        padding: Tuple
            :math:`(w_{ini}, w_{fin}, h_{ini}, h_{fin}, d_{ini}, d_{fin})`
            defining the number of values padded to the edges of each axis.
            If the initial shape of the image is
            :math:`W \\times H \\times D`, the final shape will be
            :math:`(w_{ini} + W + w_{fin}) \\times (h_{ini} + H + h_{fin})
            \\times (d_{ini} + D + d_{fin})`.
            If only three values :math:`(w, h, d)` are provided, then
            :math:`w_{ini} = w_{fin} = w`,
            :math:`h_{ini} = h_{fin} = h` and
            :math:`d_{ini} = d_{fin} = d`.
            If only one value :math:`n` is provided, then
            :math:`w_{ini} = w_{fin} = h_{ini} = h_{fin} =
            d_{ini} = d_{fin} = n`.
        padding_mode: See possible modes in `NumPy docs`_. If it is a number,
            the mode will be set to ``'constant'``. If it is ``'mean'``,
            ``'maximum'``, ``'median'`` or ``'minimum'``, the statistic will be
            computed from the whole volume, unlike in NumPy, which computes it
            along the padded axis.
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.

    .. seealso:: If you want to pass the output shape instead, please use
        :class:`~torchio.transforms.CropOrPad` instead.

    .. _NumPy docs: https://numpy.org/doc/stable/reference/generated/numpy.pad.html
    """
    PADDING_MODES = ('empty', 'edge', 'wrap', 'constant', 'linear_ramp', 'maximum', 'mean', 'median', 'minimum', 'reflect', 'symmetric')

    def __init__(self, padding: TypeBounds, padding_mode: Union[str, float]=0, **kwargs):
        super().__init__(padding, **kwargs)
        self.padding = padding
        self.check_padding_mode(padding_mode)
        self.padding_mode = padding_mode
        self.args_names = ['padding', 'padding_mode']

    @classmethod
    def check_padding_mode(cls, padding_mode):
        is_number = isinstance(padding_mode, Number)
        is_callable = callable(padding_mode)
        if not (padding_mode in cls.PADDING_MODES or is_number or is_callable):
            message = f'Padding mode "{padding_mode}" not valid. Valid options are {list(cls.PADDING_MODES)}, a number or a function'
            raise KeyError(message)

    def _check_truncation(self, image: Image, mode: Union[str, float]) -> None:
        if mode not in ('mean', 'median'):
            return
        if torch.is_floating_point(image.data):
            return
        message = f'The constant value computed for padding mode "{mode}" might be truncated  in the output, as the data type of the input image is not float. Consider converting the image to a floating point type before applying this transform.'
        warnings.warn(message, RuntimeWarning, stacklevel=2)

    def apply_transform(self, subject: Subject) -> Subject:
        assert self.bounds_parameters is not None
        low = self.bounds_parameters[::2]
        for image in self.get_images(subject):
            self._check_truncation(image, self.padding_mode)
            new_origin = apply_affine(image.affine, -np.array(low))
            new_affine = image.affine.copy()
            new_affine[:3, 3] = new_origin
            mode: str | float = 'constant'
            constant: torch.Tensor | float | None = None
            kwargs: dict[str, str | float | torch.Tensor] = {}
            if isinstance(self.padding_mode, Number):
                constant = self.padding_mode
            elif self.padding_mode == 'maximum':
                constant = image.data.max()
            elif self.padding_mode == 'mean':
                constant = image.data.float().mean()
            elif self.padding_mode == 'median':
                constant = torch.quantile(image.data.float(), 0.5)
            elif self.padding_mode == 'minimum':
                constant = image.data.min()
            else:
                constant = None
                mode = self.padding_mode
            if constant is not None:
                kwargs['constant_values'] = constant
            kwargs['mode'] = mode
            pad_params = self.bounds_parameters
            paddings = ((0, 0), pad_params[:2], pad_params[2:4], pad_params[4:])
            padded = np.pad(image.data, paddings, **kwargs)
            image.set_data(torch.as_tensor(padded))
            image.affine = new_affine
        return subject

    def inverse(self):
        from .crop import Crop
        return Crop(self.padding)

def apply_transform(self, subject: Subject) -> Subject:
    assert self.bounds_parameters is not None
    low = self.bounds_parameters[::2]
    for image in self.get_images(subject):
        self._check_truncation(image, self.padding_mode)
        new_origin = apply_affine(image.affine, -np.array(low))
        new_affine = image.affine.copy()
        new_affine[:3, 3] = new_origin
        mode: str | float = 'constant'
        constant: torch.Tensor | float | None = None
        kwargs: dict[str, str | float | torch.Tensor] = {}
        if isinstance(self.padding_mode, Number):
            constant = self.padding_mode
        elif self.padding_mode == 'maximum':
            constant = image.data.max()
        elif self.padding_mode == 'mean':
            constant = image.data.float().mean()
        elif self.padding_mode == 'median':
            constant = torch.quantile(image.data.float(), 0.5)
        elif self.padding_mode == 'minimum':
            constant = image.data.min()
        else:
            constant = None
            mode = self.padding_mode
        if constant is not None:
            kwargs['constant_values'] = constant
        kwargs['mode'] = mode
        pad_params = self.bounds_parameters
        paddings = ((0, 0), pad_params[:2], pad_params[2:4], pad_params[4:])
        padded = np.pad(image.data, paddings, **kwargs)
        image.set_data(torch.as_tensor(padded))
        image.affine = new_affine
    return subject

class RescaleIntensity(NormalizationTransform):
    """Rescale intensity values to a certain range.

    Args:
        out_min_max: Range :math:`(n_{min}, n_{max})` of output intensities.
            If only one value :math:`d` is provided,
            :math:`(n_{min}, n_{max}) = (-d, d)`.
        percentiles: Percentile values of the input image that will be mapped
            to :math:`(n_{min}, n_{max})`. They can be used for contrast
            stretching, as in `this scikit-image example`_. For example,
            Isensee et al. use ``(0.5, 99.5)`` in their `nn-UNet paper`_.
            If only one value :math:`d` is provided,
            :math:`(n_{min}, n_{max}) = (0, d)`.
        masking_method: See
            :class:`~torchio.transforms.preprocessing.intensity.NormalizationTransform`.
        in_min_max: Range :math:`(m_{min}, m_{max})` of input intensities that
            will be mapped to :math:`(n_{min}, n_{max})`. If ``None``, the
            minimum and maximum input intensities will be used.
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.

    Example:
        >>> import torchio as tio
        >>> ct = tio.ScalarImage('ct_scan.nii.gz')
        >>> ct_air, ct_bone = -1000, 1000
        >>> rescale = tio.RescaleIntensity(
        ...     out_min_max=(-1, 1), in_min_max=(ct_air, ct_bone))
        >>> ct_normalized = rescale(ct)

    .. _this scikit-image example: https://scikit-image.org/docs/dev/auto_examples/color_exposure/plot_equalize.html#sphx-glr-auto-examples-color-exposure-plot-equalize-py
    .. _nn-UNet paper: https://arxiv.org/abs/1809.10486
    """

    def __init__(self, out_min_max: TypeDoubleFloat=(0, 1), percentiles: TypeDoubleFloat=(0, 100), masking_method: TypeMaskingMethod=None, in_min_max: TypeDoubleFloat | None=None, **kwargs):
        super().__init__(masking_method=masking_method, **kwargs)
        self.out_min_max = out_min_max
        self.in_min_max = in_min_max
        self.out_min, self.out_max = self._parse_range(out_min_max, 'out_min_max')
        self.percentiles = self._parse_range(percentiles, 'percentiles', min_constraint=0, max_constraint=100)
        if self.in_min_max is not None:
            self.in_min_max = self._parse_range(self.in_min_max, 'in_min_max')
        self.args_names = ['out_min_max', 'percentiles', 'masking_method', 'in_min_max']

    def apply_normalization(self, subject: Subject, image_name: str, mask: torch.Tensor) -> None:
        image: Image = subject[image_name]
        image.set_data(self.rescale(image.data, mask, image_name))

    def rescale(self, tensor: torch.Tensor, mask: torch.Tensor, image_name: str) -> torch.Tensor:
        array = tensor.clone().float().numpy()
        mask_array = mask.numpy()
        if not mask_array.any():
            message = f'Rescaling image "{image_name}" not possible because the mask to compute the statistics is empty'
            warnings.warn(message, RuntimeWarning, stacklevel=2)
            return tensor
        values = array[mask_array]
        cutoff = np.percentile(values, self.percentiles)
        np.clip(array, *cutoff, out=array)
        if self.in_min_max is None:
            in_min, in_max = (array.min(), array.max())
        else:
            in_min, in_max = self.in_min_max
        in_range = in_max - in_min
        if in_range == 0:
            message = f'Rescaling image "{image_name}" not possible because all the intensity values are the same'
            warnings.warn(message, RuntimeWarning, stacklevel=2)
            return tensor
        out_range = self.out_max - self.out_min
        array -= in_min
        array /= in_range
        array *= out_range
        array += self.out_min
        return torch.as_tensor(array)

def rescale(self, tensor: torch.Tensor, mask: torch.Tensor, image_name: str) -> torch.Tensor:
    array = tensor.clone().float().numpy()
    mask_array = mask.numpy()
    if not mask_array.any():
        message = f'Rescaling image "{image_name}" not possible because the mask to compute the statistics is empty'
        warnings.warn(message, RuntimeWarning, stacklevel=2)
        return tensor
    values = array[mask_array]
    cutoff = np.percentile(values, self.percentiles)
    np.clip(array, *cutoff, out=array)
    if self.in_min_max is None:
        in_min, in_max = (array.min(), array.max())
    else:
        in_min, in_max = self.in_min_max
    in_range = in_max - in_min
    if in_range == 0:
        message = f'Rescaling image "{image_name}" not possible because all the intensity values are the same'
        warnings.warn(message, RuntimeWarning, stacklevel=2)
        return tensor
    out_range = self.out_max - self.out_min
    array -= in_min
    array /= in_range
    array *= out_range
    array += self.out_min
    return torch.as_tensor(array)

def _standardize_cutoff(cutoff: Sequence[float]) -> np.ndarray:
    """Standardize the cutoff values given in the configuration.

    Computes percentile landmark normalization by default.
    """
    cutoff_array = np.asarray(cutoff)
    cutoff_array[0] = max(0, cutoff_array[0])
    cutoff_array[1] = min(1, cutoff_array[1])
    cutoff_array[0] = np.min([cutoff_array[0], 0.09])
    cutoff_array[1] = np.max([cutoff_array[1], 0.91])
    return cutoff_array

def _get_average_mapping(percentiles_database: np.ndarray) -> np.ndarray:
    """Map the landmarks of the database to the chosen range.

    Args:
        percentiles_database: Percentiles database over which to perform the
            averaging.
    """
    pc1 = percentiles_database[:, 0]
    pc2 = percentiles_database[:, -1]
    s1, s2 = STANDARD_RANGE
    slopes = (s2 - s1) / (pc2 - pc1)
    slopes = np.nan_to_num(slopes)
    intercepts = np.mean(s1 - slopes * pc1)
    num_images = len(percentiles_database)
    final_map = slopes.dot(percentiles_database) / num_images + intercepts
    return final_map

def _get_percentiles(percentiles_cutoff: tuple[float, float]) -> np.ndarray:
    quartiles = np.arange(25, 100, 25).tolist()
    deciles = np.arange(10, 100, 10).tolist()
    all_percentiles = list(percentiles_cutoff) + quartiles + deciles
    percentiles = sorted(set(all_percentiles))
    return np.array(percentiles)

class Clamp(IntensityTransform):
    """Clamp intensity values into a range :math:`[a, b]`.

    For more information, see :func:`torch.clamp`.

    Args:
        out_min: Minimum value :math:`a` of the output image. If ``None``, the
            minimum of the image is used.
        out_max: Maximum value :math:`b` of the output image. If ``None``, the
            maximum of the image is used.

    Example:
        >>> import torchio as tio
        >>> ct = tio.datasets.Slicer('CTChest').CT_chest
        >>> HOUNSFIELD_AIR, HOUNSFIELD_BONE = -1000, 1000
        >>> clamp = tio.Clamp(out_min=HOUNSFIELD_AIR, out_max=HOUNSFIELD_BONE)
        >>> ct_clamped = clamp(ct)

    .. plot::

        import torchio as tio
        subject = tio.datasets.Slicer('CTChest')
        ct = subject.CT_chest
        HOUNSFIELD_AIR, HOUNSFIELD_BONE = -1000, 1000
        clamp = tio.Clamp(out_min=HOUNSFIELD_AIR, out_max=HOUNSFIELD_BONE)
        ct_clamped = clamp(ct)
        subject.add_image(ct_clamped, 'Clamped')
        subject.plot()
    """

    def __init__(self, out_min: float | None=None, out_max: float | None=None, **kwargs):
        super().__init__(**kwargs)
        self.out_min, self.out_max = (out_min, out_max)
        self.args_names = ['out_min', 'out_max']

    def apply_transform(self, subject: Subject) -> Subject:
        for image in self.get_images(subject):
            assert isinstance(image, ScalarImage)
            self.apply_clamp(image)
        return subject

    def apply_clamp(self, image: ScalarImage) -> None:
        image.set_data(self.clamp(image.data))

    def clamp(self, tensor: torch.Tensor) -> torch.Tensor:
        return tensor.clamp(self.out_min, self.out_max)

def apply_clamp(self, image: ScalarImage) -> None:
    image.set_data(self.clamp(image.data))

def clamp(self, tensor: torch.Tensor) -> torch.Tensor:
    return tensor.clamp(self.out_min, self.out_max)

class ZNormalization(NormalizationTransform):
    """Subtract mean and divide by standard deviation.

    Args:
        masking_method: See
            :class:`~torchio.transforms.preprocessing.intensity.NormalizationTransform`.
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.
    """

    def __init__(self, masking_method: TypeMaskingMethod=None, **kwargs):
        super().__init__(masking_method=masking_method, **kwargs)
        self.args_names = ['masking_method']

    def apply_normalization(self, subject: Subject, image_name: str, mask: torch.Tensor) -> None:
        image = subject[image_name]
        standardized = self.znorm(image.data, mask)
        if standardized is None:
            message = f'Standard deviation is 0 for masked values in image "{image_name}" ({image.path})'
            raise RuntimeError(message)
        image.set_data(standardized)

    @staticmethod
    def znorm(tensor: torch.Tensor, mask: torch.Tensor) -> torch.Tensor | None:
        tensor = tensor.clone().float()
        values = tensor[mask]
        mean, std = (values.mean(), values.std())
        if std == 0:
            return None
        tensor -= mean
        tensor /= std
        return tensor

@staticmethod
def znorm(tensor: torch.Tensor, mask: torch.Tensor) -> torch.Tensor | None:
    tensor = tensor.clone().float()
    values = tensor[mask]
    mean, std = (values.mean(), values.std())
    if std == 0:
        return None
    tensor -= mean
    tensor /= std
    return tensor

def _compute_pca(embeddings: ScalarImage, num_components: int, whiten: bool, normalize: bool, make_skewness_positive: bool, values_range: tuple[float, float] | None, clip: bool, **pca_kwargs) -> ScalarImage:
    sklearn = get_sklearn()
    PCA = sklearn.decomposition.PCA
    data = embeddings.numpy()
    _, size_x, size_y, size_z = data.shape
    X = rearrange(data, 'c x y z -> (x y z) c')
    pca = PCA(n_components=num_components, whiten=whiten, **pca_kwargs)
    projected: np.ndarray = pca.fit_transform(X).T
    if normalize:
        projected /= projected[0].std()
    if make_skewness_positive:
        for component in projected:
            third_cumulant = np.mean(component ** 3)
            second_cumulant = np.mean(component ** 2)
            skewness = third_cumulant / second_cumulant ** (3 / 2)
            if skewness < 0:
                component *= -1
    grid: np.ndarray = rearrange(projected, 'c (x y z) -> c x y z', x=size_x, y=size_y, z=size_z)
    if values_range is not None:
        vmin, vmax = values_range
    else:
        vmin, vmax = (grid.min(), grid.max())
    grid = (grid - vmin) / (vmax - vmin)
    if clip:
        grid = np.clip(grid, 0, 1)
    return ScalarImage(tensor=grid, affine=embeddings.affine)

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

class TestInvertibility(TorchioTestCase):

    def test_all_random_transforms(self):
        transform = self.get_large_composed_transform()
        for t in transform.transforms:
            if t.name == 'RandomLabelsToImage':
                transform.transforms.remove(t)
                break
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', RuntimeWarning)
            transformed = transform(self.sample_subject)
            inverting_transform = transformed.get_inverse_transform()
            transformed_back = inverting_transform(transformed)
        assert transformed.t1.shape == transformed_back.t1.shape
        self.assert_tensor_equal(transformed.label.affine, transformed_back.label.affine)

    def test_different_interpolation(self):

        def model_probs(subject):
            subject = copy.deepcopy(subject)
            subject.im.set_data(torch.rand_like(subject.im.data))
            return subject

        def model_label(subject):
            subject = model_probs(subject)
            subject.im.set_data(torch.bernoulli(subject.im.data))
            return subject
        transform = tio.RandomAffine(image_interpolation='bspline')
        subject = copy.deepcopy(self.sample_subject)
        tensor = (torch.rand(1, 20, 20, 20) > 0.5).float()
        subject = tio.Subject(im=tio.ScalarImage(tensor=tensor))
        transformed = transform(subject)
        assert transformed.im.data.min() < 0
        assert transformed.im.data.max() > 1
        subject_probs = model_probs(transformed)
        transformed_back = subject_probs.apply_inverse_transform()
        assert transformed_back.im.data.min() < 0
        assert transformed_back.im.data.max() > 1
        transformed_back_linear = subject_probs.apply_inverse_transform(image_interpolation='linear')
        assert transformed_back_linear.im.data.min() >= 0
        assert transformed_back_linear.im.data.max() <= 1
        subject_label = model_label(transformed)
        transformed_back = subject_label.apply_inverse_transform()
        assert transformed_back.im.data.min() < 0
        assert transformed_back.im.data.max() > 1
        transformed_back_linear = subject_label.apply_inverse_transform(image_interpolation='nearest')
        assert transformed_back_linear.im.data.unique().tolist() == [0, 1]

def model_label(subject):
    subject = model_probs(subject)
    subject.im.set_data(torch.bernoulli(subject.im.data))
    return subject

def test_different_interpolation(self):

    def model_probs(subject):
        subject = copy.deepcopy(subject)
        subject.im.set_data(torch.rand_like(subject.im.data))
        return subject

    def model_label(subject):
        subject = model_probs(subject)
        subject.im.set_data(torch.bernoulli(subject.im.data))
        return subject
    transform = tio.RandomAffine(image_interpolation='bspline')
    subject = copy.deepcopy(self.sample_subject)
    tensor = (torch.rand(1, 20, 20, 20) > 0.5).float()
    subject = tio.Subject(im=tio.ScalarImage(tensor=tensor))
    transformed = transform(subject)
    assert transformed.im.data.min() < 0
    assert transformed.im.data.max() > 1
    subject_probs = model_probs(transformed)
    transformed_back = subject_probs.apply_inverse_transform()
    assert transformed_back.im.data.min() < 0
    assert transformed_back.im.data.max() > 1
    transformed_back_linear = subject_probs.apply_inverse_transform(image_interpolation='linear')
    assert transformed_back_linear.im.data.min() >= 0
    assert transformed_back_linear.im.data.max() <= 1
    subject_label = model_label(transformed)
    transformed_back = subject_label.apply_inverse_transform()
    assert transformed_back.im.data.min() < 0
    assert transformed_back.im.data.max() > 1
    transformed_back_linear = subject_label.apply_inverse_transform(image_interpolation='nearest')
    assert transformed_back_linear.im.data.unique().tolist() == [0, 1]

class TestRandomLabelsToImage(TorchioTestCase):
    """Tests for `RandomLabelsToImage`."""

    def test_random_simulation(self):
        """The transform runs without error and an 'image_from_labels' key is
        present in the transformed subject."""
        transform = RandomLabelsToImage(label_key='label')
        transformed = transform(self.sample_subject)
        self.assertIn('image_from_labels', transformed)

    def test_deterministic_simulation(self):
        """The transform creates an image where values are equal to given mean
        if standard deviation is zero.

        Using a label map.
        """
        transform = RandomLabelsToImage(label_key='label', mean=[0.5, 2], std=[0, 0])
        transformed = transform(self.sample_subject)
        self.assert_tensor_equal(transformed['image_from_labels'].data == 0.5, self.sample_subject['label'].data == 0)
        self.assert_tensor_equal(transformed['image_from_labels'].data == 2, self.sample_subject['label'].data == 1)

    def test_deterministic_simulation_with_discretized_label_map(self):
        """The transform creates an image where values are equal to given mean
        if standard deviation is zero.

        Using a discretized label map.
        """
        transform = RandomLabelsToImage(label_key='label', mean=[0.5, 2], std=[0, 0], discretize=True)
        transformed = transform(self.sample_subject)
        self.assert_tensor_equal(transformed['image_from_labels'].data == 0.5, self.sample_subject['label'].data == 0)
        self.assert_tensor_equal(transformed['image_from_labels'].data == 2, self.sample_subject['label'].data == 1)

    def test_deterministic_simulation_with_pv_map(self):
        """The transform creates an image where values are equal to given mean
        weighted by partial-volume if standard deviation is zero."""
        subject = self.get_subject_with_partial_volume_label_map(components=2)
        transform = RandomLabelsToImage(label_key='label', mean=[0.5, 1], std=[0, 0])
        transformed = transform(subject)
        self.assert_tensor_almost_equal(transformed['image_from_labels'].data[0], subject['label'].data[0] * 0.5 + subject['label'].data[1] * 1)
        assert transformed['image_from_labels'].data.shape == (1, 10, 20, 30)

    def test_deterministic_simulation_with_discretized_pv_map(self):
        """The transform creates an image where values are equal to given mean
        if standard deviation is zero.

        Using a discretized partial-volume label map.
        """
        subject = self.get_subject_with_partial_volume_label_map()
        transform = RandomLabelsToImage(label_key='label', mean=[0.5], std=[0], discretize=True)
        transformed = transform(subject)
        self.assert_tensor_almost_equal(transformed['image_from_labels'].data, (subject['label'].data > 0) * 0.5)

    def test_filling(self):
        """The transform can fill in the generated image with an already
        existing image.

        Using a label map.
        """
        transform = RandomLabelsToImage(label_key='label', image_key='t1', used_labels=[1])
        t1_indices = self.sample_subject['label'].data == 0
        transformed = transform(self.sample_subject)
        self.assert_tensor_almost_equal(transformed['t1'].data[t1_indices], self.sample_subject['t1'].data[t1_indices])

    def test_filling_with_discretized_label_map(self):
        """The transform can fill in the generated image with an already
        existing image.

        Using a discretized label map.
        """
        transform = RandomLabelsToImage(label_key='label', image_key='t1', discretize=True, used_labels=[1])
        t1_indices = self.sample_subject['label'].data < 0.5
        transformed = transform(self.sample_subject)
        self.assert_tensor_almost_equal(transformed['t1'].data[t1_indices], self.sample_subject['t1'].data[t1_indices])

    def test_filling_with_discretized_pv_label_map(self):
        """The transform can fill in the generated image with an already
        existing image.

        Using a discretized partial-volume label map.
        """
        subject = self.get_subject_with_partial_volume_label_map(components=2)
        transform = RandomLabelsToImage(label_key='label', image_key='t1', discretize=True, used_labels=[1])
        t1_indices = subject['label'].data.argmax(dim=0) == 0
        transformed = transform(subject)
        self.assert_tensor_almost_equal(transformed['t1'].data[0][t1_indices], subject['t1'].data[0][t1_indices])

    def test_filling_without_any_hole(self):
        """The transform does not fill anything if there is no hole."""
        transform = RandomLabelsToImage(label_key='label', image_key='t1', default_std=0, default_mean=-1)
        original_t1 = self.sample_subject.t1.data.clone()
        transformed = transform(self.sample_subject)
        self.assert_tensor_not_equal(original_t1, transformed.t1.data)

    def test_with_bad_default_mean_range(self):
        """The transform raises an error if default_mean is not a single value
        nor a tuple of two values."""
        with pytest.raises(ValueError):
            RandomLabelsToImage(label_key='label', default_mean=(0, 1, 2))

    def test_with_bad_default_mean_type(self):
        """The transform raises an error if default_mean has the wrong type."""
        with pytest.raises(ValueError):
            RandomLabelsToImage(label_key='label', default_mean='wrong')

    def test_with_bad_default_std_range(self):
        """The transform raises an error if default_std is not a single value
        nor a tuple of two values."""
        with pytest.raises(ValueError):
            RandomLabelsToImage(label_key='label', default_std=(0, 1, 2))

    def test_with_bad_default_std_type(self):
        """The transform raises an error if default_std has the wrong type."""
        with pytest.raises(ValueError):
            RandomLabelsToImage(label_key='label', default_std='wrong')

    def test_with_wrong_label_key_type(self):
        """The transform raises an error if a wrong type is given for
        label_key."""
        with pytest.raises(TypeError):
            RandomLabelsToImage(label_key=42)

    def test_with_wrong_used_labels_type(self):
        """The transform raises an error if a wrong type is given for
        used_labels."""
        with pytest.raises(TypeError):
            RandomLabelsToImage(label_key='label', used_labels=42)

    def test_with_wrong_used_labels_elements_type(self):
        """The transform raises an error if wrong type are given for
        used_labels elements."""
        with pytest.raises(ValueError):
            RandomLabelsToImage(label_key='label', used_labels=['wrong'])

    def test_with_wrong_mean_type(self):
        """The transform raises an error if wrong type is given for mean."""
        with pytest.raises(TypeError):
            RandomLabelsToImage(label_key='label', mean=42)

    def test_with_wrong_mean_elements_type(self):
        """The transform raises an error if wrong type are given for mean
        elements."""
        with pytest.raises(ValueError):
            RandomLabelsToImage(label_key='label', mean=['wrong'])

    def test_with_wrong_std_type(self):
        """The transform raises an error if wrong type is given for std."""
        with pytest.raises(TypeError):
            RandomLabelsToImage(label_key='label', std=42)

    def test_with_wrong_std_elements_type(self):
        """The transform raises an error if wrong type are given for std
        elements."""
        with pytest.raises(ValueError):
            RandomLabelsToImage(label_key='label', std=['wrong'])

    def test_mean_and_std_len_not_matching(self):
        """The transform raises an error if mean and std length don't match."""
        with pytest.raises(AssertionError):
            RandomLabelsToImage(label_key='label', mean=[0], std=[0, 1])

    def test_mean_and_used_labels_len_not_matching(self):
        """The transform raises an error if mean and used_labels length don't
        match."""
        with pytest.raises(AssertionError):
            RandomLabelsToImage(label_key='label', mean=[0], used_labels=[0, 1])

    def test_std_and_used_labels_len_not_matching(self):
        """The transform raises an error if std and used_labels length don't
        match."""
        with pytest.raises(AssertionError):
            RandomLabelsToImage(label_key='label', std=[0], used_labels=[0, 1])

    def test_mean_not_matching_number_of_labels(self):
        """The transform raises an error at runtime if mean length does not
        match label numbers."""
        transform = RandomLabelsToImage(label_key='label', mean=[0])
        with pytest.raises(RuntimeError):
            transform(self.sample_subject)

    def test_std_not_matching_number_of_labels(self):
        """The transform raises an error at runtime if std length does not
        match label numbers."""
        transform = RandomLabelsToImage(label_key='label', std=[1, 2, 3])
        with pytest.raises(RuntimeError):
            transform(self.sample_subject)

    def test_bad_range(self):
        with pytest.raises(ValueError):
            RandomLabelsToImage(default_mean=(2, 1))

    def test_no_labels(self):
        transform = RandomLabelsToImage()
        with pytest.raises(RuntimeError):
            transform(self.sample_subject.t1)

def test_filling_without_any_hole(self):
    """The transform does not fill anything if there is no hole."""
    transform = RandomLabelsToImage(label_key='label', image_key='t1', default_std=0, default_mean=-1)
    original_t1 = self.sample_subject.t1.data.clone()
    transformed = transform(self.sample_subject)
    self.assert_tensor_not_equal(original_t1, transformed.t1.data)

class TestClamp(TorchioTestCase):
    """Tests for :class:`tio.Clamp` class."""

    def test_out_min_max(self):
        transform = tio.Clamp(out_min=0, out_max=1)
        transformed = transform(self.sample_subject)
        assert transformed.t1.data.min() == 0
        assert transformed.t1.data.max() == 1

    def test_ct(self):
        ct_max = 1500
        ct_min = -2000
        ct_range = ct_max - ct_min
        tensor = torch.rand(1, 30, 30, 30) * ct_range + ct_min
        ct = tio.ScalarImage(tensor=tensor)
        ct_air = -1000
        ct_bone = 1000
        clamp = tio.Clamp(ct_air, ct_bone)
        clamped = clamp(ct)
        assert clamped.data.min() == ct_air
        assert clamped.data.max() == ct_bone

    def test_too_many_values_for_out_min(self):
        with pytest.raises(TypeError):
            clamp = tio.Clamp(out_min=(1, 2))
            clamp(self.sample_subject)

    def test_too_many_values_for_out_max(self):
        with pytest.raises(TypeError):
            clamp = tio.Clamp(out_max=(1, 2))
            clamp(self.sample_subject)

    def test_wrong_out_min_type(self):
        with pytest.raises(TypeError):
            clamp = tio.Clamp(out_min='foo')
            clamp(self.sample_subject)

    def test_wrong_out_max_type(self):
        with pytest.raises(TypeError):
            clamp = tio.Clamp(out_max='foo')
            clamp(self.sample_subject)

def test_out_min_max(self):
    transform = tio.Clamp(out_min=0, out_max=1)
    transformed = transform(self.sample_subject)
    assert transformed.t1.data.min() == 0
    assert transformed.t1.data.max() == 1

def test_ct(self):
    ct_max = 1500
    ct_min = -2000
    ct_range = ct_max - ct_min
    tensor = torch.rand(1, 30, 30, 30) * ct_range + ct_min
    ct = tio.ScalarImage(tensor=tensor)
    ct_air = -1000
    ct_bone = 1000
    clamp = tio.Clamp(ct_air, ct_bone)
    clamped = clamp(ct)
    assert clamped.data.min() == ct_air
    assert clamped.data.max() == ct_bone

def test_too_many_values_for_out_min(self):
    with pytest.raises(TypeError):
        clamp = tio.Clamp(out_min=(1, 2))
        clamp(self.sample_subject)

def test_too_many_values_for_out_max(self):
    with pytest.raises(TypeError):
        clamp = tio.Clamp(out_max=(1, 2))
        clamp(self.sample_subject)

def test_wrong_out_min_type(self):
    with pytest.raises(TypeError):
        clamp = tio.Clamp(out_min='foo')
        clamp(self.sample_subject)

def test_wrong_out_max_type(self):
    with pytest.raises(TypeError):
        clamp = tio.Clamp(out_max='foo')
        clamp(self.sample_subject)

class TestRescaleIntensity(TorchioTestCase):

    def test_rescale_to_same_intentisy(self):
        min_t1 = float(self.sample_subject.t1.data.min())
        max_t1 = float(self.sample_subject.t1.data.max())
        transform = tio.RescaleIntensity(out_min_max=(min_t1, max_t1))
        transformed = transform(self.sample_subject)
        assert np.allclose(transformed.t1.data, self.sample_subject.t1.data, rtol=0, atol=1e-05)

    def test_min_max(self):
        transform = tio.RescaleIntensity(out_min_max=(0, 1))
        transformed = transform(self.sample_subject)
        assert transformed.t1.data.min() == 0
        assert transformed.t1.data.max() == 1

    def test_percentiles(self):
        low_quantile = np.percentile(self.sample_subject.t1.data, 5)
        high_quantile = np.percentile(self.sample_subject.t1.data, 95)
        low_indices = (self.sample_subject.t1.data < low_quantile).nonzero(as_tuple=True)
        high_indices = (self.sample_subject.t1.data > high_quantile).nonzero(as_tuple=True)
        rescale = tio.RescaleIntensity(out_min_max=(0, 1), percentiles=(5, 95))
        transformed = rescale(self.sample_subject)
        assert (transformed.t1.data[low_indices] == 0).all()
        assert (transformed.t1.data[high_indices] == 1).all()

    def test_masking_using_label(self):
        transform = tio.RescaleIntensity(out_min_max=(0, 1), percentiles=(5, 95), masking_method='label')
        transformed = transform(self.sample_subject)
        mask = self.sample_subject.label.data > 0
        low_quantile = np.percentile(self.sample_subject.t1.data[mask], 5)
        high_quantile = np.percentile(self.sample_subject.t1.data[mask], 95)
        low_indices = (self.sample_subject.t1.data < low_quantile).nonzero(as_tuple=True)
        high_indices = (self.sample_subject.t1.data > high_quantile).nonzero(as_tuple=True)
        assert transformed.t1.data.min() == 0
        assert transformed.t1.data.max() == 1
        assert (transformed.t1.data[low_indices] == 0).all()
        assert (transformed.t1.data[high_indices] == 1).all()

    def test_ct(self):
        ct_max = 1500
        ct_min = -2000
        ct_range = ct_max - ct_min
        tensor = torch.rand(1, 30, 30, 30) * ct_range + ct_min
        ct = tio.ScalarImage(tensor=tensor)
        ct_air = -1000
        ct_bone = 1000
        rescale = tio.RescaleIntensity(out_min_max=(-1, 1), in_min_max=(ct_air, ct_bone))
        rescaled = rescale(ct)
        assert rescaled.data.min() < -1
        assert rescaled.data.max() > 1

    def test_out_min_higher_than_out_max(self):
        with pytest.raises(ValueError):
            tio.RescaleIntensity(out_min_max=(1, 0))

    def test_too_many_values_for_out_min_max(self):
        with pytest.raises(ValueError):
            tio.RescaleIntensity(out_min_max=(1, 2, 3))

    def test_wrong_out_min_max_type(self):
        with pytest.raises(ValueError):
            tio.RescaleIntensity(out_min_max='wrong')

    def test_min_percentile_higher_than_max_percentile(self):
        with pytest.raises(ValueError):
            tio.RescaleIntensity(out_min_max=(0, 1), percentiles=(1, 0))

    def test_too_many_values_for_percentiles(self):
        with pytest.raises(ValueError):
            tio.RescaleIntensity(out_min_max=(0, 1), percentiles=(1, 2, 3))

    def test_wrong_percentiles_type(self):
        with pytest.raises(ValueError):
            tio.RescaleIntensity(out_min_max=(0, 1), percentiles='wrong')

    def test_empty_mask(self):
        subject = copy.deepcopy(self.sample_subject)
        subject.label.set_data(subject.label.data * 0)
        rescale = tio.RescaleIntensity(masking_method='label')
        with pytest.warns(RuntimeWarning):
            rescale(subject)

    def test_persistent_in_min_max(self):
        img1 = torch.tensor([[[[0, 1]]]])
        img2 = torch.tensor([[[[0, 10]]]])
        rescale = tio.RescaleIntensity(out_min_max=(0, 1))
        assert rescale(img1).data.flatten().tolist() == [0, 1]
        assert rescale(img2).data.flatten().tolist() == [0, 1]
        rescale = tio.RescaleIntensity(out_min_max=(0, 1))
        assert rescale(img2).data.flatten().tolist() == [0, 1]
        assert rescale(img1).data.flatten().tolist() == [0, 1]

def test_rescale_to_same_intentisy(self):
    min_t1 = float(self.sample_subject.t1.data.min())
    max_t1 = float(self.sample_subject.t1.data.max())
    transform = tio.RescaleIntensity(out_min_max=(min_t1, max_t1))
    transformed = transform(self.sample_subject)
    assert np.allclose(transformed.t1.data, self.sample_subject.t1.data, rtol=0, atol=1e-05)

def test_min_max(self):
    transform = tio.RescaleIntensity(out_min_max=(0, 1))
    transformed = transform(self.sample_subject)
    assert transformed.t1.data.min() == 0
    assert transformed.t1.data.max() == 1

def test_masking_using_label(self):
    transform = tio.RescaleIntensity(out_min_max=(0, 1), percentiles=(5, 95), masking_method='label')
    transformed = transform(self.sample_subject)
    mask = self.sample_subject.label.data > 0
    low_quantile = np.percentile(self.sample_subject.t1.data[mask], 5)
    high_quantile = np.percentile(self.sample_subject.t1.data[mask], 95)
    low_indices = (self.sample_subject.t1.data < low_quantile).nonzero(as_tuple=True)
    high_indices = (self.sample_subject.t1.data > high_quantile).nonzero(as_tuple=True)
    assert transformed.t1.data.min() == 0
    assert transformed.t1.data.max() == 1
    assert (transformed.t1.data[low_indices] == 0).all()
    assert (transformed.t1.data[high_indices] == 1).all()

def test_ct(self):
    ct_max = 1500
    ct_min = -2000
    ct_range = ct_max - ct_min
    tensor = torch.rand(1, 30, 30, 30) * ct_range + ct_min
    ct = tio.ScalarImage(tensor=tensor)
    ct_air = -1000
    ct_bone = 1000
    rescale = tio.RescaleIntensity(out_min_max=(-1, 1), in_min_max=(ct_air, ct_bone))
    rescaled = rescale(ct)
    assert rescaled.data.min() < -1
    assert rescaled.data.max() > 1

class TestZNormalization(TorchioTestCase):
    """Tests for :class:`ZNormalization` class."""

    def test_z_normalization(self):
        transform = tio.ZNormalization()
        transformed = transform(self.sample_subject)
        assert float(transformed.t1.data.mean()) == pytest.approx(0, abs=1e-06)
        assert float(transformed.t1.data.std()) == pytest.approx(1)

    def test_no_std(self):
        image = tio.ScalarImage(tensor=torch.ones(1, 2, 2, 2))
        with pytest.raises(RuntimeError):
            tio.ZNormalization()(image)

    def test_dtype(self):
        tensor_int = (100 * torch.rand(1, 2, 3, 4)).byte()
        transform = tio.ZNormalization(masking_method=tio.ZNormalization.mean)
        transform(tensor_int)
        transform = tio.ZNormalization()
        transform(tensor_int)

def test_z_normalization(self):
    transform = tio.ZNormalization()
    transformed = transform(self.sample_subject)
    assert float(transformed.t1.data.mean()) == pytest.approx(0, abs=1e-06)
    assert float(transformed.t1.data.std()) == pytest.approx(1)

