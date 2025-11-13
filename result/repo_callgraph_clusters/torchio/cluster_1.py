# Cluster 1

class Subject(dict):
    """Class to store information about the images corresponding to a subject.

    Args:
        *args: If provided, a dictionary of items.
        **kwargs: Items that will be added to the subject sample.

    Example:

        >>> import torchio as tio
        >>> # One way:
        >>> subject = tio.Subject(
        ...     one_image=tio.ScalarImage('path_to_image.nii.gz'),
        ...     a_segmentation=tio.LabelMap('path_to_seg.nii.gz'),
        ...     age=45,
        ...     name='John Doe',
        ...     hospital='Hospital Juan Negrín',
        ... )
        >>> # If you want to create the mapping before, or have spaces in the keys:
        >>> subject_dict = {
        ...     'one image': tio.ScalarImage('path_to_image.nii.gz'),
        ...     'a segmentation': tio.LabelMap('path_to_seg.nii.gz'),
        ...     'age': 45,
        ...     'name': 'John Doe',
        ...     'hospital': 'Hospital Juan Negrín',
        ... }
        >>> subject = tio.Subject(subject_dict)
    """

    def __init__(self, *args, **kwargs: dict[str, Any]):
        if args:
            if len(args) == 1 and isinstance(args[0], dict):
                kwargs.update(args[0])
            else:
                message = 'Only one dictionary as positional argument is allowed'
                raise ValueError(message)
        super().__init__(**kwargs)
        self._parse_images(self.get_images(intensity_only=False))
        self.update_attributes()
        self.applied_transforms: list[tuple[str, dict]] = []

    def __repr__(self):
        num_images = len(self.get_images(intensity_only=False))
        string = f'{self.__class__.__name__}(Keys: {tuple(self.keys())}; images: {num_images})'
        return string

    def __len__(self):
        return len(self.get_images(intensity_only=False))

    def __getitem__(self, item):
        if isinstance(item, (slice, int, tuple)):
            try:
                self.check_consistent_spatial_shape()
            except RuntimeError as e:
                message = 'To use indexing, all images in the subject must have the same spatial shape'
                raise RuntimeError(message) from e
            copied = copy.deepcopy(self)
            for image_name, image in copied.items():
                copied[image_name] = image[item]
            return copied
        else:
            return super().__getitem__(item)

    @staticmethod
    def _parse_images(images: list[Image]) -> None:
        if not images:
            raise TypeError('A subject without images cannot be created')

    @property
    def shape(self):
        """Return shape of first image in subject.

        Consistency of shapes across images in the subject is checked first.

        Example:

            >>> import torchio as tio
            >>> colin = tio.datasets.Colin27()
            >>> colin.shape
            (1, 181, 217, 181)
        """
        self.check_consistent_attribute('shape')
        return self.get_first_image().shape

    @property
    def spatial_shape(self):
        """Return spatial shape of first image in subject.

        Consistency of spatial shapes across images in the subject is checked
        first.

        Example:

            >>> import torchio as tio
            >>> colin = tio.datasets.Colin27()
            >>> colin.spatial_shape
            (181, 217, 181)
        """
        self.check_consistent_spatial_shape()
        return self.get_first_image().spatial_shape

    @property
    def spacing(self):
        """Return spacing of first image in subject.

        Consistency of spacings across images in the subject is checked first.

        Example:

            >>> import torchio as tio
            >>> colin = tio.datasets.Slicer()
            >>> colin.spacing
            (1.0, 1.0, 1.2999954223632812)
        """
        self.check_consistent_attribute('spacing')
        return self.get_first_image().spacing

    @property
    def history(self):
        return self.get_applied_transforms()

    def is_2d(self):
        return all((i.is_2d() for i in self.get_images(intensity_only=False)))

    def get_applied_transforms(self, ignore_intensity: bool=False, image_interpolation: str | None=None) -> list[Transform]:
        from ..transforms.intensity_transform import IntensityTransform
        from ..transforms.transform import Transform
        name_to_transform = {cls.__name__: cls for cls in get_subclasses(Transform)}
        transforms_list = []
        for transform_name, arguments in self.applied_transforms:
            transform = name_to_transform[transform_name](**arguments)
            if ignore_intensity and isinstance(transform, IntensityTransform):
                continue
            resamples = hasattr(transform, 'image_interpolation')
            if resamples and image_interpolation is not None:
                parsed = transform.parse_interpolation(image_interpolation)
                transform.image_interpolation = parsed
            transforms_list.append(transform)
        return transforms_list

    def get_composed_history(self, ignore_intensity: bool=False, image_interpolation: str | None=None) -> Compose:
        from ..transforms.augmentation.composition import Compose
        transforms = self.get_applied_transforms(ignore_intensity=ignore_intensity, image_interpolation=image_interpolation)
        return Compose(transforms)

    def get_inverse_transform(self, warn: bool=True, ignore_intensity: bool=False, image_interpolation: str | None=None) -> Compose:
        """Get a reversed list of the inverses of the applied transforms.

        Args:
            warn: Issue a warning if some transforms are not invertible.
            ignore_intensity: If ``True``, all instances of
                :class:`~torchio.transforms.intensity_transform.IntensityTransform`
                will be ignored.
            image_interpolation: Modify interpolation for scalar images inside
                transforms that perform resampling.
        """
        history_transform = self.get_composed_history(ignore_intensity=ignore_intensity, image_interpolation=image_interpolation)
        inverse_transform = history_transform.inverse(warn=warn)
        return inverse_transform

    def apply_inverse_transform(self, **kwargs) -> Subject:
        """Apply the inverse of all applied transforms, in reverse order.

        Args:
            **kwargs: Keyword arguments passed on to
                :meth:`~torchio.data.subject.Subject.get_inverse_transform`.
        """
        inverse_transform = self.get_inverse_transform(**kwargs)
        transformed: Subject
        transformed = inverse_transform(self)
        transformed.clear_history()
        return transformed

    def clear_history(self) -> None:
        self.applied_transforms = []

    def check_consistent_attribute(self, attribute: str, relative_tolerance: float=1e-06, absolute_tolerance: float=1e-06, message: str | None=None) -> None:
        """Check for consistency of an attribute across all images.

        Args:
            attribute: Name of the image attribute to check
            relative_tolerance: Relative tolerance for :func:`numpy.allclose()`
            absolute_tolerance: Absolute tolerance for :func:`numpy.allclose()`

        Example:
            >>> import numpy as np
            >>> import torch
            >>> import torchio as tio
            >>> scalars = torch.randn(1, 512, 512, 100)
            >>> mask = torch.tensor(scalars > 0).type(torch.int16)
            >>> af1 = np.eye([0.8, 0.8, 2.50000000000001, 1])
            >>> af2 = np.eye([0.8, 0.8, 2.49999999999999, 1])  # small difference here (e.g. due to different reader)
            >>> subject = tio.Subject(
            ...   image = tio.ScalarImage(tensor=scalars, affine=af1),
            ...   mask = tio.LabelMap(tensor=mask, affine=af2)
            ... )
            >>> subject.check_consistent_attribute('spacing')  # no error as tolerances are > 0

        .. note:: To check that all values for a specific attribute are close
            between all images in the subject, :func:`numpy.allclose()` is used.
            This function returns ``True`` if
            :math:`|a_i - b_i| \\leq t_{abs} + t_{rel} * |b_i|`, where
            :math:`a_i` and :math:`b_i` are the :math:`i`-th element of the same
            attribute of two images being compared,
            :math:`t_{abs}` is the ``absolute_tolerance`` and
            :math:`t_{rel}` is the ``relative_tolerance``.
        """
        message = f'More than one value for "{attribute}" found in subject images:\n{{}}'
        names_images = self.get_images_dict(intensity_only=False).items()
        try:
            first_attribute = None
            first_image = None
            for image_name, image in names_images:
                if first_attribute is None:
                    first_attribute = getattr(image, attribute)
                    first_image = image_name
                    continue
                current_attribute = getattr(image, attribute)
                all_close = np.allclose(current_attribute, first_attribute, rtol=relative_tolerance, atol=absolute_tolerance)
                if not all_close:
                    message = message.format(pprint.pformat({first_image: first_attribute, image_name: current_attribute}))
                    raise RuntimeError(message)
        except TypeError:
            values_dict = {}
            for image_name, image in names_images:
                values_dict[image_name] = getattr(image, attribute)
            num_unique_values = len(set(values_dict.values()))
            if num_unique_values > 1:
                message = message.format(pprint.pformat(values_dict))
                raise RuntimeError(message) from None

    def check_consistent_spatial_shape(self) -> None:
        self.check_consistent_attribute('spatial_shape')

    def check_consistent_orientation(self) -> None:
        self.check_consistent_attribute('orientation')

    def check_consistent_affine(self) -> None:
        self.check_consistent_attribute('affine')

    def check_consistent_space(self) -> None:
        try:
            self.check_consistent_attribute('spacing')
            self.check_consistent_attribute('direction')
            self.check_consistent_attribute('origin')
            self.check_consistent_spatial_shape()
        except RuntimeError as e:
            message = 'As described above, some images in the subject are not in the same space. You probably can use the transforms ToCanonical and Resample to fix this, as explained at https://github.com/TorchIO-project/torchio/issues/647#issuecomment-913025695'
            raise RuntimeError(message) from e

    def get_images_names(self) -> list[str]:
        return list(self.get_images_dict(intensity_only=False).keys())

    def get_images_dict(self, intensity_only=True, include: Sequence[str] | None=None, exclude: Sequence[str] | None=None) -> dict[str, Image]:
        images = {}
        for image_name, image in self.items():
            if not isinstance(image, Image):
                continue
            if intensity_only and (not image[TYPE] == INTENSITY):
                continue
            if include is not None and image_name not in include:
                continue
            if exclude is not None and image_name in exclude:
                continue
            images[image_name] = image
        return images

    def get_images(self, intensity_only=True, include: Sequence[str] | None=None, exclude: Sequence[str] | None=None) -> list[Image]:
        images_dict = self.get_images_dict(intensity_only=intensity_only, include=include, exclude=exclude)
        return list(images_dict.values())

    def get_image(self, image_name: str) -> Image:
        """Get a single image by its name."""
        return self.get_images_dict(intensity_only=False)[image_name]

    def get_first_image(self) -> Image:
        return self.get_images(intensity_only=False)[0]

    def add_transform(self, transform: Transform, parameters_dict: dict) -> None:
        self.applied_transforms.append((transform.name, parameters_dict))

    def load(self) -> None:
        """Load images in subject on RAM."""
        for image in self.get_images(intensity_only=False):
            image.load()

    def unload(self) -> None:
        """Unload images in subject."""
        for image in self.get_images(intensity_only=False):
            image.unload()

    def update_attributes(self) -> None:
        self.__dict__.update(self)

    @staticmethod
    def _check_image_name(image_name):
        if not isinstance(image_name, str):
            message = f'The image name must be a string, but it has type "{type(image_name)}"'
            raise ValueError(message)
        return image_name

    def add_image(self, image: Image, image_name: str) -> None:
        """Add an image to the subject instance."""
        if not isinstance(image, Image):
            message = f'Image must be an instance of torchio.Image, but its type is "{type(image)}"'
            raise ValueError(message)
        self._check_image_name(image_name)
        self[image_name] = image
        self.update_attributes()

    def remove_image(self, image_name: str) -> None:
        """Remove an image from the subject instance."""
        self._check_image_name(image_name)
        del self[image_name]
        delattr(self, image_name)

    def plot(self, **kwargs) -> None:
        """Plot images using matplotlib.

        Args:
            **kwargs: Keyword arguments that will be passed on to
                :meth:`~torchio.Image.plot`.
        """
        from ..visualization import plot_subject
        plot_subject(self, **kwargs)

def apply_inverse_transform(self, **kwargs) -> Subject:
    """Apply the inverse of all applied transforms, in reverse order.

        Args:
            **kwargs: Keyword arguments passed on to
                :meth:`~torchio.data.subject.Subject.get_inverse_transform`.
        """
    inverse_transform = self.get_inverse_transform(**kwargs)
    transformed: Subject
    transformed = inverse_transform(self)
    transformed.clear_history()
    return transformed

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

def to_ras(self) -> Image:
    if self.orientation_str != 'RAS':
        from ..transforms.preprocessing.spatial.to_canonical import ToCanonical
        return ToCanonical()(self)
    return self

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

class FourierTransform:

    @staticmethod
    def fourier_transform(tensor: torch.Tensor) -> torch.Tensor:
        try:
            import torch.fft
            transformed = torch.fft.fftn(tensor)
            fshift = torch.fft.fftshift(transformed)
            return fshift
        except (ModuleNotFoundError, AttributeError):
            import torch
            transformed = np.fft.fftn(tensor)
            fshift = np.fft.fftshift(transformed)
            return torch.from_numpy(fshift)

    @staticmethod
    def inv_fourier_transform(tensor: torch.Tensor) -> torch.Tensor:
        try:
            import torch.fft
            f_ishift = torch.fft.ifftshift(tensor)
            img_back = torch.fft.ifftn(f_ishift)
            return img_back
        except (ModuleNotFoundError, AttributeError):
            import torch
            f_ishift = np.fft.ifftshift(tensor)
            img_back = np.fft.ifftn(f_ishift)
            return torch.from_numpy(img_back)

@staticmethod
def fourier_transform(tensor: torch.Tensor) -> torch.Tensor:
    try:
        import torch.fft
        transformed = torch.fft.fftn(tensor)
        fshift = torch.fft.fftshift(transformed)
        return fshift
    except (ModuleNotFoundError, AttributeError):
        import torch
        transformed = np.fft.fftn(tensor)
        fshift = np.fft.fftshift(transformed)
        return torch.from_numpy(fshift)

@staticmethod
def inv_fourier_transform(tensor: torch.Tensor) -> torch.Tensor:
    try:
        import torch.fft
        f_ishift = torch.fft.ifftshift(tensor)
        img_back = torch.fft.ifftn(f_ishift)
        return img_back
    except (ModuleNotFoundError, AttributeError):
        import torch
        f_ishift = np.fft.ifftshift(tensor)
        img_back = np.fft.ifftn(f_ishift)
        return torch.from_numpy(img_back)

class Compose(Transform):
    """Compose several transforms together.

    Args:
        transforms: Sequence of instances of
            :class:`~torchio.transforms.Transform`.
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.
    """

    def __init__(self, transforms: Sequence[Transform], **kwargs):
        super().__init__(parse_input=False, **kwargs)
        for transform in transforms:
            if not callable(transform):
                message = f'One or more of the objects passed to the Compose transform are not callable: "{transform}"'
                raise TypeError(message)
        self.transforms = list(transforms)

    def __len__(self):
        return len(self.transforms)

    def __getitem__(self, index) -> Transform:
        return self.transforms[index]

    def __repr__(self) -> str:
        return f'{self.name}({self.transforms})'

    def get_base_args(self) -> dict:
        init_args = super().get_base_args()
        if 'parse_input' in init_args:
            init_args.pop('parse_input')
        return init_args

    def apply_transform(self, subject: Subject) -> Subject:
        for transform in self.transforms:
            subject = transform(subject)
        return subject

    def is_invertible(self) -> bool:
        return all((t.is_invertible() for t in self.transforms))

    def inverse(self, warn: bool=True) -> Compose:
        """Return a composed transform with inverted order and transforms.

        Args:
            warn: Issue a warning if some transforms are not invertible.
        """
        transforms = []
        for transform in self.transforms:
            if transform.is_invertible():
                transforms.append(transform.inverse())
            elif warn:
                message = f'Skipping {transform.name} as it is not invertible'
                warnings.warn(message, RuntimeWarning, stacklevel=2)
        transforms.reverse()
        result = Compose(transforms, **self.get_base_args())
        if not transforms and warn:
            warnings.warn('No invertible transforms found', RuntimeWarning, stacklevel=2)
        return result

def apply_transform(self, subject: Subject) -> Subject:
    for transform in self.transforms:
        subject = transform(subject)
    return subject

class CopyAffine(SpatialTransform):
    """Copy the spatial metadata from a reference image in the subject.

    Small unexpected differences in spatial metadata across different images
    of a subject can arise due to rounding errors while converting formats.

    If the ``shape`` and ``orientation`` of the images are the same and their
    ``affine`` attributes are different but very similar, this transform can be
    used to avoid errors during safety checks in other transforms and samplers.

    Args:
        target: Name of the image within the subject whose affine matrix will
            be used.

    Example:
        >>> import torch
        >>> import torchio as tio
        >>> import numpy as np
        >>> np.random.seed(0)
        >>> affine = np.diag((*(np.random.rand(3) + 0.5), 1))
        >>> t1 = tio.ScalarImage(tensor=torch.rand(1, 100, 100, 100), affine=affine)
        >>> # Let's simulate a loss of precision
        >>> # (caused for example by NIfTI storing spatial metadata in single precision)
        >>> bad_affine = affine.astype(np.float16)
        >>> t2 = tio.ScalarImage(tensor=torch.rand(1, 100, 100, 100), affine=bad_affine)
        >>> subject = tio.Subject(t1=t1, t2=t2)
        >>> resample = tio.Resample(0.5)
        >>> resample(subject).shape  # error as images are in different spaces
        Traceback (most recent call last):
          File "<stdin>", line 1, in <module>
          File "/Users/fernando/git/torchio/torchio/data/subject.py", line 101, in shape
            self.check_consistent_attribute('shape')
          File "/Users/fernando/git/torchio/torchio/data/subject.py", line 229, in check_consistent_attribute
            raise RuntimeError(message)
        RuntimeError: More than one shape found in subject images:
        {'t1': (1, 210, 244, 221), 't2': (1, 210, 243, 221)}
        >>> transform = tio.CopyAffine('t1')
        >>> fixed = transform(subject)
        >>> resample(fixed).shape
        (1, 210, 244, 221)


    .. warning:: This transform should be used with caution. Modifying the
        spatial metadata of an image manually can lead to incorrect processing
        of the position of anatomical structures. For example, a machine
        learning algorithm might incorrectly predict that a lesion on the right
        lung is on the left lung.

    .. note:: For more information, see some related discussions on GitHub:

        * https://github.com/TorchIO-project/torchio/issues/354
        * https://github.com/TorchIO-project/torchio/discussions/489
        * https://github.com/TorchIO-project/torchio/pull/584
        * https://github.com/TorchIO-project/torchio/issues/430
        * https://github.com/TorchIO-project/torchio/issues/382
        * https://github.com/TorchIO-project/torchio/pull/592
    """

    def __init__(self, target: str, **kwargs):
        super().__init__(**kwargs)
        if not isinstance(target, str):
            message = f'The target must be a string, but "{type(target)}" was found'
            raise ValueError(message)
        self.target = target
        self.args_names = ['target']

    def apply_transform(self, subject: Subject) -> Subject:
        if self.target not in subject:
            message = f'Target image "{self.target}" not found in subject'
            raise RuntimeError(message)
        reference = subject[self.target]
        affine = copy.deepcopy(reference.affine)
        for image in self.get_images(subject):
            if image is reference:
                continue
            image.load()
            image.affine = affine
        return subject

def apply_transform(self, subject: Subject) -> Subject:
    if self.target not in subject:
        message = f'Target image "{self.target}" not found in subject'
        raise RuntimeError(message)
    reference = subject[self.target]
    affine = copy.deepcopy(reference.affine)
    for image in self.get_images(subject):
        if image is reference:
            continue
        image.load()
        image.affine = affine
    return subject

class Transpose(SpatialTransform):
    """Swap the first and last spatial dimensions of the image.

    The spatial metadata is updated accordingly, so the world coordinates of
    all voxels in the input and output spaces match.

    Example:

    >>> import torchio as tio
    >>> image = tio.datasets.FPG().t1
    >>> image
    ScalarImage(shape: (1, 256, 256, 176); spacing: (1.00, 1.00, 1.00); orientation: PIR+; path: "/home/fernando/.cache/torchio/fpg/t1.nii.gz")
    >>> transpose = tio.Transpose()
    >>> transposed = transpose(image)
    >>> transposed
    ScalarImage(shape: (1, 176, 256, 256); spacing: (1.00, 1.00, 1.00); orientation: RIP+; dtype: torch.IntTensor; memory: 44.0 MiB)
    """

    def apply_transform(self, subject: Subject) -> Subject:
        for image in self.get_images(subject):
            old_orientation = image.orientation_str
            new_orientation = old_orientation[::-1]
            transform = ToOrientation(new_orientation)
            transposed = transform(image)
            image.set_data(transposed.data)
            image.affine = transposed.affine
        return subject

    def is_invertible(self):
        return True

    def inverse(self):
        return self

def apply_transform(self, subject: Subject) -> Subject:
    for image in self.get_images(subject):
        old_orientation = image.orientation_str
        new_orientation = old_orientation[::-1]
        transform = ToOrientation(new_orientation)
        transposed = transform(image)
        image.set_data(transposed.data)
        image.affine = transposed.affine
    return subject

class EnsureShapeMultiple(SpatialTransform):
    """Ensure that all values in the image shape are divisible by :math:`n`.

    Some convolutional neural network architectures need that the size of the
    input across all spatial dimensions is a power of :math:`2`.

    For example, the canonical 3D U-Net from
    `Çiçek et al. <https://link.springer.com/chapter/10.1007/978-3-319-46723-8_49>`_
    includes three downsampling (pooling) and upsampling operations:

    .. image:: https://www.researchgate.net/profile/Olaf-Ronneberger/publication/304226155/figure/fig1/AS:375619658502144@1466566113191/The-3D-u-net-architecture-Blue-boxes-represent-feature-maps-The-number-of-channels-is.png
        :alt: 3D U-Net

    Pooling operations in PyTorch round down the output size:

        >>> import torch
        >>> x = torch.rand(3, 10, 20, 31)
        >>> x_down = torch.nn.functional.max_pool3d(x, 2)
        >>> x_down.shape
        torch.Size([3, 5, 10, 15])

    If we upsample this tensor, the original shape is lost:

        >>> x_down_up = torch.nn.functional.interpolate(x_down, scale_factor=2)
        >>> x_down_up.shape
        torch.Size([3, 10, 20, 30])
        >>> x.shape
        torch.Size([3, 10, 20, 31])

    If we try to concatenate ``x_down`` and ``x_down_up`` (to create skip
    connections), we will get an error. It is therefore good practice to ensure
    that the size of our images is such that concatenations will be safe.

    .. note:: In these examples, it's assumed that all convolutions in the
        U-Net use padding so that the output size is the same as the input
        size.

    The image above shows :math:`3` downsampling operations, so the input size
    along all dimensions should be a multiple of :math:`2^3 = 8`.

    Example (assuming ``pip install unet`` has been run before):

        >>> import torchio as tio
        >>> import unet
        >>> net = unet.UNet3D(padding=1)
        >>> t1 = tio.datasets.Colin27().t1
        >>> tensor_bad = t1.data.unsqueeze(0)
        >>> tensor_bad.shape
        torch.Size([1, 1, 181, 217, 181])
        >>> net(tensor_bad).shape
        Traceback (most recent call last):
          File "<stdin>", line 1, in <module>
          File "/home/fernando/miniconda3/envs/resseg/lib/python3.7/site-packages/torch/nn/modules/module.py", line 727, in _call_impl
            result = self.forward(*input, **kwargs)
          File "/home/fernando/miniconda3/envs/resseg/lib/python3.7/site-packages/unet/unet.py", line 122, in forward
            x = self.decoder(skip_connections, encoding)
          File "/home/fernando/miniconda3/envs/resseg/lib/python3.7/site-packages/torch/nn/modules/module.py", line 727, in _call_impl
            result = self.forward(*input, **kwargs)
          File "/home/fernando/miniconda3/envs/resseg/lib/python3.7/site-packages/unet/decoding.py", line 61, in forward
            x = decoding_block(skip_connection, x)
          File "/home/fernando/miniconda3/envs/resseg/lib/python3.7/site-packages/torch/nn/modules/module.py", line 727, in _call_impl
            result = self.forward(*input, **kwargs)
          File "/home/fernando/miniconda3/envs/resseg/lib/python3.7/site-packages/unet/decoding.py", line 131, in forward
            x = torch.cat((skip_connection, x), dim=CHANNELS_DIMENSION)
        RuntimeError: Sizes of tensors must match except in dimension 1. Got 45 and 44 in dimension 2 (The offending index is 1)
        >>> num_poolings = 3
        >>> fix_shape_unet = tio.EnsureShapeMultiple(2**num_poolings)
        >>> t1_fixed = fix_shape_unet(t1)
        >>> tensor_ok = t1_fixed.data.unsqueeze(0)
        >>> tensor_ok.shape
        torch.Size([1, 1, 184, 224, 184])  # as expected

    Args:
        target_multiple: Tuple :math:`(n_w, n_h, n_d)`, so that the size of the
            output along axis :math:`i` is a multiple of :math:`n_i`. If a
            single value :math:`n` is provided, then
            :math:`n_w = n_h = n_d = n`.
        method: Either ``'crop'`` or ``'pad'``.
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.

    Example:
        >>> import torchio as tio
        >>> image = tio.datasets.Colin27().t1
        >>> image.shape
        (1, 181, 217, 181)
        >>> transform = tio.EnsureShapeMultiple(8, method='pad')
        >>> transformed = transform(image)
        >>> transformed.shape
        (1, 184, 224, 184)
        >>> transform = tio.EnsureShapeMultiple(8, method='crop')
        >>> transformed = transform(image)
        >>> transformed.shape
        (1, 176, 216, 176)
        >>> image_2d = image.data[..., :1]
        >>> image_2d.shape
        torch.Size([1, 181, 217, 1])
        >>> transformed = transform(image_2d)
        >>> transformed.shape
        torch.Size([1, 176, 216, 1])
    """

    def __init__(self, target_multiple: int | TypeTripletInt, *, method: str='pad', **kwargs):
        super().__init__(**kwargs)
        self.target_multiple = np.array(to_tuple(target_multiple, 3))
        if method not in ('crop', 'pad'):
            raise ValueError('Method must be "crop" or "pad"')
        self.method = method

    def apply_transform(self, subject: Subject) -> Subject:
        source_shape = np.array(subject.spatial_shape, np.uint16)
        function: Callable = np.floor if self.method == 'crop' else np.ceil
        integer_ratio = function(source_shape / self.target_multiple)
        target_shape = integer_ratio * self.target_multiple
        target_shape = np.maximum(target_shape, 1)
        transform = CropOrPad(target_shape.astype(int), **self.get_base_args())
        subject = transform(subject)
        return subject

def apply_transform(self, subject: Subject) -> Subject:
    source_shape = np.array(subject.spatial_shape, np.uint16)
    function: Callable = np.floor if self.method == 'crop' else np.ceil
    integer_ratio = function(source_shape / self.target_multiple)
    target_shape = integer_ratio * self.target_multiple
    target_shape = np.maximum(target_shape, 1)
    transform = CropOrPad(target_shape.astype(int), **self.get_base_args())
    subject = transform(subject)
    return subject

class TorchioTestCase(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures, if any."""
        self.dir = Path(tempfile.gettempdir()) / os.urandom(24).hex()
        self.dir.mkdir(exist_ok=True)
        random.seed(42)
        np.random.seed(42)
        registration_matrix = np.array([[1, 0, 0, 10], [0, 1, 0, 0], [0, 0, 1.2, 0], [0, 0, 0, 1]])
        subject_a = tio.Subject(t1=tio.ScalarImage(self.get_image_path('t1_a')))
        subject_b = tio.Subject(t1=tio.ScalarImage(self.get_image_path('t1_b')), label=tio.LabelMap(self.get_image_path('label_b', binary=True)))
        subject_c = tio.Subject(label=tio.LabelMap(self.get_image_path('label_c', binary=True)))
        subject_d = tio.Subject(t1=tio.ScalarImage(self.get_image_path('t1_d'), pre_affine=registration_matrix), t2=tio.ScalarImage(self.get_image_path('t2_d')), label=tio.LabelMap(self.get_image_path('label_d', binary=True)))
        subject_a4 = tio.Subject(t1=tio.ScalarImage(self.get_image_path('t1_a'), components=4))
        self.subjects_list = [subject_a, subject_a4, subject_b, subject_c, subject_d]
        self.dataset = tio.SubjectsDataset(self.subjects_list)
        self.sample_subject = self.dataset[-1]
        self.subject_4d = self.dataset[1]

    def make_2d(self, subject):
        subject = copy.deepcopy(subject)
        for image in subject.get_images(intensity_only=False):
            image.set_data(image.data[..., :1])
        return subject

    def make_multichannel(self, subject):
        subject = copy.deepcopy(subject)
        for image in subject.get_images(intensity_only=False):
            image.set_data(torch.cat(4 * (image.data,)))
        return subject

    def flip_affine_x(self, subject):
        subject = copy.deepcopy(subject)
        for image in subject.get_images(intensity_only=False):
            image.affine = np.diag((-1, 1, 1, 1)) @ image.affine
        return subject

    def get_inconsistent_shape_subject(self):
        """Return a subject containing images of different shape."""
        subject = tio.Subject(t1=tio.ScalarImage(self.get_image_path('t1_inc')), t2=tio.ScalarImage(self.get_image_path('t2_inc', shape=(10, 20, 31))), label=tio.LabelMap(self.get_image_path('label_inc', shape=(8, 17, 25), binary=True)), label2=tio.LabelMap(self.get_image_path('label2_inc', shape=(18, 17, 25), binary=True)))
        return subject

    def get_reference_image_and_path(self):
        """Return a reference image and its path."""
        path = self.get_image_path('ref', shape=(10, 20, 31), spacing=(1, 1, 2))
        image = tio.ScalarImage(path)
        return (image, path)

    def get_subject_with_partial_volume_label_map(self, components=1):
        """Return a subject with a partial-volume label map."""
        return tio.Subject(t1=tio.ScalarImage(self.get_image_path('t1_d')), label=tio.LabelMap(self.get_image_path('label_d2', binary=False, components=components)))

    def get_subject_with_labels(self, labels):
        return tio.Subject(label=tio.LabelMap(self.get_image_path('label_multi', labels=labels)))

    @staticmethod
    def get_unique_labels(data: torch.Tensor) -> set[int]:
        labels = data.unique().tolist()
        return set(labels)

    @staticmethod
    def get_tensor_with_labels(labels: Sequence) -> torch.Tensor:
        tensor = torch.as_tensor(list(labels))
        return tensor.repeat_interleave(2).reshape(1, 1, 1, -1)

    def tearDown(self):
        """Tear down test fixtures, if any."""
        shutil.rmtree(self.dir)

    def get_ixi_tiny(self):
        root_dir = Path(tempfile.gettempdir()) / 'torchio' / 'ixi_tiny'
        return tio.datasets.IXITiny(root_dir, download=True)

    def get_image_path(self, stem, binary=False, labels=None, shape=(10, 20, 30), spacing=(1, 1, 1), components=1, add_nans=False, suffix=None, force_binary_foreground=True):
        shape = (*shape, 1) if len(shape) == 2 else shape
        data = np.random.rand(components, *shape)
        if binary:
            data = (data > 0.5).astype(np.uint8)
            if not data.sum() and force_binary_foreground:
                data[..., 0] = 1
        elif labels is not None:
            data = (data * (len(labels) + 1)).astype(np.uint8)
            new_data = np.zeros_like(data)
            for i, label in enumerate(labels):
                new_data[data == i + 1] = label
                if not (new_data == label).sum():
                    new_data[..., i] = label
            data = new_data
        elif self.flip_coin():
            data *= 100
            dtype = np.uint8 if self.flip_coin() else np.uint16
            data = data.astype(dtype)
        if add_nans:
            data[:] = np.nan
        affine = np.diag((*spacing, 1))
        if suffix is None:
            extensions = ('.nii.gz', '.nii', '.nrrd', '.img', '.mnc')
            suffix = random.choice(extensions)
        path = self.dir / f'{stem}{suffix}'
        if self.flip_coin():
            path = str(path)
        image = tio.ScalarImage(tensor=data, affine=affine, check_nans=not add_nans)
        image.save(path)
        return path

    def flip_coin(self):
        return np.random.rand() > 0.5

    def get_tests_data_dir(self):
        return Path(__file__).parent / 'image_data'

    def assert_tensor_not_equal(self, *args, **kwargs):
        with pytest.raises(AssertionError):
            self.assert_tensor_equal(*args, **kwargs)

    @staticmethod
    def assert_tensor_equal(*args, **kwargs):
        torch.testing.assert_close(*args, rtol=0, atol=0, check_dtype=False, **kwargs)

    @staticmethod
    def assert_tensor_almost_equal(*args, **kwargs):
        torch.testing.assert_close(*args, **kwargs, check_dtype=False)

    @staticmethod
    def assert_tensor_all_zeros(tensor):
        assert torch.all(tensor == 0)

    def get_large_composed_transform(self):
        all_classes = get_all_random_transforms()
        shuffle(all_classes)
        transforms = [t() for t in all_classes]
        for tr in transforms:
            if tr.name == 'RandomSwap':
                tr.patch_size = np.array((10, 10, 10))
        return tio.Compose(transforms)

def make_2d(self, subject):
    subject = copy.deepcopy(subject)
    for image in subject.get_images(intensity_only=False):
        image.set_data(image.data[..., :1])
    return subject

def flip_affine_x(self, subject):
    subject = copy.deepcopy(subject)
    for image in subject.get_images(intensity_only=False):
        image.affine = np.diag((-1, 1, 1, 1)) @ image.affine
    return subject

def assert_tensor_not_equal(self, *args, **kwargs):
    with pytest.raises(AssertionError):
        self.assert_tensor_equal(*args, **kwargs)

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

def test_add_images_from_batch(self):
    subject = copy.deepcopy(self.sample_subject)
    subjects = 4 * [subject]
    preds = torch.rand(4, *subject.shape)
    tio.utils.add_images_from_batch(subjects, preds)

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

def test_history(self):
    transformed = tio.RandomGamma()(self.sample_subject)
    assert len(transformed.history) == 1

def test_delete_image(self):
    subject = copy.deepcopy(self.sample_subject)
    subject.remove_image('t1')
    with pytest.raises(KeyError):
        subject['t1']
    with pytest.raises(AttributeError):
        _ = subject.t1

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

def test_subject_shape(self):
    patch_size = (5, 20, 20)
    patch_overlap = (2, 4, 6)
    initial_shape = copy(self.sample_subject.shape)
    tio.GridSampler(self.sample_subject, patch_size, patch_overlap, padding_mode='reflect')
    final_shape = self.sample_subject.shape
    assert initial_shape == final_shape

class TestTransforms(TorchioTestCase):
    """Tests for all transforms."""

    def get_transform(self, channels, is_3d=True, labels=True):
        landmarks_dict = {channel: np.linspace(0, 100, 13) for channel in channels}
        disp = 1 if is_3d else (1, 1, 0.01)
        elastic = tio.RandomElasticDeformation(max_displacement=disp)
        affine_elastic = tio.RandomAffineElasticDeformation(elastic_kwargs={'max_displacement': disp})
        cp_args = (9, 21, 30) if is_3d else (21, 30, 1)
        resize_args = (10, 20, 30) if is_3d else (10, 20, 1)
        flip_axes = axes_downsample = (0, 1, 2) if is_3d else (0, 1)
        swap_patch = (2, 3, 4) if is_3d else (3, 4, 1)
        pad_args = (1, 2, 3, 0, 5, 6) if is_3d else (0, 0, 3, 0, 5, 6)
        crop_args = (3, 2, 8, 0, 1, 4) if is_3d else (0, 0, 8, 0, 1, 4)
        remapping = {1: 2, 2: 1, 3: 20, 4: 25}
        transforms = [tio.CropOrPad(cp_args), tio.EnsureShapeMultiple(2, method='crop'), tio.Resize(resize_args), tio.ToCanonical(), tio.RandomAnisotropy(downsampling=(1.75, 2), axes=axes_downsample), tio.CopyAffine(channels[0]), tio.Resample((1, 1.1, 1.25)), tio.RandomFlip(axes=flip_axes, flip_probability=1), tio.RandomMotion(), tio.RandomGhosting(axes=(0, 1, 2)), tio.RandomSpike(), tio.RandomNoise(), tio.RandomBlur(), tio.RandomSwap(patch_size=swap_patch, num_iterations=5), tio.Lambda(lambda x: 2 * x, types_to_apply=tio.INTENSITY), tio.RandomBiasField(), tio.RescaleIntensity(out_min_max=(0, 1)), tio.ZNormalization(), tio.HistogramStandardization(landmarks_dict), elastic, tio.RandomAffine(), affine_elastic, tio.OneOf({tio.RandomAffine(): 3, elastic: 1}), tio.RemapLabels(remapping=remapping, masking_method='Left'), tio.RemoveLabels([1, 3]), tio.SequentialLabels(), tio.Pad(pad_args, padding_mode=3), tio.Crop(crop_args)]
        if labels:
            transforms.append(tio.RandomLabelsToImage(label_key='label'))
        return tio.Compose(transforms)

    def test_transforms_dict(self):
        transform = tio.RandomNoise(include=('t1', 't2'))
        input_dict = {k: v.data for k, v in self.sample_subject.items()}
        transformed = transform(input_dict)
        assert isinstance(transformed, dict)

    def test_transforms_dict_no_keys(self):
        transform = tio.RandomNoise()
        input_dict = {k: v.data for k, v in self.sample_subject.items()}
        with pytest.raises(RuntimeError):
            transform(input_dict)

    def test_transforms_image(self):
        transform = self.get_transform(channels=('default_image_name',), labels=False)
        transformed = transform(self.sample_subject.t1)
        assert isinstance(transformed, tio.ScalarImage)

    def test_transforms_tensor(self):
        tensor = torch.rand(2, 4, 5, 8)
        transform = self.get_transform(channels=('default_image_name',), labels=False)
        transformed = transform(tensor)
        assert isinstance(transformed, torch.Tensor)

    def test_transforms_array(self):
        tensor = torch.rand(2, 4, 5, 8).numpy()
        transform = self.get_transform(channels=('default_image_name',), labels=False)
        transformed = transform(tensor)
        assert isinstance(transformed, np.ndarray)

    def test_transforms_sitk(self):
        tensor = torch.rand(2, 4, 5, 8)
        affine = np.diag((-1, 2, -3, 1))
        image = tio.data.io.nib_to_sitk(tensor, affine)
        transform = self.get_transform(channels=('default_image_name',), labels=False)
        transformed = transform(image)
        assert isinstance(transformed, sitk.Image)

    def test_transforms_subject_3d(self):
        transform = self.get_transform(channels=('t1', 't2'), is_3d=True)
        transformed = transform(self.sample_subject)
        assert isinstance(transformed, tio.Subject)

    def test_transforms_subject_2d(self):
        transform = self.get_transform(channels=('t1', 't2'), is_3d=False)
        subject = self.make_2d(self.sample_subject)
        transformed = transform(subject)
        assert isinstance(transformed, tio.Subject)

    def test_transforms_subject_4d(self):
        composed = self.get_transform(channels=('t1', 't2'), is_3d=True)
        subject = self.make_multichannel(self.sample_subject)
        subject = self.flip_affine_x(subject)
        transformed = None
        for transform in composed.transforms:
            repr(transform)
            transformed = transform(subject)
            trsf_channels = len(transformed.t1.data)
            assert trsf_channels > 1, f'Lost channels in {transform.name}'
            exclude = ('RandomLabelsToImage', 'RemapLabels', 'RemoveLabels', 'SequentialLabels', 'CopyAffine')
            if transform.name not in exclude:
                assert subject.shape[0] == transformed.shape[0], f'Different number of channels after {transform.name}'
                self.assert_tensor_not_equal(subject.t1.data[1], transformed.t1.data[1], msg=f'No changes after {transform.name}')
            subject = transformed
        assert isinstance(transformed, tio.Subject)

    def test_transform_noop(self):
        transform = tio.RandomMotion(p=0)
        transformed = transform(self.sample_subject)
        assert transformed is self.sample_subject
        tensor = torch.rand(2, 4, 5, 8).numpy()
        transformed = transform(tensor)
        assert transformed is tensor

    def test_original_unchanged(self):
        subject = copy.deepcopy(self.sample_subject)
        composed = self.get_transform(channels=('t1', 't2'), is_3d=True)
        subject = self.flip_affine_x(subject)
        for transform in composed.transforms:
            original_data = copy.deepcopy(subject.t1.data)
            transform(subject)
            self.assert_tensor_equal(subject.t1.data, original_data, msg=f'Changes after {transform.name}')

    def test_transforms_use_include(self):
        original_subject = copy.deepcopy(self.sample_subject)
        transform = tio.RandomNoise(include=['t1'])
        transformed = transform(self.sample_subject)
        self.assert_tensor_not_equal(original_subject.t1.data, transformed.t1.data, msg=f'Changes after {transform.name}')
        self.assert_tensor_equal(original_subject.t2.data, transformed.t2.data, msg=f'Changes after {transform.name}')

    def test_transforms_use_exclude(self):
        original_subject = copy.deepcopy(self.sample_subject)
        transform = tio.RandomNoise(exclude=['t2'])
        transformed = transform(self.sample_subject)
        self.assert_tensor_not_equal(original_subject.t1.data, transformed.t1.data, msg=f'Changes after {transform.name}')
        self.assert_tensor_equal(original_subject.t2.data, transformed.t2.data, msg=f'Changes after {transform.name}')

    def test_transforms_use_include_and_exclude(self):
        with pytest.raises(ValueError):
            tio.RandomNoise(include=['t2'], exclude=['t1'])

    def test_keys_deprecated(self):
        with pytest.warns(FutureWarning):
            tio.RandomNoise(keys=['t2'])

    def test_keep_original(self):
        subject = copy.deepcopy(self.sample_subject)
        old, new = ('t1', 't1_original')
        transformed = tio.RandomAffine(keep={old: new})(subject)
        assert old in transformed
        assert new in transformed
        self.assert_tensor_equal(transformed[new].data, subject[old].data)
        self.assert_tensor_not_equal(transformed[new].data, transformed[old].data)

def test_transforms_dict(self):
    transform = tio.RandomNoise(include=('t1', 't2'))
    input_dict = {k: v.data for k, v in self.sample_subject.items()}
    transformed = transform(input_dict)
    assert isinstance(transformed, dict)

def test_transforms_dict_no_keys(self):
    transform = tio.RandomNoise()
    input_dict = {k: v.data for k, v in self.sample_subject.items()}
    with pytest.raises(RuntimeError):
        transform(input_dict)

def test_transforms_image(self):
    transform = self.get_transform(channels=('default_image_name',), labels=False)
    transformed = transform(self.sample_subject.t1)
    assert isinstance(transformed, tio.ScalarImage)

def test_transforms_tensor(self):
    tensor = torch.rand(2, 4, 5, 8)
    transform = self.get_transform(channels=('default_image_name',), labels=False)
    transformed = transform(tensor)
    assert isinstance(transformed, torch.Tensor)

def test_transforms_array(self):
    tensor = torch.rand(2, 4, 5, 8).numpy()
    transform = self.get_transform(channels=('default_image_name',), labels=False)
    transformed = transform(tensor)
    assert isinstance(transformed, np.ndarray)

def test_transforms_sitk(self):
    tensor = torch.rand(2, 4, 5, 8)
    affine = np.diag((-1, 2, -3, 1))
    image = tio.data.io.nib_to_sitk(tensor, affine)
    transform = self.get_transform(channels=('default_image_name',), labels=False)
    transformed = transform(image)
    assert isinstance(transformed, sitk.Image)

def test_transforms_subject_3d(self):
    transform = self.get_transform(channels=('t1', 't2'), is_3d=True)
    transformed = transform(self.sample_subject)
    assert isinstance(transformed, tio.Subject)

def test_transforms_subject_2d(self):
    transform = self.get_transform(channels=('t1', 't2'), is_3d=False)
    subject = self.make_2d(self.sample_subject)
    transformed = transform(subject)
    assert isinstance(transformed, tio.Subject)

def test_transforms_subject_4d(self):
    composed = self.get_transform(channels=('t1', 't2'), is_3d=True)
    subject = self.make_multichannel(self.sample_subject)
    subject = self.flip_affine_x(subject)
    transformed = None
    for transform in composed.transforms:
        repr(transform)
        transformed = transform(subject)
        trsf_channels = len(transformed.t1.data)
        assert trsf_channels > 1, f'Lost channels in {transform.name}'
        exclude = ('RandomLabelsToImage', 'RemapLabels', 'RemoveLabels', 'SequentialLabels', 'CopyAffine')
        if transform.name not in exclude:
            assert subject.shape[0] == transformed.shape[0], f'Different number of channels after {transform.name}'
            self.assert_tensor_not_equal(subject.t1.data[1], transformed.t1.data[1], msg=f'No changes after {transform.name}')
        subject = transformed
    assert isinstance(transformed, tio.Subject)

def test_original_unchanged(self):
    subject = copy.deepcopy(self.sample_subject)
    composed = self.get_transform(channels=('t1', 't2'), is_3d=True)
    subject = self.flip_affine_x(subject)
    for transform in composed.transforms:
        original_data = copy.deepcopy(subject.t1.data)
        transform(subject)
        self.assert_tensor_equal(subject.t1.data, original_data, msg=f'Changes after {transform.name}')

def test_transforms_use_include(self):
    original_subject = copy.deepcopy(self.sample_subject)
    transform = tio.RandomNoise(include=['t1'])
    transformed = transform(self.sample_subject)
    self.assert_tensor_not_equal(original_subject.t1.data, transformed.t1.data, msg=f'Changes after {transform.name}')
    self.assert_tensor_equal(original_subject.t2.data, transformed.t2.data, msg=f'Changes after {transform.name}')

def test_transforms_use_exclude(self):
    original_subject = copy.deepcopy(self.sample_subject)
    transform = tio.RandomNoise(exclude=['t2'])
    transformed = transform(self.sample_subject)
    self.assert_tensor_not_equal(original_subject.t1.data, transformed.t1.data, msg=f'Changes after {transform.name}')
    self.assert_tensor_equal(original_subject.t2.data, transformed.t2.data, msg=f'Changes after {transform.name}')

def test_transforms_use_include_and_exclude(self):
    with pytest.raises(ValueError):
        tio.RandomNoise(include=['t2'], exclude=['t1'])

def test_keep_original(self):
    subject = copy.deepcopy(self.sample_subject)
    old, new = ('t1', 't1_original')
    transformed = tio.RandomAffine(keep={old: new})(subject)
    assert old in transformed
    assert new in transformed
    self.assert_tensor_equal(transformed[new].data, subject[old].data)
    self.assert_tensor_not_equal(transformed[new].data, transformed[old].data)

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

class TestReproducibility(TorchioTestCase):

    def test_all_random_transforms(self):
        transform = self.get_large_composed_transform()
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', (RuntimeWarning, UserWarning))
            transformed = transform(self.sample_subject)
        reproducing_transform = transformed.get_composed_history()
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', (RuntimeWarning, UserWarning))
            new_transformed = reproducing_transform(self.sample_subject)
        self.assert_tensor_equal(transformed.t1.data, new_transformed.t1.data)
        self.assert_tensor_equal(transformed.label.data, new_transformed.label.data)

def test_all_random_transforms(self):
    transform = self.get_large_composed_transform()
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', (RuntimeWarning, UserWarning))
        transformed = transform(self.sample_subject)
    reproducing_transform = transformed.get_composed_history()
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', (RuntimeWarning, UserWarning))
        new_transformed = reproducing_transform(self.sample_subject)
    self.assert_tensor_equal(transformed.t1.data, new_transformed.t1.data)
    self.assert_tensor_equal(transformed.label.data, new_transformed.label.data)

class TestRandomGamma(TorchioTestCase):
    """Tests for `RandomGamma`."""

    def get_random_tensor_zero_one(self):
        return torch.rand(4, 5, 6, 7)

    def test_with_zero_gamma(self):
        transform = RandomGamma(log_gamma=0)
        tensor = self.get_random_tensor_zero_one()
        transformed = transform(tensor)
        self.assert_tensor_almost_equal(tensor, transformed)

    def test_with_non_zero_gamma(self):
        transform = RandomGamma(log_gamma=(0.1, 0.3))
        tensor = self.get_random_tensor_zero_one()
        transformed = transform(tensor)
        self.assert_tensor_not_equal(tensor, transformed)

    def test_with_high_gamma(self):
        transform = RandomGamma(log_gamma=(100, 100))
        tensor = self.get_random_tensor_zero_one()
        transformed = transform(tensor)
        self.assert_tensor_almost_equal(tensor == 1, transformed)

    def test_with_low_gamma(self):
        transform = RandomGamma(log_gamma=(-100, -100))
        tensor = self.get_random_tensor_zero_one()
        transformed = transform(tensor)
        self.assert_tensor_almost_equal(tensor > 0, transformed)

    def test_wrong_gamma_type(self):
        with pytest.raises(ValueError):
            RandomGamma(log_gamma='wrong')

def test_with_zero_gamma(self):
    transform = RandomGamma(log_gamma=0)
    tensor = self.get_random_tensor_zero_one()
    transformed = transform(tensor)
    self.assert_tensor_almost_equal(tensor, transformed)

def test_with_non_zero_gamma(self):
    transform = RandomGamma(log_gamma=(0.1, 0.3))
    tensor = self.get_random_tensor_zero_one()
    transformed = transform(tensor)
    self.assert_tensor_not_equal(tensor, transformed)

def test_with_high_gamma(self):
    transform = RandomGamma(log_gamma=(100, 100))
    tensor = self.get_random_tensor_zero_one()
    transformed = transform(tensor)
    self.assert_tensor_almost_equal(tensor == 1, transformed)

def test_with_low_gamma(self):
    transform = RandomGamma(log_gamma=(-100, -100))
    tensor = self.get_random_tensor_zero_one()
    transformed = transform(tensor)
    self.assert_tensor_almost_equal(tensor > 0, transformed)

def test_wrong_gamma_type(self):
    with pytest.raises(ValueError):
        RandomGamma(log_gamma='wrong')

class TestRandomNoise(TorchioTestCase):
    """Tests for `RandomNoise`."""

    def test_no_noise(self):
        transform = RandomNoise(mean=0, std=0)
        transformed = transform(self.sample_subject)
        self.assert_tensor_almost_equal(self.sample_subject.t1.data, transformed.t1.data)

    def test_with_noise(self):
        transform = RandomNoise()
        transformed = transform(self.sample_subject)
        self.assert_tensor_not_equal(self.sample_subject.t1.data, transformed.t1.data)

    def test_constant_noise(self):
        transform = RandomNoise(mean=(5, 5), std=0)
        transformed = transform(self.sample_subject)
        self.assert_tensor_almost_equal(self.sample_subject.t1.data + 5, transformed.t1.data)

    def test_negative_std(self):
        with pytest.raises(ValueError):
            RandomNoise(std=-2)

    def test_std_range_with_negative_min(self):
        with pytest.raises(ValueError):
            RandomNoise(std=(-0.5, 4))

    def test_wrong_std_type(self):
        with pytest.raises(ValueError):
            RandomNoise(std='wrong')

    def test_wrong_mean_type(self):
        with pytest.raises(ValueError):
            RandomNoise(mean='wrong')

def test_no_noise(self):
    transform = RandomNoise(mean=0, std=0)
    transformed = transform(self.sample_subject)
    self.assert_tensor_almost_equal(self.sample_subject.t1.data, transformed.t1.data)

def test_with_noise(self):
    transform = RandomNoise()
    transformed = transform(self.sample_subject)
    self.assert_tensor_not_equal(self.sample_subject.t1.data, transformed.t1.data)

def test_constant_noise(self):
    transform = RandomNoise(mean=(5, 5), std=0)
    transformed = transform(self.sample_subject)
    self.assert_tensor_almost_equal(self.sample_subject.t1.data + 5, transformed.t1.data)

def test_negative_std(self):
    with pytest.raises(ValueError):
        RandomNoise(std=-2)

def test_std_range_with_negative_min(self):
    with pytest.raises(ValueError):
        RandomNoise(std=(-0.5, 4))

def test_wrong_std_type(self):
    with pytest.raises(ValueError):
        RandomNoise(std='wrong')

def test_wrong_mean_type(self):
    with pytest.raises(ValueError):
        RandomNoise(mean='wrong')

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

class TestRandomGhosting(TorchioTestCase):
    """Tests for `RandomGhosting`."""

    def test_with_zero_intensity(self):
        transform = RandomGhosting(intensity=0)
        transformed = transform(self.sample_subject)
        self.assert_tensor_almost_equal(self.sample_subject.t1.data, transformed.t1.data)

    def test_with_zero_ghost(self):
        transform = RandomGhosting(num_ghosts=0)
        transformed = transform(self.sample_subject)
        self.assert_tensor_almost_equal(self.sample_subject.t1.data, transformed.t1.data)

    def test_with_ghosting(self):
        transform = RandomGhosting()
        transformed = transform(self.sample_subject)
        self.assert_tensor_not_equal(self.sample_subject.t1.data, transformed.t1.data)

    def test_intensity_range_with_negative_min(self):
        with pytest.raises(ValueError):
            RandomGhosting(intensity=(-0.5, 4))

    def test_wrong_intensity_type(self):
        with pytest.raises(ValueError):
            RandomGhosting(intensity='wrong')

    def test_negative_num_ghosts(self):
        with pytest.raises(ValueError):
            RandomGhosting(num_ghosts=-1)

    def test_num_ghosts_range_with_negative_min(self):
        with pytest.raises(ValueError):
            RandomGhosting(num_ghosts=(-1, 4))

    def test_not_integer_num_ghosts(self):
        with pytest.raises(ValueError):
            RandomGhosting(num_ghosts=(0.7, 4))

    def test_wrong_num_ghosts_type(self):
        with pytest.raises(ValueError):
            RandomGhosting(num_ghosts='wrong')

    def test_out_of_range_axis(self):
        with pytest.raises(ValueError):
            RandomGhosting(axes=3)

    def test_out_of_range_axis_in_tuple(self):
        with pytest.raises(ValueError):
            RandomGhosting(axes=(0, -1, 2))

    def test_wrong_axes_type(self):
        with pytest.raises(ValueError):
            RandomGhosting(axes=None)

    def test_out_of_range_restore(self):
        with pytest.raises(ValueError):
            RandomGhosting(restore=-1)

    def test_wrong_restore_type(self):
        with pytest.raises(ValueError):
            RandomGhosting(restore='wrong')

def test_with_ghosting(self):
    transform = RandomGhosting()
    transformed = transform(self.sample_subject)
    self.assert_tensor_not_equal(self.sample_subject.t1.data, transformed.t1.data)

class TestRandomFlip(TorchioTestCase):

    def test_2d(self):
        subject = self.make_2d(self.sample_subject)
        transform = tio.RandomFlip(axes=(1, 2), flip_probability=1)
        transformed = transform(subject)
        self.assert_tensor_equal(torch.from_numpy(subject.t1.data.numpy()[..., ::-1, ::-1].copy()), transformed.t1.data)

    def test_out_of_range_axis(self):
        with pytest.raises(ValueError):
            tio.RandomFlip(axes=3)

    def test_out_of_range_axis_in_tuple(self):
        with pytest.raises(ValueError):
            tio.RandomFlip(axes=(0, -1, 2))

    def test_wrong_axes_type(self):
        with pytest.raises(ValueError):
            tio.RandomFlip(axes=None)

    def test_wrong_flip_probability_type(self):
        with pytest.raises(ValueError):
            tio.RandomFlip(flip_probability='wrong')

    def test_anatomical_axis(self):
        transform = tio.RandomFlip(axes=['i'], flip_probability=1)
        tensor = torch.rand(1, 2, 3, 4)
        transformed = transform(tensor)
        self.assert_tensor_equal(torch.from_numpy(tensor.numpy()[..., ::-1].copy()), transformed)

def test_2d(self):
    subject = self.make_2d(self.sample_subject)
    transform = tio.RandomFlip(axes=(1, 2), flip_probability=1)
    transformed = transform(subject)
    self.assert_tensor_equal(torch.from_numpy(subject.t1.data.numpy()[..., ::-1, ::-1].copy()), transformed.t1.data)

def test_anatomical_axis(self):
    transform = tio.RandomFlip(axes=['i'], flip_probability=1)
    tensor = torch.rand(1, 2, 3, 4)
    transformed = transform(tensor)
    self.assert_tensor_equal(torch.from_numpy(tensor.numpy()[..., ::-1].copy()), transformed)

class TestRandomAffineElasticDeformation(TorchioTestCase):
    """Tests for `RandomAffineElasticDeformation`."""

    def setUp(self):
        super().setUp()
        affine = self.sample_subject.t1.affine
        affine[:3, 3] = 100000.0

    def test_inputs_pta_gt_one(self):
        with pytest.raises(ValueError):
            tio.RandomAffineElasticDeformation(p=1.5)

    def test_inputs_pta_lt_zero(self):
        with pytest.raises(ValueError):
            tio.RandomAffineElasticDeformation(p=-1)

    def test_inputs_interpolation_int(self):
        with pytest.raises(TypeError):
            tio.RandomAffineElasticDeformation(image_interpolation=1)

    def test_inputs_interpolation(self):
        with pytest.raises(TypeError):
            tio.RandomAffineElasticDeformation(image_interpolation=0)

    def test_num_control_points_noint(self):
        with pytest.raises(ValueError):
            tio.RandomAffineElasticDeformation(elastic_kwargs={'num_control_points': 2.5})

    def test_num_control_points_small(self):
        with pytest.raises(ValueError):
            tio.RandomAffineElasticDeformation(elastic_kwargs={'num_control_points': 3})

    def test_max_displacement_no_num(self):
        with pytest.raises(ValueError):
            tio.RandomAffineElasticDeformation(elastic_kwargs={'max_displacement': None})

    def test_max_displacement_negative(self):
        with pytest.raises(ValueError):
            tio.RandomAffineElasticDeformation(elastic_kwargs={'max_displacement': -1})

    def test_wrong_locked_borders(self):
        with pytest.raises(ValueError):
            tio.RandomAffineElasticDeformation(elastic_kwargs={'locked_borders': -1})

    def test_coarse_grid_removed(self):
        with pytest.raises(ValueError):
            tio.RandomAffineElasticDeformation(elastic_kwargs={'num_control_points': (4, 5, 6), 'locked_borders': 2})

    def test_folding(self):
        transform = tio.RandomAffineElasticDeformation(elastic_kwargs={'num_control_points': (12, 5, 5), 'max_displacement': 6})
        with pytest.warns(RuntimeWarning):
            transform(self.sample_subject)

    def test_num_control_points(self):
        tio.RandomAffineElasticDeformation(elastic_kwargs={'num_control_points': 5})
        tio.RandomAffineElasticDeformation(elastic_kwargs={'num_control_points': (5, 6, 7)})

    def test_max_displacement(self):
        tio.RandomAffineElasticDeformation(elastic_kwargs={'max_displacement': 5})
        tio.RandomAffineElasticDeformation(elastic_kwargs={'max_displacement': (5, 6, 7)})

    def test_no_displacement(self):
        transform = tio.RandomAffineElasticDeformation(affine_kwargs={'scales': 0, 'degrees': 0, 'translation': 0}, elastic_kwargs={'max_displacement': 0})
        transformed = transform(self.sample_subject)
        self.assert_tensor_equal(self.sample_subject.t1.data, transformed.t1.data)
        self.assert_tensor_equal(self.sample_subject.label.data, transformed.label.data)

    def test_rotation_image(self):
        transform = tio.RandomAffineElasticDeformation(affine_kwargs={'degrees': (90, 90), 'default_pad_value': 0, 'center': 'image'})
        transformed = transform(self.sample_subject)
        total = transformed.t1.data.sum()
        self.assertNotEqual(total, 0)

    def test_rotation_origin(self):
        transform = tio.RandomAffineElasticDeformation(affine_kwargs={'degrees': (90, 90), 'default_pad_value': 0, 'center': 'origin'})
        transformed = transform(self.sample_subject)
        total = transformed.t1.data.sum()
        assert total == 0

    def test_no_rotation(self):
        transform = tio.RandomAffineElasticDeformation(affine_kwargs={'scales': (1, 1), 'degrees': (0, 0), 'default_pad_value': 0, 'center': 'image'}, elastic_kwargs={'max_displacement': 0})
        transformed = transform(self.sample_subject)
        self.assert_tensor_almost_equal(self.sample_subject.t1.data, transformed.t1.data)
        transform = tio.RandomAffineElasticDeformation(affine_kwargs={'scales': (1, 1), 'degrees': (180, 180), 'default_pad_value': 0, 'center': 'image'}, elastic_kwargs={'max_displacement': 0})
        transformed = transform(self.sample_subject)
        transformed = transform(transformed)
        self.assert_tensor_almost_equal(self.sample_subject.t1.data, transformed.t1.data)

    def test_isotropic(self):
        tio.RandomAffineElasticDeformation(affine_kwargs={'isotropic': True})(self.sample_subject)

    def test_mean(self):
        tio.RandomAffineElasticDeformation(affine_kwargs={'default_pad_value': 'mean'})(self.sample_subject)

    def test_otsu(self):
        tio.RandomAffineElasticDeformation(affine_kwargs={'default_pad_value': 'otsu'})(self.sample_subject)

    def test_bad_center(self):
        with pytest.raises(ValueError):
            tio.RandomAffineElasticDeformation(affine_kwargs={'center': 'bad'})

    def test_negative_scales(self):
        with pytest.raises(ValueError):
            tio.RandomAffineElasticDeformation(affine_kwargs={'scales': (-1, 1)})

    def test_scale_too_large(self):
        with pytest.raises(ValueError):
            tio.RandomAffineElasticDeformation(affine_kwargs={'scales': 1.5})

    def test_scales_range_with_negative_min(self):
        with pytest.raises(ValueError):
            tio.RandomAffineElasticDeformation(affine_kwargs={'scales': (-1, 4)})

    def test_wrong_scales_type(self):
        with pytest.raises(ValueError):
            tio.RandomAffineElasticDeformation(affine_kwargs={'scales': 'wrong'})

    def test_wrong_degrees_type(self):
        with pytest.raises(ValueError):
            tio.RandomAffineElasticDeformation(affine_kwargs={'degrees': 'wrong'})

    def test_too_many_translation_values(self):
        with pytest.raises(ValueError):
            tio.RandomAffineElasticDeformation(affine_kwargs={'translation': (-10, 4, 42)})

    def test_wrong_translation_type(self):
        with pytest.raises(ValueError):
            tio.RandomAffineElasticDeformation(affine_kwargs={'translation': 'wrong'})

    def test_wrong_center(self):
        with pytest.raises(ValueError):
            tio.RandomAffineElasticDeformation(affine_kwargs={'center': 0})

    def test_wrong_default_pad_value(self):
        with pytest.raises(ValueError):
            tio.RandomAffineElasticDeformation(affine_kwargs={'default_pad_value': 'wrong'})

    def test_wrong_image_interpolation_type(self):
        with pytest.raises(TypeError):
            tio.RandomAffineElasticDeformation(affine_kwargs={'image_interpolation': 0})

    def test_wrong_image_interpolation_value(self):
        with pytest.raises(ValueError):
            tio.RandomAffineElasticDeformation(affine_kwargs={'image_interpolation': 'wrong'})

    def test_incompatible_args_isotropic(self):
        with pytest.raises(ValueError):
            tio.RandomAffineElasticDeformation(affine_kwargs={'scales': (0.8, 0.5, 0.1), 'isotropic': True})

    def test_parse_scales(self):

        def do_assert(transform):
            assert transform.random_affine.scales == 3 * (0.9, 1.1)
        do_assert(tio.RandomAffineElasticDeformation(affine_kwargs={'scales': 0.1}))
        do_assert(tio.RandomAffineElasticDeformation(affine_kwargs={'scales': (0.9, 1.1)}))
        do_assert(tio.RandomAffineElasticDeformation(affine_kwargs={'scales': 3 * (0.1,)}))
        do_assert(tio.RandomAffineElasticDeformation(affine_kwargs={'scales': 3 * [0.9, 1.1]}))

    def test_parse_degrees(self):

        def do_assert(transform):
            assert transform.random_affine.degrees == 3 * (-10, 10)
        do_assert(tio.RandomAffineElasticDeformation(affine_kwargs={'degrees': 10}))
        do_assert(tio.RandomAffineElasticDeformation(affine_kwargs={'degrees': (-10, 10)}))
        do_assert(tio.RandomAffineElasticDeformation(affine_kwargs={'degrees': 3 * (10,)}))
        do_assert(tio.RandomAffineElasticDeformation(affine_kwargs={'degrees': 3 * [-10, 10]}))

    def test_parse_translation(self):

        def do_assert(transform):
            assert transform.random_affine.translation == 3 * (-10, 10)
        do_assert(tio.RandomAffineElasticDeformation(affine_kwargs={'translation': 10}))
        do_assert(tio.RandomAffineElasticDeformation(affine_kwargs={'translation': (-10, 10)}))
        do_assert(tio.RandomAffineElasticDeformation(affine_kwargs={'translation': 3 * (10,)}))
        do_assert(tio.RandomAffineElasticDeformation(affine_kwargs={'translation': 3 * [-10, 10]}))

    def test_default_value_label_map(self):
        a = torch.tensor([[1, 0, 0], [0, 1, 0], [0, 0, 1]]).reshape(1, 3, 3, 1)
        image = tio.LabelMap(tensor=a)
        aff = tio.RandomAffineElasticDeformation(affine_kwargs={'translation': (0, 1, 1), 'default_pad_value': 'otsu'})
        transformed = aff(image)
        assert all((n in (0, 1) for n in transformed.data.flatten()))

    def test_no_inverse(self):
        tensor = torch.zeros((1, 2, 2, 2))
        tensor[0, 1, 1, 1] = 1
        expected = torch.zeros((1, 2, 2, 2))
        expected[0, 0, 1, 1] = 1
        scales = (1, 1, 1)
        degrees = (0, 0, 90)
        translation = (0, 0, 0)
        apply_affine = tio.Affine(scales, degrees, translation)
        transformed = apply_affine(tensor)
        self.assert_tensor_almost_equal(transformed, expected)

    def test_different_spaces(self):
        t1 = self.sample_subject.t1
        label = tio.Resample(2)(self.sample_subject.label)
        new_subject = tio.Subject(t1=t1, label=label)
        with pytest.raises(RuntimeError):
            tio.RandomAffineElasticDeformation()(new_subject)
        tio.RandomAffineElasticDeformation(affine_kwargs={'check_shape': False})(new_subject)

    def test_transform_order(self):
        src_transform = tio.RandomAffineElasticDeformation(affine_kwargs={'scales': 0, 'degrees': 0, 'translation': 1}, elastic_kwargs={'num_control_points': 5, 'max_displacement': 1})
        (scales, degrees, translation), control_points = src_transform.get_params()
        max_displacement = src_transform.random_elastic.max_displacement
        transform1 = tio.AffineElasticDeformation(affine_first=True, affine_params={'scales': scales, 'degrees': degrees, 'translation': translation}, elastic_params={'control_points': control_points, 'max_displacement': max_displacement})
        transform2 = tio.AffineElasticDeformation(affine_first=False, affine_params={'scales': scales, 'degrees': degrees, 'translation': translation}, elastic_params={'control_points': control_points, 'max_displacement': max_displacement})
        transformed1 = transform1(self.sample_subject)
        transformed2 = transform2(self.sample_subject)
        self.assert_tensor_not_equal(transformed1.t1.data, transformed2.t1.data)

def test_no_displacement(self):
    transform = tio.RandomAffineElasticDeformation(affine_kwargs={'scales': 0, 'degrees': 0, 'translation': 0}, elastic_kwargs={'max_displacement': 0})
    transformed = transform(self.sample_subject)
    self.assert_tensor_equal(self.sample_subject.t1.data, transformed.t1.data)
    self.assert_tensor_equal(self.sample_subject.label.data, transformed.label.data)

def test_rotation_image(self):
    transform = tio.RandomAffineElasticDeformation(affine_kwargs={'degrees': (90, 90), 'default_pad_value': 0, 'center': 'image'})
    transformed = transform(self.sample_subject)
    total = transformed.t1.data.sum()
    self.assertNotEqual(total, 0)

def test_rotation_origin(self):
    transform = tio.RandomAffineElasticDeformation(affine_kwargs={'degrees': (90, 90), 'default_pad_value': 0, 'center': 'origin'})
    transformed = transform(self.sample_subject)
    total = transformed.t1.data.sum()
    assert total == 0

def test_no_rotation(self):
    transform = tio.RandomAffineElasticDeformation(affine_kwargs={'scales': (1, 1), 'degrees': (0, 0), 'default_pad_value': 0, 'center': 'image'}, elastic_kwargs={'max_displacement': 0})
    transformed = transform(self.sample_subject)
    self.assert_tensor_almost_equal(self.sample_subject.t1.data, transformed.t1.data)
    transform = tio.RandomAffineElasticDeformation(affine_kwargs={'scales': (1, 1), 'degrees': (180, 180), 'default_pad_value': 0, 'center': 'image'}, elastic_kwargs={'max_displacement': 0})
    transformed = transform(self.sample_subject)
    transformed = transform(transformed)
    self.assert_tensor_almost_equal(self.sample_subject.t1.data, transformed.t1.data)

class TestRandomSpike(TorchioTestCase):
    """Tests for `RandomSpike`."""

    def test_with_zero_intensity(self):
        transform = RandomSpike(intensity=0)
        transformed = transform(self.sample_subject)
        self.assert_tensor_almost_equal(self.sample_subject.t1.data, transformed.t1.data)

    def test_with_zero_spike(self):
        transform = RandomSpike(num_spikes=0)
        transformed = transform(self.sample_subject)
        self.assert_tensor_almost_equal(self.sample_subject.t1.data, transformed.t1.data)

    def test_with_spikes(self):
        transform = RandomSpike()
        transformed = transform(self.sample_subject)
        self.assert_tensor_not_equal(self.sample_subject.t1.data, transformed.t1.data)

    def test_negative_num_spikes(self):
        with pytest.raises(ValueError):
            RandomSpike(num_spikes=-1)

    def test_num_spikes_range_with_negative_min(self):
        with pytest.raises(ValueError):
            RandomSpike(num_spikes=(-1, 4))

    def test_not_integer_num_spikes(self):
        with pytest.raises(ValueError):
            RandomSpike(num_spikes=(0.7, 4))

    def test_wrong_num_spikes_type(self):
        with pytest.raises(ValueError):
            RandomSpike(num_spikes='wrong')

    def test_wrong_intensity_type(self):
        with pytest.raises(ValueError):
            RandomSpike(intensity='wrong')

def test_with_zero_intensity(self):
    transform = RandomSpike(intensity=0)
    transformed = transform(self.sample_subject)
    self.assert_tensor_almost_equal(self.sample_subject.t1.data, transformed.t1.data)

def test_with_zero_spike(self):
    transform = RandomSpike(num_spikes=0)
    transformed = transform(self.sample_subject)
    self.assert_tensor_almost_equal(self.sample_subject.t1.data, transformed.t1.data)

def test_with_spikes(self):
    transform = RandomSpike()
    transformed = transform(self.sample_subject)
    self.assert_tensor_not_equal(self.sample_subject.t1.data, transformed.t1.data)

def test_negative_num_spikes(self):
    with pytest.raises(ValueError):
        RandomSpike(num_spikes=-1)

def test_num_spikes_range_with_negative_min(self):
    with pytest.raises(ValueError):
        RandomSpike(num_spikes=(-1, 4))

def test_not_integer_num_spikes(self):
    with pytest.raises(ValueError):
        RandomSpike(num_spikes=(0.7, 4))

def test_wrong_num_spikes_type(self):
    with pytest.raises(ValueError):
        RandomSpike(num_spikes='wrong')

def test_wrong_intensity_type(self):
    with pytest.raises(ValueError):
        RandomSpike(intensity='wrong')

class TestRandomBiasField(TorchioTestCase):

    def test_no_bias(self):
        transform = tio.RandomBiasField(coefficients=0)
        transformed = transform(self.sample_subject)
        self.assert_tensor_almost_equal(self.sample_subject.t1.data, transformed.t1.data)

    def test_with_bias(self):
        transform = tio.RandomBiasField(coefficients=0.1)
        transformed = transform(self.sample_subject)
        self.assert_tensor_not_equal(self.sample_subject.t1.data, transformed.t1.data)

    def test_wrong_coefficient_type(self):
        with pytest.raises(ValueError):
            tio.RandomBiasField(coefficients='wrong')

    def test_negative_order(self):
        with pytest.raises(ValueError):
            tio.RandomBiasField(order=-1)

    def test_wrong_order_type(self):
        with pytest.raises(TypeError):
            tio.RandomBiasField(order='wrong')

    def test_small_image(self):
        tio.RandomBiasField()(torch.rand(1, 2, 3, 4))

def test_no_bias(self):
    transform = tio.RandomBiasField(coefficients=0)
    transformed = transform(self.sample_subject)
    self.assert_tensor_almost_equal(self.sample_subject.t1.data, transformed.t1.data)

def test_with_bias(self):
    transform = tio.RandomBiasField(coefficients=0.1)
    transformed = transform(self.sample_subject)
    self.assert_tensor_not_equal(self.sample_subject.t1.data, transformed.t1.data)

def test_wrong_coefficient_type(self):
    with pytest.raises(ValueError):
        tio.RandomBiasField(coefficients='wrong')

def test_negative_order(self):
    with pytest.raises(ValueError):
        tio.RandomBiasField(order=-1)

def test_wrong_order_type(self):
    with pytest.raises(TypeError):
        tio.RandomBiasField(order='wrong')

def test_small_image(self):
    tio.RandomBiasField()(torch.rand(1, 2, 3, 4))

class TestRandomSwap(TorchioTestCase):

    def test_no_swap(self):
        transform = tio.RandomSwap(patch_size=5, num_iterations=0)
        transformed = transform(self.sample_subject)
        self.assert_tensor_equal(self.sample_subject.t1.data, transformed.t1.data)

    def test_with_swap(self):
        transform = tio.RandomSwap(patch_size=5)
        transformed = transform(self.sample_subject)
        self.assert_tensor_not_equal(self.sample_subject.t1.data, transformed.t1.data)

    def test_wrong_num_iterations_type(self):
        with pytest.raises(TypeError):
            tio.RandomSwap(num_iterations='wrong')

    def test_negative_num_iterations(self):
        with pytest.raises(ValueError):
            tio.RandomSwap(num_iterations=-1)

def test_no_swap(self):
    transform = tio.RandomSwap(patch_size=5, num_iterations=0)
    transformed = transform(self.sample_subject)
    self.assert_tensor_equal(self.sample_subject.t1.data, transformed.t1.data)

def test_with_swap(self):
    transform = tio.RandomSwap(patch_size=5)
    transformed = transform(self.sample_subject)
    self.assert_tensor_not_equal(self.sample_subject.t1.data, transformed.t1.data)

def test_wrong_num_iterations_type(self):
    with pytest.raises(TypeError):
        tio.RandomSwap(num_iterations='wrong')

def test_negative_num_iterations(self):
    with pytest.raises(ValueError):
        tio.RandomSwap(num_iterations=-1)

class TestRandomAffine(TorchioTestCase):
    """Tests for `RandomAffine`."""

    def setUp(self):
        super().setUp()
        affine = self.sample_subject.t1.affine
        affine[:3, 3] = 100000.0

    def test_rotation_image(self):
        transform = tio.RandomAffine(degrees=(90, 90), default_pad_value=0, center='image')
        transformed = transform(self.sample_subject)
        total = transformed.t1.data.sum()
        self.assertNotEqual(total, 0)

    def test_rotation_origin(self):
        transform = tio.RandomAffine(degrees=(90, 90), default_pad_value=0, center='origin')
        transformed = transform(self.sample_subject)
        total = transformed.t1.data.sum()
        assert total == 0

    def test_no_rotation(self):
        transform = tio.RandomAffine(scales=(1, 1), degrees=(0, 0), default_pad_value=0, center='image')
        transformed = transform(self.sample_subject)
        self.assert_tensor_almost_equal(self.sample_subject.t1.data, transformed.t1.data)
        transform = tio.RandomAffine(scales=(1, 1), degrees=(180, 180), default_pad_value=0, center='image')
        transformed = transform(self.sample_subject)
        transformed = transform(transformed)
        self.assert_tensor_almost_equal(self.sample_subject.t1.data, transformed.t1.data)

    def test_isotropic(self):
        tio.RandomAffine(isotropic=True)(self.sample_subject)

    def test_mean(self):
        tio.RandomAffine(default_pad_value='mean')(self.sample_subject)

    def test_otsu(self):
        tio.RandomAffine(default_pad_value='otsu')(self.sample_subject)

    def test_bad_center(self):
        with pytest.raises(ValueError):
            tio.RandomAffine(center='bad')

    def test_negative_scales(self):
        with pytest.raises(ValueError):
            tio.RandomAffine(scales=(-1, 1))

    def test_scale_too_large(self):
        with pytest.raises(ValueError):
            tio.RandomAffine(scales=1.5)

    def test_scales_range_with_negative_min(self):
        with pytest.raises(ValueError):
            tio.RandomAffine(scales=(-1, 4))

    def test_wrong_scales_type(self):
        with pytest.raises(ValueError):
            tio.RandomAffine(scales='wrong')

    def test_wrong_degrees_type(self):
        with pytest.raises(ValueError):
            tio.RandomAffine(degrees='wrong')

    def test_too_many_translation_values(self):
        with pytest.raises(ValueError):
            tio.RandomAffine(translation=(-10, 4, 42))

    def test_wrong_translation_type(self):
        with pytest.raises(ValueError):
            tio.RandomAffine(translation='wrong')

    def test_wrong_center(self):
        with pytest.raises(ValueError):
            tio.RandomAffine(center=0)

    def test_wrong_default_pad_value(self):
        with pytest.raises(ValueError):
            tio.RandomAffine(default_pad_value='wrong')

    def test_wrong_image_interpolation_type(self):
        with pytest.raises(TypeError):
            tio.RandomAffine(image_interpolation=0)

    def test_wrong_image_interpolation_value(self):
        with pytest.raises(ValueError):
            tio.RandomAffine(image_interpolation='wrong')

    def test_incompatible_args_isotropic(self):
        with pytest.raises(ValueError):
            tio.RandomAffine(scales=(0.8, 0.5, 0.1), isotropic=True)

    def test_parse_scales(self):

        def do_assert(transform):
            assert transform.scales == 3 * (0.9, 1.1)
        do_assert(tio.RandomAffine(scales=0.1))
        do_assert(tio.RandomAffine(scales=(0.9, 1.1)))
        do_assert(tio.RandomAffine(scales=3 * (0.1,)))
        do_assert(tio.RandomAffine(scales=3 * [0.9, 1.1]))

    def test_parse_degrees(self):

        def do_assert(transform):
            assert transform.degrees == 3 * (-10, 10)
        do_assert(tio.RandomAffine(degrees=10))
        do_assert(tio.RandomAffine(degrees=(-10, 10)))
        do_assert(tio.RandomAffine(degrees=3 * (10,)))
        do_assert(tio.RandomAffine(degrees=3 * [-10, 10]))

    def test_parse_translation(self):

        def do_assert(transform):
            assert transform.translation == 3 * (-10, 10)
        do_assert(tio.RandomAffine(translation=10))
        do_assert(tio.RandomAffine(translation=(-10, 10)))
        do_assert(tio.RandomAffine(translation=3 * (10,)))
        do_assert(tio.RandomAffine(translation=3 * [-10, 10]))

    def test_default_value_label_map(self):
        a = torch.tensor([[1, 0, 0], [0, 1, 0], [0, 0, 1]]).reshape(1, 3, 3, 1)
        image = tio.LabelMap(tensor=a)
        aff = tio.RandomAffine(translation=(0, 1, 1), default_pad_value='otsu')
        transformed = aff(image)
        assert all((n in (0, 1) for n in transformed.data.flatten()))

    def test_default_pad_label_parameter(self):
        label_data = torch.ones((1, 2, 2, 2))
        subject = tio.Subject(label=tio.LabelMap(tensor=label_data))
        transform = tio.RandomAffine(translation=(10, 10), default_pad_label=250)
        transformed_subject = transform(subject)
        message = 'default_pad_label=250 should be respected for LABEL images'
        has_expected_value = (transformed_subject['label'].tensor == 250).any()
        assert has_expected_value, message
        message = 'default_pad_value should still be ignored for LABEL images (backward compatibility)'
        aff_old = tio.RandomAffine(translation=(-10, 10, -10, 10, -10, 10), default_pad_value=250)
        s_aug_old = aff_old.apply_transform(subject)
        non_one_values = s_aug_old['label'].data[s_aug_old['label'].data != 1]
        all_zeros = (non_one_values == 0).all() if len(non_one_values) > 0 else True
        assert all_zeros, message
        affine_transform = tio.Affine(scales=(1, 1, 1), degrees=(0, 0, 0), translation=(5, 0, 0), default_pad_label=123)
        s_affine = affine_transform.apply_transform(subject)
        has_affine_value = (s_affine['label'].tensor == 123).any()
        assert has_affine_value, 'Direct Affine class should respect default_pad_label'

    def test_wrong_default_pad_label(self):
        with pytest.raises(ValueError):
            tio.RandomAffine(default_pad_label='minimum')

    def test_no_inverse(self):
        tensor = torch.zeros((1, 2, 2, 2))
        tensor[0, 1, 1, 1] = 1
        expected = torch.zeros((1, 2, 2, 2))
        expected[0, 0, 1, 1] = 1
        scales = (1, 1, 1)
        degrees = (0, 0, 90)
        translation = (0, 0, 0)
        apply_affine = tio.Affine(scales, degrees, translation)
        transformed = apply_affine(tensor)
        self.assert_tensor_almost_equal(transformed, expected)

    def test_different_spaces(self):
        t1 = self.sample_subject.t1
        label = tio.Resample(2)(self.sample_subject.label)
        new_subject = tio.Subject(t1=t1, label=label)
        with pytest.raises(RuntimeError):
            tio.RandomAffine()(new_subject)
        tio.RandomAffine(check_shape=False)(new_subject)

def test_rotation_image(self):
    transform = tio.RandomAffine(degrees=(90, 90), default_pad_value=0, center='image')
    transformed = transform(self.sample_subject)
    total = transformed.t1.data.sum()
    self.assertNotEqual(total, 0)

def test_rotation_origin(self):
    transform = tio.RandomAffine(degrees=(90, 90), default_pad_value=0, center='origin')
    transformed = transform(self.sample_subject)
    total = transformed.t1.data.sum()
    assert total == 0

def test_no_rotation(self):
    transform = tio.RandomAffine(scales=(1, 1), degrees=(0, 0), default_pad_value=0, center='image')
    transformed = transform(self.sample_subject)
    self.assert_tensor_almost_equal(self.sample_subject.t1.data, transformed.t1.data)
    transform = tio.RandomAffine(scales=(1, 1), degrees=(180, 180), default_pad_value=0, center='image')
    transformed = transform(self.sample_subject)
    transformed = transform(transformed)
    self.assert_tensor_almost_equal(self.sample_subject.t1.data, transformed.t1.data)

class TestRandomMotion(TorchioTestCase):
    """Tests for `RandomMotion`."""

    def test_bad_num_transforms_value(self):
        with pytest.raises(ValueError):
            RandomMotion(num_transforms=0)

    def test_no_movement(self):
        transform = RandomMotion(degrees=0, translation=0, num_transforms=1)
        transformed = transform(self.sample_subject)
        self.assert_tensor_almost_equal(self.sample_subject.t1.data, transformed.t1.data, atol=0.0001, rtol=0)

    def test_with_movement(self):
        transform = RandomMotion(num_transforms=1)
        transformed = transform(self.sample_subject)
        self.assert_tensor_not_equal(self.sample_subject.t1.data, transformed.t1.data)

    def test_negative_degrees(self):
        with pytest.raises(ValueError):
            RandomMotion(degrees=-10)

    def test_wrong_degrees_type(self):
        with pytest.raises(ValueError):
            RandomMotion(degrees='wrong')

    def test_negative_translation(self):
        with pytest.raises(ValueError):
            RandomMotion(translation=-10)

    def test_wrong_translation_type(self):
        with pytest.raises(ValueError):
            RandomMotion(translation='wrong')

    def test_wrong_image_interpolation_type(self):
        with pytest.raises(TypeError):
            RandomMotion(image_interpolation=0)

    def test_wrong_image_interpolation_value(self):
        with pytest.raises(ValueError):
            RandomMotion(image_interpolation='wrong')

def test_with_movement(self):
    transform = RandomMotion(num_transforms=1)
    transformed = transform(self.sample_subject)
    self.assert_tensor_not_equal(self.sample_subject.t1.data, transformed.t1.data)

class TestToOrientation(TorchioTestCase):

    def test_invalid_orientation_length(self):
        with pytest.raises(ValueError, match='3-letter'):
            tio.ToOrientation('RA')

    def test_invalid_orientation_characters(self):
        with pytest.raises(ValueError, match='three distinct characters'):
            tio.ToOrientation('XYZ')

    def test_missing_axis_direction(self):
        match = 'must include one character for each axis'
        with pytest.raises(ValueError, match=match):
            tio.ToOrientation('RAA')

    def test_no_change_if_already_correct(self):
        transform = tio.ToOrientation('RAS')
        subject = transform(self.sample_subject)
        self.assert_tensor_equal(subject.t1.data, self.sample_subject.t1.data)
        self.assert_tensor_equal(subject.t1.affine, self.sample_subject.t1.affine)

    def test_ras_to_las(self):
        ras_subject = self.sample_subject
        to_las = tio.ToOrientation('LAS')
        las_subject = to_las(ras_subject)
        self.assertEqual(las_subject.t1.orientation, ('L', 'A', 'S'))
        expected_affine = ras_subject.t1.affine.copy()
        expected_affine[0, 0] = -ras_subject.t1.affine[0, 0]
        expected_affine[0, 3] = ras_subject.t1.affine[0, 0] * (ras_subject.t1.spatial_shape[0] - 1) + ras_subject.t1.affine[0, 3]
        flipped_data = torch.flip(ras_subject.t1.data, dims=[1])
        self.assert_tensor_almost_equal(las_subject.t1.data, flipped_data, check_stride=False)
        self.assert_tensor_almost_equal(las_subject.t1.affine, expected_affine)

    def test_ras_to_las_to_ras(self):
        original_subject = self.sample_subject
        original_data = original_subject.t1.data.clone()
        original_affine = original_subject.t1.affine.copy()
        to_las = tio.ToOrientation('LAS')
        las_subject = to_las(original_subject)
        self.assertEqual(las_subject.t1.orientation, ('L', 'A', 'S'))
        to_ras = tio.ToOrientation('RAS')
        recovered_subject = to_ras(las_subject)
        self.assertEqual(recovered_subject.t1.orientation, ('R', 'A', 'S'))
        self.assert_tensor_almost_equal(recovered_subject.t1.data, original_data, check_stride=False)
        self.assert_tensor_almost_equal(recovered_subject.t1.affine, original_affine)

def test_invalid_orientation_length(self):
    with pytest.raises(ValueError, match='3-letter'):
        tio.ToOrientation('RA')

def test_invalid_orientation_characters(self):
    with pytest.raises(ValueError, match='three distinct characters'):
        tio.ToOrientation('XYZ')

def test_missing_axis_direction(self):
    match = 'must include one character for each axis'
    with pytest.raises(ValueError, match=match):
        tio.ToOrientation('RAA')

def test_no_change_if_already_correct(self):
    transform = tio.ToOrientation('RAS')
    subject = transform(self.sample_subject)
    self.assert_tensor_equal(subject.t1.data, self.sample_subject.t1.data)
    self.assert_tensor_equal(subject.t1.affine, self.sample_subject.t1.affine)

def test_ras_to_las(self):
    ras_subject = self.sample_subject
    to_las = tio.ToOrientation('LAS')
    las_subject = to_las(ras_subject)
    self.assertEqual(las_subject.t1.orientation, ('L', 'A', 'S'))
    expected_affine = ras_subject.t1.affine.copy()
    expected_affine[0, 0] = -ras_subject.t1.affine[0, 0]
    expected_affine[0, 3] = ras_subject.t1.affine[0, 0] * (ras_subject.t1.spatial_shape[0] - 1) + ras_subject.t1.affine[0, 3]
    flipped_data = torch.flip(ras_subject.t1.data, dims=[1])
    self.assert_tensor_almost_equal(las_subject.t1.data, flipped_data, check_stride=False)
    self.assert_tensor_almost_equal(las_subject.t1.affine, expected_affine)

def test_ras_to_las_to_ras(self):
    original_subject = self.sample_subject
    original_data = original_subject.t1.data.clone()
    original_affine = original_subject.t1.affine.copy()
    to_las = tio.ToOrientation('LAS')
    las_subject = to_las(original_subject)
    self.assertEqual(las_subject.t1.orientation, ('L', 'A', 'S'))
    to_ras = tio.ToOrientation('RAS')
    recovered_subject = to_ras(las_subject)
    self.assertEqual(recovered_subject.t1.orientation, ('R', 'A', 'S'))
    self.assert_tensor_almost_equal(recovered_subject.t1.data, original_data, check_stride=False)
    self.assert_tensor_almost_equal(recovered_subject.t1.affine, original_affine)

class TestTranspose(TorchioTestCase):

    def test_transpose(self):
        transform = tio.Transpose()
        image = tio.ScalarImage(self.get_image_path('image'))
        transformed = transform(image)
        sitk_image = sitk.GetImageFromArray(image.numpy()[0])
        from_sitk = tio.ScalarImage.from_sitk(sitk_image)
        self.assert_tensor_equal(transformed.data, from_sitk.data)

    def test_orientation_reversed(self):
        transform = tio.Transpose()
        image = tio.ScalarImage(self.get_image_path('image'))
        transformed = transform(image)
        self.assertEqual(transformed.orientation_str, image.orientation_str[::-1])

def test_transpose(self):
    transform = tio.Transpose()
    image = tio.ScalarImage(self.get_image_path('image'))
    transformed = transform(image)
    sitk_image = sitk.GetImageFromArray(image.numpy()[0])
    from_sitk = tio.ScalarImage.from_sitk(sitk_image)
    self.assert_tensor_equal(transformed.data, from_sitk.data)

def test_orientation_reversed(self):
    transform = tio.Transpose()
    image = tio.ScalarImage(self.get_image_path('image'))
    transformed = transform(image)
    self.assertEqual(transformed.orientation_str, image.orientation_str[::-1])

class TestToCanonical(TorchioTestCase):

    def test_no_changes(self):
        transform = tio.ToCanonical()
        transformed = transform(self.sample_subject)
        self.assert_tensor_equal(transformed.t1.data, self.sample_subject.t1.data)
        self.assert_tensor_equal(transformed.t1.affine, self.sample_subject.t1.affine)

    def test_las_to_ras(self):
        self.sample_subject.t1.affine[0, 0] = -1
        transform = tio.ToCanonical()
        transformed = transform(self.sample_subject)
        assert transformed.t1.orientation == ('R', 'A', 'S')
        array_flip = self.sample_subject.t1.data.numpy()[:, ::-1, :, :].copy()
        self.assert_tensor_almost_equal(transformed.t1.data, torch.from_numpy(array_flip), check_stride=False)
        fixture = np.eye(4)
        fixture[0, -1] = -self.sample_subject.t1.spatial_shape[0] + 1
        self.assert_tensor_equal(transformed.t1.affine, fixture)

def test_no_changes(self):
    transform = tio.ToCanonical()
    transformed = transform(self.sample_subject)
    self.assert_tensor_equal(transformed.t1.data, self.sample_subject.t1.data)
    self.assert_tensor_equal(transformed.t1.affine, self.sample_subject.t1.affine)

def test_las_to_ras(self):
    self.sample_subject.t1.affine[0, 0] = -1
    transform = tio.ToCanonical()
    transformed = transform(self.sample_subject)
    assert transformed.t1.orientation == ('R', 'A', 'S')
    array_flip = self.sample_subject.t1.data.numpy()[:, ::-1, :, :].copy()
    self.assert_tensor_almost_equal(transformed.t1.data, torch.from_numpy(array_flip), check_stride=False)
    fixture = np.eye(4)
    fixture[0, -1] = -self.sample_subject.t1.spatial_shape[0] + 1
    self.assert_tensor_equal(transformed.t1.affine, fixture)

class TestEnsureShapeMultiple(TorchioTestCase):

    def test_bad_method(self):
        with pytest.raises(ValueError):
            tio.EnsureShapeMultiple(1, method='bad')

    def test_pad(self):
        sample_t1 = self.sample_subject.t1
        assert sample_t1.shape == (1, 10, 20, 30)
        transform = tio.EnsureShapeMultiple(4, method='pad')
        transformed = transform(sample_t1)
        assert transformed.shape == (1, 12, 20, 32)

    def test_crop(self):
        sample_t1 = self.sample_subject.t1
        assert sample_t1.shape == (1, 10, 20, 30)
        transform = tio.EnsureShapeMultiple(4, method='crop')
        transformed = transform(sample_t1)
        assert transformed.shape == (1, 8, 20, 28)

    def test_2d(self):
        sample_t1 = self.sample_subject.t1
        sample_2d = sample_t1.data[..., :1]
        assert sample_2d.shape == (1, 10, 20, 1)
        transform = tio.EnsureShapeMultiple(4, method='crop')
        transformed = transform(sample_2d)
        assert transformed.shape == (1, 8, 20, 1)

def test_bad_method(self):
    with pytest.raises(ValueError):
        tio.EnsureShapeMultiple(1, method='bad')

def test_pad(self):
    sample_t1 = self.sample_subject.t1
    assert sample_t1.shape == (1, 10, 20, 30)
    transform = tio.EnsureShapeMultiple(4, method='pad')
    transformed = transform(sample_t1)
    assert transformed.shape == (1, 12, 20, 32)

def test_crop(self):
    sample_t1 = self.sample_subject.t1
    assert sample_t1.shape == (1, 10, 20, 30)
    transform = tio.EnsureShapeMultiple(4, method='crop')
    transformed = transform(sample_t1)
    assert transformed.shape == (1, 8, 20, 28)

def test_2d(self):
    sample_t1 = self.sample_subject.t1
    sample_2d = sample_t1.data[..., :1]
    assert sample_2d.shape == (1, 10, 20, 1)
    transform = tio.EnsureShapeMultiple(4, method='crop')
    transformed = transform(sample_2d)
    assert transformed.shape == (1, 8, 20, 1)

class TestCropOrPad(TorchioTestCase):
    """Tests for `CropOrPad`."""

    def test_no_changes(self):
        sample_t1 = self.sample_subject['t1']
        shape = sample_t1.spatial_shape
        transform = tio.CropOrPad(shape)
        transformed = transform(self.sample_subject)
        self.assert_tensor_equal(sample_t1.data, transformed['t1'].data)
        self.assert_tensor_equal(sample_t1.affine, transformed['t1'].affine)

    def test_no_changes_mask(self):
        sample_t1 = self.sample_subject['t1']
        sample_mask = self.sample_subject['label'].data
        sample_mask *= 0
        shape = sample_t1.spatial_shape
        transform = tio.CropOrPad(shape, mask_name='label')
        with pytest.warns(RuntimeWarning):
            transformed = transform(self.sample_subject)
        for key in transformed:
            image = self.sample_subject[key]
            self.assert_tensor_equal(image.data, transformed[key].data)
            self.assert_tensor_equal(image.affine, transformed[key].affine)

    def test_different_shape(self):
        shape = self.sample_subject['t1'].spatial_shape
        target_shape = (9, 21, 30)
        transform = tio.CropOrPad(target_shape)
        transformed = transform(self.sample_subject)
        for key in transformed:
            result_shape = transformed[key].spatial_shape
            self.assertNotEqual(shape, result_shape)

    def test_shape_right(self):
        target_shape = (9, 21, 30)
        transform = tio.CropOrPad(target_shape)
        transformed = transform(self.sample_subject)
        for key in transformed:
            result_shape = transformed[key].spatial_shape
            assert target_shape == result_shape

    def test_only_pad(self):
        target_shape = (11, 22, 30)
        transform = tio.CropOrPad(target_shape)
        transformed = transform(self.sample_subject)
        for key in transformed:
            result_shape = transformed[key].spatial_shape
            assert target_shape == result_shape

    def test_only_crop(self):
        target_shape = (9, 18, 30)
        transform = tio.CropOrPad(target_shape)
        transformed = transform(self.sample_subject)
        for key in transformed:
            result_shape = transformed[key].spatial_shape
            assert target_shape == result_shape

    def test_shape_negative(self):
        with pytest.raises(ValueError):
            tio.CropOrPad(-1)

    def test_shape_float(self):
        with pytest.raises(ValueError):
            tio.CropOrPad(2.5)

    def test_shape_string(self):
        with pytest.raises(ValueError):
            tio.CropOrPad('')

    def test_shape_one(self):
        transform = tio.CropOrPad(1)
        transformed = transform(self.sample_subject)
        for key in transformed:
            result_shape = transformed[key].spatial_shape
            assert result_shape == (1, 1, 1)

    def test_wrong_mask_name(self):
        cop = tio.CropOrPad(1, mask_name='wrong')
        with pytest.warns(RuntimeWarning):
            cop(self.sample_subject)

    def test_empty_mask(self):
        target_shape = (8, 22, 30)
        transform = tio.CropOrPad(target_shape, mask_name='label')
        mask = self.sample_subject['label'].data
        mask *= 0
        with pytest.warns(RuntimeWarning):
            transform(self.sample_subject)

    def mask_only(self, target_shape):
        transform = tio.CropOrPad(target_shape, mask_name='label')
        mask = self.sample_subject['label'].data
        mask *= 0
        mask[0, 4:6, 5:8, 3:7] = 1
        transformed = transform(self.sample_subject)
        shapes = []
        for key in transformed:
            result_shape = transformed[key].spatial_shape
            shapes.append(result_shape)
        set_shapes = set(shapes)
        message = f'Images have different shapes: {set_shapes}'
        assert len(set_shapes) == 1, message
        for key in transformed:
            result_shape = transformed[key].spatial_shape
            assert target_shape == result_shape, f'Wrong shape for image: {key}'

    def test_mask_only_pad(self):
        self.mask_only((11, 22, 30))

    def test_mask_only_crop(self):
        self.mask_only((9, 18, 30))

    def test_center_mask(self):
        """The mask bounding box and the input image have the same center."""
        target_shape = (8, 22, 30)
        transform_center = tio.CropOrPad(target_shape)
        transform_mask = tio.CropOrPad(target_shape, mask_name='label')
        mask = self.sample_subject['label'].data
        mask *= 0
        mask[0, 4:6, 9:11, 14:16] = 1
        transformed_center = transform_center(self.sample_subject)
        transformed_mask = transform_mask(self.sample_subject)
        zipped = zip(transformed_center.values(), transformed_mask.values())
        for image_center, image_mask in zipped:
            self.assert_tensor_equal(image_center.data, image_mask.data, msg='Data is different after cropping')
            self.assert_tensor_equal(image_center.affine, image_mask.affine, msg='Physical position is different after cropping')

    def test_mask_corners(self):
        """The mask bounding box and the input image have the same center."""
        target_shape = (8, 22, 30)
        transform_center = tio.CropOrPad(target_shape)
        transform_mask = tio.CropOrPad(target_shape, mask_name='label')
        mask = self.sample_subject['label'].data
        mask *= 0
        mask[0, 0, 0, 0] = 1
        mask[0, -1, -1, -1] = 1
        transformed_center = transform_center(self.sample_subject)
        transformed_mask = transform_mask(self.sample_subject)
        zipped = zip(transformed_center.values(), transformed_mask.values())
        for image_center, image_mask in zipped:
            self.assert_tensor_equal(image_center.data, image_mask.data, msg='Data is different after cropping')
            self.assert_tensor_equal(image_center.affine, image_mask.affine, msg='Physical position is different after cropping')

    def test_2d(self):
        image = np.random.rand(1, 16, 16, 1)
        mask = np.zeros_like(image, dtype=bool)
        mask[0, 7, 0] = True
        subject = tio.Subject(image=tio.ScalarImage(tensor=image), mask=tio.LabelMap(tensor=mask))
        transform = tio.CropOrPad((12, 12, 1), mask_name='mask')
        transformed = transform(subject)
        assert transformed.shape == (1, 12, 12, 1)

    def test_no_target_no_mask(self):
        with pytest.raises(ValueError):
            tio.CropOrPad()

    def test_labels_but_no_mask(self):
        with pytest.raises(ValueError):
            tio.CropOrPad(target_shape=(3, 4, 5), labels=[2, 3])

    def test_no_target(self):
        crop_with_mask = tio.CropOrPad(mask_name='label')
        crop_with_mask(self.sample_subject)

    def test_persistent_bounds_params(self):
        shape = (1, 5, 5, 5)
        mask_a = np.zeros(shape)
        mask_a[0, 2, 2, 2] = 1
        mask_b = mask_a.copy()
        mask_b[0, 1:4, 1:4, 1:4] = 1
        tensor = np.ones(shape)
        image_a = tio.ScalarImage(tensor=tensor)
        mask_a = tio.LabelMap(tensor=mask_a)
        subject_a = tio.Subject(image=image_a, mask=mask_a)
        image_b = tio.ScalarImage(tensor=tensor)
        mask_b = tio.LabelMap(tensor=mask_b)
        subject_b = tio.Subject(image=image_b, mask=mask_b)
        crop = tio.CropOrPad(mask_name='mask')
        for _ in range(2):
            shape_a = crop(subject_a).image.shape
            shape_b = crop(subject_b).image.shape
            assert shape_a != shape_b

    def test_only_crop_pad_true(self):
        with pytest.raises(ValueError):
            tio.CropOrPad((1, 2, 3), only_crop=True, only_pad=True)

    def test_only_pad_true(self):
        target_shape = (9, 21, 30)
        orig_shape = self.sample_subject['t1'].spatial_shape
        expected_shape = tuple((t if t > o else o for o, t in zip(orig_shape, target_shape)))
        transform = tio.CropOrPad(target_shape, only_pad=True)
        transformed = transform(self.sample_subject)
        for key in transformed:
            result_shape = transformed[key].spatial_shape
            assert result_shape == expected_shape

    def test_only_crop_true(self):
        target_shape = (9, 21, 30)
        orig_shape = self.sample_subject['t1'].spatial_shape
        expected_shape = tuple((t if t < o else o for o, t in zip(orig_shape, target_shape)))
        transform = tio.CropOrPad(target_shape, only_crop=True)
        transformed = transform(self.sample_subject)
        for key in transformed:
            result_shape = transformed[key].spatial_shape
            assert result_shape == expected_shape

def test_no_changes(self):
    sample_t1 = self.sample_subject['t1']
    shape = sample_t1.spatial_shape
    transform = tio.CropOrPad(shape)
    transformed = transform(self.sample_subject)
    self.assert_tensor_equal(sample_t1.data, transformed['t1'].data)
    self.assert_tensor_equal(sample_t1.affine, transformed['t1'].affine)

def test_no_changes_mask(self):
    sample_t1 = self.sample_subject['t1']
    sample_mask = self.sample_subject['label'].data
    sample_mask *= 0
    shape = sample_t1.spatial_shape
    transform = tio.CropOrPad(shape, mask_name='label')
    with pytest.warns(RuntimeWarning):
        transformed = transform(self.sample_subject)
    for key in transformed:
        image = self.sample_subject[key]
        self.assert_tensor_equal(image.data, transformed[key].data)
        self.assert_tensor_equal(image.affine, transformed[key].affine)

def test_different_shape(self):
    shape = self.sample_subject['t1'].spatial_shape
    target_shape = (9, 21, 30)
    transform = tio.CropOrPad(target_shape)
    transformed = transform(self.sample_subject)
    for key in transformed:
        result_shape = transformed[key].spatial_shape
        self.assertNotEqual(shape, result_shape)

def test_shape_right(self):
    target_shape = (9, 21, 30)
    transform = tio.CropOrPad(target_shape)
    transformed = transform(self.sample_subject)
    for key in transformed:
        result_shape = transformed[key].spatial_shape
        assert target_shape == result_shape

def test_only_pad(self):
    target_shape = (11, 22, 30)
    transform = tio.CropOrPad(target_shape)
    transformed = transform(self.sample_subject)
    for key in transformed:
        result_shape = transformed[key].spatial_shape
        assert target_shape == result_shape

def test_only_crop(self):
    target_shape = (9, 18, 30)
    transform = tio.CropOrPad(target_shape)
    transformed = transform(self.sample_subject)
    for key in transformed:
        result_shape = transformed[key].spatial_shape
        assert target_shape == result_shape

def test_shape_negative(self):
    with pytest.raises(ValueError):
        tio.CropOrPad(-1)

def test_shape_float(self):
    with pytest.raises(ValueError):
        tio.CropOrPad(2.5)

def test_shape_string(self):
    with pytest.raises(ValueError):
        tio.CropOrPad('')

def test_shape_one(self):
    transform = tio.CropOrPad(1)
    transformed = transform(self.sample_subject)
    for key in transformed:
        result_shape = transformed[key].spatial_shape
        assert result_shape == (1, 1, 1)

def test_wrong_mask_name(self):
    cop = tio.CropOrPad(1, mask_name='wrong')
    with pytest.warns(RuntimeWarning):
        cop(self.sample_subject)

def test_empty_mask(self):
    target_shape = (8, 22, 30)
    transform = tio.CropOrPad(target_shape, mask_name='label')
    mask = self.sample_subject['label'].data
    mask *= 0
    with pytest.warns(RuntimeWarning):
        transform(self.sample_subject)

def mask_only(self, target_shape):
    transform = tio.CropOrPad(target_shape, mask_name='label')
    mask = self.sample_subject['label'].data
    mask *= 0
    mask[0, 4:6, 5:8, 3:7] = 1
    transformed = transform(self.sample_subject)
    shapes = []
    for key in transformed:
        result_shape = transformed[key].spatial_shape
        shapes.append(result_shape)
    set_shapes = set(shapes)
    message = f'Images have different shapes: {set_shapes}'
    assert len(set_shapes) == 1, message
    for key in transformed:
        result_shape = transformed[key].spatial_shape
        assert target_shape == result_shape, f'Wrong shape for image: {key}'

def test_center_mask(self):
    """The mask bounding box and the input image have the same center."""
    target_shape = (8, 22, 30)
    transform_center = tio.CropOrPad(target_shape)
    transform_mask = tio.CropOrPad(target_shape, mask_name='label')
    mask = self.sample_subject['label'].data
    mask *= 0
    mask[0, 4:6, 9:11, 14:16] = 1
    transformed_center = transform_center(self.sample_subject)
    transformed_mask = transform_mask(self.sample_subject)
    zipped = zip(transformed_center.values(), transformed_mask.values())
    for image_center, image_mask in zipped:
        self.assert_tensor_equal(image_center.data, image_mask.data, msg='Data is different after cropping')
        self.assert_tensor_equal(image_center.affine, image_mask.affine, msg='Physical position is different after cropping')

def test_mask_corners(self):
    """The mask bounding box and the input image have the same center."""
    target_shape = (8, 22, 30)
    transform_center = tio.CropOrPad(target_shape)
    transform_mask = tio.CropOrPad(target_shape, mask_name='label')
    mask = self.sample_subject['label'].data
    mask *= 0
    mask[0, 0, 0, 0] = 1
    mask[0, -1, -1, -1] = 1
    transformed_center = transform_center(self.sample_subject)
    transformed_mask = transform_mask(self.sample_subject)
    zipped = zip(transformed_center.values(), transformed_mask.values())
    for image_center, image_mask in zipped:
        self.assert_tensor_equal(image_center.data, image_mask.data, msg='Data is different after cropping')
        self.assert_tensor_equal(image_center.affine, image_mask.affine, msg='Physical position is different after cropping')

def test_no_target_no_mask(self):
    with pytest.raises(ValueError):
        tio.CropOrPad()

def test_labels_but_no_mask(self):
    with pytest.raises(ValueError):
        tio.CropOrPad(target_shape=(3, 4, 5), labels=[2, 3])

def test_no_target(self):
    crop_with_mask = tio.CropOrPad(mask_name='label')
    crop_with_mask(self.sample_subject)

def test_only_crop_pad_true(self):
    with pytest.raises(ValueError):
        tio.CropOrPad((1, 2, 3), only_crop=True, only_pad=True)

def test_only_pad_true(self):
    target_shape = (9, 21, 30)
    orig_shape = self.sample_subject['t1'].spatial_shape
    expected_shape = tuple((t if t > o else o for o, t in zip(orig_shape, target_shape)))
    transform = tio.CropOrPad(target_shape, only_pad=True)
    transformed = transform(self.sample_subject)
    for key in transformed:
        result_shape = transformed[key].spatial_shape
        assert result_shape == expected_shape

def test_only_crop_true(self):
    target_shape = (9, 21, 30)
    orig_shape = self.sample_subject['t1'].spatial_shape
    expected_shape = tuple((t if t < o else o for o, t in zip(orig_shape, target_shape)))
    transform = tio.CropOrPad(target_shape, only_crop=True)
    transformed = transform(self.sample_subject)
    for key in transformed:
        result_shape = transformed[key].spatial_shape
        assert result_shape == expected_shape

class TestResample(TorchioTestCase):
    """Tests for `Resample`."""

    def test_spacing(self):
        spacing = 2
        transform = tio.Resample(spacing)
        transformed = transform(self.sample_subject)
        for image in transformed.get_images(intensity_only=False):
            assert image.spacing == 3 * (spacing,)

    def test_reference_name(self):
        subject = self.get_inconsistent_shape_subject()
        reference_name = 't1'
        transform = tio.Resample(reference_name)
        transformed = transform(subject)
        reference_image = subject[reference_name]
        for image in transformed.get_images(intensity_only=False):
            assert reference_image.shape == image.shape
            self.assert_tensor_almost_equal(reference_image.affine, image.affine)

    def test_affine(self):
        spacing = 1
        affine_name = 'pre_affine'
        transform = tio.Resample(spacing, pre_affine_name=affine_name)
        transformed = transform(self.sample_subject)
        for image in transformed.values():
            if affine_name in image:
                target_affine = np.eye(4)
                target_affine[:3, 3] = (10, 0, -0.1)
                self.assert_tensor_almost_equal(image.affine, target_affine)
            else:
                self.assert_tensor_equal(image.affine, np.eye(4))

    def test_missing_affine(self):
        transform = tio.Resample(1, pre_affine_name='missing')
        with pytest.raises(ValueError):
            transform(self.sample_subject)

    def test_reference_path(self):
        reference_image, reference_path = self.get_reference_image_and_path()
        transform = tio.Resample(reference_path)
        transformed = transform(self.sample_subject)
        for image in transformed.values():
            assert reference_image.shape == image.shape
            self.assert_tensor_almost_equal(reference_image.affine, image.affine)

    def test_wrong_spacing_length(self):
        with pytest.raises(RuntimeError):
            tio.Resample((1, 2))(self.sample_subject)

    def test_wrong_spacing_value(self):
        with pytest.raises(ValueError):
            tio.Resample(0)(self.sample_subject)

    def test_wrong_target_type(self):
        with pytest.raises(RuntimeError):
            tio.Resample(None)(self.sample_subject)

    def test_missing_reference(self):
        transform = tio.Resample('missing')
        with pytest.raises(ValueError):
            transform(self.sample_subject)

    def test_2d(self):
        """Check that image is still 2D after resampling."""
        image = tio.ScalarImage(tensor=torch.rand(1, 2, 3, 1))
        transform = tio.Resample(0.5)
        shape = transform(image).shape
        assert shape == (1, 4, 6, 1)

    def test_input_list(self):
        tio.Resample([1, 2, 3])(self.sample_subject)

    def test_input_array(self):
        resample = tio.Resample(np.asarray([1, 2, 3]))
        resample(self.sample_subject)

    def test_image_target(self):
        tio.Resample(self.sample_subject.t1)(self.sample_subject)

    def test_bad_affine(self):
        shape = (1, 2, 3)
        affine = np.eye(3)
        target = (shape, affine)
        transform = tio.Resample(target)
        with pytest.raises(RuntimeError):
            transform(self.sample_subject)

    def test_resample_flip_consistent(self):
        image = torch.rand(1, 10, 10, 10)
        resample = tio.Resample(1.35)
        flip = tio.Flip(0)
        flipped_and_resampled = resample(flip(image))
        resampled_and_flipped = flip(resample(image))
        self.assert_tensor_almost_equal(flipped_and_resampled.data, resampled_and_flipped.data)

def test_reference_name(self):
    subject = self.get_inconsistent_shape_subject()
    reference_name = 't1'
    transform = tio.Resample(reference_name)
    transformed = transform(subject)
    reference_image = subject[reference_name]
    for image in transformed.get_images(intensity_only=False):
        assert reference_image.shape == image.shape
        self.assert_tensor_almost_equal(reference_image.affine, image.affine)

def test_reference_path(self):
    reference_image, reference_path = self.get_reference_image_and_path()
    transform = tio.Resample(reference_path)
    transformed = transform(self.sample_subject)
    for image in transformed.values():
        assert reference_image.shape == image.shape
        self.assert_tensor_almost_equal(reference_image.affine, image.affine)

