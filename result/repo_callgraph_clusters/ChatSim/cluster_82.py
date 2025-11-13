# Cluster 82

class BaseDataset:
    """Base class for all datasets."""

    def __init__(self):
        self.env_settings = env_settings()

    def __len__(self):
        """Overload this function in your dataset. This should return number of sequences in the dataset."""
        raise NotImplementedError

    def get_sequence_list(self):
        """Overload this in your dataset. Should return the list of sequences in the dataset."""
        raise NotImplementedError

def __init__(self):
    self.env_settings = env_settings()

