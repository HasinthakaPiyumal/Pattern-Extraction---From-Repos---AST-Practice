# Cluster 29

@TRANSFORMS.register_module()
class RandomColorJitter(object):
    """
    Random Color Jitter for 3D point cloud (refer torchvision)
    """

    def __init__(self, brightness=0, contrast=0, saturation=0, hue=0, p=0.95):
        self.brightness = self._check_input(brightness, 'brightness')
        self.contrast = self._check_input(contrast, 'contrast')
        self.saturation = self._check_input(saturation, 'saturation')
        self.hue = self._check_input(hue, 'hue', center=0, bound=(-0.5, 0.5), clip_first_on_zero=False)
        self.p = p

    @staticmethod
    def _check_input(value, name, center=1, bound=(0, float('inf')), clip_first_on_zero=True):
        if isinstance(value, numbers.Number):
            if value < 0:
                raise ValueError('If {} is a single number, it must be non negative.'.format(name))
            value = [center - float(value), center + float(value)]
            if clip_first_on_zero:
                value[0] = max(value[0], 0.0)
        elif isinstance(value, (tuple, list)) and len(value) == 2:
            if not bound[0] <= value[0] <= value[1] <= bound[1]:
                raise ValueError('{} values should be between {}'.format(name, bound))
        else:
            raise TypeError('{} should be a single number or a list/tuple with length 2.'.format(name))
        if value[0] == value[1] == center:
            value = None
        return value

    @staticmethod
    def blend(color1, color2, ratio):
        ratio = float(ratio)
        bound = 255.0
        return (ratio * color1 + (1.0 - ratio) * color2).clip(0, bound).astype(color1.dtype)

    @staticmethod
    def rgb2hsv(rgb):
        r, g, b = (rgb[..., 0], rgb[..., 1], rgb[..., 2])
        maxc = np.max(rgb, axis=-1)
        minc = np.min(rgb, axis=-1)
        eqc = maxc == minc
        cr = maxc - minc
        s = cr / (np.ones_like(maxc) * eqc + maxc * (1 - eqc))
        cr_divisor = np.ones_like(maxc) * eqc + cr * (1 - eqc)
        rc = (maxc - r) / cr_divisor
        gc = (maxc - g) / cr_divisor
        bc = (maxc - b) / cr_divisor
        hr = (maxc == r) * (bc - gc)
        hg = ((maxc == g) & (maxc != r)) * (2.0 + rc - bc)
        hb = ((maxc != g) & (maxc != r)) * (4.0 + gc - rc)
        h = hr + hg + hb
        h = (h / 6.0 + 1.0) % 1.0
        return np.stack((h, s, maxc), axis=-1)

    @staticmethod
    def hsv2rgb(hsv):
        h, s, v = (hsv[..., 0], hsv[..., 1], hsv[..., 2])
        i = np.floor(h * 6.0)
        f = h * 6.0 - i
        i = i.astype(np.int32)
        p = np.clip(v * (1.0 - s), 0.0, 1.0)
        q = np.clip(v * (1.0 - s * f), 0.0, 1.0)
        t = np.clip(v * (1.0 - s * (1.0 - f)), 0.0, 1.0)
        i = i % 6
        mask = np.expand_dims(i, axis=-1) == np.arange(6)
        a1 = np.stack((v, q, p, p, t, v), axis=-1)
        a2 = np.stack((t, v, v, q, p, p), axis=-1)
        a3 = np.stack((p, p, t, v, v, q), axis=-1)
        a4 = np.stack((a1, a2, a3), axis=-1)
        return np.einsum('...na, ...nab -> ...nb', mask.astype(hsv.dtype), a4)

    def adjust_brightness(self, color, brightness_factor):
        if brightness_factor < 0:
            raise ValueError('brightness_factor ({}) is not non-negative.'.format(brightness_factor))
        return self.blend(color, np.zeros_like(color), brightness_factor)

    def adjust_contrast(self, color, contrast_factor):
        if contrast_factor < 0:
            raise ValueError('contrast_factor ({}) is not non-negative.'.format(contrast_factor))
        mean = np.mean(RandomColorGrayScale.rgb_to_grayscale(color))
        return self.blend(color, mean, contrast_factor)

    def adjust_saturation(self, color, saturation_factor):
        if saturation_factor < 0:
            raise ValueError('saturation_factor ({}) is not non-negative.'.format(saturation_factor))
        gray = RandomColorGrayScale.rgb_to_grayscale(color)
        return self.blend(color, gray, saturation_factor)

    def adjust_hue(self, color, hue_factor):
        if not -0.5 <= hue_factor <= 0.5:
            raise ValueError('hue_factor ({}) is not in [-0.5, 0.5].'.format(hue_factor))
        orig_dtype = color.dtype
        hsv = self.rgb2hsv(color / 255.0)
        h, s, v = (hsv[..., 0], hsv[..., 1], hsv[..., 2])
        h = (h + hue_factor) % 1.0
        hsv = np.stack((h, s, v), axis=-1)
        color_hue_adj = (self.hsv2rgb(hsv) * 255.0).astype(orig_dtype)
        return color_hue_adj

    @staticmethod
    def get_params(brightness, contrast, saturation, hue):
        fn_idx = torch.randperm(4)
        b = None if brightness is None else np.random.uniform(brightness[0], brightness[1])
        c = None if contrast is None else np.random.uniform(contrast[0], contrast[1])
        s = None if saturation is None else np.random.uniform(saturation[0], saturation[1])
        h = None if hue is None else np.random.uniform(hue[0], hue[1])
        return (fn_idx, b, c, s, h)

    def __call__(self, data_dict):
        fn_idx, brightness_factor, contrast_factor, saturation_factor, hue_factor = self.get_params(self.brightness, self.contrast, self.saturation, self.hue)
        for fn_id in fn_idx:
            if fn_id == 0 and brightness_factor is not None and (np.random.rand() < self.p):
                data_dict['color'] = self.adjust_brightness(data_dict['color'], brightness_factor)
            elif fn_id == 1 and contrast_factor is not None and (np.random.rand() < self.p):
                data_dict['color'] = self.adjust_contrast(data_dict['color'], contrast_factor)
            elif fn_id == 2 and saturation_factor is not None and (np.random.rand() < self.p):
                data_dict['color'] = self.adjust_saturation(data_dict['color'], saturation_factor)
            elif fn_id == 3 and hue_factor is not None and (np.random.rand() < self.p):
                data_dict['color'] = self.adjust_hue(data_dict['color'], hue_factor)
        return data_dict

@staticmethod
def hsv2rgb(hsv):
    h, s, v = (hsv[..., 0], hsv[..., 1], hsv[..., 2])
    i = np.floor(h * 6.0)
    f = h * 6.0 - i
    i = i.astype(np.int32)
    p = np.clip(v * (1.0 - s), 0.0, 1.0)
    q = np.clip(v * (1.0 - s * f), 0.0, 1.0)
    t = np.clip(v * (1.0 - s * (1.0 - f)), 0.0, 1.0)
    i = i % 6
    mask = np.expand_dims(i, axis=-1) == np.arange(6)
    a1 = np.stack((v, q, p, p, t, v), axis=-1)
    a2 = np.stack((t, v, v, q, p, p), axis=-1)
    a3 = np.stack((p, p, t, v, v, q), axis=-1)
    a4 = np.stack((a1, a2, a3), axis=-1)
    return np.einsum('...na, ...nab -> ...nb', mask.astype(hsv.dtype), a4)

class UnpoolWithSkip(nn.Module):
    """
    Map Unpooling with skip connection
    """

    def __init__(self, in_channels, skip_channels, out_channels, bias=True, skip=True, backend='map'):
        super(UnpoolWithSkip, self).__init__()
        self.in_channels = in_channels
        self.skip_channels = skip_channels
        self.out_channels = out_channels
        self.skip = skip
        self.backend = backend
        assert self.backend in ['map', 'interp']
        self.proj = nn.Sequential(nn.Linear(in_channels, out_channels, bias=bias), PointBatchNorm(out_channels), nn.ReLU(inplace=True))
        self.proj_skip = nn.Sequential(nn.Linear(skip_channels, out_channels, bias=bias), PointBatchNorm(out_channels), nn.ReLU(inplace=True))

    def forward(self, points, skip_points, cluster=None):
        coord, feat, offset = points
        skip_coord, skip_feat, skip_offset = skip_points
        if self.backend == 'map' and cluster is not None:
            feat = self.proj(feat)[cluster]
        else:
            feat = pointops.interpolation(coord, skip_coord, self.proj(feat), offset, skip_offset)
        if self.skip:
            feat = feat + self.proj_skip(skip_feat)
        return [skip_coord, feat, skip_offset]

def forward(self, points, skip_points, cluster=None):
    coord, feat, offset = points
    skip_coord, skip_feat, skip_offset = skip_points
    if self.backend == 'map' and cluster is not None:
        feat = self.proj(feat)[cluster]
    else:
        feat = pointops.interpolation(coord, skip_coord, self.proj(feat), offset, skip_offset)
    if self.skip:
        feat = feat + self.proj_skip(skip_feat)
    return [skip_coord, feat, skip_offset]

class Encoder(nn.Module):

    def __init__(self, depth, in_channels, embed_channels, groups, grid_size=None, neighbours=16, qkv_bias=True, pe_multiplier=False, pe_bias=True, attn_drop_rate=None, drop_path_rate=None, enable_checkpoint=False):
        super(Encoder, self).__init__()
        self.down = GridPool(in_channels=in_channels, out_channels=embed_channels, grid_size=grid_size)
        self.blocks = BlockSequence(depth=depth, embed_channels=embed_channels, groups=groups, neighbours=neighbours, qkv_bias=qkv_bias, pe_multiplier=pe_multiplier, pe_bias=pe_bias, attn_drop_rate=attn_drop_rate if attn_drop_rate is not None else 0.0, drop_path_rate=drop_path_rate if drop_path_rate is not None else 0.0, enable_checkpoint=enable_checkpoint)

    def forward(self, points):
        points, cluster = self.down(points)
        return (self.blocks(points), cluster)

def forward(self, points):
    points, cluster = self.down(points)
    return (self.blocks(points), cluster)

class Decoder(nn.Module):

    def __init__(self, in_channels, skip_channels, embed_channels, groups, depth, neighbours=16, qkv_bias=True, pe_multiplier=False, pe_bias=True, attn_drop_rate=None, drop_path_rate=None, enable_checkpoint=False, unpool_backend='map'):
        super(Decoder, self).__init__()
        self.up = UnpoolWithSkip(in_channels=in_channels, out_channels=embed_channels, skip_channels=skip_channels, backend=unpool_backend)
        self.blocks = BlockSequence(depth=depth, embed_channels=embed_channels, groups=groups, neighbours=neighbours, qkv_bias=qkv_bias, pe_multiplier=pe_multiplier, pe_bias=pe_bias, attn_drop_rate=attn_drop_rate if attn_drop_rate is not None else 0.0, drop_path_rate=drop_path_rate if drop_path_rate is not None else 0.0, enable_checkpoint=enable_checkpoint)

    def forward(self, points, skip_points, cluster):
        points = self.up(points, skip_points, cluster)
        return self.blocks(points)

def forward(self, points, skip_points, cluster):
    points = self.up(points, skip_points, cluster)
    return self.blocks(points)

class GVAPatchEmbed(nn.Module):

    def __init__(self, depth, in_channels, embed_channels, groups, neighbours=16, qkv_bias=True, pe_multiplier=False, pe_bias=True, attn_drop_rate=0.0, drop_path_rate=0.0, enable_checkpoint=False):
        super(GVAPatchEmbed, self).__init__()
        self.in_channels = in_channels
        self.embed_channels = embed_channels
        self.proj = nn.Sequential(nn.Linear(in_channels, embed_channels, bias=False), PointBatchNorm(embed_channels), nn.ReLU(inplace=True))
        self.blocks = BlockSequence(depth=depth, embed_channels=embed_channels, groups=groups, neighbours=neighbours, qkv_bias=qkv_bias, pe_multiplier=pe_multiplier, pe_bias=pe_bias, attn_drop_rate=attn_drop_rate, drop_path_rate=drop_path_rate, enable_checkpoint=enable_checkpoint)

    def forward(self, points):
        coord, feat, offset = points
        feat = self.proj(feat)
        return self.blocks([coord, feat, offset])

def forward(self, points):
    coord, feat, offset = points
    feat = self.proj(feat)
    return self.blocks([coord, feat, offset])

class UnpoolWithSkip(nn.Module):
    """
    Map Unpooling with skip connection
    """

    def __init__(self, in_channels, skip_channels, out_channels, bias=True, skip=True, backend='map'):
        super(UnpoolWithSkip, self).__init__()
        self.in_channels = in_channels
        self.skip_channels = skip_channels
        self.out_channels = out_channels
        self.skip = skip
        self.backend = backend
        assert self.backend in ['map', 'interp']
        self.proj = nn.Sequential(nn.Linear(in_channels, out_channels, bias=bias), PointBatchNorm(out_channels), nn.ReLU(inplace=True))
        self.proj_skip = nn.Sequential(nn.Linear(skip_channels, out_channels, bias=bias), PointBatchNorm(out_channels), nn.ReLU(inplace=True))

    def forward(self, points, skip_points, cluster=None):
        coord, feat, offset = points
        skip_coord, skip_feat, skip_offset = skip_points
        if self.backend == 'map' and cluster is not None:
            feat = self.proj(feat)[cluster]
        else:
            feat = pointops.interpolation(coord, skip_coord, self.proj(feat), offset, skip_offset)
        if self.skip:
            feat = feat + self.proj_skip(skip_feat)
        return [skip_coord, feat, skip_offset]

def forward(self, points, skip_points, cluster=None):
    coord, feat, offset = points
    skip_coord, skip_feat, skip_offset = skip_points
    if self.backend == 'map' and cluster is not None:
        feat = self.proj(feat)[cluster]
    else:
        feat = pointops.interpolation(coord, skip_coord, self.proj(feat), offset, skip_offset)
    if self.skip:
        feat = feat + self.proj_skip(skip_feat)
    return [skip_coord, feat, skip_offset]

class Encoder(nn.Module):

    def __init__(self, depth, in_channels, embed_channels, groups, grid_size=None, neighbours=16, qkv_bias=True, pe_multiplier=False, pe_bias=True, attn_drop_rate=None, drop_path_rate=None, enable_checkpoint=False):
        super(Encoder, self).__init__()
        self.down = GridPool(in_channels=in_channels, out_channels=embed_channels, grid_size=grid_size)
        self.blocks = BlockSequence(depth=depth, embed_channels=embed_channels, groups=groups, neighbours=neighbours, qkv_bias=qkv_bias, pe_multiplier=pe_multiplier, pe_bias=pe_bias, attn_drop_rate=attn_drop_rate if attn_drop_rate is not None else 0.0, drop_path_rate=drop_path_rate if drop_path_rate is not None else 0.0, enable_checkpoint=enable_checkpoint)

    def forward(self, points):
        points, cluster = self.down(points)
        return (self.blocks(points), cluster)

def forward(self, points):
    points, cluster = self.down(points)
    return (self.blocks(points), cluster)

class Decoder(nn.Module):

    def __init__(self, in_channels, skip_channels, embed_channels, groups, depth, neighbours=16, qkv_bias=True, pe_multiplier=False, pe_bias=True, attn_drop_rate=None, drop_path_rate=None, enable_checkpoint=False, unpool_backend='map'):
        super(Decoder, self).__init__()
        self.up = UnpoolWithSkip(in_channels=in_channels, out_channels=embed_channels, skip_channels=skip_channels, backend=unpool_backend)
        self.blocks = BlockSequence(depth=depth, embed_channels=embed_channels, groups=groups, neighbours=neighbours, qkv_bias=qkv_bias, pe_multiplier=pe_multiplier, pe_bias=pe_bias, attn_drop_rate=attn_drop_rate if attn_drop_rate is not None else 0.0, drop_path_rate=drop_path_rate if drop_path_rate is not None else 0.0, enable_checkpoint=enable_checkpoint)

    def forward(self, points, skip_points, cluster):
        points = self.up(points, skip_points, cluster)
        return self.blocks(points)

def forward(self, points, skip_points, cluster):
    points = self.up(points, skip_points, cluster)
    return self.blocks(points)

class GVAPatchEmbed(nn.Module):

    def __init__(self, depth, in_channels, embed_channels, groups, neighbours=16, qkv_bias=True, pe_multiplier=False, pe_bias=True, attn_drop_rate=0.0, drop_path_rate=0.0, enable_checkpoint=False):
        super(GVAPatchEmbed, self).__init__()
        self.in_channels = in_channels
        self.embed_channels = embed_channels
        self.proj = nn.Sequential(nn.Linear(in_channels, embed_channels, bias=False), PointBatchNorm(embed_channels), nn.ReLU(inplace=True))
        self.blocks = BlockSequence(depth=depth, embed_channels=embed_channels, groups=groups, neighbours=neighbours, qkv_bias=qkv_bias, pe_multiplier=pe_multiplier, pe_bias=pe_bias, attn_drop_rate=attn_drop_rate, drop_path_rate=drop_path_rate, enable_checkpoint=enable_checkpoint)

    def forward(self, points):
        coord, feat, offset = points
        feat = self.proj(feat)
        return self.blocks([coord, feat, offset])

def forward(self, points):
    coord, feat, offset = points
    feat = self.proj(feat)
    return self.blocks([coord, feat, offset])

def initial_voxelize(z):
    pc_hash = F.sphash(torch.floor(z.C).int())
    sparse_hash = torch.unique(pc_hash)
    idx_query = F.sphashquery(pc_hash, sparse_hash)
    counts = F.spcount(idx_query.int(), len(sparse_hash))
    inserted_coords = F.spvoxelize(torch.floor(z.C), idx_query, counts)
    inserted_coords = torch.round(inserted_coords).int()
    inserted_feat = F.spvoxelize(z.F, idx_query, counts)
    new_tensor = SparseTensor(inserted_feat, inserted_coords, 1)
    new_tensor.cmaps.setdefault(new_tensor.stride, new_tensor.coords)
    z.additional_features['idx_query'][1] = idx_query
    z.additional_features['counts'][1] = counts
    return new_tensor

def point_to_voxel(x, z):
    if z.additional_features is None or z.additional_features.get('idx_query') is None or z.additional_features['idx_query'].get(x.s) is None:
        pc_hash = F.sphash(torch.cat([torch.floor(z.C[:, :3] / x.s[0]).int() * x.s[0], z.C[:, -1].int().view(-1, 1)], 1))
        sparse_hash = F.sphash(x.C)
        idx_query = F.sphashquery(pc_hash, sparse_hash)
        counts = F.spcount(idx_query.int(), x.C.shape[0])
        z.additional_features['idx_query'][x.s] = idx_query
        z.additional_features['counts'][x.s] = counts
    else:
        idx_query = z.additional_features['idx_query'][x.s]
        counts = z.additional_features['counts'][x.s]
    inserted_feat = F.spvoxelize(z.F, idx_query, counts)
    new_tensor = SparseTensor(inserted_feat, x.C, x.s)
    new_tensor.cmaps = x.cmaps
    new_tensor.kmaps = x.kmaps
    return new_tensor

def voxel_to_point(x, z, nearest=False):
    if z.idx_query is None or z.weights is None or z.idx_query.get(x.s) is None or (z.weights.get(x.s) is None):
        off = spnn.utils.get_kernel_offsets(2, x.s, 1, device=z.F.device)
        old_hash = F.sphash(torch.cat([torch.floor(z.C[:, :3] / x.s[0]).int() * x.s[0], z.C[:, -1].int().view(-1, 1)], 1), off)
        pc_hash = F.sphash(x.C.to(z.F.device))
        idx_query = F.sphashquery(old_hash, pc_hash)
        weights = F.calc_ti_weights(z.C, idx_query, scale=x.s[0]).transpose(0, 1).contiguous()
        idx_query = idx_query.transpose(0, 1).contiguous()
        if nearest:
            weights[:, 1:] = 0.0
            idx_query[:, 1:] = -1
        new_feat = F.spdevoxelize(x.F, idx_query, weights)
        new_tensor = PointTensor(new_feat, z.C, idx_query=z.idx_query, weights=z.weights)
        new_tensor.additional_features = z.additional_features
        new_tensor.idx_query[x.s] = idx_query
        new_tensor.weights[x.s] = weights
        z.idx_query[x.s] = idx_query
        z.weights[x.s] = weights
    else:
        new_feat = F.spdevoxelize(x.F, z.idx_query.get(x.s), z.weights.get(x.s))
        new_tensor = PointTensor(new_feat, z.C, idx_query=z.idx_query, weights=z.weights)
        new_tensor.additional_features = z.additional_features
    return new_tensor

class WindowAttention(nn.Module):
    """ Window based multi-head self attention (W-MSA) module with relative position bias.
    It supports both of shifted and non-shifted window.

    Args:
        dim (int): Number of input channels.
        window_size (tuple[int]): The height and width of the window.
        num_heads (int): Number of attention heads.
        qkv_bias (bool, optional):  If True, add a learnable bias to query, key, value. Default: True
        qk_scale (float | None, optional): Override default qk scale of head_dim ** -0.5 if set
        attn_drop (float, optional): Dropout ratio of attention weight. Default: 0.0
        proj_drop (float, optional): Dropout ratio of output. Default: 0.0
    """

    def __init__(self, dim, window_size, num_heads, quant_size, rel_query=True, rel_key=False, rel_value=False, qkv_bias=True, qk_scale=None, attn_drop=0.0, proj_drop=0.0):
        super().__init__()
        self.dim = dim
        self.num_heads = num_heads
        head_dim = dim // num_heads
        self.scale = qk_scale or head_dim ** (-0.5)
        self.window_size = window_size
        self.quant_size = quant_size
        self.rel_query = rel_query
        self.rel_key = rel_key
        self.rel_value = rel_value
        quant_grid_length = int((2 * window_size + 0.0001) // quant_size)
        if rel_query:
            self.relative_pos_query_table = nn.Parameter(torch.zeros(2 * quant_grid_length, num_heads, head_dim, 3))
            trunc_normal_(self.relative_pos_query_table, std=0.02)
        if rel_key:
            self.relative_pos_key_table = nn.Parameter(torch.zeros(2 * quant_grid_length, num_heads, head_dim, 3))
            trunc_normal_(self.relative_pos_key_table, std=0.02)
        if rel_value:
            self.relative_pos_value_table = nn.Parameter(torch.zeros(2 * quant_grid_length, num_heads, head_dim, 3))
            trunc_normal_(self.relative_pos_value_table, std=0.02)
        self.quant_grid_length = quant_grid_length
        self.qkv = nn.Linear(dim, dim * 3, bias=qkv_bias)
        self.attn_drop = nn.Dropout(attn_drop, inplace=True)
        self.proj = nn.Linear(dim, dim)
        self.proj_drop = nn.Dropout(proj_drop, inplace=True)
        self.softmax = nn.Softmax(dim=-1)

    def forward(self, feats, xyz, index_0, index_1, index_0_offsets, n_max):
        """ Forward function.

        Args:
            feats: N, C
            xyz: N, 3
            index_0: M,
            index_1: M,
        """
        N, C = feats.shape
        M = index_0.shape[0]
        assert index_0.shape[0] == index_1.shape[0]
        qkv = self.qkv(feats).reshape(N, 3, self.num_heads, C // self.num_heads).permute(1, 0, 2, 3).contiguous()
        query, key, value = (qkv[0], qkv[1], qkv[2])
        query = query * self.scale
        attn_flat = pointops.attention_step1_v2(query.float(), key.float(), index_1.int(), index_0_offsets.int(), n_max)
        relative_position = xyz[index_0] - xyz[index_1]
        relative_position = torch.round(relative_position * 100000) / 100000
        relative_position_index = (relative_position + 2 * self.window_size - 0.0001) // self.quant_size
        assert (relative_position_index >= 0).all()
        assert (relative_position_index <= 2 * self.quant_grid_length - 1).all()
        assert self.rel_query and self.rel_key
        if self.rel_query and self.rel_key:
            relative_position_bias = pointops.dot_prod_with_idx_v3(query.float(), index_0_offsets.int(), n_max, key.float(), index_1.int(), self.relative_pos_query_table.float(), self.relative_pos_key_table.float(), relative_position_index.int())
        elif self.rel_query:
            relative_position_bias = pointops.dot_prod_with_idx(query.float(), index_0.int(), self.relative_pos_query_table.float(), relative_position_index.int())
        elif self.rel_key:
            relative_position_bias = pointops.dot_prod_with_idx(key.float(), index_1.int(), self.relative_pos_key_table.float(), relative_position_index.int())
        else:
            relative_position_bias = 0.0
        attn_flat = attn_flat + relative_position_bias
        softmax_attn_flat = scatter_softmax(src=attn_flat, index=index_0, dim=0)
        if self.rel_value:
            x = pointops.attention_step2_with_rel_pos_value_v2(softmax_attn_flat.float(), value.float(), index_0_offsets.int(), n_max, index_1.int(), self.relative_pos_value_table.float(), relative_position_index.int())
        else:
            x = pointops.attention_step2(softmax_attn_flat.float(), value.float(), index_0.int(), index_1.int())
        x = x.view(N, C)
        x = self.proj(x)
        x = self.proj_drop(x)
        return x

def forward(self, feats, xyz, index_0, index_1, index_0_offsets, n_max):
    """ Forward function.

        Args:
            feats: N, C
            xyz: N, 3
            index_0: M,
            index_1: M,
        """
    N, C = feats.shape
    M = index_0.shape[0]
    assert index_0.shape[0] == index_1.shape[0]
    qkv = self.qkv(feats).reshape(N, 3, self.num_heads, C // self.num_heads).permute(1, 0, 2, 3).contiguous()
    query, key, value = (qkv[0], qkv[1], qkv[2])
    query = query * self.scale
    attn_flat = pointops.attention_step1_v2(query.float(), key.float(), index_1.int(), index_0_offsets.int(), n_max)
    relative_position = xyz[index_0] - xyz[index_1]
    relative_position = torch.round(relative_position * 100000) / 100000
    relative_position_index = (relative_position + 2 * self.window_size - 0.0001) // self.quant_size
    assert (relative_position_index >= 0).all()
    assert (relative_position_index <= 2 * self.quant_grid_length - 1).all()
    assert self.rel_query and self.rel_key
    if self.rel_query and self.rel_key:
        relative_position_bias = pointops.dot_prod_with_idx_v3(query.float(), index_0_offsets.int(), n_max, key.float(), index_1.int(), self.relative_pos_query_table.float(), self.relative_pos_key_table.float(), relative_position_index.int())
    elif self.rel_query:
        relative_position_bias = pointops.dot_prod_with_idx(query.float(), index_0.int(), self.relative_pos_query_table.float(), relative_position_index.int())
    elif self.rel_key:
        relative_position_bias = pointops.dot_prod_with_idx(key.float(), index_1.int(), self.relative_pos_key_table.float(), relative_position_index.int())
    else:
        relative_position_bias = 0.0
    attn_flat = attn_flat + relative_position_bias
    softmax_attn_flat = scatter_softmax(src=attn_flat, index=index_0, dim=0)
    if self.rel_value:
        x = pointops.attention_step2_with_rel_pos_value_v2(softmax_attn_flat.float(), value.float(), index_0_offsets.int(), n_max, index_1.int(), self.relative_pos_value_table.float(), relative_position_index.int())
    else:
        x = pointops.attention_step2(softmax_attn_flat.float(), value.float(), index_0.int(), index_1.int())
    x = x.view(N, C)
    x = self.proj(x)
    x = self.proj_drop(x)
    return x

class WindowAttention(nn.Module):
    """ Window based multi-head self attention (W-MSA) module with relative position bias.
    It supports both of shifted and non-shifted window.
    """

    def __init__(self, embed_channels, num_heads, window_size, quant_size, attn_drop=0.0, proj_drop=0.0, scale=None, rel_query=True, rel_key=True, rel_value=True, qkv_bias=True):
        super().__init__()
        self.embed_channels = embed_channels
        self.head_channels = embed_channels // num_heads
        self.num_heads = num_heads
        self.scale = scale or self.head_channels ** (-0.5)
        self.window_size = window_size
        self.quant_size = quant_size
        self.rel_query = rel_query
        self.rel_key = rel_key
        self.rel_value = rel_value
        self.quant_grid_length = int((2 * window_size + 0.0001) // quant_size)
        assert self.rel_query and self.rel_key
        if rel_query:
            self.relative_pos_query_table = nn.Parameter(torch.zeros(2 * self.quant_grid_length, self.num_heads, self.head_channels, 3))
            trunc_normal_(self.relative_pos_query_table, std=0.02)
        if rel_key:
            self.relative_pos_key_table = nn.Parameter(torch.zeros(2 * self.quant_grid_length, self.num_heads, self.head_channels, 3))
            trunc_normal_(self.relative_pos_query_table, std=0.02)
        if rel_value:
            self.relative_pos_value_table = nn.Parameter(torch.zeros(2 * self.quant_grid_length, self.num_heads, self.head_channels, 3))
            trunc_normal_(self.relative_pos_query_table, std=0.02)
        self.qkv = nn.Linear(embed_channels, embed_channels * 3, bias=qkv_bias)
        self.attn_drop = nn.Dropout(attn_drop, inplace=True)
        self.proj = nn.Linear(embed_channels, embed_channels)
        self.proj_drop = nn.Dropout(proj_drop, inplace=True)
        self.softmax = nn.Softmax(dim=-1)

    def forward(self, feats, coords, index_0, index_1, index_0_offsets, n_max):
        n, c = feats.shape
        m = index_0.shape[0]
        assert index_0.shape[0] == index_1.shape[0]
        qkv = self.qkv(feats).reshape(n, 3, self.num_heads, c // self.num_heads).permute(1, 0, 2, 3).contiguous()
        query, key, value = (qkv[0], qkv[1], qkv[2])
        query = query * self.scale
        attn_flat = pointops.attention_step1_v2(query.float(), key.float(), index_1.int(), index_0_offsets.int(), n_max)
        relative_position = coords[index_0] - coords[index_1]
        relative_position = torch.round(relative_position * 100000) / 100000
        relative_position_index = torch.div(relative_position + 2 * self.window_size - 0.0001, self.quant_size, rounding_mode='trunc')
        assert (relative_position_index >= 0).all()
        assert (relative_position_index <= 2 * self.quant_grid_length - 1).all()
        if self.rel_query and self.rel_key:
            relative_position_bias = pointops.dot_prod_with_idx_v3(query.float(), index_0_offsets.int(), n_max, key.float(), index_1.int(), self.relative_pos_query_table.float(), self.relative_pos_key_table.float(), relative_position_index.int())
        elif self.rel_query:
            relative_position_bias = pointops.dot_prod_with_idx(query.float(), index_0.int(), self.relative_pos_query_table.float(), relative_position_index.int())
        elif self.rel_key:
            relative_position_bias = pointops.dot_prod_with_idx(key.float(), index_1.int(), self.relative_pos_key_table.float(), relative_position_index.int())
        else:
            relative_position_bias = 0.0
        attn_flat += relative_position_bias
        softmax_attn_flat = scatter_softmax(src=attn_flat, index=index_0, dim=0)
        if self.rel_value:
            x = pointops.attention_step2_with_rel_pos_value_v2(softmax_attn_flat.float(), value.float(), index_0_offsets.int(), n_max, index_1.int(), self.relative_pos_value_table.float(), relative_position_index.int())
        else:
            x = pointops.attention_step2(softmax_attn_flat.float(), value.float(), index_0.int(), index_1.int())
        x = x.view(n, c)
        x = self.proj(x)
        x = self.proj_drop(x)
        return x

def forward(self, feats, coords, index_0, index_1, index_0_offsets, n_max):
    n, c = feats.shape
    m = index_0.shape[0]
    assert index_0.shape[0] == index_1.shape[0]
    qkv = self.qkv(feats).reshape(n, 3, self.num_heads, c // self.num_heads).permute(1, 0, 2, 3).contiguous()
    query, key, value = (qkv[0], qkv[1], qkv[2])
    query = query * self.scale
    attn_flat = pointops.attention_step1_v2(query.float(), key.float(), index_1.int(), index_0_offsets.int(), n_max)
    relative_position = coords[index_0] - coords[index_1]
    relative_position = torch.round(relative_position * 100000) / 100000
    relative_position_index = torch.div(relative_position + 2 * self.window_size - 0.0001, self.quant_size, rounding_mode='trunc')
    assert (relative_position_index >= 0).all()
    assert (relative_position_index <= 2 * self.quant_grid_length - 1).all()
    if self.rel_query and self.rel_key:
        relative_position_bias = pointops.dot_prod_with_idx_v3(query.float(), index_0_offsets.int(), n_max, key.float(), index_1.int(), self.relative_pos_query_table.float(), self.relative_pos_key_table.float(), relative_position_index.int())
    elif self.rel_query:
        relative_position_bias = pointops.dot_prod_with_idx(query.float(), index_0.int(), self.relative_pos_query_table.float(), relative_position_index.int())
    elif self.rel_key:
        relative_position_bias = pointops.dot_prod_with_idx(key.float(), index_1.int(), self.relative_pos_key_table.float(), relative_position_index.int())
    else:
        relative_position_bias = 0.0
    attn_flat += relative_position_bias
    softmax_attn_flat = scatter_softmax(src=attn_flat, index=index_0, dim=0)
    if self.rel_value:
        x = pointops.attention_step2_with_rel_pos_value_v2(softmax_attn_flat.float(), value.float(), index_0_offsets.int(), n_max, index_1.int(), self.relative_pos_value_table.float(), relative_position_index.int())
    else:
        x = pointops.attention_step2(softmax_attn_flat.float(), value.float(), index_0.int(), index_1.int())
    x = x.view(n, c)
    x = self.proj(x)
    x = self.proj_drop(x)
    return x

