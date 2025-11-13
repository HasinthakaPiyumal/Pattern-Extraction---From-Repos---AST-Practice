# Cluster 37

class TestLidar(unittest.TestCase):
    """Test class Lidar"""

    def setUp(self) -> None:
        """
        Initializes a test Lidar
        """
        self.lidar = get_test_nuplan_lidar()

    @patch('nuplan.database.nuplan_db_orm.lidar.inspect', autospec=True)
    def test_session(self, inspect: Mock) -> None:
        """
        Tests _session method
        """
        mock_session = PropertyMock()
        inspect.return_value = Mock()
        inspect.return_value.session = mock_session
        result = self.lidar._session()
        inspect.assert_called_once_with(self.lidar)
        mock_session.assert_called_once()
        self.assertEqual(result, mock_session.return_value)

    @patch('nuplan.database.nuplan_db_orm.lidar.simple_repr', autospec=True)
    def test_repr(self, simple_repr: Mock) -> None:
        """
        Tests string representation
        """
        result = self.lidar.__repr__()
        simple_repr.assert_called_once_with(self.lidar)
        self.assertEqual(result, simple_repr.return_value)

    @patch('nuplan.database.nuplan_db_orm.lidar.np.array', autospec=True)
    def test_translation_np(self, np_array: Mock) -> None:
        """
        Test property - translation.
        """
        result = self.lidar.translation_np
        np_array.assert_called_once_with(self.lidar.translation)
        self.assertEqual(result, np_array.return_value)

    def test_quaternion(self) -> None:
        """
        Test property - rotation in quaternion.
        """
        result = self.lidar.quaternion
        np.testing.assert_array_equal(self.lidar.rotation, result.elements)

    def test_trans_matrix_and_inv(self) -> None:
        """
        Test two properties - transformation matrix and its inverse.
        """
        trans_mat = self.lidar.trans_matrix
        inv_trans_mat = self.lidar.trans_matrix_inv
        np.testing.assert_allclose(trans_mat @ inv_trans_mat, np.eye(4), atol=0.001)

def setUp(self) -> None:
    """
        Initializes a test Lidar
        """
    self.lidar = get_test_nuplan_lidar()

