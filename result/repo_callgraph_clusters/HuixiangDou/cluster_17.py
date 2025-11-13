# Cluster 17

class DistanceStrategy(str, Enum):
    """Enumerator of the Distance strategies for calculating distances
    between vectors."""
    EUCLIDEAN_DISTANCE = 'EUCLIDEAN_DISTANCE'
    MAX_INNER_PRODUCT = 'MAX_INNER_PRODUCT'
    UNKNOWN = 'UNKNOWN'

    @staticmethod
    def euclidean_relevance_score_fn(distance: float) -> float:
        """Return a similarity score on a scale [0, 1]."""
        return 1.0 - distance / math.sqrt(2)

    @staticmethod
    def max_inner_product_relevance_score_fn(similarity: float) -> float:
        """Normalize the distance to a score on a scale [0, 1]."""
        return similarity

@staticmethod
def euclidean_relevance_score_fn(distance: float) -> float:
    """Return a similarity score on a scale [0, 1]."""
    return 1.0 - distance / math.sqrt(2)

