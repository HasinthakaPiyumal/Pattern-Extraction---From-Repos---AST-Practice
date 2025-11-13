# Cluster 10

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

class _iterator:

    def __init__(self, dataPtr):
        self.dataPtr = dataPtr
        self.currentElement = 0
        self.elementNames = ['x', 'y', 'z', 'w']

    def __iter__(self):
        return self

    def next(self):
        return self.__next__()

    def __next__(self):
        element = self.currentElement
        if self.currentElement >= 4:
            raise StopIteration
        self.currentElement = self.currentElement + 1
        item = self.dataPtr.dereference()
        self.dataPtr = self.dataPtr + 1
        return ('[%s]' % (self.elementNames[element],), item)

def __init__(self, dataPtr):
    self.dataPtr = dataPtr
    self.currentElement = 0
    self.elementNames = ['x', 'y', 'z', 'w']

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

class Camera(nn.Module):

    def __init__(self, colmap_id, R, T, FoVx, FoVy, image, gt_alpha_mask, image_name, uid, trans=np.array([0.0, 0.0, 0.0]), scale=1.0, data_device='cuda', K=None, sky_mask=None, normal=None, depth=None, exposure_scale=None):
        super(Camera, self).__init__()
        self.uid = uid
        self.colmap_id = colmap_id
        self.R = R
        self.T = T
        self.FoVx = FoVx
        self.FoVy = FoVy
        self.image_name = image_name
        self.K = K
        self.sky_mask = sky_mask
        self.normal = normal
        self.depth = depth
        self.exposure_scale = exposure_scale
        try:
            self.data_device = torch.device(data_device)
        except Exception as e:
            print(e)
            print(f'[Warning] Custom device {data_device} failed, fallback to default cuda device')
            self.data_device = torch.device('cuda')
        self.original_image = image.clamp(0.0, 1.0).to(self.data_device)
        self.image_width = self.original_image.shape[2]
        self.image_height = self.original_image.shape[1]
        if gt_alpha_mask is not None:
            self.original_image *= gt_alpha_mask.to(self.data_device)
        else:
            self.original_image *= torch.ones((1, self.image_height, self.image_width), device=self.data_device)
        self.zfar = 100.0
        self.znear = 0.01
        self.trans = trans
        self.scale = scale
        self.world_view_transform = torch.tensor(getWorld2View2(R, T, trans, scale)).transpose(0, 1).cuda()
        self.projection_matrix = getProjectionMatrixFromK(self.znear, self.zfar, self.image_width, self.image_height, self.K).transpose(0, 1).cuda()
        self.full_proj_transform = self.world_view_transform.unsqueeze(0).bmm(self.projection_matrix.unsqueeze(0)).squeeze(0)
        self.camera_center = self.world_view_transform.inverse()[3, :3]

def __init__(self, colmap_id, R, T, FoVx, FoVy, image, gt_alpha_mask, image_name, uid, trans=np.array([0.0, 0.0, 0.0]), scale=1.0, data_device='cuda', K=None, sky_mask=None, normal=None, depth=None, exposure_scale=None):
    super(Camera, self).__init__()
    self.uid = uid
    self.colmap_id = colmap_id
    self.R = R
    self.T = T
    self.FoVx = FoVx
    self.FoVy = FoVy
    self.image_name = image_name
    self.K = K
    self.sky_mask = sky_mask
    self.normal = normal
    self.depth = depth
    self.exposure_scale = exposure_scale
    try:
        self.data_device = torch.device(data_device)
    except Exception as e:
        print(e)
        print(f'[Warning] Custom device {data_device} failed, fallback to default cuda device')
        self.data_device = torch.device('cuda')
    self.original_image = image.clamp(0.0, 1.0).to(self.data_device)
    self.image_width = self.original_image.shape[2]
    self.image_height = self.original_image.shape[1]
    if gt_alpha_mask is not None:
        self.original_image *= gt_alpha_mask.to(self.data_device)
    else:
        self.original_image *= torch.ones((1, self.image_height, self.image_width), device=self.data_device)
    self.zfar = 100.0
    self.znear = 0.01
    self.trans = trans
    self.scale = scale
    self.world_view_transform = torch.tensor(getWorld2View2(R, T, trans, scale)).transpose(0, 1).cuda()
    self.projection_matrix = getProjectionMatrixFromK(self.znear, self.zfar, self.image_width, self.image_height, self.K).transpose(0, 1).cuda()
    self.full_proj_transform = self.world_view_transform.unsqueeze(0).bmm(self.projection_matrix.unsqueeze(0)).squeeze(0)
    self.camera_center = self.world_view_transform.inverse()[3, :3]

class MiniCam:

    def __init__(self, width, height, fovy, fovx, znear, zfar, world_view_transform, full_proj_transform):
        self.image_width = width
        self.image_height = height
        self.FoVy = fovy
        self.FoVx = fovx
        self.znear = znear
        self.zfar = zfar
        self.world_view_transform = world_view_transform
        self.full_proj_transform = full_proj_transform
        view_inv = torch.inverse(self.world_view_transform)
        self.camera_center = view_inv[3][:3]

def __init__(self, width, height, fovy, fovx, znear, zfar, world_view_transform, full_proj_transform):
    self.image_width = width
    self.image_height = height
    self.FoVy = fovy
    self.FoVx = fovx
    self.znear = znear
    self.zfar = zfar
    self.world_view_transform = world_view_transform
    self.full_proj_transform = full_proj_transform
    view_inv = torch.inverse(self.world_view_transform)
    self.camera_center = view_inv[3][:3]

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

def __init__(self, num_encoding_functions, include_input=True):
    super().__init__()
    self.num_encoding_functions = num_encoding_functions
    self.include_input = include_input

class SkyMlp(nn.Module):

    def __init__(self, sky_model_args):
        super(SkyMlp, self).__init__()
        num_encoding_functions = sky_model_args.num_encoding_functions
        hidden_dim = sky_model_args.hidden_dim
        self.positional_encoding = PositionalEncoding(num_encoding_functions)
        self.fc1 = nn.Linear(3 + 3 * 2 * num_encoding_functions, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, 3)
        self.relu = nn.ReLU()

    def capture(self):
        return self.state_dict()

    def train_params(self):
        return self.parameters()

    def restore(self, model_args):
        self.load_state_dict(model_args)

    def _forward(self, view_dir):
        """
        Input:
            view_dir: torch.Tensor of shape [batch_size, num_samples, 3]
        Returns:
            rgb: torch.Tensor of shape [batch_size, num_samples, 3]
        """
        x = self.positional_encoding(view_dir)
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        x = self.relu(x)
        x = self.fc3(x)
        return x

    def forward(self, viewpoint_camera):
        c2w = torch.linalg.inv(viewpoint_camera.world_view_transform.transpose(0, 1))
        ray_d_world = get_ray_directions(viewpoint_camera.image_height, viewpoint_camera.image_width, viewpoint_camera.FoVx, viewpoint_camera.FoVy, c2w).cuda()
        ray_d_world_batch = ray_d_world.view(1, -1, 3)
        skymap = self._forward(ray_d_world_batch).view(viewpoint_camera.image_height, viewpoint_camera.image_width, 3).permute(2, 0, 1)
        return skymap

def __init__(self, sky_model_args):
    super(SkyMlp, self).__init__()
    num_encoding_functions = sky_model_args.num_encoding_functions
    hidden_dim = sky_model_args.hidden_dim
    self.positional_encoding = PositionalEncoding(num_encoding_functions)
    self.fc1 = nn.Linear(3 + 3 * 2 * num_encoding_functions, hidden_dim)
    self.fc2 = nn.Linear(hidden_dim, hidden_dim)
    self.fc3 = nn.Linear(hidden_dim, 3)
    self.relu = nn.ReLU()

def train_params(self):
    return self.parameters()

class SkyCube(torch.nn.Module):

    def __init__(self, sky_model_args):
        super().__init__()
        resolution = sky_model_args.resolution
        self.waymo_to_opengl = torch.tensor([[0, -1, 0], [0, 0, 1], [-1, 0, 0]], dtype=torch.float32, device='cuda')
        self.base = torch.nn.Parameter(0.5 * torch.ones(6, resolution, resolution, 3, requires_grad=True))

    def capture(self):
        return self.base

    def train_params(self):
        return [self.base]

    def restore(self, model_args):
        self.base = model_args

    def _forward(self, l):
        import nvdiffrast.torch as dr
        l = (l.reshape(-1, 3) @ self.waymo_to_opengl.T).reshape(*l.shape)
        l = l.contiguous()
        prefix = l.shape[:-1]
        if len(prefix) != 3:
            l = l.reshape(1, 1, -1, l.shape[-1])
        light = dr.texture(self.base[None, ...], l, filter_mode='linear', boundary_mode='cube')
        light = light.view(*prefix, -1)
        return light

    def forward(self, viewpoint_camera):
        c2w = torch.linalg.inv(viewpoint_camera.world_view_transform.transpose(0, 1))
        ray_d_world = get_ray_directions(viewpoint_camera.image_height, viewpoint_camera.image_width, viewpoint_camera.FoVx, viewpoint_camera.FoVy, c2w).cuda()
        skymap = self._forward(ray_d_world)
        skymap = skymap.permute(2, 0, 1)
        return skymap

def __init__(self, sky_model_args):
    super().__init__()
    resolution = sky_model_args.resolution
    self.waymo_to_opengl = torch.tensor([[0, -1, 0], [0, 0, 1], [-1, 0, 0]], dtype=torch.float32, device='cuda')
    self.base = torch.nn.Parameter(0.5 * torch.ones(6, resolution, resolution, 3, requires_grad=True))

class ModelParams(ParamGroup):

    def __init__(self, parser, sentinel=False):
        self.sh_degree = 3
        self._source_path = ''
        self._model_path = ''
        self._images = 'images'
        self._resolution = -1
        self._white_background = False
        self.data_device = 'cuda'
        self.eval = False
        super().__init__(parser, 'Loading Parameters', sentinel)

    def extract(self, args):
        g = super().extract(args)
        g.source_path = os.path.abspath(g.source_path)
        return g

def __init__(self, parser, sentinel=False):
    self.sh_degree = 3
    self._source_path = ''
    self._model_path = ''
    self._images = 'images'
    self._resolution = -1
    self._white_background = False
    self.data_device = 'cuda'
    self.eval = False
    super().__init__(parser, 'Loading Parameters', sentinel)

def extract(self, args):
    g = super().extract(args)
    g.source_path = os.path.abspath(g.source_path)
    return g

class PipelineParams(ParamGroup):

    def __init__(self, parser):
        self.convert_SHs_python = False
        self.compute_cov3D_python = False
        self.debug = False
        super().__init__(parser, 'Pipeline Parameters')

def __init__(self, parser):
    self.convert_SHs_python = False
    self.compute_cov3D_python = False
    self.debug = False
    super().__init__(parser, 'Pipeline Parameters')

class OptimizationParams(ParamGroup):

    def __init__(self, parser):
        self.iterations = 30000
        self.position_lr_init = 0.00016
        self.position_lr_final = 1.6e-06
        self.position_lr_delay_mult = 0.01
        self.position_lr_max_steps = 30000
        self.feature_lr = 0.0025
        self.opacity_lr = 0.05
        self.scaling_lr = 0.005
        self.rotation_lr = 0.001
        self.percent_dense = 0.01
        self.lambda_dssim = 0.2
        self.densification_interval = 100
        self.opacity_reset_interval = 3000
        self.densify_from_iter = 500
        self.densify_until_iter = 15000
        self.densify_grad_threshold = 0.0002
        self.random_background = False
        super().__init__(parser, 'Optimization Parameters')

def __init__(self, parser):
    self.iterations = 30000
    self.position_lr_init = 0.00016
    self.position_lr_final = 1.6e-06
    self.position_lr_delay_mult = 0.01
    self.position_lr_max_steps = 30000
    self.feature_lr = 0.0025
    self.opacity_lr = 0.05
    self.scaling_lr = 0.005
    self.rotation_lr = 0.001
    self.percent_dense = 0.01
    self.lambda_dssim = 0.2
    self.densification_interval = 100
    self.opacity_reset_interval = 3000
    self.densify_from_iter = 500
    self.densify_until_iter = 15000
    self.densify_grad_threshold = 0.0002
    self.random_background = False
    super().__init__(parser, 'Optimization Parameters')

class LPIPS(nn.Module):
    """Creates a criterion that measures
    Learned Perceptual Image Patch Similarity (LPIPS).

    Arguments:
        net_type (str): the network type to compare the features: 
                        'alex' | 'squeeze' | 'vgg'. Default: 'alex'.
        version (str): the version of LPIPS. Default: 0.1.
    """

    def __init__(self, net_type: str='alex', version: str='0.1'):
        assert version in ['0.1'], 'v0.1 is only supported now'
        super(LPIPS, self).__init__()
        self.net = get_network(net_type)
        self.lin = LinLayers(self.net.n_channels_list)
        self.lin.load_state_dict(get_state_dict(net_type, version))

    def forward(self, x: torch.Tensor, y: torch.Tensor):
        feat_x, feat_y = (self.net(x), self.net(y))
        diff = [(fx - fy) ** 2 for fx, fy in zip(feat_x, feat_y)]
        res = [l(d).mean((2, 3), True) for d, l in zip(diff, self.lin)]
        return torch.sum(torch.cat(res, 0), 0, True)

def __init__(self, net_type: str='alex', version: str='0.1'):
    assert version in ['0.1'], 'v0.1 is only supported now'
    super(LPIPS, self).__init__()
    self.net = get_network(net_type)
    self.lin = LinLayers(self.net.n_channels_list)
    self.lin.load_state_dict(get_state_dict(net_type, version))

class LinLayers(nn.ModuleList):

    def __init__(self, n_channels_list: Sequence[int]):
        super(LinLayers, self).__init__([nn.Sequential(nn.Identity(), nn.Conv2d(nc, 1, 1, 1, 0, bias=False)) for nc in n_channels_list])
        for param in self.parameters():
            param.requires_grad = False

def __init__(self, n_channels_list: Sequence[int]):
    super(LinLayers, self).__init__([nn.Sequential(nn.Identity(), nn.Conv2d(nc, 1, 1, 1, 0, bias=False)) for nc in n_channels_list])
    for param in self.parameters():
        param.requires_grad = False

class BaseNet(nn.Module):

    def __init__(self):
        super(BaseNet, self).__init__()
        self.register_buffer('mean', torch.Tensor([-0.03, -0.088, -0.188])[None, :, None, None])
        self.register_buffer('std', torch.Tensor([0.458, 0.448, 0.45])[None, :, None, None])

    def set_requires_grad(self, state: bool):
        for param in chain(self.parameters(), self.buffers()):
            param.requires_grad = state

    def z_score(self, x: torch.Tensor):
        return (x - self.mean) / self.std

    def forward(self, x: torch.Tensor):
        x = self.z_score(x)
        output = []
        for i, (_, layer) in enumerate(self.layers._modules.items(), 1):
            x = layer(x)
            if i in self.target_layers:
                output.append(normalize_activation(x))
            if len(output) == len(self.target_layers):
                break
        return output

def __init__(self):
    super(BaseNet, self).__init__()
    self.register_buffer('mean', torch.Tensor([-0.03, -0.088, -0.188])[None, :, None, None])
    self.register_buffer('std', torch.Tensor([0.458, 0.448, 0.45])[None, :, None, None])

def set_requires_grad(self, state: bool):
    for param in chain(self.parameters(), self.buffers()):
        param.requires_grad = state

class SqueezeNet(BaseNet):

    def __init__(self):
        super(SqueezeNet, self).__init__()
        self.layers = models.squeezenet1_1(True).features
        self.target_layers = [2, 5, 8, 10, 11, 12, 13]
        self.n_channels_list = [64, 128, 256, 384, 384, 512, 512]
        self.set_requires_grad(False)

def __init__(self):
    super(SqueezeNet, self).__init__()
    self.layers = models.squeezenet1_1(True).features
    self.target_layers = [2, 5, 8, 10, 11, 12, 13]
    self.n_channels_list = [64, 128, 256, 384, 384, 512, 512]
    self.set_requires_grad(False)

class AlexNet(BaseNet):

    def __init__(self):
        super(AlexNet, self).__init__()
        self.layers = models.alexnet(True).features
        self.target_layers = [2, 5, 8, 10, 12]
        self.n_channels_list = [64, 192, 384, 256, 256]
        self.set_requires_grad(False)

def __init__(self):
    super(AlexNet, self).__init__()
    self.layers = models.alexnet(True).features
    self.target_layers = [2, 5, 8, 10, 12]
    self.n_channels_list = [64, 192, 384, 256, 256]
    self.set_requires_grad(False)

class VGG16(BaseNet):

    def __init__(self):
        super(VGG16, self).__init__()
        self.layers = models.vgg16(weights=models.VGG16_Weights.IMAGENET1K_V1).features
        self.target_layers = [4, 9, 16, 23, 30]
        self.n_channels_list = [64, 128, 256, 512, 512]
        self.set_requires_grad(False)

def __init__(self):
    super(VGG16, self).__init__()
    self.layers = models.vgg16(weights=models.VGG16_Weights.IMAGENET1K_V1).features
    self.target_layers = [4, 9, 16, 23, 30]
    self.n_channels_list = [64, 128, 256, 512, 512]
    self.set_requires_grad(False)

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

def __init__(self, args, tracker_target='ostrack', segmentor_target='sam', inpainter_target='sttn'):
    super().__init__()
    tracker_build_args = {'tracker_param': args.tracker_ckpt}
    inpainter_build_args = {'lama': {'lama_config': args.lama_config, 'lama_ckpt': args.lama_ckpt}, 'sttn': {'model_type': 'sttn', 'ckpt_p': args.vi_ckpt}}
    self.tracker = self.build_tracker(tracker_target, **tracker_build_args)
    self.inpainter = self.build_inpainter(inpainter_target, **inpainter_build_args[inpainter_target])
    self.tracker_target = tracker_target
    self.inpainter_target = inpainter_target

@property
def device(self):
    return 'cuda' if torch.cuda.is_available() else 'cpu'

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

@property
def device(self):
    return 'cuda' if torch.cuda.is_available() else 'cpu'

class BaseNetwork(nn.Module):

    def __init__(self):
        super(BaseNetwork, self).__init__()

    def print_network(self):
        if isinstance(self, list):
            self = self[0]
        num_params = 0
        for param in self.parameters():
            num_params += param.numel()
        print('Network [%s] was created. Total number of parameters: %.1f million. To see the architecture, do print(network).' % (type(self).__name__, num_params / 1000000))

    def init_weights(self, init_type='normal', gain=0.02):
        """
        initialize network's weights
        init_type: normal | xavier | kaiming | orthogonal
        https://github.com/junyanz/pytorch-CycleGAN-and-pix2pix/blob/9451e70673400885567d08a9e97ade2524c700d0/models/networks.py#L39
        """

        def init_func(m):
            classname = m.__class__.__name__
            if classname.find('InstanceNorm2d') != -1:
                if hasattr(m, 'weight') and m.weight is not None:
                    nn.init.constant_(m.weight.data, 1.0)
                if hasattr(m, 'bias') and m.bias is not None:
                    nn.init.constant_(m.bias.data, 0.0)
            elif hasattr(m, 'weight') and (classname.find('Conv') != -1 or classname.find('Linear') != -1):
                if init_type == 'normal':
                    nn.init.normal_(m.weight.data, 0.0, gain)
                elif init_type == 'xavier':
                    nn.init.xavier_normal_(m.weight.data, gain=gain)
                elif init_type == 'xavier_uniform':
                    nn.init.xavier_uniform_(m.weight.data, gain=1.0)
                elif init_type == 'kaiming':
                    nn.init.kaiming_normal_(m.weight.data, a=0, mode='fan_in')
                elif init_type == 'orthogonal':
                    nn.init.orthogonal_(m.weight.data, gain=gain)
                elif init_type == 'none':
                    m.reset_parameters()
                else:
                    raise NotImplementedError('initialization method [%s] is not implemented' % init_type)
                if hasattr(m, 'bias') and m.bias is not None:
                    nn.init.constant_(m.bias.data, 0.0)
        self.apply(init_func)
        for m in self.children():
            if hasattr(m, 'init_weights'):
                m.init_weights(init_type, gain)

def __init__(self):
    super(BaseNetwork, self).__init__()

class InpaintGenerator(BaseNetwork):

    def __init__(self, init_weights=True):
        super(InpaintGenerator, self).__init__()
        channel = 256
        stack_num = 8
        patchsize = [(108, 60), (36, 20), (18, 10), (9, 5)]
        blocks = []
        for _ in range(stack_num):
            blocks.append(TransformerBlock(patchsize, hidden=channel))
        self.transformer = nn.Sequential(*blocks)
        self.encoder = nn.Sequential(nn.Conv2d(3, 64, kernel_size=3, stride=2, padding=1), nn.LeakyReLU(0.2, inplace=True), nn.Conv2d(64, 64, kernel_size=3, stride=1, padding=1), nn.LeakyReLU(0.2, inplace=True), nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1), nn.LeakyReLU(0.2, inplace=True), nn.Conv2d(128, channel, kernel_size=3, stride=1, padding=1), nn.LeakyReLU(0.2, inplace=True))
        self.decoder = nn.Sequential(deconv(channel, 128, kernel_size=3, padding=1), nn.LeakyReLU(0.2, inplace=True), nn.Conv2d(128, 64, kernel_size=3, stride=1, padding=1), nn.LeakyReLU(0.2, inplace=True), deconv(64, 64, kernel_size=3, padding=1), nn.LeakyReLU(0.2, inplace=True), nn.Conv2d(64, 3, kernel_size=3, stride=1, padding=1))
        if init_weights:
            self.init_weights()

    def forward(self, masked_frames, masks):
        b, t, c, h, w = masked_frames.size()
        masks = masks.view(b * t, 1, h, w)
        enc_feat = self.encoder(masked_frames.view(b * t, c, h, w))
        _, c, h, w = enc_feat.size()
        masks = F.interpolate(masks, scale_factor=1.0 / 4)
        enc_feat = self.transformer({'x': enc_feat, 'm': masks, 'b': b, 'c': c})['x']
        output = self.decoder(enc_feat)
        output = torch.tanh(output)
        return output

    def infer(self, feat, masks):
        t, c, h, w = masks.size()
        masks = masks.view(t, c, h, w)
        masks = F.interpolate(masks, scale_factor=1.0 / 4)
        t, c, _, _ = feat.size()
        enc_feat = self.transformer({'x': feat, 'm': masks, 'b': 1, 'c': c})['x']
        return enc_feat

def __init__(self, init_weights=True):
    super(InpaintGenerator, self).__init__()
    channel = 256
    stack_num = 8
    patchsize = [(108, 60), (36, 20), (18, 10), (9, 5)]
    blocks = []
    for _ in range(stack_num):
        blocks.append(TransformerBlock(patchsize, hidden=channel))
    self.transformer = nn.Sequential(*blocks)
    self.encoder = nn.Sequential(nn.Conv2d(3, 64, kernel_size=3, stride=2, padding=1), nn.LeakyReLU(0.2, inplace=True), nn.Conv2d(64, 64, kernel_size=3, stride=1, padding=1), nn.LeakyReLU(0.2, inplace=True), nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1), nn.LeakyReLU(0.2, inplace=True), nn.Conv2d(128, channel, kernel_size=3, stride=1, padding=1), nn.LeakyReLU(0.2, inplace=True))
    self.decoder = nn.Sequential(deconv(channel, 128, kernel_size=3, padding=1), nn.LeakyReLU(0.2, inplace=True), nn.Conv2d(128, 64, kernel_size=3, stride=1, padding=1), nn.LeakyReLU(0.2, inplace=True), deconv(64, 64, kernel_size=3, padding=1), nn.LeakyReLU(0.2, inplace=True), nn.Conv2d(64, 3, kernel_size=3, stride=1, padding=1))
    if init_weights:
        self.init_weights()

class deconv(nn.Module):

    def __init__(self, input_channel, output_channel, kernel_size=3, padding=0):
        super().__init__()
        self.conv = nn.Conv2d(input_channel, output_channel, kernel_size=kernel_size, stride=1, padding=padding)

    def forward(self, x):
        x = F.interpolate(x, scale_factor=2, mode='bilinear', align_corners=True)
        return self.conv(x)

def __init__(self, input_channel, output_channel, kernel_size=3, padding=0):
    super().__init__()
    self.conv = nn.Conv2d(input_channel, output_channel, kernel_size=kernel_size, stride=1, padding=padding)

class MultiHeadedAttention(nn.Module):
    """
    Take in model size and number of heads.
    """

    def __init__(self, patchsize, d_model):
        super().__init__()
        self.patchsize = patchsize
        self.query_embedding = nn.Conv2d(d_model, d_model, kernel_size=1, padding=0)
        self.value_embedding = nn.Conv2d(d_model, d_model, kernel_size=1, padding=0)
        self.key_embedding = nn.Conv2d(d_model, d_model, kernel_size=1, padding=0)
        self.output_linear = nn.Sequential(nn.Conv2d(d_model, d_model, kernel_size=3, padding=1), nn.LeakyReLU(0.2, inplace=True))
        self.attention = Attention()

    def forward(self, x, m, b, c):
        bt, _, h, w = x.size()
        t = bt // b
        d_k = c // len(self.patchsize)
        output = []
        _query = self.query_embedding(x)
        _key = self.key_embedding(x)
        _value = self.value_embedding(x)
        for (width, height), query, key, value in zip(self.patchsize, torch.chunk(_query, len(self.patchsize), dim=1), torch.chunk(_key, len(self.patchsize), dim=1), torch.chunk(_value, len(self.patchsize), dim=1)):
            out_w, out_h = (w // width, h // height)
            mm = m.view(b, t, 1, out_h, height, out_w, width)
            mm = mm.permute(0, 1, 3, 5, 2, 4, 6).contiguous().view(b, t * out_h * out_w, height * width)
            mm = (mm.mean(-1) > 0.5).unsqueeze(1).repeat(1, t * out_h * out_w, 1)
            query = query.view(b, t, d_k, out_h, height, out_w, width)
            query = query.permute(0, 1, 3, 5, 2, 4, 6).contiguous().view(b, t * out_h * out_w, d_k * height * width)
            key = key.view(b, t, d_k, out_h, height, out_w, width)
            key = key.permute(0, 1, 3, 5, 2, 4, 6).contiguous().view(b, t * out_h * out_w, d_k * height * width)
            value = value.view(b, t, d_k, out_h, height, out_w, width)
            value = value.permute(0, 1, 3, 5, 2, 4, 6).contiguous().view(b, t * out_h * out_w, d_k * height * width)
            '\n            # 2) Apply attention on all the projected vectors in batch.\n            tmp1 = []\n            for q,k,v in zip(torch.chunk(query, b, dim=0), torch.chunk(key, b, dim=0), torch.chunk(value, b, dim=0)):\n                y, _ = self.attention(q.unsqueeze(0), k.unsqueeze(0), v.unsqueeze(0))\n                tmp1.append(y)\n            y = torch.cat(tmp1,1)\n            '
            y, _ = self.attention(query, key, value, mm)
            y = y.view(b, t, out_h, out_w, d_k, height, width)
            y = y.permute(0, 1, 4, 2, 5, 3, 6).contiguous().view(bt, d_k, h, w)
            output.append(y)
        output = torch.cat(output, 1)
        x = self.output_linear(output)
        return x

def __init__(self, patchsize, d_model):
    super().__init__()
    self.patchsize = patchsize
    self.query_embedding = nn.Conv2d(d_model, d_model, kernel_size=1, padding=0)
    self.value_embedding = nn.Conv2d(d_model, d_model, kernel_size=1, padding=0)
    self.key_embedding = nn.Conv2d(d_model, d_model, kernel_size=1, padding=0)
    self.output_linear = nn.Sequential(nn.Conv2d(d_model, d_model, kernel_size=3, padding=1), nn.LeakyReLU(0.2, inplace=True))
    self.attention = Attention()

class FeedForward(nn.Module):

    def __init__(self, d_model):
        super(FeedForward, self).__init__()
        self.conv = nn.Sequential(nn.Conv2d(d_model, d_model, kernel_size=3, padding=2, dilation=2), nn.LeakyReLU(0.2, inplace=True), nn.Conv2d(d_model, d_model, kernel_size=3, padding=1), nn.LeakyReLU(0.2, inplace=True))

    def forward(self, x):
        x = self.conv(x)
        return x

def __init__(self, d_model):
    super(FeedForward, self).__init__()
    self.conv = nn.Sequential(nn.Conv2d(d_model, d_model, kernel_size=3, padding=2, dilation=2), nn.LeakyReLU(0.2, inplace=True), nn.Conv2d(d_model, d_model, kernel_size=3, padding=1), nn.LeakyReLU(0.2, inplace=True))

class TransformerBlock(nn.Module):
    """
    Transformer = MultiHead_Attention + Feed_Forward with sublayer connection
    """

    def __init__(self, patchsize, hidden=128):
        super().__init__()
        self.attention = MultiHeadedAttention(patchsize, d_model=hidden)
        self.feed_forward = FeedForward(hidden)

    def forward(self, x):
        x, m, b, c = (x['x'], x['m'], x['b'], x['c'])
        x = x + self.attention(x, m, b, c)
        x = x + self.feed_forward(x)
        return {'x': x, 'm': m, 'b': b, 'c': c}

def __init__(self, patchsize, hidden=128):
    super().__init__()
    self.attention = MultiHeadedAttention(patchsize, d_model=hidden)
    self.feed_forward = FeedForward(hidden)

class Discriminator(BaseNetwork):

    def __init__(self, in_channels=3, use_sigmoid=False, use_spectral_norm=True, init_weights=True):
        super(Discriminator, self).__init__()
        self.use_sigmoid = use_sigmoid
        nf = 64
        self.conv = nn.Sequential(spectral_norm(nn.Conv3d(in_channels=in_channels, out_channels=nf * 1, kernel_size=(3, 5, 5), stride=(1, 2, 2), padding=1, bias=not use_spectral_norm), use_spectral_norm), nn.LeakyReLU(0.2, inplace=True), spectral_norm(nn.Conv3d(nf * 1, nf * 2, kernel_size=(3, 5, 5), stride=(1, 2, 2), padding=(1, 2, 2), bias=not use_spectral_norm), use_spectral_norm), nn.LeakyReLU(0.2, inplace=True), spectral_norm(nn.Conv3d(nf * 2, nf * 4, kernel_size=(3, 5, 5), stride=(1, 2, 2), padding=(1, 2, 2), bias=not use_spectral_norm), use_spectral_norm), nn.LeakyReLU(0.2, inplace=True), spectral_norm(nn.Conv3d(nf * 4, nf * 4, kernel_size=(3, 5, 5), stride=(1, 2, 2), padding=(1, 2, 2), bias=not use_spectral_norm), use_spectral_norm), nn.LeakyReLU(0.2, inplace=True), spectral_norm(nn.Conv3d(nf * 4, nf * 4, kernel_size=(3, 5, 5), stride=(1, 2, 2), padding=(1, 2, 2), bias=not use_spectral_norm), use_spectral_norm), nn.LeakyReLU(0.2, inplace=True), nn.Conv3d(nf * 4, nf * 4, kernel_size=(3, 5, 5), stride=(1, 2, 2), padding=(1, 2, 2)))
        if init_weights:
            self.init_weights()

    def forward(self, xs):
        xs_t = torch.transpose(xs, 0, 1)
        xs_t = xs_t.unsqueeze(0)
        feat = self.conv(xs_t)
        if self.use_sigmoid:
            feat = torch.sigmoid(feat)
        out = torch.transpose(feat, 1, 2)
        return out

def __init__(self, in_channels=3, use_sigmoid=False, use_spectral_norm=True, init_weights=True):
    super(Discriminator, self).__init__()
    self.use_sigmoid = use_sigmoid
    nf = 64
    self.conv = nn.Sequential(spectral_norm(nn.Conv3d(in_channels=in_channels, out_channels=nf * 1, kernel_size=(3, 5, 5), stride=(1, 2, 2), padding=1, bias=not use_spectral_norm), use_spectral_norm), nn.LeakyReLU(0.2, inplace=True), spectral_norm(nn.Conv3d(nf * 1, nf * 2, kernel_size=(3, 5, 5), stride=(1, 2, 2), padding=(1, 2, 2), bias=not use_spectral_norm), use_spectral_norm), nn.LeakyReLU(0.2, inplace=True), spectral_norm(nn.Conv3d(nf * 2, nf * 4, kernel_size=(3, 5, 5), stride=(1, 2, 2), padding=(1, 2, 2), bias=not use_spectral_norm), use_spectral_norm), nn.LeakyReLU(0.2, inplace=True), spectral_norm(nn.Conv3d(nf * 4, nf * 4, kernel_size=(3, 5, 5), stride=(1, 2, 2), padding=(1, 2, 2), bias=not use_spectral_norm), use_spectral_norm), nn.LeakyReLU(0.2, inplace=True), spectral_norm(nn.Conv3d(nf * 4, nf * 4, kernel_size=(3, 5, 5), stride=(1, 2, 2), padding=(1, 2, 2), bias=not use_spectral_norm), use_spectral_norm), nn.LeakyReLU(0.2, inplace=True), nn.Conv3d(nf * 4, nf * 4, kernel_size=(3, 5, 5), stride=(1, 2, 2), padding=(1, 2, 2)))
    if init_weights:
        self.init_weights()

class BaseNetwork(nn.Module):

    def __init__(self):
        super(BaseNetwork, self).__init__()

    def print_network(self):
        if isinstance(self, list):
            self = self[0]
        num_params = 0
        for param in self.parameters():
            num_params += param.numel()
        print('Network [%s] was created. Total number of parameters: %.1f million. To see the architecture, do print(network).' % (type(self).__name__, num_params / 1000000))

    def init_weights(self, init_type='normal', gain=0.02):
        """
        initialize network's weights
        init_type: normal | xavier | kaiming | orthogonal
        https://github.com/junyanz/pytorch-CycleGAN-and-pix2pix/blob/9451e70673400885567d08a9e97ade2524c700d0/models/networks.py#L39
        """

        def init_func(m):
            classname = m.__class__.__name__
            if classname.find('InstanceNorm2d') != -1:
                if hasattr(m, 'weight') and m.weight is not None:
                    nn.init.constant_(m.weight.data, 1.0)
                if hasattr(m, 'bias') and m.bias is not None:
                    nn.init.constant_(m.bias.data, 0.0)
            elif hasattr(m, 'weight') and (classname.find('Conv') != -1 or classname.find('Linear') != -1):
                if init_type == 'normal':
                    nn.init.normal_(m.weight.data, 0.0, gain)
                elif init_type == 'xavier':
                    nn.init.xavier_normal_(m.weight.data, gain=gain)
                elif init_type == 'xavier_uniform':
                    nn.init.xavier_uniform_(m.weight.data, gain=1.0)
                elif init_type == 'kaiming':
                    nn.init.kaiming_normal_(m.weight.data, a=0, mode='fan_in')
                elif init_type == 'orthogonal':
                    nn.init.orthogonal_(m.weight.data, gain=gain)
                elif init_type == 'none':
                    m.reset_parameters()
                else:
                    raise NotImplementedError('initialization method [%s] is not implemented' % init_type)
                if hasattr(m, 'bias') and m.bias is not None:
                    nn.init.constant_(m.bias.data, 0.0)
        self.apply(init_func)
        for m in self.children():
            if hasattr(m, 'init_weights'):
                m.init_weights(init_type, gain)

def __init__(self):
    super(BaseNetwork, self).__init__()

class InpaintGenerator(BaseNetwork):

    def __init__(self, init_weights=True):
        super(InpaintGenerator, self).__init__()
        channel = 256
        stack_num = 8
        patchsize = [(108, 60), (36, 20), (18, 10), (9, 5)]
        blocks = []
        for _ in range(stack_num):
            blocks.append(TransformerBlock(patchsize, hidden=channel))
        self.transformer = nn.Sequential(*blocks)
        self.encoder = nn.Sequential(nn.Conv2d(3, 64, kernel_size=3, stride=2, padding=1), nn.LeakyReLU(0.2, inplace=True), nn.Conv2d(64, 64, kernel_size=3, stride=1, padding=1), nn.LeakyReLU(0.2, inplace=True), nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1), nn.LeakyReLU(0.2, inplace=True), nn.Conv2d(128, channel, kernel_size=3, stride=1, padding=1), nn.LeakyReLU(0.2, inplace=True))
        self.decoder = nn.Sequential(deconv(channel, 128, kernel_size=3, padding=1), nn.LeakyReLU(0.2, inplace=True), nn.Conv2d(128, 64, kernel_size=3, stride=1, padding=1), nn.LeakyReLU(0.2, inplace=True), deconv(64, 64, kernel_size=3, padding=1), nn.LeakyReLU(0.2, inplace=True), nn.Conv2d(64, 3, kernel_size=3, stride=1, padding=1))
        if init_weights:
            self.init_weights()

    def forward(self, masked_frames, masks):
        b, t, c, h, w = masked_frames.size()
        masks = masks.view(b * t, 1, h, w)
        enc_feat = self.encoder(masked_frames.view(b * t, c, h, w))
        _, c, h, w = enc_feat.size()
        masks = F.interpolate(masks, scale_factor=1.0 / 4)
        enc_feat = self.transformer({'x': enc_feat, 'm': masks, 'b': b, 'c': c})['x']
        output = self.decoder(enc_feat)
        output = torch.tanh(output)
        return output

    def infer(self, feat, masks):
        t, c, h, w = masks.size()
        masks = masks.view(t, c, h, w)
        masks = F.interpolate(masks, scale_factor=1.0 / 4)
        t, c, _, _ = feat.size()
        output = self.transformer({'x': feat, 'm': masks, 'b': 1, 'c': c})
        enc_feat = output['x']
        attn = output['attn']
        mm = output['smm']
        return (enc_feat, attn, mm)

def __init__(self, init_weights=True):
    super(InpaintGenerator, self).__init__()
    channel = 256
    stack_num = 8
    patchsize = [(108, 60), (36, 20), (18, 10), (9, 5)]
    blocks = []
    for _ in range(stack_num):
        blocks.append(TransformerBlock(patchsize, hidden=channel))
    self.transformer = nn.Sequential(*blocks)
    self.encoder = nn.Sequential(nn.Conv2d(3, 64, kernel_size=3, stride=2, padding=1), nn.LeakyReLU(0.2, inplace=True), nn.Conv2d(64, 64, kernel_size=3, stride=1, padding=1), nn.LeakyReLU(0.2, inplace=True), nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1), nn.LeakyReLU(0.2, inplace=True), nn.Conv2d(128, channel, kernel_size=3, stride=1, padding=1), nn.LeakyReLU(0.2, inplace=True))
    self.decoder = nn.Sequential(deconv(channel, 128, kernel_size=3, padding=1), nn.LeakyReLU(0.2, inplace=True), nn.Conv2d(128, 64, kernel_size=3, stride=1, padding=1), nn.LeakyReLU(0.2, inplace=True), deconv(64, 64, kernel_size=3, padding=1), nn.LeakyReLU(0.2, inplace=True), nn.Conv2d(64, 3, kernel_size=3, stride=1, padding=1))
    if init_weights:
        self.init_weights()

class deconv(nn.Module):

    def __init__(self, input_channel, output_channel, kernel_size=3, padding=0):
        super().__init__()
        self.conv = nn.Conv2d(input_channel, output_channel, kernel_size=kernel_size, stride=1, padding=padding)

    def forward(self, x):
        x = F.interpolate(x, scale_factor=2, mode='bilinear', align_corners=True)
        return self.conv(x)

def __init__(self, input_channel, output_channel, kernel_size=3, padding=0):
    super().__init__()
    self.conv = nn.Conv2d(input_channel, output_channel, kernel_size=kernel_size, stride=1, padding=padding)

class MultiHeadedAttention(nn.Module):
    """
    Take in model size and number of heads.
    """

    def __init__(self, patchsize, d_model):
        super().__init__()
        self.patchsize = patchsize
        self.query_embedding = nn.Conv2d(d_model, d_model, kernel_size=1, padding=0)
        self.value_embedding = nn.Conv2d(d_model, d_model, kernel_size=1, padding=0)
        self.key_embedding = nn.Conv2d(d_model, d_model, kernel_size=1, padding=0)
        self.output_linear = nn.Sequential(nn.Conv2d(d_model, d_model, kernel_size=3, padding=1), nn.LeakyReLU(0.2, inplace=True))
        self.attention = Attention()

    def forward(self, x, m, b, c):
        bt, _, h, w = x.size()
        t = bt // b
        d_k = c // len(self.patchsize)
        output = []
        _query = self.query_embedding(x)
        _key = self.key_embedding(x)
        _value = self.value_embedding(x)
        for (width, height), query, key, value in zip(self.patchsize, torch.chunk(_query, len(self.patchsize), dim=1), torch.chunk(_key, len(self.patchsize), dim=1), torch.chunk(_value, len(self.patchsize), dim=1)):
            out_w, out_h = (w // width, h // height)
            mm = m.view(b, t, 1, out_h, height, out_w, width)
            mm = mm.permute(0, 1, 3, 5, 2, 4, 6).contiguous().view(b, t * out_h * out_w, height * width)
            mm = (mm.mean(-1) > 0.5).unsqueeze(1).repeat(1, t * out_h * out_w, 1)
            query = query.view(b, t, d_k, out_h, height, out_w, width)
            query = query.permute(0, 1, 3, 5, 2, 4, 6).contiguous().view(b, t * out_h * out_w, d_k * height * width)
            key = key.view(b, t, d_k, out_h, height, out_w, width)
            key = key.permute(0, 1, 3, 5, 2, 4, 6).contiguous().view(b, t * out_h * out_w, d_k * height * width)
            value = value.view(b, t, d_k, out_h, height, out_w, width)
            value = value.permute(0, 1, 3, 5, 2, 4, 6).contiguous().view(b, t * out_h * out_w, d_k * height * width)
            '\n            # 2) Apply attention on all the projected vectors in batch.\n            tmp1 = []\n            for q,k,v in zip(torch.chunk(query, b, dim=0), torch.chunk(key, b, dim=0), torch.chunk(value, b, dim=0)):\n                y, _ = self.attention(q.unsqueeze(0), k.unsqueeze(0), v.unsqueeze(0))\n                tmp1.append(y)\n            y = torch.cat(tmp1,1)\n            '
            y, attn = self.attention(query, key, value, mm)
            if width == 18:
                select_attn = attn.view(t, out_h * out_w, t, out_h, out_w)[0]
                select_mm = mm[0].view(t * out_h * out_w, t, out_h, out_w)[0]
            y = y.view(b, t, out_h, out_w, d_k, height, width)
            y = y.permute(0, 1, 4, 2, 5, 3, 6).contiguous().view(bt, d_k, h, w)
            output.append(y)
        output = torch.cat(output, 1)
        x = self.output_linear(output)
        return (x, select_attn, select_mm)

def __init__(self, patchsize, d_model):
    super().__init__()
    self.patchsize = patchsize
    self.query_embedding = nn.Conv2d(d_model, d_model, kernel_size=1, padding=0)
    self.value_embedding = nn.Conv2d(d_model, d_model, kernel_size=1, padding=0)
    self.key_embedding = nn.Conv2d(d_model, d_model, kernel_size=1, padding=0)
    self.output_linear = nn.Sequential(nn.Conv2d(d_model, d_model, kernel_size=3, padding=1), nn.LeakyReLU(0.2, inplace=True))
    self.attention = Attention()

class FeedForward(nn.Module):

    def __init__(self, d_model):
        super(FeedForward, self).__init__()
        self.conv = nn.Sequential(nn.Conv2d(d_model, d_model, kernel_size=3, padding=2, dilation=2), nn.LeakyReLU(0.2, inplace=True), nn.Conv2d(d_model, d_model, kernel_size=3, padding=1), nn.LeakyReLU(0.2, inplace=True))

    def forward(self, x):
        x = self.conv(x)
        return x

def __init__(self, d_model):
    super(FeedForward, self).__init__()
    self.conv = nn.Sequential(nn.Conv2d(d_model, d_model, kernel_size=3, padding=2, dilation=2), nn.LeakyReLU(0.2, inplace=True), nn.Conv2d(d_model, d_model, kernel_size=3, padding=1), nn.LeakyReLU(0.2, inplace=True))

class TransformerBlock(nn.Module):
    """
    Transformer = MultiHead_Attention + Feed_Forward with sublayer connection
    """

    def __init__(self, patchsize, hidden=128):
        super().__init__()
        self.attention = MultiHeadedAttention(patchsize, d_model=hidden)
        self.feed_forward = FeedForward(hidden)

    def forward(self, x):
        x, m, b, c = (x['x'], x['m'], x['b'], x['c'])
        val, attn, mm = self.attention(x, m, b, c)
        x = x + val
        x = x + self.feed_forward(x)
        return {'x': x, 'm': m, 'b': b, 'c': c, 'attn': attn, 'smm': mm}

def __init__(self, patchsize, hidden=128):
    super().__init__()
    self.attention = MultiHeadedAttention(patchsize, d_model=hidden)
    self.feed_forward = FeedForward(hidden)

class Discriminator(BaseNetwork):

    def __init__(self, in_channels=3, use_sigmoid=False, use_spectral_norm=True, init_weights=True):
        super(Discriminator, self).__init__()
        self.use_sigmoid = use_sigmoid
        nf = 64
        self.conv = nn.Sequential(spectral_norm(nn.Conv3d(in_channels=in_channels, out_channels=nf * 1, kernel_size=(3, 5, 5), stride=(1, 2, 2), padding=1, bias=not use_spectral_norm), use_spectral_norm), nn.LeakyReLU(0.2, inplace=True), spectral_norm(nn.Conv3d(nf * 1, nf * 2, kernel_size=(3, 5, 5), stride=(1, 2, 2), padding=(1, 2, 2), bias=not use_spectral_norm), use_spectral_norm), nn.LeakyReLU(0.2, inplace=True), spectral_norm(nn.Conv3d(nf * 2, nf * 4, kernel_size=(3, 5, 5), stride=(1, 2, 2), padding=(1, 2, 2), bias=not use_spectral_norm), use_spectral_norm), nn.LeakyReLU(0.2, inplace=True), spectral_norm(nn.Conv3d(nf * 4, nf * 4, kernel_size=(3, 5, 5), stride=(1, 2, 2), padding=(1, 2, 2), bias=not use_spectral_norm), use_spectral_norm), nn.LeakyReLU(0.2, inplace=True), spectral_norm(nn.Conv3d(nf * 4, nf * 4, kernel_size=(3, 5, 5), stride=(1, 2, 2), padding=(1, 2, 2), bias=not use_spectral_norm), use_spectral_norm), nn.LeakyReLU(0.2, inplace=True), nn.Conv3d(nf * 4, nf * 4, kernel_size=(3, 5, 5), stride=(1, 2, 2), padding=(1, 2, 2)))
        if init_weights:
            self.init_weights()

    def forward(self, xs):
        xs_t = torch.transpose(xs, 0, 1)
        xs_t = xs_t.unsqueeze(0)
        feat = self.conv(xs_t)
        if self.use_sigmoid:
            feat = torch.sigmoid(feat)
        out = torch.transpose(feat, 1, 2)
        return out

def __init__(self, in_channels=3, use_sigmoid=False, use_spectral_norm=True, init_weights=True):
    super(Discriminator, self).__init__()
    self.use_sigmoid = use_sigmoid
    nf = 64
    self.conv = nn.Sequential(spectral_norm(nn.Conv3d(in_channels=in_channels, out_channels=nf * 1, kernel_size=(3, 5, 5), stride=(1, 2, 2), padding=1, bias=not use_spectral_norm), use_spectral_norm), nn.LeakyReLU(0.2, inplace=True), spectral_norm(nn.Conv3d(nf * 1, nf * 2, kernel_size=(3, 5, 5), stride=(1, 2, 2), padding=(1, 2, 2), bias=not use_spectral_norm), use_spectral_norm), nn.LeakyReLU(0.2, inplace=True), spectral_norm(nn.Conv3d(nf * 2, nf * 4, kernel_size=(3, 5, 5), stride=(1, 2, 2), padding=(1, 2, 2), bias=not use_spectral_norm), use_spectral_norm), nn.LeakyReLU(0.2, inplace=True), spectral_norm(nn.Conv3d(nf * 4, nf * 4, kernel_size=(3, 5, 5), stride=(1, 2, 2), padding=(1, 2, 2), bias=not use_spectral_norm), use_spectral_norm), nn.LeakyReLU(0.2, inplace=True), spectral_norm(nn.Conv3d(nf * 4, nf * 4, kernel_size=(3, 5, 5), stride=(1, 2, 2), padding=(1, 2, 2), bias=not use_spectral_norm), use_spectral_norm), nn.LeakyReLU(0.2, inplace=True), nn.Conv3d(nf * 4, nf * 4, kernel_size=(3, 5, 5), stride=(1, 2, 2), padding=(1, 2, 2)))
    if init_weights:
        self.init_weights()

class ZipReader(object):
    file_dict = dict()

    def __init__(self):
        super(ZipReader, self).__init__()

    @staticmethod
    def build_file_dict(path):
        file_dict = ZipReader.file_dict
        if path in file_dict:
            return file_dict[path]
        else:
            file_handle = zipfile.ZipFile(path, 'r')
            file_dict[path] = file_handle
            return file_dict[path]

    @staticmethod
    def imread(path, image_name):
        zfile = ZipReader.build_file_dict(path)
        data = zfile.read(image_name)
        im = Image.open(io.BytesIO(data))
        return im

def __init__(self):
    super(ZipReader, self).__init__()

class Trainer:

    def __init__(self, config, debug=False):
        self.config = config
        self.epoch = 0
        self.iteration = 0
        if debug:
            self.config['trainer']['save_freq'] = 5
            self.config['trainer']['valid_freq'] = 5
            self.config['trainer']['iterations'] = 5
        self.train_dataset = Dataset(config['data_loader'], split='train', debug=debug)
        self.train_sampler = None
        self.train_args = config['trainer']
        if config['distributed']:
            self.train_sampler = DistributedSampler(self.train_dataset, num_replicas=config['world_size'], rank=config['global_rank'])
        self.train_loader = DataLoader(self.train_dataset, batch_size=self.train_args['batch_size'] // config['world_size'], shuffle=self.train_sampler is None, num_workers=self.train_args['num_workers'], sampler=self.train_sampler)
        self.adversarial_loss = AdversarialLoss(type=self.config['losses']['GAN_LOSS'])
        self.adversarial_loss = self.adversarial_loss.to(self.config['device'])
        self.l1_loss = nn.L1Loss()
        net = importlib.import_module('model.' + config['model'])
        self.netG = net.InpaintGenerator()
        self.netG = self.netG.to(self.config['device'])
        self.netD = net.Discriminator(in_channels=3, use_sigmoid=config['losses']['GAN_LOSS'] != 'hinge')
        self.netD = self.netD.to(self.config['device'])
        self.optimG = torch.optim.Adam(self.netG.parameters(), lr=config['trainer']['lr'], betas=(self.config['trainer']['beta1'], self.config['trainer']['beta2']))
        self.optimD = torch.optim.Adam(self.netD.parameters(), lr=config['trainer']['lr'], betas=(self.config['trainer']['beta1'], self.config['trainer']['beta2']))
        self.load()
        if config['distributed']:
            self.netG = DDP(self.netG, device_ids=[self.config['local_rank']], output_device=self.config['local_rank'], broadcast_buffers=True, find_unused_parameters=False)
            self.netD = DDP(self.netD, device_ids=[self.config['local_rank']], output_device=self.config['local_rank'], broadcast_buffers=True, find_unused_parameters=False)
        self.dis_writer = None
        self.gen_writer = None
        self.summary = {}
        if self.config['global_rank'] == 0 or not config['distributed']:
            self.dis_writer = SummaryWriter(os.path.join(config['save_dir'], 'dis'))
            self.gen_writer = SummaryWriter(os.path.join(config['save_dir'], 'gen'))

    def get_lr(self):
        return self.optimG.param_groups[0]['lr']

    def adjust_learning_rate(self):
        decay = 0.1 ** (min(self.iteration, self.config['trainer']['niter_steady']) // self.config['trainer']['niter'])
        new_lr = self.config['trainer']['lr'] * decay
        if new_lr != self.get_lr():
            for param_group in self.optimG.param_groups:
                param_group['lr'] = new_lr
            for param_group in self.optimD.param_groups:
                param_group['lr'] = new_lr

    def add_summary(self, writer, name, val):
        if name not in self.summary:
            self.summary[name] = 0
        self.summary[name] += val
        if writer is not None and self.iteration % 100 == 0:
            writer.add_scalar(name, self.summary[name] / 100, self.iteration)
            self.summary[name] = 0

    def load(self):
        model_path = self.config['save_dir']
        if os.path.isfile(os.path.join(model_path, 'latest.ckpt')):
            latest_epoch = open(os.path.join(model_path, 'latest.ckpt'), 'r').read().splitlines()[-1]
        else:
            ckpts = [os.path.basename(i).split('.pth')[0] for i in glob.glob(os.path.join(model_path, '*.pth'))]
            ckpts.sort()
            latest_epoch = ckpts[-1] if len(ckpts) > 0 else None
        if latest_epoch is not None:
            gen_path = os.path.join(model_path, 'gen_{}.pth'.format(str(latest_epoch).zfill(5)))
            dis_path = os.path.join(model_path, 'dis_{}.pth'.format(str(latest_epoch).zfill(5)))
            opt_path = os.path.join(model_path, 'opt_{}.pth'.format(str(latest_epoch).zfill(5)))
            if self.config['global_rank'] == 0:
                print('Loading model from {}...'.format(gen_path))
            data = torch.load(gen_path, map_location=self.config['device'])
            self.netG.load_state_dict(data['netG'])
            data = torch.load(dis_path, map_location=self.config['device'])
            self.netD.load_state_dict(data['netD'])
            data = torch.load(opt_path, map_location=self.config['device'])
            self.optimG.load_state_dict(data['optimG'])
            self.optimD.load_state_dict(data['optimD'])
            self.epoch = data['epoch']
            self.iteration = data['iteration']
        elif self.config['global_rank'] == 0:
            print('Warnning: There is no trained model found. An initialized model will be used.')

    def save(self, it):
        if self.config['global_rank'] == 0:
            gen_path = os.path.join(self.config['save_dir'], 'gen_{}.pth'.format(str(it).zfill(5)))
            dis_path = os.path.join(self.config['save_dir'], 'dis_{}.pth'.format(str(it).zfill(5)))
            opt_path = os.path.join(self.config['save_dir'], 'opt_{}.pth'.format(str(it).zfill(5)))
            print('\nsaving model to {} ...'.format(gen_path))
            if isinstance(self.netG, torch.nn.DataParallel) or isinstance(self.netG, DDP):
                netG = self.netG.module
                netD = self.netD.module
            else:
                netG = self.netG
                netD = self.netD
            torch.save({'netG': netG.state_dict()}, gen_path)
            torch.save({'netD': netD.state_dict()}, dis_path)
            torch.save({'epoch': self.epoch, 'iteration': self.iteration, 'optimG': self.optimG.state_dict(), 'optimD': self.optimD.state_dict()}, opt_path)
            os.system('echo {} > {}'.format(str(it).zfill(5), os.path.join(self.config['save_dir'], 'latest.ckpt')))

    def train(self):
        pbar = range(int(self.train_args['iterations']))
        if self.config['global_rank'] == 0:
            pbar = tqdm(pbar, initial=self.iteration, dynamic_ncols=True, smoothing=0.01)
        while True:
            self.epoch += 1
            if self.config['distributed']:
                self.train_sampler.set_epoch(self.epoch)
            self._train_epoch(pbar)
            if self.iteration > self.train_args['iterations']:
                break
        print('\nEnd training....')

    def _train_epoch(self, pbar):
        device = self.config['device']
        for frames, masks in self.train_loader:
            self.adjust_learning_rate()
            self.iteration += 1
            frames, masks = (frames.to(device), masks.to(device))
            b, t, c, h, w = frames.size()
            masked_frame = frames * (1 - masks).float()
            pred_img = self.netG(masked_frame, masks)
            frames = frames.view(b * t, c, h, w)
            masks = masks.view(b * t, 1, h, w)
            comp_img = frames * (1.0 - masks) + masks * pred_img
            gen_loss = 0
            dis_loss = 0
            real_vid_feat = self.netD(frames)
            fake_vid_feat = self.netD(comp_img.detach())
            dis_real_loss = self.adversarial_loss(real_vid_feat, True, True)
            dis_fake_loss = self.adversarial_loss(fake_vid_feat, False, True)
            dis_loss += (dis_real_loss + dis_fake_loss) / 2
            self.add_summary(self.dis_writer, 'loss/dis_vid_fake', dis_fake_loss.item())
            self.add_summary(self.dis_writer, 'loss/dis_vid_real', dis_real_loss.item())
            self.optimD.zero_grad()
            dis_loss.backward()
            self.optimD.step()
            gen_vid_feat = self.netD(comp_img)
            gan_loss = self.adversarial_loss(gen_vid_feat, True, False)
            gan_loss = gan_loss * self.config['losses']['adversarial_weight']
            gen_loss += gan_loss
            self.add_summary(self.gen_writer, 'loss/gan_loss', gan_loss.item())
            hole_loss = self.l1_loss(pred_img * masks, frames * masks)
            hole_loss = hole_loss / torch.mean(masks) * self.config['losses']['hole_weight']
            gen_loss += hole_loss
            self.add_summary(self.gen_writer, 'loss/hole_loss', hole_loss.item())
            valid_loss = self.l1_loss(pred_img * (1 - masks), frames * (1 - masks))
            valid_loss = valid_loss / torch.mean(1 - masks) * self.config['losses']['valid_weight']
            gen_loss += valid_loss
            self.add_summary(self.gen_writer, 'loss/valid_loss', valid_loss.item())
            self.optimG.zero_grad()
            gen_loss.backward()
            self.optimG.step()
            if self.config['global_rank'] == 0:
                pbar.update(1)
                pbar.set_description(f'd: {dis_loss.item():.3f}; g: {gan_loss.item():.3f};hole: {hole_loss.item():.3f}; valid: {valid_loss.item():.3f}')
            if self.iteration % self.train_args['save_freq'] == 0:
                self.save(int(self.iteration // self.train_args['save_freq']))
            if self.iteration > self.train_args['iterations']:
                break

def adjust_learning_rate(self):
    decay = 0.1 ** (min(self.iteration, self.config['trainer']['niter_steady']) // self.config['trainer']['niter'])
    new_lr = self.config['trainer']['lr'] * decay
    if new_lr != self.get_lr():
        for param_group in self.optimG.param_groups:
            param_group['lr'] = new_lr
        for param_group in self.optimD.param_groups:
            param_group['lr'] = new_lr

class AdversarialLoss(nn.Module):
    """
    Adversarial loss
    https://arxiv.org/abs/1711.10337
    """

    def __init__(self, type='nsgan', target_real_label=1.0, target_fake_label=0.0):
        """
        type = nsgan | lsgan | hinge
        """
        super(AdversarialLoss, self).__init__()
        self.type = type
        self.register_buffer('real_label', torch.tensor(target_real_label))
        self.register_buffer('fake_label', torch.tensor(target_fake_label))
        if type == 'nsgan':
            self.criterion = nn.BCELoss()
        elif type == 'lsgan':
            self.criterion = nn.MSELoss()
        elif type == 'hinge':
            self.criterion = nn.ReLU()

    def __call__(self, outputs, is_real, is_disc=None):
        if self.type == 'hinge':
            if is_disc:
                if is_real:
                    outputs = -outputs
                return self.criterion(1 + outputs).mean()
            else:
                return (-outputs).mean()
        else:
            labels = (self.real_label if is_real else self.fake_label).expand_as(outputs)
            loss = self.criterion(outputs, labels)
            return loss

def __init__(self, type='nsgan', target_real_label=1.0, target_fake_label=0.0):
    """
        type = nsgan | lsgan | hinge
        """
    super(AdversarialLoss, self).__init__()
    self.type = type
    self.register_buffer('real_label', torch.tensor(target_real_label))
    self.register_buffer('fake_label', torch.tensor(target_fake_label))
    if type == 'nsgan':
        self.criterion = nn.BCELoss()
    elif type == 'lsgan':
        self.criterion = nn.MSELoss()
    elif type == 'hinge':
        self.criterion = nn.ReLU()

def use_spectral_norm(module, use_sn=False):
    if use_sn:
        return spectral_norm(module)
    return module

class SamPredictor:

    def __init__(self, sam_model: Sam) -> None:
        """
        Uses SAM to calculate the image embedding for an image, and then
        allow repeated, efficient mask prediction given prompts.

        Arguments:
          sam_model (Sam): The model to use for mask prediction.
        """
        super().__init__()
        self.model = sam_model
        self.transform = ResizeLongestSide(sam_model.image_encoder.img_size)
        self.reset_image()

    def set_image(self, image: np.ndarray, image_format: str='RGB') -> None:
        """
        Calculates the image embeddings for the provided image, allowing
        masks to be predicted with the 'predict' method.

        Arguments:
          image (np.ndarray): The image for calculating masks. Expects an
            image in HWC uint8 format, with pixel values in [0, 255].
          image_format (str): The color format of the image, in ['RGB', 'BGR'].
        """
        assert image_format in ['RGB', 'BGR'], f"image_format must be in ['RGB', 'BGR'], is {image_format}."
        if image_format != self.model.image_format:
            image = image[..., ::-1]
        input_image = self.transform.apply_image(image)
        input_image_torch = torch.as_tensor(input_image, device=self.device)
        input_image_torch = input_image_torch.permute(2, 0, 1).contiguous()[None, :, :, :]
        self.set_torch_image(input_image_torch, image.shape[:2])

    @torch.no_grad()
    def set_torch_image(self, transformed_image: torch.Tensor, original_image_size: Tuple[int, ...]) -> None:
        """
        Calculates the image embeddings for the provided image, allowing
        masks to be predicted with the 'predict' method. Expects the input
        image to be already transformed to the format expected by the model.

        Arguments:
          transformed_image (torch.Tensor): The input image, with shape
            1x3xHxW, which has been transformed with ResizeLongestSide.
          original_image_size (tuple(int, int)): The size of the image
            before transformation, in (H, W) format.
        """
        assert len(transformed_image.shape) == 4 and transformed_image.shape[1] == 3 and (max(*transformed_image.shape[2:]) == self.model.image_encoder.img_size), f'set_torch_image input must be BCHW with long side {self.model.image_encoder.img_size}.'
        self.reset_image()
        self.original_size = original_image_size
        self.input_size = tuple(transformed_image.shape[-2:])
        input_image = self.model.preprocess(transformed_image)
        self.features = self.model.image_encoder(input_image)
        self.is_image_set = True

    def predict(self, point_coords: Optional[np.ndarray]=None, point_labels: Optional[np.ndarray]=None, box: Optional[np.ndarray]=None, mask_input: Optional[np.ndarray]=None, multimask_output: bool=True, return_logits: bool=False) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Predict masks for the given input prompts, using the currently set image.

        Arguments:
          point_coords (np.ndarray or None): A Nx2 array of point prompts to the
            model. Each point is in (X,Y) in pixels.
          point_labels (np.ndarray or None): A length N array of labels for the
            point prompts. 1 indicates a foreground point and 0 indicates a
            background point.
          box (np.ndarray or None): A length 4 array given a box prompt to the
            model, in XYXY format.
          mask_input (np.ndarray): A low resolution mask input to the model, typically
            coming from a previous prediction iteration. Has form 1xHxW, where
            for SAM, H=W=256.
          multimask_output (bool): If true, the model will return three masks.
            For ambiguous input prompts (such as a single click), this will often
            produce better masks than a single prediction. If only a single
            mask is needed, the model's predicted quality score can be used
            to select the best mask. For non-ambiguous prompts, such as multiple
            input prompts, multimask_output=False can give better results.
          return_logits (bool): If true, returns un-thresholded masks logits
            instead of a binary mask.

        Returns:
          (np.ndarray): The output masks in CxHxW format, where C is the
            number of masks, and (H, W) is the original image size.
          (np.ndarray): An array of length C containing the model's
            predictions for the quality of each mask.
          (np.ndarray): An array of shape CxHxW, where C is the number
            of masks and H=W=256. These low resolution logits can be passed to
            a subsequent iteration as mask input.
        """
        if not self.is_image_set:
            raise RuntimeError('An image must be set with .set_image(...) before mask prediction.')
        coords_torch, labels_torch, box_torch, mask_input_torch = (None, None, None, None)
        if point_coords is not None:
            assert point_labels is not None, 'point_labels must be supplied if point_coords is supplied.'
            point_coords = self.transform.apply_coords(point_coords, self.original_size)
            coords_torch = torch.as_tensor(point_coords, dtype=torch.float, device=self.device)
            labels_torch = torch.as_tensor(point_labels, dtype=torch.int, device=self.device)
            coords_torch, labels_torch = (coords_torch[None, :, :], labels_torch[None, :])
        if box is not None:
            box = self.transform.apply_boxes(box, self.original_size)
            box_torch = torch.as_tensor(box, dtype=torch.float, device=self.device)
            box_torch = box_torch[None, :]
        if mask_input is not None:
            mask_input_torch = torch.as_tensor(mask_input, dtype=torch.float, device=self.device)
            mask_input_torch = mask_input_torch[None, :, :, :]
        masks, iou_predictions, low_res_masks = self.predict_torch(coords_torch, labels_torch, box_torch, mask_input_torch, multimask_output, return_logits=return_logits)
        masks = masks[0].detach().cpu().numpy()
        iou_predictions = iou_predictions[0].detach().cpu().numpy()
        low_res_masks = low_res_masks[0].detach().cpu().numpy()
        return (masks, iou_predictions, low_res_masks)

    @torch.no_grad()
    def predict_torch(self, point_coords: Optional[torch.Tensor], point_labels: Optional[torch.Tensor], boxes: Optional[torch.Tensor]=None, mask_input: Optional[torch.Tensor]=None, multimask_output: bool=True, return_logits: bool=False) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Predict masks for the given input prompts, using the currently set image.
        Input prompts are batched torch tensors and are expected to already be
        transformed to the input frame using ResizeLongestSide.

        Arguments:
          point_coords (torch.Tensor or None): A BxNx2 array of point prompts to the
            model. Each point is in (X,Y) in pixels.
          point_labels (torch.Tensor or None): A BxN array of labels for the
            point prompts. 1 indicates a foreground point and 0 indicates a
            background point.
          box (np.ndarray or None): A Bx4 array given a box prompt to the
            model, in XYXY format.
          mask_input (np.ndarray): A low resolution mask input to the model, typically
            coming from a previous prediction iteration. Has form Bx1xHxW, where
            for SAM, H=W=256. Masks returned by a previous iteration of the
            predict method do not need further transformation.
          multimask_output (bool): If true, the model will return three masks.
            For ambiguous input prompts (such as a single click), this will often
            produce better masks than a single prediction. If only a single
            mask is needed, the model's predicted quality score can be used
            to select the best mask. For non-ambiguous prompts, such as multiple
            input prompts, multimask_output=False can give better results.
          return_logits (bool): If true, returns un-thresholded masks logits
            instead of a binary mask.

        Returns:
          (torch.Tensor): The output masks in BxCxHxW format, where C is the
            number of masks, and (H, W) is the original image size.
          (torch.Tensor): An array of shape BxC containing the model's
            predictions for the quality of each mask.
          (torch.Tensor): An array of shape BxCxHxW, where C is the number
            of masks and H=W=256. These low res logits can be passed to
            a subsequent iteration as mask input.
        """
        if not self.is_image_set:
            raise RuntimeError('An image must be set with .set_image(...) before mask prediction.')
        if point_coords is not None:
            points = (point_coords, point_labels)
        else:
            points = None
        sparse_embeddings, dense_embeddings = self.model.prompt_encoder(points=points, boxes=boxes, masks=mask_input)
        low_res_masks, iou_predictions = self.model.mask_decoder(image_embeddings=self.features, image_pe=self.model.prompt_encoder.get_dense_pe(), sparse_prompt_embeddings=sparse_embeddings, dense_prompt_embeddings=dense_embeddings, multimask_output=multimask_output)
        masks = self.model.postprocess_masks(low_res_masks, self.input_size, self.original_size)
        if not return_logits:
            masks = masks > self.model.mask_threshold
        return (masks, iou_predictions, low_res_masks)

    def get_image_embedding(self) -> torch.Tensor:
        """
        Returns the image embeddings for the currently set image, with
        shape 1xCxHxW, where C is the embedding dimension and (H,W) are
        the embedding spatial dimension of SAM (typically C=256, H=W=64).
        """
        if not self.is_image_set:
            raise RuntimeError('An image must be set with .set_image(...) to generate an embedding.')
        assert self.features is not None, 'Features must exist if an image has been set.'
        return self.features

    @property
    def device(self) -> torch.device:
        return self.model.device

    def reset_image(self) -> None:
        """Resets the currently set image."""
        self.is_image_set = False
        self.features = None
        self.orig_h = None
        self.orig_w = None
        self.input_h = None
        self.input_w = None

def __init__(self, sam_model: Sam) -> None:
    """
        Uses SAM to calculate the image embedding for an image, and then
        allow repeated, efficient mask prediction given prompts.

        Arguments:
          sam_model (Sam): The model to use for mask prediction.
        """
    super().__init__()
    self.model = sam_model
    self.transform = ResizeLongestSide(sam_model.image_encoder.img_size)
    self.reset_image()

class ImageEncoderViT(nn.Module):

    def __init__(self, img_size: int=1024, patch_size: int=16, in_chans: int=3, embed_dim: int=768, depth: int=12, num_heads: int=12, mlp_ratio: float=4.0, out_chans: int=256, qkv_bias: bool=True, norm_layer: Type[nn.Module]=nn.LayerNorm, act_layer: Type[nn.Module]=nn.GELU, use_abs_pos: bool=True, use_rel_pos: bool=False, rel_pos_zero_init: bool=True, window_size: int=0, global_attn_indexes: Tuple[int, ...]=()) -> None:
        """
        Args:
            img_size (int): Input image size.
            patch_size (int): Patch size.
            in_chans (int): Number of input image channels.
            embed_dim (int): Patch embedding dimension.
            depth (int): Depth of ViT.
            num_heads (int): Number of attention heads in each ViT block.
            mlp_ratio (float): Ratio of mlp hidden dim to embedding dim.
            qkv_bias (bool): If True, add a learnable bias to query, key, value.
            norm_layer (nn.Module): Normalization layer.
            act_layer (nn.Module): Activation layer.
            use_abs_pos (bool): If True, use absolute positional embeddings.
            use_rel_pos (bool): If True, add relative positional embeddings to the attention map.
            rel_pos_zero_init (bool): If True, zero initialize relative positional parameters.
            window_size (int): Window size for window attention blocks.
            global_attn_indexes (list): Indexes for blocks using global attention.
        """
        super().__init__()
        self.img_size = img_size
        self.patch_embed = PatchEmbed(kernel_size=(patch_size, patch_size), stride=(patch_size, patch_size), in_chans=in_chans, embed_dim=embed_dim)
        self.pos_embed: Optional[nn.Parameter] = None
        if use_abs_pos:
            self.pos_embed = nn.Parameter(torch.zeros(1, img_size // patch_size, img_size // patch_size, embed_dim))
        self.blocks = nn.ModuleList()
        for i in range(depth):
            block = Block(dim=embed_dim, num_heads=num_heads, mlp_ratio=mlp_ratio, qkv_bias=qkv_bias, norm_layer=norm_layer, act_layer=act_layer, use_rel_pos=use_rel_pos, rel_pos_zero_init=rel_pos_zero_init, window_size=window_size if i not in global_attn_indexes else 0, input_size=(img_size // patch_size, img_size // patch_size))
            self.blocks.append(block)
        self.neck = nn.Sequential(nn.Conv2d(embed_dim, out_chans, kernel_size=1, bias=False), LayerNorm2d(out_chans), nn.Conv2d(out_chans, out_chans, kernel_size=3, padding=1, bias=False), LayerNorm2d(out_chans))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.patch_embed(x)
        if self.pos_embed is not None:
            x = x + self.pos_embed
        for blk in self.blocks:
            x = blk(x)
        x = self.neck(x.permute(0, 3, 1, 2))
        return x

def __init__(self, img_size: int=1024, patch_size: int=16, in_chans: int=3, embed_dim: int=768, depth: int=12, num_heads: int=12, mlp_ratio: float=4.0, out_chans: int=256, qkv_bias: bool=True, norm_layer: Type[nn.Module]=nn.LayerNorm, act_layer: Type[nn.Module]=nn.GELU, use_abs_pos: bool=True, use_rel_pos: bool=False, rel_pos_zero_init: bool=True, window_size: int=0, global_attn_indexes: Tuple[int, ...]=()) -> None:
    """
        Args:
            img_size (int): Input image size.
            patch_size (int): Patch size.
            in_chans (int): Number of input image channels.
            embed_dim (int): Patch embedding dimension.
            depth (int): Depth of ViT.
            num_heads (int): Number of attention heads in each ViT block.
            mlp_ratio (float): Ratio of mlp hidden dim to embedding dim.
            qkv_bias (bool): If True, add a learnable bias to query, key, value.
            norm_layer (nn.Module): Normalization layer.
            act_layer (nn.Module): Activation layer.
            use_abs_pos (bool): If True, use absolute positional embeddings.
            use_rel_pos (bool): If True, add relative positional embeddings to the attention map.
            rel_pos_zero_init (bool): If True, zero initialize relative positional parameters.
            window_size (int): Window size for window attention blocks.
            global_attn_indexes (list): Indexes for blocks using global attention.
        """
    super().__init__()
    self.img_size = img_size
    self.patch_embed = PatchEmbed(kernel_size=(patch_size, patch_size), stride=(patch_size, patch_size), in_chans=in_chans, embed_dim=embed_dim)
    self.pos_embed: Optional[nn.Parameter] = None
    if use_abs_pos:
        self.pos_embed = nn.Parameter(torch.zeros(1, img_size // patch_size, img_size // patch_size, embed_dim))
    self.blocks = nn.ModuleList()
    for i in range(depth):
        block = Block(dim=embed_dim, num_heads=num_heads, mlp_ratio=mlp_ratio, qkv_bias=qkv_bias, norm_layer=norm_layer, act_layer=act_layer, use_rel_pos=use_rel_pos, rel_pos_zero_init=rel_pos_zero_init, window_size=window_size if i not in global_attn_indexes else 0, input_size=(img_size // patch_size, img_size // patch_size))
        self.blocks.append(block)
    self.neck = nn.Sequential(nn.Conv2d(embed_dim, out_chans, kernel_size=1, bias=False), LayerNorm2d(out_chans), nn.Conv2d(out_chans, out_chans, kernel_size=3, padding=1, bias=False), LayerNorm2d(out_chans))

class Block(nn.Module):
    """Transformer blocks with support of window attention and residual propagation blocks"""

    def __init__(self, dim: int, num_heads: int, mlp_ratio: float=4.0, qkv_bias: bool=True, norm_layer: Type[nn.Module]=nn.LayerNorm, act_layer: Type[nn.Module]=nn.GELU, use_rel_pos: bool=False, rel_pos_zero_init: bool=True, window_size: int=0, input_size: Optional[Tuple[int, int]]=None) -> None:
        """
        Args:
            dim (int): Number of input channels.
            num_heads (int): Number of attention heads in each ViT block.
            mlp_ratio (float): Ratio of mlp hidden dim to embedding dim.
            qkv_bias (bool): If True, add a learnable bias to query, key, value.
            norm_layer (nn.Module): Normalization layer.
            act_layer (nn.Module): Activation layer.
            use_rel_pos (bool): If True, add relative positional embeddings to the attention map.
            rel_pos_zero_init (bool): If True, zero initialize relative positional parameters.
            window_size (int): Window size for window attention blocks. If it equals 0, then
                use global attention.
            input_size (int or None): Input resolution for calculating the relative positional
                parameter size.
        """
        super().__init__()
        self.norm1 = norm_layer(dim)
        self.attn = Attention(dim, num_heads=num_heads, qkv_bias=qkv_bias, use_rel_pos=use_rel_pos, rel_pos_zero_init=rel_pos_zero_init, input_size=input_size if window_size == 0 else (window_size, window_size))
        self.norm2 = norm_layer(dim)
        self.mlp = MLPBlock(embedding_dim=dim, mlp_dim=int(dim * mlp_ratio), act=act_layer)
        self.window_size = window_size

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        shortcut = x
        x = self.norm1(x)
        if self.window_size > 0:
            H, W = (x.shape[1], x.shape[2])
            x, pad_hw = window_partition(x, self.window_size)
        x = self.attn(x)
        if self.window_size > 0:
            x = window_unpartition(x, self.window_size, pad_hw, (H, W))
        x = shortcut + x
        x = x + self.mlp(self.norm2(x))
        return x

def __init__(self, dim: int, num_heads: int, mlp_ratio: float=4.0, qkv_bias: bool=True, norm_layer: Type[nn.Module]=nn.LayerNorm, act_layer: Type[nn.Module]=nn.GELU, use_rel_pos: bool=False, rel_pos_zero_init: bool=True, window_size: int=0, input_size: Optional[Tuple[int, int]]=None) -> None:
    """
        Args:
            dim (int): Number of input channels.
            num_heads (int): Number of attention heads in each ViT block.
            mlp_ratio (float): Ratio of mlp hidden dim to embedding dim.
            qkv_bias (bool): If True, add a learnable bias to query, key, value.
            norm_layer (nn.Module): Normalization layer.
            act_layer (nn.Module): Activation layer.
            use_rel_pos (bool): If True, add relative positional embeddings to the attention map.
            rel_pos_zero_init (bool): If True, zero initialize relative positional parameters.
            window_size (int): Window size for window attention blocks. If it equals 0, then
                use global attention.
            input_size (int or None): Input resolution for calculating the relative positional
                parameter size.
        """
    super().__init__()
    self.norm1 = norm_layer(dim)
    self.attn = Attention(dim, num_heads=num_heads, qkv_bias=qkv_bias, use_rel_pos=use_rel_pos, rel_pos_zero_init=rel_pos_zero_init, input_size=input_size if window_size == 0 else (window_size, window_size))
    self.norm2 = norm_layer(dim)
    self.mlp = MLPBlock(embedding_dim=dim, mlp_dim=int(dim * mlp_ratio), act=act_layer)
    self.window_size = window_size

class Attention(nn.Module):
    """Multi-head Attention block with relative position embeddings."""

    def __init__(self, dim: int, num_heads: int=8, qkv_bias: bool=True, use_rel_pos: bool=False, rel_pos_zero_init: bool=True, input_size: Optional[Tuple[int, int]]=None) -> None:
        """
        Args:
            dim (int): Number of input channels.
            num_heads (int): Number of attention heads.
            qkv_bias (bool:  If True, add a learnable bias to query, key, value.
            rel_pos (bool): If True, add relative positional embeddings to the attention map.
            rel_pos_zero_init (bool): If True, zero initialize relative positional parameters.
            input_size (int or None): Input resolution for calculating the relative positional
                parameter size.
        """
        super().__init__()
        self.num_heads = num_heads
        head_dim = dim // num_heads
        self.scale = head_dim ** (-0.5)
        self.qkv = nn.Linear(dim, dim * 3, bias=qkv_bias)
        self.proj = nn.Linear(dim, dim)
        self.use_rel_pos = use_rel_pos
        if self.use_rel_pos:
            assert input_size is not None, 'Input size must be provided if using relative positional encoding.'
            self.rel_pos_h = nn.Parameter(torch.zeros(2 * input_size[0] - 1, head_dim))
            self.rel_pos_w = nn.Parameter(torch.zeros(2 * input_size[1] - 1, head_dim))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B, H, W, _ = x.shape
        qkv = self.qkv(x).reshape(B, H * W, 3, self.num_heads, -1).permute(2, 0, 3, 1, 4)
        q, k, v = qkv.reshape(3, B * self.num_heads, H * W, -1).unbind(0)
        attn = q * self.scale @ k.transpose(-2, -1)
        if self.use_rel_pos:
            attn = add_decomposed_rel_pos(attn, q, self.rel_pos_h, self.rel_pos_w, (H, W), (H, W))
        attn = attn.softmax(dim=-1)
        x = (attn @ v).view(B, self.num_heads, H, W, -1).permute(0, 2, 3, 1, 4).reshape(B, H, W, -1)
        x = self.proj(x)
        return x

def __init__(self, dim: int, num_heads: int=8, qkv_bias: bool=True, use_rel_pos: bool=False, rel_pos_zero_init: bool=True, input_size: Optional[Tuple[int, int]]=None) -> None:
    """
        Args:
            dim (int): Number of input channels.
            num_heads (int): Number of attention heads.
            qkv_bias (bool:  If True, add a learnable bias to query, key, value.
            rel_pos (bool): If True, add relative positional embeddings to the attention map.
            rel_pos_zero_init (bool): If True, zero initialize relative positional parameters.
            input_size (int or None): Input resolution for calculating the relative positional
                parameter size.
        """
    super().__init__()
    self.num_heads = num_heads
    head_dim = dim // num_heads
    self.scale = head_dim ** (-0.5)
    self.qkv = nn.Linear(dim, dim * 3, bias=qkv_bias)
    self.proj = nn.Linear(dim, dim)
    self.use_rel_pos = use_rel_pos
    if self.use_rel_pos:
        assert input_size is not None, 'Input size must be provided if using relative positional encoding.'
        self.rel_pos_h = nn.Parameter(torch.zeros(2 * input_size[0] - 1, head_dim))
        self.rel_pos_w = nn.Parameter(torch.zeros(2 * input_size[1] - 1, head_dim))

class PatchEmbed(nn.Module):
    """
    Image to Patch Embedding.
    """

    def __init__(self, kernel_size: Tuple[int, int]=(16, 16), stride: Tuple[int, int]=(16, 16), padding: Tuple[int, int]=(0, 0), in_chans: int=3, embed_dim: int=768) -> None:
        """
        Args:
            kernel_size (Tuple): kernel size of the projection layer.
            stride (Tuple): stride of the projection layer.
            padding (Tuple): padding size of the projection layer.
            in_chans (int): Number of input image channels.
            embed_dim (int):  embed_dim (int): Patch embedding dimension.
        """
        super().__init__()
        self.proj = nn.Conv2d(in_chans, embed_dim, kernel_size=kernel_size, stride=stride, padding=padding)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.proj(x)
        x = x.permute(0, 2, 3, 1)
        return x

def __init__(self, kernel_size: Tuple[int, int]=(16, 16), stride: Tuple[int, int]=(16, 16), padding: Tuple[int, int]=(0, 0), in_chans: int=3, embed_dim: int=768) -> None:
    """
        Args:
            kernel_size (Tuple): kernel size of the projection layer.
            stride (Tuple): stride of the projection layer.
            padding (Tuple): padding size of the projection layer.
            in_chans (int): Number of input image channels.
            embed_dim (int):  embed_dim (int): Patch embedding dimension.
        """
    super().__init__()
    self.proj = nn.Conv2d(in_chans, embed_dim, kernel_size=kernel_size, stride=stride, padding=padding)

class TwoWayTransformer(nn.Module):

    def __init__(self, depth: int, embedding_dim: int, num_heads: int, mlp_dim: int, activation: Type[nn.Module]=nn.ReLU, attention_downsample_rate: int=2) -> None:
        """
        A transformer decoder that attends to an input image using
        queries whose positional embedding is supplied.

        Args:
          depth (int): number of layers in the transformer
          embedding_dim (int): the channel dimension for the input embeddings
          num_heads (int): the number of heads for multihead attention. Must
            divide embedding_dim
          mlp_dim (int): the channel dimension internal to the MLP block
          activation (nn.Module): the activation to use in the MLP block
        """
        super().__init__()
        self.depth = depth
        self.embedding_dim = embedding_dim
        self.num_heads = num_heads
        self.mlp_dim = mlp_dim
        self.layers = nn.ModuleList()
        for i in range(depth):
            self.layers.append(TwoWayAttentionBlock(embedding_dim=embedding_dim, num_heads=num_heads, mlp_dim=mlp_dim, activation=activation, attention_downsample_rate=attention_downsample_rate, skip_first_layer_pe=i == 0))
        self.final_attn_token_to_image = Attention(embedding_dim, num_heads, downsample_rate=attention_downsample_rate)
        self.norm_final_attn = nn.LayerNorm(embedding_dim)

    def forward(self, image_embedding: Tensor, image_pe: Tensor, point_embedding: Tensor) -> Tuple[Tensor, Tensor]:
        """
        Args:
          image_embedding (torch.Tensor): image to attend to. Should be shape
            B x embedding_dim x h x w for any h and w.
          image_pe (torch.Tensor): the positional encoding to add to the image. Must
            have the same shape as image_embedding.
          point_embedding (torch.Tensor): the embedding to add to the query points.
            Must have shape B x N_points x embedding_dim for any N_points.

        Returns:
          torch.Tensor: the processed point_embedding
          torch.Tensor: the processed image_embedding
        """
        bs, c, h, w = image_embedding.shape
        image_embedding = image_embedding.flatten(2).permute(0, 2, 1)
        image_pe = image_pe.flatten(2).permute(0, 2, 1)
        queries = point_embedding
        keys = image_embedding
        for layer in self.layers:
            queries, keys = layer(queries=queries, keys=keys, query_pe=point_embedding, key_pe=image_pe)
        q = queries + point_embedding
        k = keys + image_pe
        attn_out = self.final_attn_token_to_image(q=q, k=k, v=keys)
        queries = queries + attn_out
        queries = self.norm_final_attn(queries)
        return (queries, keys)

def __init__(self, depth: int, embedding_dim: int, num_heads: int, mlp_dim: int, activation: Type[nn.Module]=nn.ReLU, attention_downsample_rate: int=2) -> None:
    """
        A transformer decoder that attends to an input image using
        queries whose positional embedding is supplied.

        Args:
          depth (int): number of layers in the transformer
          embedding_dim (int): the channel dimension for the input embeddings
          num_heads (int): the number of heads for multihead attention. Must
            divide embedding_dim
          mlp_dim (int): the channel dimension internal to the MLP block
          activation (nn.Module): the activation to use in the MLP block
        """
    super().__init__()
    self.depth = depth
    self.embedding_dim = embedding_dim
    self.num_heads = num_heads
    self.mlp_dim = mlp_dim
    self.layers = nn.ModuleList()
    for i in range(depth):
        self.layers.append(TwoWayAttentionBlock(embedding_dim=embedding_dim, num_heads=num_heads, mlp_dim=mlp_dim, activation=activation, attention_downsample_rate=attention_downsample_rate, skip_first_layer_pe=i == 0))
    self.final_attn_token_to_image = Attention(embedding_dim, num_heads, downsample_rate=attention_downsample_rate)
    self.norm_final_attn = nn.LayerNorm(embedding_dim)

class TwoWayAttentionBlock(nn.Module):

    def __init__(self, embedding_dim: int, num_heads: int, mlp_dim: int=2048, activation: Type[nn.Module]=nn.ReLU, attention_downsample_rate: int=2, skip_first_layer_pe: bool=False) -> None:
        """
        A transformer block with four layers: (1) self-attention of sparse
        inputs, (2) cross attention of sparse inputs to dense inputs, (3) mlp
        block on sparse inputs, and (4) cross attention of dense inputs to sparse
        inputs.

        Arguments:
          embedding_dim (int): the channel dimension of the embeddings
          num_heads (int): the number of heads in the attention layers
          mlp_dim (int): the hidden dimension of the mlp block
          activation (nn.Module): the activation of the mlp block
          skip_first_layer_pe (bool): skip the PE on the first layer
        """
        super().__init__()
        self.self_attn = Attention(embedding_dim, num_heads)
        self.norm1 = nn.LayerNorm(embedding_dim)
        self.cross_attn_token_to_image = Attention(embedding_dim, num_heads, downsample_rate=attention_downsample_rate)
        self.norm2 = nn.LayerNorm(embedding_dim)
        self.mlp = MLPBlock(embedding_dim, mlp_dim, activation)
        self.norm3 = nn.LayerNorm(embedding_dim)
        self.norm4 = nn.LayerNorm(embedding_dim)
        self.cross_attn_image_to_token = Attention(embedding_dim, num_heads, downsample_rate=attention_downsample_rate)
        self.skip_first_layer_pe = skip_first_layer_pe

    def forward(self, queries: Tensor, keys: Tensor, query_pe: Tensor, key_pe: Tensor) -> Tuple[Tensor, Tensor]:
        if self.skip_first_layer_pe:
            queries = self.self_attn(q=queries, k=queries, v=queries)
        else:
            q = queries + query_pe
            attn_out = self.self_attn(q=q, k=q, v=queries)
            queries = queries + attn_out
        queries = self.norm1(queries)
        q = queries + query_pe
        k = keys + key_pe
        attn_out = self.cross_attn_token_to_image(q=q, k=k, v=keys)
        queries = queries + attn_out
        queries = self.norm2(queries)
        mlp_out = self.mlp(queries)
        queries = queries + mlp_out
        queries = self.norm3(queries)
        q = queries + query_pe
        k = keys + key_pe
        attn_out = self.cross_attn_image_to_token(q=k, k=q, v=queries)
        keys = keys + attn_out
        keys = self.norm4(keys)
        return (queries, keys)

def __init__(self, embedding_dim: int, num_heads: int, mlp_dim: int=2048, activation: Type[nn.Module]=nn.ReLU, attention_downsample_rate: int=2, skip_first_layer_pe: bool=False) -> None:
    """
        A transformer block with four layers: (1) self-attention of sparse
        inputs, (2) cross attention of sparse inputs to dense inputs, (3) mlp
        block on sparse inputs, and (4) cross attention of dense inputs to sparse
        inputs.

        Arguments:
          embedding_dim (int): the channel dimension of the embeddings
          num_heads (int): the number of heads in the attention layers
          mlp_dim (int): the hidden dimension of the mlp block
          activation (nn.Module): the activation of the mlp block
          skip_first_layer_pe (bool): skip the PE on the first layer
        """
    super().__init__()
    self.self_attn = Attention(embedding_dim, num_heads)
    self.norm1 = nn.LayerNorm(embedding_dim)
    self.cross_attn_token_to_image = Attention(embedding_dim, num_heads, downsample_rate=attention_downsample_rate)
    self.norm2 = nn.LayerNorm(embedding_dim)
    self.mlp = MLPBlock(embedding_dim, mlp_dim, activation)
    self.norm3 = nn.LayerNorm(embedding_dim)
    self.norm4 = nn.LayerNorm(embedding_dim)
    self.cross_attn_image_to_token = Attention(embedding_dim, num_heads, downsample_rate=attention_downsample_rate)
    self.skip_first_layer_pe = skip_first_layer_pe

class Attention(nn.Module):
    """
    An attention layer that allows for downscaling the size of the embedding
    after projection to queries, keys, and values.
    """

    def __init__(self, embedding_dim: int, num_heads: int, downsample_rate: int=1) -> None:
        super().__init__()
        self.embedding_dim = embedding_dim
        self.internal_dim = embedding_dim // downsample_rate
        self.num_heads = num_heads
        assert self.internal_dim % num_heads == 0, 'num_heads must divide embedding_dim.'
        self.q_proj = nn.Linear(embedding_dim, self.internal_dim)
        self.k_proj = nn.Linear(embedding_dim, self.internal_dim)
        self.v_proj = nn.Linear(embedding_dim, self.internal_dim)
        self.out_proj = nn.Linear(self.internal_dim, embedding_dim)

    def _separate_heads(self, x: Tensor, num_heads: int) -> Tensor:
        b, n, c = x.shape
        x = x.reshape(b, n, num_heads, c // num_heads)
        return x.transpose(1, 2)

    def _recombine_heads(self, x: Tensor) -> Tensor:
        b, n_heads, n_tokens, c_per_head = x.shape
        x = x.transpose(1, 2)
        return x.reshape(b, n_tokens, n_heads * c_per_head)

    def forward(self, q: Tensor, k: Tensor, v: Tensor) -> Tensor:
        q = self.q_proj(q)
        k = self.k_proj(k)
        v = self.v_proj(v)
        q = self._separate_heads(q, self.num_heads)
        k = self._separate_heads(k, self.num_heads)
        v = self._separate_heads(v, self.num_heads)
        _, _, _, c_per_head = q.shape
        attn = q @ k.permute(0, 1, 3, 2)
        attn = attn / math.sqrt(c_per_head)
        attn = torch.softmax(attn, dim=-1)
        out = attn @ v
        out = self._recombine_heads(out)
        out = self.out_proj(out)
        return out

def __init__(self, embedding_dim: int, num_heads: int, downsample_rate: int=1) -> None:
    super().__init__()
    self.embedding_dim = embedding_dim
    self.internal_dim = embedding_dim // downsample_rate
    self.num_heads = num_heads
    assert self.internal_dim % num_heads == 0, 'num_heads must divide embedding_dim.'
    self.q_proj = nn.Linear(embedding_dim, self.internal_dim)
    self.k_proj = nn.Linear(embedding_dim, self.internal_dim)
    self.v_proj = nn.Linear(embedding_dim, self.internal_dim)
    self.out_proj = nn.Linear(self.internal_dim, embedding_dim)

class Sam(nn.Module):
    mask_threshold: float = 0.0
    image_format: str = 'RGB'

    def __init__(self, image_encoder: Union[ImageEncoderViT, TinyViT], prompt_encoder: PromptEncoder, mask_decoder: MaskDecoder, pixel_mean: List[float]=[123.675, 116.28, 103.53], pixel_std: List[float]=[58.395, 57.12, 57.375]) -> None:
        """
        SAM predicts object masks from an image and input prompts.

        Arguments:
          image_encoder (ImageEncoderViT): The backbone used to encode the
            image into image embeddings that allow for efficient mask prediction.
          prompt_encoder (PromptEncoder): Encodes various types of input prompts.
          mask_decoder (MaskDecoder): Predicts masks from the image embeddings
            and encoded prompts.
          pixel_mean (list(float)): Mean values for normalizing pixels in the input image.
          pixel_std (list(float)): Std values for normalizing pixels in the input image.
        """
        super().__init__()
        self.image_encoder = image_encoder
        self.prompt_encoder = prompt_encoder
        self.mask_decoder = mask_decoder
        self.register_buffer('pixel_mean', torch.Tensor(pixel_mean).view(-1, 1, 1), False)
        self.register_buffer('pixel_std', torch.Tensor(pixel_std).view(-1, 1, 1), False)

    @property
    def device(self) -> Any:
        return self.pixel_mean.device

    @torch.no_grad()
    def forward(self, batched_input: List[Dict[str, Any]], multimask_output: bool) -> List[Dict[str, torch.Tensor]]:
        """
        Predicts masks end-to-end from provided images and prompts.
        If prompts are not known in advance, using SamPredictor is
        recommended over calling the model directly.

        Arguments:
          batched_input (list(dict)): A list over input images, each a
            dictionary with the following keys. A prompt key can be
            excluded if it is not present.
              'image': The image as a torch tensor in 3xHxW format,
                already transformed for input to the model.
              'original_size': (tuple(int, int)) The original size of
                the image before transformation, as (H, W).
              'point_coords': (torch.Tensor) Batched point prompts for
                this image, with shape BxNx2. Already transformed to the
                input frame of the model.
              'point_labels': (torch.Tensor) Batched labels for point prompts,
                with shape BxN.
              'boxes': (torch.Tensor) Batched box inputs, with shape Bx4.
                Already transformed to the input frame of the model.
              'mask_inputs': (torch.Tensor) Batched mask inputs to the model,
                in the form Bx1xHxW.
          multimask_output (bool): Whether the model should predict multiple
            disambiguating masks, or return a single mask.

        Returns:
          (list(dict)): A list over input images, where each element is
            as dictionary with the following keys.
              'masks': (torch.Tensor) Batched binary mask predictions,
                with shape BxCxHxW, where B is the number of input promts,
                C is determiend by multimask_output, and (H, W) is the
                original size of the image.
              'iou_predictions': (torch.Tensor) The model's predictions
                of mask quality, in shape BxC.
              'low_res_logits': (torch.Tensor) Low resolution logits with
                shape BxCxHxW, where H=W=256. Can be passed as mask input
                to subsequent iterations of prediction.
        """
        input_images = torch.stack([self.preprocess(x['image']) for x in batched_input], dim=0)
        image_embeddings = self.image_encoder(input_images)
        outputs = []
        for image_record, curr_embedding in zip(batched_input, image_embeddings):
            if 'point_coords' in image_record:
                points = (image_record['point_coords'], image_record['point_labels'])
            else:
                points = None
            sparse_embeddings, dense_embeddings = self.prompt_encoder(points=points, boxes=image_record.get('boxes', None), masks=image_record.get('mask_inputs', None))
            low_res_masks, iou_predictions = self.mask_decoder(image_embeddings=curr_embedding.unsqueeze(0), image_pe=self.prompt_encoder.get_dense_pe(), sparse_prompt_embeddings=sparse_embeddings, dense_prompt_embeddings=dense_embeddings, multimask_output=multimask_output)
            masks = self.postprocess_masks(low_res_masks, input_size=image_record['image'].shape[-2:], original_size=image_record['original_size'])
            masks = masks > self.mask_threshold
            outputs.append({'masks': masks, 'iou_predictions': iou_predictions, 'low_res_logits': low_res_masks})
        return outputs

    def postprocess_masks(self, masks: torch.Tensor, input_size: Tuple[int, ...], original_size: Tuple[int, ...]) -> torch.Tensor:
        """
        Remove padding and upscale masks to the original image size.

        Arguments:
          masks (torch.Tensor): Batched masks from the mask_decoder,
            in BxCxHxW format.
          input_size (tuple(int, int)): The size of the image input to the
            model, in (H, W) format. Used to remove padding.
          original_size (tuple(int, int)): The original size of the image
            before resizing for input to the model, in (H, W) format.

        Returns:
          (torch.Tensor): Batched masks in BxCxHxW format, where (H, W)
            is given by original_size.
        """
        masks = F.interpolate(masks, (self.image_encoder.img_size, self.image_encoder.img_size), mode='bilinear', align_corners=False)
        masks = masks[..., :input_size[0], :input_size[1]]
        masks = F.interpolate(masks, original_size, mode='bilinear', align_corners=False)
        return masks

    def preprocess(self, x: torch.Tensor) -> torch.Tensor:
        """Normalize pixel values and pad to a square input."""
        x = (x - self.pixel_mean) / self.pixel_std
        h, w = x.shape[-2:]
        padh = self.image_encoder.img_size - h
        padw = self.image_encoder.img_size - w
        x = F.pad(x, (0, padw, 0, padh))
        return x

def __init__(self, image_encoder: Union[ImageEncoderViT, TinyViT], prompt_encoder: PromptEncoder, mask_decoder: MaskDecoder, pixel_mean: List[float]=[123.675, 116.28, 103.53], pixel_std: List[float]=[58.395, 57.12, 57.375]) -> None:
    """
        SAM predicts object masks from an image and input prompts.

        Arguments:
          image_encoder (ImageEncoderViT): The backbone used to encode the
            image into image embeddings that allow for efficient mask prediction.
          prompt_encoder (PromptEncoder): Encodes various types of input prompts.
          mask_decoder (MaskDecoder): Predicts masks from the image embeddings
            and encoded prompts.
          pixel_mean (list(float)): Mean values for normalizing pixels in the input image.
          pixel_std (list(float)): Std values for normalizing pixels in the input image.
        """
    super().__init__()
    self.image_encoder = image_encoder
    self.prompt_encoder = prompt_encoder
    self.mask_decoder = mask_decoder
    self.register_buffer('pixel_mean', torch.Tensor(pixel_mean).view(-1, 1, 1), False)
    self.register_buffer('pixel_std', torch.Tensor(pixel_std).view(-1, 1, 1), False)

class MaskDecoder(nn.Module):

    def __init__(self, *, transformer_dim: int, transformer: nn.Module, num_multimask_outputs: int=3, activation: Type[nn.Module]=nn.GELU, iou_head_depth: int=3, iou_head_hidden_dim: int=256) -> None:
        """
        Predicts masks given an image and prompt embeddings, using a
        tranformer architecture.

        Arguments:
          transformer_dim (int): the channel dimension of the transformer
          transformer (nn.Module): the transformer used to predict masks
          num_multimask_outputs (int): the number of masks to predict
            when disambiguating masks
          activation (nn.Module): the type of activation to use when
            upscaling masks
          iou_head_depth (int): the depth of the MLP used to predict
            mask quality
          iou_head_hidden_dim (int): the hidden dimension of the MLP
            used to predict mask quality
        """
        super().__init__()
        self.transformer_dim = transformer_dim
        self.transformer = transformer
        self.num_multimask_outputs = num_multimask_outputs
        self.iou_token = nn.Embedding(1, transformer_dim)
        self.num_mask_tokens = num_multimask_outputs + 1
        self.mask_tokens = nn.Embedding(self.num_mask_tokens, transformer_dim)
        self.output_upscaling = nn.Sequential(nn.ConvTranspose2d(transformer_dim, transformer_dim // 4, kernel_size=2, stride=2), LayerNorm2d(transformer_dim // 4), activation(), nn.ConvTranspose2d(transformer_dim // 4, transformer_dim // 8, kernel_size=2, stride=2), activation())
        self.output_hypernetworks_mlps = nn.ModuleList([MLP(transformer_dim, transformer_dim, transformer_dim // 8, 3) for i in range(self.num_mask_tokens)])
        self.iou_prediction_head = MLP(transformer_dim, iou_head_hidden_dim, self.num_mask_tokens, iou_head_depth)

    def forward(self, image_embeddings: torch.Tensor, image_pe: torch.Tensor, sparse_prompt_embeddings: torch.Tensor, dense_prompt_embeddings: torch.Tensor, multimask_output: bool) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Predict masks given image and prompt embeddings.

        Arguments:
          image_embeddings (torch.Tensor): the embeddings from the image encoder
          image_pe (torch.Tensor): positional encoding with the shape of image_embeddings
          sparse_prompt_embeddings (torch.Tensor): the embeddings of the points and boxes
          dense_prompt_embeddings (torch.Tensor): the embeddings of the mask inputs
          multimask_output (bool): Whether to return multiple masks or a single
            mask.

        Returns:
          torch.Tensor: batched predicted masks
          torch.Tensor: batched predictions of mask quality
        """
        masks, iou_pred = self.predict_masks(image_embeddings=image_embeddings, image_pe=image_pe, sparse_prompt_embeddings=sparse_prompt_embeddings, dense_prompt_embeddings=dense_prompt_embeddings)
        if multimask_output:
            mask_slice = slice(1, None)
        else:
            mask_slice = slice(0, 1)
        masks = masks[:, mask_slice, :, :]
        iou_pred = iou_pred[:, mask_slice]
        return (masks, iou_pred)

    def predict_masks(self, image_embeddings: torch.Tensor, image_pe: torch.Tensor, sparse_prompt_embeddings: torch.Tensor, dense_prompt_embeddings: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Predicts masks. See 'forward' for more details."""
        output_tokens = torch.cat([self.iou_token.weight, self.mask_tokens.weight], dim=0)
        output_tokens = output_tokens.unsqueeze(0).expand(sparse_prompt_embeddings.size(0), -1, -1)
        tokens = torch.cat((output_tokens, sparse_prompt_embeddings), dim=1)
        src = torch.repeat_interleave(image_embeddings, tokens.shape[0], dim=0)
        src = src + dense_prompt_embeddings
        pos_src = torch.repeat_interleave(image_pe, tokens.shape[0], dim=0)
        b, c, h, w = src.shape
        hs, src = self.transformer(src, pos_src, tokens)
        iou_token_out = hs[:, 0, :]
        mask_tokens_out = hs[:, 1:1 + self.num_mask_tokens, :]
        src = src.transpose(1, 2).view(b, c, h, w)
        upscaled_embedding = self.output_upscaling(src)
        hyper_in_list: List[torch.Tensor] = []
        for i in range(self.num_mask_tokens):
            hyper_in_list.append(self.output_hypernetworks_mlps[i](mask_tokens_out[:, i, :]))
        hyper_in = torch.stack(hyper_in_list, dim=1)
        b, c, h, w = upscaled_embedding.shape
        masks = (hyper_in @ upscaled_embedding.view(b, c, h * w)).view(b, -1, h, w)
        iou_pred = self.iou_prediction_head(iou_token_out)
        return (masks, iou_pred)

def __init__(self, *, transformer_dim: int, transformer: nn.Module, num_multimask_outputs: int=3, activation: Type[nn.Module]=nn.GELU, iou_head_depth: int=3, iou_head_hidden_dim: int=256) -> None:
    """
        Predicts masks given an image and prompt embeddings, using a
        tranformer architecture.

        Arguments:
          transformer_dim (int): the channel dimension of the transformer
          transformer (nn.Module): the transformer used to predict masks
          num_multimask_outputs (int): the number of masks to predict
            when disambiguating masks
          activation (nn.Module): the type of activation to use when
            upscaling masks
          iou_head_depth (int): the depth of the MLP used to predict
            mask quality
          iou_head_hidden_dim (int): the hidden dimension of the MLP
            used to predict mask quality
        """
    super().__init__()
    self.transformer_dim = transformer_dim
    self.transformer = transformer
    self.num_multimask_outputs = num_multimask_outputs
    self.iou_token = nn.Embedding(1, transformer_dim)
    self.num_mask_tokens = num_multimask_outputs + 1
    self.mask_tokens = nn.Embedding(self.num_mask_tokens, transformer_dim)
    self.output_upscaling = nn.Sequential(nn.ConvTranspose2d(transformer_dim, transformer_dim // 4, kernel_size=2, stride=2), LayerNorm2d(transformer_dim // 4), activation(), nn.ConvTranspose2d(transformer_dim // 4, transformer_dim // 8, kernel_size=2, stride=2), activation())
    self.output_hypernetworks_mlps = nn.ModuleList([MLP(transformer_dim, transformer_dim, transformer_dim // 8, 3) for i in range(self.num_mask_tokens)])
    self.iou_prediction_head = MLP(transformer_dim, iou_head_hidden_dim, self.num_mask_tokens, iou_head_depth)

class MLP(nn.Module):

    def __init__(self, input_dim: int, hidden_dim: int, output_dim: int, num_layers: int, sigmoid_output: bool=False) -> None:
        super().__init__()
        self.num_layers = num_layers
        h = [hidden_dim] * (num_layers - 1)
        self.layers = nn.ModuleList((nn.Linear(n, k) for n, k in zip([input_dim] + h, h + [output_dim])))
        self.sigmoid_output = sigmoid_output

    def forward(self, x):
        for i, layer in enumerate(self.layers):
            x = F.relu(layer(x)) if i < self.num_layers - 1 else layer(x)
        if self.sigmoid_output:
            x = F.sigmoid(x)
        return x

def __init__(self, input_dim: int, hidden_dim: int, output_dim: int, num_layers: int, sigmoid_output: bool=False) -> None:
    super().__init__()
    self.num_layers = num_layers
    h = [hidden_dim] * (num_layers - 1)
    self.layers = nn.ModuleList((nn.Linear(n, k) for n, k in zip([input_dim] + h, h + [output_dim])))
    self.sigmoid_output = sigmoid_output

class PromptEncoder(nn.Module):

    def __init__(self, embed_dim: int, image_embedding_size: Tuple[int, int], input_image_size: Tuple[int, int], mask_in_chans: int, activation: Type[nn.Module]=nn.GELU) -> None:
        """
        Encodes prompts for input to SAM's mask decoder.

        Arguments:
          embed_dim (int): The prompts' embedding dimension
          image_embedding_size (tuple(int, int)): The spatial size of the
            image embedding, as (H, W).
          input_image_size (int): The padded size of the image as input
            to the image encoder, as (H, W).
          mask_in_chans (int): The number of hidden channels used for
            encoding input masks.
          activation (nn.Module): The activation to use when encoding
            input masks.
        """
        super().__init__()
        self.embed_dim = embed_dim
        self.input_image_size = input_image_size
        self.image_embedding_size = image_embedding_size
        self.pe_layer = PositionEmbeddingRandom(embed_dim // 2)
        self.num_point_embeddings: int = 4
        point_embeddings = [nn.Embedding(1, embed_dim) for i in range(self.num_point_embeddings)]
        self.point_embeddings = nn.ModuleList(point_embeddings)
        self.not_a_point_embed = nn.Embedding(1, embed_dim)
        self.mask_input_size = (4 * image_embedding_size[0], 4 * image_embedding_size[1])
        self.mask_downscaling = nn.Sequential(nn.Conv2d(1, mask_in_chans // 4, kernel_size=2, stride=2), LayerNorm2d(mask_in_chans // 4), activation(), nn.Conv2d(mask_in_chans // 4, mask_in_chans, kernel_size=2, stride=2), LayerNorm2d(mask_in_chans), activation(), nn.Conv2d(mask_in_chans, embed_dim, kernel_size=1))
        self.no_mask_embed = nn.Embedding(1, embed_dim)

    def get_dense_pe(self) -> torch.Tensor:
        """
        Returns the positional encoding used to encode point prompts,
        applied to a dense set of points the shape of the image encoding.

        Returns:
          torch.Tensor: Positional encoding with shape
            1x(embed_dim)x(embedding_h)x(embedding_w)
        """
        return self.pe_layer(self.image_embedding_size).unsqueeze(0)

    def _embed_points(self, points: torch.Tensor, labels: torch.Tensor, pad: bool) -> torch.Tensor:
        """Embeds point prompts."""
        points = points + 0.5
        if pad:
            padding_point = torch.zeros((points.shape[0], 1, 2), device=points.device)
            padding_label = -torch.ones((labels.shape[0], 1), device=labels.device)
            points = torch.cat([points, padding_point], dim=1)
            labels = torch.cat([labels, padding_label], dim=1)
        point_embedding = self.pe_layer.forward_with_coords(points, self.input_image_size)
        point_embedding[labels == -1] = 0.0
        point_embedding[labels == -1] += self.not_a_point_embed.weight
        point_embedding[labels == 0] += self.point_embeddings[0].weight
        point_embedding[labels == 1] += self.point_embeddings[1].weight
        return point_embedding

    def _embed_boxes(self, boxes: torch.Tensor) -> torch.Tensor:
        """Embeds box prompts."""
        boxes = boxes + 0.5
        coords = boxes.reshape(-1, 2, 2)
        corner_embedding = self.pe_layer.forward_with_coords(coords, self.input_image_size)
        corner_embedding[:, 0, :] += self.point_embeddings[2].weight
        corner_embedding[:, 1, :] += self.point_embeddings[3].weight
        return corner_embedding

    def _embed_masks(self, masks: torch.Tensor) -> torch.Tensor:
        """Embeds mask inputs."""
        mask_embedding = self.mask_downscaling(masks)
        return mask_embedding

    def _get_batch_size(self, points: Optional[Tuple[torch.Tensor, torch.Tensor]], boxes: Optional[torch.Tensor], masks: Optional[torch.Tensor]) -> int:
        """
        Gets the batch size of the output given the batch size of the input prompts.
        """
        if points is not None:
            return points[0].shape[0]
        elif boxes is not None:
            return boxes.shape[0]
        elif masks is not None:
            return masks.shape[0]
        else:
            return 1

    def _get_device(self) -> torch.device:
        return self.point_embeddings[0].weight.device

    def forward(self, points: Optional[Tuple[torch.Tensor, torch.Tensor]], boxes: Optional[torch.Tensor], masks: Optional[torch.Tensor]) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Embeds different types of prompts, returning both sparse and dense
        embeddings.

        Arguments:
          points (tuple(torch.Tensor, torch.Tensor) or none): point coordinates
            and labels to embed.
          boxes (torch.Tensor or none): boxes to embed
          masks (torch.Tensor or none): masks to embed

        Returns:
          torch.Tensor: sparse embeddings for the points and boxes, with shape
            BxNx(embed_dim), where N is determined by the number of input points
            and boxes.
          torch.Tensor: dense embeddings for the masks, in the shape
            Bx(embed_dim)x(embed_H)x(embed_W)
        """
        bs = self._get_batch_size(points, boxes, masks)
        sparse_embeddings = torch.empty((bs, 0, self.embed_dim), device=self._get_device())
        if points is not None:
            coords, labels = points
            point_embeddings = self._embed_points(coords, labels, pad=boxes is None)
            sparse_embeddings = torch.cat([sparse_embeddings, point_embeddings], dim=1)
        if boxes is not None:
            box_embeddings = self._embed_boxes(boxes)
            sparse_embeddings = torch.cat([sparse_embeddings, box_embeddings], dim=1)
        if masks is not None:
            dense_embeddings = self._embed_masks(masks)
        else:
            dense_embeddings = self.no_mask_embed.weight.reshape(1, -1, 1, 1).expand(bs, -1, self.image_embedding_size[0], self.image_embedding_size[1])
        return (sparse_embeddings, dense_embeddings)

def __init__(self, embed_dim: int, image_embedding_size: Tuple[int, int], input_image_size: Tuple[int, int], mask_in_chans: int, activation: Type[nn.Module]=nn.GELU) -> None:
    """
        Encodes prompts for input to SAM's mask decoder.

        Arguments:
          embed_dim (int): The prompts' embedding dimension
          image_embedding_size (tuple(int, int)): The spatial size of the
            image embedding, as (H, W).
          input_image_size (int): The padded size of the image as input
            to the image encoder, as (H, W).
          mask_in_chans (int): The number of hidden channels used for
            encoding input masks.
          activation (nn.Module): The activation to use when encoding
            input masks.
        """
    super().__init__()
    self.embed_dim = embed_dim
    self.input_image_size = input_image_size
    self.image_embedding_size = image_embedding_size
    self.pe_layer = PositionEmbeddingRandom(embed_dim // 2)
    self.num_point_embeddings: int = 4
    point_embeddings = [nn.Embedding(1, embed_dim) for i in range(self.num_point_embeddings)]
    self.point_embeddings = nn.ModuleList(point_embeddings)
    self.not_a_point_embed = nn.Embedding(1, embed_dim)
    self.mask_input_size = (4 * image_embedding_size[0], 4 * image_embedding_size[1])
    self.mask_downscaling = nn.Sequential(nn.Conv2d(1, mask_in_chans // 4, kernel_size=2, stride=2), LayerNorm2d(mask_in_chans // 4), activation(), nn.Conv2d(mask_in_chans // 4, mask_in_chans, kernel_size=2, stride=2), LayerNorm2d(mask_in_chans), activation(), nn.Conv2d(mask_in_chans, embed_dim, kernel_size=1))
    self.no_mask_embed = nn.Embedding(1, embed_dim)

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

def __init__(self, num_pos_feats: int=64, scale: Optional[float]=None) -> None:
    super().__init__()
    if scale is None or scale <= 0.0:
        scale = 1.0
    self.register_buffer('positional_encoding_gaussian_matrix', scale * torch.randn((2, num_pos_feats)))

class MLPBlock(nn.Module):

    def __init__(self, embedding_dim: int, mlp_dim: int, act: Type[nn.Module]=nn.GELU) -> None:
        super().__init__()
        self.lin1 = nn.Linear(embedding_dim, mlp_dim)
        self.lin2 = nn.Linear(mlp_dim, embedding_dim)
        self.act = act()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.lin2(self.act(self.lin1(x)))

def __init__(self, embedding_dim: int, mlp_dim: int, act: Type[nn.Module]=nn.GELU) -> None:
    super().__init__()
    self.lin1 = nn.Linear(embedding_dim, mlp_dim)
    self.lin2 = nn.Linear(mlp_dim, embedding_dim)
    self.act = act()

class LayerNorm2d(nn.Module):

    def __init__(self, num_channels: int, eps: float=1e-06) -> None:
        super().__init__()
        self.weight = nn.Parameter(torch.ones(num_channels))
        self.bias = nn.Parameter(torch.zeros(num_channels))
        self.eps = eps

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        u = x.mean(1, keepdim=True)
        s = (x - u).pow(2).mean(1, keepdim=True)
        x = (x - u) / torch.sqrt(s + self.eps)
        x = self.weight[:, None, None] * x + self.bias[:, None, None]
        return x

def __init__(self, num_channels: int, eps: float=1e-06) -> None:
    super().__init__()
    self.weight = nn.Parameter(torch.ones(num_channels))
    self.bias = nn.Parameter(torch.zeros(num_channels))
    self.eps = eps

class Conv2d_BN(torch.nn.Sequential):

    def __init__(self, a, b, ks=1, stride=1, pad=0, dilation=1, groups=1, bn_weight_init=1):
        super().__init__()
        self.add_module('c', torch.nn.Conv2d(a, b, ks, stride, pad, dilation, groups, bias=False))
        bn = torch.nn.BatchNorm2d(b)
        torch.nn.init.constant_(bn.weight, bn_weight_init)
        torch.nn.init.constant_(bn.bias, 0)
        self.add_module('bn', bn)

    @torch.no_grad()
    def fuse(self):
        c, bn = self._modules.values()
        w = bn.weight / (bn.running_var + bn.eps) ** 0.5
        w = c.weight * w[:, None, None, None]
        b = bn.bias - bn.running_mean * bn.weight / (bn.running_var + bn.eps) ** 0.5
        m = torch.nn.Conv2d(w.size(1) * self.c.groups, w.size(0), w.shape[2:], stride=self.c.stride, padding=self.c.padding, dilation=self.c.dilation, groups=self.c.groups)
        m.weight.data.copy_(w)
        m.bias.data.copy_(b)
        return m

def __init__(self, a, b, ks=1, stride=1, pad=0, dilation=1, groups=1, bn_weight_init=1):
    super().__init__()
    self.add_module('c', torch.nn.Conv2d(a, b, ks, stride, pad, dilation, groups, bias=False))
    bn = torch.nn.BatchNorm2d(b)
    torch.nn.init.constant_(bn.weight, bn_weight_init)
    torch.nn.init.constant_(bn.bias, 0)
    self.add_module('bn', bn)

@torch.no_grad()
def fuse(self):
    c, bn = self._modules.values()
    w = bn.weight / (bn.running_var + bn.eps) ** 0.5
    w = c.weight * w[:, None, None, None]
    b = bn.bias - bn.running_mean * bn.weight / (bn.running_var + bn.eps) ** 0.5
    m = torch.nn.Conv2d(w.size(1) * self.c.groups, w.size(0), w.shape[2:], stride=self.c.stride, padding=self.c.padding, dilation=self.c.dilation, groups=self.c.groups)
    m.weight.data.copy_(w)
    m.bias.data.copy_(b)
    return m

class DropPath(TimmDropPath):

    def __init__(self, drop_prob=None):
        super().__init__(drop_prob=drop_prob)
        self.drop_prob = drop_prob

    def __repr__(self):
        msg = super().__repr__()
        msg += f'(drop_prob={self.drop_prob})'
        return msg

def __init__(self, drop_prob=None):
    super().__init__(drop_prob=drop_prob)
    self.drop_prob = drop_prob

def __repr__(self):
    msg = super().__repr__()
    msg += f'(drop_prob={self.drop_prob})'
    return msg

class PatchEmbed(nn.Module):

    def __init__(self, in_chans, embed_dim, resolution, activation):
        super().__init__()
        img_size: Tuple[int, int] = to_2tuple(resolution)
        self.patches_resolution = (img_size[0] // 4, img_size[1] // 4)
        self.num_patches = self.patches_resolution[0] * self.patches_resolution[1]
        self.in_chans = in_chans
        self.embed_dim = embed_dim
        n = embed_dim
        self.seq = nn.Sequential(Conv2d_BN(in_chans, n // 2, 3, 2, 1), activation(), Conv2d_BN(n // 2, n, 3, 2, 1))

    def forward(self, x):
        return self.seq(x)

def __init__(self, in_chans, embed_dim, resolution, activation):
    super().__init__()
    img_size: Tuple[int, int] = to_2tuple(resolution)
    self.patches_resolution = (img_size[0] // 4, img_size[1] // 4)
    self.num_patches = self.patches_resolution[0] * self.patches_resolution[1]
    self.in_chans = in_chans
    self.embed_dim = embed_dim
    n = embed_dim
    self.seq = nn.Sequential(Conv2d_BN(in_chans, n // 2, 3, 2, 1), activation(), Conv2d_BN(n // 2, n, 3, 2, 1))

class MBConv(nn.Module):

    def __init__(self, in_chans, out_chans, expand_ratio, activation, drop_path):
        super().__init__()
        self.in_chans = in_chans
        self.hidden_chans = int(in_chans * expand_ratio)
        self.out_chans = out_chans
        self.conv1 = Conv2d_BN(in_chans, self.hidden_chans, ks=1)
        self.act1 = activation()
        self.conv2 = Conv2d_BN(self.hidden_chans, self.hidden_chans, ks=3, stride=1, pad=1, groups=self.hidden_chans)
        self.act2 = activation()
        self.conv3 = Conv2d_BN(self.hidden_chans, out_chans, ks=1, bn_weight_init=0.0)
        self.act3 = activation()
        self.drop_path = DropPath(drop_path) if drop_path > 0.0 else nn.Identity()

    def forward(self, x):
        shortcut = x
        x = self.conv1(x)
        x = self.act1(x)
        x = self.conv2(x)
        x = self.act2(x)
        x = self.conv3(x)
        x = self.drop_path(x)
        x += shortcut
        x = self.act3(x)
        return x

def __init__(self, in_chans, out_chans, expand_ratio, activation, drop_path):
    super().__init__()
    self.in_chans = in_chans
    self.hidden_chans = int(in_chans * expand_ratio)
    self.out_chans = out_chans
    self.conv1 = Conv2d_BN(in_chans, self.hidden_chans, ks=1)
    self.act1 = activation()
    self.conv2 = Conv2d_BN(self.hidden_chans, self.hidden_chans, ks=3, stride=1, pad=1, groups=self.hidden_chans)
    self.act2 = activation()
    self.conv3 = Conv2d_BN(self.hidden_chans, out_chans, ks=1, bn_weight_init=0.0)
    self.act3 = activation()
    self.drop_path = DropPath(drop_path) if drop_path > 0.0 else nn.Identity()

class PatchMerging(nn.Module):

    def __init__(self, input_resolution, dim, out_dim, activation):
        super().__init__()
        self.input_resolution = input_resolution
        self.dim = dim
        self.out_dim = out_dim
        self.act = activation()
        self.conv1 = Conv2d_BN(dim, out_dim, 1, 1, 0)
        stride_c = 2
        if out_dim == 320 or out_dim == 448 or out_dim == 576:
            stride_c = 1
        self.conv2 = Conv2d_BN(out_dim, out_dim, 3, stride_c, 1, groups=out_dim)
        self.conv3 = Conv2d_BN(out_dim, out_dim, 1, 1, 0)

    def forward(self, x):
        if x.ndim == 3:
            H, W = self.input_resolution
            B = len(x)
            x = x.view(B, H, W, -1).permute(0, 3, 1, 2)
        x = self.conv1(x)
        x = self.act(x)
        x = self.conv2(x)
        x = self.act(x)
        x = self.conv3(x)
        x = x.flatten(2).transpose(1, 2)
        return x

def __init__(self, input_resolution, dim, out_dim, activation):
    super().__init__()
    self.input_resolution = input_resolution
    self.dim = dim
    self.out_dim = out_dim
    self.act = activation()
    self.conv1 = Conv2d_BN(dim, out_dim, 1, 1, 0)
    stride_c = 2
    if out_dim == 320 or out_dim == 448 or out_dim == 576:
        stride_c = 1
    self.conv2 = Conv2d_BN(out_dim, out_dim, 3, stride_c, 1, groups=out_dim)
    self.conv3 = Conv2d_BN(out_dim, out_dim, 1, 1, 0)

class ConvLayer(nn.Module):

    def __init__(self, dim, input_resolution, depth, activation, drop_path=0.0, downsample=None, use_checkpoint=False, out_dim=None, conv_expand_ratio=4.0):
        super().__init__()
        self.dim = dim
        self.input_resolution = input_resolution
        self.depth = depth
        self.use_checkpoint = use_checkpoint
        self.blocks = nn.ModuleList([MBConv(dim, dim, conv_expand_ratio, activation, drop_path[i] if isinstance(drop_path, list) else drop_path) for i in range(depth)])
        if downsample is not None:
            self.downsample = downsample(input_resolution, dim=dim, out_dim=out_dim, activation=activation)
        else:
            self.downsample = None

    def forward(self, x):
        for blk in self.blocks:
            if self.use_checkpoint:
                x = checkpoint.checkpoint(blk, x)
            else:
                x = blk(x)
        if self.downsample is not None:
            x = self.downsample(x)
        return x

def __init__(self, dim, input_resolution, depth, activation, drop_path=0.0, downsample=None, use_checkpoint=False, out_dim=None, conv_expand_ratio=4.0):
    super().__init__()
    self.dim = dim
    self.input_resolution = input_resolution
    self.depth = depth
    self.use_checkpoint = use_checkpoint
    self.blocks = nn.ModuleList([MBConv(dim, dim, conv_expand_ratio, activation, drop_path[i] if isinstance(drop_path, list) else drop_path) for i in range(depth)])
    if downsample is not None:
        self.downsample = downsample(input_resolution, dim=dim, out_dim=out_dim, activation=activation)
    else:
        self.downsample = None

class Mlp(nn.Module):

    def __init__(self, in_features, hidden_features=None, out_features=None, act_layer=nn.GELU, drop=0.0):
        super().__init__()
        out_features = out_features or in_features
        hidden_features = hidden_features or in_features
        self.norm = nn.LayerNorm(in_features)
        self.fc1 = nn.Linear(in_features, hidden_features)
        self.fc2 = nn.Linear(hidden_features, out_features)
        self.act = act_layer()
        self.drop = nn.Dropout(drop)

    def forward(self, x):
        x = self.norm(x)
        x = self.fc1(x)
        x = self.act(x)
        x = self.drop(x)
        x = self.fc2(x)
        x = self.drop(x)
        return x

def __init__(self, in_features, hidden_features=None, out_features=None, act_layer=nn.GELU, drop=0.0):
    super().__init__()
    out_features = out_features or in_features
    hidden_features = hidden_features or in_features
    self.norm = nn.LayerNorm(in_features)
    self.fc1 = nn.Linear(in_features, hidden_features)
    self.fc2 = nn.Linear(hidden_features, out_features)
    self.act = act_layer()
    self.drop = nn.Dropout(drop)

class Attention(torch.nn.Module):

    def __init__(self, dim, key_dim, num_heads=8, attn_ratio=4, resolution=(14, 14)):
        super().__init__()
        assert isinstance(resolution, tuple) and len(resolution) == 2
        self.num_heads = num_heads
        self.scale = key_dim ** (-0.5)
        self.key_dim = key_dim
        self.nh_kd = nh_kd = key_dim * num_heads
        self.d = int(attn_ratio * key_dim)
        self.dh = int(attn_ratio * key_dim) * num_heads
        self.attn_ratio = attn_ratio
        h = self.dh + nh_kd * 2
        self.norm = nn.LayerNorm(dim)
        self.qkv = nn.Linear(dim, h)
        self.proj = nn.Linear(self.dh, dim)
        points = list(itertools.product(range(resolution[0]), range(resolution[1])))
        N = len(points)
        attention_offsets = {}
        idxs = []
        for p1 in points:
            for p2 in points:
                offset = (abs(p1[0] - p2[0]), abs(p1[1] - p2[1]))
                if offset not in attention_offsets:
                    attention_offsets[offset] = len(attention_offsets)
                idxs.append(attention_offsets[offset])
        self.attention_biases = torch.nn.Parameter(torch.zeros(num_heads, len(attention_offsets)))
        self.register_buffer('attention_bias_idxs', torch.LongTensor(idxs).view(N, N), persistent=False)

    @torch.no_grad()
    def train(self, mode=True):
        super().train(mode)
        if mode and hasattr(self, 'ab'):
            del self.ab
        else:
            self.register_buffer('ab', self.attention_biases[:, self.attention_bias_idxs], persistent=False)

    def forward(self, x):
        B, N, _ = x.shape
        x = self.norm(x)
        qkv = self.qkv(x)
        q, k, v = qkv.view(B, N, self.num_heads, -1).split([self.key_dim, self.key_dim, self.d], dim=3)
        q = q.permute(0, 2, 1, 3)
        k = k.permute(0, 2, 1, 3)
        v = v.permute(0, 2, 1, 3)
        attn = q @ k.transpose(-2, -1) * self.scale + (self.attention_biases[:, self.attention_bias_idxs] if self.training else self.ab)
        attn = attn.softmax(dim=-1)
        x = (attn @ v).transpose(1, 2).reshape(B, N, self.dh)
        x = self.proj(x)
        return x

def __init__(self, dim, key_dim, num_heads=8, attn_ratio=4, resolution=(14, 14)):
    super().__init__()
    assert isinstance(resolution, tuple) and len(resolution) == 2
    self.num_heads = num_heads
    self.scale = key_dim ** (-0.5)
    self.key_dim = key_dim
    self.nh_kd = nh_kd = key_dim * num_heads
    self.d = int(attn_ratio * key_dim)
    self.dh = int(attn_ratio * key_dim) * num_heads
    self.attn_ratio = attn_ratio
    h = self.dh + nh_kd * 2
    self.norm = nn.LayerNorm(dim)
    self.qkv = nn.Linear(dim, h)
    self.proj = nn.Linear(self.dh, dim)
    points = list(itertools.product(range(resolution[0]), range(resolution[1])))
    N = len(points)
    attention_offsets = {}
    idxs = []
    for p1 in points:
        for p2 in points:
            offset = (abs(p1[0] - p2[0]), abs(p1[1] - p2[1]))
            if offset not in attention_offsets:
                attention_offsets[offset] = len(attention_offsets)
            idxs.append(attention_offsets[offset])
    self.attention_biases = torch.nn.Parameter(torch.zeros(num_heads, len(attention_offsets)))
    self.register_buffer('attention_bias_idxs', torch.LongTensor(idxs).view(N, N), persistent=False)

@torch.no_grad()
def train(self, mode=True):
    super().train(mode)
    if mode and hasattr(self, 'ab'):
        del self.ab
    else:
        self.register_buffer('ab', self.attention_biases[:, self.attention_bias_idxs], persistent=False)

class TinyViTBlock(nn.Module):
    """ TinyViT Block.

    Args:
        dim (int): Number of input channels.
        input_resolution (tuple[int, int]): Input resulotion.
        num_heads (int): Number of attention heads.
        window_size (int): Window size.
        mlp_ratio (float): Ratio of mlp hidden dim to embedding dim.
        drop (float, optional): Dropout rate. Default: 0.0
        drop_path (float, optional): Stochastic depth rate. Default: 0.0
        local_conv_size (int): the kernel size of the convolution between
                               Attention and MLP. Default: 3
        activation: the activation function. Default: nn.GELU
    """

    def __init__(self, dim, input_resolution, num_heads, window_size=7, mlp_ratio=4.0, drop=0.0, drop_path=0.0, local_conv_size=3, activation=nn.GELU):
        super().__init__()
        self.dim = dim
        self.input_resolution = input_resolution
        self.num_heads = num_heads
        assert window_size > 0, 'window_size must be greater than 0'
        self.window_size = window_size
        self.mlp_ratio = mlp_ratio
        self.drop_path = DropPath(drop_path) if drop_path > 0.0 else nn.Identity()
        assert dim % num_heads == 0, 'dim must be divisible by num_heads'
        head_dim = dim // num_heads
        window_resolution = (window_size, window_size)
        self.attn = Attention(dim, head_dim, num_heads, attn_ratio=1, resolution=window_resolution)
        mlp_hidden_dim = int(dim * mlp_ratio)
        mlp_activation = activation
        self.mlp = Mlp(in_features=dim, hidden_features=mlp_hidden_dim, act_layer=mlp_activation, drop=drop)
        pad = local_conv_size // 2
        self.local_conv = Conv2d_BN(dim, dim, ks=local_conv_size, stride=1, pad=pad, groups=dim)

    def forward(self, x):
        H, W = self.input_resolution
        B, L, C = x.shape
        assert L == H * W, 'input feature has wrong size'
        res_x = x
        if H == self.window_size and W == self.window_size:
            x = self.attn(x)
        else:
            x = x.view(B, H, W, C)
            pad_b = (self.window_size - H % self.window_size) % self.window_size
            pad_r = (self.window_size - W % self.window_size) % self.window_size
            padding = pad_b > 0 or pad_r > 0
            if padding:
                x = F.pad(x, (0, 0, 0, pad_r, 0, pad_b))
            pH, pW = (H + pad_b, W + pad_r)
            nH = pH // self.window_size
            nW = pW // self.window_size
            x = x.view(B, nH, self.window_size, nW, self.window_size, C).transpose(2, 3).reshape(B * nH * nW, self.window_size * self.window_size, C)
            x = self.attn(x)
            x = x.view(B, nH, nW, self.window_size, self.window_size, C).transpose(2, 3).reshape(B, pH, pW, C)
            if padding:
                x = x[:, :H, :W].contiguous()
            x = x.view(B, L, C)
        x = res_x + self.drop_path(x)
        x = x.transpose(1, 2).reshape(B, C, H, W)
        x = self.local_conv(x)
        x = x.view(B, C, L).transpose(1, 2)
        x = x + self.drop_path(self.mlp(x))
        return x

    def extra_repr(self) -> str:
        return f'dim={self.dim}, input_resolution={self.input_resolution}, num_heads={self.num_heads}, window_size={self.window_size}, mlp_ratio={self.mlp_ratio}'

def __init__(self, dim, input_resolution, num_heads, window_size=7, mlp_ratio=4.0, drop=0.0, drop_path=0.0, local_conv_size=3, activation=nn.GELU):
    super().__init__()
    self.dim = dim
    self.input_resolution = input_resolution
    self.num_heads = num_heads
    assert window_size > 0, 'window_size must be greater than 0'
    self.window_size = window_size
    self.mlp_ratio = mlp_ratio
    self.drop_path = DropPath(drop_path) if drop_path > 0.0 else nn.Identity()
    assert dim % num_heads == 0, 'dim must be divisible by num_heads'
    head_dim = dim // num_heads
    window_resolution = (window_size, window_size)
    self.attn = Attention(dim, head_dim, num_heads, attn_ratio=1, resolution=window_resolution)
    mlp_hidden_dim = int(dim * mlp_ratio)
    mlp_activation = activation
    self.mlp = Mlp(in_features=dim, hidden_features=mlp_hidden_dim, act_layer=mlp_activation, drop=drop)
    pad = local_conv_size // 2
    self.local_conv = Conv2d_BN(dim, dim, ks=local_conv_size, stride=1, pad=pad, groups=dim)

class BasicLayer(nn.Module):
    """ A basic TinyViT layer for one stage.

    Args:
        dim (int): Number of input channels.
        input_resolution (tuple[int]): Input resolution.
        depth (int): Number of blocks.
        num_heads (int): Number of attention heads.
        window_size (int): Local window size.
        mlp_ratio (float): Ratio of mlp hidden dim to embedding dim.
        drop (float, optional): Dropout rate. Default: 0.0
        drop_path (float | tuple[float], optional): Stochastic depth rate. Default: 0.0
        downsample (nn.Module | None, optional): Downsample layer at the end of the layer. Default: None
        use_checkpoint (bool): Whether to use checkpointing to save memory. Default: False.
        local_conv_size: the kernel size of the depthwise convolution between attention and MLP. Default: 3
        activation: the activation function. Default: nn.GELU
        out_dim: the output dimension of the layer. Default: dim
    """

    def __init__(self, dim, input_resolution, depth, num_heads, window_size, mlp_ratio=4.0, drop=0.0, drop_path=0.0, downsample=None, use_checkpoint=False, local_conv_size=3, activation=nn.GELU, out_dim=None):
        super().__init__()
        self.dim = dim
        self.input_resolution = input_resolution
        self.depth = depth
        self.use_checkpoint = use_checkpoint
        self.blocks = nn.ModuleList([TinyViTBlock(dim=dim, input_resolution=input_resolution, num_heads=num_heads, window_size=window_size, mlp_ratio=mlp_ratio, drop=drop, drop_path=drop_path[i] if isinstance(drop_path, list) else drop_path, local_conv_size=local_conv_size, activation=activation) for i in range(depth)])
        if downsample is not None:
            self.downsample = downsample(input_resolution, dim=dim, out_dim=out_dim, activation=activation)
        else:
            self.downsample = None

    def forward(self, x):
        for blk in self.blocks:
            if self.use_checkpoint:
                x = checkpoint.checkpoint(blk, x)
            else:
                x = blk(x)
        if self.downsample is not None:
            x = self.downsample(x)
        return x

    def extra_repr(self) -> str:
        return f'dim={self.dim}, input_resolution={self.input_resolution}, depth={self.depth}'

def __init__(self, dim, input_resolution, depth, num_heads, window_size, mlp_ratio=4.0, drop=0.0, drop_path=0.0, downsample=None, use_checkpoint=False, local_conv_size=3, activation=nn.GELU, out_dim=None):
    super().__init__()
    self.dim = dim
    self.input_resolution = input_resolution
    self.depth = depth
    self.use_checkpoint = use_checkpoint
    self.blocks = nn.ModuleList([TinyViTBlock(dim=dim, input_resolution=input_resolution, num_heads=num_heads, window_size=window_size, mlp_ratio=mlp_ratio, drop=drop, drop_path=drop_path[i] if isinstance(drop_path, list) else drop_path, local_conv_size=local_conv_size, activation=activation) for i in range(depth)])
    if downsample is not None:
        self.downsample = downsample(input_resolution, dim=dim, out_dim=out_dim, activation=activation)
    else:
        self.downsample = None

class LayerNorm2d(nn.Module):

    def __init__(self, num_channels: int, eps: float=1e-06) -> None:
        super().__init__()
        self.weight = nn.Parameter(torch.ones(num_channels))
        self.bias = nn.Parameter(torch.zeros(num_channels))
        self.eps = eps

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        u = x.mean(1, keepdim=True)
        s = (x - u).pow(2).mean(1, keepdim=True)
        x = (x - u) / torch.sqrt(s + self.eps)
        x = self.weight[:, None, None] * x + self.bias[:, None, None]
        return x

def __init__(self, num_channels: int, eps: float=1e-06) -> None:
    super().__init__()
    self.weight = nn.Parameter(torch.ones(num_channels))
    self.bias = nn.Parameter(torch.zeros(num_channels))
    self.eps = eps

class TinyViT(nn.Module):

    def __init__(self, img_size=224, in_chans=3, num_classes=1000, embed_dims=[96, 192, 384, 768], depths=[2, 2, 6, 2], num_heads=[3, 6, 12, 24], window_sizes=[7, 7, 14, 7], mlp_ratio=4.0, drop_rate=0.0, drop_path_rate=0.1, use_checkpoint=False, mbconv_expand_ratio=4.0, local_conv_size=3, layer_lr_decay=1.0):
        super().__init__()
        self.img_size = img_size
        self.num_classes = num_classes
        self.depths = depths
        self.num_layers = len(depths)
        self.mlp_ratio = mlp_ratio
        activation = nn.GELU
        self.patch_embed = PatchEmbed(in_chans=in_chans, embed_dim=embed_dims[0], resolution=img_size, activation=activation)
        patches_resolution = self.patch_embed.patches_resolution
        self.patches_resolution = patches_resolution
        dpr = [x.item() for x in torch.linspace(0, drop_path_rate, sum(depths))]
        self.layers = nn.ModuleList()
        for i_layer in range(self.num_layers):
            kwargs = dict(dim=embed_dims[i_layer], input_resolution=(patches_resolution[0] // 2 ** (i_layer - 1 if i_layer == 3 else i_layer), patches_resolution[1] // 2 ** (i_layer - 1 if i_layer == 3 else i_layer)), depth=depths[i_layer], drop_path=dpr[sum(depths[:i_layer]):sum(depths[:i_layer + 1])], downsample=PatchMerging if i_layer < self.num_layers - 1 else None, use_checkpoint=use_checkpoint, out_dim=embed_dims[min(i_layer + 1, len(embed_dims) - 1)], activation=activation)
            if i_layer == 0:
                layer = ConvLayer(conv_expand_ratio=mbconv_expand_ratio, **kwargs)
            else:
                layer = BasicLayer(num_heads=num_heads[i_layer], window_size=window_sizes[i_layer], mlp_ratio=self.mlp_ratio, drop=drop_rate, local_conv_size=local_conv_size, **kwargs)
            self.layers.append(layer)
        self.norm_head = nn.LayerNorm(embed_dims[-1])
        self.head = nn.Linear(embed_dims[-1], num_classes) if num_classes > 0 else torch.nn.Identity()
        self.apply(self._init_weights)
        self.set_layer_lr_decay(layer_lr_decay)
        self.neck = nn.Sequential(nn.Conv2d(embed_dims[-1], 256, kernel_size=1, bias=False), LayerNorm2d(256), nn.Conv2d(256, 256, kernel_size=3, padding=1, bias=False), LayerNorm2d(256))

    def set_layer_lr_decay(self, layer_lr_decay):
        decay_rate = layer_lr_decay
        depth = sum(self.depths)
        lr_scales = [decay_rate ** (depth - i - 1) for i in range(depth)]

        def _set_lr_scale(m, scale):
            for p in m.parameters():
                p.lr_scale = scale
        self.patch_embed.apply(lambda x: _set_lr_scale(x, lr_scales[0]))
        i = 0
        for layer in self.layers:
            for block in layer.blocks:
                block.apply(lambda x: _set_lr_scale(x, lr_scales[i]))
                i += 1
            if layer.downsample is not None:
                layer.downsample.apply(lambda x: _set_lr_scale(x, lr_scales[i - 1]))
        assert i == depth
        for m in [self.norm_head, self.head]:
            m.apply(lambda x: _set_lr_scale(x, lr_scales[-1]))
        for k, p in self.named_parameters():
            p.param_name = k

        def _check_lr_scale(m):
            for p in m.parameters():
                assert hasattr(p, 'lr_scale'), p.param_name
        self.apply(_check_lr_scale)

    def _init_weights(self, m):
        if isinstance(m, nn.Linear):
            trunc_normal_(m.weight, std=0.02)
            if isinstance(m, nn.Linear) and m.bias is not None:
                nn.init.constant_(m.bias, 0)
        elif isinstance(m, nn.LayerNorm):
            nn.init.constant_(m.bias, 0)
            nn.init.constant_(m.weight, 1.0)

    @torch.jit.ignore
    def no_weight_decay_keywords(self):
        return {'attention_biases'}

    def forward_features(self, x):
        x = self.patch_embed(x)
        x = self.layers[0](x)
        start_i = 1
        for i in range(start_i, len(self.layers)):
            layer = self.layers[i]
            x = layer(x)
        B, _, C = x.size()
        x = x.view(B, 64, 64, C)
        x = x.permute(0, 3, 1, 2)
        x = self.neck(x)
        return x

    def forward(self, x):
        x = self.forward_features(x)
        return x

def __init__(self, img_size=224, in_chans=3, num_classes=1000, embed_dims=[96, 192, 384, 768], depths=[2, 2, 6, 2], num_heads=[3, 6, 12, 24], window_sizes=[7, 7, 14, 7], mlp_ratio=4.0, drop_rate=0.0, drop_path_rate=0.1, use_checkpoint=False, mbconv_expand_ratio=4.0, local_conv_size=3, layer_lr_decay=1.0):
    super().__init__()
    self.img_size = img_size
    self.num_classes = num_classes
    self.depths = depths
    self.num_layers = len(depths)
    self.mlp_ratio = mlp_ratio
    activation = nn.GELU
    self.patch_embed = PatchEmbed(in_chans=in_chans, embed_dim=embed_dims[0], resolution=img_size, activation=activation)
    patches_resolution = self.patch_embed.patches_resolution
    self.patches_resolution = patches_resolution
    dpr = [x.item() for x in torch.linspace(0, drop_path_rate, sum(depths))]
    self.layers = nn.ModuleList()
    for i_layer in range(self.num_layers):
        kwargs = dict(dim=embed_dims[i_layer], input_resolution=(patches_resolution[0] // 2 ** (i_layer - 1 if i_layer == 3 else i_layer), patches_resolution[1] // 2 ** (i_layer - 1 if i_layer == 3 else i_layer)), depth=depths[i_layer], drop_path=dpr[sum(depths[:i_layer]):sum(depths[:i_layer + 1])], downsample=PatchMerging if i_layer < self.num_layers - 1 else None, use_checkpoint=use_checkpoint, out_dim=embed_dims[min(i_layer + 1, len(embed_dims) - 1)], activation=activation)
        if i_layer == 0:
            layer = ConvLayer(conv_expand_ratio=mbconv_expand_ratio, **kwargs)
        else:
            layer = BasicLayer(num_heads=num_heads[i_layer], window_size=window_sizes[i_layer], mlp_ratio=self.mlp_ratio, drop=drop_rate, local_conv_size=local_conv_size, **kwargs)
        self.layers.append(layer)
    self.norm_head = nn.LayerNorm(embed_dims[-1])
    self.head = nn.Linear(embed_dims[-1], num_classes) if num_classes > 0 else torch.nn.Identity()
    self.apply(self._init_weights)
    self.set_layer_lr_decay(layer_lr_decay)
    self.neck = nn.Sequential(nn.Conv2d(embed_dims[-1], 256, kernel_size=1, bias=False), LayerNorm2d(256), nn.Conv2d(256, 256, kernel_size=3, padding=1, bias=False), LayerNorm2d(256))

def _set_lr_scale(m, scale):
    for p in m.parameters():
        p.lr_scale = scale

class SamOnnxModel(nn.Module):
    """
    This model should not be called directly, but is used in ONNX export.
    It combines the prompt encoder, mask decoder, and mask postprocessing of Sam,
    with some functions modified to enable model tracing. Also supports extra
    options controlling what information. See the ONNX export script for details.
    """

    def __init__(self, model: Sam, return_single_mask: bool, use_stability_score: bool=False, return_extra_metrics: bool=False) -> None:
        super().__init__()
        self.mask_decoder = model.mask_decoder
        self.model = model
        self.img_size = model.image_encoder.img_size
        self.return_single_mask = return_single_mask
        self.use_stability_score = use_stability_score
        self.stability_score_offset = 1.0
        self.return_extra_metrics = return_extra_metrics

    @staticmethod
    def resize_longest_image_size(input_image_size: torch.Tensor, longest_side: int) -> torch.Tensor:
        input_image_size = input_image_size.to(torch.float32)
        scale = longest_side / torch.max(input_image_size)
        transformed_size = scale * input_image_size
        transformed_size = torch.floor(transformed_size + 0.5).to(torch.int64)
        return transformed_size

    def _embed_points(self, point_coords: torch.Tensor, point_labels: torch.Tensor) -> torch.Tensor:
        point_coords = point_coords + 0.5
        point_coords = point_coords / self.img_size
        point_embedding = self.model.prompt_encoder.pe_layer._pe_encoding(point_coords)
        point_labels = point_labels.unsqueeze(-1).expand_as(point_embedding)
        point_embedding = point_embedding * (point_labels != -1)
        point_embedding = point_embedding + self.model.prompt_encoder.not_a_point_embed.weight * (point_labels == -1)
        for i in range(self.model.prompt_encoder.num_point_embeddings):
            point_embedding = point_embedding + self.model.prompt_encoder.point_embeddings[i].weight * (point_labels == i)
        return point_embedding

    def _embed_masks(self, input_mask: torch.Tensor, has_mask_input: torch.Tensor) -> torch.Tensor:
        mask_embedding = has_mask_input * self.model.prompt_encoder.mask_downscaling(input_mask)
        mask_embedding = mask_embedding + (1 - has_mask_input) * self.model.prompt_encoder.no_mask_embed.weight.reshape(1, -1, 1, 1)
        return mask_embedding

    def mask_postprocessing(self, masks: torch.Tensor, orig_im_size: torch.Tensor) -> torch.Tensor:
        masks = F.interpolate(masks, size=(self.img_size, self.img_size), mode='bilinear', align_corners=False)
        prepadded_size = self.resize_longest_image_size(orig_im_size, self.img_size).to(torch.int64)
        masks = masks[..., :prepadded_size[0], :prepadded_size[1]]
        orig_im_size = orig_im_size.to(torch.int64)
        h, w = (orig_im_size[0], orig_im_size[1])
        masks = F.interpolate(masks, size=(h, w), mode='bilinear', align_corners=False)
        return masks

    def select_masks(self, masks: torch.Tensor, iou_preds: torch.Tensor, num_points: int) -> Tuple[torch.Tensor, torch.Tensor]:
        score_reweight = torch.tensor([[1000] + [0] * (self.model.mask_decoder.num_mask_tokens - 1)]).to(iou_preds.device)
        score = iou_preds + (num_points - 2.5) * score_reweight
        best_idx = torch.argmax(score, dim=1)
        masks = masks[torch.arange(masks.shape[0]), best_idx, :, :].unsqueeze(1)
        iou_preds = iou_preds[torch.arange(masks.shape[0]), best_idx].unsqueeze(1)
        return (masks, iou_preds)

    @torch.no_grad()
    def forward(self, image_embeddings: torch.Tensor, point_coords: torch.Tensor, point_labels: torch.Tensor, mask_input: torch.Tensor, has_mask_input: torch.Tensor, orig_im_size: torch.Tensor):
        sparse_embedding = self._embed_points(point_coords, point_labels)
        dense_embedding = self._embed_masks(mask_input, has_mask_input)
        masks, scores = self.model.mask_decoder.predict_masks(image_embeddings=image_embeddings, image_pe=self.model.prompt_encoder.get_dense_pe(), sparse_prompt_embeddings=sparse_embedding, dense_prompt_embeddings=dense_embedding)
        if self.use_stability_score:
            scores = calculate_stability_score(masks, self.model.mask_threshold, self.stability_score_offset)
        if self.return_single_mask:
            masks, scores = self.select_masks(masks, scores, point_coords.shape[1])
        upscaled_masks = self.mask_postprocessing(masks, orig_im_size)
        if self.return_extra_metrics:
            stability_scores = calculate_stability_score(upscaled_masks, self.model.mask_threshold, self.stability_score_offset)
            areas = (upscaled_masks > self.model.mask_threshold).sum(-1).sum(-1)
            return (upscaled_masks, scores, stability_scores, areas, masks)
        return (upscaled_masks, scores, masks)

def __init__(self, model: Sam, return_single_mask: bool, use_stability_score: bool=False, return_extra_metrics: bool=False) -> None:
    super().__init__()
    self.mask_decoder = model.mask_decoder
    self.model = model
    self.img_size = model.image_encoder.img_size
    self.return_single_mask = return_single_mask
    self.use_stability_score = use_stability_score
    self.stability_score_offset = 1.0
    self.return_extra_metrics = return_extra_metrics

def generate_crop_boxes(im_size: Tuple[int, ...], n_layers: int, overlap_ratio: float) -> Tuple[List[List[int]], List[int]]:
    """
    Generates a list of crop boxes of different sizes. Each layer
    has (2**i)**2 boxes for the ith layer.
    """
    crop_boxes, layer_idxs = ([], [])
    im_h, im_w = im_size
    short_side = min(im_h, im_w)
    crop_boxes.append([0, 0, im_w, im_h])
    layer_idxs.append(0)

    def crop_len(orig_len, n_crops, overlap):
        return int(math.ceil((overlap * (n_crops - 1) + orig_len) / n_crops))
    for i_layer in range(n_layers):
        n_crops_per_side = 2 ** (i_layer + 1)
        overlap = int(overlap_ratio * short_side * (2 / n_crops_per_side))
        crop_w = crop_len(im_w, n_crops_per_side, overlap)
        crop_h = crop_len(im_h, n_crops_per_side, overlap)
        crop_box_x0 = [int((crop_w - overlap) * i) for i in range(n_crops_per_side)]
        crop_box_y0 = [int((crop_h - overlap) * i) for i in range(n_crops_per_side)]
        for x0, y0 in product(crop_box_x0, crop_box_y0):
            box = [x0, y0, min(x0 + crop_w, im_w), min(y0 + crop_h, im_h)]
            crop_boxes.append(box)
            layer_idxs.append(i_layer + 1)
    return (crop_boxes, layer_idxs)

class JITWrapper(nn.Module):

    def __init__(self, model):
        super().__init__()
        self.model = model

    def forward(self, image, mask):
        batch = {'image': image, 'mask': mask}
        out = self.model(batch)
        return out['inpainted']

def __init__(self, model):
    super().__init__()
    self.model = model

def set_requires_grad(module, value):
    for param in module.parameters():
        param.requires_grad = value

class PerceptualLoss(nn.Module):
    """
    Perceptual loss, VGG-based
    https://arxiv.org/abs/1603.08155
    https://github.com/dxyang/StyleTransfer/blob/master/utils.py
    """

    def __init__(self, weights=[1.0, 1.0, 1.0, 1.0, 1.0]):
        super(PerceptualLoss, self).__init__()
        self.add_module('vgg', VGG19())
        self.criterion = torch.nn.L1Loss()
        self.weights = weights

    def __call__(self, x, y):
        x_vgg, y_vgg = (self.vgg(x), self.vgg(y))
        content_loss = 0.0
        content_loss += self.weights[0] * self.criterion(x_vgg['relu1_1'], y_vgg['relu1_1'])
        content_loss += self.weights[1] * self.criterion(x_vgg['relu2_1'], y_vgg['relu2_1'])
        content_loss += self.weights[2] * self.criterion(x_vgg['relu3_1'], y_vgg['relu3_1'])
        content_loss += self.weights[3] * self.criterion(x_vgg['relu4_1'], y_vgg['relu4_1'])
        content_loss += self.weights[4] * self.criterion(x_vgg['relu5_1'], y_vgg['relu5_1'])
        return content_loss

def __init__(self, weights=[1.0, 1.0, 1.0, 1.0, 1.0]):
    super(PerceptualLoss, self).__init__()
    self.add_module('vgg', VGG19())
    self.criterion = torch.nn.L1Loss()
    self.weights = weights

class VGG19(torch.nn.Module):

    def __init__(self):
        super(VGG19, self).__init__()
        features = models.vgg19(pretrained=True).features
        self.relu1_1 = torch.nn.Sequential()
        self.relu1_2 = torch.nn.Sequential()
        self.relu2_1 = torch.nn.Sequential()
        self.relu2_2 = torch.nn.Sequential()
        self.relu3_1 = torch.nn.Sequential()
        self.relu3_2 = torch.nn.Sequential()
        self.relu3_3 = torch.nn.Sequential()
        self.relu3_4 = torch.nn.Sequential()
        self.relu4_1 = torch.nn.Sequential()
        self.relu4_2 = torch.nn.Sequential()
        self.relu4_3 = torch.nn.Sequential()
        self.relu4_4 = torch.nn.Sequential()
        self.relu5_1 = torch.nn.Sequential()
        self.relu5_2 = torch.nn.Sequential()
        self.relu5_3 = torch.nn.Sequential()
        self.relu5_4 = torch.nn.Sequential()
        for x in range(2):
            self.relu1_1.add_module(str(x), features[x])
        for x in range(2, 4):
            self.relu1_2.add_module(str(x), features[x])
        for x in range(4, 7):
            self.relu2_1.add_module(str(x), features[x])
        for x in range(7, 9):
            self.relu2_2.add_module(str(x), features[x])
        for x in range(9, 12):
            self.relu3_1.add_module(str(x), features[x])
        for x in range(12, 14):
            self.relu3_2.add_module(str(x), features[x])
        for x in range(14, 16):
            self.relu3_2.add_module(str(x), features[x])
        for x in range(16, 18):
            self.relu3_4.add_module(str(x), features[x])
        for x in range(18, 21):
            self.relu4_1.add_module(str(x), features[x])
        for x in range(21, 23):
            self.relu4_2.add_module(str(x), features[x])
        for x in range(23, 25):
            self.relu4_3.add_module(str(x), features[x])
        for x in range(25, 27):
            self.relu4_4.add_module(str(x), features[x])
        for x in range(27, 30):
            self.relu5_1.add_module(str(x), features[x])
        for x in range(30, 32):
            self.relu5_2.add_module(str(x), features[x])
        for x in range(32, 34):
            self.relu5_3.add_module(str(x), features[x])
        for x in range(34, 36):
            self.relu5_4.add_module(str(x), features[x])
        for param in self.parameters():
            param.requires_grad = False

    def forward(self, x):
        relu1_1 = self.relu1_1(x)
        relu1_2 = self.relu1_2(relu1_1)
        relu2_1 = self.relu2_1(relu1_2)
        relu2_2 = self.relu2_2(relu2_1)
        relu3_1 = self.relu3_1(relu2_2)
        relu3_2 = self.relu3_2(relu3_1)
        relu3_3 = self.relu3_3(relu3_2)
        relu3_4 = self.relu3_4(relu3_3)
        relu4_1 = self.relu4_1(relu3_4)
        relu4_2 = self.relu4_2(relu4_1)
        relu4_3 = self.relu4_3(relu4_2)
        relu4_4 = self.relu4_4(relu4_3)
        relu5_1 = self.relu5_1(relu4_4)
        relu5_2 = self.relu5_2(relu5_1)
        relu5_3 = self.relu5_3(relu5_2)
        relu5_4 = self.relu5_4(relu5_3)
        out = {'relu1_1': relu1_1, 'relu1_2': relu1_2, 'relu2_1': relu2_1, 'relu2_2': relu2_2, 'relu3_1': relu3_1, 'relu3_2': relu3_2, 'relu3_3': relu3_3, 'relu3_4': relu3_4, 'relu4_1': relu4_1, 'relu4_2': relu4_2, 'relu4_3': relu4_3, 'relu4_4': relu4_4, 'relu5_1': relu5_1, 'relu5_2': relu5_2, 'relu5_3': relu5_3, 'relu5_4': relu5_4}
        return out

def __init__(self):
    super(VGG19, self).__init__()
    features = models.vgg19(pretrained=True).features
    self.relu1_1 = torch.nn.Sequential()
    self.relu1_2 = torch.nn.Sequential()
    self.relu2_1 = torch.nn.Sequential()
    self.relu2_2 = torch.nn.Sequential()
    self.relu3_1 = torch.nn.Sequential()
    self.relu3_2 = torch.nn.Sequential()
    self.relu3_3 = torch.nn.Sequential()
    self.relu3_4 = torch.nn.Sequential()
    self.relu4_1 = torch.nn.Sequential()
    self.relu4_2 = torch.nn.Sequential()
    self.relu4_3 = torch.nn.Sequential()
    self.relu4_4 = torch.nn.Sequential()
    self.relu5_1 = torch.nn.Sequential()
    self.relu5_2 = torch.nn.Sequential()
    self.relu5_3 = torch.nn.Sequential()
    self.relu5_4 = torch.nn.Sequential()
    for x in range(2):
        self.relu1_1.add_module(str(x), features[x])
    for x in range(2, 4):
        self.relu1_2.add_module(str(x), features[x])
    for x in range(4, 7):
        self.relu2_1.add_module(str(x), features[x])
    for x in range(7, 9):
        self.relu2_2.add_module(str(x), features[x])
    for x in range(9, 12):
        self.relu3_1.add_module(str(x), features[x])
    for x in range(12, 14):
        self.relu3_2.add_module(str(x), features[x])
    for x in range(14, 16):
        self.relu3_2.add_module(str(x), features[x])
    for x in range(16, 18):
        self.relu3_4.add_module(str(x), features[x])
    for x in range(18, 21):
        self.relu4_1.add_module(str(x), features[x])
    for x in range(21, 23):
        self.relu4_2.add_module(str(x), features[x])
    for x in range(23, 25):
        self.relu4_3.add_module(str(x), features[x])
    for x in range(25, 27):
        self.relu4_4.add_module(str(x), features[x])
    for x in range(27, 30):
        self.relu5_1.add_module(str(x), features[x])
    for x in range(30, 32):
        self.relu5_2.add_module(str(x), features[x])
    for x in range(32, 34):
        self.relu5_3.add_module(str(x), features[x])
    for x in range(34, 36):
        self.relu5_4.add_module(str(x), features[x])
    for param in self.parameters():
        param.requires_grad = False

class CrossEntropy2d(nn.Module):

    def __init__(self, reduction='mean', ignore_label=255, weights=None, *args, **kwargs):
        """
        weight (Tensor, optional): a manual rescaling weight given to each class.
            If given, has to be a Tensor of size "nclasses"
        """
        super(CrossEntropy2d, self).__init__()
        self.reduction = reduction
        self.ignore_label = ignore_label
        self.weights = weights
        if self.weights is not None:
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.weights = torch.FloatTensor(constant_weights[weights]).to(device)

    def forward(self, predict, target):
        """
            Args:
                predict:(n, c, h, w)
                target:(n, 1, h, w)
        """
        target = target.long()
        assert not target.requires_grad
        assert predict.dim() == 4, '{0}'.format(predict.size())
        assert target.dim() == 4, '{0}'.format(target.size())
        assert predict.size(0) == target.size(0), '{0} vs {1} '.format(predict.size(0), target.size(0))
        assert target.size(1) == 1, '{0}'.format(target.size(1))
        assert predict.size(2) == target.size(2), '{0} vs {1} '.format(predict.size(2), target.size(2))
        assert predict.size(3) == target.size(3), '{0} vs {1} '.format(predict.size(3), target.size(3))
        target = target.squeeze(1)
        n, c, h, w = predict.size()
        target_mask = (target >= 0) * (target != self.ignore_label)
        target = target[target_mask]
        predict = predict.transpose(1, 2).transpose(2, 3).contiguous()
        predict = predict[target_mask.view(n, h, w, 1).repeat(1, 1, 1, c)].view(-1, c)
        loss = F.cross_entropy(predict, target, weight=self.weights, reduction=self.reduction)
        return loss

def __init__(self, reduction='mean', ignore_label=255, weights=None, *args, **kwargs):
    """
        weight (Tensor, optional): a manual rescaling weight given to each class.
            If given, has to be a Tensor of size "nclasses"
        """
    super(CrossEntropy2d, self).__init__()
    self.reduction = reduction
    self.ignore_label = ignore_label
    self.weights = weights
    if self.weights is not None:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.weights = torch.FloatTensor(constant_weights[weights]).to(device)

class BlurMask(nn.Module):

    def __init__(self, kernel_size=5, width_factor=1):
        super().__init__()
        self.filter = nn.Conv2d(1, 1, kernel_size, padding=kernel_size // 2, padding_mode='replicate', bias=False)
        self.filter.weight.data.copy_(get_gauss_kernel(kernel_size, width_factor=width_factor))

    def forward(self, real_img, pred_img, mask):
        with torch.no_grad():
            result = self.filter(mask) * mask
            return result

def __init__(self, kernel_size=5, width_factor=1):
    super().__init__()
    self.filter = nn.Conv2d(1, 1, kernel_size, padding=kernel_size // 2, padding_mode='replicate', bias=False)
    self.filter.weight.data.copy_(get_gauss_kernel(kernel_size, width_factor=width_factor))

class EmulatedEDTMask(nn.Module):

    def __init__(self, dilate_kernel_size=5, blur_kernel_size=5, width_factor=1):
        super().__init__()
        self.dilate_filter = nn.Conv2d(1, 1, dilate_kernel_size, padding=dilate_kernel_size // 2, padding_mode='replicate', bias=False)
        self.dilate_filter.weight.data.copy_(torch.ones(1, 1, dilate_kernel_size, dilate_kernel_size, dtype=torch.float))
        self.blur_filter = nn.Conv2d(1, 1, blur_kernel_size, padding=blur_kernel_size // 2, padding_mode='replicate', bias=False)
        self.blur_filter.weight.data.copy_(get_gauss_kernel(blur_kernel_size, width_factor=width_factor))

    def forward(self, real_img, pred_img, mask):
        with torch.no_grad():
            known_mask = 1 - mask
            dilated_known_mask = (self.dilate_filter(known_mask) > 1).float()
            result = self.blur_filter(1 - dilated_known_mask) * mask
            return result

def __init__(self, dilate_kernel_size=5, blur_kernel_size=5, width_factor=1):
    super().__init__()
    self.dilate_filter = nn.Conv2d(1, 1, dilate_kernel_size, padding=dilate_kernel_size // 2, padding_mode='replicate', bias=False)
    self.dilate_filter.weight.data.copy_(torch.ones(1, 1, dilate_kernel_size, dilate_kernel_size, dtype=torch.float))
    self.blur_filter = nn.Conv2d(1, 1, blur_kernel_size, padding=blur_kernel_size // 2, padding_mode='replicate', bias=False)
    self.blur_filter.weight.data.copy_(get_gauss_kernel(blur_kernel_size, width_factor=width_factor))

class PropagatePerceptualSim(nn.Module):

    def __init__(self, level=2, max_iters=10, temperature=500, erode_mask_size=3):
        super().__init__()
        vgg = torchvision.models.vgg19(pretrained=True).features
        vgg_avg_pooling = []
        for weights in vgg.parameters():
            weights.requires_grad = False
        cur_level_i = 0
        for module in vgg.modules():
            if module.__class__.__name__ == 'Sequential':
                continue
            elif module.__class__.__name__ == 'MaxPool2d':
                vgg_avg_pooling.append(nn.AvgPool2d(kernel_size=2, stride=2, padding=0))
            else:
                vgg_avg_pooling.append(module)
                if module.__class__.__name__ == 'ReLU':
                    cur_level_i += 1
                if cur_level_i == level:
                    break
        self.features = nn.Sequential(*vgg_avg_pooling)
        self.max_iters = max_iters
        self.temperature = temperature
        self.do_erode = erode_mask_size > 0
        if self.do_erode:
            self.erode_mask = nn.Conv2d(1, 1, erode_mask_size, padding=erode_mask_size // 2, bias=False)
            self.erode_mask.weight.data.fill_(1)

    def forward(self, real_img, pred_img, mask):
        with torch.no_grad():
            real_img = (real_img - IMAGENET_MEAN.to(real_img)) / IMAGENET_STD.to(real_img)
            real_feats = self.features(real_img)
            vertical_sim = torch.exp(-(real_feats[:, :, 1:] - real_feats[:, :, :-1]).pow(2).sum(1, keepdim=True) / self.temperature)
            horizontal_sim = torch.exp(-(real_feats[:, :, :, 1:] - real_feats[:, :, :, :-1]).pow(2).sum(1, keepdim=True) / self.temperature)
            mask_scaled = F.interpolate(mask, size=real_feats.shape[-2:], mode='bilinear', align_corners=False)
            if self.do_erode:
                mask_scaled = (self.erode_mask(mask_scaled) > 1).float()
            cur_knowness = 1 - mask_scaled
            for iter_i in range(self.max_iters):
                new_top_knowness = F.pad(cur_knowness[:, :, :-1] * vertical_sim, (0, 0, 1, 0), mode='replicate')
                new_bottom_knowness = F.pad(cur_knowness[:, :, 1:] * vertical_sim, (0, 0, 0, 1), mode='replicate')
                new_left_knowness = F.pad(cur_knowness[:, :, :, :-1] * horizontal_sim, (1, 0, 0, 0), mode='replicate')
                new_right_knowness = F.pad(cur_knowness[:, :, :, 1:] * horizontal_sim, (0, 1, 0, 0), mode='replicate')
                new_knowness = torch.stack([new_top_knowness, new_bottom_knowness, new_left_knowness, new_right_knowness], dim=0).max(0).values
                cur_knowness = torch.max(cur_knowness, new_knowness)
            cur_knowness = F.interpolate(cur_knowness, size=mask.shape[-2:], mode='bilinear')
            result = torch.min(mask, 1 - cur_knowness)
            return result

def __init__(self, level=2, max_iters=10, temperature=500, erode_mask_size=3):
    super().__init__()
    vgg = torchvision.models.vgg19(pretrained=True).features
    vgg_avg_pooling = []
    for weights in vgg.parameters():
        weights.requires_grad = False
    cur_level_i = 0
    for module in vgg.modules():
        if module.__class__.__name__ == 'Sequential':
            continue
        elif module.__class__.__name__ == 'MaxPool2d':
            vgg_avg_pooling.append(nn.AvgPool2d(kernel_size=2, stride=2, padding=0))
        else:
            vgg_avg_pooling.append(module)
            if module.__class__.__name__ == 'ReLU':
                cur_level_i += 1
            if cur_level_i == level:
                break
    self.features = nn.Sequential(*vgg_avg_pooling)
    self.max_iters = max_iters
    self.temperature = temperature
    self.do_erode = erode_mask_size > 0
    if self.do_erode:
        self.erode_mask = nn.Conv2d(1, 1, erode_mask_size, padding=erode_mask_size // 2, bias=False)
        self.erode_mask.weight.data.fill_(1)

class PerceptualLoss(nn.Module):

    def __init__(self, normalize_inputs=True):
        super(PerceptualLoss, self).__init__()
        self.normalize_inputs = normalize_inputs
        self.mean_ = IMAGENET_MEAN
        self.std_ = IMAGENET_STD
        vgg = torchvision.models.vgg19(pretrained=True).features
        vgg_avg_pooling = []
        for weights in vgg.parameters():
            weights.requires_grad = False
        for module in vgg.modules():
            if module.__class__.__name__ == 'Sequential':
                continue
            elif module.__class__.__name__ == 'MaxPool2d':
                vgg_avg_pooling.append(nn.AvgPool2d(kernel_size=2, stride=2, padding=0))
            else:
                vgg_avg_pooling.append(module)
        self.vgg = nn.Sequential(*vgg_avg_pooling)

    def do_normalize_inputs(self, x):
        return (x - self.mean_.to(x.device)) / self.std_.to(x.device)

    def partial_losses(self, input, target, mask=None):
        check_and_warn_input_range(target, 0, 1, 'PerceptualLoss target in partial_losses')
        losses = []
        if self.normalize_inputs:
            features_input = self.do_normalize_inputs(input)
            features_target = self.do_normalize_inputs(target)
        else:
            features_input = input
            features_target = target
        for layer in self.vgg[:30]:
            features_input = layer(features_input)
            features_target = layer(features_target)
            if layer.__class__.__name__ == 'ReLU':
                loss = F.mse_loss(features_input, features_target, reduction='none')
                if mask is not None:
                    cur_mask = F.interpolate(mask, size=features_input.shape[-2:], mode='bilinear', align_corners=False)
                    loss = loss * (1 - cur_mask)
                loss = loss.mean(dim=tuple(range(1, len(loss.shape))))
                losses.append(loss)
        return losses

    def forward(self, input, target, mask=None):
        losses = self.partial_losses(input, target, mask=mask)
        return torch.stack(losses).sum(dim=0)

    def get_global_features(self, input):
        check_and_warn_input_range(input, 0, 1, 'PerceptualLoss input in get_global_features')
        if self.normalize_inputs:
            features_input = self.do_normalize_inputs(input)
        else:
            features_input = input
        features_input = self.vgg(features_input)
        return features_input

def __init__(self, normalize_inputs=True):
    super(PerceptualLoss, self).__init__()
    self.normalize_inputs = normalize_inputs
    self.mean_ = IMAGENET_MEAN
    self.std_ = IMAGENET_STD
    vgg = torchvision.models.vgg19(pretrained=True).features
    vgg_avg_pooling = []
    for weights in vgg.parameters():
        weights.requires_grad = False
    for module in vgg.modules():
        if module.__class__.__name__ == 'Sequential':
            continue
        elif module.__class__.__name__ == 'MaxPool2d':
            vgg_avg_pooling.append(nn.AvgPool2d(kernel_size=2, stride=2, padding=0))
        else:
            vgg_avg_pooling.append(module)
    self.vgg = nn.Sequential(*vgg_avg_pooling)

class ResNetPL(nn.Module):

    def __init__(self, weight=1, weights_path=None, arch_encoder='resnet50dilated', segmentation=True):
        super().__init__()
        self.impl = ModelBuilder.get_encoder(weights_path=weights_path, arch_encoder=arch_encoder, arch_decoder='ppm_deepsup', fc_dim=2048, segmentation=segmentation)
        self.impl.eval()
        for w in self.impl.parameters():
            w.requires_grad_(False)
        self.weight = weight

    def forward(self, pred, target):
        pred = (pred - IMAGENET_MEAN.to(pred)) / IMAGENET_STD.to(pred)
        target = (target - IMAGENET_MEAN.to(target)) / IMAGENET_STD.to(target)
        pred_feats = self.impl(pred, return_feature_maps=True)
        target_feats = self.impl(target, return_feature_maps=True)
        result = torch.stack([F.mse_loss(cur_pred, cur_target) for cur_pred, cur_target in zip(pred_feats, target_feats)]).sum() * self.weight
        return result

def __init__(self, weight=1, weights_path=None, arch_encoder='resnet50dilated', segmentation=True):
    super().__init__()
    self.impl = ModelBuilder.get_encoder(weights_path=weights_path, arch_encoder=arch_encoder, arch_decoder='ppm_deepsup', fc_dim=2048, segmentation=segmentation)
    self.impl.eval()
    for w in self.impl.parameters():
        w.requires_grad_(False)
    self.weight = weight

class BaseInpaintingTrainingModule(ptl.LightningModule):

    def __init__(self, config, use_ddp, *args, predict_only=False, visualize_each_iters=100, average_generator=False, generator_avg_beta=0.999, average_generator_start_step=30000, average_generator_period=10, store_discr_outputs_for_vis=False, **kwargs):
        super().__init__(*args, **kwargs)
        LOGGER.info('BaseInpaintingTrainingModule init called')
        self.config = config
        self.generator = make_generator(config, **self.config.generator)
        self.use_ddp = use_ddp
        if not get_has_ddp_rank():
            LOGGER.info(f'Generator\n{self.generator}')
        if not predict_only:
            self.save_hyperparameters(self.config)
            self.discriminator = make_discriminator(**self.config.discriminator)
            self.adversarial_loss = make_discrim_loss(**self.config.losses.adversarial)
            self.visualizer = make_visualizer(**self.config.visualizer)
            self.val_evaluator = make_evaluator(**self.config.evaluator)
            self.test_evaluator = make_evaluator(**self.config.evaluator)
            if not get_has_ddp_rank():
                LOGGER.info(f'Discriminator\n{self.discriminator}')
            extra_val = self.config.data.get('extra_val', ())
            if extra_val:
                self.extra_val_titles = list(extra_val)
                self.extra_evaluators = nn.ModuleDict({k: make_evaluator(**self.config.evaluator) for k in extra_val})
            else:
                self.extra_evaluators = {}
            self.average_generator = average_generator
            self.generator_avg_beta = generator_avg_beta
            self.average_generator_start_step = average_generator_start_step
            self.average_generator_period = average_generator_period
            self.generator_average = None
            self.last_generator_averaging_step = -1
            self.store_discr_outputs_for_vis = store_discr_outputs_for_vis
            if self.config.losses.get('l1', {'weight_known': 0})['weight_known'] > 0:
                self.loss_l1 = nn.L1Loss(reduction='none')
            if self.config.losses.get('mse', {'weight': 0})['weight'] > 0:
                self.loss_mse = nn.MSELoss(reduction='none')
            if self.config.losses.perceptual.weight > 0:
                self.loss_pl = PerceptualLoss()
            if self.config.losses.get('resnet_pl', {'weight': 0})['weight'] > 0:
                self.loss_resnet_pl = ResNetPL(**self.config.losses.resnet_pl)
            else:
                self.loss_resnet_pl = None
        self.visualize_each_iters = visualize_each_iters
        LOGGER.info('BaseInpaintingTrainingModule init done')

    def configure_optimizers(self):
        discriminator_params = list(self.discriminator.parameters())
        return [dict(optimizer=make_optimizer(self.generator.parameters(), **self.config.optimizers.generator)), dict(optimizer=make_optimizer(discriminator_params, **self.config.optimizers.discriminator))]

    def train_dataloader(self):
        kwargs = dict(self.config.data.train)
        if self.use_ddp:
            kwargs['ddp_kwargs'] = dict(num_replicas=self.trainer.num_nodes * self.trainer.num_processes, rank=self.trainer.global_rank, shuffle=True)
        dataloader = make_default_train_dataloader(**self.config.data.train)
        return dataloader

    def val_dataloader(self):
        res = [make_default_val_dataloader(**self.config.data.val)]
        if self.config.data.visual_test is not None:
            res = res + [make_default_val_dataloader(**self.config.data.visual_test)]
        else:
            res = res + res
        extra_val = self.config.data.get('extra_val', ())
        if extra_val:
            res += [make_default_val_dataloader(**extra_val[k]) for k in self.extra_val_titles]
        return res

    def training_step(self, batch, batch_idx, optimizer_idx=None):
        self._is_training_step = True
        return self._do_step(batch, batch_idx, mode='train', optimizer_idx=optimizer_idx)

    def validation_step(self, batch, batch_idx, dataloader_idx):
        extra_val_key = None
        if dataloader_idx == 0:
            mode = 'val'
        elif dataloader_idx == 1:
            mode = 'test'
        else:
            mode = 'extra_val'
            extra_val_key = self.extra_val_titles[dataloader_idx - 2]
        self._is_training_step = False
        return self._do_step(batch, batch_idx, mode=mode, extra_val_key=extra_val_key)

    def training_step_end(self, batch_parts_outputs):
        if self.training and self.average_generator and (self.global_step >= self.average_generator_start_step) and (self.global_step >= self.last_generator_averaging_step + self.average_generator_period):
            if self.generator_average is None:
                self.generator_average = copy.deepcopy(self.generator)
            else:
                update_running_average(self.generator_average, self.generator, decay=self.generator_avg_beta)
            self.last_generator_averaging_step = self.global_step
        full_loss = batch_parts_outputs['loss'].mean() if torch.is_tensor(batch_parts_outputs['loss']) else torch.tensor(batch_parts_outputs['loss']).float().requires_grad_(True)
        log_info = {k: v.mean() for k, v in batch_parts_outputs['log_info'].items()}
        self.log_dict(log_info, on_step=True, on_epoch=False)
        return full_loss

    def validation_epoch_end(self, outputs):
        outputs = [step_out for out_group in outputs for step_out in out_group]
        averaged_logs = average_dicts((step_out['log_info'] for step_out in outputs))
        self.log_dict({k: v.mean() for k, v in averaged_logs.items()})
        pd.set_option('display.max_columns', 500)
        pd.set_option('display.width', 1000)
        val_evaluator_states = [s['val_evaluator_state'] for s in outputs if 'val_evaluator_state' in s]
        val_evaluator_res = self.val_evaluator.evaluation_end(states=val_evaluator_states)
        val_evaluator_res_df = pd.DataFrame(val_evaluator_res).stack(1).unstack(0)
        val_evaluator_res_df.dropna(axis=1, how='all', inplace=True)
        LOGGER.info(f'Validation metrics after epoch #{self.current_epoch}, total {self.global_step} iterations:\n{val_evaluator_res_df}')
        for k, v in flatten_dict(val_evaluator_res).items():
            self.log(f'val_{k}', v)
        test_evaluator_states = [s['test_evaluator_state'] for s in outputs if 'test_evaluator_state' in s]
        test_evaluator_res = self.test_evaluator.evaluation_end(states=test_evaluator_states)
        test_evaluator_res_df = pd.DataFrame(test_evaluator_res).stack(1).unstack(0)
        test_evaluator_res_df.dropna(axis=1, how='all', inplace=True)
        LOGGER.info(f'Test metrics after epoch #{self.current_epoch}, total {self.global_step} iterations:\n{test_evaluator_res_df}')
        for k, v in flatten_dict(test_evaluator_res).items():
            self.log(f'test_{k}', v)
        if self.extra_evaluators:
            for cur_eval_title, cur_evaluator in self.extra_evaluators.items():
                cur_state_key = f'extra_val_{cur_eval_title}_evaluator_state'
                cur_states = [s[cur_state_key] for s in outputs if cur_state_key in s]
                cur_evaluator_res = cur_evaluator.evaluation_end(states=cur_states)
                cur_evaluator_res_df = pd.DataFrame(cur_evaluator_res).stack(1).unstack(0)
                cur_evaluator_res_df.dropna(axis=1, how='all', inplace=True)
                LOGGER.info(f'Extra val {cur_eval_title} metrics after epoch #{self.current_epoch}, total {self.global_step} iterations:\n{cur_evaluator_res_df}')
                for k, v in flatten_dict(cur_evaluator_res).items():
                    self.log(f'extra_val_{cur_eval_title}_{k}', v)

    def _do_step(self, batch, batch_idx, mode='train', optimizer_idx=None, extra_val_key=None):
        if optimizer_idx == 0:
            set_requires_grad(self.generator, True)
            set_requires_grad(self.discriminator, False)
        elif optimizer_idx == 1:
            set_requires_grad(self.generator, False)
            set_requires_grad(self.discriminator, True)
        batch = self(batch)
        total_loss = 0
        metrics = {}
        if optimizer_idx is None or optimizer_idx == 0:
            total_loss, metrics = self.generator_loss(batch)
        elif optimizer_idx is None or optimizer_idx == 1:
            if self.config.losses.adversarial.weight > 0:
                total_loss, metrics = self.discriminator_loss(batch)
        if self.get_ddp_rank() in (None, 0) and (batch_idx % self.visualize_each_iters == 0 or mode == 'test'):
            if self.config.losses.adversarial.weight > 0:
                if self.store_discr_outputs_for_vis:
                    with torch.no_grad():
                        self.store_discr_outputs(batch)
            vis_suffix = f'_{mode}'
            if mode == 'extra_val':
                vis_suffix += f'_{extra_val_key}'
            self.visualizer(self.current_epoch, batch_idx, batch, suffix=vis_suffix)
        metrics_prefix = f'{mode}_'
        if mode == 'extra_val':
            metrics_prefix += f'{extra_val_key}_'
        result = dict(loss=total_loss, log_info=add_prefix_to_keys(metrics, metrics_prefix))
        if mode == 'val':
            result['val_evaluator_state'] = self.val_evaluator.process_batch(batch)
        elif mode == 'test':
            result['test_evaluator_state'] = self.test_evaluator.process_batch(batch)
        elif mode == 'extra_val':
            result[f'extra_val_{extra_val_key}_evaluator_state'] = self.extra_evaluators[extra_val_key].process_batch(batch)
        return result

    def get_current_generator(self, no_average=False):
        if not no_average and (not self.training) and self.average_generator and (self.generator_average is not None):
            return self.generator_average
        return self.generator

    def forward(self, batch: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """Pass data through generator and obtain at leas 'predicted_image' and 'inpainted' keys"""
        raise NotImplementedError()

    def generator_loss(self, batch) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        raise NotImplementedError()

    def discriminator_loss(self, batch) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        raise NotImplementedError()

    def store_discr_outputs(self, batch):
        out_size = batch['image'].shape[2:]
        discr_real_out, _ = self.discriminator(batch['image'])
        discr_fake_out, _ = self.discriminator(batch['predicted_image'])
        batch['discr_output_real'] = F.interpolate(discr_real_out, size=out_size, mode='nearest')
        batch['discr_output_fake'] = F.interpolate(discr_fake_out, size=out_size, mode='nearest')
        batch['discr_output_diff'] = batch['discr_output_real'] - batch['discr_output_fake']

    def get_ddp_rank(self):
        return self.trainer.global_rank if self.trainer.num_nodes * self.trainer.num_processes > 1 else None

def __init__(self, config, use_ddp, *args, predict_only=False, visualize_each_iters=100, average_generator=False, generator_avg_beta=0.999, average_generator_start_step=30000, average_generator_period=10, store_discr_outputs_for_vis=False, **kwargs):
    super().__init__(*args, **kwargs)
    LOGGER.info('BaseInpaintingTrainingModule init called')
    self.config = config
    self.generator = make_generator(config, **self.config.generator)
    self.use_ddp = use_ddp
    if not get_has_ddp_rank():
        LOGGER.info(f'Generator\n{self.generator}')
    if not predict_only:
        self.save_hyperparameters(self.config)
        self.discriminator = make_discriminator(**self.config.discriminator)
        self.adversarial_loss = make_discrim_loss(**self.config.losses.adversarial)
        self.visualizer = make_visualizer(**self.config.visualizer)
        self.val_evaluator = make_evaluator(**self.config.evaluator)
        self.test_evaluator = make_evaluator(**self.config.evaluator)
        if not get_has_ddp_rank():
            LOGGER.info(f'Discriminator\n{self.discriminator}')
        extra_val = self.config.data.get('extra_val', ())
        if extra_val:
            self.extra_val_titles = list(extra_val)
            self.extra_evaluators = nn.ModuleDict({k: make_evaluator(**self.config.evaluator) for k in extra_val})
        else:
            self.extra_evaluators = {}
        self.average_generator = average_generator
        self.generator_avg_beta = generator_avg_beta
        self.average_generator_start_step = average_generator_start_step
        self.average_generator_period = average_generator_period
        self.generator_average = None
        self.last_generator_averaging_step = -1
        self.store_discr_outputs_for_vis = store_discr_outputs_for_vis
        if self.config.losses.get('l1', {'weight_known': 0})['weight_known'] > 0:
            self.loss_l1 = nn.L1Loss(reduction='none')
        if self.config.losses.get('mse', {'weight': 0})['weight'] > 0:
            self.loss_mse = nn.MSELoss(reduction='none')
        if self.config.losses.perceptual.weight > 0:
            self.loss_pl = PerceptualLoss()
        if self.config.losses.get('resnet_pl', {'weight': 0})['weight'] > 0:
            self.loss_resnet_pl = ResNetPL(**self.config.losses.resnet_pl)
        else:
            self.loss_resnet_pl = None
    self.visualize_each_iters = visualize_each_iters
    LOGGER.info('BaseInpaintingTrainingModule init done')

class DefaultInpaintingTrainingModule(BaseInpaintingTrainingModule):

    def __init__(self, *args, concat_mask=True, rescale_scheduler_kwargs=None, image_to_discriminator='predicted_image', add_noise_kwargs=None, noise_fill_hole=False, const_area_crop_kwargs=None, distance_weighter_kwargs=None, distance_weighted_mask_for_discr=False, fake_fakes_proba=0, fake_fakes_generator_kwargs=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.concat_mask = concat_mask
        self.rescale_size_getter = get_ramp(**rescale_scheduler_kwargs) if rescale_scheduler_kwargs is not None else None
        self.image_to_discriminator = image_to_discriminator
        self.add_noise_kwargs = add_noise_kwargs
        self.noise_fill_hole = noise_fill_hole
        self.const_area_crop_kwargs = const_area_crop_kwargs
        self.refine_mask_for_losses = make_mask_distance_weighter(**distance_weighter_kwargs) if distance_weighter_kwargs is not None else None
        self.distance_weighted_mask_for_discr = distance_weighted_mask_for_discr
        self.fake_fakes_proba = fake_fakes_proba
        if self.fake_fakes_proba > 0.001:
            self.fake_fakes_gen = FakeFakesGenerator(**fake_fakes_generator_kwargs or {})

    def forward(self, batch):
        if self.training and self.rescale_size_getter is not None:
            cur_size = self.rescale_size_getter(self.global_step)
            batch['image'] = F.interpolate(batch['image'], size=cur_size, mode='bilinear', align_corners=False)
            batch['mask'] = F.interpolate(batch['mask'], size=cur_size, mode='nearest')
        if self.training and self.const_area_crop_kwargs is not None:
            batch = make_constant_area_crop_batch(batch, **self.const_area_crop_kwargs)
        img = batch['image']
        mask = batch['mask']
        masked_img = img * (1 - mask)
        if self.add_noise_kwargs is not None:
            noise = make_multiscale_noise(masked_img, **self.add_noise_kwargs)
            if self.noise_fill_hole:
                masked_img = masked_img + mask * noise[:, :masked_img.shape[1]]
            masked_img = torch.cat([masked_img, noise], dim=1)
        if self.concat_mask:
            masked_img = torch.cat([masked_img, mask], dim=1)
        batch['predicted_image'] = self.generator(masked_img)
        batch['inpainted'] = mask * batch['predicted_image'] + (1 - mask) * batch['image']
        if self.fake_fakes_proba > 0.001:
            if self.training and torch.rand(1).item() < self.fake_fakes_proba:
                batch['fake_fakes'], batch['fake_fakes_masks'] = self.fake_fakes_gen(img, mask)
                batch['use_fake_fakes'] = True
            else:
                batch['fake_fakes'] = torch.zeros_like(img)
                batch['fake_fakes_masks'] = torch.zeros_like(mask)
                batch['use_fake_fakes'] = False
        batch['mask_for_losses'] = self.refine_mask_for_losses(img, batch['predicted_image'], mask) if self.refine_mask_for_losses is not None and self.training else mask
        return batch

    def generator_loss(self, batch):
        img = batch['image']
        predicted_img = batch[self.image_to_discriminator]
        original_mask = batch['mask']
        supervised_mask = batch['mask_for_losses']
        l1_value = masked_l1_loss(predicted_img, img, supervised_mask, self.config.losses.l1.weight_known, self.config.losses.l1.weight_missing)
        total_loss = l1_value
        metrics = dict(gen_l1=l1_value)
        if self.config.losses.perceptual.weight > 0:
            pl_value = self.loss_pl(predicted_img, img, mask=supervised_mask).sum() * self.config.losses.perceptual.weight
            total_loss = total_loss + pl_value
            metrics['gen_pl'] = pl_value
        mask_for_discr = supervised_mask if self.distance_weighted_mask_for_discr else original_mask
        self.adversarial_loss.pre_generator_step(real_batch=img, fake_batch=predicted_img, generator=self.generator, discriminator=self.discriminator)
        discr_real_pred, discr_real_features = self.discriminator(img)
        discr_fake_pred, discr_fake_features = self.discriminator(predicted_img)
        adv_gen_loss, adv_metrics = self.adversarial_loss.generator_loss(real_batch=img, fake_batch=predicted_img, discr_real_pred=discr_real_pred, discr_fake_pred=discr_fake_pred, mask=mask_for_discr)
        total_loss = total_loss + adv_gen_loss
        metrics['gen_adv'] = adv_gen_loss
        metrics.update(add_prefix_to_keys(adv_metrics, 'adv_'))
        if self.config.losses.feature_matching.weight > 0:
            need_mask_in_fm = OmegaConf.to_container(self.config.losses.feature_matching).get('pass_mask', False)
            mask_for_fm = supervised_mask if need_mask_in_fm else None
            fm_value = feature_matching_loss(discr_fake_features, discr_real_features, mask=mask_for_fm) * self.config.losses.feature_matching.weight
            total_loss = total_loss + fm_value
            metrics['gen_fm'] = fm_value
        if self.loss_resnet_pl is not None:
            resnet_pl_value = self.loss_resnet_pl(predicted_img, img)
            total_loss = total_loss + resnet_pl_value
            metrics['gen_resnet_pl'] = resnet_pl_value
        return (total_loss, metrics)

    def discriminator_loss(self, batch):
        total_loss = 0
        metrics = {}
        predicted_img = batch[self.image_to_discriminator].detach()
        self.adversarial_loss.pre_discriminator_step(real_batch=batch['image'], fake_batch=predicted_img, generator=self.generator, discriminator=self.discriminator)
        discr_real_pred, discr_real_features = self.discriminator(batch['image'])
        discr_fake_pred, discr_fake_features = self.discriminator(predicted_img)
        adv_discr_loss, adv_metrics = self.adversarial_loss.discriminator_loss(real_batch=batch['image'], fake_batch=predicted_img, discr_real_pred=discr_real_pred, discr_fake_pred=discr_fake_pred, mask=batch['mask'])
        total_loss = total_loss + adv_discr_loss
        metrics['discr_adv'] = adv_discr_loss
        metrics.update(add_prefix_to_keys(adv_metrics, 'adv_'))
        if batch.get('use_fake_fakes', False):
            fake_fakes = batch['fake_fakes']
            self.adversarial_loss.pre_discriminator_step(real_batch=batch['image'], fake_batch=fake_fakes, generator=self.generator, discriminator=self.discriminator)
            discr_fake_fakes_pred, _ = self.discriminator(fake_fakes)
            fake_fakes_adv_discr_loss, fake_fakes_adv_metrics = self.adversarial_loss.discriminator_loss(real_batch=batch['image'], fake_batch=fake_fakes, discr_real_pred=discr_real_pred, discr_fake_pred=discr_fake_fakes_pred, mask=batch['mask'])
            total_loss = total_loss + fake_fakes_adv_discr_loss
            metrics['discr_adv_fake_fakes'] = fake_fakes_adv_discr_loss
            metrics.update(add_prefix_to_keys(fake_fakes_adv_metrics, 'adv_'))
        return (total_loss, metrics)

def __init__(self, *args, concat_mask=True, rescale_scheduler_kwargs=None, image_to_discriminator='predicted_image', add_noise_kwargs=None, noise_fill_hole=False, const_area_crop_kwargs=None, distance_weighter_kwargs=None, distance_weighted_mask_for_discr=False, fake_fakes_proba=0, fake_fakes_generator_kwargs=None, **kwargs):
    super().__init__(*args, **kwargs)
    self.concat_mask = concat_mask
    self.rescale_size_getter = get_ramp(**rescale_scheduler_kwargs) if rescale_scheduler_kwargs is not None else None
    self.image_to_discriminator = image_to_discriminator
    self.add_noise_kwargs = add_noise_kwargs
    self.noise_fill_hole = noise_fill_hole
    self.const_area_crop_kwargs = const_area_crop_kwargs
    self.refine_mask_for_losses = make_mask_distance_weighter(**distance_weighter_kwargs) if distance_weighter_kwargs is not None else None
    self.distance_weighted_mask_for_discr = distance_weighted_mask_for_discr
    self.fake_fakes_proba = fake_fakes_proba
    if self.fake_fakes_proba > 0.001:
        self.fake_fakes_gen = FakeFakesGenerator(**fake_fakes_generator_kwargs or {})

class ResNetHead(nn.Module):

    def __init__(self, input_nc, ngf=64, n_downsampling=3, n_blocks=9, norm_layer=nn.BatchNorm2d, padding_type='reflect', conv_kind='default', activation=nn.ReLU(True)):
        assert n_blocks >= 0
        super(ResNetHead, self).__init__()
        conv_layer = get_conv_block_ctor(conv_kind)
        model = [nn.ReflectionPad2d(3), conv_layer(input_nc, ngf, kernel_size=7, padding=0), norm_layer(ngf), activation]
        for i in range(n_downsampling):
            mult = 2 ** i
            model += [conv_layer(ngf * mult, ngf * mult * 2, kernel_size=3, stride=2, padding=1), norm_layer(ngf * mult * 2), activation]
        mult = 2 ** n_downsampling
        for i in range(n_blocks):
            model += [ResnetBlock(ngf * mult, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=conv_kind)]
        self.model = nn.Sequential(*model)

    def forward(self, input):
        return self.model(input)

def __init__(self, input_nc, ngf=64, n_downsampling=3, n_blocks=9, norm_layer=nn.BatchNorm2d, padding_type='reflect', conv_kind='default', activation=nn.ReLU(True)):
    assert n_blocks >= 0
    super(ResNetHead, self).__init__()
    conv_layer = get_conv_block_ctor(conv_kind)
    model = [nn.ReflectionPad2d(3), conv_layer(input_nc, ngf, kernel_size=7, padding=0), norm_layer(ngf), activation]
    for i in range(n_downsampling):
        mult = 2 ** i
        model += [conv_layer(ngf * mult, ngf * mult * 2, kernel_size=3, stride=2, padding=1), norm_layer(ngf * mult * 2), activation]
    mult = 2 ** n_downsampling
    for i in range(n_blocks):
        model += [ResnetBlock(ngf * mult, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=conv_kind)]
    self.model = nn.Sequential(*model)

class ResNetTail(nn.Module):

    def __init__(self, output_nc, ngf=64, n_downsampling=3, n_blocks=9, norm_layer=nn.BatchNorm2d, padding_type='reflect', conv_kind='default', activation=nn.ReLU(True), up_norm_layer=nn.BatchNorm2d, up_activation=nn.ReLU(True), add_out_act=False, out_extra_layers_n=0, add_in_proj=None):
        assert n_blocks >= 0
        super(ResNetTail, self).__init__()
        mult = 2 ** n_downsampling
        model = []
        if add_in_proj is not None:
            model.append(nn.Conv2d(add_in_proj, ngf * mult, kernel_size=1))
        for i in range(n_blocks):
            model += [ResnetBlock(ngf * mult, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=conv_kind)]
        for i in range(n_downsampling):
            mult = 2 ** (n_downsampling - i)
            model += [nn.ConvTranspose2d(ngf * mult, int(ngf * mult / 2), kernel_size=3, stride=2, padding=1, output_padding=1), up_norm_layer(int(ngf * mult / 2)), up_activation]
        self.model = nn.Sequential(*model)
        out_layers = []
        for _ in range(out_extra_layers_n):
            out_layers += [nn.Conv2d(ngf, ngf, kernel_size=1, padding=0), up_norm_layer(ngf), up_activation]
        out_layers += [nn.ReflectionPad2d(3), nn.Conv2d(ngf, output_nc, kernel_size=7, padding=0)]
        if add_out_act:
            out_layers.append(get_activation('tanh' if add_out_act is True else add_out_act))
        self.out_proj = nn.Sequential(*out_layers)

    def forward(self, input, return_last_act=False):
        features = self.model(input)
        out = self.out_proj(features)
        if return_last_act:
            return (out, features)
        else:
            return out

def __init__(self, output_nc, ngf=64, n_downsampling=3, n_blocks=9, norm_layer=nn.BatchNorm2d, padding_type='reflect', conv_kind='default', activation=nn.ReLU(True), up_norm_layer=nn.BatchNorm2d, up_activation=nn.ReLU(True), add_out_act=False, out_extra_layers_n=0, add_in_proj=None):
    assert n_blocks >= 0
    super(ResNetTail, self).__init__()
    mult = 2 ** n_downsampling
    model = []
    if add_in_proj is not None:
        model.append(nn.Conv2d(add_in_proj, ngf * mult, kernel_size=1))
    for i in range(n_blocks):
        model += [ResnetBlock(ngf * mult, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=conv_kind)]
    for i in range(n_downsampling):
        mult = 2 ** (n_downsampling - i)
        model += [nn.ConvTranspose2d(ngf * mult, int(ngf * mult / 2), kernel_size=3, stride=2, padding=1, output_padding=1), up_norm_layer(int(ngf * mult / 2)), up_activation]
    self.model = nn.Sequential(*model)
    out_layers = []
    for _ in range(out_extra_layers_n):
        out_layers += [nn.Conv2d(ngf, ngf, kernel_size=1, padding=0), up_norm_layer(ngf), up_activation]
    out_layers += [nn.ReflectionPad2d(3), nn.Conv2d(ngf, output_nc, kernel_size=7, padding=0)]
    if add_out_act:
        out_layers.append(get_activation('tanh' if add_out_act is True else add_out_act))
    self.out_proj = nn.Sequential(*out_layers)

class MultiscaleResNet(nn.Module):

    def __init__(self, input_nc, output_nc, ngf=64, n_downsampling=2, n_blocks_head=2, n_blocks_tail=6, n_scales=3, norm_layer=nn.BatchNorm2d, padding_type='reflect', conv_kind='default', activation=nn.ReLU(True), up_norm_layer=nn.BatchNorm2d, up_activation=nn.ReLU(True), add_out_act=False, out_extra_layers_n=0, out_cumulative=False, return_only_hr=False):
        super().__init__()
        self.heads = nn.ModuleList([ResNetHead(input_nc, ngf=ngf, n_downsampling=n_downsampling, n_blocks=n_blocks_head, norm_layer=norm_layer, padding_type=padding_type, conv_kind=conv_kind, activation=activation) for i in range(n_scales)])
        tail_in_feats = ngf * 2 ** n_downsampling + ngf
        self.tails = nn.ModuleList([ResNetTail(output_nc, ngf=ngf, n_downsampling=n_downsampling, n_blocks=n_blocks_tail, norm_layer=norm_layer, padding_type=padding_type, conv_kind=conv_kind, activation=activation, up_norm_layer=up_norm_layer, up_activation=up_activation, add_out_act=add_out_act, out_extra_layers_n=out_extra_layers_n, add_in_proj=None if i == n_scales - 1 else tail_in_feats) for i in range(n_scales)])
        self.out_cumulative = out_cumulative
        self.return_only_hr = return_only_hr

    @property
    def num_scales(self):
        return len(self.heads)

    def forward(self, ms_inputs: List[torch.Tensor], smallest_scales_num: Optional[int]=None) -> Union[torch.Tensor, List[torch.Tensor]]:
        """
        :param ms_inputs: List of inputs of different resolutions from HR to LR
        :param smallest_scales_num: int or None, number of smallest scales to take at input
        :return: Depending on return_only_hr:
            True: Only the most HR output
            False: List of outputs of different resolutions from HR to LR
        """
        if smallest_scales_num is None:
            assert len(self.heads) == len(ms_inputs), (len(self.heads), len(ms_inputs), smallest_scales_num)
            smallest_scales_num = len(self.heads)
        else:
            assert smallest_scales_num == len(ms_inputs) <= len(self.heads), (len(self.heads), len(ms_inputs), smallest_scales_num)
        cur_heads = self.heads[-smallest_scales_num:]
        ms_features = [cur_head(cur_inp) for cur_head, cur_inp in zip(cur_heads, ms_inputs)]
        all_outputs = []
        prev_tail_features = None
        for i in range(len(ms_features)):
            scale_i = -i - 1
            cur_tail_input = ms_features[-i - 1]
            if prev_tail_features is not None:
                if prev_tail_features.shape != cur_tail_input.shape:
                    prev_tail_features = F.interpolate(prev_tail_features, size=cur_tail_input.shape[2:], mode='bilinear', align_corners=False)
                cur_tail_input = torch.cat((cur_tail_input, prev_tail_features), dim=1)
            cur_out, cur_tail_feats = self.tails[scale_i](cur_tail_input, return_last_act=True)
            prev_tail_features = cur_tail_feats
            all_outputs.append(cur_out)
        if self.out_cumulative:
            all_outputs_cum = [all_outputs[0]]
            for i in range(1, len(ms_features)):
                cur_out = all_outputs[i]
                cur_out_cum = cur_out + F.interpolate(all_outputs_cum[-1], size=cur_out.shape[2:], mode='bilinear', align_corners=False)
                all_outputs_cum.append(cur_out_cum)
            all_outputs = all_outputs_cum
        if self.return_only_hr:
            return all_outputs[-1]
        else:
            return all_outputs[::-1]

def __init__(self, input_nc, output_nc, ngf=64, n_downsampling=2, n_blocks_head=2, n_blocks_tail=6, n_scales=3, norm_layer=nn.BatchNorm2d, padding_type='reflect', conv_kind='default', activation=nn.ReLU(True), up_norm_layer=nn.BatchNorm2d, up_activation=nn.ReLU(True), add_out_act=False, out_extra_layers_n=0, out_cumulative=False, return_only_hr=False):
    super().__init__()
    self.heads = nn.ModuleList([ResNetHead(input_nc, ngf=ngf, n_downsampling=n_downsampling, n_blocks=n_blocks_head, norm_layer=norm_layer, padding_type=padding_type, conv_kind=conv_kind, activation=activation) for i in range(n_scales)])
    tail_in_feats = ngf * 2 ** n_downsampling + ngf
    self.tails = nn.ModuleList([ResNetTail(output_nc, ngf=ngf, n_downsampling=n_downsampling, n_blocks=n_blocks_tail, norm_layer=norm_layer, padding_type=padding_type, conv_kind=conv_kind, activation=activation, up_norm_layer=up_norm_layer, up_activation=up_activation, add_out_act=add_out_act, out_extra_layers_n=out_extra_layers_n, add_in_proj=None if i == n_scales - 1 else tail_in_feats) for i in range(n_scales)])
    self.out_cumulative = out_cumulative
    self.return_only_hr = return_only_hr

class MultiscaleDiscriminatorSimple(nn.Module):

    def __init__(self, ms_impl):
        super().__init__()
        self.ms_impl = nn.ModuleList(ms_impl)

    @property
    def num_scales(self):
        return len(self.ms_impl)

    def forward(self, ms_inputs: List[torch.Tensor], smallest_scales_num: Optional[int]=None) -> List[Tuple[torch.Tensor, List[torch.Tensor]]]:
        """
        :param ms_inputs: List of inputs of different resolutions from HR to LR
        :param smallest_scales_num: int or None, number of smallest scales to take at input
        :return: List of pairs (prediction, features) for different resolutions from HR to LR
        """
        if smallest_scales_num is None:
            assert len(self.ms_impl) == len(ms_inputs), (len(self.ms_impl), len(ms_inputs), smallest_scales_num)
            smallest_scales_num = len(self.heads)
        else:
            assert smallest_scales_num == len(ms_inputs) <= len(self.ms_impl), (len(self.ms_impl), len(ms_inputs), smallest_scales_num)
        return [cur_discr(cur_input) for cur_discr, cur_input in zip(self.ms_impl[-smallest_scales_num:], ms_inputs)]

def __init__(self, ms_impl):
    super().__init__()
    self.ms_impl = nn.ModuleList(ms_impl)

class SingleToMultiScaleInputMixin:

    def forward(self, x: torch.Tensor) -> List:
        orig_height, orig_width = x.shape[2:]
        factors = [2 ** i for i in range(self.num_scales)]
        ms_inputs = [F.interpolate(x, size=(orig_height // f, orig_width // f), mode='bilinear', align_corners=False) for f in factors]
        return super().forward(ms_inputs)

def forward(self, x: torch.Tensor) -> List:
    orig_height, orig_width = x.shape[2:]
    factors = [2 ** i for i in range(self.num_scales)]
    ms_inputs = [F.interpolate(x, size=(orig_height // f, orig_width // f), mode='bilinear', align_corners=False) for f in factors]
    return super().forward(ms_inputs)

class GeneratorMultiToSingleOutputMixin:

    def forward(self, x):
        return super().forward(x)[0]

def forward(self, x):
    return super().forward(x)[0]

class DiscriminatorMultiToSingleOutputMixin:

    def forward(self, x):
        out_feat_tuples = super().forward(x)
        return (out_feat_tuples[0][0], [f for _, flist in out_feat_tuples for f in flist])

def forward(self, x):
    out_feat_tuples = super().forward(x)
    return (out_feat_tuples[0][0], [f for _, flist in out_feat_tuples for f in flist])

class DiscriminatorMultiToSingleOutputStackedMixin:

    def __init__(self, *args, return_feats_only_levels=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.return_feats_only_levels = return_feats_only_levels

    def forward(self, x):
        out_feat_tuples = super().forward(x)
        outs = [out for out, _ in out_feat_tuples]
        scaled_outs = [outs[0]] + [F.interpolate(cur_out, size=outs[0].shape[-2:], mode='bilinear', align_corners=False) for cur_out in outs[1:]]
        out = torch.cat(scaled_outs, dim=1)
        if self.return_feats_only_levels is not None:
            feat_lists = [out_feat_tuples[i][1] for i in self.return_feats_only_levels]
        else:
            feat_lists = [flist for _, flist in out_feat_tuples]
        feats = [f for flist in feat_lists for f in flist]
        return (out, feats)

def __init__(self, *args, return_feats_only_levels=None, **kwargs):
    super().__init__(*args, **kwargs)
    self.return_feats_only_levels = return_feats_only_levels

def forward(self, x):
    out_feat_tuples = super().forward(x)
    outs = [out for out, _ in out_feat_tuples]
    scaled_outs = [outs[0]] + [F.interpolate(cur_out, size=outs[0].shape[-2:], mode='bilinear', align_corners=False) for cur_out in outs[1:]]
    out = torch.cat(scaled_outs, dim=1)
    if self.return_feats_only_levels is not None:
        feat_lists = [out_feat_tuples[i][1] for i in self.return_feats_only_levels]
    else:
        feat_lists = [flist for _, flist in out_feat_tuples]
    feats = [f for flist in feat_lists for f in flist]
    return (out, feats)

def get_activation(kind='tanh'):
    if kind == 'tanh':
        return nn.Tanh()
    if kind == 'sigmoid':
        return nn.Sigmoid()
    if kind is False:
        return nn.Identity()
    raise ValueError(f'Unknown activation kind {kind}')

class SimpleMultiStepGenerator(nn.Module):

    def __init__(self, steps: List[nn.Module]):
        super().__init__()
        self.steps = nn.ModuleList(steps)

    def forward(self, x):
        cur_in = x
        outs = []
        for step in self.steps:
            cur_out = step(cur_in)
            outs.append(cur_out)
            cur_in = torch.cat((cur_in, cur_out), dim=1)
        return torch.cat(outs[::-1], dim=1)

def __init__(self, steps: List[nn.Module]):
    super().__init__()
    self.steps = nn.ModuleList(steps)

def deconv_factory(kind, ngf, mult, norm_layer, activation, max_features):
    if kind == 'convtranspose':
        return [nn.ConvTranspose2d(min(max_features, ngf * mult), min(max_features, int(ngf * mult / 2)), kernel_size=3, stride=2, padding=1, output_padding=1), norm_layer(min(max_features, int(ngf * mult / 2))), activation]
    elif kind == 'bilinear':
        return [nn.Upsample(scale_factor=2, mode='bilinear'), DepthWiseSeperableConv(min(max_features, ngf * mult), min(max_features, int(ngf * mult / 2)), kernel_size=3, stride=1, padding=1), norm_layer(min(max_features, int(ngf * mult / 2))), activation]
    else:
        raise Exception(f'Invalid deconv kind: {kind}')

class FFCSE_block(nn.Module):

    def __init__(self, channels, ratio_g):
        super(FFCSE_block, self).__init__()
        in_cg = int(channels * ratio_g)
        in_cl = channels - in_cg
        r = 16
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.conv1 = nn.Conv2d(channels, channels // r, kernel_size=1, bias=True)
        self.relu1 = nn.ReLU(inplace=True)
        self.conv_a2l = None if in_cl == 0 else nn.Conv2d(channels // r, in_cl, kernel_size=1, bias=True)
        self.conv_a2g = None if in_cg == 0 else nn.Conv2d(channels // r, in_cg, kernel_size=1, bias=True)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        x = x if type(x) is tuple else (x, 0)
        id_l, id_g = x
        x = id_l if type(id_g) is int else torch.cat([id_l, id_g], dim=1)
        x = self.avgpool(x)
        x = self.relu1(self.conv1(x))
        x_l = 0 if self.conv_a2l is None else id_l * self.sigmoid(self.conv_a2l(x))
        x_g = 0 if self.conv_a2g is None else id_g * self.sigmoid(self.conv_a2g(x))
        return (x_l, x_g)

def __init__(self, channels, ratio_g):
    super(FFCSE_block, self).__init__()
    in_cg = int(channels * ratio_g)
    in_cl = channels - in_cg
    r = 16
    self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
    self.conv1 = nn.Conv2d(channels, channels // r, kernel_size=1, bias=True)
    self.relu1 = nn.ReLU(inplace=True)
    self.conv_a2l = None if in_cl == 0 else nn.Conv2d(channels // r, in_cl, kernel_size=1, bias=True)
    self.conv_a2g = None if in_cg == 0 else nn.Conv2d(channels // r, in_cg, kernel_size=1, bias=True)
    self.sigmoid = nn.Sigmoid()

class FourierUnit(nn.Module):

    def __init__(self, in_channels, out_channels, groups=1, spatial_scale_factor=None, spatial_scale_mode='bilinear', spectral_pos_encoding=False, use_se=False, se_kwargs=None, ffc3d=False, fft_norm='ortho'):
        super(FourierUnit, self).__init__()
        self.groups = groups
        self.conv_layer = torch.nn.Conv2d(in_channels=in_channels * 2 + (2 if spectral_pos_encoding else 0), out_channels=out_channels * 2, kernel_size=1, stride=1, padding=0, groups=self.groups, bias=False)
        self.bn = torch.nn.BatchNorm2d(out_channels * 2)
        self.relu = torch.nn.ReLU(inplace=True)
        self.use_se = use_se
        if use_se:
            if se_kwargs is None:
                se_kwargs = {}
            self.se = SELayer(self.conv_layer.in_channels, **se_kwargs)
        self.spatial_scale_factor = spatial_scale_factor
        self.spatial_scale_mode = spatial_scale_mode
        self.spectral_pos_encoding = spectral_pos_encoding
        self.ffc3d = ffc3d
        self.fft_norm = fft_norm

    def forward(self, x):
        batch = x.shape[0]
        if self.spatial_scale_factor is not None:
            orig_size = x.shape[-2:]
            x = F.interpolate(x, scale_factor=self.spatial_scale_factor, mode=self.spatial_scale_mode, align_corners=False)
        r_size = x.size()
        fft_dim = (-3, -2, -1) if self.ffc3d else (-2, -1)
        ffted = torch.fft.rfftn(x, dim=fft_dim, norm=self.fft_norm)
        ffted = torch.stack((ffted.real, ffted.imag), dim=-1)
        ffted = ffted.permute(0, 1, 4, 2, 3).contiguous()
        ffted = ffted.view((batch, -1) + ffted.size()[3:])
        if self.spectral_pos_encoding:
            height, width = ffted.shape[-2:]
            coords_vert = torch.linspace(0, 1, height)[None, None, :, None].expand(batch, 1, height, width).to(ffted)
            coords_hor = torch.linspace(0, 1, width)[None, None, None, :].expand(batch, 1, height, width).to(ffted)
            ffted = torch.cat((coords_vert, coords_hor, ffted), dim=1)
        if self.use_se:
            ffted = self.se(ffted)
        ffted = self.conv_layer(ffted)
        ffted = self.relu(self.bn(ffted))
        ffted = ffted.view((batch, -1, 2) + ffted.size()[2:]).permute(0, 1, 3, 4, 2).contiguous()
        ffted = torch.complex(ffted[..., 0], ffted[..., 1])
        ifft_shape_slice = x.shape[-3:] if self.ffc3d else x.shape[-2:]
        output = torch.fft.irfftn(ffted, s=ifft_shape_slice, dim=fft_dim, norm=self.fft_norm)
        if self.spatial_scale_factor is not None:
            output = F.interpolate(output, size=orig_size, mode=self.spatial_scale_mode, align_corners=False)
        return output

def __init__(self, in_channels, out_channels, groups=1, spatial_scale_factor=None, spatial_scale_mode='bilinear', spectral_pos_encoding=False, use_se=False, se_kwargs=None, ffc3d=False, fft_norm='ortho'):
    super(FourierUnit, self).__init__()
    self.groups = groups
    self.conv_layer = torch.nn.Conv2d(in_channels=in_channels * 2 + (2 if spectral_pos_encoding else 0), out_channels=out_channels * 2, kernel_size=1, stride=1, padding=0, groups=self.groups, bias=False)
    self.bn = torch.nn.BatchNorm2d(out_channels * 2)
    self.relu = torch.nn.ReLU(inplace=True)
    self.use_se = use_se
    if use_se:
        if se_kwargs is None:
            se_kwargs = {}
        self.se = SELayer(self.conv_layer.in_channels, **se_kwargs)
    self.spatial_scale_factor = spatial_scale_factor
    self.spatial_scale_mode = spatial_scale_mode
    self.spectral_pos_encoding = spectral_pos_encoding
    self.ffc3d = ffc3d
    self.fft_norm = fft_norm

class SpectralTransform(nn.Module):

    def __init__(self, in_channels, out_channels, stride=1, groups=1, enable_lfu=True, **fu_kwargs):
        super(SpectralTransform, self).__init__()
        self.enable_lfu = enable_lfu
        if stride == 2:
            self.downsample = nn.AvgPool2d(kernel_size=(2, 2), stride=2)
        else:
            self.downsample = nn.Identity()
        self.stride = stride
        self.conv1 = nn.Sequential(nn.Conv2d(in_channels, out_channels // 2, kernel_size=1, groups=groups, bias=False), nn.BatchNorm2d(out_channels // 2), nn.ReLU(inplace=True))
        self.fu = FourierUnit(out_channels // 2, out_channels // 2, groups, **fu_kwargs)
        if self.enable_lfu:
            self.lfu = FourierUnit(out_channels // 2, out_channels // 2, groups)
        self.conv2 = torch.nn.Conv2d(out_channels // 2, out_channels, kernel_size=1, groups=groups, bias=False)

    def forward(self, x):
        x = self.downsample(x)
        x = self.conv1(x)
        output = self.fu(x)
        if self.enable_lfu:
            n, c, h, w = x.shape
            split_no = 2
            split_s = h // split_no
            xs = torch.cat(torch.split(x[:, :c // 4], split_s, dim=-2), dim=1).contiguous()
            xs = torch.cat(torch.split(xs, split_s, dim=-1), dim=1).contiguous()
            xs = self.lfu(xs)
            xs = xs.repeat(1, 1, split_no, split_no).contiguous()
        else:
            xs = 0
        output = self.conv2(x + output + xs)
        return output

def __init__(self, in_channels, out_channels, stride=1, groups=1, enable_lfu=True, **fu_kwargs):
    super(SpectralTransform, self).__init__()
    self.enable_lfu = enable_lfu
    if stride == 2:
        self.downsample = nn.AvgPool2d(kernel_size=(2, 2), stride=2)
    else:
        self.downsample = nn.Identity()
    self.stride = stride
    self.conv1 = nn.Sequential(nn.Conv2d(in_channels, out_channels // 2, kernel_size=1, groups=groups, bias=False), nn.BatchNorm2d(out_channels // 2), nn.ReLU(inplace=True))
    self.fu = FourierUnit(out_channels // 2, out_channels // 2, groups, **fu_kwargs)
    if self.enable_lfu:
        self.lfu = FourierUnit(out_channels // 2, out_channels // 2, groups)
    self.conv2 = torch.nn.Conv2d(out_channels // 2, out_channels, kernel_size=1, groups=groups, bias=False)

class FFC(nn.Module):

    def __init__(self, in_channels, out_channels, kernel_size, ratio_gin, ratio_gout, stride=1, padding=0, dilation=1, groups=1, bias=False, enable_lfu=True, padding_type='reflect', gated=False, **spectral_kwargs):
        super(FFC, self).__init__()
        assert stride == 1 or stride == 2, 'Stride should be 1 or 2.'
        self.stride = stride
        in_cg = int(in_channels * ratio_gin)
        in_cl = in_channels - in_cg
        out_cg = int(out_channels * ratio_gout)
        out_cl = out_channels - out_cg
        self.ratio_gin = ratio_gin
        self.ratio_gout = ratio_gout
        self.global_in_num = in_cg
        module = nn.Identity if in_cl == 0 or out_cl == 0 else nn.Conv2d
        self.convl2l = module(in_cl, out_cl, kernel_size, stride, padding, dilation, groups, bias, padding_mode=padding_type)
        module = nn.Identity if in_cl == 0 or out_cg == 0 else nn.Conv2d
        self.convl2g = module(in_cl, out_cg, kernel_size, stride, padding, dilation, groups, bias, padding_mode=padding_type)
        module = nn.Identity if in_cg == 0 or out_cl == 0 else nn.Conv2d
        self.convg2l = module(in_cg, out_cl, kernel_size, stride, padding, dilation, groups, bias, padding_mode=padding_type)
        module = nn.Identity if in_cg == 0 or out_cg == 0 else SpectralTransform
        self.convg2g = module(in_cg, out_cg, stride, 1 if groups == 1 else groups // 2, enable_lfu, **spectral_kwargs)
        self.gated = gated
        module = nn.Identity if in_cg == 0 or out_cl == 0 or (not self.gated) else nn.Conv2d
        self.gate = module(in_channels, 2, 1)

    def forward(self, x):
        x_l, x_g = x if type(x) is tuple else (x, 0)
        out_xl, out_xg = (0, 0)
        if self.gated:
            total_input_parts = [x_l]
            if torch.is_tensor(x_g):
                total_input_parts.append(x_g)
            total_input = torch.cat(total_input_parts, dim=1)
            gates = torch.sigmoid(self.gate(total_input))
            g2l_gate, l2g_gate = gates.chunk(2, dim=1)
        else:
            g2l_gate, l2g_gate = (1, 1)
        if self.ratio_gout != 1:
            out_xl = self.convl2l(x_l) + self.convg2l(x_g) * g2l_gate
        if self.ratio_gout != 0:
            out_xg = self.convl2g(x_l) * l2g_gate + self.convg2g(x_g)
        return (out_xl, out_xg)

def __init__(self, in_channels, out_channels, kernel_size, ratio_gin, ratio_gout, stride=1, padding=0, dilation=1, groups=1, bias=False, enable_lfu=True, padding_type='reflect', gated=False, **spectral_kwargs):
    super(FFC, self).__init__()
    assert stride == 1 or stride == 2, 'Stride should be 1 or 2.'
    self.stride = stride
    in_cg = int(in_channels * ratio_gin)
    in_cl = in_channels - in_cg
    out_cg = int(out_channels * ratio_gout)
    out_cl = out_channels - out_cg
    self.ratio_gin = ratio_gin
    self.ratio_gout = ratio_gout
    self.global_in_num = in_cg
    module = nn.Identity if in_cl == 0 or out_cl == 0 else nn.Conv2d
    self.convl2l = module(in_cl, out_cl, kernel_size, stride, padding, dilation, groups, bias, padding_mode=padding_type)
    module = nn.Identity if in_cl == 0 or out_cg == 0 else nn.Conv2d
    self.convl2g = module(in_cl, out_cg, kernel_size, stride, padding, dilation, groups, bias, padding_mode=padding_type)
    module = nn.Identity if in_cg == 0 or out_cl == 0 else nn.Conv2d
    self.convg2l = module(in_cg, out_cl, kernel_size, stride, padding, dilation, groups, bias, padding_mode=padding_type)
    module = nn.Identity if in_cg == 0 or out_cg == 0 else SpectralTransform
    self.convg2g = module(in_cg, out_cg, stride, 1 if groups == 1 else groups // 2, enable_lfu, **spectral_kwargs)
    self.gated = gated
    module = nn.Identity if in_cg == 0 or out_cl == 0 or (not self.gated) else nn.Conv2d
    self.gate = module(in_channels, 2, 1)

class FFCResnetBlock(nn.Module):

    def __init__(self, dim, padding_type, norm_layer, activation_layer=nn.ReLU, dilation=1, spatial_transform_kwargs=None, inline=False, **conv_kwargs):
        super().__init__()
        self.conv1 = FFC_BN_ACT(dim, dim, kernel_size=3, padding=dilation, dilation=dilation, norm_layer=norm_layer, activation_layer=activation_layer, padding_type=padding_type, **conv_kwargs)
        self.conv2 = FFC_BN_ACT(dim, dim, kernel_size=3, padding=dilation, dilation=dilation, norm_layer=norm_layer, activation_layer=activation_layer, padding_type=padding_type, **conv_kwargs)
        if spatial_transform_kwargs is not None:
            self.conv1 = LearnableSpatialTransformWrapper(self.conv1, **spatial_transform_kwargs)
            self.conv2 = LearnableSpatialTransformWrapper(self.conv2, **spatial_transform_kwargs)
        self.inline = inline

    def forward(self, x):
        if self.inline:
            x_l, x_g = (x[:, :-self.conv1.ffc.global_in_num], x[:, -self.conv1.ffc.global_in_num:])
        else:
            x_l, x_g = x if type(x) is tuple else (x, 0)
        id_l, id_g = (x_l, x_g)
        x_l, x_g = self.conv1((x_l, x_g))
        x_l, x_g = self.conv2((x_l, x_g))
        x_l, x_g = (id_l + x_l, id_g + x_g)
        out = (x_l, x_g)
        if self.inline:
            out = torch.cat(out, dim=1)
        return out

def __init__(self, dim, padding_type, norm_layer, activation_layer=nn.ReLU, dilation=1, spatial_transform_kwargs=None, inline=False, **conv_kwargs):
    super().__init__()
    self.conv1 = FFC_BN_ACT(dim, dim, kernel_size=3, padding=dilation, dilation=dilation, norm_layer=norm_layer, activation_layer=activation_layer, padding_type=padding_type, **conv_kwargs)
    self.conv2 = FFC_BN_ACT(dim, dim, kernel_size=3, padding=dilation, dilation=dilation, norm_layer=norm_layer, activation_layer=activation_layer, padding_type=padding_type, **conv_kwargs)
    if spatial_transform_kwargs is not None:
        self.conv1 = LearnableSpatialTransformWrapper(self.conv1, **spatial_transform_kwargs)
        self.conv2 = LearnableSpatialTransformWrapper(self.conv2, **spatial_transform_kwargs)
    self.inline = inline

class FFCResNetGenerator(nn.Module):

    def __init__(self, input_nc, output_nc, ngf=64, n_downsampling=3, n_blocks=9, norm_layer=nn.BatchNorm2d, padding_type='reflect', activation_layer=nn.ReLU, up_norm_layer=nn.BatchNorm2d, up_activation=nn.ReLU(True), init_conv_kwargs={}, downsample_conv_kwargs={}, resnet_conv_kwargs={}, spatial_transform_layers=None, spatial_transform_kwargs={}, add_out_act=True, max_features=1024, out_ffc=False, out_ffc_kwargs={}):
        assert n_blocks >= 0
        super().__init__()
        model = [nn.ReflectionPad2d(3), FFC_BN_ACT(input_nc, ngf, kernel_size=7, padding=0, norm_layer=norm_layer, activation_layer=activation_layer, **init_conv_kwargs)]
        for i in range(n_downsampling):
            mult = 2 ** i
            if i == n_downsampling - 1:
                cur_conv_kwargs = dict(downsample_conv_kwargs)
                cur_conv_kwargs['ratio_gout'] = resnet_conv_kwargs.get('ratio_gin', 0)
            else:
                cur_conv_kwargs = downsample_conv_kwargs
            model += [FFC_BN_ACT(min(max_features, ngf * mult), min(max_features, ngf * mult * 2), kernel_size=3, stride=2, padding=1, norm_layer=norm_layer, activation_layer=activation_layer, **cur_conv_kwargs)]
        mult = 2 ** n_downsampling
        feats_num_bottleneck = min(max_features, ngf * mult)
        for i in range(n_blocks):
            cur_resblock = FFCResnetBlock(feats_num_bottleneck, padding_type=padding_type, activation_layer=activation_layer, norm_layer=norm_layer, **resnet_conv_kwargs)
            if spatial_transform_layers is not None and i in spatial_transform_layers:
                cur_resblock = LearnableSpatialTransformWrapper(cur_resblock, **spatial_transform_kwargs)
            model += [cur_resblock]
        model += [ConcatTupleLayer()]
        for i in range(n_downsampling):
            mult = 2 ** (n_downsampling - i)
            model += [nn.ConvTranspose2d(min(max_features, ngf * mult), min(max_features, int(ngf * mult / 2)), kernel_size=3, stride=2, padding=1, output_padding=1), up_norm_layer(min(max_features, int(ngf * mult / 2))), up_activation]
        if out_ffc:
            model += [FFCResnetBlock(ngf, padding_type=padding_type, activation_layer=activation_layer, norm_layer=norm_layer, inline=True, **out_ffc_kwargs)]
        model += [nn.ReflectionPad2d(3), nn.Conv2d(ngf, output_nc, kernel_size=7, padding=0)]
        if add_out_act:
            model.append(get_activation('tanh' if add_out_act is True else add_out_act))
        self.model = nn.Sequential(*model)

    def forward(self, input):
        return self.model(input)

def __init__(self, input_nc, output_nc, ngf=64, n_downsampling=3, n_blocks=9, norm_layer=nn.BatchNorm2d, padding_type='reflect', activation_layer=nn.ReLU, up_norm_layer=nn.BatchNorm2d, up_activation=nn.ReLU(True), init_conv_kwargs={}, downsample_conv_kwargs={}, resnet_conv_kwargs={}, spatial_transform_layers=None, spatial_transform_kwargs={}, add_out_act=True, max_features=1024, out_ffc=False, out_ffc_kwargs={}):
    assert n_blocks >= 0
    super().__init__()
    model = [nn.ReflectionPad2d(3), FFC_BN_ACT(input_nc, ngf, kernel_size=7, padding=0, norm_layer=norm_layer, activation_layer=activation_layer, **init_conv_kwargs)]
    for i in range(n_downsampling):
        mult = 2 ** i
        if i == n_downsampling - 1:
            cur_conv_kwargs = dict(downsample_conv_kwargs)
            cur_conv_kwargs['ratio_gout'] = resnet_conv_kwargs.get('ratio_gin', 0)
        else:
            cur_conv_kwargs = downsample_conv_kwargs
        model += [FFC_BN_ACT(min(max_features, ngf * mult), min(max_features, ngf * mult * 2), kernel_size=3, stride=2, padding=1, norm_layer=norm_layer, activation_layer=activation_layer, **cur_conv_kwargs)]
    mult = 2 ** n_downsampling
    feats_num_bottleneck = min(max_features, ngf * mult)
    for i in range(n_blocks):
        cur_resblock = FFCResnetBlock(feats_num_bottleneck, padding_type=padding_type, activation_layer=activation_layer, norm_layer=norm_layer, **resnet_conv_kwargs)
        if spatial_transform_layers is not None and i in spatial_transform_layers:
            cur_resblock = LearnableSpatialTransformWrapper(cur_resblock, **spatial_transform_kwargs)
        model += [cur_resblock]
    model += [ConcatTupleLayer()]
    for i in range(n_downsampling):
        mult = 2 ** (n_downsampling - i)
        model += [nn.ConvTranspose2d(min(max_features, ngf * mult), min(max_features, int(ngf * mult / 2)), kernel_size=3, stride=2, padding=1, output_padding=1), up_norm_layer(min(max_features, int(ngf * mult / 2))), up_activation]
    if out_ffc:
        model += [FFCResnetBlock(ngf, padding_type=padding_type, activation_layer=activation_layer, norm_layer=norm_layer, inline=True, **out_ffc_kwargs)]
    model += [nn.ReflectionPad2d(3), nn.Conv2d(ngf, output_nc, kernel_size=7, padding=0)]
    if add_out_act:
        model.append(get_activation('tanh' if add_out_act is True else add_out_act))
    self.model = nn.Sequential(*model)

class FFCNLayerDiscriminator(BaseDiscriminator):

    def __init__(self, input_nc, ndf=64, n_layers=3, norm_layer=nn.BatchNorm2d, max_features=512, init_conv_kwargs={}, conv_kwargs={}):
        super().__init__()
        self.n_layers = n_layers

        def _act_ctor(inplace=True):
            return nn.LeakyReLU(negative_slope=0.2, inplace=inplace)
        kw = 3
        padw = int(np.ceil((kw - 1.0) / 2))
        sequence = [[FFC_BN_ACT(input_nc, ndf, kernel_size=kw, padding=padw, norm_layer=norm_layer, activation_layer=_act_ctor, **init_conv_kwargs)]]
        nf = ndf
        for n in range(1, n_layers):
            nf_prev = nf
            nf = min(nf * 2, max_features)
            cur_model = [FFC_BN_ACT(nf_prev, nf, kernel_size=kw, stride=2, padding=padw, norm_layer=norm_layer, activation_layer=_act_ctor, **conv_kwargs)]
            sequence.append(cur_model)
        nf_prev = nf
        nf = min(nf * 2, 512)
        cur_model = [FFC_BN_ACT(nf_prev, nf, kernel_size=kw, stride=1, padding=padw, norm_layer=norm_layer, activation_layer=lambda *args, **kwargs: nn.LeakyReLU(*args, negative_slope=0.2, **kwargs), **conv_kwargs), ConcatTupleLayer()]
        sequence.append(cur_model)
        sequence += [[nn.Conv2d(nf, 1, kernel_size=kw, stride=1, padding=padw)]]
        for n in range(len(sequence)):
            setattr(self, 'model' + str(n), nn.Sequential(*sequence[n]))

    def get_all_activations(self, x):
        res = [x]
        for n in range(self.n_layers + 2):
            model = getattr(self, 'model' + str(n))
            res.append(model(res[-1]))
        return res[1:]

    def forward(self, x):
        act = self.get_all_activations(x)
        feats = []
        for out in act[:-1]:
            if isinstance(out, tuple):
                if torch.is_tensor(out[1]):
                    out = torch.cat(out, dim=1)
                else:
                    out = out[0]
            feats.append(out)
        return (act[-1], feats)

def __init__(self, input_nc, ndf=64, n_layers=3, norm_layer=nn.BatchNorm2d, max_features=512, init_conv_kwargs={}, conv_kwargs={}):
    super().__init__()
    self.n_layers = n_layers

    def _act_ctor(inplace=True):
        return nn.LeakyReLU(negative_slope=0.2, inplace=inplace)
    kw = 3
    padw = int(np.ceil((kw - 1.0) / 2))
    sequence = [[FFC_BN_ACT(input_nc, ndf, kernel_size=kw, padding=padw, norm_layer=norm_layer, activation_layer=_act_ctor, **init_conv_kwargs)]]
    nf = ndf
    for n in range(1, n_layers):
        nf_prev = nf
        nf = min(nf * 2, max_features)
        cur_model = [FFC_BN_ACT(nf_prev, nf, kernel_size=kw, stride=2, padding=padw, norm_layer=norm_layer, activation_layer=_act_ctor, **conv_kwargs)]
        sequence.append(cur_model)
    nf_prev = nf
    nf = min(nf * 2, 512)
    cur_model = [FFC_BN_ACT(nf_prev, nf, kernel_size=kw, stride=1, padding=padw, norm_layer=norm_layer, activation_layer=lambda *args, **kwargs: nn.LeakyReLU(*args, negative_slope=0.2, **kwargs), **conv_kwargs), ConcatTupleLayer()]
    sequence.append(cur_model)
    sequence += [[nn.Conv2d(nf, 1, kernel_size=kw, stride=1, padding=padw)]]
    for n in range(len(sequence)):
        setattr(self, 'model' + str(n), nn.Sequential(*sequence[n]))

def _act_ctor(inplace=True):
    return nn.LeakyReLU(negative_slope=0.2, inplace=inplace)

class SELayer(nn.Module):

    def __init__(self, channel, reduction=16):
        super(SELayer, self).__init__()
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Sequential(nn.Linear(channel, channel // reduction, bias=False), nn.ReLU(inplace=True), nn.Linear(channel // reduction, channel, bias=False), nn.Sigmoid())

    def forward(self, x):
        b, c, _, _ = x.size()
        y = self.avg_pool(x).view(b, c)
        y = self.fc(y).view(b, c, 1, 1)
        res = x * y.expand_as(x)
        return res

def __init__(self, channel, reduction=16):
    super(SELayer, self).__init__()
    self.avg_pool = nn.AdaptiveAvgPool2d(1)
    self.fc = nn.Sequential(nn.Linear(channel, channel // reduction, bias=False), nn.ReLU(inplace=True), nn.Linear(channel // reduction, channel, bias=False), nn.Sigmoid())

class MultidilatedConv(nn.Module):

    def __init__(self, in_dim, out_dim, kernel_size, dilation_num=3, comb_mode='sum', equal_dim=True, shared_weights=False, padding=1, min_dilation=1, shuffle_in_channels=False, use_depthwise=False, **kwargs):
        super().__init__()
        convs = []
        self.equal_dim = equal_dim
        assert comb_mode in ('cat_out', 'sum', 'cat_in', 'cat_both'), comb_mode
        if comb_mode in ('cat_out', 'cat_both'):
            self.cat_out = True
            if equal_dim:
                assert out_dim % dilation_num == 0
                out_dims = [out_dim // dilation_num] * dilation_num
                self.index = sum([[i + j * out_dims[0] for j in range(dilation_num)] for i in range(out_dims[0])], [])
            else:
                out_dims = [out_dim // 2 ** (i + 1) for i in range(dilation_num - 1)]
                out_dims.append(out_dim - sum(out_dims))
                index = []
                starts = [0] + out_dims[:-1]
                lengths = [out_dims[i] // out_dims[-1] for i in range(dilation_num)]
                for i in range(out_dims[-1]):
                    for j in range(dilation_num):
                        index += list(range(starts[j], starts[j] + lengths[j]))
                        starts[j] += lengths[j]
                self.index = index
                assert len(index) == out_dim
            self.out_dims = out_dims
        else:
            self.cat_out = False
            self.out_dims = [out_dim] * dilation_num
        if comb_mode in ('cat_in', 'cat_both'):
            if equal_dim:
                assert in_dim % dilation_num == 0
                in_dims = [in_dim // dilation_num] * dilation_num
            else:
                in_dims = [in_dim // 2 ** (i + 1) for i in range(dilation_num - 1)]
                in_dims.append(in_dim - sum(in_dims))
            self.in_dims = in_dims
            self.cat_in = True
        else:
            self.cat_in = False
            self.in_dims = [in_dim] * dilation_num
        conv_type = DepthWiseSeperableConv if use_depthwise else nn.Conv2d
        dilation = min_dilation
        for i in range(dilation_num):
            if isinstance(padding, int):
                cur_padding = padding * dilation
            else:
                cur_padding = padding[i]
            convs.append(conv_type(self.in_dims[i], self.out_dims[i], kernel_size, padding=cur_padding, dilation=dilation, **kwargs))
            if i > 0 and shared_weights:
                convs[-1].weight = convs[0].weight
                convs[-1].bias = convs[0].bias
            dilation *= 2
        self.convs = nn.ModuleList(convs)
        self.shuffle_in_channels = shuffle_in_channels
        if self.shuffle_in_channels:
            in_channels_permute = list(range(in_dim))
            random.shuffle(in_channels_permute)
            self.register_buffer('in_channels_permute', torch.tensor(in_channels_permute))

    def forward(self, x):
        if self.shuffle_in_channels:
            x = x[:, self.in_channels_permute]
        outs = []
        if self.cat_in:
            if self.equal_dim:
                x = x.chunk(len(self.convs), dim=1)
            else:
                new_x = []
                start = 0
                for dim in self.in_dims:
                    new_x.append(x[:, start:start + dim])
                    start += dim
                x = new_x
        for i, conv in enumerate(self.convs):
            if self.cat_in:
                input = x[i]
            else:
                input = x
            outs.append(conv(input))
        if self.cat_out:
            out = torch.cat(outs, dim=1)[:, self.index]
        else:
            out = sum(outs)
        return out

def __init__(self, in_dim, out_dim, kernel_size, dilation_num=3, comb_mode='sum', equal_dim=True, shared_weights=False, padding=1, min_dilation=1, shuffle_in_channels=False, use_depthwise=False, **kwargs):
    super().__init__()
    convs = []
    self.equal_dim = equal_dim
    assert comb_mode in ('cat_out', 'sum', 'cat_in', 'cat_both'), comb_mode
    if comb_mode in ('cat_out', 'cat_both'):
        self.cat_out = True
        if equal_dim:
            assert out_dim % dilation_num == 0
            out_dims = [out_dim // dilation_num] * dilation_num
            self.index = sum([[i + j * out_dims[0] for j in range(dilation_num)] for i in range(out_dims[0])], [])
        else:
            out_dims = [out_dim // 2 ** (i + 1) for i in range(dilation_num - 1)]
            out_dims.append(out_dim - sum(out_dims))
            index = []
            starts = [0] + out_dims[:-1]
            lengths = [out_dims[i] // out_dims[-1] for i in range(dilation_num)]
            for i in range(out_dims[-1]):
                for j in range(dilation_num):
                    index += list(range(starts[j], starts[j] + lengths[j]))
                    starts[j] += lengths[j]
            self.index = index
            assert len(index) == out_dim
        self.out_dims = out_dims
    else:
        self.cat_out = False
        self.out_dims = [out_dim] * dilation_num
    if comb_mode in ('cat_in', 'cat_both'):
        if equal_dim:
            assert in_dim % dilation_num == 0
            in_dims = [in_dim // dilation_num] * dilation_num
        else:
            in_dims = [in_dim // 2 ** (i + 1) for i in range(dilation_num - 1)]
            in_dims.append(in_dim - sum(in_dims))
        self.in_dims = in_dims
        self.cat_in = True
    else:
        self.cat_in = False
        self.in_dims = [in_dim] * dilation_num
    conv_type = DepthWiseSeperableConv if use_depthwise else nn.Conv2d
    dilation = min_dilation
    for i in range(dilation_num):
        if isinstance(padding, int):
            cur_padding = padding * dilation
        else:
            cur_padding = padding[i]
        convs.append(conv_type(self.in_dims[i], self.out_dims[i], kernel_size, padding=cur_padding, dilation=dilation, **kwargs))
        if i > 0 and shared_weights:
            convs[-1].weight = convs[0].weight
            convs[-1].bias = convs[0].bias
        dilation *= 2
    self.convs = nn.ModuleList(convs)
    self.shuffle_in_channels = shuffle_in_channels
    if self.shuffle_in_channels:
        in_channels_permute = list(range(in_dim))
        random.shuffle(in_channels_permute)
        self.register_buffer('in_channels_permute', torch.tensor(in_channels_permute))

class Identity(nn.Module):

    def __init__(self):
        super().__init__()

    def forward(self, x):
        return x

def __init__(self):
    super().__init__()

class ResnetBlock(nn.Module):

    def __init__(self, dim, padding_type, norm_layer, activation=nn.ReLU(True), use_dropout=False, conv_kind='default', dilation=1, in_dim=None, groups=1, second_dilation=None):
        super(ResnetBlock, self).__init__()
        self.in_dim = in_dim
        self.dim = dim
        if second_dilation is None:
            second_dilation = dilation
        self.conv_block = self.build_conv_block(dim, padding_type, norm_layer, activation, use_dropout, conv_kind=conv_kind, dilation=dilation, in_dim=in_dim, groups=groups, second_dilation=second_dilation)
        if self.in_dim is not None:
            self.input_conv = nn.Conv2d(in_dim, dim, 1)
        self.out_channnels = dim

    def build_conv_block(self, dim, padding_type, norm_layer, activation, use_dropout, conv_kind='default', dilation=1, in_dim=None, groups=1, second_dilation=1):
        conv_layer = get_conv_block_ctor(conv_kind)
        conv_block = []
        p = 0
        if padding_type == 'reflect':
            conv_block += [nn.ReflectionPad2d(dilation)]
        elif padding_type == 'replicate':
            conv_block += [nn.ReplicationPad2d(dilation)]
        elif padding_type == 'zero':
            p = dilation
        else:
            raise NotImplementedError('padding [%s] is not implemented' % padding_type)
        if in_dim is None:
            in_dim = dim
        conv_block += [conv_layer(in_dim, dim, kernel_size=3, padding=p, dilation=dilation), norm_layer(dim), activation]
        if use_dropout:
            conv_block += [nn.Dropout(0.5)]
        p = 0
        if padding_type == 'reflect':
            conv_block += [nn.ReflectionPad2d(second_dilation)]
        elif padding_type == 'replicate':
            conv_block += [nn.ReplicationPad2d(second_dilation)]
        elif padding_type == 'zero':
            p = second_dilation
        else:
            raise NotImplementedError('padding [%s] is not implemented' % padding_type)
        conv_block += [conv_layer(dim, dim, kernel_size=3, padding=p, dilation=second_dilation, groups=groups), norm_layer(dim)]
        return nn.Sequential(*conv_block)

    def forward(self, x):
        x_before = x
        if self.in_dim is not None:
            x = self.input_conv(x)
        out = x + self.conv_block(x_before)
        return out

def __init__(self, dim, padding_type, norm_layer, activation=nn.ReLU(True), use_dropout=False, conv_kind='default', dilation=1, in_dim=None, groups=1, second_dilation=None):
    super(ResnetBlock, self).__init__()
    self.in_dim = in_dim
    self.dim = dim
    if second_dilation is None:
        second_dilation = dilation
    self.conv_block = self.build_conv_block(dim, padding_type, norm_layer, activation, use_dropout, conv_kind=conv_kind, dilation=dilation, in_dim=in_dim, groups=groups, second_dilation=second_dilation)
    if self.in_dim is not None:
        self.input_conv = nn.Conv2d(in_dim, dim, 1)
    self.out_channnels = dim

def build_conv_block(self, dim, padding_type, norm_layer, activation, use_dropout, conv_kind='default', dilation=1, in_dim=None, groups=1, second_dilation=1):
    conv_layer = get_conv_block_ctor(conv_kind)
    conv_block = []
    p = 0
    if padding_type == 'reflect':
        conv_block += [nn.ReflectionPad2d(dilation)]
    elif padding_type == 'replicate':
        conv_block += [nn.ReplicationPad2d(dilation)]
    elif padding_type == 'zero':
        p = dilation
    else:
        raise NotImplementedError('padding [%s] is not implemented' % padding_type)
    if in_dim is None:
        in_dim = dim
    conv_block += [conv_layer(in_dim, dim, kernel_size=3, padding=p, dilation=dilation), norm_layer(dim), activation]
    if use_dropout:
        conv_block += [nn.Dropout(0.5)]
    p = 0
    if padding_type == 'reflect':
        conv_block += [nn.ReflectionPad2d(second_dilation)]
    elif padding_type == 'replicate':
        conv_block += [nn.ReplicationPad2d(second_dilation)]
    elif padding_type == 'zero':
        p = second_dilation
    else:
        raise NotImplementedError('padding [%s] is not implemented' % padding_type)
    conv_block += [conv_layer(dim, dim, kernel_size=3, padding=p, dilation=second_dilation, groups=groups), norm_layer(dim)]
    return nn.Sequential(*conv_block)

class ResnetBlock5x5(nn.Module):

    def __init__(self, dim, padding_type, norm_layer, activation=nn.ReLU(True), use_dropout=False, conv_kind='default', dilation=1, in_dim=None, groups=1, second_dilation=None):
        super(ResnetBlock5x5, self).__init__()
        self.in_dim = in_dim
        self.dim = dim
        if second_dilation is None:
            second_dilation = dilation
        self.conv_block = self.build_conv_block(dim, padding_type, norm_layer, activation, use_dropout, conv_kind=conv_kind, dilation=dilation, in_dim=in_dim, groups=groups, second_dilation=second_dilation)
        if self.in_dim is not None:
            self.input_conv = nn.Conv2d(in_dim, dim, 1)
        self.out_channnels = dim

    def build_conv_block(self, dim, padding_type, norm_layer, activation, use_dropout, conv_kind='default', dilation=1, in_dim=None, groups=1, second_dilation=1):
        conv_layer = get_conv_block_ctor(conv_kind)
        conv_block = []
        p = 0
        if padding_type == 'reflect':
            conv_block += [nn.ReflectionPad2d(dilation * 2)]
        elif padding_type == 'replicate':
            conv_block += [nn.ReplicationPad2d(dilation * 2)]
        elif padding_type == 'zero':
            p = dilation * 2
        else:
            raise NotImplementedError('padding [%s] is not implemented' % padding_type)
        if in_dim is None:
            in_dim = dim
        conv_block += [conv_layer(in_dim, dim, kernel_size=5, padding=p, dilation=dilation), norm_layer(dim), activation]
        if use_dropout:
            conv_block += [nn.Dropout(0.5)]
        p = 0
        if padding_type == 'reflect':
            conv_block += [nn.ReflectionPad2d(second_dilation * 2)]
        elif padding_type == 'replicate':
            conv_block += [nn.ReplicationPad2d(second_dilation * 2)]
        elif padding_type == 'zero':
            p = second_dilation * 2
        else:
            raise NotImplementedError('padding [%s] is not implemented' % padding_type)
        conv_block += [conv_layer(dim, dim, kernel_size=5, padding=p, dilation=second_dilation, groups=groups), norm_layer(dim)]
        return nn.Sequential(*conv_block)

    def forward(self, x):
        x_before = x
        if self.in_dim is not None:
            x = self.input_conv(x)
        out = x + self.conv_block(x_before)
        return out

def __init__(self, dim, padding_type, norm_layer, activation=nn.ReLU(True), use_dropout=False, conv_kind='default', dilation=1, in_dim=None, groups=1, second_dilation=None):
    super(ResnetBlock5x5, self).__init__()
    self.in_dim = in_dim
    self.dim = dim
    if second_dilation is None:
        second_dilation = dilation
    self.conv_block = self.build_conv_block(dim, padding_type, norm_layer, activation, use_dropout, conv_kind=conv_kind, dilation=dilation, in_dim=in_dim, groups=groups, second_dilation=second_dilation)
    if self.in_dim is not None:
        self.input_conv = nn.Conv2d(in_dim, dim, 1)
    self.out_channnels = dim

def build_conv_block(self, dim, padding_type, norm_layer, activation, use_dropout, conv_kind='default', dilation=1, in_dim=None, groups=1, second_dilation=1):
    conv_layer = get_conv_block_ctor(conv_kind)
    conv_block = []
    p = 0
    if padding_type == 'reflect':
        conv_block += [nn.ReflectionPad2d(dilation * 2)]
    elif padding_type == 'replicate':
        conv_block += [nn.ReplicationPad2d(dilation * 2)]
    elif padding_type == 'zero':
        p = dilation * 2
    else:
        raise NotImplementedError('padding [%s] is not implemented' % padding_type)
    if in_dim is None:
        in_dim = dim
    conv_block += [conv_layer(in_dim, dim, kernel_size=5, padding=p, dilation=dilation), norm_layer(dim), activation]
    if use_dropout:
        conv_block += [nn.Dropout(0.5)]
    p = 0
    if padding_type == 'reflect':
        conv_block += [nn.ReflectionPad2d(second_dilation * 2)]
    elif padding_type == 'replicate':
        conv_block += [nn.ReplicationPad2d(second_dilation * 2)]
    elif padding_type == 'zero':
        p = second_dilation * 2
    else:
        raise NotImplementedError('padding [%s] is not implemented' % padding_type)
    conv_block += [conv_layer(dim, dim, kernel_size=5, padding=p, dilation=second_dilation, groups=groups), norm_layer(dim)]
    return nn.Sequential(*conv_block)

class MultidilatedResnetBlock(nn.Module):

    def __init__(self, dim, padding_type, conv_layer, norm_layer, activation=nn.ReLU(True), use_dropout=False):
        super().__init__()
        self.conv_block = self.build_conv_block(dim, padding_type, conv_layer, norm_layer, activation, use_dropout)

    def build_conv_block(self, dim, padding_type, conv_layer, norm_layer, activation, use_dropout, dilation=1):
        conv_block = []
        conv_block += [conv_layer(dim, dim, kernel_size=3, padding_mode=padding_type), norm_layer(dim), activation]
        if use_dropout:
            conv_block += [nn.Dropout(0.5)]
        conv_block += [conv_layer(dim, dim, kernel_size=3, padding_mode=padding_type), norm_layer(dim)]
        return nn.Sequential(*conv_block)

    def forward(self, x):
        out = x + self.conv_block(x)
        return out

def __init__(self, dim, padding_type, conv_layer, norm_layer, activation=nn.ReLU(True), use_dropout=False):
    super().__init__()
    self.conv_block = self.build_conv_block(dim, padding_type, conv_layer, norm_layer, activation, use_dropout)

def build_conv_block(self, dim, padding_type, conv_layer, norm_layer, activation, use_dropout, dilation=1):
    conv_block = []
    conv_block += [conv_layer(dim, dim, kernel_size=3, padding_mode=padding_type), norm_layer(dim), activation]
    if use_dropout:
        conv_block += [nn.Dropout(0.5)]
    conv_block += [conv_layer(dim, dim, kernel_size=3, padding_mode=padding_type), norm_layer(dim)]
    return nn.Sequential(*conv_block)

class MultiDilatedGlobalGenerator(nn.Module):

    def __init__(self, input_nc, output_nc, ngf=64, n_downsampling=3, n_blocks=3, norm_layer=nn.BatchNorm2d, padding_type='reflect', conv_kind='default', deconv_kind='convtranspose', activation=nn.ReLU(True), up_norm_layer=nn.BatchNorm2d, affine=None, up_activation=nn.ReLU(True), add_out_act=True, max_features=1024, multidilation_kwargs={}, ffc_positions=None, ffc_kwargs={}):
        assert n_blocks >= 0
        super().__init__()
        conv_layer = get_conv_block_ctor(conv_kind)
        resnet_conv_layer = functools.partial(get_conv_block_ctor('multidilated'), **multidilation_kwargs)
        norm_layer = get_norm_layer(norm_layer)
        if affine is not None:
            norm_layer = partial(norm_layer, affine=affine)
        up_norm_layer = get_norm_layer(up_norm_layer)
        if affine is not None:
            up_norm_layer = partial(up_norm_layer, affine=affine)
        model = [nn.ReflectionPad2d(3), conv_layer(input_nc, ngf, kernel_size=7, padding=0), norm_layer(ngf), activation]
        identity = Identity()
        for i in range(n_downsampling):
            mult = 2 ** i
            model += [conv_layer(min(max_features, ngf * mult), min(max_features, ngf * mult * 2), kernel_size=3, stride=2, padding=1), norm_layer(min(max_features, ngf * mult * 2)), activation]
        mult = 2 ** n_downsampling
        feats_num_bottleneck = min(max_features, ngf * mult)
        for i in range(n_blocks):
            if ffc_positions is not None and i in ffc_positions:
                model += [FFCResnetBlock(feats_num_bottleneck, padding_type, norm_layer, activation_layer=nn.ReLU, inline=True, **ffc_kwargs)]
            model += [MultidilatedResnetBlock(feats_num_bottleneck, padding_type=padding_type, conv_layer=resnet_conv_layer, activation=activation, norm_layer=norm_layer)]
        for i in range(n_downsampling):
            mult = 2 ** (n_downsampling - i)
            model += deconv_factory(deconv_kind, ngf, mult, up_norm_layer, up_activation, max_features)
        model += [nn.ReflectionPad2d(3), nn.Conv2d(ngf, output_nc, kernel_size=7, padding=0)]
        if add_out_act:
            model.append(get_activation('tanh' if add_out_act is True else add_out_act))
        self.model = nn.Sequential(*model)

    def forward(self, input):
        return self.model(input)

def __init__(self, input_nc, output_nc, ngf=64, n_downsampling=3, n_blocks=3, norm_layer=nn.BatchNorm2d, padding_type='reflect', conv_kind='default', deconv_kind='convtranspose', activation=nn.ReLU(True), up_norm_layer=nn.BatchNorm2d, affine=None, up_activation=nn.ReLU(True), add_out_act=True, max_features=1024, multidilation_kwargs={}, ffc_positions=None, ffc_kwargs={}):
    assert n_blocks >= 0
    super().__init__()
    conv_layer = get_conv_block_ctor(conv_kind)
    resnet_conv_layer = functools.partial(get_conv_block_ctor('multidilated'), **multidilation_kwargs)
    norm_layer = get_norm_layer(norm_layer)
    if affine is not None:
        norm_layer = partial(norm_layer, affine=affine)
    up_norm_layer = get_norm_layer(up_norm_layer)
    if affine is not None:
        up_norm_layer = partial(up_norm_layer, affine=affine)
    model = [nn.ReflectionPad2d(3), conv_layer(input_nc, ngf, kernel_size=7, padding=0), norm_layer(ngf), activation]
    identity = Identity()
    for i in range(n_downsampling):
        mult = 2 ** i
        model += [conv_layer(min(max_features, ngf * mult), min(max_features, ngf * mult * 2), kernel_size=3, stride=2, padding=1), norm_layer(min(max_features, ngf * mult * 2)), activation]
    mult = 2 ** n_downsampling
    feats_num_bottleneck = min(max_features, ngf * mult)
    for i in range(n_blocks):
        if ffc_positions is not None and i in ffc_positions:
            model += [FFCResnetBlock(feats_num_bottleneck, padding_type, norm_layer, activation_layer=nn.ReLU, inline=True, **ffc_kwargs)]
        model += [MultidilatedResnetBlock(feats_num_bottleneck, padding_type=padding_type, conv_layer=resnet_conv_layer, activation=activation, norm_layer=norm_layer)]
    for i in range(n_downsampling):
        mult = 2 ** (n_downsampling - i)
        model += deconv_factory(deconv_kind, ngf, mult, up_norm_layer, up_activation, max_features)
    model += [nn.ReflectionPad2d(3), nn.Conv2d(ngf, output_nc, kernel_size=7, padding=0)]
    if add_out_act:
        model.append(get_activation('tanh' if add_out_act is True else add_out_act))
    self.model = nn.Sequential(*model)

class ConfigGlobalGenerator(nn.Module):

    def __init__(self, input_nc, output_nc, ngf=64, n_downsampling=3, n_blocks=3, norm_layer=nn.BatchNorm2d, padding_type='reflect', conv_kind='default', deconv_kind='convtranspose', activation=nn.ReLU(True), up_norm_layer=nn.BatchNorm2d, affine=None, up_activation=nn.ReLU(True), add_out_act=True, max_features=1024, manual_block_spec=[], resnet_block_kind='multidilatedresnetblock', resnet_conv_kind='multidilated', resnet_dilation=1, multidilation_kwargs={}):
        assert n_blocks >= 0
        super().__init__()
        conv_layer = get_conv_block_ctor(conv_kind)
        resnet_conv_layer = functools.partial(get_conv_block_ctor(resnet_conv_kind), **multidilation_kwargs)
        norm_layer = get_norm_layer(norm_layer)
        if affine is not None:
            norm_layer = partial(norm_layer, affine=affine)
        up_norm_layer = get_norm_layer(up_norm_layer)
        if affine is not None:
            up_norm_layer = partial(up_norm_layer, affine=affine)
        model = [nn.ReflectionPad2d(3), conv_layer(input_nc, ngf, kernel_size=7, padding=0), norm_layer(ngf), activation]
        identity = Identity()
        for i in range(n_downsampling):
            mult = 2 ** i
            model += [conv_layer(min(max_features, ngf * mult), min(max_features, ngf * mult * 2), kernel_size=3, stride=2, padding=1), norm_layer(min(max_features, ngf * mult * 2)), activation]
        mult = 2 ** n_downsampling
        feats_num_bottleneck = min(max_features, ngf * mult)
        if len(manual_block_spec) == 0:
            manual_block_spec = [DotDict(lambda: None, {'n_blocks': n_blocks, 'use_default': True})]
        for block_spec in manual_block_spec:

            def make_and_add_blocks(model, block_spec):
                block_spec = DotDict(lambda: None, block_spec)
                if not block_spec.use_default:
                    resnet_conv_layer = functools.partial(get_conv_block_ctor(block_spec.resnet_conv_kind), **block_spec.multidilation_kwargs)
                    resnet_conv_kind = block_spec.resnet_conv_kind
                    resnet_block_kind = block_spec.resnet_block_kind
                    if block_spec.resnet_dilation is not None:
                        resnet_dilation = block_spec.resnet_dilation
                for i in range(block_spec.n_blocks):
                    if resnet_block_kind == 'multidilatedresnetblock':
                        model += [MultidilatedResnetBlock(feats_num_bottleneck, padding_type=padding_type, conv_layer=resnet_conv_layer, activation=activation, norm_layer=norm_layer)]
                    if resnet_block_kind == 'resnetblock':
                        model += [ResnetBlock(ngf * mult, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=resnet_conv_kind)]
                    if resnet_block_kind == 'resnetblock5x5':
                        model += [ResnetBlock5x5(ngf * mult, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=resnet_conv_kind)]
                    if resnet_block_kind == 'resnetblockdwdil':
                        model += [ResnetBlock(ngf * mult, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=resnet_conv_kind, dilation=resnet_dilation, second_dilation=resnet_dilation)]
            make_and_add_blocks(model, block_spec)
        for i in range(n_downsampling):
            mult = 2 ** (n_downsampling - i)
            model += deconv_factory(deconv_kind, ngf, mult, up_norm_layer, up_activation, max_features)
        model += [nn.ReflectionPad2d(3), nn.Conv2d(ngf, output_nc, kernel_size=7, padding=0)]
        if add_out_act:
            model.append(get_activation('tanh' if add_out_act is True else add_out_act))
        self.model = nn.Sequential(*model)

    def forward(self, input):
        return self.model(input)

def __init__(self, input_nc, output_nc, ngf=64, n_downsampling=3, n_blocks=3, norm_layer=nn.BatchNorm2d, padding_type='reflect', conv_kind='default', deconv_kind='convtranspose', activation=nn.ReLU(True), up_norm_layer=nn.BatchNorm2d, affine=None, up_activation=nn.ReLU(True), add_out_act=True, max_features=1024, manual_block_spec=[], resnet_block_kind='multidilatedresnetblock', resnet_conv_kind='multidilated', resnet_dilation=1, multidilation_kwargs={}):
    assert n_blocks >= 0
    super().__init__()
    conv_layer = get_conv_block_ctor(conv_kind)
    resnet_conv_layer = functools.partial(get_conv_block_ctor(resnet_conv_kind), **multidilation_kwargs)
    norm_layer = get_norm_layer(norm_layer)
    if affine is not None:
        norm_layer = partial(norm_layer, affine=affine)
    up_norm_layer = get_norm_layer(up_norm_layer)
    if affine is not None:
        up_norm_layer = partial(up_norm_layer, affine=affine)
    model = [nn.ReflectionPad2d(3), conv_layer(input_nc, ngf, kernel_size=7, padding=0), norm_layer(ngf), activation]
    identity = Identity()
    for i in range(n_downsampling):
        mult = 2 ** i
        model += [conv_layer(min(max_features, ngf * mult), min(max_features, ngf * mult * 2), kernel_size=3, stride=2, padding=1), norm_layer(min(max_features, ngf * mult * 2)), activation]
    mult = 2 ** n_downsampling
    feats_num_bottleneck = min(max_features, ngf * mult)
    if len(manual_block_spec) == 0:
        manual_block_spec = [DotDict(lambda: None, {'n_blocks': n_blocks, 'use_default': True})]
    for block_spec in manual_block_spec:

        def make_and_add_blocks(model, block_spec):
            block_spec = DotDict(lambda: None, block_spec)
            if not block_spec.use_default:
                resnet_conv_layer = functools.partial(get_conv_block_ctor(block_spec.resnet_conv_kind), **block_spec.multidilation_kwargs)
                resnet_conv_kind = block_spec.resnet_conv_kind
                resnet_block_kind = block_spec.resnet_block_kind
                if block_spec.resnet_dilation is not None:
                    resnet_dilation = block_spec.resnet_dilation
            for i in range(block_spec.n_blocks):
                if resnet_block_kind == 'multidilatedresnetblock':
                    model += [MultidilatedResnetBlock(feats_num_bottleneck, padding_type=padding_type, conv_layer=resnet_conv_layer, activation=activation, norm_layer=norm_layer)]
                if resnet_block_kind == 'resnetblock':
                    model += [ResnetBlock(ngf * mult, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=resnet_conv_kind)]
                if resnet_block_kind == 'resnetblock5x5':
                    model += [ResnetBlock5x5(ngf * mult, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=resnet_conv_kind)]
                if resnet_block_kind == 'resnetblockdwdil':
                    model += [ResnetBlock(ngf * mult, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=resnet_conv_kind, dilation=resnet_dilation, second_dilation=resnet_dilation)]
        make_and_add_blocks(model, block_spec)
    for i in range(n_downsampling):
        mult = 2 ** (n_downsampling - i)
        model += deconv_factory(deconv_kind, ngf, mult, up_norm_layer, up_activation, max_features)
    model += [nn.ReflectionPad2d(3), nn.Conv2d(ngf, output_nc, kernel_size=7, padding=0)]
    if add_out_act:
        model.append(get_activation('tanh' if add_out_act is True else add_out_act))
    self.model = nn.Sequential(*model)

def make_and_add_blocks(model, block_spec):
    block_spec = DotDict(lambda: None, block_spec)
    if not block_spec.use_default:
        resnet_conv_layer = functools.partial(get_conv_block_ctor(block_spec.resnet_conv_kind), **block_spec.multidilation_kwargs)
        resnet_conv_kind = block_spec.resnet_conv_kind
        resnet_block_kind = block_spec.resnet_block_kind
        if block_spec.resnet_dilation is not None:
            resnet_dilation = block_spec.resnet_dilation
    for i in range(block_spec.n_blocks):
        if resnet_block_kind == 'multidilatedresnetblock':
            model += [MultidilatedResnetBlock(feats_num_bottleneck, padding_type=padding_type, conv_layer=resnet_conv_layer, activation=activation, norm_layer=norm_layer)]
        if resnet_block_kind == 'resnetblock':
            model += [ResnetBlock(ngf * mult, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=resnet_conv_kind)]
        if resnet_block_kind == 'resnetblock5x5':
            model += [ResnetBlock5x5(ngf * mult, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=resnet_conv_kind)]
        if resnet_block_kind == 'resnetblockdwdil':
            model += [ResnetBlock(ngf * mult, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=resnet_conv_kind, dilation=resnet_dilation, second_dilation=resnet_dilation)]

def make_dil_blocks(dilated_blocks_n, dilation_block_kind, dilated_block_kwargs):
    blocks = []
    for i in range(dilated_blocks_n):
        if dilation_block_kind == 'simple':
            blocks.append(ResnetBlock(**dilated_block_kwargs, dilation=2 ** (i + 1)))
        elif dilation_block_kind == 'multi':
            blocks.append(MultidilatedResnetBlock(**dilated_block_kwargs))
        else:
            raise ValueError(f'dilation_block_kind could not be "{dilation_block_kind}"')
    return blocks

class GlobalGenerator(nn.Module):

    def __init__(self, input_nc, output_nc, ngf=64, n_downsampling=3, n_blocks=9, norm_layer=nn.BatchNorm2d, padding_type='reflect', conv_kind='default', activation=nn.ReLU(True), up_norm_layer=nn.BatchNorm2d, affine=None, up_activation=nn.ReLU(True), dilated_blocks_n=0, dilated_blocks_n_start=0, dilated_blocks_n_middle=0, add_out_act=True, max_features=1024, is_resblock_depthwise=False, ffc_positions=None, ffc_kwargs={}, dilation=1, second_dilation=None, dilation_block_kind='simple', multidilation_kwargs={}):
        assert n_blocks >= 0
        super().__init__()
        conv_layer = get_conv_block_ctor(conv_kind)
        norm_layer = get_norm_layer(norm_layer)
        if affine is not None:
            norm_layer = partial(norm_layer, affine=affine)
        up_norm_layer = get_norm_layer(up_norm_layer)
        if affine is not None:
            up_norm_layer = partial(up_norm_layer, affine=affine)
        if ffc_positions is not None:
            ffc_positions = collections.Counter(ffc_positions)
        model = [nn.ReflectionPad2d(3), conv_layer(input_nc, ngf, kernel_size=7, padding=0), norm_layer(ngf), activation]
        identity = Identity()
        for i in range(n_downsampling):
            mult = 2 ** i
            model += [conv_layer(min(max_features, ngf * mult), min(max_features, ngf * mult * 2), kernel_size=3, stride=2, padding=1), norm_layer(min(max_features, ngf * mult * 2)), activation]
        mult = 2 ** n_downsampling
        feats_num_bottleneck = min(max_features, ngf * mult)
        dilated_block_kwargs = dict(dim=feats_num_bottleneck, padding_type=padding_type, activation=activation, norm_layer=norm_layer)
        if dilation_block_kind == 'simple':
            dilated_block_kwargs['conv_kind'] = conv_kind
        elif dilation_block_kind == 'multi':
            dilated_block_kwargs['conv_layer'] = functools.partial(get_conv_block_ctor('multidilated'), **multidilation_kwargs)
        if dilated_blocks_n_start is not None and dilated_blocks_n_start > 0:
            model += make_dil_blocks(dilated_blocks_n_start, dilation_block_kind, dilated_block_kwargs)
        for i in range(n_blocks):
            if i == n_blocks // 2 and dilated_blocks_n_middle is not None and (dilated_blocks_n_middle > 0):
                model += make_dil_blocks(dilated_blocks_n_middle, dilation_block_kind, dilated_block_kwargs)
            if ffc_positions is not None and i in ffc_positions:
                for _ in range(ffc_positions[i]):
                    model += [FFCResnetBlock(feats_num_bottleneck, padding_type, norm_layer, activation_layer=nn.ReLU, inline=True, **ffc_kwargs)]
            if is_resblock_depthwise:
                resblock_groups = feats_num_bottleneck
            else:
                resblock_groups = 1
            model += [ResnetBlock(feats_num_bottleneck, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=conv_kind, groups=resblock_groups, dilation=dilation, second_dilation=second_dilation)]
        if dilated_blocks_n is not None and dilated_blocks_n > 0:
            model += make_dil_blocks(dilated_blocks_n, dilation_block_kind, dilated_block_kwargs)
        for i in range(n_downsampling):
            mult = 2 ** (n_downsampling - i)
            model += [nn.ConvTranspose2d(min(max_features, ngf * mult), min(max_features, int(ngf * mult / 2)), kernel_size=3, stride=2, padding=1, output_padding=1), up_norm_layer(min(max_features, int(ngf * mult / 2))), up_activation]
        model += [nn.ReflectionPad2d(3), nn.Conv2d(ngf, output_nc, kernel_size=7, padding=0)]
        if add_out_act:
            model.append(get_activation('tanh' if add_out_act is True else add_out_act))
        self.model = nn.Sequential(*model)

    def forward(self, input):
        return self.model(input)

def __init__(self, input_nc, output_nc, ngf=64, n_downsampling=3, n_blocks=9, norm_layer=nn.BatchNorm2d, padding_type='reflect', conv_kind='default', activation=nn.ReLU(True), up_norm_layer=nn.BatchNorm2d, affine=None, up_activation=nn.ReLU(True), dilated_blocks_n=0, dilated_blocks_n_start=0, dilated_blocks_n_middle=0, add_out_act=True, max_features=1024, is_resblock_depthwise=False, ffc_positions=None, ffc_kwargs={}, dilation=1, second_dilation=None, dilation_block_kind='simple', multidilation_kwargs={}):
    assert n_blocks >= 0
    super().__init__()
    conv_layer = get_conv_block_ctor(conv_kind)
    norm_layer = get_norm_layer(norm_layer)
    if affine is not None:
        norm_layer = partial(norm_layer, affine=affine)
    up_norm_layer = get_norm_layer(up_norm_layer)
    if affine is not None:
        up_norm_layer = partial(up_norm_layer, affine=affine)
    if ffc_positions is not None:
        ffc_positions = collections.Counter(ffc_positions)
    model = [nn.ReflectionPad2d(3), conv_layer(input_nc, ngf, kernel_size=7, padding=0), norm_layer(ngf), activation]
    identity = Identity()
    for i in range(n_downsampling):
        mult = 2 ** i
        model += [conv_layer(min(max_features, ngf * mult), min(max_features, ngf * mult * 2), kernel_size=3, stride=2, padding=1), norm_layer(min(max_features, ngf * mult * 2)), activation]
    mult = 2 ** n_downsampling
    feats_num_bottleneck = min(max_features, ngf * mult)
    dilated_block_kwargs = dict(dim=feats_num_bottleneck, padding_type=padding_type, activation=activation, norm_layer=norm_layer)
    if dilation_block_kind == 'simple':
        dilated_block_kwargs['conv_kind'] = conv_kind
    elif dilation_block_kind == 'multi':
        dilated_block_kwargs['conv_layer'] = functools.partial(get_conv_block_ctor('multidilated'), **multidilation_kwargs)
    if dilated_blocks_n_start is not None and dilated_blocks_n_start > 0:
        model += make_dil_blocks(dilated_blocks_n_start, dilation_block_kind, dilated_block_kwargs)
    for i in range(n_blocks):
        if i == n_blocks // 2 and dilated_blocks_n_middle is not None and (dilated_blocks_n_middle > 0):
            model += make_dil_blocks(dilated_blocks_n_middle, dilation_block_kind, dilated_block_kwargs)
        if ffc_positions is not None and i in ffc_positions:
            for _ in range(ffc_positions[i]):
                model += [FFCResnetBlock(feats_num_bottleneck, padding_type, norm_layer, activation_layer=nn.ReLU, inline=True, **ffc_kwargs)]
        if is_resblock_depthwise:
            resblock_groups = feats_num_bottleneck
        else:
            resblock_groups = 1
        model += [ResnetBlock(feats_num_bottleneck, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=conv_kind, groups=resblock_groups, dilation=dilation, second_dilation=second_dilation)]
    if dilated_blocks_n is not None and dilated_blocks_n > 0:
        model += make_dil_blocks(dilated_blocks_n, dilation_block_kind, dilated_block_kwargs)
    for i in range(n_downsampling):
        mult = 2 ** (n_downsampling - i)
        model += [nn.ConvTranspose2d(min(max_features, ngf * mult), min(max_features, int(ngf * mult / 2)), kernel_size=3, stride=2, padding=1, output_padding=1), up_norm_layer(min(max_features, int(ngf * mult / 2))), up_activation]
    model += [nn.ReflectionPad2d(3), nn.Conv2d(ngf, output_nc, kernel_size=7, padding=0)]
    if add_out_act:
        model.append(get_activation('tanh' if add_out_act is True else add_out_act))
    self.model = nn.Sequential(*model)

class GlobalGeneratorGated(GlobalGenerator):

    def __init__(self, *args, **kwargs):
        real_kwargs = dict(conv_kind='gated_bn_relu', activation=nn.Identity(), norm_layer=nn.Identity)
        real_kwargs.update(kwargs)
        super().__init__(*args, **real_kwargs)

def __init__(self, *args, **kwargs):
    real_kwargs = dict(conv_kind='gated_bn_relu', activation=nn.Identity(), norm_layer=nn.Identity)
    real_kwargs.update(kwargs)
    super().__init__(*args, **real_kwargs)

class GlobalGeneratorFromSuperChannels(nn.Module):

    def __init__(self, input_nc, output_nc, n_downsampling, n_blocks, super_channels, norm_layer='bn', padding_type='reflect', add_out_act=True):
        super().__init__()
        self.n_downsampling = n_downsampling
        norm_layer = get_norm_layer(norm_layer)
        if type(norm_layer) == functools.partial:
            use_bias = norm_layer.func == nn.InstanceNorm2d
        else:
            use_bias = norm_layer == nn.InstanceNorm2d
        channels = self.convert_super_channels(super_channels)
        self.channels = channels
        model = [nn.ReflectionPad2d(3), nn.Conv2d(input_nc, channels[0], kernel_size=7, padding=0, bias=use_bias), norm_layer(channels[0]), nn.ReLU(True)]
        for i in range(n_downsampling):
            mult = 2 ** i
            model += [nn.Conv2d(channels[0 + i], channels[1 + i], kernel_size=3, stride=2, padding=1, bias=use_bias), norm_layer(channels[1 + i]), nn.ReLU(True)]
        mult = 2 ** n_downsampling
        n_blocks1 = n_blocks // 3
        n_blocks2 = n_blocks1
        n_blocks3 = n_blocks - n_blocks1 - n_blocks2
        for i in range(n_blocks1):
            c = n_downsampling
            dim = channels[c]
            model += [ResnetBlock(dim, padding_type=padding_type, norm_layer=norm_layer)]
        for i in range(n_blocks2):
            c = n_downsampling + 1
            dim = channels[c]
            kwargs = {}
            if i == 0:
                kwargs = {'in_dim': channels[c - 1]}
            model += [ResnetBlock(dim, padding_type=padding_type, norm_layer=norm_layer, **kwargs)]
        for i in range(n_blocks3):
            c = n_downsampling + 2
            dim = channels[c]
            kwargs = {}
            if i == 0:
                kwargs = {'in_dim': channels[c - 1]}
            model += [ResnetBlock(dim, padding_type=padding_type, norm_layer=norm_layer, **kwargs)]
        for i in range(n_downsampling):
            mult = 2 ** (n_downsampling - i)
            model += [nn.ConvTranspose2d(channels[n_downsampling + 3 + i], channels[n_downsampling + 3 + i + 1], kernel_size=3, stride=2, padding=1, output_padding=1, bias=use_bias), norm_layer(channels[n_downsampling + 3 + i + 1]), nn.ReLU(True)]
        model += [nn.ReflectionPad2d(3)]
        model += [nn.Conv2d(channels[2 * n_downsampling + 3], output_nc, kernel_size=7, padding=0)]
        if add_out_act:
            model.append(get_activation('tanh' if add_out_act is True else add_out_act))
        self.model = nn.Sequential(*model)

    def convert_super_channels(self, super_channels):
        n_downsampling = self.n_downsampling
        result = []
        cnt = 0
        if n_downsampling == 2:
            N1 = 10
        elif n_downsampling == 3:
            N1 = 13
        else:
            raise NotImplementedError
        for i in range(0, N1):
            if i in [1, 4, 7, 10]:
                channel = super_channels[cnt] * 2 ** cnt
                config = {'channel': channel}
                result.append(channel)
                logging.info(f'Downsample channels {result[-1]}')
                cnt += 1
        for i in range(3):
            for counter, j in enumerate(range(N1 + i * 3, N1 + 3 + i * 3)):
                if len(super_channels) == 6:
                    channel = super_channels[3] * 4
                else:
                    channel = super_channels[i + 3] * 4
                config = {'channel': channel}
                if counter == 0:
                    result.append(channel)
                    logging.info(f'Bottleneck channels {result[-1]}')
        cnt = 2
        for i in range(N1 + 9, N1 + 21):
            if i in [22, 25, 28]:
                cnt -= 1
                if len(super_channels) == 6:
                    channel = super_channels[5 - cnt] * 2 ** cnt
                else:
                    channel = super_channels[7 - cnt] * 2 ** cnt
                result.append(int(channel))
                logging.info(f'Upsample channels {result[-1]}')
        return result

    def forward(self, input):
        return self.model(input)

def __init__(self, input_nc, output_nc, n_downsampling, n_blocks, super_channels, norm_layer='bn', padding_type='reflect', add_out_act=True):
    super().__init__()
    self.n_downsampling = n_downsampling
    norm_layer = get_norm_layer(norm_layer)
    if type(norm_layer) == functools.partial:
        use_bias = norm_layer.func == nn.InstanceNorm2d
    else:
        use_bias = norm_layer == nn.InstanceNorm2d
    channels = self.convert_super_channels(super_channels)
    self.channels = channels
    model = [nn.ReflectionPad2d(3), nn.Conv2d(input_nc, channels[0], kernel_size=7, padding=0, bias=use_bias), norm_layer(channels[0]), nn.ReLU(True)]
    for i in range(n_downsampling):
        mult = 2 ** i
        model += [nn.Conv2d(channels[0 + i], channels[1 + i], kernel_size=3, stride=2, padding=1, bias=use_bias), norm_layer(channels[1 + i]), nn.ReLU(True)]
    mult = 2 ** n_downsampling
    n_blocks1 = n_blocks // 3
    n_blocks2 = n_blocks1
    n_blocks3 = n_blocks - n_blocks1 - n_blocks2
    for i in range(n_blocks1):
        c = n_downsampling
        dim = channels[c]
        model += [ResnetBlock(dim, padding_type=padding_type, norm_layer=norm_layer)]
    for i in range(n_blocks2):
        c = n_downsampling + 1
        dim = channels[c]
        kwargs = {}
        if i == 0:
            kwargs = {'in_dim': channels[c - 1]}
        model += [ResnetBlock(dim, padding_type=padding_type, norm_layer=norm_layer, **kwargs)]
    for i in range(n_blocks3):
        c = n_downsampling + 2
        dim = channels[c]
        kwargs = {}
        if i == 0:
            kwargs = {'in_dim': channels[c - 1]}
        model += [ResnetBlock(dim, padding_type=padding_type, norm_layer=norm_layer, **kwargs)]
    for i in range(n_downsampling):
        mult = 2 ** (n_downsampling - i)
        model += [nn.ConvTranspose2d(channels[n_downsampling + 3 + i], channels[n_downsampling + 3 + i + 1], kernel_size=3, stride=2, padding=1, output_padding=1, bias=use_bias), norm_layer(channels[n_downsampling + 3 + i + 1]), nn.ReLU(True)]
    model += [nn.ReflectionPad2d(3)]
    model += [nn.Conv2d(channels[2 * n_downsampling + 3], output_nc, kernel_size=7, padding=0)]
    if add_out_act:
        model.append(get_activation('tanh' if add_out_act is True else add_out_act))
    self.model = nn.Sequential(*model)

class NLayerDiscriminator(BaseDiscriminator):

    def __init__(self, input_nc, ndf=64, n_layers=3, norm_layer=nn.BatchNorm2d):
        super().__init__()
        self.n_layers = n_layers
        kw = 4
        padw = int(np.ceil((kw - 1.0) / 2))
        sequence = [[nn.Conv2d(input_nc, ndf, kernel_size=kw, stride=2, padding=padw), nn.LeakyReLU(0.2, True)]]
        nf = ndf
        for n in range(1, n_layers):
            nf_prev = nf
            nf = min(nf * 2, 512)
            cur_model = []
            cur_model += [nn.Conv2d(nf_prev, nf, kernel_size=kw, stride=2, padding=padw), norm_layer(nf), nn.LeakyReLU(0.2, True)]
            sequence.append(cur_model)
        nf_prev = nf
        nf = min(nf * 2, 512)
        cur_model = []
        cur_model += [nn.Conv2d(nf_prev, nf, kernel_size=kw, stride=1, padding=padw), norm_layer(nf), nn.LeakyReLU(0.2, True)]
        sequence.append(cur_model)
        sequence += [[nn.Conv2d(nf, 1, kernel_size=kw, stride=1, padding=padw)]]
        for n in range(len(sequence)):
            setattr(self, 'model' + str(n), nn.Sequential(*sequence[n]))

    def get_all_activations(self, x):
        res = [x]
        for n in range(self.n_layers + 2):
            model = getattr(self, 'model' + str(n))
            res.append(model(res[-1]))
        return res[1:]

    def forward(self, x):
        act = self.get_all_activations(x)
        return (act[-1], act[:-1])

def __init__(self, input_nc, ndf=64, n_layers=3, norm_layer=nn.BatchNorm2d):
    super().__init__()
    self.n_layers = n_layers
    kw = 4
    padw = int(np.ceil((kw - 1.0) / 2))
    sequence = [[nn.Conv2d(input_nc, ndf, kernel_size=kw, stride=2, padding=padw), nn.LeakyReLU(0.2, True)]]
    nf = ndf
    for n in range(1, n_layers):
        nf_prev = nf
        nf = min(nf * 2, 512)
        cur_model = []
        cur_model += [nn.Conv2d(nf_prev, nf, kernel_size=kw, stride=2, padding=padw), norm_layer(nf), nn.LeakyReLU(0.2, True)]
        sequence.append(cur_model)
    nf_prev = nf
    nf = min(nf * 2, 512)
    cur_model = []
    cur_model += [nn.Conv2d(nf_prev, nf, kernel_size=kw, stride=1, padding=padw), norm_layer(nf), nn.LeakyReLU(0.2, True)]
    sequence.append(cur_model)
    sequence += [[nn.Conv2d(nf, 1, kernel_size=kw, stride=1, padding=padw)]]
    for n in range(len(sequence)):
        setattr(self, 'model' + str(n), nn.Sequential(*sequence[n]))

class MultidilatedNLayerDiscriminator(BaseDiscriminator):

    def __init__(self, input_nc, ndf=64, n_layers=3, norm_layer=nn.BatchNorm2d, multidilation_kwargs={}):
        super().__init__()
        self.n_layers = n_layers
        kw = 4
        padw = int(np.ceil((kw - 1.0) / 2))
        sequence = [[nn.Conv2d(input_nc, ndf, kernel_size=kw, stride=2, padding=padw), nn.LeakyReLU(0.2, True)]]
        nf = ndf
        for n in range(1, n_layers):
            nf_prev = nf
            nf = min(nf * 2, 512)
            cur_model = []
            cur_model += [MultidilatedConv(nf_prev, nf, kernel_size=kw, stride=2, padding=[2, 3], **multidilation_kwargs), norm_layer(nf), nn.LeakyReLU(0.2, True)]
            sequence.append(cur_model)
        nf_prev = nf
        nf = min(nf * 2, 512)
        cur_model = []
        cur_model += [nn.Conv2d(nf_prev, nf, kernel_size=kw, stride=1, padding=padw), norm_layer(nf), nn.LeakyReLU(0.2, True)]
        sequence.append(cur_model)
        sequence += [[nn.Conv2d(nf, 1, kernel_size=kw, stride=1, padding=padw)]]
        for n in range(len(sequence)):
            setattr(self, 'model' + str(n), nn.Sequential(*sequence[n]))

    def get_all_activations(self, x):
        res = [x]
        for n in range(self.n_layers + 2):
            model = getattr(self, 'model' + str(n))
            res.append(model(res[-1]))
        return res[1:]

    def forward(self, x):
        act = self.get_all_activations(x)
        return (act[-1], act[:-1])

def __init__(self, input_nc, ndf=64, n_layers=3, norm_layer=nn.BatchNorm2d, multidilation_kwargs={}):
    super().__init__()
    self.n_layers = n_layers
    kw = 4
    padw = int(np.ceil((kw - 1.0) / 2))
    sequence = [[nn.Conv2d(input_nc, ndf, kernel_size=kw, stride=2, padding=padw), nn.LeakyReLU(0.2, True)]]
    nf = ndf
    for n in range(1, n_layers):
        nf_prev = nf
        nf = min(nf * 2, 512)
        cur_model = []
        cur_model += [MultidilatedConv(nf_prev, nf, kernel_size=kw, stride=2, padding=[2, 3], **multidilation_kwargs), norm_layer(nf), nn.LeakyReLU(0.2, True)]
        sequence.append(cur_model)
    nf_prev = nf
    nf = min(nf * 2, 512)
    cur_model = []
    cur_model += [nn.Conv2d(nf_prev, nf, kernel_size=kw, stride=1, padding=padw), norm_layer(nf), nn.LeakyReLU(0.2, True)]
    sequence.append(cur_model)
    sequence += [[nn.Conv2d(nf, 1, kernel_size=kw, stride=1, padding=padw)]]
    for n in range(len(sequence)):
        setattr(self, 'model' + str(n), nn.Sequential(*sequence[n]))

class NLayerDiscriminatorAsGen(NLayerDiscriminator):

    def forward(self, x):
        return super().forward(x)[0]

def forward(self, x):
    return super().forward(x)[0]

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

def __init__(self, impl, pad_coef=0.5, angle_init_range=80, train_angle=True):
    super().__init__()
    self.impl = impl
    self.angle = torch.rand(1) * angle_init_range
    if train_angle:
        self.angle = nn.Parameter(self.angle, requires_grad=True)
    self.pad_coef = pad_coef

class DepthWiseSeperableConv(nn.Module):

    def __init__(self, in_dim, out_dim, *args, **kwargs):
        super().__init__()
        if 'groups' in kwargs:
            del kwargs['groups']
        self.depthwise = nn.Conv2d(in_dim, in_dim, *args, groups=in_dim, **kwargs)
        self.pointwise = nn.Conv2d(in_dim, out_dim, kernel_size=1)

    def forward(self, x):
        out = self.depthwise(x)
        out = self.pointwise(out)
        return out

def __init__(self, in_dim, out_dim, *args, **kwargs):
    super().__init__()
    if 'groups' in kwargs:
        del kwargs['groups']
    self.depthwise = nn.Conv2d(in_dim, in_dim, *args, groups=in_dim, **kwargs)
    self.pointwise = nn.Conv2d(in_dim, out_dim, kernel_size=1)

class PairwiseScore(EvaluatorScore, ABC):

    def __init__(self):
        super().__init__()
        self.individual_values = None

    def get_value(self, groups=None, states=None):
        """
        :param groups:
        :return:
            total_results: dict of kind {'mean': score mean, 'std': score std}
            group_results: None, if groups is None;
                else dict {group_idx: {'mean': score mean among group, 'std': score std among group}}
        """
        individual_values = torch.cat(states, dim=-1).reshape(-1).cpu().numpy() if states is not None else self.individual_values
        total_results = {'mean': individual_values.mean(), 'std': individual_values.std()}
        if groups is None:
            return (total_results, None)
        group_results = dict()
        grouping = get_groupings(groups)
        for label, index in grouping.items():
            group_scores = individual_values[index]
            group_results[label] = {'mean': group_scores.mean(), 'std': group_scores.std()}
        return (total_results, group_results)

    def reset(self):
        self.individual_values = []

def __init__(self):
    super().__init__()
    self.individual_values = None

class SSIMScore(PairwiseScore):

    def __init__(self, window_size=11):
        super().__init__()
        self.score = SSIM(window_size=window_size, size_average=False).eval()
        self.reset()

    def forward(self, pred_batch, target_batch, mask=None):
        batch_values = self.score(pred_batch, target_batch)
        self.individual_values = np.hstack([self.individual_values, batch_values.detach().cpu().numpy()])
        return batch_values

def __init__(self, window_size=11):
    super().__init__()
    self.score = SSIM(window_size=window_size, size_average=False).eval()
    self.reset()

class LPIPSScore(PairwiseScore):

    def __init__(self, model='net-lin', net='vgg', model_path=None, use_gpu=True):
        super().__init__()
        self.score = PerceptualLoss(model=model, net=net, model_path=model_path, use_gpu=use_gpu, spatial=False).eval()
        self.reset()

    def forward(self, pred_batch, target_batch, mask=None):
        batch_values = self.score(pred_batch, target_batch).flatten()
        self.individual_values = np.hstack([self.individual_values, batch_values.detach().cpu().numpy()])
        return batch_values

def __init__(self, model='net-lin', net='vgg', model_path=None, use_gpu=True):
    super().__init__()
    self.score = PerceptualLoss(model=model, net=net, model_path=model_path, use_gpu=use_gpu, spatial=False).eval()
    self.reset()

class SegmentationAwareScore(EvaluatorScore):

    def __init__(self, weights_path):
        super().__init__()
        self.segm_network = SegmentationModule(weights_path=weights_path, use_default_normalization=True).eval()
        self.target_class_freq_by_image_total = []
        self.target_class_freq_by_image_mask = []
        self.pred_class_freq_by_image_mask = []

    def forward(self, pred_batch, target_batch, mask):
        pred_segm_flat = self.segm_network.predict(pred_batch)[0].view(pred_batch.shape[0], -1).long().detach().cpu().numpy()
        target_segm_flat = self.segm_network.predict(target_batch)[0].view(pred_batch.shape[0], -1).long().detach().cpu().numpy()
        mask_flat = (mask.view(mask.shape[0], -1) > 0.5).detach().cpu().numpy()
        batch_target_class_freq_total = []
        batch_target_class_freq_mask = []
        batch_pred_class_freq_mask = []
        for cur_pred_segm, cur_target_segm, cur_mask in zip(pred_segm_flat, target_segm_flat, mask_flat):
            cur_target_class_freq_total = np.bincount(cur_target_segm, minlength=NUM_CLASS)[None, ...]
            cur_target_class_freq_mask = np.bincount(cur_target_segm[cur_mask], minlength=NUM_CLASS)[None, ...]
            cur_pred_class_freq_mask = np.bincount(cur_pred_segm[cur_mask], minlength=NUM_CLASS)[None, ...]
            self.target_class_freq_by_image_total.append(cur_target_class_freq_total)
            self.target_class_freq_by_image_mask.append(cur_target_class_freq_mask)
            self.pred_class_freq_by_image_mask.append(cur_pred_class_freq_mask)
            batch_target_class_freq_total.append(cur_target_class_freq_total)
            batch_target_class_freq_mask.append(cur_target_class_freq_mask)
            batch_pred_class_freq_mask.append(cur_pred_class_freq_mask)
        batch_target_class_freq_total = np.concatenate(batch_target_class_freq_total, axis=0)
        batch_target_class_freq_mask = np.concatenate(batch_target_class_freq_mask, axis=0)
        batch_pred_class_freq_mask = np.concatenate(batch_pred_class_freq_mask, axis=0)
        return (batch_target_class_freq_total, batch_target_class_freq_mask, batch_pred_class_freq_mask)

    def reset(self):
        super().reset()
        self.target_class_freq_by_image_total = []
        self.target_class_freq_by_image_mask = []
        self.pred_class_freq_by_image_mask = []

def __init__(self, weights_path):
    super().__init__()
    self.segm_network = SegmentationModule(weights_path=weights_path, use_default_normalization=True).eval()
    self.target_class_freq_by_image_total = []
    self.target_class_freq_by_image_mask = []
    self.pred_class_freq_by_image_mask = []

class SegmentationAwarePairwiseScore(SegmentationAwareScore):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.individual_values = []
        self.segm_idx2name = get_segmentation_idx2name()

    def forward(self, pred_batch, target_batch, mask):
        cur_class_stats = super().forward(pred_batch, target_batch, mask)
        score_values = self.calc_score(pred_batch, target_batch, mask)
        self.individual_values.append(score_values)
        return cur_class_stats + (score_values,)

    @abstractmethod
    def calc_score(self, pred_batch, target_batch, mask):
        raise NotImplementedError()

    def get_value(self, groups=None, states=None):
        """
        :param groups:
        :return:
            total_results: dict of kind {'mean': score mean, 'std': score std}
            group_results: None, if groups is None;
                else dict {group_idx: {'mean': score mean among group, 'std': score std among group}}
        """
        if states is not None:
            target_class_freq_by_image_total, target_class_freq_by_image_mask, pred_class_freq_by_image_mask, individual_values = states
        else:
            target_class_freq_by_image_total = self.target_class_freq_by_image_total
            target_class_freq_by_image_mask = self.target_class_freq_by_image_mask
            pred_class_freq_by_image_mask = self.pred_class_freq_by_image_mask
            individual_values = self.individual_values
        target_class_freq_by_image_total = np.concatenate(target_class_freq_by_image_total, axis=0)
        target_class_freq_by_image_mask = np.concatenate(target_class_freq_by_image_mask, axis=0)
        pred_class_freq_by_image_mask = np.concatenate(pred_class_freq_by_image_mask, axis=0)
        individual_values = np.concatenate(individual_values, axis=0)
        total_results = {'mean': individual_values.mean(), 'std': individual_values.std(), **distribute_values_to_classes(target_class_freq_by_image_mask, individual_values, self.segm_idx2name)}
        if groups is None:
            return (total_results, None)
        group_results = dict()
        grouping = get_groupings(groups)
        for label, index in grouping.items():
            group_class_freq = target_class_freq_by_image_mask[index]
            group_scores = individual_values[index]
            group_results[label] = {'mean': group_scores.mean(), 'std': group_scores.std(), **distribute_values_to_classes(group_class_freq, group_scores, self.segm_idx2name)}
        return (total_results, group_results)

    def reset(self):
        super().reset()
        self.individual_values = []

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.individual_values = []
    self.segm_idx2name = get_segmentation_idx2name()

def forward(self, pred_batch, target_batch, mask):
    cur_class_stats = super().forward(pred_batch, target_batch, mask)
    score_values = self.calc_score(pred_batch, target_batch, mask)
    self.individual_values.append(score_values)
    return cur_class_stats + (score_values,)

class SegmentationAwareSSIM(SegmentationAwarePairwiseScore):

    def __init__(self, *args, window_size=11, **kwargs):
        super().__init__(*args, **kwargs)
        self.score_impl = SSIM(window_size=window_size, size_average=False).eval()

    def calc_score(self, pred_batch, target_batch, mask):
        return self.score_impl(pred_batch, target_batch).detach().cpu().numpy()

def __init__(self, *args, window_size=11, **kwargs):
    super().__init__(*args, **kwargs)
    self.score_impl = SSIM(window_size=window_size, size_average=False).eval()

class SegmentationAwareLPIPS(SegmentationAwarePairwiseScore):

    def __init__(self, *args, model='net-lin', net='vgg', model_path=None, use_gpu=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.score_impl = PerceptualLoss(model=model, net=net, model_path=model_path, use_gpu=use_gpu, spatial=False).eval()

    def calc_score(self, pred_batch, target_batch, mask):
        return self.score_impl(pred_batch, target_batch).flatten().detach().cpu().numpy()

def __init__(self, *args, model='net-lin', net='vgg', model_path=None, use_gpu=True, **kwargs):
    super().__init__(*args, **kwargs)
    self.score_impl = PerceptualLoss(model=model, net=net, model_path=model_path, use_gpu=use_gpu, spatial=False).eval()

class SSIM(torch.nn.Module):
    """SSIM. Modified from:
    https://github.com/Po-Hsun-Su/pytorch-ssim/blob/master/pytorch_ssim/__init__.py
    """

    def __init__(self, window_size=11, size_average=True):
        super().__init__()
        self.window_size = window_size
        self.size_average = size_average
        self.channel = 1
        self.register_buffer('window', self._create_window(window_size, self.channel))

    def forward(self, img1, img2):
        assert len(img1.shape) == 4
        channel = img1.size()[1]
        if channel == self.channel and self.window.data.type() == img1.data.type():
            window = self.window
        else:
            window = self._create_window(self.window_size, channel)
            window = window.type_as(img1)
            self.window = window
            self.channel = channel
        return self._ssim(img1, img2, window, self.window_size, channel, self.size_average)

    def _gaussian(self, window_size, sigma):
        gauss = torch.Tensor([np.exp(-(x - window_size // 2) ** 2 / float(2 * sigma ** 2)) for x in range(window_size)])
        return gauss / gauss.sum()

    def _create_window(self, window_size, channel):
        _1D_window = self._gaussian(window_size, 1.5).unsqueeze(1)
        _2D_window = _1D_window.mm(_1D_window.t()).float().unsqueeze(0).unsqueeze(0)
        return _2D_window.expand(channel, 1, window_size, window_size).contiguous()

    def _ssim(self, img1, img2, window, window_size, channel, size_average=True):
        mu1 = F.conv2d(img1, window, padding=window_size // 2, groups=channel)
        mu2 = F.conv2d(img2, window, padding=window_size // 2, groups=channel)
        mu1_sq = mu1.pow(2)
        mu2_sq = mu2.pow(2)
        mu1_mu2 = mu1 * mu2
        sigma1_sq = F.conv2d(img1 * img1, window, padding=window_size // 2, groups=channel) - mu1_sq
        sigma2_sq = F.conv2d(img2 * img2, window, padding=window_size // 2, groups=channel) - mu2_sq
        sigma12 = F.conv2d(img1 * img2, window, padding=window_size // 2, groups=channel) - mu1_mu2
        C1 = 0.01 ** 2
        C2 = 0.03 ** 2
        ssim_map = (2 * mu1_mu2 + C1) * (2 * sigma12 + C2) / ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
        if size_average:
            return ssim_map.mean()
        return ssim_map.mean(1).mean(1).mean(1)

    def _load_from_state_dict(self, state_dict, prefix, local_metadata, strict, missing_keys, unexpected_keys, error_msgs):
        return

def __init__(self, window_size=11, size_average=True):
    super().__init__()
    self.window_size = window_size
    self.size_average = size_average
    self.channel = 1
    self.register_buffer('window', self._create_window(window_size, self.channel))

class PerceptualLoss(torch.nn.Module):

    def __init__(self, model='net-lin', net='alex', colorspace='rgb', model_path=None, spatial=False, use_gpu=True):
        super(PerceptualLoss, self).__init__()
        self.use_gpu = use_gpu
        self.spatial = spatial
        self.model = DistModel()
        self.model.initialize(model=model, net=net, use_gpu=use_gpu, colorspace=colorspace, model_path=model_path, spatial=self.spatial)

    def forward(self, pred, target, normalize=True):
        """
        Pred and target are Variables.
        If normalize is True, assumes the images are between [0,1] and then scales them between [-1,+1]
        If normalize is False, assumes the images are already between [-1,+1]
        Inputs pred and target are Nx3xHxW
        Output pytorch Variable N long
        """
        if normalize:
            target = 2 * target - 1
            pred = 2 * pred - 1
        return self.model(target, pred)

def __init__(self, model='net-lin', net='alex', colorspace='rgb', model_path=None, spatial=False, use_gpu=True):
    super(PerceptualLoss, self).__init__()
    self.use_gpu = use_gpu
    self.spatial = spatial
    self.model = DistModel()
    self.model.initialize(model=model, net=net, use_gpu=use_gpu, colorspace=colorspace, model_path=model_path, spatial=self.spatial)

class BaseModel(torch.nn.Module):

    def __init__(self):
        super().__init__()

    def name(self):
        return 'BaseModel'

    def initialize(self, use_gpu=True):
        self.use_gpu = use_gpu

    def forward(self):
        pass

    def get_image_paths(self):
        pass

    def optimize_parameters(self):
        pass

    def get_current_visuals(self):
        return self.input

    def get_current_errors(self):
        return {}

    def save(self, label):
        pass

    def save_network(self, network, path, network_label, epoch_label):
        save_filename = '%s_net_%s.pth' % (epoch_label, network_label)
        save_path = os.path.join(path, save_filename)
        torch.save(network.state_dict(), save_path)

    def load_network(self, network, network_label, epoch_label):
        save_filename = '%s_net_%s.pth' % (epoch_label, network_label)
        save_path = os.path.join(self.save_dir, save_filename)
        print('Loading network from %s' % save_path)
        network.load_state_dict(torch.load(save_path, map_location='cpu'))

    def update_learning_rate():
        pass

    def get_image_paths(self):
        return self.image_paths

    def save_done(self, flag=False):
        np.save(os.path.join(self.save_dir, 'done_flag'), flag)
        np.savetxt(os.path.join(self.save_dir, 'done_flag'), [flag], fmt='%i')

def __init__(self):
    super().__init__()

def upsample(in_tens, out_H=64):
    in_H = in_tens.shape[2]
    scale_factor = 1.0 * out_H / in_H
    return nn.Upsample(scale_factor=scale_factor, mode='bilinear', align_corners=False)(in_tens)

class PNetLin(nn.Module):

    def __init__(self, pnet_type='vgg', pnet_rand=False, pnet_tune=False, use_dropout=True, spatial=False, version='0.1', lpips=True):
        super(PNetLin, self).__init__()
        self.pnet_type = pnet_type
        self.pnet_tune = pnet_tune
        self.pnet_rand = pnet_rand
        self.spatial = spatial
        self.lpips = lpips
        self.version = version
        self.scaling_layer = ScalingLayer()
        if self.pnet_type in ['vgg', 'vgg16']:
            net_type = vgg16
            self.chns = [64, 128, 256, 512, 512]
        elif self.pnet_type == 'alex':
            net_type = alexnet
            self.chns = [64, 192, 384, 256, 256]
        elif self.pnet_type == 'squeeze':
            net_type = squeezenet
            self.chns = [64, 128, 256, 384, 384, 512, 512]
        self.L = len(self.chns)
        self.net = net_type(pretrained=not self.pnet_rand, requires_grad=self.pnet_tune)
        if lpips:
            self.lin0 = NetLinLayer(self.chns[0], use_dropout=use_dropout)
            self.lin1 = NetLinLayer(self.chns[1], use_dropout=use_dropout)
            self.lin2 = NetLinLayer(self.chns[2], use_dropout=use_dropout)
            self.lin3 = NetLinLayer(self.chns[3], use_dropout=use_dropout)
            self.lin4 = NetLinLayer(self.chns[4], use_dropout=use_dropout)
            self.lins = [self.lin0, self.lin1, self.lin2, self.lin3, self.lin4]
            if self.pnet_type == 'squeeze':
                self.lin5 = NetLinLayer(self.chns[5], use_dropout=use_dropout)
                self.lin6 = NetLinLayer(self.chns[6], use_dropout=use_dropout)
                self.lins += [self.lin5, self.lin6]

    def forward(self, in0, in1, retPerLayer=False):
        in0_input, in1_input = (self.scaling_layer(in0), self.scaling_layer(in1)) if self.version == '0.1' else (in0, in1)
        outs0, outs1 = (self.net(in0_input), self.net(in1_input))
        feats0, feats1, diffs = ({}, {}, {})
        for kk in range(self.L):
            feats0[kk], feats1[kk] = (normalize_tensor(outs0[kk]), normalize_tensor(outs1[kk]))
            diffs[kk] = (feats0[kk] - feats1[kk]) ** 2
        if self.lpips:
            if self.spatial:
                res = [upsample(self.lins[kk].model(diffs[kk]), out_H=in0.shape[2]) for kk in range(self.L)]
            else:
                res = [spatial_average(self.lins[kk].model(diffs[kk]), keepdim=True) for kk in range(self.L)]
        elif self.spatial:
            res = [upsample(diffs[kk].sum(dim=1, keepdim=True), out_H=in0.shape[2]) for kk in range(self.L)]
        else:
            res = [spatial_average(diffs[kk].sum(dim=1, keepdim=True), keepdim=True) for kk in range(self.L)]
        val = res[0]
        for l in range(1, self.L):
            val += res[l]
        if retPerLayer:
            return (val, res)
        else:
            return val

def __init__(self, pnet_type='vgg', pnet_rand=False, pnet_tune=False, use_dropout=True, spatial=False, version='0.1', lpips=True):
    super(PNetLin, self).__init__()
    self.pnet_type = pnet_type
    self.pnet_tune = pnet_tune
    self.pnet_rand = pnet_rand
    self.spatial = spatial
    self.lpips = lpips
    self.version = version
    self.scaling_layer = ScalingLayer()
    if self.pnet_type in ['vgg', 'vgg16']:
        net_type = vgg16
        self.chns = [64, 128, 256, 512, 512]
    elif self.pnet_type == 'alex':
        net_type = alexnet
        self.chns = [64, 192, 384, 256, 256]
    elif self.pnet_type == 'squeeze':
        net_type = squeezenet
        self.chns = [64, 128, 256, 384, 384, 512, 512]
    self.L = len(self.chns)
    self.net = net_type(pretrained=not self.pnet_rand, requires_grad=self.pnet_tune)
    if lpips:
        self.lin0 = NetLinLayer(self.chns[0], use_dropout=use_dropout)
        self.lin1 = NetLinLayer(self.chns[1], use_dropout=use_dropout)
        self.lin2 = NetLinLayer(self.chns[2], use_dropout=use_dropout)
        self.lin3 = NetLinLayer(self.chns[3], use_dropout=use_dropout)
        self.lin4 = NetLinLayer(self.chns[4], use_dropout=use_dropout)
        self.lins = [self.lin0, self.lin1, self.lin2, self.lin3, self.lin4]
        if self.pnet_type == 'squeeze':
            self.lin5 = NetLinLayer(self.chns[5], use_dropout=use_dropout)
            self.lin6 = NetLinLayer(self.chns[6], use_dropout=use_dropout)
            self.lins += [self.lin5, self.lin6]

class ScalingLayer(nn.Module):

    def __init__(self):
        super(ScalingLayer, self).__init__()
        self.register_buffer('shift', torch.Tensor([-0.03, -0.088, -0.188])[None, :, None, None])
        self.register_buffer('scale', torch.Tensor([0.458, 0.448, 0.45])[None, :, None, None])

    def forward(self, inp):
        return (inp - self.shift) / self.scale

def __init__(self):
    super(ScalingLayer, self).__init__()
    self.register_buffer('shift', torch.Tensor([-0.03, -0.088, -0.188])[None, :, None, None])
    self.register_buffer('scale', torch.Tensor([0.458, 0.448, 0.45])[None, :, None, None])

class NetLinLayer(nn.Module):
    """ A single linear layer which does a 1x1 conv """

    def __init__(self, chn_in, chn_out=1, use_dropout=False):
        super(NetLinLayer, self).__init__()
        layers = [nn.Dropout()] if use_dropout else []
        layers += [nn.Conv2d(chn_in, chn_out, 1, stride=1, padding=0, bias=False)]
        self.model = nn.Sequential(*layers)

def __init__(self, chn_in, chn_out=1, use_dropout=False):
    super(NetLinLayer, self).__init__()
    layers = [nn.Dropout()] if use_dropout else []
    layers += [nn.Conv2d(chn_in, chn_out, 1, stride=1, padding=0, bias=False)]
    self.model = nn.Sequential(*layers)

class Dist2LogitLayer(nn.Module):
    """ takes 2 distances, puts through fc layers, spits out value between [0,1] (if use_sigmoid is True) """

    def __init__(self, chn_mid=32, use_sigmoid=True):
        super(Dist2LogitLayer, self).__init__()
        layers = [nn.Conv2d(5, chn_mid, 1, stride=1, padding=0, bias=True)]
        layers += [nn.LeakyReLU(0.2, True)]
        layers += [nn.Conv2d(chn_mid, chn_mid, 1, stride=1, padding=0, bias=True)]
        layers += [nn.LeakyReLU(0.2, True)]
        layers += [nn.Conv2d(chn_mid, 1, 1, stride=1, padding=0, bias=True)]
        if use_sigmoid:
            layers += [nn.Sigmoid()]
        self.model = nn.Sequential(*layers)

    def forward(self, d0, d1, eps=0.1):
        return self.model(torch.cat((d0, d1, d0 - d1, d0 / (d1 + eps), d1 / (d0 + eps)), dim=1))

def __init__(self, chn_mid=32, use_sigmoid=True):
    super(Dist2LogitLayer, self).__init__()
    layers = [nn.Conv2d(5, chn_mid, 1, stride=1, padding=0, bias=True)]
    layers += [nn.LeakyReLU(0.2, True)]
    layers += [nn.Conv2d(chn_mid, chn_mid, 1, stride=1, padding=0, bias=True)]
    layers += [nn.LeakyReLU(0.2, True)]
    layers += [nn.Conv2d(chn_mid, 1, 1, stride=1, padding=0, bias=True)]
    if use_sigmoid:
        layers += [nn.Sigmoid()]
    self.model = nn.Sequential(*layers)

class BCERankingLoss(nn.Module):

    def __init__(self, chn_mid=32):
        super(BCERankingLoss, self).__init__()
        self.net = Dist2LogitLayer(chn_mid=chn_mid)
        self.loss = torch.nn.BCELoss()

    def forward(self, d0, d1, judge):
        per = (judge + 1.0) / 2.0
        self.logit = self.net(d0, d1)
        return self.loss(self.logit, per)

def __init__(self, chn_mid=32):
    super(BCERankingLoss, self).__init__()
    self.net = Dist2LogitLayer(chn_mid=chn_mid)
    self.loss = torch.nn.BCELoss()

class FakeNet(nn.Module):

    def __init__(self, use_gpu=True, colorspace='Lab'):
        super(FakeNet, self).__init__()
        self.use_gpu = use_gpu
        self.colorspace = colorspace

def __init__(self, use_gpu=True, colorspace='Lab'):
    super(FakeNet, self).__init__()
    self.use_gpu = use_gpu
    self.colorspace = colorspace

class squeezenet(torch.nn.Module):

    def __init__(self, requires_grad=False, pretrained=True):
        super(squeezenet, self).__init__()
        pretrained_features = tv.squeezenet1_1(pretrained=pretrained).features
        self.slice1 = torch.nn.Sequential()
        self.slice2 = torch.nn.Sequential()
        self.slice3 = torch.nn.Sequential()
        self.slice4 = torch.nn.Sequential()
        self.slice5 = torch.nn.Sequential()
        self.slice6 = torch.nn.Sequential()
        self.slice7 = torch.nn.Sequential()
        self.N_slices = 7
        for x in range(2):
            self.slice1.add_module(str(x), pretrained_features[x])
        for x in range(2, 5):
            self.slice2.add_module(str(x), pretrained_features[x])
        for x in range(5, 8):
            self.slice3.add_module(str(x), pretrained_features[x])
        for x in range(8, 10):
            self.slice4.add_module(str(x), pretrained_features[x])
        for x in range(10, 11):
            self.slice5.add_module(str(x), pretrained_features[x])
        for x in range(11, 12):
            self.slice6.add_module(str(x), pretrained_features[x])
        for x in range(12, 13):
            self.slice7.add_module(str(x), pretrained_features[x])
        if not requires_grad:
            for param in self.parameters():
                param.requires_grad = False

    def forward(self, X):
        h = self.slice1(X)
        h_relu1 = h
        h = self.slice2(h)
        h_relu2 = h
        h = self.slice3(h)
        h_relu3 = h
        h = self.slice4(h)
        h_relu4 = h
        h = self.slice5(h)
        h_relu5 = h
        h = self.slice6(h)
        h_relu6 = h
        h = self.slice7(h)
        h_relu7 = h
        vgg_outputs = namedtuple('SqueezeOutputs', ['relu1', 'relu2', 'relu3', 'relu4', 'relu5', 'relu6', 'relu7'])
        out = vgg_outputs(h_relu1, h_relu2, h_relu3, h_relu4, h_relu5, h_relu6, h_relu7)
        return out

def __init__(self, requires_grad=False, pretrained=True):
    super(squeezenet, self).__init__()
    pretrained_features = tv.squeezenet1_1(pretrained=pretrained).features
    self.slice1 = torch.nn.Sequential()
    self.slice2 = torch.nn.Sequential()
    self.slice3 = torch.nn.Sequential()
    self.slice4 = torch.nn.Sequential()
    self.slice5 = torch.nn.Sequential()
    self.slice6 = torch.nn.Sequential()
    self.slice7 = torch.nn.Sequential()
    self.N_slices = 7
    for x in range(2):
        self.slice1.add_module(str(x), pretrained_features[x])
    for x in range(2, 5):
        self.slice2.add_module(str(x), pretrained_features[x])
    for x in range(5, 8):
        self.slice3.add_module(str(x), pretrained_features[x])
    for x in range(8, 10):
        self.slice4.add_module(str(x), pretrained_features[x])
    for x in range(10, 11):
        self.slice5.add_module(str(x), pretrained_features[x])
    for x in range(11, 12):
        self.slice6.add_module(str(x), pretrained_features[x])
    for x in range(12, 13):
        self.slice7.add_module(str(x), pretrained_features[x])
    if not requires_grad:
        for param in self.parameters():
            param.requires_grad = False

class alexnet(torch.nn.Module):

    def __init__(self, requires_grad=False, pretrained=True):
        super(alexnet, self).__init__()
        alexnet_pretrained_features = tv.alexnet(pretrained=pretrained).features
        self.slice1 = torch.nn.Sequential()
        self.slice2 = torch.nn.Sequential()
        self.slice3 = torch.nn.Sequential()
        self.slice4 = torch.nn.Sequential()
        self.slice5 = torch.nn.Sequential()
        self.N_slices = 5
        for x in range(2):
            self.slice1.add_module(str(x), alexnet_pretrained_features[x])
        for x in range(2, 5):
            self.slice2.add_module(str(x), alexnet_pretrained_features[x])
        for x in range(5, 8):
            self.slice3.add_module(str(x), alexnet_pretrained_features[x])
        for x in range(8, 10):
            self.slice4.add_module(str(x), alexnet_pretrained_features[x])
        for x in range(10, 12):
            self.slice5.add_module(str(x), alexnet_pretrained_features[x])
        if not requires_grad:
            for param in self.parameters():
                param.requires_grad = False

    def forward(self, X):
        h = self.slice1(X)
        h_relu1 = h
        h = self.slice2(h)
        h_relu2 = h
        h = self.slice3(h)
        h_relu3 = h
        h = self.slice4(h)
        h_relu4 = h
        h = self.slice5(h)
        h_relu5 = h
        alexnet_outputs = namedtuple('AlexnetOutputs', ['relu1', 'relu2', 'relu3', 'relu4', 'relu5'])
        out = alexnet_outputs(h_relu1, h_relu2, h_relu3, h_relu4, h_relu5)
        return out

def __init__(self, requires_grad=False, pretrained=True):
    super(alexnet, self).__init__()
    alexnet_pretrained_features = tv.alexnet(pretrained=pretrained).features
    self.slice1 = torch.nn.Sequential()
    self.slice2 = torch.nn.Sequential()
    self.slice3 = torch.nn.Sequential()
    self.slice4 = torch.nn.Sequential()
    self.slice5 = torch.nn.Sequential()
    self.N_slices = 5
    for x in range(2):
        self.slice1.add_module(str(x), alexnet_pretrained_features[x])
    for x in range(2, 5):
        self.slice2.add_module(str(x), alexnet_pretrained_features[x])
    for x in range(5, 8):
        self.slice3.add_module(str(x), alexnet_pretrained_features[x])
    for x in range(8, 10):
        self.slice4.add_module(str(x), alexnet_pretrained_features[x])
    for x in range(10, 12):
        self.slice5.add_module(str(x), alexnet_pretrained_features[x])
    if not requires_grad:
        for param in self.parameters():
            param.requires_grad = False

class vgg16(torch.nn.Module):

    def __init__(self, requires_grad=False, pretrained=True):
        super(vgg16, self).__init__()
        vgg_pretrained_features = tv.vgg16(pretrained=pretrained).features
        self.slice1 = torch.nn.Sequential()
        self.slice2 = torch.nn.Sequential()
        self.slice3 = torch.nn.Sequential()
        self.slice4 = torch.nn.Sequential()
        self.slice5 = torch.nn.Sequential()
        self.N_slices = 5
        for x in range(4):
            self.slice1.add_module(str(x), vgg_pretrained_features[x])
        for x in range(4, 9):
            self.slice2.add_module(str(x), vgg_pretrained_features[x])
        for x in range(9, 16):
            self.slice3.add_module(str(x), vgg_pretrained_features[x])
        for x in range(16, 23):
            self.slice4.add_module(str(x), vgg_pretrained_features[x])
        for x in range(23, 30):
            self.slice5.add_module(str(x), vgg_pretrained_features[x])
        if not requires_grad:
            for param in self.parameters():
                param.requires_grad = False

    def forward(self, X):
        h = self.slice1(X)
        h_relu1_2 = h
        h = self.slice2(h)
        h_relu2_2 = h
        h = self.slice3(h)
        h_relu3_3 = h
        h = self.slice4(h)
        h_relu4_3 = h
        h = self.slice5(h)
        h_relu5_3 = h
        vgg_outputs = namedtuple('VggOutputs', ['relu1_2', 'relu2_2', 'relu3_3', 'relu4_3', 'relu5_3'])
        out = vgg_outputs(h_relu1_2, h_relu2_2, h_relu3_3, h_relu4_3, h_relu5_3)
        return out

def __init__(self, requires_grad=False, pretrained=True):
    super(vgg16, self).__init__()
    vgg_pretrained_features = tv.vgg16(pretrained=pretrained).features
    self.slice1 = torch.nn.Sequential()
    self.slice2 = torch.nn.Sequential()
    self.slice3 = torch.nn.Sequential()
    self.slice4 = torch.nn.Sequential()
    self.slice5 = torch.nn.Sequential()
    self.N_slices = 5
    for x in range(4):
        self.slice1.add_module(str(x), vgg_pretrained_features[x])
    for x in range(4, 9):
        self.slice2.add_module(str(x), vgg_pretrained_features[x])
    for x in range(9, 16):
        self.slice3.add_module(str(x), vgg_pretrained_features[x])
    for x in range(16, 23):
        self.slice4.add_module(str(x), vgg_pretrained_features[x])
    for x in range(23, 30):
        self.slice5.add_module(str(x), vgg_pretrained_features[x])
    if not requires_grad:
        for param in self.parameters():
            param.requires_grad = False

class resnet(torch.nn.Module):

    def __init__(self, requires_grad=False, pretrained=True, num=18):
        super(resnet, self).__init__()
        if num == 18:
            self.net = tv.resnet18(pretrained=pretrained)
        elif num == 34:
            self.net = tv.resnet34(pretrained=pretrained)
        elif num == 50:
            self.net = tv.resnet50(pretrained=pretrained)
        elif num == 101:
            self.net = tv.resnet101(pretrained=pretrained)
        elif num == 152:
            self.net = tv.resnet152(pretrained=pretrained)
        self.N_slices = 5
        self.conv1 = self.net.conv1
        self.bn1 = self.net.bn1
        self.relu = self.net.relu
        self.maxpool = self.net.maxpool
        self.layer1 = self.net.layer1
        self.layer2 = self.net.layer2
        self.layer3 = self.net.layer3
        self.layer4 = self.net.layer4

    def forward(self, X):
        h = self.conv1(X)
        h = self.bn1(h)
        h = self.relu(h)
        h_relu1 = h
        h = self.maxpool(h)
        h = self.layer1(h)
        h_conv2 = h
        h = self.layer2(h)
        h_conv3 = h
        h = self.layer3(h)
        h_conv4 = h
        h = self.layer4(h)
        h_conv5 = h
        outputs = namedtuple('Outputs', ['relu1', 'conv2', 'conv3', 'conv4', 'conv5'])
        out = outputs(h_relu1, h_conv2, h_conv3, h_conv4, h_conv5)
        return out

def __init__(self, requires_grad=False, pretrained=True, num=18):
    super(resnet, self).__init__()
    if num == 18:
        self.net = tv.resnet18(pretrained=pretrained)
    elif num == 34:
        self.net = tv.resnet34(pretrained=pretrained)
    elif num == 50:
        self.net = tv.resnet50(pretrained=pretrained)
    elif num == 101:
        self.net = tv.resnet101(pretrained=pretrained)
    elif num == 152:
        self.net = tv.resnet152(pretrained=pretrained)
    self.N_slices = 5
    self.conv1 = self.net.conv1
    self.bn1 = self.net.bn1
    self.relu = self.net.relu
    self.maxpool = self.net.maxpool
    self.layer1 = self.net.layer1
    self.layer2 = self.net.layer2
    self.layer3 = self.net.layer3
    self.layer4 = self.net.layer4

class InceptionV3(nn.Module):
    """Pretrained InceptionV3 network returning feature maps"""
    DEFAULT_BLOCK_INDEX = 3
    BLOCK_INDEX_BY_DIM = {64: 0, 192: 1, 768: 2, 2048: 3}

    def __init__(self, output_blocks=[DEFAULT_BLOCK_INDEX], resize_input=True, normalize_input=True, requires_grad=False, use_fid_inception=True):
        """Build pretrained InceptionV3

        Parameters
        ----------
        output_blocks : list of int
            Indices of blocks to return features of. Possible values are:
                - 0: corresponds to output of first max pooling
                - 1: corresponds to output of second max pooling
                - 2: corresponds to output which is fed to aux classifier
                - 3: corresponds to output of final average pooling
        resize_input : bool
            If true, bilinearly resizes input to width and height 299 before
            feeding input to model. As the network without fully connected
            layers is fully convolutional, it should be able to handle inputs
            of arbitrary size, so resizing might not be strictly needed
        normalize_input : bool
            If true, scales the input from range (0, 1) to the range the
            pretrained Inception network expects, namely (-1, 1)
        requires_grad : bool
            If true, parameters of the model require gradients. Possibly useful
            for finetuning the network
        use_fid_inception : bool
            If true, uses the pretrained Inception model used in Tensorflow's
            FID implementation. If false, uses the pretrained Inception model
            available in torchvision. The FID Inception model has different
            weights and a slightly different structure from torchvision's
            Inception model. If you want to compute FID scores, you are
            strongly advised to set this parameter to true to get comparable
            results.
        """
        super(InceptionV3, self).__init__()
        self.resize_input = resize_input
        self.normalize_input = normalize_input
        self.output_blocks = sorted(output_blocks)
        self.last_needed_block = max(output_blocks)
        assert self.last_needed_block <= 3, 'Last possible output block index is 3'
        self.blocks = nn.ModuleList()
        if use_fid_inception:
            inception = fid_inception_v3()
        else:
            inception = models.inception_v3(pretrained=True)
        block0 = [inception.Conv2d_1a_3x3, inception.Conv2d_2a_3x3, inception.Conv2d_2b_3x3, nn.MaxPool2d(kernel_size=3, stride=2)]
        self.blocks.append(nn.Sequential(*block0))
        if self.last_needed_block >= 1:
            block1 = [inception.Conv2d_3b_1x1, inception.Conv2d_4a_3x3, nn.MaxPool2d(kernel_size=3, stride=2)]
            self.blocks.append(nn.Sequential(*block1))
        if self.last_needed_block >= 2:
            block2 = [inception.Mixed_5b, inception.Mixed_5c, inception.Mixed_5d, inception.Mixed_6a, inception.Mixed_6b, inception.Mixed_6c, inception.Mixed_6d, inception.Mixed_6e]
            self.blocks.append(nn.Sequential(*block2))
        if self.last_needed_block >= 3:
            block3 = [inception.Mixed_7a, inception.Mixed_7b, inception.Mixed_7c, nn.AdaptiveAvgPool2d(output_size=(1, 1))]
            self.blocks.append(nn.Sequential(*block3))
        for param in self.parameters():
            param.requires_grad = requires_grad

    def forward(self, inp):
        """Get Inception feature maps

        Parameters
        ----------
        inp : torch.autograd.Variable
            Input tensor of shape Bx3xHxW. Values are expected to be in
            range (0, 1)

        Returns
        -------
        List of torch.autograd.Variable, corresponding to the selected output
        block, sorted ascending by index
        """
        outp = []
        x = inp
        if self.resize_input:
            x = F.interpolate(x, size=(299, 299), mode='bilinear', align_corners=False)
        if self.normalize_input:
            x = 2 * x - 1
        for idx, block in enumerate(self.blocks):
            x = block(x)
            if idx in self.output_blocks:
                outp.append(x)
            if idx == self.last_needed_block:
                break
        return outp

def __init__(self, output_blocks=[DEFAULT_BLOCK_INDEX], resize_input=True, normalize_input=True, requires_grad=False, use_fid_inception=True):
    """Build pretrained InceptionV3

        Parameters
        ----------
        output_blocks : list of int
            Indices of blocks to return features of. Possible values are:
                - 0: corresponds to output of first max pooling
                - 1: corresponds to output of second max pooling
                - 2: corresponds to output which is fed to aux classifier
                - 3: corresponds to output of final average pooling
        resize_input : bool
            If true, bilinearly resizes input to width and height 299 before
            feeding input to model. As the network without fully connected
            layers is fully convolutional, it should be able to handle inputs
            of arbitrary size, so resizing might not be strictly needed
        normalize_input : bool
            If true, scales the input from range (0, 1) to the range the
            pretrained Inception network expects, namely (-1, 1)
        requires_grad : bool
            If true, parameters of the model require gradients. Possibly useful
            for finetuning the network
        use_fid_inception : bool
            If true, uses the pretrained Inception model used in Tensorflow's
            FID implementation. If false, uses the pretrained Inception model
            available in torchvision. The FID Inception model has different
            weights and a slightly different structure from torchvision's
            Inception model. If you want to compute FID scores, you are
            strongly advised to set this parameter to true to get comparable
            results.
        """
    super(InceptionV3, self).__init__()
    self.resize_input = resize_input
    self.normalize_input = normalize_input
    self.output_blocks = sorted(output_blocks)
    self.last_needed_block = max(output_blocks)
    assert self.last_needed_block <= 3, 'Last possible output block index is 3'
    self.blocks = nn.ModuleList()
    if use_fid_inception:
        inception = fid_inception_v3()
    else:
        inception = models.inception_v3(pretrained=True)
    block0 = [inception.Conv2d_1a_3x3, inception.Conv2d_2a_3x3, inception.Conv2d_2b_3x3, nn.MaxPool2d(kernel_size=3, stride=2)]
    self.blocks.append(nn.Sequential(*block0))
    if self.last_needed_block >= 1:
        block1 = [inception.Conv2d_3b_1x1, inception.Conv2d_4a_3x3, nn.MaxPool2d(kernel_size=3, stride=2)]
        self.blocks.append(nn.Sequential(*block1))
    if self.last_needed_block >= 2:
        block2 = [inception.Mixed_5b, inception.Mixed_5c, inception.Mixed_5d, inception.Mixed_6a, inception.Mixed_6b, inception.Mixed_6c, inception.Mixed_6d, inception.Mixed_6e]
        self.blocks.append(nn.Sequential(*block2))
    if self.last_needed_block >= 3:
        block3 = [inception.Mixed_7a, inception.Mixed_7b, inception.Mixed_7c, nn.AdaptiveAvgPool2d(output_size=(1, 1))]
        self.blocks.append(nn.Sequential(*block3))
    for param in self.parameters():
        param.requires_grad = requires_grad

class FIDInceptionA(models.inception.InceptionA):
    """InceptionA block patched for FID computation"""

    def __init__(self, in_channels, pool_features):
        super(FIDInceptionA, self).__init__(in_channels, pool_features)

    def forward(self, x):
        branch1x1 = self.branch1x1(x)
        branch5x5 = self.branch5x5_1(x)
        branch5x5 = self.branch5x5_2(branch5x5)
        branch3x3dbl = self.branch3x3dbl_1(x)
        branch3x3dbl = self.branch3x3dbl_2(branch3x3dbl)
        branch3x3dbl = self.branch3x3dbl_3(branch3x3dbl)
        branch_pool = F.avg_pool2d(x, kernel_size=3, stride=1, padding=1, count_include_pad=False)
        branch_pool = self.branch_pool(branch_pool)
        outputs = [branch1x1, branch5x5, branch3x3dbl, branch_pool]
        return torch.cat(outputs, 1)

def __init__(self, in_channels, pool_features):
    super(FIDInceptionA, self).__init__(in_channels, pool_features)

class FIDInceptionC(models.inception.InceptionC):
    """InceptionC block patched for FID computation"""

    def __init__(self, in_channels, channels_7x7):
        super(FIDInceptionC, self).__init__(in_channels, channels_7x7)

    def forward(self, x):
        branch1x1 = self.branch1x1(x)
        branch7x7 = self.branch7x7_1(x)
        branch7x7 = self.branch7x7_2(branch7x7)
        branch7x7 = self.branch7x7_3(branch7x7)
        branch7x7dbl = self.branch7x7dbl_1(x)
        branch7x7dbl = self.branch7x7dbl_2(branch7x7dbl)
        branch7x7dbl = self.branch7x7dbl_3(branch7x7dbl)
        branch7x7dbl = self.branch7x7dbl_4(branch7x7dbl)
        branch7x7dbl = self.branch7x7dbl_5(branch7x7dbl)
        branch_pool = F.avg_pool2d(x, kernel_size=3, stride=1, padding=1, count_include_pad=False)
        branch_pool = self.branch_pool(branch_pool)
        outputs = [branch1x1, branch7x7, branch7x7dbl, branch_pool]
        return torch.cat(outputs, 1)

def __init__(self, in_channels, channels_7x7):
    super(FIDInceptionC, self).__init__(in_channels, channels_7x7)

class FIDInceptionE_1(models.inception.InceptionE):
    """First InceptionE block patched for FID computation"""

    def __init__(self, in_channels):
        super(FIDInceptionE_1, self).__init__(in_channels)

    def forward(self, x):
        branch1x1 = self.branch1x1(x)
        branch3x3 = self.branch3x3_1(x)
        branch3x3 = [self.branch3x3_2a(branch3x3), self.branch3x3_2b(branch3x3)]
        branch3x3 = torch.cat(branch3x3, 1)
        branch3x3dbl = self.branch3x3dbl_1(x)
        branch3x3dbl = self.branch3x3dbl_2(branch3x3dbl)
        branch3x3dbl = [self.branch3x3dbl_3a(branch3x3dbl), self.branch3x3dbl_3b(branch3x3dbl)]
        branch3x3dbl = torch.cat(branch3x3dbl, 1)
        branch_pool = F.avg_pool2d(x, kernel_size=3, stride=1, padding=1, count_include_pad=False)
        branch_pool = self.branch_pool(branch_pool)
        outputs = [branch1x1, branch3x3, branch3x3dbl, branch_pool]
        return torch.cat(outputs, 1)

def __init__(self, in_channels):
    super(FIDInceptionE_1, self).__init__(in_channels)

class FIDInceptionE_2(models.inception.InceptionE):
    """Second InceptionE block patched for FID computation"""

    def __init__(self, in_channels):
        super(FIDInceptionE_2, self).__init__(in_channels)

    def forward(self, x):
        branch1x1 = self.branch1x1(x)
        branch3x3 = self.branch3x3_1(x)
        branch3x3 = [self.branch3x3_2a(branch3x3), self.branch3x3_2b(branch3x3)]
        branch3x3 = torch.cat(branch3x3, 1)
        branch3x3dbl = self.branch3x3dbl_1(x)
        branch3x3dbl = self.branch3x3dbl_2(branch3x3dbl)
        branch3x3dbl = [self.branch3x3dbl_3a(branch3x3dbl), self.branch3x3dbl_3b(branch3x3dbl)]
        branch3x3dbl = torch.cat(branch3x3dbl, 1)
        branch_pool = F.max_pool2d(x, kernel_size=3, stride=1, padding=1)
        branch_pool = self.branch_pool(branch_pool)
        outputs = [branch1x1, branch3x3, branch3x3dbl, branch_pool]
        return torch.cat(outputs, 1)

def __init__(self, in_channels):
    super(FIDInceptionE_2, self).__init__(in_channels)

def conv_bn(inp, oup, stride):
    return nn.Sequential(nn.Conv2d(inp, oup, 3, stride, 1, bias=False), BatchNorm2d(oup), nn.ReLU6(inplace=True))

def conv_1x1_bn(inp, oup):
    return nn.Sequential(nn.Conv2d(inp, oup, 1, 1, 0, bias=False), BatchNorm2d(oup), nn.ReLU6(inplace=True))

class InvertedResidual(nn.Module):

    def __init__(self, inp, oup, stride, expand_ratio):
        super(InvertedResidual, self).__init__()
        self.stride = stride
        assert stride in [1, 2]
        hidden_dim = round(inp * expand_ratio)
        self.use_res_connect = self.stride == 1 and inp == oup
        if expand_ratio == 1:
            self.conv = nn.Sequential(nn.Conv2d(hidden_dim, hidden_dim, 3, stride, 1, groups=hidden_dim, bias=False), BatchNorm2d(hidden_dim), nn.ReLU6(inplace=True), nn.Conv2d(hidden_dim, oup, 1, 1, 0, bias=False), BatchNorm2d(oup))
        else:
            self.conv = nn.Sequential(nn.Conv2d(inp, hidden_dim, 1, 1, 0, bias=False), BatchNorm2d(hidden_dim), nn.ReLU6(inplace=True), nn.Conv2d(hidden_dim, hidden_dim, 3, stride, 1, groups=hidden_dim, bias=False), BatchNorm2d(hidden_dim), nn.ReLU6(inplace=True), nn.Conv2d(hidden_dim, oup, 1, 1, 0, bias=False), BatchNorm2d(oup))

    def forward(self, x):
        if self.use_res_connect:
            return x + self.conv(x)
        else:
            return self.conv(x)

def __init__(self, inp, oup, stride, expand_ratio):
    super(InvertedResidual, self).__init__()
    self.stride = stride
    assert stride in [1, 2]
    hidden_dim = round(inp * expand_ratio)
    self.use_res_connect = self.stride == 1 and inp == oup
    if expand_ratio == 1:
        self.conv = nn.Sequential(nn.Conv2d(hidden_dim, hidden_dim, 3, stride, 1, groups=hidden_dim, bias=False), BatchNorm2d(hidden_dim), nn.ReLU6(inplace=True), nn.Conv2d(hidden_dim, oup, 1, 1, 0, bias=False), BatchNorm2d(oup))
    else:
        self.conv = nn.Sequential(nn.Conv2d(inp, hidden_dim, 1, 1, 0, bias=False), BatchNorm2d(hidden_dim), nn.ReLU6(inplace=True), nn.Conv2d(hidden_dim, hidden_dim, 3, stride, 1, groups=hidden_dim, bias=False), BatchNorm2d(hidden_dim), nn.ReLU6(inplace=True), nn.Conv2d(hidden_dim, oup, 1, 1, 0, bias=False), BatchNorm2d(oup))

class MobileNetV2(nn.Module):

    def __init__(self, n_class=1000, input_size=224, width_mult=1.0):
        super(MobileNetV2, self).__init__()
        block = InvertedResidual
        input_channel = 32
        last_channel = 1280
        interverted_residual_setting = [[1, 16, 1, 1], [6, 24, 2, 2], [6, 32, 3, 2], [6, 64, 4, 2], [6, 96, 3, 1], [6, 160, 3, 2], [6, 320, 1, 1]]
        assert input_size % 32 == 0
        input_channel = int(input_channel * width_mult)
        self.last_channel = int(last_channel * width_mult) if width_mult > 1.0 else last_channel
        self.features = [conv_bn(3, input_channel, 2)]
        for t, c, n, s in interverted_residual_setting:
            output_channel = int(c * width_mult)
            for i in range(n):
                if i == 0:
                    self.features.append(block(input_channel, output_channel, s, expand_ratio=t))
                else:
                    self.features.append(block(input_channel, output_channel, 1, expand_ratio=t))
                input_channel = output_channel
        self.features.append(conv_1x1_bn(input_channel, self.last_channel))
        self.features = nn.Sequential(*self.features)
        self.classifier = nn.Sequential(nn.Dropout(0.2), nn.Linear(self.last_channel, n_class))
        self._initialize_weights()

    def forward(self, x):
        x = self.features(x)
        x = x.mean(3).mean(2)
        x = self.classifier(x)
        return x

    def _initialize_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                n = m.kernel_size[0] * m.kernel_size[1] * m.out_channels
                m.weight.data.normal_(0, math.sqrt(2.0 / n))
                if m.bias is not None:
                    m.bias.data.zero_()
            elif isinstance(m, BatchNorm2d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()
            elif isinstance(m, nn.Linear):
                n = m.weight.size(1)
                m.weight.data.normal_(0, 0.01)
                m.bias.data.zero_()

def __init__(self, n_class=1000, input_size=224, width_mult=1.0):
    super(MobileNetV2, self).__init__()
    block = InvertedResidual
    input_channel = 32
    last_channel = 1280
    interverted_residual_setting = [[1, 16, 1, 1], [6, 24, 2, 2], [6, 32, 3, 2], [6, 64, 4, 2], [6, 96, 3, 1], [6, 160, 3, 2], [6, 320, 1, 1]]
    assert input_size % 32 == 0
    input_channel = int(input_channel * width_mult)
    self.last_channel = int(last_channel * width_mult) if width_mult > 1.0 else last_channel
    self.features = [conv_bn(3, input_channel, 2)]
    for t, c, n, s in interverted_residual_setting:
        output_channel = int(c * width_mult)
        for i in range(n):
            if i == 0:
                self.features.append(block(input_channel, output_channel, s, expand_ratio=t))
            else:
                self.features.append(block(input_channel, output_channel, 1, expand_ratio=t))
            input_channel = output_channel
    self.features.append(conv_1x1_bn(input_channel, self.last_channel))
    self.features = nn.Sequential(*self.features)
    self.classifier = nn.Sequential(nn.Dropout(0.2), nn.Linear(self.last_channel, n_class))
    self._initialize_weights()

def _initialize_weights(self):
    for m in self.modules():
        if isinstance(m, nn.Conv2d):
            n = m.kernel_size[0] * m.kernel_size[1] * m.out_channels
            m.weight.data.normal_(0, math.sqrt(2.0 / n))
            if m.bias is not None:
                m.bias.data.zero_()
        elif isinstance(m, BatchNorm2d):
            m.weight.data.fill_(1)
            m.bias.data.zero_()
        elif isinstance(m, nn.Linear):
            n = m.weight.size(1)
            m.weight.data.normal_(0, 0.01)
            m.bias.data.zero_()

def conv3x3_bn_relu(in_planes, out_planes, stride=1):
    return nn.Sequential(nn.Conv2d(in_planes, out_planes, kernel_size=3, stride=stride, padding=1, bias=False), BatchNorm2d(out_planes), nn.ReLU(inplace=True))

class SegmentationModule(nn.Module):

    def __init__(self, weights_path, num_classes=150, arch_encoder='resnet50dilated', drop_last_conv=False, net_enc=None, net_dec=None, encode=None, use_default_normalization=False, return_feature_maps=False, return_feature_maps_level=3, return_feature_maps_only=True, **kwargs):
        super().__init__()
        self.weights_path = weights_path
        self.drop_last_conv = drop_last_conv
        self.arch_encoder = arch_encoder
        if self.arch_encoder == 'resnet50dilated':
            self.arch_decoder = 'ppm_deepsup'
            self.fc_dim = 2048
        elif self.arch_encoder == 'mobilenetv2dilated':
            self.arch_decoder = 'c1_deepsup'
            self.fc_dim = 320
        else:
            raise NotImplementedError(f'No such arch_encoder={self.arch_encoder}')
        model_builder_kwargs = dict(arch_encoder=self.arch_encoder, arch_decoder=self.arch_decoder, fc_dim=self.fc_dim, drop_last_conv=drop_last_conv, weights_path=self.weights_path)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.encoder = ModelBuilder.get_encoder(**model_builder_kwargs) if net_enc is None else net_enc
        self.decoder = ModelBuilder.get_decoder(**model_builder_kwargs) if net_dec is None else net_dec
        self.use_default_normalization = use_default_normalization
        self.default_normalization = NormalizeTensor(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        self.encode = encode
        self.return_feature_maps = return_feature_maps
        assert 0 <= return_feature_maps_level <= 3
        self.return_feature_maps_level = return_feature_maps_level

    def normalize_input(self, tensor):
        if tensor.min() < 0 or tensor.max() > 1:
            raise ValueError('Tensor should be 0..1 before using normalize_input')
        return self.default_normalization(tensor)

    @property
    def feature_maps_channels(self):
        return 256 * 2 ** self.return_feature_maps_level

    def forward(self, img_data, segSize=None):
        if segSize is None:
            raise NotImplementedError('Please pass segSize param. By default: (300, 300)')
        fmaps = self.encoder(img_data, return_feature_maps=True)
        pred = self.decoder(fmaps, segSize=segSize)
        if self.return_feature_maps:
            return (pred, fmaps)
        return pred

    def multi_mask_from_multiclass(self, pred, classes):

        def isin(ar1, ar2):
            return (ar1[..., None] == ar2).any(-1).float()
        return isin(pred, torch.LongTensor(classes).to(self.device))

    @staticmethod
    def multi_mask_from_multiclass_probs(scores, classes):
        res = None
        for c in classes:
            if res is None:
                res = scores[:, c]
            else:
                res += scores[:, c]
        return res

    def predict(self, tensor, imgSizes=(-1,), segSize=None):
        """Entry-point for segmentation. Use this methods instead of forward
        Arguments:
            tensor {torch.Tensor} -- BCHW
        Keyword Arguments:
            imgSizes {tuple or list} -- imgSizes for segmentation input.
                default: (300, 450)
                original implementation: (300, 375, 450, 525, 600)

        """
        if segSize is None:
            segSize = tensor.shape[-2:]
        segSize = (tensor.shape[2], tensor.shape[3])
        with torch.no_grad():
            if self.use_default_normalization:
                tensor = self.normalize_input(tensor)
            scores = torch.zeros(1, NUM_CLASS, segSize[0], segSize[1]).to(self.device)
            features = torch.zeros(1, self.feature_maps_channels, segSize[0], segSize[1]).to(self.device)
            result = []
            for img_size in imgSizes:
                if img_size != -1:
                    img_data = F.interpolate(tensor.clone(), size=img_size)
                else:
                    img_data = tensor.clone()
                if self.return_feature_maps:
                    pred_current, fmaps = self.forward(img_data, segSize=segSize)
                else:
                    pred_current = self.forward(img_data, segSize=segSize)
                result.append(pred_current)
                scores = scores + pred_current / len(imgSizes)
                if self.return_feature_maps:
                    features = features + F.interpolate(fmaps[self.return_feature_maps_level], size=segSize) / len(imgSizes)
            _, pred = torch.max(scores, dim=1)
            if self.return_feature_maps:
                return features
            return (pred, result)

    def get_edges(self, t):
        edge = torch.cuda.ByteTensor(t.size()).zero_()
        edge[:, :, :, 1:] = edge[:, :, :, 1:] | (t[:, :, :, 1:] != t[:, :, :, :-1])
        edge[:, :, :, :-1] = edge[:, :, :, :-1] | (t[:, :, :, 1:] != t[:, :, :, :-1])
        edge[:, :, 1:, :] = edge[:, :, 1:, :] | (t[:, :, 1:, :] != t[:, :, :-1, :])
        edge[:, :, :-1, :] = edge[:, :, :-1, :] | (t[:, :, 1:, :] != t[:, :, :-1, :])
        if True:
            return edge.half()
        return edge.float()

def __init__(self, weights_path, num_classes=150, arch_encoder='resnet50dilated', drop_last_conv=False, net_enc=None, net_dec=None, encode=None, use_default_normalization=False, return_feature_maps=False, return_feature_maps_level=3, return_feature_maps_only=True, **kwargs):
    super().__init__()
    self.weights_path = weights_path
    self.drop_last_conv = drop_last_conv
    self.arch_encoder = arch_encoder
    if self.arch_encoder == 'resnet50dilated':
        self.arch_decoder = 'ppm_deepsup'
        self.fc_dim = 2048
    elif self.arch_encoder == 'mobilenetv2dilated':
        self.arch_decoder = 'c1_deepsup'
        self.fc_dim = 320
    else:
        raise NotImplementedError(f'No such arch_encoder={self.arch_encoder}')
    model_builder_kwargs = dict(arch_encoder=self.arch_encoder, arch_decoder=self.arch_decoder, fc_dim=self.fc_dim, drop_last_conv=drop_last_conv, weights_path=self.weights_path)
    self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    self.encoder = ModelBuilder.get_encoder(**model_builder_kwargs) if net_enc is None else net_enc
    self.decoder = ModelBuilder.get_decoder(**model_builder_kwargs) if net_dec is None else net_dec
    self.use_default_normalization = use_default_normalization
    self.default_normalization = NormalizeTensor(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    self.encode = encode
    self.return_feature_maps = return_feature_maps
    assert 0 <= return_feature_maps_level <= 3
    self.return_feature_maps_level = return_feature_maps_level

class PPMDeepsup(nn.Module):

    def __init__(self, num_class=NUM_CLASS, fc_dim=4096, use_softmax=False, pool_scales=(1, 2, 3, 6), drop_last_conv=False):
        super().__init__()
        self.use_softmax = use_softmax
        self.drop_last_conv = drop_last_conv
        self.ppm = []
        for scale in pool_scales:
            self.ppm.append(nn.Sequential(nn.AdaptiveAvgPool2d(scale), nn.Conv2d(fc_dim, 512, kernel_size=1, bias=False), BatchNorm2d(512), nn.ReLU(inplace=True)))
        self.ppm = nn.ModuleList(self.ppm)
        self.cbr_deepsup = conv3x3_bn_relu(fc_dim // 2, fc_dim // 4, 1)
        self.conv_last = nn.Sequential(nn.Conv2d(fc_dim + len(pool_scales) * 512, 512, kernel_size=3, padding=1, bias=False), BatchNorm2d(512), nn.ReLU(inplace=True), nn.Dropout2d(0.1), nn.Conv2d(512, num_class, kernel_size=1))
        self.conv_last_deepsup = nn.Conv2d(fc_dim // 4, num_class, 1, 1, 0)
        self.dropout_deepsup = nn.Dropout2d(0.1)

    def forward(self, conv_out, segSize=None):
        conv5 = conv_out[-1]
        input_size = conv5.size()
        ppm_out = [conv5]
        for pool_scale in self.ppm:
            ppm_out.append(nn.functional.interpolate(pool_scale(conv5), (input_size[2], input_size[3]), mode='bilinear', align_corners=False))
        ppm_out = torch.cat(ppm_out, 1)
        if self.drop_last_conv:
            return ppm_out
        else:
            x = self.conv_last(ppm_out)
            if self.use_softmax:
                x = nn.functional.interpolate(x, size=segSize, mode='bilinear', align_corners=False)
                x = nn.functional.softmax(x, dim=1)
                return x
            conv4 = conv_out[-2]
            _ = self.cbr_deepsup(conv4)
            _ = self.dropout_deepsup(_)
            _ = self.conv_last_deepsup(_)
            x = nn.functional.log_softmax(x, dim=1)
            _ = nn.functional.log_softmax(_, dim=1)
            return (x, _)

def __init__(self, num_class=NUM_CLASS, fc_dim=4096, use_softmax=False, pool_scales=(1, 2, 3, 6), drop_last_conv=False):
    super().__init__()
    self.use_softmax = use_softmax
    self.drop_last_conv = drop_last_conv
    self.ppm = []
    for scale in pool_scales:
        self.ppm.append(nn.Sequential(nn.AdaptiveAvgPool2d(scale), nn.Conv2d(fc_dim, 512, kernel_size=1, bias=False), BatchNorm2d(512), nn.ReLU(inplace=True)))
    self.ppm = nn.ModuleList(self.ppm)
    self.cbr_deepsup = conv3x3_bn_relu(fc_dim // 2, fc_dim // 4, 1)
    self.conv_last = nn.Sequential(nn.Conv2d(fc_dim + len(pool_scales) * 512, 512, kernel_size=3, padding=1, bias=False), BatchNorm2d(512), nn.ReLU(inplace=True), nn.Dropout2d(0.1), nn.Conv2d(512, num_class, kernel_size=1))
    self.conv_last_deepsup = nn.Conv2d(fc_dim // 4, num_class, 1, 1, 0)
    self.dropout_deepsup = nn.Dropout2d(0.1)

class Resnet(nn.Module):

    def __init__(self, orig_resnet):
        super(Resnet, self).__init__()
        self.conv1 = orig_resnet.conv1
        self.bn1 = orig_resnet.bn1
        self.relu1 = orig_resnet.relu1
        self.conv2 = orig_resnet.conv2
        self.bn2 = orig_resnet.bn2
        self.relu2 = orig_resnet.relu2
        self.conv3 = orig_resnet.conv3
        self.bn3 = orig_resnet.bn3
        self.relu3 = orig_resnet.relu3
        self.maxpool = orig_resnet.maxpool
        self.layer1 = orig_resnet.layer1
        self.layer2 = orig_resnet.layer2
        self.layer3 = orig_resnet.layer3
        self.layer4 = orig_resnet.layer4

    def forward(self, x, return_feature_maps=False):
        conv_out = []
        x = self.relu1(self.bn1(self.conv1(x)))
        x = self.relu2(self.bn2(self.conv2(x)))
        x = self.relu3(self.bn3(self.conv3(x)))
        x = self.maxpool(x)
        x = self.layer1(x)
        conv_out.append(x)
        x = self.layer2(x)
        conv_out.append(x)
        x = self.layer3(x)
        conv_out.append(x)
        x = self.layer4(x)
        conv_out.append(x)
        if return_feature_maps:
            return conv_out
        return [x]

def __init__(self, orig_resnet):
    super(Resnet, self).__init__()
    self.conv1 = orig_resnet.conv1
    self.bn1 = orig_resnet.bn1
    self.relu1 = orig_resnet.relu1
    self.conv2 = orig_resnet.conv2
    self.bn2 = orig_resnet.bn2
    self.relu2 = orig_resnet.relu2
    self.conv3 = orig_resnet.conv3
    self.bn3 = orig_resnet.bn3
    self.relu3 = orig_resnet.relu3
    self.maxpool = orig_resnet.maxpool
    self.layer1 = orig_resnet.layer1
    self.layer2 = orig_resnet.layer2
    self.layer3 = orig_resnet.layer3
    self.layer4 = orig_resnet.layer4

class ResnetDilated(nn.Module):

    def __init__(self, orig_resnet, dilate_scale=8):
        super().__init__()
        from functools import partial
        if dilate_scale == 8:
            orig_resnet.layer3.apply(partial(self._nostride_dilate, dilate=2))
            orig_resnet.layer4.apply(partial(self._nostride_dilate, dilate=4))
        elif dilate_scale == 16:
            orig_resnet.layer4.apply(partial(self._nostride_dilate, dilate=2))
        self.conv1 = orig_resnet.conv1
        self.bn1 = orig_resnet.bn1
        self.relu1 = orig_resnet.relu1
        self.conv2 = orig_resnet.conv2
        self.bn2 = orig_resnet.bn2
        self.relu2 = orig_resnet.relu2
        self.conv3 = orig_resnet.conv3
        self.bn3 = orig_resnet.bn3
        self.relu3 = orig_resnet.relu3
        self.maxpool = orig_resnet.maxpool
        self.layer1 = orig_resnet.layer1
        self.layer2 = orig_resnet.layer2
        self.layer3 = orig_resnet.layer3
        self.layer4 = orig_resnet.layer4

    def _nostride_dilate(self, m, dilate):
        classname = m.__class__.__name__
        if classname.find('Conv') != -1:
            if m.stride == (2, 2):
                m.stride = (1, 1)
                if m.kernel_size == (3, 3):
                    m.dilation = (dilate // 2, dilate // 2)
                    m.padding = (dilate // 2, dilate // 2)
            elif m.kernel_size == (3, 3):
                m.dilation = (dilate, dilate)
                m.padding = (dilate, dilate)

    def forward(self, x, return_feature_maps=False):
        conv_out = []
        x = self.relu1(self.bn1(self.conv1(x)))
        x = self.relu2(self.bn2(self.conv2(x)))
        x = self.relu3(self.bn3(self.conv3(x)))
        x = self.maxpool(x)
        x = self.layer1(x)
        conv_out.append(x)
        x = self.layer2(x)
        conv_out.append(x)
        x = self.layer3(x)
        conv_out.append(x)
        x = self.layer4(x)
        conv_out.append(x)
        if return_feature_maps:
            return conv_out
        return [x]

def __init__(self, orig_resnet, dilate_scale=8):
    super().__init__()
    from functools import partial
    if dilate_scale == 8:
        orig_resnet.layer3.apply(partial(self._nostride_dilate, dilate=2))
        orig_resnet.layer4.apply(partial(self._nostride_dilate, dilate=4))
    elif dilate_scale == 16:
        orig_resnet.layer4.apply(partial(self._nostride_dilate, dilate=2))
    self.conv1 = orig_resnet.conv1
    self.bn1 = orig_resnet.bn1
    self.relu1 = orig_resnet.relu1
    self.conv2 = orig_resnet.conv2
    self.bn2 = orig_resnet.bn2
    self.relu2 = orig_resnet.relu2
    self.conv3 = orig_resnet.conv3
    self.bn3 = orig_resnet.bn3
    self.relu3 = orig_resnet.relu3
    self.maxpool = orig_resnet.maxpool
    self.layer1 = orig_resnet.layer1
    self.layer2 = orig_resnet.layer2
    self.layer3 = orig_resnet.layer3
    self.layer4 = orig_resnet.layer4

class MobileNetV2Dilated(nn.Module):

    def __init__(self, orig_net, dilate_scale=8):
        super(MobileNetV2Dilated, self).__init__()
        from functools import partial
        self.features = orig_net.features[:-1]
        self.total_idx = len(self.features)
        self.down_idx = [2, 4, 7, 14]
        if dilate_scale == 8:
            for i in range(self.down_idx[-2], self.down_idx[-1]):
                self.features[i].apply(partial(self._nostride_dilate, dilate=2))
            for i in range(self.down_idx[-1], self.total_idx):
                self.features[i].apply(partial(self._nostride_dilate, dilate=4))
        elif dilate_scale == 16:
            for i in range(self.down_idx[-1], self.total_idx):
                self.features[i].apply(partial(self._nostride_dilate, dilate=2))

    def _nostride_dilate(self, m, dilate):
        classname = m.__class__.__name__
        if classname.find('Conv') != -1:
            if m.stride == (2, 2):
                m.stride = (1, 1)
                if m.kernel_size == (3, 3):
                    m.dilation = (dilate // 2, dilate // 2)
                    m.padding = (dilate // 2, dilate // 2)
            elif m.kernel_size == (3, 3):
                m.dilation = (dilate, dilate)
                m.padding = (dilate, dilate)

    def forward(self, x, return_feature_maps=False):
        if return_feature_maps:
            conv_out = []
            for i in range(self.total_idx):
                x = self.features[i](x)
                if i in self.down_idx:
                    conv_out.append(x)
            conv_out.append(x)
            return conv_out
        else:
            return [self.features(x)]

def __init__(self, orig_net, dilate_scale=8):
    super(MobileNetV2Dilated, self).__init__()
    from functools import partial
    self.features = orig_net.features[:-1]
    self.total_idx = len(self.features)
    self.down_idx = [2, 4, 7, 14]
    if dilate_scale == 8:
        for i in range(self.down_idx[-2], self.down_idx[-1]):
            self.features[i].apply(partial(self._nostride_dilate, dilate=2))
        for i in range(self.down_idx[-1], self.total_idx):
            self.features[i].apply(partial(self._nostride_dilate, dilate=4))
    elif dilate_scale == 16:
        for i in range(self.down_idx[-1], self.total_idx):
            self.features[i].apply(partial(self._nostride_dilate, dilate=2))

class C1DeepSup(nn.Module):

    def __init__(self, num_class=150, fc_dim=2048, use_softmax=False, drop_last_conv=False):
        super(C1DeepSup, self).__init__()
        self.use_softmax = use_softmax
        self.drop_last_conv = drop_last_conv
        self.cbr = conv3x3_bn_relu(fc_dim, fc_dim // 4, 1)
        self.cbr_deepsup = conv3x3_bn_relu(fc_dim // 2, fc_dim // 4, 1)
        self.conv_last = nn.Conv2d(fc_dim // 4, num_class, 1, 1, 0)
        self.conv_last_deepsup = nn.Conv2d(fc_dim // 4, num_class, 1, 1, 0)

    def forward(self, conv_out, segSize=None):
        conv5 = conv_out[-1]
        x = self.cbr(conv5)
        if self.drop_last_conv:
            return x
        else:
            x = self.conv_last(x)
            if self.use_softmax:
                x = nn.functional.interpolate(x, size=segSize, mode='bilinear', align_corners=False)
                x = nn.functional.softmax(x, dim=1)
                return x
            conv4 = conv_out[-2]
            _ = self.cbr_deepsup(conv4)
            _ = self.conv_last_deepsup(_)
            x = nn.functional.log_softmax(x, dim=1)
            _ = nn.functional.log_softmax(_, dim=1)
            return (x, _)

def __init__(self, num_class=150, fc_dim=2048, use_softmax=False, drop_last_conv=False):
    super(C1DeepSup, self).__init__()
    self.use_softmax = use_softmax
    self.drop_last_conv = drop_last_conv
    self.cbr = conv3x3_bn_relu(fc_dim, fc_dim // 4, 1)
    self.cbr_deepsup = conv3x3_bn_relu(fc_dim // 2, fc_dim // 4, 1)
    self.conv_last = nn.Conv2d(fc_dim // 4, num_class, 1, 1, 0)
    self.conv_last_deepsup = nn.Conv2d(fc_dim // 4, num_class, 1, 1, 0)

class C1(nn.Module):

    def __init__(self, num_class=150, fc_dim=2048, use_softmax=False):
        super(C1, self).__init__()
        self.use_softmax = use_softmax
        self.cbr = conv3x3_bn_relu(fc_dim, fc_dim // 4, 1)
        self.conv_last = nn.Conv2d(fc_dim // 4, num_class, 1, 1, 0)

    def forward(self, conv_out, segSize=None):
        conv5 = conv_out[-1]
        x = self.cbr(conv5)
        x = self.conv_last(x)
        if self.use_softmax:
            x = nn.functional.interpolate(x, size=segSize, mode='bilinear', align_corners=False)
            x = nn.functional.softmax(x, dim=1)
        else:
            x = nn.functional.log_softmax(x, dim=1)
        return x

def __init__(self, num_class=150, fc_dim=2048, use_softmax=False):
    super(C1, self).__init__()
    self.use_softmax = use_softmax
    self.cbr = conv3x3_bn_relu(fc_dim, fc_dim // 4, 1)
    self.conv_last = nn.Conv2d(fc_dim // 4, num_class, 1, 1, 0)

class PPM(nn.Module):

    def __init__(self, num_class=150, fc_dim=4096, use_softmax=False, pool_scales=(1, 2, 3, 6)):
        super(PPM, self).__init__()
        self.use_softmax = use_softmax
        self.ppm = []
        for scale in pool_scales:
            self.ppm.append(nn.Sequential(nn.AdaptiveAvgPool2d(scale), nn.Conv2d(fc_dim, 512, kernel_size=1, bias=False), BatchNorm2d(512), nn.ReLU(inplace=True)))
        self.ppm = nn.ModuleList(self.ppm)
        self.conv_last = nn.Sequential(nn.Conv2d(fc_dim + len(pool_scales) * 512, 512, kernel_size=3, padding=1, bias=False), BatchNorm2d(512), nn.ReLU(inplace=True), nn.Dropout2d(0.1), nn.Conv2d(512, num_class, kernel_size=1))

    def forward(self, conv_out, segSize=None):
        conv5 = conv_out[-1]
        input_size = conv5.size()
        ppm_out = [conv5]
        for pool_scale in self.ppm:
            ppm_out.append(nn.functional.interpolate(pool_scale(conv5), (input_size[2], input_size[3]), mode='bilinear', align_corners=False))
        ppm_out = torch.cat(ppm_out, 1)
        x = self.conv_last(ppm_out)
        if self.use_softmax:
            x = nn.functional.interpolate(x, size=segSize, mode='bilinear', align_corners=False)
            x = nn.functional.softmax(x, dim=1)
        else:
            x = nn.functional.log_softmax(x, dim=1)
        return x

def __init__(self, num_class=150, fc_dim=4096, use_softmax=False, pool_scales=(1, 2, 3, 6)):
    super(PPM, self).__init__()
    self.use_softmax = use_softmax
    self.ppm = []
    for scale in pool_scales:
        self.ppm.append(nn.Sequential(nn.AdaptiveAvgPool2d(scale), nn.Conv2d(fc_dim, 512, kernel_size=1, bias=False), BatchNorm2d(512), nn.ReLU(inplace=True)))
    self.ppm = nn.ModuleList(self.ppm)
    self.conv_last = nn.Sequential(nn.Conv2d(fc_dim + len(pool_scales) * 512, 512, kernel_size=3, padding=1, bias=False), BatchNorm2d(512), nn.ReLU(inplace=True), nn.Dropout2d(0.1), nn.Conv2d(512, num_class, kernel_size=1))

def conv3x3(in_planes, out_planes, stride=1):
    """3x3 convolution with padding"""
    return nn.Conv2d(in_planes, out_planes, kernel_size=3, stride=stride, padding=1, bias=False)

class BasicBlock(nn.Module):
    expansion = 1

    def __init__(self, inplanes, planes, stride=1, downsample=None):
        super(BasicBlock, self).__init__()
        self.conv1 = conv3x3(inplanes, planes, stride)
        self.bn1 = BatchNorm2d(planes)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = conv3x3(planes, planes)
        self.bn2 = BatchNorm2d(planes)
        self.downsample = downsample
        self.stride = stride

    def forward(self, x):
        residual = x
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)
        out = self.conv2(out)
        out = self.bn2(out)
        if self.downsample is not None:
            residual = self.downsample(x)
        out += residual
        out = self.relu(out)
        return out

def __init__(self, inplanes, planes, stride=1, downsample=None):
    super(BasicBlock, self).__init__()
    self.conv1 = conv3x3(inplanes, planes, stride)
    self.bn1 = BatchNorm2d(planes)
    self.relu = nn.ReLU(inplace=True)
    self.conv2 = conv3x3(planes, planes)
    self.bn2 = BatchNorm2d(planes)
    self.downsample = downsample
    self.stride = stride

class Bottleneck(nn.Module):
    expansion = 4

    def __init__(self, inplanes, planes, stride=1, downsample=None):
        super(Bottleneck, self).__init__()
        self.conv1 = nn.Conv2d(inplanes, planes, kernel_size=1, bias=False)
        self.bn1 = BatchNorm2d(planes)
        self.conv2 = nn.Conv2d(planes, planes, kernel_size=3, stride=stride, padding=1, bias=False)
        self.bn2 = BatchNorm2d(planes)
        self.conv3 = nn.Conv2d(planes, planes * 4, kernel_size=1, bias=False)
        self.bn3 = BatchNorm2d(planes * 4)
        self.relu = nn.ReLU(inplace=True)
        self.downsample = downsample
        self.stride = stride

    def forward(self, x):
        residual = x
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)
        out = self.conv2(out)
        out = self.bn2(out)
        out = self.relu(out)
        out = self.conv3(out)
        out = self.bn3(out)
        if self.downsample is not None:
            residual = self.downsample(x)
        out += residual
        out = self.relu(out)
        return out

def __init__(self, inplanes, planes, stride=1, downsample=None):
    super(Bottleneck, self).__init__()
    self.conv1 = nn.Conv2d(inplanes, planes, kernel_size=1, bias=False)
    self.bn1 = BatchNorm2d(planes)
    self.conv2 = nn.Conv2d(planes, planes, kernel_size=3, stride=stride, padding=1, bias=False)
    self.bn2 = BatchNorm2d(planes)
    self.conv3 = nn.Conv2d(planes, planes * 4, kernel_size=1, bias=False)
    self.bn3 = BatchNorm2d(planes * 4)
    self.relu = nn.ReLU(inplace=True)
    self.downsample = downsample
    self.stride = stride

class ResNet(nn.Module):

    def __init__(self, block, layers, num_classes=1000):
        self.inplanes = 128
        super(ResNet, self).__init__()
        self.conv1 = conv3x3(3, 64, stride=2)
        self.bn1 = BatchNorm2d(64)
        self.relu1 = nn.ReLU(inplace=True)
        self.conv2 = conv3x3(64, 64)
        self.bn2 = BatchNorm2d(64)
        self.relu2 = nn.ReLU(inplace=True)
        self.conv3 = conv3x3(64, 128)
        self.bn3 = BatchNorm2d(128)
        self.relu3 = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        self.layer1 = self._make_layer(block, 64, layers[0])
        self.layer2 = self._make_layer(block, 128, layers[1], stride=2)
        self.layer3 = self._make_layer(block, 256, layers[2], stride=2)
        self.layer4 = self._make_layer(block, 512, layers[3], stride=2)
        self.avgpool = nn.AvgPool2d(7, stride=1)
        self.fc = nn.Linear(512 * block.expansion, num_classes)
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                n = m.kernel_size[0] * m.kernel_size[1] * m.out_channels
                m.weight.data.normal_(0, math.sqrt(2.0 / n))
            elif isinstance(m, BatchNorm2d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()

    def _make_layer(self, block, planes, blocks, stride=1):
        downsample = None
        if stride != 1 or self.inplanes != planes * block.expansion:
            downsample = nn.Sequential(nn.Conv2d(self.inplanes, planes * block.expansion, kernel_size=1, stride=stride, bias=False), BatchNorm2d(planes * block.expansion))
        layers = []
        layers.append(block(self.inplanes, planes, stride, downsample))
        self.inplanes = planes * block.expansion
        for i in range(1, blocks):
            layers.append(block(self.inplanes, planes))
        return nn.Sequential(*layers)

    def forward(self, x):
        x = self.relu1(self.bn1(self.conv1(x)))
        x = self.relu2(self.bn2(self.conv2(x)))
        x = self.relu3(self.bn3(self.conv3(x)))
        x = self.maxpool(x)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)
        x = self.avgpool(x)
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        return x

def __init__(self, block, layers, num_classes=1000):
    self.inplanes = 128
    super(ResNet, self).__init__()
    self.conv1 = conv3x3(3, 64, stride=2)
    self.bn1 = BatchNorm2d(64)
    self.relu1 = nn.ReLU(inplace=True)
    self.conv2 = conv3x3(64, 64)
    self.bn2 = BatchNorm2d(64)
    self.relu2 = nn.ReLU(inplace=True)
    self.conv3 = conv3x3(64, 128)
    self.bn3 = BatchNorm2d(128)
    self.relu3 = nn.ReLU(inplace=True)
    self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
    self.layer1 = self._make_layer(block, 64, layers[0])
    self.layer2 = self._make_layer(block, 128, layers[1], stride=2)
    self.layer3 = self._make_layer(block, 256, layers[2], stride=2)
    self.layer4 = self._make_layer(block, 512, layers[3], stride=2)
    self.avgpool = nn.AvgPool2d(7, stride=1)
    self.fc = nn.Linear(512 * block.expansion, num_classes)
    for m in self.modules():
        if isinstance(m, nn.Conv2d):
            n = m.kernel_size[0] * m.kernel_size[1] * m.out_channels
            m.weight.data.normal_(0, math.sqrt(2.0 / n))
        elif isinstance(m, BatchNorm2d):
            m.weight.data.fill_(1)
            m.bias.data.zero_()

def _make_layer(self, block, planes, blocks, stride=1):
    downsample = None
    if stride != 1 or self.inplanes != planes * block.expansion:
        downsample = nn.Sequential(nn.Conv2d(self.inplanes, planes * block.expansion, kernel_size=1, stride=stride, bias=False), BatchNorm2d(planes * block.expansion))
    layers = []
    layers.append(block(self.inplanes, planes, stride, downsample))
    self.inplanes = planes * block.expansion
    for i in range(1, blocks):
        layers.append(block(self.inplanes, planes))
    return nn.Sequential(*layers)

class UserScatteredDataParallel(DictGatherDataParallel):

    def scatter(self, inputs, kwargs, device_ids):
        assert len(inputs) == 1
        inputs = inputs[0]
        inputs = _async_copy_stream(inputs, device_ids)
        inputs = [[i] for i in inputs]
        assert len(kwargs) == 0
        kwargs = [{} for _ in range(len(inputs))]
        return (inputs, kwargs)

def scatter(self, inputs, kwargs, device_ids):
    assert len(inputs) == 1
    inputs = inputs[0]
    inputs = _async_copy_stream(inputs, device_ids)
    inputs = [[i] for i in inputs]
    assert len(kwargs) == 0
    kwargs = [{} for _ in range(len(inputs))]
    return (inputs, kwargs)

class _SynchronizedBatchNorm(_BatchNorm):

    def __init__(self, num_features, eps=1e-05, momentum=0.001, affine=True):
        super(_SynchronizedBatchNorm, self).__init__(num_features, eps=eps, momentum=momentum, affine=affine)
        self._sync_master = SyncMaster(self._data_parallel_master)
        self._is_parallel = False
        self._parallel_id = None
        self._slave_pipe = None
        self._moving_average_fraction = 1.0 - momentum
        self.register_buffer('_tmp_running_mean', torch.zeros(self.num_features))
        self.register_buffer('_tmp_running_var', torch.ones(self.num_features))
        self.register_buffer('_running_iter', torch.ones(1))
        self._tmp_running_mean = self.running_mean.clone() * self._running_iter
        self._tmp_running_var = self.running_var.clone() * self._running_iter

    def forward(self, input):
        if not (self._is_parallel and self.training):
            return F.batch_norm(input, self.running_mean, self.running_var, self.weight, self.bias, self.training, self.momentum, self.eps)
        input_shape = input.size()
        input = input.view(input.size(0), self.num_features, -1)
        sum_size = input.size(0) * input.size(2)
        input_sum = _sum_ft(input)
        input_ssum = _sum_ft(input ** 2)
        if self._parallel_id == 0:
            mean, inv_std = self._sync_master.run_master(_ChildMessage(input_sum, input_ssum, sum_size))
        else:
            mean, inv_std = self._slave_pipe.run_slave(_ChildMessage(input_sum, input_ssum, sum_size))
        if self.affine:
            output = (input - _unsqueeze_ft(mean)) * _unsqueeze_ft(inv_std * self.weight) + _unsqueeze_ft(self.bias)
        else:
            output = (input - _unsqueeze_ft(mean)) * _unsqueeze_ft(inv_std)
        return output.view(input_shape)

    def __data_parallel_replicate__(self, ctx, copy_id):
        self._is_parallel = True
        self._parallel_id = copy_id
        if self._parallel_id == 0:
            ctx.sync_master = self._sync_master
        else:
            self._slave_pipe = ctx.sync_master.register_slave(copy_id)

    def _data_parallel_master(self, intermediates):
        """Reduce the sum and square-sum, compute the statistics, and broadcast it."""
        intermediates = sorted(intermediates, key=lambda i: i[1].sum.get_device())
        to_reduce = [i[1][:2] for i in intermediates]
        to_reduce = [j for i in to_reduce for j in i]
        target_gpus = [i[1].sum.get_device() for i in intermediates]
        sum_size = sum([i[1].sum_size for i in intermediates])
        sum_, ssum = ReduceAddCoalesced.apply(target_gpus[0], 2, *to_reduce)
        mean, inv_std = self._compute_mean_std(sum_, ssum, sum_size)
        broadcasted = Broadcast.apply(target_gpus, mean, inv_std)
        outputs = []
        for i, rec in enumerate(intermediates):
            outputs.append((rec[0], _MasterMessage(*broadcasted[i * 2:i * 2 + 2])))
        return outputs

    def _add_weighted(self, dest, delta, alpha=1, beta=1, bias=0):
        """return *dest* by `dest := dest*alpha + delta*beta + bias`"""
        return dest * alpha + delta * beta + bias

    def _compute_mean_std(self, sum_, ssum, size):
        """Compute the mean and standard-deviation with sum and square-sum. This method
        also maintains the moving average on the master device."""
        assert size > 1, 'BatchNorm computes unbiased standard-deviation, which requires size > 1.'
        mean = sum_ / size
        sumvar = ssum - sum_ * mean
        unbias_var = sumvar / (size - 1)
        bias_var = sumvar / size
        self._tmp_running_mean = self._add_weighted(self._tmp_running_mean, mean.data, alpha=self._moving_average_fraction)
        self._tmp_running_var = self._add_weighted(self._tmp_running_var, unbias_var.data, alpha=self._moving_average_fraction)
        self._running_iter = self._add_weighted(self._running_iter, 1, alpha=self._moving_average_fraction)
        self.running_mean = self._tmp_running_mean / self._running_iter
        self.running_var = self._tmp_running_var / self._running_iter
        return (mean, bias_var.clamp(self.eps) ** (-0.5))

def __init__(self, num_features, eps=1e-05, momentum=0.001, affine=True):
    super(_SynchronizedBatchNorm, self).__init__(num_features, eps=eps, momentum=momentum, affine=affine)
    self._sync_master = SyncMaster(self._data_parallel_master)
    self._is_parallel = False
    self._parallel_id = None
    self._slave_pipe = None
    self._moving_average_fraction = 1.0 - momentum
    self.register_buffer('_tmp_running_mean', torch.zeros(self.num_features))
    self.register_buffer('_tmp_running_var', torch.ones(self.num_features))
    self.register_buffer('_running_iter', torch.ones(1))
    self._tmp_running_mean = self.running_mean.clone() * self._running_iter
    self._tmp_running_var = self.running_var.clone() * self._running_iter

def set_requires_grad(module, value):
    for param in module.parameters():
        param.requires_grad = value

class PerceptualLoss(nn.Module):
    """
    Perceptual loss, VGG-based
    https://arxiv.org/abs/1603.08155
    https://github.com/dxyang/StyleTransfer/blob/master/utils.py
    """

    def __init__(self, weights=[1.0, 1.0, 1.0, 1.0, 1.0]):
        super(PerceptualLoss, self).__init__()
        self.add_module('vgg', VGG19())
        self.criterion = torch.nn.L1Loss()
        self.weights = weights

    def __call__(self, x, y):
        x_vgg, y_vgg = (self.vgg(x), self.vgg(y))
        content_loss = 0.0
        content_loss += self.weights[0] * self.criterion(x_vgg['relu1_1'], y_vgg['relu1_1'])
        content_loss += self.weights[1] * self.criterion(x_vgg['relu2_1'], y_vgg['relu2_1'])
        content_loss += self.weights[2] * self.criterion(x_vgg['relu3_1'], y_vgg['relu3_1'])
        content_loss += self.weights[3] * self.criterion(x_vgg['relu4_1'], y_vgg['relu4_1'])
        content_loss += self.weights[4] * self.criterion(x_vgg['relu5_1'], y_vgg['relu5_1'])
        return content_loss

def __init__(self, weights=[1.0, 1.0, 1.0, 1.0, 1.0]):
    super(PerceptualLoss, self).__init__()
    self.add_module('vgg', VGG19())
    self.criterion = torch.nn.L1Loss()
    self.weights = weights

class VGG19(torch.nn.Module):

    def __init__(self):
        super(VGG19, self).__init__()
        features = models.vgg19(pretrained=True).features
        self.relu1_1 = torch.nn.Sequential()
        self.relu1_2 = torch.nn.Sequential()
        self.relu2_1 = torch.nn.Sequential()
        self.relu2_2 = torch.nn.Sequential()
        self.relu3_1 = torch.nn.Sequential()
        self.relu3_2 = torch.nn.Sequential()
        self.relu3_3 = torch.nn.Sequential()
        self.relu3_4 = torch.nn.Sequential()
        self.relu4_1 = torch.nn.Sequential()
        self.relu4_2 = torch.nn.Sequential()
        self.relu4_3 = torch.nn.Sequential()
        self.relu4_4 = torch.nn.Sequential()
        self.relu5_1 = torch.nn.Sequential()
        self.relu5_2 = torch.nn.Sequential()
        self.relu5_3 = torch.nn.Sequential()
        self.relu5_4 = torch.nn.Sequential()
        for x in range(2):
            self.relu1_1.add_module(str(x), features[x])
        for x in range(2, 4):
            self.relu1_2.add_module(str(x), features[x])
        for x in range(4, 7):
            self.relu2_1.add_module(str(x), features[x])
        for x in range(7, 9):
            self.relu2_2.add_module(str(x), features[x])
        for x in range(9, 12):
            self.relu3_1.add_module(str(x), features[x])
        for x in range(12, 14):
            self.relu3_2.add_module(str(x), features[x])
        for x in range(14, 16):
            self.relu3_2.add_module(str(x), features[x])
        for x in range(16, 18):
            self.relu3_4.add_module(str(x), features[x])
        for x in range(18, 21):
            self.relu4_1.add_module(str(x), features[x])
        for x in range(21, 23):
            self.relu4_2.add_module(str(x), features[x])
        for x in range(23, 25):
            self.relu4_3.add_module(str(x), features[x])
        for x in range(25, 27):
            self.relu4_4.add_module(str(x), features[x])
        for x in range(27, 30):
            self.relu5_1.add_module(str(x), features[x])
        for x in range(30, 32):
            self.relu5_2.add_module(str(x), features[x])
        for x in range(32, 34):
            self.relu5_3.add_module(str(x), features[x])
        for x in range(34, 36):
            self.relu5_4.add_module(str(x), features[x])
        for param in self.parameters():
            param.requires_grad = False

    def forward(self, x):
        relu1_1 = self.relu1_1(x)
        relu1_2 = self.relu1_2(relu1_1)
        relu2_1 = self.relu2_1(relu1_2)
        relu2_2 = self.relu2_2(relu2_1)
        relu3_1 = self.relu3_1(relu2_2)
        relu3_2 = self.relu3_2(relu3_1)
        relu3_3 = self.relu3_3(relu3_2)
        relu3_4 = self.relu3_4(relu3_3)
        relu4_1 = self.relu4_1(relu3_4)
        relu4_2 = self.relu4_2(relu4_1)
        relu4_3 = self.relu4_3(relu4_2)
        relu4_4 = self.relu4_4(relu4_3)
        relu5_1 = self.relu5_1(relu4_4)
        relu5_2 = self.relu5_2(relu5_1)
        relu5_3 = self.relu5_3(relu5_2)
        relu5_4 = self.relu5_4(relu5_3)
        out = {'relu1_1': relu1_1, 'relu1_2': relu1_2, 'relu2_1': relu2_1, 'relu2_2': relu2_2, 'relu3_1': relu3_1, 'relu3_2': relu3_2, 'relu3_3': relu3_3, 'relu3_4': relu3_4, 'relu4_1': relu4_1, 'relu4_2': relu4_2, 'relu4_3': relu4_3, 'relu4_4': relu4_4, 'relu5_1': relu5_1, 'relu5_2': relu5_2, 'relu5_3': relu5_3, 'relu5_4': relu5_4}
        return out

def __init__(self):
    super(VGG19, self).__init__()
    features = models.vgg19(pretrained=True).features
    self.relu1_1 = torch.nn.Sequential()
    self.relu1_2 = torch.nn.Sequential()
    self.relu2_1 = torch.nn.Sequential()
    self.relu2_2 = torch.nn.Sequential()
    self.relu3_1 = torch.nn.Sequential()
    self.relu3_2 = torch.nn.Sequential()
    self.relu3_3 = torch.nn.Sequential()
    self.relu3_4 = torch.nn.Sequential()
    self.relu4_1 = torch.nn.Sequential()
    self.relu4_2 = torch.nn.Sequential()
    self.relu4_3 = torch.nn.Sequential()
    self.relu4_4 = torch.nn.Sequential()
    self.relu5_1 = torch.nn.Sequential()
    self.relu5_2 = torch.nn.Sequential()
    self.relu5_3 = torch.nn.Sequential()
    self.relu5_4 = torch.nn.Sequential()
    for x in range(2):
        self.relu1_1.add_module(str(x), features[x])
    for x in range(2, 4):
        self.relu1_2.add_module(str(x), features[x])
    for x in range(4, 7):
        self.relu2_1.add_module(str(x), features[x])
    for x in range(7, 9):
        self.relu2_2.add_module(str(x), features[x])
    for x in range(9, 12):
        self.relu3_1.add_module(str(x), features[x])
    for x in range(12, 14):
        self.relu3_2.add_module(str(x), features[x])
    for x in range(14, 16):
        self.relu3_2.add_module(str(x), features[x])
    for x in range(16, 18):
        self.relu3_4.add_module(str(x), features[x])
    for x in range(18, 21):
        self.relu4_1.add_module(str(x), features[x])
    for x in range(21, 23):
        self.relu4_2.add_module(str(x), features[x])
    for x in range(23, 25):
        self.relu4_3.add_module(str(x), features[x])
    for x in range(25, 27):
        self.relu4_4.add_module(str(x), features[x])
    for x in range(27, 30):
        self.relu5_1.add_module(str(x), features[x])
    for x in range(30, 32):
        self.relu5_2.add_module(str(x), features[x])
    for x in range(32, 34):
        self.relu5_3.add_module(str(x), features[x])
    for x in range(34, 36):
        self.relu5_4.add_module(str(x), features[x])
    for param in self.parameters():
        param.requires_grad = False

class CrossEntropy2d(nn.Module):

    def __init__(self, reduction='mean', ignore_label=255, weights=None, *args, **kwargs):
        """
        weight (Tensor, optional): a manual rescaling weight given to each class.
            If given, has to be a Tensor of size "nclasses"
        """
        super(CrossEntropy2d, self).__init__()
        self.reduction = reduction
        self.ignore_label = ignore_label
        self.weights = weights
        if self.weights is not None:
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.weights = torch.FloatTensor(constant_weights[weights]).to(device)

    def forward(self, predict, target):
        """
            Args:
                predict:(n, c, h, w)
                target:(n, 1, h, w)
        """
        target = target.long()
        assert not target.requires_grad
        assert predict.dim() == 4, '{0}'.format(predict.size())
        assert target.dim() == 4, '{0}'.format(target.size())
        assert predict.size(0) == target.size(0), '{0} vs {1} '.format(predict.size(0), target.size(0))
        assert target.size(1) == 1, '{0}'.format(target.size(1))
        assert predict.size(2) == target.size(2), '{0} vs {1} '.format(predict.size(2), target.size(2))
        assert predict.size(3) == target.size(3), '{0} vs {1} '.format(predict.size(3), target.size(3))
        target = target.squeeze(1)
        n, c, h, w = predict.size()
        target_mask = (target >= 0) * (target != self.ignore_label)
        target = target[target_mask]
        predict = predict.transpose(1, 2).transpose(2, 3).contiguous()
        predict = predict[target_mask.view(n, h, w, 1).repeat(1, 1, 1, c)].view(-1, c)
        loss = F.cross_entropy(predict, target, weight=self.weights, reduction=self.reduction)
        return loss

def __init__(self, reduction='mean', ignore_label=255, weights=None, *args, **kwargs):
    """
        weight (Tensor, optional): a manual rescaling weight given to each class.
            If given, has to be a Tensor of size "nclasses"
        """
    super(CrossEntropy2d, self).__init__()
    self.reduction = reduction
    self.ignore_label = ignore_label
    self.weights = weights
    if self.weights is not None:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.weights = torch.FloatTensor(constant_weights[weights]).to(device)

class BlurMask(nn.Module):

    def __init__(self, kernel_size=5, width_factor=1):
        super().__init__()
        self.filter = nn.Conv2d(1, 1, kernel_size, padding=kernel_size // 2, padding_mode='replicate', bias=False)
        self.filter.weight.data.copy_(get_gauss_kernel(kernel_size, width_factor=width_factor))

    def forward(self, real_img, pred_img, mask):
        with torch.no_grad():
            result = self.filter(mask) * mask
            return result

def __init__(self, kernel_size=5, width_factor=1):
    super().__init__()
    self.filter = nn.Conv2d(1, 1, kernel_size, padding=kernel_size // 2, padding_mode='replicate', bias=False)
    self.filter.weight.data.copy_(get_gauss_kernel(kernel_size, width_factor=width_factor))

class EmulatedEDTMask(nn.Module):

    def __init__(self, dilate_kernel_size=5, blur_kernel_size=5, width_factor=1):
        super().__init__()
        self.dilate_filter = nn.Conv2d(1, 1, dilate_kernel_size, padding=dilate_kernel_size // 2, padding_mode='replicate', bias=False)
        self.dilate_filter.weight.data.copy_(torch.ones(1, 1, dilate_kernel_size, dilate_kernel_size, dtype=torch.float))
        self.blur_filter = nn.Conv2d(1, 1, blur_kernel_size, padding=blur_kernel_size // 2, padding_mode='replicate', bias=False)
        self.blur_filter.weight.data.copy_(get_gauss_kernel(blur_kernel_size, width_factor=width_factor))

    def forward(self, real_img, pred_img, mask):
        with torch.no_grad():
            known_mask = 1 - mask
            dilated_known_mask = (self.dilate_filter(known_mask) > 1).float()
            result = self.blur_filter(1 - dilated_known_mask) * mask
            return result

def __init__(self, dilate_kernel_size=5, blur_kernel_size=5, width_factor=1):
    super().__init__()
    self.dilate_filter = nn.Conv2d(1, 1, dilate_kernel_size, padding=dilate_kernel_size // 2, padding_mode='replicate', bias=False)
    self.dilate_filter.weight.data.copy_(torch.ones(1, 1, dilate_kernel_size, dilate_kernel_size, dtype=torch.float))
    self.blur_filter = nn.Conv2d(1, 1, blur_kernel_size, padding=blur_kernel_size // 2, padding_mode='replicate', bias=False)
    self.blur_filter.weight.data.copy_(get_gauss_kernel(blur_kernel_size, width_factor=width_factor))

class PropagatePerceptualSim(nn.Module):

    def __init__(self, level=2, max_iters=10, temperature=500, erode_mask_size=3):
        super().__init__()
        vgg = torchvision.models.vgg19(pretrained=True).features
        vgg_avg_pooling = []
        for weights in vgg.parameters():
            weights.requires_grad = False
        cur_level_i = 0
        for module in vgg.modules():
            if module.__class__.__name__ == 'Sequential':
                continue
            elif module.__class__.__name__ == 'MaxPool2d':
                vgg_avg_pooling.append(nn.AvgPool2d(kernel_size=2, stride=2, padding=0))
            else:
                vgg_avg_pooling.append(module)
                if module.__class__.__name__ == 'ReLU':
                    cur_level_i += 1
                if cur_level_i == level:
                    break
        self.features = nn.Sequential(*vgg_avg_pooling)
        self.max_iters = max_iters
        self.temperature = temperature
        self.do_erode = erode_mask_size > 0
        if self.do_erode:
            self.erode_mask = nn.Conv2d(1, 1, erode_mask_size, padding=erode_mask_size // 2, bias=False)
            self.erode_mask.weight.data.fill_(1)

    def forward(self, real_img, pred_img, mask):
        with torch.no_grad():
            real_img = (real_img - IMAGENET_MEAN.to(real_img)) / IMAGENET_STD.to(real_img)
            real_feats = self.features(real_img)
            vertical_sim = torch.exp(-(real_feats[:, :, 1:] - real_feats[:, :, :-1]).pow(2).sum(1, keepdim=True) / self.temperature)
            horizontal_sim = torch.exp(-(real_feats[:, :, :, 1:] - real_feats[:, :, :, :-1]).pow(2).sum(1, keepdim=True) / self.temperature)
            mask_scaled = F.interpolate(mask, size=real_feats.shape[-2:], mode='bilinear', align_corners=False)
            if self.do_erode:
                mask_scaled = (self.erode_mask(mask_scaled) > 1).float()
            cur_knowness = 1 - mask_scaled
            for iter_i in range(self.max_iters):
                new_top_knowness = F.pad(cur_knowness[:, :, :-1] * vertical_sim, (0, 0, 1, 0), mode='replicate')
                new_bottom_knowness = F.pad(cur_knowness[:, :, 1:] * vertical_sim, (0, 0, 0, 1), mode='replicate')
                new_left_knowness = F.pad(cur_knowness[:, :, :, :-1] * horizontal_sim, (1, 0, 0, 0), mode='replicate')
                new_right_knowness = F.pad(cur_knowness[:, :, :, 1:] * horizontal_sim, (0, 1, 0, 0), mode='replicate')
                new_knowness = torch.stack([new_top_knowness, new_bottom_knowness, new_left_knowness, new_right_knowness], dim=0).max(0).values
                cur_knowness = torch.max(cur_knowness, new_knowness)
            cur_knowness = F.interpolate(cur_knowness, size=mask.shape[-2:], mode='bilinear')
            result = torch.min(mask, 1 - cur_knowness)
            return result

def __init__(self, level=2, max_iters=10, temperature=500, erode_mask_size=3):
    super().__init__()
    vgg = torchvision.models.vgg19(pretrained=True).features
    vgg_avg_pooling = []
    for weights in vgg.parameters():
        weights.requires_grad = False
    cur_level_i = 0
    for module in vgg.modules():
        if module.__class__.__name__ == 'Sequential':
            continue
        elif module.__class__.__name__ == 'MaxPool2d':
            vgg_avg_pooling.append(nn.AvgPool2d(kernel_size=2, stride=2, padding=0))
        else:
            vgg_avg_pooling.append(module)
            if module.__class__.__name__ == 'ReLU':
                cur_level_i += 1
            if cur_level_i == level:
                break
    self.features = nn.Sequential(*vgg_avg_pooling)
    self.max_iters = max_iters
    self.temperature = temperature
    self.do_erode = erode_mask_size > 0
    if self.do_erode:
        self.erode_mask = nn.Conv2d(1, 1, erode_mask_size, padding=erode_mask_size // 2, bias=False)
        self.erode_mask.weight.data.fill_(1)

class PerceptualLoss(nn.Module):

    def __init__(self, normalize_inputs=True):
        super(PerceptualLoss, self).__init__()
        self.normalize_inputs = normalize_inputs
        self.mean_ = IMAGENET_MEAN
        self.std_ = IMAGENET_STD
        vgg = torchvision.models.vgg19(pretrained=True).features
        vgg_avg_pooling = []
        for weights in vgg.parameters():
            weights.requires_grad = False
        for module in vgg.modules():
            if module.__class__.__name__ == 'Sequential':
                continue
            elif module.__class__.__name__ == 'MaxPool2d':
                vgg_avg_pooling.append(nn.AvgPool2d(kernel_size=2, stride=2, padding=0))
            else:
                vgg_avg_pooling.append(module)
        self.vgg = nn.Sequential(*vgg_avg_pooling)

    def do_normalize_inputs(self, x):
        return (x - self.mean_.to(x.device)) / self.std_.to(x.device)

    def partial_losses(self, input, target, mask=None):
        check_and_warn_input_range(target, 0, 1, 'PerceptualLoss target in partial_losses')
        losses = []
        if self.normalize_inputs:
            features_input = self.do_normalize_inputs(input)
            features_target = self.do_normalize_inputs(target)
        else:
            features_input = input
            features_target = target
        for layer in self.vgg[:30]:
            features_input = layer(features_input)
            features_target = layer(features_target)
            if layer.__class__.__name__ == 'ReLU':
                loss = F.mse_loss(features_input, features_target, reduction='none')
                if mask is not None:
                    cur_mask = F.interpolate(mask, size=features_input.shape[-2:], mode='bilinear', align_corners=False)
                    loss = loss * (1 - cur_mask)
                loss = loss.mean(dim=tuple(range(1, len(loss.shape))))
                losses.append(loss)
        return losses

    def forward(self, input, target, mask=None):
        losses = self.partial_losses(input, target, mask=mask)
        return torch.stack(losses).sum(dim=0)

    def get_global_features(self, input):
        check_and_warn_input_range(input, 0, 1, 'PerceptualLoss input in get_global_features')
        if self.normalize_inputs:
            features_input = self.do_normalize_inputs(input)
        else:
            features_input = input
        features_input = self.vgg(features_input)
        return features_input

def __init__(self, normalize_inputs=True):
    super(PerceptualLoss, self).__init__()
    self.normalize_inputs = normalize_inputs
    self.mean_ = IMAGENET_MEAN
    self.std_ = IMAGENET_STD
    vgg = torchvision.models.vgg19(pretrained=True).features
    vgg_avg_pooling = []
    for weights in vgg.parameters():
        weights.requires_grad = False
    for module in vgg.modules():
        if module.__class__.__name__ == 'Sequential':
            continue
        elif module.__class__.__name__ == 'MaxPool2d':
            vgg_avg_pooling.append(nn.AvgPool2d(kernel_size=2, stride=2, padding=0))
        else:
            vgg_avg_pooling.append(module)
    self.vgg = nn.Sequential(*vgg_avg_pooling)

class ResNetPL(nn.Module):

    def __init__(self, weight=1, weights_path=None, arch_encoder='resnet50dilated', segmentation=True):
        super().__init__()
        self.impl = ModelBuilder.get_encoder(weights_path=weights_path, arch_encoder=arch_encoder, arch_decoder='ppm_deepsup', fc_dim=2048, segmentation=segmentation)
        self.impl.eval()
        for w in self.impl.parameters():
            w.requires_grad_(False)
        self.weight = weight

    def forward(self, pred, target):
        pred = (pred - IMAGENET_MEAN.to(pred)) / IMAGENET_STD.to(pred)
        target = (target - IMAGENET_MEAN.to(target)) / IMAGENET_STD.to(target)
        pred_feats = self.impl(pred, return_feature_maps=True)
        target_feats = self.impl(target, return_feature_maps=True)
        result = torch.stack([F.mse_loss(cur_pred, cur_target) for cur_pred, cur_target in zip(pred_feats, target_feats)]).sum() * self.weight
        return result

def __init__(self, weight=1, weights_path=None, arch_encoder='resnet50dilated', segmentation=True):
    super().__init__()
    self.impl = ModelBuilder.get_encoder(weights_path=weights_path, arch_encoder=arch_encoder, arch_decoder='ppm_deepsup', fc_dim=2048, segmentation=segmentation)
    self.impl.eval()
    for w in self.impl.parameters():
        w.requires_grad_(False)
    self.weight = weight

def make_random_rectangle_mask(shape, margin=10, bbox_min_size=30, bbox_max_size=100, min_times=0, max_times=3):
    height, width = shape
    mask = np.zeros((height, width), np.float32)
    bbox_max_size = min(bbox_max_size, height - margin * 2, width - margin * 2)
    times = np.random.randint(min_times, max_times + 1)
    for i in range(times):
        box_width = np.random.randint(bbox_min_size, bbox_max_size)
        box_height = np.random.randint(bbox_min_size, bbox_max_size)
        start_x = np.random.randint(margin, width - margin - box_width + 1)
        start_y = np.random.randint(margin, height - margin - box_height + 1)
        mask[start_y:start_y + box_height, start_x:start_x + box_width] = 1
    return mask[None, ...]

def make_random_superres_mask(shape, min_step=2, max_step=4, min_width=1, max_width=3):
    height, width = shape
    mask = np.zeros((height, width), np.float32)
    step_x = np.random.randint(min_step, max_step + 1)
    width_x = np.random.randint(min_width, min(step_x, max_width + 1))
    offset_x = np.random.randint(0, step_x)
    step_y = np.random.randint(min_step, max_step + 1)
    width_y = np.random.randint(min_width, min(step_y, max_width + 1))
    offset_y = np.random.randint(0, step_y)
    for dy in range(width_y):
        mask[offset_y + dy::step_y] = 1
    for dx in range(width_x):
        mask[:, offset_x + dx::step_x] = 1
    return mask[None, ...]

class InpaintingTrainWebDataset(IterableDataset):

    def __init__(self, indir, mask_generator, transform, shuffle_buffer=200):
        self.impl = webdataset.Dataset(indir).shuffle(shuffle_buffer).decode('rgb').to_tuple('jpg')
        self.mask_generator = mask_generator
        self.transform = transform

    def __iter__(self):
        for iter_i, (img,) in enumerate(self.impl):
            img = np.clip(img * 255, 0, 255).astype('uint8')
            img = self.transform(image=img)['image']
            img = np.transpose(img, (2, 0, 1))
            mask = self.mask_generator(img, iter_i=iter_i)
            yield dict(image=img, mask=mask)

def __init__(self, indir, mask_generator, transform, shuffle_buffer=200):
    self.impl = webdataset.Dataset(indir).shuffle(shuffle_buffer).decode('rgb').to_tuple('jpg')
    self.mask_generator = mask_generator
    self.transform = transform

class IAAAffine2(DualIAATransform):
    """Place a regular grid of points on the input and randomly move the neighbourhood of these point around
    via affine transformations.

    Note: This class introduce interpolation artifacts to mask if it has values other than {0;1}

    Args:
        p (float): probability of applying the transform. Default: 0.5.

    Targets:
        image, mask
    """

    def __init__(self, scale=(0.7, 1.3), translate_percent=None, translate_px=None, rotate=0.0, shear=(-0.1, 0.1), order=1, cval=0, mode='reflect', always_apply=False, p=0.5):
        super(IAAAffine2, self).__init__(always_apply, p)
        self.scale = dict(x=scale, y=scale)
        self.translate_percent = to_tuple(translate_percent, 0)
        self.translate_px = to_tuple(translate_px, 0)
        self.rotate = to_tuple(rotate)
        self.shear = dict(x=shear, y=shear)
        self.order = order
        self.cval = cval
        self.mode = mode

    @property
    def processor(self):
        return iaa.Affine(self.scale, self.translate_percent, self.translate_px, self.rotate, self.shear, self.order, self.cval, self.mode)

    def get_transform_init_args_names(self):
        return ('scale', 'translate_percent', 'translate_px', 'rotate', 'shear', 'order', 'cval', 'mode')

def __init__(self, scale=(0.7, 1.3), translate_percent=None, translate_px=None, rotate=0.0, shear=(-0.1, 0.1), order=1, cval=0, mode='reflect', always_apply=False, p=0.5):
    super(IAAAffine2, self).__init__(always_apply, p)
    self.scale = dict(x=scale, y=scale)
    self.translate_percent = to_tuple(translate_percent, 0)
    self.translate_px = to_tuple(translate_px, 0)
    self.rotate = to_tuple(rotate)
    self.shear = dict(x=shear, y=shear)
    self.order = order
    self.cval = cval
    self.mode = mode

class IAAPerspective2(DualIAATransform):
    """Perform a random four point perspective transform of the input.

    Note: This class introduce interpolation artifacts to mask if it has values other than {0;1}

    Args:
        scale ((float, float): standard deviation of the normal distributions. These are used to sample
            the random distances of the subimage's corners from the full image's corners. Default: (0.05, 0.1).
        p (float): probability of applying the transform. Default: 0.5.

    Targets:
        image, mask
    """

    def __init__(self, scale=(0.05, 0.1), keep_size=True, always_apply=False, p=0.5, order=1, cval=0, mode='replicate'):
        super(IAAPerspective2, self).__init__(always_apply, p)
        self.scale = to_tuple(scale, 1.0)
        self.keep_size = keep_size
        self.cval = cval
        self.mode = mode

    @property
    def processor(self):
        return iaa.PerspectiveTransform(self.scale, keep_size=self.keep_size, mode=self.mode, cval=self.cval)

    def get_transform_init_args_names(self):
        return ('scale', 'keep_size')

def __init__(self, scale=(0.05, 0.1), keep_size=True, always_apply=False, p=0.5, order=1, cval=0, mode='replicate'):
    super(IAAPerspective2, self).__init__(always_apply, p)
    self.scale = to_tuple(scale, 1.0)
    self.keep_size = keep_size
    self.cval = cval
    self.mode = mode

class BaseInpaintingTrainingModule(ptl.LightningModule):

    def __init__(self, config, use_ddp, *args, predict_only=False, visualize_each_iters=100, average_generator=False, generator_avg_beta=0.999, average_generator_start_step=30000, average_generator_period=10, store_discr_outputs_for_vis=False, **kwargs):
        super().__init__(*args, **kwargs)
        LOGGER.info('BaseInpaintingTrainingModule init called')
        self.config = config
        self.generator = make_generator(config, **self.config.generator)
        self.use_ddp = use_ddp
        if not get_has_ddp_rank():
            LOGGER.info(f'Generator\n{self.generator}')
        if not predict_only:
            self.save_hyperparameters(self.config)
            self.discriminator = make_discriminator(**self.config.discriminator)
            self.adversarial_loss = make_discrim_loss(**self.config.losses.adversarial)
            self.visualizer = make_visualizer(**self.config.visualizer)
            self.val_evaluator = make_evaluator(**self.config.evaluator)
            self.test_evaluator = make_evaluator(**self.config.evaluator)
            if not get_has_ddp_rank():
                LOGGER.info(f'Discriminator\n{self.discriminator}')
            extra_val = self.config.data.get('extra_val', ())
            if extra_val:
                self.extra_val_titles = list(extra_val)
                self.extra_evaluators = nn.ModuleDict({k: make_evaluator(**self.config.evaluator) for k in extra_val})
            else:
                self.extra_evaluators = {}
            self.average_generator = average_generator
            self.generator_avg_beta = generator_avg_beta
            self.average_generator_start_step = average_generator_start_step
            self.average_generator_period = average_generator_period
            self.generator_average = None
            self.last_generator_averaging_step = -1
            self.store_discr_outputs_for_vis = store_discr_outputs_for_vis
            if self.config.losses.get('l1', {'weight_known': 0})['weight_known'] > 0:
                self.loss_l1 = nn.L1Loss(reduction='none')
            if self.config.losses.get('mse', {'weight': 0})['weight'] > 0:
                self.loss_mse = nn.MSELoss(reduction='none')
            if self.config.losses.perceptual.weight > 0:
                self.loss_pl = PerceptualLoss()
            if self.config.losses.get('resnet_pl', {'weight': 0})['weight'] > 0:
                self.loss_resnet_pl = ResNetPL(**self.config.losses.resnet_pl)
            else:
                self.loss_resnet_pl = None
        self.visualize_each_iters = visualize_each_iters
        LOGGER.info('BaseInpaintingTrainingModule init done')

    def configure_optimizers(self):
        discriminator_params = list(self.discriminator.parameters())
        return [dict(optimizer=make_optimizer(self.generator.parameters(), **self.config.optimizers.generator)), dict(optimizer=make_optimizer(discriminator_params, **self.config.optimizers.discriminator))]

    def train_dataloader(self):
        kwargs = dict(self.config.data.train)
        if self.use_ddp:
            kwargs['ddp_kwargs'] = dict(num_replicas=self.trainer.num_nodes * self.trainer.num_processes, rank=self.trainer.global_rank, shuffle=True)
        dataloader = make_default_train_dataloader(**self.config.data.train)
        return dataloader

    def val_dataloader(self):
        res = [make_default_val_dataloader(**self.config.data.val)]
        if self.config.data.visual_test is not None:
            res = res + [make_default_val_dataloader(**self.config.data.visual_test)]
        else:
            res = res + res
        extra_val = self.config.data.get('extra_val', ())
        if extra_val:
            res += [make_default_val_dataloader(**extra_val[k]) for k in self.extra_val_titles]
        return res

    def training_step(self, batch, batch_idx, optimizer_idx=None):
        self._is_training_step = True
        return self._do_step(batch, batch_idx, mode='train', optimizer_idx=optimizer_idx)

    def validation_step(self, batch, batch_idx, dataloader_idx):
        extra_val_key = None
        if dataloader_idx == 0:
            mode = 'val'
        elif dataloader_idx == 1:
            mode = 'test'
        else:
            mode = 'extra_val'
            extra_val_key = self.extra_val_titles[dataloader_idx - 2]
        self._is_training_step = False
        return self._do_step(batch, batch_idx, mode=mode, extra_val_key=extra_val_key)

    def training_step_end(self, batch_parts_outputs):
        if self.training and self.average_generator and (self.global_step >= self.average_generator_start_step) and (self.global_step >= self.last_generator_averaging_step + self.average_generator_period):
            if self.generator_average is None:
                self.generator_average = copy.deepcopy(self.generator)
            else:
                update_running_average(self.generator_average, self.generator, decay=self.generator_avg_beta)
            self.last_generator_averaging_step = self.global_step
        full_loss = batch_parts_outputs['loss'].mean() if torch.is_tensor(batch_parts_outputs['loss']) else torch.tensor(batch_parts_outputs['loss']).float().requires_grad_(True)
        log_info = {k: v.mean() for k, v in batch_parts_outputs['log_info'].items()}
        self.log_dict(log_info, on_step=True, on_epoch=False)
        return full_loss

    def validation_epoch_end(self, outputs):
        outputs = [step_out for out_group in outputs for step_out in out_group]
        averaged_logs = average_dicts((step_out['log_info'] for step_out in outputs))
        self.log_dict({k: v.mean() for k, v in averaged_logs.items()})
        pd.set_option('display.max_columns', 500)
        pd.set_option('display.width', 1000)
        val_evaluator_states = [s['val_evaluator_state'] for s in outputs if 'val_evaluator_state' in s]
        val_evaluator_res = self.val_evaluator.evaluation_end(states=val_evaluator_states)
        val_evaluator_res_df = pd.DataFrame(val_evaluator_res).stack(1).unstack(0)
        val_evaluator_res_df.dropna(axis=1, how='all', inplace=True)
        LOGGER.info(f'Validation metrics after epoch #{self.current_epoch}, total {self.global_step} iterations:\n{val_evaluator_res_df}')
        for k, v in flatten_dict(val_evaluator_res).items():
            self.log(f'val_{k}', v)
        test_evaluator_states = [s['test_evaluator_state'] for s in outputs if 'test_evaluator_state' in s]
        test_evaluator_res = self.test_evaluator.evaluation_end(states=test_evaluator_states)
        test_evaluator_res_df = pd.DataFrame(test_evaluator_res).stack(1).unstack(0)
        test_evaluator_res_df.dropna(axis=1, how='all', inplace=True)
        LOGGER.info(f'Test metrics after epoch #{self.current_epoch}, total {self.global_step} iterations:\n{test_evaluator_res_df}')
        for k, v in flatten_dict(test_evaluator_res).items():
            self.log(f'test_{k}', v)
        if self.extra_evaluators:
            for cur_eval_title, cur_evaluator in self.extra_evaluators.items():
                cur_state_key = f'extra_val_{cur_eval_title}_evaluator_state'
                cur_states = [s[cur_state_key] for s in outputs if cur_state_key in s]
                cur_evaluator_res = cur_evaluator.evaluation_end(states=cur_states)
                cur_evaluator_res_df = pd.DataFrame(cur_evaluator_res).stack(1).unstack(0)
                cur_evaluator_res_df.dropna(axis=1, how='all', inplace=True)
                LOGGER.info(f'Extra val {cur_eval_title} metrics after epoch #{self.current_epoch}, total {self.global_step} iterations:\n{cur_evaluator_res_df}')
                for k, v in flatten_dict(cur_evaluator_res).items():
                    self.log(f'extra_val_{cur_eval_title}_{k}', v)

    def _do_step(self, batch, batch_idx, mode='train', optimizer_idx=None, extra_val_key=None):
        if optimizer_idx == 0:
            set_requires_grad(self.generator, True)
            set_requires_grad(self.discriminator, False)
        elif optimizer_idx == 1:
            set_requires_grad(self.generator, False)
            set_requires_grad(self.discriminator, True)
        batch = self(batch)
        total_loss = 0
        metrics = {}
        if optimizer_idx is None or optimizer_idx == 0:
            total_loss, metrics = self.generator_loss(batch)
        elif optimizer_idx is None or optimizer_idx == 1:
            if self.config.losses.adversarial.weight > 0:
                total_loss, metrics = self.discriminator_loss(batch)
        if self.get_ddp_rank() in (None, 0) and (batch_idx % self.visualize_each_iters == 0 or mode == 'test'):
            if self.config.losses.adversarial.weight > 0:
                if self.store_discr_outputs_for_vis:
                    with torch.no_grad():
                        self.store_discr_outputs(batch)
            vis_suffix = f'_{mode}'
            if mode == 'extra_val':
                vis_suffix += f'_{extra_val_key}'
            self.visualizer(self.current_epoch, batch_idx, batch, suffix=vis_suffix)
        metrics_prefix = f'{mode}_'
        if mode == 'extra_val':
            metrics_prefix += f'{extra_val_key}_'
        result = dict(loss=total_loss, log_info=add_prefix_to_keys(metrics, metrics_prefix))
        if mode == 'val':
            result['val_evaluator_state'] = self.val_evaluator.process_batch(batch)
        elif mode == 'test':
            result['test_evaluator_state'] = self.test_evaluator.process_batch(batch)
        elif mode == 'extra_val':
            result[f'extra_val_{extra_val_key}_evaluator_state'] = self.extra_evaluators[extra_val_key].process_batch(batch)
        return result

    def get_current_generator(self, no_average=False):
        if not no_average and (not self.training) and self.average_generator and (self.generator_average is not None):
            return self.generator_average
        return self.generator

    def forward(self, batch: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """Pass data through generator and obtain at leas 'predicted_image' and 'inpainted' keys"""
        raise NotImplementedError()

    def generator_loss(self, batch) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        raise NotImplementedError()

    def discriminator_loss(self, batch) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        raise NotImplementedError()

    def store_discr_outputs(self, batch):
        out_size = batch['image'].shape[2:]
        discr_real_out, _ = self.discriminator(batch['image'])
        discr_fake_out, _ = self.discriminator(batch['predicted_image'])
        batch['discr_output_real'] = F.interpolate(discr_real_out, size=out_size, mode='nearest')
        batch['discr_output_fake'] = F.interpolate(discr_fake_out, size=out_size, mode='nearest')
        batch['discr_output_diff'] = batch['discr_output_real'] - batch['discr_output_fake']

    def get_ddp_rank(self):
        return self.trainer.global_rank if self.trainer.num_nodes * self.trainer.num_processes > 1 else None

def __init__(self, config, use_ddp, *args, predict_only=False, visualize_each_iters=100, average_generator=False, generator_avg_beta=0.999, average_generator_start_step=30000, average_generator_period=10, store_discr_outputs_for_vis=False, **kwargs):
    super().__init__(*args, **kwargs)
    LOGGER.info('BaseInpaintingTrainingModule init called')
    self.config = config
    self.generator = make_generator(config, **self.config.generator)
    self.use_ddp = use_ddp
    if not get_has_ddp_rank():
        LOGGER.info(f'Generator\n{self.generator}')
    if not predict_only:
        self.save_hyperparameters(self.config)
        self.discriminator = make_discriminator(**self.config.discriminator)
        self.adversarial_loss = make_discrim_loss(**self.config.losses.adversarial)
        self.visualizer = make_visualizer(**self.config.visualizer)
        self.val_evaluator = make_evaluator(**self.config.evaluator)
        self.test_evaluator = make_evaluator(**self.config.evaluator)
        if not get_has_ddp_rank():
            LOGGER.info(f'Discriminator\n{self.discriminator}')
        extra_val = self.config.data.get('extra_val', ())
        if extra_val:
            self.extra_val_titles = list(extra_val)
            self.extra_evaluators = nn.ModuleDict({k: make_evaluator(**self.config.evaluator) for k in extra_val})
        else:
            self.extra_evaluators = {}
        self.average_generator = average_generator
        self.generator_avg_beta = generator_avg_beta
        self.average_generator_start_step = average_generator_start_step
        self.average_generator_period = average_generator_period
        self.generator_average = None
        self.last_generator_averaging_step = -1
        self.store_discr_outputs_for_vis = store_discr_outputs_for_vis
        if self.config.losses.get('l1', {'weight_known': 0})['weight_known'] > 0:
            self.loss_l1 = nn.L1Loss(reduction='none')
        if self.config.losses.get('mse', {'weight': 0})['weight'] > 0:
            self.loss_mse = nn.MSELoss(reduction='none')
        if self.config.losses.perceptual.weight > 0:
            self.loss_pl = PerceptualLoss()
        if self.config.losses.get('resnet_pl', {'weight': 0})['weight'] > 0:
            self.loss_resnet_pl = ResNetPL(**self.config.losses.resnet_pl)
        else:
            self.loss_resnet_pl = None
    self.visualize_each_iters = visualize_each_iters
    LOGGER.info('BaseInpaintingTrainingModule init done')

class DefaultInpaintingTrainingModule(BaseInpaintingTrainingModule):

    def __init__(self, *args, concat_mask=True, rescale_scheduler_kwargs=None, image_to_discriminator='predicted_image', add_noise_kwargs=None, noise_fill_hole=False, const_area_crop_kwargs=None, distance_weighter_kwargs=None, distance_weighted_mask_for_discr=False, fake_fakes_proba=0, fake_fakes_generator_kwargs=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.concat_mask = concat_mask
        self.rescale_size_getter = get_ramp(**rescale_scheduler_kwargs) if rescale_scheduler_kwargs is not None else None
        self.image_to_discriminator = image_to_discriminator
        self.add_noise_kwargs = add_noise_kwargs
        self.noise_fill_hole = noise_fill_hole
        self.const_area_crop_kwargs = const_area_crop_kwargs
        self.refine_mask_for_losses = make_mask_distance_weighter(**distance_weighter_kwargs) if distance_weighter_kwargs is not None else None
        self.distance_weighted_mask_for_discr = distance_weighted_mask_for_discr
        self.fake_fakes_proba = fake_fakes_proba
        if self.fake_fakes_proba > 0.001:
            self.fake_fakes_gen = FakeFakesGenerator(**fake_fakes_generator_kwargs or {})

    def forward(self, batch):
        if self.training and self.rescale_size_getter is not None:
            cur_size = self.rescale_size_getter(self.global_step)
            batch['image'] = F.interpolate(batch['image'], size=cur_size, mode='bilinear', align_corners=False)
            batch['mask'] = F.interpolate(batch['mask'], size=cur_size, mode='nearest')
        if self.training and self.const_area_crop_kwargs is not None:
            batch = make_constant_area_crop_batch(batch, **self.const_area_crop_kwargs)
        img = batch['image']
        mask = batch['mask']
        masked_img = img * (1 - mask)
        if self.add_noise_kwargs is not None:
            noise = make_multiscale_noise(masked_img, **self.add_noise_kwargs)
            if self.noise_fill_hole:
                masked_img = masked_img + mask * noise[:, :masked_img.shape[1]]
            masked_img = torch.cat([masked_img, noise], dim=1)
        if self.concat_mask:
            masked_img = torch.cat([masked_img, mask], dim=1)
        batch['predicted_image'] = self.generator(masked_img)
        batch['inpainted'] = mask * batch['predicted_image'] + (1 - mask) * batch['image']
        if self.fake_fakes_proba > 0.001:
            if self.training and torch.rand(1).item() < self.fake_fakes_proba:
                batch['fake_fakes'], batch['fake_fakes_masks'] = self.fake_fakes_gen(img, mask)
                batch['use_fake_fakes'] = True
            else:
                batch['fake_fakes'] = torch.zeros_like(img)
                batch['fake_fakes_masks'] = torch.zeros_like(mask)
                batch['use_fake_fakes'] = False
        batch['mask_for_losses'] = self.refine_mask_for_losses(img, batch['predicted_image'], mask) if self.refine_mask_for_losses is not None and self.training else mask
        return batch

    def generator_loss(self, batch):
        img = batch['image']
        predicted_img = batch[self.image_to_discriminator]
        original_mask = batch['mask']
        supervised_mask = batch['mask_for_losses']
        l1_value = masked_l1_loss(predicted_img, img, supervised_mask, self.config.losses.l1.weight_known, self.config.losses.l1.weight_missing)
        total_loss = l1_value
        metrics = dict(gen_l1=l1_value)
        if self.config.losses.perceptual.weight > 0:
            pl_value = self.loss_pl(predicted_img, img, mask=supervised_mask).sum() * self.config.losses.perceptual.weight
            total_loss = total_loss + pl_value
            metrics['gen_pl'] = pl_value
        mask_for_discr = supervised_mask if self.distance_weighted_mask_for_discr else original_mask
        self.adversarial_loss.pre_generator_step(real_batch=img, fake_batch=predicted_img, generator=self.generator, discriminator=self.discriminator)
        discr_real_pred, discr_real_features = self.discriminator(img)
        discr_fake_pred, discr_fake_features = self.discriminator(predicted_img)
        adv_gen_loss, adv_metrics = self.adversarial_loss.generator_loss(real_batch=img, fake_batch=predicted_img, discr_real_pred=discr_real_pred, discr_fake_pred=discr_fake_pred, mask=mask_for_discr)
        total_loss = total_loss + adv_gen_loss
        metrics['gen_adv'] = adv_gen_loss
        metrics.update(add_prefix_to_keys(adv_metrics, 'adv_'))
        if self.config.losses.feature_matching.weight > 0:
            need_mask_in_fm = OmegaConf.to_container(self.config.losses.feature_matching).get('pass_mask', False)
            mask_for_fm = supervised_mask if need_mask_in_fm else None
            fm_value = feature_matching_loss(discr_fake_features, discr_real_features, mask=mask_for_fm) * self.config.losses.feature_matching.weight
            total_loss = total_loss + fm_value
            metrics['gen_fm'] = fm_value
        if self.loss_resnet_pl is not None:
            resnet_pl_value = self.loss_resnet_pl(predicted_img, img)
            total_loss = total_loss + resnet_pl_value
            metrics['gen_resnet_pl'] = resnet_pl_value
        return (total_loss, metrics)

    def discriminator_loss(self, batch):
        total_loss = 0
        metrics = {}
        predicted_img = batch[self.image_to_discriminator].detach()
        self.adversarial_loss.pre_discriminator_step(real_batch=batch['image'], fake_batch=predicted_img, generator=self.generator, discriminator=self.discriminator)
        discr_real_pred, discr_real_features = self.discriminator(batch['image'])
        discr_fake_pred, discr_fake_features = self.discriminator(predicted_img)
        adv_discr_loss, adv_metrics = self.adversarial_loss.discriminator_loss(real_batch=batch['image'], fake_batch=predicted_img, discr_real_pred=discr_real_pred, discr_fake_pred=discr_fake_pred, mask=batch['mask'])
        total_loss = total_loss + adv_discr_loss
        metrics['discr_adv'] = adv_discr_loss
        metrics.update(add_prefix_to_keys(adv_metrics, 'adv_'))
        if batch.get('use_fake_fakes', False):
            fake_fakes = batch['fake_fakes']
            self.adversarial_loss.pre_discriminator_step(real_batch=batch['image'], fake_batch=fake_fakes, generator=self.generator, discriminator=self.discriminator)
            discr_fake_fakes_pred, _ = self.discriminator(fake_fakes)
            fake_fakes_adv_discr_loss, fake_fakes_adv_metrics = self.adversarial_loss.discriminator_loss(real_batch=batch['image'], fake_batch=fake_fakes, discr_real_pred=discr_real_pred, discr_fake_pred=discr_fake_fakes_pred, mask=batch['mask'])
            total_loss = total_loss + fake_fakes_adv_discr_loss
            metrics['discr_adv_fake_fakes'] = fake_fakes_adv_discr_loss
            metrics.update(add_prefix_to_keys(fake_fakes_adv_metrics, 'adv_'))
        return (total_loss, metrics)

def __init__(self, *args, concat_mask=True, rescale_scheduler_kwargs=None, image_to_discriminator='predicted_image', add_noise_kwargs=None, noise_fill_hole=False, const_area_crop_kwargs=None, distance_weighter_kwargs=None, distance_weighted_mask_for_discr=False, fake_fakes_proba=0, fake_fakes_generator_kwargs=None, **kwargs):
    super().__init__(*args, **kwargs)
    self.concat_mask = concat_mask
    self.rescale_size_getter = get_ramp(**rescale_scheduler_kwargs) if rescale_scheduler_kwargs is not None else None
    self.image_to_discriminator = image_to_discriminator
    self.add_noise_kwargs = add_noise_kwargs
    self.noise_fill_hole = noise_fill_hole
    self.const_area_crop_kwargs = const_area_crop_kwargs
    self.refine_mask_for_losses = make_mask_distance_weighter(**distance_weighter_kwargs) if distance_weighter_kwargs is not None else None
    self.distance_weighted_mask_for_discr = distance_weighted_mask_for_discr
    self.fake_fakes_proba = fake_fakes_proba
    if self.fake_fakes_proba > 0.001:
        self.fake_fakes_gen = FakeFakesGenerator(**fake_fakes_generator_kwargs or {})

class ResNetHead(nn.Module):

    def __init__(self, input_nc, ngf=64, n_downsampling=3, n_blocks=9, norm_layer=nn.BatchNorm2d, padding_type='reflect', conv_kind='default', activation=nn.ReLU(True)):
        assert n_blocks >= 0
        super(ResNetHead, self).__init__()
        conv_layer = get_conv_block_ctor(conv_kind)
        model = [nn.ReflectionPad2d(3), conv_layer(input_nc, ngf, kernel_size=7, padding=0), norm_layer(ngf), activation]
        for i in range(n_downsampling):
            mult = 2 ** i
            model += [conv_layer(ngf * mult, ngf * mult * 2, kernel_size=3, stride=2, padding=1), norm_layer(ngf * mult * 2), activation]
        mult = 2 ** n_downsampling
        for i in range(n_blocks):
            model += [ResnetBlock(ngf * mult, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=conv_kind)]
        self.model = nn.Sequential(*model)

    def forward(self, input):
        return self.model(input)

def __init__(self, input_nc, ngf=64, n_downsampling=3, n_blocks=9, norm_layer=nn.BatchNorm2d, padding_type='reflect', conv_kind='default', activation=nn.ReLU(True)):
    assert n_blocks >= 0
    super(ResNetHead, self).__init__()
    conv_layer = get_conv_block_ctor(conv_kind)
    model = [nn.ReflectionPad2d(3), conv_layer(input_nc, ngf, kernel_size=7, padding=0), norm_layer(ngf), activation]
    for i in range(n_downsampling):
        mult = 2 ** i
        model += [conv_layer(ngf * mult, ngf * mult * 2, kernel_size=3, stride=2, padding=1), norm_layer(ngf * mult * 2), activation]
    mult = 2 ** n_downsampling
    for i in range(n_blocks):
        model += [ResnetBlock(ngf * mult, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=conv_kind)]
    self.model = nn.Sequential(*model)

class ResNetTail(nn.Module):

    def __init__(self, output_nc, ngf=64, n_downsampling=3, n_blocks=9, norm_layer=nn.BatchNorm2d, padding_type='reflect', conv_kind='default', activation=nn.ReLU(True), up_norm_layer=nn.BatchNorm2d, up_activation=nn.ReLU(True), add_out_act=False, out_extra_layers_n=0, add_in_proj=None):
        assert n_blocks >= 0
        super(ResNetTail, self).__init__()
        mult = 2 ** n_downsampling
        model = []
        if add_in_proj is not None:
            model.append(nn.Conv2d(add_in_proj, ngf * mult, kernel_size=1))
        for i in range(n_blocks):
            model += [ResnetBlock(ngf * mult, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=conv_kind)]
        for i in range(n_downsampling):
            mult = 2 ** (n_downsampling - i)
            model += [nn.ConvTranspose2d(ngf * mult, int(ngf * mult / 2), kernel_size=3, stride=2, padding=1, output_padding=1), up_norm_layer(int(ngf * mult / 2)), up_activation]
        self.model = nn.Sequential(*model)
        out_layers = []
        for _ in range(out_extra_layers_n):
            out_layers += [nn.Conv2d(ngf, ngf, kernel_size=1, padding=0), up_norm_layer(ngf), up_activation]
        out_layers += [nn.ReflectionPad2d(3), nn.Conv2d(ngf, output_nc, kernel_size=7, padding=0)]
        if add_out_act:
            out_layers.append(get_activation('tanh' if add_out_act is True else add_out_act))
        self.out_proj = nn.Sequential(*out_layers)

    def forward(self, input, return_last_act=False):
        features = self.model(input)
        out = self.out_proj(features)
        if return_last_act:
            return (out, features)
        else:
            return out

def __init__(self, output_nc, ngf=64, n_downsampling=3, n_blocks=9, norm_layer=nn.BatchNorm2d, padding_type='reflect', conv_kind='default', activation=nn.ReLU(True), up_norm_layer=nn.BatchNorm2d, up_activation=nn.ReLU(True), add_out_act=False, out_extra_layers_n=0, add_in_proj=None):
    assert n_blocks >= 0
    super(ResNetTail, self).__init__()
    mult = 2 ** n_downsampling
    model = []
    if add_in_proj is not None:
        model.append(nn.Conv2d(add_in_proj, ngf * mult, kernel_size=1))
    for i in range(n_blocks):
        model += [ResnetBlock(ngf * mult, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=conv_kind)]
    for i in range(n_downsampling):
        mult = 2 ** (n_downsampling - i)
        model += [nn.ConvTranspose2d(ngf * mult, int(ngf * mult / 2), kernel_size=3, stride=2, padding=1, output_padding=1), up_norm_layer(int(ngf * mult / 2)), up_activation]
    self.model = nn.Sequential(*model)
    out_layers = []
    for _ in range(out_extra_layers_n):
        out_layers += [nn.Conv2d(ngf, ngf, kernel_size=1, padding=0), up_norm_layer(ngf), up_activation]
    out_layers += [nn.ReflectionPad2d(3), nn.Conv2d(ngf, output_nc, kernel_size=7, padding=0)]
    if add_out_act:
        out_layers.append(get_activation('tanh' if add_out_act is True else add_out_act))
    self.out_proj = nn.Sequential(*out_layers)

class MultiscaleResNet(nn.Module):

    def __init__(self, input_nc, output_nc, ngf=64, n_downsampling=2, n_blocks_head=2, n_blocks_tail=6, n_scales=3, norm_layer=nn.BatchNorm2d, padding_type='reflect', conv_kind='default', activation=nn.ReLU(True), up_norm_layer=nn.BatchNorm2d, up_activation=nn.ReLU(True), add_out_act=False, out_extra_layers_n=0, out_cumulative=False, return_only_hr=False):
        super().__init__()
        self.heads = nn.ModuleList([ResNetHead(input_nc, ngf=ngf, n_downsampling=n_downsampling, n_blocks=n_blocks_head, norm_layer=norm_layer, padding_type=padding_type, conv_kind=conv_kind, activation=activation) for i in range(n_scales)])
        tail_in_feats = ngf * 2 ** n_downsampling + ngf
        self.tails = nn.ModuleList([ResNetTail(output_nc, ngf=ngf, n_downsampling=n_downsampling, n_blocks=n_blocks_tail, norm_layer=norm_layer, padding_type=padding_type, conv_kind=conv_kind, activation=activation, up_norm_layer=up_norm_layer, up_activation=up_activation, add_out_act=add_out_act, out_extra_layers_n=out_extra_layers_n, add_in_proj=None if i == n_scales - 1 else tail_in_feats) for i in range(n_scales)])
        self.out_cumulative = out_cumulative
        self.return_only_hr = return_only_hr

    @property
    def num_scales(self):
        return len(self.heads)

    def forward(self, ms_inputs: List[torch.Tensor], smallest_scales_num: Optional[int]=None) -> Union[torch.Tensor, List[torch.Tensor]]:
        """
        :param ms_inputs: List of inputs of different resolutions from HR to LR
        :param smallest_scales_num: int or None, number of smallest scales to take at input
        :return: Depending on return_only_hr:
            True: Only the most HR output
            False: List of outputs of different resolutions from HR to LR
        """
        if smallest_scales_num is None:
            assert len(self.heads) == len(ms_inputs), (len(self.heads), len(ms_inputs), smallest_scales_num)
            smallest_scales_num = len(self.heads)
        else:
            assert smallest_scales_num == len(ms_inputs) <= len(self.heads), (len(self.heads), len(ms_inputs), smallest_scales_num)
        cur_heads = self.heads[-smallest_scales_num:]
        ms_features = [cur_head(cur_inp) for cur_head, cur_inp in zip(cur_heads, ms_inputs)]
        all_outputs = []
        prev_tail_features = None
        for i in range(len(ms_features)):
            scale_i = -i - 1
            cur_tail_input = ms_features[-i - 1]
            if prev_tail_features is not None:
                if prev_tail_features.shape != cur_tail_input.shape:
                    prev_tail_features = F.interpolate(prev_tail_features, size=cur_tail_input.shape[2:], mode='bilinear', align_corners=False)
                cur_tail_input = torch.cat((cur_tail_input, prev_tail_features), dim=1)
            cur_out, cur_tail_feats = self.tails[scale_i](cur_tail_input, return_last_act=True)
            prev_tail_features = cur_tail_feats
            all_outputs.append(cur_out)
        if self.out_cumulative:
            all_outputs_cum = [all_outputs[0]]
            for i in range(1, len(ms_features)):
                cur_out = all_outputs[i]
                cur_out_cum = cur_out + F.interpolate(all_outputs_cum[-1], size=cur_out.shape[2:], mode='bilinear', align_corners=False)
                all_outputs_cum.append(cur_out_cum)
            all_outputs = all_outputs_cum
        if self.return_only_hr:
            return all_outputs[-1]
        else:
            return all_outputs[::-1]

def __init__(self, input_nc, output_nc, ngf=64, n_downsampling=2, n_blocks_head=2, n_blocks_tail=6, n_scales=3, norm_layer=nn.BatchNorm2d, padding_type='reflect', conv_kind='default', activation=nn.ReLU(True), up_norm_layer=nn.BatchNorm2d, up_activation=nn.ReLU(True), add_out_act=False, out_extra_layers_n=0, out_cumulative=False, return_only_hr=False):
    super().__init__()
    self.heads = nn.ModuleList([ResNetHead(input_nc, ngf=ngf, n_downsampling=n_downsampling, n_blocks=n_blocks_head, norm_layer=norm_layer, padding_type=padding_type, conv_kind=conv_kind, activation=activation) for i in range(n_scales)])
    tail_in_feats = ngf * 2 ** n_downsampling + ngf
    self.tails = nn.ModuleList([ResNetTail(output_nc, ngf=ngf, n_downsampling=n_downsampling, n_blocks=n_blocks_tail, norm_layer=norm_layer, padding_type=padding_type, conv_kind=conv_kind, activation=activation, up_norm_layer=up_norm_layer, up_activation=up_activation, add_out_act=add_out_act, out_extra_layers_n=out_extra_layers_n, add_in_proj=None if i == n_scales - 1 else tail_in_feats) for i in range(n_scales)])
    self.out_cumulative = out_cumulative
    self.return_only_hr = return_only_hr

class MultiscaleDiscriminatorSimple(nn.Module):

    def __init__(self, ms_impl):
        super().__init__()
        self.ms_impl = nn.ModuleList(ms_impl)

    @property
    def num_scales(self):
        return len(self.ms_impl)

    def forward(self, ms_inputs: List[torch.Tensor], smallest_scales_num: Optional[int]=None) -> List[Tuple[torch.Tensor, List[torch.Tensor]]]:
        """
        :param ms_inputs: List of inputs of different resolutions from HR to LR
        :param smallest_scales_num: int or None, number of smallest scales to take at input
        :return: List of pairs (prediction, features) for different resolutions from HR to LR
        """
        if smallest_scales_num is None:
            assert len(self.ms_impl) == len(ms_inputs), (len(self.ms_impl), len(ms_inputs), smallest_scales_num)
            smallest_scales_num = len(self.heads)
        else:
            assert smallest_scales_num == len(ms_inputs) <= len(self.ms_impl), (len(self.ms_impl), len(ms_inputs), smallest_scales_num)
        return [cur_discr(cur_input) for cur_discr, cur_input in zip(self.ms_impl[-smallest_scales_num:], ms_inputs)]

def __init__(self, ms_impl):
    super().__init__()
    self.ms_impl = nn.ModuleList(ms_impl)

class SingleToMultiScaleInputMixin:

    def forward(self, x: torch.Tensor) -> List:
        orig_height, orig_width = x.shape[2:]
        factors = [2 ** i for i in range(self.num_scales)]
        ms_inputs = [F.interpolate(x, size=(orig_height // f, orig_width // f), mode='bilinear', align_corners=False) for f in factors]
        return super().forward(ms_inputs)

def forward(self, x: torch.Tensor) -> List:
    orig_height, orig_width = x.shape[2:]
    factors = [2 ** i for i in range(self.num_scales)]
    ms_inputs = [F.interpolate(x, size=(orig_height // f, orig_width // f), mode='bilinear', align_corners=False) for f in factors]
    return super().forward(ms_inputs)

class GeneratorMultiToSingleOutputMixin:

    def forward(self, x):
        return super().forward(x)[0]

def forward(self, x):
    return super().forward(x)[0]

class DiscriminatorMultiToSingleOutputMixin:

    def forward(self, x):
        out_feat_tuples = super().forward(x)
        return (out_feat_tuples[0][0], [f for _, flist in out_feat_tuples for f in flist])

def forward(self, x):
    out_feat_tuples = super().forward(x)
    return (out_feat_tuples[0][0], [f for _, flist in out_feat_tuples for f in flist])

class DiscriminatorMultiToSingleOutputStackedMixin:

    def __init__(self, *args, return_feats_only_levels=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.return_feats_only_levels = return_feats_only_levels

    def forward(self, x):
        out_feat_tuples = super().forward(x)
        outs = [out for out, _ in out_feat_tuples]
        scaled_outs = [outs[0]] + [F.interpolate(cur_out, size=outs[0].shape[-2:], mode='bilinear', align_corners=False) for cur_out in outs[1:]]
        out = torch.cat(scaled_outs, dim=1)
        if self.return_feats_only_levels is not None:
            feat_lists = [out_feat_tuples[i][1] for i in self.return_feats_only_levels]
        else:
            feat_lists = [flist for _, flist in out_feat_tuples]
        feats = [f for flist in feat_lists for f in flist]
        return (out, feats)

def __init__(self, *args, return_feats_only_levels=None, **kwargs):
    super().__init__(*args, **kwargs)
    self.return_feats_only_levels = return_feats_only_levels

def forward(self, x):
    out_feat_tuples = super().forward(x)
    outs = [out for out, _ in out_feat_tuples]
    scaled_outs = [outs[0]] + [F.interpolate(cur_out, size=outs[0].shape[-2:], mode='bilinear', align_corners=False) for cur_out in outs[1:]]
    out = torch.cat(scaled_outs, dim=1)
    if self.return_feats_only_levels is not None:
        feat_lists = [out_feat_tuples[i][1] for i in self.return_feats_only_levels]
    else:
        feat_lists = [flist for _, flist in out_feat_tuples]
    feats = [f for flist in feat_lists for f in flist]
    return (out, feats)

def get_activation(kind='tanh'):
    if kind == 'tanh':
        return nn.Tanh()
    if kind == 'sigmoid':
        return nn.Sigmoid()
    if kind is False:
        return nn.Identity()
    raise ValueError(f'Unknown activation kind {kind}')

class SimpleMultiStepGenerator(nn.Module):

    def __init__(self, steps: List[nn.Module]):
        super().__init__()
        self.steps = nn.ModuleList(steps)

    def forward(self, x):
        cur_in = x
        outs = []
        for step in self.steps:
            cur_out = step(cur_in)
            outs.append(cur_out)
            cur_in = torch.cat((cur_in, cur_out), dim=1)
        return torch.cat(outs[::-1], dim=1)

def __init__(self, steps: List[nn.Module]):
    super().__init__()
    self.steps = nn.ModuleList(steps)

def deconv_factory(kind, ngf, mult, norm_layer, activation, max_features):
    if kind == 'convtranspose':
        return [nn.ConvTranspose2d(min(max_features, ngf * mult), min(max_features, int(ngf * mult / 2)), kernel_size=3, stride=2, padding=1, output_padding=1), norm_layer(min(max_features, int(ngf * mult / 2))), activation]
    elif kind == 'bilinear':
        return [nn.Upsample(scale_factor=2, mode='bilinear'), DepthWiseSeperableConv(min(max_features, ngf * mult), min(max_features, int(ngf * mult / 2)), kernel_size=3, stride=1, padding=1), norm_layer(min(max_features, int(ngf * mult / 2))), activation]
    else:
        raise Exception(f'Invalid deconv kind: {kind}')

class FFCSE_block(nn.Module):

    def __init__(self, channels, ratio_g):
        super(FFCSE_block, self).__init__()
        in_cg = int(channels * ratio_g)
        in_cl = channels - in_cg
        r = 16
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.conv1 = nn.Conv2d(channels, channels // r, kernel_size=1, bias=True)
        self.relu1 = nn.ReLU(inplace=True)
        self.conv_a2l = None if in_cl == 0 else nn.Conv2d(channels // r, in_cl, kernel_size=1, bias=True)
        self.conv_a2g = None if in_cg == 0 else nn.Conv2d(channels // r, in_cg, kernel_size=1, bias=True)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        x = x if type(x) is tuple else (x, 0)
        id_l, id_g = x
        x = id_l if type(id_g) is int else torch.cat([id_l, id_g], dim=1)
        x = self.avgpool(x)
        x = self.relu1(self.conv1(x))
        x_l = 0 if self.conv_a2l is None else id_l * self.sigmoid(self.conv_a2l(x))
        x_g = 0 if self.conv_a2g is None else id_g * self.sigmoid(self.conv_a2g(x))
        return (x_l, x_g)

def __init__(self, channels, ratio_g):
    super(FFCSE_block, self).__init__()
    in_cg = int(channels * ratio_g)
    in_cl = channels - in_cg
    r = 16
    self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
    self.conv1 = nn.Conv2d(channels, channels // r, kernel_size=1, bias=True)
    self.relu1 = nn.ReLU(inplace=True)
    self.conv_a2l = None if in_cl == 0 else nn.Conv2d(channels // r, in_cl, kernel_size=1, bias=True)
    self.conv_a2g = None if in_cg == 0 else nn.Conv2d(channels // r, in_cg, kernel_size=1, bias=True)
    self.sigmoid = nn.Sigmoid()

class FourierUnit(nn.Module):

    def __init__(self, in_channels, out_channels, groups=1, spatial_scale_factor=None, spatial_scale_mode='bilinear', spectral_pos_encoding=False, use_se=False, se_kwargs=None, ffc3d=False, fft_norm='ortho'):
        super(FourierUnit, self).__init__()
        self.groups = groups
        self.conv_layer = torch.nn.Conv2d(in_channels=in_channels * 2 + (2 if spectral_pos_encoding else 0), out_channels=out_channels * 2, kernel_size=1, stride=1, padding=0, groups=self.groups, bias=False)
        self.bn = torch.nn.BatchNorm2d(out_channels * 2)
        self.relu = torch.nn.ReLU(inplace=True)
        self.use_se = use_se
        if use_se:
            if se_kwargs is None:
                se_kwargs = {}
            self.se = SELayer(self.conv_layer.in_channels, **se_kwargs)
        self.spatial_scale_factor = spatial_scale_factor
        self.spatial_scale_mode = spatial_scale_mode
        self.spectral_pos_encoding = spectral_pos_encoding
        self.ffc3d = ffc3d
        self.fft_norm = fft_norm

    def forward(self, x):
        batch = x.shape[0]
        if self.spatial_scale_factor is not None:
            orig_size = x.shape[-2:]
            x = F.interpolate(x, scale_factor=self.spatial_scale_factor, mode=self.spatial_scale_mode, align_corners=False)
        r_size = x.size()
        fft_dim = (-3, -2, -1) if self.ffc3d else (-2, -1)
        ffted = torch.fft.rfftn(x, dim=fft_dim, norm=self.fft_norm)
        ffted = torch.stack((ffted.real, ffted.imag), dim=-1)
        ffted = ffted.permute(0, 1, 4, 2, 3).contiguous()
        ffted = ffted.view((batch, -1) + ffted.size()[3:])
        if self.spectral_pos_encoding:
            height, width = ffted.shape[-2:]
            coords_vert = torch.linspace(0, 1, height)[None, None, :, None].expand(batch, 1, height, width).to(ffted)
            coords_hor = torch.linspace(0, 1, width)[None, None, None, :].expand(batch, 1, height, width).to(ffted)
            ffted = torch.cat((coords_vert, coords_hor, ffted), dim=1)
        if self.use_se:
            ffted = self.se(ffted)
        ffted = self.conv_layer(ffted)
        ffted = self.relu(self.bn(ffted))
        ffted = ffted.view((batch, -1, 2) + ffted.size()[2:]).permute(0, 1, 3, 4, 2).contiguous()
        ffted = torch.complex(ffted[..., 0], ffted[..., 1])
        ifft_shape_slice = x.shape[-3:] if self.ffc3d else x.shape[-2:]
        output = torch.fft.irfftn(ffted, s=ifft_shape_slice, dim=fft_dim, norm=self.fft_norm)
        if self.spatial_scale_factor is not None:
            output = F.interpolate(output, size=orig_size, mode=self.spatial_scale_mode, align_corners=False)
        return output

def __init__(self, in_channels, out_channels, groups=1, spatial_scale_factor=None, spatial_scale_mode='bilinear', spectral_pos_encoding=False, use_se=False, se_kwargs=None, ffc3d=False, fft_norm='ortho'):
    super(FourierUnit, self).__init__()
    self.groups = groups
    self.conv_layer = torch.nn.Conv2d(in_channels=in_channels * 2 + (2 if spectral_pos_encoding else 0), out_channels=out_channels * 2, kernel_size=1, stride=1, padding=0, groups=self.groups, bias=False)
    self.bn = torch.nn.BatchNorm2d(out_channels * 2)
    self.relu = torch.nn.ReLU(inplace=True)
    self.use_se = use_se
    if use_se:
        if se_kwargs is None:
            se_kwargs = {}
        self.se = SELayer(self.conv_layer.in_channels, **se_kwargs)
    self.spatial_scale_factor = spatial_scale_factor
    self.spatial_scale_mode = spatial_scale_mode
    self.spectral_pos_encoding = spectral_pos_encoding
    self.ffc3d = ffc3d
    self.fft_norm = fft_norm

class SpectralTransform(nn.Module):

    def __init__(self, in_channels, out_channels, stride=1, groups=1, enable_lfu=True, **fu_kwargs):
        super(SpectralTransform, self).__init__()
        self.enable_lfu = enable_lfu
        if stride == 2:
            self.downsample = nn.AvgPool2d(kernel_size=(2, 2), stride=2)
        else:
            self.downsample = nn.Identity()
        self.stride = stride
        self.conv1 = nn.Sequential(nn.Conv2d(in_channels, out_channels // 2, kernel_size=1, groups=groups, bias=False), nn.BatchNorm2d(out_channels // 2), nn.ReLU(inplace=True))
        self.fu = FourierUnit(out_channels // 2, out_channels // 2, groups, **fu_kwargs)
        if self.enable_lfu:
            self.lfu = FourierUnit(out_channels // 2, out_channels // 2, groups)
        self.conv2 = torch.nn.Conv2d(out_channels // 2, out_channels, kernel_size=1, groups=groups, bias=False)

    def forward(self, x):
        x = self.downsample(x)
        x = self.conv1(x)
        output = self.fu(x)
        if self.enable_lfu:
            n, c, h, w = x.shape
            split_no = 2
            split_s = h // split_no
            xs = torch.cat(torch.split(x[:, :c // 4], split_s, dim=-2), dim=1).contiguous()
            xs = torch.cat(torch.split(xs, split_s, dim=-1), dim=1).contiguous()
            xs = self.lfu(xs)
            xs = xs.repeat(1, 1, split_no, split_no).contiguous()
        else:
            xs = 0
        output = self.conv2(x + output + xs)
        return output

def __init__(self, in_channels, out_channels, stride=1, groups=1, enable_lfu=True, **fu_kwargs):
    super(SpectralTransform, self).__init__()
    self.enable_lfu = enable_lfu
    if stride == 2:
        self.downsample = nn.AvgPool2d(kernel_size=(2, 2), stride=2)
    else:
        self.downsample = nn.Identity()
    self.stride = stride
    self.conv1 = nn.Sequential(nn.Conv2d(in_channels, out_channels // 2, kernel_size=1, groups=groups, bias=False), nn.BatchNorm2d(out_channels // 2), nn.ReLU(inplace=True))
    self.fu = FourierUnit(out_channels // 2, out_channels // 2, groups, **fu_kwargs)
    if self.enable_lfu:
        self.lfu = FourierUnit(out_channels // 2, out_channels // 2, groups)
    self.conv2 = torch.nn.Conv2d(out_channels // 2, out_channels, kernel_size=1, groups=groups, bias=False)

class FFC(nn.Module):

    def __init__(self, in_channels, out_channels, kernel_size, ratio_gin, ratio_gout, stride=1, padding=0, dilation=1, groups=1, bias=False, enable_lfu=True, padding_type='reflect', gated=False, **spectral_kwargs):
        super(FFC, self).__init__()
        assert stride == 1 or stride == 2, 'Stride should be 1 or 2.'
        self.stride = stride
        in_cg = int(in_channels * ratio_gin)
        in_cl = in_channels - in_cg
        out_cg = int(out_channels * ratio_gout)
        out_cl = out_channels - out_cg
        self.ratio_gin = ratio_gin
        self.ratio_gout = ratio_gout
        self.global_in_num = in_cg
        module = nn.Identity if in_cl == 0 or out_cl == 0 else nn.Conv2d
        self.convl2l = module(in_cl, out_cl, kernel_size, stride, padding, dilation, groups, bias, padding_mode=padding_type)
        module = nn.Identity if in_cl == 0 or out_cg == 0 else nn.Conv2d
        self.convl2g = module(in_cl, out_cg, kernel_size, stride, padding, dilation, groups, bias, padding_mode=padding_type)
        module = nn.Identity if in_cg == 0 or out_cl == 0 else nn.Conv2d
        self.convg2l = module(in_cg, out_cl, kernel_size, stride, padding, dilation, groups, bias, padding_mode=padding_type)
        module = nn.Identity if in_cg == 0 or out_cg == 0 else SpectralTransform
        self.convg2g = module(in_cg, out_cg, stride, 1 if groups == 1 else groups // 2, enable_lfu, **spectral_kwargs)
        self.gated = gated
        module = nn.Identity if in_cg == 0 or out_cl == 0 or (not self.gated) else nn.Conv2d
        self.gate = module(in_channels, 2, 1)

    def forward(self, x):
        x_l, x_g = x if type(x) is tuple else (x, 0)
        out_xl, out_xg = (0, 0)
        if self.gated:
            total_input_parts = [x_l]
            if torch.is_tensor(x_g):
                total_input_parts.append(x_g)
            total_input = torch.cat(total_input_parts, dim=1)
            gates = torch.sigmoid(self.gate(total_input))
            g2l_gate, l2g_gate = gates.chunk(2, dim=1)
        else:
            g2l_gate, l2g_gate = (1, 1)
        if self.ratio_gout != 1:
            out_xl = self.convl2l(x_l) + self.convg2l(x_g) * g2l_gate
        if self.ratio_gout != 0:
            out_xg = self.convl2g(x_l) * l2g_gate + self.convg2g(x_g)
        return (out_xl, out_xg)

def __init__(self, in_channels, out_channels, kernel_size, ratio_gin, ratio_gout, stride=1, padding=0, dilation=1, groups=1, bias=False, enable_lfu=True, padding_type='reflect', gated=False, **spectral_kwargs):
    super(FFC, self).__init__()
    assert stride == 1 or stride == 2, 'Stride should be 1 or 2.'
    self.stride = stride
    in_cg = int(in_channels * ratio_gin)
    in_cl = in_channels - in_cg
    out_cg = int(out_channels * ratio_gout)
    out_cl = out_channels - out_cg
    self.ratio_gin = ratio_gin
    self.ratio_gout = ratio_gout
    self.global_in_num = in_cg
    module = nn.Identity if in_cl == 0 or out_cl == 0 else nn.Conv2d
    self.convl2l = module(in_cl, out_cl, kernel_size, stride, padding, dilation, groups, bias, padding_mode=padding_type)
    module = nn.Identity if in_cl == 0 or out_cg == 0 else nn.Conv2d
    self.convl2g = module(in_cl, out_cg, kernel_size, stride, padding, dilation, groups, bias, padding_mode=padding_type)
    module = nn.Identity if in_cg == 0 or out_cl == 0 else nn.Conv2d
    self.convg2l = module(in_cg, out_cl, kernel_size, stride, padding, dilation, groups, bias, padding_mode=padding_type)
    module = nn.Identity if in_cg == 0 or out_cg == 0 else SpectralTransform
    self.convg2g = module(in_cg, out_cg, stride, 1 if groups == 1 else groups // 2, enable_lfu, **spectral_kwargs)
    self.gated = gated
    module = nn.Identity if in_cg == 0 or out_cl == 0 or (not self.gated) else nn.Conv2d
    self.gate = module(in_channels, 2, 1)

class FFCResnetBlock(nn.Module):

    def __init__(self, dim, padding_type, norm_layer, activation_layer=nn.ReLU, dilation=1, spatial_transform_kwargs=None, inline=False, **conv_kwargs):
        super().__init__()
        self.conv1 = FFC_BN_ACT(dim, dim, kernel_size=3, padding=dilation, dilation=dilation, norm_layer=norm_layer, activation_layer=activation_layer, padding_type=padding_type, **conv_kwargs)
        self.conv2 = FFC_BN_ACT(dim, dim, kernel_size=3, padding=dilation, dilation=dilation, norm_layer=norm_layer, activation_layer=activation_layer, padding_type=padding_type, **conv_kwargs)
        if spatial_transform_kwargs is not None:
            self.conv1 = LearnableSpatialTransformWrapper(self.conv1, **spatial_transform_kwargs)
            self.conv2 = LearnableSpatialTransformWrapper(self.conv2, **spatial_transform_kwargs)
        self.inline = inline

    def forward(self, x):
        if self.inline:
            x_l, x_g = (x[:, :-self.conv1.ffc.global_in_num], x[:, -self.conv1.ffc.global_in_num:])
        else:
            x_l, x_g = x if type(x) is tuple else (x, 0)
        id_l, id_g = (x_l, x_g)
        x_l, x_g = self.conv1((x_l, x_g))
        x_l, x_g = self.conv2((x_l, x_g))
        x_l, x_g = (id_l + x_l, id_g + x_g)
        out = (x_l, x_g)
        if self.inline:
            out = torch.cat(out, dim=1)
        return out

def __init__(self, dim, padding_type, norm_layer, activation_layer=nn.ReLU, dilation=1, spatial_transform_kwargs=None, inline=False, **conv_kwargs):
    super().__init__()
    self.conv1 = FFC_BN_ACT(dim, dim, kernel_size=3, padding=dilation, dilation=dilation, norm_layer=norm_layer, activation_layer=activation_layer, padding_type=padding_type, **conv_kwargs)
    self.conv2 = FFC_BN_ACT(dim, dim, kernel_size=3, padding=dilation, dilation=dilation, norm_layer=norm_layer, activation_layer=activation_layer, padding_type=padding_type, **conv_kwargs)
    if spatial_transform_kwargs is not None:
        self.conv1 = LearnableSpatialTransformWrapper(self.conv1, **spatial_transform_kwargs)
        self.conv2 = LearnableSpatialTransformWrapper(self.conv2, **spatial_transform_kwargs)
    self.inline = inline

class FFCResNetGenerator(nn.Module):

    def __init__(self, input_nc, output_nc, ngf=64, n_downsampling=3, n_blocks=9, norm_layer=nn.BatchNorm2d, padding_type='reflect', activation_layer=nn.ReLU, up_norm_layer=nn.BatchNorm2d, up_activation=nn.ReLU(True), init_conv_kwargs={}, downsample_conv_kwargs={}, resnet_conv_kwargs={}, spatial_transform_layers=None, spatial_transform_kwargs={}, add_out_act=True, max_features=1024, out_ffc=False, out_ffc_kwargs={}):
        assert n_blocks >= 0
        super().__init__()
        model = [nn.ReflectionPad2d(3), FFC_BN_ACT(input_nc, ngf, kernel_size=7, padding=0, norm_layer=norm_layer, activation_layer=activation_layer, **init_conv_kwargs)]
        for i in range(n_downsampling):
            mult = 2 ** i
            if i == n_downsampling - 1:
                cur_conv_kwargs = dict(downsample_conv_kwargs)
                cur_conv_kwargs['ratio_gout'] = resnet_conv_kwargs.get('ratio_gin', 0)
            else:
                cur_conv_kwargs = downsample_conv_kwargs
            model += [FFC_BN_ACT(min(max_features, ngf * mult), min(max_features, ngf * mult * 2), kernel_size=3, stride=2, padding=1, norm_layer=norm_layer, activation_layer=activation_layer, **cur_conv_kwargs)]
        mult = 2 ** n_downsampling
        feats_num_bottleneck = min(max_features, ngf * mult)
        for i in range(n_blocks):
            cur_resblock = FFCResnetBlock(feats_num_bottleneck, padding_type=padding_type, activation_layer=activation_layer, norm_layer=norm_layer, **resnet_conv_kwargs)
            if spatial_transform_layers is not None and i in spatial_transform_layers:
                cur_resblock = LearnableSpatialTransformWrapper(cur_resblock, **spatial_transform_kwargs)
            model += [cur_resblock]
        model += [ConcatTupleLayer()]
        for i in range(n_downsampling):
            mult = 2 ** (n_downsampling - i)
            model += [nn.ConvTranspose2d(min(max_features, ngf * mult), min(max_features, int(ngf * mult / 2)), kernel_size=3, stride=2, padding=1, output_padding=1), up_norm_layer(min(max_features, int(ngf * mult / 2))), up_activation]
        if out_ffc:
            model += [FFCResnetBlock(ngf, padding_type=padding_type, activation_layer=activation_layer, norm_layer=norm_layer, inline=True, **out_ffc_kwargs)]
        model += [nn.ReflectionPad2d(3), nn.Conv2d(ngf, output_nc, kernel_size=7, padding=0)]
        if add_out_act:
            model.append(get_activation('tanh' if add_out_act is True else add_out_act))
        self.model = nn.Sequential(*model)

    def forward(self, input):
        return self.model(input)

def __init__(self, input_nc, output_nc, ngf=64, n_downsampling=3, n_blocks=9, norm_layer=nn.BatchNorm2d, padding_type='reflect', activation_layer=nn.ReLU, up_norm_layer=nn.BatchNorm2d, up_activation=nn.ReLU(True), init_conv_kwargs={}, downsample_conv_kwargs={}, resnet_conv_kwargs={}, spatial_transform_layers=None, spatial_transform_kwargs={}, add_out_act=True, max_features=1024, out_ffc=False, out_ffc_kwargs={}):
    assert n_blocks >= 0
    super().__init__()
    model = [nn.ReflectionPad2d(3), FFC_BN_ACT(input_nc, ngf, kernel_size=7, padding=0, norm_layer=norm_layer, activation_layer=activation_layer, **init_conv_kwargs)]
    for i in range(n_downsampling):
        mult = 2 ** i
        if i == n_downsampling - 1:
            cur_conv_kwargs = dict(downsample_conv_kwargs)
            cur_conv_kwargs['ratio_gout'] = resnet_conv_kwargs.get('ratio_gin', 0)
        else:
            cur_conv_kwargs = downsample_conv_kwargs
        model += [FFC_BN_ACT(min(max_features, ngf * mult), min(max_features, ngf * mult * 2), kernel_size=3, stride=2, padding=1, norm_layer=norm_layer, activation_layer=activation_layer, **cur_conv_kwargs)]
    mult = 2 ** n_downsampling
    feats_num_bottleneck = min(max_features, ngf * mult)
    for i in range(n_blocks):
        cur_resblock = FFCResnetBlock(feats_num_bottleneck, padding_type=padding_type, activation_layer=activation_layer, norm_layer=norm_layer, **resnet_conv_kwargs)
        if spatial_transform_layers is not None and i in spatial_transform_layers:
            cur_resblock = LearnableSpatialTransformWrapper(cur_resblock, **spatial_transform_kwargs)
        model += [cur_resblock]
    model += [ConcatTupleLayer()]
    for i in range(n_downsampling):
        mult = 2 ** (n_downsampling - i)
        model += [nn.ConvTranspose2d(min(max_features, ngf * mult), min(max_features, int(ngf * mult / 2)), kernel_size=3, stride=2, padding=1, output_padding=1), up_norm_layer(min(max_features, int(ngf * mult / 2))), up_activation]
    if out_ffc:
        model += [FFCResnetBlock(ngf, padding_type=padding_type, activation_layer=activation_layer, norm_layer=norm_layer, inline=True, **out_ffc_kwargs)]
    model += [nn.ReflectionPad2d(3), nn.Conv2d(ngf, output_nc, kernel_size=7, padding=0)]
    if add_out_act:
        model.append(get_activation('tanh' if add_out_act is True else add_out_act))
    self.model = nn.Sequential(*model)

class FFCNLayerDiscriminator(BaseDiscriminator):

    def __init__(self, input_nc, ndf=64, n_layers=3, norm_layer=nn.BatchNorm2d, max_features=512, init_conv_kwargs={}, conv_kwargs={}):
        super().__init__()
        self.n_layers = n_layers

        def _act_ctor(inplace=True):
            return nn.LeakyReLU(negative_slope=0.2, inplace=inplace)
        kw = 3
        padw = int(np.ceil((kw - 1.0) / 2))
        sequence = [[FFC_BN_ACT(input_nc, ndf, kernel_size=kw, padding=padw, norm_layer=norm_layer, activation_layer=_act_ctor, **init_conv_kwargs)]]
        nf = ndf
        for n in range(1, n_layers):
            nf_prev = nf
            nf = min(nf * 2, max_features)
            cur_model = [FFC_BN_ACT(nf_prev, nf, kernel_size=kw, stride=2, padding=padw, norm_layer=norm_layer, activation_layer=_act_ctor, **conv_kwargs)]
            sequence.append(cur_model)
        nf_prev = nf
        nf = min(nf * 2, 512)
        cur_model = [FFC_BN_ACT(nf_prev, nf, kernel_size=kw, stride=1, padding=padw, norm_layer=norm_layer, activation_layer=lambda *args, **kwargs: nn.LeakyReLU(*args, negative_slope=0.2, **kwargs), **conv_kwargs), ConcatTupleLayer()]
        sequence.append(cur_model)
        sequence += [[nn.Conv2d(nf, 1, kernel_size=kw, stride=1, padding=padw)]]
        for n in range(len(sequence)):
            setattr(self, 'model' + str(n), nn.Sequential(*sequence[n]))

    def get_all_activations(self, x):
        res = [x]
        for n in range(self.n_layers + 2):
            model = getattr(self, 'model' + str(n))
            res.append(model(res[-1]))
        return res[1:]

    def forward(self, x):
        act = self.get_all_activations(x)
        feats = []
        for out in act[:-1]:
            if isinstance(out, tuple):
                if torch.is_tensor(out[1]):
                    out = torch.cat(out, dim=1)
                else:
                    out = out[0]
            feats.append(out)
        return (act[-1], feats)

def __init__(self, input_nc, ndf=64, n_layers=3, norm_layer=nn.BatchNorm2d, max_features=512, init_conv_kwargs={}, conv_kwargs={}):
    super().__init__()
    self.n_layers = n_layers

    def _act_ctor(inplace=True):
        return nn.LeakyReLU(negative_slope=0.2, inplace=inplace)
    kw = 3
    padw = int(np.ceil((kw - 1.0) / 2))
    sequence = [[FFC_BN_ACT(input_nc, ndf, kernel_size=kw, padding=padw, norm_layer=norm_layer, activation_layer=_act_ctor, **init_conv_kwargs)]]
    nf = ndf
    for n in range(1, n_layers):
        nf_prev = nf
        nf = min(nf * 2, max_features)
        cur_model = [FFC_BN_ACT(nf_prev, nf, kernel_size=kw, stride=2, padding=padw, norm_layer=norm_layer, activation_layer=_act_ctor, **conv_kwargs)]
        sequence.append(cur_model)
    nf_prev = nf
    nf = min(nf * 2, 512)
    cur_model = [FFC_BN_ACT(nf_prev, nf, kernel_size=kw, stride=1, padding=padw, norm_layer=norm_layer, activation_layer=lambda *args, **kwargs: nn.LeakyReLU(*args, negative_slope=0.2, **kwargs), **conv_kwargs), ConcatTupleLayer()]
    sequence.append(cur_model)
    sequence += [[nn.Conv2d(nf, 1, kernel_size=kw, stride=1, padding=padw)]]
    for n in range(len(sequence)):
        setattr(self, 'model' + str(n), nn.Sequential(*sequence[n]))

def _act_ctor(inplace=True):
    return nn.LeakyReLU(negative_slope=0.2, inplace=inplace)

class SELayer(nn.Module):

    def __init__(self, channel, reduction=16):
        super(SELayer, self).__init__()
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Sequential(nn.Linear(channel, channel // reduction, bias=False), nn.ReLU(inplace=True), nn.Linear(channel // reduction, channel, bias=False), nn.Sigmoid())

    def forward(self, x):
        b, c, _, _ = x.size()
        y = self.avg_pool(x).view(b, c)
        y = self.fc(y).view(b, c, 1, 1)
        res = x * y.expand_as(x)
        return res

def __init__(self, channel, reduction=16):
    super(SELayer, self).__init__()
    self.avg_pool = nn.AdaptiveAvgPool2d(1)
    self.fc = nn.Sequential(nn.Linear(channel, channel // reduction, bias=False), nn.ReLU(inplace=True), nn.Linear(channel // reduction, channel, bias=False), nn.Sigmoid())

class MultidilatedConv(nn.Module):

    def __init__(self, in_dim, out_dim, kernel_size, dilation_num=3, comb_mode='sum', equal_dim=True, shared_weights=False, padding=1, min_dilation=1, shuffle_in_channels=False, use_depthwise=False, **kwargs):
        super().__init__()
        convs = []
        self.equal_dim = equal_dim
        assert comb_mode in ('cat_out', 'sum', 'cat_in', 'cat_both'), comb_mode
        if comb_mode in ('cat_out', 'cat_both'):
            self.cat_out = True
            if equal_dim:
                assert out_dim % dilation_num == 0
                out_dims = [out_dim // dilation_num] * dilation_num
                self.index = sum([[i + j * out_dims[0] for j in range(dilation_num)] for i in range(out_dims[0])], [])
            else:
                out_dims = [out_dim // 2 ** (i + 1) for i in range(dilation_num - 1)]
                out_dims.append(out_dim - sum(out_dims))
                index = []
                starts = [0] + out_dims[:-1]
                lengths = [out_dims[i] // out_dims[-1] for i in range(dilation_num)]
                for i in range(out_dims[-1]):
                    for j in range(dilation_num):
                        index += list(range(starts[j], starts[j] + lengths[j]))
                        starts[j] += lengths[j]
                self.index = index
                assert len(index) == out_dim
            self.out_dims = out_dims
        else:
            self.cat_out = False
            self.out_dims = [out_dim] * dilation_num
        if comb_mode in ('cat_in', 'cat_both'):
            if equal_dim:
                assert in_dim % dilation_num == 0
                in_dims = [in_dim // dilation_num] * dilation_num
            else:
                in_dims = [in_dim // 2 ** (i + 1) for i in range(dilation_num - 1)]
                in_dims.append(in_dim - sum(in_dims))
            self.in_dims = in_dims
            self.cat_in = True
        else:
            self.cat_in = False
            self.in_dims = [in_dim] * dilation_num
        conv_type = DepthWiseSeperableConv if use_depthwise else nn.Conv2d
        dilation = min_dilation
        for i in range(dilation_num):
            if isinstance(padding, int):
                cur_padding = padding * dilation
            else:
                cur_padding = padding[i]
            convs.append(conv_type(self.in_dims[i], self.out_dims[i], kernel_size, padding=cur_padding, dilation=dilation, **kwargs))
            if i > 0 and shared_weights:
                convs[-1].weight = convs[0].weight
                convs[-1].bias = convs[0].bias
            dilation *= 2
        self.convs = nn.ModuleList(convs)
        self.shuffle_in_channels = shuffle_in_channels
        if self.shuffle_in_channels:
            in_channels_permute = list(range(in_dim))
            random.shuffle(in_channels_permute)
            self.register_buffer('in_channels_permute', torch.tensor(in_channels_permute))

    def forward(self, x):
        if self.shuffle_in_channels:
            x = x[:, self.in_channels_permute]
        outs = []
        if self.cat_in:
            if self.equal_dim:
                x = x.chunk(len(self.convs), dim=1)
            else:
                new_x = []
                start = 0
                for dim in self.in_dims:
                    new_x.append(x[:, start:start + dim])
                    start += dim
                x = new_x
        for i, conv in enumerate(self.convs):
            if self.cat_in:
                input = x[i]
            else:
                input = x
            outs.append(conv(input))
        if self.cat_out:
            out = torch.cat(outs, dim=1)[:, self.index]
        else:
            out = sum(outs)
        return out

def __init__(self, in_dim, out_dim, kernel_size, dilation_num=3, comb_mode='sum', equal_dim=True, shared_weights=False, padding=1, min_dilation=1, shuffle_in_channels=False, use_depthwise=False, **kwargs):
    super().__init__()
    convs = []
    self.equal_dim = equal_dim
    assert comb_mode in ('cat_out', 'sum', 'cat_in', 'cat_both'), comb_mode
    if comb_mode in ('cat_out', 'cat_both'):
        self.cat_out = True
        if equal_dim:
            assert out_dim % dilation_num == 0
            out_dims = [out_dim // dilation_num] * dilation_num
            self.index = sum([[i + j * out_dims[0] for j in range(dilation_num)] for i in range(out_dims[0])], [])
        else:
            out_dims = [out_dim // 2 ** (i + 1) for i in range(dilation_num - 1)]
            out_dims.append(out_dim - sum(out_dims))
            index = []
            starts = [0] + out_dims[:-1]
            lengths = [out_dims[i] // out_dims[-1] for i in range(dilation_num)]
            for i in range(out_dims[-1]):
                for j in range(dilation_num):
                    index += list(range(starts[j], starts[j] + lengths[j]))
                    starts[j] += lengths[j]
            self.index = index
            assert len(index) == out_dim
        self.out_dims = out_dims
    else:
        self.cat_out = False
        self.out_dims = [out_dim] * dilation_num
    if comb_mode in ('cat_in', 'cat_both'):
        if equal_dim:
            assert in_dim % dilation_num == 0
            in_dims = [in_dim // dilation_num] * dilation_num
        else:
            in_dims = [in_dim // 2 ** (i + 1) for i in range(dilation_num - 1)]
            in_dims.append(in_dim - sum(in_dims))
        self.in_dims = in_dims
        self.cat_in = True
    else:
        self.cat_in = False
        self.in_dims = [in_dim] * dilation_num
    conv_type = DepthWiseSeperableConv if use_depthwise else nn.Conv2d
    dilation = min_dilation
    for i in range(dilation_num):
        if isinstance(padding, int):
            cur_padding = padding * dilation
        else:
            cur_padding = padding[i]
        convs.append(conv_type(self.in_dims[i], self.out_dims[i], kernel_size, padding=cur_padding, dilation=dilation, **kwargs))
        if i > 0 and shared_weights:
            convs[-1].weight = convs[0].weight
            convs[-1].bias = convs[0].bias
        dilation *= 2
    self.convs = nn.ModuleList(convs)
    self.shuffle_in_channels = shuffle_in_channels
    if self.shuffle_in_channels:
        in_channels_permute = list(range(in_dim))
        random.shuffle(in_channels_permute)
        self.register_buffer('in_channels_permute', torch.tensor(in_channels_permute))

class Identity(nn.Module):

    def __init__(self):
        super().__init__()

    def forward(self, x):
        return x

def __init__(self):
    super().__init__()

class ResnetBlock(nn.Module):

    def __init__(self, dim, padding_type, norm_layer, activation=nn.ReLU(True), use_dropout=False, conv_kind='default', dilation=1, in_dim=None, groups=1, second_dilation=None):
        super(ResnetBlock, self).__init__()
        self.in_dim = in_dim
        self.dim = dim
        if second_dilation is None:
            second_dilation = dilation
        self.conv_block = self.build_conv_block(dim, padding_type, norm_layer, activation, use_dropout, conv_kind=conv_kind, dilation=dilation, in_dim=in_dim, groups=groups, second_dilation=second_dilation)
        if self.in_dim is not None:
            self.input_conv = nn.Conv2d(in_dim, dim, 1)
        self.out_channnels = dim

    def build_conv_block(self, dim, padding_type, norm_layer, activation, use_dropout, conv_kind='default', dilation=1, in_dim=None, groups=1, second_dilation=1):
        conv_layer = get_conv_block_ctor(conv_kind)
        conv_block = []
        p = 0
        if padding_type == 'reflect':
            conv_block += [nn.ReflectionPad2d(dilation)]
        elif padding_type == 'replicate':
            conv_block += [nn.ReplicationPad2d(dilation)]
        elif padding_type == 'zero':
            p = dilation
        else:
            raise NotImplementedError('padding [%s] is not implemented' % padding_type)
        if in_dim is None:
            in_dim = dim
        conv_block += [conv_layer(in_dim, dim, kernel_size=3, padding=p, dilation=dilation), norm_layer(dim), activation]
        if use_dropout:
            conv_block += [nn.Dropout(0.5)]
        p = 0
        if padding_type == 'reflect':
            conv_block += [nn.ReflectionPad2d(second_dilation)]
        elif padding_type == 'replicate':
            conv_block += [nn.ReplicationPad2d(second_dilation)]
        elif padding_type == 'zero':
            p = second_dilation
        else:
            raise NotImplementedError('padding [%s] is not implemented' % padding_type)
        conv_block += [conv_layer(dim, dim, kernel_size=3, padding=p, dilation=second_dilation, groups=groups), norm_layer(dim)]
        return nn.Sequential(*conv_block)

    def forward(self, x):
        x_before = x
        if self.in_dim is not None:
            x = self.input_conv(x)
        out = x + self.conv_block(x_before)
        return out

def __init__(self, dim, padding_type, norm_layer, activation=nn.ReLU(True), use_dropout=False, conv_kind='default', dilation=1, in_dim=None, groups=1, second_dilation=None):
    super(ResnetBlock, self).__init__()
    self.in_dim = in_dim
    self.dim = dim
    if second_dilation is None:
        second_dilation = dilation
    self.conv_block = self.build_conv_block(dim, padding_type, norm_layer, activation, use_dropout, conv_kind=conv_kind, dilation=dilation, in_dim=in_dim, groups=groups, second_dilation=second_dilation)
    if self.in_dim is not None:
        self.input_conv = nn.Conv2d(in_dim, dim, 1)
    self.out_channnels = dim

def build_conv_block(self, dim, padding_type, norm_layer, activation, use_dropout, conv_kind='default', dilation=1, in_dim=None, groups=1, second_dilation=1):
    conv_layer = get_conv_block_ctor(conv_kind)
    conv_block = []
    p = 0
    if padding_type == 'reflect':
        conv_block += [nn.ReflectionPad2d(dilation)]
    elif padding_type == 'replicate':
        conv_block += [nn.ReplicationPad2d(dilation)]
    elif padding_type == 'zero':
        p = dilation
    else:
        raise NotImplementedError('padding [%s] is not implemented' % padding_type)
    if in_dim is None:
        in_dim = dim
    conv_block += [conv_layer(in_dim, dim, kernel_size=3, padding=p, dilation=dilation), norm_layer(dim), activation]
    if use_dropout:
        conv_block += [nn.Dropout(0.5)]
    p = 0
    if padding_type == 'reflect':
        conv_block += [nn.ReflectionPad2d(second_dilation)]
    elif padding_type == 'replicate':
        conv_block += [nn.ReplicationPad2d(second_dilation)]
    elif padding_type == 'zero':
        p = second_dilation
    else:
        raise NotImplementedError('padding [%s] is not implemented' % padding_type)
    conv_block += [conv_layer(dim, dim, kernel_size=3, padding=p, dilation=second_dilation, groups=groups), norm_layer(dim)]
    return nn.Sequential(*conv_block)

class ResnetBlock5x5(nn.Module):

    def __init__(self, dim, padding_type, norm_layer, activation=nn.ReLU(True), use_dropout=False, conv_kind='default', dilation=1, in_dim=None, groups=1, second_dilation=None):
        super(ResnetBlock5x5, self).__init__()
        self.in_dim = in_dim
        self.dim = dim
        if second_dilation is None:
            second_dilation = dilation
        self.conv_block = self.build_conv_block(dim, padding_type, norm_layer, activation, use_dropout, conv_kind=conv_kind, dilation=dilation, in_dim=in_dim, groups=groups, second_dilation=second_dilation)
        if self.in_dim is not None:
            self.input_conv = nn.Conv2d(in_dim, dim, 1)
        self.out_channnels = dim

    def build_conv_block(self, dim, padding_type, norm_layer, activation, use_dropout, conv_kind='default', dilation=1, in_dim=None, groups=1, second_dilation=1):
        conv_layer = get_conv_block_ctor(conv_kind)
        conv_block = []
        p = 0
        if padding_type == 'reflect':
            conv_block += [nn.ReflectionPad2d(dilation * 2)]
        elif padding_type == 'replicate':
            conv_block += [nn.ReplicationPad2d(dilation * 2)]
        elif padding_type == 'zero':
            p = dilation * 2
        else:
            raise NotImplementedError('padding [%s] is not implemented' % padding_type)
        if in_dim is None:
            in_dim = dim
        conv_block += [conv_layer(in_dim, dim, kernel_size=5, padding=p, dilation=dilation), norm_layer(dim), activation]
        if use_dropout:
            conv_block += [nn.Dropout(0.5)]
        p = 0
        if padding_type == 'reflect':
            conv_block += [nn.ReflectionPad2d(second_dilation * 2)]
        elif padding_type == 'replicate':
            conv_block += [nn.ReplicationPad2d(second_dilation * 2)]
        elif padding_type == 'zero':
            p = second_dilation * 2
        else:
            raise NotImplementedError('padding [%s] is not implemented' % padding_type)
        conv_block += [conv_layer(dim, dim, kernel_size=5, padding=p, dilation=second_dilation, groups=groups), norm_layer(dim)]
        return nn.Sequential(*conv_block)

    def forward(self, x):
        x_before = x
        if self.in_dim is not None:
            x = self.input_conv(x)
        out = x + self.conv_block(x_before)
        return out

def __init__(self, dim, padding_type, norm_layer, activation=nn.ReLU(True), use_dropout=False, conv_kind='default', dilation=1, in_dim=None, groups=1, second_dilation=None):
    super(ResnetBlock5x5, self).__init__()
    self.in_dim = in_dim
    self.dim = dim
    if second_dilation is None:
        second_dilation = dilation
    self.conv_block = self.build_conv_block(dim, padding_type, norm_layer, activation, use_dropout, conv_kind=conv_kind, dilation=dilation, in_dim=in_dim, groups=groups, second_dilation=second_dilation)
    if self.in_dim is not None:
        self.input_conv = nn.Conv2d(in_dim, dim, 1)
    self.out_channnels = dim

def build_conv_block(self, dim, padding_type, norm_layer, activation, use_dropout, conv_kind='default', dilation=1, in_dim=None, groups=1, second_dilation=1):
    conv_layer = get_conv_block_ctor(conv_kind)
    conv_block = []
    p = 0
    if padding_type == 'reflect':
        conv_block += [nn.ReflectionPad2d(dilation * 2)]
    elif padding_type == 'replicate':
        conv_block += [nn.ReplicationPad2d(dilation * 2)]
    elif padding_type == 'zero':
        p = dilation * 2
    else:
        raise NotImplementedError('padding [%s] is not implemented' % padding_type)
    if in_dim is None:
        in_dim = dim
    conv_block += [conv_layer(in_dim, dim, kernel_size=5, padding=p, dilation=dilation), norm_layer(dim), activation]
    if use_dropout:
        conv_block += [nn.Dropout(0.5)]
    p = 0
    if padding_type == 'reflect':
        conv_block += [nn.ReflectionPad2d(second_dilation * 2)]
    elif padding_type == 'replicate':
        conv_block += [nn.ReplicationPad2d(second_dilation * 2)]
    elif padding_type == 'zero':
        p = second_dilation * 2
    else:
        raise NotImplementedError('padding [%s] is not implemented' % padding_type)
    conv_block += [conv_layer(dim, dim, kernel_size=5, padding=p, dilation=second_dilation, groups=groups), norm_layer(dim)]
    return nn.Sequential(*conv_block)

class MultidilatedResnetBlock(nn.Module):

    def __init__(self, dim, padding_type, conv_layer, norm_layer, activation=nn.ReLU(True), use_dropout=False):
        super().__init__()
        self.conv_block = self.build_conv_block(dim, padding_type, conv_layer, norm_layer, activation, use_dropout)

    def build_conv_block(self, dim, padding_type, conv_layer, norm_layer, activation, use_dropout, dilation=1):
        conv_block = []
        conv_block += [conv_layer(dim, dim, kernel_size=3, padding_mode=padding_type), norm_layer(dim), activation]
        if use_dropout:
            conv_block += [nn.Dropout(0.5)]
        conv_block += [conv_layer(dim, dim, kernel_size=3, padding_mode=padding_type), norm_layer(dim)]
        return nn.Sequential(*conv_block)

    def forward(self, x):
        out = x + self.conv_block(x)
        return out

def __init__(self, dim, padding_type, conv_layer, norm_layer, activation=nn.ReLU(True), use_dropout=False):
    super().__init__()
    self.conv_block = self.build_conv_block(dim, padding_type, conv_layer, norm_layer, activation, use_dropout)

def build_conv_block(self, dim, padding_type, conv_layer, norm_layer, activation, use_dropout, dilation=1):
    conv_block = []
    conv_block += [conv_layer(dim, dim, kernel_size=3, padding_mode=padding_type), norm_layer(dim), activation]
    if use_dropout:
        conv_block += [nn.Dropout(0.5)]
    conv_block += [conv_layer(dim, dim, kernel_size=3, padding_mode=padding_type), norm_layer(dim)]
    return nn.Sequential(*conv_block)

class MultiDilatedGlobalGenerator(nn.Module):

    def __init__(self, input_nc, output_nc, ngf=64, n_downsampling=3, n_blocks=3, norm_layer=nn.BatchNorm2d, padding_type='reflect', conv_kind='default', deconv_kind='convtranspose', activation=nn.ReLU(True), up_norm_layer=nn.BatchNorm2d, affine=None, up_activation=nn.ReLU(True), add_out_act=True, max_features=1024, multidilation_kwargs={}, ffc_positions=None, ffc_kwargs={}):
        assert n_blocks >= 0
        super().__init__()
        conv_layer = get_conv_block_ctor(conv_kind)
        resnet_conv_layer = functools.partial(get_conv_block_ctor('multidilated'), **multidilation_kwargs)
        norm_layer = get_norm_layer(norm_layer)
        if affine is not None:
            norm_layer = partial(norm_layer, affine=affine)
        up_norm_layer = get_norm_layer(up_norm_layer)
        if affine is not None:
            up_norm_layer = partial(up_norm_layer, affine=affine)
        model = [nn.ReflectionPad2d(3), conv_layer(input_nc, ngf, kernel_size=7, padding=0), norm_layer(ngf), activation]
        identity = Identity()
        for i in range(n_downsampling):
            mult = 2 ** i
            model += [conv_layer(min(max_features, ngf * mult), min(max_features, ngf * mult * 2), kernel_size=3, stride=2, padding=1), norm_layer(min(max_features, ngf * mult * 2)), activation]
        mult = 2 ** n_downsampling
        feats_num_bottleneck = min(max_features, ngf * mult)
        for i in range(n_blocks):
            if ffc_positions is not None and i in ffc_positions:
                model += [FFCResnetBlock(feats_num_bottleneck, padding_type, norm_layer, activation_layer=nn.ReLU, inline=True, **ffc_kwargs)]
            model += [MultidilatedResnetBlock(feats_num_bottleneck, padding_type=padding_type, conv_layer=resnet_conv_layer, activation=activation, norm_layer=norm_layer)]
        for i in range(n_downsampling):
            mult = 2 ** (n_downsampling - i)
            model += deconv_factory(deconv_kind, ngf, mult, up_norm_layer, up_activation, max_features)
        model += [nn.ReflectionPad2d(3), nn.Conv2d(ngf, output_nc, kernel_size=7, padding=0)]
        if add_out_act:
            model.append(get_activation('tanh' if add_out_act is True else add_out_act))
        self.model = nn.Sequential(*model)

    def forward(self, input):
        return self.model(input)

def __init__(self, input_nc, output_nc, ngf=64, n_downsampling=3, n_blocks=3, norm_layer=nn.BatchNorm2d, padding_type='reflect', conv_kind='default', deconv_kind='convtranspose', activation=nn.ReLU(True), up_norm_layer=nn.BatchNorm2d, affine=None, up_activation=nn.ReLU(True), add_out_act=True, max_features=1024, multidilation_kwargs={}, ffc_positions=None, ffc_kwargs={}):
    assert n_blocks >= 0
    super().__init__()
    conv_layer = get_conv_block_ctor(conv_kind)
    resnet_conv_layer = functools.partial(get_conv_block_ctor('multidilated'), **multidilation_kwargs)
    norm_layer = get_norm_layer(norm_layer)
    if affine is not None:
        norm_layer = partial(norm_layer, affine=affine)
    up_norm_layer = get_norm_layer(up_norm_layer)
    if affine is not None:
        up_norm_layer = partial(up_norm_layer, affine=affine)
    model = [nn.ReflectionPad2d(3), conv_layer(input_nc, ngf, kernel_size=7, padding=0), norm_layer(ngf), activation]
    identity = Identity()
    for i in range(n_downsampling):
        mult = 2 ** i
        model += [conv_layer(min(max_features, ngf * mult), min(max_features, ngf * mult * 2), kernel_size=3, stride=2, padding=1), norm_layer(min(max_features, ngf * mult * 2)), activation]
    mult = 2 ** n_downsampling
    feats_num_bottleneck = min(max_features, ngf * mult)
    for i in range(n_blocks):
        if ffc_positions is not None and i in ffc_positions:
            model += [FFCResnetBlock(feats_num_bottleneck, padding_type, norm_layer, activation_layer=nn.ReLU, inline=True, **ffc_kwargs)]
        model += [MultidilatedResnetBlock(feats_num_bottleneck, padding_type=padding_type, conv_layer=resnet_conv_layer, activation=activation, norm_layer=norm_layer)]
    for i in range(n_downsampling):
        mult = 2 ** (n_downsampling - i)
        model += deconv_factory(deconv_kind, ngf, mult, up_norm_layer, up_activation, max_features)
    model += [nn.ReflectionPad2d(3), nn.Conv2d(ngf, output_nc, kernel_size=7, padding=0)]
    if add_out_act:
        model.append(get_activation('tanh' if add_out_act is True else add_out_act))
    self.model = nn.Sequential(*model)

class ConfigGlobalGenerator(nn.Module):

    def __init__(self, input_nc, output_nc, ngf=64, n_downsampling=3, n_blocks=3, norm_layer=nn.BatchNorm2d, padding_type='reflect', conv_kind='default', deconv_kind='convtranspose', activation=nn.ReLU(True), up_norm_layer=nn.BatchNorm2d, affine=None, up_activation=nn.ReLU(True), add_out_act=True, max_features=1024, manual_block_spec=[], resnet_block_kind='multidilatedresnetblock', resnet_conv_kind='multidilated', resnet_dilation=1, multidilation_kwargs={}):
        assert n_blocks >= 0
        super().__init__()
        conv_layer = get_conv_block_ctor(conv_kind)
        resnet_conv_layer = functools.partial(get_conv_block_ctor(resnet_conv_kind), **multidilation_kwargs)
        norm_layer = get_norm_layer(norm_layer)
        if affine is not None:
            norm_layer = partial(norm_layer, affine=affine)
        up_norm_layer = get_norm_layer(up_norm_layer)
        if affine is not None:
            up_norm_layer = partial(up_norm_layer, affine=affine)
        model = [nn.ReflectionPad2d(3), conv_layer(input_nc, ngf, kernel_size=7, padding=0), norm_layer(ngf), activation]
        identity = Identity()
        for i in range(n_downsampling):
            mult = 2 ** i
            model += [conv_layer(min(max_features, ngf * mult), min(max_features, ngf * mult * 2), kernel_size=3, stride=2, padding=1), norm_layer(min(max_features, ngf * mult * 2)), activation]
        mult = 2 ** n_downsampling
        feats_num_bottleneck = min(max_features, ngf * mult)
        if len(manual_block_spec) == 0:
            manual_block_spec = [DotDict(lambda: None, {'n_blocks': n_blocks, 'use_default': True})]
        for block_spec in manual_block_spec:

            def make_and_add_blocks(model, block_spec):
                block_spec = DotDict(lambda: None, block_spec)
                if not block_spec.use_default:
                    resnet_conv_layer = functools.partial(get_conv_block_ctor(block_spec.resnet_conv_kind), **block_spec.multidilation_kwargs)
                    resnet_conv_kind = block_spec.resnet_conv_kind
                    resnet_block_kind = block_spec.resnet_block_kind
                    if block_spec.resnet_dilation is not None:
                        resnet_dilation = block_spec.resnet_dilation
                for i in range(block_spec.n_blocks):
                    if resnet_block_kind == 'multidilatedresnetblock':
                        model += [MultidilatedResnetBlock(feats_num_bottleneck, padding_type=padding_type, conv_layer=resnet_conv_layer, activation=activation, norm_layer=norm_layer)]
                    if resnet_block_kind == 'resnetblock':
                        model += [ResnetBlock(ngf * mult, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=resnet_conv_kind)]
                    if resnet_block_kind == 'resnetblock5x5':
                        model += [ResnetBlock5x5(ngf * mult, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=resnet_conv_kind)]
                    if resnet_block_kind == 'resnetblockdwdil':
                        model += [ResnetBlock(ngf * mult, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=resnet_conv_kind, dilation=resnet_dilation, second_dilation=resnet_dilation)]
            make_and_add_blocks(model, block_spec)
        for i in range(n_downsampling):
            mult = 2 ** (n_downsampling - i)
            model += deconv_factory(deconv_kind, ngf, mult, up_norm_layer, up_activation, max_features)
        model += [nn.ReflectionPad2d(3), nn.Conv2d(ngf, output_nc, kernel_size=7, padding=0)]
        if add_out_act:
            model.append(get_activation('tanh' if add_out_act is True else add_out_act))
        self.model = nn.Sequential(*model)

    def forward(self, input):
        return self.model(input)

def __init__(self, input_nc, output_nc, ngf=64, n_downsampling=3, n_blocks=3, norm_layer=nn.BatchNorm2d, padding_type='reflect', conv_kind='default', deconv_kind='convtranspose', activation=nn.ReLU(True), up_norm_layer=nn.BatchNorm2d, affine=None, up_activation=nn.ReLU(True), add_out_act=True, max_features=1024, manual_block_spec=[], resnet_block_kind='multidilatedresnetblock', resnet_conv_kind='multidilated', resnet_dilation=1, multidilation_kwargs={}):
    assert n_blocks >= 0
    super().__init__()
    conv_layer = get_conv_block_ctor(conv_kind)
    resnet_conv_layer = functools.partial(get_conv_block_ctor(resnet_conv_kind), **multidilation_kwargs)
    norm_layer = get_norm_layer(norm_layer)
    if affine is not None:
        norm_layer = partial(norm_layer, affine=affine)
    up_norm_layer = get_norm_layer(up_norm_layer)
    if affine is not None:
        up_norm_layer = partial(up_norm_layer, affine=affine)
    model = [nn.ReflectionPad2d(3), conv_layer(input_nc, ngf, kernel_size=7, padding=0), norm_layer(ngf), activation]
    identity = Identity()
    for i in range(n_downsampling):
        mult = 2 ** i
        model += [conv_layer(min(max_features, ngf * mult), min(max_features, ngf * mult * 2), kernel_size=3, stride=2, padding=1), norm_layer(min(max_features, ngf * mult * 2)), activation]
    mult = 2 ** n_downsampling
    feats_num_bottleneck = min(max_features, ngf * mult)
    if len(manual_block_spec) == 0:
        manual_block_spec = [DotDict(lambda: None, {'n_blocks': n_blocks, 'use_default': True})]
    for block_spec in manual_block_spec:

        def make_and_add_blocks(model, block_spec):
            block_spec = DotDict(lambda: None, block_spec)
            if not block_spec.use_default:
                resnet_conv_layer = functools.partial(get_conv_block_ctor(block_spec.resnet_conv_kind), **block_spec.multidilation_kwargs)
                resnet_conv_kind = block_spec.resnet_conv_kind
                resnet_block_kind = block_spec.resnet_block_kind
                if block_spec.resnet_dilation is not None:
                    resnet_dilation = block_spec.resnet_dilation
            for i in range(block_spec.n_blocks):
                if resnet_block_kind == 'multidilatedresnetblock':
                    model += [MultidilatedResnetBlock(feats_num_bottleneck, padding_type=padding_type, conv_layer=resnet_conv_layer, activation=activation, norm_layer=norm_layer)]
                if resnet_block_kind == 'resnetblock':
                    model += [ResnetBlock(ngf * mult, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=resnet_conv_kind)]
                if resnet_block_kind == 'resnetblock5x5':
                    model += [ResnetBlock5x5(ngf * mult, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=resnet_conv_kind)]
                if resnet_block_kind == 'resnetblockdwdil':
                    model += [ResnetBlock(ngf * mult, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=resnet_conv_kind, dilation=resnet_dilation, second_dilation=resnet_dilation)]
        make_and_add_blocks(model, block_spec)
    for i in range(n_downsampling):
        mult = 2 ** (n_downsampling - i)
        model += deconv_factory(deconv_kind, ngf, mult, up_norm_layer, up_activation, max_features)
    model += [nn.ReflectionPad2d(3), nn.Conv2d(ngf, output_nc, kernel_size=7, padding=0)]
    if add_out_act:
        model.append(get_activation('tanh' if add_out_act is True else add_out_act))
    self.model = nn.Sequential(*model)

def make_and_add_blocks(model, block_spec):
    block_spec = DotDict(lambda: None, block_spec)
    if not block_spec.use_default:
        resnet_conv_layer = functools.partial(get_conv_block_ctor(block_spec.resnet_conv_kind), **block_spec.multidilation_kwargs)
        resnet_conv_kind = block_spec.resnet_conv_kind
        resnet_block_kind = block_spec.resnet_block_kind
        if block_spec.resnet_dilation is not None:
            resnet_dilation = block_spec.resnet_dilation
    for i in range(block_spec.n_blocks):
        if resnet_block_kind == 'multidilatedresnetblock':
            model += [MultidilatedResnetBlock(feats_num_bottleneck, padding_type=padding_type, conv_layer=resnet_conv_layer, activation=activation, norm_layer=norm_layer)]
        if resnet_block_kind == 'resnetblock':
            model += [ResnetBlock(ngf * mult, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=resnet_conv_kind)]
        if resnet_block_kind == 'resnetblock5x5':
            model += [ResnetBlock5x5(ngf * mult, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=resnet_conv_kind)]
        if resnet_block_kind == 'resnetblockdwdil':
            model += [ResnetBlock(ngf * mult, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=resnet_conv_kind, dilation=resnet_dilation, second_dilation=resnet_dilation)]

def make_dil_blocks(dilated_blocks_n, dilation_block_kind, dilated_block_kwargs):
    blocks = []
    for i in range(dilated_blocks_n):
        if dilation_block_kind == 'simple':
            blocks.append(ResnetBlock(**dilated_block_kwargs, dilation=2 ** (i + 1)))
        elif dilation_block_kind == 'multi':
            blocks.append(MultidilatedResnetBlock(**dilated_block_kwargs))
        else:
            raise ValueError(f'dilation_block_kind could not be "{dilation_block_kind}"')
    return blocks

class GlobalGenerator(nn.Module):

    def __init__(self, input_nc, output_nc, ngf=64, n_downsampling=3, n_blocks=9, norm_layer=nn.BatchNorm2d, padding_type='reflect', conv_kind='default', activation=nn.ReLU(True), up_norm_layer=nn.BatchNorm2d, affine=None, up_activation=nn.ReLU(True), dilated_blocks_n=0, dilated_blocks_n_start=0, dilated_blocks_n_middle=0, add_out_act=True, max_features=1024, is_resblock_depthwise=False, ffc_positions=None, ffc_kwargs={}, dilation=1, second_dilation=None, dilation_block_kind='simple', multidilation_kwargs={}):
        assert n_blocks >= 0
        super().__init__()
        conv_layer = get_conv_block_ctor(conv_kind)
        norm_layer = get_norm_layer(norm_layer)
        if affine is not None:
            norm_layer = partial(norm_layer, affine=affine)
        up_norm_layer = get_norm_layer(up_norm_layer)
        if affine is not None:
            up_norm_layer = partial(up_norm_layer, affine=affine)
        if ffc_positions is not None:
            ffc_positions = collections.Counter(ffc_positions)
        model = [nn.ReflectionPad2d(3), conv_layer(input_nc, ngf, kernel_size=7, padding=0), norm_layer(ngf), activation]
        identity = Identity()
        for i in range(n_downsampling):
            mult = 2 ** i
            model += [conv_layer(min(max_features, ngf * mult), min(max_features, ngf * mult * 2), kernel_size=3, stride=2, padding=1), norm_layer(min(max_features, ngf * mult * 2)), activation]
        mult = 2 ** n_downsampling
        feats_num_bottleneck = min(max_features, ngf * mult)
        dilated_block_kwargs = dict(dim=feats_num_bottleneck, padding_type=padding_type, activation=activation, norm_layer=norm_layer)
        if dilation_block_kind == 'simple':
            dilated_block_kwargs['conv_kind'] = conv_kind
        elif dilation_block_kind == 'multi':
            dilated_block_kwargs['conv_layer'] = functools.partial(get_conv_block_ctor('multidilated'), **multidilation_kwargs)
        if dilated_blocks_n_start is not None and dilated_blocks_n_start > 0:
            model += make_dil_blocks(dilated_blocks_n_start, dilation_block_kind, dilated_block_kwargs)
        for i in range(n_blocks):
            if i == n_blocks // 2 and dilated_blocks_n_middle is not None and (dilated_blocks_n_middle > 0):
                model += make_dil_blocks(dilated_blocks_n_middle, dilation_block_kind, dilated_block_kwargs)
            if ffc_positions is not None and i in ffc_positions:
                for _ in range(ffc_positions[i]):
                    model += [FFCResnetBlock(feats_num_bottleneck, padding_type, norm_layer, activation_layer=nn.ReLU, inline=True, **ffc_kwargs)]
            if is_resblock_depthwise:
                resblock_groups = feats_num_bottleneck
            else:
                resblock_groups = 1
            model += [ResnetBlock(feats_num_bottleneck, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=conv_kind, groups=resblock_groups, dilation=dilation, second_dilation=second_dilation)]
        if dilated_blocks_n is not None and dilated_blocks_n > 0:
            model += make_dil_blocks(dilated_blocks_n, dilation_block_kind, dilated_block_kwargs)
        for i in range(n_downsampling):
            mult = 2 ** (n_downsampling - i)
            model += [nn.ConvTranspose2d(min(max_features, ngf * mult), min(max_features, int(ngf * mult / 2)), kernel_size=3, stride=2, padding=1, output_padding=1), up_norm_layer(min(max_features, int(ngf * mult / 2))), up_activation]
        model += [nn.ReflectionPad2d(3), nn.Conv2d(ngf, output_nc, kernel_size=7, padding=0)]
        if add_out_act:
            model.append(get_activation('tanh' if add_out_act is True else add_out_act))
        self.model = nn.Sequential(*model)

    def forward(self, input):
        return self.model(input)

def __init__(self, input_nc, output_nc, ngf=64, n_downsampling=3, n_blocks=9, norm_layer=nn.BatchNorm2d, padding_type='reflect', conv_kind='default', activation=nn.ReLU(True), up_norm_layer=nn.BatchNorm2d, affine=None, up_activation=nn.ReLU(True), dilated_blocks_n=0, dilated_blocks_n_start=0, dilated_blocks_n_middle=0, add_out_act=True, max_features=1024, is_resblock_depthwise=False, ffc_positions=None, ffc_kwargs={}, dilation=1, second_dilation=None, dilation_block_kind='simple', multidilation_kwargs={}):
    assert n_blocks >= 0
    super().__init__()
    conv_layer = get_conv_block_ctor(conv_kind)
    norm_layer = get_norm_layer(norm_layer)
    if affine is not None:
        norm_layer = partial(norm_layer, affine=affine)
    up_norm_layer = get_norm_layer(up_norm_layer)
    if affine is not None:
        up_norm_layer = partial(up_norm_layer, affine=affine)
    if ffc_positions is not None:
        ffc_positions = collections.Counter(ffc_positions)
    model = [nn.ReflectionPad2d(3), conv_layer(input_nc, ngf, kernel_size=7, padding=0), norm_layer(ngf), activation]
    identity = Identity()
    for i in range(n_downsampling):
        mult = 2 ** i
        model += [conv_layer(min(max_features, ngf * mult), min(max_features, ngf * mult * 2), kernel_size=3, stride=2, padding=1), norm_layer(min(max_features, ngf * mult * 2)), activation]
    mult = 2 ** n_downsampling
    feats_num_bottleneck = min(max_features, ngf * mult)
    dilated_block_kwargs = dict(dim=feats_num_bottleneck, padding_type=padding_type, activation=activation, norm_layer=norm_layer)
    if dilation_block_kind == 'simple':
        dilated_block_kwargs['conv_kind'] = conv_kind
    elif dilation_block_kind == 'multi':
        dilated_block_kwargs['conv_layer'] = functools.partial(get_conv_block_ctor('multidilated'), **multidilation_kwargs)
    if dilated_blocks_n_start is not None and dilated_blocks_n_start > 0:
        model += make_dil_blocks(dilated_blocks_n_start, dilation_block_kind, dilated_block_kwargs)
    for i in range(n_blocks):
        if i == n_blocks // 2 and dilated_blocks_n_middle is not None and (dilated_blocks_n_middle > 0):
            model += make_dil_blocks(dilated_blocks_n_middle, dilation_block_kind, dilated_block_kwargs)
        if ffc_positions is not None and i in ffc_positions:
            for _ in range(ffc_positions[i]):
                model += [FFCResnetBlock(feats_num_bottleneck, padding_type, norm_layer, activation_layer=nn.ReLU, inline=True, **ffc_kwargs)]
        if is_resblock_depthwise:
            resblock_groups = feats_num_bottleneck
        else:
            resblock_groups = 1
        model += [ResnetBlock(feats_num_bottleneck, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=conv_kind, groups=resblock_groups, dilation=dilation, second_dilation=second_dilation)]
    if dilated_blocks_n is not None and dilated_blocks_n > 0:
        model += make_dil_blocks(dilated_blocks_n, dilation_block_kind, dilated_block_kwargs)
    for i in range(n_downsampling):
        mult = 2 ** (n_downsampling - i)
        model += [nn.ConvTranspose2d(min(max_features, ngf * mult), min(max_features, int(ngf * mult / 2)), kernel_size=3, stride=2, padding=1, output_padding=1), up_norm_layer(min(max_features, int(ngf * mult / 2))), up_activation]
    model += [nn.ReflectionPad2d(3), nn.Conv2d(ngf, output_nc, kernel_size=7, padding=0)]
    if add_out_act:
        model.append(get_activation('tanh' if add_out_act is True else add_out_act))
    self.model = nn.Sequential(*model)

class GlobalGeneratorGated(GlobalGenerator):

    def __init__(self, *args, **kwargs):
        real_kwargs = dict(conv_kind='gated_bn_relu', activation=nn.Identity(), norm_layer=nn.Identity)
        real_kwargs.update(kwargs)
        super().__init__(*args, **real_kwargs)

def __init__(self, *args, **kwargs):
    real_kwargs = dict(conv_kind='gated_bn_relu', activation=nn.Identity(), norm_layer=nn.Identity)
    real_kwargs.update(kwargs)
    super().__init__(*args, **real_kwargs)

class GlobalGeneratorFromSuperChannels(nn.Module):

    def __init__(self, input_nc, output_nc, n_downsampling, n_blocks, super_channels, norm_layer='bn', padding_type='reflect', add_out_act=True):
        super().__init__()
        self.n_downsampling = n_downsampling
        norm_layer = get_norm_layer(norm_layer)
        if type(norm_layer) == functools.partial:
            use_bias = norm_layer.func == nn.InstanceNorm2d
        else:
            use_bias = norm_layer == nn.InstanceNorm2d
        channels = self.convert_super_channels(super_channels)
        self.channels = channels
        model = [nn.ReflectionPad2d(3), nn.Conv2d(input_nc, channels[0], kernel_size=7, padding=0, bias=use_bias), norm_layer(channels[0]), nn.ReLU(True)]
        for i in range(n_downsampling):
            mult = 2 ** i
            model += [nn.Conv2d(channels[0 + i], channels[1 + i], kernel_size=3, stride=2, padding=1, bias=use_bias), norm_layer(channels[1 + i]), nn.ReLU(True)]
        mult = 2 ** n_downsampling
        n_blocks1 = n_blocks // 3
        n_blocks2 = n_blocks1
        n_blocks3 = n_blocks - n_blocks1 - n_blocks2
        for i in range(n_blocks1):
            c = n_downsampling
            dim = channels[c]
            model += [ResnetBlock(dim, padding_type=padding_type, norm_layer=norm_layer)]
        for i in range(n_blocks2):
            c = n_downsampling + 1
            dim = channels[c]
            kwargs = {}
            if i == 0:
                kwargs = {'in_dim': channels[c - 1]}
            model += [ResnetBlock(dim, padding_type=padding_type, norm_layer=norm_layer, **kwargs)]
        for i in range(n_blocks3):
            c = n_downsampling + 2
            dim = channels[c]
            kwargs = {}
            if i == 0:
                kwargs = {'in_dim': channels[c - 1]}
            model += [ResnetBlock(dim, padding_type=padding_type, norm_layer=norm_layer, **kwargs)]
        for i in range(n_downsampling):
            mult = 2 ** (n_downsampling - i)
            model += [nn.ConvTranspose2d(channels[n_downsampling + 3 + i], channels[n_downsampling + 3 + i + 1], kernel_size=3, stride=2, padding=1, output_padding=1, bias=use_bias), norm_layer(channels[n_downsampling + 3 + i + 1]), nn.ReLU(True)]
        model += [nn.ReflectionPad2d(3)]
        model += [nn.Conv2d(channels[2 * n_downsampling + 3], output_nc, kernel_size=7, padding=0)]
        if add_out_act:
            model.append(get_activation('tanh' if add_out_act is True else add_out_act))
        self.model = nn.Sequential(*model)

    def convert_super_channels(self, super_channels):
        n_downsampling = self.n_downsampling
        result = []
        cnt = 0
        if n_downsampling == 2:
            N1 = 10
        elif n_downsampling == 3:
            N1 = 13
        else:
            raise NotImplementedError
        for i in range(0, N1):
            if i in [1, 4, 7, 10]:
                channel = super_channels[cnt] * 2 ** cnt
                config = {'channel': channel}
                result.append(channel)
                logging.info(f'Downsample channels {result[-1]}')
                cnt += 1
        for i in range(3):
            for counter, j in enumerate(range(N1 + i * 3, N1 + 3 + i * 3)):
                if len(super_channels) == 6:
                    channel = super_channels[3] * 4
                else:
                    channel = super_channels[i + 3] * 4
                config = {'channel': channel}
                if counter == 0:
                    result.append(channel)
                    logging.info(f'Bottleneck channels {result[-1]}')
        cnt = 2
        for i in range(N1 + 9, N1 + 21):
            if i in [22, 25, 28]:
                cnt -= 1
                if len(super_channels) == 6:
                    channel = super_channels[5 - cnt] * 2 ** cnt
                else:
                    channel = super_channels[7 - cnt] * 2 ** cnt
                result.append(int(channel))
                logging.info(f'Upsample channels {result[-1]}')
        return result

    def forward(self, input):
        return self.model(input)

def __init__(self, input_nc, output_nc, n_downsampling, n_blocks, super_channels, norm_layer='bn', padding_type='reflect', add_out_act=True):
    super().__init__()
    self.n_downsampling = n_downsampling
    norm_layer = get_norm_layer(norm_layer)
    if type(norm_layer) == functools.partial:
        use_bias = norm_layer.func == nn.InstanceNorm2d
    else:
        use_bias = norm_layer == nn.InstanceNorm2d
    channels = self.convert_super_channels(super_channels)
    self.channels = channels
    model = [nn.ReflectionPad2d(3), nn.Conv2d(input_nc, channels[0], kernel_size=7, padding=0, bias=use_bias), norm_layer(channels[0]), nn.ReLU(True)]
    for i in range(n_downsampling):
        mult = 2 ** i
        model += [nn.Conv2d(channels[0 + i], channels[1 + i], kernel_size=3, stride=2, padding=1, bias=use_bias), norm_layer(channels[1 + i]), nn.ReLU(True)]
    mult = 2 ** n_downsampling
    n_blocks1 = n_blocks // 3
    n_blocks2 = n_blocks1
    n_blocks3 = n_blocks - n_blocks1 - n_blocks2
    for i in range(n_blocks1):
        c = n_downsampling
        dim = channels[c]
        model += [ResnetBlock(dim, padding_type=padding_type, norm_layer=norm_layer)]
    for i in range(n_blocks2):
        c = n_downsampling + 1
        dim = channels[c]
        kwargs = {}
        if i == 0:
            kwargs = {'in_dim': channels[c - 1]}
        model += [ResnetBlock(dim, padding_type=padding_type, norm_layer=norm_layer, **kwargs)]
    for i in range(n_blocks3):
        c = n_downsampling + 2
        dim = channels[c]
        kwargs = {}
        if i == 0:
            kwargs = {'in_dim': channels[c - 1]}
        model += [ResnetBlock(dim, padding_type=padding_type, norm_layer=norm_layer, **kwargs)]
    for i in range(n_downsampling):
        mult = 2 ** (n_downsampling - i)
        model += [nn.ConvTranspose2d(channels[n_downsampling + 3 + i], channels[n_downsampling + 3 + i + 1], kernel_size=3, stride=2, padding=1, output_padding=1, bias=use_bias), norm_layer(channels[n_downsampling + 3 + i + 1]), nn.ReLU(True)]
    model += [nn.ReflectionPad2d(3)]
    model += [nn.Conv2d(channels[2 * n_downsampling + 3], output_nc, kernel_size=7, padding=0)]
    if add_out_act:
        model.append(get_activation('tanh' if add_out_act is True else add_out_act))
    self.model = nn.Sequential(*model)

class NLayerDiscriminator(BaseDiscriminator):

    def __init__(self, input_nc, ndf=64, n_layers=3, norm_layer=nn.BatchNorm2d):
        super().__init__()
        self.n_layers = n_layers
        kw = 4
        padw = int(np.ceil((kw - 1.0) / 2))
        sequence = [[nn.Conv2d(input_nc, ndf, kernel_size=kw, stride=2, padding=padw), nn.LeakyReLU(0.2, True)]]
        nf = ndf
        for n in range(1, n_layers):
            nf_prev = nf
            nf = min(nf * 2, 512)
            cur_model = []
            cur_model += [nn.Conv2d(nf_prev, nf, kernel_size=kw, stride=2, padding=padw), norm_layer(nf), nn.LeakyReLU(0.2, True)]
            sequence.append(cur_model)
        nf_prev = nf
        nf = min(nf * 2, 512)
        cur_model = []
        cur_model += [nn.Conv2d(nf_prev, nf, kernel_size=kw, stride=1, padding=padw), norm_layer(nf), nn.LeakyReLU(0.2, True)]
        sequence.append(cur_model)
        sequence += [[nn.Conv2d(nf, 1, kernel_size=kw, stride=1, padding=padw)]]
        for n in range(len(sequence)):
            setattr(self, 'model' + str(n), nn.Sequential(*sequence[n]))

    def get_all_activations(self, x):
        res = [x]
        for n in range(self.n_layers + 2):
            model = getattr(self, 'model' + str(n))
            res.append(model(res[-1]))
        return res[1:]

    def forward(self, x):
        act = self.get_all_activations(x)
        return (act[-1], act[:-1])

def __init__(self, input_nc, ndf=64, n_layers=3, norm_layer=nn.BatchNorm2d):
    super().__init__()
    self.n_layers = n_layers
    kw = 4
    padw = int(np.ceil((kw - 1.0) / 2))
    sequence = [[nn.Conv2d(input_nc, ndf, kernel_size=kw, stride=2, padding=padw), nn.LeakyReLU(0.2, True)]]
    nf = ndf
    for n in range(1, n_layers):
        nf_prev = nf
        nf = min(nf * 2, 512)
        cur_model = []
        cur_model += [nn.Conv2d(nf_prev, nf, kernel_size=kw, stride=2, padding=padw), norm_layer(nf), nn.LeakyReLU(0.2, True)]
        sequence.append(cur_model)
    nf_prev = nf
    nf = min(nf * 2, 512)
    cur_model = []
    cur_model += [nn.Conv2d(nf_prev, nf, kernel_size=kw, stride=1, padding=padw), norm_layer(nf), nn.LeakyReLU(0.2, True)]
    sequence.append(cur_model)
    sequence += [[nn.Conv2d(nf, 1, kernel_size=kw, stride=1, padding=padw)]]
    for n in range(len(sequence)):
        setattr(self, 'model' + str(n), nn.Sequential(*sequence[n]))

class MultidilatedNLayerDiscriminator(BaseDiscriminator):

    def __init__(self, input_nc, ndf=64, n_layers=3, norm_layer=nn.BatchNorm2d, multidilation_kwargs={}):
        super().__init__()
        self.n_layers = n_layers
        kw = 4
        padw = int(np.ceil((kw - 1.0) / 2))
        sequence = [[nn.Conv2d(input_nc, ndf, kernel_size=kw, stride=2, padding=padw), nn.LeakyReLU(0.2, True)]]
        nf = ndf
        for n in range(1, n_layers):
            nf_prev = nf
            nf = min(nf * 2, 512)
            cur_model = []
            cur_model += [MultidilatedConv(nf_prev, nf, kernel_size=kw, stride=2, padding=[2, 3], **multidilation_kwargs), norm_layer(nf), nn.LeakyReLU(0.2, True)]
            sequence.append(cur_model)
        nf_prev = nf
        nf = min(nf * 2, 512)
        cur_model = []
        cur_model += [nn.Conv2d(nf_prev, nf, kernel_size=kw, stride=1, padding=padw), norm_layer(nf), nn.LeakyReLU(0.2, True)]
        sequence.append(cur_model)
        sequence += [[nn.Conv2d(nf, 1, kernel_size=kw, stride=1, padding=padw)]]
        for n in range(len(sequence)):
            setattr(self, 'model' + str(n), nn.Sequential(*sequence[n]))

    def get_all_activations(self, x):
        res = [x]
        for n in range(self.n_layers + 2):
            model = getattr(self, 'model' + str(n))
            res.append(model(res[-1]))
        return res[1:]

    def forward(self, x):
        act = self.get_all_activations(x)
        return (act[-1], act[:-1])

def __init__(self, input_nc, ndf=64, n_layers=3, norm_layer=nn.BatchNorm2d, multidilation_kwargs={}):
    super().__init__()
    self.n_layers = n_layers
    kw = 4
    padw = int(np.ceil((kw - 1.0) / 2))
    sequence = [[nn.Conv2d(input_nc, ndf, kernel_size=kw, stride=2, padding=padw), nn.LeakyReLU(0.2, True)]]
    nf = ndf
    for n in range(1, n_layers):
        nf_prev = nf
        nf = min(nf * 2, 512)
        cur_model = []
        cur_model += [MultidilatedConv(nf_prev, nf, kernel_size=kw, stride=2, padding=[2, 3], **multidilation_kwargs), norm_layer(nf), nn.LeakyReLU(0.2, True)]
        sequence.append(cur_model)
    nf_prev = nf
    nf = min(nf * 2, 512)
    cur_model = []
    cur_model += [nn.Conv2d(nf_prev, nf, kernel_size=kw, stride=1, padding=padw), norm_layer(nf), nn.LeakyReLU(0.2, True)]
    sequence.append(cur_model)
    sequence += [[nn.Conv2d(nf, 1, kernel_size=kw, stride=1, padding=padw)]]
    for n in range(len(sequence)):
        setattr(self, 'model' + str(n), nn.Sequential(*sequence[n]))

class NLayerDiscriminatorAsGen(NLayerDiscriminator):

    def forward(self, x):
        return super().forward(x)[0]

def forward(self, x):
    return super().forward(x)[0]

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

def __init__(self, impl, pad_coef=0.5, angle_init_range=80, train_angle=True):
    super().__init__()
    self.impl = impl
    self.angle = torch.rand(1) * angle_init_range
    if train_angle:
        self.angle = nn.Parameter(self.angle, requires_grad=True)
    self.pad_coef = pad_coef

class DepthWiseSeperableConv(nn.Module):

    def __init__(self, in_dim, out_dim, *args, **kwargs):
        super().__init__()
        if 'groups' in kwargs:
            del kwargs['groups']
        self.depthwise = nn.Conv2d(in_dim, in_dim, *args, groups=in_dim, **kwargs)
        self.pointwise = nn.Conv2d(in_dim, out_dim, kernel_size=1)

    def forward(self, x):
        out = self.depthwise(x)
        out = self.pointwise(out)
        return out

def __init__(self, in_dim, out_dim, *args, **kwargs):
    super().__init__()
    if 'groups' in kwargs:
        del kwargs['groups']
    self.depthwise = nn.Conv2d(in_dim, in_dim, *args, groups=in_dim, **kwargs)
    self.pointwise = nn.Conv2d(in_dim, out_dim, kernel_size=1)

class PairwiseScore(EvaluatorScore, ABC):

    def __init__(self):
        super().__init__()
        self.individual_values = None

    def get_value(self, groups=None, states=None):
        """
        :param groups:
        :return:
            total_results: dict of kind {'mean': score mean, 'std': score std}
            group_results: None, if groups is None;
                else dict {group_idx: {'mean': score mean among group, 'std': score std among group}}
        """
        individual_values = torch.cat(states, dim=-1).reshape(-1).cpu().numpy() if states is not None else self.individual_values
        total_results = {'mean': individual_values.mean(), 'std': individual_values.std()}
        if groups is None:
            return (total_results, None)
        group_results = dict()
        grouping = get_groupings(groups)
        for label, index in grouping.items():
            group_scores = individual_values[index]
            group_results[label] = {'mean': group_scores.mean(), 'std': group_scores.std()}
        return (total_results, group_results)

    def reset(self):
        self.individual_values = []

def __init__(self):
    super().__init__()
    self.individual_values = None

class SSIMScore(PairwiseScore):

    def __init__(self, window_size=11):
        super().__init__()
        self.score = SSIM(window_size=window_size, size_average=False).eval()
        self.reset()

    def forward(self, pred_batch, target_batch, mask=None):
        batch_values = self.score(pred_batch, target_batch)
        self.individual_values = np.hstack([self.individual_values, batch_values.detach().cpu().numpy()])
        return batch_values

def __init__(self, window_size=11):
    super().__init__()
    self.score = SSIM(window_size=window_size, size_average=False).eval()
    self.reset()

class LPIPSScore(PairwiseScore):

    def __init__(self, model='net-lin', net='vgg', model_path=None, use_gpu=True):
        super().__init__()
        self.score = PerceptualLoss(model=model, net=net, model_path=model_path, use_gpu=use_gpu, spatial=False).eval()
        self.reset()

    def forward(self, pred_batch, target_batch, mask=None):
        batch_values = self.score(pred_batch, target_batch).flatten()
        self.individual_values = np.hstack([self.individual_values, batch_values.detach().cpu().numpy()])
        return batch_values

def __init__(self, model='net-lin', net='vgg', model_path=None, use_gpu=True):
    super().__init__()
    self.score = PerceptualLoss(model=model, net=net, model_path=model_path, use_gpu=use_gpu, spatial=False).eval()
    self.reset()

class SegmentationAwareScore(EvaluatorScore):

    def __init__(self, weights_path):
        super().__init__()
        self.segm_network = SegmentationModule(weights_path=weights_path, use_default_normalization=True).eval()
        self.target_class_freq_by_image_total = []
        self.target_class_freq_by_image_mask = []
        self.pred_class_freq_by_image_mask = []

    def forward(self, pred_batch, target_batch, mask):
        pred_segm_flat = self.segm_network.predict(pred_batch)[0].view(pred_batch.shape[0], -1).long().detach().cpu().numpy()
        target_segm_flat = self.segm_network.predict(target_batch)[0].view(pred_batch.shape[0], -1).long().detach().cpu().numpy()
        mask_flat = (mask.view(mask.shape[0], -1) > 0.5).detach().cpu().numpy()
        batch_target_class_freq_total = []
        batch_target_class_freq_mask = []
        batch_pred_class_freq_mask = []
        for cur_pred_segm, cur_target_segm, cur_mask in zip(pred_segm_flat, target_segm_flat, mask_flat):
            cur_target_class_freq_total = np.bincount(cur_target_segm, minlength=NUM_CLASS)[None, ...]
            cur_target_class_freq_mask = np.bincount(cur_target_segm[cur_mask], minlength=NUM_CLASS)[None, ...]
            cur_pred_class_freq_mask = np.bincount(cur_pred_segm[cur_mask], minlength=NUM_CLASS)[None, ...]
            self.target_class_freq_by_image_total.append(cur_target_class_freq_total)
            self.target_class_freq_by_image_mask.append(cur_target_class_freq_mask)
            self.pred_class_freq_by_image_mask.append(cur_pred_class_freq_mask)
            batch_target_class_freq_total.append(cur_target_class_freq_total)
            batch_target_class_freq_mask.append(cur_target_class_freq_mask)
            batch_pred_class_freq_mask.append(cur_pred_class_freq_mask)
        batch_target_class_freq_total = np.concatenate(batch_target_class_freq_total, axis=0)
        batch_target_class_freq_mask = np.concatenate(batch_target_class_freq_mask, axis=0)
        batch_pred_class_freq_mask = np.concatenate(batch_pred_class_freq_mask, axis=0)
        return (batch_target_class_freq_total, batch_target_class_freq_mask, batch_pred_class_freq_mask)

    def reset(self):
        super().reset()
        self.target_class_freq_by_image_total = []
        self.target_class_freq_by_image_mask = []
        self.pred_class_freq_by_image_mask = []

def __init__(self, weights_path):
    super().__init__()
    self.segm_network = SegmentationModule(weights_path=weights_path, use_default_normalization=True).eval()
    self.target_class_freq_by_image_total = []
    self.target_class_freq_by_image_mask = []
    self.pred_class_freq_by_image_mask = []

class SegmentationAwarePairwiseScore(SegmentationAwareScore):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.individual_values = []
        self.segm_idx2name = get_segmentation_idx2name()

    def forward(self, pred_batch, target_batch, mask):
        cur_class_stats = super().forward(pred_batch, target_batch, mask)
        score_values = self.calc_score(pred_batch, target_batch, mask)
        self.individual_values.append(score_values)
        return cur_class_stats + (score_values,)

    @abstractmethod
    def calc_score(self, pred_batch, target_batch, mask):
        raise NotImplementedError()

    def get_value(self, groups=None, states=None):
        """
        :param groups:
        :return:
            total_results: dict of kind {'mean': score mean, 'std': score std}
            group_results: None, if groups is None;
                else dict {group_idx: {'mean': score mean among group, 'std': score std among group}}
        """
        if states is not None:
            target_class_freq_by_image_total, target_class_freq_by_image_mask, pred_class_freq_by_image_mask, individual_values = states
        else:
            target_class_freq_by_image_total = self.target_class_freq_by_image_total
            target_class_freq_by_image_mask = self.target_class_freq_by_image_mask
            pred_class_freq_by_image_mask = self.pred_class_freq_by_image_mask
            individual_values = self.individual_values
        target_class_freq_by_image_total = np.concatenate(target_class_freq_by_image_total, axis=0)
        target_class_freq_by_image_mask = np.concatenate(target_class_freq_by_image_mask, axis=0)
        pred_class_freq_by_image_mask = np.concatenate(pred_class_freq_by_image_mask, axis=0)
        individual_values = np.concatenate(individual_values, axis=0)
        total_results = {'mean': individual_values.mean(), 'std': individual_values.std(), **distribute_values_to_classes(target_class_freq_by_image_mask, individual_values, self.segm_idx2name)}
        if groups is None:
            return (total_results, None)
        group_results = dict()
        grouping = get_groupings(groups)
        for label, index in grouping.items():
            group_class_freq = target_class_freq_by_image_mask[index]
            group_scores = individual_values[index]
            group_results[label] = {'mean': group_scores.mean(), 'std': group_scores.std(), **distribute_values_to_classes(group_class_freq, group_scores, self.segm_idx2name)}
        return (total_results, group_results)

    def reset(self):
        super().reset()
        self.individual_values = []

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.individual_values = []
    self.segm_idx2name = get_segmentation_idx2name()

def forward(self, pred_batch, target_batch, mask):
    cur_class_stats = super().forward(pred_batch, target_batch, mask)
    score_values = self.calc_score(pred_batch, target_batch, mask)
    self.individual_values.append(score_values)
    return cur_class_stats + (score_values,)

class SegmentationAwareSSIM(SegmentationAwarePairwiseScore):

    def __init__(self, *args, window_size=11, **kwargs):
        super().__init__(*args, **kwargs)
        self.score_impl = SSIM(window_size=window_size, size_average=False).eval()

    def calc_score(self, pred_batch, target_batch, mask):
        return self.score_impl(pred_batch, target_batch).detach().cpu().numpy()

def __init__(self, *args, window_size=11, **kwargs):
    super().__init__(*args, **kwargs)
    self.score_impl = SSIM(window_size=window_size, size_average=False).eval()

class SegmentationAwareLPIPS(SegmentationAwarePairwiseScore):

    def __init__(self, *args, model='net-lin', net='vgg', model_path=None, use_gpu=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.score_impl = PerceptualLoss(model=model, net=net, model_path=model_path, use_gpu=use_gpu, spatial=False).eval()

    def calc_score(self, pred_batch, target_batch, mask):
        return self.score_impl(pred_batch, target_batch).flatten().detach().cpu().numpy()

def __init__(self, *args, model='net-lin', net='vgg', model_path=None, use_gpu=True, **kwargs):
    super().__init__(*args, **kwargs)
    self.score_impl = PerceptualLoss(model=model, net=net, model_path=model_path, use_gpu=use_gpu, spatial=False).eval()

class SSIM(torch.nn.Module):
    """SSIM. Modified from:
    https://github.com/Po-Hsun-Su/pytorch-ssim/blob/master/pytorch_ssim/__init__.py
    """

    def __init__(self, window_size=11, size_average=True):
        super().__init__()
        self.window_size = window_size
        self.size_average = size_average
        self.channel = 1
        self.register_buffer('window', self._create_window(window_size, self.channel))

    def forward(self, img1, img2):
        assert len(img1.shape) == 4
        channel = img1.size()[1]
        if channel == self.channel and self.window.data.type() == img1.data.type():
            window = self.window
        else:
            window = self._create_window(self.window_size, channel)
            window = window.type_as(img1)
            self.window = window
            self.channel = channel
        return self._ssim(img1, img2, window, self.window_size, channel, self.size_average)

    def _gaussian(self, window_size, sigma):
        gauss = torch.Tensor([np.exp(-(x - window_size // 2) ** 2 / float(2 * sigma ** 2)) for x in range(window_size)])
        return gauss / gauss.sum()

    def _create_window(self, window_size, channel):
        _1D_window = self._gaussian(window_size, 1.5).unsqueeze(1)
        _2D_window = _1D_window.mm(_1D_window.t()).float().unsqueeze(0).unsqueeze(0)
        return _2D_window.expand(channel, 1, window_size, window_size).contiguous()

    def _ssim(self, img1, img2, window, window_size, channel, size_average=True):
        mu1 = F.conv2d(img1, window, padding=window_size // 2, groups=channel)
        mu2 = F.conv2d(img2, window, padding=window_size // 2, groups=channel)
        mu1_sq = mu1.pow(2)
        mu2_sq = mu2.pow(2)
        mu1_mu2 = mu1 * mu2
        sigma1_sq = F.conv2d(img1 * img1, window, padding=window_size // 2, groups=channel) - mu1_sq
        sigma2_sq = F.conv2d(img2 * img2, window, padding=window_size // 2, groups=channel) - mu2_sq
        sigma12 = F.conv2d(img1 * img2, window, padding=window_size // 2, groups=channel) - mu1_mu2
        C1 = 0.01 ** 2
        C2 = 0.03 ** 2
        ssim_map = (2 * mu1_mu2 + C1) * (2 * sigma12 + C2) / ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
        if size_average:
            return ssim_map.mean()
        return ssim_map.mean(1).mean(1).mean(1)

    def _load_from_state_dict(self, state_dict, prefix, local_metadata, strict, missing_keys, unexpected_keys, error_msgs):
        return

def __init__(self, window_size=11, size_average=True):
    super().__init__()
    self.window_size = window_size
    self.size_average = size_average
    self.channel = 1
    self.register_buffer('window', self._create_window(window_size, self.channel))

class PerceptualLoss(torch.nn.Module):

    def __init__(self, model='net-lin', net='alex', colorspace='rgb', model_path=None, spatial=False, use_gpu=True):
        super(PerceptualLoss, self).__init__()
        self.use_gpu = use_gpu
        self.spatial = spatial
        self.model = DistModel()
        self.model.initialize(model=model, net=net, use_gpu=use_gpu, colorspace=colorspace, model_path=model_path, spatial=self.spatial)

    def forward(self, pred, target, normalize=True):
        """
        Pred and target are Variables.
        If normalize is True, assumes the images are between [0,1] and then scales them between [-1,+1]
        If normalize is False, assumes the images are already between [-1,+1]
        Inputs pred and target are Nx3xHxW
        Output pytorch Variable N long
        """
        if normalize:
            target = 2 * target - 1
            pred = 2 * pred - 1
        return self.model(target, pred)

def __init__(self, model='net-lin', net='alex', colorspace='rgb', model_path=None, spatial=False, use_gpu=True):
    super(PerceptualLoss, self).__init__()
    self.use_gpu = use_gpu
    self.spatial = spatial
    self.model = DistModel()
    self.model.initialize(model=model, net=net, use_gpu=use_gpu, colorspace=colorspace, model_path=model_path, spatial=self.spatial)

class BaseModel(torch.nn.Module):

    def __init__(self):
        super().__init__()

    def name(self):
        return 'BaseModel'

    def initialize(self, use_gpu=True):
        self.use_gpu = use_gpu

    def forward(self):
        pass

    def get_image_paths(self):
        pass

    def optimize_parameters(self):
        pass

    def get_current_visuals(self):
        return self.input

    def get_current_errors(self):
        return {}

    def save(self, label):
        pass

    def save_network(self, network, path, network_label, epoch_label):
        save_filename = '%s_net_%s.pth' % (epoch_label, network_label)
        save_path = os.path.join(path, save_filename)
        torch.save(network.state_dict(), save_path)

    def load_network(self, network, network_label, epoch_label):
        save_filename = '%s_net_%s.pth' % (epoch_label, network_label)
        save_path = os.path.join(self.save_dir, save_filename)
        print('Loading network from %s' % save_path)
        network.load_state_dict(torch.load(save_path, map_location='cpu'))

    def update_learning_rate():
        pass

    def get_image_paths(self):
        return self.image_paths

    def save_done(self, flag=False):
        np.save(os.path.join(self.save_dir, 'done_flag'), flag)
        np.savetxt(os.path.join(self.save_dir, 'done_flag'), [flag], fmt='%i')

def __init__(self):
    super().__init__()

def upsample(in_tens, out_H=64):
    in_H = in_tens.shape[2]
    scale_factor = 1.0 * out_H / in_H
    return nn.Upsample(scale_factor=scale_factor, mode='bilinear', align_corners=False)(in_tens)

class PNetLin(nn.Module):

    def __init__(self, pnet_type='vgg', pnet_rand=False, pnet_tune=False, use_dropout=True, spatial=False, version='0.1', lpips=True):
        super(PNetLin, self).__init__()
        self.pnet_type = pnet_type
        self.pnet_tune = pnet_tune
        self.pnet_rand = pnet_rand
        self.spatial = spatial
        self.lpips = lpips
        self.version = version
        self.scaling_layer = ScalingLayer()
        if self.pnet_type in ['vgg', 'vgg16']:
            net_type = vgg16
            self.chns = [64, 128, 256, 512, 512]
        elif self.pnet_type == 'alex':
            net_type = alexnet
            self.chns = [64, 192, 384, 256, 256]
        elif self.pnet_type == 'squeeze':
            net_type = squeezenet
            self.chns = [64, 128, 256, 384, 384, 512, 512]
        self.L = len(self.chns)
        self.net = net_type(pretrained=not self.pnet_rand, requires_grad=self.pnet_tune)
        if lpips:
            self.lin0 = NetLinLayer(self.chns[0], use_dropout=use_dropout)
            self.lin1 = NetLinLayer(self.chns[1], use_dropout=use_dropout)
            self.lin2 = NetLinLayer(self.chns[2], use_dropout=use_dropout)
            self.lin3 = NetLinLayer(self.chns[3], use_dropout=use_dropout)
            self.lin4 = NetLinLayer(self.chns[4], use_dropout=use_dropout)
            self.lins = [self.lin0, self.lin1, self.lin2, self.lin3, self.lin4]
            if self.pnet_type == 'squeeze':
                self.lin5 = NetLinLayer(self.chns[5], use_dropout=use_dropout)
                self.lin6 = NetLinLayer(self.chns[6], use_dropout=use_dropout)
                self.lins += [self.lin5, self.lin6]

    def forward(self, in0, in1, retPerLayer=False):
        in0_input, in1_input = (self.scaling_layer(in0), self.scaling_layer(in1)) if self.version == '0.1' else (in0, in1)
        outs0, outs1 = (self.net(in0_input), self.net(in1_input))
        feats0, feats1, diffs = ({}, {}, {})
        for kk in range(self.L):
            feats0[kk], feats1[kk] = (normalize_tensor(outs0[kk]), normalize_tensor(outs1[kk]))
            diffs[kk] = (feats0[kk] - feats1[kk]) ** 2
        if self.lpips:
            if self.spatial:
                res = [upsample(self.lins[kk].model(diffs[kk]), out_H=in0.shape[2]) for kk in range(self.L)]
            else:
                res = [spatial_average(self.lins[kk].model(diffs[kk]), keepdim=True) for kk in range(self.L)]
        elif self.spatial:
            res = [upsample(diffs[kk].sum(dim=1, keepdim=True), out_H=in0.shape[2]) for kk in range(self.L)]
        else:
            res = [spatial_average(diffs[kk].sum(dim=1, keepdim=True), keepdim=True) for kk in range(self.L)]
        val = res[0]
        for l in range(1, self.L):
            val += res[l]
        if retPerLayer:
            return (val, res)
        else:
            return val

def __init__(self, pnet_type='vgg', pnet_rand=False, pnet_tune=False, use_dropout=True, spatial=False, version='0.1', lpips=True):
    super(PNetLin, self).__init__()
    self.pnet_type = pnet_type
    self.pnet_tune = pnet_tune
    self.pnet_rand = pnet_rand
    self.spatial = spatial
    self.lpips = lpips
    self.version = version
    self.scaling_layer = ScalingLayer()
    if self.pnet_type in ['vgg', 'vgg16']:
        net_type = vgg16
        self.chns = [64, 128, 256, 512, 512]
    elif self.pnet_type == 'alex':
        net_type = alexnet
        self.chns = [64, 192, 384, 256, 256]
    elif self.pnet_type == 'squeeze':
        net_type = squeezenet
        self.chns = [64, 128, 256, 384, 384, 512, 512]
    self.L = len(self.chns)
    self.net = net_type(pretrained=not self.pnet_rand, requires_grad=self.pnet_tune)
    if lpips:
        self.lin0 = NetLinLayer(self.chns[0], use_dropout=use_dropout)
        self.lin1 = NetLinLayer(self.chns[1], use_dropout=use_dropout)
        self.lin2 = NetLinLayer(self.chns[2], use_dropout=use_dropout)
        self.lin3 = NetLinLayer(self.chns[3], use_dropout=use_dropout)
        self.lin4 = NetLinLayer(self.chns[4], use_dropout=use_dropout)
        self.lins = [self.lin0, self.lin1, self.lin2, self.lin3, self.lin4]
        if self.pnet_type == 'squeeze':
            self.lin5 = NetLinLayer(self.chns[5], use_dropout=use_dropout)
            self.lin6 = NetLinLayer(self.chns[6], use_dropout=use_dropout)
            self.lins += [self.lin5, self.lin6]

class ScalingLayer(nn.Module):

    def __init__(self):
        super(ScalingLayer, self).__init__()
        self.register_buffer('shift', torch.Tensor([-0.03, -0.088, -0.188])[None, :, None, None])
        self.register_buffer('scale', torch.Tensor([0.458, 0.448, 0.45])[None, :, None, None])

    def forward(self, inp):
        return (inp - self.shift) / self.scale

def __init__(self):
    super(ScalingLayer, self).__init__()
    self.register_buffer('shift', torch.Tensor([-0.03, -0.088, -0.188])[None, :, None, None])
    self.register_buffer('scale', torch.Tensor([0.458, 0.448, 0.45])[None, :, None, None])

class NetLinLayer(nn.Module):
    """ A single linear layer which does a 1x1 conv """

    def __init__(self, chn_in, chn_out=1, use_dropout=False):
        super(NetLinLayer, self).__init__()
        layers = [nn.Dropout()] if use_dropout else []
        layers += [nn.Conv2d(chn_in, chn_out, 1, stride=1, padding=0, bias=False)]
        self.model = nn.Sequential(*layers)

def __init__(self, chn_in, chn_out=1, use_dropout=False):
    super(NetLinLayer, self).__init__()
    layers = [nn.Dropout()] if use_dropout else []
    layers += [nn.Conv2d(chn_in, chn_out, 1, stride=1, padding=0, bias=False)]
    self.model = nn.Sequential(*layers)

class Dist2LogitLayer(nn.Module):
    """ takes 2 distances, puts through fc layers, spits out value between [0,1] (if use_sigmoid is True) """

    def __init__(self, chn_mid=32, use_sigmoid=True):
        super(Dist2LogitLayer, self).__init__()
        layers = [nn.Conv2d(5, chn_mid, 1, stride=1, padding=0, bias=True)]
        layers += [nn.LeakyReLU(0.2, True)]
        layers += [nn.Conv2d(chn_mid, chn_mid, 1, stride=1, padding=0, bias=True)]
        layers += [nn.LeakyReLU(0.2, True)]
        layers += [nn.Conv2d(chn_mid, 1, 1, stride=1, padding=0, bias=True)]
        if use_sigmoid:
            layers += [nn.Sigmoid()]
        self.model = nn.Sequential(*layers)

    def forward(self, d0, d1, eps=0.1):
        return self.model(torch.cat((d0, d1, d0 - d1, d0 / (d1 + eps), d1 / (d0 + eps)), dim=1))

def __init__(self, chn_mid=32, use_sigmoid=True):
    super(Dist2LogitLayer, self).__init__()
    layers = [nn.Conv2d(5, chn_mid, 1, stride=1, padding=0, bias=True)]
    layers += [nn.LeakyReLU(0.2, True)]
    layers += [nn.Conv2d(chn_mid, chn_mid, 1, stride=1, padding=0, bias=True)]
    layers += [nn.LeakyReLU(0.2, True)]
    layers += [nn.Conv2d(chn_mid, 1, 1, stride=1, padding=0, bias=True)]
    if use_sigmoid:
        layers += [nn.Sigmoid()]
    self.model = nn.Sequential(*layers)

class BCERankingLoss(nn.Module):

    def __init__(self, chn_mid=32):
        super(BCERankingLoss, self).__init__()
        self.net = Dist2LogitLayer(chn_mid=chn_mid)
        self.loss = torch.nn.BCELoss()

    def forward(self, d0, d1, judge):
        per = (judge + 1.0) / 2.0
        self.logit = self.net(d0, d1)
        return self.loss(self.logit, per)

def __init__(self, chn_mid=32):
    super(BCERankingLoss, self).__init__()
    self.net = Dist2LogitLayer(chn_mid=chn_mid)
    self.loss = torch.nn.BCELoss()

class FakeNet(nn.Module):

    def __init__(self, use_gpu=True, colorspace='Lab'):
        super(FakeNet, self).__init__()
        self.use_gpu = use_gpu
        self.colorspace = colorspace

def __init__(self, use_gpu=True, colorspace='Lab'):
    super(FakeNet, self).__init__()
    self.use_gpu = use_gpu
    self.colorspace = colorspace

class squeezenet(torch.nn.Module):

    def __init__(self, requires_grad=False, pretrained=True):
        super(squeezenet, self).__init__()
        pretrained_features = tv.squeezenet1_1(pretrained=pretrained).features
        self.slice1 = torch.nn.Sequential()
        self.slice2 = torch.nn.Sequential()
        self.slice3 = torch.nn.Sequential()
        self.slice4 = torch.nn.Sequential()
        self.slice5 = torch.nn.Sequential()
        self.slice6 = torch.nn.Sequential()
        self.slice7 = torch.nn.Sequential()
        self.N_slices = 7
        for x in range(2):
            self.slice1.add_module(str(x), pretrained_features[x])
        for x in range(2, 5):
            self.slice2.add_module(str(x), pretrained_features[x])
        for x in range(5, 8):
            self.slice3.add_module(str(x), pretrained_features[x])
        for x in range(8, 10):
            self.slice4.add_module(str(x), pretrained_features[x])
        for x in range(10, 11):
            self.slice5.add_module(str(x), pretrained_features[x])
        for x in range(11, 12):
            self.slice6.add_module(str(x), pretrained_features[x])
        for x in range(12, 13):
            self.slice7.add_module(str(x), pretrained_features[x])
        if not requires_grad:
            for param in self.parameters():
                param.requires_grad = False

    def forward(self, X):
        h = self.slice1(X)
        h_relu1 = h
        h = self.slice2(h)
        h_relu2 = h
        h = self.slice3(h)
        h_relu3 = h
        h = self.slice4(h)
        h_relu4 = h
        h = self.slice5(h)
        h_relu5 = h
        h = self.slice6(h)
        h_relu6 = h
        h = self.slice7(h)
        h_relu7 = h
        vgg_outputs = namedtuple('SqueezeOutputs', ['relu1', 'relu2', 'relu3', 'relu4', 'relu5', 'relu6', 'relu7'])
        out = vgg_outputs(h_relu1, h_relu2, h_relu3, h_relu4, h_relu5, h_relu6, h_relu7)
        return out

def __init__(self, requires_grad=False, pretrained=True):
    super(squeezenet, self).__init__()
    pretrained_features = tv.squeezenet1_1(pretrained=pretrained).features
    self.slice1 = torch.nn.Sequential()
    self.slice2 = torch.nn.Sequential()
    self.slice3 = torch.nn.Sequential()
    self.slice4 = torch.nn.Sequential()
    self.slice5 = torch.nn.Sequential()
    self.slice6 = torch.nn.Sequential()
    self.slice7 = torch.nn.Sequential()
    self.N_slices = 7
    for x in range(2):
        self.slice1.add_module(str(x), pretrained_features[x])
    for x in range(2, 5):
        self.slice2.add_module(str(x), pretrained_features[x])
    for x in range(5, 8):
        self.slice3.add_module(str(x), pretrained_features[x])
    for x in range(8, 10):
        self.slice4.add_module(str(x), pretrained_features[x])
    for x in range(10, 11):
        self.slice5.add_module(str(x), pretrained_features[x])
    for x in range(11, 12):
        self.slice6.add_module(str(x), pretrained_features[x])
    for x in range(12, 13):
        self.slice7.add_module(str(x), pretrained_features[x])
    if not requires_grad:
        for param in self.parameters():
            param.requires_grad = False

class alexnet(torch.nn.Module):

    def __init__(self, requires_grad=False, pretrained=True):
        super(alexnet, self).__init__()
        alexnet_pretrained_features = tv.alexnet(pretrained=pretrained).features
        self.slice1 = torch.nn.Sequential()
        self.slice2 = torch.nn.Sequential()
        self.slice3 = torch.nn.Sequential()
        self.slice4 = torch.nn.Sequential()
        self.slice5 = torch.nn.Sequential()
        self.N_slices = 5
        for x in range(2):
            self.slice1.add_module(str(x), alexnet_pretrained_features[x])
        for x in range(2, 5):
            self.slice2.add_module(str(x), alexnet_pretrained_features[x])
        for x in range(5, 8):
            self.slice3.add_module(str(x), alexnet_pretrained_features[x])
        for x in range(8, 10):
            self.slice4.add_module(str(x), alexnet_pretrained_features[x])
        for x in range(10, 12):
            self.slice5.add_module(str(x), alexnet_pretrained_features[x])
        if not requires_grad:
            for param in self.parameters():
                param.requires_grad = False

    def forward(self, X):
        h = self.slice1(X)
        h_relu1 = h
        h = self.slice2(h)
        h_relu2 = h
        h = self.slice3(h)
        h_relu3 = h
        h = self.slice4(h)
        h_relu4 = h
        h = self.slice5(h)
        h_relu5 = h
        alexnet_outputs = namedtuple('AlexnetOutputs', ['relu1', 'relu2', 'relu3', 'relu4', 'relu5'])
        out = alexnet_outputs(h_relu1, h_relu2, h_relu3, h_relu4, h_relu5)
        return out

def __init__(self, requires_grad=False, pretrained=True):
    super(alexnet, self).__init__()
    alexnet_pretrained_features = tv.alexnet(pretrained=pretrained).features
    self.slice1 = torch.nn.Sequential()
    self.slice2 = torch.nn.Sequential()
    self.slice3 = torch.nn.Sequential()
    self.slice4 = torch.nn.Sequential()
    self.slice5 = torch.nn.Sequential()
    self.N_slices = 5
    for x in range(2):
        self.slice1.add_module(str(x), alexnet_pretrained_features[x])
    for x in range(2, 5):
        self.slice2.add_module(str(x), alexnet_pretrained_features[x])
    for x in range(5, 8):
        self.slice3.add_module(str(x), alexnet_pretrained_features[x])
    for x in range(8, 10):
        self.slice4.add_module(str(x), alexnet_pretrained_features[x])
    for x in range(10, 12):
        self.slice5.add_module(str(x), alexnet_pretrained_features[x])
    if not requires_grad:
        for param in self.parameters():
            param.requires_grad = False

class vgg16(torch.nn.Module):

    def __init__(self, requires_grad=False, pretrained=True):
        super(vgg16, self).__init__()
        vgg_pretrained_features = tv.vgg16(pretrained=pretrained).features
        self.slice1 = torch.nn.Sequential()
        self.slice2 = torch.nn.Sequential()
        self.slice3 = torch.nn.Sequential()
        self.slice4 = torch.nn.Sequential()
        self.slice5 = torch.nn.Sequential()
        self.N_slices = 5
        for x in range(4):
            self.slice1.add_module(str(x), vgg_pretrained_features[x])
        for x in range(4, 9):
            self.slice2.add_module(str(x), vgg_pretrained_features[x])
        for x in range(9, 16):
            self.slice3.add_module(str(x), vgg_pretrained_features[x])
        for x in range(16, 23):
            self.slice4.add_module(str(x), vgg_pretrained_features[x])
        for x in range(23, 30):
            self.slice5.add_module(str(x), vgg_pretrained_features[x])
        if not requires_grad:
            for param in self.parameters():
                param.requires_grad = False

    def forward(self, X):
        h = self.slice1(X)
        h_relu1_2 = h
        h = self.slice2(h)
        h_relu2_2 = h
        h = self.slice3(h)
        h_relu3_3 = h
        h = self.slice4(h)
        h_relu4_3 = h
        h = self.slice5(h)
        h_relu5_3 = h
        vgg_outputs = namedtuple('VggOutputs', ['relu1_2', 'relu2_2', 'relu3_3', 'relu4_3', 'relu5_3'])
        out = vgg_outputs(h_relu1_2, h_relu2_2, h_relu3_3, h_relu4_3, h_relu5_3)
        return out

def __init__(self, requires_grad=False, pretrained=True):
    super(vgg16, self).__init__()
    vgg_pretrained_features = tv.vgg16(pretrained=pretrained).features
    self.slice1 = torch.nn.Sequential()
    self.slice2 = torch.nn.Sequential()
    self.slice3 = torch.nn.Sequential()
    self.slice4 = torch.nn.Sequential()
    self.slice5 = torch.nn.Sequential()
    self.N_slices = 5
    for x in range(4):
        self.slice1.add_module(str(x), vgg_pretrained_features[x])
    for x in range(4, 9):
        self.slice2.add_module(str(x), vgg_pretrained_features[x])
    for x in range(9, 16):
        self.slice3.add_module(str(x), vgg_pretrained_features[x])
    for x in range(16, 23):
        self.slice4.add_module(str(x), vgg_pretrained_features[x])
    for x in range(23, 30):
        self.slice5.add_module(str(x), vgg_pretrained_features[x])
    if not requires_grad:
        for param in self.parameters():
            param.requires_grad = False

class resnet(torch.nn.Module):

    def __init__(self, requires_grad=False, pretrained=True, num=18):
        super(resnet, self).__init__()
        if num == 18:
            self.net = tv.resnet18(pretrained=pretrained)
        elif num == 34:
            self.net = tv.resnet34(pretrained=pretrained)
        elif num == 50:
            self.net = tv.resnet50(pretrained=pretrained)
        elif num == 101:
            self.net = tv.resnet101(pretrained=pretrained)
        elif num == 152:
            self.net = tv.resnet152(pretrained=pretrained)
        self.N_slices = 5
        self.conv1 = self.net.conv1
        self.bn1 = self.net.bn1
        self.relu = self.net.relu
        self.maxpool = self.net.maxpool
        self.layer1 = self.net.layer1
        self.layer2 = self.net.layer2
        self.layer3 = self.net.layer3
        self.layer4 = self.net.layer4

    def forward(self, X):
        h = self.conv1(X)
        h = self.bn1(h)
        h = self.relu(h)
        h_relu1 = h
        h = self.maxpool(h)
        h = self.layer1(h)
        h_conv2 = h
        h = self.layer2(h)
        h_conv3 = h
        h = self.layer3(h)
        h_conv4 = h
        h = self.layer4(h)
        h_conv5 = h
        outputs = namedtuple('Outputs', ['relu1', 'conv2', 'conv3', 'conv4', 'conv5'])
        out = outputs(h_relu1, h_conv2, h_conv3, h_conv4, h_conv5)
        return out

def __init__(self, requires_grad=False, pretrained=True, num=18):
    super(resnet, self).__init__()
    if num == 18:
        self.net = tv.resnet18(pretrained=pretrained)
    elif num == 34:
        self.net = tv.resnet34(pretrained=pretrained)
    elif num == 50:
        self.net = tv.resnet50(pretrained=pretrained)
    elif num == 101:
        self.net = tv.resnet101(pretrained=pretrained)
    elif num == 152:
        self.net = tv.resnet152(pretrained=pretrained)
    self.N_slices = 5
    self.conv1 = self.net.conv1
    self.bn1 = self.net.bn1
    self.relu = self.net.relu
    self.maxpool = self.net.maxpool
    self.layer1 = self.net.layer1
    self.layer2 = self.net.layer2
    self.layer3 = self.net.layer3
    self.layer4 = self.net.layer4

class InceptionV3(nn.Module):
    """Pretrained InceptionV3 network returning feature maps"""
    DEFAULT_BLOCK_INDEX = 3
    BLOCK_INDEX_BY_DIM = {64: 0, 192: 1, 768: 2, 2048: 3}

    def __init__(self, output_blocks=[DEFAULT_BLOCK_INDEX], resize_input=True, normalize_input=True, requires_grad=False, use_fid_inception=True):
        """Build pretrained InceptionV3

        Parameters
        ----------
        output_blocks : list of int
            Indices of blocks to return features of. Possible values are:
                - 0: corresponds to output of first max pooling
                - 1: corresponds to output of second max pooling
                - 2: corresponds to output which is fed to aux classifier
                - 3: corresponds to output of final average pooling
        resize_input : bool
            If true, bilinearly resizes input to width and height 299 before
            feeding input to model. As the network without fully connected
            layers is fully convolutional, it should be able to handle inputs
            of arbitrary size, so resizing might not be strictly needed
        normalize_input : bool
            If true, scales the input from range (0, 1) to the range the
            pretrained Inception network expects, namely (-1, 1)
        requires_grad : bool
            If true, parameters of the model require gradients. Possibly useful
            for finetuning the network
        use_fid_inception : bool
            If true, uses the pretrained Inception model used in Tensorflow's
            FID implementation. If false, uses the pretrained Inception model
            available in torchvision. The FID Inception model has different
            weights and a slightly different structure from torchvision's
            Inception model. If you want to compute FID scores, you are
            strongly advised to set this parameter to true to get comparable
            results.
        """
        super(InceptionV3, self).__init__()
        self.resize_input = resize_input
        self.normalize_input = normalize_input
        self.output_blocks = sorted(output_blocks)
        self.last_needed_block = max(output_blocks)
        assert self.last_needed_block <= 3, 'Last possible output block index is 3'
        self.blocks = nn.ModuleList()
        if use_fid_inception:
            inception = fid_inception_v3()
        else:
            inception = models.inception_v3(pretrained=True)
        block0 = [inception.Conv2d_1a_3x3, inception.Conv2d_2a_3x3, inception.Conv2d_2b_3x3, nn.MaxPool2d(kernel_size=3, stride=2)]
        self.blocks.append(nn.Sequential(*block0))
        if self.last_needed_block >= 1:
            block1 = [inception.Conv2d_3b_1x1, inception.Conv2d_4a_3x3, nn.MaxPool2d(kernel_size=3, stride=2)]
            self.blocks.append(nn.Sequential(*block1))
        if self.last_needed_block >= 2:
            block2 = [inception.Mixed_5b, inception.Mixed_5c, inception.Mixed_5d, inception.Mixed_6a, inception.Mixed_6b, inception.Mixed_6c, inception.Mixed_6d, inception.Mixed_6e]
            self.blocks.append(nn.Sequential(*block2))
        if self.last_needed_block >= 3:
            block3 = [inception.Mixed_7a, inception.Mixed_7b, inception.Mixed_7c, nn.AdaptiveAvgPool2d(output_size=(1, 1))]
            self.blocks.append(nn.Sequential(*block3))
        for param in self.parameters():
            param.requires_grad = requires_grad

    def forward(self, inp):
        """Get Inception feature maps

        Parameters
        ----------
        inp : torch.autograd.Variable
            Input tensor of shape Bx3xHxW. Values are expected to be in
            range (0, 1)

        Returns
        -------
        List of torch.autograd.Variable, corresponding to the selected output
        block, sorted ascending by index
        """
        outp = []
        x = inp
        if self.resize_input:
            x = F.interpolate(x, size=(299, 299), mode='bilinear', align_corners=False)
        if self.normalize_input:
            x = 2 * x - 1
        for idx, block in enumerate(self.blocks):
            x = block(x)
            if idx in self.output_blocks:
                outp.append(x)
            if idx == self.last_needed_block:
                break
        return outp

def __init__(self, output_blocks=[DEFAULT_BLOCK_INDEX], resize_input=True, normalize_input=True, requires_grad=False, use_fid_inception=True):
    """Build pretrained InceptionV3

        Parameters
        ----------
        output_blocks : list of int
            Indices of blocks to return features of. Possible values are:
                - 0: corresponds to output of first max pooling
                - 1: corresponds to output of second max pooling
                - 2: corresponds to output which is fed to aux classifier
                - 3: corresponds to output of final average pooling
        resize_input : bool
            If true, bilinearly resizes input to width and height 299 before
            feeding input to model. As the network without fully connected
            layers is fully convolutional, it should be able to handle inputs
            of arbitrary size, so resizing might not be strictly needed
        normalize_input : bool
            If true, scales the input from range (0, 1) to the range the
            pretrained Inception network expects, namely (-1, 1)
        requires_grad : bool
            If true, parameters of the model require gradients. Possibly useful
            for finetuning the network
        use_fid_inception : bool
            If true, uses the pretrained Inception model used in Tensorflow's
            FID implementation. If false, uses the pretrained Inception model
            available in torchvision. The FID Inception model has different
            weights and a slightly different structure from torchvision's
            Inception model. If you want to compute FID scores, you are
            strongly advised to set this parameter to true to get comparable
            results.
        """
    super(InceptionV3, self).__init__()
    self.resize_input = resize_input
    self.normalize_input = normalize_input
    self.output_blocks = sorted(output_blocks)
    self.last_needed_block = max(output_blocks)
    assert self.last_needed_block <= 3, 'Last possible output block index is 3'
    self.blocks = nn.ModuleList()
    if use_fid_inception:
        inception = fid_inception_v3()
    else:
        inception = models.inception_v3(pretrained=True)
    block0 = [inception.Conv2d_1a_3x3, inception.Conv2d_2a_3x3, inception.Conv2d_2b_3x3, nn.MaxPool2d(kernel_size=3, stride=2)]
    self.blocks.append(nn.Sequential(*block0))
    if self.last_needed_block >= 1:
        block1 = [inception.Conv2d_3b_1x1, inception.Conv2d_4a_3x3, nn.MaxPool2d(kernel_size=3, stride=2)]
        self.blocks.append(nn.Sequential(*block1))
    if self.last_needed_block >= 2:
        block2 = [inception.Mixed_5b, inception.Mixed_5c, inception.Mixed_5d, inception.Mixed_6a, inception.Mixed_6b, inception.Mixed_6c, inception.Mixed_6d, inception.Mixed_6e]
        self.blocks.append(nn.Sequential(*block2))
    if self.last_needed_block >= 3:
        block3 = [inception.Mixed_7a, inception.Mixed_7b, inception.Mixed_7c, nn.AdaptiveAvgPool2d(output_size=(1, 1))]
        self.blocks.append(nn.Sequential(*block3))
    for param in self.parameters():
        param.requires_grad = requires_grad

class FIDInceptionA(models.inception.InceptionA):
    """InceptionA block patched for FID computation"""

    def __init__(self, in_channels, pool_features):
        super(FIDInceptionA, self).__init__(in_channels, pool_features)

    def forward(self, x):
        branch1x1 = self.branch1x1(x)
        branch5x5 = self.branch5x5_1(x)
        branch5x5 = self.branch5x5_2(branch5x5)
        branch3x3dbl = self.branch3x3dbl_1(x)
        branch3x3dbl = self.branch3x3dbl_2(branch3x3dbl)
        branch3x3dbl = self.branch3x3dbl_3(branch3x3dbl)
        branch_pool = F.avg_pool2d(x, kernel_size=3, stride=1, padding=1, count_include_pad=False)
        branch_pool = self.branch_pool(branch_pool)
        outputs = [branch1x1, branch5x5, branch3x3dbl, branch_pool]
        return torch.cat(outputs, 1)

def __init__(self, in_channels, pool_features):
    super(FIDInceptionA, self).__init__(in_channels, pool_features)

class FIDInceptionC(models.inception.InceptionC):
    """InceptionC block patched for FID computation"""

    def __init__(self, in_channels, channels_7x7):
        super(FIDInceptionC, self).__init__(in_channels, channels_7x7)

    def forward(self, x):
        branch1x1 = self.branch1x1(x)
        branch7x7 = self.branch7x7_1(x)
        branch7x7 = self.branch7x7_2(branch7x7)
        branch7x7 = self.branch7x7_3(branch7x7)
        branch7x7dbl = self.branch7x7dbl_1(x)
        branch7x7dbl = self.branch7x7dbl_2(branch7x7dbl)
        branch7x7dbl = self.branch7x7dbl_3(branch7x7dbl)
        branch7x7dbl = self.branch7x7dbl_4(branch7x7dbl)
        branch7x7dbl = self.branch7x7dbl_5(branch7x7dbl)
        branch_pool = F.avg_pool2d(x, kernel_size=3, stride=1, padding=1, count_include_pad=False)
        branch_pool = self.branch_pool(branch_pool)
        outputs = [branch1x1, branch7x7, branch7x7dbl, branch_pool]
        return torch.cat(outputs, 1)

def __init__(self, in_channels, channels_7x7):
    super(FIDInceptionC, self).__init__(in_channels, channels_7x7)

class FIDInceptionE_1(models.inception.InceptionE):
    """First InceptionE block patched for FID computation"""

    def __init__(self, in_channels):
        super(FIDInceptionE_1, self).__init__(in_channels)

    def forward(self, x):
        branch1x1 = self.branch1x1(x)
        branch3x3 = self.branch3x3_1(x)
        branch3x3 = [self.branch3x3_2a(branch3x3), self.branch3x3_2b(branch3x3)]
        branch3x3 = torch.cat(branch3x3, 1)
        branch3x3dbl = self.branch3x3dbl_1(x)
        branch3x3dbl = self.branch3x3dbl_2(branch3x3dbl)
        branch3x3dbl = [self.branch3x3dbl_3a(branch3x3dbl), self.branch3x3dbl_3b(branch3x3dbl)]
        branch3x3dbl = torch.cat(branch3x3dbl, 1)
        branch_pool = F.avg_pool2d(x, kernel_size=3, stride=1, padding=1, count_include_pad=False)
        branch_pool = self.branch_pool(branch_pool)
        outputs = [branch1x1, branch3x3, branch3x3dbl, branch_pool]
        return torch.cat(outputs, 1)

def __init__(self, in_channels):
    super(FIDInceptionE_1, self).__init__(in_channels)

class FIDInceptionE_2(models.inception.InceptionE):
    """Second InceptionE block patched for FID computation"""

    def __init__(self, in_channels):
        super(FIDInceptionE_2, self).__init__(in_channels)

    def forward(self, x):
        branch1x1 = self.branch1x1(x)
        branch3x3 = self.branch3x3_1(x)
        branch3x3 = [self.branch3x3_2a(branch3x3), self.branch3x3_2b(branch3x3)]
        branch3x3 = torch.cat(branch3x3, 1)
        branch3x3dbl = self.branch3x3dbl_1(x)
        branch3x3dbl = self.branch3x3dbl_2(branch3x3dbl)
        branch3x3dbl = [self.branch3x3dbl_3a(branch3x3dbl), self.branch3x3dbl_3b(branch3x3dbl)]
        branch3x3dbl = torch.cat(branch3x3dbl, 1)
        branch_pool = F.max_pool2d(x, kernel_size=3, stride=1, padding=1)
        branch_pool = self.branch_pool(branch_pool)
        outputs = [branch1x1, branch3x3, branch3x3dbl, branch_pool]
        return torch.cat(outputs, 1)

def __init__(self, in_channels):
    super(FIDInceptionE_2, self).__init__(in_channels)

def conv_bn(inp, oup, stride):
    return nn.Sequential(nn.Conv2d(inp, oup, 3, stride, 1, bias=False), BatchNorm2d(oup), nn.ReLU6(inplace=True))

def conv_1x1_bn(inp, oup):
    return nn.Sequential(nn.Conv2d(inp, oup, 1, 1, 0, bias=False), BatchNorm2d(oup), nn.ReLU6(inplace=True))

class InvertedResidual(nn.Module):

    def __init__(self, inp, oup, stride, expand_ratio):
        super(InvertedResidual, self).__init__()
        self.stride = stride
        assert stride in [1, 2]
        hidden_dim = round(inp * expand_ratio)
        self.use_res_connect = self.stride == 1 and inp == oup
        if expand_ratio == 1:
            self.conv = nn.Sequential(nn.Conv2d(hidden_dim, hidden_dim, 3, stride, 1, groups=hidden_dim, bias=False), BatchNorm2d(hidden_dim), nn.ReLU6(inplace=True), nn.Conv2d(hidden_dim, oup, 1, 1, 0, bias=False), BatchNorm2d(oup))
        else:
            self.conv = nn.Sequential(nn.Conv2d(inp, hidden_dim, 1, 1, 0, bias=False), BatchNorm2d(hidden_dim), nn.ReLU6(inplace=True), nn.Conv2d(hidden_dim, hidden_dim, 3, stride, 1, groups=hidden_dim, bias=False), BatchNorm2d(hidden_dim), nn.ReLU6(inplace=True), nn.Conv2d(hidden_dim, oup, 1, 1, 0, bias=False), BatchNorm2d(oup))

    def forward(self, x):
        if self.use_res_connect:
            return x + self.conv(x)
        else:
            return self.conv(x)

def __init__(self, inp, oup, stride, expand_ratio):
    super(InvertedResidual, self).__init__()
    self.stride = stride
    assert stride in [1, 2]
    hidden_dim = round(inp * expand_ratio)
    self.use_res_connect = self.stride == 1 and inp == oup
    if expand_ratio == 1:
        self.conv = nn.Sequential(nn.Conv2d(hidden_dim, hidden_dim, 3, stride, 1, groups=hidden_dim, bias=False), BatchNorm2d(hidden_dim), nn.ReLU6(inplace=True), nn.Conv2d(hidden_dim, oup, 1, 1, 0, bias=False), BatchNorm2d(oup))
    else:
        self.conv = nn.Sequential(nn.Conv2d(inp, hidden_dim, 1, 1, 0, bias=False), BatchNorm2d(hidden_dim), nn.ReLU6(inplace=True), nn.Conv2d(hidden_dim, hidden_dim, 3, stride, 1, groups=hidden_dim, bias=False), BatchNorm2d(hidden_dim), nn.ReLU6(inplace=True), nn.Conv2d(hidden_dim, oup, 1, 1, 0, bias=False), BatchNorm2d(oup))

class MobileNetV2(nn.Module):

    def __init__(self, n_class=1000, input_size=224, width_mult=1.0):
        super(MobileNetV2, self).__init__()
        block = InvertedResidual
        input_channel = 32
        last_channel = 1280
        interverted_residual_setting = [[1, 16, 1, 1], [6, 24, 2, 2], [6, 32, 3, 2], [6, 64, 4, 2], [6, 96, 3, 1], [6, 160, 3, 2], [6, 320, 1, 1]]
        assert input_size % 32 == 0
        input_channel = int(input_channel * width_mult)
        self.last_channel = int(last_channel * width_mult) if width_mult > 1.0 else last_channel
        self.features = [conv_bn(3, input_channel, 2)]
        for t, c, n, s in interverted_residual_setting:
            output_channel = int(c * width_mult)
            for i in range(n):
                if i == 0:
                    self.features.append(block(input_channel, output_channel, s, expand_ratio=t))
                else:
                    self.features.append(block(input_channel, output_channel, 1, expand_ratio=t))
                input_channel = output_channel
        self.features.append(conv_1x1_bn(input_channel, self.last_channel))
        self.features = nn.Sequential(*self.features)
        self.classifier = nn.Sequential(nn.Dropout(0.2), nn.Linear(self.last_channel, n_class))
        self._initialize_weights()

    def forward(self, x):
        x = self.features(x)
        x = x.mean(3).mean(2)
        x = self.classifier(x)
        return x

    def _initialize_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                n = m.kernel_size[0] * m.kernel_size[1] * m.out_channels
                m.weight.data.normal_(0, math.sqrt(2.0 / n))
                if m.bias is not None:
                    m.bias.data.zero_()
            elif isinstance(m, BatchNorm2d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()
            elif isinstance(m, nn.Linear):
                n = m.weight.size(1)
                m.weight.data.normal_(0, 0.01)
                m.bias.data.zero_()

def __init__(self, n_class=1000, input_size=224, width_mult=1.0):
    super(MobileNetV2, self).__init__()
    block = InvertedResidual
    input_channel = 32
    last_channel = 1280
    interverted_residual_setting = [[1, 16, 1, 1], [6, 24, 2, 2], [6, 32, 3, 2], [6, 64, 4, 2], [6, 96, 3, 1], [6, 160, 3, 2], [6, 320, 1, 1]]
    assert input_size % 32 == 0
    input_channel = int(input_channel * width_mult)
    self.last_channel = int(last_channel * width_mult) if width_mult > 1.0 else last_channel
    self.features = [conv_bn(3, input_channel, 2)]
    for t, c, n, s in interverted_residual_setting:
        output_channel = int(c * width_mult)
        for i in range(n):
            if i == 0:
                self.features.append(block(input_channel, output_channel, s, expand_ratio=t))
            else:
                self.features.append(block(input_channel, output_channel, 1, expand_ratio=t))
            input_channel = output_channel
    self.features.append(conv_1x1_bn(input_channel, self.last_channel))
    self.features = nn.Sequential(*self.features)
    self.classifier = nn.Sequential(nn.Dropout(0.2), nn.Linear(self.last_channel, n_class))
    self._initialize_weights()

def _initialize_weights(self):
    for m in self.modules():
        if isinstance(m, nn.Conv2d):
            n = m.kernel_size[0] * m.kernel_size[1] * m.out_channels
            m.weight.data.normal_(0, math.sqrt(2.0 / n))
            if m.bias is not None:
                m.bias.data.zero_()
        elif isinstance(m, BatchNorm2d):
            m.weight.data.fill_(1)
            m.bias.data.zero_()
        elif isinstance(m, nn.Linear):
            n = m.weight.size(1)
            m.weight.data.normal_(0, 0.01)
            m.bias.data.zero_()

def conv3x3_bn_relu(in_planes, out_planes, stride=1):
    return nn.Sequential(nn.Conv2d(in_planes, out_planes, kernel_size=3, stride=stride, padding=1, bias=False), BatchNorm2d(out_planes), nn.ReLU(inplace=True))

class SegmentationModule(nn.Module):

    def __init__(self, weights_path, num_classes=150, arch_encoder='resnet50dilated', drop_last_conv=False, net_enc=None, net_dec=None, encode=None, use_default_normalization=False, return_feature_maps=False, return_feature_maps_level=3, return_feature_maps_only=True, **kwargs):
        super().__init__()
        self.weights_path = weights_path
        self.drop_last_conv = drop_last_conv
        self.arch_encoder = arch_encoder
        if self.arch_encoder == 'resnet50dilated':
            self.arch_decoder = 'ppm_deepsup'
            self.fc_dim = 2048
        elif self.arch_encoder == 'mobilenetv2dilated':
            self.arch_decoder = 'c1_deepsup'
            self.fc_dim = 320
        else:
            raise NotImplementedError(f'No such arch_encoder={self.arch_encoder}')
        model_builder_kwargs = dict(arch_encoder=self.arch_encoder, arch_decoder=self.arch_decoder, fc_dim=self.fc_dim, drop_last_conv=drop_last_conv, weights_path=self.weights_path)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.encoder = ModelBuilder.get_encoder(**model_builder_kwargs) if net_enc is None else net_enc
        self.decoder = ModelBuilder.get_decoder(**model_builder_kwargs) if net_dec is None else net_dec
        self.use_default_normalization = use_default_normalization
        self.default_normalization = NormalizeTensor(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        self.encode = encode
        self.return_feature_maps = return_feature_maps
        assert 0 <= return_feature_maps_level <= 3
        self.return_feature_maps_level = return_feature_maps_level

    def normalize_input(self, tensor):
        if tensor.min() < 0 or tensor.max() > 1:
            raise ValueError('Tensor should be 0..1 before using normalize_input')
        return self.default_normalization(tensor)

    @property
    def feature_maps_channels(self):
        return 256 * 2 ** self.return_feature_maps_level

    def forward(self, img_data, segSize=None):
        if segSize is None:
            raise NotImplementedError('Please pass segSize param. By default: (300, 300)')
        fmaps = self.encoder(img_data, return_feature_maps=True)
        pred = self.decoder(fmaps, segSize=segSize)
        if self.return_feature_maps:
            return (pred, fmaps)
        return pred

    def multi_mask_from_multiclass(self, pred, classes):

        def isin(ar1, ar2):
            return (ar1[..., None] == ar2).any(-1).float()
        return isin(pred, torch.LongTensor(classes).to(self.device))

    @staticmethod
    def multi_mask_from_multiclass_probs(scores, classes):
        res = None
        for c in classes:
            if res is None:
                res = scores[:, c]
            else:
                res += scores[:, c]
        return res

    def predict(self, tensor, imgSizes=(-1,), segSize=None):
        """Entry-point for segmentation. Use this methods instead of forward
        Arguments:
            tensor {torch.Tensor} -- BCHW
        Keyword Arguments:
            imgSizes {tuple or list} -- imgSizes for segmentation input.
                default: (300, 450)
                original implementation: (300, 375, 450, 525, 600)

        """
        if segSize is None:
            segSize = tensor.shape[-2:]
        segSize = (tensor.shape[2], tensor.shape[3])
        with torch.no_grad():
            if self.use_default_normalization:
                tensor = self.normalize_input(tensor)
            scores = torch.zeros(1, NUM_CLASS, segSize[0], segSize[1]).to(self.device)
            features = torch.zeros(1, self.feature_maps_channels, segSize[0], segSize[1]).to(self.device)
            result = []
            for img_size in imgSizes:
                if img_size != -1:
                    img_data = F.interpolate(tensor.clone(), size=img_size)
                else:
                    img_data = tensor.clone()
                if self.return_feature_maps:
                    pred_current, fmaps = self.forward(img_data, segSize=segSize)
                else:
                    pred_current = self.forward(img_data, segSize=segSize)
                result.append(pred_current)
                scores = scores + pred_current / len(imgSizes)
                if self.return_feature_maps:
                    features = features + F.interpolate(fmaps[self.return_feature_maps_level], size=segSize) / len(imgSizes)
            _, pred = torch.max(scores, dim=1)
            if self.return_feature_maps:
                return features
            return (pred, result)

    def get_edges(self, t):
        edge = torch.cuda.ByteTensor(t.size()).zero_()
        edge[:, :, :, 1:] = edge[:, :, :, 1:] | (t[:, :, :, 1:] != t[:, :, :, :-1])
        edge[:, :, :, :-1] = edge[:, :, :, :-1] | (t[:, :, :, 1:] != t[:, :, :, :-1])
        edge[:, :, 1:, :] = edge[:, :, 1:, :] | (t[:, :, 1:, :] != t[:, :, :-1, :])
        edge[:, :, :-1, :] = edge[:, :, :-1, :] | (t[:, :, 1:, :] != t[:, :, :-1, :])
        if True:
            return edge.half()
        return edge.float()

def __init__(self, weights_path, num_classes=150, arch_encoder='resnet50dilated', drop_last_conv=False, net_enc=None, net_dec=None, encode=None, use_default_normalization=False, return_feature_maps=False, return_feature_maps_level=3, return_feature_maps_only=True, **kwargs):
    super().__init__()
    self.weights_path = weights_path
    self.drop_last_conv = drop_last_conv
    self.arch_encoder = arch_encoder
    if self.arch_encoder == 'resnet50dilated':
        self.arch_decoder = 'ppm_deepsup'
        self.fc_dim = 2048
    elif self.arch_encoder == 'mobilenetv2dilated':
        self.arch_decoder = 'c1_deepsup'
        self.fc_dim = 320
    else:
        raise NotImplementedError(f'No such arch_encoder={self.arch_encoder}')
    model_builder_kwargs = dict(arch_encoder=self.arch_encoder, arch_decoder=self.arch_decoder, fc_dim=self.fc_dim, drop_last_conv=drop_last_conv, weights_path=self.weights_path)
    self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    self.encoder = ModelBuilder.get_encoder(**model_builder_kwargs) if net_enc is None else net_enc
    self.decoder = ModelBuilder.get_decoder(**model_builder_kwargs) if net_dec is None else net_dec
    self.use_default_normalization = use_default_normalization
    self.default_normalization = NormalizeTensor(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    self.encode = encode
    self.return_feature_maps = return_feature_maps
    assert 0 <= return_feature_maps_level <= 3
    self.return_feature_maps_level = return_feature_maps_level

class PPMDeepsup(nn.Module):

    def __init__(self, num_class=NUM_CLASS, fc_dim=4096, use_softmax=False, pool_scales=(1, 2, 3, 6), drop_last_conv=False):
        super().__init__()
        self.use_softmax = use_softmax
        self.drop_last_conv = drop_last_conv
        self.ppm = []
        for scale in pool_scales:
            self.ppm.append(nn.Sequential(nn.AdaptiveAvgPool2d(scale), nn.Conv2d(fc_dim, 512, kernel_size=1, bias=False), BatchNorm2d(512), nn.ReLU(inplace=True)))
        self.ppm = nn.ModuleList(self.ppm)
        self.cbr_deepsup = conv3x3_bn_relu(fc_dim // 2, fc_dim // 4, 1)
        self.conv_last = nn.Sequential(nn.Conv2d(fc_dim + len(pool_scales) * 512, 512, kernel_size=3, padding=1, bias=False), BatchNorm2d(512), nn.ReLU(inplace=True), nn.Dropout2d(0.1), nn.Conv2d(512, num_class, kernel_size=1))
        self.conv_last_deepsup = nn.Conv2d(fc_dim // 4, num_class, 1, 1, 0)
        self.dropout_deepsup = nn.Dropout2d(0.1)

    def forward(self, conv_out, segSize=None):
        conv5 = conv_out[-1]
        input_size = conv5.size()
        ppm_out = [conv5]
        for pool_scale in self.ppm:
            ppm_out.append(nn.functional.interpolate(pool_scale(conv5), (input_size[2], input_size[3]), mode='bilinear', align_corners=False))
        ppm_out = torch.cat(ppm_out, 1)
        if self.drop_last_conv:
            return ppm_out
        else:
            x = self.conv_last(ppm_out)
            if self.use_softmax:
                x = nn.functional.interpolate(x, size=segSize, mode='bilinear', align_corners=False)
                x = nn.functional.softmax(x, dim=1)
                return x
            conv4 = conv_out[-2]
            _ = self.cbr_deepsup(conv4)
            _ = self.dropout_deepsup(_)
            _ = self.conv_last_deepsup(_)
            x = nn.functional.log_softmax(x, dim=1)
            _ = nn.functional.log_softmax(_, dim=1)
            return (x, _)

def __init__(self, num_class=NUM_CLASS, fc_dim=4096, use_softmax=False, pool_scales=(1, 2, 3, 6), drop_last_conv=False):
    super().__init__()
    self.use_softmax = use_softmax
    self.drop_last_conv = drop_last_conv
    self.ppm = []
    for scale in pool_scales:
        self.ppm.append(nn.Sequential(nn.AdaptiveAvgPool2d(scale), nn.Conv2d(fc_dim, 512, kernel_size=1, bias=False), BatchNorm2d(512), nn.ReLU(inplace=True)))
    self.ppm = nn.ModuleList(self.ppm)
    self.cbr_deepsup = conv3x3_bn_relu(fc_dim // 2, fc_dim // 4, 1)
    self.conv_last = nn.Sequential(nn.Conv2d(fc_dim + len(pool_scales) * 512, 512, kernel_size=3, padding=1, bias=False), BatchNorm2d(512), nn.ReLU(inplace=True), nn.Dropout2d(0.1), nn.Conv2d(512, num_class, kernel_size=1))
    self.conv_last_deepsup = nn.Conv2d(fc_dim // 4, num_class, 1, 1, 0)
    self.dropout_deepsup = nn.Dropout2d(0.1)

class Resnet(nn.Module):

    def __init__(self, orig_resnet):
        super(Resnet, self).__init__()
        self.conv1 = orig_resnet.conv1
        self.bn1 = orig_resnet.bn1
        self.relu1 = orig_resnet.relu1
        self.conv2 = orig_resnet.conv2
        self.bn2 = orig_resnet.bn2
        self.relu2 = orig_resnet.relu2
        self.conv3 = orig_resnet.conv3
        self.bn3 = orig_resnet.bn3
        self.relu3 = orig_resnet.relu3
        self.maxpool = orig_resnet.maxpool
        self.layer1 = orig_resnet.layer1
        self.layer2 = orig_resnet.layer2
        self.layer3 = orig_resnet.layer3
        self.layer4 = orig_resnet.layer4

    def forward(self, x, return_feature_maps=False):
        conv_out = []
        x = self.relu1(self.bn1(self.conv1(x)))
        x = self.relu2(self.bn2(self.conv2(x)))
        x = self.relu3(self.bn3(self.conv3(x)))
        x = self.maxpool(x)
        x = self.layer1(x)
        conv_out.append(x)
        x = self.layer2(x)
        conv_out.append(x)
        x = self.layer3(x)
        conv_out.append(x)
        x = self.layer4(x)
        conv_out.append(x)
        if return_feature_maps:
            return conv_out
        return [x]

def __init__(self, orig_resnet):
    super(Resnet, self).__init__()
    self.conv1 = orig_resnet.conv1
    self.bn1 = orig_resnet.bn1
    self.relu1 = orig_resnet.relu1
    self.conv2 = orig_resnet.conv2
    self.bn2 = orig_resnet.bn2
    self.relu2 = orig_resnet.relu2
    self.conv3 = orig_resnet.conv3
    self.bn3 = orig_resnet.bn3
    self.relu3 = orig_resnet.relu3
    self.maxpool = orig_resnet.maxpool
    self.layer1 = orig_resnet.layer1
    self.layer2 = orig_resnet.layer2
    self.layer3 = orig_resnet.layer3
    self.layer4 = orig_resnet.layer4

class ResnetDilated(nn.Module):

    def __init__(self, orig_resnet, dilate_scale=8):
        super().__init__()
        from functools import partial
        if dilate_scale == 8:
            orig_resnet.layer3.apply(partial(self._nostride_dilate, dilate=2))
            orig_resnet.layer4.apply(partial(self._nostride_dilate, dilate=4))
        elif dilate_scale == 16:
            orig_resnet.layer4.apply(partial(self._nostride_dilate, dilate=2))
        self.conv1 = orig_resnet.conv1
        self.bn1 = orig_resnet.bn1
        self.relu1 = orig_resnet.relu1
        self.conv2 = orig_resnet.conv2
        self.bn2 = orig_resnet.bn2
        self.relu2 = orig_resnet.relu2
        self.conv3 = orig_resnet.conv3
        self.bn3 = orig_resnet.bn3
        self.relu3 = orig_resnet.relu3
        self.maxpool = orig_resnet.maxpool
        self.layer1 = orig_resnet.layer1
        self.layer2 = orig_resnet.layer2
        self.layer3 = orig_resnet.layer3
        self.layer4 = orig_resnet.layer4

    def _nostride_dilate(self, m, dilate):
        classname = m.__class__.__name__
        if classname.find('Conv') != -1:
            if m.stride == (2, 2):
                m.stride = (1, 1)
                if m.kernel_size == (3, 3):
                    m.dilation = (dilate // 2, dilate // 2)
                    m.padding = (dilate // 2, dilate // 2)
            elif m.kernel_size == (3, 3):
                m.dilation = (dilate, dilate)
                m.padding = (dilate, dilate)

    def forward(self, x, return_feature_maps=False):
        conv_out = []
        x = self.relu1(self.bn1(self.conv1(x)))
        x = self.relu2(self.bn2(self.conv2(x)))
        x = self.relu3(self.bn3(self.conv3(x)))
        x = self.maxpool(x)
        x = self.layer1(x)
        conv_out.append(x)
        x = self.layer2(x)
        conv_out.append(x)
        x = self.layer3(x)
        conv_out.append(x)
        x = self.layer4(x)
        conv_out.append(x)
        if return_feature_maps:
            return conv_out
        return [x]

def __init__(self, orig_resnet, dilate_scale=8):
    super().__init__()
    from functools import partial
    if dilate_scale == 8:
        orig_resnet.layer3.apply(partial(self._nostride_dilate, dilate=2))
        orig_resnet.layer4.apply(partial(self._nostride_dilate, dilate=4))
    elif dilate_scale == 16:
        orig_resnet.layer4.apply(partial(self._nostride_dilate, dilate=2))
    self.conv1 = orig_resnet.conv1
    self.bn1 = orig_resnet.bn1
    self.relu1 = orig_resnet.relu1
    self.conv2 = orig_resnet.conv2
    self.bn2 = orig_resnet.bn2
    self.relu2 = orig_resnet.relu2
    self.conv3 = orig_resnet.conv3
    self.bn3 = orig_resnet.bn3
    self.relu3 = orig_resnet.relu3
    self.maxpool = orig_resnet.maxpool
    self.layer1 = orig_resnet.layer1
    self.layer2 = orig_resnet.layer2
    self.layer3 = orig_resnet.layer3
    self.layer4 = orig_resnet.layer4

class MobileNetV2Dilated(nn.Module):

    def __init__(self, orig_net, dilate_scale=8):
        super(MobileNetV2Dilated, self).__init__()
        from functools import partial
        self.features = orig_net.features[:-1]
        self.total_idx = len(self.features)
        self.down_idx = [2, 4, 7, 14]
        if dilate_scale == 8:
            for i in range(self.down_idx[-2], self.down_idx[-1]):
                self.features[i].apply(partial(self._nostride_dilate, dilate=2))
            for i in range(self.down_idx[-1], self.total_idx):
                self.features[i].apply(partial(self._nostride_dilate, dilate=4))
        elif dilate_scale == 16:
            for i in range(self.down_idx[-1], self.total_idx):
                self.features[i].apply(partial(self._nostride_dilate, dilate=2))

    def _nostride_dilate(self, m, dilate):
        classname = m.__class__.__name__
        if classname.find('Conv') != -1:
            if m.stride == (2, 2):
                m.stride = (1, 1)
                if m.kernel_size == (3, 3):
                    m.dilation = (dilate // 2, dilate // 2)
                    m.padding = (dilate // 2, dilate // 2)
            elif m.kernel_size == (3, 3):
                m.dilation = (dilate, dilate)
                m.padding = (dilate, dilate)

    def forward(self, x, return_feature_maps=False):
        if return_feature_maps:
            conv_out = []
            for i in range(self.total_idx):
                x = self.features[i](x)
                if i in self.down_idx:
                    conv_out.append(x)
            conv_out.append(x)
            return conv_out
        else:
            return [self.features(x)]

def __init__(self, orig_net, dilate_scale=8):
    super(MobileNetV2Dilated, self).__init__()
    from functools import partial
    self.features = orig_net.features[:-1]
    self.total_idx = len(self.features)
    self.down_idx = [2, 4, 7, 14]
    if dilate_scale == 8:
        for i in range(self.down_idx[-2], self.down_idx[-1]):
            self.features[i].apply(partial(self._nostride_dilate, dilate=2))
        for i in range(self.down_idx[-1], self.total_idx):
            self.features[i].apply(partial(self._nostride_dilate, dilate=4))
    elif dilate_scale == 16:
        for i in range(self.down_idx[-1], self.total_idx):
            self.features[i].apply(partial(self._nostride_dilate, dilate=2))

class C1DeepSup(nn.Module):

    def __init__(self, num_class=150, fc_dim=2048, use_softmax=False, drop_last_conv=False):
        super(C1DeepSup, self).__init__()
        self.use_softmax = use_softmax
        self.drop_last_conv = drop_last_conv
        self.cbr = conv3x3_bn_relu(fc_dim, fc_dim // 4, 1)
        self.cbr_deepsup = conv3x3_bn_relu(fc_dim // 2, fc_dim // 4, 1)
        self.conv_last = nn.Conv2d(fc_dim // 4, num_class, 1, 1, 0)
        self.conv_last_deepsup = nn.Conv2d(fc_dim // 4, num_class, 1, 1, 0)

    def forward(self, conv_out, segSize=None):
        conv5 = conv_out[-1]
        x = self.cbr(conv5)
        if self.drop_last_conv:
            return x
        else:
            x = self.conv_last(x)
            if self.use_softmax:
                x = nn.functional.interpolate(x, size=segSize, mode='bilinear', align_corners=False)
                x = nn.functional.softmax(x, dim=1)
                return x
            conv4 = conv_out[-2]
            _ = self.cbr_deepsup(conv4)
            _ = self.conv_last_deepsup(_)
            x = nn.functional.log_softmax(x, dim=1)
            _ = nn.functional.log_softmax(_, dim=1)
            return (x, _)

def __init__(self, num_class=150, fc_dim=2048, use_softmax=False, drop_last_conv=False):
    super(C1DeepSup, self).__init__()
    self.use_softmax = use_softmax
    self.drop_last_conv = drop_last_conv
    self.cbr = conv3x3_bn_relu(fc_dim, fc_dim // 4, 1)
    self.cbr_deepsup = conv3x3_bn_relu(fc_dim // 2, fc_dim // 4, 1)
    self.conv_last = nn.Conv2d(fc_dim // 4, num_class, 1, 1, 0)
    self.conv_last_deepsup = nn.Conv2d(fc_dim // 4, num_class, 1, 1, 0)

class C1(nn.Module):

    def __init__(self, num_class=150, fc_dim=2048, use_softmax=False):
        super(C1, self).__init__()
        self.use_softmax = use_softmax
        self.cbr = conv3x3_bn_relu(fc_dim, fc_dim // 4, 1)
        self.conv_last = nn.Conv2d(fc_dim // 4, num_class, 1, 1, 0)

    def forward(self, conv_out, segSize=None):
        conv5 = conv_out[-1]
        x = self.cbr(conv5)
        x = self.conv_last(x)
        if self.use_softmax:
            x = nn.functional.interpolate(x, size=segSize, mode='bilinear', align_corners=False)
            x = nn.functional.softmax(x, dim=1)
        else:
            x = nn.functional.log_softmax(x, dim=1)
        return x

def __init__(self, num_class=150, fc_dim=2048, use_softmax=False):
    super(C1, self).__init__()
    self.use_softmax = use_softmax
    self.cbr = conv3x3_bn_relu(fc_dim, fc_dim // 4, 1)
    self.conv_last = nn.Conv2d(fc_dim // 4, num_class, 1, 1, 0)

class PPM(nn.Module):

    def __init__(self, num_class=150, fc_dim=4096, use_softmax=False, pool_scales=(1, 2, 3, 6)):
        super(PPM, self).__init__()
        self.use_softmax = use_softmax
        self.ppm = []
        for scale in pool_scales:
            self.ppm.append(nn.Sequential(nn.AdaptiveAvgPool2d(scale), nn.Conv2d(fc_dim, 512, kernel_size=1, bias=False), BatchNorm2d(512), nn.ReLU(inplace=True)))
        self.ppm = nn.ModuleList(self.ppm)
        self.conv_last = nn.Sequential(nn.Conv2d(fc_dim + len(pool_scales) * 512, 512, kernel_size=3, padding=1, bias=False), BatchNorm2d(512), nn.ReLU(inplace=True), nn.Dropout2d(0.1), nn.Conv2d(512, num_class, kernel_size=1))

    def forward(self, conv_out, segSize=None):
        conv5 = conv_out[-1]
        input_size = conv5.size()
        ppm_out = [conv5]
        for pool_scale in self.ppm:
            ppm_out.append(nn.functional.interpolate(pool_scale(conv5), (input_size[2], input_size[3]), mode='bilinear', align_corners=False))
        ppm_out = torch.cat(ppm_out, 1)
        x = self.conv_last(ppm_out)
        if self.use_softmax:
            x = nn.functional.interpolate(x, size=segSize, mode='bilinear', align_corners=False)
            x = nn.functional.softmax(x, dim=1)
        else:
            x = nn.functional.log_softmax(x, dim=1)
        return x

def __init__(self, num_class=150, fc_dim=4096, use_softmax=False, pool_scales=(1, 2, 3, 6)):
    super(PPM, self).__init__()
    self.use_softmax = use_softmax
    self.ppm = []
    for scale in pool_scales:
        self.ppm.append(nn.Sequential(nn.AdaptiveAvgPool2d(scale), nn.Conv2d(fc_dim, 512, kernel_size=1, bias=False), BatchNorm2d(512), nn.ReLU(inplace=True)))
    self.ppm = nn.ModuleList(self.ppm)
    self.conv_last = nn.Sequential(nn.Conv2d(fc_dim + len(pool_scales) * 512, 512, kernel_size=3, padding=1, bias=False), BatchNorm2d(512), nn.ReLU(inplace=True), nn.Dropout2d(0.1), nn.Conv2d(512, num_class, kernel_size=1))

def conv3x3(in_planes, out_planes, stride=1):
    """3x3 convolution with padding"""
    return nn.Conv2d(in_planes, out_planes, kernel_size=3, stride=stride, padding=1, bias=False)

class BasicBlock(nn.Module):
    expansion = 1

    def __init__(self, inplanes, planes, stride=1, downsample=None):
        super(BasicBlock, self).__init__()
        self.conv1 = conv3x3(inplanes, planes, stride)
        self.bn1 = BatchNorm2d(planes)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = conv3x3(planes, planes)
        self.bn2 = BatchNorm2d(planes)
        self.downsample = downsample
        self.stride = stride

    def forward(self, x):
        residual = x
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)
        out = self.conv2(out)
        out = self.bn2(out)
        if self.downsample is not None:
            residual = self.downsample(x)
        out += residual
        out = self.relu(out)
        return out

def __init__(self, inplanes, planes, stride=1, downsample=None):
    super(BasicBlock, self).__init__()
    self.conv1 = conv3x3(inplanes, planes, stride)
    self.bn1 = BatchNorm2d(planes)
    self.relu = nn.ReLU(inplace=True)
    self.conv2 = conv3x3(planes, planes)
    self.bn2 = BatchNorm2d(planes)
    self.downsample = downsample
    self.stride = stride

class Bottleneck(nn.Module):
    expansion = 4

    def __init__(self, inplanes, planes, stride=1, downsample=None):
        super(Bottleneck, self).__init__()
        self.conv1 = nn.Conv2d(inplanes, planes, kernel_size=1, bias=False)
        self.bn1 = BatchNorm2d(planes)
        self.conv2 = nn.Conv2d(planes, planes, kernel_size=3, stride=stride, padding=1, bias=False)
        self.bn2 = BatchNorm2d(planes)
        self.conv3 = nn.Conv2d(planes, planes * 4, kernel_size=1, bias=False)
        self.bn3 = BatchNorm2d(planes * 4)
        self.relu = nn.ReLU(inplace=True)
        self.downsample = downsample
        self.stride = stride

    def forward(self, x):
        residual = x
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)
        out = self.conv2(out)
        out = self.bn2(out)
        out = self.relu(out)
        out = self.conv3(out)
        out = self.bn3(out)
        if self.downsample is not None:
            residual = self.downsample(x)
        out += residual
        out = self.relu(out)
        return out

def __init__(self, inplanes, planes, stride=1, downsample=None):
    super(Bottleneck, self).__init__()
    self.conv1 = nn.Conv2d(inplanes, planes, kernel_size=1, bias=False)
    self.bn1 = BatchNorm2d(planes)
    self.conv2 = nn.Conv2d(planes, planes, kernel_size=3, stride=stride, padding=1, bias=False)
    self.bn2 = BatchNorm2d(planes)
    self.conv3 = nn.Conv2d(planes, planes * 4, kernel_size=1, bias=False)
    self.bn3 = BatchNorm2d(planes * 4)
    self.relu = nn.ReLU(inplace=True)
    self.downsample = downsample
    self.stride = stride

class ResNet(nn.Module):

    def __init__(self, block, layers, num_classes=1000):
        self.inplanes = 128
        super(ResNet, self).__init__()
        self.conv1 = conv3x3(3, 64, stride=2)
        self.bn1 = BatchNorm2d(64)
        self.relu1 = nn.ReLU(inplace=True)
        self.conv2 = conv3x3(64, 64)
        self.bn2 = BatchNorm2d(64)
        self.relu2 = nn.ReLU(inplace=True)
        self.conv3 = conv3x3(64, 128)
        self.bn3 = BatchNorm2d(128)
        self.relu3 = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        self.layer1 = self._make_layer(block, 64, layers[0])
        self.layer2 = self._make_layer(block, 128, layers[1], stride=2)
        self.layer3 = self._make_layer(block, 256, layers[2], stride=2)
        self.layer4 = self._make_layer(block, 512, layers[3], stride=2)
        self.avgpool = nn.AvgPool2d(7, stride=1)
        self.fc = nn.Linear(512 * block.expansion, num_classes)
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                n = m.kernel_size[0] * m.kernel_size[1] * m.out_channels
                m.weight.data.normal_(0, math.sqrt(2.0 / n))
            elif isinstance(m, BatchNorm2d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()

    def _make_layer(self, block, planes, blocks, stride=1):
        downsample = None
        if stride != 1 or self.inplanes != planes * block.expansion:
            downsample = nn.Sequential(nn.Conv2d(self.inplanes, planes * block.expansion, kernel_size=1, stride=stride, bias=False), BatchNorm2d(planes * block.expansion))
        layers = []
        layers.append(block(self.inplanes, planes, stride, downsample))
        self.inplanes = planes * block.expansion
        for i in range(1, blocks):
            layers.append(block(self.inplanes, planes))
        return nn.Sequential(*layers)

    def forward(self, x):
        x = self.relu1(self.bn1(self.conv1(x)))
        x = self.relu2(self.bn2(self.conv2(x)))
        x = self.relu3(self.bn3(self.conv3(x)))
        x = self.maxpool(x)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)
        x = self.avgpool(x)
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        return x

def __init__(self, block, layers, num_classes=1000):
    self.inplanes = 128
    super(ResNet, self).__init__()
    self.conv1 = conv3x3(3, 64, stride=2)
    self.bn1 = BatchNorm2d(64)
    self.relu1 = nn.ReLU(inplace=True)
    self.conv2 = conv3x3(64, 64)
    self.bn2 = BatchNorm2d(64)
    self.relu2 = nn.ReLU(inplace=True)
    self.conv3 = conv3x3(64, 128)
    self.bn3 = BatchNorm2d(128)
    self.relu3 = nn.ReLU(inplace=True)
    self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
    self.layer1 = self._make_layer(block, 64, layers[0])
    self.layer2 = self._make_layer(block, 128, layers[1], stride=2)
    self.layer3 = self._make_layer(block, 256, layers[2], stride=2)
    self.layer4 = self._make_layer(block, 512, layers[3], stride=2)
    self.avgpool = nn.AvgPool2d(7, stride=1)
    self.fc = nn.Linear(512 * block.expansion, num_classes)
    for m in self.modules():
        if isinstance(m, nn.Conv2d):
            n = m.kernel_size[0] * m.kernel_size[1] * m.out_channels
            m.weight.data.normal_(0, math.sqrt(2.0 / n))
        elif isinstance(m, BatchNorm2d):
            m.weight.data.fill_(1)
            m.bias.data.zero_()

def _make_layer(self, block, planes, blocks, stride=1):
    downsample = None
    if stride != 1 or self.inplanes != planes * block.expansion:
        downsample = nn.Sequential(nn.Conv2d(self.inplanes, planes * block.expansion, kernel_size=1, stride=stride, bias=False), BatchNorm2d(planes * block.expansion))
    layers = []
    layers.append(block(self.inplanes, planes, stride, downsample))
    self.inplanes = planes * block.expansion
    for i in range(1, blocks):
        layers.append(block(self.inplanes, planes))
    return nn.Sequential(*layers)

class UserScatteredDataParallel(DictGatherDataParallel):

    def scatter(self, inputs, kwargs, device_ids):
        assert len(inputs) == 1
        inputs = inputs[0]
        inputs = _async_copy_stream(inputs, device_ids)
        inputs = [[i] for i in inputs]
        assert len(kwargs) == 0
        kwargs = [{} for _ in range(len(inputs))]
        return (inputs, kwargs)

def scatter(self, inputs, kwargs, device_ids):
    assert len(inputs) == 1
    inputs = inputs[0]
    inputs = _async_copy_stream(inputs, device_ids)
    inputs = [[i] for i in inputs]
    assert len(kwargs) == 0
    kwargs = [{} for _ in range(len(inputs))]
    return (inputs, kwargs)

class _SynchronizedBatchNorm(_BatchNorm):

    def __init__(self, num_features, eps=1e-05, momentum=0.001, affine=True):
        super(_SynchronizedBatchNorm, self).__init__(num_features, eps=eps, momentum=momentum, affine=affine)
        self._sync_master = SyncMaster(self._data_parallel_master)
        self._is_parallel = False
        self._parallel_id = None
        self._slave_pipe = None
        self._moving_average_fraction = 1.0 - momentum
        self.register_buffer('_tmp_running_mean', torch.zeros(self.num_features))
        self.register_buffer('_tmp_running_var', torch.ones(self.num_features))
        self.register_buffer('_running_iter', torch.ones(1))
        self._tmp_running_mean = self.running_mean.clone() * self._running_iter
        self._tmp_running_var = self.running_var.clone() * self._running_iter

    def forward(self, input):
        if not (self._is_parallel and self.training):
            return F.batch_norm(input, self.running_mean, self.running_var, self.weight, self.bias, self.training, self.momentum, self.eps)
        input_shape = input.size()
        input = input.view(input.size(0), self.num_features, -1)
        sum_size = input.size(0) * input.size(2)
        input_sum = _sum_ft(input)
        input_ssum = _sum_ft(input ** 2)
        if self._parallel_id == 0:
            mean, inv_std = self._sync_master.run_master(_ChildMessage(input_sum, input_ssum, sum_size))
        else:
            mean, inv_std = self._slave_pipe.run_slave(_ChildMessage(input_sum, input_ssum, sum_size))
        if self.affine:
            output = (input - _unsqueeze_ft(mean)) * _unsqueeze_ft(inv_std * self.weight) + _unsqueeze_ft(self.bias)
        else:
            output = (input - _unsqueeze_ft(mean)) * _unsqueeze_ft(inv_std)
        return output.view(input_shape)

    def __data_parallel_replicate__(self, ctx, copy_id):
        self._is_parallel = True
        self._parallel_id = copy_id
        if self._parallel_id == 0:
            ctx.sync_master = self._sync_master
        else:
            self._slave_pipe = ctx.sync_master.register_slave(copy_id)

    def _data_parallel_master(self, intermediates):
        """Reduce the sum and square-sum, compute the statistics, and broadcast it."""
        intermediates = sorted(intermediates, key=lambda i: i[1].sum.get_device())
        to_reduce = [i[1][:2] for i in intermediates]
        to_reduce = [j for i in to_reduce for j in i]
        target_gpus = [i[1].sum.get_device() for i in intermediates]
        sum_size = sum([i[1].sum_size for i in intermediates])
        sum_, ssum = ReduceAddCoalesced.apply(target_gpus[0], 2, *to_reduce)
        mean, inv_std = self._compute_mean_std(sum_, ssum, sum_size)
        broadcasted = Broadcast.apply(target_gpus, mean, inv_std)
        outputs = []
        for i, rec in enumerate(intermediates):
            outputs.append((rec[0], _MasterMessage(*broadcasted[i * 2:i * 2 + 2])))
        return outputs

    def _add_weighted(self, dest, delta, alpha=1, beta=1, bias=0):
        """return *dest* by `dest := dest*alpha + delta*beta + bias`"""
        return dest * alpha + delta * beta + bias

    def _compute_mean_std(self, sum_, ssum, size):
        """Compute the mean and standard-deviation with sum and square-sum. This method
        also maintains the moving average on the master device."""
        assert size > 1, 'BatchNorm computes unbiased standard-deviation, which requires size > 1.'
        mean = sum_ / size
        sumvar = ssum - sum_ * mean
        unbias_var = sumvar / (size - 1)
        bias_var = sumvar / size
        self._tmp_running_mean = self._add_weighted(self._tmp_running_mean, mean.data, alpha=self._moving_average_fraction)
        self._tmp_running_var = self._add_weighted(self._tmp_running_var, unbias_var.data, alpha=self._moving_average_fraction)
        self._running_iter = self._add_weighted(self._running_iter, 1, alpha=self._moving_average_fraction)
        self.running_mean = self._tmp_running_mean / self._running_iter
        self.running_var = self._tmp_running_var / self._running_iter
        return (mean, bias_var.clamp(self.eps) ** (-0.5))

def __init__(self, num_features, eps=1e-05, momentum=0.001, affine=True):
    super(_SynchronizedBatchNorm, self).__init__(num_features, eps=eps, momentum=momentum, affine=affine)
    self._sync_master = SyncMaster(self._data_parallel_master)
    self._is_parallel = False
    self._parallel_id = None
    self._slave_pipe = None
    self._moving_average_fraction = 1.0 - momentum
    self.register_buffer('_tmp_running_mean', torch.zeros(self.num_features))
    self.register_buffer('_tmp_running_var', torch.ones(self.num_features))
    self.register_buffer('_running_iter', torch.ones(1))
    self._tmp_running_mean = self.running_mean.clone() * self._running_iter
    self._tmp_running_var = self.running_var.clone() * self._running_iter

class FocalLoss(nn.Module, ABC):

    def __init__(self, alpha=2, beta=4):
        super(FocalLoss, self).__init__()
        self.alpha = alpha
        self.beta = beta

    def forward(self, prediction, target):
        positive_index = target.eq(1).float()
        negative_index = target.lt(1).float()
        negative_weights = torch.pow(1 - target, self.beta)
        prediction = torch.clamp(prediction, 1e-12)
        positive_loss = torch.log(prediction) * torch.pow(1 - prediction, self.alpha) * positive_index
        negative_loss = torch.log(1 - prediction) * torch.pow(prediction, self.alpha) * negative_weights * negative_index
        num_positive = positive_index.float().sum()
        positive_loss = positive_loss.sum()
        negative_loss = negative_loss.sum()
        if num_positive == 0:
            loss = -negative_loss
        else:
            loss = -(positive_loss + negative_loss) / num_positive
        return loss

def __init__(self, alpha=2, beta=4):
    super(FocalLoss, self).__init__()
    self.alpha = alpha
    self.beta = beta

class LBHinge(nn.Module):
    """Loss that uses a 'hinge' on the lower bound.
    This means that for samples with a label value smaller than the threshold, the loss is zero if the prediction is
    also smaller than that threshold.
    args:
        error_matric:  What base loss to use (MSE by default).
        threshold:  Threshold to use for the hinge.
        clip:  Clip the loss if it is above this value.
    """

    def __init__(self, error_metric=nn.MSELoss(), threshold=None, clip=None):
        super().__init__()
        self.error_metric = error_metric
        self.threshold = threshold if threshold is not None else -100
        self.clip = clip

    def forward(self, prediction, label, target_bb=None):
        negative_mask = (label < self.threshold).float()
        positive_mask = 1.0 - negative_mask
        prediction = negative_mask * F.relu(prediction) + positive_mask * prediction
        loss = self.error_metric(prediction, positive_mask * label)
        if self.clip is not None:
            loss = torch.min(loss, torch.tensor([self.clip], device=loss.device))
        return loss

def __init__(self, error_metric=nn.MSELoss(), threshold=None, clip=None):
    super().__init__()
    self.error_metric = error_metric
    self.threshold = threshold if threshold is not None else -100
    self.clip = clip

class TensorList(list):
    """Container mainly used for lists of torch tensors. Extends lists with pytorch functionality."""

    def __init__(self, list_of_tensors=None):
        if list_of_tensors is None:
            list_of_tensors = list()
        super(TensorList, self).__init__(list_of_tensors)

    def __deepcopy__(self, memodict={}):
        return TensorList(copy.deepcopy(list(self), memodict))

    def __getitem__(self, item):
        if isinstance(item, int):
            return super(TensorList, self).__getitem__(item)
        elif isinstance(item, (tuple, list)):
            return TensorList([super(TensorList, self).__getitem__(i) for i in item])
        else:
            return TensorList(super(TensorList, self).__getitem__(item))

    def __add__(self, other):
        if TensorList._iterable(other):
            return TensorList([e1 + e2 for e1, e2 in zip(self, other)])
        return TensorList([e + other for e in self])

    def __radd__(self, other):
        if TensorList._iterable(other):
            return TensorList([e2 + e1 for e1, e2 in zip(self, other)])
        return TensorList([other + e for e in self])

    def __iadd__(self, other):
        if TensorList._iterable(other):
            for i, e2 in enumerate(other):
                self[i] += e2
        else:
            for i in range(len(self)):
                self[i] += other
        return self

    def __sub__(self, other):
        if TensorList._iterable(other):
            return TensorList([e1 - e2 for e1, e2 in zip(self, other)])
        return TensorList([e - other for e in self])

    def __rsub__(self, other):
        if TensorList._iterable(other):
            return TensorList([e2 - e1 for e1, e2 in zip(self, other)])
        return TensorList([other - e for e in self])

    def __isub__(self, other):
        if TensorList._iterable(other):
            for i, e2 in enumerate(other):
                self[i] -= e2
        else:
            for i in range(len(self)):
                self[i] -= other
        return self

    def __mul__(self, other):
        if TensorList._iterable(other):
            return TensorList([e1 * e2 for e1, e2 in zip(self, other)])
        return TensorList([e * other for e in self])

    def __rmul__(self, other):
        if TensorList._iterable(other):
            return TensorList([e2 * e1 for e1, e2 in zip(self, other)])
        return TensorList([other * e for e in self])

    def __imul__(self, other):
        if TensorList._iterable(other):
            for i, e2 in enumerate(other):
                self[i] *= e2
        else:
            for i in range(len(self)):
                self[i] *= other
        return self

    def __truediv__(self, other):
        if TensorList._iterable(other):
            return TensorList([e1 / e2 for e1, e2 in zip(self, other)])
        return TensorList([e / other for e in self])

    def __rtruediv__(self, other):
        if TensorList._iterable(other):
            return TensorList([e2 / e1 for e1, e2 in zip(self, other)])
        return TensorList([other / e for e in self])

    def __itruediv__(self, other):
        if TensorList._iterable(other):
            for i, e2 in enumerate(other):
                self[i] /= e2
        else:
            for i in range(len(self)):
                self[i] /= other
        return self

    def __matmul__(self, other):
        if TensorList._iterable(other):
            return TensorList([e1 @ e2 for e1, e2 in zip(self, other)])
        return TensorList([e @ other for e in self])

    def __rmatmul__(self, other):
        if TensorList._iterable(other):
            return TensorList([e2 @ e1 for e1, e2 in zip(self, other)])
        return TensorList([other @ e for e in self])

    def __imatmul__(self, other):
        if TensorList._iterable(other):
            for i, e2 in enumerate(other):
                self[i] @= e2
        else:
            for i in range(len(self)):
                self[i] @= other
        return self

    def __mod__(self, other):
        if TensorList._iterable(other):
            return TensorList([e1 % e2 for e1, e2 in zip(self, other)])
        return TensorList([e % other for e in self])

    def __rmod__(self, other):
        if TensorList._iterable(other):
            return TensorList([e2 % e1 for e1, e2 in zip(self, other)])
        return TensorList([other % e for e in self])

    def __pos__(self):
        return TensorList([+e for e in self])

    def __neg__(self):
        return TensorList([-e for e in self])

    def __le__(self, other):
        if TensorList._iterable(other):
            return TensorList([e1 <= e2 for e1, e2 in zip(self, other)])
        return TensorList([e <= other for e in self])

    def __ge__(self, other):
        if TensorList._iterable(other):
            return TensorList([e1 >= e2 for e1, e2 in zip(self, other)])
        return TensorList([e >= other for e in self])

    def concat(self, other):
        return TensorList(super(TensorList, self).__add__(other))

    def copy(self):
        return TensorList(super(TensorList, self).copy())

    def unroll(self):
        if not any((isinstance(t, TensorList) for t in self)):
            return self
        new_list = TensorList()
        for t in self:
            if isinstance(t, TensorList):
                new_list.extend(t.unroll())
            else:
                new_list.append(t)
        return new_list

    def list(self):
        return list(self)

    def attribute(self, attr: str, *args):
        return TensorList([getattr(e, attr, *args) for e in self])

    def apply(self, fn):
        return TensorList([fn(e) for e in self])

    def __getattr__(self, name):
        if not hasattr(torch.Tensor, name):
            raise AttributeError("'TensorList' object has not attribute '{}'".format(name))

        def apply_attr(*args, **kwargs):
            return TensorList([getattr(e, name)(*args, **kwargs) for e in self])
        return apply_attr

    @staticmethod
    def _iterable(a):
        return isinstance(a, (TensorList, list))

def __init__(self, list_of_tensors=None):
    if list_of_tensors is None:
        list_of_tensors = list()
    super(TensorList, self).__init__(list_of_tensors)

def concat(self, other):
    return TensorList(super(TensorList, self).__add__(other))

def is_dist_avail_and_initialized():
    if not dist.is_available():
        return False
    if not dist.is_initialized():
        return False
    return True

def pad_img(img):
    height, width, channels = img.shape
    im_bg = np.ones((height, width + 8, channels)) * 255
    im_bg[0:height, 0:width, :] = img
    return im_bg

class SequenceList(list):
    """List of sequences. Supports the addition operator to concatenate sequence lists."""

    def __getitem__(self, item):
        if isinstance(item, str):
            for seq in self:
                if seq.name == item:
                    return seq
            raise IndexError('Sequence name not in the dataset.')
        elif isinstance(item, int):
            return super(SequenceList, self).__getitem__(item)
        elif isinstance(item, (tuple, list)):
            return SequenceList([super(SequenceList, self).__getitem__(i) for i in item])
        else:
            return SequenceList(super(SequenceList, self).__getitem__(item))

    def __add__(self, other):
        return SequenceList(super(SequenceList, self).__add__(other))

    def copy(self):
        return SequenceList(super(SequenceList, self).copy())

def __getitem__(self, item):
    if isinstance(item, str):
        for seq in self:
            if seq.name == item:
                return seq
        raise IndexError('Sequence name not in the dataset.')
    elif isinstance(item, int):
        return super(SequenceList, self).__getitem__(item)
    elif isinstance(item, (tuple, list)):
        return SequenceList([super(SequenceList, self).__getitem__(i) for i in item])
    else:
        return SequenceList(super(SequenceList, self).__getitem__(item))

def __add__(self, other):
    return SequenceList(super(SequenceList, self).__add__(other))

def copy(self):
    return SequenceList(super(SequenceList, self).copy())

class Attention(nn.Module):

    def __init__(self, dim, num_heads=8, qkv_bias=False, attn_drop=0.0, proj_drop=0.0):
        super().__init__()
        self.num_heads = num_heads
        head_dim = dim // num_heads
        self.scale = head_dim ** (-0.5)
        self.qkv = nn.Linear(dim, dim * 3, bias=qkv_bias)
        self.attn_drop = nn.Dropout(attn_drop)
        self.proj = nn.Linear(dim, dim)
        self.proj_drop = nn.Dropout(proj_drop)

    def forward(self, x, return_attention=False):
        B, N, C = x.shape
        qkv = self.qkv(x).reshape(B, N, 3, self.num_heads, C // self.num_heads).permute(2, 0, 3, 1, 4)
        q, k, v = (qkv[0], qkv[1], qkv[2])
        attn = q @ k.transpose(-2, -1) * self.scale
        attn = attn.softmax(dim=-1)
        attn = self.attn_drop(attn)
        x = (attn @ v).transpose(1, 2).reshape(B, N, C)
        x = self.proj(x)
        x = self.proj_drop(x)
        if return_attention:
            return (x, attn)
        return x

def __init__(self, dim, num_heads=8, qkv_bias=False, attn_drop=0.0, proj_drop=0.0):
    super().__init__()
    self.num_heads = num_heads
    head_dim = dim // num_heads
    self.scale = head_dim ** (-0.5)
    self.qkv = nn.Linear(dim, dim * 3, bias=qkv_bias)
    self.attn_drop = nn.Dropout(attn_drop)
    self.proj = nn.Linear(dim, dim)
    self.proj_drop = nn.Dropout(proj_drop)

class Block(nn.Module):

    def __init__(self, dim, num_heads, mlp_ratio=4.0, qkv_bias=False, drop=0.0, attn_drop=0.0, drop_path=0.0, act_layer=nn.GELU, norm_layer=nn.LayerNorm):
        super().__init__()
        self.norm1 = norm_layer(dim)
        self.attn = Attention(dim, num_heads=num_heads, qkv_bias=qkv_bias, attn_drop=attn_drop, proj_drop=drop)
        self.drop_path = DropPath(drop_path) if drop_path > 0.0 else nn.Identity()
        self.norm2 = norm_layer(dim)
        mlp_hidden_dim = int(dim * mlp_ratio)
        self.mlp = Mlp(in_features=dim, hidden_features=mlp_hidden_dim, act_layer=act_layer, drop=drop)

    def forward(self, x, return_attention=False):
        if return_attention:
            feat, attn = self.attn(self.norm1(x), True)
            x = x + self.drop_path(feat)
            x = x + self.drop_path(self.mlp(self.norm2(x)))
            return (x, attn)
        else:
            x = x + self.drop_path(self.attn(self.norm1(x)))
            x = x + self.drop_path(self.mlp(self.norm2(x)))
            return x

def __init__(self, dim, num_heads, mlp_ratio=4.0, qkv_bias=False, drop=0.0, attn_drop=0.0, drop_path=0.0, act_layer=nn.GELU, norm_layer=nn.LayerNorm):
    super().__init__()
    self.norm1 = norm_layer(dim)
    self.attn = Attention(dim, num_heads=num_heads, qkv_bias=qkv_bias, attn_drop=attn_drop, proj_drop=drop)
    self.drop_path = DropPath(drop_path) if drop_path > 0.0 else nn.Identity()
    self.norm2 = norm_layer(dim)
    mlp_hidden_dim = int(dim * mlp_ratio)
    self.mlp = Mlp(in_features=dim, hidden_features=mlp_hidden_dim, act_layer=act_layer, drop=drop)

class VisionTransformer(BaseBackbone):
    """ Vision Transformer
    A PyTorch impl of : `An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale`
        - https://arxiv.org/abs/2010.11929
    Includes distillation token & head support for `DeiT: Data-efficient Image Transformers`
        - https://arxiv.org/abs/2012.12877
    """

    def __init__(self, img_size=224, patch_size=16, in_chans=3, num_classes=1000, embed_dim=768, depth=12, num_heads=12, mlp_ratio=4.0, qkv_bias=True, representation_size=None, distilled=False, drop_rate=0.0, attn_drop_rate=0.0, drop_path_rate=0.0, embed_layer=PatchEmbed, norm_layer=None, act_layer=None, weight_init=''):
        """
        Args:
            img_size (int, tuple): input image size
            patch_size (int, tuple): patch size
            in_chans (int): number of input channels
            num_classes (int): number of classes for classification head
            embed_dim (int): embedding dimension
            depth (int): depth of transformer
            num_heads (int): number of attention heads
            mlp_ratio (int): ratio of mlp hidden dim to embedding dim
            qkv_bias (bool): enable bias for qkv if True
            representation_size (Optional[int]): enable and set representation layer (pre-logits) to this value if set
            distilled (bool): model includes a distillation token and head as in DeiT models
            drop_rate (float): dropout rate
            attn_drop_rate (float): attention dropout rate
            drop_path_rate (float): stochastic depth rate
            embed_layer (nn.Module): patch embedding layer
            norm_layer: (nn.Module): normalization layer
            weight_init: (str): weight init scheme
        """
        super().__init__()
        self.num_classes = num_classes
        self.num_features = self.embed_dim = embed_dim
        self.num_tokens = 2 if distilled else 1
        norm_layer = norm_layer or partial(nn.LayerNorm, eps=1e-06)
        act_layer = act_layer or nn.GELU
        self.patch_embed = embed_layer(img_size=img_size, patch_size=patch_size, in_chans=in_chans, embed_dim=embed_dim)
        num_patches = self.patch_embed.num_patches
        self.cls_token = nn.Parameter(torch.zeros(1, 1, embed_dim))
        self.dist_token = nn.Parameter(torch.zeros(1, 1, embed_dim)) if distilled else None
        self.pos_embed = nn.Parameter(torch.zeros(1, num_patches + self.num_tokens, embed_dim))
        self.pos_drop = nn.Dropout(p=drop_rate)
        dpr = [x.item() for x in torch.linspace(0, drop_path_rate, depth)]
        self.blocks = nn.Sequential(*[Block(dim=embed_dim, num_heads=num_heads, mlp_ratio=mlp_ratio, qkv_bias=qkv_bias, drop=drop_rate, attn_drop=attn_drop_rate, drop_path=dpr[i], norm_layer=norm_layer, act_layer=act_layer) for i in range(depth)])
        self.norm = norm_layer(embed_dim)
        self.init_weights(weight_init)

    def init_weights(self, mode=''):
        assert mode in ('jax', 'jax_nlhb', 'nlhb', '')
        head_bias = -math.log(self.num_classes) if 'nlhb' in mode else 0.0
        trunc_normal_(self.pos_embed, std=0.02)
        if self.dist_token is not None:
            trunc_normal_(self.dist_token, std=0.02)
        if mode.startswith('jax'):
            named_apply(partial(_init_vit_weights, head_bias=head_bias, jax_impl=True), self)
        else:
            trunc_normal_(self.cls_token, std=0.02)
            self.apply(_init_vit_weights)

    def _init_weights(self, m):
        _init_vit_weights(m)

    @torch.jit.ignore()
    def load_pretrained(self, checkpoint_path, prefix=''):
        _load_weights(self, checkpoint_path, prefix)

    @torch.jit.ignore
    def no_weight_decay(self):
        return {'pos_embed', 'cls_token', 'dist_token'}

    def get_classifier(self):
        if self.dist_token is None:
            return self.head
        else:
            return (self.head, self.head_dist)

    def reset_classifier(self, num_classes, global_pool=''):
        self.num_classes = num_classes
        self.head = nn.Linear(self.embed_dim, num_classes) if num_classes > 0 else nn.Identity()
        if self.num_tokens == 2:
            self.head_dist = nn.Linear(self.embed_dim, self.num_classes) if num_classes > 0 else nn.Identity()

def __init__(self, img_size=224, patch_size=16, in_chans=3, num_classes=1000, embed_dim=768, depth=12, num_heads=12, mlp_ratio=4.0, qkv_bias=True, representation_size=None, distilled=False, drop_rate=0.0, attn_drop_rate=0.0, drop_path_rate=0.0, embed_layer=PatchEmbed, norm_layer=None, act_layer=None, weight_init=''):
    """
        Args:
            img_size (int, tuple): input image size
            patch_size (int, tuple): patch size
            in_chans (int): number of input channels
            num_classes (int): number of classes for classification head
            embed_dim (int): embedding dimension
            depth (int): depth of transformer
            num_heads (int): number of attention heads
            mlp_ratio (int): ratio of mlp hidden dim to embedding dim
            qkv_bias (bool): enable bias for qkv if True
            representation_size (Optional[int]): enable and set representation layer (pre-logits) to this value if set
            distilled (bool): model includes a distillation token and head as in DeiT models
            drop_rate (float): dropout rate
            attn_drop_rate (float): attention dropout rate
            drop_path_rate (float): stochastic depth rate
            embed_layer (nn.Module): patch embedding layer
            norm_layer: (nn.Module): normalization layer
            weight_init: (str): weight init scheme
        """
    super().__init__()
    self.num_classes = num_classes
    self.num_features = self.embed_dim = embed_dim
    self.num_tokens = 2 if distilled else 1
    norm_layer = norm_layer or partial(nn.LayerNorm, eps=1e-06)
    act_layer = act_layer or nn.GELU
    self.patch_embed = embed_layer(img_size=img_size, patch_size=patch_size, in_chans=in_chans, embed_dim=embed_dim)
    num_patches = self.patch_embed.num_patches
    self.cls_token = nn.Parameter(torch.zeros(1, 1, embed_dim))
    self.dist_token = nn.Parameter(torch.zeros(1, 1, embed_dim)) if distilled else None
    self.pos_embed = nn.Parameter(torch.zeros(1, num_patches + self.num_tokens, embed_dim))
    self.pos_drop = nn.Dropout(p=drop_rate)
    dpr = [x.item() for x in torch.linspace(0, drop_path_rate, depth)]
    self.blocks = nn.Sequential(*[Block(dim=embed_dim, num_heads=num_heads, mlp_ratio=mlp_ratio, qkv_bias=qkv_bias, drop=drop_rate, attn_drop=attn_drop_rate, drop_path=dpr[i], norm_layer=norm_layer, act_layer=act_layer) for i in range(depth)])
    self.norm = norm_layer(embed_dim)
    self.init_weights(weight_init)

def reset_classifier(self, num_classes, global_pool=''):
    self.num_classes = num_classes
    self.head = nn.Linear(self.embed_dim, num_classes) if num_classes > 0 else nn.Identity()
    if self.num_tokens == 2:
        self.head_dist = nn.Linear(self.embed_dim, self.num_classes) if num_classes > 0 else nn.Identity()

class VisionTransformerCE(VisionTransformer):
    """ Vision Transformer with candidate elimination (CE) module

    A PyTorch impl of : `An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale`
        - https://arxiv.org/abs/2010.11929

    Includes distillation token & head support for `DeiT: Data-efficient Image Transformers`
        - https://arxiv.org/abs/2012.12877
    """

    def __init__(self, img_size=224, patch_size=16, in_chans=3, num_classes=1000, embed_dim=768, depth=12, num_heads=12, mlp_ratio=4.0, qkv_bias=True, representation_size=None, distilled=False, drop_rate=0.0, attn_drop_rate=0.0, drop_path_rate=0.0, embed_layer=PatchEmbed, norm_layer=None, act_layer=None, weight_init='', ce_loc=None, ce_keep_ratio=None):
        """
        Args:
            img_size (int, tuple): input image size
            patch_size (int, tuple): patch size
            in_chans (int): number of input channels
            num_classes (int): number of classes for classification head
            embed_dim (int): embedding dimension
            depth (int): depth of transformer
            num_heads (int): number of attention heads
            mlp_ratio (int): ratio of mlp hidden dim to embedding dim
            qkv_bias (bool): enable bias for qkv if True
            representation_size (Optional[int]): enable and set representation layer (pre-logits) to this value if set
            distilled (bool): model includes a distillation token and head as in DeiT models
            drop_rate (float): dropout rate
            attn_drop_rate (float): attention dropout rate
            drop_path_rate (float): stochastic depth rate
            embed_layer (nn.Module): patch embedding layer
            norm_layer: (nn.Module): normalization layer
            weight_init: (str): weight init scheme
        """
        super().__init__()
        if isinstance(img_size, tuple):
            self.img_size = img_size
        else:
            self.img_size = to_2tuple(img_size)
        self.patch_size = patch_size
        self.in_chans = in_chans
        self.num_classes = num_classes
        self.num_features = self.embed_dim = embed_dim
        self.num_tokens = 2 if distilled else 1
        norm_layer = norm_layer or partial(nn.LayerNorm, eps=1e-06)
        act_layer = act_layer or nn.GELU
        self.patch_embed = embed_layer(img_size=img_size, patch_size=patch_size, in_chans=in_chans, embed_dim=embed_dim)
        num_patches = self.patch_embed.num_patches
        self.cls_token = nn.Parameter(torch.zeros(1, 1, embed_dim))
        self.dist_token = nn.Parameter(torch.zeros(1, 1, embed_dim)) if distilled else None
        self.pos_embed = nn.Parameter(torch.zeros(1, num_patches + self.num_tokens, embed_dim))
        self.pos_drop = nn.Dropout(p=drop_rate)
        dpr = [x.item() for x in torch.linspace(0, drop_path_rate, depth)]
        blocks = []
        ce_index = 0
        self.ce_loc = ce_loc
        for i in range(depth):
            ce_keep_ratio_i = 1.0
            if ce_loc is not None and i in ce_loc:
                ce_keep_ratio_i = ce_keep_ratio[ce_index]
                ce_index += 1
            blocks.append(CEBlock(dim=embed_dim, num_heads=num_heads, mlp_ratio=mlp_ratio, qkv_bias=qkv_bias, drop=drop_rate, attn_drop=attn_drop_rate, drop_path=dpr[i], norm_layer=norm_layer, act_layer=act_layer, keep_ratio_search=ce_keep_ratio_i))
        self.blocks = nn.Sequential(*blocks)
        self.norm = norm_layer(embed_dim)
        self.init_weights(weight_init)

    def forward_features(self, z, x, mask_z=None, mask_x=None, ce_template_mask=None, ce_keep_rate=None, return_last_attn=False):
        B, H, W = (x.shape[0], x.shape[2], x.shape[3])
        x = self.patch_embed(x)
        z = self.patch_embed(z)
        if mask_z is not None and mask_x is not None:
            mask_z = F.interpolate(mask_z[None].float(), scale_factor=1.0 / self.patch_size).to(torch.bool)[0]
            mask_z = mask_z.flatten(1).unsqueeze(-1)
            mask_x = F.interpolate(mask_x[None].float(), scale_factor=1.0 / self.patch_size).to(torch.bool)[0]
            mask_x = mask_x.flatten(1).unsqueeze(-1)
            mask_x = combine_tokens(mask_z, mask_x, mode=self.cat_mode)
            mask_x = mask_x.squeeze(-1)
        if self.add_cls_token:
            cls_tokens = self.cls_token.expand(B, -1, -1)
            cls_tokens = cls_tokens + self.cls_pos_embed
        z += self.pos_embed_z
        x += self.pos_embed_x
        if self.add_sep_seg:
            x += self.search_segment_pos_embed
            z += self.template_segment_pos_embed
        x = combine_tokens(z, x, mode=self.cat_mode)
        if self.add_cls_token:
            x = torch.cat([cls_tokens, x], dim=1)
        x = self.pos_drop(x)
        lens_z = self.pos_embed_z.shape[1]
        lens_x = self.pos_embed_x.shape[1]
        global_index_t = torch.linspace(0, lens_z - 1, lens_z).to(x.device)
        global_index_t = global_index_t.repeat(B, 1)
        global_index_s = torch.linspace(0, lens_x - 1, lens_x).to(x.device)
        global_index_s = global_index_s.repeat(B, 1)
        removed_indexes_s = []
        for i, blk in enumerate(self.blocks):
            x, global_index_t, global_index_s, removed_index_s, attn = blk(x, global_index_t, global_index_s, mask_x, ce_template_mask, ce_keep_rate)
            if self.ce_loc is not None and i in self.ce_loc:
                removed_indexes_s.append(removed_index_s)
        x = self.norm(x)
        lens_x_new = global_index_s.shape[1]
        lens_z_new = global_index_t.shape[1]
        z = x[:, :lens_z_new]
        x = x[:, lens_z_new:]
        if removed_indexes_s and removed_indexes_s[0] is not None:
            removed_indexes_cat = torch.cat(removed_indexes_s, dim=1)
            pruned_lens_x = lens_x - lens_x_new
            pad_x = torch.zeros([B, pruned_lens_x, x.shape[2]], device=x.device)
            x = torch.cat([x, pad_x], dim=1)
            index_all = torch.cat([global_index_s, removed_indexes_cat], dim=1)
            C = x.shape[-1]
            x = torch.zeros_like(x).scatter_(dim=1, index=index_all.unsqueeze(-1).expand(B, -1, C).to(torch.int64), src=x)
        x = recover_tokens(x, lens_z_new, lens_x, mode=self.cat_mode)
        x = torch.cat([z, x], dim=1)
        aux_dict = {'attn': attn, 'removed_indexes_s': removed_indexes_s}
        return (x, aux_dict)

    def forward(self, z, x, ce_template_mask=None, ce_keep_rate=None, tnc_keep_rate=None, return_last_attn=False):
        x, aux_dict = self.forward_features(z, x, ce_template_mask=ce_template_mask, ce_keep_rate=ce_keep_rate)
        return (x, aux_dict)

def __init__(self, img_size=224, patch_size=16, in_chans=3, num_classes=1000, embed_dim=768, depth=12, num_heads=12, mlp_ratio=4.0, qkv_bias=True, representation_size=None, distilled=False, drop_rate=0.0, attn_drop_rate=0.0, drop_path_rate=0.0, embed_layer=PatchEmbed, norm_layer=None, act_layer=None, weight_init='', ce_loc=None, ce_keep_ratio=None):
    """
        Args:
            img_size (int, tuple): input image size
            patch_size (int, tuple): patch size
            in_chans (int): number of input channels
            num_classes (int): number of classes for classification head
            embed_dim (int): embedding dimension
            depth (int): depth of transformer
            num_heads (int): number of attention heads
            mlp_ratio (int): ratio of mlp hidden dim to embedding dim
            qkv_bias (bool): enable bias for qkv if True
            representation_size (Optional[int]): enable and set representation layer (pre-logits) to this value if set
            distilled (bool): model includes a distillation token and head as in DeiT models
            drop_rate (float): dropout rate
            attn_drop_rate (float): attention dropout rate
            drop_path_rate (float): stochastic depth rate
            embed_layer (nn.Module): patch embedding layer
            norm_layer: (nn.Module): normalization layer
            weight_init: (str): weight init scheme
        """
    super().__init__()
    if isinstance(img_size, tuple):
        self.img_size = img_size
    else:
        self.img_size = to_2tuple(img_size)
    self.patch_size = patch_size
    self.in_chans = in_chans
    self.num_classes = num_classes
    self.num_features = self.embed_dim = embed_dim
    self.num_tokens = 2 if distilled else 1
    norm_layer = norm_layer or partial(nn.LayerNorm, eps=1e-06)
    act_layer = act_layer or nn.GELU
    self.patch_embed = embed_layer(img_size=img_size, patch_size=patch_size, in_chans=in_chans, embed_dim=embed_dim)
    num_patches = self.patch_embed.num_patches
    self.cls_token = nn.Parameter(torch.zeros(1, 1, embed_dim))
    self.dist_token = nn.Parameter(torch.zeros(1, 1, embed_dim)) if distilled else None
    self.pos_embed = nn.Parameter(torch.zeros(1, num_patches + self.num_tokens, embed_dim))
    self.pos_drop = nn.Dropout(p=drop_rate)
    dpr = [x.item() for x in torch.linspace(0, drop_path_rate, depth)]
    blocks = []
    ce_index = 0
    self.ce_loc = ce_loc
    for i in range(depth):
        ce_keep_ratio_i = 1.0
        if ce_loc is not None and i in ce_loc:
            ce_keep_ratio_i = ce_keep_ratio[ce_index]
            ce_index += 1
        blocks.append(CEBlock(dim=embed_dim, num_heads=num_heads, mlp_ratio=mlp_ratio, qkv_bias=qkv_bias, drop=drop_rate, attn_drop=attn_drop_rate, drop_path=dpr[i], norm_layer=norm_layer, act_layer=act_layer, keep_ratio_search=ce_keep_ratio_i))
    self.blocks = nn.Sequential(*blocks)
    self.norm = norm_layer(embed_dim)
    self.init_weights(weight_init)

class BaseBackbone(nn.Module):

    def __init__(self):
        super().__init__()
        self.pos_embed = None
        self.img_size = [224, 224]
        self.patch_size = 16
        self.embed_dim = 384
        self.cat_mode = 'direct'
        self.pos_embed_z = None
        self.pos_embed_x = None
        self.template_segment_pos_embed = None
        self.search_segment_pos_embed = None
        self.return_inter = False
        self.return_stage = [2, 5, 8, 11]
        self.add_cls_token = False
        self.add_sep_seg = False

    def finetune_track(self, cfg, patch_start_index=1):
        search_size = to_2tuple(cfg.DATA.SEARCH.SIZE)
        template_size = to_2tuple(cfg.DATA.TEMPLATE.SIZE)
        new_patch_size = cfg.MODEL.BACKBONE.STRIDE
        self.cat_mode = cfg.MODEL.BACKBONE.CAT_MODE
        self.return_inter = cfg.MODEL.RETURN_INTER
        self.return_stage = cfg.MODEL.RETURN_STAGES
        self.add_sep_seg = cfg.MODEL.BACKBONE.SEP_SEG
        if new_patch_size != self.patch_size:
            print('Inconsistent Patch Size With The Pretrained Weights, Interpolate The Weight!')
            old_patch_embed = {}
            for name, param in self.patch_embed.named_parameters():
                if 'weight' in name:
                    param = nn.functional.interpolate(param, size=(new_patch_size, new_patch_size), mode='bicubic', align_corners=False)
                    param = nn.Parameter(param)
                old_patch_embed[name] = param
            self.patch_embed = PatchEmbed(img_size=self.img_size, patch_size=new_patch_size, in_chans=3, embed_dim=self.embed_dim)
            self.patch_embed.proj.bias = old_patch_embed['proj.bias']
            self.patch_embed.proj.weight = old_patch_embed['proj.weight']
        patch_pos_embed = self.pos_embed[:, patch_start_index:, :]
        patch_pos_embed = patch_pos_embed.transpose(1, 2)
        B, E, Q = patch_pos_embed.shape
        P_H, P_W = (self.img_size[0] // self.patch_size, self.img_size[1] // self.patch_size)
        patch_pos_embed = patch_pos_embed.view(B, E, P_H, P_W)
        H, W = search_size
        new_P_H, new_P_W = (H // new_patch_size, W // new_patch_size)
        search_patch_pos_embed = nn.functional.interpolate(patch_pos_embed, size=(new_P_H, new_P_W), mode='bicubic', align_corners=False)
        search_patch_pos_embed = search_patch_pos_embed.flatten(2).transpose(1, 2)
        H, W = template_size
        new_P_H, new_P_W = (H // new_patch_size, W // new_patch_size)
        template_patch_pos_embed = nn.functional.interpolate(patch_pos_embed, size=(new_P_H, new_P_W), mode='bicubic', align_corners=False)
        template_patch_pos_embed = template_patch_pos_embed.flatten(2).transpose(1, 2)
        self.pos_embed_z = nn.Parameter(template_patch_pos_embed)
        self.pos_embed_x = nn.Parameter(search_patch_pos_embed)
        if self.add_cls_token and patch_start_index > 0:
            cls_pos_embed = self.pos_embed[:, 0:1, :]
            self.cls_pos_embed = nn.Parameter(cls_pos_embed)
        if self.add_sep_seg:
            self.template_segment_pos_embed = nn.Parameter(torch.zeros(1, 1, self.embed_dim))
            self.template_segment_pos_embed = trunc_normal_(self.template_segment_pos_embed, std=0.02)
            self.search_segment_pos_embed = nn.Parameter(torch.zeros(1, 1, self.embed_dim))
            self.search_segment_pos_embed = trunc_normal_(self.search_segment_pos_embed, std=0.02)
        if self.return_inter:
            for i_layer in self.return_stage:
                if i_layer != 11:
                    norm_layer = partial(nn.LayerNorm, eps=1e-06)
                    layer = norm_layer(self.embed_dim)
                    layer_name = f'norm{i_layer}'
                    self.add_module(layer_name, layer)

    def forward_features(self, z, x):
        B, H, W = (x.shape[0], x.shape[2], x.shape[3])
        x = self.patch_embed(x)
        z = self.patch_embed(z)
        if self.add_cls_token:
            cls_tokens = self.cls_token.expand(B, -1, -1)
            cls_tokens = cls_tokens + self.cls_pos_embed
        z += self.pos_embed_z
        x += self.pos_embed_x
        if self.add_sep_seg:
            x += self.search_segment_pos_embed
            z += self.template_segment_pos_embed
        x = combine_tokens(z, x, mode=self.cat_mode)
        if self.add_cls_token:
            x = torch.cat([cls_tokens, x], dim=1)
        x = self.pos_drop(x)
        for i, blk in enumerate(self.blocks):
            x = blk(x)
        lens_z = self.pos_embed_z.shape[1]
        lens_x = self.pos_embed_x.shape[1]
        x = recover_tokens(x, lens_z, lens_x, mode=self.cat_mode)
        aux_dict = {'attn': None}
        return (self.norm(x), aux_dict)

    def forward(self, z, x, **kwargs):
        """
        Joint feature extraction and relation modeling for the basic ViT backbone.
        Args:
            z (torch.Tensor): template feature, [B, C, H_z, W_z]
            x (torch.Tensor): search region feature, [B, C, H_x, W_x]

        Returns:
            x (torch.Tensor): merged template and search region feature, [B, L_z+L_x, C]
            attn : None
        """
        x, aux_dict = self.forward_features(z, x)
        return (x, aux_dict)

def __init__(self):
    super().__init__()
    self.pos_embed = None
    self.img_size = [224, 224]
    self.patch_size = 16
    self.embed_dim = 384
    self.cat_mode = 'direct'
    self.pos_embed_z = None
    self.pos_embed_x = None
    self.template_segment_pos_embed = None
    self.search_segment_pos_embed = None
    self.return_inter = False
    self.return_stage = [2, 5, 8, 11]
    self.add_cls_token = False
    self.add_sep_seg = False

def finetune_track(self, cfg, patch_start_index=1):
    search_size = to_2tuple(cfg.DATA.SEARCH.SIZE)
    template_size = to_2tuple(cfg.DATA.TEMPLATE.SIZE)
    new_patch_size = cfg.MODEL.BACKBONE.STRIDE
    self.cat_mode = cfg.MODEL.BACKBONE.CAT_MODE
    self.return_inter = cfg.MODEL.RETURN_INTER
    self.return_stage = cfg.MODEL.RETURN_STAGES
    self.add_sep_seg = cfg.MODEL.BACKBONE.SEP_SEG
    if new_patch_size != self.patch_size:
        print('Inconsistent Patch Size With The Pretrained Weights, Interpolate The Weight!')
        old_patch_embed = {}
        for name, param in self.patch_embed.named_parameters():
            if 'weight' in name:
                param = nn.functional.interpolate(param, size=(new_patch_size, new_patch_size), mode='bicubic', align_corners=False)
                param = nn.Parameter(param)
            old_patch_embed[name] = param
        self.patch_embed = PatchEmbed(img_size=self.img_size, patch_size=new_patch_size, in_chans=3, embed_dim=self.embed_dim)
        self.patch_embed.proj.bias = old_patch_embed['proj.bias']
        self.patch_embed.proj.weight = old_patch_embed['proj.weight']
    patch_pos_embed = self.pos_embed[:, patch_start_index:, :]
    patch_pos_embed = patch_pos_embed.transpose(1, 2)
    B, E, Q = patch_pos_embed.shape
    P_H, P_W = (self.img_size[0] // self.patch_size, self.img_size[1] // self.patch_size)
    patch_pos_embed = patch_pos_embed.view(B, E, P_H, P_W)
    H, W = search_size
    new_P_H, new_P_W = (H // new_patch_size, W // new_patch_size)
    search_patch_pos_embed = nn.functional.interpolate(patch_pos_embed, size=(new_P_H, new_P_W), mode='bicubic', align_corners=False)
    search_patch_pos_embed = search_patch_pos_embed.flatten(2).transpose(1, 2)
    H, W = template_size
    new_P_H, new_P_W = (H // new_patch_size, W // new_patch_size)
    template_patch_pos_embed = nn.functional.interpolate(patch_pos_embed, size=(new_P_H, new_P_W), mode='bicubic', align_corners=False)
    template_patch_pos_embed = template_patch_pos_embed.flatten(2).transpose(1, 2)
    self.pos_embed_z = nn.Parameter(template_patch_pos_embed)
    self.pos_embed_x = nn.Parameter(search_patch_pos_embed)
    if self.add_cls_token and patch_start_index > 0:
        cls_pos_embed = self.pos_embed[:, 0:1, :]
        self.cls_pos_embed = nn.Parameter(cls_pos_embed)
    if self.add_sep_seg:
        self.template_segment_pos_embed = nn.Parameter(torch.zeros(1, 1, self.embed_dim))
        self.template_segment_pos_embed = trunc_normal_(self.template_segment_pos_embed, std=0.02)
        self.search_segment_pos_embed = nn.Parameter(torch.zeros(1, 1, self.embed_dim))
        self.search_segment_pos_embed = trunc_normal_(self.search_segment_pos_embed, std=0.02)
    if self.return_inter:
        for i_layer in self.return_stage:
            if i_layer != 11:
                norm_layer = partial(nn.LayerNorm, eps=1e-06)
                layer = norm_layer(self.embed_dim)
                layer_name = f'norm{i_layer}'
                self.add_module(layer_name, layer)

class OSTrack(nn.Module):
    """ This is the base class for OSTrack """

    def __init__(self, transformer, box_head, aux_loss=False, head_type='CORNER'):
        """ Initializes the model.
        Parameters:
            transformer: torch module of the transformer architecture.
            aux_loss: True if auxiliary decoding losses (loss at each decoder layer) are to be used.
        """
        super().__init__()
        self.backbone = transformer
        self.box_head = box_head
        self.aux_loss = aux_loss
        self.head_type = head_type
        if head_type == 'CORNER' or head_type == 'CENTER':
            self.feat_sz_s = int(box_head.feat_sz)
            self.feat_len_s = int(box_head.feat_sz ** 2)
        if self.aux_loss:
            self.box_head = _get_clones(self.box_head, 6)

    def forward(self, template: torch.Tensor, search: torch.Tensor, ce_template_mask=None, ce_keep_rate=None, return_last_attn=False):
        x, aux_dict = self.backbone(z=template, x=search, ce_template_mask=ce_template_mask, ce_keep_rate=ce_keep_rate, return_last_attn=return_last_attn)
        feat_last = x
        if isinstance(x, list):
            feat_last = x[-1]
        out = self.forward_head(feat_last, None)
        out.update(aux_dict)
        out['backbone_feat'] = x
        return out

    def forward_head(self, cat_feature, gt_score_map=None):
        """
        cat_feature: output embeddings of the backbone, it can be (HW1+HW2, B, C) or (HW2, B, C)
        """
        enc_opt = cat_feature[:, -self.feat_len_s:]
        opt = enc_opt.unsqueeze(-1).permute((0, 3, 2, 1)).contiguous()
        bs, Nq, C, HW = opt.size()
        opt_feat = opt.view(-1, C, self.feat_sz_s, self.feat_sz_s)
        if self.head_type == 'CORNER':
            pred_box, score_map = self.box_head(opt_feat, True)
            outputs_coord = box_xyxy_to_cxcywh(pred_box)
            outputs_coord_new = outputs_coord.view(bs, Nq, 4)
            out = {'pred_boxes': outputs_coord_new, 'score_map': score_map}
            return out
        elif self.head_type == 'CENTER':
            score_map_ctr, bbox, size_map, offset_map = self.box_head(opt_feat, gt_score_map)
            outputs_coord = bbox
            outputs_coord_new = outputs_coord.view(bs, Nq, 4)
            out = {'pred_boxes': outputs_coord_new, 'score_map': score_map_ctr, 'size_map': size_map, 'offset_map': offset_map}
            return out
        else:
            raise NotImplementedError

def __init__(self, transformer, box_head, aux_loss=False, head_type='CORNER'):
    """ Initializes the model.
        Parameters:
            transformer: torch module of the transformer architecture.
            aux_loss: True if auxiliary decoding losses (loss at each decoder layer) are to be used.
        """
    super().__init__()
    self.backbone = transformer
    self.box_head = box_head
    self.aux_loss = aux_loss
    self.head_type = head_type
    if head_type == 'CORNER' or head_type == 'CENTER':
        self.feat_sz_s = int(box_head.feat_sz)
        self.feat_len_s = int(box_head.feat_sz ** 2)
    if self.aux_loss:
        self.box_head = _get_clones(self.box_head, 6)

def conv(in_planes, out_planes, kernel_size=3, stride=1, padding=1, dilation=1, freeze_bn=False):
    if freeze_bn:
        return nn.Sequential(nn.Conv2d(in_planes, out_planes, kernel_size=kernel_size, stride=stride, padding=padding, dilation=dilation, bias=True), FrozenBatchNorm2d(out_planes), nn.ReLU(inplace=True))
    else:
        return nn.Sequential(nn.Conv2d(in_planes, out_planes, kernel_size=kernel_size, stride=stride, padding=padding, dilation=dilation, bias=True), nn.BatchNorm2d(out_planes), nn.ReLU(inplace=True))

class CenterPredictor(nn.Module):

    def __init__(self, inplanes=64, channel=256, feat_sz=20, stride=16, freeze_bn=False):
        super(CenterPredictor, self).__init__()
        self.feat_sz = feat_sz
        self.stride = stride
        self.img_sz = self.feat_sz * self.stride
        self.conv1_ctr = conv(inplanes, channel, freeze_bn=freeze_bn)
        self.conv2_ctr = conv(channel, channel // 2, freeze_bn=freeze_bn)
        self.conv3_ctr = conv(channel // 2, channel // 4, freeze_bn=freeze_bn)
        self.conv4_ctr = conv(channel // 4, channel // 8, freeze_bn=freeze_bn)
        self.conv5_ctr = nn.Conv2d(channel // 8, 1, kernel_size=1)
        self.conv1_offset = conv(inplanes, channel, freeze_bn=freeze_bn)
        self.conv2_offset = conv(channel, channel // 2, freeze_bn=freeze_bn)
        self.conv3_offset = conv(channel // 2, channel // 4, freeze_bn=freeze_bn)
        self.conv4_offset = conv(channel // 4, channel // 8, freeze_bn=freeze_bn)
        self.conv5_offset = nn.Conv2d(channel // 8, 2, kernel_size=1)
        self.conv1_size = conv(inplanes, channel, freeze_bn=freeze_bn)
        self.conv2_size = conv(channel, channel // 2, freeze_bn=freeze_bn)
        self.conv3_size = conv(channel // 2, channel // 4, freeze_bn=freeze_bn)
        self.conv4_size = conv(channel // 4, channel // 8, freeze_bn=freeze_bn)
        self.conv5_size = nn.Conv2d(channel // 8, 2, kernel_size=1)
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)

    def forward(self, x, gt_score_map=None):
        """ Forward pass with input x. """
        score_map_ctr, size_map, offset_map = self.get_score_map(x)
        if gt_score_map is None:
            bbox = self.cal_bbox(score_map_ctr, size_map, offset_map)
        else:
            bbox = self.cal_bbox(gt_score_map.unsqueeze(1), size_map, offset_map)
        return (score_map_ctr, bbox, size_map, offset_map)

    def cal_bbox(self, score_map_ctr, size_map, offset_map, return_score=False):
        max_score, idx = torch.max(score_map_ctr.flatten(1), dim=1, keepdim=True)
        idx_y = idx // self.feat_sz
        idx_x = idx % self.feat_sz
        idx = idx.unsqueeze(1).expand(idx.shape[0], 2, 1)
        size = size_map.flatten(2).gather(dim=2, index=idx)
        offset = offset_map.flatten(2).gather(dim=2, index=idx).squeeze(-1)
        bbox = torch.cat([(idx_x.to(torch.float) + offset[:, :1]) / self.feat_sz, (idx_y.to(torch.float) + offset[:, 1:]) / self.feat_sz, size.squeeze(-1)], dim=1)
        if return_score:
            return (bbox, max_score)
        return bbox

    def get_pred(self, score_map_ctr, size_map, offset_map):
        max_score, idx = torch.max(score_map_ctr.flatten(1), dim=1, keepdim=True)
        idx_y = idx // self.feat_sz
        idx_x = idx % self.feat_sz
        idx = idx.unsqueeze(1).expand(idx.shape[0], 2, 1)
        size = size_map.flatten(2).gather(dim=2, index=idx)
        offset = offset_map.flatten(2).gather(dim=2, index=idx).squeeze(-1)
        return (size * self.feat_sz, offset)

    def get_score_map(self, x):

        def _sigmoid(x):
            y = torch.clamp(x.sigmoid_(), min=0.0001, max=1 - 0.0001)
            return y
        x_ctr1 = self.conv1_ctr(x)
        x_ctr2 = self.conv2_ctr(x_ctr1)
        x_ctr3 = self.conv3_ctr(x_ctr2)
        x_ctr4 = self.conv4_ctr(x_ctr3)
        score_map_ctr = self.conv5_ctr(x_ctr4)
        x_offset1 = self.conv1_offset(x)
        x_offset2 = self.conv2_offset(x_offset1)
        x_offset3 = self.conv3_offset(x_offset2)
        x_offset4 = self.conv4_offset(x_offset3)
        score_map_offset = self.conv5_offset(x_offset4)
        x_size1 = self.conv1_size(x)
        x_size2 = self.conv2_size(x_size1)
        x_size3 = self.conv3_size(x_size2)
        x_size4 = self.conv4_size(x_size3)
        score_map_size = self.conv5_size(x_size4)
        return (_sigmoid(score_map_ctr), _sigmoid(score_map_size), score_map_offset)

def __init__(self, inplanes=64, channel=256, feat_sz=20, stride=16, freeze_bn=False):
    super(CenterPredictor, self).__init__()
    self.feat_sz = feat_sz
    self.stride = stride
    self.img_sz = self.feat_sz * self.stride
    self.conv1_ctr = conv(inplanes, channel, freeze_bn=freeze_bn)
    self.conv2_ctr = conv(channel, channel // 2, freeze_bn=freeze_bn)
    self.conv3_ctr = conv(channel // 2, channel // 4, freeze_bn=freeze_bn)
    self.conv4_ctr = conv(channel // 4, channel // 8, freeze_bn=freeze_bn)
    self.conv5_ctr = nn.Conv2d(channel // 8, 1, kernel_size=1)
    self.conv1_offset = conv(inplanes, channel, freeze_bn=freeze_bn)
    self.conv2_offset = conv(channel, channel // 2, freeze_bn=freeze_bn)
    self.conv3_offset = conv(channel // 2, channel // 4, freeze_bn=freeze_bn)
    self.conv4_offset = conv(channel // 4, channel // 8, freeze_bn=freeze_bn)
    self.conv5_offset = nn.Conv2d(channel // 8, 2, kernel_size=1)
    self.conv1_size = conv(inplanes, channel, freeze_bn=freeze_bn)
    self.conv2_size = conv(channel, channel // 2, freeze_bn=freeze_bn)
    self.conv3_size = conv(channel // 2, channel // 4, freeze_bn=freeze_bn)
    self.conv4_size = conv(channel // 4, channel // 8, freeze_bn=freeze_bn)
    self.conv5_size = nn.Conv2d(channel // 8, 2, kernel_size=1)
    for p in self.parameters():
        if p.dim() > 1:
            nn.init.xavier_uniform_(p)

class MLP(nn.Module):
    """ Very simple multi-layer perceptron (also called FFN)"""

    def __init__(self, input_dim, hidden_dim, output_dim, num_layers, BN=False):
        super().__init__()
        self.num_layers = num_layers
        h = [hidden_dim] * (num_layers - 1)
        if BN:
            self.layers = nn.ModuleList((nn.Sequential(nn.Linear(n, k), nn.BatchNorm1d(k)) for n, k in zip([input_dim] + h, h + [output_dim])))
        else:
            self.layers = nn.ModuleList((nn.Linear(n, k) for n, k in zip([input_dim] + h, h + [output_dim])))

    def forward(self, x):
        for i, layer in enumerate(self.layers):
            x = F.relu(layer(x)) if i < self.num_layers - 1 else layer(x)
        return x

def __init__(self, input_dim, hidden_dim, output_dim, num_layers, BN=False):
    super().__init__()
    self.num_layers = num_layers
    h = [hidden_dim] * (num_layers - 1)
    if BN:
        self.layers = nn.ModuleList((nn.Sequential(nn.Linear(n, k), nn.BatchNorm1d(k)) for n, k in zip([input_dim] + h, h + [output_dim])))
    else:
        self.layers = nn.ModuleList((nn.Linear(n, k) for n, k in zip([input_dim] + h, h + [output_dim])))

class Attention(nn.Module):

    def __init__(self, dim, num_heads=8, qkv_bias=False, attn_drop=0.0, proj_drop=0.0, rpe=False, z_size=7, x_size=14):
        super().__init__()
        self.num_heads = num_heads
        head_dim = dim // num_heads
        self.scale = head_dim ** (-0.5)
        self.qkv = nn.Linear(dim, dim * 3, bias=qkv_bias)
        self.attn_drop = nn.Dropout(attn_drop)
        self.proj = nn.Linear(dim, dim)
        self.proj_drop = nn.Dropout(proj_drop)
        self.rpe = rpe
        if self.rpe:
            relative_position_index = generate_2d_concatenated_self_attention_relative_positional_encoding_index([z_size, z_size], [x_size, x_size])
            self.register_buffer('relative_position_index', relative_position_index)
            self.relative_position_bias_table = nn.Parameter(torch.empty((num_heads, relative_position_index.max() + 1)))
            trunc_normal_(self.relative_position_bias_table, std=0.02)

    def forward(self, x, mask=None, return_attention=False):
        B, N, C = x.shape
        qkv = self.qkv(x).reshape(B, N, 3, self.num_heads, C // self.num_heads).permute(2, 0, 3, 1, 4)
        q, k, v = qkv.unbind(0)
        attn = q @ k.transpose(-2, -1) * self.scale
        if self.rpe:
            relative_position_bias = self.relative_position_bias_table[:, self.relative_position_index].unsqueeze(0)
            attn += relative_position_bias
        if mask is not None:
            attn = attn.masked_fill(mask.unsqueeze(1).unsqueeze(2), float('-inf'))
        attn = attn.softmax(dim=-1)
        attn = self.attn_drop(attn)
        x = (attn @ v).transpose(1, 2).reshape(B, N, C)
        x = self.proj(x)
        x = self.proj_drop(x)
        if return_attention:
            return (x, attn)
        else:
            return x

def __init__(self, dim, num_heads=8, qkv_bias=False, attn_drop=0.0, proj_drop=0.0, rpe=False, z_size=7, x_size=14):
    super().__init__()
    self.num_heads = num_heads
    head_dim = dim // num_heads
    self.scale = head_dim ** (-0.5)
    self.qkv = nn.Linear(dim, dim * 3, bias=qkv_bias)
    self.attn_drop = nn.Dropout(attn_drop)
    self.proj = nn.Linear(dim, dim)
    self.proj_drop = nn.Dropout(proj_drop)
    self.rpe = rpe
    if self.rpe:
        relative_position_index = generate_2d_concatenated_self_attention_relative_positional_encoding_index([z_size, z_size], [x_size, x_size])
        self.register_buffer('relative_position_index', relative_position_index)
        self.relative_position_bias_table = nn.Parameter(torch.empty((num_heads, relative_position_index.max() + 1)))
        trunc_normal_(self.relative_position_bias_table, std=0.02)

class Attention_talking_head(nn.Module):

    def __init__(self, dim, num_heads=8, qkv_bias=False, qk_scale=None, attn_drop=0.0, proj_drop=0.0, rpe=True, z_size=7, x_size=14):
        super().__init__()
        self.num_heads = num_heads
        head_dim = dim // num_heads
        self.scale = qk_scale or head_dim ** (-0.5)
        self.qkv = nn.Linear(dim, dim * 3, bias=qkv_bias)
        self.attn_drop = nn.Dropout(attn_drop)
        self.proj = nn.Linear(dim, dim)
        self.proj_l = nn.Linear(num_heads, num_heads)
        self.proj_w = nn.Linear(num_heads, num_heads)
        self.proj_drop = nn.Dropout(proj_drop)
        self.rpe = rpe
        if self.rpe:
            relative_position_index = generate_2d_concatenated_self_attention_relative_positional_encoding_index([z_size, z_size], [x_size, x_size])
            self.register_buffer('relative_position_index', relative_position_index)
            self.relative_position_bias_table = nn.Parameter(torch.empty((num_heads, relative_position_index.max() + 1)))
            trunc_normal_(self.relative_position_bias_table, std=0.02)

    def forward(self, x, mask=None):
        B, N, C = x.shape
        qkv = self.qkv(x).reshape(B, N, 3, self.num_heads, C // self.num_heads).permute(2, 0, 3, 1, 4)
        q, k, v = (qkv[0] * self.scale, qkv[1], qkv[2])
        attn = q @ k.transpose(-2, -1)
        if self.rpe:
            relative_position_bias = self.relative_position_bias_table[:, self.relative_position_index].unsqueeze(0)
            attn += relative_position_bias
        if mask is not None:
            attn = attn.masked_fill(mask.unsqueeze(1).unsqueeze(2), float('-inf'))
        attn = self.proj_l(attn.permute(0, 2, 3, 1)).permute(0, 3, 1, 2)
        attn = attn.softmax(dim=-1)
        attn = self.proj_w(attn.permute(0, 2, 3, 1)).permute(0, 3, 1, 2)
        attn = self.attn_drop(attn)
        x = (attn @ v).transpose(1, 2).reshape(B, N, C)
        x = self.proj(x)
        x = self.proj_drop(x)
        return x

def __init__(self, dim, num_heads=8, qkv_bias=False, qk_scale=None, attn_drop=0.0, proj_drop=0.0, rpe=True, z_size=7, x_size=14):
    super().__init__()
    self.num_heads = num_heads
    head_dim = dim // num_heads
    self.scale = qk_scale or head_dim ** (-0.5)
    self.qkv = nn.Linear(dim, dim * 3, bias=qkv_bias)
    self.attn_drop = nn.Dropout(attn_drop)
    self.proj = nn.Linear(dim, dim)
    self.proj_l = nn.Linear(num_heads, num_heads)
    self.proj_w = nn.Linear(num_heads, num_heads)
    self.proj_drop = nn.Dropout(proj_drop)
    self.rpe = rpe
    if self.rpe:
        relative_position_index = generate_2d_concatenated_self_attention_relative_positional_encoding_index([z_size, z_size], [x_size, x_size])
        self.register_buffer('relative_position_index', relative_position_index)
        self.relative_position_bias_table = nn.Parameter(torch.empty((num_heads, relative_position_index.max() + 1)))
        trunc_normal_(self.relative_position_bias_table, std=0.02)

class RelativePosition2DEncoder(nn.Module):

    def __init__(self, num_heads, embed_size):
        super(RelativePosition2DEncoder, self).__init__()
        self.relative_position_bias_table = nn.Parameter(torch.empty((num_heads, embed_size)))
        trunc_normal_(self.relative_position_bias_table, std=0.02)

    def forward(self, attn_rpe_index):
        """
            Args:
                attn_rpe_index (torch.Tensor): (*), any shape containing indices, max(attn_rpe_index) < embed_size
            Returns:
                torch.Tensor: (1, num_heads, *)
        """
        return self.relative_position_bias_table[:, attn_rpe_index].unsqueeze(0)

def __init__(self, num_heads, embed_size):
    super(RelativePosition2DEncoder, self).__init__()
    self.relative_position_bias_table = nn.Parameter(torch.empty((num_heads, embed_size)))
    trunc_normal_(self.relative_position_bias_table, std=0.02)

class CEBlock(nn.Module):

    def __init__(self, dim, num_heads, mlp_ratio=4.0, qkv_bias=False, drop=0.0, attn_drop=0.0, drop_path=0.0, act_layer=nn.GELU, norm_layer=nn.LayerNorm, keep_ratio_search=1.0):
        super().__init__()
        self.norm1 = norm_layer(dim)
        self.attn = Attention(dim, num_heads=num_heads, qkv_bias=qkv_bias, attn_drop=attn_drop, proj_drop=drop)
        self.drop_path = DropPath(drop_path) if drop_path > 0.0 else nn.Identity()
        self.norm2 = norm_layer(dim)
        mlp_hidden_dim = int(dim * mlp_ratio)
        self.mlp = Mlp(in_features=dim, hidden_features=mlp_hidden_dim, act_layer=act_layer, drop=drop)
        self.keep_ratio_search = keep_ratio_search

    def forward(self, x, global_index_template, global_index_search, mask=None, ce_template_mask=None, keep_ratio_search=None):
        x_attn, attn = self.attn(self.norm1(x), mask, True)
        x = x + self.drop_path(x_attn)
        lens_t = global_index_template.shape[1]
        removed_index_search = None
        if self.keep_ratio_search < 1 and (keep_ratio_search is None or keep_ratio_search < 1):
            keep_ratio_search = self.keep_ratio_search if keep_ratio_search is None else keep_ratio_search
            x, global_index_search, removed_index_search = candidate_elimination(attn, x, lens_t, keep_ratio_search, global_index_search, ce_template_mask)
        x = x + self.drop_path(self.mlp(self.norm2(x)))
        return (x, global_index_template, global_index_search, removed_index_search, attn)

def __init__(self, dim, num_heads, mlp_ratio=4.0, qkv_bias=False, drop=0.0, attn_drop=0.0, drop_path=0.0, act_layer=nn.GELU, norm_layer=nn.LayerNorm, keep_ratio_search=1.0):
    super().__init__()
    self.norm1 = norm_layer(dim)
    self.attn = Attention(dim, num_heads=num_heads, qkv_bias=qkv_bias, attn_drop=attn_drop, proj_drop=drop)
    self.drop_path = DropPath(drop_path) if drop_path > 0.0 else nn.Identity()
    self.norm2 = norm_layer(dim)
    mlp_hidden_dim = int(dim * mlp_ratio)
    self.mlp = Mlp(in_features=dim, hidden_features=mlp_hidden_dim, act_layer=act_layer, drop=drop)
    self.keep_ratio_search = keep_ratio_search

class Block(nn.Module):

    def __init__(self, dim, num_heads, mlp_ratio=4.0, qkv_bias=False, drop=0.0, attn_drop=0.0, drop_path=0.0, act_layer=nn.GELU, norm_layer=nn.LayerNorm):
        super().__init__()
        self.norm1 = norm_layer(dim)
        self.attn = Attention(dim, num_heads=num_heads, qkv_bias=qkv_bias, attn_drop=attn_drop, proj_drop=drop)
        self.drop_path = DropPath(drop_path) if drop_path > 0.0 else nn.Identity()
        self.norm2 = norm_layer(dim)
        mlp_hidden_dim = int(dim * mlp_ratio)
        self.mlp = Mlp(in_features=dim, hidden_features=mlp_hidden_dim, act_layer=act_layer, drop=drop)

    def forward(self, x, mask=None):
        x = x + self.drop_path(self.attn(self.norm1(x), mask))
        x = x + self.drop_path(self.mlp(self.norm2(x)))
        return x

def __init__(self, dim, num_heads, mlp_ratio=4.0, qkv_bias=False, drop=0.0, attn_drop=0.0, drop_path=0.0, act_layer=nn.GELU, norm_layer=nn.LayerNorm):
    super().__init__()
    self.norm1 = norm_layer(dim)
    self.attn = Attention(dim, num_heads=num_heads, qkv_bias=qkv_bias, attn_drop=attn_drop, proj_drop=drop)
    self.drop_path = DropPath(drop_path) if drop_path > 0.0 else nn.Identity()
    self.norm2 = norm_layer(dim)
    mlp_hidden_dim = int(dim * mlp_ratio)
    self.mlp = Mlp(in_features=dim, hidden_features=mlp_hidden_dim, act_layer=act_layer, drop=drop)

class PatchEmbed(nn.Module):
    """ 2D Image to Patch Embedding
    """

    def __init__(self, img_size=224, patch_size=16, in_chans=3, embed_dim=768, norm_layer=None, flatten=True):
        super().__init__()
        img_size = to_2tuple(img_size)
        patch_size = to_2tuple(patch_size)
        self.img_size = img_size
        self.patch_size = patch_size
        self.grid_size = (img_size[0] // patch_size[0], img_size[1] // patch_size[1])
        self.num_patches = self.grid_size[0] * self.grid_size[1]
        self.flatten = flatten
        self.proj = nn.Conv2d(in_chans, embed_dim, kernel_size=patch_size, stride=patch_size)
        self.norm = norm_layer(embed_dim) if norm_layer else nn.Identity()

    def forward(self, x):
        x = self.proj(x)
        if self.flatten:
            x = x.flatten(2).transpose(1, 2)
        x = self.norm(x)
        return x

def __init__(self, img_size=224, patch_size=16, in_chans=3, embed_dim=768, norm_layer=None, flatten=True):
    super().__init__()
    img_size = to_2tuple(img_size)
    patch_size = to_2tuple(patch_size)
    self.img_size = img_size
    self.patch_size = patch_size
    self.grid_size = (img_size[0] // patch_size[0], img_size[1] // patch_size[1])
    self.num_patches = self.grid_size[0] * self.grid_size[1]
    self.flatten = flatten
    self.proj = nn.Conv2d(in_chans, embed_dim, kernel_size=patch_size, stride=patch_size)
    self.norm = norm_layer(embed_dim) if norm_layer else nn.Identity()

class FrozenBatchNorm2d(torch.nn.Module):
    """
    BatchNorm2d where the batch statistics and the affine parameters are fixed.

    Copy-paste from torchvision.misc.ops with added eps before rqsrt,
    without which any other models than torchvision.models.resnet[18,34,50,101]
    produce nans.
    """

    def __init__(self, n):
        super(FrozenBatchNorm2d, self).__init__()
        self.register_buffer('weight', torch.ones(n))
        self.register_buffer('bias', torch.zeros(n))
        self.register_buffer('running_mean', torch.zeros(n))
        self.register_buffer('running_var', torch.ones(n))

    def _load_from_state_dict(self, state_dict, prefix, local_metadata, strict, missing_keys, unexpected_keys, error_msgs):
        num_batches_tracked_key = prefix + 'num_batches_tracked'
        if num_batches_tracked_key in state_dict:
            del state_dict[num_batches_tracked_key]
        super(FrozenBatchNorm2d, self)._load_from_state_dict(state_dict, prefix, local_metadata, strict, missing_keys, unexpected_keys, error_msgs)

    def forward(self, x):
        w = self.weight.reshape(1, -1, 1, 1)
        b = self.bias.reshape(1, -1, 1, 1)
        rv = self.running_var.reshape(1, -1, 1, 1)
        rm = self.running_mean.reshape(1, -1, 1, 1)
        eps = 1e-05
        scale = w * (rv + eps).rsqrt()
        bias = b - rm * scale
        return x * scale + bias

def __init__(self, n):
    super(FrozenBatchNorm2d, self).__init__()
    self.register_buffer('weight', torch.ones(n))
    self.register_buffer('bias', torch.zeros(n))
    self.register_buffer('running_mean', torch.zeros(n))
    self.register_buffer('running_var', torch.ones(n))

def _load_from_state_dict(self, state_dict, prefix, local_metadata, strict, missing_keys, unexpected_keys, error_msgs):
    num_batches_tracked_key = prefix + 'num_batches_tracked'
    if num_batches_tracked_key in state_dict:
        del state_dict[num_batches_tracked_key]
    super(FrozenBatchNorm2d, self)._load_from_state_dict(state_dict, prefix, local_metadata, strict, missing_keys, unexpected_keys, error_msgs)

class DataModuleFromConfig(pl.LightningDataModule):

    def __init__(self, batch_size, train=None, validation=None, test=None, predict=None, wrap=False, num_workers=None, shuffle_test_loader=False, use_worker_init_fn=False, shuffle_val_dataloader=False):
        super().__init__()
        self.batch_size = batch_size
        self.dataset_configs = dict()
        self.num_workers = num_workers if num_workers is not None else batch_size * 2
        self.use_worker_init_fn = use_worker_init_fn
        if train is not None:
            self.dataset_configs['train'] = train
            self.train_dataloader = self._train_dataloader
        if validation is not None:
            self.dataset_configs['validation'] = validation
            self.val_dataloader = partial(self._val_dataloader, shuffle=shuffle_val_dataloader)
        if test is not None:
            self.dataset_configs['test'] = test
            self.test_dataloader = partial(self._test_dataloader, shuffle=shuffle_test_loader)
        if predict is not None:
            self.dataset_configs['predict'] = predict
            self.predict_dataloader = self._predict_dataloader
        self.wrap = wrap

    def prepare_data(self):
        for data_cfg in self.dataset_configs.values():
            instantiate_from_config(data_cfg)

    def setup(self, stage=None):
        self.datasets = dict(((k, instantiate_from_config(self.dataset_configs[k])) for k in self.dataset_configs))
        if self.wrap:
            for k in self.datasets:
                self.datasets[k] = WrappedDataset(self.datasets[k])

    def _train_dataloader(self):
        is_iterable_dataset = isinstance(self.datasets['train'], Txt2ImgIterableBaseDataset)
        if is_iterable_dataset or self.use_worker_init_fn:
            init_fn = worker_init_fn
        else:
            init_fn = None
        return DataLoader(self.datasets['train'], batch_size=self.batch_size, num_workers=self.num_workers, shuffle=False if is_iterable_dataset else True, worker_init_fn=init_fn)

    def _val_dataloader(self, shuffle=False):
        if isinstance(self.datasets['validation'], Txt2ImgIterableBaseDataset) or self.use_worker_init_fn:
            init_fn = worker_init_fn
        else:
            init_fn = None
        return DataLoader(self.datasets['validation'], batch_size=self.batch_size, num_workers=self.num_workers, worker_init_fn=init_fn, shuffle=shuffle)

    def _test_dataloader(self, shuffle=False):
        is_iterable_dataset = isinstance(self.datasets['train'], Txt2ImgIterableBaseDataset)
        if is_iterable_dataset or self.use_worker_init_fn:
            init_fn = worker_init_fn
        else:
            init_fn = None
        shuffle = shuffle and (not is_iterable_dataset)
        return DataLoader(self.datasets['test'], batch_size=self.batch_size, num_workers=self.num_workers, worker_init_fn=init_fn, shuffle=shuffle)

    def _predict_dataloader(self, shuffle=False):
        if isinstance(self.datasets['predict'], Txt2ImgIterableBaseDataset) or self.use_worker_init_fn:
            init_fn = worker_init_fn
        else:
            init_fn = None
        return DataLoader(self.datasets['predict'], batch_size=self.batch_size, num_workers=self.num_workers, worker_init_fn=init_fn)

def __init__(self, batch_size, train=None, validation=None, test=None, predict=None, wrap=False, num_workers=None, shuffle_test_loader=False, use_worker_init_fn=False, shuffle_val_dataloader=False):
    super().__init__()
    self.batch_size = batch_size
    self.dataset_configs = dict()
    self.num_workers = num_workers if num_workers is not None else batch_size * 2
    self.use_worker_init_fn = use_worker_init_fn
    if train is not None:
        self.dataset_configs['train'] = train
        self.train_dataloader = self._train_dataloader
    if validation is not None:
        self.dataset_configs['validation'] = validation
        self.val_dataloader = partial(self._val_dataloader, shuffle=shuffle_val_dataloader)
    if test is not None:
        self.dataset_configs['test'] = test
        self.test_dataloader = partial(self._test_dataloader, shuffle=shuffle_test_loader)
    if predict is not None:
        self.dataset_configs['predict'] = predict
        self.predict_dataloader = self._predict_dataloader
    self.wrap = wrap

class SetupCallback(Callback):

    def __init__(self, resume, now, logdir, ckptdir, cfgdir, config, lightning_config):
        super().__init__()
        self.resume = resume
        self.now = now
        self.logdir = logdir
        self.ckptdir = ckptdir
        self.cfgdir = cfgdir
        self.config = config
        self.lightning_config = lightning_config

    def on_keyboard_interrupt(self, trainer, pl_module):
        if trainer.global_rank == 0:
            print('Summoning checkpoint.')
            ckpt_path = os.path.join(self.ckptdir, 'last.ckpt')
            trainer.save_checkpoint(ckpt_path)

    def on_pretrain_routine_start(self, trainer, pl_module):
        if trainer.global_rank == 0:
            os.makedirs(self.logdir, exist_ok=True)
            os.makedirs(self.ckptdir, exist_ok=True)
            os.makedirs(self.cfgdir, exist_ok=True)
            if 'callbacks' in self.lightning_config:
                if 'metrics_over_trainsteps_checkpoint' in self.lightning_config['callbacks']:
                    os.makedirs(os.path.join(self.ckptdir, 'trainstep_checkpoints'), exist_ok=True)
            print('Project config')
            print(OmegaConf.to_yaml(self.config))
            OmegaConf.save(self.config, os.path.join(self.cfgdir, '{}-project.yaml'.format(self.now)))
            print('Lightning config')
            print(OmegaConf.to_yaml(self.lightning_config))
            OmegaConf.save(OmegaConf.create({'lightning': self.lightning_config}), os.path.join(self.cfgdir, '{}-lightning.yaml'.format(self.now)))
        elif not self.resume and os.path.exists(self.logdir):
            dst, name = os.path.split(self.logdir)
            dst = os.path.join(dst, 'child_runs', name)
            os.makedirs(os.path.split(dst)[0], exist_ok=True)
            try:
                os.rename(self.logdir, dst)
            except FileNotFoundError:
                pass

def __init__(self, resume, now, logdir, ckptdir, cfgdir, config, lightning_config):
    super().__init__()
    self.resume = resume
    self.now = now
    self.logdir = logdir
    self.ckptdir = ckptdir
    self.cfgdir = cfgdir
    self.config = config
    self.lightning_config = lightning_config

class ImageLogger(Callback):

    def __init__(self, batch_frequency, max_images, clamp=True, increase_log_steps=True, rescale=True, disabled=False, log_on_batch_idx=False, log_first_step=False, log_images_kwargs=None):
        super().__init__()
        self.rescale = rescale
        self.batch_freq = batch_frequency
        self.max_images = max_images
        self.logger_log_images = {pl.loggers.TestTubeLogger: self._testtube}
        self.log_steps = [2 ** n for n in range(int(np.log2(self.batch_freq)) + 1)]
        if not increase_log_steps:
            self.log_steps = [self.batch_freq]
        self.clamp = clamp
        self.disabled = disabled
        self.log_on_batch_idx = log_on_batch_idx
        self.log_images_kwargs = log_images_kwargs if log_images_kwargs else {}
        self.log_first_step = log_first_step

    @rank_zero_only
    def _testtube(self, pl_module, images, batch_idx, split):
        for k in images:
            grid = torchvision.utils.make_grid(images[k])
            grid = (grid + 1.0) / 2.0
            tag = f'{split}/{k}'
            pl_module.logger.experiment.add_image(tag, grid, global_step=pl_module.global_step)

    @rank_zero_only
    def log_local(self, save_dir, split, images, global_step, current_epoch, batch_idx):
        root = os.path.join(save_dir, 'images', split)
        for k in images:
            grid = torchvision.utils.make_grid(images[k], nrow=4)
            if self.rescale:
                grid = (grid + 1.0) / 2.0
            grid = grid.transpose(0, 1).transpose(1, 2).squeeze(-1)
            grid = grid.numpy()
            grid = (grid * 255).astype(np.uint8)
            filename = '{}_gs-{:06}_e-{:06}_b-{:06}.png'.format(k, global_step, current_epoch, batch_idx)
            path = os.path.join(root, filename)
            os.makedirs(os.path.split(path)[0], exist_ok=True)
            Image.fromarray(grid).save(path)

    def log_img(self, pl_module, batch, batch_idx, split='train'):
        check_idx = batch_idx if self.log_on_batch_idx else pl_module.global_step
        if self.check_frequency(check_idx) and hasattr(pl_module, 'log_images') and callable(pl_module.log_images) and (self.max_images > 0):
            logger = type(pl_module.logger)
            is_train = pl_module.training
            if is_train:
                pl_module.eval()
            with torch.no_grad():
                images = pl_module.log_images(batch, split=split, **self.log_images_kwargs)
            for k in images:
                N = min(images[k].shape[0], self.max_images)
                images[k] = images[k][:N]
                if isinstance(images[k], torch.Tensor):
                    images[k] = images[k].detach().cpu()
                    if self.clamp:
                        images[k] = torch.clamp(images[k], -1.0, 1.0)
            self.log_local(pl_module.logger.save_dir, split, images, pl_module.global_step, pl_module.current_epoch, batch_idx)
            logger_log_images = self.logger_log_images.get(logger, lambda *args, **kwargs: None)
            logger_log_images(pl_module, images, pl_module.global_step, split)
            if is_train:
                pl_module.train()

    def check_frequency(self, check_idx):
        if (check_idx % self.batch_freq == 0 or check_idx in self.log_steps) and (check_idx > 0 or self.log_first_step):
            try:
                self.log_steps.pop(0)
            except IndexError as e:
                print(e)
                pass
            return True
        return False

    def on_train_batch_end(self, trainer, pl_module, outputs, batch, batch_idx, dataloader_idx):
        if not self.disabled and (pl_module.global_step > 0 or self.log_first_step):
            self.log_img(pl_module, batch, batch_idx, split='train')

    def on_validation_batch_end(self, trainer, pl_module, outputs, batch, batch_idx, dataloader_idx):
        if not self.disabled and pl_module.global_step > 0:
            self.log_img(pl_module, batch, batch_idx, split='val')
        if hasattr(pl_module, 'calibrate_grad_norm'):
            if (pl_module.calibrate_grad_norm and batch_idx % 25 == 0) and batch_idx > 0:
                self.log_gradients(trainer, pl_module, batch_idx=batch_idx)

def __init__(self, batch_frequency, max_images, clamp=True, increase_log_steps=True, rescale=True, disabled=False, log_on_batch_idx=False, log_first_step=False, log_images_kwargs=None):
    super().__init__()
    self.rescale = rescale
    self.batch_freq = batch_frequency
    self.max_images = max_images
    self.logger_log_images = {pl.loggers.TestTubeLogger: self._testtube}
    self.log_steps = [2 ** n for n in range(int(np.log2(self.batch_freq)) + 1)]
    if not increase_log_steps:
        self.log_steps = [self.batch_freq]
    self.clamp = clamp
    self.disabled = disabled
    self.log_on_batch_idx = log_on_batch_idx
    self.log_images_kwargs = log_images_kwargs if log_images_kwargs else {}
    self.log_first_step = log_first_step

class LitEma(nn.Module):

    def __init__(self, model, decay=0.9999, use_num_upates=True):
        super().__init__()
        if decay < 0.0 or decay > 1.0:
            raise ValueError('Decay must be between 0 and 1')
        self.m_name2s_name = {}
        self.register_buffer('decay', torch.tensor(decay, dtype=torch.float32))
        self.register_buffer('num_updates', torch.tensor(0, dtype=torch.int) if use_num_upates else torch.tensor(-1, dtype=torch.int))
        for name, p in model.named_parameters():
            if p.requires_grad:
                s_name = name.replace('.', '')
                self.m_name2s_name.update({name: s_name})
                self.register_buffer(s_name, p.clone().detach().data)
        self.collected_params = []

    def forward(self, model):
        decay = self.decay
        if self.num_updates >= 0:
            self.num_updates += 1
            decay = min(self.decay, (1 + self.num_updates) / (10 + self.num_updates))
        one_minus_decay = 1.0 - decay
        with torch.no_grad():
            m_param = dict(model.named_parameters())
            shadow_params = dict(self.named_buffers())
            for key in m_param:
                if m_param[key].requires_grad:
                    sname = self.m_name2s_name[key]
                    shadow_params[sname] = shadow_params[sname].type_as(m_param[key])
                    shadow_params[sname].sub_(one_minus_decay * (shadow_params[sname] - m_param[key]))
                else:
                    assert not key in self.m_name2s_name

    def copy_to(self, model):
        m_param = dict(model.named_parameters())
        shadow_params = dict(self.named_buffers())
        for key in m_param:
            if m_param[key].requires_grad:
                m_param[key].data.copy_(shadow_params[self.m_name2s_name[key]].data)
            else:
                assert not key in self.m_name2s_name

    def store(self, parameters):
        """
        Save the current parameters for restoring later.
        Args:
          parameters: Iterable of `torch.nn.Parameter`; the parameters to be
            temporarily stored.
        """
        self.collected_params = [param.clone() for param in parameters]

    def restore(self, parameters):
        """
        Restore the parameters stored with the `store` method.
        Useful to validate the model with EMA parameters without affecting the
        original optimization process. Store the parameters before the
        `copy_to` method. After validation (or model saving), use this to
        restore the former parameters.
        Args:
          parameters: Iterable of `torch.nn.Parameter`; the parameters to be
            updated with the stored parameters.
        """
        for c_param, param in zip(self.collected_params, parameters):
            param.data.copy_(c_param.data)

def __init__(self, model, decay=0.9999, use_num_upates=True):
    super().__init__()
    if decay < 0.0 or decay > 1.0:
        raise ValueError('Decay must be between 0 and 1')
    self.m_name2s_name = {}
    self.register_buffer('decay', torch.tensor(decay, dtype=torch.float32))
    self.register_buffer('num_updates', torch.tensor(0, dtype=torch.int) if use_num_upates else torch.tensor(-1, dtype=torch.int))
    for name, p in model.named_parameters():
        if p.requires_grad:
            s_name = name.replace('.', '')
            self.m_name2s_name.update({name: s_name})
            self.register_buffer(s_name, p.clone().detach().data)
    self.collected_params = []

class AbsolutePositionalEmbedding(nn.Module):

    def __init__(self, dim, max_seq_len):
        super().__init__()
        self.emb = nn.Embedding(max_seq_len, dim)
        self.init_()

    def init_(self):
        nn.init.normal_(self.emb.weight, std=0.02)

    def forward(self, x):
        n = torch.arange(x.shape[1], device=x.device)
        return self.emb(n)[None, :, :]

def __init__(self, dim, max_seq_len):
    super().__init__()
    self.emb = nn.Embedding(max_seq_len, dim)
    self.init_()

def init_(self):
    nn.init.normal_(self.emb.weight, std=0.02)

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

def __init__(self, dim):
    super().__init__()
    inv_freq = 1.0 / 10000 ** (torch.arange(0, dim, 2).float() / dim)
    self.register_buffer('inv_freq', inv_freq)

class Scale(nn.Module):

    def __init__(self, value, fn):
        super().__init__()
        self.value = value
        self.fn = fn

    def forward(self, x, **kwargs):
        x, *rest = self.fn(x, **kwargs)
        return (x * self.value, *rest)

def __init__(self, value, fn):
    super().__init__()
    self.value = value
    self.fn = fn

class Rezero(nn.Module):

    def __init__(self, fn):
        super().__init__()
        self.fn = fn
        self.g = nn.Parameter(torch.zeros(1))

    def forward(self, x, **kwargs):
        x, *rest = self.fn(x, **kwargs)
        return (x * self.g, *rest)

def __init__(self, fn):
    super().__init__()
    self.fn = fn
    self.g = nn.Parameter(torch.zeros(1))

class ScaleNorm(nn.Module):

    def __init__(self, dim, eps=1e-05):
        super().__init__()
        self.scale = dim ** (-0.5)
        self.eps = eps
        self.g = nn.Parameter(torch.ones(1))

    def forward(self, x):
        norm = torch.norm(x, dim=-1, keepdim=True) * self.scale
        return x / norm.clamp(min=self.eps) * self.g

def __init__(self, dim, eps=1e-05):
    super().__init__()
    self.scale = dim ** (-0.5)
    self.eps = eps
    self.g = nn.Parameter(torch.ones(1))

class RMSNorm(nn.Module):

    def __init__(self, dim, eps=1e-08):
        super().__init__()
        self.scale = dim ** (-0.5)
        self.eps = eps
        self.g = nn.Parameter(torch.ones(dim))

    def forward(self, x):
        norm = torch.norm(x, dim=-1, keepdim=True) * self.scale
        return x / norm.clamp(min=self.eps) * self.g

def __init__(self, dim, eps=1e-08):
    super().__init__()
    self.scale = dim ** (-0.5)
    self.eps = eps
    self.g = nn.Parameter(torch.ones(dim))

class GRUGating(nn.Module):

    def __init__(self, dim):
        super().__init__()
        self.gru = nn.GRUCell(dim, dim)

    def forward(self, x, residual):
        gated_output = self.gru(rearrange(x, 'b n d -> (b n) d'), rearrange(residual, 'b n d -> (b n) d'))
        return gated_output.reshape_as(x)

def __init__(self, dim):
    super().__init__()
    self.gru = nn.GRUCell(dim, dim)

class GEGLU(nn.Module):

    def __init__(self, dim_in, dim_out):
        super().__init__()
        self.proj = nn.Linear(dim_in, dim_out * 2)

    def forward(self, x):
        x, gate = self.proj(x).chunk(2, dim=-1)
        return x * F.gelu(gate)

def __init__(self, dim_in, dim_out):
    super().__init__()
    self.proj = nn.Linear(dim_in, dim_out * 2)

class FeedForward(nn.Module):

    def __init__(self, dim, dim_out=None, mult=4, glu=False, dropout=0.0):
        super().__init__()
        inner_dim = int(dim * mult)
        dim_out = default(dim_out, dim)
        project_in = nn.Sequential(nn.Linear(dim, inner_dim), nn.GELU()) if not glu else GEGLU(dim, inner_dim)
        self.net = nn.Sequential(project_in, nn.Dropout(dropout), nn.Linear(inner_dim, dim_out))

    def forward(self, x):
        return self.net(x)

def __init__(self, dim, dim_out=None, mult=4, glu=False, dropout=0.0):
    super().__init__()
    inner_dim = int(dim * mult)
    dim_out = default(dim_out, dim)
    project_in = nn.Sequential(nn.Linear(dim, inner_dim), nn.GELU()) if not glu else GEGLU(dim, inner_dim)
    self.net = nn.Sequential(project_in, nn.Dropout(dropout), nn.Linear(inner_dim, dim_out))

class Attention(nn.Module):

    def __init__(self, dim, dim_head=DEFAULT_DIM_HEAD, heads=8, causal=False, mask=None, talking_heads=False, sparse_topk=None, use_entmax15=False, num_mem_kv=0, dropout=0.0, on_attn=False):
        super().__init__()
        if use_entmax15:
            raise NotImplementedError('Check out entmax activation instead of softmax activation!')
        self.scale = dim_head ** (-0.5)
        self.heads = heads
        self.causal = causal
        self.mask = mask
        inner_dim = dim_head * heads
        self.to_q = nn.Linear(dim, inner_dim, bias=False)
        self.to_k = nn.Linear(dim, inner_dim, bias=False)
        self.to_v = nn.Linear(dim, inner_dim, bias=False)
        self.dropout = nn.Dropout(dropout)
        self.talking_heads = talking_heads
        if talking_heads:
            self.pre_softmax_proj = nn.Parameter(torch.randn(heads, heads))
            self.post_softmax_proj = nn.Parameter(torch.randn(heads, heads))
        self.sparse_topk = sparse_topk
        self.attn_fn = F.softmax
        self.num_mem_kv = num_mem_kv
        if num_mem_kv > 0:
            self.mem_k = nn.Parameter(torch.randn(heads, num_mem_kv, dim_head))
            self.mem_v = nn.Parameter(torch.randn(heads, num_mem_kv, dim_head))
        self.attn_on_attn = on_attn
        self.to_out = nn.Sequential(nn.Linear(inner_dim, dim * 2), nn.GLU()) if on_attn else nn.Linear(inner_dim, dim)

    def forward(self, x, context=None, mask=None, context_mask=None, rel_pos=None, sinusoidal_emb=None, prev_attn=None, mem=None):
        b, n, _, h, talking_heads, device = (*x.shape, self.heads, self.talking_heads, x.device)
        kv_input = default(context, x)
        q_input = x
        k_input = kv_input
        v_input = kv_input
        if exists(mem):
            k_input = torch.cat((mem, k_input), dim=-2)
            v_input = torch.cat((mem, v_input), dim=-2)
        if exists(sinusoidal_emb):
            offset = k_input.shape[-2] - q_input.shape[-2]
            q_input = q_input + sinusoidal_emb(q_input, offset=offset)
            k_input = k_input + sinusoidal_emb(k_input)
        q = self.to_q(q_input)
        k = self.to_k(k_input)
        v = self.to_v(v_input)
        q, k, v = map(lambda t: rearrange(t, 'b n (h d) -> b h n d', h=h), (q, k, v))
        input_mask = None
        if any(map(exists, (mask, context_mask))):
            q_mask = default(mask, lambda: torch.ones((b, n), device=device).bool())
            k_mask = q_mask if not exists(context) else context_mask
            k_mask = default(k_mask, lambda: torch.ones((b, k.shape[-2]), device=device).bool())
            q_mask = rearrange(q_mask, 'b i -> b () i ()')
            k_mask = rearrange(k_mask, 'b j -> b () () j')
            input_mask = q_mask * k_mask
        if self.num_mem_kv > 0:
            mem_k, mem_v = map(lambda t: repeat(t, 'h n d -> b h n d', b=b), (self.mem_k, self.mem_v))
            k = torch.cat((mem_k, k), dim=-2)
            v = torch.cat((mem_v, v), dim=-2)
            if exists(input_mask):
                input_mask = F.pad(input_mask, (self.num_mem_kv, 0), value=True)
        dots = einsum('b h i d, b h j d -> b h i j', q, k) * self.scale
        mask_value = max_neg_value(dots)
        if exists(prev_attn):
            dots = dots + prev_attn
        pre_softmax_attn = dots
        if talking_heads:
            dots = einsum('b h i j, h k -> b k i j', dots, self.pre_softmax_proj).contiguous()
        if exists(rel_pos):
            dots = rel_pos(dots)
        if exists(input_mask):
            dots.masked_fill_(~input_mask, mask_value)
            del input_mask
        if self.causal:
            i, j = dots.shape[-2:]
            r = torch.arange(i, device=device)
            mask = rearrange(r, 'i -> () () i ()') < rearrange(r, 'j -> () () () j')
            mask = F.pad(mask, (j - i, 0), value=False)
            dots.masked_fill_(mask, mask_value)
            del mask
        if exists(self.sparse_topk) and self.sparse_topk < dots.shape[-1]:
            top, _ = dots.topk(self.sparse_topk, dim=-1)
            vk = top[..., -1].unsqueeze(-1).expand_as(dots)
            mask = dots < vk
            dots.masked_fill_(mask, mask_value)
            del mask
        attn = self.attn_fn(dots, dim=-1)
        post_softmax_attn = attn
        attn = self.dropout(attn)
        if talking_heads:
            attn = einsum('b h i j, h k -> b k i j', attn, self.post_softmax_proj).contiguous()
        out = einsum('b h i j, b h j d -> b h i d', attn, v)
        out = rearrange(out, 'b h n d -> b n (h d)')
        intermediates = Intermediates(pre_softmax_attn=pre_softmax_attn, post_softmax_attn=post_softmax_attn)
        return (self.to_out(out), intermediates)

def __init__(self, dim, dim_head=DEFAULT_DIM_HEAD, heads=8, causal=False, mask=None, talking_heads=False, sparse_topk=None, use_entmax15=False, num_mem_kv=0, dropout=0.0, on_attn=False):
    super().__init__()
    if use_entmax15:
        raise NotImplementedError('Check out entmax activation instead of softmax activation!')
    self.scale = dim_head ** (-0.5)
    self.heads = heads
    self.causal = causal
    self.mask = mask
    inner_dim = dim_head * heads
    self.to_q = nn.Linear(dim, inner_dim, bias=False)
    self.to_k = nn.Linear(dim, inner_dim, bias=False)
    self.to_v = nn.Linear(dim, inner_dim, bias=False)
    self.dropout = nn.Dropout(dropout)
    self.talking_heads = talking_heads
    if talking_heads:
        self.pre_softmax_proj = nn.Parameter(torch.randn(heads, heads))
        self.post_softmax_proj = nn.Parameter(torch.randn(heads, heads))
    self.sparse_topk = sparse_topk
    self.attn_fn = F.softmax
    self.num_mem_kv = num_mem_kv
    if num_mem_kv > 0:
        self.mem_k = nn.Parameter(torch.randn(heads, num_mem_kv, dim_head))
        self.mem_v = nn.Parameter(torch.randn(heads, num_mem_kv, dim_head))
    self.attn_on_attn = on_attn
    self.to_out = nn.Sequential(nn.Linear(inner_dim, dim * 2), nn.GLU()) if on_attn else nn.Linear(inner_dim, dim)

class AttentionLayers(nn.Module):

    def __init__(self, dim, depth, heads=8, causal=False, cross_attend=False, only_cross=False, use_scalenorm=False, use_rmsnorm=False, use_rezero=False, rel_pos_num_buckets=32, rel_pos_max_distance=128, position_infused_attn=False, custom_layers=None, sandwich_coef=None, par_ratio=None, residual_attn=False, cross_residual_attn=False, macaron=False, pre_norm=True, gate_residual=False, **kwargs):
        super().__init__()
        ff_kwargs, kwargs = groupby_prefix_and_trim('ff_', kwargs)
        attn_kwargs, _ = groupby_prefix_and_trim('attn_', kwargs)
        dim_head = attn_kwargs.get('dim_head', DEFAULT_DIM_HEAD)
        self.dim = dim
        self.depth = depth
        self.layers = nn.ModuleList([])
        self.has_pos_emb = position_infused_attn
        self.pia_pos_emb = FixedPositionalEmbedding(dim) if position_infused_attn else None
        self.rotary_pos_emb = always(None)
        assert rel_pos_num_buckets <= rel_pos_max_distance, 'number of relative position buckets must be less than the relative position max distance'
        self.rel_pos = None
        self.pre_norm = pre_norm
        self.residual_attn = residual_attn
        self.cross_residual_attn = cross_residual_attn
        norm_class = ScaleNorm if use_scalenorm else nn.LayerNorm
        norm_class = RMSNorm if use_rmsnorm else norm_class
        norm_fn = partial(norm_class, dim)
        norm_fn = nn.Identity if use_rezero else norm_fn
        branch_fn = Rezero if use_rezero else None
        if cross_attend and (not only_cross):
            default_block = ('a', 'c', 'f')
        elif cross_attend and only_cross:
            default_block = ('c', 'f')
        else:
            default_block = ('a', 'f')
        if macaron:
            default_block = ('f',) + default_block
        if exists(custom_layers):
            layer_types = custom_layers
        elif exists(par_ratio):
            par_depth = depth * len(default_block)
            assert 1 < par_ratio <= par_depth, 'par ratio out of range'
            default_block = tuple(filter(not_equals('f'), default_block))
            par_attn = par_depth // par_ratio
            depth_cut = par_depth * 2 // 3
            par_width = (depth_cut + depth_cut // par_attn) // par_attn
            assert len(default_block) <= par_width, 'default block is too large for par_ratio'
            par_block = default_block + ('f',) * (par_width - len(default_block))
            par_head = par_block * par_attn
            layer_types = par_head + ('f',) * (par_depth - len(par_head))
        elif exists(sandwich_coef):
            assert sandwich_coef > 0 and sandwich_coef <= depth, 'sandwich coefficient should be less than the depth'
            layer_types = ('a',) * sandwich_coef + default_block * (depth - sandwich_coef) + ('f',) * sandwich_coef
        else:
            layer_types = default_block * depth
        self.layer_types = layer_types
        self.num_attn_layers = len(list(filter(equals('a'), layer_types)))
        for layer_type in self.layer_types:
            if layer_type == 'a':
                layer = Attention(dim, heads=heads, causal=causal, **attn_kwargs)
            elif layer_type == 'c':
                layer = Attention(dim, heads=heads, **attn_kwargs)
            elif layer_type == 'f':
                layer = FeedForward(dim, **ff_kwargs)
                layer = layer if not macaron else Scale(0.5, layer)
            else:
                raise Exception(f'invalid layer type {layer_type}')
            if isinstance(layer, Attention) and exists(branch_fn):
                layer = branch_fn(layer)
            if gate_residual:
                residual_fn = GRUGating(dim)
            else:
                residual_fn = Residual()
            self.layers.append(nn.ModuleList([norm_fn(), layer, residual_fn]))

    def forward(self, x, context=None, mask=None, context_mask=None, mems=None, return_hiddens=False):
        hiddens = []
        intermediates = []
        prev_attn = None
        prev_cross_attn = None
        mems = mems.copy() if exists(mems) else [None] * self.num_attn_layers
        for ind, (layer_type, (norm, block, residual_fn)) in enumerate(zip(self.layer_types, self.layers)):
            is_last = ind == len(self.layers) - 1
            if layer_type == 'a':
                hiddens.append(x)
                layer_mem = mems.pop(0)
            residual = x
            if self.pre_norm:
                x = norm(x)
            if layer_type == 'a':
                out, inter = block(x, mask=mask, sinusoidal_emb=self.pia_pos_emb, rel_pos=self.rel_pos, prev_attn=prev_attn, mem=layer_mem)
            elif layer_type == 'c':
                out, inter = block(x, context=context, mask=mask, context_mask=context_mask, prev_attn=prev_cross_attn)
            elif layer_type == 'f':
                out = block(x)
            x = residual_fn(out, residual)
            if layer_type in ('a', 'c'):
                intermediates.append(inter)
            if layer_type == 'a' and self.residual_attn:
                prev_attn = inter.pre_softmax_attn
            elif layer_type == 'c' and self.cross_residual_attn:
                prev_cross_attn = inter.pre_softmax_attn
            if not self.pre_norm and (not is_last):
                x = norm(x)
        if return_hiddens:
            intermediates = LayerIntermediates(hiddens=hiddens, attn_intermediates=intermediates)
            return (x, intermediates)
        return x

def __init__(self, dim, depth, heads=8, causal=False, cross_attend=False, only_cross=False, use_scalenorm=False, use_rmsnorm=False, use_rezero=False, rel_pos_num_buckets=32, rel_pos_max_distance=128, position_infused_attn=False, custom_layers=None, sandwich_coef=None, par_ratio=None, residual_attn=False, cross_residual_attn=False, macaron=False, pre_norm=True, gate_residual=False, **kwargs):
    super().__init__()
    ff_kwargs, kwargs = groupby_prefix_and_trim('ff_', kwargs)
    attn_kwargs, _ = groupby_prefix_and_trim('attn_', kwargs)
    dim_head = attn_kwargs.get('dim_head', DEFAULT_DIM_HEAD)
    self.dim = dim
    self.depth = depth
    self.layers = nn.ModuleList([])
    self.has_pos_emb = position_infused_attn
    self.pia_pos_emb = FixedPositionalEmbedding(dim) if position_infused_attn else None
    self.rotary_pos_emb = always(None)
    assert rel_pos_num_buckets <= rel_pos_max_distance, 'number of relative position buckets must be less than the relative position max distance'
    self.rel_pos = None
    self.pre_norm = pre_norm
    self.residual_attn = residual_attn
    self.cross_residual_attn = cross_residual_attn
    norm_class = ScaleNorm if use_scalenorm else nn.LayerNorm
    norm_class = RMSNorm if use_rmsnorm else norm_class
    norm_fn = partial(norm_class, dim)
    norm_fn = nn.Identity if use_rezero else norm_fn
    branch_fn = Rezero if use_rezero else None
    if cross_attend and (not only_cross):
        default_block = ('a', 'c', 'f')
    elif cross_attend and only_cross:
        default_block = ('c', 'f')
    else:
        default_block = ('a', 'f')
    if macaron:
        default_block = ('f',) + default_block
    if exists(custom_layers):
        layer_types = custom_layers
    elif exists(par_ratio):
        par_depth = depth * len(default_block)
        assert 1 < par_ratio <= par_depth, 'par ratio out of range'
        default_block = tuple(filter(not_equals('f'), default_block))
        par_attn = par_depth // par_ratio
        depth_cut = par_depth * 2 // 3
        par_width = (depth_cut + depth_cut // par_attn) // par_attn
        assert len(default_block) <= par_width, 'default block is too large for par_ratio'
        par_block = default_block + ('f',) * (par_width - len(default_block))
        par_head = par_block * par_attn
        layer_types = par_head + ('f',) * (par_depth - len(par_head))
    elif exists(sandwich_coef):
        assert sandwich_coef > 0 and sandwich_coef <= depth, 'sandwich coefficient should be less than the depth'
        layer_types = ('a',) * sandwich_coef + default_block * (depth - sandwich_coef) + ('f',) * sandwich_coef
    else:
        layer_types = default_block * depth
    self.layer_types = layer_types
    self.num_attn_layers = len(list(filter(equals('a'), layer_types)))
    for layer_type in self.layer_types:
        if layer_type == 'a':
            layer = Attention(dim, heads=heads, causal=causal, **attn_kwargs)
        elif layer_type == 'c':
            layer = Attention(dim, heads=heads, **attn_kwargs)
        elif layer_type == 'f':
            layer = FeedForward(dim, **ff_kwargs)
            layer = layer if not macaron else Scale(0.5, layer)
        else:
            raise Exception(f'invalid layer type {layer_type}')
        if isinstance(layer, Attention) and exists(branch_fn):
            layer = branch_fn(layer)
        if gate_residual:
            residual_fn = GRUGating(dim)
        else:
            residual_fn = Residual()
        self.layers.append(nn.ModuleList([norm_fn(), layer, residual_fn]))

class Encoder(AttentionLayers):

    def __init__(self, **kwargs):
        assert 'causal' not in kwargs, 'cannot set causality on encoder'
        super().__init__(causal=False, **kwargs)

def __init__(self, **kwargs):
    assert 'causal' not in kwargs, 'cannot set causality on encoder'
    super().__init__(causal=False, **kwargs)

class TransformerWrapper(nn.Module):

    def __init__(self, *, num_tokens, max_seq_len, attn_layers, emb_dim=None, max_mem_len=0.0, emb_dropout=0.0, num_memory_tokens=None, tie_embedding=False, use_pos_emb=True):
        super().__init__()
        assert isinstance(attn_layers, AttentionLayers), 'attention layers must be one of Encoder or Decoder'
        dim = attn_layers.dim
        emb_dim = default(emb_dim, dim)
        self.max_seq_len = max_seq_len
        self.max_mem_len = max_mem_len
        self.num_tokens = num_tokens
        self.token_emb = nn.Embedding(num_tokens, emb_dim)
        self.pos_emb = AbsolutePositionalEmbedding(emb_dim, max_seq_len) if use_pos_emb and (not attn_layers.has_pos_emb) else always(0)
        self.emb_dropout = nn.Dropout(emb_dropout)
        self.project_emb = nn.Linear(emb_dim, dim) if emb_dim != dim else nn.Identity()
        self.attn_layers = attn_layers
        self.norm = nn.LayerNorm(dim)
        self.init_()
        self.to_logits = nn.Linear(dim, num_tokens) if not tie_embedding else lambda t: t @ self.token_emb.weight.t()
        num_memory_tokens = default(num_memory_tokens, 0)
        self.num_memory_tokens = num_memory_tokens
        if num_memory_tokens > 0:
            self.memory_tokens = nn.Parameter(torch.randn(num_memory_tokens, dim))
            if hasattr(attn_layers, 'num_memory_tokens'):
                attn_layers.num_memory_tokens = num_memory_tokens

    def init_(self):
        nn.init.normal_(self.token_emb.weight, std=0.02)

    def forward(self, x, return_embeddings=False, mask=None, return_mems=False, return_attn=False, mems=None, **kwargs):
        b, n, device, num_mem = (*x.shape, x.device, self.num_memory_tokens)
        x = self.token_emb(x)
        x += self.pos_emb(x)
        x = self.emb_dropout(x)
        x = self.project_emb(x)
        if num_mem > 0:
            mem = repeat(self.memory_tokens, 'n d -> b n d', b=b)
            x = torch.cat((mem, x), dim=1)
            if exists(mask):
                mask = F.pad(mask, (num_mem, 0), value=True)
        x, intermediates = self.attn_layers(x, mask=mask, mems=mems, return_hiddens=True, **kwargs)
        x = self.norm(x)
        mem, x = (x[:, :num_mem], x[:, num_mem:])
        out = self.to_logits(x) if not return_embeddings else x
        if return_mems:
            hiddens = intermediates.hiddens
            new_mems = list(map(lambda pair: torch.cat(pair, dim=-2), zip(mems, hiddens))) if exists(mems) else hiddens
            new_mems = list(map(lambda t: t[..., -self.max_mem_len:, :].detach(), new_mems))
            return (out, new_mems)
        if return_attn:
            attn_maps = list(map(lambda t: t.post_softmax_attn, intermediates.attn_intermediates))
            return (out, attn_maps)
        return out

def __init__(self, *, num_tokens, max_seq_len, attn_layers, emb_dim=None, max_mem_len=0.0, emb_dropout=0.0, num_memory_tokens=None, tie_embedding=False, use_pos_emb=True):
    super().__init__()
    assert isinstance(attn_layers, AttentionLayers), 'attention layers must be one of Encoder or Decoder'
    dim = attn_layers.dim
    emb_dim = default(emb_dim, dim)
    self.max_seq_len = max_seq_len
    self.max_mem_len = max_mem_len
    self.num_tokens = num_tokens
    self.token_emb = nn.Embedding(num_tokens, emb_dim)
    self.pos_emb = AbsolutePositionalEmbedding(emb_dim, max_seq_len) if use_pos_emb and (not attn_layers.has_pos_emb) else always(0)
    self.emb_dropout = nn.Dropout(emb_dropout)
    self.project_emb = nn.Linear(emb_dim, dim) if emb_dim != dim else nn.Identity()
    self.attn_layers = attn_layers
    self.norm = nn.LayerNorm(dim)
    self.init_()
    self.to_logits = nn.Linear(dim, num_tokens) if not tie_embedding else lambda t: t @ self.token_emb.weight.t()
    num_memory_tokens = default(num_memory_tokens, 0)
    self.num_memory_tokens = num_memory_tokens
    if num_memory_tokens > 0:
        self.memory_tokens = nn.Parameter(torch.randn(num_memory_tokens, dim))
        if hasattr(attn_layers, 'num_memory_tokens'):
            attn_layers.num_memory_tokens = num_memory_tokens

def init_(self):
    nn.init.normal_(self.token_emb.weight, std=0.02)

class GEGLU(nn.Module):

    def __init__(self, dim_in, dim_out):
        super().__init__()
        self.proj = nn.Linear(dim_in, dim_out * 2)

    def forward(self, x):
        x, gate = self.proj(x).chunk(2, dim=-1)
        return x * F.gelu(gate)

def __init__(self, dim_in, dim_out):
    super().__init__()
    self.proj = nn.Linear(dim_in, dim_out * 2)

class FeedForward(nn.Module):

    def __init__(self, dim, dim_out=None, mult=4, glu=False, dropout=0.0):
        super().__init__()
        inner_dim = int(dim * mult)
        dim_out = default(dim_out, dim)
        project_in = nn.Sequential(nn.Linear(dim, inner_dim), nn.GELU()) if not glu else GEGLU(dim, inner_dim)
        self.net = nn.Sequential(project_in, nn.Dropout(dropout), nn.Linear(inner_dim, dim_out))

    def forward(self, x):
        return self.net(x)

def __init__(self, dim, dim_out=None, mult=4, glu=False, dropout=0.0):
    super().__init__()
    inner_dim = int(dim * mult)
    dim_out = default(dim_out, dim)
    project_in = nn.Sequential(nn.Linear(dim, inner_dim), nn.GELU()) if not glu else GEGLU(dim, inner_dim)
    self.net = nn.Sequential(project_in, nn.Dropout(dropout), nn.Linear(inner_dim, dim_out))

def zero_module(module):
    """
    Zero out the parameters of a module and return it.
    """
    for p in module.parameters():
        p.detach().zero_()
    return module

class LinearAttention(nn.Module):

    def __init__(self, dim, heads=4, dim_head=32):
        super().__init__()
        self.heads = heads
        hidden_dim = dim_head * heads
        self.to_qkv = nn.Conv2d(dim, hidden_dim * 3, 1, bias=False)
        self.to_out = nn.Conv2d(hidden_dim, dim, 1)

    def forward(self, x):
        b, c, h, w = x.shape
        qkv = self.to_qkv(x)
        q, k, v = rearrange(qkv, 'b (qkv heads c) h w -> qkv b heads c (h w)', heads=self.heads, qkv=3)
        k = k.softmax(dim=-1)
        context = torch.einsum('bhdn,bhen->bhde', k, v)
        out = torch.einsum('bhde,bhdn->bhen', context, q)
        out = rearrange(out, 'b heads c (h w) -> b (heads c) h w', heads=self.heads, h=h, w=w)
        return self.to_out(out)

def __init__(self, dim, heads=4, dim_head=32):
    super().__init__()
    self.heads = heads
    hidden_dim = dim_head * heads
    self.to_qkv = nn.Conv2d(dim, hidden_dim * 3, 1, bias=False)
    self.to_out = nn.Conv2d(hidden_dim, dim, 1)

class SpatialSelfAttention(nn.Module):

    def __init__(self, in_channels):
        super().__init__()
        self.in_channels = in_channels
        self.norm = Normalize(in_channels)
        self.q = torch.nn.Conv2d(in_channels, in_channels, kernel_size=1, stride=1, padding=0)
        self.k = torch.nn.Conv2d(in_channels, in_channels, kernel_size=1, stride=1, padding=0)
        self.v = torch.nn.Conv2d(in_channels, in_channels, kernel_size=1, stride=1, padding=0)
        self.proj_out = torch.nn.Conv2d(in_channels, in_channels, kernel_size=1, stride=1, padding=0)

    def forward(self, x):
        h_ = x
        h_ = self.norm(h_)
        q = self.q(h_)
        k = self.k(h_)
        v = self.v(h_)
        b, c, h, w = q.shape
        q = rearrange(q, 'b c h w -> b (h w) c')
        k = rearrange(k, 'b c h w -> b c (h w)')
        w_ = torch.einsum('bij,bjk->bik', q, k)
        w_ = w_ * int(c) ** (-0.5)
        w_ = torch.nn.functional.softmax(w_, dim=2)
        v = rearrange(v, 'b c h w -> b c (h w)')
        w_ = rearrange(w_, 'b i j -> b j i')
        h_ = torch.einsum('bij,bjk->bik', v, w_)
        h_ = rearrange(h_, 'b c (h w) -> b c h w', h=h)
        h_ = self.proj_out(h_)
        return x + h_

def __init__(self, in_channels):
    super().__init__()
    self.in_channels = in_channels
    self.norm = Normalize(in_channels)
    self.q = torch.nn.Conv2d(in_channels, in_channels, kernel_size=1, stride=1, padding=0)
    self.k = torch.nn.Conv2d(in_channels, in_channels, kernel_size=1, stride=1, padding=0)
    self.v = torch.nn.Conv2d(in_channels, in_channels, kernel_size=1, stride=1, padding=0)
    self.proj_out = torch.nn.Conv2d(in_channels, in_channels, kernel_size=1, stride=1, padding=0)

class CrossAttention(nn.Module):

    def __init__(self, query_dim, context_dim=None, heads=8, dim_head=64, dropout=0.0):
        super().__init__()
        inner_dim = dim_head * heads
        context_dim = default(context_dim, query_dim)
        self.scale = dim_head ** (-0.5)
        self.heads = heads
        self.to_q = nn.Linear(query_dim, inner_dim, bias=False)
        self.to_k = nn.Linear(context_dim, inner_dim, bias=False)
        self.to_v = nn.Linear(context_dim, inner_dim, bias=False)
        self.to_out = nn.Sequential(nn.Linear(inner_dim, query_dim), nn.Dropout(dropout))

    def forward(self, x, context=None, mask=None):
        h = self.heads
        q = self.to_q(x)
        context = default(context, x)
        k = self.to_k(context)
        v = self.to_v(context)
        q, k, v = map(lambda t: rearrange(t, 'b n (h d) -> (b h) n d', h=h), (q, k, v))
        sim = einsum('b i d, b j d -> b i j', q, k) * self.scale
        if exists(mask):
            mask = rearrange(mask, 'b ... -> b (...)')
            max_neg_value = -torch.finfo(sim.dtype).max
            mask = repeat(mask, 'b j -> (b h) () j', h=h)
            sim.masked_fill_(~mask, max_neg_value)
        attn = sim.softmax(dim=-1)
        out = einsum('b i j, b j d -> b i d', attn, v)
        out = rearrange(out, '(b h) n d -> b n (h d)', h=h)
        return self.to_out(out)

def __init__(self, query_dim, context_dim=None, heads=8, dim_head=64, dropout=0.0):
    super().__init__()
    inner_dim = dim_head * heads
    context_dim = default(context_dim, query_dim)
    self.scale = dim_head ** (-0.5)
    self.heads = heads
    self.to_q = nn.Linear(query_dim, inner_dim, bias=False)
    self.to_k = nn.Linear(context_dim, inner_dim, bias=False)
    self.to_v = nn.Linear(context_dim, inner_dim, bias=False)
    self.to_out = nn.Sequential(nn.Linear(inner_dim, query_dim), nn.Dropout(dropout))

class BasicTransformerBlock(nn.Module):

    def __init__(self, dim, n_heads, d_head, dropout=0.0, context_dim=None, gated_ff=True, checkpoint=True):
        super().__init__()
        self.attn1 = CrossAttention(query_dim=dim, heads=n_heads, dim_head=d_head, dropout=dropout)
        self.ff = FeedForward(dim, dropout=dropout, glu=gated_ff)
        self.attn2 = CrossAttention(query_dim=dim, context_dim=context_dim, heads=n_heads, dim_head=d_head, dropout=dropout)
        self.norm1 = nn.LayerNorm(dim)
        self.norm2 = nn.LayerNorm(dim)
        self.norm3 = nn.LayerNorm(dim)
        self.checkpoint = checkpoint

    def forward(self, x, context=None):
        return checkpoint(self._forward, (x, context), self.parameters(), self.checkpoint)

    def _forward(self, x, context=None):
        x = self.attn1(self.norm1(x)) + x
        x = self.attn2(self.norm2(x), context=context) + x
        x = self.ff(self.norm3(x)) + x
        return x

def __init__(self, dim, n_heads, d_head, dropout=0.0, context_dim=None, gated_ff=True, checkpoint=True):
    super().__init__()
    self.attn1 = CrossAttention(query_dim=dim, heads=n_heads, dim_head=d_head, dropout=dropout)
    self.ff = FeedForward(dim, dropout=dropout, glu=gated_ff)
    self.attn2 = CrossAttention(query_dim=dim, context_dim=context_dim, heads=n_heads, dim_head=d_head, dropout=dropout)
    self.norm1 = nn.LayerNorm(dim)
    self.norm2 = nn.LayerNorm(dim)
    self.norm3 = nn.LayerNorm(dim)
    self.checkpoint = checkpoint

def forward(self, x, context=None):
    return checkpoint(self._forward, (x, context), self.parameters(), self.checkpoint)

class SpatialTransformer(nn.Module):
    """
    Transformer block for image-like data.
    First, project the input (aka embedding)
    and reshape to b, t, d.
    Then apply standard transformer action.
    Finally, reshape to image
    """

    def __init__(self, in_channels, n_heads, d_head, depth=1, dropout=0.0, context_dim=None):
        super().__init__()
        self.in_channels = in_channels
        inner_dim = n_heads * d_head
        self.norm = Normalize(in_channels)
        self.proj_in = nn.Conv2d(in_channels, inner_dim, kernel_size=1, stride=1, padding=0)
        self.transformer_blocks = nn.ModuleList([BasicTransformerBlock(inner_dim, n_heads, d_head, dropout=dropout, context_dim=context_dim) for d in range(depth)])
        self.proj_out = zero_module(nn.Conv2d(inner_dim, in_channels, kernel_size=1, stride=1, padding=0))

    def forward(self, x, context=None):
        b, c, h, w = x.shape
        x_in = x
        x = self.norm(x)
        x = self.proj_in(x)
        x = rearrange(x, 'b c h w -> b (h w) c')
        for block in self.transformer_blocks:
            x = block(x, context=context)
        x = rearrange(x, 'b (h w) c -> b c h w', h=h, w=w)
        x = self.proj_out(x)
        return x + x_in

def __init__(self, in_channels, n_heads, d_head, depth=1, dropout=0.0, context_dim=None):
    super().__init__()
    self.in_channels = in_channels
    inner_dim = n_heads * d_head
    self.norm = Normalize(in_channels)
    self.proj_in = nn.Conv2d(in_channels, inner_dim, kernel_size=1, stride=1, padding=0)
    self.transformer_blocks = nn.ModuleList([BasicTransformerBlock(inner_dim, n_heads, d_head, dropout=dropout, context_dim=context_dim) for d in range(depth)])
    self.proj_out = zero_module(nn.Conv2d(inner_dim, in_channels, kernel_size=1, stride=1, padding=0))

class VQLPIPSWithDiscriminator(nn.Module):

    def __init__(self, disc_start, codebook_weight=1.0, pixelloss_weight=1.0, disc_num_layers=3, disc_in_channels=3, disc_factor=1.0, disc_weight=1.0, perceptual_weight=1.0, use_actnorm=False, disc_conditional=False, disc_ndf=64, disc_loss='hinge', n_classes=None, perceptual_loss='lpips', pixel_loss='l1'):
        super().__init__()
        assert disc_loss in ['hinge', 'vanilla']
        assert perceptual_loss in ['lpips', 'clips', 'dists']
        assert pixel_loss in ['l1', 'l2']
        self.codebook_weight = codebook_weight
        self.pixel_weight = pixelloss_weight
        if perceptual_loss == 'lpips':
            print(f'{self.__class__.__name__}: Running with LPIPS.')
            self.perceptual_loss = LPIPS().eval()
        else:
            raise ValueError(f'Unknown perceptual loss: >> {perceptual_loss} <<')
        self.perceptual_weight = perceptual_weight
        if pixel_loss == 'l1':
            self.pixel_loss = l1
        else:
            self.pixel_loss = l2
        self.discriminator = NLayerDiscriminator(input_nc=disc_in_channels, n_layers=disc_num_layers, use_actnorm=use_actnorm, ndf=disc_ndf).apply(weights_init)
        self.discriminator_iter_start = disc_start
        if disc_loss == 'hinge':
            self.disc_loss = hinge_d_loss
        elif disc_loss == 'vanilla':
            self.disc_loss = vanilla_d_loss
        else:
            raise ValueError(f"Unknown GAN loss '{disc_loss}'.")
        print(f'VQLPIPSWithDiscriminator running with {disc_loss} loss.')
        self.disc_factor = disc_factor
        self.discriminator_weight = disc_weight
        self.disc_conditional = disc_conditional
        self.n_classes = n_classes

    def calculate_adaptive_weight(self, nll_loss, g_loss, last_layer=None):
        if last_layer is not None:
            nll_grads = torch.autograd.grad(nll_loss, last_layer, retain_graph=True)[0]
            g_grads = torch.autograd.grad(g_loss, last_layer, retain_graph=True)[0]
        else:
            nll_grads = torch.autograd.grad(nll_loss, self.last_layer[0], retain_graph=True)[0]
            g_grads = torch.autograd.grad(g_loss, self.last_layer[0], retain_graph=True)[0]
        d_weight = torch.norm(nll_grads) / (torch.norm(g_grads) + 0.0001)
        d_weight = torch.clamp(d_weight, 0.0, 10000.0).detach()
        d_weight = d_weight * self.discriminator_weight
        return d_weight

    def forward(self, codebook_loss, inputs, reconstructions, optimizer_idx, global_step, last_layer=None, cond=None, split='train', predicted_indices=None):
        if not exists(codebook_loss):
            codebook_loss = torch.tensor([0.0]).to(inputs.device)
        rec_loss = self.pixel_loss(inputs.contiguous(), reconstructions.contiguous())
        if self.perceptual_weight > 0:
            p_loss = self.perceptual_loss(inputs.contiguous(), reconstructions.contiguous())
            rec_loss = rec_loss + self.perceptual_weight * p_loss
        else:
            p_loss = torch.tensor([0.0])
        nll_loss = rec_loss
        nll_loss = torch.mean(nll_loss)
        if optimizer_idx == 0:
            if cond is None:
                assert not self.disc_conditional
                logits_fake = self.discriminator(reconstructions.contiguous())
            else:
                assert self.disc_conditional
                logits_fake = self.discriminator(torch.cat((reconstructions.contiguous(), cond), dim=1))
            g_loss = -torch.mean(logits_fake)
            try:
                d_weight = self.calculate_adaptive_weight(nll_loss, g_loss, last_layer=last_layer)
            except RuntimeError:
                assert not self.training
                d_weight = torch.tensor(0.0)
            disc_factor = adopt_weight(self.disc_factor, global_step, threshold=self.discriminator_iter_start)
            loss = nll_loss + d_weight * disc_factor * g_loss + self.codebook_weight * codebook_loss.mean()
            log = {'{}/total_loss'.format(split): loss.clone().detach().mean(), '{}/quant_loss'.format(split): codebook_loss.detach().mean(), '{}/nll_loss'.format(split): nll_loss.detach().mean(), '{}/rec_loss'.format(split): rec_loss.detach().mean(), '{}/p_loss'.format(split): p_loss.detach().mean(), '{}/d_weight'.format(split): d_weight.detach(), '{}/disc_factor'.format(split): torch.tensor(disc_factor), '{}/g_loss'.format(split): g_loss.detach().mean()}
            if predicted_indices is not None:
                assert self.n_classes is not None
                with torch.no_grad():
                    perplexity, cluster_usage = measure_perplexity(predicted_indices, self.n_classes)
                log[f'{split}/perplexity'] = perplexity
                log[f'{split}/cluster_usage'] = cluster_usage
            return (loss, log)
        if optimizer_idx == 1:
            if cond is None:
                logits_real = self.discriminator(inputs.contiguous().detach())
                logits_fake = self.discriminator(reconstructions.contiguous().detach())
            else:
                logits_real = self.discriminator(torch.cat((inputs.contiguous().detach(), cond), dim=1))
                logits_fake = self.discriminator(torch.cat((reconstructions.contiguous().detach(), cond), dim=1))
            disc_factor = adopt_weight(self.disc_factor, global_step, threshold=self.discriminator_iter_start)
            d_loss = disc_factor * self.disc_loss(logits_real, logits_fake)
            log = {'{}/disc_loss'.format(split): d_loss.clone().detach().mean(), '{}/logits_real'.format(split): logits_real.detach().mean(), '{}/logits_fake'.format(split): logits_fake.detach().mean()}
            return (d_loss, log)

def __init__(self, disc_start, codebook_weight=1.0, pixelloss_weight=1.0, disc_num_layers=3, disc_in_channels=3, disc_factor=1.0, disc_weight=1.0, perceptual_weight=1.0, use_actnorm=False, disc_conditional=False, disc_ndf=64, disc_loss='hinge', n_classes=None, perceptual_loss='lpips', pixel_loss='l1'):
    super().__init__()
    assert disc_loss in ['hinge', 'vanilla']
    assert perceptual_loss in ['lpips', 'clips', 'dists']
    assert pixel_loss in ['l1', 'l2']
    self.codebook_weight = codebook_weight
    self.pixel_weight = pixelloss_weight
    if perceptual_loss == 'lpips':
        print(f'{self.__class__.__name__}: Running with LPIPS.')
        self.perceptual_loss = LPIPS().eval()
    else:
        raise ValueError(f'Unknown perceptual loss: >> {perceptual_loss} <<')
    self.perceptual_weight = perceptual_weight
    if pixel_loss == 'l1':
        self.pixel_loss = l1
    else:
        self.pixel_loss = l2
    self.discriminator = NLayerDiscriminator(input_nc=disc_in_channels, n_layers=disc_num_layers, use_actnorm=use_actnorm, ndf=disc_ndf).apply(weights_init)
    self.discriminator_iter_start = disc_start
    if disc_loss == 'hinge':
        self.disc_loss = hinge_d_loss
    elif disc_loss == 'vanilla':
        self.disc_loss = vanilla_d_loss
    else:
        raise ValueError(f"Unknown GAN loss '{disc_loss}'.")
    print(f'VQLPIPSWithDiscriminator running with {disc_loss} loss.')
    self.disc_factor = disc_factor
    self.discriminator_weight = disc_weight
    self.disc_conditional = disc_conditional
    self.n_classes = n_classes

class LPIPSWithDiscriminator(nn.Module):

    def __init__(self, disc_start, logvar_init=0.0, kl_weight=1.0, pixelloss_weight=1.0, disc_num_layers=3, disc_in_channels=3, disc_factor=1.0, disc_weight=1.0, perceptual_weight=1.0, use_actnorm=False, disc_conditional=False, disc_loss='hinge'):
        super().__init__()
        assert disc_loss in ['hinge', 'vanilla']
        self.kl_weight = kl_weight
        self.pixel_weight = pixelloss_weight
        self.perceptual_loss = LPIPS().eval()
        self.perceptual_weight = perceptual_weight
        self.logvar = nn.Parameter(torch.ones(size=()) * logvar_init)
        self.discriminator = NLayerDiscriminator(input_nc=disc_in_channels, n_layers=disc_num_layers, use_actnorm=use_actnorm).apply(weights_init)
        self.discriminator_iter_start = disc_start
        self.disc_loss = hinge_d_loss if disc_loss == 'hinge' else vanilla_d_loss
        self.disc_factor = disc_factor
        self.discriminator_weight = disc_weight
        self.disc_conditional = disc_conditional

    def calculate_adaptive_weight(self, nll_loss, g_loss, last_layer=None):
        if last_layer is not None:
            nll_grads = torch.autograd.grad(nll_loss, last_layer, retain_graph=True)[0]
            g_grads = torch.autograd.grad(g_loss, last_layer, retain_graph=True)[0]
        else:
            nll_grads = torch.autograd.grad(nll_loss, self.last_layer[0], retain_graph=True)[0]
            g_grads = torch.autograd.grad(g_loss, self.last_layer[0], retain_graph=True)[0]
        d_weight = torch.norm(nll_grads) / (torch.norm(g_grads) + 0.0001)
        d_weight = torch.clamp(d_weight, 0.0, 10000.0).detach()
        d_weight = d_weight * self.discriminator_weight
        return d_weight

    def forward(self, inputs, reconstructions, posteriors, optimizer_idx, global_step, last_layer=None, cond=None, split='train', weights=None):
        rec_loss = torch.abs(inputs.contiguous() - reconstructions.contiguous())
        if self.perceptual_weight > 0:
            p_loss = self.perceptual_loss(inputs.contiguous(), reconstructions.contiguous())
            rec_loss = rec_loss + self.perceptual_weight * p_loss
        nll_loss = rec_loss / torch.exp(self.logvar) + self.logvar
        weighted_nll_loss = nll_loss
        if weights is not None:
            weighted_nll_loss = weights * nll_loss
        weighted_nll_loss = torch.sum(weighted_nll_loss) / weighted_nll_loss.shape[0]
        nll_loss = torch.sum(nll_loss) / nll_loss.shape[0]
        kl_loss = posteriors.kl()
        kl_loss = torch.sum(kl_loss) / kl_loss.shape[0]
        if optimizer_idx == 0:
            if cond is None:
                assert not self.disc_conditional
                logits_fake = self.discriminator(reconstructions.contiguous())
            else:
                assert self.disc_conditional
                logits_fake = self.discriminator(torch.cat((reconstructions.contiguous(), cond), dim=1))
            g_loss = -torch.mean(logits_fake)
            if self.disc_factor > 0.0:
                try:
                    d_weight = self.calculate_adaptive_weight(nll_loss, g_loss, last_layer=last_layer)
                except RuntimeError:
                    assert not self.training
                    d_weight = torch.tensor(0.0)
            else:
                d_weight = torch.tensor(0.0)
            disc_factor = adopt_weight(self.disc_factor, global_step, threshold=self.discriminator_iter_start)
            loss = weighted_nll_loss + self.kl_weight * kl_loss + d_weight * disc_factor * g_loss
            log = {'{}/total_loss'.format(split): loss.clone().detach().mean(), '{}/logvar'.format(split): self.logvar.detach(), '{}/kl_loss'.format(split): kl_loss.detach().mean(), '{}/nll_loss'.format(split): nll_loss.detach().mean(), '{}/rec_loss'.format(split): rec_loss.detach().mean(), '{}/d_weight'.format(split): d_weight.detach(), '{}/disc_factor'.format(split): torch.tensor(disc_factor), '{}/g_loss'.format(split): g_loss.detach().mean()}
            return (loss, log)
        if optimizer_idx == 1:
            if cond is None:
                logits_real = self.discriminator(inputs.contiguous().detach())
                logits_fake = self.discriminator(reconstructions.contiguous().detach())
            else:
                logits_real = self.discriminator(torch.cat((inputs.contiguous().detach(), cond), dim=1))
                logits_fake = self.discriminator(torch.cat((reconstructions.contiguous().detach(), cond), dim=1))
            disc_factor = adopt_weight(self.disc_factor, global_step, threshold=self.discriminator_iter_start)
            d_loss = disc_factor * self.disc_loss(logits_real, logits_fake)
            log = {'{}/disc_loss'.format(split): d_loss.clone().detach().mean(), '{}/logits_real'.format(split): logits_real.detach().mean(), '{}/logits_fake'.format(split): logits_fake.detach().mean()}
            return (d_loss, log)

def __init__(self, disc_start, logvar_init=0.0, kl_weight=1.0, pixelloss_weight=1.0, disc_num_layers=3, disc_in_channels=3, disc_factor=1.0, disc_weight=1.0, perceptual_weight=1.0, use_actnorm=False, disc_conditional=False, disc_loss='hinge'):
    super().__init__()
    assert disc_loss in ['hinge', 'vanilla']
    self.kl_weight = kl_weight
    self.pixel_weight = pixelloss_weight
    self.perceptual_loss = LPIPS().eval()
    self.perceptual_weight = perceptual_weight
    self.logvar = nn.Parameter(torch.ones(size=()) * logvar_init)
    self.discriminator = NLayerDiscriminator(input_nc=disc_in_channels, n_layers=disc_num_layers, use_actnorm=use_actnorm).apply(weights_init)
    self.discriminator_iter_start = disc_start
    self.disc_loss = hinge_d_loss if disc_loss == 'hinge' else vanilla_d_loss
    self.disc_factor = disc_factor
    self.discriminator_weight = disc_weight
    self.disc_conditional = disc_conditional

class AttentionPool2d(nn.Module):
    """
    Adapted from CLIP: https://github.com/openai/CLIP/blob/main/clip/model.py
    """

    def __init__(self, spacial_dim: int, embed_dim: int, num_heads_channels: int, output_dim: int=None):
        super().__init__()
        self.positional_embedding = nn.Parameter(th.randn(embed_dim, spacial_dim ** 2 + 1) / embed_dim ** 0.5)
        self.qkv_proj = conv_nd(1, embed_dim, 3 * embed_dim, 1)
        self.c_proj = conv_nd(1, embed_dim, output_dim or embed_dim, 1)
        self.num_heads = embed_dim // num_heads_channels
        self.attention = QKVAttention(self.num_heads)

    def forward(self, x):
        b, c, *_spatial = x.shape
        x = x.reshape(b, c, -1)
        x = th.cat([x.mean(dim=-1, keepdim=True), x], dim=-1)
        x = x + self.positional_embedding[None, :, :].to(x.dtype)
        x = self.qkv_proj(x)
        x = self.attention(x)
        x = self.c_proj(x)
        return x[:, :, 0]

def __init__(self, spacial_dim: int, embed_dim: int, num_heads_channels: int, output_dim: int=None):
    super().__init__()
    self.positional_embedding = nn.Parameter(th.randn(embed_dim, spacial_dim ** 2 + 1) / embed_dim ** 0.5)
    self.qkv_proj = conv_nd(1, embed_dim, 3 * embed_dim, 1)
    self.c_proj = conv_nd(1, embed_dim, output_dim or embed_dim, 1)
    self.num_heads = embed_dim // num_heads_channels
    self.attention = QKVAttention(self.num_heads)

class Upsample(nn.Module):
    """
    An upsampling layer with an optional convolution.
    :param channels: channels in the inputs and outputs.
    :param use_conv: a bool determining if a convolution is applied.
    :param dims: determines if the signal is 1D, 2D, or 3D. If 3D, then
                 upsampling occurs in the inner-two dimensions.
    """

    def __init__(self, channels, use_conv, dims=2, out_channels=None, padding=1):
        super().__init__()
        self.channels = channels
        self.out_channels = out_channels or channels
        self.use_conv = use_conv
        self.dims = dims
        if use_conv:
            self.conv = conv_nd(dims, self.channels, self.out_channels, 3, padding=padding)

    def forward(self, x):
        assert x.shape[1] == self.channels
        if self.dims == 3:
            x = F.interpolate(x, (x.shape[2], x.shape[3] * 2, x.shape[4] * 2), mode='nearest')
        else:
            x = F.interpolate(x, scale_factor=2, mode='nearest')
        if self.use_conv:
            x = self.conv(x)
        return x

def __init__(self, channels, use_conv, dims=2, out_channels=None, padding=1):
    super().__init__()
    self.channels = channels
    self.out_channels = out_channels or channels
    self.use_conv = use_conv
    self.dims = dims
    if use_conv:
        self.conv = conv_nd(dims, self.channels, self.out_channels, 3, padding=padding)

class TransposedUpsample(nn.Module):
    """Learned 2x upsampling without padding"""

    def __init__(self, channels, out_channels=None, ks=5):
        super().__init__()
        self.channels = channels
        self.out_channels = out_channels or channels
        self.up = nn.ConvTranspose2d(self.channels, self.out_channels, kernel_size=ks, stride=2)

    def forward(self, x):
        return self.up(x)

def __init__(self, channels, out_channels=None, ks=5):
    super().__init__()
    self.channels = channels
    self.out_channels = out_channels or channels
    self.up = nn.ConvTranspose2d(self.channels, self.out_channels, kernel_size=ks, stride=2)

class Downsample(nn.Module):
    """
    A downsampling layer with an optional convolution.
    :param channels: channels in the inputs and outputs.
    :param use_conv: a bool determining if a convolution is applied.
    :param dims: determines if the signal is 1D, 2D, or 3D. If 3D, then
                 downsampling occurs in the inner-two dimensions.
    """

    def __init__(self, channels, use_conv, dims=2, out_channels=None, padding=1):
        super().__init__()
        self.channels = channels
        self.out_channels = out_channels or channels
        self.use_conv = use_conv
        self.dims = dims
        stride = 2 if dims != 3 else (1, 2, 2)
        if use_conv:
            self.op = conv_nd(dims, self.channels, self.out_channels, 3, stride=stride, padding=padding)
        else:
            assert self.channels == self.out_channels
            self.op = avg_pool_nd(dims, kernel_size=stride, stride=stride)

    def forward(self, x):
        assert x.shape[1] == self.channels
        return self.op(x)

def __init__(self, channels, use_conv, dims=2, out_channels=None, padding=1):
    super().__init__()
    self.channels = channels
    self.out_channels = out_channels or channels
    self.use_conv = use_conv
    self.dims = dims
    stride = 2 if dims != 3 else (1, 2, 2)
    if use_conv:
        self.op = conv_nd(dims, self.channels, self.out_channels, 3, stride=stride, padding=padding)
    else:
        assert self.channels == self.out_channels
        self.op = avg_pool_nd(dims, kernel_size=stride, stride=stride)

class ResBlock(TimestepBlock):
    """
    A residual block that can optionally change the number of channels.
    :param channels: the number of input channels.
    :param emb_channels: the number of timestep embedding channels.
    :param dropout: the rate of dropout.
    :param out_channels: if specified, the number of out channels.
    :param use_conv: if True and out_channels is specified, use a spatial
        convolution instead of a smaller 1x1 convolution to change the
        channels in the skip connection.
    :param dims: determines if the signal is 1D, 2D, or 3D.
    :param use_checkpoint: if True, use gradient checkpointing on this module.
    :param up: if True, use this block for upsampling.
    :param down: if True, use this block for downsampling.
    """

    def __init__(self, channels, emb_channels, dropout, out_channels=None, use_conv=False, use_scale_shift_norm=False, dims=2, use_checkpoint=False, up=False, down=False):
        super().__init__()
        self.channels = channels
        self.emb_channels = emb_channels
        self.dropout = dropout
        self.out_channels = out_channels or channels
        self.use_conv = use_conv
        self.use_checkpoint = use_checkpoint
        self.use_scale_shift_norm = use_scale_shift_norm
        self.in_layers = nn.Sequential(normalization(channels), nn.SiLU(), conv_nd(dims, channels, self.out_channels, 3, padding=1))
        self.updown = up or down
        if up:
            self.h_upd = Upsample(channels, False, dims)
            self.x_upd = Upsample(channels, False, dims)
        elif down:
            self.h_upd = Downsample(channels, False, dims)
            self.x_upd = Downsample(channels, False, dims)
        else:
            self.h_upd = self.x_upd = nn.Identity()
        self.emb_layers = nn.Sequential(nn.SiLU(), linear(emb_channels, 2 * self.out_channels if use_scale_shift_norm else self.out_channels))
        self.out_layers = nn.Sequential(normalization(self.out_channels), nn.SiLU(), nn.Dropout(p=dropout), zero_module(conv_nd(dims, self.out_channels, self.out_channels, 3, padding=1)))
        if self.out_channels == channels:
            self.skip_connection = nn.Identity()
        elif use_conv:
            self.skip_connection = conv_nd(dims, channels, self.out_channels, 3, padding=1)
        else:
            self.skip_connection = conv_nd(dims, channels, self.out_channels, 1)

    def forward(self, x, emb):
        """
        Apply the block to a Tensor, conditioned on a timestep embedding.
        :param x: an [N x C x ...] Tensor of features.
        :param emb: an [N x emb_channels] Tensor of timestep embeddings.
        :return: an [N x C x ...] Tensor of outputs.
        """
        return checkpoint(self._forward, (x, emb), self.parameters(), self.use_checkpoint)

    def _forward(self, x, emb):
        if self.updown:
            in_rest, in_conv = (self.in_layers[:-1], self.in_layers[-1])
            h = in_rest(x)
            h = self.h_upd(h)
            x = self.x_upd(x)
            h = in_conv(h)
        else:
            h = self.in_layers(x)
        emb_out = self.emb_layers(emb).type(h.dtype)
        while len(emb_out.shape) < len(h.shape):
            emb_out = emb_out[..., None]
        if self.use_scale_shift_norm:
            out_norm, out_rest = (self.out_layers[0], self.out_layers[1:])
            scale, shift = th.chunk(emb_out, 2, dim=1)
            h = out_norm(h) * (1 + scale) + shift
            h = out_rest(h)
        else:
            h = h + emb_out
            h = self.out_layers(h)
        return self.skip_connection(x) + h

def __init__(self, channels, emb_channels, dropout, out_channels=None, use_conv=False, use_scale_shift_norm=False, dims=2, use_checkpoint=False, up=False, down=False):
    super().__init__()
    self.channels = channels
    self.emb_channels = emb_channels
    self.dropout = dropout
    self.out_channels = out_channels or channels
    self.use_conv = use_conv
    self.use_checkpoint = use_checkpoint
    self.use_scale_shift_norm = use_scale_shift_norm
    self.in_layers = nn.Sequential(normalization(channels), nn.SiLU(), conv_nd(dims, channels, self.out_channels, 3, padding=1))
    self.updown = up or down
    if up:
        self.h_upd = Upsample(channels, False, dims)
        self.x_upd = Upsample(channels, False, dims)
    elif down:
        self.h_upd = Downsample(channels, False, dims)
        self.x_upd = Downsample(channels, False, dims)
    else:
        self.h_upd = self.x_upd = nn.Identity()
    self.emb_layers = nn.Sequential(nn.SiLU(), linear(emb_channels, 2 * self.out_channels if use_scale_shift_norm else self.out_channels))
    self.out_layers = nn.Sequential(normalization(self.out_channels), nn.SiLU(), nn.Dropout(p=dropout), zero_module(conv_nd(dims, self.out_channels, self.out_channels, 3, padding=1)))
    if self.out_channels == channels:
        self.skip_connection = nn.Identity()
    elif use_conv:
        self.skip_connection = conv_nd(dims, channels, self.out_channels, 3, padding=1)
    else:
        self.skip_connection = conv_nd(dims, channels, self.out_channels, 1)

def forward(self, x, emb):
    """
        Apply the block to a Tensor, conditioned on a timestep embedding.
        :param x: an [N x C x ...] Tensor of features.
        :param emb: an [N x emb_channels] Tensor of timestep embeddings.
        :return: an [N x C x ...] Tensor of outputs.
        """
    return checkpoint(self._forward, (x, emb), self.parameters(), self.use_checkpoint)

class AttentionBlock(nn.Module):
    """
    An attention block that allows spatial positions to attend to each other.
    Originally ported from here, but adapted to the N-d case.
    https://github.com/hojonathanho/diffusion/blob/1e0dceb3b3495bbe19116a5e1b3596cd0706c543/diffusion_tf/models/unet.py#L66.
    """

    def __init__(self, channels, num_heads=1, num_head_channels=-1, use_checkpoint=False, use_new_attention_order=False):
        super().__init__()
        self.channels = channels
        if num_head_channels == -1:
            self.num_heads = num_heads
        else:
            assert channels % num_head_channels == 0, f'q,k,v channels {channels} is not divisible by num_head_channels {num_head_channels}'
            self.num_heads = channels // num_head_channels
        self.use_checkpoint = use_checkpoint
        self.norm = normalization(channels)
        self.qkv = conv_nd(1, channels, channels * 3, 1)
        if use_new_attention_order:
            self.attention = QKVAttention(self.num_heads)
        else:
            self.attention = QKVAttentionLegacy(self.num_heads)
        self.proj_out = zero_module(conv_nd(1, channels, channels, 1))

    def forward(self, x):
        return checkpoint(self._forward, (x,), self.parameters(), True)

    def _forward(self, x):
        b, c, *spatial = x.shape
        x = x.reshape(b, c, -1)
        qkv = self.qkv(self.norm(x))
        h = self.attention(qkv)
        h = self.proj_out(h)
        return (x + h).reshape(b, c, *spatial)

def __init__(self, channels, num_heads=1, num_head_channels=-1, use_checkpoint=False, use_new_attention_order=False):
    super().__init__()
    self.channels = channels
    if num_head_channels == -1:
        self.num_heads = num_heads
    else:
        assert channels % num_head_channels == 0, f'q,k,v channels {channels} is not divisible by num_head_channels {num_head_channels}'
        self.num_heads = channels // num_head_channels
    self.use_checkpoint = use_checkpoint
    self.norm = normalization(channels)
    self.qkv = conv_nd(1, channels, channels * 3, 1)
    if use_new_attention_order:
        self.attention = QKVAttention(self.num_heads)
    else:
        self.attention = QKVAttentionLegacy(self.num_heads)
    self.proj_out = zero_module(conv_nd(1, channels, channels, 1))

def forward(self, x):
    return checkpoint(self._forward, (x,), self.parameters(), True)

class QKVAttentionLegacy(nn.Module):
    """
    A module which performs QKV attention. Matches legacy QKVAttention + input/ouput heads shaping
    """

    def __init__(self, n_heads):
        super().__init__()
        self.n_heads = n_heads

    def forward(self, qkv):
        """
        Apply QKV attention.
        :param qkv: an [N x (H * 3 * C) x T] tensor of Qs, Ks, and Vs.
        :return: an [N x (H * C) x T] tensor after attention.
        """
        bs, width, length = qkv.shape
        assert width % (3 * self.n_heads) == 0
        ch = width // (3 * self.n_heads)
        q, k, v = qkv.reshape(bs * self.n_heads, ch * 3, length).split(ch, dim=1)
        scale = 1 / math.sqrt(math.sqrt(ch))
        weight = th.einsum('bct,bcs->bts', q * scale, k * scale)
        weight = th.softmax(weight.float(), dim=-1).type(weight.dtype)
        a = th.einsum('bts,bcs->bct', weight, v)
        return a.reshape(bs, -1, length)

    @staticmethod
    def count_flops(model, _x, y):
        return count_flops_attn(model, _x, y)

def __init__(self, n_heads):
    super().__init__()
    self.n_heads = n_heads

class QKVAttention(nn.Module):
    """
    A module which performs QKV attention and splits in a different order.
    """

    def __init__(self, n_heads):
        super().__init__()
        self.n_heads = n_heads

    def forward(self, qkv):
        """
        Apply QKV attention.
        :param qkv: an [N x (3 * H * C) x T] tensor of Qs, Ks, and Vs.
        :return: an [N x (H * C) x T] tensor after attention.
        """
        bs, width, length = qkv.shape
        assert width % (3 * self.n_heads) == 0
        ch = width // (3 * self.n_heads)
        q, k, v = qkv.chunk(3, dim=1)
        scale = 1 / math.sqrt(math.sqrt(ch))
        weight = th.einsum('bct,bcs->bts', (q * scale).view(bs * self.n_heads, ch, length), (k * scale).view(bs * self.n_heads, ch, length))
        weight = th.softmax(weight.float(), dim=-1).type(weight.dtype)
        a = th.einsum('bts,bcs->bct', weight, v.reshape(bs * self.n_heads, ch, length))
        return a.reshape(bs, -1, length)

    @staticmethod
    def count_flops(model, _x, y):
        return count_flops_attn(model, _x, y)

def __init__(self, n_heads):
    super().__init__()
    self.n_heads = n_heads

class UNetModel(nn.Module):
    """
    The full UNet model with attention and timestep embedding.
    :param in_channels: channels in the input Tensor.
    :param model_channels: base channel count for the model.
    :param out_channels: channels in the output Tensor.
    :param num_res_blocks: number of residual blocks per downsample.
    :param attention_resolutions: a collection of downsample rates at which
        attention will take place. May be a set, list, or tuple.
        For example, if this contains 4, then at 4x downsampling, attention
        will be used.
    :param dropout: the dropout probability.
    :param channel_mult: channel multiplier for each level of the UNet.
    :param conv_resample: if True, use learned convolutions for upsampling and
        downsampling.
    :param dims: determines if the signal is 1D, 2D, or 3D.
    :param num_classes: if specified (as an int), then this model will be
        class-conditional with `num_classes` classes.
    :param use_checkpoint: use gradient checkpointing to reduce memory usage.
    :param num_heads: the number of attention heads in each attention layer.
    :param num_heads_channels: if specified, ignore num_heads and instead use
                               a fixed channel width per attention head.
    :param num_heads_upsample: works with num_heads to set a different number
                               of heads for upsampling. Deprecated.
    :param use_scale_shift_norm: use a FiLM-like conditioning mechanism.
    :param resblock_updown: use residual blocks for up/downsampling.
    :param use_new_attention_order: use a different attention pattern for potentially
                                    increased efficiency.
    """

    def __init__(self, image_size, in_channels, model_channels, out_channels, num_res_blocks, attention_resolutions, dropout=0, channel_mult=(1, 2, 4, 8), conv_resample=True, dims=2, num_classes=None, use_checkpoint=False, use_fp16=False, num_heads=-1, num_head_channels=-1, num_heads_upsample=-1, use_scale_shift_norm=False, resblock_updown=False, use_new_attention_order=False, use_spatial_transformer=False, transformer_depth=1, context_dim=None, n_embed=None, legacy=True):
        super().__init__()
        if use_spatial_transformer:
            assert context_dim is not None, 'Fool!! You forgot to include the dimension of your cross-attention conditioning...'
        if context_dim is not None:
            assert use_spatial_transformer, 'Fool!! You forgot to use the spatial transformer for your cross-attention conditioning...'
            from omegaconf.listconfig import ListConfig
            if type(context_dim) == ListConfig:
                context_dim = list(context_dim)
        if num_heads_upsample == -1:
            num_heads_upsample = num_heads
        if num_heads == -1:
            assert num_head_channels != -1, 'Either num_heads or num_head_channels has to be set'
        if num_head_channels == -1:
            assert num_heads != -1, 'Either num_heads or num_head_channels has to be set'
        self.image_size = image_size
        self.in_channels = in_channels
        self.model_channels = model_channels
        self.out_channels = out_channels
        self.num_res_blocks = num_res_blocks
        self.attention_resolutions = attention_resolutions
        self.dropout = dropout
        self.channel_mult = channel_mult
        self.conv_resample = conv_resample
        self.num_classes = num_classes
        self.use_checkpoint = use_checkpoint
        self.dtype = th.float16 if use_fp16 else th.float32
        self.num_heads = num_heads
        self.num_head_channels = num_head_channels
        self.num_heads_upsample = num_heads_upsample
        self.predict_codebook_ids = n_embed is not None
        time_embed_dim = model_channels * 4
        self.time_embed = nn.Sequential(linear(model_channels, time_embed_dim), nn.SiLU(), linear(time_embed_dim, time_embed_dim))
        if self.num_classes is not None:
            self.label_emb = nn.Embedding(num_classes, time_embed_dim)
        self.input_blocks = nn.ModuleList([TimestepEmbedSequential(conv_nd(dims, in_channels, model_channels, 3, padding=1))])
        self._feature_size = model_channels
        input_block_chans = [model_channels]
        ch = model_channels
        ds = 1
        for level, mult in enumerate(channel_mult):
            for _ in range(num_res_blocks):
                layers = [ResBlock(ch, time_embed_dim, dropout, out_channels=mult * model_channels, dims=dims, use_checkpoint=use_checkpoint, use_scale_shift_norm=use_scale_shift_norm)]
                ch = mult * model_channels
                if ds in attention_resolutions:
                    if num_head_channels == -1:
                        dim_head = ch // num_heads
                    else:
                        num_heads = ch // num_head_channels
                        dim_head = num_head_channels
                    if legacy:
                        dim_head = ch // num_heads if use_spatial_transformer else num_head_channels
                    layers.append(AttentionBlock(ch, use_checkpoint=use_checkpoint, num_heads=num_heads, num_head_channels=dim_head, use_new_attention_order=use_new_attention_order) if not use_spatial_transformer else SpatialTransformer(ch, num_heads, dim_head, depth=transformer_depth, context_dim=context_dim))
                self.input_blocks.append(TimestepEmbedSequential(*layers))
                self._feature_size += ch
                input_block_chans.append(ch)
            if level != len(channel_mult) - 1:
                out_ch = ch
                self.input_blocks.append(TimestepEmbedSequential(ResBlock(ch, time_embed_dim, dropout, out_channels=out_ch, dims=dims, use_checkpoint=use_checkpoint, use_scale_shift_norm=use_scale_shift_norm, down=True) if resblock_updown else Downsample(ch, conv_resample, dims=dims, out_channels=out_ch)))
                ch = out_ch
                input_block_chans.append(ch)
                ds *= 2
                self._feature_size += ch
        if num_head_channels == -1:
            dim_head = ch // num_heads
        else:
            num_heads = ch // num_head_channels
            dim_head = num_head_channels
        if legacy:
            dim_head = ch // num_heads if use_spatial_transformer else num_head_channels
        self.middle_block = TimestepEmbedSequential(ResBlock(ch, time_embed_dim, dropout, dims=dims, use_checkpoint=use_checkpoint, use_scale_shift_norm=use_scale_shift_norm), AttentionBlock(ch, use_checkpoint=use_checkpoint, num_heads=num_heads, num_head_channels=dim_head, use_new_attention_order=use_new_attention_order) if not use_spatial_transformer else SpatialTransformer(ch, num_heads, dim_head, depth=transformer_depth, context_dim=context_dim), ResBlock(ch, time_embed_dim, dropout, dims=dims, use_checkpoint=use_checkpoint, use_scale_shift_norm=use_scale_shift_norm))
        self._feature_size += ch
        self.output_blocks = nn.ModuleList([])
        for level, mult in list(enumerate(channel_mult))[::-1]:
            for i in range(num_res_blocks + 1):
                ich = input_block_chans.pop()
                layers = [ResBlock(ch + ich, time_embed_dim, dropout, out_channels=model_channels * mult, dims=dims, use_checkpoint=use_checkpoint, use_scale_shift_norm=use_scale_shift_norm)]
                ch = model_channels * mult
                if ds in attention_resolutions:
                    if num_head_channels == -1:
                        dim_head = ch // num_heads
                    else:
                        num_heads = ch // num_head_channels
                        dim_head = num_head_channels
                    if legacy:
                        dim_head = ch // num_heads if use_spatial_transformer else num_head_channels
                    layers.append(AttentionBlock(ch, use_checkpoint=use_checkpoint, num_heads=num_heads_upsample, num_head_channels=dim_head, use_new_attention_order=use_new_attention_order) if not use_spatial_transformer else SpatialTransformer(ch, num_heads, dim_head, depth=transformer_depth, context_dim=context_dim))
                if level and i == num_res_blocks:
                    out_ch = ch
                    layers.append(ResBlock(ch, time_embed_dim, dropout, out_channels=out_ch, dims=dims, use_checkpoint=use_checkpoint, use_scale_shift_norm=use_scale_shift_norm, up=True) if resblock_updown else Upsample(ch, conv_resample, dims=dims, out_channels=out_ch))
                    ds //= 2
                self.output_blocks.append(TimestepEmbedSequential(*layers))
                self._feature_size += ch
        self.out = nn.Sequential(normalization(ch), nn.SiLU(), zero_module(conv_nd(dims, model_channels, out_channels, 3, padding=1)))
        if self.predict_codebook_ids:
            self.id_predictor = nn.Sequential(normalization(ch), conv_nd(dims, model_channels, n_embed, 1))

    def convert_to_fp16(self):
        """
        Convert the torso of the model to float16.
        """
        self.input_blocks.apply(convert_module_to_f16)
        self.middle_block.apply(convert_module_to_f16)
        self.output_blocks.apply(convert_module_to_f16)

    def convert_to_fp32(self):
        """
        Convert the torso of the model to float32.
        """
        self.input_blocks.apply(convert_module_to_f32)
        self.middle_block.apply(convert_module_to_f32)
        self.output_blocks.apply(convert_module_to_f32)

    def forward(self, x, timesteps=None, context=None, y=None, **kwargs):
        """
        Apply the model to an input batch.
        :param x: an [N x C x ...] Tensor of inputs.
        :param timesteps: a 1-D batch of timesteps.
        :param context: conditioning plugged in via crossattn
        :param y: an [N] Tensor of labels, if class-conditional.
        :return: an [N x C x ...] Tensor of outputs.
        """
        assert (y is not None) == (self.num_classes is not None), 'must specify y if and only if the model is class-conditional'
        hs = []
        t_emb = timestep_embedding(timesteps, self.model_channels, repeat_only=False)
        emb = self.time_embed(t_emb)
        if self.num_classes is not None:
            assert y.shape == (x.shape[0],)
            emb = emb + self.label_emb(y)
        h = x.type(self.dtype)
        for module in self.input_blocks:
            h = module(h, emb, context)
            hs.append(h)
        h = self.middle_block(h, emb, context)
        for module in self.output_blocks:
            h = th.cat([h, hs.pop()], dim=1)
            h = module(h, emb, context)
        h = h.type(x.dtype)
        if self.predict_codebook_ids:
            return self.id_predictor(h)
        else:
            return self.out(h)

def __init__(self, image_size, in_channels, model_channels, out_channels, num_res_blocks, attention_resolutions, dropout=0, channel_mult=(1, 2, 4, 8), conv_resample=True, dims=2, num_classes=None, use_checkpoint=False, use_fp16=False, num_heads=-1, num_head_channels=-1, num_heads_upsample=-1, use_scale_shift_norm=False, resblock_updown=False, use_new_attention_order=False, use_spatial_transformer=False, transformer_depth=1, context_dim=None, n_embed=None, legacy=True):
    super().__init__()
    if use_spatial_transformer:
        assert context_dim is not None, 'Fool!! You forgot to include the dimension of your cross-attention conditioning...'
    if context_dim is not None:
        assert use_spatial_transformer, 'Fool!! You forgot to use the spatial transformer for your cross-attention conditioning...'
        from omegaconf.listconfig import ListConfig
        if type(context_dim) == ListConfig:
            context_dim = list(context_dim)
    if num_heads_upsample == -1:
        num_heads_upsample = num_heads
    if num_heads == -1:
        assert num_head_channels != -1, 'Either num_heads or num_head_channels has to be set'
    if num_head_channels == -1:
        assert num_heads != -1, 'Either num_heads or num_head_channels has to be set'
    self.image_size = image_size
    self.in_channels = in_channels
    self.model_channels = model_channels
    self.out_channels = out_channels
    self.num_res_blocks = num_res_blocks
    self.attention_resolutions = attention_resolutions
    self.dropout = dropout
    self.channel_mult = channel_mult
    self.conv_resample = conv_resample
    self.num_classes = num_classes
    self.use_checkpoint = use_checkpoint
    self.dtype = th.float16 if use_fp16 else th.float32
    self.num_heads = num_heads
    self.num_head_channels = num_head_channels
    self.num_heads_upsample = num_heads_upsample
    self.predict_codebook_ids = n_embed is not None
    time_embed_dim = model_channels * 4
    self.time_embed = nn.Sequential(linear(model_channels, time_embed_dim), nn.SiLU(), linear(time_embed_dim, time_embed_dim))
    if self.num_classes is not None:
        self.label_emb = nn.Embedding(num_classes, time_embed_dim)
    self.input_blocks = nn.ModuleList([TimestepEmbedSequential(conv_nd(dims, in_channels, model_channels, 3, padding=1))])
    self._feature_size = model_channels
    input_block_chans = [model_channels]
    ch = model_channels
    ds = 1
    for level, mult in enumerate(channel_mult):
        for _ in range(num_res_blocks):
            layers = [ResBlock(ch, time_embed_dim, dropout, out_channels=mult * model_channels, dims=dims, use_checkpoint=use_checkpoint, use_scale_shift_norm=use_scale_shift_norm)]
            ch = mult * model_channels
            if ds in attention_resolutions:
                if num_head_channels == -1:
                    dim_head = ch // num_heads
                else:
                    num_heads = ch // num_head_channels
                    dim_head = num_head_channels
                if legacy:
                    dim_head = ch // num_heads if use_spatial_transformer else num_head_channels
                layers.append(AttentionBlock(ch, use_checkpoint=use_checkpoint, num_heads=num_heads, num_head_channels=dim_head, use_new_attention_order=use_new_attention_order) if not use_spatial_transformer else SpatialTransformer(ch, num_heads, dim_head, depth=transformer_depth, context_dim=context_dim))
            self.input_blocks.append(TimestepEmbedSequential(*layers))
            self._feature_size += ch
            input_block_chans.append(ch)
        if level != len(channel_mult) - 1:
            out_ch = ch
            self.input_blocks.append(TimestepEmbedSequential(ResBlock(ch, time_embed_dim, dropout, out_channels=out_ch, dims=dims, use_checkpoint=use_checkpoint, use_scale_shift_norm=use_scale_shift_norm, down=True) if resblock_updown else Downsample(ch, conv_resample, dims=dims, out_channels=out_ch)))
            ch = out_ch
            input_block_chans.append(ch)
            ds *= 2
            self._feature_size += ch
    if num_head_channels == -1:
        dim_head = ch // num_heads
    else:
        num_heads = ch // num_head_channels
        dim_head = num_head_channels
    if legacy:
        dim_head = ch // num_heads if use_spatial_transformer else num_head_channels
    self.middle_block = TimestepEmbedSequential(ResBlock(ch, time_embed_dim, dropout, dims=dims, use_checkpoint=use_checkpoint, use_scale_shift_norm=use_scale_shift_norm), AttentionBlock(ch, use_checkpoint=use_checkpoint, num_heads=num_heads, num_head_channels=dim_head, use_new_attention_order=use_new_attention_order) if not use_spatial_transformer else SpatialTransformer(ch, num_heads, dim_head, depth=transformer_depth, context_dim=context_dim), ResBlock(ch, time_embed_dim, dropout, dims=dims, use_checkpoint=use_checkpoint, use_scale_shift_norm=use_scale_shift_norm))
    self._feature_size += ch
    self.output_blocks = nn.ModuleList([])
    for level, mult in list(enumerate(channel_mult))[::-1]:
        for i in range(num_res_blocks + 1):
            ich = input_block_chans.pop()
            layers = [ResBlock(ch + ich, time_embed_dim, dropout, out_channels=model_channels * mult, dims=dims, use_checkpoint=use_checkpoint, use_scale_shift_norm=use_scale_shift_norm)]
            ch = model_channels * mult
            if ds in attention_resolutions:
                if num_head_channels == -1:
                    dim_head = ch // num_heads
                else:
                    num_heads = ch // num_head_channels
                    dim_head = num_head_channels
                if legacy:
                    dim_head = ch // num_heads if use_spatial_transformer else num_head_channels
                layers.append(AttentionBlock(ch, use_checkpoint=use_checkpoint, num_heads=num_heads_upsample, num_head_channels=dim_head, use_new_attention_order=use_new_attention_order) if not use_spatial_transformer else SpatialTransformer(ch, num_heads, dim_head, depth=transformer_depth, context_dim=context_dim))
            if level and i == num_res_blocks:
                out_ch = ch
                layers.append(ResBlock(ch, time_embed_dim, dropout, out_channels=out_ch, dims=dims, use_checkpoint=use_checkpoint, use_scale_shift_norm=use_scale_shift_norm, up=True) if resblock_updown else Upsample(ch, conv_resample, dims=dims, out_channels=out_ch))
                ds //= 2
            self.output_blocks.append(TimestepEmbedSequential(*layers))
            self._feature_size += ch
    self.out = nn.Sequential(normalization(ch), nn.SiLU(), zero_module(conv_nd(dims, model_channels, out_channels, 3, padding=1)))
    if self.predict_codebook_ids:
        self.id_predictor = nn.Sequential(normalization(ch), conv_nd(dims, model_channels, n_embed, 1))

class EncoderUNetModel(nn.Module):
    """
    The half UNet model with attention and timestep embedding.
    For usage, see UNet.
    """

    def __init__(self, image_size, in_channels, model_channels, out_channels, num_res_blocks, attention_resolutions, dropout=0, channel_mult=(1, 2, 4, 8), conv_resample=True, dims=2, use_checkpoint=False, use_fp16=False, num_heads=1, num_head_channels=-1, num_heads_upsample=-1, use_scale_shift_norm=False, resblock_updown=False, use_new_attention_order=False, pool='adaptive', *args, **kwargs):
        super().__init__()
        if num_heads_upsample == -1:
            num_heads_upsample = num_heads
        self.in_channels = in_channels
        self.model_channels = model_channels
        self.out_channels = out_channels
        self.num_res_blocks = num_res_blocks
        self.attention_resolutions = attention_resolutions
        self.dropout = dropout
        self.channel_mult = channel_mult
        self.conv_resample = conv_resample
        self.use_checkpoint = use_checkpoint
        self.dtype = th.float16 if use_fp16 else th.float32
        self.num_heads = num_heads
        self.num_head_channels = num_head_channels
        self.num_heads_upsample = num_heads_upsample
        time_embed_dim = model_channels * 4
        self.time_embed = nn.Sequential(linear(model_channels, time_embed_dim), nn.SiLU(), linear(time_embed_dim, time_embed_dim))
        self.input_blocks = nn.ModuleList([TimestepEmbedSequential(conv_nd(dims, in_channels, model_channels, 3, padding=1))])
        self._feature_size = model_channels
        input_block_chans = [model_channels]
        ch = model_channels
        ds = 1
        for level, mult in enumerate(channel_mult):
            for _ in range(num_res_blocks):
                layers = [ResBlock(ch, time_embed_dim, dropout, out_channels=mult * model_channels, dims=dims, use_checkpoint=use_checkpoint, use_scale_shift_norm=use_scale_shift_norm)]
                ch = mult * model_channels
                if ds in attention_resolutions:
                    layers.append(AttentionBlock(ch, use_checkpoint=use_checkpoint, num_heads=num_heads, num_head_channels=num_head_channels, use_new_attention_order=use_new_attention_order))
                self.input_blocks.append(TimestepEmbedSequential(*layers))
                self._feature_size += ch
                input_block_chans.append(ch)
            if level != len(channel_mult) - 1:
                out_ch = ch
                self.input_blocks.append(TimestepEmbedSequential(ResBlock(ch, time_embed_dim, dropout, out_channels=out_ch, dims=dims, use_checkpoint=use_checkpoint, use_scale_shift_norm=use_scale_shift_norm, down=True) if resblock_updown else Downsample(ch, conv_resample, dims=dims, out_channels=out_ch)))
                ch = out_ch
                input_block_chans.append(ch)
                ds *= 2
                self._feature_size += ch
        self.middle_block = TimestepEmbedSequential(ResBlock(ch, time_embed_dim, dropout, dims=dims, use_checkpoint=use_checkpoint, use_scale_shift_norm=use_scale_shift_norm), AttentionBlock(ch, use_checkpoint=use_checkpoint, num_heads=num_heads, num_head_channels=num_head_channels, use_new_attention_order=use_new_attention_order), ResBlock(ch, time_embed_dim, dropout, dims=dims, use_checkpoint=use_checkpoint, use_scale_shift_norm=use_scale_shift_norm))
        self._feature_size += ch
        self.pool = pool
        if pool == 'adaptive':
            self.out = nn.Sequential(normalization(ch), nn.SiLU(), nn.AdaptiveAvgPool2d((1, 1)), zero_module(conv_nd(dims, ch, out_channels, 1)), nn.Flatten())
        elif pool == 'attention':
            assert num_head_channels != -1
            self.out = nn.Sequential(normalization(ch), nn.SiLU(), AttentionPool2d(image_size // ds, ch, num_head_channels, out_channels))
        elif pool == 'spatial':
            self.out = nn.Sequential(nn.Linear(self._feature_size, 2048), nn.ReLU(), nn.Linear(2048, self.out_channels))
        elif pool == 'spatial_v2':
            self.out = nn.Sequential(nn.Linear(self._feature_size, 2048), normalization(2048), nn.SiLU(), nn.Linear(2048, self.out_channels))
        else:
            raise NotImplementedError(f'Unexpected {pool} pooling')

    def convert_to_fp16(self):
        """
        Convert the torso of the model to float16.
        """
        self.input_blocks.apply(convert_module_to_f16)
        self.middle_block.apply(convert_module_to_f16)

    def convert_to_fp32(self):
        """
        Convert the torso of the model to float32.
        """
        self.input_blocks.apply(convert_module_to_f32)
        self.middle_block.apply(convert_module_to_f32)

    def forward(self, x, timesteps):
        """
        Apply the model to an input batch.
        :param x: an [N x C x ...] Tensor of inputs.
        :param timesteps: a 1-D batch of timesteps.
        :return: an [N x K] Tensor of outputs.
        """
        emb = self.time_embed(timestep_embedding(timesteps, self.model_channels))
        results = []
        h = x.type(self.dtype)
        for module in self.input_blocks:
            h = module(h, emb)
            if self.pool.startswith('spatial'):
                results.append(h.type(x.dtype).mean(dim=(2, 3)))
        h = self.middle_block(h, emb)
        if self.pool.startswith('spatial'):
            results.append(h.type(x.dtype).mean(dim=(2, 3)))
            h = th.cat(results, axis=-1)
            return self.out(h)
        else:
            h = h.type(x.dtype)
            return self.out(h)

def __init__(self, image_size, in_channels, model_channels, out_channels, num_res_blocks, attention_resolutions, dropout=0, channel_mult=(1, 2, 4, 8), conv_resample=True, dims=2, use_checkpoint=False, use_fp16=False, num_heads=1, num_head_channels=-1, num_heads_upsample=-1, use_scale_shift_norm=False, resblock_updown=False, use_new_attention_order=False, pool='adaptive', *args, **kwargs):
    super().__init__()
    if num_heads_upsample == -1:
        num_heads_upsample = num_heads
    self.in_channels = in_channels
    self.model_channels = model_channels
    self.out_channels = out_channels
    self.num_res_blocks = num_res_blocks
    self.attention_resolutions = attention_resolutions
    self.dropout = dropout
    self.channel_mult = channel_mult
    self.conv_resample = conv_resample
    self.use_checkpoint = use_checkpoint
    self.dtype = th.float16 if use_fp16 else th.float32
    self.num_heads = num_heads
    self.num_head_channels = num_head_channels
    self.num_heads_upsample = num_heads_upsample
    time_embed_dim = model_channels * 4
    self.time_embed = nn.Sequential(linear(model_channels, time_embed_dim), nn.SiLU(), linear(time_embed_dim, time_embed_dim))
    self.input_blocks = nn.ModuleList([TimestepEmbedSequential(conv_nd(dims, in_channels, model_channels, 3, padding=1))])
    self._feature_size = model_channels
    input_block_chans = [model_channels]
    ch = model_channels
    ds = 1
    for level, mult in enumerate(channel_mult):
        for _ in range(num_res_blocks):
            layers = [ResBlock(ch, time_embed_dim, dropout, out_channels=mult * model_channels, dims=dims, use_checkpoint=use_checkpoint, use_scale_shift_norm=use_scale_shift_norm)]
            ch = mult * model_channels
            if ds in attention_resolutions:
                layers.append(AttentionBlock(ch, use_checkpoint=use_checkpoint, num_heads=num_heads, num_head_channels=num_head_channels, use_new_attention_order=use_new_attention_order))
            self.input_blocks.append(TimestepEmbedSequential(*layers))
            self._feature_size += ch
            input_block_chans.append(ch)
        if level != len(channel_mult) - 1:
            out_ch = ch
            self.input_blocks.append(TimestepEmbedSequential(ResBlock(ch, time_embed_dim, dropout, out_channels=out_ch, dims=dims, use_checkpoint=use_checkpoint, use_scale_shift_norm=use_scale_shift_norm, down=True) if resblock_updown else Downsample(ch, conv_resample, dims=dims, out_channels=out_ch)))
            ch = out_ch
            input_block_chans.append(ch)
            ds *= 2
            self._feature_size += ch
    self.middle_block = TimestepEmbedSequential(ResBlock(ch, time_embed_dim, dropout, dims=dims, use_checkpoint=use_checkpoint, use_scale_shift_norm=use_scale_shift_norm), AttentionBlock(ch, use_checkpoint=use_checkpoint, num_heads=num_heads, num_head_channels=num_head_channels, use_new_attention_order=use_new_attention_order), ResBlock(ch, time_embed_dim, dropout, dims=dims, use_checkpoint=use_checkpoint, use_scale_shift_norm=use_scale_shift_norm))
    self._feature_size += ch
    self.pool = pool
    if pool == 'adaptive':
        self.out = nn.Sequential(normalization(ch), nn.SiLU(), nn.AdaptiveAvgPool2d((1, 1)), zero_module(conv_nd(dims, ch, out_channels, 1)), nn.Flatten())
    elif pool == 'attention':
        assert num_head_channels != -1
        self.out = nn.Sequential(normalization(ch), nn.SiLU(), AttentionPool2d(image_size // ds, ch, num_head_channels, out_channels))
    elif pool == 'spatial':
        self.out = nn.Sequential(nn.Linear(self._feature_size, 2048), nn.ReLU(), nn.Linear(2048, self.out_channels))
    elif pool == 'spatial_v2':
        self.out = nn.Sequential(nn.Linear(self._feature_size, 2048), normalization(2048), nn.SiLU(), nn.Linear(2048, self.out_channels))
    else:
        raise NotImplementedError(f'Unexpected {pool} pooling')

class Upsample(nn.Module):

    def __init__(self, in_channels, with_conv):
        super().__init__()
        self.with_conv = with_conv
        if self.with_conv:
            self.conv = torch.nn.Conv2d(in_channels, in_channels, kernel_size=3, stride=1, padding=1)

    def forward(self, x):
        x = torch.nn.functional.interpolate(x, scale_factor=2.0, mode='nearest')
        if self.with_conv:
            x = self.conv(x)
        return x

def __init__(self, in_channels, with_conv):
    super().__init__()
    self.with_conv = with_conv
    if self.with_conv:
        self.conv = torch.nn.Conv2d(in_channels, in_channels, kernel_size=3, stride=1, padding=1)

class Downsample(nn.Module):

    def __init__(self, in_channels, with_conv):
        super().__init__()
        self.with_conv = with_conv
        if self.with_conv:
            self.conv = torch.nn.Conv2d(in_channels, in_channels, kernel_size=3, stride=2, padding=0)

    def forward(self, x):
        if self.with_conv:
            pad = (0, 1, 0, 1)
            x = torch.nn.functional.pad(x, pad, mode='constant', value=0)
            x = self.conv(x)
        else:
            x = torch.nn.functional.avg_pool2d(x, kernel_size=2, stride=2)
        return x

def __init__(self, in_channels, with_conv):
    super().__init__()
    self.with_conv = with_conv
    if self.with_conv:
        self.conv = torch.nn.Conv2d(in_channels, in_channels, kernel_size=3, stride=2, padding=0)

class ResnetBlock(nn.Module):

    def __init__(self, *, in_channels, out_channels=None, conv_shortcut=False, dropout, temb_channels=512):
        super().__init__()
        self.in_channels = in_channels
        out_channels = in_channels if out_channels is None else out_channels
        self.out_channels = out_channels
        self.use_conv_shortcut = conv_shortcut
        self.norm1 = Normalize(in_channels)
        self.conv1 = torch.nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=1, padding=1)
        if temb_channels > 0:
            self.temb_proj = torch.nn.Linear(temb_channels, out_channels)
        self.norm2 = Normalize(out_channels)
        self.dropout = torch.nn.Dropout(dropout)
        self.conv2 = torch.nn.Conv2d(out_channels, out_channels, kernel_size=3, stride=1, padding=1)
        if self.in_channels != self.out_channels:
            if self.use_conv_shortcut:
                self.conv_shortcut = torch.nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=1, padding=1)
            else:
                self.nin_shortcut = torch.nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=1, padding=0)

    def forward(self, x, temb):
        h = x
        h = self.norm1(h)
        h = nonlinearity(h)
        h = self.conv1(h)
        if temb is not None:
            h = h + self.temb_proj(nonlinearity(temb))[:, :, None, None]
        h = self.norm2(h)
        h = nonlinearity(h)
        h = self.dropout(h)
        h = self.conv2(h)
        if self.in_channels != self.out_channels:
            if self.use_conv_shortcut:
                x = self.conv_shortcut(x)
            else:
                x = self.nin_shortcut(x)
        return x + h

def __init__(self, *, in_channels, out_channels=None, conv_shortcut=False, dropout, temb_channels=512):
    super().__init__()
    self.in_channels = in_channels
    out_channels = in_channels if out_channels is None else out_channels
    self.out_channels = out_channels
    self.use_conv_shortcut = conv_shortcut
    self.norm1 = Normalize(in_channels)
    self.conv1 = torch.nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=1, padding=1)
    if temb_channels > 0:
        self.temb_proj = torch.nn.Linear(temb_channels, out_channels)
    self.norm2 = Normalize(out_channels)
    self.dropout = torch.nn.Dropout(dropout)
    self.conv2 = torch.nn.Conv2d(out_channels, out_channels, kernel_size=3, stride=1, padding=1)
    if self.in_channels != self.out_channels:
        if self.use_conv_shortcut:
            self.conv_shortcut = torch.nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=1, padding=1)
        else:
            self.nin_shortcut = torch.nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=1, padding=0)

class LinAttnBlock(LinearAttention):
    """to match AttnBlock usage"""

    def __init__(self, in_channels):
        super().__init__(dim=in_channels, heads=1, dim_head=in_channels)

def __init__(self, in_channels):
    super().__init__(dim=in_channels, heads=1, dim_head=in_channels)

class AttnBlock(nn.Module):

    def __init__(self, in_channels):
        super().__init__()
        self.in_channels = in_channels
        self.norm = Normalize(in_channels)
        self.q = torch.nn.Conv2d(in_channels, in_channels, kernel_size=1, stride=1, padding=0)
        self.k = torch.nn.Conv2d(in_channels, in_channels, kernel_size=1, stride=1, padding=0)
        self.v = torch.nn.Conv2d(in_channels, in_channels, kernel_size=1, stride=1, padding=0)
        self.proj_out = torch.nn.Conv2d(in_channels, in_channels, kernel_size=1, stride=1, padding=0)

    def forward(self, x):
        h_ = x
        h_ = self.norm(h_)
        q = self.q(h_)
        k = self.k(h_)
        v = self.v(h_)
        b, c, h, w = q.shape
        q = q.reshape(b, c, h * w)
        q = q.permute(0, 2, 1)
        k = k.reshape(b, c, h * w)
        w_ = torch.bmm(q, k)
        w_ = w_ * int(c) ** (-0.5)
        w_ = torch.nn.functional.softmax(w_, dim=2)
        v = v.reshape(b, c, h * w)
        w_ = w_.permute(0, 2, 1)
        h_ = torch.bmm(v, w_)
        h_ = h_.reshape(b, c, h, w)
        h_ = self.proj_out(h_)
        return x + h_

def __init__(self, in_channels):
    super().__init__()
    self.in_channels = in_channels
    self.norm = Normalize(in_channels)
    self.q = torch.nn.Conv2d(in_channels, in_channels, kernel_size=1, stride=1, padding=0)
    self.k = torch.nn.Conv2d(in_channels, in_channels, kernel_size=1, stride=1, padding=0)
    self.v = torch.nn.Conv2d(in_channels, in_channels, kernel_size=1, stride=1, padding=0)
    self.proj_out = torch.nn.Conv2d(in_channels, in_channels, kernel_size=1, stride=1, padding=0)

def make_attn(in_channels, attn_type='vanilla'):
    assert attn_type in ['vanilla', 'linear', 'none'], f'attn_type {attn_type} unknown'
    print(f"making attention of type '{attn_type}' with {in_channels} in_channels")
    if attn_type == 'vanilla':
        return AttnBlock(in_channels)
    elif attn_type == 'none':
        return nn.Identity(in_channels)
    else:
        return LinAttnBlock(in_channels)

class Model(nn.Module):

    def __init__(self, *, ch, out_ch, ch_mult=(1, 2, 4, 8), num_res_blocks, attn_resolutions, dropout=0.0, resamp_with_conv=True, in_channels, resolution, use_timestep=True, use_linear_attn=False, attn_type='vanilla'):
        super().__init__()
        if use_linear_attn:
            attn_type = 'linear'
        self.ch = ch
        self.temb_ch = self.ch * 4
        self.num_resolutions = len(ch_mult)
        self.num_res_blocks = num_res_blocks
        self.resolution = resolution
        self.in_channels = in_channels
        self.use_timestep = use_timestep
        if self.use_timestep:
            self.temb = nn.Module()
            self.temb.dense = nn.ModuleList([torch.nn.Linear(self.ch, self.temb_ch), torch.nn.Linear(self.temb_ch, self.temb_ch)])
        self.conv_in = torch.nn.Conv2d(in_channels, self.ch, kernel_size=3, stride=1, padding=1)
        curr_res = resolution
        in_ch_mult = (1,) + tuple(ch_mult)
        self.down = nn.ModuleList()
        for i_level in range(self.num_resolutions):
            block = nn.ModuleList()
            attn = nn.ModuleList()
            block_in = ch * in_ch_mult[i_level]
            block_out = ch * ch_mult[i_level]
            for i_block in range(self.num_res_blocks):
                block.append(ResnetBlock(in_channels=block_in, out_channels=block_out, temb_channels=self.temb_ch, dropout=dropout))
                block_in = block_out
                if curr_res in attn_resolutions:
                    attn.append(make_attn(block_in, attn_type=attn_type))
            down = nn.Module()
            down.block = block
            down.attn = attn
            if i_level != self.num_resolutions - 1:
                down.downsample = Downsample(block_in, resamp_with_conv)
                curr_res = curr_res // 2
            self.down.append(down)
        self.mid = nn.Module()
        self.mid.block_1 = ResnetBlock(in_channels=block_in, out_channels=block_in, temb_channels=self.temb_ch, dropout=dropout)
        self.mid.attn_1 = make_attn(block_in, attn_type=attn_type)
        self.mid.block_2 = ResnetBlock(in_channels=block_in, out_channels=block_in, temb_channels=self.temb_ch, dropout=dropout)
        self.up = nn.ModuleList()
        for i_level in reversed(range(self.num_resolutions)):
            block = nn.ModuleList()
            attn = nn.ModuleList()
            block_out = ch * ch_mult[i_level]
            skip_in = ch * ch_mult[i_level]
            for i_block in range(self.num_res_blocks + 1):
                if i_block == self.num_res_blocks:
                    skip_in = ch * in_ch_mult[i_level]
                block.append(ResnetBlock(in_channels=block_in + skip_in, out_channels=block_out, temb_channels=self.temb_ch, dropout=dropout))
                block_in = block_out
                if curr_res in attn_resolutions:
                    attn.append(make_attn(block_in, attn_type=attn_type))
            up = nn.Module()
            up.block = block
            up.attn = attn
            if i_level != 0:
                up.upsample = Upsample(block_in, resamp_with_conv)
                curr_res = curr_res * 2
            self.up.insert(0, up)
        self.norm_out = Normalize(block_in)
        self.conv_out = torch.nn.Conv2d(block_in, out_ch, kernel_size=3, stride=1, padding=1)

    def forward(self, x, t=None, context=None):
        if context is not None:
            x = torch.cat((x, context), dim=1)
        if self.use_timestep:
            assert t is not None
            temb = get_timestep_embedding(t, self.ch)
            temb = self.temb.dense[0](temb)
            temb = nonlinearity(temb)
            temb = self.temb.dense[1](temb)
        else:
            temb = None
        hs = [self.conv_in(x)]
        for i_level in range(self.num_resolutions):
            for i_block in range(self.num_res_blocks):
                h = self.down[i_level].block[i_block](hs[-1], temb)
                if len(self.down[i_level].attn) > 0:
                    h = self.down[i_level].attn[i_block](h)
                hs.append(h)
            if i_level != self.num_resolutions - 1:
                hs.append(self.down[i_level].downsample(hs[-1]))
        h = hs[-1]
        h = self.mid.block_1(h, temb)
        h = self.mid.attn_1(h)
        h = self.mid.block_2(h, temb)
        for i_level in reversed(range(self.num_resolutions)):
            for i_block in range(self.num_res_blocks + 1):
                h = self.up[i_level].block[i_block](torch.cat([h, hs.pop()], dim=1), temb)
                if len(self.up[i_level].attn) > 0:
                    h = self.up[i_level].attn[i_block](h)
            if i_level != 0:
                h = self.up[i_level].upsample(h)
        h = self.norm_out(h)
        h = nonlinearity(h)
        h = self.conv_out(h)
        return h

    def get_last_layer(self):
        return self.conv_out.weight

def __init__(self, *, ch, out_ch, ch_mult=(1, 2, 4, 8), num_res_blocks, attn_resolutions, dropout=0.0, resamp_with_conv=True, in_channels, resolution, use_timestep=True, use_linear_attn=False, attn_type='vanilla'):
    super().__init__()
    if use_linear_attn:
        attn_type = 'linear'
    self.ch = ch
    self.temb_ch = self.ch * 4
    self.num_resolutions = len(ch_mult)
    self.num_res_blocks = num_res_blocks
    self.resolution = resolution
    self.in_channels = in_channels
    self.use_timestep = use_timestep
    if self.use_timestep:
        self.temb = nn.Module()
        self.temb.dense = nn.ModuleList([torch.nn.Linear(self.ch, self.temb_ch), torch.nn.Linear(self.temb_ch, self.temb_ch)])
    self.conv_in = torch.nn.Conv2d(in_channels, self.ch, kernel_size=3, stride=1, padding=1)
    curr_res = resolution
    in_ch_mult = (1,) + tuple(ch_mult)
    self.down = nn.ModuleList()
    for i_level in range(self.num_resolutions):
        block = nn.ModuleList()
        attn = nn.ModuleList()
        block_in = ch * in_ch_mult[i_level]
        block_out = ch * ch_mult[i_level]
        for i_block in range(self.num_res_blocks):
            block.append(ResnetBlock(in_channels=block_in, out_channels=block_out, temb_channels=self.temb_ch, dropout=dropout))
            block_in = block_out
            if curr_res in attn_resolutions:
                attn.append(make_attn(block_in, attn_type=attn_type))
        down = nn.Module()
        down.block = block
        down.attn = attn
        if i_level != self.num_resolutions - 1:
            down.downsample = Downsample(block_in, resamp_with_conv)
            curr_res = curr_res // 2
        self.down.append(down)
    self.mid = nn.Module()
    self.mid.block_1 = ResnetBlock(in_channels=block_in, out_channels=block_in, temb_channels=self.temb_ch, dropout=dropout)
    self.mid.attn_1 = make_attn(block_in, attn_type=attn_type)
    self.mid.block_2 = ResnetBlock(in_channels=block_in, out_channels=block_in, temb_channels=self.temb_ch, dropout=dropout)
    self.up = nn.ModuleList()
    for i_level in reversed(range(self.num_resolutions)):
        block = nn.ModuleList()
        attn = nn.ModuleList()
        block_out = ch * ch_mult[i_level]
        skip_in = ch * ch_mult[i_level]
        for i_block in range(self.num_res_blocks + 1):
            if i_block == self.num_res_blocks:
                skip_in = ch * in_ch_mult[i_level]
            block.append(ResnetBlock(in_channels=block_in + skip_in, out_channels=block_out, temb_channels=self.temb_ch, dropout=dropout))
            block_in = block_out
            if curr_res in attn_resolutions:
                attn.append(make_attn(block_in, attn_type=attn_type))
        up = nn.Module()
        up.block = block
        up.attn = attn
        if i_level != 0:
            up.upsample = Upsample(block_in, resamp_with_conv)
            curr_res = curr_res * 2
        self.up.insert(0, up)
    self.norm_out = Normalize(block_in)
    self.conv_out = torch.nn.Conv2d(block_in, out_ch, kernel_size=3, stride=1, padding=1)

class Encoder(nn.Module):

    def __init__(self, *, ch, out_ch, ch_mult=(1, 2, 4, 8), num_res_blocks, attn_resolutions, dropout=0.0, resamp_with_conv=True, in_channels, resolution, z_channels, double_z=True, use_linear_attn=False, attn_type='vanilla', **ignore_kwargs):
        super().__init__()
        if use_linear_attn:
            attn_type = 'linear'
        self.ch = ch
        self.temb_ch = 0
        self.num_resolutions = len(ch_mult)
        self.num_res_blocks = num_res_blocks
        self.resolution = resolution
        self.in_channels = in_channels
        self.conv_in = torch.nn.Conv2d(in_channels, self.ch, kernel_size=3, stride=1, padding=1)
        curr_res = resolution
        in_ch_mult = (1,) + tuple(ch_mult)
        self.in_ch_mult = in_ch_mult
        self.down = nn.ModuleList()
        for i_level in range(self.num_resolutions):
            block = nn.ModuleList()
            attn = nn.ModuleList()
            block_in = ch * in_ch_mult[i_level]
            block_out = ch * ch_mult[i_level]
            for i_block in range(self.num_res_blocks):
                block.append(ResnetBlock(in_channels=block_in, out_channels=block_out, temb_channels=self.temb_ch, dropout=dropout))
                block_in = block_out
                if curr_res in attn_resolutions:
                    attn.append(make_attn(block_in, attn_type=attn_type))
            down = nn.Module()
            down.block = block
            down.attn = attn
            if i_level != self.num_resolutions - 1:
                down.downsample = Downsample(block_in, resamp_with_conv)
                curr_res = curr_res // 2
            self.down.append(down)
        self.mid = nn.Module()
        self.mid.block_1 = ResnetBlock(in_channels=block_in, out_channels=block_in, temb_channels=self.temb_ch, dropout=dropout)
        self.mid.attn_1 = make_attn(block_in, attn_type=attn_type)
        self.mid.block_2 = ResnetBlock(in_channels=block_in, out_channels=block_in, temb_channels=self.temb_ch, dropout=dropout)
        self.norm_out = Normalize(block_in)
        self.conv_out = torch.nn.Conv2d(block_in, 2 * z_channels if double_z else z_channels, kernel_size=3, stride=1, padding=1)

    def forward(self, x):
        temb = None
        hs = [self.conv_in(x)]
        for i_level in range(self.num_resolutions):
            for i_block in range(self.num_res_blocks):
                h = self.down[i_level].block[i_block](hs[-1], temb)
                if len(self.down[i_level].attn) > 0:
                    h = self.down[i_level].attn[i_block](h)
                hs.append(h)
            if i_level != self.num_resolutions - 1:
                hs.append(self.down[i_level].downsample(hs[-1]))
        h = hs[-1]
        h = self.mid.block_1(h, temb)
        h = self.mid.attn_1(h)
        h = self.mid.block_2(h, temb)
        h = self.norm_out(h)
        h = nonlinearity(h)
        h = self.conv_out(h)
        return h

def __init__(self, *, ch, out_ch, ch_mult=(1, 2, 4, 8), num_res_blocks, attn_resolutions, dropout=0.0, resamp_with_conv=True, in_channels, resolution, z_channels, double_z=True, use_linear_attn=False, attn_type='vanilla', **ignore_kwargs):
    super().__init__()
    if use_linear_attn:
        attn_type = 'linear'
    self.ch = ch
    self.temb_ch = 0
    self.num_resolutions = len(ch_mult)
    self.num_res_blocks = num_res_blocks
    self.resolution = resolution
    self.in_channels = in_channels
    self.conv_in = torch.nn.Conv2d(in_channels, self.ch, kernel_size=3, stride=1, padding=1)
    curr_res = resolution
    in_ch_mult = (1,) + tuple(ch_mult)
    self.in_ch_mult = in_ch_mult
    self.down = nn.ModuleList()
    for i_level in range(self.num_resolutions):
        block = nn.ModuleList()
        attn = nn.ModuleList()
        block_in = ch * in_ch_mult[i_level]
        block_out = ch * ch_mult[i_level]
        for i_block in range(self.num_res_blocks):
            block.append(ResnetBlock(in_channels=block_in, out_channels=block_out, temb_channels=self.temb_ch, dropout=dropout))
            block_in = block_out
            if curr_res in attn_resolutions:
                attn.append(make_attn(block_in, attn_type=attn_type))
        down = nn.Module()
        down.block = block
        down.attn = attn
        if i_level != self.num_resolutions - 1:
            down.downsample = Downsample(block_in, resamp_with_conv)
            curr_res = curr_res // 2
        self.down.append(down)
    self.mid = nn.Module()
    self.mid.block_1 = ResnetBlock(in_channels=block_in, out_channels=block_in, temb_channels=self.temb_ch, dropout=dropout)
    self.mid.attn_1 = make_attn(block_in, attn_type=attn_type)
    self.mid.block_2 = ResnetBlock(in_channels=block_in, out_channels=block_in, temb_channels=self.temb_ch, dropout=dropout)
    self.norm_out = Normalize(block_in)
    self.conv_out = torch.nn.Conv2d(block_in, 2 * z_channels if double_z else z_channels, kernel_size=3, stride=1, padding=1)

class Decoder(nn.Module):

    def __init__(self, *, ch, out_ch, ch_mult=(1, 2, 4, 8), num_res_blocks, attn_resolutions, dropout=0.0, resamp_with_conv=True, in_channels, resolution, z_channels, give_pre_end=False, tanh_out=False, use_linear_attn=False, attn_type='vanilla', **ignorekwargs):
        super().__init__()
        if use_linear_attn:
            attn_type = 'linear'
        self.ch = ch
        self.temb_ch = 0
        self.num_resolutions = len(ch_mult)
        self.num_res_blocks = num_res_blocks
        self.resolution = resolution
        self.in_channels = in_channels
        self.give_pre_end = give_pre_end
        self.tanh_out = tanh_out
        in_ch_mult = (1,) + tuple(ch_mult)
        block_in = ch * ch_mult[self.num_resolutions - 1]
        curr_res = resolution // 2 ** (self.num_resolutions - 1)
        self.z_shape = (1, z_channels, curr_res, curr_res)
        print('Working with z of shape {} = {} dimensions.'.format(self.z_shape, np.prod(self.z_shape)))
        self.conv_in = torch.nn.Conv2d(z_channels, block_in, kernel_size=3, stride=1, padding=1)
        self.mid = nn.Module()
        self.mid.block_1 = ResnetBlock(in_channels=block_in, out_channels=block_in, temb_channels=self.temb_ch, dropout=dropout)
        self.mid.attn_1 = make_attn(block_in, attn_type=attn_type)
        self.mid.block_2 = ResnetBlock(in_channels=block_in, out_channels=block_in, temb_channels=self.temb_ch, dropout=dropout)
        self.up = nn.ModuleList()
        for i_level in reversed(range(self.num_resolutions)):
            block = nn.ModuleList()
            attn = nn.ModuleList()
            block_out = ch * ch_mult[i_level]
            for i_block in range(self.num_res_blocks + 1):
                block.append(ResnetBlock(in_channels=block_in, out_channels=block_out, temb_channels=self.temb_ch, dropout=dropout))
                block_in = block_out
                if curr_res in attn_resolutions:
                    attn.append(make_attn(block_in, attn_type=attn_type))
            up = nn.Module()
            up.block = block
            up.attn = attn
            if i_level != 0:
                up.upsample = Upsample(block_in, resamp_with_conv)
                curr_res = curr_res * 2
            self.up.insert(0, up)
        self.norm_out = Normalize(block_in)
        self.conv_out = torch.nn.Conv2d(block_in, out_ch, kernel_size=3, stride=1, padding=1)

    def forward(self, z):
        self.last_z_shape = z.shape
        temb = None
        h = self.conv_in(z)
        h = self.mid.block_1(h, temb)
        h = self.mid.attn_1(h)
        h = self.mid.block_2(h, temb)
        for i_level in reversed(range(self.num_resolutions)):
            for i_block in range(self.num_res_blocks + 1):
                h = self.up[i_level].block[i_block](h, temb)
                if len(self.up[i_level].attn) > 0:
                    h = self.up[i_level].attn[i_block](h)
            if i_level != 0:
                h = self.up[i_level].upsample(h)
        if self.give_pre_end:
            return h
        h = self.norm_out(h)
        h = nonlinearity(h)
        h = self.conv_out(h)
        if self.tanh_out:
            h = torch.tanh(h)
        return h

def __init__(self, *, ch, out_ch, ch_mult=(1, 2, 4, 8), num_res_blocks, attn_resolutions, dropout=0.0, resamp_with_conv=True, in_channels, resolution, z_channels, give_pre_end=False, tanh_out=False, use_linear_attn=False, attn_type='vanilla', **ignorekwargs):
    super().__init__()
    if use_linear_attn:
        attn_type = 'linear'
    self.ch = ch
    self.temb_ch = 0
    self.num_resolutions = len(ch_mult)
    self.num_res_blocks = num_res_blocks
    self.resolution = resolution
    self.in_channels = in_channels
    self.give_pre_end = give_pre_end
    self.tanh_out = tanh_out
    in_ch_mult = (1,) + tuple(ch_mult)
    block_in = ch * ch_mult[self.num_resolutions - 1]
    curr_res = resolution // 2 ** (self.num_resolutions - 1)
    self.z_shape = (1, z_channels, curr_res, curr_res)
    print('Working with z of shape {} = {} dimensions.'.format(self.z_shape, np.prod(self.z_shape)))
    self.conv_in = torch.nn.Conv2d(z_channels, block_in, kernel_size=3, stride=1, padding=1)
    self.mid = nn.Module()
    self.mid.block_1 = ResnetBlock(in_channels=block_in, out_channels=block_in, temb_channels=self.temb_ch, dropout=dropout)
    self.mid.attn_1 = make_attn(block_in, attn_type=attn_type)
    self.mid.block_2 = ResnetBlock(in_channels=block_in, out_channels=block_in, temb_channels=self.temb_ch, dropout=dropout)
    self.up = nn.ModuleList()
    for i_level in reversed(range(self.num_resolutions)):
        block = nn.ModuleList()
        attn = nn.ModuleList()
        block_out = ch * ch_mult[i_level]
        for i_block in range(self.num_res_blocks + 1):
            block.append(ResnetBlock(in_channels=block_in, out_channels=block_out, temb_channels=self.temb_ch, dropout=dropout))
            block_in = block_out
            if curr_res in attn_resolutions:
                attn.append(make_attn(block_in, attn_type=attn_type))
        up = nn.Module()
        up.block = block
        up.attn = attn
        if i_level != 0:
            up.upsample = Upsample(block_in, resamp_with_conv)
            curr_res = curr_res * 2
        self.up.insert(0, up)
    self.norm_out = Normalize(block_in)
    self.conv_out = torch.nn.Conv2d(block_in, out_ch, kernel_size=3, stride=1, padding=1)

class SimpleDecoder(nn.Module):

    def __init__(self, in_channels, out_channels, *args, **kwargs):
        super().__init__()
        self.model = nn.ModuleList([nn.Conv2d(in_channels, in_channels, 1), ResnetBlock(in_channels=in_channels, out_channels=2 * in_channels, temb_channels=0, dropout=0.0), ResnetBlock(in_channels=2 * in_channels, out_channels=4 * in_channels, temb_channels=0, dropout=0.0), ResnetBlock(in_channels=4 * in_channels, out_channels=2 * in_channels, temb_channels=0, dropout=0.0), nn.Conv2d(2 * in_channels, in_channels, 1), Upsample(in_channels, with_conv=True)])
        self.norm_out = Normalize(in_channels)
        self.conv_out = torch.nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=1, padding=1)

    def forward(self, x):
        for i, layer in enumerate(self.model):
            if i in [1, 2, 3]:
                x = layer(x, None)
            else:
                x = layer(x)
        h = self.norm_out(x)
        h = nonlinearity(h)
        x = self.conv_out(h)
        return x

def __init__(self, in_channels, out_channels, *args, **kwargs):
    super().__init__()
    self.model = nn.ModuleList([nn.Conv2d(in_channels, in_channels, 1), ResnetBlock(in_channels=in_channels, out_channels=2 * in_channels, temb_channels=0, dropout=0.0), ResnetBlock(in_channels=2 * in_channels, out_channels=4 * in_channels, temb_channels=0, dropout=0.0), ResnetBlock(in_channels=4 * in_channels, out_channels=2 * in_channels, temb_channels=0, dropout=0.0), nn.Conv2d(2 * in_channels, in_channels, 1), Upsample(in_channels, with_conv=True)])
    self.norm_out = Normalize(in_channels)
    self.conv_out = torch.nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=1, padding=1)

class UpsampleDecoder(nn.Module):

    def __init__(self, in_channels, out_channels, ch, num_res_blocks, resolution, ch_mult=(2, 2), dropout=0.0):
        super().__init__()
        self.temb_ch = 0
        self.num_resolutions = len(ch_mult)
        self.num_res_blocks = num_res_blocks
        block_in = in_channels
        curr_res = resolution // 2 ** (self.num_resolutions - 1)
        self.res_blocks = nn.ModuleList()
        self.upsample_blocks = nn.ModuleList()
        for i_level in range(self.num_resolutions):
            res_block = []
            block_out = ch * ch_mult[i_level]
            for i_block in range(self.num_res_blocks + 1):
                res_block.append(ResnetBlock(in_channels=block_in, out_channels=block_out, temb_channels=self.temb_ch, dropout=dropout))
                block_in = block_out
            self.res_blocks.append(nn.ModuleList(res_block))
            if i_level != self.num_resolutions - 1:
                self.upsample_blocks.append(Upsample(block_in, True))
                curr_res = curr_res * 2
        self.norm_out = Normalize(block_in)
        self.conv_out = torch.nn.Conv2d(block_in, out_channels, kernel_size=3, stride=1, padding=1)

    def forward(self, x):
        h = x
        for k, i_level in enumerate(range(self.num_resolutions)):
            for i_block in range(self.num_res_blocks + 1):
                h = self.res_blocks[i_level][i_block](h, None)
            if i_level != self.num_resolutions - 1:
                h = self.upsample_blocks[k](h)
        h = self.norm_out(h)
        h = nonlinearity(h)
        h = self.conv_out(h)
        return h

def __init__(self, in_channels, out_channels, ch, num_res_blocks, resolution, ch_mult=(2, 2), dropout=0.0):
    super().__init__()
    self.temb_ch = 0
    self.num_resolutions = len(ch_mult)
    self.num_res_blocks = num_res_blocks
    block_in = in_channels
    curr_res = resolution // 2 ** (self.num_resolutions - 1)
    self.res_blocks = nn.ModuleList()
    self.upsample_blocks = nn.ModuleList()
    for i_level in range(self.num_resolutions):
        res_block = []
        block_out = ch * ch_mult[i_level]
        for i_block in range(self.num_res_blocks + 1):
            res_block.append(ResnetBlock(in_channels=block_in, out_channels=block_out, temb_channels=self.temb_ch, dropout=dropout))
            block_in = block_out
        self.res_blocks.append(nn.ModuleList(res_block))
        if i_level != self.num_resolutions - 1:
            self.upsample_blocks.append(Upsample(block_in, True))
            curr_res = curr_res * 2
    self.norm_out = Normalize(block_in)
    self.conv_out = torch.nn.Conv2d(block_in, out_channels, kernel_size=3, stride=1, padding=1)

class LatentRescaler(nn.Module):

    def __init__(self, factor, in_channels, mid_channels, out_channels, depth=2):
        super().__init__()
        self.factor = factor
        self.conv_in = nn.Conv2d(in_channels, mid_channels, kernel_size=3, stride=1, padding=1)
        self.res_block1 = nn.ModuleList([ResnetBlock(in_channels=mid_channels, out_channels=mid_channels, temb_channels=0, dropout=0.0) for _ in range(depth)])
        self.attn = AttnBlock(mid_channels)
        self.res_block2 = nn.ModuleList([ResnetBlock(in_channels=mid_channels, out_channels=mid_channels, temb_channels=0, dropout=0.0) for _ in range(depth)])
        self.conv_out = nn.Conv2d(mid_channels, out_channels, kernel_size=1)

    def forward(self, x):
        x = self.conv_in(x)
        for block in self.res_block1:
            x = block(x, None)
        x = torch.nn.functional.interpolate(x, size=(int(round(x.shape[2] * self.factor)), int(round(x.shape[3] * self.factor))))
        x = self.attn(x)
        for block in self.res_block2:
            x = block(x, None)
        x = self.conv_out(x)
        return x

def __init__(self, factor, in_channels, mid_channels, out_channels, depth=2):
    super().__init__()
    self.factor = factor
    self.conv_in = nn.Conv2d(in_channels, mid_channels, kernel_size=3, stride=1, padding=1)
    self.res_block1 = nn.ModuleList([ResnetBlock(in_channels=mid_channels, out_channels=mid_channels, temb_channels=0, dropout=0.0) for _ in range(depth)])
    self.attn = AttnBlock(mid_channels)
    self.res_block2 = nn.ModuleList([ResnetBlock(in_channels=mid_channels, out_channels=mid_channels, temb_channels=0, dropout=0.0) for _ in range(depth)])
    self.conv_out = nn.Conv2d(mid_channels, out_channels, kernel_size=1)

class MergedRescaleEncoder(nn.Module):

    def __init__(self, in_channels, ch, resolution, out_ch, num_res_blocks, attn_resolutions, dropout=0.0, resamp_with_conv=True, ch_mult=(1, 2, 4, 8), rescale_factor=1.0, rescale_module_depth=1):
        super().__init__()
        intermediate_chn = ch * ch_mult[-1]
        self.encoder = Encoder(in_channels=in_channels, num_res_blocks=num_res_blocks, ch=ch, ch_mult=ch_mult, z_channels=intermediate_chn, double_z=False, resolution=resolution, attn_resolutions=attn_resolutions, dropout=dropout, resamp_with_conv=resamp_with_conv, out_ch=None)
        self.rescaler = LatentRescaler(factor=rescale_factor, in_channels=intermediate_chn, mid_channels=intermediate_chn, out_channels=out_ch, depth=rescale_module_depth)

    def forward(self, x):
        x = self.encoder(x)
        x = self.rescaler(x)
        return x

def __init__(self, in_channels, ch, resolution, out_ch, num_res_blocks, attn_resolutions, dropout=0.0, resamp_with_conv=True, ch_mult=(1, 2, 4, 8), rescale_factor=1.0, rescale_module_depth=1):
    super().__init__()
    intermediate_chn = ch * ch_mult[-1]
    self.encoder = Encoder(in_channels=in_channels, num_res_blocks=num_res_blocks, ch=ch, ch_mult=ch_mult, z_channels=intermediate_chn, double_z=False, resolution=resolution, attn_resolutions=attn_resolutions, dropout=dropout, resamp_with_conv=resamp_with_conv, out_ch=None)
    self.rescaler = LatentRescaler(factor=rescale_factor, in_channels=intermediate_chn, mid_channels=intermediate_chn, out_channels=out_ch, depth=rescale_module_depth)

class MergedRescaleDecoder(nn.Module):

    def __init__(self, z_channels, out_ch, resolution, num_res_blocks, attn_resolutions, ch, ch_mult=(1, 2, 4, 8), dropout=0.0, resamp_with_conv=True, rescale_factor=1.0, rescale_module_depth=1):
        super().__init__()
        tmp_chn = z_channels * ch_mult[-1]
        self.decoder = Decoder(out_ch=out_ch, z_channels=tmp_chn, attn_resolutions=attn_resolutions, dropout=dropout, resamp_with_conv=resamp_with_conv, in_channels=None, num_res_blocks=num_res_blocks, ch_mult=ch_mult, resolution=resolution, ch=ch)
        self.rescaler = LatentRescaler(factor=rescale_factor, in_channels=z_channels, mid_channels=tmp_chn, out_channels=tmp_chn, depth=rescale_module_depth)

    def forward(self, x):
        x = self.rescaler(x)
        x = self.decoder(x)
        return x

def __init__(self, z_channels, out_ch, resolution, num_res_blocks, attn_resolutions, ch, ch_mult=(1, 2, 4, 8), dropout=0.0, resamp_with_conv=True, rescale_factor=1.0, rescale_module_depth=1):
    super().__init__()
    tmp_chn = z_channels * ch_mult[-1]
    self.decoder = Decoder(out_ch=out_ch, z_channels=tmp_chn, attn_resolutions=attn_resolutions, dropout=dropout, resamp_with_conv=resamp_with_conv, in_channels=None, num_res_blocks=num_res_blocks, ch_mult=ch_mult, resolution=resolution, ch=ch)
    self.rescaler = LatentRescaler(factor=rescale_factor, in_channels=z_channels, mid_channels=tmp_chn, out_channels=tmp_chn, depth=rescale_module_depth)

class Upsampler(nn.Module):

    def __init__(self, in_size, out_size, in_channels, out_channels, ch_mult=2):
        super().__init__()
        assert out_size >= in_size
        num_blocks = int(np.log2(out_size // in_size)) + 1
        factor_up = 1.0 + out_size % in_size
        print(f'Building {self.__class__.__name__} with in_size: {in_size} --> out_size {out_size} and factor {factor_up}')
        self.rescaler = LatentRescaler(factor=factor_up, in_channels=in_channels, mid_channels=2 * in_channels, out_channels=in_channels)
        self.decoder = Decoder(out_ch=out_channels, resolution=out_size, z_channels=in_channels, num_res_blocks=2, attn_resolutions=[], in_channels=None, ch=in_channels, ch_mult=[ch_mult for _ in range(num_blocks)])

    def forward(self, x):
        x = self.rescaler(x)
        x = self.decoder(x)
        return x

def __init__(self, in_size, out_size, in_channels, out_channels, ch_mult=2):
    super().__init__()
    assert out_size >= in_size
    num_blocks = int(np.log2(out_size // in_size)) + 1
    factor_up = 1.0 + out_size % in_size
    print(f'Building {self.__class__.__name__} with in_size: {in_size} --> out_size {out_size} and factor {factor_up}')
    self.rescaler = LatentRescaler(factor=factor_up, in_channels=in_channels, mid_channels=2 * in_channels, out_channels=in_channels)
    self.decoder = Decoder(out_ch=out_channels, resolution=out_size, z_channels=in_channels, num_res_blocks=2, attn_resolutions=[], in_channels=None, ch=in_channels, ch_mult=[ch_mult for _ in range(num_blocks)])

class Resize(nn.Module):

    def __init__(self, in_channels=None, learned=False, mode='bilinear'):
        super().__init__()
        self.with_conv = learned
        self.mode = mode
        if self.with_conv:
            print(f'Note: {self.__class__.__name} uses learned downsampling and will ignore the fixed {mode} mode')
            raise NotImplementedError()
            assert in_channels is not None
            self.conv = torch.nn.Conv2d(in_channels, in_channels, kernel_size=4, stride=2, padding=1)

    def forward(self, x, scale_factor=1.0):
        if scale_factor == 1.0:
            return x
        else:
            x = torch.nn.functional.interpolate(x, mode=self.mode, align_corners=False, scale_factor=scale_factor)
        return x

def __init__(self, in_channels=None, learned=False, mode='bilinear'):
    super().__init__()
    self.with_conv = learned
    self.mode = mode
    if self.with_conv:
        print(f'Note: {self.__class__.__name} uses learned downsampling and will ignore the fixed {mode} mode')
        raise NotImplementedError()
        assert in_channels is not None
        self.conv = torch.nn.Conv2d(in_channels, in_channels, kernel_size=4, stride=2, padding=1)

class FirstStagePostProcessor(nn.Module):

    def __init__(self, ch_mult: list, in_channels, pretrained_model: nn.Module=None, reshape=False, n_channels=None, dropout=0.0, pretrained_config=None):
        super().__init__()
        if pretrained_config is None:
            assert pretrained_model is not None, 'Either "pretrained_model" or "pretrained_config" must not be None'
            self.pretrained_model = pretrained_model
        else:
            assert pretrained_config is not None, 'Either "pretrained_model" or "pretrained_config" must not be None'
            self.instantiate_pretrained(pretrained_config)
        self.do_reshape = reshape
        if n_channels is None:
            n_channels = self.pretrained_model.encoder.ch
        self.proj_norm = Normalize(in_channels, num_groups=in_channels // 2)
        self.proj = nn.Conv2d(in_channels, n_channels, kernel_size=3, stride=1, padding=1)
        blocks = []
        downs = []
        ch_in = n_channels
        for m in ch_mult:
            blocks.append(ResnetBlock(in_channels=ch_in, out_channels=m * n_channels, dropout=dropout))
            ch_in = m * n_channels
            downs.append(Downsample(ch_in, with_conv=False))
        self.model = nn.ModuleList(blocks)
        self.downsampler = nn.ModuleList(downs)

    def instantiate_pretrained(self, config):
        model = instantiate_from_config(config)
        self.pretrained_model = model.eval()
        for param in self.pretrained_model.parameters():
            param.requires_grad = False

    @torch.no_grad()
    def encode_with_pretrained(self, x):
        c = self.pretrained_model.encode(x)
        if isinstance(c, DiagonalGaussianDistribution):
            c = c.mode()
        return c

    def forward(self, x):
        z_fs = self.encode_with_pretrained(x)
        z = self.proj_norm(z_fs)
        z = self.proj(z)
        z = nonlinearity(z)
        for submodel, downmodel in zip(self.model, self.downsampler):
            z = submodel(z, temb=None)
            z = downmodel(z)
        if self.do_reshape:
            z = rearrange(z, 'b c h w -> b (h w) c')
        return z

def __init__(self, ch_mult: list, in_channels, pretrained_model: nn.Module=None, reshape=False, n_channels=None, dropout=0.0, pretrained_config=None):
    super().__init__()
    if pretrained_config is None:
        assert pretrained_model is not None, 'Either "pretrained_model" or "pretrained_config" must not be None'
        self.pretrained_model = pretrained_model
    else:
        assert pretrained_config is not None, 'Either "pretrained_model" or "pretrained_config" must not be None'
        self.instantiate_pretrained(pretrained_config)
    self.do_reshape = reshape
    if n_channels is None:
        n_channels = self.pretrained_model.encoder.ch
    self.proj_norm = Normalize(in_channels, num_groups=in_channels // 2)
    self.proj = nn.Conv2d(in_channels, n_channels, kernel_size=3, stride=1, padding=1)
    blocks = []
    downs = []
    ch_in = n_channels
    for m in ch_mult:
        blocks.append(ResnetBlock(in_channels=ch_in, out_channels=m * n_channels, dropout=dropout))
        ch_in = m * n_channels
        downs.append(Downsample(ch_in, with_conv=False))
    self.model = nn.ModuleList(blocks)
    self.downsampler = nn.ModuleList(downs)

def betas_for_alpha_bar(num_diffusion_timesteps, alpha_bar, max_beta=0.999):
    """
    Create a beta schedule that discretizes the given alpha_t_bar function,
    which defines the cumulative product of (1-beta) over time from t = [0,1].
    :param num_diffusion_timesteps: the number of betas to produce.
    :param alpha_bar: a lambda that takes an argument t from 0 to 1 and
                      produces the cumulative product of (1-beta) up to that
                      part of the diffusion process.
    :param max_beta: the maximum beta to use; use values lower than 1 to
                     prevent singularities.
    """
    betas = []
    for i in range(num_diffusion_timesteps):
        t1 = i / num_diffusion_timesteps
        t2 = (i + 1) / num_diffusion_timesteps
        betas.append(min(1 - alpha_bar(t2) / alpha_bar(t1), max_beta))
    return np.array(betas)

def zero_module(module):
    """
    Zero out the parameters of a module and return it.
    """
    for p in module.parameters():
        p.detach().zero_()
    return module

class GroupNorm32(nn.GroupNorm):

    def forward(self, x):
        return super().forward(x.float()).type(x.dtype)

def forward(self, x):
    return super().forward(x.float()).type(x.dtype)

def conv_nd(dims, *args, **kwargs):
    """
    Create a 1D, 2D, or 3D convolution module.
    """
    if dims == 1:
        return nn.Conv1d(*args, **kwargs)
    elif dims == 2:
        return nn.Conv2d(*args, **kwargs)
    elif dims == 3:
        return nn.Conv3d(*args, **kwargs)
    raise ValueError(f'unsupported dimensions: {dims}')

def linear(*args, **kwargs):
    """
    Create a linear module.
    """
    return nn.Linear(*args, **kwargs)

class HybridConditioner(nn.Module):

    def __init__(self, c_concat_config, c_crossattn_config):
        super().__init__()
        self.concat_conditioner = instantiate_from_config(c_concat_config)
        self.crossattn_conditioner = instantiate_from_config(c_crossattn_config)

    def forward(self, c_concat, c_crossattn):
        c_concat = self.concat_conditioner(c_concat)
        c_crossattn = self.crossattn_conditioner(c_crossattn)
        return {'c_concat': [c_concat], 'c_crossattn': [c_crossattn]}

def __init__(self, c_concat_config, c_crossattn_config):
    super().__init__()
    self.concat_conditioner = instantiate_from_config(c_concat_config)
    self.crossattn_conditioner = instantiate_from_config(c_crossattn_config)

class AbstractEncoder(nn.Module):

    def __init__(self):
        super().__init__()

    def encode(self, *args, **kwargs):
        raise NotImplementedError

def __init__(self):
    super().__init__()

class ClassEmbedder(nn.Module):

    def __init__(self, embed_dim, n_classes=1000, key='class'):
        super().__init__()
        self.key = key
        self.embedding = nn.Embedding(n_classes, embed_dim)

    def forward(self, batch, key=None):
        if key is None:
            key = self.key
        c = batch[key][:, None]
        c = self.embedding(c)
        return c

def __init__(self, embed_dim, n_classes=1000, key='class'):
    super().__init__()
    self.key = key
    self.embedding = nn.Embedding(n_classes, embed_dim)

class TransformerEmbedder(AbstractEncoder):
    """Some transformer encoder layers"""

    def __init__(self, n_embed, n_layer, vocab_size, max_seq_len=77, device='cuda'):
        super().__init__()
        self.device = device
        self.transformer = TransformerWrapper(num_tokens=vocab_size, max_seq_len=max_seq_len, attn_layers=Encoder(dim=n_embed, depth=n_layer))

    def forward(self, tokens):
        tokens = tokens.to(self.device)
        z = self.transformer(tokens, return_embeddings=True)
        return z

    def encode(self, x):
        return self(x)

def __init__(self, n_embed, n_layer, vocab_size, max_seq_len=77, device='cuda'):
    super().__init__()
    self.device = device
    self.transformer = TransformerWrapper(num_tokens=vocab_size, max_seq_len=max_seq_len, attn_layers=Encoder(dim=n_embed, depth=n_layer))

class BERTTokenizer(AbstractEncoder):
    """ Uses a pretrained BERT tokenizer by huggingface. Vocab size: 30522 (?)"""

    def __init__(self, device='cuda', vq_interface=True, max_length=77):
        super().__init__()
        from transformers import BertTokenizerFast
        self.tokenizer = BertTokenizerFast.from_pretrained('bert-base-uncased')
        self.device = device
        self.vq_interface = vq_interface
        self.max_length = max_length

    def forward(self, text):
        batch_encoding = self.tokenizer(text, truncation=True, max_length=self.max_length, return_length=True, return_overflowing_tokens=False, padding='max_length', return_tensors='pt')
        tokens = batch_encoding['input_ids'].to(self.device)
        return tokens

    @torch.no_grad()
    def encode(self, text):
        tokens = self(text)
        if not self.vq_interface:
            return tokens
        return (None, None, [None, None, tokens])

    def decode(self, text):
        return text

def __init__(self, device='cuda', vq_interface=True, max_length=77):
    super().__init__()
    from transformers import BertTokenizerFast
    self.tokenizer = BertTokenizerFast.from_pretrained('bert-base-uncased')
    self.device = device
    self.vq_interface = vq_interface
    self.max_length = max_length

class BERTEmbedder(AbstractEncoder):
    """Uses the BERT tokenizr model and add some transformer encoder layers"""

    def __init__(self, n_embed, n_layer, vocab_size=30522, max_seq_len=77, device='cuda', use_tokenizer=True, embedding_dropout=0.0):
        super().__init__()
        self.use_tknz_fn = use_tokenizer
        if self.use_tknz_fn:
            self.tknz_fn = BERTTokenizer(vq_interface=False, max_length=max_seq_len)
        self.device = device
        self.transformer = TransformerWrapper(num_tokens=vocab_size, max_seq_len=max_seq_len, attn_layers=Encoder(dim=n_embed, depth=n_layer), emb_dropout=embedding_dropout)

    def forward(self, text):
        if self.use_tknz_fn:
            tokens = self.tknz_fn(text)
        else:
            tokens = text
        z = self.transformer(tokens, return_embeddings=True)
        return z

    def encode(self, text):
        return self(text)

def __init__(self, n_embed, n_layer, vocab_size=30522, max_seq_len=77, device='cuda', use_tokenizer=True, embedding_dropout=0.0):
    super().__init__()
    self.use_tknz_fn = use_tokenizer
    if self.use_tknz_fn:
        self.tknz_fn = BERTTokenizer(vq_interface=False, max_length=max_seq_len)
    self.device = device
    self.transformer = TransformerWrapper(num_tokens=vocab_size, max_seq_len=max_seq_len, attn_layers=Encoder(dim=n_embed, depth=n_layer), emb_dropout=embedding_dropout)

class SpatialRescaler(nn.Module):

    def __init__(self, n_stages=1, method='bilinear', multiplier=0.5, in_channels=3, out_channels=None, bias=False):
        super().__init__()
        self.n_stages = n_stages
        assert self.n_stages >= 0
        assert method in ['nearest', 'linear', 'bilinear', 'trilinear', 'bicubic', 'area']
        self.multiplier = multiplier
        self.interpolator = partial(torch.nn.functional.interpolate, mode=method)
        self.remap_output = out_channels is not None
        if self.remap_output:
            print(f'Spatial Rescaler mapping from {in_channels} to {out_channels} channels after resizing.')
            self.channel_mapper = nn.Conv2d(in_channels, out_channels, 1, bias=bias)

    def forward(self, x):
        for stage in range(self.n_stages):
            x = self.interpolator(x, scale_factor=self.multiplier)
        if self.remap_output:
            x = self.channel_mapper(x)
        return x

    def encode(self, x):
        return self(x)

def __init__(self, n_stages=1, method='bilinear', multiplier=0.5, in_channels=3, out_channels=None, bias=False):
    super().__init__()
    self.n_stages = n_stages
    assert self.n_stages >= 0
    assert method in ['nearest', 'linear', 'bilinear', 'trilinear', 'bicubic', 'area']
    self.multiplier = multiplier
    self.interpolator = partial(torch.nn.functional.interpolate, mode=method)
    self.remap_output = out_channels is not None
    if self.remap_output:
        print(f'Spatial Rescaler mapping from {in_channels} to {out_channels} channels after resizing.')
        self.channel_mapper = nn.Conv2d(in_channels, out_channels, 1, bias=bias)

def forward(self, x):
    for stage in range(self.n_stages):
        x = self.interpolator(x, scale_factor=self.multiplier)
    if self.remap_output:
        x = self.channel_mapper(x)
    return x

class FrozenCLIPTextEmbedder(nn.Module):
    """
    Uses the CLIP transformer encoder for text.
    """

    def __init__(self, version='ViT-L/14', device='cuda', max_length=77, n_repeat=1, normalize=True):
        super().__init__()
        self.model, _ = clip.load(version, jit=False, device='cpu')
        self.device = device
        self.max_length = max_length
        self.n_repeat = n_repeat
        self.normalize = normalize

    def freeze(self):
        self.model = self.model.eval()
        for param in self.parameters():
            param.requires_grad = False

    def forward(self, text):
        tokens = clip.tokenize(text).to(self.device)
        z = self.model.encode_text(tokens)
        if self.normalize:
            z = z / torch.linalg.norm(z, dim=1, keepdim=True)
        return z

    def encode(self, text):
        z = self(text)
        if z.ndim == 2:
            z = z[:, None, :]
        z = repeat(z, 'b 1 d -> b k d', k=self.n_repeat)
        return z

def __init__(self, version='ViT-L/14', device='cuda', max_length=77, n_repeat=1, normalize=True):
    super().__init__()
    self.model, _ = clip.load(version, jit=False, device='cpu')
    self.device = device
    self.max_length = max_length
    self.n_repeat = n_repeat
    self.normalize = normalize

class FrozenClipImageEmbedder(nn.Module):
    """
        Uses the CLIP image encoder.
        """

    def __init__(self, model, jit=False, device='cuda' if torch.cuda.is_available() else 'cpu', antialias=False):
        super().__init__()
        self.model, _ = clip.load(name=model, device=device, jit=jit)
        self.antialias = antialias
        self.register_buffer('mean', torch.Tensor([0.48145466, 0.4578275, 0.40821073]), persistent=False)
        self.register_buffer('std', torch.Tensor([0.26862954, 0.26130258, 0.27577711]), persistent=False)

    def preprocess(self, x):
        x = kornia.geometry.resize(x, (224, 224), interpolation='bicubic', align_corners=True, antialias=self.antialias)
        x = (x + 1.0) / 2.0
        x = kornia.enhance.normalize(x, self.mean, self.std)
        return x

    def forward(self, x):
        return self.model.encode_image(self.preprocess(x))

def __init__(self, model, jit=False, device='cuda' if torch.cuda.is_available() else 'cpu', antialias=False):
    super().__init__()
    self.model, _ = clip.load(name=model, device=device, jit=jit)
    self.antialias = antialias
    self.register_buffer('mean', torch.Tensor([0.48145466, 0.4578275, 0.40821073]), persistent=False)
    self.register_buffer('std', torch.Tensor([0.26862954, 0.26130258, 0.27577711]), persistent=False)

class VQModel(pl.LightningModule):

    def __init__(self, ddconfig, lossconfig, n_embed, embed_dim, ckpt_path=None, ignore_keys=[], image_key='image', colorize_nlabels=None, monitor=None, batch_resize_range=None, scheduler_config=None, lr_g_factor=1.0, remap=None, sane_index_shape=False, use_ema=False):
        super().__init__()
        self.embed_dim = embed_dim
        self.n_embed = n_embed
        self.image_key = image_key
        self.encoder = Encoder(**ddconfig)
        self.decoder = Decoder(**ddconfig)
        self.loss = instantiate_from_config(lossconfig)
        self.quantize = VectorQuantizer(n_embed, embed_dim, beta=0.25, remap=remap, sane_index_shape=sane_index_shape)
        self.quant_conv = torch.nn.Conv2d(ddconfig['z_channels'], embed_dim, 1)
        self.post_quant_conv = torch.nn.Conv2d(embed_dim, ddconfig['z_channels'], 1)
        if colorize_nlabels is not None:
            assert type(colorize_nlabels) == int
            self.register_buffer('colorize', torch.randn(3, colorize_nlabels, 1, 1))
        if monitor is not None:
            self.monitor = monitor
        self.batch_resize_range = batch_resize_range
        if self.batch_resize_range is not None:
            print(f'{self.__class__.__name__}: Using per-batch resizing in range {batch_resize_range}.')
        self.use_ema = use_ema
        if self.use_ema:
            self.model_ema = LitEma(self)
            print(f'Keeping EMAs of {len(list(self.model_ema.buffers()))}.')
        if ckpt_path is not None:
            self.init_from_ckpt(ckpt_path, ignore_keys=ignore_keys)
        self.scheduler_config = scheduler_config
        self.lr_g_factor = lr_g_factor

    @contextmanager
    def ema_scope(self, context=None):
        if self.use_ema:
            self.model_ema.store(self.parameters())
            self.model_ema.copy_to(self)
            if context is not None:
                print(f'{context}: Switched to EMA weights')
        try:
            yield None
        finally:
            if self.use_ema:
                self.model_ema.restore(self.parameters())
                if context is not None:
                    print(f'{context}: Restored training weights')

    def init_from_ckpt(self, path, ignore_keys=list()):
        sd = torch.load(path, map_location='cpu')['state_dict']
        keys = list(sd.keys())
        for k in keys:
            for ik in ignore_keys:
                if k.startswith(ik):
                    print('Deleting key {} from state_dict.'.format(k))
                    del sd[k]
        missing, unexpected = self.load_state_dict(sd, strict=False)
        print(f'Restored from {path} with {len(missing)} missing and {len(unexpected)} unexpected keys')
        if len(missing) > 0:
            print(f'Missing Keys: {missing}')
            print(f'Unexpected Keys: {unexpected}')

    def on_train_batch_end(self, *args, **kwargs):
        if self.use_ema:
            self.model_ema(self)

    def encode(self, x):
        h = self.encoder(x)
        h = self.quant_conv(h)
        quant, emb_loss, info = self.quantize(h)
        return (quant, emb_loss, info)

    def encode_to_prequant(self, x):
        h = self.encoder(x)
        h = self.quant_conv(h)
        return h

    def decode(self, quant):
        quant = self.post_quant_conv(quant)
        dec = self.decoder(quant)
        return dec

    def decode_code(self, code_b):
        quant_b = self.quantize.embed_code(code_b)
        dec = self.decode(quant_b)
        return dec

    def forward(self, input, return_pred_indices=False):
        quant, diff, (_, _, ind) = self.encode(input)
        dec = self.decode(quant)
        if return_pred_indices:
            return (dec, diff, ind)
        return (dec, diff)

    def get_input(self, batch, k):
        x = batch[k]
        if len(x.shape) == 3:
            x = x[..., None]
        x = x.permute(0, 3, 1, 2).to(memory_format=torch.contiguous_format).float()
        if self.batch_resize_range is not None:
            lower_size = self.batch_resize_range[0]
            upper_size = self.batch_resize_range[1]
            if self.global_step <= 4:
                new_resize = upper_size
            else:
                new_resize = np.random.choice(np.arange(lower_size, upper_size + 16, 16))
            if new_resize != x.shape[2]:
                x = F.interpolate(x, size=new_resize, mode='bicubic')
            x = x.detach()
        return x

    def training_step(self, batch, batch_idx, optimizer_idx):
        x = self.get_input(batch, self.image_key)
        xrec, qloss, ind = self(x, return_pred_indices=True)
        if optimizer_idx == 0:
            aeloss, log_dict_ae = self.loss(qloss, x, xrec, optimizer_idx, self.global_step, last_layer=self.get_last_layer(), split='train', predicted_indices=ind)
            self.log_dict(log_dict_ae, prog_bar=False, logger=True, on_step=True, on_epoch=True)
            return aeloss
        if optimizer_idx == 1:
            discloss, log_dict_disc = self.loss(qloss, x, xrec, optimizer_idx, self.global_step, last_layer=self.get_last_layer(), split='train')
            self.log_dict(log_dict_disc, prog_bar=False, logger=True, on_step=True, on_epoch=True)
            return discloss

    def validation_step(self, batch, batch_idx):
        log_dict = self._validation_step(batch, batch_idx)
        with self.ema_scope():
            log_dict_ema = self._validation_step(batch, batch_idx, suffix='_ema')
        return log_dict

    def _validation_step(self, batch, batch_idx, suffix=''):
        x = self.get_input(batch, self.image_key)
        xrec, qloss, ind = self(x, return_pred_indices=True)
        aeloss, log_dict_ae = self.loss(qloss, x, xrec, 0, self.global_step, last_layer=self.get_last_layer(), split='val' + suffix, predicted_indices=ind)
        discloss, log_dict_disc = self.loss(qloss, x, xrec, 1, self.global_step, last_layer=self.get_last_layer(), split='val' + suffix, predicted_indices=ind)
        rec_loss = log_dict_ae[f'val{suffix}/rec_loss']
        self.log(f'val{suffix}/rec_loss', rec_loss, prog_bar=True, logger=True, on_step=False, on_epoch=True, sync_dist=True)
        self.log(f'val{suffix}/aeloss', aeloss, prog_bar=True, logger=True, on_step=False, on_epoch=True, sync_dist=True)
        if version.parse(pl.__version__) >= version.parse('1.4.0'):
            del log_dict_ae[f'val{suffix}/rec_loss']
        self.log_dict(log_dict_ae)
        self.log_dict(log_dict_disc)
        return self.log_dict

    def configure_optimizers(self):
        lr_d = self.learning_rate
        lr_g = self.lr_g_factor * self.learning_rate
        print('lr_d', lr_d)
        print('lr_g', lr_g)
        opt_ae = torch.optim.Adam(list(self.encoder.parameters()) + list(self.decoder.parameters()) + list(self.quantize.parameters()) + list(self.quant_conv.parameters()) + list(self.post_quant_conv.parameters()), lr=lr_g, betas=(0.5, 0.9))
        opt_disc = torch.optim.Adam(self.loss.discriminator.parameters(), lr=lr_d, betas=(0.5, 0.9))
        if self.scheduler_config is not None:
            scheduler = instantiate_from_config(self.scheduler_config)
            print('Setting up LambdaLR scheduler...')
            scheduler = [{'scheduler': LambdaLR(opt_ae, lr_lambda=scheduler.schedule), 'interval': 'step', 'frequency': 1}, {'scheduler': LambdaLR(opt_disc, lr_lambda=scheduler.schedule), 'interval': 'step', 'frequency': 1}]
            return ([opt_ae, opt_disc], scheduler)
        return ([opt_ae, opt_disc], [])

    def get_last_layer(self):
        return self.decoder.conv_out.weight

    def log_images(self, batch, only_inputs=False, plot_ema=False, **kwargs):
        log = dict()
        x = self.get_input(batch, self.image_key)
        x = x.to(self.device)
        if only_inputs:
            log['inputs'] = x
            return log
        xrec, _ = self(x)
        if x.shape[1] > 3:
            assert xrec.shape[1] > 3
            x = self.to_rgb(x)
            xrec = self.to_rgb(xrec)
        log['inputs'] = x
        log['reconstructions'] = xrec
        if plot_ema:
            with self.ema_scope():
                xrec_ema, _ = self(x)
                if x.shape[1] > 3:
                    xrec_ema = self.to_rgb(xrec_ema)
                log['reconstructions_ema'] = xrec_ema
        return log

    def to_rgb(self, x):
        assert self.image_key == 'segmentation'
        if not hasattr(self, 'colorize'):
            self.register_buffer('colorize', torch.randn(3, x.shape[1], 1, 1).to(x))
        x = F.conv2d(x, weight=self.colorize)
        x = 2.0 * (x - x.min()) / (x.max() - x.min()) - 1.0
        return x

def __init__(self, ddconfig, lossconfig, n_embed, embed_dim, ckpt_path=None, ignore_keys=[], image_key='image', colorize_nlabels=None, monitor=None, batch_resize_range=None, scheduler_config=None, lr_g_factor=1.0, remap=None, sane_index_shape=False, use_ema=False):
    super().__init__()
    self.embed_dim = embed_dim
    self.n_embed = n_embed
    self.image_key = image_key
    self.encoder = Encoder(**ddconfig)
    self.decoder = Decoder(**ddconfig)
    self.loss = instantiate_from_config(lossconfig)
    self.quantize = VectorQuantizer(n_embed, embed_dim, beta=0.25, remap=remap, sane_index_shape=sane_index_shape)
    self.quant_conv = torch.nn.Conv2d(ddconfig['z_channels'], embed_dim, 1)
    self.post_quant_conv = torch.nn.Conv2d(embed_dim, ddconfig['z_channels'], 1)
    if colorize_nlabels is not None:
        assert type(colorize_nlabels) == int
        self.register_buffer('colorize', torch.randn(3, colorize_nlabels, 1, 1))
    if monitor is not None:
        self.monitor = monitor
    self.batch_resize_range = batch_resize_range
    if self.batch_resize_range is not None:
        print(f'{self.__class__.__name__}: Using per-batch resizing in range {batch_resize_range}.')
    self.use_ema = use_ema
    if self.use_ema:
        self.model_ema = LitEma(self)
        print(f'Keeping EMAs of {len(list(self.model_ema.buffers()))}.')
    if ckpt_path is not None:
        self.init_from_ckpt(ckpt_path, ignore_keys=ignore_keys)
    self.scheduler_config = scheduler_config
    self.lr_g_factor = lr_g_factor

class VQModelInterface(VQModel):

    def __init__(self, embed_dim, *args, **kwargs):
        super().__init__(*args, embed_dim=embed_dim, **kwargs)
        self.embed_dim = embed_dim

    def encode(self, x):
        h = self.encoder(x)
        h = self.quant_conv(h)
        return h

    def decode(self, h, force_not_quantize=False):
        if not force_not_quantize:
            quant, emb_loss, info = self.quantize(h)
        else:
            quant = h
        quant = self.post_quant_conv(quant)
        dec = self.decoder(quant)
        return dec

def __init__(self, embed_dim, *args, **kwargs):
    super().__init__(*args, embed_dim=embed_dim, **kwargs)
    self.embed_dim = embed_dim

class AutoencoderKL(pl.LightningModule):

    def __init__(self, ddconfig, lossconfig, embed_dim, ckpt_path=None, ignore_keys=[], image_key='image', colorize_nlabels=None, monitor=None):
        super().__init__()
        self.image_key = image_key
        self.encoder = Encoder(**ddconfig)
        self.decoder = Decoder(**ddconfig)
        self.loss = instantiate_from_config(lossconfig)
        assert ddconfig['double_z']
        self.quant_conv = torch.nn.Conv2d(2 * ddconfig['z_channels'], 2 * embed_dim, 1)
        self.post_quant_conv = torch.nn.Conv2d(embed_dim, ddconfig['z_channels'], 1)
        self.embed_dim = embed_dim
        if colorize_nlabels is not None:
            assert type(colorize_nlabels) == int
            self.register_buffer('colorize', torch.randn(3, colorize_nlabels, 1, 1))
        if monitor is not None:
            self.monitor = monitor
        if ckpt_path is not None:
            self.init_from_ckpt(ckpt_path, ignore_keys=ignore_keys)

    def init_from_ckpt(self, path, ignore_keys=list()):
        sd = torch.load(path, map_location='cpu')['state_dict']
        keys = list(sd.keys())
        for k in keys:
            for ik in ignore_keys:
                if k.startswith(ik):
                    print('Deleting key {} from state_dict.'.format(k))
                    del sd[k]
        self.load_state_dict(sd, strict=False)
        print(f'Restored from {path}')

    def encode(self, x):
        h = self.encoder(x)
        moments = self.quant_conv(h)
        posterior = DiagonalGaussianDistribution(moments)
        return posterior

    def decode(self, z):
        z = self.post_quant_conv(z)
        dec = self.decoder(z)
        return dec

    def forward(self, input, sample_posterior=True):
        posterior = self.encode(input)
        if sample_posterior:
            z = posterior.sample()
        else:
            z = posterior.mode()
        dec = self.decode(z)
        return (dec, posterior)

    def get_input(self, batch, k):
        x = batch[k]
        if len(x.shape) == 3:
            x = x[..., None]
        x = x.permute(0, 3, 1, 2).to(memory_format=torch.contiguous_format).float()
        return x

    def training_step(self, batch, batch_idx, optimizer_idx):
        inputs = self.get_input(batch, self.image_key)
        reconstructions, posterior = self(inputs)
        if optimizer_idx == 0:
            aeloss, log_dict_ae = self.loss(inputs, reconstructions, posterior, optimizer_idx, self.global_step, last_layer=self.get_last_layer(), split='train')
            self.log('aeloss', aeloss, prog_bar=True, logger=True, on_step=True, on_epoch=True)
            self.log_dict(log_dict_ae, prog_bar=False, logger=True, on_step=True, on_epoch=False)
            return aeloss
        if optimizer_idx == 1:
            discloss, log_dict_disc = self.loss(inputs, reconstructions, posterior, optimizer_idx, self.global_step, last_layer=self.get_last_layer(), split='train')
            self.log('discloss', discloss, prog_bar=True, logger=True, on_step=True, on_epoch=True)
            self.log_dict(log_dict_disc, prog_bar=False, logger=True, on_step=True, on_epoch=False)
            return discloss

    def validation_step(self, batch, batch_idx):
        inputs = self.get_input(batch, self.image_key)
        reconstructions, posterior = self(inputs)
        aeloss, log_dict_ae = self.loss(inputs, reconstructions, posterior, 0, self.global_step, last_layer=self.get_last_layer(), split='val')
        discloss, log_dict_disc = self.loss(inputs, reconstructions, posterior, 1, self.global_step, last_layer=self.get_last_layer(), split='val')
        self.log('val/rec_loss', log_dict_ae['val/rec_loss'])
        self.log_dict(log_dict_ae)
        self.log_dict(log_dict_disc)
        return self.log_dict

    def configure_optimizers(self):
        lr = self.learning_rate
        opt_ae = torch.optim.Adam(list(self.encoder.parameters()) + list(self.decoder.parameters()) + list(self.quant_conv.parameters()) + list(self.post_quant_conv.parameters()), lr=lr, betas=(0.5, 0.9))
        opt_disc = torch.optim.Adam(self.loss.discriminator.parameters(), lr=lr, betas=(0.5, 0.9))
        return ([opt_ae, opt_disc], [])

    def get_last_layer(self):
        return self.decoder.conv_out.weight

    @torch.no_grad()
    def log_images(self, batch, only_inputs=False, **kwargs):
        log = dict()
        x = self.get_input(batch, self.image_key)
        x = x.to(self.device)
        if not only_inputs:
            xrec, posterior = self(x)
            if x.shape[1] > 3:
                assert xrec.shape[1] > 3
                x = self.to_rgb(x)
                xrec = self.to_rgb(xrec)
            log['samples'] = self.decode(torch.randn_like(posterior.sample()))
            log['reconstructions'] = xrec
        log['inputs'] = x
        return log

    def to_rgb(self, x):
        assert self.image_key == 'segmentation'
        if not hasattr(self, 'colorize'):
            self.register_buffer('colorize', torch.randn(3, x.shape[1], 1, 1).to(x))
        x = F.conv2d(x, weight=self.colorize)
        x = 2.0 * (x - x.min()) / (x.max() - x.min()) - 1.0
        return x

def __init__(self, ddconfig, lossconfig, embed_dim, ckpt_path=None, ignore_keys=[], image_key='image', colorize_nlabels=None, monitor=None):
    super().__init__()
    self.image_key = image_key
    self.encoder = Encoder(**ddconfig)
    self.decoder = Decoder(**ddconfig)
    self.loss = instantiate_from_config(lossconfig)
    assert ddconfig['double_z']
    self.quant_conv = torch.nn.Conv2d(2 * ddconfig['z_channels'], 2 * embed_dim, 1)
    self.post_quant_conv = torch.nn.Conv2d(embed_dim, ddconfig['z_channels'], 1)
    self.embed_dim = embed_dim
    if colorize_nlabels is not None:
        assert type(colorize_nlabels) == int
        self.register_buffer('colorize', torch.randn(3, colorize_nlabels, 1, 1))
    if monitor is not None:
        self.monitor = monitor
    if ckpt_path is not None:
        self.init_from_ckpt(ckpt_path, ignore_keys=ignore_keys)

class IdentityFirstStage(torch.nn.Module):

    def __init__(self, *args, vq_interface=False, **kwargs):
        self.vq_interface = vq_interface
        super().__init__()

    def encode(self, x, *args, **kwargs):
        return x

    def decode(self, x, *args, **kwargs):
        return x

    def quantize(self, x, *args, **kwargs):
        if self.vq_interface:
            return (x, None, [None, None, None])
        return x

    def forward(self, x, *args, **kwargs):
        return x

def __init__(self, *args, vq_interface=False, **kwargs):
    self.vq_interface = vq_interface
    super().__init__()

class NoisyLatentImageClassifier(pl.LightningModule):

    def __init__(self, diffusion_path, num_classes, ckpt_path=None, pool='attention', label_key=None, diffusion_ckpt_path=None, scheduler_config=None, weight_decay=0.01, log_steps=10, monitor='val/loss', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.num_classes = num_classes
        diffusion_config = natsorted(glob(os.path.join(diffusion_path, 'configs', '*-project.yaml')))[-1]
        self.diffusion_config = OmegaConf.load(diffusion_config).model
        self.diffusion_config.params.ckpt_path = diffusion_ckpt_path
        self.load_diffusion()
        self.monitor = monitor
        self.numd = self.diffusion_model.first_stage_model.encoder.num_resolutions - 1
        self.log_time_interval = self.diffusion_model.num_timesteps // log_steps
        self.log_steps = log_steps
        self.label_key = label_key if not hasattr(self.diffusion_model, 'cond_stage_key') else self.diffusion_model.cond_stage_key
        assert self.label_key is not None, 'label_key neither in diffusion model nor in model.params'
        if self.label_key not in __models__:
            raise NotImplementedError()
        self.load_classifier(ckpt_path, pool)
        self.scheduler_config = scheduler_config
        self.use_scheduler = self.scheduler_config is not None
        self.weight_decay = weight_decay

    def init_from_ckpt(self, path, ignore_keys=list(), only_model=False):
        sd = torch.load(path, map_location='cpu')
        if 'state_dict' in list(sd.keys()):
            sd = sd['state_dict']
        keys = list(sd.keys())
        for k in keys:
            for ik in ignore_keys:
                if k.startswith(ik):
                    print('Deleting key {} from state_dict.'.format(k))
                    del sd[k]
        missing, unexpected = self.load_state_dict(sd, strict=False) if not only_model else self.model.load_state_dict(sd, strict=False)
        print(f'Restored from {path} with {len(missing)} missing and {len(unexpected)} unexpected keys')
        if len(missing) > 0:
            print(f'Missing Keys: {missing}')
        if len(unexpected) > 0:
            print(f'Unexpected Keys: {unexpected}')

    def load_diffusion(self):
        model = instantiate_from_config(self.diffusion_config)
        self.diffusion_model = model.eval()
        self.diffusion_model.train = disabled_train
        for param in self.diffusion_model.parameters():
            param.requires_grad = False

    def load_classifier(self, ckpt_path, pool):
        model_config = deepcopy(self.diffusion_config.params.unet_config.params)
        model_config.in_channels = self.diffusion_config.params.unet_config.params.out_channels
        model_config.out_channels = self.num_classes
        if self.label_key == 'class_label':
            model_config.pool = pool
        self.model = __models__[self.label_key](**model_config)
        if ckpt_path is not None:
            print('#####################################################################')
            print(f'load from ckpt "{ckpt_path}"')
            print('#####################################################################')
            self.init_from_ckpt(ckpt_path)

    @torch.no_grad()
    def get_x_noisy(self, x, t, noise=None):
        noise = default(noise, lambda: torch.randn_like(x))
        continuous_sqrt_alpha_cumprod = None
        if self.diffusion_model.use_continuous_noise:
            continuous_sqrt_alpha_cumprod = self.diffusion_model.sample_continuous_noise_level(x.shape[0], t + 1)
        return self.diffusion_model.q_sample(x_start=x, t=t, noise=noise, continuous_sqrt_alpha_cumprod=continuous_sqrt_alpha_cumprod)

    def forward(self, x_noisy, t, *args, **kwargs):
        return self.model(x_noisy, t)

    @torch.no_grad()
    def get_input(self, batch, k):
        x = batch[k]
        if len(x.shape) == 3:
            x = x[..., None]
        x = rearrange(x, 'b h w c -> b c h w')
        x = x.to(memory_format=torch.contiguous_format).float()
        return x

    @torch.no_grad()
    def get_conditioning(self, batch, k=None):
        if k is None:
            k = self.label_key
        assert k is not None, 'Needs to provide label key'
        targets = batch[k].to(self.device)
        if self.label_key == 'segmentation':
            targets = rearrange(targets, 'b h w c -> b c h w')
            for down in range(self.numd):
                h, w = targets.shape[-2:]
                targets = F.interpolate(targets, size=(h // 2, w // 2), mode='nearest')
        return targets

    def compute_top_k(self, logits, labels, k, reduction='mean'):
        _, top_ks = torch.topk(logits, k, dim=1)
        if reduction == 'mean':
            return (top_ks == labels[:, None]).float().sum(dim=-1).mean().item()
        elif reduction == 'none':
            return (top_ks == labels[:, None]).float().sum(dim=-1)

    def on_train_epoch_start(self):
        self.diffusion_model.model.to('cpu')

    @torch.no_grad()
    def write_logs(self, loss, logits, targets):
        log_prefix = 'train' if self.training else 'val'
        log = {}
        log[f'{log_prefix}/loss'] = loss.mean()
        log[f'{log_prefix}/acc@1'] = self.compute_top_k(logits, targets, k=1, reduction='mean')
        log[f'{log_prefix}/acc@5'] = self.compute_top_k(logits, targets, k=5, reduction='mean')
        self.log_dict(log, prog_bar=False, logger=True, on_step=self.training, on_epoch=True)
        self.log('loss', log[f'{log_prefix}/loss'], prog_bar=True, logger=False)
        self.log('global_step', self.global_step, logger=False, on_epoch=False, prog_bar=True)
        lr = self.optimizers().param_groups[0]['lr']
        self.log('lr_abs', lr, on_step=True, logger=True, on_epoch=False, prog_bar=True)

    def shared_step(self, batch, t=None):
        x, *_ = self.diffusion_model.get_input(batch, k=self.diffusion_model.first_stage_key)
        targets = self.get_conditioning(batch)
        if targets.dim() == 4:
            targets = targets.argmax(dim=1)
        if t is None:
            t = torch.randint(0, self.diffusion_model.num_timesteps, (x.shape[0],), device=self.device).long()
        else:
            t = torch.full(size=(x.shape[0],), fill_value=t, device=self.device).long()
        x_noisy = self.get_x_noisy(x, t)
        logits = self(x_noisy, t)
        loss = F.cross_entropy(logits, targets, reduction='none')
        self.write_logs(loss.detach(), logits.detach(), targets.detach())
        loss = loss.mean()
        return (loss, logits, x_noisy, targets)

    def training_step(self, batch, batch_idx):
        loss, *_ = self.shared_step(batch)
        return loss

    def reset_noise_accs(self):
        self.noisy_acc = {t: {'acc@1': [], 'acc@5': []} for t in range(0, self.diffusion_model.num_timesteps, self.diffusion_model.log_every_t)}

    def on_validation_start(self):
        self.reset_noise_accs()

    @torch.no_grad()
    def validation_step(self, batch, batch_idx):
        loss, *_ = self.shared_step(batch)
        for t in self.noisy_acc:
            _, logits, _, targets = self.shared_step(batch, t)
            self.noisy_acc[t]['acc@1'].append(self.compute_top_k(logits, targets, k=1, reduction='mean'))
            self.noisy_acc[t]['acc@5'].append(self.compute_top_k(logits, targets, k=5, reduction='mean'))
        return loss

    def configure_optimizers(self):
        optimizer = AdamW(self.model.parameters(), lr=self.learning_rate, weight_decay=self.weight_decay)
        if self.use_scheduler:
            scheduler = instantiate_from_config(self.scheduler_config)
            print('Setting up LambdaLR scheduler...')
            scheduler = [{'scheduler': LambdaLR(optimizer, lr_lambda=scheduler.schedule), 'interval': 'step', 'frequency': 1}]
            return ([optimizer], scheduler)
        return optimizer

    @torch.no_grad()
    def log_images(self, batch, N=8, *args, **kwargs):
        log = dict()
        x = self.get_input(batch, self.diffusion_model.first_stage_key)
        log['inputs'] = x
        y = self.get_conditioning(batch)
        if self.label_key == 'class_label':
            y = log_txt_as_img((x.shape[2], x.shape[3]), batch['human_label'])
            log['labels'] = y
        if ismap(y):
            log['labels'] = self.diffusion_model.to_rgb(y)
            for step in range(self.log_steps):
                current_time = step * self.log_time_interval
                _, logits, x_noisy, _ = self.shared_step(batch, t=current_time)
                log[f'inputs@t{current_time}'] = x_noisy
                pred = F.one_hot(logits.argmax(dim=1), num_classes=self.num_classes)
                pred = rearrange(pred, 'b h w c -> b c h w')
                log[f'pred@t{current_time}'] = self.diffusion_model.to_rgb(pred)
        for key in log:
            log[key] = log[key][:N]
        return log

def reset_noise_accs(self):
    self.noisy_acc = {t: {'acc@1': [], 'acc@5': []} for t in range(0, self.diffusion_model.num_timesteps, self.diffusion_model.log_every_t)}

class DDIMSampler(object):

    def __init__(self, model, schedule='linear', **kwargs):
        super().__init__()
        self.model = model
        self.ddpm_num_timesteps = model.num_timesteps
        self.schedule = schedule

    def register_buffer(self, name, attr):
        if type(attr) == torch.Tensor:
            if attr.device != torch.device('cuda'):
                attr = attr.to(torch.device('cuda'))
        setattr(self, name, attr)

    def make_schedule(self, ddim_num_steps, ddim_discretize='uniform', ddim_eta=0.0, verbose=True):
        self.ddim_timesteps = make_ddim_timesteps(ddim_discr_method=ddim_discretize, num_ddim_timesteps=ddim_num_steps, num_ddpm_timesteps=self.ddpm_num_timesteps, verbose=verbose)
        alphas_cumprod = self.model.alphas_cumprod
        assert alphas_cumprod.shape[0] == self.ddpm_num_timesteps, 'alphas have to be defined for each timestep'
        to_torch = lambda x: x.clone().detach().to(torch.float32).to(self.model.device)
        self.register_buffer('betas', to_torch(self.model.betas))
        self.register_buffer('alphas_cumprod', to_torch(alphas_cumprod))
        self.register_buffer('alphas_cumprod_prev', to_torch(self.model.alphas_cumprod_prev))
        self.register_buffer('sqrt_alphas_cumprod', to_torch(np.sqrt(alphas_cumprod.cpu())))
        self.register_buffer('sqrt_one_minus_alphas_cumprod', to_torch(np.sqrt(1.0 - alphas_cumprod.cpu())))
        self.register_buffer('log_one_minus_alphas_cumprod', to_torch(np.log(1.0 - alphas_cumprod.cpu())))
        self.register_buffer('sqrt_recip_alphas_cumprod', to_torch(np.sqrt(1.0 / alphas_cumprod.cpu())))
        self.register_buffer('sqrt_recipm1_alphas_cumprod', to_torch(np.sqrt(1.0 / alphas_cumprod.cpu() - 1)))
        ddim_sigmas, ddim_alphas, ddim_alphas_prev = make_ddim_sampling_parameters(alphacums=alphas_cumprod.cpu(), ddim_timesteps=self.ddim_timesteps, eta=ddim_eta, verbose=verbose)
        self.register_buffer('ddim_sigmas', ddim_sigmas)
        self.register_buffer('ddim_alphas', ddim_alphas)
        self.register_buffer('ddim_alphas_prev', ddim_alphas_prev)
        self.register_buffer('ddim_sqrt_one_minus_alphas', np.sqrt(1.0 - ddim_alphas))
        sigmas_for_original_sampling_steps = ddim_eta * torch.sqrt((1 - self.alphas_cumprod_prev) / (1 - self.alphas_cumprod) * (1 - self.alphas_cumprod / self.alphas_cumprod_prev))
        self.register_buffer('ddim_sigmas_for_original_num_steps', sigmas_for_original_sampling_steps)

    @torch.no_grad()
    def sample(self, S, batch_size, shape, conditioning=None, callback=None, normals_sequence=None, img_callback=None, quantize_x0=False, eta=0.0, mask=None, x0=None, temperature=1.0, noise_dropout=0.0, score_corrector=None, corrector_kwargs=None, verbose=True, x_T=None, log_every_t=100, unconditional_guidance_scale=1.0, unconditional_conditioning=None, **kwargs):
        if conditioning is not None:
            if isinstance(conditioning, dict):
                cbs = conditioning[list(conditioning.keys())[0]].shape[0]
                if cbs != batch_size:
                    print(f'Warning: Got {cbs} conditionings but batch-size is {batch_size}')
            elif conditioning.shape[0] != batch_size:
                print(f'Warning: Got {conditioning.shape[0]} conditionings but batch-size is {batch_size}')
        self.make_schedule(ddim_num_steps=S, ddim_eta=eta, verbose=verbose)
        C, H, W = shape
        size = (batch_size, C, H, W)
        print(f'Data shape for DDIM sampling is {size}, eta {eta}')
        samples, intermediates = self.ddim_sampling(conditioning, size, callback=callback, img_callback=img_callback, quantize_denoised=quantize_x0, mask=mask, x0=x0, ddim_use_original_steps=False, noise_dropout=noise_dropout, temperature=temperature, score_corrector=score_corrector, corrector_kwargs=corrector_kwargs, x_T=x_T, log_every_t=log_every_t, unconditional_guidance_scale=unconditional_guidance_scale, unconditional_conditioning=unconditional_conditioning)
        return (samples, intermediates)

    @torch.no_grad()
    def ddim_sampling(self, cond, shape, x_T=None, ddim_use_original_steps=False, callback=None, timesteps=None, quantize_denoised=False, mask=None, x0=None, img_callback=None, log_every_t=100, temperature=1.0, noise_dropout=0.0, score_corrector=None, corrector_kwargs=None, unconditional_guidance_scale=1.0, unconditional_conditioning=None):
        device = self.model.betas.device
        b = shape[0]
        if x_T is None:
            img = torch.randn(shape, device=device)
        else:
            img = x_T
        if timesteps is None:
            timesteps = self.ddpm_num_timesteps if ddim_use_original_steps else self.ddim_timesteps
        elif timesteps is not None and (not ddim_use_original_steps):
            subset_end = int(min(timesteps / self.ddim_timesteps.shape[0], 1) * self.ddim_timesteps.shape[0]) - 1
            timesteps = self.ddim_timesteps[:subset_end]
        intermediates = {'x_inter': [img], 'pred_x0': [img]}
        time_range = reversed(range(0, timesteps)) if ddim_use_original_steps else np.flip(timesteps)
        total_steps = timesteps if ddim_use_original_steps else timesteps.shape[0]
        print(f'Running DDIM Sampling with {total_steps} timesteps')
        iterator = tqdm(time_range, desc='DDIM Sampler', total=total_steps)
        for i, step in enumerate(iterator):
            index = total_steps - i - 1
            ts = torch.full((b,), step, device=device, dtype=torch.long)
            if mask is not None:
                assert x0 is not None
                img_orig = self.model.q_sample(x0, ts)
                img = img_orig * mask + (1.0 - mask) * img
            outs = self.p_sample_ddim(img, cond, ts, index=index, use_original_steps=ddim_use_original_steps, quantize_denoised=quantize_denoised, temperature=temperature, noise_dropout=noise_dropout, score_corrector=score_corrector, corrector_kwargs=corrector_kwargs, unconditional_guidance_scale=unconditional_guidance_scale, unconditional_conditioning=unconditional_conditioning)
            img, pred_x0 = outs
            if callback:
                callback(i)
            if img_callback:
                img_callback(pred_x0, i)
            if index % log_every_t == 0 or index == total_steps - 1:
                intermediates['x_inter'].append(img)
                intermediates['pred_x0'].append(pred_x0)
        return (img, intermediates)

    @torch.no_grad()
    def p_sample_ddim(self, x, c, t, index, repeat_noise=False, use_original_steps=False, quantize_denoised=False, temperature=1.0, noise_dropout=0.0, score_corrector=None, corrector_kwargs=None, unconditional_guidance_scale=1.0, unconditional_conditioning=None):
        b, *_, device = (*x.shape, x.device)
        if unconditional_conditioning is None or unconditional_guidance_scale == 1.0:
            e_t = self.model.apply_model(x, t, c)
        else:
            x_in = torch.cat([x] * 2)
            t_in = torch.cat([t] * 2)
            c_in = torch.cat([unconditional_conditioning, c])
            e_t_uncond, e_t = self.model.apply_model(x_in, t_in, c_in).chunk(2)
            e_t = e_t_uncond + unconditional_guidance_scale * (e_t - e_t_uncond)
        if score_corrector is not None:
            assert self.model.parameterization == 'eps'
            e_t = score_corrector.modify_score(self.model, e_t, x, t, c, **corrector_kwargs)
        alphas = self.model.alphas_cumprod if use_original_steps else self.ddim_alphas
        alphas_prev = self.model.alphas_cumprod_prev if use_original_steps else self.ddim_alphas_prev
        sqrt_one_minus_alphas = self.model.sqrt_one_minus_alphas_cumprod if use_original_steps else self.ddim_sqrt_one_minus_alphas
        sigmas = self.model.ddim_sigmas_for_original_num_steps if use_original_steps else self.ddim_sigmas
        a_t = torch.full((b, 1, 1, 1), alphas[index], device=device)
        a_prev = torch.full((b, 1, 1, 1), alphas_prev[index], device=device)
        sigma_t = torch.full((b, 1, 1, 1), sigmas[index], device=device)
        sqrt_one_minus_at = torch.full((b, 1, 1, 1), sqrt_one_minus_alphas[index], device=device)
        pred_x0 = (x - sqrt_one_minus_at * e_t) / a_t.sqrt()
        if quantize_denoised:
            pred_x0, _, *_ = self.model.first_stage_model.quantize(pred_x0)
        dir_xt = (1.0 - a_prev - sigma_t ** 2).sqrt() * e_t
        noise = sigma_t * noise_like(x.shape, device, repeat_noise) * temperature
        if noise_dropout > 0.0:
            noise = torch.nn.functional.dropout(noise, p=noise_dropout)
        x_prev = a_prev.sqrt() * pred_x0 + dir_xt + noise
        return (x_prev, pred_x0)

def __init__(self, model, schedule='linear', **kwargs):
    super().__init__()
    self.model = model
    self.ddpm_num_timesteps = model.num_timesteps
    self.schedule = schedule

class DDPM(pl.LightningModule):

    def __init__(self, unet_config, timesteps=1000, beta_schedule='linear', loss_type='l2', ckpt_path=None, ignore_keys=[], load_only_unet=False, monitor='val/loss', use_ema=True, first_stage_key='image', image_size=256, channels=3, log_every_t=100, clip_denoised=True, linear_start=0.0001, linear_end=0.02, cosine_s=0.008, given_betas=None, original_elbo_weight=0.0, v_posterior=0.0, l_simple_weight=1.0, conditioning_key=None, parameterization='eps', scheduler_config=None, use_positional_encodings=False, learn_logvar=False, logvar_init=0.0):
        super().__init__()
        assert parameterization in ['eps', 'x0'], 'currently only supporting "eps" and "x0"'
        self.parameterization = parameterization
        print(f'{self.__class__.__name__}: Running in {self.parameterization}-prediction mode')
        self.cond_stage_model = None
        self.clip_denoised = clip_denoised
        self.log_every_t = log_every_t
        self.first_stage_key = first_stage_key
        self.image_size = image_size
        self.channels = channels
        self.use_positional_encodings = use_positional_encodings
        self.model = DiffusionWrapper(unet_config, conditioning_key)
        count_params(self.model, verbose=True)
        self.use_ema = use_ema
        if self.use_ema:
            self.model_ema = LitEma(self.model)
            print(f'Keeping EMAs of {len(list(self.model_ema.buffers()))}.')
        self.use_scheduler = scheduler_config is not None
        if self.use_scheduler:
            self.scheduler_config = scheduler_config
        self.v_posterior = v_posterior
        self.original_elbo_weight = original_elbo_weight
        self.l_simple_weight = l_simple_weight
        if monitor is not None:
            self.monitor = monitor
        if ckpt_path is not None:
            self.init_from_ckpt(ckpt_path, ignore_keys=ignore_keys, only_model=load_only_unet)
        self.register_schedule(given_betas=given_betas, beta_schedule=beta_schedule, timesteps=timesteps, linear_start=linear_start, linear_end=linear_end, cosine_s=cosine_s)
        self.loss_type = loss_type
        self.learn_logvar = learn_logvar
        self.logvar = torch.full(fill_value=logvar_init, size=(self.num_timesteps,))
        if self.learn_logvar:
            self.logvar = nn.Parameter(self.logvar, requires_grad=True)

    def register_schedule(self, given_betas=None, beta_schedule='linear', timesteps=1000, linear_start=0.0001, linear_end=0.02, cosine_s=0.008):
        if exists(given_betas):
            betas = given_betas
        else:
            betas = make_beta_schedule(beta_schedule, timesteps, linear_start=linear_start, linear_end=linear_end, cosine_s=cosine_s)
        alphas = 1.0 - betas
        alphas_cumprod = np.cumprod(alphas, axis=0)
        alphas_cumprod_prev = np.append(1.0, alphas_cumprod[:-1])
        timesteps, = betas.shape
        self.num_timesteps = int(timesteps)
        self.linear_start = linear_start
        self.linear_end = linear_end
        assert alphas_cumprod.shape[0] == self.num_timesteps, 'alphas have to be defined for each timestep'
        to_torch = partial(torch.tensor, dtype=torch.float32)
        self.register_buffer('betas', to_torch(betas))
        self.register_buffer('alphas_cumprod', to_torch(alphas_cumprod))
        self.register_buffer('alphas_cumprod_prev', to_torch(alphas_cumprod_prev))
        self.register_buffer('sqrt_alphas_cumprod', to_torch(np.sqrt(alphas_cumprod)))
        self.register_buffer('sqrt_one_minus_alphas_cumprod', to_torch(np.sqrt(1.0 - alphas_cumprod)))
        self.register_buffer('log_one_minus_alphas_cumprod', to_torch(np.log(1.0 - alphas_cumprod)))
        self.register_buffer('sqrt_recip_alphas_cumprod', to_torch(np.sqrt(1.0 / alphas_cumprod)))
        self.register_buffer('sqrt_recipm1_alphas_cumprod', to_torch(np.sqrt(1.0 / alphas_cumprod - 1)))
        posterior_variance = (1 - self.v_posterior) * betas * (1.0 - alphas_cumprod_prev) / (1.0 - alphas_cumprod) + self.v_posterior * betas
        self.register_buffer('posterior_variance', to_torch(posterior_variance))
        self.register_buffer('posterior_log_variance_clipped', to_torch(np.log(np.maximum(posterior_variance, 1e-20))))
        self.register_buffer('posterior_mean_coef1', to_torch(betas * np.sqrt(alphas_cumprod_prev) / (1.0 - alphas_cumprod)))
        self.register_buffer('posterior_mean_coef2', to_torch((1.0 - alphas_cumprod_prev) * np.sqrt(alphas) / (1.0 - alphas_cumprod)))
        if self.parameterization == 'eps':
            lvlb_weights = self.betas ** 2 / (2 * self.posterior_variance * to_torch(alphas) * (1 - self.alphas_cumprod))
        elif self.parameterization == 'x0':
            lvlb_weights = 0.5 * np.sqrt(torch.Tensor(alphas_cumprod)) / (2.0 * 1 - torch.Tensor(alphas_cumprod))
        else:
            raise NotImplementedError('mu not supported')
        lvlb_weights[0] = lvlb_weights[1]
        self.register_buffer('lvlb_weights', lvlb_weights, persistent=False)
        assert not torch.isnan(self.lvlb_weights).all()

    @contextmanager
    def ema_scope(self, context=None):
        if self.use_ema:
            self.model_ema.store(self.model.parameters())
            self.model_ema.copy_to(self.model)
            if context is not None:
                print(f'{context}: Switched to EMA weights')
        try:
            yield None
        finally:
            if self.use_ema:
                self.model_ema.restore(self.model.parameters())
                if context is not None:
                    print(f'{context}: Restored training weights')

    def init_from_ckpt(self, path, ignore_keys=list(), only_model=False):
        sd = torch.load(path, map_location='cpu')
        if 'state_dict' in list(sd.keys()):
            sd = sd['state_dict']
        keys = list(sd.keys())
        for k in keys:
            for ik in ignore_keys:
                if k.startswith(ik):
                    print('Deleting key {} from state_dict.'.format(k))
                    del sd[k]
        missing, unexpected = self.load_state_dict(sd, strict=False) if not only_model else self.model.load_state_dict(sd, strict=False)
        print(f'Restored from {path} with {len(missing)} missing and {len(unexpected)} unexpected keys')
        if len(missing) > 0:
            print(f'Missing Keys: {missing}')
        if len(unexpected) > 0:
            print(f'Unexpected Keys: {unexpected}')

    def q_mean_variance(self, x_start, t):
        """
        Get the distribution q(x_t | x_0).
        :param x_start: the [N x C x ...] tensor of noiseless inputs.
        :param t: the number of diffusion steps (minus 1). Here, 0 means one step.
        :return: A tuple (mean, variance, log_variance), all of x_start's shape.
        """
        mean = extract_into_tensor(self.sqrt_alphas_cumprod, t, x_start.shape) * x_start
        variance = extract_into_tensor(1.0 - self.alphas_cumprod, t, x_start.shape)
        log_variance = extract_into_tensor(self.log_one_minus_alphas_cumprod, t, x_start.shape)
        return (mean, variance, log_variance)

    def predict_start_from_noise(self, x_t, t, noise):
        return extract_into_tensor(self.sqrt_recip_alphas_cumprod, t, x_t.shape) * x_t - extract_into_tensor(self.sqrt_recipm1_alphas_cumprod, t, x_t.shape) * noise

    def q_posterior(self, x_start, x_t, t):
        posterior_mean = extract_into_tensor(self.posterior_mean_coef1, t, x_t.shape) * x_start + extract_into_tensor(self.posterior_mean_coef2, t, x_t.shape) * x_t
        posterior_variance = extract_into_tensor(self.posterior_variance, t, x_t.shape)
        posterior_log_variance_clipped = extract_into_tensor(self.posterior_log_variance_clipped, t, x_t.shape)
        return (posterior_mean, posterior_variance, posterior_log_variance_clipped)

    def p_mean_variance(self, x, t, clip_denoised: bool):
        model_out = self.model(x, t)
        if self.parameterization == 'eps':
            x_recon = self.predict_start_from_noise(x, t=t, noise=model_out)
        elif self.parameterization == 'x0':
            x_recon = model_out
        if clip_denoised:
            x_recon.clamp_(-1.0, 1.0)
        model_mean, posterior_variance, posterior_log_variance = self.q_posterior(x_start=x_recon, x_t=x, t=t)
        return (model_mean, posterior_variance, posterior_log_variance)

    @torch.no_grad()
    def p_sample(self, x, t, clip_denoised=True, repeat_noise=False):
        b, *_, device = (*x.shape, x.device)
        model_mean, _, model_log_variance = self.p_mean_variance(x=x, t=t, clip_denoised=clip_denoised)
        noise = noise_like(x.shape, device, repeat_noise)
        nonzero_mask = (1 - (t == 0).float()).reshape(b, *(1,) * (len(x.shape) - 1))
        return model_mean + nonzero_mask * (0.5 * model_log_variance).exp() * noise

    @torch.no_grad()
    def p_sample_loop(self, shape, return_intermediates=False):
        device = self.betas.device
        b = shape[0]
        img = torch.randn(shape, device=device)
        intermediates = [img]
        for i in tqdm(reversed(range(0, self.num_timesteps)), desc='Sampling t', total=self.num_timesteps):
            img = self.p_sample(img, torch.full((b,), i, device=device, dtype=torch.long), clip_denoised=self.clip_denoised)
            if i % self.log_every_t == 0 or i == self.num_timesteps - 1:
                intermediates.append(img)
        if return_intermediates:
            return (img, intermediates)
        return img

    @torch.no_grad()
    def sample(self, batch_size=16, return_intermediates=False):
        image_size = self.image_size
        channels = self.channels
        return self.p_sample_loop((batch_size, channels, image_size, image_size), return_intermediates=return_intermediates)

    def q_sample(self, x_start, t, noise=None):
        noise = default(noise, lambda: torch.randn_like(x_start))
        return extract_into_tensor(self.sqrt_alphas_cumprod, t, x_start.shape) * x_start + extract_into_tensor(self.sqrt_one_minus_alphas_cumprod, t, x_start.shape) * noise

    def get_loss(self, pred, target, mean=True):
        if self.loss_type == 'l1':
            loss = (target - pred).abs()
            if mean:
                loss = loss.mean()
        elif self.loss_type == 'l2':
            if mean:
                loss = torch.nn.functional.mse_loss(target, pred)
            else:
                loss = torch.nn.functional.mse_loss(target, pred, reduction='none')
        else:
            raise NotImplementedError("unknown loss type '{loss_type}'")
        return loss

    def p_losses(self, x_start, t, noise=None):
        noise = default(noise, lambda: torch.randn_like(x_start))
        x_noisy = self.q_sample(x_start=x_start, t=t, noise=noise)
        model_out = self.model(x_noisy, t)
        loss_dict = {}
        if self.parameterization == 'eps':
            target = noise
        elif self.parameterization == 'x0':
            target = x_start
        else:
            raise NotImplementedError(f'Paramterization {self.parameterization} not yet supported')
        loss = self.get_loss(model_out, target, mean=False).mean(dim=[1, 2, 3])
        log_prefix = 'train' if self.training else 'val'
        loss_dict.update({f'{log_prefix}/loss_simple': loss.mean()})
        loss_simple = loss.mean() * self.l_simple_weight
        loss_vlb = (self.lvlb_weights[t] * loss).mean()
        loss_dict.update({f'{log_prefix}/loss_vlb': loss_vlb})
        loss = loss_simple + self.original_elbo_weight * loss_vlb
        loss_dict.update({f'{log_prefix}/loss': loss})
        return (loss, loss_dict)

    def forward(self, x, *args, **kwargs):
        t = torch.randint(0, self.num_timesteps, (x.shape[0],), device=self.device).long()
        return self.p_losses(x, t, *args, **kwargs)

    def get_input(self, batch, k):
        x = batch[k]
        if len(x.shape) == 3:
            x = x[..., None]
        x = rearrange(x, 'b h w c -> b c h w')
        x = x.to(memory_format=torch.contiguous_format).float()
        return x

    def shared_step(self, batch):
        x = self.get_input(batch, self.first_stage_key)
        loss, loss_dict = self(x)
        return (loss, loss_dict)

    def training_step(self, batch, batch_idx):
        loss, loss_dict = self.shared_step(batch)
        self.log_dict(loss_dict, prog_bar=True, logger=True, on_step=True, on_epoch=True)
        self.log('global_step', self.global_step, prog_bar=True, logger=True, on_step=True, on_epoch=False)
        if self.use_scheduler:
            lr = self.optimizers().param_groups[0]['lr']
            self.log('lr_abs', lr, prog_bar=True, logger=True, on_step=True, on_epoch=False)
        return loss

    @torch.no_grad()
    def validation_step(self, batch, batch_idx):
        _, loss_dict_no_ema = self.shared_step(batch)
        with self.ema_scope():
            _, loss_dict_ema = self.shared_step(batch)
            loss_dict_ema = {key + '_ema': loss_dict_ema[key] for key in loss_dict_ema}
        self.log_dict(loss_dict_no_ema, prog_bar=False, logger=True, on_step=False, on_epoch=True)
        self.log_dict(loss_dict_ema, prog_bar=False, logger=True, on_step=False, on_epoch=True)

    def on_train_batch_end(self, *args, **kwargs):
        if self.use_ema:
            self.model_ema(self.model)

    def _get_rows_from_list(self, samples):
        n_imgs_per_row = len(samples)
        denoise_grid = rearrange(samples, 'n b c h w -> b n c h w')
        denoise_grid = rearrange(denoise_grid, 'b n c h w -> (b n) c h w')
        denoise_grid = make_grid(denoise_grid, nrow=n_imgs_per_row)
        return denoise_grid

    @torch.no_grad()
    def log_images(self, batch, N=8, n_row=2, sample=True, return_keys=None, **kwargs):
        log = dict()
        x = self.get_input(batch, self.first_stage_key)
        N = min(x.shape[0], N)
        n_row = min(x.shape[0], n_row)
        x = x.to(self.device)[:N]
        log['inputs'] = x
        diffusion_row = list()
        x_start = x[:n_row]
        for t in range(self.num_timesteps):
            if t % self.log_every_t == 0 or t == self.num_timesteps - 1:
                t = repeat(torch.tensor([t]), '1 -> b', b=n_row)
                t = t.to(self.device).long()
                noise = torch.randn_like(x_start)
                x_noisy = self.q_sample(x_start=x_start, t=t, noise=noise)
                diffusion_row.append(x_noisy)
        log['diffusion_row'] = self._get_rows_from_list(diffusion_row)
        if sample:
            with self.ema_scope('Plotting'):
                samples, denoise_row = self.sample(batch_size=N, return_intermediates=True)
            log['samples'] = samples
            log['denoise_row'] = self._get_rows_from_list(denoise_row)
        if return_keys:
            if np.intersect1d(list(log.keys()), return_keys).shape[0] == 0:
                return log
            else:
                return {key: log[key] for key in return_keys}
        return log

    def configure_optimizers(self):
        lr = self.learning_rate
        params = list(self.model.parameters())
        if self.learn_logvar:
            params = params + [self.logvar]
        opt = torch.optim.AdamW(params, lr=lr)
        return opt

def __init__(self, unet_config, timesteps=1000, beta_schedule='linear', loss_type='l2', ckpt_path=None, ignore_keys=[], load_only_unet=False, monitor='val/loss', use_ema=True, first_stage_key='image', image_size=256, channels=3, log_every_t=100, clip_denoised=True, linear_start=0.0001, linear_end=0.02, cosine_s=0.008, given_betas=None, original_elbo_weight=0.0, v_posterior=0.0, l_simple_weight=1.0, conditioning_key=None, parameterization='eps', scheduler_config=None, use_positional_encodings=False, learn_logvar=False, logvar_init=0.0):
    super().__init__()
    assert parameterization in ['eps', 'x0'], 'currently only supporting "eps" and "x0"'
    self.parameterization = parameterization
    print(f'{self.__class__.__name__}: Running in {self.parameterization}-prediction mode')
    self.cond_stage_model = None
    self.clip_denoised = clip_denoised
    self.log_every_t = log_every_t
    self.first_stage_key = first_stage_key
    self.image_size = image_size
    self.channels = channels
    self.use_positional_encodings = use_positional_encodings
    self.model = DiffusionWrapper(unet_config, conditioning_key)
    count_params(self.model, verbose=True)
    self.use_ema = use_ema
    if self.use_ema:
        self.model_ema = LitEma(self.model)
        print(f'Keeping EMAs of {len(list(self.model_ema.buffers()))}.')
    self.use_scheduler = scheduler_config is not None
    if self.use_scheduler:
        self.scheduler_config = scheduler_config
    self.v_posterior = v_posterior
    self.original_elbo_weight = original_elbo_weight
    self.l_simple_weight = l_simple_weight
    if monitor is not None:
        self.monitor = monitor
    if ckpt_path is not None:
        self.init_from_ckpt(ckpt_path, ignore_keys=ignore_keys, only_model=load_only_unet)
    self.register_schedule(given_betas=given_betas, beta_schedule=beta_schedule, timesteps=timesteps, linear_start=linear_start, linear_end=linear_end, cosine_s=cosine_s)
    self.loss_type = loss_type
    self.learn_logvar = learn_logvar
    self.logvar = torch.full(fill_value=logvar_init, size=(self.num_timesteps,))
    if self.learn_logvar:
        self.logvar = nn.Parameter(self.logvar, requires_grad=True)

class LatentDiffusion(DDPM):
    """main class"""

    def __init__(self, first_stage_config, cond_stage_config, num_timesteps_cond=None, cond_stage_key='image', cond_stage_trainable=False, concat_mode=True, cond_stage_forward=None, conditioning_key=None, scale_factor=1.0, scale_by_std=False, *args, **kwargs):
        self.num_timesteps_cond = default(num_timesteps_cond, 1)
        self.scale_by_std = scale_by_std
        assert self.num_timesteps_cond <= kwargs['timesteps']
        if conditioning_key is None:
            conditioning_key = 'concat' if concat_mode else 'crossattn'
        if cond_stage_config == '__is_unconditional__':
            conditioning_key = None
        ckpt_path = kwargs.pop('ckpt_path', None)
        ignore_keys = kwargs.pop('ignore_keys', [])
        super().__init__(*args, conditioning_key=conditioning_key, **kwargs)
        self.concat_mode = concat_mode
        self.cond_stage_trainable = cond_stage_trainable
        self.cond_stage_key = cond_stage_key
        try:
            self.num_downs = len(first_stage_config.params.ddconfig.ch_mult) - 1
        except:
            self.num_downs = 0
        if not scale_by_std:
            self.scale_factor = scale_factor
        else:
            self.register_buffer('scale_factor', torch.tensor(scale_factor))
        self.instantiate_first_stage(first_stage_config)
        self.instantiate_cond_stage(cond_stage_config)
        self.cond_stage_forward = cond_stage_forward
        self.clip_denoised = False
        self.bbox_tokenizer = None
        self.restarted_from_ckpt = False
        if ckpt_path is not None:
            self.init_from_ckpt(ckpt_path, ignore_keys)
            self.restarted_from_ckpt = True

    def make_cond_schedule(self):
        self.cond_ids = torch.full(size=(self.num_timesteps,), fill_value=self.num_timesteps - 1, dtype=torch.long)
        ids = torch.round(torch.linspace(0, self.num_timesteps - 1, self.num_timesteps_cond)).long()
        self.cond_ids[:self.num_timesteps_cond] = ids

    @rank_zero_only
    @torch.no_grad()
    def on_train_batch_start(self, batch, batch_idx, dataloader_idx):
        if self.scale_by_std and self.current_epoch == 0 and (self.global_step == 0) and (batch_idx == 0) and (not self.restarted_from_ckpt):
            assert self.scale_factor == 1.0, 'rather not use custom rescaling and std-rescaling simultaneously'
            print('### USING STD-RESCALING ###')
            x = super().get_input(batch, self.first_stage_key)
            x = x.to(self.device)
            encoder_posterior = self.encode_first_stage(x)
            z = self.get_first_stage_encoding(encoder_posterior).detach()
            del self.scale_factor
            self.register_buffer('scale_factor', 1.0 / z.flatten().std())
            print(f'setting self.scale_factor to {self.scale_factor}')
            print('### USING STD-RESCALING ###')

    def register_schedule(self, given_betas=None, beta_schedule='linear', timesteps=1000, linear_start=0.0001, linear_end=0.02, cosine_s=0.008):
        super().register_schedule(given_betas, beta_schedule, timesteps, linear_start, linear_end, cosine_s)
        self.shorten_cond_schedule = self.num_timesteps_cond > 1
        if self.shorten_cond_schedule:
            self.make_cond_schedule()

    def instantiate_first_stage(self, config):
        model = instantiate_from_config(config)
        self.first_stage_model = model.eval()
        self.first_stage_model.train = disabled_train
        for param in self.first_stage_model.parameters():
            param.requires_grad = False

    def instantiate_cond_stage(self, config):
        if not self.cond_stage_trainable:
            if config == '__is_first_stage__':
                print('Using first stage also as cond stage.')
                self.cond_stage_model = self.first_stage_model
            elif config == '__is_unconditional__':
                print(f'Training {self.__class__.__name__} as an unconditional model.')
                self.cond_stage_model = None
            else:
                model = instantiate_from_config(config)
                self.cond_stage_model = model.eval()
                self.cond_stage_model.train = disabled_train
                for param in self.cond_stage_model.parameters():
                    param.requires_grad = False
        else:
            assert config != '__is_first_stage__'
            assert config != '__is_unconditional__'
            model = instantiate_from_config(config)
            self.cond_stage_model = model

    def _get_denoise_row_from_list(self, samples, desc='', force_no_decoder_quantization=False):
        denoise_row = []
        for zd in tqdm(samples, desc=desc):
            denoise_row.append(self.decode_first_stage(zd.to(self.device), force_not_quantize=force_no_decoder_quantization))
        n_imgs_per_row = len(denoise_row)
        denoise_row = torch.stack(denoise_row)
        denoise_grid = rearrange(denoise_row, 'n b c h w -> b n c h w')
        denoise_grid = rearrange(denoise_grid, 'b n c h w -> (b n) c h w')
        denoise_grid = make_grid(denoise_grid, nrow=n_imgs_per_row)
        return denoise_grid

    def get_first_stage_encoding(self, encoder_posterior):
        if isinstance(encoder_posterior, DiagonalGaussianDistribution):
            z = encoder_posterior.sample()
        elif isinstance(encoder_posterior, torch.Tensor):
            z = encoder_posterior
        else:
            raise NotImplementedError(f"encoder_posterior of type '{type(encoder_posterior)}' not yet implemented")
        return self.scale_factor * z

    def get_learned_conditioning(self, c):
        if self.cond_stage_forward is None:
            if hasattr(self.cond_stage_model, 'encode') and callable(self.cond_stage_model.encode):
                c = self.cond_stage_model.encode(c)
                if isinstance(c, DiagonalGaussianDistribution):
                    c = c.mode()
            else:
                c = self.cond_stage_model(c)
        else:
            assert hasattr(self.cond_stage_model, self.cond_stage_forward)
            c = getattr(self.cond_stage_model, self.cond_stage_forward)(c)
        return c

    def meshgrid(self, h, w):
        y = torch.arange(0, h).view(h, 1, 1).repeat(1, w, 1)
        x = torch.arange(0, w).view(1, w, 1).repeat(h, 1, 1)
        arr = torch.cat([y, x], dim=-1)
        return arr

    def delta_border(self, h, w):
        """
        :param h: height
        :param w: width
        :return: normalized distance to image border,
         wtith min distance = 0 at border and max dist = 0.5 at image center
        """
        lower_right_corner = torch.tensor([h - 1, w - 1]).view(1, 1, 2)
        arr = self.meshgrid(h, w) / lower_right_corner
        dist_left_up = torch.min(arr, dim=-1, keepdims=True)[0]
        dist_right_down = torch.min(1 - arr, dim=-1, keepdims=True)[0]
        edge_dist = torch.min(torch.cat([dist_left_up, dist_right_down], dim=-1), dim=-1)[0]
        return edge_dist

    def get_weighting(self, h, w, Ly, Lx, device):
        weighting = self.delta_border(h, w)
        weighting = torch.clip(weighting, self.split_input_params['clip_min_weight'], self.split_input_params['clip_max_weight'])
        weighting = weighting.view(1, h * w, 1).repeat(1, 1, Ly * Lx).to(device)
        if self.split_input_params['tie_braker']:
            L_weighting = self.delta_border(Ly, Lx)
            L_weighting = torch.clip(L_weighting, self.split_input_params['clip_min_tie_weight'], self.split_input_params['clip_max_tie_weight'])
            L_weighting = L_weighting.view(1, 1, Ly * Lx).to(device)
            weighting = weighting * L_weighting
        return weighting

    def get_fold_unfold(self, x, kernel_size, stride, uf=1, df=1):
        """
        :param x: img of size (bs, c, h, w)
        :return: n img crops of size (n, bs, c, kernel_size[0], kernel_size[1])
        """
        bs, nc, h, w = x.shape
        Ly = (h - kernel_size[0]) // stride[0] + 1
        Lx = (w - kernel_size[1]) // stride[1] + 1
        if uf == 1 and df == 1:
            fold_params = dict(kernel_size=kernel_size, dilation=1, padding=0, stride=stride)
            unfold = torch.nn.Unfold(**fold_params)
            fold = torch.nn.Fold(output_size=x.shape[2:], **fold_params)
            weighting = self.get_weighting(kernel_size[0], kernel_size[1], Ly, Lx, x.device).to(x.dtype)
            normalization = fold(weighting).view(1, 1, h, w)
            weighting = weighting.view((1, 1, kernel_size[0], kernel_size[1], Ly * Lx))
        elif uf > 1 and df == 1:
            fold_params = dict(kernel_size=kernel_size, dilation=1, padding=0, stride=stride)
            unfold = torch.nn.Unfold(**fold_params)
            fold_params2 = dict(kernel_size=(kernel_size[0] * uf, kernel_size[0] * uf), dilation=1, padding=0, stride=(stride[0] * uf, stride[1] * uf))
            fold = torch.nn.Fold(output_size=(x.shape[2] * uf, x.shape[3] * uf), **fold_params2)
            weighting = self.get_weighting(kernel_size[0] * uf, kernel_size[1] * uf, Ly, Lx, x.device).to(x.dtype)
            normalization = fold(weighting).view(1, 1, h * uf, w * uf)
            weighting = weighting.view((1, 1, kernel_size[0] * uf, kernel_size[1] * uf, Ly * Lx))
        elif df > 1 and uf == 1:
            fold_params = dict(kernel_size=kernel_size, dilation=1, padding=0, stride=stride)
            unfold = torch.nn.Unfold(**fold_params)
            fold_params2 = dict(kernel_size=(kernel_size[0] // df, kernel_size[0] // df), dilation=1, padding=0, stride=(stride[0] // df, stride[1] // df))
            fold = torch.nn.Fold(output_size=(x.shape[2] // df, x.shape[3] // df), **fold_params2)
            weighting = self.get_weighting(kernel_size[0] // df, kernel_size[1] // df, Ly, Lx, x.device).to(x.dtype)
            normalization = fold(weighting).view(1, 1, h // df, w // df)
            weighting = weighting.view((1, 1, kernel_size[0] // df, kernel_size[1] // df, Ly * Lx))
        else:
            raise NotImplementedError
        return (fold, unfold, normalization, weighting)

    @torch.no_grad()
    def get_input(self, batch, k, return_first_stage_outputs=False, force_c_encode=False, cond_key=None, return_original_cond=False, bs=None):
        x = super().get_input(batch, k)
        if bs is not None:
            x = x[:bs]
        x = x.to(self.device)
        encoder_posterior = self.encode_first_stage(x)
        z = self.get_first_stage_encoding(encoder_posterior).detach()
        if self.model.conditioning_key is not None:
            if cond_key is None:
                cond_key = self.cond_stage_key
            if cond_key != self.first_stage_key:
                if cond_key in ['caption', 'coordinates_bbox']:
                    xc = batch[cond_key]
                elif cond_key == 'class_label':
                    xc = batch
                else:
                    xc = super().get_input(batch, cond_key).to(self.device)
            else:
                xc = x
            if not self.cond_stage_trainable or force_c_encode:
                if isinstance(xc, dict) or isinstance(xc, list):
                    c = self.get_learned_conditioning(xc)
                else:
                    c = self.get_learned_conditioning(xc.to(self.device))
            else:
                c = xc
            if bs is not None:
                c = c[:bs]
            if self.use_positional_encodings:
                pos_x, pos_y = self.compute_latent_shifts(batch)
                ckey = __conditioning_keys__[self.model.conditioning_key]
                c = {ckey: c, 'pos_x': pos_x, 'pos_y': pos_y}
        else:
            c = None
            xc = None
            if self.use_positional_encodings:
                pos_x, pos_y = self.compute_latent_shifts(batch)
                c = {'pos_x': pos_x, 'pos_y': pos_y}
        out = [z, c]
        if return_first_stage_outputs:
            xrec = self.decode_first_stage(z)
            out.extend([x, xrec])
        if return_original_cond:
            out.append(xc)
        return out

    @torch.no_grad()
    def decode_first_stage(self, z, predict_cids=False, force_not_quantize=False):
        if predict_cids:
            if z.dim() == 4:
                z = torch.argmax(z.exp(), dim=1).long()
            z = self.first_stage_model.quantize.get_codebook_entry(z, shape=None)
            z = rearrange(z, 'b h w c -> b c h w').contiguous()
        z = 1.0 / self.scale_factor * z
        if hasattr(self, 'split_input_params'):
            if self.split_input_params['patch_distributed_vq']:
                ks = self.split_input_params['ks']
                stride = self.split_input_params['stride']
                uf = self.split_input_params['vqf']
                bs, nc, h, w = z.shape
                if ks[0] > h or ks[1] > w:
                    ks = (min(ks[0], h), min(ks[1], w))
                    print('reducing Kernel')
                if stride[0] > h or stride[1] > w:
                    stride = (min(stride[0], h), min(stride[1], w))
                    print('reducing stride')
                fold, unfold, normalization, weighting = self.get_fold_unfold(z, ks, stride, uf=uf)
                z = unfold(z)
                z = z.view((z.shape[0], -1, ks[0], ks[1], z.shape[-1]))
                if isinstance(self.first_stage_model, VQModelInterface):
                    output_list = [self.first_stage_model.decode(z[:, :, :, :, i], force_not_quantize=predict_cids or force_not_quantize) for i in range(z.shape[-1])]
                else:
                    output_list = [self.first_stage_model.decode(z[:, :, :, :, i]) for i in range(z.shape[-1])]
                o = torch.stack(output_list, axis=-1)
                o = o * weighting
                o = o.view((o.shape[0], -1, o.shape[-1]))
                decoded = fold(o)
                decoded = decoded / normalization
                return decoded
            elif isinstance(self.first_stage_model, VQModelInterface):
                return self.first_stage_model.decode(z, force_not_quantize=predict_cids or force_not_quantize)
            else:
                return self.first_stage_model.decode(z)
        elif isinstance(self.first_stage_model, VQModelInterface):
            return self.first_stage_model.decode(z, force_not_quantize=predict_cids or force_not_quantize)
        else:
            return self.first_stage_model.decode(z)

    def differentiable_decode_first_stage(self, z, predict_cids=False, force_not_quantize=False):
        if predict_cids:
            if z.dim() == 4:
                z = torch.argmax(z.exp(), dim=1).long()
            z = self.first_stage_model.quantize.get_codebook_entry(z, shape=None)
            z = rearrange(z, 'b h w c -> b c h w').contiguous()
        z = 1.0 / self.scale_factor * z
        if hasattr(self, 'split_input_params'):
            if self.split_input_params['patch_distributed_vq']:
                ks = self.split_input_params['ks']
                stride = self.split_input_params['stride']
                uf = self.split_input_params['vqf']
                bs, nc, h, w = z.shape
                if ks[0] > h or ks[1] > w:
                    ks = (min(ks[0], h), min(ks[1], w))
                    print('reducing Kernel')
                if stride[0] > h or stride[1] > w:
                    stride = (min(stride[0], h), min(stride[1], w))
                    print('reducing stride')
                fold, unfold, normalization, weighting = self.get_fold_unfold(z, ks, stride, uf=uf)
                z = unfold(z)
                z = z.view((z.shape[0], -1, ks[0], ks[1], z.shape[-1]))
                if isinstance(self.first_stage_model, VQModelInterface):
                    output_list = [self.first_stage_model.decode(z[:, :, :, :, i], force_not_quantize=predict_cids or force_not_quantize) for i in range(z.shape[-1])]
                else:
                    output_list = [self.first_stage_model.decode(z[:, :, :, :, i]) for i in range(z.shape[-1])]
                o = torch.stack(output_list, axis=-1)
                o = o * weighting
                o = o.view((o.shape[0], -1, o.shape[-1]))
                decoded = fold(o)
                decoded = decoded / normalization
                return decoded
            elif isinstance(self.first_stage_model, VQModelInterface):
                return self.first_stage_model.decode(z, force_not_quantize=predict_cids or force_not_quantize)
            else:
                return self.first_stage_model.decode(z)
        elif isinstance(self.first_stage_model, VQModelInterface):
            return self.first_stage_model.decode(z, force_not_quantize=predict_cids or force_not_quantize)
        else:
            return self.first_stage_model.decode(z)

    @torch.no_grad()
    def encode_first_stage(self, x):
        if hasattr(self, 'split_input_params'):
            if self.split_input_params['patch_distributed_vq']:
                ks = self.split_input_params['ks']
                stride = self.split_input_params['stride']
                df = self.split_input_params['vqf']
                self.split_input_params['original_image_size'] = x.shape[-2:]
                bs, nc, h, w = x.shape
                if ks[0] > h or ks[1] > w:
                    ks = (min(ks[0], h), min(ks[1], w))
                    print('reducing Kernel')
                if stride[0] > h or stride[1] > w:
                    stride = (min(stride[0], h), min(stride[1], w))
                    print('reducing stride')
                fold, unfold, normalization, weighting = self.get_fold_unfold(x, ks, stride, df=df)
                z = unfold(x)
                z = z.view((z.shape[0], -1, ks[0], ks[1], z.shape[-1]))
                output_list = [self.first_stage_model.encode(z[:, :, :, :, i]) for i in range(z.shape[-1])]
                o = torch.stack(output_list, axis=-1)
                o = o * weighting
                o = o.view((o.shape[0], -1, o.shape[-1]))
                decoded = fold(o)
                decoded = decoded / normalization
                return decoded
            else:
                return self.first_stage_model.encode(x)
        else:
            return self.first_stage_model.encode(x)

    def shared_step(self, batch, **kwargs):
        x, c = self.get_input(batch, self.first_stage_key)
        loss = self(x, c)
        return loss

    def forward(self, x, c, *args, **kwargs):
        t = torch.randint(0, self.num_timesteps, (x.shape[0],), device=self.device).long()
        if self.model.conditioning_key is not None:
            assert c is not None
            if self.cond_stage_trainable:
                c = self.get_learned_conditioning(c)
            if self.shorten_cond_schedule:
                tc = self.cond_ids[t].to(self.device)
                c = self.q_sample(x_start=c, t=tc, noise=torch.randn_like(c.float()))
        return self.p_losses(x, c, t, *args, **kwargs)

    def _rescale_annotations(self, bboxes, crop_coordinates):

        def rescale_bbox(bbox):
            x0 = clamp((bbox[0] - crop_coordinates[0]) / crop_coordinates[2])
            y0 = clamp((bbox[1] - crop_coordinates[1]) / crop_coordinates[3])
            w = min(bbox[2] / crop_coordinates[2], 1 - x0)
            h = min(bbox[3] / crop_coordinates[3], 1 - y0)
            return (x0, y0, w, h)
        return [rescale_bbox(b) for b in bboxes]

    def apply_model(self, x_noisy, t, cond, return_ids=False):
        if isinstance(cond, dict):
            pass
        else:
            if not isinstance(cond, list):
                cond = [cond]
            key = 'c_concat' if self.model.conditioning_key == 'concat' else 'c_crossattn'
            cond = {key: cond}
        if hasattr(self, 'split_input_params'):
            assert len(cond) == 1
            assert not return_ids
            ks = self.split_input_params['ks']
            stride = self.split_input_params['stride']
            h, w = x_noisy.shape[-2:]
            fold, unfold, normalization, weighting = self.get_fold_unfold(x_noisy, ks, stride)
            z = unfold(x_noisy)
            z = z.view((z.shape[0], -1, ks[0], ks[1], z.shape[-1]))
            z_list = [z[:, :, :, :, i] for i in range(z.shape[-1])]
            if self.cond_stage_key in ['image', 'LR_image', 'segmentation', 'bbox_img'] and self.model.conditioning_key:
                c_key = next(iter(cond.keys()))
                c = next(iter(cond.values()))
                assert len(c) == 1
                c = c[0]
                c = unfold(c)
                c = c.view((c.shape[0], -1, ks[0], ks[1], c.shape[-1]))
                cond_list = [{c_key: [c[:, :, :, :, i]]} for i in range(c.shape[-1])]
            elif self.cond_stage_key == 'coordinates_bbox':
                assert 'original_image_size' in self.split_input_params, 'BoudingBoxRescaling is missing original_image_size'
                n_patches_per_row = int((w - ks[0]) / stride[0] + 1)
                full_img_h, full_img_w = self.split_input_params['original_image_size']
                num_downs = self.first_stage_model.encoder.num_resolutions - 1
                rescale_latent = 2 ** num_downs
                tl_patch_coordinates = [(rescale_latent * stride[0] * (patch_nr % n_patches_per_row) / full_img_w, rescale_latent * stride[1] * (patch_nr // n_patches_per_row) / full_img_h) for patch_nr in range(z.shape[-1])]
                patch_limits = [(x_tl, y_tl, rescale_latent * ks[0] / full_img_w, rescale_latent * ks[1] / full_img_h) for x_tl, y_tl in tl_patch_coordinates]
                patch_limits_tknzd = [torch.LongTensor(self.bbox_tokenizer._crop_encoder(bbox))[None].to(self.device) for bbox in patch_limits]
                print(patch_limits_tknzd[0].shape)
                assert isinstance(cond, dict), 'cond must be dict to be fed into model'
                cut_cond = cond['c_crossattn'][0][..., :-2].to(self.device)
                print(cut_cond.shape)
                adapted_cond = torch.stack([torch.cat([cut_cond, p], dim=1) for p in patch_limits_tknzd])
                adapted_cond = rearrange(adapted_cond, 'l b n -> (l b) n')
                print(adapted_cond.shape)
                adapted_cond = self.get_learned_conditioning(adapted_cond)
                print(adapted_cond.shape)
                adapted_cond = rearrange(adapted_cond, '(l b) n d -> l b n d', l=z.shape[-1])
                print(adapted_cond.shape)
                cond_list = [{'c_crossattn': [e]} for e in adapted_cond]
            else:
                cond_list = [cond for i in range(z.shape[-1])]
            output_list = [self.model(z_list[i], t, **cond_list[i]) for i in range(z.shape[-1])]
            assert not isinstance(output_list[0], tuple)
            o = torch.stack(output_list, axis=-1)
            o = o * weighting
            o = o.view((o.shape[0], -1, o.shape[-1]))
            x_recon = fold(o) / normalization
        else:
            x_recon = self.model(x_noisy, t, **cond)
        if isinstance(x_recon, tuple) and (not return_ids):
            return x_recon[0]
        else:
            return x_recon

    def _predict_eps_from_xstart(self, x_t, t, pred_xstart):
        return (extract_into_tensor(self.sqrt_recip_alphas_cumprod, t, x_t.shape) * x_t - pred_xstart) / extract_into_tensor(self.sqrt_recipm1_alphas_cumprod, t, x_t.shape)

    def _prior_bpd(self, x_start):
        """
        Get the prior KL term for the variational lower-bound, measured in
        bits-per-dim.
        This term can't be optimized, as it only depends on the encoder.
        :param x_start: the [N x C x ...] tensor of inputs.
        :return: a batch of [N] KL values (in bits), one per batch element.
        """
        batch_size = x_start.shape[0]
        t = torch.tensor([self.num_timesteps - 1] * batch_size, device=x_start.device)
        qt_mean, _, qt_log_variance = self.q_mean_variance(x_start, t)
        kl_prior = normal_kl(mean1=qt_mean, logvar1=qt_log_variance, mean2=0.0, logvar2=0.0)
        return mean_flat(kl_prior) / np.log(2.0)

    def p_losses(self, x_start, cond, t, noise=None):
        noise = default(noise, lambda: torch.randn_like(x_start))
        x_noisy = self.q_sample(x_start=x_start, t=t, noise=noise)
        model_output = self.apply_model(x_noisy, t, cond)
        loss_dict = {}
        prefix = 'train' if self.training else 'val'
        if self.parameterization == 'x0':
            target = x_start
        elif self.parameterization == 'eps':
            target = noise
        else:
            raise NotImplementedError()
        loss_simple = self.get_loss(model_output, target, mean=False).mean([1, 2, 3])
        loss_dict.update({f'{prefix}/loss_simple': loss_simple.mean()})
        logvar_t = self.logvar[t].to(self.device)
        loss = loss_simple / torch.exp(logvar_t) + logvar_t
        if self.learn_logvar:
            loss_dict.update({f'{prefix}/loss_gamma': loss.mean()})
            loss_dict.update({'logvar': self.logvar.data.mean()})
        loss = self.l_simple_weight * loss.mean()
        loss_vlb = self.get_loss(model_output, target, mean=False).mean(dim=(1, 2, 3))
        loss_vlb = (self.lvlb_weights[t] * loss_vlb).mean()
        loss_dict.update({f'{prefix}/loss_vlb': loss_vlb})
        loss += self.original_elbo_weight * loss_vlb
        loss_dict.update({f'{prefix}/loss': loss})
        return (loss, loss_dict)

    def p_mean_variance(self, x, c, t, clip_denoised: bool, return_codebook_ids=False, quantize_denoised=False, return_x0=False, score_corrector=None, corrector_kwargs=None):
        t_in = t
        model_out = self.apply_model(x, t_in, c, return_ids=return_codebook_ids)
        if score_corrector is not None:
            assert self.parameterization == 'eps'
            model_out = score_corrector.modify_score(self, model_out, x, t, c, **corrector_kwargs)
        if return_codebook_ids:
            model_out, logits = model_out
        if self.parameterization == 'eps':
            x_recon = self.predict_start_from_noise(x, t=t, noise=model_out)
        elif self.parameterization == 'x0':
            x_recon = model_out
        else:
            raise NotImplementedError()
        if clip_denoised:
            x_recon.clamp_(-1.0, 1.0)
        if quantize_denoised:
            x_recon, _, [_, _, indices] = self.first_stage_model.quantize(x_recon)
        model_mean, posterior_variance, posterior_log_variance = self.q_posterior(x_start=x_recon, x_t=x, t=t)
        if return_codebook_ids:
            return (model_mean, posterior_variance, posterior_log_variance, logits)
        elif return_x0:
            return (model_mean, posterior_variance, posterior_log_variance, x_recon)
        else:
            return (model_mean, posterior_variance, posterior_log_variance)

    @torch.no_grad()
    def p_sample(self, x, c, t, clip_denoised=False, repeat_noise=False, return_codebook_ids=False, quantize_denoised=False, return_x0=False, temperature=1.0, noise_dropout=0.0, score_corrector=None, corrector_kwargs=None):
        b, *_, device = (*x.shape, x.device)
        outputs = self.p_mean_variance(x=x, c=c, t=t, clip_denoised=clip_denoised, return_codebook_ids=return_codebook_ids, quantize_denoised=quantize_denoised, return_x0=return_x0, score_corrector=score_corrector, corrector_kwargs=corrector_kwargs)
        if return_codebook_ids:
            raise DeprecationWarning('Support dropped.')
            model_mean, _, model_log_variance, logits = outputs
        elif return_x0:
            model_mean, _, model_log_variance, x0 = outputs
        else:
            model_mean, _, model_log_variance = outputs
        noise = noise_like(x.shape, device, repeat_noise) * temperature
        if noise_dropout > 0.0:
            noise = torch.nn.functional.dropout(noise, p=noise_dropout)
        nonzero_mask = (1 - (t == 0).float()).reshape(b, *(1,) * (len(x.shape) - 1))
        if return_codebook_ids:
            return (model_mean + nonzero_mask * (0.5 * model_log_variance).exp() * noise, logits.argmax(dim=1))
        if return_x0:
            return (model_mean + nonzero_mask * (0.5 * model_log_variance).exp() * noise, x0)
        else:
            return model_mean + nonzero_mask * (0.5 * model_log_variance).exp() * noise

    @torch.no_grad()
    def progressive_denoising(self, cond, shape, verbose=True, callback=None, quantize_denoised=False, img_callback=None, mask=None, x0=None, temperature=1.0, noise_dropout=0.0, score_corrector=None, corrector_kwargs=None, batch_size=None, x_T=None, start_T=None, log_every_t=None):
        if not log_every_t:
            log_every_t = self.log_every_t
        timesteps = self.num_timesteps
        if batch_size is not None:
            b = batch_size if batch_size is not None else shape[0]
            shape = [batch_size] + list(shape)
        else:
            b = batch_size = shape[0]
        if x_T is None:
            img = torch.randn(shape, device=self.device)
        else:
            img = x_T
        intermediates = []
        if cond is not None:
            if isinstance(cond, dict):
                cond = {key: cond[key][:batch_size] if not isinstance(cond[key], list) else list(map(lambda x: x[:batch_size], cond[key])) for key in cond}
            else:
                cond = [c[:batch_size] for c in cond] if isinstance(cond, list) else cond[:batch_size]
        if start_T is not None:
            timesteps = min(timesteps, start_T)
        iterator = tqdm(reversed(range(0, timesteps)), desc='Progressive Generation', total=timesteps) if verbose else reversed(range(0, timesteps))
        if type(temperature) == float:
            temperature = [temperature] * timesteps
        for i in iterator:
            ts = torch.full((b,), i, device=self.device, dtype=torch.long)
            if self.shorten_cond_schedule:
                assert self.model.conditioning_key != 'hybrid'
                tc = self.cond_ids[ts].to(cond.device)
                cond = self.q_sample(x_start=cond, t=tc, noise=torch.randn_like(cond))
            img, x0_partial = self.p_sample(img, cond, ts, clip_denoised=self.clip_denoised, quantize_denoised=quantize_denoised, return_x0=True, temperature=temperature[i], noise_dropout=noise_dropout, score_corrector=score_corrector, corrector_kwargs=corrector_kwargs)
            if mask is not None:
                assert x0 is not None
                img_orig = self.q_sample(x0, ts)
                img = img_orig * mask + (1.0 - mask) * img
            if i % log_every_t == 0 or i == timesteps - 1:
                intermediates.append(x0_partial)
            if callback:
                callback(i)
            if img_callback:
                img_callback(img, i)
        return (img, intermediates)

    @torch.no_grad()
    def p_sample_loop(self, cond, shape, return_intermediates=False, x_T=None, verbose=True, callback=None, timesteps=None, quantize_denoised=False, mask=None, x0=None, img_callback=None, start_T=None, log_every_t=None):
        if not log_every_t:
            log_every_t = self.log_every_t
        device = self.betas.device
        b = shape[0]
        if x_T is None:
            img = torch.randn(shape, device=device)
        else:
            img = x_T
        intermediates = [img]
        if timesteps is None:
            timesteps = self.num_timesteps
        if start_T is not None:
            timesteps = min(timesteps, start_T)
        iterator = tqdm(reversed(range(0, timesteps)), desc='Sampling t', total=timesteps) if verbose else reversed(range(0, timesteps))
        if mask is not None:
            assert x0 is not None
            assert x0.shape[2:3] == mask.shape[2:3]
        for i in iterator:
            ts = torch.full((b,), i, device=device, dtype=torch.long)
            if self.shorten_cond_schedule:
                assert self.model.conditioning_key != 'hybrid'
                tc = self.cond_ids[ts].to(cond.device)
                cond = self.q_sample(x_start=cond, t=tc, noise=torch.randn_like(cond))
            img = self.p_sample(img, cond, ts, clip_denoised=self.clip_denoised, quantize_denoised=quantize_denoised)
            if mask is not None:
                img_orig = self.q_sample(x0, ts)
                img = img_orig * mask + (1.0 - mask) * img
            if i % log_every_t == 0 or i == timesteps - 1:
                intermediates.append(img)
            if callback:
                callback(i)
            if img_callback:
                img_callback(img, i)
        if return_intermediates:
            return (img, intermediates)
        return img

    @torch.no_grad()
    def sample(self, cond, batch_size=16, return_intermediates=False, x_T=None, verbose=True, timesteps=None, quantize_denoised=False, mask=None, x0=None, shape=None, **kwargs):
        if shape is None:
            shape = (batch_size, self.channels, self.image_size, self.image_size)
        if cond is not None:
            if isinstance(cond, dict):
                cond = {key: cond[key][:batch_size] if not isinstance(cond[key], list) else list(map(lambda x: x[:batch_size], cond[key])) for key in cond}
            else:
                cond = [c[:batch_size] for c in cond] if isinstance(cond, list) else cond[:batch_size]
        return self.p_sample_loop(cond, shape, return_intermediates=return_intermediates, x_T=x_T, verbose=verbose, timesteps=timesteps, quantize_denoised=quantize_denoised, mask=mask, x0=x0)

    @torch.no_grad()
    def sample_log(self, cond, batch_size, ddim, ddim_steps, **kwargs):
        if ddim:
            ddim_sampler = DDIMSampler(self)
            shape = (self.channels, self.image_size, self.image_size)
            samples, intermediates = ddim_sampler.sample(ddim_steps, batch_size, shape, cond, verbose=False, **kwargs)
        else:
            samples, intermediates = self.sample(cond=cond, batch_size=batch_size, return_intermediates=True, **kwargs)
        return (samples, intermediates)

    @torch.no_grad()
    def log_images(self, batch, N=8, n_row=4, sample=True, ddim_steps=200, ddim_eta=1.0, return_keys=None, quantize_denoised=True, inpaint=True, plot_denoise_rows=False, plot_progressive_rows=True, plot_diffusion_rows=True, **kwargs):
        use_ddim = ddim_steps is not None
        log = dict()
        z, c, x, xrec, xc = self.get_input(batch, self.first_stage_key, return_first_stage_outputs=True, force_c_encode=True, return_original_cond=True, bs=N)
        N = min(x.shape[0], N)
        n_row = min(x.shape[0], n_row)
        log['inputs'] = x
        log['reconstruction'] = xrec
        if self.model.conditioning_key is not None:
            if hasattr(self.cond_stage_model, 'decode'):
                xc = self.cond_stage_model.decode(c)
                log['conditioning'] = xc
            elif self.cond_stage_key in ['caption']:
                xc = log_txt_as_img((x.shape[2], x.shape[3]), batch['caption'])
                log['conditioning'] = xc
            elif self.cond_stage_key == 'class_label':
                xc = log_txt_as_img((x.shape[2], x.shape[3]), batch['human_label'])
                log['conditioning'] = xc
            elif isimage(xc):
                log['conditioning'] = xc
            if ismap(xc):
                log['original_conditioning'] = self.to_rgb(xc)
        if plot_diffusion_rows:
            diffusion_row = list()
            z_start = z[:n_row]
            for t in range(self.num_timesteps):
                if t % self.log_every_t == 0 or t == self.num_timesteps - 1:
                    t = repeat(torch.tensor([t]), '1 -> b', b=n_row)
                    t = t.to(self.device).long()
                    noise = torch.randn_like(z_start)
                    z_noisy = self.q_sample(x_start=z_start, t=t, noise=noise)
                    diffusion_row.append(self.decode_first_stage(z_noisy))
            diffusion_row = torch.stack(diffusion_row)
            diffusion_grid = rearrange(diffusion_row, 'n b c h w -> b n c h w')
            diffusion_grid = rearrange(diffusion_grid, 'b n c h w -> (b n) c h w')
            diffusion_grid = make_grid(diffusion_grid, nrow=diffusion_row.shape[0])
            log['diffusion_row'] = diffusion_grid
        if sample:
            with self.ema_scope('Plotting'):
                samples, z_denoise_row = self.sample_log(cond=c, batch_size=N, ddim=use_ddim, ddim_steps=ddim_steps, eta=ddim_eta)
            x_samples = self.decode_first_stage(samples)
            log['samples'] = x_samples
            if plot_denoise_rows:
                denoise_grid = self._get_denoise_row_from_list(z_denoise_row)
                log['denoise_row'] = denoise_grid
            if quantize_denoised and (not isinstance(self.first_stage_model, AutoencoderKL)) and (not isinstance(self.first_stage_model, IdentityFirstStage)):
                with self.ema_scope('Plotting Quantized Denoised'):
                    samples, z_denoise_row = self.sample_log(cond=c, batch_size=N, ddim=use_ddim, ddim_steps=ddim_steps, eta=ddim_eta, quantize_denoised=True)
                x_samples = self.decode_first_stage(samples.to(self.device))
                log['samples_x0_quantized'] = x_samples
            if inpaint:
                b, h, w = (z.shape[0], z.shape[2], z.shape[3])
                mask = torch.ones(N, h, w).to(self.device)
                mask[:, h // 4:3 * h // 4, w // 4:3 * w // 4] = 0.0
                mask = mask[:, None, ...]
                with self.ema_scope('Plotting Inpaint'):
                    samples, _ = self.sample_log(cond=c, batch_size=N, ddim=use_ddim, eta=ddim_eta, ddim_steps=ddim_steps, x0=z[:N], mask=mask)
                x_samples = self.decode_first_stage(samples.to(self.device))
                log['samples_inpainting'] = x_samples
                log['mask'] = mask
                with self.ema_scope('Plotting Outpaint'):
                    samples, _ = self.sample_log(cond=c, batch_size=N, ddim=use_ddim, eta=ddim_eta, ddim_steps=ddim_steps, x0=z[:N], mask=mask)
                x_samples = self.decode_first_stage(samples.to(self.device))
                log['samples_outpainting'] = x_samples
        if plot_progressive_rows:
            with self.ema_scope('Plotting Progressives'):
                img, progressives = self.progressive_denoising(c, shape=(self.channels, self.image_size, self.image_size), batch_size=N)
            prog_row = self._get_denoise_row_from_list(progressives, desc='Progressive Generation')
            log['progressive_row'] = prog_row
        if return_keys:
            if np.intersect1d(list(log.keys()), return_keys).shape[0] == 0:
                return log
            else:
                return {key: log[key] for key in return_keys}
        return log

    def configure_optimizers(self):
        lr = self.learning_rate
        params = list(self.model.parameters())
        if self.cond_stage_trainable:
            print(f'{self.__class__.__name__}: Also optimizing conditioner params!')
            params = params + list(self.cond_stage_model.parameters())
        if self.learn_logvar:
            print('Diffusion model optimizing logvar')
            params.append(self.logvar)
        opt = torch.optim.AdamW(params, lr=lr)
        if self.use_scheduler:
            assert 'target' in self.scheduler_config
            scheduler = instantiate_from_config(self.scheduler_config)
            print('Setting up LambdaLR scheduler...')
            scheduler = [{'scheduler': LambdaLR(opt, lr_lambda=scheduler.schedule), 'interval': 'step', 'frequency': 1}]
            return ([opt], scheduler)
        return opt

    @torch.no_grad()
    def to_rgb(self, x):
        x = x.float()
        if not hasattr(self, 'colorize'):
            self.colorize = torch.randn(3, x.shape[1], 1, 1).to(x)
        x = nn.functional.conv2d(x, weight=self.colorize)
        x = 2.0 * (x - x.min()) / (x.max() - x.min()) - 1.0
        return x

def __init__(self, first_stage_config, cond_stage_config, num_timesteps_cond=None, cond_stage_key='image', cond_stage_trainable=False, concat_mode=True, cond_stage_forward=None, conditioning_key=None, scale_factor=1.0, scale_by_std=False, *args, **kwargs):
    self.num_timesteps_cond = default(num_timesteps_cond, 1)
    self.scale_by_std = scale_by_std
    assert self.num_timesteps_cond <= kwargs['timesteps']
    if conditioning_key is None:
        conditioning_key = 'concat' if concat_mode else 'crossattn'
    if cond_stage_config == '__is_unconditional__':
        conditioning_key = None
    ckpt_path = kwargs.pop('ckpt_path', None)
    ignore_keys = kwargs.pop('ignore_keys', [])
    super().__init__(*args, conditioning_key=conditioning_key, **kwargs)
    self.concat_mode = concat_mode
    self.cond_stage_trainable = cond_stage_trainable
    self.cond_stage_key = cond_stage_key
    try:
        self.num_downs = len(first_stage_config.params.ddconfig.ch_mult) - 1
    except:
        self.num_downs = 0
    if not scale_by_std:
        self.scale_factor = scale_factor
    else:
        self.register_buffer('scale_factor', torch.tensor(scale_factor))
    self.instantiate_first_stage(first_stage_config)
    self.instantiate_cond_stage(cond_stage_config)
    self.cond_stage_forward = cond_stage_forward
    self.clip_denoised = False
    self.bbox_tokenizer = None
    self.restarted_from_ckpt = False
    if ckpt_path is not None:
        self.init_from_ckpt(ckpt_path, ignore_keys)
        self.restarted_from_ckpt = True

def register_schedule(self, given_betas=None, beta_schedule='linear', timesteps=1000, linear_start=0.0001, linear_end=0.02, cosine_s=0.008):
    super().register_schedule(given_betas, beta_schedule, timesteps, linear_start, linear_end, cosine_s)
    self.shorten_cond_schedule = self.num_timesteps_cond > 1
    if self.shorten_cond_schedule:
        self.make_cond_schedule()

class DiffusionWrapper(pl.LightningModule):

    def __init__(self, diff_model_config, conditioning_key):
        super().__init__()
        self.diffusion_model = instantiate_from_config(diff_model_config)
        self.conditioning_key = conditioning_key
        assert self.conditioning_key in [None, 'concat', 'crossattn', 'hybrid', 'adm']

    def forward(self, x, t, c_concat: list=None, c_crossattn: list=None):
        if self.conditioning_key is None:
            out = self.diffusion_model(x, t)
        elif self.conditioning_key == 'concat':
            xc = torch.cat([x] + c_concat, dim=1)
            out = self.diffusion_model(xc, t)
        elif self.conditioning_key == 'crossattn':
            cc = torch.cat(c_crossattn, 1)
            out = self.diffusion_model(x, t, context=cc)
        elif self.conditioning_key == 'hybrid':
            xc = torch.cat([x] + c_concat, dim=1)
            cc = torch.cat(c_crossattn, 1)
            out = self.diffusion_model(xc, t, context=cc)
        elif self.conditioning_key == 'adm':
            cc = c_crossattn[0]
            out = self.diffusion_model(x, t, y=cc)
        else:
            raise NotImplementedError()
        return out

def __init__(self, diff_model_config, conditioning_key):
    super().__init__()
    self.diffusion_model = instantiate_from_config(diff_model_config)
    self.conditioning_key = conditioning_key
    assert self.conditioning_key in [None, 'concat', 'crossattn', 'hybrid', 'adm']

class Layout2ImgDiffusion(LatentDiffusion):

    def __init__(self, cond_stage_key, *args, **kwargs):
        assert cond_stage_key == 'coordinates_bbox', 'Layout2ImgDiffusion only for cond_stage_key="coordinates_bbox"'
        super().__init__(*args, cond_stage_key=cond_stage_key, **kwargs)

    def log_images(self, batch, N=8, *args, **kwargs):
        logs = super().log_images(*args, batch=batch, N=N, **kwargs)
        key = 'train' if self.training else 'validation'
        dset = self.trainer.datamodule.datasets[key]
        mapper = dset.conditional_builders[self.cond_stage_key]
        bbox_imgs = []
        map_fn = lambda catno: dset.get_textual_label(dset.get_category_id(catno))
        for tknzd_bbox in batch[self.cond_stage_key][:N]:
            bboximg = mapper.plot(tknzd_bbox.detach().cpu(), map_fn, (256, 256))
            bbox_imgs.append(bboximg)
        cond_img = torch.stack(bbox_imgs, dim=0)
        logs['bbox_image'] = cond_img
        return logs

def __init__(self, cond_stage_key, *args, **kwargs):
    assert cond_stage_key == 'coordinates_bbox', 'Layout2ImgDiffusion only for cond_stage_key="coordinates_bbox"'
    super().__init__(*args, cond_stage_key=cond_stage_key, **kwargs)

class PLMSSampler(object):

    def __init__(self, model, schedule='linear', **kwargs):
        super().__init__()
        self.model = model
        self.ddpm_num_timesteps = model.num_timesteps
        self.schedule = schedule

    def register_buffer(self, name, attr):
        if type(attr) == torch.Tensor:
            if attr.device != torch.device('cuda'):
                attr = attr.to(torch.device('cuda'))
        setattr(self, name, attr)

    def make_schedule(self, ddim_num_steps, ddim_discretize='uniform', ddim_eta=0.0, verbose=True):
        if ddim_eta != 0:
            raise ValueError('ddim_eta must be 0 for PLMS')
        self.ddim_timesteps = make_ddim_timesteps(ddim_discr_method=ddim_discretize, num_ddim_timesteps=ddim_num_steps, num_ddpm_timesteps=self.ddpm_num_timesteps, verbose=verbose)
        alphas_cumprod = self.model.alphas_cumprod
        assert alphas_cumprod.shape[0] == self.ddpm_num_timesteps, 'alphas have to be defined for each timestep'
        to_torch = lambda x: x.clone().detach().to(torch.float32).to(self.model.device)
        self.register_buffer('betas', to_torch(self.model.betas))
        self.register_buffer('alphas_cumprod', to_torch(alphas_cumprod))
        self.register_buffer('alphas_cumprod_prev', to_torch(self.model.alphas_cumprod_prev))
        self.register_buffer('sqrt_alphas_cumprod', to_torch(np.sqrt(alphas_cumprod.cpu())))
        self.register_buffer('sqrt_one_minus_alphas_cumprod', to_torch(np.sqrt(1.0 - alphas_cumprod.cpu())))
        self.register_buffer('log_one_minus_alphas_cumprod', to_torch(np.log(1.0 - alphas_cumprod.cpu())))
        self.register_buffer('sqrt_recip_alphas_cumprod', to_torch(np.sqrt(1.0 / alphas_cumprod.cpu())))
        self.register_buffer('sqrt_recipm1_alphas_cumprod', to_torch(np.sqrt(1.0 / alphas_cumprod.cpu() - 1)))
        ddim_sigmas, ddim_alphas, ddim_alphas_prev = make_ddim_sampling_parameters(alphacums=alphas_cumprod.cpu(), ddim_timesteps=self.ddim_timesteps, eta=ddim_eta, verbose=verbose)
        self.register_buffer('ddim_sigmas', ddim_sigmas)
        self.register_buffer('ddim_alphas', ddim_alphas)
        self.register_buffer('ddim_alphas_prev', ddim_alphas_prev)
        self.register_buffer('ddim_sqrt_one_minus_alphas', np.sqrt(1.0 - ddim_alphas))
        sigmas_for_original_sampling_steps = ddim_eta * torch.sqrt((1 - self.alphas_cumprod_prev) / (1 - self.alphas_cumprod) * (1 - self.alphas_cumprod / self.alphas_cumprod_prev))
        self.register_buffer('ddim_sigmas_for_original_num_steps', sigmas_for_original_sampling_steps)

    @torch.no_grad()
    def sample(self, S, batch_size, shape, conditioning=None, callback=None, normals_sequence=None, img_callback=None, quantize_x0=False, eta=0.0, mask=None, x0=None, temperature=1.0, noise_dropout=0.0, score_corrector=None, corrector_kwargs=None, verbose=True, x_T=None, log_every_t=100, unconditional_guidance_scale=1.0, unconditional_conditioning=None, **kwargs):
        if conditioning is not None:
            if isinstance(conditioning, dict):
                cbs = conditioning[list(conditioning.keys())[0]].shape[0]
                if cbs != batch_size:
                    print(f'Warning: Got {cbs} conditionings but batch-size is {batch_size}')
            elif conditioning.shape[0] != batch_size:
                print(f'Warning: Got {conditioning.shape[0]} conditionings but batch-size is {batch_size}')
        self.make_schedule(ddim_num_steps=S, ddim_eta=eta, verbose=verbose)
        C, H, W = shape
        size = (batch_size, C, H, W)
        print(f'Data shape for PLMS sampling is {size}')
        samples, intermediates = self.plms_sampling(conditioning, size, callback=callback, img_callback=img_callback, quantize_denoised=quantize_x0, mask=mask, x0=x0, ddim_use_original_steps=False, noise_dropout=noise_dropout, temperature=temperature, score_corrector=score_corrector, corrector_kwargs=corrector_kwargs, x_T=x_T, log_every_t=log_every_t, unconditional_guidance_scale=unconditional_guidance_scale, unconditional_conditioning=unconditional_conditioning)
        return (samples, intermediates)

    @torch.no_grad()
    def plms_sampling(self, cond, shape, x_T=None, ddim_use_original_steps=False, callback=None, timesteps=None, quantize_denoised=False, mask=None, x0=None, img_callback=None, log_every_t=100, temperature=1.0, noise_dropout=0.0, score_corrector=None, corrector_kwargs=None, unconditional_guidance_scale=1.0, unconditional_conditioning=None):
        device = self.model.betas.device
        b = shape[0]
        if x_T is None:
            img = torch.randn(shape, device=device)
        else:
            img = x_T
        if timesteps is None:
            timesteps = self.ddpm_num_timesteps if ddim_use_original_steps else self.ddim_timesteps
        elif timesteps is not None and (not ddim_use_original_steps):
            subset_end = int(min(timesteps / self.ddim_timesteps.shape[0], 1) * self.ddim_timesteps.shape[0]) - 1
            timesteps = self.ddim_timesteps[:subset_end]
        intermediates = {'x_inter': [img], 'pred_x0': [img]}
        time_range = list(reversed(range(0, timesteps))) if ddim_use_original_steps else np.flip(timesteps)
        total_steps = timesteps if ddim_use_original_steps else timesteps.shape[0]
        print(f'Running PLMS Sampling with {total_steps} timesteps')
        iterator = tqdm(time_range, desc='PLMS Sampler', total=total_steps)
        old_eps = []
        for i, step in enumerate(iterator):
            index = total_steps - i - 1
            ts = torch.full((b,), step, device=device, dtype=torch.long)
            ts_next = torch.full((b,), time_range[min(i + 1, len(time_range) - 1)], device=device, dtype=torch.long)
            if mask is not None:
                assert x0 is not None
                img_orig = self.model.q_sample(x0, ts)
                img = img_orig * mask + (1.0 - mask) * img
            outs = self.p_sample_plms(img, cond, ts, index=index, use_original_steps=ddim_use_original_steps, quantize_denoised=quantize_denoised, temperature=temperature, noise_dropout=noise_dropout, score_corrector=score_corrector, corrector_kwargs=corrector_kwargs, unconditional_guidance_scale=unconditional_guidance_scale, unconditional_conditioning=unconditional_conditioning, old_eps=old_eps, t_next=ts_next)
            img, pred_x0, e_t = outs
            old_eps.append(e_t)
            if len(old_eps) >= 4:
                old_eps.pop(0)
            if callback:
                callback(i)
            if img_callback:
                img_callback(pred_x0, i)
            if index % log_every_t == 0 or index == total_steps - 1:
                intermediates['x_inter'].append(img)
                intermediates['pred_x0'].append(pred_x0)
        return (img, intermediates)

    @torch.no_grad()
    def p_sample_plms(self, x, c, t, index, repeat_noise=False, use_original_steps=False, quantize_denoised=False, temperature=1.0, noise_dropout=0.0, score_corrector=None, corrector_kwargs=None, unconditional_guidance_scale=1.0, unconditional_conditioning=None, old_eps=None, t_next=None):
        b, *_, device = (*x.shape, x.device)

        def get_model_output(x, t):
            if unconditional_conditioning is None or unconditional_guidance_scale == 1.0:
                e_t = self.model.apply_model(x, t, c)
            else:
                x_in = torch.cat([x] * 2)
                t_in = torch.cat([t] * 2)
                c_in = torch.cat([unconditional_conditioning, c])
                e_t_uncond, e_t = self.model.apply_model(x_in, t_in, c_in).chunk(2)
                e_t = e_t_uncond + unconditional_guidance_scale * (e_t - e_t_uncond)
            if score_corrector is not None:
                assert self.model.parameterization == 'eps'
                e_t = score_corrector.modify_score(self.model, e_t, x, t, c, **corrector_kwargs)
            return e_t
        alphas = self.model.alphas_cumprod if use_original_steps else self.ddim_alphas
        alphas_prev = self.model.alphas_cumprod_prev if use_original_steps else self.ddim_alphas_prev
        sqrt_one_minus_alphas = self.model.sqrt_one_minus_alphas_cumprod if use_original_steps else self.ddim_sqrt_one_minus_alphas
        sigmas = self.model.ddim_sigmas_for_original_num_steps if use_original_steps else self.ddim_sigmas

        def get_x_prev_and_pred_x0(e_t, index):
            a_t = torch.full((b, 1, 1, 1), alphas[index], device=device)
            a_prev = torch.full((b, 1, 1, 1), alphas_prev[index], device=device)
            sigma_t = torch.full((b, 1, 1, 1), sigmas[index], device=device)
            sqrt_one_minus_at = torch.full((b, 1, 1, 1), sqrt_one_minus_alphas[index], device=device)
            pred_x0 = (x - sqrt_one_minus_at * e_t) / a_t.sqrt()
            if quantize_denoised:
                pred_x0, _, *_ = self.model.first_stage_model.quantize(pred_x0)
            dir_xt = (1.0 - a_prev - sigma_t ** 2).sqrt() * e_t
            noise = sigma_t * noise_like(x.shape, device, repeat_noise) * temperature
            if noise_dropout > 0.0:
                noise = torch.nn.functional.dropout(noise, p=noise_dropout)
            x_prev = a_prev.sqrt() * pred_x0 + dir_xt + noise
            return (x_prev, pred_x0)
        e_t = get_model_output(x, t)
        if len(old_eps) == 0:
            x_prev, pred_x0 = get_x_prev_and_pred_x0(e_t, index)
            e_t_next = get_model_output(x_prev, t_next)
            e_t_prime = (e_t + e_t_next) / 2
        elif len(old_eps) == 1:
            e_t_prime = (3 * e_t - old_eps[-1]) / 2
        elif len(old_eps) == 2:
            e_t_prime = (23 * e_t - 16 * old_eps[-1] + 5 * old_eps[-2]) / 12
        elif len(old_eps) >= 3:
            e_t_prime = (55 * e_t - 59 * old_eps[-1] + 37 * old_eps[-2] - 9 * old_eps[-3]) / 24
        x_prev, pred_x0 = get_x_prev_and_pred_x0(e_t_prime, index)
        return (x_prev, pred_x0, e_t)

def __init__(self, model, schedule='linear', **kwargs):
    super().__init__()
    self.model = model
    self.ddpm_num_timesteps = model.num_timesteps
    self.schedule = schedule

class SkyModel(pl.LightningModule):

    def __init__(self, hypes):
        super().__init__()
        self.hypes = hypes
        downsample = hypes['dataset']['downsample']
        self.sky_H = hypes['dataset']['image_H'] // downsample // 2
        self.sky_W = hypes['dataset']['image_W'] // downsample
        self.teacher_prob = hypes['model']['teacher_prob']
        self.env_template = EnvironmentMap(self.sky_H, 'skylatlong')
        world_coord = self.env_template.worldCoordinates()
        self.pos_encoding = torch.from_numpy(np.stack([world_coord[0], world_coord[1], world_coord[2]], axis=-1))
        self.pos_encoding = self.pos_encoding.to('cuda')
        self.input_inv_gamma = hypes['model']['input_inv_gamma']
        self.input_add_pe = hypes['model']['input_add_pe']
        self.encoder_outdim = hypes['model']['ldr_encoder']['args']['layer_channels'][-1]
        self.feat_down = reduce(lambda x, y: x * y, hypes['model']['ldr_encoder']['args']['strides'])
        self.save_hyperparameters()
        self.ldr_encoder = build_module(hypes['model']['ldr_encoder'])
        self.shared_mlp = build_module(hypes['model']['shared_mlp'])
        self.latent_mlp = build_module(hypes['model']['latent_mlp'])
        self.latent_mlp_recon = build_module(hypes['model']['latent_mlp_recon'])
        self.peak_dir_mlp = build_module(hypes['model']['peak_dir_mlp'])
        self.peak_int_mlp = build_module(hypes['model']['peak_int_mlp'])
        self.ldr_decoder = nn.Sequential(build_module(hypes['model']['ldr_decoder']), nn.Sigmoid())
        self.hdr_decoder = build_module(hypes['model']['hdr_decoder'])
        self.ldr_recon_loss = build_loss(hypes['loss']['ldr_recon_loss'])
        self.hdr_recon_loss = build_loss(hypes['loss']['hdr_recon_loss'])
        self.peak_int_loss = build_loss(hypes['loss']['peak_int_loss'])
        self.peak_dir_loss = build_loss(hypes['loss']['peak_dir_loss'])
        self.fix_modules = hypes['model'].get('fix_modules', [])
        self.on_train_epoch_start()

    def encode_forward(self, x):
        """
        Encode LDR panorama to sky vector: 
            1) peak dir 
            2) peak int 
            3) latent vector
            where 1) and 2) can cat together
        
        deep vector -> shared vector -->    latent vector      --> recon deep vector 
                                     |
                                     .->  peak int/dir vector

        Should we add explicit inv gamma to the input?
        """
        if self.input_inv_gamma:
            x = srgb_inv_gamma_correction_torch(x)
        if self.input_add_pe:
            x = x + self.pos_encoding.permute(2, 0, 1)
        deep_feature = self.ldr_encoder(x)
        deep_vector = deep_feature.permute(0, 2, 3, 1).flatten(1)
        shared_vector = self.shared_mlp(deep_vector)
        peak_dir_vector = self.peak_dir_mlp(shared_vector)
        peak_int_vector = self.peak_int_mlp(shared_vector)
        latent_vector = self.latent_mlp(shared_vector)
        peak_dir_vector = peak_dir_vector / peak_dir_vector.norm(dim=1, keepdim=True)
        peak_vector = torch.cat([peak_dir_vector, peak_int_vector], dim=-1)
        return (peak_vector, latent_vector)

    def decode_forward(self, latent_vector, peak_vector, peak_vector_gt):
        use_gt_peak = False
        if self.training and np.random.rand() < self.teacher_prob:
            use_gt_peak = True
            peak_vector = peak_vector_gt
        B = peak_vector.shape[0]
        peak_dir_encoding, peak_int_encoding = self.build_peak_map(peak_vector)
        decoder_input = torch.cat([peak_dir_encoding, peak_int_encoding, self.pos_encoding.expand(B, -1, -1, -1)], dim=-1)
        decoder_input = decoder_input.permute(0, 3, 1, 2)
        recon_deep_vector = self.latent_mlp_recon(latent_vector)
        recon_deep_feature = recon_deep_vector.view(B, self.sky_H // self.feat_down, self.sky_W // self.feat_down, self.encoder_outdim).permute(0, 3, 1, 2)
        ldr_skypano_recon = self.ldr_decoder(recon_deep_feature)
        hdr_skypano_recon = self.hdr_decoder(decoder_input, recon_deep_feature)
        return (hdr_skypano_recon, ldr_skypano_recon, use_gt_peak)

    def build_peak_map(self, peak_vector):
        """
        Args:
            peak_vector: [B, 6]
                3 for peak dir, 3 for peak intensity

        Returns:
            peak encoding map: [B, 4, H, W]
                1 for peak dir using spherical gaussian lobe, 3 for peak intensity
        """
        dir_vector = peak_vector[..., :3]
        int_vector = peak_vector[..., 3:]
        dir_vector_expand = dir_vector.unsqueeze(1).unsqueeze(1).expand(-1, self.sky_H, self.sky_W, -1)
        peak_dir_encoding = torch.exp(100 * (torch.einsum('nhwc,nhwc->nhw', dir_vector_expand, self.pos_encoding.expand(dir_vector_expand.shape)) - 1)).unsqueeze(-1)
        sun_mask = torch.gt(peak_dir_encoding, 0.9).expand(-1, -1, -1, 3)
        int_vector_expand = int_vector.unsqueeze(1).unsqueeze(1).expand(-1, self.sky_H, self.sky_W, -1)
        peak_int_encoding = torch.where(sun_mask, int_vector_expand, 0)
        return (peak_dir_encoding, peak_int_encoding)

    def on_train_epoch_start(self):
        print(f'Module fixed in training: {self.fix_modules}.')
        for module in self.fix_modules:
            for p in eval(f'self.{module}').parameters():
                p.requires_grad_(False)
            eval(f'self.{module}').eval()

    def training_step(self, batch, batch_idx):
        ldr_skypano, hdr_skypano_gt, peak_vector_gt = batch
        peak_vector_pred, latent_vector = self.encode_forward(ldr_skypano)
        hdr_skypano_pred, ldr_skypano_recon, _ = self.decode_forward(latent_vector, peak_vector_pred, peak_vector_gt)
        ldr_recon_loss = self.ldr_recon_loss(ldr_skypano_recon, ldr_skypano)
        hdr_recon_loss = self.hdr_recon_loss(hdr_skypano_pred, hdr_skypano_gt)
        peak_dir_loss = self.peak_dir_loss(peak_vector_pred[..., :3], peak_vector_gt[..., :3])
        peak_int_loss = self.peak_int_loss(peak_vector_pred[..., 3:], peak_vector_gt[..., 3:])
        loss = hdr_recon_loss + peak_dir_loss + peak_int_loss + ldr_recon_loss
        self.log('train_loss', loss)
        self.log('hdr_recon_loss', hdr_recon_loss)
        self.log('ldr_recon_loss', ldr_recon_loss)
        self.log('peak_dir_loss', peak_dir_loss)
        self.log('peak_int_loss', peak_int_loss)
        log_info = f'|| loss: {loss:.3f} || hdr_recon_loss: {hdr_recon_loss:.3f}  || ldr_recon_loss: {ldr_recon_loss:.3f} || peak_dir_loss: {peak_dir_loss:.3f} ' + f'|| peak_int_loss: {peak_int_loss:.3f}'
        print(log_info)
        return loss

    def validation_step(self, batch, batch_idx):
        ldr_skypano, hdr_skypano_gt, peak_vector_gt = batch
        peak_vector_pred, latent_vector = self.encode_forward(ldr_skypano)
        hdr_skypano_pred, ldr_skypano_recon, _ = self.decode_forward(latent_vector, peak_vector_pred, peak_vector_pred)
        ldr_recon_loss = self.ldr_recon_loss(ldr_skypano_recon, ldr_skypano)
        hdr_recon_loss = self.hdr_recon_loss(hdr_skypano_pred, hdr_skypano_gt)
        loss = hdr_recon_loss
        self.log('val_loss', loss)
        return loss

    def test_step(self, batch, batch_idx):
        return self.validation_step(batch, batch_idx)

    def predict_step(self, batch, batch_idx):
        ldr_skypano, hdr_skypano_gt, peak_vector_gt = batch
        peak_vector_pred, latent_vector = self.encode_forward(ldr_skypano)
        hdr_skypano_pred, ldr_skypano_recon, _ = self.decode_forward(latent_vector, peak_vector_pred, peak_vector_pred)
        print(f'{batch_idx:0>3} \n                  HDRI Peak Intensity:\t\t {hdr_skypano_pred[0].flatten(1, 2).max(dim=-1)[0]} \n                  Peak Intensity Vector:\t {peak_vector_pred[0][3:]} \n                  Ground Truth Peak Intensity:\t {peak_vector_gt[0][3:]}')
        return_dict = {'ldr_skypano_input': ldr_skypano.permute(0, 2, 3, 1), 'ldr_skypano_pred': ldr_skypano_recon.permute(0, 2, 3, 1), 'hdr_skypano_gt': hdr_skypano_gt.permute(0, 2, 3, 1), 'hdr_skypano_pred': hdr_skypano_pred.permute(0, 2, 3, 1), 'batch_idx': batch_idx}
        return return_dict

    def configure_optimizers(self):
        optimizer = torch.optim.Adam(self.parameters(), lr=self.hypes['lr_schedule']['init_lr'])
        lr_scheduler = StepLR(optimizer=optimizer, step_size=self.hypes['lr_schedule']['decay_per_epoch'], gamma=self.hypes['lr_schedule']['decay_rate'])
        return ([optimizer], [lr_scheduler])

def __init__(self, hypes):
    super().__init__()
    self.hypes = hypes
    downsample = hypes['dataset']['downsample']
    self.sky_H = hypes['dataset']['image_H'] // downsample // 2
    self.sky_W = hypes['dataset']['image_W'] // downsample
    self.teacher_prob = hypes['model']['teacher_prob']
    self.env_template = EnvironmentMap(self.sky_H, 'skylatlong')
    world_coord = self.env_template.worldCoordinates()
    self.pos_encoding = torch.from_numpy(np.stack([world_coord[0], world_coord[1], world_coord[2]], axis=-1))
    self.pos_encoding = self.pos_encoding.to('cuda')
    self.input_inv_gamma = hypes['model']['input_inv_gamma']
    self.input_add_pe = hypes['model']['input_add_pe']
    self.encoder_outdim = hypes['model']['ldr_encoder']['args']['layer_channels'][-1]
    self.feat_down = reduce(lambda x, y: x * y, hypes['model']['ldr_encoder']['args']['strides'])
    self.save_hyperparameters()
    self.ldr_encoder = build_module(hypes['model']['ldr_encoder'])
    self.shared_mlp = build_module(hypes['model']['shared_mlp'])
    self.latent_mlp = build_module(hypes['model']['latent_mlp'])
    self.latent_mlp_recon = build_module(hypes['model']['latent_mlp_recon'])
    self.peak_dir_mlp = build_module(hypes['model']['peak_dir_mlp'])
    self.peak_int_mlp = build_module(hypes['model']['peak_int_mlp'])
    self.ldr_decoder = nn.Sequential(build_module(hypes['model']['ldr_decoder']), nn.Sigmoid())
    self.hdr_decoder = build_module(hypes['model']['hdr_decoder'])
    self.ldr_recon_loss = build_loss(hypes['loss']['ldr_recon_loss'])
    self.hdr_recon_loss = build_loss(hypes['loss']['hdr_recon_loss'])
    self.peak_int_loss = build_loss(hypes['loss']['peak_int_loss'])
    self.peak_dir_loss = build_loss(hypes['loss']['peak_dir_loss'])
    self.fix_modules = hypes['model'].get('fix_modules', [])
    self.on_train_epoch_start()

class SkyModelEnhanced(pl.LightningModule):

    def __init__(self, hypes):
        super().__init__()
        self.hypes = hypes
        downsample = hypes['dataset']['downsample']
        self.sky_H = hypes['dataset']['image_H'] // downsample // 2
        self.sky_W = hypes['dataset']['image_W'] // downsample
        self.teacher_prob = hypes['model']['teacher_prob']
        self.env_template = EnvironmentMap(self.sky_H, 'skylatlong')
        world_coord = self.env_template.worldCoordinates()
        self.pos_encoding = torch.from_numpy(np.stack([world_coord[0], world_coord[1], world_coord[2]], axis=-1))
        self.pos_encoding = self.pos_encoding.to('cuda')
        self.input_inv_gamma = hypes['model']['input_inv_gamma']
        self.input_add_pe = hypes['model']['input_add_pe']
        self.encoder_outdim = hypes['model']['ldr_encoder']['args']['layer_channels'][-1]
        self.feat_down = reduce(lambda x, y: x * y, hypes['model']['ldr_encoder']['args']['strides'])
        self.sum_lobe_thres = hypes['model'].get('sum_lobe_thres', 0.9)
        self.save_hyperparameters()
        self.ldr_encoder = build_module(hypes['model']['ldr_encoder'])
        self.shared_mlp = build_module(hypes['model']['shared_mlp'])
        self.latent_mlp = build_module(hypes['model']['latent_mlp'])
        self.latent_mlp_recon = build_module(hypes['model']['latent_mlp_recon'])
        self.peak_dir_mlp = build_module(hypes['model']['peak_dir_mlp'])
        self.peak_int_mlp = build_module(hypes['model']['peak_int_mlp'])
        self.ldr_decoder = nn.Sequential(build_module(hypes['model']['ldr_decoder']), nn.Sigmoid())
        self.hdr_decoder = build_module(hypes['model']['hdr_decoder'])
        self.ldr_recon_loss = build_loss(hypes['loss']['ldr_recon_loss'])
        self.hdr_recon_loss = build_loss(hypes['loss']['hdr_recon_loss'])
        self.peak_int_loss = build_loss(hypes['loss']['peak_int_loss'])
        self.peak_dir_loss = build_loss(hypes['loss']['peak_dir_loss'])
        self.fix_modules = hypes['model'].get('fix_modules', [])
        self.on_train_epoch_start()

    def encode_forward(self, x):
        """
        Encode LDR panorama to sky vector: 
            1) peak dir 
            2) peak int 
            3) latent vector
            where 1) and 2) can cat together
        
        deep vector -> shared vector -->    latent vector      --> recon deep vector 
                                     |
                                     .->  peak int/dir vector

        Should we add explicit inv gamma to the input?
        """
        if self.input_inv_gamma:
            x = srgb_inv_gamma_correction_torch(x)
        if self.input_add_pe:
            x = x + self.pos_encoding.permute(2, 0, 1)
        deep_feature = self.ldr_encoder(x)
        deep_vector = deep_feature.permute(0, 2, 3, 1).flatten(1)
        shared_vector = self.shared_mlp(deep_vector)
        peak_dir_vector = self.peak_dir_mlp(shared_vector)
        peak_int_vector = self.peak_int_mlp(shared_vector)
        latent_vector = self.latent_mlp(shared_vector)
        peak_dir_vector = peak_dir_vector / peak_dir_vector.norm(dim=1, keepdim=True)
        peak_vector = torch.cat([peak_dir_vector, peak_int_vector], dim=-1)
        return (peak_vector, latent_vector)

    def decode_forward(self, latent_vector, peak_vector, peak_vector_gt):
        use_gt_peak = False
        if self.training and np.random.rand() < self.teacher_prob:
            use_gt_peak = True
            peak_vector = peak_vector_gt
        B = peak_vector.shape[0]
        peak_dir_encoding, peak_int_encoding, sum_mask = self.build_peak_map(peak_vector)
        decoder_input = torch.cat([peak_dir_encoding, peak_int_encoding, self.pos_encoding.expand(B, -1, -1, -1)], dim=-1)
        decoder_input = decoder_input.permute(0, 3, 1, 2)
        recon_deep_vector = self.latent_mlp_recon(latent_vector)
        recon_deep_feature = recon_deep_vector.view(B, self.sky_H // self.feat_down, self.sky_W // self.feat_down, self.encoder_outdim).permute(0, 3, 1, 2)
        ldr_skypano_recon = self.ldr_decoder(recon_deep_feature)
        hdr_skypano_recon = self.hdr_decoder(decoder_input, recon_deep_feature)
        sum_mask = sum_mask.permute(0, 3, 1, 2)
        sun_peak_map = peak_dir_encoding.permute(0, 3, 1, 2) * peak_int_encoding.permute(0, 3, 1, 2)
        hdr_skypano_recon = torch.where(sum_mask, sun_peak_map, hdr_skypano_recon)
        return (hdr_skypano_recon, ldr_skypano_recon, use_gt_peak)

    def build_peak_map(self, peak_vector):
        """
        Args:
            peak_vector : [B, 6]
                3 for peak dir, 3 for peak intensity

        Returns:
            peak encoding map : [B, H, W, 4]
                1 for peak dir using spherical gaussian lobe, 3 for peak intensity

            sum_mask :[B, H, W, 3]
        """
        dir_vector = peak_vector[..., :3]
        int_vector = peak_vector[..., 3:]
        dir_vector_expand = dir_vector.unsqueeze(1).unsqueeze(1).expand(-1, self.sky_H, self.sky_W, -1)
        peak_dir_cosine = torch.einsum('nhwc,nhwc->nhw', dir_vector_expand, self.pos_encoding.expand(dir_vector_expand.shape)).unsqueeze(-1)
        peak_dir_encoding = torch.exp(100 * (peak_dir_cosine - 1))
        sun_mask = torch.gt(peak_dir_encoding, self.sum_lobe_thres).expand(-1, -1, -1, 3)
        int_vector_expand = int_vector.unsqueeze(1).unsqueeze(1).expand(-1, self.sky_H, self.sky_W, -1)
        peak_int_encoding = torch.where(sun_mask, int_vector_expand, 0)
        return (peak_dir_encoding, peak_int_encoding, sun_mask)

    def on_train_epoch_start(self):
        print(f'Module fixed in training: {self.fix_modules}.')
        for module in self.fix_modules:
            for p in eval(f'self.{module}').parameters():
                p.requires_grad_(False)
            eval(f'self.{module}').eval()

    def training_step(self, batch, batch_idx):
        ldr_skypano, hdr_skypano_gt, peak_vector_gt = batch
        peak_vector_pred, latent_vector = self.encode_forward(ldr_skypano)
        hdr_skypano_pred, ldr_skypano_recon, _ = self.decode_forward(latent_vector, peak_vector_pred, peak_vector_gt)
        ldr_recon_loss = self.ldr_recon_loss(ldr_skypano_recon, ldr_skypano)
        hdr_recon_loss = self.hdr_recon_loss(hdr_skypano_pred, hdr_skypano_gt)
        peak_dir_loss = self.peak_dir_loss(peak_vector_pred[..., :3], peak_vector_gt[..., :3])
        peak_int_loss = self.peak_int_loss(peak_vector_pred[..., 3:], peak_vector_gt[..., 3:])
        loss = hdr_recon_loss + peak_dir_loss + peak_int_loss + ldr_recon_loss
        self.log('train_loss', loss)
        self.log('hdr_recon_loss', hdr_recon_loss)
        self.log('ldr_recon_loss', ldr_recon_loss)
        self.log('peak_dir_loss', peak_dir_loss)
        self.log('peak_int_loss', peak_int_loss)
        log_info = f'|| loss: {loss:.3f} || hdr_recon_loss: {hdr_recon_loss:.3f}  || ldr_recon_loss: {ldr_recon_loss:.3f} || peak_dir_loss: {peak_dir_loss:.3f} ' + f'|| peak_int_loss: {peak_int_loss:.3f}'
        print(log_info)
        return loss

    def validation_step(self, batch, batch_idx):
        ldr_skypano, hdr_skypano_gt, peak_vector_gt = batch
        peak_vector_pred, latent_vector = self.encode_forward(ldr_skypano)
        hdr_skypano_pred, ldr_skypano_recon, _ = self.decode_forward(latent_vector, peak_vector_pred, peak_vector_pred)
        ldr_recon_loss = self.ldr_recon_loss(ldr_skypano_recon, ldr_skypano)
        hdr_recon_loss = self.hdr_recon_loss(hdr_skypano_pred, hdr_skypano_gt)
        peak_dir_loss = self.peak_dir_loss(peak_vector_pred[..., :3], peak_vector_gt[..., :3])
        peak_int_loss = self.peak_int_loss(peak_vector_pred[..., 3:], peak_vector_gt[..., 3:])
        loss = hdr_recon_loss + peak_dir_loss + peak_int_loss + ldr_recon_loss
        self.log('val_loss', loss)
        return loss

    def test_step(self, batch, batch_idx):
        return self.validation_step(batch, batch_idx)

    def predict_step(self, batch, batch_idx):
        ldr_skypano, hdr_skypano_gt, peak_vector_gt = batch
        peak_vector_pred, latent_vector = self.encode_forward(ldr_skypano)
        hdr_skypano_pred, ldr_skypano_recon, _ = self.decode_forward(latent_vector, peak_vector_pred, peak_vector_pred)
        print(f'{batch_idx:0>3} \n                  HDRI Peak Intensity:\t\t {hdr_skypano_pred[0].flatten(1, 2).max(dim=-1)[0]} \n                  Peak Intensity Vector:\t {peak_vector_pred[0][3:]} \n                  Ground Truth Peak Intensity:\t {peak_vector_gt[0][3:]}')
        return_dict = {'ldr_skypano_input': ldr_skypano.permute(0, 2, 3, 1), 'ldr_skypano_pred': ldr_skypano_recon.permute(0, 2, 3, 1), 'hdr_skypano_gt': hdr_skypano_gt.permute(0, 2, 3, 1), 'hdr_skypano_pred': hdr_skypano_pred.permute(0, 2, 3, 1), 'batch_idx': batch_idx}
        return return_dict

    def configure_optimizers(self):
        optimizer = torch.optim.Adam(self.parameters(), lr=self.hypes['lr_schedule']['init_lr'])
        lr_scheduler = StepLR(optimizer=optimizer, step_size=self.hypes['lr_schedule']['decay_per_epoch'], gamma=self.hypes['lr_schedule']['decay_rate'])
        return ([optimizer], [lr_scheduler])

def __init__(self, hypes):
    super().__init__()
    self.hypes = hypes
    downsample = hypes['dataset']['downsample']
    self.sky_H = hypes['dataset']['image_H'] // downsample // 2
    self.sky_W = hypes['dataset']['image_W'] // downsample
    self.teacher_prob = hypes['model']['teacher_prob']
    self.env_template = EnvironmentMap(self.sky_H, 'skylatlong')
    world_coord = self.env_template.worldCoordinates()
    self.pos_encoding = torch.from_numpy(np.stack([world_coord[0], world_coord[1], world_coord[2]], axis=-1))
    self.pos_encoding = self.pos_encoding.to('cuda')
    self.input_inv_gamma = hypes['model']['input_inv_gamma']
    self.input_add_pe = hypes['model']['input_add_pe']
    self.encoder_outdim = hypes['model']['ldr_encoder']['args']['layer_channels'][-1]
    self.feat_down = reduce(lambda x, y: x * y, hypes['model']['ldr_encoder']['args']['strides'])
    self.sum_lobe_thres = hypes['model'].get('sum_lobe_thres', 0.9)
    self.save_hyperparameters()
    self.ldr_encoder = build_module(hypes['model']['ldr_encoder'])
    self.shared_mlp = build_module(hypes['model']['shared_mlp'])
    self.latent_mlp = build_module(hypes['model']['latent_mlp'])
    self.latent_mlp_recon = build_module(hypes['model']['latent_mlp_recon'])
    self.peak_dir_mlp = build_module(hypes['model']['peak_dir_mlp'])
    self.peak_int_mlp = build_module(hypes['model']['peak_int_mlp'])
    self.ldr_decoder = nn.Sequential(build_module(hypes['model']['ldr_decoder']), nn.Sigmoid())
    self.hdr_decoder = build_module(hypes['model']['hdr_decoder'])
    self.ldr_recon_loss = build_loss(hypes['loss']['ldr_recon_loss'])
    self.hdr_recon_loss = build_loss(hypes['loss']['hdr_recon_loss'])
    self.peak_int_loss = build_loss(hypes['loss']['peak_int_loss'])
    self.peak_dir_loss = build_loss(hypes['loss']['peak_dir_loss'])
    self.fix_modules = hypes['model'].get('fix_modules', [])
    self.on_train_epoch_start()

class SkyPred(pl.LightningModule):

    def __init__(self, hypes):
        super().__init__()
        self.hypes = hypes
        self.save_hyperparameters()
        self.latent_predictor = build_latent_predictor(hypes['model']['latent_predictor'])
        sky_model_core_method = hypes['model']['sky_model']['core_method']
        sky_model_core_method_ckpt_path = hypes['model']['sky_model']['ckpt_path']
        if sky_model_core_method == 'sky_model_enhanced':
            self.sky_model = SkyModelEnhanced.load_from_checkpoint(sky_model_core_method_ckpt_path)
        elif sky_model_core_method == 'sky_model':
            self.sky_model = SkyModel.load_from_checkpoint(sky_model_core_method_ckpt_path)
        self.ldr_recon_loss = build_loss(hypes['loss']['ldr_recon_loss'])
        self.hdr_recon_loss = build_loss(hypes['loss']['hdr_recon_loss'])
        self.peak_int_loss = build_loss(hypes['loss']['peak_int_loss'])
        self.peak_dir_loss = build_loss(hypes['loss']['peak_dir_loss'])
        self.latent_loss = build_loss(hypes['loss']['latent_loss'])
        self.fix_modules = hypes['model'].get('fix_modules', [])
        self.on_train_epoch_start()

    def decode_forward(self, latent_vector, peak_vector):
        return self.sky_model.decode_forward(latent_vector, peak_vector, peak_vector)

    def on_train_epoch_start(self):
        print(f'Module fixed in training: {self.fix_modules}.')
        for module in self.fix_modules:
            for p in eval(f'self.{module}').parameters():
                p.requires_grad_(False)
            eval(f'self.{module}').eval()

    def training_step(self, batch, batch_idx):
        img_crops_tensor, peak_vector_gt, latent_vector_gt, mask_envmap_tensor, hdr_envmap_tensor, ldr_envmap_tensor = batch
        peak_vector_pred, latent_vector_pred = self.latent_predictor(img_crops_tensor)
        hdr_skypano_pred, ldr_skypano_pred, _ = self.decode_forward(latent_vector_pred, peak_vector_pred)
        hdr_recon_loss = self.hdr_recon_loss(hdr_skypano_pred, hdr_envmap_tensor, mask_envmap_tensor)
        ldr_recon_loss = self.ldr_recon_loss(srgb_gamma_correction_torch(hdr_skypano_pred), ldr_envmap_tensor, mask_envmap_tensor)
        latent_loss = self.latent_loss(latent_vector_pred, latent_vector_gt)
        peak_dir_loss = self.peak_dir_loss(peak_vector_pred[..., :3], peak_vector_gt[..., :3])
        peak_int_loss = self.peak_int_loss(peak_vector_pred[..., 3:], peak_vector_gt[..., 3:])
        loss = hdr_recon_loss + ldr_recon_loss + latent_loss + peak_dir_loss + peak_int_loss
        self.log('train_loss', loss)
        self.log('hdr_recon_loss', hdr_recon_loss)
        self.log('ldr_recon_loss', ldr_recon_loss)
        self.log('latent_loss', latent_loss)
        self.log('peak_dir_loss', peak_dir_loss)
        self.log('peak_int_loss', peak_int_loss)
        print(f'|| loss: {loss:.3f} || hdr_recon_loss: {hdr_recon_loss:.3f} || ldr_recon_loss: {ldr_recon_loss:.3f} ' + f'|| latent_loss: {latent_loss:.3f} || peak_dir_loss: {peak_dir_loss:.3f} || peak_int_loss: {peak_int_loss:.3f}')
        return loss

    def validation_step(self, batch, batch_idx):
        img_crops_tensor, peak_vector_gt, latent_vector_gt, mask_envmap_tensor, hdr_envmap_tensor, ldr_envmap_tensor = batch
        mask_envmap_tensor = torch.gt(mask_envmap_tensor, 0.8)
        peak_vector_pred, latent_vector_pred = self.latent_predictor(img_crops_tensor)
        hdr_skypano_pred, ldr_skypano_pred, _ = self.decode_forward(latent_vector_pred, peak_vector_pred)
        hdr_recon_loss = self.hdr_recon_loss(hdr_skypano_pred, hdr_envmap_tensor, mask_envmap_tensor)
        ldr_recon_loss = self.ldr_recon_loss(srgb_gamma_correction_torch(hdr_skypano_pred), ldr_envmap_tensor, mask_envmap_tensor)
        latent_loss = self.latent_loss(latent_vector_pred, latent_vector_gt)
        peak_dir_loss = self.peak_dir_loss(peak_vector_pred[..., :3], peak_vector_gt[..., :3])
        peak_int_loss = self.peak_int_loss(peak_vector_pred[..., 3:], peak_vector_gt[..., 3:])
        loss = hdr_recon_loss + ldr_recon_loss
        self.log('val_loss', loss)
        return loss

    def test_step(self, batch, batch_idx):
        return self.validation_step(batch, batch_idx)

    def predict_step(self, batch, batch_idx):
        img_crops_tensor, peak_vector_gt, latent_vector_gt, mask_envmap_tensor, hdr_envmap_tensor, ldr_envmap_tensor = batch
        mask_envmap_tensor = torch.gt(mask_envmap_tensor, 0.8)
        peak_vector_pred, latent_vector_pred = self.latent_predictor(img_crops_tensor)
        hdr_skypano_pred, ldr_skypano_pred, _ = self.decode_forward(latent_vector_pred, peak_vector_pred)
        return_dict = {'hdr_skypano_pred': hdr_skypano_pred.permute(0, 2, 3, 1), 'ldr_skypano_pred': srgb_gamma_correction_torch(hdr_skypano_pred).permute(0, 2, 3, 1), 'hdr_skypano_gt': hdr_envmap_tensor.permute(0, 2, 3, 1), 'ldr_skypano_input': ldr_envmap_tensor.permute(0, 2, 3, 1), 'mask_env': mask_envmap_tensor.permute(0, 2, 3, 1), 'image_crops': img_crops_tensor.permute(0, 1, 3, 4, 2), 'batch_idx': batch_idx}
        return return_dict

    def configure_optimizers(self):
        optimizer = torch.optim.Adam(self.parameters(), lr=self.hypes['lr_schedule']['init_lr'])
        lr_scheduler = StepLR(optimizer=optimizer, step_size=self.hypes['lr_schedule']['decay_per_epoch'], gamma=self.hypes['lr_schedule']['decay_rate'])
        return ([optimizer], [lr_scheduler])

def __init__(self, hypes):
    super().__init__()
    self.hypes = hypes
    self.save_hyperparameters()
    self.latent_predictor = build_latent_predictor(hypes['model']['latent_predictor'])
    sky_model_core_method = hypes['model']['sky_model']['core_method']
    sky_model_core_method_ckpt_path = hypes['model']['sky_model']['ckpt_path']
    if sky_model_core_method == 'sky_model_enhanced':
        self.sky_model = SkyModelEnhanced.load_from_checkpoint(sky_model_core_method_ckpt_path)
    elif sky_model_core_method == 'sky_model':
        self.sky_model = SkyModel.load_from_checkpoint(sky_model_core_method_ckpt_path)
    self.ldr_recon_loss = build_loss(hypes['loss']['ldr_recon_loss'])
    self.hdr_recon_loss = build_loss(hypes['loss']['hdr_recon_loss'])
    self.peak_int_loss = build_loss(hypes['loss']['peak_int_loss'])
    self.peak_dir_loss = build_loss(hypes['loss']['peak_dir_loss'])
    self.latent_loss = build_loss(hypes['loss']['latent_loss'])
    self.fix_modules = hypes['model'].get('fix_modules', [])
    self.on_train_epoch_start()

class ScaledDotProductAttention(nn.Module):
    """
    Scaled Dot-Product Attention proposed in "Attention Is All You Need"
    Compute the dot products of the query with all keys, divide each by sqrt(dim),
    and apply a softmax function to obtain the weights on the values
    Args: dim, mask
        dim (int): dimention of attention
    Inputs: query, key, value, mask
        - **query** (batch, q_len, d_model): tensor containing projection
          vector for decoder.
        - **key** (batch, k_len, d_model): tensor containing projection
          vector for encoder.
        - **value** (batch, v_len, d_model): tensor containing features of the
          encoded input sequence.
    Returns: context, attn
        - **context**: tensor containing the context vector from
          attention mechanism.
        - **attn**: tensor containing the attention (alignment) from the
          encoder outputs.
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

class NaiveSingleView(nn.Module):

    def __init__(self, args):
        super().__init__()
        self.args = args
        view_args = args['view_setting']
        self.view_num = view_args['view_num']
        self.view_dis_deg = view_args['view_dis']
        self.view_dis_rad = [np.radians(x) for x in view_args['view_dis']]
        self.center_view = view_args['view_dis'].index(0)
        self.img_encoder = build_module(args['img_encoder'])
        self.shared_mlp = build_module(args['shared_mlp'])
        self.latent_mlp = build_module(args['latent_mlp'])
        self.peak_dir_mlp = build_module(args['peak_dir_mlp'])
        self.peak_int_mlp = build_module(args['peak_int_mlp'])

    def forward(self, x):
        """
        x: B, N_view, C, H, W
        """
        x = x[:, self.center_view, ...]
        x = self.img_encoder(x).permute(0, 2, 3, 1)
        x_flatten = x.flatten(1)
        deep_vector = self.shared_mlp(x_flatten)
        latent_vector = self.latent_mlp(deep_vector)
        peak_dir_vector = self.peak_dir_mlp(deep_vector)
        peak_int_vector = self.peak_int_mlp(deep_vector)
        peak_dir_vector = peak_dir_vector / peak_dir_vector.norm(dim=1, keepdim=True)
        peak_vector = torch.cat([peak_dir_vector, peak_int_vector], dim=-1)
        return (peak_vector, latent_vector)

def __init__(self, args):
    super().__init__()
    self.args = args
    view_args = args['view_setting']
    self.view_num = view_args['view_num']
    self.view_dis_deg = view_args['view_dis']
    self.view_dis_rad = [np.radians(x) for x in view_args['view_dis']]
    self.center_view = view_args['view_dis'].index(0)
    self.img_encoder = build_module(args['img_encoder'])
    self.shared_mlp = build_module(args['shared_mlp'])
    self.latent_mlp = build_module(args['latent_mlp'])
    self.peak_dir_mlp = build_module(args['peak_dir_mlp'])
    self.peak_int_mlp = build_module(args['peak_int_mlp'])

class CatMultiView(nn.Module):

    def __init__(self, args):
        super().__init__()
        self.args = args
        view_args = args['view_setting']
        self.view_num = view_args['view_num']
        self.view_dis_deg = view_args['view_dis']
        self.sort_index = np.argsort(self.view_dis_deg)
        self.view_dis_rad = [np.radians(x) for x in view_args['view_dis']]
        self.center_view = view_args['view_dis'].index(0)
        self.img_encoder = build_module(args['img_encoder'])
        self.shared_mlp = build_module(args['shared_mlp'])
        self.latent_mlp = build_module(args['latent_mlp'])
        self.peak_dir_mlp = build_module(args['peak_dir_mlp'])
        self.peak_int_mlp = build_module(args['peak_int_mlp'])

    def forward(self, x):
        """
        x: B, N_view, C, H, W, suppose center view is the first 
        """
        B, N_view, C, H, W = x.shape
        x = x[:, self.sort_index, ...]
        x = x.permute(0, 2, 3, 1, 4).flatten(3)
        x = self.img_encoder(x).permute(0, 2, 3, 1)
        x_flatten = x.flatten(1)
        deep_vector = self.shared_mlp(x_flatten)
        latent_vector = self.latent_mlp(deep_vector)
        peak_dir_vector = self.peak_dir_mlp(deep_vector)
        peak_int_vector = self.peak_int_mlp(deep_vector)
        peak_dir_vector = peak_dir_vector / peak_dir_vector.norm(dim=1, keepdim=True)
        peak_vector = torch.cat([peak_dir_vector, peak_int_vector], dim=-1)
        return (peak_vector, latent_vector)

def __init__(self, args):
    super().__init__()
    self.args = args
    view_args = args['view_setting']
    self.view_num = view_args['view_num']
    self.view_dis_deg = view_args['view_dis']
    self.sort_index = np.argsort(self.view_dis_deg)
    self.view_dis_rad = [np.radians(x) for x in view_args['view_dis']]
    self.center_view = view_args['view_dis'].index(0)
    self.img_encoder = build_module(args['img_encoder'])
    self.shared_mlp = build_module(args['shared_mlp'])
    self.latent_mlp = build_module(args['latent_mlp'])
    self.peak_dir_mlp = build_module(args['peak_dir_mlp'])
    self.peak_int_mlp = build_module(args['peak_int_mlp'])

class AvgMultiView(nn.Module):
    """
    Avg is not suitable.

    use self.attention to fuse latent vector
    use max to fuse peak intensity
    use avg to fuse peak direction
    """

    def __init__(self, args):
        super().__init__()
        self.args = args
        view_args = args['view_setting']
        self.view_num = view_args['view_num']
        self.view_dis_deg = view_args['view_dis']
        self.view_dis_rad = [np.radians(x) for x in view_args['view_dis']]
        self.center_view = view_args['view_dis'].index(0)
        self.crop_H = view_args['camera_H'] // view_args['downsample_for_crop']
        self.crop_W = view_args['camera_W'] // view_args['downsample_for_crop']
        self.camera_vfov = np.degrees(np.arctan2(view_args['camera_H'] / 2, view_args['focal'])) * 2
        self.aspect_ratio = view_args['camera_W'] / view_args['camera_H']
        self.img_encoder = build_module(args['img_encoder'])
        self.shared_mlp = build_module(args['shared_mlp'])
        self.latent_mlp = build_module(args['latent_mlp'])
        int_channel = args['latent_mlp']['args']['layer_channels'][-1]
        self.att = ScaledDotProductAttention(int_channel)
        self.peak_dir_mlp = build_module(args['peak_dir_mlp'])
        self.peak_int_mlp = build_module(args['peak_int_mlp'])

    def forward(self, x):
        """
        x: B, N_view, C, H, W
        """
        B, N_view, _, _, _ = x.shape
        x = x.flatten(0, 1)
        x = self.img_encoder(x).permute(0, 2, 3, 1)
        x_flatten = x.flatten(1)
        deep_vector = self.shared_mlp(x_flatten)
        deep_vector = deep_vector.view(B, N_view, -1)
        latent_vector = self.latent_mlp(deep_vector)
        latent_vector = self.att(latent_vector[:, self.center_view:self.center_view + 1], latent_vector, latent_vector)
        peak_dir_vector = self.peak_dir_mlp(deep_vector)
        for i in range(self.view_num):
            azimuth_rad_i = self.view_dis_rad[i]
            rotation_mat_i = rotation_matrix(azimuth=azimuth_rad_i, elevation=0)
            inv_rotation_mat_i = rotation_matrix(azimuth=-azimuth_rad_i, elevation=0)
            inv_rotation_mat_i = torch.from_numpy(inv_rotation_mat_i).to(x.device).float()
            peak_dir_vector[:, i] = (inv_rotation_mat_i @ peak_dir_vector[:, i].T).T
        peak_dir_vector = peak_dir_vector / peak_dir_vector.norm(dim=-1, keepdim=True)
        peak_dir_vector_sum = peak_dir_vector.mean(dim=1)
        peak_dir_vector_avg = peak_dir_vector_sum / peak_dir_vector_sum.norm(dim=-1, keepdim=True)
        peak_int_vector = self.peak_int_mlp(deep_vector).mean(dim=1)
        peak_vector = torch.cat([peak_dir_vector_avg, peak_int_vector], dim=-1)
        return (peak_vector, latent_vector)

def __init__(self, args):
    super().__init__()
    self.args = args
    view_args = args['view_setting']
    self.view_num = view_args['view_num']
    self.view_dis_deg = view_args['view_dis']
    self.view_dis_rad = [np.radians(x) for x in view_args['view_dis']]
    self.center_view = view_args['view_dis'].index(0)
    self.crop_H = view_args['camera_H'] // view_args['downsample_for_crop']
    self.crop_W = view_args['camera_W'] // view_args['downsample_for_crop']
    self.camera_vfov = np.degrees(np.arctan2(view_args['camera_H'] / 2, view_args['focal'])) * 2
    self.aspect_ratio = view_args['camera_W'] / view_args['camera_H']
    self.img_encoder = build_module(args['img_encoder'])
    self.shared_mlp = build_module(args['shared_mlp'])
    self.latent_mlp = build_module(args['latent_mlp'])
    int_channel = args['latent_mlp']['args']['layer_channels'][-1]
    self.att = ScaledDotProductAttention(int_channel)
    self.peak_dir_mlp = build_module(args['peak_dir_mlp'])
    self.peak_int_mlp = build_module(args['peak_int_mlp'])

def conv3x3(in_planes: int, out_planes: int, stride: int=1, groups: int=1, dilation: int=1) -> nn.Conv2d:
    """3x3 convolution with padding"""
    return nn.Conv2d(in_planes, out_planes, kernel_size=3, stride=stride, padding=dilation, groups=groups, bias=False, dilation=dilation)

def conv1x1(in_planes: int, out_planes: int, stride: int=1) -> nn.Conv2d:
    """1x1 convolution"""
    return nn.Conv2d(in_planes, out_planes, kernel_size=1, stride=stride, bias=False)

class BasicBlock(nn.Module):

    def __init__(self, inplanes: int, planes: int, kernel_size=3, stride: int=1, act: str='relu', use_bn: bool=True):
        super().__init__()
        self.conv1 = nn.Conv2d(inplanes, planes, kernel_size=kernel_size, stride=stride, padding=kernel_size // 2)
        self.conv2 = nn.Conv2d(planes, planes, kernel_size=kernel_size, stride=1, padding=kernel_size // 2)
        if use_bn:
            self.bn1 = nn.BatchNorm2d(planes)
            self.bn2 = nn.BatchNorm2d(planes)
            self.bn3 = nn.BatchNorm2d(planes)
        else:
            self.bn1 = nn.Identity()
            self.bn2 = nn.Identity()
            self.bn3 = nn.Identity()
        if act == 'relu':
            self.act = nn.ReLU(inplace=True)
        elif act == 'selu':
            self.act = nn.SELU(inplace=True)
        elif act == 'elu':
            self.act = nn.ELU(inplace=True)
        if inplanes != planes or stride != 1:
            self.downsample = nn.Sequential(conv1x1(inplanes, planes, stride), self.bn3)
        else:
            self.downsample = None
        self.stride = stride

    def forward(self, x: Tensor) -> Tensor:
        identity = x
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.act(out)
        out = self.conv2(out)
        out = self.bn2(out)
        if self.downsample is not None:
            identity = self.downsample(x)
        out += identity
        out = self.act(out)
        return out

def __init__(self, inplanes: int, planes: int, kernel_size=3, stride: int=1, act: str='relu', use_bn: bool=True):
    super().__init__()
    self.conv1 = nn.Conv2d(inplanes, planes, kernel_size=kernel_size, stride=stride, padding=kernel_size // 2)
    self.conv2 = nn.Conv2d(planes, planes, kernel_size=kernel_size, stride=1, padding=kernel_size // 2)
    if use_bn:
        self.bn1 = nn.BatchNorm2d(planes)
        self.bn2 = nn.BatchNorm2d(planes)
        self.bn3 = nn.BatchNorm2d(planes)
    else:
        self.bn1 = nn.Identity()
        self.bn2 = nn.Identity()
        self.bn3 = nn.Identity()
    if act == 'relu':
        self.act = nn.ReLU(inplace=True)
    elif act == 'selu':
        self.act = nn.SELU(inplace=True)
    elif act == 'elu':
        self.act = nn.ELU(inplace=True)
    if inplanes != planes or stride != 1:
        self.downsample = nn.Sequential(conv1x1(inplanes, planes, stride), self.bn3)
    else:
        self.downsample = None
    self.stride = stride

class UpBasicBlock(nn.Module):

    def __init__(self, inplanes: int, planes: int, kernel_size=3, stride: int=1, act: str='relu', use_bn: bool=True):
        super().__init__()
        self.conv1 = nn.ConvTranspose2d(inplanes, planes, kernel_size=kernel_size, stride=stride, padding=kernel_size // 2, output_padding=kernel_size // 2)
        self.conv2 = nn.Conv2d(planes, planes, kernel_size=kernel_size, stride=1, padding=kernel_size // 2)
        if use_bn:
            self.bn1 = nn.BatchNorm2d(planes)
            self.bn2 = nn.BatchNorm2d(planes)
            self.bn3 = nn.BatchNorm2d(planes)
        else:
            self.bn1 = nn.Identity()
            self.bn2 = nn.Identity()
            self.bn3 = nn.Identity()
        if act == 'relu':
            self.act = nn.ReLU(inplace=True)
        elif act == 'selu':
            self.act = nn.SELU(inplace=True)
        elif act == 'elu':
            self.act = nn.ELU(inplace=True)
        self.stride = stride

    def forward(self, x: Tensor) -> Tensor:
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.act(out)
        out = self.conv2(out)
        out = self.bn2(out)
        out = self.act(out)
        return out

def __init__(self, inplanes: int, planes: int, kernel_size=3, stride: int=1, act: str='relu', use_bn: bool=True):
    super().__init__()
    self.conv1 = nn.ConvTranspose2d(inplanes, planes, kernel_size=kernel_size, stride=stride, padding=kernel_size // 2, output_padding=kernel_size // 2)
    self.conv2 = nn.Conv2d(planes, planes, kernel_size=kernel_size, stride=1, padding=kernel_size // 2)
    if use_bn:
        self.bn1 = nn.BatchNorm2d(planes)
        self.bn2 = nn.BatchNorm2d(planes)
        self.bn3 = nn.BatchNorm2d(planes)
    else:
        self.bn1 = nn.Identity()
        self.bn2 = nn.Identity()
        self.bn3 = nn.Identity()
    if act == 'relu':
        self.act = nn.ReLU(inplace=True)
    elif act == 'selu':
        self.act = nn.SELU(inplace=True)
    elif act == 'elu':
        self.act = nn.ELU(inplace=True)
    self.stride = stride

def build_layer(inplane, plane, kernel_size, stride, block_num, act='relu', use_bn=True):
    module_list = []
    module_list.append(BasicBlock(inplane, plane, kernel_size=kernel_size, stride=stride, act=act, use_bn=use_bn))
    for _ in range(1, block_num):
        module_list.append(BasicBlock(plane, plane, kernel_size=kernel_size, act=act, use_bn=use_bn))
    return nn.Sequential(*module_list)

def build_up_layer(inplane, plane, kernel_size, stride, block_num, act='relu', use_bn=True):
    """
    Here stride refers to upsampling stride
    """
    module_list = []
    module_list.append(UpBasicBlock(inplane, plane, kernel_size=kernel_size, stride=stride, act=act, use_bn=use_bn))
    for _ in range(1, block_num):
        module_list.append(BasicBlock(plane, plane, kernel_size=kernel_size, act=act, use_bn=use_bn))
    return nn.Sequential(*module_list)

class EncoderNet(nn.Module):

    def __init__(self, args):
        super().__init__()
        self.args = args
        layer_num = len(args['layer_channels'])
        layer_channels = args['layer_channels']
        kernel_size = args['kernel_size']
        strides = args['strides']
        block_nums = args['block_nums']
        use_bn = args['use_bn']
        act = args['act']
        inplanes = args['in_ch']
        module_list = []
        for i in range(layer_num):
            module_list.append(build_layer(inplanes, layer_channels[i], kernel_size, strides[i], block_nums[i], act, use_bn))
            inplanes = layer_channels[i]
        self.model = nn.Sequential(*module_list)

    def forward(self, x):
        return self.model(x)

def __init__(self, args):
    super().__init__()
    self.args = args
    layer_num = len(args['layer_channels'])
    layer_channels = args['layer_channels']
    kernel_size = args['kernel_size']
    strides = args['strides']
    block_nums = args['block_nums']
    use_bn = args['use_bn']
    act = args['act']
    inplanes = args['in_ch']
    module_list = []
    for i in range(layer_num):
        module_list.append(build_layer(inplanes, layer_channels[i], kernel_size, strides[i], block_nums[i], act, use_bn))
        inplanes = layer_channels[i]
    self.model = nn.Sequential(*module_list)

class DecoderNet(nn.Module):

    def __init__(self, args):
        super().__init__()
        self.args = args
        layer_num = len(args['layer_channels'])
        layer_channels = args['layer_channels']
        kernel_size = args['kernel_size']
        upstrides = args['upstrides']
        block_nums = args['block_nums']
        use_bn = args['use_bn']
        act = args['act']
        inplanes = args['in_ch']
        module_list = []
        for i in range(layer_num):
            module_list.append(build_up_layer(inplanes, layer_channels[i], kernel_size, upstrides[i], block_nums[i], act, use_bn))
            inplanes = layer_channels[i]
        self.model = nn.Sequential(*module_list)

    def forward(self, x):
        return self.model(x)

def __init__(self, args):
    super().__init__()
    self.args = args
    layer_num = len(args['layer_channels'])
    layer_channels = args['layer_channels']
    kernel_size = args['kernel_size']
    upstrides = args['upstrides']
    block_nums = args['block_nums']
    use_bn = args['use_bn']
    act = args['act']
    inplanes = args['in_ch']
    module_list = []
    for i in range(layer_num):
        module_list.append(build_up_layer(inplanes, layer_channels[i], kernel_size, upstrides[i], block_nums[i], act, use_bn))
        inplanes = layer_channels[i]
    self.model = nn.Sequential(*module_list)

class UNet(nn.Module):

    def __init__(self, args):
        super().__init__()
        self.args = args
        layer_num = len(args['layer_channels'])
        self.layer_num = layer_num
        layer_channels = args['layer_channels']
        strides = args['strides']
        block_nums = args['block_nums']
        up_in_channels = args['up_in_channels']
        up_layer_channels = args['up_layer_channels']
        up_strides = args['up_strides']
        up_block_nums = args['up_block_nums']
        kernel_size = args['kernel_size']
        use_bn = args['use_bn']
        act = args['act']
        self.inject_latent = args['inject_latent']
        inplanes = args['in_ch']
        self.final_conv_to_RGB = args['final_conv_to_RGB']
        final_act = args.get('final_conv_to_RGB_act', 'relu')
        if final_act == 'relu':
            self.final_act = nn.ReLU()
        elif final_act == 'sigmoid':
            self.final_act = nn.Sigmoid()
        self.module_dict = nn.ModuleDict()
        for i in range(layer_num):
            self.module_dict[f'down{i}'] = build_layer(inplanes, layer_channels[i], kernel_size, strides[i], block_nums[i], act, use_bn)
            inplanes = layer_channels[i]
            self.module_dict[f'up{i}'] = build_up_layer(up_in_channels[i], up_layer_channels[i], kernel_size, up_strides[i], up_block_nums[i], act, use_bn)
        if self.final_conv_to_RGB:
            self.final_conv = nn.Sequential(nn.Conv2d(up_layer_channels[-1], 3, kernel_size=3, stride=1, padding=1), self.final_act)

    def forward(self, x, latent_feature=None):
        """
        Args:
            x : tensor 
                shape [N, C, H, W], C = 7
            latent_feature : tensor
                shape [N, C2, h, w], the small feature map from LDR encoder
        """
        x_downs = []
        for i in range(self.layer_num):
            x = self.module_dict[f'down{i}'](x)
            x_downs.append(x)
        if self.inject_latent:
            x = torch.cat([x, latent_feature], dim=1)
        x = self.module_dict[f'up0'](x)
        for i in range(1, self.layer_num):
            x = torch.cat([x, x_downs[self.layer_num - 1 - i]], dim=1)
            x = self.module_dict[f'up{i}'](x)
        if self.final_conv_to_RGB:
            x = self.final_conv(x)
        return x

def __init__(self, args):
    super().__init__()
    self.args = args
    layer_num = len(args['layer_channels'])
    self.layer_num = layer_num
    layer_channels = args['layer_channels']
    strides = args['strides']
    block_nums = args['block_nums']
    up_in_channels = args['up_in_channels']
    up_layer_channels = args['up_layer_channels']
    up_strides = args['up_strides']
    up_block_nums = args['up_block_nums']
    kernel_size = args['kernel_size']
    use_bn = args['use_bn']
    act = args['act']
    self.inject_latent = args['inject_latent']
    inplanes = args['in_ch']
    self.final_conv_to_RGB = args['final_conv_to_RGB']
    final_act = args.get('final_conv_to_RGB_act', 'relu')
    if final_act == 'relu':
        self.final_act = nn.ReLU()
    elif final_act == 'sigmoid':
        self.final_act = nn.Sigmoid()
    self.module_dict = nn.ModuleDict()
    for i in range(layer_num):
        self.module_dict[f'down{i}'] = build_layer(inplanes, layer_channels[i], kernel_size, strides[i], block_nums[i], act, use_bn)
        inplanes = layer_channels[i]
        self.module_dict[f'up{i}'] = build_up_layer(up_in_channels[i], up_layer_channels[i], kernel_size, up_strides[i], up_block_nums[i], act, use_bn)
    if self.final_conv_to_RGB:
        self.final_conv = nn.Sequential(nn.Conv2d(up_layer_channels[-1], 3, kernel_size=3, stride=1, padding=1), self.final_act)

class MLP(nn.Module):

    def __init__(self, args):
        super().__init__()
        self.args = args
        layer_num = len(args['layer_channels'])
        layer_channels = args['layer_channels']
        act = args['act']
        if act == 'relu':
            self.act = nn.ReLU(inplace=True)
        elif act == 'selu':
            self.act = nn.SELU(inplace=True)
        elif act == 'elu':
            self.act = nn.ELU(inplace=True)
        elif act == 'none':
            self.act = nn.Identity()
        inplanes = args['in_ch']
        module_list = []
        for i in range(layer_num):
            module_list.append(nn.Linear(inplanes, layer_channels[i]))
            module_list.append(self.act)
            inplanes = layer_channels[i]
        self.model = nn.Sequential(*module_list)

    def forward(self, x):
        return self.model(x)

def __init__(self, args):
    super().__init__()
    self.args = args
    layer_num = len(args['layer_channels'])
    layer_channels = args['layer_channels']
    act = args['act']
    if act == 'relu':
        self.act = nn.ReLU(inplace=True)
    elif act == 'selu':
        self.act = nn.SELU(inplace=True)
    elif act == 'elu':
        self.act = nn.ELU(inplace=True)
    elif act == 'none':
        self.act = nn.Identity()
    inplanes = args['in_ch']
    module_list = []
    for i in range(layer_num):
        module_list.append(nn.Linear(inplanes, layer_channels[i]))
        module_list.append(self.act)
        inplanes = layer_channels[i]
    self.model = nn.Sequential(*module_list)

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

def __init__(self, args):
    super().__init__()
    self.weight = args['weight']
    self.gamma = args['gamma']
    self.alpha = args['alpha']

class LogEncodedL2Loss(nn.Module):

    def __init__(self, args):
        super(LogEncodedL2Loss, self).__init__()
        self.weight = args['weight']

    def forward(self, pred, target, mask=None):
        loss_map = torch.pow(torch.log(pred + 1 + eps) - torch.log(target + 1 + eps), 2)
        if mask is not None:
            loss = (loss_map * mask).sum() / mask.sum()
        else:
            loss = loss_map.mean()
        return loss * self.weight

def __init__(self, args):
    super(LogEncodedL2Loss, self).__init__()
    self.weight = args['weight']

class L2Loss(nn.Module):

    def __init__(self, args):
        super(L2Loss, self).__init__()
        self.weight = args['weight']

    def forward(self, pred, target, mask=None):
        loss_map = torch.pow(pred - target, 2)
        if mask is not None:
            loss = (loss_map * mask).sum() / mask.sum()
        else:
            loss = loss_map.mean()
        return loss * self.weight

def __init__(self, args):
    super(L2Loss, self).__init__()
    self.weight = args['weight']

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

def __init__(self, args):
    super(L1Loss, self).__init__()
    self.weight = args['weight']

class L1AngularLoss(nn.Module):

    def __init__(self, args):
        super(L1AngularLoss, self).__init__()
        self.weight = args['weight']

    def forward(self, pred, target):
        """
            pred/target: [B, 3]
        """
        cosine_similarity = (pred * target).sum(dim=1).clamp(-1 + eps, 1 - eps)
        angle_diff = torch.acos(cosine_similarity)
        loss = torch.abs(angle_diff).mean()
        return loss * self.weight

def __init__(self, args):
    super(L1AngularLoss, self).__init__()
    self.weight = args['weight']

class AngleClassificationLoss(nn.Module):

    def __init__(self, args):
        super().__init__()
        self.weight = args['weight']
        self.num_bins = args['num_bins']
        self.cross_entropy = nn.CrossEntropyLoss()

    def forward(self, pred, target):
        """
        pred : torch.tensor
            unnormalized logits, shape [B, num_bins]
        target : torch.tensor
            shape [B, ], ground-truth angle in [0, 2pi]
        """
        bin_indices = (target / (2 * np.pi / self.num_bins)).floor().long()
        loss = self.cross_entropy(pred, bin_indices) * self.weight
        return loss

def __init__(self, args):
    super().__init__()
    self.weight = args['weight']
    self.num_bins = args['num_bins']
    self.cross_entropy = nn.CrossEntropyLoss()

