# Cluster 78

def transform_vector_global_to_local_frame(vector: Tuple[float, float, float], theta: float) -> Tuple[float, float, float]:
    """
    Transform a vector from global frame to local frame.

    :param vector: the vector to be rotated
    :param theta: the amount to rotate by
    :return: the transformed vector.
    """
    return rotate_vector(vector, theta)

def transform_vector_local_to_global_frame(vector: Tuple[float, float, float], theta: float) -> Tuple[float, float, float]:
    """
    Transform a vector from local frame to global frame.

    :param vector: the vector to be rotated
    :param theta: the amount to rotate by
    :return: the transformed vector.
    """
    return rotate_vector(vector, theta, inverse=True)

