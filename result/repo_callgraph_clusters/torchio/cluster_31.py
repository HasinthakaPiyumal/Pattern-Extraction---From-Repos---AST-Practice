# Cluster 31

def _check_and_import(module: str, extra: str, **kwargs) -> ModuleType:
    _check_module(module=module, extra=extra, **kwargs)
    return import_module(module)

