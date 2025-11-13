# Cluster 10

def get_noise(tensor: torch.Tensor, mean: float, std: float) -> torch.Tensor:
    return torch.randn(*tensor.shape) * std + mean

class LabelsToImage(IntensityTransform):
    """Generate an image from a segmentation.

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
            If not ``None`` and :attr:`label_channels` is not ``None``,
            :attr:`mean` and :attr:`label_channels` must have the
            same length.
        std: Sequence of standard deviations for each label.
            If not ``None`` and :attr:`label_channels` is not ``None``,
            :attr:`std` and :attr:`label_channels` must have the
            same length.
        discretize: If ``True``, partial-volume label maps will be discretized.
            Does not have any effects if not using partial-volume label maps.
            Discretization is done taking the class of the highest value per
            voxel in the different partial-volume label maps using
            :func:`torch.argmax()` on the channel dimension (i.e. 0).
        ignore_background: If ``True``, input voxels labeled as ``0`` will not
            be modified.
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.

    .. note:: It is recommended to blur the new images to make the result more
        realistic. See
        :class:`~torchio.transforms.augmentation.RandomBlur`.
    """

    def __init__(self, label_key: str, mean: Sequence[float] | None, std: Sequence[float] | None, image_key: str='image_from_labels', used_labels: Sequence[int] | None=None, ignore_background: bool=False, discretize: bool=False, **kwargs):
        super().__init__(**kwargs)
        self.label_key = _parse_label_key(label_key)
        self.used_labels = _parse_used_labels(used_labels)
        self.mean, self.std = (mean, std)
        self.image_key = image_key
        self.ignore_background = ignore_background
        self.discretize = discretize
        self.args_names = ['label_key', 'mean', 'std', 'image_key', 'used_labels', 'ignore_background', 'discretize']

    def apply_transform(self, subject: Subject) -> Subject:
        original_image = subject.get(self.image_key)
        label_map_image = subject[self.label_key]
        label_map = label_map_image.data
        affine = label_map_image.affine
        all_discrete = label_map.eq(label_map.float().round()).all()
        same_num_dims = label_map.squeeze().dim() < label_map.dim()
        is_discretized = all_discrete and same_num_dims
        if not is_discretized and self.discretize:
            max_label, label_map = label_map.max(dim=0, keepdim=True)
            label_map[max_label == 0] = -1
            is_discretized = True
        tissues = torch.zeros(1, *label_map_image.spatial_shape).float()
        if is_discretized:
            labels_in_image = label_map.unique().long().tolist()
            if -1 in labels_in_image:
                labels_in_image.remove(-1)
        else:
            labels_in_image = range(label_map.shape[0])
        _check_mean_and_std_length(labels_in_image, self.mean, self.std)
        for i, label in enumerate(labels_in_image):
            if label == 0 and self.ignore_background:
                continue
            if self.used_labels is None or label in self.used_labels:
                assert isinstance(self.mean, Sequence)
                assert isinstance(self.std, Sequence)
                mean = self.mean[i]
                std = self.std[i]
                if is_discretized:
                    mask = label_map == label
                else:
                    mask = label_map[label]
                tissues += self.generate_tissue(mask, mean, std)
            elif is_discretized:
                label_map[label_map == label] = -1
            else:
                label_map[label] = 0
        final_image = ScalarImage(affine=affine, tensor=tissues)
        if original_image is not None:
            if is_discretized:
                bg_mask = label_map == -1
            else:
                bg_mask = label_map.sum(dim=0, keepdim=True) < 0.5
            final_image.data[bg_mask] = original_image.data[bg_mask].float()
        subject.add_image(final_image, self.image_key)
        return subject

    @staticmethod
    def generate_tissue(data: TypeData, mean: float, std: float) -> TypeData:
        gaussian = torch.randn(data.shape) * std + mean
        return gaussian * data

@staticmethod
def generate_tissue(data: TypeData, mean: float, std: float) -> TypeData:
    gaussian = torch.randn(data.shape) * std + mean
    return gaussian * data

class OneHot(LabelTransform):
    """Reencode label maps using one-hot encoding.

    Args:
        num_classes: See :func:`~torch.nn.functional.one_hot`.
        **kwargs: See :class:`~torchio.transforms.Transform` for additional
            keyword arguments.
    """

    def __init__(self, num_classes: int=-1, **kwargs):
        super().__init__(**kwargs)
        self.num_classes = num_classes
        self.args_names = ['num_classes']
        self.invert_transform = False

    def apply_transform(self, subject):
        for image in self.get_images(subject):
            if self.invert_transform:
                self.argmax(image)
            else:
                self.one_hot(image)
        return subject

    @staticmethod
    def argmax(image: Image) -> None:
        data = image.data.argmax(dim=0, keepdim=True)
        image.set_data(data)

    def one_hot(self, image: Image) -> None:
        if image.num_channels > 1:
            message = f'The number of input channels must be 1, but it is {image.num_channels}'
            raise RuntimeError(message)
        data = image.data[0]
        num_classes = -1 if self.num_classes is None else self.num_classes
        one_hot = F.one_hot(data.long(), num_classes=num_classes)
        image.set_data(one_hot.permute(3, 0, 1, 2).type(data.type()))

def apply_transform(self, subject):
    for image in self.get_images(subject):
        if self.invert_transform:
            self.argmax(image)
        else:
            self.one_hot(image)
    return subject

@staticmethod
def argmax(image: Image) -> None:
    data = image.data.argmax(dim=0, keepdim=True)
    image.set_data(data)

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

def get_ixi_tiny(self):
    root_dir = Path(tempfile.gettempdir()) / 'torchio' / 'ixi_tiny'
    return tio.datasets.IXITiny(root_dir, download=True)

@pytest.mark.parametrize(('save_lib', 'load_lib', 'dims'), parameters)
def test_write_nd_with_a_read_it_with_b(save_lib, load_lib, dims):
    shape = [1, 4, 5, 6]
    if dims == 2:
        shape[-1] = 1
    elif dims == 4:
        shape[0] = 2
    tensor = torch.randn(*shape)
    affine = np.eye(4)
    tempdir = Path(tempfile.gettempdir()) / '.torchio_tests'
    tempdir.mkdir(exist_ok=True)
    path = tempdir / 'test_io.nii'
    save_function = getattr(io, f'_write_{save_lib}')
    load_function = getattr(io, f'_read_{save_lib}')
    save_function(tensor, affine, path)
    loaded_tensor, loaded_affine = load_function(path)
    TorchioTestCase.assert_tensor_equal(tensor.squeeze(), loaded_tensor.squeeze(), msg=f'Save lib: {save_lib}; load lib: {load_lib}; dims: {dims}', check_stride=False)
    TorchioTestCase.assert_tensor_equal(affine, loaded_affine)

class TestIXI(TorchioTestCase):
    """Tests for `ixi` module."""

    def test_not_downloaded(self):
        with pytest.raises(RuntimeError):
            tio.datasets.IXI('testing123', download=False)

    def test_tiny_not_downloaded(self):
        with pytest.raises(RuntimeError):
            tio.datasets.IXITiny('testing123', download=False)

def test_tiny_not_downloaded(self):
    with pytest.raises(RuntimeError):
        tio.datasets.IXITiny('testing123', download=False)

@pytest.mark.slow
@pytest.mark.skipif('CI' in os.environ, reason='Unstable on GitHub Actions')
@pytest.mark.parametrize('class_', classes)
@pytest.mark.parametrize('split', ('train', 'val', 'test'))
def test_load_all(class_, split):
    dataset = class_(split)
    loader = tio.SubjectsLoader(dataset, batch_size=256)
    for _ in loader:
        pass

@pytest.mark.parametrize('original_labels', ((0,), (0, 1), (0, 1, 2), (0, 2), (0, 4, 8), (1,), (1, 2), (3, 5, 9, 15, 16, 23), (0, 3, 5, 9, 15, 16, 23), (2, 8, 9, 10, 15, 20, 100), (0, 2, 8, 9, 10, 15, 20, 100)))
def test_sequential(original_labels):
    remap_labels = tio.SequentialLabels()
    tensor = TorchioTestCase.get_tensor_with_labels(original_labels)
    subject = tio.Subject(label=tio.LabelMap(tensor=tensor))
    transformed = remap_labels(subject)
    for i, label in enumerate(original_labels):
        original_mask = tensor == label
        new_mask = transformed.label.data == i
        TorchioTestCase.assert_tensor_equal(original_mask, new_mask)
    inverted = transformed.apply_inverse_transform()
    TorchioTestCase.assert_tensor_equal(tensor, inverted.label.data)

class TestRemoveLabels(TorchioTestCase):
    """Tests for `RemoveLabels`."""

    def test_remove(self):
        original_labels = (1, 2, 3, 4, 5, 6, 7)
        labels_to_remove = (1, 2, 5, 6)
        remaining_labels = (3, 4, 7)
        remove_labels = tio.RemoveLabels(labels_to_remove)
        tensor = TorchioTestCase.get_tensor_with_labels(original_labels)
        subject = tio.Subject(label=tio.LabelMap(tensor=tensor))
        transformed = remove_labels(subject)
        for removed_label in labels_to_remove:
            original_mask = subject.label.data == removed_label
            new_values = transformed.label.data[original_mask]
            self.assert_tensor_all_zeros(new_values)
        for remaining_label in remaining_labels:
            original_mask = subject.label.data == remaining_label
            original_values = subject.label.data[original_mask]
            output_values = transformed.label.data[original_mask]
            self.assert_tensor_equal(original_values, output_values)

def test_remove(self):
    original_labels = (1, 2, 3, 4, 5, 6, 7)
    labels_to_remove = (1, 2, 5, 6)
    remaining_labels = (3, 4, 7)
    remove_labels = tio.RemoveLabels(labels_to_remove)
    tensor = TorchioTestCase.get_tensor_with_labels(original_labels)
    subject = tio.Subject(label=tio.LabelMap(tensor=tensor))
    transformed = remove_labels(subject)
    for removed_label in labels_to_remove:
        original_mask = subject.label.data == removed_label
        new_values = transformed.label.data[original_mask]
        self.assert_tensor_all_zeros(new_values)
    for remaining_label in remaining_labels:
        original_mask = subject.label.data == remaining_label
        original_values = subject.label.data[original_mask]
        output_values = transformed.label.data[original_mask]
        self.assert_tensor_equal(original_values, output_values)

@pytest.mark.parametrize('original_label_set', ({0}, {0, 1}, {0, 1, 2}, {0, 2}, {1, 2, 5, 6}))
@pytest.mark.parametrize('remapping', ({}, {0: 10}, {0: 10, 1: 11, 2: 12}, {0: 1}, {0: 1, 1: 0}, {0: 1, 1: 2, 2: 0}, {2: 1, 5: 1}, {3: 4}, {3: 1}, {1: 2, 2: 1, 5: 10, 6: 11}))
def test_remap(original_label_set, remapping):
    source_label_set = set(remapping.keys())
    target_label_set = set(remapping.values())
    remap_labels = tio.RemapLabels(remapping=remapping)
    tensor = TorchioTestCase.get_tensor_with_labels(original_label_set)
    subject = tio.Subject(label=tio.LabelMap(tensor=tensor))
    transformed = remap_labels(subject)
    new_label_set = TorchioTestCase.get_unique_labels(transformed.label.data)
    if source_label_set.intersection(original_label_set):
        assert new_label_set.intersection(target_label_set)
    else:
        assert new_label_set == original_label_set
    if len(target_label_set) < len(remapping.keys()):
        with pytest.raises(RuntimeError):
            _ = transformed.apply_inverse_transform()
    else:
        inverse_data = transformed.apply_inverse_transform().label.data
        inverted_label_set = TorchioTestCase.get_unique_labels(inverse_data)
        if target_label_set.isdisjoint(original_label_set):
            assert inverted_label_set == original_label_set

class TestOneHot(TorchioTestCase):
    """Tests for `OneHot`."""

    def test_one_hot(self):
        image = self.sample_subject.label
        one_hot = tio.OneHot(num_classes=3)(image)
        assert one_hot.num_channels == 3

    def test_multichannel(self):
        label_map = tio.LabelMap(tensor=torch.rand(2, 3, 3, 3) > 1)
        with pytest.raises(RuntimeError):
            tio.OneHot()(label_map)

    def test_inverse(self):
        one_hot = tio.OneHot()
        subject_one_hot = one_hot(self.sample_subject)
        subject_back = subject_one_hot.apply_inverse_transform()
        self.assert_tensor_equal(self.sample_subject.label.data, subject_back.label.data)

def test_one_hot(self):
    image = self.sample_subject.label
    one_hot = tio.OneHot(num_classes=3)(image)
    assert one_hot.num_channels == 3

def test_inverse(self):
    one_hot = tio.OneHot()
    subject_one_hot = one_hot(self.sample_subject)
    subject_back = subject_one_hot.apply_inverse_transform()
    self.assert_tensor_equal(self.sample_subject.label.data, subject_back.label.data)

