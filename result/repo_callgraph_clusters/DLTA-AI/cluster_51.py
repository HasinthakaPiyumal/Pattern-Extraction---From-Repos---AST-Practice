# Cluster 51

class SimplifiedBasicBlock(BaseModule):
    """Simplified version of original basic residual block. This is used in
    `SCNet <https://arxiv.org/abs/2012.10150>`_.

    - Norm layer is now optional
    - Last ReLU in forward function is removed
    """
    expansion = 1

    def __init__(self, inplanes, planes, stride=1, dilation=1, downsample=None, style='pytorch', with_cp=False, conv_cfg=None, norm_cfg=dict(type='BN'), dcn=None, plugins=None, init_fg=None):
        super(SimplifiedBasicBlock, self).__init__(init_fg)
        assert dcn is None, 'Not implemented yet.'
        assert plugins is None, 'Not implemented yet.'
        assert not with_cp, 'Not implemented yet.'
        self.with_norm = norm_cfg is not None
        with_bias = True if norm_cfg is None else False
        self.conv1 = build_conv_layer(conv_cfg, inplanes, planes, 3, stride=stride, padding=dilation, dilation=dilation, bias=with_bias)
        if self.with_norm:
            self.norm1_name, norm1 = build_norm_layer(norm_cfg, planes, postfix=1)
            self.add_module(self.norm1_name, norm1)
        self.conv2 = build_conv_layer(conv_cfg, planes, planes, 3, padding=1, bias=with_bias)
        if self.with_norm:
            self.norm2_name, norm2 = build_norm_layer(norm_cfg, planes, postfix=2)
            self.add_module(self.norm2_name, norm2)
        self.relu = nn.ReLU(inplace=True)
        self.downsample = downsample
        self.stride = stride
        self.dilation = dilation
        self.with_cp = with_cp

    @property
    def norm1(self):
        """nn.Module: normalization layer after the first convolution layer"""
        return getattr(self, self.norm1_name) if self.with_norm else None

    @property
    def norm2(self):
        """nn.Module: normalization layer after the second convolution layer"""
        return getattr(self, self.norm2_name) if self.with_norm else None

    def forward(self, x):
        """Forward function."""
        identity = x
        out = self.conv1(x)
        if self.with_norm:
            out = self.norm1(out)
        out = self.relu(out)
        out = self.conv2(out)
        if self.with_norm:
            out = self.norm2(out)
        if self.downsample is not None:
            identity = self.downsample(x)
        out += identity
        return out

def forward(self, x):
    """Forward function."""
    identity = x
    out = self.conv1(x)
    if self.with_norm:
        out = self.norm1(out)
    out = self.relu(out)
    out = self.conv2(out)
    if self.with_norm:
        out = self.norm2(out)
    if self.downsample is not None:
        identity = self.downsample(x)
    out += identity
    return out

class InvertedResidual(BaseModule):
    """Inverted Residual Block.

    Args:
        in_channels (int): The input channels of this Module.
        out_channels (int): The output channels of this Module.
        mid_channels (int): The input channels of the depthwise convolution.
        kernel_size (int): The kernel size of the depthwise convolution.
            Default: 3.
        stride (int): The stride of the depthwise convolution. Default: 1.
        se_cfg (dict): Config dict for se layer. Default: None, which means no
            se layer.
        with_expand_conv (bool): Use expand conv or not. If set False,
            mid_channels must be the same with in_channels.
            Default: True.
        conv_cfg (dict): Config dict for convolution layer. Default: None,
            which means using conv2d.
        norm_cfg (dict): Config dict for normalization layer.
            Default: dict(type='BN').
        act_cfg (dict): Config dict for activation layer.
            Default: dict(type='ReLU').
        drop_path_rate (float): stochastic depth rate. Defaults to 0.
        with_cp (bool): Use checkpoint or not. Using checkpoint will save some
            memory while slowing down the training speed. Default: False.
        init_cfg (dict or list[dict], optional): Initialization config dict.
            Default: None

    Returns:
        Tensor: The output tensor.
    """

    def __init__(self, in_channels, out_channels, mid_channels, kernel_size=3, stride=1, se_cfg=None, with_expand_conv=True, conv_cfg=None, norm_cfg=dict(type='BN'), act_cfg=dict(type='ReLU'), drop_path_rate=0.0, with_cp=False, init_cfg=None):
        super(InvertedResidual, self).__init__(init_cfg)
        self.with_res_shortcut = stride == 1 and in_channels == out_channels
        assert stride in [1, 2], f'stride must in [1, 2]. But received {stride}.'
        self.with_cp = with_cp
        self.drop_path = DropPath(drop_path_rate) if drop_path_rate > 0 else nn.Identity()
        self.with_se = se_cfg is not None
        self.with_expand_conv = with_expand_conv
        if self.with_se:
            assert isinstance(se_cfg, dict)
        if not self.with_expand_conv:
            assert mid_channels == in_channels
        if self.with_expand_conv:
            self.expand_conv = ConvModule(in_channels=in_channels, out_channels=mid_channels, kernel_size=1, stride=1, padding=0, conv_cfg=conv_cfg, norm_cfg=norm_cfg, act_cfg=act_cfg)
        self.depthwise_conv = ConvModule(in_channels=mid_channels, out_channels=mid_channels, kernel_size=kernel_size, stride=stride, padding=kernel_size // 2, groups=mid_channels, conv_cfg=conv_cfg, norm_cfg=norm_cfg, act_cfg=act_cfg)
        if self.with_se:
            self.se = SELayer(**se_cfg)
        self.linear_conv = ConvModule(in_channels=mid_channels, out_channels=out_channels, kernel_size=1, stride=1, padding=0, conv_cfg=conv_cfg, norm_cfg=norm_cfg, act_cfg=None)

    def forward(self, x):

        def _inner_forward(x):
            out = x
            if self.with_expand_conv:
                out = self.expand_conv(out)
            out = self.depthwise_conv(out)
            if self.with_se:
                out = self.se(out)
            out = self.linear_conv(out)
            if self.with_res_shortcut:
                return x + self.drop_path(out)
            else:
                return out
        if self.with_cp and x.requires_grad:
            out = cp.checkpoint(_inner_forward, x)
        else:
            out = _inner_forward(x)
        return out

def _inner_forward(x):
    out = x
    if self.with_expand_conv:
        out = self.expand_conv(out)
    out = self.depthwise_conv(out)
    if self.with_se:
        out = self.se(out)
    out = self.linear_conv(out)
    if self.with_res_shortcut:
        return x + self.drop_path(out)
    else:
        return out

def forward(self, x):

    def _inner_forward(x):
        out = x
        if self.with_expand_conv:
            out = self.expand_conv(out)
        out = self.depthwise_conv(out)
        if self.with_se:
            out = self.se(out)
        out = self.linear_conv(out)
        if self.with_res_shortcut:
            return x + self.drop_path(out)
        else:
            return out
    if self.with_cp and x.requires_grad:
        out = cp.checkpoint(_inner_forward, x)
    else:
        out = _inner_forward(x)
    return out

@LINEAR_LAYERS.register_module(name='NormedLinear')
class NormedLinear(nn.Linear):
    """Normalized Linear Layer.

    Args:
        tempeature (float, optional): Tempeature term. Default to 20.
        power (int, optional): Power term. Default to 1.0.
        eps (float, optional): The minimal value of divisor to
             keep numerical stability. Default to 1e-6.
    """

    def __init__(self, *args, tempearture=20, power=1.0, eps=1e-06, **kwargs):
        super(NormedLinear, self).__init__(*args, **kwargs)
        self.tempearture = tempearture
        self.power = power
        self.eps = eps
        self.init_weights()

    def init_weights(self):
        nn.init.normal_(self.weight, mean=0, std=0.01)
        if self.bias is not None:
            nn.init.constant_(self.bias, 0)

    def forward(self, x):
        weight_ = self.weight / (self.weight.norm(dim=1, keepdim=True).pow(self.power) + self.eps)
        x_ = x / (x.norm(dim=1, keepdim=True).pow(self.power) + self.eps)
        x_ = x_ * self.tempearture
        return F.linear(x_, weight_, self.bias)

def forward(self, x):
    weight_ = self.weight / (self.weight.norm(dim=1, keepdim=True).pow(self.power) + self.eps)
    x_ = x / (x.norm(dim=1, keepdim=True).pow(self.power) + self.eps)
    x_ = x_ * self.tempearture
    return F.linear(x_, weight_, self.bias)

class SELayer(BaseModule):
    """Squeeze-and-Excitation Module.

    Args:
        channels (int): The input (and output) channels of the SE layer.
        ratio (int): Squeeze ratio in SELayer, the intermediate channel will be
            ``int(channels/ratio)``. Default: 16.
        conv_cfg (None or dict): Config dict for convolution layer.
            Default: None, which means using conv2d.
        act_cfg (dict or Sequence[dict]): Config dict for activation layer.
            If act_cfg is a dict, two activation layers will be configurated
            by this dict. If act_cfg is a sequence of dicts, the first
            activation layer will be configurated by the first dict and the
            second activation layer will be configurated by the second dict.
            Default: (dict(type='ReLU'), dict(type='Sigmoid'))
        init_cfg (dict or list[dict], optional): Initialization config dict.
            Default: None
    """

    def __init__(self, channels, ratio=16, conv_cfg=None, act_cfg=(dict(type='ReLU'), dict(type='Sigmoid')), init_cfg=None):
        super(SELayer, self).__init__(init_cfg)
        if isinstance(act_cfg, dict):
            act_cfg = (act_cfg, act_cfg)
        assert len(act_cfg) == 2
        assert mmcv.is_tuple_of(act_cfg, dict)
        self.global_avgpool = nn.AdaptiveAvgPool2d(1)
        self.conv1 = ConvModule(in_channels=channels, out_channels=int(channels / ratio), kernel_size=1, stride=1, conv_cfg=conv_cfg, act_cfg=act_cfg[0])
        self.conv2 = ConvModule(in_channels=int(channels / ratio), out_channels=channels, kernel_size=1, stride=1, conv_cfg=conv_cfg, act_cfg=act_cfg[1])

    def forward(self, x):
        out = self.global_avgpool(x)
        out = self.conv1(out)
        out = self.conv2(out)
        return x * out

def forward(self, x):
    out = self.global_avgpool(x)
    out = self.conv1(out)
    out = self.conv2(out)
    return x * out

class DyReLU(BaseModule):
    """Dynamic ReLU (DyReLU) module.

    See `Dynamic ReLU <https://arxiv.org/abs/2003.10027>`_ for details.
    Current implementation is specialized for task-aware attention in DyHead.
    HSigmoid arguments in default act_cfg follow DyHead official code.
    https://github.com/microsoft/DynamicHead/blob/master/dyhead/dyrelu.py

    Args:
        channels (int): The input (and output) channels of DyReLU module.
        ratio (int): Squeeze ratio in Squeeze-and-Excitation-like module,
            the intermediate channel will be ``int(channels/ratio)``.
            Default: 4.
        conv_cfg (None or dict): Config dict for convolution layer.
            Default: None, which means using conv2d.
        act_cfg (dict or Sequence[dict]): Config dict for activation layer.
            If act_cfg is a dict, two activation layers will be configurated
            by this dict. If act_cfg is a sequence of dicts, the first
            activation layer will be configurated by the first dict and the
            second activation layer will be configurated by the second dict.
            Default: (dict(type='ReLU'), dict(type='HSigmoid', bias=3.0,
            divisor=6.0))
        init_cfg (dict or list[dict], optional): Initialization config dict.
            Default: None
    """

    def __init__(self, channels, ratio=4, conv_cfg=None, act_cfg=(dict(type='ReLU'), dict(type='HSigmoid', bias=3.0, divisor=6.0)), init_cfg=None):
        super().__init__(init_cfg=init_cfg)
        if isinstance(act_cfg, dict):
            act_cfg = (act_cfg, act_cfg)
        assert len(act_cfg) == 2
        assert mmcv.is_tuple_of(act_cfg, dict)
        self.channels = channels
        self.expansion = 4
        self.global_avgpool = nn.AdaptiveAvgPool2d(1)
        self.conv1 = ConvModule(in_channels=channels, out_channels=int(channels / ratio), kernel_size=1, stride=1, conv_cfg=conv_cfg, act_cfg=act_cfg[0])
        self.conv2 = ConvModule(in_channels=int(channels / ratio), out_channels=channels * self.expansion, kernel_size=1, stride=1, conv_cfg=conv_cfg, act_cfg=act_cfg[1])

    def forward(self, x):
        """Forward function."""
        coeffs = self.global_avgpool(x)
        coeffs = self.conv1(coeffs)
        coeffs = self.conv2(coeffs) - 0.5
        a1, b1, a2, b2 = torch.split(coeffs, self.channels, dim=1)
        a1 = a1 * 2.0 + 1.0
        a2 = a2 * 2.0
        out = torch.max(x * a1 + b1, x * a2 + b2)
        return out

def forward(self, x):
    """Forward function."""
    coeffs = self.global_avgpool(x)
    coeffs = self.conv1(coeffs)
    coeffs = self.conv2(coeffs) - 0.5
    a1, b1, a2, b2 = torch.split(coeffs, self.channels, dim=1)
    a1 = a1 * 2.0 + 1.0
    a2 = a2 * 2.0
    out = torch.max(x * a1 + b1, x * a2 + b2)
    return out

class DarknetBottleneck(BaseModule):
    """The basic bottleneck block used in Darknet.

    Each ResBlock consists of two ConvModules and the input is added to the
    final output. Each ConvModule is composed of Conv, BN, and LeakyReLU.
    The first convLayer has filter size of 1x1 and the second one has the
    filter size of 3x3.

    Args:
        in_channels (int): The input channels of this Module.
        out_channels (int): The output channels of this Module.
        expansion (int): The kernel size of the convolution. Default: 0.5
        add_identity (bool): Whether to add identity to the out.
            Default: True
        use_depthwise (bool): Whether to use depthwise separable convolution.
            Default: False
        conv_cfg (dict): Config dict for convolution layer. Default: None,
            which means using conv2d.
        norm_cfg (dict): Config dict for normalization layer.
            Default: dict(type='BN').
        act_cfg (dict): Config dict for activation layer.
            Default: dict(type='Swish').
    """

    def __init__(self, in_channels, out_channels, expansion=0.5, add_identity=True, use_depthwise=False, conv_cfg=None, norm_cfg=dict(type='BN', momentum=0.03, eps=0.001), act_cfg=dict(type='Swish'), init_cfg=None):
        super().__init__(init_cfg)
        hidden_channels = int(out_channels * expansion)
        conv = DepthwiseSeparableConvModule if use_depthwise else ConvModule
        self.conv1 = ConvModule(in_channels, hidden_channels, 1, conv_cfg=conv_cfg, norm_cfg=norm_cfg, act_cfg=act_cfg)
        self.conv2 = conv(hidden_channels, out_channels, 3, stride=1, padding=1, conv_cfg=conv_cfg, norm_cfg=norm_cfg, act_cfg=act_cfg)
        self.add_identity = add_identity and in_channels == out_channels

    def forward(self, x):
        identity = x
        out = self.conv1(x)
        out = self.conv2(out)
        if self.add_identity:
            return out + identity
        else:
            return out

def forward(self, x):
    identity = x
    out = self.conv1(x)
    out = self.conv2(out)
    if self.add_identity:
        return out + identity
    else:
        return out

class TridentConv(BaseModule):
    """Trident Convolution Module.

    Args:
        in_channels (int): Number of channels in input.
        out_channels (int): Number of channels in output.
        kernel_size (int): Size of convolution kernel.
        stride (int, optional): Convolution stride. Default: 1.
        trident_dilations (tuple[int, int, int], optional): Dilations of
            different trident branch. Default: (1, 2, 3).
        test_branch_idx (int, optional): In inference, all 3 branches will
            be used if `test_branch_idx==-1`, otherwise only branch with
            index `test_branch_idx` will be used. Default: 1.
        bias (bool, optional): Whether to use bias in convolution or not.
            Default: False.
        init_cfg (dict or list[dict], optional): Initialization config dict.
            Default: None
    """

    def __init__(self, in_channels, out_channels, kernel_size, stride=1, trident_dilations=(1, 2, 3), test_branch_idx=1, bias=False, init_cfg=None):
        super(TridentConv, self).__init__(init_cfg)
        self.num_branch = len(trident_dilations)
        self.with_bias = bias
        self.test_branch_idx = test_branch_idx
        self.stride = _pair(stride)
        self.kernel_size = _pair(kernel_size)
        self.paddings = _pair(trident_dilations)
        self.dilations = trident_dilations
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.bias = bias
        self.weight = nn.Parameter(torch.Tensor(out_channels, in_channels, *self.kernel_size))
        if bias:
            self.bias = nn.Parameter(torch.Tensor(out_channels))
        else:
            self.bias = None

    def extra_repr(self):
        tmpstr = f'in_channels={self.in_channels}'
        tmpstr += f', out_channels={self.out_channels}'
        tmpstr += f', kernel_size={self.kernel_size}'
        tmpstr += f', num_branch={self.num_branch}'
        tmpstr += f', test_branch_idx={self.test_branch_idx}'
        tmpstr += f', stride={self.stride}'
        tmpstr += f', paddings={self.paddings}'
        tmpstr += f', dilations={self.dilations}'
        tmpstr += f', bias={self.bias}'
        return tmpstr

    def forward(self, inputs):
        if self.training or self.test_branch_idx == -1:
            outputs = [F.conv2d(input, self.weight, self.bias, self.stride, padding, dilation) for input, dilation, padding in zip(inputs, self.dilations, self.paddings)]
        else:
            assert len(inputs) == 1
            outputs = [F.conv2d(inputs[0], self.weight, self.bias, self.stride, self.paddings[self.test_branch_idx], self.dilations[self.test_branch_idx])]
        return outputs

def forward(self, inputs):
    if self.training or self.test_branch_idx == -1:
        outputs = [F.conv2d(input, self.weight, self.bias, self.stride, padding, dilation) for input, dilation, padding in zip(inputs, self.dilations, self.paddings)]
    else:
        assert len(inputs) == 1
        outputs = [F.conv2d(inputs[0], self.weight, self.bias, self.stride, self.paddings[self.test_branch_idx], self.dilations[self.test_branch_idx])]
    return outputs

class TridentBottleneck(Bottleneck):
    """BottleBlock for TridentResNet.

    Args:
        trident_dilations (tuple[int, int, int]): Dilations of different
            trident branch.
        test_branch_idx (int): In inference, all 3 branches will be used
            if `test_branch_idx==-1`, otherwise only branch with index
            `test_branch_idx` will be used.
        concat_output (bool): Whether to concat the output list to a Tensor.
            `True` only in the last Block.
    """

    def __init__(self, trident_dilations, test_branch_idx, concat_output, **kwargs):
        super(TridentBottleneck, self).__init__(**kwargs)
        self.trident_dilations = trident_dilations
        self.num_branch = len(trident_dilations)
        self.concat_output = concat_output
        self.test_branch_idx = test_branch_idx
        self.conv2 = TridentConv(self.planes, self.planes, kernel_size=3, stride=self.conv2_stride, bias=False, trident_dilations=self.trident_dilations, test_branch_idx=test_branch_idx, init_cfg=dict(type='Kaiming', distribution='uniform', mode='fan_in', override=dict(name='conv2')))

    def forward(self, x):

        def _inner_forward(x):
            num_branch = self.num_branch if self.training or self.test_branch_idx == -1 else 1
            identity = x
            if not isinstance(x, list):
                x = (x,) * num_branch
                identity = x
                if self.downsample is not None:
                    identity = [self.downsample(b) for b in x]
            out = [self.conv1(b) for b in x]
            out = [self.norm1(b) for b in out]
            out = [self.relu(b) for b in out]
            if self.with_plugins:
                for k in range(len(out)):
                    out[k] = self.forward_plugin(out[k], self.after_conv1_plugin_names)
            out = self.conv2(out)
            out = [self.norm2(b) for b in out]
            out = [self.relu(b) for b in out]
            if self.with_plugins:
                for k in range(len(out)):
                    out[k] = self.forward_plugin(out[k], self.after_conv2_plugin_names)
            out = [self.conv3(b) for b in out]
            out = [self.norm3(b) for b in out]
            if self.with_plugins:
                for k in range(len(out)):
                    out[k] = self.forward_plugin(out[k], self.after_conv3_plugin_names)
            out = [out_b + identity_b for out_b, identity_b in zip(out, identity)]
            return out
        if self.with_cp and x.requires_grad:
            out = cp.checkpoint(_inner_forward, x)
        else:
            out = _inner_forward(x)
        out = [self.relu(b) for b in out]
        if self.concat_output:
            out = torch.cat(out, dim=0)
        return out

def _inner_forward(x):
    num_branch = self.num_branch if self.training or self.test_branch_idx == -1 else 1
    identity = x
    if not isinstance(x, list):
        x = (x,) * num_branch
        identity = x
        if self.downsample is not None:
            identity = [self.downsample(b) for b in x]
    out = [self.conv1(b) for b in x]
    out = [self.norm1(b) for b in out]
    out = [self.relu(b) for b in out]
    if self.with_plugins:
        for k in range(len(out)):
            out[k] = self.forward_plugin(out[k], self.after_conv1_plugin_names)
    out = self.conv2(out)
    out = [self.norm2(b) for b in out]
    out = [self.relu(b) for b in out]
    if self.with_plugins:
        for k in range(len(out)):
            out[k] = self.forward_plugin(out[k], self.after_conv2_plugin_names)
    out = [self.conv3(b) for b in out]
    out = [self.norm3(b) for b in out]
    if self.with_plugins:
        for k in range(len(out)):
            out[k] = self.forward_plugin(out[k], self.after_conv3_plugin_names)
    out = [out_b + identity_b for out_b, identity_b in zip(out, identity)]
    return out

def forward(self, x):

    def _inner_forward(x):
        num_branch = self.num_branch if self.training or self.test_branch_idx == -1 else 1
        identity = x
        if not isinstance(x, list):
            x = (x,) * num_branch
            identity = x
            if self.downsample is not None:
                identity = [self.downsample(b) for b in x]
        out = [self.conv1(b) for b in x]
        out = [self.norm1(b) for b in out]
        out = [self.relu(b) for b in out]
        if self.with_plugins:
            for k in range(len(out)):
                out[k] = self.forward_plugin(out[k], self.after_conv1_plugin_names)
        out = self.conv2(out)
        out = [self.norm2(b) for b in out]
        out = [self.relu(b) for b in out]
        if self.with_plugins:
            for k in range(len(out)):
                out[k] = self.forward_plugin(out[k], self.after_conv2_plugin_names)
        out = [self.conv3(b) for b in out]
        out = [self.norm3(b) for b in out]
        if self.with_plugins:
            for k in range(len(out)):
                out[k] = self.forward_plugin(out[k], self.after_conv3_plugin_names)
        out = [out_b + identity_b for out_b, identity_b in zip(out, identity)]
        return out
    if self.with_cp and x.requires_grad:
        out = cp.checkpoint(_inner_forward, x)
    else:
        out = _inner_forward(x)
    out = [self.relu(b) for b in out]
    if self.concat_output:
        out = torch.cat(out, dim=0)
    return out

@BACKBONES.register_module()
class RegNet(ResNet):
    """RegNet backbone.

    More details can be found in `paper <https://arxiv.org/abs/2003.13678>`_ .

    Args:
        arch (dict): The parameter of RegNets.

            - w0 (int): initial width
            - wa (float): slope of width
            - wm (float): quantization parameter to quantize the width
            - depth (int): depth of the backbone
            - group_w (int): width of group
            - bot_mul (float): bottleneck ratio, i.e. expansion of bottleneck.
        strides (Sequence[int]): Strides of the first block of each stage.
        base_channels (int): Base channels after stem layer.
        in_channels (int): Number of input image channels. Default: 3.
        dilations (Sequence[int]): Dilation of each stage.
        out_indices (Sequence[int]): Output from which stages.
        style (str): `pytorch` or `caffe`. If set to "pytorch", the stride-two
            layer is the 3x3 conv layer, otherwise the stride-two layer is
            the first 1x1 conv layer.
        frozen_stages (int): Stages to be frozen (all param fixed). -1 means
            not freezing any parameters.
        norm_cfg (dict): dictionary to construct and config norm layer.
        norm_eval (bool): Whether to set norm layers to eval mode, namely,
            freeze running stats (mean and var). Note: Effect on Batch Norm
            and its variants only.
        with_cp (bool): Use checkpoint or not. Using checkpoint will save some
            memory while slowing down the training speed.
        zero_init_residual (bool): whether to use zero init for last norm layer
            in resblocks to let them behave as identity.
        pretrained (str, optional): model pretrained path. Default: None
        init_cfg (dict or list[dict], optional): Initialization config dict.
            Default: None

    Example:
        >>> from mmdet.models import RegNet
        >>> import torch
        >>> self = RegNet(
                arch=dict(
                    w0=88,
                    wa=26.31,
                    wm=2.25,
                    group_w=48,
                    depth=25,
                    bot_mul=1.0))
        >>> self.eval()
        >>> inputs = torch.rand(1, 3, 32, 32)
        >>> level_outputs = self.forward(inputs)
        >>> for level_out in level_outputs:
        ...     print(tuple(level_out.shape))
        (1, 96, 8, 8)
        (1, 192, 4, 4)
        (1, 432, 2, 2)
        (1, 1008, 1, 1)
    """
    arch_settings = {'regnetx_400mf': dict(w0=24, wa=24.48, wm=2.54, group_w=16, depth=22, bot_mul=1.0), 'regnetx_800mf': dict(w0=56, wa=35.73, wm=2.28, group_w=16, depth=16, bot_mul=1.0), 'regnetx_1.6gf': dict(w0=80, wa=34.01, wm=2.25, group_w=24, depth=18, bot_mul=1.0), 'regnetx_3.2gf': dict(w0=88, wa=26.31, wm=2.25, group_w=48, depth=25, bot_mul=1.0), 'regnetx_4.0gf': dict(w0=96, wa=38.65, wm=2.43, group_w=40, depth=23, bot_mul=1.0), 'regnetx_6.4gf': dict(w0=184, wa=60.83, wm=2.07, group_w=56, depth=17, bot_mul=1.0), 'regnetx_8.0gf': dict(w0=80, wa=49.56, wm=2.88, group_w=120, depth=23, bot_mul=1.0), 'regnetx_12gf': dict(w0=168, wa=73.36, wm=2.37, group_w=112, depth=19, bot_mul=1.0)}

    def __init__(self, arch, in_channels=3, stem_channels=32, base_channels=32, strides=(2, 2, 2, 2), dilations=(1, 1, 1, 1), out_indices=(0, 1, 2, 3), style='pytorch', deep_stem=False, avg_down=False, frozen_stages=-1, conv_cfg=None, norm_cfg=dict(type='BN', requires_grad=True), norm_eval=True, dcn=None, stage_with_dcn=(False, False, False, False), plugins=None, with_cp=False, zero_init_residual=True, pretrained=None, init_cfg=None):
        super(ResNet, self).__init__(init_cfg)
        if isinstance(arch, str):
            assert arch in self.arch_settings, f'"arch": "{arch}" is not one of the arch_settings'
            arch = self.arch_settings[arch]
        elif not isinstance(arch, dict):
            raise ValueError(f'Expect "arch" to be either a string or a dict, got {type(arch)}')
        widths, num_stages = self.generate_regnet(arch['w0'], arch['wa'], arch['wm'], arch['depth'])
        stage_widths, stage_blocks = self.get_stages_from_blocks(widths)
        group_widths = [arch['group_w'] for _ in range(num_stages)]
        self.bottleneck_ratio = [arch['bot_mul'] for _ in range(num_stages)]
        stage_widths, group_widths = self.adjust_width_group(stage_widths, self.bottleneck_ratio, group_widths)
        self.stage_widths = stage_widths
        self.group_widths = group_widths
        self.depth = sum(stage_blocks)
        self.stem_channels = stem_channels
        self.base_channels = base_channels
        self.num_stages = num_stages
        assert num_stages >= 1 and num_stages <= 4
        self.strides = strides
        self.dilations = dilations
        assert len(strides) == len(dilations) == num_stages
        self.out_indices = out_indices
        assert max(out_indices) < num_stages
        self.style = style
        self.deep_stem = deep_stem
        self.avg_down = avg_down
        self.frozen_stages = frozen_stages
        self.conv_cfg = conv_cfg
        self.norm_cfg = norm_cfg
        self.with_cp = with_cp
        self.norm_eval = norm_eval
        self.dcn = dcn
        self.stage_with_dcn = stage_with_dcn
        if dcn is not None:
            assert len(stage_with_dcn) == num_stages
        self.plugins = plugins
        self.zero_init_residual = zero_init_residual
        self.block = Bottleneck
        expansion_bak = self.block.expansion
        self.block.expansion = 1
        self.stage_blocks = stage_blocks[:num_stages]
        self._make_stem_layer(in_channels, stem_channels)
        block_init_cfg = None
        assert not (init_cfg and pretrained), 'init_cfg and pretrained cannot be specified at the same time'
        if isinstance(pretrained, str):
            warnings.warn('DeprecationWarning: pretrained is deprecated, please use "init_cfg" instead')
            self.init_cfg = dict(type='Pretrained', checkpoint=pretrained)
        elif pretrained is None:
            if init_cfg is None:
                self.init_cfg = [dict(type='Kaiming', layer='Conv2d'), dict(type='Constant', val=1, layer=['_BatchNorm', 'GroupNorm'])]
                if self.zero_init_residual:
                    block_init_cfg = dict(type='Constant', val=0, override=dict(name='norm3'))
        else:
            raise TypeError('pretrained must be a str or None')
        self.inplanes = stem_channels
        self.res_layers = []
        for i, num_blocks in enumerate(self.stage_blocks):
            stride = self.strides[i]
            dilation = self.dilations[i]
            group_width = self.group_widths[i]
            width = int(round(self.stage_widths[i] * self.bottleneck_ratio[i]))
            stage_groups = width // group_width
            dcn = self.dcn if self.stage_with_dcn[i] else None
            if self.plugins is not None:
                stage_plugins = self.make_stage_plugins(self.plugins, i)
            else:
                stage_plugins = None
            res_layer = self.make_res_layer(block=self.block, inplanes=self.inplanes, planes=self.stage_widths[i], num_blocks=num_blocks, stride=stride, dilation=dilation, style=self.style, avg_down=self.avg_down, with_cp=self.with_cp, conv_cfg=self.conv_cfg, norm_cfg=self.norm_cfg, dcn=dcn, plugins=stage_plugins, groups=stage_groups, base_width=group_width, base_channels=self.stage_widths[i], init_cfg=block_init_cfg)
            self.inplanes = self.stage_widths[i]
            layer_name = f'layer{i + 1}'
            self.add_module(layer_name, res_layer)
            self.res_layers.append(layer_name)
        self._freeze_stages()
        self.feat_dim = stage_widths[-1]
        self.block.expansion = expansion_bak

    def _make_stem_layer(self, in_channels, base_channels):
        self.conv1 = build_conv_layer(self.conv_cfg, in_channels, base_channels, kernel_size=3, stride=2, padding=1, bias=False)
        self.norm1_name, norm1 = build_norm_layer(self.norm_cfg, base_channels, postfix=1)
        self.add_module(self.norm1_name, norm1)
        self.relu = nn.ReLU(inplace=True)

    def generate_regnet(self, initial_width, width_slope, width_parameter, depth, divisor=8):
        """Generates per block width from RegNet parameters.

        Args:
            initial_width ([int]): Initial width of the backbone
            width_slope ([float]): Slope of the quantized linear function
            width_parameter ([int]): Parameter used to quantize the width.
            depth ([int]): Depth of the backbone.
            divisor (int, optional): The divisor of channels. Defaults to 8.

        Returns:
            list, int: return a list of widths of each stage and the number                 of stages
        """
        assert width_slope >= 0
        assert initial_width > 0
        assert width_parameter > 1
        assert initial_width % divisor == 0
        widths_cont = np.arange(depth) * width_slope + initial_width
        ks = np.round(np.log(widths_cont / initial_width) / np.log(width_parameter))
        widths = initial_width * np.power(width_parameter, ks)
        widths = np.round(np.divide(widths, divisor)) * divisor
        num_stages = len(np.unique(widths))
        widths, widths_cont = (widths.astype(int).tolist(), widths_cont.tolist())
        return (widths, num_stages)

    @staticmethod
    def quantize_float(number, divisor):
        """Converts a float to closest non-zero int divisible by divisor.

        Args:
            number (int): Original number to be quantized.
            divisor (int): Divisor used to quantize the number.

        Returns:
            int: quantized number that is divisible by devisor.
        """
        return int(round(number / divisor) * divisor)

    def adjust_width_group(self, widths, bottleneck_ratio, groups):
        """Adjusts the compatibility of widths and groups.

        Args:
            widths (list[int]): Width of each stage.
            bottleneck_ratio (float): Bottleneck ratio.
            groups (int): number of groups in each stage

        Returns:
            tuple(list): The adjusted widths and groups of each stage.
        """
        bottleneck_width = [int(w * b) for w, b in zip(widths, bottleneck_ratio)]
        groups = [min(g, w_bot) for g, w_bot in zip(groups, bottleneck_width)]
        bottleneck_width = [self.quantize_float(w_bot, g) for w_bot, g in zip(bottleneck_width, groups)]
        widths = [int(w_bot / b) for w_bot, b in zip(bottleneck_width, bottleneck_ratio)]
        return (widths, groups)

    def get_stages_from_blocks(self, widths):
        """Gets widths/stage_blocks of network at each stage.

        Args:
            widths (list[int]): Width in each stage.

        Returns:
            tuple(list): width and depth of each stage
        """
        width_diff = [width != width_prev for width, width_prev in zip(widths + [0], [0] + widths)]
        stage_widths = [width for width, diff in zip(widths, width_diff[:-1]) if diff]
        stage_blocks = np.diff([depth for depth, diff in zip(range(len(width_diff)), width_diff) if diff]).tolist()
        return (stage_widths, stage_blocks)

    def forward(self, x):
        """Forward function."""
        x = self.conv1(x)
        x = self.norm1(x)
        x = self.relu(x)
        outs = []
        for i, layer_name in enumerate(self.res_layers):
            res_layer = getattr(self, layer_name)
            x = res_layer(x)
            if i in self.out_indices:
                outs.append(x)
        return tuple(outs)

def forward(self, x):
    """Forward function."""
    x = self.conv1(x)
    x = self.norm1(x)
    x = self.relu(x)
    outs = []
    for i, layer_name in enumerate(self.res_layers):
        res_layer = getattr(self, layer_name)
        x = res_layer(x)
        if i in self.out_indices:
            outs.append(x)
    return tuple(outs)

class SwinBlock(BaseModule):
    """"
    Args:
        embed_dims (int): The feature dimension.
        num_heads (int): Parallel attention heads.
        feedforward_channels (int): The hidden dimension for FFNs.
        window_size (int, optional): The local window scale. Default: 7.
        shift (bool, optional): whether to shift window or not. Default False.
        qkv_bias (bool, optional): enable bias for qkv if True. Default: True.
        qk_scale (float | None, optional): Override default qk scale of
            head_dim ** -0.5 if set. Default: None.
        drop_rate (float, optional): Dropout rate. Default: 0.
        attn_drop_rate (float, optional): Attention dropout rate. Default: 0.
        drop_path_rate (float, optional): Stochastic depth rate. Default: 0.
        act_cfg (dict, optional): The config dict of activation function.
            Default: dict(type='GELU').
        norm_cfg (dict, optional): The config dict of normalization.
            Default: dict(type='LN').
        with_cp (bool, optional): Use checkpoint or not. Using checkpoint
            will save some memory while slowing down the training speed.
            Default: False.
        init_cfg (dict | list | None, optional): The init config.
            Default: None.
    """

    def __init__(self, embed_dims, num_heads, feedforward_channels, window_size=7, shift=False, qkv_bias=True, qk_scale=None, drop_rate=0.0, attn_drop_rate=0.0, drop_path_rate=0.0, act_cfg=dict(type='GELU'), norm_cfg=dict(type='LN'), with_cp=False, init_cfg=None):
        super(SwinBlock, self).__init__()
        self.init_cfg = init_cfg
        self.with_cp = with_cp
        self.norm1 = build_norm_layer(norm_cfg, embed_dims)[1]
        self.attn = ShiftWindowMSA(embed_dims=embed_dims, num_heads=num_heads, window_size=window_size, shift_size=window_size // 2 if shift else 0, qkv_bias=qkv_bias, qk_scale=qk_scale, attn_drop_rate=attn_drop_rate, proj_drop_rate=drop_rate, dropout_layer=dict(type='DropPath', drop_prob=drop_path_rate), init_cfg=None)
        self.norm2 = build_norm_layer(norm_cfg, embed_dims)[1]
        self.ffn = FFN(embed_dims=embed_dims, feedforward_channels=feedforward_channels, num_fcs=2, ffn_drop=drop_rate, dropout_layer=dict(type='DropPath', drop_prob=drop_path_rate), act_cfg=act_cfg, add_identity=True, init_cfg=None)

    def forward(self, x, hw_shape):

        def _inner_forward(x):
            identity = x
            x = self.norm1(x)
            x = self.attn(x, hw_shape)
            x = x + identity
            identity = x
            x = self.norm2(x)
            x = self.ffn(x, identity=identity)
            return x
        if self.with_cp and x.requires_grad:
            x = cp.checkpoint(_inner_forward, x)
        else:
            x = _inner_forward(x)
        return x

def _inner_forward(x):
    identity = x
    x = self.norm1(x)
    x = self.attn(x, hw_shape)
    x = x + identity
    identity = x
    x = self.norm2(x)
    x = self.ffn(x, identity=identity)
    return x

def forward(self, x, hw_shape):

    def _inner_forward(x):
        identity = x
        x = self.norm1(x)
        x = self.attn(x, hw_shape)
        x = x + identity
        identity = x
        x = self.norm2(x)
        x = self.ffn(x, identity=identity)
        return x
    if self.with_cp and x.requires_grad:
        x = cp.checkpoint(_inner_forward, x)
    else:
        x = _inner_forward(x)
    return x

class SwinBlockSequence(BaseModule):
    """Implements one stage in Swin Transformer.

    Args:
        embed_dims (int): The feature dimension.
        num_heads (int): Parallel attention heads.
        feedforward_channels (int): The hidden dimension for FFNs.
        depth (int): The number of blocks in this stage.
        window_size (int, optional): The local window scale. Default: 7.
        qkv_bias (bool, optional): enable bias for qkv if True. Default: True.
        qk_scale (float | None, optional): Override default qk scale of
            head_dim ** -0.5 if set. Default: None.
        drop_rate (float, optional): Dropout rate. Default: 0.
        attn_drop_rate (float, optional): Attention dropout rate. Default: 0.
        drop_path_rate (float | list[float], optional): Stochastic depth
            rate. Default: 0.
        downsample (BaseModule | None, optional): The downsample operation
            module. Default: None.
        act_cfg (dict, optional): The config dict of activation function.
            Default: dict(type='GELU').
        norm_cfg (dict, optional): The config dict of normalization.
            Default: dict(type='LN').
        with_cp (bool, optional): Use checkpoint or not. Using checkpoint
            will save some memory while slowing down the training speed.
            Default: False.
        init_cfg (dict | list | None, optional): The init config.
            Default: None.
    """

    def __init__(self, embed_dims, num_heads, feedforward_channels, depth, window_size=7, qkv_bias=True, qk_scale=None, drop_rate=0.0, attn_drop_rate=0.0, drop_path_rate=0.0, downsample=None, act_cfg=dict(type='GELU'), norm_cfg=dict(type='LN'), with_cp=False, init_cfg=None):
        super().__init__(init_cfg=init_cfg)
        if isinstance(drop_path_rate, list):
            drop_path_rates = drop_path_rate
            assert len(drop_path_rates) == depth
        else:
            drop_path_rates = [deepcopy(drop_path_rate) for _ in range(depth)]
        self.blocks = ModuleList()
        for i in range(depth):
            block = SwinBlock(embed_dims=embed_dims, num_heads=num_heads, feedforward_channels=feedforward_channels, window_size=window_size, shift=False if i % 2 == 0 else True, qkv_bias=qkv_bias, qk_scale=qk_scale, drop_rate=drop_rate, attn_drop_rate=attn_drop_rate, drop_path_rate=drop_path_rates[i], act_cfg=act_cfg, norm_cfg=norm_cfg, with_cp=with_cp, init_cfg=None)
            self.blocks.append(block)
        self.downsample = downsample

    def forward(self, x, hw_shape):
        for block in self.blocks:
            x = block(x, hw_shape)
        if self.downsample:
            x_down, down_hw_shape = self.downsample(x, hw_shape)
            return (x_down, down_hw_shape, x, hw_shape)
        else:
            return (x, hw_shape, x, hw_shape)

def forward(self, x, hw_shape):
    for block in self.blocks:
        x = block(x, hw_shape)
    if self.downsample:
        x_down, down_hw_shape = self.downsample(x, hw_shape)
        return (x_down, down_hw_shape, x, hw_shape)
    else:
        return (x, hw_shape, x, hw_shape)

class Bottleneck(_Bottleneck):
    """Bottleneck for the ResNet backbone in `DetectoRS
    <https://arxiv.org/pdf/2006.02334.pdf>`_.

    This bottleneck allows the users to specify whether to use
    SAC (Switchable Atrous Convolution) and RFP (Recursive Feature Pyramid).

    Args:
         inplanes (int): The number of input channels.
         planes (int): The number of output channels before expansion.
         rfp_inplanes (int, optional): The number of channels from RFP.
             Default: None. If specified, an additional conv layer will be
             added for ``rfp_feat``. Otherwise, the structure is the same as
             base class.
         sac (dict, optional): Dictionary to construct SAC. Default: None.
         init_cfg (dict or list[dict], optional): Initialization config dict.
            Default: None
    """
    expansion = 4

    def __init__(self, inplanes, planes, rfp_inplanes=None, sac=None, init_cfg=None, **kwargs):
        super(Bottleneck, self).__init__(inplanes, planes, init_cfg=init_cfg, **kwargs)
        assert sac is None or isinstance(sac, dict)
        self.sac = sac
        self.with_sac = sac is not None
        if self.with_sac:
            self.conv2 = build_conv_layer(self.sac, planes, planes, kernel_size=3, stride=self.conv2_stride, padding=self.dilation, dilation=self.dilation, bias=False)
        self.rfp_inplanes = rfp_inplanes
        if self.rfp_inplanes:
            self.rfp_conv = build_conv_layer(None, self.rfp_inplanes, planes * self.expansion, 1, stride=1, bias=True)
            if init_cfg is None:
                self.init_cfg = dict(type='Constant', val=0, override=dict(name='rfp_conv'))

    def rfp_forward(self, x, rfp_feat):
        """The forward function that also takes the RFP features as input."""

        def _inner_forward(x):
            identity = x
            out = self.conv1(x)
            out = self.norm1(out)
            out = self.relu(out)
            if self.with_plugins:
                out = self.forward_plugin(out, self.after_conv1_plugin_names)
            out = self.conv2(out)
            out = self.norm2(out)
            out = self.relu(out)
            if self.with_plugins:
                out = self.forward_plugin(out, self.after_conv2_plugin_names)
            out = self.conv3(out)
            out = self.norm3(out)
            if self.with_plugins:
                out = self.forward_plugin(out, self.after_conv3_plugin_names)
            if self.downsample is not None:
                identity = self.downsample(x)
            out += identity
            return out
        if self.with_cp and x.requires_grad:
            out = cp.checkpoint(_inner_forward, x)
        else:
            out = _inner_forward(x)
        if self.rfp_inplanes:
            rfp_feat = self.rfp_conv(rfp_feat)
            out = out + rfp_feat
        out = self.relu(out)
        return out

def _inner_forward(x):
    identity = x
    out = self.conv1(x)
    out = self.norm1(out)
    out = self.relu(out)
    if self.with_plugins:
        out = self.forward_plugin(out, self.after_conv1_plugin_names)
    out = self.conv2(out)
    out = self.norm2(out)
    out = self.relu(out)
    if self.with_plugins:
        out = self.forward_plugin(out, self.after_conv2_plugin_names)
    out = self.conv3(out)
    out = self.norm3(out)
    if self.with_plugins:
        out = self.forward_plugin(out, self.after_conv3_plugin_names)
    if self.downsample is not None:
        identity = self.downsample(x)
    out += identity
    return out

def rfp_forward(self, x, rfp_feat):
    """The forward function that also takes the RFP features as input."""

    def _inner_forward(x):
        identity = x
        out = self.conv1(x)
        out = self.norm1(out)
        out = self.relu(out)
        if self.with_plugins:
            out = self.forward_plugin(out, self.after_conv1_plugin_names)
        out = self.conv2(out)
        out = self.norm2(out)
        out = self.relu(out)
        if self.with_plugins:
            out = self.forward_plugin(out, self.after_conv2_plugin_names)
        out = self.conv3(out)
        out = self.norm3(out)
        if self.with_plugins:
            out = self.forward_plugin(out, self.after_conv3_plugin_names)
        if self.downsample is not None:
            identity = self.downsample(x)
        out += identity
        return out
    if self.with_cp and x.requires_grad:
        out = cp.checkpoint(_inner_forward, x)
    else:
        out = _inner_forward(x)
    if self.rfp_inplanes:
        rfp_feat = self.rfp_conv(rfp_feat)
        out = out + rfp_feat
    out = self.relu(out)
    return out

@BACKBONES.register_module()
class DetectoRS_ResNet(ResNet):
    """ResNet backbone for DetectoRS.

    Args:
        sac (dict, optional): Dictionary to construct SAC (Switchable Atrous
            Convolution). Default: None.
        stage_with_sac (list): Which stage to use sac. Default: (False, False,
            False, False).
        rfp_inplanes (int, optional): The number of channels from RFP.
            Default: None. If specified, an additional conv layer will be
            added for ``rfp_feat``. Otherwise, the structure is the same as
            base class.
        output_img (bool): If ``True``, the input image will be inserted into
            the starting position of output. Default: False.
    """
    arch_settings = {50: (Bottleneck, (3, 4, 6, 3)), 101: (Bottleneck, (3, 4, 23, 3)), 152: (Bottleneck, (3, 8, 36, 3))}

    def __init__(self, sac=None, stage_with_sac=(False, False, False, False), rfp_inplanes=None, output_img=False, pretrained=None, init_cfg=None, **kwargs):
        assert not (init_cfg and pretrained), 'init_cfg and pretrained cannot be specified at the same time'
        self.pretrained = pretrained
        if init_cfg is not None:
            assert isinstance(init_cfg, dict), f'init_cfg must be a dict, but got {type(init_cfg)}'
            if 'type' in init_cfg:
                assert init_cfg.get('type') == 'Pretrained', 'Only can initialize module by loading a pretrained model'
            else:
                raise KeyError('`init_cfg` must contain the key "type"')
            self.pretrained = init_cfg.get('checkpoint')
        self.sac = sac
        self.stage_with_sac = stage_with_sac
        self.rfp_inplanes = rfp_inplanes
        self.output_img = output_img
        super(DetectoRS_ResNet, self).__init__(**kwargs)
        self.inplanes = self.stem_channels
        self.res_layers = []
        for i, num_blocks in enumerate(self.stage_blocks):
            stride = self.strides[i]
            dilation = self.dilations[i]
            dcn = self.dcn if self.stage_with_dcn[i] else None
            sac = self.sac if self.stage_with_sac[i] else None
            if self.plugins is not None:
                stage_plugins = self.make_stage_plugins(self.plugins, i)
            else:
                stage_plugins = None
            planes = self.base_channels * 2 ** i
            res_layer = self.make_res_layer(block=self.block, inplanes=self.inplanes, planes=planes, num_blocks=num_blocks, stride=stride, dilation=dilation, style=self.style, avg_down=self.avg_down, with_cp=self.with_cp, conv_cfg=self.conv_cfg, norm_cfg=self.norm_cfg, dcn=dcn, sac=sac, rfp_inplanes=rfp_inplanes if i > 0 else None, plugins=stage_plugins)
            self.inplanes = planes * self.block.expansion
            layer_name = f'layer{i + 1}'
            self.add_module(layer_name, res_layer)
            self.res_layers.append(layer_name)
        self._freeze_stages()

    def init_weights(self):
        if isinstance(self.pretrained, str):
            logger = get_root_logger()
            load_checkpoint(self, self.pretrained, strict=False, logger=logger)
        elif self.pretrained is None:
            for m in self.modules():
                if isinstance(m, nn.Conv2d):
                    kaiming_init(m)
                elif isinstance(m, (_BatchNorm, nn.GroupNorm)):
                    constant_init(m, 1)
            if self.dcn is not None:
                for m in self.modules():
                    if isinstance(m, Bottleneck) and hasattr(m.conv2, 'conv_offset'):
                        constant_init(m.conv2.conv_offset, 0)
            if self.zero_init_residual:
                for m in self.modules():
                    if isinstance(m, Bottleneck):
                        constant_init(m.norm3, 0)
                    elif isinstance(m, BasicBlock):
                        constant_init(m.norm2, 0)
        else:
            raise TypeError('pretrained must be a str or None')

    def make_res_layer(self, **kwargs):
        """Pack all blocks in a stage into a ``ResLayer`` for DetectoRS."""
        return ResLayer(**kwargs)

    def forward(self, x):
        """Forward function."""
        outs = list(super(DetectoRS_ResNet, self).forward(x))
        if self.output_img:
            outs.insert(0, x)
        return tuple(outs)

    def rfp_forward(self, x, rfp_feats):
        """Forward function for RFP."""
        if self.deep_stem:
            x = self.stem(x)
        else:
            x = self.conv1(x)
            x = self.norm1(x)
            x = self.relu(x)
        x = self.maxpool(x)
        outs = []
        for i, layer_name in enumerate(self.res_layers):
            res_layer = getattr(self, layer_name)
            rfp_feat = rfp_feats[i] if i > 0 else None
            for layer in res_layer:
                x = layer.rfp_forward(x, rfp_feat)
            if i in self.out_indices:
                outs.append(x)
        return tuple(outs)

def rfp_forward(self, x, rfp_feats):
    """Forward function for RFP."""
    if self.deep_stem:
        x = self.stem(x)
    else:
        x = self.conv1(x)
        x = self.norm1(x)
        x = self.relu(x)
    x = self.maxpool(x)
    outs = []
    for i, layer_name in enumerate(self.res_layers):
        res_layer = getattr(self, layer_name)
        rfp_feat = rfp_feats[i] if i > 0 else None
        for layer in res_layer:
            x = layer.rfp_forward(x, rfp_feat)
        if i in self.out_indices:
            outs.append(x)
    return tuple(outs)

class EdgeResidual(BaseModule):
    """Edge Residual Block.

    Args:
        in_channels (int): The input channels of this module.
        out_channels (int): The output channels of this module.
        mid_channels (int): The input channels of the second convolution.
        kernel_size (int): The kernel size of the first convolution.
            Defaults to 3.
        stride (int): The stride of the first convolution. Defaults to 1.
        se_cfg (dict, optional): Config dict for se layer. Defaults to None,
            which means no se layer.
        with_residual (bool): Use residual connection. Defaults to True.
        conv_cfg (dict, optional): Config dict for convolution layer.
            Defaults to None, which means using conv2d.
        norm_cfg (dict): Config dict for normalization layer.
            Defaults to ``dict(type='BN')``.
        act_cfg (dict): Config dict for activation layer.
            Defaults to ``dict(type='ReLU')``.
        drop_path_rate (float): stochastic depth rate. Defaults to 0.
        with_cp (bool): Use checkpoint or not. Using checkpoint will save some
            memory while slowing down the training speed. Defaults to False.
        init_cfg (dict | list[dict], optional): Initialization config dict.
    """

    def __init__(self, in_channels, out_channels, mid_channels, kernel_size=3, stride=1, se_cfg=None, with_residual=True, conv_cfg=None, norm_cfg=dict(type='BN'), act_cfg=dict(type='ReLU'), drop_path_rate=0.0, with_cp=False, init_cfg=None, **kwargs):
        super(EdgeResidual, self).__init__(init_cfg=init_cfg)
        assert stride in [1, 2]
        self.with_cp = with_cp
        self.drop_path = DropPath(drop_path_rate) if drop_path_rate > 0 else nn.Identity()
        self.with_se = se_cfg is not None
        self.with_residual = stride == 1 and in_channels == out_channels and with_residual
        if self.with_se:
            assert isinstance(se_cfg, dict)
        self.conv1 = ConvModule(in_channels=in_channels, out_channels=mid_channels, kernel_size=kernel_size, stride=1, padding=kernel_size // 2, conv_cfg=conv_cfg, norm_cfg=norm_cfg, act_cfg=act_cfg)
        if self.with_se:
            self.se = SELayer(**se_cfg)
        self.conv2 = ConvModule(in_channels=mid_channels, out_channels=out_channels, kernel_size=1, stride=stride, padding=0, conv_cfg=conv_cfg, norm_cfg=norm_cfg, act_cfg=None)

    def forward(self, x):

        def _inner_forward(x):
            out = x
            out = self.conv1(out)
            if self.with_se:
                out = self.se(out)
            out = self.conv2(out)
            if self.with_residual:
                return x + self.drop_path(out)
            else:
                return out
        if self.with_cp and x.requires_grad:
            out = cp.checkpoint(_inner_forward, x)
        else:
            out = _inner_forward(x)
        return out

def _inner_forward(x):
    out = x
    out = self.conv1(out)
    if self.with_se:
        out = self.se(out)
    out = self.conv2(out)
    if self.with_residual:
        return x + self.drop_path(out)
    else:
        return out

def forward(self, x):

    def _inner_forward(x):
        out = x
        out = self.conv1(out)
        if self.with_se:
            out = self.se(out)
        out = self.conv2(out)
        if self.with_residual:
            return x + self.drop_path(out)
        else:
            return out
    if self.with_cp and x.requires_grad:
        out = cp.checkpoint(_inner_forward, x)
    else:
        out = _inner_forward(x)
    return out

class BasicBlock(BaseModule):
    expansion = 1

    def __init__(self, inplanes, planes, stride=1, dilation=1, downsample=None, style='pytorch', with_cp=False, conv_cfg=None, norm_cfg=dict(type='BN'), dcn=None, plugins=None, init_cfg=None):
        super(BasicBlock, self).__init__(init_cfg)
        assert dcn is None, 'Not implemented yet.'
        assert plugins is None, 'Not implemented yet.'
        self.norm1_name, norm1 = build_norm_layer(norm_cfg, planes, postfix=1)
        self.norm2_name, norm2 = build_norm_layer(norm_cfg, planes, postfix=2)
        self.conv1 = build_conv_layer(conv_cfg, inplanes, planes, 3, stride=stride, padding=dilation, dilation=dilation, bias=False)
        self.add_module(self.norm1_name, norm1)
        self.conv2 = build_conv_layer(conv_cfg, planes, planes, 3, padding=1, bias=False)
        self.add_module(self.norm2_name, norm2)
        self.relu = nn.ReLU(inplace=True)
        self.downsample = downsample
        self.stride = stride
        self.dilation = dilation
        self.with_cp = with_cp

    @property
    def norm1(self):
        """nn.Module: normalization layer after the first convolution layer"""
        return getattr(self, self.norm1_name)

    @property
    def norm2(self):
        """nn.Module: normalization layer after the second convolution layer"""
        return getattr(self, self.norm2_name)

    def forward(self, x):
        """Forward function."""

        def _inner_forward(x):
            identity = x
            out = self.conv1(x)
            out = self.norm1(out)
            out = self.relu(out)
            out = self.conv2(out)
            out = self.norm2(out)
            if self.downsample is not None:
                identity = self.downsample(x)
            out += identity
            return out
        if self.with_cp and x.requires_grad:
            out = cp.checkpoint(_inner_forward, x)
        else:
            out = _inner_forward(x)
        out = self.relu(out)
        return out

def _inner_forward(x):
    identity = x
    out = self.conv1(x)
    out = self.norm1(out)
    out = self.relu(out)
    out = self.conv2(out)
    out = self.norm2(out)
    if self.downsample is not None:
        identity = self.downsample(x)
    out += identity
    return out

def forward(self, x):
    """Forward function."""

    def _inner_forward(x):
        identity = x
        out = self.conv1(x)
        out = self.norm1(out)
        out = self.relu(out)
        out = self.conv2(out)
        out = self.norm2(out)
        if self.downsample is not None:
            identity = self.downsample(x)
        out += identity
        return out
    if self.with_cp and x.requires_grad:
        out = cp.checkpoint(_inner_forward, x)
    else:
        out = _inner_forward(x)
    out = self.relu(out)
    return out

class Bottleneck(BaseModule):
    expansion = 4

    def __init__(self, inplanes, planes, stride=1, dilation=1, downsample=None, style='pytorch', with_cp=False, conv_cfg=None, norm_cfg=dict(type='BN'), dcn=None, plugins=None, init_cfg=None):
        """Bottleneck block for ResNet.

        If style is "pytorch", the stride-two layer is the 3x3 conv layer, if
        it is "caffe", the stride-two layer is the first 1x1 conv layer.
        """
        super(Bottleneck, self).__init__(init_cfg)
        assert style in ['pytorch', 'caffe']
        assert dcn is None or isinstance(dcn, dict)
        assert plugins is None or isinstance(plugins, list)
        if plugins is not None:
            allowed_position = ['after_conv1', 'after_conv2', 'after_conv3']
            assert all((p['position'] in allowed_position for p in plugins))
        self.inplanes = inplanes
        self.planes = planes
        self.stride = stride
        self.dilation = dilation
        self.style = style
        self.with_cp = with_cp
        self.conv_cfg = conv_cfg
        self.norm_cfg = norm_cfg
        self.dcn = dcn
        self.with_dcn = dcn is not None
        self.plugins = plugins
        self.with_plugins = plugins is not None
        if self.with_plugins:
            self.after_conv1_plugins = [plugin['cfg'] for plugin in plugins if plugin['position'] == 'after_conv1']
            self.after_conv2_plugins = [plugin['cfg'] for plugin in plugins if plugin['position'] == 'after_conv2']
            self.after_conv3_plugins = [plugin['cfg'] for plugin in plugins if plugin['position'] == 'after_conv3']
        if self.style == 'pytorch':
            self.conv1_stride = 1
            self.conv2_stride = stride
        else:
            self.conv1_stride = stride
            self.conv2_stride = 1
        self.norm1_name, norm1 = build_norm_layer(norm_cfg, planes, postfix=1)
        self.norm2_name, norm2 = build_norm_layer(norm_cfg, planes, postfix=2)
        self.norm3_name, norm3 = build_norm_layer(norm_cfg, planes * self.expansion, postfix=3)
        self.conv1 = build_conv_layer(conv_cfg, inplanes, planes, kernel_size=1, stride=self.conv1_stride, bias=False)
        self.add_module(self.norm1_name, norm1)
        fallback_on_stride = False
        if self.with_dcn:
            fallback_on_stride = dcn.pop('fallback_on_stride', False)
        if not self.with_dcn or fallback_on_stride:
            self.conv2 = build_conv_layer(conv_cfg, planes, planes, kernel_size=3, stride=self.conv2_stride, padding=dilation, dilation=dilation, bias=False)
        else:
            assert self.conv_cfg is None, 'conv_cfg must be None for DCN'
            self.conv2 = build_conv_layer(dcn, planes, planes, kernel_size=3, stride=self.conv2_stride, padding=dilation, dilation=dilation, bias=False)
        self.add_module(self.norm2_name, norm2)
        self.conv3 = build_conv_layer(conv_cfg, planes, planes * self.expansion, kernel_size=1, bias=False)
        self.add_module(self.norm3_name, norm3)
        self.relu = nn.ReLU(inplace=True)
        self.downsample = downsample
        if self.with_plugins:
            self.after_conv1_plugin_names = self.make_block_plugins(planes, self.after_conv1_plugins)
            self.after_conv2_plugin_names = self.make_block_plugins(planes, self.after_conv2_plugins)
            self.after_conv3_plugin_names = self.make_block_plugins(planes * self.expansion, self.after_conv3_plugins)

    def make_block_plugins(self, in_channels, plugins):
        """make plugins for block.

        Args:
            in_channels (int): Input channels of plugin.
            plugins (list[dict]): List of plugins cfg to build.

        Returns:
            list[str]: List of the names of plugin.
        """
        assert isinstance(plugins, list)
        plugin_names = []
        for plugin in plugins:
            plugin = plugin.copy()
            name, layer = build_plugin_layer(plugin, in_channels=in_channels, postfix=plugin.pop('postfix', ''))
            assert not hasattr(self, name), f'duplicate plugin {name}'
            self.add_module(name, layer)
            plugin_names.append(name)
        return plugin_names

    def forward_plugin(self, x, plugin_names):
        out = x
        for name in plugin_names:
            out = getattr(self, name)(out)
        return out

    @property
    def norm1(self):
        """nn.Module: normalization layer after the first convolution layer"""
        return getattr(self, self.norm1_name)

    @property
    def norm2(self):
        """nn.Module: normalization layer after the second convolution layer"""
        return getattr(self, self.norm2_name)

    @property
    def norm3(self):
        """nn.Module: normalization layer after the third convolution layer"""
        return getattr(self, self.norm3_name)

    def forward(self, x):
        """Forward function."""

        def _inner_forward(x):
            identity = x
            out = self.conv1(x)
            out = self.norm1(out)
            out = self.relu(out)
            if self.with_plugins:
                out = self.forward_plugin(out, self.after_conv1_plugin_names)
            out = self.conv2(out)
            out = self.norm2(out)
            out = self.relu(out)
            if self.with_plugins:
                out = self.forward_plugin(out, self.after_conv2_plugin_names)
            out = self.conv3(out)
            out = self.norm3(out)
            if self.with_plugins:
                out = self.forward_plugin(out, self.after_conv3_plugin_names)
            if self.downsample is not None:
                identity = self.downsample(x)
            out += identity
            return out
        if self.with_cp and x.requires_grad:
            out = cp.checkpoint(_inner_forward, x)
        else:
            out = _inner_forward(x)
        out = self.relu(out)
        return out

def _inner_forward(x):
    identity = x
    out = self.conv1(x)
    out = self.norm1(out)
    out = self.relu(out)
    if self.with_plugins:
        out = self.forward_plugin(out, self.after_conv1_plugin_names)
    out = self.conv2(out)
    out = self.norm2(out)
    out = self.relu(out)
    if self.with_plugins:
        out = self.forward_plugin(out, self.after_conv2_plugin_names)
    out = self.conv3(out)
    out = self.norm3(out)
    if self.with_plugins:
        out = self.forward_plugin(out, self.after_conv3_plugin_names)
    if self.downsample is not None:
        identity = self.downsample(x)
    out += identity
    return out

def forward(self, x):
    """Forward function."""

    def _inner_forward(x):
        identity = x
        out = self.conv1(x)
        out = self.norm1(out)
        out = self.relu(out)
        if self.with_plugins:
            out = self.forward_plugin(out, self.after_conv1_plugin_names)
        out = self.conv2(out)
        out = self.norm2(out)
        out = self.relu(out)
        if self.with_plugins:
            out = self.forward_plugin(out, self.after_conv2_plugin_names)
        out = self.conv3(out)
        out = self.norm3(out)
        if self.with_plugins:
            out = self.forward_plugin(out, self.after_conv3_plugin_names)
        if self.downsample is not None:
            identity = self.downsample(x)
        out += identity
        return out
    if self.with_cp and x.requires_grad:
        out = cp.checkpoint(_inner_forward, x)
    else:
        out = _inner_forward(x)
    out = self.relu(out)
    return out

@BACKBONES.register_module()
class ResNet(BaseModule):
    """ResNet backbone.

    Args:
        depth (int): Depth of resnet, from {18, 34, 50, 101, 152}.
        stem_channels (int | None): Number of stem channels. If not specified,
            it will be the same as `base_channels`. Default: None.
        base_channels (int): Number of base channels of res layer. Default: 64.
        in_channels (int): Number of input image channels. Default: 3.
        num_stages (int): Resnet stages. Default: 4.
        strides (Sequence[int]): Strides of the first block of each stage.
        dilations (Sequence[int]): Dilation of each stage.
        out_indices (Sequence[int]): Output from which stages.
        style (str): `pytorch` or `caffe`. If set to "pytorch", the stride-two
            layer is the 3x3 conv layer, otherwise the stride-two layer is
            the first 1x1 conv layer.
        deep_stem (bool): Replace 7x7 conv in input stem with 3 3x3 conv
        avg_down (bool): Use AvgPool instead of stride conv when
            downsampling in the bottleneck.
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
        >>> from mmdet.models import ResNet
        >>> import torch
        >>> self = ResNet(depth=18)
        >>> self.eval()
        >>> inputs = torch.rand(1, 3, 32, 32)
        >>> level_outputs = self.forward(inputs)
        >>> for level_out in level_outputs:
        ...     print(tuple(level_out.shape))
        (1, 64, 8, 8)
        (1, 128, 4, 4)
        (1, 256, 2, 2)
        (1, 512, 1, 1)
    """
    arch_settings = {18: (BasicBlock, (2, 2, 2, 2)), 34: (BasicBlock, (3, 4, 6, 3)), 50: (Bottleneck, (3, 4, 6, 3)), 101: (Bottleneck, (3, 4, 23, 3)), 152: (Bottleneck, (3, 8, 36, 3))}

    def __init__(self, depth, in_channels=3, stem_channels=None, base_channels=64, num_stages=4, strides=(1, 2, 2, 2), dilations=(1, 1, 1, 1), out_indices=(0, 1, 2, 3), style='pytorch', deep_stem=False, avg_down=False, frozen_stages=-1, conv_cfg=None, norm_cfg=dict(type='BN', requires_grad=True), norm_eval=True, dcn=None, stage_with_dcn=(False, False, False, False), plugins=None, with_cp=False, zero_init_residual=True, pretrained=None, init_cfg=None):
        super(ResNet, self).__init__(init_cfg)
        self.zero_init_residual = zero_init_residual
        if depth not in self.arch_settings:
            raise KeyError(f'invalid depth {depth} for resnet')
        block_init_cfg = None
        assert not (init_cfg and pretrained), 'init_cfg and pretrained cannot be specified at the same time'
        if isinstance(pretrained, str):
            warnings.warn('DeprecationWarning: pretrained is deprecated, please use "init_cfg" instead')
            self.init_cfg = dict(type='Pretrained', checkpoint=pretrained)
        elif pretrained is None:
            if init_cfg is None:
                self.init_cfg = [dict(type='Kaiming', layer='Conv2d'), dict(type='Constant', val=1, layer=['_BatchNorm', 'GroupNorm'])]
                block = self.arch_settings[depth][0]
                if self.zero_init_residual:
                    if block is BasicBlock:
                        block_init_cfg = dict(type='Constant', val=0, override=dict(name='norm2'))
                    elif block is Bottleneck:
                        block_init_cfg = dict(type='Constant', val=0, override=dict(name='norm3'))
        else:
            raise TypeError('pretrained must be a str or None')
        self.depth = depth
        if stem_channels is None:
            stem_channels = base_channels
        self.stem_channels = stem_channels
        self.base_channels = base_channels
        self.num_stages = num_stages
        assert num_stages >= 1 and num_stages <= 4
        self.strides = strides
        self.dilations = dilations
        assert len(strides) == len(dilations) == num_stages
        self.out_indices = out_indices
        assert max(out_indices) < num_stages
        self.style = style
        self.deep_stem = deep_stem
        self.avg_down = avg_down
        self.frozen_stages = frozen_stages
        self.conv_cfg = conv_cfg
        self.norm_cfg = norm_cfg
        self.with_cp = with_cp
        self.norm_eval = norm_eval
        self.dcn = dcn
        self.stage_with_dcn = stage_with_dcn
        if dcn is not None:
            assert len(stage_with_dcn) == num_stages
        self.plugins = plugins
        self.block, stage_blocks = self.arch_settings[depth]
        self.stage_blocks = stage_blocks[:num_stages]
        self.inplanes = stem_channels
        self._make_stem_layer(in_channels, stem_channels)
        self.res_layers = []
        for i, num_blocks in enumerate(self.stage_blocks):
            stride = strides[i]
            dilation = dilations[i]
            dcn = self.dcn if self.stage_with_dcn[i] else None
            if plugins is not None:
                stage_plugins = self.make_stage_plugins(plugins, i)
            else:
                stage_plugins = None
            planes = base_channels * 2 ** i
            res_layer = self.make_res_layer(block=self.block, inplanes=self.inplanes, planes=planes, num_blocks=num_blocks, stride=stride, dilation=dilation, style=self.style, avg_down=self.avg_down, with_cp=with_cp, conv_cfg=conv_cfg, norm_cfg=norm_cfg, dcn=dcn, plugins=stage_plugins, init_cfg=block_init_cfg)
            self.inplanes = planes * self.block.expansion
            layer_name = f'layer{i + 1}'
            self.add_module(layer_name, res_layer)
            self.res_layers.append(layer_name)
        self._freeze_stages()
        self.feat_dim = self.block.expansion * base_channels * 2 ** (len(self.stage_blocks) - 1)

    def make_stage_plugins(self, plugins, stage_idx):
        """Make plugins for ResNet ``stage_idx`` th stage.

        Currently we support to insert ``context_block``,
        ``empirical_attention_block``, ``nonlocal_block`` into the backbone
        like ResNet/ResNeXt. They could be inserted after conv1/conv2/conv3 of
        Bottleneck.

        An example of plugins format could be:

        Examples:
            >>> plugins=[
            ...     dict(cfg=dict(type='xxx', arg1='xxx'),
            ...          stages=(False, True, True, True),
            ...          position='after_conv2'),
            ...     dict(cfg=dict(type='yyy'),
            ...          stages=(True, True, True, True),
            ...          position='after_conv3'),
            ...     dict(cfg=dict(type='zzz', postfix='1'),
            ...          stages=(True, True, True, True),
            ...          position='after_conv3'),
            ...     dict(cfg=dict(type='zzz', postfix='2'),
            ...          stages=(True, True, True, True),
            ...          position='after_conv3')
            ... ]
            >>> self = ResNet(depth=18)
            >>> stage_plugins = self.make_stage_plugins(plugins, 0)
            >>> assert len(stage_plugins) == 3

        Suppose ``stage_idx=0``, the structure of blocks in the stage would be:

        .. code-block:: none

            conv1-> conv2->conv3->yyy->zzz1->zzz2

        Suppose 'stage_idx=1', the structure of blocks in the stage would be:

        .. code-block:: none

            conv1-> conv2->xxx->conv3->yyy->zzz1->zzz2

        If stages is missing, the plugin would be applied to all stages.

        Args:
            plugins (list[dict]): List of plugins cfg to build. The postfix is
                required if multiple same type plugins are inserted.
            stage_idx (int): Index of stage to build

        Returns:
            list[dict]: Plugins for current stage
        """
        stage_plugins = []
        for plugin in plugins:
            plugin = plugin.copy()
            stages = plugin.pop('stages', None)
            assert stages is None or len(stages) == self.num_stages
            if stages is None or stages[stage_idx]:
                stage_plugins.append(plugin)
        return stage_plugins

    def make_res_layer(self, **kwargs):
        """Pack all blocks in a stage into a ``ResLayer``."""
        return ResLayer(**kwargs)

    @property
    def norm1(self):
        """nn.Module: the normalization layer named "norm1" """
        return getattr(self, self.norm1_name)

    def _make_stem_layer(self, in_channels, stem_channels):
        if self.deep_stem:
            self.stem = nn.Sequential(build_conv_layer(self.conv_cfg, in_channels, stem_channels // 2, kernel_size=3, stride=2, padding=1, bias=False), build_norm_layer(self.norm_cfg, stem_channels // 2)[1], nn.ReLU(inplace=True), build_conv_layer(self.conv_cfg, stem_channels // 2, stem_channels // 2, kernel_size=3, stride=1, padding=1, bias=False), build_norm_layer(self.norm_cfg, stem_channels // 2)[1], nn.ReLU(inplace=True), build_conv_layer(self.conv_cfg, stem_channels // 2, stem_channels, kernel_size=3, stride=1, padding=1, bias=False), build_norm_layer(self.norm_cfg, stem_channels)[1], nn.ReLU(inplace=True))
        else:
            self.conv1 = build_conv_layer(self.conv_cfg, in_channels, stem_channels, kernel_size=7, stride=2, padding=3, bias=False)
            self.norm1_name, norm1 = build_norm_layer(self.norm_cfg, stem_channels, postfix=1)
            self.add_module(self.norm1_name, norm1)
            self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)

    def _freeze_stages(self):
        if self.frozen_stages >= 0:
            if self.deep_stem:
                self.stem.eval()
                for param in self.stem.parameters():
                    param.requires_grad = False
            else:
                self.norm1.eval()
                for m in [self.conv1, self.norm1]:
                    for param in m.parameters():
                        param.requires_grad = False
        for i in range(1, self.frozen_stages + 1):
            m = getattr(self, f'layer{i}')
            m.eval()
            for param in m.parameters():
                param.requires_grad = False

    def forward(self, x):
        """Forward function."""
        if self.deep_stem:
            x = self.stem(x)
        else:
            x = self.conv1(x)
            x = self.norm1(x)
            x = self.relu(x)
        x = self.maxpool(x)
        outs = []
        for i, layer_name in enumerate(self.res_layers):
            res_layer = getattr(self, layer_name)
            x = res_layer(x)
            if i in self.out_indices:
                outs.append(x)
        return tuple(outs)

    def train(self, mode=True):
        """Convert the model into training mode while keep normalization layer
        freezed."""
        super(ResNet, self).train(mode)
        self._freeze_stages()
        if mode and self.norm_eval:
            for m in self.modules():
                if isinstance(m, _BatchNorm):
                    m.eval()

def forward(self, x):
    """Forward function."""
    if self.deep_stem:
        x = self.stem(x)
    else:
        x = self.conv1(x)
        x = self.norm1(x)
        x = self.relu(x)
    x = self.maxpool(x)
    outs = []
    for i, layer_name in enumerate(self.res_layers):
        res_layer = getattr(self, layer_name)
        x = res_layer(x)
        if i in self.out_indices:
            outs.append(x)
    return tuple(outs)

class Bottle2neck(_Bottleneck):
    expansion = 4

    def __init__(self, inplanes, planes, scales=4, base_width=26, base_channels=64, stage_type='normal', **kwargs):
        """Bottle2neck block for Res2Net.

        If style is "pytorch", the stride-two layer is the 3x3 conv layer, if
        it is "caffe", the stride-two layer is the first 1x1 conv layer.
        """
        super(Bottle2neck, self).__init__(inplanes, planes, **kwargs)
        assert scales > 1, 'Res2Net degenerates to ResNet when scales = 1.'
        width = int(math.floor(self.planes * (base_width / base_channels)))
        self.norm1_name, norm1 = build_norm_layer(self.norm_cfg, width * scales, postfix=1)
        self.norm3_name, norm3 = build_norm_layer(self.norm_cfg, self.planes * self.expansion, postfix=3)
        self.conv1 = build_conv_layer(self.conv_cfg, self.inplanes, width * scales, kernel_size=1, stride=self.conv1_stride, bias=False)
        self.add_module(self.norm1_name, norm1)
        if stage_type == 'stage' and self.conv2_stride != 1:
            self.pool = nn.AvgPool2d(kernel_size=3, stride=self.conv2_stride, padding=1)
        convs = []
        bns = []
        fallback_on_stride = False
        if self.with_dcn:
            fallback_on_stride = self.dcn.pop('fallback_on_stride', False)
        if not self.with_dcn or fallback_on_stride:
            for i in range(scales - 1):
                convs.append(build_conv_layer(self.conv_cfg, width, width, kernel_size=3, stride=self.conv2_stride, padding=self.dilation, dilation=self.dilation, bias=False))
                bns.append(build_norm_layer(self.norm_cfg, width, postfix=i + 1)[1])
            self.convs = nn.ModuleList(convs)
            self.bns = nn.ModuleList(bns)
        else:
            assert self.conv_cfg is None, 'conv_cfg must be None for DCN'
            for i in range(scales - 1):
                convs.append(build_conv_layer(self.dcn, width, width, kernel_size=3, stride=self.conv2_stride, padding=self.dilation, dilation=self.dilation, bias=False))
                bns.append(build_norm_layer(self.norm_cfg, width, postfix=i + 1)[1])
            self.convs = nn.ModuleList(convs)
            self.bns = nn.ModuleList(bns)
        self.conv3 = build_conv_layer(self.conv_cfg, width * scales, self.planes * self.expansion, kernel_size=1, bias=False)
        self.add_module(self.norm3_name, norm3)
        self.stage_type = stage_type
        self.scales = scales
        self.width = width
        delattr(self, 'conv2')
        delattr(self, self.norm2_name)

    def forward(self, x):
        """Forward function."""

        def _inner_forward(x):
            identity = x
            out = self.conv1(x)
            out = self.norm1(out)
            out = self.relu(out)
            if self.with_plugins:
                out = self.forward_plugin(out, self.after_conv1_plugin_names)
            spx = torch.split(out, self.width, 1)
            sp = self.convs[0](spx[0].contiguous())
            sp = self.relu(self.bns[0](sp))
            out = sp
            for i in range(1, self.scales - 1):
                if self.stage_type == 'stage':
                    sp = spx[i]
                else:
                    sp = sp + spx[i]
                sp = self.convs[i](sp.contiguous())
                sp = self.relu(self.bns[i](sp))
                out = torch.cat((out, sp), 1)
            if self.stage_type == 'normal' or self.conv2_stride == 1:
                out = torch.cat((out, spx[self.scales - 1]), 1)
            elif self.stage_type == 'stage':
                out = torch.cat((out, self.pool(spx[self.scales - 1])), 1)
            if self.with_plugins:
                out = self.forward_plugin(out, self.after_conv2_plugin_names)
            out = self.conv3(out)
            out = self.norm3(out)
            if self.with_plugins:
                out = self.forward_plugin(out, self.after_conv3_plugin_names)
            if self.downsample is not None:
                identity = self.downsample(x)
            out += identity
            return out
        if self.with_cp and x.requires_grad:
            out = cp.checkpoint(_inner_forward, x)
        else:
            out = _inner_forward(x)
        out = self.relu(out)
        return out

def _inner_forward(x):
    identity = x
    out = self.conv1(x)
    out = self.norm1(out)
    out = self.relu(out)
    if self.with_plugins:
        out = self.forward_plugin(out, self.after_conv1_plugin_names)
    spx = torch.split(out, self.width, 1)
    sp = self.convs[0](spx[0].contiguous())
    sp = self.relu(self.bns[0](sp))
    out = sp
    for i in range(1, self.scales - 1):
        if self.stage_type == 'stage':
            sp = spx[i]
        else:
            sp = sp + spx[i]
        sp = self.convs[i](sp.contiguous())
        sp = self.relu(self.bns[i](sp))
        out = torch.cat((out, sp), 1)
    if self.stage_type == 'normal' or self.conv2_stride == 1:
        out = torch.cat((out, spx[self.scales - 1]), 1)
    elif self.stage_type == 'stage':
        out = torch.cat((out, self.pool(spx[self.scales - 1])), 1)
    if self.with_plugins:
        out = self.forward_plugin(out, self.after_conv2_plugin_names)
    out = self.conv3(out)
    out = self.norm3(out)
    if self.with_plugins:
        out = self.forward_plugin(out, self.after_conv3_plugin_names)
    if self.downsample is not None:
        identity = self.downsample(x)
    out += identity
    return out

def forward(self, x):
    """Forward function."""

    def _inner_forward(x):
        identity = x
        out = self.conv1(x)
        out = self.norm1(out)
        out = self.relu(out)
        if self.with_plugins:
            out = self.forward_plugin(out, self.after_conv1_plugin_names)
        spx = torch.split(out, self.width, 1)
        sp = self.convs[0](spx[0].contiguous())
        sp = self.relu(self.bns[0](sp))
        out = sp
        for i in range(1, self.scales - 1):
            if self.stage_type == 'stage':
                sp = spx[i]
            else:
                sp = sp + spx[i]
            sp = self.convs[i](sp.contiguous())
            sp = self.relu(self.bns[i](sp))
            out = torch.cat((out, sp), 1)
        if self.stage_type == 'normal' or self.conv2_stride == 1:
            out = torch.cat((out, spx[self.scales - 1]), 1)
        elif self.stage_type == 'stage':
            out = torch.cat((out, self.pool(spx[self.scales - 1])), 1)
        if self.with_plugins:
            out = self.forward_plugin(out, self.after_conv2_plugin_names)
        out = self.conv3(out)
        out = self.norm3(out)
        if self.with_plugins:
            out = self.forward_plugin(out, self.after_conv3_plugin_names)
        if self.downsample is not None:
            identity = self.downsample(x)
        out += identity
        return out
    if self.with_cp and x.requires_grad:
        out = cp.checkpoint(_inner_forward, x)
    else:
        out = _inner_forward(x)
    out = self.relu(out)
    return out

class Focus(nn.Module):
    """Focus width and height information into channel space.

    Args:
        in_channels (int): The input channels of this Module.
        out_channels (int): The output channels of this Module.
        kernel_size (int): The kernel size of the convolution. Default: 1
        stride (int): The stride of the convolution. Default: 1
        conv_cfg (dict): Config dict for convolution layer. Default: None,
            which means using conv2d.
        norm_cfg (dict): Config dict for normalization layer.
            Default: dict(type='BN', momentum=0.03, eps=0.001).
        act_cfg (dict): Config dict for activation layer.
            Default: dict(type='Swish').
    """

    def __init__(self, in_channels, out_channels, kernel_size=1, stride=1, conv_cfg=None, norm_cfg=dict(type='BN', momentum=0.03, eps=0.001), act_cfg=dict(type='Swish')):
        super().__init__()
        self.conv = ConvModule(in_channels * 4, out_channels, kernel_size, stride, padding=(kernel_size - 1) // 2, conv_cfg=conv_cfg, norm_cfg=norm_cfg, act_cfg=act_cfg)

    def forward(self, x):
        patch_top_left = x[..., ::2, ::2]
        patch_top_right = x[..., ::2, 1::2]
        patch_bot_left = x[..., 1::2, ::2]
        patch_bot_right = x[..., 1::2, 1::2]
        x = torch.cat((patch_top_left, patch_bot_left, patch_top_right, patch_bot_right), dim=1)
        return self.conv(x)

def forward(self, x):
    patch_top_left = x[..., ::2, ::2]
    patch_top_right = x[..., ::2, 1::2]
    patch_bot_left = x[..., 1::2, ::2]
    patch_bot_right = x[..., 1::2, 1::2]
    x = torch.cat((patch_top_left, patch_bot_left, patch_top_right, patch_bot_right), dim=1)
    return self.conv(x)

class SPPBottleneck(BaseModule):
    """Spatial pyramid pooling layer used in YOLOv3-SPP.

    Args:
        in_channels (int): The input channels of this Module.
        out_channels (int): The output channels of this Module.
        kernel_sizes (tuple[int]): Sequential of kernel sizes of pooling
            layers. Default: (5, 9, 13).
        conv_cfg (dict): Config dict for convolution layer. Default: None,
            which means using conv2d.
        norm_cfg (dict): Config dict for normalization layer.
            Default: dict(type='BN').
        act_cfg (dict): Config dict for activation layer.
            Default: dict(type='Swish').
        init_cfg (dict or list[dict], optional): Initialization config dict.
            Default: None.
    """

    def __init__(self, in_channels, out_channels, kernel_sizes=(5, 9, 13), conv_cfg=None, norm_cfg=dict(type='BN', momentum=0.03, eps=0.001), act_cfg=dict(type='Swish'), init_cfg=None):
        super().__init__(init_cfg)
        mid_channels = in_channels // 2
        self.conv1 = ConvModule(in_channels, mid_channels, 1, stride=1, conv_cfg=conv_cfg, norm_cfg=norm_cfg, act_cfg=act_cfg)
        self.poolings = nn.ModuleList([nn.MaxPool2d(kernel_size=ks, stride=1, padding=ks // 2) for ks in kernel_sizes])
        conv2_channels = mid_channels * (len(kernel_sizes) + 1)
        self.conv2 = ConvModule(conv2_channels, out_channels, 1, conv_cfg=conv_cfg, norm_cfg=norm_cfg, act_cfg=act_cfg)

    def forward(self, x):
        x = self.conv1(x)
        x = torch.cat([x] + [pooling(x) for pooling in self.poolings], dim=1)
        x = self.conv2(x)
        return x

def forward(self, x):
    x = self.conv1(x)
    x = torch.cat([x] + [pooling(x) for pooling in self.poolings], dim=1)
    x = self.conv2(x)
    return x

class SplitAttentionConv2d(BaseModule):
    """Split-Attention Conv2d in ResNeSt.

    Args:
        in_channels (int): Number of channels in the input feature map.
        channels (int): Number of intermediate channels.
        kernel_size (int | tuple[int]): Size of the convolution kernel.
        stride (int | tuple[int]): Stride of the convolution.
        padding (int | tuple[int]): Zero-padding added to both sides of
        dilation (int | tuple[int]): Spacing between kernel elements.
        groups (int): Number of blocked connections from input channels to
            output channels.
        groups (int): Same as nn.Conv2d.
        radix (int): Radix of SpltAtConv2d. Default: 2
        reduction_factor (int): Reduction factor of inter_channels. Default: 4.
        conv_cfg (dict): Config dict for convolution layer. Default: None,
            which means using conv2d.
        norm_cfg (dict): Config dict for normalization layer. Default: None.
        dcn (dict): Config dict for DCN. Default: None.
        init_cfg (dict or list[dict], optional): Initialization config dict.
            Default: None
    """

    def __init__(self, in_channels, channels, kernel_size, stride=1, padding=0, dilation=1, groups=1, radix=2, reduction_factor=4, conv_cfg=None, norm_cfg=dict(type='BN'), dcn=None, init_cfg=None):
        super(SplitAttentionConv2d, self).__init__(init_cfg)
        inter_channels = max(in_channels * radix // reduction_factor, 32)
        self.radix = radix
        self.groups = groups
        self.channels = channels
        self.with_dcn = dcn is not None
        self.dcn = dcn
        fallback_on_stride = False
        if self.with_dcn:
            fallback_on_stride = self.dcn.pop('fallback_on_stride', False)
        if self.with_dcn and (not fallback_on_stride):
            assert conv_cfg is None, 'conv_cfg must be None for DCN'
            conv_cfg = dcn
        self.conv = build_conv_layer(conv_cfg, in_channels, channels * radix, kernel_size, stride=stride, padding=padding, dilation=dilation, groups=groups * radix, bias=False)
        self.norm0_name, norm0 = build_norm_layer(norm_cfg, channels * radix, postfix=0)
        self.add_module(self.norm0_name, norm0)
        self.relu = nn.ReLU(inplace=True)
        self.fc1 = build_conv_layer(None, channels, inter_channels, 1, groups=self.groups)
        self.norm1_name, norm1 = build_norm_layer(norm_cfg, inter_channels, postfix=1)
        self.add_module(self.norm1_name, norm1)
        self.fc2 = build_conv_layer(None, inter_channels, channels * radix, 1, groups=self.groups)
        self.rsoftmax = RSoftmax(radix, groups)

    @property
    def norm0(self):
        """nn.Module: the normalization layer named "norm0" """
        return getattr(self, self.norm0_name)

    @property
    def norm1(self):
        """nn.Module: the normalization layer named "norm1" """
        return getattr(self, self.norm1_name)

    def forward(self, x):
        x = self.conv(x)
        x = self.norm0(x)
        x = self.relu(x)
        batch, rchannel = x.shape[:2]
        batch = x.size(0)
        if self.radix > 1:
            splits = x.view(batch, self.radix, -1, *x.shape[2:])
            gap = splits.sum(dim=1)
        else:
            gap = x
        gap = F.adaptive_avg_pool2d(gap, 1)
        gap = self.fc1(gap)
        gap = self.norm1(gap)
        gap = self.relu(gap)
        atten = self.fc2(gap)
        atten = self.rsoftmax(atten).view(batch, -1, 1, 1)
        if self.radix > 1:
            attens = atten.view(batch, self.radix, -1, *atten.shape[2:])
            out = torch.sum(attens * splits, dim=1)
        else:
            out = atten * x
        return out.contiguous()

def forward(self, x):
    x = self.conv(x)
    x = self.norm0(x)
    x = self.relu(x)
    batch, rchannel = x.shape[:2]
    batch = x.size(0)
    if self.radix > 1:
        splits = x.view(batch, self.radix, -1, *x.shape[2:])
        gap = splits.sum(dim=1)
    else:
        gap = x
    gap = F.adaptive_avg_pool2d(gap, 1)
    gap = self.fc1(gap)
    gap = self.norm1(gap)
    gap = self.relu(gap)
    atten = self.fc2(gap)
    atten = self.rsoftmax(atten).view(batch, -1, 1, 1)
    if self.radix > 1:
        attens = atten.view(batch, self.radix, -1, *atten.shape[2:])
        out = torch.sum(attens * splits, dim=1)
    else:
        out = atten * x
    return out.contiguous()

class Bottleneck(_Bottleneck):
    """Bottleneck block for ResNeSt.

    Args:
        inplane (int): Input planes of this block.
        planes (int): Middle planes of this block.
        groups (int): Groups of conv2.
        base_width (int): Base of width in terms of base channels. Default: 4.
        base_channels (int): Base of channels for calculating width.
            Default: 64.
        radix (int): Radix of SpltAtConv2d. Default: 2
        reduction_factor (int): Reduction factor of inter_channels in
            SplitAttentionConv2d. Default: 4.
        avg_down_stride (bool): Whether to use average pool for stride in
            Bottleneck. Default: True.
        kwargs (dict): Key word arguments for base class.
    """
    expansion = 4

    def __init__(self, inplanes, planes, groups=1, base_width=4, base_channels=64, radix=2, reduction_factor=4, avg_down_stride=True, **kwargs):
        """Bottleneck block for ResNeSt."""
        super(Bottleneck, self).__init__(inplanes, planes, **kwargs)
        if groups == 1:
            width = self.planes
        else:
            width = math.floor(self.planes * (base_width / base_channels)) * groups
        self.avg_down_stride = avg_down_stride and self.conv2_stride > 1
        self.norm1_name, norm1 = build_norm_layer(self.norm_cfg, width, postfix=1)
        self.norm3_name, norm3 = build_norm_layer(self.norm_cfg, self.planes * self.expansion, postfix=3)
        self.conv1 = build_conv_layer(self.conv_cfg, self.inplanes, width, kernel_size=1, stride=self.conv1_stride, bias=False)
        self.add_module(self.norm1_name, norm1)
        self.with_modulated_dcn = False
        self.conv2 = SplitAttentionConv2d(width, width, kernel_size=3, stride=1 if self.avg_down_stride else self.conv2_stride, padding=self.dilation, dilation=self.dilation, groups=groups, radix=radix, reduction_factor=reduction_factor, conv_cfg=self.conv_cfg, norm_cfg=self.norm_cfg, dcn=self.dcn)
        delattr(self, self.norm2_name)
        if self.avg_down_stride:
            self.avd_layer = nn.AvgPool2d(3, self.conv2_stride, padding=1)
        self.conv3 = build_conv_layer(self.conv_cfg, width, self.planes * self.expansion, kernel_size=1, bias=False)
        self.add_module(self.norm3_name, norm3)

    def forward(self, x):

        def _inner_forward(x):
            identity = x
            out = self.conv1(x)
            out = self.norm1(out)
            out = self.relu(out)
            if self.with_plugins:
                out = self.forward_plugin(out, self.after_conv1_plugin_names)
            out = self.conv2(out)
            if self.avg_down_stride:
                out = self.avd_layer(out)
            if self.with_plugins:
                out = self.forward_plugin(out, self.after_conv2_plugin_names)
            out = self.conv3(out)
            out = self.norm3(out)
            if self.with_plugins:
                out = self.forward_plugin(out, self.after_conv3_plugin_names)
            if self.downsample is not None:
                identity = self.downsample(x)
            out += identity
            return out
        if self.with_cp and x.requires_grad:
            out = cp.checkpoint(_inner_forward, x)
        else:
            out = _inner_forward(x)
        out = self.relu(out)
        return out

def _inner_forward(x):
    identity = x
    out = self.conv1(x)
    out = self.norm1(out)
    out = self.relu(out)
    if self.with_plugins:
        out = self.forward_plugin(out, self.after_conv1_plugin_names)
    out = self.conv2(out)
    if self.avg_down_stride:
        out = self.avd_layer(out)
    if self.with_plugins:
        out = self.forward_plugin(out, self.after_conv2_plugin_names)
    out = self.conv3(out)
    out = self.norm3(out)
    if self.with_plugins:
        out = self.forward_plugin(out, self.after_conv3_plugin_names)
    if self.downsample is not None:
        identity = self.downsample(x)
    out += identity
    return out

def forward(self, x):

    def _inner_forward(x):
        identity = x
        out = self.conv1(x)
        out = self.norm1(out)
        out = self.relu(out)
        if self.with_plugins:
            out = self.forward_plugin(out, self.after_conv1_plugin_names)
        out = self.conv2(out)
        if self.avg_down_stride:
            out = self.avd_layer(out)
        if self.with_plugins:
            out = self.forward_plugin(out, self.after_conv2_plugin_names)
        out = self.conv3(out)
        out = self.norm3(out)
        if self.with_plugins:
            out = self.forward_plugin(out, self.after_conv3_plugin_names)
        if self.downsample is not None:
            identity = self.downsample(x)
        out += identity
        return out
    if self.with_cp and x.requires_grad:
        out = cp.checkpoint(_inner_forward, x)
    else:
        out = _inner_forward(x)
    out = self.relu(out)
    return out

@BACKBONES.register_module()
class HRNet(BaseModule):
    """HRNet backbone.

    `High-Resolution Representations for Labeling Pixels and Regions
    arXiv: <https://arxiv.org/abs/1904.04514>`_.

    Args:
        extra (dict): Detailed configuration for each stage of HRNet.
            There must be 4 stages, the configuration for each stage must have
            5 keys:

                - num_modules(int): The number of HRModule in this stage.
                - num_branches(int): The number of branches in the HRModule.
                - block(str): The type of convolution block.
                - num_blocks(tuple): The number of blocks in each branch.
                    The length must be equal to num_branches.
                - num_channels(tuple): The number of channels in each branch.
                    The length must be equal to num_branches.
        in_channels (int): Number of input image channels. Default: 3.
        conv_cfg (dict): Dictionary to construct and config conv layer.
        norm_cfg (dict): Dictionary to construct and config norm layer.
        norm_eval (bool): Whether to set norm layers to eval mode, namely,
            freeze running stats (mean and var). Note: Effect on Batch Norm
            and its variants only. Default: True.
        with_cp (bool): Use checkpoint or not. Using checkpoint will save some
            memory while slowing down the training speed. Default: False.
        zero_init_residual (bool): Whether to use zero init for last norm layer
            in resblocks to let them behave as identity. Default: False.
        multiscale_output (bool): Whether to output multi-level features
            produced by multiple branches. If False, only the first level
            feature will be output. Default: True.
        pretrained (str, optional): Model pretrained path. Default: None.
        init_cfg (dict or list[dict], optional): Initialization config dict.
            Default: None.

    Example:
        >>> from mmdet.models import HRNet
        >>> import torch
        >>> extra = dict(
        >>>     stage1=dict(
        >>>         num_modules=1,
        >>>         num_branches=1,
        >>>         block='BOTTLENECK',
        >>>         num_blocks=(4, ),
        >>>         num_channels=(64, )),
        >>>     stage2=dict(
        >>>         num_modules=1,
        >>>         num_branches=2,
        >>>         block='BASIC',
        >>>         num_blocks=(4, 4),
        >>>         num_channels=(32, 64)),
        >>>     stage3=dict(
        >>>         num_modules=4,
        >>>         num_branches=3,
        >>>         block='BASIC',
        >>>         num_blocks=(4, 4, 4),
        >>>         num_channels=(32, 64, 128)),
        >>>     stage4=dict(
        >>>         num_modules=3,
        >>>         num_branches=4,
        >>>         block='BASIC',
        >>>         num_blocks=(4, 4, 4, 4),
        >>>         num_channels=(32, 64, 128, 256)))
        >>> self = HRNet(extra, in_channels=1)
        >>> self.eval()
        >>> inputs = torch.rand(1, 1, 32, 32)
        >>> level_outputs = self.forward(inputs)
        >>> for level_out in level_outputs:
        ...     print(tuple(level_out.shape))
        (1, 32, 8, 8)
        (1, 64, 4, 4)
        (1, 128, 2, 2)
        (1, 256, 1, 1)
    """
    blocks_dict = {'BASIC': BasicBlock, 'BOTTLENECK': Bottleneck}

    def __init__(self, extra, in_channels=3, conv_cfg=None, norm_cfg=dict(type='BN'), norm_eval=True, with_cp=False, zero_init_residual=False, multiscale_output=True, pretrained=None, init_cfg=None):
        super(HRNet, self).__init__(init_cfg)
        self.pretrained = pretrained
        assert not (init_cfg and pretrained), 'init_cfg and pretrained cannot be specified at the same time'
        if isinstance(pretrained, str):
            warnings.warn('DeprecationWarning: pretrained is deprecated, please use "init_cfg" instead')
            self.init_cfg = dict(type='Pretrained', checkpoint=pretrained)
        elif pretrained is None:
            if init_cfg is None:
                self.init_cfg = [dict(type='Kaiming', layer='Conv2d'), dict(type='Constant', val=1, layer=['_BatchNorm', 'GroupNorm'])]
        else:
            raise TypeError('pretrained must be a str or None')
        assert 'stage1' in extra and 'stage2' in extra and ('stage3' in extra) and ('stage4' in extra)
        for i in range(4):
            cfg = extra[f'stage{i + 1}']
            assert len(cfg['num_blocks']) == cfg['num_branches'] and len(cfg['num_channels']) == cfg['num_branches']
        self.extra = extra
        self.conv_cfg = conv_cfg
        self.norm_cfg = norm_cfg
        self.norm_eval = norm_eval
        self.with_cp = with_cp
        self.zero_init_residual = zero_init_residual
        self.norm1_name, norm1 = build_norm_layer(self.norm_cfg, 64, postfix=1)
        self.norm2_name, norm2 = build_norm_layer(self.norm_cfg, 64, postfix=2)
        self.conv1 = build_conv_layer(self.conv_cfg, in_channels, 64, kernel_size=3, stride=2, padding=1, bias=False)
        self.add_module(self.norm1_name, norm1)
        self.conv2 = build_conv_layer(self.conv_cfg, 64, 64, kernel_size=3, stride=2, padding=1, bias=False)
        self.add_module(self.norm2_name, norm2)
        self.relu = nn.ReLU(inplace=True)
        self.stage1_cfg = self.extra['stage1']
        num_channels = self.stage1_cfg['num_channels'][0]
        block_type = self.stage1_cfg['block']
        num_blocks = self.stage1_cfg['num_blocks'][0]
        block = self.blocks_dict[block_type]
        stage1_out_channels = num_channels * block.expansion
        self.layer1 = self._make_layer(block, 64, num_channels, num_blocks)
        self.stage2_cfg = self.extra['stage2']
        num_channels = self.stage2_cfg['num_channels']
        block_type = self.stage2_cfg['block']
        block = self.blocks_dict[block_type]
        num_channels = [channel * block.expansion for channel in num_channels]
        self.transition1 = self._make_transition_layer([stage1_out_channels], num_channels)
        self.stage2, pre_stage_channels = self._make_stage(self.stage2_cfg, num_channels)
        self.stage3_cfg = self.extra['stage3']
        num_channels = self.stage3_cfg['num_channels']
        block_type = self.stage3_cfg['block']
        block = self.blocks_dict[block_type]
        num_channels = [channel * block.expansion for channel in num_channels]
        self.transition2 = self._make_transition_layer(pre_stage_channels, num_channels)
        self.stage3, pre_stage_channels = self._make_stage(self.stage3_cfg, num_channels)
        self.stage4_cfg = self.extra['stage4']
        num_channels = self.stage4_cfg['num_channels']
        block_type = self.stage4_cfg['block']
        block = self.blocks_dict[block_type]
        num_channels = [channel * block.expansion for channel in num_channels]
        self.transition3 = self._make_transition_layer(pre_stage_channels, num_channels)
        self.stage4, pre_stage_channels = self._make_stage(self.stage4_cfg, num_channels, multiscale_output=multiscale_output)

    @property
    def norm1(self):
        """nn.Module: the normalization layer named "norm1" """
        return getattr(self, self.norm1_name)

    @property
    def norm2(self):
        """nn.Module: the normalization layer named "norm2" """
        return getattr(self, self.norm2_name)

    def _make_transition_layer(self, num_channels_pre_layer, num_channels_cur_layer):
        num_branches_cur = len(num_channels_cur_layer)
        num_branches_pre = len(num_channels_pre_layer)
        transition_layers = []
        for i in range(num_branches_cur):
            if i < num_branches_pre:
                if num_channels_cur_layer[i] != num_channels_pre_layer[i]:
                    transition_layers.append(nn.Sequential(build_conv_layer(self.conv_cfg, num_channels_pre_layer[i], num_channels_cur_layer[i], kernel_size=3, stride=1, padding=1, bias=False), build_norm_layer(self.norm_cfg, num_channels_cur_layer[i])[1], nn.ReLU(inplace=True)))
                else:
                    transition_layers.append(None)
            else:
                conv_downsamples = []
                for j in range(i + 1 - num_branches_pre):
                    in_channels = num_channels_pre_layer[-1]
                    out_channels = num_channels_cur_layer[i] if j == i - num_branches_pre else in_channels
                    conv_downsamples.append(nn.Sequential(build_conv_layer(self.conv_cfg, in_channels, out_channels, kernel_size=3, stride=2, padding=1, bias=False), build_norm_layer(self.norm_cfg, out_channels)[1], nn.ReLU(inplace=True)))
                transition_layers.append(nn.Sequential(*conv_downsamples))
        return nn.ModuleList(transition_layers)

    def _make_layer(self, block, inplanes, planes, blocks, stride=1):
        downsample = None
        if stride != 1 or inplanes != planes * block.expansion:
            downsample = nn.Sequential(build_conv_layer(self.conv_cfg, inplanes, planes * block.expansion, kernel_size=1, stride=stride, bias=False), build_norm_layer(self.norm_cfg, planes * block.expansion)[1])
        layers = []
        block_init_cfg = None
        if self.pretrained is None and (not hasattr(self, 'init_cfg')) and self.zero_init_residual:
            if block is BasicBlock:
                block_init_cfg = dict(type='Constant', val=0, override=dict(name='norm2'))
            elif block is Bottleneck:
                block_init_cfg = dict(type='Constant', val=0, override=dict(name='norm3'))
        layers.append(block(inplanes, planes, stride, downsample=downsample, with_cp=self.with_cp, norm_cfg=self.norm_cfg, conv_cfg=self.conv_cfg, init_cfg=block_init_cfg))
        inplanes = planes * block.expansion
        for i in range(1, blocks):
            layers.append(block(inplanes, planes, with_cp=self.with_cp, norm_cfg=self.norm_cfg, conv_cfg=self.conv_cfg, init_cfg=block_init_cfg))
        return Sequential(*layers)

    def _make_stage(self, layer_config, in_channels, multiscale_output=True):
        num_modules = layer_config['num_modules']
        num_branches = layer_config['num_branches']
        num_blocks = layer_config['num_blocks']
        num_channels = layer_config['num_channels']
        block = self.blocks_dict[layer_config['block']]
        hr_modules = []
        block_init_cfg = None
        if self.pretrained is None and (not hasattr(self, 'init_cfg')) and self.zero_init_residual:
            if block is BasicBlock:
                block_init_cfg = dict(type='Constant', val=0, override=dict(name='norm2'))
            elif block is Bottleneck:
                block_init_cfg = dict(type='Constant', val=0, override=dict(name='norm3'))
        for i in range(num_modules):
            if not multiscale_output and i == num_modules - 1:
                reset_multiscale_output = False
            else:
                reset_multiscale_output = True
            hr_modules.append(HRModule(num_branches, block, num_blocks, in_channels, num_channels, reset_multiscale_output, with_cp=self.with_cp, norm_cfg=self.norm_cfg, conv_cfg=self.conv_cfg, block_init_cfg=block_init_cfg))
        return (Sequential(*hr_modules), in_channels)

    def forward(self, x):
        """Forward function."""
        x = self.conv1(x)
        x = self.norm1(x)
        x = self.relu(x)
        x = self.conv2(x)
        x = self.norm2(x)
        x = self.relu(x)
        x = self.layer1(x)
        x_list = []
        for i in range(self.stage2_cfg['num_branches']):
            if self.transition1[i] is not None:
                x_list.append(self.transition1[i](x))
            else:
                x_list.append(x)
        y_list = self.stage2(x_list)
        x_list = []
        for i in range(self.stage3_cfg['num_branches']):
            if self.transition2[i] is not None:
                x_list.append(self.transition2[i](y_list[-1]))
            else:
                x_list.append(y_list[i])
        y_list = self.stage3(x_list)
        x_list = []
        for i in range(self.stage4_cfg['num_branches']):
            if self.transition3[i] is not None:
                x_list.append(self.transition3[i](y_list[-1]))
            else:
                x_list.append(y_list[i])
        y_list = self.stage4(x_list)
        return y_list

    def train(self, mode=True):
        """Convert the model into training mode will keeping the normalization
        layer freezed."""
        super(HRNet, self).train(mode)
        if mode and self.norm_eval:
            for m in self.modules():
                if isinstance(m, _BatchNorm):
                    m.eval()

def forward(self, x):
    """Forward function."""
    x = self.conv1(x)
    x = self.norm1(x)
    x = self.relu(x)
    x = self.conv2(x)
    x = self.norm2(x)
    x = self.relu(x)
    x = self.layer1(x)
    x_list = []
    for i in range(self.stage2_cfg['num_branches']):
        if self.transition1[i] is not None:
            x_list.append(self.transition1[i](x))
        else:
            x_list.append(x)
    y_list = self.stage2(x_list)
    x_list = []
    for i in range(self.stage3_cfg['num_branches']):
        if self.transition2[i] is not None:
            x_list.append(self.transition2[i](y_list[-1]))
        else:
            x_list.append(y_list[i])
    y_list = self.stage3(x_list)
    x_list = []
    for i in range(self.stage4_cfg['num_branches']):
        if self.transition3[i] is not None:
            x_list.append(self.transition3[i](y_list[-1]))
        else:
            x_list.append(y_list[i])
    y_list = self.stage4(x_list)
    return y_list

@BACKBONES.register_module()
class HourglassNet(BaseModule):
    """HourglassNet backbone.

    Stacked Hourglass Networks for Human Pose Estimation.
    More details can be found in the `paper
    <https://arxiv.org/abs/1603.06937>`_ .

    Args:
        downsample_times (int): Downsample times in a HourglassModule.
        num_stacks (int): Number of HourglassModule modules stacked,
            1 for Hourglass-52, 2 for Hourglass-104.
        stage_channels (list[int]): Feature channel of each sub-module in a
            HourglassModule.
        stage_blocks (list[int]): Number of sub-modules stacked in a
            HourglassModule.
        feat_channel (int): Feature channel of conv after a HourglassModule.
        norm_cfg (dict): Dictionary to construct and config norm layer.
        pretrained (str, optional): model pretrained path. Default: None
        init_cfg (dict or list[dict], optional): Initialization config dict.
            Default: None

    Example:
        >>> from mmdet.models import HourglassNet
        >>> import torch
        >>> self = HourglassNet()
        >>> self.eval()
        >>> inputs = torch.rand(1, 3, 511, 511)
        >>> level_outputs = self.forward(inputs)
        >>> for level_output in level_outputs:
        ...     print(tuple(level_output.shape))
        (1, 256, 128, 128)
        (1, 256, 128, 128)
    """

    def __init__(self, downsample_times=5, num_stacks=2, stage_channels=(256, 256, 384, 384, 384, 512), stage_blocks=(2, 2, 2, 2, 2, 4), feat_channel=256, norm_cfg=dict(type='BN', requires_grad=True), pretrained=None, init_cfg=None):
        assert init_cfg is None, 'To prevent abnormal initialization behavior, init_cfg is not allowed to be set'
        super(HourglassNet, self).__init__(init_cfg)
        self.num_stacks = num_stacks
        assert self.num_stacks >= 1
        assert len(stage_channels) == len(stage_blocks)
        assert len(stage_channels) > downsample_times
        cur_channel = stage_channels[0]
        self.stem = nn.Sequential(ConvModule(3, cur_channel // 2, 7, padding=3, stride=2, norm_cfg=norm_cfg), ResLayer(BasicBlock, cur_channel // 2, cur_channel, 1, stride=2, norm_cfg=norm_cfg))
        self.hourglass_modules = nn.ModuleList([HourglassModule(downsample_times, stage_channels, stage_blocks) for _ in range(num_stacks)])
        self.inters = ResLayer(BasicBlock, cur_channel, cur_channel, num_stacks - 1, norm_cfg=norm_cfg)
        self.conv1x1s = nn.ModuleList([ConvModule(cur_channel, cur_channel, 1, norm_cfg=norm_cfg, act_cfg=None) for _ in range(num_stacks - 1)])
        self.out_convs = nn.ModuleList([ConvModule(cur_channel, feat_channel, 3, padding=1, norm_cfg=norm_cfg) for _ in range(num_stacks)])
        self.remap_convs = nn.ModuleList([ConvModule(feat_channel, cur_channel, 1, norm_cfg=norm_cfg, act_cfg=None) for _ in range(num_stacks - 1)])
        self.relu = nn.ReLU(inplace=True)

    def init_weights(self):
        """Init module weights."""
        super(HourglassNet, self).init_weights()
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                m.reset_parameters()

    def forward(self, x):
        """Forward function."""
        inter_feat = self.stem(x)
        out_feats = []
        for ind in range(self.num_stacks):
            single_hourglass = self.hourglass_modules[ind]
            out_conv = self.out_convs[ind]
            hourglass_feat = single_hourglass(inter_feat)
            out_feat = out_conv(hourglass_feat)
            out_feats.append(out_feat)
            if ind < self.num_stacks - 1:
                inter_feat = self.conv1x1s[ind](inter_feat) + self.remap_convs[ind](out_feat)
                inter_feat = self.inters[ind](self.relu(inter_feat))
        return out_feats

def forward(self, x):
    """Forward function."""
    inter_feat = self.stem(x)
    out_feats = []
    for ind in range(self.num_stacks):
        single_hourglass = self.hourglass_modules[ind]
        out_conv = self.out_convs[ind]
        hourglass_feat = single_hourglass(inter_feat)
        out_feat = out_conv(hourglass_feat)
        out_feats.append(out_feat)
        if ind < self.num_stacks - 1:
            inter_feat = self.conv1x1s[ind](inter_feat) + self.remap_convs[ind](out_feat)
            inter_feat = self.inters[ind](self.relu(inter_feat))
    return out_feats

class MixFFN(BaseModule):
    """An implementation of MixFFN of PVT.

    The differences between MixFFN & FFN:
        1. Use 1X1 Conv to replace Linear layer.
        2. Introduce 3X3 Depth-wise Conv to encode positional information.

    Args:
        embed_dims (int): The feature dimension. Same as
            `MultiheadAttention`.
        feedforward_channels (int): The hidden dimension of FFNs.
        act_cfg (dict, optional): The activation config for FFNs.
            Default: dict(type='GELU').
        ffn_drop (float, optional): Probability of an element to be
            zeroed in FFN. Default 0.0.
        dropout_layer (obj:`ConfigDict`): The dropout_layer used
            when adding the shortcut.
            Default: None.
        use_conv (bool): If True, add 3x3 DWConv between two Linear layers.
            Defaults: False.
        init_cfg (obj:`mmcv.ConfigDict`): The Config for initialization.
            Default: None.
    """

    def __init__(self, embed_dims, feedforward_channels, act_cfg=dict(type='GELU'), ffn_drop=0.0, dropout_layer=None, use_conv=False, init_cfg=None):
        super(MixFFN, self).__init__(init_cfg=init_cfg)
        self.embed_dims = embed_dims
        self.feedforward_channels = feedforward_channels
        self.act_cfg = act_cfg
        activate = build_activation_layer(act_cfg)
        in_channels = embed_dims
        fc1 = Conv2d(in_channels=in_channels, out_channels=feedforward_channels, kernel_size=1, stride=1, bias=True)
        if use_conv:
            dw_conv = Conv2d(in_channels=feedforward_channels, out_channels=feedforward_channels, kernel_size=3, stride=1, padding=(3 - 1) // 2, bias=True, groups=feedforward_channels)
        fc2 = Conv2d(in_channels=feedforward_channels, out_channels=in_channels, kernel_size=1, stride=1, bias=True)
        drop = nn.Dropout(ffn_drop)
        layers = [fc1, activate, drop, fc2, drop]
        if use_conv:
            layers.insert(1, dw_conv)
        self.layers = Sequential(*layers)
        self.dropout_layer = build_dropout(dropout_layer) if dropout_layer else torch.nn.Identity()

    def forward(self, x, hw_shape, identity=None):
        out = nlc_to_nchw(x, hw_shape)
        out = self.layers(out)
        out = nchw_to_nlc(out)
        if identity is None:
            identity = x
        return identity + self.dropout_layer(out)

def forward(self, x, hw_shape, identity=None):
    out = nlc_to_nchw(x, hw_shape)
    out = self.layers(out)
    out = nchw_to_nlc(out)
    if identity is None:
        identity = x
    return identity + self.dropout_layer(out)

class SpatialReductionAttention(MultiheadAttention):
    """An implementation of Spatial Reduction Attention of PVT.

    This module is modified from MultiheadAttention which is a module from
    mmcv.cnn.bricks.transformer.

    Args:
        embed_dims (int): The embedding dimension.
        num_heads (int): Parallel attention heads.
        attn_drop (float): A Dropout layer on attn_output_weights.
            Default: 0.0.
        proj_drop (float): A Dropout layer after `nn.MultiheadAttention`.
            Default: 0.0.
        dropout_layer (obj:`ConfigDict`): The dropout_layer used
            when adding the shortcut. Default: None.
        batch_first (bool): Key, Query and Value are shape of
            (batch, n, embed_dim)
            or (n, batch, embed_dim). Default: False.
        qkv_bias (bool): enable bias for qkv if True. Default: True.
        norm_cfg (dict): Config dict for normalization layer.
            Default: dict(type='LN').
        sr_ratio (int): The ratio of spatial reduction of Spatial Reduction
            Attention of PVT. Default: 1.
        init_cfg (obj:`mmcv.ConfigDict`): The Config for initialization.
            Default: None.
    """

    def __init__(self, embed_dims, num_heads, attn_drop=0.0, proj_drop=0.0, dropout_layer=None, batch_first=True, qkv_bias=True, norm_cfg=dict(type='LN'), sr_ratio=1, init_cfg=None):
        super().__init__(embed_dims, num_heads, attn_drop, proj_drop, batch_first=batch_first, dropout_layer=dropout_layer, bias=qkv_bias, init_cfg=init_cfg)
        self.sr_ratio = sr_ratio
        if sr_ratio > 1:
            self.sr = Conv2d(in_channels=embed_dims, out_channels=embed_dims, kernel_size=sr_ratio, stride=sr_ratio)
            self.norm = build_norm_layer(norm_cfg, embed_dims)[1]
        from mmdet import digit_version, mmcv_version
        if mmcv_version < digit_version('1.3.17'):
            warnings.warn('The legacy version of forward function inSpatialReductionAttention is deprecated inmmcv>=1.3.17 and will no longer support in thefuture. Please upgrade your mmcv.')
            self.forward = self.legacy_forward

    def forward(self, x, hw_shape, identity=None):
        x_q = x
        if self.sr_ratio > 1:
            x_kv = nlc_to_nchw(x, hw_shape)
            x_kv = self.sr(x_kv)
            x_kv = nchw_to_nlc(x_kv)
            x_kv = self.norm(x_kv)
        else:
            x_kv = x
        if identity is None:
            identity = x_q
        if self.batch_first:
            x_q = x_q.transpose(0, 1)
            x_kv = x_kv.transpose(0, 1)
        out = self.attn(query=x_q, key=x_kv, value=x_kv)[0]
        if self.batch_first:
            out = out.transpose(0, 1)
        return identity + self.dropout_layer(self.proj_drop(out))

    def legacy_forward(self, x, hw_shape, identity=None):
        """multi head attention forward in mmcv version < 1.3.17."""
        x_q = x
        if self.sr_ratio > 1:
            x_kv = nlc_to_nchw(x, hw_shape)
            x_kv = self.sr(x_kv)
            x_kv = nchw_to_nlc(x_kv)
            x_kv = self.norm(x_kv)
        else:
            x_kv = x
        if identity is None:
            identity = x_q
        out = self.attn(query=x_q, key=x_kv, value=x_kv)[0]
        return identity + self.dropout_layer(self.proj_drop(out))

def forward(self, x, hw_shape, identity=None):
    x_q = x
    if self.sr_ratio > 1:
        x_kv = nlc_to_nchw(x, hw_shape)
        x_kv = self.sr(x_kv)
        x_kv = nchw_to_nlc(x_kv)
        x_kv = self.norm(x_kv)
    else:
        x_kv = x
    if identity is None:
        identity = x_q
    if self.batch_first:
        x_q = x_q.transpose(0, 1)
        x_kv = x_kv.transpose(0, 1)
    out = self.attn(query=x_q, key=x_kv, value=x_kv)[0]
    if self.batch_first:
        out = out.transpose(0, 1)
    return identity + self.dropout_layer(self.proj_drop(out))

def legacy_forward(self, x, hw_shape, identity=None):
    """multi head attention forward in mmcv version < 1.3.17."""
    x_q = x
    if self.sr_ratio > 1:
        x_kv = nlc_to_nchw(x, hw_shape)
        x_kv = self.sr(x_kv)
        x_kv = nchw_to_nlc(x_kv)
        x_kv = self.norm(x_kv)
    else:
        x_kv = x
    if identity is None:
        identity = x_q
    out = self.attn(query=x_q, key=x_kv, value=x_kv)[0]
    return identity + self.dropout_layer(self.proj_drop(out))

class PVTEncoderLayer(BaseModule):
    """Implements one encoder layer in PVT.

    Args:
        embed_dims (int): The feature dimension.
        num_heads (int): Parallel attention heads.
        feedforward_channels (int): The hidden dimension for FFNs.
        drop_rate (float): Probability of an element to be zeroed.
            after the feed forward layer. Default: 0.0.
        attn_drop_rate (float): The drop out rate for attention layer.
            Default: 0.0.
        drop_path_rate (float): stochastic depth rate. Default: 0.0.
        qkv_bias (bool): enable bias for qkv if True.
            Default: True.
        act_cfg (dict): The activation config for FFNs.
            Default: dict(type='GELU').
        norm_cfg (dict): Config dict for normalization layer.
            Default: dict(type='LN').
        sr_ratio (int): The ratio of spatial reduction of Spatial Reduction
            Attention of PVT. Default: 1.
        use_conv_ffn (bool): If True, use Convolutional FFN to replace FFN.
            Default: False.
        init_cfg (dict, optional): Initialization config dict.
            Default: None.
    """

    def __init__(self, embed_dims, num_heads, feedforward_channels, drop_rate=0.0, attn_drop_rate=0.0, drop_path_rate=0.0, qkv_bias=True, act_cfg=dict(type='GELU'), norm_cfg=dict(type='LN'), sr_ratio=1, use_conv_ffn=False, init_cfg=None):
        super(PVTEncoderLayer, self).__init__(init_cfg=init_cfg)
        self.norm1 = build_norm_layer(norm_cfg, embed_dims)[1]
        self.attn = SpatialReductionAttention(embed_dims=embed_dims, num_heads=num_heads, attn_drop=attn_drop_rate, proj_drop=drop_rate, dropout_layer=dict(type='DropPath', drop_prob=drop_path_rate), qkv_bias=qkv_bias, norm_cfg=norm_cfg, sr_ratio=sr_ratio)
        self.norm2 = build_norm_layer(norm_cfg, embed_dims)[1]
        self.ffn = MixFFN(embed_dims=embed_dims, feedforward_channels=feedforward_channels, ffn_drop=drop_rate, dropout_layer=dict(type='DropPath', drop_prob=drop_path_rate), use_conv=use_conv_ffn, act_cfg=act_cfg)

    def forward(self, x, hw_shape):
        x = self.attn(self.norm1(x), hw_shape, identity=x)
        x = self.ffn(self.norm2(x), hw_shape, identity=x)
        return x

def forward(self, x, hw_shape):
    x = self.attn(self.norm1(x), hw_shape, identity=x)
    x = self.ffn(self.norm2(x), hw_shape, identity=x)
    return x

class ResBlock(BaseModule):
    """The basic residual block used in Darknet. Each ResBlock consists of two
    ConvModules and the input is added to the final output. Each ConvModule is
    composed of Conv, BN, and LeakyReLU. In YoloV3 paper, the first convLayer
    has half of the number of the filters as much as the second convLayer. The
    first convLayer has filter size of 1x1 and the second one has the filter
    size of 3x3.

    Args:
        in_channels (int): The input channels. Must be even.
        conv_cfg (dict): Config dict for convolution layer. Default: None.
        norm_cfg (dict): Dictionary to construct and config norm layer.
            Default: dict(type='BN', requires_grad=True)
        act_cfg (dict): Config dict for activation layer.
            Default: dict(type='LeakyReLU', negative_slope=0.1).
        init_cfg (dict or list[dict], optional): Initialization config dict.
            Default: None
    """

    def __init__(self, in_channels, conv_cfg=None, norm_cfg=dict(type='BN', requires_grad=True), act_cfg=dict(type='LeakyReLU', negative_slope=0.1), init_cfg=None):
        super(ResBlock, self).__init__(init_cfg)
        assert in_channels % 2 == 0
        half_in_channels = in_channels // 2
        cfg = dict(conv_cfg=conv_cfg, norm_cfg=norm_cfg, act_cfg=act_cfg)
        self.conv1 = ConvModule(in_channels, half_in_channels, 1, **cfg)
        self.conv2 = ConvModule(half_in_channels, in_channels, 3, padding=1, **cfg)

    def forward(self, x):
        residual = x
        out = self.conv1(x)
        out = self.conv2(out)
        out = out + residual
        return out

def forward(self, x):
    residual = x
    out = self.conv1(x)
    out = self.conv2(out)
    out = out + residual
    return out

@HEADS.register_module()
class CentripetalHead(CornerHead):
    """Head of CentripetalNet: Pursuing High-quality Keypoint Pairs for Object
    Detection.

    CentripetalHead inherits from :class:`CornerHead`. It removes the
    embedding branch and adds guiding shift and centripetal shift branches.
    More details can be found in the `paper
    <https://arxiv.org/abs/2003.09119>`_ .

    Args:
        num_classes (int): Number of categories excluding the background
            category.
        in_channels (int): Number of channels in the input feature map.
        num_feat_levels (int): Levels of feature from the previous module. 2
            for HourglassNet-104 and 1 for HourglassNet-52. HourglassNet-104
            outputs the final feature and intermediate supervision feature and
            HourglassNet-52 only outputs the final feature. Default: 2.
        corner_emb_channels (int): Channel of embedding vector. Default: 1.
        train_cfg (dict | None): Training config. Useless in CornerHead,
            but we keep this variable for SingleStageDetector. Default: None.
        test_cfg (dict | None): Testing config of CornerHead. Default: None.
        loss_heatmap (dict | None): Config of corner heatmap loss. Default:
            GaussianFocalLoss.
        loss_embedding (dict | None): Config of corner embedding loss. Default:
            AssociativeEmbeddingLoss.
        loss_offset (dict | None): Config of corner offset loss. Default:
            SmoothL1Loss.
        loss_guiding_shift (dict): Config of guiding shift loss. Default:
            SmoothL1Loss.
        loss_centripetal_shift (dict): Config of centripetal shift loss.
            Default: SmoothL1Loss.
        init_cfg (dict or list[dict], optional): Initialization config dict.
            Default: None
    """

    def __init__(self, *args, centripetal_shift_channels=2, guiding_shift_channels=2, feat_adaption_conv_kernel=3, loss_guiding_shift=dict(type='SmoothL1Loss', beta=1.0, loss_weight=0.05), loss_centripetal_shift=dict(type='SmoothL1Loss', beta=1.0, loss_weight=1), init_cfg=None, **kwargs):
        assert init_cfg is None, 'To prevent abnormal initialization behavior, init_cfg is not allowed to be set'
        assert centripetal_shift_channels == 2, 'CentripetalHead only support centripetal_shift_channels == 2'
        self.centripetal_shift_channels = centripetal_shift_channels
        assert guiding_shift_channels == 2, 'CentripetalHead only support guiding_shift_channels == 2'
        self.guiding_shift_channels = guiding_shift_channels
        self.feat_adaption_conv_kernel = feat_adaption_conv_kernel
        super(CentripetalHead, self).__init__(*args, init_cfg=init_cfg, **kwargs)
        self.loss_guiding_shift = build_loss(loss_guiding_shift)
        self.loss_centripetal_shift = build_loss(loss_centripetal_shift)

    def _init_centripetal_layers(self):
        """Initialize centripetal layers.

        Including feature adaption deform convs (feat_adaption), deform offset
        prediction convs (dcn_off), guiding shift (guiding_shift) and
        centripetal shift ( centripetal_shift). Each branch has two parts:
        prefix `tl_` for top-left and `br_` for bottom-right.
        """
        self.tl_feat_adaption = nn.ModuleList()
        self.br_feat_adaption = nn.ModuleList()
        self.tl_dcn_offset = nn.ModuleList()
        self.br_dcn_offset = nn.ModuleList()
        self.tl_guiding_shift = nn.ModuleList()
        self.br_guiding_shift = nn.ModuleList()
        self.tl_centripetal_shift = nn.ModuleList()
        self.br_centripetal_shift = nn.ModuleList()
        for _ in range(self.num_feat_levels):
            self.tl_feat_adaption.append(DeformConv2d(self.in_channels, self.in_channels, self.feat_adaption_conv_kernel, 1, 1))
            self.br_feat_adaption.append(DeformConv2d(self.in_channels, self.in_channels, self.feat_adaption_conv_kernel, 1, 1))
            self.tl_guiding_shift.append(self._make_layers(out_channels=self.guiding_shift_channels, in_channels=self.in_channels))
            self.br_guiding_shift.append(self._make_layers(out_channels=self.guiding_shift_channels, in_channels=self.in_channels))
            self.tl_dcn_offset.append(ConvModule(self.guiding_shift_channels, self.feat_adaption_conv_kernel ** 2 * self.guiding_shift_channels, 1, bias=False, act_cfg=None))
            self.br_dcn_offset.append(ConvModule(self.guiding_shift_channels, self.feat_adaption_conv_kernel ** 2 * self.guiding_shift_channels, 1, bias=False, act_cfg=None))
            self.tl_centripetal_shift.append(self._make_layers(out_channels=self.centripetal_shift_channels, in_channels=self.in_channels))
            self.br_centripetal_shift.append(self._make_layers(out_channels=self.centripetal_shift_channels, in_channels=self.in_channels))

    def _init_layers(self):
        """Initialize layers for CentripetalHead.

        Including two parts: CornerHead layers and CentripetalHead layers
        """
        super()._init_layers()
        self._init_centripetal_layers()

    def init_weights(self):
        super(CentripetalHead, self).init_weights()
        for i in range(self.num_feat_levels):
            normal_init(self.tl_feat_adaption[i], std=0.01)
            normal_init(self.br_feat_adaption[i], std=0.01)
            normal_init(self.tl_dcn_offset[i].conv, std=0.1)
            normal_init(self.br_dcn_offset[i].conv, std=0.1)
            _ = [x.conv.reset_parameters() for x in self.tl_guiding_shift[i]]
            _ = [x.conv.reset_parameters() for x in self.br_guiding_shift[i]]
            _ = [x.conv.reset_parameters() for x in self.tl_centripetal_shift[i]]
            _ = [x.conv.reset_parameters() for x in self.br_centripetal_shift[i]]

    def forward_single(self, x, lvl_ind):
        """Forward feature of a single level.

        Args:
            x (Tensor): Feature of a single level.
            lvl_ind (int): Level index of current feature.

        Returns:
            tuple[Tensor]: A tuple of CentripetalHead's output for current
            feature level. Containing the following Tensors:

                - tl_heat (Tensor): Predicted top-left corner heatmap.
                - br_heat (Tensor): Predicted bottom-right corner heatmap.
                - tl_off (Tensor): Predicted top-left offset heatmap.
                - br_off (Tensor): Predicted bottom-right offset heatmap.
                - tl_guiding_shift (Tensor): Predicted top-left guiding shift
                  heatmap.
                - br_guiding_shift (Tensor): Predicted bottom-right guiding
                  shift heatmap.
                - tl_centripetal_shift (Tensor): Predicted top-left centripetal
                  shift heatmap.
                - br_centripetal_shift (Tensor): Predicted bottom-right
                  centripetal shift heatmap.
        """
        tl_heat, br_heat, _, _, tl_off, br_off, tl_pool, br_pool = super().forward_single(x, lvl_ind, return_pool=True)
        tl_guiding_shift = self.tl_guiding_shift[lvl_ind](tl_pool)
        br_guiding_shift = self.br_guiding_shift[lvl_ind](br_pool)
        tl_dcn_offset = self.tl_dcn_offset[lvl_ind](tl_guiding_shift.detach())
        br_dcn_offset = self.br_dcn_offset[lvl_ind](br_guiding_shift.detach())
        tl_feat_adaption = self.tl_feat_adaption[lvl_ind](tl_pool, tl_dcn_offset)
        br_feat_adaption = self.br_feat_adaption[lvl_ind](br_pool, br_dcn_offset)
        tl_centripetal_shift = self.tl_centripetal_shift[lvl_ind](tl_feat_adaption)
        br_centripetal_shift = self.br_centripetal_shift[lvl_ind](br_feat_adaption)
        result_list = [tl_heat, br_heat, tl_off, br_off, tl_guiding_shift, br_guiding_shift, tl_centripetal_shift, br_centripetal_shift]
        return result_list

    @force_fp32()
    def loss(self, tl_heats, br_heats, tl_offs, br_offs, tl_guiding_shifts, br_guiding_shifts, tl_centripetal_shifts, br_centripetal_shifts, gt_bboxes, gt_labels, img_metas, gt_bboxes_ignore=None):
        """Compute losses of the head.

        Args:
            tl_heats (list[Tensor]): Top-left corner heatmaps for each level
                with shape (N, num_classes, H, W).
            br_heats (list[Tensor]): Bottom-right corner heatmaps for each
                level with shape (N, num_classes, H, W).
            tl_offs (list[Tensor]): Top-left corner offsets for each level
                with shape (N, corner_offset_channels, H, W).
            br_offs (list[Tensor]): Bottom-right corner offsets for each level
                with shape (N, corner_offset_channels, H, W).
            tl_guiding_shifts (list[Tensor]): Top-left guiding shifts for each
                level with shape (N, guiding_shift_channels, H, W).
            br_guiding_shifts (list[Tensor]): Bottom-right guiding shifts for
                each level with shape (N, guiding_shift_channels, H, W).
            tl_centripetal_shifts (list[Tensor]): Top-left centripetal shifts
                for each level with shape (N, centripetal_shift_channels, H,
                W).
            br_centripetal_shifts (list[Tensor]): Bottom-right centripetal
                shifts for each level with shape (N,
                centripetal_shift_channels, H, W).
            gt_bboxes (list[Tensor]): Ground truth bboxes for each image with
                shape (num_gts, 4) in [left, top, right, bottom] format.
            gt_labels (list[Tensor]): Class indices corresponding to each box.
            img_metas (list[dict]): Meta information of each image, e.g.,
                image size, scaling factor, etc.
            gt_bboxes_ignore (list[Tensor] | None): Specify which bounding
                boxes can be ignored when computing the loss.

        Returns:
            dict[str, Tensor]: A dictionary of loss components. Containing the
            following losses:

                - det_loss (list[Tensor]): Corner keypoint losses of all
                  feature levels.
                - off_loss (list[Tensor]): Corner offset losses of all feature
                  levels.
                - guiding_loss (list[Tensor]): Guiding shift losses of all
                  feature levels.
                - centripetal_loss (list[Tensor]): Centripetal shift losses of
                  all feature levels.
        """
        targets = self.get_targets(gt_bboxes, gt_labels, tl_heats[-1].shape, img_metas[0]['pad_shape'], with_corner_emb=self.with_corner_emb, with_guiding_shift=True, with_centripetal_shift=True)
        mlvl_targets = [targets for _ in range(self.num_feat_levels)]
        [det_losses, off_losses, guiding_losses, centripetal_losses] = multi_apply(self.loss_single, tl_heats, br_heats, tl_offs, br_offs, tl_guiding_shifts, br_guiding_shifts, tl_centripetal_shifts, br_centripetal_shifts, mlvl_targets)
        loss_dict = dict(det_loss=det_losses, off_loss=off_losses, guiding_loss=guiding_losses, centripetal_loss=centripetal_losses)
        return loss_dict

    def loss_single(self, tl_hmp, br_hmp, tl_off, br_off, tl_guiding_shift, br_guiding_shift, tl_centripetal_shift, br_centripetal_shift, targets):
        """Compute losses for single level.

        Args:
            tl_hmp (Tensor): Top-left corner heatmap for current level with
                shape (N, num_classes, H, W).
            br_hmp (Tensor): Bottom-right corner heatmap for current level with
                shape (N, num_classes, H, W).
            tl_off (Tensor): Top-left corner offset for current level with
                shape (N, corner_offset_channels, H, W).
            br_off (Tensor): Bottom-right corner offset for current level with
                shape (N, corner_offset_channels, H, W).
            tl_guiding_shift (Tensor): Top-left guiding shift for current level
                with shape (N, guiding_shift_channels, H, W).
            br_guiding_shift (Tensor): Bottom-right guiding shift for current
                level with shape (N, guiding_shift_channels, H, W).
            tl_centripetal_shift (Tensor): Top-left centripetal shift for
                current level with shape (N, centripetal_shift_channels, H, W).
            br_centripetal_shift (Tensor): Bottom-right centripetal shift for
                current level with shape (N, centripetal_shift_channels, H, W).
            targets (dict): Corner target generated by `get_targets`.

        Returns:
            tuple[torch.Tensor]: Losses of the head's different branches
            containing the following losses:

                - det_loss (Tensor): Corner keypoint loss.
                - off_loss (Tensor): Corner offset loss.
                - guiding_loss (Tensor): Guiding shift loss.
                - centripetal_loss (Tensor): Centripetal shift loss.
        """
        targets['corner_embedding'] = None
        det_loss, _, _, off_loss = super().loss_single(tl_hmp, br_hmp, None, None, tl_off, br_off, targets)
        gt_tl_guiding_shift = targets['topleft_guiding_shift']
        gt_br_guiding_shift = targets['bottomright_guiding_shift']
        gt_tl_centripetal_shift = targets['topleft_centripetal_shift']
        gt_br_centripetal_shift = targets['bottomright_centripetal_shift']
        gt_tl_heatmap = targets['topleft_heatmap']
        gt_br_heatmap = targets['bottomright_heatmap']
        tl_mask = gt_tl_heatmap.eq(1).sum(1).gt(0).unsqueeze(1).type_as(gt_tl_heatmap)
        br_mask = gt_br_heatmap.eq(1).sum(1).gt(0).unsqueeze(1).type_as(gt_br_heatmap)
        tl_guiding_loss = self.loss_guiding_shift(tl_guiding_shift, gt_tl_guiding_shift, tl_mask, avg_factor=tl_mask.sum())
        br_guiding_loss = self.loss_guiding_shift(br_guiding_shift, gt_br_guiding_shift, br_mask, avg_factor=br_mask.sum())
        guiding_loss = (tl_guiding_loss + br_guiding_loss) / 2.0
        tl_centripetal_loss = self.loss_centripetal_shift(tl_centripetal_shift, gt_tl_centripetal_shift, tl_mask, avg_factor=tl_mask.sum())
        br_centripetal_loss = self.loss_centripetal_shift(br_centripetal_shift, gt_br_centripetal_shift, br_mask, avg_factor=br_mask.sum())
        centripetal_loss = (tl_centripetal_loss + br_centripetal_loss) / 2.0
        return (det_loss, off_loss, guiding_loss, centripetal_loss)

    @force_fp32()
    def get_bboxes(self, tl_heats, br_heats, tl_offs, br_offs, tl_guiding_shifts, br_guiding_shifts, tl_centripetal_shifts, br_centripetal_shifts, img_metas, rescale=False, with_nms=True):
        """Transform network output for a batch into bbox predictions.

        Args:
            tl_heats (list[Tensor]): Top-left corner heatmaps for each level
                with shape (N, num_classes, H, W).
            br_heats (list[Tensor]): Bottom-right corner heatmaps for each
                level with shape (N, num_classes, H, W).
            tl_offs (list[Tensor]): Top-left corner offsets for each level
                with shape (N, corner_offset_channels, H, W).
            br_offs (list[Tensor]): Bottom-right corner offsets for each level
                with shape (N, corner_offset_channels, H, W).
            tl_guiding_shifts (list[Tensor]): Top-left guiding shifts for each
                level with shape (N, guiding_shift_channels, H, W). Useless in
                this function, we keep this arg because it's the raw output
                from CentripetalHead.
            br_guiding_shifts (list[Tensor]): Bottom-right guiding shifts for
                each level with shape (N, guiding_shift_channels, H, W).
                Useless in this function, we keep this arg because it's the
                raw output from CentripetalHead.
            tl_centripetal_shifts (list[Tensor]): Top-left centripetal shifts
                for each level with shape (N, centripetal_shift_channels, H,
                W).
            br_centripetal_shifts (list[Tensor]): Bottom-right centripetal
                shifts for each level with shape (N,
                centripetal_shift_channels, H, W).
            img_metas (list[dict]): Meta information of each image, e.g.,
                image size, scaling factor, etc.
            rescale (bool): If True, return boxes in original image space.
                Default: False.
            with_nms (bool): If True, do nms before return boxes.
                Default: True.
        """
        assert tl_heats[-1].shape[0] == br_heats[-1].shape[0] == len(img_metas)
        result_list = []
        for img_id in range(len(img_metas)):
            result_list.append(self._get_bboxes_single(tl_heats[-1][img_id:img_id + 1, :], br_heats[-1][img_id:img_id + 1, :], tl_offs[-1][img_id:img_id + 1, :], br_offs[-1][img_id:img_id + 1, :], img_metas[img_id], tl_emb=None, br_emb=None, tl_centripetal_shift=tl_centripetal_shifts[-1][img_id:img_id + 1, :], br_centripetal_shift=br_centripetal_shifts[-1][img_id:img_id + 1, :], rescale=rescale, with_nms=with_nms))
        return result_list

def forward_single(self, x, lvl_ind):
    """Forward feature of a single level.

        Args:
            x (Tensor): Feature of a single level.
            lvl_ind (int): Level index of current feature.

        Returns:
            tuple[Tensor]: A tuple of CentripetalHead's output for current
            feature level. Containing the following Tensors:

                - tl_heat (Tensor): Predicted top-left corner heatmap.
                - br_heat (Tensor): Predicted bottom-right corner heatmap.
                - tl_off (Tensor): Predicted top-left offset heatmap.
                - br_off (Tensor): Predicted bottom-right offset heatmap.
                - tl_guiding_shift (Tensor): Predicted top-left guiding shift
                  heatmap.
                - br_guiding_shift (Tensor): Predicted bottom-right guiding
                  shift heatmap.
                - tl_centripetal_shift (Tensor): Predicted top-left centripetal
                  shift heatmap.
                - br_centripetal_shift (Tensor): Predicted bottom-right
                  centripetal shift heatmap.
        """
    tl_heat, br_heat, _, _, tl_off, br_off, tl_pool, br_pool = super().forward_single(x, lvl_ind, return_pool=True)
    tl_guiding_shift = self.tl_guiding_shift[lvl_ind](tl_pool)
    br_guiding_shift = self.br_guiding_shift[lvl_ind](br_pool)
    tl_dcn_offset = self.tl_dcn_offset[lvl_ind](tl_guiding_shift.detach())
    br_dcn_offset = self.br_dcn_offset[lvl_ind](br_guiding_shift.detach())
    tl_feat_adaption = self.tl_feat_adaption[lvl_ind](tl_pool, tl_dcn_offset)
    br_feat_adaption = self.br_feat_adaption[lvl_ind](br_pool, br_dcn_offset)
    tl_centripetal_shift = self.tl_centripetal_shift[lvl_ind](tl_feat_adaption)
    br_centripetal_shift = self.br_centripetal_shift[lvl_ind](br_feat_adaption)
    result_list = [tl_heat, br_heat, tl_off, br_off, tl_guiding_shift, br_guiding_shift, tl_centripetal_shift, br_centripetal_shift]
    return result_list

@HEADS.register_module()
class RPNHead(AnchorHead):
    """RPN head.

    Args:
        in_channels (int): Number of channels in the input feature map.
        init_cfg (dict or list[dict], optional): Initialization config dict.
        num_convs (int): Number of convolution layers in the head. Default 1.
    """

    def __init__(self, in_channels, init_cfg=dict(type='Normal', layer='Conv2d', std=0.01), num_convs=1, **kwargs):
        self.num_convs = num_convs
        super(RPNHead, self).__init__(1, in_channels, init_cfg=init_cfg, **kwargs)

    def _init_layers(self):
        """Initialize layers of the head."""
        if self.num_convs > 1:
            rpn_convs = []
            for i in range(self.num_convs):
                if i == 0:
                    in_channels = self.in_channels
                else:
                    in_channels = self.feat_channels
                rpn_convs.append(ConvModule(in_channels, self.feat_channels, 3, padding=1, inplace=False))
            self.rpn_conv = nn.Sequential(*rpn_convs)
        else:
            self.rpn_conv = nn.Conv2d(self.in_channels, self.feat_channels, 3, padding=1)
        self.rpn_cls = nn.Conv2d(self.feat_channels, self.num_base_priors * self.cls_out_channels, 1)
        self.rpn_reg = nn.Conv2d(self.feat_channels, self.num_base_priors * 4, 1)

    def forward_single(self, x):
        """Forward feature map of a single scale level."""
        x = self.rpn_conv(x)
        x = F.relu(x, inplace=False)
        rpn_cls_score = self.rpn_cls(x)
        rpn_bbox_pred = self.rpn_reg(x)
        return (rpn_cls_score, rpn_bbox_pred)

    def loss(self, cls_scores, bbox_preds, gt_bboxes, img_metas, gt_bboxes_ignore=None):
        """Compute losses of the head.

        Args:
            cls_scores (list[Tensor]): Box scores for each scale level
                Has shape (N, num_anchors * num_classes, H, W)
            bbox_preds (list[Tensor]): Box energies / deltas for each scale
                level with shape (N, num_anchors * 4, H, W)
            gt_bboxes (list[Tensor]): Ground truth bboxes for each image with
                shape (num_gts, 4) in [tl_x, tl_y, br_x, br_y] format.
            img_metas (list[dict]): Meta information of each image, e.g.,
                image size, scaling factor, etc.
            gt_bboxes_ignore (None | list[Tensor]): specify which bounding
                boxes can be ignored when computing the loss.

        Returns:
            dict[str, Tensor]: A dictionary of loss components.
        """
        losses = super(RPNHead, self).loss(cls_scores, bbox_preds, gt_bboxes, None, img_metas, gt_bboxes_ignore=gt_bboxes_ignore)
        return dict(loss_rpn_cls=losses['loss_cls'], loss_rpn_bbox=losses['loss_bbox'])

    def _get_bboxes_single(self, cls_score_list, bbox_pred_list, score_factor_list, mlvl_anchors, img_meta, cfg, rescale=False, with_nms=True, **kwargs):
        """Transform outputs of a single image into bbox predictions.

        Args:
            cls_score_list (list[Tensor]): Box scores from all scale
                levels of a single image, each item has shape
                (num_anchors * num_classes, H, W).
            bbox_pred_list (list[Tensor]): Box energies / deltas from
                all scale levels of a single image, each item has
                shape (num_anchors * 4, H, W).
            score_factor_list (list[Tensor]): Score factor from all scale
                levels of a single image. RPN head does not need this value.
            mlvl_anchors (list[Tensor]): Anchors of all scale level
                each item has shape (num_anchors, 4).
            img_meta (dict): Image meta info.
            cfg (mmcv.Config): Test / postprocessing configuration,
                if None, test_cfg would be used.
            rescale (bool): If True, return boxes in original image space.
                Default: False.
            with_nms (bool): If True, do nms before return boxes.
                Default: True.

        Returns:
            Tensor: Labeled boxes in shape (n, 5), where the first 4 columns
                are bounding box positions (tl_x, tl_y, br_x, br_y) and the
                5-th column is a score between 0 and 1.
        """
        cfg = self.test_cfg if cfg is None else cfg
        cfg = copy.deepcopy(cfg)
        img_shape = img_meta['img_shape']
        level_ids = []
        mlvl_scores = []
        mlvl_bbox_preds = []
        mlvl_valid_anchors = []
        nms_pre = cfg.get('nms_pre', -1)
        for level_idx in range(len(cls_score_list)):
            rpn_cls_score = cls_score_list[level_idx]
            rpn_bbox_pred = bbox_pred_list[level_idx]
            assert rpn_cls_score.size()[-2:] == rpn_bbox_pred.size()[-2:]
            rpn_cls_score = rpn_cls_score.permute(1, 2, 0)
            if self.use_sigmoid_cls:
                rpn_cls_score = rpn_cls_score.reshape(-1)
                scores = rpn_cls_score.sigmoid()
            else:
                rpn_cls_score = rpn_cls_score.reshape(-1, 2)
                scores = rpn_cls_score.softmax(dim=1)[:, 0]
            rpn_bbox_pred = rpn_bbox_pred.permute(1, 2, 0).reshape(-1, 4)
            anchors = mlvl_anchors[level_idx]
            if 0 < nms_pre < scores.shape[0]:
                ranked_scores, rank_inds = scores.sort(descending=True)
                topk_inds = rank_inds[:nms_pre]
                scores = ranked_scores[:nms_pre]
                rpn_bbox_pred = rpn_bbox_pred[topk_inds, :]
                anchors = anchors[topk_inds, :]
            mlvl_scores.append(scores)
            mlvl_bbox_preds.append(rpn_bbox_pred)
            mlvl_valid_anchors.append(anchors)
            level_ids.append(scores.new_full((scores.size(0),), level_idx, dtype=torch.long))
        return self._bbox_post_process(mlvl_scores, mlvl_bbox_preds, mlvl_valid_anchors, level_ids, cfg, img_shape)

    def _bbox_post_process(self, mlvl_scores, mlvl_bboxes, mlvl_valid_anchors, level_ids, cfg, img_shape, **kwargs):
        """bbox post-processing method.

        Do the nms operation for bboxes in same level.

        Args:
            mlvl_scores (list[Tensor]): Box scores from all scale
                levels of a single image, each item has shape
                (num_bboxes, ).
            mlvl_bboxes (list[Tensor]): Decoded bboxes from all scale
                levels of a single image, each item has shape (num_bboxes, 4).
            mlvl_valid_anchors (list[Tensor]): Anchors of all scale level
                each item has shape (num_bboxes, 4).
            level_ids (list[Tensor]): Indexes from all scale levels of a
                single image, each item has shape (num_bboxes, ).
            cfg (mmcv.Config): Test / postprocessing configuration,
                if None, `self.test_cfg` would be used.
            img_shape (tuple(int)): The shape of model's input image.

        Returns:
            Tensor: Labeled boxes in shape (n, 5), where the first 4 columns
                are bounding box positions (tl_x, tl_y, br_x, br_y) and the
                5-th column is a score between 0 and 1.
        """
        scores = torch.cat(mlvl_scores)
        anchors = torch.cat(mlvl_valid_anchors)
        rpn_bbox_pred = torch.cat(mlvl_bboxes)
        proposals = self.bbox_coder.decode(anchors, rpn_bbox_pred, max_shape=img_shape)
        ids = torch.cat(level_ids)
        if cfg.min_bbox_size >= 0:
            w = proposals[:, 2] - proposals[:, 0]
            h = proposals[:, 3] - proposals[:, 1]
            valid_mask = (w > cfg.min_bbox_size) & (h > cfg.min_bbox_size)
            if not valid_mask.all():
                proposals = proposals[valid_mask]
                scores = scores[valid_mask]
                ids = ids[valid_mask]
        if proposals.numel() > 0:
            dets, _ = batched_nms(proposals, scores, ids, cfg.nms)
        else:
            return proposals.new_zeros(0, 5)
        return dets[:cfg.max_per_img]

    def onnx_export(self, x, img_metas):
        """Test without augmentation.

        Args:
            x (tuple[Tensor]): Features from the upstream network, each is
                a 4D-tensor.
            img_metas (list[dict]): Meta info of each image.
        Returns:
            Tensor: dets of shape [N, num_det, 5].
        """
        cls_scores, bbox_preds = self(x)
        assert len(cls_scores) == len(bbox_preds)
        batch_bboxes, batch_scores = super(RPNHead, self).onnx_export(cls_scores, bbox_preds, img_metas=img_metas, with_nms=False)
        from mmdet.core.export import add_dummy_nms_for_onnx
        cfg = copy.deepcopy(self.test_cfg)
        score_threshold = cfg.nms.get('score_thr', 0.0)
        nms_pre = cfg.get('deploy_nms_pre', -1)
        dets, _ = add_dummy_nms_for_onnx(batch_bboxes, batch_scores, cfg.max_per_img, cfg.nms.iou_threshold, score_threshold, nms_pre, cfg.max_per_img)
        return dets

def forward_single(self, x):
    """Forward feature map of a single scale level."""
    x = self.rpn_conv(x)
    x = F.relu(x, inplace=False)
    rpn_cls_score = self.rpn_cls(x)
    rpn_bbox_pred = self.rpn_reg(x)
    return (rpn_cls_score, rpn_bbox_pred)

@HEADS.register_module()
class StageCascadeRPNHead(RPNHead):
    """Stage of CascadeRPNHead.

    Args:
        in_channels (int): Number of channels in the input feature map.
        anchor_generator (dict): anchor generator config.
        adapt_cfg (dict): adaptation config.
        bridged_feature (bool, optional): whether update rpn feature.
            Default: False.
        with_cls (bool, optional): whether use classification branch.
            Default: True.
        sampling (bool, optional): whether use sampling. Default: True.
        init_cfg (dict or list[dict], optional): Initialization config dict.
            Default: None
    """

    def __init__(self, in_channels, anchor_generator=dict(type='AnchorGenerator', scales=[8], ratios=[1.0], strides=[4, 8, 16, 32, 64]), adapt_cfg=dict(type='dilation', dilation=3), bridged_feature=False, with_cls=True, sampling=True, init_cfg=None, **kwargs):
        self.with_cls = with_cls
        self.anchor_strides = anchor_generator['strides']
        self.anchor_scales = anchor_generator['scales']
        self.bridged_feature = bridged_feature
        self.adapt_cfg = adapt_cfg
        super(StageCascadeRPNHead, self).__init__(in_channels, anchor_generator=anchor_generator, init_cfg=init_cfg, **kwargs)
        self.sampling = sampling
        if self.train_cfg:
            self.assigner = build_assigner(self.train_cfg.assigner)
            if self.sampling and hasattr(self.train_cfg, 'sampler'):
                sampler_cfg = self.train_cfg.sampler
            else:
                sampler_cfg = dict(type='PseudoSampler')
            self.sampler = build_sampler(sampler_cfg, context=self)
        if init_cfg is None:
            self.init_cfg = dict(type='Normal', std=0.01, override=[dict(name='rpn_reg')])
            if self.with_cls:
                self.init_cfg['override'].append(dict(name='rpn_cls'))

    def _init_layers(self):
        """Init layers of a CascadeRPN stage."""
        self.rpn_conv = AdaptiveConv(self.in_channels, self.feat_channels, **self.adapt_cfg)
        if self.with_cls:
            self.rpn_cls = nn.Conv2d(self.feat_channels, self.num_anchors * self.cls_out_channels, 1)
        self.rpn_reg = nn.Conv2d(self.feat_channels, self.num_anchors * 4, 1)
        self.relu = nn.ReLU(inplace=True)

    def forward_single(self, x, offset):
        """Forward function of single scale."""
        bridged_x = x
        x = self.relu(self.rpn_conv(x, offset))
        if self.bridged_feature:
            bridged_x = x
        cls_score = self.rpn_cls(x) if self.with_cls else None
        bbox_pred = self.rpn_reg(x)
        return (bridged_x, cls_score, bbox_pred)

    def forward(self, feats, offset_list=None):
        """Forward function."""
        if offset_list is None:
            offset_list = [None for _ in range(len(feats))]
        return multi_apply(self.forward_single, feats, offset_list)

    def _region_targets_single(self, anchors, valid_flags, gt_bboxes, gt_bboxes_ignore, gt_labels, img_meta, featmap_sizes, label_channels=1):
        """Get anchor targets based on region for single level."""
        assign_result = self.assigner.assign(anchors, valid_flags, gt_bboxes, img_meta, featmap_sizes, self.anchor_scales[0], self.anchor_strides, gt_bboxes_ignore=gt_bboxes_ignore, gt_labels=None, allowed_border=self.train_cfg.allowed_border)
        flat_anchors = torch.cat(anchors)
        sampling_result = self.sampler.sample(assign_result, flat_anchors, gt_bboxes)
        num_anchors = flat_anchors.shape[0]
        bbox_targets = torch.zeros_like(flat_anchors)
        bbox_weights = torch.zeros_like(flat_anchors)
        labels = flat_anchors.new_zeros(num_anchors, dtype=torch.long)
        label_weights = flat_anchors.new_zeros(num_anchors, dtype=torch.float)
        pos_inds = sampling_result.pos_inds
        neg_inds = sampling_result.neg_inds
        if len(pos_inds) > 0:
            if not self.reg_decoded_bbox:
                pos_bbox_targets = self.bbox_coder.encode(sampling_result.pos_bboxes, sampling_result.pos_gt_bboxes)
            else:
                pos_bbox_targets = sampling_result.pos_gt_bboxes
            bbox_targets[pos_inds, :] = pos_bbox_targets
            bbox_weights[pos_inds, :] = 1.0
            if gt_labels is None:
                labels[pos_inds] = 1
            else:
                labels[pos_inds] = gt_labels[sampling_result.pos_assigned_gt_inds]
            if self.train_cfg.pos_weight <= 0:
                label_weights[pos_inds] = 1.0
            else:
                label_weights[pos_inds] = self.train_cfg.pos_weight
        if len(neg_inds) > 0:
            label_weights[neg_inds] = 1.0
        return (labels, label_weights, bbox_targets, bbox_weights, pos_inds, neg_inds)

    def region_targets(self, anchor_list, valid_flag_list, gt_bboxes_list, img_metas, featmap_sizes, gt_bboxes_ignore_list=None, gt_labels_list=None, label_channels=1, unmap_outputs=True):
        """See :func:`StageCascadeRPNHead.get_targets`."""
        num_imgs = len(img_metas)
        assert len(anchor_list) == len(valid_flag_list) == num_imgs
        num_level_anchors = [anchors.size(0) for anchors in anchor_list[0]]
        if gt_bboxes_ignore_list is None:
            gt_bboxes_ignore_list = [None for _ in range(num_imgs)]
        if gt_labels_list is None:
            gt_labels_list = [None for _ in range(num_imgs)]
        all_labels, all_label_weights, all_bbox_targets, all_bbox_weights, pos_inds_list, neg_inds_list = multi_apply(self._region_targets_single, anchor_list, valid_flag_list, gt_bboxes_list, gt_bboxes_ignore_list, gt_labels_list, img_metas, featmap_sizes=featmap_sizes, label_channels=label_channels)
        if any([labels is None for labels in all_labels]):
            return None
        num_total_pos = sum([max(inds.numel(), 1) for inds in pos_inds_list])
        num_total_neg = sum([max(inds.numel(), 1) for inds in neg_inds_list])
        labels_list = images_to_levels(all_labels, num_level_anchors)
        label_weights_list = images_to_levels(all_label_weights, num_level_anchors)
        bbox_targets_list = images_to_levels(all_bbox_targets, num_level_anchors)
        bbox_weights_list = images_to_levels(all_bbox_weights, num_level_anchors)
        return (labels_list, label_weights_list, bbox_targets_list, bbox_weights_list, num_total_pos, num_total_neg)

    def get_targets(self, anchor_list, valid_flag_list, gt_bboxes, img_metas, featmap_sizes, gt_bboxes_ignore=None, label_channels=1):
        """Compute regression and classification targets for anchors.

        Args:
            anchor_list (list[list]): Multi level anchors of each image.
            valid_flag_list (list[list]): Multi level valid flags of each
                image.
            gt_bboxes (list[Tensor]): Ground truth bboxes of each image.
            img_metas (list[dict]): Meta info of each image.
            featmap_sizes (list[Tensor]): Feature mapsize each level
            gt_bboxes_ignore (list[Tensor]): Ignore bboxes of each images
            label_channels (int): Channel of label.

        Returns:
            cls_reg_targets (tuple)
        """
        if isinstance(self.assigner, RegionAssigner):
            cls_reg_targets = self.region_targets(anchor_list, valid_flag_list, gt_bboxes, img_metas, featmap_sizes, gt_bboxes_ignore_list=gt_bboxes_ignore, label_channels=label_channels)
        else:
            cls_reg_targets = super(StageCascadeRPNHead, self).get_targets(anchor_list, valid_flag_list, gt_bboxes, img_metas, gt_bboxes_ignore_list=gt_bboxes_ignore, label_channels=label_channels)
        return cls_reg_targets

    def anchor_offset(self, anchor_list, anchor_strides, featmap_sizes):
        """ Get offset for deformable conv based on anchor shape
        NOTE: currently support deformable kernel_size=3 and dilation=1

        Args:
            anchor_list (list[list[tensor])): [NI, NLVL, NA, 4] list of
                multi-level anchors
            anchor_strides (list[int]): anchor stride of each level

        Returns:
            offset_list (list[tensor]): [NLVL, NA, 2, 18]: offset of DeformConv
                kernel.
        """

        def _shape_offset(anchors, stride, ks=3, dilation=1):
            assert ks == 3 and dilation == 1
            pad = (ks - 1) // 2
            idx = torch.arange(-pad, pad + 1, dtype=dtype, device=device)
            yy, xx = torch.meshgrid(idx, idx)
            xx = xx.reshape(-1)
            yy = yy.reshape(-1)
            w = (anchors[:, 2] - anchors[:, 0]) / stride
            h = (anchors[:, 3] - anchors[:, 1]) / stride
            w = w / (ks - 1) - dilation
            h = h / (ks - 1) - dilation
            offset_x = w[:, None] * xx
            offset_y = h[:, None] * yy
            return (offset_x, offset_y)

        def _ctr_offset(anchors, stride, featmap_size):
            feat_h, feat_w = featmap_size
            assert len(anchors) == feat_h * feat_w
            x = (anchors[:, 0] + anchors[:, 2]) * 0.5
            y = (anchors[:, 1] + anchors[:, 3]) * 0.5
            x = x / stride
            y = y / stride
            xx = torch.arange(0, feat_w, device=anchors.device)
            yy = torch.arange(0, feat_h, device=anchors.device)
            yy, xx = torch.meshgrid(yy, xx)
            xx = xx.reshape(-1).type_as(x)
            yy = yy.reshape(-1).type_as(y)
            offset_x = x - xx
            offset_y = y - yy
            return (offset_x, offset_y)
        num_imgs = len(anchor_list)
        num_lvls = len(anchor_list[0])
        dtype = anchor_list[0][0].dtype
        device = anchor_list[0][0].device
        num_level_anchors = [anchors.size(0) for anchors in anchor_list[0]]
        offset_list = []
        for i in range(num_imgs):
            mlvl_offset = []
            for lvl in range(num_lvls):
                c_offset_x, c_offset_y = _ctr_offset(anchor_list[i][lvl], anchor_strides[lvl], featmap_sizes[lvl])
                s_offset_x, s_offset_y = _shape_offset(anchor_list[i][lvl], anchor_strides[lvl])
                offset_x = s_offset_x + c_offset_x[:, None]
                offset_y = s_offset_y + c_offset_y[:, None]
                offset = torch.stack([offset_y, offset_x], dim=-1)
                offset = offset.reshape(offset.size(0), -1)
                mlvl_offset.append(offset)
            offset_list.append(torch.cat(mlvl_offset))
        offset_list = images_to_levels(offset_list, num_level_anchors)
        return offset_list

    def loss_single(self, cls_score, bbox_pred, anchors, labels, label_weights, bbox_targets, bbox_weights, num_total_samples):
        """Loss function on single scale."""
        if self.with_cls:
            labels = labels.reshape(-1)
            label_weights = label_weights.reshape(-1)
            cls_score = cls_score.permute(0, 2, 3, 1).reshape(-1, self.cls_out_channels)
            loss_cls = self.loss_cls(cls_score, labels, label_weights, avg_factor=num_total_samples)
        bbox_targets = bbox_targets.reshape(-1, 4)
        bbox_weights = bbox_weights.reshape(-1, 4)
        bbox_pred = bbox_pred.permute(0, 2, 3, 1).reshape(-1, 4)
        if self.reg_decoded_bbox:
            anchors = anchors.reshape(-1, 4)
            bbox_pred = self.bbox_coder.decode(anchors, bbox_pred)
        loss_reg = self.loss_bbox(bbox_pred, bbox_targets, bbox_weights, avg_factor=num_total_samples)
        if self.with_cls:
            return (loss_cls, loss_reg)
        return (None, loss_reg)

    def loss(self, anchor_list, valid_flag_list, cls_scores, bbox_preds, gt_bboxes, img_metas, gt_bboxes_ignore=None):
        """Compute losses of the head.

        Args:
            anchor_list (list[list]): Multi level anchors of each image.
            cls_scores (list[Tensor]): Box scores for each scale level
                Has shape (N, num_anchors * num_classes, H, W)
            bbox_preds (list[Tensor]): Box energies / deltas for each scale
                level with shape (N, num_anchors * 4, H, W)
            gt_bboxes (list[Tensor]): Ground truth bboxes for each image with
                shape (num_gts, 4) in [tl_x, tl_y, br_x, br_y] format.
            img_metas (list[dict]): Meta information of each image, e.g.,
                image size, scaling factor, etc.
            gt_bboxes_ignore (None | list[Tensor]): specify which bounding
                boxes can be ignored when computing the loss. Default: None

        Returns:
            dict[str, Tensor]: A dictionary of loss components.
        """
        featmap_sizes = [featmap.size()[-2:] for featmap in bbox_preds]
        label_channels = self.cls_out_channels if self.use_sigmoid_cls else 1
        cls_reg_targets = self.get_targets(anchor_list, valid_flag_list, gt_bboxes, img_metas, featmap_sizes, gt_bboxes_ignore=gt_bboxes_ignore, label_channels=label_channels)
        if cls_reg_targets is None:
            return None
        labels_list, label_weights_list, bbox_targets_list, bbox_weights_list, num_total_pos, num_total_neg = cls_reg_targets
        if self.sampling:
            num_total_samples = num_total_pos + num_total_neg
        else:
            num_total_samples = sum([label.numel() for label in labels_list]) / 200.0
        mlvl_anchor_list = list(zip(*anchor_list))
        mlvl_anchor_list = [torch.cat(anchors, dim=0) for anchors in mlvl_anchor_list]
        losses = multi_apply(self.loss_single, cls_scores, bbox_preds, mlvl_anchor_list, labels_list, label_weights_list, bbox_targets_list, bbox_weights_list, num_total_samples=num_total_samples)
        if self.with_cls:
            return dict(loss_rpn_cls=losses[0], loss_rpn_reg=losses[1])
        return dict(loss_rpn_reg=losses[1])

    def get_bboxes(self, anchor_list, cls_scores, bbox_preds, img_metas, cfg, rescale=False):
        """Get proposal predict.

        Args:
            anchor_list (list[list]): Multi level anchors of each image.
            cls_scores (list[Tensor]): Classification scores for all
                scale levels, each is a 4D-tensor, has shape
                (batch_size, num_priors * num_classes, H, W).
            bbox_preds (list[Tensor]): Box energies / deltas for all
                scale levels, each is a 4D-tensor, has shape
                (batch_size, num_priors * 4, H, W).
            img_metas (list[dict], Optional): Image meta info. Default None.
            cfg (mmcv.Config, Optional): Test / postprocessing configuration,
                if None, test_cfg would be used.
            rescale (bool): If True, return boxes in original image space.
                Default: False.

        Returns:
            Tensor: Labeled boxes in shape (n, 5), where the first 4 columns
                are bounding box positions (tl_x, tl_y, br_x, br_y) and the
                5-th column is a score between 0 and 1.
        """
        assert len(cls_scores) == len(bbox_preds)
        result_list = []
        for img_id in range(len(img_metas)):
            cls_score_list = select_single_mlvl(cls_scores, img_id)
            bbox_pred_list = select_single_mlvl(bbox_preds, img_id)
            img_shape = img_metas[img_id]['img_shape']
            scale_factor = img_metas[img_id]['scale_factor']
            proposals = self._get_bboxes_single(cls_score_list, bbox_pred_list, anchor_list[img_id], img_shape, scale_factor, cfg, rescale)
            result_list.append(proposals)
        return result_list

    def _get_bboxes_single(self, cls_scores, bbox_preds, mlvl_anchors, img_shape, scale_factor, cfg, rescale=False):
        """Transform outputs of a single image into bbox predictions.

        Args:
            cls_scores (list[Tensor]): Box scores from all scale
                levels of a single image, each item has shape
                (num_anchors * num_classes, H, W).
            bbox_preds (list[Tensor]): Box energies / deltas from
                all scale levels of a single image, each item has
                shape (num_anchors * 4, H, W).
            mlvl_anchors (list[Tensor]): Box reference from all scale
                levels of a single image, each item has shape
                (num_total_anchors, 4).
            img_shape (tuple[int]): Shape of the input image,
                (height, width, 3).
            scale_factor (ndarray): Scale factor of the image arange as
                (w_scale, h_scale, w_scale, h_scale).
            cfg (mmcv.Config): Test / postprocessing configuration,
                if None, test_cfg would be used.
            rescale (bool): If True, return boxes in original image space.
                Default False.

        Returns:
            Tensor: Labeled boxes in shape (n, 5), where the first 4 columns
                are bounding box positions (tl_x, tl_y, br_x, br_y) and the
                5-th column is a score between 0 and 1.
        """
        cfg = self.test_cfg if cfg is None else cfg
        cfg = copy.deepcopy(cfg)
        level_ids = []
        mlvl_scores = []
        mlvl_bbox_preds = []
        mlvl_valid_anchors = []
        nms_pre = cfg.get('nms_pre', -1)
        for idx in range(len(cls_scores)):
            rpn_cls_score = cls_scores[idx]
            rpn_bbox_pred = bbox_preds[idx]
            assert rpn_cls_score.size()[-2:] == rpn_bbox_pred.size()[-2:]
            rpn_cls_score = rpn_cls_score.permute(1, 2, 0)
            if self.use_sigmoid_cls:
                rpn_cls_score = rpn_cls_score.reshape(-1)
                scores = rpn_cls_score.sigmoid()
            else:
                rpn_cls_score = rpn_cls_score.reshape(-1, 2)
                scores = rpn_cls_score.softmax(dim=1)[:, 0]
            rpn_bbox_pred = rpn_bbox_pred.permute(1, 2, 0).reshape(-1, 4)
            anchors = mlvl_anchors[idx]
            if 0 < nms_pre < scores.shape[0]:
                ranked_scores, rank_inds = scores.sort(descending=True)
                topk_inds = rank_inds[:nms_pre]
                scores = ranked_scores[:nms_pre]
                rpn_bbox_pred = rpn_bbox_pred[topk_inds, :]
                anchors = anchors[topk_inds, :]
            mlvl_scores.append(scores)
            mlvl_bbox_preds.append(rpn_bbox_pred)
            mlvl_valid_anchors.append(anchors)
            level_ids.append(scores.new_full((scores.size(0),), idx, dtype=torch.long))
        scores = torch.cat(mlvl_scores)
        anchors = torch.cat(mlvl_valid_anchors)
        rpn_bbox_pred = torch.cat(mlvl_bbox_preds)
        proposals = self.bbox_coder.decode(anchors, rpn_bbox_pred, max_shape=img_shape)
        ids = torch.cat(level_ids)
        if cfg.min_bbox_size >= 0:
            w = proposals[:, 2] - proposals[:, 0]
            h = proposals[:, 3] - proposals[:, 1]
            valid_mask = (w > cfg.min_bbox_size) & (h > cfg.min_bbox_size)
            if not valid_mask.all():
                proposals = proposals[valid_mask]
                scores = scores[valid_mask]
                ids = ids[valid_mask]
        if 'nms' not in cfg or 'max_num' in cfg or 'nms_thr' in cfg:
            warnings.warn('In rpn_proposal or test_cfg, nms_thr has been moved to a dict named nms as iou_threshold, max_num has been renamed as max_per_img, name of original arguments and the way to specify iou_threshold of NMS will be deprecated.')
        if 'nms' not in cfg:
            cfg.nms = ConfigDict(dict(type='nms', iou_threshold=cfg.nms_thr))
        if 'max_num' in cfg:
            if 'max_per_img' in cfg:
                assert cfg.max_num == cfg.max_per_img, f'You set max_num and max_per_img at the same time, but get {cfg.max_num} and {cfg.max_per_img} respectivelyPlease delete max_num which will be deprecated.'
            else:
                cfg.max_per_img = cfg.max_num
        if 'nms_thr' in cfg:
            assert cfg.nms.iou_threshold == cfg.nms_thr, f'You set iou_threshold in nms and nms_thr at the same time, but get {cfg.nms.iou_threshold} and {cfg.nms_thr} respectively. Please delete the nms_thr which will be deprecated.'
        if proposals.numel() > 0:
            dets, _ = batched_nms(proposals, scores, ids, cfg.nms)
        else:
            return proposals.new_zeros(0, 5)
        return dets[:cfg.max_per_img]

    def refine_bboxes(self, anchor_list, bbox_preds, img_metas):
        """Refine bboxes through stages."""
        num_levels = len(bbox_preds)
        new_anchor_list = []
        for img_id in range(len(img_metas)):
            mlvl_anchors = []
            for i in range(num_levels):
                bbox_pred = bbox_preds[i][img_id].detach()
                bbox_pred = bbox_pred.permute(1, 2, 0).reshape(-1, 4)
                img_shape = img_metas[img_id]['img_shape']
                bboxes = self.bbox_coder.decode(anchor_list[img_id][i], bbox_pred, img_shape)
                mlvl_anchors.append(bboxes)
            new_anchor_list.append(mlvl_anchors)
        return new_anchor_list

def forward_single(self, x, offset):
    """Forward function of single scale."""
    bridged_x = x
    x = self.relu(self.rpn_conv(x, offset))
    if self.bridged_feature:
        bridged_x = x
    cls_score = self.rpn_cls(x) if self.with_cls else None
    bbox_pred = self.rpn_reg(x)
    return (bridged_x, cls_score, bbox_pred)

class FeatureAdaption(BaseModule):
    """Feature Adaption Module.

    Feature Adaption Module is implemented based on DCN v1.
    It uses anchor shape prediction rather than feature map to
    predict offsets of deform conv layer.

    Args:
        in_channels (int): Number of channels in the input feature map.
        out_channels (int): Number of channels in the output feature map.
        kernel_size (int): Deformable conv kernel size.
        deform_groups (int): Deformable conv group size.
        init_cfg (dict or list[dict], optional): Initialization config dict.
    """

    def __init__(self, in_channels, out_channels, kernel_size=3, deform_groups=4, init_cfg=dict(type='Normal', layer='Conv2d', std=0.1, override=dict(type='Normal', name='conv_adaption', std=0.01))):
        super(FeatureAdaption, self).__init__(init_cfg)
        offset_channels = kernel_size * kernel_size * 2
        self.conv_offset = nn.Conv2d(2, deform_groups * offset_channels, 1, bias=False)
        self.conv_adaption = DeformConv2d(in_channels, out_channels, kernel_size=kernel_size, padding=(kernel_size - 1) // 2, deform_groups=deform_groups)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x, shape):
        offset = self.conv_offset(shape.detach())
        x = self.relu(self.conv_adaption(x, offset))
        return x

def forward(self, x, shape):
    offset = self.conv_offset(shape.detach())
    x = self.relu(self.conv_adaption(x, offset))
    return x

class BiCornerPool(BaseModule):
    """Bidirectional Corner Pooling Module (TopLeft, BottomRight, etc.)

    Args:
        in_channels (int): Input channels of module.
        out_channels (int): Output channels of module.
        feat_channels (int): Feature channels of module.
        directions (list[str]): Directions of two CornerPools.
        norm_cfg (dict): Dictionary to construct and config norm layer.
        init_cfg (dict or list[dict], optional): Initialization config dict.
            Default: None
    """

    def __init__(self, in_channels, directions, feat_channels=128, out_channels=128, norm_cfg=dict(type='BN', requires_grad=True), init_cfg=None):
        super(BiCornerPool, self).__init__(init_cfg)
        self.direction1_conv = ConvModule(in_channels, feat_channels, 3, padding=1, norm_cfg=norm_cfg)
        self.direction2_conv = ConvModule(in_channels, feat_channels, 3, padding=1, norm_cfg=norm_cfg)
        self.aftpool_conv = ConvModule(feat_channels, out_channels, 3, padding=1, norm_cfg=norm_cfg, act_cfg=None)
        self.conv1 = ConvModule(in_channels, out_channels, 1, norm_cfg=norm_cfg, act_cfg=None)
        self.conv2 = ConvModule(in_channels, out_channels, 3, padding=1, norm_cfg=norm_cfg)
        self.direction1_pool = CornerPool(directions[0])
        self.direction2_pool = CornerPool(directions[1])
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        """Forward features from the upstream network.

        Args:
            x (tensor): Input feature of BiCornerPool.

        Returns:
            conv2 (tensor): Output feature of BiCornerPool.
        """
        direction1_conv = self.direction1_conv(x)
        direction2_conv = self.direction2_conv(x)
        direction1_feat = self.direction1_pool(direction1_conv)
        direction2_feat = self.direction2_pool(direction2_conv)
        aftpool_conv = self.aftpool_conv(direction1_feat + direction2_feat)
        conv1 = self.conv1(x)
        relu = self.relu(aftpool_conv + conv1)
        conv2 = self.conv2(relu)
        return conv2

def forward(self, x):
    """Forward features from the upstream network.

        Args:
            x (tensor): Input feature of BiCornerPool.

        Returns:
            conv2 (tensor): Output feature of BiCornerPool.
        """
    direction1_conv = self.direction1_conv(x)
    direction2_conv = self.direction2_conv(x)
    direction1_feat = self.direction1_pool(direction1_conv)
    direction2_feat = self.direction2_pool(direction2_conv)
    aftpool_conv = self.aftpool_conv(direction1_feat + direction2_feat)
    conv1 = self.conv1(x)
    relu = self.relu(aftpool_conv + conv1)
    conv2 = self.conv2(relu)
    return conv2

@HEADS.register_module()
class GARPNHead(GuidedAnchorHead):
    """Guided-Anchor-based RPN head."""

    def __init__(self, in_channels, init_cfg=dict(type='Normal', layer='Conv2d', std=0.01, override=dict(type='Normal', name='conv_loc', std=0.01, bias_prob=0.01)), **kwargs):
        super(GARPNHead, self).__init__(1, in_channels, init_cfg=init_cfg, **kwargs)

    def _init_layers(self):
        """Initialize layers of the head."""
        self.rpn_conv = nn.Conv2d(self.in_channels, self.feat_channels, 3, padding=1)
        super(GARPNHead, self)._init_layers()

    def forward_single(self, x):
        """Forward feature of a single scale level."""
        x = self.rpn_conv(x)
        x = F.relu(x, inplace=True)
        cls_score, bbox_pred, shape_pred, loc_pred = super(GARPNHead, self).forward_single(x)
        return (cls_score, bbox_pred, shape_pred, loc_pred)

    def loss(self, cls_scores, bbox_preds, shape_preds, loc_preds, gt_bboxes, img_metas, gt_bboxes_ignore=None):
        losses = super(GARPNHead, self).loss(cls_scores, bbox_preds, shape_preds, loc_preds, gt_bboxes, None, img_metas, gt_bboxes_ignore=gt_bboxes_ignore)
        return dict(loss_rpn_cls=losses['loss_cls'], loss_rpn_bbox=losses['loss_bbox'], loss_anchor_shape=losses['loss_shape'], loss_anchor_loc=losses['loss_loc'])

    def _get_bboxes_single(self, cls_scores, bbox_preds, mlvl_anchors, mlvl_masks, img_shape, scale_factor, cfg, rescale=False):
        cfg = self.test_cfg if cfg is None else cfg
        cfg = copy.deepcopy(cfg)
        if 'nms' not in cfg or 'max_num' in cfg or 'nms_thr' in cfg:
            warnings.warn('In rpn_proposal or test_cfg, nms_thr has been moved to a dict named nms as iou_threshold, max_num has been renamed as max_per_img, name of original arguments and the way to specify iou_threshold of NMS will be deprecated.')
        if 'nms' not in cfg:
            cfg.nms = ConfigDict(dict(type='nms', iou_threshold=cfg.nms_thr))
        if 'max_num' in cfg:
            if 'max_per_img' in cfg:
                assert cfg.max_num == cfg.max_per_img, f'You set max_num and max_per_img at the same time, but get {cfg.max_num} and {cfg.max_per_img} respectivelyPlease delete max_num which will be deprecated.'
            else:
                cfg.max_per_img = cfg.max_num
        if 'nms_thr' in cfg:
            assert cfg.nms.iou_threshold == cfg.nms_thr, f'You set iou_threshold in nms and nms_thr at the same time, but get {cfg.nms.iou_threshold} and {cfg.nms_thr} respectively. Please delete the nms_thr which will be deprecated.'
        assert cfg.nms.get('type', 'nms') == 'nms', 'GARPNHead only support naive nms.'
        mlvl_proposals = []
        for idx in range(len(cls_scores)):
            rpn_cls_score = cls_scores[idx]
            rpn_bbox_pred = bbox_preds[idx]
            anchors = mlvl_anchors[idx]
            mask = mlvl_masks[idx]
            assert rpn_cls_score.size()[-2:] == rpn_bbox_pred.size()[-2:]
            if mask.sum() == 0:
                continue
            rpn_cls_score = rpn_cls_score.permute(1, 2, 0)
            if self.use_sigmoid_cls:
                rpn_cls_score = rpn_cls_score.reshape(-1)
                scores = rpn_cls_score.sigmoid()
            else:
                rpn_cls_score = rpn_cls_score.reshape(-1, 2)
                scores = rpn_cls_score.softmax(dim=1)[:, :-1]
            scores = scores[mask]
            rpn_bbox_pred = rpn_bbox_pred.permute(1, 2, 0).reshape(-1, 4)[mask, :]
            if scores.dim() == 0:
                rpn_bbox_pred = rpn_bbox_pred.unsqueeze(0)
                anchors = anchors.unsqueeze(0)
                scores = scores.unsqueeze(0)
            if cfg.nms_pre > 0 and scores.shape[0] > cfg.nms_pre:
                _, topk_inds = scores.topk(cfg.nms_pre)
                rpn_bbox_pred = rpn_bbox_pred[topk_inds, :]
                anchors = anchors[topk_inds, :]
                scores = scores[topk_inds]
            proposals = self.bbox_coder.decode(anchors, rpn_bbox_pred, max_shape=img_shape)
            if cfg.min_bbox_size >= 0:
                w = proposals[:, 2] - proposals[:, 0]
                h = proposals[:, 3] - proposals[:, 1]
                valid_mask = (w > cfg.min_bbox_size) & (h > cfg.min_bbox_size)
                if not valid_mask.all():
                    proposals = proposals[valid_mask]
                    scores = scores[valid_mask]
            proposals, _ = nms(proposals, scores, cfg.nms.iou_threshold)
            proposals = proposals[:cfg.nms_post, :]
            mlvl_proposals.append(proposals)
        proposals = torch.cat(mlvl_proposals, 0)
        if cfg.get('nms_across_levels', False):
            proposals, _ = nms(proposals[:, :4], proposals[:, -1], cfg.nms.iou_threshold)
            proposals = proposals[:cfg.max_per_img, :]
        else:
            scores = proposals[:, 4]
            num = min(cfg.max_per_img, proposals.shape[0])
            _, topk_inds = scores.topk(num)
            proposals = proposals[topk_inds, :]
        return proposals

def forward_single(self, x):
    """Forward feature of a single scale level."""
    x = self.rpn_conv(x)
    x = F.relu(x, inplace=True)
    cls_score, bbox_pred, shape_pred, loc_pred = super(GARPNHead, self).forward_single(x)
    return (cls_score, bbox_pred, shape_pred, loc_pred)

@HEADS.register_module()
class FSAFHead(RetinaHead):
    """Anchor-free head used in `FSAF <https://arxiv.org/abs/1903.00621>`_.

    The head contains two subnetworks. The first classifies anchor boxes and
    the second regresses deltas for the anchors (num_anchors is 1 for anchor-
    free methods)

    Args:
        *args: Same as its base class in :class:`RetinaHead`
        score_threshold (float, optional): The score_threshold to calculate
            positive recall. If given, prediction scores lower than this value
            is counted as incorrect prediction. Default to None.
        init_cfg (dict or list[dict], optional): Initialization config dict.
            Default: None
        **kwargs: Same as its base class in :class:`RetinaHead`

    Example:
        >>> import torch
        >>> self = FSAFHead(11, 7)
        >>> x = torch.rand(1, 7, 32, 32)
        >>> cls_score, bbox_pred = self.forward_single(x)
        >>> # Each anchor predicts a score for each class except background
        >>> cls_per_anchor = cls_score.shape[1] / self.num_anchors
        >>> box_per_anchor = bbox_pred.shape[1] / self.num_anchors
        >>> assert cls_per_anchor == self.num_classes
        >>> assert box_per_anchor == 4
    """

    def __init__(self, *args, score_threshold=None, init_cfg=None, **kwargs):
        if init_cfg is None:
            init_cfg = dict(type='Normal', layer='Conv2d', std=0.01, override=[dict(type='Normal', name='retina_cls', std=0.01, bias_prob=0.01), dict(type='Normal', name='retina_reg', std=0.01, bias=0.25)])
        super().__init__(*args, init_cfg=init_cfg, **kwargs)
        self.score_threshold = score_threshold

    def forward_single(self, x):
        """Forward feature map of a single scale level.

        Args:
            x (Tensor): Feature map of a single scale level.

        Returns:
            tuple (Tensor):
                cls_score (Tensor): Box scores for each scale level
                    Has shape (N, num_points * num_classes, H, W).
                bbox_pred (Tensor): Box energies / deltas for each scale
                    level with shape (N, num_points * 4, H, W).
        """
        cls_score, bbox_pred = super().forward_single(x)
        return (cls_score, self.relu(bbox_pred))

    def _get_targets_single(self, flat_anchors, valid_flags, gt_bboxes, gt_bboxes_ignore, gt_labels, img_meta, label_channels=1, unmap_outputs=True):
        """Compute regression and classification targets for anchors in a
        single image.

        Most of the codes are the same with the base class
          :obj: `AnchorHead`, except that it also collects and returns
          the matched gt index in the image (from 0 to num_gt-1). If the
          anchor bbox is not matched to any gt, the corresponding value in
          pos_gt_inds is -1.
        """
        inside_flags = anchor_inside_flags(flat_anchors, valid_flags, img_meta['img_shape'][:2], self.train_cfg.allowed_border)
        if not inside_flags.any():
            return (None,) * 7
        anchors = flat_anchors[inside_flags.type(torch.bool), :]
        assign_result = self.assigner.assign(anchors, gt_bboxes, gt_bboxes_ignore, None if self.sampling else gt_labels)
        sampling_result = self.sampler.sample(assign_result, anchors, gt_bboxes)
        num_valid_anchors = anchors.shape[0]
        bbox_targets = torch.zeros_like(anchors)
        bbox_weights = torch.zeros_like(anchors)
        labels = anchors.new_full((num_valid_anchors,), self.num_classes, dtype=torch.long)
        label_weights = anchors.new_zeros((num_valid_anchors, label_channels), dtype=torch.float)
        pos_gt_inds = anchors.new_full((num_valid_anchors,), -1, dtype=torch.long)
        pos_inds = sampling_result.pos_inds
        neg_inds = sampling_result.neg_inds
        if len(pos_inds) > 0:
            if not self.reg_decoded_bbox:
                pos_bbox_targets = self.bbox_coder.encode(sampling_result.pos_bboxes, sampling_result.pos_gt_bboxes)
            else:
                pos_bbox_targets = sampling_result.pos_gt_bboxes
            bbox_targets[pos_inds, :] = pos_bbox_targets
            bbox_weights[pos_inds, :] = 1.0
            pos_gt_inds[pos_inds] = sampling_result.pos_assigned_gt_inds
            if gt_labels is None:
                labels[pos_inds] = 0
            else:
                labels[pos_inds] = gt_labels[sampling_result.pos_assigned_gt_inds]
            if self.train_cfg.pos_weight <= 0:
                label_weights[pos_inds] = 1.0
            else:
                label_weights[pos_inds] = self.train_cfg.pos_weight
        if len(neg_inds) > 0:
            label_weights[neg_inds] = 1.0
        shadowed_labels = assign_result.get_extra_property('shadowed_labels')
        if shadowed_labels is not None and shadowed_labels.numel():
            if len(shadowed_labels.shape) == 2:
                idx_, label_ = (shadowed_labels[:, 0], shadowed_labels[:, 1])
                assert (labels[idx_] != label_).all(), 'One label cannot be both positive and ignored'
                label_weights[idx_, label_] = 0
            else:
                label_weights[shadowed_labels] = 0
        if unmap_outputs:
            num_total_anchors = flat_anchors.size(0)
            labels = unmap(labels, num_total_anchors, inside_flags)
            label_weights = unmap(label_weights, num_total_anchors, inside_flags)
            bbox_targets = unmap(bbox_targets, num_total_anchors, inside_flags)
            bbox_weights = unmap(bbox_weights, num_total_anchors, inside_flags)
            pos_gt_inds = unmap(pos_gt_inds, num_total_anchors, inside_flags, fill=-1)
        return (labels, label_weights, bbox_targets, bbox_weights, pos_inds, neg_inds, sampling_result, pos_gt_inds)

    @force_fp32(apply_to=('cls_scores', 'bbox_preds'))
    def loss(self, cls_scores, bbox_preds, gt_bboxes, gt_labels, img_metas, gt_bboxes_ignore=None):
        """Compute loss of the head.

        Args:
            cls_scores (list[Tensor]): Box scores for each scale level
                Has shape (N, num_points * num_classes, H, W).
            bbox_preds (list[Tensor]): Box energies / deltas for each scale
                level with shape (N, num_points * 4, H, W).
            gt_bboxes (list[Tensor]): each item are the truth boxes for each
                image in [tl_x, tl_y, br_x, br_y] format.
            gt_labels (list[Tensor]): class indices corresponding to each box
            img_metas (list[dict]): Meta information of each image, e.g.,
                image size, scaling factor, etc.
            gt_bboxes_ignore (None | list[Tensor]): specify which bounding
                boxes can be ignored when computing the loss.

        Returns:
            dict[str, Tensor]: A dictionary of loss components.
        """
        for i in range(len(bbox_preds)):
            bbox_preds[i] = bbox_preds[i].clamp(min=0.0001)
        featmap_sizes = [featmap.size()[-2:] for featmap in cls_scores]
        assert len(featmap_sizes) == self.prior_generator.num_levels
        batch_size = len(gt_bboxes)
        device = cls_scores[0].device
        anchor_list, valid_flag_list = self.get_anchors(featmap_sizes, img_metas, device=device)
        label_channels = self.cls_out_channels if self.use_sigmoid_cls else 1
        cls_reg_targets = self.get_targets(anchor_list, valid_flag_list, gt_bboxes, img_metas, gt_bboxes_ignore_list=gt_bboxes_ignore, gt_labels_list=gt_labels, label_channels=label_channels)
        if cls_reg_targets is None:
            return None
        labels_list, label_weights_list, bbox_targets_list, bbox_weights_list, num_total_pos, num_total_neg, pos_assigned_gt_inds_list = cls_reg_targets
        num_gts = np.array(list(map(len, gt_labels)))
        num_total_samples = num_total_pos + num_total_neg if self.sampling else num_total_pos
        num_level_anchors = [anchors.size(0) for anchors in anchor_list[0]]
        concat_anchor_list = []
        for i in range(len(anchor_list)):
            concat_anchor_list.append(torch.cat(anchor_list[i]))
        all_anchor_list = images_to_levels(concat_anchor_list, num_level_anchors)
        losses_cls, losses_bbox = multi_apply(self.loss_single, cls_scores, bbox_preds, all_anchor_list, labels_list, label_weights_list, bbox_targets_list, bbox_weights_list, num_total_samples=num_total_samples)
        cum_num_gts = list(np.cumsum(num_gts))
        for i, assign in enumerate(pos_assigned_gt_inds_list):
            for j in range(1, batch_size):
                assign[j][assign[j] >= 0] += int(cum_num_gts[j - 1])
            pos_assigned_gt_inds_list[i] = assign.flatten()
            labels_list[i] = labels_list[i].flatten()
        num_gts = sum(map(len, gt_labels))
        label_sequence = torch.arange(num_gts, device=device)
        with torch.no_grad():
            loss_levels, = multi_apply(self.collect_loss_level_single, losses_cls, losses_bbox, pos_assigned_gt_inds_list, labels_seq=label_sequence)
            loss_levels = torch.stack(loss_levels, dim=0)
            if loss_levels.numel() == 0:
                argmin = loss_levels.new_empty((num_gts,), dtype=torch.long)
            else:
                _, argmin = loss_levels.min(dim=0)
        losses_cls, losses_bbox, pos_inds = multi_apply(self.reweight_loss_single, losses_cls, losses_bbox, pos_assigned_gt_inds_list, labels_list, list(range(len(losses_cls))), min_levels=argmin)
        num_pos = torch.cat(pos_inds, 0).sum().float()
        pos_recall = self.calculate_pos_recall(cls_scores, labels_list, pos_inds)
        if num_pos == 0:
            avg_factor = num_pos + float(num_total_neg)
        else:
            avg_factor = num_pos
        for i in range(len(losses_cls)):
            losses_cls[i] /= avg_factor
            losses_bbox[i] /= avg_factor
        return dict(loss_cls=losses_cls, loss_bbox=losses_bbox, num_pos=num_pos / batch_size, pos_recall=pos_recall)

    def calculate_pos_recall(self, cls_scores, labels_list, pos_inds):
        """Calculate positive recall with score threshold.

        Args:
            cls_scores (list[Tensor]): Classification scores at all fpn levels.
                Each tensor is in shape (N, num_classes * num_anchors, H, W)
            labels_list (list[Tensor]): The label that each anchor is assigned
                to. Shape (N * H * W * num_anchors, )
            pos_inds (list[Tensor]): List of bool tensors indicating whether
                the anchor is assigned to a positive label.
                Shape (N * H * W * num_anchors, )

        Returns:
            Tensor: A single float number indicating the positive recall.
        """
        with torch.no_grad():
            num_class = self.num_classes
            scores = [cls.permute(0, 2, 3, 1).reshape(-1, num_class)[pos] for cls, pos in zip(cls_scores, pos_inds)]
            labels = [label.reshape(-1)[pos] for label, pos in zip(labels_list, pos_inds)]
            scores = torch.cat(scores, dim=0)
            labels = torch.cat(labels, dim=0)
            if self.use_sigmoid_cls:
                scores = scores.sigmoid()
            else:
                scores = scores.softmax(dim=1)
            return accuracy(scores, labels, thresh=self.score_threshold)

    def collect_loss_level_single(self, cls_loss, reg_loss, assigned_gt_inds, labels_seq):
        """Get the average loss in each FPN level w.r.t. each gt label.

        Args:
            cls_loss (Tensor): Classification loss of each feature map pixel,
              shape (num_anchor, num_class)
            reg_loss (Tensor): Regression loss of each feature map pixel,
              shape (num_anchor, 4)
            assigned_gt_inds (Tensor): It indicates which gt the prior is
              assigned to (0-based, -1: no assignment). shape (num_anchor),
            labels_seq: The rank of labels. shape (num_gt)

        Returns:
            shape: (num_gt), average loss of each gt in this level
        """
        if len(reg_loss.shape) == 2:
            reg_loss = reg_loss.sum(dim=-1)
        if len(cls_loss.shape) == 2:
            cls_loss = cls_loss.sum(dim=-1)
        loss = cls_loss + reg_loss
        assert loss.size(0) == assigned_gt_inds.size(0)
        losses_ = loss.new_full(labels_seq.shape, 1000000.0)
        for i, l in enumerate(labels_seq):
            match = assigned_gt_inds == l
            if match.any():
                losses_[i] = loss[match].mean()
        return (losses_,)

    def reweight_loss_single(self, cls_loss, reg_loss, assigned_gt_inds, labels, level, min_levels):
        """Reweight loss values at each level.

        Reassign loss values at each level by masking those where the
        pre-calculated loss is too large. Then return the reduced losses.

        Args:
            cls_loss (Tensor): Element-wise classification loss.
              Shape: (num_anchors, num_classes)
            reg_loss (Tensor): Element-wise regression loss.
              Shape: (num_anchors, 4)
            assigned_gt_inds (Tensor): The gt indices that each anchor bbox
              is assigned to. -1 denotes a negative anchor, otherwise it is the
              gt index (0-based). Shape: (num_anchors, ),
            labels (Tensor): Label assigned to anchors. Shape: (num_anchors, ).
            level (int): The current level index in the pyramid
              (0-4 for RetinaNet)
            min_levels (Tensor): The best-matching level for each gt.
              Shape: (num_gts, ),

        Returns:
            tuple:
                - cls_loss: Reduced corrected classification loss. Scalar.
                - reg_loss: Reduced corrected regression loss. Scalar.
                - pos_flags (Tensor): Corrected bool tensor indicating the
                  final positive anchors. Shape: (num_anchors, ).
        """
        loc_weight = torch.ones_like(reg_loss)
        cls_weight = torch.ones_like(cls_loss)
        pos_flags = assigned_gt_inds >= 0
        pos_indices = torch.nonzero(pos_flags, as_tuple=False).flatten()
        if pos_flags.any():
            pos_assigned_gt_inds = assigned_gt_inds[pos_flags]
            zeroing_indices = min_levels[pos_assigned_gt_inds] != level
            neg_indices = pos_indices[zeroing_indices]
            if neg_indices.numel():
                pos_flags[neg_indices] = 0
                loc_weight[neg_indices] = 0
                zeroing_labels = labels[neg_indices]
                assert (zeroing_labels >= 0).all()
                cls_weight[neg_indices, zeroing_labels] = 0
        cls_loss = weight_reduce_loss(cls_loss, cls_weight, reduction='sum')
        reg_loss = weight_reduce_loss(reg_loss, loc_weight, reduction='sum')
        return (cls_loss, reg_loss, pos_flags)

def forward_single(self, x):
    """Forward feature map of a single scale level.

        Args:
            x (Tensor): Feature map of a single scale level.

        Returns:
            tuple (Tensor):
                cls_score (Tensor): Box scores for each scale level
                    Has shape (N, num_points * num_classes, H, W).
                bbox_pred (Tensor): Box energies / deltas for each scale
                    level with shape (N, num_points * 4, H, W).
        """
    cls_score, bbox_pred = super().forward_single(x)
    return (cls_score, self.relu(bbox_pred))

class FeatureAlign(BaseModule):

    def __init__(self, in_channels, out_channels, kernel_size=3, deform_groups=4, init_cfg=dict(type='Normal', layer='Conv2d', std=0.1, override=dict(type='Normal', name='conv_adaption', std=0.01))):
        super(FeatureAlign, self).__init__(init_cfg)
        offset_channels = kernel_size * kernel_size * 2
        self.conv_offset = nn.Conv2d(4, deform_groups * offset_channels, 1, bias=False)
        self.conv_adaption = DeformConv2d(in_channels, out_channels, kernel_size=kernel_size, padding=(kernel_size - 1) // 2, deform_groups=deform_groups)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x, shape):
        offset = self.conv_offset(shape)
        x = self.relu(self.conv_adaption(x, offset))
        return x

def forward(self, x, shape):
    offset = self.conv_offset(shape)
    x = self.relu(self.conv_adaption(x, offset))
    return x

class BasicResBlock(BaseModule):
    """Basic residual block.

    This block is a little different from the block in the ResNet backbone.
    The kernel size of conv1 is 1 in this block while 3 in ResNet BasicBlock.

    Args:
        in_channels (int): Channels of the input feature map.
        out_channels (int): Channels of the output feature map.
        conv_cfg (dict): The config dict for convolution layers.
        norm_cfg (dict): The config dict for normalization layers.
        init_cfg (dict or list[dict], optional): Initialization config dict.
            Default: None
    """

    def __init__(self, in_channels, out_channels, conv_cfg=None, norm_cfg=dict(type='BN'), init_cfg=None):
        super(BasicResBlock, self).__init__(init_cfg)
        self.conv1 = ConvModule(in_channels, in_channels, kernel_size=3, padding=1, bias=False, conv_cfg=conv_cfg, norm_cfg=norm_cfg)
        self.conv2 = ConvModule(in_channels, out_channels, kernel_size=1, bias=False, conv_cfg=conv_cfg, norm_cfg=norm_cfg, act_cfg=None)
        self.conv_identity = ConvModule(in_channels, out_channels, kernel_size=1, conv_cfg=conv_cfg, norm_cfg=norm_cfg, act_cfg=None)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        identity = x
        x = self.conv1(x)
        x = self.conv2(x)
        identity = self.conv_identity(identity)
        out = x + identity
        out = self.relu(out)
        return out

def forward(self, x):
    identity = x
    x = self.conv1(x)
    x = self.conv2(x)
    identity = self.conv_identity(identity)
    out = x + identity
    out = self.relu(out)
    return out

@HEADS.register_module()
class SABLHead(BaseModule):
    """Side-Aware Boundary Localization (SABL) for RoI-Head.

    Side-Aware features are extracted by conv layers
    with an attention mechanism.
    Boundary Localization with Bucketing and Bucketing Guided Rescoring
    are implemented in BucketingBBoxCoder.

    Please refer to https://arxiv.org/abs/1912.04260 for more details.

    Args:
        cls_in_channels (int): Input channels of cls RoI feature.             Defaults to 256.
        reg_in_channels (int): Input channels of reg RoI feature.             Defaults to 256.
        roi_feat_size (int): Size of RoI features. Defaults to 7.
        reg_feat_up_ratio (int): Upsample ratio of reg features.             Defaults to 2.
        reg_pre_kernel (int): Kernel of 2D conv layers before             attention pooling. Defaults to 3.
        reg_post_kernel (int): Kernel of 1D conv layers after             attention pooling. Defaults to 3.
        reg_pre_num (int): Number of pre convs. Defaults to 2.
        reg_post_num (int): Number of post convs. Defaults to 1.
        num_classes (int): Number of classes in dataset. Defaults to 80.
        cls_out_channels (int): Hidden channels in cls fcs. Defaults to 1024.
        reg_offset_out_channels (int): Hidden and output channel             of reg offset branch. Defaults to 256.
        reg_cls_out_channels (int): Hidden and output channel             of reg cls branch. Defaults to 256.
        num_cls_fcs (int): Number of fcs for cls branch. Defaults to 1.
        num_reg_fcs (int): Number of fcs for reg branch.. Defaults to 0.
        reg_class_agnostic (bool): Class agnostic regression or not.             Defaults to True.
        norm_cfg (dict): Config of norm layers. Defaults to None.
        bbox_coder (dict): Config of bbox coder. Defaults 'BucketingBBoxCoder'.
        loss_cls (dict): Config of classification loss.
        loss_bbox_cls (dict): Config of classification loss for bbox branch.
        loss_bbox_reg (dict): Config of regression loss for bbox branch.
        init_cfg (dict or list[dict], optional): Initialization config dict.
            Default: None
    """

    def __init__(self, num_classes, cls_in_channels=256, reg_in_channels=256, roi_feat_size=7, reg_feat_up_ratio=2, reg_pre_kernel=3, reg_post_kernel=3, reg_pre_num=2, reg_post_num=1, cls_out_channels=1024, reg_offset_out_channels=256, reg_cls_out_channels=256, num_cls_fcs=1, num_reg_fcs=0, reg_class_agnostic=True, norm_cfg=None, bbox_coder=dict(type='BucketingBBoxCoder', num_buckets=14, scale_factor=1.7), loss_cls=dict(type='CrossEntropyLoss', use_sigmoid=False, loss_weight=1.0), loss_bbox_cls=dict(type='CrossEntropyLoss', use_sigmoid=True, loss_weight=1.0), loss_bbox_reg=dict(type='SmoothL1Loss', beta=0.1, loss_weight=1.0), init_cfg=None):
        super(SABLHead, self).__init__(init_cfg)
        self.cls_in_channels = cls_in_channels
        self.reg_in_channels = reg_in_channels
        self.roi_feat_size = roi_feat_size
        self.reg_feat_up_ratio = int(reg_feat_up_ratio)
        self.num_buckets = bbox_coder['num_buckets']
        assert self.reg_feat_up_ratio // 2 >= 1
        self.up_reg_feat_size = roi_feat_size * self.reg_feat_up_ratio
        assert self.up_reg_feat_size == bbox_coder['num_buckets']
        self.reg_pre_kernel = reg_pre_kernel
        self.reg_post_kernel = reg_post_kernel
        self.reg_pre_num = reg_pre_num
        self.reg_post_num = reg_post_num
        self.num_classes = num_classes
        self.cls_out_channels = cls_out_channels
        self.reg_offset_out_channels = reg_offset_out_channels
        self.reg_cls_out_channels = reg_cls_out_channels
        self.num_cls_fcs = num_cls_fcs
        self.num_reg_fcs = num_reg_fcs
        self.reg_class_agnostic = reg_class_agnostic
        assert self.reg_class_agnostic
        self.norm_cfg = norm_cfg
        self.bbox_coder = build_bbox_coder(bbox_coder)
        self.loss_cls = build_loss(loss_cls)
        self.loss_bbox_cls = build_loss(loss_bbox_cls)
        self.loss_bbox_reg = build_loss(loss_bbox_reg)
        self.cls_fcs = self._add_fc_branch(self.num_cls_fcs, self.cls_in_channels, self.roi_feat_size, self.cls_out_channels)
        self.side_num = int(np.ceil(self.num_buckets / 2))
        if self.reg_feat_up_ratio > 1:
            self.upsample_x = nn.ConvTranspose1d(reg_in_channels, reg_in_channels, self.reg_feat_up_ratio, stride=self.reg_feat_up_ratio)
            self.upsample_y = nn.ConvTranspose1d(reg_in_channels, reg_in_channels, self.reg_feat_up_ratio, stride=self.reg_feat_up_ratio)
        self.reg_pre_convs = nn.ModuleList()
        for i in range(self.reg_pre_num):
            reg_pre_conv = ConvModule(reg_in_channels, reg_in_channels, kernel_size=reg_pre_kernel, padding=reg_pre_kernel // 2, norm_cfg=norm_cfg, act_cfg=dict(type='ReLU'))
            self.reg_pre_convs.append(reg_pre_conv)
        self.reg_post_conv_xs = nn.ModuleList()
        for i in range(self.reg_post_num):
            reg_post_conv_x = ConvModule(reg_in_channels, reg_in_channels, kernel_size=(1, reg_post_kernel), padding=(0, reg_post_kernel // 2), norm_cfg=norm_cfg, act_cfg=dict(type='ReLU'))
            self.reg_post_conv_xs.append(reg_post_conv_x)
        self.reg_post_conv_ys = nn.ModuleList()
        for i in range(self.reg_post_num):
            reg_post_conv_y = ConvModule(reg_in_channels, reg_in_channels, kernel_size=(reg_post_kernel, 1), padding=(reg_post_kernel // 2, 0), norm_cfg=norm_cfg, act_cfg=dict(type='ReLU'))
            self.reg_post_conv_ys.append(reg_post_conv_y)
        self.reg_conv_att_x = nn.Conv2d(reg_in_channels, 1, 1)
        self.reg_conv_att_y = nn.Conv2d(reg_in_channels, 1, 1)
        self.fc_cls = nn.Linear(self.cls_out_channels, self.num_classes + 1)
        self.relu = nn.ReLU(inplace=True)
        self.reg_cls_fcs = self._add_fc_branch(self.num_reg_fcs, self.reg_in_channels, 1, self.reg_cls_out_channels)
        self.reg_offset_fcs = self._add_fc_branch(self.num_reg_fcs, self.reg_in_channels, 1, self.reg_offset_out_channels)
        self.fc_reg_cls = nn.Linear(self.reg_cls_out_channels, 1)
        self.fc_reg_offset = nn.Linear(self.reg_offset_out_channels, 1)
        if init_cfg is None:
            self.init_cfg = [dict(type='Xavier', layer='Linear', distribution='uniform', override=[dict(type='Normal', name='reg_conv_att_x', std=0.01), dict(type='Normal', name='reg_conv_att_y', std=0.01), dict(type='Normal', name='fc_reg_cls', std=0.01), dict(type='Normal', name='fc_cls', std=0.01), dict(type='Normal', name='fc_reg_offset', std=0.001)])]
            if self.reg_feat_up_ratio > 1:
                self.init_cfg += [dict(type='Kaiming', distribution='normal', override=[dict(name='upsample_x'), dict(name='upsample_y')])]

    @property
    def custom_cls_channels(self):
        return getattr(self.loss_cls, 'custom_cls_channels', False)

    @property
    def custom_activation(self):
        return getattr(self.loss_cls, 'custom_activation', False)

    @property
    def custom_accuracy(self):
        return getattr(self.loss_cls, 'custom_accuracy', False)

    def _add_fc_branch(self, num_branch_fcs, in_channels, roi_feat_size, fc_out_channels):
        in_channels = in_channels * roi_feat_size * roi_feat_size
        branch_fcs = nn.ModuleList()
        for i in range(num_branch_fcs):
            fc_in_channels = in_channels if i == 0 else fc_out_channels
            branch_fcs.append(nn.Linear(fc_in_channels, fc_out_channels))
        return branch_fcs

    def cls_forward(self, cls_x):
        cls_x = cls_x.view(cls_x.size(0), -1)
        for fc in self.cls_fcs:
            cls_x = self.relu(fc(cls_x))
        cls_score = self.fc_cls(cls_x)
        return cls_score

    def attention_pool(self, reg_x):
        """Extract direction-specific features fx and fy with attention
        methanism."""
        reg_fx = reg_x
        reg_fy = reg_x
        reg_fx_att = self.reg_conv_att_x(reg_fx).sigmoid()
        reg_fy_att = self.reg_conv_att_y(reg_fy).sigmoid()
        reg_fx_att = reg_fx_att / reg_fx_att.sum(dim=2).unsqueeze(2)
        reg_fy_att = reg_fy_att / reg_fy_att.sum(dim=3).unsqueeze(3)
        reg_fx = (reg_fx * reg_fx_att).sum(dim=2)
        reg_fy = (reg_fy * reg_fy_att).sum(dim=3)
        return (reg_fx, reg_fy)

    def side_aware_feature_extractor(self, reg_x):
        """Refine and extract side-aware features without split them."""
        for reg_pre_conv in self.reg_pre_convs:
            reg_x = reg_pre_conv(reg_x)
        reg_fx, reg_fy = self.attention_pool(reg_x)
        if self.reg_post_num > 0:
            reg_fx = reg_fx.unsqueeze(2)
            reg_fy = reg_fy.unsqueeze(3)
            for i in range(self.reg_post_num):
                reg_fx = self.reg_post_conv_xs[i](reg_fx)
                reg_fy = self.reg_post_conv_ys[i](reg_fy)
            reg_fx = reg_fx.squeeze(2)
            reg_fy = reg_fy.squeeze(3)
        if self.reg_feat_up_ratio > 1:
            reg_fx = self.relu(self.upsample_x(reg_fx))
            reg_fy = self.relu(self.upsample_y(reg_fy))
        reg_fx = torch.transpose(reg_fx, 1, 2)
        reg_fy = torch.transpose(reg_fy, 1, 2)
        return (reg_fx.contiguous(), reg_fy.contiguous())

    def reg_pred(self, x, offset_fcs, cls_fcs):
        """Predict bucketing estimation (cls_pred) and fine regression (offset
        pred) with side-aware features."""
        x_offset = x.view(-1, self.reg_in_channels)
        x_cls = x.view(-1, self.reg_in_channels)
        for fc in offset_fcs:
            x_offset = self.relu(fc(x_offset))
        for fc in cls_fcs:
            x_cls = self.relu(fc(x_cls))
        offset_pred = self.fc_reg_offset(x_offset)
        cls_pred = self.fc_reg_cls(x_cls)
        offset_pred = offset_pred.view(x.size(0), -1)
        cls_pred = cls_pred.view(x.size(0), -1)
        return (offset_pred, cls_pred)

    def side_aware_split(self, feat):
        """Split side-aware features aligned with orders of bucketing
        targets."""
        l_end = int(np.ceil(self.up_reg_feat_size / 2))
        r_start = int(np.floor(self.up_reg_feat_size / 2))
        feat_fl = feat[:, :l_end]
        feat_fr = feat[:, r_start:].flip(dims=(1,))
        feat_fl = feat_fl.contiguous()
        feat_fr = feat_fr.contiguous()
        feat = torch.cat([feat_fl, feat_fr], dim=-1)
        return feat

    def bbox_pred_split(self, bbox_pred, num_proposals_per_img):
        """Split batch bbox prediction back to each image."""
        bucket_cls_preds, bucket_offset_preds = bbox_pred
        bucket_cls_preds = bucket_cls_preds.split(num_proposals_per_img, 0)
        bucket_offset_preds = bucket_offset_preds.split(num_proposals_per_img, 0)
        bbox_pred = tuple(zip(bucket_cls_preds, bucket_offset_preds))
        return bbox_pred

    def reg_forward(self, reg_x):
        outs = self.side_aware_feature_extractor(reg_x)
        edge_offset_preds = []
        edge_cls_preds = []
        reg_fx = outs[0]
        reg_fy = outs[1]
        offset_pred_x, cls_pred_x = self.reg_pred(reg_fx, self.reg_offset_fcs, self.reg_cls_fcs)
        offset_pred_y, cls_pred_y = self.reg_pred(reg_fy, self.reg_offset_fcs, self.reg_cls_fcs)
        offset_pred_x = self.side_aware_split(offset_pred_x)
        offset_pred_y = self.side_aware_split(offset_pred_y)
        cls_pred_x = self.side_aware_split(cls_pred_x)
        cls_pred_y = self.side_aware_split(cls_pred_y)
        edge_offset_preds = torch.cat([offset_pred_x, offset_pred_y], dim=-1)
        edge_cls_preds = torch.cat([cls_pred_x, cls_pred_y], dim=-1)
        return (edge_cls_preds, edge_offset_preds)

    def forward(self, x):
        bbox_pred = self.reg_forward(x)
        cls_score = self.cls_forward(x)
        return (cls_score, bbox_pred)

    def get_targets(self, sampling_results, gt_bboxes, gt_labels, rcnn_train_cfg):
        pos_proposals = [res.pos_bboxes for res in sampling_results]
        neg_proposals = [res.neg_bboxes for res in sampling_results]
        pos_gt_bboxes = [res.pos_gt_bboxes for res in sampling_results]
        pos_gt_labels = [res.pos_gt_labels for res in sampling_results]
        cls_reg_targets = self.bucket_target(pos_proposals, neg_proposals, pos_gt_bboxes, pos_gt_labels, rcnn_train_cfg)
        labels, label_weights, bucket_cls_targets, bucket_cls_weights, bucket_offset_targets, bucket_offset_weights = cls_reg_targets
        return (labels, label_weights, (bucket_cls_targets, bucket_offset_targets), (bucket_cls_weights, bucket_offset_weights))

    def bucket_target(self, pos_proposals_list, neg_proposals_list, pos_gt_bboxes_list, pos_gt_labels_list, rcnn_train_cfg, concat=True):
        labels, label_weights, bucket_cls_targets, bucket_cls_weights, bucket_offset_targets, bucket_offset_weights = multi_apply(self._bucket_target_single, pos_proposals_list, neg_proposals_list, pos_gt_bboxes_list, pos_gt_labels_list, cfg=rcnn_train_cfg)
        if concat:
            labels = torch.cat(labels, 0)
            label_weights = torch.cat(label_weights, 0)
            bucket_cls_targets = torch.cat(bucket_cls_targets, 0)
            bucket_cls_weights = torch.cat(bucket_cls_weights, 0)
            bucket_offset_targets = torch.cat(bucket_offset_targets, 0)
            bucket_offset_weights = torch.cat(bucket_offset_weights, 0)
        return (labels, label_weights, bucket_cls_targets, bucket_cls_weights, bucket_offset_targets, bucket_offset_weights)

    def _bucket_target_single(self, pos_proposals, neg_proposals, pos_gt_bboxes, pos_gt_labels, cfg):
        """Compute bucketing estimation targets and fine regression targets for
        a single image.

        Args:
            pos_proposals (Tensor): positive proposals of a single image,
                 Shape (n_pos, 4)
            neg_proposals (Tensor): negative proposals of a single image,
                 Shape (n_neg, 4).
            pos_gt_bboxes (Tensor): gt bboxes assigned to positive proposals
                 of a single image, Shape (n_pos, 4).
            pos_gt_labels (Tensor): gt labels assigned to positive proposals
                 of a single image, Shape (n_pos, ).
            cfg (dict): Config of calculating targets

        Returns:
            tuple:

                - labels (Tensor): Labels in a single image.                     Shape (n,).
                - label_weights (Tensor): Label weights in a single image.                    Shape (n,)
                - bucket_cls_targets (Tensor): Bucket cls targets in                     a single image. Shape (n, num_buckets*2).
                - bucket_cls_weights (Tensor): Bucket cls weights in                     a single image. Shape (n, num_buckets*2).
                - bucket_offset_targets (Tensor): Bucket offset targets                     in a single image. Shape (n, num_buckets*2).
                - bucket_offset_targets (Tensor): Bucket offset weights                     in a single image. Shape (n, num_buckets*2).
        """
        num_pos = pos_proposals.size(0)
        num_neg = neg_proposals.size(0)
        num_samples = num_pos + num_neg
        labels = pos_gt_bboxes.new_full((num_samples,), self.num_classes, dtype=torch.long)
        label_weights = pos_proposals.new_zeros(num_samples)
        bucket_cls_targets = pos_proposals.new_zeros(num_samples, 4 * self.side_num)
        bucket_cls_weights = pos_proposals.new_zeros(num_samples, 4 * self.side_num)
        bucket_offset_targets = pos_proposals.new_zeros(num_samples, 4 * self.side_num)
        bucket_offset_weights = pos_proposals.new_zeros(num_samples, 4 * self.side_num)
        if num_pos > 0:
            labels[:num_pos] = pos_gt_labels
            label_weights[:num_pos] = 1.0
            pos_bucket_offset_targets, pos_bucket_offset_weights, pos_bucket_cls_targets, pos_bucket_cls_weights = self.bbox_coder.encode(pos_proposals, pos_gt_bboxes)
            bucket_cls_targets[:num_pos, :] = pos_bucket_cls_targets
            bucket_cls_weights[:num_pos, :] = pos_bucket_cls_weights
            bucket_offset_targets[:num_pos, :] = pos_bucket_offset_targets
            bucket_offset_weights[:num_pos, :] = pos_bucket_offset_weights
        if num_neg > 0:
            label_weights[-num_neg:] = 1.0
        return (labels, label_weights, bucket_cls_targets, bucket_cls_weights, bucket_offset_targets, bucket_offset_weights)

    def loss(self, cls_score, bbox_pred, rois, labels, label_weights, bbox_targets, bbox_weights, reduction_override=None):
        losses = dict()
        if cls_score is not None:
            avg_factor = max(torch.sum(label_weights > 0).float().item(), 1.0)
            losses['loss_cls'] = self.loss_cls(cls_score, labels, label_weights, avg_factor=avg_factor, reduction_override=reduction_override)
            losses['acc'] = accuracy(cls_score, labels)
        if bbox_pred is not None:
            bucket_cls_preds, bucket_offset_preds = bbox_pred
            bucket_cls_targets, bucket_offset_targets = bbox_targets
            bucket_cls_weights, bucket_offset_weights = bbox_weights
            bucket_cls_preds = bucket_cls_preds.view(-1, self.side_num)
            bucket_cls_targets = bucket_cls_targets.view(-1, self.side_num)
            bucket_cls_weights = bucket_cls_weights.view(-1, self.side_num)
            losses['loss_bbox_cls'] = self.loss_bbox_cls(bucket_cls_preds, bucket_cls_targets, bucket_cls_weights, avg_factor=bucket_cls_targets.size(0), reduction_override=reduction_override)
            losses['loss_bbox_reg'] = self.loss_bbox_reg(bucket_offset_preds, bucket_offset_targets, bucket_offset_weights, avg_factor=bucket_offset_targets.size(0), reduction_override=reduction_override)
        return losses

    @force_fp32(apply_to=('cls_score', 'bbox_pred'))
    def get_bboxes(self, rois, cls_score, bbox_pred, img_shape, scale_factor, rescale=False, cfg=None):
        if isinstance(cls_score, list):
            cls_score = sum(cls_score) / float(len(cls_score))
        scores = F.softmax(cls_score, dim=1) if cls_score is not None else None
        if bbox_pred is not None:
            bboxes, confidences = self.bbox_coder.decode(rois[:, 1:], bbox_pred, img_shape)
        else:
            bboxes = rois[:, 1:].clone()
            confidences = None
            if img_shape is not None:
                bboxes[:, [0, 2]].clamp_(min=0, max=img_shape[1] - 1)
                bboxes[:, [1, 3]].clamp_(min=0, max=img_shape[0] - 1)
        if rescale and bboxes.size(0) > 0:
            if isinstance(scale_factor, float):
                bboxes /= scale_factor
            else:
                bboxes /= torch.from_numpy(scale_factor).to(bboxes.device)
        if cfg is None:
            return (bboxes, scores)
        else:
            det_bboxes, det_labels = multiclass_nms(bboxes, scores, cfg.score_thr, cfg.nms, cfg.max_per_img, score_factors=confidences)
            return (det_bboxes, det_labels)

    @force_fp32(apply_to=('bbox_preds',))
    def refine_bboxes(self, rois, labels, bbox_preds, pos_is_gts, img_metas):
        """Refine bboxes during training.

        Args:
            rois (Tensor): Shape (n*bs, 5), where n is image number per GPU,
                and bs is the sampled RoIs per image.
            labels (Tensor): Shape (n*bs, ).
            bbox_preds (list[Tensor]): Shape [(n*bs, num_buckets*2),                 (n*bs, num_buckets*2)].
            pos_is_gts (list[Tensor]): Flags indicating if each positive bbox
                is a gt bbox.
            img_metas (list[dict]): Meta info of each image.

        Returns:
            list[Tensor]: Refined bboxes of each image in a mini-batch.
        """
        img_ids = rois[:, 0].long().unique(sorted=True)
        assert img_ids.numel() == len(img_metas)
        bboxes_list = []
        for i in range(len(img_metas)):
            inds = torch.nonzero(rois[:, 0] == i, as_tuple=False).squeeze(dim=1)
            num_rois = inds.numel()
            bboxes_ = rois[inds, 1:]
            label_ = labels[inds]
            edge_cls_preds, edge_offset_preds = bbox_preds
            edge_cls_preds_ = edge_cls_preds[inds]
            edge_offset_preds_ = edge_offset_preds[inds]
            bbox_pred_ = [edge_cls_preds_, edge_offset_preds_]
            img_meta_ = img_metas[i]
            pos_is_gts_ = pos_is_gts[i]
            bboxes = self.regress_by_class(bboxes_, label_, bbox_pred_, img_meta_)
            pos_keep = 1 - pos_is_gts_
            keep_inds = pos_is_gts_.new_ones(num_rois)
            keep_inds[:len(pos_is_gts_)] = pos_keep
            bboxes_list.append(bboxes[keep_inds.type(torch.bool)])
        return bboxes_list

    @force_fp32(apply_to=('bbox_pred',))
    def regress_by_class(self, rois, label, bbox_pred, img_meta):
        """Regress the bbox for the predicted class. Used in Cascade R-CNN.

        Args:
            rois (Tensor): shape (n, 4) or (n, 5)
            label (Tensor): shape (n, )
            bbox_pred (list[Tensor]): shape [(n, num_buckets *2),                 (n, num_buckets *2)]
            img_meta (dict): Image meta info.

        Returns:
            Tensor: Regressed bboxes, the same shape as input rois.
        """
        assert rois.size(1) == 4 or rois.size(1) == 5
        if rois.size(1) == 4:
            new_rois, _ = self.bbox_coder.decode(rois, bbox_pred, img_meta['img_shape'])
        else:
            bboxes, _ = self.bbox_coder.decode(rois[:, 1:], bbox_pred, img_meta['img_shape'])
            new_rois = torch.cat((rois[:, [0]], bboxes), dim=1)
        return new_rois

def side_aware_feature_extractor(self, reg_x):
    """Refine and extract side-aware features without split them."""
    for reg_pre_conv in self.reg_pre_convs:
        reg_x = reg_pre_conv(reg_x)
    reg_fx, reg_fy = self.attention_pool(reg_x)
    if self.reg_post_num > 0:
        reg_fx = reg_fx.unsqueeze(2)
        reg_fy = reg_fy.unsqueeze(3)
        for i in range(self.reg_post_num):
            reg_fx = self.reg_post_conv_xs[i](reg_fx)
            reg_fy = self.reg_post_conv_ys[i](reg_fy)
        reg_fx = reg_fx.squeeze(2)
        reg_fy = reg_fy.squeeze(3)
    if self.reg_feat_up_ratio > 1:
        reg_fx = self.relu(self.upsample_x(reg_fx))
        reg_fy = self.relu(self.upsample_y(reg_fy))
    reg_fx = torch.transpose(reg_fx, 1, 2)
    reg_fy = torch.transpose(reg_fy, 1, 2)
    return (reg_fx.contiguous(), reg_fy.contiguous())

@HEADS.register_module()
class GridHead(BaseModule):

    def __init__(self, grid_points=9, num_convs=8, roi_feat_size=14, in_channels=256, conv_kernel_size=3, point_feat_channels=64, deconv_kernel_size=4, class_agnostic=False, loss_grid=dict(type='CrossEntropyLoss', use_sigmoid=True, loss_weight=15), conv_cfg=None, norm_cfg=dict(type='GN', num_groups=36), init_cfg=[dict(type='Kaiming', layer=['Conv2d', 'Linear']), dict(type='Normal', layer='ConvTranspose2d', std=0.001, override=dict(type='Normal', name='deconv2', std=0.001, bias=-np.log(0.99 / 0.01)))]):
        super(GridHead, self).__init__(init_cfg)
        self.grid_points = grid_points
        self.num_convs = num_convs
        self.roi_feat_size = roi_feat_size
        self.in_channels = in_channels
        self.conv_kernel_size = conv_kernel_size
        self.point_feat_channels = point_feat_channels
        self.conv_out_channels = self.point_feat_channels * self.grid_points
        self.class_agnostic = class_agnostic
        self.conv_cfg = conv_cfg
        self.norm_cfg = norm_cfg
        if isinstance(norm_cfg, dict) and norm_cfg['type'] == 'GN':
            assert self.conv_out_channels % norm_cfg['num_groups'] == 0
        assert self.grid_points >= 4
        self.grid_size = int(np.sqrt(self.grid_points))
        if self.grid_size * self.grid_size != self.grid_points:
            raise ValueError('grid_points must be a square number')
        if not isinstance(self.roi_feat_size, int):
            raise ValueError('Only square RoIs are supporeted in Grid R-CNN')
        self.whole_map_size = self.roi_feat_size * 4
        self.sub_regions = self.calc_sub_regions()
        self.convs = []
        for i in range(self.num_convs):
            in_channels = self.in_channels if i == 0 else self.conv_out_channels
            stride = 2 if i == 0 else 1
            padding = (self.conv_kernel_size - 1) // 2
            self.convs.append(ConvModule(in_channels, self.conv_out_channels, self.conv_kernel_size, stride=stride, padding=padding, conv_cfg=self.conv_cfg, norm_cfg=self.norm_cfg, bias=True))
        self.convs = nn.Sequential(*self.convs)
        self.deconv1 = nn.ConvTranspose2d(self.conv_out_channels, self.conv_out_channels, kernel_size=deconv_kernel_size, stride=2, padding=(deconv_kernel_size - 2) // 2, groups=grid_points)
        self.norm1 = nn.GroupNorm(grid_points, self.conv_out_channels)
        self.deconv2 = nn.ConvTranspose2d(self.conv_out_channels, grid_points, kernel_size=deconv_kernel_size, stride=2, padding=(deconv_kernel_size - 2) // 2, groups=grid_points)
        self.neighbor_points = []
        grid_size = self.grid_size
        for i in range(grid_size):
            for j in range(grid_size):
                neighbors = []
                if i > 0:
                    neighbors.append((i - 1) * grid_size + j)
                if j > 0:
                    neighbors.append(i * grid_size + j - 1)
                if j < grid_size - 1:
                    neighbors.append(i * grid_size + j + 1)
                if i < grid_size - 1:
                    neighbors.append((i + 1) * grid_size + j)
                self.neighbor_points.append(tuple(neighbors))
        self.num_edges = sum([len(p) for p in self.neighbor_points])
        self.forder_trans = nn.ModuleList()
        self.sorder_trans = nn.ModuleList()
        for neighbors in self.neighbor_points:
            fo_trans = nn.ModuleList()
            so_trans = nn.ModuleList()
            for _ in range(len(neighbors)):
                fo_trans.append(nn.Sequential(nn.Conv2d(self.point_feat_channels, self.point_feat_channels, 5, stride=1, padding=2, groups=self.point_feat_channels), nn.Conv2d(self.point_feat_channels, self.point_feat_channels, 1)))
                so_trans.append(nn.Sequential(nn.Conv2d(self.point_feat_channels, self.point_feat_channels, 5, 1, 2, groups=self.point_feat_channels), nn.Conv2d(self.point_feat_channels, self.point_feat_channels, 1)))
            self.forder_trans.append(fo_trans)
            self.sorder_trans.append(so_trans)
        self.loss_grid = build_loss(loss_grid)

    def forward(self, x):
        assert x.shape[-1] == x.shape[-2] == self.roi_feat_size
        x = self.convs(x)
        c = self.point_feat_channels
        x_fo = [None for _ in range(self.grid_points)]
        for i, points in enumerate(self.neighbor_points):
            x_fo[i] = x[:, i * c:(i + 1) * c]
            for j, point_idx in enumerate(points):
                x_fo[i] = x_fo[i] + self.forder_trans[i][j](x[:, point_idx * c:(point_idx + 1) * c])
        x_so = [None for _ in range(self.grid_points)]
        for i, points in enumerate(self.neighbor_points):
            x_so[i] = x[:, i * c:(i + 1) * c]
            for j, point_idx in enumerate(points):
                x_so[i] = x_so[i] + self.sorder_trans[i][j](x_fo[point_idx])
        x2 = torch.cat(x_so, dim=1)
        x2 = self.deconv1(x2)
        x2 = F.relu(self.norm1(x2), inplace=True)
        heatmap = self.deconv2(x2)
        if self.training:
            x1 = x
            x1 = self.deconv1(x1)
            x1 = F.relu(self.norm1(x1), inplace=True)
            heatmap_unfused = self.deconv2(x1)
        else:
            heatmap_unfused = heatmap
        return dict(fused=heatmap, unfused=heatmap_unfused)

    def calc_sub_regions(self):
        """Compute point specific representation regions.

        See Grid R-CNN Plus (https://arxiv.org/abs/1906.05688) for details.
        """
        half_size = self.whole_map_size // 4 * 2
        sub_regions = []
        for i in range(self.grid_points):
            x_idx = i // self.grid_size
            y_idx = i % self.grid_size
            if x_idx == 0:
                sub_x1 = 0
            elif x_idx == self.grid_size - 1:
                sub_x1 = half_size
            else:
                ratio = x_idx / (self.grid_size - 1) - 0.25
                sub_x1 = max(int(ratio * self.whole_map_size), 0)
            if y_idx == 0:
                sub_y1 = 0
            elif y_idx == self.grid_size - 1:
                sub_y1 = half_size
            else:
                ratio = y_idx / (self.grid_size - 1) - 0.25
                sub_y1 = max(int(ratio * self.whole_map_size), 0)
            sub_regions.append((sub_x1, sub_y1, sub_x1 + half_size, sub_y1 + half_size))
        return sub_regions

    def get_targets(self, sampling_results, rcnn_train_cfg):
        pos_bboxes = torch.cat([res.pos_bboxes for res in sampling_results], dim=0).cpu()
        pos_gt_bboxes = torch.cat([res.pos_gt_bboxes for res in sampling_results], dim=0).cpu()
        assert pos_bboxes.shape == pos_gt_bboxes.shape
        x1 = pos_bboxes[:, 0] - (pos_bboxes[:, 2] - pos_bboxes[:, 0]) / 2
        y1 = pos_bboxes[:, 1] - (pos_bboxes[:, 3] - pos_bboxes[:, 1]) / 2
        x2 = pos_bboxes[:, 2] + (pos_bboxes[:, 2] - pos_bboxes[:, 0]) / 2
        y2 = pos_bboxes[:, 3] + (pos_bboxes[:, 3] - pos_bboxes[:, 1]) / 2
        pos_bboxes = torch.stack([x1, y1, x2, y2], dim=-1)
        pos_bbox_ws = (pos_bboxes[:, 2] - pos_bboxes[:, 0]).unsqueeze(-1)
        pos_bbox_hs = (pos_bboxes[:, 3] - pos_bboxes[:, 1]).unsqueeze(-1)
        num_rois = pos_bboxes.shape[0]
        map_size = self.whole_map_size
        targets = torch.zeros((num_rois, self.grid_points, map_size, map_size), dtype=torch.float)
        factors = []
        for j in range(self.grid_points):
            x_idx = j // self.grid_size
            y_idx = j % self.grid_size
            factors.append((1 - x_idx / (self.grid_size - 1), 1 - y_idx / (self.grid_size - 1)))
        radius = rcnn_train_cfg.pos_radius
        radius2 = radius ** 2
        for i in range(num_rois):
            if pos_bbox_ws[i] <= self.grid_size or pos_bbox_hs[i] <= self.grid_size:
                continue
            for j in range(self.grid_points):
                factor_x, factor_y = factors[j]
                gridpoint_x = factor_x * pos_gt_bboxes[i, 0] + (1 - factor_x) * pos_gt_bboxes[i, 2]
                gridpoint_y = factor_y * pos_gt_bboxes[i, 1] + (1 - factor_y) * pos_gt_bboxes[i, 3]
                cx = int((gridpoint_x - pos_bboxes[i, 0]) / pos_bbox_ws[i] * map_size)
                cy = int((gridpoint_y - pos_bboxes[i, 1]) / pos_bbox_hs[i] * map_size)
                for x in range(cx - radius, cx + radius + 1):
                    for y in range(cy - radius, cy + radius + 1):
                        if x >= 0 and x < map_size and (y >= 0) and (y < map_size):
                            if (x - cx) ** 2 + (y - cy) ** 2 <= radius2:
                                targets[i, j, y, x] = 1
        sub_targets = []
        for i in range(self.grid_points):
            sub_x1, sub_y1, sub_x2, sub_y2 = self.sub_regions[i]
            sub_targets.append(targets[:, [i], sub_y1:sub_y2, sub_x1:sub_x2])
        sub_targets = torch.cat(sub_targets, dim=1)
        sub_targets = sub_targets.to(sampling_results[0].pos_bboxes.device)
        return sub_targets

    def loss(self, grid_pred, grid_targets):
        loss_fused = self.loss_grid(grid_pred['fused'], grid_targets)
        loss_unfused = self.loss_grid(grid_pred['unfused'], grid_targets)
        loss_grid = loss_fused + loss_unfused
        return dict(loss_grid=loss_grid)

    def get_bboxes(self, det_bboxes, grid_pred, img_metas):
        assert det_bboxes.shape[0] == grid_pred.shape[0]
        det_bboxes = det_bboxes.cpu()
        cls_scores = det_bboxes[:, [4]]
        det_bboxes = det_bboxes[:, :4]
        grid_pred = grid_pred.sigmoid().cpu()
        R, c, h, w = grid_pred.shape
        half_size = self.whole_map_size // 4 * 2
        assert h == w == half_size
        assert c == self.grid_points
        grid_pred = grid_pred.view(R * c, h * w)
        pred_scores, pred_position = grid_pred.max(dim=1)
        xs = pred_position % w
        ys = pred_position // w
        for i in range(self.grid_points):
            xs[i::self.grid_points] += self.sub_regions[i][0]
            ys[i::self.grid_points] += self.sub_regions[i][1]
        pred_scores, xs, ys = tuple(map(lambda x: x.view(R, c), [pred_scores, xs, ys]))
        widths = (det_bboxes[:, 2] - det_bboxes[:, 0]).unsqueeze(-1)
        heights = (det_bboxes[:, 3] - det_bboxes[:, 1]).unsqueeze(-1)
        x1 = det_bboxes[:, 0, None] - widths / 2
        y1 = det_bboxes[:, 1, None] - heights / 2
        abs_xs = (xs.float() + 0.5) / w * widths + x1
        abs_ys = (ys.float() + 0.5) / h * heights + y1
        x1_inds = [i for i in range(self.grid_size)]
        y1_inds = [i * self.grid_size for i in range(self.grid_size)]
        x2_inds = [self.grid_points - self.grid_size + i for i in range(self.grid_size)]
        y2_inds = [(i + 1) * self.grid_size - 1 for i in range(self.grid_size)]
        bboxes_x1 = (abs_xs[:, x1_inds] * pred_scores[:, x1_inds]).sum(dim=1, keepdim=True) / pred_scores[:, x1_inds].sum(dim=1, keepdim=True)
        bboxes_y1 = (abs_ys[:, y1_inds] * pred_scores[:, y1_inds]).sum(dim=1, keepdim=True) / pred_scores[:, y1_inds].sum(dim=1, keepdim=True)
        bboxes_x2 = (abs_xs[:, x2_inds] * pred_scores[:, x2_inds]).sum(dim=1, keepdim=True) / pred_scores[:, x2_inds].sum(dim=1, keepdim=True)
        bboxes_y2 = (abs_ys[:, y2_inds] * pred_scores[:, y2_inds]).sum(dim=1, keepdim=True) / pred_scores[:, y2_inds].sum(dim=1, keepdim=True)
        bbox_res = torch.cat([bboxes_x1, bboxes_y1, bboxes_x2, bboxes_y2, cls_scores], dim=1)
        bbox_res[:, [0, 2]].clamp_(min=0, max=img_metas[0]['img_shape'][1])
        bbox_res[:, [1, 3]].clamp_(min=0, max=img_metas[0]['img_shape'][0])
        return bbox_res

def forward(self, x):
    assert x.shape[-1] == x.shape[-2] == self.roi_feat_size
    x = self.convs(x)
    c = self.point_feat_channels
    x_fo = [None for _ in range(self.grid_points)]
    for i, points in enumerate(self.neighbor_points):
        x_fo[i] = x[:, i * c:(i + 1) * c]
        for j, point_idx in enumerate(points):
            x_fo[i] = x_fo[i] + self.forder_trans[i][j](x[:, point_idx * c:(point_idx + 1) * c])
    x_so = [None for _ in range(self.grid_points)]
    for i, points in enumerate(self.neighbor_points):
        x_so[i] = x[:, i * c:(i + 1) * c]
        for j, point_idx in enumerate(points):
            x_so[i] = x_so[i] + self.sorder_trans[i][j](x_fo[point_idx])
    x2 = torch.cat(x_so, dim=1)
    x2 = self.deconv1(x2)
    x2 = F.relu(self.norm1(x2), inplace=True)
    heatmap = self.deconv2(x2)
    if self.training:
        x1 = x
        x1 = self.deconv1(x1)
        x1 = F.relu(self.norm1(x1), inplace=True)
        heatmap_unfused = self.deconv2(x1)
    else:
        heatmap_unfused = heatmap
    return dict(fused=heatmap, unfused=heatmap_unfused)

class DetectionBlock(BaseModule):
    """Detection block in YOLO neck.

    Let out_channels = n, the DetectionBlock contains:
    Six ConvLayers, 1 Conv2D Layer and 1 YoloLayer.
    The first 6 ConvLayers are formed the following way:
        1x1xn, 3x3x2n, 1x1xn, 3x3x2n, 1x1xn, 3x3x2n.
    The Conv2D layer is 1x1x255.
    Some block will have branch after the fifth ConvLayer.
    The input channel is arbitrary (in_channels)

    Args:
        in_channels (int): The number of input channels.
        out_channels (int): The number of output channels.
        conv_cfg (dict): Config dict for convolution layer. Default: None.
        norm_cfg (dict): Dictionary to construct and config norm layer.
            Default: dict(type='BN', requires_grad=True)
        act_cfg (dict): Config dict for activation layer.
            Default: dict(type='LeakyReLU', negative_slope=0.1).
        init_cfg (dict or list[dict], optional): Initialization config dict.
            Default: None
    """

    def __init__(self, in_channels, out_channels, conv_cfg=None, norm_cfg=dict(type='BN', requires_grad=True), act_cfg=dict(type='LeakyReLU', negative_slope=0.1), init_cfg=None):
        super(DetectionBlock, self).__init__(init_cfg)
        double_out_channels = out_channels * 2
        cfg = dict(conv_cfg=conv_cfg, norm_cfg=norm_cfg, act_cfg=act_cfg)
        self.conv1 = ConvModule(in_channels, out_channels, 1, **cfg)
        self.conv2 = ConvModule(out_channels, double_out_channels, 3, padding=1, **cfg)
        self.conv3 = ConvModule(double_out_channels, out_channels, 1, **cfg)
        self.conv4 = ConvModule(out_channels, double_out_channels, 3, padding=1, **cfg)
        self.conv5 = ConvModule(double_out_channels, out_channels, 1, **cfg)

    def forward(self, x):
        tmp = self.conv1(x)
        tmp = self.conv2(tmp)
        tmp = self.conv3(tmp)
        tmp = self.conv4(tmp)
        out = self.conv5(tmp)
        return out

def forward(self, x):
    tmp = self.conv1(x)
    tmp = self.conv2(tmp)
    tmp = self.conv3(tmp)
    tmp = self.conv4(tmp)
    out = self.conv5(tmp)
    return out

@NECKS.register_module()
class NASFPN(BaseModule):
    """NAS-FPN.

    Implementation of `NAS-FPN: Learning Scalable Feature Pyramid Architecture
    for Object Detection <https://arxiv.org/abs/1904.07392>`_

    Args:
        in_channels (List[int]): Number of input channels per scale.
        out_channels (int): Number of output channels (used at each scale)
        num_outs (int): Number of output scales.
        stack_times (int): The number of times the pyramid architecture will
            be stacked.
        start_level (int): Index of the start input backbone level used to
            build the feature pyramid. Default: 0.
        end_level (int): Index of the end input backbone level (exclusive) to
            build the feature pyramid. Default: -1, which means the last level.
        add_extra_convs (bool): It decides whether to add conv
            layers on top of the original feature maps. Default to False.
            If True, its actual mode is specified by `extra_convs_on_inputs`.
        init_cfg (dict or list[dict], optional): Initialization config dict.
    """

    def __init__(self, in_channels, out_channels, num_outs, stack_times, start_level=0, end_level=-1, add_extra_convs=False, norm_cfg=None, init_cfg=dict(type='Caffe2Xavier', layer='Conv2d')):
        super(NASFPN, self).__init__(init_cfg)
        assert isinstance(in_channels, list)
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.num_ins = len(in_channels)
        self.num_outs = num_outs
        self.stack_times = stack_times
        self.norm_cfg = norm_cfg
        if end_level == -1 or end_level == self.num_ins - 1:
            self.backbone_end_level = self.num_ins
            assert num_outs >= self.num_ins - start_level
        else:
            self.backbone_end_level = end_level + 1
            assert end_level < self.num_ins
            assert num_outs == end_level - start_level + 1
        self.start_level = start_level
        self.end_level = end_level
        self.add_extra_convs = add_extra_convs
        self.lateral_convs = nn.ModuleList()
        for i in range(self.start_level, self.backbone_end_level):
            l_conv = ConvModule(in_channels[i], out_channels, 1, norm_cfg=norm_cfg, act_cfg=None)
            self.lateral_convs.append(l_conv)
        extra_levels = num_outs - self.backbone_end_level + self.start_level
        self.extra_downsamples = nn.ModuleList()
        for i in range(extra_levels):
            extra_conv = ConvModule(out_channels, out_channels, 1, norm_cfg=norm_cfg, act_cfg=None)
            self.extra_downsamples.append(nn.Sequential(extra_conv, nn.MaxPool2d(2, 2)))
        self.fpn_stages = ModuleList()
        for _ in range(self.stack_times):
            stage = nn.ModuleDict()
            stage['gp_64_4'] = GlobalPoolingCell(in_channels=out_channels, out_channels=out_channels, out_norm_cfg=norm_cfg)
            stage['sum_44_4'] = SumCell(in_channels=out_channels, out_channels=out_channels, out_norm_cfg=norm_cfg)
            stage['sum_43_3'] = SumCell(in_channels=out_channels, out_channels=out_channels, out_norm_cfg=norm_cfg)
            stage['sum_34_4'] = SumCell(in_channels=out_channels, out_channels=out_channels, out_norm_cfg=norm_cfg)
            stage['gp_43_5'] = GlobalPoolingCell(with_out_conv=False)
            stage['sum_55_5'] = SumCell(in_channels=out_channels, out_channels=out_channels, out_norm_cfg=norm_cfg)
            stage['gp_54_7'] = GlobalPoolingCell(with_out_conv=False)
            stage['sum_77_7'] = SumCell(in_channels=out_channels, out_channels=out_channels, out_norm_cfg=norm_cfg)
            stage['gp_75_6'] = GlobalPoolingCell(in_channels=out_channels, out_channels=out_channels, out_norm_cfg=norm_cfg)
            self.fpn_stages.append(stage)

    def forward(self, inputs):
        """Forward function."""
        feats = [lateral_conv(inputs[i + self.start_level]) for i, lateral_conv in enumerate(self.lateral_convs)]
        for downsample in self.extra_downsamples:
            feats.append(downsample(feats[-1]))
        p3, p4, p5, p6, p7 = feats
        for stage in self.fpn_stages:
            p4_1 = stage['gp_64_4'](p6, p4, out_size=p4.shape[-2:])
            p4_2 = stage['sum_44_4'](p4_1, p4, out_size=p4.shape[-2:])
            p3 = stage['sum_43_3'](p4_2, p3, out_size=p3.shape[-2:])
            p4 = stage['sum_34_4'](p3, p4_2, out_size=p4.shape[-2:])
            p5_tmp = stage['gp_43_5'](p4, p3, out_size=p5.shape[-2:])
            p5 = stage['sum_55_5'](p5, p5_tmp, out_size=p5.shape[-2:])
            p7_tmp = stage['gp_54_7'](p5, p4_2, out_size=p7.shape[-2:])
            p7 = stage['sum_77_7'](p7, p7_tmp, out_size=p7.shape[-2:])
            p6 = stage['gp_75_6'](p7, p5, out_size=p6.shape[-2:])
        return (p3, p4, p5, p6, p7)

def forward(self, inputs):
    """Forward function."""
    feats = [lateral_conv(inputs[i + self.start_level]) for i, lateral_conv in enumerate(self.lateral_convs)]
    for downsample in self.extra_downsamples:
        feats.append(downsample(feats[-1]))
    p3, p4, p5, p6, p7 = feats
    for stage in self.fpn_stages:
        p4_1 = stage['gp_64_4'](p6, p4, out_size=p4.shape[-2:])
        p4_2 = stage['sum_44_4'](p4_1, p4, out_size=p4.shape[-2:])
        p3 = stage['sum_43_3'](p4_2, p3, out_size=p3.shape[-2:])
        p4 = stage['sum_34_4'](p3, p4_2, out_size=p4.shape[-2:])
        p5_tmp = stage['gp_43_5'](p4, p3, out_size=p5.shape[-2:])
        p5 = stage['sum_55_5'](p5, p5_tmp, out_size=p5.shape[-2:])
        p7_tmp = stage['gp_54_7'](p5, p4_2, out_size=p7.shape[-2:])
        p7 = stage['sum_77_7'](p7, p7_tmp, out_size=p7.shape[-2:])
        p6 = stage['gp_75_6'](p7, p5, out_size=p6.shape[-2:])
    return (p3, p4, p5, p6, p7)

@NECKS.register_module()
class HRFPN(BaseModule):
    """HRFPN (High Resolution Feature Pyramids)

    paper: `High-Resolution Representations for Labeling Pixels and Regions
    <https://arxiv.org/abs/1904.04514>`_.

    Args:
        in_channels (list): number of channels for each branch.
        out_channels (int): output channels of feature pyramids.
        num_outs (int): number of output stages.
        pooling_type (str): pooling for generating feature pyramids
            from {MAX, AVG}.
        conv_cfg (dict): dictionary to construct and config conv layer.
        norm_cfg (dict): dictionary to construct and config norm layer.
        with_cp  (bool): Use checkpoint or not. Using checkpoint will save some
            memory while slowing down the training speed.
        stride (int): stride of 3x3 convolutional layers
        init_cfg (dict or list[dict], optional): Initialization config dict.
    """

    def __init__(self, in_channels, out_channels, num_outs=5, pooling_type='AVG', conv_cfg=None, norm_cfg=None, with_cp=False, stride=1, init_cfg=dict(type='Caffe2Xavier', layer='Conv2d')):
        super(HRFPN, self).__init__(init_cfg)
        assert isinstance(in_channels, list)
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.num_ins = len(in_channels)
        self.num_outs = num_outs
        self.with_cp = with_cp
        self.conv_cfg = conv_cfg
        self.norm_cfg = norm_cfg
        self.reduction_conv = ConvModule(sum(in_channels), out_channels, kernel_size=1, conv_cfg=self.conv_cfg, act_cfg=None)
        self.fpn_convs = nn.ModuleList()
        for i in range(self.num_outs):
            self.fpn_convs.append(ConvModule(out_channels, out_channels, kernel_size=3, padding=1, stride=stride, conv_cfg=self.conv_cfg, act_cfg=None))
        if pooling_type == 'MAX':
            self.pooling = F.max_pool2d
        else:
            self.pooling = F.avg_pool2d

    def forward(self, inputs):
        """Forward function."""
        assert len(inputs) == self.num_ins
        outs = [inputs[0]]
        for i in range(1, self.num_ins):
            outs.append(F.interpolate(inputs[i], scale_factor=2 ** i, mode='bilinear'))
        out = torch.cat(outs, dim=1)
        if out.requires_grad and self.with_cp:
            out = checkpoint(self.reduction_conv, out)
        else:
            out = self.reduction_conv(out)
        outs = [out]
        for i in range(1, self.num_outs):
            outs.append(self.pooling(out, kernel_size=2 ** i, stride=2 ** i))
        outputs = []
        for i in range(self.num_outs):
            if outs[i].requires_grad and self.with_cp:
                tmp_out = checkpoint(self.fpn_convs[i], outs[i])
            else:
                tmp_out = self.fpn_convs[i](outs[i])
            outputs.append(tmp_out)
        return tuple(outputs)

def forward(self, inputs):
    """Forward function."""
    assert len(inputs) == self.num_ins
    outs = [inputs[0]]
    for i in range(1, self.num_ins):
        outs.append(F.interpolate(inputs[i], scale_factor=2 ** i, mode='bilinear'))
    out = torch.cat(outs, dim=1)
    if out.requires_grad and self.with_cp:
        out = checkpoint(self.reduction_conv, out)
    else:
        out = self.reduction_conv(out)
    outs = [out]
    for i in range(1, self.num_outs):
        outs.append(self.pooling(out, kernel_size=2 ** i, stride=2 ** i))
    outputs = []
    for i in range(self.num_outs):
        if outs[i].requires_grad and self.with_cp:
            tmp_out = checkpoint(self.fpn_convs[i], outs[i])
        else:
            tmp_out = self.fpn_convs[i](outs[i])
        outputs.append(tmp_out)
    return tuple(outputs)

class UpInterpolationConv(Transition):
    """A transition used for up-sampling.

    Up-sample the input by interpolation then refines the feature by
    a convolution layer.

    Args:
        in_channels (int): Number of input channels.
        out_channels (int): Number of output channels.
        scale_factor (int): Up-sampling factor. Default: 2.
        mode (int): Interpolation mode. Default: nearest.
        align_corners (bool): Whether align corners when interpolation.
            Default: None.
        kernel_size (int): Kernel size for the conv. Default: 3.
    """

    def __init__(self, in_channels, out_channels, scale_factor=2, mode='nearest', align_corners=None, kernel_size=3, init_cfg=None, **kwargs):
        super().__init__(in_channels, out_channels, init_cfg)
        self.mode = mode
        self.scale_factor = scale_factor
        self.align_corners = align_corners
        self.conv = ConvModule(in_channels, out_channels, kernel_size, padding=(kernel_size - 1) // 2, **kwargs)

    def forward(self, x):
        x = F.interpolate(x, scale_factor=self.scale_factor, mode=self.mode, align_corners=self.align_corners)
        x = self.conv(x)
        return x

def forward(self, x):
    x = F.interpolate(x, scale_factor=self.scale_factor, mode=self.mode, align_corners=self.align_corners)
    x = self.conv(x)
    return x

@NECKS.register_module()
class FPG(BaseModule):
    """FPG.

    Implementation of `Feature Pyramid Grids (FPG)
    <https://arxiv.org/abs/2004.03580>`_.
    This implementation only gives the basic structure stated in the paper.
    But users can implement different type of transitions to fully explore the
    the potential power of the structure of FPG.

    Args:
        in_channels (int): Number of input channels (feature maps of all levels
            should have the same channels).
        out_channels (int): Number of output channels (used at each scale)
        num_outs (int): Number of output scales.
        stack_times (int): The number of times the pyramid architecture will
            be stacked.
        paths (list[str]): Specify the path order of each stack level.
            Each element in the list should be either 'bu' (bottom-up) or
            'td' (top-down).
        inter_channels (int): Number of inter channels.
        same_up_trans (dict): Transition that goes down at the same stage.
        same_down_trans (dict): Transition that goes up at the same stage.
        across_lateral_trans (dict): Across-pathway same-stage
        across_down_trans (dict): Across-pathway bottom-up connection.
        across_up_trans (dict): Across-pathway top-down connection.
        across_skip_trans (dict): Across-pathway skip connection.
        output_trans (dict): Transition that trans the output of the
            last stage.
        start_level (int): Index of the start input backbone level used to
            build the feature pyramid. Default: 0.
        end_level (int): Index of the end input backbone level (exclusive) to
            build the feature pyramid. Default: -1, which means the last level.
        add_extra_convs (bool): It decides whether to add conv
            layers on top of the original feature maps. Default to False.
            If True, its actual mode is specified by `extra_convs_on_inputs`.
        norm_cfg (dict): Config dict for normalization layer. Default: None.
        init_cfg (dict or list[dict], optional): Initialization config dict.
    """
    transition_types = {'conv': ConvModule, 'interpolation_conv': UpInterpolationConv, 'last_conv': LastConv}

    def __init__(self, in_channels, out_channels, num_outs, stack_times, paths, inter_channels=None, same_down_trans=None, same_up_trans=dict(type='conv', kernel_size=3, stride=2, padding=1), across_lateral_trans=dict(type='conv', kernel_size=1), across_down_trans=dict(type='conv', kernel_size=3), across_up_trans=None, across_skip_trans=dict(type='identity'), output_trans=dict(type='last_conv', kernel_size=3), start_level=0, end_level=-1, add_extra_convs=False, norm_cfg=None, skip_inds=None, init_cfg=[dict(type='Caffe2Xavier', layer='Conv2d'), dict(type='Constant', layer=['_BatchNorm', '_InstanceNorm', 'GroupNorm', 'LayerNorm'], val=1.0)]):
        super(FPG, self).__init__(init_cfg)
        assert isinstance(in_channels, list)
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.num_ins = len(in_channels)
        self.num_outs = num_outs
        if inter_channels is None:
            self.inter_channels = [out_channels for _ in range(num_outs)]
        elif isinstance(inter_channels, int):
            self.inter_channels = [inter_channels for _ in range(num_outs)]
        else:
            assert isinstance(inter_channels, list)
            assert len(inter_channels) == num_outs
            self.inter_channels = inter_channels
        self.stack_times = stack_times
        self.paths = paths
        assert isinstance(paths, list) and len(paths) == stack_times
        for d in paths:
            assert d in ('bu', 'td')
        self.same_down_trans = same_down_trans
        self.same_up_trans = same_up_trans
        self.across_lateral_trans = across_lateral_trans
        self.across_down_trans = across_down_trans
        self.across_up_trans = across_up_trans
        self.output_trans = output_trans
        self.across_skip_trans = across_skip_trans
        self.with_bias = norm_cfg is None
        if self.across_skip_trans is not None:
            skip_inds is not None
        self.skip_inds = skip_inds
        assert len(self.skip_inds[0]) <= self.stack_times
        if end_level == -1 or end_level == self.num_ins - 1:
            self.backbone_end_level = self.num_ins
            assert num_outs >= self.num_ins - start_level
        else:
            self.backbone_end_level = end_level + 1
            assert end_level < self.num_ins
            assert num_outs == end_level - start_level + 1
        self.start_level = start_level
        self.end_level = end_level
        self.add_extra_convs = add_extra_convs
        self.lateral_convs = nn.ModuleList()
        for i in range(self.start_level, self.backbone_end_level):
            l_conv = nn.Conv2d(self.in_channels[i], self.inter_channels[i - self.start_level], 1)
            self.lateral_convs.append(l_conv)
        extra_levels = num_outs - self.backbone_end_level + self.start_level
        self.extra_downsamples = nn.ModuleList()
        for i in range(extra_levels):
            if self.add_extra_convs:
                fpn_idx = self.backbone_end_level - self.start_level + i
                extra_conv = nn.Conv2d(self.inter_channels[fpn_idx - 1], self.inter_channels[fpn_idx], 3, stride=2, padding=1)
                self.extra_downsamples.append(extra_conv)
            else:
                self.extra_downsamples.append(nn.MaxPool2d(1, stride=2))
        self.fpn_transitions = nn.ModuleList()
        for s in range(self.stack_times):
            stage_trans = nn.ModuleList()
            for i in range(self.num_outs):
                trans = nn.ModuleDict()
                if s in self.skip_inds[i]:
                    stage_trans.append(trans)
                    continue
                if i == 0 or self.same_up_trans is None:
                    same_up_trans = None
                else:
                    same_up_trans = self.build_trans(self.same_up_trans, self.inter_channels[i - 1], self.inter_channels[i])
                trans['same_up'] = same_up_trans
                if i == self.num_outs - 1 or self.same_down_trans is None:
                    same_down_trans = None
                else:
                    same_down_trans = self.build_trans(self.same_down_trans, self.inter_channels[i + 1], self.inter_channels[i])
                trans['same_down'] = same_down_trans
                across_lateral_trans = self.build_trans(self.across_lateral_trans, self.inter_channels[i], self.inter_channels[i])
                trans['across_lateral'] = across_lateral_trans
                if i == self.num_outs - 1 or self.across_down_trans is None:
                    across_down_trans = None
                else:
                    across_down_trans = self.build_trans(self.across_down_trans, self.inter_channels[i + 1], self.inter_channels[i])
                trans['across_down'] = across_down_trans
                if i == 0 or self.across_up_trans is None:
                    across_up_trans = None
                else:
                    across_up_trans = self.build_trans(self.across_up_trans, self.inter_channels[i - 1], self.inter_channels[i])
                trans['across_up'] = across_up_trans
                if self.across_skip_trans is None:
                    across_skip_trans = None
                else:
                    across_skip_trans = self.build_trans(self.across_skip_trans, self.inter_channels[i - 1], self.inter_channels[i])
                trans['across_skip'] = across_skip_trans
                stage_trans.append(trans)
            self.fpn_transitions.append(stage_trans)
        self.output_transition = nn.ModuleList()
        for i in range(self.num_outs):
            trans = self.build_trans(self.output_trans, self.inter_channels[i], self.out_channels, num_inputs=self.stack_times + 1)
            self.output_transition.append(trans)
        self.relu = nn.ReLU(inplace=True)

    def build_trans(self, cfg, in_channels, out_channels, **extra_args):
        cfg_ = cfg.copy()
        trans_type = cfg_.pop('type')
        trans_cls = self.transition_types[trans_type]
        return trans_cls(in_channels, out_channels, **cfg_, **extra_args)

    def fuse(self, fuse_dict):
        out = None
        for item in fuse_dict.values():
            if item is not None:
                if out is None:
                    out = item
                else:
                    out = out + item
        return out

    def forward(self, inputs):
        assert len(inputs) == len(self.in_channels)
        feats = [lateral_conv(inputs[i + self.start_level]) for i, lateral_conv in enumerate(self.lateral_convs)]
        for downsample in self.extra_downsamples:
            feats.append(downsample(feats[-1]))
        outs = [feats]
        for i in range(self.stack_times):
            current_outs = outs[-1]
            next_outs = []
            direction = self.paths[i]
            for j in range(self.num_outs):
                if i in self.skip_inds[j]:
                    next_outs.append(outs[-1][j])
                    continue
                if direction == 'td':
                    lvl = self.num_outs - j - 1
                else:
                    lvl = j
                if direction == 'td':
                    same_trans = self.fpn_transitions[i][lvl]['same_down']
                else:
                    same_trans = self.fpn_transitions[i][lvl]['same_up']
                across_lateral_trans = self.fpn_transitions[i][lvl]['across_lateral']
                across_down_trans = self.fpn_transitions[i][lvl]['across_down']
                across_up_trans = self.fpn_transitions[i][lvl]['across_up']
                across_skip_trans = self.fpn_transitions[i][lvl]['across_skip']
                to_fuse = dict(same=None, lateral=None, across_up=None, across_down=None)
                if same_trans is not None:
                    to_fuse['same'] = same_trans(next_outs[-1])
                if across_lateral_trans is not None:
                    to_fuse['lateral'] = across_lateral_trans(current_outs[lvl])
                if lvl > 0 and across_up_trans is not None:
                    to_fuse['across_up'] = across_up_trans(current_outs[lvl - 1])
                if lvl < self.num_outs - 1 and across_down_trans is not None:
                    to_fuse['across_down'] = across_down_trans(current_outs[lvl + 1])
                if across_skip_trans is not None:
                    to_fuse['across_skip'] = across_skip_trans(outs[0][lvl])
                x = self.fuse(to_fuse)
                next_outs.append(x)
            if direction == 'td':
                outs.append(next_outs[::-1])
            else:
                outs.append(next_outs)
        final_outs = []
        for i in range(self.num_outs):
            lvl_out_list = []
            for s in range(len(outs)):
                lvl_out_list.append(outs[s][i])
            lvl_out = self.output_transition[i](lvl_out_list)
            final_outs.append(lvl_out)
        return final_outs

def forward(self, inputs):
    assert len(inputs) == len(self.in_channels)
    feats = [lateral_conv(inputs[i + self.start_level]) for i, lateral_conv in enumerate(self.lateral_convs)]
    for downsample in self.extra_downsamples:
        feats.append(downsample(feats[-1]))
    outs = [feats]
    for i in range(self.stack_times):
        current_outs = outs[-1]
        next_outs = []
        direction = self.paths[i]
        for j in range(self.num_outs):
            if i in self.skip_inds[j]:
                next_outs.append(outs[-1][j])
                continue
            if direction == 'td':
                lvl = self.num_outs - j - 1
            else:
                lvl = j
            if direction == 'td':
                same_trans = self.fpn_transitions[i][lvl]['same_down']
            else:
                same_trans = self.fpn_transitions[i][lvl]['same_up']
            across_lateral_trans = self.fpn_transitions[i][lvl]['across_lateral']
            across_down_trans = self.fpn_transitions[i][lvl]['across_down']
            across_up_trans = self.fpn_transitions[i][lvl]['across_up']
            across_skip_trans = self.fpn_transitions[i][lvl]['across_skip']
            to_fuse = dict(same=None, lateral=None, across_up=None, across_down=None)
            if same_trans is not None:
                to_fuse['same'] = same_trans(next_outs[-1])
            if across_lateral_trans is not None:
                to_fuse['lateral'] = across_lateral_trans(current_outs[lvl])
            if lvl > 0 and across_up_trans is not None:
                to_fuse['across_up'] = across_up_trans(current_outs[lvl - 1])
            if lvl < self.num_outs - 1 and across_down_trans is not None:
                to_fuse['across_down'] = across_down_trans(current_outs[lvl + 1])
            if across_skip_trans is not None:
                to_fuse['across_skip'] = across_skip_trans(outs[0][lvl])
            x = self.fuse(to_fuse)
            next_outs.append(x)
        if direction == 'td':
            outs.append(next_outs[::-1])
        else:
            outs.append(next_outs)
    final_outs = []
    for i in range(self.num_outs):
        lvl_out_list = []
        for s in range(len(outs)):
            lvl_out_list.append(outs[s][i])
        lvl_out = self.output_transition[i](lvl_out_list)
        final_outs.append(lvl_out)
    return final_outs

class Bottleneck(nn.Module):
    """Bottleneck block for DilatedEncoder used in `YOLOF.

    <https://arxiv.org/abs/2103.09460>`.

    The Bottleneck contains three ConvLayers and one residual connection.

    Args:
        in_channels (int): The number of input channels.
        mid_channels (int): The number of middle output channels.
        dilation (int): Dilation rate.
        norm_cfg (dict): Dictionary to construct and config norm layer.
    """

    def __init__(self, in_channels, mid_channels, dilation, norm_cfg=dict(type='BN', requires_grad=True)):
        super(Bottleneck, self).__init__()
        self.conv1 = ConvModule(in_channels, mid_channels, 1, norm_cfg=norm_cfg)
        self.conv2 = ConvModule(mid_channels, mid_channels, 3, padding=dilation, dilation=dilation, norm_cfg=norm_cfg)
        self.conv3 = ConvModule(mid_channels, in_channels, 1, norm_cfg=norm_cfg)

    def forward(self, x):
        identity = x
        out = self.conv1(x)
        out = self.conv2(out)
        out = self.conv3(out)
        out = out + identity
        return out

def forward(self, x):
    identity = x
    out = self.conv1(x)
    out = self.conv2(out)
    out = self.conv3(out)
    out = out + identity
    return out

class Model(nn.Module):

    def __init__(self):
        super().__init__()
        self.linear = nn.Linear(2, 1)
        self.conv = nn.Conv2d(3, 3, 3)

    def forward(self, x):
        return self.linear(x)

    def train_step(self, x, optimizer, **kwargs):
        return dict(loss=self(x))

    def val_step(self, x, optimizer, **kwargs):
        return dict(loss=self(x))

def forward(self, x):
    return self.linear(x)

class DemoModel(nn.Module):

    def __init__(self):
        super().__init__()
        self.epoch = 0
        self.linear = nn.Linear(2, 1)

    def forward(self, x):
        return self.linear(x)

    def train_step(self, x, optimizer, **kwargs):
        return dict(loss=self(x))

    def set_epoch(self, epoch):
        self.epoch = epoch

def forward(self, x):
    return self.linear(x)

class Model(nn.Module):

    def __init__(self):
        super().__init__()
        self.linear = nn.Linear(2, 1)

    def forward(self, x):
        return self.linear(x)

    def train_step(self, x, optimizer, **kwargs):
        return dict(loss=self(x))

    def val_step(self, x, optimizer, **kwargs):
        return dict(loss=self(x))

def forward(self, x):
    return self.linear(x)

class ConvBlock(nn.Module):
    """Basic convolutional block.
    
    convolution + batch normalization + relu.

    Args:
        in_c (int): number of input channels.
        out_c (int): number of output channels.
        k (int or tuple): kernel size.
        s (int or tuple): stride.
        p (int or tuple): padding.
    """

    def __init__(self, in_c, out_c, k, s=1, p=0):
        super(ConvBlock, self).__init__()
        self.conv = nn.Conv2d(in_c, out_c, k, stride=s, padding=p)
        self.bn = nn.BatchNorm2d(out_c)

    def forward(self, x):
        return F.relu(self.bn(self.conv(x)))

def forward(self, x):
    return F.relu(self.bn(self.conv(x)))

class SpatialAttn(nn.Module):
    """Spatial Attention (Sec. 3.1.I.1)"""

    def __init__(self):
        super(SpatialAttn, self).__init__()
        self.conv1 = ConvBlock(1, 1, 3, s=2, p=1)
        self.conv2 = ConvBlock(1, 1, 1)

    def forward(self, x):
        x = x.mean(1, keepdim=True)
        x = self.conv1(x)
        x = F.upsample(x, (x.size(2) * 2, x.size(3) * 2), mode='bilinear', align_corners=True)
        x = self.conv2(x)
        return x

def forward(self, x):
    x = x.mean(1, keepdim=True)
    x = self.conv1(x)
    x = F.upsample(x, (x.size(2) * 2, x.size(3) * 2), mode='bilinear', align_corners=True)
    x = self.conv2(x)
    return x

class ChannelAttn(nn.Module):
    """Channel Attention (Sec. 3.1.I.2)"""

    def __init__(self, in_channels, reduction_rate=16):
        super(ChannelAttn, self).__init__()
        assert in_channels % reduction_rate == 0
        self.conv1 = ConvBlock(in_channels, in_channels // reduction_rate, 1)
        self.conv2 = ConvBlock(in_channels // reduction_rate, in_channels, 1)

    def forward(self, x):
        x = F.avg_pool2d(x, x.size()[2:])
        x = self.conv1(x)
        x = self.conv2(x)
        return x

def forward(self, x):
    x = F.avg_pool2d(x, x.size()[2:])
    x = self.conv1(x)
    x = self.conv2(x)
    return x

class SoftAttn(nn.Module):
    """Soft Attention (Sec. 3.1.I)
    
    Aim: Spatial Attention + Channel Attention
    
    Output: attention maps with shape identical to input.
    """

    def __init__(self, in_channels):
        super(SoftAttn, self).__init__()
        self.spatial_attn = SpatialAttn()
        self.channel_attn = ChannelAttn(in_channels)
        self.conv = ConvBlock(in_channels, in_channels, 1)

    def forward(self, x):
        y_spatial = self.spatial_attn(x)
        y_channel = self.channel_attn(x)
        y = y_spatial * y_channel
        y = torch.sigmoid(self.conv(y))
        return y

def forward(self, x):
    y_spatial = self.spatial_attn(x)
    y_channel = self.channel_attn(x)
    y = y_spatial * y_channel
    y = torch.sigmoid(self.conv(y))
    return y

class ConvBlock(nn.Module):
    """Basic convolutional block.
    
    convolution + batch normalization + relu.

    Args:
        in_c (int): number of input channels.
        out_c (int): number of output channels.
        k (int or tuple): kernel size.
        s (int or tuple): stride.
        p (int or tuple): padding.
    """

    def __init__(self, in_c, out_c, k, s, p):
        super(ConvBlock, self).__init__()
        self.conv = nn.Conv2d(in_c, out_c, k, stride=s, padding=p)
        self.bn = nn.BatchNorm2d(out_c)

    def forward(self, x):
        return F.relu(self.bn(self.conv(x)))

def forward(self, x):
    return F.relu(self.bn(self.conv(x)))

class ConvLayers(nn.Module):
    """Preprocessing layers."""

    def __init__(self):
        super(ConvLayers, self).__init__()
        self.conv1 = ConvBlock(3, 48, k=3, s=1, p=1)
        self.conv2 = ConvBlock(48, 96, k=3, s=1, p=1)
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)

    def forward(self, x):
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.maxpool(x)
        return x

def forward(self, x):
    x = self.conv1(x)
    x = self.conv2(x)
    x = self.maxpool(x)
    return x

class MuDeep(nn.Module):
    """Multiscale deep neural network.

    Reference:
        Qian et al. Multi-scale Deep Learning Architectures
        for Person Re-identification. ICCV 2017.

    Public keys:
        - ``mudeep``: Multiscale deep neural network.
    """

    def __init__(self, num_classes, loss='softmax', **kwargs):
        super(MuDeep, self).__init__()
        self.loss = loss
        self.block1 = ConvLayers()
        self.block2 = MultiScaleA()
        self.block3 = Reduction()
        self.block4 = MultiScaleB()
        self.block5 = Fusion()
        self.fc = nn.Sequential(nn.Linear(256 * 16 * 8, 4096), nn.BatchNorm1d(4096), nn.ReLU())
        self.classifier = nn.Linear(4096, num_classes)
        self.feat_dim = 4096

    def featuremaps(self, x):
        x = self.block1(x)
        x = self.block2(x)
        x = self.block3(x)
        x = self.block4(x)
        x = self.block5(*x)
        return x

    def forward(self, x):
        x = self.featuremaps(x)
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        y = self.classifier(x)
        if not self.training:
            return x
        if self.loss == 'softmax':
            return y
        elif self.loss == 'triplet':
            return (y, x)
        else:
            raise KeyError('Unsupported loss: {}'.format(self.loss))

def featuremaps(self, x):
    x = self.block1(x)
    x = self.block2(x)
    x = self.block3(x)
    x = self.block4(x)
    x = self.block5(*x)
    return x

class BasicConv2d(nn.Module):

    def __init__(self, in_planes, out_planes, kernel_size, stride, padding=0):
        super(BasicConv2d, self).__init__()
        self.conv = nn.Conv2d(in_planes, out_planes, kernel_size=kernel_size, stride=stride, padding=padding, bias=False)
        self.bn = nn.BatchNorm2d(out_planes, eps=0.001, momentum=0.1, affine=True)
        self.relu = nn.ReLU(inplace=False)

    def forward(self, x):
        x = self.conv(x)
        x = self.bn(x)
        x = self.relu(x)
        return x

def forward(self, x):
    x = self.conv(x)
    x = self.bn(x)
    x = self.relu(x)
    return x

class Mixed_5b(nn.Module):

    def __init__(self):
        super(Mixed_5b, self).__init__()
        self.branch0 = BasicConv2d(192, 96, kernel_size=1, stride=1)
        self.branch1 = nn.Sequential(BasicConv2d(192, 48, kernel_size=1, stride=1), BasicConv2d(48, 64, kernel_size=5, stride=1, padding=2))
        self.branch2 = nn.Sequential(BasicConv2d(192, 64, kernel_size=1, stride=1), BasicConv2d(64, 96, kernel_size=3, stride=1, padding=1), BasicConv2d(96, 96, kernel_size=3, stride=1, padding=1))
        self.branch3 = nn.Sequential(nn.AvgPool2d(3, stride=1, padding=1, count_include_pad=False), BasicConv2d(192, 64, kernel_size=1, stride=1))

    def forward(self, x):
        x0 = self.branch0(x)
        x1 = self.branch1(x)
        x2 = self.branch2(x)
        x3 = self.branch3(x)
        out = torch.cat((x0, x1, x2, x3), 1)
        return out

def forward(self, x):
    x0 = self.branch0(x)
    x1 = self.branch1(x)
    x2 = self.branch2(x)
    x3 = self.branch3(x)
    out = torch.cat((x0, x1, x2, x3), 1)
    return out

class Block35(nn.Module):

    def __init__(self, scale=1.0):
        super(Block35, self).__init__()
        self.scale = scale
        self.branch0 = BasicConv2d(320, 32, kernel_size=1, stride=1)
        self.branch1 = nn.Sequential(BasicConv2d(320, 32, kernel_size=1, stride=1), BasicConv2d(32, 32, kernel_size=3, stride=1, padding=1))
        self.branch2 = nn.Sequential(BasicConv2d(320, 32, kernel_size=1, stride=1), BasicConv2d(32, 48, kernel_size=3, stride=1, padding=1), BasicConv2d(48, 64, kernel_size=3, stride=1, padding=1))
        self.conv2d = nn.Conv2d(128, 320, kernel_size=1, stride=1)
        self.relu = nn.ReLU(inplace=False)

    def forward(self, x):
        x0 = self.branch0(x)
        x1 = self.branch1(x)
        x2 = self.branch2(x)
        out = torch.cat((x0, x1, x2), 1)
        out = self.conv2d(out)
        out = out * self.scale + x
        out = self.relu(out)
        return out

def forward(self, x):
    x0 = self.branch0(x)
    x1 = self.branch1(x)
    x2 = self.branch2(x)
    out = torch.cat((x0, x1, x2), 1)
    out = self.conv2d(out)
    out = out * self.scale + x
    out = self.relu(out)
    return out

class Mixed_6a(nn.Module):

    def __init__(self):
        super(Mixed_6a, self).__init__()
        self.branch0 = BasicConv2d(320, 384, kernel_size=3, stride=2)
        self.branch1 = nn.Sequential(BasicConv2d(320, 256, kernel_size=1, stride=1), BasicConv2d(256, 256, kernel_size=3, stride=1, padding=1), BasicConv2d(256, 384, kernel_size=3, stride=2))
        self.branch2 = nn.MaxPool2d(3, stride=2)

    def forward(self, x):
        x0 = self.branch0(x)
        x1 = self.branch1(x)
        x2 = self.branch2(x)
        out = torch.cat((x0, x1, x2), 1)
        return out

def forward(self, x):
    x0 = self.branch0(x)
    x1 = self.branch1(x)
    x2 = self.branch2(x)
    out = torch.cat((x0, x1, x2), 1)
    return out

class Block17(nn.Module):

    def __init__(self, scale=1.0):
        super(Block17, self).__init__()
        self.scale = scale
        self.branch0 = BasicConv2d(1088, 192, kernel_size=1, stride=1)
        self.branch1 = nn.Sequential(BasicConv2d(1088, 128, kernel_size=1, stride=1), BasicConv2d(128, 160, kernel_size=(1, 7), stride=1, padding=(0, 3)), BasicConv2d(160, 192, kernel_size=(7, 1), stride=1, padding=(3, 0)))
        self.conv2d = nn.Conv2d(384, 1088, kernel_size=1, stride=1)
        self.relu = nn.ReLU(inplace=False)

    def forward(self, x):
        x0 = self.branch0(x)
        x1 = self.branch1(x)
        out = torch.cat((x0, x1), 1)
        out = self.conv2d(out)
        out = out * self.scale + x
        out = self.relu(out)
        return out

def forward(self, x):
    x0 = self.branch0(x)
    x1 = self.branch1(x)
    out = torch.cat((x0, x1), 1)
    out = self.conv2d(out)
    out = out * self.scale + x
    out = self.relu(out)
    return out

class Mixed_7a(nn.Module):

    def __init__(self):
        super(Mixed_7a, self).__init__()
        self.branch0 = nn.Sequential(BasicConv2d(1088, 256, kernel_size=1, stride=1), BasicConv2d(256, 384, kernel_size=3, stride=2))
        self.branch1 = nn.Sequential(BasicConv2d(1088, 256, kernel_size=1, stride=1), BasicConv2d(256, 288, kernel_size=3, stride=2))
        self.branch2 = nn.Sequential(BasicConv2d(1088, 256, kernel_size=1, stride=1), BasicConv2d(256, 288, kernel_size=3, stride=1, padding=1), BasicConv2d(288, 320, kernel_size=3, stride=2))
        self.branch3 = nn.MaxPool2d(3, stride=2)

    def forward(self, x):
        x0 = self.branch0(x)
        x1 = self.branch1(x)
        x2 = self.branch2(x)
        x3 = self.branch3(x)
        out = torch.cat((x0, x1, x2, x3), 1)
        return out

def forward(self, x):
    x0 = self.branch0(x)
    x1 = self.branch1(x)
    x2 = self.branch2(x)
    x3 = self.branch3(x)
    out = torch.cat((x0, x1, x2, x3), 1)
    return out

class Block8(nn.Module):

    def __init__(self, scale=1.0, noReLU=False):
        super(Block8, self).__init__()
        self.scale = scale
        self.noReLU = noReLU
        self.branch0 = BasicConv2d(2080, 192, kernel_size=1, stride=1)
        self.branch1 = nn.Sequential(BasicConv2d(2080, 192, kernel_size=1, stride=1), BasicConv2d(192, 224, kernel_size=(1, 3), stride=1, padding=(0, 1)), BasicConv2d(224, 256, kernel_size=(3, 1), stride=1, padding=(1, 0)))
        self.conv2d = nn.Conv2d(448, 2080, kernel_size=1, stride=1)
        if not self.noReLU:
            self.relu = nn.ReLU(inplace=False)

    def forward(self, x):
        x0 = self.branch0(x)
        x1 = self.branch1(x)
        out = torch.cat((x0, x1), 1)
        out = self.conv2d(out)
        out = out * self.scale + x
        if not self.noReLU:
            out = self.relu(out)
        return out

def forward(self, x):
    x0 = self.branch0(x)
    x1 = self.branch1(x)
    out = torch.cat((x0, x1), 1)
    out = self.conv2d(out)
    out = out * self.scale + x
    if not self.noReLU:
        out = self.relu(out)
    return out

class InceptionResNetV2(nn.Module):
    """Inception-ResNet-V2.

    Reference:
        Szegedy et al. Inception-v4, Inception-ResNet and the Impact of Residual
        Connections on Learning. AAAI 2017.

    Public keys:
        - ``inceptionresnetv2``: Inception-ResNet-V2.
    """

    def __init__(self, num_classes, loss='softmax', **kwargs):
        super(InceptionResNetV2, self).__init__()
        self.loss = loss
        self.conv2d_1a = BasicConv2d(3, 32, kernel_size=3, stride=2)
        self.conv2d_2a = BasicConv2d(32, 32, kernel_size=3, stride=1)
        self.conv2d_2b = BasicConv2d(32, 64, kernel_size=3, stride=1, padding=1)
        self.maxpool_3a = nn.MaxPool2d(3, stride=2)
        self.conv2d_3b = BasicConv2d(64, 80, kernel_size=1, stride=1)
        self.conv2d_4a = BasicConv2d(80, 192, kernel_size=3, stride=1)
        self.maxpool_5a = nn.MaxPool2d(3, stride=2)
        self.mixed_5b = Mixed_5b()
        self.repeat = nn.Sequential(Block35(scale=0.17), Block35(scale=0.17), Block35(scale=0.17), Block35(scale=0.17), Block35(scale=0.17), Block35(scale=0.17), Block35(scale=0.17), Block35(scale=0.17), Block35(scale=0.17), Block35(scale=0.17))
        self.mixed_6a = Mixed_6a()
        self.repeat_1 = nn.Sequential(Block17(scale=0.1), Block17(scale=0.1), Block17(scale=0.1), Block17(scale=0.1), Block17(scale=0.1), Block17(scale=0.1), Block17(scale=0.1), Block17(scale=0.1), Block17(scale=0.1), Block17(scale=0.1), Block17(scale=0.1), Block17(scale=0.1), Block17(scale=0.1), Block17(scale=0.1), Block17(scale=0.1), Block17(scale=0.1), Block17(scale=0.1), Block17(scale=0.1), Block17(scale=0.1), Block17(scale=0.1))
        self.mixed_7a = Mixed_7a()
        self.repeat_2 = nn.Sequential(Block8(scale=0.2), Block8(scale=0.2), Block8(scale=0.2), Block8(scale=0.2), Block8(scale=0.2), Block8(scale=0.2), Block8(scale=0.2), Block8(scale=0.2), Block8(scale=0.2))
        self.block8 = Block8(noReLU=True)
        self.conv2d_7b = BasicConv2d(2080, 1536, kernel_size=1, stride=1)
        self.global_avgpool = nn.AdaptiveAvgPool2d(1)
        self.classifier = nn.Linear(1536, num_classes)

    def load_imagenet_weights(self):
        settings = pretrained_settings['inceptionresnetv2']['imagenet']
        pretrain_dict = model_zoo.load_url(settings['url'])
        model_dict = self.state_dict()
        pretrain_dict = {k: v for k, v in pretrain_dict.items() if k in model_dict and model_dict[k].size() == v.size()}
        model_dict.update(pretrain_dict)
        self.load_state_dict(model_dict)

    def featuremaps(self, x):
        x = self.conv2d_1a(x)
        x = self.conv2d_2a(x)
        x = self.conv2d_2b(x)
        x = self.maxpool_3a(x)
        x = self.conv2d_3b(x)
        x = self.conv2d_4a(x)
        x = self.maxpool_5a(x)
        x = self.mixed_5b(x)
        x = self.repeat(x)
        x = self.mixed_6a(x)
        x = self.repeat_1(x)
        x = self.mixed_7a(x)
        x = self.repeat_2(x)
        x = self.block8(x)
        x = self.conv2d_7b(x)
        return x

    def forward(self, x):
        f = self.featuremaps(x)
        v = self.global_avgpool(f)
        v = v.view(v.size(0), -1)
        if not self.training:
            return v
        y = self.classifier(v)
        if self.loss == 'softmax':
            return y
        elif self.loss == 'triplet':
            return (y, v)
        else:
            raise KeyError('Unsupported loss: {}'.format(self.loss))

def featuremaps(self, x):
    x = self.conv2d_1a(x)
    x = self.conv2d_2a(x)
    x = self.conv2d_2b(x)
    x = self.maxpool_3a(x)
    x = self.conv2d_3b(x)
    x = self.conv2d_4a(x)
    x = self.maxpool_5a(x)
    x = self.mixed_5b(x)
    x = self.repeat(x)
    x = self.mixed_6a(x)
    x = self.repeat_1(x)
    x = self.mixed_7a(x)
    x = self.repeat_2(x)
    x = self.block8(x)
    x = self.conv2d_7b(x)
    return x

class BasicBlock(nn.Module):
    expansion = 1

    def __init__(self, inplanes, planes, stride=1, downsample=None):
        super(BasicBlock, self).__init__()
        self.conv1 = conv3x3(inplanes, planes, stride)
        self.bn1 = nn.BatchNorm2d(planes)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = conv3x3(planes, planes)
        self.bn2 = nn.BatchNorm2d(planes)
        self.downsample = downsample
        self.stride = stride

    def forward(self, x):
        residual = x
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)
        out = self.conv2(out)
        out = self.bn2(out)
        if self.downsample is not None:
            residual = self.downsample(x)
        out += residual
        out = self.relu(out)
        return out

def forward(self, x):
    residual = x
    out = self.conv1(x)
    out = self.bn1(out)
    out = self.relu(out)
    out = self.conv2(out)
    out = self.bn2(out)
    if self.downsample is not None:
        residual = self.downsample(x)
    out += residual
    out = self.relu(out)
    return out

class Bottleneck(nn.Module):
    expansion = 4

    def __init__(self, inplanes, planes, stride=1, downsample=None, IN=False):
        super(Bottleneck, self).__init__()
        self.conv1 = nn.Conv2d(inplanes, planes, kernel_size=1, bias=False)
        self.bn1 = nn.BatchNorm2d(planes)
        self.conv2 = nn.Conv2d(planes, planes, kernel_size=3, stride=stride, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(planes)
        self.conv3 = nn.Conv2d(planes, planes * self.expansion, kernel_size=1, bias=False)
        self.bn3 = nn.BatchNorm2d(planes * self.expansion)
        self.IN = None
        if IN:
            self.IN = nn.InstanceNorm2d(planes * 4, affine=True)
        self.relu = nn.ReLU(inplace=True)
        self.downsample = downsample
        self.stride = stride

    def forward(self, x):
        residual = x
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)
        out = self.conv2(out)
        out = self.bn2(out)
        out = self.relu(out)
        out = self.conv3(out)
        out = self.bn3(out)
        if self.downsample is not None:
            residual = self.downsample(x)
        out += residual
        if self.IN is not None:
            out = self.IN(out)
        out = self.relu(out)
        return out

def forward(self, x):
    residual = x
    out = self.conv1(x)
    out = self.bn1(out)
    out = self.relu(out)
    out = self.conv2(out)
    out = self.bn2(out)
    out = self.relu(out)
    out = self.conv3(out)
    out = self.bn3(out)
    if self.downsample is not None:
        residual = self.downsample(x)
    out += residual
    if self.IN is not None:
        out = self.IN(out)
    out = self.relu(out)
    return out

class ResNet(nn.Module):
    """Residual network + IBN layer.
    
    Reference:
        - He et al. Deep Residual Learning for Image Recognition. CVPR 2016.
        - Pan et al. Two at Once: Enhancing Learning and Generalization
          Capacities via IBN-Net. ECCV 2018.
    """

    def __init__(self, block, layers, num_classes=1000, loss='softmax', fc_dims=None, dropout_p=None, **kwargs):
        scale = 64
        self.inplanes = scale
        super(ResNet, self).__init__()
        self.loss = loss
        self.feature_dim = scale * 8 * block.expansion
        self.conv1 = nn.Conv2d(3, scale, kernel_size=7, stride=2, padding=3, bias=False)
        self.bn1 = nn.InstanceNorm2d(scale, affine=True)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        self.layer1 = self._make_layer(block, scale, layers[0], stride=1, IN=True)
        self.layer2 = self._make_layer(block, scale * 2, layers[1], stride=2, IN=True)
        self.layer3 = self._make_layer(block, scale * 4, layers[2], stride=2)
        self.layer4 = self._make_layer(block, scale * 8, layers[3], stride=2)
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = self._construct_fc_layer(fc_dims, scale * 8 * block.expansion, dropout_p)
        self.classifier = nn.Linear(self.feature_dim, num_classes)
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                n = m.kernel_size[0] * m.kernel_size[1] * m.out_channels
                m.weight.data.normal_(0, math.sqrt(2.0 / n))
            elif isinstance(m, nn.BatchNorm2d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()
            elif isinstance(m, nn.InstanceNorm2d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()

    def _make_layer(self, block, planes, blocks, stride=1, IN=False):
        downsample = None
        if stride != 1 or self.inplanes != planes * block.expansion:
            downsample = nn.Sequential(nn.Conv2d(self.inplanes, planes * block.expansion, kernel_size=1, stride=stride, bias=False), nn.BatchNorm2d(planes * block.expansion))
        layers = []
        layers.append(block(self.inplanes, planes, stride, downsample))
        self.inplanes = planes * block.expansion
        for i in range(1, blocks - 1):
            layers.append(block(self.inplanes, planes))
        layers.append(block(self.inplanes, planes, IN=IN))
        return nn.Sequential(*layers)

    def _construct_fc_layer(self, fc_dims, input_dim, dropout_p=None):
        """Constructs fully connected layer

        Args:
            fc_dims (list or tuple): dimensions of fc layers, if None, no fc layers are constructed
            input_dim (int): input dimension
            dropout_p (float): dropout probability, if None, dropout is unused
        """
        if fc_dims is None:
            self.feature_dim = input_dim
            return None
        assert isinstance(fc_dims, (list, tuple)), 'fc_dims must be either list or tuple, but got {}'.format(type(fc_dims))
        layers = []
        for dim in fc_dims:
            layers.append(nn.Linear(input_dim, dim))
            layers.append(nn.BatchNorm1d(dim))
            layers.append(nn.ReLU(inplace=True))
            if dropout_p is not None:
                layers.append(nn.Dropout(p=dropout_p))
            input_dim = dim
        self.feature_dim = fc_dims[-1]
        return nn.Sequential(*layers)

    def featuremaps(self, x):
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)
        return x

    def forward(self, x):
        f = self.featuremaps(x)
        v = self.avgpool(f)
        v = v.view(v.size(0), -1)
        if self.fc is not None:
            v = self.fc(v)
        if not self.training:
            return v
        y = self.classifier(v)
        if self.loss == 'softmax':
            return y
        elif self.loss == 'triplet':
            return (y, v)
        else:
            raise KeyError('Unsupported loss: {}'.format(self.loss))

def featuremaps(self, x):
    x = self.conv1(x)
    x = self.bn1(x)
    x = self.relu(x)
    x = self.maxpool(x)
    x = self.layer1(x)
    x = self.layer2(x)
    x = self.layer3(x)
    x = self.layer4(x)
    return x

class BranchSeparables(nn.Module):

    def __init__(self, in_channels, out_channels, kernel_size, stride, padding, name=None, bias=False):
        super(BranchSeparables, self).__init__()
        self.relu = nn.ReLU()
        self.separable_1 = SeparableConv2d(in_channels, in_channels, kernel_size, stride, padding, bias=bias)
        self.bn_sep_1 = nn.BatchNorm2d(in_channels, eps=0.001, momentum=0.1, affine=True)
        self.relu1 = nn.ReLU()
        self.separable_2 = SeparableConv2d(in_channels, out_channels, kernel_size, 1, padding, bias=bias)
        self.bn_sep_2 = nn.BatchNorm2d(out_channels, eps=0.001, momentum=0.1, affine=True)
        self.name = name

    def forward(self, x):
        x = self.relu(x)
        if self.name == 'specific':
            x = nn.ZeroPad2d((1, 0, 1, 0))(x)
        x = self.separable_1(x)
        if self.name == 'specific':
            x = x[:, :, 1:, 1:].contiguous()
        x = self.bn_sep_1(x)
        x = self.relu1(x)
        x = self.separable_2(x)
        x = self.bn_sep_2(x)
        return x

def forward(self, x):
    x = self.relu(x)
    if self.name == 'specific':
        x = nn.ZeroPad2d((1, 0, 1, 0))(x)
    x = self.separable_1(x)
    if self.name == 'specific':
        x = x[:, :, 1:, 1:].contiguous()
    x = self.bn_sep_1(x)
    x = self.relu1(x)
    x = self.separable_2(x)
    x = self.bn_sep_2(x)
    return x

class BranchSeparablesStem(nn.Module):

    def __init__(self, in_channels, out_channels, kernel_size, stride, padding, bias=False):
        super(BranchSeparablesStem, self).__init__()
        self.relu = nn.ReLU()
        self.separable_1 = SeparableConv2d(in_channels, out_channels, kernel_size, stride, padding, bias=bias)
        self.bn_sep_1 = nn.BatchNorm2d(out_channels, eps=0.001, momentum=0.1, affine=True)
        self.relu1 = nn.ReLU()
        self.separable_2 = SeparableConv2d(out_channels, out_channels, kernel_size, 1, padding, bias=bias)
        self.bn_sep_2 = nn.BatchNorm2d(out_channels, eps=0.001, momentum=0.1, affine=True)

    def forward(self, x):
        x = self.relu(x)
        x = self.separable_1(x)
        x = self.bn_sep_1(x)
        x = self.relu1(x)
        x = self.separable_2(x)
        x = self.bn_sep_2(x)
        return x

def forward(self, x):
    x = self.relu(x)
    x = self.separable_1(x)
    x = self.bn_sep_1(x)
    x = self.relu1(x)
    x = self.separable_2(x)
    x = self.bn_sep_2(x)
    return x

class BranchSeparablesReduction(BranchSeparables):

    def __init__(self, in_channels, out_channels, kernel_size, stride, padding, z_padding=1, bias=False):
        BranchSeparables.__init__(self, in_channels, out_channels, kernel_size, stride, padding, bias)
        self.padding = nn.ZeroPad2d((z_padding, 0, z_padding, 0))

    def forward(self, x):
        x = self.relu(x)
        x = self.padding(x)
        x = self.separable_1(x)
        x = x[:, :, 1:, 1:].contiguous()
        x = self.bn_sep_1(x)
        x = self.relu1(x)
        x = self.separable_2(x)
        x = self.bn_sep_2(x)
        return x

def forward(self, x):
    x = self.relu(x)
    x = self.padding(x)
    x = self.separable_1(x)
    x = x[:, :, 1:, 1:].contiguous()
    x = self.bn_sep_1(x)
    x = self.relu1(x)
    x = self.separable_2(x)
    x = self.bn_sep_2(x)
    return x

class NASNetAMobile(nn.Module):
    """Neural Architecture Search (NAS).

    Reference:
        Zoph et al. Learning Transferable Architectures
        for Scalable Image Recognition. CVPR 2018.

    Public keys:
        - ``nasnetamobile``: NASNet-A Mobile.
    """

    def __init__(self, num_classes, loss, stem_filters=32, penultimate_filters=1056, filters_multiplier=2, **kwargs):
        super(NASNetAMobile, self).__init__()
        self.stem_filters = stem_filters
        self.penultimate_filters = penultimate_filters
        self.filters_multiplier = filters_multiplier
        self.loss = loss
        filters = self.penultimate_filters // 24
        self.conv0 = nn.Sequential()
        self.conv0.add_module('conv', nn.Conv2d(in_channels=3, out_channels=self.stem_filters, kernel_size=3, padding=0, stride=2, bias=False))
        self.conv0.add_module('bn', nn.BatchNorm2d(self.stem_filters, eps=0.001, momentum=0.1, affine=True))
        self.cell_stem_0 = CellStem0(self.stem_filters, num_filters=filters // filters_multiplier ** 2)
        self.cell_stem_1 = CellStem1(self.stem_filters, num_filters=filters // filters_multiplier)
        self.cell_0 = FirstCell(in_channels_left=filters, out_channels_left=filters // 2, in_channels_right=2 * filters, out_channels_right=filters)
        self.cell_1 = NormalCell(in_channels_left=2 * filters, out_channels_left=filters, in_channels_right=6 * filters, out_channels_right=filters)
        self.cell_2 = NormalCell(in_channels_left=6 * filters, out_channels_left=filters, in_channels_right=6 * filters, out_channels_right=filters)
        self.cell_3 = NormalCell(in_channels_left=6 * filters, out_channels_left=filters, in_channels_right=6 * filters, out_channels_right=filters)
        self.reduction_cell_0 = ReductionCell0(in_channels_left=6 * filters, out_channels_left=2 * filters, in_channels_right=6 * filters, out_channels_right=2 * filters)
        self.cell_6 = FirstCell(in_channels_left=6 * filters, out_channels_left=filters, in_channels_right=8 * filters, out_channels_right=2 * filters)
        self.cell_7 = NormalCell(in_channels_left=8 * filters, out_channels_left=2 * filters, in_channels_right=12 * filters, out_channels_right=2 * filters)
        self.cell_8 = NormalCell(in_channels_left=12 * filters, out_channels_left=2 * filters, in_channels_right=12 * filters, out_channels_right=2 * filters)
        self.cell_9 = NormalCell(in_channels_left=12 * filters, out_channels_left=2 * filters, in_channels_right=12 * filters, out_channels_right=2 * filters)
        self.reduction_cell_1 = ReductionCell1(in_channels_left=12 * filters, out_channels_left=4 * filters, in_channels_right=12 * filters, out_channels_right=4 * filters)
        self.cell_12 = FirstCell(in_channels_left=12 * filters, out_channels_left=2 * filters, in_channels_right=16 * filters, out_channels_right=4 * filters)
        self.cell_13 = NormalCell(in_channels_left=16 * filters, out_channels_left=4 * filters, in_channels_right=24 * filters, out_channels_right=4 * filters)
        self.cell_14 = NormalCell(in_channels_left=24 * filters, out_channels_left=4 * filters, in_channels_right=24 * filters, out_channels_right=4 * filters)
        self.cell_15 = NormalCell(in_channels_left=24 * filters, out_channels_left=4 * filters, in_channels_right=24 * filters, out_channels_right=4 * filters)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout()
        self.classifier = nn.Linear(24 * filters, num_classes)
        self._init_params()

    def _init_params(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)

    def features(self, input):
        x_conv0 = self.conv0(input)
        x_stem_0 = self.cell_stem_0(x_conv0)
        x_stem_1 = self.cell_stem_1(x_conv0, x_stem_0)
        x_cell_0 = self.cell_0(x_stem_1, x_stem_0)
        x_cell_1 = self.cell_1(x_cell_0, x_stem_1)
        x_cell_2 = self.cell_2(x_cell_1, x_cell_0)
        x_cell_3 = self.cell_3(x_cell_2, x_cell_1)
        x_reduction_cell_0 = self.reduction_cell_0(x_cell_3, x_cell_2)
        x_cell_6 = self.cell_6(x_reduction_cell_0, x_cell_3)
        x_cell_7 = self.cell_7(x_cell_6, x_reduction_cell_0)
        x_cell_8 = self.cell_8(x_cell_7, x_cell_6)
        x_cell_9 = self.cell_9(x_cell_8, x_cell_7)
        x_reduction_cell_1 = self.reduction_cell_1(x_cell_9, x_cell_8)
        x_cell_12 = self.cell_12(x_reduction_cell_1, x_cell_9)
        x_cell_13 = self.cell_13(x_cell_12, x_reduction_cell_1)
        x_cell_14 = self.cell_14(x_cell_13, x_cell_12)
        x_cell_15 = self.cell_15(x_cell_14, x_cell_13)
        x_cell_15 = self.relu(x_cell_15)
        x_cell_15 = F.avg_pool2d(x_cell_15, x_cell_15.size()[2:])
        x_cell_15 = x_cell_15.view(x_cell_15.size(0), -1)
        x_cell_15 = self.dropout(x_cell_15)
        return x_cell_15

    def forward(self, input):
        v = self.features(input)
        if not self.training:
            return v
        y = self.classifier(v)
        if self.loss == 'softmax':
            return y
        elif self.loss == 'triplet':
            return (y, v)
        else:
            raise KeyError('Unsupported loss: {}'.format(self.loss))

def features(self, input):
    x_conv0 = self.conv0(input)
    x_stem_0 = self.cell_stem_0(x_conv0)
    x_stem_1 = self.cell_stem_1(x_conv0, x_stem_0)
    x_cell_0 = self.cell_0(x_stem_1, x_stem_0)
    x_cell_1 = self.cell_1(x_cell_0, x_stem_1)
    x_cell_2 = self.cell_2(x_cell_1, x_cell_0)
    x_cell_3 = self.cell_3(x_cell_2, x_cell_1)
    x_reduction_cell_0 = self.reduction_cell_0(x_cell_3, x_cell_2)
    x_cell_6 = self.cell_6(x_reduction_cell_0, x_cell_3)
    x_cell_7 = self.cell_7(x_cell_6, x_reduction_cell_0)
    x_cell_8 = self.cell_8(x_cell_7, x_cell_6)
    x_cell_9 = self.cell_9(x_cell_8, x_cell_7)
    x_reduction_cell_1 = self.reduction_cell_1(x_cell_9, x_cell_8)
    x_cell_12 = self.cell_12(x_reduction_cell_1, x_cell_9)
    x_cell_13 = self.cell_13(x_cell_12, x_reduction_cell_1)
    x_cell_14 = self.cell_14(x_cell_13, x_cell_12)
    x_cell_15 = self.cell_15(x_cell_14, x_cell_13)
    x_cell_15 = self.relu(x_cell_15)
    x_cell_15 = F.avg_pool2d(x_cell_15, x_cell_15.size()[2:])
    x_cell_15 = x_cell_15.view(x_cell_15.size(0), -1)
    x_cell_15 = self.dropout(x_cell_15)
    return x_cell_15

class _DenseLayer(nn.Sequential):

    def __init__(self, num_input_features, growth_rate, bn_size, drop_rate):
        super(_DenseLayer, self).__init__()
        (self.add_module('norm1', nn.BatchNorm2d(num_input_features)),)
        (self.add_module('relu1', nn.ReLU(inplace=True)),)
        (self.add_module('conv1', nn.Conv2d(num_input_features, bn_size * growth_rate, kernel_size=1, stride=1, bias=False)),)
        (self.add_module('norm2', nn.BatchNorm2d(bn_size * growth_rate)),)
        (self.add_module('relu2', nn.ReLU(inplace=True)),)
        (self.add_module('conv2', nn.Conv2d(bn_size * growth_rate, growth_rate, kernel_size=3, stride=1, padding=1, bias=False)),)
        self.drop_rate = drop_rate

    def forward(self, x):
        new_features = super(_DenseLayer, self).forward(x)
        if self.drop_rate > 0:
            new_features = F.dropout(new_features, p=self.drop_rate, training=self.training)
        return torch.cat([x, new_features], 1)

def forward(self, x):
    new_features = super(_DenseLayer, self).forward(x)
    if self.drop_rate > 0:
        new_features = F.dropout(new_features, p=self.drop_rate, training=self.training)
    return torch.cat([x, new_features], 1)

class Bottleneck(nn.Module):

    def __init__(self, in_channels, out_channels, stride, num_groups, group_conv1x1=True):
        super(Bottleneck, self).__init__()
        assert stride in [1, 2], 'Warning: stride must be either 1 or 2'
        self.stride = stride
        mid_channels = out_channels // 4
        if stride == 2:
            out_channels -= in_channels
        num_groups_conv1x1 = num_groups if group_conv1x1 else 1
        self.conv1 = nn.Conv2d(in_channels, mid_channels, 1, groups=num_groups_conv1x1, bias=False)
        self.bn1 = nn.BatchNorm2d(mid_channels)
        self.shuffle1 = ChannelShuffle(num_groups)
        self.conv2 = nn.Conv2d(mid_channels, mid_channels, 3, stride=stride, padding=1, groups=mid_channels, bias=False)
        self.bn2 = nn.BatchNorm2d(mid_channels)
        self.conv3 = nn.Conv2d(mid_channels, out_channels, 1, groups=num_groups, bias=False)
        self.bn3 = nn.BatchNorm2d(out_channels)
        if stride == 2:
            self.shortcut = nn.AvgPool2d(3, stride=2, padding=1)

    def forward(self, x):
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.shuffle1(out)
        out = self.bn2(self.conv2(out))
        out = self.bn3(self.conv3(out))
        if self.stride == 2:
            res = self.shortcut(x)
            out = F.relu(torch.cat([res, out], 1))
        else:
            out = F.relu(x + out)
        return out

def forward(self, x):
    out = F.relu(self.bn1(self.conv1(x)))
    out = self.shuffle1(out)
    out = self.bn2(self.conv2(out))
    out = self.bn3(self.conv3(out))
    if self.stride == 2:
        res = self.shortcut(x)
        out = F.relu(torch.cat([res, out], 1))
    else:
        out = F.relu(x + out)
    return out

class ShuffleNet(nn.Module):
    """ShuffleNet.

    Reference:
        Zhang et al. ShuffleNet: An Extremely Efficient Convolutional Neural
        Network for Mobile Devices. CVPR 2018.

    Public keys:
        - ``shufflenet``: ShuffleNet (groups=3).
    """

    def __init__(self, num_classes, loss='softmax', num_groups=3, **kwargs):
        super(ShuffleNet, self).__init__()
        self.loss = loss
        self.conv1 = nn.Sequential(nn.Conv2d(3, 24, 3, stride=2, padding=1, bias=False), nn.BatchNorm2d(24), nn.ReLU(), nn.MaxPool2d(3, stride=2, padding=1))
        self.stage2 = nn.Sequential(Bottleneck(24, cfg[num_groups][0], 2, num_groups, group_conv1x1=False), Bottleneck(cfg[num_groups][0], cfg[num_groups][0], 1, num_groups), Bottleneck(cfg[num_groups][0], cfg[num_groups][0], 1, num_groups), Bottleneck(cfg[num_groups][0], cfg[num_groups][0], 1, num_groups))
        self.stage3 = nn.Sequential(Bottleneck(cfg[num_groups][0], cfg[num_groups][1], 2, num_groups), Bottleneck(cfg[num_groups][1], cfg[num_groups][1], 1, num_groups), Bottleneck(cfg[num_groups][1], cfg[num_groups][1], 1, num_groups), Bottleneck(cfg[num_groups][1], cfg[num_groups][1], 1, num_groups), Bottleneck(cfg[num_groups][1], cfg[num_groups][1], 1, num_groups), Bottleneck(cfg[num_groups][1], cfg[num_groups][1], 1, num_groups), Bottleneck(cfg[num_groups][1], cfg[num_groups][1], 1, num_groups), Bottleneck(cfg[num_groups][1], cfg[num_groups][1], 1, num_groups))
        self.stage4 = nn.Sequential(Bottleneck(cfg[num_groups][1], cfg[num_groups][2], 2, num_groups), Bottleneck(cfg[num_groups][2], cfg[num_groups][2], 1, num_groups), Bottleneck(cfg[num_groups][2], cfg[num_groups][2], 1, num_groups), Bottleneck(cfg[num_groups][2], cfg[num_groups][2], 1, num_groups))
        self.classifier = nn.Linear(cfg[num_groups][2], num_classes)
        self.feat_dim = cfg[num_groups][2]

    def forward(self, x):
        x = self.conv1(x)
        x = self.stage2(x)
        x = self.stage3(x)
        x = self.stage4(x)
        x = F.avg_pool2d(x, x.size()[2:]).view(x.size(0), -1)
        if not self.training:
            return x
        y = self.classifier(x)
        if self.loss == 'softmax':
            return y
        elif self.loss == 'triplet':
            return (y, x)
        else:
            raise KeyError('Unsupported loss: {}'.format(self.loss))

def forward(self, x):
    x = self.conv1(x)
    x = self.stage2(x)
    x = self.stage3(x)
    x = self.stage4(x)
    x = F.avg_pool2d(x, x.size()[2:]).view(x.size(0), -1)
    if not self.training:
        return x
    y = self.classifier(x)
    if self.loss == 'softmax':
        return y
    elif self.loss == 'triplet':
        return (y, x)
    else:
        raise KeyError('Unsupported loss: {}'.format(self.loss))

class SEModule(nn.Module):

    def __init__(self, channels, reduction):
        super(SEModule, self).__init__()
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.fc1 = nn.Conv2d(channels, channels // reduction, kernel_size=1, padding=0)
        self.relu = nn.ReLU(inplace=True)
        self.fc2 = nn.Conv2d(channels // reduction, channels, kernel_size=1, padding=0)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        module_input = x
        x = self.avg_pool(x)
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        x = self.sigmoid(x)
        return module_input * x

def forward(self, x):
    module_input = x
    x = self.avg_pool(x)
    x = self.fc1(x)
    x = self.relu(x)
    x = self.fc2(x)
    x = self.sigmoid(x)
    return module_input * x

class Bottleneck(nn.Module):
    """
    Base class for bottlenecks that implements `forward()` method.
    """

    def forward(self, x):
        residual = x
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)
        out = self.conv2(out)
        out = self.bn2(out)
        out = self.relu(out)
        out = self.conv3(out)
        out = self.bn3(out)
        if self.downsample is not None:
            residual = self.downsample(x)
        out = self.se_module(out) + residual
        out = self.relu(out)
        return out

def forward(self, x):
    residual = x
    out = self.conv1(x)
    out = self.bn1(out)
    out = self.relu(out)
    out = self.conv2(out)
    out = self.bn2(out)
    out = self.relu(out)
    out = self.conv3(out)
    out = self.bn3(out)
    if self.downsample is not None:
        residual = self.downsample(x)
    out = self.se_module(out) + residual
    out = self.relu(out)
    return out

class SENet(nn.Module):
    """Squeeze-and-excitation network.
    
    Reference:
        Hu et al. Squeeze-and-Excitation Networks. CVPR 2018.

    Public keys:
        - ``senet154``: SENet154.
        - ``se_resnet50``: ResNet50 + SE.
        - ``se_resnet101``: ResNet101 + SE.
        - ``se_resnet152``: ResNet152 + SE.
        - ``se_resnext50_32x4d``: ResNeXt50 (groups=32, width=4) + SE.
        - ``se_resnext101_32x4d``: ResNeXt101 (groups=32, width=4) + SE.
        - ``se_resnet50_fc512``: (ResNet50 + SE) + FC.
    """

    def __init__(self, num_classes, loss, block, layers, groups, reduction, dropout_p=0.2, inplanes=128, input_3x3=True, downsample_kernel_size=3, downsample_padding=1, last_stride=2, fc_dims=None, **kwargs):
        """
        Parameters
        ----------
        block (nn.Module): Bottleneck class.
            - For SENet154: SEBottleneck
            - For SE-ResNet models: SEResNetBottleneck
            - For SE-ResNeXt models:  SEResNeXtBottleneck
        layers (list of ints): Number of residual blocks for 4 layers of the
            network (layer1...layer4).
        groups (int): Number of groups for the 3x3 convolution in each
            bottleneck block.
            - For SENet154: 64
            - For SE-ResNet models: 1
            - For SE-ResNeXt models:  32
        reduction (int): Reduction ratio for Squeeze-and-Excitation modules.
            - For all models: 16
        dropout_p (float or None): Drop probability for the Dropout layer.
            If `None` the Dropout layer is not used.
            - For SENet154: 0.2
            - For SE-ResNet models: None
            - For SE-ResNeXt models: None
        inplanes (int):  Number of input channels for layer1.
            - For SENet154: 128
            - For SE-ResNet models: 64
            - For SE-ResNeXt models: 64
        input_3x3 (bool): If `True`, use three 3x3 convolutions instead of
            a single 7x7 convolution in layer0.
            - For SENet154: True
            - For SE-ResNet models: False
            - For SE-ResNeXt models: False
        downsample_kernel_size (int): Kernel size for downsampling convolutions
            in layer2, layer3 and layer4.
            - For SENet154: 3
            - For SE-ResNet models: 1
            - For SE-ResNeXt models: 1
        downsample_padding (int): Padding for downsampling convolutions in
            layer2, layer3 and layer4.
            - For SENet154: 1
            - For SE-ResNet models: 0
            - For SE-ResNeXt models: 0
        num_classes (int): Number of outputs in `classifier` layer.
        """
        super(SENet, self).__init__()
        self.inplanes = inplanes
        self.loss = loss
        if input_3x3:
            layer0_modules = [('conv1', nn.Conv2d(3, 64, 3, stride=2, padding=1, bias=False)), ('bn1', nn.BatchNorm2d(64)), ('relu1', nn.ReLU(inplace=True)), ('conv2', nn.Conv2d(64, 64, 3, stride=1, padding=1, bias=False)), ('bn2', nn.BatchNorm2d(64)), ('relu2', nn.ReLU(inplace=True)), ('conv3', nn.Conv2d(64, inplanes, 3, stride=1, padding=1, bias=False)), ('bn3', nn.BatchNorm2d(inplanes)), ('relu3', nn.ReLU(inplace=True))]
        else:
            layer0_modules = [('conv1', nn.Conv2d(3, inplanes, kernel_size=7, stride=2, padding=3, bias=False)), ('bn1', nn.BatchNorm2d(inplanes)), ('relu1', nn.ReLU(inplace=True))]
        layer0_modules.append(('pool', nn.MaxPool2d(3, stride=2, ceil_mode=True)))
        self.layer0 = nn.Sequential(OrderedDict(layer0_modules))
        self.layer1 = self._make_layer(block, planes=64, blocks=layers[0], groups=groups, reduction=reduction, downsample_kernel_size=1, downsample_padding=0)
        self.layer2 = self._make_layer(block, planes=128, blocks=layers[1], stride=2, groups=groups, reduction=reduction, downsample_kernel_size=downsample_kernel_size, downsample_padding=downsample_padding)
        self.layer3 = self._make_layer(block, planes=256, blocks=layers[2], stride=2, groups=groups, reduction=reduction, downsample_kernel_size=downsample_kernel_size, downsample_padding=downsample_padding)
        self.layer4 = self._make_layer(block, planes=512, blocks=layers[3], stride=last_stride, groups=groups, reduction=reduction, downsample_kernel_size=downsample_kernel_size, downsample_padding=downsample_padding)
        self.global_avgpool = nn.AdaptiveAvgPool2d(1)
        self.fc = self._construct_fc_layer(fc_dims, 512 * block.expansion, dropout_p)
        self.classifier = nn.Linear(self.feature_dim, num_classes)

    def _make_layer(self, block, planes, blocks, groups, reduction, stride=1, downsample_kernel_size=1, downsample_padding=0):
        downsample = None
        if stride != 1 or self.inplanes != planes * block.expansion:
            downsample = nn.Sequential(nn.Conv2d(self.inplanes, planes * block.expansion, kernel_size=downsample_kernel_size, stride=stride, padding=downsample_padding, bias=False), nn.BatchNorm2d(planes * block.expansion))
        layers = []
        layers.append(block(self.inplanes, planes, groups, reduction, stride, downsample))
        self.inplanes = planes * block.expansion
        for i in range(1, blocks):
            layers.append(block(self.inplanes, planes, groups, reduction))
        return nn.Sequential(*layers)

    def _construct_fc_layer(self, fc_dims, input_dim, dropout_p=None):
        """
        Construct fully connected layer

        - fc_dims (list or tuple): dimensions of fc layers, if None,
                                   no fc layers are constructed
        - input_dim (int): input dimension
        - dropout_p (float): dropout probability, if None, dropout is unused
        """
        if fc_dims is None:
            self.feature_dim = input_dim
            return None
        assert isinstance(fc_dims, (list, tuple)), 'fc_dims must be either list or tuple, but got {}'.format(type(fc_dims))
        layers = []
        for dim in fc_dims:
            layers.append(nn.Linear(input_dim, dim))
            layers.append(nn.BatchNorm1d(dim))
            layers.append(nn.ReLU(inplace=True))
            if dropout_p is not None:
                layers.append(nn.Dropout(p=dropout_p))
            input_dim = dim
        self.feature_dim = fc_dims[-1]
        return nn.Sequential(*layers)

    def featuremaps(self, x):
        x = self.layer0(x)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)
        return x

    def forward(self, x):
        f = self.featuremaps(x)
        v = self.global_avgpool(f)
        v = v.view(v.size(0), -1)
        if self.fc is not None:
            v = self.fc(v)
        if not self.training:
            return v
        y = self.classifier(v)
        if self.loss == 'softmax':
            return y
        elif self.loss == 'triplet':
            return (y, v)
        else:
            raise KeyError('Unsupported loss: {}'.format(self.loss))

def featuremaps(self, x):
    x = self.layer0(x)
    x = self.layer1(x)
    x = self.layer2(x)
    x = self.layer3(x)
    x = self.layer4(x)
    return x

class ConvBlock(nn.Module):
    """Basic convolutional block.
    
    convolution (bias discarded) + batch normalization + relu6.

    Args:
        in_c (int): number of input channels.
        out_c (int): number of output channels.
        k (int or tuple): kernel size.
        s (int or tuple): stride.
        p (int or tuple): padding.
        g (int): number of blocked connections from input channels
            to output channels (default: 1).
    """

    def __init__(self, in_c, out_c, k, s=1, p=0, g=1):
        super(ConvBlock, self).__init__()
        self.conv = nn.Conv2d(in_c, out_c, k, stride=s, padding=p, bias=False, groups=g)
        self.bn = nn.BatchNorm2d(out_c)

    def forward(self, x):
        return F.relu6(self.bn(self.conv(x)))

def forward(self, x):
    return F.relu6(self.bn(self.conv(x)))

class Bottleneck(nn.Module):

    def __init__(self, in_channels, out_channels, expansion_factor, stride=1):
        super(Bottleneck, self).__init__()
        mid_channels = in_channels * expansion_factor
        self.use_residual = stride == 1 and in_channels == out_channels
        self.conv1 = ConvBlock(in_channels, mid_channels, 1)
        self.dwconv2 = ConvBlock(mid_channels, mid_channels, 3, stride, 1, g=mid_channels)
        self.conv3 = nn.Sequential(nn.Conv2d(mid_channels, out_channels, 1, bias=False), nn.BatchNorm2d(out_channels))

    def forward(self, x):
        m = self.conv1(x)
        m = self.dwconv2(m)
        m = self.conv3(m)
        if self.use_residual:
            return x + m
        else:
            return m

def forward(self, x):
    m = self.conv1(x)
    m = self.dwconv2(m)
    m = self.conv3(m)
    if self.use_residual:
        return x + m
    else:
        return m

class MobileNetV2(nn.Module):
    """MobileNetV2.

    Reference:
        Sandler et al. MobileNetV2: Inverted Residuals and
        Linear Bottlenecks. CVPR 2018.

    Public keys:
        - ``mobilenetv2_x1_0``: MobileNetV2 x1.0.
        - ``mobilenetv2_x1_4``: MobileNetV2 x1.4.
    """

    def __init__(self, num_classes, width_mult=1, loss='softmax', fc_dims=None, dropout_p=None, **kwargs):
        super(MobileNetV2, self).__init__()
        self.loss = loss
        self.in_channels = int(32 * width_mult)
        self.feature_dim = int(1280 * width_mult) if width_mult > 1 else 1280
        self.conv1 = ConvBlock(3, self.in_channels, 3, s=2, p=1)
        self.conv2 = self._make_layer(Bottleneck, 1, int(16 * width_mult), 1, 1)
        self.conv3 = self._make_layer(Bottleneck, 6, int(24 * width_mult), 2, 2)
        self.conv4 = self._make_layer(Bottleneck, 6, int(32 * width_mult), 3, 2)
        self.conv5 = self._make_layer(Bottleneck, 6, int(64 * width_mult), 4, 2)
        self.conv6 = self._make_layer(Bottleneck, 6, int(96 * width_mult), 3, 1)
        self.conv7 = self._make_layer(Bottleneck, 6, int(160 * width_mult), 3, 2)
        self.conv8 = self._make_layer(Bottleneck, 6, int(320 * width_mult), 1, 1)
        self.conv9 = ConvBlock(self.in_channels, self.feature_dim, 1)
        self.global_avgpool = nn.AdaptiveAvgPool2d(1)
        self.fc = self._construct_fc_layer(fc_dims, self.feature_dim, dropout_p)
        self.classifier = nn.Linear(self.feature_dim, num_classes)
        self._init_params()

    def _make_layer(self, block, t, c, n, s):
        layers = []
        layers.append(block(self.in_channels, c, t, s))
        self.in_channels = c
        for i in range(1, n):
            layers.append(block(self.in_channels, c, t))
        return nn.Sequential(*layers)

    def _construct_fc_layer(self, fc_dims, input_dim, dropout_p=None):
        """Constructs fully connected layer.

        Args:
            fc_dims (list or tuple): dimensions of fc layers, if None, no fc layers are constructed
            input_dim (int): input dimension
            dropout_p (float): dropout probability, if None, dropout is unused
        """
        if fc_dims is None:
            self.feature_dim = input_dim
            return None
        assert isinstance(fc_dims, (list, tuple)), 'fc_dims must be either list or tuple, but got {}'.format(type(fc_dims))
        layers = []
        for dim in fc_dims:
            layers.append(nn.Linear(input_dim, dim))
            layers.append(nn.BatchNorm1d(dim))
            layers.append(nn.ReLU(inplace=True))
            if dropout_p is not None:
                layers.append(nn.Dropout(p=dropout_p))
            input_dim = dim
        self.feature_dim = fc_dims[-1]
        return nn.Sequential(*layers)

    def _init_params(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)

    def featuremaps(self, x):
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)
        x = self.conv4(x)
        x = self.conv5(x)
        x = self.conv6(x)
        x = self.conv7(x)
        x = self.conv8(x)
        x = self.conv9(x)
        return x

    def forward(self, x):
        f = self.featuremaps(x)
        v = self.global_avgpool(f)
        v = v.view(v.size(0), -1)
        if self.fc is not None:
            v = self.fc(v)
        if not self.training:
            return v
        y = self.classifier(v)
        if self.loss == 'softmax':
            return y
        elif self.loss == 'triplet':
            return (y, v)
        else:
            raise KeyError('Unsupported loss: {}'.format(self.loss))

def featuremaps(self, x):
    x = self.conv1(x)
    x = self.conv2(x)
    x = self.conv3(x)
    x = self.conv4(x)
    x = self.conv5(x)
    x = self.conv6(x)
    x = self.conv7(x)
    x = self.conv8(x)
    x = self.conv9(x)
    return x

class BasicBlock(nn.Module):
    expansion = 1

    def __init__(self, inplanes, planes, stride=1, downsample=None, groups=1, base_width=64, dilation=1, norm_layer=None):
        super(BasicBlock, self).__init__()
        if norm_layer is None:
            norm_layer = nn.BatchNorm2d
        if groups != 1 or base_width != 64:
            raise ValueError('BasicBlock only supports groups=1 and base_width=64')
        if dilation > 1:
            raise NotImplementedError('Dilation > 1 not supported in BasicBlock')
        self.conv1 = conv3x3(inplanes, planes, stride)
        self.bn1 = norm_layer(planes)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = conv3x3(planes, planes)
        self.bn2 = norm_layer(planes)
        self.downsample = downsample
        self.stride = stride

    def forward(self, x):
        identity = x
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)
        out = self.conv2(out)
        out = self.bn2(out)
        if self.downsample is not None:
            identity = self.downsample(x)
        out += identity
        out = self.relu(out)
        return out

def forward(self, x):
    identity = x
    out = self.conv1(x)
    out = self.bn1(out)
    out = self.relu(out)
    out = self.conv2(out)
    out = self.bn2(out)
    if self.downsample is not None:
        identity = self.downsample(x)
    out += identity
    out = self.relu(out)
    return out

class Bottleneck(nn.Module):
    expansion = 4

    def __init__(self, inplanes, planes, stride=1, downsample=None, groups=1, base_width=64, dilation=1, norm_layer=None):
        super(Bottleneck, self).__init__()
        if norm_layer is None:
            norm_layer = nn.BatchNorm2d
        width = int(planes * (base_width / 64.0)) * groups
        self.conv1 = conv1x1(inplanes, width)
        self.bn1 = norm_layer(width)
        self.conv2 = conv3x3(width, width, stride, groups, dilation)
        self.bn2 = norm_layer(width)
        self.conv3 = conv1x1(width, planes * self.expansion)
        self.bn3 = norm_layer(planes * self.expansion)
        self.relu = nn.ReLU(inplace=True)
        self.downsample = downsample
        self.stride = stride

    def forward(self, x):
        identity = x
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)
        out = self.conv2(out)
        out = self.bn2(out)
        out = self.relu(out)
        out = self.conv3(out)
        out = self.bn3(out)
        if self.downsample is not None:
            identity = self.downsample(x)
        out += identity
        out = self.relu(out)
        return out

def forward(self, x):
    identity = x
    out = self.conv1(x)
    out = self.bn1(out)
    out = self.relu(out)
    out = self.conv2(out)
    out = self.bn2(out)
    out = self.relu(out)
    out = self.conv3(out)
    out = self.bn3(out)
    if self.downsample is not None:
        identity = self.downsample(x)
    out += identity
    out = self.relu(out)
    return out

class ResNet(nn.Module):
    """Residual network.
    
    Reference:
        - He et al. Deep Residual Learning for Image Recognition. CVPR 2016.
        - Xie et al. Aggregated Residual Transformations for Deep Neural Networks. CVPR 2017.

    Public keys:
        - ``resnet18``: ResNet18.
        - ``resnet34``: ResNet34.
        - ``resnet50``: ResNet50.
        - ``resnet101``: ResNet101.
        - ``resnet152``: ResNet152.
        - ``resnext50_32x4d``: ResNeXt50.
        - ``resnext101_32x8d``: ResNeXt101.
        - ``resnet50_fc512``: ResNet50 + FC.
    """

    def __init__(self, num_classes, loss, block, layers, zero_init_residual=False, groups=1, width_per_group=64, replace_stride_with_dilation=None, norm_layer=None, last_stride=2, fc_dims=None, dropout_p=None, **kwargs):
        super(ResNet, self).__init__()
        if norm_layer is None:
            norm_layer = nn.BatchNorm2d
        self._norm_layer = norm_layer
        self.loss = loss
        self.feature_dim = 512 * block.expansion
        self.inplanes = 64
        self.dilation = 1
        if replace_stride_with_dilation is None:
            replace_stride_with_dilation = [False, False, False]
        if len(replace_stride_with_dilation) != 3:
            raise ValueError('replace_stride_with_dilation should be None or a 3-element tuple, got {}'.format(replace_stride_with_dilation))
        self.groups = groups
        self.base_width = width_per_group
        self.conv1 = nn.Conv2d(3, self.inplanes, kernel_size=7, stride=2, padding=3, bias=False)
        self.bn1 = norm_layer(self.inplanes)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        self.layer1 = self._make_layer(block, 64, layers[0])
        self.layer2 = self._make_layer(block, 128, layers[1], stride=2, dilate=replace_stride_with_dilation[0])
        self.layer3 = self._make_layer(block, 256, layers[2], stride=2, dilate=replace_stride_with_dilation[1])
        self.layer4 = self._make_layer(block, 512, layers[3], stride=last_stride, dilate=replace_stride_with_dilation[2])
        self.global_avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = self._construct_fc_layer(fc_dims, 512 * block.expansion, dropout_p)
        self.classifier = nn.Linear(self.feature_dim, num_classes)
        self._init_params()
        if zero_init_residual:
            for m in self.modules():
                if isinstance(m, Bottleneck):
                    nn.init.constant_(m.bn3.weight, 0)
                elif isinstance(m, BasicBlock):
                    nn.init.constant_(m.bn2.weight, 0)

    def _make_layer(self, block, planes, blocks, stride=1, dilate=False):
        norm_layer = self._norm_layer
        downsample = None
        previous_dilation = self.dilation
        if dilate:
            self.dilation *= stride
            stride = 1
        if stride != 1 or self.inplanes != planes * block.expansion:
            downsample = nn.Sequential(conv1x1(self.inplanes, planes * block.expansion, stride), norm_layer(planes * block.expansion))
        layers = []
        layers.append(block(self.inplanes, planes, stride, downsample, self.groups, self.base_width, previous_dilation, norm_layer))
        self.inplanes = planes * block.expansion
        for _ in range(1, blocks):
            layers.append(block(self.inplanes, planes, groups=self.groups, base_width=self.base_width, dilation=self.dilation, norm_layer=norm_layer))
        return nn.Sequential(*layers)

    def _construct_fc_layer(self, fc_dims, input_dim, dropout_p=None):
        """Constructs fully connected layer

        Args:
            fc_dims (list or tuple): dimensions of fc layers, if None, no fc layers are constructed
            input_dim (int): input dimension
            dropout_p (float): dropout probability, if None, dropout is unused
        """
        if fc_dims is None:
            self.feature_dim = input_dim
            return None
        assert isinstance(fc_dims, (list, tuple)), 'fc_dims must be either list or tuple, but got {}'.format(type(fc_dims))
        layers = []
        for dim in fc_dims:
            layers.append(nn.Linear(input_dim, dim))
            layers.append(nn.BatchNorm1d(dim))
            layers.append(nn.ReLU(inplace=True))
            if dropout_p is not None:
                layers.append(nn.Dropout(p=dropout_p))
            input_dim = dim
        self.feature_dim = fc_dims[-1]
        return nn.Sequential(*layers)

    def _init_params(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)

    def featuremaps(self, x):
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)
        return x

    def forward(self, x):
        f = self.featuremaps(x)
        v = self.global_avgpool(f)
        v = v.view(v.size(0), -1)
        if self.fc is not None:
            v = self.fc(v)
        if not self.training:
            return v
        y = self.classifier(v)
        if self.loss == 'softmax':
            return y
        elif self.loss == 'triplet':
            return (y, v)
        else:
            raise KeyError('Unsupported loss: {}'.format(self.loss))

def featuremaps(self, x):
    x = self.conv1(x)
    x = self.bn1(x)
    x = self.relu(x)
    x = self.maxpool(x)
    x = self.layer1(x)
    x = self.layer2(x)
    x = self.layer3(x)
    x = self.layer4(x)
    return x

class ConvLayer(nn.Module):
    """Convolution layer (conv + bn + relu)."""

    def __init__(self, in_channels, out_channels, kernel_size, stride=1, padding=0, groups=1, IN=False):
        super(ConvLayer, self).__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size, stride=stride, padding=padding, bias=False, groups=groups)
        if IN:
            self.bn = nn.InstanceNorm2d(out_channels, affine=True)
        else:
            self.bn = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        x = self.conv(x)
        x = self.bn(x)
        x = self.relu(x)
        return x

def forward(self, x):
    x = self.conv(x)
    x = self.bn(x)
    x = self.relu(x)
    return x

class Conv1x1(nn.Module):
    """1x1 convolution + bn + relu."""

    def __init__(self, in_channels, out_channels, stride=1, groups=1):
        super(Conv1x1, self).__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, 1, stride=stride, padding=0, bias=False, groups=groups)
        self.bn = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        x = self.conv(x)
        x = self.bn(x)
        x = self.relu(x)
        return x

def forward(self, x):
    x = self.conv(x)
    x = self.bn(x)
    x = self.relu(x)
    return x

class Conv1x1Linear(nn.Module):
    """1x1 convolution + bn (w/o non-linearity)."""

    def __init__(self, in_channels, out_channels, stride=1):
        super(Conv1x1Linear, self).__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, 1, stride=stride, padding=0, bias=False)
        self.bn = nn.BatchNorm2d(out_channels)

    def forward(self, x):
        x = self.conv(x)
        x = self.bn(x)
        return x

def forward(self, x):
    x = self.conv(x)
    x = self.bn(x)
    return x

class Conv3x3(nn.Module):
    """3x3 convolution + bn + relu."""

    def __init__(self, in_channels, out_channels, stride=1, groups=1):
        super(Conv3x3, self).__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, 3, stride=stride, padding=1, bias=False, groups=groups)
        self.bn = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        x = self.conv(x)
        x = self.bn(x)
        x = self.relu(x)
        return x

def forward(self, x):
    x = self.conv(x)
    x = self.bn(x)
    x = self.relu(x)
    return x

class LightConv3x3(nn.Module):
    """Lightweight 3x3 convolution.

    1x1 (linear) + dw 3x3 (nonlinear).
    """

    def __init__(self, in_channels, out_channels):
        super(LightConv3x3, self).__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, 1, stride=1, padding=0, bias=False)
        self.conv2 = nn.Conv2d(out_channels, out_channels, 3, stride=1, padding=1, bias=False, groups=out_channels)
        self.bn = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.bn(x)
        x = self.relu(x)
        return x

def forward(self, x):
    x = self.conv1(x)
    x = self.conv2(x)
    x = self.bn(x)
    x = self.relu(x)
    return x

class ChannelGate(nn.Module):
    """A mini-network that generates channel-wise gates conditioned on input tensor."""

    def __init__(self, in_channels, num_gates=None, return_gates=False, gate_activation='sigmoid', reduction=16, layer_norm=False):
        super(ChannelGate, self).__init__()
        if num_gates is None:
            num_gates = in_channels
        self.return_gates = return_gates
        self.global_avgpool = nn.AdaptiveAvgPool2d(1)
        self.fc1 = nn.Conv2d(in_channels, in_channels // reduction, kernel_size=1, bias=True, padding=0)
        self.norm1 = None
        if layer_norm:
            self.norm1 = nn.LayerNorm((in_channels // reduction, 1, 1))
        self.relu = nn.ReLU(inplace=True)
        self.fc2 = nn.Conv2d(in_channels // reduction, num_gates, kernel_size=1, bias=True, padding=0)
        if gate_activation == 'sigmoid':
            self.gate_activation = nn.Sigmoid()
        elif gate_activation == 'relu':
            self.gate_activation = nn.ReLU(inplace=True)
        elif gate_activation == 'linear':
            self.gate_activation = None
        else:
            raise RuntimeError('Unknown gate activation: {}'.format(gate_activation))

    def forward(self, x):
        input = x
        x = self.global_avgpool(x)
        x = self.fc1(x)
        if self.norm1 is not None:
            x = self.norm1(x)
        x = self.relu(x)
        x = self.fc2(x)
        if self.gate_activation is not None:
            x = self.gate_activation(x)
        if self.return_gates:
            return x
        return input * x

def forward(self, x):
    input = x
    x = self.global_avgpool(x)
    x = self.fc1(x)
    if self.norm1 is not None:
        x = self.norm1(x)
    x = self.relu(x)
    x = self.fc2(x)
    if self.gate_activation is not None:
        x = self.gate_activation(x)
    if self.return_gates:
        return x
    return input * x

class OSBlock(nn.Module):
    """Omni-scale feature learning block."""

    def __init__(self, in_channels, out_channels, IN=False, bottleneck_reduction=4, **kwargs):
        super(OSBlock, self).__init__()
        mid_channels = out_channels // bottleneck_reduction
        self.conv1 = Conv1x1(in_channels, mid_channels)
        self.conv2a = LightConv3x3(mid_channels, mid_channels)
        self.conv2b = nn.Sequential(LightConv3x3(mid_channels, mid_channels), LightConv3x3(mid_channels, mid_channels))
        self.conv2c = nn.Sequential(LightConv3x3(mid_channels, mid_channels), LightConv3x3(mid_channels, mid_channels), LightConv3x3(mid_channels, mid_channels))
        self.conv2d = nn.Sequential(LightConv3x3(mid_channels, mid_channels), LightConv3x3(mid_channels, mid_channels), LightConv3x3(mid_channels, mid_channels), LightConv3x3(mid_channels, mid_channels))
        self.gate = ChannelGate(mid_channels)
        self.conv3 = Conv1x1Linear(mid_channels, out_channels)
        self.downsample = None
        if in_channels != out_channels:
            self.downsample = Conv1x1Linear(in_channels, out_channels)
        self.IN = None
        if IN:
            self.IN = nn.InstanceNorm2d(out_channels, affine=True)

    def forward(self, x):
        identity = x
        x1 = self.conv1(x)
        x2a = self.conv2a(x1)
        x2b = self.conv2b(x1)
        x2c = self.conv2c(x1)
        x2d = self.conv2d(x1)
        x2 = self.gate(x2a) + self.gate(x2b) + self.gate(x2c) + self.gate(x2d)
        x3 = self.conv3(x2)
        if self.downsample is not None:
            identity = self.downsample(identity)
        out = x3 + identity
        if self.IN is not None:
            out = self.IN(out)
        return F.relu(out)

def forward(self, x):
    identity = x
    x1 = self.conv1(x)
    x2a = self.conv2a(x1)
    x2b = self.conv2b(x1)
    x2c = self.conv2c(x1)
    x2d = self.conv2d(x1)
    x2 = self.gate(x2a) + self.gate(x2b) + self.gate(x2c) + self.gate(x2d)
    x3 = self.conv3(x2)
    if self.downsample is not None:
        identity = self.downsample(identity)
    out = x3 + identity
    if self.IN is not None:
        out = self.IN(out)
    return F.relu(out)

class OSNet(nn.Module):
    """Omni-Scale Network.
    
    Reference:
        - Zhou et al. Omni-Scale Feature Learning for Person Re-Identification. ICCV, 2019.
        - Zhou et al. Learning Generalisable Omni-Scale Representations
          for Person Re-Identification. TPAMI, 2021.
    """

    def __init__(self, num_classes, blocks, layers, channels, feature_dim=512, loss='softmax', IN=False, **kwargs):
        super(OSNet, self).__init__()
        num_blocks = len(blocks)
        assert num_blocks == len(layers)
        assert num_blocks == len(channels) - 1
        self.loss = loss
        self.feature_dim = feature_dim
        self.conv1 = ConvLayer(3, channels[0], 7, stride=2, padding=3, IN=IN)
        self.maxpool = nn.MaxPool2d(3, stride=2, padding=1)
        self.conv2 = self._make_layer(blocks[0], layers[0], channels[0], channels[1], reduce_spatial_size=True, IN=IN)
        self.conv3 = self._make_layer(blocks[1], layers[1], channels[1], channels[2], reduce_spatial_size=True)
        self.conv4 = self._make_layer(blocks[2], layers[2], channels[2], channels[3], reduce_spatial_size=False)
        self.conv5 = Conv1x1(channels[3], channels[3])
        self.global_avgpool = nn.AdaptiveAvgPool2d(1)
        self.fc = self._construct_fc_layer(self.feature_dim, channels[3], dropout_p=None)
        self.classifier = nn.Linear(self.feature_dim, num_classes)
        self._init_params()

    def _make_layer(self, block, layer, in_channels, out_channels, reduce_spatial_size, IN=False):
        layers = []
        layers.append(block(in_channels, out_channels, IN=IN))
        for i in range(1, layer):
            layers.append(block(out_channels, out_channels, IN=IN))
        if reduce_spatial_size:
            layers.append(nn.Sequential(Conv1x1(out_channels, out_channels), nn.AvgPool2d(2, stride=2)))
        return nn.Sequential(*layers)

    def _construct_fc_layer(self, fc_dims, input_dim, dropout_p=None):
        if fc_dims is None or fc_dims < 0:
            self.feature_dim = input_dim
            return None
        if isinstance(fc_dims, int):
            fc_dims = [fc_dims]
        layers = []
        for dim in fc_dims:
            layers.append(nn.Linear(input_dim, dim))
            layers.append(nn.BatchNorm1d(dim))
            layers.append(nn.ReLU(inplace=True))
            if dropout_p is not None:
                layers.append(nn.Dropout(p=dropout_p))
            input_dim = dim
        self.feature_dim = fc_dims[-1]
        return nn.Sequential(*layers)

    def _init_params(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)

    def featuremaps(self, x):
        x = self.conv1(x)
        x = self.maxpool(x)
        x = self.conv2(x)
        x = self.conv3(x)
        x = self.conv4(x)
        x = self.conv5(x)
        return x

    def forward(self, x, return_featuremaps=False):
        x = self.featuremaps(x)
        if return_featuremaps:
            return x
        v = self.global_avgpool(x)
        v = v.view(v.size(0), -1)
        if self.fc is not None:
            v = self.fc(v)
        if not self.training:
            return v
        y = self.classifier(v)
        if self.loss == 'softmax':
            return y
        elif self.loss == 'triplet':
            return (y, v)
        else:
            raise KeyError('Unsupported loss: {}'.format(self.loss))

def featuremaps(self, x):
    x = self.conv1(x)
    x = self.maxpool(x)
    x = self.conv2(x)
    x = self.conv3(x)
    x = self.conv4(x)
    x = self.conv5(x)
    return x

class BasicBlock(nn.Module):
    expansion = 1

    def __init__(self, inplanes, planes, stride=1, downsample=None):
        super(BasicBlock, self).__init__()
        self.conv1 = conv3x3(inplanes, planes, stride)
        self.bn1 = nn.BatchNorm2d(planes)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = conv3x3(planes, planes)
        self.bn2 = nn.BatchNorm2d(planes)
        self.downsample = downsample
        self.stride = stride

    def forward(self, x):
        residual = x
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)
        out = self.conv2(out)
        out = self.bn2(out)
        if self.downsample is not None:
            residual = self.downsample(x)
        out += residual
        out = self.relu(out)
        return out

def forward(self, x):
    residual = x
    out = self.conv1(x)
    out = self.bn1(out)
    out = self.relu(out)
    out = self.conv2(out)
    out = self.bn2(out)
    if self.downsample is not None:
        residual = self.downsample(x)
    out += residual
    out = self.relu(out)
    return out

class Bottleneck(nn.Module):
    expansion = 4

    def __init__(self, inplanes, planes, ibn=False, stride=1, downsample=None):
        super(Bottleneck, self).__init__()
        self.conv1 = nn.Conv2d(inplanes, planes, kernel_size=1, bias=False)
        if ibn:
            self.bn1 = IBN(planes)
        else:
            self.bn1 = nn.BatchNorm2d(planes)
        self.conv2 = nn.Conv2d(planes, planes, kernel_size=3, stride=stride, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(planes)
        self.conv3 = nn.Conv2d(planes, planes * self.expansion, kernel_size=1, bias=False)
        self.bn3 = nn.BatchNorm2d(planes * self.expansion)
        self.relu = nn.ReLU(inplace=True)
        self.downsample = downsample
        self.stride = stride

    def forward(self, x):
        residual = x
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)
        out = self.conv2(out)
        out = self.bn2(out)
        out = self.relu(out)
        out = self.conv3(out)
        out = self.bn3(out)
        if self.downsample is not None:
            residual = self.downsample(x)
        out += residual
        out = self.relu(out)
        return out

def forward(self, x):
    residual = x
    out = self.conv1(x)
    out = self.bn1(out)
    out = self.relu(out)
    out = self.conv2(out)
    out = self.bn2(out)
    out = self.relu(out)
    out = self.conv3(out)
    out = self.bn3(out)
    if self.downsample is not None:
        residual = self.downsample(x)
    out += residual
    out = self.relu(out)
    return out

class ResNet(nn.Module):
    """Residual network + IBN layer.
    
    Reference:
        - He et al. Deep Residual Learning for Image Recognition. CVPR 2016.
        - Pan et al. Two at Once: Enhancing Learning and Generalization
          Capacities via IBN-Net. ECCV 2018.
    """

    def __init__(self, block, layers, num_classes=1000, loss='softmax', fc_dims=None, dropout_p=None, **kwargs):
        scale = 64
        self.inplanes = scale
        super(ResNet, self).__init__()
        self.loss = loss
        self.feature_dim = scale * 8 * block.expansion
        self.conv1 = nn.Conv2d(3, scale, kernel_size=7, stride=2, padding=3, bias=False)
        self.bn1 = nn.BatchNorm2d(scale)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        self.layer1 = self._make_layer(block, scale, layers[0])
        self.layer2 = self._make_layer(block, scale * 2, layers[1], stride=2)
        self.layer3 = self._make_layer(block, scale * 4, layers[2], stride=2)
        self.layer4 = self._make_layer(block, scale * 8, layers[3], stride=2)
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = self._construct_fc_layer(fc_dims, scale * 8 * block.expansion, dropout_p)
        self.classifier = nn.Linear(self.feature_dim, num_classes)
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                n = m.kernel_size[0] * m.kernel_size[1] * m.out_channels
                m.weight.data.normal_(0, math.sqrt(2.0 / n))
            elif isinstance(m, nn.BatchNorm2d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()
            elif isinstance(m, nn.InstanceNorm2d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()

    def _make_layer(self, block, planes, blocks, stride=1):
        downsample = None
        if stride != 1 or self.inplanes != planes * block.expansion:
            downsample = nn.Sequential(nn.Conv2d(self.inplanes, planes * block.expansion, kernel_size=1, stride=stride, bias=False), nn.BatchNorm2d(planes * block.expansion))
        layers = []
        ibn = True
        if planes == 512:
            ibn = False
        layers.append(block(self.inplanes, planes, ibn, stride, downsample))
        self.inplanes = planes * block.expansion
        for i in range(1, blocks):
            layers.append(block(self.inplanes, planes, ibn))
        return nn.Sequential(*layers)

    def _construct_fc_layer(self, fc_dims, input_dim, dropout_p=None):
        """Constructs fully connected layer

        Args:
            fc_dims (list or tuple): dimensions of fc layers, if None, no fc layers are constructed
            input_dim (int): input dimension
            dropout_p (float): dropout probability, if None, dropout is unused
        """
        if fc_dims is None:
            self.feature_dim = input_dim
            return None
        assert isinstance(fc_dims, (list, tuple)), 'fc_dims must be either list or tuple, but got {}'.format(type(fc_dims))
        layers = []
        for dim in fc_dims:
            layers.append(nn.Linear(input_dim, dim))
            layers.append(nn.BatchNorm1d(dim))
            layers.append(nn.ReLU(inplace=True))
            if dropout_p is not None:
                layers.append(nn.Dropout(p=dropout_p))
            input_dim = dim
        self.feature_dim = fc_dims[-1]
        return nn.Sequential(*layers)

    def featuremaps(self, x):
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)
        return x

    def forward(self, x):
        f = self.featuremaps(x)
        v = self.avgpool(f)
        v = v.view(v.size(0), -1)
        if self.fc is not None:
            v = self.fc(v)
        if not self.training:
            return v
        y = self.classifier(v)
        if self.loss == 'softmax':
            return y
        elif self.loss == 'triplet':
            return (y, v)
        else:
            raise KeyError('Unsupported loss: {}'.format(self.loss))

def featuremaps(self, x):
    x = self.conv1(x)
    x = self.bn1(x)
    x = self.relu(x)
    x = self.maxpool(x)
    x = self.layer1(x)
    x = self.layer2(x)
    x = self.layer3(x)
    x = self.layer4(x)
    return x

class InvertedResidual(nn.Module):

    def __init__(self, inp, oup, stride):
        super(InvertedResidual, self).__init__()
        if not 1 <= stride <= 3:
            raise ValueError('illegal stride value')
        self.stride = stride
        branch_features = oup // 2
        assert self.stride != 1 or inp == branch_features << 1
        if self.stride > 1:
            self.branch1 = nn.Sequential(self.depthwise_conv(inp, inp, kernel_size=3, stride=self.stride, padding=1), nn.BatchNorm2d(inp), nn.Conv2d(inp, branch_features, kernel_size=1, stride=1, padding=0, bias=False), nn.BatchNorm2d(branch_features), nn.ReLU(inplace=True))
        self.branch2 = nn.Sequential(nn.Conv2d(inp if self.stride > 1 else branch_features, branch_features, kernel_size=1, stride=1, padding=0, bias=False), nn.BatchNorm2d(branch_features), nn.ReLU(inplace=True), self.depthwise_conv(branch_features, branch_features, kernel_size=3, stride=self.stride, padding=1), nn.BatchNorm2d(branch_features), nn.Conv2d(branch_features, branch_features, kernel_size=1, stride=1, padding=0, bias=False), nn.BatchNorm2d(branch_features), nn.ReLU(inplace=True))

    @staticmethod
    def depthwise_conv(i, o, kernel_size, stride=1, padding=0, bias=False):
        return nn.Conv2d(i, o, kernel_size, stride, padding, bias=bias, groups=i)

    def forward(self, x):
        if self.stride == 1:
            x1, x2 = x.chunk(2, dim=1)
            out = torch.cat((x1, self.branch2(x2)), dim=1)
        else:
            out = torch.cat((self.branch1(x), self.branch2(x)), dim=1)
        out = channel_shuffle(out, 2)
        return out

def forward(self, x):
    if self.stride == 1:
        x1, x2 = x.chunk(2, dim=1)
        out = torch.cat((x1, self.branch2(x2)), dim=1)
    else:
        out = torch.cat((self.branch1(x), self.branch2(x)), dim=1)
    out = channel_shuffle(out, 2)
    return out

class ShuffleNetV2(nn.Module):
    """ShuffleNetV2.
    
    Reference:
        Ma et al. ShuffleNet V2: Practical Guidelines for Efficient CNN Architecture Design. ECCV 2018.

    Public keys:
        - ``shufflenet_v2_x0_5``: ShuffleNetV2 x0.5.
        - ``shufflenet_v2_x1_0``: ShuffleNetV2 x1.0.
        - ``shufflenet_v2_x1_5``: ShuffleNetV2 x1.5.
        - ``shufflenet_v2_x2_0``: ShuffleNetV2 x2.0.
    """

    def __init__(self, num_classes, loss, stages_repeats, stages_out_channels, **kwargs):
        super(ShuffleNetV2, self).__init__()
        self.loss = loss
        if len(stages_repeats) != 3:
            raise ValueError('expected stages_repeats as list of 3 positive ints')
        if len(stages_out_channels) != 5:
            raise ValueError('expected stages_out_channels as list of 5 positive ints')
        self._stage_out_channels = stages_out_channels
        input_channels = 3
        output_channels = self._stage_out_channels[0]
        self.conv1 = nn.Sequential(nn.Conv2d(input_channels, output_channels, 3, 2, 1, bias=False), nn.BatchNorm2d(output_channels), nn.ReLU(inplace=True))
        input_channels = output_channels
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        stage_names = ['stage{}'.format(i) for i in [2, 3, 4]]
        for name, repeats, output_channels in zip(stage_names, stages_repeats, self._stage_out_channels[1:]):
            seq = [InvertedResidual(input_channels, output_channels, 2)]
            for i in range(repeats - 1):
                seq.append(InvertedResidual(output_channels, output_channels, 1))
            setattr(self, name, nn.Sequential(*seq))
            input_channels = output_channels
        output_channels = self._stage_out_channels[-1]
        self.conv5 = nn.Sequential(nn.Conv2d(input_channels, output_channels, 1, 1, 0, bias=False), nn.BatchNorm2d(output_channels), nn.ReLU(inplace=True))
        self.global_avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.classifier = nn.Linear(output_channels, num_classes)

    def featuremaps(self, x):
        x = self.conv1(x)
        x = self.maxpool(x)
        x = self.stage2(x)
        x = self.stage3(x)
        x = self.stage4(x)
        x = self.conv5(x)
        return x

    def forward(self, x):
        f = self.featuremaps(x)
        v = self.global_avgpool(f)
        v = v.view(v.size(0), -1)
        if not self.training:
            return v
        y = self.classifier(v)
        if self.loss == 'softmax':
            return y
        elif self.loss == 'triplet':
            return (y, v)
        else:
            raise KeyError('Unsupported loss: {}'.format(self.loss))

def featuremaps(self, x):
    x = self.conv1(x)
    x = self.maxpool(x)
    x = self.stage2(x)
    x = self.stage3(x)
    x = self.stage4(x)
    x = self.conv5(x)
    return x

class BasicBlock(nn.Module):
    expansion = 1

    def __init__(self, inplanes, planes, stride=1, downsample=None):
        super(BasicBlock, self).__init__()
        self.conv1 = conv3x3(inplanes, planes, stride)
        self.bn1 = nn.BatchNorm2d(planes)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = conv3x3(planes, planes)
        self.bn2 = nn.BatchNorm2d(planes)
        self.downsample = downsample
        self.stride = stride

    def forward(self, x):
        residual = x
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)
        out = self.conv2(out)
        out = self.bn2(out)
        if self.downsample is not None:
            residual = self.downsample(x)
        out += residual
        out = self.relu(out)
        return out

def forward(self, x):
    residual = x
    out = self.conv1(x)
    out = self.bn1(out)
    out = self.relu(out)
    out = self.conv2(out)
    out = self.bn2(out)
    if self.downsample is not None:
        residual = self.downsample(x)
    out += residual
    out = self.relu(out)
    return out

class Bottleneck(nn.Module):
    expansion = 4

    def __init__(self, inplanes, planes, stride=1, downsample=None):
        super(Bottleneck, self).__init__()
        self.conv1 = nn.Conv2d(inplanes, planes, kernel_size=1, bias=False)
        self.bn1 = nn.BatchNorm2d(planes)
        self.conv2 = nn.Conv2d(planes, planes, kernel_size=3, stride=stride, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(planes)
        self.conv3 = nn.Conv2d(planes, planes * self.expansion, kernel_size=1, bias=False)
        self.bn3 = nn.BatchNorm2d(planes * self.expansion)
        self.relu = nn.ReLU(inplace=True)
        self.downsample = downsample
        self.stride = stride

    def forward(self, x):
        residual = x
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)
        out = self.conv2(out)
        out = self.bn2(out)
        out = self.relu(out)
        out = self.conv3(out)
        out = self.bn3(out)
        if self.downsample is not None:
            residual = self.downsample(x)
        out += residual
        out = self.relu(out)
        return out

def forward(self, x):
    residual = x
    out = self.conv1(x)
    out = self.bn1(out)
    out = self.relu(out)
    out = self.conv2(out)
    out = self.bn2(out)
    out = self.relu(out)
    out = self.conv3(out)
    out = self.bn3(out)
    if self.downsample is not None:
        residual = self.downsample(x)
    out += residual
    out = self.relu(out)
    return out

class ResNetMid(nn.Module):
    """Residual network + mid-level features.
    
    Reference:
        Yu et al. The Devil is in the Middle: Exploiting Mid-level Representations for
        Cross-Domain Instance Matching. arXiv:1711.08106.

    Public keys:
        - ``resnet50mid``: ResNet50 + mid-level feature fusion.
    """

    def __init__(self, num_classes, loss, block, layers, last_stride=2, fc_dims=None, **kwargs):
        self.inplanes = 64
        super(ResNetMid, self).__init__()
        self.loss = loss
        self.feature_dim = 512 * block.expansion
        self.conv1 = nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3, bias=False)
        self.bn1 = nn.BatchNorm2d(64)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        self.layer1 = self._make_layer(block, 64, layers[0])
        self.layer2 = self._make_layer(block, 128, layers[1], stride=2)
        self.layer3 = self._make_layer(block, 256, layers[2], stride=2)
        self.layer4 = self._make_layer(block, 512, layers[3], stride=last_stride)
        self.global_avgpool = nn.AdaptiveAvgPool2d(1)
        assert fc_dims is not None
        self.fc_fusion = self._construct_fc_layer(fc_dims, 512 * block.expansion * 2)
        self.feature_dim += 512 * block.expansion
        self.classifier = nn.Linear(self.feature_dim, num_classes)
        self._init_params()

    def _make_layer(self, block, planes, blocks, stride=1):
        downsample = None
        if stride != 1 or self.inplanes != planes * block.expansion:
            downsample = nn.Sequential(nn.Conv2d(self.inplanes, planes * block.expansion, kernel_size=1, stride=stride, bias=False), nn.BatchNorm2d(planes * block.expansion))
        layers = []
        layers.append(block(self.inplanes, planes, stride, downsample))
        self.inplanes = planes * block.expansion
        for i in range(1, blocks):
            layers.append(block(self.inplanes, planes))
        return nn.Sequential(*layers)

    def _construct_fc_layer(self, fc_dims, input_dim, dropout_p=None):
        """Constructs fully connected layer

        Args:
            fc_dims (list or tuple): dimensions of fc layers, if None, no fc layers are constructed
            input_dim (int): input dimension
            dropout_p (float): dropout probability, if None, dropout is unused
        """
        if fc_dims is None:
            self.feature_dim = input_dim
            return None
        assert isinstance(fc_dims, (list, tuple)), 'fc_dims must be either list or tuple, but got {}'.format(type(fc_dims))
        layers = []
        for dim in fc_dims:
            layers.append(nn.Linear(input_dim, dim))
            layers.append(nn.BatchNorm1d(dim))
            layers.append(nn.ReLU(inplace=True))
            if dropout_p is not None:
                layers.append(nn.Dropout(p=dropout_p))
            input_dim = dim
        self.feature_dim = fc_dims[-1]
        return nn.Sequential(*layers)

    def _init_params(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)

    def featuremaps(self, x):
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x4a = self.layer4[0](x)
        x4b = self.layer4[1](x4a)
        x4c = self.layer4[2](x4b)
        return (x4a, x4b, x4c)

    def forward(self, x):
        x4a, x4b, x4c = self.featuremaps(x)
        v4a = self.global_avgpool(x4a)
        v4b = self.global_avgpool(x4b)
        v4c = self.global_avgpool(x4c)
        v4ab = torch.cat([v4a, v4b], 1)
        v4ab = v4ab.view(v4ab.size(0), -1)
        v4ab = self.fc_fusion(v4ab)
        v4c = v4c.view(v4c.size(0), -1)
        v = torch.cat([v4ab, v4c], 1)
        if not self.training:
            return v
        y = self.classifier(v)
        if self.loss == 'softmax':
            return y
        elif self.loss == 'triplet':
            return (y, v)
        else:
            raise KeyError('Unsupported loss: {}'.format(self.loss))

def featuremaps(self, x):
    x = self.conv1(x)
    x = self.bn1(x)
    x = self.relu(x)
    x = self.maxpool(x)
    x = self.layer1(x)
    x = self.layer2(x)
    x = self.layer3(x)
    x4a = self.layer4[0](x)
    x4b = self.layer4[1](x4a)
    x4c = self.layer4[2](x4b)
    return (x4a, x4b, x4c)

class BasicConv2d(nn.Module):

    def __init__(self, in_planes, out_planes, kernel_size, stride, padding=0):
        super(BasicConv2d, self).__init__()
        self.conv = nn.Conv2d(in_planes, out_planes, kernel_size=kernel_size, stride=stride, padding=padding, bias=False)
        self.bn = nn.BatchNorm2d(out_planes, eps=0.001, momentum=0.1, affine=True)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        x = self.conv(x)
        x = self.bn(x)
        x = self.relu(x)
        return x

def forward(self, x):
    x = self.conv(x)
    x = self.bn(x)
    x = self.relu(x)
    return x

class Mixed_3a(nn.Module):

    def __init__(self):
        super(Mixed_3a, self).__init__()
        self.maxpool = nn.MaxPool2d(3, stride=2)
        self.conv = BasicConv2d(64, 96, kernel_size=3, stride=2)

    def forward(self, x):
        x0 = self.maxpool(x)
        x1 = self.conv(x)
        out = torch.cat((x0, x1), 1)
        return out

def forward(self, x):
    x0 = self.maxpool(x)
    x1 = self.conv(x)
    out = torch.cat((x0, x1), 1)
    return out

class Mixed_4a(nn.Module):

    def __init__(self):
        super(Mixed_4a, self).__init__()
        self.branch0 = nn.Sequential(BasicConv2d(160, 64, kernel_size=1, stride=1), BasicConv2d(64, 96, kernel_size=3, stride=1))
        self.branch1 = nn.Sequential(BasicConv2d(160, 64, kernel_size=1, stride=1), BasicConv2d(64, 64, kernel_size=(1, 7), stride=1, padding=(0, 3)), BasicConv2d(64, 64, kernel_size=(7, 1), stride=1, padding=(3, 0)), BasicConv2d(64, 96, kernel_size=(3, 3), stride=1))

    def forward(self, x):
        x0 = self.branch0(x)
        x1 = self.branch1(x)
        out = torch.cat((x0, x1), 1)
        return out

def forward(self, x):
    x0 = self.branch0(x)
    x1 = self.branch1(x)
    out = torch.cat((x0, x1), 1)
    return out

class Mixed_5a(nn.Module):

    def __init__(self):
        super(Mixed_5a, self).__init__()
        self.conv = BasicConv2d(192, 192, kernel_size=3, stride=2)
        self.maxpool = nn.MaxPool2d(3, stride=2)

    def forward(self, x):
        x0 = self.conv(x)
        x1 = self.maxpool(x)
        out = torch.cat((x0, x1), 1)
        return out

def forward(self, x):
    x0 = self.conv(x)
    x1 = self.maxpool(x)
    out = torch.cat((x0, x1), 1)
    return out

class Inception_A(nn.Module):

    def __init__(self):
        super(Inception_A, self).__init__()
        self.branch0 = BasicConv2d(384, 96, kernel_size=1, stride=1)
        self.branch1 = nn.Sequential(BasicConv2d(384, 64, kernel_size=1, stride=1), BasicConv2d(64, 96, kernel_size=3, stride=1, padding=1))
        self.branch2 = nn.Sequential(BasicConv2d(384, 64, kernel_size=1, stride=1), BasicConv2d(64, 96, kernel_size=3, stride=1, padding=1), BasicConv2d(96, 96, kernel_size=3, stride=1, padding=1))
        self.branch3 = nn.Sequential(nn.AvgPool2d(3, stride=1, padding=1, count_include_pad=False), BasicConv2d(384, 96, kernel_size=1, stride=1))

    def forward(self, x):
        x0 = self.branch0(x)
        x1 = self.branch1(x)
        x2 = self.branch2(x)
        x3 = self.branch3(x)
        out = torch.cat((x0, x1, x2, x3), 1)
        return out

def forward(self, x):
    x0 = self.branch0(x)
    x1 = self.branch1(x)
    x2 = self.branch2(x)
    x3 = self.branch3(x)
    out = torch.cat((x0, x1, x2, x3), 1)
    return out

class Reduction_A(nn.Module):

    def __init__(self):
        super(Reduction_A, self).__init__()
        self.branch0 = BasicConv2d(384, 384, kernel_size=3, stride=2)
        self.branch1 = nn.Sequential(BasicConv2d(384, 192, kernel_size=1, stride=1), BasicConv2d(192, 224, kernel_size=3, stride=1, padding=1), BasicConv2d(224, 256, kernel_size=3, stride=2))
        self.branch2 = nn.MaxPool2d(3, stride=2)

    def forward(self, x):
        x0 = self.branch0(x)
        x1 = self.branch1(x)
        x2 = self.branch2(x)
        out = torch.cat((x0, x1, x2), 1)
        return out

def forward(self, x):
    x0 = self.branch0(x)
    x1 = self.branch1(x)
    x2 = self.branch2(x)
    out = torch.cat((x0, x1, x2), 1)
    return out

class Inception_B(nn.Module):

    def __init__(self):
        super(Inception_B, self).__init__()
        self.branch0 = BasicConv2d(1024, 384, kernel_size=1, stride=1)
        self.branch1 = nn.Sequential(BasicConv2d(1024, 192, kernel_size=1, stride=1), BasicConv2d(192, 224, kernel_size=(1, 7), stride=1, padding=(0, 3)), BasicConv2d(224, 256, kernel_size=(7, 1), stride=1, padding=(3, 0)))
        self.branch2 = nn.Sequential(BasicConv2d(1024, 192, kernel_size=1, stride=1), BasicConv2d(192, 192, kernel_size=(7, 1), stride=1, padding=(3, 0)), BasicConv2d(192, 224, kernel_size=(1, 7), stride=1, padding=(0, 3)), BasicConv2d(224, 224, kernel_size=(7, 1), stride=1, padding=(3, 0)), BasicConv2d(224, 256, kernel_size=(1, 7), stride=1, padding=(0, 3)))
        self.branch3 = nn.Sequential(nn.AvgPool2d(3, stride=1, padding=1, count_include_pad=False), BasicConv2d(1024, 128, kernel_size=1, stride=1))

    def forward(self, x):
        x0 = self.branch0(x)
        x1 = self.branch1(x)
        x2 = self.branch2(x)
        x3 = self.branch3(x)
        out = torch.cat((x0, x1, x2, x3), 1)
        return out

def forward(self, x):
    x0 = self.branch0(x)
    x1 = self.branch1(x)
    x2 = self.branch2(x)
    x3 = self.branch3(x)
    out = torch.cat((x0, x1, x2, x3), 1)
    return out

class Reduction_B(nn.Module):

    def __init__(self):
        super(Reduction_B, self).__init__()
        self.branch0 = nn.Sequential(BasicConv2d(1024, 192, kernel_size=1, stride=1), BasicConv2d(192, 192, kernel_size=3, stride=2))
        self.branch1 = nn.Sequential(BasicConv2d(1024, 256, kernel_size=1, stride=1), BasicConv2d(256, 256, kernel_size=(1, 7), stride=1, padding=(0, 3)), BasicConv2d(256, 320, kernel_size=(7, 1), stride=1, padding=(3, 0)), BasicConv2d(320, 320, kernel_size=3, stride=2))
        self.branch2 = nn.MaxPool2d(3, stride=2)

    def forward(self, x):
        x0 = self.branch0(x)
        x1 = self.branch1(x)
        x2 = self.branch2(x)
        out = torch.cat((x0, x1, x2), 1)
        return out

def forward(self, x):
    x0 = self.branch0(x)
    x1 = self.branch1(x)
    x2 = self.branch2(x)
    out = torch.cat((x0, x1, x2), 1)
    return out

class Inception_C(nn.Module):

    def __init__(self):
        super(Inception_C, self).__init__()
        self.branch0 = BasicConv2d(1536, 256, kernel_size=1, stride=1)
        self.branch1_0 = BasicConv2d(1536, 384, kernel_size=1, stride=1)
        self.branch1_1a = BasicConv2d(384, 256, kernel_size=(1, 3), stride=1, padding=(0, 1))
        self.branch1_1b = BasicConv2d(384, 256, kernel_size=(3, 1), stride=1, padding=(1, 0))
        self.branch2_0 = BasicConv2d(1536, 384, kernel_size=1, stride=1)
        self.branch2_1 = BasicConv2d(384, 448, kernel_size=(3, 1), stride=1, padding=(1, 0))
        self.branch2_2 = BasicConv2d(448, 512, kernel_size=(1, 3), stride=1, padding=(0, 1))
        self.branch2_3a = BasicConv2d(512, 256, kernel_size=(1, 3), stride=1, padding=(0, 1))
        self.branch2_3b = BasicConv2d(512, 256, kernel_size=(3, 1), stride=1, padding=(1, 0))
        self.branch3 = nn.Sequential(nn.AvgPool2d(3, stride=1, padding=1, count_include_pad=False), BasicConv2d(1536, 256, kernel_size=1, stride=1))

    def forward(self, x):
        x0 = self.branch0(x)
        x1_0 = self.branch1_0(x)
        x1_1a = self.branch1_1a(x1_0)
        x1_1b = self.branch1_1b(x1_0)
        x1 = torch.cat((x1_1a, x1_1b), 1)
        x2_0 = self.branch2_0(x)
        x2_1 = self.branch2_1(x2_0)
        x2_2 = self.branch2_2(x2_1)
        x2_3a = self.branch2_3a(x2_2)
        x2_3b = self.branch2_3b(x2_2)
        x2 = torch.cat((x2_3a, x2_3b), 1)
        x3 = self.branch3(x)
        out = torch.cat((x0, x1, x2, x3), 1)
        return out

def forward(self, x):
    x0 = self.branch0(x)
    x1_0 = self.branch1_0(x)
    x1_1a = self.branch1_1a(x1_0)
    x1_1b = self.branch1_1b(x1_0)
    x1 = torch.cat((x1_1a, x1_1b), 1)
    x2_0 = self.branch2_0(x)
    x2_1 = self.branch2_1(x2_0)
    x2_2 = self.branch2_2(x2_1)
    x2_3a = self.branch2_3a(x2_2)
    x2_3b = self.branch2_3b(x2_2)
    x2 = torch.cat((x2_3a, x2_3b), 1)
    x3 = self.branch3(x)
    out = torch.cat((x0, x1, x2, x3), 1)
    return out

class SeparableConv2d(nn.Module):

    def __init__(self, in_channels, out_channels, kernel_size=1, stride=1, padding=0, dilation=1, bias=False):
        super(SeparableConv2d, self).__init__()
        self.conv1 = nn.Conv2d(in_channels, in_channels, kernel_size, stride, padding, dilation, groups=in_channels, bias=bias)
        self.pointwise = nn.Conv2d(in_channels, out_channels, 1, 1, 0, 1, 1, bias=bias)

    def forward(self, x):
        x = self.conv1(x)
        x = self.pointwise(x)
        return x

def forward(self, x):
    x = self.conv1(x)
    x = self.pointwise(x)
    return x

class Xception(nn.Module):
    """Xception.
    
    Reference:
        Chollet. Xception: Deep Learning with Depthwise
        Separable Convolutions. CVPR 2017.

    Public keys:
        - ``xception``: Xception.
    """

    def __init__(self, num_classes, loss, fc_dims=None, dropout_p=None, **kwargs):
        super(Xception, self).__init__()
        self.loss = loss
        self.conv1 = nn.Conv2d(3, 32, 3, 2, 0, bias=False)
        self.bn1 = nn.BatchNorm2d(32)
        self.conv2 = nn.Conv2d(32, 64, 3, bias=False)
        self.bn2 = nn.BatchNorm2d(64)
        self.block1 = Block(64, 128, 2, 2, start_with_relu=False, grow_first=True)
        self.block2 = Block(128, 256, 2, 2, start_with_relu=True, grow_first=True)
        self.block3 = Block(256, 728, 2, 2, start_with_relu=True, grow_first=True)
        self.block4 = Block(728, 728, 3, 1, start_with_relu=True, grow_first=True)
        self.block5 = Block(728, 728, 3, 1, start_with_relu=True, grow_first=True)
        self.block6 = Block(728, 728, 3, 1, start_with_relu=True, grow_first=True)
        self.block7 = Block(728, 728, 3, 1, start_with_relu=True, grow_first=True)
        self.block8 = Block(728, 728, 3, 1, start_with_relu=True, grow_first=True)
        self.block9 = Block(728, 728, 3, 1, start_with_relu=True, grow_first=True)
        self.block10 = Block(728, 728, 3, 1, start_with_relu=True, grow_first=True)
        self.block11 = Block(728, 728, 3, 1, start_with_relu=True, grow_first=True)
        self.block12 = Block(728, 1024, 2, 2, start_with_relu=True, grow_first=False)
        self.conv3 = SeparableConv2d(1024, 1536, 3, 1, 1)
        self.bn3 = nn.BatchNorm2d(1536)
        self.conv4 = SeparableConv2d(1536, 2048, 3, 1, 1)
        self.bn4 = nn.BatchNorm2d(2048)
        self.global_avgpool = nn.AdaptiveAvgPool2d(1)
        self.feature_dim = 2048
        self.fc = self._construct_fc_layer(fc_dims, 2048, dropout_p)
        self.classifier = nn.Linear(self.feature_dim, num_classes)
        self._init_params()

    def _construct_fc_layer(self, fc_dims, input_dim, dropout_p=None):
        """Constructs fully connected layer.

        Args:
            fc_dims (list or tuple): dimensions of fc layers, if None, no fc layers are constructed
            input_dim (int): input dimension
            dropout_p (float): dropout probability, if None, dropout is unused
        """
        if fc_dims is None:
            self.feature_dim = input_dim
            return None
        assert isinstance(fc_dims, (list, tuple)), 'fc_dims must be either list or tuple, but got {}'.format(type(fc_dims))
        layers = []
        for dim in fc_dims:
            layers.append(nn.Linear(input_dim, dim))
            layers.append(nn.BatchNorm1d(dim))
            layers.append(nn.ReLU(inplace=True))
            if dropout_p is not None:
                layers.append(nn.Dropout(p=dropout_p))
            input_dim = dim
        self.feature_dim = fc_dims[-1]
        return nn.Sequential(*layers)

    def _init_params(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)

    def featuremaps(self, input):
        x = self.conv1(input)
        x = self.bn1(x)
        x = F.relu(x, inplace=True)
        x = self.conv2(x)
        x = self.bn2(x)
        x = F.relu(x, inplace=True)
        x = self.block1(x)
        x = self.block2(x)
        x = self.block3(x)
        x = self.block4(x)
        x = self.block5(x)
        x = self.block6(x)
        x = self.block7(x)
        x = self.block8(x)
        x = self.block9(x)
        x = self.block10(x)
        x = self.block11(x)
        x = self.block12(x)
        x = self.conv3(x)
        x = self.bn3(x)
        x = F.relu(x, inplace=True)
        x = self.conv4(x)
        x = self.bn4(x)
        x = F.relu(x, inplace=True)
        return x

    def forward(self, x):
        f = self.featuremaps(x)
        v = self.global_avgpool(f)
        v = v.view(v.size(0), -1)
        if self.fc is not None:
            v = self.fc(v)
        if not self.training:
            return v
        y = self.classifier(v)
        if self.loss == 'softmax':
            return y
        elif self.loss == 'triplet':
            return (y, v)
        else:
            raise KeyError('Unsupported loss: {}'.format(self.loss))

def featuremaps(self, input):
    x = self.conv1(input)
    x = self.bn1(x)
    x = F.relu(x, inplace=True)
    x = self.conv2(x)
    x = self.bn2(x)
    x = F.relu(x, inplace=True)
    x = self.block1(x)
    x = self.block2(x)
    x = self.block3(x)
    x = self.block4(x)
    x = self.block5(x)
    x = self.block6(x)
    x = self.block7(x)
    x = self.block8(x)
    x = self.block9(x)
    x = self.block10(x)
    x = self.block11(x)
    x = self.block12(x)
    x = self.conv3(x)
    x = self.bn3(x)
    x = F.relu(x, inplace=True)
    x = self.conv4(x)
    x = self.bn4(x)
    x = F.relu(x, inplace=True)
    return x

class BasicBlock(nn.Module):
    expansion = 1

    def __init__(self, inplanes, planes, stride=1, downsample=None):
        super(BasicBlock, self).__init__()
        self.conv1 = conv3x3(inplanes, planes, stride)
        self.bn1 = nn.BatchNorm2d(planes)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = conv3x3(planes, planes)
        self.bn2 = nn.BatchNorm2d(planes)
        self.downsample = downsample
        self.stride = stride

    def forward(self, x):
        residual = x
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)
        out = self.conv2(out)
        out = self.bn2(out)
        if self.downsample is not None:
            residual = self.downsample(x)
        out += residual
        out = self.relu(out)
        return out

def forward(self, x):
    residual = x
    out = self.conv1(x)
    out = self.bn1(out)
    out = self.relu(out)
    out = self.conv2(out)
    out = self.bn2(out)
    if self.downsample is not None:
        residual = self.downsample(x)
    out += residual
    out = self.relu(out)
    return out

class Bottleneck(nn.Module):
    expansion = 4

    def __init__(self, inplanes, planes, stride=1, downsample=None):
        super(Bottleneck, self).__init__()
        self.conv1 = nn.Conv2d(inplanes, planes, kernel_size=1, bias=False)
        self.bn1 = nn.BatchNorm2d(planes)
        self.conv2 = nn.Conv2d(planes, planes, kernel_size=3, stride=stride, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(planes)
        self.conv3 = nn.Conv2d(planes, planes * self.expansion, kernel_size=1, bias=False)
        self.bn3 = nn.BatchNorm2d(planes * self.expansion)
        self.relu = nn.ReLU(inplace=True)
        self.downsample = downsample
        self.stride = stride

    def forward(self, x):
        residual = x
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)
        out = self.conv2(out)
        out = self.bn2(out)
        out = self.relu(out)
        out = self.conv3(out)
        out = self.bn3(out)
        if self.downsample is not None:
            residual = self.downsample(x)
        out += residual
        out = self.relu(out)
        return out

def forward(self, x):
    residual = x
    out = self.conv1(x)
    out = self.bn1(out)
    out = self.relu(out)
    out = self.conv2(out)
    out = self.bn2(out)
    out = self.relu(out)
    out = self.conv3(out)
    out = self.bn3(out)
    if self.downsample is not None:
        residual = self.downsample(x)
    out += residual
    out = self.relu(out)
    return out

class DimReduceLayer(nn.Module):

    def __init__(self, in_channels, out_channels, nonlinear):
        super(DimReduceLayer, self).__init__()
        layers = []
        layers.append(nn.Conv2d(in_channels, out_channels, 1, stride=1, padding=0, bias=False))
        layers.append(nn.BatchNorm2d(out_channels))
        if nonlinear == 'relu':
            layers.append(nn.ReLU(inplace=True))
        elif nonlinear == 'leakyrelu':
            layers.append(nn.LeakyReLU(0.1))
        self.layers = nn.Sequential(*layers)

    def forward(self, x):
        return self.layers(x)

def forward(self, x):
    return self.layers(x)

class PCB(nn.Module):
    """Part-based Convolutional Baseline.

    Reference:
        Sun et al. Beyond Part Models: Person Retrieval with Refined
        Part Pooling (and A Strong Convolutional Baseline). ECCV 2018.

    Public keys:
        - ``pcb_p4``: PCB with 4-part strips.
        - ``pcb_p6``: PCB with 6-part strips.
    """

    def __init__(self, num_classes, loss, block, layers, parts=6, reduced_dim=256, nonlinear='relu', **kwargs):
        self.inplanes = 64
        super(PCB, self).__init__()
        self.loss = loss
        self.parts = parts
        self.feature_dim = 512 * block.expansion
        self.conv1 = nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3, bias=False)
        self.bn1 = nn.BatchNorm2d(64)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        self.layer1 = self._make_layer(block, 64, layers[0])
        self.layer2 = self._make_layer(block, 128, layers[1], stride=2)
        self.layer3 = self._make_layer(block, 256, layers[2], stride=2)
        self.layer4 = self._make_layer(block, 512, layers[3], stride=1)
        self.parts_avgpool = nn.AdaptiveAvgPool2d((self.parts, 1))
        self.dropout = nn.Dropout(p=0.5)
        self.conv5 = DimReduceLayer(512 * block.expansion, reduced_dim, nonlinear=nonlinear)
        self.feature_dim = reduced_dim
        self.classifier = nn.ModuleList([nn.Linear(self.feature_dim, num_classes) for _ in range(self.parts)])
        self._init_params()

    def _make_layer(self, block, planes, blocks, stride=1):
        downsample = None
        if stride != 1 or self.inplanes != planes * block.expansion:
            downsample = nn.Sequential(nn.Conv2d(self.inplanes, planes * block.expansion, kernel_size=1, stride=stride, bias=False), nn.BatchNorm2d(planes * block.expansion))
        layers = []
        layers.append(block(self.inplanes, planes, stride, downsample))
        self.inplanes = planes * block.expansion
        for i in range(1, blocks):
            layers.append(block(self.inplanes, planes))
        return nn.Sequential(*layers)

    def _init_params(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)

    def featuremaps(self, x):
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)
        return x

    def forward(self, x):
        f = self.featuremaps(x)
        v_g = self.parts_avgpool(f)
        if not self.training:
            v_g = F.normalize(v_g, p=2, dim=1)
            return v_g.view(v_g.size(0), -1)
        v_g = self.dropout(v_g)
        v_h = self.conv5(v_g)
        y = []
        for i in range(self.parts):
            v_h_i = v_h[:, :, i, :]
            v_h_i = v_h_i.view(v_h_i.size(0), -1)
            y_i = self.classifier[i](v_h_i)
            y.append(y_i)
        if self.loss == 'softmax':
            return y
        elif self.loss == 'triplet':
            v_g = F.normalize(v_g, p=2, dim=1)
            return (y, v_g.view(v_g.size(0), -1))
        else:
            raise KeyError('Unsupported loss: {}'.format(self.loss))

def featuremaps(self, x):
    x = self.conv1(x)
    x = self.bn1(x)
    x = self.relu(x)
    x = self.maxpool(x)
    x = self.layer1(x)
    x = self.layer2(x)
    x = self.layer3(x)
    x = self.layer4(x)
    return x

class ConvLayer(nn.Module):
    """Convolution layer (conv + bn + relu)."""

    def __init__(self, in_channels, out_channels, kernel_size, stride=1, padding=0, groups=1, IN=False):
        super(ConvLayer, self).__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size, stride=stride, padding=padding, bias=False, groups=groups)
        if IN:
            self.bn = nn.InstanceNorm2d(out_channels, affine=True)
        else:
            self.bn = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.conv(x)
        x = self.bn(x)
        return self.relu(x)

def forward(self, x):
    x = self.conv(x)
    x = self.bn(x)
    return self.relu(x)

class Conv1x1(nn.Module):
    """1x1 convolution + bn + relu."""

    def __init__(self, in_channels, out_channels, stride=1, groups=1):
        super(Conv1x1, self).__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, 1, stride=stride, padding=0, bias=False, groups=groups)
        self.bn = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.conv(x)
        x = self.bn(x)
        return self.relu(x)

def forward(self, x):
    x = self.conv(x)
    x = self.bn(x)
    return self.relu(x)

class Conv1x1Linear(nn.Module):
    """1x1 convolution + bn (w/o non-linearity)."""

    def __init__(self, in_channels, out_channels, stride=1, bn=True):
        super(Conv1x1Linear, self).__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, 1, stride=stride, padding=0, bias=False)
        self.bn = None
        if bn:
            self.bn = nn.BatchNorm2d(out_channels)

    def forward(self, x):
        x = self.conv(x)
        if self.bn is not None:
            x = self.bn(x)
        return x

def forward(self, x):
    x = self.conv(x)
    if self.bn is not None:
        x = self.bn(x)
    return x

class Conv3x3(nn.Module):
    """3x3 convolution + bn + relu."""

    def __init__(self, in_channels, out_channels, stride=1, groups=1):
        super(Conv3x3, self).__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, 3, stride=stride, padding=1, bias=False, groups=groups)
        self.bn = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.conv(x)
        x = self.bn(x)
        return self.relu(x)

def forward(self, x):
    x = self.conv(x)
    x = self.bn(x)
    return self.relu(x)

class LightConv3x3(nn.Module):
    """Lightweight 3x3 convolution.

    1x1 (linear) + dw 3x3 (nonlinear).
    """

    def __init__(self, in_channels, out_channels):
        super(LightConv3x3, self).__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, 1, stride=1, padding=0, bias=False)
        self.conv2 = nn.Conv2d(out_channels, out_channels, 3, stride=1, padding=1, bias=False, groups=out_channels)
        self.bn = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.bn(x)
        return self.relu(x)

def forward(self, x):
    x = self.conv1(x)
    x = self.conv2(x)
    x = self.bn(x)
    return self.relu(x)

class LightConvStream(nn.Module):
    """Lightweight convolution stream."""

    def __init__(self, in_channels, out_channels, depth):
        super(LightConvStream, self).__init__()
        assert depth >= 1, 'depth must be equal to or larger than 1, but got {}'.format(depth)
        layers = []
        layers += [LightConv3x3(in_channels, out_channels)]
        for i in range(depth - 1):
            layers += [LightConv3x3(out_channels, out_channels)]
        self.layers = nn.Sequential(*layers)

    def forward(self, x):
        return self.layers(x)

def forward(self, x):
    return self.layers(x)

class ChannelGate(nn.Module):
    """A mini-network that generates channel-wise gates conditioned on input tensor."""

    def __init__(self, in_channels, num_gates=None, return_gates=False, gate_activation='sigmoid', reduction=16, layer_norm=False):
        super(ChannelGate, self).__init__()
        if num_gates is None:
            num_gates = in_channels
        self.return_gates = return_gates
        self.global_avgpool = nn.AdaptiveAvgPool2d(1)
        self.fc1 = nn.Conv2d(in_channels, in_channels // reduction, kernel_size=1, bias=True, padding=0)
        self.norm1 = None
        if layer_norm:
            self.norm1 = nn.LayerNorm((in_channels // reduction, 1, 1))
        self.relu = nn.ReLU()
        self.fc2 = nn.Conv2d(in_channels // reduction, num_gates, kernel_size=1, bias=True, padding=0)
        if gate_activation == 'sigmoid':
            self.gate_activation = nn.Sigmoid()
        elif gate_activation == 'relu':
            self.gate_activation = nn.ReLU()
        elif gate_activation == 'linear':
            self.gate_activation = None
        else:
            raise RuntimeError('Unknown gate activation: {}'.format(gate_activation))

    def forward(self, x):
        input = x
        x = self.global_avgpool(x)
        x = self.fc1(x)
        if self.norm1 is not None:
            x = self.norm1(x)
        x = self.relu(x)
        x = self.fc2(x)
        if self.gate_activation is not None:
            x = self.gate_activation(x)
        if self.return_gates:
            return x
        return input * x

def forward(self, x):
    input = x
    x = self.global_avgpool(x)
    x = self.fc1(x)
    if self.norm1 is not None:
        x = self.norm1(x)
    x = self.relu(x)
    x = self.fc2(x)
    if self.gate_activation is not None:
        x = self.gate_activation(x)
    if self.return_gates:
        return x
    return input * x

class OSBlock(nn.Module):
    """Omni-scale feature learning block."""

    def __init__(self, in_channels, out_channels, reduction=4, T=4, **kwargs):
        super(OSBlock, self).__init__()
        assert T >= 1
        assert out_channels >= reduction and out_channels % reduction == 0
        mid_channels = out_channels // reduction
        self.conv1 = Conv1x1(in_channels, mid_channels)
        self.conv2 = nn.ModuleList()
        for t in range(1, T + 1):
            self.conv2 += [LightConvStream(mid_channels, mid_channels, t)]
        self.gate = ChannelGate(mid_channels)
        self.conv3 = Conv1x1Linear(mid_channels, out_channels)
        self.downsample = None
        if in_channels != out_channels:
            self.downsample = Conv1x1Linear(in_channels, out_channels)

    def forward(self, x):
        identity = x
        x1 = self.conv1(x)
        x2 = 0
        for conv2_t in self.conv2:
            x2_t = conv2_t(x1)
            x2 = x2 + self.gate(x2_t)
        x3 = self.conv3(x2)
        if self.downsample is not None:
            identity = self.downsample(identity)
        out = x3 + identity
        return F.relu(out)

def forward(self, x):
    identity = x
    x1 = self.conv1(x)
    x2 = 0
    for conv2_t in self.conv2:
        x2_t = conv2_t(x1)
        x2 = x2 + self.gate(x2_t)
    x3 = self.conv3(x2)
    if self.downsample is not None:
        identity = self.downsample(identity)
    out = x3 + identity
    return F.relu(out)

class OSBlockINin(nn.Module):
    """Omni-scale feature learning block with instance normalization."""

    def __init__(self, in_channels, out_channels, reduction=4, T=4, **kwargs):
        super(OSBlockINin, self).__init__()
        assert T >= 1
        assert out_channels >= reduction and out_channels % reduction == 0
        mid_channels = out_channels // reduction
        self.conv1 = Conv1x1(in_channels, mid_channels)
        self.conv2 = nn.ModuleList()
        for t in range(1, T + 1):
            self.conv2 += [LightConvStream(mid_channels, mid_channels, t)]
        self.gate = ChannelGate(mid_channels)
        self.conv3 = Conv1x1Linear(mid_channels, out_channels, bn=False)
        self.downsample = None
        if in_channels != out_channels:
            self.downsample = Conv1x1Linear(in_channels, out_channels)
        self.IN = nn.InstanceNorm2d(out_channels, affine=True)

    def forward(self, x):
        identity = x
        x1 = self.conv1(x)
        x2 = 0
        for conv2_t in self.conv2:
            x2_t = conv2_t(x1)
            x2 = x2 + self.gate(x2_t)
        x3 = self.conv3(x2)
        x3 = self.IN(x3)
        if self.downsample is not None:
            identity = self.downsample(identity)
        out = x3 + identity
        return F.relu(out)

def forward(self, x):
    identity = x
    x1 = self.conv1(x)
    x2 = 0
    for conv2_t in self.conv2:
        x2_t = conv2_t(x1)
        x2 = x2 + self.gate(x2_t)
    x3 = self.conv3(x2)
    x3 = self.IN(x3)
    if self.downsample is not None:
        identity = self.downsample(identity)
    out = x3 + identity
    return F.relu(out)

class OSNet(nn.Module):
    """Omni-Scale Network.
    
    Reference:
        - Zhou et al. Omni-Scale Feature Learning for Person Re-Identification. ICCV, 2019.
        - Zhou et al. Learning Generalisable Omni-Scale Representations
          for Person Re-Identification. TPAMI, 2021.
    """

    def __init__(self, num_classes, blocks, layers, channels, feature_dim=512, loss='softmax', conv1_IN=False, **kwargs):
        super(OSNet, self).__init__()
        num_blocks = len(blocks)
        assert num_blocks == len(layers)
        assert num_blocks == len(channels) - 1
        self.loss = loss
        self.feature_dim = feature_dim
        self.conv1 = ConvLayer(3, channels[0], 7, stride=2, padding=3, IN=conv1_IN)
        self.maxpool = nn.MaxPool2d(3, stride=2, padding=1)
        self.conv2 = self._make_layer(blocks[0], layers[0], channels[0], channels[1])
        self.pool2 = nn.Sequential(Conv1x1(channels[1], channels[1]), nn.AvgPool2d(2, stride=2))
        self.conv3 = self._make_layer(blocks[1], layers[1], channels[1], channels[2])
        self.pool3 = nn.Sequential(Conv1x1(channels[2], channels[2]), nn.AvgPool2d(2, stride=2))
        self.conv4 = self._make_layer(blocks[2], layers[2], channels[2], channels[3])
        self.conv5 = Conv1x1(channels[3], channels[3])
        self.global_avgpool = nn.AdaptiveAvgPool2d(1)
        self.fc = self._construct_fc_layer(self.feature_dim, channels[3], dropout_p=None)
        self.classifier = nn.Linear(self.feature_dim, num_classes)
        self._init_params()

    def _make_layer(self, blocks, layer, in_channels, out_channels):
        layers = []
        layers += [blocks[0](in_channels, out_channels)]
        for i in range(1, len(blocks)):
            layers += [blocks[i](out_channels, out_channels)]
        return nn.Sequential(*layers)

    def _construct_fc_layer(self, fc_dims, input_dim, dropout_p=None):
        if fc_dims is None or fc_dims < 0:
            self.feature_dim = input_dim
            return None
        if isinstance(fc_dims, int):
            fc_dims = [fc_dims]
        layers = []
        for dim in fc_dims:
            layers.append(nn.Linear(input_dim, dim))
            layers.append(nn.BatchNorm1d(dim))
            layers.append(nn.ReLU())
            if dropout_p is not None:
                layers.append(nn.Dropout(p=dropout_p))
            input_dim = dim
        self.feature_dim = fc_dims[-1]
        return nn.Sequential(*layers)

    def _init_params(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.InstanceNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)

    def featuremaps(self, x):
        x = self.conv1(x)
        x = self.maxpool(x)
        x = self.conv2(x)
        x = self.pool2(x)
        x = self.conv3(x)
        x = self.pool3(x)
        x = self.conv4(x)
        x = self.conv5(x)
        return x

    def forward(self, x, return_featuremaps=False):
        x = self.featuremaps(x)
        if return_featuremaps:
            return x
        v = self.global_avgpool(x)
        v = v.view(v.size(0), -1)
        if self.fc is not None:
            v = self.fc(v)
        if not self.training:
            return v
        y = self.classifier(v)
        if self.loss == 'softmax':
            return y
        elif self.loss == 'triplet':
            return (y, v)
        else:
            raise KeyError('Unsupported loss: {}'.format(self.loss))

def featuremaps(self, x):
    x = self.conv1(x)
    x = self.maxpool(x)
    x = self.conv2(x)
    x = self.pool2(x)
    x = self.conv3(x)
    x = self.pool3(x)
    x = self.conv4(x)
    x = self.conv5(x)
    return x

class MLFNBlock(nn.Module):

    def __init__(self, in_channels, out_channels, stride, fsm_channels, groups=32):
        super(MLFNBlock, self).__init__()
        self.groups = groups
        mid_channels = out_channels // 2
        self.fm_conv1 = nn.Conv2d(in_channels, mid_channels, 1, bias=False)
        self.fm_bn1 = nn.BatchNorm2d(mid_channels)
        self.fm_conv2 = nn.Conv2d(mid_channels, mid_channels, 3, stride=stride, padding=1, bias=False, groups=self.groups)
        self.fm_bn2 = nn.BatchNorm2d(mid_channels)
        self.fm_conv3 = nn.Conv2d(mid_channels, out_channels, 1, bias=False)
        self.fm_bn3 = nn.BatchNorm2d(out_channels)
        self.fsm = nn.Sequential(nn.AdaptiveAvgPool2d(1), nn.Conv2d(in_channels, fsm_channels[0], 1), nn.BatchNorm2d(fsm_channels[0]), nn.ReLU(inplace=True), nn.Conv2d(fsm_channels[0], fsm_channels[1], 1), nn.BatchNorm2d(fsm_channels[1]), nn.ReLU(inplace=True), nn.Conv2d(fsm_channels[1], self.groups, 1), nn.BatchNorm2d(self.groups), nn.Sigmoid())
        self.downsample = None
        if in_channels != out_channels or stride > 1:
            self.downsample = nn.Sequential(nn.Conv2d(in_channels, out_channels, 1, stride=stride, bias=False), nn.BatchNorm2d(out_channels))

    def forward(self, x):
        residual = x
        s = self.fsm(x)
        x = self.fm_conv1(x)
        x = self.fm_bn1(x)
        x = F.relu(x, inplace=True)
        x = self.fm_conv2(x)
        x = self.fm_bn2(x)
        x = F.relu(x, inplace=True)
        b, c = (x.size(0), x.size(1))
        n = c // self.groups
        ss = s.repeat(1, n, 1, 1)
        ss = ss.view(b, n, self.groups, 1, 1)
        ss = ss.permute(0, 2, 1, 3, 4).contiguous()
        ss = ss.view(b, c, 1, 1)
        x = ss * x
        x = self.fm_conv3(x)
        x = self.fm_bn3(x)
        x = F.relu(x, inplace=True)
        if self.downsample is not None:
            residual = self.downsample(residual)
        return (F.relu(residual + x, inplace=True), s)

def forward(self, x):
    residual = x
    s = self.fsm(x)
    x = self.fm_conv1(x)
    x = self.fm_bn1(x)
    x = F.relu(x, inplace=True)
    x = self.fm_conv2(x)
    x = self.fm_bn2(x)
    x = F.relu(x, inplace=True)
    b, c = (x.size(0), x.size(1))
    n = c // self.groups
    ss = s.repeat(1, n, 1, 1)
    ss = ss.view(b, n, self.groups, 1, 1)
    ss = ss.permute(0, 2, 1, 3, 4).contiguous()
    ss = ss.view(b, c, 1, 1)
    x = ss * x
    x = self.fm_conv3(x)
    x = self.fm_bn3(x)
    x = F.relu(x, inplace=True)
    if self.downsample is not None:
        residual = self.downsample(residual)
    return (F.relu(residual + x, inplace=True), s)

