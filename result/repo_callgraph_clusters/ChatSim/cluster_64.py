# Cluster 64

def _erode_mask(mask: torch.Tensor, ekernel: torch.Tensor=None, eps: float=1e-08):
    """erode the mask, and set gray pixels to 0"""
    if ekernel is not None:
        mask = erosion(mask, ekernel)
        mask[mask >= 1.0 - eps] = 1
        mask[mask < 1.0 - eps] = 0
    return mask

def _erode_mask(mask: torch.Tensor, ekernel: torch.Tensor=None, eps: float=1e-08):
    """erode the mask, and set gray pixels to 0"""
    if ekernel is not None:
        mask = erosion(mask, ekernel)
        mask[mask >= 1.0 - eps] = 1
        mask[mask < 1.0 - eps] = 0
    return mask

