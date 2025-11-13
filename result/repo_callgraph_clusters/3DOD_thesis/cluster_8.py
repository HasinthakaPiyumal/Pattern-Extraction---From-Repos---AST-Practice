# Cluster 8

class FrustumPointNetImg(nn.Module):

    def __init__(self, model_id, project_dir, num_points=1024):
        super(FrustumPointNetImg, self).__init__()
        self.num_points = num_points
        self.model_id = model_id
        self.project_dir = project_dir
        self.create_model_dirs()
        self.InstanceSeg_network = InstanceSeg()
        self.TNet_network = TNet()
        self.BboxNet_network = BboxNet()

    def forward(self, pcd, img):
        batch_size = pcd.size()[0]
        out_InstanceSeg = self.InstanceSeg_network(pcd)
        point_clouds = pcd.transpose(2, 1)[:, :, 0:3].data.cpu().numpy()
        seg_scores = out_InstanceSeg.data.cpu().numpy()
        seg_point_clouds = np.zeros((0, 512, 3), dtype=np.float32)
        out_dont_care_mask = torch.ones((batch_size,))
        out_dont_care_mask = out_dont_care_mask.type(torch.ByteTensor).cuda()
        for i in range(seg_scores.shape[0]):
            ex_seg_scores = seg_scores[i]
            ex_point_cloud = point_clouds[i]
            row_mask = ex_seg_scores[:, 1] > ex_seg_scores[:, 0]
            ex_seg_point_cloud = ex_point_cloud[row_mask, :]
            if ex_seg_point_cloud.shape[0] == 0:
                ex_seg_point_cloud = np.zeros((512, 3), dtype=np.float32)
                out_dont_care_mask[i] = 0
            if ex_seg_point_cloud.shape[0] < 512:
                row_idx = np.random.choice(ex_seg_point_cloud.shape[0], 512, replace=True)
            else:
                row_idx = np.random.choice(ex_seg_point_cloud.shape[0], 512, replace=False)
            ex_seg_point_cloud = ex_seg_point_cloud[row_idx, :]
            seg_point_clouds = np.concatenate((seg_point_clouds, [ex_seg_point_cloud]), axis=0)
        seg_point_clouds_mean = np.mean(seg_point_clouds, axis=1)
        out_seg_point_clouds_mean = Variable(torch.from_numpy(seg_point_clouds_mean)).cuda()
        seg_point_clouds_mean = np.expand_dims(seg_point_clouds_mean, axis=1)
        seg_point_clouds = seg_point_clouds - seg_point_clouds_mean
        seg_point_clouds = Variable(torch.from_numpy(seg_point_clouds)).cuda()
        seg_point_clouds = seg_point_clouds.transpose(2, 1)
        out_TNet = self.TNet_network(seg_point_clouds)
        seg_point_clouds = seg_point_clouds - out_TNet.unsqueeze(2).repeat(1, 1, seg_point_clouds.size()[2])
        out_BboxNet = self.BboxNet_network(seg_point_clouds, img)
        return (out_InstanceSeg, out_TNet, out_BboxNet, out_seg_point_clouds_mean, out_dont_care_mask)

    def create_model_dirs(self):
        self.logs_dir = self.project_dir + '/training_logs'
        self.model_dir = self.logs_dir + '/model_%s' % self.model_id
        self.checkpoints_dir = self.model_dir + '/checkpoints'
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)
            os.makedirs(self.checkpoints_dir)

def forward(self, pcd, img):
    batch_size = pcd.size()[0]
    out_InstanceSeg = self.InstanceSeg_network(pcd)
    point_clouds = pcd.transpose(2, 1)[:, :, 0:3].data.cpu().numpy()
    seg_scores = out_InstanceSeg.data.cpu().numpy()
    seg_point_clouds = np.zeros((0, 512, 3), dtype=np.float32)
    out_dont_care_mask = torch.ones((batch_size,))
    out_dont_care_mask = out_dont_care_mask.type(torch.ByteTensor).cuda()
    for i in range(seg_scores.shape[0]):
        ex_seg_scores = seg_scores[i]
        ex_point_cloud = point_clouds[i]
        row_mask = ex_seg_scores[:, 1] > ex_seg_scores[:, 0]
        ex_seg_point_cloud = ex_point_cloud[row_mask, :]
        if ex_seg_point_cloud.shape[0] == 0:
            ex_seg_point_cloud = np.zeros((512, 3), dtype=np.float32)
            out_dont_care_mask[i] = 0
        if ex_seg_point_cloud.shape[0] < 512:
            row_idx = np.random.choice(ex_seg_point_cloud.shape[0], 512, replace=True)
        else:
            row_idx = np.random.choice(ex_seg_point_cloud.shape[0], 512, replace=False)
        ex_seg_point_cloud = ex_seg_point_cloud[row_idx, :]
        seg_point_clouds = np.concatenate((seg_point_clouds, [ex_seg_point_cloud]), axis=0)
    seg_point_clouds_mean = np.mean(seg_point_clouds, axis=1)
    out_seg_point_clouds_mean = Variable(torch.from_numpy(seg_point_clouds_mean)).cuda()
    seg_point_clouds_mean = np.expand_dims(seg_point_clouds_mean, axis=1)
    seg_point_clouds = seg_point_clouds - seg_point_clouds_mean
    seg_point_clouds = Variable(torch.from_numpy(seg_point_clouds)).cuda()
    seg_point_clouds = seg_point_clouds.transpose(2, 1)
    out_TNet = self.TNet_network(seg_point_clouds)
    seg_point_clouds = seg_point_clouds - out_TNet.unsqueeze(2).repeat(1, 1, seg_point_clouds.size()[2])
    out_BboxNet = self.BboxNet_network(seg_point_clouds, img)
    return (out_InstanceSeg, out_TNet, out_BboxNet, out_seg_point_clouds_mean, out_dont_care_mask)

class FrustumPointNet(nn.Module):

    def __init__(self, model_id, project_dir, num_points=1024):
        super(FrustumPointNet, self).__init__()
        self.num_points = num_points
        self.model_id = model_id
        self.project_dir = project_dir
        self.create_model_dirs()
        self.InstanceSeg_network = InstanceSeg()
        self.TNet_network = TNet()
        self.BboxNet_network = BboxNet()

    def forward(self, x):
        batch_size = x.size()[0]
        out_InstanceSeg = self.InstanceSeg_network(x)
        point_clouds = x.transpose(2, 1)[:, :, 0:3].data.cpu().numpy()
        seg_scores = out_InstanceSeg.data.cpu().numpy()
        seg_point_clouds = np.zeros((0, 512, 3), dtype=np.float32)
        out_dont_care_mask = torch.ones((batch_size,))
        out_dont_care_mask = out_dont_care_mask.type(torch.ByteTensor).cuda()
        for i in range(seg_scores.shape[0]):
            ex_seg_scores = seg_scores[i]
            ex_point_cloud = point_clouds[i]
            row_mask = ex_seg_scores[:, 1] > ex_seg_scores[:, 0]
            ex_seg_point_cloud = ex_point_cloud[row_mask, :]
            if ex_seg_point_cloud.shape[0] == 0:
                ex_seg_point_cloud = np.zeros((512, 3), dtype=np.float32)
                out_dont_care_mask[i] = 0
            if ex_seg_point_cloud.shape[0] < 512:
                row_idx = np.random.choice(ex_seg_point_cloud.shape[0], 512, replace=True)
            else:
                row_idx = np.random.choice(ex_seg_point_cloud.shape[0], 512, replace=False)
            ex_seg_point_cloud = ex_seg_point_cloud[row_idx, :]
            seg_point_clouds = np.concatenate((seg_point_clouds, [ex_seg_point_cloud]), axis=0)
        seg_point_clouds_mean = np.mean(seg_point_clouds, axis=1)
        out_seg_point_clouds_mean = Variable(torch.from_numpy(seg_point_clouds_mean)).cuda()
        seg_point_clouds_mean = np.expand_dims(seg_point_clouds_mean, axis=1)
        seg_point_clouds = seg_point_clouds - seg_point_clouds_mean
        seg_point_clouds = Variable(torch.from_numpy(seg_point_clouds)).cuda()
        seg_point_clouds = seg_point_clouds.transpose(2, 1)
        out_TNet = self.TNet_network(seg_point_clouds)
        seg_point_clouds = seg_point_clouds - out_TNet.unsqueeze(2).repeat(1, 1, seg_point_clouds.size()[2])
        out_BboxNet = self.BboxNet_network(seg_point_clouds)
        return (out_InstanceSeg, out_TNet, out_BboxNet, out_seg_point_clouds_mean, out_dont_care_mask)

    def create_model_dirs(self):
        self.logs_dir = self.project_dir + '/training_logs'
        self.model_dir = self.logs_dir + '/model_%s' % self.model_id
        self.checkpoints_dir = self.model_dir + '/checkpoints'
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)
            os.makedirs(self.checkpoints_dir)

def forward(self, x):
    batch_size = x.size()[0]
    out_InstanceSeg = self.InstanceSeg_network(x)
    point_clouds = x.transpose(2, 1)[:, :, 0:3].data.cpu().numpy()
    seg_scores = out_InstanceSeg.data.cpu().numpy()
    seg_point_clouds = np.zeros((0, 512, 3), dtype=np.float32)
    out_dont_care_mask = torch.ones((batch_size,))
    out_dont_care_mask = out_dont_care_mask.type(torch.ByteTensor).cuda()
    for i in range(seg_scores.shape[0]):
        ex_seg_scores = seg_scores[i]
        ex_point_cloud = point_clouds[i]
        row_mask = ex_seg_scores[:, 1] > ex_seg_scores[:, 0]
        ex_seg_point_cloud = ex_point_cloud[row_mask, :]
        if ex_seg_point_cloud.shape[0] == 0:
            ex_seg_point_cloud = np.zeros((512, 3), dtype=np.float32)
            out_dont_care_mask[i] = 0
        if ex_seg_point_cloud.shape[0] < 512:
            row_idx = np.random.choice(ex_seg_point_cloud.shape[0], 512, replace=True)
        else:
            row_idx = np.random.choice(ex_seg_point_cloud.shape[0], 512, replace=False)
        ex_seg_point_cloud = ex_seg_point_cloud[row_idx, :]
        seg_point_clouds = np.concatenate((seg_point_clouds, [ex_seg_point_cloud]), axis=0)
    seg_point_clouds_mean = np.mean(seg_point_clouds, axis=1)
    out_seg_point_clouds_mean = Variable(torch.from_numpy(seg_point_clouds_mean)).cuda()
    seg_point_clouds_mean = np.expand_dims(seg_point_clouds_mean, axis=1)
    seg_point_clouds = seg_point_clouds - seg_point_clouds_mean
    seg_point_clouds = Variable(torch.from_numpy(seg_point_clouds)).cuda()
    seg_point_clouds = seg_point_clouds.transpose(2, 1)
    out_TNet = self.TNet_network(seg_point_clouds)
    seg_point_clouds = seg_point_clouds - out_TNet.unsqueeze(2).repeat(1, 1, seg_point_clouds.size()[2])
    out_BboxNet = self.BboxNet_network(seg_point_clouds)
    return (out_InstanceSeg, out_TNet, out_BboxNet, out_seg_point_clouds_mean, out_dont_care_mask)

class BoxRegressor(object):

    def __init__(self, camera_matrix, pred_size, pred_keypoints, pred_distance):
        super(BoxRegressor, self).__init__()
        self.P = camera_matrix
        self.P_pseudo_inverse = np.linalg.pinv(self.P)
        self.pred_keypoints = pred_keypoints
        self.pred_size = pred_size
        self.pred_distance = pred_distance

    def _residuals(self, params):
        [h, w, l, x, y, z, rot_y] = params
        projected_keypoints = get_keypoints(np.array([x, y, z]), h, w, l, rot_y, self.P)
        resids_keypoints = projected_keypoints - self.pred_keypoints
        resids_keypoints = resids_keypoints.flatten()
        resids_size_regularization = np.array([h - self.pred_size[0], w - self.pred_size[1], l - self.pred_size[2]])
        resids_distance_regularization = np.array([np.linalg.norm(params[3:6]) - self.pred_distance])
        resids = np.append(resids_keypoints, 100 * resids_size_regularization)
        resids = np.append(resids, 10 * resids_distance_regularization)
        return resids

    def _initial_guess(self):
        h, w, l = self.pred_size
        img_keypoints_center_hom = [np.mean(self.pred_keypoints[:, 0]), np.mean(self.pred_keypoints[:, 1]), 1]
        l0 = np.dot(self.P_pseudo_inverse, img_keypoints_center_hom)
        l0 = l0[:3] / l0[3]
        if l0[2] < 0:
            l0[0] = -l0[0]
            l0[2] = -l0[2]
        [x0, y0, z0] = l0 / np.linalg.norm(l0) * self.pred_distance
        rot_y = -np.pi / 2
        return [h, w, l, x0, y0, z0, rot_y]

    def solve(self):
        x0 = self._initial_guess()
        ls_results = []
        costs = []
        for rot_y in [-2, -1, 0, 1]:
            x0[6] = rot_y * np.pi / 2
            ls_result = least_squares(self._residuals, x0, jac='3-point')
            ls_results.append(ls_result)
            costs.append(ls_result.cost)
        self.result = ls_results[np.argmin(costs)]
        params = self.result.x
        return params

def _initial_guess(self):
    h, w, l = self.pred_size
    img_keypoints_center_hom = [np.mean(self.pred_keypoints[:, 0]), np.mean(self.pred_keypoints[:, 1]), 1]
    l0 = np.dot(self.P_pseudo_inverse, img_keypoints_center_hom)
    l0 = l0[:3] / l0[3]
    if l0[2] < 0:
        l0[0] = -l0[0]
        l0[2] = -l0[2]
    [x0, y0, z0] = l0 / np.linalg.norm(l0) * self.pred_distance
    rot_y = -np.pi / 2
    return [h, w, l, x0, y0, z0, rot_y]

