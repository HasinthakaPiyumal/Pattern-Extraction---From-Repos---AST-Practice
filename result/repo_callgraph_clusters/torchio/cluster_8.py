# Cluster 8

def to_tuple(value: Any, length: int=1) -> tuple[TypeNumber, ...]:
    """Convert variable to tuple of length n.

    Example:
        >>> from torchio.utils import to_tuple
        >>> to_tuple(1, length=1)
        (1,)
        >>> to_tuple(1, length=3)
        (1, 1, 1)

    If value is an iterable, n is ignored and tuple(value) is returned

    Example:
        >>> to_tuple((1,), length=1)
        (1,)
        >>> to_tuple((1, 2), length=1)
        (1, 2)
        >>> to_tuple([1, 2], length=3)
        (1, 2)
    """
    try:
        iter(value)
        value = tuple(value)
    except TypeError:
        value = length * (value,)
    return value

def get_stem(path: TypePath | Sequence[TypePath]) -> str | list[str]:
    """Get stem of path or paths.

    Example:
        >>> from torchio.utils import get_stem
        >>> get_stem('/home/user/my_image.nii.gz')
        'my_image'
    """

    def _get_stem(path_string: TypePath) -> str:
        return Path(path_string).name.split('.')[0]
    if isinstance(path, (str, os.PathLike)):
        return _get_stem(path)
    else:
        return [_get_stem(p) for p in path]

def guess_type(string: str) -> Any:
    string = string.replace(' ', '')
    result_type: Any
    try:
        value = ast.literal_eval(string)
    except ValueError:
        result_type = str
    else:
        result_type = type(value)
    if result_type in (list, tuple):
        string = string[1:-1]
        split = string.split(',')
        list_result = [guess_type(n) for n in split]
        value = tuple(list_result) if result_type is tuple else list_result
        return value
    try:
        value = result_type(string)
    except TypeError:
        value = None
    return value

def check_sequence(sequence: Sequence, name: str) -> None:
    try:
        iter(sequence)
    except TypeError as err:
        message = f'"{name}" must be a sequence, not {type(name)}'
        raise TypeError(message) from err

def get_major_sitk_version() -> int:
    version = getattr(sitk, '__version__', None)
    major_version = 1 if version is None else 2
    return major_version

def history_collate(batch: Sequence, collate_transforms=True) -> dict:
    attr = constants.HISTORY if collate_transforms else 'applied_transforms'
    from .data import Subject
    first_element = batch[0]
    if isinstance(first_element, Subject):
        dictionary = {key: default_collate([d[key] for d in batch]) for key in first_element}
        if hasattr(first_element, attr):
            dictionary.update({attr: [getattr(d, attr) for d in batch]})
    else:
        dictionary = {}
    return dictionary

def get_subclasses(target_class: type) -> list[type]:
    subclasses = target_class.__subclasses__()
    subclasses += sum((get_subclasses(cls) for cls in subclasses), [])
    return subclasses

def get_first_item(data_loader: DataLoader):
    return next(iter(data_loader))

def parse_spatial_shape(shape):
    result = to_tuple(shape, length=3)
    for n in result:
        if n < 1 or n % 1:
            message = f'All elements in a spatial shape must be positive integers, but the following shape was passed: {shape}'
            raise ValueError(message)
    if len(result) != 3:
        message = f'Spatial shapes must have 3 elements, but the following shape was passed: {shape}'
        raise ValueError(message)
    return result

def is_iterable(object: Any) -> bool:
    try:
        iter(object)
        return True
    except TypeError:
        return False

def get_params_dict_from_kwargs(kwargs):
    from torchio.utils import guess_type
    params_dict = {}
    if kwargs is not None:
        for substring in kwargs.split():
            try:
                key, value_string = substring.split('=')
            except ValueError as error:
                message = f'Arguments string "{kwargs}" not valid'
                raise ValueError(message) from error
            value = guess_type(value_string)
            params_dict[key] = value
    return params_dict

class SubjectsDataset(Dataset):
    """Base TorchIO dataset.

    Reader of 3D medical images that directly inherits from the PyTorch
    :class:`~torch.utils.data.Dataset`. It can be used with a
    :class:`~tio.SubjectsLoader` for efficient loading and
    augmentation. It receives a list of instances of :class:`~torchio.Subject`
    and an optional transform applied to the volumes after loading.

    Args:
        subjects: List of instances of :class:`~torchio.Subject`.
        transform: An instance of :class:`~torchio.transforms.Transform`
            that will be applied to each subject.
        load_getitem: Load all subject images before returning it in
            :meth:`__getitem__`. Set it to ``False`` if some of the images will
            not be needed during training.

    Example:
        >>> import torchio as tio
        >>> subject_a = tio.Subject(
        ...     t1=tio.ScalarImage('t1.nrrd',),
        ...     t2=tio.ScalarImage('t2.mha',),
        ...     label=tio.LabelMap('t1_seg.nii.gz'),
        ...     age=31,
        ...     name='Fernando Perez',
        ... )
        >>> subject_b = tio.Subject(
        ...     t1=tio.ScalarImage('colin27_t1_tal_lin.minc',),
        ...     t2=tio.ScalarImage('colin27_t2_tal_lin_dicom',),
        ...     label=tio.LabelMap('colin27_seg1.nii.gz'),
        ...     age=56,
        ...     name='Colin Holmes',
        ... )
        >>> subjects_list = [subject_a, subject_b]
        >>> transforms = [
        ...     tio.RescaleIntensity(out_min_max=(0, 1)),
        ...     tio.RandomAffine(),
        ... ]
        >>> transform = tio.Compose(transforms)
        >>> subjects_dataset = tio.SubjectsDataset(subjects_list, transform=transform)
        >>> subject = subjects_dataset[0]

    .. _NiBabel: https://nipy.org/nibabel/#nibabel
    .. _SimpleITK: https://itk.org/Wiki/ITK/FAQ#What_3D_file_formats_can_ITK_import_and_export.3F
    .. _DICOM: https://www.dicomstandard.org/
    .. _affine matrix: https://nipy.org/nibabel/coordinate_systems.html

    .. tip:: To quickly iterate over the subjects without loading the images,
        use :meth:`dry_iter()`.
    """

    def __init__(self, subjects: Sequence[Subject], transform: Callable | None=None, load_getitem: bool=True):
        self._parse_subjects_list(subjects)
        self._subjects = subjects
        self._transform: Callable | None
        self.set_transform(transform)
        self.load_getitem = load_getitem

    def __len__(self):
        return len(self._subjects)

    def __getitem__(self, index: int) -> Subject:
        try:
            index = int(index)
        except (RuntimeError, TypeError) as err:
            message = f'Index "{index}" must be int or compatible dtype, but an object of type "{type(index)}" was passed'
            raise ValueError(message) from err
        subject = self._subjects[index]
        subject = copy.deepcopy(subject)
        if self.load_getitem:
            subject.load()
        if self._transform is not None:
            subject = self._transform(subject)
        return subject

    @classmethod
    def from_batch(cls, batch: dict) -> SubjectsDataset:
        """Instantiate a dataset from a batch generated by a data loader.

        Args:
            batch: Dictionary generated by a data loader, containing data that
                can be converted to instances of :class:`~.torchio.Subject`.
        """
        subjects: list[Subject] = get_subjects_from_batch(batch)
        return cls(subjects)

    def dry_iter(self):
        """Return the internal list of subjects.

        This can be used to iterate over the subjects without loading the data
        and applying any transforms::

        >>> names = [subject.name for subject in dataset.dry_iter()]
        """
        return self._subjects

    def set_transform(self, transform: Callable | None) -> None:
        """Set the :attr:`transform` attribute.

        Args:
            transform: Callable object, typically an subclass of
                :class:`torchio.transforms.Transform`.
        """
        if transform is not None and (not callable(transform)):
            message = f'The transform must be a callable object, but it has type {type(transform)}'
            raise ValueError(message)
        self._transform = transform

    @staticmethod
    def _parse_subjects_list(subjects_list: Iterable[Subject]) -> None:
        try:
            iter(subjects_list)
        except TypeError as e:
            message = f'Subject list must be an iterable, not {type(subjects_list)}'
            raise TypeError(message) from e
        if not subjects_list:
            raise ValueError('Subjects list is empty')
        for subject in subjects_list:
            if not isinstance(subject, Subject):
                message = f'Subjects list must contain instances of torchio.Subject, not "{type(subject)}"'
                raise TypeError(message)

def __len__(self):
    return len(self._subjects)

def __getitem__(self, index: int) -> Subject:
    try:
        index = int(index)
    except (RuntimeError, TypeError) as err:
        message = f'Index "{index}" must be int or compatible dtype, but an object of type "{type(index)}" was passed'
        raise ValueError(message) from err
    subject = self._subjects[index]
    subject = copy.deepcopy(subject)
    if self.load_getitem:
        subject.load()
    if self._transform is not None:
        subject = self._transform(subject)
    return subject

def set_transform(self, transform: Callable | None) -> None:
    """Set the :attr:`transform` attribute.

        Args:
            transform: Callable object, typically an subclass of
                :class:`torchio.transforms.Transform`.
        """
    if transform is not None and (not callable(transform)):
        message = f'The transform must be a callable object, but it has type {type(transform)}'
        raise ValueError(message)
    self._transform = transform

@staticmethod
def _parse_subjects_list(subjects_list: Iterable[Subject]) -> None:
    try:
        iter(subjects_list)
    except TypeError as e:
        message = f'Subject list must be an iterable, not {type(subjects_list)}'
        raise TypeError(message) from e
    if not subjects_list:
        raise ValueError('Subjects list is empty')
    for subject in subjects_list:
        if not isinstance(subject, Subject):
            message = f'Subjects list must contain instances of torchio.Subject, not "{type(subject)}"'
            raise TypeError(message)

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

@staticmethod
def _parse_images(images: list[Image]) -> None:
    if not images:
        raise TypeError('A subject without images cannot be created')

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

def read_matrix(path: TypePath):
    """Read an affine transform and convert to tensor."""
    path = Path(path)
    suffix = path.suffix
    if suffix in ('.tfm', '.h5'):
        tensor = _read_itk_matrix(path)
    elif suffix in ('.txt', '.trsf'):
        tensor = _read_niftyreg_matrix(path)
    else:
        raise ValueError(f'Unknown suffix for transform file: "{suffix}"')
    return tensor

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

def set_data(self, tensor: TypeData):
    """Store a 4D tensor in the :attr:`data` key and attribute.

        Args:
            tensor: 4D tensor with dimensions :math:`(C, W, H, D)`.
        """
    self[DATA] = self._parse_tensor(tensor, none_ok=False)
    self._loaded = True

@affine.setter
def affine(self, matrix):
    self[AFFINE] = self._parse_affine(matrix)

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

def _get_subject_num_samples(self, subject):
    num_samples = getattr(subject, NUM_SAMPLES, self.samples_per_volume)
    return num_samples

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

def __len__(self):
    return len(self.locations)

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

class PatchSampler:
    """Base class for TorchIO samplers.

    Args:
        patch_size: Tuple of integers :math:`(w, h, d)` to generate patches
            of size :math:`w \\times h \\times d`.
            If a single number :math:`n` is provided, :math:`w = h = d = n`.

    .. warning:: This is an abstract class that should only be instantiated
        using child classes such as :class:`~torchio.data.UniformSampler` and
        :class:`~torchio.data.WeightedSampler`.
    """

    def __init__(self, patch_size: TypeSpatialShape):
        patch_size_array = np.array(to_tuple(patch_size, length=3))
        for n in patch_size_array:
            if n < 1 or not isinstance(n, (int, np.integer)):
                message = f'Patch dimensions must be positive integers, not {patch_size_array}'
                raise ValueError(message)
        self.patch_size = patch_size_array.astype(np.uint16)

    def extract_patch(self, subject: Subject, index_ini: TypeTripletInt) -> Subject:
        cropped_subject = self.crop(subject, index_ini, self.patch_size)
        return cropped_subject

    def crop(self, subject: Subject, index_ini: TypeTripletInt, patch_size: TypeTripletInt) -> Subject:
        transform = self._get_crop_transform(subject, index_ini, patch_size)
        cropped_subject = transform(subject)
        index_ini_array = np.asarray(index_ini)
        patch_size_array = np.asarray(patch_size)
        index_fin = index_ini_array + patch_size_array
        location = index_ini_array.tolist() + index_fin.tolist()
        cropped_subject[LOCATION] = torch.as_tensor(location)
        cropped_subject.update_attributes()
        return cropped_subject

    @staticmethod
    def _get_crop_transform(subject, index_ini: TypeTripletInt, patch_size: TypeSpatialShape):
        from ...transforms.preprocessing.spatial.crop import Crop
        shape = np.array(subject.spatial_shape, dtype=np.uint16)
        index_ini_array = np.array(index_ini, dtype=np.uint16)
        patch_size_array = np.array(patch_size, dtype=np.uint16)
        assert len(index_ini_array) == 3
        assert len(patch_size_array) == 3
        index_fin = index_ini_array + patch_size_array
        crop_ini = index_ini_array.tolist()
        crop_fin = (shape - index_fin).tolist()
        start = ()
        cropping = sum(zip(crop_ini, crop_fin), start)
        return Crop(cropping)

    def __call__(self, subject: Subject, num_patches: int | None=None) -> Generator[Subject]:
        subject.check_consistent_space()
        if np.any(self.patch_size > subject.spatial_shape):
            message = f'Patch size {tuple(self.patch_size)} cannot be larger than image size {tuple(subject.spatial_shape)}'
            raise RuntimeError(message)
        kwargs = {} if num_patches is None else {'num_patches': num_patches}
        return self._generate_patches(subject, **kwargs)

    def _generate_patches(self, subject: Subject, num_patches: int | None=None) -> Generator[Subject]:
        raise NotImplementedError

def __init__(self, patch_size: TypeSpatialShape):
    patch_size_array = np.array(to_tuple(patch_size, length=3))
    for n in patch_size_array:
        if n < 1 or not isinstance(n, (int, np.integer)):
            message = f'Patch dimensions must be positive integers, not {patch_size_array}'
            raise ValueError(message)
    self.patch_size = patch_size_array.astype(np.uint16)

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

@staticmethod
def _parse_overlap_mode(overlap_mode):
    if overlap_mode not in ('crop', 'average', 'hann'):
        message = f'Overlap mode must be "crop", "average" or "hann" but  "{overlap_mode}" was passed'
        raise ValueError(message)

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

def is_invertible(self):
    return hasattr(self, 'invert_transform')

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

class Lambda(Transform):
    """Applies a user-defined function as transform.

    Args:
        function: Callable that receives and returns a 4D
            :class:`torch.Tensor`.
        types_to_apply: List of strings corresponding to the image types to
            which this transform should be applied. If ``None``, the transform
            will be applied to all images in the subject.
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.

    Example:
        >>> import torchio as tio
        >>> invert_intensity = tio.Lambda(lambda x: -x, types_to_apply=[tio.INTENSITY])
        >>> invert_mask = tio.Lambda(lambda x: 1 - x, types_to_apply=[tio.LABEL])
        >>> def double(x):
        ...     return 2 * x
        >>> double_transform = tio.Lambda(double)
    """

    def __init__(self, function: TypeCallable, types_to_apply: Sequence[str] | None=None, **kwargs):
        super().__init__(**kwargs)
        self.function = function
        self.types_to_apply = types_to_apply
        self.args_names = ['function', 'types_to_apply']

    def apply_transform(self, subject: Subject) -> Subject:
        images = subject.get_images(intensity_only=False, include=self.include, exclude=self.exclude)
        for image in images:
            image_type = image[TYPE]
            if self.types_to_apply is not None:
                if image_type not in self.types_to_apply:
                    continue
            function_arg = image.data
            result = self.function(function_arg)
            if not isinstance(result, torch.Tensor):
                message = f'The returned value from the callable argument must be of type {torch.Tensor}, not {type(result)}'
                raise ValueError(message)
            if result.ndim != function_arg.ndim:
                message = f'The number of dimensions of the returned value must be {function_arg.ndim}, not {result.ndim}'
                raise ValueError(message)
            image.set_data(result)
        return subject

def apply_transform(self, subject: Subject) -> Subject:
    images = subject.get_images(intensity_only=False, include=self.include, exclude=self.exclude)
    for image in images:
        image_type = image[TYPE]
        if self.types_to_apply is not None:
            if image_type not in self.types_to_apply:
                continue
        function_arg = image.data
        result = self.function(function_arg)
        if not isinstance(result, torch.Tensor):
            message = f'The returned value from the callable argument must be of type {torch.Tensor}, not {type(result)}'
            raise ValueError(message)
        if result.ndim != function_arg.ndim:
            message = f'The number of dimensions of the returned value must be {function_arg.ndim}, not {result.ndim}'
            raise ValueError(message)
        image.set_data(result)
    return subject

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

def get_sitk_interpolator(interpolation: str) -> int:
    if not isinstance(interpolation, str):
        message = f'Interpolation must be a string, not "{interpolation}" of type {type(interpolation)}'
        raise ValueError(message)
    string = getattr(Interpolation, interpolation.upper()).value
    return getattr(sitk, string)

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

def __len__(self):
    return len(self.transforms)

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

def _parse_scales_isotropic(scales, isotropic):
    scales = to_tuple(scales)
    if isotropic and len(scales) in (3, 6):
        message = f'If "isotropic" is True, the value for "scales" must have length 1 or 2, but "{scales}" was passed. If you want to set isotropic scaling, use a single value or two values as a range for the scaling factor. Refer to the documentation for more information.'
        raise ValueError(message)

def _parse_default_value(value: str | float) -> str | float:
    if isinstance(value, Number) or value in ('minimum', 'otsu', 'mean'):
        return value
    message = 'Value for default_pad_value must be "minimum", "otsu", "mean" or a number'
    raise ValueError(message)

def _parse_num_control_points(num_control_points: TypeTripletInt) -> None:
    for axis, number in enumerate(num_control_points):
        if not isinstance(number, int) or number < 4:
            message = f'The number of control points for axis {axis} must be an integer greater than 3, not {number}'
            raise ValueError(message)

def _parse_max_displacement(max_displacement: tuple[float, float, float]) -> None:
    for axis, number in enumerate(max_displacement):
        if not isinstance(number, Number) or number < 0:
            message = f'The maximum displacement at each control point for axis {axis} must be a number greater or equal to 0, not {number}'
            raise ValueError(message)

def _parse_axes(axes: Union[int, tuple[int, ...]]):
    axes_tuple = to_tuple(axes)
    for axis in axes_tuple:
        is_int = isinstance(axis, int)
        is_string = isinstance(axis, str)
        valid_number = is_int and axis in (0, 1, 2)
        if not is_string and (not valid_number):
            message = f'All axes must be 0, 1 or 2, but found "{axis}" with type {type(axis)}'
            raise ValueError(message)
    return axes_tuple

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

@staticmethod
def parse_axes(axes: Union[int, tuple[int, ...]]):
    axes_tuple = to_tuple(axes)
    for axis in axes_tuple:
        is_int = isinstance(axis, int)
        if not is_int or axis not in (0, 1, 2):
            raise ValueError('All axes must be 0, 1 or 2')
    return axes_tuple

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

@staticmethod
def _parse_num_iterations(num_iterations):
    if not isinstance(num_iterations, int):
        raise TypeError(f'num_iterations must be an int,not {num_iterations}')
    if num_iterations < 0:
        raise ValueError(f'num_iterations must be positive,not {num_iterations}')
    return num_iterations

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

def _parse_label_key(label_key: str | None) -> str | None:
    if label_key is not None and (not isinstance(label_key, str)):
        message = f'"label_key" must be a string or None, not {type(label_key)}'
        raise TypeError(message)
    return label_key

def _parse_used_labels(used_labels: Sequence[int] | None) -> Sequence[int] | None:
    if used_labels is None:
        return None
    check_sequence(used_labels, 'used_labels')
    for e in used_labels:
        if not isinstance(e, int):
            message = f'Items in "used_labels" must be integers, but some are not: {used_labels}'
            raise ValueError(message)
    return used_labels

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

def arguments_are_dict(self):
    coefficients_dict = isinstance(self.coefficients, dict)
    order_dict = isinstance(self.order, dict)
    if coefficients_dict != order_dict:
        message = 'If one of the arguments is a dict, all must be'
        raise ValueError(message)
    return coefficients_dict and order_dict

def _parse_order(order):
    if not isinstance(order, int):
        raise TypeError(f'Order must be an int, not {type(order)}')
    if order < 0:
        raise ValueError(f'Order must be a positive int, not {order}')
    return order

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

def __init__(self, reference: Image, **kwargs):
    super().__init__(**kwargs)
    if not isinstance(reference, Image):
        raise TypeError('The reference must be a TorchIO image')
    self.reference = reference

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

def __init__(self, target: str, **kwargs):
    super().__init__(**kwargs)
    if not isinstance(target, str):
        message = f'The target must be a string, but "{type(target)}" was found'
        raise ValueError(message)
    self.target = target
    self.args_names = ['target']

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

class Resize(SpatialTransform):
    """Resample images so the output shape matches the given target shape.

    The field of view remains the same.

    .. warning:: In most medical image applications, this transform should not
        be used as it will deform the physical object by scaling anisotropically
        along the different dimensions. The solution to change an image size is
        typically applying :class:`~torchio.transforms.Resample` and
        :class:`~torchio.transforms.CropOrPad`.

    Args:
        target_shape: Tuple :math:`(W, H, D)`. If a single value :math:`N` is
            provided, then :math:`W = H = D = N`. The size of dimensions set to
            -1 will be kept.
        image_interpolation: See :ref:`Interpolation`.
        label_interpolation: See :ref:`Interpolation`.
    """

    def __init__(self, target_shape: TypeSpatialShape, image_interpolation: str='linear', label_interpolation: str='nearest', **kwargs):
        super().__init__(**kwargs)
        self.target_shape = np.asarray(to_tuple(target_shape, length=3))
        self.image_interpolation = self.parse_interpolation(image_interpolation)
        self.label_interpolation = self.parse_interpolation(label_interpolation)
        self.args_names = ['target_shape', 'image_interpolation', 'label_interpolation']

    def apply_transform(self, subject: Subject) -> Subject:
        shape_in = np.asarray(subject.spatial_shape)
        shape_out = self.target_shape
        negative_mask = shape_out == -1
        shape_out[negative_mask] = shape_in[negative_mask]
        spacing_in = np.asarray(subject.spacing)
        spacing_out = shape_in / shape_out * spacing_in
        resample = Resample(spacing_out, image_interpolation=self.image_interpolation, label_interpolation=self.label_interpolation, **self.get_base_args())
        resampled = resample(subject)
        assert isinstance(resampled, Subject)
        if not resampled.spatial_shape == tuple(shape_out):
            message = f'Output shape {resampled.spatial_shape} != target shape {tuple(shape_out)}. Fixing with CropOrPad'
            warnings.warn(message, RuntimeWarning, stacklevel=2)
            crop_pad = CropOrPad(shape_out, **self.get_base_args())
            resampled = crop_pad(resampled)
        assert isinstance(resampled, Subject)
        return resampled

def apply_transform(self, subject: Subject) -> Subject:
    shape_in = np.asarray(subject.spatial_shape)
    shape_out = self.target_shape
    negative_mask = shape_out == -1
    shape_out[negative_mask] = shape_in[negative_mask]
    spacing_in = np.asarray(subject.spacing)
    spacing_out = shape_in / shape_out * spacing_in
    resample = Resample(spacing_out, image_interpolation=self.image_interpolation, label_interpolation=self.label_interpolation, **self.get_base_args())
    resampled = resample(subject)
    assert isinstance(resampled, Subject)
    if not resampled.spatial_shape == tuple(shape_out):
        message = f'Output shape {resampled.spatial_shape} != target shape {tuple(shape_out)}. Fixing with CropOrPad'
        warnings.warn(message, RuntimeWarning, stacklevel=2)
        crop_pad = CropOrPad(shape_out, **self.get_base_args())
        resampled = crop_pad(resampled)
    assert isinstance(resampled, Subject)
    return resampled

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

class To(IntensityTransform):
    """Convert the image tensor data type and/or device.

    This transform is a thin wrapper around :func:`torch.Tensor.to`.

    Args:
        target: First argument to :func:`torch.Tensor.to`.
        to_kwargs: Additional keyword arguments to pass to :func:`torch.Tensor.to`.

    Example:
        >>> import torchio as tio
        >>> ct = tio.datasets.Slicer('CTChest').CT_chest
        >>> clamp = tio.Clamp(out_min=-1000, out_max=1000)
        >>> ct_clamped = clamp(ct)
        >>> rescale = tio.RescaleIntensity(in_min_max=(-1000, 1000), out_min_max=(0, 255))
        >>> ct_rescaled = rescale(ct_clamped)
        >>> to_uint8 = tio.To(torch.uint8)
        >>> ct_uint8 = to_uint8(ct_rescaled)
    """

    def __init__(self, target: str | torch.dtype | torch.device, to_kwargs: dict[str, Any] | None=None, **kwargs):
        super().__init__(**kwargs)
        self.target = target
        if to_kwargs is None:
            to_kwargs = {}
        self.to_kwargs = to_kwargs
        self.args_names = ['target', 'to_kwargs']

    def apply_transform(self, subject: Subject) -> Subject:
        for image in self.get_images(subject):
            assert isinstance(image, ScalarImage)
            image.set_data(image.data.to(self.target, **self.to_kwargs))
        return subject

def apply_transform(self, subject: Subject) -> Subject:
    for image in self.get_images(subject):
        assert isinstance(image, ScalarImage)
        image.set_data(image.data.to(self.target, **self.to_kwargs))
    return subject

def get_all_random_transforms():
    transforms_names = [name for name in dir(tio.transforms) if name.startswith('Random')]
    classes = [getattr(tio.transforms, name) for name in transforms_names]
    return classes

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

def test_guess_type(self):
    assert tio.utils.guess_type('None') is None
    assert isinstance(tio.utils.guess_type('1'), int)
    assert isinstance(tio.utils.guess_type('1.5'), float)
    assert isinstance(tio.utils.guess_type('(1, 3, 5)'), tuple)
    assert isinstance(tio.utils.guess_type('(1,3,5)'), tuple)
    assert isinstance(tio.utils.guess_type('[1,3,5]'), list)
    assert isinstance(tio.utils.guess_type('test'), str)

class TestIO(TorchioTestCase):
    """Tests for `io` module."""

    def setUp(self):
        super().setUp()
        self.nii_path = self.get_image_path('read_image')
        self.dicom_dir = self.get_tests_data_dir() / 'dicom'
        self.dicom_path = self.dicom_dir / 'IMG0001.dcm'
        string = '1.5 0.18088 -0.124887 0.65072 -0.20025 0.965639 -0.165653 -11.6452 0.0906326 0.18661 0.978245 11.4002 0 0 0 1 '
        tensor = torch.as_tensor(np.fromstring(string, sep=' ').reshape(4, 4))
        self.matrix = tensor

    def test_read_image(self):
        io.read_image(self.nii_path)

    def test_save_rgb(self):
        im = ScalarImage(tensor=torch.rand(1, 4, 5, 1))
        with pytest.warns(RuntimeWarning):
            im.save(self.dir / 'test.jpg')

    def test_read_dicom_file(self):
        tensor, _ = io.read_image(self.dicom_path)
        assert tuple(tensor.shape) == (1, 88, 128, 1)

    def test_read_dicom_dir(self):
        tensor, _ = io.read_image(self.dicom_dir)
        assert tuple(tensor.shape) == (1, 88, 128, 17)

    def test_dicom_dir_missing(self):
        with pytest.raises(FileNotFoundError):
            io._read_dicom('missing')

    def test_dicom_dir_no_files(self):
        empty = self.dir / 'empty'
        empty.mkdir()
        sitk.ProcessObject_SetGlobalWarningDisplay(False)
        with pytest.raises(FileNotFoundError):
            io._read_dicom(empty)
        sitk.ProcessObject_SetGlobalWarningDisplay(True)

    def write_read_matrix(self, suffix):
        out_path = self.dir / f'matrix{suffix}'
        io.write_matrix(self.matrix, out_path)
        matrix = io.read_matrix(out_path)
        assert torch.allclose(matrix, self.matrix)

    def test_matrix_itk(self):
        self.write_read_matrix('.tfm')
        self.write_read_matrix('.h5')

    def test_matrix_txt(self):
        self.write_read_matrix('.txt')

    def test_ensure_4d_5d(self):
        tensor = torch.rand(3, 4, 5, 1, 2)
        assert io.ensure_4d(tensor).shape == (2, 3, 4, 5)

    def test_ensure_4d_5d_t_gt_1(self):
        tensor = torch.rand(3, 4, 5, 2, 2)
        with pytest.raises(ValueError):
            io.ensure_4d(tensor)

    def test_ensure_4d_2d(self):
        tensor = torch.rand(4, 5)
        assert io.ensure_4d(tensor).shape == (1, 4, 5, 1)

    def test_ensure_4d_2d_3dims_rgb_first(self):
        tensor = torch.rand(3, 4, 5)
        assert io.ensure_4d(tensor).shape == (3, 4, 5, 1)

    def test_ensure_4d_2d_3dims_rgb_last(self):
        tensor = torch.rand(4, 5, 3)
        assert io.ensure_4d(tensor).shape == (3, 4, 5, 1)

    def test_ensure_4d_3d(self):
        tensor = torch.rand(4, 5, 6)
        assert io.ensure_4d(tensor).shape == (1, 4, 5, 6)

    def test_ensure_4d_2_spatial_dims(self):
        tensor = torch.rand(4, 5, 6)
        assert io.ensure_4d(tensor, num_spatial_dims=2).shape == (4, 5, 6, 1)

    def test_ensure_4d_3_spatial_dims(self):
        tensor = torch.rand(4, 5, 6)
        assert io.ensure_4d(tensor, num_spatial_dims=3).shape == (1, 4, 5, 6)

    def test_ensure_4d_nd_not_supported(self):
        tensor = torch.rand(1, 2, 3, 4, 5)
        with pytest.raises(ValueError):
            io.ensure_4d(tensor)

    def test_sitk_to_nib(self):
        data = np.random.rand(10, 12)
        image = sitk.GetImageFromArray(data)
        tensor, _ = io.sitk_to_nib(image)
        assert data.sum() == pytest.approx(tensor.sum())

    def test_sitk_to_affine(self):
        spacing = (1, 2, 3)
        direction_lps = (-1, 0, 0, 0, -1, 0, 0, 0, 1)
        origin_lps = left, posterior, superior = (-10, -20, 30)
        image = sitk.GetImageFromArray(np.random.rand(10, 20, 30))
        image.SetDirection(direction_lps)
        image.SetSpacing(spacing)
        image.SetOrigin(origin_lps)
        origin_ras = (-left, -posterior, superior)
        fixture = np.diag((*spacing, 1))
        fixture[:3, 3] = origin_ras
        affine = io.get_ras_affine_from_sitk(image)
        self.assert_tensor_almost_equal(fixture, affine)

def test_read_image(self):
    io.read_image(self.nii_path)

def test_read_dicom_file(self):
    tensor, _ = io.read_image(self.dicom_path)
    assert tuple(tensor.shape) == (1, 88, 128, 1)

def test_read_dicom_dir(self):
    tensor, _ = io.read_image(self.dicom_dir)
    assert tuple(tensor.shape) == (1, 88, 128, 17)

class Dataset:

    def __init__(self, data):
        self.data = data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index):
        return self.data[index]

def __len__(self):
    return len(self.data)

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

def get_mask(label):
    mask = transform.get_mask_from_anatomical_label(label, tensor)
    return mask

class TestPad(TorchioTestCase):
    """Tests for `Pad`."""

    def test_pad(self):
        image = self.sample_subject.t1
        padding = (1, 2, 3, 4, 5, 6)
        sitk_image = image.as_sitk()
        low, high = (padding[::2], padding[1::2])
        sitk_padded = sitk.ConstantPad(sitk_image, low, high, 0)
        tio_padded = tio.Pad(padding, padding_mode=0)(image)
        sitk_tensor, sitk_affine = sitk_to_nib(sitk_padded)
        tio_tensor, tio_affine = sitk_to_nib(tio_padded.as_sitk())
        self.assert_tensor_equal(sitk_tensor, tio_tensor)
        self.assert_tensor_equal(sitk_affine, tio_affine)

    def test_nans_history(self):
        padded = tio.Pad(1, padding_mode=2)(self.sample_subject)
        again = padded.history[0](self.sample_subject)
        assert not torch.isnan(again.t1.data).any()

    def test_padding_modes(self):

        def padding_func():
            return
        for padding_mode in [0, *tio.Pad.PADDING_MODES, padding_func]:
            tio.Pad(0, padding_mode=padding_mode)
        with self.assertRaises(KeyError):
            tio.Pad(0, padding_mode='abc')

    def test_padding_mean_label_map(self):
        with self.assertWarns(RuntimeWarning):
            tio.Pad(1, padding_mode='mean')(self.sample_subject.label)

    def test_padding_modes_global(self):
        x = torch.ones(1, 1, 2, 2, dtype=torch.int)
        x[..., 0, 0] = 0
        add_bottom_row = (0, 0, 0, 1, 0, 0)
        with_zeros = tio.Pad(add_bottom_row)(x)
        assert with_zeros[0, 0, 2].tolist() == [0, 0]
        with_minimum = tio.Pad(add_bottom_row, padding_mode='minimum')(x)
        assert with_minimum[0, 0, 2].tolist() == [0, 0]
        with_maximum = tio.Pad(add_bottom_row, padding_mode='maximum')(x)
        assert with_maximum[0, 0, 2].tolist() == [1, 1]
        with_median = tio.Pad(add_bottom_row, padding_mode='median')(x)
        assert with_median[0, 0, 2].tolist() == [1, 1]
        with_mean = tio.Pad(add_bottom_row, padding_mode='mean')(x)
        assert with_mean[0, 0, 2].tolist() == [0, 0]
        x = x.float()
        with_mean = tio.Pad(add_bottom_row, padding_mode='mean')(x)
        assert with_mean[0, 0, 2].tolist() == [0.75, 0.75]

    def test_truncation_warning(self):
        x = torch.ones(1, 1, 2, 2, dtype=torch.int)
        pad = tio.Pad(1, padding_mode='mean')
        with pytest.warns(RuntimeWarning):
            pad(x)

def test_nans_history(self):
    padded = tio.Pad(1, padding_mode=2)(self.sample_subject)
    again = padded.history[0](self.sample_subject)
    assert not torch.isnan(again.t1.data).any()

