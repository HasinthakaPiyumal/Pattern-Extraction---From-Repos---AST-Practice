# Cluster 17

class RCB(nn.Module):

    def __init__(self, n_feat, kernel_size=3, reduction=8, bias=False, groups=1):
        super(RCB, self).__init__()
        act = nn.LeakyReLU(0.2)
        self.body = nn.Sequential(nn.Conv2d(n_feat, n_feat, kernel_size=3, stride=1, padding=1, bias=bias, groups=groups), act, nn.Conv2d(n_feat, n_feat, kernel_size=3, stride=1, padding=1, bias=bias, groups=groups))
        self.act = act
        self.gcnet = ContextBlock(n_feat, bias=bias)

    def forward(self, x):
        res = self.body(x)
        res = self.act(self.gcnet(res))
        res += x
        return res

def forward(self, x):
    res = self.body(x)
    res = self.act(self.gcnet(res))
    res += x
    return res

class DownSample(nn.Module):

    def __init__(self, in_channels, scale_factor, chan_factor=2, kernel_size=3):
        super(DownSample, self).__init__()
        self.scale_factor = int(np.log2(scale_factor))
        modules_body = []
        for i in range(self.scale_factor):
            modules_body.append(Down(in_channels, chan_factor))
            in_channels = int(in_channels * chan_factor)
        self.body = nn.Sequential(*modules_body)

    def forward(self, x):
        x = self.body(x)
        return x

def forward(self, x):
    x = self.body(x)
    return x

class UpSample(nn.Module):

    def __init__(self, in_channels, scale_factor, chan_factor=2, kernel_size=3):
        super(UpSample, self).__init__()
        self.scale_factor = int(np.log2(scale_factor))
        modules_body = []
        for i in range(self.scale_factor):
            modules_body.append(Up(in_channels, chan_factor))
            in_channels = int(in_channels // chan_factor)
        self.body = nn.Sequential(*modules_body)

    def forward(self, x):
        x = self.body(x)
        return x

def forward(self, x):
    x = self.body(x)
    return x

class MRB(nn.Module):

    def __init__(self, n_feat, height, width, chan_factor, bias, groups):
        super(MRB, self).__init__()
        self.n_feat, self.height, self.width = (n_feat, height, width)
        self.dau_top = RCB(int(n_feat * chan_factor ** 0), bias=bias, groups=groups)
        self.dau_mid = RCB(int(n_feat * chan_factor ** 1), bias=bias, groups=groups)
        self.dau_bot = RCB(int(n_feat * chan_factor ** 2), bias=bias, groups=groups)
        self.down2 = DownSample(int(chan_factor ** 0 * n_feat), 2, chan_factor)
        self.down4 = nn.Sequential(DownSample(int(chan_factor ** 0 * n_feat), 2, chan_factor), DownSample(int(chan_factor ** 1 * n_feat), 2, chan_factor))
        self.up21_1 = UpSample(int(chan_factor ** 1 * n_feat), 2, chan_factor)
        self.up21_2 = UpSample(int(chan_factor ** 1 * n_feat), 2, chan_factor)
        self.up32_1 = UpSample(int(chan_factor ** 2 * n_feat), 2, chan_factor)
        self.up32_2 = UpSample(int(chan_factor ** 2 * n_feat), 2, chan_factor)
        self.conv_out = nn.Conv2d(n_feat, n_feat, kernel_size=1, padding=0, bias=bias)
        self.skff_top = SKFF(int(n_feat * chan_factor ** 0), 2)
        self.skff_mid = SKFF(int(n_feat * chan_factor ** 1), 2)

    def forward(self, x):
        x_top = x.clone()
        x_mid = self.down2(x_top)
        x_bot = self.down4(x_top)
        x_top = self.dau_top(x_top)
        x_mid = self.dau_mid(x_mid)
        x_bot = self.dau_bot(x_bot)
        x_mid = self.skff_mid([x_mid, self.up32_1(x_bot)])
        x_top = self.skff_top([x_top, self.up21_1(x_mid)])
        x_top = self.dau_top(x_top)
        x_mid = self.dau_mid(x_mid)
        x_bot = self.dau_bot(x_bot)
        x_mid = self.skff_mid([x_mid, self.up32_2(x_bot)])
        x_top = self.skff_top([x_top, self.up21_2(x_mid)])
        out = self.conv_out(x_top)
        out = out + x
        return out

def forward(self, x):
    x_top = x.clone()
    x_mid = self.down2(x_top)
    x_bot = self.down4(x_top)
    x_top = self.dau_top(x_top)
    x_mid = self.dau_mid(x_mid)
    x_bot = self.dau_bot(x_bot)
    x_mid = self.skff_mid([x_mid, self.up32_1(x_bot)])
    x_top = self.skff_top([x_top, self.up21_1(x_mid)])
    x_top = self.dau_top(x_top)
    x_mid = self.dau_mid(x_mid)
    x_bot = self.dau_bot(x_bot)
    x_mid = self.skff_mid([x_mid, self.up32_2(x_bot)])
    x_top = self.skff_top([x_top, self.up21_2(x_mid)])
    out = self.conv_out(x_top)
    out = out + x
    return out

class RRG(nn.Module):

    def __init__(self, n_feat, n_MRB, height, width, chan_factor, bias=False, groups=1):
        super(RRG, self).__init__()
        modules_body = [MRB(n_feat, height, width, chan_factor, bias, groups) for _ in range(n_MRB)]
        modules_body.append(nn.Conv2d(n_feat, n_feat, kernel_size=3, stride=1, padding=1, bias=bias))
        self.body = nn.Sequential(*modules_body)

    def forward(self, x):
        res = self.body(x)
        res += x
        return res

def forward(self, x):
    res = self.body(x)
    res += x
    return res

class MIRNet_v2(nn.Module):

    def __init__(self, inp_channels=3, out_channels=3, n_feat=80, chan_factor=1.5, n_RRG=4, n_MRB=2, height=3, width=2, scale=1, bias=False, task=None):
        super(MIRNet_v2, self).__init__()
        kernel_size = 3
        self.task = task
        self.conv_in = nn.Conv2d(inp_channels, n_feat, kernel_size=3, padding=1, bias=bias)
        modules_body = []
        modules_body.append(RRG(n_feat, n_MRB, height, width, chan_factor, bias, groups=1))
        modules_body.append(RRG(n_feat, n_MRB, height, width, chan_factor, bias, groups=2))
        modules_body.append(RRG(n_feat, n_MRB, height, width, chan_factor, bias, groups=4))
        modules_body.append(RRG(n_feat, n_MRB, height, width, chan_factor, bias, groups=4))
        self.body = nn.Sequential(*modules_body)
        self.conv_out = nn.Conv2d(n_feat, out_channels, kernel_size=3, padding=1, bias=bias)

    def forward(self, inp_img):
        shallow_feats = self.conv_in(inp_img)
        deep_feats = self.body(shallow_feats)
        if self.task == 'defocus_deblurring':
            deep_feats += shallow_feats
            out_img = self.conv_out(deep_feats)
        else:
            out_img = self.conv_out(deep_feats)
            out_img += inp_img
        return out_img

def forward(self, inp_img):
    shallow_feats = self.conv_in(inp_img)
    deep_feats = self.body(shallow_feats)
    if self.task == 'defocus_deblurring':
        deep_feats += shallow_feats
        out_img = self.conv_out(deep_feats)
    else:
        out_img = self.conv_out(deep_feats)
        out_img += inp_img
    return out_img

def resize_flow(flow, size_type, sizes, interp_mode='bilinear', align_corners=False):
    """Resize a flow according to ratio or shape.

    Args:
        flow (Tensor): Precomputed flow. shape [N, 2, H, W].
        size_type (str): 'ratio' or 'shape'.
        sizes (list[int | float]): the ratio for resizing or the final output
            shape.
            1) The order of ratio should be [ratio_h, ratio_w]. For
            downsampling, the ratio should be smaller than 1.0 (i.e., ratio
            < 1.0). For upsampling, the ratio should be larger than 1.0 (i.e.,
            ratio > 1.0).
            2) The order of output_size should be [out_h, out_w].
        interp_mode (str): The mode of interpolation for resizing.
            Default: 'bilinear'.
        align_corners (bool): Whether align corners. Default: False.

    Returns:
        Tensor: Resized flow.
    """
    _, _, flow_h, flow_w = flow.size()
    if size_type == 'ratio':
        output_h, output_w = (int(flow_h * sizes[0]), int(flow_w * sizes[1]))
    elif size_type == 'shape':
        output_h, output_w = (sizes[0], sizes[1])
    else:
        raise ValueError(f'Size type should be ratio or shape, but got type {size_type}.')
    input_flow = flow.clone()
    ratio_h = output_h / flow_h
    ratio_w = output_w / flow_w
    input_flow[:, 0, :, :] *= ratio_w
    input_flow[:, 1, :, :] *= ratio_h
    resized_flow = F.interpolate(input=input_flow, size=(output_h, output_w), mode=interp_mode, align_corners=align_corners)
    return resized_flow

