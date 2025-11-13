# Cluster 20

def _is_tarxz(filename):
    return filename.endswith('.tar.xz')

def _is_tar(filename):
    return filename.endswith('.tar')

def _is_targz(filename):
    return filename.endswith('.tar.gz')

def _is_tgz(filename):
    return filename.endswith('.tgz')

def _is_gzip(filename):
    return filename.endswith('.gz') and (not filename.endswith('.tar.gz'))

def _is_zip(filename):
    return filename.endswith('.zip')

