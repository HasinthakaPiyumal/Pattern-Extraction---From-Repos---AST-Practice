# Cluster 56

@BACKBONES.register_module()
class Res2Net(ResNet):
    """Res2Net backbone.

    Args:
        scales (int): Scales used in Res2Net. Default: 4
        base_width (int): Basic width of each scale. Default: 26
        depth (int): Depth of res2net, from {50, 101, 152}.
        in_channels (int): Number of input image channels. Default: 3.
        num_stages (int): Res2net stages. Default: 4.
        strides (Sequence[int]): Strides of the first block of each stage.
        dilations (Sequence[int]): Dilation of each stage.
        out_indices (Sequence[int]): Output from which stages.
        style (str): `pytorch` or `caffe`. If set to "pytorch", the stride-two
            layer is the 3x3 conv layer, otherwise the stride-two layer is
            the first 1x1 conv layer.
        deep_stem (bool): Replace 7x7 conv in input stem with 3 3x3 conv
        avg_down (bool): Use AvgPool instead of stride conv when
            downsampling in the bottle2neck.
        frozen_stages (int): Stages to be frozen (stop grad and set eval mode).
            -1 means not freezing any parameters.
        norm_cfg (dict): Dictionary to construct and config norm layer.
        norm_eval (bool): Whether to set norm layers to eval mode, namely,
            freeze running stats (mean and var). Note: Effect on Batch Norm
            and its variants only.
        plugins (list[dict]): List of plugins for stages, each dict contains:

            - cfg (dict, required): Cfg dict to build plugin.
            - position (str, required): Position inside block to insert
              plugin, options are 'after_conv1', 'after_conv2', 'after_conv3'.
            - stages (tuple[bool], optional): Stages to apply plugin, length
              should be same as 'num_stages'.
        with_cp (bool): Use checkpoint or not. Using checkpoint will save some
            memory while slowing down the training speed.
        zero_init_residual (bool): Whether to use zero init for last norm layer
            in resblocks to let them behave as identity.
        pretrained (str, optional): model pretrained path. Default: None
        init_cfg (dict or list[dict], optional): Initialization config dict.
            Default: None

    Example:
        >>> from mmdet.models import Res2Net
        >>> import torch
        >>> self = Res2Net(depth=50, scales=4, base_width=26)
        >>> self.eval()
        >>> inputs = torch.rand(1, 3, 32, 32)
        >>> level_outputs = self.forward(inputs)
        >>> for level_out in level_outputs:
        ...     print(tuple(level_out.shape))
        (1, 256, 8, 8)
        (1, 512, 4, 4)
        (1, 1024, 2, 2)
        (1, 2048, 1, 1)
    """
    arch_settings = {50: (Bottle2neck, (3, 4, 6, 3)), 101: (Bottle2neck, (3, 4, 23, 3)), 152: (Bottle2neck, (3, 8, 36, 3))}

    def __init__(self, scales=4, base_width=26, style='pytorch', deep_stem=True, avg_down=True, pretrained=None, init_cfg=None, **kwargs):
        self.scales = scales
        self.base_width = base_width
        super(Res2Net, self).__init__(style='pytorch', deep_stem=True, avg_down=True, pretrained=pretrained, init_cfg=init_cfg, **kwargs)

    def make_res_layer(self, **kwargs):
        return Res2Layer(scales=self.scales, base_width=self.base_width, base_channels=self.base_channels, **kwargs)

def make_res_layer(self, **kwargs):
    return Res2Layer(scales=self.scales, base_width=self.base_width, base_channels=self.base_channels, **kwargs)

