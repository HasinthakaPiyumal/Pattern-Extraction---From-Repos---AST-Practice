# Cluster 13

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

def rotate_points_along_z(points, angle):
    """
    Args:
        points: (B, N, 3 + C)
        angle: (B), radians, angle along z-axis, angle increases x ==> y
    Returns:

    """
    points, is_numpy = check_numpy_to_torch(points)
    angle, _ = check_numpy_to_torch(angle)
    cosa = torch.cos(angle)
    sina = torch.sin(angle)
    zeros = angle.new_zeros(points.shape[0])
    ones = angle.new_ones(points.shape[0])
    rot_matrix = torch.stack((cosa, sina, zeros, -sina, cosa, zeros, zeros, zeros, ones), dim=1).view(-1, 3, 3).float()
    points_rot = torch.matmul(points[:, :, 0:3].float(), rot_matrix)
    points_rot = torch.cat((points_rot, points[:, :, 3:]), dim=-1)
    return points_rot.numpy() if is_numpy else points_rot

def rotate_points_along_z_2d(points, angle):
    """
    Rorate the points along z-axis.
    Parameters
    ----------
    points : torch.Tensor / np.ndarray
        (N, 2).
    angle : torch.Tensor / np.ndarray
        (N,)

    Returns
    -------
    points_rot : torch.Tensor / np.ndarray
        Rorated points with shape (N, 2)

    """
    points, is_numpy = check_numpy_to_torch(points)
    angle, _ = check_numpy_to_torch(angle)
    cosa = torch.cos(angle)
    sina = torch.sin(angle)
    rot_matrix = torch.stack((cosa, sina, -sina, cosa), dim=1).view(-1, 2, 2).float()
    points_rot = torch.einsum('ik, ikj->ij', points.float(), rot_matrix)
    return points_rot.numpy() if is_numpy else points_rot

def calculate_ap(result_stat, iou):
    """
    Calculate the average precision and recall, and save them into a txt.

    Parameters
    ----------
    result_stat : dict
        A dictionary contains fp, tp and gt number.
    iou : float
    """
    iou_5 = result_stat[iou]
    fp = iou_5['fp']
    tp = iou_5['tp']
    assert len(fp) == len(tp)
    gt_total = iou_5['gt']
    cumsum = 0
    for idx, val in enumerate(fp):
        fp[idx] += cumsum
        cumsum += val
    cumsum = 0
    for idx, val in enumerate(tp):
        tp[idx] += cumsum
        cumsum += val
    rec = tp[:]
    for idx, val in enumerate(tp):
        rec[idx] = float(tp[idx]) / gt_total
    prec = tp[:]
    for idx, val in enumerate(tp):
        prec[idx] = float(tp[idx]) / (fp[idx] + tp[idx])
    ap, mrec, mprec = voc_ap(rec[:], prec[:])
    return (ap, mrec, mprec)

def boxes2d_to_corners2d(boxes2d, order='lwh'):
    """
      0 -------- 1
      |          |
      |          |
      |          |
      3 -------- 2
    Parameters
    __________
    boxes2d: np.ndarray or torch.Tensor
        (..., 5) [x, y, dx, dy, heading], (x, y) is the box center.

    order : str
        'lwh' or 'hwl'

    Returns:
        corners2d: np.ndarray or torch.Tensor
        (..., 4, 2), the 4 corners of the bounding box.

    """
    assert order == 'lwh', 'boxes2d_to_corners_2d only supports lwh order for now.'
    boxes2d, is_numpy = common_utils.check_numpy_to_torch(boxes2d)
    template = boxes2d.new_tensor(([1, -1], [1, 1], [-1, 1], [-1, -1])) / 2
    input_shape = boxes2d.shape
    boxes2d = boxes2d.view(-1, 5)
    corners2d = boxes2d[:, None, 2:4].repeat(1, 4, 1) * template[None, :, :]
    corners2d = common_utils.rotate_points_along_z_2d(corners2d.view(-1, 2), boxes2d[:, 4].repeat_interleave(4)).view(-1, 4, 2)
    corners2d += boxes2d[:, None, 0:2]
    corners2d = corners2d.view(*input_shape[:-1], 4, 2)
    return corners2d

def boxes_to_corners_3d(boxes3d, order):
    """
        4 -------- 5
       /|         /|
      7 -------- 6 .
      | |        | |
      . 0 -------- 1
      |/         |/
      3 -------- 2
    Parameters
    __________
    boxes3d: np.ndarray or torch.Tensor
        (N, 7) [x, y, z, dx, dy, dz, heading], (x, y, z) is the box center.

    order : str
        'lwh' or 'hwl'

    Returns:
        corners3d: np.ndarray or torch.Tensor
        (N, 8, 3), the 8 corners of the bounding box.

    """
    boxes3d, is_numpy = common_utils.check_numpy_to_torch(boxes3d)
    if order == 'hwl':
        boxes3d[:, 3:6] = boxes3d[:, [5, 4, 3]]
    template = boxes3d.new_tensor(([1, -1, -1], [1, 1, -1], [-1, 1, -1], [-1, -1, -1], [1, -1, 1], [1, 1, 1], [-1, 1, 1], [-1, -1, 1])) / 2
    corners3d = boxes3d[:, None, 3:6].repeat(1, 8, 1) * template[None, :, :]
    corners3d = common_utils.rotate_points_along_z(corners3d.view(-1, 8, 3), boxes3d[:, 6]).view(-1, 8, 3)
    corners3d += boxes3d[:, None, 0:3]
    return corners3d.numpy() if is_numpy else corners3d

def project_box3d(box3d, transformation_matrix):
    """
    Project the 3d bounding box to another coordinate system based on the
    transfomration matrix.

    Parameters
    ----------
    box3d : torch.Tensor or np.ndarray
        3D bounding box, (N, 8, 3)

    transformation_matrix : torch.Tensor or np.ndarray
        Transformation matrix, (4, 4)

    Returns
    -------
    projected_box3d : torch.Tensor
        The projected bounding box, (N, 8, 3)
    """
    assert transformation_matrix.shape == (4, 4)
    box3d, is_numpy = common_utils.check_numpy_to_torch(box3d)
    transformation_matrix, _ = common_utils.check_numpy_to_torch(transformation_matrix)
    box3d_corner = box3d.transpose(1, 2)
    torch_ones = torch.ones((box3d_corner.shape[0], 1, 8))
    torch_ones = torch_ones.to(box3d_corner.device)
    box3d_corner = torch.cat((box3d_corner, torch_ones), dim=1)
    projected_box3d = torch.matmul(transformation_matrix, box3d_corner)
    projected_box3d = projected_box3d[:, :3, :].transpose(1, 2)
    return projected_box3d if not is_numpy else projected_box3d.numpy()

def project_points_by_matrix_torch(points, transformation_matrix):
    """
    Project the points to another coordinate system based on the
    transformation matrix.

    Parameters
    ----------
    points : torch.Tensor
        3D points, (N, 3)
    transformation_matrix : torch.Tensor
        Transformation matrix, (4, 4)
    Returns
    -------
    projected_points : torch.Tensor
        The projected points, (N, 3)
    """
    points, is_numpy = common_utils.check_numpy_to_torch(points)
    transformation_matrix, _ = common_utils.check_numpy_to_torch(transformation_matrix)
    points_homogeneous = F.pad(points, (0, 1), mode='constant', value=1)
    projected_points = torch.einsum('ik, jk->ij', points_homogeneous, transformation_matrix)
    return projected_points[:, :3] if not is_numpy else projected_points[:, :3].numpy()

class ConvGRU(nn.Module):

    def __init__(self, input_size, input_dim, hidden_dim, kernel_size, num_layers, batch_first=False, bias=True, return_all_layers=False):
        """
        :param input_size: (int, int)
            Height and width of input tensor as (height, width).
        :param input_dim: int e.g. 256
            Number of channels of input tensor.
        :param hidden_dim: int e.g. 1024
            Number of channels of hidden state.
        :param kernel_size: (int, int)
            Size of the convolutional kernel.
        :param num_layers: int
            Number of ConvLSTM layers
        :param dtype: torch.cuda.FloatTensor or torch.FloatTensor
            Whether or not to use cuda.
        :param alexnet_path: str
            pretrained alexnet parameters
        :param batch_first: bool
            if the first position of array is batch or not
        :param bias: bool
            Whether or not to add the bias.
        :param return_all_layers: bool
            if return hidden and cell states for all layers
        """
        super(ConvGRU, self).__init__()
        kernel_size = self._extend_for_multilayer(kernel_size, num_layers)
        hidden_dim = self._extend_for_multilayer(hidden_dim, num_layers)
        if not len(kernel_size) == len(hidden_dim) == num_layers:
            raise ValueError('Inconsistent list length.')
        self.height, self.width = input_size
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.kernel_size = kernel_size
        self.num_layers = num_layers
        self.batch_first = batch_first
        self.bias = bias
        self.return_all_layers = return_all_layers
        cell_list = []
        for i in range(0, self.num_layers):
            cur_input_dim = input_dim if i == 0 else hidden_dim[i - 1]
            cell_list.append(ConvGRUCell(input_size=(self.height, self.width), input_dim=cur_input_dim, hidden_dim=self.hidden_dim[i], kernel_size=self.kernel_size[i], bias=self.bias))
        self.cell_list = nn.ModuleList(cell_list)

    def forward(self, input_tensor, hidden_state=None):
        """
        :param input_tensor: (b, t, c, h, w) or (t,b,c,h,w)
            depends on if batch first or not extracted features from alexnet
        :param hidden_state:
        :return: layer_output_list, last_state_list
        """
        if not self.batch_first:
            input_tensor = input_tensor.permute(1, 0, 2, 3, 4)
        if hidden_state is not None:
            raise NotImplementedError()
        else:
            hidden_state = self._init_hidden(batch_size=input_tensor.size(0), device=input_tensor.device, dtype=input_tensor.dtype)
        layer_output_list = []
        last_state_list = []
        seq_len = input_tensor.size(1)
        cur_layer_input = input_tensor
        for layer_idx in range(self.num_layers):
            h = hidden_state[layer_idx]
            output_inner = []
            for t in range(seq_len):
                h = self.cell_list[layer_idx](input_tensor=cur_layer_input[:, t, :, :, :], h_cur=h)
                output_inner.append(h)
            layer_output = torch.stack(output_inner, dim=1)
            cur_layer_input = layer_output
            layer_output_list.append(layer_output)
            last_state_list.append([h])
        if not self.return_all_layers:
            layer_output_list = layer_output_list[-1:]
            last_state_list = last_state_list[-1:]
        return (layer_output_list, last_state_list)

    def _init_hidden(self, batch_size, device=None, dtype=None):
        init_states = []
        for i in range(self.num_layers):
            init_states.append(self.cell_list[i].init_hidden(batch_size).to(device).to(dtype))
        return init_states

    @staticmethod
    def _check_kernel_size_consistency(kernel_size):
        if not (isinstance(kernel_size, tuple) or (isinstance(kernel_size, list) and all([isinstance(elem, tuple) for elem in kernel_size]))):
            raise ValueError('`kernel_size` must be tuple or list of tuples')

    @staticmethod
    def _extend_for_multilayer(param, num_layers):
        if not isinstance(param, list):
            param = [param] * num_layers
        return param

def forward(self, input_tensor, hidden_state=None):
    """
        :param input_tensor: (b, t, c, h, w) or (t,b,c,h,w)
            depends on if batch first or not extracted features from alexnet
        :param hidden_state:
        :return: layer_output_list, last_state_list
        """
    if not self.batch_first:
        input_tensor = input_tensor.permute(1, 0, 2, 3, 4)
    if hidden_state is not None:
        raise NotImplementedError()
    else:
        hidden_state = self._init_hidden(batch_size=input_tensor.size(0), device=input_tensor.device, dtype=input_tensor.dtype)
    layer_output_list = []
    last_state_list = []
    seq_len = input_tensor.size(1)
    cur_layer_input = input_tensor
    for layer_idx in range(self.num_layers):
        h = hidden_state[layer_idx]
        output_inner = []
        for t in range(seq_len):
            h = self.cell_list[layer_idx](input_tensor=cur_layer_input[:, t, :, :, :], h_cur=h)
            output_inner.append(h)
        layer_output = torch.stack(output_inner, dim=1)
        cur_layer_input = layer_output
        layer_output_list.append(layer_output)
        last_state_list.append([h])
    if not self.return_all_layers:
        layer_output_list = layer_output_list[-1:]
        last_state_list = last_state_list[-1:]
    return (layer_output_list, last_state_list)

class HGTCavAttention(nn.Module):

    def __init__(self, dim, heads, num_types=2, num_relations=4, dim_head=64, dropout=0.1):
        super().__init__()
        inner_dim = heads * dim_head
        self.heads = heads
        self.scale = dim_head ** (-0.5)
        self.num_types = num_types
        self.attend = nn.Softmax(dim=-1)
        self.drop_out = nn.Dropout(dropout)
        self.k_linears = nn.ModuleList()
        self.q_linears = nn.ModuleList()
        self.v_linears = nn.ModuleList()
        self.a_linears = nn.ModuleList()
        self.norms = nn.ModuleList()
        for t in range(num_types):
            self.k_linears.append(nn.Linear(dim, inner_dim))
            self.q_linears.append(nn.Linear(dim, inner_dim))
            self.v_linears.append(nn.Linear(dim, inner_dim))
            self.a_linears.append(nn.Linear(inner_dim, dim))
        self.relation_att = nn.Parameter(torch.Tensor(num_relations, heads, dim_head, dim_head))
        self.relation_msg = nn.Parameter(torch.Tensor(num_relations, heads, dim_head, dim_head))
        torch.nn.init.xavier_uniform(self.relation_att)
        torch.nn.init.xavier_uniform(self.relation_msg)

    def to_qkv(self, x, types):
        q_batch = []
        k_batch = []
        v_batch = []
        for b in range(x.shape[0]):
            q_list = []
            k_list = []
            v_list = []
            for i in range(x.shape[-2]):
                q_list.append(self.q_linears[types[b, i]](x[b, :, :, i, :].unsqueeze(2)))
                k_list.append(self.k_linears[types[b, i]](x[b, :, :, i, :].unsqueeze(2)))
                v_list.append(self.v_linears[types[b, i]](x[b, :, :, i, :].unsqueeze(2)))
            q_batch.append(torch.cat(q_list, dim=2).unsqueeze(0))
            k_batch.append(torch.cat(k_list, dim=2).unsqueeze(0))
            v_batch.append(torch.cat(v_list, dim=2).unsqueeze(0))
        q = torch.cat(q_batch, dim=0)
        k = torch.cat(k_batch, dim=0)
        v = torch.cat(v_batch, dim=0)
        return (q, k, v)

    def get_relation_type_index(self, type1, type2):
        return type1 * self.num_types + type2

    def get_hetero_edge_weights(self, x, types):
        w_att_batch = []
        w_msg_batch = []
        for b in range(x.shape[0]):
            w_att_list = []
            w_msg_list = []
            for i in range(x.shape[-2]):
                w_att_i_list = []
                w_msg_i_list = []
                for j in range(x.shape[-2]):
                    e_type = self.get_relation_type_index(types[b, i], types[b, j])
                    w_att_i_list.append(self.relation_att[e_type].unsqueeze(0))
                    w_msg_i_list.append(self.relation_msg[e_type].unsqueeze(0))
                w_att_list.append(torch.cat(w_att_i_list, dim=0).unsqueeze(0))
                w_msg_list.append(torch.cat(w_msg_i_list, dim=0).unsqueeze(0))
            w_att_batch.append(torch.cat(w_att_list, dim=0).unsqueeze(0))
            w_msg_batch.append(torch.cat(w_msg_list, dim=0).unsqueeze(0))
        w_att = torch.cat(w_att_batch, dim=0).permute(0, 3, 1, 2, 4, 5)
        w_msg = torch.cat(w_msg_batch, dim=0).permute(0, 3, 1, 2, 4, 5)
        return (w_att, w_msg)

    def to_out(self, x, types):
        out_batch = []
        for b in range(x.shape[0]):
            out_list = []
            for i in range(x.shape[-2]):
                out_list.append(self.a_linears[types[b, i]](x[b, :, :, i, :].unsqueeze(2)))
            out_batch.append(torch.cat(out_list, dim=2).unsqueeze(0))
        out = torch.cat(out_batch, dim=0)
        return out

    def forward(self, x, mask, prior_encoding):
        x = x.permute(0, 2, 3, 1, 4)
        mask = mask.unsqueeze(1)
        velocities, dts, types = [itm.squeeze(-1) for itm in prior_encoding[:, :, 0, 0, :].split([1, 1, 1], dim=-1)]
        types = types.to(torch.int)
        dts = dts.to(torch.int)
        qkv = self.to_qkv(x, types)
        w_att, w_msg = self.get_hetero_edge_weights(x, types)
        q, k, v = map(lambda t: rearrange(t, 'b h w l (m c) -> b m h w l c', m=self.heads), qkv)
        att_map = torch.einsum('b m h w i p, b m i j p q, bm h w j q -> b m h w i j', [q, w_att, k]) * self.scale
        att_map = att_map.masked_fill(mask == 0, -float('inf'))
        att_map = self.attend(att_map)
        v_msg = torch.einsum('b m i j p c, b m h w j p -> b m h w i j c', w_msg, v)
        out = torch.einsum('b m h w i j, b m h w i j c -> b m h w i c', att_map, v_msg)
        out = rearrange(out, 'b m h w l c -> b h w l (m c)', m=self.heads)
        out = self.to_out(out, types)
        out = self.drop_out(out)
        out = out.permute(0, 3, 1, 2, 4)
        return out

def forward(self, x, mask, prior_encoding):
    x = x.permute(0, 2, 3, 1, 4)
    mask = mask.unsqueeze(1)
    velocities, dts, types = [itm.squeeze(-1) for itm in prior_encoding[:, :, 0, 0, :].split([1, 1, 1], dim=-1)]
    types = types.to(torch.int)
    dts = dts.to(torch.int)
    qkv = self.to_qkv(x, types)
    w_att, w_msg = self.get_hetero_edge_weights(x, types)
    q, k, v = map(lambda t: rearrange(t, 'b h w l (m c) -> b m h w l c', m=self.heads), qkv)
    att_map = torch.einsum('b m h w i p, b m i j p q, bm h w j q -> b m h w i j', [q, w_att, k]) * self.scale
    att_map = att_map.masked_fill(mask == 0, -float('inf'))
    att_map = self.attend(att_map)
    v_msg = torch.einsum('b m i j p c, b m h w j p -> b m h w i j c', w_msg, v)
    out = torch.einsum('b m h w i j, b m h w i j c -> b m h w i c', att_map, v_msg)
    out = rearrange(out, 'b m h w l c -> b h w l (m c)', m=self.heads)
    out = self.to_out(out, types)
    out = self.drop_out(out)
    out = out.permute(0, 3, 1, 2, 4)
    return out

class RadixSoftmax(nn.Module):

    def __init__(self, radix, cardinality):
        super(RadixSoftmax, self).__init__()
        self.radix = radix
        self.cardinality = cardinality

    def forward(self, x):
        batch = x.size(0)
        cav_num = x.size(1)
        if self.radix > 1:
            x = x.view(batch, cav_num, self.cardinality, self.radix, -1)
            x = F.softmax(x, dim=3)
            x = x.reshape(batch, -1)
        else:
            x = torch.sigmoid(x)
        return x

def forward(self, x):
    batch = x.size(0)
    cav_num = x.size(1)
    if self.radix > 1:
        x = x.view(batch, cav_num, self.cardinality, self.radix, -1)
        x = F.softmax(x, dim=3)
        x = x.reshape(batch, -1)
    else:
        x = torch.sigmoid(x)
    return x

class PreNorm(nn.Module):

    def __init__(self, dim, fn):
        super().__init__()
        self.norm = nn.LayerNorm(dim)
        self.fn = fn

    def forward(self, x, **kwargs):
        return self.fn(self.norm(x), **kwargs)

def forward(self, x, **kwargs):
    return self.fn(self.norm(x), **kwargs)

class CavAttention(nn.Module):
    """
    Vanilla CAV attention.
    """

    def __init__(self, dim, heads, dim_head=64, dropout=0.1):
        super().__init__()
        inner_dim = heads * dim_head
        self.heads = heads
        self.scale = dim_head ** (-0.5)
        self.attend = nn.Softmax(dim=-1)
        self.to_qkv = nn.Linear(dim, inner_dim * 3, bias=False)
        self.to_out = nn.Sequential(nn.Linear(inner_dim, dim), nn.Dropout(dropout))

    def forward(self, x, mask, prior_encoding):
        x = x.permute(0, 2, 3, 1, 4)
        mask = mask.unsqueeze(1)
        qkv = self.to_qkv(x).chunk(3, dim=-1)
        q, k, v = map(lambda t: rearrange(t, 'b h w l (m c) -> b m h w l c', m=self.heads), qkv)
        att_map = torch.einsum('b m h w i c, b m h w j c -> b m h w i j', q, k) * self.scale
        att_map = att_map.masked_fill(mask == 0, -float('inf'))
        att_map = self.attend(att_map)
        out = torch.einsum('b m h w i j, b m h w j c -> b m h w i c', att_map, v)
        out = rearrange(out, 'b m h w l c -> b h w l (m c)', m=self.heads)
        out = self.to_out(out)
        out = out.permute(0, 3, 1, 2, 4)
        return out

def forward(self, x, mask, prior_encoding):
    x = x.permute(0, 2, 3, 1, 4)
    mask = mask.unsqueeze(1)
    qkv = self.to_qkv(x).chunk(3, dim=-1)
    q, k, v = map(lambda t: rearrange(t, 'b h w l (m c) -> b m h w l c', m=self.heads), qkv)
    att_map = torch.einsum('b m h w i c, b m h w j c -> b m h w i j', q, k) * self.scale
    att_map = att_map.masked_fill(mask == 0, -float('inf'))
    att_map = self.attend(att_map)
    out = torch.einsum('b m h w i j, b m h w j c -> b m h w i c', att_map, v)
    out = rearrange(out, 'b m h w l c -> b h w l (m c)', m=self.heads)
    out = self.to_out(out)
    out = out.permute(0, 3, 1, 2, 4)
    return out

def combine_roi_and_cav_mask(roi_mask, cav_mask):
    """
    Combine ROI mask and CAV mask

    Parameters
    ----------
    roi_mask : torch.Tensor
        Mask for ROI region after considering the spatial transformation/correction.
    cav_mask : torch.Tensor
        Mask for CAV to remove padded 0.

    Returns
    -------
    com_mask : torch.Tensor
        Combined mask.
    """
    cav_mask = cav_mask.unsqueeze(2).unsqueeze(3).unsqueeze(4)
    cav_mask = cav_mask.expand(roi_mask.shape)
    com_mask = roi_mask * cav_mask
    return com_mask

class PFNLayer(nn.Module):

    def __init__(self, in_channels, out_channels, use_norm=True, last_layer=False):
        super().__init__()
        self.last_vfe = last_layer
        self.use_norm = use_norm
        if not self.last_vfe:
            out_channels = out_channels // 2
        if self.use_norm:
            self.linear = nn.Linear(in_channels, out_channels, bias=False)
            self.norm = nn.BatchNorm1d(out_channels, eps=0.001, momentum=0.01)
        else:
            self.linear = nn.Linear(in_channels, out_channels, bias=True)
        self.part = 50000

    def forward(self, inputs):
        if inputs.shape[0] > self.part:
            num_parts = inputs.shape[0] // self.part
            part_linear_out = [self.linear(inputs[num_part * self.part:(num_part + 1) * self.part]) for num_part in range(num_parts + 1)]
            x = torch.cat(part_linear_out, dim=0)
        else:
            x = self.linear(inputs)
        torch.backends.cudnn.enabled = False
        x = self.norm(x.permute(0, 2, 1)).permute(0, 2, 1) if self.use_norm else x
        torch.backends.cudnn.enabled = True
        x = F.relu(x)
        x_max = torch.max(x, dim=1, keepdim=True)[0]
        if self.last_vfe:
            return x_max
        else:
            x_repeat = x_max.repeat(1, inputs.shape[1], 1)
            x_concatenated = torch.cat([x, x_repeat], dim=2)
            return x_concatenated

def forward(self, inputs):
    if inputs.shape[0] > self.part:
        num_parts = inputs.shape[0] // self.part
        part_linear_out = [self.linear(inputs[num_part * self.part:(num_part + 1) * self.part]) for num_part in range(num_parts + 1)]
        x = torch.cat(part_linear_out, dim=0)
    else:
        x = self.linear(inputs)
    torch.backends.cudnn.enabled = False
    x = self.norm(x.permute(0, 2, 1)).permute(0, 2, 1) if self.use_norm else x
    torch.backends.cudnn.enabled = True
    x = F.relu(x)
    x_max = torch.max(x, dim=1, keepdim=True)[0]
    if self.last_vfe:
        return x_max
    else:
        x_repeat = x_max.repeat(1, inputs.shape[1], 1)
        x_concatenated = torch.cat([x, x_repeat], dim=2)
        return x_concatenated

class PillarVFE(nn.Module):

    def __init__(self, model_cfg, num_point_features, voxel_size, point_cloud_range):
        super().__init__()
        self.model_cfg = model_cfg
        self.use_norm = self.model_cfg['use_norm']
        self.with_distance = self.model_cfg['with_distance']
        self.use_absolute_xyz = self.model_cfg['use_absolute_xyz']
        num_point_features += 6 if self.use_absolute_xyz else 3
        if self.with_distance:
            num_point_features += 1
        self.num_filters = self.model_cfg['num_filters']
        assert len(self.num_filters) > 0
        num_filters = [num_point_features] + list(self.num_filters)
        pfn_layers = []
        for i in range(len(num_filters) - 1):
            in_filters = num_filters[i]
            out_filters = num_filters[i + 1]
            pfn_layers.append(PFNLayer(in_filters, out_filters, self.use_norm, last_layer=i >= len(num_filters) - 2))
        self.pfn_layers = nn.ModuleList(pfn_layers)
        self.voxel_x = voxel_size[0]
        self.voxel_y = voxel_size[1]
        self.voxel_z = voxel_size[2]
        self.x_offset = self.voxel_x / 2 + point_cloud_range[0]
        self.y_offset = self.voxel_y / 2 + point_cloud_range[1]
        self.z_offset = self.voxel_z / 2 + point_cloud_range[2]

    def get_output_feature_dim(self):
        return self.num_filters[-1]

    @staticmethod
    def get_paddings_indicator(actual_num, max_num, axis=0):
        actual_num = torch.unsqueeze(actual_num, axis + 1)
        max_num_shape = [1] * len(actual_num.shape)
        max_num_shape[axis + 1] = -1
        max_num = torch.arange(max_num, dtype=torch.int, device=actual_num.device).view(max_num_shape)
        paddings_indicator = actual_num.int() > max_num
        return paddings_indicator

    def forward(self, batch_dict):
        voxel_features, voxel_num_points, coords = (batch_dict['voxel_features'], batch_dict['voxel_num_points'], batch_dict['voxel_coords'])
        points_mean = voxel_features[:, :, :3].sum(dim=1, keepdim=True) / voxel_num_points.type_as(voxel_features).view(-1, 1, 1)
        f_cluster = voxel_features[:, :, :3] - points_mean
        f_center = torch.zeros_like(voxel_features[:, :, :3])
        f_center[:, :, 0] = voxel_features[:, :, 0] - (coords[:, 3].to(voxel_features.dtype).unsqueeze(1) * self.voxel_x + self.x_offset)
        f_center[:, :, 1] = voxel_features[:, :, 1] - (coords[:, 2].to(voxel_features.dtype).unsqueeze(1) * self.voxel_y + self.y_offset)
        f_center[:, :, 2] = voxel_features[:, :, 2] - (coords[:, 1].to(voxel_features.dtype).unsqueeze(1) * self.voxel_z + self.z_offset)
        if self.use_absolute_xyz:
            features = [voxel_features, f_cluster, f_center]
        else:
            features = [voxel_features[..., 3:], f_cluster, f_center]
        if self.with_distance:
            points_dist = torch.norm(voxel_features[:, :, :3], 2, 2, keepdim=True)
            features.append(points_dist)
        features = torch.cat(features, dim=-1)
        voxel_count = features.shape[1]
        mask = self.get_paddings_indicator(voxel_num_points, voxel_count, axis=0)
        mask = torch.unsqueeze(mask, -1).type_as(voxel_features)
        features *= mask
        for pfn in self.pfn_layers:
            features = pfn(features)
        features = features.squeeze()
        batch_dict['pillar_features'] = features
        return batch_dict

def forward(self, batch_dict):
    voxel_features, voxel_num_points, coords = (batch_dict['voxel_features'], batch_dict['voxel_num_points'], batch_dict['voxel_coords'])
    points_mean = voxel_features[:, :, :3].sum(dim=1, keepdim=True) / voxel_num_points.type_as(voxel_features).view(-1, 1, 1)
    f_cluster = voxel_features[:, :, :3] - points_mean
    f_center = torch.zeros_like(voxel_features[:, :, :3])
    f_center[:, :, 0] = voxel_features[:, :, 0] - (coords[:, 3].to(voxel_features.dtype).unsqueeze(1) * self.voxel_x + self.x_offset)
    f_center[:, :, 1] = voxel_features[:, :, 1] - (coords[:, 2].to(voxel_features.dtype).unsqueeze(1) * self.voxel_y + self.y_offset)
    f_center[:, :, 2] = voxel_features[:, :, 2] - (coords[:, 1].to(voxel_features.dtype).unsqueeze(1) * self.voxel_z + self.z_offset)
    if self.use_absolute_xyz:
        features = [voxel_features, f_cluster, f_center]
    else:
        features = [voxel_features[..., 3:], f_cluster, f_center]
    if self.with_distance:
        points_dist = torch.norm(voxel_features[:, :, :3], 2, 2, keepdim=True)
        features.append(points_dist)
    features = torch.cat(features, dim=-1)
    voxel_count = features.shape[1]
    mask = self.get_paddings_indicator(voxel_num_points, voxel_count, axis=0)
    mask = torch.unsqueeze(mask, -1).type_as(voxel_features)
    features *= mask
    for pfn in self.pfn_layers:
        features = pfn(features)
    features = features.squeeze()
    batch_dict['pillar_features'] = features
    return batch_dict

class ScaledDotProductAttention(nn.Module):
    """
    Scaled Dot-Product Attention proposed in "Attention Is All You Need"
    Compute the dot products of the query with all keys, divide each by sqrt(dim),
    and apply a softmax function to obtain the weights on the values
    Args: dim, mask
        dim (int): dimention of attention
        mask (torch.Tensor): tensor containing indices to be masked
    Inputs: query, key, value, mask
        - **query** (batch, q_len, d_model): tensor containing projection vector for decoder.
        - **key** (batch, k_len, d_model): tensor containing projection vector for encoder.
        - **value** (batch, v_len, d_model): tensor containing features of the encoded input sequence.
        - **mask** (-): tensor containing indices to be masked
    Returns: context, attn
        - **context**: tensor containing the context vector from attention mechanism.
        - **attn**: tensor containing the attention (alignment) from the encoder outputs.
    """

    def __init__(self, dim):
        super(ScaledDotProductAttention, self).__init__()
        self.sqrt_dim = np.sqrt(dim)

    def forward(self, query, key, value):
        score = torch.bmm(query, key.transpose(1, 2)) / self.sqrt_dim
        attn = F.softmax(score, -1)
        context = torch.bmm(attn, value)
        return context

def forward(self, query, key, value):
    score = torch.bmm(query, key.transpose(1, 2)) / self.sqrt_dim
    attn = F.softmax(score, -1)
    context = torch.bmm(attn, value)
    return context

class BaseWindowAttention(nn.Module):

    def __init__(self, dim, heads, dim_head, drop_out, window_size, relative_pos_embedding):
        super().__init__()
        inner_dim = dim_head * heads
        self.heads = heads
        self.scale = dim_head ** (-0.5)
        self.window_size = window_size
        self.relative_pos_embedding = relative_pos_embedding
        self.to_qkv = nn.Linear(dim, inner_dim * 3, bias=False)
        if self.relative_pos_embedding:
            self.relative_indices = get_relative_distances(window_size) + window_size - 1
            self.pos_embedding = nn.Parameter(torch.randn(2 * window_size - 1, 2 * window_size - 1))
        else:
            self.pos_embedding = nn.Parameter(torch.randn(window_size ** 2, window_size ** 2))
        self.to_out = nn.Sequential(nn.Linear(inner_dim, dim), nn.Dropout(drop_out))

    def forward(self, x):
        b, l, h, w, c, m = (*x.shape, self.heads)
        qkv = self.to_qkv(x).chunk(3, dim=-1)
        new_h = h // self.window_size
        new_w = w // self.window_size
        q, k, v = map(lambda t: rearrange(t, 'b l (new_h w_h) (new_w w_w) (m c) -> b l m (new_h new_w) (w_h w_w) c', m=m, w_h=self.window_size, w_w=self.window_size), qkv)
        dots = torch.einsum('b l m h i c, b l m h j c -> b l m h i j', q, k) * self.scale
        if self.relative_pos_embedding:
            dots += self.pos_embedding[self.relative_indices[:, :, 0], self.relative_indices[:, :, 1]]
        else:
            dots += self.pos_embedding
        attn = dots.softmax(dim=-1)
        out = torch.einsum('b l m h i j, b l m h j c -> b l m h i c', attn, v)
        out = rearrange(out, 'b l m (new_h new_w) (w_h w_w) c -> b l (new_h w_h) (new_w w_w) (m c)', m=self.heads, w_h=self.window_size, w_w=self.window_size, new_w=new_w, new_h=new_h)
        out = self.to_out(out)
        return out

def forward(self, x):
    b, l, h, w, c, m = (*x.shape, self.heads)
    qkv = self.to_qkv(x).chunk(3, dim=-1)
    new_h = h // self.window_size
    new_w = w // self.window_size
    q, k, v = map(lambda t: rearrange(t, 'b l (new_h w_h) (new_w w_w) (m c) -> b l m (new_h new_w) (w_h w_w) c', m=m, w_h=self.window_size, w_w=self.window_size), qkv)
    dots = torch.einsum('b l m h i c, b l m h j c -> b l m h i j', q, k) * self.scale
    if self.relative_pos_embedding:
        dots += self.pos_embedding[self.relative_indices[:, :, 0], self.relative_indices[:, :, 1]]
    else:
        dots += self.pos_embedding
    attn = dots.softmax(dim=-1)
    out = torch.einsum('b l m h i j, b l m h j c -> b l m h i c', attn, v)
    out = rearrange(out, 'b l m (new_h new_w) (w_h w_w) c -> b l (new_h w_h) (new_w w_w) (m c)', m=self.heads, w_h=self.window_size, w_w=self.window_size, new_w=new_w, new_h=new_h)
    out = self.to_out(out)
    return out

class VoxelNetLoss(nn.Module):

    def __init__(self, args):
        super(VoxelNetLoss, self).__init__()
        self.smoothl1loss = nn.SmoothL1Loss(size_average=False)
        self.alpha = args['alpha']
        self.beta = args['beta']
        self.reg_coe = args['reg']
        self.loss_dict = {}

    def forward(self, output_dict, target_dict):
        """
        Parameters
        ----------
        output_dict : dict
        target_dict : dict
        """
        rm = output_dict['rm']
        psm = output_dict['psm']
        pos_equal_one = target_dict['pos_equal_one']
        neg_equal_one = target_dict['neg_equal_one']
        targets = target_dict['targets']
        p_pos = F.sigmoid(psm.permute(0, 2, 3, 1))
        rm = rm.permute(0, 2, 3, 1).contiguous()
        rm = rm.view(rm.size(0), rm.size(1), rm.size(2), -1, 7)
        targets = targets.view(targets.size(0), targets.size(1), targets.size(2), -1, 7)
        pos_equal_one_for_reg = pos_equal_one.unsqueeze(pos_equal_one.dim()).expand(-1, -1, -1, -1, 7)
        rm_pos = rm * pos_equal_one_for_reg
        targets_pos = targets * pos_equal_one_for_reg
        cls_pos_loss = -pos_equal_one * torch.log(p_pos + 1e-06)
        cls_pos_loss = cls_pos_loss.sum() / (pos_equal_one.sum() + 1e-06)
        cls_neg_loss = -neg_equal_one * torch.log(1 - p_pos + 1e-06)
        cls_neg_loss = cls_neg_loss.sum() / (neg_equal_one.sum() + 1e-06)
        reg_loss = self.smoothl1loss(rm_pos, targets_pos)
        reg_loss = reg_loss / (pos_equal_one.sum() + 1e-06)
        conf_loss = self.alpha * cls_pos_loss + self.beta * cls_neg_loss
        total_loss = self.reg_coe * reg_loss + conf_loss
        self.loss_dict.update({'total_loss': total_loss, 'reg_loss': reg_loss, 'conf_loss': conf_loss})
        return total_loss

    def logging(self, epoch, batch_id, batch_len, writer):
        """
        Print out  the loss function for current iteration.

        Parameters
        ----------
        epoch : int
            Current epoch for training.
        batch_id : int
            The current batch.
        batch_len : int
            Total batch length in one iteration of training,
        writer : SummaryWriter
            Used to visualize on tensorboard
        """
        total_loss = self.loss_dict['total_loss']
        reg_loss = self.loss_dict['reg_loss']
        conf_loss = self.loss_dict['conf_loss']
        print('[epoch %d][%d/%d], || Loss: %.4f || Conf Loss: %.4f || Loc Loss: %.4f' % (epoch, batch_id + 1, batch_len, total_loss.item(), conf_loss.item(), reg_loss.item()))
        writer.add_scalar('Regression_loss', reg_loss.item(), epoch * batch_len + batch_id)
        writer.add_scalar('Confidence_loss', conf_loss.item(), epoch * batch_len + batch_id)

def forward(self, output_dict, target_dict):
    """
        Parameters
        ----------
        output_dict : dict
        target_dict : dict
        """
    rm = output_dict['rm']
    psm = output_dict['psm']
    pos_equal_one = target_dict['pos_equal_one']
    neg_equal_one = target_dict['neg_equal_one']
    targets = target_dict['targets']
    p_pos = F.sigmoid(psm.permute(0, 2, 3, 1))
    rm = rm.permute(0, 2, 3, 1).contiguous()
    rm = rm.view(rm.size(0), rm.size(1), rm.size(2), -1, 7)
    targets = targets.view(targets.size(0), targets.size(1), targets.size(2), -1, 7)
    pos_equal_one_for_reg = pos_equal_one.unsqueeze(pos_equal_one.dim()).expand(-1, -1, -1, -1, 7)
    rm_pos = rm * pos_equal_one_for_reg
    targets_pos = targets * pos_equal_one_for_reg
    cls_pos_loss = -pos_equal_one * torch.log(p_pos + 1e-06)
    cls_pos_loss = cls_pos_loss.sum() / (pos_equal_one.sum() + 1e-06)
    cls_neg_loss = -neg_equal_one * torch.log(1 - p_pos + 1e-06)
    cls_neg_loss = cls_neg_loss.sum() / (neg_equal_one.sum() + 1e-06)
    reg_loss = self.smoothl1loss(rm_pos, targets_pos)
    reg_loss = reg_loss / (pos_equal_one.sum() + 1e-06)
    conf_loss = self.alpha * cls_pos_loss + self.beta * cls_neg_loss
    total_loss = self.reg_coe * reg_loss + conf_loss
    self.loss_dict.update({'total_loss': total_loss, 'reg_loss': reg_loss, 'conf_loss': conf_loss})
    return total_loss

class PointPillarLoss(nn.Module):

    def __init__(self, args):
        super(PointPillarLoss, self).__init__()
        self.reg_loss_func = WeightedSmoothL1Loss()
        self.alpha = 0.25
        self.gamma = 2.0
        self.cls_weight = args['cls_weight']
        self.reg_coe = args['reg']
        self.loss_dict = {}

    def forward(self, output_dict, target_dict):
        """
        Parameters
        ----------
        output_dict : dict
        target_dict : dict
        """
        rm = output_dict['rm']
        psm = output_dict['psm']
        targets = target_dict['targets']
        cls_preds = psm.permute(0, 2, 3, 1).contiguous()
        box_cls_labels = target_dict['pos_equal_one']
        box_cls_labels = box_cls_labels.view(psm.shape[0], -1).contiguous()
        positives = box_cls_labels > 0
        negatives = box_cls_labels == 0
        negative_cls_weights = negatives * 1.0
        cls_weights = (negative_cls_weights + 1.0 * positives).float()
        reg_weights = positives.float()
        pos_normalizer = positives.sum(1, keepdim=True).float()
        reg_weights /= torch.clamp(pos_normalizer, min=1.0)
        cls_weights /= torch.clamp(pos_normalizer, min=1.0)
        cls_targets = box_cls_labels
        cls_targets = cls_targets.unsqueeze(dim=-1)
        cls_targets = cls_targets.squeeze(dim=-1)
        one_hot_targets = torch.zeros(*list(cls_targets.shape), 2, dtype=cls_preds.dtype, device=cls_targets.device)
        one_hot_targets.scatter_(-1, cls_targets.unsqueeze(dim=-1).long(), 1.0)
        cls_preds = cls_preds.view(psm.shape[0], -1, 1)
        one_hot_targets = one_hot_targets[..., 1:]
        cls_loss_src = self.cls_loss_func(cls_preds, one_hot_targets, weights=cls_weights)
        cls_loss = cls_loss_src.sum() / psm.shape[0]
        conf_loss = cls_loss * self.cls_weight
        rm = rm.permute(0, 2, 3, 1).contiguous()
        rm = rm.view(rm.size(0), -1, 7)
        targets = targets.view(targets.size(0), -1, 7)
        box_preds_sin, reg_targets_sin = self.add_sin_difference(rm, targets)
        loc_loss_src = self.reg_loss_func(box_preds_sin, reg_targets_sin, weights=reg_weights)
        reg_loss = loc_loss_src.sum() / rm.shape[0]
        reg_loss *= self.reg_coe
        total_loss = reg_loss + conf_loss
        self.loss_dict.update({'total_loss': total_loss, 'reg_loss': reg_loss, 'conf_loss': conf_loss})
        return total_loss

    def cls_loss_func(self, input: torch.Tensor, target: torch.Tensor, weights: torch.Tensor):
        """
        Args:
            input: (B, #anchors, #classes) float tensor.
                Predicted logits for each class
            target: (B, #anchors, #classes) float tensor.
                One-hot encoded classification targets
            weights: (B, #anchors) float tensor.
                Anchor-wise weights.

        Returns:
            weighted_loss: (B, #anchors, #classes) float tensor after weighting.
        """
        pred_sigmoid = torch.sigmoid(input)
        alpha_weight = target * self.alpha + (1 - target) * (1 - self.alpha)
        pt = target * (1.0 - pred_sigmoid) + (1.0 - target) * pred_sigmoid
        focal_weight = alpha_weight * torch.pow(pt, self.gamma)
        bce_loss = self.sigmoid_cross_entropy_with_logits(input, target)
        loss = focal_weight * bce_loss
        if weights.shape.__len__() == 2 or (weights.shape.__len__() == 1 and target.shape.__len__() == 2):
            weights = weights.unsqueeze(-1)
        assert weights.shape.__len__() == loss.shape.__len__()
        return loss * weights

    @staticmethod
    def sigmoid_cross_entropy_with_logits(input: torch.Tensor, target: torch.Tensor):
        """ PyTorch Implementation for tf.nn.sigmoid_cross_entropy_with_logits:
            max(x, 0) - x * z + log(1 + exp(-abs(x))) in
            https://www.tensorflow.org/api_docs/python/tf/nn/sigmoid_cross_entropy_with_logits

        Args:
            input: (B, #anchors, #classes) float tensor.
                Predicted logits for each class
            target: (B, #anchors, #classes) float tensor.
                One-hot encoded classification targets

        Returns:
            loss: (B, #anchors, #classes) float tensor.
                Sigmoid cross entropy loss without reduction
        """
        loss = torch.clamp(input, min=0) - input * target + torch.log1p(torch.exp(-torch.abs(input)))
        return loss

    @staticmethod
    def add_sin_difference(boxes1, boxes2, dim=6):
        assert dim != -1
        rad_pred_encoding = torch.sin(boxes1[..., dim:dim + 1]) * torch.cos(boxes2[..., dim:dim + 1])
        rad_tg_encoding = torch.cos(boxes1[..., dim:dim + 1]) * torch.sin(boxes2[..., dim:dim + 1])
        boxes1 = torch.cat([boxes1[..., :dim], rad_pred_encoding, boxes1[..., dim + 1:]], dim=-1)
        boxes2 = torch.cat([boxes2[..., :dim], rad_tg_encoding, boxes2[..., dim + 1:]], dim=-1)
        return (boxes1, boxes2)

    def logging(self, epoch, batch_id, batch_len, writer, pbar=None):
        """
        Print out  the loss function for current iteration.

        Parameters
        ----------
        epoch : int
            Current epoch for training.
        batch_id : int
            The current batch.
        batch_len : int
            Total batch length in one iteration of training,
        writer : SummaryWriter
            Used to visualize on tensorboard
        """
        total_loss = self.loss_dict['total_loss']
        reg_loss = self.loss_dict['reg_loss']
        conf_loss = self.loss_dict['conf_loss']
        if pbar is None:
            print('[epoch %d][%d/%d], || Loss: %.4f || Conf Loss: %.4f || Loc Loss: %.4f' % (epoch, batch_id + 1, batch_len, total_loss.item(), conf_loss.item(), reg_loss.item()))
        else:
            pbar.set_description('[epoch %d][%d/%d], || Loss: %.4f || Conf Loss: %.4f || Loc Loss: %.4f' % (epoch, batch_id + 1, batch_len, total_loss.item(), conf_loss.item(), reg_loss.item()))
        writer.add_scalar('Regression_loss', reg_loss.item(), epoch * batch_len + batch_id)
        writer.add_scalar('Confidence_loss', conf_loss.item(), epoch * batch_len + batch_id)

def forward(self, output_dict, target_dict):
    """
        Parameters
        ----------
        output_dict : dict
        target_dict : dict
        """
    rm = output_dict['rm']
    psm = output_dict['psm']
    targets = target_dict['targets']
    cls_preds = psm.permute(0, 2, 3, 1).contiguous()
    box_cls_labels = target_dict['pos_equal_one']
    box_cls_labels = box_cls_labels.view(psm.shape[0], -1).contiguous()
    positives = box_cls_labels > 0
    negatives = box_cls_labels == 0
    negative_cls_weights = negatives * 1.0
    cls_weights = (negative_cls_weights + 1.0 * positives).float()
    reg_weights = positives.float()
    pos_normalizer = positives.sum(1, keepdim=True).float()
    reg_weights /= torch.clamp(pos_normalizer, min=1.0)
    cls_weights /= torch.clamp(pos_normalizer, min=1.0)
    cls_targets = box_cls_labels
    cls_targets = cls_targets.unsqueeze(dim=-1)
    cls_targets = cls_targets.squeeze(dim=-1)
    one_hot_targets = torch.zeros(*list(cls_targets.shape), 2, dtype=cls_preds.dtype, device=cls_targets.device)
    one_hot_targets.scatter_(-1, cls_targets.unsqueeze(dim=-1).long(), 1.0)
    cls_preds = cls_preds.view(psm.shape[0], -1, 1)
    one_hot_targets = one_hot_targets[..., 1:]
    cls_loss_src = self.cls_loss_func(cls_preds, one_hot_targets, weights=cls_weights)
    cls_loss = cls_loss_src.sum() / psm.shape[0]
    conf_loss = cls_loss * self.cls_weight
    rm = rm.permute(0, 2, 3, 1).contiguous()
    rm = rm.view(rm.size(0), -1, 7)
    targets = targets.view(targets.size(0), -1, 7)
    box_preds_sin, reg_targets_sin = self.add_sin_difference(rm, targets)
    loc_loss_src = self.reg_loss_func(box_preds_sin, reg_targets_sin, weights=reg_weights)
    reg_loss = loc_loss_src.sum() / rm.shape[0]
    reg_loss *= self.reg_coe
    total_loss = reg_loss + conf_loss
    self.loss_dict.update({'total_loss': total_loss, 'reg_loss': reg_loss, 'conf_loss': conf_loss})
    return total_loss

def cls_loss_func(self, input: torch.Tensor, target: torch.Tensor, weights: torch.Tensor):
    """
        Args:
            input: (B, #anchors, #classes) float tensor.
                Predicted logits for each class
            target: (B, #anchors, #classes) float tensor.
                One-hot encoded classification targets
            weights: (B, #anchors) float tensor.
                Anchor-wise weights.

        Returns:
            weighted_loss: (B, #anchors, #classes) float tensor after weighting.
        """
    pred_sigmoid = torch.sigmoid(input)
    alpha_weight = target * self.alpha + (1 - target) * (1 - self.alpha)
    pt = target * (1.0 - pred_sigmoid) + (1.0 - target) * pred_sigmoid
    focal_weight = alpha_weight * torch.pow(pt, self.gamma)
    bce_loss = self.sigmoid_cross_entropy_with_logits(input, target)
    loss = focal_weight * bce_loss
    if weights.shape.__len__() == 2 or (weights.shape.__len__() == 1 and target.shape.__len__() == 2):
        weights = weights.unsqueeze(-1)
    assert weights.shape.__len__() == loss.shape.__len__()
    return loss * weights

@staticmethod
def sigmoid_cross_entropy_with_logits(input: torch.Tensor, target: torch.Tensor):
    """ PyTorch Implementation for tf.nn.sigmoid_cross_entropy_with_logits:
            max(x, 0) - x * z + log(1 + exp(-abs(x))) in
            https://www.tensorflow.org/api_docs/python/tf/nn/sigmoid_cross_entropy_with_logits

        Args:
            input: (B, #anchors, #classes) float tensor.
                Predicted logits for each class
            target: (B, #anchors, #classes) float tensor.
                One-hot encoded classification targets

        Returns:
            loss: (B, #anchors, #classes) float tensor.
                Sigmoid cross entropy loss without reduction
        """
    loss = torch.clamp(input, min=0) - input * target + torch.log1p(torch.exp(-torch.abs(input)))
    return loss

