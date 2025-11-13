# Cluster 0

class InstanceSeg(nn.Module):

    def __init__(self, num_points=1024):
        super(InstanceSeg, self).__init__()
        self.num_points = num_points
        self.conv1 = nn.Conv1d(4, 64, 1)
        self.conv2 = nn.Conv1d(64, 64, 1)
        self.conv3 = nn.Conv1d(64, 64, 1)
        self.conv4 = nn.Conv1d(64, 128, 1)
        self.conv5 = nn.Conv1d(128, 1024, 1)
        self.conv6 = nn.Conv1d(1088, 512, 1)
        self.conv7 = nn.Conv1d(512, 256, 1)
        self.conv8 = nn.Conv1d(256, 128, 1)
        self.conv9 = nn.Conv1d(128, 128, 1)
        self.conv10 = nn.Conv1d(128, 2, 1)
        self.max_pool = nn.MaxPool1d(num_points)

    def forward(self, x):
        batch_size = x.size()[0]
        out = F.relu(self.conv1(x))
        out = F.relu(self.conv2(out))
        point_features = out
        out = F.relu(self.conv3(out))
        out = F.relu(self.conv4(out))
        out = F.relu(self.conv5(out))
        global_feature = self.max_pool(out)
        global_feature_repeated = global_feature.repeat(1, 1, self.num_points)
        out = torch.cat([global_feature_repeated, point_features], 1)
        out = F.relu(self.conv6(out))
        out = F.relu(self.conv7(out))
        out = F.relu(self.conv8(out))
        out = F.relu(self.conv9(out))
        out = self.conv10(out)
        out = out.transpose(2, 1).contiguous()
        out = F.log_softmax(out.view(-1, 2), dim=1)
        out = out.view(batch_size, self.num_points, 2)
        return out

def __init__(self, num_points=1024):
    super(InstanceSeg, self).__init__()
    self.num_points = num_points
    self.conv1 = nn.Conv1d(4, 64, 1)
    self.conv2 = nn.Conv1d(64, 64, 1)
    self.conv3 = nn.Conv1d(64, 64, 1)
    self.conv4 = nn.Conv1d(64, 128, 1)
    self.conv5 = nn.Conv1d(128, 1024, 1)
    self.conv6 = nn.Conv1d(1088, 512, 1)
    self.conv7 = nn.Conv1d(512, 256, 1)
    self.conv8 = nn.Conv1d(256, 128, 1)
    self.conv9 = nn.Conv1d(128, 128, 1)
    self.conv10 = nn.Conv1d(128, 2, 1)
    self.max_pool = nn.MaxPool1d(num_points)

class TNet(nn.Module):

    def __init__(self, num_seg_points=512):
        super(TNet, self).__init__()
        self.num_seg_points = num_seg_points
        self.conv1 = nn.Conv1d(3, 128, 1)
        self.conv2 = nn.Conv1d(128, 256, 1)
        self.conv3 = nn.Conv1d(256, 512, 1)
        self.max_pool = nn.MaxPool1d(num_seg_points)
        self.fc1 = nn.Linear(512, 256)
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, 3)

    def forward(self, x):
        out = F.relu(self.conv1(x))
        out = F.relu(self.conv2(out))
        out = F.relu(self.conv3(out))
        out = self.max_pool(out)
        out = out.view(-1, 512)
        out = F.relu(self.fc1(out))
        out = F.relu(self.fc2(out))
        out = self.fc3(out)
        return out

def __init__(self, num_seg_points=512):
    super(TNet, self).__init__()
    self.num_seg_points = num_seg_points
    self.conv1 = nn.Conv1d(3, 128, 1)
    self.conv2 = nn.Conv1d(128, 256, 1)
    self.conv3 = nn.Conv1d(256, 512, 1)
    self.max_pool = nn.MaxPool1d(num_seg_points)
    self.fc1 = nn.Linear(512, 256)
    self.fc2 = nn.Linear(256, 128)
    self.fc3 = nn.Linear(128, 3)

class BboxNet(nn.Module):

    def __init__(self, num_seg_points=512):
        super(BboxNet, self).__init__()
        self.NH = 4
        self.num_seg_points = num_seg_points
        self.conv1 = nn.Conv1d(3, 128, 1)
        self.conv2 = nn.Conv1d(128, 128, 1)
        self.conv3 = nn.Conv1d(128, 256, 1)
        self.conv4 = nn.Conv1d(256, 512, 1)
        self.max_pool = nn.MaxPool1d(num_seg_points)
        self.fc_pcd1 = nn.Linear(512, 512)
        self.fc_pcd2 = nn.Linear(512, 256)
        self.fc_pcd3 = nn.Linear(256, 3)
        self.fc_pcd_img1 = nn.Linear(1024, 512)
        self.fc_pcd_img2 = nn.Linear(512, 256)
        self.fc_pcd_img3 = nn.Linear(256, 3 + 2 * self.NH)
        resnet34 = models.resnet34()
        resnet34.load_state_dict(torch.load('/root/3DOD_thesis/pretrained_models/resnet/resnet34-333f7ec4.pth'))
        self.resnet34 = nn.Sequential(*list(resnet34.children())[:-2])
        self.avg_pool = nn.AvgPool2d(kernel_size=7)

    def forward(self, pcd, img):
        out_pcd = F.relu(self.conv1(pcd))
        out_pcd = F.relu(self.conv2(out_pcd))
        out_pcd = F.relu(self.conv3(out_pcd))
        out_pcd = F.relu(self.conv4(out_pcd))
        out_pcd = self.max_pool(out_pcd)
        out_pcd = out_pcd.view(-1, 512)
        out_img = self.resnet34(img)
        out_img = self.avg_pool(out_img)
        out_img = out_img.view(-1, 512)
        out_pcd_img = torch.cat([out_pcd, out_img], 1)
        out_pcd_img = F.relu(self.fc_pcd_img1(out_pcd_img))
        out_pcd_img = F.relu(self.fc_pcd_img2(out_pcd_img))
        out_pcd_img = self.fc_pcd_img3(out_pcd_img)
        out_pcd = F.relu(self.fc_pcd1(out_pcd))
        out_pcd = F.relu(self.fc_pcd2(out_pcd))
        out_pcd = self.fc_pcd3(out_pcd)
        out = torch.cat([out_pcd, out_pcd_img], 1)
        return out

def __init__(self, num_seg_points=512):
    super(BboxNet, self).__init__()
    self.NH = 4
    self.num_seg_points = num_seg_points
    self.conv1 = nn.Conv1d(3, 128, 1)
    self.conv2 = nn.Conv1d(128, 128, 1)
    self.conv3 = nn.Conv1d(128, 256, 1)
    self.conv4 = nn.Conv1d(256, 512, 1)
    self.max_pool = nn.MaxPool1d(num_seg_points)
    self.fc_pcd1 = nn.Linear(512, 512)
    self.fc_pcd2 = nn.Linear(512, 256)
    self.fc_pcd3 = nn.Linear(256, 3)
    self.fc_pcd_img1 = nn.Linear(1024, 512)
    self.fc_pcd_img2 = nn.Linear(512, 256)
    self.fc_pcd_img3 = nn.Linear(256, 3 + 2 * self.NH)
    resnet34 = models.resnet34()
    resnet34.load_state_dict(torch.load('/root/3DOD_thesis/pretrained_models/resnet/resnet34-333f7ec4.pth'))
    self.resnet34 = nn.Sequential(*list(resnet34.children())[:-2])
    self.avg_pool = nn.AvgPool2d(kernel_size=7)

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

def __init__(self, model_id, project_dir, num_points=1024):
    super(FrustumPointNetImg, self).__init__()
    self.num_points = num_points
    self.model_id = model_id
    self.project_dir = project_dir
    self.create_model_dirs()
    self.InstanceSeg_network = InstanceSeg()
    self.TNet_network = TNet()
    self.BboxNet_network = BboxNet()

class InstanceSeg(nn.Module):

    def __init__(self, num_points=1024):
        super(InstanceSeg, self).__init__()
        self.num_points = num_points
        self.conv1 = nn.Conv1d(4, 64, 1)
        self.conv2 = nn.Conv1d(64, 64, 1)
        self.conv3 = nn.Conv1d(64, 64, 1)
        self.conv4 = nn.Conv1d(64, 128, 1)
        self.conv5 = nn.Conv1d(128, 1024, 1)
        self.conv6 = nn.Conv1d(1088, 512, 1)
        self.conv7 = nn.Conv1d(512, 256, 1)
        self.conv8 = nn.Conv1d(256, 128, 1)
        self.conv9 = nn.Conv1d(128, 128, 1)
        self.conv10 = nn.Conv1d(128, 2, 1)
        self.max_pool = nn.MaxPool1d(num_points)

    def forward(self, x):
        batch_size = x.size()[0]
        out = F.relu(self.conv1(x))
        out = F.relu(self.conv2(out))
        point_features = out
        out = F.relu(self.conv3(out))
        out = F.relu(self.conv4(out))
        out = F.relu(self.conv5(out))
        global_feature = self.max_pool(out)
        global_feature_repeated = global_feature.repeat(1, 1, self.num_points)
        out = torch.cat([global_feature_repeated, point_features], 1)
        out = F.relu(self.conv6(out))
        out = F.relu(self.conv7(out))
        out = F.relu(self.conv8(out))
        out = F.relu(self.conv9(out))
        out = self.conv10(out)
        out = out.transpose(2, 1).contiguous()
        out = F.log_softmax(out.view(-1, 2), dim=1)
        out = out.view(batch_size, self.num_points, 2)
        return out

def __init__(self, num_points=1024):
    super(InstanceSeg, self).__init__()
    self.num_points = num_points
    self.conv1 = nn.Conv1d(4, 64, 1)
    self.conv2 = nn.Conv1d(64, 64, 1)
    self.conv3 = nn.Conv1d(64, 64, 1)
    self.conv4 = nn.Conv1d(64, 128, 1)
    self.conv5 = nn.Conv1d(128, 1024, 1)
    self.conv6 = nn.Conv1d(1088, 512, 1)
    self.conv7 = nn.Conv1d(512, 256, 1)
    self.conv8 = nn.Conv1d(256, 128, 1)
    self.conv9 = nn.Conv1d(128, 128, 1)
    self.conv10 = nn.Conv1d(128, 2, 1)
    self.max_pool = nn.MaxPool1d(num_points)

class TNet(nn.Module):

    def __init__(self, num_seg_points=512):
        super(TNet, self).__init__()
        self.num_seg_points = num_seg_points
        self.conv1 = nn.Conv1d(3, 128, 1)
        self.conv2 = nn.Conv1d(128, 256, 1)
        self.conv3 = nn.Conv1d(256, 512, 1)
        self.max_pool = nn.MaxPool1d(num_seg_points)
        self.fc1 = nn.Linear(512, 256)
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, 3)

    def forward(self, x):
        out = F.relu(self.conv1(x))
        out = F.relu(self.conv2(out))
        out = F.relu(self.conv3(out))
        out = self.max_pool(out)
        out = out.view(-1, 512)
        out = F.relu(self.fc1(out))
        out = F.relu(self.fc2(out))
        out = self.fc3(out)
        return out

def __init__(self, num_seg_points=512):
    super(TNet, self).__init__()
    self.num_seg_points = num_seg_points
    self.conv1 = nn.Conv1d(3, 128, 1)
    self.conv2 = nn.Conv1d(128, 256, 1)
    self.conv3 = nn.Conv1d(256, 512, 1)
    self.max_pool = nn.MaxPool1d(num_seg_points)
    self.fc1 = nn.Linear(512, 256)
    self.fc2 = nn.Linear(256, 128)
    self.fc3 = nn.Linear(128, 3)

class BboxNet(nn.Module):

    def __init__(self, num_seg_points=512):
        super(BboxNet, self).__init__()
        self.NH = 4
        self.num_seg_points = num_seg_points
        self.conv1 = nn.Conv1d(3, 128, 1)
        self.conv2 = nn.Conv1d(128, 128, 1)
        self.conv3 = nn.Conv1d(128, 256, 1)
        self.conv4 = nn.Conv1d(256, 512, 1)
        self.max_pool = nn.MaxPool1d(num_seg_points)
        self.fc1 = nn.Linear(512, 512)
        self.fc2 = nn.Linear(512, 256)
        self.fc3 = nn.Linear(256, 3 + 3 + 2 * self.NH)

    def forward(self, x):
        out = F.relu(self.conv1(x))
        out = F.relu(self.conv2(out))
        out = F.relu(self.conv3(out))
        out = F.relu(self.conv4(out))
        out = self.max_pool(out)
        out = out.view(-1, 512)
        out = F.relu(self.fc1(out))
        out = F.relu(self.fc2(out))
        out = self.fc3(out)
        return out

def __init__(self, num_seg_points=512):
    super(BboxNet, self).__init__()
    self.NH = 4
    self.num_seg_points = num_seg_points
    self.conv1 = nn.Conv1d(3, 128, 1)
    self.conv2 = nn.Conv1d(128, 128, 1)
    self.conv3 = nn.Conv1d(128, 256, 1)
    self.conv4 = nn.Conv1d(256, 512, 1)
    self.max_pool = nn.MaxPool1d(num_seg_points)
    self.fc1 = nn.Linear(512, 512)
    self.fc2 = nn.Linear(512, 256)
    self.fc3 = nn.Linear(256, 3 + 3 + 2 * self.NH)

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

def __init__(self, model_id, project_dir, num_points=1024):
    super(FrustumPointNet, self).__init__()
    self.num_points = num_points
    self.model_id = model_id
    self.project_dir = project_dir
    self.create_model_dirs()
    self.InstanceSeg_network = InstanceSeg()
    self.TNet_network = TNet()
    self.BboxNet_network = BboxNet()

class ImgNet(nn.Module):

    def __init__(self, model_id, project_dir):
        super(ImgNet, self).__init__()
        self.model_id = model_id
        self.project_dir = project_dir
        self.create_model_dirs()
        resnet34 = models.resnet34()
        resnet34.load_state_dict(torch.load('/root/3DOD_thesis/pretrained_models/resnet/resnet34-333f7ec4.pth'))
        self.resnet34 = nn.Sequential(*list(resnet34.children())[:-2])
        self.avg_pool = nn.AvgPool2d(kernel_size=7)
        self.fc1 = nn.Linear(512, 256)
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, 2 * 8 + 3 + 1)

    def forward(self, img):
        out = self.resnet34(img)
        out = self.avg_pool(out)
        out = out.view(-1, 512)
        out = F.relu(self.fc1(out))
        out = F.relu(self.fc2(out))
        out = self.fc3(out)
        return out

    def create_model_dirs(self):
        self.logs_dir = self.project_dir + '/training_logs'
        self.model_dir = self.logs_dir + '/model_%s' % self.model_id
        self.checkpoints_dir = self.model_dir + '/checkpoints'
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)
            os.makedirs(self.checkpoints_dir)

def __init__(self, model_id, project_dir):
    super(ImgNet, self).__init__()
    self.model_id = model_id
    self.project_dir = project_dir
    self.create_model_dirs()
    resnet34 = models.resnet34()
    resnet34.load_state_dict(torch.load('/root/3DOD_thesis/pretrained_models/resnet/resnet34-333f7ec4.pth'))
    self.resnet34 = nn.Sequential(*list(resnet34.children())[:-2])
    self.avg_pool = nn.AvgPool2d(kernel_size=7)
    self.fc1 = nn.Linear(512, 256)
    self.fc2 = nn.Linear(256, 128)
    self.fc3 = nn.Linear(128, 2 * 8 + 3 + 1)

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

def __init__(self, camera_matrix, pred_size, pred_keypoints, pred_distance):
    super(BoxRegressor, self).__init__()
    self.P = camera_matrix
    self.P_pseudo_inverse = np.linalg.pinv(self.P)
    self.pred_keypoints = pred_keypoints
    self.pred_size = pred_size
    self.pred_distance = pred_distance

