# Cluster 57

def complex_method(x: int, y: int) -> int:
    """
    A mock complex method to use with the patch tests.
    :param x: One input parameter.
    :param y: The other input parameter.
    :return: The output.
    """
    xx = base_method(x)
    return xx * y

