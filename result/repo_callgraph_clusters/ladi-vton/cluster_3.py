# Cluster 3

class VGG19(torch.nn.Module):

    def __init__(self, requires_grad=False):
        super().__init__()
        vgg_pretrained_features = torchvision.models.vgg19(torchvision.models.VGG19_Weights.IMAGENET1K_V1).features
        self.slice1 = torch.nn.Sequential()
        self.slice2 = torch.nn.Sequential()
        self.slice3 = torch.nn.Sequential()
        self.slice4 = torch.nn.Sequential()
        self.slice5 = torch.nn.Sequential()
        for x in range(2):
            self.slice1.add_module(str(x), vgg_pretrained_features[x])
        for x in range(2, 7):
            self.slice2.add_module(str(x), vgg_pretrained_features[x])
        for x in range(7, 12):
            self.slice3.add_module(str(x), vgg_pretrained_features[x])
        for x in range(12, 21):
            self.slice4.add_module(str(x), vgg_pretrained_features[x])
        for x in range(21, 30):
            self.slice5.add_module(str(x), vgg_pretrained_features[x])
        if not requires_grad:
            for param in self.parameters():
                param.requires_grad = False

    def forward(self, X):
        h_relu1 = self.slice1(X)
        h_relu2 = self.slice2(h_relu1)
        h_relu3 = self.slice3(h_relu2)
        h_relu4 = self.slice4(h_relu3)
        h_relu5 = self.slice5(h_relu4)
        out = [h_relu1, h_relu2, h_relu3, h_relu4, h_relu5]
        return out

def __init__(self, requires_grad=False):
    super().__init__()
    vgg_pretrained_features = torchvision.models.vgg19(torchvision.models.VGG19_Weights.IMAGENET1K_V1).features
    self.slice1 = torch.nn.Sequential()
    self.slice2 = torch.nn.Sequential()
    self.slice3 = torch.nn.Sequential()
    self.slice4 = torch.nn.Sequential()
    self.slice5 = torch.nn.Sequential()
    for x in range(2):
        self.slice1.add_module(str(x), vgg_pretrained_features[x])
    for x in range(2, 7):
        self.slice2.add_module(str(x), vgg_pretrained_features[x])
    for x in range(7, 12):
        self.slice3.add_module(str(x), vgg_pretrained_features[x])
    for x in range(12, 21):
        self.slice4.add_module(str(x), vgg_pretrained_features[x])
    for x in range(21, 30):
        self.slice5.add_module(str(x), vgg_pretrained_features[x])
    if not requires_grad:
        for param in self.parameters():
            param.requires_grad = False

class DoubleConv(nn.Module):
    """(convolution => [BN] => ReLU) * 2"""

    def __init__(self, in_channels, out_channels, mid_channels=None):
        super().__init__()
        if not mid_channels:
            mid_channels = out_channels
        self.double_conv = nn.Sequential(nn.Conv2d(in_channels, mid_channels, kernel_size=3, padding=1, bias=False), nn.BatchNorm2d(mid_channels), nn.ReLU(inplace=True), nn.Conv2d(mid_channels, out_channels, kernel_size=3, padding=1, bias=False), nn.BatchNorm2d(out_channels), nn.ReLU(inplace=True))

    def forward(self, x):
        return self.double_conv(x)

def __init__(self, in_channels, out_channels, mid_channels=None):
    super().__init__()
    if not mid_channels:
        mid_channels = out_channels
    self.double_conv = nn.Sequential(nn.Conv2d(in_channels, mid_channels, kernel_size=3, padding=1, bias=False), nn.BatchNorm2d(mid_channels), nn.ReLU(inplace=True), nn.Conv2d(mid_channels, out_channels, kernel_size=3, padding=1, bias=False), nn.BatchNorm2d(out_channels), nn.ReLU(inplace=True))

class Down(nn.Module):
    """Downscaling with maxpool then double conv"""

    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.maxpool_conv = nn.Sequential(nn.MaxPool2d(2), DoubleConv(in_channels, out_channels))

    def forward(self, x):
        return self.maxpool_conv(x)

def __init__(self, in_channels, out_channels):
    super().__init__()
    self.maxpool_conv = nn.Sequential(nn.MaxPool2d(2), DoubleConv(in_channels, out_channels))

class Up(nn.Module):
    """Upscaling then double conv"""

    def __init__(self, in_channels, out_channels, bilinear=True):
        super().__init__()
        if bilinear:
            self.up = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True)
            self.conv = DoubleConv(in_channels, out_channels, in_channels // 2)
        else:
            self.up = nn.ConvTranspose2d(in_channels, in_channels // 2, kernel_size=2, stride=2)
            self.conv = DoubleConv(in_channels, out_channels)

    def forward(self, x1, x2):
        x1 = self.up(x1)
        diffY = x2.size()[2] - x1.size()[2]
        diffX = x2.size()[3] - x1.size()[3]
        x1 = F.pad(x1, [diffX // 2, diffX - diffX // 2, diffY // 2, diffY - diffY // 2])
        x = torch.cat([x2, x1], dim=1)
        return self.conv(x)

def __init__(self, in_channels, out_channels, bilinear=True):
    super().__init__()
    if bilinear:
        self.up = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True)
        self.conv = DoubleConv(in_channels, out_channels, in_channels // 2)
    else:
        self.up = nn.ConvTranspose2d(in_channels, in_channels // 2, kernel_size=2, stride=2)
        self.conv = DoubleConv(in_channels, out_channels)

class OutConv(nn.Module):

    def __init__(self, in_channels, out_channels):
        super(OutConv, self).__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size=1)

    def forward(self, x):
        return self.conv(x)

def __init__(self, in_channels, out_channels):
    super(OutConv, self).__init__()
    self.conv = nn.Conv2d(in_channels, out_channels, kernel_size=1)

class Encoder(nn.Module):

    def __init__(self, in_channels=3, out_channels=3, down_block_types=('DownEncoderBlock2D',), block_out_channels=(64,), layers_per_block=2, norm_num_groups=32, act_fn='silu', double_z=True):
        super().__init__()
        self.layers_per_block = layers_per_block
        self.conv_in = torch.nn.Conv2d(in_channels, block_out_channels[0], kernel_size=3, stride=1, padding=1)
        self.mid_block = None
        self.down_blocks = nn.ModuleList([])
        output_channel = block_out_channels[0]
        for i, down_block_type in enumerate(down_block_types):
            input_channel = output_channel
            output_channel = block_out_channels[i]
            is_final_block = i == len(block_out_channels) - 1
            down_block = get_down_block(down_block_type, num_layers=self.layers_per_block, in_channels=input_channel, out_channels=output_channel, add_downsample=not is_final_block, resnet_eps=1e-06, downsample_padding=0, resnet_act_fn=act_fn, resnet_groups=norm_num_groups, attn_num_head_channels=None, temb_channels=None)
            self.down_blocks.append(down_block)
        self.mid_block = UNetMidBlock2D(in_channels=block_out_channels[-1], resnet_eps=1e-06, resnet_act_fn=act_fn, output_scale_factor=1, resnet_time_scale_shift='default', attn_num_head_channels=None, resnet_groups=norm_num_groups, temb_channels=None)
        self.conv_norm_out = nn.GroupNorm(num_channels=block_out_channels[-1], num_groups=norm_num_groups, eps=1e-06)
        self.conv_act = nn.SiLU()
        conv_out_channels = 2 * out_channels if double_z else out_channels
        self.conv_out = nn.Conv2d(block_out_channels[-1], conv_out_channels, 3, padding=1)

    def forward(self, x):
        intermediate_features = []
        intermediate_features.append(x)
        sample = x
        sample = self.conv_in(sample)
        intermediate_features.append(sample)
        for down_block in self.down_blocks:
            intermediate_features.append(sample)
            sample = down_block(sample)
        sample = self.mid_block(sample)
        sample = self.conv_norm_out(sample)
        sample = self.conv_act(sample)
        sample = self.conv_out(sample)
        return (sample, intermediate_features)

def __init__(self, in_channels=3, out_channels=3, down_block_types=('DownEncoderBlock2D',), block_out_channels=(64,), layers_per_block=2, norm_num_groups=32, act_fn='silu', double_z=True):
    super().__init__()
    self.layers_per_block = layers_per_block
    self.conv_in = torch.nn.Conv2d(in_channels, block_out_channels[0], kernel_size=3, stride=1, padding=1)
    self.mid_block = None
    self.down_blocks = nn.ModuleList([])
    output_channel = block_out_channels[0]
    for i, down_block_type in enumerate(down_block_types):
        input_channel = output_channel
        output_channel = block_out_channels[i]
        is_final_block = i == len(block_out_channels) - 1
        down_block = get_down_block(down_block_type, num_layers=self.layers_per_block, in_channels=input_channel, out_channels=output_channel, add_downsample=not is_final_block, resnet_eps=1e-06, downsample_padding=0, resnet_act_fn=act_fn, resnet_groups=norm_num_groups, attn_num_head_channels=None, temb_channels=None)
        self.down_blocks.append(down_block)
    self.mid_block = UNetMidBlock2D(in_channels=block_out_channels[-1], resnet_eps=1e-06, resnet_act_fn=act_fn, output_scale_factor=1, resnet_time_scale_shift='default', attn_num_head_channels=None, resnet_groups=norm_num_groups, temb_channels=None)
    self.conv_norm_out = nn.GroupNorm(num_channels=block_out_channels[-1], num_groups=norm_num_groups, eps=1e-06)
    self.conv_act = nn.SiLU()
    conv_out_channels = 2 * out_channels if double_z else out_channels
    self.conv_out = nn.Conv2d(block_out_channels[-1], conv_out_channels, 3, padding=1)

class Decoder(nn.Module):

    def __init__(self, in_channels=3, out_channels=3, up_block_types=('UpDecoderBlock2D',), block_out_channels=(64,), layers_per_block=2, norm_num_groups=32, act_fn='silu'):
        super().__init__()
        self.layers_per_block = layers_per_block
        self.conv_in = nn.Conv2d(in_channels, block_out_channels[-1], kernel_size=3, stride=1, padding=1)
        self.mid_block = None
        self.up_blocks = nn.ModuleList([])
        self.mid_block = UNetMidBlock2D(in_channels=block_out_channels[-1], resnet_eps=1e-06, resnet_act_fn=act_fn, output_scale_factor=1, resnet_time_scale_shift='default', attn_num_head_channels=None, resnet_groups=norm_num_groups, temb_channels=None)
        reversed_block_out_channels = list(reversed(block_out_channels))
        output_channel = reversed_block_out_channels[0]
        for i, up_block_type in enumerate(up_block_types):
            prev_output_channel = output_channel
            output_channel = reversed_block_out_channels[i]
            is_final_block = i == len(block_out_channels) - 1
            up_block = get_up_block(up_block_type, num_layers=self.layers_per_block + 1, in_channels=prev_output_channel, out_channels=output_channel, prev_output_channel=None, add_upsample=not is_final_block, resnet_eps=1e-06, resnet_act_fn=act_fn, resnet_groups=norm_num_groups, attn_num_head_channels=None, temb_channels=None)
            self.up_blocks.append(up_block)
            prev_output_channel = output_channel
        self.conv_norm_out = nn.GroupNorm(num_channels=block_out_channels[0], num_groups=norm_num_groups, eps=1e-06)
        self.conv_act = nn.SiLU()
        self.conv_out = nn.Conv2d(block_out_channels[0], out_channels, 3, padding=1)

    def forward(self, z, intermediate_features=None, int_layers=None):
        sample = z
        sample = self.conv_in(sample)
        sample = self.mid_block(sample)
        if intermediate_features:
            intermediate_features.reverse()
            for up_block, int_feat in zip(self.up_blocks, intermediate_features):
                sample += int_feat
                sample = up_block(sample)
        else:
            for up_block in self.up_blocks:
                sample = up_block(sample)
        sample = self.conv_norm_out(sample)
        sample = self.conv_act(sample)
        if int_layers and 1 in int_layers:
            sample += intermediate_features[len(int_layers) - 1 - int_layers.index(1)]
        sample = self.conv_out(sample)
        if int_layers and 0 in int_layers:
            sample += intermediate_features[len(int_layers) - 1 - int_layers.index(0)]
        return sample

def __init__(self, in_channels=3, out_channels=3, up_block_types=('UpDecoderBlock2D',), block_out_channels=(64,), layers_per_block=2, norm_num_groups=32, act_fn='silu'):
    super().__init__()
    self.layers_per_block = layers_per_block
    self.conv_in = nn.Conv2d(in_channels, block_out_channels[-1], kernel_size=3, stride=1, padding=1)
    self.mid_block = None
    self.up_blocks = nn.ModuleList([])
    self.mid_block = UNetMidBlock2D(in_channels=block_out_channels[-1], resnet_eps=1e-06, resnet_act_fn=act_fn, output_scale_factor=1, resnet_time_scale_shift='default', attn_num_head_channels=None, resnet_groups=norm_num_groups, temb_channels=None)
    reversed_block_out_channels = list(reversed(block_out_channels))
    output_channel = reversed_block_out_channels[0]
    for i, up_block_type in enumerate(up_block_types):
        prev_output_channel = output_channel
        output_channel = reversed_block_out_channels[i]
        is_final_block = i == len(block_out_channels) - 1
        up_block = get_up_block(up_block_type, num_layers=self.layers_per_block + 1, in_channels=prev_output_channel, out_channels=output_channel, prev_output_channel=None, add_upsample=not is_final_block, resnet_eps=1e-06, resnet_act_fn=act_fn, resnet_groups=norm_num_groups, attn_num_head_channels=None, temb_channels=None)
        self.up_blocks.append(up_block)
        prev_output_channel = output_channel
    self.conv_norm_out = nn.GroupNorm(num_channels=block_out_channels[0], num_groups=norm_num_groups, eps=1e-06)
    self.conv_act = nn.SiLU()
    self.conv_out = nn.Conv2d(block_out_channels[0], out_channels, 3, padding=1)

class FeatureExtraction(nn.Module):

    def __init__(self, input_nc, ngf=64, n_layers=3, norm_layer=nn.BatchNorm2d, use_dropout=False):
        super(FeatureExtraction, self).__init__()
        downconv = nn.Conv2d(input_nc, ngf, kernel_size=4, stride=2, padding=1)
        model = [downconv, nn.ReLU(True), norm_layer(ngf)]
        for i in range(n_layers):
            in_ngf = 2 ** i * ngf if 2 ** i * ngf < 512 else 512
            out_ngf = 2 ** (i + 1) * ngf if 2 ** i * ngf < 512 else 512
            downconv = nn.Conv2d(in_ngf, out_ngf, kernel_size=4, stride=2, padding=1)
            model += [downconv, nn.ReLU(True)]
            model += [norm_layer(out_ngf)]
        model += [nn.Conv2d(512, 512, kernel_size=3, stride=1, padding=1), nn.ReLU(True)]
        model += [norm_layer(512)]
        model += [nn.Conv2d(512, 512, kernel_size=3, stride=1, padding=1), nn.ReLU(True)]
        self.model = nn.Sequential(*model)
        init_weights(self.model, init_type='normal')

    def get_output_size(self, in_shape):
        out_shape = None
        with torch.no_grad():
            out_shape = self.model(torch.randn(in_shape))
        return out_shape.shape

    def forward(self, x):
        return self.model(x)

def __init__(self, input_nc, ngf=64, n_layers=3, norm_layer=nn.BatchNorm2d, use_dropout=False):
    super(FeatureExtraction, self).__init__()
    downconv = nn.Conv2d(input_nc, ngf, kernel_size=4, stride=2, padding=1)
    model = [downconv, nn.ReLU(True), norm_layer(ngf)]
    for i in range(n_layers):
        in_ngf = 2 ** i * ngf if 2 ** i * ngf < 512 else 512
        out_ngf = 2 ** (i + 1) * ngf if 2 ** i * ngf < 512 else 512
        downconv = nn.Conv2d(in_ngf, out_ngf, kernel_size=4, stride=2, padding=1)
        model += [downconv, nn.ReLU(True)]
        model += [norm_layer(out_ngf)]
    model += [nn.Conv2d(512, 512, kernel_size=3, stride=1, padding=1), nn.ReLU(True)]
    model += [norm_layer(512)]
    model += [nn.Conv2d(512, 512, kernel_size=3, stride=1, padding=1), nn.ReLU(True)]
    self.model = nn.Sequential(*model)
    init_weights(self.model, init_type='normal')

class FeatureL2Norm(torch.nn.Module):

    def __init__(self):
        super(FeatureL2Norm, self).__init__()

    def forward(self, feature):
        epsilon = 1e-06
        norm = torch.pow(torch.sum(torch.pow(feature, 2), 1) + epsilon, 0.5).unsqueeze(1).expand_as(feature)
        return torch.div(feature, norm)

def __init__(self):
    super(FeatureL2Norm, self).__init__()

class FeatureCorrelation(nn.Module):

    def __init__(self):
        super(FeatureCorrelation, self).__init__()

    def forward(self, feature_A, feature_B):
        b, c, h, w = feature_A.size()
        feature_A = feature_A.transpose(2, 3).contiguous().view(b, c, h * w)
        feature_B = feature_B.view(b, c, h * w).transpose(1, 2)
        feature_mul = torch.bmm(feature_B, feature_A)
        correlation_tensor = feature_mul.view(b, h, w, h * w).transpose(2, 3).transpose(1, 2)
        return correlation_tensor

    def get_output_size(self, in_shape):
        out_shape = None
        with torch.no_grad():
            out_shape = self.forward(torch.randn(in_shape), torch.randn(in_shape))
        return out_shape.shape

def __init__(self):
    super(FeatureCorrelation, self).__init__()

class FeatureRegression(nn.Module):

    def __init__(self, input_nc=192, output_dim=6, use_cuda=True, in_shape=None):
        super(FeatureRegression, self).__init__()
        self.conv = nn.Sequential(nn.Conv2d(input_nc, 512, kernel_size=4, stride=2, padding=1), nn.BatchNorm2d(512), nn.ReLU(inplace=True), nn.Conv2d(512, 256, kernel_size=4, stride=2, padding=1), nn.BatchNorm2d(256), nn.ReLU(inplace=True), nn.Conv2d(256, 128, kernel_size=3, padding=1), nn.BatchNorm2d(128), nn.ReLU(inplace=True), nn.Conv2d(128, 64, kernel_size=3, padding=1), nn.BatchNorm2d(64), nn.ReLU(inplace=True))
        if in_shape is not None:
            with torch.no_grad():
                out = self.conv(torch.randn(in_shape))
            _, out_c, out_w, out_h = out.shape
        else:
            out_c, out_w, out_h = (64, 3, 4)
        self.linear = nn.Linear(out_c * out_h * out_w, output_dim)
        self.tanh = nn.Tanh()

    def forward(self, x):
        x = self.conv(x)
        x = x.reshape(x.size(0), -1)
        x = self.linear(x)
        x = self.tanh(x)
        return x

def __init__(self, input_nc=192, output_dim=6, use_cuda=True, in_shape=None):
    super(FeatureRegression, self).__init__()
    self.conv = nn.Sequential(nn.Conv2d(input_nc, 512, kernel_size=4, stride=2, padding=1), nn.BatchNorm2d(512), nn.ReLU(inplace=True), nn.Conv2d(512, 256, kernel_size=4, stride=2, padding=1), nn.BatchNorm2d(256), nn.ReLU(inplace=True), nn.Conv2d(256, 128, kernel_size=3, padding=1), nn.BatchNorm2d(128), nn.ReLU(inplace=True), nn.Conv2d(128, 64, kernel_size=3, padding=1), nn.BatchNorm2d(64), nn.ReLU(inplace=True))
    if in_shape is not None:
        with torch.no_grad():
            out = self.conv(torch.randn(in_shape))
        _, out_c, out_w, out_h = out.shape
    else:
        out_c, out_w, out_h = (64, 3, 4)
    self.linear = nn.Linear(out_c * out_h * out_w, output_dim)
    self.tanh = nn.Tanh()

class ConvNet_TPS(nn.Module):
    """ Geometric Matching Module
    """

    def __init__(self, height, width, input_nc=6, n_layer=4):
        super(ConvNet_TPS, self).__init__()
        range = 0.9
        r1 = range
        r2 = range
        grid_size_h = 5
        grid_size_w = 5
        self.height = height
        self.width = width
        assert r1 < 1 and r2 < 1
        target_control_points = torch.Tensor(list(itertools.product(np.arange(-r1, r1 + 1e-05, 2.0 * r1 / (grid_size_h - 1)), np.arange(-r2, r2 + 1e-05, 2.0 * r2 / (grid_size_w - 1)))))
        Y, X = target_control_points.split(1, dim=1)
        target_control_points = torch.cat([X, Y], dim=1)
        self.extractionA = FeatureExtraction(3, ngf=64, n_layers=n_layer, norm_layer=nn.BatchNorm2d)
        self.extractionB = FeatureExtraction(input_nc, ngf=64, n_layers=n_layer, norm_layer=nn.BatchNorm2d)
        self.in_shape = self.extractionA.get_output_size((4, 3, height, width))
        self.l2norm = FeatureL2Norm()
        self.correlation = FeatureCorrelation()
        self.in_shape = self.correlation.get_output_size(self.in_shape)
        self.loc_net = BoundedGridLocNet(grid_size_h, grid_size_w, target_control_points, n_layers=5)
        self.gridGen = TPSGridGen(height, width, target_control_points)

    def forward(self, inputA, inputB):
        batch_size = inputA.size(0)
        featureA = self.extractionA(inputA)
        featureB = self.extractionB(inputB)
        featureA = self.l2norm(featureA)
        featureB = self.l2norm(featureB)
        correlation = self.correlation(featureA, featureB)
        source_control_points, rx, ry, cx, cy, rg, cg = self.loc_net(correlation)
        source_control_points = source_control_points
        source_coordinate = self.gridGen(source_control_points)
        grid = source_coordinate.view(batch_size, self.height, self.width, 2)
        return (grid, source_control_points, rx, ry, cx, cy, rg, cg)

def __init__(self, height, width, input_nc=6, n_layer=4):
    super(ConvNet_TPS, self).__init__()
    range = 0.9
    r1 = range
    r2 = range
    grid_size_h = 5
    grid_size_w = 5
    self.height = height
    self.width = width
    assert r1 < 1 and r2 < 1
    target_control_points = torch.Tensor(list(itertools.product(np.arange(-r1, r1 + 1e-05, 2.0 * r1 / (grid_size_h - 1)), np.arange(-r2, r2 + 1e-05, 2.0 * r2 / (grid_size_w - 1)))))
    Y, X = target_control_points.split(1, dim=1)
    target_control_points = torch.cat([X, Y], dim=1)
    self.extractionA = FeatureExtraction(3, ngf=64, n_layers=n_layer, norm_layer=nn.BatchNorm2d)
    self.extractionB = FeatureExtraction(input_nc, ngf=64, n_layers=n_layer, norm_layer=nn.BatchNorm2d)
    self.in_shape = self.extractionA.get_output_size((4, 3, height, width))
    self.l2norm = FeatureL2Norm()
    self.correlation = FeatureCorrelation()
    self.in_shape = self.correlation.get_output_size(self.in_shape)
    self.loc_net = BoundedGridLocNet(grid_size_h, grid_size_w, target_control_points, n_layers=5)
    self.gridGen = TPSGridGen(height, width, target_control_points)

class InversionAdapter(nn.Module):

    def __init__(self, input_dim: int, hidden_dim: int, output_dim, config, num_encoder_layers, dropout=0.5):
        super().__init__()
        self.config = config
        self.encoder_layers = nn.ModuleList([CLIPEncoderLayer(config) for _ in range(num_encoder_layers)])
        self.post_layernorm = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_eps)
        self.layers = nn.Sequential(nn.Linear(input_dim, hidden_dim), nn.GELU(), nn.Dropout(p=dropout), nn.Linear(hidden_dim, hidden_dim), nn.GELU(), nn.Dropout(p=dropout), nn.Linear(hidden_dim, output_dim))

    def forward(self, x):
        for encoder_layer in self.encoder_layers:
            x = encoder_layer(x, None, None)
            x = x[0]
        x = x[:, 0, :]
        x = self.post_layernorm(x)
        return self.layers(x)

def __init__(self, input_dim: int, hidden_dim: int, output_dim, config, num_encoder_layers, dropout=0.5):
    super().__init__()
    self.config = config
    self.encoder_layers = nn.ModuleList([CLIPEncoderLayer(config) for _ in range(num_encoder_layers)])
    self.post_layernorm = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_eps)
    self.layers = nn.Sequential(nn.Linear(input_dim, hidden_dim), nn.GELU(), nn.Dropout(p=dropout), nn.Linear(hidden_dim, hidden_dim), nn.GELU(), nn.Dropout(p=dropout), nn.Linear(hidden_dim, output_dim))

class EMASC(nn.Module):
    """
    EMASC: Enhanced Mask-Aware Skip Connections
    """

    def __init__(self, in_channels: List[int], out_channels: List[int], kernel_size: int=3, padding: int=1, stride: int=1, type: str='nonlinear'):
        super().__init__()
        if type == 'linear':
            self.conv = nn.ModuleList()
            for in_ch, out_ch in zip(in_channels, out_channels):
                self.conv.append(nn.Conv2d(in_ch, out_ch, kernel_size=3, bias=True, padding=padding, stride=stride))
            self.apply(self._init_weights)
        elif type == 'nonlinear':
            self.conv = nn.ModuleList()
            for in_ch, out_ch in zip(in_channels, out_channels):
                adapter = nn.Sequential(nn.Conv2d(in_ch, in_ch, kernel_size=kernel_size, bias=True, padding=padding, stride=stride), nn.SiLU(inplace=True), nn.Conv2d(in_ch, out_ch, kernel_size=kernel_size, bias=True, padding=padding, stride=stride))
                self.conv.append(adapter)
        else:
            raise NotImplementedError(f'EMASC type {type} is not implemented.')

    def forward(self, x: list):
        for i in range(len(x)):
            x[i] = self.conv[i](x[i])
        return x

    def _init_weights(self, w):
        if isinstance(w, nn.Conv2d):
            w.weight.data.fill_(0.0)
            w.bias.data.fill_(0.0)

def __init__(self, in_channels: List[int], out_channels: List[int], kernel_size: int=3, padding: int=1, stride: int=1, type: str='nonlinear'):
    super().__init__()
    if type == 'linear':
        self.conv = nn.ModuleList()
        for in_ch, out_ch in zip(in_channels, out_channels):
            self.conv.append(nn.Conv2d(in_ch, out_ch, kernel_size=3, bias=True, padding=padding, stride=stride))
        self.apply(self._init_weights)
    elif type == 'nonlinear':
        self.conv = nn.ModuleList()
        for in_ch, out_ch in zip(in_channels, out_channels):
            adapter = nn.Sequential(nn.Conv2d(in_ch, in_ch, kernel_size=kernel_size, bias=True, padding=padding, stride=stride), nn.SiLU(inplace=True), nn.Conv2d(in_ch, out_ch, kernel_size=kernel_size, bias=True, padding=padding, stride=stride))
            self.conv.append(adapter)
    else:
        raise NotImplementedError(f'EMASC type {type} is not implemented.')

class UNetVanilla(nn.Module):

    def __init__(self, n_channels: int, n_classes: int, bilinear: bool=False):
        super(UNetVanilla, self).__init__()
        self.n_channels = n_channels
        self.n_classes = n_classes
        self.bilinear = bilinear
        self.inc = DoubleConv(n_channels, 64)
        self.down1 = Down(64, 128)
        self.down2 = Down(128, 256)
        self.down3 = Down(256, 512)
        factor = 2 if bilinear else 1
        self.down4 = Down(512, 1024 // factor)
        self.up1 = Up(1024, 512 // factor, bilinear)
        self.up2 = Up(512, 256 // factor, bilinear)
        self.up3 = Up(256, 128 // factor, bilinear)
        self.up4 = Up(128, 64, bilinear)
        self.outc = OutConv(64, n_classes)

    def forward(self, x):
        x1 = self.inc(x)
        x2 = self.down1(x1)
        x3 = self.down2(x2)
        x4 = self.down3(x3)
        x5 = self.down4(x4)
        x = self.up1(x5, x4)
        x = self.up2(x, x3)
        x = self.up3(x, x2)
        x = self.up4(x, x1)
        logits = self.outc(x)
        return logits

def __init__(self, n_channels: int, n_classes: int, bilinear: bool=False):
    super(UNetVanilla, self).__init__()
    self.n_channels = n_channels
    self.n_classes = n_classes
    self.bilinear = bilinear
    self.inc = DoubleConv(n_channels, 64)
    self.down1 = Down(64, 128)
    self.down2 = Down(128, 256)
    self.down3 = Down(256, 512)
    factor = 2 if bilinear else 1
    self.down4 = Down(512, 1024 // factor)
    self.up1 = Up(1024, 512 // factor, bilinear)
    self.up2 = Up(512, 256 // factor, bilinear)
    self.up3 = Up(256, 128 // factor, bilinear)
    self.up4 = Up(128, 64, bilinear)
    self.outc = OutConv(64, n_classes)

class AutoencoderKL(ModelMixin, ConfigMixin):
    """Variational Autoencoder (VAE) model with KL loss from the paper Auto-Encoding Variational Bayes by Diederik P. Kingma
    and Max Welling.

    This model inherits from [`ModelMixin`]. Check the superclass documentation for the generic methods the library
    implements for all the model (such as downloading or saving, etc.)

    Parameters:
        in_channels (int, *optional*, defaults to 3): Number of channels in the input image.
        out_channels (int,  *optional*, defaults to 3): Number of channels in the output.
        down_block_types (`Tuple[str]`, *optional*, defaults to :
            obj:`("DownEncoderBlock2D",)`): Tuple of downsample block types.
        up_block_types (`Tuple[str]`, *optional*, defaults to :
            obj:`("UpDecoderBlock2D",)`): Tuple of upsample block types.
        block_out_channels (`Tuple[int]`, *optional*, defaults to :
            obj:`(64,)`): Tuple of block output channels.
        act_fn (`str`, *optional*, defaults to `"silu"`): The activation function to use.
        latent_channels (`int`, *optional*, defaults to 4): Number of channels in the latent space.
        sample_size (`int`, *optional*, defaults to `32`): TODO
        scaling_factor (`float`, *optional*, defaults to 0.18215):
            The component-wise standard deviation of the trained latent space computed using the first batch of the
            training set. This is used to scale the latent space to have unit variance when training the diffusion
            model. The latents are scaled with the formula `z = z * scaling_factor` before being passed to the
            diffusion model. When decoding, the latents are scaled back to the original scale with the formula: `z = 1
            / scaling_factor * z`. For more details, refer to sections 4.3.2 and D.1 of the [High-Resolution Image
            Synthesis with Latent Diffusion Models](https://arxiv.org/abs/2112.10752) paper.
    """

    @register_to_config
    def __init__(self, in_channels: int=3, out_channels: int=3, down_block_types: Tuple[str]=('DownEncoderBlock2D',), up_block_types: Tuple[str]=('UpDecoderBlock2D',), block_out_channels: Tuple[int]=(64,), layers_per_block: int=1, act_fn: str='silu', latent_channels: int=4, norm_num_groups: int=32, sample_size: int=32, scaling_factor: float=0.18215):
        super().__init__()
        self.encoder = Encoder(in_channels=in_channels, out_channels=latent_channels, down_block_types=down_block_types, block_out_channels=block_out_channels, layers_per_block=layers_per_block, act_fn=act_fn, norm_num_groups=norm_num_groups, double_z=True)
        self.decoder = Decoder(in_channels=latent_channels, out_channels=out_channels, up_block_types=up_block_types, block_out_channels=block_out_channels, layers_per_block=layers_per_block, norm_num_groups=norm_num_groups, act_fn=act_fn)
        self.quant_conv = nn.Conv2d(2 * latent_channels, 2 * latent_channels, 1)
        self.post_quant_conv = nn.Conv2d(latent_channels, latent_channels, 1)
        self.use_slicing = False
        self.use_tiling = False
        self.tile_sample_min_size = self.config.sample_size
        sample_size = self.config.sample_size[0] if isinstance(self.config.sample_size, (list, tuple)) else self.config.sample_size
        self.tile_latent_min_size = int(sample_size / 2 ** (len(self.block_out_channels) - 1))
        self.tile_overlap_factor = 0.25

    def enable_tiling(self, use_tiling: bool=True):
        """
        Enable tiled VAE decoding. When this option is enabled, the VAE will split the input tensor into tiles to
        compute decoding and encoding in several steps. This is useful to save a large amount of memory and to allow
        the processing of larger images.
        """
        self.use_tiling = use_tiling

    def disable_tiling(self):
        """
        Disable tiled VAE decoding. If `enable_vae_tiling` was previously invoked, this method will go back to
        computing decoding in one step.
        """
        self.enable_tiling(False)

    def enable_slicing(self):
        """
        Enable sliced VAE decoding. When this option is enabled, the VAE will split the input tensor in slices to
        compute decoding in several steps. This is useful to save some memory and allow larger batch sizes.
        """
        self.use_slicing = True

    def disable_slicing(self):
        """
        Disable sliced VAE decoding. If `enable_slicing` was previously invoked, this method will go back to computing
        decoding in one step.
        """
        self.use_slicing = False

    @apply_forward_hook
    def encode(self, x: torch.FloatTensor, return_dict: bool=True) -> AutoencoderKLOutput:
        if self.use_tiling and (x.shape[-1] > self.tile_sample_min_size or x.shape[-2] > self.tile_sample_min_size):
            return self.tiled_encode(x, return_dict=return_dict)
        h, intermediate_features = self.encoder(x)
        moments = self.quant_conv(h)
        posterior = DiagonalGaussianDistribution(moments)
        if not return_dict:
            return (posterior,)
        return (AutoencoderKLOutput(latent_dist=posterior), intermediate_features)

    def _decode(self, z: torch.FloatTensor, intermediate_features: list=None, int_layers: list=None, return_dict: bool=True) -> Union[DecoderOutput, torch.FloatTensor]:
        if self.use_tiling and (z.shape[-1] > self.tile_latent_min_size or z.shape[-2] > self.tile_latent_min_size):
            return self.tiled_decode(z, return_dict=return_dict)
        z = self.post_quant_conv(z)
        if intermediate_features:
            dec = self.decoder(z, intermediate_features, int_layers)
        else:
            dec = self.decoder(z)
        if not return_dict:
            return (dec,)
        return DecoderOutput(sample=dec)

    @apply_forward_hook
    def decode(self, z: torch.FloatTensor, intermediate_features: list=None, int_layers: list=None, return_dict: bool=True) -> Union[DecoderOutput, torch.FloatTensor]:
        if self.use_slicing and z.shape[0] > 1:
            decoded_slices = [self._decode(z_slice).sample for z_slice in z.split(1)]
            decoded = torch.cat(decoded_slices)
        elif intermediate_features:
            decoded = self._decode(z, intermediate_features, int_layers).sample
        else:
            decoded = self._decode(z).sample
        if not return_dict:
            return (decoded,)
        return DecoderOutput(sample=decoded)

    def blend_v(self, a, b, blend_extent):
        for y in range(blend_extent):
            b[:, :, y, :] = a[:, :, -blend_extent + y, :] * (1 - y / blend_extent) + b[:, :, y, :] * (y / blend_extent)
        return b

    def blend_h(self, a, b, blend_extent):
        for x in range(blend_extent):
            b[:, :, :, x] = a[:, :, :, -blend_extent + x] * (1 - x / blend_extent) + b[:, :, :, x] * (x / blend_extent)
        return b

    def tiled_encode(self, x: torch.FloatTensor, return_dict: bool=True) -> AutoencoderKLOutput:
        """Encode a batch of images using a tiled encoder.
        Args:
        When this option is enabled, the VAE will split the input tensor into tiles to compute encoding in several
        steps. This is useful to keep memory use constant regardless of image size. The end result of tiled encoding is:
        different from non-tiled encoding due to each tile using a different encoder. To avoid tiling artifacts, the
        tiles overlap and are blended together to form a smooth output. You may still see tile-sized changes in the
        look of the output, but they should be much less noticeable.
            x (`torch.FloatTensor`): Input batch of images. return_dict (`bool`, *optional*, defaults to `True`):
                Whether or not to return a [`AutoencoderKLOutput`] instead of a plain tuple.
        """
        overlap_size = int(self.tile_sample_min_size * (1 - self.tile_overlap_factor))
        blend_extent = int(self.tile_latent_min_size * self.tile_overlap_factor)
        row_limit = self.tile_latent_min_size - blend_extent
        rows = []
        for i in range(0, x.shape[2], overlap_size):
            row = []
            for j in range(0, x.shape[3], overlap_size):
                tile = x[:, :, i:i + self.tile_sample_min_size, j:j + self.tile_sample_min_size]
                tile, intermediate_features = self.encoder(tile)
                tile = self.quant_conv(tile)
                row.append(tile)
            rows.append(row)
        result_rows = []
        for i, row in enumerate(rows):
            result_row = []
            for j, tile in enumerate(row):
                if i > 0:
                    tile = self.blend_v(rows[i - 1][j], tile, blend_extent)
                if j > 0:
                    tile = self.blend_h(row[j - 1], tile, blend_extent)
                result_row.append(tile[:, :, :row_limit, :row_limit])
            result_rows.append(torch.cat(result_row, dim=3))
        moments = torch.cat(result_rows, dim=2)
        posterior = DiagonalGaussianDistribution(moments)
        if not return_dict:
            return (posterior,)
        return (AutoencoderKLOutput(latent_dist=posterior), intermediate_features)

    def tiled_decode(self, z: torch.FloatTensor, return_dict: bool=True) -> Union[DecoderOutput, torch.FloatTensor]:
        """Decode a batch of images using a tiled decoder.
        Args:
        When this option is enabled, the VAE will split the input tensor into tiles to compute decoding in several
        steps. This is useful to keep memory use constant regardless of image size. The end result of tiled decoding is:
        different from non-tiled decoding due to each tile using a different decoder. To avoid tiling artifacts, the
        tiles overlap and are blended together to form a smooth output. You may still see tile-sized changes in the
        look of the output, but they should be much less noticeable.
            z (`torch.FloatTensor`): Input batch of latent vectors. return_dict (`bool`, *optional*, defaults to
            `True`):
                Whether or not to return a [`DecoderOutput`] instead of a plain tuple.
        """
        overlap_size = int(self.tile_latent_min_size * (1 - self.tile_overlap_factor))
        blend_extent = int(self.tile_sample_min_size * self.tile_overlap_factor)
        row_limit = self.tile_sample_min_size - blend_extent
        rows = []
        for i in range(0, z.shape[2], overlap_size):
            row = []
            for j in range(0, z.shape[3], overlap_size):
                tile = z[:, :, i:i + self.tile_latent_min_size, j:j + self.tile_latent_min_size]
                tile = self.post_quant_conv(tile)
                decoded = self.decoder(tile)
                row.append(decoded)
            rows.append(row)
        result_rows = []
        for i, row in enumerate(rows):
            result_row = []
            for j, tile in enumerate(row):
                if i > 0:
                    tile = self.blend_v(rows[i - 1][j], tile, blend_extent)
                if j > 0:
                    tile = self.blend_h(row[j - 1], tile, blend_extent)
                result_row.append(tile[:, :, :row_limit, :row_limit])
            result_rows.append(torch.cat(result_row, dim=3))
        dec = torch.cat(result_rows, dim=2)
        if not return_dict:
            return (dec,)
        return DecoderOutput(sample=dec)

    def forward(self, sample: torch.FloatTensor, sample_posterior: bool=False, return_dict: bool=True, generator: Optional[torch.Generator]=None) -> Union[DecoderOutput, torch.FloatTensor]:
        """
        Args:
            sample (`torch.FloatTensor`): Input sample.
            sample_posterior (`bool`, *optional*, defaults to `False`):
                Whether to sample from the posterior.
            return_dict (`bool`, *optional*, defaults to `True`):
                Whether or not to return a [`DecoderOutput`] instead of a plain tuple.
        """
        x = sample
        posterior = self.encode(x).latent_dist
        if sample_posterior:
            z = posterior.sample(generator=generator)
        else:
            z = posterior.mode()
        dec = self.decode(z).sample
        if not return_dict:
            return (dec,)
        return DecoderOutput(sample=dec)

@register_to_config
def __init__(self, in_channels: int=3, out_channels: int=3, down_block_types: Tuple[str]=('DownEncoderBlock2D',), up_block_types: Tuple[str]=('UpDecoderBlock2D',), block_out_channels: Tuple[int]=(64,), layers_per_block: int=1, act_fn: str='silu', latent_channels: int=4, norm_num_groups: int=32, sample_size: int=32, scaling_factor: float=0.18215):
    super().__init__()
    self.encoder = Encoder(in_channels=in_channels, out_channels=latent_channels, down_block_types=down_block_types, block_out_channels=block_out_channels, layers_per_block=layers_per_block, act_fn=act_fn, norm_num_groups=norm_num_groups, double_z=True)
    self.decoder = Decoder(in_channels=latent_channels, out_channels=out_channels, up_block_types=up_block_types, block_out_channels=block_out_channels, layers_per_block=layers_per_block, norm_num_groups=norm_num_groups, act_fn=act_fn)
    self.quant_conv = nn.Conv2d(2 * latent_channels, 2 * latent_channels, 1)
    self.post_quant_conv = nn.Conv2d(latent_channels, latent_channels, 1)
    self.use_slicing = False
    self.use_tiling = False
    self.tile_sample_min_size = self.config.sample_size
    sample_size = self.config.sample_size[0] if isinstance(self.config.sample_size, (list, tuple)) else self.config.sample_size
    self.tile_latent_min_size = int(sample_size / 2 ** (len(self.block_out_channels) - 1))
    self.tile_overlap_factor = 0.25

