# Cluster 10

class TestSubmissionValidator(unittest.TestCase):
    """Tests for the BaseSubmissionValidator class"""

    def setUp(self) -> None:
        """Sets variables for testing"""
        self.validator = BaseSubmissionValidator()

    def test_construction(self) -> None:
        """Tests that the variables are initialized correctly."""
        self.assertEqual(None, self.validator._next_validator)
        self.assertEqual(None, self.validator.failing_validator)

    def test_set_next(self) -> None:
        """Tests that assigning the next validator works."""
        next_validator = Mock()
        self.validator.set_next(next_validator)
        self.assertEqual(next_validator, self.validator._next_validator)

    def test_validate(self) -> None:
        """Tests that base validator works, and that validators are called in chain."""
        self.assertTrue(self.validator.validate(Mock()))
        validate = Mock(return_value=False)
        next_validator = Mock(validate=validate)
        self.validator._next_validator = next_validator
        result = self.validator.validate(Mock())
        validate.assert_called_once()
        self.assertEqual(validate.return_value, result)

def setUp(self) -> None:
    """Sets variables for testing"""
    self.validator = BaseSubmissionValidator()

