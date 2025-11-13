# Cluster 14

def split_rays(rays, batch_size):
    ret = []
    origins_all = rays.origins.split(batch_size)
    directions_all = rays.directions.split(batch_size)
    viewdirs_all = rays.viewdirs.split(batch_size)
    radii_all = rays.radii.split(batch_size)
    near_all = rays.near.split(batch_size)
    far_all = rays.far.split(batch_size)
    for o, d, v, r, n, f in zip(origins_all, directions_all, viewdirs_all, radii_all, near_all, far_all):
        ret.append(Rays(o, d, v, r, n, f))
    return ret

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

def build_scene_graph(self):
    self.scene_graph = defaultdict(lambda: defaultdict(int))
    point3D_iter = self.point3D_id_to_images.iteritems()
    for i, (point3D_id, images) in enumerate(point3D_iter):
        if not self.point3D_valid(point3D_id):
            continue
        for image_id1, image_id2 in combinations(images[:, 0], 2):
            self.scene_graph[image_id1][image_id2] += 1
            self.scene_graph[image_id2][image_id1] += 1

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

def remove_car(self, car_name):
    """
        append car_id to self.removed_cars, inpaint them later.

        car_name
        """
    self.removed_cars.append(car_name)

def register_eigen_printers(obj):
    """Register eigen pretty-printers with objfile Obj"""
    if obj == None:
        obj = gdb
    obj.pretty_printers.append(lookup_function)

def split_rays(rays, batch_size):
    ret = []
    origins_all = rays.origins.split(batch_size)
    directions_all = rays.directions.split(batch_size)
    viewdirs_all = rays.viewdirs.split(batch_size)
    radii_all = rays.radii.split(batch_size)
    near_all = rays.near.split(batch_size)
    far_all = rays.far.split(batch_size)
    for o, d, v, r, n, f in zip(origins_all, directions_all, viewdirs_all, radii_all, near_all, far_all):
        ret.append(Rays(o, d, v, r, n, f))
    return ret

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

def build_scene_graph(self):
    self.scene_graph = defaultdict(lambda: defaultdict(int))
    point3D_iter = self.point3D_id_to_images.iteritems()
    for i, (point3D_id, images) in enumerate(point3D_iter):
        if not self.point3D_valid(point3D_id):
            continue
        for image_id1, image_id2 in combinations(images[:, 0], 2):
            self.scene_graph[image_id1][image_id2] += 1
            self.scene_graph[image_id2][image_id1] += 1

def cameraList_from_camInfos(cam_infos, resolution_scale, args):
    camera_list = []
    for id, c in enumerate(cam_infos):
        camera_list.append(loadCam(args, id, c, resolution_scale))
    return camera_list

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

def lpips(x: torch.Tensor, y: torch.Tensor, net_type: str='alex', version: str='0.1'):
    """Function that measures
    Learned Perceptual Image Patch Similarity (LPIPS).

    Arguments:
        x, y (torch.Tensor): the input tensors to compare.
        net_type (str): the network type to compare the features: 
                        'alex' | 'squeeze' | 'vgg'. Default: 'alex'.
        version (str): the version of LPIPS. Default: 0.1.
    """
    device = x.device
    criterion = LPIPS(net_type, version).to(device)
    return criterion(x, y)

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

def get_ref_index(neighbor_ids, length):
    ref_length = 10
    ref_index = []
    for i in range(0, length, ref_length):
        if not i in neighbor_ids:
            ref_index.append(i)
    return ref_index

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

def get_ref_index(neighbor_ids, length):
    ref_index = []
    for i in range(0, length, ref_length):
        if not i in neighbor_ids:
            ref_index.append(i)
    return ref_index

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

def forward(self, xs):
    xs_t = torch.transpose(xs, 0, 1)
    xs_t = xs_t.unsqueeze(0)
    feat = self.conv(xs_t)
    if self.use_sigmoid:
        feat = torch.sigmoid(feat)
    out = torch.transpose(feat, 1, 2)
    return out

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

def forward(self, xs):
    xs_t = torch.transpose(xs, 0, 1)
    xs_t = xs_t.unsqueeze(0)
    feat = self.conv(xs_t)
    if self.use_sigmoid:
        feat = torch.sigmoid(feat)
    out = torch.transpose(feat, 1, 2)
    return out

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

def forward(self, x):
    for i, layer in enumerate(self.layers):
        x = F.relu(layer(x)) if i < self.num_layers - 1 else layer(x)
    if self.sigmoid_output:
        x = F.sigmoid(x)
    return x

def remove_small_regions(mask: np.ndarray, area_thresh: float, mode: str) -> Tuple[np.ndarray, bool]:
    """
    Removes small disconnected regions and holes in a mask. Returns the
    mask and an indicator of if the mask has been modified.
    """
    import cv2
    assert mode in ['holes', 'islands']
    correct_holes = mode == 'holes'
    working_mask = (correct_holes ^ mask).astype(np.uint8)
    n_labels, regions, stats, _ = cv2.connectedComponentsWithStats(working_mask, 8)
    sizes = stats[:, -1][1:]
    small_regions = [i + 1 for i, s in enumerate(sizes) if s < area_thresh]
    if len(small_regions) == 0:
        return (mask, False)
    fill_labels = [0] + small_regions
    if not correct_holes:
        fill_labels = [i for i in range(n_labels) if i not in fill_labels]
        if len(fill_labels) == 0:
            fill_labels = [int(np.argmax(sizes)) + 1]
    mask = np.isin(regions, fill_labels)
    return (mask, True)

class MakeManyMasksWrapper:

    def __init__(self, impl, variants_n=2):
        self.impl = impl
        self.variants_n = variants_n

    def get_masks(self, img):
        img = np.transpose(np.array(img), (2, 0, 1))
        return [self.impl(img)[0] for _ in range(self.variants_n)]

def get_masks(self, img):
    img = np.transpose(np.array(img), (2, 0, 1))
    return [self.impl(img)[0] for _ in range(self.variants_n)]

class MakeManyMasksWrapper:

    def __init__(self, impl, variants_n=2):
        self.impl = impl
        self.variants_n = variants_n

    def get_masks(self, img):
        img = np.transpose(np.array(img), (2, 0, 1))
        return [self.impl(img)[0] for _ in range(self.variants_n)]

def get_masks(self, img):
    img = np.transpose(np.array(img), (2, 0, 1))
    return [self.impl(img)[0] for _ in range(self.variants_n)]

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

def __call__(self, x, y):
    x_vgg, y_vgg = (self.vgg(x), self.vgg(y))
    content_loss = 0.0
    content_loss += self.weights[0] * self.criterion(x_vgg['relu1_1'], y_vgg['relu1_1'])
    content_loss += self.weights[1] * self.criterion(x_vgg['relu2_1'], y_vgg['relu2_1'])
    content_loss += self.weights[2] * self.criterion(x_vgg['relu3_1'], y_vgg['relu3_1'])
    content_loss += self.weights[3] * self.criterion(x_vgg['relu4_1'], y_vgg['relu4_1'])
    content_loss += self.weights[4] * self.criterion(x_vgg['relu5_1'], y_vgg['relu5_1'])
    return content_loss

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

def get_global_features(self, input):
    check_and_warn_input_range(input, 0, 1, 'PerceptualLoss input in get_global_features')
    if self.normalize_inputs:
        features_input = self.do_normalize_inputs(input)
    else:
        features_input = input
    features_input = self.vgg(features_input)
    return features_input

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

def forward(self, pred, target):
    pred = (pred - IMAGENET_MEAN.to(pred)) / IMAGENET_STD.to(pred)
    target = (target - IMAGENET_MEAN.to(target)) / IMAGENET_STD.to(target)
    pred_feats = self.impl(pred, return_feature_maps=True)
    target_feats = self.impl(target, return_feature_maps=True)
    result = torch.stack([F.mse_loss(cur_pred, cur_target) for cur_pred, cur_target in zip(pred_feats, target_feats)]).sum() * self.weight
    return result

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

def forward(self, x):
    if torch.is_tensor(x):
        return self.inverse_transform(self.impl(self.transform(x)), x)
    elif isinstance(x, tuple):
        x_trans = tuple((self.transform(elem) for elem in x))
        y_trans = self.impl(x_trans)
        return tuple((self.inverse_transform(elem, orig_x) for elem, orig_x in zip(y_trans, x)))
    else:
        raise ValueError(f'Unexpected input type {type(x)}')

class InpaintingEvaluatorOnline(nn.Module):

    def __init__(self, scores, bins=10, image_key='image', inpainted_key='inpainted', integral_func=None, integral_title=None, clamp_image_range=None):
        """
        :param scores: dict {score_name: EvaluatorScore object}
        :param bins: number of groups, partition is generated by np.linspace(0., 1., bins + 1)
        :param device: device to use
        """
        super().__init__()
        LOGGER.info(f'{type(self)} init called')
        self.scores = nn.ModuleDict(scores)
        self.image_key = image_key
        self.inpainted_key = inpainted_key
        self.bins_num = bins
        self.bin_edges = np.linspace(0, 1, self.bins_num + 1)
        num_digits = max(0, math.ceil(math.log10(self.bins_num)) - 1)
        self.interval_names = []
        for idx_bin in range(self.bins_num):
            start_percent, end_percent = (round(100 * self.bin_edges[idx_bin], num_digits), round(100 * self.bin_edges[idx_bin + 1], num_digits))
            start_percent = '{:.{n}f}'.format(start_percent, n=num_digits)
            end_percent = '{:.{n}f}'.format(end_percent, n=num_digits)
            self.interval_names.append('{0}-{1}%'.format(start_percent, end_percent))
        self.groups = []
        self.integral_func = integral_func
        self.integral_title = integral_title
        self.clamp_image_range = clamp_image_range
        LOGGER.info(f'{type(self)} init done')

    def _get_bins(self, mask_batch):
        batch_size = mask_batch.shape[0]
        area = mask_batch.view(batch_size, -1).mean(dim=-1).detach().cpu().numpy()
        bin_indices = np.clip(np.searchsorted(self.bin_edges, area) - 1, 0, self.bins_num - 1)
        return bin_indices

    def forward(self, batch: Dict[str, torch.Tensor]):
        """
        Calculate and accumulate metrics for batch. To finalize evaluation and obtain final metrics, call evaluation_end
        :param batch: batch dict with mandatory fields mask, image, inpainted (can be overriden by self.inpainted_key)
        """
        result = {}
        with torch.no_grad():
            image_batch, mask_batch, inpainted_batch = (batch[self.image_key], batch['mask'], batch[self.inpainted_key])
            if self.clamp_image_range is not None:
                image_batch = torch.clamp(image_batch, min=self.clamp_image_range[0], max=self.clamp_image_range[1])
            self.groups.extend(self._get_bins(mask_batch))
            for score_name, score in self.scores.items():
                result[score_name] = score(inpainted_batch, image_batch, mask_batch)
        return result

    def process_batch(self, batch: Dict[str, torch.Tensor]):
        return self(batch)

    def evaluation_end(self, states=None):
        """:return: dict with (score_name, group_type) as keys, where group_type can be either 'overall' or
            name of the particular group arranged by area of mask (e.g. '10-20%')
            and score statistics for the group as values.
        """
        LOGGER.info(f'{type(self)}: evaluation_end called')
        self.groups = np.array(self.groups)
        results = {}
        for score_name, score in self.scores.items():
            LOGGER.info(f'Getting value of {score_name}')
            cur_states = [s[score_name] for s in states] if states is not None else None
            total_results, group_results = score.get_value(groups=self.groups, states=cur_states)
            LOGGER.info(f'Getting value of {score_name} done')
            results[score_name, 'total'] = total_results
            for group_index, group_values in group_results.items():
                group_name = self.interval_names[group_index]
                results[score_name, group_name] = group_values
        if self.integral_func is not None:
            results[self.integral_title, 'total'] = dict(mean=self.integral_func(results))
        LOGGER.info(f'{type(self)}: reset scores')
        self.groups = []
        for sc in self.scores.values():
            sc.reset()
        LOGGER.info(f'{type(self)}: reset scores done')
        LOGGER.info(f'{type(self)}: evaluation_end done')
        return results

def __init__(self, scores, bins=10, image_key='image', inpainted_key='inpainted', integral_func=None, integral_title=None, clamp_image_range=None):
    """
        :param scores: dict {score_name: EvaluatorScore object}
        :param bins: number of groups, partition is generated by np.linspace(0., 1., bins + 1)
        :param device: device to use
        """
    super().__init__()
    LOGGER.info(f'{type(self)} init called')
    self.scores = nn.ModuleDict(scores)
    self.image_key = image_key
    self.inpainted_key = inpainted_key
    self.bins_num = bins
    self.bin_edges = np.linspace(0, 1, self.bins_num + 1)
    num_digits = max(0, math.ceil(math.log10(self.bins_num)) - 1)
    self.interval_names = []
    for idx_bin in range(self.bins_num):
        start_percent, end_percent = (round(100 * self.bin_edges[idx_bin], num_digits), round(100 * self.bin_edges[idx_bin + 1], num_digits))
        start_percent = '{:.{n}f}'.format(start_percent, n=num_digits)
        end_percent = '{:.{n}f}'.format(end_percent, n=num_digits)
        self.interval_names.append('{0}-{1}%'.format(start_percent, end_percent))
    self.groups = []
    self.integral_func = integral_func
    self.integral_title = integral_title
    self.clamp_image_range = clamp_image_range
    LOGGER.info(f'{type(self)} init done')

def get_groupings(groups):
    """
    :param groups: group numbers for respective elements
    :return: dict of kind {group_idx: indices of the corresponding group elements}
    """
    label_groups, count_groups = np.unique(groups, return_counts=True)
    indices = np.argsort(groups)
    grouping = dict()
    cur_start = 0
    for label, count in zip(label_groups, count_groups):
        cur_end = cur_start + count
        cur_indices = indices[cur_start:cur_end]
        grouping[label] = cur_indices
        cur_start = cur_end
    return grouping

def simplest_countless(data):
    """
  Vectorized implementation of downsampling a 2D 
  image by 2 on each side using the COUNTLESS algorithm.
  
  data is a 2D numpy array with even dimensions.
  """
    sections = []
    factor = (2, 2)
    for offset in np.ndindex(factor):
        part = data[tuple((np.s_[o::f] for o, f in zip(offset, factor)))]
        sections.append(part)
    a, b, c, d = sections
    ab = a * (a == b)
    ac = a * (a == c)
    bc = b * (b == c)
    a = ab | ac | bc
    return a + (a == 0) * d

def quick_countless(data):
    """
  Vectorized implementation of downsampling a 2D 
  image by 2 on each side using the COUNTLESS algorithm.
  
  data is a 2D numpy array with even dimensions.
  """
    sections = []
    factor = (2, 2)
    for offset in np.ndindex(factor):
        part = data[tuple((np.s_[o::f] for o, f in zip(offset, factor)))]
        sections.append(part)
    a, b, c, d = sections
    ab_ac = a * ((a == b) | (a == c))
    bc = b * (b == c)
    a = ab_ac | bc
    return a + (a == 0) * d

def quickest_countless(data):
    """
  Vectorized implementation of downsampling a 2D 
  image by 2 on each side using the COUNTLESS algorithm.
  
  data is a 2D numpy array with even dimensions.
  """
    sections = []
    factor = (2, 2)
    for offset in np.ndindex(factor):
        part = data[tuple((np.s_[o::f] for o, f in zip(offset, factor)))]
        sections.append(part)
    a, b, c, d = sections
    ab_ac = a * ((a == b) | (a == c))
    ab_ac |= b * (b == c)
    return ab_ac + (ab_ac == 0) * d

def quick_countless_xor(data):
    """
  Vectorized implementation of downsampling a 2D 
  image by 2 on each side using the COUNTLESS algorithm.
  
  data is a 2D numpy array with even dimensions.
  """
    sections = []
    factor = (2, 2)
    for offset in np.ndindex(factor):
        part = data[tuple((np.s_[o::f] for o, f in zip(offset, factor)))]
        sections.append(part)
    a, b, c, d = sections
    ab = a ^ (a ^ b)
    ab += (ab != a) * ((ab ^ (ab ^ c)) - b)
    ab += (ab == c) * ((ab ^ (ab ^ d)) - c)
    return ab

def stippled_countless(data):
    """
  Vectorized implementation of downsampling a 2D 
  image by 2 on each side using the COUNTLESS algorithm
  that treats zero as "background" and inflates lone
  pixels.
  
  data is a 2D numpy array with even dimensions.
  """
    sections = []
    factor = (2, 2)
    for offset in np.ndindex(factor):
        part = data[tuple((np.s_[o::f] for o, f in zip(offset, factor)))]
        sections.append(part)
    a, b, c, d = sections
    ab_ac = a * ((a == b) | (a == c))
    ab_ac |= b * (b == c)
    nonzero = a + (a == 0) * (b + (b == 0) * c)
    return ab_ac + (ab_ac == 0) * (d + (d == 0) * nonzero)

def zero_corrected_countless(data):
    """
  Vectorized implementation of downsampling a 2D 
  image by 2 on each side using the COUNTLESS algorithm.
  
  data is a 2D numpy array with even dimensions.
  """
    data, upgraded = upgrade_type(data)
    data += 1
    sections = []
    factor = (2, 2)
    for offset in np.ndindex(factor):
        part = data[tuple((np.s_[o::f] for o, f in zip(offset, factor)))]
        sections.append(part)
    a, b, c, d = sections
    ab = a * (a == b)
    ac = a * (a == c)
    bc = b * (b == c)
    a = ab | ac | bc
    result = a + (a == 0) * d - 1
    if upgraded:
        return downgrade_type(result)
    data -= 1
    return result

def countless_extreme(data):
    nonzeros = np.count_nonzero(data)
    N = reduce(operator.mul, data.shape)
    if nonzeros == N:
        print('quick')
        return quick_countless(data)
    elif np.count_nonzero(data + 1) == N:
        print('quick')
        return quick_countless(data)
    else:
        return countless(data)

def countless(data):
    """
  Vectorized implementation of downsampling a 2D 
  image by 2 on each side using the COUNTLESS algorithm.
  
  data is a 2D numpy array with even dimensions.
  """
    data, upgraded = upgrade_type(data)
    data += 1
    sections = []
    factor = (2, 2)
    for offset in np.ndindex(factor):
        part = data[tuple((np.s_[o::f] for o, f in zip(offset, factor)))]
        sections.append(part)
    a, b, c, d = sections
    ab_ac = a * ((a == b) | (a == c))
    ab_ac |= b * (b == c)
    result = ab_ac + (ab_ac == 0) * d - 1
    if upgraded:
        return downgrade_type(result)
    data -= 1
    return result

def counting(array):
    factor = (2, 2, 1)
    shape = array.shape
    while len(shape) < 4:
        array = np.expand_dims(array, axis=-1)
        shape = array.shape
    output_shape = tuple((int(math.ceil(s / f)) for s, f in zip(shape, factor)))
    output = np.zeros(output_shape, dtype=array.dtype)
    for chan in range(0, shape[3]):
        for z in range(0, shape[2]):
            for x in range(0, shape[0], 2):
                for y in range(0, shape[1], 2):
                    block = array[x:x + 2, y:y + 2, z, chan]
                    hashtable = defaultdict(int)
                    for subx, suby in np.ndindex(block.shape[0], block.shape[1]):
                        hashtable[block[subx, suby]] += 1
                    best = (0, 0)
                    for segid, val in six.iteritems(hashtable):
                        if best[1] < val:
                            best = (segid, val)
                    output[x // 2, y // 2, chan] = best[0]
    return output

def countless_if(array):
    factor = (2, 2, 1)
    shape = array.shape
    if len(shape) < 3:
        array = array[:, :, np.newaxis]
        shape = array.shape
    output_shape = tuple((int(math.ceil(s / f)) for s, f in zip(shape, factor)))
    output = np.zeros(output_shape, dtype=array.dtype)
    for chan in range(0, shape[2]):
        for x in range(0, shape[0], 2):
            for y in range(0, shape[1], 2):
                block = array[x:x + 2, y:y + 2, chan]
                if block[0, 0] == block[1, 0]:
                    pick = block[0, 0]
                elif block[0, 0] == block[0, 1]:
                    pick = block[0, 0]
                elif block[1, 0] == block[0, 1]:
                    pick = block[1, 0]
                else:
                    pick = block[1, 1]
                output[x // 2, y // 2, chan] = pick
    return np.squeeze(output)

def downsample_with_averaging(array):
    """
  Downsample x by factor using averaging.

  @return: The downsampled array, of the same type as x.
  """
    if len(array.shape) == 3:
        factor = (2, 2, 1)
    else:
        factor = (2, 2)
    if np.array_equal(factor[:3], np.array([1, 1, 1])):
        return array
    output_shape = tuple((int(math.ceil(s / f)) for s, f in zip(array.shape, factor)))
    temp = np.zeros(output_shape, float)
    counts = np.zeros(output_shape, np.int)
    for offset in np.ndindex(factor):
        part = array[tuple((np.s_[o::f] for o, f in zip(offset, factor)))]
        indexing_expr = tuple((np.s_[:s] for s in part.shape))
        temp[indexing_expr] += part
        counts[indexing_expr] += 1
    return np.cast[array.dtype](temp / counts)

def downsample_with_max_pooling(array):
    factor = (2, 2)
    if np.all(np.array(factor, int) == 1):
        return array
    sections = []
    for offset in np.ndindex(factor):
        part = array[tuple((np.s_[o::f] for o, f in zip(offset, factor)))]
        sections.append(part)
    output = sections[0].copy()
    for section in sections[1:]:
        np.maximum(output, section, output)
    return output

def countless5(a, b, c, d, e):
    """First stage of generalizing from countless2d. 

  You have five slots: A, B, C, D, E

  You can decide if something is the winner by first checking for 
  matches of three, then matches of two, then picking just one if 
  the other two tries fail. In countless2d, you just check for matches
  of two and then pick one of them otherwise.

  Unfortunately, you need to check ABC, ABD, ABE, BCD, BDE, & CDE.
  Then you need to check AB, AC, AD, BC, BD
  We skip checking E because if none of these match, we pick E. We can
  skip checking AE, BE, CE, DE since if any of those match, E is our boy
  so it's redundant.

  So countless grows cominatorially in complexity.
  """
    sections = [a, b, c, d, e]
    p2 = lambda q, r: q * (q == r)
    p3 = lambda q, r, s: q * ((q == r) & (r == s))
    lor = lambda x, y: x + (x == 0) * y
    results3 = (p3(x, y, z) for x, y, z in combinations(sections, 3))
    results3 = reduce(lor, results3)
    results2 = (p2(x, y) for x, y in combinations(sections[:-1], 2))
    results2 = reduce(lor, results2)
    return reduce(lor, (results3, results2, e))

def countless8(a, b, c, d, e, f, g, h):
    """Extend countless5 to countless8. Same deal, except we also
    need to check for matches of length 4."""
    sections = [a, b, c, d, e, f, g, h]
    p2 = lambda q, r: q * (q == r)
    p3 = lambda q, r, s: q * ((q == r) & (r == s))
    p4 = lambda p, q, r, s: p * ((p == q) & (q == r) & (r == s))
    lor = lambda x, y: x + (x == 0) * y
    results4 = (p4(x, y, z, w) for x, y, z, w in combinations(sections, 4))
    results4 = reduce(lor, results4)
    results3 = (p3(x, y, z) for x, y, z in combinations(sections, 3))
    results3 = reduce(lor, results3)
    results2 = (p2(x, y) for x, y in combinations(sections[:-1], 2))
    results2 = reduce(lor, results2)
    return reduce(lor, [results4, results3, results2, h])

def dynamic_countless3d(data):
    """countless8 + dynamic programming. ~2x faster"""
    sections = []
    data += 1
    factor = (2, 2, 2)
    for offset in np.ndindex(factor):
        part = data[tuple((np.s_[o::f] for o, f in zip(offset, factor)))]
        sections.append(part)
    pick = lambda a, b: a * (a == b)
    lor = lambda x, y: x + (x == 0) * y
    subproblems2 = {}
    results2 = None
    for x, y in combinations(range(7), 2):
        res = pick(sections[x], sections[y])
        subproblems2[x, y] = res
        if results2 is not None:
            results2 += (results2 == 0) * res
        else:
            results2 = res
    subproblems3 = {}
    results3 = None
    for x, y, z in combinations(range(8), 3):
        res = pick(subproblems2[x, y], sections[z])
        if z != 7:
            subproblems3[x, y, z] = res
        if results3 is not None:
            results3 += (results3 == 0) * res
        else:
            results3 = res
    results3 = reduce(lor, (results3, results2, sections[-1]))
    results2 = None
    subproblems2 = None
    res = None
    results4 = (pick(subproblems3[x, y, z], sections[w]) for x, y, z, w in combinations(range(8), 4))
    results4 = reduce(lor, results4)
    subproblems3 = None
    final_result = lor(results4, results3) - 1
    data -= 1
    return final_result

def countless3d(data):
    """Now write countless8 in such a way that it could be used
  to process an image."""
    sections = []
    data += 1
    factor = (2, 2, 2)
    for offset in np.ndindex(factor):
        part = data[tuple((np.s_[o::f] for o, f in zip(offset, factor)))]
        sections.append(part)
    p2 = lambda q, r: q * (q == r)
    p3 = lambda q, r, s: q * ((q == r) & (r == s))
    p4 = lambda p, q, r, s: p * ((p == q) & (q == r) & (r == s))
    lor = lambda x, y: x + (x == 0) * y
    results4 = (p4(x, y, z, w) for x, y, z, w in combinations(sections, 4))
    results4 = reduce(lor, results4)
    results3 = (p3(x, y, z) for x, y, z in combinations(sections, 3))
    results3 = reduce(lor, results3)
    results2 = (p2(x, y) for x, y in combinations(sections[:-1], 2))
    results2 = reduce(lor, results2)
    final_result = reduce(lor, (results4, results3, results2, sections[-1])) - 1
    data -= 1
    return final_result

def countless_generalized(data, factor):
    assert len(data.shape) == len(factor)
    sections = []
    mode_of = reduce(lambda x, y: x * y, factor)
    majority = int(math.ceil(float(mode_of) / 2))
    data += 1
    for offset in np.ndindex(factor):
        part = data[tuple((np.s_[o::f] for o, f in zip(offset, factor)))]
        sections.append(part)

    def pick(elements):
        eq = (elements[i] == elements[i + 1] for i in range(len(elements) - 1))
        anded = reduce(lambda p, q: p & q, eq)
        return elements[0] * anded

    def logical_or(x, y):
        return x + (x == 0) * y
    result = (pick(combo) for combo in combinations(sections, majority))
    result = reduce(logical_or, result)
    for i in range(majority - 1, 3 - 1, -1):
        partial_result = (pick(combo) for combo in combinations(sections, i))
        partial_result = reduce(logical_or, partial_result)
        result = logical_or(result, partial_result)
    partial_result = (pick(combo) for combo in combinations(sections[:-1], 2))
    partial_result = reduce(logical_or, partial_result)
    result = logical_or(result, partial_result)
    result = logical_or(result, sections[-1]) - 1
    data -= 1
    return result

def dynamic_countless_generalized(data, factor):
    assert len(data.shape) == len(factor)
    sections = []
    mode_of = reduce(lambda x, y: x * y, factor)
    majority = int(math.ceil(float(mode_of) / 2))
    data += 1
    for offset in np.ndindex(factor):
        part = data[tuple((np.s_[o::f] for o, f in zip(offset, factor)))]
        sections.append(part)
    pick = lambda a, b: a * (a == b)
    lor = lambda x, y: x + (x == 0) * y
    subproblems = [{}, {}]
    results2 = None
    for x, y in combinations(range(len(sections) - 1), 2):
        res = pick(sections[x], sections[y])
        subproblems[0][x, y] = res
        if results2 is not None:
            results2 = lor(results2, res)
        else:
            results2 = res
    results = [results2]
    for r in range(3, majority + 1):
        r_results = None
        for combo in combinations(range(len(sections)), r):
            res = pick(subproblems[0][combo[:-1]], sections[combo[-1]])
            if combo[-1] != len(sections) - 1:
                subproblems[1][combo] = res
            if r_results is not None:
                r_results = lor(r_results, res)
            else:
                r_results = res
        results.append(r_results)
        subproblems[0] = subproblems[1]
        subproblems[1] = {}
    results.reverse()
    final_result = lor(reduce(lor, results), sections[-1]) - 1
    data -= 1
    return final_result

def downsample_with_averaging(array):
    """
  Downsample x by factor using averaging.

  @return: The downsampled array, of the same type as x.
  """
    factor = (2, 2, 2)
    if np.array_equal(factor[:3], np.array([1, 1, 1])):
        return array
    output_shape = tuple((int(math.ceil(s / f)) for s, f in zip(array.shape, factor)))
    temp = np.zeros(output_shape, float)
    counts = np.zeros(output_shape, np.int)
    for offset in np.ndindex(factor):
        part = array[tuple((np.s_[o::f] for o, f in zip(offset, factor)))]
        indexing_expr = tuple((np.s_[:s] for s in part.shape))
        temp[indexing_expr] += part
        counts[indexing_expr] += 1
    return np.cast[array.dtype](temp / counts)

def downsample_with_max_pooling(array):
    factor = (2, 2, 2)
    sections = []
    for offset in np.ndindex(factor):
        part = array[tuple((np.s_[o::f] for o, f in zip(offset, factor)))]
        sections.append(part)
    output = sections[0].copy()
    for section in sections[1:]:
        np.maximum(output, section, output)
    return output

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

def forward(self, x):
    x = self.features(x)
    x = x.mean(3).mean(2)
    x = self.classifier(x)
    return x

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

def _async_copy(inputs, device_ids):
    nr_devs = len(device_ids)
    assert type(inputs) in (tuple, list)
    assert len(inputs) == nr_devs
    outputs = []
    for i, dev in zip(inputs, device_ids):
        with cuda.device(dev):
            outputs.append(async_copy_to(i, dev))
    return tuple(outputs)

def _async_copy_stream(inputs, device_ids):
    nr_devs = len(device_ids)
    assert type(inputs) in (tuple, list)
    assert len(inputs) == nr_devs
    outputs = []
    streams = [_get_stream(d) for d in device_ids]
    for i, dev, stream in zip(inputs, device_ids, streams):
        with cuda.device(dev):
            main_stream = cuda.current_stream()
            with cuda.stream(stream):
                outputs.append(async_copy_to(i, dev, main_stream=main_stream))
            main_stream.wait_stream(stream)
    return outputs

def execute_replication_callbacks(modules):
    """
    Execute an replication callback `__data_parallel_replicate__` on each module created by original replication.

    The callback will be invoked with arguments `__data_parallel_replicate__(ctx, copy_id)`

    Note that, as all modules are isomorphism, we assign each sub-module with a context
    (shared among multiple copies of this module on different devices).
    Through this context, different copies can share some information.

    We guarantee that the callback on the master copy (the first copy) will be called ahead of calling the callback
    of any slave copies.
    """
    master_copy = modules[0]
    nr_modules = len(list(master_copy.modules()))
    ctxs = [CallbackContext() for _ in range(nr_modules)]
    for i, module in enumerate(modules):
        for j, m in enumerate(module.modules()):
            if hasattr(m, '__data_parallel_replicate__'):
                m.__data_parallel_replicate__(ctxs[j], i)

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

def __call__(self, x, y):
    x_vgg, y_vgg = (self.vgg(x), self.vgg(y))
    content_loss = 0.0
    content_loss += self.weights[0] * self.criterion(x_vgg['relu1_1'], y_vgg['relu1_1'])
    content_loss += self.weights[1] * self.criterion(x_vgg['relu2_1'], y_vgg['relu2_1'])
    content_loss += self.weights[2] * self.criterion(x_vgg['relu3_1'], y_vgg['relu3_1'])
    content_loss += self.weights[3] * self.criterion(x_vgg['relu4_1'], y_vgg['relu4_1'])
    content_loss += self.weights[4] * self.criterion(x_vgg['relu5_1'], y_vgg['relu5_1'])
    return content_loss

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

def get_global_features(self, input):
    check_and_warn_input_range(input, 0, 1, 'PerceptualLoss input in get_global_features')
    if self.normalize_inputs:
        features_input = self.do_normalize_inputs(input)
    else:
        features_input = input
    features_input = self.vgg(features_input)
    return features_input

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

def forward(self, pred, target):
    pred = (pred - IMAGENET_MEAN.to(pred)) / IMAGENET_STD.to(pred)
    target = (target - IMAGENET_MEAN.to(target)) / IMAGENET_STD.to(target)
    pred_feats = self.impl(pred, return_feature_maps=True)
    target_feats = self.impl(target, return_feature_maps=True)
    result = torch.stack([F.mse_loss(cur_pred, cur_target) for cur_pred, cur_target in zip(pred_feats, target_feats)]).sum() * self.weight
    return result

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

def forward(self, x):
    if torch.is_tensor(x):
        return self.inverse_transform(self.impl(self.transform(x)), x)
    elif isinstance(x, tuple):
        x_trans = tuple((self.transform(elem) for elem in x))
        y_trans = self.impl(x_trans)
        return tuple((self.inverse_transform(elem, orig_x) for elem, orig_x in zip(y_trans, x)))
    else:
        raise ValueError(f'Unexpected input type {type(x)}')

class InpaintingEvaluatorOnline(nn.Module):

    def __init__(self, scores, bins=10, image_key='image', inpainted_key='inpainted', integral_func=None, integral_title=None, clamp_image_range=None):
        """
        :param scores: dict {score_name: EvaluatorScore object}
        :param bins: number of groups, partition is generated by np.linspace(0., 1., bins + 1)
        :param device: device to use
        """
        super().__init__()
        LOGGER.info(f'{type(self)} init called')
        self.scores = nn.ModuleDict(scores)
        self.image_key = image_key
        self.inpainted_key = inpainted_key
        self.bins_num = bins
        self.bin_edges = np.linspace(0, 1, self.bins_num + 1)
        num_digits = max(0, math.ceil(math.log10(self.bins_num)) - 1)
        self.interval_names = []
        for idx_bin in range(self.bins_num):
            start_percent, end_percent = (round(100 * self.bin_edges[idx_bin], num_digits), round(100 * self.bin_edges[idx_bin + 1], num_digits))
            start_percent = '{:.{n}f}'.format(start_percent, n=num_digits)
            end_percent = '{:.{n}f}'.format(end_percent, n=num_digits)
            self.interval_names.append('{0}-{1}%'.format(start_percent, end_percent))
        self.groups = []
        self.integral_func = integral_func
        self.integral_title = integral_title
        self.clamp_image_range = clamp_image_range
        LOGGER.info(f'{type(self)} init done')

    def _get_bins(self, mask_batch):
        batch_size = mask_batch.shape[0]
        area = mask_batch.view(batch_size, -1).mean(dim=-1).detach().cpu().numpy()
        bin_indices = np.clip(np.searchsorted(self.bin_edges, area) - 1, 0, self.bins_num - 1)
        return bin_indices

    def forward(self, batch: Dict[str, torch.Tensor]):
        """
        Calculate and accumulate metrics for batch. To finalize evaluation and obtain final metrics, call evaluation_end
        :param batch: batch dict with mandatory fields mask, image, inpainted (can be overriden by self.inpainted_key)
        """
        result = {}
        with torch.no_grad():
            image_batch, mask_batch, inpainted_batch = (batch[self.image_key], batch['mask'], batch[self.inpainted_key])
            if self.clamp_image_range is not None:
                image_batch = torch.clamp(image_batch, min=self.clamp_image_range[0], max=self.clamp_image_range[1])
            self.groups.extend(self._get_bins(mask_batch))
            for score_name, score in self.scores.items():
                result[score_name] = score(inpainted_batch, image_batch, mask_batch)
        return result

    def process_batch(self, batch: Dict[str, torch.Tensor]):
        return self(batch)

    def evaluation_end(self, states=None):
        """:return: dict with (score_name, group_type) as keys, where group_type can be either 'overall' or
            name of the particular group arranged by area of mask (e.g. '10-20%')
            and score statistics for the group as values.
        """
        LOGGER.info(f'{type(self)}: evaluation_end called')
        self.groups = np.array(self.groups)
        results = {}
        for score_name, score in self.scores.items():
            LOGGER.info(f'Getting value of {score_name}')
            cur_states = [s[score_name] for s in states] if states is not None else None
            total_results, group_results = score.get_value(groups=self.groups, states=cur_states)
            LOGGER.info(f'Getting value of {score_name} done')
            results[score_name, 'total'] = total_results
            for group_index, group_values in group_results.items():
                group_name = self.interval_names[group_index]
                results[score_name, group_name] = group_values
        if self.integral_func is not None:
            results[self.integral_title, 'total'] = dict(mean=self.integral_func(results))
        LOGGER.info(f'{type(self)}: reset scores')
        self.groups = []
        for sc in self.scores.values():
            sc.reset()
        LOGGER.info(f'{type(self)}: reset scores done')
        LOGGER.info(f'{type(self)}: evaluation_end done')
        return results

def __init__(self, scores, bins=10, image_key='image', inpainted_key='inpainted', integral_func=None, integral_title=None, clamp_image_range=None):
    """
        :param scores: dict {score_name: EvaluatorScore object}
        :param bins: number of groups, partition is generated by np.linspace(0., 1., bins + 1)
        :param device: device to use
        """
    super().__init__()
    LOGGER.info(f'{type(self)} init called')
    self.scores = nn.ModuleDict(scores)
    self.image_key = image_key
    self.inpainted_key = inpainted_key
    self.bins_num = bins
    self.bin_edges = np.linspace(0, 1, self.bins_num + 1)
    num_digits = max(0, math.ceil(math.log10(self.bins_num)) - 1)
    self.interval_names = []
    for idx_bin in range(self.bins_num):
        start_percent, end_percent = (round(100 * self.bin_edges[idx_bin], num_digits), round(100 * self.bin_edges[idx_bin + 1], num_digits))
        start_percent = '{:.{n}f}'.format(start_percent, n=num_digits)
        end_percent = '{:.{n}f}'.format(end_percent, n=num_digits)
        self.interval_names.append('{0}-{1}%'.format(start_percent, end_percent))
    self.groups = []
    self.integral_func = integral_func
    self.integral_title = integral_title
    self.clamp_image_range = clamp_image_range
    LOGGER.info(f'{type(self)} init done')

def get_groupings(groups):
    """
    :param groups: group numbers for respective elements
    :return: dict of kind {group_idx: indices of the corresponding group elements}
    """
    label_groups, count_groups = np.unique(groups, return_counts=True)
    indices = np.argsort(groups)
    grouping = dict()
    cur_start = 0
    for label, count in zip(label_groups, count_groups):
        cur_end = cur_start + count
        cur_indices = indices[cur_start:cur_end]
        grouping[label] = cur_indices
        cur_start = cur_end
    return grouping

def simplest_countless(data):
    """
  Vectorized implementation of downsampling a 2D 
  image by 2 on each side using the COUNTLESS algorithm.
  
  data is a 2D numpy array with even dimensions.
  """
    sections = []
    factor = (2, 2)
    for offset in np.ndindex(factor):
        part = data[tuple((np.s_[o::f] for o, f in zip(offset, factor)))]
        sections.append(part)
    a, b, c, d = sections
    ab = a * (a == b)
    ac = a * (a == c)
    bc = b * (b == c)
    a = ab | ac | bc
    return a + (a == 0) * d

def quick_countless(data):
    """
  Vectorized implementation of downsampling a 2D 
  image by 2 on each side using the COUNTLESS algorithm.
  
  data is a 2D numpy array with even dimensions.
  """
    sections = []
    factor = (2, 2)
    for offset in np.ndindex(factor):
        part = data[tuple((np.s_[o::f] for o, f in zip(offset, factor)))]
        sections.append(part)
    a, b, c, d = sections
    ab_ac = a * ((a == b) | (a == c))
    bc = b * (b == c)
    a = ab_ac | bc
    return a + (a == 0) * d

def quickest_countless(data):
    """
  Vectorized implementation of downsampling a 2D 
  image by 2 on each side using the COUNTLESS algorithm.
  
  data is a 2D numpy array with even dimensions.
  """
    sections = []
    factor = (2, 2)
    for offset in np.ndindex(factor):
        part = data[tuple((np.s_[o::f] for o, f in zip(offset, factor)))]
        sections.append(part)
    a, b, c, d = sections
    ab_ac = a * ((a == b) | (a == c))
    ab_ac |= b * (b == c)
    return ab_ac + (ab_ac == 0) * d

def quick_countless_xor(data):
    """
  Vectorized implementation of downsampling a 2D 
  image by 2 on each side using the COUNTLESS algorithm.
  
  data is a 2D numpy array with even dimensions.
  """
    sections = []
    factor = (2, 2)
    for offset in np.ndindex(factor):
        part = data[tuple((np.s_[o::f] for o, f in zip(offset, factor)))]
        sections.append(part)
    a, b, c, d = sections
    ab = a ^ (a ^ b)
    ab += (ab != a) * ((ab ^ (ab ^ c)) - b)
    ab += (ab == c) * ((ab ^ (ab ^ d)) - c)
    return ab

def stippled_countless(data):
    """
  Vectorized implementation of downsampling a 2D 
  image by 2 on each side using the COUNTLESS algorithm
  that treats zero as "background" and inflates lone
  pixels.
  
  data is a 2D numpy array with even dimensions.
  """
    sections = []
    factor = (2, 2)
    for offset in np.ndindex(factor):
        part = data[tuple((np.s_[o::f] for o, f in zip(offset, factor)))]
        sections.append(part)
    a, b, c, d = sections
    ab_ac = a * ((a == b) | (a == c))
    ab_ac |= b * (b == c)
    nonzero = a + (a == 0) * (b + (b == 0) * c)
    return ab_ac + (ab_ac == 0) * (d + (d == 0) * nonzero)

def zero_corrected_countless(data):
    """
  Vectorized implementation of downsampling a 2D 
  image by 2 on each side using the COUNTLESS algorithm.
  
  data is a 2D numpy array with even dimensions.
  """
    data, upgraded = upgrade_type(data)
    data += 1
    sections = []
    factor = (2, 2)
    for offset in np.ndindex(factor):
        part = data[tuple((np.s_[o::f] for o, f in zip(offset, factor)))]
        sections.append(part)
    a, b, c, d = sections
    ab = a * (a == b)
    ac = a * (a == c)
    bc = b * (b == c)
    a = ab | ac | bc
    result = a + (a == 0) * d - 1
    if upgraded:
        return downgrade_type(result)
    data -= 1
    return result

def countless_extreme(data):
    nonzeros = np.count_nonzero(data)
    N = reduce(operator.mul, data.shape)
    if nonzeros == N:
        print('quick')
        return quick_countless(data)
    elif np.count_nonzero(data + 1) == N:
        print('quick')
        return quick_countless(data)
    else:
        return countless(data)

def countless(data):
    """
  Vectorized implementation of downsampling a 2D 
  image by 2 on each side using the COUNTLESS algorithm.
  
  data is a 2D numpy array with even dimensions.
  """
    data, upgraded = upgrade_type(data)
    data += 1
    sections = []
    factor = (2, 2)
    for offset in np.ndindex(factor):
        part = data[tuple((np.s_[o::f] for o, f in zip(offset, factor)))]
        sections.append(part)
    a, b, c, d = sections
    ab_ac = a * ((a == b) | (a == c))
    ab_ac |= b * (b == c)
    result = ab_ac + (ab_ac == 0) * d - 1
    if upgraded:
        return downgrade_type(result)
    data -= 1
    return result

def counting(array):
    factor = (2, 2, 1)
    shape = array.shape
    while len(shape) < 4:
        array = np.expand_dims(array, axis=-1)
        shape = array.shape
    output_shape = tuple((int(math.ceil(s / f)) for s, f in zip(shape, factor)))
    output = np.zeros(output_shape, dtype=array.dtype)
    for chan in range(0, shape[3]):
        for z in range(0, shape[2]):
            for x in range(0, shape[0], 2):
                for y in range(0, shape[1], 2):
                    block = array[x:x + 2, y:y + 2, z, chan]
                    hashtable = defaultdict(int)
                    for subx, suby in np.ndindex(block.shape[0], block.shape[1]):
                        hashtable[block[subx, suby]] += 1
                    best = (0, 0)
                    for segid, val in six.iteritems(hashtable):
                        if best[1] < val:
                            best = (segid, val)
                    output[x // 2, y // 2, chan] = best[0]
    return output

def countless_if(array):
    factor = (2, 2, 1)
    shape = array.shape
    if len(shape) < 3:
        array = array[:, :, np.newaxis]
        shape = array.shape
    output_shape = tuple((int(math.ceil(s / f)) for s, f in zip(shape, factor)))
    output = np.zeros(output_shape, dtype=array.dtype)
    for chan in range(0, shape[2]):
        for x in range(0, shape[0], 2):
            for y in range(0, shape[1], 2):
                block = array[x:x + 2, y:y + 2, chan]
                if block[0, 0] == block[1, 0]:
                    pick = block[0, 0]
                elif block[0, 0] == block[0, 1]:
                    pick = block[0, 0]
                elif block[1, 0] == block[0, 1]:
                    pick = block[1, 0]
                else:
                    pick = block[1, 1]
                output[x // 2, y // 2, chan] = pick
    return np.squeeze(output)

def downsample_with_averaging(array):
    """
  Downsample x by factor using averaging.

  @return: The downsampled array, of the same type as x.
  """
    if len(array.shape) == 3:
        factor = (2, 2, 1)
    else:
        factor = (2, 2)
    if np.array_equal(factor[:3], np.array([1, 1, 1])):
        return array
    output_shape = tuple((int(math.ceil(s / f)) for s, f in zip(array.shape, factor)))
    temp = np.zeros(output_shape, float)
    counts = np.zeros(output_shape, np.int)
    for offset in np.ndindex(factor):
        part = array[tuple((np.s_[o::f] for o, f in zip(offset, factor)))]
        indexing_expr = tuple((np.s_[:s] for s in part.shape))
        temp[indexing_expr] += part
        counts[indexing_expr] += 1
    return np.cast[array.dtype](temp / counts)

def downsample_with_max_pooling(array):
    factor = (2, 2)
    if np.all(np.array(factor, int) == 1):
        return array
    sections = []
    for offset in np.ndindex(factor):
        part = array[tuple((np.s_[o::f] for o, f in zip(offset, factor)))]
        sections.append(part)
    output = sections[0].copy()
    for section in sections[1:]:
        np.maximum(output, section, output)
    return output

def countless5(a, b, c, d, e):
    """First stage of generalizing from countless2d. 

  You have five slots: A, B, C, D, E

  You can decide if something is the winner by first checking for 
  matches of three, then matches of two, then picking just one if 
  the other two tries fail. In countless2d, you just check for matches
  of two and then pick one of them otherwise.

  Unfortunately, you need to check ABC, ABD, ABE, BCD, BDE, & CDE.
  Then you need to check AB, AC, AD, BC, BD
  We skip checking E because if none of these match, we pick E. We can
  skip checking AE, BE, CE, DE since if any of those match, E is our boy
  so it's redundant.

  So countless grows cominatorially in complexity.
  """
    sections = [a, b, c, d, e]
    p2 = lambda q, r: q * (q == r)
    p3 = lambda q, r, s: q * ((q == r) & (r == s))
    lor = lambda x, y: x + (x == 0) * y
    results3 = (p3(x, y, z) for x, y, z in combinations(sections, 3))
    results3 = reduce(lor, results3)
    results2 = (p2(x, y) for x, y in combinations(sections[:-1], 2))
    results2 = reduce(lor, results2)
    return reduce(lor, (results3, results2, e))

def countless8(a, b, c, d, e, f, g, h):
    """Extend countless5 to countless8. Same deal, except we also
    need to check for matches of length 4."""
    sections = [a, b, c, d, e, f, g, h]
    p2 = lambda q, r: q * (q == r)
    p3 = lambda q, r, s: q * ((q == r) & (r == s))
    p4 = lambda p, q, r, s: p * ((p == q) & (q == r) & (r == s))
    lor = lambda x, y: x + (x == 0) * y
    results4 = (p4(x, y, z, w) for x, y, z, w in combinations(sections, 4))
    results4 = reduce(lor, results4)
    results3 = (p3(x, y, z) for x, y, z in combinations(sections, 3))
    results3 = reduce(lor, results3)
    results2 = (p2(x, y) for x, y in combinations(sections[:-1], 2))
    results2 = reduce(lor, results2)
    return reduce(lor, [results4, results3, results2, h])

def dynamic_countless3d(data):
    """countless8 + dynamic programming. ~2x faster"""
    sections = []
    data += 1
    factor = (2, 2, 2)
    for offset in np.ndindex(factor):
        part = data[tuple((np.s_[o::f] for o, f in zip(offset, factor)))]
        sections.append(part)
    pick = lambda a, b: a * (a == b)
    lor = lambda x, y: x + (x == 0) * y
    subproblems2 = {}
    results2 = None
    for x, y in combinations(range(7), 2):
        res = pick(sections[x], sections[y])
        subproblems2[x, y] = res
        if results2 is not None:
            results2 += (results2 == 0) * res
        else:
            results2 = res
    subproblems3 = {}
    results3 = None
    for x, y, z in combinations(range(8), 3):
        res = pick(subproblems2[x, y], sections[z])
        if z != 7:
            subproblems3[x, y, z] = res
        if results3 is not None:
            results3 += (results3 == 0) * res
        else:
            results3 = res
    results3 = reduce(lor, (results3, results2, sections[-1]))
    results2 = None
    subproblems2 = None
    res = None
    results4 = (pick(subproblems3[x, y, z], sections[w]) for x, y, z, w in combinations(range(8), 4))
    results4 = reduce(lor, results4)
    subproblems3 = None
    final_result = lor(results4, results3) - 1
    data -= 1
    return final_result

def countless3d(data):
    """Now write countless8 in such a way that it could be used
  to process an image."""
    sections = []
    data += 1
    factor = (2, 2, 2)
    for offset in np.ndindex(factor):
        part = data[tuple((np.s_[o::f] for o, f in zip(offset, factor)))]
        sections.append(part)
    p2 = lambda q, r: q * (q == r)
    p3 = lambda q, r, s: q * ((q == r) & (r == s))
    p4 = lambda p, q, r, s: p * ((p == q) & (q == r) & (r == s))
    lor = lambda x, y: x + (x == 0) * y
    results4 = (p4(x, y, z, w) for x, y, z, w in combinations(sections, 4))
    results4 = reduce(lor, results4)
    results3 = (p3(x, y, z) for x, y, z in combinations(sections, 3))
    results3 = reduce(lor, results3)
    results2 = (p2(x, y) for x, y in combinations(sections[:-1], 2))
    results2 = reduce(lor, results2)
    final_result = reduce(lor, (results4, results3, results2, sections[-1])) - 1
    data -= 1
    return final_result

def countless_generalized(data, factor):
    assert len(data.shape) == len(factor)
    sections = []
    mode_of = reduce(lambda x, y: x * y, factor)
    majority = int(math.ceil(float(mode_of) / 2))
    data += 1
    for offset in np.ndindex(factor):
        part = data[tuple((np.s_[o::f] for o, f in zip(offset, factor)))]
        sections.append(part)

    def pick(elements):
        eq = (elements[i] == elements[i + 1] for i in range(len(elements) - 1))
        anded = reduce(lambda p, q: p & q, eq)
        return elements[0] * anded

    def logical_or(x, y):
        return x + (x == 0) * y
    result = (pick(combo) for combo in combinations(sections, majority))
    result = reduce(logical_or, result)
    for i in range(majority - 1, 3 - 1, -1):
        partial_result = (pick(combo) for combo in combinations(sections, i))
        partial_result = reduce(logical_or, partial_result)
        result = logical_or(result, partial_result)
    partial_result = (pick(combo) for combo in combinations(sections[:-1], 2))
    partial_result = reduce(logical_or, partial_result)
    result = logical_or(result, partial_result)
    result = logical_or(result, sections[-1]) - 1
    data -= 1
    return result

def dynamic_countless_generalized(data, factor):
    assert len(data.shape) == len(factor)
    sections = []
    mode_of = reduce(lambda x, y: x * y, factor)
    majority = int(math.ceil(float(mode_of) / 2))
    data += 1
    for offset in np.ndindex(factor):
        part = data[tuple((np.s_[o::f] for o, f in zip(offset, factor)))]
        sections.append(part)
    pick = lambda a, b: a * (a == b)
    lor = lambda x, y: x + (x == 0) * y
    subproblems = [{}, {}]
    results2 = None
    for x, y in combinations(range(len(sections) - 1), 2):
        res = pick(sections[x], sections[y])
        subproblems[0][x, y] = res
        if results2 is not None:
            results2 = lor(results2, res)
        else:
            results2 = res
    results = [results2]
    for r in range(3, majority + 1):
        r_results = None
        for combo in combinations(range(len(sections)), r):
            res = pick(subproblems[0][combo[:-1]], sections[combo[-1]])
            if combo[-1] != len(sections) - 1:
                subproblems[1][combo] = res
            if r_results is not None:
                r_results = lor(r_results, res)
            else:
                r_results = res
        results.append(r_results)
        subproblems[0] = subproblems[1]
        subproblems[1] = {}
    results.reverse()
    final_result = lor(reduce(lor, results), sections[-1]) - 1
    data -= 1
    return final_result

def downsample_with_averaging(array):
    """
  Downsample x by factor using averaging.

  @return: The downsampled array, of the same type as x.
  """
    factor = (2, 2, 2)
    if np.array_equal(factor[:3], np.array([1, 1, 1])):
        return array
    output_shape = tuple((int(math.ceil(s / f)) for s, f in zip(array.shape, factor)))
    temp = np.zeros(output_shape, float)
    counts = np.zeros(output_shape, np.int)
    for offset in np.ndindex(factor):
        part = array[tuple((np.s_[o::f] for o, f in zip(offset, factor)))]
        indexing_expr = tuple((np.s_[:s] for s in part.shape))
        temp[indexing_expr] += part
        counts[indexing_expr] += 1
    return np.cast[array.dtype](temp / counts)

def downsample_with_max_pooling(array):
    factor = (2, 2, 2)
    sections = []
    for offset in np.ndindex(factor):
        part = array[tuple((np.s_[o::f] for o, f in zip(offset, factor)))]
        sections.append(part)
    output = sections[0].copy()
    for section in sections[1:]:
        np.maximum(output, section, output)
    return output

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

def forward(self, x):
    x = self.features(x)
    x = x.mean(3).mean(2)
    x = self.classifier(x)
    return x

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

def _async_copy(inputs, device_ids):
    nr_devs = len(device_ids)
    assert type(inputs) in (tuple, list)
    assert len(inputs) == nr_devs
    outputs = []
    for i, dev in zip(inputs, device_ids):
        with cuda.device(dev):
            outputs.append(async_copy_to(i, dev))
    return tuple(outputs)

def _async_copy_stream(inputs, device_ids):
    nr_devs = len(device_ids)
    assert type(inputs) in (tuple, list)
    assert len(inputs) == nr_devs
    outputs = []
    streams = [_get_stream(d) for d in device_ids]
    for i, dev, stream in zip(inputs, device_ids, streams):
        with cuda.device(dev):
            main_stream = cuda.current_stream()
            with cuda.stream(stream):
                outputs.append(async_copy_to(i, dev, main_stream=main_stream))
            main_stream.wait_stream(stream)
    return outputs

def execute_replication_callbacks(modules):
    """
    Execute an replication callback `__data_parallel_replicate__` on each module created by original replication.

    The callback will be invoked with arguments `__data_parallel_replicate__(ctx, copy_id)`

    Note that, as all modules are isomorphism, we assign each sub-module with a context
    (shared among multiple copies of this module on different devices).
    Through this context, different copies can share some information.

    We guarantee that the callback on the master copy (the first copy) will be called ahead of calling the callback
    of any slave copies.
    """
    master_copy = modules[0]
    nr_modules = len(list(master_copy.modules()))
    ctxs = [CallbackContext() for _ in range(nr_modules)]
    for i, module in enumerate(modules):
        for j, m in enumerate(module.modules()):
            if hasattr(m, '__data_parallel_replicate__'):
                m.__data_parallel_replicate__(ctxs[j], i)

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

@functools.wraps(op)
def oplist(*args, **kwargs):
    if len(args) == 0:
        raise ValueError('Must be at least one argument without keyword (i.e. operand).')
    if len(args) == 1:
        if islist(args[0]):
            return TensorList([op(a, **kwargs) for a in args[0]])
    else:
        if islist(args[0]) and islist(args[1]):
            return TensorList([op(a, b, *args[2:], **kwargs) for a, b in zip(*args[:2])])
        if islist(args[0]):
            return TensorList([op(a, *args[1:], **kwargs) for a in args[0]])
        if islist(args[1]):
            return TensorList([op(args[0], b, *args[2:], **kwargs) for b in args[1]])
    return op(*args, **kwargs)

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

def update(self, value, n=1):
    self.deque.append(value)
    self.count += n
    self.total += value * n

def reduce_dict(input_dict, average=True):
    """
    Args:
        input_dict (dict): all the values will be reduced
        average (bool): whether to do average or sum
    Reduce the values in the dictionary from all processes so that all processes
    have the averaged results. Returns a dict with the same fields as
    input_dict, after reduction.
    """
    world_size = get_world_size()
    if world_size < 2:
        return input_dict
    with torch.no_grad():
        names = []
        values = []
        for k in sorted(input_dict.keys()):
            names.append(k)
            values.append(input_dict[k])
        values = torch.stack(values, dim=0)
        dist.all_reduce(values)
        if average:
            values /= world_size
        reduced_dict = {k: v for k, v in zip(names, values)}
    return reduced_dict

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

def __init__(self, delimiter='\t'):
    self.meters = defaultdict(SmoothedValue)
    self.delimiter = delimiter

def collate_fn(batch):
    batch = list(zip(*batch))
    batch[0] = nested_tensor_from_tensor_list(batch[0])
    return tuple(batch)

def _max_by_axis(the_list):
    maxes = the_list[0]
    for sublist in the_list[1:]:
        for index, item in enumerate(sublist):
            maxes[index] = max(maxes[index], item)
    return maxes

@torch.jit.unused
def _onnx_nested_tensor_from_tensor_list(tensor_list: List[Tensor]) -> NestedTensor:
    max_size = []
    for i in range(tensor_list[0].dim()):
        max_size_i = torch.max(torch.stack([img.shape[i] for img in tensor_list]).to(torch.float32)).to(torch.int64)
        max_size.append(max_size_i)
    max_size = tuple(max_size)
    padded_imgs = []
    padded_masks = []
    for img in tensor_list:
        padding = [s1 - s2 for s1, s2 in zip(max_size, tuple(img.shape))]
        padded_img = torch.nn.functional.pad(img, (0, padding[2], 0, padding[1], 0, padding[0]))
        padded_imgs.append(padded_img)
        m = torch.zeros_like(img[0], dtype=torch.int, device=img.device)
        padded_mask = torch.nn.functional.pad(m, (0, padding[2], 0, padding[1]), 'constant', 1)
        padded_masks.append(padded_mask.to(torch.bool))
    tensor = torch.stack(padded_imgs)
    mask = torch.stack(padded_masks)
    return NestedTensor(tensor, mask=mask)

def get_keep_indices(decisions):
    keep_indices = []
    for i in range(3):
        if i == 0:
            keep_indices.append(decisions[i])
        else:
            keep_indices.append(keep_indices[-1][decisions[i]])
    return keep_indices

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

def add_hook(self):
    conv_features, enc_attn_weights, dec_attn_weights = ([], [], [])
    for i in range(12):
        self.network.backbone.blocks[i].attn.register_forward_hook(lambda self, input, output: enc_attn_weights.append(output[1]))
    self.enc_attn_weights = enc_attn_weights

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

def forward(self, x):
    for i, layer in enumerate(self.layers):
        x = F.relu(layer(x)) if i < self.num_layers - 1 else layer(x)
    return x

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

class GEGLU(nn.Module):

    def __init__(self, dim_in, dim_out):
        super().__init__()
        self.proj = nn.Linear(dim_in, dim_out * 2)

    def forward(self, x):
        x, gate = self.proj(x).chunk(2, dim=-1)
        return x * F.gelu(gate)

def forward(self, x):
    x, gate = self.proj(x).chunk(2, dim=-1)
    return x * F.gelu(gate)

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

class GEGLU(nn.Module):

    def __init__(self, dim_in, dim_out):
        super().__init__()
        self.proj = nn.Linear(dim_in, dim_out * 2)

    def forward(self, x):
        x, gate = self.proj(x).chunk(2, dim=-1)
        return x * F.gelu(gate)

def forward(self, x):
    x, gate = self.proj(x).chunk(2, dim=-1)
    return x * F.gelu(gate)

class TimestepEmbedSequential(nn.Sequential, TimestepBlock):
    """
    A sequential module that passes timestep embeddings to the children that
    support it as an extra input.
    """

    def forward(self, x, emb, context=None):
        for layer in self:
            if isinstance(layer, TimestepBlock):
                x = layer(x, emb)
            elif isinstance(layer, SpatialTransformer):
                x = layer(x, context)
            else:
                x = layer(x)
        return x

def forward(self, x, emb, context=None):
    for layer in self:
        if isinstance(layer, TimestepBlock):
            x = layer(x, emb)
        elif isinstance(layer, SpatialTransformer):
            x = layer(x, context)
        else:
            x = layer(x)
    return x

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

def forward(self, x):
    assert x.shape[1] == self.channels
    return self.op(x)

def nonlinearity(x):
    return x * torch.sigmoid(x)

class SiLU(nn.Module):

    def forward(self, x):
        return x * torch.sigmoid(x)

def forward(self, x):
    return x * torch.sigmoid(x)

def getColorList():
    dict = collections.defaultdict(list)
    lower_black = np.array([0, 0, 0])
    upper_black = np.array([180, 255, 46])
    color_list = []
    color_list.append(lower_black)
    color_list.append(upper_black)
    dict['black'] = color_list
    lower_white = np.array([0, 0, 221])
    upper_white = np.array([180, 30, 255])
    color_list = []
    color_list.append(lower_white)
    color_list.append(upper_white)
    dict['white'] = color_list
    lower_red = np.array([156, 43, 46])
    upper_red = np.array([180, 255, 255])
    color_list = []
    color_list.append(lower_red)
    color_list.append(upper_red)
    dict['red'] = color_list
    lower_red = np.array([0, 43, 46])
    upper_red = np.array([10, 255, 255])
    color_list = []
    color_list.append(lower_red)
    color_list.append(upper_red)
    dict['red2'] = color_list
    lower_orange = np.array([11, 43, 46])
    upper_orange = np.array([25, 255, 255])
    color_list = []
    color_list.append(lower_orange)
    color_list.append(upper_orange)
    dict['orange'] = color_list
    lower_yellow = np.array([26, 43, 46])
    upper_yellow = np.array([34, 255, 255])
    color_list = []
    color_list.append(lower_yellow)
    color_list.append(upper_yellow)
    dict['yellow'] = color_list
    lower_green = np.array([35, 43, 46])
    upper_green = np.array([77, 255, 255])
    color_list = []
    color_list.append(lower_green)
    color_list.append(upper_green)
    dict['green'] = color_list
    lower_cyan = np.array([78, 43, 46])
    upper_cyan = np.array([99, 255, 255])
    color_list = []
    color_list.append(lower_cyan)
    color_list.append(upper_cyan)
    dict['cyan'] = color_list
    lower_blue = np.array([100, 43, 46])
    upper_blue = np.array([124, 255, 255])
    color_list = []
    color_list.append(lower_blue)
    color_list.append(upper_blue)
    dict['blue'] = color_list
    lower_purple = np.array([125, 43, 46])
    upper_purple = np.array([155, 255, 255])
    color_list = []
    color_list.append(lower_purple)
    color_list.append(upper_purple)
    dict['purple'] = color_list
    return dict

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

def expand_depth(depth_vp, neighbor_size=1, bg_value=10000000000.0):
    """
        depth_vp: np.ndarray
            shape: [H, W, 1]
        neighbor_size: int
            kernel size, but not used currently
    """
    bg_pos = depth_vp == bg_value
    neighbor_depth = np.zeros((depth_vp.shape[0], depth_vp.shape[1], 5))
    neighbor_depth[:, :, 0] = depth_vp[:, :, 0]
    for idx, axis_shift in enumerate([(0, 1), (0, -1), (1, 1), (1, -1)]):
        axis, shift = axis_shift
        depth_vp_new = np.roll(depth_vp[:, :, 0], axis=axis, shift=shift)
        if axis == 0:
            target = 0 if shift == 1 else -1
            depth_vp_new[target] = bg_value
        if axis == 1:
            target = 0 if shift == 1 else -1
            depth_vp_new[:, target] = bg_value
        neighbor_depth[:, :, idx + 1] = depth_vp_new
    bg_neighbor_depth = np.min(neighbor_depth, axis=2)[..., np.newaxis]
    return bg_pos * bg_neighbor_depth + (1 - bg_pos) * depth_vp

def transform_node_to_lane(input_map, pre_transform=True):
    output_lane_map = {}
    edge_lanes = []
    for edge in input_map['boundary']:
        N = edge.shape[0]
        edge_lane = np.zeros((N, 6))
        edge_lane[:, :2] = edge[:, :2]
        edge_lane[:-1, 2:4] = edge[1:, :2]
        edge_lane[:, -2] = 0
        edge_lane = edge_lane[:-1]
        edge_lanes.append(edge_lane)
    centerline_lanes = []
    for i, centerline in enumerate(input_map['centerline']):
        if pre_transform:
            centerline = centerline[centerline[:, 0] > 0]
        N = centerline.shape[0]
        if N > 0:
            centerline_lane = np.zeros((N, 6))
            centerline_lane[:, :2] = centerline[:, :2]
            centerline_lane[:-1, 2:4] = centerline[1:, :2]
            centerline_lane[:, -2] = 1
            if np.linalg.norm(centerline[-1]) - np.linalg.norm(centerline[0]) > 0:
                centerline_lane[:, -1] = 1
            else:
                centerline_lane[:, -1] = 0
            centerline_lane = centerline_lane[:-1]
            centerline_lanes.append(centerline_lane)
    output_lane_map['boundary'] = np.concatenate(edge_lanes, axis=0)
    output_lane_map['centerline'] = np.concatenate(centerline_lanes, axis=0)
    if pre_transform:
        output_lane_map = crop_map(output_lane_map)
    return output_lane_map

