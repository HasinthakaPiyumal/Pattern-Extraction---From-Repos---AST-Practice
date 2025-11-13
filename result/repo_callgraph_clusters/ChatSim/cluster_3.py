# Cluster 3

class ChatSim:

    def __init__(self, config):
        self.config = config
        self.scene = Scene(config['scene'])
        agents_config = config['agents']
        self.project_manager = ProjectManager(agents_config['project_manager'])
        self.asset_select_agent = AssetSelectAgent(agents_config['asset_select_agent'])
        self.deletion_agent = DeletionAgent(agents_config['deletion_agent'])
        self.foreground_rendering_agent = ForegroundRenderingAgent(agents_config['foreground_rendering_agent'])
        self.motion_agent = MotionAgent(agents_config['motion_agent'])
        self.view_adjust_agent = ViewAdjustAgent(agents_config['view_adjust_agent'])
        if agents_config['background_rendering_agent'].get('scene_representation', 'nerf') == 'nerf':
            self.background_rendering_agent = BackgroundRenderingAgent(agents_config['background_rendering_agent'])
        else:
            self.background_rendering_agent = BackgroundRendering3DGSAgent(agents_config['background_rendering_agent'])
        self.tech_agents = {'asset_select_agent': self.asset_select_agent, 'background_rendering_agent': self.background_rendering_agent, 'deletion_agent': self.deletion_agent, 'foreground_rendering_agent': self.foreground_rendering_agent, 'motion_agent': self.motion_agent, 'view_adjust_agent': self.view_adjust_agent}
        self.current_prompt = 'An empty prompt'

    def setup_init_frame(self):
        """Setup initial frame for ChatSim's reasoning and rendering.
        """
        if not os.path.exists(self.scene.init_img_path):
            print(f'{colored('[Note]', color='red', attrs=['bold'])} ', f'{colored('can not find init image, rendering it for the first time')}\n')
            self.background_rendering_agent.func_render_background(self.scene)
            imageio.imwrite(self.scene.init_img_path, self.scene.current_images[0])
        else:
            self.scene.current_images = [imageio.imread(self.scene.init_img_path)] * self.scene.frames

    def execute_llms(self, prompt):
        """Entry of ChatSim's reasoning.
        We perform multi-LLM reasoning for the user's prompt

        Input:
            prompt : str
                language prompt to ChatSim.
        """
        self.scene.setup_cars()
        self.current_prompt = prompt
        tasks = self.project_manager.decompose_prompt(self.scene, prompt)
        for task in tasks.values():
            print(f'{colored('[Performing Single Prompt]', on_color='on_blue', attrs=['bold'])} {colored(task, attrs=['bold'])}\n')
            self.project_manager.dispatch_task(self.scene, task, self.tech_agents)
        print(colored('scene.added_cars_dict', color='red', attrs=['bold']), end=' ')
        pprint.pprint(self.scene.added_cars_dict.keys())
        print(colored('scene.removed_cars', color='red', attrs=['bold']), end=' ')
        pprint.pprint(self.scene.removed_cars)

    def execute_funcs(self):
        """Entry of ChatSim's rendering functions
        We perform agent's functions following the self.scene's configuration.
        self.scene's configuration are updated in self.execute_llms()
        """
        self.background_rendering_agent.func_render_background(self.scene)
        self.deletion_agent.func_inpaint_scene(self.scene)
        self.asset_select_agent.func_retrieve_blender_file(self.scene)
        self.foreground_rendering_agent.func_blender_add_cars(self.scene)
        generate_video(self.scene, self.current_prompt)

def setup_init_frame(self):
    """Setup initial frame for ChatSim's reasoning and rendering.
        """
    if not os.path.exists(self.scene.init_img_path):
        print(f'{colored('[Note]', color='red', attrs=['bold'])} ', f'{colored('can not find init image, rendering it for the first time')}\n')
        self.background_rendering_agent.func_render_background(self.scene)
        imageio.imwrite(self.scene.init_img_path, self.scene.current_images[0])
    else:
        self.scene.current_images = [imageio.imread(self.scene.init_img_path)] * self.scene.frames

def semantic_seg(image_data_input, semantic_folder_name, sky_folder_name):
    sky_masks_dir = image_data_input.rstrip('/') + '_' + sky_folder_name
    segformer_path = Path(__file__).parent / 'SegFormer'
    segformer_path = segformer_path.as_posix()
    config = os.path.join(segformer_path, 'local_configs', 'segformer', 'B5', 'segformer.b5.1024x1024.city.160k.py')
    checkpoint = os.path.join(segformer_path, 'segformer.b5.1024x1024.city.160k.pth')
    model = init_segmentor(config, checkpoint, device='cuda')
    for filename in os.listdir(image_data_input):
        image_path = os.path.join(image_data_input, filename)
        result = inference_segmentor(model, image_path)
        semantic_mask = result[0].astype(np.uint8)
        sky_mask = (semantic_mask == 10).astype(np.uint8)
        sky_mask = (1 - sky_mask) * 255
        sky_mask_path = os.path.join(sky_masks_dir, filename) + '.png'
        os.makedirs(os.path.dirname(sky_mask_path), exist_ok=True)
        cv2.imwrite(sky_mask_path, sky_mask)

@click.command()
@click.option('--image_data_input', '-i', default='/home/jiahuih/workspace/yiflu-workspace/video_for_xcube++/000', help='The directory of the waymo data')
@click.option('--semantic_folder_name', default='semantic_masks', help='The name of folder to save the semantic masks (same directory as images)')
@click.option('--sky_mask_folder_name', default='sky_masks', help='The name of folder to save the sky masks (same directory as images)')
@click.option('--overwrite', '-o', is_flag=True, help='Whether to overwrite the existing masks')
def main(image_data_input, semantic_folder_name, sky_mask_folder_name, overwrite):
    semantic_seg(image_data_input, semantic_folder_name, sky_mask_folder_name)

def read_xml_save_npy(data_dir):
    """
    We will save `cams_meta_metashape.npy` (RUB convention)
    not `poses_bounds_metashape.npy` (DRB) now.
    """
    print('Parsing Metashape results')
    intrinsic, (width, height), dist_params = intrinsics_from_xml(os.path.join(data_dir, 'camera.xml'))
    poses_RDF, labels_sort = extrinsics_from_xml(os.path.join(data_dir, 'camera.xml'))
    poses_RDF = np.stack(poses_RDF, axis=0)
    poses_RUB = np.concatenate((poses_RDF[:, :, 0:1], -poses_RDF[:, :, 1:2], -poses_RDF[:, :, 2:3], poses_RDF[:, :, 3:]), axis=-1)
    poses_RUB = poses_RUB[:, :3, :]
    N = poses_RUB.shape[0]
    intrinsic = intrinsic.reshape(1, 3, 3).repeat(N, axis=0)
    dist_params = np.array(dist_params).reshape(1, 4).repeat(N, axis=0)
    bounds = np.array([0.1, 999]).reshape(1, 2).repeat(N, axis=0)
    cams_meta = np.concatenate([poses_RUB.reshape(N, -1), intrinsic.reshape(N, -1), dist_params.reshape(N, -1), bounds.reshape(N, -1)], axis=1)
    np.save(os.path.join(data_dir, 'cams_meta_metashape.npy'), cams_meta)

class NeRFSceneManager(SceneManager):
    """COLMAP pose loader.

    Minor NeRF-specific extension to the third_party Python COLMAP loader:
    google3/third_party/py/pycolmap/scene_manager.py
    """

    def __init__(self, data_dir, use_undistorted=False):
        """
        use_undistorted: bool
            gaussians splatting needs undistorted camera intrinsics,
            McNeRF does not need undistorted camera intrinsics.

            But the images in the root folder is distorted. The undistorted version is in data_dir/colmap/sparse_undistorted/images
        """
        if use_undistorted:
            sfm_dir = pjoin(data_dir, 'colmap/sparse_undistorted/sparse')
        else:
            sfm_dir = pjoin(data_dir, 'colmap/sparse/not_align/0')
        assert os.path.exists(sfm_dir)
        super(NeRFSceneManager, self).__init__(sfm_dir)

    def process(self) -> Tuple[Sequence[Text], np.ndarray, np.ndarray, Optional[Mapping[Text, float]], camera_utils.ProjectionType]:
        """Applies NeRF-specific postprocessing to the loaded pose data.

        Returns:
          a tuple [image_names, poses, pixtocam, distortion_params].
          image_names:  contains the only the basename of the images.
          poses: [N, 4, 4] array containing the camera to world matrices.
          pixtocam: [N, 3, 3] array containing the camera to pixel space matrices.
          distortion_params: mapping of distortion param name to distortion
            parameters. Cameras share intrinsics. Valid keys are k1, k2, p1 and p2.
        """
        self.load_cameras()
        self.load_images()
        self.load_points3D()
        cam = self.cameras[1]
        fx, fy, cx, cy = (cam.fx, cam.fy, cam.cx, cam.cy)
        pixtocam = np.linalg.inv(camera_utils.intrinsic_matrix(fx, fy, cx, cy))
        imdata = self.images
        w2c_mats = []
        bottom = np.array([0, 0, 0, 1]).reshape(1, 4)
        for k in imdata:
            im = imdata[k]
            rot = im.R()
            trans = im.tvec.reshape(3, 1)
            w2c = np.concatenate([np.concatenate([rot, trans], 1), bottom], axis=0)
            w2c_mats.append(w2c)
        w2c_mats = np.stack(w2c_mats, axis=0)
        c2w_mats = np.linalg.inv(w2c_mats)
        poses = c2w_mats[:, :3, :4]
        names = [imdata[k].name for k in imdata]
        poses = poses @ np.diag([1, -1, -1, 1])
        type_ = cam.camera_type
        if type_ == 0 or type_ == 'SIMPLE_PINHOLE':
            params = None
            camtype = camera_utils.ProjectionType.PERSPECTIVE
        elif type_ == 1 or type_ == 'PINHOLE':
            params = None
            camtype = camera_utils.ProjectionType.PERSPECTIVE
        if type_ == 2 or type_ == 'SIMPLE_RADIAL':
            params = {k: 0.0 for k in ['k1', 'k2', 'k3', 'p1', 'p2']}
            params['k1'] = cam.k1
            camtype = camera_utils.ProjectionType.PERSPECTIVE
        elif type_ == 3 or type_ == 'RADIAL':
            params = {k: 0.0 for k in ['k1', 'k2', 'k3', 'p1', 'p2']}
            params['k1'] = cam.k1
            params['k2'] = cam.k2
            camtype = camera_utils.ProjectionType.PERSPECTIVE
        elif type_ == 4 or type_ == 'OPENCV':
            params = {k: 0.0 for k in ['k1', 'k2', 'k3', 'p1', 'p2']}
            params['k1'] = cam.k1
            params['k2'] = cam.k2
            params['p1'] = cam.p1
            params['p2'] = cam.p2
            camtype = camera_utils.ProjectionType.PERSPECTIVE
        elif type_ == 5 or type_ == 'OPENCV_FISHEYE':
            params = {k: 0.0 for k in ['k1', 'k2', 'k3', 'k4']}
            params['k1'] = cam.k1
            params['k2'] = cam.k2
            params['k3'] = cam.k3
            params['k4'] = cam.k4
            camtype = camera_utils.ProjectionType.FISHEYE
        return (names, poses, pixtocam, params, camtype)

def __init__(self, data_dir, use_undistorted=False):
    """
        use_undistorted: bool
            gaussians splatting needs undistorted camera intrinsics,
            McNeRF does not need undistorted camera intrinsics.

            But the images in the root folder is distorted. The undistorted version is in data_dir/colmap/sparse_undistorted/images
        """
    if use_undistorted:
        sfm_dir = pjoin(data_dir, 'colmap/sparse_undistorted/sparse')
    else:
        sfm_dir = pjoin(data_dir, 'colmap/sparse/not_align/0')
    assert os.path.exists(sfm_dir)
    super(NeRFSceneManager, self).__init__(sfm_dir)

def process(self) -> Tuple[Sequence[Text], np.ndarray, np.ndarray, Optional[Mapping[Text, float]], camera_utils.ProjectionType]:
    """Applies NeRF-specific postprocessing to the loaded pose data.

        Returns:
          a tuple [image_names, poses, pixtocam, distortion_params].
          image_names:  contains the only the basename of the images.
          poses: [N, 4, 4] array containing the camera to world matrices.
          pixtocam: [N, 3, 3] array containing the camera to pixel space matrices.
          distortion_params: mapping of distortion param name to distortion
            parameters. Cameras share intrinsics. Valid keys are k1, k2, p1 and p2.
        """
    self.load_cameras()
    self.load_images()
    self.load_points3D()
    cam = self.cameras[1]
    fx, fy, cx, cy = (cam.fx, cam.fy, cam.cx, cam.cy)
    pixtocam = np.linalg.inv(camera_utils.intrinsic_matrix(fx, fy, cx, cy))
    imdata = self.images
    w2c_mats = []
    bottom = np.array([0, 0, 0, 1]).reshape(1, 4)
    for k in imdata:
        im = imdata[k]
        rot = im.R()
        trans = im.tvec.reshape(3, 1)
        w2c = np.concatenate([np.concatenate([rot, trans], 1), bottom], axis=0)
        w2c_mats.append(w2c)
    w2c_mats = np.stack(w2c_mats, axis=0)
    c2w_mats = np.linalg.inv(w2c_mats)
    poses = c2w_mats[:, :3, :4]
    names = [imdata[k].name for k in imdata]
    poses = poses @ np.diag([1, -1, -1, 1])
    type_ = cam.camera_type
    if type_ == 0 or type_ == 'SIMPLE_PINHOLE':
        params = None
        camtype = camera_utils.ProjectionType.PERSPECTIVE
    elif type_ == 1 or type_ == 'PINHOLE':
        params = None
        camtype = camera_utils.ProjectionType.PERSPECTIVE
    if type_ == 2 or type_ == 'SIMPLE_RADIAL':
        params = {k: 0.0 for k in ['k1', 'k2', 'k3', 'p1', 'p2']}
        params['k1'] = cam.k1
        camtype = camera_utils.ProjectionType.PERSPECTIVE
    elif type_ == 3 or type_ == 'RADIAL':
        params = {k: 0.0 for k in ['k1', 'k2', 'k3', 'p1', 'p2']}
        params['k1'] = cam.k1
        params['k2'] = cam.k2
        camtype = camera_utils.ProjectionType.PERSPECTIVE
    elif type_ == 4 or type_ == 'OPENCV':
        params = {k: 0.0 for k in ['k1', 'k2', 'k3', 'p1', 'p2']}
        params['k1'] = cam.k1
        params['k2'] = cam.k2
        params['p1'] = cam.p1
        params['p2'] = cam.p2
        camtype = camera_utils.ProjectionType.PERSPECTIVE
    elif type_ == 5 or type_ == 'OPENCV_FISHEYE':
        params = {k: 0.0 for k in ['k1', 'k2', 'k3', 'k4']}
        params['k1'] = cam.k1
        params['k2'] = cam.k2
        params['k3'] = cam.k3
        params['k4'] = cam.k4
        camtype = camera_utils.ProjectionType.FISHEYE
    return (names, poses, pixtocam, params, camtype)

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

def align(data_dir, src_cams_meta='cams_meta_metashape.npy', dst_cams_meta='cams_meta_waymo.npy'):
    if src_cams_meta == 'cams_meta_metashape.npy':
        print("Aligning Metashape's coordinates with Waymo's coordinates")
    elif src_cams_meta == 'cams_meta_colmap.npy':
        print("Aligning Colmap's coordinates with Waymo's coordinates")
    cams_meta_data_source = np.load(os.path.join(data_dir, src_cams_meta))
    cams_meta_data_target = np.load(os.path.join(data_dir, dst_cams_meta))
    extrinsic_source = cams_meta_data_source[:, :12].reshape(-1, 3, 4)
    last_row = np.zeros((extrinsic_source.shape[0], 1, 4))
    last_row[:, :, -1] = 1
    extrinsic_source = np.concatenate((extrinsic_source, last_row), axis=1)
    extrinsic_target = cams_meta_data_target[:, :12].reshape(-1, 3, 4)
    last_row = np.zeros((extrinsic_target.shape[0], 1, 4))
    last_row[:, :, -1] = 1
    extrinsic_target = np.concatenate((extrinsic_target, last_row), axis=1)
    scale = np.linalg.norm(extrinsic_source[3, :3, -1] - extrinsic_source[0, :3, -1]) / np.linalg.norm(extrinsic_target[3, :3, -1] - extrinsic_target[0, :3, -1])
    rotate_0_target = extrinsic_target[0, :3, :3]
    rotate_0_source = extrinsic_source[0, :3, :3]
    rotate_source_world_to_target_world = rotate_0_target @ np.linalg.inv(rotate_0_source)
    rotate_source_world_to_target_world = rotate_source_world_to_target_world[None, ...]
    extrinsic_results = np.zeros_like(extrinsic_source)
    extrinsic_results[:, :3, :3] = rotate_source_world_to_target_world @ extrinsic_source[:, :3, :3]
    delta_translation_in_source_world = extrinsic_source[:, :3, -1:] - extrinsic_source[0:1, :3, -1:]
    delta_translation_in_target_world = rotate_source_world_to_target_world @ delta_translation_in_source_world / scale
    extrinsic_results[:, :3, -1:] = delta_translation_in_target_world + extrinsic_target[0:1, :3, -1:]
    extrinsic_results[:, -1, -1] = 1
    cams_meta_data_source[:, :12] = extrinsic_results[:, :3, :].reshape(-1, 12)
    data = np.ascontiguousarray(np.array(cams_meta_data_source).astype(np.float64))
    if src_cams_meta == 'cams_meta_metashape.npy':
        print(f'\n{colored('[Imporant]', 'green', attrs=['bold'])} save to cams_meta.npy')
        np.save(os.path.join(data_dir, 'cams_meta.npy'), data)
    if src_cams_meta == 'cams_meta_colmap.npy':
        print(f'\n{colored('[Imporant]', 'green', attrs=['bold'])} Save to colmap/sparse_undistorted/cams_meta.npy')
        print(f'cams_meta.npy from metashape (in the root folder) will not be overwritten.')
        np.save(os.path.join(data_dir, 'colmap/sparse_undistorted/cams_meta.npy'), data)
        src_point3D_path = os.path.join(data_dir, 'colmap/sparse_undistorted/sparse/points3D.bin')
        dst_point3D_path = os.path.join(data_dir, 'colmap/sparse_undistorted/points3D_waymo.ply')
        points = load_colmap_sparse_points(src_point3D_path)
        points3D = points['xyz']
        points3D_colors = points['rgb']
        delta_translation_in_source_world = points3D - np.expand_dims(extrinsic_source[0, :3, -1], axis=0)
        delta_translation_in_source_world = delta_translation_in_source_world[..., np.newaxis]
        delta_translation_in_target_world = rotate_source_world_to_target_world @ delta_translation_in_source_world / scale
        translation_0_target = extrinsic_target[0:1, :3, -1:]
        points3D_in_target_world = delta_translation_in_target_world + translation_0_target
        sfm_points = np.squeeze(points3D_in_target_world)
        sfm_colors = points3D_colors / 255.0
        lidar_open3d = o3d.io.read_point_cloud(os.path.join(data_dir, 'point_cloud/000_TOP.ply'))
        lidar_points = np.array(lidar_open3d.points)
        lidar_colors = np.full(lidar_points.shape, 0.3)
        mask = lidar_points[:, 0] > 0
        lidar_points = lidar_points[mask]
        lidar_colors = lidar_colors[mask]
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(np.concatenate([sfm_points, lidar_points], axis=0))
        pcd.colors = o3d.utility.Vector3dVector(np.concatenate([sfm_colors, lidar_colors], axis=0))
        o3d.io.write_point_cloud(dst_point3D_path, pcd)

def get_shutter(filename, save_path, start_frame=0, end_frame=40, normalize=True):
    if not os.path.exists(save_path):
        os.mkdir(save_path)
    dataset = tf.data.TFRecordDataset(filename, compression_type='')
    dataset_iter = list(dataset.as_numpy_iterator())
    frame = open_dataset.Frame()
    print(f'{filename}')
    shutter_save = []
    for i, frame_data in tqdm(enumerate(dataset_iter)):
        if i < start_frame or i >= end_frame:
            continue
        frame.ParseFromString(frame_data)
        for image in frame.images:
            if open_dataset.CameraName.Name.Name(image.name) in CAMERAS:
                shutter_save.append(image.shutter)
    shutter_save = np.array(shutter_save)
    if normalize:
        mean = shutter_save.mean()
        std = shutter_save.std()
        shutter_save = (shutter_save - mean) / std
    for i in range(len(shutter_save)):
        filename = f'{save_path}/{str(i).zfill(3)}.txt'
        with open(filename, 'w') as f:
            f.write(str(shutter_save[i]))

def main():
    args = parse_args()
    tfrecord_path = args.tfrecord_dir
    export_data = not args.no_data
    scene_name = tfrecord_path.split('/')[-1].split('.')[0]
    scene_name = scene_name[scene_name.find('segment'):]
    saving_dir = os.path.join(args.nerf_data_dir, scene_name)
    if not isinstance(tfrecord_path, list):
        tfrecord_path = [tfrecord_path]
    if not os.path.isdir(saving_dir):
        os.makedirs(saving_dir, exist_ok=True)
    isotropic_focal = lambda intrinsic_dict: intrinsic_dict['f_u'] == intrinsic_dict['f_v']
    if SINGLE_TRACK_INFO_FILE:
        tracking_info = {}
    print('Processing file ', tfrecord_path)
    if not os.path.isdir(os.path.join(saving_dir, 'images_all')):
        os.mkdir(os.path.join(saving_dir, 'images_all'))
    if not os.path.isdir(os.path.join(saving_dir, 'images')):
        os.mkdir(os.path.join(saving_dir, 'images'))
    if not os.path.isdir(os.path.join(saving_dir, 'point_cloud')):
        os.mkdir(os.path.join(saving_dir, 'point_cloud'))
    if not SINGLE_TRACK_INFO_FILE:
        if not os.path.isdir(os.path.join(saving_dir, 'tracking')):
            os.mkdir(os.path.join(saving_dir, 'tracking'))
    dataset = tf.data.TFRecordDataset(tfrecord_path, compression_type='')
    frames = []
    for f_num, data in enumerate(tqdm(dataset)):
        frame = open_dataset.Frame()
        frames.append(frame)
        frame.ParseFromString(bytearray(data.numpy()))
        pose = np.zeros([len(frame.images), 4, 4])
        im_paths = {}
        pcd_paths = {}
        if SAVE_INTRINSIC:
            intrinsic = np.zeros([len(frame.images), 9])
        extrinsic = np.zeros_like(pose)
        width, height, camera_labels = (np.zeros([len(frame.images)]), np.zeros([len(frame.images)]), defaultdict(dict))
        for im in frame.images:
            saving_name = os.path.join(saving_dir, 'images_all', '%03d_%s.png' % (f_num, open_dataset.CameraName.Name.Name(im.name)))
            if not DEBUG and export_data:
                im_array = tf.image.decode_jpeg(im.image).numpy()
                imageio.imwrite(saving_name, im_array, compress_level=3)
            pose[im.name - 1, :, :] = np.reshape(im.pose.transform, [4, 4])
            im_paths[im.name] = saving_name
            extrinsic[im.name - 1, :, :] = np.reshape(frame.context.camera_calibrations[im.name - 1].extrinsic.transform, [4, 4])
            if SAVE_INTRINSIC:
                intrinsic[im.name - 1, :] = frame.context.camera_calibrations[im.name - 1].intrinsic
                assert isotropic_focal(read_intrinsic(intrinsic[im.name - 1, :])), 'Unexpected difference between f_u and f_v.'
            width[im.name - 1] = frame.context.camera_calibrations[im.name - 1].width
            height[im.name - 1] = frame.context.camera_calibrations[im.name - 1].height
            for obj_label in frame.projected_lidar_labels[im.name - 1].labels:
                camera_labels[im.name][obj_label.id.replace('_' + open_dataset.CameraName.Name.Name(im.name), '')] = extract_label_fields(obj_label, 2)
        laser_calib = np.zeros([len(frame.lasers), 4, 4])
        if export_data:
            range_images, camera_projections, seg_labels, range_image_top_pose = frame_utils.parse_range_image_and_camera_projection(frame)
            points, cp_points = frame_utils.convert_range_image_to_point_cloud(frame, range_images, camera_projections, range_image_top_pose)
        else:
            points = np.empty([len(frame.lasers), 1])
        laser_mapping = {}
        for laser, pts in zip(frame.lasers, points):
            saving_name = os.path.join(saving_dir, 'point_cloud', '%03d_%s.ply' % (f_num, open_dataset.LaserName.Name.Name(laser.name)))
            if export_data and f_num == 0:
                pcd = o3d.geometry.PointCloud()
                pcd.points = o3d.utility.Vector3dVector(pts)
                o3d.io.write_point_cloud(saving_name, pcd)
            calib_id = int(np.where(np.array([cali.name for cali in frame.context.laser_calibrations[:5]]) == laser.name)[0])
            laser_calib[laser.name - 1, :, :] = np.reshape(frame.context.laser_calibrations[calib_id].extrinsic.transform, [4, 4])
            pcd_paths[laser.name] = saving_name
            laser_mapping.update({open_dataset.LaserName.Name.Name(laser.name): calib_id})
        if 'intrinsic' in tracking_info:
            assert np.all(tracking_info['intrinsic'] == intrinsic) and np.all(tracking_info['width'] == width) and np.all(tracking_info['height'] == height)
        else:
            tracking_info['intrinsic'], tracking_info['width'], tracking_info['height'] = (intrinsic, width, height)
        dict_2_save = {'per_cam_veh_pose': pose, 'cam2veh': extrinsic, 'im_paths': im_paths, 'width': width, 'height': height, 'veh2laser': laser_calib, 'pcd_paths': pcd_paths, 'focal': intrinsic[:, 0]}
        if SAVE_INTRINSIC and SINGLE_TRACK_INFO_FILE:
            dict_2_save['intrinsic'] = intrinsic
        lidar_labels = {}
        for obj_label in frame.laser_labels:
            lidar_labels[obj_label.id] = extract_label_fields(obj_label, 3)
        dict_2_save['lidar_labels'] = lidar_labels
        dict_2_save['camera_labels'] = camera_labels
        dict_2_save['veh_pose'] = np.reshape(frame.pose.transform, [4, 4])
        dict_2_save['timestamp'] = frame.timestamp_micros
        tracking_info[0, f_num] = deepcopy(dict_2_save)
    with open(os.path.join(saving_dir, 'tracking_info%s.pkl' % ('_debug' if DEBUG else '')), 'wb') as f:
        pickle.dump(tracking_info, f)
    transform = np.reshape(np.array(frames[args.start_frame].pose.transform), [4, 4])
    transform = np.linalg.inv(transform)
    road_edges = []
    lanes = []
    for i in range(len(frames[0].map_features)):
        if len(frames[0].map_features[i].lane.polyline) > 0:
            curr_lane = []
            for node in frames[0].map_features[i].lane.polyline:
                node_position = np.ones(4)
                node_position[0] = node.x
                node_position[1] = node.y
                node_position[2] = node.z
                curr_lane.append(node_position)
            curr_lane = np.stack(curr_lane)
            curr_lane = np.transpose(np.matmul(transform, np.transpose(curr_lane)))[:, 0:3]
            lanes.append(curr_lane)
        if len(frames[0].map_features[i].road_edge.polyline) > 0:
            curr_edge = []
            for node in frames[0].map_features[i].road_edge.polyline:
                node_position = np.ones(4)
                node_position[0] = node.x
                node_position[1] = node.y
                node_position[2] = node.z
                curr_edge.append(node_position)
            curr_edge = np.stack(curr_edge)
            curr_edge = np.transpose(np.matmul(transform, np.transpose(curr_edge)))[:, 0:3]
            road_edges.append(curr_edge)
    x_min = -30
    x_max = 50
    y_min = -20
    y_max = 20
    cropped_road_edges = []
    for edge in road_edges:
        new_road_edge = []
        for i in range(edge.shape[0]):
            if edge[i, 0] < x_min or edge[i, 0] > x_max or edge[i, 1] < y_min or (edge[i, 1] > y_max):
                continue
            new_road_edge.append(edge[i])
        if len(new_road_edge) > 0:
            new_road_edge = np.stack(new_road_edge)
            cropped_road_edges.append(new_road_edge)
    cropped_lanes = []
    for lane in lanes:
        new_lane = []
        for i in range(lane.shape[0]):
            if lane[i, 0] < x_min or lane[i, 0] > x_max or lane[i, 1] < y_min or (lane[i, 1] > y_max):
                continue
            new_lane.append(lane[i])
        if len(new_lane) > 0:
            new_lane = np.stack(new_lane)
            cropped_lanes.append(new_lane)
    output_map = {'centerline': cropped_lanes, 'boundary': cropped_road_edges}
    with open(os.path.join(saving_dir, 'map.pkl'), 'wb') as f:
        pickle.dump(output_map, f)
    with open(os.path.join(saving_dir, 'tracking_info.pkl'), 'rb') as file:
        data = pickle.load(file)
    all_veh_poses_per_cam = []
    all_cam2veh = []
    all_veh2world = []
    all_intrinsic_matrices = []
    all_distortions = []
    for i in range(args.start_frame, args.start_frame + args.frame_nums):
        frame = data[0, i]
        all_veh_poses_per_cam.append(frame['per_cam_veh_pose'][None, ...])
        all_cam2veh.append(frame['cam2veh'][None, ...])
        all_veh2world.append(np.stack([frame['veh_pose'] for j in range(len(CAMERAS))])[None, ...])
        intrinsic_and_dist = frame['intrinsic']
        intrinsic_matrix = np.stack([np.array([[intrinsic_and_dist[j, 0], 0, intrinsic_and_dist[j, 2]], [0, intrinsic_and_dist[j, 1], intrinsic_and_dist[j, 3]], [0, 0, 1]]) for j in range(len(CAMERAS))])
        all_intrinsic_matrices.append(intrinsic_matrix)
        distortion = np.stack([np.array([intrinsic_and_dist[j, 4], intrinsic_and_dist[j, 5], intrinsic_and_dist[j, 6], intrinsic_and_dist[j, 7]]) for j in range(len(CAMERAS))])
        all_distortions.append(distortion)
    all_veh_poses_per_cam = np.concatenate(all_veh_poses_per_cam, 0)
    all_cam2veh = np.concatenate(all_cam2veh, 0)
    all_veh2world = np.concatenate(all_veh2world, 0)
    all_intrinsic_matrices = np.concatenate(all_intrinsic_matrices)
    all_distortions = np.concatenate(all_distortions)
    extrinsics = []
    all_vehi2veh0 = []
    veh2world_per_cam = all_veh_poses_per_cam[:, 0]
    world2veh_per_cam = np.stack([invert_transformation(v[:3, :3], v[:3, 3]) for v in veh2world_per_cam])
    print(world2veh_per_cam.shape)
    cam2veh = all_cam2veh[:, 0]
    veh2world = all_veh2world[:, 0]
    cam2veh = np.matmul(world2veh_per_cam, np.matmul(veh2world, cam2veh))
    veh2world_per_cam_0 = copy.deepcopy(veh2world_per_cam[0])
    world2veh_per_cam_0 = invert_transformation(veh2world_per_cam_0[:3, :3], veh2world_per_cam_0[:3, 3])
    for cam_i in range(len(CAMERAS)):
        veh2world_per_cam = all_veh_poses_per_cam[:, cam_i]
        world2veh_per_cam = np.stack([invert_transformation(v[:3, :3], v[:3, 3]) for v in veh2world_per_cam])
        cam2veh = all_cam2veh[:, cam_i]
        veh2world = all_veh2world[:, cam_i]
        cam2veh = np.matmul(world2veh_per_cam, np.matmul(veh2world, cam2veh))
        vehi2veh0 = []
        for i in range(1, len(veh2world_per_cam)):
            veh2world_i = veh2world_per_cam[i]
            vehi2veh0.append(world2veh_per_cam_0.dot(veh2world_i))
        vehi2veh0 = np.stack(vehi2veh0)
        pose_0 = np.eye(4)[None, ...]
        vehi2veh0 = np.concatenate((pose_0, vehi2veh0))
        all_vehi2veh0.append(vehi2veh0)
        cam2veh0 = np.matmul(vehi2veh0, cam2veh)
        cam2veh0_FLU = cam2veh0
        trans_mat = np.array([[[0, 0, -1, 0], [-1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]]])
        cam2veh0_RUB = np.matmul(cam2veh0_FLU, trans_mat)
        extrinsics.append(cam2veh0_RUB[:, None, ...])
    all_vehi2veh0 = np.stack(all_vehi2veh0)
    np.save(os.path.join(saving_dir, 'vehi2veh0.npy'), all_vehi2veh0)
    extrinsics = np.concatenate(extrinsics, axis=1)
    extrinsics = extrinsics[:, :, :3, :4].reshape(args.frame_nums * len(CAMERAS), 3, 4)
    all_intrinsic_matrices = all_intrinsic_matrices.reshape(args.frame_nums * len(CAMERAS), 3, 3)
    all_distortions = all_distortions.reshape(args.frame_nums * len(CAMERAS), 4)
    N = extrinsics.shape[0]
    bounds = np.array([0.1, 999]).reshape(1, 2).repeat(N, axis=0)
    cams_meta_data = np.concatenate([extrinsics.reshape(N, -1), all_intrinsic_matrices.reshape(N, -1), all_distortions.reshape(N, -1), bounds.reshape(N, -1)], axis=1)
    np.save(os.path.join(saving_dir, 'cams_meta_waymo.npy'), cams_meta_data)
    print('Getting Shutter Times from tfrecord files')
    save_path = os.path.join(saving_dir, 'shutters')
    get_shutter(args.tfrecord_dir, save_path, start_frame=args.start_frame, end_frame=args.start_frame + args.frame_nums, normalize=True)
    save_path = os.path.join(saving_dir, 'shutters_not_normalize')
    get_shutter(args.tfrecord_dir, save_path, start_frame=args.start_frame, end_frame=args.start_frame + args.frame_nums, normalize=False)
    for save_idx, img_index in enumerate(range(args.start_frame, args.start_frame + args.frame_nums)):
        for key, value in CAMERAS.items():
            img_path_from = os.path.join(saving_dir, 'images_all', '%03d_%s.png' % (img_index, key))
            img_path_to = os.path.join(saving_dir, 'images', '%03d.png' % (save_idx * len(CAMERAS) + value))
            shutil.copyfile(img_path_from, img_path_to)
    valid_vehicles = data[0, args.start_frame]['camera_labels'][1].keys()
    valid_vehicles = [key for key in valid_vehicles if data[0, args.start_frame]['camera_labels'][1][key]['type'] == 1]
    bboxes_dict = {}
    for i, key in enumerate(valid_vehicles):
        bboxes_dict[str(i)] = data[0, args.start_frame]['lidar_labels'][key]
        bboxes_dict[str(i)]['cx'] = bboxes_dict[str(i)].pop('c_x')
        bboxes_dict[str(i)]['cy'] = bboxes_dict[str(i)].pop('c_y')
        bboxes_dict[str(i)]['cz'] = bboxes_dict[str(i)].pop('c_z')
    np.save(os.path.join(saving_dir, '3d_boxes.npy'), bboxes_dict)

def main(args):
    scene_manager = SceneManager(args.input_folder)
    scene_manager.load()
    images = sorted(scene_manager.images.itervalues(), key=image_to_idx)
    if args.method.lower() == 'linear':
        new_images = interpolate_linear(images, args.camera_id, args.format)
    else:
        new_images = interpolate_hermite(images, args.camera_id, args.format)
    map(scene_manager.add_image, new_images)
    scene_manager.save(args.output_folder)

def main(args):
    suffix = '.photometric.bin' if args.photometric else '.geometric.bin'
    image_file = os.path.join(args.dense_folder, 'images', args.image_filename)
    depth_file = os.path.join(args.dense_folder, args.stereo_folder, 'depth_maps', args.image_filename + suffix)
    if args.save_normals:
        normals_file = os.path.join(args.dense_folder, args.stereo_folder, 'normal_maps', args.image_filename + suffix)
    scene_manager = SceneManager(os.path.join(args.dense_folder, 'sparse'))
    scene_manager.load_cameras()
    scene_manager.load_images()
    image_id, image = scene_manager.get_image_from_name(args.image_filename)
    camera = scene_manager.cameras[image.camera_id]
    rotation_camera_from_world = image.R()
    camera_center = image.C()
    image = imageio.imread(image_file)
    with open(depth_file, 'rb') as fid:
        w = int(''.join(iter(lambda: fid.read(1), '&')))
        h = int(''.join(iter(lambda: fid.read(1), '&')))
        c = int(''.join(iter(lambda: fid.read(1), '&')))
        depth_map = np.fromfile(fid, np.float32).reshape(h, w)
        if (h, w) != image.shape[:2]:
            depth_map = zoom(depth_map, (float(image.shape[0]) / h, float(image.shape[1]) / w), order=0)
    if args.save_normals:
        with open(normals_file, 'rb') as fid:
            w = int(''.join(iter(lambda: fid.read(1), '&')))
            h = int(''.join(iter(lambda: fid.read(1), '&')))
            c = int(''.join(iter(lambda: fid.read(1), '&')))
            normals = np.fromfile(fid, np.float32).reshape(c, h, w).transpose([1, 2, 0])
            if (h, w) != image.shape[:2]:
                normals = zoom(normals, (float(image.shape[0]) / h, float(image.shape[1]) / w, 1.0), order=0)
    if args.min_depth is not None:
        depth_map[depth_map < args.min_depth] = 0.0
    if args.max_depth is not None:
        depth_map[depth_map > args.max_depth] = 0.0
    points3D = np.dstack(camera.get_image_grid() + [depth_map])
    points3D[:, :, :2] *= depth_map[:, :, np.newaxis]
    points3D = points3D.astype(np.float32).reshape(-1, 3)
    if args.save_normals:
        normals = normals.astype(np.float32).reshape(-1, 3)
    image = image.reshape(-1, 3)
    if image.dtype != np.uint8:
        if image.max() <= 1:
            image = (image * 255.0).astype(np.uint8)
        else:
            image = image.astype(np.uint8)
    if args.world_space:
        points3D = points3D.dot(rotation_camera_from_world) + camera_center
        if args.save_normals:
            normals = normals.dot(rotation_camera_from_world)
    if args.save_normals:
        vertices = np.rec.fromarrays(tuple(points3D.T) + tuple(normals.T) + tuple(image.T), names='x,y,z,nx,ny,nz,red,green,blue')
    else:
        vertices = np.rec.fromarrays(tuple(points3D.T) + tuple(image.T), names='x,y,z,red,green,blue')
    vertices = PlyElement.describe(vertices, 'vertex')
    PlyData([vertices]).write(args.output_filename)

def main(args):
    scene_manager = SceneManager(args.input_folder)
    scene_manager.load_cameras()
    scene_manager.load_images()
    if args.sort:
        images = sorted(scene_manager.images.itervalues(), key=lambda im: im.name)
    else:
        images = scene_manager.images.values()
    fid = open(args.output_file, 'w')
    fid_filenames = open(args.output_file + '.list.txt', 'w')
    (print >> fid, '# Bundle file v0.3')
    (print >> fid, len(images), 0)
    for image in images:
        (print >> fid_filenames, image.name)
        camera = scene_manager.cameras[image.camera_id]
        (print >> fid, 0.5 * (camera.fx + camera.fy), 0, 0)
        R, t = (image.R(), image.t)
        (print >> fid, R[0, 0], R[0, 1], R[0, 2])
        (print >> fid, -R[1, 0], -R[1, 1], -R[1, 2])
        (print >> fid, -R[2, 0], -R[2, 1], -R[2, 2])
        (print >> fid, t[0], -t[1], -t[2])
    fid.close()
    fid_filenames.close()

def main(args):
    scene_manager = SceneManager(args.input_folder)
    scene_manager.load()
    with open(args.output_file, 'w') as fid:
        fid.write('NVM_V3\n \n{:d}\n'.format(len(scene_manager.images)))
        image_fmt_str = ' {:.3f} ' + 7 * '{:.7f} '
        for image_id, image in scene_manager.images.iteritems():
            camera = scene_manager.cameras[image.camera_id]
            f = 0.5 * (camera.fx + camera.fy)
            fid.write(args.image_name_prefix + image.name)
            fid.write(image_fmt_str.format(*(f,) + tuple(image.q.q) + tuple(image.C())))
            if camera.distortion_func is None:
                fid.write('0 0\n')
            else:
                fid.write('{:.7f} 0\n'.format(-camera.k1))
        image_id_to_idx = dict(((image_id, i) for i, image_id in enumerate(scene_manager.images)))
        fid.write('{:d}\n'.format(len(scene_manager.points3D)))
        for i, point3D_id in enumerate(scene_manager.point3D_ids):
            fid.write('{:.7f} {:.7f} {:.7f} '.format(*scene_manager.points3D[i]))
            fid.write('{:d} {:d} {:d} '.format(*scene_manager.point3D_colors[i]))
            keypoints = [(image_id_to_idx[image_id], kp_idx) + tuple(scene_manager.images[image_id].points2D[kp_idx]) for image_id, kp_idx in scene_manager.point3D_id_to_images[point3D_id]]
            fid.write('{:d}'.format(len(keypoints)))
            fid.write((len(keypoints) * ' {:d} {:d} {:.3f} {:.3f}' + '\n').format(*itertools.chain(*keypoints)))

def save_camera_ply(ply_file, images, scale):
    points3D = scale * np.array(((0.0, 0.0, 0.0), (-1.0, -1.0, 1.0), (-1.0, 1.0, 1.0), (1.0, -1.0, 1.0), (1.0, 1.0, 1.0)))
    faces = np.array(((0, 2, 1), (0, 4, 2), (0, 3, 4), (0, 1, 3), (1, 2, 4), (1, 4, 3)))
    r = np.linspace(0, 255, len(images), dtype=np.uint8)
    g = 255 - r
    b = r - np.linspace(0, 128, len(images), dtype=np.uint8)
    color = np.column_stack((r, g, b))
    with open(ply_file, 'w') as fid:
        (print >> fid, 'ply')
        (print >> fid, 'format ascii 1.0')
        (print >> fid, 'element vertex', len(points3D) * len(images))
        (print >> fid, 'property float x')
        (print >> fid, 'property float y')
        (print >> fid, 'property float z')
        (print >> fid, 'property uchar red')
        (print >> fid, 'property uchar green')
        (print >> fid, 'property uchar blue')
        (print >> fid, 'element face', len(faces) * len(images))
        (print >> fid, 'property list uchar int vertex_index')
        (print >> fid, 'end_header')
        for image, c in zip(images, color):
            for p3D in points3D.dot(image.R()) + image.C():
                (print >> fid, p3D[0], p3D[1], p3D[2], c[0], c[1], c[2])
        for i in xrange(len(images)):
            for f in faces + len(points3D) * i:
                (print >> fid, '3 {} {} {}'.format(*f))

def main(args):
    scene_manager = SceneManager(args.input_folder)
    scene_manager.load_images()
    images = sorted(scene_manager.images.itervalues(), key=lambda image: image.name)
    save_camera_ply(args.output_file, images, args.scale)

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

def load(self):
    self.load_cameras()
    self.load_images()
    self.load_points3D()

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

def __str__(self):
    return str(self.q)

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

def clean_cache(self):
    folder_path = self.cache_dir
    shutil.rmtree(folder_path)

@click.command()
@click.option('--data_dir', type=str)
def hello(data_dir):
    poses = np.load(pjoin(data_dir, 'cams_meta.npy')).reshape(-1, 27)[:, :12].reshape(-1, 3, 4)
    np.save(pjoin(data_dir, 'poses_render.npy'), poses)
    last_row = np.zeros((poses.shape[0], 1, 4))
    last_row[:, :, -1] = 1
    poses = np.concatenate((poses, last_row), axis=1)
    extrinsic_opencv = np.concatenate((poses[:, :, 0:1], -poses[:, :, 1:2], -poses[:, :, 2:3], poses[:, :, 3:]), axis=2)
    np.save(pjoin(data_dir, 'extrinsics.npy'), extrinsic_opencv)

def frame2video(im_dir, video_dir, fps):
    im_list = os.listdir(im_dir)
    im_list = sorted([os.path.join(im_dir, img) for img in os.listdir(im_dir) if img.endswith(('.png', '.jpg', '.jpeg'))])
    img = Image.open(os.path.join(im_dir, im_list[0]))
    img_size = img.size
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    videoWriter = cv2.VideoWriter(video_dir, fourcc, fps, img_size)
    for i in im_list:
        im_name = os.path.join(im_dir, i)
        frame = cv2.imdecode(np.fromfile(im_name, dtype=np.uint8), -1)
        videoWriter.write(frame)
    videoWriter.release()
    print('Done')

@click.command()
@click.option('--data_dir', type=str, default='.')
def main(data_dir):
    n_cams = 10
    poses = np.zeros([n_cams, 3, 4])
    poses[:, :3, :3] = np.eye(3)
    poses[:, :3, 3] = np.array([0.0, 0.0, 0.0])
    intri = np.zeros([n_cams, 3, 3])
    intri[:, 0, 0] = 256.0
    intri[:, 1, 1] = 256.0
    intri[:, 0, 2] = 256.0
    intri[:, 1, 2] = 256.0
    intri[:, 2, 2] = 1.0
    distortion_params = np.zeros([n_cams, 4])
    bounds = np.zeros([n_cams, 2])
    bounds[:, 0] = 1.0
    bounds[:, 1] = 100.0
    data = np.concatenate([poses.reshape(n_cams, 12), intri.reshape(n_cams, 9), distortion_params.reshape(n_cams, 4), bounds.reshape(n_cams, 2)], -1)
    print(data.shape)
    data = np.ascontiguousarray(np.array(data).astype(np.float64))
    np.save(pjoin(data_dir, 'cams_meta.npy'), data)

@click.command()
@click.option('--data_dir', type=str)
@click.option('--key_poses', type=str)
@click.option('--n_out_poses', type=int, default=240)
def hello(data_dir, n_out_poses, key_poses):
    poses = np.load(pjoin(data_dir, 'cams_meta.npy')).reshape(-1, 27)[:, :12].reshape(-1, 3, 4)
    n_poses = len(poses)
    if key_poses == 'all':
        key_poses = poses.copy()
    else:
        key_poses = np.array([int(_) for _ in key_poses.split(',')])
        key_poses = poses[key_poses]
    out_poses = inter_poses(key_poses, n_out_poses)
    out_poses = np.ascontiguousarray(out_poses.astype(np.float64))
    np.save(pjoin(data_dir, 'poses_render.npy'), out_poses)

def make_image_list(data_path, factor):
    image_list = []
    suffix = ['*.jpg', '*.png', '*.JPG', '*.jpeg']
    if 0.999 < factor < 1.001:
        for suf in suffix:
            image_list += glob(os.path.join(data_path, 'images', suf)) + glob(os.path.join(data_path, 'images_1', suf))
    else:
        f_int = int(np.round(factor))
        for suf in suffix:
            image_list += glob(os.path.join(data_path, 'images_{}'.format(f_int), suf))
    assert len(image_list) > 0, 'No image found'
    image_list.sort()
    f = open(os.path.join(data_path, 'image_list.txt'), 'w')
    for image_path in image_list:
        f.write(image_path + '\n')
    f = open(os.path.join(data_path, 'shutter_list.txt'), 'w')
    for image_path in image_list:
        f.write(image_path[:-14] + 'shutters' + image_path[-8:-4] + '.txt' + '\n')

@hydra.main(version_base=None, config_path='../confs', config_name='default')
def main(conf: DictConfig) -> None:
    if 'work_dir' in conf:
        base_dir = conf['work_dir']
    else:
        base_dir = os.getcwd()
    print('Working directory is {}'.format(base_dir))
    data_path = os.path.join(base_dir, 'data', conf['dataset_name'], conf['case_name'])
    base_exp_dir = os.path.join(base_dir, 'exp', conf['case_name'], conf['exp_name'])
    os.makedirs(base_exp_dir, exist_ok=True)
    file_backup_dir = os.path.join(base_exp_dir, 'record/')
    os.makedirs(file_backup_dir, exist_ok=True)
    for file_pattern in backup_file_patterns:
        file_list = glob(os.path.join(base_dir, file_pattern))
        for file_name in file_list:
            new_file_name = file_name.replace(base_dir, file_backup_dir)
            os.makedirs(os.path.dirname(new_file_name), exist_ok=True)
            copyfile(file_name, new_file_name)
    make_image_list(data_path, conf['dataset']['factor'])
    conf = OmegaConf.to_container(conf, resolve=True)
    conf['dataset']['data_path'] = data_path
    conf['base_dir'] = base_dir
    conf['base_exp_dir'] = base_exp_dir
    print(data_path)
    OmegaConf.save(conf, os.path.join(file_backup_dir, 'runtime_config.yaml'))
    OmegaConf.save(conf, './runtime_config.yaml')
    for build_dir in ['build', 'cmake-build-release']:
        if os.path.exists('{}/{}/main'.format(base_dir, build_dir)):
            os.system('{}/{}/main'.format(base_dir, build_dir))
            return
    assert False, 'Can not find executable file'

@click.command()
@click.option('--data_dir', type=str)
@click.option('--suffix', type=str, default='*.png')
@click.option('--fps', type=int, default=20)
def hello(data_dir, suffix, fps):
    input_dir = '/dssg/home/acct-umjpyb/umjpyb/ziwang/edition_system/outputs/1137_demo2_120frames_2023_11_22_13_52_57/__init__/'
    image_list = []
    for i in range(100):
        image_list.append(input_dir + str(i) + '.png')
    imgs = []
    for img_path in image_list:
        imgs.append(cv.imread(img_path)[:, :])
    last = imgs[-1]
    for i in range(30):
        imgs.append(last)
    height, width, layers = imgs[-1].shape
    size = (width, height)
    writer = imageio.get_writer(pjoin(data_dir, 'output.mp4'), fps=fps)
    for i, frame in enumerate(imgs):
        writer.append_data(np.array(frame[:, :, ::-1]))
    writer.close()

@click.command()
@click.option('--data_dir', type=str)
def hello(data_dir):
    poses_bounds = np.load(pjoin(data_dir, 'poses_bounds.npy')).reshape(-1, 17)
    poses_hwf = poses_bounds[:, :15].reshape(-1, 3, 5)
    poses = poses_hwf[:, :3, :4]
    hwf = poses_hwf[:, :3, 4]
    poses = np.concatenate([poses[:, :, 1:2], -poses[:, :, 0:1], poses[:, :, 2:]], 2)
    bounds = poses_bounds[:, 15:17]
    n_poses = len(poses)
    intri = np.zeros([n_poses, 3, 3])
    intri[:, :3, :3] = np.eye(3)
    intri[:, 0, 0] = hwf[:, 2]
    intri[:, 1, 1] = hwf[:, 2]
    intri[:, 0, 2] = hwf[:, 1] * 0.5
    intri[:, 1, 2] = hwf[:, 0] * 0.5
    data = np.concatenate([poses.reshape(n_poses, -1), intri.reshape(n_poses, -1), np.zeros([n_poses, 4]), bounds.reshape(n_poses, -1)], -1)
    data = np.ascontiguousarray(np.array(data).astype(np.float64))
    np.save(pjoin(data_dir, 'cams_meta.npy'), data)

class NeRFSceneManager(SceneManager):
    """COLMAP pose loader.

    Minor NeRF-specific extension to the third_party Python COLMAP loader:
    google3/third_party/py/pycolmap/scene_manager.py
    """

    def __init__(self, data_dir):
        if os.path.exists(pjoin(data_dir, 'sparse', '0')):
            sfm_dir = pjoin(data_dir, 'sparse', '0')
        else:
            sfm_dir = pjoin(data_dir, 'hloc_sfm')
        assert os.path.exists(sfm_dir)
        super(NeRFSceneManager, self).__init__(sfm_dir)

    def process(self) -> Tuple[Sequence[Text], np.ndarray, np.ndarray, Optional[Mapping[Text, float]], camera_utils.ProjectionType]:
        """Applies NeRF-specific postprocessing to the loaded pose data.

        Returns:
          a tuple [image_names, poses, pixtocam, distortion_params].
          image_names:  contains the only the basename of the images.
          poses: [N, 4, 4] array containing the camera to world matrices.
          pixtocam: [N, 3, 3] array containing the camera to pixel space matrices.
          distortion_params: mapping of distortion param name to distortion
            parameters. Cameras share intrinsics. Valid keys are k1, k2, p1 and p2.
        """
        self.load_cameras()
        self.load_images()
        self.load_points3D()
        cam = self.cameras[1]
        fx, fy, cx, cy = (cam.fx, cam.fy, cam.cx, cam.cy)
        pixtocam = np.linalg.inv(camera_utils.intrinsic_matrix(fx, fy, cx, cy))
        imdata = self.images
        w2c_mats = []
        bottom = np.array([0, 0, 0, 1]).reshape(1, 4)
        for k in imdata:
            im = imdata[k]
            rot = im.R()
            trans = im.tvec.reshape(3, 1)
            w2c = np.concatenate([np.concatenate([rot, trans], 1), bottom], axis=0)
            w2c_mats.append(w2c)
        w2c_mats = np.stack(w2c_mats, axis=0)
        c2w_mats = np.linalg.inv(w2c_mats)
        poses = c2w_mats[:, :3, :4]
        names = [imdata[k].name for k in imdata]
        poses = poses @ np.diag([1, -1, -1, 1])
        type_ = cam.camera_type
        if type_ == 0 or type_ == 'SIMPLE_PINHOLE':
            params = None
            camtype = camera_utils.ProjectionType.PERSPECTIVE
        elif type_ == 1 or type_ == 'PINHOLE':
            params = None
            camtype = camera_utils.ProjectionType.PERSPECTIVE
        if type_ == 2 or type_ == 'SIMPLE_RADIAL':
            params = {k: 0.0 for k in ['k1', 'k2', 'k3', 'p1', 'p2']}
            params['k1'] = cam.k1
            camtype = camera_utils.ProjectionType.PERSPECTIVE
        elif type_ == 3 or type_ == 'RADIAL':
            params = {k: 0.0 for k in ['k1', 'k2', 'k3', 'p1', 'p2']}
            params['k1'] = cam.k1
            params['k2'] = cam.k2
            camtype = camera_utils.ProjectionType.PERSPECTIVE
        elif type_ == 4 or type_ == 'OPENCV':
            params = {k: 0.0 for k in ['k1', 'k2', 'k3', 'p1', 'p2']}
            params['k1'] = cam.k1
            params['k2'] = cam.k2
            params['p1'] = cam.p1
            params['p2'] = cam.p2
            camtype = camera_utils.ProjectionType.PERSPECTIVE
        elif type_ == 5 or type_ == 'OPENCV_FISHEYE':
            params = {k: 0.0 for k in ['k1', 'k2', 'k3', 'k4']}
            params['k1'] = cam.k1
            params['k2'] = cam.k2
            params['k3'] = cam.k3
            params['k4'] = cam.k4
            camtype = camera_utils.ProjectionType.FISHEYE
        return (names, poses, pixtocam, params, camtype)

def __init__(self, data_dir):
    if os.path.exists(pjoin(data_dir, 'sparse', '0')):
        sfm_dir = pjoin(data_dir, 'sparse', '0')
    else:
        sfm_dir = pjoin(data_dir, 'hloc_sfm')
    assert os.path.exists(sfm_dir)
    super(NeRFSceneManager, self).__init__(sfm_dir)

def process(self) -> Tuple[Sequence[Text], np.ndarray, np.ndarray, Optional[Mapping[Text, float]], camera_utils.ProjectionType]:
    """Applies NeRF-specific postprocessing to the loaded pose data.

        Returns:
          a tuple [image_names, poses, pixtocam, distortion_params].
          image_names:  contains the only the basename of the images.
          poses: [N, 4, 4] array containing the camera to world matrices.
          pixtocam: [N, 3, 3] array containing the camera to pixel space matrices.
          distortion_params: mapping of distortion param name to distortion
            parameters. Cameras share intrinsics. Valid keys are k1, k2, p1 and p2.
        """
    self.load_cameras()
    self.load_images()
    self.load_points3D()
    cam = self.cameras[1]
    fx, fy, cx, cy = (cam.fx, cam.fy, cam.cx, cam.cy)
    pixtocam = np.linalg.inv(camera_utils.intrinsic_matrix(fx, fy, cx, cy))
    imdata = self.images
    w2c_mats = []
    bottom = np.array([0, 0, 0, 1]).reshape(1, 4)
    for k in imdata:
        im = imdata[k]
        rot = im.R()
        trans = im.tvec.reshape(3, 1)
        w2c = np.concatenate([np.concatenate([rot, trans], 1), bottom], axis=0)
        w2c_mats.append(w2c)
    w2c_mats = np.stack(w2c_mats, axis=0)
    c2w_mats = np.linalg.inv(w2c_mats)
    poses = c2w_mats[:, :3, :4]
    names = [imdata[k].name for k in imdata]
    poses = poses @ np.diag([1, -1, -1, 1])
    type_ = cam.camera_type
    if type_ == 0 or type_ == 'SIMPLE_PINHOLE':
        params = None
        camtype = camera_utils.ProjectionType.PERSPECTIVE
    elif type_ == 1 or type_ == 'PINHOLE':
        params = None
        camtype = camera_utils.ProjectionType.PERSPECTIVE
    if type_ == 2 or type_ == 'SIMPLE_RADIAL':
        params = {k: 0.0 for k in ['k1', 'k2', 'k3', 'p1', 'p2']}
        params['k1'] = cam.k1
        camtype = camera_utils.ProjectionType.PERSPECTIVE
    elif type_ == 3 or type_ == 'RADIAL':
        params = {k: 0.0 for k in ['k1', 'k2', 'k3', 'p1', 'p2']}
        params['k1'] = cam.k1
        params['k2'] = cam.k2
        camtype = camera_utils.ProjectionType.PERSPECTIVE
    elif type_ == 4 or type_ == 'OPENCV':
        params = {k: 0.0 for k in ['k1', 'k2', 'k3', 'p1', 'p2']}
        params['k1'] = cam.k1
        params['k2'] = cam.k2
        params['p1'] = cam.p1
        params['p2'] = cam.p2
        camtype = camera_utils.ProjectionType.PERSPECTIVE
    elif type_ == 5 or type_ == 'OPENCV_FISHEYE':
        params = {k: 0.0 for k in ['k1', 'k2', 'k3', 'k4']}
        params['k1'] = cam.k1
        params['k2'] = cam.k2
        params['k3'] = cam.k3
        params['k4'] = cam.k4
        camtype = camera_utils.ProjectionType.FISHEYE
    return (names, poses, pixtocam, params, camtype)

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

@click.command()
@click.option('--data_dir', type=str)
@click.option('--out_mode', type=str, default='cams_meta')
def main(data_dir, out_mode):
    dataset = Dataset(data_dir)
    dataset.export(data_dir, out_mode)

def glob_images(image_dir):
    ret = []
    for suff in ['*.jpg', '*.JPG', '*.png', '*.PNG']:
        ret += glob(pjoin(image_dir, suff))
    return sorted(ret)

@click.command()
@click.option('--base_dir', type=str, default='/dssg/home/acct-umjpyb/umjpyb/ziwang/f2-nerf/')
@click.option('--scene_name', type=str, default='segment-12879640240483815315_5852_605_5872_605_with_camera_labels')
@click.option('--exp_name', type=str, default='exp_1108_0.15')
def main(base_dir, scene_name, exp_name):
    print('scene_name', scene_name)
    print('exp_name', exp_name)
    loss_fn_vgg = LPIPS(network='vgg').to(torch.device('cuda'))
    base_data_dir = os.path.join(base_dir, 'data/waymo_multi_view')
    gt_image_dir = os.path.join(base_data_dir, scene_name, 'images')
    pred_image_dir = os.path.join(base_dir, 'exp', scene_name, exp_name, 'test_images')
    gt_image_list = os.listdir(gt_image_dir)
    gt_image_list.sort(key=lambda x: int(x[:-4]))
    gt_image_list = gt_image_list[::8]
    psnr_tot, ssim_tot, lpips_tot = (0.0, 0.0, 0.0)
    info_data = {'psnr': dict(), 'ssim': dict(), 'lpips': dict()}
    for i, gt_image_path in tqdm(enumerate(gt_image_list)):
        gt_path = os.path.join(gt_image_dir, gt_image_path)
        pred_path = os.path.join(pred_image_dir, 'color_50000_' + gt_image_path)
        gt_image = imageio.imread(gt_path)[:, :, :3]
        pd_image = imageio.imread(pred_path)[:, :, :3]
        psnr = peak_signal_noise_ratio(gt_image, pd_image)
        ssim = rgb_ssim(gt_image / 255.0, pd_image / 255.0, max_val=1)
        lpip = loss_fn_vgg(to_torch_image(pd_image), to_torch_image(gt_image)).cpu().item()
        psnr_tot += psnr
        ssim_tot += ssim
        lpips_tot += lpip
        info_data['psnr'][str(i)] = psnr
        info_data['ssim'][str(i)] = ssim
        info_data['lpips'][str(i)] = lpip
    n_images = len(gt_image_list)
    info_data['psnr']['mean'] = psnr_tot / n_images
    info_data['ssim']['mean'] = ssim_tot / n_images
    info_data['lpips']['mean'] = lpips_tot / n_images
    print('psnr:', info_data['psnr']['mean'])
    print('ssim', info_data['ssim']['mean'])
    print('lpips', info_data['lpips']['mean'])
    with open(pjoin(base_dir, 'exp', scene_name, exp_name, 'info.json'), 'w') as f:
        json.dump(info_data, f, indent=2)

def glob_images(image_dir):
    ret = []
    for suff in ['*.jpg', '*.JPG', '*.png', '*.PNG']:
        ret += glob(pjoin(image_dir, suff))
    return sorted(ret)

@click.command()
@click.option('--base_data_dir', type=str, default='/home/ppwang/Projects/SANR/exp/evals')
@click.option('--scenes', type=str)
@click.option('--methods', type=str)
def main(base_data_dir, scenes, methods):
    loss_fn_vgg = lpips.LPIPS(net='vgg').to(torch.device('cuda'))
    scenes = scenes.split(',')
    methods = methods.split(',')
    for scene in scenes:
        scene_dir = pjoin(base_data_dir, scene)
        gt_image_paths = glob_images(pjoin(scene_dir, 'gt'))
        for method in methods:
            pd_image_paths = glob_images(pjoin(scene_dir, method))
            psnr_tot, ssim_tot, lpips_tot = (0.0, 0.0, 0.0)
            info_data = {'psnr': dict(), 'ssim': dict(), 'lpips': dict()}
            assert len(gt_image_paths) == len(pd_image_paths)
            for i, (gt_path, pd_path) in tqdm(enumerate(zip(gt_image_paths, pd_image_paths))):
                gt_image = imageio.imread(gt_path)[:, :, :3]
                pd_image = imageio.imread(pd_path)[:, :, :3]
                psnr = peak_signal_noise_ratio(gt_image, pd_image)
                ssim = rgb_ssim(gt_image / 255.0, pd_image / 255.0, max_val=1)
                lpip = loss_fn_vgg(to_torch_image(gt_image), to_torch_image(pd_image)).cpu().item()
                psnr_tot += psnr
                ssim_tot += ssim
                lpips_tot += lpip
                info_data['psnr'][str(i)] = psnr
                info_data['ssim'][str(i)] = ssim
                info_data['lpips'][str(i)] = lpip
            n_images = len(gt_image_paths)
            info_data['psnr']['mean'] = psnr_tot / n_images
            info_data['ssim']['mean'] = ssim_tot / n_images
            info_data['lpips']['mean'] = lpips_tot / n_images
            with open(pjoin(scene_dir, method, 'info.json'), 'w') as f:
                json.dump(info_data, f, indent=2)

@click.command()
@click.option('--data_dir', type=str)
@click.option('--match_type', type=str, default='exhaustive')
def hello(data_dir, match_type):
    images = Path(data_dir) / 'images/'
    outputs = Path(data_dir)
    sfm_pairs = outputs / 'pairs-sfm.txt'
    loc_pairs = outputs / 'pairs-loc.txt'
    sfm_dir = outputs / 'hloc_sfm'
    features = outputs / 'features.h5'
    matches = outputs / 'matches.h5'
    feature_conf = extract_features.confs['superpoint_aachen']
    matcher_conf = match_features.confs['superglue']
    assert match_type in ['exhaustive', 'local']
    if match_type == 'exhaustive':
        references = [p.relative_to(images).as_posix() for p in images.iterdir()]
        print(len(references), 'mapping images')
        extract_features.main(feature_conf, images, image_list=references, feature_path=features)
        pairs_from_exhaustive.main(sfm_pairs, image_list=references)
        match_features.main(matcher_conf, sfm_pairs, features=features, matches=matches)
        reconstruction.main(sfm_dir, images, sfm_pairs, features, matches, image_list=references, image_options={'camera_model': 'OPENCV'})
    else:
        retrieval_conf = extract_features.confs['netvlad']
        retrieval_path = extract_features.main(retrieval_conf, images, outputs)
        pairs_from_retrieval.main(retrieval_path, sfm_pairs, num_matched=20)
        feature_path = extract_features.main(feature_conf, images, outputs)
        match_path = match_features.main(matcher_conf, sfm_pairs, feature_conf['output'], outputs)
        reconstruction.main(sfm_dir, images, sfm_pairs, feature_path, match_path, image_options={'camera_model': 'OPENCV'})

def main(args):
    scene_manager = SceneManager(args.input_folder)
    scene_manager.load()
    images = sorted(scene_manager.images.itervalues(), key=image_to_idx)
    if args.method.lower() == 'linear':
        new_images = interpolate_linear(images, args.camera_id, args.format)
    else:
        new_images = interpolate_hermite(images, args.camera_id, args.format)
    map(scene_manager.add_image, new_images)
    scene_manager.save(args.output_folder)

def main(args):
    suffix = '.photometric.bin' if args.photometric else '.geometric.bin'
    image_file = os.path.join(args.dense_folder, 'images', args.image_filename)
    depth_file = os.path.join(args.dense_folder, args.stereo_folder, 'depth_maps', args.image_filename + suffix)
    if args.save_normals:
        normals_file = os.path.join(args.dense_folder, args.stereo_folder, 'normal_maps', args.image_filename + suffix)
    scene_manager = SceneManager(os.path.join(args.dense_folder, 'sparse'))
    scene_manager.load_cameras()
    scene_manager.load_images()
    image_id, image = scene_manager.get_image_from_name(args.image_filename)
    camera = scene_manager.cameras[image.camera_id]
    rotation_camera_from_world = image.R()
    camera_center = image.C()
    image = imageio.imread(image_file)
    with open(depth_file, 'rb') as fid:
        w = int(''.join(iter(lambda: fid.read(1), '&')))
        h = int(''.join(iter(lambda: fid.read(1), '&')))
        c = int(''.join(iter(lambda: fid.read(1), '&')))
        depth_map = np.fromfile(fid, np.float32).reshape(h, w)
        if (h, w) != image.shape[:2]:
            depth_map = zoom(depth_map, (float(image.shape[0]) / h, float(image.shape[1]) / w), order=0)
    if args.save_normals:
        with open(normals_file, 'rb') as fid:
            w = int(''.join(iter(lambda: fid.read(1), '&')))
            h = int(''.join(iter(lambda: fid.read(1), '&')))
            c = int(''.join(iter(lambda: fid.read(1), '&')))
            normals = np.fromfile(fid, np.float32).reshape(c, h, w).transpose([1, 2, 0])
            if (h, w) != image.shape[:2]:
                normals = zoom(normals, (float(image.shape[0]) / h, float(image.shape[1]) / w, 1.0), order=0)
    if args.min_depth is not None:
        depth_map[depth_map < args.min_depth] = 0.0
    if args.max_depth is not None:
        depth_map[depth_map > args.max_depth] = 0.0
    points3D = np.dstack(camera.get_image_grid() + [depth_map])
    points3D[:, :, :2] *= depth_map[:, :, np.newaxis]
    points3D = points3D.astype(np.float32).reshape(-1, 3)
    if args.save_normals:
        normals = normals.astype(np.float32).reshape(-1, 3)
    image = image.reshape(-1, 3)
    if image.dtype != np.uint8:
        if image.max() <= 1:
            image = (image * 255.0).astype(np.uint8)
        else:
            image = image.astype(np.uint8)
    if args.world_space:
        points3D = points3D.dot(rotation_camera_from_world) + camera_center
        if args.save_normals:
            normals = normals.dot(rotation_camera_from_world)
    if args.save_normals:
        vertices = np.rec.fromarrays(tuple(points3D.T) + tuple(normals.T) + tuple(image.T), names='x,y,z,nx,ny,nz,red,green,blue')
    else:
        vertices = np.rec.fromarrays(tuple(points3D.T) + tuple(image.T), names='x,y,z,red,green,blue')
    vertices = PlyElement.describe(vertices, 'vertex')
    PlyData([vertices]).write(args.output_filename)

def main(args):
    scene_manager = SceneManager(args.input_folder)
    scene_manager.load_cameras()
    scene_manager.load_images()
    if args.sort:
        images = sorted(scene_manager.images.itervalues(), key=lambda im: im.name)
    else:
        images = scene_manager.images.values()
    fid = open(args.output_file, 'w')
    fid_filenames = open(args.output_file + '.list.txt', 'w')
    (print >> fid, '# Bundle file v0.3')
    (print >> fid, len(images), 0)
    for image in images:
        (print >> fid_filenames, image.name)
        camera = scene_manager.cameras[image.camera_id]
        (print >> fid, 0.5 * (camera.fx + camera.fy), 0, 0)
        R, t = (image.R(), image.t)
        (print >> fid, R[0, 0], R[0, 1], R[0, 2])
        (print >> fid, -R[1, 0], -R[1, 1], -R[1, 2])
        (print >> fid, -R[2, 0], -R[2, 1], -R[2, 2])
        (print >> fid, t[0], -t[1], -t[2])
    fid.close()
    fid_filenames.close()

def main(args):
    scene_manager = SceneManager(args.input_folder)
    scene_manager.load()
    with open(args.output_file, 'w') as fid:
        fid.write('NVM_V3\n \n{:d}\n'.format(len(scene_manager.images)))
        image_fmt_str = ' {:.3f} ' + 7 * '{:.7f} '
        for image_id, image in scene_manager.images.iteritems():
            camera = scene_manager.cameras[image.camera_id]
            f = 0.5 * (camera.fx + camera.fy)
            fid.write(args.image_name_prefix + image.name)
            fid.write(image_fmt_str.format(*(f,) + tuple(image.q.q) + tuple(image.C())))
            if camera.distortion_func is None:
                fid.write('0 0\n')
            else:
                fid.write('{:.7f} 0\n'.format(-camera.k1))
        image_id_to_idx = dict(((image_id, i) for i, image_id in enumerate(scene_manager.images)))
        fid.write('{:d}\n'.format(len(scene_manager.points3D)))
        for i, point3D_id in enumerate(scene_manager.point3D_ids):
            fid.write('{:.7f} {:.7f} {:.7f} '.format(*scene_manager.points3D[i]))
            fid.write('{:d} {:d} {:d} '.format(*scene_manager.point3D_colors[i]))
            keypoints = [(image_id_to_idx[image_id], kp_idx) + tuple(scene_manager.images[image_id].points2D[kp_idx]) for image_id, kp_idx in scene_manager.point3D_id_to_images[point3D_id]]
            fid.write('{:d}'.format(len(keypoints)))
            fid.write((len(keypoints) * ' {:d} {:d} {:.3f} {:.3f}' + '\n').format(*itertools.chain(*keypoints)))

def save_camera_ply(ply_file, images, scale):
    points3D = scale * np.array(((0.0, 0.0, 0.0), (-1.0, -1.0, 1.0), (-1.0, 1.0, 1.0), (1.0, -1.0, 1.0), (1.0, 1.0, 1.0)))
    faces = np.array(((0, 2, 1), (0, 4, 2), (0, 3, 4), (0, 1, 3), (1, 2, 4), (1, 4, 3)))
    r = np.linspace(0, 255, len(images), dtype=np.uint8)
    g = 255 - r
    b = r - np.linspace(0, 128, len(images), dtype=np.uint8)
    color = np.column_stack((r, g, b))
    with open(ply_file, 'w') as fid:
        (print >> fid, 'ply')
        (print >> fid, 'format ascii 1.0')
        (print >> fid, 'element vertex', len(points3D) * len(images))
        (print >> fid, 'property float x')
        (print >> fid, 'property float y')
        (print >> fid, 'property float z')
        (print >> fid, 'property uchar red')
        (print >> fid, 'property uchar green')
        (print >> fid, 'property uchar blue')
        (print >> fid, 'element face', len(faces) * len(images))
        (print >> fid, 'property list uchar int vertex_index')
        (print >> fid, 'end_header')
        for image, c in zip(images, color):
            for p3D in points3D.dot(image.R()) + image.C():
                (print >> fid, p3D[0], p3D[1], p3D[2], c[0], c[1], c[2])
        for i in xrange(len(images)):
            for f in faces + len(points3D) * i:
                (print >> fid, '3 {} {} {}'.format(*f))

def main(args):
    scene_manager = SceneManager(args.input_folder)
    scene_manager.load_images()
    images = sorted(scene_manager.images.itervalues(), key=lambda image: image.name)
    save_camera_ply(args.output_file, images, args.scale)

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

def load(self):
    self.load_cameras()
    self.load_images()
    self.load_points3D()

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

def __str__(self):
    return str(self.q)

def minify_v0(basedir, factors=[], resolutions=[]):
    needtoload = False
    for r in factors:
        imgdir = os.path.join(basedir, 'images_{}'.format(r))
        if not os.path.exists(imgdir):
            needtoload = True
    for r in resolutions:
        imgdir = os.path.join(basedir, 'images_{}x{}'.format(r[1], r[0]))
        if not os.path.exists(imgdir):
            needtoload = True
    if not needtoload:
        return

    def downsample(imgs, f):
        sh = list(imgs.shape)
        sh = sh[:-3] + [sh[-3] // f, f, sh[-2] // f, f, sh[-1]]
        imgs = np.reshape(imgs, sh)
        imgs = np.mean(imgs, (-2, -4))
        return imgs
    imgdir = os.path.join(basedir, 'images')
    imgs = [os.path.join(imgdir, f) for f in sorted(os.listdir(imgdir))]
    imgs = [f for f in imgs if any([f.endswith(ex) for ex in ['JPG', 'jpg', 'png', 'jpeg', 'PNG']])]
    imgs = np.stack([imageio.imread(img) / 255.0 for img in imgs], 0)
    for r in factors + resolutions:
        if isinstance(r, int):
            name = 'images_{}'.format(r)
        else:
            name = 'images_{}x{}'.format(r[1], r[0])
        imgdir = os.path.join(basedir, name)
        if os.path.exists(imgdir):
            continue
        print('Minifying', r, basedir)
        if isinstance(r, int):
            imgs_down = downsample(imgs, r)
        else:
            imgs_down = skimage.transform.resize(imgs, [imgs.shape[0], r[0], r[1], imgs.shape[-1]], order=1, mode='constant', cval=0, clip=True, preserve_range=False, anti_aliasing=True, anti_aliasing_sigma=None)
        os.makedirs(imgdir)
        for i in range(imgs_down.shape[0]):
            imageio.imwrite(os.path.join(imgdir, 'image{:03d}.png'.format(i)), (255 * imgs_down[i]).astype(np.uint8))

def downsample(imgs, f):
    sh = list(imgs.shape)
    sh = sh[:-3] + [sh[-3] // f, f, sh[-2] // f, f, sh[-1]]
    imgs = np.reshape(imgs, sh)
    imgs = np.mean(imgs, (-2, -4))
    return imgs

def minify(basedir, factors=[], resolutions=[]):
    needtoload = False
    for r in factors:
        imgdir = os.path.join(basedir, 'images_{}'.format(r))
        if not os.path.exists(imgdir):
            needtoload = True
    for r in resolutions:
        imgdir = os.path.join(basedir, 'images_{}x{}'.format(r[1], r[0]))
        if not os.path.exists(imgdir):
            needtoload = True
    if not needtoload:
        return
    from shutil import copy
    from subprocess import check_output
    imgdir = os.path.join(basedir, 'images')
    imgs = [os.path.join(imgdir, f) for f in sorted(os.listdir(imgdir))]
    imgs = [f for f in imgs if any([f.endswith(ex) for ex in ['JPG', 'jpg', 'png', 'jpeg', 'PNG']])]
    imgdir_orig = imgdir
    wd = os.getcwd()
    for r in factors + resolutions:
        if isinstance(r, int):
            name = 'images_{}'.format(r)
            resizearg = '{}%'.format(int(100.0 / r))
        else:
            name = 'images_{}x{}'.format(r[1], r[0])
            resizearg = '{}x{}'.format(r[1], r[0])
        imgdir = os.path.join(basedir, name)
        if os.path.exists(imgdir):
            continue
        print('Minifying', r, basedir)
        os.makedirs(imgdir)
        check_output('cp {}/* {}'.format(imgdir_orig, imgdir), shell=True)
        ext = imgs[0].split('.')[-1]
        args = ' '.join(['mogrify', '-resize', resizearg, '-format', 'png', '*.{}'.format(ext)])
        print(args)
        os.chdir(imgdir)
        check_output(args, shell=True)
        os.chdir(wd)
        if ext != 'png':
            check_output('rm {}/*.{}'.format(imgdir, ext), shell=True)
            print('Removed duplicates')
        print('Done')

def load_data(basedir, factor=None, width=None, height=None, load_imgs=True):
    poses_arr = np.load(os.path.join(basedir, 'poses_bounds.npy'))
    poses = poses_arr[:, :-2].reshape([-1, 3, 5]).transpose([1, 2, 0])
    bds = poses_arr[:, -2:].transpose([1, 0])
    img0 = [os.path.join(basedir, 'images', f) for f in sorted(os.listdir(os.path.join(basedir, 'images'))) if f.endswith('JPG') or f.endswith('jpg') or f.endswith('png')][0]
    sh = imageio.imread(img0).shape
    sfx = ''
    if factor is not None:
        sfx = '_{}'.format(factor)
        minify(basedir, factors=[factor])
        factor = factor
    elif height is not None:
        factor = sh[0] / float(height)
        width = int(sh[1] / factor)
        minify(basedir, resolutions=[[height, width]])
        sfx = '_{}x{}'.format(width, height)
    elif width is not None:
        factor = sh[1] / float(width)
        height = int(sh[0] / factor)
        minify(basedir, resolutions=[[height, width]])
        sfx = '_{}x{}'.format(width, height)
    else:
        factor = 1
    imgdir = os.path.join(basedir, 'images' + sfx)
    if not os.path.exists(imgdir):
        print(imgdir, 'does not exist, returning')
        return
    imgfiles = [os.path.join(imgdir, f) for f in sorted(os.listdir(imgdir)) if f.endswith('JPG') or f.endswith('jpg') or f.endswith('png')]
    if poses.shape[-1] != len(imgfiles):
        print('Mismatch between imgs {} and poses {} !!!!'.format(len(imgfiles), poses.shape[-1]))
        return
    sh = imageio.imread(imgfiles[0]).shape
    poses[:2, 4, :] = np.array(sh[:2]).reshape([2, 1])
    poses[2, 4, :] = poses[2, 4, :] * 1.0 / factor
    if not load_imgs:
        return (poses, bds)

    def imread(f):
        if f.endswith('png'):
            return imageio.imread(f, ignoregamma=True)
        else:
            return imageio.imread(f)
    imgs = imgs = [imread(f)[..., :3] / 255.0 for f in imgfiles]
    imgs = np.stack(imgs, -1)
    print('Loaded image data', imgs.shape, poses[:, -1, 0])
    return (poses, bds, imgs)

def imread(f):
    if f.endswith('png'):
        return imageio.imread(f, ignoregamma=True)
    else:
        return imageio.imread(f)

def gen_poses(basedir, match_type, factors=None):
    files_needed = ['{}.bin'.format(f) for f in ['cameras', 'images', 'points3D']]
    if os.path.exists(os.path.join(basedir, 'sparse/0')):
        files_had = os.listdir(os.path.join(basedir, 'sparse/0'))
    else:
        files_had = []
    if not all([f in files_had for f in files_needed]):
        print('Need to run COLMAP')
        run_colmap(basedir, match_type)
    else:
        print("Don't need to run COLMAP")
    print('Post-colmap')
    poses, pts3d, perm = load_colmap_data(basedir)
    save_poses(basedir, poses, pts3d, perm)
    if factors is not None:
        print('Factors:', factors)
        minify(basedir, factors)
    print('Done with imgs2poses')
    return True

def run_colmap(basedir, match_type):
    logfile_name = os.path.join(basedir, 'colmap_output.txt')
    logfile = open(logfile_name, 'w')
    feature_extractor_args = ['colmap', 'feature_extractor', '--database_path', os.path.join(basedir, 'database.db'), '--image_path', os.path.join(basedir, 'images'), '--ImageReader.single_camera', '1']
    feat_output = subprocess.check_output(feature_extractor_args, universal_newlines=True)
    logfile.write(feat_output)
    print('Features extracted')
    exhaustive_matcher_args = ['colmap', match_type, '--database_path', os.path.join(basedir, 'database.db')]
    match_output = subprocess.check_output(exhaustive_matcher_args, universal_newlines=True)
    logfile.write(match_output)
    print('Features matched')
    p = os.path.join(basedir, 'sparse')
    if not os.path.exists(p):
        os.makedirs(p)
    mapper_args = ['colmap', 'mapper', '--database_path', os.path.join(basedir, 'database.db'), '--image_path', os.path.join(basedir, 'images'), '--output_path', os.path.join(basedir, 'sparse'), '--Mapper.num_threads', '16', '--Mapper.init_min_tri_angle', '4', '--Mapper.multiple_models', '0', '--Mapper.extract_colors', '0']
    map_output = subprocess.check_output(mapper_args, universal_newlines=True)
    logfile.write(map_output)
    logfile.close()
    print('Sparse map created')
    print('Finished running COLMAP, see {} for logs'.format(logfile_name))

def main():
    if len(sys.argv) != 3:
        print('Usage: python read_model.py path/to/model/folder [.txt,.bin]')
        return
    cameras, images, points3D = read_model(path=sys.argv[1], ext=sys.argv[2])
    print('num_cameras:', len(cameras))
    print('num_images:', len(images))
    print('num_points3D:', len(points3D))

def render_set(args, name, iteration, views, gaussians, background):
    model_path = args.model_path
    render_path = os.path.join(model_path, name, 'ours_{}'.format(iteration), 'renders')
    gts_path = os.path.join(model_path, name, 'ours_{}'.format(iteration), 'gt')
    makedirs(render_path, exist_ok=True)
    makedirs(gts_path, exist_ok=True)
    if args.render_depth:
        depth_path = os.path.join(model_path, name, 'ours_{}'.format(iteration), 'depth')
        makedirs(depth_path, exist_ok=True)
    if args.render_opacity:
        opacity_path = os.path.join(model_path, name, 'ours_{}'.format(iteration), 'opacity')
        makedirs(opacity_path, exist_ok=True)
    for idx, view in enumerate(tqdm(views, desc='Rendering progress')):
        render_pkg = render(view, gaussians, args, background, exposure_scale=view.exposure_scale)
        gt = view.original_image[0:3, :, :]
        torchvision.utils.save_image(render_pkg['render'], os.path.join(render_path, '{0:05d}'.format(idx) + '.png'))
        torchvision.utils.save_image(gt, os.path.join(gts_path, '{0:05d}'.format(idx) + '.png'))

def render_set(args, view_cameras, iteration):
    with torch.no_grad():
        gaussians = GaussianModel(args)
        loaded_iter = searchForMaxIteration(os.path.join(args.model_path, 'point_cloud'))
        gaussians.load_ply(os.path.join(args.model_path, 'point_cloud', 'iteration_' + str(loaded_iter), 'point_cloud.ply'))
        sky_weigth_path = os.path.join(args.model_path, 'point_cloud', 'iteration_' + str(loaded_iter), 'sky_weight.pth')
        if gaussians.sky_model is not None and os.path.exists(sky_weigth_path):
            gaussians.sky_model.restore(torch.load(sky_weigth_path))
        bg_color = [0, 0, 0]
        background = torch.tensor(bg_color, dtype=torch.float32, device='cuda')
        model_path = args.model_path
        render_path = os.path.join(model_path, 'chatsim_novel_views')
        makedirs(render_path, exist_ok=True)
        print('Rendering and saving to images')
        rendered_images_tensor_list = []
        for idx, view in tqdm(enumerate(view_cameras)):
            render_pkg = render(view, gaussians, args, background, exposure_scale=1.0 if args.load_exposure else None)
            rendered_images_tensor_list.append((render_pkg['render'].permute(1, 2, 0).clamp(0, 1).cpu().numpy() * 255).astype(np.uint8))
        with open(os.path.join(render_path, 'rendered.pkl'), 'wb') as f:
            pickle.dump(rendered_images_tensor_list, f)

def readImages(renders_dir, gt_dir):
    renders = []
    gts = []
    image_names = []
    for fname in os.listdir(renders_dir):
        render = Image.open(renders_dir / fname)
        gt = Image.open(gt_dir / fname)
        renders.append(tf.to_tensor(render).unsqueeze(0)[:, :3, :, :].cuda())
        gts.append(tf.to_tensor(gt).unsqueeze(0)[:, :3, :, :].cuda())
        image_names.append(fname)
    return (renders, gts, image_names)

def evaluate(model_paths):
    full_dict = {}
    per_view_dict = {}
    full_dict_polytopeonly = {}
    per_view_dict_polytopeonly = {}
    print('')
    for scene_dir in model_paths:
        try:
            print('Scene:', scene_dir)
            full_dict[scene_dir] = {}
            per_view_dict[scene_dir] = {}
            full_dict_polytopeonly[scene_dir] = {}
            per_view_dict_polytopeonly[scene_dir] = {}
            test_dir = Path(scene_dir) / 'test'
            train_dir = Path(scene_dir) / 'train'
            evaulation = {'test': test_dir, 'train': train_dir}
            for split, split_dir in evaulation.items():
                if not os.path.exists(split_dir):
                    continue
                for method in os.listdir(split_dir):
                    print('Method:', method)
                    full_dict[scene_dir][method] = {}
                    per_view_dict[scene_dir][method] = {}
                    full_dict_polytopeonly[scene_dir][method] = {}
                    per_view_dict_polytopeonly[scene_dir][method] = {}
                    method_dir = split_dir / method
                    gt_dir = method_dir / 'gt'
                    renders_dir = method_dir / 'renders'
                    subdirs = [d for d in os.listdir(gt_dir) if os.path.isdir(gt_dir / d)]
                    if len(subdirs) == 0:
                        renders, gts, image_names = readImages(renders_dir, gt_dir)
                        ssims = []
                        psnrs = []
                        lpipss = []
                        for idx in tqdm(range(len(renders)), desc='Metric evaluation progress'):
                            ssims.append(ssim(renders[idx], gts[idx]))
                            psnrs.append(psnr(renders[idx], gts[idx]))
                            lpipss.append(lpips(renders[idx], gts[idx], net_type='vgg'))
                        print('  SSIM : {:>12.7f}'.format(torch.tensor(ssims).mean(), '.5'))
                        print('  PSNR : {:>12.7f}'.format(torch.tensor(psnrs).mean(), '.5'))
                        print('  LPIPS: {:>12.7f}'.format(torch.tensor(lpipss).mean(), '.5'))
                        print('')
                        full_dict[scene_dir][method].update({'SSIM': torch.tensor(ssims).mean().item(), 'PSNR': torch.tensor(psnrs).mean().item(), 'LPIPS': torch.tensor(lpipss).mean().item()})
                        per_view_dict[scene_dir][method].update({'SSIM': {name: ssim for ssim, name in zip(torch.tensor(ssims).tolist(), image_names)}, 'PSNR': {name: psnr for psnr, name in zip(torch.tensor(psnrs).tolist(), image_names)}, 'LPIPS': {name: lp for lp, name in zip(torch.tensor(lpipss).tolist(), image_names)}})
                    else:
                        for subdir in subdirs:
                            print(' Subdir:', subdir)
                            renders, gts, image_names = readImages(renders_dir / subdir, gt_dir / subdir)
                            ssims = []
                            psnrs = []
                            lpipss = []
                            for idx in tqdm(range(len(renders)), desc='Metric evaluation progress'):
                                ssims.append(ssim(renders[idx], gts[idx]))
                                psnrs.append(psnr(renders[idx], gts[idx]))
                                lpipss.append(lpips(renders[idx], gts[idx], net_type='vgg'))
                            print('  SSIM : {:>12.7f}'.format(torch.tensor(ssims).mean(), '.5'))
                            print('  PSNR : {:>12.7f}'.format(torch.tensor(psnrs).mean(), '.5'))
                            print('  LPIPS: {:>12.7f}'.format(torch.tensor(lpipss).mean(), '.5'))
                            print('')
                            full_dict[scene_dir][method][subdir] = {}
                            per_view_dict[scene_dir][method][subdir] = {}
                            full_dict[scene_dir][method][subdir].update({'SSIM': torch.tensor(ssims).mean().item(), 'PSNR': torch.tensor(psnrs).mean().item(), 'LPIPS': torch.tensor(lpipss).mean().item()})
                            per_view_dict[scene_dir][method][subdir].update({'SSIM': {name: ssim for ssim, name in zip(torch.tensor(ssims).tolist(), image_names)}, 'PSNR': {name: psnr for psnr, name in zip(torch.tensor(psnrs).tolist(), image_names)}, 'LPIPS': {name: lp for lp, name in zip(torch.tensor(lpipss).tolist(), image_names)}})
                    with open(scene_dir + f'/{split}_results.json', 'w') as fp:
                        json.dump(full_dict[scene_dir], fp, indent=True)
                    with open(scene_dir + f'/{split}_per_view.json', 'w') as fp:
                        json.dump(per_view_dict[scene_dir], fp, indent=True)
        except Exception as e:
            print('Unable to compute metrics for model', scene_dir, ':', e)

class F:

    def __init__(self, silent):
        self.silent = silent

    def write(self, x):
        if not self.silent:
            if x.endswith('\n'):
                old_f.write(x.replace('\n', ' [{}]\n'.format(str(datetime.now().strftime('%d/%m %H:%M:%S')))))
            else:
                old_f.write(x)

    def flush(self):
        old_f.flush()

def write(self, x):
    if not self.silent:
        if x.endswith('\n'):
            old_f.write(x.replace('\n', ' [{}]\n'.format(str(datetime.now().strftime('%d/%m %H:%M:%S')))))
        else:
            old_f.write(x)

def flush(self):
    old_f.flush()

def mkdir_p(folder_path):
    try:
        makedirs(folder_path)
    except OSError as exc:
        if exc.errno == EEXIST and path.isdir(folder_path):
            pass
        else:
            raise

def readColmapCameras(cam_extrinsics, cam_intrinsics, images_folder, args):
    cam_infos = []
    for idx, key in enumerate(cam_extrinsics):
        sys.stdout.write('\r')
        sys.stdout.write('Reading camera {}/{}'.format(idx + 1, len(cam_extrinsics)))
        sys.stdout.flush()
        extr = cam_extrinsics[key]
        intr = cam_intrinsics[extr.camera_id]
        height = intr.height
        width = intr.width
        uid = intr.id
        R = np.transpose(qvec2rotmat(extr.qvec))
        T = np.array(extr.tvec)
        if intr.model == 'SIMPLE_PINHOLE':
            focal_length_x = intr.params[0]
            FovY = focal2fov(focal_length_x, height)
            FovX = focal2fov(focal_length_x, width)
        elif intr.model == 'PINHOLE':
            focal_length_x = intr.params[0]
            focal_length_y = intr.params[1]
            FovY = focal2fov(focal_length_y, height)
            FovX = focal2fov(focal_length_x, width)
        else:
            assert False, 'Colmap camera model not handled: only undistorted datasets (PINHOLE or SIMPLE_PINHOLE cameras) supported!'
        image_path = os.path.join(images_folder, os.path.basename(extr.name))
        image_name = os.path.basename(image_path).split('.')[0]
        image = Image.open(image_path)
        cam_info = CameraInfo(uid=uid, R=R, T=T, FovY=FovY, FovX=FovX, image=image, image_path=image_path, image_name=image_name, width=width, height=height, K=intr.params)
        cam_infos.append(cam_info)
    sys.stdout.write('\n')
    return cam_infos

def fetchPly(path):
    plydata = PlyData.read(path)
    vertices = plydata['vertex']
    positions = np.vstack([vertices['x'], vertices['y'], vertices['z']]).T
    colors = np.vstack([vertices['red'], vertices['green'], vertices['blue']]).T / 255.0
    normals = np.vstack([vertices['nx'], vertices['ny'], vertices['nz']]).T
    return BasicPointCloud(points=positions, colors=colors, normals=normals)

def fetchPlyOpen3D(path):
    open3d_data = open3d.io.read_point_cloud(path)
    positions = np.array(open3d_data.points)
    colors = np.array(open3d_data.colors)
    normals = np.zeros_like(positions)
    return BasicPointCloud(points=positions, colors=colors, normals=normals)

def storePly(path, xyz, rgb):
    dtype = [('x', 'f4'), ('y', 'f4'), ('z', 'f4'), ('nx', 'f4'), ('ny', 'f4'), ('nz', 'f4'), ('red', 'u1'), ('green', 'u1'), ('blue', 'u1')]
    normals = np.zeros_like(xyz)
    elements = np.empty(xyz.shape[0], dtype=dtype)
    attributes = np.concatenate((xyz, normals, rgb), axis=1)
    elements[:] = list(map(tuple, attributes))
    vertex_element = PlyElement.describe(elements, 'vertex')
    ply_data = PlyData([vertex_element])
    ply_data.write(path)

def readChatsimSceneInfo(args):
    """
    This is modified for ChatSim, which use points3D_waymo.ply for initialization

    points3D_waymo.ply is from recalibration with COLMAP. See data_utils/README.md for details
    """
    path = args.source_path
    images = args.images
    cams_meta_file = os.path.join(path, 'cams_meta.npy')
    ply_path = os.path.join(path, 'points3D_waymo.ply')
    images_folder = os.path.join(path, 'images')
    image_name_list = os.listdir(images_folder)
    image_file_list = [os.path.join(images_folder, f) for f in os.listdir(images_folder)]
    image_name_list.sort()
    image_file_list.sort()
    cam_infos_unsorted = []
    cams_meta = np.load(cams_meta_file)
    for idx, cam_data in enumerate(cams_meta):
        image_path = image_file_list[idx]
        image_name = image_name_list[idx]
        image = Image.open(image_file_list[idx])
        H, W = image.size
        c2w_RUB = np.eye(4)
        c2w_RUB[:3, :] = cam_data[:12].reshape(3, 4)
        c2w_RDF = np.concatenate([c2w_RUB[:, 0:1], -c2w_RUB[:, 1:2], -c2w_RUB[:, 2:3], c2w_RUB[:, 3:4]], axis=1)
        c2w = c2w_RDF
        w2c = np.linalg.inv(c2w)
        camera_intrinsics = cam_data[12:21].reshape(3, 3)
        R = c2w[:3, :3]
        T = w2c[:3, 3]
        K = np.array([camera_intrinsics[0, 0], camera_intrinsics[1, 1], camera_intrinsics[0, 2], camera_intrinsics[1, 2]])
        FoVx = 2 * np.arctan(W / (2 * camera_intrinsics[0, 0]))
        FoVy = 2 * np.arctan(H / (2 * camera_intrinsics[1, 1]))
        cam_info = CameraInfo(uid=idx, R=R, T=T, FovY=FoVy, FovX=FoVx, image=image, image_path=image_path, image_name=image_name, width=W, height=H, K=K)
        if args.get('load_sky_mask', False):
            sky_mask_folder = args.sky_mask_folder
            sky_mask_path = image_path.replace(os.path.basename(images_folder), sky_mask_folder)
            try:
                sky_mask = Image.open(sky_mask_path)
            except:
                sky_mask = Image.open(sky_mask_path + '.png')
            sky_mask = np.array(sky_mask)
            cam_info = cam_info._replace(sky_mask=sky_mask)
        if args.get('load_normal', False):
            normal_folder = args.normal_folder
            normal_path = image_path.replace(os.path.basename(images_folder), normal_folder).replace('.png', '.exr')
            normal = Image.open(normal_path)
            normal = np.array(normal)
            cam_info = cam_info._replace(normal=normal)
        if args.get('load_depth', False):
            depth_folder = args.depth_folder
            depth_path = image_path.replace(os.path.basename(images_folder), depth_folder).replace('.png', '.exr')
            depth = imageio.imread(depth_path)
            cam_info = cam_info._replace(depth=depth)
        if args.get('load_exposure', False):
            exposure_folder = args.exposure_folder
            exposure_path = os.path.join(image_path.split('colmap/')[0], exposure_folder, image_name + '.txt')
            with open(exposure_path, 'r') as f:
                exposure = float(f.read())
            exposure_scale = 1 + args.exposure_coefficient * exposure
            cam_info = cam_info._replace(exposure_scale=exposure_scale)
        cam_infos_unsorted.append(cam_info)
    cam_infos = sorted(cam_infos_unsorted.copy(), key=lambda x: x.image_name)
    if args.eval:
        train_cam_infos = [c for idx, c in enumerate(cam_infos) if idx % args.llffhold != 0]
        test_cam_infos = [c for idx, c in enumerate(cam_infos) if idx % args.llffhold == 0]
    else:
        train_cam_infos = cam_infos
        test_cam_infos = []
    nerf_normalization = getNerfppNorm(train_cam_infos)
    assert os.path.exists(ply_path), 'Please run recalibration with colmap or download provided calibration files'
    try:
        pcd = fetchPlyOpen3D(ply_path)
    except:
        pcd = None
    scene_info = SceneInfo(point_cloud=pcd, train_cameras=train_cam_infos, test_cameras=test_cam_infos, nerf_normalization=nerf_normalization, ply_path=ply_path)
    return scene_info

def readColmapSceneInfo(args):
    path = args.source_path
    images = args.images
    try:
        cameras_extrinsic_file = os.path.join(path, f'sparse/{args.sparse_folder}', 'images.bin')
        cameras_intrinsic_file = os.path.join(path, f'sparse/{args.sparse_folder}', 'cameras.bin')
        cam_extrinsics = read_extrinsics_binary(cameras_extrinsic_file)
        cam_intrinsics = read_intrinsics_binary(cameras_intrinsic_file)
    except:
        cameras_extrinsic_file = os.path.join(path, f'sparse/{args.sparse_folder}', 'images.txt')
        cameras_intrinsic_file = os.path.join(path, f'sparse/{args.sparse_folder}', 'cameras.txt')
        cam_extrinsics = read_extrinsics_text(cameras_extrinsic_file)
        cam_intrinsics = read_intrinsics_text(cameras_intrinsic_file)
    reading_dir = 'images' if images == None else images
    cam_infos_unsorted = readColmapCameras(cam_extrinsics=cam_extrinsics, cam_intrinsics=cam_intrinsics, images_folder=os.path.join(path, reading_dir), args=args)
    cam_infos = sorted(cam_infos_unsorted.copy(), key=lambda x: x.image_name)
    if args.eval:
        train_cam_infos = [c for idx, c in enumerate(cam_infos) if idx % args.llffhold != 0]
        test_cam_infos = [c for idx, c in enumerate(cam_infos) if idx % args.llffhold == 0]
    else:
        train_cam_infos = cam_infos
        test_cam_infos = []
    nerf_normalization = getNerfppNorm(train_cam_infos)
    ply_path = os.path.join(path, f'sparse/{args.sparse_folder}', 'points3D.ply')
    bin_path = os.path.join(path, f'sparse/{args.sparse_folder}', 'points3D.bin')
    txt_path = os.path.join(path, f'sparse/{args.sparse_folder}', 'points3D.txt')
    if not os.path.exists(ply_path):
        print('Converting point3d.bin to .ply, will happen only the first time you open the scene.')
        try:
            xyz, rgb, _ = read_points3D_binary(bin_path)
        except:
            xyz, rgb, _ = read_points3D_text(txt_path)
        storePly(ply_path, xyz, rgb)
    try:
        pcd = fetchPly(ply_path)
    except:
        pcd = None
    scene_info = SceneInfo(point_cloud=pcd, train_cameras=train_cam_infos, test_cameras=test_cam_infos, nerf_normalization=nerf_normalization, ply_path=ply_path)
    return scene_info

def readCamerasFromTransforms(path, transformsfile, white_background, extension='.png'):
    cam_infos = []
    with open(os.path.join(path, transformsfile)) as json_file:
        contents = json.load(json_file)
        fovx = contents['camera_angle_x']
        frames = contents['frames']
        for idx, frame in enumerate(frames):
            cam_name = os.path.join(path, frame['file_path'] + extension)
            c2w = np.array(frame['transform_matrix'])
            c2w[:3, 1:3] *= -1
            w2c = np.linalg.inv(c2w)
            R = np.transpose(w2c[:3, :3])
            T = w2c[:3, 3]
            image_path = os.path.join(path, cam_name)
            image_name = Path(cam_name).stem
            image = Image.open(image_path)
            im_data = np.array(image.convert('RGBA'))
            bg = np.array([1, 1, 1]) if white_background else np.array([0, 0, 0])
            norm_data = im_data / 255.0
            arr = norm_data[:, :, :3] * norm_data[:, :, 3:4] + bg * (1 - norm_data[:, :, 3:4])
            image = Image.fromarray(np.array(arr * 255.0, dtype=np.byte), 'RGB')
            fovy = focal2fov(fov2focal(fovx, image.size[0]), image.size[1])
            FovY = fovy
            FovX = fovx
            cam_infos.append(CameraInfo(uid=idx, R=R, T=T, FovY=FovY, FovX=FovX, image=image, image_path=image_path, image_name=image_name, width=image.size[0], height=image.size[1]))
    return cam_infos

def readNerfSyntheticInfo(path, white_background, eval, extension='.png'):
    print('Reading Training Transforms')
    train_cam_infos = readCamerasFromTransforms(path, 'transforms_train.json', white_background, extension)
    print('Reading Test Transforms')
    test_cam_infos = readCamerasFromTransforms(path, 'transforms_test.json', white_background, extension)
    if not eval:
        train_cam_infos.extend(test_cam_infos)
        test_cam_infos = []
    nerf_normalization = getNerfppNorm(train_cam_infos)
    ply_path = os.path.join(path, 'points3d.ply')
    if not os.path.exists(ply_path):
        num_pts = 100000
        print(f'Generating random point cloud ({num_pts})...')
        xyz = np.random.random((num_pts, 3)) * 2.6 - 1.3
        shs = np.random.random((num_pts, 3)) / 255.0
        pcd = BasicPointCloud(points=xyz, colors=SH2RGB(shs), normals=np.zeros((num_pts, 3)))
        storePly(ply_path, xyz, SH2RGB(shs) * 255)
    try:
        pcd = fetchPly(ply_path)
    except:
        pcd = None
    scene_info = SceneInfo(point_cloud=pcd, train_cameras=train_cam_infos, test_cameras=test_cam_infos, nerf_normalization=nerf_normalization, ply_path=ply_path)
    return scene_info

class Scene:
    gaussians: GaussianModel

    def __init__(self, args, gaussians: GaussianModel, load_iteration=None, shuffle=True, resolution_scales=[1.0]):
        """b
        :param path: Path to colmap scene main folder.
        """
        self.model_path = args.model_path
        self.loaded_iter = None
        self.gaussians = gaussians
        if load_iteration:
            if load_iteration == -1:
                self.loaded_iter = searchForMaxIteration(os.path.join(self.model_path, 'point_cloud'))
            else:
                self.loaded_iter = load_iteration
            print('Loading trained model at iteration {}'.format(self.loaded_iter))
        self.train_cameras = {}
        self.test_cameras = {}
        scene_info = sceneLoadTypeCallbacks[args.scene_type](args)
        if not self.loaded_iter:
            with open(scene_info.ply_path, 'rb') as src_file, open(os.path.join(self.model_path, 'input.ply'), 'wb') as dest_file:
                dest_file.write(src_file.read())
            json_cams = []
            camlist = []
            if scene_info.test_cameras:
                camlist.extend(scene_info.test_cameras)
            if scene_info.train_cameras:
                camlist.extend(scene_info.train_cameras)
            for id, cam in enumerate(camlist):
                json_cams.append(camera_to_JSON(id, cam))
            with open(os.path.join(self.model_path, 'cameras.json'), 'w') as file:
                json.dump(json_cams, file)
        if shuffle:
            random.shuffle(scene_info.train_cameras)
            random.shuffle(scene_info.test_cameras)
        self.cameras_extent = scene_info.nerf_normalization['radius']
        for resolution_scale in resolution_scales:
            print('Loading Training Cameras')
            self.train_cameras[resolution_scale] = cameraList_from_camInfos(scene_info.train_cameras, resolution_scale, args)
            print('Loading Test Cameras')
            self.test_cameras[resolution_scale] = cameraList_from_camInfos(scene_info.test_cameras, resolution_scale, args)
        if self.loaded_iter:
            self.gaussians.load_ply(os.path.join(self.model_path, 'point_cloud', 'iteration_' + str(self.loaded_iter), 'point_cloud.ply'))
            sky_weigth_path = os.path.join(self.model_path, 'point_cloud', 'iteration_' + str(self.loaded_iter), 'sky_weight.pth')
            if self.gaussians.sky_model is not None and os.path.exists(sky_weigth_path):
                self.gaussians.sky_model.restore(torch.load(sky_weigth_path))
        else:
            self.gaussians.create_from_pcd(scene_info.point_cloud, self.cameras_extent)

    def save(self, iteration):
        point_cloud_path = os.path.join(self.model_path, 'point_cloud/iteration_{}'.format(iteration))
        self.gaussians.save_ply(os.path.join(point_cloud_path, 'point_cloud.ply'))
        if self.gaussians.sky_model is not None:
            torch.save(self.gaussians.sky_model.capture(), os.path.join(point_cloud_path, 'sky_weight.pth'))

    def getTrainCameras(self, scale=1.0):
        return self.train_cameras[scale]

    def getTestCameras(self, scale=1.0):
        return self.test_cameras[scale]

def __init__(self, args, gaussians: GaussianModel, load_iteration=None, shuffle=True, resolution_scales=[1.0]):
    """b
        :param path: Path to colmap scene main folder.
        """
    self.model_path = args.model_path
    self.loaded_iter = None
    self.gaussians = gaussians
    if load_iteration:
        if load_iteration == -1:
            self.loaded_iter = searchForMaxIteration(os.path.join(self.model_path, 'point_cloud'))
        else:
            self.loaded_iter = load_iteration
        print('Loading trained model at iteration {}'.format(self.loaded_iter))
    self.train_cameras = {}
    self.test_cameras = {}
    scene_info = sceneLoadTypeCallbacks[args.scene_type](args)
    if not self.loaded_iter:
        with open(scene_info.ply_path, 'rb') as src_file, open(os.path.join(self.model_path, 'input.ply'), 'wb') as dest_file:
            dest_file.write(src_file.read())
        json_cams = []
        camlist = []
        if scene_info.test_cameras:
            camlist.extend(scene_info.test_cameras)
        if scene_info.train_cameras:
            camlist.extend(scene_info.train_cameras)
        for id, cam in enumerate(camlist):
            json_cams.append(camera_to_JSON(id, cam))
        with open(os.path.join(self.model_path, 'cameras.json'), 'w') as file:
            json.dump(json_cams, file)
    if shuffle:
        random.shuffle(scene_info.train_cameras)
        random.shuffle(scene_info.test_cameras)
    self.cameras_extent = scene_info.nerf_normalization['radius']
    for resolution_scale in resolution_scales:
        print('Loading Training Cameras')
        self.train_cameras[resolution_scale] = cameraList_from_camInfos(scene_info.train_cameras, resolution_scale, args)
        print('Loading Test Cameras')
        self.test_cameras[resolution_scale] = cameraList_from_camInfos(scene_info.test_cameras, resolution_scale, args)
    if self.loaded_iter:
        self.gaussians.load_ply(os.path.join(self.model_path, 'point_cloud', 'iteration_' + str(self.loaded_iter), 'point_cloud.ply'))
        sky_weigth_path = os.path.join(self.model_path, 'point_cloud', 'iteration_' + str(self.loaded_iter), 'sky_weight.pth')
        if self.gaussians.sky_model is not None and os.path.exists(sky_weigth_path):
            self.gaussians.sky_model.restore(torch.load(sky_weigth_path))
    else:
        self.gaussians.create_from_pcd(scene_info.point_cloud, self.cameras_extent)

def save(self, iteration):
    point_cloud_path = os.path.join(self.model_path, 'point_cloud/iteration_{}'.format(iteration))
    self.gaussians.save_ply(os.path.join(point_cloud_path, 'point_cloud.ply'))
    if self.gaussians.sky_model is not None:
        torch.save(self.gaussians.sky_model.capture(), os.path.join(point_cloud_path, 'sky_weight.pth'))

class GaussianModel:

    def setup_functions(self):

        def build_covariance_from_scaling_rotation(scaling, scaling_modifier, rotation):
            L = build_scaling_rotation(scaling_modifier * scaling, rotation)
            actual_covariance = L @ L.transpose(1, 2)
            symm = strip_symmetric(actual_covariance)
            return symm
        self.scaling_activation = torch.exp
        self.scaling_inverse_activation = torch.log
        self.covariance_activation = build_covariance_from_scaling_rotation
        self.opacity_activation = torch.sigmoid
        self.inverse_opacity_activation = inverse_sigmoid
        self.rotation_activation = torch.nn.functional.normalize

    def __init__(self, args):
        self.active_sh_degree = 0
        self.max_sh_degree = args.sh_degree
        self._xyz = torch.empty(0)
        self._features_dc = torch.empty(0)
        self._features_rest = torch.empty(0)
        self._scaling = torch.empty(0)
        self._rotation = torch.empty(0)
        self._opacity = torch.empty(0)
        self.max_radii2D = torch.empty(0)
        self.xyz_gradient_accum = torch.empty(0)
        self.denom = torch.empty(0)
        self.optimizer = None
        self.percent_dense = 0
        self.spatial_lr_scale = 0
        self.setup_functions()
        if args.get('sky_model', None) is not None:
            model_filename = 'scene.sky.' + args.sky_model
            model_lib = importlib.import_module(model_filename)
            model_cls = None
            target_model_name = args.sky_model.replace('_', '')
            for name, cls in model_lib.__dict__.items():
                if name.lower() == target_model_name.lower():
                    model_cls = cls
            self.sky_model = model_cls(args.sky_model_args).cuda()
        else:
            self.sky_model = None

    def capture(self):
        return_list = [self.active_sh_degree, self._xyz, self._features_dc, self._features_rest, self._scaling, self._rotation, self._opacity, self.max_radii2D, self.xyz_gradient_accum, self.denom, self.optimizer.state_dict(), self.spatial_lr_scale]
        if self.sky_model is not None:
            return_list.append(self.sky_model.capture())
        return return_list

    def restore(self, model_args, training_args):
        if self.sky_model is not None:
            self.sky_model.restore(model_args.pop(-1))
        self.active_sh_degree, self._xyz, self._features_dc, self._features_rest, self._scaling, self._rotation, self._opacity, self.max_radii2D, xyz_gradient_accum, denom, opt_dict, self.spatial_lr_scale = model_args
        self.training_setup(training_args)
        self.xyz_gradient_accum = xyz_gradient_accum
        self.denom = denom
        self.optimizer.load_state_dict(opt_dict)

    @property
    def get_scaling(self):
        return self.scaling_activation(self._scaling)

    @property
    def get_rotation(self):
        return self.rotation_activation(self._rotation)

    @property
    def get_xyz(self):
        return self._xyz

    @property
    def get_features(self):
        features_dc = self._features_dc
        features_rest = self._features_rest
        return torch.cat((features_dc, features_rest), dim=1)

    @property
    def get_opacity(self):
        return self.opacity_activation(self._opacity)

    def get_covariance(self, scaling_modifier=1):
        return self.covariance_activation(self.get_scaling, scaling_modifier, self._rotation)

    def oneupSHdegree(self):
        if self.active_sh_degree < self.max_sh_degree:
            self.active_sh_degree += 1

    def create_from_pcd(self, pcd: BasicPointCloud, spatial_lr_scale: float):
        self.spatial_lr_scale = spatial_lr_scale
        fused_point_cloud = torch.tensor(np.asarray(pcd.points)).float().cuda()
        fused_color = RGB2SH(torch.tensor(np.asarray(pcd.colors)).float().cuda())
        features = torch.zeros((fused_color.shape[0], 3, (self.max_sh_degree + 1) ** 2)).float().cuda()
        features[:, :3, 0] = fused_color
        features[:, 3:, 1:] = 0.0
        print('Number of points at initialisation : ', fused_point_cloud.shape[0])
        dist2 = torch.clamp_min(distCUDA2(torch.from_numpy(np.asarray(pcd.points)).float().cuda()), 1e-07)
        scales = torch.log(torch.sqrt(dist2))[..., None].repeat(1, 3)
        rots = torch.zeros((fused_point_cloud.shape[0], 4), device='cuda')
        rots[:, 0] = 1
        opacities = inverse_sigmoid(0.1 * torch.ones((fused_point_cloud.shape[0], 1), dtype=torch.float, device='cuda'))
        self._xyz = nn.Parameter(fused_point_cloud.requires_grad_(True))
        self._features_dc = nn.Parameter(features[:, :, 0:1].transpose(1, 2).contiguous().requires_grad_(True))
        self._features_rest = nn.Parameter(features[:, :, 1:].transpose(1, 2).contiguous().requires_grad_(True))
        self._scaling = nn.Parameter(scales.requires_grad_(True))
        self._rotation = nn.Parameter(rots.requires_grad_(True))
        self._opacity = nn.Parameter(opacities.requires_grad_(True))
        self.max_radii2D = torch.zeros(self.get_xyz.shape[0], device='cuda')

    def training_setup(self, training_args):
        self.percent_dense = training_args.percent_dense
        self.xyz_gradient_accum = torch.zeros((self.get_xyz.shape[0], 1), device='cuda')
        self.denom = torch.zeros((self.get_xyz.shape[0], 1), device='cuda')
        l = [{'params': [self._xyz], 'lr': training_args.position_lr_init * self.spatial_lr_scale, 'name': 'xyz'}, {'params': [self._features_dc], 'lr': training_args.feature_lr, 'name': 'f_dc'}, {'params': [self._features_rest], 'lr': training_args.feature_lr / 20.0, 'name': 'f_rest'}, {'params': [self._opacity], 'lr': training_args.opacity_lr, 'name': 'opacity'}, {'params': [self._scaling], 'lr': training_args.scaling_lr, 'name': 'scaling'}, {'params': [self._rotation], 'lr': training_args.rotation_lr, 'name': 'rotation'}]
        if self.sky_model is not None:
            l += ({'params': self.sky_model.train_params(), 'lr': training_args.sky_model_lr, 'name': 'sky_model'},)
        self.optimizer = torch.optim.Adam(l, lr=0.0, eps=1e-15)
        self.xyz_scheduler_args = get_expon_lr_func(lr_init=training_args.position_lr_init * self.spatial_lr_scale, lr_final=training_args.position_lr_final * self.spatial_lr_scale, lr_delay_mult=training_args.position_lr_delay_mult, max_steps=training_args.position_lr_max_steps)

    def update_learning_rate(self, iteration):
        """ Learning rate scheduling per step """
        for param_group in self.optimizer.param_groups:
            if param_group['name'] == 'xyz':
                lr = self.xyz_scheduler_args(iteration)
                param_group['lr'] = lr
                return lr

    def construct_list_of_attributes(self):
        l = ['x', 'y', 'z', 'nx', 'ny', 'nz']
        for i in range(self._features_dc.shape[1] * self._features_dc.shape[2]):
            l.append('f_dc_{}'.format(i))
        for i in range(self._features_rest.shape[1] * self._features_rest.shape[2]):
            l.append('f_rest_{}'.format(i))
        l.append('opacity')
        for i in range(self._scaling.shape[1]):
            l.append('scale_{}'.format(i))
        for i in range(self._rotation.shape[1]):
            l.append('rot_{}'.format(i))
        return l

    def save_ply(self, path):
        mkdir_p(os.path.dirname(path))
        xyz = self._xyz.detach().cpu().numpy()
        normals = np.zeros_like(xyz)
        f_dc = self._features_dc.detach().transpose(1, 2).flatten(start_dim=1).contiguous().cpu().numpy()
        f_rest = self._features_rest.detach().transpose(1, 2).flatten(start_dim=1).contiguous().cpu().numpy()
        opacities = self._opacity.detach().cpu().numpy()
        scale = self._scaling.detach().cpu().numpy()
        rotation = self._rotation.detach().cpu().numpy()
        dtype_full = [(attribute, 'f4') for attribute in self.construct_list_of_attributes()]
        elements = np.empty(xyz.shape[0], dtype=dtype_full)
        attributes = np.concatenate((xyz, normals, f_dc, f_rest, opacities, scale, rotation), axis=1)
        elements[:] = list(map(tuple, attributes))
        el = PlyElement.describe(elements, 'vertex')
        PlyData([el]).write(path)

    def reset_opacity(self):
        opacities_new = inverse_sigmoid(torch.min(self.get_opacity, torch.ones_like(self.get_opacity) * 0.01))
        optimizable_tensors = self.replace_tensor_to_optimizer(opacities_new, 'opacity')
        self._opacity = optimizable_tensors['opacity']

    def load_ply(self, path):
        plydata = PlyData.read(path)
        xyz = np.stack((np.asarray(plydata.elements[0]['x']), np.asarray(plydata.elements[0]['y']), np.asarray(plydata.elements[0]['z'])), axis=1)
        opacities = np.asarray(plydata.elements[0]['opacity'])[..., np.newaxis]
        features_dc = np.zeros((xyz.shape[0], 3, 1))
        features_dc[:, 0, 0] = np.asarray(plydata.elements[0]['f_dc_0'])
        features_dc[:, 1, 0] = np.asarray(plydata.elements[0]['f_dc_1'])
        features_dc[:, 2, 0] = np.asarray(plydata.elements[0]['f_dc_2'])
        extra_f_names = [p.name for p in plydata.elements[0].properties if p.name.startswith('f_rest_')]
        extra_f_names = sorted(extra_f_names, key=lambda x: int(x.split('_')[-1]))
        assert len(extra_f_names) == 3 * (self.max_sh_degree + 1) ** 2 - 3
        features_extra = np.zeros((xyz.shape[0], len(extra_f_names)))
        for idx, attr_name in enumerate(extra_f_names):
            features_extra[:, idx] = np.asarray(plydata.elements[0][attr_name])
        features_extra = features_extra.reshape((features_extra.shape[0], 3, (self.max_sh_degree + 1) ** 2 - 1))
        scale_names = [p.name for p in plydata.elements[0].properties if p.name.startswith('scale_')]
        scale_names = sorted(scale_names, key=lambda x: int(x.split('_')[-1]))
        scales = np.zeros((xyz.shape[0], len(scale_names)))
        for idx, attr_name in enumerate(scale_names):
            scales[:, idx] = np.asarray(plydata.elements[0][attr_name])
        rot_names = [p.name for p in plydata.elements[0].properties if p.name.startswith('rot')]
        rot_names = sorted(rot_names, key=lambda x: int(x.split('_')[-1]))
        rots = np.zeros((xyz.shape[0], len(rot_names)))
        for idx, attr_name in enumerate(rot_names):
            rots[:, idx] = np.asarray(plydata.elements[0][attr_name])
        self._xyz = nn.Parameter(torch.tensor(xyz, dtype=torch.float, device='cuda').requires_grad_(True))
        self._features_dc = nn.Parameter(torch.tensor(features_dc, dtype=torch.float, device='cuda').transpose(1, 2).contiguous().requires_grad_(True))
        self._features_rest = nn.Parameter(torch.tensor(features_extra, dtype=torch.float, device='cuda').transpose(1, 2).contiguous().requires_grad_(True))
        self._opacity = nn.Parameter(torch.tensor(opacities, dtype=torch.float, device='cuda').requires_grad_(True))
        self._scaling = nn.Parameter(torch.tensor(scales, dtype=torch.float, device='cuda').requires_grad_(True))
        self._rotation = nn.Parameter(torch.tensor(rots, dtype=torch.float, device='cuda').requires_grad_(True))
        self.active_sh_degree = self.max_sh_degree

    def replace_tensor_to_optimizer(self, tensor, name):
        optimizable_tensors = {}
        for group in self.optimizer.param_groups:
            if group['name'] == name:
                stored_state = self.optimizer.state.get(group['params'][0], None)
                stored_state['exp_avg'] = torch.zeros_like(tensor)
                stored_state['exp_avg_sq'] = torch.zeros_like(tensor)
                del self.optimizer.state[group['params'][0]]
                group['params'][0] = nn.Parameter(tensor.requires_grad_(True))
                self.optimizer.state[group['params'][0]] = stored_state
                optimizable_tensors[group['name']] = group['params'][0]
        return optimizable_tensors

    def _prune_optimizer(self, mask):
        optimizable_tensors = {}
        for group in self.optimizer.param_groups:
            if 'sky_model' in group['name']:
                continue
            stored_state = self.optimizer.state.get(group['params'][0], None)
            if stored_state is not None:
                stored_state['exp_avg'] = stored_state['exp_avg'][mask]
                stored_state['exp_avg_sq'] = stored_state['exp_avg_sq'][mask]
                del self.optimizer.state[group['params'][0]]
                group['params'][0] = nn.Parameter(group['params'][0][mask].requires_grad_(True))
                self.optimizer.state[group['params'][0]] = stored_state
                optimizable_tensors[group['name']] = group['params'][0]
            else:
                group['params'][0] = nn.Parameter(group['params'][0][mask].requires_grad_(True))
                optimizable_tensors[group['name']] = group['params'][0]
        return optimizable_tensors

    def prune_points(self, mask):
        valid_points_mask = ~mask
        optimizable_tensors = self._prune_optimizer(valid_points_mask)
        self._xyz = optimizable_tensors['xyz']
        self._features_dc = optimizable_tensors['f_dc']
        self._features_rest = optimizable_tensors['f_rest']
        self._opacity = optimizable_tensors['opacity']
        self._scaling = optimizable_tensors['scaling']
        self._rotation = optimizable_tensors['rotation']
        self.xyz_gradient_accum = self.xyz_gradient_accum[valid_points_mask]
        self.denom = self.denom[valid_points_mask]
        self.max_radii2D = self.max_radii2D[valid_points_mask]

    def cat_tensors_to_optimizer(self, tensors_dict):
        optimizable_tensors = {}
        for group in self.optimizer.param_groups:
            if 'sky_model' in group['name']:
                continue
            assert len(group['params']) == 1
            extension_tensor = tensors_dict[group['name']]
            stored_state = self.optimizer.state.get(group['params'][0], None)
            if stored_state is not None:
                stored_state['exp_avg'] = torch.cat((stored_state['exp_avg'], torch.zeros_like(extension_tensor)), dim=0)
                stored_state['exp_avg_sq'] = torch.cat((stored_state['exp_avg_sq'], torch.zeros_like(extension_tensor)), dim=0)
                del self.optimizer.state[group['params'][0]]
                group['params'][0] = nn.Parameter(torch.cat((group['params'][0], extension_tensor), dim=0).requires_grad_(True))
                self.optimizer.state[group['params'][0]] = stored_state
                optimizable_tensors[group['name']] = group['params'][0]
            else:
                group['params'][0] = nn.Parameter(torch.cat((group['params'][0], extension_tensor), dim=0).requires_grad_(True))
                optimizable_tensors[group['name']] = group['params'][0]
        return optimizable_tensors

    def densification_postfix(self, new_xyz, new_features_dc, new_features_rest, new_opacities, new_scaling, new_rotation):
        d = {'xyz': new_xyz, 'f_dc': new_features_dc, 'f_rest': new_features_rest, 'opacity': new_opacities, 'scaling': new_scaling, 'rotation': new_rotation}
        optimizable_tensors = self.cat_tensors_to_optimizer(d)
        self._xyz = optimizable_tensors['xyz']
        self._features_dc = optimizable_tensors['f_dc']
        self._features_rest = optimizable_tensors['f_rest']
        self._opacity = optimizable_tensors['opacity']
        self._scaling = optimizable_tensors['scaling']
        self._rotation = optimizable_tensors['rotation']
        self.xyz_gradient_accum = torch.zeros((self.get_xyz.shape[0], 1), device='cuda')
        self.denom = torch.zeros((self.get_xyz.shape[0], 1), device='cuda')
        self.max_radii2D = torch.zeros(self.get_xyz.shape[0], device='cuda')

    def densify_and_split(self, grads, grad_threshold, scene_extent, N=2):
        n_init_points = self.get_xyz.shape[0]
        padded_grad = torch.zeros(n_init_points, device='cuda')
        padded_grad[:grads.shape[0]] = grads.squeeze()
        selected_pts_mask = torch.where(padded_grad >= grad_threshold, True, False)
        selected_pts_mask = torch.logical_and(selected_pts_mask, torch.max(self.get_scaling, dim=1).values > self.percent_dense * scene_extent)
        stds = self.get_scaling[selected_pts_mask].repeat(N, 1)
        means = torch.zeros((stds.size(0), 3), device='cuda')
        samples = torch.normal(mean=means, std=stds)
        rots = build_rotation(self._rotation[selected_pts_mask]).repeat(N, 1, 1)
        new_xyz = torch.bmm(rots, samples.unsqueeze(-1)).squeeze(-1) + self.get_xyz[selected_pts_mask].repeat(N, 1)
        new_scaling = self.scaling_inverse_activation(self.get_scaling[selected_pts_mask].repeat(N, 1) / (0.8 * N))
        new_rotation = self._rotation[selected_pts_mask].repeat(N, 1)
        new_features_dc = self._features_dc[selected_pts_mask].repeat(N, 1, 1)
        new_features_rest = self._features_rest[selected_pts_mask].repeat(N, 1, 1)
        new_opacity = self._opacity[selected_pts_mask].repeat(N, 1)
        self.densification_postfix(new_xyz, new_features_dc, new_features_rest, new_opacity, new_scaling, new_rotation)
        prune_filter = torch.cat((selected_pts_mask, torch.zeros(N * selected_pts_mask.sum(), device='cuda', dtype=bool)))
        self.prune_points(prune_filter)

    def densify_and_clone(self, grads, grad_threshold, scene_extent):
        selected_pts_mask = torch.where(torch.norm(grads, dim=-1) >= grad_threshold, True, False)
        selected_pts_mask = torch.logical_and(selected_pts_mask, torch.max(self.get_scaling, dim=1).values <= self.percent_dense * scene_extent)
        new_xyz = self._xyz[selected_pts_mask]
        new_features_dc = self._features_dc[selected_pts_mask]
        new_features_rest = self._features_rest[selected_pts_mask]
        new_opacities = self._opacity[selected_pts_mask]
        new_scaling = self._scaling[selected_pts_mask]
        new_rotation = self._rotation[selected_pts_mask]
        self.densification_postfix(new_xyz, new_features_dc, new_features_rest, new_opacities, new_scaling, new_rotation)

    def densify_and_prune(self, max_grad, min_opacity, extent, max_screen_size):
        grads = self.xyz_gradient_accum / self.denom
        grads[grads.isnan()] = 0.0
        self.densify_and_clone(grads, max_grad, extent)
        self.densify_and_split(grads, max_grad, extent)
        prune_mask = (self.get_opacity < min_opacity).squeeze()
        if max_screen_size:
            big_points_vs = self.max_radii2D > max_screen_size
            big_points_ws = self.get_scaling.max(dim=1).values > 0.1 * extent
            prune_mask = torch.logical_or(torch.logical_or(prune_mask, big_points_vs), big_points_ws)
        self.prune_points(prune_mask)
        torch.cuda.empty_cache()

    def add_densification_stats(self, viewspace_point_tensor, update_filter, width, height):
        grad = viewspace_point_tensor.grad.squeeze(0)
        grad[:, 0] *= width * 0.5
        grad[:, 1] *= height * 0.5
        self.xyz_gradient_accum[update_filter] += torch.norm(grad[update_filter, :2], dim=-1, keepdim=True)
        self.denom[update_filter] += 1

    def get_sky_bg(self, viewpoint_camera):
        return self.sky_model(viewpoint_camera)

def __init__(self, args):
    self.active_sh_degree = 0
    self.max_sh_degree = args.sh_degree
    self._xyz = torch.empty(0)
    self._features_dc = torch.empty(0)
    self._features_rest = torch.empty(0)
    self._scaling = torch.empty(0)
    self._rotation = torch.empty(0)
    self._opacity = torch.empty(0)
    self.max_radii2D = torch.empty(0)
    self.xyz_gradient_accum = torch.empty(0)
    self.denom = torch.empty(0)
    self.optimizer = None
    self.percent_dense = 0
    self.spatial_lr_scale = 0
    self.setup_functions()
    if args.get('sky_model', None) is not None:
        model_filename = 'scene.sky.' + args.sky_model
        model_lib = importlib.import_module(model_filename)
        model_cls = None
        target_model_name = args.sky_model.replace('_', '')
        for name, cls in model_lib.__dict__.items():
            if name.lower() == target_model_name.lower():
                model_cls = cls
        self.sky_model = model_cls(args.sky_model_args).cuda()
    else:
        self.sky_model = None

def capture(self):
    return_list = [self.active_sh_degree, self._xyz, self._features_dc, self._features_rest, self._scaling, self._rotation, self._opacity, self.max_radii2D, self.xyz_gradient_accum, self.denom, self.optimizer.state_dict(), self.spatial_lr_scale]
    if self.sky_model is not None:
        return_list.append(self.sky_model.capture())
    return return_list

def restore(self, model_args, training_args):
    if self.sky_model is not None:
        self.sky_model.restore(model_args.pop(-1))
    self.active_sh_degree, self._xyz, self._features_dc, self._features_rest, self._scaling, self._rotation, self._opacity, self.max_radii2D, xyz_gradient_accum, denom, opt_dict, self.spatial_lr_scale = model_args
    self.training_setup(training_args)
    self.xyz_gradient_accum = xyz_gradient_accum
    self.denom = denom
    self.optimizer.load_state_dict(opt_dict)

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

def capture(self):
    return self.state_dict()

def restore(self, model_args):
    self.load_state_dict(model_args)

def get_combined_args(parser: ArgumentParser):
    cmdlne_string = sys.argv[1:]
    cfgfile_string = 'Namespace()'
    args_cmdline = parser.parse_args(cmdlne_string)
    try:
        cfgfilepath = os.path.join(args_cmdline.model_path, 'cfg_args')
        print('Looking for config file in', cfgfilepath)
        with open(cfgfilepath) as cfg_file:
            print('Config file found: {}'.format(cfgfilepath))
            cfgfile_string = cfg_file.read()
    except TypeError:
        print('Config file not found at')
        pass
    args_cfgfile = eval(cfgfile_string)
    merged_dict = vars(args_cfgfile).copy()
    for k, v in vars(args_cmdline).items():
        if v != None:
            merged_dict[k] = v
    return Namespace(**merged_dict)

def merge_videos(video_path1, video_path2, output_path):
    cap1 = cv2.VideoCapture(video_path1)
    cap2 = cv2.VideoCapture(video_path2)
    fps1 = cap1.get(cv2.CAP_PROP_FPS)
    fps2 = cap2.get(cv2.CAP_PROP_FPS)
    width1 = int(cap1.get(cv2.CAP_PROP_FRAME_WIDTH))
    height1 = int(cap1.get(cv2.CAP_PROP_FRAME_HEIGHT))
    width2 = int(cap2.get(cv2.CAP_PROP_FRAME_WIDTH))
    height2 = int(cap2.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, min(fps1, fps2), (width1 + width2, max(height1, height2)))
    while True:
        ret1, frame1 = cap1.read()
        ret2, frame2 = cap2.read()
        if not ret1 and (not ret2):
            break
        if not ret1:
            frame1 = 255 * np.ones((height1, width1, 3), dtype=np.uint8)
        if not ret2:
            frame2 = 255 * np.ones((height2, width2, 3), dtype=np.uint8)
        if height1 != height2:
            frame1 = cv2.resize(frame1, (width1, height2))
            frame2 = cv2.resize(frame2, (width2, height2))
        merged_frame = cv2.hconcat([frame1, frame2])
        out.write(merged_frame)
    cap1.release()
    cap2.release()
    out.release()

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

def read_mask(mpath):
    masks = []
    mnames = os.listdir(mpath)
    mnames.sort()
    for m in mnames:
        m = Image.open(os.path.join(mpath, m))
        m = np.array(m.convert('L'))
        m = np.array(m > 0).astype(np.uint8)
        m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3)), iterations=4)
        masks.append(Image.fromarray(m * 255))
    return masks

def read_frame_from_videos(vname):
    frames = []
    vidcap = cv2.VideoCapture(vname)
    success, image = vidcap.read()
    count = 0
    while success:
        image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        frames.append(image)
        success, image = vidcap.read()
        count += 1
    return frames

def build_sttn_model(ckpt_p, model_type='sttn', device='cuda'):
    net = importlib.import_module(f'model.{model_type}')
    model = net.InpaintGenerator().to(device)
    data = torch.load(ckpt_p, map_location=device)
    model.load_state_dict(data['netG'])
    model.eval()
    return model

@torch.no_grad()
def inpaint_video_with_builded_sttn(model, frames: List[Image.Image], masks: List[Image.Image], device='cuda') -> List[Image.Image]:
    w, h = (432, 240)
    neighbor_stride = 5
    video_length = len(frames)
    feats = [frame.resize((w, h)) for frame in frames]
    feats = _to_tensors(feats).unsqueeze(0) * 2 - 1
    _masks = [mask.resize((w, h), Image.NEAREST) for mask in masks]
    _masks = _to_tensors(_masks).unsqueeze(0)
    feats, _masks = (feats.to(device), _masks.to(device))
    comp_frames = [None] * video_length
    feats = (feats * (1 - _masks).float()).view(video_length, 3, h, w)
    feats = model.encoder(feats)
    _, c, feat_h, feat_w = feats.size()
    feats = feats.view(1, video_length, c, feat_h, feat_w)
    for f in range(0, video_length, neighbor_stride):
        neighbor_ids = list(range(max(0, f - neighbor_stride), min(video_length, f + neighbor_stride + 1)))
        ref_ids = get_ref_index(neighbor_ids, video_length)
        pred_feat = model.infer(feats[0, neighbor_ids + ref_ids, :, :, :], _masks[0, neighbor_ids + ref_ids, :, :, :])
        pred_img = model.decoder(pred_feat[:len(neighbor_ids), :, :, :])
        pred_img = torch.tanh(pred_img)
        pred_img = (pred_img + 1) / 2
        pred_img = pred_img.permute(0, 2, 3, 1) * 255
        for i in range(len(neighbor_ids)):
            idx = neighbor_ids[i]
            b_mask = _masks.squeeze()[idx].unsqueeze(-1)
            b_mask = (b_mask != 0).int()
            frame = torch.from_numpy(np.array(frames[idx].resize((w, h))))
            frame = frame.to(device)
            img = pred_img[i] * b_mask + frame * (1 - b_mask)
            img = img.cpu().numpy()
            if comp_frames[idx] is None:
                comp_frames[idx] = img
            else:
                comp_frames[idx] = comp_frames[idx] * 0.5 + img * 0.5
    ori_w, ori_h = frames[0].size
    for idx in range(len(frames)):
        frame = np.array(frames[idx])
        b_mask = np.uint8(np.array(masks[idx])[..., np.newaxis] != 0)
        comp_frame = np.uint8(comp_frames[idx])
        comp_frame = Image.fromarray(comp_frame).resize((ori_w, ori_h))
        comp_frame = np.array(comp_frame)
        comp_frame = comp_frame * b_mask + frame * (1 - b_mask)
        comp_frames[idx] = Image.fromarray(np.uint8(comp_frame))
    return comp_frames

@torch.no_grad()
def inpaint_video_with_sttn(video_p, mask_dir, output_dir, ckpt_p, model_type='sttn'):
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = build_sttn_model(ckpt_p, model_type, device)
    frames = read_frame_from_videos(video_p)
    masks = read_mask(mask_dir)
    comp_frames = inpaint_video_with_builded_sttn(model, frames, masks, device)
    video_stem = Path(video_p).stem
    output_p = Path(output_dir) / video_stem / f'removed_w_mask.mp4'
    output_p.parent.mkdir(exist_ok=True, parents=True)
    w, h = frames[0].size
    fps = imageio.v3.immeta(video_p, exclude_applied=False)['fps']
    writer = cv2.VideoWriter(str(output_p), cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
    for idx in range(len(comp_frames)):
        writer.write(cv2.cvtColor(np.uint8(comp_frames[idx]), cv2.COLOR_BGR2RGB))
    writer.release()
    print(output_p)

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

def main_worker(rank, config):
    if 'local_rank' not in config:
        config['local_rank'] = config['global_rank'] = rank
    if config['distributed']:
        torch.cuda.set_device(int(config['local_rank']))
        torch.distributed.init_process_group(backend='nccl', init_method=config['init_method'], world_size=config['world_size'], rank=config['global_rank'], group_name='mtorch')
        print('using GPU {}-{} for training'.format(int(config['global_rank']), int(config['local_rank'])))
    config['save_dir'] = os.path.join(config['save_dir'], '{}_{}'.format(config['model'], os.path.basename(args.config).split('.')[0]))
    if torch.cuda.is_available():
        config['device'] = torch.device('cuda:{}'.format(config['local_rank']))
    else:
        config['device'] = 'cpu'
    if not config['distributed'] or config['global_rank'] == 0:
        os.makedirs(config['save_dir'], exist_ok=True)
        config_path = os.path.join(config['save_dir'], config['config'].split('/')[-1])
        if not os.path.isfile(config_path):
            copyfile(config['config'], config_path)
        print('[**] create folder {}'.format(config['save_dir']))
    trainer = Trainer(config, debug=args.exam)
    trainer.train()

def read_mask(mpath):
    masks = []
    mnames = os.listdir(mpath)
    mnames.sort()
    for m in mnames:
        m = Image.open(os.path.join(mpath, m))
        m = m.resize((w, h), Image.NEAREST)
        m = np.array(m.convert('L'))
        m = np.array(m > 0).astype(np.uint8)
        m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3)), iterations=4)
        masks.append(Image.fromarray(m * 255))
    return masks

def read_frame_from_videos(vname):
    frames = []
    vidcap = cv2.VideoCapture(vname)
    success, image = vidcap.read()
    count = 0
    while success:
        image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        frames.append(image.resize((w, h)))
        success, image = vidcap.read()
        count += 1
    return frames

def main_worker():
    device = torch.device('cuda:1' if torch.cuda.is_available() else 'cpu')
    net = importlib.import_module('model.' + args.model)
    model = net.InpaintGenerator().to(device)
    model_path = args.ckpt
    data = torch.load(args.ckpt, map_location=device)
    model.load_state_dict(data['netG'])
    print('loading from: {}'.format(args.ckpt))
    model.eval()
    frames = read_frame_from_videos(args.video)
    video_length = len(frames)
    feats = _to_tensors(frames).unsqueeze(0) * 2 - 1
    frames = [np.array(f).astype(np.uint8) for f in frames]
    masks = read_mask(args.mask)
    binary_masks = [np.expand_dims((np.array(m) != 0).astype(np.uint8), 2) for m in masks]
    masks = _to_tensors(masks).unsqueeze(0)
    feats, masks = (feats.to(device), masks.to(device))
    comp_frames = [None] * video_length
    with torch.no_grad():
        feats = model.encoder((feats * (1 - masks).float()).view(video_length, 3, h, w))
        _, c, feat_h, feat_w = feats.size()
        feats = feats.view(1, video_length, c, feat_h, feat_w)
    print('loading videos and masks from: {}'.format(args.video))
    for f in range(0, video_length, neighbor_stride):
        neighbor_ids = [i for i in range(max(0, f - neighbor_stride), min(video_length, f + neighbor_stride + 1))]
        ref_ids = get_ref_index(neighbor_ids, video_length)
        with torch.no_grad():
            pred_feat = model.infer(feats[0, neighbor_ids + ref_ids, :, :, :], masks[0, neighbor_ids + ref_ids, :, :, :])
            pred_img = torch.tanh(model.decoder(pred_feat[:len(neighbor_ids), :, :, :])).detach()
            pred_img = (pred_img + 1) / 2
            pred_img = pred_img.cpu().permute(0, 2, 3, 1).numpy() * 255
            for i in range(len(neighbor_ids)):
                idx = neighbor_ids[i]
                img = np.array(pred_img[i]).astype(np.uint8) * binary_masks[idx] + frames[idx] * (1 - binary_masks[idx])
                if comp_frames[idx] is None:
                    comp_frames[idx] = img
                else:
                    comp_frames[idx] = comp_frames[idx].astype(np.float32) * 0.5 + img.astype(np.float32) * 0.5
    writer = cv2.VideoWriter(f'{args.mask}_result.mp4', cv2.VideoWriter_fourcc(*'mp4v'), default_fps, (w, h))
    for f in range(video_length):
        comp = np.array(comp_frames[f]).astype(np.uint8) * binary_masks[f] + frames[f] * (1 - binary_masks[f])
        writer.write(cv2.cvtColor(np.array(comp).astype(np.uint8), cv2.COLOR_BGR2RGB))
    writer.release()
    print('Finish in {}'.format(f'{args.mask}_result.mp4'))

class Dataset(torch.utils.data.Dataset):

    def __init__(self, args: dict, split='train', debug=False):
        self.args = args
        self.split = split
        self.sample_length = args['sample_length']
        self.size = self.w, self.h = (args['w'], args['h'])
        with open(os.path.join(args['data_root'], args['name'], split + '.json'), 'r') as f:
            self.video_dict = json.load(f)
        self.video_names = list(self.video_dict.keys())
        if debug or split != 'train':
            self.video_names = self.video_names[:100]
        self._to_tensors = transforms.Compose([Stack(), ToTorchFormatTensor()])

    def __len__(self):
        return len(self.video_names)

    def __getitem__(self, index):
        try:
            item = self.load_item(index)
        except:
            print('Loading error in video {}'.format(self.video_names[index]))
            item = self.load_item(0)
        return item

    def load_item(self, index):
        video_name = self.video_names[index]
        all_frames = [f'{str(i).zfill(5)}.jpg' for i in range(self.video_dict[video_name])]
        all_masks = create_random_shape_with_random_motion(len(all_frames), imageHeight=self.h, imageWidth=self.w)
        ref_index = get_ref_index(len(all_frames), self.sample_length)
        frames = []
        masks = []
        for idx in ref_index:
            img = ZipReader.imread('{}/{}/JPEGImages/{}.zip'.format(self.args['data_root'], self.args['name'], video_name), all_frames[idx]).convert('RGB')
            img = img.resize(self.size)
            frames.append(img)
            masks.append(all_masks[idx])
        if self.split == 'train':
            frames = GroupRandomHorizontalFlip()(frames)
        frame_tensors = self._to_tensors(frames) * 2.0 - 1.0
        mask_tensors = self._to_tensors(masks)
        return (frame_tensors, mask_tensors)

def __init__(self, args: dict, split='train', debug=False):
    self.args = args
    self.split = split
    self.sample_length = args['sample_length']
    self.size = self.w, self.h = (args['w'], args['h'])
    with open(os.path.join(args['data_root'], args['name'], split + '.json'), 'r') as f:
        self.video_dict = json.load(f)
    self.video_names = list(self.video_dict.keys())
    if debug or split != 'train':
        self.video_names = self.video_names[:100]
    self._to_tensors = transforms.Compose([Stack(), ToTorchFormatTensor()])

def __len__(self):
    return len(self.video_names)

def __getitem__(self, index):
    try:
        item = self.load_item(index)
    except:
        print('Loading error in video {}'.format(self.video_names[index]))
        item = self.load_item(0)
    return item

def load_item(self, index):
    video_name = self.video_names[index]
    all_frames = [f'{str(i).zfill(5)}.jpg' for i in range(self.video_dict[video_name])]
    all_masks = create_random_shape_with_random_motion(len(all_frames), imageHeight=self.h, imageWidth=self.w)
    ref_index = get_ref_index(len(all_frames), self.sample_length)
    frames = []
    masks = []
    for idx in ref_index:
        img = ZipReader.imread('{}/{}/JPEGImages/{}.zip'.format(self.args['data_root'], self.args['name'], video_name), all_frames[idx]).convert('RGB')
        img = img.resize(self.size)
        frames.append(img)
        masks.append(all_masks[idx])
    if self.split == 'train':
        frames = GroupRandomHorizontalFlip()(frames)
    frame_tensors = self._to_tensors(frames) * 2.0 - 1.0
    mask_tensors = self._to_tensors(masks)
    return (frame_tensors, mask_tensors)

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

def write_masks_to_folder(masks: List[Dict[str, Any]], path: str) -> None:
    header = 'id,area,bbox_x0,bbox_y0,bbox_w,bbox_h,point_input_x,point_input_y,predicted_iou,stability_score,crop_box_x0,crop_box_y0,crop_box_w,crop_box_h'
    metadata = [header]
    for i, mask_data in enumerate(masks):
        mask = mask_data['segmentation']
        filename = f'{i}.png'
        cv2.imwrite(os.path.join(path, filename), mask * 255)
        mask_metadata = [str(i), str(mask_data['area']), *[str(x) for x in mask_data['bbox']], *[str(x) for x in mask_data['point_coords'][0]], str(mask_data['predicted_iou']), str(mask_data['stability_score']), *[str(x) for x in mask_data['crop_box']]]
        row = ','.join(mask_metadata)
        metadata.append(row)
    metadata_path = os.path.join(path, 'metadata.csv')
    with open(metadata_path, 'w') as f:
        f.write('\n'.join(metadata))
    return

def main(args: argparse.Namespace) -> None:
    print('Loading model...')
    sam = sam_model_registry[args.model_type](checkpoint=args.checkpoint)
    _ = sam.to(device=args.device)
    output_mode = 'coco_rle' if args.convert_to_rle else 'binary_mask'
    amg_kwargs = get_amg_kwargs(args)
    generator = SamAutomaticMaskGenerator(sam, output_mode=output_mode, **amg_kwargs)
    if not os.path.isdir(args.input):
        targets = [args.input]
    else:
        targets = [f for f in os.listdir(args.input) if not os.path.isdir(os.path.join(args.input, f))]
        targets = [os.path.join(args.input, f) for f in targets]
    os.makedirs(args.output, exist_ok=True)
    for t in targets:
        print(f"Processing '{t}'...")
        image = cv2.imread(t)
        if image is None:
            print(f"Could not load '{t}' as an image, skipping...")
            continue
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        masks = generator.generate(image)
        base = os.path.basename(t)
        base = os.path.splitext(base)[0]
        save_base = os.path.join(args.output, base)
        if output_mode == 'binary_mask':
            os.makedirs(save_base, exist_ok=False)
            write_masks_to_folder(masks, save_base)
        else:
            save_file = save_base + '.json'
            with open(save_file, 'w') as f:
                json.dump(masks, f)
    print('Done!')

def get_inpainted_img(img, mask0, mask1, mask2):
    lama_config = args.lama_config
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    out = []
    for mask in [mask0, mask1, mask2]:
        if len(mask.shape) == 3:
            mask = mask[:, :, 0]
        img_inpainted = inpaint_img_with_builded_lama(model['lama'], img, mask, lama_config, device=device)
        out.append(img_inpainted)
    return out

def video2frames(video_path, frame_path):
    video = cv2.VideoCapture(video_path)
    os.makedirs(frame_path, exist_ok=True)
    frame_num = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = video.get(cv2.CAP_PROP_FPS)
    initial_img = None
    for idx in tqdm(range(frame_num), 'Extract frames'):
        success, image = video.read()
        if idx == 0:
            initial_img = image.copy()
        assert success, 'extract the {}th frame in video {} failed!'.format(idx, video_path)
        cv2.imwrite('{}/{:05d}.jpg'.format(frame_path, idx), image)
    return (fps, initial_img)

def load_img_to_array(img_p):
    img = Image.open(img_p)
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    return np.array(img)

def save_array_to_img(img_arr, img_p):
    Image.fromarray(img_arr.astype(np.uint8)).save(img_p)

def get_clicked_point(img_path):
    img = cv2.imread(img_path)
    cv2.namedWindow('image')
    cv2.imshow('image', img)
    last_point = []
    keep_looping = True

    def mouse_callback(event, x, y, flags, param):
        nonlocal last_point, keep_looping, img
        if event == cv2.EVENT_LBUTTONDOWN:
            if last_point:
                cv2.circle(img, tuple(last_point), 5, (0, 0, 0), -1)
            last_point = [x, y]
            cv2.circle(img, tuple(last_point), 5, (0, 0, 255), -1)
            cv2.imshow('image', img)
        elif event == cv2.EVENT_RBUTTONDOWN:
            keep_looping = False
    cv2.setMouseCallback('image', mouse_callback)
    while keep_looping:
        cv2.waitKey(1)
    cv2.destroyAllWindows()
    return last_point

def frames2video(frames_list, video_path, fps=30, remove_tmp=False):
    if isinstance(frames_list, str):
        frames_list = glob(f'{frames_list}/*.jpg')
    video_dir = os.path.dirname(video_path)
    if not os.path.exists(video_dir):
        os.makedirs(video_dir)
    writer = imageio.get_writer(video_dir, fps=fps, plugin='ffmpeg')
    for frame in tqdm(frames_list, 'Export video'):
        if isinstance(frame, str):
            frame = imageio.imread(frame)
        else:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = imageio.core.util.Array(frame)
        writer.append_data(frame)
    writer.close()
    print(f'find video at {video_path}.')
    if remove_tmp and isinstance(frames_list, str):
        shutil.rmtree(frames_list)

def write_frames(frame_path, fps, size, codec='libx264', quality=8):
    for filename in sorted(os.listdir(frame_path)):
        if not filename.endswith('.jpg'):
            continue
        yield imageio.imread(os.path.join(frame_path, filename))

def frames2video(frame_path, video_path, fps, show_progress=False, codec='libx264', quality=8):
    sample_frame = imageio.imread(os.path.join(frame_path, os.listdir(frame_path)[0]))
    height, width, _ = sample_frame.shape
    size = (width, height)
    video_dir = os.path.dirname(video_path)
    if not os.path.exists(video_dir):
        os.makedirs(video_dir)
    writer = imageio.get_writer(video_path, fps=fps, codec=codec, quality=quality)
    for frame in write_frames(frame_path, fps=fps, size=size, codec=codec, quality=quality):
        writer.append_data(frame)
        if show_progress:
            print(f'Frame {writer.get_length()} written')
    writer.close()

def click_event(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        print('Point coordinates ({}, {})'.format(x, y))

def main(args):
    dataset = InpaintingDataset(args.datadir, img_suffix='.png')
    area_bins = np.linspace(0, 1, args.area_bins + 1)
    heights = []
    widths = []
    image_areas = []
    hole_areas = []
    hole_area_percents = []
    area_bins_count = np.zeros(args.area_bins)
    area_bin_titles = [f'{area_bins[i] * 100:.0f}-{area_bins[i + 1] * 100:.0f}' for i in range(args.area_bins)]
    bin2i = [[] for _ in range(args.area_bins)]
    for i, item in enumerate(tqdm.tqdm(dataset)):
        h, w = item['image'].shape[1:]
        heights.append(h)
        widths.append(w)
        full_area = h * w
        image_areas.append(full_area)
        hole_area = (item['mask'] == 1).sum()
        hole_areas.append(hole_area)
        hole_percent = hole_area / full_area
        hole_area_percents.append(hole_percent)
        bin_i = np.clip(np.searchsorted(area_bins, hole_percent) - 1, 0, len(area_bins_count) - 1)
        area_bins_count[bin_i] += 1
        bin2i[bin_i].append(i)
    os.makedirs(args.outdir, exist_ok=True)
    for bin_i in range(args.area_bins):
        bindir = os.path.join(args.outdir, area_bin_titles[bin_i])
        os.makedirs(bindir, exist_ok=True)
        bin_idx = bin2i[bin_i]
        for sample_i in np.random.choice(bin_idx, size=min(len(bin_idx), args.samples_n), replace=False):
            item = dataset[sample_i]
            path = os.path.join(bindir, dataset.img_filenames[sample_i].split('/')[-1])
            save_masked_img_for_sidebyside(item, path)

def main(args):
    if not args.indir.endswith('/'):
        args.indir += '/'
    os.makedirs(args.outdir, exist_ok=True)
    src_images = [args.indir + fname for fname in os.listdir(args.indir)]
    tgt_masks = [args.outdir + fname[:-4] + f'_mask000.png' for fname in os.listdir(args.indir)]
    for img_name, msk_name in zip(src_images, tgt_masks):
        image = Image.open(img_name).convert('RGB')
        image = np.transpose(np.array(image), (2, 0, 1))
        mask = (image == 255).astype(int)
        print(mask.dtype, mask.shape)
        Image.fromarray(np.clip(mask[0, :, :] * 255, 0, 255).astype('uint8'), mode='L').save(msk_name)
    "\n    for infile in src_images:\n        try:\n            file_relpath = infile[len(indir):]\n            img_outpath = os.path.join(outdir, file_relpath)\n            os.makedirs(os.path.dirname(img_outpath), exist_ok=True)\n\n            image = Image.open(infile).convert('RGB')\n\n            mask = \n\n            Image.fromarray(\n                np.clip(\n                    cur_mask * 255, 0, 255).astype('uint8'),\n                    mode='L'\n                ).save(cur_basename + f'_mask{i:03d}.png')\n    "

@handle_ddp_subprocess()
@hydra.main(config_path='../configs/training', config_name='tiny_test.yaml')
def main(config: OmegaConf):
    try:
        need_set_deterministic = handle_deterministic_config(config)
        register_debug_signal_handlers()
        is_in_ddp_subprocess = handle_ddp_parent_process()
        config.visualizer.outdir = os.path.join(os.getcwd(), config.visualizer.outdir)
        if not is_in_ddp_subprocess:
            LOGGER.info(OmegaConf.to_yaml(config))
            OmegaConf.save(config, os.path.join(os.getcwd(), 'config.yaml'))
        checkpoints_dir = os.path.join(os.getcwd(), 'models')
        os.makedirs(checkpoints_dir, exist_ok=True)
        metrics_logger = TensorBoardLogger(config.location.tb_dir, name=os.path.basename(os.getcwd()))
        metrics_logger.log_hyperparams(config)
        training_model = make_training_model(config)
        trainer_kwargs = OmegaConf.to_container(config.trainer.kwargs, resolve=True)
        if need_set_deterministic:
            trainer_kwargs['deterministic'] = True
        trainer = Trainer(callbacks=ModelCheckpoint(dirpath=checkpoints_dir, **config.trainer.checkpoint_kwargs), logger=metrics_logger, default_root_dir=os.getcwd(), **trainer_kwargs)
        trainer.fit(training_model)
    except KeyboardInterrupt:
        LOGGER.warning('Interrupted by user')
    except Exception as ex:
        LOGGER.critical(f'Training failed due to {ex}:\n{traceback.format_exc()}')
        sys.exit(1)

def main(args):
    input_dataset = wds.Dataset(args.infile)
    output_dataset = wds.ShardWriter(args.outpattern)
    for rec in tqdm.tqdm(input_dataset):
        output_dataset.write(rec)

@hydra.main(config_path='../configs/prediction', config_name='default.yaml')
def main(predict_config: OmegaConf):
    register_debug_signal_handlers()
    train_config_path = os.path.join(predict_config.model.path, 'config.yaml')
    with open(train_config_path, 'r') as f:
        train_config = OmegaConf.create(yaml.safe_load(f))
    train_config.training_model.predict_only = True
    train_config.visualizer.kind = 'noop'
    checkpoint_path = os.path.join(predict_config.model.path, 'models', predict_config.model.checkpoint)
    model = load_checkpoint(train_config, checkpoint_path, strict=False, map_location='cpu')
    model.eval()
    jit_model_wrapper = JITWrapper(model)
    image = torch.rand(1, 3, 120, 120)
    mask = torch.rand(1, 1, 120, 120)
    output = jit_model_wrapper(image, mask)
    if torch.cuda.is_available():
        device = torch.device('cuda')
    else:
        device = torch.device('cpu')
    image = image.to(device)
    mask = mask.to(device)
    traced_model = torch.jit.trace(jit_model_wrapper, (image, mask), strict=False).to(device)
    save_path = Path(predict_config.save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    print(f'Saving big-lama.pt model to {save_path}')
    traced_model.save(save_path)
    print(f'Checking jit model output...')
    jit_model = torch.jit.load(str(save_path))
    jit_output = jit_model(image, mask)
    diff = (output - jit_output).abs().sum()
    print(f'diff: {diff}')

def main(args):
    checkpoint_fnames = get_checkpoint_files(args.epochs)
    if isinstance(checkpoint_fnames, str):
        checkpoint_fnames = [checkpoint_fnames]
    assert len(checkpoint_fnames) >= 1
    checkpoint_path = os.path.join(args.indir, 'models', checkpoint_fnames[0])
    checkpoint = torch.load(checkpoint_path, map_location='cpu')
    del checkpoint['optimizer_states']
    if len(checkpoint_fnames) > 1:
        for fname in checkpoint_fnames[1:]:
            print('sum', fname)
            sum_tensors_cnt = 0
            other_cp = torch.load(os.path.join(args.indir, 'models', fname), map_location='cpu')
            for k in checkpoint['state_dict'].keys():
                if checkpoint['state_dict'][k].dtype is torch.float:
                    checkpoint['state_dict'][k].data.add_(other_cp['state_dict'][k].data)
                    sum_tensors_cnt += 1
            print('summed', sum_tensors_cnt, 'tensors')
        for k in checkpoint['state_dict'].keys():
            if checkpoint['state_dict'][k].dtype is torch.float:
                checkpoint['state_dict'][k].data.mul_(1 / float(len(checkpoint_fnames)))
    state_dict = checkpoint['state_dict']
    if not args.leave_discriminators:
        for k in list(state_dict.keys()):
            if k.startswith('discriminator.'):
                del state_dict[k]
    if not args.leave_losses:
        for k in list(state_dict.keys()):
            if k.startswith('loss_'):
                del state_dict[k]
    out_checkpoint_path = os.path.join(args.outdir, 'models', 'best.ckpt')
    os.makedirs(os.path.dirname(out_checkpoint_path), exist_ok=True)
    torch.save(checkpoint, out_checkpoint_path)
    shutil.copy2(os.path.join(args.indir, 'config.yaml'), os.path.join(args.outdir, 'config.yaml'))

class SimpleImageDataset(Dataset):

    def __init__(self, root_dir, image_size=(400, 600)):
        self.root_dir = root_dir
        self.files = sorted(os.listdir(root_dir))
        self.image_size = image_size

    def __getitem__(self, index):
        img_name = os.path.join(self.root_dir, self.files[index])
        image = io.imread(img_name)
        image = resize(image, self.image_size, anti_aliasing=True)
        image = torch.FloatTensor(image).permute(2, 0, 1)
        return image

    def __len__(self):
        return len(self.files)

def __init__(self, root_dir, image_size=(400, 600)):
    self.root_dir = root_dir
    self.files = sorted(os.listdir(root_dir))
    self.image_size = image_size

def __getitem__(self, index):
    img_name = os.path.join(self.root_dir, self.files[index])
    image = io.imread(img_name)
    image = resize(image, self.image_size, anti_aliasing=True)
    image = torch.FloatTensor(image).permute(2, 0, 1)
    return image

def __len__(self):
    return len(self.files)

class SimpleImageSquareMaskDataset(Dataset):

    def __init__(self, dataset):
        self.dataset = dataset
        self.mask = torch.FloatTensor(create_rectangle_mask(*self.dataset.image_size))
        self.model = Model()

    def __getitem__(self, index):
        img = self.dataset[index]
        mask = self.mask.clone()
        inpainted = self.model(img[None, ...], mask[None, ...])
        return dict(image=img, mask=mask, inpainted=inpainted)

    def __len__(self):
        return len(self.dataset)

def __len__(self):
    return len(self.dataset)

@hydra.main(config_path='../configs/data_gen/whydra', config_name='random_medium_256.yaml')
def main(config: OmegaConf):
    if not config.indir.endswith('/'):
        config.indir += '/'
    os.makedirs(config.outdir, exist_ok=True)
    in_files = list(glob.glob(os.path.join(config.indir, '**', f'*.{config.location.extension}'), recursive=True))
    if config.n_jobs == 0:
        process_images(in_files, config.indir, config.outdir, config)
    else:
        in_files_n = len(in_files)
        chunk_size = in_files_n // config.n_jobs + (1 if in_files_n % config.n_jobs > 0 else 0)
        Parallel(n_jobs=config.n_jobs)((delayed(process_images)(in_files[start:start + chunk_size], config.indir, config.outdir, config) for start in range(0, len(in_files), chunk_size)))

def generate_masks_for_img(infile, outmask_pattern, mask_size=200, step=0.5):
    inimg = Image.open(infile)
    width, height = inimg.size
    step_abs = int(mask_size * step)
    mask = np.zeros((height, width), dtype='uint8')
    mask_i = 0
    for start_vertical in range(0, height - step_abs, step_abs):
        for start_horizontal in range(0, width - step_abs, step_abs):
            mask[start_vertical:start_vertical + mask_size, start_horizontal:start_horizontal + mask_size] = 255
            cv2.imwrite(outmask_pattern.format(mask_i), mask)
            mask[start_vertical:start_vertical + mask_size, start_horizontal:start_horizontal + mask_size] = 0
            mask_i += 1

def main(args):
    if not args.indir.endswith('/'):
        args.indir += '/'
    if not args.outdir.endswith('/'):
        args.outdir += '/'
    config = load_yaml(args.config)
    in_files = list(glob.glob(os.path.join(args.indir, '**', f'*{config.img_ext}'), recursive=True))
    for infile in tqdm.tqdm(in_files):
        outimg = args.outdir + infile[len(args.indir):]
        outmask_pattern = outimg[:-len(config.img_ext)] + '_mask{:04d}.png'
        os.makedirs(os.path.dirname(outimg), exist_ok=True)
        shutil.copy2(infile, outimg)
        generate_masks_for_img(infile, outmask_pattern, **config.gen_kwargs)

def main(args):
    os.makedirs(args.outdir, exist_ok=True)
    ignored_events = set()
    for orig_fname in glob.glob(args.inglob):
        cur_dirpath = os.path.dirname(orig_fname)
        subdirname = os.path.basename(cur_dirpath)
        exp_root_path = os.path.dirname(cur_dirpath)
        exp_name = os.path.basename(exp_root_path)
        writers_by_group = {}
        for e in tf.compat.v1.train.summary_iterator(orig_fname):
            for v in e.summary.value:
                if need_drop(v.tag):
                    continue
                cur_group, cur_title = get_group_and_title(v.tag)
                if cur_group is None:
                    if v.tag not in ignored_events:
                        print(f'WARNING: Could not detect group for {v.tag}, ignoring it')
                        ignored_events.add(v.tag)
                    continue
                cur_writer = writers_by_group.get(cur_group, None)
                if cur_writer is None:
                    if args.include_version:
                        cur_outdir = os.path.join(args.outdir, exp_name, f'{subdirname}_{cur_group}')
                    else:
                        cur_outdir = os.path.join(args.outdir, exp_name, cur_group)
                    cur_writer = SummaryWriter(cur_outdir)
                    writers_by_group[cur_group] = cur_writer
                cur_writer.add_scalar(cur_title, v.simple_value, global_step=e.step, walltime=e.wall_time)

def main(args):
    if not args.indir.endswith('/'):
        args.indir += '/'
    os.makedirs(args.outdir, exist_ok=True)
    config = load_yaml(args.config)
    in_files = list(glob.glob(os.path.join(args.indir, '**', f'*.{args.ext}'), recursive=True))
    if args.n_jobs == 0:
        process_images(in_files, args.indir, args.outdir, config)
    else:
        in_files_n = len(in_files)
        chunk_size = in_files_n // args.n_jobs + (1 if in_files_n % args.n_jobs > 0 else 0)
        Parallel(n_jobs=args.n_jobs)((delayed(process_images)(in_files[start:start + chunk_size], args.indir, args.outdir, config) for start in range(0, len(in_files), chunk_size)))

def main(args):
    dataset = InpaintingDataset(args.datadir, img_suffix='.png')
    area_bins = np.linspace(0, 1, args.area_bins + 1)
    heights = []
    widths = []
    image_areas = []
    hole_areas = []
    hole_area_percents = []
    known_pixel_distances = []
    area_bins_count = np.zeros(args.area_bins)
    area_bin_titles = [f'{area_bins[i] * 100:.0f}-{area_bins[i + 1] * 100:.0f}' for i in range(args.area_bins)]
    bin2i = [[] for _ in range(args.area_bins)]
    for i, item in enumerate(tqdm.tqdm(dataset)):
        h, w = item['image'].shape[1:]
        heights.append(h)
        widths.append(w)
        full_area = h * w
        image_areas.append(full_area)
        bin_mask = item['mask'] > 0.5
        hole_area = bin_mask.sum()
        hole_areas.append(hole_area)
        hole_percent = hole_area / full_area
        hole_area_percents.append(hole_percent)
        bin_i = np.clip(np.searchsorted(area_bins, hole_percent) - 1, 0, len(area_bins_count) - 1)
        area_bins_count[bin_i] += 1
        bin2i[bin_i].append(i)
        cur_dist = distance_transform_edt(bin_mask)
        cur_dist_inside_mask = cur_dist[bin_mask]
        known_pixel_distances.append(cur_dist_inside_mask.mean())
    os.makedirs(args.outdir, exist_ok=True)
    with open(os.path.join(args.outdir, 'summary.txt'), 'w') as f:
        f.write(f'Location:          {args.datadir}\n\nNumber of samples: {len(dataset)}\n\nImage height: min {min(heights):5d} max {max(heights):5d} mean {np.mean(heights):.2f}\nImage width:  min {min(widths):5d} max {max(widths):5d} mean {np.mean(widths):.2f}\nImage area:   min {min(image_areas):7d} max {max(image_areas):7d} mean {np.mean(image_areas):.2f}\nHole area:    min {min(hole_areas):7d} max {max(hole_areas):7d} mean {np.mean(hole_areas):.2f}\nHole area %:  min {min(hole_area_percents) * 100:2.2f} max {max(hole_area_percents) * 100:2.2f} mean {np.mean(hole_area_percents) * 100:2.2f}\nDist 2known:  min {min(known_pixel_distances):2.2f} max {max(known_pixel_distances):2.2f} mean {np.mean(known_pixel_distances):2.2f} median {np.median(known_pixel_distances):2.2f}\n\nStats by hole area %:\n')
        for bin_i in range(args.area_bins):
            f.write(f'{area_bin_titles[bin_i]}%: samples number {area_bins_count[bin_i]}, {area_bins_count[bin_i] / len(dataset) * 100:.1f}%\n')
    for bin_i in range(args.area_bins):
        bindir = os.path.join(args.outdir, 'samples', area_bin_titles[bin_i])
        os.makedirs(bindir, exist_ok=True)
        bin_idx = bin2i[bin_i]
        for sample_i in np.random.choice(bin_idx, size=min(len(bin_idx), args.samples_n), replace=False):
            save_item_for_vis(dataset[sample_i], os.path.join(bindir, f'{sample_i}.png'))

def average_dicts(dict_list):
    result = {}
    norm = 0.001
    for dct in dict_list:
        sum_dict_with_prefix(result, dct, '')
        norm += 1
    for k in list(result):
        result[k] /= norm
    return result

class LadderRamp:

    def __init__(self, start_iters, values):
        self.start_iters = start_iters
        self.values = values
        assert len(values) == len(start_iters) + 1, (len(values), len(start_iters))

    def __call__(self, i):
        segment_i = bisect.bisect_right(self.start_iters, i)
        return self.values[segment_i]

def __init__(self, start_iters, values):
    self.start_iters = start_iters
    self.values = values
    assert len(values) == len(start_iters) + 1, (len(values), len(start_iters))

def load_checkpoint(train_config, path, map_location='cuda', strict=True):
    model: torch.nn.Module = make_training_model(train_config)
    state = torch.load(path, map_location=map_location)
    model.load_state_dict(state['state_dict'], strict=strict)
    model.on_load_checkpoint(state)
    return model

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

@property
def num_scales(self):
    return len(self.heads)

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

@property
def num_scales(self):
    return len(self.ms_impl)

class DirectoryVisualizer(BaseVisualizer):
    DEFAULT_KEY_ORDER = 'image predicted_image inpainted'.split(' ')

    def __init__(self, outdir, key_order=DEFAULT_KEY_ORDER, max_items_in_batch=10, last_without_mask=True, rescale_keys=None):
        self.outdir = outdir
        os.makedirs(self.outdir, exist_ok=True)
        self.key_order = key_order
        self.max_items_in_batch = max_items_in_batch
        self.last_without_mask = last_without_mask
        self.rescale_keys = rescale_keys

    def __call__(self, epoch_i, batch_i, batch, suffix='', rank=None):
        check_and_warn_input_range(batch['image'], 0, 1, 'DirectoryVisualizer target image')
        vis_img = visualize_mask_and_images_batch(batch, self.key_order, max_items=self.max_items_in_batch, last_without_mask=self.last_without_mask, rescale_keys=self.rescale_keys)
        vis_img = np.clip(vis_img * 255, 0, 255).astype('uint8')
        curoutdir = os.path.join(self.outdir, f'epoch{epoch_i:04d}{suffix}')
        os.makedirs(curoutdir, exist_ok=True)
        rank_suffix = f'_r{rank}' if rank is not None else ''
        out_fname = os.path.join(curoutdir, f'batch{batch_i:07d}{rank_suffix}.jpg')
        vis_img = cv2.cvtColor(vis_img, cv2.COLOR_RGB2BGR)
        cv2.imwrite(out_fname, vis_img)

def __init__(self, outdir, key_order=DEFAULT_KEY_ORDER, max_items_in_batch=10, last_without_mask=True, rescale_keys=None):
    self.outdir = outdir
    os.makedirs(self.outdir, exist_ok=True)
    self.key_order = key_order
    self.max_items_in_batch = max_items_in_batch
    self.last_without_mask = last_without_mask
    self.rescale_keys = rescale_keys

def load_yaml(path):
    with open(path, 'r') as f:
        return edict(yaml.safe_load(f))

class InpaintingDataset(Dataset):

    def __init__(self, datadir, img_suffix='.jpg', pad_out_to_modulo=None, scale_factor=None):
        self.datadir = datadir
        self.mask_filenames = sorted(list(glob.glob(os.path.join(self.datadir, '**', '*mask*.png'), recursive=True)))
        self.img_filenames = [fname.rsplit('_mask', 1)[0] + img_suffix for fname in self.mask_filenames]
        self.pad_out_to_modulo = pad_out_to_modulo
        self.scale_factor = scale_factor

    def __len__(self):
        return len(self.mask_filenames)

    def __getitem__(self, i):
        image = load_image(self.img_filenames[i], mode='RGB')
        mask = load_image(self.mask_filenames[i], mode='L')
        result = dict(image=image, mask=mask[None, ...])
        if self.scale_factor is not None:
            result['image'] = scale_image(result['image'], self.scale_factor)
            result['mask'] = scale_image(result['mask'], self.scale_factor, interpolation=cv2.INTER_NEAREST)
        if self.pad_out_to_modulo is not None and self.pad_out_to_modulo > 1:
            result['unpad_to_size'] = result['image'].shape[1:]
            result['image'] = pad_img_to_modulo(result['image'], self.pad_out_to_modulo)
            result['mask'] = pad_img_to_modulo(result['mask'], self.pad_out_to_modulo)
        return result

def __init__(self, datadir, img_suffix='.jpg', pad_out_to_modulo=None, scale_factor=None):
    self.datadir = datadir
    self.mask_filenames = sorted(list(glob.glob(os.path.join(self.datadir, '**', '*mask*.png'), recursive=True)))
    self.img_filenames = [fname.rsplit('_mask', 1)[0] + img_suffix for fname in self.mask_filenames]
    self.pad_out_to_modulo = pad_out_to_modulo
    self.scale_factor = scale_factor

def __len__(self):
    return len(self.mask_filenames)

class OurInpaintingDataset(Dataset):

    def __init__(self, datadir, img_suffix='.jpg', pad_out_to_modulo=None, scale_factor=None):
        self.datadir = datadir
        self.mask_filenames = sorted(list(glob.glob(os.path.join(self.datadir, 'mask', '**', '*mask*.png'), recursive=True)))
        self.img_filenames = [os.path.join(self.datadir, 'img', os.path.basename(fname.rsplit('-', 1)[0].rsplit('_', 1)[0]) + '.png') for fname in self.mask_filenames]
        self.pad_out_to_modulo = pad_out_to_modulo
        self.scale_factor = scale_factor

    def __len__(self):
        return len(self.mask_filenames)

    def __getitem__(self, i):
        result = dict(image=load_image(self.img_filenames[i], mode='RGB'), mask=load_image(self.mask_filenames[i], mode='L')[None, ...])
        if self.scale_factor is not None:
            result['image'] = scale_image(result['image'], self.scale_factor)
            result['mask'] = scale_image(result['mask'], self.scale_factor)
        if self.pad_out_to_modulo is not None and self.pad_out_to_modulo > 1:
            result['image'] = pad_img_to_modulo(result['image'], self.pad_out_to_modulo)
            result['mask'] = pad_img_to_modulo(result['mask'], self.pad_out_to_modulo)
        return result

def __init__(self, datadir, img_suffix='.jpg', pad_out_to_modulo=None, scale_factor=None):
    self.datadir = datadir
    self.mask_filenames = sorted(list(glob.glob(os.path.join(self.datadir, 'mask', '**', '*mask*.png'), recursive=True)))
    self.img_filenames = [os.path.join(self.datadir, 'img', os.path.basename(fname.rsplit('-', 1)[0].rsplit('_', 1)[0]) + '.png') for fname in self.mask_filenames]
    self.pad_out_to_modulo = pad_out_to_modulo
    self.scale_factor = scale_factor

def __len__(self):
    return len(self.mask_filenames)

class PrecomputedInpaintingResultsDataset(InpaintingDataset):

    def __init__(self, datadir, predictdir, inpainted_suffix='_inpainted.jpg', **kwargs):
        super().__init__(datadir, **kwargs)
        if not datadir.endswith('/'):
            datadir += '/'
        self.predictdir = predictdir
        self.pred_filenames = [os.path.join(predictdir, os.path.splitext(fname[len(datadir):])[0] + inpainted_suffix) for fname in self.mask_filenames]

    def __getitem__(self, i):
        result = super().__getitem__(i)
        result['inpainted'] = load_image(self.pred_filenames[i])
        if self.pad_out_to_modulo is not None and self.pad_out_to_modulo > 1:
            result['inpainted'] = pad_img_to_modulo(result['inpainted'], self.pad_out_to_modulo)
        return result

def __init__(self, datadir, predictdir, inpainted_suffix='_inpainted.jpg', **kwargs):
    super().__init__(datadir, **kwargs)
    if not datadir.endswith('/'):
        datadir += '/'
    self.predictdir = predictdir
    self.pred_filenames = [os.path.join(predictdir, os.path.splitext(fname[len(datadir):])[0] + inpainted_suffix) for fname in self.mask_filenames]

class OurPrecomputedInpaintingResultsDataset(OurInpaintingDataset):

    def __init__(self, datadir, predictdir, inpainted_suffix='png', **kwargs):
        super().__init__(datadir, **kwargs)
        if not datadir.endswith('/'):
            datadir += '/'
        self.predictdir = predictdir
        self.pred_filenames = [os.path.join(predictdir, os.path.basename(os.path.splitext(fname)[0]) + f'_inpainted.{inpainted_suffix}') for fname in self.mask_filenames]

    def __getitem__(self, i):
        result = super().__getitem__(i)
        result['inpainted'] = self.file_loader(self.pred_filenames[i])
        if self.pad_out_to_modulo is not None and self.pad_out_to_modulo > 1:
            result['inpainted'] = pad_img_to_modulo(result['inpainted'], self.pad_out_to_modulo)
        return result

def __init__(self, datadir, predictdir, inpainted_suffix='png', **kwargs):
    super().__init__(datadir, **kwargs)
    if not datadir.endswith('/'):
        datadir += '/'
    self.predictdir = predictdir
    self.pred_filenames = [os.path.join(predictdir, os.path.basename(os.path.splitext(fname)[0]) + f'_inpainted.{inpainted_suffix}') for fname in self.mask_filenames]

class InpaintingEvalOnlineDataset(Dataset):

    def __init__(self, indir, mask_generator, img_suffix='.jpg', pad_out_to_modulo=None, scale_factor=None, **kwargs):
        self.indir = indir
        self.mask_generator = mask_generator
        self.img_filenames = sorted(list(glob.glob(os.path.join(self.indir, '**', f'*{img_suffix}'), recursive=True)))
        self.pad_out_to_modulo = pad_out_to_modulo
        self.scale_factor = scale_factor

    def __len__(self):
        return len(self.img_filenames)

    def __getitem__(self, i):
        img, raw_image = load_image(self.img_filenames[i], mode='RGB', return_orig=True)
        mask = self.mask_generator(img, raw_image=raw_image)
        result = dict(image=img, mask=mask)
        if self.scale_factor is not None:
            result['image'] = scale_image(result['image'], self.scale_factor)
            result['mask'] = scale_image(result['mask'], self.scale_factor, interpolation=cv2.INTER_NEAREST)
        if self.pad_out_to_modulo is not None and self.pad_out_to_modulo > 1:
            result['image'] = pad_img_to_modulo(result['image'], self.pad_out_to_modulo)
            result['mask'] = pad_img_to_modulo(result['mask'], self.pad_out_to_modulo)
        return result

def __init__(self, indir, mask_generator, img_suffix='.jpg', pad_out_to_modulo=None, scale_factor=None, **kwargs):
    self.indir = indir
    self.mask_generator = mask_generator
    self.img_filenames = sorted(list(glob.glob(os.path.join(self.indir, '**', f'*{img_suffix}'), recursive=True)))
    self.pad_out_to_modulo = pad_out_to_modulo
    self.scale_factor = scale_factor

def __len__(self):
    return len(self.img_filenames)

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

def save_network(self, network, path, network_label, epoch_label):
    save_filename = '%s_net_%s.pth' % (epoch_label, network_label)
    save_path = os.path.join(path, save_filename)
    torch.save(network.state_dict(), save_path)

def load_network(self, network, network_label, epoch_label):
    save_filename = '%s_net_%s.pth' % (epoch_label, network_label)
    save_path = os.path.join(self.save_dir, save_filename)
    print('Loading network from %s' % save_path)
    network.load_state_dict(torch.load(save_path, map_location='cpu'))

def save_done(self, flag=False):
    np.save(os.path.join(self.save_dir, 'done_flag'), flag)
    np.savetxt(os.path.join(self.save_dir, 'done_flag'), [flag], fmt='%i')

class DistModel(BaseModel):

    def name(self):
        return self.model_name

    def initialize(self, model='net-lin', net='alex', colorspace='Lab', pnet_rand=False, pnet_tune=False, model_path=None, use_gpu=True, printNet=False, spatial=False, is_train=False, lr=0.0001, beta1=0.5, version='0.1'):
        """
        INPUTS
            model - ['net-lin'] for linearly calibrated network
                    ['net'] for off-the-shelf network
                    ['L2'] for L2 distance in Lab colorspace
                    ['SSIM'] for ssim in RGB colorspace
            net - ['squeeze','alex','vgg']
            model_path - if None, will look in weights/[NET_NAME].pth
            colorspace - ['Lab','RGB'] colorspace to use for L2 and SSIM
            use_gpu - bool - whether or not to use a GPU
            printNet - bool - whether or not to print network architecture out
            spatial - bool - whether to output an array containing varying distances across spatial dimensions
            spatial_shape - if given, output spatial shape. if None then spatial shape is determined automatically via spatial_factor (see below).
            spatial_factor - if given, specifies upsampling factor relative to the largest spatial extent of a convolutional layer. if None then resized to size of input images.
            spatial_order - spline order of filter for upsampling in spatial mode, by default 1 (bilinear).
            is_train - bool - [True] for training mode
            lr - float - initial learning rate
            beta1 - float - initial momentum term for adam
            version - 0.1 for latest, 0.0 was original (with a bug)
        """
        BaseModel.initialize(self, use_gpu=use_gpu)
        self.model = model
        self.net = net
        self.is_train = is_train
        self.spatial = spatial
        self.model_name = '%s [%s]' % (model, net)
        if self.model == 'net-lin':
            self.net = PNetLin(pnet_rand=pnet_rand, pnet_tune=pnet_tune, pnet_type=net, use_dropout=True, spatial=spatial, version=version, lpips=True)
            kw = dict(map_location='cpu')
            if model_path is None:
                import inspect
                model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'models', 'lpips_models', f'{net}.pth'))
            if not is_train:
                self.net.load_state_dict(torch.load(model_path, **kw), strict=False)
        elif self.model == 'net':
            self.net = PNetLin(pnet_rand=pnet_rand, pnet_type=net, lpips=False)
        elif self.model in ['L2', 'l2']:
            self.net = L2(use_gpu=use_gpu, colorspace=colorspace)
            self.model_name = 'L2'
        elif self.model in ['DSSIM', 'dssim', 'SSIM', 'ssim']:
            self.net = DSSIM(use_gpu=use_gpu, colorspace=colorspace)
            self.model_name = 'SSIM'
        else:
            raise ValueError('Model [%s] not recognized.' % self.model)
        self.trainable_parameters = list(self.net.parameters())
        if self.is_train:
            self.rankLoss = BCERankingLoss()
            self.trainable_parameters += list(self.rankLoss.net.parameters())
            self.lr = lr
            self.old_lr = lr
            self.optimizer_net = torch.optim.Adam(self.trainable_parameters, lr=lr, betas=(beta1, 0.999))
        else:
            self.net.eval()
        if printNet:
            print('---------- Networks initialized -------------')
            print_network(self.net)
            print('-----------------------------------------------')

    def forward(self, in0, in1, retPerLayer=False):
        """ Function computes the distance between image patches in0 and in1
        INPUTS
            in0, in1 - torch.Tensor object of shape Nx3xXxY - image patch scaled to [-1,1]
        OUTPUT
            computed distances between in0 and in1
        """
        return self.net(in0, in1, retPerLayer=retPerLayer)

    def optimize_parameters(self):
        self.forward_train()
        self.optimizer_net.zero_grad()
        self.backward_train()
        self.optimizer_net.step()
        self.clamp_weights()

    def clamp_weights(self):
        for module in self.net.modules():
            if hasattr(module, 'weight') and module.kernel_size == (1, 1):
                module.weight.data = torch.clamp(module.weight.data, min=0)

    def set_input(self, data):
        self.input_ref = data['ref']
        self.input_p0 = data['p0']
        self.input_p1 = data['p1']
        self.input_judge = data['judge']

    def forward_train(self):
        assert False, "We shoud've not get here when using LPIPS as a metric"
        self.d0 = self(self.var_ref, self.var_p0)
        self.d1 = self(self.var_ref, self.var_p1)
        self.acc_r = self.compute_accuracy(self.d0, self.d1, self.input_judge)
        self.var_judge = Variable(1.0 * self.input_judge).view(self.d0.size())
        self.loss_total = self.rankLoss(self.d0, self.d1, self.var_judge * 2.0 - 1.0)
        return self.loss_total

    def backward_train(self):
        torch.mean(self.loss_total).backward()

    def compute_accuracy(self, d0, d1, judge):
        """ d0, d1 are Variables, judge is a Tensor """
        d1_lt_d0 = (d1 < d0).cpu().data.numpy().flatten()
        judge_per = judge.cpu().numpy().flatten()
        return d1_lt_d0 * judge_per + (1 - d1_lt_d0) * (1 - judge_per)

    def get_current_errors(self):
        retDict = OrderedDict([('loss_total', self.loss_total.data.cpu().numpy()), ('acc_r', self.acc_r)])
        for key in retDict.keys():
            retDict[key] = np.mean(retDict[key])
        return retDict

    def get_current_visuals(self):
        zoom_factor = 256 / self.var_ref.data.size()[2]
        ref_img = tensor2im(self.var_ref.data)
        p0_img = tensor2im(self.var_p0.data)
        p1_img = tensor2im(self.var_p1.data)
        ref_img_vis = zoom(ref_img, [zoom_factor, zoom_factor, 1], order=0)
        p0_img_vis = zoom(p0_img, [zoom_factor, zoom_factor, 1], order=0)
        p1_img_vis = zoom(p1_img, [zoom_factor, zoom_factor, 1], order=0)
        return OrderedDict([('ref', ref_img_vis), ('p0', p0_img_vis), ('p1', p1_img_vis)])

    def save(self, path, label):
        if self.use_gpu:
            self.save_network(self.net.module, path, '', label)
        else:
            self.save_network(self.net, path, '', label)
        self.save_network(self.rankLoss.net, path, 'rank', label)

    def update_learning_rate(self, nepoch_decay):
        lrd = self.lr / nepoch_decay
        lr = self.old_lr - lrd
        for param_group in self.optimizer_net.param_groups:
            param_group['lr'] = lr
        print('update lr [%s] decay: %f -> %f' % (type, self.old_lr, lr))
        self.old_lr = lr

def initialize(self, model='net-lin', net='alex', colorspace='Lab', pnet_rand=False, pnet_tune=False, model_path=None, use_gpu=True, printNet=False, spatial=False, is_train=False, lr=0.0001, beta1=0.5, version='0.1'):
    """
        INPUTS
            model - ['net-lin'] for linearly calibrated network
                    ['net'] for off-the-shelf network
                    ['L2'] for L2 distance in Lab colorspace
                    ['SSIM'] for ssim in RGB colorspace
            net - ['squeeze','alex','vgg']
            model_path - if None, will look in weights/[NET_NAME].pth
            colorspace - ['Lab','RGB'] colorspace to use for L2 and SSIM
            use_gpu - bool - whether or not to use a GPU
            printNet - bool - whether or not to print network architecture out
            spatial - bool - whether to output an array containing varying distances across spatial dimensions
            spatial_shape - if given, output spatial shape. if None then spatial shape is determined automatically via spatial_factor (see below).
            spatial_factor - if given, specifies upsampling factor relative to the largest spatial extent of a convolutional layer. if None then resized to size of input images.
            spatial_order - spline order of filter for upsampling in spatial mode, by default 1 (bilinear).
            is_train - bool - [True] for training mode
            lr - float - initial learning rate
            beta1 - float - initial momentum term for adam
            version - 0.1 for latest, 0.0 was original (with a bug)
        """
    BaseModel.initialize(self, use_gpu=use_gpu)
    self.model = model
    self.net = net
    self.is_train = is_train
    self.spatial = spatial
    self.model_name = '%s [%s]' % (model, net)
    if self.model == 'net-lin':
        self.net = PNetLin(pnet_rand=pnet_rand, pnet_tune=pnet_tune, pnet_type=net, use_dropout=True, spatial=spatial, version=version, lpips=True)
        kw = dict(map_location='cpu')
        if model_path is None:
            import inspect
            model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'models', 'lpips_models', f'{net}.pth'))
        if not is_train:
            self.net.load_state_dict(torch.load(model_path, **kw), strict=False)
    elif self.model == 'net':
        self.net = PNetLin(pnet_rand=pnet_rand, pnet_type=net, lpips=False)
    elif self.model in ['L2', 'l2']:
        self.net = L2(use_gpu=use_gpu, colorspace=colorspace)
        self.model_name = 'L2'
    elif self.model in ['DSSIM', 'dssim', 'SSIM', 'ssim']:
        self.net = DSSIM(use_gpu=use_gpu, colorspace=colorspace)
        self.model_name = 'SSIM'
    else:
        raise ValueError('Model [%s] not recognized.' % self.model)
    self.trainable_parameters = list(self.net.parameters())
    if self.is_train:
        self.rankLoss = BCERankingLoss()
        self.trainable_parameters += list(self.rankLoss.net.parameters())
        self.lr = lr
        self.old_lr = lr
        self.optimizer_net = torch.optim.Adam(self.trainable_parameters, lr=lr, betas=(beta1, 0.999))
    else:
        self.net.eval()
    if printNet:
        print('---------- Networks initialized -------------')
        print_network(self.net)
        print('-----------------------------------------------')

def update_learning_rate(self, nepoch_decay):
    lrd = self.lr / nepoch_decay
    lr = self.old_lr - lrd
    for param_group in self.optimizer_net.param_groups:
        param_group['lr'] = lr
    print('update lr [%s] decay: %f -> %f' % (type, self.old_lr, lr))
    self.old_lr = lr

def benchmark():
    filename = sys.argv[1]
    img = Image.open(filename)
    data = np.array(img.getdata(), dtype=np.uint8)
    if len(data.shape) == 1:
        n_channels = 1
        reshape = (img.height, img.width)
    else:
        n_channels = min(data.shape[1], 3)
        data = data[:, :n_channels]
        reshape = (img.height, img.width, n_channels)
    data = data.reshape(reshape).astype(np.uint8)
    methods = [simplest_countless, quick_countless, quick_countless_xor, quickest_countless, stippled_countless, zero_corrected_countless, countless, downsample_with_averaging, downsample_with_max_pooling, ndzoom, striding]
    formats = {1: 'L', 3: 'RGB', 4: 'RGBA'}
    if not os.path.exists('./results'):
        os.mkdir('./results')
    N = 500
    img_size = float(img.width * img.height) / 1024.0 / 1024.0
    print('N = %d, %dx%d (%.2f MPx) %d chan, %s' % (N, img.width, img.height, img_size, n_channels, filename))
    print('Algorithm\tMPx/sec\tMB/sec\tSec')
    for fn in methods:
        print(fn.__name__, end='')
        sys.stdout.flush()
        start = time.time()
        for _ in tqdm(range(N), desc=fn.__name__, disable=True):
            result = fn(data)
        end = time.time()
        print('\r', end='')
        total_time = end - start
        mpx = N * img_size / total_time
        mbytes = N * img_size * n_channels / total_time
        print('%s\t%.3f\t%.3f\t%.2f' % (fn.__name__, mpx, mbytes, total_time))
        outimg = Image.fromarray(np.squeeze(result), formats[n_channels])
        outimg.save('./results/{}.png'.format(fn.__name__, 'PNG'))

def test_countless2d():

    def test_all_cases(fn, test_zero):
        case1 = np.array([[1, 2], [3, 4]]).reshape((2, 2, 1, 1))
        case2 = np.array([[1, 1], [2, 3]]).reshape((2, 2, 1, 1))
        case1z = np.array([[0, 1], [2, 3]]).reshape((2, 2, 1, 1))
        case2z = np.array([[0, 0], [2, 3]]).reshape((2, 2, 1, 1))
        case3 = np.array([[1, 1], [2, 2]]).reshape((2, 2, 1, 1))
        case4 = np.array([[1, 2], [2, 2]]).reshape((2, 2, 1, 1))
        case5 = np.array([[5, 5], [5, 5]]).reshape((2, 2, 1, 1))
        is_255_handled = np.array([[255, 255], [1, 2]], dtype=np.uint8).reshape((2, 2, 1, 1))
        test = lambda case: fn(case)
        if test_zero:
            assert test(case1z) == [[[[3]]]]
            assert test(case2z) == [[[[0]]]]
        else:
            assert test(case1) == [[[[4]]]]
            assert test(case2) == [[[[1]]]]
        assert test(case3) == [[[[1]]]]
        assert test(case4) == [[[[2]]]]
        assert test(case5) == [[[[5]]]]
        assert test(is_255_handled) == [[[[255]]]]
        assert fn(case1).dtype == case1.dtype
    test_all_cases(countless2d.simplest_countless, False)
    test_all_cases(countless2d.quick_countless, False)
    test_all_cases(countless2d.quickest_countless, False)
    test_all_cases(countless2d.stippled_countless, False)
    methods = [countless2d.zero_corrected_countless, countless2d.countless, countless2d.countless_if]
    for fn in methods:
        print(fn.__name__)
        test_all_cases(fn, True)

def test_countless3d():

    def test_all_cases(fn):
        alldifferent = [[[1, 2], [3, 4]], [[5, 6], [7, 8]]]
        allsame = [[[1, 1], [1, 1]], [[1, 1], [1, 1]]]
        assert fn(np.array(alldifferent)) == [[[8]]]
        assert fn(np.array(allsame)) == [[[1]]]
        twosame = deepcopy(alldifferent)
        twosame[1][1][0] = 2
        assert fn(np.array(twosame)) == [[[2]]]
        threemixed = [[[3, 3], [1, 2]], [[2, 4], [4, 3]]]
        assert fn(np.array(threemixed)) == [[[3]]]
        foursame = [[[4, 4], [1, 2]], [[2, 4], [4, 3]]]
        assert fn(np.array(foursame)) == [[[4]]]
        fivesame = [[[5, 4], [5, 5]], [[2, 4], [5, 5]]]
        assert fn(np.array(fivesame)) == [[[5]]]

    def countless3d_generalized(img):
        return countless3d.countless_generalized(img, (2, 2, 2))

    def countless3d_dynamic_generalized(img):
        return countless3d.dynamic_countless_generalized(img, (2, 2, 2))
    methods = [countless3d.countless3d, countless3d.dynamic_countless3d, countless3d_generalized, countless3d_dynamic_generalized]
    for fn in methods:
        test_all_cases(fn)

def pick(elements):
    eq = (elements[i] == elements[i + 1] for i in range(len(elements) - 1))
    anded = reduce(lambda p, q: p & q, eq)
    return elements[0] * anded

def mobilenetv2(pretrained=False, **kwargs):
    """Constructs a MobileNet_V2 model.

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    model = MobileNetV2(n_class=1000, **kwargs)
    if pretrained:
        model.load_state_dict(load_url(model_urls['mobilenetv2']), strict=False)
    return model

class ModelBuilder:

    @staticmethod
    def weights_init(m):
        classname = m.__class__.__name__
        if classname.find('Conv') != -1:
            nn.init.kaiming_normal_(m.weight.data)
        elif classname.find('BatchNorm') != -1:
            m.weight.data.fill_(1.0)
            m.bias.data.fill_(0.0001)

    @staticmethod
    def build_encoder(arch='resnet50dilated', fc_dim=512, weights=''):
        pretrained = True if len(weights) == 0 else False
        arch = arch.lower()
        if arch == 'mobilenetv2dilated':
            orig_mobilenet = mobilenet.__dict__['mobilenetv2'](pretrained=pretrained)
            net_encoder = MobileNetV2Dilated(orig_mobilenet, dilate_scale=8)
        elif arch == 'resnet18':
            orig_resnet = resnet.__dict__['resnet18'](pretrained=pretrained)
            net_encoder = Resnet(orig_resnet)
        elif arch == 'resnet18dilated':
            orig_resnet = resnet.__dict__['resnet18'](pretrained=pretrained)
            net_encoder = ResnetDilated(orig_resnet, dilate_scale=8)
        elif arch == 'resnet50dilated':
            orig_resnet = resnet.__dict__['resnet50'](pretrained=pretrained)
            net_encoder = ResnetDilated(orig_resnet, dilate_scale=8)
        elif arch == 'resnet50':
            orig_resnet = resnet.__dict__['resnet50'](pretrained=pretrained)
            net_encoder = Resnet(orig_resnet)
        else:
            raise Exception('Architecture undefined!')
        if len(weights) > 0:
            print('Loading weights for net_encoder')
            net_encoder.load_state_dict(torch.load(weights, map_location=lambda storage, loc: storage), strict=False)
        return net_encoder

    @staticmethod
    def build_decoder(arch='ppm_deepsup', fc_dim=512, num_class=NUM_CLASS, weights='', use_softmax=False, drop_last_conv=False):
        arch = arch.lower()
        if arch == 'ppm_deepsup':
            net_decoder = PPMDeepsup(num_class=num_class, fc_dim=fc_dim, use_softmax=use_softmax, drop_last_conv=drop_last_conv)
        elif arch == 'c1_deepsup':
            net_decoder = C1DeepSup(num_class=num_class, fc_dim=fc_dim, use_softmax=use_softmax, drop_last_conv=drop_last_conv)
        else:
            raise Exception('Architecture undefined!')
        net_decoder.apply(ModelBuilder.weights_init)
        if len(weights) > 0:
            print('Loading weights for net_decoder')
            net_decoder.load_state_dict(torch.load(weights, map_location=lambda storage, loc: storage), strict=False)
        return net_decoder

    @staticmethod
    def get_decoder(weights_path, arch_encoder, arch_decoder, fc_dim, drop_last_conv, *arts, **kwargs):
        path = os.path.join(weights_path, 'ade20k', f'ade20k-{arch_encoder}-{arch_decoder}/decoder_epoch_20.pth')
        return ModelBuilder.build_decoder(arch=arch_decoder, fc_dim=fc_dim, weights=path, use_softmax=True, drop_last_conv=drop_last_conv)

    @staticmethod
    def get_encoder(weights_path, arch_encoder, arch_decoder, fc_dim, segmentation, *arts, **kwargs):
        if segmentation:
            path = os.path.join(weights_path, 'ade20k', f'ade20k-{arch_encoder}-{arch_decoder}/encoder_epoch_20.pth')
        else:
            path = ''
        return ModelBuilder.build_encoder(arch=arch_encoder, fc_dim=fc_dim, weights=path)

@staticmethod
def build_encoder(arch='resnet50dilated', fc_dim=512, weights=''):
    pretrained = True if len(weights) == 0 else False
    arch = arch.lower()
    if arch == 'mobilenetv2dilated':
        orig_mobilenet = mobilenet.__dict__['mobilenetv2'](pretrained=pretrained)
        net_encoder = MobileNetV2Dilated(orig_mobilenet, dilate_scale=8)
    elif arch == 'resnet18':
        orig_resnet = resnet.__dict__['resnet18'](pretrained=pretrained)
        net_encoder = Resnet(orig_resnet)
    elif arch == 'resnet18dilated':
        orig_resnet = resnet.__dict__['resnet18'](pretrained=pretrained)
        net_encoder = ResnetDilated(orig_resnet, dilate_scale=8)
    elif arch == 'resnet50dilated':
        orig_resnet = resnet.__dict__['resnet50'](pretrained=pretrained)
        net_encoder = ResnetDilated(orig_resnet, dilate_scale=8)
    elif arch == 'resnet50':
        orig_resnet = resnet.__dict__['resnet50'](pretrained=pretrained)
        net_encoder = Resnet(orig_resnet)
    else:
        raise Exception('Architecture undefined!')
    if len(weights) > 0:
        print('Loading weights for net_encoder')
        net_encoder.load_state_dict(torch.load(weights, map_location=lambda storage, loc: storage), strict=False)
    return net_encoder

@staticmethod
def build_decoder(arch='ppm_deepsup', fc_dim=512, num_class=NUM_CLASS, weights='', use_softmax=False, drop_last_conv=False):
    arch = arch.lower()
    if arch == 'ppm_deepsup':
        net_decoder = PPMDeepsup(num_class=num_class, fc_dim=fc_dim, use_softmax=use_softmax, drop_last_conv=drop_last_conv)
    elif arch == 'c1_deepsup':
        net_decoder = C1DeepSup(num_class=num_class, fc_dim=fc_dim, use_softmax=use_softmax, drop_last_conv=drop_last_conv)
    else:
        raise Exception('Architecture undefined!')
    net_decoder.apply(ModelBuilder.weights_init)
    if len(weights) > 0:
        print('Loading weights for net_decoder')
        net_decoder.load_state_dict(torch.load(weights, map_location=lambda storage, loc: storage), strict=False)
    return net_decoder

@staticmethod
def get_decoder(weights_path, arch_encoder, arch_decoder, fc_dim, drop_last_conv, *arts, **kwargs):
    path = os.path.join(weights_path, 'ade20k', f'ade20k-{arch_encoder}-{arch_decoder}/decoder_epoch_20.pth')
    return ModelBuilder.build_decoder(arch=arch_decoder, fc_dim=fc_dim, weights=path, use_softmax=True, drop_last_conv=drop_last_conv)

@staticmethod
def get_encoder(weights_path, arch_encoder, arch_decoder, fc_dim, segmentation, *arts, **kwargs):
    if segmentation:
        path = os.path.join(weights_path, 'ade20k', f'ade20k-{arch_encoder}-{arch_decoder}/encoder_epoch_20.pth')
    else:
        path = ''
    return ModelBuilder.build_encoder(arch=arch_encoder, fc_dim=fc_dim, weights=path)

def load_url(url, model_dir='./pretrained', map_location=None):
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)
    filename = url.split('/')[-1]
    cached_file = os.path.join(model_dir, filename)
    if not os.path.exists(cached_file):
        sys.stderr.write('Downloading: "{}" to {}\n'.format(url, cached_file))
        urlretrieve(url, cached_file)
    return torch.load(cached_file, map_location=map_location)

def resnet50(pretrained=False, **kwargs):
    """Constructs a ResNet-50 model.

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    model = ResNet(Bottleneck, [3, 4, 6, 3], **kwargs)
    if pretrained:
        model.load_state_dict(load_url(model_urls['resnet50']), strict=False)
    return model

def resnet18(pretrained=False, **kwargs):
    """Constructs a ResNet-18 model.
    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    model = ResNet(BasicBlock, [2, 2, 2, 2], **kwargs)
    if pretrained:
        model.load_state_dict(load_url(model_urls['resnet18']))
    return model

class SyncMaster(object):
    """An abstract `SyncMaster` object.

    - During the replication, as the data parallel will trigger an callback of each module, all slave devices should
    call `register(id)` and obtain an `SlavePipe` to communicate with the master.
    - During the forward pass, master device invokes `run_master`, all messages from slave devices will be collected,
    and passed to a registered callback.
    - After receiving the messages, the master device should gather the information and determine to message passed
    back to each slave devices.
    """

    def __init__(self, master_callback):
        """

        Args:
            master_callback: a callback to be invoked after having collected messages from slave devices.
        """
        self._master_callback = master_callback
        self._queue = queue.Queue()
        self._registry = collections.OrderedDict()
        self._activated = False

    def register_slave(self, identifier):
        """
        Register an slave device.

        Args:
            identifier: an identifier, usually is the device id.

        Returns: a `SlavePipe` object which can be used to communicate with the master device.

        """
        if self._activated:
            assert self._queue.empty(), 'Queue is not clean before next initialization.'
            self._activated = False
            self._registry.clear()
        future = FutureResult()
        self._registry[identifier] = _MasterRegistry(future)
        return SlavePipe(identifier, self._queue, future)

    def run_master(self, master_msg):
        """
        Main entry for the master device in each forward pass.
        The messages were first collected from each devices (including the master device), and then
        an callback will be invoked to compute the message to be sent back to each devices
        (including the master device).

        Args:
            master_msg: the message that the master want to send to itself. This will be placed as the first
            message when calling `master_callback`. For detailed usage, see `_SynchronizedBatchNorm` for an example.

        Returns: the message to be sent back to the master device.

        """
        self._activated = True
        intermediates = [(0, master_msg)]
        for i in range(self.nr_slaves):
            intermediates.append(self._queue.get())
        results = self._master_callback(intermediates)
        assert results[0][0] == 0, 'The first result should belongs to the master.'
        for i, res in results:
            if i == 0:
                continue
            self._registry[i].result.put(res)
        for i in range(self.nr_slaves):
            assert self._queue.get() is True
        return results[0][1]

    @property
    def nr_slaves(self):
        return len(self._registry)

@property
def nr_slaves(self):
    return len(self._registry)

def average_dicts(dict_list):
    result = {}
    norm = 0.001
    for dct in dict_list:
        sum_dict_with_prefix(result, dct, '')
        norm += 1
    for k in list(result):
        result[k] /= norm
    return result

class LadderRamp:

    def __init__(self, start_iters, values):
        self.start_iters = start_iters
        self.values = values
        assert len(values) == len(start_iters) + 1, (len(values), len(start_iters))

    def __call__(self, i):
        segment_i = bisect.bisect_right(self.start_iters, i)
        return self.values[segment_i]

def __init__(self, start_iters, values):
    self.start_iters = start_iters
    self.values = values
    assert len(values) == len(start_iters) + 1, (len(values), len(start_iters))

class InpaintingTrainDataset(Dataset):

    def __init__(self, indir, mask_generator, transform):
        self.in_files = list(glob.glob(os.path.join(indir, '**', '*.jpg'), recursive=True))
        self.mask_generator = mask_generator
        self.transform = transform
        self.iter_i = 0

    def __len__(self):
        return len(self.in_files)

    def __getitem__(self, item):
        path = self.in_files[item]
        img = cv2.imread(path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = self.transform(image=img)['image']
        img = np.transpose(img, (2, 0, 1))
        mask = self.mask_generator(img, iter_i=self.iter_i)
        self.iter_i += 1
        return dict(image=img, mask=mask)

def __init__(self, indir, mask_generator, transform):
    self.in_files = list(glob.glob(os.path.join(indir, '**', '*.jpg'), recursive=True))
    self.mask_generator = mask_generator
    self.transform = transform
    self.iter_i = 0

def __len__(self):
    return len(self.in_files)

class ImgSegmentationDataset(Dataset):

    def __init__(self, indir, mask_generator, transform, out_size, segm_indir, semantic_seg_n_classes):
        self.indir = indir
        self.segm_indir = segm_indir
        self.mask_generator = mask_generator
        self.transform = transform
        self.out_size = out_size
        self.semantic_seg_n_classes = semantic_seg_n_classes
        self.in_files = list(glob.glob(os.path.join(indir, '**', '*.jpg'), recursive=True))

    def __len__(self):
        return len(self.in_files)

    def __getitem__(self, item):
        path = self.in_files[item]
        img = cv2.imread(path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (self.out_size, self.out_size))
        img = self.transform(image=img)['image']
        img = np.transpose(img, (2, 0, 1))
        mask = self.mask_generator(img)
        segm, segm_classes = self.load_semantic_segm(path)
        result = dict(image=img, mask=mask, segm=segm, segm_classes=segm_classes)
        return result

    def load_semantic_segm(self, img_path):
        segm_path = img_path.replace(self.indir, self.segm_indir).replace('.jpg', '.png')
        mask = cv2.imread(segm_path, cv2.IMREAD_GRAYSCALE)
        mask = cv2.resize(mask, (self.out_size, self.out_size))
        tensor = torch.from_numpy(np.clip(mask.astype(int) - 1, 0, None))
        ohe = F.one_hot(tensor.long(), num_classes=self.semantic_seg_n_classes)
        return (ohe.permute(2, 0, 1).float(), tensor.unsqueeze(0))

def __init__(self, indir, mask_generator, transform, out_size, segm_indir, semantic_seg_n_classes):
    self.indir = indir
    self.segm_indir = segm_indir
    self.mask_generator = mask_generator
    self.transform = transform
    self.out_size = out_size
    self.semantic_seg_n_classes = semantic_seg_n_classes
    self.in_files = list(glob.glob(os.path.join(indir, '**', '*.jpg'), recursive=True))

def __len__(self):
    return len(self.in_files)

def load_checkpoint(train_config, path, map_location='cuda', strict=True):
    model: torch.nn.Module = make_training_model(train_config)
    state = torch.load(path, map_location=map_location)
    model.load_state_dict(state['state_dict'], strict=strict)
    model.on_load_checkpoint(state)
    return model

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

@property
def num_scales(self):
    return len(self.heads)

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

@property
def num_scales(self):
    return len(self.ms_impl)

class DirectoryVisualizer(BaseVisualizer):
    DEFAULT_KEY_ORDER = 'image predicted_image inpainted'.split(' ')

    def __init__(self, outdir, key_order=DEFAULT_KEY_ORDER, max_items_in_batch=10, last_without_mask=True, rescale_keys=None):
        self.outdir = outdir
        os.makedirs(self.outdir, exist_ok=True)
        self.key_order = key_order
        self.max_items_in_batch = max_items_in_batch
        self.last_without_mask = last_without_mask
        self.rescale_keys = rescale_keys

    def __call__(self, epoch_i, batch_i, batch, suffix='', rank=None):
        check_and_warn_input_range(batch['image'], 0, 1, 'DirectoryVisualizer target image')
        vis_img = visualize_mask_and_images_batch(batch, self.key_order, max_items=self.max_items_in_batch, last_without_mask=self.last_without_mask, rescale_keys=self.rescale_keys)
        vis_img = np.clip(vis_img * 255, 0, 255).astype('uint8')
        curoutdir = os.path.join(self.outdir, f'epoch{epoch_i:04d}{suffix}')
        os.makedirs(curoutdir, exist_ok=True)
        rank_suffix = f'_r{rank}' if rank is not None else ''
        out_fname = os.path.join(curoutdir, f'batch{batch_i:07d}{rank_suffix}.jpg')
        vis_img = cv2.cvtColor(vis_img, cv2.COLOR_RGB2BGR)
        cv2.imwrite(out_fname, vis_img)

def __init__(self, outdir, key_order=DEFAULT_KEY_ORDER, max_items_in_batch=10, last_without_mask=True, rescale_keys=None):
    self.outdir = outdir
    os.makedirs(self.outdir, exist_ok=True)
    self.key_order = key_order
    self.max_items_in_batch = max_items_in_batch
    self.last_without_mask = last_without_mask
    self.rescale_keys = rescale_keys

def load_yaml(path):
    with open(path, 'r') as f:
        return edict(yaml.safe_load(f))

class InpaintingDataset(Dataset):

    def __init__(self, datadir, img_suffix='.jpg', pad_out_to_modulo=None, scale_factor=None):
        self.datadir = datadir
        self.mask_filenames = sorted(list(glob.glob(os.path.join(self.datadir, '**', '*mask*.png'), recursive=True)))
        self.img_filenames = [fname.rsplit('_mask', 1)[0] + img_suffix for fname in self.mask_filenames]
        self.pad_out_to_modulo = pad_out_to_modulo
        self.scale_factor = scale_factor

    def __len__(self):
        return len(self.mask_filenames)

    def __getitem__(self, i):
        image = load_image(self.img_filenames[i], mode='RGB')
        mask = load_image(self.mask_filenames[i], mode='L')
        result = dict(image=image, mask=mask[None, ...])
        if self.scale_factor is not None:
            result['image'] = scale_image(result['image'], self.scale_factor)
            result['mask'] = scale_image(result['mask'], self.scale_factor, interpolation=cv2.INTER_NEAREST)
        if self.pad_out_to_modulo is not None and self.pad_out_to_modulo > 1:
            result['unpad_to_size'] = result['image'].shape[1:]
            result['image'] = pad_img_to_modulo(result['image'], self.pad_out_to_modulo)
            result['mask'] = pad_img_to_modulo(result['mask'], self.pad_out_to_modulo)
        return result

def __init__(self, datadir, img_suffix='.jpg', pad_out_to_modulo=None, scale_factor=None):
    self.datadir = datadir
    self.mask_filenames = sorted(list(glob.glob(os.path.join(self.datadir, '**', '*mask*.png'), recursive=True)))
    self.img_filenames = [fname.rsplit('_mask', 1)[0] + img_suffix for fname in self.mask_filenames]
    self.pad_out_to_modulo = pad_out_to_modulo
    self.scale_factor = scale_factor

def __len__(self):
    return len(self.mask_filenames)

class OurInpaintingDataset(Dataset):

    def __init__(self, datadir, img_suffix='.jpg', pad_out_to_modulo=None, scale_factor=None):
        self.datadir = datadir
        self.mask_filenames = sorted(list(glob.glob(os.path.join(self.datadir, 'mask', '**', '*mask*.png'), recursive=True)))
        self.img_filenames = [os.path.join(self.datadir, 'img', os.path.basename(fname.rsplit('-', 1)[0].rsplit('_', 1)[0]) + '.png') for fname in self.mask_filenames]
        self.pad_out_to_modulo = pad_out_to_modulo
        self.scale_factor = scale_factor

    def __len__(self):
        return len(self.mask_filenames)

    def __getitem__(self, i):
        result = dict(image=load_image(self.img_filenames[i], mode='RGB'), mask=load_image(self.mask_filenames[i], mode='L')[None, ...])
        if self.scale_factor is not None:
            result['image'] = scale_image(result['image'], self.scale_factor)
            result['mask'] = scale_image(result['mask'], self.scale_factor)
        if self.pad_out_to_modulo is not None and self.pad_out_to_modulo > 1:
            result['image'] = pad_img_to_modulo(result['image'], self.pad_out_to_modulo)
            result['mask'] = pad_img_to_modulo(result['mask'], self.pad_out_to_modulo)
        return result

def __init__(self, datadir, img_suffix='.jpg', pad_out_to_modulo=None, scale_factor=None):
    self.datadir = datadir
    self.mask_filenames = sorted(list(glob.glob(os.path.join(self.datadir, 'mask', '**', '*mask*.png'), recursive=True)))
    self.img_filenames = [os.path.join(self.datadir, 'img', os.path.basename(fname.rsplit('-', 1)[0].rsplit('_', 1)[0]) + '.png') for fname in self.mask_filenames]
    self.pad_out_to_modulo = pad_out_to_modulo
    self.scale_factor = scale_factor

def __len__(self):
    return len(self.mask_filenames)

class PrecomputedInpaintingResultsDataset(InpaintingDataset):

    def __init__(self, datadir, predictdir, inpainted_suffix='_inpainted.jpg', **kwargs):
        super().__init__(datadir, **kwargs)
        if not datadir.endswith('/'):
            datadir += '/'
        self.predictdir = predictdir
        self.pred_filenames = [os.path.join(predictdir, os.path.splitext(fname[len(datadir):])[0] + inpainted_suffix) for fname in self.mask_filenames]

    def __getitem__(self, i):
        result = super().__getitem__(i)
        result['inpainted'] = load_image(self.pred_filenames[i])
        if self.pad_out_to_modulo is not None and self.pad_out_to_modulo > 1:
            result['inpainted'] = pad_img_to_modulo(result['inpainted'], self.pad_out_to_modulo)
        return result

def __init__(self, datadir, predictdir, inpainted_suffix='_inpainted.jpg', **kwargs):
    super().__init__(datadir, **kwargs)
    if not datadir.endswith('/'):
        datadir += '/'
    self.predictdir = predictdir
    self.pred_filenames = [os.path.join(predictdir, os.path.splitext(fname[len(datadir):])[0] + inpainted_suffix) for fname in self.mask_filenames]

class OurPrecomputedInpaintingResultsDataset(OurInpaintingDataset):

    def __init__(self, datadir, predictdir, inpainted_suffix='png', **kwargs):
        super().__init__(datadir, **kwargs)
        if not datadir.endswith('/'):
            datadir += '/'
        self.predictdir = predictdir
        self.pred_filenames = [os.path.join(predictdir, os.path.basename(os.path.splitext(fname)[0]) + f'_inpainted.{inpainted_suffix}') for fname in self.mask_filenames]

    def __getitem__(self, i):
        result = super().__getitem__(i)
        result['inpainted'] = self.file_loader(self.pred_filenames[i])
        if self.pad_out_to_modulo is not None and self.pad_out_to_modulo > 1:
            result['inpainted'] = pad_img_to_modulo(result['inpainted'], self.pad_out_to_modulo)
        return result

def __init__(self, datadir, predictdir, inpainted_suffix='png', **kwargs):
    super().__init__(datadir, **kwargs)
    if not datadir.endswith('/'):
        datadir += '/'
    self.predictdir = predictdir
    self.pred_filenames = [os.path.join(predictdir, os.path.basename(os.path.splitext(fname)[0]) + f'_inpainted.{inpainted_suffix}') for fname in self.mask_filenames]

class InpaintingEvalOnlineDataset(Dataset):

    def __init__(self, indir, mask_generator, img_suffix='.jpg', pad_out_to_modulo=None, scale_factor=None, **kwargs):
        self.indir = indir
        self.mask_generator = mask_generator
        self.img_filenames = sorted(list(glob.glob(os.path.join(self.indir, '**', f'*{img_suffix}'), recursive=True)))
        self.pad_out_to_modulo = pad_out_to_modulo
        self.scale_factor = scale_factor

    def __len__(self):
        return len(self.img_filenames)

    def __getitem__(self, i):
        img, raw_image = load_image(self.img_filenames[i], mode='RGB', return_orig=True)
        mask = self.mask_generator(img, raw_image=raw_image)
        result = dict(image=img, mask=mask)
        if self.scale_factor is not None:
            result['image'] = scale_image(result['image'], self.scale_factor)
            result['mask'] = scale_image(result['mask'], self.scale_factor, interpolation=cv2.INTER_NEAREST)
        if self.pad_out_to_modulo is not None and self.pad_out_to_modulo > 1:
            result['image'] = pad_img_to_modulo(result['image'], self.pad_out_to_modulo)
            result['mask'] = pad_img_to_modulo(result['mask'], self.pad_out_to_modulo)
        return result

def __init__(self, indir, mask_generator, img_suffix='.jpg', pad_out_to_modulo=None, scale_factor=None, **kwargs):
    self.indir = indir
    self.mask_generator = mask_generator
    self.img_filenames = sorted(list(glob.glob(os.path.join(self.indir, '**', f'*{img_suffix}'), recursive=True)))
    self.pad_out_to_modulo = pad_out_to_modulo
    self.scale_factor = scale_factor

def __len__(self):
    return len(self.img_filenames)

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

def save_network(self, network, path, network_label, epoch_label):
    save_filename = '%s_net_%s.pth' % (epoch_label, network_label)
    save_path = os.path.join(path, save_filename)
    torch.save(network.state_dict(), save_path)

def load_network(self, network, network_label, epoch_label):
    save_filename = '%s_net_%s.pth' % (epoch_label, network_label)
    save_path = os.path.join(self.save_dir, save_filename)
    print('Loading network from %s' % save_path)
    network.load_state_dict(torch.load(save_path, map_location='cpu'))

def save_done(self, flag=False):
    np.save(os.path.join(self.save_dir, 'done_flag'), flag)
    np.savetxt(os.path.join(self.save_dir, 'done_flag'), [flag], fmt='%i')

class DistModel(BaseModel):

    def name(self):
        return self.model_name

    def initialize(self, model='net-lin', net='alex', colorspace='Lab', pnet_rand=False, pnet_tune=False, model_path=None, use_gpu=True, printNet=False, spatial=False, is_train=False, lr=0.0001, beta1=0.5, version='0.1'):
        """
        INPUTS
            model - ['net-lin'] for linearly calibrated network
                    ['net'] for off-the-shelf network
                    ['L2'] for L2 distance in Lab colorspace
                    ['SSIM'] for ssim in RGB colorspace
            net - ['squeeze','alex','vgg']
            model_path - if None, will look in weights/[NET_NAME].pth
            colorspace - ['Lab','RGB'] colorspace to use for L2 and SSIM
            use_gpu - bool - whether or not to use a GPU
            printNet - bool - whether or not to print network architecture out
            spatial - bool - whether to output an array containing varying distances across spatial dimensions
            spatial_shape - if given, output spatial shape. if None then spatial shape is determined automatically via spatial_factor (see below).
            spatial_factor - if given, specifies upsampling factor relative to the largest spatial extent of a convolutional layer. if None then resized to size of input images.
            spatial_order - spline order of filter for upsampling in spatial mode, by default 1 (bilinear).
            is_train - bool - [True] for training mode
            lr - float - initial learning rate
            beta1 - float - initial momentum term for adam
            version - 0.1 for latest, 0.0 was original (with a bug)
        """
        BaseModel.initialize(self, use_gpu=use_gpu)
        self.model = model
        self.net = net
        self.is_train = is_train
        self.spatial = spatial
        self.model_name = '%s [%s]' % (model, net)
        if self.model == 'net-lin':
            self.net = PNetLin(pnet_rand=pnet_rand, pnet_tune=pnet_tune, pnet_type=net, use_dropout=True, spatial=spatial, version=version, lpips=True)
            kw = dict(map_location='cpu')
            if model_path is None:
                import inspect
                model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'models', 'lpips_models', f'{net}.pth'))
            if not is_train:
                self.net.load_state_dict(torch.load(model_path, **kw), strict=False)
        elif self.model == 'net':
            self.net = PNetLin(pnet_rand=pnet_rand, pnet_type=net, lpips=False)
        elif self.model in ['L2', 'l2']:
            self.net = L2(use_gpu=use_gpu, colorspace=colorspace)
            self.model_name = 'L2'
        elif self.model in ['DSSIM', 'dssim', 'SSIM', 'ssim']:
            self.net = DSSIM(use_gpu=use_gpu, colorspace=colorspace)
            self.model_name = 'SSIM'
        else:
            raise ValueError('Model [%s] not recognized.' % self.model)
        self.trainable_parameters = list(self.net.parameters())
        if self.is_train:
            self.rankLoss = BCERankingLoss()
            self.trainable_parameters += list(self.rankLoss.net.parameters())
            self.lr = lr
            self.old_lr = lr
            self.optimizer_net = torch.optim.Adam(self.trainable_parameters, lr=lr, betas=(beta1, 0.999))
        else:
            self.net.eval()
        if printNet:
            print('---------- Networks initialized -------------')
            print_network(self.net)
            print('-----------------------------------------------')

    def forward(self, in0, in1, retPerLayer=False):
        """ Function computes the distance between image patches in0 and in1
        INPUTS
            in0, in1 - torch.Tensor object of shape Nx3xXxY - image patch scaled to [-1,1]
        OUTPUT
            computed distances between in0 and in1
        """
        return self.net(in0, in1, retPerLayer=retPerLayer)

    def optimize_parameters(self):
        self.forward_train()
        self.optimizer_net.zero_grad()
        self.backward_train()
        self.optimizer_net.step()
        self.clamp_weights()

    def clamp_weights(self):
        for module in self.net.modules():
            if hasattr(module, 'weight') and module.kernel_size == (1, 1):
                module.weight.data = torch.clamp(module.weight.data, min=0)

    def set_input(self, data):
        self.input_ref = data['ref']
        self.input_p0 = data['p0']
        self.input_p1 = data['p1']
        self.input_judge = data['judge']

    def forward_train(self):
        assert False, "We shoud've not get here when using LPIPS as a metric"
        self.d0 = self(self.var_ref, self.var_p0)
        self.d1 = self(self.var_ref, self.var_p1)
        self.acc_r = self.compute_accuracy(self.d0, self.d1, self.input_judge)
        self.var_judge = Variable(1.0 * self.input_judge).view(self.d0.size())
        self.loss_total = self.rankLoss(self.d0, self.d1, self.var_judge * 2.0 - 1.0)
        return self.loss_total

    def backward_train(self):
        torch.mean(self.loss_total).backward()

    def compute_accuracy(self, d0, d1, judge):
        """ d0, d1 are Variables, judge is a Tensor """
        d1_lt_d0 = (d1 < d0).cpu().data.numpy().flatten()
        judge_per = judge.cpu().numpy().flatten()
        return d1_lt_d0 * judge_per + (1 - d1_lt_d0) * (1 - judge_per)

    def get_current_errors(self):
        retDict = OrderedDict([('loss_total', self.loss_total.data.cpu().numpy()), ('acc_r', self.acc_r)])
        for key in retDict.keys():
            retDict[key] = np.mean(retDict[key])
        return retDict

    def get_current_visuals(self):
        zoom_factor = 256 / self.var_ref.data.size()[2]
        ref_img = tensor2im(self.var_ref.data)
        p0_img = tensor2im(self.var_p0.data)
        p1_img = tensor2im(self.var_p1.data)
        ref_img_vis = zoom(ref_img, [zoom_factor, zoom_factor, 1], order=0)
        p0_img_vis = zoom(p0_img, [zoom_factor, zoom_factor, 1], order=0)
        p1_img_vis = zoom(p1_img, [zoom_factor, zoom_factor, 1], order=0)
        return OrderedDict([('ref', ref_img_vis), ('p0', p0_img_vis), ('p1', p1_img_vis)])

    def save(self, path, label):
        if self.use_gpu:
            self.save_network(self.net.module, path, '', label)
        else:
            self.save_network(self.net, path, '', label)
        self.save_network(self.rankLoss.net, path, 'rank', label)

    def update_learning_rate(self, nepoch_decay):
        lrd = self.lr / nepoch_decay
        lr = self.old_lr - lrd
        for param_group in self.optimizer_net.param_groups:
            param_group['lr'] = lr
        print('update lr [%s] decay: %f -> %f' % (type, self.old_lr, lr))
        self.old_lr = lr

def initialize(self, model='net-lin', net='alex', colorspace='Lab', pnet_rand=False, pnet_tune=False, model_path=None, use_gpu=True, printNet=False, spatial=False, is_train=False, lr=0.0001, beta1=0.5, version='0.1'):
    """
        INPUTS
            model - ['net-lin'] for linearly calibrated network
                    ['net'] for off-the-shelf network
                    ['L2'] for L2 distance in Lab colorspace
                    ['SSIM'] for ssim in RGB colorspace
            net - ['squeeze','alex','vgg']
            model_path - if None, will look in weights/[NET_NAME].pth
            colorspace - ['Lab','RGB'] colorspace to use for L2 and SSIM
            use_gpu - bool - whether or not to use a GPU
            printNet - bool - whether or not to print network architecture out
            spatial - bool - whether to output an array containing varying distances across spatial dimensions
            spatial_shape - if given, output spatial shape. if None then spatial shape is determined automatically via spatial_factor (see below).
            spatial_factor - if given, specifies upsampling factor relative to the largest spatial extent of a convolutional layer. if None then resized to size of input images.
            spatial_order - spline order of filter for upsampling in spatial mode, by default 1 (bilinear).
            is_train - bool - [True] for training mode
            lr - float - initial learning rate
            beta1 - float - initial momentum term for adam
            version - 0.1 for latest, 0.0 was original (with a bug)
        """
    BaseModel.initialize(self, use_gpu=use_gpu)
    self.model = model
    self.net = net
    self.is_train = is_train
    self.spatial = spatial
    self.model_name = '%s [%s]' % (model, net)
    if self.model == 'net-lin':
        self.net = PNetLin(pnet_rand=pnet_rand, pnet_tune=pnet_tune, pnet_type=net, use_dropout=True, spatial=spatial, version=version, lpips=True)
        kw = dict(map_location='cpu')
        if model_path is None:
            import inspect
            model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'models', 'lpips_models', f'{net}.pth'))
        if not is_train:
            self.net.load_state_dict(torch.load(model_path, **kw), strict=False)
    elif self.model == 'net':
        self.net = PNetLin(pnet_rand=pnet_rand, pnet_type=net, lpips=False)
    elif self.model in ['L2', 'l2']:
        self.net = L2(use_gpu=use_gpu, colorspace=colorspace)
        self.model_name = 'L2'
    elif self.model in ['DSSIM', 'dssim', 'SSIM', 'ssim']:
        self.net = DSSIM(use_gpu=use_gpu, colorspace=colorspace)
        self.model_name = 'SSIM'
    else:
        raise ValueError('Model [%s] not recognized.' % self.model)
    self.trainable_parameters = list(self.net.parameters())
    if self.is_train:
        self.rankLoss = BCERankingLoss()
        self.trainable_parameters += list(self.rankLoss.net.parameters())
        self.lr = lr
        self.old_lr = lr
        self.optimizer_net = torch.optim.Adam(self.trainable_parameters, lr=lr, betas=(beta1, 0.999))
    else:
        self.net.eval()
    if printNet:
        print('---------- Networks initialized -------------')
        print_network(self.net)
        print('-----------------------------------------------')

def update_learning_rate(self, nepoch_decay):
    lrd = self.lr / nepoch_decay
    lr = self.old_lr - lrd
    for param_group in self.optimizer_net.param_groups:
        param_group['lr'] = lr
    print('update lr [%s] decay: %f -> %f' % (type, self.old_lr, lr))
    self.old_lr = lr

def benchmark():
    filename = sys.argv[1]
    img = Image.open(filename)
    data = np.array(img.getdata(), dtype=np.uint8)
    if len(data.shape) == 1:
        n_channels = 1
        reshape = (img.height, img.width)
    else:
        n_channels = min(data.shape[1], 3)
        data = data[:, :n_channels]
        reshape = (img.height, img.width, n_channels)
    data = data.reshape(reshape).astype(np.uint8)
    methods = [simplest_countless, quick_countless, quick_countless_xor, quickest_countless, stippled_countless, zero_corrected_countless, countless, downsample_with_averaging, downsample_with_max_pooling, ndzoom, striding]
    formats = {1: 'L', 3: 'RGB', 4: 'RGBA'}
    if not os.path.exists('./results'):
        os.mkdir('./results')
    N = 500
    img_size = float(img.width * img.height) / 1024.0 / 1024.0
    print('N = %d, %dx%d (%.2f MPx) %d chan, %s' % (N, img.width, img.height, img_size, n_channels, filename))
    print('Algorithm\tMPx/sec\tMB/sec\tSec')
    for fn in methods:
        print(fn.__name__, end='')
        sys.stdout.flush()
        start = time.time()
        for _ in tqdm(range(N), desc=fn.__name__, disable=True):
            result = fn(data)
        end = time.time()
        print('\r', end='')
        total_time = end - start
        mpx = N * img_size / total_time
        mbytes = N * img_size * n_channels / total_time
        print('%s\t%.3f\t%.3f\t%.2f' % (fn.__name__, mpx, mbytes, total_time))
        outimg = Image.fromarray(np.squeeze(result), formats[n_channels])
        outimg.save('./results/{}.png'.format(fn.__name__, 'PNG'))

def test_countless2d():

    def test_all_cases(fn, test_zero):
        case1 = np.array([[1, 2], [3, 4]]).reshape((2, 2, 1, 1))
        case2 = np.array([[1, 1], [2, 3]]).reshape((2, 2, 1, 1))
        case1z = np.array([[0, 1], [2, 3]]).reshape((2, 2, 1, 1))
        case2z = np.array([[0, 0], [2, 3]]).reshape((2, 2, 1, 1))
        case3 = np.array([[1, 1], [2, 2]]).reshape((2, 2, 1, 1))
        case4 = np.array([[1, 2], [2, 2]]).reshape((2, 2, 1, 1))
        case5 = np.array([[5, 5], [5, 5]]).reshape((2, 2, 1, 1))
        is_255_handled = np.array([[255, 255], [1, 2]], dtype=np.uint8).reshape((2, 2, 1, 1))
        test = lambda case: fn(case)
        if test_zero:
            assert test(case1z) == [[[[3]]]]
            assert test(case2z) == [[[[0]]]]
        else:
            assert test(case1) == [[[[4]]]]
            assert test(case2) == [[[[1]]]]
        assert test(case3) == [[[[1]]]]
        assert test(case4) == [[[[2]]]]
        assert test(case5) == [[[[5]]]]
        assert test(is_255_handled) == [[[[255]]]]
        assert fn(case1).dtype == case1.dtype
    test_all_cases(countless2d.simplest_countless, False)
    test_all_cases(countless2d.quick_countless, False)
    test_all_cases(countless2d.quickest_countless, False)
    test_all_cases(countless2d.stippled_countless, False)
    methods = [countless2d.zero_corrected_countless, countless2d.countless, countless2d.countless_if]
    for fn in methods:
        print(fn.__name__)
        test_all_cases(fn, True)

def test_countless3d():

    def test_all_cases(fn):
        alldifferent = [[[1, 2], [3, 4]], [[5, 6], [7, 8]]]
        allsame = [[[1, 1], [1, 1]], [[1, 1], [1, 1]]]
        assert fn(np.array(alldifferent)) == [[[8]]]
        assert fn(np.array(allsame)) == [[[1]]]
        twosame = deepcopy(alldifferent)
        twosame[1][1][0] = 2
        assert fn(np.array(twosame)) == [[[2]]]
        threemixed = [[[3, 3], [1, 2]], [[2, 4], [4, 3]]]
        assert fn(np.array(threemixed)) == [[[3]]]
        foursame = [[[4, 4], [1, 2]], [[2, 4], [4, 3]]]
        assert fn(np.array(foursame)) == [[[4]]]
        fivesame = [[[5, 4], [5, 5]], [[2, 4], [5, 5]]]
        assert fn(np.array(fivesame)) == [[[5]]]

    def countless3d_generalized(img):
        return countless3d.countless_generalized(img, (2, 2, 2))

    def countless3d_dynamic_generalized(img):
        return countless3d.dynamic_countless_generalized(img, (2, 2, 2))
    methods = [countless3d.countless3d, countless3d.dynamic_countless3d, countless3d_generalized, countless3d_dynamic_generalized]
    for fn in methods:
        test_all_cases(fn)

def pick(elements):
    eq = (elements[i] == elements[i + 1] for i in range(len(elements) - 1))
    anded = reduce(lambda p, q: p & q, eq)
    return elements[0] * anded

def mobilenetv2(pretrained=False, **kwargs):
    """Constructs a MobileNet_V2 model.

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    model = MobileNetV2(n_class=1000, **kwargs)
    if pretrained:
        model.load_state_dict(load_url(model_urls['mobilenetv2']), strict=False)
    return model

class ModelBuilder:

    @staticmethod
    def weights_init(m):
        classname = m.__class__.__name__
        if classname.find('Conv') != -1:
            nn.init.kaiming_normal_(m.weight.data)
        elif classname.find('BatchNorm') != -1:
            m.weight.data.fill_(1.0)
            m.bias.data.fill_(0.0001)

    @staticmethod
    def build_encoder(arch='resnet50dilated', fc_dim=512, weights=''):
        pretrained = True if len(weights) == 0 else False
        arch = arch.lower()
        if arch == 'mobilenetv2dilated':
            orig_mobilenet = mobilenet.__dict__['mobilenetv2'](pretrained=pretrained)
            net_encoder = MobileNetV2Dilated(orig_mobilenet, dilate_scale=8)
        elif arch == 'resnet18':
            orig_resnet = resnet.__dict__['resnet18'](pretrained=pretrained)
            net_encoder = Resnet(orig_resnet)
        elif arch == 'resnet18dilated':
            orig_resnet = resnet.__dict__['resnet18'](pretrained=pretrained)
            net_encoder = ResnetDilated(orig_resnet, dilate_scale=8)
        elif arch == 'resnet50dilated':
            orig_resnet = resnet.__dict__['resnet50'](pretrained=pretrained)
            net_encoder = ResnetDilated(orig_resnet, dilate_scale=8)
        elif arch == 'resnet50':
            orig_resnet = resnet.__dict__['resnet50'](pretrained=pretrained)
            net_encoder = Resnet(orig_resnet)
        else:
            raise Exception('Architecture undefined!')
        if len(weights) > 0:
            print('Loading weights for net_encoder')
            net_encoder.load_state_dict(torch.load(weights, map_location=lambda storage, loc: storage), strict=False)
        return net_encoder

    @staticmethod
    def build_decoder(arch='ppm_deepsup', fc_dim=512, num_class=NUM_CLASS, weights='', use_softmax=False, drop_last_conv=False):
        arch = arch.lower()
        if arch == 'ppm_deepsup':
            net_decoder = PPMDeepsup(num_class=num_class, fc_dim=fc_dim, use_softmax=use_softmax, drop_last_conv=drop_last_conv)
        elif arch == 'c1_deepsup':
            net_decoder = C1DeepSup(num_class=num_class, fc_dim=fc_dim, use_softmax=use_softmax, drop_last_conv=drop_last_conv)
        else:
            raise Exception('Architecture undefined!')
        net_decoder.apply(ModelBuilder.weights_init)
        if len(weights) > 0:
            print('Loading weights for net_decoder')
            net_decoder.load_state_dict(torch.load(weights, map_location=lambda storage, loc: storage), strict=False)
        return net_decoder

    @staticmethod
    def get_decoder(weights_path, arch_encoder, arch_decoder, fc_dim, drop_last_conv, *arts, **kwargs):
        path = os.path.join(weights_path, 'ade20k', f'ade20k-{arch_encoder}-{arch_decoder}/decoder_epoch_20.pth')
        return ModelBuilder.build_decoder(arch=arch_decoder, fc_dim=fc_dim, weights=path, use_softmax=True, drop_last_conv=drop_last_conv)

    @staticmethod
    def get_encoder(weights_path, arch_encoder, arch_decoder, fc_dim, segmentation, *arts, **kwargs):
        if segmentation:
            path = os.path.join(weights_path, 'ade20k', f'ade20k-{arch_encoder}-{arch_decoder}/encoder_epoch_20.pth')
        else:
            path = ''
        return ModelBuilder.build_encoder(arch=arch_encoder, fc_dim=fc_dim, weights=path)

@staticmethod
def build_encoder(arch='resnet50dilated', fc_dim=512, weights=''):
    pretrained = True if len(weights) == 0 else False
    arch = arch.lower()
    if arch == 'mobilenetv2dilated':
        orig_mobilenet = mobilenet.__dict__['mobilenetv2'](pretrained=pretrained)
        net_encoder = MobileNetV2Dilated(orig_mobilenet, dilate_scale=8)
    elif arch == 'resnet18':
        orig_resnet = resnet.__dict__['resnet18'](pretrained=pretrained)
        net_encoder = Resnet(orig_resnet)
    elif arch == 'resnet18dilated':
        orig_resnet = resnet.__dict__['resnet18'](pretrained=pretrained)
        net_encoder = ResnetDilated(orig_resnet, dilate_scale=8)
    elif arch == 'resnet50dilated':
        orig_resnet = resnet.__dict__['resnet50'](pretrained=pretrained)
        net_encoder = ResnetDilated(orig_resnet, dilate_scale=8)
    elif arch == 'resnet50':
        orig_resnet = resnet.__dict__['resnet50'](pretrained=pretrained)
        net_encoder = Resnet(orig_resnet)
    else:
        raise Exception('Architecture undefined!')
    if len(weights) > 0:
        print('Loading weights for net_encoder')
        net_encoder.load_state_dict(torch.load(weights, map_location=lambda storage, loc: storage), strict=False)
    return net_encoder

@staticmethod
def build_decoder(arch='ppm_deepsup', fc_dim=512, num_class=NUM_CLASS, weights='', use_softmax=False, drop_last_conv=False):
    arch = arch.lower()
    if arch == 'ppm_deepsup':
        net_decoder = PPMDeepsup(num_class=num_class, fc_dim=fc_dim, use_softmax=use_softmax, drop_last_conv=drop_last_conv)
    elif arch == 'c1_deepsup':
        net_decoder = C1DeepSup(num_class=num_class, fc_dim=fc_dim, use_softmax=use_softmax, drop_last_conv=drop_last_conv)
    else:
        raise Exception('Architecture undefined!')
    net_decoder.apply(ModelBuilder.weights_init)
    if len(weights) > 0:
        print('Loading weights for net_decoder')
        net_decoder.load_state_dict(torch.load(weights, map_location=lambda storage, loc: storage), strict=False)
    return net_decoder

@staticmethod
def get_decoder(weights_path, arch_encoder, arch_decoder, fc_dim, drop_last_conv, *arts, **kwargs):
    path = os.path.join(weights_path, 'ade20k', f'ade20k-{arch_encoder}-{arch_decoder}/decoder_epoch_20.pth')
    return ModelBuilder.build_decoder(arch=arch_decoder, fc_dim=fc_dim, weights=path, use_softmax=True, drop_last_conv=drop_last_conv)

@staticmethod
def get_encoder(weights_path, arch_encoder, arch_decoder, fc_dim, segmentation, *arts, **kwargs):
    if segmentation:
        path = os.path.join(weights_path, 'ade20k', f'ade20k-{arch_encoder}-{arch_decoder}/encoder_epoch_20.pth')
    else:
        path = ''
    return ModelBuilder.build_encoder(arch=arch_encoder, fc_dim=fc_dim, weights=path)

def load_url(url, model_dir='./pretrained', map_location=None):
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)
    filename = url.split('/')[-1]
    cached_file = os.path.join(model_dir, filename)
    if not os.path.exists(cached_file):
        sys.stderr.write('Downloading: "{}" to {}\n'.format(url, cached_file))
        urlretrieve(url, cached_file)
    return torch.load(cached_file, map_location=map_location)

def resnet50(pretrained=False, **kwargs):
    """Constructs a ResNet-50 model.

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    model = ResNet(Bottleneck, [3, 4, 6, 3], **kwargs)
    if pretrained:
        model.load_state_dict(load_url(model_urls['resnet50']), strict=False)
    return model

def resnet18(pretrained=False, **kwargs):
    """Constructs a ResNet-18 model.
    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    model = ResNet(BasicBlock, [2, 2, 2, 2], **kwargs)
    if pretrained:
        model.load_state_dict(load_url(model_urls['resnet18']))
    return model

class SyncMaster(object):
    """An abstract `SyncMaster` object.

    - During the replication, as the data parallel will trigger an callback of each module, all slave devices should
    call `register(id)` and obtain an `SlavePipe` to communicate with the master.
    - During the forward pass, master device invokes `run_master`, all messages from slave devices will be collected,
    and passed to a registered callback.
    - After receiving the messages, the master device should gather the information and determine to message passed
    back to each slave devices.
    """

    def __init__(self, master_callback):
        """

        Args:
            master_callback: a callback to be invoked after having collected messages from slave devices.
        """
        self._master_callback = master_callback
        self._queue = queue.Queue()
        self._registry = collections.OrderedDict()
        self._activated = False

    def register_slave(self, identifier):
        """
        Register an slave device.

        Args:
            identifier: an identifier, usually is the device id.

        Returns: a `SlavePipe` object which can be used to communicate with the master device.

        """
        if self._activated:
            assert self._queue.empty(), 'Queue is not clean before next initialization.'
            self._activated = False
            self._registry.clear()
        future = FutureResult()
        self._registry[identifier] = _MasterRegistry(future)
        return SlavePipe(identifier, self._queue, future)

    def run_master(self, master_msg):
        """
        Main entry for the master device in each forward pass.
        The messages were first collected from each devices (including the master device), and then
        an callback will be invoked to compute the message to be sent back to each devices
        (including the master device).

        Args:
            master_msg: the message that the master want to send to itself. This will be placed as the first
            message when calling `master_callback`. For detailed usage, see `_SynchronizedBatchNorm` for an example.

        Returns: the message to be sent back to the master device.

        """
        self._activated = True
        intermediates = [(0, master_msg)]
        for i in range(self.nr_slaves):
            intermediates.append(self._queue.get())
        results = self._master_callback(intermediates)
        assert results[0][0] == 0, 'The first result should belongs to the master.'
        for i, res in results:
            if i == 0:
                continue
            self._registry[i].result.put(res)
        for i in range(self.nr_slaves):
            assert self._queue.get() is True
        return results[0][1]

    @property
    def nr_slaves(self):
        return len(self._registry)

@property
def nr_slaves(self):
    return len(self._registry)

def default_image_loader(path):
    """The default image loader, reads the image from the given path. It first tries to use the jpeg4py_loader,
    but reverts to the opencv_loader if the former is not available."""
    if default_image_loader.use_jpeg4py is None:
        im = jpeg4py_loader(path)
        if im is None:
            default_image_loader.use_jpeg4py = False
            print('Using opencv_loader instead.')
        else:
            default_image_loader.use_jpeg4py = True
            return im
    if default_image_loader.use_jpeg4py:
        return jpeg4py_loader(path)
    return opencv_loader(path)

def opencv_loader(path):
    """ Read image using opencv's imread function and returns it in rgb format"""
    try:
        im = cv.imread(path, cv.IMREAD_COLOR)
        return cv.cvtColor(im, cv.COLOR_BGR2RGB)
    except Exception as e:
        print('ERROR: Could not read image "{}"'.format(path))
        print(e)
        return None

def opencv_seg_loader(path):
    """ Read segmentation annotation using opencv's imread function"""
    try:
        return cv.imread(path)
    except Exception as e:
        print('ERROR: Could not read image "{}"'.format(path))
        print(e)
        return None

def imread_indexed(filename):
    """ Load indexed image with given filename. Used to read segmentation annotations."""
    im = Image.open(filename)
    annotation = np.atleast_3d(im)[..., 0]
    return annotation

def imwrite_indexed(filename, array, color_palette=None):
    """ Save indexed image as png. Used to save segmentation annotation."""
    if color_palette is None:
        color_palette = davis_palette
    if np.atleast_3d(array).shape[2] != 1:
        raise Exception('Saving indexed PNGs requires 2D array.')
    im = Image.fromarray(array)
    im.putpalette(color_palette.ravel())
    im.save(filename, format='PNG')

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

def list(self):
    return list(self)

def video2frames(video_path, frame_path):
    video = cv2.VideoCapture(video_path)
    os.makedirs(frame_path, exist_ok=True)
    frame_num = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = video.get(cv2.CAP_PROP_FPS)
    initial_img = None
    for idx in tqdm(range(frame_num), 'Extract frames'):
        success, image = video.read()
        if idx == 0:
            initial_img = image.copy()
        assert success, 'extract the {}th frame in video {} failed!'.format(idx, video_path)
        cv2.imwrite('{}/{:05d}.jpg'.format(frame_path, idx), image)
    return (fps, initial_img)

def frames2video(frames_list, video_path, fps=30, remove_tmp=False):
    if isinstance(frames_list, str):
        frames_list = glob(f'{frames_list}/*.jpg')
    writer = imageio.get_writer(video_path, fps=fps)
    for frame in tqdm(frames_list, 'Export video'):
        if isinstance(frame, str):
            frame = imageio.imread(frame)
        else:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = imageio.core.util.Array(frame)
        writer.append_data(frame)
    writer.close()
    print(f'find video at {video_path}.')
    if remove_tmp and isinstance(frames_list, str):
        shutil.rmtree(frames_list)

class SmoothedValue(object):
    """Track a series of values and provide access to smoothed values over a
    window or the global series average.
    """

    def __init__(self, window_size=20, fmt=None):
        if fmt is None:
            fmt = '{median:.4f} ({global_avg:.4f})'
        self.deque = deque(maxlen=window_size)
        self.total = 0.0
        self.count = 0
        self.fmt = fmt

    def update(self, value, n=1):
        self.deque.append(value)
        self.count += n
        self.total += value * n

    def synchronize_between_processes(self):
        """
        Warning: does not synchronize the deque!
        """
        if not is_dist_avail_and_initialized():
            return
        t = torch.tensor([self.count, self.total], dtype=torch.float64, device='cuda')
        dist.barrier()
        dist.all_reduce(t)
        t = t.tolist()
        self.count = int(t[0])
        self.total = t[1]

    @property
    def median(self):
        d = torch.tensor(list(self.deque))
        return d.median().item()

    @property
    def avg(self):
        d = torch.tensor(list(self.deque), dtype=torch.float32)
        return d.mean().item()

    @property
    def global_avg(self):
        return self.total / self.count

    @property
    def max(self):
        return max(self.deque)

    @property
    def value(self):
        return self.deque[-1]

    def __str__(self):
        return self.fmt.format(median=self.median, avg=self.avg, global_avg=self.global_avg, max=self.max, value=self.value)

def __str__(self):
    return self.fmt.format(median=self.median, avg=self.avg, global_avg=self.global_avg, max=self.max, value=self.value)

class MetricLogger(object):

    def __init__(self, delimiter='\t'):
        self.meters = defaultdict(SmoothedValue)
        self.delimiter = delimiter

    def update(self, **kwargs):
        for k, v in kwargs.items():
            if isinstance(v, torch.Tensor):
                v = v.item()
            assert isinstance(v, (float, int))
            self.meters[k].update(v)

    def __getattr__(self, attr):
        if attr in self.meters:
            return self.meters[attr]
        if attr in self.__dict__:
            return self.__dict__[attr]
        raise AttributeError("'{}' object has no attribute '{}'".format(type(self).__name__, attr))

    def __str__(self):
        loss_str = []
        for name, meter in self.meters.items():
            loss_str.append('{}: {}'.format(name, str(meter)))
        return self.delimiter.join(loss_str)

    def synchronize_between_processes(self):
        for meter in self.meters.values():
            meter.synchronize_between_processes()

    def add_meter(self, name, meter):
        self.meters[name] = meter

    def log_every(self, iterable, print_freq, header=None):
        i = 0
        if not header:
            header = ''
        start_time = time.time()
        end = time.time()
        iter_time = SmoothedValue(fmt='{avg:.4f}')
        data_time = SmoothedValue(fmt='{avg:.4f}')
        space_fmt = ':' + str(len(str(len(iterable)))) + 'd'
        if torch.cuda.is_available():
            log_msg = self.delimiter.join([header, '[{0' + space_fmt + '}/{1}]', 'eta: {eta}', '{meters}', 'time: {time}', 'data: {data}', 'max mem: {memory:.0f}'])
        else:
            log_msg = self.delimiter.join([header, '[{0' + space_fmt + '}/{1}]', 'eta: {eta}', '{meters}', 'time: {time}', 'data: {data}'])
        MB = 1024.0 * 1024.0
        for obj in iterable:
            data_time.update(time.time() - end)
            yield obj
            iter_time.update(time.time() - end)
            if i % print_freq == 0 or i == len(iterable) - 1:
                eta_seconds = iter_time.global_avg * (len(iterable) - i)
                eta_string = str(datetime.timedelta(seconds=int(eta_seconds)))
                if torch.cuda.is_available():
                    print(log_msg.format(i, len(iterable), eta=eta_string, meters=str(self), time=str(iter_time), data=str(data_time), memory=torch.cuda.max_memory_allocated() / MB))
                else:
                    print(log_msg.format(i, len(iterable), eta=eta_string, meters=str(self), time=str(iter_time), data=str(data_time)))
            i += 1
            end = time.time()
        total_time = time.time() - start_time
        total_time_str = str(datetime.timedelta(seconds=int(total_time)))
        print('{} Total time: {} ({:.4f} s / it)'.format(header, total_time_str, total_time / len(iterable)))

def __str__(self):
    loss_str = []
    for name, meter in self.meters.items():
        loss_str.append('{}: {}'.format(name, str(meter)))
    return self.delimiter.join(loss_str)

def log_every(self, iterable, print_freq, header=None):
    i = 0
    if not header:
        header = ''
    start_time = time.time()
    end = time.time()
    iter_time = SmoothedValue(fmt='{avg:.4f}')
    data_time = SmoothedValue(fmt='{avg:.4f}')
    space_fmt = ':' + str(len(str(len(iterable)))) + 'd'
    if torch.cuda.is_available():
        log_msg = self.delimiter.join([header, '[{0' + space_fmt + '}/{1}]', 'eta: {eta}', '{meters}', 'time: {time}', 'data: {data}', 'max mem: {memory:.0f}'])
    else:
        log_msg = self.delimiter.join([header, '[{0' + space_fmt + '}/{1}]', 'eta: {eta}', '{meters}', 'time: {time}', 'data: {data}'])
    MB = 1024.0 * 1024.0
    for obj in iterable:
        data_time.update(time.time() - end)
        yield obj
        iter_time.update(time.time() - end)
        if i % print_freq == 0 or i == len(iterable) - 1:
            eta_seconds = iter_time.global_avg * (len(iterable) - i)
            eta_string = str(datetime.timedelta(seconds=int(eta_seconds)))
            if torch.cuda.is_available():
                print(log_msg.format(i, len(iterable), eta=eta_string, meters=str(self), time=str(iter_time), data=str(data_time), memory=torch.cuda.max_memory_allocated() / MB))
            else:
                print(log_msg.format(i, len(iterable), eta=eta_string, meters=str(self), time=str(iter_time), data=str(data_time)))
        i += 1
        end = time.time()
    total_time = time.time() - start_time
    total_time_str = str(datetime.timedelta(seconds=int(total_time)))
    print('{} Total time: {} ({:.4f} s / it)'.format(header, total_time_str, total_time / len(iterable)))

def get_sha():
    cwd = os.path.dirname(os.path.abspath(__file__))

    def _run(command):
        return subprocess.check_output(command, cwd=cwd).decode('ascii').strip()
    sha = 'N/A'
    diff = 'clean'
    branch = 'N/A'
    try:
        sha = _run(['git', 'rev-parse', 'HEAD'])
        subprocess.check_output(['git', 'diff'], cwd=cwd)
        diff = _run(['git', 'diff-index', 'HEAD'])
        diff = 'has uncommited changes' if diff else 'clean'
        branch = _run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
    except Exception:
        pass
    message = f'sha: {sha}, status: {diff}, branch: {branch}'
    return message

class NestedTensor(object):

    def __init__(self, tensors, mask: Optional[Tensor]):
        self.tensors = tensors
        self.mask = mask

    def to(self, device):
        cast_tensor = self.tensors.to(device)
        mask = self.mask
        if mask is not None:
            assert mask is not None
            cast_mask = mask.to(device)
        else:
            cast_mask = None
        return NestedTensor(cast_tensor, cast_mask)

    def decompose(self):
        return (self.tensors, self.mask)

    def __repr__(self):
        return str(self.tensors)

def __repr__(self):
    return str(self.tensors)

def save_on_master(*args, **kwargs):
    if is_main_process():
        torch.save(*args, **kwargs)

class get_local(object):
    cache = {}
    is_activate = False

    def __init__(self, varname):
        self.varname = varname

    def __call__(self, func):
        if not type(self).is_activate:
            return func
        type(self).cache[func.__qualname__] = []
        c = Bytecode.from_code(func.__code__)
        extra_code = [Instr('STORE_FAST', '_res'), Instr('LOAD_FAST', self.varname), Instr('STORE_FAST', '_value'), Instr('LOAD_FAST', '_res'), Instr('LOAD_FAST', '_value'), Instr('BUILD_TUPLE', 2), Instr('STORE_FAST', '_result_tuple'), Instr('LOAD_FAST', '_result_tuple')]
        c[-1:-1] = extra_code
        func.__code__ = c.to_code()

        def wrapper(*args, **kwargs):
            res, values = func(*args, **kwargs)
            if isinstance(values, torch.Tensor):
                type(self).cache[func.__qualname__].append(values.detach().cpu().numpy())
            elif isinstance(values, list):
                type(self).cache[func.__qualname__].append([value.detach().cpu().numpy() for value in values])
            else:
                raise NotImplementedError
            return res
        return wrapper

    @classmethod
    def clear(cls):
        for key in cls.cache.keys():
            cls.cache[key] = []

    @classmethod
    def activate(cls):
        cls.is_activate = True

@classmethod
def clear(cls):
    for key in cls.cache.keys():
        cls.cache[key] = []

def parameters(yaml_name: str):
    params = TrackerParams()
    prj_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
    yaml_file = os.path.join(prj_dir, 'experiments/ostrack/%s.yaml' % yaml_name)
    update_config_from_file(yaml_file)
    params.cfg = cfg
    params.template_factor = cfg.TEST.TEMPLATE_FACTOR
    params.template_size = cfg.TEST.TEMPLATE_SIZE
    params.search_factor = cfg.TEST.SEARCH_FACTOR
    params.search_size = cfg.TEST.SEARCH_SIZE
    params.checkpoint = os.path.join(prj_dir, 'pretrain', f'{yaml_name}.pth')
    assert os.path.exists(params.checkpoint), f'checkpoint not found at {params.checkpoint}'
    params.save_all_boxes = False
    return params

def load_text_numpy(path, delimiter, dtype):
    if isinstance(delimiter, (tuple, list)):
        for d in delimiter:
            try:
                ground_truth_rect = np.loadtxt(path, delimiter=d, dtype=dtype)
                return ground_truth_rect
            except:
                pass
        raise Exception('Could not read file {}'.format(path))
    else:
        ground_truth_rect = np.loadtxt(path, delimiter=delimiter, dtype=dtype)
        return ground_truth_rect

def load_text_pandas(path, delimiter, dtype):
    if isinstance(delimiter, (tuple, list)):
        for d in delimiter:
            try:
                ground_truth_rect = pd.read_csv(path, delimiter=d, header=None, dtype=dtype, na_filter=False, low_memory=False).values
                return ground_truth_rect
            except Exception as e:
                pass
        raise Exception('Could not read file {}'.format(path))
    else:
        ground_truth_rect = pd.read_csv(path, delimiter=delimiter, header=None, dtype=dtype, na_filter=False, low_memory=False).values
        return ground_truth_rect

class OSTrack(BaseTracker):

    def __init__(self, params, dataset_name):
        super(OSTrack, self).__init__(params)
        network = build_ostrack(params.cfg, training=False)
        network.load_state_dict(torch.load(self.params.checkpoint, map_location='cpu')['net'], strict=True)
        self.cfg = params.cfg
        self.network = network.cuda()
        self.network.eval()
        self.preprocessor = Preprocessor()
        self.state = None
        self.feat_sz = self.cfg.TEST.SEARCH_SIZE // self.cfg.MODEL.BACKBONE.STRIDE
        self.output_window = hann2d(torch.tensor([self.feat_sz, self.feat_sz]).long(), centered=True).cuda()
        self.debug = params.debug
        self.use_visdom = params.debug
        self.frame_id = 0
        if self.debug:
            if not self.use_visdom:
                self.save_dir = 'debug'
                if not os.path.exists(self.save_dir):
                    os.makedirs(self.save_dir)
            else:
                self._init_visdom(None, 1)
        self.save_all_boxes = params.save_all_boxes
        self.z_dict1 = {}

    def initialize(self, image, info: dict):
        z_patch_arr, resize_factor, z_amask_arr = sample_target(image, info['init_bbox'], self.params.template_factor, output_sz=self.params.template_size)
        self.z_patch_arr = z_patch_arr
        template = self.preprocessor.process(z_patch_arr, z_amask_arr)
        with torch.no_grad():
            self.z_dict1 = template
        self.box_mask_z = None
        if self.cfg.MODEL.BACKBONE.CE_LOC:
            template_bbox = self.transform_bbox_to_crop(info['init_bbox'], resize_factor, template.tensors.device).squeeze(1)
            self.box_mask_z = generate_mask_cond(self.cfg, 1, template.tensors.device, template_bbox)
        self.state = info['init_bbox']
        self.frame_id = 0
        if self.save_all_boxes:
            'save all predicted boxes'
            all_boxes_save = info['init_bbox'] * self.cfg.MODEL.NUM_OBJECT_QUERIES
            return {'all_boxes': all_boxes_save}

    def track(self, image, info: dict=None):
        H, W, _ = image.shape
        self.frame_id += 1
        x_patch_arr, resize_factor, x_amask_arr = sample_target(image, self.state, self.params.search_factor, output_sz=self.params.search_size)
        search = self.preprocessor.process(x_patch_arr, x_amask_arr)
        with torch.no_grad():
            x_dict = search
            out_dict = self.network.forward(template=self.z_dict1.tensors, search=x_dict.tensors, ce_template_mask=self.box_mask_z)
        pred_score_map = out_dict['score_map']
        response = self.output_window * pred_score_map
        pred_boxes = self.network.box_head.cal_bbox(response, out_dict['size_map'], out_dict['offset_map'])
        pred_boxes = pred_boxes.view(-1, 4)
        pred_box = (pred_boxes.mean(dim=0) * self.params.search_size / resize_factor).tolist()
        self.state = clip_box(self.map_box_back(pred_box, resize_factor), H, W, margin=10)
        if self.debug:
            if not self.use_visdom:
                x1, y1, w, h = self.state
                image_BGR = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                cv2.rectangle(image_BGR, (int(x1), int(y1)), (int(x1 + w), int(y1 + h)), color=(0, 0, 255), thickness=2)
                save_path = os.path.join(self.save_dir, '%04d.jpg' % self.frame_id)
                cv2.imwrite(save_path, image_BGR)
            else:
                self.visdom.register((image, info['gt_bbox'].tolist(), self.state), 'Tracking', 1, 'Tracking')
                self.visdom.register(torch.from_numpy(x_patch_arr).permute(2, 0, 1), 'image', 1, 'search_region')
                self.visdom.register(torch.from_numpy(self.z_patch_arr).permute(2, 0, 1), 'image', 1, 'template')
                self.visdom.register(pred_score_map.view(self.feat_sz, self.feat_sz), 'heatmap', 1, 'score_map')
                self.visdom.register((pred_score_map * self.output_window).view(self.feat_sz, self.feat_sz), 'heatmap', 1, 'score_map_hann')
                if 'removed_indexes_s' in out_dict and out_dict['removed_indexes_s']:
                    removed_indexes_s = out_dict['removed_indexes_s']
                    removed_indexes_s = [removed_indexes_s_i.cpu().numpy() for removed_indexes_s_i in removed_indexes_s]
                    masked_search = gen_visualization(x_patch_arr, removed_indexes_s)
                    self.visdom.register(torch.from_numpy(masked_search).permute(2, 0, 1), 'image', 1, 'masked_search')
                while self.pause_mode:
                    if self.step:
                        self.step = False
                        break
        if self.save_all_boxes:
            'save all predictions'
            all_boxes = self.map_box_back_batch(pred_boxes * self.params.search_size / resize_factor, resize_factor)
            all_boxes_save = all_boxes.view(-1).tolist()
            return {'target_bbox': self.state, 'all_boxes': all_boxes_save}
        else:
            return {'target_bbox': self.state}

    def map_box_back(self, pred_box: list, resize_factor: float):
        cx_prev, cy_prev = (self.state[0] + 0.5 * self.state[2], self.state[1] + 0.5 * self.state[3])
        cx, cy, w, h = pred_box
        half_side = 0.5 * self.params.search_size / resize_factor
        cx_real = cx + (cx_prev - half_side)
        cy_real = cy + (cy_prev - half_side)
        return [cx_real - 0.5 * w, cy_real - 0.5 * h, w, h]

    def map_box_back_batch(self, pred_box: torch.Tensor, resize_factor: float):
        cx_prev, cy_prev = (self.state[0] + 0.5 * self.state[2], self.state[1] + 0.5 * self.state[3])
        cx, cy, w, h = pred_box.unbind(-1)
        half_side = 0.5 * self.params.search_size / resize_factor
        cx_real = cx + (cx_prev - half_side)
        cy_real = cy + (cy_prev - half_side)
        return torch.stack([cx_real - 0.5 * w, cy_real - 0.5 * h, w, h], dim=-1)

    def add_hook(self):
        conv_features, enc_attn_weights, dec_attn_weights = ([], [], [])
        for i in range(12):
            self.network.backbone.blocks[i].attn.register_forward_hook(lambda self, input, output: enc_attn_weights.append(output[1]))
        self.enc_attn_weights = enc_attn_weights

def __init__(self, params, dataset_name):
    super(OSTrack, self).__init__(params)
    network = build_ostrack(params.cfg, training=False)
    network.load_state_dict(torch.load(self.params.checkpoint, map_location='cpu')['net'], strict=True)
    self.cfg = params.cfg
    self.network = network.cuda()
    self.network.eval()
    self.preprocessor = Preprocessor()
    self.state = None
    self.feat_sz = self.cfg.TEST.SEARCH_SIZE // self.cfg.MODEL.BACKBONE.STRIDE
    self.output_window = hann2d(torch.tensor([self.feat_sz, self.feat_sz]).long(), centered=True).cuda()
    self.debug = params.debug
    self.use_visdom = params.debug
    self.frame_id = 0
    if self.debug:
        if not self.use_visdom:
            self.save_dir = 'debug'
            if not os.path.exists(self.save_dir):
                os.makedirs(self.save_dir)
        else:
            self._init_visdom(None, 1)
    self.save_all_boxes = params.save_all_boxes
    self.z_dict1 = {}

class Sequence:
    """Class for the sequence in an evaluation."""

    def __init__(self, name, frames, dataset, ground_truth_rect, ground_truth_seg=None, init_data=None, object_class=None, target_visible=None, object_ids=None, multiobj_mode=False):
        self.name = name
        self.frames = frames
        self.dataset = dataset
        self.ground_truth_rect = ground_truth_rect
        self.ground_truth_seg = ground_truth_seg
        self.object_class = object_class
        self.target_visible = target_visible
        self.object_ids = object_ids
        self.multiobj_mode = multiobj_mode
        self.init_data = self._construct_init_data(init_data)
        self._ensure_start_frame()

    def _ensure_start_frame(self):
        start_frame = min(list(self.init_data.keys()))
        if start_frame > 0:
            self.frames = self.frames[start_frame:]
            if self.ground_truth_rect is not None:
                if isinstance(self.ground_truth_rect, (dict, OrderedDict)):
                    for obj_id, gt in self.ground_truth_rect.items():
                        self.ground_truth_rect[obj_id] = gt[start_frame:, :]
                else:
                    self.ground_truth_rect = self.ground_truth_rect[start_frame:, :]
            if self.ground_truth_seg is not None:
                self.ground_truth_seg = self.ground_truth_seg[start_frame:]
                assert len(self.frames) == len(self.ground_truth_seg)
            if self.target_visible is not None:
                self.target_visible = self.target_visible[start_frame:]
            self.init_data = {frame - start_frame: val for frame, val in self.init_data.items()}

    def _construct_init_data(self, init_data):
        if init_data is not None:
            if not self.multiobj_mode:
                assert self.object_ids is None or len(self.object_ids) == 1
                for frame, init_val in init_data.items():
                    if 'bbox' in init_val and isinstance(init_val['bbox'], (dict, OrderedDict)):
                        init_val['bbox'] = init_val['bbox'][self.object_ids[0]]
            for frame, init_val in init_data.items():
                if 'bbox' in init_val:
                    if isinstance(init_val['bbox'], (dict, OrderedDict)):
                        init_val['bbox'] = OrderedDict({obj_id: list(init) for obj_id, init in init_val['bbox'].items()})
                    else:
                        init_val['bbox'] = list(init_val['bbox'])
        else:
            init_data = {0: dict()}
            if self.object_ids is not None:
                init_data[0]['object_ids'] = self.object_ids
            if self.ground_truth_rect is not None:
                if self.multiobj_mode:
                    assert isinstance(self.ground_truth_rect, (dict, OrderedDict))
                    init_data[0]['bbox'] = OrderedDict({obj_id: list(gt[0, :]) for obj_id, gt in self.ground_truth_rect.items()})
                else:
                    assert self.object_ids is None or len(self.object_ids) == 1
                    if isinstance(self.ground_truth_rect, (dict, OrderedDict)):
                        init_data[0]['bbox'] = list(self.ground_truth_rect[self.object_ids[0]][0, :])
                    else:
                        init_data[0]['bbox'] = list(self.ground_truth_rect[0, :])
            if self.ground_truth_seg is not None:
                init_data[0]['mask'] = self.ground_truth_seg[0]
        return init_data

    def init_info(self):
        info = self.frame_info(frame_num=0)
        return info

    def frame_info(self, frame_num):
        info = self.object_init_data(frame_num=frame_num)
        return info

    def init_bbox(self, frame_num=0):
        return self.object_init_data(frame_num=frame_num).get('init_bbox')

    def init_mask(self, frame_num=0):
        return self.object_init_data(frame_num=frame_num).get('init_mask')

    def get_info(self, keys, frame_num=None):
        info = dict()
        for k in keys:
            val = self.get(k, frame_num=frame_num)
            if val is not None:
                info[k] = val
        return info

    def object_init_data(self, frame_num=None) -> dict:
        if frame_num is None:
            frame_num = 0
        if frame_num not in self.init_data:
            return dict()
        init_data = dict()
        for key, val in self.init_data[frame_num].items():
            if val is None:
                continue
            init_data['init_' + key] = val
        if 'init_mask' in init_data and init_data['init_mask'] is not None:
            anno = imread_indexed(init_data['init_mask'])
            if not self.multiobj_mode and self.object_ids is not None:
                assert len(self.object_ids) == 1
                anno = (anno == int(self.object_ids[0])).astype(np.uint8)
            init_data['init_mask'] = anno
        if self.object_ids is not None:
            init_data['object_ids'] = self.object_ids
            init_data['sequence_object_ids'] = self.object_ids
        return init_data

    def target_class(self, frame_num=None):
        return self.object_class

    def get(self, name, frame_num=None):
        return getattr(self, name)(frame_num)

    def __repr__(self):
        return '{self.__class__.__name__} {self.name}, length={len} frames'.format(self=self, len=len(self.frames))

def _ensure_start_frame(self):
    start_frame = min(list(self.init_data.keys()))
    if start_frame > 0:
        self.frames = self.frames[start_frame:]
        if self.ground_truth_rect is not None:
            if isinstance(self.ground_truth_rect, (dict, OrderedDict)):
                for obj_id, gt in self.ground_truth_rect.items():
                    self.ground_truth_rect[obj_id] = gt[start_frame:, :]
            else:
                self.ground_truth_rect = self.ground_truth_rect[start_frame:, :]
        if self.ground_truth_seg is not None:
            self.ground_truth_seg = self.ground_truth_seg[start_frame:]
            assert len(self.frames) == len(self.ground_truth_seg)
        if self.target_visible is not None:
            self.target_visible = self.target_visible[start_frame:]
        self.init_data = {frame - start_frame: val for frame, val in self.init_data.items()}

def _construct_init_data(self, init_data):
    if init_data is not None:
        if not self.multiobj_mode:
            assert self.object_ids is None or len(self.object_ids) == 1
            for frame, init_val in init_data.items():
                if 'bbox' in init_val and isinstance(init_val['bbox'], (dict, OrderedDict)):
                    init_val['bbox'] = init_val['bbox'][self.object_ids[0]]
        for frame, init_val in init_data.items():
            if 'bbox' in init_val:
                if isinstance(init_val['bbox'], (dict, OrderedDict)):
                    init_val['bbox'] = OrderedDict({obj_id: list(init) for obj_id, init in init_val['bbox'].items()})
                else:
                    init_val['bbox'] = list(init_val['bbox'])
    else:
        init_data = {0: dict()}
        if self.object_ids is not None:
            init_data[0]['object_ids'] = self.object_ids
        if self.ground_truth_rect is not None:
            if self.multiobj_mode:
                assert isinstance(self.ground_truth_rect, (dict, OrderedDict))
                init_data[0]['bbox'] = OrderedDict({obj_id: list(gt[0, :]) for obj_id, gt in self.ground_truth_rect.items()})
            else:
                assert self.object_ids is None or len(self.object_ids) == 1
                if isinstance(self.ground_truth_rect, (dict, OrderedDict)):
                    init_data[0]['bbox'] = list(self.ground_truth_rect[self.object_ids[0]][0, :])
                else:
                    init_data[0]['bbox'] = list(self.ground_truth_rect[0, :])
        if self.ground_truth_seg is not None:
            init_data[0]['mask'] = self.ground_truth_seg[0]
    return init_data

def __repr__(self):
    return '{self.__class__.__name__} {self.name}, length={len} frames'.format(self=self, len=len(self.frames))

class Tracker:
    """Wraps the tracker for evaluation and running purposes.
    args:
        name: Name of tracking method.
        parameter_name: Name of parameter file.
        run_id: The run id.
        display_name: Name to be displayed in the result plots.
    """

    def __init__(self, name: str, parameter_name: str, dataset_name: str, run_id: int=None, display_name: str=None, result_only=False):
        assert run_id is None or isinstance(run_id, int)
        self.name = name
        self.parameter_name = parameter_name
        self.dataset_name = dataset_name
        self.run_id = run_id
        self.display_name = display_name
        tracker_module_abspath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tracker', '%s.py' % self.name))
        if os.path.isfile(tracker_module_abspath):
            tracker_module = importlib.import_module('lib.test.tracker.{}'.format(self.name))
            self.tracker_class = tracker_module.get_tracker_class()
        else:
            self.tracker_class = None

    def create_tracker(self, params):
        tracker = self.tracker_class(params, self.dataset_name)
        return tracker

    def run_sequence(self, seq, debug=None):
        """Run tracker on sequence.
        args:
            seq: Sequence to run the tracker on.
            visualization: Set visualization flag (None means default value specified in the parameters).
            debug: Set debug level (None means default value specified in the parameters).
            multiobj_mode: Which mode to use for multiple objects.
        """
        params = self.get_parameters()
        debug_ = debug
        if debug is None:
            debug_ = getattr(params, 'debug', 0)
        params.debug = debug_
        init_info = seq.init_info()
        tracker = self.create_tracker(params)
        output = self._track_sequence(tracker, seq, init_info)
        return output

    def _track_sequence(self, tracker, seq, init_info):
        output = {'target_bbox': [], 'time': []}
        if tracker.params.save_all_boxes:
            output['all_boxes'] = []
            output['all_scores'] = []

        def _store_outputs(tracker_out: dict, defaults=None):
            defaults = {} if defaults is None else defaults
            for key in output.keys():
                val = tracker_out.get(key, defaults.get(key, None))
                if key in tracker_out or val is not None:
                    output[key].append(val)
        image = self._read_image(seq.frames[0])
        start_time = time.time()
        out = tracker.initialize(image, init_info)
        if out is None:
            out = {}
        prev_output = OrderedDict(out)
        init_default = {'target_bbox': init_info.get('init_bbox'), 'time': time.time() - start_time}
        if tracker.params.save_all_boxes:
            init_default['all_boxes'] = out['all_boxes']
            init_default['all_scores'] = out['all_scores']
        _store_outputs(out, init_default)
        for frame_num, frame_path in enumerate(seq.frames[1:], start=1):
            image = self._read_image(frame_path)
            start_time = time.time()
            info = seq.frame_info(frame_num)
            info['previous_output'] = prev_output
            if len(seq.ground_truth_rect) > 1:
                info['gt_bbox'] = seq.ground_truth_rect[frame_num]
            out = tracker.track(image, info)
            prev_output = OrderedDict(out)
            _store_outputs(out, {'time': time.time() - start_time})
        for key in ['target_bbox', 'all_boxes', 'all_scores']:
            if key in output and len(output[key]) <= 1:
                output.pop(key)
        return output

    def run_video(self, videofilepath, optional_box=None, debug=None, visdom_info=None, save_results=False):
        """Run the tracker with the vieofile.
        args:
            debug: Debug level.
        """
        params = self.get_parameters()
        debug_ = debug
        if debug is None:
            debug_ = getattr(params, 'debug', 0)
        params.debug = debug_
        params.tracker_name = self.name
        params.param_name = self.parameter_name
        multiobj_mode = getattr(params, 'multiobj_mode', getattr(self.tracker_class, 'multiobj_mode', 'default'))
        if multiobj_mode == 'default':
            tracker = self.create_tracker(params)
        elif multiobj_mode == 'parallel':
            tracker = MultiObjectWrapper(self.tracker_class, params, self.visdom, fast_load=True)
        else:
            raise ValueError('Unknown multi object mode {}'.format(multiobj_mode))
        assert os.path.isfile(videofilepath), 'Invalid param {}'.format(videofilepath)
        ', videofilepath must be a valid videofile'
        output_boxes = []
        cap = cv.VideoCapture(videofilepath)
        display_name = 'Display: ' + tracker.params.tracker_name
        cv.namedWindow(display_name, cv.WINDOW_NORMAL | cv.WINDOW_KEEPRATIO)
        cv.resizeWindow(display_name, 960, 720)
        success, frame = cap.read()
        cv.imshow(display_name, frame)

        def _build_init_info(box):
            return {'init_bbox': box}
        if success is not True:
            print('Read frame from {} failed.'.format(videofilepath))
            exit(-1)
        if optional_box is not None:
            assert isinstance(optional_box, (list, tuple))
            assert len(optional_box) == 4, "valid box's foramt is [x,y,w,h]"
            tracker.initialize(frame, _build_init_info(optional_box))
            output_boxes.append(optional_box)
        else:
            while True:
                frame_disp = frame.copy()
                cv.putText(frame_disp, 'Select target ROI and press ENTER', (20, 30), cv.FONT_HERSHEY_COMPLEX_SMALL, 1.5, (0, 0, 0), 1)
                x, y, w, h = cv.selectROI(display_name, frame_disp, fromCenter=False)
                init_state = [x, y, w, h]
                tracker.initialize(frame, _build_init_info(init_state))
                output_boxes.append(init_state)
                break
        while True:
            ret, frame = cap.read()
            if frame is None:
                break
            frame_disp = frame.copy()
            out = tracker.track(frame)
            state = [int(s) for s in out['target_bbox']]
            output_boxes.append(state)
            cv.rectangle(frame_disp, (state[0], state[1]), (state[2] + state[0], state[3] + state[1]), (0, 255, 0), 5)
            font_color = (0, 0, 0)
            cv.putText(frame_disp, 'Tracking!', (20, 30), cv.FONT_HERSHEY_COMPLEX_SMALL, 1, font_color, 1)
            cv.putText(frame_disp, 'Press r to reset', (20, 55), cv.FONT_HERSHEY_COMPLEX_SMALL, 1, font_color, 1)
            cv.putText(frame_disp, 'Press q to quit', (20, 80), cv.FONT_HERSHEY_COMPLEX_SMALL, 1, font_color, 1)
            cv.imshow(display_name, frame_disp)
            key = cv.waitKey(1)
            if key == ord('q'):
                break
            elif key == ord('r'):
                ret, frame = cap.read()
                frame_disp = frame.copy()
                cv.putText(frame_disp, 'Select target ROI and press ENTER', (20, 30), cv.FONT_HERSHEY_COMPLEX_SMALL, 1.5, (0, 0, 0), 1)
                cv.imshow(display_name, frame_disp)
                x, y, w, h = cv.selectROI(display_name, frame_disp, fromCenter=False)
                init_state = [x, y, w, h]
                tracker.initialize(frame, _build_init_info(init_state))
                output_boxes.append(init_state)
        cap.release()
        cv.destroyAllWindows()
        if save_results:
            if not os.path.exists(self.results_dir):
                os.makedirs(self.results_dir)
            video_name = Path(videofilepath).stem
            base_results_path = os.path.join(self.results_dir, 'video_{}'.format(video_name))
            tracked_bb = np.array(output_boxes).astype(int)
            bbox_file = '{}.txt'.format(base_results_path)
            np.savetxt(bbox_file, tracked_bb, delimiter='\t', fmt='%d')

    def get_parameters(self):
        """Get parameters."""
        param_module = importlib.import_module('lib.test.parameter.{}'.format(self.name))
        params = param_module.parameters(self.parameter_name)
        return params

    def _read_image(self, image_file: str):
        if isinstance(image_file, str):
            im = cv.imread(image_file)
            return cv.cvtColor(im, cv.COLOR_BGR2RGB)
        elif isinstance(image_file, list) and len(image_file) == 2:
            return decode_img(image_file[0], image_file[1])
        else:
            raise ValueError('type of image_file should be str or list')

def __init__(self, name: str, parameter_name: str, dataset_name: str, run_id: int=None, display_name: str=None, result_only=False):
    assert run_id is None or isinstance(run_id, int)
    self.name = name
    self.parameter_name = parameter_name
    self.dataset_name = dataset_name
    self.run_id = run_id
    self.display_name = display_name
    tracker_module_abspath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tracker', '%s.py' % self.name))
    if os.path.isfile(tracker_module_abspath):
        tracker_module = importlib.import_module('lib.test.tracker.{}'.format(self.name))
        self.tracker_class = tracker_module.get_tracker_class()
    else:
        self.tracker_class = None

def run_video(self, videofilepath, optional_box=None, debug=None, visdom_info=None, save_results=False):
    """Run the tracker with the vieofile.
        args:
            debug: Debug level.
        """
    params = self.get_parameters()
    debug_ = debug
    if debug is None:
        debug_ = getattr(params, 'debug', 0)
    params.debug = debug_
    params.tracker_name = self.name
    params.param_name = self.parameter_name
    multiobj_mode = getattr(params, 'multiobj_mode', getattr(self.tracker_class, 'multiobj_mode', 'default'))
    if multiobj_mode == 'default':
        tracker = self.create_tracker(params)
    elif multiobj_mode == 'parallel':
        tracker = MultiObjectWrapper(self.tracker_class, params, self.visdom, fast_load=True)
    else:
        raise ValueError('Unknown multi object mode {}'.format(multiobj_mode))
    assert os.path.isfile(videofilepath), 'Invalid param {}'.format(videofilepath)
    ', videofilepath must be a valid videofile'
    output_boxes = []
    cap = cv.VideoCapture(videofilepath)
    display_name = 'Display: ' + tracker.params.tracker_name
    cv.namedWindow(display_name, cv.WINDOW_NORMAL | cv.WINDOW_KEEPRATIO)
    cv.resizeWindow(display_name, 960, 720)
    success, frame = cap.read()
    cv.imshow(display_name, frame)

    def _build_init_info(box):
        return {'init_bbox': box}
    if success is not True:
        print('Read frame from {} failed.'.format(videofilepath))
        exit(-1)
    if optional_box is not None:
        assert isinstance(optional_box, (list, tuple))
        assert len(optional_box) == 4, "valid box's foramt is [x,y,w,h]"
        tracker.initialize(frame, _build_init_info(optional_box))
        output_boxes.append(optional_box)
    else:
        while True:
            frame_disp = frame.copy()
            cv.putText(frame_disp, 'Select target ROI and press ENTER', (20, 30), cv.FONT_HERSHEY_COMPLEX_SMALL, 1.5, (0, 0, 0), 1)
            x, y, w, h = cv.selectROI(display_name, frame_disp, fromCenter=False)
            init_state = [x, y, w, h]
            tracker.initialize(frame, _build_init_info(init_state))
            output_boxes.append(init_state)
            break
    while True:
        ret, frame = cap.read()
        if frame is None:
            break
        frame_disp = frame.copy()
        out = tracker.track(frame)
        state = [int(s) for s in out['target_bbox']]
        output_boxes.append(state)
        cv.rectangle(frame_disp, (state[0], state[1]), (state[2] + state[0], state[3] + state[1]), (0, 255, 0), 5)
        font_color = (0, 0, 0)
        cv.putText(frame_disp, 'Tracking!', (20, 30), cv.FONT_HERSHEY_COMPLEX_SMALL, 1, font_color, 1)
        cv.putText(frame_disp, 'Press r to reset', (20, 55), cv.FONT_HERSHEY_COMPLEX_SMALL, 1, font_color, 1)
        cv.putText(frame_disp, 'Press q to quit', (20, 80), cv.FONT_HERSHEY_COMPLEX_SMALL, 1, font_color, 1)
        cv.imshow(display_name, frame_disp)
        key = cv.waitKey(1)
        if key == ord('q'):
            break
        elif key == ord('r'):
            ret, frame = cap.read()
            frame_disp = frame.copy()
            cv.putText(frame_disp, 'Select target ROI and press ENTER', (20, 30), cv.FONT_HERSHEY_COMPLEX_SMALL, 1.5, (0, 0, 0), 1)
            cv.imshow(display_name, frame_disp)
            x, y, w, h = cv.selectROI(display_name, frame_disp, fromCenter=False)
            init_state = [x, y, w, h]
            tracker.initialize(frame, _build_init_info(init_state))
            output_boxes.append(init_state)
    cap.release()
    cv.destroyAllWindows()
    if save_results:
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)
        video_name = Path(videofilepath).stem
        base_results_path = os.path.join(self.results_dir, 'video_{}'.format(video_name))
        tracked_bb = np.array(output_boxes).astype(int)
        bbox_file = '{}.txt'.format(base_results_path)
        np.savetxt(bbox_file, tracked_bb, delimiter='\t', fmt='%d')

def get_parameters(self):
    """Get parameters."""
    param_module = importlib.import_module('lib.test.parameter.{}'.format(self.name))
    params = param_module.parameters(self.parameter_name)
    return params

def gen_config(config_file):
    cfg_dict = {}
    _edict2dict(cfg_dict, cfg)
    with open(config_file, 'w') as f:
        yaml.dump(cfg_dict, f, default_flow_style=False)

def update_config_from_file(filename, base_cfg=None):
    exp_config = None
    with open(filename) as f:
        exp_config = edict(yaml.safe_load(f))
        if base_cfg is not None:
            _update_config(base_cfg, exp_config)
        else:
            _update_config(cfg, exp_config)

def _create_vision_transformer(variant, pretrained=False, default_cfg=None, **kwargs):
    if kwargs.get('features_only', None):
        raise RuntimeError('features_only not implemented for Vision Transformer models.')
    model = VisionTransformer(**kwargs)
    if pretrained:
        if 'npz' in pretrained:
            model.load_pretrained(pretrained, prefix='')
        else:
            checkpoint = torch.load(pretrained, map_location='cpu')
            missing_keys, unexpected_keys = model.load_state_dict(checkpoint['model'], strict=False)
            print('Load pretrained model from: ' + pretrained)
    return model

def _create_vision_transformer(pretrained=False, **kwargs):
    model = VisionTransformerCE(**kwargs)
    if pretrained:
        if 'npz' in pretrained:
            model.load_pretrained(pretrained, prefix='')
        else:
            checkpoint = torch.load(pretrained, map_location='cpu')
            missing_keys, unexpected_keys = model.load_state_dict(checkpoint['model'], strict=False)
            print('Load pretrained model from: ' + pretrained)
    return model

def build_ostrack(cfg, training=True):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pretrained_path = os.path.join(current_dir, '../../../pretrained_models')
    if cfg.MODEL.PRETRAIN_FILE and 'OSTrack' not in cfg.MODEL.PRETRAIN_FILE and training:
        pretrained = os.path.join(pretrained_path, cfg.MODEL.PRETRAIN_FILE)
    else:
        pretrained = ''
    if cfg.MODEL.BACKBONE.TYPE == 'vit_base_patch16_224':
        backbone = vit_base_patch16_224(pretrained, drop_path_rate=cfg.TRAIN.DROP_PATH_RATE)
        hidden_dim = backbone.embed_dim
        patch_start_index = 1
    elif cfg.MODEL.BACKBONE.TYPE == 'vit_base_patch16_224_ce':
        backbone = vit_base_patch16_224_ce(pretrained, drop_path_rate=cfg.TRAIN.DROP_PATH_RATE, ce_loc=cfg.MODEL.BACKBONE.CE_LOC, ce_keep_ratio=cfg.MODEL.BACKBONE.CE_KEEP_RATIO)
        hidden_dim = backbone.embed_dim
        patch_start_index = 1
    elif cfg.MODEL.BACKBONE.TYPE == 'vit_large_patch16_224_ce':
        backbone = vit_large_patch16_224_ce(pretrained, drop_path_rate=cfg.TRAIN.DROP_PATH_RATE, ce_loc=cfg.MODEL.BACKBONE.CE_LOC, ce_keep_ratio=cfg.MODEL.BACKBONE.CE_KEEP_RATIO)
        hidden_dim = backbone.embed_dim
        patch_start_index = 1
    else:
        raise NotImplementedError
    backbone.finetune_track(cfg=cfg, patch_start_index=patch_start_index)
    box_head = build_box_head(cfg, hidden_dim)
    model = OSTrack(backbone, box_head, aux_loss=False, head_type=cfg.MODEL.HEAD.TYPE)
    if 'OSTrack' in cfg.MODEL.PRETRAIN_FILE and training:
        checkpoint = torch.load(cfg.MODEL.PRETRAIN_FILE, map_location='cpu')
        missing_keys, unexpected_keys = model.load_state_dict(checkpoint['net'], strict=False)
        print('Load pretrained model from: ' + cfg.MODEL.PRETRAIN_FILE)
    return model

def evaluate_vit(model, template, search):
    """Speed Test"""
    macs1, params1 = profile(model, inputs=(template, search), custom_ops=None, verbose=False)
    macs, params = clever_format([macs1, params1], '%.3f')
    print('overall macs is ', macs)
    print('overall params is ', params)
    T_w = 500
    T_t = 1000
    print('testing speed ...')
    torch.cuda.synchronize()
    with torch.no_grad():
        for i in range(T_w):
            _ = model(template, search)
        start = time.time()
        for i in range(T_t):
            _ = model(template, search)
        torch.cuda.synchronize()
        end = time.time()
        avg_lat = (end - start) / T_t
        print('The average overall latency is %.2f ms' % (avg_lat * 1000))
        print('FPS is %.2f fps' % (1.0 / avg_lat))

def evaluate_vit_separate(model, template, search):
    """Speed Test"""
    T_w = 50
    T_t = 1000
    print('testing speed ...')
    z = model.forward_backbone(template, image_type='template')
    x = model.forward_backbone(search, image_type='search')
    with torch.no_grad():
        for i in range(T_w):
            _ = model.forward_backbone(search, image_type='search')
            _ = model.forward_cat(z, x)
        start = time.time()
        for i in range(T_t):
            _ = model.forward_backbone(search, image_type='search')
            _ = model.forward_cat(z, x)
        end = time.time()
        avg_lat = (end - start) / T_t
        print('The average overall latency is %.2f ms' % (avg_lat * 1000))

def load_model_from_config(config, ckpt):
    print(f'Loading model from {ckpt}')
    pl_sd = torch.load(ckpt, map_location='cpu')
    global_step = pl_sd['global_step']
    sd = pl_sd['state_dict']
    model = instantiate_from_config(config.model)
    m, u = model.load_state_dict(sd, strict=False)
    model.cuda()
    model.eval()
    return ({'model': model}, global_step)

def get_model(mode):
    path_conf, path_ckpt = download_models(mode)
    config = OmegaConf.load(path_conf)
    model, step = load_model_from_config(config, path_ckpt)
    return model

def get_cond_options(mode):
    path = 'data/example_conditioning'
    path = os.path.join(path, mode)
    onlyfiles = [f for f in sorted(os.listdir(path))]
    return (path, onlyfiles)

def select_cond_path(mode):
    path = 'data/example_conditioning'
    path = os.path.join(path, mode)
    onlyfiles = [f for f in sorted(os.listdir(path))]
    selected = widgets.RadioButtons(options=onlyfiles, description='Select conditioning:', disabled=False)
    display(selected)
    selected_path = os.path.join(path, selected.value)
    return selected_path

class WrappedDataset(Dataset):
    """Wraps an arbitrary object with __len__ and __getitem__ into a pytorch dataset"""

    def __init__(self, dataset):
        self.data = dataset

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx]

def __len__(self):
    return len(self.data)

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

class CUDACallback(Callback):

    def on_train_epoch_start(self, trainer, pl_module):
        torch.cuda.reset_peak_memory_stats(trainer.root_gpu)
        torch.cuda.synchronize(trainer.root_gpu)
        self.start_time = time.time()

    def on_train_epoch_end(self, trainer, pl_module, outputs):
        torch.cuda.synchronize(trainer.root_gpu)
        max_memory = torch.cuda.max_memory_allocated(trainer.root_gpu) / 2 ** 20
        epoch_time = time.time() - self.start_time
        try:
            max_memory = trainer.training_type_plugin.reduce(max_memory)
            epoch_time = trainer.training_type_plugin.reduce(epoch_time)
            rank_zero_info(f'Average Epoch time: {epoch_time:.2f} seconds')
            rank_zero_info(f'Average Peak memory {max_memory:.2f}MiB')
        except AttributeError:
            pass

def on_train_epoch_start(self, trainer, pl_module):
    torch.cuda.reset_peak_memory_stats(trainer.root_gpu)
    torch.cuda.synchronize(trainer.root_gpu)
    self.start_time = time.time()

def on_train_epoch_end(self, trainer, pl_module, outputs):
    torch.cuda.synchronize(trainer.root_gpu)
    max_memory = torch.cuda.max_memory_allocated(trainer.root_gpu) / 2 ** 20
    epoch_time = time.time() - self.start_time
    try:
        max_memory = trainer.training_type_plugin.reduce(max_memory)
        epoch_time = trainer.training_type_plugin.reduce(epoch_time)
        rank_zero_info(f'Average Epoch time: {epoch_time:.2f} seconds')
        rank_zero_info(f'Average Peak memory {max_memory:.2f}MiB')
    except AttributeError:
        pass

def melk(*args, **kwargs):
    if trainer.global_rank == 0:
        print('Summoning checkpoint.')
        ckpt_path = os.path.join(ckptdir, 'last.ckpt')
        trainer.save_checkpoint(ckpt_path)

def load_model_from_config(config, ckpt, verbose=False):
    print(f'Loading model from {ckpt}')
    pl_sd = torch.load(ckpt, map_location='cpu')
    sd = pl_sd['state_dict']
    model = instantiate_from_config(config.model)
    m, u = model.load_state_dict(sd, strict=False)
    if len(m) > 0 and verbose:
        print('missing keys:')
        print(m)
    if len(u) > 0 and verbose:
        print('unexpected keys:')
        print(u)
    model.cuda()
    model.eval()
    return model

def load_single_file(saved_embeddings):
    compressed = np.load(saved_embeddings)
    database = {key: compressed[key] for key in compressed.files}
    return database

def load_multi_files(data_archive):
    database = {key: [] for key in data_archive[0].files}
    for d in tqdm(data_archive, desc=f'Loading datapool from {len(data_archive)} individual files.'):
        for key in d.files:
            database[key].append(d[key])
    return database

def load_datapool(dpath):

    def load_single_file(saved_embeddings):
        compressed = np.load(saved_embeddings)
        database = {key: compressed[key] for key in compressed.files}
        return database

    def load_multi_files(data_archive):
        database = {key: [] for key in data_archive[0].files}
        for d in tqdm(data_archive, desc=f'Loading datapool from {len(data_archive)} individual files.'):
            for key in d.files:
                database[key].append(d[key])
        return database
    print(f'Load saved patch embedding from "{dpath}"')
    file_content = glob.glob(os.path.join(dpath, '*.npz'))
    if len(file_content) == 1:
        data_pool = load_single_file(file_content[0])
    elif len(file_content) > 1:
        data = [np.load(f) for f in file_content]
        prefetched_data = parallel_data_prefetch(load_multi_files, data, n_proc=min(len(data), cpu_count()), target_data_type='dict')
        data_pool = {key: np.concatenate([od[key] for od in prefetched_data], axis=1)[0] for key in prefetched_data[0].keys()}
    else:
        raise ValueError(f'No npz-files in specified path "{dpath}" is this directory existing?')
    print(f'Finished loading of retrieval database of length {data_pool['embedding'].shape[0]}.')
    return data_pool

def logs2pil(logs, keys=['sample']):
    imgs = dict()
    for k in logs:
        try:
            if len(logs[k].shape) == 4:
                img = custom_to_pil(logs[k][0, ...])
            elif len(logs[k].shape) == 3:
                img = custom_to_pil(logs[k])
            else:
                print(f'Unknown format for key {k}. ')
                img = None
        except:
            img = None
        imgs[k] = img
    return imgs

def run(model, logdir, batch_size=50, vanilla=False, custom_steps=None, eta=None, n_samples=50000, nplog=None):
    if vanilla:
        print(f'Using Vanilla DDPM sampling with {model.num_timesteps} sampling steps.')
    else:
        print(f'Using DDIM sampling with {custom_steps} sampling steps and eta={eta}')
    tstart = time.time()
    n_saved = len(glob.glob(os.path.join(logdir, '*.png'))) - 1
    if model.cond_stage_model is None:
        all_images = []
        print(f'Running unconditional sampling for {n_samples} samples')
        for _ in trange(n_samples // batch_size, desc='Sampling Batches (unconditional)'):
            logs = make_convolutional_sample(model, batch_size=batch_size, vanilla=vanilla, custom_steps=custom_steps, eta=eta)
            n_saved = save_logs(logs, logdir, n_saved=n_saved, key='sample')
            all_images.extend([custom_to_np(logs['sample'])])
            if n_saved >= n_samples:
                print(f'Finish after generating {n_saved} samples')
                break
        all_img = np.concatenate(all_images, axis=0)
        all_img = all_img[:n_samples]
        shape_str = 'x'.join([str(x) for x in all_img.shape])
        nppath = os.path.join(nplog, f'{shape_str}-samples.npz')
        np.savez(nppath, all_img)
    else:
        raise NotImplementedError('Currently only sampling for unconditional models supported.')
    print(f'sampling of {n_saved} images finished in {(time.time() - tstart) / 60.0:.2f} minutes.')

def save_logs(logs, path, n_saved=0, key='sample', np_path=None):
    for k in logs:
        if k == key:
            batch = logs[key]
            if np_path is None:
                for x in batch:
                    img = custom_to_pil(x)
                    imgpath = os.path.join(path, f'{key}_{n_saved:06}.png')
                    img.save(imgpath)
                    n_saved += 1
            else:
                npbatch = custom_to_np(batch)
                shape_str = 'x'.join([str(x) for x in npbatch.shape])
                nppath = os.path.join(np_path, f'{n_saved}-{shape_str}-samples.npz')
                np.savez(nppath, npbatch)
                n_saved += npbatch.shape[0]
    return n_saved

def load_model(config, ckpt, gpu, eval_mode):
    if ckpt:
        print(f'Loading model from {ckpt}')
        pl_sd = torch.load(ckpt, map_location='cpu')
        global_step = pl_sd['global_step']
    else:
        pl_sd = {'state_dict': None}
        global_step = None
    model = load_model_from_config(config.model, pl_sd['state_dict'])
    return (model, global_step)

def load_model_from_config(config, ckpt, verbose=False):
    print(f'Loading model from {ckpt}')
    pl_sd = torch.load(ckpt, map_location='cpu')
    if 'global_step' in pl_sd:
        print(f'Global Step: {pl_sd['global_step']}')
    sd = pl_sd['state_dict']
    model = instantiate_from_config(config.model)
    m, u = model.load_state_dict(sd, strict=False)
    if len(m) > 0 and verbose:
        print('missing keys:')
        print(m)
    if len(u) > 0 and verbose:
        print('unexpected keys:')
        print(u)
    model.cuda()
    model.eval()
    return model

class Searcher(object):

    def __init__(self, database, retriever_version='ViT-L/14'):
        assert database in DATABASES
        self.database_name = database
        self.searcher_savedir = f'data/rdm/searchers/{self.database_name}'
        self.database_path = f'data/rdm/retrieval_databases/{self.database_name}'
        self.retriever = self.load_retriever(version=retriever_version)
        self.database = {'embedding': [], 'img_id': [], 'patch_coords': []}
        self.load_database()
        self.load_searcher()

    def train_searcher(self, k, metric='dot_product', searcher_savedir=None):
        print('Start training searcher')
        searcher = scann.scann_ops_pybind.builder(self.database['embedding'] / np.linalg.norm(self.database['embedding'], axis=1)[:, np.newaxis], k, metric)
        self.searcher = searcher.score_brute_force().build()
        print('Finish training searcher')
        if searcher_savedir is not None:
            print(f'Save trained searcher under "{searcher_savedir}"')
            os.makedirs(searcher_savedir, exist_ok=True)
            self.searcher.serialize(searcher_savedir)

    def load_single_file(self, saved_embeddings):
        compressed = np.load(saved_embeddings)
        self.database = {key: compressed[key] for key in compressed.files}
        print('Finished loading of clip embeddings.')

    def load_multi_files(self, data_archive):
        out_data = {key: [] for key in self.database}
        for d in tqdm(data_archive, desc=f'Loading datapool from {len(data_archive)} individual files.'):
            for key in d.files:
                out_data[key].append(d[key])
        return out_data

    def load_database(self):
        print(f'Load saved patch embedding from "{self.database_path}"')
        file_content = glob.glob(os.path.join(self.database_path, '*.npz'))
        if len(file_content) == 1:
            self.load_single_file(file_content[0])
        elif len(file_content) > 1:
            data = [np.load(f) for f in file_content]
            prefetched_data = parallel_data_prefetch(self.load_multi_files, data, n_proc=min(len(data), cpu_count()), target_data_type='dict')
            self.database = {key: np.concatenate([od[key] for od in prefetched_data], axis=1)[0] for key in self.database}
        else:
            raise ValueError(f'No npz-files in specified path "{self.database_path}" is this directory existing?')
        print(f'Finished loading of retrieval database of length {self.database['embedding'].shape[0]}.')

    def load_retriever(self, version='ViT-L/14'):
        model = FrozenClipImageEmbedder(model=version)
        if torch.cuda.is_available():
            model.cuda()
        model.eval()
        return model

    def load_searcher(self):
        print(f'load searcher for database {self.database_name} from {self.searcher_savedir}')
        self.searcher = scann.scann_ops_pybind.load_searcher(self.searcher_savedir)
        print('Finished loading searcher.')

    def search(self, x, k):
        if self.searcher is None and self.database['embedding'].shape[0] < 20000.0:
            self.train_searcher(k)
        assert self.searcher is not None, 'Cannot search with uninitialized searcher'
        if isinstance(x, torch.Tensor):
            x = x.detach().cpu().numpy()
        if len(x.shape) == 3:
            x = x[:, 0]
        query_embeddings = x / np.linalg.norm(x, axis=1)[:, np.newaxis]
        start = time.time()
        nns, distances = self.searcher.search_batched(query_embeddings, final_num_neighbors=k)
        end = time.time()
        out_embeddings = self.database['embedding'][nns]
        out_img_ids = self.database['img_id'][nns]
        out_pc = self.database['patch_coords'][nns]
        out = {'nn_embeddings': out_embeddings / np.linalg.norm(out_embeddings, axis=-1)[..., np.newaxis], 'img_ids': out_img_ids, 'patch_coords': out_pc, 'queries': x, 'exec_time': end - start, 'nns': nns, 'q_embeddings': query_embeddings}
        return out

    def __call__(self, x, n):
        return self.search(x, n)

def load_single_file(self, saved_embeddings):
    compressed = np.load(saved_embeddings)
    self.database = {key: compressed[key] for key in compressed.files}
    print('Finished loading of clip embeddings.')

def load_multi_files(self, data_archive):
    out_data = {key: [] for key in self.database}
    for d in tqdm(data_archive, desc=f'Loading datapool from {len(data_archive)} individual files.'):
        for key in d.files:
            out_data[key].append(d[key])
    return out_data

def load_database(self):
    print(f'Load saved patch embedding from "{self.database_path}"')
    file_content = glob.glob(os.path.join(self.database_path, '*.npz'))
    if len(file_content) == 1:
        self.load_single_file(file_content[0])
    elif len(file_content) > 1:
        data = [np.load(f) for f in file_content]
        prefetched_data = parallel_data_prefetch(self.load_multi_files, data, n_proc=min(len(data), cpu_count()), target_data_type='dict')
        self.database = {key: np.concatenate([od[key] for od in prefetched_data], axis=1)[0] for key in self.database}
    else:
        raise ValueError(f'No npz-files in specified path "{self.database_path}" is this directory existing?')
    print(f'Finished loading of retrieval database of length {self.database['embedding'].shape[0]}.')

class LambdaWarmUpCosineScheduler2:
    """
    supports repeated iterations, configurable via lists
    note: use with a base_lr of 1.0.
    """

    def __init__(self, warm_up_steps, f_min, f_max, f_start, cycle_lengths, verbosity_interval=0):
        assert len(warm_up_steps) == len(f_min) == len(f_max) == len(f_start) == len(cycle_lengths)
        self.lr_warm_up_steps = warm_up_steps
        self.f_start = f_start
        self.f_min = f_min
        self.f_max = f_max
        self.cycle_lengths = cycle_lengths
        self.cum_cycles = np.cumsum([0] + list(self.cycle_lengths))
        self.last_f = 0.0
        self.verbosity_interval = verbosity_interval

    def find_in_interval(self, n):
        interval = 0
        for cl in self.cum_cycles[1:]:
            if n <= cl:
                return interval
            interval += 1

    def schedule(self, n, **kwargs):
        cycle = self.find_in_interval(n)
        n = n - self.cum_cycles[cycle]
        if self.verbosity_interval > 0:
            if n % self.verbosity_interval == 0:
                print(f'current step: {n}, recent lr-multiplier: {self.last_f}, current cycle {cycle}')
        if n < self.lr_warm_up_steps[cycle]:
            f = (self.f_max[cycle] - self.f_start[cycle]) / self.lr_warm_up_steps[cycle] * n + self.f_start[cycle]
            self.last_f = f
            return f
        else:
            t = (n - self.lr_warm_up_steps[cycle]) / (self.cycle_lengths[cycle] - self.lr_warm_up_steps[cycle])
            t = min(t, 1.0)
            f = self.f_min[cycle] + 0.5 * (self.f_max[cycle] - self.f_min[cycle]) * (1 + np.cos(t * np.pi))
            self.last_f = f
            return f

    def __call__(self, n, **kwargs):
        return self.schedule(n, **kwargs)

def schedule(self, n, **kwargs):
    cycle = self.find_in_interval(n)
    n = n - self.cum_cycles[cycle]
    if self.verbosity_interval > 0:
        if n % self.verbosity_interval == 0:
            print(f'current step: {n}, recent lr-multiplier: {self.last_f}, current cycle {cycle}')
    if n < self.lr_warm_up_steps[cycle]:
        f = (self.f_max[cycle] - self.f_start[cycle]) / self.lr_warm_up_steps[cycle] * n + self.f_start[cycle]
        self.last_f = f
        return f
    else:
        t = (n - self.lr_warm_up_steps[cycle]) / (self.cycle_lengths[cycle] - self.lr_warm_up_steps[cycle])
        t = min(t, 1.0)
        f = self.f_min[cycle] + 0.5 * (self.f_max[cycle] - self.f_min[cycle]) * (1 + np.cos(t * np.pi))
        self.last_f = f
        return f

class LambdaLinearScheduler(LambdaWarmUpCosineScheduler2):

    def schedule(self, n, **kwargs):
        cycle = self.find_in_interval(n)
        n = n - self.cum_cycles[cycle]
        if self.verbosity_interval > 0:
            if n % self.verbosity_interval == 0:
                print(f'current step: {n}, recent lr-multiplier: {self.last_f}, current cycle {cycle}')
        if n < self.lr_warm_up_steps[cycle]:
            f = (self.f_max[cycle] - self.f_start[cycle]) / self.lr_warm_up_steps[cycle] * n + self.f_start[cycle]
            self.last_f = f
            return f
        else:
            f = self.f_min[cycle] + (self.f_max[cycle] - self.f_min[cycle]) * (self.cycle_lengths[cycle] - n) / self.cycle_lengths[cycle]
            self.last_f = f
            return f

def schedule(self, n, **kwargs):
    cycle = self.find_in_interval(n)
    n = n - self.cum_cycles[cycle]
    if self.verbosity_interval > 0:
        if n % self.verbosity_interval == 0:
            print(f'current step: {n}, recent lr-multiplier: {self.last_f}, current cycle {cycle}')
    if n < self.lr_warm_up_steps[cycle]:
        f = (self.f_max[cycle] - self.f_start[cycle]) / self.lr_warm_up_steps[cycle] * n + self.f_start[cycle]
        self.last_f = f
        return f
    else:
        f = self.f_min[cycle] + (self.f_max[cycle] - self.f_min[cycle]) * (self.cycle_lengths[cycle] - n) / self.cycle_lengths[cycle]
        self.last_f = f
        return f

def default(val, d):
    if exists(val):
        return val
    return d() if isfunction(d) else d

def mean_flat(tensor):
    """
    https://github.com/openai/guided-diffusion/blob/27c20a8fab9cb472df5d6bdd6c8d11c8f430b924/guided_diffusion/nn.py#L86
    Take the mean over all non-batch dimensions.
    """
    return tensor.mean(dim=list(range(1, len(tensor.shape))))

def get_obj_from_str(string, reload=False):
    module, cls = string.rsplit('.', 1)
    if reload:
        module_imp = importlib.import_module(module)
        importlib.reload(module_imp)
    return getattr(importlib.import_module(module, package=None), cls)

def default(val, d):
    if exists(val):
        return val
    return d() if isfunction(d) else d

def uniq(arr):
    return {el: True for el in arr}.keys()

def default(val, d):
    if exists(val):
        return val
    return d() if isfunction(d) else d

def get_timestamp():
    return datetime.now().strftime('%y%m%d-%H%M%S')

def get_image_paths(dataroot):
    paths = None
    if dataroot is not None:
        paths = sorted(_get_paths_from_images(dataroot))
    return paths

def _get_paths_from_images(path):
    assert os.path.isdir(path), '{:s} is not a valid directory'.format(path)
    images = []
    for dirpath, _, fnames in sorted(os.walk(path)):
        for fname in sorted(fnames):
            if is_image_file(fname):
                img_path = os.path.join(dirpath, fname)
                images.append(img_path)
    assert images, '{:s} has no valid image file'.format(path)
    return images

def patches_from_image(img, p_size=512, p_overlap=64, p_max=800):
    w, h = img.shape[:2]
    patches = []
    if w > p_max and h > p_max:
        w1 = list(np.arange(0, w - p_size, p_size - p_overlap, dtype=np.int))
        h1 = list(np.arange(0, h - p_size, p_size - p_overlap, dtype=np.int))
        w1.append(w - p_size)
        h1.append(h - p_size)
        for i in w1:
            for j in h1:
                patches.append(img[i:i + p_size, j:j + p_size, :])
    else:
        patches.append(img)
    return patches

def imssave(imgs, img_path):
    """
    imgs: list, N images of size WxHxC
    """
    img_name, ext = os.path.splitext(os.path.basename(img_path))
    for i, img in enumerate(imgs):
        if img.ndim == 3:
            img = img[:, :, [2, 1, 0]]
        new_path = os.path.join(os.path.dirname(img_path), img_name + str('_s{:04d}'.format(i)) + '.png')
        cv2.imwrite(new_path, img)

def split_imageset(original_dataroot, taget_dataroot, n_channels=3, p_size=800, p_overlap=96, p_max=1000):
    """
    split the large images from original_dataroot into small overlapped images with size (p_size)x(p_size),
    and save them into taget_dataroot; only the images with larger size than (p_max)x(p_max)
    will be splitted.
    Args:
        original_dataroot:
        taget_dataroot:
        p_size: size of small images
        p_overlap: patch size in training is a good choice
        p_max: images with smaller size than (p_max)x(p_max) keep unchanged.
    """
    paths = get_image_paths(original_dataroot)
    for img_path in paths:
        img = imread_uint(img_path, n_channels=n_channels)
        patches = patches_from_image(img, p_size, p_overlap, p_max)
        imssave(patches, os.path.join(taget_dataroot, os.path.basename(img_path)))

def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def mkdir_and_rename(path):
    if os.path.exists(path):
        new_name = path + '_archived_' + get_timestamp()
        print('Path already exists. Rename it to [{:s}]'.format(new_name))
        os.rename(path, new_name)
    os.makedirs(path)

def mean_flat(tensor):
    """
    Take the mean over all non-batch dimensions.
    """
    return tensor.mean(dim=list(range(1, len(tensor.shape))))

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

def read_yaml(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def dump_yaml(data, savepath):
    with open(os.path.join(savepath, 'config.yaml'), 'w') as outfile:
        yaml.dump(data, outfile, default_flow_style=False)

def check_and_mkdirs(path):
    if not os.path.exists(path):
        os.makedirs(path)

def generate_video(scene, prompt, save_images=False):
    video_output_path = os.path.join(scene.output_dir, scene.logging_name)
    check_and_mkdirs(video_output_path)
    filename = prompt.replace(' ', '_')[:40]
    fps = scene.fps
    print(colored('[Compositing video]', 'blue', attrs=['bold']), 'start...')
    writer = imageio.get_writer(os.path.join(video_output_path, f'{filename}.mp4'), fps=fps)
    for frame in tqdm(scene.final_video_frames):
        writer.append_data(frame)
    writer.close()
    if save_images:
        check_and_mkdirs(os.path.join(video_output_path, f'{filename}'))
        for i, img in enumerate(scene.final_video_frames):
            imageio.imsave(os.path.join(video_output_path, f'{filename}/{i}.png'), img)
    if not scene.save_cache:
        scene.clean_cache()
    print(colored('[Compositing video]', 'blue', attrs=['bold']), 'done.')

class DeletionAgent:

    def __init__(self, config):
        self.config = config
        self.inpaint_dir = config['inpaint_dir']
        self.video_inpaint_dir = config['video_inpaint_dir']

    def llm_finding_deletion(self, scene, message, scene_object_description):
        try:
            q0 = 'I will provide you with an operation statement and a dictionary containing information about cars in a scene. ' + ' You need to determine which car or cars should be deleted from the dictionary. '
            q1 = 'The dictionary is ' + str(scene_object_description)
            q2 = 'The keys of the dictionary are the car IDs, and the value is also a dictionary containing car detail, ' + 'including its image coordinate (u,v) in an image frame, depth, color in RGB.'
            q2 = "My statement may include information about the car's color or position. You should find out from my statement which cars should be deleted and return their car IDs"
            q3 = 'Note: (1) The definitions of u and v conform to the image coordinate system, u=0, v=0 represents the upper left corner. ' + "And the larger the 'u', the more to the right; And the larger the 'v', the more to the down. " + "(2) You can judge the distance by the 'depth'. The greater the depth, the farther the distance, the smaller the depth, the closer the distance." + '(3) The description of the color may not be absolutely accurate, choose the car with the closest color.'
            q4 = "You should return a JSON dictionary, with a key: 'removed_cars'." + " 'removed_cars' contains IDs of all the cars that meet the requirements. "
            q5 = 'Note that there is no need to return any code or explanations; only provide a JSON dictionary.'
            q6 = "If the dictionary is empty, 'removed_cars' should be an empty list "
            q7 = 'The requirement is :' + message
            prompt_list = [q0, q1, q2, q3, q4, q5, q6, q7]
            result = openai.ChatCompletion.create(model='gpt-4', messages=[{'role': 'system', 'content': 'You are an assistant helping me to assess and maintain information in a dictionary.'}] + [{'role': 'user', 'content': q} for q in prompt_list])
            answer = result['choices'][0]['message']['content']
            print(f'{colored('[Deletion Agent LLM] finding the car to delete', color='magenta', attrs=['bold'])}                     \n{colored('[Raw Response>>>]', attrs=['bold'])} {answer}')
            start = answer.index('{')
            answer = answer[start:]
            end = answer.rfind('}')
            answer = answer[:end + 1]
            deletion_car_ids = eval(answer)['removed_cars']
            print(f'{colored('[Extracted Response>>>]', attrs=['bold'])} {deletion_car_ids} \n')
        except Exception as e:
            print(e)
            traceback.print_exc()
            print('[Deletion Agent LLM] finding the car to delete fails')
            return []
        return deletion_car_ids

    def llm_putting_back_deletion(self, scene, message, scene_object_description):
        try:
            deleted_object_dict = {k: v for k, v in scene_object_description.items() if k in scene.removed_cars}
            q0 = 'I will provide you with a dictionary in which each key is a vehicle id, and each value is the description of the vehicle in the image.'
            q1 = "Specifically, description of the vehicle is also a dictionary. It has keys: (1) vehicle's u in image coordinate (2) vehicle's v in image coordinate (3) vehicle color in RGB. (4) vehicle's depth from viewpoint"
            q2 = 'The definitions of u and v conform to the image coordinate system, u=0, v=0 represents the upper left corner. ' + "The larger the 'u', the more to the right; And the larger the 'v', the more to the down. "
            q3 = 'I will get you a requirement, and I want you can follow this requirement and take out all the relavant vehicle ids from the dictionary.'
            q4 = f'Now the dictionary is {deleted_object_dict}, and my requirement is {message}. My requirement may contain extraneous verb descriptions or the wrong singular and plural expression, please ignore.'
            q5 = "Note that you should return a JSON dictionary, the key is 'selected_vehicle', the value includes the vehicle ids. DO NOT return anything else. I'm not asking you to write code."
            prompt_list = [q0, q1, q2, q3, q4, q5]
            result = openai.ChatCompletion.create(model='gpt-4', messages=[{'role': 'system', 'content': 'You are an assistant helping me maintain and return dictionaries.'}] + [{'role': 'user', 'content': q} for q in prompt_list])
            answer = result['choices'][0]['message']['content']
            print(f'{colored('[Deletion Agent LLM] finding the car to be put back', color='magenta', attrs=['bold'])}                      \n{colored('[Raw Response>>>]', attrs=['bold'])} {answer}')
            start = answer.index('{')
            answer = answer[start:]
            end = answer.rfind('}')
            answer = answer[:end + 1]
            put_back_car_ids = eval(answer)['selected_vehicle']
            print(f'{colored('[Extracted Response>>>]', attrs=['bold'])} {put_back_car_ids} \n')
        except Exception as e:
            print(e)
            traceback.print_exc()
            print('[Deletion Agent LLM] finding the car to be put back fails')
        return put_back_car_ids

    def func_inpaint_scene(self, scene):
        """
        Call inpainting, store results in scene.current_inpainted_images

        if no scene.removed_cars
            just return

        """
        if len(scene.removed_cars) == 0:
            print(f'{colored('[Inpaint]', 'green', attrs=['bold'])} No inpainting.')
            scene.current_inpainted_images = scene.current_images
            return
        current_dir = os.getcwd()
        inpaint_input_path = os.path.join(current_dir, scene.cache_dir, 'inpaint_input')
        inpaint_output_path = os.path.join(current_dir, scene.cache_dir, 'inpaint_output')
        check_and_mkdirs(inpaint_input_path)
        check_and_mkdirs(inpaint_output_path)
        if scene.is_ego_motion is False:
            print(f'{colored('[Inpaint]', 'green', attrs=['bold'])} is_ego_motion is False, inpainting one frame.')
            all_mask = self.func_get_mask(scene)
            img = scene.current_images[0]
            masked_img = copy.deepcopy(img)
            if scene.is_wide_angle:
                masked_img = cv2.resize(masked_img, (1152, 256))
            else:
                masked_img = cv2.resize(masked_img, (512, 384))
            imageio.imwrite(os.path.join(inpaint_input_path, 'img.png'), masked_img.astype(np.uint8))
            imageio.imwrite(os.path.join(inpaint_input_path, 'img_mask.png'), all_mask.astype(np.uint8))
            current_dir = os.getcwd()
            os.chdir(self.inpaint_dir)
            os.system(f'python scripts/inpaint.py --indir {inpaint_input_path} --outdir {inpaint_output_path}')
            os.chdir(current_dir)
            new_img = imageio.imread(os.path.join(inpaint_output_path, 'img.png'))
            new_img = cv2.resize(new_img, (scene.width, scene.height))
            all_mask_in_ori_resolution = cv2.resize(all_mask, (scene.width, scene.height)).reshape(scene.height, scene.width, 1).repeat(3, axis=2)
            new_img = np.where(all_mask_in_ori_resolution == 0, scene.current_images[0], new_img)
            scene.current_inpainted_images = [new_img] * scene.frames
        else:
            print(f'{colored('[Inpaint]', 'green', attrs=['bold'])} is_ego_motion is True, inpainting multiple frame (as video).')
            mask_list = []
            for i in range(scene.frames):
                current_frame_mask = np.zeros((scene.height, scene.width))
                for car_id in scene.bbox_data.keys():
                    if scene.bbox_car_id_to_name[car_id] in scene.removed_cars:
                        corners = generate_vertices(scene.bbox_data[car_id])
                        mask, mask_corners = get_outlines(corners, transform_nerf2opencv_convention(scene.current_extrinsics[i]), scene.intrinsics, scene.height, scene.width)
                        current_frame_mask[mask == 1] = 1
                mask_list.append(current_frame_mask)
            np.save(f'{self.video_inpaint_dir}/chatsim/masks.npy', mask_list)
            np.save(f'{self.video_inpaint_dir}/chatsim/current_images.npy', scene.current_images)
            current_dir = os.getcwd()
            os.chdir(self.video_inpaint_dir)
            os.system(f'python remove_anything_video_npy.py                         --dilate_kernel_size 15                         --lama_config lama/configs/prediction/default.yaml                         --lama_ckpt ./pretrained_models/big-lama                         --tracker_ckpt vitb_384_mae_ce_32x4_ep300                         --vi_ckpt ./pretrained_models/sttn.pth                         --mask_idx 2                         --fps 25')
            os.chdir(current_dir)
            print(f'{colored('[Inpaint]', 'green', attrs=['bold'])} Video Inpainting Done!')
            inpainted_images = np.load(f'{self.video_inpaint_dir}/chatsim/inpainted_imgs.npy', allow_pickle=True)
            scene.current_inpainted_images = [np.array(image) for image in inpainted_images]

    def func_get_mask(self, scene):
        masks = []
        extrinsic_for_project = transform_nerf2opencv_convention(scene.current_extrinsics[0])
        for car_name in scene.removed_cars:
            car_id = scene.name_to_bbox_car_id[car_name]
            corners = generate_vertices(scene.bbox_data[car_id])
            mask, _ = get_outlines(corners, extrinsic_for_project, scene.intrinsics, scene.height, scene.width)
            mask *= 255
            masks.append(mask)
        mask = np.max(np.stack(masks), axis=0)
        if scene.is_wide_angle:
            mask = cv2.resize(mask, (1152, 256))
        else:
            mask = cv2.resize(mask, (512, 384))
        return mask

def func_inpaint_scene(self, scene):
    """
        Call inpainting, store results in scene.current_inpainted_images

        if no scene.removed_cars
            just return

        """
    if len(scene.removed_cars) == 0:
        print(f'{colored('[Inpaint]', 'green', attrs=['bold'])} No inpainting.')
        scene.current_inpainted_images = scene.current_images
        return
    current_dir = os.getcwd()
    inpaint_input_path = os.path.join(current_dir, scene.cache_dir, 'inpaint_input')
    inpaint_output_path = os.path.join(current_dir, scene.cache_dir, 'inpaint_output')
    check_and_mkdirs(inpaint_input_path)
    check_and_mkdirs(inpaint_output_path)
    if scene.is_ego_motion is False:
        print(f'{colored('[Inpaint]', 'green', attrs=['bold'])} is_ego_motion is False, inpainting one frame.')
        all_mask = self.func_get_mask(scene)
        img = scene.current_images[0]
        masked_img = copy.deepcopy(img)
        if scene.is_wide_angle:
            masked_img = cv2.resize(masked_img, (1152, 256))
        else:
            masked_img = cv2.resize(masked_img, (512, 384))
        imageio.imwrite(os.path.join(inpaint_input_path, 'img.png'), masked_img.astype(np.uint8))
        imageio.imwrite(os.path.join(inpaint_input_path, 'img_mask.png'), all_mask.astype(np.uint8))
        current_dir = os.getcwd()
        os.chdir(self.inpaint_dir)
        os.system(f'python scripts/inpaint.py --indir {inpaint_input_path} --outdir {inpaint_output_path}')
        os.chdir(current_dir)
        new_img = imageio.imread(os.path.join(inpaint_output_path, 'img.png'))
        new_img = cv2.resize(new_img, (scene.width, scene.height))
        all_mask_in_ori_resolution = cv2.resize(all_mask, (scene.width, scene.height)).reshape(scene.height, scene.width, 1).repeat(3, axis=2)
        new_img = np.where(all_mask_in_ori_resolution == 0, scene.current_images[0], new_img)
        scene.current_inpainted_images = [new_img] * scene.frames
    else:
        print(f'{colored('[Inpaint]', 'green', attrs=['bold'])} is_ego_motion is True, inpainting multiple frame (as video).')
        mask_list = []
        for i in range(scene.frames):
            current_frame_mask = np.zeros((scene.height, scene.width))
            for car_id in scene.bbox_data.keys():
                if scene.bbox_car_id_to_name[car_id] in scene.removed_cars:
                    corners = generate_vertices(scene.bbox_data[car_id])
                    mask, mask_corners = get_outlines(corners, transform_nerf2opencv_convention(scene.current_extrinsics[i]), scene.intrinsics, scene.height, scene.width)
                    current_frame_mask[mask == 1] = 1
            mask_list.append(current_frame_mask)
        np.save(f'{self.video_inpaint_dir}/chatsim/masks.npy', mask_list)
        np.save(f'{self.video_inpaint_dir}/chatsim/current_images.npy', scene.current_images)
        current_dir = os.getcwd()
        os.chdir(self.video_inpaint_dir)
        os.system(f'python remove_anything_video_npy.py                         --dilate_kernel_size 15                         --lama_config lama/configs/prediction/default.yaml                         --lama_ckpt ./pretrained_models/big-lama                         --tracker_ckpt vitb_384_mae_ce_32x4_ep300                         --vi_ckpt ./pretrained_models/sttn.pth                         --mask_idx 2                         --fps 25')
        os.chdir(current_dir)
        print(f'{colored('[Inpaint]', 'green', attrs=['bold'])} Video Inpainting Done!')
        inpainted_images = np.load(f'{self.video_inpaint_dir}/chatsim/inpainted_imgs.npy', allow_pickle=True)
        scene.current_inpainted_images = [np.array(image) for image in inpainted_images]

def func_get_mask(self, scene):
    masks = []
    extrinsic_for_project = transform_nerf2opencv_convention(scene.current_extrinsics[0])
    for car_name in scene.removed_cars:
        car_id = scene.name_to_bbox_car_id[car_name]
        corners = generate_vertices(scene.bbox_data[car_id])
        mask, _ = get_outlines(corners, extrinsic_for_project, scene.intrinsics, scene.height, scene.width)
        mask *= 255
        masks.append(mask)
    mask = np.max(np.stack(masks), axis=0)
    if scene.is_wide_angle:
        mask = cv2.resize(mask, (1152, 256))
    else:
        mask = cv2.resize(mask, (512, 384))
    return mask

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

def func_generate_extrinsic(self, scene, start_frame_idx, end_frame_idx):
    scene.current_extrinsics = inter_poses(scene.nerf_motion_extrinsics[start_frame_idx:end_frame_idx:3], scene.frames)

class ForegroundRenderingAgent:

    def __init__(self, config):
        self.config = config
        self.blender_dir = config['blender_dir']
        self.blender_utils_dir = config['blender_utils_dir']
        self.skydome_hdri_dir = config['skydome_hdri_dir']
        self.skydome_hdri_idx = config['skydome_hdri_idx']
        self.use_surrounding_lighting = config['use_surrounding_lighting']
        self.is_wide_angle = config['nerf_config']['is_wide_angle']
        self.scene_name = config['nerf_config']['scene_name']
        self.f2nerf_dir = config['nerf_config']['f2nerf_dir']
        self.nerf_exp_name = config['nerf_config']['nerf_exp_name']
        self.f2nerf_config = config['nerf_config']['f2nerf_config']
        self.dataset_name = config['nerf_config']['dataset_name']
        self.nerf_exp_dir = os.path.join(self.f2nerf_dir, 'exp', self.scene_name, self.nerf_exp_name)
        nerf_output_foler_name = 'wide_angle_novel_images' if self.is_wide_angle else 'novel_images'
        self.nerf_novel_view_dir = os.path.join(self.nerf_exp_dir, nerf_output_foler_name)
        self.nerf_quiet_render = config['nerf_config']['nerf_quiet_render']
        self.estimate_depth = config['estimate_depth']
        if self.estimate_depth:
            from segment_anything import SamAutomaticMaskGenerator, sam_model_registry
            self.depth_est_method = config['depth_est']['method']
            self.sam_checkpoint = config['depth_est']['SAM']['ckpt']
            self.sam_model_type = config['depth_est']['SAM']['model_type']
            sam = sam_model_registry[self.sam_model_type](checkpoint=self.sam_checkpoint).cuda()
            self.mask_generator = SamAutomaticMaskGenerator(sam)

    def func_blender_add_cars(self, scene):
        """
        use blender to add cars for multiple frames. Static image is one frame.

        call self.blender_add_cars_single_frame in multi processing
        """
        check_and_mkdirs(os.path.join(scene.cache_dir, 'blender_npz'))
        check_and_mkdirs(os.path.join(scene.cache_dir, 'blender_output'))
        check_and_mkdirs(os.path.join(scene.cache_dir, 'blender_yaml'))
        check_and_mkdirs(os.path.join(scene.cache_dir, 'spatial_varying_hdri'))
        output_path = os.path.join(scene.cache_dir, 'blender_output')
        if len(scene.added_cars_dict) > 0:
            scene.check_added_car_static()
            real_render_frames = 1 if scene.add_car_all_static else scene.frames
            print(f'{colored('[Blender]', 'magenta', attrs=['bold'])} Start rendering {real_render_frames} images.')
            print(f'see the log in {os.path.join(scene.cache_dir, 'rendering_log')} if save_cache is enabled')
            background_depth_list = []
            if self.estimate_depth:
                real_update_frames = scene.frames if scene.is_ego_motion else 1
                if self.depth_est_method == 'SAM':
                    background_depth_list = self.update_depth_batch_SAM(scene, scene.current_images[:real_update_frames])
                else:
                    raise NotImplementedError
                print(f'{colored('[Depth Estimation]', 'cyan', attrs=['bold'])} Finish depth estimation {real_update_frames} images.')
            print('preparing input files for blender rendering')
            for frame_id in tqdm(range(real_render_frames)):
                self.func_blender_add_cars_prepare_files_single_frame(scene, frame_id, background_depth_list)
            print(f'start rendering in parallel, process number is {scene.multi_process_num}.')
            print('This may take a few minutes. To speed up the foreground rendering, you can lower the `frames` number or render not-wide images.')
            print('If you find the results are incomplete or missing, that may due to OOM. You can reduce the multi_process_num in config yaml.')
            print('You can also check the log file for debugging with `save_cache` enabled in the yaml.')
            self.func_parallel_blender_rendering(scene)
            print(f'{colored('[Blender]', 'magenta', attrs=['bold'])} Finish rendering {real_render_frames} images.')
            for frame_id in range(real_render_frames, scene.frames):
                assert real_render_frames == 1
                source_blender_output_folder = f'{output_path}/0'
                target_blender_output_folder = f'{output_path}/{frame_id}'
                shutil.copytree(source_blender_output_folder, target_blender_output_folder, dirs_exist_ok=True)
            print(f'{colored('[Blender]', 'magenta', attrs=['bold'])} Copying Remaining {scene.frames - real_render_frames} images.')
            video_frames = []
            for frame_id in range(scene.frames):
                video_frame_file = os.path.join(scene.cache_dir, 'blender_output', str(frame_id), 'RGB_composite.png')
                img = imageio.imread(video_frame_file)
                video_frames.append(img)
        else:
            video_frames = scene.current_inpainted_images
        scene.final_video_frames = video_frames

    def func_blender_add_cars_prepare_files_single_frame(self, scene, frame_id, background_depth_list):
        np.savez(os.path.join(scene.cache_dir, 'blender_npz', f'{frame_id}.npz'), H=scene.height, W=scene.width, focal=scene.focal, rgb=scene.current_inpainted_images[frame_id], depth=background_depth_list[frame_id] if len(background_depth_list) > 0 else 1000, extrinsic=transform_nerf2opencv_convention(scene.current_extrinsics[frame_id]))
        car_list_for_blender = []
        for car_name, car_info in scene.added_cars_dict.items():
            car_blender_file = car_info['blender_file']
            car_list_for_blender.append({'new_obj_name': car_name, 'blender_file': car_blender_file, 'insert_pos': [car_info['motion'][frame_id, 0].tolist(), car_info['motion'][frame_id, 1].tolist(), 0], 'insert_rot': [0, 0, car_info['motion'][frame_id, 2].tolist()], 'model_obj_name': 'Car', **({'target_color': {'material_key': 'car_paint', 'color': [i / 255 for i in car_info['color']] + [1]}} if car_info['color'] != 'default' else {})})
        yaml_path = os.path.join(scene.cache_dir, 'blender_yaml', f'{frame_id}.yaml')
        output_path = os.path.join(scene.cache_dir, 'blender_output')
        skydome_hdri_path = os.path.join(self.skydome_hdri_dir, self.scene_name, f'{self.skydome_hdri_idx}.exr')
        final_hdri_path = skydome_hdri_path
        if self.use_surrounding_lighting:
            print(f'{colored('[Blender]', 'magenta', attrs=['bold'])} Generating Spatial Varying HDRI.')
            assert len(scene.added_cars_dict) == 1
            car_info = list(scene.added_cars_dict.values())[0]
            insert_x = car_info['motion'][frame_id, 0].tolist()
            insert_y = car_info['motion'][frame_id, 1].tolist()
            generate_rays(insert_x, insert_y, scene.ext_int_path, self.nerf_exp_dir)
            current_dir = os.getcwd()
            os.chdir(self.f2nerf_dir)
            print(f'{colored('[Mc-NeRF]', 'red', attrs=['bold'])} Generating Panorama.')
            render_command = f'python scripts/run.py                                     --config-name={self.f2nerf_config} dataset_name={self.dataset_name}                                     case_name={self.scene_name}                                     exp_name={self.nerf_exp_name}                                     mode=render_panorama_shutter                                     is_continue=true                                     +work_dir={os.getcwd()}'
            if self.nerf_quiet_render:
                render_command += ' > /dev/null 2>&1'
            os.system(render_command)
            os.chdir(current_dir)
            nerf_last_trans_file = os.path.join(self.nerf_exp_dir, 'last_trans.pt')
            nerf_panorama_dir = os.path.join(self.nerf_exp_dir, 'panorama')
            nerf_panorama_pngs = os.listdir(nerf_panorama_dir)
            assert len(nerf_panorama_pngs) == 1
            nerf_panorama_pt_file = os.path.join(self.nerf_exp_dir, 'nerf_panorama.pt')
            arbitray_H = 128
            sky_mask = np.zeros((arbitray_H, arbitray_H * 4, 3))
            nerf_env_panorama = torch.jit.load(nerf_panorama_pt_file).state_dict()['0'].cpu().numpy()
            nerf_last_trans = torch.jit.load(nerf_last_trans_file).state_dict()['0'].cpu().numpy()
            pure_sky_hdri_path = skydome_hdri_path.replace('.exr', '_sky.exr')
            sky_dome_panorama = imageio.imread(pure_sky_hdri_path)
            print(f'{colored('[Blender]', 'magenta', attrs=['bold'])} Merging HDRI')
            blending_panorama = blending_hdr_sky(nerf_env_panorama, sky_dome_panorama, nerf_last_trans, sky_mask)
            nerf_env_panorama_gamma_corrected = (srgb_gamma_correction(nerf_env_panorama) * 255).astype(np.uint8)
            sky_dome_panorama_gamma_corrected = (srgb_gamma_correction(sky_dome_panorama) * 255).astype(np.uint8)
            blending_hdr_sky_gamma_corrected = (srgb_gamma_correction(blending_panorama) * 255).astype(np.uint8)
            final_hdri_path = os.path.join(scene.cache_dir, 'spatial_varying_hdri', f'{frame_id}.exr')
            imageio.imwrite(final_hdri_path.replace('.exr', '_env.png'), nerf_env_panorama_gamma_corrected)
            imageio.imwrite(final_hdri_path.replace('.exr', '_sky.png'), sky_dome_panorama_gamma_corrected)
            imageio.imwrite(final_hdri_path.replace('.exr', '_blending.png'), blending_hdr_sky_gamma_corrected)
            sky_H, sky_W, _ = blending_panorama.shape
            blending_panorama_full = np.zeros((sky_H * 2, sky_W, 3))
            blending_panorama_full[:sky_H] = blending_panorama
            imageio.imwrite(final_hdri_path, blending_panorama_full.astype(np.float32))
            print(f'{colored('[Blender]', 'magenta', attrs=['bold'])} Finish Merging HDRI')
        blender_dict = {'render_name': str(frame_id), 'output_dir': output_path, 'scene_file': os.path.join(scene.cache_dir, 'blender_npz', f'{frame_id}.npz'), 'hdri_file': final_hdri_path, 'render_downsample': 2, 'cars': car_list_for_blender, 'depth_and_occlusion': scene.depth_and_occlusion, 'backup_hdri': scene.backup_hdri}
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(data=blender_dict, stream=f, allow_unicode=True)

    def func_compose_with_new_depth_single_frame(self, scene, frame_id):
        output_path = os.path.join(scene.cache_dir, 'blender_output')
        background_image = imageio.imread(os.path.join(output_path, str(frame_id), 'backup', 'RGB.png'))
        depth_map = np.load(f'{output_path}/{frame_id}/depth/background_depth.npy')
        sys.path.append(os.path.join(self.blender_utils_dir, 'postprocess'))
        import compose
        compose.compose(os.path.join(output_path, str(frame_id)), background_image, depth_map, 2)

    def func_parallel_blender_rendering(self, scene):
        multi_process_num = scene.multi_process_num
        log_dir = os.path.join(scene.cache_dir, 'rendering_log')
        check_and_mkdirs(os.path.join(scene.cache_dir, 'rendering_log'))
        frames = scene.frames
        segment_length = frames // multi_process_num
        processes = []
        for i in range(multi_process_num):
            start_frame = i * segment_length
            end_frame = (i + 1) * segment_length if i < multi_process_num - 1 else frames
            log_file = os.path.join(log_dir, f'{i}.txt')
            command = f'{self.blender_dir} -b --python {self.blender_utils_dir}/main_multicar.py -- {os.path.join(scene.cache_dir, 'blender_yaml')} -- {start_frame} -- {end_frame} > {log_file}'
            with open(log_file, 'w') as f:
                process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                processes.append(process)
        for process in processes:
            stdout, stderr = process.communicate()

    def get_sparse_depth_from_LiDAR(self, scene, frame_id):
        extrinsic_opencv = transform_nerf2opencv_convention(scene.current_extrinsics[frame_id])
        pointcloud_world = np.concatenate((scene.pcd, np.ones((scene.pcd.shape[0], 1))), axis=1).T
        pointcloud_camera = (np.linalg.inv(extrinsic_opencv) @ pointcloud_world)[:3]
        pointcloud_image = (scene.intrinsics @ pointcloud_camera)[:2] / pointcloud_camera[2:3]
        z_positive = pointcloud_camera[2] > 0
        valid_points = (pointcloud_image[0] > 0) & (pointcloud_image[0] < scene.width) & (pointcloud_image[1] > 0) & (pointcloud_image[1] < scene.height) & z_positive
        pointcloud_image_valid = pointcloud_image[:, valid_points]
        valid_u_coord = pointcloud_image_valid[0].astype(np.int32)
        valid_v_coord = pointcloud_image_valid[1].astype(np.int32)
        sparse_depth_map = np.zeros((scene.height, scene.width))
        sparse_depth_map[valid_v_coord, valid_u_coord] = pointcloud_camera[2, valid_points]
        return sparse_depth_map

    def update_depth_batch_SAM(self, scene, image_list):
        """
        update depth batch use [SAM] + [LiDAR projection correction] to get instance-level depth

        Args:
            image_list : list of np.ndarray, len = 1 or scene.frames
                image is [H, W, 3] shape

        Returns:
            overlap_depth_list : list of np.array, len = 1 or scene.frames
                depth is [H, W] shape
        """
        real_update_frames = len(image_list)
        overlap_depth_list = []
        for frame_id in range(real_update_frames):
            output_path = os.path.join(scene.cache_dir, 'blender_output')
            rendered_car_mask = imageio.imread(f'{output_path}/{frame_id}/mask/vehicle_and_shadow0001.exr')
            rendered_car_mask = cv2.resize(rendered_car_mask, (scene.current_inpainted_images[frame_id].shape[1], scene.current_inpainted_images[frame_id].shape[0]))
            rendered_car_mask = rendered_car_mask[..., 0] > 20 / 255
            masks = self.mask_generator.generate(scene.current_inpainted_images[frame_id])
            num_masks = len(masks)
            import itertools
            mask_pairs = list(itertools.permutations(range(num_masks), 2))
            valid_mask_idx = np.ones(num_masks, dtype=bool)
            for pair in mask_pairs:
                mask_1 = masks[pair[0]]
                mask_2 = masks[pair[1]]
                if (mask_1['segmentation'] & mask_2['segmentation']).sum() > 0:
                    if mask_1['area'] < mask_2['area']:
                        valid_mask_idx[pair[0]] = False
                    else:
                        valid_mask_idx[pair[1]] = False
            idx = np.where(valid_mask_idx == True)[0]
            masks = [masks[i] for i in idx]
            sparse_depth_map = self.get_sparse_depth_from_LiDAR(scene, frame_id)
            sparse_depth_mask = sparse_depth_map != 0
            overlap_depth = np.ones((scene.height, scene.width)) * 500
            for i in range(len(masks)):
                intersection_area = masks[i]['segmentation'] & rendered_car_mask
                if intersection_area.sum() > 0:
                    intersection_area_with_depth = intersection_area & sparse_depth_mask
                    if intersection_area_with_depth.sum() > 0 and intersection_area_with_depth.sum() > 10:
                        avg_depth = sparse_depth_map[intersection_area_with_depth].mean()
                        min_depth = sparse_depth_map[intersection_area_with_depth].min()
                        max_depth = sparse_depth_map[intersection_area_with_depth].max()
                        median_depth = np.median(sparse_depth_map[intersection_area_with_depth])
                        overlap_depth[intersection_area] = avg_depth
            overlap_depth_list.append(overlap_depth.astype(np.float32))
        return overlap_depth_list

def __init__(self, config):
    self.config = config
    self.blender_dir = config['blender_dir']
    self.blender_utils_dir = config['blender_utils_dir']
    self.skydome_hdri_dir = config['skydome_hdri_dir']
    self.skydome_hdri_idx = config['skydome_hdri_idx']
    self.use_surrounding_lighting = config['use_surrounding_lighting']
    self.is_wide_angle = config['nerf_config']['is_wide_angle']
    self.scene_name = config['nerf_config']['scene_name']
    self.f2nerf_dir = config['nerf_config']['f2nerf_dir']
    self.nerf_exp_name = config['nerf_config']['nerf_exp_name']
    self.f2nerf_config = config['nerf_config']['f2nerf_config']
    self.dataset_name = config['nerf_config']['dataset_name']
    self.nerf_exp_dir = os.path.join(self.f2nerf_dir, 'exp', self.scene_name, self.nerf_exp_name)
    nerf_output_foler_name = 'wide_angle_novel_images' if self.is_wide_angle else 'novel_images'
    self.nerf_novel_view_dir = os.path.join(self.nerf_exp_dir, nerf_output_foler_name)
    self.nerf_quiet_render = config['nerf_config']['nerf_quiet_render']
    self.estimate_depth = config['estimate_depth']
    if self.estimate_depth:
        from segment_anything import SamAutomaticMaskGenerator, sam_model_registry
        self.depth_est_method = config['depth_est']['method']
        self.sam_checkpoint = config['depth_est']['SAM']['ckpt']
        self.sam_model_type = config['depth_est']['SAM']['model_type']
        sam = sam_model_registry[self.sam_model_type](checkpoint=self.sam_checkpoint).cuda()
        self.mask_generator = SamAutomaticMaskGenerator(sam)

def func_blender_add_cars(self, scene):
    """
        use blender to add cars for multiple frames. Static image is one frame.

        call self.blender_add_cars_single_frame in multi processing
        """
    check_and_mkdirs(os.path.join(scene.cache_dir, 'blender_npz'))
    check_and_mkdirs(os.path.join(scene.cache_dir, 'blender_output'))
    check_and_mkdirs(os.path.join(scene.cache_dir, 'blender_yaml'))
    check_and_mkdirs(os.path.join(scene.cache_dir, 'spatial_varying_hdri'))
    output_path = os.path.join(scene.cache_dir, 'blender_output')
    if len(scene.added_cars_dict) > 0:
        scene.check_added_car_static()
        real_render_frames = 1 if scene.add_car_all_static else scene.frames
        print(f'{colored('[Blender]', 'magenta', attrs=['bold'])} Start rendering {real_render_frames} images.')
        print(f'see the log in {os.path.join(scene.cache_dir, 'rendering_log')} if save_cache is enabled')
        background_depth_list = []
        if self.estimate_depth:
            real_update_frames = scene.frames if scene.is_ego_motion else 1
            if self.depth_est_method == 'SAM':
                background_depth_list = self.update_depth_batch_SAM(scene, scene.current_images[:real_update_frames])
            else:
                raise NotImplementedError
            print(f'{colored('[Depth Estimation]', 'cyan', attrs=['bold'])} Finish depth estimation {real_update_frames} images.')
        print('preparing input files for blender rendering')
        for frame_id in tqdm(range(real_render_frames)):
            self.func_blender_add_cars_prepare_files_single_frame(scene, frame_id, background_depth_list)
        print(f'start rendering in parallel, process number is {scene.multi_process_num}.')
        print('This may take a few minutes. To speed up the foreground rendering, you can lower the `frames` number or render not-wide images.')
        print('If you find the results are incomplete or missing, that may due to OOM. You can reduce the multi_process_num in config yaml.')
        print('You can also check the log file for debugging with `save_cache` enabled in the yaml.')
        self.func_parallel_blender_rendering(scene)
        print(f'{colored('[Blender]', 'magenta', attrs=['bold'])} Finish rendering {real_render_frames} images.')
        for frame_id in range(real_render_frames, scene.frames):
            assert real_render_frames == 1
            source_blender_output_folder = f'{output_path}/0'
            target_blender_output_folder = f'{output_path}/{frame_id}'
            shutil.copytree(source_blender_output_folder, target_blender_output_folder, dirs_exist_ok=True)
        print(f'{colored('[Blender]', 'magenta', attrs=['bold'])} Copying Remaining {scene.frames - real_render_frames} images.')
        video_frames = []
        for frame_id in range(scene.frames):
            video_frame_file = os.path.join(scene.cache_dir, 'blender_output', str(frame_id), 'RGB_composite.png')
            img = imageio.imread(video_frame_file)
            video_frames.append(img)
    else:
        video_frames = scene.current_inpainted_images
    scene.final_video_frames = video_frames

def func_blender_add_cars_prepare_files_single_frame(self, scene, frame_id, background_depth_list):
    np.savez(os.path.join(scene.cache_dir, 'blender_npz', f'{frame_id}.npz'), H=scene.height, W=scene.width, focal=scene.focal, rgb=scene.current_inpainted_images[frame_id], depth=background_depth_list[frame_id] if len(background_depth_list) > 0 else 1000, extrinsic=transform_nerf2opencv_convention(scene.current_extrinsics[frame_id]))
    car_list_for_blender = []
    for car_name, car_info in scene.added_cars_dict.items():
        car_blender_file = car_info['blender_file']
        car_list_for_blender.append({'new_obj_name': car_name, 'blender_file': car_blender_file, 'insert_pos': [car_info['motion'][frame_id, 0].tolist(), car_info['motion'][frame_id, 1].tolist(), 0], 'insert_rot': [0, 0, car_info['motion'][frame_id, 2].tolist()], 'model_obj_name': 'Car', **({'target_color': {'material_key': 'car_paint', 'color': [i / 255 for i in car_info['color']] + [1]}} if car_info['color'] != 'default' else {})})
    yaml_path = os.path.join(scene.cache_dir, 'blender_yaml', f'{frame_id}.yaml')
    output_path = os.path.join(scene.cache_dir, 'blender_output')
    skydome_hdri_path = os.path.join(self.skydome_hdri_dir, self.scene_name, f'{self.skydome_hdri_idx}.exr')
    final_hdri_path = skydome_hdri_path
    if self.use_surrounding_lighting:
        print(f'{colored('[Blender]', 'magenta', attrs=['bold'])} Generating Spatial Varying HDRI.')
        assert len(scene.added_cars_dict) == 1
        car_info = list(scene.added_cars_dict.values())[0]
        insert_x = car_info['motion'][frame_id, 0].tolist()
        insert_y = car_info['motion'][frame_id, 1].tolist()
        generate_rays(insert_x, insert_y, scene.ext_int_path, self.nerf_exp_dir)
        current_dir = os.getcwd()
        os.chdir(self.f2nerf_dir)
        print(f'{colored('[Mc-NeRF]', 'red', attrs=['bold'])} Generating Panorama.')
        render_command = f'python scripts/run.py                                     --config-name={self.f2nerf_config} dataset_name={self.dataset_name}                                     case_name={self.scene_name}                                     exp_name={self.nerf_exp_name}                                     mode=render_panorama_shutter                                     is_continue=true                                     +work_dir={os.getcwd()}'
        if self.nerf_quiet_render:
            render_command += ' > /dev/null 2>&1'
        os.system(render_command)
        os.chdir(current_dir)
        nerf_last_trans_file = os.path.join(self.nerf_exp_dir, 'last_trans.pt')
        nerf_panorama_dir = os.path.join(self.nerf_exp_dir, 'panorama')
        nerf_panorama_pngs = os.listdir(nerf_panorama_dir)
        assert len(nerf_panorama_pngs) == 1
        nerf_panorama_pt_file = os.path.join(self.nerf_exp_dir, 'nerf_panorama.pt')
        arbitray_H = 128
        sky_mask = np.zeros((arbitray_H, arbitray_H * 4, 3))
        nerf_env_panorama = torch.jit.load(nerf_panorama_pt_file).state_dict()['0'].cpu().numpy()
        nerf_last_trans = torch.jit.load(nerf_last_trans_file).state_dict()['0'].cpu().numpy()
        pure_sky_hdri_path = skydome_hdri_path.replace('.exr', '_sky.exr')
        sky_dome_panorama = imageio.imread(pure_sky_hdri_path)
        print(f'{colored('[Blender]', 'magenta', attrs=['bold'])} Merging HDRI')
        blending_panorama = blending_hdr_sky(nerf_env_panorama, sky_dome_panorama, nerf_last_trans, sky_mask)
        nerf_env_panorama_gamma_corrected = (srgb_gamma_correction(nerf_env_panorama) * 255).astype(np.uint8)
        sky_dome_panorama_gamma_corrected = (srgb_gamma_correction(sky_dome_panorama) * 255).astype(np.uint8)
        blending_hdr_sky_gamma_corrected = (srgb_gamma_correction(blending_panorama) * 255).astype(np.uint8)
        final_hdri_path = os.path.join(scene.cache_dir, 'spatial_varying_hdri', f'{frame_id}.exr')
        imageio.imwrite(final_hdri_path.replace('.exr', '_env.png'), nerf_env_panorama_gamma_corrected)
        imageio.imwrite(final_hdri_path.replace('.exr', '_sky.png'), sky_dome_panorama_gamma_corrected)
        imageio.imwrite(final_hdri_path.replace('.exr', '_blending.png'), blending_hdr_sky_gamma_corrected)
        sky_H, sky_W, _ = blending_panorama.shape
        blending_panorama_full = np.zeros((sky_H * 2, sky_W, 3))
        blending_panorama_full[:sky_H] = blending_panorama
        imageio.imwrite(final_hdri_path, blending_panorama_full.astype(np.float32))
        print(f'{colored('[Blender]', 'magenta', attrs=['bold'])} Finish Merging HDRI')
    blender_dict = {'render_name': str(frame_id), 'output_dir': output_path, 'scene_file': os.path.join(scene.cache_dir, 'blender_npz', f'{frame_id}.npz'), 'hdri_file': final_hdri_path, 'render_downsample': 2, 'cars': car_list_for_blender, 'depth_and_occlusion': scene.depth_and_occlusion, 'backup_hdri': scene.backup_hdri}
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(data=blender_dict, stream=f, allow_unicode=True)

def func_compose_with_new_depth_single_frame(self, scene, frame_id):
    output_path = os.path.join(scene.cache_dir, 'blender_output')
    background_image = imageio.imread(os.path.join(output_path, str(frame_id), 'backup', 'RGB.png'))
    depth_map = np.load(f'{output_path}/{frame_id}/depth/background_depth.npy')
    sys.path.append(os.path.join(self.blender_utils_dir, 'postprocess'))
    import compose
    compose.compose(os.path.join(output_path, str(frame_id)), background_image, depth_map, 2)

def func_parallel_blender_rendering(self, scene):
    multi_process_num = scene.multi_process_num
    log_dir = os.path.join(scene.cache_dir, 'rendering_log')
    check_and_mkdirs(os.path.join(scene.cache_dir, 'rendering_log'))
    frames = scene.frames
    segment_length = frames // multi_process_num
    processes = []
    for i in range(multi_process_num):
        start_frame = i * segment_length
        end_frame = (i + 1) * segment_length if i < multi_process_num - 1 else frames
        log_file = os.path.join(log_dir, f'{i}.txt')
        command = f'{self.blender_dir} -b --python {self.blender_utils_dir}/main_multicar.py -- {os.path.join(scene.cache_dir, 'blender_yaml')} -- {start_frame} -- {end_frame} > {log_file}'
        with open(log_file, 'w') as f:
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            processes.append(process)
    for process in processes:
        stdout, stderr = process.communicate()

def get_sparse_depth_from_LiDAR(self, scene, frame_id):
    extrinsic_opencv = transform_nerf2opencv_convention(scene.current_extrinsics[frame_id])
    pointcloud_world = np.concatenate((scene.pcd, np.ones((scene.pcd.shape[0], 1))), axis=1).T
    pointcloud_camera = (np.linalg.inv(extrinsic_opencv) @ pointcloud_world)[:3]
    pointcloud_image = (scene.intrinsics @ pointcloud_camera)[:2] / pointcloud_camera[2:3]
    z_positive = pointcloud_camera[2] > 0
    valid_points = (pointcloud_image[0] > 0) & (pointcloud_image[0] < scene.width) & (pointcloud_image[1] > 0) & (pointcloud_image[1] < scene.height) & z_positive
    pointcloud_image_valid = pointcloud_image[:, valid_points]
    valid_u_coord = pointcloud_image_valid[0].astype(np.int32)
    valid_v_coord = pointcloud_image_valid[1].astype(np.int32)
    sparse_depth_map = np.zeros((scene.height, scene.width))
    sparse_depth_map[valid_v_coord, valid_u_coord] = pointcloud_camera[2, valid_points]
    return sparse_depth_map

def update_depth_batch_SAM(self, scene, image_list):
    """
        update depth batch use [SAM] + [LiDAR projection correction] to get instance-level depth

        Args:
            image_list : list of np.ndarray, len = 1 or scene.frames
                image is [H, W, 3] shape

        Returns:
            overlap_depth_list : list of np.array, len = 1 or scene.frames
                depth is [H, W] shape
        """
    real_update_frames = len(image_list)
    overlap_depth_list = []
    for frame_id in range(real_update_frames):
        output_path = os.path.join(scene.cache_dir, 'blender_output')
        rendered_car_mask = imageio.imread(f'{output_path}/{frame_id}/mask/vehicle_and_shadow0001.exr')
        rendered_car_mask = cv2.resize(rendered_car_mask, (scene.current_inpainted_images[frame_id].shape[1], scene.current_inpainted_images[frame_id].shape[0]))
        rendered_car_mask = rendered_car_mask[..., 0] > 20 / 255
        masks = self.mask_generator.generate(scene.current_inpainted_images[frame_id])
        num_masks = len(masks)
        import itertools
        mask_pairs = list(itertools.permutations(range(num_masks), 2))
        valid_mask_idx = np.ones(num_masks, dtype=bool)
        for pair in mask_pairs:
            mask_1 = masks[pair[0]]
            mask_2 = masks[pair[1]]
            if (mask_1['segmentation'] & mask_2['segmentation']).sum() > 0:
                if mask_1['area'] < mask_2['area']:
                    valid_mask_idx[pair[0]] = False
                else:
                    valid_mask_idx[pair[1]] = False
        idx = np.where(valid_mask_idx == True)[0]
        masks = [masks[i] for i in idx]
        sparse_depth_map = self.get_sparse_depth_from_LiDAR(scene, frame_id)
        sparse_depth_mask = sparse_depth_map != 0
        overlap_depth = np.ones((scene.height, scene.width)) * 500
        for i in range(len(masks)):
            intersection_area = masks[i]['segmentation'] & rendered_car_mask
            if intersection_area.sum() > 0:
                intersection_area_with_depth = intersection_area & sparse_depth_mask
                if intersection_area_with_depth.sum() > 0 and intersection_area_with_depth.sum() > 10:
                    avg_depth = sparse_depth_map[intersection_area_with_depth].mean()
                    min_depth = sparse_depth_map[intersection_area_with_depth].min()
                    max_depth = sparse_depth_map[intersection_area_with_depth].max()
                    median_depth = np.median(sparse_depth_map[intersection_area_with_depth])
                    overlap_depth[intersection_area] = avg_depth
        overlap_depth_list.append(overlap_depth.astype(np.float32))
    return overlap_depth_list

class BackgroundRendering3DGSAgent:

    def __init__(self, config):
        self.config = config
        self.is_wide_angle = config['nerf_config']['is_wide_angle']
        self.gs_dir = config['gs_config']['gs_dir']
        self.model_folder = os.path.join(config['gs_config']['gs_dir'], config['gs_config']['output_folder'], config['gs_config']['gs_model_name'])
        self.gs_novel_view_dir = os.path.join(self.model_folder, 'chatsim_novel_views')

    def func_render_background(self, scene):
        """
        Call the NeRF, store results in scene.current_images
        """
        scene.is_ego_motion = not np.all(scene.current_extrinsics == scene.current_extrinsics[0])
        if scene.is_ego_motion:
            print(f'{colored('[Background Gaussian Splatting]', 'red', attrs=['bold'])} is_ego_motion is True, rendering multiple frames')
            camera_extrinsics = scene.current_extrinsics[:, :3, :]
            camera_intrinsics = scene.intrinsics
        else:
            print(f'{colored('[Background Gaussian Splatting]', 'red', attrs=['bold'])} is_ego_motion is False, rendering one frame')
            camera_extrinsics = scene.current_extrinsics[0:1, :3, :]
            camera_intrinsics = scene.intrinsics
        np.savez(os.path.join(self.model_folder, 'chatsim_extint.npz'), camera_extrinsics=camera_extrinsics, camera_intrinsics=camera_intrinsics, H=scene.height, W=scene.width)
        if os.path.exists(self.gs_novel_view_dir) and len(os.listdir(self.gs_novel_view_dir)) > 0:
            os.system(f'rm -r {self.gs_novel_view_dir}/*')
        current_dir = os.getcwd()
        os.chdir(self.gs_dir)
        render_command = f'python render_chatsim.py                             --model_path {self.model_folder}'
        os.system(render_command)
        os.chdir(current_dir)
        scene.current_images = []
        img_rendered_pkls = os.listdir(self.gs_novel_view_dir)
        assert len(img_rendered_pkls) == 1, f'the folder has {len(img_rendered_pkls)} files'
        img_rendered_pkl = os.path.join(self.gs_novel_view_dir, img_rendered_pkls[0])
        with open(img_rendered_pkl, 'rb') as f:
            scene.current_images = pickle.load(f)
        if not scene.is_ego_motion:
            scene.current_images = scene.current_images * scene.frames

def __init__(self, config):
    self.config = config
    self.is_wide_angle = config['nerf_config']['is_wide_angle']
    self.gs_dir = config['gs_config']['gs_dir']
    self.model_folder = os.path.join(config['gs_config']['gs_dir'], config['gs_config']['output_folder'], config['gs_config']['gs_model_name'])
    self.gs_novel_view_dir = os.path.join(self.model_folder, 'chatsim_novel_views')

def func_render_background(self, scene):
    """
        Call the NeRF, store results in scene.current_images
        """
    scene.is_ego_motion = not np.all(scene.current_extrinsics == scene.current_extrinsics[0])
    if scene.is_ego_motion:
        print(f'{colored('[Background Gaussian Splatting]', 'red', attrs=['bold'])} is_ego_motion is True, rendering multiple frames')
        camera_extrinsics = scene.current_extrinsics[:, :3, :]
        camera_intrinsics = scene.intrinsics
    else:
        print(f'{colored('[Background Gaussian Splatting]', 'red', attrs=['bold'])} is_ego_motion is False, rendering one frame')
        camera_extrinsics = scene.current_extrinsics[0:1, :3, :]
        camera_intrinsics = scene.intrinsics
    np.savez(os.path.join(self.model_folder, 'chatsim_extint.npz'), camera_extrinsics=camera_extrinsics, camera_intrinsics=camera_intrinsics, H=scene.height, W=scene.width)
    if os.path.exists(self.gs_novel_view_dir) and len(os.listdir(self.gs_novel_view_dir)) > 0:
        os.system(f'rm -r {self.gs_novel_view_dir}/*')
    current_dir = os.getcwd()
    os.chdir(self.gs_dir)
    render_command = f'python render_chatsim.py                             --model_path {self.model_folder}'
    os.system(render_command)
    os.chdir(current_dir)
    scene.current_images = []
    img_rendered_pkls = os.listdir(self.gs_novel_view_dir)
    assert len(img_rendered_pkls) == 1, f'the folder has {len(img_rendered_pkls)} files'
    img_rendered_pkl = os.path.join(self.gs_novel_view_dir, img_rendered_pkls[0])
    with open(img_rendered_pkl, 'rb') as f:
        scene.current_images = pickle.load(f)
    if not scene.is_ego_motion:
        scene.current_images = scene.current_images * scene.frames

class BackgroundRenderingAgent:

    def __init__(self, config):
        self.config = config
        self.is_wide_angle = config['nerf_config']['is_wide_angle']
        self.scene_name = config['nerf_config']['scene_name']
        self.f2nerf_dir = config['nerf_config']['f2nerf_dir']
        self.nerf_exp_name = config['nerf_config']['nerf_exp_name']
        self.f2nerf_config = config['nerf_config']['f2nerf_config']
        self.dataset_name = config['nerf_config']['dataset_name']
        self.nerf_mode = config['nerf_config']['rendering_mode']
        self.nerf_exp_dir = os.path.join(self.f2nerf_dir, 'exp', self.scene_name, self.nerf_exp_name)
        self.nerf_data_dir = os.path.join(self.f2nerf_dir, 'data', self.dataset_name, self.scene_name)
        nerf_output_foler_name = 'wide_angle_novel_images' if self.is_wide_angle else 'novel_images'
        self.nerf_novel_view_dir = os.path.join(self.nerf_exp_dir, nerf_output_foler_name)
        self.nerf_quiet_render = config['nerf_config']['nerf_quiet_render']
        if self.is_wide_angle:
            assert 'wide' in self.nerf_mode
        else:
            assert 'wide' not in self.nerf_mode

    def func_render_background(self, scene):
        """
        Call the NeRF, store results in scene.current_images
        """
        scene.is_ego_motion = not np.all(scene.current_extrinsics == scene.current_extrinsics[0])
        if scene.is_ego_motion:
            print(f'{colored('[Mc-NeRF]', 'red', attrs=['bold'])} is_ego_motion is True, rendering multiple frames')
            poses_render = scene.current_extrinsics[:, :3, :]
            np.save(os.path.join(self.nerf_data_dir, 'poses_render.npy'), poses_render)
            if os.path.exists(self.nerf_novel_view_dir) and len(os.listdir(self.nerf_novel_view_dir)) > 0:
                os.system(f'rm -r {self.nerf_novel_view_dir}/*')
            current_dir = os.getcwd()
            os.chdir(self.f2nerf_dir)
            render_command = f'python scripts/run.py                                 --config-name={self.f2nerf_config}                                 dataset_name={self.dataset_name}                                 case_name={self.scene_name}                                 exp_name={self.nerf_exp_name}                                 mode={self.nerf_mode}                                 is_continue=true                                 +work_dir={os.getcwd()}'
            if self.nerf_quiet_render:
                render_command += ' > /dev/null 2>&1'
            os.system(render_command)
            os.chdir(current_dir)
            scene.current_images = []
            img_path_list = os.listdir(self.nerf_novel_view_dir)
            img_path_list.sort(key=lambda x: int(x[:-4]))
            for img_path in img_path_list:
                scene.current_images.append(imageio.imread(os.path.join(self.nerf_novel_view_dir, img_path))[:, :scene.width])
        else:
            print(f'{colored('[Mc-NeRF]', 'red', attrs=['bold'])} is_ego_motion is False, rendering one frame')
            poses_render = scene.current_extrinsics[0:1, :3, :]
            np.save(os.path.join(self.nerf_data_dir, 'poses_render.npy'), poses_render)
            current_dir = os.getcwd()
            os.chdir(self.f2nerf_dir)
            render_command = f'python scripts/run.py                                 --config-name={self.f2nerf_config}                                 dataset_name={self.dataset_name}                                 case_name={self.scene_name}                                 exp_name={self.nerf_exp_name}                                 mode={self.nerf_mode}                                 is_continue=true                                 +work_dir={os.getcwd()}'
            if self.nerf_quiet_render:
                render_command += ' > /dev/null 2>&1'
            os.system(render_command)
            os.chdir(current_dir)
            novel_image = imageio.imread(os.path.join(self.nerf_novel_view_dir, '50000_000.png'))[:, :scene.width]
            scene.current_images = [novel_image] * scene.frames

def __init__(self, config):
    self.config = config
    self.is_wide_angle = config['nerf_config']['is_wide_angle']
    self.scene_name = config['nerf_config']['scene_name']
    self.f2nerf_dir = config['nerf_config']['f2nerf_dir']
    self.nerf_exp_name = config['nerf_config']['nerf_exp_name']
    self.f2nerf_config = config['nerf_config']['f2nerf_config']
    self.dataset_name = config['nerf_config']['dataset_name']
    self.nerf_mode = config['nerf_config']['rendering_mode']
    self.nerf_exp_dir = os.path.join(self.f2nerf_dir, 'exp', self.scene_name, self.nerf_exp_name)
    self.nerf_data_dir = os.path.join(self.f2nerf_dir, 'data', self.dataset_name, self.scene_name)
    nerf_output_foler_name = 'wide_angle_novel_images' if self.is_wide_angle else 'novel_images'
    self.nerf_novel_view_dir = os.path.join(self.nerf_exp_dir, nerf_output_foler_name)
    self.nerf_quiet_render = config['nerf_config']['nerf_quiet_render']
    if self.is_wide_angle:
        assert 'wide' in self.nerf_mode
    else:
        assert 'wide' not in self.nerf_mode

def func_render_background(self, scene):
    """
        Call the NeRF, store results in scene.current_images
        """
    scene.is_ego_motion = not np.all(scene.current_extrinsics == scene.current_extrinsics[0])
    if scene.is_ego_motion:
        print(f'{colored('[Mc-NeRF]', 'red', attrs=['bold'])} is_ego_motion is True, rendering multiple frames')
        poses_render = scene.current_extrinsics[:, :3, :]
        np.save(os.path.join(self.nerf_data_dir, 'poses_render.npy'), poses_render)
        if os.path.exists(self.nerf_novel_view_dir) and len(os.listdir(self.nerf_novel_view_dir)) > 0:
            os.system(f'rm -r {self.nerf_novel_view_dir}/*')
        current_dir = os.getcwd()
        os.chdir(self.f2nerf_dir)
        render_command = f'python scripts/run.py                                 --config-name={self.f2nerf_config}                                 dataset_name={self.dataset_name}                                 case_name={self.scene_name}                                 exp_name={self.nerf_exp_name}                                 mode={self.nerf_mode}                                 is_continue=true                                 +work_dir={os.getcwd()}'
        if self.nerf_quiet_render:
            render_command += ' > /dev/null 2>&1'
        os.system(render_command)
        os.chdir(current_dir)
        scene.current_images = []
        img_path_list = os.listdir(self.nerf_novel_view_dir)
        img_path_list.sort(key=lambda x: int(x[:-4]))
        for img_path in img_path_list:
            scene.current_images.append(imageio.imread(os.path.join(self.nerf_novel_view_dir, img_path))[:, :scene.width])
    else:
        print(f'{colored('[Mc-NeRF]', 'red', attrs=['bold'])} is_ego_motion is False, rendering one frame')
        poses_render = scene.current_extrinsics[0:1, :3, :]
        np.save(os.path.join(self.nerf_data_dir, 'poses_render.npy'), poses_render)
        current_dir = os.getcwd()
        os.chdir(self.f2nerf_dir)
        render_command = f'python scripts/run.py                                 --config-name={self.f2nerf_config}                                 dataset_name={self.dataset_name}                                 case_name={self.scene_name}                                 exp_name={self.nerf_exp_name}                                 mode={self.nerf_mode}                                 is_continue=true                                 +work_dir={os.getcwd()}'
        if self.nerf_quiet_render:
            render_command += ' > /dev/null 2>&1'
        os.system(render_command)
        os.chdir(current_dir)
        novel_image = imageio.imread(os.path.join(self.nerf_novel_view_dir, '50000_000.png'))[:, :scene.width]
        scene.current_images = [novel_image] * scene.frames

class HoliCitySDRDataset(Dataset):

    def __init__(self, args, split='train'):
        self.multicrop_dir = args['multicrop_dir']
        self.skymask_dir = args['skymask_dir']
        self.skyldr_dir = args['skyldr_dir']
        self.skyhdr_dir = args['skyhdr_dir']
        selected_sample_json = args['selected_sample_json']
        view_args = args['view_setting']
        self.crop_H = view_args['camera_H'] // view_args['downsample_for_crop']
        self.crop_W = view_args['camera_W'] // view_args['downsample_for_crop']
        self.camera_vfov = np.degrees(np.arctan2(view_args['camera_H'] / 2, view_args['focal'])) * 2
        self.aspect_ratio = view_args['camera_W'] / view_args['camera_H']
        self.view_num = view_args['view_num']
        self.view_dis_deg = view_args['view_dis']
        self.sky_pano_H = args['sky_pano_H']
        self.sky_pano_W = args['sky_pano_W']
        with open(selected_sample_json, 'r') as f:
            self.select_sample = json.load(f)
        random.seed(303)
        random.shuffle(self.select_sample)
        all_sample_num = len(self.select_sample)
        train_ratio = 0.8
        self.train_file_list = self.select_sample[:int(all_sample_num * train_ratio)]
        self.val_file_list = self.select_sample[int(all_sample_num * train_ratio):]
        self.is_train = split == 'train'
        if self.is_train:
            self.file_list = self.train_file_list
        else:
            self.file_list = self.val_file_list
        self.aug_rotation = True if self.is_train else False

    def __len__(self):
        return len(self.file_list)

    def __getitem__(self, idx):
        sky_ldr_path = os.path.join(self.skyldr_dir, self.file_list[idx])
        sky_mask_path = os.path.join(self.skymask_dir, self.file_list[idx])
        sky_hdr_path = os.path.join(self.skyhdr_dir, self.file_list[idx].replace('.jpg', '.npz'))
        ldr_skypano = imread(sky_ldr_path) / 255
        sky_mask = imread(sky_mask_path).astype(np.float32) / 255
        sky_hdr_dict = np.load(sky_hdr_path)
        peak_vector = sky_hdr_dict['peak_vector']
        latent_vector = sky_hdr_dict['latent_vector']
        hdr_skypano = sky_hdr_dict['hdr_skypano']
        ldr_envmap = EnvironmentMap(ldr_skypano, 'skylatlong')
        hdr_envmap = EnvironmentMap(hdr_skypano, 'skylatlong')
        mask_envmap = EnvironmentMap(sky_mask, 'skylatlong')
        if self.aug_rotation:
            azimuth_deg = choice(range(0, 360, 45))
            azimuth_rad = np.radians(azimuth_deg)
            rotation_mat = rotation_matrix(azimuth=azimuth_rad, elevation=0)
            inv_rotation_mat = rotation_matrix(azimuth=-azimuth_rad, elevation=0)
        else:
            azimuth_deg = 0
        img_crops_tensor_list = []
        for i in range(self.view_num):
            azimuth_deg_i = (azimuth_deg + self.view_dis_deg[i]) % 360
            azimuth_deg_i = int(azimuth_deg_i)
            img_crop_path = os.path.join(self.multicrop_dir, str(azimuth_deg_i), self.file_list[idx])
            img_crop = imread(img_crop_path) / 255
            img_crops_tensor_list.append(totensor(img_crop))
        if self.aug_rotation:
            hdr_envmap.rotate(dcm=inv_rotation_mat)
            mask_envmap.rotate(dcm=inv_rotation_mat)
            ldr_envmap.rotate(dcm=inv_rotation_mat)
            peak_vector[:3] = (rotation_mat @ peak_vector[:3].reshape(3, 1)).flatten()
        img_crops_tensor = torch.stack(img_crops_tensor_list)
        peak_vector_tensor = totensor(peak_vector)
        latent_vector_tensor = totensor(latent_vector)
        mask_envmap_tensor = totensor(mask_envmap.data)
        hdr_envmap_tensor = totensor(hdr_envmap.data)
        ldr_envmap_tensor = totensor(ldr_envmap.data)
        return (img_crops_tensor, peak_vector_tensor, latent_vector_tensor, mask_envmap_tensor, hdr_envmap_tensor, ldr_envmap_tensor)

def __init__(self, args, split='train'):
    self.multicrop_dir = args['multicrop_dir']
    self.skymask_dir = args['skymask_dir']
    self.skyldr_dir = args['skyldr_dir']
    self.skyhdr_dir = args['skyhdr_dir']
    selected_sample_json = args['selected_sample_json']
    view_args = args['view_setting']
    self.crop_H = view_args['camera_H'] // view_args['downsample_for_crop']
    self.crop_W = view_args['camera_W'] // view_args['downsample_for_crop']
    self.camera_vfov = np.degrees(np.arctan2(view_args['camera_H'] / 2, view_args['focal'])) * 2
    self.aspect_ratio = view_args['camera_W'] / view_args['camera_H']
    self.view_num = view_args['view_num']
    self.view_dis_deg = view_args['view_dis']
    self.sky_pano_H = args['sky_pano_H']
    self.sky_pano_W = args['sky_pano_W']
    with open(selected_sample_json, 'r') as f:
        self.select_sample = json.load(f)
    random.seed(303)
    random.shuffle(self.select_sample)
    all_sample_num = len(self.select_sample)
    train_ratio = 0.8
    self.train_file_list = self.select_sample[:int(all_sample_num * train_ratio)]
    self.val_file_list = self.select_sample[int(all_sample_num * train_ratio):]
    self.is_train = split == 'train'
    if self.is_train:
        self.file_list = self.train_file_list
    else:
        self.file_list = self.val_file_list
    self.aug_rotation = True if self.is_train else False

def __len__(self):
    return len(self.file_list)

class HDRSkyDataset(Dataset):

    def __init__(self, args, split='train'):
        root_dir = args['root_dir']
        downsample = args['downsample']
        self.sky_H = args['image_H'] // downsample // 2
        self.sky_W = args['image_W'] // downsample
        self.root_dir = os.path.join(root_dir, split)
        self.downsample = downsample
        self.file_list = sorted(os.listdir(self.root_dir))
        self.is_train = split == 'train'
        self.env_template = EnvironmentMap(self.sky_H, 'skylatlong')
        self.center_align = args.get('center_align', False)
        self.normalize = args.get('normalize', None)
        self.aug_exposure_range = args.get('aug_exposure_range', [-2.5, 0.5])
        self.aug_temperature_range = args.get('aug_temperature_range', [1, 1])

    def __len__(self):
        return len(self.file_list)

    def __getitem__(self, idx):
        file_path = os.path.join(self.root_dir, self.file_list[idx])
        hdr_pano = imread(file_path)
        hdr_skypano = hdr_pano[:hdr_pano.shape[0] // 2, :, :]
        hdr_skypano = cv2.resize(hdr_skypano, (self.sky_W, self.sky_H))[:, :, :3]
        if self.is_train:
            hdr_skypano = adjust_exposure(hdr_skypano, self.aug_exposure_range)
            hdr_skypano = adjust_flip(hdr_skypano)
            if not self.center_align:
                hdr_skypano = adjust_rotation(hdr_skypano)
            hdr_skypano = adjust_color_temperature(hdr_skypano, self.aug_temperature_range)
        illumination = 0.2126 * hdr_skypano[..., 0] + 0.7152 * hdr_skypano[..., 1] + 0.0722 * hdr_skypano[..., 2]
        max_index = np.argmax(illumination, axis=None)
        max_index_2d = np.unravel_index(max_index, illumination.shape)
        peak_int_v, peak_int_u = max_index_2d
        if self.center_align:
            azimuth = (self.sky_W // 2 - peak_int_u) % self.sky_W / self.sky_W * 2 * np.pi
            hdr_skypano = adjust_rotation(hdr_skypano, azimuth)
            peak_int_u = self.sky_W // 2
        peak_int = hdr_skypano[peak_int_v, peak_int_u]
        peak_dir_w_flag = self.env_template.pixel2world(peak_int_u, peak_int_v)
        peak_dir = np.array([peak_dir_w_flag[0], peak_dir_w_flag[1], peak_dir_w_flag[2]])
        ldr_skypano = srgb_gamma_correction(hdr_skypano)
        if self.normalize:
            peak_int_R = np.percentile(hdr_skypano[..., 0], self.normalize * 100)
            peak_int_G = np.percentile(hdr_skypano[..., 1], self.normalize * 100)
            peak_int_B = np.percentile(hdr_skypano[..., 2], self.normalize * 100)
            peak_int = np.array([peak_int_R, peak_int_G, peak_int_B])
            hdr_skypano = hdr_skypano / peak_int
            hdr_skypano = hdr_skypano.clip(0, 1)
        peak_vector = np.concatenate([peak_dir, peak_int], axis=-1)
        peak_vector_tensor = torch.from_numpy(peak_vector.astype(np.float32))
        hdr_skypano_tensor = torch.from_numpy(hdr_skypano.astype(np.float32)).permute(2, 0, 1)
        ldr_skypano_tensor = torch.from_numpy(ldr_skypano.astype(np.float32)).permute(2, 0, 1)
        return (ldr_skypano_tensor, hdr_skypano_tensor, peak_vector_tensor)

def __init__(self, args, split='train'):
    root_dir = args['root_dir']
    downsample = args['downsample']
    self.sky_H = args['image_H'] // downsample // 2
    self.sky_W = args['image_W'] // downsample
    self.root_dir = os.path.join(root_dir, split)
    self.downsample = downsample
    self.file_list = sorted(os.listdir(self.root_dir))
    self.is_train = split == 'train'
    self.env_template = EnvironmentMap(self.sky_H, 'skylatlong')
    self.center_align = args.get('center_align', False)
    self.normalize = args.get('normalize', None)
    self.aug_exposure_range = args.get('aug_exposure_range', [-2.5, 0.5])
    self.aug_temperature_range = args.get('aug_temperature_range', [1, 1])

def __len__(self):
    return len(self.file_list)

class materialed_meshes:
    """
    If the obj have mulitple meshes and materials, it will build a scene.
    And seperate meshes by material.

    Dump all meshes and concatenate them is a good way to accelerate ray-mesh intersection.
    But we need to record each vertex belongs which material. 
    """

    def __init__(self, obj_path):
        scene = trimesh.load(obj_path, force='scene')
        self.scene_dump = scene.dump()
        self.mesh_all = scene.dump(concatenate=True)
        self.vertex_cnt = [mesh.vertices.shape[0] for mesh in self.scene_dump]
        self.face_cnt = [mesh.faces.shape[0] for mesh in self.scene_dump]
        self.vertex_accu = list(itertools.accumulate(self.vertex_cnt))
        self.face_accu = list(itertools.accumulate(self.face_cnt))

    def find_material_and_idx(self, accu_list, idx):
        material_idx = np.searchsorted(accu_list, idx, side='right')
        local_idx = idx - accu_list[material_idx]
        return (material_idx, local_idx)

    def get_material_from_face_idx_of_all(self, face_idx_in_all):
        """
            face_idx_in_all:
                face idx in self.mesh_all.faces
        """
        material_idx, local_idx = self.find_material_and_idx(self.face_accu, face_idx_in_all)
        mesh = self.scene_dump[material_idx]
        face_local = mesh.faces[local_idx]
        uv_local = mesh.visual.uv[face_local]
        material = mesh.visual.material
        material.kwargs['name'] = mesh.metadata['name']
        return (material, face_local, uv_local)

    def get_all_meshes(self):
        return self.mesh_all

def __init__(self, obj_path):
    scene = trimesh.load(obj_path, force='scene')
    self.scene_dump = scene.dump()
    self.mesh_all = scene.dump(concatenate=True)
    self.vertex_cnt = [mesh.vertices.shape[0] for mesh in self.scene_dump]
    self.face_cnt = [mesh.faces.shape[0] for mesh in self.scene_dump]
    self.vertex_accu = list(itertools.accumulate(self.vertex_cnt))
    self.face_accu = list(itertools.accumulate(self.face_cnt))

def read_yaml(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def dump_yaml(data, savepath):
    with open(os.path.join(savepath, 'config.yaml'), 'w') as outfile:
        yaml.dump(data, outfile, default_flow_style=False)

def get_exp_dir(expname):
    current_time = datetime.datetime.now()
    current_time_str = current_time.strftime(f'{expname}_%m%d_%H%M%S')
    root_dir = os.getcwd()
    root_dir_log = os.path.join(root_dir, 'mc_to_sky/logs')
    if not os.path.exists(root_dir_log):
        os.mkdir(root_dir_log)
    exp_dir = os.path.join(root_dir_log, current_time_str)
    if not os.path.exists(exp_dir):
        os.mkdir(exp_dir)
    return exp_dir

def check_and_mkdirs(path):
    if not os.path.exists(path):
        os.makedirs(path)

def build_model(hypes, return_cls=False):
    model_args = hypes['model']
    model_name = model_args['name']
    model_filename = 'mc_to_sky.model.' + model_name
    model_lib = importlib.import_module(model_filename)
    model_cls = None
    target_model_name = model_name.replace('_', '')
    for name, cls in model_lib.__dict__.items():
        if name.lower() == target_model_name.lower():
            model_cls = cls
    if return_cls:
        return model_cls
    model = model_cls(hypes)
    return model

def backup_script(full_path, folders_to_save=['model', 'data_utils', 'utils', 'loss', 'tools']):
    target_folder = os.path.join(full_path, 'scripts')
    if not os.path.exists(target_folder):
        if not os.path.exists(target_folder):
            os.mkdir(target_folder)
    current_path = os.path.dirname(__file__)
    for folder_name in folders_to_save:
        ttarget_folder = os.path.join(target_folder, folder_name)
        source_folder = os.path.join(current_path, f'../{folder_name}')
        shutil.copytree(source_folder, ttarget_folder, dirs_exist_ok=True)

class Timer:

    def __init__(self):
        self.time = time.time()
        print('Start timing ... ')

    def print(self, message=''):
        print(f'\n--- {message} using time {time.time() - self.time:3f} ---\n')
        self.time = time.time()

def __init__(self):
    self.time = time.time()
    print('Start timing ... ')

def print(self, message=''):
    print(f'\n--- {message} using time {time.time() - self.time:3f} ---\n')
    self.time = time.time()

def get_callback():
    checkpoint_callback = ModelCheckpoint(monitor='val_loss', filename='{epoch}-{val_loss:.2f}', save_top_k=1, save_last=True, mode='min')
    return checkpoint_callback

def main():
    args = get_parser()
    hypes = read_yaml(args.config)
    train_conf = hypes['train_conf']
    train_set = build_dataset(hypes, split='train')
    valid_set = build_dataset(hypes, split='val')
    train_loader = DataLoader(train_set, batch_size=train_conf['batch_size'], shuffle=True, num_workers=24, pin_memory=True)
    valid_loader = DataLoader(valid_set, batch_size=train_conf['batch_size'], shuffle=False, num_workers=24, pin_memory=True)
    if args.ckpt_path and (not args.load_weight_only):
        exp_dir = args.ckpt_path.split('lightning_logs')[0]
    else:
        exp_dir = get_exp_dir(hypes['exp_name'])
        dump_yaml(hypes, exp_dir)
    backup_script(exp_dir)
    model = build_model(hypes)
    if args.load_weight_only:
        model.load_state_dict(torch.load(args.ckpt_path)['state_dict'])
        args.ckpt_path = None
    checkpoint_callback = get_callback()
    trainer = pl.Trainer(default_root_dir=exp_dir, accelerator=train_conf['accelerator'], devices=train_conf['device_num'], max_epochs=train_conf['epoch'], check_val_every_n_epoch=train_conf['check_val_every_n_epoch'], log_every_n_steps=train_conf['log_every_n_steps'], callbacks=[checkpoint_callback])
    trainer.fit(model, train_loader, valid_loader, ckpt_path=args.ckpt_path)

def main():
    args = get_parser()
    hypes = read_yaml(args.config)
    model = build_model(hypes, return_cls=True).load_from_checkpoint(args.ckpt_path, hypes=hypes).to('cuda')
    model.eval()
    model_name = hypes['model']['name']
    skip = hypes['dataset']['view_setting']['view_num']
    skip = 3
    all_waymo = args.waymo_scenes_dir
    scenes = os.listdir(all_waymo)
    for scene in tqdm(scenes):
        scene_image_dir = os.path.join(all_waymo, scene, 'images')
        scene_output_dir = os.path.join(args.output_dir, scene)
        check_and_mkdirs(scene_output_dir)
        filename_list = sorted(os.listdir(scene_image_dir))
        for idx in range(0, len(filename_list), skip):
            input_W = hypes['dataset']['view_setting']['camera_W'] // hypes['dataset']['view_setting']['downsample_for_crop']
            input_H = hypes['dataset']['view_setting']['camera_H'] // hypes['dataset']['view_setting']['downsample_for_crop']
            image_paths = [os.path.join(scene_image_dir, filename_list[idx + ii]) for ii in range(skip)]
            images = [imageio.imread(image_path).astype(np.float32) / 255.0 for image_path in image_paths]
            images_crop = [cv2.resize(image, (input_W, input_H)) for image in images]
            images_input = [torch.from_numpy(image_crop).permute(2, 0, 1).unsqueeze(0).to('cuda') for image_crop in images_crop]
            inputs = torch.stack(images_input, dim=1)
            hdr_skypano = infer_sky(model, inputs)
            imageio.imwrite(os.path.join(scene_output_dir, image_paths[0].split('/')[-1].replace('.png', '_sky.exr')), hdr_skypano)
            hdr_fullpano = np.zeros((hdr_skypano.shape[0] * 2, hdr_skypano.shape[1], 3), dtype=np.float32)
            hdr_fullpano[:hdr_skypano.shape[0]] = hdr_skypano
            imageio.imwrite(os.path.join(scene_output_dir, image_paths[0].split('/')[-1].replace('.png', '.exr')), hdr_fullpano)
            SAVE_FULL_NPZ = False
            if SAVE_FULL_NPZ:
                poses_bounds = image_paths[0].split('images')[0] + 'poses_bounds.npy'
                waymo_ext_int = np.load(poses_bounds)[:, :15].reshape(-1, 3, 5)
                waymo_ext = waymo_ext_int[idx, :3, :4]
                waymo_ext_opencv = np.stack([waymo_ext[:, 1], waymo_ext[:, 0], -waymo_ext[:, 2], waymo_ext[:, 3]], axis=-1)
                waymo_ext_pad = np.identity(4)
                waymo_ext_pad[:3, :4] = waymo_ext_opencv
                waymo_int = waymo_ext_int[idx, :3, 4]
                print(os.path.join(scene_output_dir, image_paths[0].split('/')[-1].replace('png', 'npz')))
                np.savez(os.path.join(scene_output_dir, image_paths[0].split('/')[-1].replace('png', 'npz')), H=int(waymo_int[0]), W=int(waymo_int[1]), focal=waymo_int[2], rgb=imageio.imread(image_paths[0]), depth=np.full((int(waymo_int[0]), int(waymo_int[1])), 10000.0), extrinsic=waymo_ext_pad)

def evaluate_peak_intensity(visualization_path):
    """
    peak_intensity_error_percentage : float
       (abs(pred_int - gt_int) / gt_int) * 100%

    Args: 
    
        visualization_path : str
            visulization is result on testset. 
            e.g. mc_to_sky/logs/pred_hdr_pano_from_AvgMultiView_enhanced_elu_white_balance_adjust3/lightning_logs/version_0/visualization
            include 'xxxx_hdr_gt.exr', 'xxxx_hdr_pred.exr'
    
    Returns:
        max, min, mean, median of peak_intensity_error_percentage
    """
    hdr_pred_files = sorted(glob.glob(os.path.join(visualization_path, '*_hdr_pred.exr')))
    hdr_gt_files = sorted(glob.glob(os.path.join(visualization_path, '*_hdr_gt.exr')))
    pred_peak_illuminance_list = []
    gt_peak_illuminance_list = []
    peak_error_list = []
    assert len(hdr_pred_files) == len(hdr_gt_files)
    for pred_file, gt_file in zip(hdr_pred_files, hdr_gt_files):
        pred = imageio.imread(pred_file)
        gt = imageio.imread(gt_file)
        pred_illuminance = 0.2126 * pred[..., 0] + 0.7152 * pred[..., 1] + 0.0722 * pred[..., 2]
        gt_illuminance = 0.2126 * gt[..., 0] + 0.7152 * gt[..., 1] + 0.0722 * gt[..., 2]
        pred_peak_illuminance = np.max(pred_illuminance)
        gt_peak_illuminance = np.max(gt_illuminance)
        if np.isinf(gt_peak_illuminance):
            continue
        pred_peak_illuminance_log10 = np.log10(pred_peak_illuminance).clip(0, 100)
        gt_peak_illuminance_log10 = np.log10(gt_peak_illuminance).clip(0, 100)
        peak_error = np.abs(pred_peak_illuminance_log10 - gt_peak_illuminance_log10) / gt_peak_illuminance_log10
        peak_error_list.append(peak_error)
    print(visualization_path)
    print(f'{colored('min: ', 'green')} {np.min(peak_error_list)}')
    print(f'{colored('max: ', 'green')} {np.max(peak_error_list)}')
    print(f'{colored('mean: ', 'green')} {np.mean(peak_error_list)}')
    print(f'{colored('median: ', 'green')} {np.median(peak_error_list)}')
    return (np.min(peak_error_list), np.max(peak_error_list), np.mean(peak_error_list), np.median(peak_error_list))

def evaluate_peak_direction(visualization_path):
    """
    peak_direction_error_percentage : float
        angle of <pred_peak_dir, gt_peak_dir>

    Args: 
        visualization_path : str
            visulization is result on testset. 
            e.g. mc_to_sky/logs/Hold_Geoffroy_pred_hdr_pano_from_single/lightning_logs/version_0/visualization
            include 'xxxx_hdr_gt.exr', 'xxxx_hdr_pred.exr', ('xxxx_hdr_pred_rotated.exr')
    
    Returns:
        max, min, mean, median of peak_intensity_error_percentage
    """
    hdr_pred_files = sorted(glob.glob(os.path.join(visualization_path, '*_hdr_pred.exr')))
    hdr_gt_files = sorted(glob.glob(os.path.join(visualization_path, '*_ldr_input.png')))
    angular_error_list = []
    if len(glob.glob(os.path.join(visualization_path, '*_hdr_pred_rotated.exr'))) != 0:
        hdr_pred_files = sorted(glob.glob(os.path.join(visualization_path, '*_hdr_pred_rotated.exr')))
    assert len(hdr_pred_files) == len(hdr_gt_files)
    for pred_file, gt_file in zip(hdr_pred_files, hdr_gt_files):
        pred = imageio.imread(pred_file)
        gt = srgb_inv_gamma_correction(imageio.imread(gt_file) / 255)
        H, W, _ = pred.shape
        env_template = EnvironmentMap(H, 'skylatlong')
        pred_illuminance = 0.2126 * pred[..., 0] + 0.7152 * pred[..., 1] + 0.0722 * pred[..., 2]
        gt_illuminance = 0.2126 * gt[..., 0] + 0.7152 * gt[..., 1] + 0.0722 * gt[..., 2]
        max_index_pred = np.argmax(pred_illuminance, axis=None)
        max_index_pred_2d = np.unravel_index(max_index_pred, pred_illuminance.shape)
        peak_pred_v, peak_pred_u = max_index_pred_2d
        max_index_gt = np.argmax(gt_illuminance, axis=None)
        max_gt_illuminance = np.max(gt_illuminance)
        max_gt_illuminance_num = np.sum(gt_illuminance == max_gt_illuminance)
        if max_gt_illuminance_num > 15:
            continue
        max_index_gt_2d = np.unravel_index(max_index_gt, gt_illuminance.shape)
        peak_gt_v, peak_gt_u = max_index_gt_2d
        peak_pred_xyz = env_template.image2world(peak_pred_u / W, peak_pred_v / H)
        peak_gt_xyz = env_template.image2world(peak_gt_u / W, peak_gt_v / H)
        angular_error_cosine = np.dot(peak_pred_xyz / np.linalg.norm(peak_pred_xyz), peak_gt_xyz / np.linalg.norm(peak_gt_xyz))
        angular_error = np.degrees(np.arccos(angular_error_cosine))
        angular_error_list.append(angular_error)
    ic(len(angular_error_list))
    print(visualization_path)
    print(f'{colored('min: ', 'green')} {np.min(angular_error_list)}')
    print(f'{colored('max: ', 'green')} {np.max(angular_error_list)}')
    print(f'{colored('mean: ', 'green')} {np.mean(angular_error_list)}')
    print(f'{colored('median: ', 'green')} {np.median(angular_error_list)}')
    return (np.min(angular_error_list), np.max(angular_error_list), np.mean(angular_error_list), np.median(angular_error_list))

def resize_all(source_dir='dataset/holicity_pano', target_dir='dataset/holicity_pano_resized_800'):
    record_dates = os.listdir(source_dir)
    for record_date in tqdm(record_dates):
        source_date_dir = os.path.join(source_dir, record_date)
        target_date_dir = os.path.join(target_dir, record_date)
        if not os.path.exists(target_date_dir):
            os.mkdir(target_date_dir)
        pano_filenames = os.listdir(source_date_dir)
        for pano_filename in pano_filenames:
            image = imageio.imread(os.path.join(source_date_dir, pano_filename))
            image_resize = cv2.resize(image, (1600, 800))
            imageio.imsave(os.path.join(target_date_dir, pano_filename), image_resize)

def resize_sky(source_dir='dataset/holicity_pano_resized_800', target_dir='dataset/holicity_pano_sky_resized_64'):
    record_dates = os.listdir(source_dir)
    for record_date in tqdm(record_dates):
        source_date_dir = os.path.join(source_dir, record_date)
        target_date_dir = os.path.join(target_dir, record_date)
        if not os.path.exists(target_date_dir):
            os.mkdir(target_date_dir)
        pano_filenames = os.listdir(source_date_dir)
        for pano_filename in pano_filenames:
            image = imageio.imread(os.path.join(source_date_dir, pano_filename))
            image_resize = cv2.resize(image[:image.shape[0] // 2, :, :], (256, 64))
            imageio.imsave(os.path.join(target_date_dir, pano_filename), image_resize)

def crop_pano(source_dir='dataset/holicity_pano', target_dir='dataset/holicity_crop_multiview', selected_sample_json='dataset/holicity_meta_info/selected_sample.json', camera_H=1280, camera_W=1920, focal=2088.465, downsample_for_crop=4, degree_interval=45, multiprocess=-1):
    crop_H = camera_H // downsample_for_crop
    crop_W = camera_W // downsample_for_crop
    camera_vfov = np.degrees(np.arctan2(camera_H, camera_W)) * 2
    aspect_ratio = camera_W / camera_H
    with open(selected_sample_json) as f:
        selected_sample = json.load(f)
    sample_dict = {}
    for selected_sample_name in selected_sample:
        date, filename = selected_sample_name.split('/')
        if date in sample_dict:
            sample_dict[date].append(filename)
        else:
            sample_dict[date] = [filename]
    info_dict = {}
    info_dict['crop_H'] = crop_H
    info_dict['crop_W'] = crop_W
    info_dict['camera_vfov'] = camera_vfov
    info_dict['aspect_ratio'] = aspect_ratio
    info_dict['degree_interval'] = degree_interval
    info_dict['source_dir'] = source_dir
    info_dict['target_dir'] = target_dir
    info_dict['selected_sample_dict'] = sample_dict
    record_dates = sorted(sample_dict.keys())
    if multiprocess <= 0:
        for record_date in record_dates:
            crop_pano_single(info_dict, record_date)
    else:
        pool = Pool(multiprocess)
        for record_date in record_dates:
            pool.apply_async(func=crop_pano_single, args=(info_dict, record_date))
        pool.close()
        pool.join()

def build_latent_predictor(args):
    model_name = args['name']
    model_lib = importlib.import_module('mc_to_sky.model.sub_module.skypred_modules')
    model_cls = None
    target_model_name = model_name.replace('_', '')
    for name, cls in model_lib.__dict__.items():
        if name.lower() == target_model_name.lower():
            model_cls = cls
    return model_cls(args)

def build_loss(loss_conf):
    loss_name = loss_conf['type']
    loss_args = loss_conf['args']
    loss_lib = importlib.import_module('mc_to_sky.loss.loss')
    loss_cls = None
    target_loss_name = loss_name.replace('_', '')
    for name, cls in loss_lib.__dict__.items():
        if name.lower() == target_loss_name.lower():
            loss_cls = cls
    return loss_cls(loss_args)

def parse_argv(argv):
    result = []
    for i in range(1, len(argv)):
        if argv[i] == '--':
            if i + 1 < len(argv):
                result.append(argv[i + 1])
    return result

def main():

    def parse_argv(argv):
        result = []
        for i in range(1, len(argv)):
            if argv[i] == '--':
                if i + 1 < len(argv):
                    result.append(argv[i + 1])
        return result
    argv = sys.argv
    argv = parse_argv(argv)
    render_yaml = argv[0]
    start_frame = int(argv[1])
    end_frame = int(argv[2])
    for frame in range(start_frame, end_frame):
        with open(os.path.join(render_yaml, f'{frame}.yaml'), 'r') as file:
            render_opt = yaml.safe_load(file)
        bpy.ops.wm.read_homefile(app_template='')
        rm_all_in_blender()
        scene_data = render_opt['scene_file']
        data_dict = np.load(scene_data)
        H = data_dict['H'].tolist()
        W = data_dict['W'].tolist()
        focal = data_dict['focal'].tolist()
        render_opt['intrinsic'] = {'H': H, 'W': W, 'focal': focal}
        render_opt['cam2world'] = data_dict['extrinsic']
        render_opt['background_RGB'] = data_dict['rgb']
        render_opt['background_depth'] = data_dict['depth']
        render(render_opt)

def check_mkdir(dir):
    if not os.path.exists(dir):
        os.mkdir(dir)

def set_render_params(render_H, render_W, render_downsample, sample_num=32, device='GPU'):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    bpy.context.preferences.addons['cycles'].preferences.compute_device_type = 'CUDA'
    bpy.context.scene.cycles.device = device
    bpy.context.preferences.addons['cycles'].preferences.get_devices()
    print('preferences.compute_device_type: ', bpy.context.preferences.addons['cycles'].preferences.compute_device_type)
    for dev in bpy.context.preferences.addons['cycles'].preferences.devices:
        print(f'Use Device {dev['name']}: {dev['use']}')
    scene.cycles.samples = sample_num
    scene.render.resolution_x = render_W
    scene.render.resolution_y = render_H
    scene.render.resolution_percentage = 100 // render_downsample
    scene.render.film_transparent = True
    bpy.context.view_layer.use_pass_combined = True
    bpy.context.view_layer.use_pass_z = True
    bpy.context.view_layer.cycles.use_pass_shadow_catcher = True

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

def set_hdri(hdri_path, rotation=None):
    """
    Args:
        hdri_path: str
            path to hdri
        rotation: list of float
            [rotate_x, rotate_y, rotate_z] rotate the HDRI. (rad)
            rotate_z (pos) will rotate the skydome clockwise

            By default, the HDRI is set to x-positive view.
    """
    C = bpy.context
    scn = C.scene
    node_tree = scn.world.node_tree
    tree_nodes = node_tree.nodes
    tree_nodes.clear()
    node_background = tree_nodes.new(type='ShaderNodeBackground')
    node_environment = tree_nodes.new('ShaderNodeTexEnvironment')
    node_environment.image = bpy.data.images.load(hdri_path)
    node_environment.location = (-300, 0)
    node_output = tree_nodes.new(type='ShaderNodeOutputWorld')
    node_output.location = (200, 0)
    links = node_tree.links
    link = links.new(node_environment.outputs['Color'], node_background.inputs['Color'])
    link = links.new(node_background.outputs['Background'], node_output.inputs['Surface'])
    if rotation is not None:
        node_map = tree_nodes.new('ShaderNodeMapping')
        node_map.location = (-500, 0)
        node_texcoor = tree_nodes.new('ShaderNodeTexCoord')
        node_texcoor.location = (-700, 0)
        link = links.new(node_texcoor.outputs['Generated'], node_map.inputs['Vector'])
        link = links.new(node_map.outputs['Vector'], node_environment.inputs['Vector'])
        if isinstance(rotation, list):
            node_map.inputs['Rotation'].default_value = rotation
        elif isinstance(rotation, str):
            if rotation == 'camera_view':
                camera_obj_name = 'Camera'
                camera = bpy.data.objects[camera_obj_name]
                camera.rotation_mode = 'XYZ'
                camera_rot_z = camera.rotation_euler.z
                print(camera.rotation_euler)
                node_map.inputs['Rotation'].default_value[2] = -camera_rot_z
                camera.rotation_mode = 'QUATERNION'
            else:
                raise 'This HDRI rotation is not implemented'
        else:
            raise 'This HDRI rotation is not implemented'

def read_from_render(rendered_output_dir, image_type, image_prefix):
    """
    Args:
        image_type: str,
            RGB/depth/mask
        image_prefix: str,
            vehicle_only/vehicle_and_plane/plane_only
    """
    files = glob.glob(os.path.join(rendered_output_dir, image_type) + f'/{image_prefix}*')
    assert len(files) == 1
    return imageio.imread(files[0])

def transform_gpt_to_trajectory(answer, agent, time, input_map=None, post_transform=(False, None), obj=None):
    python_file = 'work_dirs/created_python_file/traj_' + str(time) + '.py'
    if os.path.exists(python_file):
        os.remove(python_file)
    with open(python_file, 'w') as f:
        f.write(extract_python_code(answer))
    python_command = 'python ' + python_file
    result = os.popen(python_command)
    res = result.read()
    coordinates = ast.literal_eval(res)
    return coordinates

def transform_coord_to_trajectory(answer, agent, time, input_map=None, post_transform=(False, None), obj=None):
    python_file = 'work_dirs/created_python_file/traj_' + str(time) + '.py'
    if os.path.exists(python_file):
        os.remove(python_file)
    with open(python_file, 'w') as f:
        f.write(extract_python_code(answer))
    python_command = 'python ' + python_file
    result = os.popen(python_command)
    res = result.read()
    coordinates = ast.literal_eval(res)
    return coordinates

