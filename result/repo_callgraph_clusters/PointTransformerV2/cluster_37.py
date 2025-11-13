# Cluster 37

class Block(nn.Module):

    def __init__(self, embed_channels, groups, qkv_bias=True, pe_multiplier=False, pe_bias=True, attn_drop_rate=0.0, drop_path_rate=0.0, enable_checkpoint=False):
        super(Block, self).__init__()
        self.attn = GroupedVectorAttention(embed_channels=embed_channels, groups=groups, qkv_bias=qkv_bias, attn_drop_rate=attn_drop_rate, pe_multiplier=pe_multiplier, pe_bias=pe_bias)
        self.fc1 = nn.Linear(embed_channels, embed_channels, bias=False)
        self.fc3 = nn.Linear(embed_channels, embed_channels, bias=False)
        self.norm1 = PointBatchNorm(embed_channels)
        self.norm2 = PointBatchNorm(embed_channels)
        self.norm3 = PointBatchNorm(embed_channels)
        self.act = nn.ReLU(inplace=True)
        self.enable_checkpoint = enable_checkpoint
        self.drop_path = DropPath(drop_path_rate) if drop_path_rate > 0.0 else nn.Identity()

    def forward(self, points, reference_index):
        coord, feat, offset = points
        identity = feat
        feat = self.act(self.norm1(self.fc1(feat)))
        feat = self.attn(feat, coord, reference_index) if not self.enable_checkpoint else checkpoint(self.attn, feat, coord, reference_index)
        feat = self.act(self.norm2(feat))
        feat = self.norm3(self.fc3(feat))
        feat = identity + self.drop_path(feat)
        feat = self.act(feat)
        return [coord, feat, offset]

def forward(self, points, reference_index):
    coord, feat, offset = points
    identity = feat
    feat = self.act(self.norm1(self.fc1(feat)))
    feat = self.attn(feat, coord, reference_index) if not self.enable_checkpoint else checkpoint(self.attn, feat, coord, reference_index)
    feat = self.act(self.norm2(feat))
    feat = self.norm3(self.fc3(feat))
    feat = identity + self.drop_path(feat)
    feat = self.act(feat)
    return [coord, feat, offset]

class Block(nn.Module):

    def __init__(self, embed_channels, groups, qkv_bias=True, pe_multiplier=False, pe_bias=True, attn_drop_rate=0.0, drop_path_rate=0.0, enable_checkpoint=False):
        super(Block, self).__init__()
        self.attn = GroupedVectorAttention(embed_channels=embed_channels, groups=groups, qkv_bias=qkv_bias, attn_drop_rate=attn_drop_rate, pe_multiplier=pe_multiplier, pe_bias=pe_bias)
        self.fc1 = nn.Linear(embed_channels, embed_channels, bias=False)
        self.fc3 = nn.Linear(embed_channels, embed_channels, bias=False)
        self.norm1 = PointBatchNorm(embed_channels)
        self.norm2 = PointBatchNorm(embed_channels)
        self.norm3 = PointBatchNorm(embed_channels)
        self.act = nn.ReLU(inplace=True)
        self.enable_checkpoint = enable_checkpoint
        self.drop_path = DropPath(drop_path_rate) if drop_path_rate > 0.0 else nn.Identity()

    def forward(self, points, reference_index):
        coord, feat, offset = points
        identity = feat
        feat = self.act(self.norm1(self.fc1(feat)))
        feat = self.attn(feat, coord, reference_index) if not self.enable_checkpoint else checkpoint(self.attn, feat, coord, reference_index)
        feat = self.act(self.norm2(feat))
        feat = self.norm3(self.fc3(feat))
        feat = identity + self.drop_path(feat)
        feat = self.act(feat)
        return [coord, feat, offset]

def forward(self, points, reference_index):
    coord, feat, offset = points
    identity = feat
    feat = self.act(self.norm1(self.fc1(feat)))
    feat = self.attn(feat, coord, reference_index) if not self.enable_checkpoint else checkpoint(self.attn, feat, coord, reference_index)
    feat = self.act(self.norm2(feat))
    feat = self.norm3(self.fc3(feat))
    feat = identity + self.drop_path(feat)
    feat = self.act(feat)
    return [coord, feat, offset]

class Bottleneck(nn.Module):
    expansion = 1

    def __init__(self, in_planes, planes, share_planes=8, nsample=16):
        super(Bottleneck, self).__init__()
        self.linear1 = nn.Linear(in_planes, planes, bias=False)
        self.bn1 = nn.BatchNorm1d(planes)
        self.transformer = PointTransformerLayer(planes, planes, share_planes, nsample)
        self.bn2 = nn.BatchNorm1d(planes)
        self.linear3 = nn.Linear(planes, planes * self.expansion, bias=False)
        self.bn3 = nn.BatchNorm1d(planes * self.expansion)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, pxo):
        p, x, o = pxo
        identity = x
        x = self.relu(self.bn1(self.linear1(x)))
        x = self.relu(self.bn2(self.transformer([p, x, o])))
        x = self.bn3(self.linear3(x))
        x += identity
        x = self.relu(x)
        return [p, x, o]

def forward(self, pxo):
    p, x, o = pxo
    identity = x
    x = self.relu(self.bn1(self.linear1(x)))
    x = self.relu(self.bn2(self.transformer([p, x, o])))
    x = self.bn3(self.linear3(x))
    x += identity
    x = self.relu(x)
    return [p, x, o]

class Bottleneck(nn.Module):
    expansion = 1

    def __init__(self, in_planes, planes, share_planes=8, nsample=16):
        super(Bottleneck, self).__init__()
        self.linear1 = nn.Linear(in_planes, planes, bias=False)
        self.bn1 = nn.BatchNorm1d(planes)
        self.transformer = PointTransformerLayer(planes, planes, share_planes, nsample)
        self.bn2 = nn.BatchNorm1d(planes)
        self.linear3 = nn.Linear(planes, planes * self.expansion, bias=False)
        self.bn3 = nn.BatchNorm1d(planes * self.expansion)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, pxo):
        p, x, o = pxo
        identity = x
        x = self.relu(self.bn1(self.linear1(x)))
        x = self.relu(self.bn2(self.transformer([p, x, o])))
        x = self.bn3(self.linear3(x))
        x += identity
        x = self.relu(x)
        return [p, x, o]

def forward(self, pxo):
    p, x, o = pxo
    identity = x
    x = self.relu(self.bn1(self.linear1(x)))
    x = self.relu(self.bn2(self.transformer([p, x, o])))
    x = self.bn3(self.linear3(x))
    x += identity
    x = self.relu(x)
    return [p, x, o]

class BasicBlock(nn.Module):
    expansion = 1

    def __init__(self, inplanes, planes, stride=1, dilation=1, downsample=None, bn_momentum=0.1, dimension=-1):
        super(BasicBlock, self).__init__()
        assert dimension > 0
        self.conv1 = ME.MinkowskiConvolution(inplanes, planes, kernel_size=3, stride=stride, dilation=dilation, dimension=dimension)
        self.norm1 = ME.MinkowskiBatchNorm(planes, momentum=bn_momentum)
        self.conv2 = ME.MinkowskiConvolution(planes, planes, kernel_size=3, stride=1, dilation=dilation, dimension=dimension)
        self.norm2 = ME.MinkowskiBatchNorm(planes, momentum=bn_momentum)
        self.relu = ME.MinkowskiReLU(inplace=True)
        self.downsample = downsample

    def forward(self, x):
        residual = x
        out = self.conv1(x)
        out = self.norm1(out)
        out = self.relu(out)
        out = self.conv2(out)
        out = self.norm2(out)
        if self.downsample is not None:
            residual = self.downsample(x)
        out += residual
        out = self.relu(out)
        return out

def forward(self, x):
    residual = x
    out = self.conv1(x)
    out = self.norm1(out)
    out = self.relu(out)
    out = self.conv2(out)
    out = self.norm2(out)
    if self.downsample is not None:
        residual = self.downsample(x)
    out += residual
    out = self.relu(out)
    return out

class Bottleneck(nn.Module):
    expansion = 4

    def __init__(self, inplanes, planes, stride=1, dilation=1, downsample=None, bn_momentum=0.1, dimension=-1):
        super(Bottleneck, self).__init__()
        assert dimension > 0
        self.conv1 = ME.MinkowskiConvolution(inplanes, planes, kernel_size=1, dimension=dimension)
        self.norm1 = ME.MinkowskiBatchNorm(planes, momentum=bn_momentum)
        self.conv2 = ME.MinkowskiConvolution(planes, planes, kernel_size=3, stride=stride, dilation=dilation, dimension=dimension)
        self.norm2 = ME.MinkowskiBatchNorm(planes, momentum=bn_momentum)
        self.conv3 = ME.MinkowskiConvolution(planes, planes * self.expansion, kernel_size=1, dimension=dimension)
        self.norm3 = ME.MinkowskiBatchNorm(planes * self.expansion, momentum=bn_momentum)
        self.relu = ME.MinkowskiReLU(inplace=True)
        self.downsample = downsample

    def forward(self, x):
        residual = x
        out = self.conv1(x)
        out = self.norm1(out)
        out = self.relu(out)
        out = self.conv2(out)
        out = self.norm2(out)
        out = self.relu(out)
        out = self.conv3(out)
        out = self.norm3(out)
        if self.downsample is not None:
            residual = self.downsample(x)
        out += residual
        out = self.relu(out)
        return out

def forward(self, x):
    residual = x
    out = self.conv1(x)
    out = self.norm1(out)
    out = self.relu(out)
    out = self.conv2(out)
    out = self.norm2(out)
    out = self.relu(out)
    out = self.conv3(out)
    out = self.norm3(out)
    if self.downsample is not None:
        residual = self.downsample(x)
    out += residual
    out = self.relu(out)
    return out

class MinkUNetBase(nn.Module):
    BLOCK = None
    PLANES = None
    DILATIONS = (1, 1, 1, 1, 1, 1, 1, 1)
    LAYERS = (2, 2, 2, 2, 2, 2, 2, 2)
    PLANES = (32, 64, 128, 256, 256, 128, 96, 96)
    INIT_DIM = 32
    OUT_TENSOR_STRIDE = 1

    def __init__(self, in_channels, out_channels, dimension=3):
        super().__init__()
        self.D = dimension
        assert self.BLOCK is not None
        self.inplanes = self.INIT_DIM
        self.conv0p1s1 = ME.MinkowskiConvolution(in_channels, self.inplanes, kernel_size=5, dimension=self.D)
        self.bn0 = ME.MinkowskiBatchNorm(self.inplanes)
        self.conv1p1s2 = ME.MinkowskiConvolution(self.inplanes, self.inplanes, kernel_size=2, stride=2, dimension=self.D)
        self.bn1 = ME.MinkowskiBatchNorm(self.inplanes)
        self.block1 = self._make_layer(self.BLOCK, self.PLANES[0], self.LAYERS[0])
        self.conv2p2s2 = ME.MinkowskiConvolution(self.inplanes, self.inplanes, kernel_size=2, stride=2, dimension=self.D)
        self.bn2 = ME.MinkowskiBatchNorm(self.inplanes)
        self.block2 = self._make_layer(self.BLOCK, self.PLANES[1], self.LAYERS[1])
        self.conv3p4s2 = ME.MinkowskiConvolution(self.inplanes, self.inplanes, kernel_size=2, stride=2, dimension=self.D)
        self.bn3 = ME.MinkowskiBatchNorm(self.inplanes)
        self.block3 = self._make_layer(self.BLOCK, self.PLANES[2], self.LAYERS[2])
        self.conv4p8s2 = ME.MinkowskiConvolution(self.inplanes, self.inplanes, kernel_size=2, stride=2, dimension=self.D)
        self.bn4 = ME.MinkowskiBatchNorm(self.inplanes)
        self.block4 = self._make_layer(self.BLOCK, self.PLANES[3], self.LAYERS[3])
        self.convtr4p16s2 = ME.MinkowskiConvolutionTranspose(self.inplanes, self.PLANES[4], kernel_size=2, stride=2, dimension=self.D)
        self.bntr4 = ME.MinkowskiBatchNorm(self.PLANES[4])
        self.inplanes = self.PLANES[4] + self.PLANES[2] * self.BLOCK.expansion
        self.block5 = self._make_layer(self.BLOCK, self.PLANES[4], self.LAYERS[4])
        self.convtr5p8s2 = ME.MinkowskiConvolutionTranspose(self.inplanes, self.PLANES[5], kernel_size=2, stride=2, dimension=self.D)
        self.bntr5 = ME.MinkowskiBatchNorm(self.PLANES[5])
        self.inplanes = self.PLANES[5] + self.PLANES[1] * self.BLOCK.expansion
        self.block6 = self._make_layer(self.BLOCK, self.PLANES[5], self.LAYERS[5])
        self.convtr6p4s2 = ME.MinkowskiConvolutionTranspose(self.inplanes, self.PLANES[6], kernel_size=2, stride=2, dimension=self.D)
        self.bntr6 = ME.MinkowskiBatchNorm(self.PLANES[6])
        self.inplanes = self.PLANES[6] + self.PLANES[0] * self.BLOCK.expansion
        self.block7 = self._make_layer(self.BLOCK, self.PLANES[6], self.LAYERS[6])
        self.convtr7p2s2 = ME.MinkowskiConvolutionTranspose(self.inplanes, self.PLANES[7], kernel_size=2, stride=2, dimension=self.D)
        self.bntr7 = ME.MinkowskiBatchNorm(self.PLANES[7])
        self.inplanes = self.PLANES[7] + self.INIT_DIM
        self.block8 = self._make_layer(self.BLOCK, self.PLANES[7], self.LAYERS[7])
        self.final = ME.MinkowskiConvolution(self.PLANES[7] * self.BLOCK.expansion, out_channels, kernel_size=1, bias=True, dimension=self.D)
        self.relu = ME.MinkowskiReLU(inplace=True)
        self.weight_initialization()

    def weight_initialization(self):
        for m in self.modules():
            if isinstance(m, ME.MinkowskiConvolution):
                ME.utils.kaiming_normal_(m.kernel, mode='fan_out', nonlinearity='relu')
            if isinstance(m, ME.MinkowskiBatchNorm):
                nn.init.constant_(m.bn.weight, 1)
                nn.init.constant_(m.bn.bias, 0)

    def _make_layer(self, block, planes, blocks, stride=1, dilation=1, bn_momentum=0.1):
        downsample = None
        if stride != 1 or self.inplanes != planes * block.expansion:
            downsample = nn.Sequential(ME.MinkowskiConvolution(self.inplanes, planes * block.expansion, kernel_size=1, stride=stride, dimension=self.D), ME.MinkowskiBatchNorm(planes * block.expansion))
        layers = []
        layers.append(block(self.inplanes, planes, stride=stride, dilation=dilation, downsample=downsample, dimension=self.D))
        self.inplanes = planes * block.expansion
        for i in range(1, blocks):
            layers.append(block(self.inplanes, planes, stride=1, dilation=dilation, dimension=self.D))
        return nn.Sequential(*layers)

    def forward(self, input_dict):
        discrete_coord = input_dict['discrete_coord']
        feat = input_dict['feat']
        offset = input_dict['offset']
        batch = offset2batch(offset)
        in_field = ME.TensorField(feat, coordinates=torch.cat([batch.unsqueeze(-1).int(), discrete_coord.int()], dim=1), quantization_mode=ME.SparseTensorQuantizationMode.UNWEIGHTED_AVERAGE, minkowski_algorithm=ME.MinkowskiAlgorithm.SPEED_OPTIMIZED, device=feat.device)
        x = in_field.sparse()
        out = self.conv0p1s1(x)
        out = self.bn0(out)
        out_p1 = self.relu(out)
        out = self.conv1p1s2(out_p1)
        out = self.bn1(out)
        out = self.relu(out)
        out_b1p2 = self.block1(out)
        out = self.conv2p2s2(out_b1p2)
        out = self.bn2(out)
        out = self.relu(out)
        out_b2p4 = self.block2(out)
        out = self.conv3p4s2(out_b2p4)
        out = self.bn3(out)
        out = self.relu(out)
        out_b3p8 = self.block3(out)
        out = self.conv4p8s2(out_b3p8)
        out = self.bn4(out)
        out = self.relu(out)
        out = self.block4(out)
        out = self.convtr4p16s2(out)
        out = self.bntr4(out)
        out = self.relu(out)
        out = ME.cat(out, out_b3p8)
        out = self.block5(out)
        out = self.convtr5p8s2(out)
        out = self.bntr5(out)
        out = self.relu(out)
        out = ME.cat(out, out_b2p4)
        out = self.block6(out)
        out = self.convtr6p4s2(out)
        out = self.bntr6(out)
        out = self.relu(out)
        out = ME.cat(out, out_b1p2)
        out = self.block7(out)
        out = self.convtr7p2s2(out)
        out = self.bntr7(out)
        out = self.relu(out)
        out = ME.cat(out, out_p1)
        out = self.block8(out)
        return self.final(out).slice(in_field).F

def forward(self, input_dict):
    discrete_coord = input_dict['discrete_coord']
    feat = input_dict['feat']
    offset = input_dict['offset']
    batch = offset2batch(offset)
    in_field = ME.TensorField(feat, coordinates=torch.cat([batch.unsqueeze(-1).int(), discrete_coord.int()], dim=1), quantization_mode=ME.SparseTensorQuantizationMode.UNWEIGHTED_AVERAGE, minkowski_algorithm=ME.MinkowskiAlgorithm.SPEED_OPTIMIZED, device=feat.device)
    x = in_field.sparse()
    out = self.conv0p1s1(x)
    out = self.bn0(out)
    out_p1 = self.relu(out)
    out = self.conv1p1s2(out_p1)
    out = self.bn1(out)
    out = self.relu(out)
    out_b1p2 = self.block1(out)
    out = self.conv2p2s2(out_b1p2)
    out = self.bn2(out)
    out = self.relu(out)
    out_b2p4 = self.block2(out)
    out = self.conv3p4s2(out_b2p4)
    out = self.bn3(out)
    out = self.relu(out)
    out_b3p8 = self.block3(out)
    out = self.conv4p8s2(out_b3p8)
    out = self.bn4(out)
    out = self.relu(out)
    out = self.block4(out)
    out = self.convtr4p16s2(out)
    out = self.bntr4(out)
    out = self.relu(out)
    out = ME.cat(out, out_b3p8)
    out = self.block5(out)
    out = self.convtr5p8s2(out)
    out = self.bntr5(out)
    out = self.relu(out)
    out = ME.cat(out, out_b2p4)
    out = self.block6(out)
    out = self.convtr6p4s2(out)
    out = self.bntr6(out)
    out = self.relu(out)
    out = ME.cat(out, out_b1p2)
    out = self.block7(out)
    out = self.convtr7p2s2(out)
    out = self.bntr7(out)
    out = self.relu(out)
    out = ME.cat(out, out_p1)
    out = self.block8(out)
    return self.final(out).slice(in_field).F

class BasicBlock(spconv.SparseModule):
    expansion = 1

    def __init__(self, in_channels, embed_channels, stride=1, norm_fn=None, indice_key=None, bias=False):
        super().__init__()
        assert norm_fn is not None
        if in_channels == embed_channels:
            self.proj = spconv.SparseSequential(nn.Identity())
        else:
            self.proj = spconv.SparseSequential(spconv.SubMConv3d(in_channels, embed_channels, kernel_size=1, bias=False), norm_fn(embed_channels))
        self.conv1 = spconv.SubMConv3d(in_channels, embed_channels, kernel_size=3, stride=stride, padding=1, bias=bias, indice_key=indice_key)
        self.bn1 = norm_fn(embed_channels)
        self.relu = nn.ReLU()
        self.conv2 = spconv.SubMConv3d(embed_channels, embed_channels, kernel_size=3, stride=stride, padding=1, bias=bias, indice_key=indice_key)
        self.bn2 = norm_fn(embed_channels)
        self.stride = stride

    def forward(self, x):
        residual = x
        out = self.conv1(x)
        out = out.replace_feature(self.bn1(out.features))
        out = out.replace_feature(self.relu(out.features))
        out = self.conv2(out)
        out = out.replace_feature(self.bn2(out.features))
        out = out.replace_feature(out.features + self.proj(residual).features)
        out = out.replace_feature(self.relu(out.features))
        return out

def forward(self, x):
    residual = x
    out = self.conv1(x)
    out = out.replace_feature(self.bn1(out.features))
    out = out.replace_feature(self.relu(out.features))
    out = self.conv2(out)
    out = out.replace_feature(self.bn2(out.features))
    out = out.replace_feature(out.features + self.proj(residual).features)
    out = out.replace_feature(self.relu(out.features))
    return out

class BasicConvolutionBlock(nn.Module):

    def __init__(self, inc, outc, ks=3, stride=1, dilation=1):
        super().__init__()
        self.net = nn.Sequential(spnn.Conv3d(inc, outc, kernel_size=ks, dilation=dilation, stride=stride), spnn.BatchNorm(outc), spnn.ReLU(True))

    def forward(self, x):
        out = self.net(x)
        return out

def forward(self, x):
    out = self.net(x)
    return out

class BasicDeconvolutionBlock(nn.Module):

    def __init__(self, inc, outc, ks=3, stride=1):
        super().__init__()
        self.net = nn.Sequential(spnn.Conv3d(inc, outc, kernel_size=ks, stride=stride, transposed=True), spnn.BatchNorm(outc), spnn.ReLU(True))

    def forward(self, x):
        return self.net(x)

def forward(self, x):
    return self.net(x)

class ResidualBlock(nn.Module):

    def __init__(self, inc, outc, ks=3, stride=1, dilation=1):
        super().__init__()
        self.net = nn.Sequential(spnn.Conv3d(inc, outc, kernel_size=ks, dilation=dilation, stride=stride), spnn.BatchNorm(outc), spnn.ReLU(True), spnn.Conv3d(outc, outc, kernel_size=ks, dilation=dilation, stride=1), spnn.BatchNorm(outc))
        if inc == outc and stride == 1:
            self.downsample = nn.Identity()
        else:
            self.downsample = nn.Sequential(spnn.Conv3d(inc, outc, kernel_size=1, dilation=1, stride=stride), spnn.BatchNorm(outc))
        self.relu = spnn.ReLU(True)

    def forward(self, x):
        out = self.relu(self.net(x) + self.downsample(x))
        return out

def forward(self, x):
    out = self.relu(self.net(x) + self.downsample(x))
    return out

class Mlp(nn.Module):
    """ Multilayer perceptron."""

    def __init__(self, in_features, hidden_features=None, out_features=None, act_layer=nn.GELU, drop=0.0):
        super().__init__()
        out_features = out_features or in_features
        hidden_features = hidden_features or in_features
        self.fc1 = nn.Linear(in_features, hidden_features)
        self.act = act_layer()
        self.fc2 = nn.Linear(hidden_features, out_features)
        self.drop = nn.Dropout(drop, inplace=True)

    def forward(self, x):
        x = self.fc1(x)
        x = self.act(x)
        x = self.drop(x)
        x = self.fc2(x)
        x = self.drop(x)
        return x

def forward(self, x):
    x = self.fc1(x)
    x = self.act(x)
    x = self.drop(x)
    x = self.fc2(x)
    x = self.drop(x)
    return x

class SwinTransformerBlock(nn.Module):

    def __init__(self, dim, num_heads, window_size, quant_size, rel_query=True, rel_key=False, rel_value=False, drop_path=0.0, mlp_ratio=4.0, qkv_bias=True, qk_scale=None, act_layer=nn.GELU, norm_layer=nn.LayerNorm, mode=4):
        super().__init__()
        self.mode = mode
        self.norm1 = norm_layer(dim)
        self.attn = WindowAttention(dim, window_size, num_heads=num_heads, quant_size=quant_size, rel_query=rel_query, rel_key=rel_key, rel_value=rel_value, qkv_bias=qkv_bias, qk_scale=qk_scale)
        self.drop_path = DropPath(drop_path) if drop_path > 0.0 else nn.Identity()
        self.norm2 = norm_layer(dim)
        mlp_hidden_dim = int(dim * mlp_ratio)
        self.mlp = Mlp(in_features=dim, hidden_features=mlp_hidden_dim, act_layer=act_layer)

    def forward(self, feats, xyz, index_0, index_1, index_0_offsets, n_max):
        short_cut = feats
        feats = self.norm1(feats)
        feats = self.attn(feats, xyz, index_0, index_1, index_0_offsets, n_max)
        feats = short_cut + self.drop_path(feats)
        feats = feats + self.drop_path(self.mlp(self.norm2(feats)))
        return feats

def forward(self, feats, xyz, index_0, index_1, index_0_offsets, n_max):
    short_cut = feats
    feats = self.norm1(feats)
    feats = self.attn(feats, xyz, index_0, index_1, index_0_offsets, n_max)
    feats = short_cut + self.drop_path(feats)
    feats = feats + self.drop_path(self.mlp(self.norm2(feats)))
    return feats

class MLP(nn.Module):

    def __init__(self, in_channels, hidden_channels=None, out_channels=None, drop=0.0):
        super().__init__()
        out_channels = out_channels or in_channels
        hidden_channels = hidden_channels or in_channels
        self.fc1 = nn.Linear(in_channels, hidden_channels)
        self.act = nn.GELU()
        self.fc2 = nn.Linear(hidden_channels, out_channels)
        self.drop = nn.Dropout(drop, inplace=True)

    def forward(self, x):
        x = self.fc1(x)
        x = self.act(x)
        x = self.drop(x)
        x = self.fc2(x)
        x = self.drop(x)
        return x

def forward(self, x):
    x = self.fc1(x)
    x = self.act(x)
    x = self.drop(x)
    x = self.fc2(x)
    x = self.drop(x)
    return x

class Block(nn.Module):

    def __init__(self, embed_channels, num_heads, window_size, quant_size, mlp_expend_ratio=4.0, drop_path=0.0, qk_scale=None, rel_query=True, rel_key=True, rel_value=True, qkv_bias=True):
        super().__init__()
        self.norm1 = nn.LayerNorm(embed_channels)
        self.attn = WindowAttention(embed_channels, num_heads, window_size, quant_size, scale=qk_scale, rel_query=rel_query, rel_key=rel_key, rel_value=rel_value, qkv_bias=qkv_bias)
        self.drop_path = DropPath(drop_path) if drop_path > 0.0 else nn.Identity()
        self.norm2 = nn.LayerNorm(embed_channels)
        self.mlp = MLP(in_channels=embed_channels, hidden_channels=int(embed_channels * mlp_expend_ratio))

    def forward(self, feats, coords, index_0, index_1, index_0_offsets, n_max):
        short_cut = feats
        feats = self.norm1(feats)
        feats = self.attn(feats, coords, index_0, index_1, index_0_offsets, n_max)
        feats = short_cut + self.drop_path(feats)
        feats += self.drop_path(self.mlp(self.norm2(feats)))
        return feats

def forward(self, feats, coords, index_0, index_1, index_0_offsets, n_max):
    short_cut = feats
    feats = self.norm1(feats)
    feats = self.attn(feats, coords, index_0, index_1, index_0_offsets, n_max)
    feats = short_cut + self.drop_path(feats)
    feats += self.drop_path(self.mlp(self.norm2(feats)))
    return feats

