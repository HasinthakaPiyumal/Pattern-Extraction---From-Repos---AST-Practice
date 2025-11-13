# Cluster 40

@BBOX_CODERS.register_module()
class TBLRBBoxCoder(BaseBBoxCoder):
    """TBLR BBox coder.

    Following the practice in `FSAF <https://arxiv.org/abs/1903.00621>`_,
    this coder encodes gt bboxes (x1, y1, x2, y2) into (top, bottom, left,
    right) and decode it back to the original.

    Args:
        normalizer (list | float): Normalization factor to be
          divided with when coding the coordinates. If it is a list, it should
          have length of 4 indicating normalization factor in tblr dims.
          Otherwise it is a unified float factor for all dims. Default: 4.0
        clip_border (bool, optional): Whether clip the objects outside the
            border of the image. Defaults to True.
    """

    def __init__(self, normalizer=4.0, clip_border=True):
        super(BaseBBoxCoder, self).__init__()
        self.normalizer = normalizer
        self.clip_border = clip_border

    def encode(self, bboxes, gt_bboxes):
        """Get box regression transformation deltas that can be used to
        transform the ``bboxes`` into the ``gt_bboxes`` in the (top, left,
        bottom, right) order.

        Args:
            bboxes (torch.Tensor): source boxes, e.g., object proposals.
            gt_bboxes (torch.Tensor): target of the transformation, e.g.,
                ground truth boxes.

        Returns:
            torch.Tensor: Box transformation deltas
        """
        assert bboxes.size(0) == gt_bboxes.size(0)
        assert bboxes.size(-1) == gt_bboxes.size(-1) == 4
        encoded_bboxes = bboxes2tblr(bboxes, gt_bboxes, normalizer=self.normalizer)
        return encoded_bboxes

    def decode(self, bboxes, pred_bboxes, max_shape=None):
        """Apply transformation `pred_bboxes` to `boxes`.

        Args:
            bboxes (torch.Tensor): Basic boxes.Shape (B, N, 4) or (N, 4)
            pred_bboxes (torch.Tensor): Encoded boxes with shape
               (B, N, 4) or (N, 4)
            max_shape (Sequence[int] or torch.Tensor or Sequence[
               Sequence[int]],optional): Maximum bounds for boxes, specifies
               (H, W, C) or (H, W). If bboxes shape is (B, N, 4), then
               the max_shape should be a Sequence[Sequence[int]]
               and the length of max_shape should also be B.

        Returns:
            torch.Tensor: Decoded boxes.
        """
        decoded_bboxes = tblr2bboxes(bboxes, pred_bboxes, normalizer=self.normalizer, max_shape=max_shape, clip_border=self.clip_border)
        return decoded_bboxes

def decode(self, bboxes, pred_bboxes, max_shape=None):
    """Apply transformation `pred_bboxes` to `boxes`.

        Args:
            bboxes (torch.Tensor): Basic boxes.Shape (B, N, 4) or (N, 4)
            pred_bboxes (torch.Tensor): Encoded boxes with shape
               (B, N, 4) or (N, 4)
            max_shape (Sequence[int] or torch.Tensor or Sequence[
               Sequence[int]],optional): Maximum bounds for boxes, specifies
               (H, W, C) or (H, W). If bboxes shape is (B, N, 4), then
               the max_shape should be a Sequence[Sequence[int]]
               and the length of max_shape should also be B.

        Returns:
            torch.Tensor: Decoded boxes.
        """
    decoded_bboxes = tblr2bboxes(bboxes, pred_bboxes, normalizer=self.normalizer, max_shape=max_shape, clip_border=self.clip_border)
    return decoded_bboxes

