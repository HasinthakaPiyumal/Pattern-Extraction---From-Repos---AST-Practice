# Cluster 93

@dataclass
class MockFeature(AbstractModelFeature):
    """
    A simple implementation of the AbstractModelFeature interface to be used with unit tests.
    """
    data: torch.Tensor

    @classmethod
    def deserialize(cls, serialized: Dict[str, Any]) -> AbstractModelFeature:
        """Implemented. See interface."""
        return MockFeature(data=serialized['data'])

    def to_feature_tensor(self) -> AbstractModelFeature:
        """Implemented. See interface."""
        return self

    def to_device(self, device: torch.device) -> AbstractModelFeature:
        """Implemented. See interface."""
        return self

    def unpack(self) -> List[AbstractModelFeature]:
        """Implemented. See interface."""
        raise NotImplementedError

@classmethod
def deserialize(cls, serialized: Dict[str, Any]) -> AbstractModelFeature:
    """Implemented. See interface."""
    return MockFeature(data=serialized['data'])

class MockFeatureBuilder(AbstractFeatureBuilder, AbstractTargetBuilder):
    """
    A simple implementation of the AbstractFeatureBuilder and AbstractTargetBuilder interfaces to be used with unit tests.
    """

    def __init__(self, data_tensor: torch.Tensor):
        """
        The init method.
        :param data_tensor: The static data tensor to return from the get_features() methods.
        """
        self.data_tensor = data_tensor

    @classmethod
    def get_feature_type(self) -> Type[AbstractModelFeature]:
        """Implemented. See interface."""
        return MockFeature

    @classmethod
    def get_feature_unique_name(self) -> str:
        """Implemented. See interface."""
        return 'MockFeature'

    def get_features_from_scenario(self, scenario: AbstractScenario) -> MockFeature:
        """Implemented. See interface."""
        return MockFeature(data=self.data_tensor)

    def get_features_from_simulation(self, current_input: PlannerInput, initialization: PlannerInitialization) -> AbstractModelFeature:
        """Implemented. See interface."""
        raise NotImplementedError

    def get_targets(self, scenario: AbstractScenario) -> MockFeature:
        """Implemented. See interface."""
        return MockFeature(data=self.data_tensor)

def get_features_from_scenario(self, scenario: AbstractScenario) -> MockFeature:
    """Implemented. See interface."""
    return MockFeature(data=self.data_tensor)

def get_targets(self, scenario: AbstractScenario) -> MockFeature:
    """Implemented. See interface."""
    return MockFeature(data=self.data_tensor)

