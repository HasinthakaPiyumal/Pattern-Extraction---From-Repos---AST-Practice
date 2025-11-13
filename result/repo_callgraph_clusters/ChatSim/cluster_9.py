# Cluster 9

def read_next_bytes(fid, num_bytes, format_char_sequence, endian_character='<'):
    """Read and unpack the next bytes from a binary file.
        :param fid:
        :param num_bytes: Sum of combination of {2, 4, 8}, e.g. 2, 6, 16, 30, etc.
        :param format_char_sequence: List of {c, e, f, d, h, H, i, I, l, L, q, Q}.
        :param endian_character: Any of {@, =, <, >, !}
        :return: Tuple of read and unpacked values.
        """
    data = fid.read(num_bytes)
    return struct.unpack(endian_character + format_char_sequence, data)

def load_colmap_sparse_points(path_to_model_file):
    """
    see: src/base/reconstruction.cc
        void Reconstruction::ReadPoints3DBinary(const std::string& path)
        void Reconstruction::WritePoints3DBinary(const std::string& path)

    """

    def read_next_bytes(fid, num_bytes, format_char_sequence, endian_character='<'):
        """Read and unpack the next bytes from a binary file.
        :param fid:
        :param num_bytes: Sum of combination of {2, 4, 8}, e.g. 2, 6, 16, 30, etc.
        :param format_char_sequence: List of {c, e, f, d, h, H, i, I, l, L, q, Q}.
        :param endian_character: Any of {@, =, <, >, !}
        :return: Tuple of read and unpacked values.
        """
        data = fid.read(num_bytes)
        return struct.unpack(endian_character + format_char_sequence, data)
    with open(path_to_model_file, 'rb') as fid:
        num_points = read_next_bytes(fid, 8, 'Q')[0]
        xyzs = np.empty((num_points, 3))
        rgbs = np.empty((num_points, 3))
        errors = np.empty((num_points, 1))
        for p_id in range(num_points):
            binary_point_line_properties = read_next_bytes(fid, num_bytes=43, format_char_sequence='QdddBBBd')
            xyz = np.array(binary_point_line_properties[1:4])
            rgb = np.array(binary_point_line_properties[4:7])
            error = np.array(binary_point_line_properties[7])
            track_length = read_next_bytes(fid, num_bytes=8, format_char_sequence='Q')[0]
            track_elems = read_next_bytes(fid, num_bytes=8 * track_length, format_char_sequence='ii' * track_length)
            xyzs[p_id] = xyz
            rgbs[p_id] = rgb
            errors[p_id] = error
    points = OrderedDict()
    points['xyz'] = xyzs
    points['rgb'] = rgbs
    points['error'] = errors
    return points

def blob_to_array(blob, dtype, shape=(-1,)):
    if IS_PYTHON3:
        return np.fromstring(blob, dtype=dtype).reshape(*shape)
    else:
        return np.frombuffer(blob, dtype=dtype).reshape(*shape)

def interpolate_linear(images, camera_id, file_format):
    if len(images) < 2:
        raise ValueError('Need at least two images for linear interpolation!')
    prev_image = images[0]
    prev_idx = image_to_idx(prev_image)
    prev_dq = DualQuaternion.FromQT(prev_image.q, prev_image.t)
    start = prev_idx
    new_images = []
    for image in images[1:]:
        curr_idx = image_to_idx(image)
        curr_dq = DualQuaternion.FromQT(image.q, image.t)
        T = curr_idx - prev_idx
        Tinv = 1.0 / T
        if prev_dq.q0.dot(curr_dq.q0) < 0:
            curr_dq = -curr_dq
        for i in xrange(1, T):
            t = i * Tinv
            dq = t * prev_dq + (1.0 - t) * curr_dq
            q, t = dq.ToQT()
            new_images.append(Image(file_format.format(prev_idx + i), args.camera_id, q, t))
        prev_idx = curr_idx
        prev_dq = curr_dq
    return new_images

def interpolate_hermite(images, camera_id, file_format):
    if len(images) < 4:
        raise ValueError('Need at least four images for Hermite spline interpolation!')
    new_images = []
    T0 = image_to_idx(images[0])
    dq0 = DualQuaternion.FromQT(images[0].q, images[0].t)
    T1 = image_to_idx(images[1])
    dq1 = DualQuaternion.FromQT(images[1].q, images[1].t)
    if dq0.q0.dot(dq1.q0) < 0:
        dq1 = -dq1
    dT = 1.0 / float(T1 - T0)
    for j in xrange(1, T1 - T0):
        t = j * dT
        dq = ((1.0 - t) * dq0 + t * dq1).normalize()
        new_images.append(Image(file_format.format(T0 + j), camera_id, *dq.ToQT()))
    T2 = image_to_idx(images[2])
    dq2 = DualQuaternion.FromQT(images[2].q, images[2].t)
    if dq1.q0.dot(dq2.q0) < 0:
        dq2 = -dq2
    for i in xrange(1, len(images) - 2):
        T3 = image_to_idx(images[i + 2])
        dq3 = DualQuaternion.FromQT(images[i + 2].q, images[i + 2].t)
        if dq2.q0.dot(dq3.q0) < 0:
            dq3 = -dq3
        prev_duration = T1 - T0
        current_duration = T2 - T1
        next_duration = T3 - T2
        dt1 = 1.0 / float(T2 - T0)
        dt2 = 1.0 / float(T3 - T1)
        m1 = current_duration * dt1 * (dq2 - dq1) + prev_duration * dt1 * (dq1 - dq0)
        m2 = next_duration * dt2 * (dq3 - dq2) + current_duration * dt2 * (dq2 - dq1)
        dT = 1.0 / float(current_duration)
        for j in xrange(1, current_duration):
            t = j * dT
            t2 = t * t
            t3 = t2 * t
            a1 = 2.0 * t3 - 3.0 * t2 + 1.0
            b1 = t3 - 2.0 * t2 + t
            a2 = -2.0 * t3 + 3.0 * t2
            b2 = t3 - t2
            dq = (a1 * dq1 + b1 * m1 + a2 * dq2 + b2 * m2).normalize()
            new_images.append(Image(file_format.format(T1 + j), camera_id, *dq.ToQT()))
        T0, T1, T2 = (T1, T2, T3)
        dq0, dq1, dq2 = (dq1, dq2, dq3)
    dT = 1.0 / float(T2 - T1)
    for j in xrange(1, T2 - T1):
        t = j * dT
        dq = ((1.0 - t) * dq1 + t * dq2).normalize()
        new_images.append(Image(file_format.format(T1 + j), camera_id, *dq.ToQT()))
    return new_images

def main(args):
    scene_manager = SceneManager(args.input_folder)
    scene_manager.load()
    image_ids = map(scene_manager.get_image_from_name, iter(lambda: sys.stdin.readline().strip(), ''))
    scene_manager.delete_images(image_ids)
    scene_manager.save(args.output_folder)

def main(args):
    scene_manager = SceneManager(args.input_folder)
    scene_manager.load()
    P = np.array([map(float, sys.stdin.readline().strip().split()) for _ in xrange(3)])
    scene_manager.points3D[:] = scene_manager.points3D.dot(P[:, :3].T) + P[:, 3]
    scale = np.cbrt(np.linalg.det(P[:, :3]))
    q_old_from_new = ~Quaternion.FromR(P[:, :3] / scale)
    for image in scene_manager.images.itervalues():
        image.q *= q_old_from_new
        image.tvec = scale * image.tvec - image.R().dot(P[:, 3])
    scene_manager.save(args.output_folder)

def blob_to_array(blob, dtype, shape=(-1,)):
    return np.frombuffer(blob, dtype).reshape(*shape)

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

def __init__(self, name_, camera_id_, q_, tvec_):
    self.name = name_
    self.camera_id = camera_id_
    self.q = q_
    self.tvec = tvec_
    self.points2D = np.empty((0, 2), dtype=np.float64)
    self.point3D_ids = np.empty((0,), dtype=np.uint64)

def rotation_matrix_to_axis_angle(R):
    return Quaternion.FromR(R).ToAxisAngle()

class _MatrixEntryIterator(object):

    def __init__(self, rows, cols, rowMajor):
        self.rows = rows
        self.cols = cols
        self.currentRow = 0
        self.currentCol = 0
        self.rowMajor = rowMajor

    def __iter__(self):
        return self

    def next(self):
        return self.__next__()

    def __next__(self):
        row = self.currentRow
        col = self.currentCol
        if self.rowMajor == 0:
            if self.currentCol >= self.cols:
                raise StopIteration
            self.currentRow = self.currentRow + 1
            if self.currentRow >= self.rows:
                self.currentRow = 0
                self.currentCol = self.currentCol + 1
        else:
            if self.currentRow >= self.rows:
                raise StopIteration
            self.currentCol = self.currentCol + 1
            if self.currentCol >= self.cols:
                self.currentCol = 0
                self.currentRow = self.currentRow + 1
        return (row, col)

def next(self):
    return self.__next__()

class EigenMatrixPrinter:
    """Print Eigen Matrix or Array of some kind"""

    def __init__(self, variety, val):
        """Extract all the necessary information"""
        self.variety = variety
        type = val.type
        if type.code == gdb.TYPE_CODE_REF:
            type = type.target()
        self.type = type.unqualified().strip_typedefs()
        tag = self.type.tag
        regex = re.compile('\\<.*\\>')
        m = regex.findall(tag)[0][1:-1]
        template_params = m.split(',')
        template_params = [x.replace(' ', '') for x in template_params]
        if template_params[1] == '-0x00000000000000001' or template_params[1] == '-0x000000001' or template_params[1] == '-1':
            self.rows = val['m_storage']['m_rows']
        else:
            self.rows = int(template_params[1])
        if template_params[2] == '-0x00000000000000001' or template_params[2] == '-0x000000001' or template_params[2] == '-1':
            self.cols = val['m_storage']['m_cols']
        else:
            self.cols = int(template_params[2])
        self.options = 0
        if len(template_params) > 3:
            self.options = template_params[3]
        self.rowMajor = int(self.options) & 1
        self.innerType = self.type.template_argument(0)
        self.val = val
        self.data = self.val['m_storage']['m_data']
        if self.data.type.code == gdb.TYPE_CODE_STRUCT:
            self.data = self.data['array']
            self.data = self.data.cast(self.innerType.pointer())

    class _iterator(_MatrixEntryIterator):

        def __init__(self, rows, cols, dataPtr, rowMajor):
            super(EigenMatrixPrinter._iterator, self).__init__(rows, cols, rowMajor)
            self.dataPtr = dataPtr

        def __next__(self):
            row, col = super(EigenMatrixPrinter._iterator, self).__next__()
            item = self.dataPtr.dereference()
            self.dataPtr = self.dataPtr + 1
            if self.cols == 1:
                return ('[%d]' % (row,), item)
            elif self.rows == 1:
                return ('[%d]' % (col,), item)
            return ('[%d,%d]' % (row, col), item)

    def children(self):
        return self._iterator(self.rows, self.cols, self.data, self.rowMajor)

    def to_string(self):
        return 'Eigen::%s<%s,%d,%d,%s> (data ptr: %s)' % (self.variety, self.innerType, self.rows, self.cols, 'RowMajor' if self.rowMajor else 'ColMajor', self.data)

def __init__(self, variety, val):
    """Extract all the necessary information"""
    self.variety = variety
    type = val.type
    if type.code == gdb.TYPE_CODE_REF:
        type = type.target()
    self.type = type.unqualified().strip_typedefs()
    tag = self.type.tag
    regex = re.compile('\\<.*\\>')
    m = regex.findall(tag)[0][1:-1]
    template_params = m.split(',')
    template_params = [x.replace(' ', '') for x in template_params]
    if template_params[1] == '-0x00000000000000001' or template_params[1] == '-0x000000001' or template_params[1] == '-1':
        self.rows = val['m_storage']['m_rows']
    else:
        self.rows = int(template_params[1])
    if template_params[2] == '-0x00000000000000001' or template_params[2] == '-0x000000001' or template_params[2] == '-1':
        self.cols = val['m_storage']['m_cols']
    else:
        self.cols = int(template_params[2])
    self.options = 0
    if len(template_params) > 3:
        self.options = template_params[3]
    self.rowMajor = int(self.options) & 1
    self.innerType = self.type.template_argument(0)
    self.val = val
    self.data = self.val['m_storage']['m_data']
    if self.data.type.code == gdb.TYPE_CODE_STRUCT:
        self.data = self.data['array']
        self.data = self.data.cast(self.innerType.pointer())

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

def __next__(self):
    element = self.currentElement
    if self.currentElement >= 4:
        raise StopIteration
    self.currentElement = self.currentElement + 1
    item = self.dataPtr.dereference()
    self.dataPtr = self.dataPtr + 1
    return ('[%s]' % (self.elementNames[element],), item)

def children(self):
    return self._iterator(self.rows, self.cols, self.data, self.rowMajor)

class EigenSparseMatrixPrinter:
    """Print an Eigen SparseMatrix"""

    def __init__(self, val):
        """Extract all the necessary information"""
        type = val.type
        if type.code == gdb.TYPE_CODE_REF:
            type = type.target()
        self.type = type.unqualified().strip_typedefs()
        tag = self.type.tag
        regex = re.compile('\\<.*\\>')
        m = regex.findall(tag)[0][1:-1]
        template_params = m.split(',')
        template_params = [x.replace(' ', '') for x in template_params]
        self.options = 0
        if len(template_params) > 1:
            self.options = template_params[1]
        self.rowMajor = int(self.options) & 1
        self.innerType = self.type.template_argument(0)
        self.val = val
        self.data = self.val['m_data']
        self.data = self.data.cast(self.innerType.pointer())

    class _iterator(_MatrixEntryIterator):

        def __init__(self, rows, cols, val, rowMajor):
            super(EigenSparseMatrixPrinter._iterator, self).__init__(rows, cols, rowMajor)
            self.val = val

        def __next__(self):
            row, col = super(EigenSparseMatrixPrinter._iterator, self).__next__()
            outer = row if self.rowMajor else col
            inner = col if self.rowMajor else row
            start = self.val['m_outerIndex'][outer]
            end = start + self.val['m_innerNonZeros'][outer] if self.val['m_innerNonZeros'] else self.val['m_outerIndex'][outer + 1]
            data = self.val['m_data']
            if start >= end:
                item = 0
            elif end > start and inner == data['m_indices'][end - 1]:
                item = data['m_values'][end - 1]
            else:
                indices = [data['m_indices'][x] for x in range(int(start), int(end) - 1)]
                idx = int(start) + bisect_left(indices, inner)
                if idx < end and data['m_indices'][idx] == inner:
                    item = data['m_values'][idx]
                else:
                    item = 0
            return ('[%d,%d]' % (row, col), item)

    def children(self):
        if self.data:
            return self._iterator(self.rows(), self.cols(), self.val, self.rowMajor)
        return iter([])

    def rows(self):
        return self.val['m_outerSize'] if self.rowMajor else self.val['m_innerSize']

    def cols(self):
        return self.val['m_innerSize'] if self.rowMajor else self.val['m_outerSize']

    def to_string(self):
        if self.data:
            status = 'not compressed' if self.val['m_innerNonZeros'] else 'compressed'
        else:
            status = 'empty'
        dimensions = '%d x %d' % (self.rows(), self.cols())
        layout = 'row' if self.rowMajor else 'column'
        return 'Eigen::SparseMatrix<%s>, %s, %s major, %s' % (self.innerType, dimensions, layout, status)

def __init__(self, val):
    """Extract all the necessary information"""
    type = val.type
    if type.code == gdb.TYPE_CODE_REF:
        type = type.target()
    self.type = type.unqualified().strip_typedefs()
    tag = self.type.tag
    regex = re.compile('\\<.*\\>')
    m = regex.findall(tag)[0][1:-1]
    template_params = m.split(',')
    template_params = [x.replace(' ', '') for x in template_params]
    self.options = 0
    if len(template_params) > 1:
        self.options = template_params[1]
    self.rowMajor = int(self.options) & 1
    self.innerType = self.type.template_argument(0)
    self.val = val
    self.data = self.val['m_data']
    self.data = self.data.cast(self.innerType.pointer())

def children(self):
    if self.data:
        return self._iterator(self.rows(), self.cols(), self.val, self.rowMajor)
    return iter([])

def to_string(self):
    if self.data:
        status = 'not compressed' if self.val['m_innerNonZeros'] else 'compressed'
    else:
        status = 'empty'
    dimensions = '%d x %d' % (self.rows(), self.cols())
    layout = 'row' if self.rowMajor else 'column'
    return 'Eigen::SparseMatrix<%s>, %s, %s major, %s' % (self.innerType, dimensions, layout, status)

class EigenQuaternionPrinter:
    """Print an Eigen Quaternion"""

    def __init__(self, val):
        """Extract all the necessary information"""
        type = val.type
        if type.code == gdb.TYPE_CODE_REF:
            type = type.target()
        self.type = type.unqualified().strip_typedefs()
        self.innerType = self.type.template_argument(0)
        self.val = val
        self.data = self.val['m_coeffs']['m_storage']['m_data']['array']
        self.data = self.data.cast(self.innerType.pointer())

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

    def children(self):
        return self._iterator(self.data)

    def to_string(self):
        return 'Eigen::Quaternion<%s> (data ptr: %s)' % (self.innerType, self.data)

def __init__(self, val):
    """Extract all the necessary information"""
    type = val.type
    if type.code == gdb.TYPE_CODE_REF:
        type = type.target()
    self.type = type.unqualified().strip_typedefs()
    self.innerType = self.type.template_argument(0)
    self.val = val
    self.data = self.val['m_coeffs']['m_storage']['m_data']['array']
    self.data = self.data.cast(self.innerType.pointer())

def next(self):
    return self.__next__()

def children(self):
    return self._iterator(self.data)

def build_eigen_dictionary():
    pretty_printers_dict[re.compile('^Eigen::Quaternion<.*>$')] = lambda val: EigenQuaternionPrinter(val)
    pretty_printers_dict[re.compile('^Eigen::Matrix<.*>$')] = lambda val: EigenMatrixPrinter('Matrix', val)
    pretty_printers_dict[re.compile('^Eigen::SparseMatrix<.*>$')] = lambda val: EigenSparseMatrixPrinter(val)
    pretty_printers_dict[re.compile('^Eigen::Array<.*>$')] = lambda val: EigenMatrixPrinter('Array', val)

def lookup_function(val):
    """Look-up and return a pretty-printer that can print va."""
    type = val.type
    if type.code == gdb.TYPE_CODE_REF:
        type = type.target()
    type = type.unqualified().strip_typedefs()
    typename = type.tag
    if typename == None:
        return None
    for function in pretty_printers_dict:
        if function.search(typename):
            return pretty_printers_dict[function](val)
    return None

def interpolate_linear(images, camera_id, file_format):
    if len(images) < 2:
        raise ValueError('Need at least two images for linear interpolation!')
    prev_image = images[0]
    prev_idx = image_to_idx(prev_image)
    prev_dq = DualQuaternion.FromQT(prev_image.q, prev_image.t)
    start = prev_idx
    new_images = []
    for image in images[1:]:
        curr_idx = image_to_idx(image)
        curr_dq = DualQuaternion.FromQT(image.q, image.t)
        T = curr_idx - prev_idx
        Tinv = 1.0 / T
        if prev_dq.q0.dot(curr_dq.q0) < 0:
            curr_dq = -curr_dq
        for i in xrange(1, T):
            t = i * Tinv
            dq = t * prev_dq + (1.0 - t) * curr_dq
            q, t = dq.ToQT()
            new_images.append(Image(file_format.format(prev_idx + i), args.camera_id, q, t))
        prev_idx = curr_idx
        prev_dq = curr_dq
    return new_images

def interpolate_hermite(images, camera_id, file_format):
    if len(images) < 4:
        raise ValueError('Need at least four images for Hermite spline interpolation!')
    new_images = []
    T0 = image_to_idx(images[0])
    dq0 = DualQuaternion.FromQT(images[0].q, images[0].t)
    T1 = image_to_idx(images[1])
    dq1 = DualQuaternion.FromQT(images[1].q, images[1].t)
    if dq0.q0.dot(dq1.q0) < 0:
        dq1 = -dq1
    dT = 1.0 / float(T1 - T0)
    for j in xrange(1, T1 - T0):
        t = j * dT
        dq = ((1.0 - t) * dq0 + t * dq1).normalize()
        new_images.append(Image(file_format.format(T0 + j), camera_id, *dq.ToQT()))
    T2 = image_to_idx(images[2])
    dq2 = DualQuaternion.FromQT(images[2].q, images[2].t)
    if dq1.q0.dot(dq2.q0) < 0:
        dq2 = -dq2
    for i in xrange(1, len(images) - 2):
        T3 = image_to_idx(images[i + 2])
        dq3 = DualQuaternion.FromQT(images[i + 2].q, images[i + 2].t)
        if dq2.q0.dot(dq3.q0) < 0:
            dq3 = -dq3
        prev_duration = T1 - T0
        current_duration = T2 - T1
        next_duration = T3 - T2
        dt1 = 1.0 / float(T2 - T0)
        dt2 = 1.0 / float(T3 - T1)
        m1 = current_duration * dt1 * (dq2 - dq1) + prev_duration * dt1 * (dq1 - dq0)
        m2 = next_duration * dt2 * (dq3 - dq2) + current_duration * dt2 * (dq2 - dq1)
        dT = 1.0 / float(current_duration)
        for j in xrange(1, current_duration):
            t = j * dT
            t2 = t * t
            t3 = t2 * t
            a1 = 2.0 * t3 - 3.0 * t2 + 1.0
            b1 = t3 - 2.0 * t2 + t
            a2 = -2.0 * t3 + 3.0 * t2
            b2 = t3 - t2
            dq = (a1 * dq1 + b1 * m1 + a2 * dq2 + b2 * m2).normalize()
            new_images.append(Image(file_format.format(T1 + j), camera_id, *dq.ToQT()))
        T0, T1, T2 = (T1, T2, T3)
        dq0, dq1, dq2 = (dq1, dq2, dq3)
    dT = 1.0 / float(T2 - T1)
    for j in xrange(1, T2 - T1):
        t = j * dT
        dq = ((1.0 - t) * dq1 + t * dq2).normalize()
        new_images.append(Image(file_format.format(T1 + j), camera_id, *dq.ToQT()))
    return new_images

def main(args):
    scene_manager = SceneManager(args.input_folder)
    scene_manager.load()
    image_ids = map(scene_manager.get_image_from_name, iter(lambda: sys.stdin.readline().strip(), ''))
    scene_manager.delete_images(image_ids)
    scene_manager.save(args.output_folder)

def main(args):
    scene_manager = SceneManager(args.input_folder)
    scene_manager.load()
    P = np.array([map(float, sys.stdin.readline().strip().split()) for _ in xrange(3)])
    scene_manager.points3D[:] = scene_manager.points3D.dot(P[:, :3].T) + P[:, 3]
    scale = np.cbrt(np.linalg.det(P[:, :3]))
    q_old_from_new = ~Quaternion.FromR(P[:, :3] / scale)
    for image in scene_manager.images.itervalues():
        image.q *= q_old_from_new
        image.tvec = scale * image.tvec - image.R().dot(P[:, 3])
    scene_manager.save(args.output_folder)

def blob_to_array(blob, dtype, shape=(-1,)):
    return np.frombuffer(blob, dtype).reshape(*shape)

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

def __init__(self, name_, camera_id_, q_, tvec_):
    self.name = name_
    self.camera_id = camera_id_
    self.q = q_
    self.tvec = tvec_
    self.points2D = np.empty((0, 2), dtype=np.float64)
    self.point3D_ids = np.empty((0,), dtype=np.uint64)

def rotation_matrix_to_axis_angle(R):
    return Quaternion.FromR(R).ToAxisAngle()

def read_next_bytes(fid, num_bytes, format_char_sequence, endian_character='<'):
    """Read and unpack the next bytes from a binary file.
    :param fid:
    :param num_bytes: Sum of combination of {2, 4, 8}, e.g. 2, 6, 16, 30, etc.
    :param format_char_sequence: List of {c, e, f, d, h, H, i, I, l, L, q, Q}.
    :param endian_character: Any of {@, =, <, >, !}
    :return: Tuple of read and unpacked values.
    """
    data = fid.read(num_bytes)
    return struct.unpack(endian_character + format_char_sequence, data)

def read_cameras_text(path):
    """
    see: src/base/reconstruction.cc
        void Reconstruction::WriteCamerasText(const std::string& path)
        void Reconstruction::ReadCamerasText(const std::string& path)
    """
    cameras = {}
    with open(path, 'r') as fid:
        while True:
            line = fid.readline()
            if not line:
                break
            line = line.strip()
            if len(line) > 0 and line[0] != '#':
                elems = line.split()
                camera_id = int(elems[0])
                model = elems[1]
                width = int(elems[2])
                height = int(elems[3])
                params = np.array(tuple(map(float, elems[4:])))
                cameras[camera_id] = Camera(id=camera_id, model=model, width=width, height=height, params=params)
    return cameras

def read_cameras_binary(path_to_model_file):
    """
    see: src/base/reconstruction.cc
        void Reconstruction::WriteCamerasBinary(const std::string& path)
        void Reconstruction::ReadCamerasBinary(const std::string& path)
    """
    cameras = {}
    with open(path_to_model_file, 'rb') as fid:
        num_cameras = read_next_bytes(fid, 8, 'Q')[0]
        for camera_line_index in range(num_cameras):
            camera_properties = read_next_bytes(fid, num_bytes=24, format_char_sequence='iiQQ')
            camera_id = camera_properties[0]
            model_id = camera_properties[1]
            model_name = CAMERA_MODEL_IDS[camera_properties[1]].model_name
            width = camera_properties[2]
            height = camera_properties[3]
            num_params = CAMERA_MODEL_IDS[model_id].num_params
            params = read_next_bytes(fid, num_bytes=8 * num_params, format_char_sequence='d' * num_params)
            cameras[camera_id] = Camera(id=camera_id, model=model_name, width=width, height=height, params=np.array(params))
        assert len(cameras) == num_cameras
    return cameras

def read_images_text(path):
    """
    see: src/base/reconstruction.cc
        void Reconstruction::ReadImagesText(const std::string& path)
        void Reconstruction::WriteImagesText(const std::string& path)
    """
    images = {}
    with open(path, 'r') as fid:
        while True:
            line = fid.readline()
            if not line:
                break
            line = line.strip()
            if len(line) > 0 and line[0] != '#':
                elems = line.split()
                image_id = int(elems[0])
                qvec = np.array(tuple(map(float, elems[1:5])))
                tvec = np.array(tuple(map(float, elems[5:8])))
                camera_id = int(elems[8])
                image_name = elems[9]
                elems = fid.readline().split()
                xys = np.column_stack([tuple(map(float, elems[0::3])), tuple(map(float, elems[1::3]))])
                point3D_ids = np.array(tuple(map(int, elems[2::3])))
                images[image_id] = Image(id=image_id, qvec=qvec, tvec=tvec, camera_id=camera_id, name=image_name, xys=xys, point3D_ids=point3D_ids)
    return images

def read_images_binary(path_to_model_file):
    """
    see: src/base/reconstruction.cc
        void Reconstruction::ReadImagesBinary(const std::string& path)
        void Reconstruction::WriteImagesBinary(const std::string& path)
    """
    images = {}
    with open(path_to_model_file, 'rb') as fid:
        num_reg_images = read_next_bytes(fid, 8, 'Q')[0]
        for image_index in range(num_reg_images):
            binary_image_properties = read_next_bytes(fid, num_bytes=64, format_char_sequence='idddddddi')
            image_id = binary_image_properties[0]
            qvec = np.array(binary_image_properties[1:5])
            tvec = np.array(binary_image_properties[5:8])
            camera_id = binary_image_properties[8]
            image_name = ''
            current_char = read_next_bytes(fid, 1, 'c')[0]
            while current_char != b'\x00':
                image_name += current_char.decode('utf-8')
                current_char = read_next_bytes(fid, 1, 'c')[0]
            num_points2D = read_next_bytes(fid, num_bytes=8, format_char_sequence='Q')[0]
            x_y_id_s = read_next_bytes(fid, num_bytes=24 * num_points2D, format_char_sequence='ddq' * num_points2D)
            xys = np.column_stack([tuple(map(float, x_y_id_s[0::3])), tuple(map(float, x_y_id_s[1::3]))])
            point3D_ids = np.array(tuple(map(int, x_y_id_s[2::3])))
            images[image_id] = Image(id=image_id, qvec=qvec, tvec=tvec, camera_id=camera_id, name=image_name, xys=xys, point3D_ids=point3D_ids)
    return images

def read_points3D_text(path):
    """
    see: src/base/reconstruction.cc
        void Reconstruction::ReadPoints3DText(const std::string& path)
        void Reconstruction::WritePoints3DText(const std::string& path)
    """
    points3D = {}
    with open(path, 'r') as fid:
        while True:
            line = fid.readline()
            if not line:
                break
            line = line.strip()
            if len(line) > 0 and line[0] != '#':
                elems = line.split()
                point3D_id = int(elems[0])
                xyz = np.array(tuple(map(float, elems[1:4])))
                rgb = np.array(tuple(map(int, elems[4:7])))
                error = float(elems[7])
                image_ids = np.array(tuple(map(int, elems[8::2])))
                point2D_idxs = np.array(tuple(map(int, elems[9::2])))
                points3D[point3D_id] = Point3D(id=point3D_id, xyz=xyz, rgb=rgb, error=error, image_ids=image_ids, point2D_idxs=point2D_idxs)
    return points3D

def read_points3d_binary(path_to_model_file):
    """
    see: src/base/reconstruction.cc
        void Reconstruction::ReadPoints3DBinary(const std::string& path)
        void Reconstruction::WritePoints3DBinary(const std::string& path)
    """
    points3D = {}
    with open(path_to_model_file, 'rb') as fid:
        num_points = read_next_bytes(fid, 8, 'Q')[0]
        for point_line_index in range(num_points):
            binary_point_line_properties = read_next_bytes(fid, num_bytes=43, format_char_sequence='QdddBBBd')
            point3D_id = binary_point_line_properties[0]
            xyz = np.array(binary_point_line_properties[1:4])
            rgb = np.array(binary_point_line_properties[4:7])
            error = np.array(binary_point_line_properties[7])
            track_length = read_next_bytes(fid, num_bytes=8, format_char_sequence='Q')[0]
            track_elems = read_next_bytes(fid, num_bytes=8 * track_length, format_char_sequence='ii' * track_length)
            image_ids = np.array(tuple(map(int, track_elems[0::2])))
            point2D_idxs = np.array(tuple(map(int, track_elems[1::2])))
            points3D[point3D_id] = Point3D(id=point3D_id, xyz=xyz, rgb=rgb, error=error, image_ids=image_ids, point2D_idxs=point2D_idxs)
    return points3D

def read():
    global conn
    messageLength = conn.recv(4)
    messageLength = int.from_bytes(messageLength, 'little')
    message = conn.recv(messageLength)
    return json.loads(message.decode('utf-8'))

def receive():
    message = read()
    width = message['resolution_x']
    height = message['resolution_y']
    if width != 0 and height != 0:
        try:
            do_training = bool(message['train'])
            fovy = message['fov_y']
            fovx = message['fov_x']
            znear = message['z_near']
            zfar = message['z_far']
            do_shs_python = bool(message['shs_python'])
            do_rot_scale_python = bool(message['rot_scale_python'])
            keep_alive = bool(message['keep_alive'])
            scaling_modifier = message['scaling_modifier']
            world_view_transform = torch.reshape(torch.tensor(message['view_matrix']), (4, 4)).cuda()
            world_view_transform[:, 1] = -world_view_transform[:, 1]
            world_view_transform[:, 2] = -world_view_transform[:, 2]
            full_proj_transform = torch.reshape(torch.tensor(message['view_projection_matrix']), (4, 4)).cuda()
            full_proj_transform[:, 1] = -full_proj_transform[:, 1]
            custom_cam = MiniCam(width, height, fovy, fovx, znear, zfar, world_view_transform, full_proj_transform)
        except Exception as e:
            print('')
            traceback.print_exc()
            raise e
        return (custom_cam, do_training, do_shs_python, do_rot_scale_python, keep_alive, scaling_modifier)
    else:
        return (None, None, None, None, None, None)

def loadCam(args, id, cam_info, resolution_scale):
    """
    resolution_scale is always 1.0
    """
    orig_w, orig_h = cam_info.image.size
    if args.resolution in [1, 2, 4, 8]:
        resolution = (round(orig_w / (resolution_scale * args.resolution)), round(orig_h / (resolution_scale * args.resolution)))
        K = cam_info.K / (resolution_scale * args.resolution)
    else:
        if args.resolution == -1:
            if orig_w > 1600:
                global WARNED
                if not WARNED:
                    print("[ INFO ] Encountered quite large input images (>1.6K pixels width), rescaling to 1.6K.\n If this is not desired, please explicitly specify '--resolution/-r' as 1")
                    WARNED = True
                global_down = orig_w / 1600
            else:
                global_down = 1
        else:
            global_down = orig_w / args.resolution
        scale = float(global_down) * float(resolution_scale)
        resolution = (int(orig_w / scale), int(orig_h / scale))
        K = cam_info.K / scale
    resized_image_rgb = PILtoTorch(cam_info.image, resolution)
    if cam_info.sky_mask is not None:
        resized_sky_mask = torch.tensor(cv2.resize(cam_info.sky_mask, resolution, interpolation=cv2.INTER_NEAREST)).to(resized_image_rgb.device)
        resized_sky_mask = resized_sky_mask == args.sky_value
    else:
        resized_sky_mask = None
    if cam_info.normal is not None:
        raise NotImplementedError('Normal maps are not supported in this version')
    else:
        resized_normal = None
    if cam_info.depth is not None:
        resized_depth = torch.tensor(cv2.resize(cam_info.depth, resolution, interpolation=cv2.INTER_NEAREST)).to(resized_image_rgb.device)
    else:
        resized_depth = None
    gt_image = resized_image_rgb[:3, ...]
    loaded_mask = None
    if resized_image_rgb.shape[1] == 4:
        loaded_mask = resized_image_rgb[3:4, ...]
    return Camera(colmap_id=cam_info.uid, R=cam_info.R, T=cam_info.T, FoVx=cam_info.FovX, FoVy=cam_info.FovY, image=gt_image, gt_alpha_mask=loaded_mask, image_name=cam_info.image_name, uid=id, data_device=args.data_device, K=K, sky_mask=resized_sky_mask, normal=resized_normal, depth=resized_depth, exposure_scale=cam_info.exposure_scale)

def searchForMaxIteration(folder):
    saved_iters = [int(fname.split('_')[-1]) for fname in os.listdir(folder)]
    return max(saved_iters)

def read_next_bytes(fid, num_bytes, format_char_sequence, endian_character='<'):
    """Read and unpack the next bytes from a binary file.
    :param fid:
    :param num_bytes: Sum of combination of {2, 4, 8}, e.g. 2, 6, 16, 30, etc.
    :param format_char_sequence: List of {c, e, f, d, h, H, i, I, l, L, q, Q}.
    :param endian_character: Any of {@, =, <, >, !}
    :return: Tuple of read and unpacked values.
    """
    data = fid.read(num_bytes)
    return struct.unpack(endian_character + format_char_sequence, data)

def read_points3D_text(path):
    """
    see: src/base/reconstruction.cc
        void Reconstruction::ReadPoints3DText(const std::string& path)
        void Reconstruction::WritePoints3DText(const std::string& path)
    """
    xyzs = None
    rgbs = None
    errors = None
    num_points = 0
    with open(path, 'r') as fid:
        while True:
            line = fid.readline()
            if not line:
                break
            line = line.strip()
            if len(line) > 0 and line[0] != '#':
                num_points += 1
    xyzs = np.empty((num_points, 3))
    rgbs = np.empty((num_points, 3))
    errors = np.empty((num_points, 1))
    count = 0
    with open(path, 'r') as fid:
        while True:
            line = fid.readline()
            if not line:
                break
            line = line.strip()
            if len(line) > 0 and line[0] != '#':
                elems = line.split()
                xyz = np.array(tuple(map(float, elems[1:4])))
                rgb = np.array(tuple(map(int, elems[4:7])))
                error = np.array(float(elems[7]))
                xyzs[count] = xyz
                rgbs[count] = rgb
                errors[count] = error
                count += 1
    return (xyzs, rgbs, errors)

def read_points3D_binary(path_to_model_file):
    """
    see: src/base/reconstruction.cc
        void Reconstruction::ReadPoints3DBinary(const std::string& path)
        void Reconstruction::WritePoints3DBinary(const std::string& path)
    """
    with open(path_to_model_file, 'rb') as fid:
        num_points = read_next_bytes(fid, 8, 'Q')[0]
        xyzs = np.empty((num_points, 3))
        rgbs = np.empty((num_points, 3))
        errors = np.empty((num_points, 1))
        for p_id in range(num_points):
            binary_point_line_properties = read_next_bytes(fid, num_bytes=43, format_char_sequence='QdddBBBd')
            xyz = np.array(binary_point_line_properties[1:4])
            rgb = np.array(binary_point_line_properties[4:7])
            error = np.array(binary_point_line_properties[7])
            track_length = read_next_bytes(fid, num_bytes=8, format_char_sequence='Q')[0]
            track_elems = read_next_bytes(fid, num_bytes=8 * track_length, format_char_sequence='ii' * track_length)
            xyzs[p_id] = xyz
            rgbs[p_id] = rgb
            errors[p_id] = error
    return (xyzs, rgbs, errors)

def read_intrinsics_text(path):
    """
    Taken from https://github.com/colmap/colmap/blob/dev/scripts/python/read_write_model.py
    """
    cameras = {}
    with open(path, 'r') as fid:
        while True:
            line = fid.readline()
            if not line:
                break
            line = line.strip()
            if len(line) > 0 and line[0] != '#':
                elems = line.split()
                camera_id = int(elems[0])
                model = elems[1]
                assert model == 'PINHOLE', 'While the loader support other types, the rest of the code assumes PINHOLE'
                width = int(elems[2])
                height = int(elems[3])
                params = np.array(tuple(map(float, elems[4:])))
                cameras[camera_id] = Camera(id=camera_id, model=model, width=width, height=height, params=params)
    return cameras

def read_extrinsics_binary(path_to_model_file):
    """
    see: src/base/reconstruction.cc
        void Reconstruction::ReadImagesBinary(const std::string& path)
        void Reconstruction::WriteImagesBinary(const std::string& path)
    """
    images = {}
    with open(path_to_model_file, 'rb') as fid:
        num_reg_images = read_next_bytes(fid, 8, 'Q')[0]
        for _ in range(num_reg_images):
            binary_image_properties = read_next_bytes(fid, num_bytes=64, format_char_sequence='idddddddi')
            image_id = binary_image_properties[0]
            qvec = np.array(binary_image_properties[1:5])
            tvec = np.array(binary_image_properties[5:8])
            camera_id = binary_image_properties[8]
            image_name = ''
            current_char = read_next_bytes(fid, 1, 'c')[0]
            while current_char != b'\x00':
                image_name += current_char.decode('utf-8')
                current_char = read_next_bytes(fid, 1, 'c')[0]
            num_points2D = read_next_bytes(fid, num_bytes=8, format_char_sequence='Q')[0]
            x_y_id_s = read_next_bytes(fid, num_bytes=24 * num_points2D, format_char_sequence='ddq' * num_points2D)
            xys = np.column_stack([tuple(map(float, x_y_id_s[0::3])), tuple(map(float, x_y_id_s[1::3]))])
            point3D_ids = np.array(tuple(map(int, x_y_id_s[2::3])))
            images[image_id] = Image(id=image_id, qvec=qvec, tvec=tvec, camera_id=camera_id, name=image_name, xys=xys, point3D_ids=point3D_ids)
    return images

def read_intrinsics_binary(path_to_model_file):
    """
    see: src/base/reconstruction.cc
        void Reconstruction::WriteCamerasBinary(const std::string& path)
        void Reconstruction::ReadCamerasBinary(const std::string& path)
    """
    cameras = {}
    with open(path_to_model_file, 'rb') as fid:
        num_cameras = read_next_bytes(fid, 8, 'Q')[0]
        for _ in range(num_cameras):
            camera_properties = read_next_bytes(fid, num_bytes=24, format_char_sequence='iiQQ')
            camera_id = camera_properties[0]
            model_id = camera_properties[1]
            model_name = CAMERA_MODEL_IDS[camera_properties[1]].model_name
            width = camera_properties[2]
            height = camera_properties[3]
            num_params = CAMERA_MODEL_IDS[model_id].num_params
            params = read_next_bytes(fid, num_bytes=8 * num_params, format_char_sequence='d' * num_params)
            cameras[camera_id] = Camera(id=camera_id, model=model_name, width=width, height=height, params=np.array(params))
        assert len(cameras) == num_cameras
    return cameras

def read_extrinsics_text(path):
    """
    Taken from https://github.com/colmap/colmap/blob/dev/scripts/python/read_write_model.py
    """
    images = {}
    with open(path, 'r') as fid:
        while True:
            line = fid.readline()
            if not line:
                break
            line = line.strip()
            if len(line) > 0 and line[0] != '#':
                elems = line.split()
                image_id = int(elems[0])
                qvec = np.array(tuple(map(float, elems[1:5])))
                tvec = np.array(tuple(map(float, elems[5:8])))
                camera_id = int(elems[8])
                image_name = elems[9]
                elems = fid.readline().split()
                xys = np.column_stack([tuple(map(float, elems[0::3])), tuple(map(float, elems[1::3]))])
                point3D_ids = np.array(tuple(map(int, elems[2::3])))
                images[image_id] = Image(id=image_id, qvec=qvec, tvec=tvec, camera_id=camera_id, name=image_name, xys=xys, point3D_ids=point3D_ids)
    return images

def read_colmap_bin_array(path):
    """
    Taken from https://github.com/colmap/colmap/blob/dev/scripts/python/read_dense.py

    :param path: path to the colmap binary file.
    :return: nd array with the floating point values in the value
    """
    with open(path, 'rb') as fid:
        width, height, channels = np.genfromtxt(fid, delimiter='&', max_rows=1, usecols=(0, 1, 2), dtype=int)
        fid.seek(0)
        num_delimiter = 0
        byte = fid.read(1)
        while True:
            if byte == b'&':
                num_delimiter += 1
                if num_delimiter >= 3:
                    break
            byte = fid.read(1)
        array = np.fromfile(fid, np.float32)
    array = array.reshape((width, height, channels), order='F')
    return np.transpose(array, (1, 0, 2)).squeeze()

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

def forward_tracker(self, frames_ps, init_box):
    init_box = np.array(init_box).astype(np.float32).reshape(-1, 4)
    seq = Sequence('tmp', frames_ps, 'inpaint-anything', init_box)
    all_box_xywh = get_box_using_ostrack(self.tracker, seq)
    return all_box_xywh

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

def forward_tracker(self, frames_ps, init_box):
    init_box = np.array(init_box).astype(np.float32).reshape(-1, 4)
    seq = Sequence('tmp', frames_ps, 'inpaint-anything', init_box)
    all_box_xywh = get_box_using_ostrack(self.tracker, seq)
    return all_box_xywh

def vis_traj(seq, output_boxes):
    frames_list = []
    for frame, box in zip(seq.frames, output_boxes):
        frame = cv2.imread(frame)
        x, y, w, h = box
        x1, y1, x2, y2 = map(lambda x: int(x), [x, y, x + w, y + h])
        frame = cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), thickness=2)
        frames_list.append(frame)
    return frames_list

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

@staticmethod
def imread(path, image_name):
    zfile = ZipReader.build_file_dict(path)
    data = zfile.read(image_name)
    im = Image.open(io.BytesIO(data))
    return im

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

def _separate_heads(self, x: Tensor, num_heads: int) -> Tensor:
    b, n, c = x.shape
    x = x.reshape(b, n, num_heads, c // num_heads)
    return x.transpose(1, 2)

def _recombine_heads(self, x: Tensor) -> Tensor:
    b, n_heads, n_tokens, c_per_head = x.shape
    x = x.transpose(1, 2)
    return x.reshape(b, n_tokens, n_heads * c_per_head)

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

def _embed_masks(self, input_mask: torch.Tensor, has_mask_input: torch.Tensor) -> torch.Tensor:
    mask_embedding = has_mask_input * self.model.prompt_encoder.mask_downscaling(input_mask)
    mask_embedding = mask_embedding + (1 - has_mask_input) * self.model.prompt_encoder.no_mask_embed.weight.reshape(1, -1, 1, 1)
    return mask_embedding

class ResizeLongestSide:
    """
    Resizes images to longest side 'target_length', as well as provides
    methods for resizing coordinates and boxes. Provides methods for
    transforming both numpy array and batched torch tensors.
    """

    def __init__(self, target_length: int) -> None:
        self.target_length = target_length

    def apply_image(self, image: np.ndarray) -> np.ndarray:
        """
        Expects a numpy array with shape HxWxC in uint8 format.
        """
        target_size = self.get_preprocess_shape(image.shape[0], image.shape[1], self.target_length)
        return np.array(resize(to_pil_image(image), target_size))

    def apply_coords(self, coords: np.ndarray, original_size: Tuple[int, ...]) -> np.ndarray:
        """
        Expects a numpy array of length 2 in the final dimension. Requires the
        original image size in (H, W) format.
        """
        old_h, old_w = original_size
        new_h, new_w = self.get_preprocess_shape(original_size[0], original_size[1], self.target_length)
        coords = deepcopy(coords).astype(float)
        coords[..., 0] = coords[..., 0] * (new_w / old_w)
        coords[..., 1] = coords[..., 1] * (new_h / old_h)
        return coords

    def apply_boxes(self, boxes: np.ndarray, original_size: Tuple[int, ...]) -> np.ndarray:
        """
        Expects a numpy array shape Bx4. Requires the original image size
        in (H, W) format.
        """
        boxes = self.apply_coords(boxes.reshape(-1, 2, 2), original_size)
        return boxes.reshape(-1, 4)

    def apply_image_torch(self, image: torch.Tensor) -> torch.Tensor:
        """
        Expects batched images with shape BxCxHxW and float format. This
        transformation may not exactly match apply_image. apply_image is
        the transformation expected by the model.
        """
        target_size = self.get_preprocess_shape(image.shape[0], image.shape[1], self.target_length)
        return F.interpolate(image, target_size, mode='bilinear', align_corners=False, antialias=True)

    def apply_coords_torch(self, coords: torch.Tensor, original_size: Tuple[int, ...]) -> torch.Tensor:
        """
        Expects a torch tensor with length 2 in the last dimension. Requires the
        original image size in (H, W) format.
        """
        old_h, old_w = original_size
        new_h, new_w = self.get_preprocess_shape(original_size[0], original_size[1], self.target_length)
        coords = deepcopy(coords).to(torch.float)
        coords[..., 0] = coords[..., 0] * (new_w / old_w)
        coords[..., 1] = coords[..., 1] * (new_h / old_h)
        return coords

    def apply_boxes_torch(self, boxes: torch.Tensor, original_size: Tuple[int, ...]) -> torch.Tensor:
        """
        Expects a torch tensor with shape Bx4. Requires the original image
        size in (H, W) format.
        """
        boxes = self.apply_coords_torch(boxes.reshape(-1, 2, 2), original_size)
        return boxes.reshape(-1, 4)

    @staticmethod
    def get_preprocess_shape(oldh: int, oldw: int, long_side_length: int) -> Tuple[int, int]:
        """
        Compute the output size given input size and target long side length.
        """
        scale = long_side_length * 1.0 / max(oldh, oldw)
        newh, neww = (oldh * scale, oldw * scale)
        neww = int(neww + 0.5)
        newh = int(newh + 0.5)
        return (newh, neww)

def apply_boxes_torch(self, boxes: torch.Tensor, original_size: Tuple[int, ...]) -> torch.Tensor:
    """
        Expects a torch tensor with shape Bx4. Requires the original image
        size in (H, W) format.
        """
    boxes = self.apply_coords_torch(boxes.reshape(-1, 2, 2), original_size)
    return boxes.reshape(-1, 4)

def rle_to_mask(rle: Dict[str, Any]) -> np.ndarray:
    """Compute a binary mask from an uncompressed RLE."""
    h, w = rle['size']
    mask = np.empty(h * w, dtype=bool)
    idx = 0
    parity = False
    for count in rle['counts']:
        mask[idx:idx + count] = parity
        idx += count
        parity ^= True
    mask = mask.reshape(w, h)
    return mask.transpose()

def build_all_layer_point_grids(n_per_side: int, n_layers: int, scale_per_layer: int) -> List[np.ndarray]:
    """Generates point grids for all crop layers."""
    points_by_layer = []
    for i in range(n_layers + 1):
        n_points = int(n_per_side / scale_per_layer ** i)
        points_by_layer.append(build_point_grid(n_points))
    return points_by_layer

def crop_len(orig_len, n_crops, overlap):
    return int(math.ceil((overlap * (n_crops - 1) + orig_len) / n_crops))

def coco_encode_rle(uncompressed_rle: Dict[str, Any]) -> Dict[str, Any]:
    from pycocotools import mask as mask_utils
    h, w = uncompressed_rle['size']
    rle = mask_utils.frPyObjects(uncompressed_rle, h, w)
    rle['counts'] = rle['counts'].decode('utf-8')
    return rle

def main(args):
    if args.categories == 'nofilter':
        good_categories = None
    else:
        with open(args.categories, 'r') as f:
            good_categories = set((line.strip().split(' ')[0] for line in f if line.strip()))
    all_input_files = list(braceexpand.braceexpand(args.infile))
    chunk_size = int(math.ceil(len(all_input_files) / args.n_read_streams))
    input_iterators = [iter(wds.Dataset(all_input_files[start:start + chunk_size]).shuffle(args.shuffle_buffer)) for start in range(0, len(all_input_files), chunk_size)]
    output_datasets = [wds.ShardWriter(args.outpattern.format(i)) for i in range(args.n_write_streams)]
    good_readers = list(range(len(input_iterators)))
    step_i = 0
    good_samples = 0
    bad_samples = 0
    while len(good_readers) > 0:
        if step_i % args.print_freq == 0:
            print(f'Iterations done {step_i}; readers alive {good_readers}; good samples {good_samples}; bad samples {bad_samples}')
        step_i += 1
        ri = random.choice(good_readers)
        try:
            sample = next(input_iterators[ri])
        except StopIteration:
            good_readers = list(set(good_readers) - {ri})
            continue
        if good_categories is not None and (not is_good_key(sample['__key__'], good_categories)):
            bad_samples += 1
            continue
        wi = random.randint(0, args.n_write_streams - 1)
        output_datasets[wi].write(sample)
        good_samples += 1

def get_checkpoint_files(s):
    s = s.strip()
    if ',' in s:
        return [get_checkpoint_files(chunk) for chunk in s.split(',')]
    return 'last.ckpt' if s == 'last' else f'{s}.ckpt'

def create_rectangle_mask(height, width):
    mask = np.ones((height, width))
    up_left_corner = (width // 4, height // 4)
    down_right_corner = (width - up_left_corner[0] - 1, height - up_left_corner[1] - 1)
    cv2.rectangle(mask, up_left_corner, down_right_corner, (0, 0, 0), thickness=cv2.FILLED)
    return mask

def need_drop(tag):
    for rule in DROP_RULES:
        if rule.search(tag):
            return True
    return False

def get_group_and_title(tag):
    for rule in GROUPING_RULES:
        match = rule.search(tag)
        if match is None:
            continue
        return (match.group('group'), match.group('title'))
    return (None, None)

def find_best_checkpoint(model_list, models_dir):
    with open(model_list) as f:
        models = [m.strip() for m in f.readlines()]
    with open(f'{model_list}_best', 'w') as f:
        for model in models:
            print(model)
            best_f1 = 0
            best_epoch = 0
            best_step = 0
            with open(os.path.join(models_dir, model, 'train.log')) as fm:
                lines = fm.readlines()
                for line_index in range(len(lines)):
                    line = lines[line_index]
                    if 'Validation metrics after epoch' in line:
                        sharp_index = line.index('#')
                        cur_ep = line[sharp_index + 1:]
                        comma_index = cur_ep.index(',')
                        cur_ep = int(cur_ep[:comma_index])
                        total_index = line.index('total ')
                        step = int(line[total_index:].split()[1].strip())
                        total_line = lines[line_index + 5]
                        if not total_line.startswith('total'):
                            continue
                        words = total_line.strip().split()
                        f1 = float(words[-1])
                        print(f'\tEpoch: {cur_ep}, f1={f1}')
                        if f1 > best_f1:
                            best_f1 = f1
                            best_epoch = cur_ep
                            best_step = step
            f.write(f'{model}\t{best_epoch}\t{best_step}\t{best_f1}\n')

class FFC_BN_ACT(nn.Module):

    def __init__(self, in_channels, out_channels, kernel_size, ratio_gin, ratio_gout, stride=1, padding=0, dilation=1, groups=1, bias=False, norm_layer=nn.BatchNorm2d, activation_layer=nn.Identity, padding_type='reflect', enable_lfu=True, **kwargs):
        super(FFC_BN_ACT, self).__init__()
        self.ffc = FFC(in_channels, out_channels, kernel_size, ratio_gin, ratio_gout, stride, padding, dilation, groups, bias, enable_lfu, padding_type=padding_type, **kwargs)
        lnorm = nn.Identity if ratio_gout == 1 else norm_layer
        gnorm = nn.Identity if ratio_gout == 0 else norm_layer
        global_channels = int(out_channels * ratio_gout)
        self.bn_l = lnorm(out_channels - global_channels)
        self.bn_g = gnorm(global_channels)
        lact = nn.Identity if ratio_gout == 1 else activation_layer
        gact = nn.Identity if ratio_gout == 0 else activation_layer
        self.act_l = lact(inplace=True)
        self.act_g = gact(inplace=True)

    def forward(self, x):
        x_l, x_g = self.ffc(x)
        x_l = self.act_l(self.bn_l(x_l))
        x_g = self.act_g(self.bn_g(x_g))
        return (x_l, x_g)

def __init__(self, in_channels, out_channels, kernel_size, ratio_gin, ratio_gout, stride=1, padding=0, dilation=1, groups=1, bias=False, norm_layer=nn.BatchNorm2d, activation_layer=nn.Identity, padding_type='reflect', enable_lfu=True, **kwargs):
    super(FFC_BN_ACT, self).__init__()
    self.ffc = FFC(in_channels, out_channels, kernel_size, ratio_gin, ratio_gout, stride, padding, dilation, groups, bias, enable_lfu, padding_type=padding_type, **kwargs)
    lnorm = nn.Identity if ratio_gout == 1 else norm_layer
    gnorm = nn.Identity if ratio_gout == 0 else norm_layer
    global_channels = int(out_channels * ratio_gout)
    self.bn_l = lnorm(out_channels - global_channels)
    self.bn_g = gnorm(global_channels)
    lact = nn.Identity if ratio_gout == 1 else activation_layer
    gact = nn.Identity if ratio_gout == 0 else activation_layer
    self.act_l = lact(inplace=True)
    self.act_g = gact(inplace=True)

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

def _clean(self):
    self.up, self.down, self.left, self.right = (0, 0, 0, 0)
    self.mask = np.empty((0, 0))

def odd_to_even(image):
    """
  To facilitate 2x2 downsampling segmentation, change an odd sized image into an even sized one.
  Works by mirroring the starting 1 pixel edge of the image on odd shaped sides.

  e.g. turn a 3x3x5 image into a 4x4x5 (the x and y are what are getting downsampled)
  
  For example: [ 3, 2, 4 ] => [ 3, 3, 2, 4 ] which is now easy to downsample.

  """
    shape = np.array(image.shape)
    offset = (shape % 2)[:2]
    if not np.any(offset):
        return image
    oddshape = image.shape[:2] + offset
    oddshape = np.append(oddshape, shape[2:])
    oddshape = oddshape.astype(int)
    newimg = np.empty(shape=oddshape, dtype=image.dtype)
    ox, oy = offset
    sx, sy = oddshape
    newimg[0, 0] = image[0, 0]
    newimg[ox:sx, 0] = image[:, 0]
    newimg[0, oy:sy] = image[0, :]
    return newimg

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

def test_stippled_countless2d():
    a = np.array([[1, 2], [3, 4]]).reshape((2, 2, 1, 1))
    b = np.array([[0, 2], [3, 4]]).reshape((2, 2, 1, 1))
    c = np.array([[1, 0], [3, 4]]).reshape((2, 2, 1, 1))
    d = np.array([[1, 2], [0, 4]]).reshape((2, 2, 1, 1))
    e = np.array([[1, 2], [3, 0]]).reshape((2, 2, 1, 1))
    f = np.array([[0, 0], [3, 4]]).reshape((2, 2, 1, 1))
    g = np.array([[0, 2], [0, 4]]).reshape((2, 2, 1, 1))
    h = np.array([[0, 2], [3, 0]]).reshape((2, 2, 1, 1))
    i = np.array([[1, 0], [0, 4]]).reshape((2, 2, 1, 1))
    j = np.array([[1, 2], [0, 0]]).reshape((2, 2, 1, 1))
    k = np.array([[1, 0], [3, 0]]).reshape((2, 2, 1, 1))
    l = np.array([[1, 0], [0, 0]]).reshape((2, 2, 1, 1))
    m = np.array([[0, 2], [0, 0]]).reshape((2, 2, 1, 1))
    n = np.array([[0, 0], [3, 0]]).reshape((2, 2, 1, 1))
    o = np.array([[0, 0], [0, 4]]).reshape((2, 2, 1, 1))
    z = np.array([[0, 0], [0, 0]]).reshape((2, 2, 1, 1))
    test = countless2d.stippled_countless
    assert test(a) == [[[[4]]]]
    assert test(b) == [[[[4]]]]
    assert test(c) == [[[[4]]]]
    assert test(d) == [[[[4]]]]
    assert test(e) == [[[[1]]]]
    assert test(f) == [[[[4]]]]
    assert test(g) == [[[[4]]]]
    assert test(h) == [[[[2]]]]
    assert test(i) == [[[[4]]]]
    assert test(j) == [[[[1]]]]
    assert test(k) == [[[[1]]]]
    assert test(l) == [[[[1]]]]
    assert test(m) == [[[[2]]]]
    assert test(n) == [[[[3]]]]
    assert test(o) == [[[[4]]]]
    assert test(z) == [[[[0]]]]
    bc = np.array([[0, 2], [2, 4]]).reshape((2, 2, 1, 1))
    bd = np.array([[0, 2], [3, 2]]).reshape((2, 2, 1, 1))
    cd = np.array([[0, 2], [3, 3]]).reshape((2, 2, 1, 1))
    assert test(bc) == [[[[2]]]]
    assert test(bd) == [[[[2]]]]
    assert test(cd) == [[[[3]]]]
    ab = np.array([[1, 1], [0, 4]]).reshape((2, 2, 1, 1))
    ac = np.array([[1, 2], [1, 0]]).reshape((2, 2, 1, 1))
    ad = np.array([[1, 0], [3, 1]]).reshape((2, 2, 1, 1))
    assert test(ab) == [[[[1]]]]
    assert test(ac) == [[[[1]]]]
    assert test(ad) == [[[[1]]]]

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

class RandomIrregularMaskGenerator:

    def __init__(self, max_angle=4, max_len=60, max_width=20, min_times=0, max_times=10, ramp_kwargs=None, draw_method=DrawMethod.LINE):
        self.max_angle = max_angle
        self.max_len = max_len
        self.max_width = max_width
        self.min_times = min_times
        self.max_times = max_times
        self.draw_method = draw_method
        self.ramp = LinearRamp(**ramp_kwargs) if ramp_kwargs is not None else None

    def __call__(self, img, iter_i=None, raw_image=None):
        coef = self.ramp(iter_i) if self.ramp is not None and iter_i is not None else 1
        cur_max_len = int(max(1, self.max_len * coef))
        cur_max_width = int(max(1, self.max_width * coef))
        cur_max_times = int(self.min_times + 1 + (self.max_times - self.min_times) * coef)
        return make_random_irregular_mask(img.shape[1:], max_angle=self.max_angle, max_len=cur_max_len, max_width=cur_max_width, min_times=self.min_times, max_times=cur_max_times, draw_method=self.draw_method)

def __call__(self, img, iter_i=None, raw_image=None):
    coef = self.ramp(iter_i) if self.ramp is not None and iter_i is not None else 1
    cur_max_len = int(max(1, self.max_len * coef))
    cur_max_width = int(max(1, self.max_width * coef))
    cur_max_times = int(self.min_times + 1 + (self.max_times - self.min_times) * coef)
    return make_random_irregular_mask(img.shape[1:], max_angle=self.max_angle, max_len=cur_max_len, max_width=cur_max_width, min_times=self.min_times, max_times=cur_max_times, draw_method=self.draw_method)

class RandomRectangleMaskGenerator:

    def __init__(self, margin=10, bbox_min_size=30, bbox_max_size=100, min_times=0, max_times=3, ramp_kwargs=None):
        self.margin = margin
        self.bbox_min_size = bbox_min_size
        self.bbox_max_size = bbox_max_size
        self.min_times = min_times
        self.max_times = max_times
        self.ramp = LinearRamp(**ramp_kwargs) if ramp_kwargs is not None else None

    def __call__(self, img, iter_i=None, raw_image=None):
        coef = self.ramp(iter_i) if self.ramp is not None and iter_i is not None else 1
        cur_bbox_max_size = int(self.bbox_min_size + 1 + (self.bbox_max_size - self.bbox_min_size) * coef)
        cur_max_times = int(self.min_times + (self.max_times - self.min_times) * coef)
        return make_random_rectangle_mask(img.shape[1:], margin=self.margin, bbox_min_size=self.bbox_min_size, bbox_max_size=cur_bbox_max_size, min_times=self.min_times, max_times=cur_max_times)

def __call__(self, img, iter_i=None, raw_image=None):
    coef = self.ramp(iter_i) if self.ramp is not None and iter_i is not None else 1
    cur_bbox_max_size = int(self.bbox_min_size + 1 + (self.bbox_max_size - self.bbox_min_size) * coef)
    cur_max_times = int(self.min_times + (self.max_times - self.min_times) * coef)
    return make_random_rectangle_mask(img.shape[1:], margin=self.margin, bbox_min_size=self.bbox_min_size, bbox_max_size=cur_bbox_max_size, min_times=self.min_times, max_times=cur_max_times)

class OutpaintingMaskGenerator:

    def __init__(self, min_padding_percent: float=0.04, max_padding_percent: int=0.25, left_padding_prob: float=0.5, top_padding_prob: float=0.5, right_padding_prob: float=0.5, bottom_padding_prob: float=0.5, is_fixed_randomness: bool=False):
        """
        is_fixed_randomness - get identical paddings for the same image if args are the same
        """
        self.min_padding_percent = min_padding_percent
        self.max_padding_percent = max_padding_percent
        self.probs = [left_padding_prob, top_padding_prob, right_padding_prob, bottom_padding_prob]
        self.is_fixed_randomness = is_fixed_randomness
        assert self.min_padding_percent <= self.max_padding_percent
        assert self.max_padding_percent > 0
        assert len([x for x in [self.min_padding_percent, self.max_padding_percent] if x >= 0 and x <= 1]) == 2, f'Padding percentage should be in [0,1]'
        assert sum(self.probs) > 0, f'At least one of the padding probs should be greater than 0 - {self.probs}'
        assert len([x for x in self.probs if x >= 0 and x <= 1]) == 4, f'At least one of padding probs is not in [0,1] - {self.probs}'
        if len([x for x in self.probs if x > 0]) == 1:
            LOGGER.warning(f'Only one padding prob is greater than zero - {self.probs}. That means that the outpainting masks will be always on the same side')

    def apply_padding(self, mask, coord):
        mask[int(coord[0][0] * self.img_h):int(coord[1][0] * self.img_h), int(coord[0][1] * self.img_w):int(coord[1][1] * self.img_w)] = 1
        return mask

    def get_padding(self, size):
        n1 = int(self.min_padding_percent * size)
        n2 = int(self.max_padding_percent * size)
        return self.rnd.randint(n1, n2) / size

    @staticmethod
    def _img2rs(img):
        arr = np.ascontiguousarray(img.astype(np.uint8))
        str_hash = hashlib.sha1(arr).hexdigest()
        res = hash(str_hash) % 2 ** 32
        return res

    def __call__(self, img, iter_i=None, raw_image=None):
        c, self.img_h, self.img_w = img.shape
        mask = np.zeros((self.img_h, self.img_w), np.float32)
        at_least_one_mask_applied = False
        if self.is_fixed_randomness:
            assert raw_image is not None, f'Cant calculate hash on raw_image=None'
            rs = self._img2rs(raw_image)
            self.rnd = np.random.RandomState(rs)
        else:
            self.rnd = np.random
        coords = [[(0, 0), (1, self.get_padding(size=self.img_h))], [(0, 0), (self.get_padding(size=self.img_w), 1)], [(0, 1 - self.get_padding(size=self.img_h)), (1, 1)], [(1 - self.get_padding(size=self.img_w), 0), (1, 1)]]
        for pp, coord in zip(self.probs, coords):
            if self.rnd.random() < pp:
                at_least_one_mask_applied = True
                mask = self.apply_padding(mask=mask, coord=coord)
        if not at_least_one_mask_applied:
            idx = self.rnd.choice(range(len(coords)), p=np.array(self.probs) / sum(self.probs))
            mask = self.apply_padding(mask=mask, coord=coords[idx])
        return mask[None, ...]

def apply_padding(self, mask, coord):
    mask[int(coord[0][0] * self.img_h):int(coord[1][0] * self.img_h), int(coord[0][1] * self.img_w):int(coord[1][1] * self.img_w)] = 1
    return mask

def get_padding(self, size):
    n1 = int(self.min_padding_percent * size)
    n2 = int(self.max_padding_percent * size)
    return self.rnd.randint(n1, n2) / size

class FFC_BN_ACT(nn.Module):

    def __init__(self, in_channels, out_channels, kernel_size, ratio_gin, ratio_gout, stride=1, padding=0, dilation=1, groups=1, bias=False, norm_layer=nn.BatchNorm2d, activation_layer=nn.Identity, padding_type='reflect', enable_lfu=True, **kwargs):
        super(FFC_BN_ACT, self).__init__()
        self.ffc = FFC(in_channels, out_channels, kernel_size, ratio_gin, ratio_gout, stride, padding, dilation, groups, bias, enable_lfu, padding_type=padding_type, **kwargs)
        lnorm = nn.Identity if ratio_gout == 1 else norm_layer
        gnorm = nn.Identity if ratio_gout == 0 else norm_layer
        global_channels = int(out_channels * ratio_gout)
        self.bn_l = lnorm(out_channels - global_channels)
        self.bn_g = gnorm(global_channels)
        lact = nn.Identity if ratio_gout == 1 else activation_layer
        gact = nn.Identity if ratio_gout == 0 else activation_layer
        self.act_l = lact(inplace=True)
        self.act_g = gact(inplace=True)

    def forward(self, x):
        x_l, x_g = self.ffc(x)
        x_l = self.act_l(self.bn_l(x_l))
        x_g = self.act_g(self.bn_g(x_g))
        return (x_l, x_g)

def __init__(self, in_channels, out_channels, kernel_size, ratio_gin, ratio_gout, stride=1, padding=0, dilation=1, groups=1, bias=False, norm_layer=nn.BatchNorm2d, activation_layer=nn.Identity, padding_type='reflect', enable_lfu=True, **kwargs):
    super(FFC_BN_ACT, self).__init__()
    self.ffc = FFC(in_channels, out_channels, kernel_size, ratio_gin, ratio_gout, stride, padding, dilation, groups, bias, enable_lfu, padding_type=padding_type, **kwargs)
    lnorm = nn.Identity if ratio_gout == 1 else norm_layer
    gnorm = nn.Identity if ratio_gout == 0 else norm_layer
    global_channels = int(out_channels * ratio_gout)
    self.bn_l = lnorm(out_channels - global_channels)
    self.bn_g = gnorm(global_channels)
    lact = nn.Identity if ratio_gout == 1 else activation_layer
    gact = nn.Identity if ratio_gout == 0 else activation_layer
    self.act_l = lact(inplace=True)
    self.act_g = gact(inplace=True)

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

def _clean(self):
    self.up, self.down, self.left, self.right = (0, 0, 0, 0)
    self.mask = np.empty((0, 0))

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

def test_stippled_countless2d():
    a = np.array([[1, 2], [3, 4]]).reshape((2, 2, 1, 1))
    b = np.array([[0, 2], [3, 4]]).reshape((2, 2, 1, 1))
    c = np.array([[1, 0], [3, 4]]).reshape((2, 2, 1, 1))
    d = np.array([[1, 2], [0, 4]]).reshape((2, 2, 1, 1))
    e = np.array([[1, 2], [3, 0]]).reshape((2, 2, 1, 1))
    f = np.array([[0, 0], [3, 4]]).reshape((2, 2, 1, 1))
    g = np.array([[0, 2], [0, 4]]).reshape((2, 2, 1, 1))
    h = np.array([[0, 2], [3, 0]]).reshape((2, 2, 1, 1))
    i = np.array([[1, 0], [0, 4]]).reshape((2, 2, 1, 1))
    j = np.array([[1, 2], [0, 0]]).reshape((2, 2, 1, 1))
    k = np.array([[1, 0], [3, 0]]).reshape((2, 2, 1, 1))
    l = np.array([[1, 0], [0, 0]]).reshape((2, 2, 1, 1))
    m = np.array([[0, 2], [0, 0]]).reshape((2, 2, 1, 1))
    n = np.array([[0, 0], [3, 0]]).reshape((2, 2, 1, 1))
    o = np.array([[0, 0], [0, 4]]).reshape((2, 2, 1, 1))
    z = np.array([[0, 0], [0, 0]]).reshape((2, 2, 1, 1))
    test = countless2d.stippled_countless
    assert test(a) == [[[[4]]]]
    assert test(b) == [[[[4]]]]
    assert test(c) == [[[[4]]]]
    assert test(d) == [[[[4]]]]
    assert test(e) == [[[[1]]]]
    assert test(f) == [[[[4]]]]
    assert test(g) == [[[[4]]]]
    assert test(h) == [[[[2]]]]
    assert test(i) == [[[[4]]]]
    assert test(j) == [[[[1]]]]
    assert test(k) == [[[[1]]]]
    assert test(l) == [[[[1]]]]
    assert test(m) == [[[[2]]]]
    assert test(n) == [[[[3]]]]
    assert test(o) == [[[[4]]]]
    assert test(z) == [[[[0]]]]
    bc = np.array([[0, 2], [2, 4]]).reshape((2, 2, 1, 1))
    bd = np.array([[0, 2], [3, 2]]).reshape((2, 2, 1, 1))
    cd = np.array([[0, 2], [3, 3]]).reshape((2, 2, 1, 1))
    assert test(bc) == [[[[2]]]]
    assert test(bd) == [[[[2]]]]
    assert test(cd) == [[[[3]]]]
    ab = np.array([[1, 1], [0, 4]]).reshape((2, 2, 1, 1))
    ac = np.array([[1, 2], [1, 0]]).reshape((2, 2, 1, 1))
    ad = np.array([[1, 0], [3, 1]]).reshape((2, 2, 1, 1))
    assert test(ab) == [[[[1]]]]
    assert test(ac) == [[[[1]]]]
    assert test(ad) == [[[[1]]]]

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

def jpeg4py_loader(path):
    """ Image reading using jpeg4py https://github.com/ajkxyz/jpeg4py"""
    try:
        return jpeg4py.JPEG(path).decode()
    except Exception as e:
        print('ERROR: Could not read image "{}"'.format(path))
        print(e)
        return None

def jpeg4py_loader_w_failsafe(path):
    """ Image reading using jpeg4py https://github.com/ajkxyz/jpeg4py"""
    try:
        return jpeg4py.JPEG(path).decode()
    except:
        try:
            im = cv.imread(path, cv.IMREAD_COLOR)
            return cv.cvtColor(im, cv.COLOR_BGR2RGB)
        except Exception as e:
            print('ERROR: Could not read image "{}"'.format(path))
            print(e)
            return None

def _run(command):
    return subprocess.check_output(command, cwd=cwd).decode('ascii').strip()

def decode_img(lmdb_fname, key_name):
    handle = get_lmdb_handle(lmdb_fname)
    binfile = handle.get(key_name.encode())
    if binfile is None:
        print('Illegal data detected. %s %s' % (lmdb_fname, key_name))
    s = np.frombuffer(binfile, np.uint8)
    x = cv2.cvtColor(cv2.imdecode(s, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
    return x

def decode_str(lmdb_fname, key_name):
    handle = get_lmdb_handle(lmdb_fname)
    binfile = handle.get(key_name.encode())
    string = binfile.decode()
    return string

def decode_json(lmdb_fname, key_name):
    return json.loads(decode_str(lmdb_fname, key_name))

def hann2d(sz: torch.Tensor, centered=True) -> torch.Tensor:
    """2D cosine window."""
    return hann1d(sz[0].item(), centered).reshape(1, 1, -1, 1) * hann1d(sz[1].item(), centered).reshape(1, 1, 1, -1)

def hann2d_bias(sz: torch.Tensor, ctr_point: torch.Tensor, centered=True) -> torch.Tensor:
    """2D cosine window."""
    distance = torch.stack([ctr_point, sz - ctr_point], dim=0)
    max_distance, _ = distance.max(dim=0)
    hann1d_x = hann1d(max_distance[0].item() * 2, centered)
    hann1d_x = hann1d_x[max_distance[0] - distance[0, 0]:max_distance[0] + distance[1, 0]]
    hann1d_y = hann1d(max_distance[1].item() * 2, centered)
    hann1d_y = hann1d_y[max_distance[1] - distance[0, 1]:max_distance[1] + distance[1, 1]]
    return hann1d_y.reshape(1, 1, -1, 1) * hann1d_x.reshape(1, 1, 1, -1)

def hann2d_clipped(sz: torch.Tensor, effective_sz: torch.Tensor, centered=True) -> torch.Tensor:
    """1D clipped cosine window."""
    effective_sz += (effective_sz - sz) % 2
    effective_window = hann1d(effective_sz[0].item(), True).reshape(1, 1, -1, 1) * hann1d(effective_sz[1].item(), True).reshape(1, 1, 1, -1)
    pad = (sz - effective_sz) // 2
    window = F.pad(effective_window, (pad[1].item(), pad[1].item(), pad[0].item(), pad[0].item()), 'replicate')
    if centered:
        return window
    else:
        mid = (sz / 2).int()
        window_shift_lr = torch.cat((window[:, :, :, mid[1]:], window[:, :, :, :mid[1]]), 3)
        return torch.cat((window_shift_lr[:, :, mid[0]:, :], window_shift_lr[:, :, :mid[0], :]), 2)

def label_function(sz: torch.Tensor, sigma: torch.Tensor):
    return gauss_fourier(sz[0].item(), sigma[0].item()).reshape(1, 1, -1, 1) * gauss_fourier(sz[1].item(), sigma[1].item(), True).reshape(1, 1, 1, -1)

def label_function_spatial(sz: torch.Tensor, sigma: torch.Tensor, center: torch.Tensor=torch.zeros(2), end_pad: torch.Tensor=torch.zeros(2)):
    """The origin is in the middle of the image."""
    return gauss_spatial(sz[0].item(), sigma[0].item(), center[0], end_pad[0].item()).reshape(1, 1, -1, 1) * gauss_spatial(sz[1].item(), sigma[1].item(), center[1], end_pad[1].item()).reshape(1, 1, 1, -1)

def load_str(path):
    with open(path, 'r') as f:
        text_str = f.readline().strip().lower()
    return text_str

def recover_image(tokens, H, W, Hp, Wp, patch_size):
    image = tokens.reshape(Hp, Wp, patch_size, patch_size, 3).swapaxes(1, 2).reshape(H, W, 3)
    return image

def gen_visualization(image, mask_indices, patch_size=16):
    num_stages = len(mask_indices)
    for i in range(1, num_stages):
        mask_indices[i] = np.concatenate([mask_indices[i - 1], mask_indices[i]], axis=1)
    image = np.asarray(image)
    H, W, C = image.shape
    Hp, Wp = (H // patch_size, W // patch_size)
    image_tokens = image.reshape(Hp, patch_size, Wp, patch_size, 3).swapaxes(1, 2).reshape(Hp * Wp, patch_size, patch_size, 3)
    stages = [recover_image(gen_masked_tokens(image_tokens, mask_indices[i]), H, W, Hp, Wp, patch_size) for i in range(num_stages)]
    imgs = [image] + stages
    imgs = [pad_img(img) for img in imgs]
    viz = np.concatenate(imgs, axis=1)
    return viz

class PreprocessorX_onnx(object):

    def __init__(self):
        self.mean = np.array([0.485, 0.456, 0.406]).reshape((1, 3, 1, 1))
        self.std = np.array([0.229, 0.224, 0.225]).reshape((1, 3, 1, 1))

    def process(self, img_arr: np.ndarray, amask_arr: np.ndarray):
        """img_arr: (H,W,3), amask_arr: (H,W)"""
        img_arr_4d = img_arr[np.newaxis, :, :, :].transpose(0, 3, 1, 2)
        img_arr_4d = (img_arr_4d / 255.0 - self.mean) / self.std
        amask_arr_3d = amask_arr[np.newaxis, :, :]
        return (img_arr_4d.astype(np.float32), amask_arr_3d.astype(np.bool))

def __init__(self):
    self.mean = np.array([0.485, 0.456, 0.406]).reshape((1, 3, 1, 1))
    self.std = np.array([0.229, 0.224, 0.225]).reshape((1, 3, 1, 1))

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

def video2seq(video_path, point_coords, point_labels, sam_model_type, sam_ckpt, output_dir):
    video_name, _ = os.path.splitext(video_path.split('/')[-1])
    frames_path = f'{output_dir}/{video_name}/original_frames'
    fps, first_frame = video2frames(video_path, frames_path)
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    first_frame = cv2.cvtColor(first_frame, cv2.COLOR_BGR2RGB)
    masks, scores, _ = predict_masks_with_sam(first_frame, [point_coords], point_labels, model_type=sam_model_type, ckpt_p=sam_ckpt, device=device)
    mask = masks[np.argmax(scores)][:, :, None].astype(np.uint8) * 255
    mask_loc = np.where(mask > 0)
    x1, x2 = (np.min(mask_loc[1]), np.max(mask_loc[1]))
    y1, y2 = (np.min(mask_loc[0]), np.max(mask_loc[0]))
    x1, y1, x2, y2 = list(map(lambda x: int(x), [x1, y1, x2, y2]))
    gt_rect = np.array([x1, y1, x2 - x1, y2 - y1]).astype(np.float32).reshape(-1, 4)
    frames_list = [os.path.join(frames_path, frame) for frame in os.listdir(frames_path) if frame.endswith('.jpg')]
    return (Sequence(video_name, frames_list, 'inpaint-anything', gt_rect.reshape(-1, 4)), fps)

def checkpoint_filter_fn(state_dict, model):
    """ convert patch embedding weight from manual patchify + linear proj to conv"""
    out_dict = {}
    if 'model' in state_dict:
        state_dict = state_dict['model']
    for k, v in state_dict.items():
        if 'patch_embed.proj.weight' in k and len(v.shape) < 4:
            O, I, H, W = model.patch_embed.proj.weight.shape
            v = v.reshape(O, -1, H, W)
        elif k == 'pos_embed' and v.shape != model.pos_embed.shape:
            v = resize_pos_embed(v, model.pos_embed, getattr(model, 'num_tokens', 1), model.patch_embed.grid_size)
        out_dict[k] = v
    return out_dict

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

def forward(self, x):
    w = self.weight.reshape(1, -1, 1, 1)
    b = self.bias.reshape(1, -1, 1, 1)
    rv = self.running_var.reshape(1, -1, 1, 1)
    rm = self.running_mean.reshape(1, -1, 1, 1)
    eps = 1e-05
    scale = w * (rv + eps).rsqrt()
    bias = b - rm * scale
    return x * scale + bias

def get_custom_cond(mode):
    dest = 'data/example_conditioning'
    if mode == 'superresolution':
        uploaded_img = files.upload()
        filename = next(iter(uploaded_img))
        name, filetype = filename.split('.')
        os.rename(f'{filename}', f'{dest}/{mode}/custom_{name}.{filetype}')
    elif mode == 'text_conditional':
        w = widgets.Text(value='A cake with cream!', disabled=True)
        display(w)
        with open(f'{dest}/{mode}/custom_{w.value[:20]}.txt', 'w') as f:
            f.write(w.value)
    elif mode == 'class_conditional':
        w = widgets.IntSlider(min=0, max=1000)
        display(w)
        with open(f'{dest}/{mode}/custom.txt', 'w') as f:
            f.write(w.value)
    else:
        raise NotImplementedError(f'cond not implemented for mode{mode}')

def visualize_cond_img(path):
    display(ipyimg(filename=path))

def chunk(it, size):
    it = iter(it)
    return iter(lambda: tuple(islice(it, size)), ())

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

def __call__(self, x, n):
    return self.search(x, n)

def group_dict_by_key(cond, d):
    return_val = [dict(), dict()]
    for key in d.keys():
        match = bool(cond(key))
        ind = int(not match)
        return_val[ind][key] = d[key]
    return (*return_val,)

def string_begins_with(prefix, str):
    return str.startswith(prefix)

def group_by_key_prefix(prefix, d):
    return group_dict_by_key(partial(string_begins_with, prefix), d)

def groupby_prefix_and_trim(prefix, d):
    kwargs_with_prefix, kwargs = group_dict_by_key(partial(string_begins_with, prefix), d)
    kwargs_without_prefix = dict(map(lambda x: (x[0][len(prefix):], x[1]), tuple(kwargs_with_prefix.items())))
    return (kwargs_without_prefix, kwargs)

def random_crop(lq, hq, sf=4, lq_patchsize=64):
    h, w = lq.shape[:2]
    rnd_h = random.randint(0, h - lq_patchsize)
    rnd_w = random.randint(0, w - lq_patchsize)
    lq = lq[rnd_h:rnd_h + lq_patchsize, rnd_w:rnd_w + lq_patchsize, :]
    rnd_h_H, rnd_w_H = (int(rnd_h * sf), int(rnd_w * sf))
    hq = hq[rnd_h_H:rnd_h_H + lq_patchsize * sf, rnd_w_H:rnd_w_H + lq_patchsize * sf, :]
    return (lq, hq)

def random_crop(lq, hq, sf=4, lq_patchsize=64):
    h, w = lq.shape[:2]
    rnd_h = random.randint(0, h - lq_patchsize)
    rnd_w = random.randint(0, w - lq_patchsize)
    lq = lq[rnd_h:rnd_h + lq_patchsize, rnd_w:rnd_w + lq_patchsize, :]
    rnd_h_H, rnd_w_H = (int(rnd_h * sf), int(rnd_w * sf))
    hq = hq[rnd_h_H:rnd_h_H + lq_patchsize * sf, rnd_w_H:rnd_w_H + lq_patchsize * sf, :]
    return (lq, hq)

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

@torch.no_grad()
def encode_with_pretrained(self, x):
    c = self.pretrained_model.encode(x)
    if isinstance(c, DiagonalGaussianDistribution):
        c = c.mode()
    return c

def extract_into_tensor(a, t, x_shape):
    b, *_ = t.shape
    out = a.gather(-1, t)
    return out.reshape(b, *(1,) * (len(x_shape) - 1))

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

def forward(self, input, sample_posterior=True):
    posterior = self.encode(input)
    if sample_posterior:
        z = posterior.sample()
    else:
        z = posterior.mode()
    dec = self.decode(z)
    return (dec, posterior)

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

def parse_config(path_to_json):
    with open(path_to_json) as f:
        data = json.load(f)
        args = Struct(**data)
    return args

def extract_python_code(s):
    pattern = '```python(.*?)```'
    match = re.search(pattern, s, re.DOTALL)
    return match.group(1).strip()

def savitzky_golay_2d(trajectory, window_size=5, polynomial_order=2):
    x_smooth = savgol_filter(trajectory[:, 0], window_size, polynomial_order)
    y_smooth = savgol_filter(trajectory[:, 1], window_size, polynomial_order)
    return np.column_stack((x_smooth, y_smooth))

