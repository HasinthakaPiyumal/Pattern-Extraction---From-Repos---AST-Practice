# Cluster 4

def linset_assign_list(vis, lineset_list1, lineset_list2, update_mode='update'):
    """
    Associate two lists of lineset.

    Parameters
    ----------
    vis : open3d.Visualizer
    lineset_list1 : list
    lineset_list2 : list
    update_mode : str
        Add or update the geometry.
    """
    for j in range(len(lineset_list1)):
        index = j if j < len(lineset_list2) else -1
        lineset_list1[j] = lineset_assign(lineset_list1[j], lineset_list2[index])
        if update_mode == 'add':
            vis.add_geometry(lineset_list1[j])
        else:
            vis.update_geometry(lineset_list1[j])

def custom_draw_geometry(pcd, pred, gt):
    vis = o3d.visualization.Visualizer()
    vis.create_window()
    opt = vis.get_render_option()
    opt.background_color = np.asarray([0, 0, 0])
    opt.point_size = 1.0
    vis.add_geometry(pcd)
    for ele in pred:
        vis.add_geometry(ele)
    for ele in gt:
        vis.add_geometry(ele)
    vis.run()
    vis.destroy_window()

def visualize_sequence_sample_output(pred_tensor_list, gt_tensor_list, pcd_list):
    vis = o3d.visualization.Visualizer()
    vis.create_window()
    vis.get_render_option().background_color = [0.05, 0.05, 0.05]
    vis.get_render_option().point_size = 1.0
    vis.get_render_option().show_coordinate_frame = True
    vis_pcd = o3d.geometry.PointCloud()
    while True:
        for i, (pred_tensor, gt_tensor, pcd) in enumerate(zip(pred_tensor_list, gt_tensor_list, pcd_list)):
            pred_tensor = pred_tensor.copy()
            gt_tensor = gt_tensor.copy()
            pcd = pcd.copy()
            pcd_intcolor = color_encoding(pcd[:, -1])
            pcd[:, :1] = -pcd[:, :1]
            vis_pcd.points = o3d.utility.Vector3dVector(pcd[:, :3])
            vis_pcd.colors = o3d.utility.Vector3dVector(pcd_intcolor)
            oabbs_pred = bbx2oabb(pred_tensor, 'hwl')
            oabbs_gt = bbx2oabb(gt_tensor, 'hwl', color=(0, 1, 0))
            oabbs = oabbs_pred + oabbs_gt
            if i == 0:
                vis.add_geometry(vis_pcd)
            for oabb in oabbs:
                vis.add_geometry(oabb)
            vis.update_geometry(vis_pcd)
            ctr = vis.get_view_control()
            param = o3d.io.read_pinhole_camera_parameters('pinhole_param.json')
            ctr.convert_from_pinhole_camera_parameters(param)
            vis.poll_events()
            vis.update_renderer()
            for oabb in oabbs:
                vis.remove_geometry(oabb)
            time.sleep(0.01)
    vis.destroy_window()

def visualize_sequence_dataloader(dataloader, order, color_mode='constant'):
    """
    Visualize the batch data in animation.

    Parameters
    ----------
    dataloader : torch.Dataloader
        Pytorch dataloader

    order : str
        Bounding box order(N, 7).

    color_mode : str
        Color rendering mode.
    """
    vis = o3d.visualization.Visualizer()
    vis.create_window()
    vis.get_render_option().background_color = [0.05, 0.05, 0.05]
    vis.get_render_option().point_size = 1.0
    vis.get_render_option().show_coordinate_frame = True
    vis_pcd = o3d.geometry.PointCloud()
    vis_aabbs = []
    for _ in range(50):
        vis_aabbs.append(o3d.geometry.LineSet())
    while True:
        for i_batch, sample_batched in enumerate(dataloader):
            print(i_batch)
            pcd, aabbs = visualize_single_sample_dataloader(sample_batched['ego'], vis_pcd, order, mode=color_mode)
            if i_batch == 0:
                vis.add_geometry(pcd)
                for i in range(len(vis_aabbs)):
                    index = i if i < len(aabbs) else -1
                    vis_aabbs[i] = lineset_assign(vis_aabbs[i], aabbs[index])
                    vis.add_geometry(vis_aabbs[i])
            for i in range(len(vis_aabbs)):
                index = i if i < len(aabbs) else -1
                vis_aabbs[i] = lineset_assign(vis_aabbs[i], aabbs[index])
                vis.update_geometry(vis_aabbs[i])
            vis.update_geometry(pcd)
            vis.poll_events()
            vis.update_renderer()
            time.sleep(0.001)
    vis.destroy_window()

def save_o3d_visualization(element, save_path):
    """
    Save the open3d drawing to folder.

    Parameters
    ----------
    element : list
        List of o3d.geometry objects.

    save_path : str
        The save path.
    """
    vis = o3d.visualization.Visualizer()
    vis.create_window()
    for i in range(len(element)):
        vis.add_geometry(element[i])
        vis.update_geometry(element[i])
    vis.poll_events()
    vis.update_renderer()
    vis.capture_screen_image(save_path)
    vis.destroy_window()

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

def test_bev_post_processing():
    opt = test_parser()
    assert opt.fusion_method in ['late', 'early', 'intermediate']
    hypes = yaml_utils.load_yaml(None, opt)
    print('Dataset Building')
    opencood_dataset = build_dataset(hypes, visualize=True, train=False)
    data_loader = DataLoader(opencood_dataset, batch_size=1, num_workers=0, collate_fn=opencood_dataset.collate_batch_test, shuffle=False, pin_memory=False, drop_last=False)
    print('Creating Model')
    model = train_utils.create_model(hypes)
    if torch.cuda.is_available():
        model.cuda()
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print('Loading Model from checkpoint')
    saved_path = opt.model_dir
    _, model = train_utils.load_saved_model(saved_path, model)
    model.eval()
    for i, batch_data in enumerate(data_loader):
        batch_data = train_utils.to_device(batch_data, device)
        label_map = batch_data['ego']['label_dict']['label_map']
        output_dict = {'cls': label_map[:, 0, :, :], 'reg': label_map[:, 1:, :, :]}
        gt_box_tensor, _ = opencood_dataset.post_processor.post_process_debug(batch_data['ego'], output_dict)
        vis_utils.visualize_single_sample_output_bev(gt_box_tensor, batch_data['ego']['origin_lidar'].squeeze(0), opencood_dataset)

def main():
    opt = train_parser()
    hypes = yaml_utils.load_yaml(opt.hypes_yaml, opt)
    print('Dataset Building')
    opencood_train_dataset = build_dataset(hypes, visualize=False, train=True)
    opencood_validate_dataset = build_dataset(hypes, visualize=False, train=False)
    train_loader = DataLoader(opencood_train_dataset, batch_size=hypes['train_params']['batch_size'], num_workers=8, collate_fn=opencood_train_dataset.collate_batch_train, shuffle=True, pin_memory=False, drop_last=True)
    val_loader = DataLoader(opencood_validate_dataset, batch_size=hypes['train_params']['batch_size'], num_workers=8, collate_fn=opencood_train_dataset.collate_batch_train, shuffle=False, pin_memory=False, drop_last=True)
    print('Creating Model')
    model = train_utils.create_model(hypes)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    if torch.cuda.is_available():
        model.to(device)
    criterion = train_utils.create_loss(hypes)
    optimizer = train_utils.setup_optimizer(hypes, model)
    scheduler = train_utils.setup_lr_schedular(hypes, optimizer)
    if opt.model_dir:
        saved_path = opt.model_dir
        init_epoch, model = train_utils.load_saved_model(saved_path, model)
    else:
        init_epoch = 0
        saved_path = train_utils.setup_train(hypes)
    writer = SummaryWriter(saved_path)
    if opt.half:
        scaler = torch.cuda.amp.GradScaler()
    print('Training start')
    epoches = hypes['train_params']['epoches']
    for epoch in range(init_epoch, max(epoches, init_epoch)):
        scheduler.step(epoch)
        for param_group in optimizer.param_groups:
            print('learning rate %f' % param_group['lr'])
        pbar2 = tqdm.tqdm(total=len(train_loader), leave=True)
        for i, batch_data in enumerate(train_loader):
            model.train()
            model.zero_grad()
            optimizer.zero_grad()
            batch_data = train_utils.to_device(batch_data, device)
            if not opt.half:
                ouput_dict = model(batch_data['ego'])
                final_loss = criterion(ouput_dict, batch_data['ego']['label_dict'])
            else:
                with torch.cuda.amp.autocast():
                    ouput_dict = model(batch_data['ego'])
                    final_loss = criterion(ouput_dict, batch_data['ego']['label_dict'])
            criterion.logging(epoch, i, len(train_loader), writer, pbar=pbar2)
            pbar2.update(1)
            if not opt.half:
                final_loss.backward()
                optimizer.step()
            else:
                scaler.scale(final_loss).backward()
                scaler.step(optimizer)
                scaler.update()
        if epoch % hypes['train_params']['eval_freq'] == 0:
            valid_ave_loss = []
            with torch.no_grad():
                for i, batch_data in enumerate(val_loader):
                    model.eval()
                    batch_data = train_utils.to_device(batch_data, device)
                    ouput_dict = model(batch_data['ego'])
                    final_loss = criterion(ouput_dict, batch_data['ego']['label_dict'])
                    valid_ave_loss.append(final_loss.item())
            valid_ave_loss = statistics.mean(valid_ave_loss)
            print('At epoch %d, the validation loss is %f' % (epoch, valid_ave_loss))
            writer.add_scalar('Validate_Loss', valid_ave_loss, epoch)
        if epoch % hypes['train_params']['save_freq'] == 0:
            torch.save(model.state_dict(), os.path.join(saved_path, 'net_epoch%d.pth' % (epoch + 1)))
    print('Training Finished, checkpoints saved to %s' % saved_path)

def main():
    opt = test_parser()
    assert opt.fusion_method in ['late', 'early', 'intermediate']
    assert not (opt.show_vis and opt.show_sequence), 'you can only visualize the results in single image mode or video mode'
    hypes = yaml_utils.load_yaml(None, opt)
    print('Dataset Building')
    opencood_dataset = build_dataset(hypes, visualize=True, train=False)
    data_loader = DataLoader(opencood_dataset, batch_size=1, num_workers=10, collate_fn=opencood_dataset.collate_batch_test, shuffle=False, pin_memory=False, drop_last=False)
    print('Creating Model')
    model = train_utils.create_model(hypes)
    if torch.cuda.is_available():
        model.cuda()
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print('Loading Model from checkpoint')
    saved_path = opt.model_dir
    _, model = train_utils.load_saved_model(saved_path, model)
    model.eval()
    result_stat = {0.3: {'tp': [], 'fp': [], 'gt': 0}, 0.5: {'tp': [], 'fp': [], 'gt': 0}, 0.7: {'tp': [], 'fp': [], 'gt': 0}}
    if opt.show_sequence:
        vis = o3d.visualization.Visualizer()
        vis.create_window()
        vis.get_render_option().background_color = [0.05, 0.05, 0.05]
        vis.get_render_option().point_size = 1.0
        vis.get_render_option().show_coordinate_frame = True
        vis_pcd = o3d.geometry.PointCloud()
        vis_aabbs_gt = []
        vis_aabbs_pred = []
        for _ in range(50):
            vis_aabbs_gt.append(o3d.geometry.LineSet())
            vis_aabbs_pred.append(o3d.geometry.LineSet())
    for i, batch_data in enumerate(data_loader):
        print(i)
        with torch.no_grad():
            torch.cuda.synchronize()
            batch_data = train_utils.to_device(batch_data, device)
            if opt.fusion_method == 'late':
                pred_box_tensor, pred_score, gt_box_tensor = infrence_utils.inference_late_fusion(batch_data, model, opencood_dataset)
            elif opt.fusion_method == 'early':
                pred_box_tensor, pred_score, gt_box_tensor = infrence_utils.inference_early_fusion(batch_data, model, opencood_dataset)
            elif opt.fusion_method == 'intermediate':
                pred_box_tensor, pred_score, gt_box_tensor = infrence_utils.inference_intermediate_fusion(batch_data, model, opencood_dataset)
            else:
                raise NotImplementedError('Only early, late and intermediatefusion is supported.')
            eval_utils.caluclate_tp_fp(pred_box_tensor, pred_score, gt_box_tensor, result_stat, 0.3)
            eval_utils.caluclate_tp_fp(pred_box_tensor, pred_score, gt_box_tensor, result_stat, 0.5)
            eval_utils.caluclate_tp_fp(pred_box_tensor, pred_score, gt_box_tensor, result_stat, 0.7)
            if opt.save_npy:
                npy_save_path = os.path.join(opt.model_dir, 'npy')
                if not os.path.exists(npy_save_path):
                    os.makedirs(npy_save_path)
                infrence_utils.save_prediction_gt(pred_box_tensor, gt_box_tensor, batch_data['ego']['origin_lidar'][0], i, npy_save_path)
            if opt.show_vis or opt.save_vis:
                vis_save_path = ''
                if opt.save_vis:
                    vis_save_path = os.path.join(opt.model_dir, 'vis')
                    if not os.path.exists(vis_save_path):
                        os.makedirs(vis_save_path)
                    vis_save_path = os.path.join(vis_save_path, '%05d.png' % i)
                opencood_dataset.visualize_result(pred_box_tensor, gt_box_tensor, batch_data['ego']['origin_lidar'][0], opt.show_vis, vis_save_path, dataset=opencood_dataset)
            if opt.show_sequence:
                pcd, pred_o3d_box, gt_o3d_box = vis_utils.visualize_inference_sample_dataloader(pred_box_tensor, gt_box_tensor, batch_data['ego']['origin_lidar'][0], vis_pcd, mode='constant')
                if i == 0:
                    vis.add_geometry(pcd)
                    vis_utils.linset_assign_list(vis, vis_aabbs_pred, pred_o3d_box, update_mode='add')
                    vis_utils.linset_assign_list(vis, vis_aabbs_gt, gt_o3d_box, update_mode='add')
                vis_utils.linset_assign_list(vis, vis_aabbs_pred, pred_o3d_box)
                vis_utils.linset_assign_list(vis, vis_aabbs_gt, gt_o3d_box)
                vis.update_geometry(pcd)
                vis.poll_events()
                vis.update_renderer()
                time.sleep(0.001)
    eval_utils.eval_final_results(result_stat, opt.model_dir)
    if opt.show_sequence:
        vis.destroy_window()

def inference_intermediate_fusion(batch_data, model, dataset):
    """
    Model inference for early fusion.

    Parameters
    ----------
    batch_data : dict
    model : opencood.object
    dataset : opencood.EarlyFusionDataset

    Returns
    -------
    pred_box_tensor : torch.Tensor
        The tensor of prediction bounding box after NMS.
    gt_box_tensor : torch.Tensor
        The tensor of gt bounding box.
    """
    return inference_early_fusion(batch_data, model, dataset)

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

