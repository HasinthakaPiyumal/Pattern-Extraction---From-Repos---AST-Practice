# Cluster 81

class TestSerializationCallbackMsgpack(SkeletonTestSerializationCallback):
    """Tests that SerializationCallback works correctly for msgpack format."""

    def setUp(self) -> None:
        """Will be called before every test"""
        self._serialization_type = 'msgpack'
        self._setUp()

    def test_serialization_callback(self) -> None:
        """Tests that we can correctly serialize data to msgpack format."""
        self._dump_test_scenario()

def setUp(self) -> None:
    """Will be called before every test"""
    self._serialization_type = 'msgpack'
    self._setUp()

class TestSerializationCallbackJson(SkeletonTestSerializationCallback):
    """Tests that SerializationCallback works correctly for JSON format."""

    def setUp(self) -> None:
        """Will be called before every test"""
        self._serialization_type = 'json'
        self._setUp()

    def test_serialization_callback(self) -> None:
        """Tests that we can correctly serialize data to JSON format."""
        self._dump_test_scenario()

def setUp(self) -> None:
    """Will be called before every test"""
    self._serialization_type = 'json'
    self._setUp()

class TestSerializationCallbackPickle(SkeletonTestSerializationCallback):
    """Tests that SerializationCallback works correctly for pickle format."""

    def setUp(self) -> None:
        """Will be called before every test"""
        self._serialization_type = 'pickle'
        self._setUp()

    def test_serialization_callback(self) -> None:
        """Tests that we can correctly serialize data to pickle format."""
        self._dump_test_scenario()

def setUp(self) -> None:
    """Will be called before every test"""
    self._serialization_type = 'pickle'
    self._setUp()

