# Cluster 32

class TransfuserBackbone(nn.Module):
    """
    Multi-scale Fusion Transformer for image + LiDAR feature fusion
    image_architecture: Architecture used in the image branch. ResNet, RegNet and ConvNext are supported
    lidar_architecture: Architecture used in the lidar branch. ResNet, RegNet and ConvNext are supported
    use_velocity: Whether to use the velocity input in the transformer.
    """

    def __init__(self, config, image_architecture='resnet34', lidar_architecture='resnet18', use_velocity=True):
        super().__init__()
        self.config = config
        self.avgpool_img = nn.AdaptiveAvgPool2d((self.config.img_vert_anchors, self.config.img_horz_anchors))
        self.avgpool_lidar = nn.AdaptiveAvgPool2d((self.config.lidar_vert_anchors, self.config.lidar_horz_anchors))
        self.image_encoder = ImageCNN(architecture=image_architecture, normalize=True, out_features=self.config.perception_output_features)
        if config.use_point_pillars == True:
            in_channels = config.num_features[-1]
        else:
            in_channels = 2 * config.lidar_seq_len
        if self.config.use_target_point_image == True:
            in_channels += 1
        self.lidar_encoder = LidarEncoder(architecture=lidar_architecture, in_channels=in_channels, out_features=self.config.perception_output_features)
        self.transformer1 = GPT(n_embd=self.image_encoder.features.feature_info[1]['num_chs'], n_head=config.n_head, block_exp=config.block_exp, n_layer=config.n_layer, img_vert_anchors=config.img_vert_anchors, img_horz_anchors=config.img_horz_anchors, lidar_vert_anchors=config.lidar_vert_anchors, lidar_horz_anchors=config.lidar_horz_anchors, seq_len=config.seq_len, embd_pdrop=config.embd_pdrop, attn_pdrop=config.attn_pdrop, resid_pdrop=config.resid_pdrop, config=config, use_velocity=use_velocity)
        self.transformer2 = GPT(n_embd=self.image_encoder.features.feature_info[2]['num_chs'], n_head=config.n_head, block_exp=config.block_exp, n_layer=config.n_layer, img_vert_anchors=config.img_vert_anchors, img_horz_anchors=config.img_horz_anchors, lidar_vert_anchors=config.lidar_vert_anchors, lidar_horz_anchors=config.lidar_horz_anchors, seq_len=config.seq_len, embd_pdrop=config.embd_pdrop, attn_pdrop=config.attn_pdrop, resid_pdrop=config.resid_pdrop, config=config, use_velocity=use_velocity)
        self.transformer3 = GPT(n_embd=self.image_encoder.features.feature_info[3]['num_chs'], n_head=config.n_head, block_exp=config.block_exp, n_layer=config.n_layer, img_vert_anchors=config.img_vert_anchors, img_horz_anchors=config.img_horz_anchors, lidar_vert_anchors=config.lidar_vert_anchors, lidar_horz_anchors=config.lidar_horz_anchors, seq_len=config.seq_len, embd_pdrop=config.embd_pdrop, attn_pdrop=config.attn_pdrop, resid_pdrop=config.resid_pdrop, config=config, use_velocity=use_velocity)
        self.transformer4 = GPT(n_embd=self.image_encoder.features.feature_info[4]['num_chs'], n_head=config.n_head, block_exp=config.block_exp, n_layer=config.n_layer, img_vert_anchors=config.img_vert_anchors, img_horz_anchors=config.img_horz_anchors, lidar_vert_anchors=config.lidar_vert_anchors, lidar_horz_anchors=config.lidar_horz_anchors, seq_len=config.seq_len, embd_pdrop=config.embd_pdrop, attn_pdrop=config.attn_pdrop, resid_pdrop=config.resid_pdrop, config=config, use_velocity=use_velocity)
        if self.image_encoder.features.feature_info[4]['num_chs'] != self.config.perception_output_features:
            self.change_channel_conv_image = nn.Conv2d(self.image_encoder.features.feature_info[4]['num_chs'], self.config.perception_output_features, (1, 1))
            self.change_channel_conv_lidar = nn.Conv2d(self.image_encoder.features.feature_info[4]['num_chs'], self.config.perception_output_features, (1, 1))
        else:
            self.change_channel_conv_image = nn.Sequential()
            self.change_channel_conv_lidar = nn.Sequential()
        channel = self.config.bev_features_chanels
        self.relu = nn.ReLU(inplace=True)
        self.upsample = nn.Upsample(scale_factor=self.config.bev_upsample_factor, mode='bilinear', align_corners=False)
        self.up_conv5 = nn.Conv2d(channel, channel, (1, 1))
        self.up_conv4 = nn.Conv2d(channel, channel, (1, 1))
        self.up_conv3 = nn.Conv2d(channel, channel, (1, 1))
        self.c5_conv = nn.Conv2d(self.config.perception_output_features, channel, (1, 1))

    def top_down(self, x):
        p5 = self.relu(self.c5_conv(x))
        p4 = self.relu(self.up_conv5(self.upsample(p5)))
        p3 = self.relu(self.up_conv4(self.upsample(p4)))
        p2 = self.relu(self.up_conv3(self.upsample(p3)))
        return (p2, p3, p4, p5)

    def forward(self, image, lidar, velocity):
        """
        Image + LiDAR feature fusion using transformers
        Args:
            image_list (list): list of input images
            lidar_list (list): list of input LiDAR BEV
            velocity (tensor): input velocity from speedometer
        """
        if self.image_encoder.normalize:
            image_tensor = normalize_imagenet(image)
        else:
            image_tensor = image
        lidar_tensor = lidar
        image_features = self.image_encoder.features.conv1(image_tensor)
        image_features = self.image_encoder.features.bn1(image_features)
        image_features = self.image_encoder.features.act1(image_features)
        image_features = self.image_encoder.features.maxpool(image_features)
        lidar_features = self.lidar_encoder._model.conv1(lidar_tensor)
        lidar_features = self.lidar_encoder._model.bn1(lidar_features)
        lidar_features = self.lidar_encoder._model.act1(lidar_features)
        lidar_features = self.lidar_encoder._model.maxpool(lidar_features)
        image_features = self.image_encoder.features.layer1(image_features)
        lidar_features = self.lidar_encoder._model.layer1(lidar_features)
        image_embd_layer1 = self.avgpool_img(image_features)
        lidar_embd_layer1 = self.avgpool_lidar(lidar_features)
        image_features_layer1, lidar_features_layer1 = self.transformer1(image_embd_layer1, lidar_embd_layer1, velocity)
        image_features_layer1 = F.interpolate(image_features_layer1, size=(image_features.shape[2], image_features.shape[3]), mode='bilinear', align_corners=False)
        lidar_features_layer1 = F.interpolate(lidar_features_layer1, size=(lidar_features.shape[2], lidar_features.shape[3]), mode='bilinear', align_corners=False)
        image_features = image_features + image_features_layer1
        lidar_features = lidar_features + lidar_features_layer1
        image_features = self.image_encoder.features.layer2(image_features)
        lidar_features = self.lidar_encoder._model.layer2(lidar_features)
        image_embd_layer2 = self.avgpool_img(image_features)
        lidar_embd_layer2 = self.avgpool_lidar(lidar_features)
        image_features_layer2, lidar_features_layer2 = self.transformer2(image_embd_layer2, lidar_embd_layer2, velocity)
        image_features_layer2 = F.interpolate(image_features_layer2, size=(image_features.shape[2], image_features.shape[3]), mode='bilinear', align_corners=False)
        lidar_features_layer2 = F.interpolate(lidar_features_layer2, size=(lidar_features.shape[2], lidar_features.shape[3]), mode='bilinear', align_corners=False)
        image_features = image_features + image_features_layer2
        lidar_features = lidar_features + lidar_features_layer2
        image_features = self.image_encoder.features.layer3(image_features)
        lidar_features = self.lidar_encoder._model.layer3(lidar_features)
        image_embd_layer3 = self.avgpool_img(image_features)
        lidar_embd_layer3 = self.avgpool_lidar(lidar_features)
        image_features_layer3, lidar_features_layer3 = self.transformer3(image_embd_layer3, lidar_embd_layer3, velocity)
        image_features_layer3 = F.interpolate(image_features_layer3, size=(image_features.shape[2], image_features.shape[3]), mode='bilinear', align_corners=False)
        lidar_features_layer3 = F.interpolate(lidar_features_layer3, size=(lidar_features.shape[2], lidar_features.shape[3]), mode='bilinear', align_corners=False)
        image_features = image_features + image_features_layer3
        lidar_features = lidar_features + lidar_features_layer3
        image_features = self.image_encoder.features.layer4(image_features)
        lidar_features = self.lidar_encoder._model.layer4(lidar_features)
        image_embd_layer4 = self.avgpool_img(image_features)
        lidar_embd_layer4 = self.avgpool_lidar(lidar_features)
        image_features_layer4, lidar_features_layer4 = self.transformer4(image_embd_layer4, lidar_embd_layer4, velocity)
        image_features_layer4 = F.interpolate(image_features_layer4, size=(image_features.shape[2], image_features.shape[3]), mode='bilinear', align_corners=False)
        lidar_features_layer4 = F.interpolate(lidar_features_layer4, size=(lidar_features.shape[2], lidar_features.shape[3]), mode='bilinear', align_corners=False)
        image_features = image_features + image_features_layer4
        lidar_features = lidar_features + lidar_features_layer4
        image_features = self.change_channel_conv_image(image_features)
        lidar_features = self.change_channel_conv_lidar(lidar_features)
        x4 = lidar_features
        image_features_grid = image_features
        image_features = self.image_encoder.features.global_pool(image_features)
        image_features = torch.flatten(image_features, 1)
        lidar_features = self.lidar_encoder._model.global_pool(lidar_features)
        lidar_features = torch.flatten(lidar_features, 1)
        fused_features = image_features + lidar_features
        features = self.top_down(x4)
        return (features, image_features_grid, fused_features)

def forward(self, image, lidar, velocity):
    """
        Image + LiDAR feature fusion using transformers
        Args:
            image_list (list): list of input images
            lidar_list (list): list of input LiDAR BEV
            velocity (tensor): input velocity from speedometer
        """
    if self.image_encoder.normalize:
        image_tensor = normalize_imagenet(image)
    else:
        image_tensor = image
    lidar_tensor = lidar
    image_features = self.image_encoder.features.conv1(image_tensor)
    image_features = self.image_encoder.features.bn1(image_features)
    image_features = self.image_encoder.features.act1(image_features)
    image_features = self.image_encoder.features.maxpool(image_features)
    lidar_features = self.lidar_encoder._model.conv1(lidar_tensor)
    lidar_features = self.lidar_encoder._model.bn1(lidar_features)
    lidar_features = self.lidar_encoder._model.act1(lidar_features)
    lidar_features = self.lidar_encoder._model.maxpool(lidar_features)
    image_features = self.image_encoder.features.layer1(image_features)
    lidar_features = self.lidar_encoder._model.layer1(lidar_features)
    image_embd_layer1 = self.avgpool_img(image_features)
    lidar_embd_layer1 = self.avgpool_lidar(lidar_features)
    image_features_layer1, lidar_features_layer1 = self.transformer1(image_embd_layer1, lidar_embd_layer1, velocity)
    image_features_layer1 = F.interpolate(image_features_layer1, size=(image_features.shape[2], image_features.shape[3]), mode='bilinear', align_corners=False)
    lidar_features_layer1 = F.interpolate(lidar_features_layer1, size=(lidar_features.shape[2], lidar_features.shape[3]), mode='bilinear', align_corners=False)
    image_features = image_features + image_features_layer1
    lidar_features = lidar_features + lidar_features_layer1
    image_features = self.image_encoder.features.layer2(image_features)
    lidar_features = self.lidar_encoder._model.layer2(lidar_features)
    image_embd_layer2 = self.avgpool_img(image_features)
    lidar_embd_layer2 = self.avgpool_lidar(lidar_features)
    image_features_layer2, lidar_features_layer2 = self.transformer2(image_embd_layer2, lidar_embd_layer2, velocity)
    image_features_layer2 = F.interpolate(image_features_layer2, size=(image_features.shape[2], image_features.shape[3]), mode='bilinear', align_corners=False)
    lidar_features_layer2 = F.interpolate(lidar_features_layer2, size=(lidar_features.shape[2], lidar_features.shape[3]), mode='bilinear', align_corners=False)
    image_features = image_features + image_features_layer2
    lidar_features = lidar_features + lidar_features_layer2
    image_features = self.image_encoder.features.layer3(image_features)
    lidar_features = self.lidar_encoder._model.layer3(lidar_features)
    image_embd_layer3 = self.avgpool_img(image_features)
    lidar_embd_layer3 = self.avgpool_lidar(lidar_features)
    image_features_layer3, lidar_features_layer3 = self.transformer3(image_embd_layer3, lidar_embd_layer3, velocity)
    image_features_layer3 = F.interpolate(image_features_layer3, size=(image_features.shape[2], image_features.shape[3]), mode='bilinear', align_corners=False)
    lidar_features_layer3 = F.interpolate(lidar_features_layer3, size=(lidar_features.shape[2], lidar_features.shape[3]), mode='bilinear', align_corners=False)
    image_features = image_features + image_features_layer3
    lidar_features = lidar_features + lidar_features_layer3
    image_features = self.image_encoder.features.layer4(image_features)
    lidar_features = self.lidar_encoder._model.layer4(lidar_features)
    image_embd_layer4 = self.avgpool_img(image_features)
    lidar_embd_layer4 = self.avgpool_lidar(lidar_features)
    image_features_layer4, lidar_features_layer4 = self.transformer4(image_embd_layer4, lidar_embd_layer4, velocity)
    image_features_layer4 = F.interpolate(image_features_layer4, size=(image_features.shape[2], image_features.shape[3]), mode='bilinear', align_corners=False)
    lidar_features_layer4 = F.interpolate(lidar_features_layer4, size=(lidar_features.shape[2], lidar_features.shape[3]), mode='bilinear', align_corners=False)
    image_features = image_features + image_features_layer4
    lidar_features = lidar_features + lidar_features_layer4
    image_features = self.change_channel_conv_image(image_features)
    lidar_features = self.change_channel_conv_lidar(lidar_features)
    x4 = lidar_features
    image_features_grid = image_features
    image_features = self.image_encoder.features.global_pool(image_features)
    image_features = torch.flatten(image_features, 1)
    lidar_features = self.lidar_encoder._model.global_pool(lidar_features)
    lidar_features = torch.flatten(lidar_features, 1)
    fused_features = image_features + lidar_features
    features = self.top_down(x4)
    return (features, image_features_grid, fused_features)

class SegDecoder(nn.Module):

    def __init__(self, config, latent_dim=512):
        super().__init__()
        self.config = config
        self.latent_dim = latent_dim
        self.num_class = config.num_class
        self.deconv1 = nn.Sequential(nn.Conv2d(self.latent_dim, self.config.deconv_channel_num_1, 3, 1, 1), nn.ReLU(True), nn.Conv2d(self.config.deconv_channel_num_1, self.config.deconv_channel_num_2, 3, 1, 1), nn.ReLU(True))
        self.deconv2 = nn.Sequential(nn.Conv2d(self.config.deconv_channel_num_2, self.config.deconv_channel_num_3, 3, 1, 1), nn.ReLU(True), nn.Conv2d(self.config.deconv_channel_num_3, self.config.deconv_channel_num_3, 3, 1, 1), nn.ReLU(True))
        self.deconv3 = nn.Sequential(nn.Conv2d(self.config.deconv_channel_num_3, self.config.deconv_channel_num_3, 3, 1, 1), nn.ReLU(True), nn.Conv2d(self.config.deconv_channel_num_3, self.num_class, 3, 1, 1))

    def forward(self, x):
        x = self.deconv1(x)
        x = F.interpolate(x, scale_factor=self.config.deconv_scale_factor_1, mode='bilinear', align_corners=False)
        x = self.deconv2(x)
        x = F.interpolate(x, scale_factor=self.config.deconv_scale_factor_2, mode='bilinear', align_corners=False)
        x = self.deconv3(x)
        return x

def forward(self, x):
    x = self.deconv1(x)
    x = F.interpolate(x, scale_factor=self.config.deconv_scale_factor_1, mode='bilinear', align_corners=False)
    x = self.deconv2(x)
    x = F.interpolate(x, scale_factor=self.config.deconv_scale_factor_2, mode='bilinear', align_corners=False)
    x = self.deconv3(x)
    return x

class DepthDecoder(nn.Module):

    def __init__(self, config, latent_dim=512):
        super().__init__()
        self.config = config
        self.latent_dim = latent_dim
        self.deconv1 = nn.Sequential(nn.Conv2d(self.latent_dim, self.config.deconv_channel_num_1, 3, 1, 1), nn.ReLU(True), nn.Conv2d(self.config.deconv_channel_num_1, self.config.deconv_channel_num_2, 3, 1, 1), nn.ReLU(True))
        self.deconv2 = nn.Sequential(nn.Conv2d(self.config.deconv_channel_num_2, self.config.deconv_channel_num_3, 3, 1, 1), nn.ReLU(True), nn.Conv2d(self.config.deconv_channel_num_3, self.config.deconv_channel_num_3, 3, 1, 1), nn.ReLU(True))
        self.deconv3 = nn.Sequential(nn.Conv2d(self.config.deconv_channel_num_3, self.config.deconv_channel_num_3, 3, 1, 1), nn.ReLU(True), nn.Conv2d(self.config.deconv_channel_num_3, 1, 3, 1, 1))

    def forward(self, x):
        x = self.deconv1(x)
        x = F.interpolate(x, scale_factor=self.config.deconv_scale_factor_1, mode='bilinear', align_corners=False)
        x = self.deconv2(x)
        x = F.interpolate(x, scale_factor=self.config.deconv_scale_factor_2, mode='bilinear', align_corners=False)
        x = self.deconv3(x)
        x = torch.sigmoid(x).squeeze(1)
        return x

def forward(self, x):
    x = self.deconv1(x)
    x = F.interpolate(x, scale_factor=self.config.deconv_scale_factor_1, mode='bilinear', align_corners=False)
    x = self.deconv2(x)
    x = F.interpolate(x, scale_factor=self.config.deconv_scale_factor_2, mode='bilinear', align_corners=False)
    x = self.deconv3(x)
    x = torch.sigmoid(x).squeeze(1)
    return x

class LateFusionBackbone(nn.Module):
    """
    image_architecture: Architecture used in the image branch. ResNet, RegNet and ConvNext are supported
    lidar_architecture: Architecture used in the lidar branch. ResNet, RegNet and ConvNext are supported
    use_velocity: Whether to use the velocity input in the transformer.
    """

    def __init__(self, config, image_architecture='resnet34', lidar_architecture='resnet18', use_velocity=0):
        super().__init__()
        self.config = config
        if config.use_point_pillars == True:
            in_channels = config.num_features[-1]
        else:
            in_channels = 2 * config.lidar_seq_len
        if self.config.use_target_point_image == True:
            in_channels += 1
        self.image_encoder = ImageCNN(architecture=image_architecture, normalize=True)
        self.lidar_encoder = LidarEncoder(architecture=lidar_architecture, in_channels=in_channels)
        if image_architecture.startswith('convnext'):
            self.norm_after_pool_img = nn.LayerNorm((self.config.perception_output_features,), eps=1e-06)
        else:
            self.norm_after_pool_img = nn.Sequential()
        if lidar_architecture.startswith('convnext'):
            self.norm_after_pool_lidar = nn.LayerNorm((self.config.perception_output_features,), eps=1e-06)
        else:
            self.norm_after_pool_lidar = nn.Sequential()
        self.use_velocity = use_velocity
        if use_velocity:
            self.vel_emb = nn.Linear(1, self.config.perception_output_features)
        channel = self.config.bev_features_chanels
        self.relu = nn.ReLU(inplace=True)
        if self.image_encoder.features.num_features != self.config.perception_output_features:
            self.reduce_channels_conv_image = nn.Conv2d(self.image_encoder.features.num_features, self.config.perception_output_features, (1, 1))
        else:
            self.reduce_channels_conv_image = nn.Sequential()
        if self.image_encoder.features.num_features != self.config.perception_output_features:
            self.reduce_channels_conv_lidar = nn.Conv2d(self.lidar_encoder._model.num_features, self.config.perception_output_features, (1, 1))
        else:
            self.reduce_channels_conv_lidar = nn.Sequential()
        self.upsample = nn.Upsample(scale_factor=self.config.bev_upsample_factor, mode='bilinear', align_corners=False)
        self.up_conv5 = nn.Conv2d(channel, channel, (1, 1))
        self.up_conv4 = nn.Conv2d(channel, channel, (1, 1))
        self.up_conv3 = nn.Conv2d(channel, channel, (1, 1))
        self.c5_conv = nn.Conv2d(self.config.perception_output_features, channel, (1, 1))

    def top_down(self, c5):
        p5 = self.relu(self.c5_conv(c5))
        p4 = self.relu(self.up_conv5(self.upsample(p5)))
        p3 = self.relu(self.up_conv4(self.upsample(p4)))
        p2 = self.relu(self.up_conv3(self.upsample(p3)))
        return (p2, p3, p4, p5)

    def forward(self, image, lidar, velocity):
        """
        Image + LiDAR feature fusion
        Args:
            image_list (list): list of input images
            lidar_list (list): list of input LiDAR BEV
            velocity (tensor): input velocity from speedometer
        """
        if self.image_encoder.normalize:
            image_tensor = normalize_imagenet(image)
        else:
            image_tensor = image
        output_features_image = self.image_encoder.features(image_tensor)
        output_features_image = self.reduce_channels_conv_image(output_features_image)
        image_features_grid = output_features_image
        image_features = torch.nn.AdaptiveAvgPool2d((1, 1))(output_features_image)
        image_features = torch.flatten(image_features, 1)
        image_features = self.norm_after_pool_img(image_features)
        output_features_lidar = self.lidar_encoder._model(lidar)
        output_features_lidar = self.reduce_channels_conv_lidar(output_features_lidar)
        lidar_features_grid = output_features_lidar
        features = self.top_down(lidar_features_grid)
        lidar_features = torch.nn.AdaptiveAvgPool2d((1, 1))(output_features_lidar)
        lidar_features = torch.flatten(lidar_features, 1)
        lidar_features = self.norm_after_pool_lidar(lidar_features)
        fused_features = torch.add(image_features, lidar_features)
        if self.use_velocity:
            velocity_embeddings = self.vel_emb(velocity)
            fused_features = torch.add(fused_features, velocity_embeddings)
        return (features, image_features_grid, fused_features)

def forward(self, image, lidar, velocity):
    """
        Image + LiDAR feature fusion
        Args:
            image_list (list): list of input images
            lidar_list (list): list of input LiDAR BEV
            velocity (tensor): input velocity from speedometer
        """
    if self.image_encoder.normalize:
        image_tensor = normalize_imagenet(image)
    else:
        image_tensor = image
    output_features_image = self.image_encoder.features(image_tensor)
    output_features_image = self.reduce_channels_conv_image(output_features_image)
    image_features_grid = output_features_image
    image_features = torch.nn.AdaptiveAvgPool2d((1, 1))(output_features_image)
    image_features = torch.flatten(image_features, 1)
    image_features = self.norm_after_pool_img(image_features)
    output_features_lidar = self.lidar_encoder._model(lidar)
    output_features_lidar = self.reduce_channels_conv_lidar(output_features_lidar)
    lidar_features_grid = output_features_lidar
    features = self.top_down(lidar_features_grid)
    lidar_features = torch.nn.AdaptiveAvgPool2d((1, 1))(output_features_lidar)
    lidar_features = torch.flatten(lidar_features, 1)
    lidar_features = self.norm_after_pool_lidar(lidar_features)
    fused_features = torch.add(image_features, lidar_features)
    if self.use_velocity:
        velocity_embeddings = self.vel_emb(velocity)
        fused_features = torch.add(fused_features, velocity_embeddings)
    return (features, image_features_grid, fused_features)

class latentTFBackbone(nn.Module):
    """
    Multi-scale Fusion Transformer for image + pos_embedding feature fusion
    image_architecture: Architecture used in the image branch. ResNet, RegNet and ConvNext are supported
    lidar_architecture: Architecture used in the lidar branch. ResNet, RegNet and ConvNext are supported
    use_velocity: Whether to use the velocity input in the transformer.
    """

    def __init__(self, config, image_architecture='resnet34', lidar_architecture='resnet18', use_velocity=True):
        super().__init__()
        self.config = config
        self.avgpool_img = nn.AdaptiveAvgPool2d((self.config.img_vert_anchors, self.config.img_horz_anchors))
        self.avgpool_lidar = nn.AdaptiveAvgPool2d((self.config.lidar_vert_anchors, self.config.lidar_horz_anchors))
        if config.use_point_pillars == True:
            in_channels = config.num_features[-1]
        else:
            in_channels = 2 * config.lidar_seq_len
        if self.config.use_target_point_image == True:
            in_channels += 1
        self.image_encoder = ImageCNN(architecture=image_architecture, normalize=True)
        self.lidar_encoder = LidarEncoder(architecture=lidar_architecture, in_channels=in_channels)
        self.transformer1 = GPT(n_embd=self.image_encoder.features.feature_info[1]['num_chs'], n_head=config.n_head, block_exp=config.block_exp, n_layer=config.n_layer, img_vert_anchors=config.img_vert_anchors, img_horz_anchors=config.img_horz_anchors, lidar_vert_anchors=config.lidar_vert_anchors, lidar_horz_anchors=config.lidar_horz_anchors, seq_len=config.seq_len, embd_pdrop=config.embd_pdrop, attn_pdrop=config.attn_pdrop, resid_pdrop=config.resid_pdrop, config=config, use_velocity=use_velocity)
        self.transformer2 = GPT(n_embd=self.image_encoder.features.feature_info[2]['num_chs'], n_head=config.n_head, block_exp=config.block_exp, n_layer=config.n_layer, img_vert_anchors=config.img_vert_anchors, img_horz_anchors=config.img_horz_anchors, lidar_vert_anchors=config.lidar_vert_anchors, lidar_horz_anchors=config.lidar_horz_anchors, seq_len=config.seq_len, embd_pdrop=config.embd_pdrop, attn_pdrop=config.attn_pdrop, resid_pdrop=config.resid_pdrop, config=config, use_velocity=use_velocity)
        self.transformer3 = GPT(n_embd=self.image_encoder.features.feature_info[3]['num_chs'], n_head=config.n_head, block_exp=config.block_exp, n_layer=config.n_layer, img_vert_anchors=config.img_vert_anchors, img_horz_anchors=config.img_horz_anchors, lidar_vert_anchors=config.lidar_vert_anchors, lidar_horz_anchors=config.lidar_horz_anchors, seq_len=config.seq_len, embd_pdrop=config.embd_pdrop, attn_pdrop=config.attn_pdrop, resid_pdrop=config.resid_pdrop, config=config, use_velocity=use_velocity)
        self.transformer4 = GPT(n_embd=self.image_encoder.features.feature_info[4]['num_chs'], n_head=config.n_head, block_exp=config.block_exp, n_layer=config.n_layer, img_vert_anchors=config.img_vert_anchors, img_horz_anchors=config.img_horz_anchors, lidar_vert_anchors=config.lidar_vert_anchors, lidar_horz_anchors=config.lidar_horz_anchors, seq_len=config.seq_len, embd_pdrop=config.embd_pdrop, attn_pdrop=config.attn_pdrop, resid_pdrop=config.resid_pdrop, config=config, use_velocity=use_velocity)
        if self.image_encoder.features.feature_info[4]['num_chs'] != self.config.perception_output_features:
            self.change_channel_conv_image = nn.Conv2d(self.image_encoder.features.feature_info[4]['num_chs'], self.config.perception_output_features, (1, 1))
            self.change_channel_conv_lidar = nn.Conv2d(self.image_encoder.features.feature_info[4]['num_chs'], self.config.perception_output_features, (1, 1))
        else:
            self.change_channel_conv_image = nn.Sequential()
            self.change_channel_conv_lidar = nn.Sequential()
        channel = self.config.bev_features_chanels
        self.relu = nn.ReLU(inplace=True)
        self.upsample = nn.Upsample(scale_factor=self.config.bev_upsample_factor, mode='bilinear', align_corners=False)
        self.up_conv5 = nn.Conv2d(channel, channel, (1, 1))
        self.up_conv4 = nn.Conv2d(channel, channel, (1, 1))
        self.up_conv3 = nn.Conv2d(channel, channel, (1, 1))
        self.c5_conv = nn.Conv2d(self.config.perception_output_features, channel, (1, 1))

    def top_down(self, x):
        p5 = self.relu(self.c5_conv(x))
        p4 = self.relu(self.up_conv5(self.upsample(p5)))
        p3 = self.relu(self.up_conv4(self.upsample(p4)))
        p2 = self.relu(self.up_conv3(self.upsample(p3)))
        return (p2, p3, p4, p5)

    def forward(self, image, lidar, velocity):
        """
        Image + LiDAR feature fusion using transformers
        Args:
            image: input rgb image
            lidar: LiDAR input will be replaced by positional encoding. Third channel may contain target point.
            velocity (tensor): input velocity from speedometer
        """
        if self.image_encoder.normalize:
            image_tensor = normalize_imagenet(image)
        else:
            image_tensor = image
        x = torch.linspace(-1, 1, self.config.lidar_resolution_width)
        y = torch.linspace(-1, 1, self.config.lidar_resolution_height)
        y_grid, x_grid = torch.meshgrid(x, y, indexing='ij')
        lidar[:, 0] = y_grid.unsqueeze(0)
        lidar[:, 1] = x_grid.unsqueeze(0)
        lidar_tensor = lidar
        image_features = self.image_encoder.features.conv1(image_tensor)
        image_features = self.image_encoder.features.bn1(image_features)
        image_features = self.image_encoder.features.act1(image_features)
        image_features = self.image_encoder.features.maxpool(image_features)
        lidar_features = self.lidar_encoder._model.conv1(lidar_tensor)
        lidar_features = self.lidar_encoder._model.bn1(lidar_features)
        lidar_features = self.lidar_encoder._model.act1(lidar_features)
        lidar_features = self.lidar_encoder._model.maxpool(lidar_features)
        image_features = self.image_encoder.features.layer1(image_features)
        lidar_features = self.lidar_encoder._model.layer1(lidar_features)
        image_embd_layer1 = self.avgpool_img(image_features)
        lidar_embd_layer1 = self.avgpool_lidar(lidar_features)
        image_features_layer1, lidar_features_layer1 = self.transformer1(image_embd_layer1, lidar_embd_layer1, velocity)
        image_features_layer1 = F.interpolate(image_features_layer1, size=(image_features.shape[2], image_features.shape[3]), mode='bilinear', align_corners=False)
        lidar_features_layer1 = F.interpolate(lidar_features_layer1, size=(lidar_features.shape[2], lidar_features.shape[3]), mode='bilinear', align_corners=False)
        image_features = image_features + image_features_layer1
        lidar_features = lidar_features + lidar_features_layer1
        image_features = self.image_encoder.features.layer2(image_features)
        lidar_features = self.lidar_encoder._model.layer2(lidar_features)
        image_embd_layer2 = self.avgpool_img(image_features)
        lidar_embd_layer2 = self.avgpool_lidar(lidar_features)
        image_features_layer2, lidar_features_layer2 = self.transformer2(image_embd_layer2, lidar_embd_layer2, velocity)
        image_features_layer2 = F.interpolate(image_features_layer2, size=(image_features.shape[2], image_features.shape[3]), mode='bilinear', align_corners=False)
        lidar_features_layer2 = F.interpolate(lidar_features_layer2, size=(lidar_features.shape[2], lidar_features.shape[3]), mode='bilinear', align_corners=False)
        image_features = image_features + image_features_layer2
        lidar_features = lidar_features + lidar_features_layer2
        image_features = self.image_encoder.features.layer3(image_features)
        lidar_features = self.lidar_encoder._model.layer3(lidar_features)
        image_embd_layer3 = self.avgpool_img(image_features)
        lidar_embd_layer3 = self.avgpool_lidar(lidar_features)
        image_features_layer3, lidar_features_layer3 = self.transformer3(image_embd_layer3, lidar_embd_layer3, velocity)
        image_features_layer3 = F.interpolate(image_features_layer3, size=(image_features.shape[2], image_features.shape[3]), mode='bilinear', align_corners=False)
        lidar_features_layer3 = F.interpolate(lidar_features_layer3, size=(lidar_features.shape[2], lidar_features.shape[3]), mode='bilinear', align_corners=False)
        image_features = image_features + image_features_layer3
        lidar_features = lidar_features + lidar_features_layer3
        image_features = self.image_encoder.features.layer4(image_features)
        lidar_features = self.lidar_encoder._model.layer4(lidar_features)
        image_embd_layer4 = self.avgpool_img(image_features)
        lidar_embd_layer4 = self.avgpool_lidar(lidar_features)
        image_features_layer4, lidar_features_layer4 = self.transformer4(image_embd_layer4, lidar_embd_layer4, velocity)
        image_features_layer4 = F.interpolate(image_features_layer4, size=(image_features.shape[2], image_features.shape[3]), mode='bilinear', align_corners=False)
        lidar_features_layer4 = F.interpolate(lidar_features_layer4, size=(lidar_features.shape[2], lidar_features.shape[3]), mode='bilinear', align_corners=False)
        image_features = image_features + image_features_layer4
        lidar_features = lidar_features + lidar_features_layer4
        image_features = self.change_channel_conv_image(image_features)
        lidar_features = self.change_channel_conv_lidar(lidar_features)
        x4 = lidar_features
        image_features_grid = image_features
        image_features = self.image_encoder.features.global_pool(image_features)
        image_features = torch.flatten(image_features, 1)
        lidar_features = self.lidar_encoder._model.global_pool(lidar_features)
        lidar_features = torch.flatten(lidar_features, 1)
        fused_features = image_features + lidar_features
        features = self.top_down(x4)
        return (features, image_features_grid, fused_features)

def forward(self, image, lidar, velocity):
    """
        Image + LiDAR feature fusion using transformers
        Args:
            image: input rgb image
            lidar: LiDAR input will be replaced by positional encoding. Third channel may contain target point.
            velocity (tensor): input velocity from speedometer
        """
    if self.image_encoder.normalize:
        image_tensor = normalize_imagenet(image)
    else:
        image_tensor = image
    x = torch.linspace(-1, 1, self.config.lidar_resolution_width)
    y = torch.linspace(-1, 1, self.config.lidar_resolution_height)
    y_grid, x_grid = torch.meshgrid(x, y, indexing='ij')
    lidar[:, 0] = y_grid.unsqueeze(0)
    lidar[:, 1] = x_grid.unsqueeze(0)
    lidar_tensor = lidar
    image_features = self.image_encoder.features.conv1(image_tensor)
    image_features = self.image_encoder.features.bn1(image_features)
    image_features = self.image_encoder.features.act1(image_features)
    image_features = self.image_encoder.features.maxpool(image_features)
    lidar_features = self.lidar_encoder._model.conv1(lidar_tensor)
    lidar_features = self.lidar_encoder._model.bn1(lidar_features)
    lidar_features = self.lidar_encoder._model.act1(lidar_features)
    lidar_features = self.lidar_encoder._model.maxpool(lidar_features)
    image_features = self.image_encoder.features.layer1(image_features)
    lidar_features = self.lidar_encoder._model.layer1(lidar_features)
    image_embd_layer1 = self.avgpool_img(image_features)
    lidar_embd_layer1 = self.avgpool_lidar(lidar_features)
    image_features_layer1, lidar_features_layer1 = self.transformer1(image_embd_layer1, lidar_embd_layer1, velocity)
    image_features_layer1 = F.interpolate(image_features_layer1, size=(image_features.shape[2], image_features.shape[3]), mode='bilinear', align_corners=False)
    lidar_features_layer1 = F.interpolate(lidar_features_layer1, size=(lidar_features.shape[2], lidar_features.shape[3]), mode='bilinear', align_corners=False)
    image_features = image_features + image_features_layer1
    lidar_features = lidar_features + lidar_features_layer1
    image_features = self.image_encoder.features.layer2(image_features)
    lidar_features = self.lidar_encoder._model.layer2(lidar_features)
    image_embd_layer2 = self.avgpool_img(image_features)
    lidar_embd_layer2 = self.avgpool_lidar(lidar_features)
    image_features_layer2, lidar_features_layer2 = self.transformer2(image_embd_layer2, lidar_embd_layer2, velocity)
    image_features_layer2 = F.interpolate(image_features_layer2, size=(image_features.shape[2], image_features.shape[3]), mode='bilinear', align_corners=False)
    lidar_features_layer2 = F.interpolate(lidar_features_layer2, size=(lidar_features.shape[2], lidar_features.shape[3]), mode='bilinear', align_corners=False)
    image_features = image_features + image_features_layer2
    lidar_features = lidar_features + lidar_features_layer2
    image_features = self.image_encoder.features.layer3(image_features)
    lidar_features = self.lidar_encoder._model.layer3(lidar_features)
    image_embd_layer3 = self.avgpool_img(image_features)
    lidar_embd_layer3 = self.avgpool_lidar(lidar_features)
    image_features_layer3, lidar_features_layer3 = self.transformer3(image_embd_layer3, lidar_embd_layer3, velocity)
    image_features_layer3 = F.interpolate(image_features_layer3, size=(image_features.shape[2], image_features.shape[3]), mode='bilinear', align_corners=False)
    lidar_features_layer3 = F.interpolate(lidar_features_layer3, size=(lidar_features.shape[2], lidar_features.shape[3]), mode='bilinear', align_corners=False)
    image_features = image_features + image_features_layer3
    lidar_features = lidar_features + lidar_features_layer3
    image_features = self.image_encoder.features.layer4(image_features)
    lidar_features = self.lidar_encoder._model.layer4(lidar_features)
    image_embd_layer4 = self.avgpool_img(image_features)
    lidar_embd_layer4 = self.avgpool_lidar(lidar_features)
    image_features_layer4, lidar_features_layer4 = self.transformer4(image_embd_layer4, lidar_embd_layer4, velocity)
    image_features_layer4 = F.interpolate(image_features_layer4, size=(image_features.shape[2], image_features.shape[3]), mode='bilinear', align_corners=False)
    lidar_features_layer4 = F.interpolate(lidar_features_layer4, size=(lidar_features.shape[2], lidar_features.shape[3]), mode='bilinear', align_corners=False)
    image_features = image_features + image_features_layer4
    lidar_features = lidar_features + lidar_features_layer4
    image_features = self.change_channel_conv_image(image_features)
    lidar_features = self.change_channel_conv_lidar(lidar_features)
    x4 = lidar_features
    image_features_grid = image_features
    image_features = self.image_encoder.features.global_pool(image_features)
    image_features = torch.flatten(image_features, 1)
    lidar_features = self.lidar_encoder._model.global_pool(lidar_features)
    lidar_features = torch.flatten(lidar_features, 1)
    fused_features = image_features + lidar_features
    features = self.top_down(x4)
    return (features, image_features_grid, fused_features)

def splat_points(point_cloud):
    pixels_per_meter = 8
    hist_max_per_pixel = 5
    x_meters_max = 16
    y_meters_max = 32
    xbins = np.linspace(-x_meters_max, x_meters_max, 32 * pixels_per_meter + 1)
    ybins = np.linspace(-y_meters_max, 0, 32 * pixels_per_meter + 1)
    hist = np.histogramdd(point_cloud[..., :2], bins=(xbins, ybins))[0]
    hist[hist > hist_max_per_pixel] = hist_max_per_pixel
    overhead_splat = hist / hist_max_per_pixel
    return overhead_splat

class GeometricFusionBackbone(nn.Module):
    """
    image_architecture: Architecture used in the image branch. ResNet, RegNet and ConvNext are supported
    lidar_architecture: Architecture used in the lidar branch. ResNet, RegNet and ConvNext are supported
    use_velocity: Whether to use the velocity input in the transformer.
    """

    def __init__(self, config, image_architecture='resnet34', lidar_architecture='resnet18', use_velocity=0):
        super().__init__()
        self.config = config
        self.use_velocity = use_velocity
        self.avgpool_img = nn.AdaptiveAvgPool2d((self.config.img_vert_anchors, self.config.img_horz_anchors))
        self.avgpool_lidar = nn.AdaptiveAvgPool2d((self.config.lidar_vert_anchors, self.config.lidar_horz_anchors))
        if config.use_point_pillars == True:
            in_channels = config.num_features[-1]
        else:
            in_channels = 2 * config.lidar_seq_len
        if self.config.use_target_point_image == True:
            in_channels += 1
        self.image_encoder = ImageCNN(architecture=image_architecture, normalize=True)
        self.lidar_encoder = LidarEncoder(architecture=lidar_architecture, in_channels=in_channels)
        self.image_conv1 = nn.Conv2d(self.image_encoder.features.feature_info[1]['num_chs'], config.n_embd, 1)
        self.image_conv2 = nn.Conv2d(self.image_encoder.features.feature_info[2]['num_chs'], config.n_embd, 1)
        self.image_conv3 = nn.Conv2d(self.image_encoder.features.feature_info[3]['num_chs'], config.n_embd, 1)
        self.image_conv4 = nn.Conv2d(self.image_encoder.features.feature_info[4]['num_chs'], config.n_embd, 1)
        self.image_deconv1 = nn.Conv2d(config.n_embd, self.image_encoder.features.feature_info[1]['num_chs'], 1)
        self.image_deconv2 = nn.Conv2d(config.n_embd, self.image_encoder.features.feature_info[2]['num_chs'], 1)
        self.image_deconv3 = nn.Conv2d(config.n_embd, self.image_encoder.features.feature_info[3]['num_chs'], 1)
        self.image_deconv4 = nn.Conv2d(config.n_embd, self.image_encoder.features.feature_info[4]['num_chs'], 1)
        if use_velocity:
            self.vel_emb1 = nn.Linear(1, self.image_encoder.features.feature_info[1]['num_chs'])
            self.vel_emb2 = nn.Linear(1, self.image_encoder.features.feature_info[2]['num_chs'])
            self.vel_emb3 = nn.Linear(1, self.image_encoder.features.feature_info[3]['num_chs'])
            self.vel_emb4 = nn.Linear(1, self.image_encoder.features.feature_info[4]['num_chs'])
        self.lidar_conv1 = nn.Conv2d(self.image_encoder.features.feature_info[1]['num_chs'], config.n_embd, 1)
        self.lidar_conv2 = nn.Conv2d(self.image_encoder.features.feature_info[2]['num_chs'], config.n_embd, 1)
        self.lidar_conv3 = nn.Conv2d(self.image_encoder.features.feature_info[3]['num_chs'], config.n_embd, 1)
        self.lidar_conv4 = nn.Conv2d(self.image_encoder.features.feature_info[4]['num_chs'], config.n_embd, 1)
        self.lidar_deconv1 = nn.Conv2d(config.n_embd, self.image_encoder.features.feature_info[1]['num_chs'], 1)
        self.lidar_deconv2 = nn.Conv2d(config.n_embd, self.image_encoder.features.feature_info[2]['num_chs'], 1)
        self.lidar_deconv3 = nn.Conv2d(config.n_embd, self.image_encoder.features.feature_info[3]['num_chs'], 1)
        self.lidar_deconv4 = nn.Conv2d(config.n_embd, self.image_encoder.features.feature_info[4]['num_chs'], 1)
        hid_dim = config.n_embd
        self.image_projection1 = nn.Sequential(nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True))
        self.image_projection2 = nn.Sequential(nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True))
        self.image_projection3 = nn.Sequential(nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True))
        self.image_projection4 = nn.Sequential(nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True))
        self.lidar_projection1 = nn.Sequential(nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True))
        self.lidar_projection2 = nn.Sequential(nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True))
        self.lidar_projection3 = nn.Sequential(nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True))
        self.lidar_projection4 = nn.Sequential(nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True))
        if self.image_encoder.features.feature_info[4]['num_chs'] != self.config.perception_output_features:
            self.change_channel_conv_image = nn.Conv2d(self.image_encoder.features.feature_info[4]['num_chs'], self.config.perception_output_features, (1, 1))
            self.change_channel_conv_lidar = nn.Conv2d(self.image_encoder.features.feature_info[4]['num_chs'], self.config.perception_output_features, (1, 1))
        else:
            self.change_channel_conv_image = nn.Sequential()
            self.change_channel_conv_lidar = nn.Sequential()
        channel = self.config.bev_features_chanels
        self.relu = nn.ReLU(inplace=True)
        self.upsample = nn.Upsample(scale_factor=self.config.bev_upsample_factor, mode='bilinear', align_corners=False)
        self.up_conv5 = nn.Conv2d(channel, channel, (1, 1))
        self.up_conv4 = nn.Conv2d(channel, channel, (1, 1))
        self.up_conv3 = nn.Conv2d(channel, channel, (1, 1))
        self.c5_conv = nn.Conv2d(self.config.perception_output_features, channel, (1, 1))

    def top_down(self, x):
        p5 = self.relu(self.c5_conv(x))
        p4 = self.relu(self.up_conv5(self.upsample(p5)))
        p3 = self.relu(self.up_conv4(self.upsample(p4)))
        p2 = self.relu(self.up_conv3(self.upsample(p3)))
        return (p2, p3, p4, p5)

    def forward(self, image, lidar, velocity, bev_points, img_points):
        """
        Image + LiDAR feature fusion using transformers
        Args:
            image_list (list): list of input images
            lidar_list (list): list of input LiDAR BEV
            velocity (tensor): input velocity from speedometer
            bev_points (tensor): projected image pixels onto the BEV grid
            cam_points (tensor): projected LiDAR point cloud onto the image space
        """
        if self.image_encoder.normalize:
            image_tensor = normalize_imagenet(image)
        else:
            image_tensor = image
        lidar_tensor = lidar
        bz = lidar_tensor.shape[0]
        image_features = self.image_encoder.features.conv1(image_tensor)
        image_features = self.image_encoder.features.bn1(image_features)
        image_features = self.image_encoder.features.act1(image_features)
        image_features = self.image_encoder.features.maxpool(image_features)
        lidar_features = self.lidar_encoder._model.conv1(lidar_tensor)
        lidar_features = self.lidar_encoder._model.bn1(lidar_features)
        lidar_features = self.lidar_encoder._model.act1(lidar_features)
        lidar_features = self.lidar_encoder._model.maxpool(lidar_features)
        image_features = self.image_encoder.features.layer1(image_features)
        lidar_features = self.lidar_encoder._model.layer1(lidar_features)
        if self.config.n_scale >= 4:
            image_embd_layer1 = self.image_conv1(image_features)
            image_embd_layer1 = self.avgpool_img(image_embd_layer1)
            lidar_embd_layer1 = self.lidar_conv1(lidar_features)
            lidar_embd_layer1 = self.avgpool_lidar(lidar_embd_layer1)
            curr_h_image, curr_w_image = image_embd_layer1.shape[-2:]
            curr_h_lidar, curr_w_lidar = lidar_embd_layer1.shape[-2:]
            bev_points_layer1 = bev_points.view(bz * curr_h_lidar * curr_w_lidar * 5, 2)
            bev_encoding_layer1 = image_embd_layer1.permute(0, 2, 3, 1).contiguous()[:, bev_points_layer1[:, 1], bev_points_layer1[:, 0]].view(bz, bz, curr_h_lidar, curr_w_lidar, 5, -1)
            bev_encoding_layer1 = torch.diagonal(bev_encoding_layer1, 0).permute(4, 3, 0, 1, 2).contiguous()
            bev_encoding_layer1 = torch.sum(bev_encoding_layer1, -1)
            bev_encoding_layer1 = self.image_projection1(bev_encoding_layer1.permute(0, 2, 3, 1)).permute(0, 3, 1, 2).contiguous()
            lidar_features_layer1 = F.interpolate(bev_encoding_layer1, scale_factor=8, mode='bilinear', align_corners=False)
            lidar_features_layer1 = self.lidar_deconv1(lidar_features_layer1)
            lidar_features = lidar_features + lidar_features_layer1
            if self.use_velocity:
                vel_embedding1 = self.vel_emb1(velocity).unsqueeze(-1).unsqueeze(-1)
                lidar_features = lidar_features + vel_embedding1
            img_points_layer1 = img_points.view(bz * curr_h_image * curr_w_image * 5, 2)
            img_encoding_layer1 = lidar_embd_layer1.permute(0, 2, 3, 1).contiguous()[:, img_points_layer1[:, 1], img_points_layer1[:, 0]].view(bz, bz, curr_h_image, curr_w_image, 5, -1)
            img_encoding_layer1 = torch.diagonal(img_encoding_layer1, 0).permute(4, 3, 0, 1, 2).contiguous()
            img_encoding_layer1 = torch.sum(img_encoding_layer1, -1)
            img_encoding_layer1 = self.lidar_projection1(img_encoding_layer1.permute(0, 2, 3, 1)).permute(0, 3, 1, 2).contiguous()
            image_features_layer1 = F.interpolate(img_encoding_layer1, scale_factor=8, mode='bilinear', align_corners=False)
            image_features_layer1 = self.image_deconv1(image_features_layer1)
            image_features = image_features + image_features_layer1
            if self.use_velocity:
                image_features = image_features + vel_embedding1
        image_features = self.image_encoder.features.layer2(image_features)
        lidar_features = self.lidar_encoder._model.layer2(lidar_features)
        if self.config.n_scale >= 3:
            image_embd_layer2 = self.image_conv2(image_features)
            image_embd_layer2 = self.avgpool_img(image_embd_layer2)
            lidar_embd_layer2 = self.lidar_conv2(lidar_features)
            lidar_embd_layer2 = self.avgpool_lidar(lidar_embd_layer2)
            curr_h_image, curr_w_image = image_embd_layer2.shape[-2:]
            curr_h_lidar, curr_w_lidar = lidar_embd_layer2.shape[-2:]
            bev_points_layer2 = bev_points.view(bz * curr_h_lidar * curr_w_lidar * 5, 2)
            bev_encoding_layer2 = image_embd_layer2.permute(0, 2, 3, 1).contiguous()[:, bev_points_layer2[:, 1], bev_points_layer2[:, 0]].view(bz, bz, curr_h_lidar, curr_w_lidar, 5, -1)
            bev_encoding_layer2 = torch.diagonal(bev_encoding_layer2, 0).permute(4, 3, 0, 1, 2).contiguous()
            bev_encoding_layer2 = torch.sum(bev_encoding_layer2, -1)
            bev_encoding_layer2 = self.image_projection2(bev_encoding_layer2.permute(0, 2, 3, 1)).permute(0, 3, 1, 2).contiguous()
            lidar_features_layer2 = F.interpolate(bev_encoding_layer2, scale_factor=4, mode='bilinear', align_corners=False)
            lidar_features_layer2 = self.lidar_deconv2(lidar_features_layer2)
            lidar_features = lidar_features + lidar_features_layer2
            if self.use_velocity:
                vel_embedding2 = self.vel_emb2(velocity).unsqueeze(-1).unsqueeze(-1)
                lidar_features = lidar_features + vel_embedding2
            img_points_layer2 = img_points.view(bz * curr_h_image * curr_w_image * 5, 2)
            img_encoding_layer2 = lidar_embd_layer2.permute(0, 2, 3, 1).contiguous()[:, img_points_layer2[:, 1], img_points_layer2[:, 0]].view(bz, bz, curr_h_image, curr_w_image, 5, -1)
            img_encoding_layer2 = torch.diagonal(img_encoding_layer2, 0).permute(4, 3, 0, 1, 2).contiguous()
            img_encoding_layer2 = torch.sum(img_encoding_layer2, -1)
            img_encoding_layer2 = self.lidar_projection2(img_encoding_layer2.permute(0, 2, 3, 1)).permute(0, 3, 1, 2).contiguous()
            image_features_layer2 = F.interpolate(img_encoding_layer2, scale_factor=4, mode='bilinear', align_corners=False)
            image_features_layer2 = self.image_deconv2(image_features_layer2)
            image_features = image_features + image_features_layer2
            if self.use_velocity:
                image_features = image_features + vel_embedding2
        image_features = self.image_encoder.features.layer3(image_features)
        lidar_features = self.lidar_encoder._model.layer3(lidar_features)
        if self.config.n_scale >= 2:
            image_embd_layer3 = self.image_conv3(image_features)
            image_embd_layer3 = self.avgpool_img(image_embd_layer3)
            lidar_embd_layer3 = self.lidar_conv3(lidar_features)
            lidar_embd_layer3 = self.avgpool_lidar(lidar_embd_layer3)
            curr_h_image, curr_w_image = image_embd_layer3.shape[-2:]
            curr_h_lidar, curr_w_lidar = lidar_embd_layer3.shape[-2:]
            bev_points_layer3 = bev_points.view(bz * curr_h_lidar * curr_w_lidar * 5, 2)
            bev_encoding_layer3 = image_embd_layer3.permute(0, 2, 3, 1).contiguous()[:, bev_points_layer3[:, 1], bev_points_layer3[:, 0]].view(bz, bz, curr_h_lidar, curr_w_lidar, 5, -1)
            bev_encoding_layer3 = torch.diagonal(bev_encoding_layer3, 0).permute(4, 3, 0, 1, 2).contiguous()
            bev_encoding_layer3 = torch.sum(bev_encoding_layer3, -1)
            bev_encoding_layer3 = self.image_projection3(bev_encoding_layer3.permute(0, 2, 3, 1)).permute(0, 3, 1, 2).contiguous()
            lidar_features_layer3 = F.interpolate(bev_encoding_layer3, scale_factor=2, mode='bilinear', align_corners=False)
            lidar_features_layer3 = self.lidar_deconv3(lidar_features_layer3)
            lidar_features = lidar_features + lidar_features_layer3
            if self.use_velocity:
                vel_embedding3 = self.vel_emb3(velocity).unsqueeze(-1).unsqueeze(-1)
                lidar_features = lidar_features + vel_embedding3
            img_points_layer3 = img_points.view(bz * curr_h_image * curr_w_image * 5, 2)
            img_encoding_layer3 = lidar_embd_layer3.permute(0, 2, 3, 1).contiguous()[:, img_points_layer3[:, 1], img_points_layer3[:, 0]].view(bz, bz, curr_h_image, curr_w_image, 5, -1)
            img_encoding_layer3 = torch.diagonal(img_encoding_layer3, 0).permute(4, 3, 0, 1, 2).contiguous()
            img_encoding_layer3 = torch.sum(img_encoding_layer3, -1)
            img_encoding_layer3 = self.lidar_projection3(img_encoding_layer3.permute(0, 2, 3, 1)).permute(0, 3, 1, 2).contiguous()
            image_features_layer3 = F.interpolate(img_encoding_layer3, scale_factor=2, mode='bilinear', align_corners=False)
            image_features_layer3 = self.image_deconv3(image_features_layer3)
            image_features = image_features + image_features_layer3
            if self.use_velocity:
                image_features = image_features + vel_embedding3
        image_features = self.image_encoder.features.layer4(image_features)
        lidar_features = self.lidar_encoder._model.layer4(lidar_features)
        if self.config.n_scale >= 1:
            image_embd_layer4 = self.image_conv4(image_features)
            image_embd_layer4 = self.avgpool_img(image_embd_layer4)
            lidar_embd_layer4 = self.lidar_conv4(lidar_features)
            lidar_embd_layer4 = self.avgpool_lidar(lidar_embd_layer4)
            curr_h_image, curr_w_image = image_embd_layer4.shape[-2:]
            curr_h_lidar, curr_w_lidar = lidar_embd_layer4.shape[-2:]
            bev_points_layer4 = bev_points.view(bz * curr_h_lidar * curr_w_lidar * 5, 2)
            bev_encoding_layer4 = image_embd_layer4.permute(0, 2, 3, 1).contiguous()[:, bev_points_layer4[:, 1], bev_points_layer4[:, 0]].view(bz, bz, curr_h_lidar, curr_w_lidar, 5, -1)
            bev_encoding_layer4 = torch.diagonal(bev_encoding_layer4, 0).permute(4, 3, 0, 1, 2).contiguous()
            bev_encoding_layer4 = torch.sum(bev_encoding_layer4, -1)
            bev_encoding_layer4 = self.image_projection4(bev_encoding_layer4.permute(0, 2, 3, 1)).permute(0, 3, 1, 2).contiguous()
            lidar_features_layer4 = self.lidar_deconv4(bev_encoding_layer4)
            lidar_features = lidar_features + lidar_features_layer4
            if self.use_velocity:
                vel_embedding4 = self.vel_emb4(velocity).unsqueeze(-1).unsqueeze(-1)
                lidar_features = lidar_features + vel_embedding4
            img_points_layer4 = img_points.view(bz * curr_h_image * curr_w_image * 5, 2)
            img_encoding_layer4 = lidar_embd_layer3.permute(0, 2, 3, 1).contiguous()[:, img_points_layer4[:, 1], img_points_layer4[:, 0]].view(bz, bz, curr_h_image, curr_w_image, 5, -1)
            img_encoding_layer4 = torch.diagonal(img_encoding_layer4, 0).permute(4, 3, 0, 1, 2).contiguous()
            img_encoding_layer4 = torch.sum(img_encoding_layer4, -1)
            img_encoding_layer4 = self.lidar_projection4(img_encoding_layer4.permute(0, 2, 3, 1)).permute(0, 3, 1, 2).contiguous()
            image_features_layer4 = self.image_deconv4(img_encoding_layer4)
            image_features = image_features + image_features_layer4
            if self.use_velocity:
                image_features = image_features + vel_embedding4
        image_features = self.change_channel_conv_image(image_features)
        lidar_features = self.change_channel_conv_lidar(lidar_features)
        x4 = lidar_features
        image_features_grid = image_features
        image_features = self.image_encoder.features.global_pool(image_features)
        image_features = torch.flatten(image_features, 1)
        lidar_features = self.lidar_encoder._model.global_pool(lidar_features)
        lidar_features = torch.flatten(lidar_features, 1)
        fused_features = image_features + lidar_features
        features = self.top_down(x4)
        return (features, image_features_grid, fused_features)

def forward(self, image, lidar, velocity, bev_points, img_points):
    """
        Image + LiDAR feature fusion using transformers
        Args:
            image_list (list): list of input images
            lidar_list (list): list of input LiDAR BEV
            velocity (tensor): input velocity from speedometer
            bev_points (tensor): projected image pixels onto the BEV grid
            cam_points (tensor): projected LiDAR point cloud onto the image space
        """
    if self.image_encoder.normalize:
        image_tensor = normalize_imagenet(image)
    else:
        image_tensor = image
    lidar_tensor = lidar
    bz = lidar_tensor.shape[0]
    image_features = self.image_encoder.features.conv1(image_tensor)
    image_features = self.image_encoder.features.bn1(image_features)
    image_features = self.image_encoder.features.act1(image_features)
    image_features = self.image_encoder.features.maxpool(image_features)
    lidar_features = self.lidar_encoder._model.conv1(lidar_tensor)
    lidar_features = self.lidar_encoder._model.bn1(lidar_features)
    lidar_features = self.lidar_encoder._model.act1(lidar_features)
    lidar_features = self.lidar_encoder._model.maxpool(lidar_features)
    image_features = self.image_encoder.features.layer1(image_features)
    lidar_features = self.lidar_encoder._model.layer1(lidar_features)
    if self.config.n_scale >= 4:
        image_embd_layer1 = self.image_conv1(image_features)
        image_embd_layer1 = self.avgpool_img(image_embd_layer1)
        lidar_embd_layer1 = self.lidar_conv1(lidar_features)
        lidar_embd_layer1 = self.avgpool_lidar(lidar_embd_layer1)
        curr_h_image, curr_w_image = image_embd_layer1.shape[-2:]
        curr_h_lidar, curr_w_lidar = lidar_embd_layer1.shape[-2:]
        bev_points_layer1 = bev_points.view(bz * curr_h_lidar * curr_w_lidar * 5, 2)
        bev_encoding_layer1 = image_embd_layer1.permute(0, 2, 3, 1).contiguous()[:, bev_points_layer1[:, 1], bev_points_layer1[:, 0]].view(bz, bz, curr_h_lidar, curr_w_lidar, 5, -1)
        bev_encoding_layer1 = torch.diagonal(bev_encoding_layer1, 0).permute(4, 3, 0, 1, 2).contiguous()
        bev_encoding_layer1 = torch.sum(bev_encoding_layer1, -1)
        bev_encoding_layer1 = self.image_projection1(bev_encoding_layer1.permute(0, 2, 3, 1)).permute(0, 3, 1, 2).contiguous()
        lidar_features_layer1 = F.interpolate(bev_encoding_layer1, scale_factor=8, mode='bilinear', align_corners=False)
        lidar_features_layer1 = self.lidar_deconv1(lidar_features_layer1)
        lidar_features = lidar_features + lidar_features_layer1
        if self.use_velocity:
            vel_embedding1 = self.vel_emb1(velocity).unsqueeze(-1).unsqueeze(-1)
            lidar_features = lidar_features + vel_embedding1
        img_points_layer1 = img_points.view(bz * curr_h_image * curr_w_image * 5, 2)
        img_encoding_layer1 = lidar_embd_layer1.permute(0, 2, 3, 1).contiguous()[:, img_points_layer1[:, 1], img_points_layer1[:, 0]].view(bz, bz, curr_h_image, curr_w_image, 5, -1)
        img_encoding_layer1 = torch.diagonal(img_encoding_layer1, 0).permute(4, 3, 0, 1, 2).contiguous()
        img_encoding_layer1 = torch.sum(img_encoding_layer1, -1)
        img_encoding_layer1 = self.lidar_projection1(img_encoding_layer1.permute(0, 2, 3, 1)).permute(0, 3, 1, 2).contiguous()
        image_features_layer1 = F.interpolate(img_encoding_layer1, scale_factor=8, mode='bilinear', align_corners=False)
        image_features_layer1 = self.image_deconv1(image_features_layer1)
        image_features = image_features + image_features_layer1
        if self.use_velocity:
            image_features = image_features + vel_embedding1
    image_features = self.image_encoder.features.layer2(image_features)
    lidar_features = self.lidar_encoder._model.layer2(lidar_features)
    if self.config.n_scale >= 3:
        image_embd_layer2 = self.image_conv2(image_features)
        image_embd_layer2 = self.avgpool_img(image_embd_layer2)
        lidar_embd_layer2 = self.lidar_conv2(lidar_features)
        lidar_embd_layer2 = self.avgpool_lidar(lidar_embd_layer2)
        curr_h_image, curr_w_image = image_embd_layer2.shape[-2:]
        curr_h_lidar, curr_w_lidar = lidar_embd_layer2.shape[-2:]
        bev_points_layer2 = bev_points.view(bz * curr_h_lidar * curr_w_lidar * 5, 2)
        bev_encoding_layer2 = image_embd_layer2.permute(0, 2, 3, 1).contiguous()[:, bev_points_layer2[:, 1], bev_points_layer2[:, 0]].view(bz, bz, curr_h_lidar, curr_w_lidar, 5, -1)
        bev_encoding_layer2 = torch.diagonal(bev_encoding_layer2, 0).permute(4, 3, 0, 1, 2).contiguous()
        bev_encoding_layer2 = torch.sum(bev_encoding_layer2, -1)
        bev_encoding_layer2 = self.image_projection2(bev_encoding_layer2.permute(0, 2, 3, 1)).permute(0, 3, 1, 2).contiguous()
        lidar_features_layer2 = F.interpolate(bev_encoding_layer2, scale_factor=4, mode='bilinear', align_corners=False)
        lidar_features_layer2 = self.lidar_deconv2(lidar_features_layer2)
        lidar_features = lidar_features + lidar_features_layer2
        if self.use_velocity:
            vel_embedding2 = self.vel_emb2(velocity).unsqueeze(-1).unsqueeze(-1)
            lidar_features = lidar_features + vel_embedding2
        img_points_layer2 = img_points.view(bz * curr_h_image * curr_w_image * 5, 2)
        img_encoding_layer2 = lidar_embd_layer2.permute(0, 2, 3, 1).contiguous()[:, img_points_layer2[:, 1], img_points_layer2[:, 0]].view(bz, bz, curr_h_image, curr_w_image, 5, -1)
        img_encoding_layer2 = torch.diagonal(img_encoding_layer2, 0).permute(4, 3, 0, 1, 2).contiguous()
        img_encoding_layer2 = torch.sum(img_encoding_layer2, -1)
        img_encoding_layer2 = self.lidar_projection2(img_encoding_layer2.permute(0, 2, 3, 1)).permute(0, 3, 1, 2).contiguous()
        image_features_layer2 = F.interpolate(img_encoding_layer2, scale_factor=4, mode='bilinear', align_corners=False)
        image_features_layer2 = self.image_deconv2(image_features_layer2)
        image_features = image_features + image_features_layer2
        if self.use_velocity:
            image_features = image_features + vel_embedding2
    image_features = self.image_encoder.features.layer3(image_features)
    lidar_features = self.lidar_encoder._model.layer3(lidar_features)
    if self.config.n_scale >= 2:
        image_embd_layer3 = self.image_conv3(image_features)
        image_embd_layer3 = self.avgpool_img(image_embd_layer3)
        lidar_embd_layer3 = self.lidar_conv3(lidar_features)
        lidar_embd_layer3 = self.avgpool_lidar(lidar_embd_layer3)
        curr_h_image, curr_w_image = image_embd_layer3.shape[-2:]
        curr_h_lidar, curr_w_lidar = lidar_embd_layer3.shape[-2:]
        bev_points_layer3 = bev_points.view(bz * curr_h_lidar * curr_w_lidar * 5, 2)
        bev_encoding_layer3 = image_embd_layer3.permute(0, 2, 3, 1).contiguous()[:, bev_points_layer3[:, 1], bev_points_layer3[:, 0]].view(bz, bz, curr_h_lidar, curr_w_lidar, 5, -1)
        bev_encoding_layer3 = torch.diagonal(bev_encoding_layer3, 0).permute(4, 3, 0, 1, 2).contiguous()
        bev_encoding_layer3 = torch.sum(bev_encoding_layer3, -1)
        bev_encoding_layer3 = self.image_projection3(bev_encoding_layer3.permute(0, 2, 3, 1)).permute(0, 3, 1, 2).contiguous()
        lidar_features_layer3 = F.interpolate(bev_encoding_layer3, scale_factor=2, mode='bilinear', align_corners=False)
        lidar_features_layer3 = self.lidar_deconv3(lidar_features_layer3)
        lidar_features = lidar_features + lidar_features_layer3
        if self.use_velocity:
            vel_embedding3 = self.vel_emb3(velocity).unsqueeze(-1).unsqueeze(-1)
            lidar_features = lidar_features + vel_embedding3
        img_points_layer3 = img_points.view(bz * curr_h_image * curr_w_image * 5, 2)
        img_encoding_layer3 = lidar_embd_layer3.permute(0, 2, 3, 1).contiguous()[:, img_points_layer3[:, 1], img_points_layer3[:, 0]].view(bz, bz, curr_h_image, curr_w_image, 5, -1)
        img_encoding_layer3 = torch.diagonal(img_encoding_layer3, 0).permute(4, 3, 0, 1, 2).contiguous()
        img_encoding_layer3 = torch.sum(img_encoding_layer3, -1)
        img_encoding_layer3 = self.lidar_projection3(img_encoding_layer3.permute(0, 2, 3, 1)).permute(0, 3, 1, 2).contiguous()
        image_features_layer3 = F.interpolate(img_encoding_layer3, scale_factor=2, mode='bilinear', align_corners=False)
        image_features_layer3 = self.image_deconv3(image_features_layer3)
        image_features = image_features + image_features_layer3
        if self.use_velocity:
            image_features = image_features + vel_embedding3
    image_features = self.image_encoder.features.layer4(image_features)
    lidar_features = self.lidar_encoder._model.layer4(lidar_features)
    if self.config.n_scale >= 1:
        image_embd_layer4 = self.image_conv4(image_features)
        image_embd_layer4 = self.avgpool_img(image_embd_layer4)
        lidar_embd_layer4 = self.lidar_conv4(lidar_features)
        lidar_embd_layer4 = self.avgpool_lidar(lidar_embd_layer4)
        curr_h_image, curr_w_image = image_embd_layer4.shape[-2:]
        curr_h_lidar, curr_w_lidar = lidar_embd_layer4.shape[-2:]
        bev_points_layer4 = bev_points.view(bz * curr_h_lidar * curr_w_lidar * 5, 2)
        bev_encoding_layer4 = image_embd_layer4.permute(0, 2, 3, 1).contiguous()[:, bev_points_layer4[:, 1], bev_points_layer4[:, 0]].view(bz, bz, curr_h_lidar, curr_w_lidar, 5, -1)
        bev_encoding_layer4 = torch.diagonal(bev_encoding_layer4, 0).permute(4, 3, 0, 1, 2).contiguous()
        bev_encoding_layer4 = torch.sum(bev_encoding_layer4, -1)
        bev_encoding_layer4 = self.image_projection4(bev_encoding_layer4.permute(0, 2, 3, 1)).permute(0, 3, 1, 2).contiguous()
        lidar_features_layer4 = self.lidar_deconv4(bev_encoding_layer4)
        lidar_features = lidar_features + lidar_features_layer4
        if self.use_velocity:
            vel_embedding4 = self.vel_emb4(velocity).unsqueeze(-1).unsqueeze(-1)
            lidar_features = lidar_features + vel_embedding4
        img_points_layer4 = img_points.view(bz * curr_h_image * curr_w_image * 5, 2)
        img_encoding_layer4 = lidar_embd_layer3.permute(0, 2, 3, 1).contiguous()[:, img_points_layer4[:, 1], img_points_layer4[:, 0]].view(bz, bz, curr_h_image, curr_w_image, 5, -1)
        img_encoding_layer4 = torch.diagonal(img_encoding_layer4, 0).permute(4, 3, 0, 1, 2).contiguous()
        img_encoding_layer4 = torch.sum(img_encoding_layer4, -1)
        img_encoding_layer4 = self.lidar_projection4(img_encoding_layer4.permute(0, 2, 3, 1)).permute(0, 3, 1, 2).contiguous()
        image_features_layer4 = self.image_deconv4(img_encoding_layer4)
        image_features = image_features + image_features_layer4
        if self.use_velocity:
            image_features = image_features + vel_embedding4
    image_features = self.change_channel_conv_image(image_features)
    lidar_features = self.change_channel_conv_lidar(lidar_features)
    x4 = lidar_features
    image_features_grid = image_features
    image_features = self.image_encoder.features.global_pool(image_features)
    image_features = torch.flatten(image_features, 1)
    lidar_features = self.lidar_encoder._model.global_pool(lidar_features)
    lidar_features = torch.flatten(lidar_features, 1)
    fused_features = image_features + lidar_features
    features = self.top_down(x4)
    return (features, image_features_grid, fused_features)

@HEADS.register_module()
class LidarCenterNetHead(BaseDenseHead, BBoxTestMixin):
    """Objects as Points Head. CenterHead use center_point to indicate object's
    position. Paper link <https://arxiv.org/abs/1904.07850>

    Args:
        in_channel (int): Number of channel in the input feature map.
        feat_channel (int): Number of channel in the intermediate feature map.
        num_classes (int): Number of categories excluding the background
            category.
        loss_center_heatmap (dict | None): Config of center heatmap loss.
            Default: GaussianFocalLoss.
        loss_wh (dict | None): Config of wh loss. Default: L1Loss.
        loss_offset (dict | None): Config of offset loss. Default: L1Loss.
        train_cfg (dict | None): Training config. Useless in CenterNet,
            but we keep this variable for SingleStageDetector. Default: None.
        test_cfg (dict | None): Testing config of CenterNet. Default: None.
        init_cfg (dict or list[dict], optional): Initialization config dict.
            Default: None
    """

    def __init__(self, in_channel, feat_channel, num_classes, loss_center_heatmap=dict(type='GaussianFocalLoss', loss_weight=1.0), loss_wh=dict(type='L1Loss', loss_weight=0.1), loss_offset=dict(type='L1Loss', loss_weight=1.0), loss_dir_class=dict(type='CrossEntropyLoss', loss_weight=1.0), loss_dir_res=dict(type='SmoothL1Loss', loss_weight=1.0), loss_velocity=dict(type='L1Loss', loss_weight=1.0), loss_brake=dict(type='CrossEntropyLoss', loss_weight=1.0), train_cfg=None, test_cfg=None, init_cfg=None):
        super(LidarCenterNetHead, self).__init__(init_cfg)
        self.num_classes = num_classes
        self.heatmap_head = self._build_head(in_channel, feat_channel, num_classes)
        self.wh_head = self._build_head(in_channel, feat_channel, 2)
        self.offset_head = self._build_head(in_channel, feat_channel, 2)
        self.num_dir_bins = train_cfg.num_dir_bins
        self.yaw_class_head = self._build_head(in_channel, feat_channel, self.num_dir_bins)
        self.yaw_res_head = self._build_head(in_channel, feat_channel, 1)
        self.velocity_head = self._build_head(in_channel, feat_channel, 1)
        self.brake_head = self._build_head(in_channel, feat_channel, 2)
        self.loss_center_heatmap = build_loss(loss_center_heatmap)
        self.loss_wh = build_loss(loss_wh)
        self.loss_offset = build_loss(loss_offset)
        self.loss_dir_class = build_loss(loss_dir_class)
        self.loss_dir_res = build_loss(loss_dir_res)
        self.loss_velocity = build_loss(loss_velocity)
        self.loss_brake = build_loss(loss_brake)
        self.train_cfg = train_cfg
        self.test_cfg = test_cfg
        self.fp16_enabled = train_cfg.fp16_enabled
        self.i = 0

    def _build_head(self, in_channel, feat_channel, out_channel):
        """Build head for each branch."""
        layer = nn.Sequential(nn.Conv2d(in_channel, feat_channel, kernel_size=3, padding=1), nn.ReLU(inplace=True), nn.Conv2d(feat_channel, out_channel, kernel_size=1))
        return layer

    def init_weights(self):
        """Initialize weights of the head."""
        bias_init = bias_init_with_prob(self.train_cfg.center_net_bias_init_with_prob)
        self.heatmap_head[-1].bias.data.fill_(bias_init)
        for head in [self.wh_head, self.offset_head]:
            for m in head.modules():
                if isinstance(m, nn.Conv2d):
                    normal_init(m, std=self.train_cfg.center_net_normal_init_std)

    def forward(self, feats):
        """Forward features. Notice CenterNet head does not use FPN.

        Args:
            feats (tuple[Tensor]): Features from the upstream network, each is
                a 4D-tensor.

        Returns:
            center_heatmap_preds (List[Tensor]): center predict heatmaps for
                all levels, the channels number is num_classes.
            wh_preds (List[Tensor]): wh predicts for all levels, the channels
                number is 2.
            offset_preds (List[Tensor]): offset predicts for all levels, the
               channels number is 2.
        """
        return multi_apply(self.forward_single, feats)

    def forward_single(self, feat):
        """Forward feature of a single level.

        Args:
            feat (Tensor): Feature of a single level.

        Returns:
            center_heatmap_pred (Tensor): center predict heatmaps, the
               channels number is num_classes.
            wh_pred (Tensor): wh predicts, the channels number is 2.
            offset_pred (Tensor): offset predicts, the channels number is 2.
        """
        center_heatmap_pred = self.heatmap_head(feat).sigmoid()
        wh_pred = self.wh_head(feat)
        offset_pred = self.offset_head(feat)
        yaw_class_pred = self.yaw_class_head(feat)
        yaw_res_pred = self.yaw_res_head(feat)
        velocity_pred = self.velocity_head(feat)
        brake_pred = self.brake_head(feat)
        return (center_heatmap_pred, wh_pred, offset_pred, yaw_class_pred, yaw_res_pred, velocity_pred, brake_pred)

    @force_fp32(apply_to=('center_heatmap_preds', 'wh_preds', 'offset_preds', 'yaw_class_preds', 'yaw_res_preds', 'velocity_pred', 'brake_pred'))
    def loss(self, center_heatmap_preds, wh_preds, offset_preds, yaw_class_preds, yaw_res_preds, velocity_preds, brake_preds, gt_bboxes, gt_labels, img_metas, gt_bboxes_ignore=None):
        """Compute losses of the head.

        Args:
            center_heatmap_preds (list[Tensor]): center predict heatmaps for
               all levels with shape (B, num_classes, H, W).
            wh_preds (list[Tensor]): wh predicts for all levels with
               shape (B, 2, H, W).
            offset_preds (list[Tensor]): offset predicts for all levels
               with shape (B, 2, H, W).
            gt_bboxes (list[Tensor]): Ground truth bboxes for each image with
                shape (num_gts, 4) in [tl_x, tl_y, br_x, br_y] format.
            gt_labels (list[Tensor]): class indices corresponding to each box.
            img_metas (list[dict]): Meta information of each image, e.g.,
                image size, scaling factor, etc.
            gt_bboxes_ignore (None | list[Tensor]): specify which bounding
                boxes can be ignored when computing the loss. Default: None

        Returns:
            dict[str, Tensor]: which has components below:
                - loss_center_heatmap (Tensor): loss of center heatmap.
                - loss_wh (Tensor): loss of hw heatmap
                - loss_offset (Tensor): loss of offset heatmap.
        """
        assert len(center_heatmap_preds) == len(wh_preds) == len(offset_preds) == 1
        center_heatmap_pred = center_heatmap_preds[0]
        wh_pred = wh_preds[0]
        offset_pred = offset_preds[0]
        yaw_class_pred = yaw_class_preds[0]
        yaw_res_pred = yaw_res_preds[0]
        velocity_pred = velocity_preds[0]
        brake_pred = brake_preds[0]
        target_result, avg_factor = self.get_targets(gt_bboxes, gt_labels, gt_bboxes_ignore, center_heatmap_pred.shape)
        center_heatmap_target = target_result['center_heatmap_target']
        wh_target = target_result['wh_target']
        yaw_class_target = target_result['yaw_class_target']
        yaw_res_target = target_result['yaw_res_target']
        offset_target = target_result['offset_target']
        velocity_target = target_result['velocity_target']
        brake_target = target_result['brake_target']
        wh_offset_target_weight = target_result['wh_offset_target_weight']
        loss_center_heatmap = self.loss_center_heatmap(center_heatmap_pred, center_heatmap_target, avg_factor=avg_factor)
        loss_wh = self.loss_wh(wh_pred, wh_target, wh_offset_target_weight, avg_factor=avg_factor * 2)
        loss_offset = self.loss_offset(offset_pred, offset_target, wh_offset_target_weight, avg_factor=avg_factor * 2)
        loss_yaw_class = self.loss_dir_class(yaw_class_pred, yaw_class_target, wh_offset_target_weight[:, :1, ...], avg_factor=avg_factor)
        loss_yaw_res = self.loss_dir_res(yaw_res_pred, yaw_res_target, wh_offset_target_weight[:, :1, ...], avg_factor=avg_factor)
        loss_velocity = self.loss_velocity(velocity_pred, velocity_target, wh_offset_target_weight[:, :1, ...], avg_factor=avg_factor)
        loss_brake = self.loss_brake(brake_pred, brake_target, wh_offset_target_weight[:, :1, ...], avg_factor=avg_factor)
        return dict(loss_center_heatmap=loss_center_heatmap, loss_wh=loss_wh, loss_offset=loss_offset, loss_yaw_class=loss_yaw_class, loss_yaw_res=loss_yaw_res, loss_velocity=loss_velocity, loss_brake=loss_brake)

    def angle2class(self, angle):
        """Convert continuous angle to a discrete class and a residual.
        Convert continuous angle to a discrete class and a small
        regression number from class center angle to current angle.
        Args:
            angle (torch.Tensor): Angle is from 0-2pi (or -pi~pi),
                class center at 0, 1*(2pi/N), 2*(2pi/N) ...  (N-1)*(2pi/N).
        Returns:
            tuple: Encoded discrete class and residual.
        """
        angle = angle % (2 * np.pi)
        angle_per_class = 2 * np.pi / float(self.num_dir_bins)
        shifted_angle = (angle + angle_per_class / 2) % (2 * np.pi)
        angle_cls = torch.div(shifted_angle, angle_per_class, rounding_mode='trunc')
        angle_res = shifted_angle - (angle_cls * angle_per_class + angle_per_class / 2)
        return (angle_cls.long(), angle_res)

    def class2angle(self, angle_cls, angle_res, limit_period=True):
        """Inverse function to angle2class.
        Args:
            angle_cls (torch.Tensor): Angle class to decode.
            angle_res (torch.Tensor): Angle residual to decode.
            limit_period (bool): Whether to limit angle to [-pi, pi].
        Returns:
            torch.Tensor: Angle decoded from angle_cls and angle_res.
        """
        angle_per_class = 2 * np.pi / float(self.num_dir_bins)
        angle_center = angle_cls.float() * angle_per_class
        angle = angle_center + angle_res
        if limit_period:
            angle[angle > np.pi] -= 2 * np.pi
        return angle

    def get_targets(self, gt_bboxes, gt_labels, gt_ignores, feat_shape):
        """Compute regression and classification targets in multiple images.

        Args:
            gt_bboxes (list[Tensor]): Ground truth bboxes for each image with
                shape (num_gts, 4) in [tl_x, tl_y, br_x, br_y] format.
            gt_labels (list[Tensor]): class indices corresponding to each box.
            feat_shape (list[int]): feature map shape with value [B, _, H, W]
            img_shape (list[int]): image shape in [h, w] format.

        Returns:
            tuple[dict,float]: The float value is mean avg_factor, the dict has
               components below:
               - center_heatmap_target (Tensor): targets of center heatmap,                    shape (B, num_classes, H, W).
               - wh_target (Tensor): targets of wh predict, shape                    (B, 2, H, W).
               - offset_target (Tensor): targets of offset predict, shape                    (B, 2, H, W).
               - wh_offset_target_weight (Tensor): weights of wh and offset                    predict, shape (B, 2, H, W).
        """
        img_h, img_w = (self.train_cfg.lidar_resolution_height, self.train_cfg.lidar_resolution_width)
        bs, _, feat_h, feat_w = feat_shape
        width_ratio = float(feat_w / img_w)
        height_ratio = float(feat_h / img_h)
        center_heatmap_target = gt_bboxes[-1].new_zeros([bs, self.num_classes, feat_h, feat_w])
        wh_target = gt_bboxes[-1].new_zeros([bs, 2, feat_h, feat_w])
        offset_target = gt_bboxes[-1].new_zeros([bs, 2, feat_h, feat_w])
        yaw_class_target = gt_bboxes[-1].new_zeros([bs, 1, feat_h, feat_w]).long()
        yaw_res_target = gt_bboxes[-1].new_zeros([bs, 1, feat_h, feat_w])
        velocity_target = gt_bboxes[-1].new_zeros([bs, 1, feat_h, feat_w])
        brake_target = gt_bboxes[-1].new_zeros([bs, 1, feat_h, feat_w]).long()
        wh_offset_target_weight = gt_bboxes[-1].new_zeros([bs, 2, feat_h, feat_w])
        for batch_id in range(bs):
            gt_bbox = gt_bboxes[0][batch_id]
            gt_label = gt_labels[0][batch_id]
            gt_ignore = gt_ignores[0][batch_id]
            center_x = gt_bbox[:, [0]] * width_ratio
            center_y = gt_bbox[:, [1]] * width_ratio
            gt_centers = torch.cat((center_x, center_y), dim=1)
            for j, ct in enumerate(gt_centers):
                if gt_ignore[j]:
                    continue
                ctx_int, cty_int = ct.int()
                ctx, cty = ct
                scale_box_h = gt_bbox[j, 3] * height_ratio
                scale_box_w = gt_bbox[j, 2] * width_ratio
                radius = gaussian_radius([scale_box_h, scale_box_w], min_overlap=0.1)
                radius = max(2, int(radius))
                ind = gt_label[j].long()
                gen_gaussian_target(center_heatmap_target[batch_id, ind], [ctx_int, cty_int], radius)
                wh_target[batch_id, 0, cty_int, ctx_int] = scale_box_w
                wh_target[batch_id, 1, cty_int, ctx_int] = scale_box_h
                yaw_class, yaw_res = self.angle2class(gt_bbox[j, 4])
                yaw_class_target[batch_id, 0, cty_int, ctx_int] = yaw_class
                yaw_res_target[batch_id, 0, cty_int, ctx_int] = yaw_res
                velocity_target[batch_id, 0, cty_int, ctx_int] = gt_bbox[j, 5]
                brake_target[batch_id, 0, cty_int, ctx_int] = gt_bbox[j, 6].long()
                offset_target[batch_id, 0, cty_int, ctx_int] = ctx - ctx_int
                offset_target[batch_id, 1, cty_int, ctx_int] = cty - cty_int
                wh_offset_target_weight[batch_id, :, cty_int, ctx_int] = 1
        avg_factor = max(1, center_heatmap_target.eq(1).sum())
        target_result = dict(center_heatmap_target=center_heatmap_target, wh_target=wh_target, yaw_class_target=yaw_class_target.squeeze(1), yaw_res_target=yaw_res_target, offset_target=offset_target, velocity_target=velocity_target, brake_target=brake_target.squeeze(1), wh_offset_target_weight=wh_offset_target_weight)
        return (target_result, avg_factor)

    def get_bboxes(self, center_heatmap_preds, wh_preds, offset_preds, yaw_class_preds, yaw_res_preds, velocity_preds, brake_preds, rescale=True, with_nms=False):
        """Transform network output for a batch into bbox predictions.

        Args:
            center_heatmap_preds (list[Tensor]): center predict heatmaps for
                all levels with shape (B, num_classes, H, W).
            wh_preds (list[Tensor]): wh predicts for all levels with
                shape (B, 2, H, W).
            offset_preds (list[Tensor]): offset predicts for all levels
                with shape (B, 2, H, W).
            img_metas (list[dict]): Meta information of each image, e.g.,
                image size, scaling factor, etc.
            rescale (bool): If True, return boxes in original image space.
                Default: True.
            with_nms (bool): If True, do nms before return boxes.
                Default: False.

        Returns:
            list[tuple[Tensor, Tensor]]: Each item in result_list is 2-tuple.
                The first item is an (n, 5) tensor, where 5 represent
                (tl_x, tl_y, br_x, br_y, score) and the score between 0 and 1.
                The shape of the second tensor in the tuple is (n,), and
                each element represents the class label of the corresponding
                box.
        """
        assert len(center_heatmap_preds) == len(wh_preds) == len(offset_preds) == 1
        batch_det_bboxes, batch_labels = self.decode_heatmap(center_heatmap_preds[0], wh_preds[0], offset_preds[0], yaw_class_preds[0], yaw_res_preds[0], velocity_preds[0], brake_preds[0], k=self.train_cfg.top_k_center_keypoints, kernel=self.train_cfg.center_net_max_pooling_kernel)
        if with_nms:
            det_results = []
            for det_bboxes, det_labels in zip(batch_det_bboxes, batch_labels):
                det_bbox, det_label = self._bboxes_nms(det_bboxes, det_labels, self.test_cfg)
                det_results.append(tuple([det_bbox, det_label]))
        else:
            det_results = [tuple(bs) for bs in zip(batch_det_bboxes, batch_labels)]
        return det_results

    def decode_heatmap(self, center_heatmap_pred, wh_pred, offset_pred, yaw_class_pred, yaw_res_pred, velocity_pred, brake_pred, k=100, kernel=3):
        """Transform outputs into detections raw bbox prediction.

        Args:
            center_heatmap_pred (Tensor): center predict heatmap,
               shape (B, num_classes, H, W).
            wh_pred (Tensor): wh predict, shape (B, 2, H, W).
            offset_pred (Tensor): offset predict, shape (B, 2, H, W).
            img_shape (list[int]): image shape in [h, w] format.
            k (int): Get top k center keypoints from heatmap. Default 100.
            kernel (int): Max pooling kernel for extract local maximum pixels.
               Default 3.

        Returns:
            tuple[torch.Tensor]: Decoded output of CenterNetHead, containing
               the following Tensors:

              - batch_bboxes (Tensor): Coords of each box with shape (B, k, 5)
              - batch_topk_labels (Tensor): Categories of each box with                   shape (B, k)
        """
        center_heatmap_pred = get_local_maximum(center_heatmap_pred, kernel=kernel)
        *batch_dets, topk_ys, topk_xs = get_topk_from_heatmap(center_heatmap_pred, k=k)
        batch_scores, batch_index, batch_topk_labels = batch_dets
        wh = transpose_and_gather_feat(wh_pred, batch_index)
        offset = transpose_and_gather_feat(offset_pred, batch_index)
        yaw_class = transpose_and_gather_feat(yaw_class_pred, batch_index)
        yaw_res = transpose_and_gather_feat(yaw_res_pred, batch_index)
        velocity = transpose_and_gather_feat(velocity_pred, batch_index)
        brake = transpose_and_gather_feat(brake_pred, batch_index)
        brake = torch.argmax(brake, -1)
        velocity = velocity[..., 0]
        yaw_class = torch.argmax(yaw_class, -1)
        yaw = self.class2angle(yaw_class, yaw_res.squeeze(2))
        topk_xs = topk_xs + offset[..., 0]
        topk_ys = topk_ys + offset[..., 1]
        ratio = 4.0
        batch_bboxes = torch.stack([topk_xs, topk_ys, wh[..., 0], wh[..., 1], yaw, velocity, brake], dim=2)
        batch_bboxes = torch.cat((batch_bboxes, batch_scores[..., None]), dim=-1)
        batch_bboxes[:, :, :4] *= ratio
        return (batch_bboxes, batch_topk_labels)

    def _bboxes_nms(self, bboxes, labels, cfg):
        if labels.numel() == 0:
            return (bboxes, labels)
        out_bboxes, keep = batched_nms(bboxes[:, :4].contiguous(), bboxes[:, -1].contiguous(), labels, cfg.nms_cfg)
        out_labels = labels[keep]
        if len(out_bboxes) > 0:
            idx = torch.argsort(out_bboxes[:, -1], descending=True)
            idx = idx[:cfg.max_per_img]
            out_bboxes = out_bboxes[idx]
            out_labels = out_labels[idx]
        return (out_bboxes, out_labels)

def forward_single(self, feat):
    """Forward feature of a single level.

        Args:
            feat (Tensor): Feature of a single level.

        Returns:
            center_heatmap_pred (Tensor): center predict heatmaps, the
               channels number is num_classes.
            wh_pred (Tensor): wh predicts, the channels number is 2.
            offset_pred (Tensor): offset predicts, the channels number is 2.
        """
    center_heatmap_pred = self.heatmap_head(feat).sigmoid()
    wh_pred = self.wh_head(feat)
    offset_pred = self.offset_head(feat)
    yaw_class_pred = self.yaw_class_head(feat)
    yaw_res_pred = self.yaw_res_head(feat)
    velocity_pred = self.velocity_head(feat)
    brake_pred = self.brake_head(feat)
    return (center_heatmap_pred, wh_pred, offset_pred, yaw_class_pred, yaw_res_pred, velocity_pred, brake_pred)

