# Cluster 21

@app.command()
def main(input_path: Path=typer.Argument(..., exists=True, file_okay=True, dir_okay=True, readable=True), plot: bool=typer.Option(False, '--plot/--no-plot', '-p/-P', help='Plot the image using Matplotlib or Pillow.'), show: bool=typer.Option(False, '--show/--no-show', '-s/-S', help='Show the image using specialized visualisation software.'), label: bool=typer.Option(False, '--label/--scalar', '-l/-s', help='Use torchio.LabelMap to instantiate the image.'), load: bool=typer.Option(False, help='Load the image from disk so that information about data type and memory can be displayed. Slower, especially for large images.')) -> None:
    """Print information about an image and, optionally, show it.

    Example:
    $ tiohd input.nii.gz
    """
    import torchio as tio
    class_ = tio.LabelMap if label else tio.ScalarImage
    image = class_(input_path)
    if load:
        image.load()
    print(image)
    if plot:
        image.plot()
    if show:
        image.show()

@app.command()
def main(input_path: Path=typer.Argument(..., exists=True, file_okay=True, dir_okay=True, readable=True), transform_name: str=typer.Argument(...), output_path: Path=typer.Argument(..., file_okay=True, dir_okay=False, writable=True), kwargs: str=typer.Option(None, '--kwargs', '-k', help='String of kwargs, e.g. "degrees=(-5,15) num_transforms=3".'), imclass: str=typer.Option('ScalarImage', '--imclass', '-c', help='Name of the subclass of torchio.Image that will be used to instantiate the image.'), seed: int=typer.Option(None, '--seed', '-s', help='Seed for PyTorch random number generator.'), verbose: bool=typer.Option(False, help='Print random transform parameters.'), show_progress: bool=typer.Option(True, '--show-progress/--hide-progress', '-p/-P', help='Show animations indicating progress.')):
    """Apply transform to an image.

    Example:
    $ tiotr input.nrrd RandomMotion output.nii "degrees=(-5,15) num_transforms=3" -v
    """
    import torch
    import torchio.transforms as transforms
    from torchio.utils import apply_transform_to_file
    try:
        transform_class = getattr(transforms, transform_name)
    except AttributeError as error:
        message = f'Transform "{transform_name}" not found in torchio'
        raise ValueError(message) from error
    params_dict = get_params_dict_from_kwargs(kwargs)
    transform = transform_class(**params_dict)
    if seed is not None:
        torch.manual_seed(seed)
    with Progress(SpinnerColumn(), TextColumn('[progress.description]{task.description}'), transient=True, disable=not show_progress) as progress:
        progress.add_task('Applying transform', total=1)
        apply_transform_to_file(input_path, transform, output_path, verbose=verbose, class_=imclass)

class FPG(Subject):
    """3T :math:`T_1`-weighted brain MRI and corresponding parcellation.

    Args:
        load_all: If ``True``, three more images will be loaded: a
            :math:`T_2`-weighted MRI, a diffusion MRI and a functional MRI.
    """

    def __init__(self, load_all: bool=False):
        repo_dir = urllib.parse.urljoin(DATA_REPO, 'fernando/')
        self.filenames = {'t1': 't1.nii.gz', 'seg': 't1_seg_gif.nii.gz', 'rigid': 't1_to_mni.tfm', 'affine': 't1_to_mni_affine.h5'}
        if load_all:
            self.filenames['t2'] = 't2.nii.gz'
            self.filenames['fmri'] = 'fmri.nrrd'
            self.filenames['dmri'] = 'dmri.nrrd'
        download_root = get_torchio_cache_dir() / 'fpg'
        for filename in self.filenames.values():
            download_url(urllib.parse.urljoin(repo_dir, filename), download_root, filename=filename)
        rigid = read_matrix(download_root / self.filenames['rigid'])
        affine = read_matrix(download_root / self.filenames['affine'])
        subject_dict = {'t1': ScalarImage(download_root / self.filenames['t1'], rigid_matrix=rigid, affine_matrix=affine), 'seg': LabelMap(download_root / self.filenames['seg'], rigid_matrix=rigid, affine_matrix=affine)}
        if load_all:
            subject_dict['t2'] = ScalarImage(download_root / self.filenames['t2'])
            subject_dict['fmri'] = ScalarImage(download_root / self.filenames['fmri'])
            subject_dict['dmri'] = ScalarImage(download_root / self.filenames['dmri'])
        super().__init__(subject_dict)
        self.gif_colors = self.GIF_COLORS

    def plot(self, *args, **kwargs):
        super().plot(*args, **kwargs, cmap_dict={'seg': self.gif_colors})
    GIF_COLORS = {0: (0, 0, 0), 1: (0, 0, 0), 5: (127, 255, 212), 12: (240, 230, 140), 16: (176, 48, 96), 24: (48, 176, 96), 31: (48, 176, 96), 32: (103, 255, 255), 33: (103, 255, 255), 35: (238, 186, 243), 36: (119, 159, 176), 37: (122, 186, 220), 38: (122, 186, 220), 39: (96, 204, 96), 40: (96, 204, 96), 41: (220, 247, 164), 42: (220, 247, 164), 43: (205, 62, 78), 44: (205, 62, 78), 45: (225, 225, 225), 46: (225, 225, 225), 47: (60, 60, 60), 48: (220, 216, 20), 49: (220, 216, 20), 50: (196, 58, 250), 51: (196, 58, 250), 52: (120, 18, 134), 53: (120, 18, 134), 54: (255, 165, 0), 55: (255, 165, 0), 56: (12, 48, 255), 57: (12, 48, 225), 58: (236, 13, 176), 59: (236, 13, 176), 60: (0, 118, 14), 61: (0, 118, 14), 62: (165, 42, 42), 63: (165, 42, 42), 64: (160, 32, 240), 65: (160, 32, 240), 66: (56, 192, 255), 67: (56, 192, 255), 70: (255, 225, 225), 72: (184, 237, 194), 73: (180, 231, 250), 74: (225, 183, 231), 76: (180, 180, 180), 77: (180, 180, 180), 81: (245, 255, 200), 82: (255, 230, 255), 83: (245, 245, 245), 84: (220, 255, 220), 85: (220, 220, 220), 86: (200, 255, 255), 87: (250, 220, 200), 89: (245, 255, 200), 90: (255, 230, 255), 91: (245, 245, 245), 92: (220, 255, 220), 93: (220, 220, 220), 94: (200, 255, 255), 96: (140, 125, 255), 97: (140, 125, 255), 101: (255, 62, 150), 102: (255, 62, 150), 103: (160, 82, 45), 104: (160, 82, 45), 105: (165, 42, 42), 106: (165, 42, 42), 107: (205, 91, 69), 108: (205, 91, 69), 109: (100, 149, 237), 110: (100, 149, 237), 113: (135, 206, 235), 114: (135, 206, 235), 115: (250, 128, 114), 116: (250, 128, 114), 117: (255, 255, 0), 118: (255, 255, 0), 119: (221, 160, 221), 120: (221, 160, 221), 121: (0, 238, 0), 122: (0, 238, 0), 123: (205, 92, 92), 124: (205, 92, 92), 125: (176, 48, 96), 126: (176, 48, 96), 129: (152, 251, 152), 130: (152, 251, 152), 133: (50, 205, 50), 134: (50, 205, 50), 135: (0, 100, 0), 136: (0, 100, 0), 137: (173, 216, 230), 138: (173, 216, 230), 139: (153, 50, 204), 140: (153, 50, 204), 141: (160, 32, 240), 142: (160, 32, 240), 143: (0, 206, 208), 144: (0, 206, 208), 145: (51, 50, 135), 146: (51, 50, 135), 147: (135, 50, 74), 148: (135, 50, 74), 149: (218, 112, 214), 150: (218, 112, 214), 151: (240, 230, 140), 152: (240, 230, 140), 153: (255, 255, 0), 154: (255, 255, 0), 155: (255, 110, 180), 156: (255, 110, 180), 157: (0, 255, 255), 158: (0, 255, 255), 161: (100, 50, 100), 162: (100, 50, 100), 163: (178, 34, 34), 164: (178, 34, 34), 165: (255, 0, 255), 166: (255, 0, 255), 167: (39, 64, 139), 168: (39, 64, 139), 169: (255, 99, 71), 170: (255, 99, 71), 171: (255, 69, 0), 172: (255, 69, 0), 173: (210, 180, 140), 174: (210, 180, 140), 175: (0, 255, 127), 176: (0, 255, 127), 177: (74, 155, 60), 178: (74, 155, 60), 179: (255, 215, 0), 180: (255, 215, 0), 181: (238, 0, 0), 182: (238, 0, 0), 183: (46, 139, 87), 184: (46, 139, 87), 185: (238, 201, 0), 186: (238, 201, 0), 187: (102, 205, 170), 188: (102, 205, 170), 191: (255, 218, 185), 192: (255, 218, 185), 193: (238, 130, 238), 194: (238, 130, 238), 195: (255, 165, 0), 196: (255, 165, 0), 197: (255, 192, 203), 198: (255, 192, 203), 199: (244, 222, 179), 200: (244, 222, 179), 201: (208, 32, 144), 202: (208, 32, 144), 203: (34, 139, 34), 204: (34, 139, 34), 205: (125, 255, 212), 206: (127, 255, 212), 207: (0, 0, 128), 208: (0, 0, 128)}

def plot(self, *args, **kwargs):
    super().plot(*args, **kwargs, cmap_dict={'seg': self.gif_colors})

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
@contextmanager
def _use_seed(seed):
    """Perform an operation using a specific seed for the PyTorch RNG."""
    torch_rng_state = torch.random.get_rng_state()
    torch.manual_seed(seed)
    yield
    torch.random.set_rng_state(torch_rng_state)

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

def test_apply_transform_to_file(self):
    transform = tio.RandomFlip()
    tio.utils.apply_transform_to_file(self.get_image_path('input'), transform, self.get_image_path('output'), verbose=True)

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

def test_queue(self):
    self.run_queue(num_workers=0)

@pytest.mark.skipif(sys.platform == 'darwin', reason='Takes too long on macOS')
def test_queue_multiprocessing(self):
    self.run_queue(num_workers=2)

def test_queue_no_start_background(self):
    self.run_queue(num_workers=0, start_background=False)

def test_get_memory_string(self):
    queue = self.run_queue()
    memory_string = queue.get_max_memory_pretty()
    assert isinstance(memory_string, str)

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

@pytest.mark.skipif(sys.platform == 'win32', reason='Path not valid')
def test_wrong_path_value(self):
    with pytest.raises(RuntimeError):
        tio.ScalarImage('~&./@#"!?X7=+')

@pytest.mark.slow
@pytest.mark.skipif(sys.platform == 'win32', reason='Unstable on Windows')
def test_plot(self):
    image = self.sample_subject.t1
    image.plot(show=False, output_path=self.dir / 'image.png')

