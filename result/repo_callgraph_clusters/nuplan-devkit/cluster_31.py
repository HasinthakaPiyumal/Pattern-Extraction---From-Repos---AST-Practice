# Cluster 31

class TestCamera(unittest.TestCase):
    """Test class Camera"""

    def setUp(self) -> None:
        """
        Initializes a test Camera
        """
        self.camera = get_test_nuplan_camera()

    @patch('nuplan.database.nuplan_db_orm.camera.inspect', autospec=True)
    def test_session(self, inspect: Mock) -> None:
        """
        Tests _session method
        """
        mock_session = PropertyMock()
        inspect.return_value = Mock()
        inspect.return_value.session = mock_session
        result = self.camera._session()
        inspect.assert_called_once_with(self.camera)
        mock_session.assert_called_once()
        self.assertEqual(result, mock_session.return_value)

    @patch('nuplan.database.nuplan_db_orm.camera.simple_repr', autospec=True)
    def test_repr(self, simple_repr: Mock) -> None:
        """
        Tests string representation
        """
        result = self.camera.__repr__()
        simple_repr.assert_called_once_with(self.camera)
        self.assertEqual(result, simple_repr.return_value)

    @patch('nuplan.database.nuplan_db_orm.camera.np.array', autospec=True)
    def test_intrinsic_np(self, np_array: Mock) -> None:
        """
        Test property - camera intrinsic.
        """
        result = self.camera.intrinsic_np
        np_array.assert_called_once_with(self.camera.intrinsic)
        self.assertEqual(result, np_array.return_value)

    @patch('nuplan.database.nuplan_db_orm.camera.np.array', autospec=True)
    def test_distortion_np(self, np_array: Mock) -> None:
        """
        Test property - camera distrotion.
        """
        result = self.camera.distortion_np
        np_array.assert_called_once_with(self.camera.distortion)
        self.assertEqual(result, np_array.return_value)

    @patch('nuplan.database.nuplan_db_orm.camera.np.array', autospec=True)
    def test_translation_np(self, np_array: Mock) -> None:
        """
        Test property - translation.
        """
        result = self.camera.translation_np
        np_array.assert_called_once_with(self.camera.translation)
        self.assertEqual(result, np_array.return_value)

    def test_quaternion(self) -> None:
        """
        Test property - rotation in quaternion.
        """
        result = self.camera.quaternion
        np.testing.assert_array_equal(self.camera.rotation, result.elements)

    def test_trans_matrix_and_inv(self) -> None:
        """
        Test two properties - transformation matrix and its inverse.
        """
        trans_mat = self.camera.trans_matrix
        inv_trans_mat = self.camera.trans_matrix_inv
        np.testing.assert_allclose(trans_mat @ inv_trans_mat, np.eye(4), atol=0.001)

def setUp(self) -> None:
    """
        Initializes a test Camera
        """
    self.camera = get_test_nuplan_camera()

