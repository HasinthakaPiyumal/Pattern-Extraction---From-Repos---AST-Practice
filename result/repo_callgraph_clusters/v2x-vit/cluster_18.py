# Cluster 18

def color_encoding(intensity, mode='intensity'):
    """
    Encode the single-channel intensity to 3 channels rgb color.

    Parameters
    ----------
    intensity : np.ndarray
        Lidar intensity, shape (n,)

    mode : str
        The color rendering mode. intensity, z-value and constant are
        supported.

    Returns
    -------
    color : np.ndarray
        Encoded Lidar color, shape (n, 3)
    """
    assert mode in ['intensity', 'z-value', 'constant']
    if mode == 'intensity':
        intensity_col = 1.0 - np.log(intensity) / np.log(np.exp(-0.004 * 100))
        int_color = np.c_[np.interp(intensity_col, VID_RANGE, VIRIDIS[:, 0]), np.interp(intensity_col, VID_RANGE, VIRIDIS[:, 1]), np.interp(intensity_col, VID_RANGE, VIRIDIS[:, 2])]
    elif mode == 'z-value':
        min_value = -1.5
        max_value = 0.5
        norm = matplotlib.colors.Normalize(vmin=min_value, vmax=max_value)
        cmap = cm.jet
        m = cm.ScalarMappable(norm=norm, cmap=cmap)
        colors = m.to_rgba(intensity)
        colors[:, [2, 1, 0, 3]] = colors[:, [0, 1, 2, 3]]
        colors[:, 3] = 0.5
        int_color = colors[:, :3]
    elif mode == 'constant':
        int_color = np.ones((intensity.shape[0], 3))
        int_color[:, 0] *= 247 / 255
        int_color[:, 1] *= 244 / 255
        int_color[:, 2] *= 237 / 255
    return int_color

class BevPostprocessor(BasePostprocessor):

    def __init__(self, anchor_params, train):
        super(BevPostprocessor, self).__init__(anchor_params, train)
        self.geometry_param = anchor_params['geometry_param']
        self.target_mean = np.array([0.008, 0.001, 0.202, 0.2, 0.43, 1.368])
        self.target_std_dev = np.array([0.866, 0.5, 0.954, 0.668, 0.09, 0.111])

    def generate_anchor_box(self):
        return None

    def generate_label(self, **kwargs):
        """
        Generate targets for training.

        Parameters
        ----------
        kwargs : list
            gt_box_center:(max_num, 7)

        Returns
        -------
        label_dict : dict
            Dictionary that contains all target related info.
        """
        assert self.params['order'] == 'lwh', 'Currently BEV only support lwh bbx order.'
        gt_box_center = kwargs['gt_box_center']
        masks = kwargs['mask']
        gt_box_center_valid = gt_box_center[masks == 1]
        bev_corners = box_utils.boxes_to_corners2d(gt_box_center_valid, self.params['order'])
        n = gt_box_center_valid.shape[0]
        bev_corners = bev_corners[:, :, :2]
        yaw = gt_box_center_valid[:, -1]
        x, y = (gt_box_center_valid[:, 0], gt_box_center_valid[:, 1])
        dx, dy = (gt_box_center_valid[:, 3], gt_box_center_valid[:, 4])
        reg_targets = np.column_stack([np.cos(yaw), np.sin(yaw), x, y, dx, dy])
        label_map = np.zeros(self.geometry_param['label_shape'])
        self.update_label_map(label_map, bev_corners, reg_targets)
        label_map = self.normalize_targets(label_map)
        label_dict = {'label_map': np.transpose(label_map, (2, 0, 1)).astype(np.float32), 'bev_corners': bev_corners}
        return label_dict

    def update_label_map(self, label_map, bev_corners, reg_targets):
        """
        Update label_map based on bbx and regression targets.

        Parameters
        ----------
        label_map : numpy.array
            Targets array for classification and regression tasks with
            the shape of label_shape.

        bev_corners : numpy.array
            The bbx corners in lidar frame with shape (n, 4, 2)

        reg_targets : numpy.array
            Array containing the regression targets information. It need to be
            further processed.

        """
        res = self.geometry_param['res']
        downsample_rate = self.geometry_param['downsample_rate']
        bev_origin = np.array([self.geometry_param['L1'], self.geometry_param['W1']]).reshape(1, -1)
        bev_corners_dist = (bev_corners - bev_origin) / res / downsample_rate
        x = np.arange(self.geometry_param['label_shape'][0])
        y = np.arange(self.geometry_param['label_shape'][1])
        xx, yy = np.meshgrid(x, y)
        points = np.concatenate([xx.reshape(-1, 1), yy.reshape(-1, 1)], axis=-1)
        bev_origin_dist = bev_origin / res / downsample_rate
        for i in range(bev_corners.shape[0]):
            reg_target = reg_targets[i, :]
            points_in_box = box_utils.get_points_in_rotated_box(points, bev_corners_dist[i, ...])
            points_continuous = dist_to_continuous(points_in_box, bev_origin_dist, res, downsample_rate)
            actual_reg_target = np.repeat(reg_target.reshape(1, -1), points_continuous.shape[0], axis=0)
            actual_reg_target[:, 2:4] = actual_reg_target[:, 2:4] - points_continuous
            actual_reg_target[:, 4:] = np.log(actual_reg_target[:, 4:])
            label_map[points_in_box[:, 0], points_in_box[:, 1], 0] = 1.0
            label_map[points_in_box[:, 0], points_in_box[:, 1], 1:] = actual_reg_target

    def normalize_targets(self, label_map):
        """
        Normalize label_map

        Parameters
        ----------
        label_map : numpy.array
            Targets array for classification and regression tasks with the
            shape of label_shape.

        Returns
        -------
        label_map: numpy.array
            Nromalized label_map.

        """
        label_map[..., 1:] = (label_map[..., 1:] - self.target_mean) / self.target_std_dev
        return label_map

    def denormalize_reg_map(self, reg_map):
        """
        Denormalize the regression map

        Parameters
        ----------
        reg_map : np.ndarray / torch.Tensor
            Regression output mapwith the shape of (label_shape[0],
            label_shape[1], 6).

        Returns
        -------
        reg_map : np.ndarray / torch.Tensor
            Denormalized regression map.

        """
        if isinstance(reg_map, np.ndarray):
            target_mean = self.target_mean
            target_std_dev = self.target_std_dev
        else:
            target_mean = torch.from_numpy(self.target_mean).to(reg_map.device)
            target_std_dev = torch.from_numpy(self.target_std_dev).to(reg_map.device)
        reg_map = reg_map * target_std_dev + target_mean
        return reg_map

    @staticmethod
    def collate_batch(label_batch_list):
        """
        Customized collate function for target label generation.

        Parameters
        ----------
        label_batch_list : list
            The list of dictionary  that contains all labels for several
            frames.

        Returns
        -------
        processed_batch : dict
            Reformatted labels in torch tensor.
        """
        label_map_list = [x['label_map'][np.newaxis, ...] for x in label_batch_list]
        processed_batch = {'label_map': torch.from_numpy(np.concatenate(label_map_list, axis=0)), 'bev_corners': [torch.from_numpy(x['bev_corners']) for x in label_batch_list]}
        return processed_batch

    def post_process(self, data_dict, output_dict):
        """
        Process the outputs of the model to 2D bounding box.
        Step1: convert each cav's output to bounding box format
        Step2: project the bounding boxes to ego space.
        Step:3 NMS

        Parameters
        ----------
        data_dict : dict
            The dictionary containing the origin input data of model.

        output_dict :dict
            The dictionary containing the output of the model.

        Returns
        -------
        pred_box2d_tensor : torch.Tensor
            The prediction bounding box tensor after NMS.

        gt_box2d_tensor : torch.Tensor
            The groundtruth bounding box tensor.
        """
        pred_box2d_list = []
        pred_score_list = []
        for cav_id, cav_content in data_dict.items():
            assert cav_id in output_dict
            transformation_matrix = cav_content['transformation_matrix']
            prob = output_dict[cav_id]['cls'].squeeze(0).squeeze(0)
            prob = torch.sigmoid(prob)
            reg_map = output_dict[cav_id]['reg'].squeeze(0).permute(1, 2, 0)
            reg_map = self.denormalize_reg_map(reg_map)
            threshold = self.params['target_args']['score_threshold']
            mask = torch.gt(prob, threshold)
            if mask.sum() > 0:
                corners2d = self.reg_map_to_bbx_corners(reg_map, mask)
                box3d = F.pad(corners2d, (0, 1))
                projected_boxes2d = box_utils.project_points_by_matrix_torch(box3d.view(-1, 3), transformation_matrix)[:, :2]
                projected_boxes2d = projected_boxes2d.view(-1, 4, 2)
                scores = prob[mask]
                pred_box2d_list.append(projected_boxes2d)
                pred_score_list.append(scores)
        if len(pred_box2d_list):
            pred_box2ds = torch.cat(pred_box2d_list, dim=0)
            pred_scores = torch.cat(pred_score_list, dim=0)
        else:
            return (None, None)
        keep_index = box_utils.nms_rotated(pred_box2ds, pred_scores, self.params['nms_thresh'])
        if len(keep_index):
            pred_box2ds = pred_box2ds[keep_index]
            pred_scores = pred_scores[keep_index]
        mask = box_utils.get_mask_for_boxes_within_range_torch(pred_box2ds)
        pred_box2ds = pred_box2ds[mask, :, :]
        pred_scores = pred_scores[mask]
        assert pred_scores.shape[0] == pred_box2ds.shape[0]
        return (pred_box2ds, pred_scores)

    def reg_map_to_bbx_corners(self, reg_map, mask):
        """
        Construct bbx from the regression output of the model.

        Parameters
        ----------
        reg_map : torch.Tensor
            Regression output of neural networks.

        mask : torch.Tensor
            Masks used to filter bbx.

        Returns
        -------
        corners : torch.Tensor
            Bbx output with shape (N, 4, 2).

        """
        assert len(reg_map.shape) == 3, 'only support shape of label_shape i.e. (*, *, 6)'
        device = reg_map.device
        cos_t, sin_t, x, y, log_dx, log_dy = [tt.squeeze(-1) for tt in torch.chunk(reg_map, 6, dim=-1)]
        yaw = torch.atan2(sin_t, cos_t)
        dx, dy = (log_dx.exp(), log_dy.exp())
        grid_size = self.geometry_param['res'] * self.geometry_param['downsample_rate']
        grid_x = torch.arange(self.geometry_param['L1'], self.geometry_param['L2'], grid_size, dtype=torch.float32, device=device)
        grid_y = torch.arange(self.geometry_param['W1'], self.geometry_param['W2'], grid_size, dtype=torch.float32, device=device)
        xx, yy = torch.meshgrid([grid_x, grid_y])
        center_x = xx + x
        center_y = yy + y
        bbx2d = torch.stack([center_x, center_y, dx, dy, yaw], dim=-1)
        bbx2d = bbx2d[mask, :]
        corners = box_utils.boxes2d_to_corners2d(bbx2d)
        return corners

    def post_process_debug(self, data_dict, output_dict):
        """
        Process the outputs of the model to 2D bounding box for debug purpose.
        Step1: convert each cav's output to bounding box format
        Step2: project the bounding boxes to ego space.
        Step:3 NMS

        Parameters
        ----------
        data_dict : dict
            The dictionary containing the origin input data of model.

        output_dict :dict
            The dictionary containing the output of the model.

        Returns
        -------
        pred_box2d_tensor : torch.Tensor
            The prediction bounding box tensor after NMS.
        gt_box2d_tensor : torch.Tensor
            The groundtruth bounding box tensor.
        """
        pred_box2d_list = []
        pred_score_list = []
        transformation_matrix = data_dict['transformation_matrix']
        prob = output_dict['cls'].squeeze(0).squeeze(0)
        prob = torch.sigmoid(prob)
        reg_map = output_dict['reg'].squeeze(0).permute(1, 2, 0)
        reg_map = self.denormalize_reg_map(reg_map)
        threshold = 0.5
        mask = torch.gt(prob, threshold)
        if mask.sum() > 0:
            corners2d = self.reg_map_to_bbx_corners(reg_map, mask)
            box3d = F.pad(corners2d, (0, 1))
            projected_boxes2d = box_utils.project_points_by_matrix_torch(box3d.view(-1, 3), transformation_matrix)[:, :2]
            projected_boxes2d = projected_boxes2d.view(-1, 4, 2)
            scores = prob[mask]
            pred_box2d_list.append(projected_boxes2d)
            pred_score_list.append(scores)
        pred_box2ds = torch.cat(pred_box2d_list, dim=0)
        pred_scores = torch.cat(pred_score_list, dim=0)
        keep_index = box_utils.nms_rotated(pred_box2ds, pred_scores, self.params['nms_thresh'])
        pred_box2ds = pred_box2ds[keep_index]
        mask = box_utils.get_mask_for_boxes_within_range_torch(pred_box2ds)
        pred_box2ds = pred_box2ds[mask, :, :]
        return pred_box2ds

    @staticmethod
    def visualize(pred_box_tensor, gt_tensor, pcd, show_vis, save_path, dataset=None):
        """
        Visualize the BEV 2D prediction, ground truth with point cloud together.

        Parameters
        ----------
        pred_box_tensor : torch.Tensor
            (N, 8, 3) prediction.

        gt_tensor : torch.Tensor
            (N, 8, 3) groundtruth bbx

        pcd : torch.Tensor
            PointCloud, (N, 4).

        show_vis : bool
            Whether to show visualization.

        save_path : str
            Save the visualization results to given path.

        dataset : BaseDataset
            opencood dataset object.
        """
        assert dataset is not None, "dataset argument can't be None"
        vis_utils.visualize_single_sample_output_bev(pred_box_tensor, gt_tensor, pcd, dataset, show_vis, save_path)

def update_label_map(self, label_map, bev_corners, reg_targets):
    """
        Update label_map based on bbx and regression targets.

        Parameters
        ----------
        label_map : numpy.array
            Targets array for classification and regression tasks with
            the shape of label_shape.

        bev_corners : numpy.array
            The bbx corners in lidar frame with shape (n, 4, 2)

        reg_targets : numpy.array
            Array containing the regression targets information. It need to be
            further processed.

        """
    res = self.geometry_param['res']
    downsample_rate = self.geometry_param['downsample_rate']
    bev_origin = np.array([self.geometry_param['L1'], self.geometry_param['W1']]).reshape(1, -1)
    bev_corners_dist = (bev_corners - bev_origin) / res / downsample_rate
    x = np.arange(self.geometry_param['label_shape'][0])
    y = np.arange(self.geometry_param['label_shape'][1])
    xx, yy = np.meshgrid(x, y)
    points = np.concatenate([xx.reshape(-1, 1), yy.reshape(-1, 1)], axis=-1)
    bev_origin_dist = bev_origin / res / downsample_rate
    for i in range(bev_corners.shape[0]):
        reg_target = reg_targets[i, :]
        points_in_box = box_utils.get_points_in_rotated_box(points, bev_corners_dist[i, ...])
        points_continuous = dist_to_continuous(points_in_box, bev_origin_dist, res, downsample_rate)
        actual_reg_target = np.repeat(reg_target.reshape(1, -1), points_continuous.shape[0], axis=0)
        actual_reg_target[:, 2:4] = actual_reg_target[:, 2:4] - points_continuous
        actual_reg_target[:, 4:] = np.log(actual_reg_target[:, 4:])
        label_map[points_in_box[:, 0], points_in_box[:, 1], 0] = 1.0
        label_map[points_in_box[:, 0], points_in_box[:, 1], 1:] = actual_reg_target

def reg_map_to_bbx_corners(self, reg_map, mask):
    """
        Construct bbx from the regression output of the model.

        Parameters
        ----------
        reg_map : torch.Tensor
            Regression output of neural networks.

        mask : torch.Tensor
            Masks used to filter bbx.

        Returns
        -------
        corners : torch.Tensor
            Bbx output with shape (N, 4, 2).

        """
    assert len(reg_map.shape) == 3, 'only support shape of label_shape i.e. (*, *, 6)'
    device = reg_map.device
    cos_t, sin_t, x, y, log_dx, log_dy = [tt.squeeze(-1) for tt in torch.chunk(reg_map, 6, dim=-1)]
    yaw = torch.atan2(sin_t, cos_t)
    dx, dy = (log_dx.exp(), log_dy.exp())
    grid_size = self.geometry_param['res'] * self.geometry_param['downsample_rate']
    grid_x = torch.arange(self.geometry_param['L1'], self.geometry_param['L2'], grid_size, dtype=torch.float32, device=device)
    grid_y = torch.arange(self.geometry_param['W1'], self.geometry_param['W2'], grid_size, dtype=torch.float32, device=device)
    xx, yy = torch.meshgrid([grid_x, grid_y])
    center_x = xx + x
    center_y = yy + y
    bbx2d = torch.stack([center_x, center_y, dx, dy, yaw], dim=-1)
    bbx2d = bbx2d[mask, :]
    corners = box_utils.boxes2d_to_corners2d(bbx2d)
    return corners

class VoxelPostprocessor(BasePostprocessor):

    def __init__(self, anchor_params, train):
        super(VoxelPostprocessor, self).__init__(anchor_params, train)
        self.anchor_num = self.params['anchor_args']['num']

    def generate_anchor_box(self):
        W = self.params['anchor_args']['W']
        H = self.params['anchor_args']['H']
        l = self.params['anchor_args']['l']
        w = self.params['anchor_args']['w']
        h = self.params['anchor_args']['h']
        r = self.params['anchor_args']['r']
        assert self.anchor_num == len(r)
        r = [math.radians(ele) for ele in r]
        vh = self.params['anchor_args']['vh']
        vw = self.params['anchor_args']['vw']
        xrange = [self.params['anchor_args']['cav_lidar_range'][0], self.params['anchor_args']['cav_lidar_range'][3]]
        yrange = [self.params['anchor_args']['cav_lidar_range'][1], self.params['anchor_args']['cav_lidar_range'][4]]
        if 'feature_stride' in self.params['anchor_args']:
            feature_stride = self.params['anchor_args']['feature_stride']
        else:
            feature_stride = 2
        x = np.linspace(xrange[0] + vw, xrange[1] - vw, W // feature_stride)
        y = np.linspace(yrange[0] + vh, yrange[1] - vh, H // feature_stride)
        cx, cy = np.meshgrid(x, y)
        cx = np.tile(cx[..., np.newaxis], self.anchor_num)
        cy = np.tile(cy[..., np.newaxis], self.anchor_num)
        cz = np.ones_like(cx) * -1.0
        w = np.ones_like(cx) * w
        l = np.ones_like(cx) * l
        h = np.ones_like(cx) * h
        r_ = np.ones_like(cx)
        for i in range(self.anchor_num):
            r_[..., i] = r[i]
        if self.params['order'] == 'hwl':
            anchors = np.stack([cx, cy, cz, h, w, l, r_], axis=-1)
        elif self.params['order'] == 'lhw':
            anchors = np.stack([cx, cy, cz, l, h, w, r_], axis=-1)
        else:
            sys.exit('Unknown bbx order.')
        return anchors

    def generate_label(self, **kwargs):
        """
        Generate targets for training.

        Parameters
        ----------
        argv : list
            gt_box_center:(max_num, 7), anchor:(H, W, anchor_num, 7)

        Returns
        -------
        label_dict : dict
            Dictionary that contains all target related info.
        """
        assert self.params['order'] == 'hwl', 'Currently Voxel only supporthwl bbx order.'
        gt_box_center = kwargs['gt_box_center']
        anchors = kwargs['anchors']
        masks = kwargs['mask']
        feature_map_shape = anchors.shape[:2]
        anchors = anchors.reshape(-1, 7)
        anchors_d = np.sqrt(anchors[:, 4] ** 2 + anchors[:, 5] ** 2)
        pos_equal_one = np.zeros((*feature_map_shape, self.anchor_num))
        neg_equal_one = np.zeros((*feature_map_shape, self.anchor_num))
        targets = np.zeros((*feature_map_shape, self.anchor_num * 7))
        gt_box_center_valid = gt_box_center[masks == 1]
        gt_box_corner_valid = box_utils.boxes_to_corners_3d(gt_box_center_valid, self.params['order'])
        anchors_corner = box_utils.boxes_to_corners_3d(anchors, order=self.params['order'])
        anchors_standup_2d = box_utils.corner2d_to_standup_box(anchors_corner)
        gt_standup_2d = box_utils.corner2d_to_standup_box(gt_box_corner_valid)
        iou = bbox_overlaps(np.ascontiguousarray(anchors_standup_2d).astype(np.float32), np.ascontiguousarray(gt_standup_2d).astype(np.float32))
        id_highest = np.argmax(iou.T, axis=1)
        id_highest_gt = np.arange(iou.T.shape[0])
        mask = iou.T[id_highest_gt, id_highest] > 0
        id_highest, id_highest_gt = (id_highest[mask], id_highest_gt[mask])
        id_pos, id_pos_gt = np.where(iou > self.params['target_args']['pos_threshold'])
        id_neg = np.where(np.sum(iou < self.params['target_args']['neg_threshold'], axis=1) == iou.shape[1])[0]
        id_pos = np.concatenate([id_pos, id_highest])
        id_pos_gt = np.concatenate([id_pos_gt, id_highest_gt])
        id_pos, index = np.unique(id_pos, return_index=True)
        id_pos_gt = id_pos_gt[index]
        id_neg.sort()
        index_x, index_y, index_z = np.unravel_index(id_pos, (*feature_map_shape, self.anchor_num))
        pos_equal_one[index_x, index_y, index_z] = 1
        targets[index_x, index_y, np.array(index_z) * 7] = (gt_box_center[id_pos_gt, 0] - anchors[id_pos, 0]) / anchors_d[id_pos]
        targets[index_x, index_y, np.array(index_z) * 7 + 1] = (gt_box_center[id_pos_gt, 1] - anchors[id_pos, 1]) / anchors_d[id_pos]
        targets[index_x, index_y, np.array(index_z) * 7 + 2] = (gt_box_center[id_pos_gt, 2] - anchors[id_pos, 2]) / anchors[id_pos, 3]
        targets[index_x, index_y, np.array(index_z) * 7 + 3] = np.log(gt_box_center[id_pos_gt, 3] / anchors[id_pos, 3])
        targets[index_x, index_y, np.array(index_z) * 7 + 4] = np.log(gt_box_center[id_pos_gt, 4] / anchors[id_pos, 4])
        targets[index_x, index_y, np.array(index_z) * 7 + 5] = np.log(gt_box_center[id_pos_gt, 5] / anchors[id_pos, 5])
        targets[index_x, index_y, np.array(index_z) * 7 + 6] = gt_box_center[id_pos_gt, 6] - anchors[id_pos, 6]
        index_x, index_y, index_z = np.unravel_index(id_neg, (*feature_map_shape, self.anchor_num))
        neg_equal_one[index_x, index_y, index_z] = 1
        index_x, index_y, index_z = np.unravel_index(id_highest, (*feature_map_shape, self.anchor_num))
        neg_equal_one[index_x, index_y, index_z] = 0
        label_dict = {'pos_equal_one': pos_equal_one, 'neg_equal_one': neg_equal_one, 'targets': targets}
        return label_dict

    @staticmethod
    def collate_batch(label_batch_list):
        """
        Customized collate function for target label generation.

        Parameters
        ----------
        label_batch_list : list
            The list of dictionary  that contains all labels for several
            frames.

        Returns
        -------
        target_batch : dict
            Reformatted labels in torch tensor.
        """
        pos_equal_one = []
        neg_equal_one = []
        targets = []
        for i in range(len(label_batch_list)):
            pos_equal_one.append(label_batch_list[i]['pos_equal_one'])
            neg_equal_one.append(label_batch_list[i]['neg_equal_one'])
            targets.append(label_batch_list[i]['targets'])
        pos_equal_one = torch.from_numpy(np.array(pos_equal_one))
        neg_equal_one = torch.from_numpy(np.array(neg_equal_one))
        targets = torch.from_numpy(np.array(targets))
        return {'targets': targets, 'pos_equal_one': pos_equal_one, 'neg_equal_one': neg_equal_one}

    def post_process(self, data_dict, output_dict):
        """
        Process the outputs of the model to 2D/3D bounding box.
        Step1: convert each cav's output to bounding box format
        Step2: project the bounding boxes to ego space.
        Step:3 NMS

        Parameters
        ----------
        data_dict : dict
            The dictionary containing the origin input data of model.

        output_dict :dict
            The dictionary containing the output of the model.

        Returns
        -------
        pred_box3d_tensor : torch.Tensor
            The prediction bounding box tensor after NMS.
        gt_box3d_tensor : torch.Tensor
            The groundtruth bounding box tensor.
        """
        pred_box3d_list = []
        pred_box2d_list = []
        for cav_id, cav_content in data_dict.items():
            assert cav_id in output_dict
            transformation_matrix = cav_content['transformation_matrix']
            anchor_box = cav_content['anchor_box']
            prob = output_dict[cav_id]['psm']
            prob = F.sigmoid(prob.permute(0, 2, 3, 1))
            prob = prob.reshape(1, -1)
            reg = output_dict[cav_id]['rm']
            batch_box3d = self.delta_to_boxes3d(reg, anchor_box)
            mask = torch.gt(prob, self.params['target_args']['score_threshold'])
            mask = mask.view(1, -1)
            mask_reg = mask.unsqueeze(2).repeat(1, 1, 7)
            assert batch_box3d.shape[0] == 1
            boxes3d = torch.masked_select(batch_box3d[0], mask_reg[0]).view(-1, 7)
            scores = torch.masked_select(prob[0], mask[0])
            if len(boxes3d) != 0:
                boxes3d_corner = box_utils.boxes_to_corners_3d(boxes3d, order=self.params['order'])
                projected_boxes3d = box_utils.project_box3d(boxes3d_corner, transformation_matrix)
                projected_boxes2d = box_utils.corner_to_standup_box_torch(projected_boxes3d)
                boxes2d_score = torch.cat((projected_boxes2d, scores.unsqueeze(1)), dim=1)
                pred_box2d_list.append(boxes2d_score)
                pred_box3d_list.append(projected_boxes3d)
        if len(pred_box2d_list) == 0 or len(pred_box3d_list) == 0:
            return (None, None)
        pred_box2d_list = torch.vstack(pred_box2d_list)
        scores = pred_box2d_list[:, -1]
        pred_box3d_tensor = torch.vstack(pred_box3d_list)
        keep_index_1 = box_utils.remove_large_pred_bbx(pred_box3d_tensor)
        keep_index_2 = box_utils.remove_bbx_abnormal_z(pred_box3d_tensor)
        keep_index = torch.logical_and(keep_index_1, keep_index_2)
        pred_box3d_tensor = pred_box3d_tensor[keep_index]
        scores = scores[keep_index]
        keep_index = box_utils.nms_rotated(pred_box3d_tensor, scores, self.params['nms_thresh'])
        pred_box3d_tensor = pred_box3d_tensor[keep_index]
        scores = scores[keep_index]
        mask = box_utils.get_mask_for_boxes_within_range_torch(pred_box3d_tensor)
        pred_box3d_tensor = pred_box3d_tensor[mask, :, :]
        scores = scores[mask]
        assert scores.shape[0] == pred_box3d_tensor.shape[0]
        return (pred_box3d_tensor, scores)

    @staticmethod
    def delta_to_boxes3d(deltas, anchors):
        """
        Convert the output delta to 3d bbx.

        Parameters
        ----------
        deltas : torch.Tensor
            (N, W, L, 14)
        anchors : torch.Tensor
            (W, L, 2, 7) -> xyzhwlr

        Returns
        -------
        box3d : torch.Tensor
            (N, W*L*2, 7)
        """
        N = deltas.shape[0]
        deltas = deltas.permute(0, 2, 3, 1).contiguous().view(N, -1, 7)
        boxes3d = torch.zeros_like(deltas)
        if deltas.is_cuda:
            anchors = anchors.cuda()
            boxes3d = boxes3d.cuda()
        anchors_reshaped = anchors.view(-1, 7).float()
        anchors_d = torch.sqrt(anchors_reshaped[:, 4] ** 2 + anchors_reshaped[:, 5] ** 2)
        anchors_d = anchors_d.repeat(N, 2, 1).transpose(1, 2)
        anchors_reshaped = anchors_reshaped.repeat(N, 1, 1)
        boxes3d[..., [0, 1]] = torch.mul(deltas[..., [0, 1]], anchors_d) + anchors_reshaped[..., [0, 1]]
        boxes3d[..., [2]] = torch.mul(deltas[..., [2]], anchors_reshaped[..., [3]]) + anchors_reshaped[..., [2]]
        boxes3d[..., [3, 4, 5]] = torch.exp(deltas[..., [3, 4, 5]]) * anchors_reshaped[..., [3, 4, 5]]
        boxes3d[..., 6] = deltas[..., 6] + anchors_reshaped[..., 6]
        return boxes3d

    @staticmethod
    def visualize(pred_box_tensor, gt_tensor, pcd, show_vis, save_path, dataset=None):
        """
        Visualize the prediction, ground truth with point cloud together.

        Parameters
        ----------
        pred_box_tensor : torch.Tensor
            (N, 8, 3) prediction.

        gt_tensor : torch.Tensor
            (N, 8, 3) groundtruth bbx

        pcd : torch.Tensor
            PointCloud, (N, 4).

        show_vis : bool
            Whether to show visualization.

        save_path : str
            Save the visualization results to given path.

        dataset : BaseDataset
            opencood dataset object.

        """
        vis_utils.visualize_single_sample_output_gt(pred_box_tensor, gt_tensor, pcd, show_vis, save_path)

def generate_label(self, **kwargs):
    """
        Generate targets for training.

        Parameters
        ----------
        argv : list
            gt_box_center:(max_num, 7), anchor:(H, W, anchor_num, 7)

        Returns
        -------
        label_dict : dict
            Dictionary that contains all target related info.
        """
    assert self.params['order'] == 'hwl', 'Currently Voxel only supporthwl bbx order.'
    gt_box_center = kwargs['gt_box_center']
    anchors = kwargs['anchors']
    masks = kwargs['mask']
    feature_map_shape = anchors.shape[:2]
    anchors = anchors.reshape(-1, 7)
    anchors_d = np.sqrt(anchors[:, 4] ** 2 + anchors[:, 5] ** 2)
    pos_equal_one = np.zeros((*feature_map_shape, self.anchor_num))
    neg_equal_one = np.zeros((*feature_map_shape, self.anchor_num))
    targets = np.zeros((*feature_map_shape, self.anchor_num * 7))
    gt_box_center_valid = gt_box_center[masks == 1]
    gt_box_corner_valid = box_utils.boxes_to_corners_3d(gt_box_center_valid, self.params['order'])
    anchors_corner = box_utils.boxes_to_corners_3d(anchors, order=self.params['order'])
    anchors_standup_2d = box_utils.corner2d_to_standup_box(anchors_corner)
    gt_standup_2d = box_utils.corner2d_to_standup_box(gt_box_corner_valid)
    iou = bbox_overlaps(np.ascontiguousarray(anchors_standup_2d).astype(np.float32), np.ascontiguousarray(gt_standup_2d).astype(np.float32))
    id_highest = np.argmax(iou.T, axis=1)
    id_highest_gt = np.arange(iou.T.shape[0])
    mask = iou.T[id_highest_gt, id_highest] > 0
    id_highest, id_highest_gt = (id_highest[mask], id_highest_gt[mask])
    id_pos, id_pos_gt = np.where(iou > self.params['target_args']['pos_threshold'])
    id_neg = np.where(np.sum(iou < self.params['target_args']['neg_threshold'], axis=1) == iou.shape[1])[0]
    id_pos = np.concatenate([id_pos, id_highest])
    id_pos_gt = np.concatenate([id_pos_gt, id_highest_gt])
    id_pos, index = np.unique(id_pos, return_index=True)
    id_pos_gt = id_pos_gt[index]
    id_neg.sort()
    index_x, index_y, index_z = np.unravel_index(id_pos, (*feature_map_shape, self.anchor_num))
    pos_equal_one[index_x, index_y, index_z] = 1
    targets[index_x, index_y, np.array(index_z) * 7] = (gt_box_center[id_pos_gt, 0] - anchors[id_pos, 0]) / anchors_d[id_pos]
    targets[index_x, index_y, np.array(index_z) * 7 + 1] = (gt_box_center[id_pos_gt, 1] - anchors[id_pos, 1]) / anchors_d[id_pos]
    targets[index_x, index_y, np.array(index_z) * 7 + 2] = (gt_box_center[id_pos_gt, 2] - anchors[id_pos, 2]) / anchors[id_pos, 3]
    targets[index_x, index_y, np.array(index_z) * 7 + 3] = np.log(gt_box_center[id_pos_gt, 3] / anchors[id_pos, 3])
    targets[index_x, index_y, np.array(index_z) * 7 + 4] = np.log(gt_box_center[id_pos_gt, 4] / anchors[id_pos, 4])
    targets[index_x, index_y, np.array(index_z) * 7 + 5] = np.log(gt_box_center[id_pos_gt, 5] / anchors[id_pos, 5])
    targets[index_x, index_y, np.array(index_z) * 7 + 6] = gt_box_center[id_pos_gt, 6] - anchors[id_pos, 6]
    index_x, index_y, index_z = np.unravel_index(id_neg, (*feature_map_shape, self.anchor_num))
    neg_equal_one[index_x, index_y, index_z] = 1
    index_x, index_y, index_z = np.unravel_index(id_highest, (*feature_map_shape, self.anchor_num))
    neg_equal_one[index_x, index_y, index_z] = 0
    label_dict = {'pos_equal_one': pos_equal_one, 'neg_equal_one': neg_equal_one, 'targets': targets}
    return label_dict

class BevPreprocessor(BasePreprocessor):

    def __init__(self, preprocess_params, train):
        super(BevPreprocessor, self).__init__(preprocess_params, train)
        self.lidar_range = self.params['cav_lidar_range']
        self.geometry_param = preprocess_params['geometry_param']

    def preprocess(self, pcd_raw):
        """
        Preprocess the lidar points to BEV representations.

        Parameters
        ----------
        pcd_raw : np.ndarray
            The raw lidar.

        Returns
        -------
        data_dict : the structured output dictionary.
        """
        bev = np.zeros(self.geometry_param['input_shape'], dtype=np.float32)
        intensity_map_count = np.zeros((bev.shape[0], bev.shape[1]), dtype=np.int)
        bev_origin = np.array([self.geometry_param['L1'], self.geometry_param['W1'], self.geometry_param['H1']]).reshape(1, -1)
        indices = ((pcd_raw[:, :3] - bev_origin) / self.geometry_param['res']).astype(int)
        for i in range(indices.shape[0]):
            bev[indices[i, 0], indices[i, 1], indices[i, 2]] = 1
            bev[indices[i, 0], indices[i, 1], -1] += pcd_raw[i, 3]
            intensity_map_count[indices[i, 0], indices[i, 1]] += 1
        divide_mask = intensity_map_count != 0
        bev[divide_mask, -1] = np.divide(bev[divide_mask, -1], intensity_map_count[divide_mask])
        data_dict = {'bev_input': np.transpose(bev, (2, 0, 1))}
        return data_dict

    @staticmethod
    def collate_batch_list(batch):
        """
        Customized pytorch data loader collate function.

        Parameters
        ----------
        batch : list
            List of dictionary. Each dictionary represent a single frame.

        Returns
        -------
        processed_batch : dict
            Updated lidar batch.
        """
        bev_input_list = [x['bev_input'][np.newaxis, ...] for x in batch]
        processed_batch = {'bev_input': torch.from_numpy(np.concatenate(bev_input_list, axis=0))}
        return processed_batch

    @staticmethod
    def collate_batch_dict(batch):
        """
        Customized pytorch data loader collate function.

        Parameters
        ----------
        batch : dict
            Dict of list. Each element represents a CAV.

        Returns
        -------
        processed_batch : dict
            Updated lidar batch.
        """
        bev_input_list = [x[np.newaxis, ...] for x in batch['bev_input']]
        processed_batch = {'bev_input': torch.from_numpy(np.concatenate(bev_input_list, axis=0))}
        return processed_batch

    def collate_batch(self, batch):
        """
        Customized pytorch data loader collate function.

        Parameters
        ----------
        batch : list / dict
            Batched data.
        Returns
        -------
        processed_batch : dict
            Updated lidar batch.
        """
        if isinstance(batch, list):
            return self.collate_batch_list(batch)
        elif isinstance(batch, dict):
            return self.collate_batch_dict(batch)
        else:
            raise NotImplemented

def preprocess(self, pcd_raw):
    """
        Preprocess the lidar points to BEV representations.

        Parameters
        ----------
        pcd_raw : np.ndarray
            The raw lidar.

        Returns
        -------
        data_dict : the structured output dictionary.
        """
    bev = np.zeros(self.geometry_param['input_shape'], dtype=np.float32)
    intensity_map_count = np.zeros((bev.shape[0], bev.shape[1]), dtype=np.int)
    bev_origin = np.array([self.geometry_param['L1'], self.geometry_param['W1'], self.geometry_param['H1']]).reshape(1, -1)
    indices = ((pcd_raw[:, :3] - bev_origin) / self.geometry_param['res']).astype(int)
    for i in range(indices.shape[0]):
        bev[indices[i, 0], indices[i, 1], indices[i, 2]] = 1
        bev[indices[i, 0], indices[i, 1], -1] += pcd_raw[i, 3]
        intensity_map_count[indices[i, 0], indices[i, 1]] += 1
    divide_mask = intensity_map_count != 0
    bev[divide_mask, -1] = np.divide(bev[divide_mask, -1], intensity_map_count[divide_mask])
    data_dict = {'bev_input': np.transpose(bev, (2, 0, 1))}
    return data_dict

class SpVoxelPreprocessor(BasePreprocessor):

    def __init__(self, preprocess_params, train):
        super(SpVoxelPreprocessor, self).__init__(preprocess_params, train)
        self.lidar_range = self.params['cav_lidar_range']
        self.voxel_size = self.params['args']['voxel_size']
        self.max_points_per_voxel = self.params['args']['max_points_per_voxel']
        if train:
            self.max_voxels = self.params['args']['max_voxel_train']
        else:
            self.max_voxels = self.params['args']['max_voxel_test']
        grid_size = (np.array(self.lidar_range[3:6]) - np.array(self.lidar_range[0:3])) / np.array(self.voxel_size)
        self.grid_size = np.round(grid_size).astype(np.int64)
        self.voxel_generator = Point2VoxelCPU3d(vsize_xyz=self.voxel_size, coors_range_xyz=self.lidar_range, max_num_points_per_voxel=self.max_points_per_voxel, num_point_features=4, max_num_voxels=self.max_voxels)

    def preprocess(self, pcd_np):
        data_dict = {}
        pcd_tv = tv.from_numpy(pcd_np)
        voxel_output = self.voxel_generator.point_to_voxel(pcd_tv)
        if isinstance(voxel_output, dict):
            voxels, coordinates, num_points = (voxel_output['voxels'], voxel_output['coordinates'], voxel_output['num_points_per_voxel'])
        else:
            voxels, coordinates, num_points = voxel_output
        data_dict['voxel_features'] = voxels.numpy()
        data_dict['voxel_coords'] = coordinates.numpy()
        data_dict['voxel_num_points'] = num_points.numpy()
        return data_dict

    def collate_batch(self, batch):
        """
        Customized pytorch data loader collate function.

        Parameters
        ----------
        batch : list or dict
            List or dictionary.

        Returns
        -------
        processed_batch : dict
            Updated lidar batch.
        """
        if isinstance(batch, list):
            return self.collate_batch_list(batch)
        elif isinstance(batch, dict):
            return self.collate_batch_dict(batch)
        else:
            sys.exit('Batch has too be a list or a dictionarn')

    @staticmethod
    def collate_batch_list(batch):
        """
        Customized pytorch data loader collate function.

        Parameters
        ----------
        batch : list
            List of dictionary. Each dictionary represent a single frame.

        Returns
        -------
        processed_batch : dict
            Updated lidar batch.
        """
        voxel_features = []
        voxel_num_points = []
        voxel_coords = []
        for i in range(len(batch)):
            voxel_features.append(batch[i]['voxel_features'])
            voxel_num_points.append(batch[i]['voxel_num_points'])
            coords = batch[i]['voxel_coords']
            voxel_coords.append(np.pad(coords, ((0, 0), (1, 0)), mode='constant', constant_values=i))
        voxel_num_points = torch.from_numpy(np.concatenate(voxel_num_points))
        voxel_features = torch.from_numpy(np.concatenate(voxel_features))
        voxel_coords = torch.from_numpy(np.concatenate(voxel_coords))
        return {'voxel_features': voxel_features, 'voxel_coords': voxel_coords, 'voxel_num_points': voxel_num_points}

    @staticmethod
    def collate_batch_dict(batch: dict):
        """
        Collate batch if the batch is a dictionary,
        eg: {'voxel_features': [feature1, feature2...., feature n]}

        Parameters
        ----------
        batch : dict

        Returns
        -------
        processed_batch : dict
            Updated lidar batch.
        """
        voxel_features = torch.from_numpy(np.concatenate(batch['voxel_features']))
        voxel_num_points = torch.from_numpy(np.concatenate(batch['voxel_num_points']))
        coords = batch['voxel_coords']
        voxel_coords = []
        for i in range(len(coords)):
            voxel_coords.append(np.pad(coords[i], ((0, 0), (1, 0)), mode='constant', constant_values=i))
        voxel_coords = torch.from_numpy(np.concatenate(voxel_coords))
        return {'voxel_features': voxel_features, 'voxel_coords': voxel_coords, 'voxel_num_points': voxel_num_points}

def __init__(self, preprocess_params, train):
    super(SpVoxelPreprocessor, self).__init__(preprocess_params, train)
    self.lidar_range = self.params['cav_lidar_range']
    self.voxel_size = self.params['args']['voxel_size']
    self.max_points_per_voxel = self.params['args']['max_points_per_voxel']
    if train:
        self.max_voxels = self.params['args']['max_voxel_train']
    else:
        self.max_voxels = self.params['args']['max_voxel_test']
    grid_size = (np.array(self.lidar_range[3:6]) - np.array(self.lidar_range[0:3])) / np.array(self.voxel_size)
    self.grid_size = np.round(grid_size).astype(np.int64)
    self.voxel_generator = Point2VoxelCPU3d(vsize_xyz=self.voxel_size, coors_range_xyz=self.lidar_range, max_num_points_per_voxel=self.max_points_per_voxel, num_point_features=4, max_num_voxels=self.max_voxels)

def load_point_pillar_params(param):
    """
    Based on the lidar range and resolution of voxel, calcuate the anchor box
    and target resolution.

    Parameters
    ----------
    param : dict
        Original loaded parameter dictionary.

    Returns
    -------
    param : dict
        Modified parameter dictionary with new attribute.
    """
    cav_lidar_range = param['preprocess']['cav_lidar_range']
    voxel_size = param['preprocess']['args']['voxel_size']
    grid_size = (np.array(cav_lidar_range[3:6]) - np.array(cav_lidar_range[0:3])) / np.array(voxel_size)
    grid_size = np.round(grid_size).astype(np.int64)
    param['model']['args']['point_pillar_scatter']['grid_size'] = grid_size
    anchor_args = param['postprocess']['anchor_args']
    vw = voxel_size[0]
    vh = voxel_size[1]
    vd = voxel_size[2]
    anchor_args['vw'] = vw
    anchor_args['vh'] = vh
    anchor_args['vd'] = vd
    anchor_args['W'] = math.ceil((cav_lidar_range[3] - cav_lidar_range[0]) / vw)
    anchor_args['H'] = math.ceil((cav_lidar_range[4] - cav_lidar_range[1]) / vh)
    anchor_args['D'] = math.ceil((cav_lidar_range[5] - cav_lidar_range[2]) / vd)
    param['postprocess'].update({'anchor_args': anchor_args})
    return param

def load_second_params(param):
    """
    Based on the lidar range and resolution of voxel, calcuate the anchor box
    and target resolution.

    Parameters
    ----------
    param : dict
        Original loaded parameter dictionary.

    Returns
    -------
    param : dict
        Modified parameter dictionary with new attribute.
    """
    cav_lidar_range = param['preprocess']['cav_lidar_range']
    voxel_size = param['preprocess']['args']['voxel_size']
    grid_size = (np.array(cav_lidar_range[3:6]) - np.array(cav_lidar_range[0:3])) / np.array(voxel_size)
    grid_size = np.round(grid_size).astype(np.int64)
    param['model']['args']['grid_size'] = grid_size
    anchor_args = param['postprocess']['anchor_args']
    vw = voxel_size[0]
    vh = voxel_size[1]
    vd = voxel_size[2]
    anchor_args['vw'] = vw
    anchor_args['vh'] = vh
    anchor_args['vd'] = vd
    anchor_args['W'] = math.ceil((cav_lidar_range[3] - cav_lidar_range[0]) / vw)
    anchor_args['H'] = math.ceil((cav_lidar_range[4] - cav_lidar_range[1]) / vh)
    anchor_args['D'] = math.ceil((cav_lidar_range[5] - cav_lidar_range[2]) / vd)
    param['postprocess'].update({'anchor_args': anchor_args})
    return param

