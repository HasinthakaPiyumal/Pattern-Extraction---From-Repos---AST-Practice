# Cluster 45

class AdaptivePadding(nn.Module):
    """Applies padding to input (if needed) so that input can get fully covered
    by filter you specified. It support two modes "same" and "corner". The
    "same" mode is same with "SAME" padding mode in TensorFlow, pad zero around
    input. The "corner"  mode would pad zero to bottom right.

    Args:
        kernel_size (int | tuple): Size of the kernel:
        stride (int | tuple): Stride of the filter. Default: 1:
        dilation (int | tuple): Spacing between kernel elements.
            Default: 1
        padding (str): Support "same" and "corner", "corner" mode
            would pad zero to bottom right, and "same" mode would
            pad zero around input. Default: "corner".
    Example:
        >>> kernel_size = 16
        >>> stride = 16
        >>> dilation = 1
        >>> input = torch.rand(1, 1, 15, 17)
        >>> adap_pad = AdaptivePadding(
        >>>     kernel_size=kernel_size,
        >>>     stride=stride,
        >>>     dilation=dilation,
        >>>     padding="corner")
        >>> out = adap_pad(input)
        >>> assert (out.shape[2], out.shape[3]) == (16, 32)
        >>> input = torch.rand(1, 1, 16, 17)
        >>> out = adap_pad(input)
        >>> assert (out.shape[2], out.shape[3]) == (16, 32)
    """

    def __init__(self, kernel_size=1, stride=1, dilation=1, padding='corner'):
        super(AdaptivePadding, self).__init__()
        assert padding in ('same', 'corner')
        kernel_size = to_2tuple(kernel_size)
        stride = to_2tuple(stride)
        padding = to_2tuple(padding)
        dilation = to_2tuple(dilation)
        self.padding = padding
        self.kernel_size = kernel_size
        self.stride = stride
        self.dilation = dilation

    def get_pad_shape(self, input_shape):
        input_h, input_w = input_shape
        kernel_h, kernel_w = self.kernel_size
        stride_h, stride_w = self.stride
        output_h = math.ceil(input_h / stride_h)
        output_w = math.ceil(input_w / stride_w)
        pad_h = max((output_h - 1) * stride_h + (kernel_h - 1) * self.dilation[0] + 1 - input_h, 0)
        pad_w = max((output_w - 1) * stride_w + (kernel_w - 1) * self.dilation[1] + 1 - input_w, 0)
        return (pad_h, pad_w)

    def forward(self, x):
        pad_h, pad_w = self.get_pad_shape(x.size()[-2:])
        if pad_h > 0 or pad_w > 0:
            if self.padding == 'corner':
                x = F.pad(x, [0, pad_w, 0, pad_h])
            elif self.padding == 'same':
                x = F.pad(x, [pad_w // 2, pad_w - pad_w // 2, pad_h // 2, pad_h - pad_h // 2])
        return x

def forward(self, x):
    pad_h, pad_w = self.get_pad_shape(x.size()[-2:])
    if pad_h > 0 or pad_w > 0:
        if self.padding == 'corner':
            x = F.pad(x, [0, pad_w, 0, pad_h])
        elif self.padding == 'same':
            x = F.pad(x, [pad_w // 2, pad_w - pad_w // 2, pad_h // 2, pad_h - pad_h // 2])
    return x

def test_adaptive_padding():
    for padding in ('same', 'corner'):
        kernel_size = 16
        stride = 16
        dilation = 1
        input = torch.rand(1, 1, 15, 17)
        pool = AdaptivePadding(kernel_size=kernel_size, stride=stride, dilation=dilation, padding=padding)
        out = pool(input)
        assert (out.shape[2], out.shape[3]) == (16, 32)
        input = torch.rand(1, 1, 16, 17)
        out = pool(input)
        assert (out.shape[2], out.shape[3]) == (16, 32)
        kernel_size = (2, 2)
        stride = (2, 2)
        dilation = (1, 1)
        adap_pad = AdaptivePadding(kernel_size=kernel_size, stride=stride, dilation=dilation, padding=padding)
        input = torch.rand(1, 1, 11, 13)
        out = adap_pad(input)
        assert (out.shape[2], out.shape[3]) == (12, 14)
        kernel_size = (2, 2)
        stride = (10, 10)
        dilation = (1, 1)
        adap_pad = AdaptivePadding(kernel_size=kernel_size, stride=stride, dilation=dilation, padding=padding)
        input = torch.rand(1, 1, 10, 13)
        out = adap_pad(input)
        assert (out.shape[2], out.shape[3]) == (10, 13)
        kernel_size = (11, 11)
        adap_pad = AdaptivePadding(kernel_size=kernel_size, stride=stride, dilation=dilation, padding=padding)
        input = torch.rand(1, 1, 11, 13)
        out = adap_pad(input)
        assert (out.shape[2], out.shape[3]) == (21, 21)
        input = torch.rand(1, 1, 11, 13)
        stride = (3, 4)
        kernel_size = (4, 5)
        dilation = (2, 2)
        adap_pad = AdaptivePadding(kernel_size=kernel_size, stride=stride, dilation=dilation, padding=padding)
        dilation_out = adap_pad(input)
        assert (dilation_out.shape[2], dilation_out.shape[3]) == (16, 21)
        kernel_size = (7, 9)
        dilation = (1, 1)
        adap_pad = AdaptivePadding(kernel_size=kernel_size, stride=stride, dilation=dilation, padding=padding)
        kernel79_out = adap_pad(input)
        assert (kernel79_out.shape[2], kernel79_out.shape[3]) == (16, 21)
        assert kernel79_out.shape == dilation_out.shape
    with pytest.raises(AssertionError):
        AdaptivePadding(kernel_size=kernel_size, stride=stride, dilation=dilation, padding=1)

class Fusion(nn.Module):
    """Saliency-based learning fusion layer (Sec.3.2)"""

    def __init__(self):
        super(Fusion, self).__init__()
        self.a1 = nn.Parameter(torch.rand(1, 256, 1, 1))
        self.a2 = nn.Parameter(torch.rand(1, 256, 1, 1))
        self.a3 = nn.Parameter(torch.rand(1, 256, 1, 1))
        self.a4 = nn.Parameter(torch.rand(1, 256, 1, 1))
        self.avgpool = nn.AvgPool2d(kernel_size=4, stride=4, padding=0)

    def forward(self, x1, x2, x3, x4):
        s1 = self.a1.expand_as(x1) * x1
        s2 = self.a2.expand_as(x2) * x2
        s3 = self.a3.expand_as(x3) * x3
        s4 = self.a4.expand_as(x4) * x4
        y = self.avgpool(s1 + s2 + s3 + s4)
        return y

def forward(self, x1, x2, x3, x4):
    s1 = self.a1.expand_as(x1) * x1
    s2 = self.a2.expand_as(x2) * x2
    s3 = self.a3.expand_as(x3) * x3
    s4 = self.a4.expand_as(x4) * x4
    y = self.avgpool(s1 + s2 + s3 + s4)
    return y

class MaxPoolPad(nn.Module):

    def __init__(self):
        super(MaxPoolPad, self).__init__()
        self.pad = nn.ZeroPad2d((1, 0, 1, 0))
        self.pool = nn.MaxPool2d(3, stride=2, padding=1)

    def forward(self, x):
        x = self.pad(x)
        x = self.pool(x)
        x = x[:, :, 1:, 1:].contiguous()
        return x

def forward(self, x):
    x = self.pad(x)
    x = self.pool(x)
    x = x[:, :, 1:, 1:].contiguous()
    return x

class AvgPoolPad(nn.Module):

    def __init__(self, stride=2, padding=1):
        super(AvgPoolPad, self).__init__()
        self.pad = nn.ZeroPad2d((1, 0, 1, 0))
        self.pool = nn.AvgPool2d(3, stride=stride, padding=padding, count_include_pad=False)

    def forward(self, x):
        x = self.pad(x)
        x = self.pool(x)
        x = x[:, :, 1:, 1:].contiguous()
        return x

def forward(self, x):
    x = self.pad(x)
    x = self.pool(x)
    x = x[:, :, 1:, 1:].contiguous()
    return x

class CellStem0(nn.Module):

    def __init__(self, stem_filters, num_filters=42):
        super(CellStem0, self).__init__()
        self.num_filters = num_filters
        self.stem_filters = stem_filters
        self.conv_1x1 = nn.Sequential()
        self.conv_1x1.add_module('relu', nn.ReLU())
        self.conv_1x1.add_module('conv', nn.Conv2d(self.stem_filters, self.num_filters, 1, stride=1, bias=False))
        self.conv_1x1.add_module('bn', nn.BatchNorm2d(self.num_filters, eps=0.001, momentum=0.1, affine=True))
        self.comb_iter_0_left = BranchSeparables(self.num_filters, self.num_filters, 5, 2, 2)
        self.comb_iter_0_right = BranchSeparablesStem(self.stem_filters, self.num_filters, 7, 2, 3, bias=False)
        self.comb_iter_1_left = nn.MaxPool2d(3, stride=2, padding=1)
        self.comb_iter_1_right = BranchSeparablesStem(self.stem_filters, self.num_filters, 7, 2, 3, bias=False)
        self.comb_iter_2_left = nn.AvgPool2d(3, stride=2, padding=1, count_include_pad=False)
        self.comb_iter_2_right = BranchSeparablesStem(self.stem_filters, self.num_filters, 5, 2, 2, bias=False)
        self.comb_iter_3_right = nn.AvgPool2d(3, stride=1, padding=1, count_include_pad=False)
        self.comb_iter_4_left = BranchSeparables(self.num_filters, self.num_filters, 3, 1, 1, bias=False)
        self.comb_iter_4_right = nn.MaxPool2d(3, stride=2, padding=1)

    def forward(self, x):
        x1 = self.conv_1x1(x)
        x_comb_iter_0_left = self.comb_iter_0_left(x1)
        x_comb_iter_0_right = self.comb_iter_0_right(x)
        x_comb_iter_0 = x_comb_iter_0_left + x_comb_iter_0_right
        x_comb_iter_1_left = self.comb_iter_1_left(x1)
        x_comb_iter_1_right = self.comb_iter_1_right(x)
        x_comb_iter_1 = x_comb_iter_1_left + x_comb_iter_1_right
        x_comb_iter_2_left = self.comb_iter_2_left(x1)
        x_comb_iter_2_right = self.comb_iter_2_right(x)
        x_comb_iter_2 = x_comb_iter_2_left + x_comb_iter_2_right
        x_comb_iter_3_right = self.comb_iter_3_right(x_comb_iter_0)
        x_comb_iter_3 = x_comb_iter_3_right + x_comb_iter_1
        x_comb_iter_4_left = self.comb_iter_4_left(x_comb_iter_0)
        x_comb_iter_4_right = self.comb_iter_4_right(x1)
        x_comb_iter_4 = x_comb_iter_4_left + x_comb_iter_4_right
        x_out = torch.cat([x_comb_iter_1, x_comb_iter_2, x_comb_iter_3, x_comb_iter_4], 1)
        return x_out

def forward(self, x):
    x1 = self.conv_1x1(x)
    x_comb_iter_0_left = self.comb_iter_0_left(x1)
    x_comb_iter_0_right = self.comb_iter_0_right(x)
    x_comb_iter_0 = x_comb_iter_0_left + x_comb_iter_0_right
    x_comb_iter_1_left = self.comb_iter_1_left(x1)
    x_comb_iter_1_right = self.comb_iter_1_right(x)
    x_comb_iter_1 = x_comb_iter_1_left + x_comb_iter_1_right
    x_comb_iter_2_left = self.comb_iter_2_left(x1)
    x_comb_iter_2_right = self.comb_iter_2_right(x)
    x_comb_iter_2 = x_comb_iter_2_left + x_comb_iter_2_right
    x_comb_iter_3_right = self.comb_iter_3_right(x_comb_iter_0)
    x_comb_iter_3 = x_comb_iter_3_right + x_comb_iter_1
    x_comb_iter_4_left = self.comb_iter_4_left(x_comb_iter_0)
    x_comb_iter_4_right = self.comb_iter_4_right(x1)
    x_comb_iter_4 = x_comb_iter_4_left + x_comb_iter_4_right
    x_out = torch.cat([x_comb_iter_1, x_comb_iter_2, x_comb_iter_3, x_comb_iter_4], 1)
    return x_out

class CellStem1(nn.Module):

    def __init__(self, stem_filters, num_filters):
        super(CellStem1, self).__init__()
        self.num_filters = num_filters
        self.stem_filters = stem_filters
        self.conv_1x1 = nn.Sequential()
        self.conv_1x1.add_module('relu', nn.ReLU())
        self.conv_1x1.add_module('conv', nn.Conv2d(2 * self.num_filters, self.num_filters, 1, stride=1, bias=False))
        self.conv_1x1.add_module('bn', nn.BatchNorm2d(self.num_filters, eps=0.001, momentum=0.1, affine=True))
        self.relu = nn.ReLU()
        self.path_1 = nn.Sequential()
        self.path_1.add_module('avgpool', nn.AvgPool2d(1, stride=2, count_include_pad=False))
        self.path_1.add_module('conv', nn.Conv2d(self.stem_filters, self.num_filters // 2, 1, stride=1, bias=False))
        self.path_2 = nn.ModuleList()
        self.path_2.add_module('pad', nn.ZeroPad2d((0, 1, 0, 1)))
        self.path_2.add_module('avgpool', nn.AvgPool2d(1, stride=2, count_include_pad=False))
        self.path_2.add_module('conv', nn.Conv2d(self.stem_filters, self.num_filters // 2, 1, stride=1, bias=False))
        self.final_path_bn = nn.BatchNorm2d(self.num_filters, eps=0.001, momentum=0.1, affine=True)
        self.comb_iter_0_left = BranchSeparables(self.num_filters, self.num_filters, 5, 2, 2, name='specific', bias=False)
        self.comb_iter_0_right = BranchSeparables(self.num_filters, self.num_filters, 7, 2, 3, name='specific', bias=False)
        self.comb_iter_1_left = MaxPoolPad()
        self.comb_iter_1_right = BranchSeparables(self.num_filters, self.num_filters, 7, 2, 3, name='specific', bias=False)
        self.comb_iter_2_left = AvgPoolPad()
        self.comb_iter_2_right = BranchSeparables(self.num_filters, self.num_filters, 5, 2, 2, name='specific', bias=False)
        self.comb_iter_3_right = nn.AvgPool2d(3, stride=1, padding=1, count_include_pad=False)
        self.comb_iter_4_left = BranchSeparables(self.num_filters, self.num_filters, 3, 1, 1, name='specific', bias=False)
        self.comb_iter_4_right = MaxPoolPad()

    def forward(self, x_conv0, x_stem_0):
        x_left = self.conv_1x1(x_stem_0)
        x_relu = self.relu(x_conv0)
        x_path1 = self.path_1(x_relu)
        x_path2 = self.path_2.pad(x_relu)
        x_path2 = x_path2[:, :, 1:, 1:]
        x_path2 = self.path_2.avgpool(x_path2)
        x_path2 = self.path_2.conv(x_path2)
        x_right = self.final_path_bn(torch.cat([x_path1, x_path2], 1))
        x_comb_iter_0_left = self.comb_iter_0_left(x_left)
        x_comb_iter_0_right = self.comb_iter_0_right(x_right)
        x_comb_iter_0 = x_comb_iter_0_left + x_comb_iter_0_right
        x_comb_iter_1_left = self.comb_iter_1_left(x_left)
        x_comb_iter_1_right = self.comb_iter_1_right(x_right)
        x_comb_iter_1 = x_comb_iter_1_left + x_comb_iter_1_right
        x_comb_iter_2_left = self.comb_iter_2_left(x_left)
        x_comb_iter_2_right = self.comb_iter_2_right(x_right)
        x_comb_iter_2 = x_comb_iter_2_left + x_comb_iter_2_right
        x_comb_iter_3_right = self.comb_iter_3_right(x_comb_iter_0)
        x_comb_iter_3 = x_comb_iter_3_right + x_comb_iter_1
        x_comb_iter_4_left = self.comb_iter_4_left(x_comb_iter_0)
        x_comb_iter_4_right = self.comb_iter_4_right(x_left)
        x_comb_iter_4 = x_comb_iter_4_left + x_comb_iter_4_right
        x_out = torch.cat([x_comb_iter_1, x_comb_iter_2, x_comb_iter_3, x_comb_iter_4], 1)
        return x_out

def forward(self, x_conv0, x_stem_0):
    x_left = self.conv_1x1(x_stem_0)
    x_relu = self.relu(x_conv0)
    x_path1 = self.path_1(x_relu)
    x_path2 = self.path_2.pad(x_relu)
    x_path2 = x_path2[:, :, 1:, 1:]
    x_path2 = self.path_2.avgpool(x_path2)
    x_path2 = self.path_2.conv(x_path2)
    x_right = self.final_path_bn(torch.cat([x_path1, x_path2], 1))
    x_comb_iter_0_left = self.comb_iter_0_left(x_left)
    x_comb_iter_0_right = self.comb_iter_0_right(x_right)
    x_comb_iter_0 = x_comb_iter_0_left + x_comb_iter_0_right
    x_comb_iter_1_left = self.comb_iter_1_left(x_left)
    x_comb_iter_1_right = self.comb_iter_1_right(x_right)
    x_comb_iter_1 = x_comb_iter_1_left + x_comb_iter_1_right
    x_comb_iter_2_left = self.comb_iter_2_left(x_left)
    x_comb_iter_2_right = self.comb_iter_2_right(x_right)
    x_comb_iter_2 = x_comb_iter_2_left + x_comb_iter_2_right
    x_comb_iter_3_right = self.comb_iter_3_right(x_comb_iter_0)
    x_comb_iter_3 = x_comb_iter_3_right + x_comb_iter_1
    x_comb_iter_4_left = self.comb_iter_4_left(x_comb_iter_0)
    x_comb_iter_4_right = self.comb_iter_4_right(x_left)
    x_comb_iter_4 = x_comb_iter_4_left + x_comb_iter_4_right
    x_out = torch.cat([x_comb_iter_1, x_comb_iter_2, x_comb_iter_3, x_comb_iter_4], 1)
    return x_out

class FirstCell(nn.Module):

    def __init__(self, in_channels_left, out_channels_left, in_channels_right, out_channels_right):
        super(FirstCell, self).__init__()
        self.conv_1x1 = nn.Sequential()
        self.conv_1x1.add_module('relu', nn.ReLU())
        self.conv_1x1.add_module('conv', nn.Conv2d(in_channels_right, out_channels_right, 1, stride=1, bias=False))
        self.conv_1x1.add_module('bn', nn.BatchNorm2d(out_channels_right, eps=0.001, momentum=0.1, affine=True))
        self.relu = nn.ReLU()
        self.path_1 = nn.Sequential()
        self.path_1.add_module('avgpool', nn.AvgPool2d(1, stride=2, count_include_pad=False))
        self.path_1.add_module('conv', nn.Conv2d(in_channels_left, out_channels_left, 1, stride=1, bias=False))
        self.path_2 = nn.ModuleList()
        self.path_2.add_module('pad', nn.ZeroPad2d((0, 1, 0, 1)))
        self.path_2.add_module('avgpool', nn.AvgPool2d(1, stride=2, count_include_pad=False))
        self.path_2.add_module('conv', nn.Conv2d(in_channels_left, out_channels_left, 1, stride=1, bias=False))
        self.final_path_bn = nn.BatchNorm2d(out_channels_left * 2, eps=0.001, momentum=0.1, affine=True)
        self.comb_iter_0_left = BranchSeparables(out_channels_right, out_channels_right, 5, 1, 2, bias=False)
        self.comb_iter_0_right = BranchSeparables(out_channels_right, out_channels_right, 3, 1, 1, bias=False)
        self.comb_iter_1_left = BranchSeparables(out_channels_right, out_channels_right, 5, 1, 2, bias=False)
        self.comb_iter_1_right = BranchSeparables(out_channels_right, out_channels_right, 3, 1, 1, bias=False)
        self.comb_iter_2_left = nn.AvgPool2d(3, stride=1, padding=1, count_include_pad=False)
        self.comb_iter_3_left = nn.AvgPool2d(3, stride=1, padding=1, count_include_pad=False)
        self.comb_iter_3_right = nn.AvgPool2d(3, stride=1, padding=1, count_include_pad=False)
        self.comb_iter_4_left = BranchSeparables(out_channels_right, out_channels_right, 3, 1, 1, bias=False)

    def forward(self, x, x_prev):
        x_relu = self.relu(x_prev)
        x_path1 = self.path_1(x_relu)
        x_path2 = self.path_2.pad(x_relu)
        x_path2 = x_path2[:, :, 1:, 1:]
        x_path2 = self.path_2.avgpool(x_path2)
        x_path2 = self.path_2.conv(x_path2)
        x_left = self.final_path_bn(torch.cat([x_path1, x_path2], 1))
        x_right = self.conv_1x1(x)
        x_comb_iter_0_left = self.comb_iter_0_left(x_right)
        x_comb_iter_0_right = self.comb_iter_0_right(x_left)
        x_comb_iter_0 = x_comb_iter_0_left + x_comb_iter_0_right
        x_comb_iter_1_left = self.comb_iter_1_left(x_left)
        x_comb_iter_1_right = self.comb_iter_1_right(x_left)
        x_comb_iter_1 = x_comb_iter_1_left + x_comb_iter_1_right
        x_comb_iter_2_left = self.comb_iter_2_left(x_right)
        x_comb_iter_2 = x_comb_iter_2_left + x_left
        x_comb_iter_3_left = self.comb_iter_3_left(x_left)
        x_comb_iter_3_right = self.comb_iter_3_right(x_left)
        x_comb_iter_3 = x_comb_iter_3_left + x_comb_iter_3_right
        x_comb_iter_4_left = self.comb_iter_4_left(x_right)
        x_comb_iter_4 = x_comb_iter_4_left + x_right
        x_out = torch.cat([x_left, x_comb_iter_0, x_comb_iter_1, x_comb_iter_2, x_comb_iter_3, x_comb_iter_4], 1)
        return x_out

def forward(self, x, x_prev):
    x_relu = self.relu(x_prev)
    x_path1 = self.path_1(x_relu)
    x_path2 = self.path_2.pad(x_relu)
    x_path2 = x_path2[:, :, 1:, 1:]
    x_path2 = self.path_2.avgpool(x_path2)
    x_path2 = self.path_2.conv(x_path2)
    x_left = self.final_path_bn(torch.cat([x_path1, x_path2], 1))
    x_right = self.conv_1x1(x)
    x_comb_iter_0_left = self.comb_iter_0_left(x_right)
    x_comb_iter_0_right = self.comb_iter_0_right(x_left)
    x_comb_iter_0 = x_comb_iter_0_left + x_comb_iter_0_right
    x_comb_iter_1_left = self.comb_iter_1_left(x_left)
    x_comb_iter_1_right = self.comb_iter_1_right(x_left)
    x_comb_iter_1 = x_comb_iter_1_left + x_comb_iter_1_right
    x_comb_iter_2_left = self.comb_iter_2_left(x_right)
    x_comb_iter_2 = x_comb_iter_2_left + x_left
    x_comb_iter_3_left = self.comb_iter_3_left(x_left)
    x_comb_iter_3_right = self.comb_iter_3_right(x_left)
    x_comb_iter_3 = x_comb_iter_3_left + x_comb_iter_3_right
    x_comb_iter_4_left = self.comb_iter_4_left(x_right)
    x_comb_iter_4 = x_comb_iter_4_left + x_right
    x_out = torch.cat([x_left, x_comb_iter_0, x_comb_iter_1, x_comb_iter_2, x_comb_iter_3, x_comb_iter_4], 1)
    return x_out

class NormalCell(nn.Module):

    def __init__(self, in_channels_left, out_channels_left, in_channels_right, out_channels_right):
        super(NormalCell, self).__init__()
        self.conv_prev_1x1 = nn.Sequential()
        self.conv_prev_1x1.add_module('relu', nn.ReLU())
        self.conv_prev_1x1.add_module('conv', nn.Conv2d(in_channels_left, out_channels_left, 1, stride=1, bias=False))
        self.conv_prev_1x1.add_module('bn', nn.BatchNorm2d(out_channels_left, eps=0.001, momentum=0.1, affine=True))
        self.conv_1x1 = nn.Sequential()
        self.conv_1x1.add_module('relu', nn.ReLU())
        self.conv_1x1.add_module('conv', nn.Conv2d(in_channels_right, out_channels_right, 1, stride=1, bias=False))
        self.conv_1x1.add_module('bn', nn.BatchNorm2d(out_channels_right, eps=0.001, momentum=0.1, affine=True))
        self.comb_iter_0_left = BranchSeparables(out_channels_right, out_channels_right, 5, 1, 2, bias=False)
        self.comb_iter_0_right = BranchSeparables(out_channels_left, out_channels_left, 3, 1, 1, bias=False)
        self.comb_iter_1_left = BranchSeparables(out_channels_left, out_channels_left, 5, 1, 2, bias=False)
        self.comb_iter_1_right = BranchSeparables(out_channels_left, out_channels_left, 3, 1, 1, bias=False)
        self.comb_iter_2_left = nn.AvgPool2d(3, stride=1, padding=1, count_include_pad=False)
        self.comb_iter_3_left = nn.AvgPool2d(3, stride=1, padding=1, count_include_pad=False)
        self.comb_iter_3_right = nn.AvgPool2d(3, stride=1, padding=1, count_include_pad=False)
        self.comb_iter_4_left = BranchSeparables(out_channels_right, out_channels_right, 3, 1, 1, bias=False)

    def forward(self, x, x_prev):
        x_left = self.conv_prev_1x1(x_prev)
        x_right = self.conv_1x1(x)
        x_comb_iter_0_left = self.comb_iter_0_left(x_right)
        x_comb_iter_0_right = self.comb_iter_0_right(x_left)
        x_comb_iter_0 = x_comb_iter_0_left + x_comb_iter_0_right
        x_comb_iter_1_left = self.comb_iter_1_left(x_left)
        x_comb_iter_1_right = self.comb_iter_1_right(x_left)
        x_comb_iter_1 = x_comb_iter_1_left + x_comb_iter_1_right
        x_comb_iter_2_left = self.comb_iter_2_left(x_right)
        x_comb_iter_2 = x_comb_iter_2_left + x_left
        x_comb_iter_3_left = self.comb_iter_3_left(x_left)
        x_comb_iter_3_right = self.comb_iter_3_right(x_left)
        x_comb_iter_3 = x_comb_iter_3_left + x_comb_iter_3_right
        x_comb_iter_4_left = self.comb_iter_4_left(x_right)
        x_comb_iter_4 = x_comb_iter_4_left + x_right
        x_out = torch.cat([x_left, x_comb_iter_0, x_comb_iter_1, x_comb_iter_2, x_comb_iter_3, x_comb_iter_4], 1)
        return x_out

def forward(self, x, x_prev):
    x_left = self.conv_prev_1x1(x_prev)
    x_right = self.conv_1x1(x)
    x_comb_iter_0_left = self.comb_iter_0_left(x_right)
    x_comb_iter_0_right = self.comb_iter_0_right(x_left)
    x_comb_iter_0 = x_comb_iter_0_left + x_comb_iter_0_right
    x_comb_iter_1_left = self.comb_iter_1_left(x_left)
    x_comb_iter_1_right = self.comb_iter_1_right(x_left)
    x_comb_iter_1 = x_comb_iter_1_left + x_comb_iter_1_right
    x_comb_iter_2_left = self.comb_iter_2_left(x_right)
    x_comb_iter_2 = x_comb_iter_2_left + x_left
    x_comb_iter_3_left = self.comb_iter_3_left(x_left)
    x_comb_iter_3_right = self.comb_iter_3_right(x_left)
    x_comb_iter_3 = x_comb_iter_3_left + x_comb_iter_3_right
    x_comb_iter_4_left = self.comb_iter_4_left(x_right)
    x_comb_iter_4 = x_comb_iter_4_left + x_right
    x_out = torch.cat([x_left, x_comb_iter_0, x_comb_iter_1, x_comb_iter_2, x_comb_iter_3, x_comb_iter_4], 1)
    return x_out

class ReductionCell0(nn.Module):

    def __init__(self, in_channels_left, out_channels_left, in_channels_right, out_channels_right):
        super(ReductionCell0, self).__init__()
        self.conv_prev_1x1 = nn.Sequential()
        self.conv_prev_1x1.add_module('relu', nn.ReLU())
        self.conv_prev_1x1.add_module('conv', nn.Conv2d(in_channels_left, out_channels_left, 1, stride=1, bias=False))
        self.conv_prev_1x1.add_module('bn', nn.BatchNorm2d(out_channels_left, eps=0.001, momentum=0.1, affine=True))
        self.conv_1x1 = nn.Sequential()
        self.conv_1x1.add_module('relu', nn.ReLU())
        self.conv_1x1.add_module('conv', nn.Conv2d(in_channels_right, out_channels_right, 1, stride=1, bias=False))
        self.conv_1x1.add_module('bn', nn.BatchNorm2d(out_channels_right, eps=0.001, momentum=0.1, affine=True))
        self.comb_iter_0_left = BranchSeparablesReduction(out_channels_right, out_channels_right, 5, 2, 2, bias=False)
        self.comb_iter_0_right = BranchSeparablesReduction(out_channels_right, out_channels_right, 7, 2, 3, bias=False)
        self.comb_iter_1_left = MaxPoolPad()
        self.comb_iter_1_right = BranchSeparablesReduction(out_channels_right, out_channels_right, 7, 2, 3, bias=False)
        self.comb_iter_2_left = AvgPoolPad()
        self.comb_iter_2_right = BranchSeparablesReduction(out_channels_right, out_channels_right, 5, 2, 2, bias=False)
        self.comb_iter_3_right = nn.AvgPool2d(3, stride=1, padding=1, count_include_pad=False)
        self.comb_iter_4_left = BranchSeparablesReduction(out_channels_right, out_channels_right, 3, 1, 1, bias=False)
        self.comb_iter_4_right = MaxPoolPad()

    def forward(self, x, x_prev):
        x_left = self.conv_prev_1x1(x_prev)
        x_right = self.conv_1x1(x)
        x_comb_iter_0_left = self.comb_iter_0_left(x_right)
        x_comb_iter_0_right = self.comb_iter_0_right(x_left)
        x_comb_iter_0 = x_comb_iter_0_left + x_comb_iter_0_right
        x_comb_iter_1_left = self.comb_iter_1_left(x_right)
        x_comb_iter_1_right = self.comb_iter_1_right(x_left)
        x_comb_iter_1 = x_comb_iter_1_left + x_comb_iter_1_right
        x_comb_iter_2_left = self.comb_iter_2_left(x_right)
        x_comb_iter_2_right = self.comb_iter_2_right(x_left)
        x_comb_iter_2 = x_comb_iter_2_left + x_comb_iter_2_right
        x_comb_iter_3_right = self.comb_iter_3_right(x_comb_iter_0)
        x_comb_iter_3 = x_comb_iter_3_right + x_comb_iter_1
        x_comb_iter_4_left = self.comb_iter_4_left(x_comb_iter_0)
        x_comb_iter_4_right = self.comb_iter_4_right(x_right)
        x_comb_iter_4 = x_comb_iter_4_left + x_comb_iter_4_right
        x_out = torch.cat([x_comb_iter_1, x_comb_iter_2, x_comb_iter_3, x_comb_iter_4], 1)
        return x_out

def forward(self, x, x_prev):
    x_left = self.conv_prev_1x1(x_prev)
    x_right = self.conv_1x1(x)
    x_comb_iter_0_left = self.comb_iter_0_left(x_right)
    x_comb_iter_0_right = self.comb_iter_0_right(x_left)
    x_comb_iter_0 = x_comb_iter_0_left + x_comb_iter_0_right
    x_comb_iter_1_left = self.comb_iter_1_left(x_right)
    x_comb_iter_1_right = self.comb_iter_1_right(x_left)
    x_comb_iter_1 = x_comb_iter_1_left + x_comb_iter_1_right
    x_comb_iter_2_left = self.comb_iter_2_left(x_right)
    x_comb_iter_2_right = self.comb_iter_2_right(x_left)
    x_comb_iter_2 = x_comb_iter_2_left + x_comb_iter_2_right
    x_comb_iter_3_right = self.comb_iter_3_right(x_comb_iter_0)
    x_comb_iter_3 = x_comb_iter_3_right + x_comb_iter_1
    x_comb_iter_4_left = self.comb_iter_4_left(x_comb_iter_0)
    x_comb_iter_4_right = self.comb_iter_4_right(x_right)
    x_comb_iter_4 = x_comb_iter_4_left + x_comb_iter_4_right
    x_out = torch.cat([x_comb_iter_1, x_comb_iter_2, x_comb_iter_3, x_comb_iter_4], 1)
    return x_out

class ReductionCell1(nn.Module):

    def __init__(self, in_channels_left, out_channels_left, in_channels_right, out_channels_right):
        super(ReductionCell1, self).__init__()
        self.conv_prev_1x1 = nn.Sequential()
        self.conv_prev_1x1.add_module('relu', nn.ReLU())
        self.conv_prev_1x1.add_module('conv', nn.Conv2d(in_channels_left, out_channels_left, 1, stride=1, bias=False))
        self.conv_prev_1x1.add_module('bn', nn.BatchNorm2d(out_channels_left, eps=0.001, momentum=0.1, affine=True))
        self.conv_1x1 = nn.Sequential()
        self.conv_1x1.add_module('relu', nn.ReLU())
        self.conv_1x1.add_module('conv', nn.Conv2d(in_channels_right, out_channels_right, 1, stride=1, bias=False))
        self.conv_1x1.add_module('bn', nn.BatchNorm2d(out_channels_right, eps=0.001, momentum=0.1, affine=True))
        self.comb_iter_0_left = BranchSeparables(out_channels_right, out_channels_right, 5, 2, 2, name='specific', bias=False)
        self.comb_iter_0_right = BranchSeparables(out_channels_right, out_channels_right, 7, 2, 3, name='specific', bias=False)
        self.comb_iter_1_left = MaxPoolPad()
        self.comb_iter_1_right = BranchSeparables(out_channels_right, out_channels_right, 7, 2, 3, name='specific', bias=False)
        self.comb_iter_2_left = AvgPoolPad()
        self.comb_iter_2_right = BranchSeparables(out_channels_right, out_channels_right, 5, 2, 2, name='specific', bias=False)
        self.comb_iter_3_right = nn.AvgPool2d(3, stride=1, padding=1, count_include_pad=False)
        self.comb_iter_4_left = BranchSeparables(out_channels_right, out_channels_right, 3, 1, 1, name='specific', bias=False)
        self.comb_iter_4_right = MaxPoolPad()

    def forward(self, x, x_prev):
        x_left = self.conv_prev_1x1(x_prev)
        x_right = self.conv_1x1(x)
        x_comb_iter_0_left = self.comb_iter_0_left(x_right)
        x_comb_iter_0_right = self.comb_iter_0_right(x_left)
        x_comb_iter_0 = x_comb_iter_0_left + x_comb_iter_0_right
        x_comb_iter_1_left = self.comb_iter_1_left(x_right)
        x_comb_iter_1_right = self.comb_iter_1_right(x_left)
        x_comb_iter_1 = x_comb_iter_1_left + x_comb_iter_1_right
        x_comb_iter_2_left = self.comb_iter_2_left(x_right)
        x_comb_iter_2_right = self.comb_iter_2_right(x_left)
        x_comb_iter_2 = x_comb_iter_2_left + x_comb_iter_2_right
        x_comb_iter_3_right = self.comb_iter_3_right(x_comb_iter_0)
        x_comb_iter_3 = x_comb_iter_3_right + x_comb_iter_1
        x_comb_iter_4_left = self.comb_iter_4_left(x_comb_iter_0)
        x_comb_iter_4_right = self.comb_iter_4_right(x_right)
        x_comb_iter_4 = x_comb_iter_4_left + x_comb_iter_4_right
        x_out = torch.cat([x_comb_iter_1, x_comb_iter_2, x_comb_iter_3, x_comb_iter_4], 1)
        return x_out

def forward(self, x, x_prev):
    x_left = self.conv_prev_1x1(x_prev)
    x_right = self.conv_1x1(x)
    x_comb_iter_0_left = self.comb_iter_0_left(x_right)
    x_comb_iter_0_right = self.comb_iter_0_right(x_left)
    x_comb_iter_0 = x_comb_iter_0_left + x_comb_iter_0_right
    x_comb_iter_1_left = self.comb_iter_1_left(x_right)
    x_comb_iter_1_right = self.comb_iter_1_right(x_left)
    x_comb_iter_1 = x_comb_iter_1_left + x_comb_iter_1_right
    x_comb_iter_2_left = self.comb_iter_2_left(x_right)
    x_comb_iter_2_right = self.comb_iter_2_right(x_left)
    x_comb_iter_2 = x_comb_iter_2_left + x_comb_iter_2_right
    x_comb_iter_3_right = self.comb_iter_3_right(x_comb_iter_0)
    x_comb_iter_3 = x_comb_iter_3_right + x_comb_iter_1
    x_comb_iter_4_left = self.comb_iter_4_left(x_comb_iter_0)
    x_comb_iter_4_right = self.comb_iter_4_right(x_right)
    x_comb_iter_4 = x_comb_iter_4_left + x_comb_iter_4_right
    x_out = torch.cat([x_comb_iter_1, x_comb_iter_2, x_comb_iter_3, x_comb_iter_4], 1)
    return x_out

