# Cluster 3

def _sum_ft(tensor):
    """sum over the first and last dimention"""
    return tensor.sum(dim=0).sum(dim=-1)

def _unsqueeze_ft(tensor):
    """add new dementions at the front and the tail"""
    return tensor.unsqueeze(0).unsqueeze(-1)

class DenseMotionModule(nn.Module):
    """
    Module that predicting a dense optical flow only from the displacement of a keypoints
    and the appearance of the first frame
    """

    def __init__(self, block_expansion, num_blocks, max_features, mask_embedding_params, num_kp, num_channels, kp_variance, use_correction, use_mask, bg_init=2, num_group_blocks=0, scale_factor=1):
        super(DenseMotionModule, self).__init__()
        self.mask_embedding = MovementEmbeddingModule(num_kp=num_kp, kp_variance=kp_variance, num_channels=num_channels, add_bg_feature_map=True, **mask_embedding_params)
        self.difference_embedding = MovementEmbeddingModule(num_kp=num_kp, kp_variance=kp_variance, num_channels=num_channels, add_bg_feature_map=True, use_difference=True, use_heatmap=False, use_deformed_source_image=False)
        group_blocks = []
        for i in range(num_group_blocks):
            group_blocks.append(SameBlock3D(self.mask_embedding.out_channels, self.mask_embedding.out_channels, groups=num_kp + 1, kernel_size=(1, 1, 1), padding=(0, 0, 0)))
        self.group_blocks = nn.ModuleList(group_blocks)
        self.hourglass = Hourglass(block_expansion=block_expansion, in_features=self.mask_embedding.out_channels, out_features=(num_kp + 1) * use_mask + 2 * use_correction, max_features=max_features, num_blocks=num_blocks)
        self.hourglass.decoder.conv.weight.data.zero_()
        bias_init = ([bg_init] + [0] * num_kp) * use_mask + [0, 0] * use_correction
        self.hourglass.decoder.conv.bias.data.copy_(torch.tensor(bias_init, dtype=torch.float))
        self.num_kp = num_kp
        self.use_correction = use_correction
        self.use_mask = use_mask
        self.scale_factor = scale_factor

    def forward(self, source_image, kp_driving, kp_source):
        if self.scale_factor != 1:
            source_image = F.interpolate(source_image, scale_factor=(1, self.scale_factor, self.scale_factor))
        prediction = self.mask_embedding(source_image, kp_driving, kp_source)
        for block in self.group_blocks:
            prediction = block(prediction)
            prediction = F.leaky_relu(prediction, 0.2)
        prediction = self.hourglass(prediction)
        bs, _, d, h, w = prediction.shape
        if self.use_mask:
            mask = prediction[:, :self.num_kp + 1]
            mask = F.softmax(mask, dim=1)
            mask = mask.unsqueeze(2)
            difference_embedding = self.difference_embedding(source_image, kp_driving, kp_source)
            difference_embedding = difference_embedding.view(bs, self.num_kp + 1, 2, d, h, w)
            deformations_relative = (difference_embedding * mask).sum(dim=1)
        else:
            deformations_relative = 0
        if self.use_correction:
            correction = prediction[:, -2:]
        else:
            correction = 0
        deformations_relative = deformations_relative + correction
        deformations_relative = deformations_relative.permute(0, 2, 3, 4, 1)
        coordinate_grid = make_coordinate_grid((h, w), type=deformations_relative.type())
        coordinate_grid = coordinate_grid.view(1, 1, h, w, 2)
        deformation = deformations_relative + coordinate_grid
        z_coordinate = torch.zeros(deformation.shape[:-1] + (1,)).type(deformation.type())
        return torch.cat([deformation, z_coordinate], dim=-1)

def forward(self, source_image, kp_driving, kp_source):
    if self.scale_factor != 1:
        source_image = F.interpolate(source_image, scale_factor=(1, self.scale_factor, self.scale_factor))
    prediction = self.mask_embedding(source_image, kp_driving, kp_source)
    for block in self.group_blocks:
        prediction = block(prediction)
        prediction = F.leaky_relu(prediction, 0.2)
    prediction = self.hourglass(prediction)
    bs, _, d, h, w = prediction.shape
    if self.use_mask:
        mask = prediction[:, :self.num_kp + 1]
        mask = F.softmax(mask, dim=1)
        mask = mask.unsqueeze(2)
        difference_embedding = self.difference_embedding(source_image, kp_driving, kp_source)
        difference_embedding = difference_embedding.view(bs, self.num_kp + 1, 2, d, h, w)
        deformations_relative = (difference_embedding * mask).sum(dim=1)
    else:
        deformations_relative = 0
    if self.use_correction:
        correction = prediction[:, -2:]
    else:
        correction = 0
    deformations_relative = deformations_relative + correction
    deformations_relative = deformations_relative.permute(0, 2, 3, 4, 1)
    coordinate_grid = make_coordinate_grid((h, w), type=deformations_relative.type())
    coordinate_grid = coordinate_grid.view(1, 1, h, w, 2)
    deformation = deformations_relative + coordinate_grid
    z_coordinate = torch.zeros(deformation.shape[:-1] + (1,)).type(deformation.type())
    return torch.cat([deformation, z_coordinate], dim=-1)

class IdentityDeformation(nn.Module):

    def forward(self, appearance_frame, kp_video, kp_appearance):
        bs, _, _, h, w = appearance_frame.shape
        _, d, num_kp, _ = kp_video['mean'].shape
        coordinate_grid = make_coordinate_grid((h, w), type=appearance_frame.type())
        coordinate_grid = coordinate_grid.view(1, 1, h, w, 2).repeat(bs, d, 1, 1, 1)
        z_coordinate = torch.zeros(coordinate_grid.shape[:-1] + (1,)).type(coordinate_grid.type())
        return torch.cat([coordinate_grid, z_coordinate], dim=-1)

def forward(self, appearance_frame, kp_video, kp_appearance):
    bs, _, _, h, w = appearance_frame.shape
    _, d, num_kp, _ = kp_video['mean'].shape
    coordinate_grid = make_coordinate_grid((h, w), type=appearance_frame.type())
    coordinate_grid = coordinate_grid.view(1, 1, h, w, 2).repeat(bs, d, 1, 1, 1)
    z_coordinate = torch.zeros(coordinate_grid.shape[:-1] + (1,)).type(coordinate_grid.type())
    return torch.cat([coordinate_grid, z_coordinate], dim=-1)

def mean_batch(val):
    return val.view(val.shape[0], -1).mean(-1)

class PredictionModule(nn.Module):
    """
    RNN for predicting kp movement
    """

    def __init__(self, num_kp=10, kp_variance=0.01, num_features=1024, num_layers=1, dropout=0.5):
        super(PredictionModule, self).__init__()
        input_size = num_kp * (2 + 4 * (kp_variance == 'matrix'))
        self.rnn = nn.GRU(input_size=input_size, hidden_size=num_features, num_layers=num_layers, dropout=dropout, batch_first=True)
        self.linear = nn.Linear(num_features, input_size)

    def net(self, input, h=None):
        output, h = self.rnn(input, h)
        init_shape = output.shape
        output = output.contiguous().view(-1, output.shape[-1])
        output = self.linear(output)
        return (output.view(init_shape[0], init_shape[1], output.shape[-1]), h)

    def forward(self, kp_batch):
        bs, d, num_kp, _ = kp_batch['mean'].shape
        inputs = [kp_batch['mean'].contiguous().view(bs, d, -1)]
        if 'var' in kp_batch:
            inputs.append(kp_batch['var'].contiguous().view(bs, d, -1))
        input = torch.cat(inputs, dim=-1)
        output, h = self.net(input)
        output = output.view(bs, d, num_kp, -1)
        mean = torch.tanh(output[:, :, :, :2])
        kp_array = {'mean': mean}
        if 'var' in kp_batch:
            var = output[:, :, :, 2:]
            var = var.view(bs, d, num_kp, 2, 2)
            var = torch.matmul(var.permute(0, 1, 2, 4, 3), var)
            kp_array['var'] = var
        return kp_array

def net(self, input, h=None):
    output, h = self.rnn(input, h)
    init_shape = output.shape
    output = output.contiguous().view(-1, output.shape[-1])
    output = self.linear(output)
    return (output.view(init_shape[0], init_shape[1], output.shape[-1]), h)

def forward(self, kp_batch):
    bs, d, num_kp, _ = kp_batch['mean'].shape
    inputs = [kp_batch['mean'].contiguous().view(bs, d, -1)]
    if 'var' in kp_batch:
        inputs.append(kp_batch['var'].contiguous().view(bs, d, -1))
    input = torch.cat(inputs, dim=-1)
    output, h = self.net(input)
    output = output.view(bs, d, num_kp, -1)
    mean = torch.tanh(output[:, :, :, :2])
    kp_array = {'mean': mean}
    if 'var' in kp_batch:
        var = output[:, :, :, 2:]
        var = var.view(bs, d, num_kp, 2, 2)
        var = torch.matmul(var.permute(0, 1, 2, 4, 3), var)
        kp_array['var'] = var
    return kp_array

def kp2gaussian(kp, spatial_size, kp_variance='matrix'):
    """
    Transform a keypoint into gaussian like representation
    """
    mean = kp['mean']
    coordinate_grid = make_coordinate_grid(spatial_size, mean.type())
    number_of_leading_dimensions = len(mean.shape) - 1
    shape = (1,) * number_of_leading_dimensions + coordinate_grid.shape
    coordinate_grid = coordinate_grid.view(*shape)
    repeats = mean.shape[:number_of_leading_dimensions] + (1, 1, 1)
    coordinate_grid = coordinate_grid.repeat(*repeats)
    shape = mean.shape[:number_of_leading_dimensions] + (1, 1, 2)
    mean = mean.view(*shape)
    mean_sub = coordinate_grid - mean
    if kp_variance == 'matrix':
        var = kp['var']
        inv_var = matrix_inverse(var)
        shape = inv_var.shape[:number_of_leading_dimensions] + (1, 1, 2, 2)
        inv_var = inv_var.view(*shape)
        under_exp = torch.matmul(torch.matmul(mean_sub.unsqueeze(-2), inv_var), mean_sub.unsqueeze(-1))
        under_exp = under_exp.squeeze(-1).squeeze(-1)
        out = torch.exp(-0.5 * under_exp)
    elif kp_variance == 'single':
        out = torch.exp(-0.5 * (mean_sub ** 2).sum(-1) / kp['var'])
    else:
        out = torch.exp(-0.5 * (mean_sub ** 2).sum(-1) / kp_variance)
    return out

def gaussian2kp(heatmap, kp_variance='matrix', clip_variance=None):
    """
    Extract the mean and the variance from a heatmap
    """
    shape = heatmap.shape
    heatmap = heatmap.unsqueeze(-1) + 1e-07
    grid = make_coordinate_grid(shape[3:], heatmap.type()).unsqueeze_(0).unsqueeze_(0).unsqueeze_(0)
    mean = (heatmap * grid).sum(dim=(3, 4))
    kp = {'mean': mean.permute(0, 2, 1, 3)}
    if kp_variance == 'matrix':
        mean_sub = grid - mean.unsqueeze(-2).unsqueeze(-2)
        var = torch.matmul(mean_sub.unsqueeze(-1), mean_sub.unsqueeze(-2))
        var = var * heatmap.unsqueeze(-1)
        var = var.sum(dim=(3, 4))
        var = var.permute(0, 2, 1, 3, 4)
        if clip_variance:
            min_norm = torch.tensor(clip_variance).type(var.type())
            sg = smallest_singular(var).unsqueeze(-1)
            var = torch.max(min_norm, sg) * var / sg
        kp['var'] = var
    elif kp_variance == 'single':
        mean_sub = grid - mean.unsqueeze(-2).unsqueeze(-2)
        var = mean_sub ** 2
        var = var * heatmap
        var = var.sum(dim=(3, 4))
        var = var.mean(dim=-1, keepdim=True)
        var = var.unsqueeze(-1)
        var = var.permute(0, 2, 1, 3, 4)
        kp['var'] = var
    return kp

class KPDetector(nn.Module):
    """
    Detecting a keypoints. Return keypoint position and variance.
    """

    def __init__(self, block_expansion, num_kp, num_channels, max_features, num_blocks, temperature, kp_variance, scale_factor=1, clip_variance=None):
        super(KPDetector, self).__init__()
        self.predictor = Hourglass(block_expansion, in_features=num_channels, out_features=num_kp, max_features=max_features, num_blocks=num_blocks)
        self.temperature = temperature
        self.kp_variance = kp_variance
        self.scale_factor = scale_factor
        self.clip_variance = clip_variance

    def forward(self, x):
        if self.scale_factor != 1:
            x = F.interpolate(x, scale_factor=(1, self.scale_factor, self.scale_factor))
        heatmap = self.predictor(x)
        final_shape = heatmap.shape
        heatmap = heatmap.view(final_shape[0], final_shape[1], final_shape[2], -1)
        heatmap = F.softmax(heatmap / self.temperature, dim=3)
        heatmap = heatmap.view(*final_shape)
        out = gaussian2kp(heatmap, self.kp_variance, self.clip_variance)
        return out

def forward(self, x):
    if self.scale_factor != 1:
        x = F.interpolate(x, scale_factor=(1, self.scale_factor, self.scale_factor))
    heatmap = self.predictor(x)
    final_shape = heatmap.shape
    heatmap = heatmap.view(final_shape[0], final_shape[1], final_shape[2], -1)
    heatmap = F.softmax(heatmap / self.temperature, dim=3)
    heatmap = heatmap.view(*final_shape)
    out = gaussian2kp(heatmap, self.kp_variance, self.clip_variance)
    return out

class DownBlock3D(nn.Module):
    """
    Simple block for processing video (encoder).
    """

    def __init__(self, in_features, out_features, norm=False, kernel_size=4):
        super(DownBlock3D, self).__init__()
        ka = kernel_size // 2
        kb = ka - 1 if kernel_size % 2 == 0 else ka
        self.conv = nn.Conv3d(in_channels=in_features, out_channels=out_features, kernel_size=(1, kernel_size, kernel_size))
        if norm:
            self.norm = nn.InstanceNorm3d(out_features, affine=True)
        else:
            self.norm = None

    def forward(self, x):
        out = x
        out = self.conv(out)
        if self.norm:
            out = self.norm(out)
        out = F.leaky_relu(out, 0.2)
        out = F.avg_pool3d(out, (1, 2, 2))
        return out

def forward(self, x):
    out = x
    out = self.conv(out)
    if self.norm:
        out = self.norm(out)
    out = F.leaky_relu(out, 0.2)
    out = F.avg_pool3d(out, (1, 2, 2))
    return out

class Discriminator(nn.Module):
    """
    Discriminator similar to Pix2Pix
    """

    def __init__(self, num_channels=3, num_kp=10, kp_variance=0.01, scale_factor=1, block_expansion=64, num_blocks=4, max_features=512, kp_embedding_params=None):
        super(Discriminator, self).__init__()
        if kp_embedding_params is not None:
            self.kp_embedding = MovementEmbeddingModule(num_kp=num_kp, kp_variance=kp_variance, num_channels=num_channels, **kp_embedding_params)
            embedding_channels = self.kp_embedding.out_channels
        else:
            self.kp_embedding = None
            embedding_channels = 0
        down_blocks = []
        for i in range(num_blocks):
            down_blocks.append(DownBlock3D(num_channels + embedding_channels if i == 0 else min(max_features, block_expansion * 2 ** i), min(max_features, block_expansion * 2 ** (i + 1)), norm=i != 0, kernel_size=4))
        self.down_blocks = nn.ModuleList(down_blocks)
        self.conv = nn.Conv3d(self.down_blocks[-1].conv.out_channels, out_channels=1, kernel_size=1)
        self.scale_factor = scale_factor

    def forward(self, x, kp_driving, kp_source):
        out_maps = [x]
        if self.scale_factor != 1:
            x = F.interpolate(x, scale_factor=(1, self.scale_factor, self.scale_factor))
        if self.kp_embedding:
            heatmap = self.kp_embedding(x, kp_driving, kp_source)
            out = torch.cat([x, heatmap], dim=1)
        else:
            out = x
        for down_block in self.down_blocks:
            out_maps.append(down_block(out))
            out = out_maps[-1]
        out = self.conv(out)
        out_maps.append(out)
        return out_maps

def forward(self, x, kp_driving, kp_source):
    out_maps = [x]
    if self.scale_factor != 1:
        x = F.interpolate(x, scale_factor=(1, self.scale_factor, self.scale_factor))
    if self.kp_embedding:
        heatmap = self.kp_embedding(x, kp_driving, kp_source)
        out = torch.cat([x, heatmap], dim=1)
    else:
        out = x
    for down_block in self.down_blocks:
        out_maps.append(down_block(out))
        out = out_maps[-1]
    out = self.conv(out)
    out_maps.append(out)
    return out_maps

class MovementEmbeddingModule(nn.Module):
    """
    Produce a keypoint representation that will be further used by other modules
    """

    def __init__(self, num_kp, kp_variance, num_channels, use_deformed_source_image=False, use_difference=False, use_heatmap=True, add_bg_feature_map=False, heatmap_type='gaussian', norm_const='sum', scale_factor=1):
        super(MovementEmbeddingModule, self).__init__()
        assert heatmap_type in ['gaussian', 'difference']
        assert int(use_heatmap) + int(use_deformed_source_image) + int(use_difference) >= 1
        self.out_channels = (1 * use_heatmap + 2 * use_difference + num_channels * use_deformed_source_image) * (num_kp + add_bg_feature_map)
        self.kp_variance = kp_variance
        self.heatmap_type = heatmap_type
        self.use_difference = use_difference
        self.use_deformed_source_image = use_deformed_source_image
        self.use_heatmap = use_heatmap
        self.add_bg_feature_map = add_bg_feature_map
        self.norm_const = norm_const
        self.scale_factor = scale_factor

    def normalize_heatmap(self, heatmap):
        if self.norm_const == 'sum':
            heatmap_shape = heatmap.shape
            heatmap = heatmap.view(heatmap_shape[0], heatmap_shape[1], heatmap_shape[2], -1)
            heatmap = heatmap / heatmap.sum(dim=3, keepdim=True)
            return heatmap.view(*heatmap_shape)
        else:
            return heatmap / self.norm_const

    def forward(self, source_image, kp_driving, kp_source):
        if self.scale_factor != 1:
            source_image = F.interpolate(source_image, scale_factor=(1, self.scale_factor, self.scale_factor))
        spatial_size = source_image.shape[3:]
        bs, _, _, h, w = source_image.shape
        _, d, num_kp, _ = kp_driving['mean'].shape
        inputs = []
        if self.use_heatmap:
            heatmap = self.normalize_heatmap(kp2gaussian(kp_driving, spatial_size=spatial_size, kp_variance=self.kp_variance))
            if self.heatmap_type == 'difference':
                heatmap_appearance = self.normalize_heatmap(kp2gaussian(kp_source, spatial_size=spatial_size, kp_variance=self.kp_variance))
                heatmap = heatmap - heatmap_appearance
            if self.add_bg_feature_map:
                zeros = torch.zeros(bs, d, 1, h, w).type(heatmap.type())
                heatmap = torch.cat([zeros, heatmap], dim=2)
            heatmap = heatmap.unsqueeze(3)
            inputs.append(heatmap)
        num_kp += self.add_bg_feature_map
        if self.use_difference or self.use_deformed_source_image:
            kp_video_diff = kp_source['mean'] - kp_driving['mean']
            if self.add_bg_feature_map:
                zeros = torch.zeros(bs, d, 1, 2).type(kp_video_diff.type())
                kp_video_diff = torch.cat([zeros, kp_video_diff], dim=2)
            kp_video_diff = kp_video_diff.view((bs, d, num_kp, 2, 1, 1)).repeat(1, 1, 1, 1, h, w)
        if self.use_difference:
            inputs.append(kp_video_diff)
        if self.use_deformed_source_image:
            appearance_repeat = source_image.unsqueeze(1).unsqueeze(1).repeat(1, d, num_kp, 1, 1, 1, 1)
            appearance_repeat = appearance_repeat.view(bs * d * num_kp, -1, h, w)
            deformation_approx = kp_video_diff.view((bs * d * num_kp, -1, h, w)).permute(0, 2, 3, 1)
            coordinate_grid = make_coordinate_grid((h, w), type=deformation_approx.type())
            coordinate_grid = coordinate_grid.view(1, h, w, 2)
            deformation_approx = coordinate_grid + deformation_approx
            appearance_approx_deform = F.grid_sample(appearance_repeat, deformation_approx)
            appearance_approx_deform = appearance_approx_deform.view((bs, d, num_kp, -1, h, w))
            inputs.append(appearance_approx_deform)
        movement_encoding = torch.cat(inputs, dim=3)
        movement_encoding = movement_encoding.view(bs, d, -1, h, w)
        return movement_encoding.permute(0, 2, 1, 3, 4)

def normalize_heatmap(self, heatmap):
    if self.norm_const == 'sum':
        heatmap_shape = heatmap.shape
        heatmap = heatmap.view(heatmap_shape[0], heatmap_shape[1], heatmap_shape[2], -1)
        heatmap = heatmap / heatmap.sum(dim=3, keepdim=True)
        return heatmap.view(*heatmap_shape)
    else:
        return heatmap / self.norm_const

def forward(self, source_image, kp_driving, kp_source):
    if self.scale_factor != 1:
        source_image = F.interpolate(source_image, scale_factor=(1, self.scale_factor, self.scale_factor))
    spatial_size = source_image.shape[3:]
    bs, _, _, h, w = source_image.shape
    _, d, num_kp, _ = kp_driving['mean'].shape
    inputs = []
    if self.use_heatmap:
        heatmap = self.normalize_heatmap(kp2gaussian(kp_driving, spatial_size=spatial_size, kp_variance=self.kp_variance))
        if self.heatmap_type == 'difference':
            heatmap_appearance = self.normalize_heatmap(kp2gaussian(kp_source, spatial_size=spatial_size, kp_variance=self.kp_variance))
            heatmap = heatmap - heatmap_appearance
        if self.add_bg_feature_map:
            zeros = torch.zeros(bs, d, 1, h, w).type(heatmap.type())
            heatmap = torch.cat([zeros, heatmap], dim=2)
        heatmap = heatmap.unsqueeze(3)
        inputs.append(heatmap)
    num_kp += self.add_bg_feature_map
    if self.use_difference or self.use_deformed_source_image:
        kp_video_diff = kp_source['mean'] - kp_driving['mean']
        if self.add_bg_feature_map:
            zeros = torch.zeros(bs, d, 1, 2).type(kp_video_diff.type())
            kp_video_diff = torch.cat([zeros, kp_video_diff], dim=2)
        kp_video_diff = kp_video_diff.view((bs, d, num_kp, 2, 1, 1)).repeat(1, 1, 1, 1, h, w)
    if self.use_difference:
        inputs.append(kp_video_diff)
    if self.use_deformed_source_image:
        appearance_repeat = source_image.unsqueeze(1).unsqueeze(1).repeat(1, d, num_kp, 1, 1, 1, 1)
        appearance_repeat = appearance_repeat.view(bs * d * num_kp, -1, h, w)
        deformation_approx = kp_video_diff.view((bs * d * num_kp, -1, h, w)).permute(0, 2, 3, 1)
        coordinate_grid = make_coordinate_grid((h, w), type=deformation_approx.type())
        coordinate_grid = coordinate_grid.view(1, h, w, 2)
        deformation_approx = coordinate_grid + deformation_approx
        appearance_approx_deform = F.grid_sample(appearance_repeat, deformation_approx)
        appearance_approx_deform = appearance_approx_deform.view((bs, d, num_kp, -1, h, w))
        inputs.append(appearance_approx_deform)
    movement_encoding = torch.cat(inputs, dim=3)
    movement_encoding = movement_encoding.view(bs, d, -1, h, w)
    return movement_encoding.permute(0, 2, 1, 3, 4)

def make_coordinate_grid(spatial_size, type):
    """
    Create a meshgrid [-1,1] x [-1,1] of given spatial_size.
    """
    h, w = spatial_size
    x = torch.arange(w).type(type)
    y = torch.arange(h).type(type)
    x = 2 * (x / (w - 1)) - 1
    y = 2 * (y / (h - 1)) - 1
    yy = y.view(-1, 1).repeat(1, w)
    xx = x.view(1, -1).repeat(h, 1)
    meshed = torch.cat([xx.unsqueeze_(2), yy.unsqueeze_(2)], 2)
    return meshed

class ResBlock3D(nn.Module):
    """
    Res block, preserve spatial resolution.
    """

    def __init__(self, in_features, kernel_size, padding):
        super(ResBlock3D, self).__init__()
        self.conv1 = nn.Conv3d(in_channels=in_features, out_channels=in_features, kernel_size=kernel_size, padding=padding)
        self.conv2 = nn.Conv3d(in_channels=in_features, out_channels=in_features, kernel_size=kernel_size, padding=padding)
        self.norm1 = BatchNorm3d(in_features, affine=True)
        self.norm2 = BatchNorm3d(in_features, affine=True)

    def forward(self, x):
        out = x
        out = self.norm1(x)
        out = F.relu(out)
        out = self.conv1(out)
        out = self.norm2(out)
        out = F.relu(out)
        out = self.conv2(out)
        out += x
        return out

def forward(self, x):
    out = x
    out = self.norm1(x)
    out = F.relu(out)
    out = self.conv1(out)
    out = self.norm2(out)
    out = F.relu(out)
    out = self.conv2(out)
    out += x
    return out

class UpBlock3D(nn.Module):
    """
    Simple block for processing video (decoder).
    """

    def __init__(self, in_features, out_features, kernel_size=3, padding=1):
        super(UpBlock3D, self).__init__()
        self.conv = nn.Conv3d(in_channels=in_features, out_channels=out_features, kernel_size=kernel_size, padding=padding)
        self.norm = BatchNorm3d(out_features, affine=True)

    def forward(self, x):
        out = F.interpolate(x, scale_factor=(1, 2, 2))
        out = self.conv(out)
        out = self.norm(out)
        out = F.relu(out)
        return out

def forward(self, x):
    out = F.interpolate(x, scale_factor=(1, 2, 2))
    out = self.conv(out)
    out = self.norm(out)
    out = F.relu(out)
    return out

class DownBlock3D(nn.Module):
    """
    Simple block for processing video (encoder).
    """

    def __init__(self, in_features, out_features, kernel_size=3, padding=1):
        super(DownBlock3D, self).__init__()
        self.conv = nn.Conv3d(in_channels=in_features, out_channels=out_features, kernel_size=kernel_size, padding=padding)
        self.norm = BatchNorm3d(out_features, affine=True)
        self.pool = nn.AvgPool3d(kernel_size=(1, 2, 2))

    def forward(self, x):
        out = self.conv(x)
        out = self.norm(out)
        out = F.relu(out)
        out = self.pool(out)
        return out

def forward(self, x):
    out = self.conv(x)
    out = self.norm(out)
    out = F.relu(out)
    out = self.pool(out)
    return out

class SameBlock3D(nn.Module):
    """
    Simple block with group convolution.
    """

    def __init__(self, in_features, out_features, groups=None, kernel_size=3, padding=1):
        super(SameBlock3D, self).__init__()
        self.conv = nn.Conv3d(in_channels=in_features, out_channels=out_features, kernel_size=kernel_size, padding=padding, groups=groups)
        self.norm = BatchNorm3d(out_features, affine=True)

    def forward(self, x):
        out = self.conv(x)
        out = self.norm(out)
        out = F.relu(out)
        return out

def forward(self, x):
    out = self.conv(x)
    out = self.norm(out)
    out = F.relu(out)
    return out

class Encoder(nn.Module):
    """
    Hourglass Encoder
    """

    def __init__(self, block_expansion, in_features, num_blocks=3, max_features=256, temporal=False):
        super(Encoder, self).__init__()
        down_blocks = []
        kernel_size = (3, 3, 3) if temporal else (1, 3, 3)
        padding = (1, 1, 1) if temporal else (0, 1, 1)
        for i in range(num_blocks):
            down_blocks.append(DownBlock3D(in_features if i == 0 else min(max_features, block_expansion * 2 ** i), min(max_features, block_expansion * 2 ** (i + 1)), kernel_size=kernel_size, padding=padding))
        self.down_blocks = nn.ModuleList(down_blocks)

    def forward(self, x):
        outs = [x]
        for down_block in self.down_blocks:
            outs.append(down_block(outs[-1]))
        return outs

def forward(self, x):
    outs = [x]
    for down_block in self.down_blocks:
        outs.append(down_block(outs[-1]))
    return outs

class Decoder(nn.Module):
    """
    Hourglass Decoder
    """

    def __init__(self, block_expansion, in_features, out_features, num_blocks=3, max_features=256, temporal=False, additional_features_for_block=0, use_last_conv=True):
        super(Decoder, self).__init__()
        kernel_size = (3, 3, 3) if temporal else (1, 3, 3)
        padding = (1, 1, 1) if temporal else (0, 1, 1)
        up_blocks = []
        for i in range(num_blocks)[::-1]:
            up_blocks.append(UpBlock3D((1 if i == num_blocks - 1 else 2) * min(max_features, block_expansion * 2 ** (i + 1)) + additional_features_for_block, min(max_features, block_expansion * 2 ** i), kernel_size=kernel_size, padding=padding))
        self.up_blocks = nn.ModuleList(up_blocks)
        if use_last_conv:
            self.conv = nn.Conv3d(in_channels=block_expansion + in_features + additional_features_for_block, out_channels=out_features, kernel_size=kernel_size, padding=padding)
        else:
            self.conv = None

    def forward(self, x):
        out = x.pop()
        for up_block in self.up_blocks:
            out = up_block(out)
            out = torch.cat([out, x.pop()], dim=1)
        if self.conv is not None:
            return self.conv(out)
        else:
            return out

def forward(self, x):
    out = x.pop()
    for up_block in self.up_blocks:
        out = up_block(out)
        out = torch.cat([out, x.pop()], dim=1)
    if self.conv is not None:
        return self.conv(out)
    else:
        return out

def matrix_det(batch_of_matrix):
    a = batch_of_matrix[..., 0, 0].unsqueeze(-1)
    b = batch_of_matrix[..., 0, 1].unsqueeze(-1)
    c = batch_of_matrix[..., 1, 0].unsqueeze(-1)
    d = batch_of_matrix[..., 1, 1].unsqueeze(-1)
    det = a * d - b * c
    return det

def matrix_trace(batch_of_matrix):
    a = batch_of_matrix[..., 0, 0].unsqueeze(-1)
    d = batch_of_matrix[..., 1, 1].unsqueeze(-1)
    return a + d

class MotionTransferGenerator(nn.Module):
    """
    Motion transfer generator. That Given a keypoints and an appearance trying to reconstruct the target frame.
    Produce 2 versions of target frame, one warped with predicted optical flow and other refined.
    """

    def __init__(self, num_channels, num_kp, kp_variance, block_expansion, max_features, num_blocks, num_refinement_blocks, dense_motion_params=None, kp_embedding_params=None, interpolation_mode='nearest'):
        super(MotionTransferGenerator, self).__init__()
        self.appearance_encoder = Encoder(block_expansion, in_features=num_channels, max_features=max_features, num_blocks=num_blocks)
        if kp_embedding_params is not None:
            self.kp_embedding_module = MovementEmbeddingModule(num_kp=num_kp, kp_variance=kp_variance, num_channels=num_channels, **kp_embedding_params)
            embedding_features = self.kp_embedding_module.out_channels
        else:
            self.kp_embedding_module = None
            embedding_features = 0
        if dense_motion_params is not None:
            self.dense_motion_module = DenseMotionModule(num_kp=num_kp, kp_variance=kp_variance, num_channels=num_channels, **dense_motion_params)
        else:
            self.dense_motion_module = IdentityDeformation()
        self.video_decoder = Decoder(block_expansion=block_expansion, in_features=num_channels, out_features=num_channels, max_features=max_features, num_blocks=num_blocks, additional_features_for_block=embedding_features, use_last_conv=False)
        self.refinement_module = torch.nn.Sequential()
        in_features = block_expansion + num_channels + embedding_features
        for i in range(num_refinement_blocks):
            self.refinement_module.add_module('r' + str(i), ResBlock3D(in_features, kernel_size=(1, 3, 3), padding=(0, 1, 1)))
        self.refinement_module.add_module('conv-last', nn.Conv3d(in_features, num_channels, kernel_size=1, padding=0))
        self.interpolation_mode = interpolation_mode

    def deform_input(self, inp, deformations_absolute):
        bs, d, h_old, w_old, _ = deformations_absolute.shape
        _, _, _, h, w = inp.shape
        deformations_absolute = deformations_absolute.permute(0, 4, 1, 2, 3)
        deformation = F.interpolate(deformations_absolute, size=(d, h, w), mode=self.interpolation_mode)
        deformation = deformation.permute(0, 2, 3, 4, 1)
        deformed_inp = F.grid_sample(inp, deformation)
        return deformed_inp

    def forward(self, source_image, kp_driving, kp_source):
        appearance_skips = self.appearance_encoder(source_image)
        deformations_absolute = self.dense_motion_module(source_image=source_image, kp_driving=kp_driving, kp_source=kp_source)
        deformed_skips = [self.deform_input(skip, deformations_absolute) for skip in appearance_skips]
        if self.kp_embedding_module is not None:
            d = kp_driving['mean'].shape[1]
            movement_embedding = self.kp_embedding_module(source_image=source_image, kp_driving=kp_driving, kp_source=kp_source)
            kp_skips = [F.interpolate(movement_embedding, size=(d,) + skip.shape[3:], mode=self.interpolation_mode) for skip in appearance_skips]
            skips = [torch.cat([a, b], dim=1) for a, b in zip(deformed_skips, kp_skips)]
        else:
            skips = deformed_skips
        video_deformed = self.deform_input(source_image, deformations_absolute)
        video_prediction = self.video_decoder(skips)
        video_prediction = self.refinement_module(video_prediction)
        video_prediction = torch.sigmoid(video_prediction)
        return {'video_prediction': video_prediction, 'video_deformed': video_deformed}

def deform_input(self, inp, deformations_absolute):
    bs, d, h_old, w_old, _ = deformations_absolute.shape
    _, _, _, h, w = inp.shape
    deformations_absolute = deformations_absolute.permute(0, 4, 1, 2, 3)
    deformation = F.interpolate(deformations_absolute, size=(d, h, w), mode=self.interpolation_mode)
    deformation = deformation.permute(0, 2, 3, 4, 1)
    deformed_inp = F.grid_sample(inp, deformation)
    return deformed_inp

def forward(self, source_image, kp_driving, kp_source):
    appearance_skips = self.appearance_encoder(source_image)
    deformations_absolute = self.dense_motion_module(source_image=source_image, kp_driving=kp_driving, kp_source=kp_source)
    deformed_skips = [self.deform_input(skip, deformations_absolute) for skip in appearance_skips]
    if self.kp_embedding_module is not None:
        d = kp_driving['mean'].shape[1]
        movement_embedding = self.kp_embedding_module(source_image=source_image, kp_driving=kp_driving, kp_source=kp_source)
        kp_skips = [F.interpolate(movement_embedding, size=(d,) + skip.shape[3:], mode=self.interpolation_mode) for skip in appearance_skips]
        skips = [torch.cat([a, b], dim=1) for a, b in zip(deformed_skips, kp_skips)]
    else:
        skips = deformed_skips
    video_deformed = self.deform_input(source_image, deformations_absolute)
    video_prediction = self.video_decoder(skips)
    video_prediction = self.refinement_module(video_prediction)
    video_prediction = torch.sigmoid(video_prediction)
    return {'video_prediction': video_prediction, 'video_deformed': video_deformed}

