# Cluster 4

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

def create_model_dirs(self):
    self.logs_dir = self.project_dir + '/training_logs'
    self.model_dir = self.logs_dir + '/model_%s' % self.model_id
    self.checkpoints_dir = self.model_dir + '/checkpoints'
    if not os.path.exists(self.logs_dir):
        os.makedirs(self.logs_dir)
    if not os.path.exists(self.model_dir):
        os.makedirs(self.model_dir)
        os.makedirs(self.checkpoints_dir)

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

def create_model_dirs(self):
    self.logs_dir = self.project_dir + '/training_logs'
    self.model_dir = self.logs_dir + '/model_%s' % self.model_id
    self.checkpoints_dir = self.model_dir + '/checkpoints'
    if not os.path.exists(self.logs_dir):
        os.makedirs(self.logs_dir)
    if not os.path.exists(self.model_dir):
        os.makedirs(self.model_dir)
        os.makedirs(self.checkpoints_dir)

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

def create_model_dirs(self):
    self.logs_dir = self.project_dir + '/training_logs'
    self.model_dir = self.logs_dir + '/model_%s' % self.model_id
    self.checkpoints_dir = self.model_dir + '/checkpoints'
    if not os.path.exists(self.logs_dir):
        os.makedirs(self.logs_dir)
    if not os.path.exists(self.model_dir):
        os.makedirs(self.model_dir)
        os.makedirs(self.checkpoints_dir)

