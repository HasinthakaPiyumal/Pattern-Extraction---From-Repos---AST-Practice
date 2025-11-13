# Cluster 30

def floordiv(dividend, divisor, rounding_mode='trunc'):
    if _torch_version_div_indexing:
        return torch.div(dividend, divisor, rounding_mode=rounding_mode)
    else:
        return dividend // divisor

