# Cluster 0

def _read_requirements_file():
    """Return the elements in requirements.txt."""
    req_file_path = '%s/requirements.txt' % dirname(realpath(__file__))
    with open(req_file_path) as f:
        return [line.strip() for line in f]

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

def eval_final_results(result_stat, save_path):
    dump_dict = {}
    ap_30, mrec_30, mpre_30 = calculate_ap(result_stat, 0.3)
    ap_50, mrec_50, mpre_50 = calculate_ap(result_stat, 0.5)
    ap_70, mrec_70, mpre_70 = calculate_ap(result_stat, 0.7)
    dump_dict.update({'ap30': ap_30, 'ap_50': ap_50, 'ap_70': ap_70, 'mpre_50': mpre_50, 'mrec_50': mrec_50, 'mpre_70': mpre_70, 'mrec_70': mrec_70})
    yaml_utils.save_yaml(dump_dict, os.path.join(save_path, 'eval.yaml'))
    print('The Average Precision at IOU 0.3 is %.2f, The Average Precision at IOU 0.5 is %.2f, The Average Precision at IOU 0.7 is %.2f' % (ap_30, ap_50, ap_70))

def load_saved_model(saved_path, model):
    """
    Load saved model if exiseted

    Parameters
    __________
    saved_path : str
       model saved path
    model : opencood object
        The model instance.

    Returns
    -------
    model : opencood object
        The model instance loaded pretrained params.
    """
    assert os.path.exists(saved_path), '{} not found'.format(saved_path)

    def findLastCheckpoint(save_dir):
        file_list = glob.glob(os.path.join(save_dir, '*epoch*.pth'))
        if file_list:
            epochs_exist = []
            for file_ in file_list:
                result = re.findall('.*epoch(.*).pth.*', file_)
                epochs_exist.append(int(result[0]))
            initial_epoch_ = max(epochs_exist)
        else:
            initial_epoch_ = 0
        return initial_epoch_
    initial_epoch = findLastCheckpoint(saved_path)
    if initial_epoch > 0:
        print('resuming by loading epoch %d' % initial_epoch)
        model.load_state_dict(torch.load(os.path.join(saved_path, 'net_epoch%d.pth' % initial_epoch)), strict=False)
    return (initial_epoch, model)

def findLastCheckpoint(save_dir):
    file_list = glob.glob(os.path.join(save_dir, '*epoch*.pth'))
    if file_list:
        epochs_exist = []
        for file_ in file_list:
            result = re.findall('.*epoch(.*).pth.*', file_)
            epochs_exist.append(int(result[0]))
        initial_epoch_ = max(epochs_exist)
    else:
        initial_epoch_ = 0
    return initial_epoch_

def setup_train(hypes):
    """
    Create folder for saved model based on current timestep and model name

    Parameters
    ----------
    hypes: dict
        Config yaml dictionary for training:
    """
    model_name = hypes['name']
    current_time = datetime.now()
    folder_name = current_time.strftime('_%Y_%m_%d_%H_%M_%S')
    folder_name = model_name + folder_name
    current_path = os.path.dirname(__file__)
    current_path = os.path.join(current_path, '../logs')
    full_path = os.path.join(current_path, folder_name)
    if not os.path.exists(full_path):
        os.makedirs(full_path)
        save_name = os.path.join(full_path, 'config.yaml')
        with open(save_name, 'w') as outfile:
            yaml.dump(hypes, outfile)
    return full_path

def save_prediction_gt(pred_tensor, gt_tensor, pcd, timestamp, save_path):
    """
    Save prediction and gt tensor to txt file.
    """
    pred_np = torch_tensor_to_numpy(pred_tensor)
    gt_np = torch_tensor_to_numpy(gt_tensor)
    pcd_np = torch_tensor_to_numpy(pcd)
    np.save(os.path.join(save_path, '%04d_pcd.npy' % timestamp), pcd_np)
    np.save(os.path.join(save_path, '%04d_pred.npy' % timestamp), pred_np)
    np.save(os.path.join(save_path, '%04d_gt.npy' % timestamp), gt_np)

def load_yaml(file, opt=None):
    """
    Load yaml file and return a dictionary.

    Parameters
    ----------
    file : string
        yaml file path.

    opt : argparser
         Argparser.
    Returns
    -------
    param : dict
        A dictionary that contains defined parameters.
    """
    if opt and opt.model_dir:
        file = os.path.join(opt.model_dir, 'config.yaml')
    stream = open(file, 'r')
    loader = yaml.Loader
    loader.add_implicit_resolver(u'tag:yaml.org,2002:float', re.compile(u'^(?:\n         [-+]?(?:[0-9][0-9_]*)\\.[0-9_]*(?:[eE][-+]?[0-9]+)?\n        |[-+]?(?:[0-9][0-9_]*)(?:[eE][-+]?[0-9]+)\n        |\\.[0-9_]+(?:[eE][-+][0-9]+)?\n        |[-+]?[0-9][0-9_]*(?::[0-5]?[0-9])+\\.[0-9_]*\n        |[-+]?\\.(?:inf|Inf|INF)\n        |\\.(?:nan|NaN|NAN))$', re.X), list(u'-+0123456789.'))
    param = yaml.load(stream, Loader=loader)
    if 'yaml_parser' in param:
        param = eval(param['yaml_parser'])(param)
    return param

def load_voxel_params(param):
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
        Modified parameter dictionary with new attribute `anchor_args[W][H][L]`
    """
    anchor_args = param['postprocess']['anchor_args']
    cav_lidar_range = anchor_args['cav_lidar_range']
    voxel_size = param['preprocess']['args']['voxel_size']
    vw = voxel_size[0]
    vh = voxel_size[1]
    vd = voxel_size[2]
    anchor_args['vw'] = vw
    anchor_args['vh'] = vh
    anchor_args['vd'] = vd
    anchor_args['W'] = int((cav_lidar_range[3] - cav_lidar_range[0]) / vw)
    anchor_args['H'] = int((cav_lidar_range[4] - cav_lidar_range[1]) / vh)
    anchor_args['D'] = int((cav_lidar_range[5] - cav_lidar_range[2]) / vd)
    param['postprocess'].update({'anchor_args': anchor_args})
    if 'model' in param:
        param['model']['args']['W'] = anchor_args['W']
        param['model']['args']['H'] = anchor_args['H']
        param['model']['args']['D'] = anchor_args['D']
    return param

def f(low, high, r):
    return int((high - low) / r)

def load_bev_params(param):
    """
    Load bev related geometry parameters s.t. boundary, resolutions, input
    shape, target shape etc.

    Parameters
    ----------
    param : dict
        Original loaded parameter dictionary.

    Returns
    -------
    param : dict
        Modified parameter dictionary with new attribute `geometry_param`.

    """
    res = param['preprocess']['args']['res']
    L1, W1, H1, L2, W2, H2 = param['preprocess']['cav_lidar_range']
    downsample_rate = param['preprocess']['args']['downsample_rate']

    def f(low, high, r):
        return int((high - low) / r)
    input_shape = (int(f(L1, L2, res)), int(f(W1, W2, res)), int(f(H1, H2, res) + 1))
    label_shape = (int(input_shape[0] / downsample_rate), int(input_shape[1] / downsample_rate), 7)
    geometry_param = {'L1': L1, 'L2': L2, 'W1': W1, 'W2': W2, 'H1': H1, 'H2': H2, 'downsample_rate': downsample_rate, 'input_shape': input_shape, 'label_shape': label_shape, 'res': res}
    param['preprocess']['geometry_param'] = geometry_param
    param['postprocess']['geometry_param'] = geometry_param
    param['model']['args']['geometry_param'] = geometry_param
    return param

def save_yaml(data, save_name):
    """
    Save the dictionary into a yaml file.

    Parameters
    ----------
    data : dict
        The dictionary contains all data.

    save_name : string
        Full path of the output yaml file.
    """
    with open(save_name, 'w') as outfile:
        yaml.dump(data, outfile, default_flow_style=False)

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

@staticmethod
def get_paddings_indicator(actual_num, max_num, axis=0):
    actual_num = torch.unsqueeze(actual_num, axis + 1)
    max_num_shape = [1] * len(actual_num.shape)
    max_num_shape[axis + 1] = -1
    max_num = torch.arange(max_num, dtype=torch.int, device=actual_num.device).view(max_num_shape)
    paddings_indicator = actual_num.int() > max_num
    return paddings_indicator

