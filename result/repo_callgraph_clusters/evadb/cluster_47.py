# Cluster 47

def get_gpu_count() -> int:
    """
    Check number of GPUs through Torch.
    """
    try:
        import torch
        return torch.cuda.device_count()
    except ImportError:
        return 0

