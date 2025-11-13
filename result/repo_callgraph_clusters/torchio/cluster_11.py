# Cluster 11

def _create_categorical_colormap(data: torch.Tensor, cmap_name: str='glasbey_category10') -> tuple[ListedColormap, BoundaryNorm]:
    num_classes = int(data.max())
    mpl, _ = import_mpl_plt()
    colors = [(0, 0, 0), (1, 1, 1)]
    if num_classes > 1:
        from .external.imports import get_colorcet
        colorcet = get_colorcet()
        cmap = getattr(colorcet.cm, cmap_name)
        color_cycle = cycle(cmap.colors)
        distinct_colors = [next(color_cycle) for _ in range(num_classes - 1)]
        colors.extend(distinct_colors)
    boundaries = np.arange(-0.5, num_classes + 1.5, 1)
    colormap = mpl.colors.ListedColormap(colors)
    boundary_norm = mpl.colors.BoundaryNorm(boundaries, ncolors=colormap.N)
    return (colormap, boundary_norm)

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

class LabelMap(Image):
    """Image whose pixel values represent segmentation labels.

    A sequence of paths to 3D images can be passed to create a 4D image.
    This is useful to create a
    `tissue probability map (TPM) <https://andysbrainbook.readthedocs.io/en/latest/SPM/SPM_Short_Course/SPM_04_Preprocessing/04_SPM_Segmentation.html#tissue-probability-maps>`,
    which contains the probability of each voxel belonging to a certain tissue type,
    or to create a label map with overlapping labels.

    Intensity transforms are not applied to these images.

    Nearest neighbor interpolation is always used to resample label maps,
    independently of the specified interpolation type in the transform
    instantiation.

    Example:
        >>> import torch
        >>> import torchio as tio
        >>> binary_tensor = torch.rand(1, 128, 128, 68) > 0.5
        >>> label_map = tio.LabelMap(tensor=binary_tensor)  # from a tensor
        >>> label_map = tio.LabelMap('t1_seg.nii.gz')  # from a file
        >>> # Create a 4D tissue probability map from different 3D images
        >>> tissues = 'gray_matter.nii.gz', 'white_matter.nii.gz', 'csf.nii.gz'
        >>> tpm = tio.LabelMap(tissues)

    See :class:`~torchio.Image` for more information.
    """

    def __init__(self, *args, **kwargs):
        if 'type' in kwargs and kwargs['type'] != LABEL:
            raise ValueError('Type of LabelMap is always torchio.LABEL')
        kwargs.update({'type': LABEL})
        super().__init__(*args, **kwargs)

    def count_nonzero(self) -> int:
        """Get the number of voxels that are not 0."""
        return int(self.data.count_nonzero().item())

    def count_labels(self) -> dict[int, int]:
        """Get the number of voxels in each label."""
        values_list = self.data.flatten().tolist()
        counter = Counter(values_list)
        counts = {label: counter[label] for label in sorted(counter)}
        return counts

def count_nonzero(self) -> int:
    """Get the number of voxels that are not 0."""
    return int(self.data.count_nonzero().item())

class Queue(Dataset):
    """Queue used for stochastic patch-based training.

    A training iteration (i.e., forward and backward pass) performed on a
    GPU is usually faster than loading, preprocessing, augmenting, and cropping
    a volume on a CPU.
    Most preprocessing operations could be performed using a GPU,
    but these devices are typically reserved for training the CNN so that batch
    size and input tensor size can be as large as possible.
    Therefore, it is beneficial to prepare (i.e., load, preprocess and augment)
    the volumes using multiprocessing CPU techniques in parallel with the
    forward-backward passes of a training iteration.
    Once a volume is appropriately prepared, it is computationally beneficial to
    sample multiple patches from a volume rather than having to prepare the same
    volume each time a patch needs to be extracted.
    The sampled patches are then stored in a buffer or *queue* until
    the next training iteration, at which point they are loaded onto the GPU
    for inference.
    For this, TorchIO provides the :class:`~torchio.data.Queue` class, which
    also inherits from the PyTorch :class:`~torch.utils.data.Dataset`.
    In this queueing system,
    samplers behave as generators that yield patches from random locations
    in volumes contained in the :class:`~torchio.data.SubjectsDataset`.

    The end of a training epoch is defined as the moment after which patches
    from all subjects have been used for training.
    At the beginning of each training epoch,
    the subjects list in the :class:`~torchio.data.SubjectsDataset` is shuffled,
    as is typically done in machine learning pipelines to increase variance
    of training instances during model optimization.
    A PyTorch loader queries the datasets copied in each process,
    which load and process the volumes in parallel on the CPU.
    A patches list is filled with patches extracted by the sampler,
    and the queue is shuffled once it has reached a specified maximum length so
    that batches are composed of patches from different subjects.
    The internal data loader continues querying the
    :class:`~torchio.data.SubjectsDataset` using multiprocessing.
    The patches list, when emptied, is refilled with new patches.
    A second data loader, external to the queue,
    may be used to collate batches of patches stored in the queue,
    which are passed to the neural network.

    Args:
        subjects_dataset: Instance of :class:`~torchio.data.SubjectsDataset`.
        max_length: Maximum number of patches that can be stored in the queue.
            Using a large number means that the queue needs to be filled less
            often, but more CPU memory is needed to store the patches.
        samples_per_volume: Default number of patches to extract from each
            volume. If a subject contains an attribute :attr:`num_samples`, it
            will be used instead of :attr:`samples_per_volume`.
            A small number of patches ensures a large variability in the queue,
            but training will be slower.
        sampler: A subclass of :class:`~torchio.data.sampler.PatchSampler` used
            to extract patches from the volumes.
        subject_sampler: Sampler to get subjects from the dataset.
            It should be an instance of
            :class:`~torch.utils.data.distributed.DistributedSampler` when
            running `distributed training
            <https://pytorch.org/tutorials/beginner/dist_overview.html>`_.
        num_workers: Number of subprocesses to use for data loading
            (as in :class:`torch.utils.data.DataLoader`).
            ``0`` means that the data will be loaded in the main process.
        shuffle_subjects: If ``True``, the subjects dataset is shuffled at the
            beginning of each epoch, i.e. when all patches from all subjects
            have been processed.
        shuffle_patches: If ``True``, patches are shuffled after filling the
            queue.
        start_background: If ``True``, the loader will start working in the
            background as soon as the queue is instantiated.
        verbose: If ``True``, some debugging messages will be printed.

    This diagram represents the connection between
    a :class:`~torchio.data.SubjectsDataset`,
    a :class:`~torchio.data.Queue`
    and the :class:`~torch.utils.data.DataLoader` used to pop batches from the
    queue.

    .. image:: https://raw.githubusercontent.com/TorchIO-project/torchio/main/docs/images/diagram_patches.svg
        :alt: Training with patches

    This sketch can be used to experiment and understand how the queue works.
    In this case, :attr:`shuffle_subjects` is ``False``
    and :attr:`shuffle_patches` is ``True``.

    .. raw:: html

        <embed>
            <iframe style="width: 640px; height: 360px; overflow: hidden;" scrolling="no" frameborder="0" src="https://editor.p5js.org/fepegar/full/DZwjZzkkV"></iframe>
        </embed>

    .. note:: :attr:`num_workers` refers to the number of workers used to
        load and transform the volumes. Multiprocessing is not needed to pop
        patches from the queue, so you should always use ``num_workers=0`` for
        the :class:`~torch.utils.data.DataLoader` you instantiate to generate
        training batches.

    Example:

    >>> import torch
    >>> import torchio as tio
    >>> patch_size = 96
    >>> queue_length = 300
    >>> samples_per_volume = 10
    >>> sampler = tio.data.UniformSampler(patch_size)
    >>> subject = tio.datasets.Colin27()
    >>> subjects_dataset = tio.SubjectsDataset(10 * [subject])
    >>> patches_queue = tio.Queue(
    ...     subjects_dataset,
    ...     queue_length,
    ...     samples_per_volume,
    ...     sampler,
    ...     num_workers=4,
    ... )
    >>> patches_loader = tio.SubjectsLoader(
    ...     patches_queue,
    ...     batch_size=16,
    ...     num_workers=0,  # this must be 0
    ... )
    >>> num_epochs = 2
    >>> model = torch.nn.Identity()
    >>> for epoch_index in range(num_epochs):
    ...     for patches_batch in patches_loader:
    ...         inputs = patches_batch['t1'][tio.DATA]  # key 't1' is in subject
    ...         targets = patches_batch['brain'][tio.DATA]  # key 'brain' is in subject
    ...         logits = model(inputs)  # model being an instance of torch.nn.Module


    Example:

    >>> # Usage with distributed training
    >>> import torch.distributed as dist
    >>> from torch.utils.data.distributed import DistributedSampler
    >>> # Assume a process running on distributed node 3
    >>> rank = 3
    >>> patch_sampler = tio.data.UniformSampler(patch_size)
    >>> subject = tio.datasets.Colin27()
    >>> subjects_dataset = tio.SubjectsDataset(10 * [subject])
    >>> subject_sampler = dist.DistributedSampler(
    ...     subjects_dataset,
    ...     rank=local_rank,
    ...     shuffle=True,
    ...     drop_last=True,
    ... )
    >>> # Each process is assigned (len(subjects_dataset) // num_processes) subjects
    >>> patches_queue = tio.Queue(
    ...     subjects_dataset,
    ...     queue_length,
    ...     samples_per_volume,
    ...     patch_sampler,
    ...     num_workers=4,
    ...     subject_sampler=subject_sampler,
    ... )
    >>> patches_loader = tio.SubjectsLoader(
    ...     patches_queue,
    ...     batch_size=16,
    ...     num_workers=0,  # this must be 0
    ... )
    >>> num_epochs = 2
    >>> model = torch.nn.Identity()
    >>> for epoch_index in range(num_epochs):
    ...     subject_sampler.set_epoch(epoch_index)
    ...     for patches_batch in patches_loader:
    ...         inputs = patches_batch['t1'][tio.DATA]  # key 't1' is in subject
    ...         targets = patches_batch['brain'][tio.DATA]  # key 'brain' is in subject
    ...         logits = model(inputs)  # model being an instance of torch.nn.Module
    """

    def __init__(self, subjects_dataset: SubjectsDataset, max_length: int, samples_per_volume: int, sampler: PatchSampler, subject_sampler: Sampler | None=None, num_workers: int=0, shuffle_subjects: bool=True, shuffle_patches: bool=True, start_background: bool=True, verbose: bool=False):
        self.subjects_dataset = subjects_dataset
        self.max_length = max_length
        self.shuffle_subjects = shuffle_subjects
        self.shuffle_patches = shuffle_patches
        self.samples_per_volume = samples_per_volume
        self.sampler = sampler
        self.subject_sampler = subject_sampler
        self.num_workers = num_workers
        self.verbose = verbose
        self._subjects_iterable = None
        self._incomplete_subject: Subject | None = None
        self._num_patches_incomplete = 0
        self._num_sampled_subjects = 0
        if start_background:
            self._initialize_subjects_iterable()
        self.patches_list: list[Subject] = []
        if self.shuffle_subjects and self.subject_sampler is not None:
            raise ValueError('The flag shuffle_subjects cannot be set when a subject sampler is passed')

    def __len__(self):
        return self.iterations_per_epoch

    def __getitem__(self, _):
        if not self.patches_list:
            self._print('Patches list is empty.')
            self._fill()
            self.patches_list.reverse()
        sample_patch = self.patches_list.pop()
        return sample_patch

    def __repr__(self):
        attributes = [f'max_length={self.max_length}', f'num_subjects={self.num_subjects}', f'num_patches={self.num_patches}', f'samples_per_volume={self.samples_per_volume}', f'iterations_per_epoch={self.iterations_per_epoch}']
        attributes_string = ', '.join(attributes)
        return f'Queue({attributes_string})'

    def _print(self, *args):
        if self.verbose:
            print(*args)

    def _initialize_subjects_iterable(self):
        self._subjects_iterable = self._get_subjects_iterable()

    @property
    def subjects_iterable(self):
        if self._subjects_iterable is None:
            self._initialize_subjects_iterable()
        return self._subjects_iterable

    @property
    def num_subjects(self) -> int:
        if self.subject_sampler is not None:
            if not hasattr(self.subject_sampler, '__len__'):
                raise ValueError('The subject sampler passed to the queue must have a __len__ method')
            num_subjects = len(self.subject_sampler)
        else:
            num_subjects = len(self.subjects_dataset)
        return num_subjects

    @property
    def num_patches(self) -> int:
        return len(self.patches_list)

    @property
    def iterations_per_epoch(self) -> int:
        all_subjects_list = self.subjects_dataset.dry_iter()
        if self.subject_sampler is not None:
            subjects_list = []
            for subject_index in self.subject_sampler:
                subject = all_subjects_list[subject_index]
                subjects_list.append(subject)
        else:
            subjects_list = all_subjects_list
        total_num_patches = sum((self._get_subject_num_samples(subject) for subject in subjects_list))
        return total_num_patches

    def _get_subject_num_samples(self, subject):
        num_samples = getattr(subject, NUM_SAMPLES, self.samples_per_volume)
        return num_samples

    def _fill(self) -> None:
        assert self.sampler is not None
        if self._incomplete_subject is not None:
            subject = self._incomplete_subject
            iterable = self.sampler(subject)
            patches = list(islice(iterable, self._num_patches_incomplete))
            self.patches_list.extend(patches)
            self._incomplete_subject = None
        while True:
            subject = self._get_next_subject()
            iterable = self.sampler(subject)
            num_samples = self._get_subject_num_samples(subject)
            num_free_slots = self.max_length - len(self.patches_list)
            if num_free_slots < num_samples:
                self._incomplete_subject = subject
                self._num_patches_incomplete = num_samples - num_free_slots
            num_samples = min(num_samples, num_free_slots)
            patches = list(islice(iterable, num_samples))
            self.patches_list.extend(patches)
            self._num_sampled_subjects += 1
            list_full = len(self.patches_list) >= self.max_length
            all_sampled = self._num_sampled_subjects >= self.num_subjects
            if list_full or all_sampled:
                break
        if self.shuffle_patches:
            self._shuffle_patches_list()

    def _shuffle_patches_list(self):
        indices = torch.randperm(self.num_patches)
        self.patches_list = [self.patches_list[i] for i in indices]

    def _get_next_subject(self) -> Subject:
        try:
            subject = next(self.subjects_iterable)
        except StopIteration as exception:
            self._print('Queue is empty:', exception)
            self._initialize_subjects_iterable()
            subject = next(self.subjects_iterable)
        except AssertionError as exception:
            if 'can only test a child process' in str(exception):
                message = 'The number of workers for the data loader used to pop patches from the queue should be 0. Is it?'
                raise RuntimeError(message) from exception
            raise exception
        return subject

    @staticmethod
    def _get_first_item(batch):
        return batch[0]

    def _get_subjects_iterable(self) -> Iterator:
        self._print(f'\nCreating subjects loader with {self.num_workers} workers')
        subjects_loader = DataLoader(self.subjects_dataset, num_workers=self.num_workers, batch_size=1, collate_fn=self._get_first_item, sampler=self.subject_sampler, shuffle=self.shuffle_subjects)
        self._num_sampled_subjects = 0
        return iter(subjects_loader)

    def get_max_memory(self, subject: Subject | None=None) -> int:
        """Get the maximum RAM occupied by the patches queue in bytes.

        Args:
            subject: Sample subject to compute the size of a patch.
        """
        images_channels = 0
        if subject is None:
            subject = self.subjects_dataset[0]
        for image in subject.get_images(intensity_only=False):
            images_channels += len(image.data)
        voxels_in_patch = int(self.sampler.patch_size.prod() * images_channels)
        bytes_per_patch = 4 * voxels_in_patch
        return int(bytes_per_patch * self.max_length)

    def get_max_memory_pretty(self, subject: Subject | None=None) -> str:
        """Get human-readable maximum RAM occupied by the patches queue.

        Args:
            subject: Sample subject to compute the size of a patch.
        """
        memory = self.get_max_memory(subject=subject)
        return humanize.naturalsize(memory, binary=True)

@property
def iterations_per_epoch(self) -> int:
    all_subjects_list = self.subjects_dataset.dry_iter()
    if self.subject_sampler is not None:
        subjects_list = []
        for subject_index in self.subject_sampler:
            subject = all_subjects_list[subject_index]
            subjects_list.append(subject)
    else:
        subjects_list = all_subjects_list
    total_num_patches = sum((self._get_subject_num_samples(subject) for subject in subjects_list))
    return total_num_patches

def _fill(self) -> None:
    assert self.sampler is not None
    if self._incomplete_subject is not None:
        subject = self._incomplete_subject
        iterable = self.sampler(subject)
        patches = list(islice(iterable, self._num_patches_incomplete))
        self.patches_list.extend(patches)
        self._incomplete_subject = None
    while True:
        subject = self._get_next_subject()
        iterable = self.sampler(subject)
        num_samples = self._get_subject_num_samples(subject)
        num_free_slots = self.max_length - len(self.patches_list)
        if num_free_slots < num_samples:
            self._incomplete_subject = subject
            self._num_patches_incomplete = num_samples - num_free_slots
        num_samples = min(num_samples, num_free_slots)
        patches = list(islice(iterable, num_samples))
        self.patches_list.extend(patches)
        self._num_sampled_subjects += 1
        list_full = len(self.patches_list) >= self.max_length
        all_sampled = self._num_sampled_subjects >= self.num_subjects
        if list_full or all_sampled:
            break
    if self.shuffle_patches:
        self._shuffle_patches_list()

def get_max_memory_pretty(self, subject: Subject | None=None) -> str:
    """Get human-readable maximum RAM occupied by the patches queue.

        Args:
            subject: Sample subject to compute the size of a patch.
        """
    memory = self.get_max_memory(subject=subject)
    return humanize.naturalsize(memory, binary=True)

class GridSampler(PatchSampler):
    """Extract patches across a whole volume.

    Grid samplers are useful to perform inference using all patches from a
    volume. It is often used with a :class:`~torchio.data.GridAggregator`.

    Args:
        subject: Instance of :class:`~torchio.data.Subject`
            from which patches will be extracted.
        patch_size: Tuple of integers :math:`(w, h, d)` to generate patches
            of size :math:`w \\times h \\times d`.
            If a single number :math:`n` is provided,
            :math:`w = h = d = n`.
        patch_overlap: Tuple of even integers :math:`(w_o, h_o, d_o)`
            specifying the overlap between patches for dense inference. If a
            single number :math:`n` is provided, :math:`w_o = h_o = d_o = n`.
        padding_mode: Same as :attr:`padding_mode` in
            :class:`~torchio.transforms.Pad`. If ``None``, the volume will not
            be padded before sampling and patches at the border will not be
            cropped by the aggregator.
            Otherwise, the volume will be padded with
            :math:`\\left(\\frac{w_o}{2}, \\frac{h_o}{2}, \\frac{d_o}{2} \\right)`
            on each side before sampling. If the sampler is passed to a
            :class:`~torchio.data.GridAggregator`, it will crop the output
            to its original size.

    Example:

        >>> import torchio as tio
        >>> colin = tio.datasets.Colin27()
        >>> sampler = tio.GridSampler(colin, patch_size=88)
        >>> for i, patch in enumerate(sampler()):
        ...     patch.t1.save(f'patch_{i}.nii.gz')
        ...
        >>> # To figure out the number of patches beforehand:
        >>> sampler = tio.GridSampler(colin, patch_size=88)
        >>> len(sampler)
        8

    .. note:: Adapted from NiftyNet. See `this NiftyNet tutorial
        <https://niftynet.readthedocs.io/en/dev/window_sizes.html>`_ for more
        information about patch based sampling. Note that
        :attr:`patch_overlap` is twice :attr:`border` in NiftyNet
        tutorial.
    """

    def __init__(self, subject: Subject, patch_size: TypeSpatialShape, patch_overlap: TypeSpatialShape=(0, 0, 0), padding_mode: str | float | None=None):
        super().__init__(patch_size)
        self.patch_overlap = np.array(to_tuple(patch_overlap, length=3))
        self.padding_mode = padding_mode
        self.subject = self._pad(subject)
        self.locations = self._compute_locations(self.subject)

    def __len__(self):
        return len(self.locations)

    def __getitem__(self, index):
        location = self.locations[index]
        index_ini = location[:3]
        cropped_subject = self.crop(self.subject, index_ini, self.patch_size)
        return cropped_subject

    def __call__(self, subject: Subject | None=None, num_patches: int | None=None) -> Generator[Subject]:
        subject = self.subject if subject is None else subject
        return super().__call__(subject, num_patches=num_patches)

    def _pad(self, subject: Subject) -> Subject:
        if self.padding_mode is not None:
            from ...transforms import Pad
            border = self.patch_overlap // 2
            padding = border.repeat(2)
            pad = Pad(padding, padding_mode=self.padding_mode)
            subject = pad(subject)
        return subject

    def _compute_locations(self, subject: Subject):
        sizes = (subject.spatial_shape, self.patch_size, self.patch_overlap)
        self._parse_sizes(*sizes)
        return self._get_patches_locations(*sizes)

    def _generate_patches(self, subject: Subject) -> Generator[Subject]:
        subject = self._pad(subject)
        sizes = (subject.spatial_shape, self.patch_size, self.patch_overlap)
        self._parse_sizes(*sizes)
        locations = self._get_patches_locations(*sizes)
        for location in locations:
            index_ini = location[:3]
            yield self.extract_patch(subject, index_ini)

    @staticmethod
    def _parse_sizes(image_size: TypeTripletInt, patch_size: TypeTripletInt, patch_overlap: TypeTripletInt) -> None:
        image_size_array = np.array(image_size)
        patch_size_array = np.array(patch_size)
        patch_overlap_array = np.array(patch_overlap)
        if np.any(patch_size_array > image_size_array):
            message = f'Patch size {tuple(patch_size_array)} cannot be larger than image size {tuple(image_size_array)}'
            raise ValueError(message)
        if np.any(patch_overlap_array >= patch_size_array):
            message = f'Patch overlap {tuple(patch_overlap_array)} must be smaller than patch size {tuple(patch_size_array)}'
            raise ValueError(message)
        if np.any(patch_overlap_array % 2):
            message = f'Patch overlap must be a tuple of even integers, not {tuple(patch_overlap_array)}'
            raise ValueError(message)

    @staticmethod
    def _get_patches_locations(image_size: TypeTripletInt, patch_size: TypeTripletInt, patch_overlap: TypeTripletInt) -> np.ndarray:
        indices = []
        zipped = zip(image_size, patch_size, patch_overlap)
        for im_size_dim, patch_size_dim, patch_overlap_dim in zipped:
            end = im_size_dim + 1 - patch_size_dim
            step = patch_size_dim - patch_overlap_dim
            indices_dim = list(range(0, end, step))
            if indices_dim[-1] != im_size_dim - patch_size_dim:
                indices_dim.append(im_size_dim - patch_size_dim)
            indices.append(indices_dim)
        indices_ini = np.array(np.meshgrid(*indices)).reshape(3, -1).T
        indices_ini = np.unique(indices_ini, axis=0)
        indices_fin = indices_ini + np.array(patch_size)
        locations = np.hstack((indices_ini, indices_fin))
        return np.array(sorted(locations.tolist()))

def _compute_locations(self, subject: Subject):
    sizes = (subject.spatial_shape, self.patch_size, self.patch_overlap)
    self._parse_sizes(*sizes)
    return self._get_patches_locations(*sizes)

def _generate_patches(self, subject: Subject) -> Generator[Subject]:
    subject = self._pad(subject)
    sizes = (subject.spatial_shape, self.patch_size, self.patch_overlap)
    self._parse_sizes(*sizes)
    locations = self._get_patches_locations(*sizes)
    for location in locations:
        index_ini = location[:3]
        yield self.extract_patch(subject, index_ini)

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

def _generate_patches(self, subject: Subject, num_patches: int | None=None) -> Generator[Subject]:
    probability_map = self.get_probability_map(subject)
    probability_map_array = self.process_probability_map(probability_map, subject)
    cdf = self.get_cumulative_distribution_function(probability_map_array)
    patches_left = num_patches if num_patches is not None else True
    while patches_left:
        yield self.extract_patch(subject, probability_map_array, cdf)
        if num_patches is not None:
            patches_left -= 1

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

class UniformSampler(RandomSampler):
    """Randomly extract patches from a volume with uniform probability.

    Args:
        patch_size: See :class:`~torchio.data.PatchSampler`.
    """

    def get_probability_map(self, subject: Subject) -> torch.Tensor:
        return torch.ones(1, *subject.spatial_shape)

    def _generate_patches(self, subject: Subject, num_patches: int | None=None) -> Generator[Subject]:
        valid_range = subject.spatial_shape - self.patch_size
        patches_left = num_patches if num_patches is not None else True
        while patches_left:
            i, j, k = tuple((int(torch.randint(x + 1, (1,)).item()) for x in valid_range))
            index_ini = (i, j, k)
            yield self.extract_patch(subject, index_ini)
            if num_patches is not None:
                patches_left -= 1

def _generate_patches(self, subject: Subject, num_patches: int | None=None) -> Generator[Subject]:
    valid_range = subject.spatial_shape - self.patch_size
    patches_left = num_patches if num_patches is not None else True
    while patches_left:
        i, j, k = tuple((int(torch.randint(x + 1, (1,)).item()) for x in valid_range))
        index_ini = (i, j, k)
        yield self.extract_patch(subject, index_ini)
        if num_patches is not None:
            patches_left -= 1

def format_age(n):
    integer = int(n)
    decimal = int(10 * (n - integer))
    return f'{integer:02d}.{decimal}'

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

class RandomAnisotropy(RandomTransform):
    """Downsample an image along an axis and upsample to initial space.

    This transform simulates an image that has been acquired using anisotropic
    spacing and resampled back to its original spacing.

    Similar to the work by Billot et al.: `Partial Volume Segmentation of Brain
    MRI Scans of any Resolution and
    Contrast <https://link.springer.com/chapter/10.1007/978-3-030-59728-3_18>`_.

    Args:
        axes: Axis or tuple of axes along which the image will be downsampled.
        downsampling: Downsampling factor :math:`m \\gt 1`. If a tuple
            :math:`(a, b)` is provided then :math:`m \\sim \\mathcal{U}(a, b)`.
        image_interpolation: Image interpolation used to upsample the image
            back to its initial spacing. Downsampling is performed using
            nearest neighbor interpolation. See :ref:`Interpolation` for
            supported interpolation types.
        scalars_only: Apply only to instances of :class:`torchio.ScalarImage`.
            This is useful when the segmentation quality needs to be kept,
            as in `Billot et al. <https://link.springer.com/chapter/10.1007/978-3-030-59728-3_18>`_.
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.

    Example:
        >>> import torchio as tio
        >>> transform = tio.RandomAnisotropy(axes=1, downsampling=2)
        >>> transform = tio.RandomAnisotropy(
        ...     axes=(0, 1, 2),
        ...     downsampling=(2, 5),
        ... )   # Multiply spacing of one of the 3 axes by a factor randomly chosen in [2, 5]
        >>> colin = tio.datasets.Colin27()
        >>> transformed = transform(colin)
    """

    def __init__(self, axes: Union[int, tuple[int, ...]]=(0, 1, 2), downsampling: TypeRangeFloat=(1.5, 5), image_interpolation: str='linear', scalars_only: bool=True, **kwargs):
        super().__init__(**kwargs)
        self.axes = self.parse_axes(axes)
        self.downsampling_range = self._parse_range(downsampling, 'downsampling', min_constraint=1)
        parsed_interpolation = self.parse_interpolation(image_interpolation)
        self.image_interpolation = parsed_interpolation
        self.scalars_only = scalars_only

    def get_params(self, axes: tuple[int, ...], downsampling_range: tuple[float, float]) -> tuple[int, float]:
        axis = axes[torch.randint(0, len(axes), (1,))]
        downsampling = self.sample_uniform(*downsampling_range)
        return (axis, downsampling)

    @staticmethod
    def parse_axes(axes: Union[int, tuple[int, ...]]):
        axes_tuple = to_tuple(axes)
        for axis in axes_tuple:
            is_int = isinstance(axis, int)
            if not is_int or axis not in (0, 1, 2):
                raise ValueError('All axes must be 0, 1 or 2')
        return axes_tuple

    def apply_transform(self, subject: Subject) -> Subject:
        is_2d = subject.get_first_image().is_2d()
        if is_2d and 2 in self.axes:
            warnings.warn(f'Input image is 2D, but "2" is in axes: {self.axes}', RuntimeWarning, stacklevel=2)
            self.axes = list(self.axes)
            self.axes.remove(2)
        axis, downsampling = self.get_params(self.axes, self.downsampling_range)
        target_spacing = list(subject.spacing)
        target_spacing[axis] *= downsampling
        downsample_args = self.add_base_args({'target': tuple(target_spacing), 'image_interpolation': 'nearest', 'scalars_only': self.scalars_only})
        image = subject.get_first_image()
        upsample_args = self.add_base_args({'target': (image.spatial_shape, image.affine), 'image_interpolation': self.image_interpolation, 'scalars_only': self.scalars_only})
        downsample = Resample(**downsample_args)
        downsampled = downsample(subject)
        upsample = Resample(**upsample_args)
        upsampled = upsample(downsampled)
        assert isinstance(upsampled, Subject)
        return upsampled

def get_params(self, axes: tuple[int, ...], downsampling_range: tuple[float, float]) -> tuple[int, float]:
    axis = axes[torch.randint(0, len(axes), (1,))]
    downsampling = self.sample_uniform(*downsampling_range)
    return (axis, downsampling)

def get_random_indices_from_shape(spatial_shape: Sequence[int], patch_size: Sequence[int]) -> tuple[np.ndarray, np.ndarray]:
    assert len(spatial_shape) == 3
    assert len(patch_size) in (1, 3)
    shape_array = np.array(spatial_shape)
    patch_size_array = np.array(patch_size)
    max_index_ini_unchecked = shape_array - patch_size_array
    if (max_index_ini_unchecked < 0).any():
        message = f'Patch size {patch_size} cannot be larger than image spatial shape {spatial_shape}'
        raise ValueError(message)
    max_index_ini = max_index_ini_unchecked.astype(np.uint16)
    coordinates = []
    for max_coordinate in max_index_ini.tolist():
        if max_coordinate == 0:
            coordinate = 0
        else:
            coordinate = int(torch.randint(max_coordinate, size=(1,)).item())
        coordinates.append(coordinate)
    index_ini = np.array(coordinates, np.uint16)
    index_fin = index_ini + patch_size_array
    return (index_ini, index_fin)

class RandomNoise(RandomTransform, IntensityTransform):
    """Add Gaussian noise with random parameters.

    Add noise sampled from a normal distribution with random parameters.

    Args:
        mean: Mean :math:`\\mu` of the Gaussian distribution
            from which the noise is sampled.
            If two values :math:`(a, b)` are provided,
            then :math:`\\mu \\sim \\mathcal{U}(a, b)`.
            If only one value :math:`d` is provided,
            :math:`\\mu \\sim \\mathcal{U}(-d, d)`.
        std: Standard deviation :math:`\\sigma` of the Gaussian distribution
            from which the noise is sampled.
            If two values :math:`(a, b)` are provided,
            then :math:`\\sigma \\sim \\mathcal{U}(a, b)`.
            If only one value :math:`d` is provided,
            :math:`\\sigma \\sim \\mathcal{U}(0, d)`.
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.
    """

    def __init__(self, mean: Union[float, tuple[float, float]]=0, std: Union[float, tuple[float, float]]=(0, 0.25), **kwargs):
        super().__init__(**kwargs)
        self.mean_range = self._parse_range(mean, 'mean')
        self.std_range = self._parse_range(std, 'std', min_constraint=0)

    def apply_transform(self, subject: Subject) -> Subject:
        images_dict = self.get_images_dict(subject)
        if not images_dict:
            return subject
        arguments: dict[str, dict] = defaultdict(dict)
        for image_name in images_dict:
            mean, std, seed = self.get_params(self.mean_range, self.std_range)
            arguments['mean'][image_name] = mean
            arguments['std'][image_name] = std
            arguments['seed'][image_name] = seed
        transform = Noise(**self.add_base_args(arguments))
        transformed = transform(subject)
        assert isinstance(transformed, Subject)
        return transformed

    def get_params(self, mean_range: tuple[float, float], std_range: tuple[float, float]) -> tuple[float, float, int]:
        mean = self.sample_uniform(*mean_range)
        std = self.sample_uniform(*std_range)
        seed = self._get_random_seed()
        return (mean, std, seed)

def get_params(self, mean_range: tuple[float, float], std_range: tuple[float, float]) -> tuple[float, float, int]:
    mean = self.sample_uniform(*mean_range)
    std = self.sample_uniform(*std_range)
    seed = self._get_random_seed()
    return (mean, std, seed)

class RandomLabelsToImage(RandomTransform, IntensityTransform):
    """Randomly generate an image from a segmentation.

    Based on the work by Billot et al.: `A Learning Strategy for Contrast-agnostic MRI Segmentation`_
    and `Partial Volume Segmentation of Brain MRI Scans of any Resolution and Contrast`_.

    .. _A Learning Strategy for Contrast-agnostic MRI Segmentation: http://proceedings.mlr.press/v121/billot20a.html

    .. _Partial Volume Segmentation of Brain MRI Scans of any Resolution and Contrast: https://link.springer.com/chapter/10.1007/978-3-030-59728-3_18

    .. plot::

        import torch
        import torchio as tio
        torch.manual_seed(42)
        colin = tio.datasets.Colin27(2008)
        label_map = colin.cls
        colin.remove_image('t1')
        colin.remove_image('t2')
        colin.remove_image('pd')
        downsample = tio.Resample(1)
        blurring_transform = tio.RandomBlur(std=0.6)
        create_synthetic_image = tio.RandomLabelsToImage(
            image_key='synthetic',
            ignore_background=True,
        )
        transform = tio.Compose((
            downsample,
            create_synthetic_image,
            blurring_transform,
        ))
        colin_synth = transform(colin)
        colin_synth.plot()

    Args:
        label_key: String designating the label map in the subject
            that will be used to generate the new image.
        used_labels: Sequence of integers designating the labels used
            to generate the new image. If categorical encoding is used,
            :attr:`label_channels` refers to the values of the
            categorical encoding. If one hot encoding or partial-volume
            label maps are used, :attr:`label_channels` refers to the
            channels of the label maps.
            Default uses all labels. Missing voxels will be filled with zero
            or with voxels from an already existing volume,
            see :attr:`image_key`.
        image_key: String designating the key to which the new volume will be
            saved. If this key corresponds to an already existing volume,
            missing voxels will be filled with the corresponding values
            in the original volume.
        mean: Sequence of means for each label.
            For each value :math:`v`, if a tuple :math:`(a, b)` is
            provided then :math:`v \\sim \\mathcal{U}(a, b)`.
            If ``None``, :attr:`default_mean` range will be used for every
            label.
            If not ``None`` and :attr:`label_channels` is not ``None``,
            :attr:`mean` and :attr:`label_channels` must have the
            same length.
        std: Sequence of standard deviations for each label.
            For each value :math:`v`, if a tuple :math:`(a, b)` is
            provided then :math:`v \\sim \\mathcal{U}(a, b)`.
            If ``None``, :attr:`default_std` range will be used for every
            label.
            If not ``None`` and :attr:`label_channels` is not ``None``,
            :attr:`std` and :attr:`label_channels` must have the
            same length.
        default_mean: Default mean range.
        default_std: Default standard deviation range.
        discretize: If ``True``, partial-volume label maps will be discretized.
            Does not have any effects if not using partial-volume label maps.
            Discretization is done taking the class of the highest value per
            voxel in the different partial-volume label maps using
            :func:`torch.argmax()` on the channel dimension (i.e. 0).
        ignore_background: If ``True``, input voxels labeled as ``0`` will not
            be modified.
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.

    .. tip:: It is recommended to blur the new images in order to simulate
        partial volume effects at the borders of the synthetic structures. See
        :class:`~torchio.transforms.augmentation.intensity.random_blur.RandomBlur`.

    Example:
        >>> import torchio as tio
        >>> subject = tio.datasets.ICBM2009CNonlinearSymmetric()
        >>> # Using the default parameters
        >>> transform = tio.RandomLabelsToImage(label_key='tissues')
        >>> # Using custom mean and std
        >>> transform = tio.RandomLabelsToImage(
        ...     label_key='tissues', mean=[0.33, 0.66, 1.], std=[0, 0, 0]
        ... )
        >>> # Discretizing the partial volume maps and blurring the result
        >>> simulation_transform = tio.RandomLabelsToImage(
        ...     label_key='tissues', mean=[0.33, 0.66, 1.], std=[0, 0, 0], discretize=True
        ... )
        >>> blurring_transform = tio.RandomBlur(std=0.3)
        >>> transform = tio.Compose([simulation_transform, blurring_transform])
        >>> transformed = transform(subject)  # subject has a new key 'image_from_labels' with the simulated image
        >>> # Filling holes of the simulated image with the original T1 image
        >>> rescale_transform = tio.RescaleIntensity(
        ...     out_min_max=(0, 1), percentiles=(1, 99))   # Rescale intensity before filling holes
        >>> simulation_transform = tio.RandomLabelsToImage(
        ...     label_key='tissues',
        ...     image_key='t1',
        ...     used_labels=[0, 1]
        ... )
        >>> transform = tio.Compose([rescale_transform, simulation_transform])
        >>> transformed = transform(subject)  # subject's key 't1' has been replaced with the simulated image

    .. seealso:: :class:`~torchio.transforms.preprocessing.label.remap_labels.RemapLabels`.
    """

    def __init__(self, label_key: str | None=None, used_labels: Sequence[int] | None=None, image_key: str='image_from_labels', mean: Sequence[TypeRangeFloat] | None=None, std: Sequence[TypeRangeFloat] | None=None, default_mean: TypeRangeFloat=(0.1, 0.9), default_std: TypeRangeFloat=(0.01, 0.1), discretize: bool=False, ignore_background: bool=False, **kwargs):
        super().__init__(**kwargs)
        self.label_key = _parse_label_key(label_key)
        self.used_labels = _parse_used_labels(used_labels)
        self.mean, self.std = self.parse_mean_and_std(mean, std)
        self.default_mean = self.parse_gaussian_parameter(default_mean, 'default_mean')
        self.default_std = self.parse_gaussian_parameter(default_std, 'default_std')
        self.image_key = image_key
        self.discretize = discretize
        self.ignore_background = ignore_background

    def parse_mean_and_std(self, mean: Sequence[TypeRangeFloat], std: Sequence[TypeRangeFloat]) -> tuple[list[TypeRangeFloat], list[TypeRangeFloat]]:
        if mean is not None:
            mean = self.parse_gaussian_parameters(mean, 'mean')
        if std is not None:
            std = self.parse_gaussian_parameters(std, 'std')
        if mean is not None and std is not None:
            message = 'If both "mean" and "std" are defined they must have the samelength'
            assert len(mean) == len(std), message
        return (mean, std)

    def parse_gaussian_parameters(self, params: Sequence[TypeRangeFloat], name: str) -> list[TypeRangeFloat]:
        check_sequence(params, name)
        params = [self.parse_gaussian_parameter(p, f'{name}[{i}]') for i, p in enumerate(params)]
        if self.used_labels is not None:
            message = f'If both "{name}" and "used_labels" are defined, they must have the same length'
            assert len(params) == len(self.used_labels), message
        return params

    @staticmethod
    def parse_gaussian_parameter(nums_range: TypeRangeFloat, name: str) -> tuple[float, float]:
        if isinstance(nums_range, (int, float)):
            return (nums_range, nums_range)
        if len(nums_range) != 2:
            raise ValueError(f'If {name} is a sequence, it must be of len 2, not {nums_range}')
        min_value, max_value = nums_range
        if min_value > max_value:
            raise ValueError(f'If {name} is a sequence, the second value must be equal or greater than the first, not {nums_range}')
        return (min_value, max_value)

    def _guess_label_key(self, subject: Subject) -> None:
        if self.label_key is None:
            iterable = subject.get_images_dict(intensity_only=False).items()
            for name, image in iterable:
                if isinstance(image, LabelMap):
                    self.label_key = name
                    break
            else:
                message = f'No label maps found in subject: {subject}'
                raise RuntimeError(message)

    def apply_transform(self, subject: Subject) -> Subject:
        self._guess_label_key(subject)
        arguments = {'label_key': self.label_key, 'mean': [], 'std': [], 'image_key': self.image_key, 'used_labels': self.used_labels, 'discretize': self.discretize, 'ignore_background': self.ignore_background}
        label_map = subject[self.label_key].data
        all_discrete = label_map.eq(label_map.float().round()).all()
        same_num_dims = label_map.squeeze().dim() < label_map.dim()
        is_discretized = all_discrete and same_num_dims
        if not is_discretized and self.discretize:
            max_label, label_map = label_map.max(dim=0, keepdim=True)
            label_map[max_label == 0] = -1
            is_discretized = True
        if is_discretized:
            labels = label_map.unique().long().tolist()
            if -1 in labels:
                labels.remove(-1)
        else:
            labels = range(label_map.shape[0])
        _check_mean_and_std_length(labels, self.mean, self.std)
        for label in labels:
            mean, std = self.get_params(label)
            means = arguments['mean']
            stds = arguments['std']
            assert isinstance(means, list)
            assert isinstance(stds, list)
            means.append(mean)
            stds.append(std)
        transform = LabelsToImage(**self.add_base_args(arguments))
        transformed = transform(subject)
        assert isinstance(transformed, Subject)
        return transformed

    def get_params(self, label: int) -> tuple[float, float]:
        if self.mean is None:
            mean_range = self.default_mean
        else:
            assert isinstance(self.mean, Sequence)
            mean_range = self.mean[label]
        if self.std is None:
            std_range = self.default_std
        else:
            std_range = self.std[label]
        mean = self.sample_uniform(*mean_range)
        std = self.sample_uniform(*std_range)
        return (mean, std)

def get_params(self, label: int) -> tuple[float, float]:
    if self.mean is None:
        mean_range = self.default_mean
    else:
        assert isinstance(self.mean, Sequence)
        mean_range = self.mean[label]
    if self.std is None:
        std_range = self.default_std
    else:
        std_range = self.std[label]
    mean = self.sample_uniform(*mean_range)
    std = self.sample_uniform(*std_range)
    return (mean, std)

class RandomGhosting(RandomTransform, IntensityTransform):
    """Add random MRI ghosting artifact.

    Discrete "ghost" artifacts may occur along the phase-encode direction
    whenever the position or signal intensity of imaged structures within the
    field-of-view vary or move in a regular (periodic) fashion. Pulsatile flow
    of blood or CSF, cardiac motion, and respiratory motion are the most
    important patient-related causes of ghost artifacts in clinical MR imaging
    (from `mriquestions.com`_).

    .. _mriquestions.com: https://mriquestions.com/why-discrete-ghosts.html

    Args:
        num_ghosts: Number of 'ghosts' :math:`n` in the image.
            If :attr:`num_ghosts` is a tuple :math:`(a, b)`, then
            :math:`n \\sim \\mathcal{U}(a, b) \\cap \\mathbb{N}`.
            If only one value :math:`d` is provided,
            :math:`n \\sim \\mathcal{U}(0, d) \\cap \\mathbb{N}`.
        axes: Axis along which the ghosts will be created. If
            :attr:`axes` is a tuple, the axis will be randomly chosen
            from the passed values. Anatomical labels may also be used (see
            :class:`~torchio.transforms.augmentation.RandomFlip`).
        intensity: Positive number representing the artifact strength
            :math:`s` with respect to the maximum of the :math:`k`-space.
            If ``0``, the ghosts will not be visible. If a tuple
            :math:`(a, b)` is provided then :math:`s \\sim \\mathcal{U}(a, b)`.
            If only one value :math:`d` is provided,
            :math:`s \\sim \\mathcal{U}(0, d)`.
        restore: Number between ``0`` and ``1`` indicating how much of the
            :math:`k`-space center should be restored after removing the planes
            that generate the artifact. If ``None``, only the central slice
            will be restored. If a tuple :math:`(a, b)` is provided then
            :math:`r \\sim \\mathcal{U}(a, b)`. If only one value :math:`d` is
            provided, :math:`r \\sim \\mathcal{U}(0, d)`.
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.

    .. note:: The execution time of this transform does not depend on the
        number of ghosts.
    """

    def __init__(self, num_ghosts: int | tuple[int, int]=(4, 10), axes: int | tuple[int, ...]=(0, 1, 2), intensity: float | tuple[float, float]=(0.5, 1), restore: float | None=None, **kwargs):
        super().__init__(**kwargs)
        if not isinstance(axes, tuple):
            try:
                axes = tuple(axes)
            except TypeError:
                axes = (axes,)
        assert isinstance(axes, Iterable)
        for axis in axes:
            if not isinstance(axis, str) and axis not in (0, 1, 2):
                raise ValueError(f'Axes must be in (0, 1, 2), not "{axes}"')
        self.axes = axes
        self.num_ghosts_range = self._parse_range(num_ghosts, 'num_ghosts', min_constraint=0, type_constraint=int)
        self.intensity_range = self._parse_range(intensity, 'intensity_range', min_constraint=0)
        if restore is None:
            self.restore = None
        else:
            self.restore = self._parse_range(restore, 'restore', min_constraint=0, max_constraint=1)

    def apply_transform(self, subject: Subject) -> Subject:
        images_dict = self.get_images_dict(subject)
        if not images_dict:
            return subject
        if any((isinstance(axis, str) for axis in self.axes)):
            subject.check_consistent_orientation()
        arguments: dict[str, dict] = defaultdict(dict)
        for name, image in images_dict.items():
            is_2d = image.is_2d()
            axes = [a for a in self.axes if a != 2] if is_2d else self.axes
            min_ghosts, max_ghosts = self.num_ghosts_range
            params = self.get_params((int(min_ghosts), int(max_ghosts)), axes, self.intensity_range, self.restore)
            num_ghosts_param, axis_param, intensity_param, restore_param = params
            arguments['num_ghosts'][name] = num_ghosts_param
            arguments['axis'][name] = axis_param
            arguments['intensity'][name] = intensity_param
            arguments['restore'][name] = restore_param
        transform = Ghosting(**self.add_base_args(arguments))
        transformed = transform(subject)
        assert isinstance(transformed, Subject)
        return transformed

    def get_params(self, num_ghosts_range: tuple[int, int], axes: tuple[int, ...], intensity_range: tuple[float, float], restore_range: tuple[float, float] | None) -> tuple[int, int, float, float | None]:
        ng_min, ng_max = num_ghosts_range
        num_ghosts = int(torch.randint(ng_min, ng_max + 1, (1,)).item())
        axis = axes[torch.randint(0, len(axes), (1,))]
        intensity = self.sample_uniform(*intensity_range)
        if restore_range is None:
            restore = None
        else:
            restore = self.sample_uniform(*restore_range)
        return (num_ghosts, axis, intensity, restore)

def get_params(self, num_ghosts_range: tuple[int, int], axes: tuple[int, ...], intensity_range: tuple[float, float], restore_range: tuple[float, float] | None) -> tuple[int, int, float, float | None]:
    ng_min, ng_max = num_ghosts_range
    num_ghosts = int(torch.randint(ng_min, ng_max + 1, (1,)).item())
    axis = axes[torch.randint(0, len(axes), (1,))]
    intensity = self.sample_uniform(*intensity_range)
    if restore_range is None:
        restore = None
    else:
        restore = self.sample_uniform(*restore_range)
    return (num_ghosts, axis, intensity, restore)

class RandomGamma(RandomTransform, IntensityTransform):
    """Randomly change contrast of an image by raising its values to the power
    :math:`\\gamma`.

    Args:
        log_gamma: Tuple :math:`(a, b)` to compute the exponent
            :math:`\\gamma = e ^ \\beta`,
            where :math:`\\beta \\sim \\mathcal{U}(a, b)`.
            If a single value :math:`d` is provided, then
            :math:`\\beta \\sim \\mathcal{U}(-d, d)`.
            Negative and positive values for this argument perform gamma
            compression and expansion, respectively.
            See the `Gamma correction`_ Wikipedia entry for more information.
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.

    .. _Gamma correction: https://en.wikipedia.org/wiki/Gamma_correction

    .. note:: Fractional exponentiation of negative values is generally not
        well-defined for non-complex numbers.
        If negative values are found in the input image :math:`I`,
        the applied transform is :math:`\\text{sign}(I) |I|^\\gamma`,
        instead of the usual :math:`I^\\gamma`. The
        :class:`~torchio.transforms.RescaleIntensity`
        transform may be used to ensure that all values are positive. This is
        generally not problematic, but it is recommended to visualize results
        on images with negative values. More information can be found on
        `this StackExchange question`_.

        .. _this StackExchange question: https://math.stackexchange.com/questions/317528/how-do-you-compute-negative-numbers-to-fractional-powers

    .. plot::

        import torch
        import torchio as tio
        subject = tio.datasets.FPG()
        subject.remove_image('seg')
        transform = tio.RandomGamma(log_gamma=(-0.3, -0.3))
        transformed = transform(subject)
        subject.add_image(transformed.t1, 'log -0.3')
        transform = tio.RandomGamma(log_gamma=(0.3, 0.3))
        transformed = transform(subject)
        subject.add_image(transformed.t1, 'log 0.3')
        subject.plot()

    Example:
        >>> import torchio as tio
        >>> subject = tio.datasets.FPG()
        >>> transform = tio.RandomGamma(log_gamma=(-0.3, 0.3))  # gamma between 0.74 and 1.34
        >>> transformed = transform(subject)
    """

    def __init__(self, log_gamma: TypeRangeFloat=(-0.3, 0.3), **kwargs):
        super().__init__(**kwargs)
        self.log_gamma_range = self._parse_range(log_gamma, 'log_gamma')

    def apply_transform(self, subject: Subject) -> Subject:
        images_dict = self.get_images_dict(subject)
        if not images_dict:
            return subject
        arguments: dict[str, dict] = defaultdict(dict)
        for name, image in images_dict.items():
            gammas = [self.get_params(self.log_gamma_range) for _ in image.data]
            arguments['gamma'][name] = gammas
        transform = Gamma(**self.add_base_args(arguments))
        transformed = transform(subject)
        assert isinstance(transformed, Subject)
        return transformed

    def get_params(self, log_gamma_range: tuple[float, float]) -> float:
        gamma = np.exp(self.sample_uniform(*log_gamma_range))
        return gamma

def get_params(self, log_gamma_range: tuple[float, float]) -> float:
    gamma = np.exp(self.sample_uniform(*log_gamma_range))
    return gamma

class RandomSpike(RandomTransform, IntensityTransform, FourierTransform):
    """Add random MRI spike artifacts.

    Also known as `Herringbone artifact
    <https://radiopaedia.org/articles/herringbone-artifact?lang=gb>`_,
    crisscross artifact or corduroy artifact, it creates stripes in different
    directions in image space due to spikes in k-space.

    Args:
        num_spikes: Number of spikes :math:`n` present in k-space.
            If a tuple :math:`(a, b)` is provided, then
            :math:`n \\sim \\mathcal{U}(a, b) \\cap \\mathbb{N}`.
            If only one value :math:`d` is provided,
            :math:`n \\sim \\mathcal{U}(0, d) \\cap \\mathbb{N}`.
            Larger values generate more distorted images.
        intensity: Ratio :math:`r` between the spike intensity and the maximum
            of the spectrum.
            If a tuple :math:`(a, b)` is provided, then
            :math:`r \\sim \\mathcal{U}(a, b)`.
            If only one value :math:`d` is provided,
            :math:`r \\sim \\mathcal{U}(-d, d)`.
            Larger values generate more distorted images.
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.

    .. note:: The execution time of this transform does not depend on the
        number of spikes.
    """

    def __init__(self, num_spikes: Union[int, tuple[int, int]]=1, intensity: Union[float, tuple[float, float]]=(1, 3), **kwargs):
        super().__init__(**kwargs)
        self.intensity_range = self._parse_range(intensity, 'intensity_range')
        self.num_spikes_range: tuple[int, int] = self._parse_range(num_spikes, 'num_spikes', min_constraint=0, type_constraint=int)

    def apply_transform(self, subject: Subject) -> Subject:
        images_dict = self.get_images_dict(subject)
        if not images_dict:
            return subject
        arguments: dict[str, dict] = defaultdict(dict)
        for image_name in images_dict:
            spikes_positions_param, intensity_param = self.get_params(self.num_spikes_range, self.intensity_range)
            arguments['spikes_positions'][image_name] = spikes_positions_param
            arguments['intensity'][image_name] = intensity_param
        transform = Spike(**self.add_base_args(arguments))
        transformed = transform(subject)
        assert isinstance(transformed, Subject)
        return transformed

    def get_params(self, num_spikes_range: tuple[int, int], intensity_range: tuple[float, float]) -> tuple[np.ndarray, float]:
        ns_min, ns_max = num_spikes_range
        num_spikes_param = int(torch.randint(ns_min, ns_max + 1, (1,)).item())
        intensity_param = self.sample_uniform(*intensity_range)
        spikes_positions = torch.rand(num_spikes_param, 3).numpy()
        return (spikes_positions, intensity_param)

def get_params(self, num_spikes_range: tuple[int, int], intensity_range: tuple[float, float]) -> tuple[np.ndarray, float]:
    ns_min, ns_max = num_spikes_range
    num_spikes_param = int(torch.randint(ns_min, ns_max + 1, (1,)).item())
    intensity_param = self.sample_uniform(*intensity_range)
    spikes_positions = torch.rand(num_spikes_param, 3).numpy()
    return (spikes_positions, intensity_param)

class CropOrPad(SpatialTransform):
    """Modify the field of view by cropping or padding to match a target shape.

    This transform modifies the affine matrix associated to the volume so that
    physical positions of the voxels are maintained.

    Args:
        target_shape: Tuple :math:`(W, H, D)`. If a single value :math:`N` is
            provided, then :math:`W = H = D = N`. If ``None``, the shape will
            be computed from the :attr:`mask_name` (and the :attr:`labels`, if
            :attr:`labels` is not ``None``).
        padding_mode: Same as :attr:`padding_mode` in
            :class:`~torchio.transforms.Pad`.
        mask_name: If ``None``, the centers of the input and output volumes
            will be the same.
            If a string is given, the output volume center will be the center
            of the bounding box of non-zero values in the image named
            :attr:`mask_name`.
        labels: If a label map is used to generate the mask, sequence of labels
            to consider.
        only_crop: If ``True``, padding will not be applied, only cropping will
            be done. ``only_crop`` and ``only_pad`` cannot both be ``True``.
        only_pad: If ``True``, cropping will not be applied, only padding will
            be done. ``only_crop`` and ``only_pad`` cannot both be ``True``.
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.

    Example:
        >>> import torchio as tio
        >>> subject = tio.Subject(
        ...     chest_ct=tio.ScalarImage('subject_a_ct.nii.gz'),
        ...     heart_mask=tio.LabelMap('subject_a_heart_seg.nii.gz'),
        ... )
        >>> subject.chest_ct.shape
        torch.Size([1, 512, 512, 289])
        >>> transform = tio.CropOrPad(
        ...     (120, 80, 180),
        ...     mask_name='heart_mask',
        ... )
        >>> transformed = transform(subject)
        >>> transformed.chest_ct.shape
        torch.Size([1, 120, 80, 180])

    .. warning:: If :attr:`target_shape` is ``None``, subjects in the dataset
        will probably have different shapes. This is probably fine if you are
        using `patch-based training <https://docs.torchio.org/patches/index.html>`_.
        If you are using full volumes for training and a batch size larger than
        one, an error will be raised by the :class:`~torch.utils.data.DataLoader`
        while trying to collate the batches.

    .. plot::

        import torchio as tio
        t1 = tio.datasets.Colin27().t1
        crop_pad = tio.CropOrPad((512, 512, 32))
        t1_pad_crop = crop_pad(t1)
        subject = tio.Subject(t1=t1, crop_pad=t1_pad_crop)
        subject.plot()
    """

    def __init__(self, target_shape: int | TypeTripletInt | None=None, padding_mode: str | float=0, mask_name: str | None=None, labels: Sequence[int] | None=None, only_crop: bool=False, only_pad: bool=False, **kwargs):
        if target_shape is None and mask_name is None:
            message = 'If mask_name is None, a target shape must be passed'
            raise ValueError(message)
        super().__init__(**kwargs)
        if target_shape is None:
            self.target_shape = None
        else:
            self.target_shape = parse_spatial_shape(target_shape)
        self.padding_mode = padding_mode
        if mask_name is not None and (not isinstance(mask_name, str)):
            message = f'If mask_name is not None, it must be a string, not {type(mask_name)}'
            raise ValueError(message)
        if mask_name is None:
            if labels is not None:
                message = f'If mask_name is None, labels should be None, but "{labels}" was passed'
                raise ValueError(message)
            self.compute_crop_or_pad = self._compute_center_crop_or_pad
        else:
            if not isinstance(mask_name, str):
                message = f'If mask_name is not None, it must be a string, not {type(mask_name)}'
                raise ValueError(message)
            self.compute_crop_or_pad = self._compute_mask_center_crop_or_pad
        self.mask_name = mask_name
        self.labels = labels
        if only_pad and only_crop:
            message = 'only_crop and only_pad cannot both be True'
            raise ValueError(message)
        self.only_crop = only_crop
        self.only_pad = only_pad
        self.args_names = ['target_shape', 'padding_mode', 'mask_name', 'labels', 'only_crop', 'only_pad']

    @staticmethod
    def _bbox_mask(mask_volume: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Return 6 coordinates of a 3D bounding box from a given mask.

        Taken from `this SO question <https://stackoverflow.com/questions/31400769/bounding-box-of-numpy-array>`_.

        Args:
            mask_volume: 3D NumPy array.
        """
        i_any = np.any(mask_volume, axis=(1, 2))
        j_any = np.any(mask_volume, axis=(0, 2))
        k_any = np.any(mask_volume, axis=(0, 1))
        i_min, i_max = np.where(i_any)[0][[0, -1]]
        j_min, j_max = np.where(j_any)[0][[0, -1]]
        k_min, k_max = np.where(k_any)[0][[0, -1]]
        bb_min = np.array([i_min, j_min, k_min])
        bb_max = np.array([i_max, j_max, k_max]) + 1
        return (bb_min, bb_max)

    @staticmethod
    def _get_six_bounds_parameters(parameters: np.ndarray) -> TypeSixBounds:
        """Compute bounds parameters for ITK filters.

        Args:
            parameters: Tuple :math:`(w, h, d)` with the number of voxels to be
                cropped or padded.

        Returns:
            Tuple :math:`(w_{ini}, w_{fin}, h_{ini}, h_{fin}, d_{ini}, d_{fin})`,
            where :math:`n_{ini} = \\left \\lceil \\frac{n}{2} \\right \\rceil` and
            :math:`n_{fin} = \\left \\lfloor \\frac{n}{2} \\right \\rfloor`.

        Example:
            >>> p = np.array((4, 0, 7))
            >>> CropOrPad._get_six_bounds_parameters(p)
            (2, 2, 0, 0, 4, 3)
        """
        parameters = parameters / 2
        result = []
        for number in parameters:
            ini, fin = (int(np.ceil(number)), int(np.floor(number)))
            result.extend([ini, fin])
        i1, i2, j1, j2, k1, k2 = result
        return (i1, i2, j1, j2, k1, k2)

    def _compute_cropping_padding_from_shapes(self, source_shape: TypeTripletInt) -> tuple[TypeSixBounds | None, TypeSixBounds | None]:
        diff_shape = np.array(self.target_shape) - source_shape
        cropping = -np.minimum(diff_shape, 0)
        if cropping.any():
            cropping_params = self._get_six_bounds_parameters(cropping)
        else:
            cropping_params = None
        padding = np.maximum(diff_shape, 0)
        if padding.any():
            padding_params = self._get_six_bounds_parameters(padding)
        else:
            padding_params = None
        return (padding_params, cropping_params)

    def _compute_center_crop_or_pad(self, subject: Subject) -> tuple[TypeSixBounds | None, TypeSixBounds | None]:
        source_shape = subject.spatial_shape
        parameters = self._compute_cropping_padding_from_shapes(source_shape)
        padding_params, cropping_params = parameters
        return (padding_params, cropping_params)

    def _compute_mask_center_crop_or_pad(self, subject: Subject) -> tuple[TypeSixBounds | None, TypeSixBounds | None]:
        if self.mask_name not in subject:
            message = f'Mask name "{self.mask_name}" not found in subject keys "{tuple(subject.keys())}". Using volume center instead'
            warnings.warn(message, RuntimeWarning, stacklevel=2)
            return self._compute_center_crop_or_pad(subject=subject)
        mask_data = self.get_mask_from_masking_method(self.mask_name, subject, subject[self.mask_name].data, self.labels).numpy()
        if not np.any(mask_data):
            message = f'All values found in the mask "{self.mask_name}" are zero. Using volume center instead'
            warnings.warn(message, RuntimeWarning, stacklevel=2)
            return self._compute_center_crop_or_pad(subject=subject)
        subject_shape = subject.spatial_shape
        bb_min, bb_max = self._bbox_mask(mask_data[0])
        center_mask = np.mean((bb_min, bb_max), axis=0)
        padding = []
        cropping = []
        if self.target_shape is None:
            target_shape = bb_max - bb_min
        else:
            target_shape = self.target_shape
        for dim in range(3):
            target_dim = target_shape[dim]
            center_dim = center_mask[dim]
            subject_dim = subject_shape[dim]
            center_on_index = not center_dim % 1
            target_even = not target_dim % 2
            if target_even ^ center_on_index:
                center_dim -= 0.5
            begin = center_dim - target_dim / 2
            if begin >= 0:
                crop_ini = begin
                pad_ini = 0
            else:
                crop_ini = 0
                pad_ini = -begin
            end = center_dim + target_dim / 2
            if end <= subject_dim:
                crop_fin = subject_dim - end
                pad_fin = 0
            else:
                crop_fin = 0
                pad_fin = end - subject_dim
            padding.extend([pad_ini, pad_fin])
            cropping.extend([crop_ini, crop_fin])
        padding_array = np.asarray(padding, dtype=int)
        cropping_array = np.asarray(cropping, dtype=int)
        if padding_array.any():
            padding_params = tuple(padding_array.tolist())
        else:
            padding_params = None
        if cropping_array.any():
            cropping_params = tuple(cropping_array.tolist())
        else:
            cropping_params = None
        return (padding_params, cropping_params)

    def apply_transform(self, subject: Subject) -> Subject:
        subject.check_consistent_space()
        padding_params, cropping_params = self.compute_crop_or_pad(subject)
        padding_kwargs = {'padding_mode': self.padding_mode}
        if padding_params is not None and (not self.only_crop):
            pad = Pad(padding_params, **self.get_base_args(), **padding_kwargs)
            subject = pad(subject)
        if cropping_params is not None and (not self.only_pad):
            crop = Crop(cropping_params, **self.get_base_args())
            subject = crop(subject)
        return subject

@staticmethod
def _get_six_bounds_parameters(parameters: np.ndarray) -> TypeSixBounds:
    """Compute bounds parameters for ITK filters.

        Args:
            parameters: Tuple :math:`(w, h, d)` with the number of voxels to be
                cropped or padded.

        Returns:
            Tuple :math:`(w_{ini}, w_{fin}, h_{ini}, h_{fin}, d_{ini}, d_{fin})`,
            where :math:`n_{ini} = \\left \\lceil \\frac{n}{2} \\right \\rceil` and
            :math:`n_{fin} = \\left \\lfloor \\frac{n}{2} \\right \\rfloor`.

        Example:
            >>> p = np.array((4, 0, 7))
            >>> CropOrPad._get_six_bounds_parameters(p)
            (2, 2, 0, 0, 4, 3)
        """
    parameters = parameters / 2
    result = []
    for number in parameters:
        ini, fin = (int(np.ceil(number)), int(np.floor(number)))
        result.extend([ini, fin])
    i1, i2, j1, j2, k1, k2 = result
    return (i1, i2, j1, j2, k1, k2)

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

def test_count(self):
    image = self.sample_subject.label
    max_n = image.data.numel()
    nonzero = image.count_nonzero()
    assert 0 <= nonzero <= max_n
    counts = image.count_labels()
    assert tuple(counts) == (0, 1)
    assert 0 <= counts[0] <= max_n
    assert 0 <= counts[1] <= max_n

class TestPatchSampler(TorchioTestCase):
    """Tests for `PatchSampler` class."""

    def test_bad_patch_size(self):
        with pytest.raises(ValueError):
            PatchSampler(0)
        with pytest.raises(ValueError):
            PatchSampler(-1)
        with pytest.raises(ValueError):
            PatchSampler(1.5)

    def test_extract_patch(self):
        PatchSampler(1).extract_patch(self.sample_subject, (3, 4, 5))

def test_bad_patch_size(self):
    with pytest.raises(ValueError):
        PatchSampler(0)
    with pytest.raises(ValueError):
        PatchSampler(-1)
    with pytest.raises(ValueError):
        PatchSampler(1.5)

def test_extract_patch(self):
    PatchSampler(1).extract_patch(self.sample_subject, (3, 4, 5))

