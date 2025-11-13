# Cluster 35

def quantize_flow(flow, max_val=0.02, norm=True):
    """Quantize flow to [0, 255].

    After this step, the size of flow will be much smaller, and can be
    dumped as jpeg images.

    Args:
        flow (ndarray): (h, w, 2) array of optical flow.
        max_val (float): Maximum value of flow, values beyond
                        [-max_val, max_val] will be truncated.
        norm (bool): Whether to divide flow values by image width/height.

    Returns:
        tuple[ndarray]: Quantized dx and dy.
    """
    h, w, _ = flow.shape
    dx = flow[..., 0]
    dy = flow[..., 1]
    if norm:
        dx = dx / w
        dy = dy / h
    flow_comps = [quantize(d, -max_val, max_val, 255, np.uint8) for d in [dx, dy]]
    return tuple(flow_comps)

