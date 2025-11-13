# Cluster 11

def visualize_single_sample_output_bev(pred_box, gt_box, pcd, dataset, show_vis=True, save_path=''):
    """
    Visualize the prediction, groundtruth with point cloud together in
    a bev format.

    Parameters
    ----------
    pred_box : torch.Tensor
        (N, 4, 2) prediction.

    gt_box : torch.Tensor
        (N, 4, 2) groundtruth bbx

    pcd : torch.Tensor
        PointCloud, (N, 4).

    show_vis : bool
        Whether to show visualization.

    save_path : str
        Save the visualization results to given path.
    """
    if not isinstance(pcd, np.ndarray):
        pcd = common_utils.torch_tensor_to_numpy(pcd)
    if pred_box is not None and (not isinstance(pred_box, np.ndarray)):
        pred_box = common_utils.torch_tensor_to_numpy(pred_box)
    if gt_box is not None and (not isinstance(gt_box, np.ndarray)):
        gt_box = common_utils.torch_tensor_to_numpy(gt_box)
    ratio = dataset.params['preprocess']['args']['res']
    L1, W1, H1, L2, W2, H2 = dataset.params['preprocess']['cav_lidar_range']
    bev_origin = np.array([L1, W1]).reshape(1, -1)
    bev_map = dataset.project_points_to_bev_map(pcd, ratio)
    bev_map = np.repeat(bev_map[:, :, np.newaxis], 3, axis=-1).astype(np.float32)
    bev_map = bev_map * 255
    if pred_box is not None:
        num_bbx = pred_box.shape[0]
        for i in range(num_bbx):
            bbx = pred_box[i]
            bbx = ((bbx - bev_origin) / ratio).astype(int)
            bbx = bbx[:, ::-1]
            cv2.polylines(bev_map, [bbx], True, (0, 0, 255), 1)
    if gt_box is not None and len(gt_box):
        for i in range(gt_box.shape[0]):
            bbx = gt_box[i][:4, :2]
            bbx = ((bbx - bev_origin) / ratio).astype(int)
            bbx = bbx[:, ::-1]
            cv2.polylines(bev_map, [bbx], True, (255, 0, 0), 1)
    if show_vis:
        plt.axis('off')
        plt.imshow(bev_map)
        plt.show()
    if save_path:
        plt.axis('off')
        plt.imshow(bev_map)
        plt.savefig(save_path)

def visualize_bev(batch_data):
    bev_input = batch_data['processed_lidar']['bev_input']
    label_map = batch_data['label_dict']['label_map']
    if not isinstance(bev_input, np.ndarray):
        bev_input = common_utils.torch_tensor_to_numpy(bev_input)
    if not isinstance(label_map, np.ndarray):
        label_map = label_map[0].numpy() if not label_map[0].is_cuda else label_map[0].cpu().detach().numpy()
    if len(bev_input.shape) > 3:
        bev_input = bev_input[0, ...]
    plt.matshow(np.sum(bev_input, axis=0))
    plt.axis('off')
    plt.matshow(label_map[0, :, :])
    plt.axis('off')
    plt.show()

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

class BaseDataset(Dataset):
    """
    Base dataset for all kinds of fusion. Mainly used to assign correct
    index and add noise.

    Parameters
    __________
    params : dict
        The dictionary contains all parameters for training/testing.

    visualize : false
        If set to true, the dataset is used for visualization.

    Attributes
    ----------
    scenario_database : OrderedDict
        A structured dictionary contains all file information.

    len_record : list
        The list to record each scenario's data length. This is used to
        retrieve the correct index during training.

    """

    def __init__(self, params, visualize, train=True):
        self.params = params
        self.visualize = visualize
        self.train = train
        self.pre_processor = None
        self.post_processor = None
        self.data_augmentor = DataAugmentor(params['data_augment'], train)
        if 'wild_setting' in params:
            self.seed = params['wild_setting']['seed']
            self.async_flag = params['wild_setting']['async']
            self.async_mode = 'sim' if 'async_mode' not in params['wild_setting'] else params['wild_setting']['async_mode']
            self.async_overhead = params['wild_setting']['async_overhead']
            self.loc_err_flag = params['wild_setting']['loc_err']
            self.xyz_noise_std = params['wild_setting']['xyz_std']
            self.ryp_noise_std = params['wild_setting']['ryp_std']
            self.data_size = params['wild_setting']['data_size'] if 'data_size' in params['wild_setting'] else 0
            self.transmission_speed = params['wild_setting']['transmission_speed'] if 'transmission_speed' in params['wild_setting'] else 27
            self.backbone_delay = params['wild_setting']['backbone_delay'] if 'backbone_delay' in params['wild_setting'] else 0
        else:
            self.async_flag = False
            self.async_overhead = 0
            self.async_mode = 'sim'
            self.loc_err_flag = False
            self.xyz_noise_std = 0
            self.ryp_noise_std = 0
            self.data_size = 0
            self.transmission_speed = 27
            self.backbone_delay = 0
        if self.train:
            root_dir = params['root_dir']
        else:
            root_dir = params['validate_dir']
        if 'max_cav' not in params['train_params']:
            self.max_cav = 7
        else:
            self.max_cav = params['train_params']['max_cav']
        scenario_folders = sorted([os.path.join(root_dir, x) for x in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, x))])
        self.scenario_database = OrderedDict()
        self.len_record = []
        for i, scenario_folder in enumerate(scenario_folders):
            self.scenario_database.update({i: OrderedDict()})
            cav_list = sorted([x for x in os.listdir(scenario_folder) if os.path.isdir(os.path.join(scenario_folder, x))])
            assert len(cav_list) > 0
            if int(cav_list[0]) < 0:
                cav_list = cav_list[1:] + [cav_list[0]]
            for j, cav_id in enumerate(cav_list):
                if j > self.max_cav - 1:
                    print('too many cavs')
                    break
                self.scenario_database[i][cav_id] = OrderedDict()
                cav_path = os.path.join(scenario_folder, cav_id)
                yaml_files = sorted([os.path.join(cav_path, x) for x in os.listdir(cav_path) if x.endswith('.yaml')])
                timestamps = self.extract_timestamps(yaml_files)
                for timestamp in timestamps:
                    self.scenario_database[i][cav_id][timestamp] = OrderedDict()
                    yaml_file = os.path.join(cav_path, timestamp + '.yaml')
                    lidar_file = os.path.join(cav_path, timestamp + '.pcd')
                    camera_files = self.load_camera_files(cav_path, timestamp)
                    self.scenario_database[i][cav_id][timestamp]['yaml'] = yaml_file
                    self.scenario_database[i][cav_id][timestamp]['lidar'] = lidar_file
                    self.scenario_database[i][cav_id][timestamp]['camera0'] = camera_files
                if j == 0:
                    self.scenario_database[i][cav_id]['ego'] = True
                    if not self.len_record:
                        self.len_record.append(len(timestamps))
                    else:
                        prev_last = self.len_record[-1]
                        self.len_record.append(prev_last + len(timestamps))
                else:
                    self.scenario_database[i][cav_id]['ego'] = False

    def __len__(self):
        return self.len_record[-1]

    def __getitem__(self, idx):
        """
        Abstract method, needs to be define by the children class.
        """
        pass

    def retrieve_base_data(self, idx, cur_ego_pose_flag=True):
        """
        Given the index, return the corresponding data.

        Parameters
        ----------
        idx : int
            Index given by dataloader.

        cur_ego_pose_flag : bool
            Indicate whether to use current timestamp ego pose to calculate
            transformation matrix.

        Returns
        -------
        data : dict
            The dictionary contains loaded yaml params and lidar data for
            each cav.
        """
        scenario_index = 0
        for i, ele in enumerate(self.len_record):
            if idx < ele:
                scenario_index = i
                break
        scenario_database = self.scenario_database[scenario_index]
        timestamp_index = idx if scenario_index == 0 else idx - self.len_record[scenario_index - 1]
        timestamp_key = self.return_timestamp_key(scenario_database, timestamp_index)
        ego_cav_content = self.calc_dist_to_ego(scenario_database, timestamp_key)
        data = OrderedDict()
        for cav_id, cav_content in scenario_database.items():
            data[cav_id] = OrderedDict()
            data[cav_id]['ego'] = cav_content['ego']
            timestamp_delay = self.time_delay_calculation(cav_content['ego'])
            if timestamp_index - timestamp_delay <= 0:
                timestamp_delay = timestamp_index
            timestamp_index_delay = max(0, timestamp_index - timestamp_delay)
            timestamp_key_delay = self.return_timestamp_key(scenario_database, timestamp_index_delay)
            data[cav_id]['time_delay'] = timestamp_delay
            data[cav_id]['params'] = self.reform_param(cav_content, ego_cav_content, timestamp_key, timestamp_key_delay, cur_ego_pose_flag)
            data[cav_id]['lidar_np'] = pcd_utils.pcd_to_np(cav_content[timestamp_key_delay]['lidar'])
        return data

    @staticmethod
    def extract_timestamps(yaml_files):
        """
        Given the list of the yaml files, extract the mocked timestamps.

        Parameters
        ----------
        yaml_files : list
            The full path of all yaml files of ego vehicle

        Returns
        -------
        timestamps : list
            The list containing timestamps only.
        """
        timestamps = []
        for file in yaml_files:
            res = file.split('/')[-1]
            timestamp = res.replace('.yaml', '')
            timestamps.append(timestamp)
        return timestamps

    @staticmethod
    def return_timestamp_key(scenario_database, timestamp_index):
        """
        Given the timestamp index, return the correct timestamp key, e.g.
        2 --> '000078'.

        Parameters
        ----------
        scenario_database : OrderedDict
            The dictionary contains all contents in the current scenario.

        timestamp_index : int
            The index for timestamp.

        Returns
        -------
        timestamp_key : str
            The timestamp key saved in the cav dictionary.
        """
        timestamp_keys = list(scenario_database.items())[0][1]
        timestamp_key = list(timestamp_keys.items())[timestamp_index][0]
        return timestamp_key

    def calc_dist_to_ego(self, scenario_database, timestamp_key):
        """
        Calculate the distance to ego for each cav.
        """
        ego_lidar_pose = None
        ego_cav_content = None
        for cav_id, cav_content in scenario_database.items():
            if cav_content['ego']:
                ego_cav_content = cav_content
                ego_lidar_pose = load_yaml(cav_content[timestamp_key]['yaml'])['lidar_pose']
                break
        assert ego_lidar_pose is not None
        for cav_id, cav_content in scenario_database.items():
            cur_lidar_pose = load_yaml(cav_content[timestamp_key]['yaml'])['lidar_pose']
            distance = math.sqrt((cur_lidar_pose[0] - ego_lidar_pose[0]) ** 2 + (cur_lidar_pose[1] - ego_lidar_pose[1]) ** 2)
            cav_content['distance_to_ego'] = distance
            scenario_database.update({cav_id: cav_content})
        return ego_cav_content

    def time_delay_calculation(self, ego_flag):
        """
        Calculate the time delay for a certain vehicle.

        Parameters
        ----------
        ego_flag : boolean
            Whether the current cav is ego.

        Return
        ------
        time_delay : int
            The time delay quantization.
        """
        if ego_flag:
            return 0
        if self.async_mode == 'real':
            overhead_noise = np.random.uniform(0, self.async_overhead)
            tc = self.data_size / self.transmission_speed * 1000
            time_delay = int(overhead_noise + tc + self.backbone_delay)
        elif self.async_mode == 'sim':
            time_delay = np.abs(self.async_overhead)
        time_delay = time_delay // 100
        return time_delay if self.async_flag else 0

    def add_loc_noise(self, pose, xyz_std, ryp_std):
        """
        Add localization noise to the pose.

        Parameters
        ----------
        pose : list
            x,y,z,roll,yaw,pitch

        xyz_std : float
            std of the gaussian noise on xyz

        ryp_std : float
            std of the gaussian noise
        """
        np.random.seed(self.seed)
        xyz_noise = np.random.normal(0, xyz_std, 3)
        ryp_std = np.random.normal(0, ryp_std, 3)
        noise_pose = [pose[0] + xyz_noise[0], pose[1] + xyz_noise[1], pose[2] + xyz_noise[2], pose[3], pose[4] + ryp_std[1], pose[5]]
        return noise_pose

    def reform_param(self, cav_content, ego_content, timestamp_cur, timestamp_delay, cur_ego_pose_flag):
        """
        Reform the data params with current timestamp object groundtruth and
        delay timestamp LiDAR pose.

        Parameters
        ----------
        cav_content : dict
            Dictionary that contains all file paths in the current cav/rsu.

        ego_content : dict
            Ego vehicle content.

        timestamp_cur : str
            The current timestamp.

        timestamp_delay : str
            The delayed timestamp.

        cur_ego_pose_flag : bool
            Whether use current ego pose to calculate transformation matrix.

        Return
        ------
        The merged parameters.
        """
        cur_params = load_yaml(cav_content[timestamp_cur]['yaml'])
        delay_params = load_yaml(cav_content[timestamp_delay]['yaml'])
        cur_ego_params = load_yaml(ego_content[timestamp_cur]['yaml'])
        delay_ego_params = load_yaml(ego_content[timestamp_delay]['yaml'])
        delay_cav_lidar_pose = delay_params['lidar_pose']
        delay_ego_lidar_pose = delay_ego_params['lidar_pose']
        cur_ego_lidar_pose = cur_ego_params['lidar_pose']
        cur_cav_lidar_pose = cur_params['lidar_pose']
        if not cav_content['ego'] and self.loc_err_flag:
            delay_cav_lidar_pose = self.add_loc_noise(delay_cav_lidar_pose, self.xyz_noise_std, self.ryp_noise_std)
            cur_cav_lidar_pose = self.add_loc_noise(cur_cav_lidar_pose, self.xyz_noise_std, self.ryp_noise_std)
        if cur_ego_pose_flag:
            transformation_matrix = x1_to_x2(delay_cav_lidar_pose, cur_ego_lidar_pose)
            spatial_correction_matrix = np.eye(4)
        else:
            transformation_matrix = x1_to_x2(delay_cav_lidar_pose, delay_ego_lidar_pose)
            spatial_correction_matrix = x1_to_x2(delay_ego_lidar_pose, cur_ego_lidar_pose)
        gt_transformation_matrix = x1_to_x2(cur_cav_lidar_pose, cur_ego_lidar_pose)
        delay_params['vehicles'] = cur_params['vehicles']
        delay_params['transformation_matrix'] = transformation_matrix
        delay_params['gt_transformation_matrix'] = gt_transformation_matrix
        delay_params['spatial_correction_matrix'] = spatial_correction_matrix
        return delay_params

    @staticmethod
    def load_camera_files(cav_path, timestamp):
        """
        Retrieve the paths to all camera files.

        Parameters
        ----------
        cav_path : str
            The full file path of current cav.

        timestamp : str
            Current timestamp

        Returns
        -------
        camera_files : list
            The list containing all camera png file paths.
        """
        camera0_file = os.path.join(cav_path, timestamp + '_camera0.png')
        camera1_file = os.path.join(cav_path, timestamp + '_camera1.png')
        camera2_file = os.path.join(cav_path, timestamp + '_camera2.png')
        camera3_file = os.path.join(cav_path, timestamp + '_camera3.png')
        return [camera0_file, camera1_file, camera2_file, camera3_file]

    def project_points_to_bev_map(self, points, ratio=0.1):
        """
        Project points to BEV occupancy map with default ratio=0.1.

        Parameters
        ----------
        points : np.ndarray
            (N, 3) / (N, 4)

        ratio : float
            Discretization parameters. Default is 0.1.

        Returns
        -------
        bev_map : np.ndarray
            BEV occupancy map including projected points
            with shape (img_row, img_col).

        """
        return self.pre_processor.project_points_to_bev_map(points, ratio)

    def augment(self, lidar_np, object_bbx_center, object_bbx_mask):
        """
        Data augmentation operation.
        """
        tmp_dict = {'lidar_np': lidar_np, 'object_bbx_center': object_bbx_center, 'object_bbx_mask': object_bbx_mask}
        tmp_dict = self.data_augmentor.forward(tmp_dict)
        lidar_np = tmp_dict['lidar_np']
        object_bbx_center = tmp_dict['object_bbx_center']
        object_bbx_mask = tmp_dict['object_bbx_mask']
        return (lidar_np, object_bbx_center, object_bbx_mask)

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
        processed_lidar_list = []
        label_dict_list = []
        if self.visualize:
            origin_lidar = []
        for i in range(len(batch)):
            ego_dict = batch[i]['ego']
            object_bbx_center.append(ego_dict['object_bbx_center'])
            object_bbx_mask.append(ego_dict['object_bbx_mask'])
            processed_lidar_list.append(ego_dict['processed_lidar'])
            label_dict_list.append(ego_dict['label_dict'])
            if self.visualize:
                origin_lidar.append(ego_dict['origin_lidar'])
        object_bbx_center = torch.from_numpy(np.array(object_bbx_center))
        object_bbx_mask = torch.from_numpy(np.array(object_bbx_mask))
        processed_lidar_torch_dict = self.pre_processor.collate_batch(processed_lidar_list)
        label_torch_dict = self.post_processor.collate_batch(label_dict_list)
        output_dict['ego'].update({'object_bbx_center': object_bbx_center, 'object_bbx_mask': object_bbx_mask, 'processed_lidar': processed_lidar_torch_dict, 'label_dict': label_torch_dict})
        if self.visualize:
            origin_lidar = np.array(downsample_lidar_minimum(pcd_np_list=origin_lidar))
            origin_lidar = torch.from_numpy(origin_lidar)
            output_dict['ego'].update({'origin_lidar': origin_lidar})
        return output_dict

    def visualize_result(self, pred_box_tensor, gt_tensor, pcd, show_vis, save_path, dataset=None):
        self.post_processor.visualize(pred_box_tensor, gt_tensor, pcd, show_vis, save_path, dataset=dataset)

def project_points_to_bev_map(self, points, ratio=0.1):
    """
        Project points to BEV occupancy map with default ratio=0.1.

        Parameters
        ----------
        points : np.ndarray
            (N, 3) / (N, 4)

        ratio : float
            Discretization parameters. Default is 0.1.

        Returns
        -------
        bev_map : np.ndarray
            BEV occupancy map including projected points
            with shape (img_row, img_col).

        """
    return self.pre_processor.project_points_to_bev_map(points, ratio)

class BasePreprocessor(object):
    """
    Basic Lidar pre-processor.

    Parameters
    ----------
    preprocess_params : dict
        The dictionary containing all parameters of the preprocessing.

    train : bool
        Train or test mode.
    """

    def __init__(self, preprocess_params, train):
        self.params = preprocess_params
        self.train = train

    def preprocess(self, pcd_np):
        """
        Preprocess the lidar points by simple sampling.

        Parameters
        ----------
        pcd_np : np.ndarray
            The raw lidar.

        Returns
        -------
        data_dict : the output dictionary.
        """
        data_dict = {}
        sample_num = self.params['args']['sample_num']
        pcd_np = pcd_utils.downsample_lidar(pcd_np, sample_num)
        data_dict['downsample_lidar'] = pcd_np
        return data_dict

    def project_points_to_bev_map(self, points, ratio=0.1):
        """
        Project points to BEV occupancy map with default ratio=0.1.

        Parameters
        ----------
        points : np.ndarray
            (N, 3) / (N, 4)

        ratio : float
            Discretization parameters. Default is 0.1.

        Returns
        -------
        bev_map : np.ndarray
            BEV occupancy map including projected points with shape
            (img_row, img_col).

        """
        L1, W1, H1, L2, W2, H2 = self.params['cav_lidar_range']
        img_row = int((L2 - L1) / ratio)
        img_col = int((W2 - W1) / ratio)
        bev_map = np.zeros((img_row, img_col))
        bev_origin = np.array([L1, W1, H1]).reshape(1, -1)
        indices = ((points[:, :3] - bev_origin) / ratio).astype(int)
        mask = np.logical_and(indices[:, 0] > 0, indices[:, 0] < img_row)
        mask = np.logical_and(mask, np.logical_and(indices[:, 1] > 0, indices[:, 1] < img_col))
        indices = indices[mask, :]
        bev_map[indices[:, 0], indices[:, 1]] = 1
        return bev_map

def project_points_to_bev_map(self, points, ratio=0.1):
    """
        Project points to BEV occupancy map with default ratio=0.1.

        Parameters
        ----------
        points : np.ndarray
            (N, 3) / (N, 4)

        ratio : float
            Discretization parameters. Default is 0.1.

        Returns
        -------
        bev_map : np.ndarray
            BEV occupancy map including projected points with shape
            (img_row, img_col).

        """
    L1, W1, H1, L2, W2, H2 = self.params['cav_lidar_range']
    img_row = int((L2 - L1) / ratio)
    img_col = int((W2 - W1) / ratio)
    bev_map = np.zeros((img_row, img_col))
    bev_origin = np.array([L1, W1, H1]).reshape(1, -1)
    indices = ((points[:, :3] - bev_origin) / ratio).astype(int)
    mask = np.logical_and(indices[:, 0] > 0, indices[:, 0] < img_row)
    mask = np.logical_and(mask, np.logical_and(indices[:, 1] > 0, indices[:, 1] < img_col))
    indices = indices[mask, :]
    bev_map[indices[:, 0], indices[:, 1]] = 1
    return bev_map

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

def check_numpy_to_torch(x):
    if isinstance(x, np.ndarray):
        return (torch.from_numpy(x).float(), True)
    return (x, False)

def dist_to_continuous(p_dist, displacement_dist, res, downsample_rate):
    """
    Convert points discretized format to continuous space for BEV representation.
    Parameters
    ----------
    p_dist : numpy.array
        Points in discretized coorindates.

    displacement_dist : numpy.array
        Discretized coordinates of bottom left origin.

    res : float
        Discretization resolution.

    downsample_rate : int
        Dowmsamping rate.

    Returns
    -------
    p_continuous : numpy.array
        Points in continuous coorindates.

    """
    p_dist = np.copy(p_dist)
    p_dist = p_dist + displacement_dist
    p_continuous = p_dist * res * downsample_rate
    return p_continuous

def corner_to_center(corner3d, order='lwh'):
    """
    Convert 8 corners to x, y, z, dx, dy, dz, yaw.

    Parameters
    ----------
    corner3d : np.ndarray
        (N, 8, 3)

    order : str
        'lwh' or 'hwl'

    Returns
    -------
    box3d : np.ndarray
        (N, 7)
    """
    assert corner3d.ndim == 3
    batch_size = corner3d.shape[0]
    xyz = np.mean(corner3d[:, [0, 3, 5, 6], :], axis=1)
    h = abs(np.mean(corner3d[:, 4:, 2] - corner3d[:, :4, 2], axis=1, keepdims=True))
    l = (np.sqrt(np.sum((corner3d[:, 0, [0, 1]] - corner3d[:, 3, [0, 1]]) ** 2, axis=1, keepdims=True)) + np.sqrt(np.sum((corner3d[:, 2, [0, 1]] - corner3d[:, 1, [0, 1]]) ** 2, axis=1, keepdims=True)) + np.sqrt(np.sum((corner3d[:, 4, [0, 1]] - corner3d[:, 7, [0, 1]]) ** 2, axis=1, keepdims=True)) + np.sqrt(np.sum((corner3d[:, 5, [0, 1]] - corner3d[:, 6, [0, 1]]) ** 2, axis=1, keepdims=True))) / 4
    w = (np.sqrt(np.sum((corner3d[:, 0, [0, 1]] - corner3d[:, 1, [0, 1]]) ** 2, axis=1, keepdims=True)) + np.sqrt(np.sum((corner3d[:, 2, [0, 1]] - corner3d[:, 3, [0, 1]]) ** 2, axis=1, keepdims=True)) + np.sqrt(np.sum((corner3d[:, 4, [0, 1]] - corner3d[:, 5, [0, 1]]) ** 2, axis=1, keepdims=True)) + np.sqrt(np.sum((corner3d[:, 6, [0, 1]] - corner3d[:, 7, [0, 1]]) ** 2, axis=1, keepdims=True))) / 4
    theta = (np.arctan2(corner3d[:, 1, 1] - corner3d[:, 2, 1], corner3d[:, 1, 0] - corner3d[:, 2, 0]) + np.arctan2(corner3d[:, 0, 1] - corner3d[:, 3, 1], corner3d[:, 0, 0] - corner3d[:, 3, 0]) + np.arctan2(corner3d[:, 5, 1] - corner3d[:, 6, 1], corner3d[:, 5, 0] - corner3d[:, 6, 0]) + np.arctan2(corner3d[:, 4, 1] - corner3d[:, 7, 1], corner3d[:, 4, 0] - corner3d[:, 7, 0]))[:, np.newaxis] / 4
    if order == 'lwh':
        return np.concatenate([xyz, l, w, h, theta], axis=1).reshape(batch_size, 7)
    elif order == 'hwl':
        return np.concatenate([xyz, h, w, l, theta], axis=1).reshape(batch_size, 7)
    else:
        sys.exit('Unknown order')

def get_mask_for_boxes_within_range_torch(boxes):
    """
    Generate mask to remove the bounding boxes
    outside the range.

    Parameters
    ----------
    boxes : torch.Tensor
        Groundtruth bbx, shape: N,8,3 or N,4,2
    Returns
    -------
    mask: torch.Tensor
        The mask for bounding box -- True means the
        bbx is within the range and False means the
        bbx is outside the range.
    """
    from v2xvit.data_utils.datasets import GT_RANGE
    device = boxes.device
    boundary_lower_range = torch.Tensor(GT_RANGE[:2]).reshape(1, 1, -1).to(device)
    boundary_higher_range = torch.Tensor(GT_RANGE[3:5]).reshape(1, 1, -1).to(device)
    mask = torch.all(torch.all(boxes[:, :, :2] >= boundary_lower_range, dim=-1) & torch.all(boxes[:, :, :2] <= boundary_higher_range, dim=-1), dim=-1)
    return mask

def mask_boxes_outside_range_numpy(boxes, limit_range, order, min_num_corners=8):
    """
    Parameters
    ----------
    boxes: np.ndarray
        (N, 7) [x, y, z, dx, dy, dz, heading], (x, y, z) is the box center

    limit_range: list
        [minx, miny, minz, maxx, maxy, maxz]

    min_num_corners: int
        The required minimum number of corners to be considered as in range.

    order : str
        'lwh' or 'hwl'

    Returns
    -------
    boxes: np.ndarray
        The filtered boxes.
    """
    assert boxes.shape[1] == 8 or boxes.shape[1] == 7
    new_boxes = boxes.copy()
    if boxes.shape[1] == 7:
        new_boxes = boxes_to_corners_3d(new_boxes, order)
    mask = ((new_boxes >= limit_range[0:3]) & (new_boxes <= limit_range[3:6])).all(axis=2)
    mask = mask.sum(axis=1) >= min_num_corners
    return boxes[mask]

def get_points_in_rotated_box(p, box_corner):
    """
    Get points within a rotated bounding box (2D version).

    Parameters
    ----------
    p : numpy.array
        Points to be tested with shape (N, 2).
    box_corner : numpy.array
        Corners of bounding box with shape (4, 2).

    Returns
    -------
    p_in_box : numpy.array
        Points within the box.

    """
    edge1 = box_corner[1, :] - box_corner[0, :]
    edge2 = box_corner[3, :] - box_corner[0, :]
    p_rel = p - box_corner[0, :].reshape(1, -1)
    l1 = get_projection_length_for_vector_projection(p_rel, edge1)
    l2 = get_projection_length_for_vector_projection(p_rel, edge2)
    mask = np.logical_and(l1 >= 0, l1 <= 1)
    mask = np.logical_and(mask, l2 >= 0)
    mask = np.logical_and(mask, l2 <= 1)
    p_in_box = p[mask, :]
    return p_in_box

def get_points_in_rotated_box_3d(p, box_corner):
    """
    Get points within a rotated bounding box (3D version).

    Parameters
    ----------
    p : numpy.array
        Points to be tested with shape (N, 3).
    box_corner : numpy.array
        Corners of bounding box with shape (8, 3).

    Returns
    -------
    p_in_box : numpy.array
        Points within the box.

    """
    edge1 = box_corner[1, :] - box_corner[0, :]
    edge2 = box_corner[3, :] - box_corner[0, :]
    edge3 = box_corner[4, :] - box_corner[0, :]
    p_rel = p - box_corner[0, :].reshape(1, -1)
    l1 = get_projection_length_for_vector_projection(p_rel, edge1)
    l2 = get_projection_length_for_vector_projection(p_rel, edge2)
    l3 = get_projection_length_for_vector_projection(p_rel, edge3)
    mask1 = np.logical_and(l1 >= 0, l1 <= 1)
    mask2 = np.logical_and(l2 >= 0, l2 <= 1)
    mask3 = np.logical_and(l3 >= 0, l3 <= 1)
    mask = np.logical_and(mask1, mask2)
    mask = np.logical_and(mask, mask3)
    p_in_box = p[mask, :]
    return p_in_box

def to_device(inputs, device):
    if isinstance(inputs, list):
        return [to_device(x, device) for x in inputs]
    elif isinstance(inputs, dict):
        return {k: to_device(v, device) for k, v in inputs.items()}
    else:
        if isinstance(inputs, int) or isinstance(inputs, float) or isinstance(inputs, str):
            return inputs
        return inputs.to(device)

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

@staticmethod
def _check_kernel_size_consistency(kernel_size):
    if not (isinstance(kernel_size, tuple) or (isinstance(kernel_size, list) and all([isinstance(elem, tuple) for elem in kernel_size]))):
        raise ValueError('`kernel_size` must be tuple or list of tuples')

@staticmethod
def _extend_for_multilayer(param, num_layers):
    if not isinstance(param, list):
        param = [param] * num_layers
    return param

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

def forward(self, x, mask):
    for attn, ff in self.layers:
        x = attn(x, mask=mask) + x
        x = ff(x) + x
    return x

def get_roi_and_cav_mask(shape, cav_mask, spatial_correction_matrix, discrete_ratio, downsample_rate):
    """
    Get mask for the combination of cav_mask and rorated ROI mask.
    Parameters
    ----------
    shape : tuple
        Shape of (B, L, H, W, C).
    cav_mask : torch.Tensor
        Shape of (B, L).
    spatial_correction_matrix : torch.Tensor
        Shape of (B, L, 4, 4)
    discrete_ratio : float
        Discrete ratio.
    downsample_rate : float
        Downsample rate.

    Returns
    -------
    com_mask : torch.Tensor
        Combined mask with shape (B, H, W, L, 1).

    """
    B, L, H, W, C = shape
    C = 1
    dist_correction_matrix = get_discretized_transformation_matrix(spatial_correction_matrix, discrete_ratio, downsample_rate)
    T = get_transformation_matrix(dist_correction_matrix.reshape(-1, 2, 3), (H, W))
    roi_mask = get_rotated_roi((B, L, C, H, W), T)
    com_mask = combine_roi_and_cav_mask(roi_mask, cav_mask)
    com_mask = com_mask.permute(0, 3, 4, 2, 1)
    return com_mask

def get_rotated_roi(shape, correction_matrix):
    """
    Get rorated ROI mask.

    Parameters
    ----------
    shape : tuple
        Shape of (B,L,C,H,W).
    correction_matrix : torch.Tensor
        Correction matrix with shape (N,2,3).

    Returns
    -------
    roi_mask : torch.Tensor
        Roated ROI mask with shape (N,2,3).

    """
    B, L, C, H, W = shape
    x = torch.ones((B, L, 1, H, W)).to(correction_matrix.dtype).to(correction_matrix.device)
    roi_mask = warp_affine(x.reshape(-1, 1, H, W), correction_matrix, dsize=(H, W), mode='nearest')
    roi_mask = torch.repeat_interleave(roi_mask, C, dim=1).reshape(B, L, C, H, W)
    return roi_mask

def _torch_inverse_cast(input):
    """
    Helper function to make torch.inverse work with other than fp32/64.
    The function torch.inverse is only implemented for fp32/64 which makes
    impossible to be used by fp16 or others. What this function does,
    is cast input data type to fp32, apply torch.inverse,
    and cast back to the input dtype.
    Args:
        input : torch.Tensor
            Tensor to be inversed.

    Returns:
        out : torch.Tensor
            Inversed Tensor.

    """
    dtype = input.dtype
    if dtype not in (torch.float32, torch.float64):
        dtype = torch.float32
    out = torch.inverse(input.to(dtype)).to(input.dtype)
    return out

class Test:
    """
    Test the transformation in this file.
    The methods in this class are not supposed to be used outside of this file.
    """

    def __init__(self):
        pass

    @staticmethod
    def load_img():
        torch.manual_seed(0)
        x = torch.randn(1, 5, 16, 400, 200) * 100
        return x

    @staticmethod
    def load_raw_transformation_matrix(N):
        a = 90 / 180 * np.pi
        matrix = torch.Tensor([[np.cos(a), -np.sin(a), 10], [np.sin(a), np.cos(a), 10]])
        matrix = torch.repeat_interleave(matrix.unsqueeze(0).unsqueeze(0), N, dim=1)
        return matrix

    @staticmethod
    def load_raw_transformation_matrix2(N, alpha):
        a = alpha / 180 * np.pi
        matrix = torch.Tensor([[np.cos(a), -np.sin(a), 0, 0], [np.sin(a), np.cos(a), 0, 0]])
        matrix = torch.repeat_interleave(matrix.unsqueeze(0).unsqueeze(0), N, dim=1)
        return matrix

    @staticmethod
    def test():
        img = Test.load_img()
        B, L, C, H, W = img.shape
        raw_T = Test.load_raw_transformation_matrix(5)
        T = get_transformation_matrix(raw_T.reshape(-1, 2, 3), (H, W))
        img_rot = warp_affine(img.reshape(-1, C, H, W), T, (H, W))
        print(img_rot[0, 0, :, :])
        plt.matshow(img_rot[0, 0, :, :])
        plt.show()

    @staticmethod
    def test_combine_roi_and_cav_mask():
        B = 2
        L = 5
        C = 16
        H = 300
        W = 400
        cav_mask = torch.Tensor([[1, 1, 1, 0, 0], [1, 0, 0, 0, 0]])
        x = torch.zeros(B, L, C, H, W)
        correction_matrix = Test.load_raw_transformation_matrix2(5, 10)
        correction_matrix = torch.cat([correction_matrix, correction_matrix], dim=0)
        mask = get_roi_and_cav_mask((B, L, H, W, C), cav_mask, correction_matrix, 0.4, 4)
        plt.matshow(mask[0, :, :, 0, 0])
        plt.show()

@staticmethod
def test():
    img = Test.load_img()
    B, L, C, H, W = img.shape
    raw_T = Test.load_raw_transformation_matrix(5)
    T = get_transformation_matrix(raw_T.reshape(-1, 2, 3), (H, W))
    img_rot = warp_affine(img.reshape(-1, C, H, W), T, (H, W))
    print(img_rot[0, 0, :, :])
    plt.matshow(img_rot[0, 0, :, :])
    plt.show()

@staticmethod
def test_combine_roi_and_cav_mask():
    B = 2
    L = 5
    C = 16
    H = 300
    W = 400
    cav_mask = torch.Tensor([[1, 1, 1, 0, 0], [1, 0, 0, 0, 0]])
    x = torch.zeros(B, L, C, H, W)
    correction_matrix = Test.load_raw_transformation_matrix2(5, 10)
    correction_matrix = torch.cat([correction_matrix, correction_matrix], dim=0)
    mask = get_roi_and_cav_mask((B, L, H, W, C), cav_mask, correction_matrix, 0.4, 4)
    plt.matshow(mask[0, :, :, 0, 0])
    plt.show()

