# Cluster 23

class DataAugmentor(object):
    """
    Data Augmentor.

    Parameters
    ----------
    augment_config : list
        A list of augmentation configuration.

    Attributes
    ----------
    data_augmentor_queue : list
        The list of data augmented functions.
    """

    def __init__(self, augment_config, train=True):
        self.data_augmentor_queue = []
        self.train = train
        for cur_cfg in augment_config:
            cur_augmentor = getattr(self, cur_cfg['NAME'])(config=cur_cfg)
            self.data_augmentor_queue.append(cur_augmentor)

    def random_world_flip(self, data_dict=None, config=None):
        if data_dict is None:
            return partial(self.random_world_flip, config=config)
        gt_boxes, gt_mask, points = (data_dict['object_bbx_center'], data_dict['object_bbx_mask'], data_dict['lidar_np'])
        gt_boxes_valid = gt_boxes[gt_mask == 1]
        for cur_axis in config['ALONG_AXIS_LIST']:
            assert cur_axis in ['x', 'y']
            gt_boxes_valid, points = getattr(augment_utils, 'random_flip_along_%s' % cur_axis)(gt_boxes_valid, points)
        gt_boxes[:gt_boxes_valid.shape[0], :] = gt_boxes_valid
        data_dict['object_bbx_center'] = gt_boxes
        data_dict['object_bbx_mask'] = gt_mask
        data_dict['lidar_np'] = points
        return data_dict

    def random_world_rotation(self, data_dict=None, config=None):
        if data_dict is None:
            return partial(self.random_world_rotation, config=config)
        rot_range = config['WORLD_ROT_ANGLE']
        if not isinstance(rot_range, list):
            rot_range = [-rot_range, rot_range]
        gt_boxes, gt_mask, points = (data_dict['object_bbx_center'], data_dict['object_bbx_mask'], data_dict['lidar_np'])
        gt_boxes_valid = gt_boxes[gt_mask == 1]
        gt_boxes_valid, points = augment_utils.global_rotation(gt_boxes_valid, points, rot_range=rot_range)
        gt_boxes[:gt_boxes_valid.shape[0], :] = gt_boxes_valid
        data_dict['object_bbx_center'] = gt_boxes
        data_dict['object_bbx_mask'] = gt_mask
        data_dict['lidar_np'] = points
        return data_dict

    def random_world_scaling(self, data_dict=None, config=None):
        if data_dict is None:
            return partial(self.random_world_scaling, config=config)
        gt_boxes, gt_mask, points = (data_dict['object_bbx_center'], data_dict['object_bbx_mask'], data_dict['lidar_np'])
        gt_boxes_valid = gt_boxes[gt_mask == 1]
        gt_boxes_valid, points = augment_utils.global_scaling(gt_boxes_valid, points, config['WORLD_SCALE_RANGE'])
        gt_boxes[:gt_boxes_valid.shape[0], :] = gt_boxes_valid
        data_dict['object_bbx_center'] = gt_boxes
        data_dict['object_bbx_mask'] = gt_mask
        data_dict['lidar_np'] = points
        return data_dict

    def forward(self, data_dict):
        """
        Args:
            data_dict:
                points: (N, 3 + C_in)
                gt_boxes: optional, (N, 7) [x, y, z, dx, dy, dz, heading]
                gt_names: optional, (N), string
                ...

        Returns:
        """
        if self.train:
            for cur_augmentor in self.data_augmentor_queue:
                data_dict = cur_augmentor(data_dict=data_dict)
        return data_dict

def __init__(self, augment_config, train=True):
    self.data_augmentor_queue = []
    self.train = train
    for cur_cfg in augment_config:
        cur_augmentor = getattr(self, cur_cfg['NAME'])(config=cur_cfg)
        self.data_augmentor_queue.append(cur_augmentor)

def random_world_flip(self, data_dict=None, config=None):
    if data_dict is None:
        return partial(self.random_world_flip, config=config)
    gt_boxes, gt_mask, points = (data_dict['object_bbx_center'], data_dict['object_bbx_mask'], data_dict['lidar_np'])
    gt_boxes_valid = gt_boxes[gt_mask == 1]
    for cur_axis in config['ALONG_AXIS_LIST']:
        assert cur_axis in ['x', 'y']
        gt_boxes_valid, points = getattr(augment_utils, 'random_flip_along_%s' % cur_axis)(gt_boxes_valid, points)
    gt_boxes[:gt_boxes_valid.shape[0], :] = gt_boxes_valid
    data_dict['object_bbx_center'] = gt_boxes
    data_dict['object_bbx_mask'] = gt_mask
    data_dict['lidar_np'] = points
    return data_dict

def random_world_rotation(self, data_dict=None, config=None):
    if data_dict is None:
        return partial(self.random_world_rotation, config=config)
    rot_range = config['WORLD_ROT_ANGLE']
    if not isinstance(rot_range, list):
        rot_range = [-rot_range, rot_range]
    gt_boxes, gt_mask, points = (data_dict['object_bbx_center'], data_dict['object_bbx_mask'], data_dict['lidar_np'])
    gt_boxes_valid = gt_boxes[gt_mask == 1]
    gt_boxes_valid, points = augment_utils.global_rotation(gt_boxes_valid, points, rot_range=rot_range)
    gt_boxes[:gt_boxes_valid.shape[0], :] = gt_boxes_valid
    data_dict['object_bbx_center'] = gt_boxes
    data_dict['object_bbx_mask'] = gt_mask
    data_dict['lidar_np'] = points
    return data_dict

def random_world_scaling(self, data_dict=None, config=None):
    if data_dict is None:
        return partial(self.random_world_scaling, config=config)
    gt_boxes, gt_mask, points = (data_dict['object_bbx_center'], data_dict['object_bbx_mask'], data_dict['lidar_np'])
    gt_boxes_valid = gt_boxes[gt_mask == 1]
    gt_boxes_valid, points = augment_utils.global_scaling(gt_boxes_valid, points, config['WORLD_SCALE_RANGE'])
    gt_boxes[:gt_boxes_valid.shape[0], :] = gt_boxes_valid
    data_dict['object_bbx_center'] = gt_boxes
    data_dict['object_bbx_mask'] = gt_mask
    data_dict['lidar_np'] = points
    return data_dict

def setup_optimizer(hypes, model):
    """
    Create optimizer corresponding to the yaml file

    Parameters
    ----------
    hypes : dict
        The training configurations.
    model : opencood model
        The pytorch model
    """
    method_dict = hypes['optimizer']
    optimizer_method = getattr(optim, method_dict['core_method'], None)
    if not optimizer_method:
        raise ValueError('{} is not supported'.format(method_dict['name']))
    if 'args' in method_dict:
        return optimizer_method(filter(lambda p: p.requires_grad, model.parameters()), lr=method_dict['lr'], **method_dict['args'])
    else:
        return optimizer_method(filter(lambda p: p.requires_grad, model.parameters()), lr=method_dict['lr'])

class PointPillarV2VNet(nn.Module):

    def __init__(self, args):
        super(PointPillarV2VNet, self).__init__()
        self.max_cav = args['max_cav']
        self.pillar_vfe = PillarVFE(args['pillar_vfe'], num_point_features=4, voxel_size=args['voxel_size'], point_cloud_range=args['lidar_range'])
        self.scatter = PointPillarScatter(args['point_pillar_scatter'])
        self.backbone = BaseBEVBackbone(args['base_bev_backbone'], 64)
        self.shrink_flag = False
        if 'shrink_header' in args:
            self.shrink_flag = True
            self.shrink_conv = DownsampleConv(args['shrink_header'])
        self.compression = False
        if args['compression'] > 0:
            self.compression = True
            self.naive_compressor = NaiveCompressor(256, args['compression'])
        self.fusion_net = V2VNetFusion(args['v2vfusion'])
        self.cls_head = nn.Conv2d(128 * 2, args['anchor_number'], kernel_size=1)
        self.reg_head = nn.Conv2d(128 * 2, 7 * args['anchor_number'], kernel_size=1)
        if args['backbone_fix']:
            self.backbone_fix()

    def backbone_fix(self):
        """
        Fix the parameters of backbone during finetune on timedelay。
        """
        for p in self.pillar_vfe.parameters():
            p.requires_grad = False
        for p in self.scatter.parameters():
            p.requires_grad = False
        for p in self.backbone.parameters():
            p.requires_grad = False
        if self.compression:
            for p in self.naive_compressor.parameters():
                p.requires_grad = False
        if self.shrink_flag:
            for p in self.shrink_conv.parameters():
                p.requires_grad = False
        for p in self.cls_head.parameters():
            p.requires_grad = False
        for p in self.reg_head.parameters():
            p.requires_grad = False

    def unpad_prior_encoding(self, x, record_len):
        B = x.shape[0]
        out = []
        for i in range(B):
            out.append(x[i, :record_len[i], :])
        out = torch.cat(out, dim=0)
        return out

    def forward(self, data_dict):
        voxel_features = data_dict['processed_lidar']['voxel_features']
        voxel_coords = data_dict['processed_lidar']['voxel_coords']
        voxel_num_points = data_dict['processed_lidar']['voxel_num_points']
        record_len = data_dict['record_len']
        spatial_correction_matrix = data_dict['spatial_correction_matrix']
        pairwise_t_matrix = data_dict['pairwise_t_matrix']
        prior_encoding = data_dict['prior_encoding']
        prior_encoding = self.unpad_prior_encoding(prior_encoding, record_len)
        batch_dict = {'voxel_features': voxel_features, 'voxel_coords': voxel_coords, 'voxel_num_points': voxel_num_points, 'record_len': record_len}
        batch_dict = self.pillar_vfe(batch_dict)
        batch_dict = self.scatter(batch_dict)
        batch_dict = self.backbone(batch_dict)
        spatial_features_2d = batch_dict['spatial_features_2d']
        if self.shrink_flag:
            spatial_features_2d = self.shrink_conv(spatial_features_2d)
        if self.compression:
            spatial_features_2d = self.naive_compressor(spatial_features_2d)
        fused_feature = self.fusion_net(spatial_features_2d, record_len, pairwise_t_matrix, prior_encoding)
        psm = self.cls_head(fused_feature)
        rm = self.reg_head(fused_feature)
        output_dict = {'psm': psm, 'rm': rm}
        return output_dict

def backbone_fix(self):
    """
        Fix the parameters of backbone during finetune on timedelay。
        """
    for p in self.pillar_vfe.parameters():
        p.requires_grad = False
    for p in self.scatter.parameters():
        p.requires_grad = False
    for p in self.backbone.parameters():
        p.requires_grad = False
    if self.compression:
        for p in self.naive_compressor.parameters():
            p.requires_grad = False
    if self.shrink_flag:
        for p in self.shrink_conv.parameters():
            p.requires_grad = False
    for p in self.cls_head.parameters():
        p.requires_grad = False
    for p in self.reg_head.parameters():
        p.requires_grad = False

class PointPillarFCooper(nn.Module):

    def __init__(self, args):
        super(PointPillarFCooper, self).__init__()
        self.max_cav = args['max_cav']
        self.pillar_vfe = PillarVFE(args['pillar_vfe'], num_point_features=4, voxel_size=args['voxel_size'], point_cloud_range=args['lidar_range'])
        self.scatter = PointPillarScatter(args['point_pillar_scatter'])
        self.backbone = BaseBEVBackbone(args['base_bev_backbone'], 64)
        self.shrink_flag = False
        if 'shrink_header' in args:
            self.shrink_flag = True
            self.shrink_conv = DownsampleConv(args['shrink_header'])
        self.compression = False
        if args['compression'] > 0:
            self.compression = True
            self.naive_compressor = NaiveCompressor(256, args['compression'])
        self.fusion_net = SpatialFusion()
        self.cls_head = nn.Conv2d(128 * 2, args['anchor_number'], kernel_size=1)
        self.reg_head = nn.Conv2d(128 * 2, 7 * args['anchor_number'], kernel_size=1)
        if args['backbone_fix']:
            self.backbone_fix()

    def backbone_fix(self):
        """
        Fix the parameters of backbone during finetune on timedelay。
        """
        for p in self.pillar_vfe.parameters():
            p.requires_grad = False
        for p in self.scatter.parameters():
            p.requires_grad = False
        for p in self.backbone.parameters():
            p.requires_grad = False
        if self.compression:
            for p in self.naive_compressor.parameters():
                p.requires_grad = False
        if self.shrink_flag:
            for p in self.shrink_conv.parameters():
                p.requires_grad = False
        for p in self.cls_head.parameters():
            p.requires_grad = False
        for p in self.reg_head.parameters():
            p.requires_grad = False

    def forward(self, data_dict):
        voxel_features = data_dict['processed_lidar']['voxel_features']
        voxel_coords = data_dict['processed_lidar']['voxel_coords']
        voxel_num_points = data_dict['processed_lidar']['voxel_num_points']
        record_len = data_dict['record_len']
        spatial_correction_matrix = data_dict['spatial_correction_matrix']
        batch_dict = {'voxel_features': voxel_features, 'voxel_coords': voxel_coords, 'voxel_num_points': voxel_num_points, 'record_len': record_len}
        batch_dict = self.pillar_vfe(batch_dict)
        batch_dict = self.scatter(batch_dict)
        batch_dict = self.backbone(batch_dict)
        spatial_features_2d = batch_dict['spatial_features_2d']
        if self.shrink_flag:
            spatial_features_2d = self.shrink_conv(spatial_features_2d)
        if self.compression:
            spatial_features_2d = self.naive_compressor(spatial_features_2d)
        fused_feature = self.fusion_net(spatial_features_2d, record_len)
        psm = self.cls_head(fused_feature)
        rm = self.reg_head(fused_feature)
        output_dict = {'psm': psm, 'rm': rm}
        return output_dict

def backbone_fix(self):
    """
        Fix the parameters of backbone during finetune on timedelay。
        """
    for p in self.pillar_vfe.parameters():
        p.requires_grad = False
    for p in self.scatter.parameters():
        p.requires_grad = False
    for p in self.backbone.parameters():
        p.requires_grad = False
    if self.compression:
        for p in self.naive_compressor.parameters():
            p.requires_grad = False
    if self.shrink_flag:
        for p in self.shrink_conv.parameters():
            p.requires_grad = False
    for p in self.cls_head.parameters():
        p.requires_grad = False
    for p in self.reg_head.parameters():
        p.requires_grad = False

class PointPillarOPV2V(nn.Module):

    def __init__(self, args):
        super(PointPillarOPV2V, self).__init__()
        self.max_cav = args['max_cav']
        self.pillar_vfe = PillarVFE(args['pillar_vfe'], num_point_features=4, voxel_size=args['voxel_size'], point_cloud_range=args['lidar_range'])
        self.scatter = PointPillarScatter(args['point_pillar_scatter'])
        self.backbone = BaseBEVBackbone(args['base_bev_backbone'], 64)
        self.shrink_flag = False
        if 'shrink_header' in args:
            self.shrink_flag = True
            self.shrink_conv = DownsampleConv(args['shrink_header'])
        self.compression = False
        if args['compression'] > 0:
            self.compression = True
            self.naive_compressor = NaiveCompressor(256, args['compression'])
        self.fusion_net = AttFusion(256)
        self.cls_head = nn.Conv2d(128 * 2, args['anchor_number'], kernel_size=1)
        self.reg_head = nn.Conv2d(128 * 2, 7 * args['anchor_number'], kernel_size=1)
        if args['backbone_fix']:
            self.backbone_fix()

    def backbone_fix(self):
        """
        Fix the parameters of backbone during finetune on timedelay。
        """
        for p in self.pillar_vfe.parameters():
            p.requires_grad = False
        for p in self.scatter.parameters():
            p.requires_grad = False
        for p in self.backbone.parameters():
            p.requires_grad = False
        if self.compression:
            for p in self.naive_compressor.parameters():
                p.requires_grad = False
        if self.shrink_flag:
            for p in self.shrink_conv.parameters():
                p.requires_grad = False
        for p in self.cls_head.parameters():
            p.requires_grad = False
        for p in self.reg_head.parameters():
            p.requires_grad = False

    def forward(self, data_dict):
        voxel_features = data_dict['processed_lidar']['voxel_features']
        voxel_coords = data_dict['processed_lidar']['voxel_coords']
        voxel_num_points = data_dict['processed_lidar']['voxel_num_points']
        record_len = data_dict['record_len']
        spatial_correction_matrix = data_dict['spatial_correction_matrix']
        prior_encoding = data_dict['prior_encoding'].unsqueeze(-1).unsqueeze(-1)
        batch_dict = {'voxel_features': voxel_features, 'voxel_coords': voxel_coords, 'voxel_num_points': voxel_num_points, 'record_len': record_len}
        batch_dict = self.pillar_vfe(batch_dict)
        batch_dict = self.scatter(batch_dict)
        batch_dict = self.backbone(batch_dict)
        spatial_features_2d = batch_dict['spatial_features_2d']
        if self.shrink_flag:
            spatial_features_2d = self.shrink_conv(spatial_features_2d)
        if self.compression:
            spatial_features_2d = self.naive_compressor(spatial_features_2d)
        fused_feature = self.fusion_net(spatial_features_2d, record_len)
        psm = self.cls_head(fused_feature)
        rm = self.reg_head(fused_feature)
        output_dict = {'psm': psm, 'rm': rm}
        return output_dict

def backbone_fix(self):
    """
        Fix the parameters of backbone during finetune on timedelay。
        """
    for p in self.pillar_vfe.parameters():
        p.requires_grad = False
    for p in self.scatter.parameters():
        p.requires_grad = False
    for p in self.backbone.parameters():
        p.requires_grad = False
    if self.compression:
        for p in self.naive_compressor.parameters():
            p.requires_grad = False
    if self.shrink_flag:
        for p in self.shrink_conv.parameters():
            p.requires_grad = False
    for p in self.cls_head.parameters():
        p.requires_grad = False
    for p in self.reg_head.parameters():
        p.requires_grad = False

class PointPillarTransformer(nn.Module):

    def __init__(self, args):
        super(PointPillarTransformer, self).__init__()
        self.max_cav = args['max_cav']
        self.pillar_vfe = PillarVFE(args['pillar_vfe'], num_point_features=4, voxel_size=args['voxel_size'], point_cloud_range=args['lidar_range'])
        self.scatter = PointPillarScatter(args['point_pillar_scatter'])
        self.backbone = BaseBEVBackbone(args['base_bev_backbone'], 64)
        self.shrink_flag = False
        if 'shrink_header' in args:
            self.shrink_flag = True
            self.shrink_conv = DownsampleConv(args['shrink_header'])
        self.compression = False
        if args['compression'] > 0:
            self.compression = True
            self.naive_compressor = NaiveCompressor(256, args['compression'])
        self.fusion_net = V2XTransformer(args['transformer'])
        self.cls_head = nn.Conv2d(128 * 2, args['anchor_number'], kernel_size=1)
        self.reg_head = nn.Conv2d(128 * 2, 7 * args['anchor_number'], kernel_size=1)
        if args['backbone_fix']:
            self.backbone_fix()

    def backbone_fix(self):
        """
        Fix the parameters of backbone during finetune on timedelay。
        """
        for p in self.pillar_vfe.parameters():
            p.requires_grad = False
        for p in self.scatter.parameters():
            p.requires_grad = False
        for p in self.backbone.parameters():
            p.requires_grad = False
        if self.compression:
            for p in self.naive_compressor.parameters():
                p.requires_grad = False
        if self.shrink_flag:
            for p in self.shrink_conv.parameters():
                p.requires_grad = False
        for p in self.cls_head.parameters():
            p.requires_grad = False
        for p in self.reg_head.parameters():
            p.requires_grad = False

    def forward(self, data_dict):
        voxel_features = data_dict['processed_lidar']['voxel_features']
        voxel_coords = data_dict['processed_lidar']['voxel_coords']
        voxel_num_points = data_dict['processed_lidar']['voxel_num_points']
        record_len = data_dict['record_len']
        spatial_correction_matrix = data_dict['spatial_correction_matrix']
        prior_encoding = data_dict['prior_encoding'].unsqueeze(-1).unsqueeze(-1)
        batch_dict = {'voxel_features': voxel_features, 'voxel_coords': voxel_coords, 'voxel_num_points': voxel_num_points, 'record_len': record_len}
        batch_dict = self.pillar_vfe(batch_dict)
        batch_dict = self.scatter(batch_dict)
        batch_dict = self.backbone(batch_dict)
        spatial_features_2d = batch_dict['spatial_features_2d']
        if self.shrink_flag:
            spatial_features_2d = self.shrink_conv(spatial_features_2d)
        if self.compression:
            spatial_features_2d = self.naive_compressor(spatial_features_2d)
        regroup_feature, mask = regroup(spatial_features_2d, record_len, self.max_cav)
        prior_encoding = prior_encoding.repeat(1, 1, 1, regroup_feature.shape[3], regroup_feature.shape[4])
        regroup_feature = torch.cat([regroup_feature, prior_encoding], dim=2)
        regroup_feature = regroup_feature.permute(0, 1, 3, 4, 2)
        fused_feature = self.fusion_net(regroup_feature, mask, spatial_correction_matrix)
        fused_feature = fused_feature.permute(0, 3, 1, 2)
        psm = self.cls_head(fused_feature)
        rm = self.reg_head(fused_feature)
        output_dict = {'psm': psm, 'rm': rm}
        return output_dict

def backbone_fix(self):
    """
        Fix the parameters of backbone during finetune on timedelay。
        """
    for p in self.pillar_vfe.parameters():
        p.requires_grad = False
    for p in self.scatter.parameters():
        p.requires_grad = False
    for p in self.backbone.parameters():
        p.requires_grad = False
    if self.compression:
        for p in self.naive_compressor.parameters():
            p.requires_grad = False
    if self.shrink_flag:
        for p in self.shrink_conv.parameters():
            p.requires_grad = False
    for p in self.cls_head.parameters():
        p.requires_grad = False
    for p in self.reg_head.parameters():
        p.requires_grad = False

