# Cluster 17

def get_transformation_matrix(M, dsize):
    """
    Return transformation matrix for torch.affine_grid.
    Args:
        M : torch.Tensor
            Transformation matrix with shape :math:`(N, 2, 3)`.
        dsize : Tuple[int, int]
            Size of the source image (height, width).

    Returns:
        T : torch.Tensor
            Transformation matrix with shape :math:`(N, 2, 3)`.
    """
    T = get_rotation_matrix2d(M, dsize)
    T[..., 2] += M[..., 2]
    return T

