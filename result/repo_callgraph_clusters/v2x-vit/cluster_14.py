# Cluster 14

def normalize_homography(dst_pix_trans_src_pix, dsize_src, dsize_dst=None):
    """
    Normalize a given homography in pixels to [-1, 1].
    Args:
        dst_pix_trans_src_pix : torch.Tensor
            Homography/ies from source to destination to be normalized with
            shape :math:`(B, 3, 3)`.
        dsize_src : Tuple[int, int]
            Size of the source image (height, width).
        dsize_dst : Tuple[int, int]
            Size of the destination image (height, width).

    Returns:
        dst_norm_trans_src_norm : torch.Tensor
            The normalized homography of shape :math:`(B, 3, 3)`.
    """
    if dsize_dst is None:
        dsize_dst = dsize_src
    src_h, src_w = dsize_src
    dst_h, dst_w = dsize_dst
    device = dst_pix_trans_src_pix.device
    dtype = dst_pix_trans_src_pix.dtype
    src_norm_trans_src_pix = normal_transform_pixel(src_h, src_w, device, dtype).to(dst_pix_trans_src_pix)
    src_pix_trans_src_norm = _torch_inverse_cast(src_norm_trans_src_pix)
    dst_norm_trans_dst_pix = normal_transform_pixel(dst_h, dst_w, device, dtype).to(dst_pix_trans_src_pix)
    dst_norm_trans_src_norm: torch.Tensor = dst_norm_trans_dst_pix @ (dst_pix_trans_src_pix @ src_pix_trans_src_norm)
    return dst_norm_trans_src_norm

def warp_affine(src, M, dsize, mode='bilinear', padding_mode='zeros', align_corners=True):
    """
    Transform the src based on transformation matrix M.
    Args:
        src : torch.Tensor
            Input feature map with shape :math:`(B,C,H,W)`.
        M : torch.Tensor
            Transformation matrix with shape :math:`(B,2,3)`.
        dsize : tuple
            Tuple of output image H_out and W_out.
        mode : str
            Interpolation methods for F.grid_sample.
        padding_mode : str
            Padding methods for F.grid_sample.
        align_corners : boolean
            Parameter of F.affine_grid.

    Returns:
        Transformed features with shape :math:`(B,C,H,W)`.
    """
    B, C, H, W = src.size()
    M_3x3 = convert_affinematrix_to_homography(M)
    dst_norm_trans_src_norm = normalize_homography(M_3x3, (H, W), dsize)
    src_norm_trans_dst_norm = _torch_inverse_cast(dst_norm_trans_src_norm)
    grid = F.affine_grid(src_norm_trans_dst_norm[:, :2, :], [B, C, dsize[0], dsize[1]], align_corners=align_corners)
    return F.grid_sample(src.half() if grid.dtype == torch.half else src, grid, align_corners=align_corners, mode=mode, padding_mode=padding_mode)

