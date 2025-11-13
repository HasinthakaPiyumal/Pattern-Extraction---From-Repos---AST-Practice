# Cluster 2

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

def get_images(self, intensity_only=True, include: Sequence[str] | None=None, exclude: Sequence[str] | None=None) -> list[Image]:
    images_dict = self.get_images_dict(intensity_only=intensity_only, include=include, exclude=exclude)
    return list(images_dict.values())

def _read_itk_matrix(path: TypePath) -> torch.Tensor:
    """Read an affine transform in ITK's .tfm format."""
    transform = sitk.ReadTransform(str(path))
    parameters = transform.GetParameters()
    rotation_parameters = parameters[:9]
    rotation_matrix = np.array(rotation_parameters).reshape(3, 3)
    translation_parameters = parameters[9:]
    translation_vector = np.array(translation_parameters).reshape(3, 1)
    matrix = np.hstack([rotation_matrix, translation_vector])
    homogeneous_matrix_lps = np.vstack([matrix, [0, 0, 0, 1]])
    homogeneous_matrix_ras = _from_itk_convention(homogeneous_matrix_lps)
    return torch.as_tensor(homogeneous_matrix_ras)

def _matrix_to_itk_transform(matrix: TypeData, dimensions: int=3) -> sitk.AffineTransform:
    matrix = _to_itk_convention(matrix)
    rotation = matrix[:dimensions, :dimensions].ravel().tolist()
    translation = matrix[:dimensions, 3].tolist()
    transform = sitk.AffineTransform(rotation, translation)
    return transform

def get_rotation_and_spacing_from_affine(affine: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    rotation_zoom = affine[:3, :3]
    spacing = np.sqrt(np.sum(rotation_zoom * rotation_zoom, axis=0))
    rotation = rotation_zoom / spacing
    return (rotation, spacing)

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

@property
def bounds(self) -> np.ndarray:
    """Position of centers of voxels in smallest and largest indices."""
    ini = (0, 0, 0)
    fin = np.array(self.spatial_shape) - 1
    point_ini = apply_affine(self.affine, ini)
    point_fin = apply_affine(self.affine, fin)
    return np.array((point_ini, point_fin))

def get_bounds(self) -> TypeBounds:
    """Get minimum and maximum world coordinates occupied by the image."""
    first_index = 3 * (-0.5,)
    last_index = np.array(self.spatial_shape) - 0.5
    first_point = apply_affine(self.affine, first_index)
    last_point = apply_affine(self.affine, last_index)
    array = np.array((first_point, last_point))
    bounds_x, bounds_y, bounds_z = array.T.tolist()
    return (bounds_x, bounds_y, bounds_z)

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

def count_labels(self) -> dict[int, int]:
    """Get the number of voxels in each label."""
    values_list = self.data.flatten().tolist()
    counter = Counter(values_list)
    counts = {label: counter[label] for label in sorted(counter)}
    return counts

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

class ZonePlate(Subject):
    """Synthetic data generated from a zone plate.

    The zone plate is a circular diffraction grating that produces concentric
    rings of light and dark bands. This dataset is useful for testing image
    processing algorithms, particularly those related to frequency analysis and
    interpolation.

    See equation 10.63 in `Practical Handbook on Image Processing for
    Scientific Applications <https://www.routledge.com/Practical-Handbook-on-Image-Processing-for-Scientific-and-Technical-Applications/Jahne/p/book/9780849319006?srsltid=AfmBOoptrtzILIlMx9FYqvx6UrGbevfD66x2k242iprFdn_CfyOWXjjH>`_
    by Bernd Jähne.

    Args:
        size: The size of the generated image along all dimensions.
    """

    def __init__(self, size: int=501):
        if size < 3:
            raise ValueError('Size must be at least 3.')
        self.size = size
        image = self._generate_image(size)
        super().__init__(image=image)

    @staticmethod
    def _generate_image(size: int) -> ScalarImage:
        if size % 2 == 1:
            fin = (size - 1) // 2
            ini = -fin
        else:
            fin = size // 2
            ini = -fin + 1
        x = np.arange(ini, fin)
        y = np.arange(ini, fin)
        z = np.arange(ini, fin)
        X, Y, Z = np.meshgrid(x, y, z)
        r = np.sqrt(X ** 2 + Y ** 2 + Z ** 2)
        km = 0.8 * np.pi
        rm = ini
        w = rm / 10
        term1 = np.sin(km * r ** 2 / (2 * rm))
        term2 = 0.5 * np.tanh((rm - r) / w) + 0.5
        g = term1 * term2
        affine = np.eye(4)
        origin = np.array([ini, ini, ini])
        affine[:3, 3] = origin
        return ScalarImage(tensor=g[np.newaxis], affine=affine)

@staticmethod
def _generate_image(size: int) -> ScalarImage:
    if size % 2 == 1:
        fin = (size - 1) // 2
        ini = -fin
    else:
        fin = size // 2
        ini = -fin + 1
    x = np.arange(ini, fin)
    y = np.arange(ini, fin)
    z = np.arange(ini, fin)
    X, Y, Z = np.meshgrid(x, y, z)
    r = np.sqrt(X ** 2 + Y ** 2 + Z ** 2)
    km = 0.8 * np.pi
    rm = ini
    w = rm / 10
    term1 = np.sin(km * r ** 2 / (2 * rm))
    term2 = 0.5 * np.tanh((rm - r) / w) + 0.5
    g = term1 * term2
    affine = np.eye(4)
    origin = np.array([ini, ini, ini])
    affine[:3, 3] = origin
    return ScalarImage(tensor=g[np.newaxis], affine=affine)

class RSNACervicalSpineFracture(SubjectsDataset):
    """RSNA 2022 Cervical Spine Fracture Detection dataset.

    This is a helper class for the dataset used in the
    `RSNA 2022 Cervical Spine Fracture Detection`_ hosted on
    `kaggle <https://www.kaggle.com/>`_. The dataset must be downloaded before
    instantiating this class.

    .. _RSNA 2022 Cervical Spine Fracture Detection: https://www.kaggle.com/competitions/rsna-2022-cervical-spine-fracture-detection/overview/evaluation
    """
    UID = 'StudyInstanceUID'

    def __init__(self, root_dir: TypePath, add_segmentations: bool=False, add_bounding_boxes: bool=False, **kwargs):
        self.root_dir = normalize_path(root_dir)
        subjects = self._get_subjects(add_segmentations, add_bounding_boxes)
        super().__init__(subjects, **kwargs)

    @staticmethod
    def _get_image_dirs_dict(images_dir: Path) -> dict[str, Path]:
        dirs_dict = {}
        for dicom_dir in sorted(images_dir.iterdir()):
            dirs_dict[dicom_dir.name] = dicom_dir
        return dirs_dict

    @staticmethod
    def _get_segs_paths_dict(segs_dir: Path) -> dict[str, Path]:
        paths_dict = {}
        for image_path in sorted(segs_dir.iterdir()):
            key = image_path.name.replace('.gz', '').replace('.nii', '')
            paths_dict[key] = image_path
        return paths_dict

    def _get_subjects(self, add_segmentations: bool, add_bounding_boxes: bool) -> list[Subject]:
        subjects = []
        pd = get_pandas()
        from tqdm.auto import tqdm
        split_name = 'train'
        images_dirname = f'{split_name}_images'
        images_dir = self.root_dir / images_dirname
        image_dirs_dict = self._get_image_dirs_dict(images_dir)
        segmentations_dir = self.root_dir / 'segmentations'
        seg_paths_dict = self._get_segs_paths_dict(segmentations_dir)
        bboxes_path = self.root_dir / 'train_bounding_boxes.csv'
        bounding_boxes_df = pd.read_csv(bboxes_path)
        grouped_boxes = bounding_boxes_df.groupby(self.UID)
        df = pd.read_csv(self.root_dir / f'{split_name}.csv')
        for _, row in tqdm(list(df.iterrows())):
            uid = row[self.UID]
            image_dir = image_dirs_dict[uid]
            seg_path = None
            if add_segmentations:
                seg_path = seg_paths_dict.get(uid, None)
            boxes = []
            if add_bounding_boxes:
                try:
                    boxes_df = grouped_boxes.get_group(uid)
                    boxes = [dict(row) for _, row in boxes_df.iterrows()]
                except KeyError:
                    pass
            subject = self._get_subject(dict(row), image_dir, seg_path, boxes)
            subjects.append(subject)
        return subjects

    @staticmethod
    def _filter_list(iterable: list[Path], target: str):

        def _filter(path: Path):
            if path.is_dir():
                return target == path.name
            else:
                name = path.name.replace('.gz', '').replace('.nii', '')
                return target == name
        found = list(filter(_filter, iterable))
        if found:
            assert len(found) == 1
            result = found[0]
        else:
            result = None
        return result

    def _get_subject(self, csv_row_dict: dict[str, str | int], image_dir: Path, seg_path: Path | None, boxes: TypeBoxes) -> Subject:
        subject_dict: dict[str, Any] = {}
        subject_dict.update(csv_row_dict)
        subject_dict['ct'] = ScalarImage(image_dir)
        if seg_path is not None:
            subject_dict['seg'] = LabelMap(seg_path)
        if boxes:
            subject_dict['boxes'] = boxes
        return Subject(**subject_dict)

@staticmethod
def _get_image_dirs_dict(images_dir: Path) -> dict[str, Path]:
    dirs_dict = {}
    for dicom_dir in sorted(images_dir.iterdir()):
        dirs_dict[dicom_dir.name] = dicom_dir
    return dirs_dict

@staticmethod
def _get_segs_paths_dict(segs_dir: Path) -> dict[str, Path]:
    paths_dict = {}
    for image_path in sorted(segs_dir.iterdir()):
        key = image_path.name.replace('.gz', '').replace('.nii', '')
        paths_dict[key] = image_path
    return paths_dict

@staticmethod
def _filter_list(iterable: list[Path], target: str):

    def _filter(path: Path):
        if path.is_dir():
            return target == path.name
        else:
            name = path.name.replace('.gz', '').replace('.nii', '')
            return target == name
    found = list(filter(_filter, iterable))
    if found:
        assert len(found) == 1
        result = found[0]
    else:
        result = None
    return result

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

class OneOf(RandomTransform):
    """Apply only one of the given transforms.

    Args:
        transforms: Dictionary with instances of
            :class:`~torchio.transforms.Transform` as keys and
            probabilities as values. Probabilities are normalized so they sum
            to one. If a sequence is given, the same probability will be
            assigned to each transform.
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.

    Example:
        >>> import torchio as tio
        >>> colin = tio.datasets.Colin27()
        >>> transforms_dict = {
        ...     tio.RandomAffine(): 0.75,
        ...     tio.RandomElasticDeformation(): 0.25,
        ... }  # Using 3 and 1 as probabilities would have the same effect
        >>> transform = tio.OneOf(transforms_dict)
        >>> transformed = transform(colin)
    """

    def __init__(self, transforms: TypeTransformsDict, **kwargs):
        super().__init__(parse_input=False, **kwargs)
        self.transforms_dict = self._get_transforms_dict(transforms)

    def get_base_args(self) -> dict:
        init_args = super().get_base_args()
        if 'parse_input' in init_args:
            init_args.pop('parse_input')
        return init_args

    def apply_transform(self, subject: Subject) -> Subject:
        weights = torch.Tensor(list(self.transforms_dict.values()))
        index = torch.multinomial(weights, 1)
        transforms = list(self.transforms_dict.keys())
        transform = transforms[index]
        transformed = transform(subject)
        return transformed

    def _get_transforms_dict(self, transforms: TypeTransformsDict) -> dict[Transform, float]:
        if isinstance(transforms, dict):
            transforms_dict = dict(transforms)
            self._normalize_probabilities(transforms_dict)
        else:
            try:
                p = 1 / len(transforms)
            except TypeError as e:
                message = f'Transforms argument must be a dictionary or a sequence, not {type(transforms)}'
                raise ValueError(message) from e
            transforms_dict = {transform: p for transform in transforms}
        for transform in transforms_dict:
            if not isinstance(transform, Transform):
                message = f'All keys in transform_dict must be instances oftorchio.Transform, not "{type(transform)}"'
                raise ValueError(message)
        return transforms_dict

    @staticmethod
    def _normalize_probabilities(transforms_dict: dict[Transform, float]) -> None:
        probabilities = np.array(list(transforms_dict.values()), dtype=float)
        if np.any(probabilities < 0):
            message = f'Probabilities must be greater or equal to zero, not "{probabilities}"'
            raise ValueError(message)
        if np.all(probabilities == 0):
            message = f'At least one probability must be greater than zero, but they are "{probabilities}"'
            raise ValueError(message)
        for transform, probability in transforms_dict.items():
            transforms_dict[transform] = probability / probabilities.sum()

def apply_transform(self, subject: Subject) -> Subject:
    weights = torch.Tensor(list(self.transforms_dict.values()))
    index = torch.multinomial(weights, 1)
    transforms = list(self.transforms_dict.keys())
    transform = transforms[index]
    transformed = transform(subject)
    return transformed

@staticmethod
def _normalize_probabilities(transforms_dict: dict[Transform, float]) -> None:
    probabilities = np.array(list(transforms_dict.values()), dtype=float)
    if np.any(probabilities < 0):
        message = f'Probabilities must be greater or equal to zero, not "{probabilities}"'
        raise ValueError(message)
    if np.all(probabilities == 0):
        message = f'At least one probability must be greater than zero, but they are "{probabilities}"'
        raise ValueError(message)
    for transform, probability in transforms_dict.items():
        transforms_dict[transform] = probability / probabilities.sum()

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

class ElasticDeformation(SpatialTransform):
    """Apply dense elastic deformation.

    Args:
        control_points:
        max_displacement:
        image_interpolation: See :ref:`Interpolation`.
        label_interpolation: See :ref:`Interpolation`.
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.
    """

    def __init__(self, control_points: np.ndarray, max_displacement: TypeTripletFloat, image_interpolation: str='linear', label_interpolation: str='nearest', **kwargs):
        super().__init__(**kwargs)
        self.control_points = control_points
        self.max_displacement = max_displacement
        self.image_interpolation = self.parse_interpolation(image_interpolation)
        self.label_interpolation = self.parse_interpolation(label_interpolation)
        self.invert_transform = False
        self.args_names = ['control_points', 'image_interpolation', 'label_interpolation', 'max_displacement']

    def get_bspline_transform(self, image: sitk.Image) -> sitk.BSplineTransform:
        control_points = self.control_points.copy()
        if self.invert_transform:
            control_points *= -1
        is_2d = image.GetSize()[2] == 1
        if is_2d:
            control_points[..., -1] = 0
        num_control_points = control_points.shape[:-1]
        mesh_shape = [n - SPLINE_ORDER for n in num_control_points]
        bspline_transform = sitk.BSplineTransformInitializer(image, mesh_shape)
        parameters = control_points.flatten(order='F').tolist()
        bspline_transform.SetParameters(parameters)
        return bspline_transform

    @staticmethod
    def parse_free_form_transform(transform: sitk.BSplineTransform, max_displacement: TypeTripletFloat) -> None:
        """Issue a warning is possible folding is detected."""
        coefficient_images = transform.GetCoefficientImages()
        grid_spacing = coefficient_images[0].GetSpacing()
        conflicts = np.array(max_displacement) > np.array(grid_spacing) / 2
        if np.any(conflicts):
            where, = np.where(conflicts)
            message = f'The maximum displacement is larger than the coarse grid spacing for dimensions: {where.tolist()}, so folding may occur. Choose fewer control points or a smaller maximum displacement'
            warnings.warn(message, RuntimeWarning, stacklevel=2)

    def apply_transform(self, subject: Subject) -> Subject:
        no_displacement = not any(self.max_displacement)
        if no_displacement:
            return subject
        subject.check_consistent_spatial_shape()
        for image in self.get_images(subject):
            if not isinstance(image, ScalarImage):
                interpolation = self.label_interpolation
            else:
                interpolation = self.image_interpolation
            transformed = self.apply_bspline_transform(image.data, image.affine, interpolation)
            image.set_data(transformed)
        return subject

    def apply_bspline_transform(self, tensor: torch.Tensor, affine: np.ndarray, interpolation: str) -> torch.Tensor:
        assert tensor.dim() == 4
        results = []
        for component in tensor:
            image = nib_to_sitk(component[np.newaxis], affine, force_3d=True)
            floating = reference = image
            bspline_transform = self.get_bspline_transform(image)
            self.parse_free_form_transform(bspline_transform, self.max_displacement)
            interpolator = self.get_sitk_interpolator(interpolation)
            resampler = sitk.ResampleImageFilter()
            resampler.SetReferenceImage(reference)
            resampler.SetTransform(bspline_transform)
            resampler.SetInterpolator(interpolator)
            resampler.SetDefaultPixelValue(component.min().item())
            resampler.SetOutputPixelType(sitk.sitkFloat32)
            resampled = resampler.Execute(floating)
            result, _ = self.sitk_to_nib(resampled)
            results.append(torch.as_tensor(result))
        tensor = torch.cat(results)
        return tensor

def get_bspline_transform(self, image: sitk.Image) -> sitk.BSplineTransform:
    control_points = self.control_points.copy()
    if self.invert_transform:
        control_points *= -1
    is_2d = image.GetSize()[2] == 1
    if is_2d:
        control_points[..., -1] = 0
    num_control_points = control_points.shape[:-1]
    mesh_shape = [n - SPLINE_ORDER for n in num_control_points]
    bspline_transform = sitk.BSplineTransformInitializer(image, mesh_shape)
    parameters = control_points.flatten(order='F').tolist()
    bspline_transform.SetParameters(parameters)
    return bspline_transform

@staticmethod
def parse_free_form_transform(transform: sitk.BSplineTransform, max_displacement: TypeTripletFloat) -> None:
    """Issue a warning is possible folding is detected."""
    coefficient_images = transform.GetCoefficientImages()
    grid_spacing = coefficient_images[0].GetSpacing()
    conflicts = np.array(max_displacement) > np.array(grid_spacing) / 2
    if np.any(conflicts):
        where, = np.where(conflicts)
        message = f'The maximum displacement is larger than the coarse grid spacing for dimensions: {where.tolist()}, so folding may occur. Choose fewer control points or a smaller maximum displacement'
        warnings.warn(message, RuntimeWarning, stacklevel=2)

class RandomFlip(RandomTransform, SpatialTransform):
    """Reverse the order of elements in an image along the given axes.

    Args:
        axes: Index or tuple of indices of the spatial dimensions along which
            the image might be flipped. If they are integers, they must be in
            ``(0, 1, 2)``. Anatomical labels may also be used, such as
            ``'Left'``, ``'Right'``, ``'Anterior'``, ``'Posterior'``,
            ``'Inferior'``, ``'Superior'``, ``'Height'`` and ``'Width'``,
            ``'AP'`` (antero-posterior), ``'lr'`` (lateral), ``'w'`` (width) or
            ``'i'`` (inferior). Only the first letter of the string will be
            used. If the image is 2D, ``'Height'`` and ``'Width'`` may be
            used.
        flip_probability: Probability that the image will be flipped. This is
            computed on a per-axis basis.
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.

    Example:
        >>> import torchio as tio
        >>> fpg = tio.datasets.FPG()
        >>> flip = tio.RandomFlip(axes=('LR',))  # flip along lateral axis only

    .. tip:: It is handy to specify the axes as anatomical labels when the
        image orientation is not known.
    """

    def __init__(self, axes: Union[int, tuple[int, ...]]=0, flip_probability: float=0.5, **kwargs):
        super().__init__(**kwargs)
        self.axes = _parse_axes(axes)
        self.flip_probability = self.parse_probability(flip_probability)

    def apply_transform(self, subject: Subject) -> Subject:
        potential_axes = _ensure_axes_indices(subject, self.axes)
        axes_to_flip_hot = self.get_params(self.flip_probability)
        for i in range(3):
            if i not in potential_axes:
                axes_to_flip_hot[i] = False
        axes, = np.where(axes_to_flip_hot)
        axes_list = axes.tolist()
        if not axes_list:
            return subject
        arguments = {'axes': axes_list}
        transform = Flip(**self.add_base_args(arguments))
        transformed = transform(subject)
        assert isinstance(transformed, Subject)
        return transformed

    @staticmethod
    def get_params(probability: float) -> list[bool]:
        return (probability > torch.rand(3)).tolist()

@staticmethod
def get_params(probability: float) -> list[bool]:
    return (probability > torch.rand(3)).tolist()

def _ensure_axes_indices(subject, axes):
    if any((isinstance(n, str) for n in axes)):
        subject.check_consistent_orientation()
        image = subject.get_first_image()
        axes = sorted((3 + image.axis_name_to_index(n) for n in axes))
    return axes

def _swap(tensor: torch.Tensor, patch_size: TypeTuple, locations: list[tuple[np.ndarray, np.ndarray]]) -> torch.Tensor:
    tensor = tensor.clone()
    patch_size_array = np.array(patch_size)
    for first_ini, second_ini in locations:
        first_fin = first_ini + patch_size_array
        second_fin = second_ini + patch_size_array
        first_patch = _crop(tensor, first_ini, first_fin)
        second_patch = _crop(tensor, second_ini, second_fin).clone()
        _insert(tensor, first_patch, second_ini)
        _insert(tensor, second_patch, first_ini)
    return tensor

def _insert(tensor: TensorArray, patch: TensorArray, index_ini: np.ndarray) -> None:
    index_fin = index_ini + np.array(patch.shape[-3:])
    i_ini, j_ini, k_ini = index_ini
    i_fin, j_fin, k_fin = index_fin
    tensor[:, i_ini:i_fin, j_ini:j_fin, k_ini:k_fin] = patch

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

@staticmethod
def sort_spectra(spectra: list[torch.Tensor], times: np.ndarray):
    """Use original spectrum to fill the center of k-space."""
    num_spectra = len(spectra)
    if np.any(times > 0.5):
        index = np.where(times > 0.5)[0].min()
    else:
        index = num_spectra - 1
    spectra[0], spectra[index] = (spectra[index], spectra[0])

class Resample(SpatialTransform):
    """Resample image to a different physical space.

    This is a powerful transform that can be used to change the image shape
    or spatial metadata, or to apply a spatial transformation.

    Args:
        target: Argument to define the output space. Can be one of:

            - Output spacing :math:`(s_w, s_h, s_d)`, in mm. If only one value
              :math:`s` is specified, then :math:`s_w = s_h = s_d = s`.

            - Path to an image that will be used as reference.

            - Instance of :class:`~torchio.Image`.

            - Name of an image key in the subject.

            - Tuple ``(spatial_shape, affine)`` defining the output space.

        pre_affine_name: Name of the *image key* (not subject key) storing an
            affine matrix that will be applied to the image header before
            resampling. If ``None``, the image is resampled with an identity
            transform. See usage in the example below.
        image_interpolation: See :ref:`Interpolation`.
        label_interpolation: See :ref:`Interpolation`.
        scalars_only: Apply only to instances of :class:`~torchio.ScalarImage`.
            Used internally by :class:`~torchio.transforms.RandomAnisotropy`.
        antialias: If ``True``, apply Gaussian smoothing before
            downsampling along any dimension that will be downsampled. For example,
            if the input image has spacing (0.5, 0.5, 4) and the target
            spacing is (1, 1, 1), the image will be smoothed along the first two
            dimensions before resampling. Label maps are not smoothed.
            The standard deviations of the Gaussian kernels are computed according to
            the method described in Cardoso et al.,
            `Scale factor point spread function matching: beyond aliasing in image
            resampling
            <https://link.springer.com/chapter/10.1007/978-3-319-24571-3_81>`_,
            MICCAI 2015.
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.

    Example:
        >>> import torch
        >>> import torchio as tio
        >>> transform = tio.Resample()                      # resample all images to 1mm isotropic
        >>> transform = tio.Resample(2)                     # resample all images to 2mm isotropic
        >>> transform = tio.Resample('t1')                  # resample all images to 't1' image space
        >>> # Example: using a precomputed transform to MNI space
        >>> ref_path = tio.datasets.Colin27().t1.path  # this image is in the MNI space, so we can use it as reference/target
        >>> affine_matrix = tio.io.read_matrix('transform_to_mni.txt')  # from a NiftyReg registration. Would also work with e.g. .tfm from SimpleITK
        >>> image = tio.ScalarImage(tensor=torch.rand(1, 256, 256, 180), to_mni=affine_matrix)  # 'to_mni' is an arbitrary name
        >>> transform = tio.Resample(colin.t1.path, pre_affine_name='to_mni')  # nearest neighbor interpolation is used for label maps
        >>> transformed = transform(image)  # "image" is now in the MNI space

    .. note::
        The ``antialias`` option is recommended when large (e.g. > 2×) downsampling
        factors are expected, particularly for offline (before training) preprocessing,
        when run times are not a concern.

    .. plot::

        import torchio as tio
        subject = tio.datasets.FPG()
        subject.remove_image('seg')
        resample = tio.Resample(8)
        t1_resampled = resample(subject.t1)
        subject.add_image(t1_resampled, 'Antialias off')
        resample = tio.Resample(8, antialias=True)
        t1_resampled_antialias = resample(subject.t1)
        subject.add_image(t1_resampled_antialias, 'Antialias on')
        subject.plot()
    """

    def __init__(self, target: TypeTarget=ONE_MILLIMITER_ISOTROPIC, image_interpolation: str='linear', label_interpolation: str='nearest', pre_affine_name: str | None=None, scalars_only: bool=False, antialias: bool=False, **kwargs):
        super().__init__(**kwargs)
        self.target = target
        self.image_interpolation = self.parse_interpolation(image_interpolation)
        self.label_interpolation = self.parse_interpolation(label_interpolation)
        self.pre_affine_name = pre_affine_name
        self.scalars_only = scalars_only
        self.antialias = antialias
        self.args_names = ['target', 'image_interpolation', 'label_interpolation', 'pre_affine_name', 'scalars_only', 'antialias']

    @staticmethod
    def _parse_spacing(spacing: TypeSpacing) -> tuple[float, float, float]:
        result: Iterable
        if isinstance(spacing, Iterable) and len(spacing) == 3:
            result = spacing
        elif isinstance(spacing, Number):
            result = 3 * (spacing,)
        else:
            message = f'Target must be a string, a positive number or a sequence of positive numbers, not {type(spacing)}'
            raise ValueError(message)
        if np.any(np.array(spacing) <= 0):
            message = f'Spacing must be strictly positive, not "{spacing}"'
            raise ValueError(message)
        return result

    @staticmethod
    def check_affine(affine_name: str, image: Image):
        if not isinstance(affine_name, str):
            message = f'Affine name argument must be a string, not {type(affine_name)}'
            raise TypeError(message)
        if affine_name in image:
            matrix = image[affine_name]
            if not isinstance(matrix, (np.ndarray, torch.Tensor)):
                message = f'The affine matrix must be a NumPy array or PyTorch tensor, not {type(matrix)}'
                raise TypeError(message)
            if matrix.shape != (4, 4):
                message = f'The affine matrix shape must be (4, 4), not {matrix.shape}'
                raise ValueError(message)

    @staticmethod
    def check_affine_key_presence(affine_name: str, subject: Subject):
        for image in subject.get_images(intensity_only=False):
            if affine_name in image:
                return
        message = f'An affine name was given ("{affine_name}"), but it was not found in any image in the subject'
        raise ValueError(message)

    def apply_transform(self, subject: Subject) -> Subject:
        use_pre_affine = self.pre_affine_name is not None
        if use_pre_affine:
            assert self.pre_affine_name is not None
            self.check_affine_key_presence(self.pre_affine_name, subject)
        for image in self.get_images(subject):
            if self.target is image:
                continue
            try:
                target_image = subject[self.target]
                if target_image is image:
                    continue
            except (KeyError, TypeError, RuntimeError):
                pass
            if not isinstance(image, ScalarImage):
                if self.scalars_only:
                    continue
                interpolation = self.label_interpolation
            else:
                interpolation = self.image_interpolation
            interpolator = self.get_sitk_interpolator(interpolation)
            if use_pre_affine and self.pre_affine_name in image:
                assert self.pre_affine_name is not None
                self.check_affine(self.pre_affine_name, image)
                matrix = image[self.pre_affine_name]
                if isinstance(matrix, torch.Tensor):
                    matrix = matrix.numpy()
                image.affine = matrix @ image.affine
            floating_sitk = image.as_sitk(force_3d=True)
            resampler = self._get_resampler(interpolator, floating_sitk, subject, self.target)
            if self.antialias and isinstance(image, ScalarImage):
                downsampling_factor = self._get_downsampling_factor(floating_sitk, resampler)
                sigmas = self._get_sigmas(downsampling_factor, floating_sitk.GetSpacing())
                floating_sitk = self._smooth(floating_sitk, sigmas)
            resampled = resampler.Execute(floating_sitk)
            array, affine = sitk_to_nib(resampled)
            image.set_data(torch.as_tensor(array))
            image.affine = affine
        return subject

    @staticmethod
    def _smooth(image: sitk.Image, sigmas: np.ndarray, epsilon: float=1e-09) -> sitk.Image:
        """Smooth the image with a Gaussian kernel.

        Args:
            image: Image to be smoothed.
            sigmas: Standard deviations of the Gaussian kernel for each
                dimension. If a value is NaN, no smoothing is applied in that
                dimension.
            epsilon: Small value to replace NaN values in sigmas, to avoid
                division-by-zero errors.
        """
        sigmas[np.isnan(sigmas)] = epsilon
        gaussian = sitk.SmoothingRecursiveGaussianImageFilter()
        gaussian.SetSigma(sigmas.tolist())
        smoothed = gaussian.Execute(image)
        return smoothed

    @staticmethod
    def _get_downsampling_factor(floating: sitk.Image, resampler: sitk.ResampleImageFilter) -> np.ndarray:
        """Get the downsampling factor for each dimension.

        The downsampling factor is the ratio between the output spacing and
        the input spacing. If the output spacing is smaller than the input
        spacing, the factor is set to NaN, meaning downsampling is not applied
        in that dimension.

        Args:
            floating: The input image to be resampled.
            resampler: The resampler that will be used to resample the image.
        """
        input_spacing = np.array(floating.GetSpacing())
        output_spacing = np.array(resampler.GetOutputSpacing())
        factors = output_spacing / input_spacing
        no_downsampling = factors <= 1
        factors[no_downsampling] = np.nan
        return factors

    def _get_resampler(self, interpolator: int, floating: sitk.Image, subject: Subject, target: TypeTarget) -> sitk.ResampleImageFilter:
        """Instantiate a SimpleITK resampler."""
        resampler = sitk.ResampleImageFilter()
        resampler.SetInterpolator(interpolator)
        self._set_resampler_reference(resampler, target, floating, subject)
        return resampler

    def _set_resampler_reference(self, resampler: sitk.ResampleImageFilter, target: TypeSpacing | TypePath | Image, floating_sitk, subject):
        if isinstance(target, (str, Path, Image)):
            if isinstance(target, Image):
                image = target
            elif Path(target).is_file():
                path = target
                image = ScalarImage(path)
            else:
                try:
                    image = subject[target]
                except KeyError as error:
                    message = f'Image name "{target}" not found in subject. If "{target}" is a path, it does not exist or permission has been denied'
                    raise ValueError(message) from error
            self._set_resampler_from_shape_affine(resampler, image.spatial_shape, image.affine)
        elif isinstance(target, Number):
            self._set_resampler_from_spacing(resampler, target, floating_sitk)
        elif isinstance(target, Iterable) and len(target) == 2:
            assert not isinstance(target, str)
            shape, affine = target
            if not (isinstance(shape, Sized) and len(shape) == 3):
                message = f'Target shape must be a sequence of three integers, but "{shape}" was passed'
                raise RuntimeError(message)
            if not affine.shape == (4, 4):
                message = f'Target affine must have shape (4, 4) but the following was passed:\n{shape}'
                raise RuntimeError(message)
            self._set_resampler_from_shape_affine(resampler, shape, affine)
        elif isinstance(target, Iterable) and len(target) == 3:
            self._set_resampler_from_spacing(resampler, target, floating_sitk)
        else:
            raise RuntimeError(f'Target not understood: "{target}"')

    def _set_resampler_from_shape_affine(self, resampler, shape, affine):
        origin, spacing, direction = get_sitk_metadata_from_ras_affine(affine)
        resampler.SetOutputDirection(direction)
        resampler.SetOutputOrigin(origin)
        resampler.SetOutputSpacing(spacing)
        resampler.SetSize(shape)

    def _set_resampler_from_spacing(self, resampler, target, floating_sitk):
        target_spacing = self._parse_spacing(target)
        reference_image = self.get_reference_image(floating_sitk, target_spacing)
        resampler.SetReferenceImage(reference_image)

    @staticmethod
    def get_reference_image(floating_sitk: sitk.Image, spacing: TypeTripletFloat) -> sitk.Image:
        old_spacing = np.array(floating_sitk.GetSpacing(), dtype=float)
        new_spacing = np.array(spacing, dtype=float)
        old_size = np.array(floating_sitk.GetSize())
        old_last_index = old_size - 1
        old_last_index_lps = np.array(floating_sitk.TransformIndexToPhysicalPoint(old_last_index.tolist()), dtype=float)
        old_origin_lps = np.array(floating_sitk.GetOrigin(), dtype=float)
        center_lps = (old_last_index_lps + old_origin_lps) / 2
        new_size = np.floor(old_size * old_spacing / new_spacing)
        new_size[old_size == 1] = 1
        direction = np.asarray(floating_sitk.GetDirection(), dtype=float).reshape(3, 3)
        half_extent = (new_size - 1) / 2 * new_spacing
        new_origin_lps = (center_lps - direction @ half_extent).tolist()
        reference = sitk.Image(new_size.astype(int).tolist(), floating_sitk.GetPixelID(), floating_sitk.GetNumberOfComponentsPerPixel())
        reference.SetDirection(floating_sitk.GetDirection())
        reference.SetSpacing(new_spacing.tolist())
        reference.SetOrigin(new_origin_lps)
        return reference

    @staticmethod
    def _get_sigmas(downsampling_factor: np.ndarray, spacing: np.ndarray) -> np.ndarray:
        """Compute optimal standard deviation for Gaussian kernel.

        From Cardoso et al., `Scale factor point spread function matching:
        beyond aliasing in image resampling
        <https://link.springer.com/chapter/10.1007/978-3-319-24571-3_81>`_,
        MICCAI 2015.

        Args:
            downsampling_factor: Array with the downsampling factor for each
                dimension.
            spacing: Array with the spacing of the input image in mm.
        """
        k = downsampling_factor
        variance = (k ** 2 - 1) * (2 * np.sqrt(2 * np.log(2))) ** (-2)
        sigma = spacing * np.sqrt(variance)
        return sigma

@staticmethod
def _smooth(image: sitk.Image, sigmas: np.ndarray, epsilon: float=1e-09) -> sitk.Image:
    """Smooth the image with a Gaussian kernel.

        Args:
            image: Image to be smoothed.
            sigmas: Standard deviations of the Gaussian kernel for each
                dimension. If a value is NaN, no smoothing is applied in that
                dimension.
            epsilon: Small value to replace NaN values in sigmas, to avoid
                division-by-zero errors.
        """
    sigmas[np.isnan(sigmas)] = epsilon
    gaussian = sitk.SmoothingRecursiveGaussianImageFilter()
    gaussian.SetSigma(sigmas.tolist())
    smoothed = gaussian.Execute(image)
    return smoothed

@staticmethod
def _get_sigmas(downsampling_factor: np.ndarray, spacing: np.ndarray) -> np.ndarray:
    """Compute optimal standard deviation for Gaussian kernel.

        From Cardoso et al., `Scale factor point spread function matching:
        beyond aliasing in image resampling
        <https://link.springer.com/chapter/10.1007/978-3-319-24571-3_81>`_,
        MICCAI 2015.

        Args:
            downsampling_factor: Array with the downsampling factor for each
                dimension.
            spacing: Array with the spacing of the input image in mm.
        """
    k = downsampling_factor
    variance = (k ** 2 - 1) * (2 * np.sqrt(2 * np.log(2))) ** (-2)
    sigma = spacing * np.sqrt(variance)
    return sigma

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

def _normalize(tensor: torch.Tensor, landmarks: np.ndarray, mask: np.ndarray | None, cutoff: tuple[float, float] | None=None, epsilon: float=1e-05) -> torch.Tensor:
    cutoff_ = DEFAULT_CUTOFF if cutoff is None else cutoff
    array = tensor.numpy()
    mapping = landmarks
    data = array
    shape = data.shape
    data = data.reshape(-1).astype(np.float32)
    if mask is None:
        mask = np.ones_like(data, bool)
    mask = mask.reshape(-1)
    range_to_use = [0, 1, 2, 4, 5, 6, 7, 8, 10, 11, 12]
    quantiles_cutoff = _standardize_cutoff(cutoff_)
    percentiles_cutoff = 100 * np.array(quantiles_cutoff)
    a, b = percentiles_cutoff
    percentiles = _get_percentiles((a, b))
    percentile_values = np.percentile(data[mask], percentiles)
    range_mapping = mapping[range_to_use]
    range_perc = percentile_values[range_to_use]
    diff_mapping = np.diff(range_mapping)
    diff_perc = np.diff(range_perc)
    diff_perc[diff_perc < epsilon] = np.inf
    affine_map = np.zeros([2, len(range_to_use) - 1])
    affine_map[0] = diff_mapping / diff_perc
    affine_map[1] = range_mapping[:-1] - affine_map[0] * range_perc[:-1]
    bin_id = np.digitize(data, range_perc[1:-1], right=False)
    lin_img = affine_map[0, bin_id]
    aff_img = affine_map[1, bin_id]
    new_img = lin_img * data + aff_img
    new_img = new_img.reshape(shape)
    new_img = new_img.astype(np.float32)
    new_img = torch.as_tensor(new_img)
    return new_img

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

@staticmethod
def get_tensor_with_labels(labels: Sequence) -> torch.Tensor:
    tensor = torch.as_tensor(list(labels))
    return tensor.repeat_interleave(2).reshape(1, 1, 1, -1)

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

def test_indexing_nonint(self):
    dset = tio.SubjectsDataset(self.subjects_list)
    dset[torch.tensor(0)]

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

def test_axis_name_2d(self):
    path = self.get_image_path('im2d', shape=(5, 6))
    image = tio.ScalarImage(path)
    height_idx = image.axis_name_to_index('t')
    width_idx = image.axis_name_to_index('l')
    assert image.height == image.shape[height_idx]
    assert image.width == image.shape[width_idx]

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

def test_default_value_label_map(self):
    a = torch.tensor([[1, 0, 0], [0, 1, 0], [0, 0, 1]]).reshape(1, 3, 3, 1)
    image = tio.LabelMap(tensor=a)
    aff = tio.RandomAffine(translation=(0, 1, 1), default_pad_value='otsu')
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

class TestMask(TorchioTestCase):

    def test_single_mask(self):
        negated_mask = self.sample_subject.label.data.logical_not()
        masked_voxel_indices = negated_mask.nonzero(as_tuple=True)
        transform = tio.Mask(masking_method='label')
        transformed = transform(self.sample_subject)
        assert (transformed.t1.data[masked_voxel_indices] == 0).all()

    def test_single_mask_nonzero_background(self):
        background_value = 314159
        negated_mask = self.sample_subject.label.data.logical_not()
        masked_voxel_indices = negated_mask.nonzero(as_tuple=True)
        transform = tio.Mask(masking_method='label', outside_value=background_value)
        transformed = transform(self.sample_subject)
        assert (transformed.t1.data[masked_voxel_indices] == background_value).all()

    def test_mask_specified_label(self):
        mask_label = [1]
        negated_mask = self.sample_subject.label.data.logical_not()
        masked_voxel_indices = negated_mask.nonzero(as_tuple=True)
        transform = tio.Mask(masking_method='label', labels=mask_label)
        transformed = transform(self.sample_subject)
        assert (transformed.t1.data[masked_voxel_indices] == 0).all()

    def test_mask_specified_label_small(self):

        def to_image(*numbers):
            return torch.as_tensor(numbers).reshape(1, 1, 1, len(numbers))
        image_tensor = to_image(1, 6, 7, 3, 0)
        label_tensor = to_image(0, 1, 2, 3, 4)
        mask_labels = [1, 2]
        subject = tio.Subject(image=tio.ScalarImage(tensor=image_tensor), label=tio.LabelMap(tensor=label_tensor))
        transform = tio.Mask(masking_method='label', labels=mask_labels)
        transformed = transform(subject)
        masked_list = transformed.image.data.flatten().tolist()
        assert masked_list == [0, 6, 7, 0, 0]

    def test_mask_example(self):
        subject = self.sample_subject
        negated_mask = subject.label.data.logical_not()
        masked_voxel_indices = negated_mask.nonzero(as_tuple=True)
        transform = tio.Mask(masking_method='label')
        transformed = transform(subject)
        assert (transformed.t1.data[masked_voxel_indices] == 0).all()

    def test_4d(self):
        image = tio.ScalarImage(tensor=torch.rand(3, 4, 5, 6))
        mask = tio.LabelMap(tensor=torch.ones(1, 4, 5, 6))
        subject = tio.Subject(image=image, mask_lm=mask)
        transform = tio.Mask(masking_method='mask_lm')
        with pytest.warns(RuntimeWarning, match='^Expanding.*'):
            masked = transform(subject)
        assert masked.image.shape == image.shape

def to_image(*numbers):
    return torch.as_tensor(numbers).reshape(1, 1, 1, len(numbers))

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

def test_persistent_in_min_max(self):
    img1 = torch.tensor([[[[0, 1]]]])
    img2 = torch.tensor([[[[0, 10]]]])
    rescale = tio.RescaleIntensity(out_min_max=(0, 1))
    assert rescale(img1).data.flatten().tolist() == [0, 1]
    assert rescale(img2).data.flatten().tolist() == [0, 1]
    rescale = tio.RescaleIntensity(out_min_max=(0, 1))
    assert rescale(img2).data.flatten().tolist() == [0, 1]
    assert rescale(img1).data.flatten().tolist() == [0, 1]

