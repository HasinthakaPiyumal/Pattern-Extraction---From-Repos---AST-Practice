# Cluster 23

def write_image(tensor: torch.Tensor, affine: TypeData, path: TypePath, squeeze: bool | None=None) -> None:
    args = (tensor, affine, path)
    try:
        _write_sitk(*args, squeeze=squeeze)
    except RuntimeError:
        _write_nibabel(*args)

