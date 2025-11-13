# Cluster 39

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

def test_matrix_itk(self):
    self.write_read_matrix('.tfm')
    self.write_read_matrix('.h5')

def test_matrix_txt(self):
    self.write_read_matrix('.txt')

