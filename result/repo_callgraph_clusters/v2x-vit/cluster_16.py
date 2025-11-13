# Cluster 16

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

def __init__(self, anchor_params, train):
    super(BevPostprocessor, self).__init__(anchor_params, train)
    self.geometry_param = anchor_params['geometry_param']
    self.target_mean = np.array([0.008, 0.001, 0.202, 0.2, 0.43, 1.368])
    self.target_std_dev = np.array([0.866, 0.5, 0.954, 0.668, 0.09, 0.111])

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

def __init__(self, anchor_params, train):
    super(VoxelPostprocessor, self).__init__(anchor_params, train)
    self.anchor_num = self.params['anchor_args']['num']

class EarlyFusionVisDataset(basedataset.BaseDataset):

    def __init__(self, params, visualize, train=True):
        super(EarlyFusionVisDataset, self).__init__(params, visualize, train)
        self.pre_processor = build_preprocessor(params['preprocess'], train)
        self.post_processor = build_postprocessor(params['postprocess'], train)

    def __getitem__(self, idx):
        base_data_dict = self.retrieve_base_data(idx)
        processed_data_dict = OrderedDict()
        processed_data_dict['ego'] = {}
        ego_id = -1
        ego_lidar_pose = []
        for cav_id, cav_content in base_data_dict.items():
            if cav_content['ego']:
                ego_id = cav_id
                ego_lidar_pose = cav_content['params']['lidar_pose']
                break
        assert ego_id != -1
        assert len(ego_lidar_pose) > 0
        projected_lidar_stack = []
        object_stack = []
        object_id_stack = []
        for cav_id, selected_cav_base in base_data_dict.items():
            selected_cav_processed = self.get_item_single_car(selected_cav_base, ego_lidar_pose)
            projected_lidar_stack.append(selected_cav_processed['projected_lidar'])
            object_stack.append(selected_cav_processed['object_bbx_center'])
            object_id_stack += selected_cav_processed['object_ids']
        unique_indices = [object_id_stack.index(x) for x in set(object_id_stack)]
        object_stack = np.vstack(object_stack)
        object_stack = object_stack[unique_indices]
        object_bbx_center = np.zeros((self.params['postprocess']['max_num'], 7))
        mask = np.zeros(self.params['postprocess']['max_num'])
        object_bbx_center[:object_stack.shape[0], :] = object_stack
        mask[:object_stack.shape[0]] = 1
        projected_lidar_stack = np.vstack(projected_lidar_stack)
        projected_lidar_stack, object_bbx_center, mask = self.augment(projected_lidar_stack, object_bbx_center, mask)
        projected_lidar_stack = mask_points_by_range(projected_lidar_stack, self.params['preprocess']['cav_lidar_range'])
        object_bbx_center_valid = object_bbx_center[mask == 1]
        object_bbx_center_valid = box_utils.mask_boxes_outside_range_numpy(object_bbx_center_valid, self.params['preprocess']['cav_lidar_range'], self.params['postprocess']['order'])
        mask[object_bbx_center_valid.shape[0]:] = 0
        object_bbx_center[:object_bbx_center_valid.shape[0]] = object_bbx_center_valid
        object_bbx_center[object_bbx_center_valid.shape[0]:] = 0
        processed_data_dict['ego'].update({'object_bbx_center': object_bbx_center, 'object_bbx_mask': mask, 'object_ids': [object_id_stack[i] for i in unique_indices], 'origin_lidar': projected_lidar_stack})
        return processed_data_dict

    def get_item_single_car(self, selected_cav_base, ego_pose):
        """
        Project the lidar and bbx to ego space first, and then do clipping.

        Parameters
        ----------
        selected_cav_base : dict
            The dictionary contains a single CAV's raw information.
        ego_pose : list
            The ego vehicle lidar pose under world coordinate.

        Returns
        -------
        selected_cav_processed : dict
            The dictionary contains the cav's processed information.
        """
        selected_cav_processed = {}
        transformation_matrix = selected_cav_base['params']['transformation_matrix']
        object_bbx_center, object_bbx_mask, object_ids = self.post_processor.generate_object_center([selected_cav_base], ego_pose)
        lidar_np = selected_cav_base['lidar_np']
        lidar_np = shuffle_points(lidar_np)
        lidar_np = mask_ego_points(lidar_np)
        lidar_np[:, :3] = box_utils.project_points_by_matrix_torch(lidar_np[:, :3], transformation_matrix)
        selected_cav_processed.update({'object_bbx_center': object_bbx_center[object_bbx_mask == 1], 'object_ids': object_ids, 'projected_lidar': lidar_np})
        return selected_cav_processed

    def collate_batch_train(self, batch):
        """
        Customized collate function for pytorch dataloader during training
        for late fusion dataset.

        Parameters
        ----------
        batch : dict

        Returns
        -------
        batch : dict
            Reformatted batch.
        """
        output_dict = {'ego': {}}
        object_bbx_center = []
        object_bbx_mask = []
        origin_lidar = []
        for i in range(len(batch)):
            ego_dict = batch[i]['ego']
            object_bbx_center.append(ego_dict['object_bbx_center'])
            object_bbx_mask.append(ego_dict['object_bbx_mask'])
            origin_lidar.append(ego_dict['origin_lidar'])
        object_bbx_center = torch.from_numpy(np.array(object_bbx_center))
        object_bbx_mask = torch.from_numpy(np.array(object_bbx_mask))
        output_dict['ego'].update({'object_bbx_center': object_bbx_center, 'object_bbx_mask': object_bbx_mask})
        origin_lidar = np.array(downsample_lidar_minimum(pcd_np_list=origin_lidar))
        origin_lidar = torch.from_numpy(origin_lidar)
        output_dict['ego'].update({'origin_lidar': origin_lidar})
        return output_dict

def __init__(self, params, visualize, train=True):
    super(EarlyFusionVisDataset, self).__init__(params, visualize, train)
    self.pre_processor = build_preprocessor(params['preprocess'], train)
    self.post_processor = build_postprocessor(params['postprocess'], train)

class IntermediateFusionDataset(basedataset.BaseDataset):

    def __init__(self, params, visualize, train=True):
        super(IntermediateFusionDataset, self).__init__(params, visualize, train)
        self.cur_ego_pose_flag = params['fusion']['args']['cur_ego_pose_flag']
        self.pre_processor = build_preprocessor(params['preprocess'], train)
        self.post_processor = post_processor.build_postprocessor(params['postprocess'], train)

    def __getitem__(self, idx):
        base_data_dict = self.retrieve_base_data(idx, cur_ego_pose_flag=self.cur_ego_pose_flag)
        processed_data_dict = OrderedDict()
        processed_data_dict['ego'] = {}
        ego_id = -1
        ego_lidar_pose = []
        for cav_id, cav_content in base_data_dict.items():
            if cav_content['ego']:
                ego_id = cav_id
                ego_lidar_pose = cav_content['params']['lidar_pose']
                break
        assert cav_id == list(base_data_dict.keys())[0], 'The first element in the OrderedDict must be ego'
        assert ego_id != -1
        assert len(ego_lidar_pose) > 0
        pairwise_t_matrix = self.get_pairwise_transformation(base_data_dict, self.params['train_params']['max_cav'])
        processed_features = []
        object_stack = []
        object_id_stack = []
        velocity = []
        time_delay = []
        infra = []
        spatial_correction_matrix = []
        if self.visualize:
            projected_lidar_stack = []
        for cav_id, selected_cav_base in base_data_dict.items():
            distance = math.sqrt((selected_cav_base['params']['lidar_pose'][0] - ego_lidar_pose[0]) ** 2 + (selected_cav_base['params']['lidar_pose'][1] - ego_lidar_pose[1]) ** 2)
            if distance > v2xvit.data_utils.datasets.COM_RANGE:
                continue
            selected_cav_processed, void_lidar = self.get_item_single_car(selected_cav_base, ego_lidar_pose)
            if void_lidar:
                continue
            object_stack.append(selected_cav_processed['object_bbx_center'])
            object_id_stack += selected_cav_processed['object_ids']
            processed_features.append(selected_cav_processed['processed_features'])
            velocity.append(selected_cav_processed['velocity'])
            time_delay.append(float(selected_cav_base['time_delay']))
            spatial_correction_matrix.append(selected_cav_base['params']['spatial_correction_matrix'])
            infra.append(1 if int(cav_id) < 0 else 0)
            if self.visualize:
                projected_lidar_stack.append(selected_cav_processed['projected_lidar'])
        unique_indices = [object_id_stack.index(x) for x in set(object_id_stack)]
        object_stack = np.vstack(object_stack)
        object_stack = object_stack[unique_indices]
        object_bbx_center = np.zeros((self.params['postprocess']['max_num'], 7))
        mask = np.zeros(self.params['postprocess']['max_num'])
        object_bbx_center[:object_stack.shape[0], :] = object_stack
        mask[:object_stack.shape[0]] = 1
        cav_num = len(processed_features)
        merged_feature_dict = self.merge_features_to_dict(processed_features)
        anchor_box = self.post_processor.generate_anchor_box()
        label_dict = self.post_processor.generate_label(gt_box_center=object_bbx_center, anchors=anchor_box, mask=mask)
        velocity = velocity + (self.max_cav - len(velocity)) * [0.0]
        time_delay = time_delay + (self.max_cav - len(time_delay)) * [0.0]
        infra = infra + (self.max_cav - len(infra)) * [0.0]
        spatial_correction_matrix = np.stack(spatial_correction_matrix)
        padding_eye = np.tile(np.eye(4)[None], (self.max_cav - len(spatial_correction_matrix), 1, 1))
        spatial_correction_matrix = np.concatenate([spatial_correction_matrix, padding_eye], axis=0)
        processed_data_dict['ego'].update({'object_bbx_center': object_bbx_center, 'object_bbx_mask': mask, 'object_ids': [object_id_stack[i] for i in unique_indices], 'anchor_box': anchor_box, 'processed_lidar': merged_feature_dict, 'label_dict': label_dict, 'cav_num': cav_num, 'velocity': velocity, 'time_delay': time_delay, 'infra': infra, 'spatial_correction_matrix': spatial_correction_matrix, 'pairwise_t_matrix': pairwise_t_matrix})
        if self.visualize:
            processed_data_dict['ego'].update({'origin_lidar': np.vstack(projected_lidar_stack)})
        return processed_data_dict

    @staticmethod
    def get_pairwise_transformation(base_data_dict, max_cav):
        """
        Get pair-wise transformation matrix across different agents.
        This is only used for v2vnet and disconet. Currently we set
        this as identity matrix as the pointcloud is projected to
        ego vehicle first.

        Parameters
        ----------
        base_data_dict : dict
            Key : cav id, item: transformation matrix to ego, lidar points.

        max_cav : int
            The maximum number of cav, default 5

        Return
        ------
        pairwise_t_matrix : np.array
            The pairwise transformation matrix across each cav.
            shape: (L, L, 4, 4)
        """
        pairwise_t_matrix = np.zeros((max_cav, max_cav, 4, 4))
        pairwise_t_matrix[:, :] = np.identity(4)
        return pairwise_t_matrix

    def get_item_single_car(self, selected_cav_base, ego_pose):
        """
        Project the lidar and bbx to ego space first, and then do clipping.

        Parameters
        ----------
        selected_cav_base : dict
            The dictionary contains a single CAV's raw information.
        ego_pose : list
            The ego vehicle lidar pose under world coordinate.

        Returns
        -------
        selected_cav_processed : dict
            The dictionary contains the cav's processed information.
        """
        selected_cav_processed = {}
        transformation_matrix = selected_cav_base['params']['transformation_matrix']
        object_bbx_center, object_bbx_mask, object_ids = self.post_processor.generate_object_center([selected_cav_base], ego_pose)
        lidar_np = selected_cav_base['lidar_np']
        lidar_np = shuffle_points(lidar_np)
        lidar_np = mask_ego_points(lidar_np)
        lidar_np[:, :3] = box_utils.project_points_by_matrix_torch(lidar_np[:, :3], transformation_matrix)
        lidar_np = mask_points_by_range(lidar_np, self.params['preprocess']['cav_lidar_range'])
        void_lidar = True if lidar_np.shape[0] < 1 else False
        processed_lidar = self.pre_processor.preprocess(lidar_np)
        velocity = selected_cav_base['params']['ego_speed']
        velocity = velocity / 30
        selected_cav_processed.update({'object_bbx_center': object_bbx_center[object_bbx_mask == 1], 'object_ids': object_ids, 'projected_lidar': lidar_np, 'processed_features': processed_lidar, 'velocity': velocity})
        return (selected_cav_processed, void_lidar)

    @staticmethod
    def merge_features_to_dict(processed_feature_list):
        """
        Merge the preprocessed features from different cavs to the same
        dictionary.

        Parameters
        ----------
        processed_feature_list : list
            A list of dictionary containing all processed features from
            different cavs.

        Returns
        -------
        merged_feature_dict: dict
            key: feature names, value: list of features.
        """
        merged_feature_dict = OrderedDict()
        for i in range(len(processed_feature_list)):
            for feature_name, feature in processed_feature_list[i].items():
                if feature_name not in merged_feature_dict:
                    merged_feature_dict[feature_name] = []
                if isinstance(feature, list):
                    merged_feature_dict[feature_name] += feature
                else:
                    merged_feature_dict[feature_name].append(feature)
        return merged_feature_dict

    def collate_batch_train(self, batch):
        output_dict = {'ego': {}}
        object_bbx_center = []
        object_bbx_mask = []
        object_ids = []
        processed_lidar_list = []
        record_len = []
        label_dict_list = []
        velocity = []
        time_delay = []
        infra = []
        pairwise_t_matrix_list = []
        spatial_correction_matrix_list = []
        if self.visualize:
            origin_lidar = []
        for i in range(len(batch)):
            ego_dict = batch[i]['ego']
            object_bbx_center.append(ego_dict['object_bbx_center'])
            object_bbx_mask.append(ego_dict['object_bbx_mask'])
            object_ids.append(ego_dict['object_ids'])
            processed_lidar_list.append(ego_dict['processed_lidar'])
            record_len.append(ego_dict['cav_num'])
            label_dict_list.append(ego_dict['label_dict'])
            velocity.append(ego_dict['velocity'])
            time_delay.append(ego_dict['time_delay'])
            infra.append(ego_dict['infra'])
            spatial_correction_matrix_list.append(ego_dict['spatial_correction_matrix'])
            pairwise_t_matrix_list.append(ego_dict['pairwise_t_matrix'])
            if self.visualize:
                origin_lidar.append(ego_dict['origin_lidar'])
        object_bbx_center = torch.from_numpy(np.array(object_bbx_center))
        object_bbx_mask = torch.from_numpy(np.array(object_bbx_mask))
        merged_feature_dict = self.merge_features_to_dict(processed_lidar_list)
        processed_lidar_torch_dict = self.pre_processor.collate_batch(merged_feature_dict)
        record_len = torch.from_numpy(np.array(record_len, dtype=int))
        label_torch_dict = self.post_processor.collate_batch(label_dict_list)
        velocity = torch.from_numpy(np.array(velocity))
        time_delay = torch.from_numpy(np.array(time_delay))
        infra = torch.from_numpy(np.array(infra))
        spatial_correction_matrix_list = torch.from_numpy(np.array(spatial_correction_matrix_list))
        prior_encoding = torch.stack([velocity, time_delay, infra], dim=-1).float()
        pairwise_t_matrix = torch.from_numpy(np.array(pairwise_t_matrix_list))
        output_dict['ego'].update({'object_bbx_center': object_bbx_center, 'object_bbx_mask': object_bbx_mask, 'processed_lidar': processed_lidar_torch_dict, 'record_len': record_len, 'label_dict': label_torch_dict, 'object_ids': object_ids[0], 'prior_encoding': prior_encoding, 'spatial_correction_matrix': spatial_correction_matrix_list, 'pairwise_t_matrix': pairwise_t_matrix})
        if self.visualize:
            origin_lidar = np.array(downsample_lidar_minimum(pcd_np_list=origin_lidar))
            origin_lidar = torch.from_numpy(origin_lidar)
            output_dict['ego'].update({'origin_lidar': origin_lidar})
        return output_dict

    def collate_batch_test(self, batch):
        assert len(batch) <= 1, 'Batch size 1 is required during testing!'
        output_dict = self.collate_batch_train(batch)
        if batch[0]['ego']['anchor_box'] is not None:
            output_dict['ego'].update({'anchor_box': torch.from_numpy(np.array(batch[0]['ego']['anchor_box']))})
        transformation_matrix_torch = torch.from_numpy(np.identity(4)).float()
        output_dict['ego'].update({'transformation_matrix': transformation_matrix_torch})
        return output_dict

    def post_process(self, data_dict, output_dict):
        """
        Process the outputs of the model to 2D/3D bounding box.

        Parameters
        ----------
        data_dict : dict
            The dictionary containing the origin input data of model.

        output_dict :dict
            The dictionary containing the output of the model.

        Returns
        -------
        pred_box_tensor : torch.Tensor
            The tensor of prediction bounding box after NMS.
        gt_box_tensor : torch.Tensor
            The tensor of gt bounding box.
        """
        pred_box_tensor, pred_score = self.post_processor.post_process(data_dict, output_dict)
        gt_box_tensor = self.post_processor.generate_gt_bbx(data_dict)
        return (pred_box_tensor, pred_score, gt_box_tensor)

def __init__(self, params, visualize, train=True):
    super(IntermediateFusionDataset, self).__init__(params, visualize, train)
    self.cur_ego_pose_flag = params['fusion']['args']['cur_ego_pose_flag']
    self.pre_processor = build_preprocessor(params['preprocess'], train)
    self.post_processor = post_processor.build_postprocessor(params['postprocess'], train)

class EarlyFusionDataset(basedataset.BaseDataset):

    def __init__(self, params, visualize, train=True):
        super(EarlyFusionDataset, self).__init__(params, visualize, train)
        self.pre_processor = build_preprocessor(params['preprocess'], train)
        self.post_processor = build_postprocessor(params['postprocess'], train)

    def __getitem__(self, idx):
        base_data_dict = self.retrieve_base_data(idx, cur_ego_pose_flag=True)
        processed_data_dict = OrderedDict()
        processed_data_dict['ego'] = {}
        ego_id = -1
        ego_lidar_pose = []
        for cav_id, cav_content in base_data_dict.items():
            if cav_content['ego']:
                ego_id = cav_id
                ego_lidar_pose = cav_content['params']['lidar_pose']
                break
        assert ego_id != -1
        assert len(ego_lidar_pose) > 0
        projected_lidar_stack = []
        object_stack = []
        object_id_stack = []
        for cav_id, selected_cav_base in base_data_dict.items():
            distance = math.sqrt((selected_cav_base['params']['lidar_pose'][0] - ego_lidar_pose[0]) ** 2 + (selected_cav_base['params']['lidar_pose'][1] - ego_lidar_pose[1]) ** 2)
            if distance > v2xvit.data_utils.datasets.COM_RANGE:
                continue
            selected_cav_processed = self.get_item_single_car(selected_cav_base, ego_lidar_pose)
            projected_lidar_stack.append(selected_cav_processed['projected_lidar'])
            object_stack.append(selected_cav_processed['object_bbx_center'])
            object_id_stack += selected_cav_processed['object_ids']
        unique_indices = [object_id_stack.index(x) for x in set(object_id_stack)]
        object_stack = np.vstack(object_stack)
        object_stack = object_stack[unique_indices]
        object_bbx_center = np.zeros((self.params['postprocess']['max_num'], 7))
        mask = np.zeros(self.params['postprocess']['max_num'])
        object_bbx_center[:object_stack.shape[0], :] = object_stack
        mask[:object_stack.shape[0]] = 1
        projected_lidar_stack = np.vstack(projected_lidar_stack)
        projected_lidar_stack, object_bbx_center, mask = self.augment(projected_lidar_stack, object_bbx_center, mask)
        projected_lidar_stack = mask_points_by_range(projected_lidar_stack, self.params['preprocess']['cav_lidar_range'])
        object_bbx_center_valid = object_bbx_center[mask == 1]
        object_bbx_center_valid = box_utils.mask_boxes_outside_range_numpy(object_bbx_center_valid, self.params['preprocess']['cav_lidar_range'], self.params['postprocess']['order'])
        mask[object_bbx_center_valid.shape[0]:] = 0
        object_bbx_center[:object_bbx_center_valid.shape[0]] = object_bbx_center_valid
        object_bbx_center[object_bbx_center_valid.shape[0]:] = 0
        lidar_dict = self.pre_processor.preprocess(projected_lidar_stack)
        anchor_box = self.post_processor.generate_anchor_box()
        label_dict = self.post_processor.generate_label(gt_box_center=object_bbx_center, anchors=anchor_box, mask=mask)
        processed_data_dict['ego'].update({'object_bbx_center': object_bbx_center, 'object_bbx_mask': mask, 'object_ids': [object_id_stack[i] for i in unique_indices], 'anchor_box': anchor_box, 'processed_lidar': lidar_dict, 'label_dict': label_dict})
        if self.visualize:
            processed_data_dict['ego'].update({'origin_lidar': projected_lidar_stack})
        return processed_data_dict

    def get_item_single_car(self, selected_cav_base, ego_pose):
        """
        Project the lidar and bbx to ego space first, and then do clipping.

        Parameters
        ----------
        selected_cav_base : dict
            The dictionary contains a single CAV's raw information.
        ego_pose : list
            The ego vehicle lidar pose under world coordinate.

        Returns
        -------
        selected_cav_processed : dict
            The dictionary contains the cav's processed information.
        """
        selected_cav_processed = {}
        transformation_matrix = selected_cav_base['params']['transformation_matrix']
        object_bbx_center, object_bbx_mask, object_ids = self.post_processor.generate_object_center([selected_cav_base], ego_pose)
        lidar_np = selected_cav_base['lidar_np']
        lidar_np = shuffle_points(lidar_np)
        lidar_np = mask_ego_points(lidar_np)
        lidar_np[:, :3] = box_utils.project_points_by_matrix_torch(lidar_np[:, :3], transformation_matrix)
        selected_cav_processed.update({'object_bbx_center': object_bbx_center[object_bbx_mask == 1], 'object_ids': object_ids, 'projected_lidar': lidar_np})
        return selected_cav_processed

    def collate_batch_test(self, batch):
        """
        Customized collate function for pytorch dataloader during testing
        for late fusion dataset.

        Parameters
        ----------
        batch : dict

        Returns
        -------
        batch : dict
            Reformatted batch.
        """
        assert len(batch) <= 1, 'Batch size 1 is required during testing!'
        batch = batch[0]
        output_dict = {}
        for cav_id, cav_content in batch.items():
            output_dict.update({cav_id: {}})
            object_bbx_center = torch.from_numpy(np.array([cav_content['object_bbx_center']]))
            object_bbx_mask = torch.from_numpy(np.array([cav_content['object_bbx_mask']]))
            object_ids = cav_content['object_ids']
            if cav_content['anchor_box'] is not None:
                output_dict[cav_id].update({'anchor_box': torch.from_numpy(np.array(cav_content['anchor_box']))})
            if self.visualize:
                origin_lidar = [cav_content['origin_lidar']]
            processed_lidar_torch_dict = self.pre_processor.collate_batch([cav_content['processed_lidar']])
            label_torch_dict = self.post_processor.collate_batch([cav_content['label_dict']])
            transformation_matrix_torch = torch.from_numpy(np.identity(4)).float()
            output_dict[cav_id].update({'object_bbx_center': object_bbx_center, 'object_bbx_mask': object_bbx_mask, 'processed_lidar': processed_lidar_torch_dict, 'label_dict': label_torch_dict, 'object_ids': object_ids, 'transformation_matrix': transformation_matrix_torch})
            if self.visualize:
                origin_lidar = np.array(downsample_lidar_minimum(pcd_np_list=origin_lidar))
                origin_lidar = torch.from_numpy(origin_lidar)
                output_dict[cav_id].update({'origin_lidar': origin_lidar})
        return output_dict

    def post_process(self, data_dict, output_dict):
        """
        Process the outputs of the model to 2D/3D bounding box.

        Parameters
        ----------
        data_dict : dict
            The dictionary containing the origin input data of model.

        output_dict :dict
            The dictionary containing the output of the model.

        Returns
        -------
        pred_box_tensor : torch.Tensor
            The tensor of prediction bounding box after NMS.
        gt_box_tensor : torch.Tensor
            The tensor of gt bounding box.
        """
        pred_box_tensor, pred_score = self.post_processor.post_process(data_dict, output_dict)
        gt_box_tensor = self.post_processor.generate_gt_bbx(data_dict)
        return (pred_box_tensor, pred_score, gt_box_tensor)

def __init__(self, params, visualize, train=True):
    super(EarlyFusionDataset, self).__init__(params, visualize, train)
    self.pre_processor = build_preprocessor(params['preprocess'], train)
    self.post_processor = build_postprocessor(params['postprocess'], train)

class LateFusionDataset(basedataset.BaseDataset):

    def __init__(self, params, visualize, train=True):
        super(LateFusionDataset, self).__init__(params, visualize, train)
        self.pre_processor = build_preprocessor(params['preprocess'], train)
        self.post_processor = build_postprocessor(params['postprocess'], train)

    def __getitem__(self, idx):
        base_data_dict = self.retrieve_base_data(idx, cur_ego_pose_flag=True)
        if self.train:
            reformat_data_dict = self.get_item_train(base_data_dict)
        else:
            reformat_data_dict = self.get_item_test(base_data_dict)
        return reformat_data_dict

    def get_item_single_car(self, selected_cav_base):
        """
        Process a single CAV's information for the train/test pipeline.

        Parameters
        ----------
        selected_cav_base : dict
            The dictionary contains a single CAV's raw information.

        Returns
        -------
        selected_cav_processed : dict
            The dictionary contains the cav's processed information.
        """
        selected_cav_processed = {}
        lidar_np = selected_cav_base['lidar_np']
        lidar_np = shuffle_points(lidar_np)
        lidar_np = mask_points_by_range(lidar_np, self.params['preprocess']['cav_lidar_range'])
        lidar_np = mask_ego_points(lidar_np)
        object_bbx_center, object_bbx_mask, object_ids = self.post_processor.generate_object_center([selected_cav_base], selected_cav_base['params']['lidar_pose'])
        lidar_np, object_bbx_center, object_bbx_mask = self.augment(lidar_np, object_bbx_center, object_bbx_mask)
        if self.visualize:
            selected_cav_processed.update({'origin_lidar': lidar_np})
        lidar_dict = self.pre_processor.preprocess(lidar_np)
        selected_cav_processed.update({'processed_lidar': lidar_dict})
        anchor_box = self.post_processor.generate_anchor_box()
        selected_cav_processed.update({'anchor_box': anchor_box})
        selected_cav_processed.update({'object_bbx_center': object_bbx_center, 'object_bbx_mask': object_bbx_mask, 'object_ids': object_ids})
        label_dict = self.post_processor.generate_label(gt_box_center=object_bbx_center, anchors=anchor_box, mask=object_bbx_mask)
        selected_cav_processed.update({'label_dict': label_dict})
        return selected_cav_processed

    def get_item_train(self, base_data_dict):
        processed_data_dict = OrderedDict()
        if not self.visualize:
            selected_cav_id, selected_cav_base = random.choice(list(base_data_dict.items()))
        else:
            selected_cav_id, selected_cav_base = list(base_data_dict.items())[0]
        selected_cav_processed = self.get_item_single_car(selected_cav_base)
        processed_data_dict.update({'ego': selected_cav_processed})
        return processed_data_dict

    def get_item_test(self, base_data_dict):
        processed_data_dict = OrderedDict()
        ego_id = -1
        ego_lidar_pose = []
        for cav_id, cav_content in base_data_dict.items():
            if cav_content['ego']:
                ego_id = cav_id
                ego_lidar_pose = cav_content['params']['lidar_pose']
                break
        assert ego_id != -1
        assert len(ego_lidar_pose) > 0
        for cav_id, selected_cav_base in base_data_dict.items():
            distance = math.sqrt((selected_cav_base['params']['lidar_pose'][0] - ego_lidar_pose[0]) ** 2 + (selected_cav_base['params']['lidar_pose'][1] - ego_lidar_pose[1]) ** 2)
            if distance > v2xvit.data_utils.datasets.COM_RANGE:
                continue
            transformation_matrix = selected_cav_base['params']['transformation_matrix']
            gt_transformation_matrix = selected_cav_base['params']['gt_transformation_matrix']
            selected_cav_processed = self.get_item_single_car(selected_cav_base)
            selected_cav_processed.update({'transformation_matrix': transformation_matrix})
            selected_cav_processed.update({'gt_transformation_matrix': gt_transformation_matrix})
            update_cav = 'ego' if cav_id == ego_id else cav_id
            processed_data_dict.update({update_cav: selected_cav_processed})
        return processed_data_dict

    def collate_batch_test(self, batch):
        """
        Customized collate function for pytorch dataloader during testing
        for late fusion dataset.

        Parameters
        ----------
        batch : dict

        Returns
        -------
        batch : dict
            Reformatted batch.
        """
        assert len(batch) <= 1, 'Batch size 1 is required during testing!'
        batch = batch[0]
        output_dict = {}
        if self.visualize:
            projected_lidar_list = []
            origin_lidar = []
        for cav_id, cav_content in batch.items():
            output_dict.update({cav_id: {}})
            object_bbx_center = torch.from_numpy(np.array([cav_content['object_bbx_center']]))
            object_bbx_mask = torch.from_numpy(np.array([cav_content['object_bbx_mask']]))
            object_ids = cav_content['object_ids']
            if cav_content['anchor_box'] is not None:
                output_dict[cav_id].update({'anchor_box': torch.from_numpy(np.array(cav_content['anchor_box']))})
            if self.visualize:
                transformation_matrix = cav_content['transformation_matrix']
                origin_lidar = [cav_content['origin_lidar']]
                projected_lidar = cav_content['origin_lidar']
                projected_lidar[:, :3] = box_utils.project_points_by_matrix_torch(projected_lidar[:, :3], transformation_matrix)
                projected_lidar_list.append(projected_lidar)
            processed_lidar_torch_dict = self.pre_processor.collate_batch([cav_content['processed_lidar']])
            label_torch_dict = self.post_processor.collate_batch([cav_content['label_dict']])
            transformation_matrix_torch = torch.from_numpy(np.array(cav_content['transformation_matrix'])).float()
            gt_transformation_matrix_torch = torch.from_numpy(np.array(cav_content['gt_transformation_matrix'])).float()
            output_dict[cav_id].update({'object_bbx_center': object_bbx_center, 'object_bbx_mask': object_bbx_mask, 'processed_lidar': processed_lidar_torch_dict, 'label_dict': label_torch_dict, 'object_ids': object_ids, 'transformation_matrix': transformation_matrix_torch, 'gt_transformation_matrix': gt_transformation_matrix_torch})
            if self.visualize:
                origin_lidar = np.array(downsample_lidar_minimum(pcd_np_list=origin_lidar))
                origin_lidar = torch.from_numpy(origin_lidar)
                output_dict[cav_id].update({'origin_lidar': origin_lidar})
        if self.visualize:
            projected_lidar_stack = [torch.from_numpy(np.vstack(projected_lidar_list))]
            output_dict['ego'].update({'origin_lidar': projected_lidar_stack})
        return output_dict

    def post_process(self, data_dict, output_dict):
        """
        Process the outputs of the model to 2D/3D bounding box.

        Parameters
        ----------
        data_dict : dict
            The dictionary containing the origin input data of model.

        output_dict :dict
            The dictionary containing the output of the model.

        Returns
        -------
        pred_box_tensor : torch.Tensor
            The tensor of prediction bounding box after NMS.
        gt_box_tensor : torch.Tensor
            The tensor of gt bounding box.
        """
        pred_box_tensor, pred_score = self.post_processor.post_process(data_dict, output_dict)
        gt_box_tensor = self.post_processor.generate_gt_bbx(data_dict)
        return (pred_box_tensor, pred_score, gt_box_tensor)

def __init__(self, params, visualize, train=True):
    super(LateFusionDataset, self).__init__(params, visualize, train)
    self.pre_processor = build_preprocessor(params['preprocess'], train)
    self.post_processor = build_postprocessor(params['postprocess'], train)

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

def __init__(self, preprocess_params, train):
    super(BevPreprocessor, self).__init__(preprocess_params, train)
    self.lidar_range = self.params['cav_lidar_range']
    self.geometry_param = preprocess_params['geometry_param']

class VoxelPreprocessor(BasePreprocessor):

    def __init__(self, preprocess_params, train):
        super(VoxelPreprocessor, self).__init__(preprocess_params, train)
        self.lidar_range = self.params['cav_lidar_range']
        self.vw = self.params['args']['vw']
        self.vh = self.params['args']['vh']
        self.vd = self.params['args']['vd']
        self.T = self.params['args']['T']

    def preprocess(self, pcd_np):
        """
        Preprocess the lidar points by  voxelization.

        Parameters
        ----------
        pcd_np : np.ndarray
            The raw lidar.

        Returns
        -------
        data_dict : the structured output dictionary.
        """
        data_dict = {}
        voxel_coords = (pcd_np[:, :3] - np.floor(np.array([self.lidar_range[0], self.lidar_range[1], self.lidar_range[2]])) / (self.vw, self.vh, self.vd)).astype(np.int32)
        voxel_coords = voxel_coords[:, [2, 1, 0]]
        voxel_coords, inv_ind, voxel_counts = np.unique(voxel_coords, axis=0, return_inverse=True, return_counts=True)
        voxel_features = []
        for i in range(len(voxel_coords)):
            voxel = np.zeros((self.T, 7), dtype=np.float32)
            pts = pcd_np[inv_ind == i]
            if voxel_counts[i] > self.T:
                pts = pts[:self.T, :]
                voxel_counts[i] = self.T
            voxel[:pts.shape[0], :] = np.concatenate((pts, pts[:, :3] - np.mean(pts[:, :3], 0)), axis=1)
            voxel_features.append(voxel)
        data_dict['voxel_features'] = np.array(voxel_features)
        data_dict['voxel_coords'] = voxel_coords
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
        voxel_coords = []
        for i in range(len(batch)):
            voxel_features.append(batch[i]['voxel_features'])
            coords = batch[i]['voxel_coords']
            voxel_coords.append(np.pad(coords, ((0, 0), (1, 0)), mode='constant', constant_values=i))
        voxel_features = torch.from_numpy(np.concatenate(voxel_features))
        voxel_coords = torch.from_numpy(np.concatenate(voxel_coords))
        return {'voxel_features': voxel_features, 'voxel_coords': voxel_coords}

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
        coords = batch['voxel_coords']
        voxel_coords = []
        for i in range(len(coords)):
            voxel_coords.append(np.pad(coords[i], ((0, 0), (1, 0)), mode='constant', constant_values=i))
        voxel_coords = torch.from_numpy(np.concatenate(voxel_coords))
        return {'voxel_features': voxel_features, 'voxel_coords': voxel_coords}

def __init__(self, preprocess_params, train):
    super(VoxelPreprocessor, self).__init__(preprocess_params, train)
    self.lidar_range = self.params['cav_lidar_range']
    self.vw = self.params['args']['vw']
    self.vh = self.params['args']['vh']
    self.vd = self.params['args']['vd']
    self.T = self.params['args']['T']

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

class PointPillar(nn.Module):

    def __init__(self, args):
        super(PointPillar, self).__init__()
        self.pillar_vfe = PillarVFE(args['pillar_vfe'], num_point_features=4, voxel_size=args['voxel_size'], point_cloud_range=args['lidar_range'])
        self.scatter = PointPillarScatter(args['point_pillar_scatter'])
        self.backbone = BaseBEVBackbone(args['base_bev_backbone'], 64)
        self.shrink_flag = False
        if 'shrink_header' in args:
            self.shrink_flag = True
            self.shrink_conv = DownsampleConv(args['shrink_header'])
        self.cls_head = nn.Conv2d(args['cls_head_dim'], args['anchor_number'], kernel_size=1)
        self.reg_head = nn.Conv2d(args['cls_head_dim'], 7 * args['anchor_number'], kernel_size=1)

    def forward(self, data_dict):
        voxel_features = data_dict['processed_lidar']['voxel_features']
        voxel_coords = data_dict['processed_lidar']['voxel_coords']
        voxel_num_points = data_dict['processed_lidar']['voxel_num_points']
        batch_dict = {'voxel_features': voxel_features, 'voxel_coords': voxel_coords, 'voxel_num_points': voxel_num_points}
        batch_dict = self.pillar_vfe(batch_dict)
        batch_dict = self.scatter(batch_dict)
        batch_dict = self.backbone(batch_dict)
        spatial_features_2d = batch_dict['spatial_features_2d']
        if self.shrink_flag:
            spatial_features_2d = self.shrink_conv(spatial_features_2d)
        psm = self.cls_head(spatial_features_2d)
        rm = self.reg_head(spatial_features_2d)
        output_dict = {'psm': psm, 'rm': rm}
        return output_dict

def __init__(self, args):
    super(PointPillar, self).__init__()
    self.pillar_vfe = PillarVFE(args['pillar_vfe'], num_point_features=4, voxel_size=args['voxel_size'], point_cloud_range=args['lidar_range'])
    self.scatter = PointPillarScatter(args['point_pillar_scatter'])
    self.backbone = BaseBEVBackbone(args['base_bev_backbone'], 64)
    self.shrink_flag = False
    if 'shrink_header' in args:
        self.shrink_flag = True
        self.shrink_conv = DownsampleConv(args['shrink_header'])
    self.cls_head = nn.Conv2d(args['cls_head_dim'], args['anchor_number'], kernel_size=1)
    self.reg_head = nn.Conv2d(args['cls_head_dim'], 7 * args['anchor_number'], kernel_size=1)

class STTF(nn.Module):

    def __init__(self, args):
        super(STTF, self).__init__()
        self.discrete_ratio = args['voxel_size'][0]
        self.downsample_rate = args['downsample_rate']

    def forward(self, x, mask, spatial_correction_matrix):
        x = x.permute(0, 1, 4, 2, 3)
        dist_correction_matrix = get_discretized_transformation_matrix(spatial_correction_matrix, self.discrete_ratio, self.downsample_rate)
        B, L, C, H, W = x.shape
        T = get_transformation_matrix(dist_correction_matrix[:, 1:, :, :].reshape(-1, 2, 3), (H, W))
        cav_features = warp_affine(x[:, 1:, :, :, :].reshape(-1, C, H, W), T, (H, W))
        cav_features = cav_features.reshape(B, -1, C, H, W)
        x = torch.cat([x[:, 0, :, :, :].unsqueeze(1), cav_features], dim=1)
        x = x.permute(0, 1, 3, 4, 2)
        return x

def __init__(self, args):
    super(STTF, self).__init__()
    self.discrete_ratio = args['voxel_size'][0]
    self.downsample_rate = args['downsample_rate']

class RelTemporalEncoding(nn.Module):
    """
    Implement the Temporal Encoding (Sinusoid) function.
    """

    def __init__(self, n_hid, RTE_ratio, max_len=100, dropout=0.2):
        super(RelTemporalEncoding, self).__init__()
        position = torch.arange(0.0, max_len).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, n_hid, 2) * -(math.log(10000.0) / n_hid))
        emb = nn.Embedding(max_len, n_hid)
        emb.weight.data[:, 0::2] = torch.sin(position * div_term) / math.sqrt(n_hid)
        emb.weight.data[:, 1::2] = torch.cos(position * div_term) / math.sqrt(n_hid)
        emb.requires_grad = False
        self.RTE_ratio = RTE_ratio
        self.emb = emb
        self.lin = nn.Linear(n_hid, n_hid)

    def forward(self, x, t):
        return x + self.lin(self.emb(t * self.RTE_ratio)).unsqueeze(0).unsqueeze(1)

def __init__(self, n_hid, RTE_ratio, max_len=100, dropout=0.2):
    super(RelTemporalEncoding, self).__init__()
    position = torch.arange(0.0, max_len).unsqueeze(1)
    div_term = torch.exp(torch.arange(0, n_hid, 2) * -(math.log(10000.0) / n_hid))
    emb = nn.Embedding(max_len, n_hid)
    emb.weight.data[:, 0::2] = torch.sin(position * div_term) / math.sqrt(n_hid)
    emb.weight.data[:, 1::2] = torch.cos(position * div_term) / math.sqrt(n_hid)
    emb.requires_grad = False
    self.RTE_ratio = RTE_ratio
    self.emb = emb
    self.lin = nn.Linear(n_hid, n_hid)

class RTE(nn.Module):

    def __init__(self, dim, RTE_ratio=2):
        super(RTE, self).__init__()
        self.RTE_ratio = RTE_ratio
        self.emb = RelTemporalEncoding(dim, RTE_ratio=self.RTE_ratio)

    def forward(self, x, dts):
        rte_batch = []
        for b in range(x.shape[0]):
            rte_list = []
            for i in range(x.shape[1]):
                rte_list.append(self.emb(x[b, i, :, :, :], dts[b, i]).unsqueeze(0))
            rte_batch.append(torch.cat(rte_list, dim=0).unsqueeze(0))
        return torch.cat(rte_batch, dim=0)

def __init__(self, dim, RTE_ratio=2):
    super(RTE, self).__init__()
    self.RTE_ratio = RTE_ratio
    self.emb = RelTemporalEncoding(dim, RTE_ratio=self.RTE_ratio)

class V2XFusionBlock(nn.Module):

    def __init__(self, num_blocks, cav_att_config, pwindow_config):
        super().__init__()
        self.layers = nn.ModuleList([])
        self.num_blocks = num_blocks
        for _ in range(num_blocks):
            att = HGTCavAttention(cav_att_config['dim'], heads=cav_att_config['heads'], dim_head=cav_att_config['dim_head'], dropout=cav_att_config['dropout']) if cav_att_config['use_hetero'] else CavAttention(cav_att_config['dim'], heads=cav_att_config['heads'], dim_head=cav_att_config['dim_head'], dropout=cav_att_config['dropout'])
            self.layers.append(nn.ModuleList([PreNorm(cav_att_config['dim'], att), PreNorm(cav_att_config['dim'], PyramidWindowAttention(pwindow_config['dim'], heads=pwindow_config['heads'], dim_heads=pwindow_config['dim_head'], drop_out=pwindow_config['dropout'], window_size=pwindow_config['window_size'], relative_pos_embedding=pwindow_config['relative_pos_embedding'], fuse_method=pwindow_config['fusion_method']))]))

    def forward(self, x, mask, prior_encoding):
        for cav_attn, pwindow_attn in self.layers:
            x = cav_attn(x, mask=mask, prior_encoding=prior_encoding) + x
            x = pwindow_attn(x) + x
        return x

def __init__(self, num_blocks, cav_att_config, pwindow_config):
    super().__init__()
    self.layers = nn.ModuleList([])
    self.num_blocks = num_blocks
    for _ in range(num_blocks):
        att = HGTCavAttention(cav_att_config['dim'], heads=cav_att_config['heads'], dim_head=cav_att_config['dim_head'], dropout=cav_att_config['dropout']) if cav_att_config['use_hetero'] else CavAttention(cav_att_config['dim'], heads=cav_att_config['heads'], dim_head=cav_att_config['dim_head'], dropout=cav_att_config['dropout'])
        self.layers.append(nn.ModuleList([PreNorm(cav_att_config['dim'], att), PreNorm(cav_att_config['dim'], PyramidWindowAttention(pwindow_config['dim'], heads=pwindow_config['heads'], dim_heads=pwindow_config['dim_head'], drop_out=pwindow_config['dropout'], window_size=pwindow_config['window_size'], relative_pos_embedding=pwindow_config['relative_pos_embedding'], fuse_method=pwindow_config['fusion_method']))]))

class V2XTEncoder(nn.Module):

    def __init__(self, args):
        super().__init__()
        cav_att_config = args['cav_att_config']
        pwindow_att_config = args['pwindow_att_config']
        feed_config = args['feed_forward']
        num_blocks = args['num_blocks']
        depth = args['depth']
        mlp_dim = feed_config['mlp_dim']
        dropout = feed_config['dropout']
        self.downsample_rate = args['sttf']['downsample_rate']
        self.discrete_ratio = args['sttf']['voxel_size'][0]
        self.use_roi_mask = args['use_roi_mask']
        self.use_RTE = cav_att_config['use_RTE']
        self.RTE_ratio = cav_att_config['RTE_ratio']
        self.sttf = STTF(args['sttf'])
        self.prior_feed = nn.Linear(cav_att_config['dim'] + 3, cav_att_config['dim'])
        self.layers = nn.ModuleList([])
        if self.use_RTE:
            self.rte = RTE(cav_att_config['dim'], self.RTE_ratio)
        for _ in range(depth):
            self.layers.append(nn.ModuleList([V2XFusionBlock(num_blocks, cav_att_config, pwindow_att_config), PreNorm(cav_att_config['dim'], FeedForward(cav_att_config['dim'], mlp_dim, dropout=dropout))]))

    def forward(self, x, mask, spatial_correction_matrix):
        prior_encoding = x[..., -3:]
        x = x[..., :-3]
        if self.use_RTE:
            dt = prior_encoding[:, :, 0, 0, 1].to(torch.int)
            x = self.rte(x, dt)
        x = self.sttf(x, mask, spatial_correction_matrix)
        com_mask = mask.unsqueeze(1).unsqueeze(2).unsqueeze(3) if not self.use_roi_mask else get_roi_and_cav_mask(x.shape, mask, spatial_correction_matrix, self.discrete_ratio, self.downsample_rate)
        for attn, ff in self.layers:
            x = attn(x, mask=com_mask, prior_encoding=prior_encoding)
            x = ff(x) + x
        return x

def __init__(self, args):
    super().__init__()
    cav_att_config = args['cav_att_config']
    pwindow_att_config = args['pwindow_att_config']
    feed_config = args['feed_forward']
    num_blocks = args['num_blocks']
    depth = args['depth']
    mlp_dim = feed_config['mlp_dim']
    dropout = feed_config['dropout']
    self.downsample_rate = args['sttf']['downsample_rate']
    self.discrete_ratio = args['sttf']['voxel_size'][0]
    self.use_roi_mask = args['use_roi_mask']
    self.use_RTE = cav_att_config['use_RTE']
    self.RTE_ratio = cav_att_config['RTE_ratio']
    self.sttf = STTF(args['sttf'])
    self.prior_feed = nn.Linear(cav_att_config['dim'] + 3, cav_att_config['dim'])
    self.layers = nn.ModuleList([])
    if self.use_RTE:
        self.rte = RTE(cav_att_config['dim'], self.RTE_ratio)
    for _ in range(depth):
        self.layers.append(nn.ModuleList([V2XFusionBlock(num_blocks, cav_att_config, pwindow_att_config), PreNorm(cav_att_config['dim'], FeedForward(cav_att_config['dim'], mlp_dim, dropout=dropout))]))

class V2XTransformer(nn.Module):

    def __init__(self, args):
        super(V2XTransformer, self).__init__()
        encoder_args = args['encoder']
        self.encoder = V2XTEncoder(encoder_args)

    def forward(self, x, mask, spatial_correction_matrix):
        output = self.encoder(x, mask, spatial_correction_matrix)
        output = output[:, 0]
        return output

def __init__(self, args):
    super(V2XTransformer, self).__init__()
    encoder_args = args['encoder']
    self.encoder = V2XTEncoder(encoder_args)

class DoubleConv(nn.Module):
    """
    Double convoltuion
    Args:
        in_channels: input channel num
        out_channels: output channel num
    """

    def __init__(self, in_channels, out_channels, kernel_size, stride, padding):
        super().__init__()
        self.double_conv = nn.Sequential(nn.Conv2d(in_channels, out_channels, kernel_size=kernel_size, stride=stride, padding=padding), nn.ReLU(inplace=True), nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1), nn.ReLU(inplace=True))

    def forward(self, x):
        return self.double_conv(x)

def __init__(self, in_channels, out_channels, kernel_size, stride, padding):
    super().__init__()
    self.double_conv = nn.Sequential(nn.Conv2d(in_channels, out_channels, kernel_size=kernel_size, stride=stride, padding=padding), nn.ReLU(inplace=True), nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1), nn.ReLU(inplace=True))

class DownsampleConv(nn.Module):

    def __init__(self, config):
        super(DownsampleConv, self).__init__()
        self.layers = nn.ModuleList([])
        input_dim = config['input_dim']
        for ksize, dim, stride, padding in zip(config['kernal_size'], config['dim'], config['stride'], config['padding']):
            self.layers.append(DoubleConv(input_dim, dim, kernel_size=ksize, stride=stride, padding=padding))
            input_dim = dim

    def forward(self, x):
        for i in range(len(self.layers)):
            x = self.layers[i](x)
        return x

def __init__(self, config):
    super(DownsampleConv, self).__init__()
    self.layers = nn.ModuleList([])
    input_dim = config['input_dim']
    for ksize, dim, stride, padding in zip(config['kernal_size'], config['dim'], config['stride'], config['padding']):
        self.layers.append(DoubleConv(input_dim, dim, kernel_size=ksize, stride=stride, padding=padding))
        input_dim = dim

class SpatialFusion(nn.Module):

    def __init__(self):
        super(SpatialFusion, self).__init__()

    def regroup(self, x, record_len):
        cum_sum_len = torch.cumsum(record_len, dim=0)
        split_x = torch.tensor_split(x, cum_sum_len[:-1].cpu())
        return split_x

    def forward(self, x, record_len):
        split_x = self.regroup(x, record_len)
        out = []
        for xx in split_x:
            xx = torch.max(xx, dim=0, keepdim=True)[0]
            out.append(xx)
        return torch.cat(out, dim=0)

def __init__(self):
    super(SpatialFusion, self).__init__()

class ConvGRUCell(nn.Module):

    def __init__(self, input_size, input_dim, hidden_dim, kernel_size, bias):
        """
        Initialize the ConvLSTM cell
        :param input_size: (int, int)
            Height and width of input tensor as (height, width).
        :param input_dim: int
            Number of channels of input tensor.
        :param hidden_dim: int
            Number of channels of hidden state.
        :param kernel_size: (int, int)
            Size of the convolutional kernel.
        :param bias: bool
            Whether or not to add the bias.
        :param dtype: torch.cuda.FloatTensor or torch.FloatTensor
            Whether or not to use cuda.
        """
        super(ConvGRUCell, self).__init__()
        self.height, self.width = input_size
        self.padding = (kernel_size[0] // 2, kernel_size[1] // 2)
        self.hidden_dim = hidden_dim
        self.bias = bias
        self.conv_gates = nn.Conv2d(in_channels=input_dim + hidden_dim, out_channels=2 * self.hidden_dim, kernel_size=kernel_size, padding=self.padding, bias=self.bias)
        self.conv_can = nn.Conv2d(in_channels=input_dim + hidden_dim, out_channels=self.hidden_dim, kernel_size=kernel_size, padding=self.padding, bias=self.bias)

    def init_hidden(self, batch_size):
        return Variable(torch.zeros(batch_size, self.hidden_dim, self.height, self.width))

    def forward(self, input_tensor, h_cur):
        """
        :param self:
        :param input_tensor: (b, c, h, w)
            input is actually the target_model
        :param h_cur: (b, c_hidden, h, w)
            current hidden and cell states respectively
        :return: h_next,
            next hidden state
        """
        combined = torch.cat([input_tensor, h_cur], dim=1)
        combined_conv = self.conv_gates(combined)
        gamma, beta = torch.split(combined_conv, self.hidden_dim, dim=1)
        reset_gate = torch.sigmoid(gamma)
        update_gate = torch.sigmoid(beta)
        combined = torch.cat([input_tensor, reset_gate * h_cur], dim=1)
        cc_cnm = self.conv_can(combined)
        cnm = torch.tanh(cc_cnm)
        h_next = (1 - update_gate) * h_cur + update_gate * cnm
        return h_next

def __init__(self, input_size, input_dim, hidden_dim, kernel_size, bias):
    """
        Initialize the ConvLSTM cell
        :param input_size: (int, int)
            Height and width of input tensor as (height, width).
        :param input_dim: int
            Number of channels of input tensor.
        :param hidden_dim: int
            Number of channels of hidden state.
        :param kernel_size: (int, int)
            Size of the convolutional kernel.
        :param bias: bool
            Whether or not to add the bias.
        :param dtype: torch.cuda.FloatTensor or torch.FloatTensor
            Whether or not to use cuda.
        """
    super(ConvGRUCell, self).__init__()
    self.height, self.width = input_size
    self.padding = (kernel_size[0] // 2, kernel_size[1] // 2)
    self.hidden_dim = hidden_dim
    self.bias = bias
    self.conv_gates = nn.Conv2d(in_channels=input_dim + hidden_dim, out_channels=2 * self.hidden_dim, kernel_size=kernel_size, padding=self.padding, bias=self.bias)
    self.conv_can = nn.Conv2d(in_channels=input_dim + hidden_dim, out_channels=self.hidden_dim, kernel_size=kernel_size, padding=self.padding, bias=self.bias)

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

class BaseBEVBackbone(nn.Module):

    def __init__(self, model_cfg, input_channels):
        super().__init__()
        self.model_cfg = model_cfg
        if 'layer_nums' in self.model_cfg:
            assert len(self.model_cfg['layer_nums']) == len(self.model_cfg['layer_strides']) == len(self.model_cfg['num_filters'])
            layer_nums = self.model_cfg['layer_nums']
            layer_strides = self.model_cfg['layer_strides']
            num_filters = self.model_cfg['num_filters']
        else:
            layer_nums = layer_strides = num_filters = []
        if 'upsample_strides' in self.model_cfg:
            assert len(self.model_cfg['upsample_strides']) == len(self.model_cfg['num_upsample_filter'])
            num_upsample_filters = self.model_cfg['num_upsample_filter']
            upsample_strides = self.model_cfg['upsample_strides']
        else:
            upsample_strides = num_upsample_filters = []
        num_levels = len(layer_nums)
        c_in_list = [input_channels, *num_filters[:-1]]
        self.blocks = nn.ModuleList()
        self.deblocks = nn.ModuleList()
        for idx in range(num_levels):
            cur_layers = [nn.ZeroPad2d(1), nn.Conv2d(c_in_list[idx], num_filters[idx], kernel_size=3, stride=layer_strides[idx], padding=0, bias=False), nn.BatchNorm2d(num_filters[idx], eps=0.001, momentum=0.01), nn.ReLU()]
            for k in range(layer_nums[idx]):
                cur_layers.extend([nn.Conv2d(num_filters[idx], num_filters[idx], kernel_size=3, padding=1, bias=False), nn.BatchNorm2d(num_filters[idx], eps=0.001, momentum=0.01), nn.ReLU()])
            self.blocks.append(nn.Sequential(*cur_layers))
            if len(upsample_strides) > 0:
                stride = upsample_strides[idx]
                if stride >= 1:
                    self.deblocks.append(nn.Sequential(nn.ConvTranspose2d(num_filters[idx], num_upsample_filters[idx], upsample_strides[idx], stride=upsample_strides[idx], bias=False), nn.BatchNorm2d(num_upsample_filters[idx], eps=0.001, momentum=0.01), nn.ReLU()))
                else:
                    stride = np.round(1 / stride).astype(np.int)
                    self.deblocks.append(nn.Sequential(nn.Conv2d(num_filters[idx], num_upsample_filters[idx], stride, stride=stride, bias=False), nn.BatchNorm2d(num_upsample_filters[idx], eps=0.001, momentum=0.01), nn.ReLU()))
        c_in = sum(num_upsample_filters)
        if len(upsample_strides) > num_levels:
            self.deblocks.append(nn.Sequential(nn.ConvTranspose2d(c_in, c_in, upsample_strides[-1], stride=upsample_strides[-1], bias=False), nn.BatchNorm2d(c_in, eps=0.001, momentum=0.01), nn.ReLU()))
        self.num_bev_features = c_in

    def forward(self, data_dict):
        spatial_features = data_dict['spatial_features']
        ups = []
        ret_dict = {}
        x = spatial_features
        for i in range(len(self.blocks)):
            x = self.blocks[i](x)
            stride = int(spatial_features.shape[2] / x.shape[2])
            ret_dict['spatial_features_%dx' % stride] = x
            if len(self.deblocks) > 0:
                ups.append(self.deblocks[i](x))
            else:
                ups.append(x)
        if len(ups) > 1:
            x = torch.cat(ups, dim=1)
        elif len(ups) == 1:
            x = ups[0]
        if len(self.deblocks) > len(self.blocks):
            x = self.deblocks[-1](x)
        data_dict['spatial_features_2d'] = x
        return data_dict

def __init__(self, model_cfg, input_channels):
    super().__init__()
    self.model_cfg = model_cfg
    if 'layer_nums' in self.model_cfg:
        assert len(self.model_cfg['layer_nums']) == len(self.model_cfg['layer_strides']) == len(self.model_cfg['num_filters'])
        layer_nums = self.model_cfg['layer_nums']
        layer_strides = self.model_cfg['layer_strides']
        num_filters = self.model_cfg['num_filters']
    else:
        layer_nums = layer_strides = num_filters = []
    if 'upsample_strides' in self.model_cfg:
        assert len(self.model_cfg['upsample_strides']) == len(self.model_cfg['num_upsample_filter'])
        num_upsample_filters = self.model_cfg['num_upsample_filter']
        upsample_strides = self.model_cfg['upsample_strides']
    else:
        upsample_strides = num_upsample_filters = []
    num_levels = len(layer_nums)
    c_in_list = [input_channels, *num_filters[:-1]]
    self.blocks = nn.ModuleList()
    self.deblocks = nn.ModuleList()
    for idx in range(num_levels):
        cur_layers = [nn.ZeroPad2d(1), nn.Conv2d(c_in_list[idx], num_filters[idx], kernel_size=3, stride=layer_strides[idx], padding=0, bias=False), nn.BatchNorm2d(num_filters[idx], eps=0.001, momentum=0.01), nn.ReLU()]
        for k in range(layer_nums[idx]):
            cur_layers.extend([nn.Conv2d(num_filters[idx], num_filters[idx], kernel_size=3, padding=1, bias=False), nn.BatchNorm2d(num_filters[idx], eps=0.001, momentum=0.01), nn.ReLU()])
        self.blocks.append(nn.Sequential(*cur_layers))
        if len(upsample_strides) > 0:
            stride = upsample_strides[idx]
            if stride >= 1:
                self.deblocks.append(nn.Sequential(nn.ConvTranspose2d(num_filters[idx], num_upsample_filters[idx], upsample_strides[idx], stride=upsample_strides[idx], bias=False), nn.BatchNorm2d(num_upsample_filters[idx], eps=0.001, momentum=0.01), nn.ReLU()))
            else:
                stride = np.round(1 / stride).astype(np.int)
                self.deblocks.append(nn.Sequential(nn.Conv2d(num_filters[idx], num_upsample_filters[idx], stride, stride=stride, bias=False), nn.BatchNorm2d(num_upsample_filters[idx], eps=0.001, momentum=0.01), nn.ReLU()))
    c_in = sum(num_upsample_filters)
    if len(upsample_strides) > num_levels:
        self.deblocks.append(nn.Sequential(nn.ConvTranspose2d(c_in, c_in, upsample_strides[-1], stride=upsample_strides[-1], bias=False), nn.BatchNorm2d(c_in, eps=0.001, momentum=0.01), nn.ReLU()))
    self.num_bev_features = c_in

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

def __init__(self, radix, cardinality):
    super(RadixSoftmax, self).__init__()
    self.radix = radix
    self.cardinality = cardinality

class SplitAttn(nn.Module):

    def __init__(self, input_dim):
        super(SplitAttn, self).__init__()
        self.input_dim = input_dim
        self.fc1 = nn.Linear(input_dim, input_dim, bias=False)
        self.bn1 = nn.LayerNorm(input_dim)
        self.act1 = nn.ReLU()
        self.fc2 = nn.Linear(input_dim, input_dim * 3, bias=False)
        self.rsoftmax = RadixSoftmax(3, 1)

    def forward(self, window_list):
        assert len(window_list) == 3, 'only 3 windows are supported'
        sw, mw, bw = (window_list[0], window_list[1], window_list[2])
        B, L = (sw.shape[0], sw.shape[1])
        x_gap = sw + mw + bw
        x_gap = x_gap.mean((2, 3), keepdim=True)
        x_gap = self.act1(self.bn1(self.fc1(x_gap)))
        x_attn = self.fc2(x_gap)
        x_attn = self.rsoftmax(x_attn).view(B, L, 1, 1, -1)
        out = sw * x_attn[:, :, :, :, 0:self.input_dim] + mw * x_attn[:, :, :, :, self.input_dim:2 * self.input_dim] + bw * x_attn[:, :, :, :, self.input_dim * 2:]
        return out

def __init__(self, input_dim):
    super(SplitAttn, self).__init__()
    self.input_dim = input_dim
    self.fc1 = nn.Linear(input_dim, input_dim, bias=False)
    self.bn1 = nn.LayerNorm(input_dim)
    self.act1 = nn.ReLU()
    self.fc2 = nn.Linear(input_dim, input_dim * 3, bias=False)
    self.rsoftmax = RadixSoftmax(3, 1)

class NaiveCompressor(nn.Module):

    def __init__(self, input_dim, compress_raito):
        super().__init__()
        self.encoder = nn.Sequential(nn.Conv2d(input_dim, input_dim // compress_raito, kernel_size=3, stride=1, padding=1), nn.BatchNorm2d(input_dim // compress_raito, eps=0.001, momentum=0.01), nn.ReLU())
        self.decoder = nn.Sequential(nn.Conv2d(input_dim // compress_raito, input_dim, kernel_size=3, stride=1, padding=1), nn.BatchNorm2d(input_dim, eps=0.001, momentum=0.01), nn.ReLU(), nn.Conv2d(input_dim, input_dim, kernel_size=3, stride=1, padding=1), nn.BatchNorm2d(input_dim, eps=0.001, momentum=0.01), nn.ReLU())

    def forward(self, x):
        x = self.encoder(x)
        x = self.decoder(x)
        return x

def __init__(self, input_dim, compress_raito):
    super().__init__()
    self.encoder = nn.Sequential(nn.Conv2d(input_dim, input_dim // compress_raito, kernel_size=3, stride=1, padding=1), nn.BatchNorm2d(input_dim // compress_raito, eps=0.001, momentum=0.01), nn.ReLU())
    self.decoder = nn.Sequential(nn.Conv2d(input_dim // compress_raito, input_dim, kernel_size=3, stride=1, padding=1), nn.BatchNorm2d(input_dim, eps=0.001, momentum=0.01), nn.ReLU(), nn.Conv2d(input_dim, input_dim, kernel_size=3, stride=1, padding=1), nn.BatchNorm2d(input_dim, eps=0.001, momentum=0.01), nn.ReLU())

class V2VNetFusion(nn.Module):

    def __init__(self, args):
        super(V2VNetFusion, self).__init__()
        in_channels = args['in_channels']
        H, W = (args['conv_gru']['H'], args['conv_gru']['W'])
        kernel_size = args['conv_gru']['kernel_size']
        num_gru_layers = args['conv_gru']['num_layers']
        self.use_temporal_encoding = args['use_temporal_encoding']
        self.discrete_ratio = args['voxel_size'][0]
        self.downsample_rate = args['downsample_rate']
        self.num_iteration = args['num_iteration']
        self.gru_flag = args['gru_flag']
        self.agg_operator = args['agg_operator']
        self.cnn = nn.Conv2d(in_channels + 1, in_channels, kernel_size=3, stride=1, padding=1)
        self.msg_cnn = nn.Conv2d(in_channels * 2, in_channels, kernel_size=3, stride=1, padding=1)
        self.conv_gru = ConvGRU(input_size=(H, W), input_dim=in_channels * 2, hidden_dim=[in_channels], kernel_size=kernel_size, num_layers=num_gru_layers, batch_first=True, bias=True, return_all_layers=False)
        self.mlp = nn.Linear(in_channels, in_channels)

    def regroup(self, x, record_len):
        cum_sum_len = torch.cumsum(record_len, dim=0)
        split_x = torch.tensor_split(x, cum_sum_len[:-1].cpu())
        return split_x

    def forward(self, x, record_len, pairwise_t_matrix, prior_encoding):
        _, C, H, W = x.shape
        B, L = pairwise_t_matrix.shape[:2]
        if self.use_temporal_encoding:
            dt = prior_encoding[:, 1].to(torch.int).unsqueeze(1).unsqueeze(2).unsqueeze(3)
            x = torch.cat([x, dt.repeat(1, 1, H, W)], dim=1)
            x = self.cnn(x)
        split_x = self.regroup(x, record_len)
        pairwise_t_matrix = get_discretized_transformation_matrix(pairwise_t_matrix.reshape(-1, L, 4, 4), self.discrete_ratio, self.downsample_rate).reshape(B, L, L, 2, 3)
        roi_mask = get_rotated_roi((B * L, L, 1, H, W), pairwise_t_matrix.reshape(B * L * L, 2, 3))
        roi_mask = roi_mask.reshape(B, L, L, 1, H, W)
        batch_node_features = split_x
        for l in range(self.num_iteration):
            batch_updated_node_features = []
            for b in range(B):
                N = record_len[b]
                t_matrix = pairwise_t_matrix[b][:N, :N, :, :]
                updated_node_features = []
                for i in range(N):
                    mask = roi_mask[b, :N, i, ...]
                    current_t_matrix = t_matrix[:, i, :, :]
                    current_t_matrix = get_transformation_matrix(current_t_matrix, (H, W))
                    neighbor_feature = warp_affine(batch_node_features[b], current_t_matrix, (H, W))
                    ego_agent_feature = batch_node_features[b][i].unsqueeze(0).repeat(N, 1, 1, 1)
                    neighbor_feature = torch.cat([neighbor_feature, ego_agent_feature], dim=1)
                    message = self.msg_cnn(neighbor_feature) * mask
                    if self.agg_operator == 'avg':
                        agg_feature = torch.mean(message, dim=0)
                    elif self.agg_operator == 'max':
                        agg_feature = torch.max(message, dim=0)[0]
                    else:
                        raise ValueError('agg_operator has wrong value')
                    cat_feature = torch.cat([batch_node_features[b][i, ...], agg_feature], dim=0)
                    if self.gru_flag:
                        gru_out = self.conv_gru(cat_feature.unsqueeze(0).unsqueeze(0))[0][0].squeeze(0).squeeze(0)
                    else:
                        gru_out = batch_node_features[b][i, ...] + agg_feature
                    updated_node_features.append(gru_out.unsqueeze(0))
                batch_updated_node_features.append(torch.cat(updated_node_features, dim=0))
            batch_node_features = batch_updated_node_features
        out = torch.cat([itm[0, ...].unsqueeze(0) for itm in batch_node_features], dim=0)
        out = self.mlp(out.permute(0, 2, 3, 1)).permute(0, 3, 1, 2)
        return out

def __init__(self, args):
    super(V2VNetFusion, self).__init__()
    in_channels = args['in_channels']
    H, W = (args['conv_gru']['H'], args['conv_gru']['W'])
    kernel_size = args['conv_gru']['kernel_size']
    num_gru_layers = args['conv_gru']['num_layers']
    self.use_temporal_encoding = args['use_temporal_encoding']
    self.discrete_ratio = args['voxel_size'][0]
    self.downsample_rate = args['downsample_rate']
    self.num_iteration = args['num_iteration']
    self.gru_flag = args['gru_flag']
    self.agg_operator = args['agg_operator']
    self.cnn = nn.Conv2d(in_channels + 1, in_channels, kernel_size=3, stride=1, padding=1)
    self.msg_cnn = nn.Conv2d(in_channels * 2, in_channels, kernel_size=3, stride=1, padding=1)
    self.conv_gru = ConvGRU(input_size=(H, W), input_dim=in_channels * 2, hidden_dim=[in_channels], kernel_size=kernel_size, num_layers=num_gru_layers, batch_first=True, bias=True, return_all_layers=False)
    self.mlp = nn.Linear(in_channels, in_channels)

class PreNorm(nn.Module):

    def __init__(self, dim, fn):
        super().__init__()
        self.norm = nn.LayerNorm(dim)
        self.fn = fn

    def forward(self, x, **kwargs):
        return self.fn(self.norm(x), **kwargs)

def __init__(self, dim, fn):
    super().__init__()
    self.norm = nn.LayerNorm(dim)
    self.fn = fn

class FeedForward(nn.Module):

    def __init__(self, dim, hidden_dim, dropout=0.0):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(dim, hidden_dim), nn.GELU(), nn.Dropout(dropout), nn.Linear(hidden_dim, dim), nn.Dropout(dropout))

    def forward(self, x):
        return self.net(x)

def __init__(self, dim, hidden_dim, dropout=0.0):
    super().__init__()
    self.net = nn.Sequential(nn.Linear(dim, hidden_dim), nn.GELU(), nn.Dropout(dropout), nn.Linear(hidden_dim, dim), nn.Dropout(dropout))

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

def __init__(self, dim, heads, dim_head=64, dropout=0.1):
    super().__init__()
    inner_dim = heads * dim_head
    self.heads = heads
    self.scale = dim_head ** (-0.5)
    self.attend = nn.Softmax(dim=-1)
    self.to_qkv = nn.Linear(dim, inner_dim * 3, bias=False)
    self.to_out = nn.Sequential(nn.Linear(inner_dim, dim), nn.Dropout(dropout))

class BaseEncoder(nn.Module):

    def __init__(self, dim, depth, heads, dim_head, mlp_dim, dropout=0.0):
        super().__init__()
        self.layers = nn.ModuleList([])
        for _ in range(depth):
            self.layers.append(nn.ModuleList([PreNorm(dim, CavAttention(dim, heads=heads, dim_head=dim_head, dropout=dropout)), PreNorm(dim, FeedForward(dim, mlp_dim, dropout=dropout))]))

    def forward(self, x, mask):
        for attn, ff in self.layers:
            x = attn(x, mask=mask) + x
            x = ff(x) + x
        return x

def __init__(self, dim, depth, heads, dim_head, mlp_dim, dropout=0.0):
    super().__init__()
    self.layers = nn.ModuleList([])
    for _ in range(depth):
        self.layers.append(nn.ModuleList([PreNorm(dim, CavAttention(dim, heads=heads, dim_head=dim_head, dropout=dropout)), PreNorm(dim, FeedForward(dim, mlp_dim, dropout=dropout))]))

class BaseTransformer(nn.Module):

    def __init__(self, args):
        super().__init__()
        dim = args['dim']
        depth = args['depth']
        heads = args['heads']
        dim_head = args['dim_head']
        mlp_dim = args['mlp_dim']
        dropout = args['dropout']
        max_cav = args['max_cav']
        self.encoder = BaseEncoder(dim, depth, heads, dim_head, mlp_dim, dropout)

    def forward(self, x, mask):
        output = self.encoder(x, mask)
        output = output[:, 0]
        return output

def __init__(self, args):
    super().__init__()
    dim = args['dim']
    depth = args['depth']
    heads = args['heads']
    dim_head = args['dim_head']
    mlp_dim = args['mlp_dim']
    dropout = args['dropout']
    max_cav = args['max_cav']
    self.encoder = BaseEncoder(dim, depth, heads, dim_head, mlp_dim, dropout)

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

class PointPillarScatter(nn.Module):

    def __init__(self, model_cfg):
        super().__init__()
        self.model_cfg = model_cfg
        self.num_bev_features = self.model_cfg['num_features']
        self.nx, self.ny, self.nz = model_cfg['grid_size']
        assert self.nz == 1

    def forward(self, batch_dict):
        pillar_features, coords = (batch_dict['pillar_features'], batch_dict['voxel_coords'])
        batch_spatial_features = []
        batch_size = coords[:, 0].max().int().item() + 1
        for batch_idx in range(batch_size):
            spatial_feature = torch.zeros(self.num_bev_features, self.nz * self.nx * self.ny, dtype=pillar_features.dtype, device=pillar_features.device)
            batch_mask = coords[:, 0] == batch_idx
            this_coords = coords[batch_mask, :]
            indices = this_coords[:, 1] + this_coords[:, 2] * self.nx + this_coords[:, 3]
            indices = indices.type(torch.long)
            pillars = pillar_features[batch_mask, :]
            pillars = pillars.t()
            spatial_feature[:, indices] = pillars
            batch_spatial_features.append(spatial_feature)
        batch_spatial_features = torch.stack(batch_spatial_features, 0)
        batch_spatial_features = batch_spatial_features.view(batch_size, self.num_bev_features * self.nz, self.ny, self.nx)
        batch_dict['spatial_features'] = batch_spatial_features
        return batch_dict

def __init__(self, model_cfg):
    super().__init__()
    self.model_cfg = model_cfg
    self.num_bev_features = self.model_cfg['num_features']
    self.nx, self.ny, self.nz = model_cfg['grid_size']
    assert self.nz == 1

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

def __init__(self, dim):
    super(ScaledDotProductAttention, self).__init__()
    self.sqrt_dim = np.sqrt(dim)

class AttFusion(nn.Module):

    def __init__(self, feature_dim):
        super(AttFusion, self).__init__()
        self.att = ScaledDotProductAttention(feature_dim)

    def forward(self, x, record_len):
        split_x = self.regroup(x, record_len)
        batch_size = len(record_len)
        C, W, H = split_x[0].shape[1:]
        out = []
        for xx in split_x:
            cav_num = xx.shape[0]
            xx = xx.view(cav_num, C, -1).permute(2, 0, 1)
            h = self.att(xx, xx, xx)
            h = h.permute(1, 2, 0).view(cav_num, C, W, H)[0, ...].unsqueeze(0)
            out.append(h)
        return torch.cat(out, dim=0)

    def regroup(self, x, record_len):
        cum_sum_len = torch.cumsum(record_len, dim=0)
        split_x = torch.tensor_split(x, cum_sum_len[:-1].cpu())
        return split_x

def __init__(self, feature_dim):
    super(AttFusion, self).__init__()
    self.att = ScaledDotProductAttention(feature_dim)

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

class PyramidWindowAttention(nn.Module):

    def __init__(self, dim, heads, dim_heads, drop_out, window_size, relative_pos_embedding, fuse_method='naive'):
        super().__init__()
        assert isinstance(window_size, list)
        assert isinstance(heads, list)
        assert isinstance(dim_heads, list)
        assert len(dim_heads) == len(heads)
        self.pwmsa = nn.ModuleList([])
        for head, dim_head, ws in zip(heads, dim_heads, window_size):
            self.pwmsa.append(BaseWindowAttention(dim, head, dim_head, drop_out, ws, relative_pos_embedding))
        self.fuse_mehod = fuse_method
        if fuse_method == 'split_attn':
            self.split_attn = SplitAttn(256)

    def forward(self, x):
        output = None
        if self.fuse_mehod == 'naive':
            for wmsa in self.pwmsa:
                output = wmsa(x) if output is None else output + wmsa(x)
            return output / len(self.pwmsa)
        elif self.fuse_mehod == 'split_attn':
            window_list = []
            for wmsa in self.pwmsa:
                window_list.append(wmsa(x))
            return self.split_attn(window_list)

def __init__(self, dim, heads, dim_heads, drop_out, window_size, relative_pos_embedding, fuse_method='naive'):
    super().__init__()
    assert isinstance(window_size, list)
    assert isinstance(heads, list)
    assert isinstance(dim_heads, list)
    assert len(dim_heads) == len(heads)
    self.pwmsa = nn.ModuleList([])
    for head, dim_head, ws in zip(heads, dim_heads, window_size):
        self.pwmsa.append(BaseWindowAttention(dim, head, dim_head, drop_out, ws, relative_pos_embedding))
    self.fuse_mehod = fuse_method
    if fuse_method == 'split_attn':
        self.split_attn = SplitAttn(256)

class PixorLoss(nn.Module):

    def __init__(self, args):
        super(PixorLoss, self).__init__()
        self.alpha = args['alpha']
        self.beta = args['beta']
        self.loss_dict = {}

    def forward(self, output_dict, target_dict):
        """
        Compute loss for pixor network
        Parameters
        ----------
        output_dict : dict
           The dictionary that contains the output.

        target_dict : dict
           The dictionary that contains the target.

        Returns
        -------
        total_loss : torch.Tensor
            Total loss.

        """
        targets = target_dict['label_map']
        cls_preds, loc_preds = (output_dict['cls'], output_dict['reg'])
        cls_targets, loc_targets = targets.split([1, 6], dim=1)
        pos_count = cls_targets.sum()
        neg_count = (cls_targets == 0).sum()
        w1, w2 = (neg_count / (pos_count + neg_count), pos_count / (pos_count + neg_count))
        weights = torch.ones_like(cls_preds.reshape(-1))
        weights[cls_targets.reshape(-1) == 1] = w1
        weights[cls_targets.reshape(-1) == 0] = w2
        cls_loss = F.binary_cross_entropy_with_logits(input=cls_preds, target=cls_targets, reduction='mean')
        pos_pixels = cls_targets.sum()
        loc_loss = F.smooth_l1_loss(cls_targets * loc_preds, cls_targets * loc_targets, reduction='sum')
        loc_loss = loc_loss / pos_pixels if pos_pixels > 0 else loc_loss
        total_loss = self.alpha * cls_loss + self.beta * loc_loss
        self.loss_dict.update({'total_loss': total_loss, 'reg_loss': loc_loss, 'cls_loss': cls_loss})
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
        cls_loss = self.loss_dict['cls_loss']
        print('[epoch %d][%d/%d], || Loss: %.4f || cls Loss: %.4f || reg Loss: %.4f' % (epoch, batch_id + 1, batch_len, total_loss.item(), cls_loss.item(), reg_loss.item()))
        writer.add_scalar('Regression_loss', reg_loss.item(), epoch * batch_len + batch_id)
        writer.add_scalar('Confidence_loss', cls_loss.item(), epoch * batch_len + batch_id)

def __init__(self, args):
    super(PixorLoss, self).__init__()
    self.alpha = args['alpha']
    self.beta = args['beta']
    self.loss_dict = {}

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

def __init__(self, args):
    super(VoxelNetLoss, self).__init__()
    self.smoothl1loss = nn.SmoothL1Loss(size_average=False)
    self.alpha = args['alpha']
    self.beta = args['beta']
    self.reg_coe = args['reg']
    self.loss_dict = {}

class WeightedSmoothL1Loss(nn.Module):
    """
    Code-wise Weighted Smooth L1 Loss modified based on fvcore.nn.smooth_l1_loss
    https://github.com/facebookresearch/fvcore/blob/master/fvcore/nn/smooth_l1_loss.py
                  | 0.5 * x ** 2 / beta   if abs(x) < beta
    smoothl1(x) = |
                  | abs(x) - 0.5 * beta   otherwise,
    where x = input - target.
    """

    def __init__(self, beta: float=1.0 / 9.0, code_weights: list=None):
        """
        Args:
            beta: Scalar float.
                L1 to L2 change point.
                For beta values < 1e-5, L1 loss is computed.
            code_weights: (#codes) float list if not None.
                Code-wise weights.
        """
        super(WeightedSmoothL1Loss, self).__init__()
        self.beta = beta
        if code_weights is not None:
            self.code_weights = np.array(code_weights, dtype=np.float32)
            self.code_weights = torch.from_numpy(self.code_weights).cuda()

    @staticmethod
    def smooth_l1_loss(diff, beta):
        if beta < 1e-05:
            loss = torch.abs(diff)
        else:
            n = torch.abs(diff)
            loss = torch.where(n < beta, 0.5 * n ** 2 / beta, n - 0.5 * beta)
        return loss

    def forward(self, input: torch.Tensor, target: torch.Tensor, weights: torch.Tensor=None):
        """
        Args:
            input: (B, #anchors, #codes) float tensor.
                Ecoded predicted locations of objects.
            target: (B, #anchors, #codes) float tensor.
                Regression targets.
            weights: (B, #anchors) float tensor if not None.

        Returns:
            loss: (B, #anchors) float tensor.
                Weighted smooth l1 loss without reduction.
        """
        target = torch.where(torch.isnan(target), input, target)
        diff = input - target
        loss = self.smooth_l1_loss(diff, self.beta)
        if weights is not None:
            assert weights.shape[0] == loss.shape[0] and weights.shape[1] == loss.shape[1]
            loss = loss * weights.unsqueeze(-1)
        return loss

def __init__(self, beta: float=1.0 / 9.0, code_weights: list=None):
    """
        Args:
            beta: Scalar float.
                L1 to L2 change point.
                For beta values < 1e-5, L1 loss is computed.
            code_weights: (#codes) float list if not None.
                Code-wise weights.
        """
    super(WeightedSmoothL1Loss, self).__init__()
    self.beta = beta
    if code_weights is not None:
        self.code_weights = np.array(code_weights, dtype=np.float32)
        self.code_weights = torch.from_numpy(self.code_weights).cuda()

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

def __init__(self, args):
    super(PointPillarLoss, self).__init__()
    self.reg_loss_func = WeightedSmoothL1Loss()
    self.alpha = 0.25
    self.gamma = 2.0
    self.cls_weight = args['cls_weight']
    self.reg_coe = args['reg']
    self.loss_dict = {}

