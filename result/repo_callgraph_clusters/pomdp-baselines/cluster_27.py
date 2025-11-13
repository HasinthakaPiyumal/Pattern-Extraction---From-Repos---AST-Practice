# Cluster 27

def func_wrapper(*args, **kwargs):
    with ProfileKV(n):
        return func(*args, **kwargs)

