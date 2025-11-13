# Cluster 35

class TestTrack(unittest.TestCase):
    """Test class Track"""

    def setUp(self) -> None:
        """
        Initializes a test Track
        """
        self.track = get_test_nuplan_track()

    @patch('nuplan.database.nuplan_db_orm.track.inspect', autospec=True)
    def test_session(self, inspect: Mock) -> None:
        """
        Tests _session method
        """
        mock_session = PropertyMock()
        inspect.return_value = Mock()
        inspect.return_value.session = mock_session
        result = self.track._session()
        inspect.assert_called_once_with(self.track)
        mock_session.assert_called_once()
        self.assertEqual(result, mock_session.return_value)

    @patch('nuplan.database.nuplan_db_orm.track.simple_repr', autospec=True)
    def test_repr(self, simple_repr: Mock) -> None:
        """
        Tests string representation
        """
        result = self.track.__repr__()
        simple_repr.assert_called_once_with(self.track)
        self.assertEqual(result, simple_repr.return_value)

    def test_nbr_lidar_boxes(self) -> None:
        """
        Tests property - number of boxes along the track.
        """
        result = self.track.nbr_lidar_boxes
        self.assertGreater(result, 0)
        self.assertIsInstance(result, int)

    def test_first_last_lidar_box(self) -> None:
        """
        Tests properties - first and last lidar box along the track.
        """
        first_lidar_box = self.track.first_lidar_box
        last_lidar_box = self.track.last_lidar_box
        self.assertGreaterEqual(last_lidar_box.timestamp, first_lidar_box.timestamp)

    @patch('nuplan.database.nuplan_db_orm.track.Track.first_lidar_box', autospec=True)
    @patch('nuplan.database.nuplan_db_orm.track.Track.last_lidar_box', autospec=True)
    def test_duration(self, mock_last_box: Mock, mock_first_box: Mock) -> None:
        """
        Tests property - duration of Track.
        """
        mock_first_box.timestamp = 1000
        mock_last_box.timestamp = 5000
        result = self.track.duration
        self.assertEqual(result, 4000)

    def test_distances_to_ego(self) -> None:
        """
        Tests property - distances of all boxes in the track from ego vehicle.
        """
        result = self.track.distances_to_ego
        self.assertEqual(len(result), self.track.nbr_lidar_boxes)

    def test_min_max_distance_to_ego(self) -> None:
        """
        Tests two properties - min and max distance to ego
        """
        min_result = self.track.min_distance_to_ego
        max_result = self.track.max_distance_to_ego
        self.assertGreaterEqual(max_result, min_result)

def setUp(self) -> None:
    """
        Initializes a test Track
        """
    self.track = get_test_nuplan_track()

