# Cluster 6

def add_images_from_batch(subjects: list, tensor: torch.Tensor, class_=None, name='prediction') -> None:
    """Add images to subjects in a list, typically from a network prediction.

    The spatial metadata (affine matrices) will be extracted from one of the
    images of each subject.

    Args:
        subjects: List of instances of :class:`torchio.Subject` to which images
            will be added.
        tensor: PyTorch tensor of shape :math:`(B, C, W, H, D)`, where
            :math:`B` is the batch size.
        class_: Class used to instantiate the images,
            e.g., :class:`torchio.LabelMap`.
            If ``None``, :class:`torchio.ScalarImage` will be used.
        name: Name of the images added to the subjects.
    """
    if class_ is None:
        from . import ScalarImage
        class_ = ScalarImage
    for subject, data in zip(subjects, tensor):
        one_image = subject.get_first_image()
        kwargs = {'tensor': data, 'affine': one_image.affine}
        if 'filename' in one_image:
            kwargs['filename'] = one_image['filename']
        image = class_(**kwargs)
        subject.add_image(image, name)

class SubjectsLoader(DataLoader):

    def __init__(self, dataset: Dataset, collate_fn: Callable[[list[T]], Any] | None=None, **kwargs):
        if collate_fn is None:
            collate_fn = self._collate
        super().__init__(dataset=dataset, collate_fn=collate_fn, **kwargs)

    @staticmethod
    def _collate(subjects: list[Subject]) -> dict[str, Any]:
        first_subject = subjects[0]
        batch_dict = {}
        for key in first_subject.keys():
            collated_value = _stack([subject[key] for subject in subjects])
            batch_dict[key] = collated_value
        return batch_dict

@staticmethod
def _collate(subjects: list[Subject]) -> dict[str, Any]:
    first_subject = subjects[0]
    batch_dict = {}
    for key in first_subject.keys():
        collated_value = _stack([subject[key] for subject in subjects])
        batch_dict[key] = collated_value
    return batch_dict

def _stack(x):
    """Determine the type of the input and stack it accordingly.

    Args:
        x: List of elements to stack.
    Returns:
        Stacked elements, as either a torch.Tensor, np.ndarray, dict or list.
    """
    first_element = x[0]
    if isinstance(first_element, torch.Tensor):
        return torch.stack(x, dim=0)
    elif isinstance(first_element, np.ndarray):
        return np.stack(x, axis=0)
    elif isinstance(first_element, dict):
        collated_dict = {}
        for key in first_element.keys():
            collated_dict[key] = _stack([element[key] for element in x])
        return collated_dict
    else:
        return x

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

def is_2d(self):
    return all((i.is_2d() for i in self.get_images(intensity_only=False)))

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

def get_image(self, image_name: str) -> Image:
    """Get a single image by its name."""
    return self.get_images_dict(intensity_only=False)[image_name]

def get_first_image(self) -> Image:
    return self.get_images(intensity_only=False)[0]

def unload(self) -> None:
    """Unload images in subject."""
    for image in self.get_images(intensity_only=False):
        image.unload()

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

def __getitem__(self, item):
    if isinstance(item, (slice, int, tuple)):
        return self._crop_from_slices(item)
    if item in (DATA, AFFINE):
        if item not in self:
            self.load()
    return super().__getitem__(item)

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

@data.setter
@deprecated(version='0.18.16', reason=deprecation_message)
def data(self, tensor: TypeData):
    self.set_data(tensor)

def check_is_2d(self) -> None:
    if not self.is_2d():
        message = f'Image is not 2D. Spatial shape: {self.spatial_shape}'
        raise RuntimeError(message)

@property
def memory(self) -> float:
    """Number of Bytes that the tensor takes in the RAM."""
    return np.prod(self.shape) * self.itemsize

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

def get_probability_map_image(self, subject: Subject) -> Image:
    assert self.probability_map_name is not None
    if self.probability_map_name in subject:
        return subject[self.probability_map_name]
    else:
        message = f'Image "{self.probability_map_name}" not found in subject: {subject}'
        raise KeyError(message)

class CtRate(SubjectsDataset):
    """CT-RATE dataset.

    This class helps loading the `CT-RATE dataset
    <https://huggingface.co/datasets/ibrahimhamamci/CT-RATE>`_,
    which contains chest CT scans with associated radiology reports and
    abnormality labels.

    The dataset must have been downloaded previously.

    Args:
        root: Root directory where the dataset has been downloaded.
        split: Dataset split to use, either ``'train'`` or ``'validation'``.
        num_subjects: Optional limit on the number of subjects to load (useful for
            debugging). If ``None``, all subjects in the split are loaded.
        report_key: Key to use for storing radiology reports in the Subject metadata.
        sizes: List of image sizes (in-plane, in voxels) to include.
        load_fixed: If ``True``, load the files with fixed spatial metadata
            added in `this pull request
            <https://huggingface.co/datasets/ibrahimhamamci/CT-RATE/discussions/85>`_.
            Otherwise, load the original files with incorrect spatial metadata.
        verify_paths: If ``True``, verify that the paths to the images exist
            during instantiation of the dataset. This might be slow for large that are
            not stored locally.
        **kwargs: Additional arguments for SubjectsDataset.

    Examples:
        >>> from torchio.datasets import CtRate
        >>> dataset = CtRate('/path/to/CT-RATE', sizes=[512])
    """
    _REPO_ID = 'ibrahimhamamci/CT-RATE'
    _FILENAME_KEY = 'VolumeName'
    _SIZES = [512, 768, 1024]
    ABNORMALITIES = ['Medical material', 'Arterial wall calcification', 'Cardiomegaly', 'Pericardial effusion', 'Coronary artery wall calcification', 'Hiatal hernia', 'Lymphadenopathy', 'Emphysema', 'Atelectasis', 'Lung nodule', 'Lung opacity', 'Pulmonary fibrotic sequela', 'Pleural effusion', 'Mosaic attenuation pattern', 'Peribronchial thickening', 'Consolidation', 'Bronchiectasis', 'Interlobular septal thickening']
    REPORT_KEYS = ['ClinicalInformation_EN', 'Findings_EN', 'Impressions_EN', 'Technique_EN']

    def __init__(self, root: TypePath, split: TypeSplit='train', *, num_subjects: int | None=None, report_key: str='report', sizes: list[int] | None=None, load_fixed: bool=True, verify_paths: bool=False, **kwargs):
        self._root_dir = Path(root)
        self._num_subjects = num_subjects
        self._report_key = report_key
        self._sizes = self._SIZES if sizes is None else sizes
        self._split = self._parse_split(split)
        self.metadata = self._get_metadata()
        self._load_fixed = load_fixed
        self._verify_paths = verify_paths
        subjects_list = self._get_subjects_list(self.metadata)
        super().__init__(subjects_list, **kwargs)

    @staticmethod
    def _parse_split(split: str) -> str:
        """Normalize the split name.

        Converts 'validation' to 'valid' and validates that the split name
        is one of the allowed values.

        Args:
            split: The split name to parse ('train', 'valid', or 'validation').

        Returns:
            str: Normalized split name ('train' or 'valid').

        Raises:
            ValueError: If the split name is not one of the allowed values.
        """
        if split in ['valid', 'validation']:
            return 'valid'
        if split not in ['train', 'valid']:
            raise ValueError(f"Invalid split '{split}'. Use 'train' or 'valid'")
        return split

    def _get_csv(self, dirname: str, filename: str) -> pd.DataFrame:
        """Load a CSV file from the specified directory within the dataset.

        Args:
            dirname: Directory name within 'dataset/' where the CSV is located.
            filename: Name of the CSV file to load.
        """
        subfolder = Path(f'dataset/{dirname}')
        path = Path(self._root_dir, subfolder, filename)
        pd = get_pandas()
        table = pd.read_csv(path)
        return table

    def _get_csv_prefix(self, expand_validation: bool=True) -> str:
        """Get the prefix for CSV filenames based on the current split.

        Returns the appropriate prefix for CSV filenames based on the current split.
        For the validation split, can either return 'valid' or 'validation' depending
        on the expand_validation parameter.

        Args:
            expand_validation: If ``True`` and split is ``'valid'``, return
                ``'validation'``. Otherwise, return the split name as is.
        """
        if expand_validation and self._split == 'valid':
            prefix = 'validation'
        else:
            prefix = self._split
        return prefix

    def _get_metadata(self) -> pd.DataFrame:
        """Load and process the dataset metadata.

        Loads metadata from the appropriate CSV file, filters images by size,
        extracts subject, scan, and reconstruction IDs from filenames, and
        merges in reports and abnormality labels.
        """
        dirname = 'metadata'
        prefix = self._get_csv_prefix()
        filename = f'{prefix}_metadata.csv'
        metadata = self._get_csv(dirname, filename)
        rows_int = metadata['Rows'].astype(int)
        metadata = metadata[rows_int.isin(self._sizes)]
        index_columns = [MetadataIndexColumn.SUBJECT_ID.value, MetadataIndexColumn.SCAN_ID.value, MetadataIndexColumn.RECONSTRUCTION_ID.value]
        pattern = '\\w+_(\\d+)_(\\w+)_(\\d+)\\.nii\\.gz'
        metadata[index_columns] = metadata[self._FILENAME_KEY].str.extract(pattern)
        if self._num_subjects is not None:
            metadata = self._keep_n_subjects(metadata, self._num_subjects)
        metadata = self._merge(metadata, self._get_reports())
        metadata = self._merge(metadata, self._get_labels())
        metadata.set_index(index_columns, inplace=True)
        return metadata

    def _merge(self, base_df: pd.DataFrame, new_df: pd.DataFrame) -> pd.DataFrame:
        """Merge a new dataframe into the base dataframe using the filename as the key.

        This method performs a left join between ``base_df`` and ``new_df`` using the
        volume filename as the join key, ensuring that all records from ``base_df`` are
        preserved while matching data from ``new_df`` is added.

        Args:
            base_df: The primary dataframe to merge into.
            new_df: The dataframe containing additional data to be merged.

        Returns:
            pd.DataFrame: The merged dataframe with all rows from base_df and
            matching columns from new_df.
        """
        pd = get_pandas()
        return pd.merge(base_df, new_df, on=self._FILENAME_KEY, how='left')

    def _keep_n_subjects(self, metadata: pd.DataFrame, n: int) -> pd.DataFrame:
        """Limit the metadata to the first ``n`` subjects.

        Args:
            metadata: The complete metadata dataframe.
            n: Maximum number of subjects to keep.
        """
        unique_subjects = metadata['subject_id'].unique()
        selected_subjects = unique_subjects[:n]
        return metadata[metadata['subject_id'].isin(selected_subjects)]

    def _get_reports(self) -> pd.DataFrame:
        """Load the radiology reports associated with the CT scans.

        Retrieves the CSV file containing radiology reports for the current split
        (train or validation).
        """
        dirname = 'radiology_text_reports'
        prefix = self._get_csv_prefix()
        filename = f'{prefix}_reports.csv'
        return self._get_csv(dirname, filename)

    def _get_labels(self) -> pd.DataFrame:
        """Load the abnormality labels for the CT scans.

        Retrieves the CSV file containing predicted abnormality labels for the
        current split.
        """
        dirname = 'multi_abnormality_labels'
        prefix = self._get_csv_prefix(expand_validation=False)
        filename = f'{prefix}_predicted_labels.csv'
        return self._get_csv(dirname, filename)

    def _get_subjects_list(self, metadata: pd.DataFrame) -> list[Subject]:
        """Create a list of Subject instances from the metadata.

        Processes the metadata to create Subject objects, each containing one or more
        CT images. Processing is performed in parallel.

        Note:
            This method uses parallelization to improve performance when creating
            multiple Subject instances.
        """
        df_no_index = metadata.reset_index()
        num_subjects = df_no_index['subject_id'].nunique()
        iterable = df_no_index.groupby('subject_id')
        subjects = thread_map(self._get_subject, iterable, max_workers=multiprocessing.cpu_count(), total=num_subjects)
        return subjects

    def _get_subject(self, subject_id_and_metadata: tuple[str, pd.DataFrame]) -> Subject:
        """Create a Subject instance for a specific subject.

        Processes all images belonging to a single subject and creates a Subject
        object containing those images.

        Args:
            subject_id_and_metadata: A tuple containing the subject ID (string) and a
                DataFrame containing metadata for all images associated to that subject.
        """
        subject_id, subject_df = subject_id_and_metadata
        subject_dict: dict[str, str | ScalarImage] = {'subject_id': subject_id}
        for _, image_row in subject_df.iterrows():
            image = self._instantiate_image(image_row)
            scan_id = image_row['scan_id']
            reconstruction_id = image_row['reconstruction_id']
            image_key = f'scan_{scan_id}_reconstruction_{reconstruction_id}'
            subject_dict[image_key] = image
        return Subject(**subject_dict)

    def _instantiate_image(self, image_row: pd.Series) -> ScalarImage:
        """Create a ScalarImage object for a specific image.

        Processes a row from the metadata DataFrame to create a ScalarImage object,

        Args:
            image_row: A pandas Series representing a row from the metadata DataFrame,
                containing information about a single image.
        """
        image_dict = image_row.to_dict()
        filename = image_dict[self._FILENAME_KEY]
        relative_image_path = self._get_image_path(filename, load_fixed=self._load_fixed)
        image_path = self._root_dir / relative_image_path
        report_dict = self._extract_report_dict(image_dict)
        image_dict[self._report_key] = report_dict
        image = ScalarImage(image_path, verify_path=self._verify_paths, **image_dict)
        return image

    def _extract_report_dict(self, subject_dict: dict[str, str]) -> dict[str, str]:
        """Extract radiology report information from the subject dictionary.

        Extracts the English radiology report components (clinical information,
        findings, impressions, and technique) from the subject dictionary and
        removes these keys from the original dictionary.

        Args:
            subject_dict: Image metadata including report fields.

        Note:
            This method modifies the input subject_dict by removing the report keys.
        """
        report_dict = {}
        for key in self.REPORT_KEYS:
            report_dict[key] = subject_dict.pop(key)
        return report_dict

    @staticmethod
    def _get_image_path(filename: str, load_fixed: bool) -> Path:
        """Construct the relative path to an image file within the dataset structure.

        Parses the filename to determine the hierarchical directory structure
        where the image is stored in the CT-RATE dataset.

        Args:
            filename: The name of the image file (e.g., 'train_2_a_1.nii.gz').

        Returns:
            Path: The relative path to the image file within the dataset directory.

        Example:
            >>> path = CtRate._get_image_path('train_2_a_1.nii.gz')
            # Returns Path('dataset/train/train_2/train_2_a/train_2_a_1.nii.gz')
        """
        parts = filename.split('_')
        base_dir = 'dataset'
        split_dir = parts[0]
        if load_fixed:
            split_dir = f'{split_dir}_fixed'
        level1 = f'{parts[0]}_{parts[1]}'
        level2 = f'{level1}_{parts[2]}'
        return Path(base_dir, split_dir, level1, level2, filename)

def _keep_n_subjects(self, metadata: pd.DataFrame, n: int) -> pd.DataFrame:
    """Limit the metadata to the first ``n`` subjects.

        Args:
            metadata: The complete metadata dataframe.
            n: Maximum number of subjects to keep.
        """
    unique_subjects = metadata['subject_id'].unique()
    selected_subjects = unique_subjects[:n]
    return metadata[metadata['subject_id'].isin(selected_subjects)]

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

class DataParser:

    def __init__(self, data: TypeTransformInput, keys: Sequence[str] | None=None, label_keys: Sequence[str] | None=None):
        self.data = data
        self.keys = keys
        self.label_keys = label_keys
        self.default_image_name = 'default_image_name'
        self.is_tensor = False
        self.is_array = False
        self.is_dict = False
        self.is_image = False
        self.is_sitk = False
        self.is_nib = False

    def get_subject(self):
        if isinstance(self.data, nib.Nifti1Image):
            tensor = self.data.get_fdata(dtype=np.float32)
            if tensor.ndim == 3:
                tensor = tensor[np.newaxis]
            elif tensor.ndim == 5:
                tensor = tensor.transpose(3, 4, 0, 1, 2)
                tensor = tensor[0]
            data = ScalarImage(tensor=tensor, affine=self.data.affine)
            subject = self._get_subject_from_image(data)
            self.is_nib = True
        elif isinstance(self.data, (np.ndarray, torch.Tensor)):
            subject = self._parse_tensor(self.data)
            self.is_array = isinstance(self.data, np.ndarray)
            self.is_tensor = True
        elif isinstance(self.data, Image):
            subject = self._get_subject_from_image(self.data)
            self.is_image = True
        elif isinstance(self.data, Subject):
            subject = self.data
        elif isinstance(self.data, sitk.Image):
            subject = self._get_subject_from_sitk_image(self.data)
            self.is_sitk = True
        elif isinstance(self.data, dict):
            if self.keys is None:
                message = 'If the input is a dictionary, a value for "include" must be specified when instantiating the transform. See the docs for Transform: https://docs.torchio.org/transforms/transforms.html#torchio.transforms.Transform'
                raise RuntimeError(message)
            subject = self._get_subject_from_dict(self.data, self.keys, self.label_keys)
            self.is_dict = True
        else:
            raise ValueError(f'Input type not recognized: {type(self.data)}')
        assert isinstance(subject, Subject)
        return subject

    def get_output(self, transformed):
        if self.is_tensor or self.is_sitk:
            image = transformed[self.default_image_name]
            transformed = image.data
            if self.is_array:
                transformed = transformed.numpy()
            elif self.is_sitk:
                transformed = nib_to_sitk(image.data, image.affine)
        elif self.is_image:
            transformed = transformed[self.default_image_name]
        elif self.is_dict:
            transformed = dict(transformed)
            for key, value in transformed.items():
                if isinstance(value, Image):
                    transformed[key] = value.data
        elif self.is_nib:
            image = transformed[self.default_image_name]
            data = image.data
            transformed = nib.Nifti1Image(data[0].numpy(), image.affine)
        return transformed

    def _parse_tensor(self, data: TypeData) -> Subject:
        if data.ndim != 4:
            message = f'The input must be a 4D tensor with dimensions (channels, x, y, z) but it has shape {tuple(data.shape)}. Tips: if it is a volume, please add the channels dimension; if it is 2D, also add a dimension of size 1 for the z axis'
            raise ValueError(message)
        return self._get_subject_from_tensor(data)

    def _get_subject_from_tensor(self, tensor: TypeData) -> Subject:
        image = ScalarImage(tensor=tensor)
        return self._get_subject_from_image(image)

    def _get_subject_from_image(self, image: Image) -> Subject:
        subject = Subject({self.default_image_name: image})
        return subject

    @staticmethod
    def _get_subject_from_dict(data: dict, image_keys: Sequence[str], label_keys: Sequence[str] | None=None) -> Subject:
        subject_dict = {}
        label_keys = [] if label_keys is None else label_keys
        for key, value in data.items():
            if key in image_keys:
                class_ = LabelMap if key in label_keys else ScalarImage
                value = class_(tensor=value)
            subject_dict[key] = value
        return Subject(subject_dict)

    def _get_subject_from_sitk_image(self, image):
        tensor, affine = sitk_to_nib(image)
        image = ScalarImage(tensor=tensor, affine=affine)
        return self._get_subject_from_image(image)

@staticmethod
def _get_subject_from_dict(data: dict, image_keys: Sequence[str], label_keys: Sequence[str] | None=None) -> Subject:
    subject_dict = {}
    label_keys = [] if label_keys is None else label_keys
    for key, value in data.items():
        if key in image_keys:
            class_ = LabelMap if key in label_keys else ScalarImage
            value = class_(tensor=value)
        subject_dict[key] = value
    return Subject(subject_dict)

class IntensityTransform(Transform):
    """Transform that modifies voxel intensities only."""

    def get_images_dict(self, subject: Subject) -> dict[str, ScalarImage]:
        images_dict = subject.get_images_dict(intensity_only=True, include=self.include, exclude=self.exclude)
        return images_dict

    def get_images(self, subject: Subject) -> list[ScalarImage]:
        images = subject.get_images(intensity_only=True, include=self.include, exclude=self.exclude)
        return images

    def arguments_are_dict(self) -> bool:
        """Check if main arguments are dict.

        Return ``True`` if the type of all attributes specified in the
        :attr:`args_names` have ``dict`` type.
        """
        args = [getattr(self, name) for name in self.args_names]
        are_dict = [isinstance(arg, dict) for arg in args]
        if all(are_dict):
            return True
        elif not any(are_dict):
            return False
        else:
            message = 'Either all or none of the arguments must be dicts'
            raise ValueError(message)

def get_images_dict(self, subject: Subject) -> dict[str, ScalarImage]:
    images_dict = subject.get_images_dict(intensity_only=True, include=self.include, exclude=self.exclude)
    return images_dict

def get_images(self, subject: Subject) -> list[ScalarImage]:
    images = subject.get_images(intensity_only=True, include=self.include, exclude=self.exclude)
    return images

class SpatialTransform(Transform):
    """Transform that modifies image bounds or voxels positions."""

    def get_images(self, subject: Subject) -> list[Image]:
        images = subject.get_images(intensity_only=False, include=self.include, exclude=self.exclude)
        return images

def get_images(self, subject: Subject) -> list[Image]:
    images = subject.get_images(intensity_only=False, include=self.include, exclude=self.exclude)
    return images

class RandomAffine(RandomTransform, SpatialTransform):
    """Apply a random affine transformation and resample the image.

    Args:
        scales: Tuple :math:`(a_1, b_1, a_2, b_2, a_3, b_3)` defining the
            scaling ranges.
            The scaling values along each dimension are :math:`(s_1, s_2, s_3)`,
            where :math:`s_i \\sim \\mathcal{U}(a_i, b_i)`.
            If two values :math:`(a, b)` are provided,
            then :math:`s_i \\sim \\mathcal{U}(a, b)`.
            If only one value :math:`x` is provided,
            then :math:`s_i \\sim \\mathcal{U}(1 - x, 1 + x)`.
            If three values :math:`(x_1, x_2, x_3)` are provided,
            then :math:`s_i \\sim \\mathcal{U}(1 - x_i, 1 + x_i)`.
            For example, using ``scales=(0.5, 0.5)`` will zoom out the image,
            making the objects inside look twice as small while preserving
            the physical size and position of the image bounds.
        degrees: Tuple :math:`(a_1, b_1, a_2, b_2, a_3, b_3)` defining the
            rotation ranges in degrees.
            Rotation angles around each axis are
            :math:`(\\theta_1, \\theta_2, \\theta_3)`,
            where :math:`\\theta_i \\sim \\mathcal{U}(a_i, b_i)`.
            If two values :math:`(a, b)` are provided,
            then :math:`\\theta_i \\sim \\mathcal{U}(a, b)`.
            If only one value :math:`x` is provided,
            then :math:`\\theta_i \\sim \\mathcal{U}(-x, x)`.
            If three values :math:`(x_1, x_2, x_3)` are provided,
            then :math:`\\theta_i \\sim \\mathcal{U}(-x_i, x_i)`.
        translation: Tuple :math:`(a_1, b_1, a_2, b_2, a_3, b_3)` defining the
            translation ranges in mm.
            Translation along each axis is :math:`(t_1, t_2, t_3)`,
            where :math:`t_i \\sim \\mathcal{U}(a_i, b_i)`.
            If two values :math:`(a, b)` are provided,
            then :math:`t_i \\sim \\mathcal{U}(a, b)`.
            If only one value :math:`x` is provided,
            then :math:`t_i \\sim \\mathcal{U}(-x, x)`.
            If three values :math:`(x_1, x_2, x_3)` are provided,
            then :math:`t_i \\sim \\mathcal{U}(-x_i, x_i)`.
            For example, if the image is in RAS+ orientation (e.g., after
            applying :class:`~torchio.transforms.preprocessing.ToCanonical`)
            and the translation is :math:`(10, 20, 30)`, the sample will move
            10 mm to the right, 20 mm to the front, and 30 mm upwards.
            If the image was in, e.g., PIR+ orientation, the sample will move
            10 mm to the back, 20 mm downwards, and 30 mm to the right.
        isotropic: If ``True``, only one scaling factor will be sampled for all dimensions,
            i.e. :math:`s_1 = s_2 = s_3`.
            If one value :math:`x` is provided in :attr:`scales`, the scaling factor along all
            dimensions will be :math:`s \\sim \\mathcal{U}(1 - x, 1 + x)`.
            If two values provided :math:`(a, b)` in :attr:`scales`, the scaling factor along all
            dimensions will be :math:`s \\sim \\mathcal{U}(a, b)`.
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

    Example:
        >>> import torchio as tio
        >>> image = tio.datasets.Colin27().t1
        >>> transform = tio.RandomAffine(
        ...     scales=(0.9, 1.2),
        ...     degrees=15,
        ... )
        >>> transformed = transform(image)

    .. plot::

        import torchio as tio
        subject = tio.datasets.Slicer('CTChest')
        ct = subject.CT_chest
        transform = tio.RandomAffine()
        ct_transformed = transform(ct)
        subject.add_image(ct_transformed, 'Transformed')
        subject.plot()
    """

    def __init__(self, scales: TypeOneToSixFloat=0.1, degrees: TypeOneToSixFloat=10, translation: TypeOneToSixFloat=0, isotropic: bool=False, center: str='image', default_pad_value: str | float='minimum', default_pad_label: int | float=0, image_interpolation: str='linear', label_interpolation: str='nearest', check_shape: bool=True, **kwargs):
        super().__init__(**kwargs)
        self.isotropic = isotropic
        _parse_scales_isotropic(scales, isotropic)
        self.scales = self.parse_params(scales, 1, 'scales', min_constraint=0)
        self.degrees = self.parse_params(degrees, 0, 'degrees')
        self.translation = self.parse_params(translation, 0, 'translation')
        if center not in ('image', 'origin'):
            message = f'Center argument must be "image" or "origin", not "{center}"'
            raise ValueError(message)
        self.center = center
        self.default_pad_value = _parse_default_value(default_pad_value)
        if not isinstance(default_pad_label, (int, float)):
            message = 'default_pad_label must be a number, '
            message += f'but it is "{default_pad_label}"'
            raise ValueError(message)
        self.default_pad_label = float(default_pad_label)
        self.image_interpolation = self.parse_interpolation(image_interpolation)
        self.label_interpolation = self.parse_interpolation(label_interpolation)
        self.check_shape = check_shape

    @staticmethod
    def get_params(scales: TypeSextetFloat, degrees: TypeSextetFloat, translation: TypeSextetFloat, isotropic: bool) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        scaling_params = torch.as_tensor(RandomTransform.sample_uniform_sextet(scales), dtype=torch.float64)
        if isotropic:
            scaling_params.fill_(scaling_params[0])
        rotation_params = torch.as_tensor(RandomTransform.sample_uniform_sextet(degrees), dtype=torch.float64)
        translation_params = torch.as_tensor(RandomTransform.sample_uniform_sextet(translation), dtype=torch.float64)
        return (scaling_params, rotation_params, translation_params)

    def apply_transform(self, subject: Subject) -> Subject:
        scaling_params, rotation_params, translation_params = self.get_params(self.scales, self.degrees, self.translation, self.isotropic)
        arguments = {'scales': scaling_params, 'degrees': rotation_params, 'translation': translation_params, 'center': self.center, 'default_pad_value': self.default_pad_value, 'default_pad_label': self.default_pad_label, 'image_interpolation': self.image_interpolation, 'label_interpolation': self.label_interpolation, 'check_shape': self.check_shape}
        transform = Affine(**self.add_base_args(arguments))
        transformed = transform(subject)
        assert isinstance(transformed, Subject)
        return transformed

def apply_transform(self, subject: Subject) -> Subject:
    scaling_params, rotation_params, translation_params = self.get_params(self.scales, self.degrees, self.translation, self.isotropic)
    arguments = {'scales': scaling_params, 'degrees': rotation_params, 'translation': translation_params, 'center': self.center, 'default_pad_value': self.default_pad_value, 'default_pad_label': self.default_pad_label, 'image_interpolation': self.image_interpolation, 'label_interpolation': self.label_interpolation, 'check_shape': self.check_shape}
    transform = Affine(**self.add_base_args(arguments))
    transformed = transform(subject)
    assert isinstance(transformed, Subject)
    return transformed

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

class RandomElasticDeformation(RandomTransform, SpatialTransform):
    """Apply dense random elastic deformation.

    A random displacement is assigned to a coarse grid of control points around
    and inside the image. The displacement at each voxel is interpolated from
    the coarse grid using cubic B-splines.

    The `'Deformable Registration' <https://www.sciencedirect.com/topics/computer-science/deformable-registration>`_
    topic on ScienceDirect contains useful articles explaining interpolation of
    displacement fields using cubic B-splines.

    .. warning:: This transform is slow as it requires expensive computations.
        If your images are large you might want to use
        :class:`~torchio.transforms.RandomAffine` instead.

    Args:
        num_control_points: Number of control points along each dimension of
            the coarse grid :math:`(n_x, n_y, n_z)`.
            If a single value :math:`n` is passed,
            then :math:`n_x = n_y = n_z = n`.
            Smaller numbers generate smoother deformations.
            The minimum number of control points is ``4`` as this transform
            uses cubic B-splines to interpolate displacement.
        max_displacement: Maximum displacement along each dimension at each
            control point :math:`(D_x, D_y, D_z)`.
            The displacement along dimension :math:`i` at each control point is
            :math:`d_i \\sim \\mathcal{U}(0, D_i)`.
            If a single value :math:`D` is passed,
            then :math:`D_x = D_y = D_z = D`.
            Note that the total maximum displacement would actually be
            :math:`D_{max} = \\sqrt{D_x^2 + D_y^2 + D_z^2}`.
        locked_borders: If ``0``, all displacement vectors are kept.
            If ``1``, displacement of control points at the
            border of the coarse grid will be set to ``0``.
            If ``2``, displacement of control points at the border of the image
            (red dots in the image below) will also be set to ``0``.
        image_interpolation: See :ref:`Interpolation`.
            Note that this is the interpolation used to compute voxel
            intensities when resampling using the dense displacement field.
            The value of the dense displacement at each voxel is always
            interpolated with cubic B-splines from the values at the control
            points of the coarse grid.
        label_interpolation: See :ref:`Interpolation`.
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.

    `This gist <https://gist.github.com/fepegar/b723d15de620cd2a3a4dbd71e491b59d>`_
    can also be used to better understand the meaning of the parameters.

    This is an example from the
    `3D Slicer registration FAQ <https://www.slicer.org/wiki/Documentation/4.10/FAQ/Registration#What.27s_the_BSpline_Grid_Size.3F>`_.

    .. image:: https://www.slicer.org/w/img_auth.php/6/6f/RegLib_BSplineGridModel.png
        :alt: B-spline example from 3D Slicer documentation

    To generate a similar grid of control points with TorchIO,
    the transform can be instantiated as follows::

        >>> from torchio import RandomElasticDeformation
        >>> transform = RandomElasticDeformation(
        ...     num_control_points=(7, 7, 7),  # or just 7
        ...     locked_borders=2,
        ... )

    Note that control points outside the image bounds are not showed in the
    example image (they would also be red as we set :attr:`locked_borders`
    to ``2``).

    .. warning:: Image folding may occur if the maximum displacement is larger
        than half the coarse grid spacing. The grid spacing can be computed
        using the image bounds in physical space [#]_ and the number of control
        points::

            >>> import numpy as np
            >>> import torchio as tio
            >>> image = tio.datasets.Slicer().MRHead.as_sitk()
            >>> image.GetSize()  # in voxels
            (256, 256, 130)
            >>> image.GetSpacing()  # in mm
            (1.0, 1.0, 1.2999954223632812)
            >>> bounds = np.array(image.GetSize()) * np.array(image.GetSpacing())
            >>> bounds  # mm
            array([256.        , 256.        , 168.99940491])
            >>> num_control_points = np.array((7, 7, 6))
            >>> grid_spacing = bounds / (num_control_points - 2)
            >>> grid_spacing
            array([51.2       , 51.2       , 42.24985123])
            >>> potential_folding = grid_spacing / 2
            >>> potential_folding  # mm
            array([25.6       , 25.6       , 21.12492561])

        Using a :attr:`max_displacement` larger than the computed
        :attr:`potential_folding` will raise a :class:`RuntimeWarning`.

        .. [#] Technically, :math:`2 \\epsilon` should be added to the
            image bounds, where :math:`\\epsilon = 2^{-3}` `according to ITK
            source code <https://github.com/InsightSoftwareConsortium/ITK/blob/633f84548311600845d54ab2463d3412194690a8/Modules/Core/Transform/include/itkBSplineTransformInitializer.hxx#L116-L138>`_.
    """

    def __init__(self, num_control_points: Union[int, TypeTripletInt]=7, max_displacement: Union[float, TypeTripletFloat]=7.5, locked_borders: int=2, image_interpolation: str='linear', label_interpolation: str='nearest', **kwargs):
        super().__init__(**kwargs)
        self._bspline_transformation = None
        self.num_control_points = to_tuple(num_control_points, length=3)
        _parse_num_control_points(self.num_control_points)
        self.max_displacement = to_tuple(max_displacement, length=3)
        _parse_max_displacement(self.max_displacement)
        self.num_locked_borders = locked_borders
        if locked_borders not in (0, 1, 2):
            raise ValueError('locked_borders must be 0, 1, or 2')
        if locked_borders == 2 and 4 in self.num_control_points:
            message = 'Setting locked_borders to 2 and using less than 5 controlpoints results in an identity transform. Lock fewer borders or use more control points.'
            raise ValueError(message)
        self.image_interpolation = self.parse_interpolation(image_interpolation)
        self.label_interpolation = self.parse_interpolation(label_interpolation)

    @staticmethod
    def get_params(num_control_points: TypeTripletInt, max_displacement: tuple[float, float, float], num_locked_borders: int) -> np.ndarray:
        grid_shape = num_control_points
        num_dimensions = 3
        coarse_field = torch.rand(*grid_shape, num_dimensions)
        coarse_field -= 0.5
        coarse_field *= 2
        for dimension in range(3):
            coarse_field[..., dimension] *= max_displacement[dimension]
        for i in range(num_locked_borders):
            coarse_field[i, :] = 0
            coarse_field[-1 - i, :] = 0
            coarse_field[:, i] = 0
            coarse_field[:, -1 - i] = 0
        return coarse_field.numpy()

    def apply_transform(self, subject: Subject) -> Subject:
        subject.check_consistent_spatial_shape()
        control_points = self.get_params(self.num_control_points, self.max_displacement, self.num_locked_borders)
        arguments = {'control_points': control_points, 'max_displacement': self.max_displacement, 'image_interpolation': self.image_interpolation, 'label_interpolation': self.label_interpolation}
        transform = ElasticDeformation(**self.add_base_args(arguments))
        transformed = transform(subject)
        assert isinstance(transformed, Subject)
        return transformed

def apply_transform(self, subject: Subject) -> Subject:
    subject.check_consistent_spatial_shape()
    control_points = self.get_params(self.num_control_points, self.max_displacement, self.num_locked_borders)
    arguments = {'control_points': control_points, 'max_displacement': self.max_displacement, 'image_interpolation': self.image_interpolation, 'label_interpolation': self.label_interpolation}
    transform = ElasticDeformation(**self.add_base_args(arguments))
    transformed = transform(subject)
    assert isinstance(transformed, Subject)
    return transformed

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

class RandomAffineElasticDeformation(RandomTransform, SpatialTransform):
    """Apply a RandomAffine and RandomElasticDeformation simultaneously.

    Optimization to use only a single SimpleITK resampling. For additional details on
    the transformations, see :class:`~torchio.transforms.RandomAffine`
    and :class:`~torchio.transforms.RandomElasticDeformation`

    Args:
        affine_first: Apply affine before elastic deformation.
        affine_kwargs: See :class:`~torchio.transforms.RandomAffine` for kwargs.
        elastic_kwargs: See :class:`~torchio.transforms.RandomElasticDeformation`
            for kwargs.
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.

    Example:
        >>> import torchio as tio
        >>> image = tio.datasets.Colin27().t1
        >>> affine_kwargs = {'scales': (0.9, 1.2), 'degrees': 15}
        >>> elastic_kwargs = {'max_displacement': (17, 12, 2)}
        >>> transform = tio.RandomAffineElasticDeformation(
        ...     affine_kwargs,
        ...     elastic_kwargs
        ... )
        >>> transformed = transform(image)

    .. plot::

        import torchio as tio
        subject = tio.datasets.Slicer('CTChest')
        ct = subject.CT_chest
        elastic_kwargs = {'max_displacement': (17, 12, 2)}
        transform = tio.RandomAffineElasticDeformation(elastic_kwargs=elastic_kwargs)
        ct_transformed = transform(ct)
        subject.add_image(ct_transformed, 'Transformed')
        subject.plot()
    """

    def __init__(self, affine_first: bool=True, affine_kwargs: dict[str, Any] | None=None, elastic_kwargs: dict[str, Any] | None=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.affine_first = affine_first
        from .random_affine import RandomAffine
        from .random_elastic_deformation import RandomElasticDeformation
        self.affine_kwargs = affine_kwargs or {}
        self.random_affine = RandomAffine(**self.affine_kwargs)
        self.elastic_kwargs = elastic_kwargs or {}
        self.random_elastic = RandomElasticDeformation(**self.elastic_kwargs)

    def get_params(self):
        affine_params = self.random_affine.get_params(self.random_affine.scales, self.random_affine.degrees, self.random_affine.translation, self.random_affine.isotropic)
        elastic_params = self.random_elastic.get_params(self.random_elastic.num_control_points, self.random_elastic.max_displacement, self.random_elastic.num_locked_borders)
        return (affine_params, elastic_params)

    def apply_transform(self, subject: Subject):
        affine_params, elastic_params = self.get_params()
        scaling_params, rotation_params, translation_params = affine_params
        affine_params = {'scales': scaling_params.tolist(), 'degrees': rotation_params.tolist(), 'translation': translation_params.tolist(), 'center': self.random_affine.center, 'default_pad_value': self.random_affine.default_pad_value, 'image_interpolation': self.random_affine.image_interpolation, 'label_interpolation': self.random_affine.label_interpolation, 'check_shape': self.random_affine.check_shape}
        elastic_params = {'control_points': elastic_params, 'max_displacement': self.random_elastic.max_displacement, 'image_interpolation': self.random_elastic.image_interpolation, 'label_interpolation': self.random_elastic.label_interpolation}
        arguments = {'affine_first': self.affine_first, 'affine_params': affine_params, 'elastic_params': elastic_params}
        transform = AffineElasticDeformation(**self.add_base_args(arguments))
        transformed = transform(subject)
        assert isinstance(transformed, Subject)
        return transformed

def get_params(self):
    affine_params = self.random_affine.get_params(self.random_affine.scales, self.random_affine.degrees, self.random_affine.translation, self.random_affine.isotropic)
    elastic_params = self.random_elastic.get_params(self.random_elastic.num_control_points, self.random_elastic.max_displacement, self.random_elastic.num_locked_borders)
    return (affine_params, elastic_params)

def apply_transform(self, subject: Subject):
    affine_params, elastic_params = self.get_params()
    scaling_params, rotation_params, translation_params = affine_params
    affine_params = {'scales': scaling_params.tolist(), 'degrees': rotation_params.tolist(), 'translation': translation_params.tolist(), 'center': self.random_affine.center, 'default_pad_value': self.random_affine.default_pad_value, 'image_interpolation': self.random_affine.image_interpolation, 'label_interpolation': self.random_affine.label_interpolation, 'check_shape': self.random_affine.check_shape}
    elastic_params = {'control_points': elastic_params, 'max_displacement': self.random_elastic.max_displacement, 'image_interpolation': self.random_elastic.image_interpolation, 'label_interpolation': self.random_elastic.label_interpolation}
    arguments = {'affine_first': self.affine_first, 'affine_params': affine_params, 'elastic_params': elastic_params}
    transform = AffineElasticDeformation(**self.add_base_args(arguments))
    transformed = transform(subject)
    assert isinstance(transformed, Subject)
    return transformed

class AffineElasticDeformation(SpatialTransform):
    """Apply an Affine and ElasticDeformation simultaneously.

    Optimization to use only a single SimpleITK resampling. For additional details
    on the transformations, see :class:`~torchio.transforms.augmentation.Affine`
    and :class:`~torchio.transforms.augmentation.ElasticDeformation`

    Args:
        affine_first: Apply affine before elastic deformation.
        affine_kwargs: See :class:`~torchio.transforms.augmentation.RandomAffine` for kwargs.
        elastic_kwargs: See
            :class:`~torchio.transforms.augmentation.RandomElasticDeformation` for kwargs.
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.
    """

    def __init__(self, affine_first: bool, affine_params: dict[str, Any], elastic_params: dict[str, Any], **kwargs) -> None:
        super().__init__(**kwargs)
        self.affine_first = affine_first
        self.affine_params = affine_params
        self._affine = Affine(**self.affine_params, **kwargs)
        self.elastic_params = elastic_params
        self._elastic = ElasticDeformation(**self.elastic_params, **kwargs)
        self.args_names = ['affine_first', 'affine_params', 'elastic_params']

    def apply_transform(self, subject: Subject) -> Subject:
        if self._affine.check_shape:
            subject.check_consistent_spatial_shape()
        default_value: float
        for image in self.get_images(subject):
            affine_transform = self._affine.get_affine_transform(image)
            transformed_tensors = []
            for tensor in image.data:
                sitk_image = nib_to_sitk(tensor[np.newaxis], image.affine, force_3d=True)
                if image[TYPE] != INTENSITY:
                    interpolation = self._affine.label_interpolation
                    default_value = 0
                else:
                    interpolation = self._affine.image_interpolation
                    default_value = self._affine.get_default_pad_value(tensor, sitk_image)
                bspline_transform = self._elastic.get_bspline_transform(sitk_image)
                self._elastic.parse_free_form_transform(bspline_transform, self._elastic.max_displacement)
                if self.affine_first:
                    combined_transforms = [affine_transform, bspline_transform]
                else:
                    combined_transforms = [bspline_transform, affine_transform]
                composite_transform = sitk.CompositeTransform(combined_transforms)
                transformed_tensor = self.apply_composite_transform(sitk_image, composite_transform, interpolation, default_value)
                transformed_tensors.append(transformed_tensor)
            image.set_data(torch.stack(transformed_tensors))
        return subject

    def apply_composite_transform(self, sitk_image: sitk.Image, transform: sitk.Transform, interpolation: str, default_value: float) -> torch.Tensor:
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

def apply_transform(self, subject: Subject) -> Subject:
    if self._affine.check_shape:
        subject.check_consistent_spatial_shape()
    default_value: float
    for image in self.get_images(subject):
        affine_transform = self._affine.get_affine_transform(image)
        transformed_tensors = []
        for tensor in image.data:
            sitk_image = nib_to_sitk(tensor[np.newaxis], image.affine, force_3d=True)
            if image[TYPE] != INTENSITY:
                interpolation = self._affine.label_interpolation
                default_value = 0
            else:
                interpolation = self._affine.image_interpolation
                default_value = self._affine.get_default_pad_value(tensor, sitk_image)
            bspline_transform = self._elastic.get_bspline_transform(sitk_image)
            self._elastic.parse_free_form_transform(bspline_transform, self._elastic.max_displacement)
            if self.affine_first:
                combined_transforms = [affine_transform, bspline_transform]
            else:
                combined_transforms = [bspline_transform, affine_transform]
            composite_transform = sitk.CompositeTransform(combined_transforms)
            transformed_tensor = self.apply_composite_transform(sitk_image, composite_transform, interpolation, default_value)
            transformed_tensors.append(transformed_tensor)
        image.set_data(torch.stack(transformed_tensors))
    return subject

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

class Flip(SpatialTransform):
    """Reverse the order of elements in an image along the given axes.

    Args:
        axes: Index or tuple of indices of the spatial dimensions along which
            the image will be flipped. See
            :class:`~torchio.transforms.augmentation.spatial.random_flip.RandomFlip`
            for more information.
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.

    .. tip:: It is handy to specify the axes as anatomical labels when the
        image orientation is not known.
    """

    def __init__(self, axes, **kwargs):
        super().__init__(**kwargs)
        self.axes = _parse_axes(axes)
        self.args_names = ['axes']

    def apply_transform(self, subject: Subject) -> Subject:
        axes = _ensure_axes_indices(subject, self.axes)
        for image in self.get_images(subject):
            _flip_image(image, axes)
        return subject

    def is_invertible(self):
        return True

    def inverse(self):
        return self

def apply_transform(self, subject: Subject) -> Subject:
    axes = _ensure_axes_indices(subject, self.axes)
    for image in self.get_images(subject):
        _flip_image(image, axes)
    return subject

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

class RandomSwap(RandomTransform, IntensityTransform):
    """Randomly swap patches within an image.

    This is typically used in `context restoration for self-supervised learning
    <https://www.sciencedirect.com/science/article/pii/S1361841518304699>`_.

    Args:
        patch_size: Tuple of integers :math:`(w, h, d)` to swap patches
            of size :math:`w \\times h \\times d`.
            If a single number :math:`n` is provided, :math:`w = h = d = n`.
        num_iterations: Number of times that two patches will be swapped.
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.
    """

    def __init__(self, patch_size: TypeTuple=15, num_iterations: int=100, **kwargs):
        super().__init__(**kwargs)
        self.patch_size = np.array(to_tuple(patch_size))
        self.num_iterations = self._parse_num_iterations(num_iterations)

    @staticmethod
    def _parse_num_iterations(num_iterations):
        if not isinstance(num_iterations, int):
            raise TypeError(f'num_iterations must be an int,not {num_iterations}')
        if num_iterations < 0:
            raise ValueError(f'num_iterations must be positive,not {num_iterations}')
        return num_iterations

    @staticmethod
    def get_params(tensor: torch.Tensor, patch_size: np.ndarray, num_iterations: int) -> list[tuple[TypeTripletInt, TypeTripletInt]]:
        si, sj, sk = tensor.shape[-3:]
        spatial_shape = (si, sj, sk)
        locations = []
        for _ in range(num_iterations):
            first_ini, first_fin = get_random_indices_from_shape(spatial_shape, patch_size.tolist())
            while True:
                second_ini, second_fin = get_random_indices_from_shape(spatial_shape, patch_size.tolist())
                larger_than_initial = np.all(second_ini >= first_ini)
                less_than_final = np.all(second_fin <= first_fin)
                if larger_than_initial and less_than_final:
                    continue
                else:
                    break
            location = (tuple(first_ini), tuple(second_ini))
            locations.append(location)
        return locations

    def apply_transform(self, subject: Subject) -> Subject:
        images_dict = self.get_images_dict(subject)
        if not images_dict:
            return subject
        arguments: dict[str, dict] = defaultdict(dict)
        for name, image in images_dict.items():
            locations = self.get_params(image.data, self.patch_size, self.num_iterations)
            arguments['locations'][name] = locations
            arguments['patch_size'][name] = self.patch_size
        transform = Swap(**self.add_base_args(arguments))
        transformed = transform(subject)
        assert isinstance(transformed, Subject)
        return transformed

def apply_transform(self, subject: Subject) -> Subject:
    images_dict = self.get_images_dict(subject)
    if not images_dict:
        return subject
    arguments: dict[str, dict] = defaultdict(dict)
    for name, image in images_dict.items():
        locations = self.get_params(image.data, self.patch_size, self.num_iterations)
        arguments['locations'][name] = locations
        arguments['patch_size'][name] = self.patch_size
    transform = Swap(**self.add_base_args(arguments))
    transformed = transform(subject)
    assert isinstance(transformed, Subject)
    return transformed

class Swap(IntensityTransform):
    """Swap patches within an image.

    This is typically used in `context restoration for self-supervised learning
    <https://www.sciencedirect.com/science/article/pii/S1361841518304699>`_.

    Args:
        patch_size: Tuple of integers :math:`(w, h, d)` to swap patches
            of size :math:`w \\times h \\times d`.
            If a single number :math:`n` is provided, :math:`w = h = d = n`.
        num_iterations: Number of times that two patches will be swapped.
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.
    """

    def __init__(self, patch_size: TypeTripletInt | dict[str, TypeTripletInt], locations: TypeLocations | dict[str, TypeLocations], **kwargs):
        super().__init__(**kwargs)
        self.locations = locations
        self.patch_size = patch_size
        self.args_names = ['locations', 'patch_size']
        self.invert_transform = False

    def apply_transform(self, subject: Subject) -> Subject:
        locations, patch_size = (self.locations, self.patch_size)
        for name, image in self.get_images_dict(subject).items():
            if self.arguments_are_dict():
                assert isinstance(self.locations, dict)
                assert isinstance(self.patch_size, dict)
                locations = self.locations[name]
                patch_size = self.patch_size[name]
            if self.invert_transform:
                assert isinstance(locations, list)
                locations.reverse()
            swapped = _swap(image.data, patch_size, locations)
            image.set_data(swapped)
        return subject

def apply_transform(self, subject: Subject) -> Subject:
    locations, patch_size = (self.locations, self.patch_size)
    for name, image in self.get_images_dict(subject).items():
        if self.arguments_are_dict():
            assert isinstance(self.locations, dict)
            assert isinstance(self.patch_size, dict)
            locations = self.locations[name]
            patch_size = self.patch_size[name]
        if self.invert_transform:
            assert isinstance(locations, list)
            locations.reverse()
        swapped = _swap(image.data, patch_size, locations)
        image.set_data(swapped)
    return subject

class RandomBlur(RandomTransform, IntensityTransform):
    """Blur an image using a random-sized Gaussian filter.

    Args:
        std: Tuple :math:`(a_1, b_1, a_2, b_2, a_3, b_3)` representing the
            ranges (in mm) of the standard deviations
            :math:`(\\sigma_1, \\sigma_2, \\sigma_3)` of the Gaussian kernels used
            to blur the image along each axis, where
            :math:`\\sigma_i \\sim \\mathcal{U}(a_i, b_i)`.
            If two values :math:`(a, b)` are provided,
            then :math:`\\sigma_i \\sim \\mathcal{U}(a, b)`.
            If only one value :math:`x` is provided,
            then :math:`\\sigma_i \\sim \\mathcal{U}(0, x)`.
            If three values :math:`(x_1, x_2, x_3)` are provided,
            then :math:`\\sigma_i \\sim \\mathcal{U}(0, x_i)`.
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.
    """

    def __init__(self, std: Union[float, tuple[float, float]]=(0, 2), **kwargs):
        super().__init__(**kwargs)
        self.std_ranges = self.parse_params(std, None, 'std', min_constraint=0)

    def apply_transform(self, subject: Subject) -> Subject:
        images_dict = self.get_images_dict(subject)
        if not images_dict:
            return subject
        arguments: dict[str, dict] = defaultdict(dict)
        for name in images_dict:
            std = self.get_params(self.std_ranges)
            arguments['std'][name] = std
        transform = Blur(**self.add_base_args(arguments))
        transformed = transform(subject)
        assert isinstance(transformed, Subject)
        return transformed

    def get_params(self, std_ranges: TypeSextetFloat) -> TypeTripletFloat:
        sx, sy, sz = self.sample_uniform_sextet(std_ranges)
        return (sx, sy, sz)

def apply_transform(self, subject: Subject) -> Subject:
    images_dict = self.get_images_dict(subject)
    if not images_dict:
        return subject
    arguments: dict[str, dict] = defaultdict(dict)
    for name in images_dict:
        std = self.get_params(self.std_ranges)
        arguments['std'][name] = std
    transform = Blur(**self.add_base_args(arguments))
    transformed = transform(subject)
    assert isinstance(transformed, Subject)
    return transformed

class Blur(IntensityTransform):
    """Blur an image using a Gaussian filter.

    Args:
        std: Tuple :math:`(\\sigma_1, \\sigma_2, \\sigma_3)` representing the
            the standard deviations (in mm) of the Gaussian kernels used to
            blur the image along each axis.
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.
    """

    def __init__(self, std: Union[TypeTripletFloat, dict[str, TypeTripletFloat]], **kwargs):
        super().__init__(**kwargs)
        self.std = std
        self.args_names = ['std']

    def apply_transform(self, subject: Subject) -> Subject:
        stds = self.std
        for name, image in self.get_images_dict(subject).items():
            if self.arguments_are_dict():
                assert isinstance(self.std, dict)
                stds = self.std[name]
            repets = (image.num_channels, 1)
            stds_channels: np.ndarray
            stds_channels = np.tile(stds, repets)
            transformed_tensors = []
            for std, channel in zip(stds_channels, image.data):
                transformed_tensor = blur(channel, image.spacing, std)
                transformed_tensors.append(transformed_tensor)
            image.set_data(torch.stack(transformed_tensors))
        return subject

def apply_transform(self, subject: Subject) -> Subject:
    stds = self.std
    for name, image in self.get_images_dict(subject).items():
        if self.arguments_are_dict():
            assert isinstance(self.std, dict)
            stds = self.std[name]
        repets = (image.num_channels, 1)
        stds_channels: np.ndarray
        stds_channels = np.tile(stds, repets)
        transformed_tensors = []
        for std, channel in zip(stds_channels, image.data):
            transformed_tensor = blur(channel, image.spacing, std)
            transformed_tensors.append(transformed_tensor)
        image.set_data(torch.stack(transformed_tensors))
    return subject

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

class Noise(IntensityTransform):
    """Add Gaussian noise.

    Add noise sampled from a normal distribution.

    Args:
        mean: Mean :math:`\\mu` of the Gaussian distribution
            from which the noise is sampled.
        std: Standard deviation :math:`\\sigma` of the Gaussian distribution
            from which the noise is sampled.
        seed: Seed for the random number generator.
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.
    """

    def __init__(self, mean: Union[float, dict[str, float]], std: Union[float, dict[str, float]], seed: Union[int, Sequence[int]], **kwargs):
        super().__init__(**kwargs)
        self.mean = mean
        self.std = std
        self.seed = seed
        self.invert_transform = False
        self.args_names = ['mean', 'std', 'seed']

    def apply_transform(self, subject: Subject) -> Subject:
        mean, std, seed = args = (self.mean, self.std, self.seed)
        for name, image in self.get_images_dict(subject).items():
            if self.arguments_are_dict():
                values = (arg[name] for arg in args)
                mean, std, seed = values
            with self._use_seed(seed):
                assert isinstance(mean, float)
                assert isinstance(std, float)
                noise = get_noise(image.data, mean, std)
            if self.invert_transform:
                noise *= -1
            image.set_data(image.data + noise)
        return subject

def apply_transform(self, subject: Subject) -> Subject:
    mean, std, seed = args = (self.mean, self.std, self.seed)
    for name, image in self.get_images_dict(subject).items():
        if self.arguments_are_dict():
            values = (arg[name] for arg in args)
            mean, std, seed = values
        with self._use_seed(seed):
            assert isinstance(mean, float)
            assert isinstance(std, float)
            noise = get_noise(image.data, mean, std)
        if self.invert_transform:
            noise *= -1
        image.set_data(image.data + noise)
    return subject

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

class Gamma(IntensityTransform):
    """Change contrast of an image by raising its values to the power
    :math:`\\gamma`.

    Args:
        gamma: Exponent to which values in the image will be raised.
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
        :class:`~torchio.transforms.preprocessing.intensity.rescale.RescaleIntensity`
        transform may be used to ensure that all values are positive. This is
        generally not problematic, but it is recommended to visualize results
        on image with negative values. More information can be found on
        `this StackExchange question`_.

        .. _this StackExchange question: https://math.stackexchange.com/questions/317528/how-do-you-compute-negative-numbers-to-fractional-powers

    Example:
        >>> import torchio as tio
        >>> subject = tio.datasets.FPG()
        >>> transform = tio.Gamma(0.8)
        >>> transformed = transform(subject)
    """

    def __init__(self, gamma: float, **kwargs):
        super().__init__(**kwargs)
        self.gamma = gamma
        self.args_names = ['gamma']
        self.invert_transform = False

    def apply_transform(self, subject: Subject) -> Subject:
        gamma = self.gamma
        for name, image in self.get_images_dict(subject).items():
            if self.arguments_are_dict():
                assert isinstance(self.gamma, dict)
                gamma = self.gamma[name]
            gammas = to_tuple(gamma, length=len(image.data))
            transformed_tensors = []
            image.set_data(image.data.float())
            for gamma, tensor in zip(gammas, image.data):
                if self.invert_transform:
                    correction = power(tensor, 1 - gamma)
                    transformed_tensor = tensor * correction
                else:
                    transformed_tensor = power(tensor, gamma)
                transformed_tensors.append(transformed_tensor)
            image.set_data(torch.stack(transformed_tensors))
        return subject

def apply_transform(self, subject: Subject) -> Subject:
    gamma = self.gamma
    for name, image in self.get_images_dict(subject).items():
        if self.arguments_are_dict():
            assert isinstance(self.gamma, dict)
            gamma = self.gamma[name]
        gammas = to_tuple(gamma, length=len(image.data))
        transformed_tensors = []
        image.set_data(image.data.float())
        for gamma, tensor in zip(gammas, image.data):
            if self.invert_transform:
                correction = power(tensor, 1 - gamma)
                transformed_tensor = tensor * correction
            else:
                transformed_tensor = power(tensor, gamma)
            transformed_tensors.append(transformed_tensor)
        image.set_data(torch.stack(transformed_tensors))
    return subject

class RandomBiasField(RandomTransform, IntensityTransform):
    """Add random MRI bias field artifact.

    MRI magnetic field inhomogeneity creates intensity
    variations of very low frequency across the whole image.

    The bias field is modeled as a linear combination of
    polynomial basis functions, as in K. Van Leemput et al., 1999,
    *Automated model-based tissue classification of MR images of the brain*.

    It was implemented in NiftyNet by Carole Sudre and used in
    `Sudre et al., 2017, Longitudinal segmentation of age-related
    white matter hyperintensities
    <https://www.sciencedirect.com/science/article/pii/S1361841517300257?via%3Dihub>`_.

    Args:
        coefficients: Maximum magnitude :math:`n` of polynomial coefficients.
            If a tuple :math:`(a, b)` is specified, then
            :math:`n \\sim \\mathcal{U}(a, b)`.
        order: Order of the basis polynomial functions.
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.
    """

    def __init__(self, coefficients: Union[float, tuple[float, float]]=0.5, order: int=3, **kwargs):
        super().__init__(**kwargs)
        self.coefficients_range = self._parse_range(coefficients, 'coefficients_range')
        self.order = _parse_order(order)

    def apply_transform(self, subject: Subject) -> Subject:
        images_dict = self.get_images_dict(subject)
        if not images_dict:
            return subject
        arguments: dict[str, dict] = defaultdict(dict)
        for image_name in images_dict:
            coefficients = self.get_params(self.order, self.coefficients_range)
            arguments['coefficients'][image_name] = coefficients
            arguments['order'][image_name] = self.order
        transform = BiasField(**self.add_base_args(arguments))
        transformed = transform(subject)
        return transformed

    def get_params(self, order: int, coefficients_range: tuple[float, float]) -> list[float]:
        random_coefficients = []
        for x_order in range(0, order + 1):
            for y_order in range(0, order + 1 - x_order):
                for _ in range(0, order + 1 - (x_order + y_order)):
                    sample = self.sample_uniform(*coefficients_range)
                    random_coefficients.append(sample)
        return random_coefficients

def apply_transform(self, subject: Subject) -> Subject:
    images_dict = self.get_images_dict(subject)
    if not images_dict:
        return subject
    arguments: dict[str, dict] = defaultdict(dict)
    for image_name in images_dict:
        coefficients = self.get_params(self.order, self.coefficients_range)
        arguments['coefficients'][image_name] = coefficients
        arguments['order'][image_name] = self.order
    transform = BiasField(**self.add_base_args(arguments))
    transformed = transform(subject)
    return transformed

class BiasField(IntensityTransform):
    """Add MRI bias field artifact.

    Args:
        coefficients: Magnitudes of the polinomial coefficients.
        order: Order of the basis polynomial functions.
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.
    """

    def __init__(self, coefficients: Union[list[float], dict[str, list[float]]], order: Union[int, dict[str, int]], **kwargs):
        super().__init__(**kwargs)
        self.coefficients = coefficients
        self.order = order
        self.invert_transform = False
        self.args_names = ['coefficients', 'order']

    def arguments_are_dict(self):
        coefficients_dict = isinstance(self.coefficients, dict)
        order_dict = isinstance(self.order, dict)
        if coefficients_dict != order_dict:
            message = 'If one of the arguments is a dict, all must be'
            raise ValueError(message)
        return coefficients_dict and order_dict

    def apply_transform(self, subject: Subject) -> Subject:
        coefficients, order = (self.coefficients, self.order)
        for name, image in self.get_images_dict(subject).items():
            if self.arguments_are_dict():
                assert isinstance(self.coefficients, dict)
                assert isinstance(self.order, dict)
                coefficients, order = (self.coefficients[name], self.order[name])
            assert isinstance(order, int)
            bias_field = self.generate_bias_field(image.data, order, coefficients)
            if self.invert_transform:
                np.divide(1, bias_field, out=bias_field)
            image.set_data(image.data * torch.as_tensor(bias_field))
        return subject

    @staticmethod
    def generate_bias_field(data: TypeData, order: int, coefficients: TypeData) -> np.ndarray:
        shape = np.array(data.shape[1:])
        half_shape = shape / 2
        ranges = [np.arange(-n, n) + 0.5 for n in half_shape]
        bias_field = np.zeros(shape)
        meshes = np.asarray(np.meshgrid(*ranges))
        for mesh in meshes:
            mesh_max = mesh.max()
            if mesh_max > 0:
                mesh /= mesh_max
        x_mesh, y_mesh, z_mesh = meshes
        i = 0
        for x_order in range(order + 1):
            for y_order in range(order + 1 - x_order):
                for z_order in range(order + 1 - (x_order + y_order)):
                    coefficient = coefficients[i]
                    new_map = coefficient * x_mesh ** x_order * y_mesh ** y_order * z_mesh ** z_order
                    bias_field += np.transpose(new_map, (1, 0, 2))
                    i += 1
        bias_field = np.exp(bias_field).astype(np.float32)
        return bias_field

def apply_transform(self, subject: Subject) -> Subject:
    coefficients, order = (self.coefficients, self.order)
    for name, image in self.get_images_dict(subject).items():
        if self.arguments_are_dict():
            assert isinstance(self.coefficients, dict)
            assert isinstance(self.order, dict)
            coefficients, order = (self.coefficients[name], self.order[name])
        assert isinstance(order, int)
        bias_field = self.generate_bias_field(image.data, order, coefficients)
        if self.invert_transform:
            np.divide(1, bias_field, out=bias_field)
        image.set_data(image.data * torch.as_tensor(bias_field))
    return subject

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

class SequentialLabels(LabelTransform):
    """Remap labels in a label map so they become consecutive.

    For example, if a label map has labels ``(0, 3, 5)``, then this will apply
    a :class:`~torchio.RemapLabels` transform with ``remapping={3: 1, 5: 2}``,
    and therefore the output image will have labels ``(0, 1, 2)``.

    Example:

        >>> import torch
        >>> import torchio as tio
        >>> def get_image(*labels):
        ...     tensor = torch.as_tensor(labels).reshape(1, 1, 1, -1)
        ...     image = tio.LabelMap(tensor=tensor)
        ...     return image
        ...
        >>> img_with_bg = get_image(0, 5, 10)
        >>> transform = tio.SequentialLabels()
        >>> transform(img_with_bg).data
        tensor([[[[0, 1, 2]]]])
        >>> img_without_bg = get_image(7, 11, 99)
        >>> transform(img_without_bg).data
        tensor([[[[0, 1, 2]]]])

    .. note::
        This transformation is always `fully invertible <invertibility>`_.

    .. warning::
        The background is typically represented with the label ``0``. There
        will be zeros in the output image even if they are none in the input.

    Args:
        masking_method: See :class:`~torchio.transforms.RemapLabels`.
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.
    """

    def __init__(self, masking_method: TypeMaskingMethod=None, **kwargs):
        super().__init__(**kwargs)
        self.masking_method = masking_method

    def apply_transform(self, subject):
        for name, image in self.get_images_dict(subject).items():
            unique_labels = torch.unique(image.data)
            remapping = {unique_labels[i].item(): i for i in range(0, len(unique_labels))}
            init_kwargs = self.get_base_args()
            init_kwargs['include'] = [name]
            transform = RemapLabels(remapping=remapping, masking_method=self.masking_method, **init_kwargs)
            subject = transform(subject)
        return subject

def apply_transform(self, subject):
    for name, image in self.get_images_dict(subject).items():
        unique_labels = torch.unique(image.data)
        remapping = {unique_labels[i].item(): i for i in range(0, len(unique_labels))}
        init_kwargs = self.get_base_args()
        init_kwargs['include'] = [name]
        transform = RemapLabels(remapping=remapping, masking_method=self.masking_method, **init_kwargs)
        subject = transform(subject)
    return subject

class RemapLabels(LabelTransform):
    """Modify labels in a label map.

    Masking can be used to split the label into two during
    the `inverse transformation <invertibility>`_.

    Args:
        remapping: Dictionary that specifies how labels should be remapped.
            The keys are the old labels, and the corresponding values replace
            them.
        masking_method: Defines a mask for where the label remapping is applied. It can be one of:

            - ``None``: the mask image is all ones, i.e. all values in the image are used.

            - A string: key to a :class:`torchio.LabelMap` in the subject which is used as a mask,
              OR an anatomical label: ``'Left'``, ``'Right'``, ``'Anterior'``, ``'Posterior'``,
              ``'Inferior'``, ``'Superior'`` which specifies a half of the mask volume to be ones.

            - A function: the mask image is computed as a function of the intensity image.
              The function must receive and return a 4D :class:`torch.Tensor`.

        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.

    .. plot::

        import torchio as tio

        subject = tio.datasets.FPG()
        subject.remove_image('t1')

        background_labels = (0, 1, 2, 3, 4)

        csf_labels = (5, 12, 16, 47, 52, 53)

        white_matter_labels = (
            45, 46,
            66, 67,
            81, 82,
            83, 84,
            85, 86,
            87,
            89, 90,
            91, 92,
            93, 94,
        )

        not_gray_matter_labels = (
            background_labels
            + csf_labels
            + white_matter_labels
        )

        gray_matter_labels = [
            label for label in subject.GIF_COLORS
            if label not in not_gray_matter_labels
        ]

        labels_groups = (
            background_labels,
            gray_matter_labels,
            white_matter_labels,
            csf_labels,
        )
        remapping = {}
        for target, labels in enumerate(labels_groups):
            for label in labels:
                remapping[label] = target

        parcellation_to_tissues = tio.RemapLabels(remapping)
        tissues = parcellation_to_tissues(subject).seg
        subject.add_image(tissues, 'remapped')
        subject.plot()

    Example:

        >>> import torch
        >>> import torchio as tio
        >>> def get_image(*labels):
        ...     tensor = torch.as_tensor(labels).reshape(1, 1, 1, -1)
        ...     image = tio.LabelMap(tensor=tensor)
        ...     return image
        ...
        >>> image = get_image(0, 1, 2, 3, 4)
        >>> remapping = {1: 2, 2: 1, 3: 1, 4: 7}
        >>> transform = tio.RemapLabels(remapping)
        >>> transform(image).data
        tensor([[[[0, 2, 1, 1, 7]]]])

    .. warning::
        The transform will not be correctly inverted if one of the values in
        ``remapping`` is also in the input image::

            >>> tensor = torch.as_tensor([0, 1]).reshape(1, 1, 1, -1)
            >>> subject = tio.Subject(label=tio.LabelMap(tensor=tensor))
            >>> mapping = {3: 1}  # the value 1 is in the input image
            >>> transform = tio.RemapLabels(mapping)
            >>> transformed = transform(subject)
            >>> back = transformed.apply_inverse_transform()
            >>> original_label_set = set(subject.label.data.unique().tolist())
            >>> back_label_set = set(back.label.data.unique().tolist())
            >>> original_label_set
            {0, 1}
            >>> back_label_set
            {0, 3}

    Example:

        >>> import torchio as tio
        >>> # Target label map has the following labels:
        >>> # {
        >>> #     'left_ventricle': 1, 'right_ventricle': 2,
        >>> #     'left_caudate': 3,   'right_caudate': 4,
        >>> #     'left_putamen': 5,   'right_putamen': 6,
        >>> #     'left_thalamus': 7,  'right_thalamus': 8,
        >>> # }
        >>> transform = tio.RemapLabels({2:1, 4:3, 6:5, 8:7})
        >>> # Merge right side labels with left side labels
        >>> transformed = transform(subject)
        >>> # Undesired behavior: The inverse transform will remap ALL left side labels to right side labels
        >>> # so the label map only has right side labels.
        >>> inverse_transformed = transformed.apply_inverse_transform()
        >>> # Here's the *right* way to do it with masking:
        >>> transform = tio.RemapLabels({2:1, 4:3, 6:5, 8:7}, masking_method="Right")
        >>> # Remap the labels on the right side only (no difference yet).
        >>> transformed = transform(subject)
        >>> # Apply the inverse on the right side only. The labels are correctly split into left/right.
        >>> inverse_transformed = transformed.apply_inverse_transform()
    """

    def __init__(self, remapping: dict[int, int], masking_method: TypeMaskingMethod=None, **kwargs):
        super().__init__(**kwargs)
        self.kwargs = kwargs
        self.remapping = remapping
        self.masking_method = masking_method
        self.args_names = ['remapping', 'masking_method']

    def apply_transform(self, subject):
        for image in self.get_images(subject):
            original_label_set = set(image.data.unique().tolist())
            source_label_set = set(self.remapping.keys())
            if not source_label_set.intersection(original_label_set):
                continue
            new_data = image.data.clone()
            mask = self.get_mask_from_masking_method(self.masking_method, subject, new_data)
            for old_id, new_id in self.remapping.items():
                new_data[mask & (image.data == old_id)] = new_id
            image.set_data(new_data)
        return subject

    def is_invertible(self):
        return True

    def inverse(self):
        targets = self.remapping.values()
        unique_targets = set(targets)
        if len(unique_targets) < len(targets):
            message = f'Labels mapping cannot be inverted because original values are not unique: {self.remapping}'
            raise RuntimeError(message)
        inverse_remapping = {v: k for k, v in self.remapping.items()}
        inverse_transform = RemapLabels(inverse_remapping, masking_method=self.masking_method, **self.kwargs)
        return inverse_transform

def apply_transform(self, subject):
    for image in self.get_images(subject):
        original_label_set = set(image.data.unique().tolist())
        source_label_set = set(self.remapping.keys())
        if not source_label_set.intersection(original_label_set):
            continue
        new_data = image.data.clone()
        mask = self.get_mask_from_masking_method(self.masking_method, subject, new_data)
        for old_id, new_id in self.remapping.items():
            new_data[mask & (image.data == old_id)] = new_id
        image.set_data(new_data)
    return subject

def inverse(self):
    targets = self.remapping.values()
    unique_targets = set(targets)
    if len(unique_targets) < len(targets):
        message = f'Labels mapping cannot be inverted because original values are not unique: {self.remapping}'
        raise RuntimeError(message)
    inverse_remapping = {v: k for k, v in self.remapping.items()}
    inverse_transform = RemapLabels(inverse_remapping, masking_method=self.masking_method, **self.kwargs)
    return inverse_transform

class LabelTransform(Transform):
    """Transform that modifies label maps."""

    def get_images(self, subject: Subject) -> list[LabelMap]:
        images = subject.get_images(intensity_only=False, include=self.include, exclude=self.exclude)
        return [im for im in images if isinstance(im, LabelMap)]

    def get_images_dict(self, subject: Subject) -> dict[str, LabelMap]:
        images = subject.get_images_dict(intensity_only=False, include=self.include, exclude=self.exclude)
        return {k: v for k, v in images.items() if isinstance(v, LabelMap)}

def get_images(self, subject: Subject) -> list[LabelMap]:
    images = subject.get_images(intensity_only=False, include=self.include, exclude=self.exclude)
    return [im for im in images if isinstance(im, LabelMap)]

def get_images_dict(self, subject: Subject) -> dict[str, LabelMap]:
    images = subject.get_images_dict(intensity_only=False, include=self.include, exclude=self.exclude)
    return {k: v for k, v in images.items() if isinstance(v, LabelMap)}

class ToReferenceSpace(SpatialTransform):
    """Modify the spatial metadata so it matches a reference space.

    This is useful, for example, to set meaningful spatial metadata of a neural
    network embedding, for visualization or further processing such as
    resampling a segmentation output.

    Example:

    >>> import torchio as tio
    >>> image = tio.datasets.FPG().t1
    >>> embedding_tensor = my_network(image.tensor)  # we lose metadata here
    >>> embedding_image = tio.ToReferenceSpace.from_tensor(embedding_tensor, image)
    """

    def __init__(self, reference: Image, **kwargs):
        super().__init__(**kwargs)
        if not isinstance(reference, Image):
            raise TypeError('The reference must be a TorchIO image')
        self.reference = reference

    def apply_transform(self, subject: Subject) -> Subject:
        for image in self.get_images(subject):
            new_image = build_image_from_reference(image.data, self.reference)
            image.set_data(new_image.data)
            image.affine = new_image.affine
        return subject

    @staticmethod
    def from_tensor(tensor: torch.Tensor, reference: Image) -> Image:
        """Build a TorchIO image from a tensor and a reference image."""
        return build_image_from_reference(tensor, reference)

def apply_transform(self, subject: Subject) -> Subject:
    for image in self.get_images(subject):
        new_image = build_image_from_reference(image.data, self.reference)
        image.set_data(new_image.data)
        image.affine = new_image.affine
    return subject

@staticmethod
def from_tensor(tensor: torch.Tensor, reference: Image) -> Image:
    """Build a TorchIO image from a tensor and a reference image."""
    return build_image_from_reference(tensor, reference)

def build_image_from_reference(tensor: torch.Tensor, reference: Image) -> Image:
    input_shape = np.array(reference.spatial_shape)
    output_shape = np.array(tensor.shape[-3:])
    downsampling_factor = input_shape / output_shape
    input_spacing = np.array(reference.spacing)
    output_spacing = input_spacing * downsampling_factor
    downsample = Resample(output_spacing, image_interpolation='nearest')
    reference = downsample(reference)
    class_ = reference.__class__
    result = class_(tensor=tensor, affine=reference.affine)
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
def check_affine_key_presence(affine_name: str, subject: Subject):
    for image in subject.get_images(intensity_only=False):
        if affine_name in image:
            return
    message = f'An affine name was given ("{affine_name}"), but it was not found in any image in the subject'
    raise ValueError(message)

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

class NormalizationTransform(IntensityTransform):
    """Base class for intensity preprocessing transforms.

    Args:
        masking_method: Defines the mask used to compute the normalization statistics. It can be one of:

            - ``None``: the mask image is all ones, i.e. all values in the image are used.

            - A string: key to a :class:`torchio.LabelMap` in the subject which is used as a mask,
              OR an anatomical label: ``'Left'``, ``'Right'``, ``'Anterior'``, ``'Posterior'``,
              ``'Inferior'``, ``'Superior'`` which specifies a side of the mask volume to be ones.

            - A function: the mask image is computed as a function of the intensity image.
              The function must receive and return a :class:`torch.Tensor`

        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.

    Example:
        >>> import torchio as tio
        >>> subject = tio.datasets.Colin27()
        >>> subject
        Colin27(Keys: ('t1', 'head', 'brain'); images: 3)
        >>> transform = tio.ZNormalization()  # ZNormalization is a subclass of NormalizationTransform
        >>> transformed = transform(subject)  # use all values to compute mean and std
        >>> transform = tio.ZNormalization(masking_method='brain')
        >>> transformed = transform(subject)  # use only values within the brain
        >>> transform = tio.ZNormalization(masking_method=lambda x: x > x.mean())
        >>> transformed = transform(subject)  # use values above the image mean
    """

    def __init__(self, masking_method: TypeMaskingMethod=None, **kwargs):
        super().__init__(**kwargs)
        self.masking_method = masking_method

    def apply_transform(self, subject: Subject) -> Subject:
        for image_name, image in self.get_images_dict(subject).items():
            mask = self.get_mask_from_masking_method(self.masking_method, subject, image.data)
            self.apply_normalization(subject, image_name, mask)
        return subject

    def apply_normalization(self, subject: Subject, image_name: str, mask: torch.Tensor) -> None:
        raise NotImplementedError

def apply_transform(self, subject: Subject) -> Subject:
    for image_name, image in self.get_images_dict(subject).items():
        mask = self.get_mask_from_masking_method(self.masking_method, subject, image.data)
        self.apply_normalization(subject, image_name, mask)
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

def apply_normalization(self, subject: Subject, image_name: str, mask: torch.Tensor) -> None:
    image: Image = subject[image_name]
    image.set_data(self.rescale(image.data, mask, image_name))

class Mask(IntensityTransform):
    """Set voxels outside of mask to a constant value.

    Args:
        masking_method: See
            :class:`~torchio.transforms.preprocessing.intensity.NormalizationTransform`.
        outside_value: Value to set for all voxels outside of the mask.
        labels: If a label map is used to generate the mask,
            sequence of labels to consider. If ``None``, all values larger than
            zero will be used for the mask.
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.

    Raises:
        RuntimeWarning: If a 4D image is masked with a 3D mask, the mask will
            be expanded along the channels (first) dimension, and a warning
            will be raised.

    Example:
        >>> import torchio as tio
        >>> subject = tio.datasets.Colin27()
        >>> subject
        Colin27(Keys: ('t1', 'head', 'brain'); images: 3)
        >>> mask = tio.Mask(masking_method='brain')  # Use "brain" image to mask
        >>> transformed = mask(subject)  # Set voxels outside of the brain to 0

    .. plot::

        import torchio as tio
        subject = tio.datasets.Colin27()
        subject.remove_image('head')
        mask = tio.Mask('brain')
        masked = mask(subject)
        subject.add_image(masked.t1, 'Masked')
        subject.plot()
    """

    def __init__(self, masking_method: TypeMaskingMethod, outside_value: float=0, labels: Sequence[int] | None=None, **kwargs):
        super().__init__(**kwargs)
        self.masking_method = masking_method
        self.masking_labels = labels
        self.outside_value = outside_value
        self.args_names = ['masking_method']

    def apply_transform(self, subject: Subject) -> Subject:
        for image in self.get_images(subject):
            mask_data = self.get_mask_from_masking_method(self.masking_method, subject, image.data, self.masking_labels)
            assert isinstance(image, ScalarImage)
            self.apply_masking(image, mask_data)
        return subject

    def apply_masking(self, image: ScalarImage, mask_data: torch.Tensor) -> None:
        masked = mask(image.data, mask_data, self.outside_value)
        image.set_data(masked)

def apply_transform(self, subject: Subject) -> Subject:
    for image in self.get_images(subject):
        mask_data = self.get_mask_from_masking_method(self.masking_method, subject, image.data, self.masking_labels)
        assert isinstance(image, ScalarImage)
        self.apply_masking(image, mask_data)
    return subject

def apply_masking(self, image: ScalarImage, mask_data: torch.Tensor) -> None:
    masked = mask(image.data, mask_data, self.outside_value)
    image.set_data(masked)

class HistogramStandardization(NormalizationTransform):
    """Perform histogram standardization of intensity values.

    Implementation of `New variants of a method of MRI scale
    standardization <https://ieeexplore.ieee.org/document/836373>`_.

    See example in :func:`torchio.transforms.HistogramStandardization.train`.

    Args:
        landmarks: Dictionary (or path to a PyTorch file with ``.pt`` or ``.pth``
            extension in which a dictionary has been saved) whose keys are
            image names in the subject and values are NumPy arrays or paths to
            NumPy arrays defining the landmarks after training with
            :meth:`torchio.transforms.HistogramStandardization.train`.
        masking_method: See
            :class:`~torchio.transforms.preprocessing.intensity.NormalizationTransform`.
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.

    Example:
        >>> import torch
        >>> import torchio as tio
        >>> landmarks = {
        ...     't1': 't1_landmarks.npy',
        ...     't2': 't2_landmarks.npy',
        ... }
        >>> transform = tio.HistogramStandardization(landmarks)
        >>> torch.save(landmarks, 'path_to_landmarks.pth')
        >>> transform = tio.HistogramStandardization('path_to_landmarks.pth')
    """

    def __init__(self, landmarks: TypeLandmarks, masking_method: TypeMaskingMethod=None, **kwargs):
        super().__init__(masking_method=masking_method, **kwargs)
        self.landmarks = landmarks
        self.landmarks_dict = self._parse_landmarks(landmarks)
        self.args_names = ['landmarks', 'masking_method']

    @staticmethod
    def _parse_landmarks(landmarks: TypeLandmarks) -> dict[str, np.ndarray]:
        if isinstance(landmarks, (str, Path)):
            path = Path(landmarks)
            if path.suffix not in ('.pt', '.pth'):
                message = f'The landmarks file must have extension .pt or .pth, not "{path.suffix}"'
                raise ValueError(message)
            landmarks_dict = torch.load(path)
        else:
            landmarks_dict = landmarks
        for key, value in landmarks_dict.items():
            if isinstance(value, (str, Path)):
                landmarks_dict[key] = np.load(value)
        return landmarks_dict

    def apply_normalization(self, subject: Subject, image_name: str, mask: torch.Tensor) -> None:
        if image_name not in self.landmarks_dict:
            keys = tuple(self.landmarks_dict.keys())
            message = f'Image name "{image_name}" should be a key in the landmarks dictionary, whose keys are {keys}'
            raise KeyError(message)
        image = subject[image_name]
        landmarks = self.landmarks_dict[image_name]
        normalized = _normalize(image.data, landmarks, mask=mask.numpy())
        image.set_data(normalized)

    @classmethod
    def train(cls, images_paths: Sequence[TypePath], cutoff: tuple[float, float] | None=None, mask_path: Sequence[TypePath] | TypePath | None=None, masking_function: Callable | None=None, output_path: TypePath | None=None, *, progress: bool=True) -> np.ndarray:
        """Extract average histogram landmarks from images used for training.

        Args:
            images_paths: List of image paths used to train.
            cutoff: Optional minimum and maximum quantile values,
                respectively, that are used to select a range of intensity of
                interest. Equivalent to :math:`pc_1` and :math:`pc_2` in
                `Nyúl and Udupa's paper <https://pubmed.ncbi.nlm.nih.gov/10571928/>`_.
            mask_path: Path (or list of paths) to a binary image that will be
                used to select the voxels use to compute the stats during
                histogram training. If ``None``, all voxels in the image will
                be used.
            masking_function: Function used to extract voxels used for
                histogram training.
            output_path: Optional file path with extension ``.txt`` or
                ``.npy``, where the landmarks will be saved.

        Example:

            >>> import torch
            >>> import numpy as np
            >>> from pathlib import Path
            >>> from torchio.transforms import HistogramStandardization
            >>>
            >>> t1_paths = ['subject_a_t1.nii', 'subject_b_t1.nii.gz']
            >>> t2_paths = ['subject_a_t2.nii', 'subject_b_t2.nii.gz']
            >>>
            >>> t1_landmarks_path = Path('t1_landmarks.npy')
            >>> t2_landmarks_path = Path('t2_landmarks.npy')
            >>>
            >>> t1_landmarks = (
            ...     t1_landmarks_path
            ...     if t1_landmarks_path.is_file()
            ...     else HistogramStandardization.train(t1_paths)
            ... )
            >>> np.save(t1_landmarks_path, t1_landmarks)
            >>>
            >>> t2_landmarks = (
            ...     t2_landmarks_path
            ...     if t2_landmarks_path.is_file()
            ...     else HistogramStandardization.train(t2_paths)
            ... )
            >>> np.save(t2_landmarks_path, t2_landmarks)
            >>>
            >>> landmarks_dict = {
            ...     't1': t1_landmarks,
            ...     't2': t2_landmarks,
            ... }
            >>>
            >>> transform = HistogramStandardization(landmarks_dict)
        """
        is_masks_list = isinstance(mask_path, Sequence)
        if is_masks_list and len(mask_path) != len(images_paths):
            message = f'Different number of images ({len(images_paths)}) and mask ({len(mask_path)}) paths found'
            raise ValueError(message)
        quantiles_cutoff = DEFAULT_CUTOFF if cutoff is None else cutoff
        percentiles_cutoff = 100 * np.array(quantiles_cutoff)
        percentiles_database = []
        a, b = percentiles_cutoff
        percentiles = _get_percentiles((a, b))
        iterable: Iterable[TypePath]
        iterable = tqdm(images_paths) if progress else images_paths
        for i, image_file_path in enumerate(iterable):
            tensor, _ = read_image(image_file_path)
            if masking_function is not None:
                mask = masking_function(tensor)
            elif mask_path is None:
                mask = np.ones_like(tensor, dtype=bool)
            else:
                if is_masks_list:
                    assert isinstance(mask_path, Sequence)
                    path = mask_path[i]
                else:
                    path = mask_path
                mask, _ = read_image(path)
                mask = mask.numpy() > 0
            array = tensor.numpy()
            percentile_values = np.percentile(array[mask], percentiles)
            percentiles_database.append(percentile_values)
        percentiles_database_array = np.vstack(percentiles_database)
        mapping = _get_average_mapping(percentiles_database_array)
        if output_path is not None:
            output_path = Path(output_path).expanduser()
            extension = output_path.suffix
            if extension == '.txt':
                modality = 'image'
                text = f'{modality} {' '.join(map(str, mapping))}'
                output_path.write_text(text)
            elif extension == '.npy':
                np.save(output_path, mapping)
        return mapping

def apply_normalization(self, subject: Subject, image_name: str, mask: torch.Tensor) -> None:
    if image_name not in self.landmarks_dict:
        keys = tuple(self.landmarks_dict.keys())
        message = f'Image name "{image_name}" should be a key in the landmarks dictionary, whose keys are {keys}'
        raise KeyError(message)
    image = subject[image_name]
    landmarks = self.landmarks_dict[image_name]
    normalized = _normalize(image.data, landmarks, mask=mask.numpy())
    image.set_data(normalized)

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

def apply_transform(self, subject: Subject) -> Subject:
    for image in self.get_images(subject):
        assert isinstance(image, ScalarImage)
        self.apply_clamp(image)
    return subject

class PCA(IntensityTransform):
    """Compute principal component analysis (PCA) of an image.

    PCA can be useful to visualize embeddings generated by a neural network.
    See for example Figure 8 in `Cluster and Predict Latent Patches for
    Improved Masked Image Modeling <https://arxiv.org/abs/2502.08769>`_.

    Args:
        num_components: Number of components to compute.
        whiten: If ``True``, the components are normalized to have unit variance.
        normalize: If ``True``, all components are divided by the standard
            deviation of the first component.
        make_skewness_positive: If ``True``, the skewness of each component is
            made positive by multiplying the component by -1 if its skewness is
            negative.
        values_range: If not ``None``, these values are linearly mappped to
            :math:`[0, 1]`.
        clip: If ``True``, the output values are clipped to :math:`[0, 1]`.
        pca_kwargs: Additional keyword arguments to pass to
            :class:`sklearn.decomposition.PCA`.

    Example:

    >>> import torchio as tio
    >>> from torchio.visualization import build_image_from_reference
    >>> ct = my_preprocessed_ct_image  # Assume this is a preprocessed CT image
    >>> ct
    ScalarImage(shape: (1, 240, 480, 480); spacing: (1.50, 0.75, 0.75); orientation: SLP+; dtype: torch.FloatTensor; memory: 210.9 MiB)
    >>> embedding_tensor = model(ct.data[None])[0]  # `model` is some pre-trained neural network
    >>> embedding_image = ToReferenceSpace(ct)(embedding_tensor)
    >>> embedding_image
    ScalarImage(shape: (512, 24, 24, 24); spacing: (15.00, 15.00, 15.00); orientation: SLP+; dtype: torch.FloatTensor; memory: 27.0 MiB)
    >>> pca = tio.PCA()(embedding_image)
    >>> pca
    ScalarImage(shape: (3, 24, 24, 24); spacing: (15.00, 15.00, 15.00); orientation: SLP+; dtype: torch.FloatTensor; memory: 162.0 KiB)
    """

    def __init__(self, num_components: int=3, *, whiten: bool=True, normalize: bool=True, make_skewness_positive: bool=True, values_range: tuple[float, float] | None=(-2.3, 2.3), clip: bool=True, pca_kwargs: dict[str, Any] | None=None, **kwargs):
        super().__init__(**kwargs)
        self.num_components = num_components
        self.whiten = whiten
        self.normalize = normalize
        self.make_skewness_positive = make_skewness_positive
        self.values_range = values_range
        self.clip = clip
        self.pca_kwargs = pca_kwargs
        self.args_names = ['num_components', 'whiten', 'normalize', 'make_skewness_positive', 'values_range', 'clip', 'pca_kwargs']

    def apply_transform(self, subject: Subject) -> Subject:
        for image in self.get_images(subject):
            kwargs = {} if self.pca_kwargs is None else self.pca_kwargs
            pca_image = _compute_pca(image, num_components=self.num_components, whiten=self.whiten, normalize=self.normalize, make_skewness_positive=self.make_skewness_positive, values_range=self.values_range, clip=self.clip, **kwargs)
            image.set_data(pca_image.data)
        return subject

def apply_transform(self, subject: Subject) -> Subject:
    for image in self.get_images(subject):
        kwargs = {} if self.pca_kwargs is None else self.pca_kwargs
        pca_image = _compute_pca(image, num_components=self.num_components, whiten=self.whiten, normalize=self.normalize, make_skewness_positive=self.make_skewness_positive, values_range=self.values_range, clip=self.clip, **kwargs)
        image.set_data(pca_image.data)
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

@staticmethod
def get_unique_labels(data: torch.Tensor) -> set[int]:
    labels = data.unique().tolist()
    return set(labels)

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

def test_2d(self):
    subject = self.make_2d(self.sample_subject)
    assert subject.is_2d()

def test_different_non_numeric(self):
    with pytest.raises(RuntimeError):
        self.sample_subject.check_consistent_attribute('path')

def test_load_unload(self):
    self.sample_subject.load()
    for image in self.sample_subject.get_images(intensity_only=False):
        assert image._loaded
    self.sample_subject.unload()
    for image in self.sample_subject.get_images(intensity_only=False):
        assert not image._loaded

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

def test_apply_transform_missing(self):

    class T(tio.Transform):
        pass
    with pytest.raises(TypeError):
        T().apply_transform(0)

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

def model_probs(subject):
    subject = copy.deepcopy(subject)
    subject.im.set_data(torch.rand_like(subject.im.data))
    return subject

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

def test_transform_order(self):
    src_transform = tio.RandomAffineElasticDeformation(affine_kwargs={'scales': 0, 'degrees': 0, 'translation': 1}, elastic_kwargs={'num_control_points': 5, 'max_displacement': 1})
    (scales, degrees, translation), control_points = src_transform.get_params()
    max_displacement = src_transform.random_elastic.max_displacement
    transform1 = tio.AffineElasticDeformation(affine_first=True, affine_params={'scales': scales, 'degrees': degrees, 'translation': translation}, elastic_params={'control_points': control_points, 'max_displacement': max_displacement})
    transform2 = tio.AffineElasticDeformation(affine_first=False, affine_params={'scales': scales, 'degrees': degrees, 'translation': translation}, elastic_params={'control_points': control_points, 'max_displacement': max_displacement})
    transformed1 = transform1(self.sample_subject)
    transformed2 = transform2(self.sample_subject)
    self.assert_tensor_not_equal(transformed1.t1.data, transformed2.t1.data)

class TestResize(TorchioTestCase):
    """Tests for `Resize`."""

    def test_one_dim(self):
        target_shape = 5
        transform = tio.Resize(target_shape)
        transformed = transform(self.sample_subject)
        for image in transformed.get_images(intensity_only=False):
            assert image.spatial_shape == 3 * (target_shape,)

    def test_all_dims(self):
        target_shape = (11, 6, 7)
        transform = tio.Resize(target_shape)
        transformed = transform(self.sample_subject)
        for image in transformed.get_images(intensity_only=False):
            assert image.spatial_shape == target_shape

def test_one_dim(self):
    target_shape = 5
    transform = tio.Resize(target_shape)
    transformed = transform(self.sample_subject)
    for image in transformed.get_images(intensity_only=False):
        assert image.spatial_shape == 3 * (target_shape,)

def test_all_dims(self):
    target_shape = (11, 6, 7)
    transform = tio.Resize(target_shape)
    transformed = transform(self.sample_subject)
    for image in transformed.get_images(intensity_only=False):
        assert image.spatial_shape == target_shape

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

def test_empty_mask(self):
    subject = copy.deepcopy(self.sample_subject)
    subject.label.set_data(subject.label.data * 0)
    rescale = tio.RescaleIntensity(masking_method='label')
    with pytest.warns(RuntimeWarning):
        rescale(subject)

