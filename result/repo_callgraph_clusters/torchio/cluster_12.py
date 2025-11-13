# Cluster 12

def import_mpl_plt():
    try:
        import matplotlib as mpl
        import matplotlib.pyplot as plt
    except ImportError as e:
        raise ImportError('Install matplotlib for plotting support') from e
    return (mpl, plt)

def _check_module(*, module: str, extra: str, package: str | None=None) -> None:
    if find_spec(module) is None:
        name = module if package is None else package
        message = f'The `{name}` package is required for this. Install TorchIO with the `{extra}` extra: `pip install torchio[{extra}]`.'
        raise ImportError(message)

