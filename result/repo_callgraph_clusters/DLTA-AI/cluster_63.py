# Cluster 63

@HEADS.register_module()
class YOLACTSegmHead(BaseModule):
    """YOLACT segmentation head used in https://arxiv.org/abs/1904.02689.

    Apply a semantic segmentation loss on feature space using layers that are
    only evaluated during training to increase performance with no speed
    penalty.

    Args:
        in_channels (int): Number of channels in the input feature map.
        num_classes (int): Number of categories excluding the background
            category.
        loss_segm (dict): Config of semantic segmentation loss.
        init_cfg (dict or list[dict], optional): Initialization config dict.
    """

    def __init__(self, num_classes, in_channels=256, loss_segm=dict(type='CrossEntropyLoss', use_sigmoid=True, loss_weight=1.0), init_cfg=dict(type='Xavier', distribution='uniform', override=dict(name='segm_conv'))):
        super(YOLACTSegmHead, self).__init__(init_cfg)
        self.in_channels = in_channels
        self.num_classes = num_classes
        self.loss_segm = build_loss(loss_segm)
        self._init_layers()
        self.fp16_enabled = False

    def _init_layers(self):
        """Initialize layers of the head."""
        self.segm_conv = nn.Conv2d(self.in_channels, self.num_classes, kernel_size=1)

    def forward(self, x):
        """Forward feature from the upstream network.

        Args:
            x (Tensor): Feature from the upstream network, which is
                a 4D-tensor.

        Returns:
            Tensor: Predicted semantic segmentation map with shape
                (N, num_classes, H, W).
        """
        return self.segm_conv(x)

    @force_fp32(apply_to=('segm_pred',))
    def loss(self, segm_pred, gt_masks, gt_labels):
        """Compute loss of the head.

        Args:
            segm_pred (list[Tensor]): Predicted semantic segmentation map
                with shape (N, num_classes, H, W).
            gt_masks (list[Tensor]): Ground truth masks for each image with
                the same shape of the input image.
            gt_labels (list[Tensor]): Class indices corresponding to each box.

        Returns:
            dict[str, Tensor]: A dictionary of loss components.
        """
        loss_segm = []
        num_imgs, num_classes, mask_h, mask_w = segm_pred.size()
        for idx in range(num_imgs):
            cur_segm_pred = segm_pred[idx]
            cur_gt_masks = gt_masks[idx].float()
            cur_gt_labels = gt_labels[idx]
            segm_targets = self.get_targets(cur_segm_pred, cur_gt_masks, cur_gt_labels)
            if segm_targets is None:
                loss = self.loss_segm(cur_segm_pred, torch.zeros_like(cur_segm_pred), torch.zeros_like(cur_segm_pred))
            else:
                loss = self.loss_segm(cur_segm_pred, segm_targets, avg_factor=num_imgs * mask_h * mask_w)
            loss_segm.append(loss)
        return dict(loss_segm=loss_segm)

    def get_targets(self, segm_pred, gt_masks, gt_labels):
        """Compute semantic segmentation targets for each image.

        Args:
            segm_pred (Tensor): Predicted semantic segmentation map
                with shape (num_classes, H, W).
            gt_masks (Tensor): Ground truth masks for each image with
                the same shape of the input image.
            gt_labels (Tensor): Class indices corresponding to each box.

        Returns:
            Tensor: Semantic segmentation targets with shape
                (num_classes, H, W).
        """
        if gt_masks.size(0) == 0:
            return None
        num_classes, mask_h, mask_w = segm_pred.size()
        with torch.no_grad():
            downsampled_masks = F.interpolate(gt_masks.unsqueeze(0), (mask_h, mask_w), mode='bilinear', align_corners=False).squeeze(0)
            downsampled_masks = downsampled_masks.gt(0.5).float()
            segm_targets = torch.zeros_like(segm_pred, requires_grad=False)
            for obj_idx in range(downsampled_masks.size(0)):
                segm_targets[gt_labels[obj_idx] - 1] = torch.max(segm_targets[gt_labels[obj_idx] - 1], downsampled_masks[obj_idx])
            return segm_targets

    def simple_test(self, feats, img_metas, rescale=False):
        """Test function without test-time augmentation."""
        raise NotImplementedError('simple_test of YOLACTSegmHead is not implemented because this head is only evaluated during training')

def forward(self, x):
    """Forward feature from the upstream network.

        Args:
            x (Tensor): Feature from the upstream network, which is
                a 4D-tensor.

        Returns:
            Tensor: Predicted semantic segmentation map with shape
                (N, num_classes, H, W).
        """
    return self.segm_conv(x)

