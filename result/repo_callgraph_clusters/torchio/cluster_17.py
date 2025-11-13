# Cluster 17

def check_md5(fpath, md5, **kwargs):
    return md5 == calculate_md5(fpath, **kwargs)

