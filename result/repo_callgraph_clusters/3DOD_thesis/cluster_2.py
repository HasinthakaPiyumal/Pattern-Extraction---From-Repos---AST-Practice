# Cluster 2

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

def forward(self, img):
    out = self.resnet34(img)
    out = self.avg_pool(out)
    out = out.view(-1, 512)
    out = F.relu(self.fc1(out))
    out = F.relu(self.fc2(out))
    out = self.fc3(out)
    return out

