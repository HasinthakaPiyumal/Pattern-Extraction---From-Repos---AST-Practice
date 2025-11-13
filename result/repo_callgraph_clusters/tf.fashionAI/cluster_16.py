# Cluster 16

def _asdict(namedtuple):
    """Returns a namedtuple as a dictionary.

  This is required because `_asdict()` in Python 3.x.x is broken in classes
  that inherit from `collections.namedtuple`. See
  https://bugs.python.org/issue24931 for more details.

  Args:
    namedtuple: An object that inherits from `collections.namedtuple`.

  Returns:
    A dictionary version of the tuple.
  """
    return {k: getattr(namedtuple, k) for k in namedtuple._fields}

