# Cluster 8

def rotate(point, angle):
    """Rotates a point around the origin by the specified angle in radians."""
    rotation_matrix = np.array([[np.cos(angle), -np.sin(angle), 0], [np.sin(angle), np.cos(angle), 0], [0, 0, 1]])
    return np.dot(rotation_matrix, point)

def generate_vertices(car):
    """Generates the vertices of a 3D box."""
    x = car['cx']
    y = car['cy']
    z = car['cz']
    length = car['length']
    width = car['width']
    height = car['height']
    heading = car['heading']
    box_center = np.array([x, y, z])
    half_dims = np.array([length / 2, width / 2, height / 2])
    relative_positions = np.array([[-1, -1, -1], [-1, -1, 1], [-1, 1, -1], [-1, 1, 1], [1, -1, -1], [1, -1, 1], [1, 1, -1], [1, 1, 1]]) * half_dims
    vertices = np.asarray([rotate(pos, heading) + box_center for pos in relative_positions])
    return vertices

def vis_map_debug(map, motion):
    from matplotlib import pyplot as plt
    cropped_road_edges = map['boundary']
    cropped_lanes = map['centerline']
    for edge in cropped_road_edges:
        edge = np.array(edge)
        plt.plot(edge[:, 0], edge[:, 1], c='red')
    for lane in cropped_lanes:
        lane = np.array(lane)
        plt.plot(lane[:, 0], lane[:, 1], c='green')
    if motion is not None:
        plt.plot(motion[:, 0], motion[:, 1], c='blue')
    plt.savefig('/home/ubuntu/yuxiwei/debug/running_map.png')

class Colamp_Dataset:

    def __init__(self, data_dir):
        scene_manager = NeRFSceneManager(data_dir)
        self.names, self.poses, self.pix2cam, self.params, self.camtype = scene_manager.process()
        self.cam2pix = np.linalg.inv(self.pix2cam)
        self.n_images = len(self.poses)
        sorted_image_names = sorted(deepcopy(self.names))
        sort_img_idx = []
        for i in range(self.n_images):
            sort_img_idx.append(self.names.index(sorted_image_names[i]))
        img_idx = np.array(sort_img_idx, dtype=np.int32)
        self.poses = self.poses[sort_img_idx]

        def proc(x):
            return np.ascontiguousarray(np.array(x).astype(np.float64))
        self.poses = proc(self.poses)
        self.cam2pix = proc(np.tile(self.cam2pix[None], (len(self.poses), 1, 1)))
        if self.params is not None:
            dist_params = [self.params['k1'], self.params['k2'], self.params['p1'], self.params['p2']]
        else:
            dist_params = [0.0, 0.0, 0.0, 0.0]
        dist_params = np.tile(np.array(dist_params), len(self.poses)).reshape([len(self.poses), -1])
        self.dist_params = proc([dist_params])

    def export(self, data_dir):
        n = len(self.poses)
        poses_RUB = deepcopy(self.poses)
        image_list = []
        suffs = ['*.png', '*.PNG', '*.jpg', '*.JPG']
        for suff in suffs:
            image_list += glob(pjoin(data_dir, 'images', suff))
        intrinsic = self.cam2pix
        dist_params = self.dist_params.reshape(-1, 4)
        bounds = np.array([0.1, 999]).reshape(1, 2).repeat(n, axis=0)
        cams_meta = np.concatenate([poses_RUB.reshape(n, -1), intrinsic.reshape(n, -1), dist_params.reshape(n, -1), bounds.reshape(n, -1)], axis=1)
        cams_meta = np.ascontiguousarray(cams_meta)
        np.save(os.path.join(data_dir, 'cams_meta_colmap.npy'), cams_meta)

def __init__(self, data_dir):
    scene_manager = NeRFSceneManager(data_dir)
    self.names, self.poses, self.pix2cam, self.params, self.camtype = scene_manager.process()
    self.cam2pix = np.linalg.inv(self.pix2cam)
    self.n_images = len(self.poses)
    sorted_image_names = sorted(deepcopy(self.names))
    sort_img_idx = []
    for i in range(self.n_images):
        sort_img_idx.append(self.names.index(sorted_image_names[i]))
    img_idx = np.array(sort_img_idx, dtype=np.int32)
    self.poses = self.poses[sort_img_idx]

    def proc(x):
        return np.ascontiguousarray(np.array(x).astype(np.float64))
    self.poses = proc(self.poses)
    self.cam2pix = proc(np.tile(self.cam2pix[None], (len(self.poses), 1, 1)))
    if self.params is not None:
        dist_params = [self.params['k1'], self.params['k2'], self.params['p1'], self.params['p2']]
    else:
        dist_params = [0.0, 0.0, 0.0, 0.0]
    dist_params = np.tile(np.array(dist_params), len(self.poses)).reshape([len(self.poses), -1])
    self.dist_params = proc([dist_params])

def proc(x):
    return np.ascontiguousarray(np.array(x).astype(np.float64))

class COLMAPDatabase(sqlite3.Connection):

    @staticmethod
    def connect(database_path):
        return sqlite3.connect(database_path, factory=COLMAPDatabase)

    def __init__(self, *args, **kwargs):
        super(COLMAPDatabase, self).__init__(*args, **kwargs)
        self.create_tables = lambda: self.executescript(CREATE_ALL)
        self.create_cameras_table = lambda: self.executescript(CREATE_CAMERAS_TABLE)
        self.create_descriptors_table = lambda: self.executescript(CREATE_DESCRIPTORS_TABLE)
        self.create_images_table = lambda: self.executescript(CREATE_IMAGES_TABLE)
        self.create_two_view_geometries_table = lambda: self.executescript(CREATE_TWO_VIEW_GEOMETRIES_TABLE)
        self.create_keypoints_table = lambda: self.executescript(CREATE_KEYPOINTS_TABLE)
        self.create_matches_table = lambda: self.executescript(CREATE_MATCHES_TABLE)
        self.create_name_index = lambda: self.executescript(CREATE_NAME_INDEX)

    def update_camera(self, model, width, height, params, camera_id):
        params = np.asarray(params, np.float64)
        cursor = self.execute('UPDATE cameras SET model=?, width=?, height=?, params=?, prior_focal_length=True WHERE camera_id=?', (model, width, height, array_to_blob(params), camera_id))
        return cursor.lastrowid

    def update_image(self, IMAGE_ID, QW, QX, QY, QZ, TX, TY, TZ, CAMERA_ID):
        cursor = self.execute('UPDATE images SET prior_qw=?,  prior_qx=?, prior_qy=?, prior_qz=?, prior_tx=?, prior_ty=?, prior_tz=? ,camera_id=? WHERE image_id=?', (QW, QX, QY, QZ, TX, TY, TZ, CAMERA_ID, IMAGE_ID))
        return cursor.lastrowid

@staticmethod
def connect(database_path):
    return sqlite3.connect(database_path, factory=COLMAPDatabase)

def update_camera(self, model, width, height, params, camera_id):
    params = np.asarray(params, np.float64)
    cursor = self.execute('UPDATE cameras SET model=?, width=?, height=?, params=?, prior_focal_length=True WHERE camera_id=?', (model, width, height, array_to_blob(params), camera_id))
    return cursor.lastrowid

def update_image(self, IMAGE_ID, QW, QX, QY, QZ, TX, TY, TZ, CAMERA_ID):
    cursor = self.execute('UPDATE images SET prior_qw=?,  prior_qx=?, prior_qy=?, prior_qz=?, prior_tx=?, prior_ty=?, prior_tz=? ,camera_id=? WHERE image_id=?', (QW, QX, QY, QZ, TX, TY, TZ, CAMERA_ID, IMAGE_ID))
    return cursor.lastrowid

def camTodatabase(txtfile, dbfile):
    camModelDict = {'SIMPLE_PINHOLE': 0, 'PINHOLE': 1, 'SIMPLE_RADIAL': 2, 'RADIAL': 3, 'OPENCV': 4, 'FULL_OPENCV': 5, 'SIMPLE_RADIAL_FISHEYE': 6, 'RADIAL_FISHEYE': 7, 'OPENCV_FISHEYE': 8, 'FOV': 9, 'THIN_PRISM_FISHEYE': 10}
    db = COLMAPDatabase.connect(dbfile)
    idList = list()
    modelList = list()
    widthList = list()
    heightList = list()
    paramsList = list()
    with open(txtfile, 'r') as cam:
        lines = cam.readlines()
        for i in range(0, len(lines), 1):
            if lines[i][0] != '#':
                strLists = lines[i].split()
                cameraId = int(strLists[0])
                cameraModel = camModelDict[strLists[1]]
                width = int(strLists[2])
                height = int(strLists[3])
                paramstr = np.array(strLists[4:12])
                params = paramstr.astype(np.float64)
                idList.append(cameraId)
                modelList.append(cameraModel)
                widthList.append(width)
                heightList.append(height)
                paramsList.append(params)
                camera_id = db.update_camera(cameraModel, width, height, params, cameraId)
    db.commit()
    rows = db.execute('SELECT * FROM cameras')
    for i in range(0, len(idList), 1):
        camera_id, model, width, height, params, prior = next(rows)
        params = blob_to_array(params, np.float64)
        assert camera_id == idList[i]
        assert model == modelList[i] and width == widthList[i] and (height == heightList[i])
        assert np.allclose(params, paramsList[i])
    db.close()

def imgTodatabase(txtfile, dbfile):
    db = COLMAPDatabase.connect(dbfile)
    with open(txtfile, 'r') as images:
        lines = images.readlines()
        for i in range(0, len(lines)):
            image_metas = lines[i].split()
            if len(image_metas) > 0:
                db.update_image(IMAGE_ID=int(image_metas[0]), QW=float(image_metas[1]), QX=float(image_metas[2]), QY=float(image_metas[3]), QZ=float(image_metas[4]), TX=float(image_metas[5]), TY=float(image_metas[6]), TZ=float(image_metas[7]), CAMERA_ID=int(image_metas[8]))
    db.commit()
    db.close()

def intrinsic_matrix(fx: float, fy: float, cx: float, cy: float):
    """Intrinsic matrix for a pinhole camera in OpenCV coordinate system."""
    return np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1.0]], dtype=np.float32)

class Camera:

    @staticmethod
    def GetNumParams(type_):
        if type_ == 0 or type_ == 'SIMPLE_PINHOLE':
            return 3
        if type_ == 1 or type_ == 'PINHOLE':
            return 4
        if type_ == 2 or type_ == 'SIMPLE_RADIAL':
            return 4
        if type_ == 3 or type_ == 'RADIAL':
            return 5
        if type_ == 4 or type_ == 'OPENCV':
            return 8
        raise Exception('Camera type not supported')

    @staticmethod
    def GetNameFromType(type_):
        if type_ == 0:
            return 'SIMPLE_PINHOLE'
        if type_ == 1:
            return 'PINHOLE'
        if type_ == 2:
            return 'SIMPLE_RADIAL'
        if type_ == 3:
            return 'RADIAL'
        if type_ == 4:
            return 'OPENCV'
        raise Exception('Camera type not supported')

    def __init__(self, type_, width_, height_, params):
        self.width = width_
        self.height = height_
        if type_ == 0 or type_ == 'SIMPLE_PINHOLE':
            self.fx, self.cx, self.cy = params
            self.fy = self.fx
            self.distortion_func = None
            self.camera_type = 0
        elif type_ == 1 or type_ == 'PINHOLE':
            self.fx, self.fy, self.cx, self.cy = params
            self.distortion_func = None
            self.camera_type = 1
        elif type_ == 2 or type_ == 'SIMPLE_RADIAL':
            self.fx, self.cx, self.cy, self.k1 = params
            self.fy = self.fx
            self.distortion_func = simple_radial_distortion
            self.camera_type = 2
        elif type_ == 3 or type_ == 'RADIAL':
            self.fx, self.cx, self.cy, self.k1, self.k2 = params
            self.fy = self.fx
            self.distortion_func = radial_distortion
            self.camera_type = 3
        elif type_ == 4 or type_ == 'OPENCV':
            self.fx, self.fy, self.cx, self.cy = params[:4]
            self.k1, self.k2, self.p1, self.p2 = params[4:]
            self.distortion_func = opencv_distortion
            self.camera_type = 4
        else:
            raise Exception('Camera type not supported')

    def __str__(self):
        s = self.GetNameFromType(self.camera_type) + ' {} {} {}'.format(self.width, self.height, self.fx)
        if self.camera_type in (1, 4):
            s += ' {}'.format(self.fy)
        s += ' {} {}'.format(self.cx, self.cy)
        if self.camera_type == 2:
            s += ' {}'.format(self.k1)
        elif self.camera_type == 3:
            s += ' {} {}'.format(self.k1, self.k2)
        elif self.camera_type == 4:
            s += ' {} {} {} {}'.format(self.k1, self.k2, self.p1, self.p2)
        return s

    def get_params(self):
        if self.camera_type == 0:
            return np.array((self.fx, self.cx, self.cy))
        if self.camera_type == 1:
            return np.array((self.fx, self.fy, self.cx, self.cy))
        if self.camera_type == 2:
            return np.array((self.fx, self.cx, self.cy, self.k1))
        if self.camera_type == 3:
            return np.array((self.fx, self.cx, self.cy, self.k1, self.k2))
        if self.camera_type == 4:
            return np.array((self.fx, self.fy, self.cx, self.cy, self.k1, self.k2, self.p1, self.p2))

    def get_camera_matrix(self):
        return np.array(((self.fx, 0, self.cx), (0, self.fy, self.cy), (0, 0, 1)))

    def get_inverse_camera_matrix(self):
        return np.array(((1.0 / self.fx, 0, -self.cx / self.fx), (0, 1.0 / self.fy, -self.cy / self.fy), (0, 0, 1)))

    @property
    def K(self):
        return self.get_camera_matrix()

    @property
    def K_inv(self):
        return self.get_inverse_camera_matrix()

    def get_inv_camera_matrix(self):
        inv_fx, inv_fy = (1.0 / self.fx, 1.0 / self.fy)
        return np.array(((inv_fx, 0, -inv_fx * self.cx), (0, inv_fy, -inv_fy * self.cy), (0, 0, 1)))

    def get_image_grid(self):
        xmin = (0.5 - self.cx) / self.fx
        xmax = (self.width - 0.5 - self.cx) / self.fx
        ymin = (0.5 - self.cy) / self.fy
        ymax = (self.height - 0.5 - self.cy) / self.fy
        return np.meshgrid(np.linspace(xmin, xmax, self.width), np.linspace(ymin, ymax, self.height))

    def distort_points(self, x, normalized=True, denormalize=True):
        x = np.atleast_2d(x)
        if not normalized:
            x -= np.array([[self.cx, self.cy]])
            x /= np.array([[self.fx, self.fy]])
        if self.distortion_func is not None:
            x = self.distortion_func(self, x)
        if denormalize:
            x *= np.array([[self.fx, self.fy]])
            x += np.array([[self.cx, self.cy]])
        return x

    def undistort_points(self, x, normalized=False, denormalize=True):
        x = np.atleast_2d(x)
        if not normalized:
            x = x - np.array([self.cx, self.cy])
            x /= np.array([self.fx, self.fy])
        if self.distortion_func is not None:

            def objective(xu):
                return (x - self.distortion_func(self, xu.reshape(*x.shape))).ravel()
            xu = root(objective, x).x.reshape(*x.shape)
        else:
            xu = x
        if denormalize:
            xu *= np.array([[self.fx, self.fy]])
            xu += np.array([[self.cx, self.cy]])
        return xu

def get_params(self):
    if self.camera_type == 0:
        return np.array((self.fx, self.cx, self.cy))
    if self.camera_type == 1:
        return np.array((self.fx, self.fy, self.cx, self.cy))
    if self.camera_type == 2:
        return np.array((self.fx, self.cx, self.cy, self.k1))
    if self.camera_type == 3:
        return np.array((self.fx, self.cx, self.cy, self.k1, self.k2))
    if self.camera_type == 4:
        return np.array((self.fx, self.fy, self.cx, self.cy, self.k1, self.k2, self.p1, self.p2))

def get_camera_matrix(self):
    return np.array(((self.fx, 0, self.cx), (0, self.fy, self.cy), (0, 0, 1)))

def get_inverse_camera_matrix(self):
    return np.array(((1.0 / self.fx, 0, -self.cx / self.fx), (0, 1.0 / self.fy, -self.cy / self.fy), (0, 0, 1)))

@property
def K(self):
    return self.get_camera_matrix()

def get_inv_camera_matrix(self):
    inv_fx, inv_fy = (1.0 / self.fx, 1.0 / self.fy)
    return np.array(((inv_fx, 0, -inv_fx * self.cx), (0, inv_fy, -inv_fy * self.cy), (0, 0, 1)))

def distort_points(self, x, normalized=True, denormalize=True):
    x = np.atleast_2d(x)
    if not normalized:
        x -= np.array([[self.cx, self.cy]])
        x /= np.array([[self.fx, self.fy]])
    if self.distortion_func is not None:
        x = self.distortion_func(self, x)
    if denormalize:
        x *= np.array([[self.fx, self.fy]])
        x += np.array([[self.cx, self.cy]])
    return x

def undistort_points(self, x, normalized=False, denormalize=True):
    x = np.atleast_2d(x)
    if not normalized:
        x = x - np.array([self.cx, self.cy])
        x /= np.array([self.fx, self.fy])
    if self.distortion_func is not None:

        def objective(xu):
            return (x - self.distortion_func(self, xu.reshape(*x.shape))).ravel()
        xu = root(objective, x).x.reshape(*x.shape)
    else:
        xu = x
    if denormalize:
        xu *= np.array([[self.fx, self.fy]])
        xu += np.array([[self.cx, self.cy]])
    return xu

def objective(xu):
    return (x - self.distortion_func(self, xu.reshape(*x.shape))).ravel()

def add_camera(db, model, width, height, params, prior_focal_length=False, camera_id=None):
    params = np.asarray(params, np.float64)
    db.execute('INSERT INTO cameras VALUES (?, ?, ?, ?, ?, ?)', (camera_id, model, width, height, array_to_blob(params), prior_focal_length))

def add_descriptors(db, image_id, descriptors):
    descriptors = np.ascontiguousarray(descriptors, np.uint8)
    db.execute('INSERT INTO descriptors VALUES (?, ?, ?, ?)', (image_id,) + descriptors.shape + (array_to_blob(descriptors),))

def add_image(db, name, camera_id, prior_q=np.zeros(4), prior_t=np.zeros(3), image_id=None):
    db.execute('INSERT INTO images VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (image_id, name, camera_id, prior_q[0], prior_q[1], prior_q[2], prior_q[3], prior_t[0], prior_t[1], prior_t[2]))

def add_inlier_matches(db, image_id1, image_id2, matches, config=2, F=None, E=None, H=None):
    assert len(matches.shape) == 2
    assert matches.shape[1] == 2
    if image_id1 > image_id2:
        matches = matches[:, ::-1]
    if F is not None:
        F = np.asarray(F, np.float64)
    if E is not None:
        E = np.asarray(E, np.float64)
    if H is not None:
        H = np.asarray(H, np.float64)
    pair_id = get_pair_id(image_id1, image_id2)
    matches = np.asarray(matches, np.uint32)
    db.execute('INSERT INTO inlier_matches VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (pair_id,) + matches.shape + (array_to_blob(matches), config, F, E, H))

def add_keypoints(db, image_id, keypoints):
    assert len(keypoints.shape) == 2
    assert keypoints.shape[1] in [2, 4, 6]
    keypoints = np.asarray(keypoints, np.float32)
    db.execute('INSERT INTO keypoints VALUES (?, ?, ?, ?)', (image_id,) + keypoints.shape + (array_to_blob(keypoints),))

def add_matches(db, image_id1, image_id2, matches):
    assert len(matches.shape) == 2
    assert matches.shape[1] == 2
    if image_id1 > image_id2:
        matches = matches[:, ::-1]
    pair_id = get_pair_id(image_id1, image_id2)
    matches = np.asarray(matches, np.uint32)
    db.execute('INSERT INTO matches VALUES (?, ?, ?, ?)', (pair_id,) + matches.shape + (array_to_blob(matches),))

class COLMAPDatabase(sqlite3.Connection):

    @staticmethod
    def connect(database_path):
        return sqlite3.connect(database_path, factory=COLMAPDatabase)

    def __init__(self, *args, **kwargs):
        super(COLMAPDatabase, self).__init__(*args, **kwargs)
        self.initialize_tables = lambda: self.executescript(CREATE_ALL)
        self.initialize_cameras = lambda: self.executescript(CREATE_CAMERAS_TABLE)
        self.initialize_descriptors = lambda: self.executescript(CREATE_DESCRIPTORS_TABLE)
        self.initialize_images = lambda: self.executescript(CREATE_IMAGES_TABLE)
        self.initialize_inlier_matches = lambda: self.executescript(CREATE_INLIER_MATCHES_TABLE)
        self.initialize_keypoints = lambda: self.executescript(CREATE_KEYPOINTS_TABLE)
        self.initialize_matches = lambda: self.executescript(CREATE_MATCHES_TABLE)
        self.create_name_index = lambda: self.executescript(CREATE_NAME_INDEX)
    add_camera = add_camera
    add_descriptors = add_descriptors
    add_image = add_image
    add_inlier_matches = add_inlier_matches
    add_keypoints = add_keypoints
    add_matches = add_matches

@staticmethod
def connect(database_path):
    return sqlite3.connect(database_path, factory=COLMAPDatabase)

def main(args):
    import os
    if os.path.exists(args.database_path):
        print('Error: database path already exists -- will not modify it.')
        exit()
    db = COLMAPDatabase.connect(args.database_path)
    db.initialize_tables()
    model1, w1, h1, params1 = (0, 1024, 768, np.array((1024.0, 512.0, 384.0)))
    model2, w2, h2, params2 = (2, 1024, 768, np.array((1024.0, 512.0, 384.0, 0.1)))
    db.add_camera(model1, w1, h1, params1)
    db.add_camera(model2, w2, h2, params2)
    db.add_image('image1.png', 0)
    db.add_image('image2.png', 0)
    db.add_image('image3.png', 2)
    db.add_image('image4.png', 2)
    N = 1000
    kp1 = np.random.rand(N, 2) * (1024.0, 768.0)
    kp2 = np.random.rand(N, 2) * (1024.0, 768.0)
    kp3 = np.random.rand(N, 2) * (1024.0, 768.0)
    kp4 = np.random.rand(N, 2) * (1024.0, 768.0)
    db.add_keypoints(1, kp1)
    db.add_keypoints(2, kp2)
    db.add_keypoints(3, kp3)
    db.add_keypoints(4, kp4)
    M = 50
    m12 = np.random.randint(N, size=(M, 2))
    m23 = np.random.randint(N, size=(M, 2))
    m34 = np.random.randint(N, size=(M, 2))
    db.add_matches(1, 2, m12)
    db.add_matches(2, 3, m23)
    db.add_matches(3, 4, m34)
    rows = db.execute('SELECT * FROM cameras')
    camera_id, model, width, height, params, prior = next(rows)
    params = blob_to_array(params, np.float32)
    assert model == model1 and width == w1 and (height == h1)
    assert np.allclose(params, params1)
    camera_id, model, width, height, params, prior = next(rows)
    params = blob_to_array(params, np.float32)
    assert model == model2 and width == w2 and (height == h2)
    assert np.allclose(params, params2)
    kps = dict(((image_id, blob_to_array(data, np.float32, (-1, 2))) for image_id, data in db.execute('SELECT image_id, data FROM keypoints')))
    assert np.allclose(kps[1], kp1)
    assert np.allclose(kps[2], kp2)
    assert np.allclose(kps[3], kp3)
    assert np.allclose(kps[4], kp4)
    pair_ids = [get_pair_id(*pair) for pair in [(1, 2), (2, 3), (3, 4)]]
    matches = dict(((get_image_ids_from_pair_id(pair_id), blob_to_array(data, np.uint32, (-1, 2))) for pair_id, data in db.execute('SELECT pair_id, data FROM matches')))
    assert np.all(matches[1, 2] == m12)
    assert np.all(matches[2, 3] == m23)
    assert np.all(matches[3, 4] == m34)
    db.close()
    os.remove(args.database_path)

class SceneManager:
    INVALID_POINT3D = np.uint64(-1)

    def __init__(self, colmap_results_folder, image_path=None):
        self.folder = colmap_results_folder
        if not self.folder.endswith('/'):
            self.folder += '/'
        self.image_path = None
        self.load_colmap_project_file(image_path=image_path)
        self.cameras = OrderedDict()
        self.images = OrderedDict()
        self.name_to_image_id = dict()
        self.last_camera_id = 0
        self.last_image_id = 0
        self.points3D = np.zeros((0, 3))
        self.point3D_ids = np.empty(0)
        self.point3D_id_to_point3D_idx = dict()
        self.point3D_id_to_images = dict()
        self.point3D_colors = np.zeros((0, 3), dtype=np.uint8)
        self.point3D_errors = np.zeros(0)

    def load_colmap_project_file(self, project_file=None, image_path=None):
        if project_file is None:
            project_file = self.folder + 'project.ini'
        self.image_path = image_path
        if self.image_path is None:
            try:
                with open(project_file, 'r') as f:
                    for line in iter(f.readline, ''):
                        if line.startswith('image_path'):
                            self.image_path = line[11:].strip()
                            break
            except:
                pass
        if self.image_path is None:
            print('Warning: image_path not found for reconstruction')
        elif not self.image_path.endswith('/'):
            self.image_path += '/'

    def load(self):
        self.load_cameras()
        self.load_images()
        self.load_points3D()

    def load_cameras(self, input_file=None):
        if input_file is None:
            input_file = self.folder + 'cameras.bin'
            if os.path.exists(input_file):
                self._load_cameras_bin(input_file)
            else:
                input_file = self.folder + 'cameras.txt'
                if os.path.exists(input_file):
                    self._load_cameras_txt(input_file)
                else:
                    raise IOError('no cameras file found')

    def _load_cameras_bin(self, input_file):
        self.cameras = OrderedDict()
        with open(input_file, 'rb') as f:
            num_cameras = struct.unpack('L', f.read(8))[0]
            for _ in range(num_cameras):
                camera_id, camera_type, w, h = struct.unpack('IiLL', f.read(24))
                num_params = Camera.GetNumParams(camera_type)
                params = struct.unpack('d' * num_params, f.read(8 * num_params))
                self.cameras[camera_id] = Camera(camera_type, w, h, params)
                self.last_camera_id = max(self.last_camera_id, camera_id)

    def _load_cameras_txt(self, input_file):
        self.cameras = OrderedDict()
        with open(input_file, 'r') as f:
            for line in iter(lambda: f.readline().strip(), ''):
                if not line or line.startswith('#'):
                    continue
                data = line.split()
                camera_id = int(data[0])
                self.cameras[camera_id] = Camera(data[1], int(data[2]), int(data[3]), map(float, data[4:]))
                self.last_camera_id = max(self.last_camera_id, camera_id)

    def load_images(self, input_file=None):
        if input_file is None:
            input_file = self.folder + 'images.bin'
            if os.path.exists(input_file):
                self._load_images_bin(input_file)
            else:
                input_file = self.folder + 'images.txt'
                if os.path.exists(input_file):
                    self._load_images_txt(input_file)
                else:
                    raise IOError('no images file found')

    def _load_images_bin(self, input_file):
        self.images = OrderedDict()
        with open(input_file, 'rb') as f:
            num_images = struct.unpack('L', f.read(8))[0]
            image_struct = struct.Struct('<I 4d 3d I')
            for _ in range(num_images):
                data = image_struct.unpack(f.read(image_struct.size))
                image_id = data[0]
                q = Quaternion(np.array(data[1:5]))
                t = np.array(data[5:8])
                camera_id = data[8]
                name = b''.join((c for c in iter(lambda: f.read(1), b'\x00'))).decode()
                image = Image(name, camera_id, q, t)
                num_points2D = struct.unpack('Q', f.read(8))[0]
                points_array = array.array('d')
                points_array.fromfile(f, 3 * num_points2D)
                points_elements = np.array(points_array).reshape((num_points2D, 3))
                image.points2D = points_elements[:, :2]
                ids_array = array.array('Q')
                ids_array.frombytes(points_elements[:, 2].tobytes())
                image.point3D_ids = np.array(ids_array, dtype=np.uint64).reshape((num_points2D,))
                self.images[image_id] = image
                self.name_to_image_id[image.name] = image_id
                self.last_image_id = max(self.last_image_id, image_id)

    def _load_images_txt(self, input_file):
        self.images = OrderedDict()
        with open(input_file, 'r') as f:
            is_camera_description_line = False
            for line in iter(lambda: f.readline().strip(), ''):
                if not line or line.startswith('#'):
                    continue
                is_camera_description_line = not is_camera_description_line
                data = line.split()
                if is_camera_description_line:
                    image_id = int(data[0])
                    image = Image(data[-1], int(data[-2]), Quaternion(np.array(map(float, data[1:5]))), np.array(map(float, data[5:8])))
                else:
                    image.points2D = np.array([map(float, data[::3]), map(float, data[1::3])]).T
                    image.point3D_ids = np.array(map(np.uint64, data[2::3]))
                    self.images[image_id] = image
                    self.name_to_image_id[image.name] = image_id
                    self.last_image_id = max(self.last_image_id, image_id)

    def load_points3D(self, input_file=None):
        if input_file is None:
            input_file = self.folder + 'points3D.bin'
            if os.path.exists(input_file):
                self._load_points3D_bin(input_file)
            else:
                input_file = self.folder + 'points3D.txt'
                if os.path.exists(input_file):
                    self._load_points3D_txt(input_file)
                else:
                    raise IOError('no points3D file found')

    def _load_points3D_bin(self, input_file):
        with open(input_file, 'rb') as f:
            num_points3D = struct.unpack('L', f.read(8))[0]
            self.points3D = np.empty((num_points3D, 3))
            self.point3D_ids = np.empty(num_points3D, dtype=np.uint64)
            self.point3D_colors = np.empty((num_points3D, 3), dtype=np.uint8)
            self.point3D_id_to_point3D_idx = dict()
            self.point3D_id_to_images = dict()
            self.point3D_errors = np.empty(num_points3D)
            data_struct = struct.Struct('<Q 3d 3B d Q')
            for i in range(num_points3D):
                data = data_struct.unpack(f.read(data_struct.size))
                self.point3D_ids[i] = data[0]
                self.points3D[i] = data[1:4]
                self.point3D_colors[i] = data[4:7]
                self.point3D_errors[i] = data[7]
                track_len = data[8]
                self.point3D_id_to_point3D_idx[self.point3D_ids[i]] = i
                data = struct.unpack(f'{2 * track_len}I', f.read(2 * track_len * 4))
                self.point3D_id_to_images[self.point3D_ids[i]] = np.array(data, dtype=np.uint32).reshape(track_len, 2)

    def _load_points3D_txt(self, input_file):
        self.points3D = []
        self.point3D_ids = []
        self.point3D_colors = []
        self.point3D_id_to_point3D_idx = dict()
        self.point3D_id_to_images = dict()
        self.point3D_errors = []
        with open(input_file, 'r') as f:
            for line in iter(lambda: f.readline().strip(), ''):
                if not line or line.startswith('#'):
                    continue
                data = line.split()
                point3D_id = np.uint64(data[0])
                self.point3D_ids.append(point3D_id)
                self.point3D_id_to_point3D_idx[point3D_id] = len(self.points3D)
                self.points3D.append(map(np.float64, data[1:4]))
                self.point3D_colors.append(map(np.uint8, data[4:7]))
                self.point3D_errors.append(np.float64(data[7]))
                self.point3D_id_to_images[point3D_id] = np.array(map(np.uint32, data[8:])).reshape(-1, 2)
        self.points3D = np.array(self.points3D)
        self.point3D_ids = np.array(self.point3D_ids)
        self.point3D_colors = np.array(self.point3D_colors)
        self.point3D_errors = np.array(self.point3D_errors)

    def save(self, output_folder, binary=True):
        self.save_cameras(output_folder, binary=binary)
        self.save_images(output_folder, binary=binary)
        self.save_points3D(output_folder, binary=binary)

    def save_cameras(self, output_folder, output_file=None, binary=True):
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        if output_file is None:
            output_file = 'cameras.bin' if binary else 'cameras.txt'
        output_file = os.path.join(output_folder, output_file)
        if binary:
            self._save_cameras_bin(output_file)
        else:
            self._save_cameras_txt(output_file)

    def _save_cameras_bin(self, output_file):
        with open(output_file, 'wb') as fid:
            fid.write(struct.pack('L', len(self.cameras)))
            camera_struct = struct.Struct('IiLL')
            for camera_id, camera in sorted(self.cameras.iteritems()):
                fid.write(camera_struct.pack(camera_id, camera.camera_type, camera.width, camera.height))
                fid.write(camera.get_params().tobytes())

    def _save_cameras_txt(self, output_file):
        with open(output_file, 'w') as fid:
            (print >> fid, '# Camera list with one line of data per camera:')
            (print >> fid, '#   CAMERA_ID, MODEL, WIDTH, HEIGHT, PARAMS[]')
            (print >> fid, '# Number of cameras:', len(self.cameras))
            for camera_id, camera in sorted(self.cameras.iteritems()):
                (print >> fid, camera_id, camera)

    def save_images(self, output_folder, output_file=None, binary=True):
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        if output_file is None:
            output_file = 'images.bin' if binary else 'images.txt'
        output_file = os.path.join(output_folder, output_file)
        if binary:
            self._save_images_bin(output_file)
        else:
            self._save_images_txt(output_file)

    def _save_images_bin(self, output_file):
        with open(output_file, 'wb') as fid:
            fid.write(struct.pack('L', len(self.images)))
            for image_id, image in self.images.iteritems():
                fid.write(struct.pack('I', image_id))
                fid.write(image.q.q.tobytes())
                fid.write(image.tvec.tobytes())
                fid.write(struct.pack('I', image.camera_id))
                fid.write(image.name + '\x00')
                fid.write(struct.pack('L', len(image.points2D)))
                data = np.rec.fromarrays((image.points2D[:, 0], image.points2D[:, 1], image.point3D_ids))
                fid.write(data.tobytes())

    def _save_images_txt(self, output_file):
        with open(output_file, 'w') as fid:
            (print >> fid, '# Image list with two lines of data per image:')
            (print >> fid, '#   IMAGE_ID, QW, QX, QY, QZ, TX, TY, TZ, CAMERA_ID, NAME')
            (print >> fid, '#   POINTS2D[] as (X, Y, POINT3D_ID)')
            (print >> fid, '# Number of images: {},'.format(len(self.images)))
            (print >> fid, 'mean observations per image: unknown')
            for image_id, image in self.images.iteritems():
                (print >> fid, image_id)
                (print >> fid, ' '.join((str(qi) for qi in image.q.q)))
                (print >> fid, ' '.join((str(ti) for ti in image.tvec)))
                (print >> fid, image.camera_id, image.name)
                data = np.rec.fromarrays((image.points2D[:, 0], image.points2D[:, 1], image.point3D_ids.astype(np.int64)))
                if len(data) > 0:
                    np.savetxt(fid, data, '%.2f %.2f %d', newline=' ')
                    fid.seek(-1, os.SEEK_CUR)
                fid.write('\n')

    def save_points3D(self, output_folder, output_file=None, binary=True):
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        if output_file is None:
            output_file = 'points3D.bin' if binary else 'points3D.txt'
        output_file = os.path.join(output_folder, output_file)
        if binary:
            self._save_points3D_bin(output_file)
        else:
            self._save_points3D_txt(output_file)

    def _save_points3D_bin(self, output_file):
        num_valid_points3D = sum((1 for point3D_idx in self.point3D_id_to_point3D_idx.itervalues() if point3D_idx != SceneManager.INVALID_POINT3D))
        iter_point3D_id_to_point3D_idx = self.point3D_id_to_point3D_idx.iteritems()
        with open(output_file, 'wb') as fid:
            fid.write(struct.pack('L', num_valid_points3D))
            for point3D_id, point3D_idx in iter_point3D_id_to_point3D_idx:
                if point3D_idx == SceneManager.INVALID_POINT3D:
                    continue
                fid.write(struct.pack('L', point3D_id))
                fid.write(self.points3D[point3D_idx].tobytes())
                fid.write(self.point3D_colors[point3D_idx].tobytes())
                fid.write(self.point3D_errors[point3D_idx].tobytes())
                fid.write(struct.pack('L', len(self.point3D_id_to_images[point3D_id])))
                fid.write(self.point3D_id_to_images[point3D_id].tobytes())

    def _save_points3D_txt(self, output_file):
        num_valid_points3D = sum((1 for point3D_idx in self.point3D_id_to_point3D_idx.itervalues() if point3D_idx != SceneManager.INVALID_POINT3D))
        array_to_string = lambda arr: ' '.join((str(x) for x in arr))
        iter_point3D_id_to_point3D_idx = self.point3D_id_to_point3D_idx.iteritems()
        with open(output_file, 'w') as fid:
            (print >> fid, '# 3D point list with one line of data per point:')
            (print >> fid, '#   POINT3D_ID, X, Y, Z, R, G, B, ERROR, TRACK[] as ')
            (print >> fid, '(IMAGE_ID, POINT2D_IDX)')
            (print >> fid, '# Number of points: {},'.format(num_valid_points3D))
            (print >> fid, 'mean track length: unknown')
            for point3D_id, point3D_idx in iter_point3D_id_to_point3D_idx:
                if point3D_idx == SceneManager.INVALID_POINT3D:
                    continue
                (print >> fid, point3D_id)
                (print >> fid, array_to_string(self.points3D[point3D_idx]))
                (print >> fid, array_to_string(self.point3D_colors[point3D_idx]))
                (print >> fid, self.point3D_errors[point3D_idx])
                (print >> fid, array_to_string(self.point3D_id_to_images[point3D_id].flat))

    def get_image_from_name(self, image_name):
        image_id = self.name_to_image_id[image_name]
        return (image_id, self.images[image_id])

    def get_camera(self, camera_id):
        return self.cameras[camera_id]

    def get_points3D(self, image_id, return_points2D=True, return_colors=False):
        image = self.images[image_id]
        mask = image.point3D_ids != SceneManager.INVALID_POINT3D
        point3D_idxs = np.array([self.point3D_id_to_point3D_idx[point3D_id] for point3D_id in image.point3D_ids[mask]])
        filter_mask = point3D_idxs != SceneManager.INVALID_POINT3D
        point3D_idxs = point3D_idxs[filter_mask]
        result = [self.points3D[point3D_idxs, :]]
        if return_points2D:
            mask[mask] &= filter_mask
            result += [image.points2D[mask]]
        if return_colors:
            result += [self.point3D_colors[point3D_idxs, :]]
        return result if len(result) > 1 else result[0]

    def point3D_valid(self, point3D_id):
        return self.point3D_id_to_point3D_idx[point3D_id] != SceneManager.INVALID_POINT3D

    def get_filtered_points3D(self, return_colors=False):
        point3D_idxs = [idx for idx in self.point3D_id_to_point3D_idx.values() if idx != SceneManager.INVALID_POINT3D]
        result = [self.points3D[point3D_idxs, :]]
        if return_colors:
            result += [self.point3D_colors[point3D_idxs, :]]
        return result if len(result) > 1 else result[0]

    def get_shared_points3D(self, image_id1, image_id2):
        point3D_ids = set(self.images[image_id1].point3D_ids) & set(self.images[image_id2].point3D_ids)
        point3D_ids.discard(SceneManager.INVALID_POINT3D)
        point3D_idxs = np.array([self.point3D_id_to_point3D_idx[point3D_id] for point3D_id in point3D_ids])
        return self.points3D[point3D_idxs, :]

    def get_viewed_points(self, image_id):
        image = self.images[image_id]
        point3D_idxs = set(self.point3D_id_to_point3D_idx.itervalues())
        point3D_idxs.discard(SceneManager.INVALID_POINT3D)
        point3D_idxs = list(point3D_idxs)
        points3D = self.points3D[point3D_idxs, :]
        R = image.q.ToR()
        points3D = points3D.dot(R.T) + image.tvec[np.newaxis, :]
        points3D = points3D[points3D[:, 2] > 0, :]
        camera = self.cameras[image.camera_id]
        points2D = points3D.dot(camera.get_camera_matrix().T)
        points2D = points2D[:, :2] / points2D[:, 2][:, np.newaxis]
        mask = (points2D[:, 0] >= 0) & (points2D[:, 1] >= 0) & (points2D[:, 0] < camera.width - 1) & (points2D[:, 1] < camera.height - 1)
        return (points2D[mask, :], points3D[mask, :])

    def add_camera(self, camera):
        self.last_camera_id += 1
        self.cameras[self.last_camera_id] = camera
        return self.last_camera_id

    def add_image(self, image):
        self.last_image_id += 1
        self.images[self.last_image_id] = image
        return self.last_image_id

    def delete_images(self, image_list):
        for image_id in image_list:
            if image_id in self.images:
                del self.images[image_id]
        keep_set = set(self.images.iterkeys())
        iter_point3D_id_to_point3D_idx = self.point3D_id_to_point3D_idx.iteritems()
        for point3D_id, point3D_idx in iter_point3D_id_to_point3D_idx:
            if point3D_idx == SceneManager.INVALID_POINT3D:
                continue
            mask = np.array([image_id in keep_set for image_id in self.point3D_id_to_images[point3D_id][:, 0]])
            if np.any(mask):
                self.point3D_id_to_images[point3D_id] = self.point3D_id_to_images[point3D_id][mask]
            else:
                self.point3D_id_to_point3D_idx[point3D_id] = SceneManager.INVALID_POINT3D

    def filter_points3D(self, min_track_len=0, max_error=np.inf, min_tri_angle=0, max_tri_angle=180, image_set=set()):
        image_set = set(image_set)
        check_triangulation_angles = min_tri_angle > 0 or max_tri_angle < 180
        if check_triangulation_angles:
            max_tri_prod = np.cos(np.radians(min_tri_angle))
            min_tri_prod = np.cos(np.radians(max_tri_angle))
        iter_point3D_id_to_point3D_idx = self.point3D_id_to_point3D_idx.iteritems()
        image_ids = []
        for point3D_id, point3D_idx in iter_point3D_id_to_point3D_idx:
            if point3D_idx == SceneManager.INVALID_POINT3D:
                continue
            if image_set or min_track_len > 0:
                image_ids = set(self.point3D_id_to_images[point3D_id][:, 0])
            if len(image_ids) < min_track_len or self.point3D_errors[point3D_idx] > max_error or (image_set and image_set.isdisjoint(image_ids)):
                self.point3D_id_to_point3D_idx[point3D_id] = SceneManager.INVALID_POINT3D
            elif check_triangulation_angles:
                xyz = self.points3D[point3D_idx, :]
                tvecs = np.array([self.images[image_id].tvec - xyz for image_id in image_ids])
                tvecs /= np.linalg.norm(tvecs, axis=-1)[:, np.newaxis]
                cos_theta = np.array([u.dot(v) for u, v in combinations(tvecs, 2)])
                if np.min(cos_theta) > max_tri_prod or np.max(cos_theta) < min_tri_prod:
                    self.point3D_id_to_point3D_idx[point3D_id] = SceneManager.INVALID_POINT3D
        for image in self.images.itervalues():
            mask = np.array([self.point3D_id_to_point3D_idx.get(point3D_id, 0) == SceneManager.INVALID_POINT3D for point3D_id in image.point3D_ids])
            image.point3D_ids[mask] = SceneManager.INVALID_POINT3D

    def build_scene_graph(self):
        self.scene_graph = defaultdict(lambda: defaultdict(int))
        point3D_iter = self.point3D_id_to_images.iteritems()
        for i, (point3D_id, images) in enumerate(point3D_iter):
            if not self.point3D_valid(point3D_id):
                continue
            for image_id1, image_id2 in combinations(images[:, 0], 2):
                self.scene_graph[image_id1][image_id2] += 1
                self.scene_graph[image_id2][image_id1] += 1

def get_points3D(self, image_id, return_points2D=True, return_colors=False):
    image = self.images[image_id]
    mask = image.point3D_ids != SceneManager.INVALID_POINT3D
    point3D_idxs = np.array([self.point3D_id_to_point3D_idx[point3D_id] for point3D_id in image.point3D_ids[mask]])
    filter_mask = point3D_idxs != SceneManager.INVALID_POINT3D
    point3D_idxs = point3D_idxs[filter_mask]
    result = [self.points3D[point3D_idxs, :]]
    if return_points2D:
        mask[mask] &= filter_mask
        result += [image.points2D[mask]]
    if return_colors:
        result += [self.point3D_colors[point3D_idxs, :]]
    return result if len(result) > 1 else result[0]

def get_shared_points3D(self, image_id1, image_id2):
    point3D_ids = set(self.images[image_id1].point3D_ids) & set(self.images[image_id2].point3D_ids)
    point3D_ids.discard(SceneManager.INVALID_POINT3D)
    point3D_idxs = np.array([self.point3D_id_to_point3D_idx[point3D_id] for point3D_id in point3D_ids])
    return self.points3D[point3D_idxs, :]

def get_viewed_points(self, image_id):
    image = self.images[image_id]
    point3D_idxs = set(self.point3D_id_to_point3D_idx.itervalues())
    point3D_idxs.discard(SceneManager.INVALID_POINT3D)
    point3D_idxs = list(point3D_idxs)
    points3D = self.points3D[point3D_idxs, :]
    R = image.q.ToR()
    points3D = points3D.dot(R.T) + image.tvec[np.newaxis, :]
    points3D = points3D[points3D[:, 2] > 0, :]
    camera = self.cameras[image.camera_id]
    points2D = points3D.dot(camera.get_camera_matrix().T)
    points2D = points2D[:, :2] / points2D[:, 2][:, np.newaxis]
    mask = (points2D[:, 0] >= 0) & (points2D[:, 1] >= 0) & (points2D[:, 0] < camera.width - 1) & (points2D[:, 1] < camera.height - 1)
    return (points2D[mask, :], points3D[mask, :])

def delete_images(self, image_list):
    for image_id in image_list:
        if image_id in self.images:
            del self.images[image_id]
    keep_set = set(self.images.iterkeys())
    iter_point3D_id_to_point3D_idx = self.point3D_id_to_point3D_idx.iteritems()
    for point3D_id, point3D_idx in iter_point3D_id_to_point3D_idx:
        if point3D_idx == SceneManager.INVALID_POINT3D:
            continue
        mask = np.array([image_id in keep_set for image_id in self.point3D_id_to_images[point3D_id][:, 0]])
        if np.any(mask):
            self.point3D_id_to_images[point3D_id] = self.point3D_id_to_images[point3D_id][mask]
        else:
            self.point3D_id_to_point3D_idx[point3D_id] = SceneManager.INVALID_POINT3D

def filter_points3D(self, min_track_len=0, max_error=np.inf, min_tri_angle=0, max_tri_angle=180, image_set=set()):
    image_set = set(image_set)
    check_triangulation_angles = min_tri_angle > 0 or max_tri_angle < 180
    if check_triangulation_angles:
        max_tri_prod = np.cos(np.radians(min_tri_angle))
        min_tri_prod = np.cos(np.radians(max_tri_angle))
    iter_point3D_id_to_point3D_idx = self.point3D_id_to_point3D_idx.iteritems()
    image_ids = []
    for point3D_id, point3D_idx in iter_point3D_id_to_point3D_idx:
        if point3D_idx == SceneManager.INVALID_POINT3D:
            continue
        if image_set or min_track_len > 0:
            image_ids = set(self.point3D_id_to_images[point3D_id][:, 0])
        if len(image_ids) < min_track_len or self.point3D_errors[point3D_idx] > max_error or (image_set and image_set.isdisjoint(image_ids)):
            self.point3D_id_to_point3D_idx[point3D_id] = SceneManager.INVALID_POINT3D
        elif check_triangulation_angles:
            xyz = self.points3D[point3D_idx, :]
            tvecs = np.array([self.images[image_id].tvec - xyz for image_id in image_ids])
            tvecs /= np.linalg.norm(tvecs, axis=-1)[:, np.newaxis]
            cos_theta = np.array([u.dot(v) for u, v in combinations(tvecs, 2)])
            if np.min(cos_theta) > max_tri_prod or np.max(cos_theta) < min_tri_prod:
                self.point3D_id_to_point3D_idx[point3D_id] = SceneManager.INVALID_POINT3D
    for image in self.images.itervalues():
        mask = np.array([self.point3D_id_to_point3D_idx.get(point3D_id, 0) == SceneManager.INVALID_POINT3D for point3D_id in image.point3D_ids])
        image.point3D_ids[mask] = SceneManager.INVALID_POINT3D

class Image:

    def __init__(self, name_, camera_id_, q_, tvec_):
        self.name = name_
        self.camera_id = camera_id_
        self.q = q_
        self.tvec = tvec_
        self.points2D = np.empty((0, 2), dtype=np.float64)
        self.point3D_ids = np.empty((0,), dtype=np.uint64)

    def R(self):
        return self.q.ToR()

    def C(self):
        return -self.R().T.dot(self.tvec)

    @property
    def t(self):
        return self.tvec

def R(self):
    return self.q.ToR()

def C(self):
    return -self.R().T.dot(self.tvec)

def cross_prod_matrix(v):
    return np.array(((0.0, -v[2], v[1]), (v[2], 0.0, -v[0]), (-v[1], v[0], 0.0)))

def axis_angle_to_rotation_matrix(axis, angle=None):
    if angle is None:
        angle = np.linalg.norm(axis)
        if np.abs(angle) > np.finfo('float').eps:
            axis = axis / angle
    cp_axis = cross_prod_matrix(axis)
    return np.eye(3) + (np.sin(angle) * cp_axis + (1.0 - np.cos(angle)) * cp_axis.dot(cp_axis))

class Quaternion:

    @staticmethod
    def FromR(R):
        trace = np.trace(R)
        if trace > 0:
            qw = 0.5 * np.sqrt(1.0 + trace)
            qx = (R[2, 1] - R[1, 2]) * 0.25 / qw
            qy = (R[0, 2] - R[2, 0]) * 0.25 / qw
            qz = (R[1, 0] - R[0, 1]) * 0.25 / qw
        elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
            s = 2.0 * np.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2])
            qw = (R[2, 1] - R[1, 2]) / s
            qx = 0.25 * s
            qy = (R[0, 1] + R[1, 0]) / s
            qz = (R[0, 2] + R[2, 0]) / s
        elif R[1, 1] > R[2, 2]:
            s = 2.0 * np.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2])
            qw = (R[0, 2] - R[2, 0]) / s
            qx = (R[0, 1] + R[1, 0]) / s
            qy = 0.25 * s
            qz = (R[1, 2] + R[2, 1]) / s
        else:
            s = 2.0 * np.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1])
            qw = (R[1, 0] - R[0, 1]) / s
            qx = (R[0, 2] + R[2, 0]) / s
            qy = (R[1, 2] + R[2, 1]) / s
            qz = 0.25 * s
        return Quaternion(np.array((qw, qx, qy, qz)))

    @staticmethod
    def FromAxisAngle(axis, angle=None):
        if angle is None:
            angle = np.linalg.norm(axis)
            if np.abs(angle) > np.finfo('float').eps:
                axis = axis / angle
        qw = np.cos(0.5 * angle)
        axis = axis * np.sin(0.5 * angle)
        return Quaternion(np.array((qw, axis[0], axis[1], axis[2])))

    def __init__(self, q=np.array((1.0, 0.0, 0.0, 0.0))):
        if isinstance(q, Quaternion):
            self.q = q.q.copy()
        else:
            q = np.asarray(q)
            if q.size == 4:
                self.q = q.copy()
            elif q.size == 3:
                self.q = np.empty(4)
                self.q[0], self.q[1:] = (0.0, q.ravel())
            else:
                raise Exception('Input quaternion should be a 3- or 4-vector')

    def __add__(self, other):
        return Quaternion(self.q + other.q)

    def __iadd__(self, other):
        self.q += other.q
        return self

    def __invert__(self):
        return Quaternion(np.array((self.q[0], -self.q[1], -self.q[2], -self.q[3])))

    def __mul__(self, other):
        if isinstance(other, Quaternion):
            return Quaternion(np.array((self.q[0] * other.q[0] - self.q[1] * other.q[1] - self.q[2] * other.q[2] - self.q[3] * other.q[3], self.q[0] * other.q[1] + self.q[1] * other.q[0] + self.q[2] * other.q[3] - self.q[3] * other.q[2], self.q[0] * other.q[2] - self.q[1] * other.q[3] + self.q[2] * other.q[0] + self.q[3] * other.q[1], self.q[0] * other.q[3] + self.q[1] * other.q[2] - self.q[2] * other.q[1] + self.q[3] * other.q[0])))
        else:
            return Quaternion(other * self.q)

    def __rmul__(self, other):
        return self * other

    def __imul__(self, other):
        self.q[:] = (self * other).q
        return self

    def __irmul__(self, other):
        self.q[:] = (self * other).q
        return self

    def __neg__(self):
        return Quaternion(-self.q)

    def __sub__(self, other):
        return Quaternion(self.q - other.q)

    def __isub__(self, other):
        self.q -= other.q
        return self

    def __str__(self):
        return str(self.q)

    def copy(self):
        return Quaternion(self)

    def dot(self, other):
        return self.q.dot(other.q)

    def inverse(self):
        return Quaternion((~self).q / self.q.dot(self.q))

    def norm(self):
        return np.linalg.norm(self.q)

    def normalize(self):
        self.q /= np.linalg.norm(self.q)
        return self

    def rotate_points(self, x):
        x = np.atleast_2d(x)
        return x.dot(self.ToR().T)

    def ToR(self):
        return np.eye(3) + 2 * np.array(((-self.q[2] * self.q[2] - self.q[3] * self.q[3], self.q[1] * self.q[2] - self.q[3] * self.q[0], self.q[1] * self.q[3] + self.q[2] * self.q[0]), (self.q[1] * self.q[2] + self.q[3] * self.q[0], -self.q[1] * self.q[1] - self.q[3] * self.q[3], self.q[2] * self.q[3] - self.q[1] * self.q[0]), (self.q[1] * self.q[3] - self.q[2] * self.q[0], self.q[2] * self.q[3] + self.q[1] * self.q[0], -self.q[1] * self.q[1] - self.q[2] * self.q[2])))

    def ToAxisAngle(self):
        sin_sq_theta = self.q[1:].dot(self.q[1:])
        if np.abs(sin_sq_theta) > np.finfo('float').eps:
            sin_theta = np.sqrt(sin_sq_theta)
            cos_theta = self.q[0]
            angle = 2.0 * (np.arctan2(-sin_theta, -cos_theta) if cos_theta < 0.0 else np.arctan2(sin_theta, cos_theta))
            return self.q[1:] * (angle / sin_theta)
        return np.zeros(3)

    def ToEulerAngles(self):
        qsq = self.q ** 2
        k = 2.0 * (self.q[0] * self.q[3] + self.q[1] * self.q[2]) / qsq.sum()
        if 1.0 - k < np.finfo('float').eps:
            return (2.0 * np.arctan2(self.q[1], self.q[0]), 0.5 * np.pi, 0.0)
        if 1.0 + k < np.finfo('float').eps:
            return (-2.0 * np.arctan2(self.q[1], self.q[0]), -0.5 * np.pi, 0.0)
        yaw = np.arctan2(2.0 * (self.q[0] * self.q[2] - self.q[1] * self.q[3]), qsq[0] + qsq[1] - qsq[2] - qsq[3])
        pitch = np.arcsin(k)
        roll = np.arctan2(2.0 * (self.q[0] * self.q[1] - self.q[2] * self.q[3]), qsq[0] - qsq[1] + qsq[2] - qsq[3])
        return (yaw, pitch, roll)

@staticmethod
def FromR(R):
    trace = np.trace(R)
    if trace > 0:
        qw = 0.5 * np.sqrt(1.0 + trace)
        qx = (R[2, 1] - R[1, 2]) * 0.25 / qw
        qy = (R[0, 2] - R[2, 0]) * 0.25 / qw
        qz = (R[1, 0] - R[0, 1]) * 0.25 / qw
    elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        s = 2.0 * np.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2])
        qw = (R[2, 1] - R[1, 2]) / s
        qx = 0.25 * s
        qy = (R[0, 1] + R[1, 0]) / s
        qz = (R[0, 2] + R[2, 0]) / s
    elif R[1, 1] > R[2, 2]:
        s = 2.0 * np.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2])
        qw = (R[0, 2] - R[2, 0]) / s
        qx = (R[0, 1] + R[1, 0]) / s
        qy = 0.25 * s
        qz = (R[1, 2] + R[2, 1]) / s
    else:
        s = 2.0 * np.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1])
        qw = (R[1, 0] - R[0, 1]) / s
        qx = (R[0, 2] + R[2, 0]) / s
        qy = (R[1, 2] + R[2, 1]) / s
        qz = 0.25 * s
    return Quaternion(np.array((qw, qx, qy, qz)))

@staticmethod
def FromAxisAngle(axis, angle=None):
    if angle is None:
        angle = np.linalg.norm(axis)
        if np.abs(angle) > np.finfo('float').eps:
            axis = axis / angle
    qw = np.cos(0.5 * angle)
    axis = axis * np.sin(0.5 * angle)
    return Quaternion(np.array((qw, axis[0], axis[1], axis[2])))

def __init__(self, q=np.array((1.0, 0.0, 0.0, 0.0))):
    if isinstance(q, Quaternion):
        self.q = q.q.copy()
    else:
        q = np.asarray(q)
        if q.size == 4:
            self.q = q.copy()
        elif q.size == 3:
            self.q = np.empty(4)
            self.q[0], self.q[1:] = (0.0, q.ravel())
        else:
            raise Exception('Input quaternion should be a 3- or 4-vector')

def __add__(self, other):
    return Quaternion(self.q + other.q)

def __invert__(self):
    return Quaternion(np.array((self.q[0], -self.q[1], -self.q[2], -self.q[3])))

def __mul__(self, other):
    if isinstance(other, Quaternion):
        return Quaternion(np.array((self.q[0] * other.q[0] - self.q[1] * other.q[1] - self.q[2] * other.q[2] - self.q[3] * other.q[3], self.q[0] * other.q[1] + self.q[1] * other.q[0] + self.q[2] * other.q[3] - self.q[3] * other.q[2], self.q[0] * other.q[2] - self.q[1] * other.q[3] + self.q[2] * other.q[0] + self.q[3] * other.q[1], self.q[0] * other.q[3] + self.q[1] * other.q[2] - self.q[2] * other.q[1] + self.q[3] * other.q[0])))
    else:
        return Quaternion(other * self.q)

def __neg__(self):
    return Quaternion(-self.q)

def __sub__(self, other):
    return Quaternion(self.q - other.q)

def copy(self):
    return Quaternion(self)

def dot(self, other):
    return self.q.dot(other.q)

def inverse(self):
    return Quaternion((~self).q / self.q.dot(self.q))

def rotate_points(self, x):
    x = np.atleast_2d(x)
    return x.dot(self.ToR().T)

def ToR(self):
    return np.eye(3) + 2 * np.array(((-self.q[2] * self.q[2] - self.q[3] * self.q[3], self.q[1] * self.q[2] - self.q[3] * self.q[0], self.q[1] * self.q[3] + self.q[2] * self.q[0]), (self.q[1] * self.q[2] + self.q[3] * self.q[0], -self.q[1] * self.q[1] - self.q[3] * self.q[3], self.q[2] * self.q[3] - self.q[1] * self.q[0]), (self.q[1] * self.q[3] - self.q[2] * self.q[0], self.q[2] * self.q[3] + self.q[1] * self.q[0], -self.q[1] * self.q[1] - self.q[2] * self.q[2])))

def ToAxisAngle(self):
    sin_sq_theta = self.q[1:].dot(self.q[1:])
    if np.abs(sin_sq_theta) > np.finfo('float').eps:
        sin_theta = np.sqrt(sin_sq_theta)
        cos_theta = self.q[0]
        angle = 2.0 * (np.arctan2(-sin_theta, -cos_theta) if cos_theta < 0.0 else np.arctan2(sin_theta, cos_theta))
        return self.q[1:] * (angle / sin_theta)
    return np.zeros(3)

class DualQuaternion:

    @staticmethod
    def FromQT(q, t):
        return DualQuaternion(qe=0.5 * np.asarray(t)) * DualQuaternion(q)

    def __init__(self, q0=np.array((1.0, 0.0, 0.0, 0.0)), qe=np.zeros(4)):
        self.q0, self.qe = (Quaternion(q0), Quaternion(qe))

    def __add__(self, other):
        return DualQuaternion(self.q0 + other.q0, self.qe + other.qe)

    def __iadd__(self, other):
        self.q0 += other.q0
        self.qe += other.qe
        return self

    def __invert__(self):
        return DualQuaternion(~self.q0, ~self.qe)

    def __mul__(self, other):
        if isinstance(other, DualQuaternion):
            return DualQuaternion(self.q0 * other.q0, self.q0 * other.qe + self.qe * other.q0)
        elif isinstance(other, complex):
            return DualQuaternion(self.q0 * other.real, self.q0 * other.imag + self.qe * other.real)
        else:
            return DualQuaternion(other * self.q0, other * self.qe)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __imul__(self, other):
        tmp = self * other
        self.q0, self.qe = (tmp.q0, tmp.qe)
        return self

    def __neg__(self):
        return DualQuaternion(-self.q0, -self.qe)

    def __sub__(self, other):
        return DualQuaternion(self.q0 - other.q0, self.qe - other.qe)

    def __isub__(self, other):
        self.q0 -= other.q0
        self.qe -= other.qe
        return self

    def inverse(self):
        normsq = complex(q0.dot(q0), 2.0 * self.q0.q.dot(self.qe.q))
        inv_len_real = 1.0 / normsq.real
        return ~self * complex(inv_len_real, -normsq.imag * inv_len_real * inv_len_real)

    def norm(self):
        q0_norm = self.q0.norm()
        return complex(q0_norm, self.q0.dot(self.qe) / q0_norm)

    def normalize(self):
        norm = self.norm()
        inv_len_real = 1.0 / norm.real
        self *= complex(inv_len_real, -norm.imag * inv_len_real * inv_len_real)
        return self

    def getT(self):
        return 2 * (self.qe * ~self.q0).q[1:]

    def ToQT(self):
        return (self.q0, self.getT())

@staticmethod
def FromQT(q, t):
    return DualQuaternion(qe=0.5 * np.asarray(t)) * DualQuaternion(q)

def __init__(self, q0=np.array((1.0, 0.0, 0.0, 0.0)), qe=np.zeros(4)):
    self.q0, self.qe = (Quaternion(q0), Quaternion(qe))

def __add__(self, other):
    return DualQuaternion(self.q0 + other.q0, self.qe + other.qe)

def __invert__(self):
    return DualQuaternion(~self.q0, ~self.qe)

def __mul__(self, other):
    if isinstance(other, DualQuaternion):
        return DualQuaternion(self.q0 * other.q0, self.q0 * other.qe + self.qe * other.q0)
    elif isinstance(other, complex):
        return DualQuaternion(self.q0 * other.real, self.q0 * other.imag + self.qe * other.real)
    else:
        return DualQuaternion(other * self.q0, other * self.qe)

def __neg__(self):
    return DualQuaternion(-self.q0, -self.qe)

def __sub__(self, other):
    return DualQuaternion(self.q0 - other.q0, self.qe - other.qe)

class Scene(nn.Module):

    def __init__(self, config):
        self.data_root = config['data_root']
        self.scene_name = config['scene_name']
        self.ext_int_path = os.path.join(self.data_root, self.scene_name, config['ext_int_file'])
        self.bbox_path = os.path.join(self.data_root, self.scene_name, config['bbox_file'])
        self.map_path = os.path.join(self.data_root, self.scene_name, config['map_file'])
        self.pcd_path = os.path.join(self.data_root, self.scene_name, config['pcd_file'])
        self.init_img_path = os.path.join(self.data_root, self.scene_name, config['init_img_file'])
        with open(self.map_path, 'rb') as f:
            self.map_data = pickle.load(f)
        self.is_wide_angle = config['is_wide_angle']
        self.fps = config.get('fps', 20)
        self.frames = config['frames']
        self.multi_process_num = config.get('multi_process_num', 1)
        self.backup_hdri = config.get('backup_hdri', True)
        self.depth_and_occlusion = config.get('depth_and_occlusion', False)
        '\n        [static scene data] \n        '
        self.bbox_data = np.load(self.bbox_path, allow_pickle=True).item()
        pcd = o3d.io.read_point_cloud(self.pcd_path)
        self.pcd = np.asarray(pcd.points)
        self.pcd = self.pcd[self.pcd[:, -1] > 0.5]
        all_current_vertices = []
        for k in self.bbox_data.keys():
            current_vertices = generate_vertices(self.bbox_data[k])
            all_current_vertices.append(current_vertices)
        self.all_current_vertices = np.array(all_current_vertices)
        if self.all_current_vertices.shape[0] > 0:
            self.all_current_vertices_coord = np.mean(self.all_current_vertices, axis=1)[:, :2]
        else:
            self.all_current_vertices_coord = np.zeros((0, 2))
        extrinsics = np.load(self.ext_int_path)[:, :12].reshape(-1, 3, 4)
        extrinsics = extrinsics[:, :3, :4]
        self.nerf_motion_extrinsics = extrinsics
        self.intrinsics = np.load(self.ext_int_path)[:, 12:21].reshape(-1, 3, 3)[0]
        self.focal = self.intrinsics[0, 0]
        self.height = 1280
        self.width = 1920
        if self.is_wide_angle:
            self.intrinsics[0, 2] += 1920
            self.width = 1920 * 3
        "\n        [dynamic scene data], will be updated during parsing. \n        ---\n        current_extrinsics : np.npdarray [N, 3, 4] \n            N=#frames, correspond to current_images. NeRF (RUB) convention\n\n        current_images : list of np.ndarray [H, W, 3] with len=frames\n            Show to users. NeRF's output: current_images\n\n        current_inpainted_images: list of np.ndarray [H, W, 3] with len=frames\n            Show to users. NeRF + inpaint's output: current_inpainted_images\n\n        "
        self.is_ego_motion = False
        self.add_car_all_static = True
        self.current_extrinsics = self.nerf_motion_extrinsics[3:4]
        self.current_extrinsics = self.current_extrinsics.repeat(self.frames, axis=0)
        self.removed_cars = []
        self.added_cars_dict = {}
        self.added_cars_count = 0
        self.past_operations = []
        self.all_trajectories = []
        current_time = datetime.datetime.now()
        short_scene_name = self.scene_name.lstrip('segment-')[:4]
        simulation_name = config['simulation_name']
        self.logging_name = current_time.strftime(f'{short_scene_name}_{simulation_name}_%Y_%m_%d_%H_%M_%S')
        self.save_cache = config['save_cache']
        self.cache_dir = os.path.join(config['cache_dir'], self.logging_name)
        self.output_dir = config['output_dir']
        check_and_mkdirs(self.cache_dir)
        check_and_mkdirs(self.output_dir)

    def setup_cars(self):
        """
        Call at the beginning of each interaction. 
        calculate the information of cars from original scene based on current extrinsic
        """
        original_cars_dict = {}
        name_to_bbox_car_id = {}
        bbox_car_id_to_name = {}
        mask_list = []
        mask_corners_list = []
        depth_list = []
        u_v_depth_list = []
        car_id_list = []
        for car_id in self.bbox_data.keys():
            extrinsic_for_project = transform_nerf2opencv_convention(self.current_extrinsics[0])
            u_v_depth = get_attributes_for_one_car(self.bbox_data[car_id], extrinsic_for_project, self.intrinsics)
            if u_v_depth['u'] < 0 or u_v_depth['u'] > self.width or u_v_depth['v'] < 0 or (u_v_depth['v'] > self.height):
                continue
            corners = generate_vertices(self.bbox_data[car_id])
            mask, mask_corners = get_outlines(corners, extrinsic_for_project, self.intrinsics, self.height, self.width)
            mask_list.append(mask)
            mask_corners_list.append(mask_corners)
            depth_list.append(u_v_depth['depth'])
            u_v_depth_list.append(u_v_depth)
            car_id_list.append(car_id)
        color_dict = getColorList()
        for idx_in_list, car_id in enumerate(car_id_list):
            car_name = f'original_car_{car_id}'
            name_to_bbox_car_id[car_name] = car_id
            bbox_car_id_to_name[car_id] = car_name
            original_cars_dict[car_name] = u_v_depth_list[idx_in_list]
            current_mask_corner = mask_corners_list[idx_in_list]
            color = get_color(self.current_images[0][current_mask_corner[0] + 50:current_mask_corner[1] - 50, current_mask_corner[2] + 50:current_mask_corner[3] - 50])
            color_vector = (color_dict[color][0] + color_dict[color][1]) / 2
            color_vector = np.uint8(color_vector.reshape(1, 1, 3))
            original_cars_dict[car_name]['rgb'] = cv2.cvtColor(color_vector, cv2.COLOR_HSV2RGB)
            original_cars_dict[car_name]['x'] = self.bbox_data[car_id]['cx']
            original_cars_dict[car_name]['y'] = self.bbox_data[car_id]['cy']
        self.original_cars_dict = original_cars_dict
        self.name_to_bbox_car_id = name_to_bbox_car_id
        self.bbox_car_id_to_name = bbox_car_id_to_name

    def remove_car(self, car_name):
        """
        append car_id to self.removed_cars, inpaint them later.

        car_name
        """
        self.removed_cars.append(car_name)

    def add_car(self, added_car_info):
        """
        Add a single car to self.added_cars_dict dictionary.
        added_car_id is the number of cars added so far.
        """
        added_car_info['need_placement_and_motion'] = True
        added_car_id = str(self.added_cars_count)
        car_name = f'added_car_{added_car_id}'
        self.added_cars_dict[car_name] = added_car_info
        self.added_cars_count += 1
        return car_name

    def check_added_car_static(self):
        """
        if all added cars are static, we only need to render one frame in blender
        """
        self.add_car_all_static = True
        for added_car_id, added_car_info in self.added_cars_dict.items():
            is_static = np.all(added_car_info['motion'] == added_car_info['motion'][0])
            self.add_car_all_static = self.add_car_all_static and is_static

    def clean_cache(self):
        folder_path = self.cache_dir
        shutil.rmtree(folder_path)

def check_added_car_static(self):
    """
        if all added cars are static, we only need to render one frame in blender
        """
    self.add_car_all_static = True
    for added_car_id, added_car_info in self.added_cars_dict.items():
        is_static = np.all(added_car_info['motion'] == added_car_info['motion'][0])
        self.add_car_all_static = self.add_car_all_static and is_static

def intrinsic_matrix(fx: float, fy: float, cx: float, cy: float):
    """Intrinsic matrix for a pinhole camera in OpenCV coordinate system."""
    return np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1.0]], dtype=np.float32)

class Dataset:

    def __init__(self, data_dir):
        scene_manager = NeRFSceneManager(data_dir)
        self.names, self.poses, self.pix2cam, self.params, self.camtype = scene_manager.process()
        self.cam2pix = np.linalg.inv(self.pix2cam)
        self.n_images = len(self.poses)
        sorted_image_names = sorted(deepcopy(self.names))
        sort_img_idx = []
        for i in range(self.n_images):
            sort_img_idx.append(self.names.index(sorted_image_names[i]))
        img_idx = np.array(sort_img_idx, dtype=np.int32)
        self.poses = self.poses[sort_img_idx]
        self.bounds = np.zeros([self.n_images, 2], dtype=np.float32)
        name_to_ids = scene_manager.name_to_image_id
        points3D = scene_manager.points3D
        points3D_ids = scene_manager.point3D_ids
        point3D_id_to_images = scene_manager.point3D_id_to_images
        image_id_to_image_idx = np.zeros(self.n_images + 10, dtype=np.int32)
        for image_name in self.names:
            image_id_to_image_idx[name_to_ids[image_name]] = sorted_image_names.index(image_name)
        vis_arr = []
        for pts_i in range(len(points3D)):
            cams = np.zeros([self.n_images], dtype=np.uint8)
            images_ids = point3D_id_to_images[points3D_ids[pts_i]]
            for image_info in images_ids:
                image_id = image_info[0]
                image_idx = image_id_to_image_idx[image_id]
                cams[image_idx] = 1
            vis_arr.append(cams)
        vis_arr = np.stack(vis_arr, 1)
        for img_i in range(self.n_images):
            vis = vis_arr[img_i]
            pts = points3D[vis == 1]
            c2w = np.diag([1.0, 1.0, 1.0, 1.0])
            c2w[:3, :4] = self.poses[img_i]
            w2c = np.linalg.inv(c2w)
            z_vals = (w2c[None, 2, :3] * pts).sum(-1) + w2c[None, 2, 3]
            depth = -z_vals
            near_depth, far_depth = (np.percentile(depth, 1.0), np.percentile(depth, 99.0))
            near_depth = near_depth * 0.5
            far_depth = far_depth * 5.0
            self.bounds[img_i, 0], self.bounds[img_i, 1] = (near_depth, far_depth)

        def proc(x):
            return np.ascontiguousarray(np.array(x).astype(np.float64))
        self.poses = proc(self.poses)
        self.cam2pix = proc(np.tile(self.cam2pix[None], (len(self.poses), 1, 1)))
        self.bounds = proc(self.bounds)
        if self.params is not None:
            dist_params = [self.params['k1'], self.params['k2'], self.params['p1'], self.params['p2']]
        else:
            dist_params = [0.0, 0.0, 0.0, 0.0]
        dist_params = np.tile(np.array(dist_params), len(self.poses)).reshape([len(self.poses), -1])
        self.dist_params = proc([dist_params])

    def export(self, data_dir, out_mode):
        n = len(self.poses)
        if out_mode == 'cams_meta':
            data = np.concatenate([self.poses.reshape([n, -1]), self.cam2pix.reshape([n, -1]), self.dist_params.reshape([n, -1]), self.bounds.reshape([n, -1])], axis=-1)
            data = np.ascontiguousarray(np.array(data).astype(np.float64))
            np.save(pjoin(data_dir, 'cams_meta.npy'), data)
        elif 'poses_bounds' in out_mode:
            poses = deepcopy(self.poses)
            image_list = []
            suffs = ['*.png', '*.PNG', '*.jpg', '*.JPG']
            for suff in suffs:
                image_list += glob(pjoin(data_dir, 'images', suff))
            h, w, _ = cv.imread(image_list[0]).shape
            focal = (self.cam2pix[0, 0, 0] + self.cam2pix[0, 1, 1]) * 0.5
            if out_mode == 'poses_bounds_raw':
                poses = np.concatenate([-poses[:, :, 1:2], poses[:, :, 0:1], poses[:, :, 2:]], 2)
            hwf = np.zeros([n, 3])
            hwf[:, 0] = h
            hwf[:, 1] = w
            hwf[:, 2] = focal
            bounds = self.bounds
            poses_hwf = np.concatenate([poses, hwf[:, :, None]], -1)
            data = np.concatenate([poses_hwf.reshape([n, -1]), bounds.reshape([n, -1])], -1)
            data = np.ascontiguousarray(np.array(data).astype(np.float64))
            np.save(pjoin(data_dir, '{}.npy'.format(out_mode)), data)

def __init__(self, data_dir):
    scene_manager = NeRFSceneManager(data_dir)
    self.names, self.poses, self.pix2cam, self.params, self.camtype = scene_manager.process()
    self.cam2pix = np.linalg.inv(self.pix2cam)
    self.n_images = len(self.poses)
    sorted_image_names = sorted(deepcopy(self.names))
    sort_img_idx = []
    for i in range(self.n_images):
        sort_img_idx.append(self.names.index(sorted_image_names[i]))
    img_idx = np.array(sort_img_idx, dtype=np.int32)
    self.poses = self.poses[sort_img_idx]
    self.bounds = np.zeros([self.n_images, 2], dtype=np.float32)
    name_to_ids = scene_manager.name_to_image_id
    points3D = scene_manager.points3D
    points3D_ids = scene_manager.point3D_ids
    point3D_id_to_images = scene_manager.point3D_id_to_images
    image_id_to_image_idx = np.zeros(self.n_images + 10, dtype=np.int32)
    for image_name in self.names:
        image_id_to_image_idx[name_to_ids[image_name]] = sorted_image_names.index(image_name)
    vis_arr = []
    for pts_i in range(len(points3D)):
        cams = np.zeros([self.n_images], dtype=np.uint8)
        images_ids = point3D_id_to_images[points3D_ids[pts_i]]
        for image_info in images_ids:
            image_id = image_info[0]
            image_idx = image_id_to_image_idx[image_id]
            cams[image_idx] = 1
        vis_arr.append(cams)
    vis_arr = np.stack(vis_arr, 1)
    for img_i in range(self.n_images):
        vis = vis_arr[img_i]
        pts = points3D[vis == 1]
        c2w = np.diag([1.0, 1.0, 1.0, 1.0])
        c2w[:3, :4] = self.poses[img_i]
        w2c = np.linalg.inv(c2w)
        z_vals = (w2c[None, 2, :3] * pts).sum(-1) + w2c[None, 2, 3]
        depth = -z_vals
        near_depth, far_depth = (np.percentile(depth, 1.0), np.percentile(depth, 99.0))
        near_depth = near_depth * 0.5
        far_depth = far_depth * 5.0
        self.bounds[img_i, 0], self.bounds[img_i, 1] = (near_depth, far_depth)

    def proc(x):
        return np.ascontiguousarray(np.array(x).astype(np.float64))
    self.poses = proc(self.poses)
    self.cam2pix = proc(np.tile(self.cam2pix[None], (len(self.poses), 1, 1)))
    self.bounds = proc(self.bounds)
    if self.params is not None:
        dist_params = [self.params['k1'], self.params['k2'], self.params['p1'], self.params['p2']]
    else:
        dist_params = [0.0, 0.0, 0.0, 0.0]
    dist_params = np.tile(np.array(dist_params), len(self.poses)).reshape([len(self.poses), -1])
    self.dist_params = proc([dist_params])

def proc(x):
    return np.ascontiguousarray(np.array(x).astype(np.float64))

class Camera:

    @staticmethod
    def GetNumParams(type_):
        if type_ == 0 or type_ == 'SIMPLE_PINHOLE':
            return 3
        if type_ == 1 or type_ == 'PINHOLE':
            return 4
        if type_ == 2 or type_ == 'SIMPLE_RADIAL':
            return 4
        if type_ == 3 or type_ == 'RADIAL':
            return 5
        if type_ == 4 or type_ == 'OPENCV':
            return 8
        raise Exception('Camera type not supported')

    @staticmethod
    def GetNameFromType(type_):
        if type_ == 0:
            return 'SIMPLE_PINHOLE'
        if type_ == 1:
            return 'PINHOLE'
        if type_ == 2:
            return 'SIMPLE_RADIAL'
        if type_ == 3:
            return 'RADIAL'
        if type_ == 4:
            return 'OPENCV'
        raise Exception('Camera type not supported')

    def __init__(self, type_, width_, height_, params):
        self.width = width_
        self.height = height_
        if type_ == 0 or type_ == 'SIMPLE_PINHOLE':
            self.fx, self.cx, self.cy = params
            self.fy = self.fx
            self.distortion_func = None
            self.camera_type = 0
        elif type_ == 1 or type_ == 'PINHOLE':
            self.fx, self.fy, self.cx, self.cy = params
            self.distortion_func = None
            self.camera_type = 1
        elif type_ == 2 or type_ == 'SIMPLE_RADIAL':
            self.fx, self.cx, self.cy, self.k1 = params
            self.fy = self.fx
            self.distortion_func = simple_radial_distortion
            self.camera_type = 2
        elif type_ == 3 or type_ == 'RADIAL':
            self.fx, self.cx, self.cy, self.k1, self.k2 = params
            self.fy = self.fx
            self.distortion_func = radial_distortion
            self.camera_type = 3
        elif type_ == 4 or type_ == 'OPENCV':
            self.fx, self.fy, self.cx, self.cy = params[:4]
            self.k1, self.k2, self.p1, self.p2 = params[4:]
            self.distortion_func = opencv_distortion
            self.camera_type = 4
        else:
            raise Exception('Camera type not supported')

    def __str__(self):
        s = self.GetNameFromType(self.camera_type) + ' {} {} {}'.format(self.width, self.height, self.fx)
        if self.camera_type in (1, 4):
            s += ' {}'.format(self.fy)
        s += ' {} {}'.format(self.cx, self.cy)
        if self.camera_type == 2:
            s += ' {}'.format(self.k1)
        elif self.camera_type == 3:
            s += ' {} {}'.format(self.k1, self.k2)
        elif self.camera_type == 4:
            s += ' {} {} {} {}'.format(self.k1, self.k2, self.p1, self.p2)
        return s

    def get_params(self):
        if self.camera_type == 0:
            return np.array((self.fx, self.cx, self.cy))
        if self.camera_type == 1:
            return np.array((self.fx, self.fy, self.cx, self.cy))
        if self.camera_type == 2:
            return np.array((self.fx, self.cx, self.cy, self.k1))
        if self.camera_type == 3:
            return np.array((self.fx, self.cx, self.cy, self.k1, self.k2))
        if self.camera_type == 4:
            return np.array((self.fx, self.fy, self.cx, self.cy, self.k1, self.k2, self.p1, self.p2))

    def get_camera_matrix(self):
        return np.array(((self.fx, 0, self.cx), (0, self.fy, self.cy), (0, 0, 1)))

    def get_inverse_camera_matrix(self):
        return np.array(((1.0 / self.fx, 0, -self.cx / self.fx), (0, 1.0 / self.fy, -self.cy / self.fy), (0, 0, 1)))

    @property
    def K(self):
        return self.get_camera_matrix()

    @property
    def K_inv(self):
        return self.get_inverse_camera_matrix()

    def get_inv_camera_matrix(self):
        inv_fx, inv_fy = (1.0 / self.fx, 1.0 / self.fy)
        return np.array(((inv_fx, 0, -inv_fx * self.cx), (0, inv_fy, -inv_fy * self.cy), (0, 0, 1)))

    def get_image_grid(self):
        xmin = (0.5 - self.cx) / self.fx
        xmax = (self.width - 0.5 - self.cx) / self.fx
        ymin = (0.5 - self.cy) / self.fy
        ymax = (self.height - 0.5 - self.cy) / self.fy
        return np.meshgrid(np.linspace(xmin, xmax, self.width), np.linspace(ymin, ymax, self.height))

    def distort_points(self, x, normalized=True, denormalize=True):
        x = np.atleast_2d(x)
        if not normalized:
            x -= np.array([[self.cx, self.cy]])
            x /= np.array([[self.fx, self.fy]])
        if self.distortion_func is not None:
            x = self.distortion_func(self, x)
        if denormalize:
            x *= np.array([[self.fx, self.fy]])
            x += np.array([[self.cx, self.cy]])
        return x

    def undistort_points(self, x, normalized=False, denormalize=True):
        x = np.atleast_2d(x)
        if not normalized:
            x = x - np.array([self.cx, self.cy])
            x /= np.array([self.fx, self.fy])
        if self.distortion_func is not None:

            def objective(xu):
                return (x - self.distortion_func(self, xu.reshape(*x.shape))).ravel()
            xu = root(objective, x).x.reshape(*x.shape)
        else:
            xu = x
        if denormalize:
            xu *= np.array([[self.fx, self.fy]])
            xu += np.array([[self.cx, self.cy]])
        return xu

def get_params(self):
    if self.camera_type == 0:
        return np.array((self.fx, self.cx, self.cy))
    if self.camera_type == 1:
        return np.array((self.fx, self.fy, self.cx, self.cy))
    if self.camera_type == 2:
        return np.array((self.fx, self.cx, self.cy, self.k1))
    if self.camera_type == 3:
        return np.array((self.fx, self.cx, self.cy, self.k1, self.k2))
    if self.camera_type == 4:
        return np.array((self.fx, self.fy, self.cx, self.cy, self.k1, self.k2, self.p1, self.p2))

def get_camera_matrix(self):
    return np.array(((self.fx, 0, self.cx), (0, self.fy, self.cy), (0, 0, 1)))

def get_inverse_camera_matrix(self):
    return np.array(((1.0 / self.fx, 0, -self.cx / self.fx), (0, 1.0 / self.fy, -self.cy / self.fy), (0, 0, 1)))

@property
def K(self):
    return self.get_camera_matrix()

def get_inv_camera_matrix(self):
    inv_fx, inv_fy = (1.0 / self.fx, 1.0 / self.fy)
    return np.array(((inv_fx, 0, -inv_fx * self.cx), (0, inv_fy, -inv_fy * self.cy), (0, 0, 1)))

def distort_points(self, x, normalized=True, denormalize=True):
    x = np.atleast_2d(x)
    if not normalized:
        x -= np.array([[self.cx, self.cy]])
        x /= np.array([[self.fx, self.fy]])
    if self.distortion_func is not None:
        x = self.distortion_func(self, x)
    if denormalize:
        x *= np.array([[self.fx, self.fy]])
        x += np.array([[self.cx, self.cy]])
    return x

def undistort_points(self, x, normalized=False, denormalize=True):
    x = np.atleast_2d(x)
    if not normalized:
        x = x - np.array([self.cx, self.cy])
        x /= np.array([self.fx, self.fy])
    if self.distortion_func is not None:

        def objective(xu):
            return (x - self.distortion_func(self, xu.reshape(*x.shape))).ravel()
        xu = root(objective, x).x.reshape(*x.shape)
    else:
        xu = x
    if denormalize:
        xu *= np.array([[self.fx, self.fy]])
        xu += np.array([[self.cx, self.cy]])
    return xu

def objective(xu):
    return (x - self.distortion_func(self, xu.reshape(*x.shape))).ravel()

def add_camera(db, model, width, height, params, prior_focal_length=False, camera_id=None):
    params = np.asarray(params, np.float64)
    db.execute('INSERT INTO cameras VALUES (?, ?, ?, ?, ?, ?)', (camera_id, model, width, height, array_to_blob(params), prior_focal_length))

def add_descriptors(db, image_id, descriptors):
    descriptors = np.ascontiguousarray(descriptors, np.uint8)
    db.execute('INSERT INTO descriptors VALUES (?, ?, ?, ?)', (image_id,) + descriptors.shape + (array_to_blob(descriptors),))

def add_image(db, name, camera_id, prior_q=np.zeros(4), prior_t=np.zeros(3), image_id=None):
    db.execute('INSERT INTO images VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (image_id, name, camera_id, prior_q[0], prior_q[1], prior_q[2], prior_q[3], prior_t[0], prior_t[1], prior_t[2]))

def add_inlier_matches(db, image_id1, image_id2, matches, config=2, F=None, E=None, H=None):
    assert len(matches.shape) == 2
    assert matches.shape[1] == 2
    if image_id1 > image_id2:
        matches = matches[:, ::-1]
    if F is not None:
        F = np.asarray(F, np.float64)
    if E is not None:
        E = np.asarray(E, np.float64)
    if H is not None:
        H = np.asarray(H, np.float64)
    pair_id = get_pair_id(image_id1, image_id2)
    matches = np.asarray(matches, np.uint32)
    db.execute('INSERT INTO inlier_matches VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (pair_id,) + matches.shape + (array_to_blob(matches), config, F, E, H))

def add_keypoints(db, image_id, keypoints):
    assert len(keypoints.shape) == 2
    assert keypoints.shape[1] in [2, 4, 6]
    keypoints = np.asarray(keypoints, np.float32)
    db.execute('INSERT INTO keypoints VALUES (?, ?, ?, ?)', (image_id,) + keypoints.shape + (array_to_blob(keypoints),))

def add_matches(db, image_id1, image_id2, matches):
    assert len(matches.shape) == 2
    assert matches.shape[1] == 2
    if image_id1 > image_id2:
        matches = matches[:, ::-1]
    pair_id = get_pair_id(image_id1, image_id2)
    matches = np.asarray(matches, np.uint32)
    db.execute('INSERT INTO matches VALUES (?, ?, ?, ?)', (pair_id,) + matches.shape + (array_to_blob(matches),))

class COLMAPDatabase(sqlite3.Connection):

    @staticmethod
    def connect(database_path):
        return sqlite3.connect(database_path, factory=COLMAPDatabase)

    def __init__(self, *args, **kwargs):
        super(COLMAPDatabase, self).__init__(*args, **kwargs)
        self.initialize_tables = lambda: self.executescript(CREATE_ALL)
        self.initialize_cameras = lambda: self.executescript(CREATE_CAMERAS_TABLE)
        self.initialize_descriptors = lambda: self.executescript(CREATE_DESCRIPTORS_TABLE)
        self.initialize_images = lambda: self.executescript(CREATE_IMAGES_TABLE)
        self.initialize_inlier_matches = lambda: self.executescript(CREATE_INLIER_MATCHES_TABLE)
        self.initialize_keypoints = lambda: self.executescript(CREATE_KEYPOINTS_TABLE)
        self.initialize_matches = lambda: self.executescript(CREATE_MATCHES_TABLE)
        self.create_name_index = lambda: self.executescript(CREATE_NAME_INDEX)
    add_camera = add_camera
    add_descriptors = add_descriptors
    add_image = add_image
    add_inlier_matches = add_inlier_matches
    add_keypoints = add_keypoints
    add_matches = add_matches

@staticmethod
def connect(database_path):
    return sqlite3.connect(database_path, factory=COLMAPDatabase)

def main(args):
    import os
    if os.path.exists(args.database_path):
        print('Error: database path already exists -- will not modify it.')
        exit()
    db = COLMAPDatabase.connect(args.database_path)
    db.initialize_tables()
    model1, w1, h1, params1 = (0, 1024, 768, np.array((1024.0, 512.0, 384.0)))
    model2, w2, h2, params2 = (2, 1024, 768, np.array((1024.0, 512.0, 384.0, 0.1)))
    db.add_camera(model1, w1, h1, params1)
    db.add_camera(model2, w2, h2, params2)
    db.add_image('image1.png', 0)
    db.add_image('image2.png', 0)
    db.add_image('image3.png', 2)
    db.add_image('image4.png', 2)
    N = 1000
    kp1 = np.random.rand(N, 2) * (1024.0, 768.0)
    kp2 = np.random.rand(N, 2) * (1024.0, 768.0)
    kp3 = np.random.rand(N, 2) * (1024.0, 768.0)
    kp4 = np.random.rand(N, 2) * (1024.0, 768.0)
    db.add_keypoints(1, kp1)
    db.add_keypoints(2, kp2)
    db.add_keypoints(3, kp3)
    db.add_keypoints(4, kp4)
    M = 50
    m12 = np.random.randint(N, size=(M, 2))
    m23 = np.random.randint(N, size=(M, 2))
    m34 = np.random.randint(N, size=(M, 2))
    db.add_matches(1, 2, m12)
    db.add_matches(2, 3, m23)
    db.add_matches(3, 4, m34)
    rows = db.execute('SELECT * FROM cameras')
    camera_id, model, width, height, params, prior = next(rows)
    params = blob_to_array(params, np.float32)
    assert model == model1 and width == w1 and (height == h1)
    assert np.allclose(params, params1)
    camera_id, model, width, height, params, prior = next(rows)
    params = blob_to_array(params, np.float32)
    assert model == model2 and width == w2 and (height == h2)
    assert np.allclose(params, params2)
    kps = dict(((image_id, blob_to_array(data, np.float32, (-1, 2))) for image_id, data in db.execute('SELECT image_id, data FROM keypoints')))
    assert np.allclose(kps[1], kp1)
    assert np.allclose(kps[2], kp2)
    assert np.allclose(kps[3], kp3)
    assert np.allclose(kps[4], kp4)
    pair_ids = [get_pair_id(*pair) for pair in [(1, 2), (2, 3), (3, 4)]]
    matches = dict(((get_image_ids_from_pair_id(pair_id), blob_to_array(data, np.uint32, (-1, 2))) for pair_id, data in db.execute('SELECT pair_id, data FROM matches')))
    assert np.all(matches[1, 2] == m12)
    assert np.all(matches[2, 3] == m23)
    assert np.all(matches[3, 4] == m34)
    db.close()
    os.remove(args.database_path)

class SceneManager:
    INVALID_POINT3D = np.uint64(-1)

    def __init__(self, colmap_results_folder, image_path=None):
        self.folder = colmap_results_folder
        if not self.folder.endswith('/'):
            self.folder += '/'
        self.image_path = None
        self.load_colmap_project_file(image_path=image_path)
        self.cameras = OrderedDict()
        self.images = OrderedDict()
        self.name_to_image_id = dict()
        self.last_camera_id = 0
        self.last_image_id = 0
        self.points3D = np.zeros((0, 3))
        self.point3D_ids = np.empty(0)
        self.point3D_id_to_point3D_idx = dict()
        self.point3D_id_to_images = dict()
        self.point3D_colors = np.zeros((0, 3), dtype=np.uint8)
        self.point3D_errors = np.zeros(0)

    def load_colmap_project_file(self, project_file=None, image_path=None):
        if project_file is None:
            project_file = self.folder + 'project.ini'
        self.image_path = image_path
        if self.image_path is None:
            try:
                with open(project_file, 'r') as f:
                    for line in iter(f.readline, ''):
                        if line.startswith('image_path'):
                            self.image_path = line[11:].strip()
                            break
            except:
                pass
        if self.image_path is None:
            print('Warning: image_path not found for reconstruction')
        elif not self.image_path.endswith('/'):
            self.image_path += '/'

    def load(self):
        self.load_cameras()
        self.load_images()
        self.load_points3D()

    def load_cameras(self, input_file=None):
        if input_file is None:
            input_file = self.folder + 'cameras.bin'
            if os.path.exists(input_file):
                self._load_cameras_bin(input_file)
            else:
                input_file = self.folder + 'cameras.txt'
                if os.path.exists(input_file):
                    self._load_cameras_txt(input_file)
                else:
                    raise IOError('no cameras file found')

    def _load_cameras_bin(self, input_file):
        self.cameras = OrderedDict()
        with open(input_file, 'rb') as f:
            num_cameras = struct.unpack('L', f.read(8))[0]
            for _ in range(num_cameras):
                camera_id, camera_type, w, h = struct.unpack('IiLL', f.read(24))
                num_params = Camera.GetNumParams(camera_type)
                params = struct.unpack('d' * num_params, f.read(8 * num_params))
                self.cameras[camera_id] = Camera(camera_type, w, h, params)
                self.last_camera_id = max(self.last_camera_id, camera_id)

    def _load_cameras_txt(self, input_file):
        self.cameras = OrderedDict()
        with open(input_file, 'r') as f:
            for line in iter(lambda: f.readline().strip(), ''):
                if not line or line.startswith('#'):
                    continue
                data = line.split()
                camera_id = int(data[0])
                self.cameras[camera_id] = Camera(data[1], int(data[2]), int(data[3]), map(float, data[4:]))
                self.last_camera_id = max(self.last_camera_id, camera_id)

    def load_images(self, input_file=None):
        if input_file is None:
            input_file = self.folder + 'images.bin'
            if os.path.exists(input_file):
                self._load_images_bin(input_file)
            else:
                input_file = self.folder + 'images.txt'
                if os.path.exists(input_file):
                    self._load_images_txt(input_file)
                else:
                    raise IOError('no images file found')

    def _load_images_bin(self, input_file):
        self.images = OrderedDict()
        with open(input_file, 'rb') as f:
            num_images = struct.unpack('L', f.read(8))[0]
            image_struct = struct.Struct('<I 4d 3d I')
            for _ in range(num_images):
                data = image_struct.unpack(f.read(image_struct.size))
                image_id = data[0]
                q = Quaternion(np.array(data[1:5]))
                t = np.array(data[5:8])
                camera_id = data[8]
                name = b''.join((c for c in iter(lambda: f.read(1), b'\x00'))).decode()
                image = Image(name, camera_id, q, t)
                num_points2D = struct.unpack('Q', f.read(8))[0]
                points_array = array.array('d')
                points_array.fromfile(f, 3 * num_points2D)
                points_elements = np.array(points_array).reshape((num_points2D, 3))
                image.points2D = points_elements[:, :2]
                ids_array = array.array('Q')
                ids_array.frombytes(points_elements[:, 2].tobytes())
                image.point3D_ids = np.array(ids_array, dtype=np.uint64).reshape((num_points2D,))
                self.images[image_id] = image
                self.name_to_image_id[image.name] = image_id
                self.last_image_id = max(self.last_image_id, image_id)

    def _load_images_txt(self, input_file):
        self.images = OrderedDict()
        with open(input_file, 'r') as f:
            is_camera_description_line = False
            for line in iter(lambda: f.readline().strip(), ''):
                if not line or line.startswith('#'):
                    continue
                is_camera_description_line = not is_camera_description_line
                data = line.split()
                if is_camera_description_line:
                    image_id = int(data[0])
                    image = Image(data[-1], int(data[-2]), Quaternion(np.array(map(float, data[1:5]))), np.array(map(float, data[5:8])))
                else:
                    image.points2D = np.array([map(float, data[::3]), map(float, data[1::3])]).T
                    image.point3D_ids = np.array(map(np.uint64, data[2::3]))
                    self.images[image_id] = image
                    self.name_to_image_id[image.name] = image_id
                    self.last_image_id = max(self.last_image_id, image_id)

    def load_points3D(self, input_file=None):
        if input_file is None:
            input_file = self.folder + 'points3D.bin'
            if os.path.exists(input_file):
                self._load_points3D_bin(input_file)
            else:
                input_file = self.folder + 'points3D.txt'
                if os.path.exists(input_file):
                    self._load_points3D_txt(input_file)
                else:
                    raise IOError('no points3D file found')

    def _load_points3D_bin(self, input_file):
        with open(input_file, 'rb') as f:
            num_points3D = struct.unpack('L', f.read(8))[0]
            self.points3D = np.empty((num_points3D, 3))
            self.point3D_ids = np.empty(num_points3D, dtype=np.uint64)
            self.point3D_colors = np.empty((num_points3D, 3), dtype=np.uint8)
            self.point3D_id_to_point3D_idx = dict()
            self.point3D_id_to_images = dict()
            self.point3D_errors = np.empty(num_points3D)
            data_struct = struct.Struct('<Q 3d 3B d Q')
            for i in range(num_points3D):
                data = data_struct.unpack(f.read(data_struct.size))
                self.point3D_ids[i] = data[0]
                self.points3D[i] = data[1:4]
                self.point3D_colors[i] = data[4:7]
                self.point3D_errors[i] = data[7]
                track_len = data[8]
                self.point3D_id_to_point3D_idx[self.point3D_ids[i]] = i
                data = struct.unpack(f'{2 * track_len}I', f.read(2 * track_len * 4))
                self.point3D_id_to_images[self.point3D_ids[i]] = np.array(data, dtype=np.uint32).reshape(track_len, 2)

    def _load_points3D_txt(self, input_file):
        self.points3D = []
        self.point3D_ids = []
        self.point3D_colors = []
        self.point3D_id_to_point3D_idx = dict()
        self.point3D_id_to_images = dict()
        self.point3D_errors = []
        with open(input_file, 'r') as f:
            for line in iter(lambda: f.readline().strip(), ''):
                if not line or line.startswith('#'):
                    continue
                data = line.split()
                point3D_id = np.uint64(data[0])
                self.point3D_ids.append(point3D_id)
                self.point3D_id_to_point3D_idx[point3D_id] = len(self.points3D)
                self.points3D.append(map(np.float64, data[1:4]))
                self.point3D_colors.append(map(np.uint8, data[4:7]))
                self.point3D_errors.append(np.float64(data[7]))
                self.point3D_id_to_images[point3D_id] = np.array(map(np.uint32, data[8:])).reshape(-1, 2)
        self.points3D = np.array(self.points3D)
        self.point3D_ids = np.array(self.point3D_ids)
        self.point3D_colors = np.array(self.point3D_colors)
        self.point3D_errors = np.array(self.point3D_errors)

    def save(self, output_folder, binary=True):
        self.save_cameras(output_folder, binary=binary)
        self.save_images(output_folder, binary=binary)
        self.save_points3D(output_folder, binary=binary)

    def save_cameras(self, output_folder, output_file=None, binary=True):
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        if output_file is None:
            output_file = 'cameras.bin' if binary else 'cameras.txt'
        output_file = os.path.join(output_folder, output_file)
        if binary:
            self._save_cameras_bin(output_file)
        else:
            self._save_cameras_txt(output_file)

    def _save_cameras_bin(self, output_file):
        with open(output_file, 'wb') as fid:
            fid.write(struct.pack('L', len(self.cameras)))
            camera_struct = struct.Struct('IiLL')
            for camera_id, camera in sorted(self.cameras.iteritems()):
                fid.write(camera_struct.pack(camera_id, camera.camera_type, camera.width, camera.height))
                fid.write(camera.get_params().tobytes())

    def _save_cameras_txt(self, output_file):
        with open(output_file, 'w') as fid:
            (print >> fid, '# Camera list with one line of data per camera:')
            (print >> fid, '#   CAMERA_ID, MODEL, WIDTH, HEIGHT, PARAMS[]')
            (print >> fid, '# Number of cameras:', len(self.cameras))
            for camera_id, camera in sorted(self.cameras.iteritems()):
                (print >> fid, camera_id, camera)

    def save_images(self, output_folder, output_file=None, binary=True):
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        if output_file is None:
            output_file = 'images.bin' if binary else 'images.txt'
        output_file = os.path.join(output_folder, output_file)
        if binary:
            self._save_images_bin(output_file)
        else:
            self._save_images_txt(output_file)

    def _save_images_bin(self, output_file):
        with open(output_file, 'wb') as fid:
            fid.write(struct.pack('L', len(self.images)))
            for image_id, image in self.images.iteritems():
                fid.write(struct.pack('I', image_id))
                fid.write(image.q.q.tobytes())
                fid.write(image.tvec.tobytes())
                fid.write(struct.pack('I', image.camera_id))
                fid.write(image.name + '\x00')
                fid.write(struct.pack('L', len(image.points2D)))
                data = np.rec.fromarrays((image.points2D[:, 0], image.points2D[:, 1], image.point3D_ids))
                fid.write(data.tobytes())

    def _save_images_txt(self, output_file):
        with open(output_file, 'w') as fid:
            (print >> fid, '# Image list with two lines of data per image:')
            (print >> fid, '#   IMAGE_ID, QW, QX, QY, QZ, TX, TY, TZ, CAMERA_ID, NAME')
            (print >> fid, '#   POINTS2D[] as (X, Y, POINT3D_ID)')
            (print >> fid, '# Number of images: {},'.format(len(self.images)))
            (print >> fid, 'mean observations per image: unknown')
            for image_id, image in self.images.iteritems():
                (print >> fid, image_id)
                (print >> fid, ' '.join((str(qi) for qi in image.q.q)))
                (print >> fid, ' '.join((str(ti) for ti in image.tvec)))
                (print >> fid, image.camera_id, image.name)
                data = np.rec.fromarrays((image.points2D[:, 0], image.points2D[:, 1], image.point3D_ids.astype(np.int64)))
                if len(data) > 0:
                    np.savetxt(fid, data, '%.2f %.2f %d', newline=' ')
                    fid.seek(-1, os.SEEK_CUR)
                fid.write('\n')

    def save_points3D(self, output_folder, output_file=None, binary=True):
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        if output_file is None:
            output_file = 'points3D.bin' if binary else 'points3D.txt'
        output_file = os.path.join(output_folder, output_file)
        if binary:
            self._save_points3D_bin(output_file)
        else:
            self._save_points3D_txt(output_file)

    def _save_points3D_bin(self, output_file):
        num_valid_points3D = sum((1 for point3D_idx in self.point3D_id_to_point3D_idx.itervalues() if point3D_idx != SceneManager.INVALID_POINT3D))
        iter_point3D_id_to_point3D_idx = self.point3D_id_to_point3D_idx.iteritems()
        with open(output_file, 'wb') as fid:
            fid.write(struct.pack('L', num_valid_points3D))
            for point3D_id, point3D_idx in iter_point3D_id_to_point3D_idx:
                if point3D_idx == SceneManager.INVALID_POINT3D:
                    continue
                fid.write(struct.pack('L', point3D_id))
                fid.write(self.points3D[point3D_idx].tobytes())
                fid.write(self.point3D_colors[point3D_idx].tobytes())
                fid.write(self.point3D_errors[point3D_idx].tobytes())
                fid.write(struct.pack('L', len(self.point3D_id_to_images[point3D_id])))
                fid.write(self.point3D_id_to_images[point3D_id].tobytes())

    def _save_points3D_txt(self, output_file):
        num_valid_points3D = sum((1 for point3D_idx in self.point3D_id_to_point3D_idx.itervalues() if point3D_idx != SceneManager.INVALID_POINT3D))
        array_to_string = lambda arr: ' '.join((str(x) for x in arr))
        iter_point3D_id_to_point3D_idx = self.point3D_id_to_point3D_idx.iteritems()
        with open(output_file, 'w') as fid:
            (print >> fid, '# 3D point list with one line of data per point:')
            (print >> fid, '#   POINT3D_ID, X, Y, Z, R, G, B, ERROR, TRACK[] as ')
            (print >> fid, '(IMAGE_ID, POINT2D_IDX)')
            (print >> fid, '# Number of points: {},'.format(num_valid_points3D))
            (print >> fid, 'mean track length: unknown')
            for point3D_id, point3D_idx in iter_point3D_id_to_point3D_idx:
                if point3D_idx == SceneManager.INVALID_POINT3D:
                    continue
                (print >> fid, point3D_id)
                (print >> fid, array_to_string(self.points3D[point3D_idx]))
                (print >> fid, array_to_string(self.point3D_colors[point3D_idx]))
                (print >> fid, self.point3D_errors[point3D_idx])
                (print >> fid, array_to_string(self.point3D_id_to_images[point3D_id].flat))

    def get_image_from_name(self, image_name):
        image_id = self.name_to_image_id[image_name]
        return (image_id, self.images[image_id])

    def get_camera(self, camera_id):
        return self.cameras[camera_id]

    def get_points3D(self, image_id, return_points2D=True, return_colors=False):
        image = self.images[image_id]
        mask = image.point3D_ids != SceneManager.INVALID_POINT3D
        point3D_idxs = np.array([self.point3D_id_to_point3D_idx[point3D_id] for point3D_id in image.point3D_ids[mask]])
        filter_mask = point3D_idxs != SceneManager.INVALID_POINT3D
        point3D_idxs = point3D_idxs[filter_mask]
        result = [self.points3D[point3D_idxs, :]]
        if return_points2D:
            mask[mask] &= filter_mask
            result += [image.points2D[mask]]
        if return_colors:
            result += [self.point3D_colors[point3D_idxs, :]]
        return result if len(result) > 1 else result[0]

    def point3D_valid(self, point3D_id):
        return self.point3D_id_to_point3D_idx[point3D_id] != SceneManager.INVALID_POINT3D

    def get_filtered_points3D(self, return_colors=False):
        point3D_idxs = [idx for idx in self.point3D_id_to_point3D_idx.values() if idx != SceneManager.INVALID_POINT3D]
        result = [self.points3D[point3D_idxs, :]]
        if return_colors:
            result += [self.point3D_colors[point3D_idxs, :]]
        return result if len(result) > 1 else result[0]

    def get_shared_points3D(self, image_id1, image_id2):
        point3D_ids = set(self.images[image_id1].point3D_ids) & set(self.images[image_id2].point3D_ids)
        point3D_ids.discard(SceneManager.INVALID_POINT3D)
        point3D_idxs = np.array([self.point3D_id_to_point3D_idx[point3D_id] for point3D_id in point3D_ids])
        return self.points3D[point3D_idxs, :]

    def get_viewed_points(self, image_id):
        image = self.images[image_id]
        point3D_idxs = set(self.point3D_id_to_point3D_idx.itervalues())
        point3D_idxs.discard(SceneManager.INVALID_POINT3D)
        point3D_idxs = list(point3D_idxs)
        points3D = self.points3D[point3D_idxs, :]
        R = image.q.ToR()
        points3D = points3D.dot(R.T) + image.tvec[np.newaxis, :]
        points3D = points3D[points3D[:, 2] > 0, :]
        camera = self.cameras[image.camera_id]
        points2D = points3D.dot(camera.get_camera_matrix().T)
        points2D = points2D[:, :2] / points2D[:, 2][:, np.newaxis]
        mask = (points2D[:, 0] >= 0) & (points2D[:, 1] >= 0) & (points2D[:, 0] < camera.width - 1) & (points2D[:, 1] < camera.height - 1)
        return (points2D[mask, :], points3D[mask, :])

    def add_camera(self, camera):
        self.last_camera_id += 1
        self.cameras[self.last_camera_id] = camera
        return self.last_camera_id

    def add_image(self, image):
        self.last_image_id += 1
        self.images[self.last_image_id] = image
        return self.last_image_id

    def delete_images(self, image_list):
        for image_id in image_list:
            if image_id in self.images:
                del self.images[image_id]
        keep_set = set(self.images.iterkeys())
        iter_point3D_id_to_point3D_idx = self.point3D_id_to_point3D_idx.iteritems()
        for point3D_id, point3D_idx in iter_point3D_id_to_point3D_idx:
            if point3D_idx == SceneManager.INVALID_POINT3D:
                continue
            mask = np.array([image_id in keep_set for image_id in self.point3D_id_to_images[point3D_id][:, 0]])
            if np.any(mask):
                self.point3D_id_to_images[point3D_id] = self.point3D_id_to_images[point3D_id][mask]
            else:
                self.point3D_id_to_point3D_idx[point3D_id] = SceneManager.INVALID_POINT3D

    def filter_points3D(self, min_track_len=0, max_error=np.inf, min_tri_angle=0, max_tri_angle=180, image_set=set()):
        image_set = set(image_set)
        check_triangulation_angles = min_tri_angle > 0 or max_tri_angle < 180
        if check_triangulation_angles:
            max_tri_prod = np.cos(np.radians(min_tri_angle))
            min_tri_prod = np.cos(np.radians(max_tri_angle))
        iter_point3D_id_to_point3D_idx = self.point3D_id_to_point3D_idx.iteritems()
        image_ids = []
        for point3D_id, point3D_idx in iter_point3D_id_to_point3D_idx:
            if point3D_idx == SceneManager.INVALID_POINT3D:
                continue
            if image_set or min_track_len > 0:
                image_ids = set(self.point3D_id_to_images[point3D_id][:, 0])
            if len(image_ids) < min_track_len or self.point3D_errors[point3D_idx] > max_error or (image_set and image_set.isdisjoint(image_ids)):
                self.point3D_id_to_point3D_idx[point3D_id] = SceneManager.INVALID_POINT3D
            elif check_triangulation_angles:
                xyz = self.points3D[point3D_idx, :]
                tvecs = np.array([self.images[image_id].tvec - xyz for image_id in image_ids])
                tvecs /= np.linalg.norm(tvecs, axis=-1)[:, np.newaxis]
                cos_theta = np.array([u.dot(v) for u, v in combinations(tvecs, 2)])
                if np.min(cos_theta) > max_tri_prod or np.max(cos_theta) < min_tri_prod:
                    self.point3D_id_to_point3D_idx[point3D_id] = SceneManager.INVALID_POINT3D
        for image in self.images.itervalues():
            mask = np.array([self.point3D_id_to_point3D_idx.get(point3D_id, 0) == SceneManager.INVALID_POINT3D for point3D_id in image.point3D_ids])
            image.point3D_ids[mask] = SceneManager.INVALID_POINT3D

    def build_scene_graph(self):
        self.scene_graph = defaultdict(lambda: defaultdict(int))
        point3D_iter = self.point3D_id_to_images.iteritems()
        for i, (point3D_id, images) in enumerate(point3D_iter):
            if not self.point3D_valid(point3D_id):
                continue
            for image_id1, image_id2 in combinations(images[:, 0], 2):
                self.scene_graph[image_id1][image_id2] += 1
                self.scene_graph[image_id2][image_id1] += 1

def get_points3D(self, image_id, return_points2D=True, return_colors=False):
    image = self.images[image_id]
    mask = image.point3D_ids != SceneManager.INVALID_POINT3D
    point3D_idxs = np.array([self.point3D_id_to_point3D_idx[point3D_id] for point3D_id in image.point3D_ids[mask]])
    filter_mask = point3D_idxs != SceneManager.INVALID_POINT3D
    point3D_idxs = point3D_idxs[filter_mask]
    result = [self.points3D[point3D_idxs, :]]
    if return_points2D:
        mask[mask] &= filter_mask
        result += [image.points2D[mask]]
    if return_colors:
        result += [self.point3D_colors[point3D_idxs, :]]
    return result if len(result) > 1 else result[0]

def get_shared_points3D(self, image_id1, image_id2):
    point3D_ids = set(self.images[image_id1].point3D_ids) & set(self.images[image_id2].point3D_ids)
    point3D_ids.discard(SceneManager.INVALID_POINT3D)
    point3D_idxs = np.array([self.point3D_id_to_point3D_idx[point3D_id] for point3D_id in point3D_ids])
    return self.points3D[point3D_idxs, :]

def get_viewed_points(self, image_id):
    image = self.images[image_id]
    point3D_idxs = set(self.point3D_id_to_point3D_idx.itervalues())
    point3D_idxs.discard(SceneManager.INVALID_POINT3D)
    point3D_idxs = list(point3D_idxs)
    points3D = self.points3D[point3D_idxs, :]
    R = image.q.ToR()
    points3D = points3D.dot(R.T) + image.tvec[np.newaxis, :]
    points3D = points3D[points3D[:, 2] > 0, :]
    camera = self.cameras[image.camera_id]
    points2D = points3D.dot(camera.get_camera_matrix().T)
    points2D = points2D[:, :2] / points2D[:, 2][:, np.newaxis]
    mask = (points2D[:, 0] >= 0) & (points2D[:, 1] >= 0) & (points2D[:, 0] < camera.width - 1) & (points2D[:, 1] < camera.height - 1)
    return (points2D[mask, :], points3D[mask, :])

def delete_images(self, image_list):
    for image_id in image_list:
        if image_id in self.images:
            del self.images[image_id]
    keep_set = set(self.images.iterkeys())
    iter_point3D_id_to_point3D_idx = self.point3D_id_to_point3D_idx.iteritems()
    for point3D_id, point3D_idx in iter_point3D_id_to_point3D_idx:
        if point3D_idx == SceneManager.INVALID_POINT3D:
            continue
        mask = np.array([image_id in keep_set for image_id in self.point3D_id_to_images[point3D_id][:, 0]])
        if np.any(mask):
            self.point3D_id_to_images[point3D_id] = self.point3D_id_to_images[point3D_id][mask]
        else:
            self.point3D_id_to_point3D_idx[point3D_id] = SceneManager.INVALID_POINT3D

def filter_points3D(self, min_track_len=0, max_error=np.inf, min_tri_angle=0, max_tri_angle=180, image_set=set()):
    image_set = set(image_set)
    check_triangulation_angles = min_tri_angle > 0 or max_tri_angle < 180
    if check_triangulation_angles:
        max_tri_prod = np.cos(np.radians(min_tri_angle))
        min_tri_prod = np.cos(np.radians(max_tri_angle))
    iter_point3D_id_to_point3D_idx = self.point3D_id_to_point3D_idx.iteritems()
    image_ids = []
    for point3D_id, point3D_idx in iter_point3D_id_to_point3D_idx:
        if point3D_idx == SceneManager.INVALID_POINT3D:
            continue
        if image_set or min_track_len > 0:
            image_ids = set(self.point3D_id_to_images[point3D_id][:, 0])
        if len(image_ids) < min_track_len or self.point3D_errors[point3D_idx] > max_error or (image_set and image_set.isdisjoint(image_ids)):
            self.point3D_id_to_point3D_idx[point3D_id] = SceneManager.INVALID_POINT3D
        elif check_triangulation_angles:
            xyz = self.points3D[point3D_idx, :]
            tvecs = np.array([self.images[image_id].tvec - xyz for image_id in image_ids])
            tvecs /= np.linalg.norm(tvecs, axis=-1)[:, np.newaxis]
            cos_theta = np.array([u.dot(v) for u, v in combinations(tvecs, 2)])
            if np.min(cos_theta) > max_tri_prod or np.max(cos_theta) < min_tri_prod:
                self.point3D_id_to_point3D_idx[point3D_id] = SceneManager.INVALID_POINT3D
    for image in self.images.itervalues():
        mask = np.array([self.point3D_id_to_point3D_idx.get(point3D_id, 0) == SceneManager.INVALID_POINT3D for point3D_id in image.point3D_ids])
        image.point3D_ids[mask] = SceneManager.INVALID_POINT3D

class Image:

    def __init__(self, name_, camera_id_, q_, tvec_):
        self.name = name_
        self.camera_id = camera_id_
        self.q = q_
        self.tvec = tvec_
        self.points2D = np.empty((0, 2), dtype=np.float64)
        self.point3D_ids = np.empty((0,), dtype=np.uint64)

    def R(self):
        return self.q.ToR()

    def C(self):
        return -self.R().T.dot(self.tvec)

    @property
    def t(self):
        return self.tvec

def R(self):
    return self.q.ToR()

def C(self):
    return -self.R().T.dot(self.tvec)

def cross_prod_matrix(v):
    return np.array(((0.0, -v[2], v[1]), (v[2], 0.0, -v[0]), (-v[1], v[0], 0.0)))

def axis_angle_to_rotation_matrix(axis, angle=None):
    if angle is None:
        angle = np.linalg.norm(axis)
        if np.abs(angle) > np.finfo('float').eps:
            axis = axis / angle
    cp_axis = cross_prod_matrix(axis)
    return np.eye(3) + (np.sin(angle) * cp_axis + (1.0 - np.cos(angle)) * cp_axis.dot(cp_axis))

class Quaternion:

    @staticmethod
    def FromR(R):
        trace = np.trace(R)
        if trace > 0:
            qw = 0.5 * np.sqrt(1.0 + trace)
            qx = (R[2, 1] - R[1, 2]) * 0.25 / qw
            qy = (R[0, 2] - R[2, 0]) * 0.25 / qw
            qz = (R[1, 0] - R[0, 1]) * 0.25 / qw
        elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
            s = 2.0 * np.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2])
            qw = (R[2, 1] - R[1, 2]) / s
            qx = 0.25 * s
            qy = (R[0, 1] + R[1, 0]) / s
            qz = (R[0, 2] + R[2, 0]) / s
        elif R[1, 1] > R[2, 2]:
            s = 2.0 * np.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2])
            qw = (R[0, 2] - R[2, 0]) / s
            qx = (R[0, 1] + R[1, 0]) / s
            qy = 0.25 * s
            qz = (R[1, 2] + R[2, 1]) / s
        else:
            s = 2.0 * np.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1])
            qw = (R[1, 0] - R[0, 1]) / s
            qx = (R[0, 2] + R[2, 0]) / s
            qy = (R[1, 2] + R[2, 1]) / s
            qz = 0.25 * s
        return Quaternion(np.array((qw, qx, qy, qz)))

    @staticmethod
    def FromAxisAngle(axis, angle=None):
        if angle is None:
            angle = np.linalg.norm(axis)
            if np.abs(angle) > np.finfo('float').eps:
                axis = axis / angle
        qw = np.cos(0.5 * angle)
        axis = axis * np.sin(0.5 * angle)
        return Quaternion(np.array((qw, axis[0], axis[1], axis[2])))

    def __init__(self, q=np.array((1.0, 0.0, 0.0, 0.0))):
        if isinstance(q, Quaternion):
            self.q = q.q.copy()
        else:
            q = np.asarray(q)
            if q.size == 4:
                self.q = q.copy()
            elif q.size == 3:
                self.q = np.empty(4)
                self.q[0], self.q[1:] = (0.0, q.ravel())
            else:
                raise Exception('Input quaternion should be a 3- or 4-vector')

    def __add__(self, other):
        return Quaternion(self.q + other.q)

    def __iadd__(self, other):
        self.q += other.q
        return self

    def __invert__(self):
        return Quaternion(np.array((self.q[0], -self.q[1], -self.q[2], -self.q[3])))

    def __mul__(self, other):
        if isinstance(other, Quaternion):
            return Quaternion(np.array((self.q[0] * other.q[0] - self.q[1] * other.q[1] - self.q[2] * other.q[2] - self.q[3] * other.q[3], self.q[0] * other.q[1] + self.q[1] * other.q[0] + self.q[2] * other.q[3] - self.q[3] * other.q[2], self.q[0] * other.q[2] - self.q[1] * other.q[3] + self.q[2] * other.q[0] + self.q[3] * other.q[1], self.q[0] * other.q[3] + self.q[1] * other.q[2] - self.q[2] * other.q[1] + self.q[3] * other.q[0])))
        else:
            return Quaternion(other * self.q)

    def __rmul__(self, other):
        return self * other

    def __imul__(self, other):
        self.q[:] = (self * other).q
        return self

    def __irmul__(self, other):
        self.q[:] = (self * other).q
        return self

    def __neg__(self):
        return Quaternion(-self.q)

    def __sub__(self, other):
        return Quaternion(self.q - other.q)

    def __isub__(self, other):
        self.q -= other.q
        return self

    def __str__(self):
        return str(self.q)

    def copy(self):
        return Quaternion(self)

    def dot(self, other):
        return self.q.dot(other.q)

    def inverse(self):
        return Quaternion((~self).q / self.q.dot(self.q))

    def norm(self):
        return np.linalg.norm(self.q)

    def normalize(self):
        self.q /= np.linalg.norm(self.q)
        return self

    def rotate_points(self, x):
        x = np.atleast_2d(x)
        return x.dot(self.ToR().T)

    def ToR(self):
        return np.eye(3) + 2 * np.array(((-self.q[2] * self.q[2] - self.q[3] * self.q[3], self.q[1] * self.q[2] - self.q[3] * self.q[0], self.q[1] * self.q[3] + self.q[2] * self.q[0]), (self.q[1] * self.q[2] + self.q[3] * self.q[0], -self.q[1] * self.q[1] - self.q[3] * self.q[3], self.q[2] * self.q[3] - self.q[1] * self.q[0]), (self.q[1] * self.q[3] - self.q[2] * self.q[0], self.q[2] * self.q[3] + self.q[1] * self.q[0], -self.q[1] * self.q[1] - self.q[2] * self.q[2])))

    def ToAxisAngle(self):
        sin_sq_theta = self.q[1:].dot(self.q[1:])
        if np.abs(sin_sq_theta) > np.finfo('float').eps:
            sin_theta = np.sqrt(sin_sq_theta)
            cos_theta = self.q[0]
            angle = 2.0 * (np.arctan2(-sin_theta, -cos_theta) if cos_theta < 0.0 else np.arctan2(sin_theta, cos_theta))
            return self.q[1:] * (angle / sin_theta)
        return np.zeros(3)

    def ToEulerAngles(self):
        qsq = self.q ** 2
        k = 2.0 * (self.q[0] * self.q[3] + self.q[1] * self.q[2]) / qsq.sum()
        if 1.0 - k < np.finfo('float').eps:
            return (2.0 * np.arctan2(self.q[1], self.q[0]), 0.5 * np.pi, 0.0)
        if 1.0 + k < np.finfo('float').eps:
            return (-2.0 * np.arctan2(self.q[1], self.q[0]), -0.5 * np.pi, 0.0)
        yaw = np.arctan2(2.0 * (self.q[0] * self.q[2] - self.q[1] * self.q[3]), qsq[0] + qsq[1] - qsq[2] - qsq[3])
        pitch = np.arcsin(k)
        roll = np.arctan2(2.0 * (self.q[0] * self.q[1] - self.q[2] * self.q[3]), qsq[0] - qsq[1] + qsq[2] - qsq[3])
        return (yaw, pitch, roll)

@staticmethod
def FromR(R):
    trace = np.trace(R)
    if trace > 0:
        qw = 0.5 * np.sqrt(1.0 + trace)
        qx = (R[2, 1] - R[1, 2]) * 0.25 / qw
        qy = (R[0, 2] - R[2, 0]) * 0.25 / qw
        qz = (R[1, 0] - R[0, 1]) * 0.25 / qw
    elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        s = 2.0 * np.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2])
        qw = (R[2, 1] - R[1, 2]) / s
        qx = 0.25 * s
        qy = (R[0, 1] + R[1, 0]) / s
        qz = (R[0, 2] + R[2, 0]) / s
    elif R[1, 1] > R[2, 2]:
        s = 2.0 * np.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2])
        qw = (R[0, 2] - R[2, 0]) / s
        qx = (R[0, 1] + R[1, 0]) / s
        qy = 0.25 * s
        qz = (R[1, 2] + R[2, 1]) / s
    else:
        s = 2.0 * np.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1])
        qw = (R[1, 0] - R[0, 1]) / s
        qx = (R[0, 2] + R[2, 0]) / s
        qy = (R[1, 2] + R[2, 1]) / s
        qz = 0.25 * s
    return Quaternion(np.array((qw, qx, qy, qz)))

@staticmethod
def FromAxisAngle(axis, angle=None):
    if angle is None:
        angle = np.linalg.norm(axis)
        if np.abs(angle) > np.finfo('float').eps:
            axis = axis / angle
    qw = np.cos(0.5 * angle)
    axis = axis * np.sin(0.5 * angle)
    return Quaternion(np.array((qw, axis[0], axis[1], axis[2])))

def __init__(self, q=np.array((1.0, 0.0, 0.0, 0.0))):
    if isinstance(q, Quaternion):
        self.q = q.q.copy()
    else:
        q = np.asarray(q)
        if q.size == 4:
            self.q = q.copy()
        elif q.size == 3:
            self.q = np.empty(4)
            self.q[0], self.q[1:] = (0.0, q.ravel())
        else:
            raise Exception('Input quaternion should be a 3- or 4-vector')

def __add__(self, other):
    return Quaternion(self.q + other.q)

def __invert__(self):
    return Quaternion(np.array((self.q[0], -self.q[1], -self.q[2], -self.q[3])))

def __mul__(self, other):
    if isinstance(other, Quaternion):
        return Quaternion(np.array((self.q[0] * other.q[0] - self.q[1] * other.q[1] - self.q[2] * other.q[2] - self.q[3] * other.q[3], self.q[0] * other.q[1] + self.q[1] * other.q[0] + self.q[2] * other.q[3] - self.q[3] * other.q[2], self.q[0] * other.q[2] - self.q[1] * other.q[3] + self.q[2] * other.q[0] + self.q[3] * other.q[1], self.q[0] * other.q[3] + self.q[1] * other.q[2] - self.q[2] * other.q[1] + self.q[3] * other.q[0])))
    else:
        return Quaternion(other * self.q)

def __neg__(self):
    return Quaternion(-self.q)

def __sub__(self, other):
    return Quaternion(self.q - other.q)

def copy(self):
    return Quaternion(self)

def dot(self, other):
    return self.q.dot(other.q)

def inverse(self):
    return Quaternion((~self).q / self.q.dot(self.q))

def rotate_points(self, x):
    x = np.atleast_2d(x)
    return x.dot(self.ToR().T)

def ToR(self):
    return np.eye(3) + 2 * np.array(((-self.q[2] * self.q[2] - self.q[3] * self.q[3], self.q[1] * self.q[2] - self.q[3] * self.q[0], self.q[1] * self.q[3] + self.q[2] * self.q[0]), (self.q[1] * self.q[2] + self.q[3] * self.q[0], -self.q[1] * self.q[1] - self.q[3] * self.q[3], self.q[2] * self.q[3] - self.q[1] * self.q[0]), (self.q[1] * self.q[3] - self.q[2] * self.q[0], self.q[2] * self.q[3] + self.q[1] * self.q[0], -self.q[1] * self.q[1] - self.q[2] * self.q[2])))

def ToAxisAngle(self):
    sin_sq_theta = self.q[1:].dot(self.q[1:])
    if np.abs(sin_sq_theta) > np.finfo('float').eps:
        sin_theta = np.sqrt(sin_sq_theta)
        cos_theta = self.q[0]
        angle = 2.0 * (np.arctan2(-sin_theta, -cos_theta) if cos_theta < 0.0 else np.arctan2(sin_theta, cos_theta))
        return self.q[1:] * (angle / sin_theta)
    return np.zeros(3)

class DualQuaternion:

    @staticmethod
    def FromQT(q, t):
        return DualQuaternion(qe=0.5 * np.asarray(t)) * DualQuaternion(q)

    def __init__(self, q0=np.array((1.0, 0.0, 0.0, 0.0)), qe=np.zeros(4)):
        self.q0, self.qe = (Quaternion(q0), Quaternion(qe))

    def __add__(self, other):
        return DualQuaternion(self.q0 + other.q0, self.qe + other.qe)

    def __iadd__(self, other):
        self.q0 += other.q0
        self.qe += other.qe
        return self

    def __invert__(self):
        return DualQuaternion(~self.q0, ~self.qe)

    def __mul__(self, other):
        if isinstance(other, DualQuaternion):
            return DualQuaternion(self.q0 * other.q0, self.q0 * other.qe + self.qe * other.q0)
        elif isinstance(other, complex):
            return DualQuaternion(self.q0 * other.real, self.q0 * other.imag + self.qe * other.real)
        else:
            return DualQuaternion(other * self.q0, other * self.qe)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __imul__(self, other):
        tmp = self * other
        self.q0, self.qe = (tmp.q0, tmp.qe)
        return self

    def __neg__(self):
        return DualQuaternion(-self.q0, -self.qe)

    def __sub__(self, other):
        return DualQuaternion(self.q0 - other.q0, self.qe - other.qe)

    def __isub__(self, other):
        self.q0 -= other.q0
        self.qe -= other.qe
        return self

    def inverse(self):
        normsq = complex(q0.dot(q0), 2.0 * self.q0.q.dot(self.qe.q))
        inv_len_real = 1.0 / normsq.real
        return ~self * complex(inv_len_real, -normsq.imag * inv_len_real * inv_len_real)

    def norm(self):
        q0_norm = self.q0.norm()
        return complex(q0_norm, self.q0.dot(self.qe) / q0_norm)

    def normalize(self):
        norm = self.norm()
        inv_len_real = 1.0 / norm.real
        self *= complex(inv_len_real, -norm.imag * inv_len_real * inv_len_real)
        return self

    def getT(self):
        return 2 * (self.qe * ~self.q0).q[1:]

    def ToQT(self):
        return (self.q0, self.getT())

@staticmethod
def FromQT(q, t):
    return DualQuaternion(qe=0.5 * np.asarray(t)) * DualQuaternion(q)

def __init__(self, q0=np.array((1.0, 0.0, 0.0, 0.0)), qe=np.zeros(4)):
    self.q0, self.qe = (Quaternion(q0), Quaternion(qe))

def __add__(self, other):
    return DualQuaternion(self.q0 + other.q0, self.qe + other.qe)

def __invert__(self):
    return DualQuaternion(~self.q0, ~self.qe)

def __mul__(self, other):
    if isinstance(other, DualQuaternion):
        return DualQuaternion(self.q0 * other.q0, self.q0 * other.qe + self.qe * other.q0)
    elif isinstance(other, complex):
        return DualQuaternion(self.q0 * other.real, self.q0 * other.imag + self.qe * other.real)
    else:
        return DualQuaternion(other * self.q0, other * self.qe)

def __neg__(self):
    return DualQuaternion(-self.q0, -self.qe)

def __sub__(self, other):
    return DualQuaternion(self.q0 - other.q0, self.qe - other.qe)

def load_colmap_data(realdir):
    camerasfile = os.path.join(realdir, 'sparse/0/cameras.bin')
    camdata = read_model.read_cameras_binary(camerasfile)
    list_of_keys = list(camdata.keys())
    cam = camdata[list_of_keys[0]]
    print('Cameras', len(cam))
    h, w, f = (cam.height, cam.width, cam.params[0])
    hwf = np.array([h, w, f]).reshape([3, 1])
    imagesfile = os.path.join(realdir, 'sparse/0/images.bin')
    imdata = read_model.read_images_binary(imagesfile)
    w2c_mats = []
    bottom = np.array([0, 0, 0, 1.0]).reshape([1, 4])
    names = [imdata[k].name for k in imdata]
    print('Images #', len(names))
    perm = np.argsort(names)
    for k in imdata:
        im = imdata[k]
        R = im.qvec2rotmat()
        t = im.tvec.reshape([3, 1])
        m = np.concatenate([np.concatenate([R, t], 1), bottom], 0)
        w2c_mats.append(m)
    w2c_mats = np.stack(w2c_mats, 0)
    c2w_mats = np.linalg.inv(w2c_mats)
    poses = c2w_mats[:, :3, :4].transpose([1, 2, 0])
    poses = np.concatenate([poses, np.tile(hwf[..., np.newaxis], [1, 1, poses.shape[-1]])], 1)
    points3dfile = os.path.join(realdir, 'sparse/0/points3D.bin')
    pts3d = read_model.read_points3d_binary(points3dfile)
    poses = np.concatenate([poses[:, 0:1, :], -poses[:, 1:2, :], -poses[:, 2:3, :], poses[:, 3:4, :], poses[:, 4:5, :]], 1)
    return (poses, pts3d, perm)

class Image(BaseImage):

    def qvec2rotmat(self):
        return qvec2rotmat(self.qvec)

def qvec2rotmat(self):
    return qvec2rotmat(self.qvec)

def read_model(path, ext):
    if ext == '.txt':
        cameras = read_cameras_text(os.path.join(path, 'cameras' + ext))
        images = read_images_text(os.path.join(path, 'images' + ext))
        points3D = read_points3D_text(os.path.join(path, 'points3D') + ext)
    else:
        cameras = read_cameras_binary(os.path.join(path, 'cameras' + ext))
        images = read_images_binary(os.path.join(path, 'images' + ext))
        points3D = read_points3d_binary(os.path.join(path, 'points3D') + ext)
    return (cameras, images, points3D)

def qvec2rotmat(qvec):
    return np.array([[1 - 2 * qvec[2] ** 2 - 2 * qvec[3] ** 2, 2 * qvec[1] * qvec[2] - 2 * qvec[0] * qvec[3], 2 * qvec[3] * qvec[1] + 2 * qvec[0] * qvec[2]], [2 * qvec[1] * qvec[2] + 2 * qvec[0] * qvec[3], 1 - 2 * qvec[1] ** 2 - 2 * qvec[3] ** 2, 2 * qvec[2] * qvec[3] - 2 * qvec[0] * qvec[1]], [2 * qvec[3] * qvec[1] - 2 * qvec[0] * qvec[2], 2 * qvec[2] * qvec[3] + 2 * qvec[0] * qvec[1], 1 - 2 * qvec[1] ** 2 - 2 * qvec[2] ** 2]])

def create_view_cameras(camera_extrinsics, camera_intrinsics, H, W):
    """
    We will transform the camera extrinsics and intrinsics to scene.cameras.Camera objects.

    Note 1) camera extrinsics are RUB, but gaussians splatting requires COLMAP convention (RDF)
    Note 2) R is c2w, T is w2c. We need to inverse the camera_extrinsics to get T.

    Args:
        camera_extrinsics: [N_frames, 3, 4], c2w
        camera_intrinsics: [3, 3]
        H: height of the image
        W: width of the image
    """
    frames_num = camera_extrinsics.shape[0]
    camera_extrinsics = np.concatenate([camera_extrinsics[:, :, 0:1], -camera_extrinsics[:, :, 1:2], -camera_extrinsics[:, :, 2:3], camera_extrinsics[:, :, 3:4]], axis=2)
    view_cameras = []
    for i in tqdm(range(frames_num)):
        c2w = np.eye(4)
        c2w[:3] = camera_extrinsics[i]
        w2c = np.linalg.inv(c2w)
        R = c2w[:3, :3]
        T = w2c[:3, 3]
        K = np.array([camera_intrinsics[0, 0], camera_intrinsics[1, 1], camera_intrinsics[0, 2], camera_intrinsics[1, 2]])
        FoVx = 2 * np.arctan(W / (2 * camera_intrinsics[0, 0]))
        FoVy = 2 * np.arctan(H / (2 * camera_intrinsics[1, 1]))
        image = torch.zeros((3, H, W), dtype=torch.float32)
        image_name = f'image_{i:03d}'
        uid = i
        camera = Camera(colmap_id=uid, R=R, T=T, FoVx=FoVx, FoVy=FoVy, image=image, gt_alpha_mask=None, image_name=image_name, uid=uid, K=K)
        view_cameras.append(camera)
    return view_cameras

def getWorld2View(R, t):
    Rt = np.zeros((4, 4))
    Rt[:3, :3] = R.transpose()
    Rt[:3, 3] = t
    Rt[3, 3] = 1.0
    return np.float32(Rt)

def getWorld2View2(R, t, translate=np.array([0.0, 0.0, 0.0]), scale=1.0):
    Rt = np.zeros((4, 4))
    Rt[:3, :3] = R.transpose()
    Rt[:3, 3] = t
    Rt[3, 3] = 1.0
    C2W = np.linalg.inv(Rt)
    cam_center = C2W[:3, 3]
    cam_center = (cam_center + translate) * scale
    C2W[:3, 3] = cam_center
    Rt = np.linalg.inv(C2W)
    return np.float32(Rt)

def l1_loss(network_output, gt):
    return torch.abs(network_output - gt).mean()

def camera_to_JSON(id, camera: Camera):
    Rt = np.zeros((4, 4))
    Rt[:3, :3] = camera.R.transpose()
    Rt[:3, 3] = camera.T
    Rt[3, 3] = 1.0
    W2C = np.linalg.inv(Rt)
    pos = W2C[:3, 3]
    rot = W2C[:3, :3]
    serializable_array_2d = [x.tolist() for x in rot]
    camera_entry = {'id': id, 'img_name': camera.image_name, 'width': camera.width, 'height': camera.height, 'position': pos.tolist(), 'rotation': serializable_array_2d, 'fy': fov2focal(camera.FovY, camera.height), 'fx': fov2focal(camera.FovX, camera.width)}
    return camera_entry

def getNerfppNorm(cam_info):

    def get_center_and_diag(cam_centers):
        cam_centers = np.hstack(cam_centers)
        avg_cam_center = np.mean(cam_centers, axis=1, keepdims=True)
        center = avg_cam_center
        dist = np.linalg.norm(cam_centers - center, axis=0, keepdims=True)
        diagonal = np.max(dist)
        return (center.flatten(), diagonal)
    cam_centers = []
    for cam in cam_info:
        W2C = getWorld2View2(cam.R, cam.T)
        C2W = np.linalg.inv(W2C)
        cam_centers.append(C2W[:3, 3:4])
    center, diagonal = get_center_and_diag(cam_centers)
    radius = diagonal * 1.1
    translate = -center
    return {'translate': translate, 'radius': radius}

def qvec2rotmat(qvec):
    return np.array([[1 - 2 * qvec[2] ** 2 - 2 * qvec[3] ** 2, 2 * qvec[1] * qvec[2] - 2 * qvec[0] * qvec[3], 2 * qvec[3] * qvec[1] + 2 * qvec[0] * qvec[2]], [2 * qvec[1] * qvec[2] + 2 * qvec[0] * qvec[3], 1 - 2 * qvec[1] ** 2 - 2 * qvec[3] ** 2, 2 * qvec[2] * qvec[3] - 2 * qvec[0] * qvec[1]], [2 * qvec[3] * qvec[1] - 2 * qvec[0] * qvec[2], 2 * qvec[2] * qvec[3] + 2 * qvec[0] * qvec[1], 1 - 2 * qvec[1] ** 2 - 2 * qvec[2] ** 2]])

class Image(BaseImage):

    def qvec2rotmat(self):
        return qvec2rotmat(self.qvec)

def qvec2rotmat(self):
    return qvec2rotmat(self.qvec)

class PositionalEncoding(nn.Module):

    def __init__(self, num_encoding_functions, include_input=True):
        super().__init__()
        self.num_encoding_functions = num_encoding_functions
        self.include_input = include_input

    def forward(self, x):
        batch_size, num_samples, _ = x.shape
        encoding_functions = torch.arange(0, self.num_encoding_functions, dtype=torch.float32, device=x.device)
        encoding_functions = 2 ** encoding_functions * math.pi
        encoded_inputs = x.unsqueeze(-1) * encoding_functions.view(1, 1, 1, -1)
        encoded_inputs = torch.cat([torch.sin(encoded_inputs), torch.cos(encoded_inputs)], dim=-1)
        encoded_inputs = encoded_inputs.view(batch_size, num_samples, -1)
        if self.include_input:
            encoded_inputs = torch.cat([x, encoded_inputs], dim=-1)
        return encoded_inputs

def forward(self, x):
    batch_size, num_samples, _ = x.shape
    encoding_functions = torch.arange(0, self.num_encoding_functions, dtype=torch.float32, device=x.device)
    encoding_functions = 2 ** encoding_functions * math.pi
    encoded_inputs = x.unsqueeze(-1) * encoding_functions.view(1, 1, 1, -1)
    encoded_inputs = torch.cat([torch.sin(encoded_inputs), torch.cos(encoded_inputs)], dim=-1)
    encoded_inputs = encoded_inputs.view(batch_size, num_samples, -1)
    if self.include_input:
        encoded_inputs = torch.cat([x, encoded_inputs], dim=-1)
    return encoded_inputs

def fill_img_with_sd(img: np.ndarray, mask: np.ndarray, text_prompt: str, device='cuda'):
    pipe = StableDiffusionInpaintPipeline.from_pretrained('stabilityai/stable-diffusion-2-inpainting', torch_dtype=torch.float32).to(device)
    img_crop, mask_crop = crop_for_filling_pre(img, mask)
    img_crop_filled = pipe(prompt=text_prompt, image=Image.fromarray(img_crop), mask_image=Image.fromarray(mask_crop)).images[0]
    img_filled = crop_for_filling_post(img, mask, np.array(img_crop_filled))
    return img_filled

def replace_img_with_sd(img: np.ndarray, mask: np.ndarray, text_prompt: str, step: int=50, device='cuda'):
    pipe = StableDiffusionInpaintPipeline.from_pretrained('stabilityai/stable-diffusion-2-inpainting', torch_dtype=torch.float32).to(device)
    img_padded, mask_padded, padding_factors = resize_and_pad(img, mask)
    img_padded = pipe(prompt=text_prompt, image=Image.fromarray(img_padded), mask_image=Image.fromarray(255 - mask_padded), num_inference_steps=step).images[0]
    height, width, _ = img.shape
    img_resized, mask_resized = recover_size(np.array(img_padded), mask_padded, (height, width), padding_factors)
    mask_resized = np.expand_dims(mask_resized, -1) / 255
    img_resized = img_resized * (1 - mask_resized) + img * mask_resized
    return img_resized

class RemoveAnythingVideo(nn.Module):

    def __init__(self, args, tracker_target='ostrack', segmentor_target='sam', inpainter_target='sttn'):
        super().__init__()
        tracker_build_args = {'tracker_param': args.tracker_ckpt}
        inpainter_build_args = {'lama': {'lama_config': args.lama_config, 'lama_ckpt': args.lama_ckpt}, 'sttn': {'model_type': 'sttn', 'ckpt_p': args.vi_ckpt}}
        self.tracker = self.build_tracker(tracker_target, **tracker_build_args)
        self.inpainter = self.build_inpainter(inpainter_target, **inpainter_build_args[inpainter_target])
        self.tracker_target = tracker_target
        self.inpainter_target = inpainter_target

    def build_tracker(self, target, **kwargs):
        assert target == 'ostrack', 'Only support sam now.'
        return build_ostrack_model(**kwargs)

    def build_segmentor(self, target='sam', **kwargs):
        assert target == 'sam', 'Only support sam now.'
        return build_sam_model(**kwargs)

    def build_inpainter(self, target='sttn', **kwargs):
        if target == 'lama':
            return build_lama_model(**kwargs)
        elif target == 'sttn':
            return build_sttn_model(**kwargs)
        else:
            raise NotImplementedError('Only support lama and sttn')

    def forward_tracker(self, frames_ps, init_box):
        init_box = np.array(init_box).astype(np.float32).reshape(-1, 4)
        seq = Sequence('tmp', frames_ps, 'inpaint-anything', init_box)
        all_box_xywh = get_box_using_ostrack(self.tracker, seq)
        return all_box_xywh

    def forward_segmentor(self, img, point_coords=None, point_labels=None, box=None, mask_input=None, multimask_output=True, return_logits=False):
        self.segmentor.set_image(img)
        masks, scores, logits = self.segmentor.predict(point_coords=point_coords, point_labels=point_labels, box=box, mask_input=mask_input, multimask_output=multimask_output, return_logits=return_logits)
        self.segmentor.reset_image()
        return (masks, scores)

    def forward_inpainter(self, frames, masks):
        print(self.inpainter_target)
        if self.inpainter_target == 'lama':
            for idx in range(len(frames)):
                frames[idx] = inpaint_img_with_builded_lama(self.inpainter, frames[idx], masks[idx], device=self.device)
        elif self.inpainter_target == 'sttn':
            frames = [Image.fromarray(frame) for frame in frames]
            masks = [Image.fromarray(np.uint8(mask * 255)) for mask in masks]
            frames = inpaint_video_with_builded_sttn(self.inpainter, frames, masks, device=self.device)
        else:
            raise NotImplementedError
        return frames

    @property
    def device(self):
        return 'cuda' if torch.cuda.is_available() else 'cpu'

    def mask_selection(self, masks, scores, ref_mask=None, interactive=False):
        if interactive:
            raise NotImplementedError
        else:
            if ref_mask is not None:
                mse = np.mean((masks.astype(np.int32) - ref_mask.astype(np.int32)) ** 2, axis=(-2, -1))
                idx = mse.argmin()
            else:
                idx = scores.argmax()
            return masks[idx]

    @staticmethod
    def get_box_from_mask(mask):
        x, y, w, h = cv2.boundingRect(mask)
        return np.array([x, y, w, h])

    def forward(self, frame_ps: List[str], key_frame_idx: int, key_frame_point_coords: np.ndarray, key_frame_point_labels: np.ndarray, key_frame_mask_idx: int=None, dilate_kernel_size: int=15):
        """
        Mask is 0-1 ndarray in default
        Frame is 0-255 ndarray in default
        """
        assert key_frame_idx == 0, 'Only support key frame at the beginning.'
        key_frame_p = frame_ps[key_frame_idx]
        key_frame = iio.imread(key_frame_p)
        key_masks, key_scores = self.forward_segmentor(key_frame, key_frame_point_coords, key_frame_point_labels)
        if key_frame_mask_idx is not None:
            key_mask = key_masks[key_frame_mask_idx]
        else:
            key_mask = self.mask_selection(key_masks, key_scores)
        if dilate_kernel_size is not None:
            key_mask = dilate_mask(key_mask, dilate_kernel_size)
        key_box = self.get_box_from_mask(key_mask)
        print('Tracking ...')
        all_box = self.forward_tracker(frame_ps, key_box)
        print('Segmenting ...')
        all_mask = [key_mask]
        all_frame = [key_frame]
        ref_mask = key_mask
        for frame_p, box in zip(frame_ps[1:], all_box[1:]):
            frame = iio.imread(frame_p)
            x, y, w, h = box
            sam_box = np.array([x, y, x + w, y + h])
            masks, scores = self.forward_segmentor(frame, box=sam_box)
            mask = self.mask_selection(masks, scores, ref_mask)
            if dilate_kernel_size is not None:
                mask = dilate_mask(mask, dilate_kernel_size)
            ref_mask = mask
            all_mask.append(mask)
            all_frame.append(frame)
        print('Inpainting ...')
        all_frame = self.forward_inpainter(all_frame, all_mask)
        return (all_frame, all_mask, all_box)

def mask_selection(self, masks, scores, ref_mask=None, interactive=False):
    if interactive:
        raise NotImplementedError
    else:
        if ref_mask is not None:
            mse = np.mean((masks.astype(np.int32) - ref_mask.astype(np.int32)) ** 2, axis=(-2, -1))
            idx = mse.argmin()
        else:
            idx = scores.argmax()
        return masks[idx]

class RemoveAnythingVideo(nn.Module):

    def __init__(self, args, tracker_target='ostrack', segmentor_target='sam', inpainter_target='sttn'):
        super().__init__()
        tracker_build_args = {'tracker_param': args.tracker_ckpt}
        segmentor_build_args = {'model_type': args.sam_model_type, 'ckpt_p': args.sam_ckpt}
        inpainter_build_args = {'lama': {'lama_config': args.lama_config, 'lama_ckpt': args.lama_ckpt}, 'sttn': {'model_type': 'sttn', 'ckpt_p': args.vi_ckpt}}
        self.tracker = self.build_tracker(tracker_target, **tracker_build_args)
        self.segmentor = self.build_segmentor(segmentor_target, **segmentor_build_args)
        self.inpainter = self.build_inpainter(inpainter_target, **inpainter_build_args[inpainter_target])
        self.tracker_target = tracker_target
        self.segmentor_target = segmentor_target
        self.inpainter_target = inpainter_target

    def build_tracker(self, target, **kwargs):
        assert target == 'ostrack', 'Only support sam now.'
        return build_ostrack_model(**kwargs)

    def build_segmentor(self, target='sam', **kwargs):
        assert target == 'sam', 'Only support sam now.'
        return build_sam_model(**kwargs)

    def build_inpainter(self, target='sttn', **kwargs):
        if target == 'lama':
            return build_lama_model(**kwargs)
        elif target == 'sttn':
            return build_sttn_model(**kwargs)
        else:
            raise NotImplementedError('Only support lama and sttn')

    def forward_tracker(self, frames_ps, init_box):
        init_box = np.array(init_box).astype(np.float32).reshape(-1, 4)
        seq = Sequence('tmp', frames_ps, 'inpaint-anything', init_box)
        all_box_xywh = get_box_using_ostrack(self.tracker, seq)
        return all_box_xywh

    def forward_segmentor(self, img, point_coords=None, point_labels=None, box=None, mask_input=None, multimask_output=True, return_logits=False):
        self.segmentor.set_image(img)
        masks, scores, logits = self.segmentor.predict(point_coords=point_coords, point_labels=point_labels, box=box, mask_input=mask_input, multimask_output=multimask_output, return_logits=return_logits)
        self.segmentor.reset_image()
        return (masks, scores)

    def forward_inpainter(self, frames, masks):
        print(self.inpainter_target)
        if self.inpainter_target == 'lama':
            for idx in range(len(frames)):
                frames[idx] = inpaint_img_with_builded_lama(self.inpainter, frames[idx], masks[idx], device=self.device)
        elif self.inpainter_target == 'sttn':
            frames = [Image.fromarray(frame) for frame in frames]
            masks = [Image.fromarray(np.uint8(mask * 255)) for mask in masks]
            frames = inpaint_video_with_builded_sttn(self.inpainter, frames, masks, device=self.device)
        else:
            raise NotImplementedError
        return frames

    @property
    def device(self):
        return 'cuda' if torch.cuda.is_available() else 'cpu'

    def mask_selection(self, masks, scores, ref_mask=None, interactive=False):
        if interactive:
            raise NotImplementedError
        else:
            if ref_mask is not None:
                mse = np.mean((masks.astype(np.int32) - ref_mask.astype(np.int32)) ** 2, axis=(-2, -1))
                idx = mse.argmin()
            else:
                idx = scores.argmax()
            return masks[idx]

    @staticmethod
    def get_box_from_mask(mask):
        x, y, w, h = cv2.boundingRect(mask)
        return np.array([x, y, w, h])

    def forward(self, frame_ps: List[str], key_frame_idx: int, key_frame_point_coords: np.ndarray, key_frame_point_labels: np.ndarray, key_frame_mask_idx: int=None, dilate_kernel_size: int=15):
        """
        Mask is 0-1 ndarray in default
        Frame is 0-255 ndarray in default
        """
        assert key_frame_idx == 0, 'Only support key frame at the beginning.'
        key_frame_p = frame_ps[key_frame_idx]
        key_frame = iio.imread(key_frame_p)
        key_masks, key_scores = self.forward_segmentor(key_frame, key_frame_point_coords, key_frame_point_labels)
        if key_frame_mask_idx is not None:
            key_mask = key_masks[key_frame_mask_idx]
        else:
            key_mask = self.mask_selection(key_masks, key_scores)
        if dilate_kernel_size is not None:
            key_mask = dilate_mask(key_mask, dilate_kernel_size)
        key_box = self.get_box_from_mask(key_mask)
        print('Tracking ...')
        all_box = self.forward_tracker(frame_ps, key_box)
        print('Segmenting ...')
        all_mask = [key_mask]
        all_frame = [key_frame]
        ref_mask = key_mask
        for frame_p, box in zip(frame_ps[1:], all_box[1:]):
            frame = iio.imread(frame_p)
            x, y, w, h = box
            sam_box = np.array([x, y, x + w, y + h])
            masks, scores = self.forward_segmentor(frame, box=sam_box)
            mask = self.mask_selection(masks, scores, ref_mask)
            if dilate_kernel_size is not None:
                mask = dilate_mask(mask, dilate_kernel_size)
            ref_mask = mask
            all_mask.append(mask)
            all_frame.append(frame)
        print('Inpainting ...')
        all_frame = self.forward_inpainter(all_frame, all_mask)
        return (all_frame, all_mask, all_box)

def mask_selection(self, masks, scores, ref_mask=None, interactive=False):
    if interactive:
        raise NotImplementedError
    else:
        if ref_mask is not None:
            mse = np.mean((masks.astype(np.int32) - ref_mask.astype(np.int32)) ** 2, axis=(-2, -1))
            idx = mse.argmin()
        else:
            idx = scores.argmax()
        return masks[idx]

def get_box_using_ostrack(tracker, seq, output_dir=None):
    output = tracker.run_sequence(seq, debug=False)
    tracked_bb = np.array(output['target_bbox']).astype(int)
    return tracked_bb

def random_move_control_points(X, Y, imageHeight, imageWidth, lineVelocity, region_size, maxLineAcceleration=(3, 0.5), maxInitSpeed=3):
    region_width, region_height = region_size
    speed, angle = lineVelocity
    X += int(speed * np.cos(angle))
    Y += int(speed * np.sin(angle))
    lineVelocity = random_accelerate(lineVelocity, maxLineAcceleration, dist='guassian')
    if X > imageHeight - region_height or X < 0 or Y > imageWidth - region_width or (Y < 0):
        lineVelocity = get_random_velocity(maxInitSpeed, dist='guassian')
    new_X = np.clip(X, 0, imageHeight - region_height)
    new_Y = np.clip(Y, 0, imageWidth - region_width)
    return (new_X, new_Y, lineVelocity)

def remove_spectral_norm(module, name='weight'):
    """Removes the spectral normalization reparameterization from a module.

    Args:
        module (Module): containing module
        name (str, optional): name of weight parameter

    Example:
        >>> m = spectral_norm(nn.Linear(40, 10))
        >>> remove_spectral_norm(m)
    """
    for k, hook in module._forward_pre_hooks.items():
        if isinstance(hook, SpectralNorm) and hook.name == name:
            hook.remove(module)
            del module._forward_pre_hooks[k]
            return module
    raise ValueError("spectral_norm of '{}' not found in {}".format(name, module))

class PositionEmbeddingRandom(nn.Module):
    """
    Positional encoding using random spatial frequencies.
    """

    def __init__(self, num_pos_feats: int=64, scale: Optional[float]=None) -> None:
        super().__init__()
        if scale is None or scale <= 0.0:
            scale = 1.0
        self.register_buffer('positional_encoding_gaussian_matrix', scale * torch.randn((2, num_pos_feats)))

    def _pe_encoding(self, coords: torch.Tensor) -> torch.Tensor:
        """Positionally encode points that are normalized to [0,1]."""
        coords = 2 * coords - 1
        coords = coords @ self.positional_encoding_gaussian_matrix
        coords = 2 * np.pi * coords
        return torch.cat([torch.sin(coords), torch.cos(coords)], dim=-1)

    def forward(self, size: Tuple[int, int]) -> torch.Tensor:
        """Generate positional encoding for a grid of the specified size."""
        h, w = size
        device: Any = self.positional_encoding_gaussian_matrix.device
        grid = torch.ones((h, w), device=device, dtype=torch.float32)
        y_embed = grid.cumsum(dim=0) - 0.5
        x_embed = grid.cumsum(dim=1) - 0.5
        y_embed = y_embed / h
        x_embed = x_embed / w
        pe = self._pe_encoding(torch.stack([x_embed, y_embed], dim=-1))
        return pe.permute(2, 0, 1)

    def forward_with_coords(self, coords_input: torch.Tensor, image_size: Tuple[int, int]) -> torch.Tensor:
        """Positionally encode points that are not normalized to [0,1]."""
        coords = coords_input.clone()
        coords[:, :, 0] = coords[:, :, 0] / image_size[1]
        coords[:, :, 1] = coords[:, :, 1] / image_size[0]
        return self._pe_encoding(coords.to(torch.float))

def _pe_encoding(self, coords: torch.Tensor) -> torch.Tensor:
    """Positionally encode points that are normalized to [0,1]."""
    coords = 2 * coords - 1
    coords = coords @ self.positional_encoding_gaussian_matrix
    coords = 2 * np.pi * coords
    return torch.cat([torch.sin(coords), torch.cos(coords)], dim=-1)

def batch_iterator(batch_size: int, *args) -> Generator[List[Any], None, None]:
    assert len(args) > 0 and all((len(a) == len(args[0]) for a in args)), 'Batched iteration must have inputs of all the same size.'
    n_batches = len(args[0]) // batch_size + int(len(args[0]) % batch_size != 0)
    for b in range(n_batches):
        yield [arg[b * batch_size:(b + 1) * batch_size] for arg in args]

def show_points(ax, coords: List[List[float]], labels: List[int], size=375):
    coords = np.array(coords)
    labels = np.array(labels)
    color_table = {0: 'red', 1: 'green'}
    for label_value, color in color_table.items():
        points = coords[labels == label_value]
        ax.scatter(points[:, 0], points[:, 1], color=color, marker='*', s=size, edgecolor='white', linewidth=1.25)

class LearnableSpatialTransformWrapper(nn.Module):

    def __init__(self, impl, pad_coef=0.5, angle_init_range=80, train_angle=True):
        super().__init__()
        self.impl = impl
        self.angle = torch.rand(1) * angle_init_range
        if train_angle:
            self.angle = nn.Parameter(self.angle, requires_grad=True)
        self.pad_coef = pad_coef

    def forward(self, x):
        if torch.is_tensor(x):
            return self.inverse_transform(self.impl(self.transform(x)), x)
        elif isinstance(x, tuple):
            x_trans = tuple((self.transform(elem) for elem in x))
            y_trans = self.impl(x_trans)
            return tuple((self.inverse_transform(elem, orig_x) for elem, orig_x in zip(y_trans, x)))
        else:
            raise ValueError(f'Unexpected input type {type(x)}')

    def transform(self, x):
        height, width = x.shape[2:]
        pad_h, pad_w = (int(height * self.pad_coef), int(width * self.pad_coef))
        x_padded = F.pad(x, [pad_w, pad_w, pad_h, pad_h], mode='reflect')
        x_padded_rotated = rotate(x_padded, angle=self.angle.to(x_padded))
        return x_padded_rotated

    def inverse_transform(self, y_padded_rotated, orig_x):
        height, width = orig_x.shape[2:]
        pad_h, pad_w = (int(height * self.pad_coef), int(width * self.pad_coef))
        y_padded = rotate(y_padded_rotated, angle=-self.angle.to(y_padded_rotated))
        y_height, y_width = y_padded.shape[2:]
        y = y_padded[:, :, pad_h:y_height - pad_h, pad_w:y_width - pad_w]
        return y

def transform(self, x):
    height, width = x.shape[2:]
    pad_h, pad_w = (int(height * self.pad_coef), int(width * self.pad_coef))
    x_padded = F.pad(x, [pad_w, pad_w, pad_h, pad_h], mode='reflect')
    x_padded_rotated = rotate(x_padded, angle=self.angle.to(x_padded))
    return x_padded_rotated

def inverse_transform(self, y_padded_rotated, orig_x):
    height, width = orig_x.shape[2:]
    pad_h, pad_w = (int(height * self.pad_coef), int(width * self.pad_coef))
    y_padded = rotate(y_padded_rotated, angle=-self.angle.to(y_padded_rotated))
    y_height, y_width = y_padded.shape[2:]
    y = y_padded[:, :, pad_h:y_height - pad_h, pad_w:y_width - pad_w]
    return y

def _l1_loss(pred: torch.Tensor, pred_downscaled: torch.Tensor, ref: torch.Tensor, mask: torch.Tensor, mask_downscaled: torch.Tensor, image: torch.Tensor, on_pred: bool=True):
    """l1 loss on src pixels, and downscaled predictions if on_pred=True"""
    loss = torch.mean(torch.abs(pred[mask < 1e-08] - image[mask < 1e-08]))
    if on_pred:
        loss += torch.mean(torch.abs(pred_downscaled[mask_downscaled >= 1e-08] - ref[mask_downscaled >= 1e-08]))
    return loss

def calculate_frechet_distance(activations_pred, activations_target, eps=1e-06):
    mu1, sigma1 = fid_calculate_activation_statistics(activations_pred)
    mu2, sigma2 = fid_calculate_activation_statistics(activations_target)
    diff = mu1 - mu2
    covmean, _ = linalg.sqrtm(sigma1.dot(sigma2), disp=False)
    if not np.isfinite(covmean).all():
        msg = 'fid calculation produces singular product; adding %s to diagonal of cov estimates' % eps
        LOGGER.warning(msg)
        offset = np.eye(sigma1.shape[0]) * eps
        covmean = linalg.sqrtm((sigma1 + offset).dot(sigma2 + offset))
    if np.iscomplexobj(covmean):
        if not np.allclose(np.diagonal(covmean).imag, 0, atol=0.01):
            m = np.max(np.abs(covmean.imag))
            raise ValueError('Imaginary component {}'.format(m))
        covmean = covmean.real
    tr_covmean = np.trace(covmean)
    return diff.dot(diff) + np.trace(sigma1) + np.trace(sigma2) - 2 * tr_covmean

def calculate_frechet_distance(mu1, sigma1, mu2, sigma2, eps=1e-06):
    """Numpy implementation of the Frechet Distance.
    The Frechet distance between two multivariate Gaussians X_1 ~ N(mu_1, C_1)
    and X_2 ~ N(mu_2, C_2) is
            d^2 = ||mu_1 - mu_2||^2 + Tr(C_1 + C_2 - 2*sqrt(C_1*C_2)).

    Stable version by Dougal J. Sutherland.

    Params:
    -- mu1   : Numpy array containing the activations of a layer of the
               inception net (like returned by the function 'get_predictions')
               for generated samples.
    -- mu2   : The sample mean over activations, precalculated on an
               representative data set.
    -- sigma1: The covariance matrix over activations for generated samples.
    -- sigma2: The covariance matrix over activations, precalculated on an
               representative data set.

    Returns:
    --   : The Frechet Distance.
    """
    mu1 = np.atleast_1d(mu1)
    mu2 = np.atleast_1d(mu2)
    sigma1 = np.atleast_2d(sigma1)
    sigma2 = np.atleast_2d(sigma2)
    assert mu1.shape == mu2.shape, 'Training and test mean vectors have different lengths'
    assert sigma1.shape == sigma2.shape, 'Training and test covariances have different dimensions'
    diff = mu1 - mu2
    covmean, _ = linalg.sqrtm(sigma1.dot(sigma2), disp=False)
    if not np.isfinite(covmean).all():
        msg = 'fid calculation produces singular product; adding %s to diagonal of cov estimates' % eps
        print(msg)
        offset = np.eye(sigma1.shape[0]) * eps
        covmean = linalg.sqrtm((sigma1 + offset).dot(sigma2 + offset))
    if np.iscomplexobj(covmean):
        if not np.allclose(np.diagonal(covmean).imag, 0, atol=0.01):
            m = np.max(np.abs(covmean.imag))
            raise ValueError('Imaginary component {}'.format(m))
        covmean = covmean.real
    tr_covmean = np.trace(covmean)
    return diff.dot(diff) + np.trace(sigma1) + np.trace(sigma2) - 2 * tr_covmean

def striding(array):
    """Downsample x by factor using striding.

  @return: The downsampled array, of the same type as x.
  """
    factor = (2, 2)
    if np.all(np.array(factor, int) == 1):
        return array
    return array[tuple((np.s_[::f] for f in factor))]

def striding(array):
    """Downsample x by factor using striding.

  @return: The downsampled array, of the same type as x.
  """
    factor = (2, 2, 2)
    if np.all(np.array(factor, int) == 1):
        return array
    return array[tuple((np.s_[::f] for f in factor))]

class TorchTestCase(unittest.TestCase):

    def assertTensorClose(self, a, b, atol=0.001, rtol=0.001):
        npa, npb = (as_numpy(a), as_numpy(b))
        self.assertTrue(np.allclose(npa, npb, atol=atol), 'Tensor close check failed\n{}\n{}\nadiff={}, rdiff={}'.format(a, b, np.abs(npa - npb).max(), np.abs((npa - npb) / np.fmax(npa, 1e-05)).max()))

def assertTensorClose(self, a, b, atol=0.001, rtol=0.001):
    npa, npb = (as_numpy(a), as_numpy(b))
    self.assertTrue(np.allclose(npa, npb, atol=atol), 'Tensor close check failed\n{}\n{}\nadiff={}, rdiff={}'.format(a, b, np.abs(npa - npb).max(), np.abs((npa - npb) / np.fmax(npa, 1e-05)).max()))

class LearnableSpatialTransformWrapper(nn.Module):

    def __init__(self, impl, pad_coef=0.5, angle_init_range=80, train_angle=True):
        super().__init__()
        self.impl = impl
        self.angle = torch.rand(1) * angle_init_range
        if train_angle:
            self.angle = nn.Parameter(self.angle, requires_grad=True)
        self.pad_coef = pad_coef

    def forward(self, x):
        if torch.is_tensor(x):
            return self.inverse_transform(self.impl(self.transform(x)), x)
        elif isinstance(x, tuple):
            x_trans = tuple((self.transform(elem) for elem in x))
            y_trans = self.impl(x_trans)
            return tuple((self.inverse_transform(elem, orig_x) for elem, orig_x in zip(y_trans, x)))
        else:
            raise ValueError(f'Unexpected input type {type(x)}')

    def transform(self, x):
        height, width = x.shape[2:]
        pad_h, pad_w = (int(height * self.pad_coef), int(width * self.pad_coef))
        x_padded = F.pad(x, [pad_w, pad_w, pad_h, pad_h], mode='reflect')
        x_padded_rotated = rotate(x_padded, angle=self.angle.to(x_padded))
        return x_padded_rotated

    def inverse_transform(self, y_padded_rotated, orig_x):
        height, width = orig_x.shape[2:]
        pad_h, pad_w = (int(height * self.pad_coef), int(width * self.pad_coef))
        y_padded = rotate(y_padded_rotated, angle=-self.angle.to(y_padded_rotated))
        y_height, y_width = y_padded.shape[2:]
        y = y_padded[:, :, pad_h:y_height - pad_h, pad_w:y_width - pad_w]
        return y

def transform(self, x):
    height, width = x.shape[2:]
    pad_h, pad_w = (int(height * self.pad_coef), int(width * self.pad_coef))
    x_padded = F.pad(x, [pad_w, pad_w, pad_h, pad_h], mode='reflect')
    x_padded_rotated = rotate(x_padded, angle=self.angle.to(x_padded))
    return x_padded_rotated

def inverse_transform(self, y_padded_rotated, orig_x):
    height, width = orig_x.shape[2:]
    pad_h, pad_w = (int(height * self.pad_coef), int(width * self.pad_coef))
    y_padded = rotate(y_padded_rotated, angle=-self.angle.to(y_padded_rotated))
    y_height, y_width = y_padded.shape[2:]
    y = y_padded[:, :, pad_h:y_height - pad_h, pad_w:y_width - pad_w]
    return y

def _l1_loss(pred: torch.Tensor, pred_downscaled: torch.Tensor, ref: torch.Tensor, mask: torch.Tensor, mask_downscaled: torch.Tensor, image: torch.Tensor, on_pred: bool=True):
    """l1 loss on src pixels, and downscaled predictions if on_pred=True"""
    loss = torch.mean(torch.abs(pred[mask < 1e-08] - image[mask < 1e-08]))
    if on_pred:
        loss += torch.mean(torch.abs(pred_downscaled[mask_downscaled >= 1e-08] - ref[mask_downscaled >= 1e-08]))
    return loss

def calculate_frechet_distance(activations_pred, activations_target, eps=1e-06):
    mu1, sigma1 = fid_calculate_activation_statistics(activations_pred)
    mu2, sigma2 = fid_calculate_activation_statistics(activations_target)
    diff = mu1 - mu2
    covmean, _ = linalg.sqrtm(sigma1.dot(sigma2), disp=False)
    if not np.isfinite(covmean).all():
        msg = 'fid calculation produces singular product; adding %s to diagonal of cov estimates' % eps
        LOGGER.warning(msg)
        offset = np.eye(sigma1.shape[0]) * eps
        covmean = linalg.sqrtm((sigma1 + offset).dot(sigma2 + offset))
    if np.iscomplexobj(covmean):
        if not np.allclose(np.diagonal(covmean).imag, 0, atol=0.01):
            m = np.max(np.abs(covmean.imag))
            raise ValueError('Imaginary component {}'.format(m))
        covmean = covmean.real
    tr_covmean = np.trace(covmean)
    return diff.dot(diff) + np.trace(sigma1) + np.trace(sigma2) - 2 * tr_covmean

def calculate_frechet_distance(mu1, sigma1, mu2, sigma2, eps=1e-06):
    """Numpy implementation of the Frechet Distance.
    The Frechet distance between two multivariate Gaussians X_1 ~ N(mu_1, C_1)
    and X_2 ~ N(mu_2, C_2) is
            d^2 = ||mu_1 - mu_2||^2 + Tr(C_1 + C_2 - 2*sqrt(C_1*C_2)).

    Stable version by Dougal J. Sutherland.

    Params:
    -- mu1   : Numpy array containing the activations of a layer of the
               inception net (like returned by the function 'get_predictions')
               for generated samples.
    -- mu2   : The sample mean over activations, precalculated on an
               representative data set.
    -- sigma1: The covariance matrix over activations for generated samples.
    -- sigma2: The covariance matrix over activations, precalculated on an
               representative data set.

    Returns:
    --   : The Frechet Distance.
    """
    mu1 = np.atleast_1d(mu1)
    mu2 = np.atleast_1d(mu2)
    sigma1 = np.atleast_2d(sigma1)
    sigma2 = np.atleast_2d(sigma2)
    assert mu1.shape == mu2.shape, 'Training and test mean vectors have different lengths'
    assert sigma1.shape == sigma2.shape, 'Training and test covariances have different dimensions'
    diff = mu1 - mu2
    covmean, _ = linalg.sqrtm(sigma1.dot(sigma2), disp=False)
    if not np.isfinite(covmean).all():
        msg = 'fid calculation produces singular product; adding %s to diagonal of cov estimates' % eps
        print(msg)
        offset = np.eye(sigma1.shape[0]) * eps
        covmean = linalg.sqrtm((sigma1 + offset).dot(sigma2 + offset))
    if np.iscomplexobj(covmean):
        if not np.allclose(np.diagonal(covmean).imag, 0, atol=0.01):
            m = np.max(np.abs(covmean.imag))
            raise ValueError('Imaginary component {}'.format(m))
        covmean = covmean.real
    tr_covmean = np.trace(covmean)
    return diff.dot(diff) + np.trace(sigma1) + np.trace(sigma2) - 2 * tr_covmean

def striding(array):
    """Downsample x by factor using striding.

  @return: The downsampled array, of the same type as x.
  """
    factor = (2, 2)
    if np.all(np.array(factor, int) == 1):
        return array
    return array[tuple((np.s_[::f] for f in factor))]

def striding(array):
    """Downsample x by factor using striding.

  @return: The downsampled array, of the same type as x.
  """
    factor = (2, 2, 2)
    if np.all(np.array(factor, int) == 1):
        return array
    return array[tuple((np.s_[::f] for f in factor))]

class TorchTestCase(unittest.TestCase):

    def assertTensorClose(self, a, b, atol=0.001, rtol=0.001):
        npa, npb = (as_numpy(a), as_numpy(b))
        self.assertTrue(np.allclose(npa, npb, atol=atol), 'Tensor close check failed\n{}\n{}\nadiff={}, rdiff={}'.format(a, b, np.abs(npa - npb).max(), np.abs((npa - npb) / np.fmax(npa, 1e-05)).max()))

def assertTensorClose(self, a, b, atol=0.001, rtol=0.001):
    npa, npb = (as_numpy(a), as_numpy(b))
    self.assertTrue(np.allclose(npa, npb, atol=atol), 'Tensor close check failed\n{}\n{}\nadiff={}, rdiff={}'.format(a, b, np.abs(npa - npb).max(), np.abs((npa - npb) / np.fmax(npa, 1e-05)).max()))

def adjust_keep_rate(epoch, warmup_epochs, total_epochs, ITERS_PER_EPOCH, base_keep_rate=0.5, max_keep_rate=1, iters=-1):
    if epoch < warmup_epochs:
        return 1
    if epoch >= total_epochs:
        return base_keep_rate
    if iters == -1:
        iters = epoch * ITERS_PER_EPOCH
    total_iters = ITERS_PER_EPOCH * (total_epochs - warmup_epochs)
    iters = iters - ITERS_PER_EPOCH * warmup_epochs
    keep_rate = base_keep_rate + (max_keep_rate - base_keep_rate) * (math.cos(iters / total_iters * math.pi) + 1) * 0.5
    return keep_rate

def get_center3x3(locations, centers, strides, range=3):
    """
    Inputs:
        locations: M x 2
        centers: N x 2
        strides: M
    """
    range = (range - 1) / 2
    M, N = (locations.shape[0], centers.shape[0])
    locations_expanded = locations.view(M, 1, 2).expand(M, N, 2)
    centers_expanded = centers.view(1, N, 2).expand(M, N, 2)
    strides_expanded = strides.view(M, 1, 1).expand(M, N, 2)
    centers_discret = ((centers_expanded / strides_expanded).int() * strides_expanded).float() + strides_expanded / 2
    dist_x = (locations_expanded[:, :, 0] - centers_discret[:, :, 0]).abs()
    dist_y = (locations_expanded[:, :, 1] - centers_discret[:, :, 1]).abs()
    return (dist_x <= strides_expanded[:, :, 0] * range) & (dist_y <= strides_expanded[:, :, 0] * range)

def cubic_spline_fourier(f, a):
    """The continuous Fourier transform of a cubic spline kernel."""
    bf = (6 * (1 - torch.cos(2 * math.pi * f)) + 3 * a * (1 - torch.cos(4 * math.pi * f)) - (6 + 8 * a) * math.pi * f * torch.sin(2 * math.pi * f) - 2 * a * math.pi * f * torch.sin(4 * math.pi * f)) / (4 * math.pi ** 4 * f ** 4)
    bf[f == 0] = 1
    return bf

class LambdaWarmUpCosineScheduler:
    """
    note: use with a base_lr of 1.0
    """

    def __init__(self, warm_up_steps, lr_min, lr_max, lr_start, max_decay_steps, verbosity_interval=0):
        self.lr_warm_up_steps = warm_up_steps
        self.lr_start = lr_start
        self.lr_min = lr_min
        self.lr_max = lr_max
        self.lr_max_decay_steps = max_decay_steps
        self.last_lr = 0.0
        self.verbosity_interval = verbosity_interval

    def schedule(self, n, **kwargs):
        if self.verbosity_interval > 0:
            if n % self.verbosity_interval == 0:
                print(f'current step: {n}, recent lr-multiplier: {self.last_lr}')
        if n < self.lr_warm_up_steps:
            lr = (self.lr_max - self.lr_start) / self.lr_warm_up_steps * n + self.lr_start
            self.last_lr = lr
            return lr
        else:
            t = (n - self.lr_warm_up_steps) / (self.lr_max_decay_steps - self.lr_warm_up_steps)
            t = min(t, 1.0)
            lr = self.lr_min + 0.5 * (self.lr_max - self.lr_min) * (1 + np.cos(t * np.pi))
            self.last_lr = lr
            return lr

    def __call__(self, n, **kwargs):
        return self.schedule(n, **kwargs)

def schedule(self, n, **kwargs):
    if self.verbosity_interval > 0:
        if n % self.verbosity_interval == 0:
            print(f'current step: {n}, recent lr-multiplier: {self.last_lr}')
    if n < self.lr_warm_up_steps:
        lr = (self.lr_max - self.lr_start) / self.lr_warm_up_steps * n + self.lr_start
        self.last_lr = lr
        return lr
    else:
        t = (n - self.lr_warm_up_steps) / (self.lr_max_decay_steps - self.lr_warm_up_steps)
        t = min(t, 1.0)
        lr = self.lr_min + 0.5 * (self.lr_max - self.lr_min) * (1 + np.cos(t * np.pi))
        self.last_lr = lr
        return lr

class FixedPositionalEmbedding(nn.Module):

    def __init__(self, dim):
        super().__init__()
        inv_freq = 1.0 / 10000 ** (torch.arange(0, dim, 2).float() / dim)
        self.register_buffer('inv_freq', inv_freq)

    def forward(self, x, seq_dim=1, offset=0):
        t = torch.arange(x.shape[seq_dim], device=x.device).type_as(self.inv_freq) + offset
        sinusoid_inp = torch.einsum('i , j -> i j', t, self.inv_freq)
        emb = torch.cat((sinusoid_inp.sin(), sinusoid_inp.cos()), dim=-1)
        return emb[None, :, :]

def forward(self, x, seq_dim=1, offset=0):
    t = torch.arange(x.shape[seq_dim], device=x.device).type_as(self.inv_freq) + offset
    sinusoid_inp = torch.einsum('i , j -> i j', t, self.inv_freq)
    emb = torch.cat((sinusoid_inp.sin(), sinusoid_inp.cos()), dim=-1)
    return emb[None, :, :]

def l1(x, y):
    return torch.abs(x - y)

def anisotropic_Gaussian(ksize=15, theta=np.pi, l1=6, l2=6):
    """ generate an anisotropic Gaussian kernel
    Args:
        ksize : e.g., 15, kernel size
        theta : [0,  pi], rotation angle range
        l1    : [0.1,50], scaling of eigenvalues
        l2    : [0.1,l1], scaling of eigenvalues
        If l1 = l2, will get an isotropic Gaussian kernel.
    Returns:
        k     : kernel
    """
    v = np.dot(np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]]), np.array([1.0, 0.0]))
    V = np.array([[v[0], v[1]], [v[1], -v[0]]])
    D = np.array([[l1, 0], [0, l2]])
    Sigma = np.dot(np.dot(V, D), np.linalg.inv(V))
    k = gm_blur_kernel(mean=[0, 0], cov=Sigma, size=ksize)
    return k

def gen_kernel(k_size=np.array([15, 15]), scale_factor=np.array([4, 4]), min_var=0.6, max_var=10.0, noise_level=0):
    """"
    # modified version of https://github.com/assafshocher/BlindSR_dataset_generator
    # Kai Zhang
    # min_var = 0.175 * sf  # variance of the gaussian kernel will be sampled between min_var and max_var
    # max_var = 2.5 * sf
    """
    lambda_1 = min_var + np.random.rand() * (max_var - min_var)
    lambda_2 = min_var + np.random.rand() * (max_var - min_var)
    theta = np.random.rand() * np.pi
    noise = -noise_level + np.random.rand(*k_size) * noise_level * 2
    LAMBDA = np.diag([lambda_1, lambda_2])
    Q = np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])
    SIGMA = Q @ LAMBDA @ Q.T
    INV_SIGMA = np.linalg.inv(SIGMA)[None, None, :, :]
    MU = k_size // 2 - 0.5 * (scale_factor - 1)
    MU = MU[None, None, :, None]
    [X, Y] = np.meshgrid(range(k_size[0]), range(k_size[1]))
    Z = np.stack([X, Y], 2)[:, :, :, None]
    ZZ = Z - MU
    ZZ_t = ZZ.transpose(0, 1, 3, 2)
    raw_kernel = np.exp(-0.5 * np.squeeze(ZZ_t @ INV_SIGMA @ ZZ)) * (1 + noise)
    kernel = raw_kernel / np.sum(raw_kernel)
    return kernel

def fspecial_laplacian(alpha):
    alpha = max([0, min([alpha, 1])])
    h1 = alpha / (alpha + 1)
    h2 = (1 - alpha) / (alpha + 1)
    h = [[h1, h2, h1], [h2, -4 / (alpha + 1), h2], [h1, h2, h1]]
    h = np.array(h)
    return h

def uint2single(img):
    return np.float32(img / 255.0)

def uint162single(img):
    return np.float32(img / 65535.0)

def anisotropic_Gaussian(ksize=15, theta=np.pi, l1=6, l2=6):
    """ generate an anisotropic Gaussian kernel
    Args:
        ksize : e.g., 15, kernel size
        theta : [0,  pi], rotation angle range
        l1    : [0.1,50], scaling of eigenvalues
        l2    : [0.1,l1], scaling of eigenvalues
        If l1 = l2, will get an isotropic Gaussian kernel.
    Returns:
        k     : kernel
    """
    v = np.dot(np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]]), np.array([1.0, 0.0]))
    V = np.array([[v[0], v[1]], [v[1], -v[0]]])
    D = np.array([[l1, 0], [0, l2]])
    Sigma = np.dot(np.dot(V, D), np.linalg.inv(V))
    k = gm_blur_kernel(mean=[0, 0], cov=Sigma, size=ksize)
    return k

def gen_kernel(k_size=np.array([15, 15]), scale_factor=np.array([4, 4]), min_var=0.6, max_var=10.0, noise_level=0):
    """"
    # modified version of https://github.com/assafshocher/BlindSR_dataset_generator
    # Kai Zhang
    # min_var = 0.175 * sf  # variance of the gaussian kernel will be sampled between min_var and max_var
    # max_var = 2.5 * sf
    """
    lambda_1 = min_var + np.random.rand() * (max_var - min_var)
    lambda_2 = min_var + np.random.rand() * (max_var - min_var)
    theta = np.random.rand() * np.pi
    noise = -noise_level + np.random.rand(*k_size) * noise_level * 2
    LAMBDA = np.diag([lambda_1, lambda_2])
    Q = np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])
    SIGMA = Q @ LAMBDA @ Q.T
    INV_SIGMA = np.linalg.inv(SIGMA)[None, None, :, :]
    MU = k_size // 2 - 0.5 * (scale_factor - 1)
    MU = MU[None, None, :, None]
    [X, Y] = np.meshgrid(range(k_size[0]), range(k_size[1]))
    Z = np.stack([X, Y], 2)[:, :, :, None]
    ZZ = Z - MU
    ZZ_t = ZZ.transpose(0, 1, 3, 2)
    raw_kernel = np.exp(-0.5 * np.squeeze(ZZ_t @ INV_SIGMA @ ZZ)) * (1 + noise)
    kernel = raw_kernel / np.sum(raw_kernel)
    return kernel

def fspecial_laplacian(alpha):
    alpha = max([0, min([alpha, 1])])
    h1 = alpha / (alpha + 1)
    h2 = (1 - alpha) / (alpha + 1)
    h = [[h1, h2, h1], [h2, -4 / (alpha + 1), h2], [h1, h2, h1]]
    h = np.array(h)
    return h

def get_timestep_embedding(timesteps, embedding_dim):
    """
    This matches the implementation in Denoising Diffusion Probabilistic Models:
    From Fairseq.
    Build sinusoidal embeddings.
    This matches the implementation in tensor2tensor, but differs slightly
    from the description in Section 3.5 of "Attention Is All You Need".
    """
    assert len(timesteps.shape) == 1
    half_dim = embedding_dim // 2
    emb = math.log(10000) / (half_dim - 1)
    emb = torch.exp(torch.arange(half_dim, dtype=torch.float32) * -emb)
    emb = emb.to(device=timesteps.device)
    emb = timesteps.float()[:, None] * emb[None, :]
    emb = torch.cat([torch.sin(emb), torch.cos(emb)], dim=1)
    if embedding_dim % 2 == 1:
        emb = torch.nn.functional.pad(emb, (0, 1, 0, 0))
    return emb

def transform_nerf2opencv_convention(extrinsic):
    """
    Transform and pad NeRF convention extrinsic (RUB) [3, 4] to
                      OpenCV convention extrisic (RDF) [4, 4].

    Args:
        extrinsic : np.ndarray
            shape [3, 4] in NeRF convention extrinsic (RUB)
    Returns:
        extrinsic_opencv : np.ndarray
            shape [4, 4] in OpenCV convention extrinsic (RDF)
    """
    all_ones = np.array([[0, 0, 0, 1]])
    extrinsic_opencv = np.concatenate((extrinsic, all_ones), axis=0)
    extrinsic_opencv = np.concatenate((extrinsic_opencv[:, 0:1], -extrinsic_opencv[:, 1:2], -extrinsic_opencv[:, 2:3], extrinsic_opencv[:, 3:]), axis=1)
    return extrinsic_opencv

def rotate(point, angle):
    """Rotates a point around the origin by the specified angle in radians."""
    rotation_matrix = np.array([[np.cos(angle), -np.sin(angle), 0], [np.sin(angle), np.cos(angle), 0], [0, 0, 1]])
    return np.dot(rotation_matrix, point)

def generate_vertices(car):
    """Generates the vertices of a 3D box."""
    x = car['cx']
    y = car['cy']
    z = car['cz']
    length = car['length']
    width = car['width']
    height = car['height']
    heading = car['heading']
    box_center = np.array([x, y, z])
    half_dims = np.array([length / 2, width / 2, height / 2])
    relative_positions = np.array([[-1, -1, -1], [-1, -1, 1], [-1, 1, -1], [-1, 1, 1], [1, -1, -1], [1, -1, 1], [1, 1, -1], [1, 1, 1]]) * half_dims
    vertices = np.asarray([rotate(pos, heading) + box_center for pos in relative_positions])
    return vertices

def skylatlong2world(u, v):
    """Get the (x, y, z, valid) coordinates of the point defined by (u, v)
    for a latlong map."""
    u = u * 2
    thetaLatLong = np.pi * (u - 1)
    phiLatLong = np.pi * v / 2
    x = np.sin(phiLatLong) * np.sin(thetaLatLong)
    y = np.cos(phiLatLong)
    z = -np.sin(phiLatLong) * np.cos(thetaLatLong)
    direction = np.concatenate((-z, -x, y), axis=1)
    return direction

class ViewAdjustAgent:

    def __init__(self, config):
        self.config = config

    def llm_reasoning_ego_motion(self, scene, message):
        try:
            q0 = 'I will give you a description about view adjustment, I need you to help me judge if the description is related to static view adjust or ego is dynamic(with motion).'
            q1 = "Given my description, return a dictionary in JSON format, with key 'if_view_motion'"
            q2 = "If the description is just a view adjust operation, the 'if_view_motion' should be 0. If the description is related to view motion, the 'if_view_motion' should be 1."
            q3 = "I will give you some examples. <user>: Rotate the viewpoint 30 degrees to the left, you should return {'if_view_motion':0}. " + "<user>: viewpoint moves ahead slowly, you should return {'if_view_motion':1}. "
            result = openai.ChatCompletion.create(model='gpt-4', messages=[{'role': 'system', 'content': 'You are an assistant helping me to provide information and ultimately return a JSON dictionary.'}, {'role': 'user', 'content': q0}, {'role': 'user', 'content': q1}, {'role': 'user', 'content': q2}, {'role': 'user', 'content': q3}, {'role': 'user', 'content': message}])
            answer = result['choices'][0]['message']['content']
            print(f'{colored('[View Adjust Agent LLM] reasoning the view motion', color='magenta', attrs=['bold'])}                      \n{colored('[Raw Response>>>]', attrs=['bold'])} {answer}')
            start = answer.index('{')
            answer = answer[start:]
            end = answer.rfind('}')
            answer = answer[:end + 1]
            if_view_motion = eval(answer)
            print(f'{colored('[Extracted Response>>>]', attrs=['bold'])} {if_view_motion} \n')
        except Exception as e:
            print(e)
            traceback.print_exc()
            return '[View Adjust Agent LLM] fails, can not recongnize instruction'
        if if_view_motion['if_view_motion'] == 0:
            return False
        else:
            return True

    def llm_view_motion_gen(self, scene, message):
        try:
            q0 = 'I will give you a description about ego motion, you should tell me the speed of ego.'
            q1 = "Given my description, return a dictionary in JSON format, with key 'speed'."
            q2 = "If the ego motion is fast, 'speed' should be 'fast'; if the ego motion is slow, 'speed' should be 'slow'; if the description doesnot mention speed, 'speed' is default as 'fast'."
            q3 = "I will give you some examples. <user>: ego vehicle moves forward, you should return {'speed':'fast'}. " + "<user>: ego vehicle drives ahead slowly, you should return {'speed':'slow'}. "
            result = openai.ChatCompletion.create(model='gpt-4', messages=[{'role': 'system', 'content': 'You are an assistant helping me to provide information and ultimately return a JSON dictionary.'}, {'role': 'user', 'content': q0}, {'role': 'user', 'content': q1}, {'role': 'user', 'content': q2}, {'role': 'user', 'content': q3}, {'role': 'user', 'content': message}])
            answer = result['choices'][0]['message']['content']
            print(f'{colored('[View Adjust Agent LLM] generating the ego motion', color='magenta', attrs=['bold'])}                      \n{colored('[Raw Response>>>]', attrs=['bold'])} {answer}')
            start = answer.index('{')
            answer = answer[start:]
            end = answer.rfind('}')
            answer = answer[:end + 1]
            ego_motion_speed = eval(answer)
            print(f'{colored('[Extracted Response>>>]', attrs=['bold'])} {ego_motion_speed} \n')
        except Exception as e:
            print(e)
            traceback.print_exc()
            return '[View Adjust Agent LLM] fails, can not recongnize instruction'
        if ego_motion_speed['speed'] == 'fast':
            return (0, scene.nerf_motion_extrinsics.shape[0])
        else:
            return (0, scene.nerf_motion_extrinsics.shape[0] // 3)

    def llm_view_adjust(self, scene, message):
        try:
            q0 = "I will give you a transformation operation for my viewpoint, which may include translation in 'x', 'y', 'z' or a rotation 'theta' around z-axis. "
            q1 = "For translation, positive 'x' represents forward, positve 'y' represents left, and 'z' represents up. It follows a left-hand coordinate system." + "For rotation, postive 'theta' is counterclockwise. So from own perspective, my viewpoint turns to the left. 'theta' is in degree."
            q2 = "Given my operation, return a dictionary in JSON format, with keys 'x', 'y', 'z', 'theta'."
            q3 = 'I will give you some examples: <user>: Rotate the viewpoint 30 degrees to the left ' + "<assistant>: {\n  'x': 0,\n  'y': 0,\n  'z': 0,\n  'theta': 30,\n } \n" + '<user>: move the viewpoint forward by 1 ' + "<assistant>: {\n  'x': 1,\n  'y': 0,\n  'z': 0,\n  'theta': 0,\n }  \n" + '<user>: move the viewpoint to the right by 1' + "<assistant>: {\n  'x': 0,\n  'y': -1,\n  'z': 0,\n  'theta': 0,\n} "
            result = openai.ChatCompletion.create(model='gpt-4', messages=[{'role': 'system', 'content': 'You are an assistant helping me to provide information and ultimately return a JSON dictionary.'}, {'role': 'user', 'content': q0}, {'role': 'user', 'content': q1}, {'role': 'user', 'content': q2}, {'role': 'user', 'content': q3}, {'role': 'user', 'content': message}])
            answer = result['choices'][0]['message']['content']
            print(f'{colored('[View Adjust Agent LLM] analyzing view change', color='magenta', attrs=['bold'])}                      \n{colored('[Raw Response>>>]', attrs=['bold'])} {answer}')
            start = answer.index('{')
            answer = answer[start:]
            end = answer.rfind('}')
            answer = answer[:end + 1]
            delta_extrinsic = eval(answer)
            print(f'{colored('[Extracted Response>>>]', attrs=['bold'])} {delta_extrinsic} \n')
        except Exception as e:
            print(e)
            traceback.print_exc()
            return '[View Adjust Agent LLM] fails, can not recongnize instruction'
        return delta_extrinsic

    def func_update_extrinsic(self, scene, delta_extrinsic):
        scene.current_extrinsics[:, 0, 3] += delta_extrinsic['x']
        scene.current_extrinsics[:, 1, 3] += delta_extrinsic['y']
        scene.current_extrinsics[:, 2, 3] += delta_extrinsic['z']
        theta = delta_extrinsic['theta']
        theta = theta / 180 * np.pi
        T_theta = np.array([[np.cos(theta), -np.sin(theta), 0], [np.sin(theta), np.cos(theta), 0], [0, 0, 1]])
        scene.current_extrinsics = np.matmul(T_theta, scene.current_extrinsics)

    def func_generate_extrinsic(self, scene, start_frame_idx, end_frame_idx):
        scene.current_extrinsics = inter_poses(scene.nerf_motion_extrinsics[start_frame_idx:end_frame_idx:3], scene.frames)

def func_update_extrinsic(self, scene, delta_extrinsic):
    scene.current_extrinsics[:, 0, 3] += delta_extrinsic['x']
    scene.current_extrinsics[:, 1, 3] += delta_extrinsic['y']
    scene.current_extrinsics[:, 2, 3] += delta_extrinsic['z']
    theta = delta_extrinsic['theta']
    theta = theta / 180 * np.pi
    T_theta = np.array([[np.cos(theta), -np.sin(theta), 0], [np.sin(theta), np.cos(theta), 0], [0, 0, 1]])
    scene.current_extrinsics = np.matmul(T_theta, scene.current_extrinsics)

class ProjectManager:

    def __init__(self, config):
        self.config = config

    def decompose_prompt(self, scene, user_prompt):
        """ decompose the prompt to the corresponding chatsim.agents.
        Input:
            scene : Scene
                scene object.
            user_prompt : str
                language prompt to ChatSim.
        Return:
            tasks : dict
                a dictionary of decomposed tasks.
        """
        q0 = 'I have a requirement of editing operations in an autonomous driving scenario, and I need your help to break it down into one or several supportable actions. The scene is large which means many vehicles can be contained. '
        q1 = 'The supportable five actions include adding vehicles ,                 deleting vehicles ,                 put back deleted vehicles,                 adjusting added vehicles ,                 viewpoint adjustment.'
        q2 = 'Please try to retain all the semantics and adjunct words from the original text. Each adding action should only contain one car. ' + 'Information about adding vehicles (such as their type, positions, driving status, speed, color, etc.) should be directly included within the adding action.'
        q3 = 'Split actions should be stored in a JSON dictonary. The key is action id and the value is specific action. They will be executed sequentially, and the broken operations should be independent with each other and do not rely on the detailed scene information.'
        q4 = "An example: the requirement is 'substitute the red car in the scene', you break it down and return" + "{ 1: 'Delete the red car from the scene', 2: 'Add a new car at the location where the red car was deleted' }."
        q5 = "An example: the requirement is 'delete the farthest car and add a red Audi in the right front', you break it down and return " + "{ 1: 'Delete the farthest car', 2: 'Add a red Audi in the right front' }"
        q6 = "An example: the requirement is 'delete all cars', you break it down and return " + "{ 1: 'Delete all the cars'} "
        q7 = 'I may provide very abstract requirements. For such requirements, you should analyze how to comply with the splitting of actions.'
        q8 = "An example (very abstract): the requirement is 'I want several cars driving slowly in the scene', you analyse and return " + "{ 1: 'Add one car driving slowly', 2 : 'Add one car driving slowly', 3 : 'Add one car driving slowly', 4 : 'Add one car driving slowly', 5 : 'Add one car driving slowly', 6 : 'Add one car driving slowly', 7 : 'Add one car driving slowly'} "
        q9 = 'The scene is large enough to contain more than 20 vehicles. So many vehicles can be added to the scene. Do not return any code or explanation; only a JSON dictionary is required.'
        q10 = 'Attention: the adjustments for one specific added vehicle should be included in one single output action. If there are multiple adjustments for one already added car, these adjustments must be merged in one action.'
        q11 = 'Attention: Do not appear information about the vehicles in the other broken actions.'
        q12 = 'The requirement is:' + user_prompt
        prompt_list = [q0, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10, q11, q12]
        result = openai.ChatCompletion.create(model='gpt-4-turbo-preview', messages=[{'role': 'system', 'content': 'You are an assistant helping me to break down the operations.'}] + [{'role': 'user', 'content': q} for q in prompt_list])
        answer = result['choices'][0]['message']['content']
        print(f'{colored('[User prompt]', color='magenta', attrs=['bold'])} {user_prompt}\n')
        print(f'{colored('[Project Manager] decomposing tasks', color='magenta', attrs=['bold'])}                \n{colored('[Raw Response>>>]', attrs=['bold'])} {answer}')
        try:
            start = answer.index('{')
            answer = answer[start:]
            end = answer.rfind('}')
            answer = answer[:end + 1]
            tasks = eval(answer)
            print(f'{colored('[Extracted Response>>>]', attrs=['bold'])} {answer} \n')
        except Exception as e:
            print(e)
            traceback.print_exc()
            return 'Can not parse the requirement.'
        return tasks

    def dispatch_task(self, scene, task, tech_agents):
        """ dispatch the tasks to the corresponding chatsim.agents.
        Input:
            scene : Scene
                scene object.
            task : str
                a decomposed task, should be assigned to one/more agents
            tech_agents : dict
                a dictionary of technical agents, helping to reason the task
        Return:
            callback_message : str
                if encounter bugs, record them in callback_message to users
        """
        operation_category = {1: 'adding', 2: 'deleting', 3: 'adjusting the viewpoint', 4: 'putting back previously deleted vehicles', 5: 'operating on previously added vehicles'}
        q0 = 'I will provide you with an action, and you will help me determine which operation this action belongs to.'
        q1 = 'Operations include (1) adding (2) deleting, (3) adjusting the viewpoint, (4) putting back previously deleted vehicles, (5) operating on previously added vehicles.'
        q2 = "Return the information in JSON format, with a key named 'operation'."
        q3 = "An Example: Given action 'Remove the red car from the scene', you should return {'operation': 2}"
        q4 = "An Example: Given action 'Add a green Porsche at the location where the red car was removed', you should return {'operation': 1}"
        q5 = "An Example: Given action 'Put back the deleted white car', you should return {'operation': 4}"
        q6 = "An Example: Given action 'Move the car just added to the right by 2m', you should return {'operation': 5}"
        q7 = 'Note that you should not return any code or explanations, only provide a JSON dictionary.'
        q8 = task
        prompt_list = [q0, q1, q2, q3, q4, q5, q6, q7, q8]
        result = openai.ChatCompletion.create(model='gpt-4', messages=[{'role': 'system', 'content': 'You are an assistant helping me to classify operations.'}] + [{'role': 'user', 'content': q} for q in prompt_list])
        answer = result['choices'][0]['message']['content']
        print(f'{colored('[Project Manager] dispatching each task', color='magenta', attrs=['bold'])}                 \n{colored('[Raw Response>>>]', attrs=['bold'])} {answer}')
        start = answer.index('{')
        answer = answer[start:]
        end = answer.rfind('}')
        answer = answer[:end + 1]
        operation = eval(answer)['operation']
        print(f'{colored('[Extracted Response>>>]', attrs=['bold'])} {operation}. ({operation_category[operation]}) \n')
        if operation == 1:
            self.addition_operation(scene, task, tech_agents)
        elif operation == 2:
            self.deletion_operation(scene, task, tech_agents)
        elif operation == 3:
            self.view_adjust_operation(scene, task, tech_agents)
        elif operation == 4:
            self.put_back_deleted_operation(scene, task, tech_agents)
        elif operation == 5:
            self.revise_added_operation(scene, task, tech_agents)
        scene.past_operations.append(task)

    def addition_operation(self, scene, task, tech_agents):
        """ addition operation. 
        Participants: asset_select_agent, motion_agent

        Input:
            scene : Scene
                scene object.
            task : str
                a decomposed task, should be assigned to one/more agents
            tech_agents : dict
                a dictionary of technical agents, helping to reason the task
        Return:
            callback_message : str
                if encounter bugs, record them in callback_message to users
        """
        asset_select_agent = tech_agents['asset_select_agent']
        motion_agent = tech_agents['motion_agent']
        placement_mode = motion_agent.llm_reasoning_dependency(scene, task)
        if placement_mode['dependency'] == 0:
            placement_prior = motion_agent.llm_placement_wo_dependency(scene, task)
        else:
            valid_object_descriptors_for_cars_in_scene = ['x', 'y', 'u', 'v', 'depth', 'rgb']
            scene_object_description = {}
            for car_name, description_dict in scene.original_cars_dict.items():
                filtered_description_dict = {k: v for k, v in description_dict.items() if k in valid_object_descriptors_for_cars_in_scene}
                scene_object_description[car_name] = filtered_description_dict
            valid_object_descriptors_for_added_cars = ['color', 'type']
            for car_name, description_dict in scene.added_cars_dict.items():
                filtered_description_dict = {k: v for k, v in description_dict.items() if k in valid_object_descriptors_for_added_cars}
                filtered_description_dict['x'] = description_dict['placement_result'][0]
                filtered_description_dict['y'] = description_dict['placement_result'][1]
                filtered_description_dict['direction'] = description_dict['direction']
                scene_object_description[car_name] = filtered_description_dict
            placement_prior = motion_agent.llm_placement_w_dependency(scene, task, scene_object_description)
        asset_color_and_type = asset_select_agent.llm_selecting_asset(scene, task)
        motion_prior = motion_agent.llm_motion_planning(scene, task)
        added_car_name = scene.add_car({**asset_color_and_type, **placement_prior, **motion_prior})
        motion_agent.func_placement_and_motion_single_vehicle(scene, added_car_name)

    def deletion_operation(self, scene, task, tech_agents):
        """ deletion operation. 
        Participants: deletion_agent

        Input:
            scene : Scene
                scene object.
            task : str
                a decomposed task, should be assigned to one/more agents
            tech_agents : dict
                a dictionary of technical agents, helping to reason the task
        Return:
            callback_message : str
                if encounter bugs, record them in callback_message to users
        """
        deletion_agent = tech_agents['deletion_agent']
        valid_object_descriptors = ['u', 'v', 'depth', 'rgb']
        scene_object_description = {}
        for car_name, description_dict in scene.original_cars_dict.items():
            filtered_description_dict = {k: v for k, v in description_dict.items() if k in valid_object_descriptors}
            scene_object_description[car_name] = filtered_description_dict
        deletion_car_names = deletion_agent.llm_finding_deletion(scene, task, scene_object_description)
        for car_name in deletion_car_names:
            scene.remove_car(car_name)

    def view_adjust_operation(self, scene, task, tech_agents):
        """ view adjust operation. 
        Participants: view_adjust_agent

        Input:
            scene : Scene
                scene object.
            task : str
                a decomposed task, should be assigned to one/more agents
            tech_agents : dict
                a dictionary of technical agents, helping to reason the task
        Return:
            callback_message : str
                if encounter bugs, record them in callback_message to users
        """
        view_adjust_agent = tech_agents['view_adjust_agent']
        is_ego_motion = view_adjust_agent.llm_reasoning_ego_motion(scene, task)
        if is_ego_motion:
            start_frame_in_nerf, end_frame_in_nerf = view_adjust_agent.llm_view_motion_gen(scene, task)
            view_adjust_agent.func_generate_extrinsic(scene, start_frame_in_nerf, end_frame_in_nerf)
        else:
            delta_extrinsic = view_adjust_agent.llm_view_adjust(scene, task)
            view_adjust_agent.func_update_extrinsic(scene, delta_extrinsic)

    def put_back_deleted_operation(self, scene, task, tech_agents):
        """ put back deleted operation. 
        Participants: deletion_agent

        Input:
            scene : Scene
                scene object.
            task : str
                a decomposed task, should be assigned to one/more agents
            tech_agents : dict
                a dictionary of technical agents, helping to reason the task
        Return:
            callback_message : str
                if encounter bugs, record them in callback_message to users
        """
        deletion_agent = tech_agents['deletion_agent']
        valid_object_descriptors = ['u', 'v', 'depth', 'rgb']
        scene_object_description = {}
        for car_name, description_dict in scene.original_cars_dict.items():
            filtered_description_dict = {k: v for k, v in description_dict.items() if k in valid_object_descriptors}
            scene_object_description[car_name] = filtered_description_dict
        put_back_car_names = deletion_agent.llm_putting_back_deletion(scene, task, scene_object_description)
        for car_name in put_back_car_names:
            scene.removed_cars.remove(car_name)

    def revise_added_operation(self, scene, task, tech_agents):
        """ revised added vehicle 
        Participants: asset_select_agent, motion_agent

        Input:
            scene : Scene
                scene object.
            task : str
                a decomposed task, should be assigned to one/more agents
            tech_agents : dict
                a dictionary of technical agents, helping to reason the task
        Return:
            callback_message : str
                if encounter bugs, record them in callback_message to users
        """
        asset_select_agent = tech_agents['asset_select_agent']
        motion_agent = tech_agents['motion_agent']
        for added_car_name, added_car_info in scene.added_cars_dict.items():
            added_car_info['x'] = added_car_info['motion'][0][0]
            added_car_info['y'] = added_car_info['motion'][0][1]
        added_cars_short_dict = copy.deepcopy(scene.added_cars_dict)
        for added_car_name, added_car_info in added_cars_short_dict.items():
            added_car_info.pop('motion')
            if 'mode' in added_car_info:
                added_car_info.pop('mode')
                added_car_info.pop('distance_constraint')
                added_car_info.pop('distance_min_max')
                added_car_info.pop('need_placement_and_motion')
        modified_car_dict = asset_select_agent.llm_revise_added_cars(scene, task, added_cars_short_dict)
        for modified_car_name, modified_car_info in modified_car_dict.items():
            scene.added_cars_dict[modified_car_name]['color'] = modified_car_info['color']
            scene.added_cars_dict[modified_car_name]['type'] = modified_car_info['type']
            scene.added_cars_dict[modified_car_name]['need_placement_and_motion'] = False
            check_attributes = ['action', 'speed', 'direction', 'x', 'y']
            for attri in check_attributes:
                if scene.added_cars_dict[modified_car_name][attri] != modified_car_info[attri]:
                    scene.added_cars_dict[modified_car_name]['need_placement_and_motion'] = True
                    scene.added_cars_dict[modified_car_name][attri] = modified_car_info[attri]
            motion_agent.func_placement_and_motion_single_vehicle(scene, modified_car_name)

def put_back_deleted_operation(self, scene, task, tech_agents):
    """ put back deleted operation. 
        Participants: deletion_agent

        Input:
            scene : Scene
                scene object.
            task : str
                a decomposed task, should be assigned to one/more agents
            tech_agents : dict
                a dictionary of technical agents, helping to reason the task
        Return:
            callback_message : str
                if encounter bugs, record them in callback_message to users
        """
    deletion_agent = tech_agents['deletion_agent']
    valid_object_descriptors = ['u', 'v', 'depth', 'rgb']
    scene_object_description = {}
    for car_name, description_dict in scene.original_cars_dict.items():
        filtered_description_dict = {k: v for k, v in description_dict.items() if k in valid_object_descriptors}
        scene_object_description[car_name] = filtered_description_dict
    put_back_car_names = deletion_agent.llm_putting_back_deletion(scene, task, scene_object_description)
    for car_name in put_back_car_names:
        scene.removed_cars.remove(car_name)

class Renderer:

    def __init__(self, obj_path):
        self.scene = materialed_meshes(obj_path)
        self.num_samples = 5000

    def read_int(self):
        self.H = 1280 // 3
        self.W = 1920 // 3
        self.focal = 2083 // 3
        self.buffer = torch.zeros(self.H * self.W, 3).to('cuda')

    def read_ext(self):
        self.c2w = np.array([[0.0123957, -0.00906409, -0.99988209, 2.35675933], [-0.99987913, 0.00927219, -0.01247972, -0.01891149], [0.00938421, 0.99991593, -0.00894806, 2.11490003]]).astype(np.float32)

    def read_env(self, envpath):
        """ envmap: viewing -Z
            Y
            | 
            |
            .------ X
           /       
          Z
        """
        self.env = EnvironmentMap(envpath, 'latlong')
        data = np.ones((2048, 4096, 3))
        self.env = EnvironmentMap(data, 'latlong')

    def IBL(self, light_dir):
        """
        Args:
            light_dir: [num_sample, 3], torch.tensor

        Returns:
            light_intensity:  [num_sample, 3], torch.tensor
        """

        def world2latlong(x, y, z):
            """Get the (u, v) coordinates of the point defined by (x, y, z) for
            a latitude-longitude map."""
            u = 1 + 1 / np.pi * torch.arctan2(x, -z)
            v = 1 / np.pi * torch.arccos(y)
            u = u / 2
            return (u, v)
        light_dir_envmap = [-light_dir[:, 1], light_dir[:, 2], -light_dir[:, 0]]
        uu, vv = world2latlong(light_dir_envmap[0], light_dir_envmap[1], light_dir_envmap[2])
        uu = np.floor(uu.cpu().numpy() * self.env.data.shape[1] % self.env.data.shape[1]).astype(int)
        vv = np.floor(vv.cpu().numpy() * self.env.data.shape[0] % self.env.data.shape[0]).astype(int)
        light_intensity = self.env.data[vv, uu]
        light_intensity = torch.from_numpy(light_intensity).to(light_dir)
        return light_intensity

    def render_hdri(self):
        self.buffer = self.IBL(torch.from_numpy(self.ray_d))

    def render(self):
        timer = Timer()
        directions = get_ray_directions(self.H, self.W, self.focal)
        self.ray_o, self.ray_d = get_rays(directions, self.c2w)
        timer.print('generating rays')
        self.render_hdri()
        timer.print('HDRI background rendering')
        mesh_all = self.scene.get_all_meshes()
        intersections, index_ray, index_tri = mesh_all.ray.intersects_location(ray_origins=self.ray_o, ray_directions=self.ray_d, multiple_hits=False)
        intersection_normals = mesh_all.face_normals[index_tri].astype(np.float32)
        timer.print('ray-mesh intersection')
        num_hit = intersections.shape[0]
        print(f'number of intersection: {num_hit}')
        for i in range(num_hit):
            intersection_p = intersections[i]
            normal = intersection_normals[i]
            idx_in_ray = index_ray[i]
            idx_in_faces = index_tri[i]
            wo = -self.ray_d[idx_in_ray]
            material, face_local, uv_local = self.scene.get_material_from_face_idx_of_all(idx_in_faces)
            if 'kd' not in material.kwargs:
                material_image = material.image
                u, v = uv_local[0]
                u = u - floor(u)
                v = v - floor(v)
                width, height = material_image.size
                pixel_x = int(u * (width - 1))
                pixel_y = int(v * (height - 1))
                kd = material_image.getpixel((pixel_x, pixel_y))
                if isinstance(kd, int):
                    kd = [kd, kd, kd]
                material.kwargs['kd'] = [kd[0] / 255, kd[1] / 255, kd[2] / 255]
            material_dict = rename_material_dict(material.kwargs)
            bdrf = UE4BRDF(base_color=material_dict['kd'], metallic=material_dict['pm'], roughness=material_dict['pr'], specular=material_dict['ks'])
            if material_dict['pr'] == 0:
                wi = 2 * np.dot(wo, normal) * normal - wo
                wi = torch.from_numpy(wi).cuda().reshape(1, 3)
                colors = self.IBL(wi)
            else:
                color = torch.zeros(3).cuda()
                normal = torch.from_numpy(normal).cuda()
                normal = normal / normal.norm()
                normal = normal.expand(self.num_samples, 3)
                view_dir = torch.from_numpy(wo).cuda()
                view_dir = view_dir.expand(self.num_samples, 3)
                light_dir = random_samples_on_hemisphere(normal, self.num_samples)
                brdfs = bdrf.evaluate_parallel(normal, light_dir, view_dir)
                light_intensity = self.IBL(light_dir)
                n_dot_l = torch.einsum('ij,ij->i', normal, light_dir).unsqueeze(-1).expand(-1, 3)
                colors = light_intensity * brdfs * n_dot_l / (0.5 / np.pi)
            self.buffer[idx_in_ray] = colors.mean(0)
        timer.print('Rendering foreground')
        self.renderd_image = self.buffer.reshape(self.H, self.W, 3)
        self.renderd_image = srgb_gamma_correction_torch(self.renderd_image)
        output = (self.renderd_image * 255).cpu().numpy().astype(np.uint8)
        imageio.imsave('/home/yfl/workspace/LDR_to_HDR/logs/rendered_result_pos2_whitehdr_kloppenheim_05_1k.png', output)

def read_ext(self):
    self.c2w = np.array([[0.0123957, -0.00906409, -0.99988209, 2.35675933], [-0.99987913, 0.00927219, -0.01247972, -0.01891149], [0.00938421, 0.99991593, -0.00894806, 2.11490003]]).astype(np.float32)

def world2latlong(x, y, z):
    """Get the (u, v) coordinates of the point defined by (x, y, z) for
            a latitude-longitude map."""
    u = 1 + 1 / np.pi * torch.arctan2(x, -z)
    v = 1 / np.pi * torch.arccos(y)
    u = u / 2
    return (u, v)

class Renderer:

    def __init__(self, obj_path):
        self.scene = materialed_meshes(obj_path)
        self.num_samples = 5000
        self.num_processes = 2

    def read_int(self):
        self.H = 1280
        self.W = 1920
        self.focal = 2083
        self.buffer = torch.zeros(self.H * self.W, 3).to('cuda')

    def read_ext(self):
        self.c2w = np.array([[0.0123957, -0.00906409, -0.99988209, 2.35675933], [-0.99987913, 0.00927219, -0.01247972, -0.01891149], [0.00938421, 0.99991593, -0.00894806, 2.11490003]]).astype(np.float32)

    def read_env(self, envpath):
        """ envmap: viewing -Z
            Y
            | 
            |
            .------ X
           /       
          Z
        """
        self.env = EnvironmentMap(envpath, 'latlong')

    def IBL(self, light_dir):
        """
        transform light_dir in world coord to envmap coor. hand-crafted
        """
        light_dir_np = light_dir.cpu().numpy()
        light_dir_envmap = [-light_dir_np[1], light_dir_np[2], -light_dir_np[0]]
        uu, vv = self.env.world2pixel(light_dir_envmap[0], light_dir_envmap[1], light_dir_envmap[2])
        light_intensity = torch.tensor(self.env.data[vv, uu], device='cuda', dtype=torch.float32)
        return light_intensity

    def render(self):
        multiprocessing.set_start_method('spawn')
        timer = Timer()
        directions = get_ray_directions(self.H, self.W, self.focal)
        self.ray_o, self.ray_d = get_rays(directions, self.c2w)
        timer.print('generating rays')
        mesh_all = self.scene.get_all_meshes()
        intersections, index_ray, index_tri = mesh_all.ray.intersects_location(ray_origins=self.ray_o, ray_directions=self.ray_d, multiple_hits=False)
        intersection_normals = mesh_all.face_normals[index_tri].astype(np.float32)
        timer.print('ray-mesh intersection')
        num_hit = intersections.shape[0]
        print(f'number of intersection: {num_hit}')
        self.inter_dict = OrderedDict()
        self.inter_dict['index_ray'] = index_ray
        self.inter_dict['index_tri'] = index_tri
        self.inter_dict['intersection_normals'] = intersection_normals
        self.inter_dict['ray_d'] = self.ray_d
        pool = multiprocessing.Pool(processes=self.num_processes)
        tasks = np.array_split(np.arange(num_hit), self.num_processes)
        results = pool.starmap(parallel_rendering, [(deepcopy(self.scene), deepcopy(self.inter_dict), ids) for ids in tasks])
        pool.close()
        pool.join()
        colors = torch.cat(results, dim=0)
        self.buffer[index_ray] = colors
        timer.print('Rendering foreground')
        self.renderd_image = self.buffer.reshape(self.H, self.W, 3)
        self.renderd_image = srgb_gamma_correction_torch(self.renderd_image)
        output = (self.renderd_image * 255).cpu().numpy().astype(np.uint8)
        imageio.imsave('/home/yfl/workspace/LDR_to_HDR/logs/rendered_result.png', output)

def read_ext(self):
    self.c2w = np.array([[0.0123957, -0.00906409, -0.99988209, 2.35675933], [-0.99987913, 0.00927219, -0.01247972, -0.01891149], [0.00938421, 0.99991593, -0.00894806, 2.11490003]]).astype(np.float32)

class GammaL1Loss(nn.Module):

    def __init__(self, args):
        super().__init__()
        self.weight = args['weight']
        self.gamma = args['gamma']
        self.alpha = args['alpha']

    def forward(self, pred, target, mask=None):
        loss_map = self.alpha * torch.abs(pred ** (1 / self.gamma) - target ** (1 / self.gamma))
        if mask is not None:
            loss = (loss_map * mask).sum() / mask.sum()
        else:
            loss = loss_map.mean()
        return loss * self.weight

def forward(self, pred, target, mask=None):
    loss_map = self.alpha * torch.abs(pred ** (1 / self.gamma) - target ** (1 / self.gamma))
    if mask is not None:
        loss = (loss_map * mask).sum() / mask.sum()
    else:
        loss = loss_map.mean()
    return loss * self.weight

class L1Loss(nn.Module):

    def __init__(self, args):
        super(L1Loss, self).__init__()
        self.weight = args['weight']

    def forward(self, pred, target, mask=None):
        loss_map = torch.abs(pred - target)
        if mask is not None:
            loss = (loss_map * mask).sum() / mask.sum()
        else:
            loss = loss_map.mean()
        return loss * self.weight

def forward(self, pred, target, mask=None):
    loss_map = torch.abs(pred - target)
    if mask is not None:
        loss = (loss_map * mask).sum() / mask.sum()
    else:
        loss = loss_map.mean()
    return loss * self.weight

def rm_all_in_blender():
    for obj in bpy.data.objects:
        bpy.data.objects.remove(obj)
    for mat in bpy.data.materials:
        bpy.data.materials.remove(mat)
    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)
    for texture in bpy.data.textures:
        bpy.data.textures.remove(texture)
    for image in bpy.data.images:
        bpy.data.images.remove(image)

def create_bbx(extent):
    """
    Create bounding box with 8 corners under obstacle vehicle reference.

    Parameters
    ----------
    extent : list
        half length, width and height

    Returns
    -------
    bbx : np.array
        The bounding box with 8 corners, shape: (8, 3)
    """
    bbx = np.array([[extent[0], -extent[1], -extent[2]], [extent[0], extent[1], -extent[2]], [-extent[0], extent[1], -extent[2]], [-extent[0], -extent[1], -extent[2]], [extent[0], -extent[1], extent[2]], [extent[0], extent[1], extent[2]], [-extent[0], extent[1], extent[2]], [-extent[0], -extent[1], extent[2]]])
    return bbx

def get_rotation_quaternion(ext):
    flip_matrix = np.array([[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]])
    ext = ext @ flip_matrix
    q = pyquaternion.Quaternion(matrix=ext)
    return [q.w, q.x, q.y, q.z]

def set_camera_params(intrinsic, cam2world, camera_obj_name='Camera'):
    """
    Args:
        int: Dict
            {H: xx, W:xx, focal:xx}
        cam2world: np.ndarray, OpenCV coordinate system for camera.
            shape [4,4]
        camera_obj_name: str
            name of Camera
    """
    if camera_obj_name not in bpy.data.objects:
        cameras = [obj for obj in bpy.data.objects if obj.type == 'CAMERA']
        for camera in cameras:
            bpy.data.objects.remove(camera, do_unlink=True)
        bpy.ops.object.camera_add(enter_editmode=False)
        if hasattr(bpy.context, 'object'):
            camera = bpy.context.object
            camera.name = camera_obj_name
        else:
            camera = bpy.data.objects['Camera']
        bpy.context.scene.camera = camera
    rot = get_rotation_quaternion(cam2world)
    loc = get_location(cam2world)
    focal_in_mm = get_focal_in_mm(intrinsic['H'], intrinsic['focal'])
    camera = bpy.data.objects[camera_obj_name]
    camera.location = loc
    camera.rotation_mode = 'QUATERNION'
    camera.rotation_quaternion = rot
    camera.data.sensor_fit = 'VERTICAL'
    camera.data.sensor_height = default_sensor_height
    camera.data.lens = focal_in_mm
    camera.data.lens_unit = 'MILLIMETERS'

def filter_right_lane_midpoint(input_map, v=8):
    output = {}
    centerline = input_map['centerline']
    boundary = input_map['boundary']
    direction = centerline[:, 2:4] - centerline[:, 0:2]
    theta = np.arctan2(direction[:, 1], direction[:, 0]) / np.pi * 180
    right_index = (theta >= -120) & (theta <= 10)
    filtered_centerline = centerline[right_index, :]
    output['centerline'] = filtered_centerline
    output['boundary'] = boundary
    return output

def filter_left_lane_midpoint(input_map, v=8):
    output = {}
    centerline = input_map['centerline']
    boundary = input_map['boundary']
    direction = centerline[:, 2:4] - centerline[:, 0:2]
    theta = np.arctan2(direction[:, 1], direction[:, 0]) / np.pi * 180
    right_index = (theta <= 120) & (theta >= -10)
    filtered_centerline = centerline[right_index, :]
    output['centerline'] = filtered_centerline
    output['boundary'] = boundary
    return output

def rotation_matrix_from_vector(v):
    angle = np.arctan2(v[1], v[0])
    R = np.array([[np.cos(angle), np.sin(angle)], [-np.sin(angle), np.cos(angle)]])
    return R

def transform_points_directly(points, source_vector, target_vector):
    R_source = rotation_matrix_from_vector(source_vector)
    R_target = rotation_matrix_from_vector(target_vector)
    R_direct = np.dot(R_target, np.linalg.inv(R_source))
    transformed_points = np.dot(points, R_direct.T)
    return transformed_points

def rot_and_trans_node(input_raw_map, current_pose):
    current_pose = np.array(current_pose)
    coordinate = current_pose[0:2]
    current_vec = current_pose[5:7] - current_pose[3:5]
    ego_vec = np.array([1.0, 0.0])
    output_centerline = []
    output_boundary = []
    centerline = input_raw_map['centerline']
    boundary = input_raw_map['boundary']
    for line in centerline:
        line[:, :2] -= coordinate[None, ...]
        line = transform_points_directly(line[:, :2], ego_vec, current_vec)
        output_centerline.append(line)
    for line in boundary:
        line[:, :2] -= coordinate[None, ...]
        line = transform_points_directly(line[:, :2], ego_vec, current_vec)
        output_boundary.append(line)
    output = {}
    output['centerline'] = output_centerline
    output['boundary'] = output_boundary
    return output

def rot_and_trans(input_map, current_pose):
    centerline = input_map['centerline'].copy()
    boundary = input_map['boundary'].copy()
    output = {}
    current_pose = np.array(current_pose)
    coordinate = current_pose[0:2]
    current_vec = current_pose[5:7] - current_pose[3:5]
    ego_vec = np.array([1.0, 0.0])
    centerline[:, 0:2] -= coordinate
    centerline[:, 2:4] -= coordinate
    boundary[:, 0:2] -= coordinate
    boundary[:, 2:4] -= coordinate
    centerline[:, 0:2] = transform_points_directly(centerline[:, 0:2], ego_vec, current_vec)
    centerline[:, 2:4] = transform_points_directly(centerline[:, 2:4], ego_vec, current_vec)
    boundary[:, 0:2] = transform_points_directly(boundary[:, 0:2], ego_vec, current_vec)
    boundary[:, 2:4] = transform_points_directly(boundary[:, 2:4], ego_vec, current_vec)
    output['centerline'] = centerline
    output['boundary'] = boundary
    return output

def rot_and_trans_bbox(input_bbox, current_pose):
    output_bbox = input_bbox.copy()
    if input_bbox.shape[0] == 0:
        return output_bbox
    current_pose = np.array(current_pose)
    coordinate = current_pose[0:2]
    current_vec = current_pose[5:7] - current_pose[3:5]
    ego_vec = np.array([1.0, 0.0])
    output_bbox = output_bbox.reshape((-1, 2))
    output_bbox[:, 0:2] -= coordinate
    output_bbox[:, 0:2] = transform_points_directly(output_bbox[:, 0:2], ego_vec, current_vec)
    output_bbox = output_bbox.reshape((-1, 4, 2))
    return output_bbox

def inverse_rot_and_trans(input, current_pose):
    current_pose = np.array(current_pose).copy()
    input = np.array(input)
    coordinate = current_pose[0:2]
    current_vec = current_pose[5:7] - current_pose[3:5]
    ego_vec = np.array([1.0, 0.0])
    output = transform_points_directly(input, current_vec, ego_vec)
    output += coordinate
    return output

def rotate(point, angle):
    """Rotates a point around the origin by the specified angle in radians."""
    rotation_matrix = np.array([[np.cos(angle), -np.sin(angle), 0], [np.sin(angle), np.cos(angle), 0], [0, 0, 1]])
    return np.dot(rotation_matrix, point)

def generate_vertices(car):
    """Generates the vertices of a 3D box."""
    x = car['cx']
    y = car['cy']
    z = car['cz']
    length = car['length']
    width = car['width']
    height = car['height']
    heading = car['heading']
    box_center = np.array([x, y, z])
    half_dims = np.array([length / 2, width / 2, height / 2])
    relative_positions = np.array([[-1, -1, -1], [-1, -1, 1], [-1, 1, -1], [-1, 1, 1], [1, -1, -1], [1, -1, 1], [1, 1, -1], [1, 1, 1]]) * half_dims
    vertices = np.asarray([rotate(pos, heading) + box_center for pos in relative_positions])
    return vertices

def compute_bezier_points(p0, p1, p2, p3, num_points=100):
    return np.array([cubic_bezier(p0, p1, p2, p3, t) for t in np.linspace(0, 1, num_points)])

def is_tailgating(trajectory1, trajectory2):
    threshold = 0.2
    speed1 = np.diff(trajectory1, axis=0)
    speed2 = np.diff(trajectory2, axis=0)
    direction = trajectory2[t] - trajectory1[t]
    speed_direction1 = speed1[t - 1] / np.linalg.norm(speed1[t - 1])
    speed_direction2 = speed2[t - 1] / np.linalg.norm(speed2[t - 1])
    angle1 = np.arccos(np.clip(np.dot(direction, speed_direction1), -1.0, 1.0))
    angle2 = np.arccos(np.clip(np.dot(-direction, speed_direction2), -1.0, 1.0))
    if angle1 < threshold and angle2 < threshold:
        return True
    else:
        return False

def visualize_placement(input_position, input_map):
    centerline = input_map['centerline']
    boundary = input_map['boundary']
    plt.cla()
    for i in range(len(centerline)):
        lane_vec = centerline[i]
        plt.plot([lane_vec[0], lane_vec[2]], [lane_vec[1], lane_vec[3]], color='green', linewidth=1)
        plt.scatter([lane_vec[0], lane_vec[2]], [lane_vec[1], lane_vec[3]], color='black', s=1)
    for i in range(len(boundary)):
        lane_vec = boundary[i]
        plt.plot([lane_vec[0], lane_vec[2]], [lane_vec[1], lane_vec[3]], color='red', linewidth=1)
        plt.scatter([lane_vec[0], lane_vec[2]], [lane_vec[1], lane_vec[3]], color='black', s=1)
    vehicle_size_x = 2
    vehicle_size_y = 4.5
    l, w = (vehicle_size_y / 2, vehicle_size_x / 2)
    for item in input_position:
        if item[0] is not None:
            xc, yc, theta, xs, ys, xe, ye = item
            theta = np.arctan2(xe - xs, ye - ys)
            x1, y1 = (xc - w * np.cos(theta) + l * np.sin(theta), yc + l * np.cos(theta) + w * np.sin(theta))
            x2, y2 = (xc + w * np.cos(theta) + l * np.sin(theta), yc + l * np.cos(theta) - w * np.sin(theta))
            x3, y3 = (xc + w * np.cos(theta) - l * np.sin(theta), yc - l * np.cos(theta) - w * np.sin(theta))
            x4, y4 = (xc - w * np.cos(theta) - l * np.sin(theta), yc - l * np.cos(theta) + w * np.sin(theta))

def find_closest_centerline(transformed_map_data, current_destination):
    thres = 0.3
    current_destination = np.array(current_destination)
    centerlines = transformed_map_data['centerline']
    centernodes = (centerlines[:, 0:2] + centerlines[:, 2:4]) / 2
    distances = np.linalg.norm(current_destination[None] - centernodes, axis=-1, ord=2)
    closest_centerline_index = np.argmin(distances)
    if distances[closest_centerline_index] < thres:
        return (True, centerlines[closest_centerline_index])
    else:
        return (False, centerlines[closest_centerline_index])

def bspline_smooth(points, degree=3):
    if points is not None:
        points = np.array(points)
        x = np.linspace(0, 1, len(points))
        bspline = BSpline(x, points, k=degree)
        x_new = np.linspace(0, 1, len(points))
        points_smoothed = bspline(x_new)
        return points_smoothed
    return None

def vehicle_motion(map_data, all_current_vertices, placement_result=[], high_level_action_direction=[], high_level_action_speed=[], dt=0.4, total_len=10):
    if placement_result[0] is None:
        return (None, 'no placement')
    if high_level_action_direction == 'static':
        return np.array(placement_result[0:2])[None, ...].repeat(total_len, axis=0)
    slow_speed_threshold = (1.5, 2)
    fast_speed_threshold = (10, 25)
    random_speed_threshold = (3, 25)
    current_position = placement_result
    transformed_map_data = rot_and_trans(map_data, current_position)
    transformed_all_current_vertices = rot_and_trans_bbox(all_current_vertices, current_position)
    if high_level_action_speed == 'slow':
        v_init = random.uniform(slow_speed_threshold[0], slow_speed_threshold[1])
    elif high_level_action_speed == 'fast':
        v_init = random.randint(fast_speed_threshold[0], fast_speed_threshold[1])
    else:
        v_init = random.randint(random_speed_threshold[0], random_speed_threshold[1])
    transformed_map_data = filter_forward_lane(transformed_map_data)
    if high_level_action_direction == 'turn left':
        transformed_map_data_dest = filter_left_lane(transformed_map_data)
    elif high_level_action_direction == 'turn right':
        transformed_map_data_dest = filter_right_lane(transformed_map_data)
    if high_level_action_direction == 'turn left' or high_level_action_direction == 'turn right':
        destination_anchor = transformed_map_data_dest['centerline'][::5]
        print(destination_anchor)
        sorted_destination = destination_anchor[random.randint(0, len(destination_anchor) - 1)]
        sorted_destination_direction = sorted_destination[2:4] - sorted_destination[0:2]
        sorted_destination = sorted_destination[:2]
    elif high_level_action_direction == 'straight':
        sorted_destination_init = np.array([v_init * dt * total_len, 0])
        _, sorted_destination = find_closest_centerline(transformed_map_data, sorted_destination_init)
        sorted_destination_direction = sorted_destination[2:4] - sorted_destination[0:2]
        sorted_destination = (sorted_destination[0:2] + sorted_destination[2:4]) / 2
    start = np.array([0, 0])
    end = np.array([sorted_destination[0], sorted_destination[1]])
    Vs = np.array([v_init, 0])
    Ve = v_init * sorted_destination_direction / np.linalg.norm(sorted_destination_direction)
    Ve = np.abs(Ve)
    coordinates = hermite_spline_once(start, end, Vs, Ve)
    current_midpoint = coordinates[-int(len(coordinates) / 2)]
    midpoint_check_flag, closest_centerline = find_closest_centerline(transformed_map_data, current_midpoint)
    midpoint = (closest_centerline[0:2] + closest_centerline[2:4]) / 2
    midpoint_direction = closest_centerline[2:4] - closest_centerline[0:2]
    Vm = v_init * midpoint_direction / np.linalg.norm(midpoint_direction)
    Vm = np.abs(Vm)
    coordinates = hermite_spline_twice(start, end, midpoint, Vs, Ve, Vm)
    generated_trajectory = np.array(coordinates[::int(len(coordinates) / total_len)])
    generated_trajectory = check_collision_and_revise_static(generated_trajectory, transformed_all_current_vertices)
    generated_trajectory = inverse_rot_and_trans(generated_trajectory, current_position)
    return generated_trajectory

def get_angle_from_line_to_line(ego_lane_vec_heading, cur_lane_vec_heading):
    cosangle = ego_lane_vec_heading.dot(cur_lane_vec_heading) / (np.linalg.norm(ego_lane_vec_heading) * np.linalg.norm(cur_lane_vec_heading))
    angle = np.arccos(cosangle) * 180 / np.pi
    a1 = np.array([*ego_lane_vec_heading, 0])
    a2 = np.array([*cur_lane_vec_heading, 0])
    a3 = np.cross(a1, a2)
    if np.sign(a3[2]) < 0:
        angle = 360 - angle
    return angle

def rotate(point, angle):
    """Rotates a point around the origin by the specified angle in radians."""
    rotation_matrix = np.array([[np.cos(angle), -np.sin(angle), 0], [np.sin(angle), np.cos(angle), 0], [0, 0, 1]])
    return np.dot(rotation_matrix, point)

def generate_vertices(car):
    """Generates the vertices of a 3D box."""
    x = car['cx']
    y = car['cy']
    z = car['cz']
    length = car['length']
    width = car['width']
    height = car['height']
    heading = car['heading']
    box_center = np.array([x, y, z])
    half_dims = np.array([length / 2, width / 2, height / 2])
    relative_positions = np.array([[-1, -1, -1], [-1, -1, 1], [-1, 1, -1], [-1, 1, 1], [1, -1, -1], [1, -1, 1], [1, 1, -1], [1, 1, 1]]) * half_dims
    vertices = np.asarray([rotate(pos, heading) + box_center for pos in relative_positions])
    return vertices

def vehicle_placement_specific(input_map, current_vertices, coord):
    centerline = input_map['centerline']
    boundary = input_map['boundary']
    plt.cla()
    print(coord)
    print(centerline[:, 0:2])
    for i in range(len(centerline)):
        lane_vec = centerline[i]
        plt.plot([lane_vec[0], lane_vec[2]], [lane_vec[1], lane_vec[3]], color='green', linewidth=1)
        plt.scatter([lane_vec[0], lane_vec[2]], [lane_vec[1], lane_vec[3]], color='black', s=1)
    for i in range(len(boundary)):
        lane_vec = boundary[i]
        plt.plot([lane_vec[0], lane_vec[2]], [lane_vec[1], lane_vec[3]], color='red', linewidth=1)
        plt.scatter([lane_vec[0], lane_vec[2]], [lane_vec[1], lane_vec[3]], color='black', s=1)
    center_coord = (centerline[:, 0:2] + centerline[:, 2:4]) / 2
    distance = np.linalg.norm(coord[None] - center_coord, ord=2, axis=-1)
    closest_distance_index = np.argmin(distance)
    lane_vec = centerline[closest_distance_index]
    x, y = (coord[0], coord[1])
    xs, ys, xe, ye = (lane_vec[0], lane_vec[1], lane_vec[2], lane_vec[3])
    theta = np.arctan2(xe - xs, ye - ys)
    return (x, y, theta, xs, ys, xe, ye)

def vehicle_placement(input_map, current_vertices, direction, vehicle_mode, distance_constraint, distance_min_max, vehicle_size):
    centerline = input_map['centerline']
    boundary = input_map['boundary']
    plt.cla()
    for i in range(len(centerline)):
        lane_vec = centerline[i]
        plt.plot([lane_vec[0], lane_vec[2]], [lane_vec[1], lane_vec[3]], color='green', linewidth=1)
        plt.scatter([lane_vec[0], lane_vec[2]], [lane_vec[1], lane_vec[3]], color='black', s=1)
    for i in range(len(boundary)):
        lane_vec = boundary[i]
        plt.plot([lane_vec[0], lane_vec[2]], [lane_vec[1], lane_vec[3]], color='red', linewidth=1)
        plt.scatter([lane_vec[0], lane_vec[2]], [lane_vec[1], lane_vec[3]], color='black', s=1)
    valid_lane_list = []
    ego_index = 0
    ego_dist = 999
    for i in range(centerline.shape[0]):
        valid_lane_list.append(i)
        center_coord = (centerline[i, 0:2] + centerline[i, 2:4]) / 2
        if np.linalg.norm(center_coord, ord=2) < ego_dist:
            ego_index = i
            ego_dist = np.linalg.norm(center_coord, ord=2)
    ego_lane_vec = centerline[ego_index]
    input_map = centerline
    vehicle_size_x = 2
    vehicle_size_y = 4.5
    distance_min_default = 4
    distance_max_default = 45
    front_placement_distance_threshold = 8
    left_front_placement_distance_threshold = (1.5, 10)
    left_front_placement_theta_threshold = (3, 60)
    right_front_placement_distance_threshold = (1.5, 10)
    right_front_placement_theta_threshold = (300, 357)
    left_placement_distance_threshold = (1.5, 10)
    left_placement_theta_threshold = (75, 105)
    right_placement_distance_threshold = (1.5, 10)
    right_placement_theta_threshold = (255, 285)
    mode = vehicle_mode
    if distance_constraint:
        distance_min = float(distance_min_max[0]) + 4
        distance_max = float(distance_min_max[1]) + 4
    l, w = (vehicle_size_y / 2, vehicle_size_x / 2)
    if mode == 'random':
        while True:
            cur_valid_lane_index_list = []
            for i in range(len(valid_lane_list)):
                center_coord = (input_map[valid_lane_list[i], 0:2] + input_map[valid_lane_list[i], 2:4]) / 2
                if not distance_constraint:
                    distance_min = distance_min_default
                    distance_max = distance_max_default
                if np.linalg.norm(center_coord, ord=2) >= distance_min and np.linalg.norm(center_coord, ord=2) <= distance_max:
                    if direction == 'close' and input_map[valid_lane_list[i], -1] == 0:
                        cur_valid_lane_index_list.append(valid_lane_list[i])
                    elif direction == 'away' and input_map[valid_lane_list[i], -1] == 1:
                        cur_valid_lane_index_list.append(valid_lane_list[i])
                    elif direction == 'random':
                        cur_valid_lane_index_list.append(valid_lane_list[i])
            try:
                random_lane_index = random.randint(0, len(cur_valid_lane_index_list) - 1)
                index = cur_valid_lane_index_list[random_lane_index]
            except:
                return (None, 'No place to put cars')
                index = -1
                break
            del valid_lane_list[random_lane_index]
            if conflict_check(centerline, index, current_vertices):
                break
            if len(valid_lane_list) <= 0:
                print('exceed the maximum number of vehicle')
                break
    elif mode == 'front':
        while True:
            cur_valid_lane_index_list = []
            for i in range(len(valid_lane_list)):
                cur_lane_vec = input_map[valid_lane_list[i]]
                center_coord = (cur_lane_vec[0:2] + cur_lane_vec[2:4]) / 2
                dist_to_lane_vec = abs(center_coord[1])
                if not distance_constraint:
                    distance_min = distance_min_default
                    distance_max = distance_max_default
                if np.linalg.norm(center_coord, ord=2) <= distance_max and np.linalg.norm(center_coord, ord=2) >= distance_min and (dist_to_lane_vec < front_placement_distance_threshold) and (center_coord[0] > 0):
                    if direction == 'close' and input_map[valid_lane_list[i], -1] == 0:
                        cur_valid_lane_index_list.append(valid_lane_list[i])
                    elif direction == 'away' and input_map[valid_lane_list[i], -1] == 1:
                        cur_valid_lane_index_list.append(valid_lane_list[i])
                    elif direction == 'random':
                        cur_valid_lane_index_list.append(valid_lane_list[i])
            try:
                random_lane_index = random.randint(0, len(cur_valid_lane_index_list) - 1)
                index = cur_valid_lane_index_list[random_lane_index]
            except:
                return (None, 'No place to put front cars')
                index = -1
                break
            del valid_lane_list[random_lane_index]
            if conflict_check(centerline, index, current_vertices):
                break
            if len(valid_lane_list) <= 0:
                print('exceed the maximum number of vehicle')
                break
    elif mode == 'left front':
        while True:
            cur_valid_lane_index_list = []
            ego_lane_vec_heading = np.array([1.0, 0.0])
            for i in range(len(valid_lane_list)):
                cur_lane_vec = input_map[valid_lane_list[i]]
                center_coord = (cur_lane_vec[0:2] + cur_lane_vec[2:4]) / 2
                dist_to_lane_vec = abs(center_coord[1])
                cur_lane_vec_heading = center_coord - ego_lane_vec[0:2]
                theta = get_angle_from_line_to_line(ego_lane_vec_heading, cur_lane_vec_heading)
                if not distance_constraint:
                    distance_min = distance_min_default
                    distance_max = distance_max_default
                if np.linalg.norm(center_coord, ord=2) <= distance_max and np.linalg.norm(center_coord, ord=2) >= distance_min and (dist_to_lane_vec >= left_front_placement_distance_threshold[0]) and (dist_to_lane_vec <= left_front_placement_distance_threshold[1]) and (theta >= left_front_placement_theta_threshold[0]) and (theta <= left_front_placement_theta_threshold[1]):
                    if direction == 'close' and input_map[valid_lane_list[i], -1] == 0:
                        cur_valid_lane_index_list.append(valid_lane_list[i])
                    elif direction == 'away' and input_map[valid_lane_list[i], -1] == 1:
                        cur_valid_lane_index_list.append(valid_lane_list[i])
                    elif direction == 'random':
                        cur_valid_lane_index_list.append(valid_lane_list[i])
            try:
                random_lane_index = random.randint(0, len(cur_valid_lane_index_list) - 1)
                index = cur_valid_lane_index_list[random_lane_index]
            except:
                index = -1
                return (None, 'No place to put left front cars')
                break
            del valid_lane_list[random_lane_index]
            if conflict_check(centerline, index, current_vertices):
                break
            if len(valid_lane_list) <= 0:
                print('exceed the maximum number of vehicle')
                break
    elif mode == 'right front':
        while True:
            cur_valid_lane_index_list = []
            ego_lane_vec_heading = ego_lane_vec_heading = np.array([1.0, 0.0])
            for i in range(len(valid_lane_list)):
                cur_lane_vec = input_map[valid_lane_list[i]]
                center_coord = (cur_lane_vec[0:2] + cur_lane_vec[2:4]) / 2
                dist_to_lane_vec = abs(center_coord[1])
                cur_lane_vec_heading = center_coord - ego_lane_vec[0:2]
                theta = get_angle_from_line_to_line(ego_lane_vec_heading, cur_lane_vec_heading)
                if not distance_constraint:
                    distance_min = distance_min_default
                    distance_max = distance_max_default
                if np.linalg.norm(center_coord, ord=2) <= distance_max and np.linalg.norm(center_coord, ord=2) >= distance_min and (dist_to_lane_vec >= right_front_placement_distance_threshold[0]) and (dist_to_lane_vec <= right_front_placement_distance_threshold[1]) and (theta >= right_front_placement_theta_threshold[0]) and (theta <= right_front_placement_theta_threshold[1]):
                    if direction == 'close' and input_map[valid_lane_list[i], -1] == 0:
                        cur_valid_lane_index_list.append(valid_lane_list[i])
                    elif direction == 'away' and input_map[valid_lane_list[i], -1] == 1:
                        cur_valid_lane_index_list.append(valid_lane_list[i])
                    elif direction == 'random':
                        cur_valid_lane_index_list.append(valid_lane_list[i])
            try:
                random_lane_index = random.randint(0, len(cur_valid_lane_index_list) - 1)
                index = cur_valid_lane_index_list[random_lane_index]
            except:
                index = -1
                return (None, 'No place to put right front cars')
                break
            del valid_lane_list[random_lane_index]
            if conflict_check(centerline, index, current_vertices):
                break
            if len(valid_lane_list) <= 0:
                print('exceed the maximum number of vehicle')
                break
    elif mode == 'left':
        while True:
            cur_valid_lane_index_list = []
            ego_lane_vec_heading = ego_lane_vec_heading = np.array([1.0, 0.0])
            for i in range(len(valid_lane_list)):
                cur_lane_vec = input_map[valid_lane_list[i]]
                center_coord = (cur_lane_vec[0:2] + cur_lane_vec[2:4]) / 2
                dist_to_lane_vec = abs(center_coord[1])
                cur_lane_vec_heading = center_coord - ego_lane_vec[0:2]
                theta = get_angle_from_line_to_line(ego_lane_vec_heading, cur_lane_vec_heading)
                if not distance_constraint:
                    distance_min = distance_min_default
                    distance_max = distance_max_default
                if np.linalg.norm(center_coord, ord=2) <= distance_max and np.linalg.norm(center_coord, ord=2) >= distance_min and (dist_to_lane_vec >= left_placement_distance_threshold[0]) and (dist_to_lane_vec <= left_placement_distance_threshold[1]) and (theta > left_placement_theta_threshold[0]) and (theta <= left_placement_theta_threshold[1]):
                    if direction == 'close' and input_map[valid_lane_list[i], -1] == 0:
                        cur_valid_lane_index_list.append(valid_lane_list[i])
                    elif direction == 'away' and input_map[valid_lane_list[i], -1] == 1:
                        cur_valid_lane_index_list.append(valid_lane_list[i])
                    elif direction == 'random':
                        cur_valid_lane_index_list.append(valid_lane_list[i])
            try:
                random_lane_index = random.randint(0, len(cur_valid_lane_index_list) - 1)
                index = cur_valid_lane_index_list[random_lane_index]
            except:
                index = -1
                return (None, 'No place to put cars on the left')
                break
            del valid_lane_list[random_lane_index]
            if conflict_check(centerline, index, current_vertices):
                break
            if len(valid_lane_list) <= 0:
                print('exceed the maximum number of vehicle')
                break
    elif mode == 'right':
        while True:
            cur_valid_lane_index_list = []
            ego_lane_vec_heading = ego_lane_vec_heading = np.array([1.0, 0.0])
            for i in range(len(valid_lane_list)):
                cur_lane_vec = input_map[valid_lane_list[i]]
                center_coord = (cur_lane_vec[0:2] + cur_lane_vec[2:4]) / 2
                dist_to_lane_vec = abs(center_coord[1])
                cur_lane_vec_heading = center_coord - ego_lane_vec[0:2]
                theta = get_angle_from_line_to_line(ego_lane_vec_heading, cur_lane_vec_heading)
                if not distance_constraint:
                    distance_min = distance_min_default
                    distance_max = distance_max_default
                if np.linalg.norm(center_coord, ord=2) <= distance_max and np.linalg.norm(center_coord, ord=2) >= distance_min and (dist_to_lane_vec >= right_placement_distance_threshold[0]) and (dist_to_lane_vec <= right_placement_distance_threshold[1]) and (theta > right_placement_theta_threshold[0]) and (theta < right_placement_theta_threshold[1]):
                    if direction == 'close' and input_map[valid_lane_list[i], -1] == 0:
                        cur_valid_lane_index_list.append(valid_lane_list[i])
                    elif direction == 'away' and input_map[valid_lane_list[i], -1] == 1:
                        cur_valid_lane_index_list.append(valid_lane_list[i])
                    elif direction == 'random':
                        cur_valid_lane_index_list.append(valid_lane_list[i])
            try:
                random_lane_index = random.randint(0, len(cur_valid_lane_index_list) - 1)
                index = cur_valid_lane_index_list[random_lane_index]
            except:
                index = -1
                return (None, 'No place to put cars on the right')
                break
            del valid_lane_list[random_lane_index]
            if conflict_check(centerline, index, current_vertices):
                break
            if len(valid_lane_list) <= 0:
                print('exceed the maximum number of vehicle')
                break
    if index < 0:
        return (None, 'No place to put cars')
    lane_vec = input_map[index]
    xs, ys, xe, ye = (lane_vec[0], lane_vec[1], lane_vec[2], lane_vec[3])
    xc, yc = ((xs + xe) / 2, (ys + ye) / 2)
    theta = np.arctan2(xe - xs, ye - ys)
    x1, y1 = (xc - w * np.cos(theta) + l * np.sin(theta), yc + l * np.cos(theta) + w * np.sin(theta))
    x2, y2 = (xc + w * np.cos(theta) + l * np.sin(theta), yc + l * np.cos(theta) - w * np.sin(theta))
    x3, y3 = (xc + w * np.cos(theta) - l * np.sin(theta), yc - l * np.cos(theta) - w * np.sin(theta))
    x4, y4 = (xc - w * np.cos(theta) - l * np.sin(theta), yc - l * np.cos(theta) + w * np.sin(theta))
    return (xc, yc, theta, xs, ys, xe, ye)

