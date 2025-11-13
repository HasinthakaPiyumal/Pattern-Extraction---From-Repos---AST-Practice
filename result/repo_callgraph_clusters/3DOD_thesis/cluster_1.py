# Cluster 1

class DatasetFrustumPointNetImgAugmentation(torch.utils.data.Dataset):

    def __init__(self, kitti_data_path, kitti_meta_path, type, NH):
        self.img_dir = kitti_data_path + '/object/training/image_2/'
        self.label_dir = kitti_data_path + '/object/training/label_2/'
        self.calib_dir = kitti_data_path + '/object/training/calib/'
        self.lidar_dir = kitti_data_path + '/object/training/velodyne/'
        self.NH = NH
        with open(kitti_meta_path + '/%s_img_ids.pkl' % type, 'rb') as file:
            img_ids = pickle.load(file)
        with open(kitti_meta_path + '/kitti_train_mean_car_size.pkl', 'rb') as file:
            self.mean_car_size = pickle.load(file)
        with open(kitti_meta_path + '/kitti_centered_frustum_mean_xyz.pkl', 'rb') as file:
            self.centered_frustum_mean_xyz = pickle.load(file)
            self.centered_frustum_mean_xyz = self.centered_frustum_mean_xyz.astype(np.float32)
        self.examples = []
        for img_id in img_ids:
            labels = LabelLoader2D3D(img_id, self.label_dir, '.txt', self.calib_dir, '.txt')
            for label in labels:
                label_2d = label['label_2D']
                if label_2d['truncated'] < 0.5 and label_2d['class'] == 'Car':
                    label['img_id'] = img_id
                    self.examples.append(label)
        self.num_examples = len(self.examples)

    def __getitem__(self, index):
        example = self.examples[index]
        img_id = example['img_id']
        lidar_path = self.lidar_dir + img_id + '.bin'
        point_cloud = np.fromfile(lidar_path, dtype=np.float32).reshape(-1, 4)
        orig_point_cloud = point_cloud
        point_cloud = point_cloud[point_cloud[:, 0] > 0, :]
        point_cloud = point_cloud[point_cloud[:, 0] < 80, :]
        calib = calibread(self.calib_dir + img_id + '.txt')
        P2 = calib['P2']
        Tr_velo_to_cam_orig = calib['Tr_velo_to_cam']
        R0_rect_orig = calib['R0_rect']
        R0_rect = np.eye(4)
        R0_rect[0:3, 0:3] = R0_rect_orig
        Tr_velo_to_cam = np.eye(4)
        Tr_velo_to_cam[0:3, :] = Tr_velo_to_cam_orig
        point_cloud_xyz = point_cloud[:, 0:3]
        point_cloud_xyz_hom = np.ones((point_cloud.shape[0], 4))
        point_cloud_xyz_hom[:, 0:3] = point_cloud[:, 0:3]
        img_points_hom = np.dot(P2, np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T))).T
        img_points = np.zeros((img_points_hom.shape[0], 2))
        img_points[:, 0] = img_points_hom[:, 0] / img_points_hom[:, 2]
        img_points[:, 1] = img_points_hom[:, 1] / img_points_hom[:, 2]
        point_cloud_xyz_camera_hom = np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T)).T
        point_cloud_xyz_camera = np.zeros((point_cloud_xyz_camera_hom.shape[0], 3))
        point_cloud_xyz_camera[:, 0] = point_cloud_xyz_camera_hom[:, 0] / point_cloud_xyz_camera_hom[:, 3]
        point_cloud_xyz_camera[:, 1] = point_cloud_xyz_camera_hom[:, 1] / point_cloud_xyz_camera_hom[:, 3]
        point_cloud_xyz_camera[:, 2] = point_cloud_xyz_camera_hom[:, 2] / point_cloud_xyz_camera_hom[:, 3]
        point_cloud_camera = point_cloud
        point_cloud_camera[:, 0:3] = point_cloud_xyz_camera
        label_2D = example['label_2D']
        label_3D = example['label_3D']
        bbox = label_2D['poly']
        u_min = bbox[0, 0]
        u_max = bbox[1, 0]
        v_min = bbox[0, 1]
        v_max = bbox[2, 1]
        w = u_max - u_min
        h = v_max - v_min
        u_center = u_min + w / 2.0
        v_center = v_min + h / 2.0
        u_center = u_center + np.random.uniform(low=-0.1 * w, high=0.1 * w)
        v_center = v_center + np.random.uniform(low=-0.1 * h, high=0.1 * h)
        w = w * np.random.uniform(low=0.9, high=1.1)
        h = h * np.random.uniform(low=0.9, high=1.1)
        u_min = u_center - w / 2.0
        u_max = u_center + w / 2.0
        v_min = v_center - h / 2.0
        v_max = v_center + h / 2.0
        row_mask = np.logical_and(np.logical_and(img_points[:, 0] >= u_min, img_points[:, 0] <= u_max), np.logical_and(img_points[:, 1] >= v_min, img_points[:, 1] <= v_max))
        frustum_point_cloud_xyz = point_cloud_xyz[row_mask, :]
        frustum_point_cloud = point_cloud[row_mask, :]
        frustum_point_cloud_xyz_camera = point_cloud_xyz_camera[row_mask, :]
        frustum_point_cloud_camera = point_cloud_camera[row_mask, :]
        if frustum_point_cloud.shape[0] == 0:
            print(img_id)
            print(frustum_point_cloud.shape)
            return self.__getitem__(0)
        if frustum_point_cloud.shape[0] < 1024:
            row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=True)
        else:
            row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=False)
        frustum_point_cloud_xyz = frustum_point_cloud_xyz[row_idx, :]
        frustum_point_cloud = frustum_point_cloud[row_idx, :]
        frustum_point_cloud_xyz_camera = frustum_point_cloud_xyz_camera[row_idx, :]
        frustum_point_cloud_camera = frustum_point_cloud_camera[row_idx, :]
        img_path = self.img_dir + img_id + '.png'
        img = cv2.imread(img_path, -1)
        bbox_2d_img = img[int(np.max([0, v_min])):int(v_max), int(np.max([0, u_min])):int(u_max)]
        bbox_2d_img = cv2.resize(bbox_2d_img, (224, 224))
        points = label_3D['points']
        y_max = points[0, 1]
        y_min = points[4, 1]
        A = np.array([points[0, 0], points[0, 2]])
        B = np.array([points[1, 0], points[1, 2]])
        D = np.array([points[3, 0], points[3, 2]])
        AB = B - A
        AD = D - A
        AB_dot_AB = np.dot(AB, AB)
        AD_dot_AD = np.dot(AD, AD)
        P = np.zeros((frustum_point_cloud_xyz_camera.shape[0], 2))
        P[:, 0] = frustum_point_cloud_xyz_camera[:, 0]
        P[:, 1] = frustum_point_cloud_xyz_camera[:, 2]
        AP = P - A
        AP_dot_AB = np.dot(AP, AB)
        AP_dot_AD = np.dot(AP, AD)
        row_mask = np.logical_and(np.logical_and(frustum_point_cloud_xyz_camera[:, 1] >= y_min, frustum_point_cloud_xyz_camera[:, 1] <= y_max), np.logical_and(np.logical_and(AP_dot_AB >= 0, AP_dot_AB <= AB_dot_AB), np.logical_and(AP_dot_AD >= 0, AP_dot_AD <= AD_dot_AD)))
        row_mask_gt = row_mask
        gt_point_cloud_xyz_camera = frustum_point_cloud_xyz_camera[row_mask, :]
        label_InstanceSeg = np.zeros((frustum_point_cloud.shape[0],), dtype=np.int64)
        label_InstanceSeg[row_mask] = 1
        u_center = u_min + (u_max - u_min) / 2.0
        v_center = v_min + (v_max - v_min) / 2.0
        center_img_point_hom = np.array([u_center, v_center, 1])
        P2_pseudo_inverse = np.linalg.pinv(P2)
        point_hom = np.dot(P2_pseudo_inverse, center_img_point_hom)
        point = np.array([point_hom[0] / point_hom[3], point_hom[1] / point_hom[3], point_hom[2] / point_hom[3]])
        if point[2] < 0:
            point[0] = -point[0]
            point[2] = -point[2]
        frustum_angle = np.arctan2(point[0], point[2])
        frustum_R = np.asarray([[np.cos(frustum_angle), 0, -np.sin(frustum_angle)], [0, 1, 0], [np.sin(frustum_angle), 0, np.cos(frustum_angle)]], dtype='float32')
        centered_frustum_point_cloud_xyz_camera = np.dot(frustum_R, frustum_point_cloud_xyz_camera.T).T
        centered_frustum_point_cloud_xyz_camera -= self.centered_frustum_mean_xyz
        centered_frustum_point_cloud_camera = frustum_point_cloud_camera
        centered_frustum_point_cloud_camera[:, 0:3] = centered_frustum_point_cloud_xyz_camera
        z_shift = np.random.uniform(low=-20, high=20)
        centered_frustum_point_cloud_camera[:, 2] -= z_shift
        flip = np.random.randint(low=0, high=2)
        centered_frustum_point_cloud_camera[:, 0] = flip * -centered_frustum_point_cloud_camera[:, 0] + (1 - flip) * centered_frustum_point_cloud_camera[:, 0]
        if flip == 1:
            bbox_2d_img = cv2.flip(bbox_2d_img, 1)
        label_TNet = np.dot(frustum_R, label_3D['center']) - self.centered_frustum_mean_xyz
        label_TNet[0] = flip * -label_TNet[0] + (1 - flip) * label_TNet[0]
        label_TNet[2] -= z_shift
        centered_r_y = wrapToPi(label_3D['r_y'] - frustum_angle)
        if flip == 1:
            centered_r_y = wrapToPi(np.pi - centered_r_y)
        bin_number = getBinNumber(centered_r_y, NH=self.NH)
        bin_center = getBinCenter(bin_number, NH=self.NH)
        residual = wrapToPi(centered_r_y - bin_center)
        label_BboxNet = np.zeros((11,), dtype=np.float32)
        label_BboxNet[0:3] = np.dot(frustum_R, label_3D['center']) - self.centered_frustum_mean_xyz
        label_BboxNet[0] = flip * -label_BboxNet[0] + (1 - flip) * label_BboxNet[0]
        label_BboxNet[2] -= z_shift
        label_BboxNet[3] = label_3D['h']
        label_BboxNet[4] = label_3D['w']
        label_BboxNet[5] = label_3D['l']
        label_BboxNet[6] = bin_number
        label_BboxNet[7] = residual
        label_BboxNet[8:] = self.mean_car_size
        Rmat = np.asarray([[math.cos(residual), 0, math.sin(residual)], [0, 1, 0], [-math.sin(residual), 0, math.cos(residual)]], dtype='float32')
        center = label_BboxNet[0:3]
        l = label_3D['l']
        w = label_3D['w']
        h = label_3D['h']
        p0 = center + np.dot(Rmat, np.asarray([l / 2.0, 0, w / 2.0], dtype='float32').flatten())
        p1 = center + np.dot(Rmat, np.asarray([-l / 2.0, 0, w / 2.0], dtype='float32').flatten())
        p2 = center + np.dot(Rmat, np.asarray([-l / 2.0, 0, -w / 2.0], dtype='float32').flatten())
        p3 = center + np.dot(Rmat, np.asarray([l / 2.0, 0, -w / 2.0], dtype='float32').flatten())
        p4 = center + np.dot(Rmat, np.asarray([l / 2.0, -h, w / 2.0], dtype='float32').flatten())
        p5 = center + np.dot(Rmat, np.asarray([-l / 2.0, -h, w / 2.0], dtype='float32').flatten())
        p6 = center + np.dot(Rmat, np.asarray([-l / 2.0, -h, -w / 2.0], dtype='float32').flatten())
        p7 = center + np.dot(Rmat, np.asarray([l / 2.0, -h, -w / 2.0], dtype='float32').flatten())
        label_corner = np.array([p0, p1, p2, p3, p4, p5, p6, p7])
        label_corner_flipped = np.array([p2, p3, p0, p1, p6, p7, p4, p5])
        bbox_2d_img = bbox_2d_img / 255.0
        bbox_2d_img = bbox_2d_img - np.array([0.485, 0.456, 0.406])
        bbox_2d_img = bbox_2d_img / np.array([0.229, 0.224, 0.225])
        bbox_2d_img = np.transpose(bbox_2d_img, (2, 0, 1))
        bbox_2d_img = bbox_2d_img.astype(np.float32)
        centered_frustum_point_cloud_camera = torch.from_numpy(centered_frustum_point_cloud_camera)
        bbox_2d_img = torch.from_numpy(bbox_2d_img)
        label_InstanceSeg = torch.from_numpy(label_InstanceSeg)
        label_TNet = torch.from_numpy(label_TNet)
        label_BboxNet = torch.from_numpy(label_BboxNet)
        label_corner = torch.from_numpy(label_corner)
        label_corner_flipped = torch.from_numpy(label_corner_flipped)
        return (centered_frustum_point_cloud_camera, bbox_2d_img, label_InstanceSeg, label_TNet, label_BboxNet, label_corner, label_corner_flipped)

    def __len__(self):
        return self.num_examples

def __getitem__(self, index):
    example = self.examples[index]
    img_id = example['img_id']
    lidar_path = self.lidar_dir + img_id + '.bin'
    point_cloud = np.fromfile(lidar_path, dtype=np.float32).reshape(-1, 4)
    orig_point_cloud = point_cloud
    point_cloud = point_cloud[point_cloud[:, 0] > 0, :]
    point_cloud = point_cloud[point_cloud[:, 0] < 80, :]
    calib = calibread(self.calib_dir + img_id + '.txt')
    P2 = calib['P2']
    Tr_velo_to_cam_orig = calib['Tr_velo_to_cam']
    R0_rect_orig = calib['R0_rect']
    R0_rect = np.eye(4)
    R0_rect[0:3, 0:3] = R0_rect_orig
    Tr_velo_to_cam = np.eye(4)
    Tr_velo_to_cam[0:3, :] = Tr_velo_to_cam_orig
    point_cloud_xyz = point_cloud[:, 0:3]
    point_cloud_xyz_hom = np.ones((point_cloud.shape[0], 4))
    point_cloud_xyz_hom[:, 0:3] = point_cloud[:, 0:3]
    img_points_hom = np.dot(P2, np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T))).T
    img_points = np.zeros((img_points_hom.shape[0], 2))
    img_points[:, 0] = img_points_hom[:, 0] / img_points_hom[:, 2]
    img_points[:, 1] = img_points_hom[:, 1] / img_points_hom[:, 2]
    point_cloud_xyz_camera_hom = np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T)).T
    point_cloud_xyz_camera = np.zeros((point_cloud_xyz_camera_hom.shape[0], 3))
    point_cloud_xyz_camera[:, 0] = point_cloud_xyz_camera_hom[:, 0] / point_cloud_xyz_camera_hom[:, 3]
    point_cloud_xyz_camera[:, 1] = point_cloud_xyz_camera_hom[:, 1] / point_cloud_xyz_camera_hom[:, 3]
    point_cloud_xyz_camera[:, 2] = point_cloud_xyz_camera_hom[:, 2] / point_cloud_xyz_camera_hom[:, 3]
    point_cloud_camera = point_cloud
    point_cloud_camera[:, 0:3] = point_cloud_xyz_camera
    label_2D = example['label_2D']
    label_3D = example['label_3D']
    bbox = label_2D['poly']
    u_min = bbox[0, 0]
    u_max = bbox[1, 0]
    v_min = bbox[0, 1]
    v_max = bbox[2, 1]
    w = u_max - u_min
    h = v_max - v_min
    u_center = u_min + w / 2.0
    v_center = v_min + h / 2.0
    u_center = u_center + np.random.uniform(low=-0.1 * w, high=0.1 * w)
    v_center = v_center + np.random.uniform(low=-0.1 * h, high=0.1 * h)
    w = w * np.random.uniform(low=0.9, high=1.1)
    h = h * np.random.uniform(low=0.9, high=1.1)
    u_min = u_center - w / 2.0
    u_max = u_center + w / 2.0
    v_min = v_center - h / 2.0
    v_max = v_center + h / 2.0
    row_mask = np.logical_and(np.logical_and(img_points[:, 0] >= u_min, img_points[:, 0] <= u_max), np.logical_and(img_points[:, 1] >= v_min, img_points[:, 1] <= v_max))
    frustum_point_cloud_xyz = point_cloud_xyz[row_mask, :]
    frustum_point_cloud = point_cloud[row_mask, :]
    frustum_point_cloud_xyz_camera = point_cloud_xyz_camera[row_mask, :]
    frustum_point_cloud_camera = point_cloud_camera[row_mask, :]
    if frustum_point_cloud.shape[0] == 0:
        print(img_id)
        print(frustum_point_cloud.shape)
        return self.__getitem__(0)
    if frustum_point_cloud.shape[0] < 1024:
        row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=True)
    else:
        row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=False)
    frustum_point_cloud_xyz = frustum_point_cloud_xyz[row_idx, :]
    frustum_point_cloud = frustum_point_cloud[row_idx, :]
    frustum_point_cloud_xyz_camera = frustum_point_cloud_xyz_camera[row_idx, :]
    frustum_point_cloud_camera = frustum_point_cloud_camera[row_idx, :]
    img_path = self.img_dir + img_id + '.png'
    img = cv2.imread(img_path, -1)
    bbox_2d_img = img[int(np.max([0, v_min])):int(v_max), int(np.max([0, u_min])):int(u_max)]
    bbox_2d_img = cv2.resize(bbox_2d_img, (224, 224))
    points = label_3D['points']
    y_max = points[0, 1]
    y_min = points[4, 1]
    A = np.array([points[0, 0], points[0, 2]])
    B = np.array([points[1, 0], points[1, 2]])
    D = np.array([points[3, 0], points[3, 2]])
    AB = B - A
    AD = D - A
    AB_dot_AB = np.dot(AB, AB)
    AD_dot_AD = np.dot(AD, AD)
    P = np.zeros((frustum_point_cloud_xyz_camera.shape[0], 2))
    P[:, 0] = frustum_point_cloud_xyz_camera[:, 0]
    P[:, 1] = frustum_point_cloud_xyz_camera[:, 2]
    AP = P - A
    AP_dot_AB = np.dot(AP, AB)
    AP_dot_AD = np.dot(AP, AD)
    row_mask = np.logical_and(np.logical_and(frustum_point_cloud_xyz_camera[:, 1] >= y_min, frustum_point_cloud_xyz_camera[:, 1] <= y_max), np.logical_and(np.logical_and(AP_dot_AB >= 0, AP_dot_AB <= AB_dot_AB), np.logical_and(AP_dot_AD >= 0, AP_dot_AD <= AD_dot_AD)))
    row_mask_gt = row_mask
    gt_point_cloud_xyz_camera = frustum_point_cloud_xyz_camera[row_mask, :]
    label_InstanceSeg = np.zeros((frustum_point_cloud.shape[0],), dtype=np.int64)
    label_InstanceSeg[row_mask] = 1
    u_center = u_min + (u_max - u_min) / 2.0
    v_center = v_min + (v_max - v_min) / 2.0
    center_img_point_hom = np.array([u_center, v_center, 1])
    P2_pseudo_inverse = np.linalg.pinv(P2)
    point_hom = np.dot(P2_pseudo_inverse, center_img_point_hom)
    point = np.array([point_hom[0] / point_hom[3], point_hom[1] / point_hom[3], point_hom[2] / point_hom[3]])
    if point[2] < 0:
        point[0] = -point[0]
        point[2] = -point[2]
    frustum_angle = np.arctan2(point[0], point[2])
    frustum_R = np.asarray([[np.cos(frustum_angle), 0, -np.sin(frustum_angle)], [0, 1, 0], [np.sin(frustum_angle), 0, np.cos(frustum_angle)]], dtype='float32')
    centered_frustum_point_cloud_xyz_camera = np.dot(frustum_R, frustum_point_cloud_xyz_camera.T).T
    centered_frustum_point_cloud_xyz_camera -= self.centered_frustum_mean_xyz
    centered_frustum_point_cloud_camera = frustum_point_cloud_camera
    centered_frustum_point_cloud_camera[:, 0:3] = centered_frustum_point_cloud_xyz_camera
    z_shift = np.random.uniform(low=-20, high=20)
    centered_frustum_point_cloud_camera[:, 2] -= z_shift
    flip = np.random.randint(low=0, high=2)
    centered_frustum_point_cloud_camera[:, 0] = flip * -centered_frustum_point_cloud_camera[:, 0] + (1 - flip) * centered_frustum_point_cloud_camera[:, 0]
    if flip == 1:
        bbox_2d_img = cv2.flip(bbox_2d_img, 1)
    label_TNet = np.dot(frustum_R, label_3D['center']) - self.centered_frustum_mean_xyz
    label_TNet[0] = flip * -label_TNet[0] + (1 - flip) * label_TNet[0]
    label_TNet[2] -= z_shift
    centered_r_y = wrapToPi(label_3D['r_y'] - frustum_angle)
    if flip == 1:
        centered_r_y = wrapToPi(np.pi - centered_r_y)
    bin_number = getBinNumber(centered_r_y, NH=self.NH)
    bin_center = getBinCenter(bin_number, NH=self.NH)
    residual = wrapToPi(centered_r_y - bin_center)
    label_BboxNet = np.zeros((11,), dtype=np.float32)
    label_BboxNet[0:3] = np.dot(frustum_R, label_3D['center']) - self.centered_frustum_mean_xyz
    label_BboxNet[0] = flip * -label_BboxNet[0] + (1 - flip) * label_BboxNet[0]
    label_BboxNet[2] -= z_shift
    label_BboxNet[3] = label_3D['h']
    label_BboxNet[4] = label_3D['w']
    label_BboxNet[5] = label_3D['l']
    label_BboxNet[6] = bin_number
    label_BboxNet[7] = residual
    label_BboxNet[8:] = self.mean_car_size
    Rmat = np.asarray([[math.cos(residual), 0, math.sin(residual)], [0, 1, 0], [-math.sin(residual), 0, math.cos(residual)]], dtype='float32')
    center = label_BboxNet[0:3]
    l = label_3D['l']
    w = label_3D['w']
    h = label_3D['h']
    p0 = center + np.dot(Rmat, np.asarray([l / 2.0, 0, w / 2.0], dtype='float32').flatten())
    p1 = center + np.dot(Rmat, np.asarray([-l / 2.0, 0, w / 2.0], dtype='float32').flatten())
    p2 = center + np.dot(Rmat, np.asarray([-l / 2.0, 0, -w / 2.0], dtype='float32').flatten())
    p3 = center + np.dot(Rmat, np.asarray([l / 2.0, 0, -w / 2.0], dtype='float32').flatten())
    p4 = center + np.dot(Rmat, np.asarray([l / 2.0, -h, w / 2.0], dtype='float32').flatten())
    p5 = center + np.dot(Rmat, np.asarray([-l / 2.0, -h, w / 2.0], dtype='float32').flatten())
    p6 = center + np.dot(Rmat, np.asarray([-l / 2.0, -h, -w / 2.0], dtype='float32').flatten())
    p7 = center + np.dot(Rmat, np.asarray([l / 2.0, -h, -w / 2.0], dtype='float32').flatten())
    label_corner = np.array([p0, p1, p2, p3, p4, p5, p6, p7])
    label_corner_flipped = np.array([p2, p3, p0, p1, p6, p7, p4, p5])
    bbox_2d_img = bbox_2d_img / 255.0
    bbox_2d_img = bbox_2d_img - np.array([0.485, 0.456, 0.406])
    bbox_2d_img = bbox_2d_img / np.array([0.229, 0.224, 0.225])
    bbox_2d_img = np.transpose(bbox_2d_img, (2, 0, 1))
    bbox_2d_img = bbox_2d_img.astype(np.float32)
    centered_frustum_point_cloud_camera = torch.from_numpy(centered_frustum_point_cloud_camera)
    bbox_2d_img = torch.from_numpy(bbox_2d_img)
    label_InstanceSeg = torch.from_numpy(label_InstanceSeg)
    label_TNet = torch.from_numpy(label_TNet)
    label_BboxNet = torch.from_numpy(label_BboxNet)
    label_corner = torch.from_numpy(label_corner)
    label_corner_flipped = torch.from_numpy(label_corner_flipped)
    return (centered_frustum_point_cloud_camera, bbox_2d_img, label_InstanceSeg, label_TNet, label_BboxNet, label_corner, label_corner_flipped)

class EvalDatasetFrustumPointNetImg(torch.utils.data.Dataset):

    def __init__(self, kitti_data_path, kitti_meta_path, type, NH):
        self.img_dir = kitti_data_path + '/object/training/image_2/'
        self.label_dir = kitti_data_path + '/object/training/label_2/'
        self.calib_dir = kitti_data_path + '/object/training/calib/'
        self.lidar_dir = kitti_data_path + '/object/training/velodyne/'
        self.NH = NH
        with open(kitti_meta_path + '/%s_img_ids.pkl' % type, 'rb') as file:
            img_ids = pickle.load(file)
        with open(kitti_meta_path + '/kitti_train_mean_car_size.pkl', 'rb') as file:
            self.mean_car_size = pickle.load(file)
        with open(kitti_meta_path + '/kitti_centered_frustum_mean_xyz.pkl', 'rb') as file:
            self.centered_frustum_mean_xyz = pickle.load(file)
            self.centered_frustum_mean_xyz = self.centered_frustum_mean_xyz.astype(np.float32)
        self.examples = []
        for img_id in img_ids:
            labels = LabelLoader2D3D(img_id, self.label_dir, '.txt', self.calib_dir, '.txt')
            for label in labels:
                label_2d = label['label_2D']
                if label_2d['truncated'] < 0.5 and label_2d['class'] == 'Car':
                    label['img_id'] = img_id
                    self.examples.append(label)
        self.num_examples = len(self.examples)

    def __getitem__(self, index):
        example = self.examples[index]
        img_id = example['img_id']
        lidar_path = self.lidar_dir + img_id + '.bin'
        point_cloud = np.fromfile(lidar_path, dtype=np.float32).reshape(-1, 4)
        orig_point_cloud = point_cloud
        point_cloud = point_cloud[point_cloud[:, 0] > 0, :]
        point_cloud = point_cloud[point_cloud[:, 0] < 80, :]
        calib = calibread(self.calib_dir + img_id + '.txt')
        P2 = calib['P2']
        Tr_velo_to_cam_orig = calib['Tr_velo_to_cam']
        R0_rect_orig = calib['R0_rect']
        R0_rect = np.eye(4)
        R0_rect[0:3, 0:3] = R0_rect_orig
        Tr_velo_to_cam = np.eye(4)
        Tr_velo_to_cam[0:3, :] = Tr_velo_to_cam_orig
        point_cloud_xyz = point_cloud[:, 0:3]
        point_cloud_xyz_hom = np.ones((point_cloud.shape[0], 4))
        point_cloud_xyz_hom[:, 0:3] = point_cloud[:, 0:3]
        img_points_hom = np.dot(P2, np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T))).T
        img_points = np.zeros((img_points_hom.shape[0], 2))
        img_points[:, 0] = img_points_hom[:, 0] / img_points_hom[:, 2]
        img_points[:, 1] = img_points_hom[:, 1] / img_points_hom[:, 2]
        point_cloud_xyz_camera_hom = np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T)).T
        point_cloud_xyz_camera = np.zeros((point_cloud_xyz_camera_hom.shape[0], 3))
        point_cloud_xyz_camera[:, 0] = point_cloud_xyz_camera_hom[:, 0] / point_cloud_xyz_camera_hom[:, 3]
        point_cloud_xyz_camera[:, 1] = point_cloud_xyz_camera_hom[:, 1] / point_cloud_xyz_camera_hom[:, 3]
        point_cloud_xyz_camera[:, 2] = point_cloud_xyz_camera_hom[:, 2] / point_cloud_xyz_camera_hom[:, 3]
        point_cloud_camera = point_cloud
        point_cloud_camera[:, 0:3] = point_cloud_xyz_camera
        label_2D = example['label_2D']
        label_3D = example['label_3D']
        bbox = label_2D['poly']
        u_min = bbox[0, 0]
        u_max = bbox[1, 0]
        v_min = bbox[0, 1]
        v_max = bbox[2, 1]
        u_min_expanded = u_min
        u_max_expanded = u_max
        v_min_expanded = v_min
        v_max_expanded = v_max
        input_2Dbbox = np.array([u_min_expanded, u_max_expanded, v_min_expanded, v_max_expanded])
        row_mask = np.logical_and(np.logical_and(img_points[:, 0] >= u_min_expanded, img_points[:, 0] <= u_max_expanded), np.logical_and(img_points[:, 1] >= v_min_expanded, img_points[:, 1] <= v_max_expanded))
        frustum_point_cloud_xyz = point_cloud_xyz[row_mask, :]
        frustum_point_cloud = point_cloud[row_mask, :]
        frustum_point_cloud_xyz_camera = point_cloud_xyz_camera[row_mask, :]
        frustum_point_cloud_camera = point_cloud_camera[row_mask, :]
        if frustum_point_cloud.shape[0] == 0:
            print(img_id)
            print(frustum_point_cloud.shape)
            return self.__getitem__(0)
        if frustum_point_cloud.shape[0] < 1024:
            row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=True)
        else:
            row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=False)
        frustum_point_cloud_xyz = frustum_point_cloud_xyz[row_idx, :]
        frustum_point_cloud = frustum_point_cloud[row_idx, :]
        frustum_point_cloud_xyz_camera = frustum_point_cloud_xyz_camera[row_idx, :]
        frustum_point_cloud_camera = frustum_point_cloud_camera[row_idx, :]
        img_path = self.img_dir + img_id + '.png'
        img = cv2.imread(img_path, -1)
        bbox_2d_img = img[int(np.max([0, v_min])):int(v_max), int(np.max([0, u_min])):int(u_max)]
        bbox_2d_img = cv2.resize(bbox_2d_img, (224, 224))
        points = label_3D['points']
        y_max = points[0, 1]
        y_min = points[4, 1]
        A = np.array([points[0, 0], points[0, 2]])
        B = np.array([points[1, 0], points[1, 2]])
        D = np.array([points[3, 0], points[3, 2]])
        AB = B - A
        AD = D - A
        AB_dot_AB = np.dot(AB, AB)
        AD_dot_AD = np.dot(AD, AD)
        P = np.zeros((frustum_point_cloud_xyz_camera.shape[0], 2))
        P[:, 0] = frustum_point_cloud_xyz_camera[:, 0]
        P[:, 1] = frustum_point_cloud_xyz_camera[:, 2]
        AP = P - A
        AP_dot_AB = np.dot(AP, AB)
        AP_dot_AD = np.dot(AP, AD)
        row_mask = np.logical_and(np.logical_and(frustum_point_cloud_xyz_camera[:, 1] >= y_min, frustum_point_cloud_xyz_camera[:, 1] <= y_max), np.logical_and(np.logical_and(AP_dot_AB >= 0, AP_dot_AB <= AB_dot_AB), np.logical_and(AP_dot_AD >= 0, AP_dot_AD <= AD_dot_AD)))
        gt_point_cloud_xyz_camera = frustum_point_cloud_xyz_camera[row_mask, :]
        label_InstanceSeg = np.zeros((frustum_point_cloud.shape[0],), dtype=np.int64)
        label_InstanceSeg[row_mask] = 1
        u_center = u_min_expanded + (u_max_expanded - u_min_expanded) / 2.0
        v_center = v_min_expanded + (v_max_expanded - v_min_expanded) / 2.0
        center_img_point_hom = np.array([u_center, v_center, 1])
        P2_pseudo_inverse = np.linalg.pinv(P2)
        point_hom = np.dot(P2_pseudo_inverse, center_img_point_hom)
        point = np.array([point_hom[0] / point_hom[3], point_hom[1] / point_hom[3], point_hom[2] / point_hom[3]])
        if point[2] < 0:
            point[0] = -point[0]
            point[2] = -point[2]
        frustum_angle = np.arctan2(point[0], point[2])
        frustum_R = np.asarray([[np.cos(frustum_angle), 0, -np.sin(frustum_angle)], [0, 1, 0], [np.sin(frustum_angle), 0, np.cos(frustum_angle)]], dtype='float32')
        centered_frustum_point_cloud_xyz_camera = np.dot(frustum_R, frustum_point_cloud_xyz_camera.T).T
        centered_frustum_point_cloud_xyz_camera -= self.centered_frustum_mean_xyz
        centered_frustum_point_cloud_camera = frustum_point_cloud_camera
        centered_frustum_point_cloud_camera[:, 0:3] = centered_frustum_point_cloud_xyz_camera
        label_TNet = np.dot(frustum_R, label_3D['center']) - self.centered_frustum_mean_xyz
        centered_r_y = wrapToPi(label_3D['r_y'] - frustum_angle)
        bin_number = getBinNumber(centered_r_y, NH=self.NH)
        bin_center = getBinCenter(bin_number, NH=self.NH)
        residual = wrapToPi(centered_r_y - bin_center)
        label_BboxNet = np.zeros((11,), dtype=np.float32)
        label_BboxNet[0:3] = np.dot(frustum_R, label_3D['center']) - self.centered_frustum_mean_xyz
        label_BboxNet[3] = label_3D['h']
        label_BboxNet[4] = label_3D['w']
        label_BboxNet[5] = label_3D['l']
        label_BboxNet[6] = bin_number
        label_BboxNet[7] = residual
        label_BboxNet[8:] = self.mean_car_size
        Rmat = np.asarray([[math.cos(residual), 0, math.sin(residual)], [0, 1, 0], [-math.sin(residual), 0, math.cos(residual)]], dtype='float32')
        center = label_BboxNet[0:3]
        l = label_3D['l']
        w = label_3D['w']
        h = label_3D['h']
        p0 = center + np.dot(Rmat, np.asarray([l / 2.0, 0, w / 2.0], dtype='float32').flatten())
        p1 = center + np.dot(Rmat, np.asarray([-l / 2.0, 0, w / 2.0], dtype='float32').flatten())
        p2 = center + np.dot(Rmat, np.asarray([-l / 2.0, 0, -w / 2.0], dtype='float32').flatten())
        p3 = center + np.dot(Rmat, np.asarray([l / 2.0, 0, -w / 2.0], dtype='float32').flatten())
        p4 = center + np.dot(Rmat, np.asarray([l / 2.0, -h, w / 2.0], dtype='float32').flatten())
        p5 = center + np.dot(Rmat, np.asarray([-l / 2.0, -h, w / 2.0], dtype='float32').flatten())
        p6 = center + np.dot(Rmat, np.asarray([-l / 2.0, -h, -w / 2.0], dtype='float32').flatten())
        p7 = center + np.dot(Rmat, np.asarray([l / 2.0, -h, -w / 2.0], dtype='float32').flatten())
        label_corner = np.array([p0, p1, p2, p3, p4, p5, p6, p7])
        label_corner_flipped = np.array([p2, p3, p0, p1, p6, p7, p4, p5])
        bbox_2d_img = bbox_2d_img / 255.0
        bbox_2d_img = bbox_2d_img - np.array([0.485, 0.456, 0.406])
        bbox_2d_img = bbox_2d_img / np.array([0.229, 0.224, 0.225])
        bbox_2d_img = np.transpose(bbox_2d_img, (2, 0, 1))
        bbox_2d_img = bbox_2d_img.astype(np.float32)
        centered_frustum_point_cloud_camera = torch.from_numpy(centered_frustum_point_cloud_camera)
        bbox_2d_img = torch.from_numpy(bbox_2d_img)
        label_InstanceSeg = torch.from_numpy(label_InstanceSeg)
        label_TNet = torch.from_numpy(label_TNet)
        label_BboxNet = torch.from_numpy(label_BboxNet)
        label_corner = torch.from_numpy(label_corner)
        label_corner_flipped = torch.from_numpy(label_corner_flipped)
        return (centered_frustum_point_cloud_camera, bbox_2d_img, label_InstanceSeg, label_TNet, label_BboxNet, label_corner, label_corner_flipped, img_id, input_2Dbbox, frustum_R, frustum_angle, self.centered_frustum_mean_xyz)

    def __len__(self):
        return self.num_examples

def __getitem__(self, index):
    example = self.examples[index]
    img_id = example['img_id']
    lidar_path = self.lidar_dir + img_id + '.bin'
    point_cloud = np.fromfile(lidar_path, dtype=np.float32).reshape(-1, 4)
    orig_point_cloud = point_cloud
    point_cloud = point_cloud[point_cloud[:, 0] > 0, :]
    point_cloud = point_cloud[point_cloud[:, 0] < 80, :]
    calib = calibread(self.calib_dir + img_id + '.txt')
    P2 = calib['P2']
    Tr_velo_to_cam_orig = calib['Tr_velo_to_cam']
    R0_rect_orig = calib['R0_rect']
    R0_rect = np.eye(4)
    R0_rect[0:3, 0:3] = R0_rect_orig
    Tr_velo_to_cam = np.eye(4)
    Tr_velo_to_cam[0:3, :] = Tr_velo_to_cam_orig
    point_cloud_xyz = point_cloud[:, 0:3]
    point_cloud_xyz_hom = np.ones((point_cloud.shape[0], 4))
    point_cloud_xyz_hom[:, 0:3] = point_cloud[:, 0:3]
    img_points_hom = np.dot(P2, np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T))).T
    img_points = np.zeros((img_points_hom.shape[0], 2))
    img_points[:, 0] = img_points_hom[:, 0] / img_points_hom[:, 2]
    img_points[:, 1] = img_points_hom[:, 1] / img_points_hom[:, 2]
    point_cloud_xyz_camera_hom = np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T)).T
    point_cloud_xyz_camera = np.zeros((point_cloud_xyz_camera_hom.shape[0], 3))
    point_cloud_xyz_camera[:, 0] = point_cloud_xyz_camera_hom[:, 0] / point_cloud_xyz_camera_hom[:, 3]
    point_cloud_xyz_camera[:, 1] = point_cloud_xyz_camera_hom[:, 1] / point_cloud_xyz_camera_hom[:, 3]
    point_cloud_xyz_camera[:, 2] = point_cloud_xyz_camera_hom[:, 2] / point_cloud_xyz_camera_hom[:, 3]
    point_cloud_camera = point_cloud
    point_cloud_camera[:, 0:3] = point_cloud_xyz_camera
    label_2D = example['label_2D']
    label_3D = example['label_3D']
    bbox = label_2D['poly']
    u_min = bbox[0, 0]
    u_max = bbox[1, 0]
    v_min = bbox[0, 1]
    v_max = bbox[2, 1]
    u_min_expanded = u_min
    u_max_expanded = u_max
    v_min_expanded = v_min
    v_max_expanded = v_max
    input_2Dbbox = np.array([u_min_expanded, u_max_expanded, v_min_expanded, v_max_expanded])
    row_mask = np.logical_and(np.logical_and(img_points[:, 0] >= u_min_expanded, img_points[:, 0] <= u_max_expanded), np.logical_and(img_points[:, 1] >= v_min_expanded, img_points[:, 1] <= v_max_expanded))
    frustum_point_cloud_xyz = point_cloud_xyz[row_mask, :]
    frustum_point_cloud = point_cloud[row_mask, :]
    frustum_point_cloud_xyz_camera = point_cloud_xyz_camera[row_mask, :]
    frustum_point_cloud_camera = point_cloud_camera[row_mask, :]
    if frustum_point_cloud.shape[0] == 0:
        print(img_id)
        print(frustum_point_cloud.shape)
        return self.__getitem__(0)
    if frustum_point_cloud.shape[0] < 1024:
        row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=True)
    else:
        row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=False)
    frustum_point_cloud_xyz = frustum_point_cloud_xyz[row_idx, :]
    frustum_point_cloud = frustum_point_cloud[row_idx, :]
    frustum_point_cloud_xyz_camera = frustum_point_cloud_xyz_camera[row_idx, :]
    frustum_point_cloud_camera = frustum_point_cloud_camera[row_idx, :]
    img_path = self.img_dir + img_id + '.png'
    img = cv2.imread(img_path, -1)
    bbox_2d_img = img[int(np.max([0, v_min])):int(v_max), int(np.max([0, u_min])):int(u_max)]
    bbox_2d_img = cv2.resize(bbox_2d_img, (224, 224))
    points = label_3D['points']
    y_max = points[0, 1]
    y_min = points[4, 1]
    A = np.array([points[0, 0], points[0, 2]])
    B = np.array([points[1, 0], points[1, 2]])
    D = np.array([points[3, 0], points[3, 2]])
    AB = B - A
    AD = D - A
    AB_dot_AB = np.dot(AB, AB)
    AD_dot_AD = np.dot(AD, AD)
    P = np.zeros((frustum_point_cloud_xyz_camera.shape[0], 2))
    P[:, 0] = frustum_point_cloud_xyz_camera[:, 0]
    P[:, 1] = frustum_point_cloud_xyz_camera[:, 2]
    AP = P - A
    AP_dot_AB = np.dot(AP, AB)
    AP_dot_AD = np.dot(AP, AD)
    row_mask = np.logical_and(np.logical_and(frustum_point_cloud_xyz_camera[:, 1] >= y_min, frustum_point_cloud_xyz_camera[:, 1] <= y_max), np.logical_and(np.logical_and(AP_dot_AB >= 0, AP_dot_AB <= AB_dot_AB), np.logical_and(AP_dot_AD >= 0, AP_dot_AD <= AD_dot_AD)))
    gt_point_cloud_xyz_camera = frustum_point_cloud_xyz_camera[row_mask, :]
    label_InstanceSeg = np.zeros((frustum_point_cloud.shape[0],), dtype=np.int64)
    label_InstanceSeg[row_mask] = 1
    u_center = u_min_expanded + (u_max_expanded - u_min_expanded) / 2.0
    v_center = v_min_expanded + (v_max_expanded - v_min_expanded) / 2.0
    center_img_point_hom = np.array([u_center, v_center, 1])
    P2_pseudo_inverse = np.linalg.pinv(P2)
    point_hom = np.dot(P2_pseudo_inverse, center_img_point_hom)
    point = np.array([point_hom[0] / point_hom[3], point_hom[1] / point_hom[3], point_hom[2] / point_hom[3]])
    if point[2] < 0:
        point[0] = -point[0]
        point[2] = -point[2]
    frustum_angle = np.arctan2(point[0], point[2])
    frustum_R = np.asarray([[np.cos(frustum_angle), 0, -np.sin(frustum_angle)], [0, 1, 0], [np.sin(frustum_angle), 0, np.cos(frustum_angle)]], dtype='float32')
    centered_frustum_point_cloud_xyz_camera = np.dot(frustum_R, frustum_point_cloud_xyz_camera.T).T
    centered_frustum_point_cloud_xyz_camera -= self.centered_frustum_mean_xyz
    centered_frustum_point_cloud_camera = frustum_point_cloud_camera
    centered_frustum_point_cloud_camera[:, 0:3] = centered_frustum_point_cloud_xyz_camera
    label_TNet = np.dot(frustum_R, label_3D['center']) - self.centered_frustum_mean_xyz
    centered_r_y = wrapToPi(label_3D['r_y'] - frustum_angle)
    bin_number = getBinNumber(centered_r_y, NH=self.NH)
    bin_center = getBinCenter(bin_number, NH=self.NH)
    residual = wrapToPi(centered_r_y - bin_center)
    label_BboxNet = np.zeros((11,), dtype=np.float32)
    label_BboxNet[0:3] = np.dot(frustum_R, label_3D['center']) - self.centered_frustum_mean_xyz
    label_BboxNet[3] = label_3D['h']
    label_BboxNet[4] = label_3D['w']
    label_BboxNet[5] = label_3D['l']
    label_BboxNet[6] = bin_number
    label_BboxNet[7] = residual
    label_BboxNet[8:] = self.mean_car_size
    Rmat = np.asarray([[math.cos(residual), 0, math.sin(residual)], [0, 1, 0], [-math.sin(residual), 0, math.cos(residual)]], dtype='float32')
    center = label_BboxNet[0:3]
    l = label_3D['l']
    w = label_3D['w']
    h = label_3D['h']
    p0 = center + np.dot(Rmat, np.asarray([l / 2.0, 0, w / 2.0], dtype='float32').flatten())
    p1 = center + np.dot(Rmat, np.asarray([-l / 2.0, 0, w / 2.0], dtype='float32').flatten())
    p2 = center + np.dot(Rmat, np.asarray([-l / 2.0, 0, -w / 2.0], dtype='float32').flatten())
    p3 = center + np.dot(Rmat, np.asarray([l / 2.0, 0, -w / 2.0], dtype='float32').flatten())
    p4 = center + np.dot(Rmat, np.asarray([l / 2.0, -h, w / 2.0], dtype='float32').flatten())
    p5 = center + np.dot(Rmat, np.asarray([-l / 2.0, -h, w / 2.0], dtype='float32').flatten())
    p6 = center + np.dot(Rmat, np.asarray([-l / 2.0, -h, -w / 2.0], dtype='float32').flatten())
    p7 = center + np.dot(Rmat, np.asarray([l / 2.0, -h, -w / 2.0], dtype='float32').flatten())
    label_corner = np.array([p0, p1, p2, p3, p4, p5, p6, p7])
    label_corner_flipped = np.array([p2, p3, p0, p1, p6, p7, p4, p5])
    bbox_2d_img = bbox_2d_img / 255.0
    bbox_2d_img = bbox_2d_img - np.array([0.485, 0.456, 0.406])
    bbox_2d_img = bbox_2d_img / np.array([0.229, 0.224, 0.225])
    bbox_2d_img = np.transpose(bbox_2d_img, (2, 0, 1))
    bbox_2d_img = bbox_2d_img.astype(np.float32)
    centered_frustum_point_cloud_camera = torch.from_numpy(centered_frustum_point_cloud_camera)
    bbox_2d_img = torch.from_numpy(bbox_2d_img)
    label_InstanceSeg = torch.from_numpy(label_InstanceSeg)
    label_TNet = torch.from_numpy(label_TNet)
    label_BboxNet = torch.from_numpy(label_BboxNet)
    label_corner = torch.from_numpy(label_corner)
    label_corner_flipped = torch.from_numpy(label_corner_flipped)
    return (centered_frustum_point_cloud_camera, bbox_2d_img, label_InstanceSeg, label_TNet, label_BboxNet, label_corner, label_corner_flipped, img_id, input_2Dbbox, frustum_R, frustum_angle, self.centered_frustum_mean_xyz)

class EvalSequenceDatasetFrustumPointNetImg(torch.utils.data.Dataset):

    def __init__(self, kitti_data_path, kitti_meta_path, NH, sequence):
        self.img_dir = kitti_data_path + '/tracking/training/image_02/' + sequence + '/'
        self.lidar_dir = kitti_data_path + '/tracking/training/velodyne/' + sequence + '/'
        self.label_path = kitti_data_path + '/tracking/training/label_02/' + sequence + '.txt'
        self.calib_path = kitti_meta_path + '/tracking/training/calib/' + sequence + '.txt'
        self.NH = NH
        with open(kitti_meta_path + '/kitti_train_mean_car_size.pkl', 'rb') as file:
            self.mean_car_size = pickle.load(file)
        with open(kitti_meta_path + '/kitti_centered_frustum_mean_xyz.pkl', 'rb') as file:
            self.centered_frustum_mean_xyz = pickle.load(file)
            self.centered_frustum_mean_xyz = self.centered_frustum_mean_xyz.astype(np.float32)
        img_ids = []
        img_names = os.listdir(self.img_dir)
        for img_name in img_names:
            img_id = img_name.split('.png')[0]
            img_ids.append(img_id)
        self.examples = []
        for img_id in img_ids:
            if img_id.lstrip('0') == '':
                img_id_float = 0.0
            else:
                img_id_float = float(img_id.lstrip('0'))
            labels = LabelLoader2D3D_sequence(img_id, img_id_float, self.label_path, self.calib_path)
            for label in labels:
                label_2d = label['label_2D']
                if label_2d['truncated'] < 0.5 and label_2d['class'] == 'Car':
                    label['img_id'] = img_id
                    self.examples.append(label)
        self.num_examples = len(self.examples)

    def __getitem__(self, index):
        example = self.examples[index]
        img_id = example['img_id']
        lidar_path = self.lidar_dir + img_id + '.bin'
        point_cloud = np.fromfile(lidar_path, dtype=np.float32).reshape(-1, 4)
        orig_point_cloud = point_cloud
        point_cloud = point_cloud[point_cloud[:, 0] > 0, :]
        point_cloud = point_cloud[point_cloud[:, 0] < 80, :]
        calib = calibread(self.calib_path)
        P2 = calib['P2']
        Tr_velo_to_cam_orig = calib['Tr_velo_to_cam']
        R0_rect_orig = calib['R0_rect']
        R0_rect = np.eye(4)
        R0_rect[0:3, 0:3] = R0_rect_orig
        Tr_velo_to_cam = np.eye(4)
        Tr_velo_to_cam[0:3, :] = Tr_velo_to_cam_orig
        point_cloud_xyz = point_cloud[:, 0:3]
        point_cloud_xyz_hom = np.ones((point_cloud.shape[0], 4))
        point_cloud_xyz_hom[:, 0:3] = point_cloud[:, 0:3]
        img_points_hom = np.dot(P2, np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T))).T
        img_points = np.zeros((img_points_hom.shape[0], 2))
        img_points[:, 0] = img_points_hom[:, 0] / img_points_hom[:, 2]
        img_points[:, 1] = img_points_hom[:, 1] / img_points_hom[:, 2]
        point_cloud_xyz_camera_hom = np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T)).T
        point_cloud_xyz_camera = np.zeros((point_cloud_xyz_camera_hom.shape[0], 3))
        point_cloud_xyz_camera[:, 0] = point_cloud_xyz_camera_hom[:, 0] / point_cloud_xyz_camera_hom[:, 3]
        point_cloud_xyz_camera[:, 1] = point_cloud_xyz_camera_hom[:, 1] / point_cloud_xyz_camera_hom[:, 3]
        point_cloud_xyz_camera[:, 2] = point_cloud_xyz_camera_hom[:, 2] / point_cloud_xyz_camera_hom[:, 3]
        point_cloud_camera = point_cloud
        point_cloud_camera[:, 0:3] = point_cloud_xyz_camera
        label_2D = example['label_2D']
        label_3D = example['label_3D']
        bbox = label_2D['poly']
        u_min = bbox[0, 0]
        u_max = bbox[1, 0]
        v_min = bbox[0, 1]
        v_max = bbox[2, 1]
        u_min_expanded = u_min
        u_max_expanded = u_max
        v_min_expanded = v_min
        v_max_expanded = v_max
        input_2Dbbox = np.array([u_min_expanded, u_max_expanded, v_min_expanded, v_max_expanded])
        row_mask = np.logical_and(np.logical_and(img_points[:, 0] >= u_min_expanded, img_points[:, 0] <= u_max_expanded), np.logical_and(img_points[:, 1] >= v_min_expanded, img_points[:, 1] <= v_max_expanded))
        frustum_point_cloud_xyz = point_cloud_xyz[row_mask, :]
        frustum_point_cloud = point_cloud[row_mask, :]
        frustum_point_cloud_xyz_camera = point_cloud_xyz_camera[row_mask, :]
        frustum_point_cloud_camera = point_cloud_camera[row_mask, :]
        if frustum_point_cloud.shape[0] == 0:
            print(img_id)
            print(frustum_point_cloud.shape)
            return self.__getitem__(0)
        if frustum_point_cloud.shape[0] < 1024:
            row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=True)
        else:
            row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=False)
        frustum_point_cloud_xyz = frustum_point_cloud_xyz[row_idx, :]
        frustum_point_cloud = frustum_point_cloud[row_idx, :]
        frustum_point_cloud_xyz_camera = frustum_point_cloud_xyz_camera[row_idx, :]
        frustum_point_cloud_camera = frustum_point_cloud_camera[row_idx, :]
        img_path = self.img_dir + img_id + '.png'
        img = cv2.imread(img_path, -1)
        bbox_2d_img = img[int(np.max([0, v_min])):int(v_max), int(np.max([0, u_min])):int(u_max)]
        bbox_2d_img = cv2.resize(bbox_2d_img, (224, 224))
        points = label_3D['points']
        y_max = points[0, 1]
        y_min = points[4, 1]
        A = np.array([points[0, 0], points[0, 2]])
        B = np.array([points[1, 0], points[1, 2]])
        D = np.array([points[3, 0], points[3, 2]])
        AB = B - A
        AD = D - A
        AB_dot_AB = np.dot(AB, AB)
        AD_dot_AD = np.dot(AD, AD)
        P = np.zeros((frustum_point_cloud_xyz_camera.shape[0], 2))
        P[:, 0] = frustum_point_cloud_xyz_camera[:, 0]
        P[:, 1] = frustum_point_cloud_xyz_camera[:, 2]
        AP = P - A
        AP_dot_AB = np.dot(AP, AB)
        AP_dot_AD = np.dot(AP, AD)
        row_mask = np.logical_and(np.logical_and(frustum_point_cloud_xyz_camera[:, 1] >= y_min, frustum_point_cloud_xyz_camera[:, 1] <= y_max), np.logical_and(np.logical_and(AP_dot_AB >= 0, AP_dot_AB <= AB_dot_AB), np.logical_and(AP_dot_AD >= 0, AP_dot_AD <= AD_dot_AD)))
        gt_point_cloud_xyz_camera = frustum_point_cloud_xyz_camera[row_mask, :]
        label_InstanceSeg = np.zeros((frustum_point_cloud.shape[0],), dtype=np.int64)
        label_InstanceSeg[row_mask] = 1
        u_center = u_min_expanded + (u_max_expanded - u_min_expanded) / 2.0
        v_center = v_min_expanded + (v_max_expanded - v_min_expanded) / 2.0
        center_img_point_hom = np.array([u_center, v_center, 1])
        P2_pseudo_inverse = np.linalg.pinv(P2)
        point_hom = np.dot(P2_pseudo_inverse, center_img_point_hom)
        point = np.array([point_hom[0] / point_hom[3], point_hom[1] / point_hom[3], point_hom[2] / point_hom[3]])
        if point[2] < 0:
            point[0] = -point[0]
            point[2] = -point[2]
        frustum_angle = np.arctan2(point[0], point[2])
        frustum_R = np.asarray([[np.cos(frustum_angle), 0, -np.sin(frustum_angle)], [0, 1, 0], [np.sin(frustum_angle), 0, np.cos(frustum_angle)]], dtype='float32')
        centered_frustum_point_cloud_xyz_camera = np.dot(frustum_R, frustum_point_cloud_xyz_camera.T).T
        centered_frustum_point_cloud_xyz_camera -= self.centered_frustum_mean_xyz
        centered_frustum_point_cloud_camera = frustum_point_cloud_camera
        centered_frustum_point_cloud_camera[:, 0:3] = centered_frustum_point_cloud_xyz_camera
        label_TNet = np.dot(frustum_R, label_3D['center']) - self.centered_frustum_mean_xyz
        centered_r_y = wrapToPi(label_3D['r_y'] - frustum_angle)
        bin_number = getBinNumber(centered_r_y, NH=self.NH)
        bin_center = getBinCenter(bin_number, NH=self.NH)
        residual = wrapToPi(centered_r_y - bin_center)
        label_BboxNet = np.zeros((11,), dtype=np.float32)
        label_BboxNet[0:3] = np.dot(frustum_R, label_3D['center']) - self.centered_frustum_mean_xyz
        label_BboxNet[3] = label_3D['h']
        label_BboxNet[4] = label_3D['w']
        label_BboxNet[5] = label_3D['l']
        label_BboxNet[6] = bin_number
        label_BboxNet[7] = residual
        label_BboxNet[8:] = self.mean_car_size
        Rmat = np.asarray([[math.cos(residual), 0, math.sin(residual)], [0, 1, 0], [-math.sin(residual), 0, math.cos(residual)]], dtype='float32')
        center = label_BboxNet[0:3]
        l = label_3D['l']
        w = label_3D['w']
        h = label_3D['h']
        p0 = center + np.dot(Rmat, np.asarray([l / 2.0, 0, w / 2.0], dtype='float32').flatten())
        p1 = center + np.dot(Rmat, np.asarray([-l / 2.0, 0, w / 2.0], dtype='float32').flatten())
        p2 = center + np.dot(Rmat, np.asarray([-l / 2.0, 0, -w / 2.0], dtype='float32').flatten())
        p3 = center + np.dot(Rmat, np.asarray([l / 2.0, 0, -w / 2.0], dtype='float32').flatten())
        p4 = center + np.dot(Rmat, np.asarray([l / 2.0, -h, w / 2.0], dtype='float32').flatten())
        p5 = center + np.dot(Rmat, np.asarray([-l / 2.0, -h, w / 2.0], dtype='float32').flatten())
        p6 = center + np.dot(Rmat, np.asarray([-l / 2.0, -h, -w / 2.0], dtype='float32').flatten())
        p7 = center + np.dot(Rmat, np.asarray([l / 2.0, -h, -w / 2.0], dtype='float32').flatten())
        label_corner = np.array([p0, p1, p2, p3, p4, p5, p6, p7])
        label_corner_flipped = np.array([p2, p3, p0, p1, p6, p7, p4, p5])
        bbox_2d_img = bbox_2d_img / 255.0
        bbox_2d_img = bbox_2d_img - np.array([0.485, 0.456, 0.406])
        bbox_2d_img = bbox_2d_img / np.array([0.229, 0.224, 0.225])
        bbox_2d_img = np.transpose(bbox_2d_img, (2, 0, 1))
        bbox_2d_img = bbox_2d_img.astype(np.float32)
        centered_frustum_point_cloud_camera = torch.from_numpy(centered_frustum_point_cloud_camera)
        bbox_2d_img = torch.from_numpy(bbox_2d_img)
        label_InstanceSeg = torch.from_numpy(label_InstanceSeg)
        label_TNet = torch.from_numpy(label_TNet)
        label_BboxNet = torch.from_numpy(label_BboxNet)
        label_corner = torch.from_numpy(label_corner)
        label_corner_flipped = torch.from_numpy(label_corner_flipped)
        return (centered_frustum_point_cloud_camera, bbox_2d_img, label_InstanceSeg, label_TNet, label_BboxNet, label_corner, label_corner_flipped, img_id, input_2Dbbox, frustum_R, frustum_angle, self.centered_frustum_mean_xyz)

    def __len__(self):
        return self.num_examples

def __getitem__(self, index):
    example = self.examples[index]
    img_id = example['img_id']
    lidar_path = self.lidar_dir + img_id + '.bin'
    point_cloud = np.fromfile(lidar_path, dtype=np.float32).reshape(-1, 4)
    orig_point_cloud = point_cloud
    point_cloud = point_cloud[point_cloud[:, 0] > 0, :]
    point_cloud = point_cloud[point_cloud[:, 0] < 80, :]
    calib = calibread(self.calib_path)
    P2 = calib['P2']
    Tr_velo_to_cam_orig = calib['Tr_velo_to_cam']
    R0_rect_orig = calib['R0_rect']
    R0_rect = np.eye(4)
    R0_rect[0:3, 0:3] = R0_rect_orig
    Tr_velo_to_cam = np.eye(4)
    Tr_velo_to_cam[0:3, :] = Tr_velo_to_cam_orig
    point_cloud_xyz = point_cloud[:, 0:3]
    point_cloud_xyz_hom = np.ones((point_cloud.shape[0], 4))
    point_cloud_xyz_hom[:, 0:3] = point_cloud[:, 0:3]
    img_points_hom = np.dot(P2, np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T))).T
    img_points = np.zeros((img_points_hom.shape[0], 2))
    img_points[:, 0] = img_points_hom[:, 0] / img_points_hom[:, 2]
    img_points[:, 1] = img_points_hom[:, 1] / img_points_hom[:, 2]
    point_cloud_xyz_camera_hom = np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T)).T
    point_cloud_xyz_camera = np.zeros((point_cloud_xyz_camera_hom.shape[0], 3))
    point_cloud_xyz_camera[:, 0] = point_cloud_xyz_camera_hom[:, 0] / point_cloud_xyz_camera_hom[:, 3]
    point_cloud_xyz_camera[:, 1] = point_cloud_xyz_camera_hom[:, 1] / point_cloud_xyz_camera_hom[:, 3]
    point_cloud_xyz_camera[:, 2] = point_cloud_xyz_camera_hom[:, 2] / point_cloud_xyz_camera_hom[:, 3]
    point_cloud_camera = point_cloud
    point_cloud_camera[:, 0:3] = point_cloud_xyz_camera
    label_2D = example['label_2D']
    label_3D = example['label_3D']
    bbox = label_2D['poly']
    u_min = bbox[0, 0]
    u_max = bbox[1, 0]
    v_min = bbox[0, 1]
    v_max = bbox[2, 1]
    u_min_expanded = u_min
    u_max_expanded = u_max
    v_min_expanded = v_min
    v_max_expanded = v_max
    input_2Dbbox = np.array([u_min_expanded, u_max_expanded, v_min_expanded, v_max_expanded])
    row_mask = np.logical_and(np.logical_and(img_points[:, 0] >= u_min_expanded, img_points[:, 0] <= u_max_expanded), np.logical_and(img_points[:, 1] >= v_min_expanded, img_points[:, 1] <= v_max_expanded))
    frustum_point_cloud_xyz = point_cloud_xyz[row_mask, :]
    frustum_point_cloud = point_cloud[row_mask, :]
    frustum_point_cloud_xyz_camera = point_cloud_xyz_camera[row_mask, :]
    frustum_point_cloud_camera = point_cloud_camera[row_mask, :]
    if frustum_point_cloud.shape[0] == 0:
        print(img_id)
        print(frustum_point_cloud.shape)
        return self.__getitem__(0)
    if frustum_point_cloud.shape[0] < 1024:
        row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=True)
    else:
        row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=False)
    frustum_point_cloud_xyz = frustum_point_cloud_xyz[row_idx, :]
    frustum_point_cloud = frustum_point_cloud[row_idx, :]
    frustum_point_cloud_xyz_camera = frustum_point_cloud_xyz_camera[row_idx, :]
    frustum_point_cloud_camera = frustum_point_cloud_camera[row_idx, :]
    img_path = self.img_dir + img_id + '.png'
    img = cv2.imread(img_path, -1)
    bbox_2d_img = img[int(np.max([0, v_min])):int(v_max), int(np.max([0, u_min])):int(u_max)]
    bbox_2d_img = cv2.resize(bbox_2d_img, (224, 224))
    points = label_3D['points']
    y_max = points[0, 1]
    y_min = points[4, 1]
    A = np.array([points[0, 0], points[0, 2]])
    B = np.array([points[1, 0], points[1, 2]])
    D = np.array([points[3, 0], points[3, 2]])
    AB = B - A
    AD = D - A
    AB_dot_AB = np.dot(AB, AB)
    AD_dot_AD = np.dot(AD, AD)
    P = np.zeros((frustum_point_cloud_xyz_camera.shape[0], 2))
    P[:, 0] = frustum_point_cloud_xyz_camera[:, 0]
    P[:, 1] = frustum_point_cloud_xyz_camera[:, 2]
    AP = P - A
    AP_dot_AB = np.dot(AP, AB)
    AP_dot_AD = np.dot(AP, AD)
    row_mask = np.logical_and(np.logical_and(frustum_point_cloud_xyz_camera[:, 1] >= y_min, frustum_point_cloud_xyz_camera[:, 1] <= y_max), np.logical_and(np.logical_and(AP_dot_AB >= 0, AP_dot_AB <= AB_dot_AB), np.logical_and(AP_dot_AD >= 0, AP_dot_AD <= AD_dot_AD)))
    gt_point_cloud_xyz_camera = frustum_point_cloud_xyz_camera[row_mask, :]
    label_InstanceSeg = np.zeros((frustum_point_cloud.shape[0],), dtype=np.int64)
    label_InstanceSeg[row_mask] = 1
    u_center = u_min_expanded + (u_max_expanded - u_min_expanded) / 2.0
    v_center = v_min_expanded + (v_max_expanded - v_min_expanded) / 2.0
    center_img_point_hom = np.array([u_center, v_center, 1])
    P2_pseudo_inverse = np.linalg.pinv(P2)
    point_hom = np.dot(P2_pseudo_inverse, center_img_point_hom)
    point = np.array([point_hom[0] / point_hom[3], point_hom[1] / point_hom[3], point_hom[2] / point_hom[3]])
    if point[2] < 0:
        point[0] = -point[0]
        point[2] = -point[2]
    frustum_angle = np.arctan2(point[0], point[2])
    frustum_R = np.asarray([[np.cos(frustum_angle), 0, -np.sin(frustum_angle)], [0, 1, 0], [np.sin(frustum_angle), 0, np.cos(frustum_angle)]], dtype='float32')
    centered_frustum_point_cloud_xyz_camera = np.dot(frustum_R, frustum_point_cloud_xyz_camera.T).T
    centered_frustum_point_cloud_xyz_camera -= self.centered_frustum_mean_xyz
    centered_frustum_point_cloud_camera = frustum_point_cloud_camera
    centered_frustum_point_cloud_camera[:, 0:3] = centered_frustum_point_cloud_xyz_camera
    label_TNet = np.dot(frustum_R, label_3D['center']) - self.centered_frustum_mean_xyz
    centered_r_y = wrapToPi(label_3D['r_y'] - frustum_angle)
    bin_number = getBinNumber(centered_r_y, NH=self.NH)
    bin_center = getBinCenter(bin_number, NH=self.NH)
    residual = wrapToPi(centered_r_y - bin_center)
    label_BboxNet = np.zeros((11,), dtype=np.float32)
    label_BboxNet[0:3] = np.dot(frustum_R, label_3D['center']) - self.centered_frustum_mean_xyz
    label_BboxNet[3] = label_3D['h']
    label_BboxNet[4] = label_3D['w']
    label_BboxNet[5] = label_3D['l']
    label_BboxNet[6] = bin_number
    label_BboxNet[7] = residual
    label_BboxNet[8:] = self.mean_car_size
    Rmat = np.asarray([[math.cos(residual), 0, math.sin(residual)], [0, 1, 0], [-math.sin(residual), 0, math.cos(residual)]], dtype='float32')
    center = label_BboxNet[0:3]
    l = label_3D['l']
    w = label_3D['w']
    h = label_3D['h']
    p0 = center + np.dot(Rmat, np.asarray([l / 2.0, 0, w / 2.0], dtype='float32').flatten())
    p1 = center + np.dot(Rmat, np.asarray([-l / 2.0, 0, w / 2.0], dtype='float32').flatten())
    p2 = center + np.dot(Rmat, np.asarray([-l / 2.0, 0, -w / 2.0], dtype='float32').flatten())
    p3 = center + np.dot(Rmat, np.asarray([l / 2.0, 0, -w / 2.0], dtype='float32').flatten())
    p4 = center + np.dot(Rmat, np.asarray([l / 2.0, -h, w / 2.0], dtype='float32').flatten())
    p5 = center + np.dot(Rmat, np.asarray([-l / 2.0, -h, w / 2.0], dtype='float32').flatten())
    p6 = center + np.dot(Rmat, np.asarray([-l / 2.0, -h, -w / 2.0], dtype='float32').flatten())
    p7 = center + np.dot(Rmat, np.asarray([l / 2.0, -h, -w / 2.0], dtype='float32').flatten())
    label_corner = np.array([p0, p1, p2, p3, p4, p5, p6, p7])
    label_corner_flipped = np.array([p2, p3, p0, p1, p6, p7, p4, p5])
    bbox_2d_img = bbox_2d_img / 255.0
    bbox_2d_img = bbox_2d_img - np.array([0.485, 0.456, 0.406])
    bbox_2d_img = bbox_2d_img / np.array([0.229, 0.224, 0.225])
    bbox_2d_img = np.transpose(bbox_2d_img, (2, 0, 1))
    bbox_2d_img = bbox_2d_img.astype(np.float32)
    centered_frustum_point_cloud_camera = torch.from_numpy(centered_frustum_point_cloud_camera)
    bbox_2d_img = torch.from_numpy(bbox_2d_img)
    label_InstanceSeg = torch.from_numpy(label_InstanceSeg)
    label_TNet = torch.from_numpy(label_TNet)
    label_BboxNet = torch.from_numpy(label_BboxNet)
    label_corner = torch.from_numpy(label_corner)
    label_corner_flipped = torch.from_numpy(label_corner_flipped)
    return (centered_frustum_point_cloud_camera, bbox_2d_img, label_InstanceSeg, label_TNet, label_BboxNet, label_corner, label_corner_flipped, img_id, input_2Dbbox, frustum_R, frustum_angle, self.centered_frustum_mean_xyz)

class DatasetKittiTestSequence(torch.utils.data.Dataset):

    def __init__(self, kitti_data_path, kitti_meta_path, NH, sequence):
        self.img_dir = kitti_data_path + '/tracking/testing/image_02/' + sequence + '/'
        self.lidar_dir = kitti_data_path + '/tracking/testing/velodyne/' + sequence + '/'
        self.calib_path = kitti_meta_path + '/tracking/testing/calib/' + sequence + '.txt'
        self.detections_2d_path = kitti_meta_path + '/tracking/testing/2d_detections/' + sequence + '/inferResult_1.txt'
        self.NH = NH
        with open(kitti_meta_path + '/kitti_train_mean_car_size.pkl', 'rb') as file:
            self.mean_car_size = pickle.load(file)
        with open(kitti_meta_path + '/kitti_centered_frustum_mean_xyz.pkl', 'rb') as file:
            self.centered_frustum_mean_xyz = pickle.load(file)
            self.centered_frustum_mean_xyz = self.centered_frustum_mean_xyz.astype(np.float32)
        self.examples = []
        with open(self.detections_2d_path) as file:
            for line in file:
                values = line.split()
                object_class = float(values[3])
                if object_class == 1:
                    img_id = values[0]
                    u_min = float(values[4])
                    v_min = float(values[5])
                    u_max = float(values[6])
                    v_max = float(values[7])
                    score_2d = float(values[8])
                    detection_2d = {}
                    detection_2d['u_min'] = u_min
                    detection_2d['v_min'] = v_min
                    detection_2d['u_max'] = u_max
                    detection_2d['v_max'] = v_max
                    detection_2d['score_2d'] = score_2d
                    detection_2d['img_id'] = img_id
                    self.examples.append(detection_2d)
        self.num_examples = len(self.examples)

    def __getitem__(self, index):
        example = self.examples[index]
        img_id = example['img_id']
        lidar_path = self.lidar_dir + img_id + '.bin'
        point_cloud = np.fromfile(lidar_path, dtype=np.float32).reshape(-1, 4)
        orig_point_cloud = point_cloud
        point_cloud = point_cloud[point_cloud[:, 0] > -5, :]
        point_cloud = point_cloud[point_cloud[:, 0] < 80, :]
        calib = calibread(self.calib_path)
        P2 = calib['P2']
        Tr_velo_to_cam_orig = calib['Tr_velo_to_cam']
        R0_rect_orig = calib['R0_rect']
        R0_rect = np.eye(4)
        R0_rect[0:3, 0:3] = R0_rect_orig
        Tr_velo_to_cam = np.eye(4)
        Tr_velo_to_cam[0:3, :] = Tr_velo_to_cam_orig
        point_cloud_xyz = point_cloud[:, 0:3]
        point_cloud_xyz_hom = np.ones((point_cloud.shape[0], 4))
        point_cloud_xyz_hom[:, 0:3] = point_cloud[:, 0:3]
        img_points_hom = np.dot(P2, np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T))).T
        img_points = np.zeros((img_points_hom.shape[0], 2))
        img_points[:, 0] = img_points_hom[:, 0] / img_points_hom[:, 2]
        img_points[:, 1] = img_points_hom[:, 1] / img_points_hom[:, 2]
        point_cloud_xyz_camera_hom = np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T)).T
        point_cloud_xyz_camera = np.zeros((point_cloud_xyz_camera_hom.shape[0], 3))
        point_cloud_xyz_camera[:, 0] = point_cloud_xyz_camera_hom[:, 0] / point_cloud_xyz_camera_hom[:, 3]
        point_cloud_xyz_camera[:, 1] = point_cloud_xyz_camera_hom[:, 1] / point_cloud_xyz_camera_hom[:, 3]
        point_cloud_xyz_camera[:, 2] = point_cloud_xyz_camera_hom[:, 2] / point_cloud_xyz_camera_hom[:, 3]
        point_cloud_camera = point_cloud
        point_cloud_camera[:, 0:3] = point_cloud_xyz_camera
        u_min = example['u_min']
        u_max = example['u_max']
        v_min = example['v_min']
        v_max = example['v_max']
        input_2Dbbox = np.array([u_min, u_max, v_min, v_max])
        row_mask = np.logical_and(np.logical_and(img_points[:, 0] >= u_min, img_points[:, 0] <= u_max), np.logical_and(img_points[:, 1] >= v_min, img_points[:, 1] <= v_max))
        frustum_point_cloud_xyz = point_cloud_xyz[row_mask, :]
        frustum_point_cloud = point_cloud[row_mask, :]
        frustum_point_cloud_xyz_camera = point_cloud_xyz_camera[row_mask, :]
        frustum_point_cloud_camera = point_cloud_camera[row_mask, :]
        empty_frustum_flag = 0
        if frustum_point_cloud.shape[0] == 0:
            empty_frustum_flag = 1
            frustum_point_cloud = np.zeros((1024, 4), dtype=np.float32)
            frustum_point_cloud_xyz = np.zeros((1024, 3), dtype=np.float32)
            frustum_point_cloud_camera = np.zeros((1024, 4), dtype=np.float32)
            frustum_point_cloud_xyz_camera = np.zeros((1024, 3), dtype=np.float32)
        if frustum_point_cloud.shape[0] < 1024:
            row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=True)
        else:
            row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=False)
        frustum_point_cloud_xyz = frustum_point_cloud_xyz[row_idx, :]
        frustum_point_cloud = frustum_point_cloud[row_idx, :]
        frustum_point_cloud_xyz_camera = frustum_point_cloud_xyz_camera[row_idx, :]
        frustum_point_cloud_camera = frustum_point_cloud_camera[row_idx, :]
        img_path = self.img_dir + img_id + '.png'
        img = cv2.imread(img_path, -1)
        bbox_2d_img = img[int(np.max([0, v_min])):int(v_max), int(np.max([0, u_min])):int(u_max)]
        bbox_2d_img = cv2.resize(bbox_2d_img, (224, 224))
        u_center = u_min + (u_max - u_min) / 2.0
        v_center = v_min + (v_max - v_min) / 2.0
        center_img_point_hom = np.array([u_center, v_center, 1])
        P2_pseudo_inverse = np.linalg.pinv(P2)
        point_hom = np.dot(P2_pseudo_inverse, center_img_point_hom)
        point = np.array([point_hom[0] / point_hom[3], point_hom[1] / point_hom[3], point_hom[2] / point_hom[3]])
        if point[2] < 0:
            point[0] = -point[0]
            point[2] = -point[2]
        frustum_angle = np.arctan2(point[0], point[2])
        frustum_R = np.asarray([[np.cos(frustum_angle), 0, -np.sin(frustum_angle)], [0, 1, 0], [np.sin(frustum_angle), 0, np.cos(frustum_angle)]], dtype='float32')
        centered_frustum_point_cloud_xyz_camera = np.dot(frustum_R, frustum_point_cloud_xyz_camera.T).T
        centered_frustum_point_cloud_xyz_camera -= self.centered_frustum_mean_xyz
        centered_frustum_point_cloud_camera = frustum_point_cloud_camera
        centered_frustum_point_cloud_camera[:, 0:3] = centered_frustum_point_cloud_xyz_camera
        bbox_2d_img = bbox_2d_img / 255.0
        bbox_2d_img = bbox_2d_img - np.array([0.485, 0.456, 0.406])
        bbox_2d_img = bbox_2d_img / np.array([0.229, 0.224, 0.225])
        bbox_2d_img = np.transpose(bbox_2d_img, (2, 0, 1))
        bbox_2d_img = bbox_2d_img.astype(np.float32)
        centered_frustum_point_cloud_camera = torch.from_numpy(centered_frustum_point_cloud_camera)
        bbox_2d_img = torch.from_numpy(bbox_2d_img)
        return (centered_frustum_point_cloud_camera, bbox_2d_img, img_id, input_2Dbbox, frustum_R, frustum_angle, empty_frustum_flag, self.centered_frustum_mean_xyz, self.mean_car_size)

    def __len__(self):
        return self.num_examples

def __getitem__(self, index):
    example = self.examples[index]
    img_id = example['img_id']
    lidar_path = self.lidar_dir + img_id + '.bin'
    point_cloud = np.fromfile(lidar_path, dtype=np.float32).reshape(-1, 4)
    orig_point_cloud = point_cloud
    point_cloud = point_cloud[point_cloud[:, 0] > -5, :]
    point_cloud = point_cloud[point_cloud[:, 0] < 80, :]
    calib = calibread(self.calib_path)
    P2 = calib['P2']
    Tr_velo_to_cam_orig = calib['Tr_velo_to_cam']
    R0_rect_orig = calib['R0_rect']
    R0_rect = np.eye(4)
    R0_rect[0:3, 0:3] = R0_rect_orig
    Tr_velo_to_cam = np.eye(4)
    Tr_velo_to_cam[0:3, :] = Tr_velo_to_cam_orig
    point_cloud_xyz = point_cloud[:, 0:3]
    point_cloud_xyz_hom = np.ones((point_cloud.shape[0], 4))
    point_cloud_xyz_hom[:, 0:3] = point_cloud[:, 0:3]
    img_points_hom = np.dot(P2, np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T))).T
    img_points = np.zeros((img_points_hom.shape[0], 2))
    img_points[:, 0] = img_points_hom[:, 0] / img_points_hom[:, 2]
    img_points[:, 1] = img_points_hom[:, 1] / img_points_hom[:, 2]
    point_cloud_xyz_camera_hom = np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T)).T
    point_cloud_xyz_camera = np.zeros((point_cloud_xyz_camera_hom.shape[0], 3))
    point_cloud_xyz_camera[:, 0] = point_cloud_xyz_camera_hom[:, 0] / point_cloud_xyz_camera_hom[:, 3]
    point_cloud_xyz_camera[:, 1] = point_cloud_xyz_camera_hom[:, 1] / point_cloud_xyz_camera_hom[:, 3]
    point_cloud_xyz_camera[:, 2] = point_cloud_xyz_camera_hom[:, 2] / point_cloud_xyz_camera_hom[:, 3]
    point_cloud_camera = point_cloud
    point_cloud_camera[:, 0:3] = point_cloud_xyz_camera
    u_min = example['u_min']
    u_max = example['u_max']
    v_min = example['v_min']
    v_max = example['v_max']
    input_2Dbbox = np.array([u_min, u_max, v_min, v_max])
    row_mask = np.logical_and(np.logical_and(img_points[:, 0] >= u_min, img_points[:, 0] <= u_max), np.logical_and(img_points[:, 1] >= v_min, img_points[:, 1] <= v_max))
    frustum_point_cloud_xyz = point_cloud_xyz[row_mask, :]
    frustum_point_cloud = point_cloud[row_mask, :]
    frustum_point_cloud_xyz_camera = point_cloud_xyz_camera[row_mask, :]
    frustum_point_cloud_camera = point_cloud_camera[row_mask, :]
    empty_frustum_flag = 0
    if frustum_point_cloud.shape[0] == 0:
        empty_frustum_flag = 1
        frustum_point_cloud = np.zeros((1024, 4), dtype=np.float32)
        frustum_point_cloud_xyz = np.zeros((1024, 3), dtype=np.float32)
        frustum_point_cloud_camera = np.zeros((1024, 4), dtype=np.float32)
        frustum_point_cloud_xyz_camera = np.zeros((1024, 3), dtype=np.float32)
    if frustum_point_cloud.shape[0] < 1024:
        row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=True)
    else:
        row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=False)
    frustum_point_cloud_xyz = frustum_point_cloud_xyz[row_idx, :]
    frustum_point_cloud = frustum_point_cloud[row_idx, :]
    frustum_point_cloud_xyz_camera = frustum_point_cloud_xyz_camera[row_idx, :]
    frustum_point_cloud_camera = frustum_point_cloud_camera[row_idx, :]
    img_path = self.img_dir + img_id + '.png'
    img = cv2.imread(img_path, -1)
    bbox_2d_img = img[int(np.max([0, v_min])):int(v_max), int(np.max([0, u_min])):int(u_max)]
    bbox_2d_img = cv2.resize(bbox_2d_img, (224, 224))
    u_center = u_min + (u_max - u_min) / 2.0
    v_center = v_min + (v_max - v_min) / 2.0
    center_img_point_hom = np.array([u_center, v_center, 1])
    P2_pseudo_inverse = np.linalg.pinv(P2)
    point_hom = np.dot(P2_pseudo_inverse, center_img_point_hom)
    point = np.array([point_hom[0] / point_hom[3], point_hom[1] / point_hom[3], point_hom[2] / point_hom[3]])
    if point[2] < 0:
        point[0] = -point[0]
        point[2] = -point[2]
    frustum_angle = np.arctan2(point[0], point[2])
    frustum_R = np.asarray([[np.cos(frustum_angle), 0, -np.sin(frustum_angle)], [0, 1, 0], [np.sin(frustum_angle), 0, np.cos(frustum_angle)]], dtype='float32')
    centered_frustum_point_cloud_xyz_camera = np.dot(frustum_R, frustum_point_cloud_xyz_camera.T).T
    centered_frustum_point_cloud_xyz_camera -= self.centered_frustum_mean_xyz
    centered_frustum_point_cloud_camera = frustum_point_cloud_camera
    centered_frustum_point_cloud_camera[:, 0:3] = centered_frustum_point_cloud_xyz_camera
    bbox_2d_img = bbox_2d_img / 255.0
    bbox_2d_img = bbox_2d_img - np.array([0.485, 0.456, 0.406])
    bbox_2d_img = bbox_2d_img / np.array([0.229, 0.224, 0.225])
    bbox_2d_img = np.transpose(bbox_2d_img, (2, 0, 1))
    bbox_2d_img = bbox_2d_img.astype(np.float32)
    centered_frustum_point_cloud_camera = torch.from_numpy(centered_frustum_point_cloud_camera)
    bbox_2d_img = torch.from_numpy(bbox_2d_img)
    return (centered_frustum_point_cloud_camera, bbox_2d_img, img_id, input_2Dbbox, frustum_R, frustum_angle, empty_frustum_flag, self.centered_frustum_mean_xyz, self.mean_car_size)

class DatasetKittiTest(torch.utils.data.Dataset):

    def __init__(self, kitti_data_path, kitti_meta_path, NH):
        self.img_dir = kitti_data_path + '/object/testing/image_2/'
        self.calib_dir = kitti_data_path + '/object/testing/calib/'
        self.lidar_dir = kitti_data_path + '/object/testing/velodyne/'
        self.detections_2d_dir = kitti_meta_path + '/object/testing/2d_detections/'
        self.NH = NH
        with open(kitti_meta_path + '/kitti_train_mean_car_size.pkl', 'rb') as file:
            self.mean_car_size = pickle.load(file)
        with open(kitti_meta_path + '/kitti_centered_frustum_mean_xyz.pkl', 'rb') as file:
            self.centered_frustum_mean_xyz = pickle.load(file)
            self.centered_frustum_mean_xyz = self.centered_frustum_mean_xyz.astype(np.float32)
        img_ids = []
        img_names = os.listdir(self.img_dir)
        for img_name in img_names:
            img_id = img_name.split('.png')[0]
            img_ids.append(img_id)
        self.examples = []
        for img_id in img_ids:
            detections_file_path = self.detections_2d_dir + img_id + '.txt'
            with open(detections_file_path) as file:
                for line in file:
                    values = line.split()
                    object_class = float(values[3])
                    if object_class == 1:
                        u_min = float(values[4])
                        v_min = float(values[5])
                        u_max = float(values[6])
                        v_max = float(values[7])
                        score_2d = float(values[8])
                        detection_2d = {}
                        detection_2d['u_min'] = u_min
                        detection_2d['v_min'] = v_min
                        detection_2d['u_max'] = u_max
                        detection_2d['v_max'] = v_max
                        detection_2d['score_2d'] = score_2d
                        detection_2d['img_id'] = img_id
                        self.examples.append(detection_2d)
        self.num_examples = len(self.examples)

    def __getitem__(self, index):
        example = self.examples[index]
        img_id = example['img_id']
        lidar_path = self.lidar_dir + img_id + '.bin'
        point_cloud = np.fromfile(lidar_path, dtype=np.float32).reshape(-1, 4)
        orig_point_cloud = point_cloud
        point_cloud = point_cloud[point_cloud[:, 0] > -5, :]
        point_cloud = point_cloud[point_cloud[:, 0] < 80, :]
        calib = calibread(self.calib_dir + img_id + '.txt')
        P2 = calib['P2']
        Tr_velo_to_cam_orig = calib['Tr_velo_to_cam']
        R0_rect_orig = calib['R0_rect']
        R0_rect = np.eye(4)
        R0_rect[0:3, 0:3] = R0_rect_orig
        Tr_velo_to_cam = np.eye(4)
        Tr_velo_to_cam[0:3, :] = Tr_velo_to_cam_orig
        point_cloud_xyz = point_cloud[:, 0:3]
        point_cloud_xyz_hom = np.ones((point_cloud.shape[0], 4))
        point_cloud_xyz_hom[:, 0:3] = point_cloud[:, 0:3]
        img_points_hom = np.dot(P2, np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T))).T
        img_points = np.zeros((img_points_hom.shape[0], 2))
        img_points[:, 0] = img_points_hom[:, 0] / img_points_hom[:, 2]
        img_points[:, 1] = img_points_hom[:, 1] / img_points_hom[:, 2]
        point_cloud_xyz_camera_hom = np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T)).T
        point_cloud_xyz_camera = np.zeros((point_cloud_xyz_camera_hom.shape[0], 3))
        point_cloud_xyz_camera[:, 0] = point_cloud_xyz_camera_hom[:, 0] / point_cloud_xyz_camera_hom[:, 3]
        point_cloud_xyz_camera[:, 1] = point_cloud_xyz_camera_hom[:, 1] / point_cloud_xyz_camera_hom[:, 3]
        point_cloud_xyz_camera[:, 2] = point_cloud_xyz_camera_hom[:, 2] / point_cloud_xyz_camera_hom[:, 3]
        point_cloud_camera = point_cloud
        point_cloud_camera[:, 0:3] = point_cloud_xyz_camera
        u_min = example['u_min']
        u_max = example['u_max']
        v_min = example['v_min']
        v_max = example['v_max']
        score_2d = example['score_2d']
        input_2Dbbox = np.array([u_min, u_max, v_min, v_max])
        row_mask = np.logical_and(np.logical_and(img_points[:, 0] >= u_min, img_points[:, 0] <= u_max), np.logical_and(img_points[:, 1] >= v_min, img_points[:, 1] <= v_max))
        frustum_point_cloud_xyz = point_cloud_xyz[row_mask, :]
        frustum_point_cloud = point_cloud[row_mask, :]
        frustum_point_cloud_xyz_camera = point_cloud_xyz_camera[row_mask, :]
        frustum_point_cloud_camera = point_cloud_camera[row_mask, :]
        empty_frustum_flag = 0
        if frustum_point_cloud.shape[0] == 0:
            empty_frustum_flag = 1
            frustum_point_cloud = np.zeros((1024, 4), dtype=np.float32)
            frustum_point_cloud_xyz = np.zeros((1024, 3), dtype=np.float32)
            frustum_point_cloud_camera = np.zeros((1024, 4), dtype=np.float32)
            frustum_point_cloud_xyz_camera = np.zeros((1024, 3), dtype=np.float32)
        if frustum_point_cloud.shape[0] < 1024:
            row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=True)
        else:
            row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=False)
        frustum_point_cloud_xyz = frustum_point_cloud_xyz[row_idx, :]
        frustum_point_cloud = frustum_point_cloud[row_idx, :]
        frustum_point_cloud_xyz_camera = frustum_point_cloud_xyz_camera[row_idx, :]
        frustum_point_cloud_camera = frustum_point_cloud_camera[row_idx, :]
        img_path = self.img_dir + img_id + '.png'
        img = cv2.imread(img_path, -1)
        bbox_2d_img = img[int(np.max([0, v_min])):int(v_max), int(np.max([0, u_min])):int(u_max)]
        bbox_2d_img = cv2.resize(bbox_2d_img, (224, 224))
        u_center = u_min + (u_max - u_min) / 2.0
        v_center = v_min + (v_max - v_min) / 2.0
        center_img_point_hom = np.array([u_center, v_center, 1])
        P2_pseudo_inverse = np.linalg.pinv(P2)
        point_hom = np.dot(P2_pseudo_inverse, center_img_point_hom)
        point = np.array([point_hom[0] / point_hom[3], point_hom[1] / point_hom[3], point_hom[2] / point_hom[3]])
        if point[2] < 0:
            point[0] = -point[0]
            point[2] = -point[2]
        frustum_angle = np.arctan2(point[0], point[2])
        frustum_R = np.asarray([[np.cos(frustum_angle), 0, -np.sin(frustum_angle)], [0, 1, 0], [np.sin(frustum_angle), 0, np.cos(frustum_angle)]], dtype='float32')
        centered_frustum_point_cloud_xyz_camera = np.dot(frustum_R, frustum_point_cloud_xyz_camera.T).T
        centered_frustum_point_cloud_xyz_camera -= self.centered_frustum_mean_xyz
        centered_frustum_point_cloud_camera = frustum_point_cloud_camera
        centered_frustum_point_cloud_camera[:, 0:3] = centered_frustum_point_cloud_xyz_camera
        bbox_2d_img = bbox_2d_img / 255.0
        bbox_2d_img = bbox_2d_img - np.array([0.485, 0.456, 0.406])
        bbox_2d_img = bbox_2d_img / np.array([0.229, 0.224, 0.225])
        bbox_2d_img = np.transpose(bbox_2d_img, (2, 0, 1))
        bbox_2d_img = bbox_2d_img.astype(np.float32)
        centered_frustum_point_cloud_camera = torch.from_numpy(centered_frustum_point_cloud_camera)
        bbox_2d_img = torch.from_numpy(bbox_2d_img)
        return (centered_frustum_point_cloud_camera, bbox_2d_img, img_id, input_2Dbbox, frustum_R, frustum_angle, empty_frustum_flag, self.centered_frustum_mean_xyz, self.mean_car_size, score_2d)

    def __len__(self):
        return self.num_examples

def __getitem__(self, index):
    example = self.examples[index]
    img_id = example['img_id']
    lidar_path = self.lidar_dir + img_id + '.bin'
    point_cloud = np.fromfile(lidar_path, dtype=np.float32).reshape(-1, 4)
    orig_point_cloud = point_cloud
    point_cloud = point_cloud[point_cloud[:, 0] > -5, :]
    point_cloud = point_cloud[point_cloud[:, 0] < 80, :]
    calib = calibread(self.calib_dir + img_id + '.txt')
    P2 = calib['P2']
    Tr_velo_to_cam_orig = calib['Tr_velo_to_cam']
    R0_rect_orig = calib['R0_rect']
    R0_rect = np.eye(4)
    R0_rect[0:3, 0:3] = R0_rect_orig
    Tr_velo_to_cam = np.eye(4)
    Tr_velo_to_cam[0:3, :] = Tr_velo_to_cam_orig
    point_cloud_xyz = point_cloud[:, 0:3]
    point_cloud_xyz_hom = np.ones((point_cloud.shape[0], 4))
    point_cloud_xyz_hom[:, 0:3] = point_cloud[:, 0:3]
    img_points_hom = np.dot(P2, np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T))).T
    img_points = np.zeros((img_points_hom.shape[0], 2))
    img_points[:, 0] = img_points_hom[:, 0] / img_points_hom[:, 2]
    img_points[:, 1] = img_points_hom[:, 1] / img_points_hom[:, 2]
    point_cloud_xyz_camera_hom = np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T)).T
    point_cloud_xyz_camera = np.zeros((point_cloud_xyz_camera_hom.shape[0], 3))
    point_cloud_xyz_camera[:, 0] = point_cloud_xyz_camera_hom[:, 0] / point_cloud_xyz_camera_hom[:, 3]
    point_cloud_xyz_camera[:, 1] = point_cloud_xyz_camera_hom[:, 1] / point_cloud_xyz_camera_hom[:, 3]
    point_cloud_xyz_camera[:, 2] = point_cloud_xyz_camera_hom[:, 2] / point_cloud_xyz_camera_hom[:, 3]
    point_cloud_camera = point_cloud
    point_cloud_camera[:, 0:3] = point_cloud_xyz_camera
    u_min = example['u_min']
    u_max = example['u_max']
    v_min = example['v_min']
    v_max = example['v_max']
    score_2d = example['score_2d']
    input_2Dbbox = np.array([u_min, u_max, v_min, v_max])
    row_mask = np.logical_and(np.logical_and(img_points[:, 0] >= u_min, img_points[:, 0] <= u_max), np.logical_and(img_points[:, 1] >= v_min, img_points[:, 1] <= v_max))
    frustum_point_cloud_xyz = point_cloud_xyz[row_mask, :]
    frustum_point_cloud = point_cloud[row_mask, :]
    frustum_point_cloud_xyz_camera = point_cloud_xyz_camera[row_mask, :]
    frustum_point_cloud_camera = point_cloud_camera[row_mask, :]
    empty_frustum_flag = 0
    if frustum_point_cloud.shape[0] == 0:
        empty_frustum_flag = 1
        frustum_point_cloud = np.zeros((1024, 4), dtype=np.float32)
        frustum_point_cloud_xyz = np.zeros((1024, 3), dtype=np.float32)
        frustum_point_cloud_camera = np.zeros((1024, 4), dtype=np.float32)
        frustum_point_cloud_xyz_camera = np.zeros((1024, 3), dtype=np.float32)
    if frustum_point_cloud.shape[0] < 1024:
        row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=True)
    else:
        row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=False)
    frustum_point_cloud_xyz = frustum_point_cloud_xyz[row_idx, :]
    frustum_point_cloud = frustum_point_cloud[row_idx, :]
    frustum_point_cloud_xyz_camera = frustum_point_cloud_xyz_camera[row_idx, :]
    frustum_point_cloud_camera = frustum_point_cloud_camera[row_idx, :]
    img_path = self.img_dir + img_id + '.png'
    img = cv2.imread(img_path, -1)
    bbox_2d_img = img[int(np.max([0, v_min])):int(v_max), int(np.max([0, u_min])):int(u_max)]
    bbox_2d_img = cv2.resize(bbox_2d_img, (224, 224))
    u_center = u_min + (u_max - u_min) / 2.0
    v_center = v_min + (v_max - v_min) / 2.0
    center_img_point_hom = np.array([u_center, v_center, 1])
    P2_pseudo_inverse = np.linalg.pinv(P2)
    point_hom = np.dot(P2_pseudo_inverse, center_img_point_hom)
    point = np.array([point_hom[0] / point_hom[3], point_hom[1] / point_hom[3], point_hom[2] / point_hom[3]])
    if point[2] < 0:
        point[0] = -point[0]
        point[2] = -point[2]
    frustum_angle = np.arctan2(point[0], point[2])
    frustum_R = np.asarray([[np.cos(frustum_angle), 0, -np.sin(frustum_angle)], [0, 1, 0], [np.sin(frustum_angle), 0, np.cos(frustum_angle)]], dtype='float32')
    centered_frustum_point_cloud_xyz_camera = np.dot(frustum_R, frustum_point_cloud_xyz_camera.T).T
    centered_frustum_point_cloud_xyz_camera -= self.centered_frustum_mean_xyz
    centered_frustum_point_cloud_camera = frustum_point_cloud_camera
    centered_frustum_point_cloud_camera[:, 0:3] = centered_frustum_point_cloud_xyz_camera
    bbox_2d_img = bbox_2d_img / 255.0
    bbox_2d_img = bbox_2d_img - np.array([0.485, 0.456, 0.406])
    bbox_2d_img = bbox_2d_img / np.array([0.229, 0.224, 0.225])
    bbox_2d_img = np.transpose(bbox_2d_img, (2, 0, 1))
    bbox_2d_img = bbox_2d_img.astype(np.float32)
    centered_frustum_point_cloud_camera = torch.from_numpy(centered_frustum_point_cloud_camera)
    bbox_2d_img = torch.from_numpy(bbox_2d_img)
    return (centered_frustum_point_cloud_camera, bbox_2d_img, img_id, input_2Dbbox, frustum_R, frustum_angle, empty_frustum_flag, self.centered_frustum_mean_xyz, self.mean_car_size, score_2d)

class DatasetKittiVal2ddetections(torch.utils.data.Dataset):

    def __init__(self, kitti_data_path, kitti_meta_path, NH):
        self.img_dir = kitti_data_path + '/object/training/image_2/'
        self.calib_dir = kitti_data_path + '/object/training/calib/'
        self.lidar_dir = kitti_data_path + '/object/training/velodyne/'
        self.detections_2d_path = kitti_meta_path + '/rgb_detection_val.txt'
        self.NH = NH
        with open(kitti_meta_path + '/val_img_ids.pkl', 'rb') as file:
            img_ids = pickle.load(file)
        with open(kitti_meta_path + '/kitti_train_mean_car_size.pkl', 'rb') as file:
            self.mean_car_size = pickle.load(file)
        with open(kitti_meta_path + '/kitti_centered_frustum_mean_xyz.pkl', 'rb') as file:
            self.centered_frustum_mean_xyz = pickle.load(file)
            self.centered_frustum_mean_xyz = self.centered_frustum_mean_xyz.astype(np.float32)
        self.examples = []
        with open(self.detections_2d_path) as file:
            for line in file:
                values = line.split()
                object_class = float(values[1])
                if object_class == 2:
                    score_2d = float(values[2])
                    u_min = float(values[3])
                    v_min = float(values[4])
                    u_max = float(values[5])
                    v_max = float(values[6])
                    img_id = values[0].split('image_2/')[1]
                    img_id = img_id.split('.')[0]
                    detection_2d = {}
                    detection_2d['u_min'] = u_min
                    detection_2d['v_min'] = v_min
                    detection_2d['u_max'] = u_max
                    detection_2d['v_max'] = v_max
                    detection_2d['score_2d'] = score_2d
                    detection_2d['img_id'] = img_id
                    self.examples.append(detection_2d)
        self.num_examples = len(self.examples)

    def __getitem__(self, index):
        example = self.examples[index]
        img_id = example['img_id']
        lidar_path = self.lidar_dir + img_id + '.bin'
        point_cloud = np.fromfile(lidar_path, dtype=np.float32).reshape(-1, 4)
        orig_point_cloud = point_cloud
        point_cloud = point_cloud[point_cloud[:, 0] > -5, :]
        point_cloud = point_cloud[point_cloud[:, 0] < 80, :]
        calib = calibread(self.calib_dir + img_id + '.txt')
        P2 = calib['P2']
        Tr_velo_to_cam_orig = calib['Tr_velo_to_cam']
        R0_rect_orig = calib['R0_rect']
        R0_rect = np.eye(4)
        R0_rect[0:3, 0:3] = R0_rect_orig
        Tr_velo_to_cam = np.eye(4)
        Tr_velo_to_cam[0:3, :] = Tr_velo_to_cam_orig
        point_cloud_xyz = point_cloud[:, 0:3]
        point_cloud_xyz_hom = np.ones((point_cloud.shape[0], 4))
        point_cloud_xyz_hom[:, 0:3] = point_cloud[:, 0:3]
        img_points_hom = np.dot(P2, np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T))).T
        img_points = np.zeros((img_points_hom.shape[0], 2))
        img_points[:, 0] = img_points_hom[:, 0] / img_points_hom[:, 2]
        img_points[:, 1] = img_points_hom[:, 1] / img_points_hom[:, 2]
        point_cloud_xyz_camera_hom = np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T)).T
        point_cloud_xyz_camera = np.zeros((point_cloud_xyz_camera_hom.shape[0], 3))
        point_cloud_xyz_camera[:, 0] = point_cloud_xyz_camera_hom[:, 0] / point_cloud_xyz_camera_hom[:, 3]
        point_cloud_xyz_camera[:, 1] = point_cloud_xyz_camera_hom[:, 1] / point_cloud_xyz_camera_hom[:, 3]
        point_cloud_xyz_camera[:, 2] = point_cloud_xyz_camera_hom[:, 2] / point_cloud_xyz_camera_hom[:, 3]
        point_cloud_camera = point_cloud
        point_cloud_camera[:, 0:3] = point_cloud_xyz_camera
        u_min = example['u_min']
        u_max = example['u_max']
        v_min = example['v_min']
        v_max = example['v_max']
        score_2d = example['score_2d']
        input_2Dbbox = np.array([u_min, u_max, v_min, v_max])
        row_mask = np.logical_and(np.logical_and(img_points[:, 0] >= u_min, img_points[:, 0] <= u_max), np.logical_and(img_points[:, 1] >= v_min, img_points[:, 1] <= v_max))
        frustum_point_cloud_xyz = point_cloud_xyz[row_mask, :]
        frustum_point_cloud = point_cloud[row_mask, :]
        frustum_point_cloud_xyz_camera = point_cloud_xyz_camera[row_mask, :]
        frustum_point_cloud_camera = point_cloud_camera[row_mask, :]
        empty_frustum_flag = 0
        if frustum_point_cloud.shape[0] == 0:
            empty_frustum_flag = 1
            frustum_point_cloud = np.zeros((1024, 4), dtype=np.float32)
            frustum_point_cloud_xyz = np.zeros((1024, 3), dtype=np.float32)
            frustum_point_cloud_camera = np.zeros((1024, 4), dtype=np.float32)
            frustum_point_cloud_xyz_camera = np.zeros((1024, 3), dtype=np.float32)
        if frustum_point_cloud.shape[0] < 1024:
            row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=True)
        else:
            row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=False)
        frustum_point_cloud_xyz = frustum_point_cloud_xyz[row_idx, :]
        frustum_point_cloud = frustum_point_cloud[row_idx, :]
        frustum_point_cloud_xyz_camera = frustum_point_cloud_xyz_camera[row_idx, :]
        frustum_point_cloud_camera = frustum_point_cloud_camera[row_idx, :]
        img_path = self.img_dir + img_id + '.png'
        img = cv2.imread(img_path, -1)
        bbox_2d_img = img[int(np.max([0, v_min])):int(v_max), int(np.max([0, u_min])):int(u_max)]
        bbox_2d_img = cv2.resize(bbox_2d_img, (224, 224))
        u_center = u_min + (u_max - u_min) / 2.0
        v_center = v_min + (v_max - v_min) / 2.0
        center_img_point_hom = np.array([u_center, v_center, 1])
        P2_pseudo_inverse = np.linalg.pinv(P2)
        point_hom = np.dot(P2_pseudo_inverse, center_img_point_hom)
        point = np.array([point_hom[0] / point_hom[3], point_hom[1] / point_hom[3], point_hom[2] / point_hom[3]])
        if point[2] < 0:
            point[0] = -point[0]
            point[2] = -point[2]
        frustum_angle = np.arctan2(point[0], point[2])
        frustum_R = np.asarray([[np.cos(frustum_angle), 0, -np.sin(frustum_angle)], [0, 1, 0], [np.sin(frustum_angle), 0, np.cos(frustum_angle)]], dtype='float32')
        centered_frustum_point_cloud_xyz_camera = np.dot(frustum_R, frustum_point_cloud_xyz_camera.T).T
        centered_frustum_point_cloud_xyz_camera -= self.centered_frustum_mean_xyz
        centered_frustum_point_cloud_camera = frustum_point_cloud_camera
        centered_frustum_point_cloud_camera[:, 0:3] = centered_frustum_point_cloud_xyz_camera
        bbox_2d_img = bbox_2d_img / 255.0
        bbox_2d_img = bbox_2d_img - np.array([0.485, 0.456, 0.406])
        bbox_2d_img = bbox_2d_img / np.array([0.229, 0.224, 0.225])
        bbox_2d_img = np.transpose(bbox_2d_img, (2, 0, 1))
        bbox_2d_img = bbox_2d_img.astype(np.float32)
        centered_frustum_point_cloud_camera = torch.from_numpy(centered_frustum_point_cloud_camera)
        bbox_2d_img = torch.from_numpy(bbox_2d_img)
        return (centered_frustum_point_cloud_camera, bbox_2d_img, img_id, input_2Dbbox, frustum_R, frustum_angle, empty_frustum_flag, self.centered_frustum_mean_xyz, self.mean_car_size, score_2d)

    def __len__(self):
        return self.num_examples

def __getitem__(self, index):
    example = self.examples[index]
    img_id = example['img_id']
    lidar_path = self.lidar_dir + img_id + '.bin'
    point_cloud = np.fromfile(lidar_path, dtype=np.float32).reshape(-1, 4)
    orig_point_cloud = point_cloud
    point_cloud = point_cloud[point_cloud[:, 0] > -5, :]
    point_cloud = point_cloud[point_cloud[:, 0] < 80, :]
    calib = calibread(self.calib_dir + img_id + '.txt')
    P2 = calib['P2']
    Tr_velo_to_cam_orig = calib['Tr_velo_to_cam']
    R0_rect_orig = calib['R0_rect']
    R0_rect = np.eye(4)
    R0_rect[0:3, 0:3] = R0_rect_orig
    Tr_velo_to_cam = np.eye(4)
    Tr_velo_to_cam[0:3, :] = Tr_velo_to_cam_orig
    point_cloud_xyz = point_cloud[:, 0:3]
    point_cloud_xyz_hom = np.ones((point_cloud.shape[0], 4))
    point_cloud_xyz_hom[:, 0:3] = point_cloud[:, 0:3]
    img_points_hom = np.dot(P2, np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T))).T
    img_points = np.zeros((img_points_hom.shape[0], 2))
    img_points[:, 0] = img_points_hom[:, 0] / img_points_hom[:, 2]
    img_points[:, 1] = img_points_hom[:, 1] / img_points_hom[:, 2]
    point_cloud_xyz_camera_hom = np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T)).T
    point_cloud_xyz_camera = np.zeros((point_cloud_xyz_camera_hom.shape[0], 3))
    point_cloud_xyz_camera[:, 0] = point_cloud_xyz_camera_hom[:, 0] / point_cloud_xyz_camera_hom[:, 3]
    point_cloud_xyz_camera[:, 1] = point_cloud_xyz_camera_hom[:, 1] / point_cloud_xyz_camera_hom[:, 3]
    point_cloud_xyz_camera[:, 2] = point_cloud_xyz_camera_hom[:, 2] / point_cloud_xyz_camera_hom[:, 3]
    point_cloud_camera = point_cloud
    point_cloud_camera[:, 0:3] = point_cloud_xyz_camera
    u_min = example['u_min']
    u_max = example['u_max']
    v_min = example['v_min']
    v_max = example['v_max']
    score_2d = example['score_2d']
    input_2Dbbox = np.array([u_min, u_max, v_min, v_max])
    row_mask = np.logical_and(np.logical_and(img_points[:, 0] >= u_min, img_points[:, 0] <= u_max), np.logical_and(img_points[:, 1] >= v_min, img_points[:, 1] <= v_max))
    frustum_point_cloud_xyz = point_cloud_xyz[row_mask, :]
    frustum_point_cloud = point_cloud[row_mask, :]
    frustum_point_cloud_xyz_camera = point_cloud_xyz_camera[row_mask, :]
    frustum_point_cloud_camera = point_cloud_camera[row_mask, :]
    empty_frustum_flag = 0
    if frustum_point_cloud.shape[0] == 0:
        empty_frustum_flag = 1
        frustum_point_cloud = np.zeros((1024, 4), dtype=np.float32)
        frustum_point_cloud_xyz = np.zeros((1024, 3), dtype=np.float32)
        frustum_point_cloud_camera = np.zeros((1024, 4), dtype=np.float32)
        frustum_point_cloud_xyz_camera = np.zeros((1024, 3), dtype=np.float32)
    if frustum_point_cloud.shape[0] < 1024:
        row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=True)
    else:
        row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=False)
    frustum_point_cloud_xyz = frustum_point_cloud_xyz[row_idx, :]
    frustum_point_cloud = frustum_point_cloud[row_idx, :]
    frustum_point_cloud_xyz_camera = frustum_point_cloud_xyz_camera[row_idx, :]
    frustum_point_cloud_camera = frustum_point_cloud_camera[row_idx, :]
    img_path = self.img_dir + img_id + '.png'
    img = cv2.imread(img_path, -1)
    bbox_2d_img = img[int(np.max([0, v_min])):int(v_max), int(np.max([0, u_min])):int(u_max)]
    bbox_2d_img = cv2.resize(bbox_2d_img, (224, 224))
    u_center = u_min + (u_max - u_min) / 2.0
    v_center = v_min + (v_max - v_min) / 2.0
    center_img_point_hom = np.array([u_center, v_center, 1])
    P2_pseudo_inverse = np.linalg.pinv(P2)
    point_hom = np.dot(P2_pseudo_inverse, center_img_point_hom)
    point = np.array([point_hom[0] / point_hom[3], point_hom[1] / point_hom[3], point_hom[2] / point_hom[3]])
    if point[2] < 0:
        point[0] = -point[0]
        point[2] = -point[2]
    frustum_angle = np.arctan2(point[0], point[2])
    frustum_R = np.asarray([[np.cos(frustum_angle), 0, -np.sin(frustum_angle)], [0, 1, 0], [np.sin(frustum_angle), 0, np.cos(frustum_angle)]], dtype='float32')
    centered_frustum_point_cloud_xyz_camera = np.dot(frustum_R, frustum_point_cloud_xyz_camera.T).T
    centered_frustum_point_cloud_xyz_camera -= self.centered_frustum_mean_xyz
    centered_frustum_point_cloud_camera = frustum_point_cloud_camera
    centered_frustum_point_cloud_camera[:, 0:3] = centered_frustum_point_cloud_xyz_camera
    bbox_2d_img = bbox_2d_img / 255.0
    bbox_2d_img = bbox_2d_img - np.array([0.485, 0.456, 0.406])
    bbox_2d_img = bbox_2d_img / np.array([0.229, 0.224, 0.225])
    bbox_2d_img = np.transpose(bbox_2d_img, (2, 0, 1))
    bbox_2d_img = bbox_2d_img.astype(np.float32)
    centered_frustum_point_cloud_camera = torch.from_numpy(centered_frustum_point_cloud_camera)
    bbox_2d_img = torch.from_numpy(bbox_2d_img)
    return (centered_frustum_point_cloud_camera, bbox_2d_img, img_id, input_2Dbbox, frustum_R, frustum_angle, empty_frustum_flag, self.centered_frustum_mean_xyz, self.mean_car_size, score_2d)

def LabelLoader2D3D(file_id, path, ext, calib_path, calib_ext):
    labels = labelread(path + '/' + file_id + ext)
    calib = calibread(calib_path + '/' + file_id + calib_ext)
    polys = list()
    for bbox in labels:
        poly = dict()
        poly2d = dict()
        poly2d['class'] = bbox['type']
        poly2d['truncated'] = bbox['truncated']
        poly2d['poly'] = np.array([[bbox['bbox']['left'], bbox['bbox']['top']], [bbox['bbox']['right'], bbox['bbox']['top']], [bbox['bbox']['right'], bbox['bbox']['bottom']], [bbox['bbox']['left'], bbox['bbox']['bottom']]], dtype='int32')
        poly['label_2D'] = poly2d
        poly3d = dict()
        poly3d['class'] = bbox['type']
        location = np.asarray([bbox['location']['x'], bbox['location']['y'], bbox['location']['z']], dtype='float32')
        r_y = bbox['rotation_y']
        Rmat = np.asarray([[math.cos(r_y), 0, math.sin(r_y)], [0, 1, 0], [-math.sin(r_y), 0, math.cos(r_y)]], dtype='float32')
        length = bbox['dimensions']['length']
        width = bbox['dimensions']['width']
        height = bbox['dimensions']['height']
        p0 = np.dot(Rmat, np.asarray([length / 2.0, 0, width / 2.0], dtype='float32'))
        p1 = np.dot(Rmat, np.asarray([-length / 2.0, 0, width / 2.0], dtype='float32'))
        p2 = np.dot(Rmat, np.asarray([-length / 2.0, 0, -width / 2.0], dtype='float32'))
        p3 = np.dot(Rmat, np.asarray([length / 2.0, 0, -width / 2.0], dtype='float32'))
        p4 = np.dot(Rmat, np.asarray([length / 2.0, -height, width / 2.0], dtype='float32'))
        p5 = np.dot(Rmat, np.asarray([-length / 2.0, -height, width / 2.0], dtype='float32'))
        p6 = np.dot(Rmat, np.asarray([-length / 2.0, -height, -width / 2.0], dtype='float32'))
        p7 = np.dot(Rmat, np.asarray([length / 2.0, -height, -width / 2.0], dtype='float32'))
        poly3d['points'] = np.array(location + [p0, p1, p2, p3, p4, p5, p6, p7])
        poly3d['lines'] = [[0, 3, 7, 4, 0], [1, 2, 6, 5, 1], [0, 1], [2, 3], [6, 7], [4, 5]]
        poly3d['colors'] = [[255, 0, 0], [0, 0, 255], [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0]]
        poly3d['P0_mat'] = calib['P2']
        poly3d['center'] = location
        poly3d['l'] = length
        poly3d['w'] = width
        poly3d['h'] = height
        poly3d['r_y'] = r_y
        poly['label_3D'] = poly3d
        polys.append(poly)
    return polys

def LabelLoader2D3D_sequence(img_id, img_id_float, label_path, calib_path):
    labels = labelread_sequence(label_path)
    img_id_labels = []
    for label in labels:
        if label['frame'] == img_id_float:
            img_id_labels.append(label)
    calib = calibread(calib_path)
    polys = list()
    for bbox in img_id_labels:
        poly = dict()
        poly2d = dict()
        poly2d['class'] = bbox['type']
        poly2d['truncated'] = bbox['truncated']
        poly2d['occluded'] = bbox['occluded']
        poly2d['poly'] = np.array([[bbox['bbox']['left'], bbox['bbox']['top']], [bbox['bbox']['right'], bbox['bbox']['top']], [bbox['bbox']['right'], bbox['bbox']['bottom']], [bbox['bbox']['left'], bbox['bbox']['bottom']]], dtype='int32')
        poly['label_2D'] = poly2d
        poly3d = dict()
        poly3d['class'] = bbox['type']
        location = np.asarray([bbox['location']['x'], bbox['location']['y'], bbox['location']['z']], dtype='float32')
        r_y = bbox['rotation_y']
        Rmat = np.asarray([[math.cos(r_y), 0, math.sin(r_y)], [0, 1, 0], [-math.sin(r_y), 0, math.cos(r_y)]], dtype='float32')
        length = bbox['dimensions']['length']
        width = bbox['dimensions']['width']
        height = bbox['dimensions']['height']
        p0 = np.dot(Rmat, np.asarray([length / 2.0, 0, width / 2.0], dtype='float32'))
        p1 = np.dot(Rmat, np.asarray([-length / 2.0, 0, width / 2.0], dtype='float32'))
        p2 = np.dot(Rmat, np.asarray([-length / 2.0, 0, -width / 2.0], dtype='float32'))
        p3 = np.dot(Rmat, np.asarray([length / 2.0, 0, -width / 2.0], dtype='float32'))
        p4 = np.dot(Rmat, np.asarray([length / 2.0, -height, width / 2.0], dtype='float32'))
        p5 = np.dot(Rmat, np.asarray([-length / 2.0, -height, width / 2.0], dtype='float32'))
        p6 = np.dot(Rmat, np.asarray([-length / 2.0, -height, -width / 2.0], dtype='float32'))
        p7 = np.dot(Rmat, np.asarray([length / 2.0, -height, -width / 2.0], dtype='float32'))
        poly3d['points'] = np.array(location + [p0, p1, p2, p3, p4, p5, p6, p7])
        poly3d['lines'] = [[0, 3, 7, 4, 0], [1, 2, 6, 5, 1], [0, 1], [2, 3], [6, 7], [4, 5]]
        poly3d['colors'] = [[255, 0, 0], [0, 0, 255], [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0]]
        poly3d['P0_mat'] = calib['P2']
        poly3d['center'] = location
        poly3d['l'] = length
        poly3d['w'] = width
        poly3d['h'] = height
        poly3d['r_y'] = r_y
        poly['label_3D'] = poly3d
        polys.append(poly)
    return polys

class DatasetFrustumPointNetAugmentation(torch.utils.data.Dataset):

    def __init__(self, kitti_data_path, kitti_meta_path, type, NH):
        self.img_dir = kitti_data_path + '/object/training/image_2/'
        self.label_dir = kitti_data_path + '/object/training/label_2/'
        self.calib_dir = kitti_data_path + '/object/training/calib/'
        self.lidar_dir = kitti_data_path + '/object/training/velodyne/'
        self.NH = NH
        with open(kitti_meta_path + '/%s_img_ids.pkl' % type, 'rb') as file:
            img_ids = pickle.load(file)
        with open(kitti_meta_path + '/kitti_train_mean_car_size.pkl', 'rb') as file:
            self.mean_car_size = pickle.load(file)
        with open(kitti_meta_path + '/kitti_centered_frustum_mean_xyz.pkl', 'rb') as file:
            self.centered_frustum_mean_xyz = pickle.load(file)
            self.centered_frustum_mean_xyz = self.centered_frustum_mean_xyz.astype(np.float32)
        self.examples = []
        for img_id in img_ids:
            labels = LabelLoader2D3D(img_id, self.label_dir, '.txt', self.calib_dir, '.txt')
            for label in labels:
                label_2d = label['label_2D']
                if label_2d['truncated'] < 0.5 and label_2d['class'] == 'Car':
                    label['img_id'] = img_id
                    self.examples.append(label)
        self.num_examples = len(self.examples)

    def __getitem__(self, index):
        example = self.examples[index]
        img_id = example['img_id']
        lidar_path = self.lidar_dir + img_id + '.bin'
        point_cloud = np.fromfile(lidar_path, dtype=np.float32).reshape(-1, 4)
        orig_point_cloud = point_cloud
        point_cloud = point_cloud[point_cloud[:, 0] > 0, :]
        point_cloud = point_cloud[point_cloud[:, 0] < 80, :]
        calib = calibread(self.calib_dir + img_id + '.txt')
        P2 = calib['P2']
        Tr_velo_to_cam_orig = calib['Tr_velo_to_cam']
        R0_rect_orig = calib['R0_rect']
        R0_rect = np.eye(4)
        R0_rect[0:3, 0:3] = R0_rect_orig
        Tr_velo_to_cam = np.eye(4)
        Tr_velo_to_cam[0:3, :] = Tr_velo_to_cam_orig
        point_cloud_xyz = point_cloud[:, 0:3]
        point_cloud_xyz_hom = np.ones((point_cloud.shape[0], 4))
        point_cloud_xyz_hom[:, 0:3] = point_cloud[:, 0:3]
        img_points_hom = np.dot(P2, np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T))).T
        img_points = np.zeros((img_points_hom.shape[0], 2))
        img_points[:, 0] = img_points_hom[:, 0] / img_points_hom[:, 2]
        img_points[:, 1] = img_points_hom[:, 1] / img_points_hom[:, 2]
        point_cloud_xyz_camera_hom = np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T)).T
        point_cloud_xyz_camera = np.zeros((point_cloud_xyz_camera_hom.shape[0], 3))
        point_cloud_xyz_camera[:, 0] = point_cloud_xyz_camera_hom[:, 0] / point_cloud_xyz_camera_hom[:, 3]
        point_cloud_xyz_camera[:, 1] = point_cloud_xyz_camera_hom[:, 1] / point_cloud_xyz_camera_hom[:, 3]
        point_cloud_xyz_camera[:, 2] = point_cloud_xyz_camera_hom[:, 2] / point_cloud_xyz_camera_hom[:, 3]
        point_cloud_camera = point_cloud
        point_cloud_camera[:, 0:3] = point_cloud_xyz_camera
        label_2D = example['label_2D']
        label_3D = example['label_3D']
        bbox = label_2D['poly']
        u_min = bbox[0, 0]
        u_max = bbox[1, 0]
        v_min = bbox[0, 1]
        v_max = bbox[2, 1]
        w = u_max - u_min
        h = v_max - v_min
        u_center = u_min + w / 2.0
        v_center = v_min + h / 2.0
        u_center = u_center + np.random.uniform(low=-0.1 * w, high=0.1 * w)
        v_center = v_center + np.random.uniform(low=-0.1 * h, high=0.1 * h)
        w = w * np.random.uniform(low=0.9, high=1.1)
        h = h * np.random.uniform(low=0.9, high=1.1)
        u_min = u_center - w / 2.0
        u_max = u_center + w / 2.0
        v_min = v_center - h / 2.0
        v_max = v_center + h / 2.0
        row_mask = np.logical_and(np.logical_and(img_points[:, 0] >= u_min, img_points[:, 0] <= u_max), np.logical_and(img_points[:, 1] >= v_min, img_points[:, 1] <= v_max))
        frustum_point_cloud_xyz = point_cloud_xyz[row_mask, :]
        frustum_point_cloud = point_cloud[row_mask, :]
        frustum_point_cloud_xyz_camera = point_cloud_xyz_camera[row_mask, :]
        frustum_point_cloud_camera = point_cloud_camera[row_mask, :]
        if frustum_point_cloud.shape[0] == 0:
            print(img_id)
            print(frustum_point_cloud.shape)
            return self.__getitem__(0)
        if frustum_point_cloud.shape[0] < 1024:
            row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=True)
        else:
            row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=False)
        frustum_point_cloud_xyz = frustum_point_cloud_xyz[row_idx, :]
        frustum_point_cloud = frustum_point_cloud[row_idx, :]
        frustum_point_cloud_xyz_camera = frustum_point_cloud_xyz_camera[row_idx, :]
        frustum_point_cloud_camera = frustum_point_cloud_camera[row_idx, :]
        points = label_3D['points']
        y_max = points[0, 1]
        y_min = points[4, 1]
        A = np.array([points[0, 0], points[0, 2]])
        B = np.array([points[1, 0], points[1, 2]])
        D = np.array([points[3, 0], points[3, 2]])
        AB = B - A
        AD = D - A
        AB_dot_AB = np.dot(AB, AB)
        AD_dot_AD = np.dot(AD, AD)
        P = np.zeros((frustum_point_cloud_xyz_camera.shape[0], 2))
        P[:, 0] = frustum_point_cloud_xyz_camera[:, 0]
        P[:, 1] = frustum_point_cloud_xyz_camera[:, 2]
        AP = P - A
        AP_dot_AB = np.dot(AP, AB)
        AP_dot_AD = np.dot(AP, AD)
        row_mask = np.logical_and(np.logical_and(frustum_point_cloud_xyz_camera[:, 1] >= y_min, frustum_point_cloud_xyz_camera[:, 1] <= y_max), np.logical_and(np.logical_and(AP_dot_AB >= 0, AP_dot_AB <= AB_dot_AB), np.logical_and(AP_dot_AD >= 0, AP_dot_AD <= AD_dot_AD)))
        row_mask_gt = row_mask
        gt_point_cloud_xyz_camera = frustum_point_cloud_xyz_camera[row_mask, :]
        label_InstanceSeg = np.zeros((frustum_point_cloud.shape[0],), dtype=np.int64)
        label_InstanceSeg[row_mask] = 1
        u_center = u_min + (u_max - u_min) / 2.0
        v_center = v_min + (v_max - v_min) / 2.0
        center_img_point_hom = np.array([u_center, v_center, 1])
        P2_pseudo_inverse = np.linalg.pinv(P2)
        point_hom = np.dot(P2_pseudo_inverse, center_img_point_hom)
        point = np.array([point_hom[0] / point_hom[3], point_hom[1] / point_hom[3], point_hom[2] / point_hom[3]])
        if point[2] < 0:
            point[0] = -point[0]
            point[2] = -point[2]
        frustum_angle = np.arctan2(point[0], point[2])
        frustum_R = np.asarray([[np.cos(frustum_angle), 0, -np.sin(frustum_angle)], [0, 1, 0], [np.sin(frustum_angle), 0, np.cos(frustum_angle)]], dtype='float32')
        centered_frustum_point_cloud_xyz_camera = np.dot(frustum_R, frustum_point_cloud_xyz_camera.T).T
        centered_frustum_point_cloud_xyz_camera -= self.centered_frustum_mean_xyz
        centered_frustum_point_cloud_camera = frustum_point_cloud_camera
        centered_frustum_point_cloud_camera[:, 0:3] = centered_frustum_point_cloud_xyz_camera
        z_shift = np.random.uniform(low=-20, high=20)
        centered_frustum_point_cloud_camera[:, 2] -= z_shift
        flip = np.random.randint(low=0, high=2)
        centered_frustum_point_cloud_camera[:, 0] = flip * -centered_frustum_point_cloud_camera[:, 0] + (1 - flip) * centered_frustum_point_cloud_camera[:, 0]
        label_TNet = np.dot(frustum_R, label_3D['center']) - self.centered_frustum_mean_xyz
        label_TNet[0] = flip * -label_TNet[0] + (1 - flip) * label_TNet[0]
        label_TNet[2] -= z_shift
        centered_frustum_point_cloud_xyz_camera = centered_frustum_point_cloud_camera[:, 0:3]
        gt_seg_point_cloud = centered_frustum_point_cloud_xyz_camera[row_mask_gt, :]
        random_angle = np.random.uniform(low=-np.pi / 10, high=np.pi / 10)
        R = np.asarray([[np.cos(random_angle), 0, -np.sin(random_angle)], [0, 1, 0], [np.sin(random_angle), 0, np.cos(random_angle)]], dtype='float32')
        gt_seg_point_cloud_at_origo = gt_seg_point_cloud - label_TNet
        rotated_gt_seg_point_cloud = np.dot(R, gt_seg_point_cloud_at_origo.T).T + label_TNet
        rot_centered_frustum_point_cloud_xyz_camera = np.copy(centered_frustum_point_cloud_xyz_camera)
        rot_centered_frustum_point_cloud_xyz_camera[row_mask_gt, :] = rotated_gt_seg_point_cloud
        centered_frustum_point_cloud_camera[:, 0:3] = rot_centered_frustum_point_cloud_xyz_camera
        centered_r_y = wrapToPi(label_3D['r_y'] - frustum_angle)
        if flip == 1:
            centered_r_y = wrapToPi(np.pi - centered_r_y)
        centered_r_y = wrapToPi(centered_r_y - random_angle)
        bin_number = getBinNumber(centered_r_y, NH=self.NH)
        bin_center = getBinCenter(bin_number, NH=self.NH)
        residual = wrapToPi(centered_r_y - bin_center)
        label_BboxNet = np.zeros((11,), dtype=np.float32)
        label_BboxNet[0:3] = np.dot(frustum_R, label_3D['center']) - self.centered_frustum_mean_xyz
        label_BboxNet[0] = flip * -label_BboxNet[0] + (1 - flip) * label_BboxNet[0]
        label_BboxNet[2] -= z_shift
        label_BboxNet[3] = label_3D['h']
        label_BboxNet[4] = label_3D['w']
        label_BboxNet[5] = label_3D['l']
        label_BboxNet[6] = bin_number
        label_BboxNet[7] = residual
        label_BboxNet[8:] = self.mean_car_size
        Rmat = np.asarray([[math.cos(residual), 0, math.sin(residual)], [0, 1, 0], [-math.sin(residual), 0, math.cos(residual)]], dtype='float32')
        center = label_BboxNet[0:3]
        l = label_3D['l']
        w = label_3D['w']
        h = label_3D['h']
        p0 = center + np.dot(Rmat, np.asarray([l / 2.0, 0, w / 2.0], dtype='float32').flatten())
        p1 = center + np.dot(Rmat, np.asarray([-l / 2.0, 0, w / 2.0], dtype='float32').flatten())
        p2 = center + np.dot(Rmat, np.asarray([-l / 2.0, 0, -w / 2.0], dtype='float32').flatten())
        p3 = center + np.dot(Rmat, np.asarray([l / 2.0, 0, -w / 2.0], dtype='float32').flatten())
        p4 = center + np.dot(Rmat, np.asarray([l / 2.0, -h, w / 2.0], dtype='float32').flatten())
        p5 = center + np.dot(Rmat, np.asarray([-l / 2.0, -h, w / 2.0], dtype='float32').flatten())
        p6 = center + np.dot(Rmat, np.asarray([-l / 2.0, -h, -w / 2.0], dtype='float32').flatten())
        p7 = center + np.dot(Rmat, np.asarray([l / 2.0, -h, -w / 2.0], dtype='float32').flatten())
        label_corner = np.array([p0, p1, p2, p3, p4, p5, p6, p7])
        label_corner_flipped = np.array([p2, p3, p0, p1, p6, p7, p4, p5])
        centered_frustum_point_cloud_camera = torch.from_numpy(centered_frustum_point_cloud_camera)
        label_InstanceSeg = torch.from_numpy(label_InstanceSeg)
        label_TNet = torch.from_numpy(label_TNet)
        label_BboxNet = torch.from_numpy(label_BboxNet)
        label_corner = torch.from_numpy(label_corner)
        label_corner_flipped = torch.from_numpy(label_corner_flipped)
        return (centered_frustum_point_cloud_camera, label_InstanceSeg, label_TNet, label_BboxNet, label_corner, label_corner_flipped)

    def __len__(self):
        return self.num_examples

def __getitem__(self, index):
    example = self.examples[index]
    img_id = example['img_id']
    lidar_path = self.lidar_dir + img_id + '.bin'
    point_cloud = np.fromfile(lidar_path, dtype=np.float32).reshape(-1, 4)
    orig_point_cloud = point_cloud
    point_cloud = point_cloud[point_cloud[:, 0] > 0, :]
    point_cloud = point_cloud[point_cloud[:, 0] < 80, :]
    calib = calibread(self.calib_dir + img_id + '.txt')
    P2 = calib['P2']
    Tr_velo_to_cam_orig = calib['Tr_velo_to_cam']
    R0_rect_orig = calib['R0_rect']
    R0_rect = np.eye(4)
    R0_rect[0:3, 0:3] = R0_rect_orig
    Tr_velo_to_cam = np.eye(4)
    Tr_velo_to_cam[0:3, :] = Tr_velo_to_cam_orig
    point_cloud_xyz = point_cloud[:, 0:3]
    point_cloud_xyz_hom = np.ones((point_cloud.shape[0], 4))
    point_cloud_xyz_hom[:, 0:3] = point_cloud[:, 0:3]
    img_points_hom = np.dot(P2, np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T))).T
    img_points = np.zeros((img_points_hom.shape[0], 2))
    img_points[:, 0] = img_points_hom[:, 0] / img_points_hom[:, 2]
    img_points[:, 1] = img_points_hom[:, 1] / img_points_hom[:, 2]
    point_cloud_xyz_camera_hom = np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T)).T
    point_cloud_xyz_camera = np.zeros((point_cloud_xyz_camera_hom.shape[0], 3))
    point_cloud_xyz_camera[:, 0] = point_cloud_xyz_camera_hom[:, 0] / point_cloud_xyz_camera_hom[:, 3]
    point_cloud_xyz_camera[:, 1] = point_cloud_xyz_camera_hom[:, 1] / point_cloud_xyz_camera_hom[:, 3]
    point_cloud_xyz_camera[:, 2] = point_cloud_xyz_camera_hom[:, 2] / point_cloud_xyz_camera_hom[:, 3]
    point_cloud_camera = point_cloud
    point_cloud_camera[:, 0:3] = point_cloud_xyz_camera
    label_2D = example['label_2D']
    label_3D = example['label_3D']
    bbox = label_2D['poly']
    u_min = bbox[0, 0]
    u_max = bbox[1, 0]
    v_min = bbox[0, 1]
    v_max = bbox[2, 1]
    w = u_max - u_min
    h = v_max - v_min
    u_center = u_min + w / 2.0
    v_center = v_min + h / 2.0
    u_center = u_center + np.random.uniform(low=-0.1 * w, high=0.1 * w)
    v_center = v_center + np.random.uniform(low=-0.1 * h, high=0.1 * h)
    w = w * np.random.uniform(low=0.9, high=1.1)
    h = h * np.random.uniform(low=0.9, high=1.1)
    u_min = u_center - w / 2.0
    u_max = u_center + w / 2.0
    v_min = v_center - h / 2.0
    v_max = v_center + h / 2.0
    row_mask = np.logical_and(np.logical_and(img_points[:, 0] >= u_min, img_points[:, 0] <= u_max), np.logical_and(img_points[:, 1] >= v_min, img_points[:, 1] <= v_max))
    frustum_point_cloud_xyz = point_cloud_xyz[row_mask, :]
    frustum_point_cloud = point_cloud[row_mask, :]
    frustum_point_cloud_xyz_camera = point_cloud_xyz_camera[row_mask, :]
    frustum_point_cloud_camera = point_cloud_camera[row_mask, :]
    if frustum_point_cloud.shape[0] == 0:
        print(img_id)
        print(frustum_point_cloud.shape)
        return self.__getitem__(0)
    if frustum_point_cloud.shape[0] < 1024:
        row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=True)
    else:
        row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=False)
    frustum_point_cloud_xyz = frustum_point_cloud_xyz[row_idx, :]
    frustum_point_cloud = frustum_point_cloud[row_idx, :]
    frustum_point_cloud_xyz_camera = frustum_point_cloud_xyz_camera[row_idx, :]
    frustum_point_cloud_camera = frustum_point_cloud_camera[row_idx, :]
    points = label_3D['points']
    y_max = points[0, 1]
    y_min = points[4, 1]
    A = np.array([points[0, 0], points[0, 2]])
    B = np.array([points[1, 0], points[1, 2]])
    D = np.array([points[3, 0], points[3, 2]])
    AB = B - A
    AD = D - A
    AB_dot_AB = np.dot(AB, AB)
    AD_dot_AD = np.dot(AD, AD)
    P = np.zeros((frustum_point_cloud_xyz_camera.shape[0], 2))
    P[:, 0] = frustum_point_cloud_xyz_camera[:, 0]
    P[:, 1] = frustum_point_cloud_xyz_camera[:, 2]
    AP = P - A
    AP_dot_AB = np.dot(AP, AB)
    AP_dot_AD = np.dot(AP, AD)
    row_mask = np.logical_and(np.logical_and(frustum_point_cloud_xyz_camera[:, 1] >= y_min, frustum_point_cloud_xyz_camera[:, 1] <= y_max), np.logical_and(np.logical_and(AP_dot_AB >= 0, AP_dot_AB <= AB_dot_AB), np.logical_and(AP_dot_AD >= 0, AP_dot_AD <= AD_dot_AD)))
    row_mask_gt = row_mask
    gt_point_cloud_xyz_camera = frustum_point_cloud_xyz_camera[row_mask, :]
    label_InstanceSeg = np.zeros((frustum_point_cloud.shape[0],), dtype=np.int64)
    label_InstanceSeg[row_mask] = 1
    u_center = u_min + (u_max - u_min) / 2.0
    v_center = v_min + (v_max - v_min) / 2.0
    center_img_point_hom = np.array([u_center, v_center, 1])
    P2_pseudo_inverse = np.linalg.pinv(P2)
    point_hom = np.dot(P2_pseudo_inverse, center_img_point_hom)
    point = np.array([point_hom[0] / point_hom[3], point_hom[1] / point_hom[3], point_hom[2] / point_hom[3]])
    if point[2] < 0:
        point[0] = -point[0]
        point[2] = -point[2]
    frustum_angle = np.arctan2(point[0], point[2])
    frustum_R = np.asarray([[np.cos(frustum_angle), 0, -np.sin(frustum_angle)], [0, 1, 0], [np.sin(frustum_angle), 0, np.cos(frustum_angle)]], dtype='float32')
    centered_frustum_point_cloud_xyz_camera = np.dot(frustum_R, frustum_point_cloud_xyz_camera.T).T
    centered_frustum_point_cloud_xyz_camera -= self.centered_frustum_mean_xyz
    centered_frustum_point_cloud_camera = frustum_point_cloud_camera
    centered_frustum_point_cloud_camera[:, 0:3] = centered_frustum_point_cloud_xyz_camera
    z_shift = np.random.uniform(low=-20, high=20)
    centered_frustum_point_cloud_camera[:, 2] -= z_shift
    flip = np.random.randint(low=0, high=2)
    centered_frustum_point_cloud_camera[:, 0] = flip * -centered_frustum_point_cloud_camera[:, 0] + (1 - flip) * centered_frustum_point_cloud_camera[:, 0]
    label_TNet = np.dot(frustum_R, label_3D['center']) - self.centered_frustum_mean_xyz
    label_TNet[0] = flip * -label_TNet[0] + (1 - flip) * label_TNet[0]
    label_TNet[2] -= z_shift
    centered_frustum_point_cloud_xyz_camera = centered_frustum_point_cloud_camera[:, 0:3]
    gt_seg_point_cloud = centered_frustum_point_cloud_xyz_camera[row_mask_gt, :]
    random_angle = np.random.uniform(low=-np.pi / 10, high=np.pi / 10)
    R = np.asarray([[np.cos(random_angle), 0, -np.sin(random_angle)], [0, 1, 0], [np.sin(random_angle), 0, np.cos(random_angle)]], dtype='float32')
    gt_seg_point_cloud_at_origo = gt_seg_point_cloud - label_TNet
    rotated_gt_seg_point_cloud = np.dot(R, gt_seg_point_cloud_at_origo.T).T + label_TNet
    rot_centered_frustum_point_cloud_xyz_camera = np.copy(centered_frustum_point_cloud_xyz_camera)
    rot_centered_frustum_point_cloud_xyz_camera[row_mask_gt, :] = rotated_gt_seg_point_cloud
    centered_frustum_point_cloud_camera[:, 0:3] = rot_centered_frustum_point_cloud_xyz_camera
    centered_r_y = wrapToPi(label_3D['r_y'] - frustum_angle)
    if flip == 1:
        centered_r_y = wrapToPi(np.pi - centered_r_y)
    centered_r_y = wrapToPi(centered_r_y - random_angle)
    bin_number = getBinNumber(centered_r_y, NH=self.NH)
    bin_center = getBinCenter(bin_number, NH=self.NH)
    residual = wrapToPi(centered_r_y - bin_center)
    label_BboxNet = np.zeros((11,), dtype=np.float32)
    label_BboxNet[0:3] = np.dot(frustum_R, label_3D['center']) - self.centered_frustum_mean_xyz
    label_BboxNet[0] = flip * -label_BboxNet[0] + (1 - flip) * label_BboxNet[0]
    label_BboxNet[2] -= z_shift
    label_BboxNet[3] = label_3D['h']
    label_BboxNet[4] = label_3D['w']
    label_BboxNet[5] = label_3D['l']
    label_BboxNet[6] = bin_number
    label_BboxNet[7] = residual
    label_BboxNet[8:] = self.mean_car_size
    Rmat = np.asarray([[math.cos(residual), 0, math.sin(residual)], [0, 1, 0], [-math.sin(residual), 0, math.cos(residual)]], dtype='float32')
    center = label_BboxNet[0:3]
    l = label_3D['l']
    w = label_3D['w']
    h = label_3D['h']
    p0 = center + np.dot(Rmat, np.asarray([l / 2.0, 0, w / 2.0], dtype='float32').flatten())
    p1 = center + np.dot(Rmat, np.asarray([-l / 2.0, 0, w / 2.0], dtype='float32').flatten())
    p2 = center + np.dot(Rmat, np.asarray([-l / 2.0, 0, -w / 2.0], dtype='float32').flatten())
    p3 = center + np.dot(Rmat, np.asarray([l / 2.0, 0, -w / 2.0], dtype='float32').flatten())
    p4 = center + np.dot(Rmat, np.asarray([l / 2.0, -h, w / 2.0], dtype='float32').flatten())
    p5 = center + np.dot(Rmat, np.asarray([-l / 2.0, -h, w / 2.0], dtype='float32').flatten())
    p6 = center + np.dot(Rmat, np.asarray([-l / 2.0, -h, -w / 2.0], dtype='float32').flatten())
    p7 = center + np.dot(Rmat, np.asarray([l / 2.0, -h, -w / 2.0], dtype='float32').flatten())
    label_corner = np.array([p0, p1, p2, p3, p4, p5, p6, p7])
    label_corner_flipped = np.array([p2, p3, p0, p1, p6, p7, p4, p5])
    centered_frustum_point_cloud_camera = torch.from_numpy(centered_frustum_point_cloud_camera)
    label_InstanceSeg = torch.from_numpy(label_InstanceSeg)
    label_TNet = torch.from_numpy(label_TNet)
    label_BboxNet = torch.from_numpy(label_BboxNet)
    label_corner = torch.from_numpy(label_corner)
    label_corner_flipped = torch.from_numpy(label_corner_flipped)
    return (centered_frustum_point_cloud_camera, label_InstanceSeg, label_TNet, label_BboxNet, label_corner, label_corner_flipped)

class EvalDatasetFrustumPointNet(torch.utils.data.Dataset):

    def __init__(self, kitti_data_path, kitti_meta_path, type, NH):
        self.img_dir = kitti_data_path + '/object/training/image_2/'
        self.label_dir = kitti_data_path + '/object/training/label_2/'
        self.calib_dir = kitti_data_path + '/object/training/calib/'
        self.lidar_dir = kitti_data_path + '/object/training/velodyne/'
        self.NH = NH
        with open(kitti_meta_path + '/%s_img_ids.pkl' % type, 'rb') as file:
            img_ids = pickle.load(file)
        with open(kitti_meta_path + '/kitti_train_mean_car_size.pkl', 'rb') as file:
            self.mean_car_size = pickle.load(file)
        with open(kitti_meta_path + '/kitti_centered_frustum_mean_xyz.pkl', 'rb') as file:
            self.centered_frustum_mean_xyz = pickle.load(file)
            self.centered_frustum_mean_xyz = self.centered_frustum_mean_xyz.astype(np.float32)
        self.examples = []
        for img_id in img_ids:
            labels = LabelLoader2D3D(img_id, self.label_dir, '.txt', self.calib_dir, '.txt')
            for label in labels:
                label_2d = label['label_2D']
                if label_2d['truncated'] < 0.5 and label_2d['class'] == 'Car':
                    label['img_id'] = img_id
                    self.examples.append(label)
        self.num_examples = len(self.examples)

    def __getitem__(self, index):
        example = self.examples[index]
        img_id = example['img_id']
        lidar_path = self.lidar_dir + img_id + '.bin'
        point_cloud = np.fromfile(lidar_path, dtype=np.float32).reshape(-1, 4)
        orig_point_cloud = point_cloud
        point_cloud = point_cloud[point_cloud[:, 0] > 0, :]
        point_cloud = point_cloud[point_cloud[:, 0] < 80, :]
        calib = calibread(self.calib_dir + img_id + '.txt')
        P2 = calib['P2']
        Tr_velo_to_cam_orig = calib['Tr_velo_to_cam']
        R0_rect_orig = calib['R0_rect']
        R0_rect = np.eye(4)
        R0_rect[0:3, 0:3] = R0_rect_orig
        Tr_velo_to_cam = np.eye(4)
        Tr_velo_to_cam[0:3, :] = Tr_velo_to_cam_orig
        point_cloud_xyz = point_cloud[:, 0:3]
        point_cloud_xyz_hom = np.ones((point_cloud.shape[0], 4))
        point_cloud_xyz_hom[:, 0:3] = point_cloud[:, 0:3]
        img_points_hom = np.dot(P2, np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T))).T
        img_points = np.zeros((img_points_hom.shape[0], 2))
        img_points[:, 0] = img_points_hom[:, 0] / img_points_hom[:, 2]
        img_points[:, 1] = img_points_hom[:, 1] / img_points_hom[:, 2]
        point_cloud_xyz_camera_hom = np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T)).T
        point_cloud_xyz_camera = np.zeros((point_cloud_xyz_camera_hom.shape[0], 3))
        point_cloud_xyz_camera[:, 0] = point_cloud_xyz_camera_hom[:, 0] / point_cloud_xyz_camera_hom[:, 3]
        point_cloud_xyz_camera[:, 1] = point_cloud_xyz_camera_hom[:, 1] / point_cloud_xyz_camera_hom[:, 3]
        point_cloud_xyz_camera[:, 2] = point_cloud_xyz_camera_hom[:, 2] / point_cloud_xyz_camera_hom[:, 3]
        point_cloud_camera = point_cloud
        point_cloud_camera[:, 0:3] = point_cloud_xyz_camera
        label_2D = example['label_2D']
        label_3D = example['label_3D']
        bbox = label_2D['poly']
        u_min = bbox[0, 0]
        u_max = bbox[1, 0]
        v_min = bbox[0, 1]
        v_max = bbox[2, 1]
        u_min_expanded = u_min
        u_max_expanded = u_max
        v_min_expanded = v_min
        v_max_expanded = v_max
        input_2Dbbox = np.array([u_min_expanded, u_max_expanded, v_min_expanded, v_max_expanded])
        row_mask = np.logical_and(np.logical_and(img_points[:, 0] >= u_min_expanded, img_points[:, 0] <= u_max_expanded), np.logical_and(img_points[:, 1] >= v_min_expanded, img_points[:, 1] <= v_max_expanded))
        frustum_point_cloud_xyz = point_cloud_xyz[row_mask, :]
        frustum_point_cloud = point_cloud[row_mask, :]
        frustum_point_cloud_xyz_camera = point_cloud_xyz_camera[row_mask, :]
        frustum_point_cloud_camera = point_cloud_camera[row_mask, :]
        if frustum_point_cloud.shape[0] == 0:
            print(img_id)
            print(frustum_point_cloud.shape)
            return self.__getitem__(0)
        if frustum_point_cloud.shape[0] < 1024:
            row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=True)
        else:
            row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=False)
        frustum_point_cloud_xyz = frustum_point_cloud_xyz[row_idx, :]
        frustum_point_cloud = frustum_point_cloud[row_idx, :]
        frustum_point_cloud_xyz_camera = frustum_point_cloud_xyz_camera[row_idx, :]
        frustum_point_cloud_camera = frustum_point_cloud_camera[row_idx, :]
        points = label_3D['points']
        y_max = points[0, 1]
        y_min = points[4, 1]
        A = np.array([points[0, 0], points[0, 2]])
        B = np.array([points[1, 0], points[1, 2]])
        D = np.array([points[3, 0], points[3, 2]])
        AB = B - A
        AD = D - A
        AB_dot_AB = np.dot(AB, AB)
        AD_dot_AD = np.dot(AD, AD)
        P = np.zeros((frustum_point_cloud_xyz_camera.shape[0], 2))
        P[:, 0] = frustum_point_cloud_xyz_camera[:, 0]
        P[:, 1] = frustum_point_cloud_xyz_camera[:, 2]
        AP = P - A
        AP_dot_AB = np.dot(AP, AB)
        AP_dot_AD = np.dot(AP, AD)
        row_mask = np.logical_and(np.logical_and(frustum_point_cloud_xyz_camera[:, 1] >= y_min, frustum_point_cloud_xyz_camera[:, 1] <= y_max), np.logical_and(np.logical_and(AP_dot_AB >= 0, AP_dot_AB <= AB_dot_AB), np.logical_and(AP_dot_AD >= 0, AP_dot_AD <= AD_dot_AD)))
        gt_point_cloud_xyz_camera = frustum_point_cloud_xyz_camera[row_mask, :]
        label_InstanceSeg = np.zeros((frustum_point_cloud.shape[0],), dtype=np.int64)
        label_InstanceSeg[row_mask] = 1
        u_center = u_min_expanded + (u_max_expanded - u_min_expanded) / 2.0
        v_center = v_min_expanded + (v_max_expanded - v_min_expanded) / 2.0
        center_img_point_hom = np.array([u_center, v_center, 1])
        P2_pseudo_inverse = np.linalg.pinv(P2)
        point_hom = np.dot(P2_pseudo_inverse, center_img_point_hom)
        point = np.array([point_hom[0] / point_hom[3], point_hom[1] / point_hom[3], point_hom[2] / point_hom[3]])
        if point[2] < 0:
            point[0] = -point[0]
            point[2] = -point[2]
        frustum_angle = np.arctan2(point[0], point[2])
        frustum_R = np.asarray([[np.cos(frustum_angle), 0, -np.sin(frustum_angle)], [0, 1, 0], [np.sin(frustum_angle), 0, np.cos(frustum_angle)]], dtype='float32')
        centered_frustum_point_cloud_xyz_camera = np.dot(frustum_R, frustum_point_cloud_xyz_camera.T).T
        centered_frustum_point_cloud_xyz_camera -= self.centered_frustum_mean_xyz
        centered_frustum_point_cloud_camera = frustum_point_cloud_camera
        centered_frustum_point_cloud_camera[:, 0:3] = centered_frustum_point_cloud_xyz_camera
        label_TNet = np.dot(frustum_R, label_3D['center']) - self.centered_frustum_mean_xyz
        centered_r_y = wrapToPi(label_3D['r_y'] - frustum_angle)
        bin_number = getBinNumber(centered_r_y, NH=self.NH)
        bin_center = getBinCenter(bin_number, NH=self.NH)
        residual = wrapToPi(centered_r_y - bin_center)
        label_BboxNet = np.zeros((11,), dtype=np.float32)
        label_BboxNet[0:3] = np.dot(frustum_R, label_3D['center']) - self.centered_frustum_mean_xyz
        label_BboxNet[3] = label_3D['h']
        label_BboxNet[4] = label_3D['w']
        label_BboxNet[5] = label_3D['l']
        label_BboxNet[6] = bin_number
        label_BboxNet[7] = residual
        label_BboxNet[8:] = self.mean_car_size
        Rmat = np.asarray([[math.cos(residual), 0, math.sin(residual)], [0, 1, 0], [-math.sin(residual), 0, math.cos(residual)]], dtype='float32')
        center = label_BboxNet[0:3]
        l = label_3D['l']
        w = label_3D['w']
        h = label_3D['h']
        p0 = center + np.dot(Rmat, np.asarray([l / 2.0, 0, w / 2.0], dtype='float32').flatten())
        p1 = center + np.dot(Rmat, np.asarray([-l / 2.0, 0, w / 2.0], dtype='float32').flatten())
        p2 = center + np.dot(Rmat, np.asarray([-l / 2.0, 0, -w / 2.0], dtype='float32').flatten())
        p3 = center + np.dot(Rmat, np.asarray([l / 2.0, 0, -w / 2.0], dtype='float32').flatten())
        p4 = center + np.dot(Rmat, np.asarray([l / 2.0, -h, w / 2.0], dtype='float32').flatten())
        p5 = center + np.dot(Rmat, np.asarray([-l / 2.0, -h, w / 2.0], dtype='float32').flatten())
        p6 = center + np.dot(Rmat, np.asarray([-l / 2.0, -h, -w / 2.0], dtype='float32').flatten())
        p7 = center + np.dot(Rmat, np.asarray([l / 2.0, -h, -w / 2.0], dtype='float32').flatten())
        label_corner = np.array([p0, p1, p2, p3, p4, p5, p6, p7])
        label_corner_flipped = np.array([p2, p3, p0, p1, p6, p7, p4, p5])
        centered_frustum_point_cloud_camera = torch.from_numpy(centered_frustum_point_cloud_camera)
        label_InstanceSeg = torch.from_numpy(label_InstanceSeg)
        label_TNet = torch.from_numpy(label_TNet)
        label_BboxNet = torch.from_numpy(label_BboxNet)
        label_corner = torch.from_numpy(label_corner)
        label_corner_flipped = torch.from_numpy(label_corner_flipped)
        return (centered_frustum_point_cloud_camera, label_InstanceSeg, label_TNet, label_BboxNet, label_corner, label_corner_flipped, img_id, input_2Dbbox, frustum_R, frustum_angle, self.centered_frustum_mean_xyz)

    def __len__(self):
        return self.num_examples

def __getitem__(self, index):
    example = self.examples[index]
    img_id = example['img_id']
    lidar_path = self.lidar_dir + img_id + '.bin'
    point_cloud = np.fromfile(lidar_path, dtype=np.float32).reshape(-1, 4)
    orig_point_cloud = point_cloud
    point_cloud = point_cloud[point_cloud[:, 0] > 0, :]
    point_cloud = point_cloud[point_cloud[:, 0] < 80, :]
    calib = calibread(self.calib_dir + img_id + '.txt')
    P2 = calib['P2']
    Tr_velo_to_cam_orig = calib['Tr_velo_to_cam']
    R0_rect_orig = calib['R0_rect']
    R0_rect = np.eye(4)
    R0_rect[0:3, 0:3] = R0_rect_orig
    Tr_velo_to_cam = np.eye(4)
    Tr_velo_to_cam[0:3, :] = Tr_velo_to_cam_orig
    point_cloud_xyz = point_cloud[:, 0:3]
    point_cloud_xyz_hom = np.ones((point_cloud.shape[0], 4))
    point_cloud_xyz_hom[:, 0:3] = point_cloud[:, 0:3]
    img_points_hom = np.dot(P2, np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T))).T
    img_points = np.zeros((img_points_hom.shape[0], 2))
    img_points[:, 0] = img_points_hom[:, 0] / img_points_hom[:, 2]
    img_points[:, 1] = img_points_hom[:, 1] / img_points_hom[:, 2]
    point_cloud_xyz_camera_hom = np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T)).T
    point_cloud_xyz_camera = np.zeros((point_cloud_xyz_camera_hom.shape[0], 3))
    point_cloud_xyz_camera[:, 0] = point_cloud_xyz_camera_hom[:, 0] / point_cloud_xyz_camera_hom[:, 3]
    point_cloud_xyz_camera[:, 1] = point_cloud_xyz_camera_hom[:, 1] / point_cloud_xyz_camera_hom[:, 3]
    point_cloud_xyz_camera[:, 2] = point_cloud_xyz_camera_hom[:, 2] / point_cloud_xyz_camera_hom[:, 3]
    point_cloud_camera = point_cloud
    point_cloud_camera[:, 0:3] = point_cloud_xyz_camera
    label_2D = example['label_2D']
    label_3D = example['label_3D']
    bbox = label_2D['poly']
    u_min = bbox[0, 0]
    u_max = bbox[1, 0]
    v_min = bbox[0, 1]
    v_max = bbox[2, 1]
    u_min_expanded = u_min
    u_max_expanded = u_max
    v_min_expanded = v_min
    v_max_expanded = v_max
    input_2Dbbox = np.array([u_min_expanded, u_max_expanded, v_min_expanded, v_max_expanded])
    row_mask = np.logical_and(np.logical_and(img_points[:, 0] >= u_min_expanded, img_points[:, 0] <= u_max_expanded), np.logical_and(img_points[:, 1] >= v_min_expanded, img_points[:, 1] <= v_max_expanded))
    frustum_point_cloud_xyz = point_cloud_xyz[row_mask, :]
    frustum_point_cloud = point_cloud[row_mask, :]
    frustum_point_cloud_xyz_camera = point_cloud_xyz_camera[row_mask, :]
    frustum_point_cloud_camera = point_cloud_camera[row_mask, :]
    if frustum_point_cloud.shape[0] == 0:
        print(img_id)
        print(frustum_point_cloud.shape)
        return self.__getitem__(0)
    if frustum_point_cloud.shape[0] < 1024:
        row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=True)
    else:
        row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=False)
    frustum_point_cloud_xyz = frustum_point_cloud_xyz[row_idx, :]
    frustum_point_cloud = frustum_point_cloud[row_idx, :]
    frustum_point_cloud_xyz_camera = frustum_point_cloud_xyz_camera[row_idx, :]
    frustum_point_cloud_camera = frustum_point_cloud_camera[row_idx, :]
    points = label_3D['points']
    y_max = points[0, 1]
    y_min = points[4, 1]
    A = np.array([points[0, 0], points[0, 2]])
    B = np.array([points[1, 0], points[1, 2]])
    D = np.array([points[3, 0], points[3, 2]])
    AB = B - A
    AD = D - A
    AB_dot_AB = np.dot(AB, AB)
    AD_dot_AD = np.dot(AD, AD)
    P = np.zeros((frustum_point_cloud_xyz_camera.shape[0], 2))
    P[:, 0] = frustum_point_cloud_xyz_camera[:, 0]
    P[:, 1] = frustum_point_cloud_xyz_camera[:, 2]
    AP = P - A
    AP_dot_AB = np.dot(AP, AB)
    AP_dot_AD = np.dot(AP, AD)
    row_mask = np.logical_and(np.logical_and(frustum_point_cloud_xyz_camera[:, 1] >= y_min, frustum_point_cloud_xyz_camera[:, 1] <= y_max), np.logical_and(np.logical_and(AP_dot_AB >= 0, AP_dot_AB <= AB_dot_AB), np.logical_and(AP_dot_AD >= 0, AP_dot_AD <= AD_dot_AD)))
    gt_point_cloud_xyz_camera = frustum_point_cloud_xyz_camera[row_mask, :]
    label_InstanceSeg = np.zeros((frustum_point_cloud.shape[0],), dtype=np.int64)
    label_InstanceSeg[row_mask] = 1
    u_center = u_min_expanded + (u_max_expanded - u_min_expanded) / 2.0
    v_center = v_min_expanded + (v_max_expanded - v_min_expanded) / 2.0
    center_img_point_hom = np.array([u_center, v_center, 1])
    P2_pseudo_inverse = np.linalg.pinv(P2)
    point_hom = np.dot(P2_pseudo_inverse, center_img_point_hom)
    point = np.array([point_hom[0] / point_hom[3], point_hom[1] / point_hom[3], point_hom[2] / point_hom[3]])
    if point[2] < 0:
        point[0] = -point[0]
        point[2] = -point[2]
    frustum_angle = np.arctan2(point[0], point[2])
    frustum_R = np.asarray([[np.cos(frustum_angle), 0, -np.sin(frustum_angle)], [0, 1, 0], [np.sin(frustum_angle), 0, np.cos(frustum_angle)]], dtype='float32')
    centered_frustum_point_cloud_xyz_camera = np.dot(frustum_R, frustum_point_cloud_xyz_camera.T).T
    centered_frustum_point_cloud_xyz_camera -= self.centered_frustum_mean_xyz
    centered_frustum_point_cloud_camera = frustum_point_cloud_camera
    centered_frustum_point_cloud_camera[:, 0:3] = centered_frustum_point_cloud_xyz_camera
    label_TNet = np.dot(frustum_R, label_3D['center']) - self.centered_frustum_mean_xyz
    centered_r_y = wrapToPi(label_3D['r_y'] - frustum_angle)
    bin_number = getBinNumber(centered_r_y, NH=self.NH)
    bin_center = getBinCenter(bin_number, NH=self.NH)
    residual = wrapToPi(centered_r_y - bin_center)
    label_BboxNet = np.zeros((11,), dtype=np.float32)
    label_BboxNet[0:3] = np.dot(frustum_R, label_3D['center']) - self.centered_frustum_mean_xyz
    label_BboxNet[3] = label_3D['h']
    label_BboxNet[4] = label_3D['w']
    label_BboxNet[5] = label_3D['l']
    label_BboxNet[6] = bin_number
    label_BboxNet[7] = residual
    label_BboxNet[8:] = self.mean_car_size
    Rmat = np.asarray([[math.cos(residual), 0, math.sin(residual)], [0, 1, 0], [-math.sin(residual), 0, math.cos(residual)]], dtype='float32')
    center = label_BboxNet[0:3]
    l = label_3D['l']
    w = label_3D['w']
    h = label_3D['h']
    p0 = center + np.dot(Rmat, np.asarray([l / 2.0, 0, w / 2.0], dtype='float32').flatten())
    p1 = center + np.dot(Rmat, np.asarray([-l / 2.0, 0, w / 2.0], dtype='float32').flatten())
    p2 = center + np.dot(Rmat, np.asarray([-l / 2.0, 0, -w / 2.0], dtype='float32').flatten())
    p3 = center + np.dot(Rmat, np.asarray([l / 2.0, 0, -w / 2.0], dtype='float32').flatten())
    p4 = center + np.dot(Rmat, np.asarray([l / 2.0, -h, w / 2.0], dtype='float32').flatten())
    p5 = center + np.dot(Rmat, np.asarray([-l / 2.0, -h, w / 2.0], dtype='float32').flatten())
    p6 = center + np.dot(Rmat, np.asarray([-l / 2.0, -h, -w / 2.0], dtype='float32').flatten())
    p7 = center + np.dot(Rmat, np.asarray([l / 2.0, -h, -w / 2.0], dtype='float32').flatten())
    label_corner = np.array([p0, p1, p2, p3, p4, p5, p6, p7])
    label_corner_flipped = np.array([p2, p3, p0, p1, p6, p7, p4, p5])
    centered_frustum_point_cloud_camera = torch.from_numpy(centered_frustum_point_cloud_camera)
    label_InstanceSeg = torch.from_numpy(label_InstanceSeg)
    label_TNet = torch.from_numpy(label_TNet)
    label_BboxNet = torch.from_numpy(label_BboxNet)
    label_corner = torch.from_numpy(label_corner)
    label_corner_flipped = torch.from_numpy(label_corner_flipped)
    return (centered_frustum_point_cloud_camera, label_InstanceSeg, label_TNet, label_BboxNet, label_corner, label_corner_flipped, img_id, input_2Dbbox, frustum_R, frustum_angle, self.centered_frustum_mean_xyz)

class EvalSequenceDatasetFrustumPointNet(torch.utils.data.Dataset):

    def __init__(self, kitti_data_path, kitti_meta_path, NH, sequence='0000'):
        self.img_dir = kitti_data_path + '/tracking/training/image_02/' + sequence + '/'
        self.lidar_dir = kitti_data_path + '/tracking/training/velodyne/' + sequence + '/'
        self.label_path = kitti_data_path + '/tracking/training/label_02/' + sequence + '.txt'
        self.calib_path = kitti_meta_path + '/tracking/training/calib/' + sequence + '.txt'
        self.NH = NH
        with open(kitti_meta_path + '/kitti_train_mean_car_size.pkl', 'rb') as file:
            self.mean_car_size = pickle.load(file)
        with open(kitti_meta_path + '/kitti_centered_frustum_mean_xyz.pkl', 'rb') as file:
            self.centered_frustum_mean_xyz = pickle.load(file)
            self.centered_frustum_mean_xyz = self.centered_frustum_mean_xyz.astype(np.float32)
        img_ids = []
        img_names = os.listdir(self.img_dir)
        for img_name in img_names:
            img_id = img_name.split('.png')[0]
            img_ids.append(img_id)
        self.examples = []
        for img_id in img_ids:
            if img_id.lstrip('0') == '':
                img_id_float = 0.0
            else:
                img_id_float = float(img_id.lstrip('0'))
            labels = LabelLoader2D3D_sequence(img_id, img_id_float, self.label_path, self.calib_path)
            for label in labels:
                label_2d = label['label_2D']
                if label_2d['truncated'] < 0.5 and label_2d['class'] == 'Car':
                    label['img_id'] = img_id
                    self.examples.append(label)
        self.num_examples = len(self.examples)

    def __getitem__(self, index):
        example = self.examples[index]
        img_id = example['img_id']
        lidar_path = self.lidar_dir + img_id + '.bin'
        point_cloud = np.fromfile(lidar_path, dtype=np.float32).reshape(-1, 4)
        orig_point_cloud = point_cloud
        point_cloud = point_cloud[point_cloud[:, 0] > 0, :]
        point_cloud = point_cloud[point_cloud[:, 0] < 80, :]
        calib = calibread(self.calib_path)
        P2 = calib['P2']
        Tr_velo_to_cam_orig = calib['Tr_velo_to_cam']
        R0_rect_orig = calib['R0_rect']
        R0_rect = np.eye(4)
        R0_rect[0:3, 0:3] = R0_rect_orig
        Tr_velo_to_cam = np.eye(4)
        Tr_velo_to_cam[0:3, :] = Tr_velo_to_cam_orig
        point_cloud_xyz = point_cloud[:, 0:3]
        point_cloud_xyz_hom = np.ones((point_cloud.shape[0], 4))
        point_cloud_xyz_hom[:, 0:3] = point_cloud[:, 0:3]
        img_points_hom = np.dot(P2, np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T))).T
        img_points = np.zeros((img_points_hom.shape[0], 2))
        img_points[:, 0] = img_points_hom[:, 0] / img_points_hom[:, 2]
        img_points[:, 1] = img_points_hom[:, 1] / img_points_hom[:, 2]
        point_cloud_xyz_camera_hom = np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T)).T
        point_cloud_xyz_camera = np.zeros((point_cloud_xyz_camera_hom.shape[0], 3))
        point_cloud_xyz_camera[:, 0] = point_cloud_xyz_camera_hom[:, 0] / point_cloud_xyz_camera_hom[:, 3]
        point_cloud_xyz_camera[:, 1] = point_cloud_xyz_camera_hom[:, 1] / point_cloud_xyz_camera_hom[:, 3]
        point_cloud_xyz_camera[:, 2] = point_cloud_xyz_camera_hom[:, 2] / point_cloud_xyz_camera_hom[:, 3]
        point_cloud_camera = point_cloud
        point_cloud_camera[:, 0:3] = point_cloud_xyz_camera
        label_2D = example['label_2D']
        label_3D = example['label_3D']
        bbox = label_2D['poly']
        u_min = bbox[0, 0]
        u_max = bbox[1, 0]
        v_min = bbox[0, 1]
        v_max = bbox[2, 1]
        u_min_expanded = u_min
        u_max_expanded = u_max
        v_min_expanded = v_min
        v_max_expanded = v_max
        input_2Dbbox = np.array([u_min_expanded, u_max_expanded, v_min_expanded, v_max_expanded])
        row_mask = np.logical_and(np.logical_and(img_points[:, 0] >= u_min_expanded, img_points[:, 0] <= u_max_expanded), np.logical_and(img_points[:, 1] >= v_min_expanded, img_points[:, 1] <= v_max_expanded))
        frustum_point_cloud_xyz = point_cloud_xyz[row_mask, :]
        frustum_point_cloud = point_cloud[row_mask, :]
        frustum_point_cloud_xyz_camera = point_cloud_xyz_camera[row_mask, :]
        frustum_point_cloud_camera = point_cloud_camera[row_mask, :]
        if frustum_point_cloud.shape[0] == 0:
            print(img_id)
            print(frustum_point_cloud.shape)
            return self.__getitem__(0)
        if frustum_point_cloud.shape[0] < 1024:
            row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=True)
        else:
            row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=False)
        frustum_point_cloud_xyz = frustum_point_cloud_xyz[row_idx, :]
        frustum_point_cloud = frustum_point_cloud[row_idx, :]
        frustum_point_cloud_xyz_camera = frustum_point_cloud_xyz_camera[row_idx, :]
        frustum_point_cloud_camera = frustum_point_cloud_camera[row_idx, :]
        points = label_3D['points']
        y_max = points[0, 1]
        y_min = points[4, 1]
        A = np.array([points[0, 0], points[0, 2]])
        B = np.array([points[1, 0], points[1, 2]])
        D = np.array([points[3, 0], points[3, 2]])
        AB = B - A
        AD = D - A
        AB_dot_AB = np.dot(AB, AB)
        AD_dot_AD = np.dot(AD, AD)
        P = np.zeros((frustum_point_cloud_xyz_camera.shape[0], 2))
        P[:, 0] = frustum_point_cloud_xyz_camera[:, 0]
        P[:, 1] = frustum_point_cloud_xyz_camera[:, 2]
        AP = P - A
        AP_dot_AB = np.dot(AP, AB)
        AP_dot_AD = np.dot(AP, AD)
        row_mask = np.logical_and(np.logical_and(frustum_point_cloud_xyz_camera[:, 1] >= y_min, frustum_point_cloud_xyz_camera[:, 1] <= y_max), np.logical_and(np.logical_and(AP_dot_AB >= 0, AP_dot_AB <= AB_dot_AB), np.logical_and(AP_dot_AD >= 0, AP_dot_AD <= AD_dot_AD)))
        gt_point_cloud_xyz_camera = frustum_point_cloud_xyz_camera[row_mask, :]
        label_InstanceSeg = np.zeros((frustum_point_cloud.shape[0],), dtype=np.int64)
        label_InstanceSeg[row_mask] = 1
        u_center = u_min_expanded + (u_max_expanded - u_min_expanded) / 2.0
        v_center = v_min_expanded + (v_max_expanded - v_min_expanded) / 2.0
        center_img_point_hom = np.array([u_center, v_center, 1])
        P2_pseudo_inverse = np.linalg.pinv(P2)
        point_hom = np.dot(P2_pseudo_inverse, center_img_point_hom)
        point = np.array([point_hom[0] / point_hom[3], point_hom[1] / point_hom[3], point_hom[2] / point_hom[3]])
        if point[2] < 0:
            point[0] = -point[0]
            point[2] = -point[2]
        frustum_angle = np.arctan2(point[0], point[2])
        frustum_R = np.asarray([[np.cos(frustum_angle), 0, -np.sin(frustum_angle)], [0, 1, 0], [np.sin(frustum_angle), 0, np.cos(frustum_angle)]], dtype='float32')
        centered_frustum_point_cloud_xyz_camera = np.dot(frustum_R, frustum_point_cloud_xyz_camera.T).T
        centered_frustum_point_cloud_xyz_camera -= self.centered_frustum_mean_xyz
        centered_frustum_point_cloud_camera = frustum_point_cloud_camera
        centered_frustum_point_cloud_camera[:, 0:3] = centered_frustum_point_cloud_xyz_camera
        label_TNet = np.dot(frustum_R, label_3D['center']) - self.centered_frustum_mean_xyz
        centered_r_y = wrapToPi(label_3D['r_y'] - frustum_angle)
        bin_number = getBinNumber(centered_r_y, NH=self.NH)
        bin_center = getBinCenter(bin_number, NH=self.NH)
        residual = wrapToPi(centered_r_y - bin_center)
        label_BboxNet = np.zeros((11,), dtype=np.float32)
        label_BboxNet[0:3] = np.dot(frustum_R, label_3D['center']) - self.centered_frustum_mean_xyz
        label_BboxNet[3] = label_3D['h']
        label_BboxNet[4] = label_3D['w']
        label_BboxNet[5] = label_3D['l']
        label_BboxNet[6] = bin_number
        label_BboxNet[7] = residual
        label_BboxNet[8:] = self.mean_car_size
        Rmat = np.asarray([[math.cos(residual), 0, math.sin(residual)], [0, 1, 0], [-math.sin(residual), 0, math.cos(residual)]], dtype='float32')
        center = label_BboxNet[0:3]
        l = label_3D['l']
        w = label_3D['w']
        h = label_3D['h']
        p0 = center + np.dot(Rmat, np.asarray([l / 2.0, 0, w / 2.0], dtype='float32').flatten())
        p1 = center + np.dot(Rmat, np.asarray([-l / 2.0, 0, w / 2.0], dtype='float32').flatten())
        p2 = center + np.dot(Rmat, np.asarray([-l / 2.0, 0, -w / 2.0], dtype='float32').flatten())
        p3 = center + np.dot(Rmat, np.asarray([l / 2.0, 0, -w / 2.0], dtype='float32').flatten())
        p4 = center + np.dot(Rmat, np.asarray([l / 2.0, -h, w / 2.0], dtype='float32').flatten())
        p5 = center + np.dot(Rmat, np.asarray([-l / 2.0, -h, w / 2.0], dtype='float32').flatten())
        p6 = center + np.dot(Rmat, np.asarray([-l / 2.0, -h, -w / 2.0], dtype='float32').flatten())
        p7 = center + np.dot(Rmat, np.asarray([l / 2.0, -h, -w / 2.0], dtype='float32').flatten())
        label_corner = np.array([p0, p1, p2, p3, p4, p5, p6, p7])
        label_corner_flipped = np.array([p2, p3, p0, p1, p6, p7, p4, p5])
        centered_frustum_point_cloud_camera = torch.from_numpy(centered_frustum_point_cloud_camera)
        label_InstanceSeg = torch.from_numpy(label_InstanceSeg)
        label_TNet = torch.from_numpy(label_TNet)
        label_BboxNet = torch.from_numpy(label_BboxNet)
        label_corner = torch.from_numpy(label_corner)
        label_corner_flipped = torch.from_numpy(label_corner_flipped)
        return (centered_frustum_point_cloud_camera, label_InstanceSeg, label_TNet, label_BboxNet, label_corner, label_corner_flipped, img_id, input_2Dbbox, frustum_R, frustum_angle, self.centered_frustum_mean_xyz)

    def __len__(self):
        return self.num_examples

def __getitem__(self, index):
    example = self.examples[index]
    img_id = example['img_id']
    lidar_path = self.lidar_dir + img_id + '.bin'
    point_cloud = np.fromfile(lidar_path, dtype=np.float32).reshape(-1, 4)
    orig_point_cloud = point_cloud
    point_cloud = point_cloud[point_cloud[:, 0] > 0, :]
    point_cloud = point_cloud[point_cloud[:, 0] < 80, :]
    calib = calibread(self.calib_path)
    P2 = calib['P2']
    Tr_velo_to_cam_orig = calib['Tr_velo_to_cam']
    R0_rect_orig = calib['R0_rect']
    R0_rect = np.eye(4)
    R0_rect[0:3, 0:3] = R0_rect_orig
    Tr_velo_to_cam = np.eye(4)
    Tr_velo_to_cam[0:3, :] = Tr_velo_to_cam_orig
    point_cloud_xyz = point_cloud[:, 0:3]
    point_cloud_xyz_hom = np.ones((point_cloud.shape[0], 4))
    point_cloud_xyz_hom[:, 0:3] = point_cloud[:, 0:3]
    img_points_hom = np.dot(P2, np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T))).T
    img_points = np.zeros((img_points_hom.shape[0], 2))
    img_points[:, 0] = img_points_hom[:, 0] / img_points_hom[:, 2]
    img_points[:, 1] = img_points_hom[:, 1] / img_points_hom[:, 2]
    point_cloud_xyz_camera_hom = np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T)).T
    point_cloud_xyz_camera = np.zeros((point_cloud_xyz_camera_hom.shape[0], 3))
    point_cloud_xyz_camera[:, 0] = point_cloud_xyz_camera_hom[:, 0] / point_cloud_xyz_camera_hom[:, 3]
    point_cloud_xyz_camera[:, 1] = point_cloud_xyz_camera_hom[:, 1] / point_cloud_xyz_camera_hom[:, 3]
    point_cloud_xyz_camera[:, 2] = point_cloud_xyz_camera_hom[:, 2] / point_cloud_xyz_camera_hom[:, 3]
    point_cloud_camera = point_cloud
    point_cloud_camera[:, 0:3] = point_cloud_xyz_camera
    label_2D = example['label_2D']
    label_3D = example['label_3D']
    bbox = label_2D['poly']
    u_min = bbox[0, 0]
    u_max = bbox[1, 0]
    v_min = bbox[0, 1]
    v_max = bbox[2, 1]
    u_min_expanded = u_min
    u_max_expanded = u_max
    v_min_expanded = v_min
    v_max_expanded = v_max
    input_2Dbbox = np.array([u_min_expanded, u_max_expanded, v_min_expanded, v_max_expanded])
    row_mask = np.logical_and(np.logical_and(img_points[:, 0] >= u_min_expanded, img_points[:, 0] <= u_max_expanded), np.logical_and(img_points[:, 1] >= v_min_expanded, img_points[:, 1] <= v_max_expanded))
    frustum_point_cloud_xyz = point_cloud_xyz[row_mask, :]
    frustum_point_cloud = point_cloud[row_mask, :]
    frustum_point_cloud_xyz_camera = point_cloud_xyz_camera[row_mask, :]
    frustum_point_cloud_camera = point_cloud_camera[row_mask, :]
    if frustum_point_cloud.shape[0] == 0:
        print(img_id)
        print(frustum_point_cloud.shape)
        return self.__getitem__(0)
    if frustum_point_cloud.shape[0] < 1024:
        row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=True)
    else:
        row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=False)
    frustum_point_cloud_xyz = frustum_point_cloud_xyz[row_idx, :]
    frustum_point_cloud = frustum_point_cloud[row_idx, :]
    frustum_point_cloud_xyz_camera = frustum_point_cloud_xyz_camera[row_idx, :]
    frustum_point_cloud_camera = frustum_point_cloud_camera[row_idx, :]
    points = label_3D['points']
    y_max = points[0, 1]
    y_min = points[4, 1]
    A = np.array([points[0, 0], points[0, 2]])
    B = np.array([points[1, 0], points[1, 2]])
    D = np.array([points[3, 0], points[3, 2]])
    AB = B - A
    AD = D - A
    AB_dot_AB = np.dot(AB, AB)
    AD_dot_AD = np.dot(AD, AD)
    P = np.zeros((frustum_point_cloud_xyz_camera.shape[0], 2))
    P[:, 0] = frustum_point_cloud_xyz_camera[:, 0]
    P[:, 1] = frustum_point_cloud_xyz_camera[:, 2]
    AP = P - A
    AP_dot_AB = np.dot(AP, AB)
    AP_dot_AD = np.dot(AP, AD)
    row_mask = np.logical_and(np.logical_and(frustum_point_cloud_xyz_camera[:, 1] >= y_min, frustum_point_cloud_xyz_camera[:, 1] <= y_max), np.logical_and(np.logical_and(AP_dot_AB >= 0, AP_dot_AB <= AB_dot_AB), np.logical_and(AP_dot_AD >= 0, AP_dot_AD <= AD_dot_AD)))
    gt_point_cloud_xyz_camera = frustum_point_cloud_xyz_camera[row_mask, :]
    label_InstanceSeg = np.zeros((frustum_point_cloud.shape[0],), dtype=np.int64)
    label_InstanceSeg[row_mask] = 1
    u_center = u_min_expanded + (u_max_expanded - u_min_expanded) / 2.0
    v_center = v_min_expanded + (v_max_expanded - v_min_expanded) / 2.0
    center_img_point_hom = np.array([u_center, v_center, 1])
    P2_pseudo_inverse = np.linalg.pinv(P2)
    point_hom = np.dot(P2_pseudo_inverse, center_img_point_hom)
    point = np.array([point_hom[0] / point_hom[3], point_hom[1] / point_hom[3], point_hom[2] / point_hom[3]])
    if point[2] < 0:
        point[0] = -point[0]
        point[2] = -point[2]
    frustum_angle = np.arctan2(point[0], point[2])
    frustum_R = np.asarray([[np.cos(frustum_angle), 0, -np.sin(frustum_angle)], [0, 1, 0], [np.sin(frustum_angle), 0, np.cos(frustum_angle)]], dtype='float32')
    centered_frustum_point_cloud_xyz_camera = np.dot(frustum_R, frustum_point_cloud_xyz_camera.T).T
    centered_frustum_point_cloud_xyz_camera -= self.centered_frustum_mean_xyz
    centered_frustum_point_cloud_camera = frustum_point_cloud_camera
    centered_frustum_point_cloud_camera[:, 0:3] = centered_frustum_point_cloud_xyz_camera
    label_TNet = np.dot(frustum_R, label_3D['center']) - self.centered_frustum_mean_xyz
    centered_r_y = wrapToPi(label_3D['r_y'] - frustum_angle)
    bin_number = getBinNumber(centered_r_y, NH=self.NH)
    bin_center = getBinCenter(bin_number, NH=self.NH)
    residual = wrapToPi(centered_r_y - bin_center)
    label_BboxNet = np.zeros((11,), dtype=np.float32)
    label_BboxNet[0:3] = np.dot(frustum_R, label_3D['center']) - self.centered_frustum_mean_xyz
    label_BboxNet[3] = label_3D['h']
    label_BboxNet[4] = label_3D['w']
    label_BboxNet[5] = label_3D['l']
    label_BboxNet[6] = bin_number
    label_BboxNet[7] = residual
    label_BboxNet[8:] = self.mean_car_size
    Rmat = np.asarray([[math.cos(residual), 0, math.sin(residual)], [0, 1, 0], [-math.sin(residual), 0, math.cos(residual)]], dtype='float32')
    center = label_BboxNet[0:3]
    l = label_3D['l']
    w = label_3D['w']
    h = label_3D['h']
    p0 = center + np.dot(Rmat, np.asarray([l / 2.0, 0, w / 2.0], dtype='float32').flatten())
    p1 = center + np.dot(Rmat, np.asarray([-l / 2.0, 0, w / 2.0], dtype='float32').flatten())
    p2 = center + np.dot(Rmat, np.asarray([-l / 2.0, 0, -w / 2.0], dtype='float32').flatten())
    p3 = center + np.dot(Rmat, np.asarray([l / 2.0, 0, -w / 2.0], dtype='float32').flatten())
    p4 = center + np.dot(Rmat, np.asarray([l / 2.0, -h, w / 2.0], dtype='float32').flatten())
    p5 = center + np.dot(Rmat, np.asarray([-l / 2.0, -h, w / 2.0], dtype='float32').flatten())
    p6 = center + np.dot(Rmat, np.asarray([-l / 2.0, -h, -w / 2.0], dtype='float32').flatten())
    p7 = center + np.dot(Rmat, np.asarray([l / 2.0, -h, -w / 2.0], dtype='float32').flatten())
    label_corner = np.array([p0, p1, p2, p3, p4, p5, p6, p7])
    label_corner_flipped = np.array([p2, p3, p0, p1, p6, p7, p4, p5])
    centered_frustum_point_cloud_camera = torch.from_numpy(centered_frustum_point_cloud_camera)
    label_InstanceSeg = torch.from_numpy(label_InstanceSeg)
    label_TNet = torch.from_numpy(label_TNet)
    label_BboxNet = torch.from_numpy(label_BboxNet)
    label_corner = torch.from_numpy(label_corner)
    label_corner_flipped = torch.from_numpy(label_corner_flipped)
    return (centered_frustum_point_cloud_camera, label_InstanceSeg, label_TNet, label_BboxNet, label_corner, label_corner_flipped, img_id, input_2Dbbox, frustum_R, frustum_angle, self.centered_frustum_mean_xyz)

class DatasetKittiTest(torch.utils.data.Dataset):

    def __init__(self, kitti_data_path, kitti_meta_path, NH):
        self.img_dir = kitti_data_path + '/object/testing/image_2/'
        self.calib_dir = kitti_data_path + '/object/testing/calib/'
        self.lidar_dir = kitti_data_path + '/object/testing/velodyne/'
        self.detections_2d_dir = kitti_meta_path + '/object/testing/2d_detections/'
        self.NH = NH
        with open(kitti_meta_path + '/kitti_train_mean_car_size.pkl', 'rb') as file:
            self.mean_car_size = pickle.load(file)
        with open(kitti_meta_path + '/kitti_centered_frustum_mean_xyz.pkl', 'rb') as file:
            self.centered_frustum_mean_xyz = pickle.load(file)
            self.centered_frustum_mean_xyz = self.centered_frustum_mean_xyz.astype(np.float32)
        img_ids = []
        img_names = os.listdir(self.img_dir)
        for img_name in img_names:
            img_id = img_name.split('.png')[0]
            img_ids.append(img_id)
        self.examples = []
        for img_id in img_ids:
            detections_file_path = self.detections_2d_dir + img_id + '.txt'
            with open(detections_file_path) as file:
                for line in file:
                    values = line.split()
                    object_class = float(values[3])
                    if object_class == 1:
                        u_min = float(values[4])
                        v_min = float(values[5])
                        u_max = float(values[6])
                        v_max = float(values[7])
                        score_2d = float(values[8])
                        detection_2d = {}
                        detection_2d['u_min'] = u_min
                        detection_2d['v_min'] = v_min
                        detection_2d['u_max'] = u_max
                        detection_2d['v_max'] = v_max
                        detection_2d['score_2d'] = score_2d
                        detection_2d['img_id'] = img_id
                        self.examples.append(detection_2d)
        self.num_examples = len(self.examples)

    def __getitem__(self, index):
        example = self.examples[index]
        img_id = example['img_id']
        lidar_path = self.lidar_dir + img_id + '.bin'
        point_cloud = np.fromfile(lidar_path, dtype=np.float32).reshape(-1, 4)
        orig_point_cloud = point_cloud
        point_cloud = point_cloud[point_cloud[:, 0] > -5, :]
        point_cloud = point_cloud[point_cloud[:, 0] < 80, :]
        calib = calibread(self.calib_dir + img_id + '.txt')
        P2 = calib['P2']
        Tr_velo_to_cam_orig = calib['Tr_velo_to_cam']
        R0_rect_orig = calib['R0_rect']
        R0_rect = np.eye(4)
        R0_rect[0:3, 0:3] = R0_rect_orig
        Tr_velo_to_cam = np.eye(4)
        Tr_velo_to_cam[0:3, :] = Tr_velo_to_cam_orig
        point_cloud_xyz = point_cloud[:, 0:3]
        point_cloud_xyz_hom = np.ones((point_cloud.shape[0], 4))
        point_cloud_xyz_hom[:, 0:3] = point_cloud[:, 0:3]
        img_points_hom = np.dot(P2, np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T))).T
        img_points = np.zeros((img_points_hom.shape[0], 2))
        img_points[:, 0] = img_points_hom[:, 0] / img_points_hom[:, 2]
        img_points[:, 1] = img_points_hom[:, 1] / img_points_hom[:, 2]
        point_cloud_xyz_camera_hom = np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T)).T
        point_cloud_xyz_camera = np.zeros((point_cloud_xyz_camera_hom.shape[0], 3))
        point_cloud_xyz_camera[:, 0] = point_cloud_xyz_camera_hom[:, 0] / point_cloud_xyz_camera_hom[:, 3]
        point_cloud_xyz_camera[:, 1] = point_cloud_xyz_camera_hom[:, 1] / point_cloud_xyz_camera_hom[:, 3]
        point_cloud_xyz_camera[:, 2] = point_cloud_xyz_camera_hom[:, 2] / point_cloud_xyz_camera_hom[:, 3]
        point_cloud_camera = point_cloud
        point_cloud_camera[:, 0:3] = point_cloud_xyz_camera
        u_min = example['u_min']
        u_max = example['u_max']
        v_min = example['v_min']
        v_max = example['v_max']
        score_2d = example['score_2d']
        input_2Dbbox = np.array([u_min, u_max, v_min, v_max])
        row_mask = np.logical_and(np.logical_and(img_points[:, 0] >= u_min, img_points[:, 0] <= u_max), np.logical_and(img_points[:, 1] >= v_min, img_points[:, 1] <= v_max))
        frustum_point_cloud_xyz = point_cloud_xyz[row_mask, :]
        frustum_point_cloud = point_cloud[row_mask, :]
        frustum_point_cloud_xyz_camera = point_cloud_xyz_camera[row_mask, :]
        frustum_point_cloud_camera = point_cloud_camera[row_mask, :]
        empty_frustum_flag = 0
        if frustum_point_cloud.shape[0] == 0:
            empty_frustum_flag = 1
            frustum_point_cloud = np.zeros((1024, 4), dtype=np.float32)
            frustum_point_cloud_xyz = np.zeros((1024, 3), dtype=np.float32)
            frustum_point_cloud_camera = np.zeros((1024, 4), dtype=np.float32)
            frustum_point_cloud_xyz_camera = np.zeros((1024, 3), dtype=np.float32)
        if frustum_point_cloud.shape[0] < 1024:
            row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=True)
        else:
            row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=False)
        frustum_point_cloud_xyz = frustum_point_cloud_xyz[row_idx, :]
        frustum_point_cloud = frustum_point_cloud[row_idx, :]
        frustum_point_cloud_xyz_camera = frustum_point_cloud_xyz_camera[row_idx, :]
        frustum_point_cloud_camera = frustum_point_cloud_camera[row_idx, :]
        u_center = u_min + (u_max - u_min) / 2.0
        v_center = v_min + (v_max - v_min) / 2.0
        center_img_point_hom = np.array([u_center, v_center, 1])
        P2_pseudo_inverse = np.linalg.pinv(P2)
        point_hom = np.dot(P2_pseudo_inverse, center_img_point_hom)
        point = np.array([point_hom[0] / point_hom[3], point_hom[1] / point_hom[3], point_hom[2] / point_hom[3]])
        if point[2] < 0:
            point[0] = -point[0]
            point[2] = -point[2]
        frustum_angle = np.arctan2(point[0], point[2])
        frustum_R = np.asarray([[np.cos(frustum_angle), 0, -np.sin(frustum_angle)], [0, 1, 0], [np.sin(frustum_angle), 0, np.cos(frustum_angle)]], dtype='float32')
        centered_frustum_point_cloud_xyz_camera = np.dot(frustum_R, frustum_point_cloud_xyz_camera.T).T
        centered_frustum_point_cloud_xyz_camera -= self.centered_frustum_mean_xyz
        centered_frustum_point_cloud_camera = frustum_point_cloud_camera
        centered_frustum_point_cloud_camera[:, 0:3] = centered_frustum_point_cloud_xyz_camera
        centered_frustum_point_cloud_camera = torch.from_numpy(centered_frustum_point_cloud_camera)
        return (centered_frustum_point_cloud_camera, img_id, input_2Dbbox, frustum_R, frustum_angle, empty_frustum_flag, self.centered_frustum_mean_xyz, self.mean_car_size, score_2d)

    def __len__(self):
        return self.num_examples

def __getitem__(self, index):
    example = self.examples[index]
    img_id = example['img_id']
    lidar_path = self.lidar_dir + img_id + '.bin'
    point_cloud = np.fromfile(lidar_path, dtype=np.float32).reshape(-1, 4)
    orig_point_cloud = point_cloud
    point_cloud = point_cloud[point_cloud[:, 0] > -5, :]
    point_cloud = point_cloud[point_cloud[:, 0] < 80, :]
    calib = calibread(self.calib_dir + img_id + '.txt')
    P2 = calib['P2']
    Tr_velo_to_cam_orig = calib['Tr_velo_to_cam']
    R0_rect_orig = calib['R0_rect']
    R0_rect = np.eye(4)
    R0_rect[0:3, 0:3] = R0_rect_orig
    Tr_velo_to_cam = np.eye(4)
    Tr_velo_to_cam[0:3, :] = Tr_velo_to_cam_orig
    point_cloud_xyz = point_cloud[:, 0:3]
    point_cloud_xyz_hom = np.ones((point_cloud.shape[0], 4))
    point_cloud_xyz_hom[:, 0:3] = point_cloud[:, 0:3]
    img_points_hom = np.dot(P2, np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T))).T
    img_points = np.zeros((img_points_hom.shape[0], 2))
    img_points[:, 0] = img_points_hom[:, 0] / img_points_hom[:, 2]
    img_points[:, 1] = img_points_hom[:, 1] / img_points_hom[:, 2]
    point_cloud_xyz_camera_hom = np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T)).T
    point_cloud_xyz_camera = np.zeros((point_cloud_xyz_camera_hom.shape[0], 3))
    point_cloud_xyz_camera[:, 0] = point_cloud_xyz_camera_hom[:, 0] / point_cloud_xyz_camera_hom[:, 3]
    point_cloud_xyz_camera[:, 1] = point_cloud_xyz_camera_hom[:, 1] / point_cloud_xyz_camera_hom[:, 3]
    point_cloud_xyz_camera[:, 2] = point_cloud_xyz_camera_hom[:, 2] / point_cloud_xyz_camera_hom[:, 3]
    point_cloud_camera = point_cloud
    point_cloud_camera[:, 0:3] = point_cloud_xyz_camera
    u_min = example['u_min']
    u_max = example['u_max']
    v_min = example['v_min']
    v_max = example['v_max']
    score_2d = example['score_2d']
    input_2Dbbox = np.array([u_min, u_max, v_min, v_max])
    row_mask = np.logical_and(np.logical_and(img_points[:, 0] >= u_min, img_points[:, 0] <= u_max), np.logical_and(img_points[:, 1] >= v_min, img_points[:, 1] <= v_max))
    frustum_point_cloud_xyz = point_cloud_xyz[row_mask, :]
    frustum_point_cloud = point_cloud[row_mask, :]
    frustum_point_cloud_xyz_camera = point_cloud_xyz_camera[row_mask, :]
    frustum_point_cloud_camera = point_cloud_camera[row_mask, :]
    empty_frustum_flag = 0
    if frustum_point_cloud.shape[0] == 0:
        empty_frustum_flag = 1
        frustum_point_cloud = np.zeros((1024, 4), dtype=np.float32)
        frustum_point_cloud_xyz = np.zeros((1024, 3), dtype=np.float32)
        frustum_point_cloud_camera = np.zeros((1024, 4), dtype=np.float32)
        frustum_point_cloud_xyz_camera = np.zeros((1024, 3), dtype=np.float32)
    if frustum_point_cloud.shape[0] < 1024:
        row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=True)
    else:
        row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=False)
    frustum_point_cloud_xyz = frustum_point_cloud_xyz[row_idx, :]
    frustum_point_cloud = frustum_point_cloud[row_idx, :]
    frustum_point_cloud_xyz_camera = frustum_point_cloud_xyz_camera[row_idx, :]
    frustum_point_cloud_camera = frustum_point_cloud_camera[row_idx, :]
    u_center = u_min + (u_max - u_min) / 2.0
    v_center = v_min + (v_max - v_min) / 2.0
    center_img_point_hom = np.array([u_center, v_center, 1])
    P2_pseudo_inverse = np.linalg.pinv(P2)
    point_hom = np.dot(P2_pseudo_inverse, center_img_point_hom)
    point = np.array([point_hom[0] / point_hom[3], point_hom[1] / point_hom[3], point_hom[2] / point_hom[3]])
    if point[2] < 0:
        point[0] = -point[0]
        point[2] = -point[2]
    frustum_angle = np.arctan2(point[0], point[2])
    frustum_R = np.asarray([[np.cos(frustum_angle), 0, -np.sin(frustum_angle)], [0, 1, 0], [np.sin(frustum_angle), 0, np.cos(frustum_angle)]], dtype='float32')
    centered_frustum_point_cloud_xyz_camera = np.dot(frustum_R, frustum_point_cloud_xyz_camera.T).T
    centered_frustum_point_cloud_xyz_camera -= self.centered_frustum_mean_xyz
    centered_frustum_point_cloud_camera = frustum_point_cloud_camera
    centered_frustum_point_cloud_camera[:, 0:3] = centered_frustum_point_cloud_xyz_camera
    centered_frustum_point_cloud_camera = torch.from_numpy(centered_frustum_point_cloud_camera)
    return (centered_frustum_point_cloud_camera, img_id, input_2Dbbox, frustum_R, frustum_angle, empty_frustum_flag, self.centered_frustum_mean_xyz, self.mean_car_size, score_2d)

class DatasetKittiTestSequence(torch.utils.data.Dataset):

    def __init__(self, kitti_data_path, kitti_meta_path, NH, sequence):
        self.img_dir = kitti_data_path + '/tracking/testing/image_02/' + sequence + '/'
        self.lidar_dir = kitti_data_path + '/tracking/testing/velodyne/' + sequence + '/'
        self.calib_path = kitti_meta_path + '/tracking/testing/calib/' + sequence + '.txt'
        self.detections_2d_path = kitti_meta_path + '/tracking/testing/2d_detections/' + sequence + '/inferResult_1.txt'
        self.NH = NH
        with open(kitti_meta_path + '/kitti_train_mean_car_size.pkl', 'rb') as file:
            self.mean_car_size = pickle.load(file)
        with open(kitti_meta_path + '/kitti_centered_frustum_mean_xyz.pkl', 'rb') as file:
            self.centered_frustum_mean_xyz = pickle.load(file)
            self.centered_frustum_mean_xyz = self.centered_frustum_mean_xyz.astype(np.float32)
        self.examples = []
        with open(self.detections_2d_path) as file:
            for line in file:
                values = line.split()
                object_class = float(values[3])
                if object_class == 1:
                    img_id = values[0]
                    u_min = float(values[4])
                    v_min = float(values[5])
                    u_max = float(values[6])
                    v_max = float(values[7])
                    score_2d = float(values[8])
                    detection_2d = {}
                    detection_2d['u_min'] = u_min
                    detection_2d['v_min'] = v_min
                    detection_2d['u_max'] = u_max
                    detection_2d['v_max'] = v_max
                    detection_2d['score_2d'] = score_2d
                    detection_2d['img_id'] = img_id
                    self.examples.append(detection_2d)
        self.num_examples = len(self.examples)

    def __getitem__(self, index):
        example = self.examples[index]
        img_id = example['img_id']
        lidar_path = self.lidar_dir + img_id + '.bin'
        point_cloud = np.fromfile(lidar_path, dtype=np.float32).reshape(-1, 4)
        orig_point_cloud = point_cloud
        point_cloud = point_cloud[point_cloud[:, 0] > -5, :]
        point_cloud = point_cloud[point_cloud[:, 0] < 80, :]
        calib = calibread(self.calib_path)
        P2 = calib['P2']
        Tr_velo_to_cam_orig = calib['Tr_velo_to_cam']
        R0_rect_orig = calib['R0_rect']
        R0_rect = np.eye(4)
        R0_rect[0:3, 0:3] = R0_rect_orig
        Tr_velo_to_cam = np.eye(4)
        Tr_velo_to_cam[0:3, :] = Tr_velo_to_cam_orig
        point_cloud_xyz = point_cloud[:, 0:3]
        point_cloud_xyz_hom = np.ones((point_cloud.shape[0], 4))
        point_cloud_xyz_hom[:, 0:3] = point_cloud[:, 0:3]
        img_points_hom = np.dot(P2, np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T))).T
        img_points = np.zeros((img_points_hom.shape[0], 2))
        img_points[:, 0] = img_points_hom[:, 0] / img_points_hom[:, 2]
        img_points[:, 1] = img_points_hom[:, 1] / img_points_hom[:, 2]
        point_cloud_xyz_camera_hom = np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T)).T
        point_cloud_xyz_camera = np.zeros((point_cloud_xyz_camera_hom.shape[0], 3))
        point_cloud_xyz_camera[:, 0] = point_cloud_xyz_camera_hom[:, 0] / point_cloud_xyz_camera_hom[:, 3]
        point_cloud_xyz_camera[:, 1] = point_cloud_xyz_camera_hom[:, 1] / point_cloud_xyz_camera_hom[:, 3]
        point_cloud_xyz_camera[:, 2] = point_cloud_xyz_camera_hom[:, 2] / point_cloud_xyz_camera_hom[:, 3]
        point_cloud_camera = point_cloud
        point_cloud_camera[:, 0:3] = point_cloud_xyz_camera
        u_min = example['u_min']
        u_max = example['u_max']
        v_min = example['v_min']
        v_max = example['v_max']
        input_2Dbbox = np.array([u_min, u_max, v_min, v_max])
        row_mask = np.logical_and(np.logical_and(img_points[:, 0] >= u_min, img_points[:, 0] <= u_max), np.logical_and(img_points[:, 1] >= v_min, img_points[:, 1] <= v_max))
        frustum_point_cloud_xyz = point_cloud_xyz[row_mask, :]
        frustum_point_cloud = point_cloud[row_mask, :]
        frustum_point_cloud_xyz_camera = point_cloud_xyz_camera[row_mask, :]
        frustum_point_cloud_camera = point_cloud_camera[row_mask, :]
        empty_frustum_flag = 0
        if frustum_point_cloud.shape[0] == 0:
            empty_frustum_flag = 1
            frustum_point_cloud = np.zeros((1024, 4), dtype=np.float32)
            frustum_point_cloud_xyz = np.zeros((1024, 3), dtype=np.float32)
            frustum_point_cloud_camera = np.zeros((1024, 4), dtype=np.float32)
            frustum_point_cloud_xyz_camera = np.zeros((1024, 3), dtype=np.float32)
        if frustum_point_cloud.shape[0] < 1024:
            row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=True)
        else:
            row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=False)
        frustum_point_cloud_xyz = frustum_point_cloud_xyz[row_idx, :]
        frustum_point_cloud = frustum_point_cloud[row_idx, :]
        frustum_point_cloud_xyz_camera = frustum_point_cloud_xyz_camera[row_idx, :]
        frustum_point_cloud_camera = frustum_point_cloud_camera[row_idx, :]
        u_center = u_min + (u_max - u_min) / 2.0
        v_center = v_min + (v_max - v_min) / 2.0
        center_img_point_hom = np.array([u_center, v_center, 1])
        P2_pseudo_inverse = np.linalg.pinv(P2)
        point_hom = np.dot(P2_pseudo_inverse, center_img_point_hom)
        point = np.array([point_hom[0] / point_hom[3], point_hom[1] / point_hom[3], point_hom[2] / point_hom[3]])
        if point[2] < 0:
            point[0] = -point[0]
            point[2] = -point[2]
        frustum_angle = np.arctan2(point[0], point[2])
        frustum_R = np.asarray([[np.cos(frustum_angle), 0, -np.sin(frustum_angle)], [0, 1, 0], [np.sin(frustum_angle), 0, np.cos(frustum_angle)]], dtype='float32')
        centered_frustum_point_cloud_xyz_camera = np.dot(frustum_R, frustum_point_cloud_xyz_camera.T).T
        centered_frustum_point_cloud_xyz_camera -= self.centered_frustum_mean_xyz
        centered_frustum_point_cloud_camera = frustum_point_cloud_camera
        centered_frustum_point_cloud_camera[:, 0:3] = centered_frustum_point_cloud_xyz_camera
        centered_frustum_point_cloud_camera = torch.from_numpy(centered_frustum_point_cloud_camera)
        return (centered_frustum_point_cloud_camera, img_id, input_2Dbbox, frustum_R, frustum_angle, empty_frustum_flag, self.centered_frustum_mean_xyz, self.mean_car_size)

    def __len__(self):
        return self.num_examples

def __getitem__(self, index):
    example = self.examples[index]
    img_id = example['img_id']
    lidar_path = self.lidar_dir + img_id + '.bin'
    point_cloud = np.fromfile(lidar_path, dtype=np.float32).reshape(-1, 4)
    orig_point_cloud = point_cloud
    point_cloud = point_cloud[point_cloud[:, 0] > -5, :]
    point_cloud = point_cloud[point_cloud[:, 0] < 80, :]
    calib = calibread(self.calib_path)
    P2 = calib['P2']
    Tr_velo_to_cam_orig = calib['Tr_velo_to_cam']
    R0_rect_orig = calib['R0_rect']
    R0_rect = np.eye(4)
    R0_rect[0:3, 0:3] = R0_rect_orig
    Tr_velo_to_cam = np.eye(4)
    Tr_velo_to_cam[0:3, :] = Tr_velo_to_cam_orig
    point_cloud_xyz = point_cloud[:, 0:3]
    point_cloud_xyz_hom = np.ones((point_cloud.shape[0], 4))
    point_cloud_xyz_hom[:, 0:3] = point_cloud[:, 0:3]
    img_points_hom = np.dot(P2, np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T))).T
    img_points = np.zeros((img_points_hom.shape[0], 2))
    img_points[:, 0] = img_points_hom[:, 0] / img_points_hom[:, 2]
    img_points[:, 1] = img_points_hom[:, 1] / img_points_hom[:, 2]
    point_cloud_xyz_camera_hom = np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T)).T
    point_cloud_xyz_camera = np.zeros((point_cloud_xyz_camera_hom.shape[0], 3))
    point_cloud_xyz_camera[:, 0] = point_cloud_xyz_camera_hom[:, 0] / point_cloud_xyz_camera_hom[:, 3]
    point_cloud_xyz_camera[:, 1] = point_cloud_xyz_camera_hom[:, 1] / point_cloud_xyz_camera_hom[:, 3]
    point_cloud_xyz_camera[:, 2] = point_cloud_xyz_camera_hom[:, 2] / point_cloud_xyz_camera_hom[:, 3]
    point_cloud_camera = point_cloud
    point_cloud_camera[:, 0:3] = point_cloud_xyz_camera
    u_min = example['u_min']
    u_max = example['u_max']
    v_min = example['v_min']
    v_max = example['v_max']
    input_2Dbbox = np.array([u_min, u_max, v_min, v_max])
    row_mask = np.logical_and(np.logical_and(img_points[:, 0] >= u_min, img_points[:, 0] <= u_max), np.logical_and(img_points[:, 1] >= v_min, img_points[:, 1] <= v_max))
    frustum_point_cloud_xyz = point_cloud_xyz[row_mask, :]
    frustum_point_cloud = point_cloud[row_mask, :]
    frustum_point_cloud_xyz_camera = point_cloud_xyz_camera[row_mask, :]
    frustum_point_cloud_camera = point_cloud_camera[row_mask, :]
    empty_frustum_flag = 0
    if frustum_point_cloud.shape[0] == 0:
        empty_frustum_flag = 1
        frustum_point_cloud = np.zeros((1024, 4), dtype=np.float32)
        frustum_point_cloud_xyz = np.zeros((1024, 3), dtype=np.float32)
        frustum_point_cloud_camera = np.zeros((1024, 4), dtype=np.float32)
        frustum_point_cloud_xyz_camera = np.zeros((1024, 3), dtype=np.float32)
    if frustum_point_cloud.shape[0] < 1024:
        row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=True)
    else:
        row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=False)
    frustum_point_cloud_xyz = frustum_point_cloud_xyz[row_idx, :]
    frustum_point_cloud = frustum_point_cloud[row_idx, :]
    frustum_point_cloud_xyz_camera = frustum_point_cloud_xyz_camera[row_idx, :]
    frustum_point_cloud_camera = frustum_point_cloud_camera[row_idx, :]
    u_center = u_min + (u_max - u_min) / 2.0
    v_center = v_min + (v_max - v_min) / 2.0
    center_img_point_hom = np.array([u_center, v_center, 1])
    P2_pseudo_inverse = np.linalg.pinv(P2)
    point_hom = np.dot(P2_pseudo_inverse, center_img_point_hom)
    point = np.array([point_hom[0] / point_hom[3], point_hom[1] / point_hom[3], point_hom[2] / point_hom[3]])
    if point[2] < 0:
        point[0] = -point[0]
        point[2] = -point[2]
    frustum_angle = np.arctan2(point[0], point[2])
    frustum_R = np.asarray([[np.cos(frustum_angle), 0, -np.sin(frustum_angle)], [0, 1, 0], [np.sin(frustum_angle), 0, np.cos(frustum_angle)]], dtype='float32')
    centered_frustum_point_cloud_xyz_camera = np.dot(frustum_R, frustum_point_cloud_xyz_camera.T).T
    centered_frustum_point_cloud_xyz_camera -= self.centered_frustum_mean_xyz
    centered_frustum_point_cloud_camera = frustum_point_cloud_camera
    centered_frustum_point_cloud_camera[:, 0:3] = centered_frustum_point_cloud_xyz_camera
    centered_frustum_point_cloud_camera = torch.from_numpy(centered_frustum_point_cloud_camera)
    return (centered_frustum_point_cloud_camera, img_id, input_2Dbbox, frustum_R, frustum_angle, empty_frustum_flag, self.centered_frustum_mean_xyz, self.mean_car_size)

class DatasetKittiVal2ddetections(torch.utils.data.Dataset):

    def __init__(self, kitti_data_path, kitti_meta_path, NH):
        self.img_dir = kitti_data_path + '/object/training/image_2/'
        self.calib_dir = kitti_data_path + '/object/training/calib/'
        self.lidar_dir = kitti_data_path + '/object/training/velodyne/'
        self.detections_2d_path = kitti_meta_path + '/rgb_detection_val.txt'
        self.NH = NH
        with open(kitti_meta_path + '/kitti_train_mean_car_size.pkl', 'rb') as file:
            self.mean_car_size = pickle.load(file)
        with open(kitti_meta_path + '/kitti_centered_frustum_mean_xyz.pkl', 'rb') as file:
            self.centered_frustum_mean_xyz = pickle.load(file)
            self.centered_frustum_mean_xyz = self.centered_frustum_mean_xyz.astype(np.float32)
        self.examples = []
        with open(self.detections_2d_path) as file:
            for line in file:
                values = line.split()
                object_class = float(values[1])
                if object_class == 2:
                    score_2d = float(values[2])
                    u_min = float(values[3])
                    v_min = float(values[4])
                    u_max = float(values[5])
                    v_max = float(values[6])
                    img_id = values[0].split('image_2/')[1]
                    img_id = img_id.split('.')[0]
                    detection_2d = {}
                    detection_2d['u_min'] = u_min
                    detection_2d['v_min'] = v_min
                    detection_2d['u_max'] = u_max
                    detection_2d['v_max'] = v_max
                    detection_2d['score_2d'] = score_2d
                    detection_2d['img_id'] = img_id
                    self.examples.append(detection_2d)
        self.num_examples = len(self.examples)

    def __getitem__(self, index):
        example = self.examples[index]
        img_id = example['img_id']
        lidar_path = self.lidar_dir + img_id + '.bin'
        point_cloud = np.fromfile(lidar_path, dtype=np.float32).reshape(-1, 4)
        orig_point_cloud = point_cloud
        point_cloud = point_cloud[point_cloud[:, 0] > -5, :]
        point_cloud = point_cloud[point_cloud[:, 0] < 80, :]
        calib = calibread(self.calib_dir + img_id + '.txt')
        P2 = calib['P2']
        Tr_velo_to_cam_orig = calib['Tr_velo_to_cam']
        R0_rect_orig = calib['R0_rect']
        R0_rect = np.eye(4)
        R0_rect[0:3, 0:3] = R0_rect_orig
        Tr_velo_to_cam = np.eye(4)
        Tr_velo_to_cam[0:3, :] = Tr_velo_to_cam_orig
        point_cloud_xyz = point_cloud[:, 0:3]
        point_cloud_xyz_hom = np.ones((point_cloud.shape[0], 4))
        point_cloud_xyz_hom[:, 0:3] = point_cloud[:, 0:3]
        img_points_hom = np.dot(P2, np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T))).T
        img_points = np.zeros((img_points_hom.shape[0], 2))
        img_points[:, 0] = img_points_hom[:, 0] / img_points_hom[:, 2]
        img_points[:, 1] = img_points_hom[:, 1] / img_points_hom[:, 2]
        point_cloud_xyz_camera_hom = np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T)).T
        point_cloud_xyz_camera = np.zeros((point_cloud_xyz_camera_hom.shape[0], 3))
        point_cloud_xyz_camera[:, 0] = point_cloud_xyz_camera_hom[:, 0] / point_cloud_xyz_camera_hom[:, 3]
        point_cloud_xyz_camera[:, 1] = point_cloud_xyz_camera_hom[:, 1] / point_cloud_xyz_camera_hom[:, 3]
        point_cloud_xyz_camera[:, 2] = point_cloud_xyz_camera_hom[:, 2] / point_cloud_xyz_camera_hom[:, 3]
        point_cloud_camera = point_cloud
        point_cloud_camera[:, 0:3] = point_cloud_xyz_camera
        u_min = example['u_min']
        u_max = example['u_max']
        v_min = example['v_min']
        v_max = example['v_max']
        score_2d = example['score_2d']
        input_2Dbbox = np.array([u_min, u_max, v_min, v_max])
        row_mask = np.logical_and(np.logical_and(img_points[:, 0] >= u_min, img_points[:, 0] <= u_max), np.logical_and(img_points[:, 1] >= v_min, img_points[:, 1] <= v_max))
        frustum_point_cloud_xyz = point_cloud_xyz[row_mask, :]
        frustum_point_cloud = point_cloud[row_mask, :]
        frustum_point_cloud_xyz_camera = point_cloud_xyz_camera[row_mask, :]
        frustum_point_cloud_camera = point_cloud_camera[row_mask, :]
        empty_frustum_flag = 0
        if frustum_point_cloud.shape[0] == 0:
            empty_frustum_flag = 1
            frustum_point_cloud = np.zeros((1024, 4), dtype=np.float32)
            frustum_point_cloud_xyz = np.zeros((1024, 3), dtype=np.float32)
            frustum_point_cloud_camera = np.zeros((1024, 4), dtype=np.float32)
            frustum_point_cloud_xyz_camera = np.zeros((1024, 3), dtype=np.float32)
        if frustum_point_cloud.shape[0] < 1024:
            row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=True)
        else:
            row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=False)
        frustum_point_cloud_xyz = frustum_point_cloud_xyz[row_idx, :]
        frustum_point_cloud = frustum_point_cloud[row_idx, :]
        frustum_point_cloud_xyz_camera = frustum_point_cloud_xyz_camera[row_idx, :]
        frustum_point_cloud_camera = frustum_point_cloud_camera[row_idx, :]
        u_center = u_min + (u_max - u_min) / 2.0
        v_center = v_min + (v_max - v_min) / 2.0
        center_img_point_hom = np.array([u_center, v_center, 1])
        P2_pseudo_inverse = np.linalg.pinv(P2)
        point_hom = np.dot(P2_pseudo_inverse, center_img_point_hom)
        point = np.array([point_hom[0] / point_hom[3], point_hom[1] / point_hom[3], point_hom[2] / point_hom[3]])
        if point[2] < 0:
            point[0] = -point[0]
            point[2] = -point[2]
        frustum_angle = np.arctan2(point[0], point[2])
        frustum_R = np.asarray([[np.cos(frustum_angle), 0, -np.sin(frustum_angle)], [0, 1, 0], [np.sin(frustum_angle), 0, np.cos(frustum_angle)]], dtype='float32')
        centered_frustum_point_cloud_xyz_camera = np.dot(frustum_R, frustum_point_cloud_xyz_camera.T).T
        centered_frustum_point_cloud_xyz_camera -= self.centered_frustum_mean_xyz
        centered_frustum_point_cloud_camera = frustum_point_cloud_camera
        centered_frustum_point_cloud_camera[:, 0:3] = centered_frustum_point_cloud_xyz_camera
        centered_frustum_point_cloud_camera = torch.from_numpy(centered_frustum_point_cloud_camera)
        return (centered_frustum_point_cloud_camera, img_id, input_2Dbbox, frustum_R, frustum_angle, empty_frustum_flag, self.centered_frustum_mean_xyz, self.mean_car_size, score_2d)

    def __len__(self):
        return self.num_examples

def __getitem__(self, index):
    example = self.examples[index]
    img_id = example['img_id']
    lidar_path = self.lidar_dir + img_id + '.bin'
    point_cloud = np.fromfile(lidar_path, dtype=np.float32).reshape(-1, 4)
    orig_point_cloud = point_cloud
    point_cloud = point_cloud[point_cloud[:, 0] > -5, :]
    point_cloud = point_cloud[point_cloud[:, 0] < 80, :]
    calib = calibread(self.calib_dir + img_id + '.txt')
    P2 = calib['P2']
    Tr_velo_to_cam_orig = calib['Tr_velo_to_cam']
    R0_rect_orig = calib['R0_rect']
    R0_rect = np.eye(4)
    R0_rect[0:3, 0:3] = R0_rect_orig
    Tr_velo_to_cam = np.eye(4)
    Tr_velo_to_cam[0:3, :] = Tr_velo_to_cam_orig
    point_cloud_xyz = point_cloud[:, 0:3]
    point_cloud_xyz_hom = np.ones((point_cloud.shape[0], 4))
    point_cloud_xyz_hom[:, 0:3] = point_cloud[:, 0:3]
    img_points_hom = np.dot(P2, np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T))).T
    img_points = np.zeros((img_points_hom.shape[0], 2))
    img_points[:, 0] = img_points_hom[:, 0] / img_points_hom[:, 2]
    img_points[:, 1] = img_points_hom[:, 1] / img_points_hom[:, 2]
    point_cloud_xyz_camera_hom = np.dot(R0_rect, np.dot(Tr_velo_to_cam, point_cloud_xyz_hom.T)).T
    point_cloud_xyz_camera = np.zeros((point_cloud_xyz_camera_hom.shape[0], 3))
    point_cloud_xyz_camera[:, 0] = point_cloud_xyz_camera_hom[:, 0] / point_cloud_xyz_camera_hom[:, 3]
    point_cloud_xyz_camera[:, 1] = point_cloud_xyz_camera_hom[:, 1] / point_cloud_xyz_camera_hom[:, 3]
    point_cloud_xyz_camera[:, 2] = point_cloud_xyz_camera_hom[:, 2] / point_cloud_xyz_camera_hom[:, 3]
    point_cloud_camera = point_cloud
    point_cloud_camera[:, 0:3] = point_cloud_xyz_camera
    u_min = example['u_min']
    u_max = example['u_max']
    v_min = example['v_min']
    v_max = example['v_max']
    score_2d = example['score_2d']
    input_2Dbbox = np.array([u_min, u_max, v_min, v_max])
    row_mask = np.logical_and(np.logical_and(img_points[:, 0] >= u_min, img_points[:, 0] <= u_max), np.logical_and(img_points[:, 1] >= v_min, img_points[:, 1] <= v_max))
    frustum_point_cloud_xyz = point_cloud_xyz[row_mask, :]
    frustum_point_cloud = point_cloud[row_mask, :]
    frustum_point_cloud_xyz_camera = point_cloud_xyz_camera[row_mask, :]
    frustum_point_cloud_camera = point_cloud_camera[row_mask, :]
    empty_frustum_flag = 0
    if frustum_point_cloud.shape[0] == 0:
        empty_frustum_flag = 1
        frustum_point_cloud = np.zeros((1024, 4), dtype=np.float32)
        frustum_point_cloud_xyz = np.zeros((1024, 3), dtype=np.float32)
        frustum_point_cloud_camera = np.zeros((1024, 4), dtype=np.float32)
        frustum_point_cloud_xyz_camera = np.zeros((1024, 3), dtype=np.float32)
    if frustum_point_cloud.shape[0] < 1024:
        row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=True)
    else:
        row_idx = np.random.choice(frustum_point_cloud.shape[0], 1024, replace=False)
    frustum_point_cloud_xyz = frustum_point_cloud_xyz[row_idx, :]
    frustum_point_cloud = frustum_point_cloud[row_idx, :]
    frustum_point_cloud_xyz_camera = frustum_point_cloud_xyz_camera[row_idx, :]
    frustum_point_cloud_camera = frustum_point_cloud_camera[row_idx, :]
    u_center = u_min + (u_max - u_min) / 2.0
    v_center = v_min + (v_max - v_min) / 2.0
    center_img_point_hom = np.array([u_center, v_center, 1])
    P2_pseudo_inverse = np.linalg.pinv(P2)
    point_hom = np.dot(P2_pseudo_inverse, center_img_point_hom)
    point = np.array([point_hom[0] / point_hom[3], point_hom[1] / point_hom[3], point_hom[2] / point_hom[3]])
    if point[2] < 0:
        point[0] = -point[0]
        point[2] = -point[2]
    frustum_angle = np.arctan2(point[0], point[2])
    frustum_R = np.asarray([[np.cos(frustum_angle), 0, -np.sin(frustum_angle)], [0, 1, 0], [np.sin(frustum_angle), 0, np.cos(frustum_angle)]], dtype='float32')
    centered_frustum_point_cloud_xyz_camera = np.dot(frustum_R, frustum_point_cloud_xyz_camera.T).T
    centered_frustum_point_cloud_xyz_camera -= self.centered_frustum_mean_xyz
    centered_frustum_point_cloud_camera = frustum_point_cloud_camera
    centered_frustum_point_cloud_camera[:, 0:3] = centered_frustum_point_cloud_xyz_camera
    centered_frustum_point_cloud_camera = torch.from_numpy(centered_frustum_point_cloud_camera)
    return (centered_frustum_point_cloud_camera, img_id, input_2Dbbox, frustum_R, frustum_angle, empty_frustum_flag, self.centered_frustum_mean_xyz, self.mean_car_size, score_2d)

def get_keypoints(center, h, w, l, r_y, P2_mat):
    Rmat = np.asarray([[math.cos(r_y), 0, math.sin(r_y)], [0, 1, 0], [-math.sin(r_y), 0, math.cos(r_y)]], dtype='float32')
    p0 = center + np.dot(Rmat, np.asarray([l / 2.0, 0, w / 2.0], dtype='float32').flatten())
    p1 = center + np.dot(Rmat, np.asarray([-l / 2.0, 0, w / 2.0], dtype='float32').flatten())
    p2 = center + np.dot(Rmat, np.asarray([-l / 2.0, 0, -w / 2.0], dtype='float32').flatten())
    p3 = center + np.dot(Rmat, np.asarray([l / 2.0, 0, -w / 2.0], dtype='float32').flatten())
    p4 = center + np.dot(Rmat, np.asarray([l / 2.0, -h, w / 2.0], dtype='float32').flatten())
    p5 = center + np.dot(Rmat, np.asarray([-l / 2.0, -h, w / 2.0], dtype='float32').flatten())
    p6 = center + np.dot(Rmat, np.asarray([-l / 2.0, -h, -w / 2.0], dtype='float32').flatten())
    p7 = center + np.dot(Rmat, np.asarray([l / 2.0, -h, -w / 2.0], dtype='float32').flatten())
    keypoints_3d = np.array([p0, p1, p2, p3, p4, p5, p6, p7])
    keypoints_3d_hom = np.ones((8, 4), dtype=np.float32)
    keypoints_3d_hom[:, 0:3] = keypoints_3d
    keypoints_hom = np.dot(P2_mat, keypoints_3d_hom.T).T
    keypoints = np.zeros((8, 2), dtype=np.float32)
    keypoints[:, 0] = keypoints_hom[:, 0] / keypoints_hom[:, 2]
    keypoints[:, 1] = keypoints_hom[:, 1] / keypoints_hom[:, 2]
    return keypoints

