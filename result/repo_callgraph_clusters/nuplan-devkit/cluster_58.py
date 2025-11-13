# Cluster 58

def assert_functions_swappable(first_func: Callable[..., Any], second_func: Callable[..., Any]) -> None:
    """
    Asserts that a second function is swappable for the supplied first function.
    "Swappable" means that they contain the same arguments, same default arguments, and same return type.
    :param first_func: The first func that is being replaced.
    :param second_func: The second func that is being replaced.
    """
    _assert_function_signature_types_match(first_func, second_func)
    _assert_function_defaults_match(first_func, second_func)
    _assert_function_kwdefaults_match(first_func, second_func)

