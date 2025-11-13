# Cluster 13

class TestImageExistsValidator(unittest.TestCase):
    """Tests for the ImageExistsValidator"""

    def setUp(self) -> None:
        """Sets variables for testing"""
        self.validator = ImageExistsValidator()

    def test_construction(self) -> None:
        """Tests that the variables are initialized correctly."""
        self.assertTrue(isinstance(self.validator, BaseSubmissionValidator))

    @patch('docker.from_env')
    def test_validate(self, mock_env: Mock) -> None:
        """Tests that the validator behaves as intended"""
        missing_submission = 'foo'
        present_submission = 'bar'
        mock_env.return_value.images.list.return_value = ['bar', 'b']
        self.assertEqual(False, self.validator.validate(missing_submission))
        with patch.object(BaseSubmissionValidator, 'validate') as mock_validate:
            self.validator.validate(present_submission)
            mock_validate.assert_called_with(present_submission)

def setUp(self) -> None:
    """Sets variables for testing"""
    self.validator = ImageExistsValidator()

