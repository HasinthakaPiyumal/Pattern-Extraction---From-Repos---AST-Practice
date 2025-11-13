# Cluster 57

class HourglassModule(BaseModule):
    """Hourglass Module for HourglassNet backbone.

    Generate module recursively and use BasicBlock as the base unit.

    Args:
        depth (int): Depth of current HourglassModule.
        stage_channels (list[int]): Feature channels of sub-modules in current
            and follow-up HourglassModule.
        stage_blocks (list[int]): Number of sub-modules stacked in current and
            follow-up HourglassModule.
        norm_cfg (dict): Dictionary to construct and config norm layer.
        init_cfg (dict or list[dict], optional): Initialization config dict.
            Default: None
        upsample_cfg (dict, optional): Config dict for interpolate layer.
            Default: `dict(mode='nearest')`
    """

    def __init__(self, depth, stage_channels, stage_blocks, norm_cfg=dict(type='BN', requires_grad=True), init_cfg=None, upsample_cfg=dict(mode='nearest')):
        super(HourglassModule, self).__init__(init_cfg)
        self.depth = depth
        cur_block = stage_blocks[0]
        next_block = stage_blocks[1]
        cur_channel = stage_channels[0]
        next_channel = stage_channels[1]
        self.up1 = ResLayer(BasicBlock, cur_channel, cur_channel, cur_block, norm_cfg=norm_cfg)
        self.low1 = ResLayer(BasicBlock, cur_channel, next_channel, cur_block, stride=2, norm_cfg=norm_cfg)
        if self.depth > 1:
            self.low2 = HourglassModule(depth - 1, stage_channels[1:], stage_blocks[1:])
        else:
            self.low2 = ResLayer(BasicBlock, next_channel, next_channel, next_block, norm_cfg=norm_cfg)
        self.low3 = ResLayer(BasicBlock, next_channel, cur_channel, cur_block, norm_cfg=norm_cfg, downsample_first=False)
        self.up2 = F.interpolate
        self.upsample_cfg = upsample_cfg

    def forward(self, x):
        """Forward function."""
        up1 = self.up1(x)
        low1 = self.low1(x)
        low2 = self.low2(low1)
        low3 = self.low3(low2)
        if 'scale_factor' in self.upsample_cfg:
            up2 = self.up2(low3, **self.upsample_cfg)
        else:
            shape = up1.shape[2:]
            up2 = self.up2(low3, size=shape, **self.upsample_cfg)
        return up1 + up2

def forward(self, x):
    """Forward function."""
    up1 = self.up1(x)
    low1 = self.low1(x)
    low2 = self.low2(low1)
    low3 = self.low3(low2)
    if 'scale_factor' in self.upsample_cfg:
        up2 = self.up2(low3, **self.upsample_cfg)
    else:
        shape = up1.shape[2:]
        up2 = self.up2(low3, size=shape, **self.upsample_cfg)
    return up1 + up2

