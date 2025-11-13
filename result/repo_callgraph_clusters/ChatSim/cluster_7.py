# Cluster 7

def rotmat2qvec(R):
    Rxx, Ryx, Rzx, Rxy, Ryy, Rzy, Rxz, Ryz, Rzz = R.flat
    K = np.array([[Rxx - Ryy - Rzz, 0, 0, 0], [Ryx + Rxy, Ryy - Rxx - Rzz, 0, 0], [Rzx + Rxz, Rzy + Ryz, Rzz - Rxx - Ryy, 0], [Ryz - Rzy, Rzx - Rxz, Rxy - Ryx, Rxx + Ryy + Rzz]]) / 3.0
    eigvals, eigvecs = np.linalg.eigh(K)
    qvec = eigvecs[[3, 0, 1, 2], np.argmax(eigvals)]
    if qvec[0] < 0:
        qvec *= -1
    return qvec

def read_intrinsic(intrinsic_params_vector):
    return dict(zip(['f_u', 'f_v', 'c_u', 'c_v', 'k_1', 'k_2', 'p_1', 'p_2', 'k_3'], intrinsic_params_vector))

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

def get_filtered_points3D(self, return_colors=False):
    point3D_idxs = [idx for idx in self.point3D_id_to_point3D_idx.values() if idx != SceneManager.INVALID_POINT3D]
    result = [self.points3D[point3D_idxs, :]]
    if return_colors:
        result += [self.point3D_colors[point3D_idxs, :]]
    return result if len(result) > 1 else result[0]

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

def get_filtered_points3D(self, return_colors=False):
    point3D_idxs = [idx for idx in self.point3D_id_to_point3D_idx.values() if idx != SceneManager.INVALID_POINT3D]
    result = [self.points3D[point3D_idxs, :]]
    if return_colors:
        result += [self.point3D_colors[point3D_idxs, :]]
    return result if len(result) > 1 else result[0]

def rotmat2qvec(R):
    Rxx, Ryx, Rzx, Rxy, Ryy, Rzy, Rxz, Ryz, Rzz = R.flat
    K = np.array([[Rxx - Ryy - Rzz, 0, 0, 0], [Ryx + Rxy, Ryy - Rxx - Rzz, 0, 0], [Rzx + Rxz, Rzy + Ryz, Rzz - Rxx - Ryy, 0], [Ryz - Rzy, Rzx - Rxz, Rxy - Ryx, Rxx + Ryy + Rzz]]) / 3.0
    eigvals, eigvecs = np.linalg.eigh(K)
    qvec = eigvecs[[3, 0, 1, 2], np.argmax(eigvals)]
    if qvec[0] < 0:
        qvec *= -1
    return qvec

def inverse_sigmoid(x):
    return torch.log(x / (1 - x))

def strip_lowerdiag(L):
    uncertainty = torch.zeros((L.shape[0], 6), dtype=torch.float, device='cuda')
    uncertainty[:, 0] = L[:, 0, 0]
    uncertainty[:, 1] = L[:, 0, 1]
    uncertainty[:, 2] = L[:, 0, 2]
    uncertainty[:, 3] = L[:, 1, 1]
    uncertainty[:, 4] = L[:, 1, 2]
    uncertainty[:, 5] = L[:, 2, 2]
    return uncertainty

def build_scaling_rotation(s, r):
    L = torch.zeros((s.shape[0], 3, 3), dtype=torch.float, device='cuda')
    R = build_rotation(r)
    L[:, 0, 0] = s[:, 0]
    L[:, 1, 1] = s[:, 1]
    L[:, 2, 2] = s[:, 2]
    L = R @ L
    return L

def getProjectionMatrixFromK(znear, zfar, W, H, K):
    """
    Args:
        K is np.ndarray including [fx, fy, cx, cy]
    """
    fx, fy, cx, cy = K.tolist()
    P = torch.zeros(4, 4)
    z_sign = 1.0
    P[0, 0] = 2 * fx / W
    P[1, 1] = 2 * fy / H
    P[0, 2] = 2 * (cx / W) - 1
    P[1, 2] = 2 * (cy / H) - 1
    P[3, 2] = z_sign
    P[2, 2] = z_sign * zfar / (zfar - znear)
    P[2, 3] = -(zfar * znear) / (zfar - znear)
    return P

def rotmat2qvec(R):
    Rxx, Ryx, Rzx, Rxy, Ryy, Rzy, Rxz, Ryz, Rzz = R.flat
    K = np.array([[Rxx - Ryy - Rzz, 0, 0, 0], [Ryx + Rxy, Ryy - Rxx - Rzz, 0, 0], [Rzx + Rxz, Rzy + Ryz, Rzz - Rxx - Ryy, 0], [Ryz - Rzy, Rzx - Rxz, Rxy - Ryx, Rxx + Ryy + Rzz]]) / 3.0
    eigvals, eigvecs = np.linalg.eigh(K)
    qvec = eigvecs[[3, 0, 1, 2], np.argmax(eigvals)]
    if qvec[0] < 0:
        qvec *= -1
    return qvec

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

def flatten(cubemap):
    """
    flatten the cube map for visualization
    Args:
        cubemap : torch.tensor
            shape [6, N, N, C], C usually 3
    Returns:
        cubemap_flatten : torch.tensor
            shape [3*N, 4*N, C]
    """
    view_names = ['right', 'left', 'top', 'bottom', 'back', 'front']
    cubemap_vis = torch.clone(cubemap).detach()
    for i, view_name in enumerate(view_names):
        cubemap_vis[i] = convert_cubemap_torch(cubemap_vis[i], view_name)
    _, N, N, C = cubemap_vis.shape
    cubemap_flatten = torch.zeros(N * 3, N * 4, C).to(cubemap)
    cubemap_flatten[:N, N:2 * N] = cubemap_vis[2]
    cubemap_flatten[N:2 * N, :N] = cubemap_vis[1]
    cubemap_flatten[N:2 * N, N:2 * N] = cubemap_vis[5]
    cubemap_flatten[N:2 * N, 2 * N:3 * N] = cubemap_vis[0]
    cubemap_flatten[N:2 * N, 3 * N:4 * N] = cubemap_vis[4]
    cubemap_flatten[2 * N:3 * N, N:2 * N] = cubemap_vis[3]
    return cubemap_flatten

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

class SpectralNorm(object):
    _version = 1

    def __init__(self, name='weight', n_power_iterations=1, dim=0, eps=1e-12):
        self.name = name
        self.dim = dim
        if n_power_iterations <= 0:
            raise ValueError('Expected n_power_iterations to be positive, but got n_power_iterations={}'.format(n_power_iterations))
        self.n_power_iterations = n_power_iterations
        self.eps = eps

    def reshape_weight_to_matrix(self, weight):
        weight_mat = weight
        if self.dim != 0:
            weight_mat = weight_mat.permute(self.dim, *[d for d in range(weight_mat.dim()) if d != self.dim])
        height = weight_mat.size(0)
        return weight_mat.reshape(height, -1)

    def compute_weight(self, module, do_power_iteration):
        weight = getattr(module, self.name + '_orig')
        u = getattr(module, self.name + '_u')
        v = getattr(module, self.name + '_v')
        weight_mat = self.reshape_weight_to_matrix(weight)
        if do_power_iteration:
            with torch.no_grad():
                for _ in range(self.n_power_iterations):
                    v = normalize(torch.mv(weight_mat.t(), u), dim=0, eps=self.eps, out=v)
                    u = normalize(torch.mv(weight_mat, v), dim=0, eps=self.eps, out=u)
                if self.n_power_iterations > 0:
                    u = u.clone()
                    v = v.clone()
        sigma = torch.dot(u, torch.mv(weight_mat, v))
        weight = weight / sigma
        return weight

    def remove(self, module):
        with torch.no_grad():
            weight = self.compute_weight(module, do_power_iteration=False)
        delattr(module, self.name)
        delattr(module, self.name + '_u')
        delattr(module, self.name + '_v')
        delattr(module, self.name + '_orig')
        module.register_parameter(self.name, torch.nn.Parameter(weight.detach()))

    def __call__(self, module, inputs):
        setattr(module, self.name, self.compute_weight(module, do_power_iteration=module.training))

    def _solve_v_and_rescale(self, weight_mat, u, target_sigma):
        v = torch.chain_matmul(weight_mat.t().mm(weight_mat).pinverse(), weight_mat.t(), u.unsqueeze(1)).squeeze(1)
        return v.mul_(target_sigma / torch.dot(u, torch.mv(weight_mat, v)))

    @staticmethod
    def apply(module, name, n_power_iterations, dim, eps):
        for k, hook in module._forward_pre_hooks.items():
            if isinstance(hook, SpectralNorm) and hook.name == name:
                raise RuntimeError('Cannot register two spectral_norm hooks on the same parameter {}'.format(name))
        fn = SpectralNorm(name, n_power_iterations, dim, eps)
        weight = module._parameters[name]
        with torch.no_grad():
            weight_mat = fn.reshape_weight_to_matrix(weight)
            h, w = weight_mat.size()
            u = normalize(weight.new_empty(h).normal_(0, 1), dim=0, eps=fn.eps)
            v = normalize(weight.new_empty(w).normal_(0, 1), dim=0, eps=fn.eps)
        delattr(module, fn.name)
        module.register_parameter(fn.name + '_orig', weight)
        setattr(module, fn.name, weight.data)
        module.register_buffer(fn.name + '_u', u)
        module.register_buffer(fn.name + '_v', v)
        module.register_forward_pre_hook(fn)
        module._register_state_dict_hook(SpectralNormStateDictHook(fn))
        module._register_load_state_dict_pre_hook(SpectralNormLoadStateDictPreHook(fn))
        return fn

def compute_weight(self, module, do_power_iteration):
    weight = getattr(module, self.name + '_orig')
    u = getattr(module, self.name + '_u')
    v = getattr(module, self.name + '_v')
    weight_mat = self.reshape_weight_to_matrix(weight)
    if do_power_iteration:
        with torch.no_grad():
            for _ in range(self.n_power_iterations):
                v = normalize(torch.mv(weight_mat.t(), u), dim=0, eps=self.eps, out=v)
                u = normalize(torch.mv(weight_mat, v), dim=0, eps=self.eps, out=u)
            if self.n_power_iterations > 0:
                u = u.clone()
                v = v.clone()
    sigma = torch.dot(u, torch.mv(weight_mat, v))
    weight = weight / sigma
    return weight

class SpectralNormLoadStateDictPreHook(object):

    def __init__(self, fn):
        self.fn = fn

    def __call__(self, state_dict, prefix, local_metadata, strict, missing_keys, unexpected_keys, error_msgs):
        fn = self.fn
        version = local_metadata.get('spectral_norm', {}).get(fn.name + '.version', None)
        if version is None or version < 1:
            with torch.no_grad():
                weight_orig = state_dict[prefix + fn.name + '_orig']
                weight_mat = fn.reshape_weight_to_matrix(weight_orig)
                u = state_dict[prefix + fn.name + '_u']

def __call__(self, state_dict, prefix, local_metadata, strict, missing_keys, unexpected_keys, error_msgs):
    fn = self.fn
    version = local_metadata.get('spectral_norm', {}).get(fn.name + '.version', None)
    if version is None or version < 1:
        with torch.no_grad():
            weight_orig = state_dict[prefix + fn.name + '_orig']
            weight_mat = fn.reshape_weight_to_matrix(weight_orig)
            u = state_dict[prefix + fn.name + '_u']

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

def _check_lr_scale(m):
    for p in m.parameters():
        assert hasattr(p, 'lr_scale'), p.param_name

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

def select_masks(self, masks: torch.Tensor, iou_preds: torch.Tensor, num_points: int) -> Tuple[torch.Tensor, torch.Tensor]:
    score_reweight = torch.tensor([[1000] + [0] * (self.model.mask_decoder.num_mask_tokens - 1)]).to(iou_preds.device)
    score = iou_preds + (num_points - 2.5) * score_reweight
    best_idx = torch.argmax(score, dim=1)
    masks = masks[torch.arange(masks.shape[0]), best_idx, :, :].unsqueeze(1)
    iou_preds = iou_preds[torch.arange(masks.shape[0]), best_idx].unsqueeze(1)
    return (masks, iou_preds)

class MaskData:
    """
    A structure for storing masks and their related data in batched format.
    Implements basic filtering and concatenation.
    """

    def __init__(self, **kwargs) -> None:
        for v in kwargs.values():
            assert isinstance(v, (list, np.ndarray, torch.Tensor)), 'MaskData only supports list, numpy arrays, and torch tensors.'
        self._stats = dict(**kwargs)

    def __setitem__(self, key: str, item: Any) -> None:
        assert isinstance(item, (list, np.ndarray, torch.Tensor)), 'MaskData only supports list, numpy arrays, and torch tensors.'
        self._stats[key] = item

    def __delitem__(self, key: str) -> None:
        del self._stats[key]

    def __getitem__(self, key: str) -> Any:
        return self._stats[key]

    def items(self) -> ItemsView[str, Any]:
        return self._stats.items()

    def filter(self, keep: torch.Tensor) -> None:
        for k, v in self._stats.items():
            if v is None:
                self._stats[k] = None
            elif isinstance(v, torch.Tensor):
                self._stats[k] = v[torch.as_tensor(keep, device=v.device)]
            elif isinstance(v, np.ndarray):
                self._stats[k] = v[keep.detach().cpu().numpy()]
            elif isinstance(v, list) and keep.dtype == torch.bool:
                self._stats[k] = [a for i, a in enumerate(v) if keep[i]]
            elif isinstance(v, list):
                self._stats[k] = [v[i] for i in keep]
            else:
                raise TypeError(f'MaskData key {k} has an unsupported type {type(v)}.')

    def cat(self, new_stats: 'MaskData') -> None:
        for k, v in new_stats.items():
            if k not in self._stats or self._stats[k] is None:
                self._stats[k] = deepcopy(v)
            elif isinstance(v, torch.Tensor):
                self._stats[k] = torch.cat([self._stats[k], v], dim=0)
            elif isinstance(v, np.ndarray):
                self._stats[k] = np.concatenate([self._stats[k], v], axis=0)
            elif isinstance(v, list):
                self._stats[k] = self._stats[k] + deepcopy(v)
            else:
                raise TypeError(f'MaskData key {k} has an unsupported type {type(v)}.')

    def to_numpy(self) -> None:
        for k, v in self._stats.items():
            if isinstance(v, torch.Tensor):
                self._stats[k] = v.detach().cpu().numpy()

def __init__(self, **kwargs) -> None:
    for v in kwargs.values():
        assert isinstance(v, (list, np.ndarray, torch.Tensor)), 'MaskData only supports list, numpy arrays, and torch tensors.'
    self._stats = dict(**kwargs)

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

def __getitem__(self, index):
    img = self.dataset[index]
    mask = self.mask.clone()
    inpainted = self.model(img[None, ...], mask[None, ...])
    return dict(image=img, mask=mask, inpainted=inpainted)

class NonSaturatingWithR1(BaseAdversarialLoss):

    def __init__(self, gp_coef=5, weight=1, mask_as_fake_target=False, allow_scale_mask=False, mask_scale_mode='nearest', extra_mask_weight_for_gen=0, use_unmasked_for_gen=True, use_unmasked_for_discr=True):
        self.gp_coef = gp_coef
        self.weight = weight
        assert use_unmasked_for_gen or not use_unmasked_for_discr
        assert use_unmasked_for_discr or not mask_as_fake_target
        self.use_unmasked_for_gen = use_unmasked_for_gen
        self.use_unmasked_for_discr = use_unmasked_for_discr
        self.mask_as_fake_target = mask_as_fake_target
        self.allow_scale_mask = allow_scale_mask
        self.mask_scale_mode = mask_scale_mode
        self.extra_mask_weight_for_gen = extra_mask_weight_for_gen

    def generator_loss(self, real_batch: torch.Tensor, fake_batch: torch.Tensor, discr_real_pred: torch.Tensor, discr_fake_pred: torch.Tensor, mask=None) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        fake_loss = F.softplus(-discr_fake_pred)
        if self.mask_as_fake_target and self.extra_mask_weight_for_gen > 0 or not self.use_unmasked_for_gen:
            mask = self.interpolate_mask(mask, discr_fake_pred.shape[-2:])
            if not self.use_unmasked_for_gen:
                fake_loss = fake_loss * mask
            else:
                pixel_weights = 1 + mask * self.extra_mask_weight_for_gen
                fake_loss = fake_loss * pixel_weights
        return (fake_loss.mean() * self.weight, dict())

    def pre_discriminator_step(self, real_batch: torch.Tensor, fake_batch: torch.Tensor, generator: nn.Module, discriminator: nn.Module):
        real_batch.requires_grad = True

    def discriminator_loss(self, real_batch: torch.Tensor, fake_batch: torch.Tensor, discr_real_pred: torch.Tensor, discr_fake_pred: torch.Tensor, mask=None) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        real_loss = F.softplus(-discr_real_pred)
        grad_penalty = make_r1_gp(discr_real_pred, real_batch) * self.gp_coef
        fake_loss = F.softplus(discr_fake_pred)
        if not self.use_unmasked_for_discr or self.mask_as_fake_target:
            mask = self.interpolate_mask(mask, discr_fake_pred.shape[-2:])
            fake_loss = fake_loss * mask
            if self.mask_as_fake_target:
                fake_loss = fake_loss + (1 - mask) * F.softplus(-discr_fake_pred)
        sum_discr_loss = real_loss + grad_penalty + fake_loss
        metrics = dict(discr_real_out=discr_real_pred.mean(), discr_fake_out=discr_fake_pred.mean(), discr_real_gp=grad_penalty)
        return (sum_discr_loss.mean(), metrics)

def generator_loss(self, real_batch: torch.Tensor, fake_batch: torch.Tensor, discr_real_pred: torch.Tensor, discr_fake_pred: torch.Tensor, mask=None) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
    fake_loss = F.softplus(-discr_fake_pred)
    if self.mask_as_fake_target and self.extra_mask_weight_for_gen > 0 or not self.use_unmasked_for_gen:
        mask = self.interpolate_mask(mask, discr_fake_pred.shape[-2:])
        if not self.use_unmasked_for_gen:
            fake_loss = fake_loss * mask
        else:
            pixel_weights = 1 + mask * self.extra_mask_weight_for_gen
            fake_loss = fake_loss * pixel_weights
    return (fake_loss.mean() * self.weight, dict())

def discriminator_loss(self, real_batch: torch.Tensor, fake_batch: torch.Tensor, discr_real_pred: torch.Tensor, discr_fake_pred: torch.Tensor, mask=None) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
    real_loss = F.softplus(-discr_real_pred)
    grad_penalty = make_r1_gp(discr_real_pred, real_batch) * self.gp_coef
    fake_loss = F.softplus(discr_fake_pred)
    if not self.use_unmasked_for_discr or self.mask_as_fake_target:
        mask = self.interpolate_mask(mask, discr_fake_pred.shape[-2:])
        fake_loss = fake_loss * mask
        if self.mask_as_fake_target:
            fake_loss = fake_loss + (1 - mask) * F.softplus(-discr_fake_pred)
    sum_discr_loss = real_loss + grad_penalty + fake_loss
    metrics = dict(discr_real_out=discr_real_pred.mean(), discr_fake_out=discr_fake_pred.mean(), discr_real_gp=grad_penalty)
    return (sum_discr_loss.mean(), metrics)

class BCELoss(BaseAdversarialLoss):

    def __init__(self, weight):
        self.weight = weight
        self.bce_loss = nn.BCEWithLogitsLoss()

    def generator_loss(self, discr_fake_pred: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        real_mask_gt = torch.zeros(discr_fake_pred.shape).to(discr_fake_pred.device)
        fake_loss = self.bce_loss(discr_fake_pred, real_mask_gt) * self.weight
        return (fake_loss, dict())

    def pre_discriminator_step(self, real_batch: torch.Tensor, fake_batch: torch.Tensor, generator: nn.Module, discriminator: nn.Module):
        real_batch.requires_grad = True

    def discriminator_loss(self, mask: torch.Tensor, discr_real_pred: torch.Tensor, discr_fake_pred: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        real_mask_gt = torch.zeros(discr_real_pred.shape).to(discr_real_pred.device)
        sum_discr_loss = (self.bce_loss(discr_real_pred, real_mask_gt) + self.bce_loss(discr_fake_pred, mask)) / 2
        metrics = dict(discr_real_out=discr_real_pred.mean(), discr_fake_out=discr_fake_pred.mean(), discr_real_gp=0)
        return (sum_discr_loss, metrics)

def generator_loss(self, discr_fake_pred: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
    real_mask_gt = torch.zeros(discr_fake_pred.shape).to(discr_fake_pred.device)
    fake_loss = self.bce_loss(discr_fake_pred, real_mask_gt) * self.weight
    return (fake_loss, dict())

def discriminator_loss(self, mask: torch.Tensor, discr_real_pred: torch.Tensor, discr_fake_pred: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
    real_mask_gt = torch.zeros(discr_real_pred.shape).to(discr_real_pred.device)
    sum_discr_loss = (self.bce_loss(discr_real_pred, real_mask_gt) + self.bce_loss(discr_fake_pred, mask)) / 2
    metrics = dict(discr_real_out=discr_real_pred.mean(), discr_fake_out=discr_fake_pred.mean(), discr_real_gp=0)
    return (sum_discr_loss, metrics)

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

def forward(self, real_img, pred_img, mask):
    with torch.no_grad():
        known_mask = 1 - mask
        dilated_known_mask = (self.dilate_filter(known_mask) > 1).float()
        result = self.blur_filter(1 - dilated_known_mask) * mask
        return result

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

def do_normalize_inputs(self, x):
    return (x - self.mean_.to(x.device)) / self.std_.to(x.device)

def update_running_average(result: nn.Module, new_iterate_model: nn.Module, decay=0.999):
    with torch.no_grad():
        res_params = dict(result.named_parameters())
        new_params = dict(new_iterate_model.named_parameters())
        for k in res_params.keys():
            res_params[k].data.mul_(decay).add_(new_params[k].data, alpha=1 - decay)

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

def configure_optimizers(self):
    discriminator_params = list(self.discriminator.parameters())
    return [dict(optimizer=make_optimizer(self.generator.parameters(), **self.config.optimizers.generator)), dict(optimizer=make_optimizer(discriminator_params, **self.config.optimizers.discriminator))]

def train_dataloader(self):
    kwargs = dict(self.config.data.train)
    if self.use_ddp:
        kwargs['ddp_kwargs'] = dict(num_replicas=self.trainer.num_nodes * self.trainer.num_processes, rank=self.trainer.global_rank, shuffle=True)
    dataloader = make_default_train_dataloader(**self.config.data.train)
    return dataloader

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

def __getitem__(self, i):
    result = dict(image=load_image(self.img_filenames[i], mode='RGB'), mask=load_image(self.mask_filenames[i], mode='L')[None, ...])
    if self.scale_factor is not None:
        result['image'] = scale_image(result['image'], self.scale_factor)
        result['mask'] = scale_image(result['mask'], self.scale_factor)
    if self.pad_out_to_modulo is not None and self.pad_out_to_modulo > 1:
        result['image'] = pad_img_to_modulo(result['image'], self.pad_out_to_modulo)
        result['mask'] = pad_img_to_modulo(result['mask'], self.pad_out_to_modulo)
    return result

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

def __getitem__(self, i):
    result = super().__getitem__(i)
    result['inpainted'] = load_image(self.pred_filenames[i])
    if self.pad_out_to_modulo is not None and self.pad_out_to_modulo > 1:
        result['inpainted'] = pad_img_to_modulo(result['inpainted'], self.pad_out_to_modulo)
    return result

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

def __getitem__(self, i):
    result = super().__getitem__(i)
    result['inpainted'] = self.file_loader(self.pred_filenames[i])
    if self.pad_out_to_modulo is not None and self.pad_out_to_modulo > 1:
        result['inpainted'] = pad_img_to_modulo(result['inpainted'], self.pad_out_to_modulo)
    return result

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

class InpaintingEvaluator:

    def __init__(self, dataset, scores, area_grouping=True, bins=10, batch_size=32, device='cuda', integral_func=None, integral_title=None, clamp_image_range=None):
        """
        :param dataset: torch.utils.data.Dataset which contains images and masks
        :param scores: dict {score_name: EvaluatorScore object}
        :param area_grouping: in addition to the overall scores, allows to compute score for the groups of samples
            which are defined by share of area occluded by mask
        :param bins: number of groups, partition is generated by np.linspace(0., 1., bins + 1)
        :param batch_size: batch_size for the dataloader
        :param device: device to use
        """
        self.scores = scores
        self.dataset = dataset
        self.area_grouping = area_grouping
        self.bins = bins
        self.device = torch.device(device)
        self.dataloader = DataLoader(self.dataset, shuffle=False, batch_size=batch_size)
        self.integral_func = integral_func
        self.integral_title = integral_title
        self.clamp_image_range = clamp_image_range

    def _get_bin_edges(self):
        bin_edges = np.linspace(0, 1, self.bins + 1)
        num_digits = max(0, math.ceil(math.log10(self.bins)) - 1)
        interval_names = []
        for idx_bin in range(self.bins):
            start_percent, end_percent = (round(100 * bin_edges[idx_bin], num_digits), round(100 * bin_edges[idx_bin + 1], num_digits))
            start_percent = '{:.{n}f}'.format(start_percent, n=num_digits)
            end_percent = '{:.{n}f}'.format(end_percent, n=num_digits)
            interval_names.append('{0}-{1}%'.format(start_percent, end_percent))
        groups = []
        for batch in self.dataloader:
            mask = batch['mask']
            batch_size = mask.shape[0]
            area = mask.to(self.device).reshape(batch_size, -1).mean(dim=-1)
            bin_indices = np.searchsorted(bin_edges, area.detach().cpu().numpy(), side='right') - 1
            bin_indices[bin_indices == self.bins] = self.bins - 1
            groups.append(bin_indices)
        groups = np.hstack(groups)
        return (groups, interval_names)

    def evaluate(self, model=None):
        """
        :param model: callable with signature (image_batch, mask_batch); should return inpainted_batch
        :return: dict with (score_name, group_type) as keys, where group_type can be either 'overall' or
            name of the particular group arranged by area of mask (e.g. '10-20%')
            and score statistics for the group as values.
        """
        results = dict()
        if self.area_grouping:
            groups, interval_names = self._get_bin_edges()
        else:
            groups = None
        for score_name, score in tqdm.auto.tqdm(self.scores.items(), desc='scores'):
            score.to(self.device)
            with torch.no_grad():
                score.reset()
                for batch in tqdm.auto.tqdm(self.dataloader, desc=score_name, leave=False):
                    batch = move_to_device(batch, self.device)
                    image_batch, mask_batch = (batch['image'], batch['mask'])
                    if self.clamp_image_range is not None:
                        image_batch = torch.clamp(image_batch, min=self.clamp_image_range[0], max=self.clamp_image_range[1])
                    if model is None:
                        assert 'inpainted' in batch, 'Model is None, so we expected precomputed inpainting results at key "inpainted"'
                        inpainted_batch = batch['inpainted']
                    else:
                        inpainted_batch = model(image_batch, mask_batch)
                    score(inpainted_batch, image_batch, mask_batch)
                total_results, group_results = score.get_value(groups=groups)
            results[score_name, 'total'] = total_results
            if groups is not None:
                for group_index, group_values in group_results.items():
                    group_name = interval_names[group_index]
                    results[score_name, group_name] = group_values
        if self.integral_func is not None:
            results[self.integral_title, 'total'] = dict(mean=self.integral_func(results))
        return results

def evaluate(self, model=None):
    """
        :param model: callable with signature (image_batch, mask_batch); should return inpainted_batch
        :return: dict with (score_name, group_type) as keys, where group_type can be either 'overall' or
            name of the particular group arranged by area of mask (e.g. '10-20%')
            and score statistics for the group as values.
        """
    results = dict()
    if self.area_grouping:
        groups, interval_names = self._get_bin_edges()
    else:
        groups = None
    for score_name, score in tqdm.auto.tqdm(self.scores.items(), desc='scores'):
        score.to(self.device)
        with torch.no_grad():
            score.reset()
            for batch in tqdm.auto.tqdm(self.dataloader, desc=score_name, leave=False):
                batch = move_to_device(batch, self.device)
                image_batch, mask_batch = (batch['image'], batch['mask'])
                if self.clamp_image_range is not None:
                    image_batch = torch.clamp(image_batch, min=self.clamp_image_range[0], max=self.clamp_image_range[1])
                if model is None:
                    assert 'inpainted' in batch, 'Model is None, so we expected precomputed inpainting results at key "inpainted"'
                    inpainted_batch = batch['inpainted']
                else:
                    inpainted_batch = model(image_batch, mask_batch)
                score(inpainted_batch, image_batch, mask_batch)
            total_results, group_results = score.get_value(groups=groups)
        results[score_name, 'total'] = total_results
        if groups is not None:
            for group_index, group_values in group_results.items():
                group_name = interval_names[group_index]
                results[score_name, group_name] = group_values
    if self.integral_func is not None:
        results[self.integral_title, 'total'] = dict(mean=self.integral_func(results))
    return results

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

class ObjectMask:

    def __init__(self, mask):
        self.height, self.width = mask.shape
        (self.up, self.down), (self.left, self.right) = self._get_limits(mask)
        self.mask = mask[self.up:self.down, self.left:self.right].copy()

    @staticmethod
    def _get_limits(mask):

        def indicator_limits(indicator):
            lower = indicator.argmax()
            upper = len(indicator) - indicator[::-1].argmax()
            return (lower, upper)
        vertical_indicator = mask.any(axis=1)
        vertical_limits = indicator_limits(vertical_indicator)
        horizontal_indicator = mask.any(axis=0)
        horizontal_limits = indicator_limits(horizontal_indicator)
        return (vertical_limits, horizontal_limits)

    def _clean(self):
        self.up, self.down, self.left, self.right = (0, 0, 0, 0)
        self.mask = np.empty((0, 0))

    def horizontal_flip(self, inplace=False):
        if not inplace:
            flipped = deepcopy(self)
            return flipped.horizontal_flip(inplace=True)
        self.mask = self.mask[:, ::-1]
        return self

    def vertical_flip(self, inplace=False):
        if not inplace:
            flipped = deepcopy(self)
            return flipped.vertical_flip(inplace=True)
        self.mask = self.mask[::-1, :]
        return self

    def image_center(self):
        y_center = self.up + (self.down - self.up) / 2
        x_center = self.left + (self.right - self.left) / 2
        return (y_center, x_center)

    def rescale(self, scaling_factor, inplace=False):
        if not inplace:
            scaled = deepcopy(self)
            return scaled.rescale(scaling_factor, inplace=True)
        scaled_mask = rescale(self.mask.astype(float), scaling_factor, order=0) > 0.5
        (up, down), (left, right) = self._get_limits(scaled_mask)
        self.mask = scaled_mask[up:down, left:right]
        y_center, x_center = self.image_center()
        mask_height, mask_width = self.mask.shape
        self.up = int(round(y_center - mask_height / 2))
        self.down = self.up + mask_height
        self.left = int(round(x_center - mask_width / 2))
        self.right = self.left + mask_width
        return self

    def crop_to_canvas(self, vertical=True, horizontal=True, inplace=False):
        if not inplace:
            cropped = deepcopy(self)
            cropped.crop_to_canvas(vertical=vertical, horizontal=horizontal, inplace=True)
            return cropped
        if vertical:
            if self.up >= self.height or self.down <= 0:
                self._clean()
            else:
                cut_up, cut_down = (max(-self.up, 0), max(self.down - self.height, 0))
                if cut_up != 0:
                    self.mask = self.mask[cut_up:]
                    self.up = 0
                if cut_down != 0:
                    self.mask = self.mask[:-cut_down]
                    self.down = self.height
        if horizontal:
            if self.left >= self.width or self.right <= 0:
                self._clean()
            else:
                cut_left, cut_right = (max(-self.left, 0), max(self.right - self.width, 0))
                if cut_left != 0:
                    self.mask = self.mask[:, cut_left:]
                    self.left = 0
                if cut_right != 0:
                    self.mask = self.mask[:, :-cut_right]
                    self.right = self.width
        return self

    def restore_full_mask(self, allow_crop=False):
        cropped = self.crop_to_canvas(inplace=allow_crop)
        mask = np.zeros((cropped.height, cropped.width), dtype=bool)
        mask[cropped.up:cropped.down, cropped.left:cropped.right] = cropped.mask
        return mask

    def shift(self, vertical=0, horizontal=0, inplace=False):
        if not inplace:
            shifted = deepcopy(self)
            return shifted.shift(vertical=vertical, horizontal=horizontal, inplace=True)
        self.up += vertical
        self.down += vertical
        self.left += horizontal
        self.right += horizontal
        return self

    def area(self):
        return self.mask.sum()

def indicator_limits(indicator):
    lower = indicator.argmax()
    upper = len(indicator) - indicator[::-1].argmax()
    return (lower, upper)

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

def multi_mask_from_multiclass(self, pred, classes):

    def isin(ar1, ar2):
        return (ar1[..., None] == ar2).any(-1).float()
    return isin(pred, torch.LongTensor(classes).to(self.device))

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

class NonSaturatingWithR1(BaseAdversarialLoss):

    def __init__(self, gp_coef=5, weight=1, mask_as_fake_target=False, allow_scale_mask=False, mask_scale_mode='nearest', extra_mask_weight_for_gen=0, use_unmasked_for_gen=True, use_unmasked_for_discr=True):
        self.gp_coef = gp_coef
        self.weight = weight
        assert use_unmasked_for_gen or not use_unmasked_for_discr
        assert use_unmasked_for_discr or not mask_as_fake_target
        self.use_unmasked_for_gen = use_unmasked_for_gen
        self.use_unmasked_for_discr = use_unmasked_for_discr
        self.mask_as_fake_target = mask_as_fake_target
        self.allow_scale_mask = allow_scale_mask
        self.mask_scale_mode = mask_scale_mode
        self.extra_mask_weight_for_gen = extra_mask_weight_for_gen

    def generator_loss(self, real_batch: torch.Tensor, fake_batch: torch.Tensor, discr_real_pred: torch.Tensor, discr_fake_pred: torch.Tensor, mask=None) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        fake_loss = F.softplus(-discr_fake_pred)
        if self.mask_as_fake_target and self.extra_mask_weight_for_gen > 0 or not self.use_unmasked_for_gen:
            mask = self.interpolate_mask(mask, discr_fake_pred.shape[-2:])
            if not self.use_unmasked_for_gen:
                fake_loss = fake_loss * mask
            else:
                pixel_weights = 1 + mask * self.extra_mask_weight_for_gen
                fake_loss = fake_loss * pixel_weights
        return (fake_loss.mean() * self.weight, dict())

    def pre_discriminator_step(self, real_batch: torch.Tensor, fake_batch: torch.Tensor, generator: nn.Module, discriminator: nn.Module):
        real_batch.requires_grad = True

    def discriminator_loss(self, real_batch: torch.Tensor, fake_batch: torch.Tensor, discr_real_pred: torch.Tensor, discr_fake_pred: torch.Tensor, mask=None) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        real_loss = F.softplus(-discr_real_pred)
        grad_penalty = make_r1_gp(discr_real_pred, real_batch) * self.gp_coef
        fake_loss = F.softplus(discr_fake_pred)
        if not self.use_unmasked_for_discr or self.mask_as_fake_target:
            mask = self.interpolate_mask(mask, discr_fake_pred.shape[-2:])
            fake_loss = fake_loss * mask
            if self.mask_as_fake_target:
                fake_loss = fake_loss + (1 - mask) * F.softplus(-discr_fake_pred)
        sum_discr_loss = real_loss + grad_penalty + fake_loss
        metrics = dict(discr_real_out=discr_real_pred.mean(), discr_fake_out=discr_fake_pred.mean(), discr_real_gp=grad_penalty)
        return (sum_discr_loss.mean(), metrics)

def generator_loss(self, real_batch: torch.Tensor, fake_batch: torch.Tensor, discr_real_pred: torch.Tensor, discr_fake_pred: torch.Tensor, mask=None) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
    fake_loss = F.softplus(-discr_fake_pred)
    if self.mask_as_fake_target and self.extra_mask_weight_for_gen > 0 or not self.use_unmasked_for_gen:
        mask = self.interpolate_mask(mask, discr_fake_pred.shape[-2:])
        if not self.use_unmasked_for_gen:
            fake_loss = fake_loss * mask
        else:
            pixel_weights = 1 + mask * self.extra_mask_weight_for_gen
            fake_loss = fake_loss * pixel_weights
    return (fake_loss.mean() * self.weight, dict())

def discriminator_loss(self, real_batch: torch.Tensor, fake_batch: torch.Tensor, discr_real_pred: torch.Tensor, discr_fake_pred: torch.Tensor, mask=None) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
    real_loss = F.softplus(-discr_real_pred)
    grad_penalty = make_r1_gp(discr_real_pred, real_batch) * self.gp_coef
    fake_loss = F.softplus(discr_fake_pred)
    if not self.use_unmasked_for_discr or self.mask_as_fake_target:
        mask = self.interpolate_mask(mask, discr_fake_pred.shape[-2:])
        fake_loss = fake_loss * mask
        if self.mask_as_fake_target:
            fake_loss = fake_loss + (1 - mask) * F.softplus(-discr_fake_pred)
    sum_discr_loss = real_loss + grad_penalty + fake_loss
    metrics = dict(discr_real_out=discr_real_pred.mean(), discr_fake_out=discr_fake_pred.mean(), discr_real_gp=grad_penalty)
    return (sum_discr_loss.mean(), metrics)

class BCELoss(BaseAdversarialLoss):

    def __init__(self, weight):
        self.weight = weight
        self.bce_loss = nn.BCEWithLogitsLoss()

    def generator_loss(self, discr_fake_pred: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        real_mask_gt = torch.zeros(discr_fake_pred.shape).to(discr_fake_pred.device)
        fake_loss = self.bce_loss(discr_fake_pred, real_mask_gt) * self.weight
        return (fake_loss, dict())

    def pre_discriminator_step(self, real_batch: torch.Tensor, fake_batch: torch.Tensor, generator: nn.Module, discriminator: nn.Module):
        real_batch.requires_grad = True

    def discriminator_loss(self, mask: torch.Tensor, discr_real_pred: torch.Tensor, discr_fake_pred: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        real_mask_gt = torch.zeros(discr_real_pred.shape).to(discr_real_pred.device)
        sum_discr_loss = (self.bce_loss(discr_real_pred, real_mask_gt) + self.bce_loss(discr_fake_pred, mask)) / 2
        metrics = dict(discr_real_out=discr_real_pred.mean(), discr_fake_out=discr_fake_pred.mean(), discr_real_gp=0)
        return (sum_discr_loss, metrics)

def generator_loss(self, discr_fake_pred: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
    real_mask_gt = torch.zeros(discr_fake_pred.shape).to(discr_fake_pred.device)
    fake_loss = self.bce_loss(discr_fake_pred, real_mask_gt) * self.weight
    return (fake_loss, dict())

def discriminator_loss(self, mask: torch.Tensor, discr_real_pred: torch.Tensor, discr_fake_pred: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
    real_mask_gt = torch.zeros(discr_real_pred.shape).to(discr_real_pred.device)
    sum_discr_loss = (self.bce_loss(discr_real_pred, real_mask_gt) + self.bce_loss(discr_fake_pred, mask)) / 2
    metrics = dict(discr_real_out=discr_real_pred.mean(), discr_fake_out=discr_fake_pred.mean(), discr_real_gp=0)
    return (sum_discr_loss, metrics)

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

def forward(self, real_img, pred_img, mask):
    with torch.no_grad():
        known_mask = 1 - mask
        dilated_known_mask = (self.dilate_filter(known_mask) > 1).float()
        result = self.blur_filter(1 - dilated_known_mask) * mask
        return result

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

def do_normalize_inputs(self, x):
    return (x - self.mean_.to(x.device)) / self.std_.to(x.device)

class DumbAreaMaskGenerator:
    min_ratio = 0.1
    max_ratio = 0.35
    default_ratio = 0.225

    def __init__(self, is_training):
        self.is_training = is_training

    def _random_vector(self, dimension):
        if self.is_training:
            lower_limit = math.sqrt(self.min_ratio)
            upper_limit = math.sqrt(self.max_ratio)
            mask_side = round((random.random() * (upper_limit - lower_limit) + lower_limit) * dimension)
            u = random.randint(0, dimension - mask_side - 1)
            v = u + mask_side
        else:
            margin = math.sqrt(self.default_ratio) / 2 * dimension
            u = round(dimension / 2 - margin)
            v = round(dimension / 2 + margin)
        return (u, v)

    def __call__(self, img, iter_i=None, raw_image=None):
        c, height, width = img.shape
        mask = np.zeros((height, width), np.float32)
        x1, x2 = self._random_vector(width)
        y1, y2 = self._random_vector(height)
        mask[x1:x2, y1:y2] = 1
        return mask[None, ...]

def __call__(self, img, iter_i=None, raw_image=None):
    c, height, width = img.shape
    mask = np.zeros((height, width), np.float32)
    x1, x2 = self._random_vector(width)
    y1, y2 = self._random_vector(height)
    mask[x1:x2, y1:y2] = 1
    return mask[None, ...]

def update_running_average(result: nn.Module, new_iterate_model: nn.Module, decay=0.999):
    with torch.no_grad():
        res_params = dict(result.named_parameters())
        new_params = dict(new_iterate_model.named_parameters())
        for k in res_params.keys():
            res_params[k].data.mul_(decay).add_(new_params[k].data, alpha=1 - decay)

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

def configure_optimizers(self):
    discriminator_params = list(self.discriminator.parameters())
    return [dict(optimizer=make_optimizer(self.generator.parameters(), **self.config.optimizers.generator)), dict(optimizer=make_optimizer(discriminator_params, **self.config.optimizers.discriminator))]

def train_dataloader(self):
    kwargs = dict(self.config.data.train)
    if self.use_ddp:
        kwargs['ddp_kwargs'] = dict(num_replicas=self.trainer.num_nodes * self.trainer.num_processes, rank=self.trainer.global_rank, shuffle=True)
    dataloader = make_default_train_dataloader(**self.config.data.train)
    return dataloader

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

def __getitem__(self, i):
    result = dict(image=load_image(self.img_filenames[i], mode='RGB'), mask=load_image(self.mask_filenames[i], mode='L')[None, ...])
    if self.scale_factor is not None:
        result['image'] = scale_image(result['image'], self.scale_factor)
        result['mask'] = scale_image(result['mask'], self.scale_factor)
    if self.pad_out_to_modulo is not None and self.pad_out_to_modulo > 1:
        result['image'] = pad_img_to_modulo(result['image'], self.pad_out_to_modulo)
        result['mask'] = pad_img_to_modulo(result['mask'], self.pad_out_to_modulo)
    return result

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

def __getitem__(self, i):
    result = super().__getitem__(i)
    result['inpainted'] = load_image(self.pred_filenames[i])
    if self.pad_out_to_modulo is not None and self.pad_out_to_modulo > 1:
        result['inpainted'] = pad_img_to_modulo(result['inpainted'], self.pad_out_to_modulo)
    return result

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

def __getitem__(self, i):
    result = super().__getitem__(i)
    result['inpainted'] = self.file_loader(self.pred_filenames[i])
    if self.pad_out_to_modulo is not None and self.pad_out_to_modulo > 1:
        result['inpainted'] = pad_img_to_modulo(result['inpainted'], self.pad_out_to_modulo)
    return result

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

class InpaintingEvaluator:

    def __init__(self, dataset, scores, area_grouping=True, bins=10, batch_size=32, device='cuda', integral_func=None, integral_title=None, clamp_image_range=None):
        """
        :param dataset: torch.utils.data.Dataset which contains images and masks
        :param scores: dict {score_name: EvaluatorScore object}
        :param area_grouping: in addition to the overall scores, allows to compute score for the groups of samples
            which are defined by share of area occluded by mask
        :param bins: number of groups, partition is generated by np.linspace(0., 1., bins + 1)
        :param batch_size: batch_size for the dataloader
        :param device: device to use
        """
        self.scores = scores
        self.dataset = dataset
        self.area_grouping = area_grouping
        self.bins = bins
        self.device = torch.device(device)
        self.dataloader = DataLoader(self.dataset, shuffle=False, batch_size=batch_size)
        self.integral_func = integral_func
        self.integral_title = integral_title
        self.clamp_image_range = clamp_image_range

    def _get_bin_edges(self):
        bin_edges = np.linspace(0, 1, self.bins + 1)
        num_digits = max(0, math.ceil(math.log10(self.bins)) - 1)
        interval_names = []
        for idx_bin in range(self.bins):
            start_percent, end_percent = (round(100 * bin_edges[idx_bin], num_digits), round(100 * bin_edges[idx_bin + 1], num_digits))
            start_percent = '{:.{n}f}'.format(start_percent, n=num_digits)
            end_percent = '{:.{n}f}'.format(end_percent, n=num_digits)
            interval_names.append('{0}-{1}%'.format(start_percent, end_percent))
        groups = []
        for batch in self.dataloader:
            mask = batch['mask']
            batch_size = mask.shape[0]
            area = mask.to(self.device).reshape(batch_size, -1).mean(dim=-1)
            bin_indices = np.searchsorted(bin_edges, area.detach().cpu().numpy(), side='right') - 1
            bin_indices[bin_indices == self.bins] = self.bins - 1
            groups.append(bin_indices)
        groups = np.hstack(groups)
        return (groups, interval_names)

    def evaluate(self, model=None):
        """
        :param model: callable with signature (image_batch, mask_batch); should return inpainted_batch
        :return: dict with (score_name, group_type) as keys, where group_type can be either 'overall' or
            name of the particular group arranged by area of mask (e.g. '10-20%')
            and score statistics for the group as values.
        """
        results = dict()
        if self.area_grouping:
            groups, interval_names = self._get_bin_edges()
        else:
            groups = None
        for score_name, score in tqdm.auto.tqdm(self.scores.items(), desc='scores'):
            score.to(self.device)
            with torch.no_grad():
                score.reset()
                for batch in tqdm.auto.tqdm(self.dataloader, desc=score_name, leave=False):
                    batch = move_to_device(batch, self.device)
                    image_batch, mask_batch = (batch['image'], batch['mask'])
                    if self.clamp_image_range is not None:
                        image_batch = torch.clamp(image_batch, min=self.clamp_image_range[0], max=self.clamp_image_range[1])
                    if model is None:
                        assert 'inpainted' in batch, 'Model is None, so we expected precomputed inpainting results at key "inpainted"'
                        inpainted_batch = batch['inpainted']
                    else:
                        inpainted_batch = model(image_batch, mask_batch)
                    score(inpainted_batch, image_batch, mask_batch)
                total_results, group_results = score.get_value(groups=groups)
            results[score_name, 'total'] = total_results
            if groups is not None:
                for group_index, group_values in group_results.items():
                    group_name = interval_names[group_index]
                    results[score_name, group_name] = group_values
        if self.integral_func is not None:
            results[self.integral_title, 'total'] = dict(mean=self.integral_func(results))
        return results

def evaluate(self, model=None):
    """
        :param model: callable with signature (image_batch, mask_batch); should return inpainted_batch
        :return: dict with (score_name, group_type) as keys, where group_type can be either 'overall' or
            name of the particular group arranged by area of mask (e.g. '10-20%')
            and score statistics for the group as values.
        """
    results = dict()
    if self.area_grouping:
        groups, interval_names = self._get_bin_edges()
    else:
        groups = None
    for score_name, score in tqdm.auto.tqdm(self.scores.items(), desc='scores'):
        score.to(self.device)
        with torch.no_grad():
            score.reset()
            for batch in tqdm.auto.tqdm(self.dataloader, desc=score_name, leave=False):
                batch = move_to_device(batch, self.device)
                image_batch, mask_batch = (batch['image'], batch['mask'])
                if self.clamp_image_range is not None:
                    image_batch = torch.clamp(image_batch, min=self.clamp_image_range[0], max=self.clamp_image_range[1])
                if model is None:
                    assert 'inpainted' in batch, 'Model is None, so we expected precomputed inpainting results at key "inpainted"'
                    inpainted_batch = batch['inpainted']
                else:
                    inpainted_batch = model(image_batch, mask_batch)
                score(inpainted_batch, image_batch, mask_batch)
            total_results, group_results = score.get_value(groups=groups)
        results[score_name, 'total'] = total_results
        if groups is not None:
            for group_index, group_values in group_results.items():
                group_name = interval_names[group_index]
                results[score_name, group_name] = group_values
    if self.integral_func is not None:
        results[self.integral_title, 'total'] = dict(mean=self.integral_func(results))
    return results

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

class ObjectMask:

    def __init__(self, mask):
        self.height, self.width = mask.shape
        (self.up, self.down), (self.left, self.right) = self._get_limits(mask)
        self.mask = mask[self.up:self.down, self.left:self.right].copy()

    @staticmethod
    def _get_limits(mask):

        def indicator_limits(indicator):
            lower = indicator.argmax()
            upper = len(indicator) - indicator[::-1].argmax()
            return (lower, upper)
        vertical_indicator = mask.any(axis=1)
        vertical_limits = indicator_limits(vertical_indicator)
        horizontal_indicator = mask.any(axis=0)
        horizontal_limits = indicator_limits(horizontal_indicator)
        return (vertical_limits, horizontal_limits)

    def _clean(self):
        self.up, self.down, self.left, self.right = (0, 0, 0, 0)
        self.mask = np.empty((0, 0))

    def horizontal_flip(self, inplace=False):
        if not inplace:
            flipped = deepcopy(self)
            return flipped.horizontal_flip(inplace=True)
        self.mask = self.mask[:, ::-1]
        return self

    def vertical_flip(self, inplace=False):
        if not inplace:
            flipped = deepcopy(self)
            return flipped.vertical_flip(inplace=True)
        self.mask = self.mask[::-1, :]
        return self

    def image_center(self):
        y_center = self.up + (self.down - self.up) / 2
        x_center = self.left + (self.right - self.left) / 2
        return (y_center, x_center)

    def rescale(self, scaling_factor, inplace=False):
        if not inplace:
            scaled = deepcopy(self)
            return scaled.rescale(scaling_factor, inplace=True)
        scaled_mask = rescale(self.mask.astype(float), scaling_factor, order=0) > 0.5
        (up, down), (left, right) = self._get_limits(scaled_mask)
        self.mask = scaled_mask[up:down, left:right]
        y_center, x_center = self.image_center()
        mask_height, mask_width = self.mask.shape
        self.up = int(round(y_center - mask_height / 2))
        self.down = self.up + mask_height
        self.left = int(round(x_center - mask_width / 2))
        self.right = self.left + mask_width
        return self

    def crop_to_canvas(self, vertical=True, horizontal=True, inplace=False):
        if not inplace:
            cropped = deepcopy(self)
            cropped.crop_to_canvas(vertical=vertical, horizontal=horizontal, inplace=True)
            return cropped
        if vertical:
            if self.up >= self.height or self.down <= 0:
                self._clean()
            else:
                cut_up, cut_down = (max(-self.up, 0), max(self.down - self.height, 0))
                if cut_up != 0:
                    self.mask = self.mask[cut_up:]
                    self.up = 0
                if cut_down != 0:
                    self.mask = self.mask[:-cut_down]
                    self.down = self.height
        if horizontal:
            if self.left >= self.width or self.right <= 0:
                self._clean()
            else:
                cut_left, cut_right = (max(-self.left, 0), max(self.right - self.width, 0))
                if cut_left != 0:
                    self.mask = self.mask[:, cut_left:]
                    self.left = 0
                if cut_right != 0:
                    self.mask = self.mask[:, :-cut_right]
                    self.right = self.width
        return self

    def restore_full_mask(self, allow_crop=False):
        cropped = self.crop_to_canvas(inplace=allow_crop)
        mask = np.zeros((cropped.height, cropped.width), dtype=bool)
        mask[cropped.up:cropped.down, cropped.left:cropped.right] = cropped.mask
        return mask

    def shift(self, vertical=0, horizontal=0, inplace=False):
        if not inplace:
            shifted = deepcopy(self)
            return shifted.shift(vertical=vertical, horizontal=horizontal, inplace=True)
        self.up += vertical
        self.down += vertical
        self.left += horizontal
        self.right += horizontal
        return self

    def area(self):
        return self.mask.sum()

def indicator_limits(indicator):
    lower = indicator.argmax()
    upper = len(indicator) - indicator[::-1].argmax()
    return (lower, upper)

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

def multi_mask_from_multiclass(self, pred, classes):

    def isin(ar1, ar2):
        return (ar1[..., None] == ar2).any(-1).float()
    return isin(pred, torch.LongTensor(classes).to(self.device))

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

def transform_box_to_crop(box: torch.Tensor, crop_box: torch.Tensor, crop_sz: torch.Tensor, normalize=False) -> torch.Tensor:
    """ Transform the box co-ordinates from the original image co-ordinates to the co-ordinates of the cropped image
    args:
        box - the box for which the co-ordinates are to be transformed
        crop_box - bounding box defining the crop in the original image
        crop_sz - size of the cropped image

    returns:
        torch.Tensor - transformed co-ordinates of box_in
    """
    box_out = box.clone()
    box_out[:2] -= crop_box[:2]
    scale_factor = crop_sz / crop_box[2:]
    box_out[:2] *= scale_factor
    box_out[2:] *= scale_factor
    if normalize:
        return box_out / crop_sz[0]
    else:
        return box_out

class TensorDict(OrderedDict):
    """Container mainly used for dicts of torch tensors. Extends OrderedDict with pytorch functionality."""

    def concat(self, other):
        """Concatenates two dicts without copying internal data."""
        return TensorDict(self, **other)

    def copy(self):
        return TensorDict(super(TensorDict, self).copy())

    def __deepcopy__(self, memodict={}):
        return TensorDict(copy.deepcopy(list(self), memodict))

    def __getattr__(self, name):
        if not hasattr(torch.Tensor, name):
            raise AttributeError("'TensorDict' object has not attribute '{}'".format(name))

        def apply_attr(*args, **kwargs):
            return TensorDict({n: getattr(e, name)(*args, **kwargs) if hasattr(e, name) else e for n, e in self.items()})
        return apply_attr

    def attribute(self, attr: str, *args):
        return TensorDict({n: getattr(e, attr, *args) for n, e in self.items()})

    def apply(self, fn, *args, **kwargs):
        return TensorDict({n: fn(e, *args, **kwargs) for n, e in self.items()})

    @staticmethod
    def _iterable(a):
        return isinstance(a, (TensorDict, list))

def __getattr__(self, name):
    if not hasattr(torch.Tensor, name):
        raise AttributeError("'TensorDict' object has not attribute '{}'".format(name))

    def apply_attr(*args, **kwargs):
        return TensorDict({n: getattr(e, name)(*args, **kwargs) if hasattr(e, name) else e for n, e in self.items()})
    return apply_attr

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

def __getitem__(self, item):
    if isinstance(item, int):
        return super(TensorList, self).__getitem__(item)
    elif isinstance(item, (tuple, list)):
        return TensorList([super(TensorList, self).__getitem__(i) for i in item])
    else:
        return TensorList(super(TensorList, self).__getitem__(item))

def __getattr__(self, name):
    if not hasattr(torch.Tensor, name):
        raise AttributeError("'TensorList' object has not attribute '{}'".format(name))

    def apply_attr(*args, **kwargs):
        return TensorList([getattr(e, name)(*args, **kwargs) for e in self])
    return apply_attr

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

def __getattr__(self, attr):
    if attr in self.meters:
        return self.meters[attr]
    if attr in self.__dict__:
        return self.__dict__[attr]
    raise AttributeError("'{}' object has no attribute '{}'".format(type(self).__name__, attr))

def synchronize_between_processes(self):
    for meter in self.meters.values():
        meter.synchronize_between_processes()

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

def to(self, device):
    cast_tensor = self.tensors.to(device)
    mask = self.mask
    if mask is not None:
        assert mask is not None
        cast_mask = mask.to(device)
    else:
        cast_mask = None
    return NestedTensor(cast_tensor, cast_mask)

def nested_tensor_from_tensor_list(tensor_list: List[Tensor]):
    if tensor_list[0].ndim == 3:
        if torchvision._is_tracing():
            return _onnx_nested_tensor_from_tensor_list(tensor_list)
        max_size = _max_by_axis([list(img.shape) for img in tensor_list])
        batch_shape = [len(tensor_list)] + max_size
        b, c, h, w = batch_shape
        dtype = tensor_list[0].dtype
        device = tensor_list[0].device
        tensor = torch.zeros(batch_shape, dtype=dtype, device=device)
        mask = torch.ones((b, h, w), dtype=torch.bool, device=device)
        for img, pad_img, m in zip(tensor_list, tensor, mask):
            pad_img[:img.shape[0], :img.shape[1], :img.shape[2]].copy_(img)
            m[:img.shape[1], :img.shape[2]] = False
    else:
        raise ValueError('not supported')
    return NestedTensor(tensor, mask)

def generate_heatmap(bboxes, patch_size=320, stride=16):
    """
    Generate ground truth heatmap same as CenterNet
    Args:
        bboxes (torch.Tensor): shape of [num_search, bs, 4]

    Returns:
        gaussian_maps: list of generated heatmap

    """
    gaussian_maps = []
    heatmap_size = patch_size // stride
    for single_patch_bboxes in bboxes:
        bs = single_patch_bboxes.shape[0]
        gt_scoremap = torch.zeros(bs, heatmap_size, heatmap_size)
        classes = torch.arange(bs).to(torch.long)
        bbox = single_patch_bboxes * heatmap_size
        wh = bbox[:, 2:]
        centers_int = (bbox[:, :2] + wh / 2).round()
        CenterNetHeatMap.generate_score_map(gt_scoremap, classes, wh, centers_int, 0.7)
        gaussian_maps.append(gt_scoremap.to(bbox.device))
    return gaussian_maps

class TrackerParams:
    """Class for tracker parameters."""

    def set_default_values(self, default_vals: dict):
        for name, val in default_vals.items():
            if not hasattr(self, name):
                setattr(self, name, val)

    def get(self, name: str, *default):
        """Get a parameter value with the given name. If it does not exists, it return the default value given as a
        second argument or returns an error if no default value is given."""
        if len(default) > 1:
            raise ValueError('Can only give one default value.')
        if not default:
            return getattr(self, name)
        return getattr(self, name, default[0])

    def has(self, name: str):
        """Check if there exist a parameter with the given name."""
        return hasattr(self, name)

def has(self, name: str):
    """Check if there exist a parameter with the given name."""
    return hasattr(self, name)

@torch.no_grad()
def _load_weights(model: VisionTransformer, checkpoint_path: str, prefix: str=''):
    """ Load weights from .npz checkpoints for official Google Brain Flax implementation
    """
    import numpy as np

    def _n2p(w, t=True):
        if w.ndim == 4 and w.shape[0] == w.shape[1] == w.shape[2] == 1:
            w = w.flatten()
        if t:
            if w.ndim == 4:
                w = w.transpose([3, 2, 0, 1])
            elif w.ndim == 3:
                w = w.transpose([2, 0, 1])
            elif w.ndim == 2:
                w = w.transpose([1, 0])
        return torch.from_numpy(w)
    w = np.load(checkpoint_path)
    if not prefix and 'opt/target/embedding/kernel' in w:
        prefix = 'opt/target/'
    if hasattr(model.patch_embed, 'backbone'):
        backbone = model.patch_embed.backbone
        stem_only = not hasattr(backbone, 'stem')
        stem = backbone if stem_only else backbone.stem
        stem.conv.weight.copy_(adapt_input_conv(stem.conv.weight.shape[1], _n2p(w[f'{prefix}conv_root/kernel'])))
        stem.norm.weight.copy_(_n2p(w[f'{prefix}gn_root/scale']))
        stem.norm.bias.copy_(_n2p(w[f'{prefix}gn_root/bias']))
        if not stem_only:
            for i, stage in enumerate(backbone.stages):
                for j, block in enumerate(stage.blocks):
                    bp = f'{prefix}block{i + 1}/unit{j + 1}/'
                    for r in range(3):
                        getattr(block, f'conv{r + 1}').weight.copy_(_n2p(w[f'{bp}conv{r + 1}/kernel']))
                        getattr(block, f'norm{r + 1}').weight.copy_(_n2p(w[f'{bp}gn{r + 1}/scale']))
                        getattr(block, f'norm{r + 1}').bias.copy_(_n2p(w[f'{bp}gn{r + 1}/bias']))
                    if block.downsample is not None:
                        block.downsample.conv.weight.copy_(_n2p(w[f'{bp}conv_proj/kernel']))
                        block.downsample.norm.weight.copy_(_n2p(w[f'{bp}gn_proj/scale']))
                        block.downsample.norm.bias.copy_(_n2p(w[f'{bp}gn_proj/bias']))
        embed_conv_w = _n2p(w[f'{prefix}embedding/kernel'])
    else:
        embed_conv_w = adapt_input_conv(model.patch_embed.proj.weight.shape[1], _n2p(w[f'{prefix}embedding/kernel']))
    model.patch_embed.proj.weight.copy_(embed_conv_w)
    model.patch_embed.proj.bias.copy_(_n2p(w[f'{prefix}embedding/bias']))
    model.cls_token.copy_(_n2p(w[f'{prefix}cls'], t=False))
    pos_embed_w = _n2p(w[f'{prefix}Transformer/posembed_input/pos_embedding'], t=False)
    if pos_embed_w.shape != model.pos_embed.shape:
        pos_embed_w = resize_pos_embed(pos_embed_w, model.pos_embed, getattr(model, 'num_tokens', 1), model.patch_embed.grid_size)
    model.pos_embed.copy_(pos_embed_w)
    model.norm.weight.copy_(_n2p(w[f'{prefix}Transformer/encoder_norm/scale']))
    model.norm.bias.copy_(_n2p(w[f'{prefix}Transformer/encoder_norm/bias']))
    if isinstance(model.head, nn.Linear) and model.head.bias.shape[0] == w[f'{prefix}head/bias'].shape[-1]:
        model.head.weight.copy_(_n2p(w[f'{prefix}head/kernel']))
        model.head.bias.copy_(_n2p(w[f'{prefix}head/bias']))
    if isinstance(getattr(model.pre_logits, 'fc', None), nn.Linear) and f'{prefix}pre_logits/bias' in w:
        model.pre_logits.fc.weight.copy_(_n2p(w[f'{prefix}pre_logits/kernel']))
        model.pre_logits.fc.bias.copy_(_n2p(w[f'{prefix}pre_logits/bias']))
    for i, block in enumerate(model.blocks.children()):
        block_prefix = f'{prefix}Transformer/encoderblock_{i}/'
        mha_prefix = block_prefix + 'MultiHeadDotProductAttention_1/'
        block.norm1.weight.copy_(_n2p(w[f'{block_prefix}LayerNorm_0/scale']))
        block.norm1.bias.copy_(_n2p(w[f'{block_prefix}LayerNorm_0/bias']))
        block.attn.qkv.weight.copy_(torch.cat([_n2p(w[f'{mha_prefix}{n}/kernel'], t=False).flatten(1).T for n in ('query', 'key', 'value')]))
        block.attn.qkv.bias.copy_(torch.cat([_n2p(w[f'{mha_prefix}{n}/bias'], t=False).reshape(-1) for n in ('query', 'key', 'value')]))
        block.attn.proj.weight.copy_(_n2p(w[f'{mha_prefix}out/kernel']).flatten(1))
        block.attn.proj.bias.copy_(_n2p(w[f'{mha_prefix}out/bias']))
        for r in range(2):
            getattr(block.mlp, f'fc{r + 1}').weight.copy_(_n2p(w[f'{block_prefix}MlpBlock_3/Dense_{r}/kernel']))
            getattr(block.mlp, f'fc{r + 1}').bias.copy_(_n2p(w[f'{block_prefix}MlpBlock_3/Dense_{r}/bias']))
        block.norm2.weight.copy_(_n2p(w[f'{block_prefix}LayerNorm_2/scale']))
        block.norm2.bias.copy_(_n2p(w[f'{block_prefix}LayerNorm_2/bias']))

def vit_base_patch16_224(pretrained=False, **kwargs):
    """
    ViT-Base model (ViT-B/16) from original paper (https://arxiv.org/abs/2010.11929).
    """
    model_kwargs = dict(patch_size=16, embed_dim=768, depth=12, num_heads=12, **kwargs)
    model = _create_vision_transformer('vit_base_patch16_224_in21k', pretrained=pretrained, **model_kwargs)
    return model

def vit_base_patch16_224_ce(pretrained=False, **kwargs):
    """ ViT-Base model (ViT-B/16) from original paper (https://arxiv.org/abs/2010.11929).
    """
    model_kwargs = dict(patch_size=16, embed_dim=768, depth=12, num_heads=12, **kwargs)
    model = _create_vision_transformer(pretrained=pretrained, **model_kwargs)
    return model

def vit_large_patch16_224_ce(pretrained=False, **kwargs):
    """ ViT-Large model (ViT-L/16) from original paper (https://arxiv.org/abs/2010.11929).
    """
    model_kwargs = dict(patch_size=16, embed_dim=1024, depth=24, num_heads=16, **kwargs)
    model = _create_vision_transformer(pretrained=pretrained, **model_kwargs)
    return model

def get_data(bs, sz):
    img_patch = torch.randn(bs, 3, sz, sz)
    att_mask = torch.rand(bs, sz, sz) > 0.5
    return NestedTensor(img_patch, att_mask)

def get_cond(mode, selected_path):
    example = dict()
    if mode == 'superresolution':
        up_f = 4
        visualize_cond_img(selected_path)
        c = Image.open(selected_path)
        c = torch.unsqueeze(torchvision.transforms.ToTensor()(c), 0)
        c_up = torchvision.transforms.functional.resize(c, size=[up_f * c.shape[2], up_f * c.shape[3]], antialias=True)
        c_up = rearrange(c_up, '1 c h w -> 1 h w c')
        c = rearrange(c, '1 c h w -> 1 h w c')
        c = 2.0 * c - 1.0
        c = c.to(torch.device('cuda'))
        example['LR_image'] = c
        example['image'] = c_up
    return example

def run(model, selected_path, task, custom_steps, resize_enabled=False, classifier_ckpt=None, global_step=None):
    example = get_cond(task, selected_path)
    save_intermediate_vid = False
    n_runs = 1
    masked = False
    guider = None
    ckwargs = None
    mode = 'ddim'
    ddim_use_x0_pred = False
    temperature = 1.0
    eta = 1.0
    make_progrow = True
    custom_shape = None
    height, width = example['image'].shape[1:3]
    split_input = height >= 128 and width >= 128
    if split_input:
        ks = 128
        stride = 64
        vqf = 4
        model.split_input_params = {'ks': (ks, ks), 'stride': (stride, stride), 'vqf': vqf, 'patch_distributed_vq': True, 'tie_braker': False, 'clip_max_weight': 0.5, 'clip_min_weight': 0.01, 'clip_max_tie_weight': 0.5, 'clip_min_tie_weight': 0.01}
    elif hasattr(model, 'split_input_params'):
        delattr(model, 'split_input_params')
    invert_mask = False
    x_T = None
    for n in range(n_runs):
        if custom_shape is not None:
            x_T = torch.randn(1, custom_shape[1], custom_shape[2], custom_shape[3]).to(model.device)
            x_T = repeat(x_T, '1 c h w -> b c h w', b=custom_shape[0])
        logs = make_convolutional_sample(example, model, mode=mode, custom_steps=custom_steps, eta=eta, swap_mode=False, masked=masked, invert_mask=invert_mask, quantize_x0=False, custom_schedule=None, decode_interval=10, resize_enabled=resize_enabled, custom_shape=custom_shape, temperature=temperature, noise_dropout=0.0, corrector=guider, corrector_kwargs=ckwargs, x_T=x_T, save_intermediate_vid=save_intermediate_vid, make_progrow=make_progrow, ddim_use_x0_pred=ddim_use_x0_pred)
    return logs

@torch.no_grad()
def make_convolutional_sample(batch, model, mode='vanilla', custom_steps=None, eta=1.0, swap_mode=False, masked=False, invert_mask=True, quantize_x0=False, custom_schedule=None, decode_interval=1000, resize_enabled=False, custom_shape=None, temperature=1.0, noise_dropout=0.0, corrector=None, corrector_kwargs=None, x_T=None, save_intermediate_vid=False, make_progrow=True, ddim_use_x0_pred=False):
    log = dict()
    z, c, x, xrec, xc = model.get_input(batch, model.first_stage_key, return_first_stage_outputs=True, force_c_encode=not (hasattr(model, 'split_input_params') and model.cond_stage_key == 'coordinates_bbox'), return_original_cond=True)
    log_every_t = 1 if save_intermediate_vid else None
    if custom_shape is not None:
        z = torch.randn(custom_shape)
        print(f'Generating {custom_shape[0]} samples of shape {custom_shape[1:]}')
    z0 = None
    log['input'] = x
    log['reconstruction'] = xrec
    if ismap(xc):
        log['original_conditioning'] = model.to_rgb(xc)
        if hasattr(model, 'cond_stage_key'):
            log[model.cond_stage_key] = model.to_rgb(xc)
    else:
        log['original_conditioning'] = xc if xc is not None else torch.zeros_like(x)
        if model.cond_stage_model:
            log[model.cond_stage_key] = xc if xc is not None else torch.zeros_like(x)
            if model.cond_stage_key == 'class_label':
                log[model.cond_stage_key] = xc[model.cond_stage_key]
    with model.ema_scope('Plotting'):
        t0 = time.time()
        img_cb = None
        sample, intermediates = convsample_ddim(model, c, steps=custom_steps, shape=z.shape, eta=eta, quantize_x0=quantize_x0, img_callback=img_cb, mask=None, x0=z0, temperature=temperature, noise_dropout=noise_dropout, score_corrector=corrector, corrector_kwargs=corrector_kwargs, x_T=x_T, log_every_t=log_every_t)
        t1 = time.time()
        if ddim_use_x0_pred:
            sample = intermediates['pred_x0'][-1]
    x_sample = model.decode_first_stage(sample)
    try:
        x_sample_noquant = model.decode_first_stage(sample, force_not_quantize=True)
        log['sample_noquant'] = x_sample_noquant
        log['sample_diff'] = torch.abs(x_sample_noquant - x_sample)
    except:
        pass
    log['sample'] = x_sample
    log['time'] = t1 - t0
    return log

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

def prepare_data(self):
    for data_cfg in self.dataset_configs.values():
        instantiate_from_config(data_cfg)

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
def _testtube(self, pl_module, images, batch_idx, split):
    for k in images:
        grid = torchvision.utils.make_grid(images[k])
        grid = (grid + 1.0) / 2.0
        tag = f'{split}/{k}'
        pl_module.logger.experiment.add_image(tag, grid, global_step=pl_module.global_step)

def on_train_batch_end(self, trainer, pl_module, outputs, batch, batch_idx, dataloader_idx):
    if not self.disabled and (pl_module.global_step > 0 or self.log_first_step):
        self.log_img(pl_module, batch, batch_idx, split='train')

def on_validation_batch_end(self, trainer, pl_module, outputs, batch, batch_idx, dataloader_idx):
    if not self.disabled and pl_module.global_step > 0:
        self.log_img(pl_module, batch, batch_idx, split='val')
    if hasattr(pl_module, 'calibrate_grad_norm'):
        if (pl_module.calibrate_grad_norm and batch_idx % 25 == 0) and batch_idx > 0:
            self.log_gradients(trainer, pl_module, batch_idx=batch_idx)

@torch.no_grad()
def convsample(model, shape, return_intermediates=True, verbose=True, make_prog_row=False):
    if not make_prog_row:
        return model.p_sample_loop(None, shape, return_intermediates=return_intermediates, verbose=verbose)
    else:
        return model.progressive_denoising(None, shape, verbose=True)

@torch.no_grad()
def make_convolutional_sample(model, batch_size, vanilla=False, custom_steps=None, eta=1.0):
    log = dict()
    shape = [batch_size, model.model.diffusion_model.in_channels, model.model.diffusion_model.image_size, model.model.diffusion_model.image_size]
    with model.ema_scope('Plotting'):
        t0 = time.time()
        if vanilla:
            sample, progrow = convsample(model, shape, make_prog_row=True)
        else:
            sample, intermediates = convsample_ddim(model, steps=custom_steps, shape=shape, eta=eta)
        t1 = time.time()
    x_sample = model.decode_first_stage(sample)
    log['sample'] = x_sample
    log['time'] = t1 - t0
    log['throughput'] = sample.shape[0] / (t1 - t0)
    print(f'Throughput for this batch: {log['throughput']}')
    return log

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

class GRUGating(nn.Module):

    def __init__(self, dim):
        super().__init__()
        self.gru = nn.GRUCell(dim, dim)

    def forward(self, x, residual):
        gated_output = self.gru(rearrange(x, 'b n d -> (b n) d'), rearrange(residual, 'b n d -> (b n) d'))
        return gated_output.reshape_as(x)

def forward(self, x, residual):
    gated_output = self.gru(rearrange(x, 'b n d -> (b n) d'), rearrange(residual, 'b n d -> (b n) d'))
    return gated_output.reshape_as(x)

class DiagonalGaussianDistribution(object):

    def __init__(self, parameters, deterministic=False):
        self.parameters = parameters
        self.mean, self.logvar = torch.chunk(parameters, 2, dim=1)
        self.logvar = torch.clamp(self.logvar, -30.0, 20.0)
        self.deterministic = deterministic
        self.std = torch.exp(0.5 * self.logvar)
        self.var = torch.exp(self.logvar)
        if self.deterministic:
            self.var = self.std = torch.zeros_like(self.mean).to(device=self.parameters.device)

    def sample(self):
        x = self.mean + self.std * torch.randn(self.mean.shape).to(device=self.parameters.device)
        return x

    def kl(self, other=None):
        if self.deterministic:
            return torch.Tensor([0.0])
        elif other is None:
            return 0.5 * torch.sum(torch.pow(self.mean, 2) + self.var - 1.0 - self.logvar, dim=[1, 2, 3])
        else:
            return 0.5 * torch.sum(torch.pow(self.mean - other.mean, 2) / other.var + self.var / other.var - 1.0 - self.logvar + other.logvar, dim=[1, 2, 3])

    def nll(self, sample, dims=[1, 2, 3]):
        if self.deterministic:
            return torch.Tensor([0.0])
        logtwopi = np.log(2.0 * np.pi)
        return 0.5 * torch.sum(logtwopi + self.logvar + torch.pow(sample - self.mean, 2) / self.var, dim=dims)

    def mode(self):
        return self.mean

def sample(self):
    x = self.mean + self.std * torch.randn(self.mean.shape).to(device=self.parameters.device)
    return x

def analytic_kernel(k):
    """Calculate the X4 kernel from the X2 kernel (for proof see appendix in paper)"""
    k_size = k.shape[0]
    big_k = np.zeros((3 * k_size - 2, 3 * k_size - 2))
    for r in range(k_size):
        for c in range(k_size):
            big_k[2 * r:2 * r + k_size, 2 * c:2 * c + k_size] += k[r, c] * k
    crop = k_size // 2
    cropped_big_k = big_k[crop:-crop, crop:-crop]
    return cropped_big_k / cropped_big_k.sum()

def analytic_kernel(k):
    """Calculate the X4 kernel from the X2 kernel (for proof see appendix in paper)"""
    k_size = k.shape[0]
    big_k = np.zeros((3 * k_size - 2, 3 * k_size - 2))
    for r in range(k_size):
        for c in range(k_size):
            big_k[2 * r:2 * r + k_size, 2 * c:2 * c + k_size] += k[r, c] * k
    crop = k_size // 2
    cropped_big_k = big_k[crop:-crop, crop:-crop]
    return cropped_big_k / cropped_big_k.sum()

def scale_module(module, scale):
    """
    Scale the parameters of a module and return it.
    """
    for p in module.parameters():
        p.detach().mul_(scale)
    return module

def noise_like(shape, device, repeat=False):
    repeat_noise = lambda: torch.randn((1, *shape[1:]), device=device).repeat(shape[0], *(1,) * (len(shape) - 1))
    noise = lambda: torch.randn(shape, device=device)
    return repeat_noise() if repeat else noise()

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

def encode(self, x):
    return self(x)

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

def encode(self, text):
    return self(text)

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

def encode(self, x):
    return self(x)

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

@torch.no_grad()
def get_x_noisy(self, x, t, noise=None):
    noise = default(noise, lambda: torch.randn_like(x))
    continuous_sqrt_alpha_cumprod = None
    if self.diffusion_model.use_continuous_noise:
        continuous_sqrt_alpha_cumprod = self.diffusion_model.sample_continuous_noise_level(x.shape[0], t + 1)
    return self.diffusion_model.q_sample(x_start=x, t=t, noise=noise, continuous_sqrt_alpha_cumprod=continuous_sqrt_alpha_cumprod)

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

@torch.no_grad()
def validation_step(self, batch, batch_idx):
    loss, *_ = self.shared_step(batch)
    for t in self.noisy_acc:
        _, logits, _, targets = self.shared_step(batch, t)
        self.noisy_acc[t]['acc@1'].append(self.compute_top_k(logits, targets, k=1, reduction='mean'))
        self.noisy_acc[t]['acc@5'].append(self.compute_top_k(logits, targets, k=5, reduction='mean'))
    return loss

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

@torch.no_grad()
def to_rgb(self, x):
    x = x.float()
    if not hasattr(self, 'colorize'):
        self.colorize = torch.randn(3, x.shape[1], 1, 1).to(x)
    x = nn.functional.conv2d(x, weight=self.colorize)
    x = 2.0 * (x - x.min()) / (x.max() - x.min()) - 1.0
    return x

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

def read_int(self):
    self.H = 1280 // 3
    self.W = 1920 // 3
    self.focal = 2083 // 3
    self.buffer = torch.zeros(self.H * self.W, 3).to('cuda')

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

def read_int(self):
    self.H = 1280
    self.W = 1920
    self.focal = 2083
    self.buffer = torch.zeros(self.H * self.W, 3).to('cuda')

def infer_sky(sky_pred, img_crop):
    """
    Args:
        img_crop: torch.tensor
            [1, 3, H, W], range 0-1
    """
    with torch.no_grad():
        peak_vector, latent_vector = sky_pred.latent_predictor(img_crop)
        hdr_skypano, ldr_skypano_pred, _ = sky_pred.decode_forward(latent_vector, peak_vector)
        hdr_skypano = hdr_skypano.permute(0, 2, 3, 1).squeeze().cpu().numpy().astype(np.float32)
        return hdr_skypano

def infer_sky(sky_pred, img_crop):
    """
    Args:
        img_crop: torch.tensor
            [1, 3, H, W], range 0-1
    """
    with torch.no_grad():
        peak_vector, latent_vector = sky_pred.latent_predictor(img_crop)
        hdr_skypano, ldr_skypano_pred, _ = sky_pred.decode_forward(latent_vector, peak_vector)
        hdr_skypano = hdr_skypano.permute(0, 2, 3, 1).squeeze().cpu().numpy().astype(np.float32)
        return hdr_skypano

def infer_and_save(sky_model, ldr_skypano, save_dir, filename):
    """
    Args:
        ldr_skypano: torch.tensor
            [1, 3, H, W]
    """
    with torch.no_grad():
        peak_vector, latent_vector = sky_model.encode_forward(ldr_skypano)
        hdr_skypano, ldr_skypano, _ = sky_model.decode_forward(latent_vector, peak_vector, peak_vector)
        sample_pseudo_gt = {'peak_vector': peak_vector.squeeze().cpu().numpy(), 'latent_vector': latent_vector.squeeze().cpu().numpy(), 'hdr_skypano': hdr_skypano.permute(0, 2, 3, 1).squeeze().cpu().numpy().astype(np.float32)}
        np.savez(os.path.join(save_dir, filename.replace('.jpg', '.npz')), **sample_pseudo_gt)
        hdr_skypano = hdr_skypano.permute(0, 2, 3, 1).squeeze().cpu().numpy().astype(np.float32)
        return hdr_skypano

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

def predict_step(self, batch, batch_idx):
    ldr_skypano, hdr_skypano_gt, peak_vector_gt = batch
    peak_vector_pred, latent_vector = self.encode_forward(ldr_skypano)
    hdr_skypano_pred, ldr_skypano_recon, _ = self.decode_forward(latent_vector, peak_vector_pred, peak_vector_pred)
    print(f'{batch_idx:0>3} \n                  HDRI Peak Intensity:\t\t {hdr_skypano_pred[0].flatten(1, 2).max(dim=-1)[0]} \n                  Peak Intensity Vector:\t {peak_vector_pred[0][3:]} \n                  Ground Truth Peak Intensity:\t {peak_vector_gt[0][3:]}')
    return_dict = {'ldr_skypano_input': ldr_skypano.permute(0, 2, 3, 1), 'ldr_skypano_pred': ldr_skypano_recon.permute(0, 2, 3, 1), 'hdr_skypano_gt': hdr_skypano_gt.permute(0, 2, 3, 1), 'hdr_skypano_pred': hdr_skypano_pred.permute(0, 2, 3, 1), 'batch_idx': batch_idx}
    return return_dict

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

def predict_step(self, batch, batch_idx):
    ldr_skypano, hdr_skypano_gt, peak_vector_gt = batch
    peak_vector_pred, latent_vector = self.encode_forward(ldr_skypano)
    hdr_skypano_pred, ldr_skypano_recon, _ = self.decode_forward(latent_vector, peak_vector_pred, peak_vector_pred)
    print(f'{batch_idx:0>3} \n                  HDRI Peak Intensity:\t\t {hdr_skypano_pred[0].flatten(1, 2).max(dim=-1)[0]} \n                  Peak Intensity Vector:\t {peak_vector_pred[0][3:]} \n                  Ground Truth Peak Intensity:\t {peak_vector_gt[0][3:]}')
    return_dict = {'ldr_skypano_input': ldr_skypano.permute(0, 2, 3, 1), 'ldr_skypano_pred': ldr_skypano_recon.permute(0, 2, 3, 1), 'hdr_skypano_gt': hdr_skypano_gt.permute(0, 2, 3, 1), 'hdr_skypano_pred': hdr_skypano_pred.permute(0, 2, 3, 1), 'batch_idx': batch_idx}
    return return_dict

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

def decode_forward(self, latent_vector, peak_vector):
    return self.sky_model.decode_forward(latent_vector, peak_vector, peak_vector)

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

def predict_step(self, batch, batch_idx):
    img_crops_tensor, peak_vector_gt, latent_vector_gt, mask_envmap_tensor, hdr_envmap_tensor, ldr_envmap_tensor = batch
    mask_envmap_tensor = torch.gt(mask_envmap_tensor, 0.8)
    peak_vector_pred, latent_vector_pred = self.latent_predictor(img_crops_tensor)
    hdr_skypano_pred, ldr_skypano_pred, _ = self.decode_forward(latent_vector_pred, peak_vector_pred)
    return_dict = {'hdr_skypano_pred': hdr_skypano_pred.permute(0, 2, 3, 1), 'ldr_skypano_pred': srgb_gamma_correction_torch(hdr_skypano_pred).permute(0, 2, 3, 1), 'hdr_skypano_gt': hdr_envmap_tensor.permute(0, 2, 3, 1), 'ldr_skypano_input': ldr_envmap_tensor.permute(0, 2, 3, 1), 'mask_env': mask_envmap_tensor.permute(0, 2, 3, 1), 'image_crops': img_crops_tensor.permute(0, 1, 3, 4, 2), 'batch_idx': batch_idx}
    return return_dict

