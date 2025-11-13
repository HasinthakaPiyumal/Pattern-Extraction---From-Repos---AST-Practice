# Cluster 32

def get_pandas() -> ModuleType:
    return _check_and_import(module='pandas', extra='csv')

def get_colorcet() -> ModuleType:
    return _check_and_import(module='colorcet', extra='plot')

def get_ffmpeg() -> ModuleType:
    ffmpeg = _check_and_import(module='ffmpeg', extra='video', package='ffmpeg-python')
    _check_executable('ffmpeg')
    return ffmpeg

def get_sklearn() -> ModuleType:
    return _check_and_import(module='sklearn', extra='sklearn', package='scikit-learn')

