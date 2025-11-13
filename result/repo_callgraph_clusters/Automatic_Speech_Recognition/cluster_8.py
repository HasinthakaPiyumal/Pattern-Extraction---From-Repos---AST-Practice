# Cluster 8

def _get_complex(c_str):
    gewei = _get_gewei(c_str)
    shiwei = _get_shiwei(c_str)
    baiwei = _get_baiwei(c_str)
    qianwei = _get_qianwei(c_str)
    c_str = qianwei + baiwei + shiwei + gewei
    return c_str

