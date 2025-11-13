# Cluster 1

def get_git_hash():

    def _minimal_ext_cmd(cmd):
        env = {}
        for k in ['SYSTEMROOT', 'PATH', 'HOME']:
            v = os.environ.get(k)
            if v is not None:
                env[k] = v
        env['LANGUAGE'] = 'C'
        env['LANG'] = 'C'
        env['LC_ALL'] = 'C'
        out = subprocess.Popen(cmd, stdout=subprocess.PIPE, env=env).communicate()[0]
        return out
    try:
        out = _minimal_ext_cmd(['git', 'rev-parse', 'HEAD'])
        sha = out.strip().decode('ascii')
    except OSError:
        sha = 'unknown'
    return sha

def get_requirements(filename='requirements.txt'):
    return []
    here = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(here, filename), 'r') as f:
        requires = [line.replace('\n', '') for line in f.readlines()]
    return requires

def load_img(filepath):
    return cv2.cvtColor(cv2.imread(filepath), cv2.COLOR_BGR2RGB)

def save_img(filepath, img):
    cv2.imwrite(filepath, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))

def load_img(filepath):
    return cv2.cvtColor(cv2.imread(filepath), cv2.COLOR_BGR2RGB)

def save_img(filepath, img):
    cv2.imwrite(filepath, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))

def load_gray_img(filepath):
    return np.expand_dims(cv2.imread(filepath, cv2.IMREAD_GRAYSCALE), axis=2)

def save_gray_img(filepath, img):
    cv2.imwrite(filepath, img)

def _totensor(img, bgr2rgb, float32):
    if img.shape[2] == 3 and bgr2rgb:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = torch.from_numpy(img.transpose(2, 0, 1))
    if float32:
        img = img.float()
    return img

def imwrite(img, file_path, params=None, auto_mkdir=True):
    """Write image to file.

    Args:
        img (ndarray): Image array to be written.
        file_path (str): Image file path.
        params (None or list): Same as opencv's :func:`imwrite` interface.
        auto_mkdir (bool): If the parent folder of `file_path` does not exist,
            whether to create it automatically.

    Returns:
        bool: Successful or not.
    """
    if auto_mkdir:
        dir_name = os.path.abspath(os.path.dirname(file_path))
        os.makedirs(dir_name, exist_ok=True)
    return cv2.imwrite(file_path, img, params)

class FaceRestorationHelper(object):
    """Helper for the face restoration pipeline."""

    def __init__(self, upscale_factor, face_size=512):
        self.upscale_factor = upscale_factor
        self.face_size = (face_size, face_size)
        self.face_template = np.array([[686.77227723, 488.62376238], [586.77227723, 493.59405941], [337.91089109, 488.38613861], [437.95049505, 493.51485149], [513.58415842, 678.5049505]])
        self.face_template = self.face_template / (1024 // face_size)
        self.similarity_trans = trans.SimilarityTransform()
        self.all_landmarks_5 = []
        self.all_landmarks_68 = []
        self.affine_matrices = []
        self.inverse_affine_matrices = []
        self.cropped_faces = []
        self.restored_faces = []
        self.save_png = True

    def init_dlib(self, detection_path, landmark5_path, landmark68_path):
        """Initialize the dlib detectors and predictors."""
        self.face_detector = dlib.cnn_face_detection_model_v1(detection_path)
        self.shape_predictor_5 = dlib.shape_predictor(landmark5_path)
        self.shape_predictor_68 = dlib.shape_predictor(landmark68_path)

    def free_dlib_gpu_memory(self):
        del self.face_detector
        del self.shape_predictor_5
        del self.shape_predictor_68

    def read_input_image(self, img_path):
        self.input_img = dlib.load_rgb_image(img_path)

    def detect_faces(self, img_path, upsample_num_times=1, only_keep_largest=False):
        """
        Args:
            img_path (str): Image path.
            upsample_num_times (int): Upsamples the image before running the
                face detector

        Returns:
            int: Number of detected faces.
        """
        self.read_input_image(img_path)
        det_faces = self.face_detector(self.input_img, upsample_num_times)
        if len(det_faces) == 0:
            print('No face detected. Try to increase upsample_num_times.')
        elif only_keep_largest:
            print('Detect several faces and only keep the largest.')
            face_areas = []
            for i in range(len(det_faces)):
                face_area = (det_faces[i].rect.right() - det_faces[i].rect.left()) * (det_faces[i].rect.bottom() - det_faces[i].rect.top())
                face_areas.append(face_area)
            largest_idx = face_areas.index(max(face_areas))
            self.det_faces = [det_faces[largest_idx]]
        else:
            self.det_faces = det_faces
        return len(self.det_faces)

    def get_face_landmarks_5(self):
        for face in self.det_faces:
            shape = self.shape_predictor_5(self.input_img, face.rect)
            landmark = np.array([[part.x, part.y] for part in shape.parts()])
            self.all_landmarks_5.append(landmark)
        return len(self.all_landmarks_5)

    def get_face_landmarks_68(self):
        """Get 68 densemarks for cropped images.

        Should only have one face at most in the cropped image.
        """
        num_detected_face = 0
        for idx, face in enumerate(self.cropped_faces):
            det_face = self.face_detector(face, 1)
            if len(det_face) == 0:
                print(f'Cannot find faces in cropped image with index {idx}.')
                self.all_landmarks_68.append(None)
            else:
                if len(det_face) > 1:
                    print('Detect several faces in the cropped face. Use the  largest one. Note that it will also cause overlap during paste_faces_to_input_image.')
                    face_areas = []
                    for i in range(len(det_face)):
                        face_area = (det_face[i].rect.right() - det_face[i].rect.left()) * (det_face[i].rect.bottom() - det_face[i].rect.top())
                        face_areas.append(face_area)
                    largest_idx = face_areas.index(max(face_areas))
                    face_rect = det_face[largest_idx].rect
                else:
                    face_rect = det_face[0].rect
                shape = self.shape_predictor_68(face, face_rect)
                landmark = np.array([[part.x, part.y] for part in shape.parts()])
                self.all_landmarks_68.append(landmark)
                num_detected_face += 1
        return num_detected_face

    def warp_crop_faces(self, save_cropped_path=None, save_inverse_affine_path=None):
        """Get affine matrix, warp and cropped faces.

        Also get inverse affine matrix for post-processing.
        """
        for idx, landmark in enumerate(self.all_landmarks_5):
            self.similarity_trans.estimate(landmark, self.face_template)
            affine_matrix = self.similarity_trans.params[0:2, :]
            self.affine_matrices.append(affine_matrix)
            cropped_face = cv2.warpAffine(self.input_img, affine_matrix, self.face_size)
            self.cropped_faces.append(cropped_face)
            if save_cropped_path is not None:
                path, ext = os.path.splitext(save_cropped_path)
                if self.save_png:
                    save_path = f'{path}_{idx:02d}.png'
                else:
                    save_path = f'{path}_{idx:02d}{ext}'
                imwrite(cv2.cvtColor(cropped_face, cv2.COLOR_RGB2BGR), save_path)
            self.similarity_trans.estimate(self.face_template, landmark * self.upscale_factor)
            inverse_affine = self.similarity_trans.params[0:2, :]
            self.inverse_affine_matrices.append(inverse_affine)
            if save_inverse_affine_path is not None:
                path, _ = os.path.splitext(save_inverse_affine_path)
                save_path = f'{path}_{idx:02d}.pth'
                torch.save(inverse_affine, save_path)

    def add_restored_face(self, face):
        self.restored_faces.append(face)

    def paste_faces_to_input_image(self, save_path):
        input_img = cv2.cvtColor(self.input_img, cv2.COLOR_RGB2BGR)
        h, w, _ = input_img.shape
        h_up, w_up = (h * self.upscale_factor, w * self.upscale_factor)
        upsample_img = cv2.resize(input_img, (w_up, h_up))
        assert len(self.restored_faces) == len(self.inverse_affine_matrices), 'length of restored_faces and affine_matrices are different.'
        for restored_face, inverse_affine in zip(self.restored_faces, self.inverse_affine_matrices):
            inv_restored = cv2.warpAffine(restored_face, inverse_affine, (w_up, h_up))
            mask = np.ones((*self.face_size, 3), dtype=np.float32)
            inv_mask = cv2.warpAffine(mask, inverse_affine, (w_up, h_up))
            inv_mask_erosion = cv2.erode(inv_mask, np.ones((2 * self.upscale_factor, 2 * self.upscale_factor), np.uint8))
            inv_restored_remove_border = inv_mask_erosion * inv_restored
            total_face_area = np.sum(inv_mask_erosion) // 3
            w_edge = int(total_face_area ** 0.5) // 20
            erosion_radius = w_edge * 2
            inv_mask_center = cv2.erode(inv_mask_erosion, np.ones((erosion_radius, erosion_radius), np.uint8))
            blur_size = w_edge * 2
            inv_soft_mask = cv2.GaussianBlur(inv_mask_center, (blur_size + 1, blur_size + 1), 0)
            upsample_img = inv_soft_mask * inv_restored_remove_border + (1 - inv_soft_mask) * upsample_img
        if self.save_png:
            save_path = save_path.replace('.jpg', '.png').replace('.jpeg', '.png')
        imwrite(upsample_img.astype(np.uint8), save_path)

    def clean_all(self):
        self.all_landmarks_5 = []
        self.all_landmarks_68 = []
        self.restored_faces = []
        self.affine_matrices = []
        self.cropped_faces = []
        self.inverse_affine_matrices = []

def warp_crop_faces(self, save_cropped_path=None, save_inverse_affine_path=None):
    """Get affine matrix, warp and cropped faces.

        Also get inverse affine matrix for post-processing.
        """
    for idx, landmark in enumerate(self.all_landmarks_5):
        self.similarity_trans.estimate(landmark, self.face_template)
        affine_matrix = self.similarity_trans.params[0:2, :]
        self.affine_matrices.append(affine_matrix)
        cropped_face = cv2.warpAffine(self.input_img, affine_matrix, self.face_size)
        self.cropped_faces.append(cropped_face)
        if save_cropped_path is not None:
            path, ext = os.path.splitext(save_cropped_path)
            if self.save_png:
                save_path = f'{path}_{idx:02d}.png'
            else:
                save_path = f'{path}_{idx:02d}{ext}'
            imwrite(cv2.cvtColor(cropped_face, cv2.COLOR_RGB2BGR), save_path)
        self.similarity_trans.estimate(self.face_template, landmark * self.upscale_factor)
        inverse_affine = self.similarity_trans.params[0:2, :]
        self.inverse_affine_matrices.append(inverse_affine)
        if save_inverse_affine_path is not None:
            path, _ = os.path.splitext(save_inverse_affine_path)
            save_path = f'{path}_{idx:02d}.pth'
            torch.save(inverse_affine, save_path)

def paste_faces_to_input_image(self, save_path):
    input_img = cv2.cvtColor(self.input_img, cv2.COLOR_RGB2BGR)
    h, w, _ = input_img.shape
    h_up, w_up = (h * self.upscale_factor, w * self.upscale_factor)
    upsample_img = cv2.resize(input_img, (w_up, h_up))
    assert len(self.restored_faces) == len(self.inverse_affine_matrices), 'length of restored_faces and affine_matrices are different.'
    for restored_face, inverse_affine in zip(self.restored_faces, self.inverse_affine_matrices):
        inv_restored = cv2.warpAffine(restored_face, inverse_affine, (w_up, h_up))
        mask = np.ones((*self.face_size, 3), dtype=np.float32)
        inv_mask = cv2.warpAffine(mask, inverse_affine, (w_up, h_up))
        inv_mask_erosion = cv2.erode(inv_mask, np.ones((2 * self.upscale_factor, 2 * self.upscale_factor), np.uint8))
        inv_restored_remove_border = inv_mask_erosion * inv_restored
        total_face_area = np.sum(inv_mask_erosion) // 3
        w_edge = int(total_face_area ** 0.5) // 20
        erosion_radius = w_edge * 2
        inv_mask_center = cv2.erode(inv_mask_erosion, np.ones((erosion_radius, erosion_radius), np.uint8))
        blur_size = w_edge * 2
        inv_soft_mask = cv2.GaussianBlur(inv_mask_center, (blur_size + 1, blur_size + 1), 0)
        upsample_img = inv_soft_mask * inv_restored_remove_border + (1 - inv_soft_mask) * upsample_img
    if self.save_png:
        save_path = save_path.replace('.jpg', '.png').replace('.jpeg', '.png')
    imwrite(upsample_img.astype(np.uint8), save_path)

def create_lmdb_for_reds():
    folder_path = './datasets/REDS/val/sharp_300'
    lmdb_path = './datasets/REDS/val/sharp_300.lmdb'
    img_path_list, keys = prepare_keys(folder_path, 'png')
    make_lmdb_from_imgs(folder_path, lmdb_path, img_path_list, keys)
    folder_path = './datasets/REDS/val/blur_300'
    lmdb_path = './datasets/REDS/val/blur_300.lmdb'
    img_path_list, keys = prepare_keys(folder_path, 'jpg')
    make_lmdb_from_imgs(folder_path, lmdb_path, img_path_list, keys)
    folder_path = './datasets/REDS/train/train_sharp'
    lmdb_path = './datasets/REDS/train/train_sharp.lmdb'
    img_path_list, keys = prepare_keys(folder_path, 'png')
    make_lmdb_from_imgs(folder_path, lmdb_path, img_path_list, keys)
    folder_path = './datasets/REDS/train/train_blur_jpeg'
    lmdb_path = './datasets/REDS/train/train_blur_jpeg.lmdb'
    img_path_list, keys = prepare_keys(folder_path, 'jpg')
    make_lmdb_from_imgs(folder_path, lmdb_path, img_path_list, keys)

def create_lmdb_for_gopro():
    folder_path = './datasets/GoPro/train/blur_crops'
    lmdb_path = './datasets/GoPro/train/blur_crops.lmdb'
    img_path_list, keys = prepare_keys(folder_path, 'png')
    make_lmdb_from_imgs(folder_path, lmdb_path, img_path_list, keys)
    folder_path = './datasets/GoPro/train/sharp_crops'
    lmdb_path = './datasets/GoPro/train/sharp_crops.lmdb'
    img_path_list, keys = prepare_keys(folder_path, 'png')
    make_lmdb_from_imgs(folder_path, lmdb_path, img_path_list, keys)
    folder_path = './datasets/GoPro/test/target'
    lmdb_path = './datasets/GoPro/test/target.lmdb'
    img_path_list, keys = prepare_keys(folder_path, 'png')
    make_lmdb_from_imgs(folder_path, lmdb_path, img_path_list, keys)
    folder_path = './datasets/GoPro/test/input'
    lmdb_path = './datasets/GoPro/test/input.lmdb'
    img_path_list, keys = prepare_keys(folder_path, 'png')
    make_lmdb_from_imgs(folder_path, lmdb_path, img_path_list, keys)

def create_lmdb_for_rain13k():
    folder_path = './datasets/Rain13k/train/input'
    lmdb_path = './datasets/Rain13k/train/input.lmdb'
    img_path_list, keys = prepare_keys(folder_path, 'jpg')
    make_lmdb_from_imgs(folder_path, lmdb_path, img_path_list, keys)
    folder_path = './datasets/Rain13k/train/target'
    lmdb_path = './datasets/Rain13k/train/target.lmdb'
    img_path_list, keys = prepare_keys(folder_path, 'jpg')
    make_lmdb_from_imgs(folder_path, lmdb_path, img_path_list, keys)

def create_lmdb_for_SIDD():
    folder_path = './datasets/SIDD/train/input_crops'
    lmdb_path = './datasets/SIDD/train/input_crops.lmdb'
    img_path_list, keys = prepare_keys(folder_path, 'PNG')
    make_lmdb_from_imgs(folder_path, lmdb_path, img_path_list, keys)
    folder_path = './datasets/SIDD/train/gt_crops'
    lmdb_path = './datasets/SIDD/train/gt_crops.lmdb'
    img_path_list, keys = prepare_keys(folder_path, 'PNG')
    make_lmdb_from_imgs(folder_path, lmdb_path, img_path_list, keys)
    folder_path = './datasets/SIDD/val/input_crops'
    lmdb_path = './datasets/SIDD/val/input_crops.lmdb'
    mat_path = './datasets/SIDD/ValidationNoisyBlocksSrgb.mat'
    if not osp.exists(folder_path):
        os.makedirs(folder_path)
    assert osp.exists(mat_path)
    data = scio.loadmat(mat_path)['ValidationNoisyBlocksSrgb']
    N, B, H, W, C = data.shape
    data = data.reshape(N * B, H, W, C)
    for i in tqdm(range(N * B)):
        cv2.imwrite(osp.join(folder_path, 'ValidationBlocksSrgb_{}.png'.format(i)), cv2.cvtColor(data[i, ...], cv2.COLOR_RGB2BGR))
    img_path_list, keys = prepare_keys(folder_path, 'png')
    make_lmdb_from_imgs(folder_path, lmdb_path, img_path_list, keys)
    folder_path = './datasets/SIDD/val/gt_crops'
    lmdb_path = './datasets/SIDD/val/gt_crops.lmdb'
    mat_path = './datasets/SIDD/ValidationGtBlocksSrgb.mat'
    if not osp.exists(folder_path):
        os.makedirs(folder_path)
    assert osp.exists(mat_path)
    data = scio.loadmat(mat_path)['ValidationGtBlocksSrgb']
    N, B, H, W, C = data.shape
    data = data.reshape(N * B, H, W, C)
    for i in tqdm(range(N * B)):
        cv2.imwrite(osp.join(folder_path, 'ValidationBlocksSrgb_{}.png'.format(i)), cv2.cvtColor(data[i, ...], cv2.COLOR_RGB2BGR))
    img_path_list, keys = prepare_keys(folder_path, 'png')
    make_lmdb_from_imgs(folder_path, lmdb_path, img_path_list, keys)

def flowread(flow_path, quantize=False, concat_axis=0, *args, **kwargs):
    """Read an optical flow map.

    Args:
        flow_path (ndarray or str): Flow path.
        quantize (bool): whether to read quantized pair, if set to True,
            remaining args will be passed to :func:`dequantize_flow`.
        concat_axis (int): The axis that dx and dy are concatenated,
            can be either 0 or 1. Ignored if quantize is False.

    Returns:
        ndarray: Optical flow represented as a (h, w, 2) numpy array
    """
    if quantize:
        assert concat_axis in [0, 1]
        cat_flow = cv2.imread(flow_path, cv2.IMREAD_UNCHANGED)
        if cat_flow.ndim != 2:
            raise IOError(f'{flow_path} is not a valid quantized flow file, its dimension is {cat_flow.ndim}.')
        assert cat_flow.shape[concat_axis] % 2 == 0
        dx, dy = np.split(cat_flow, 2, axis=concat_axis)
        flow = dequantize_flow(dx, dy, *args, **kwargs)
    else:
        with open(flow_path, 'rb') as f:
            try:
                header = f.read(4).decode('utf-8')
            except Exception:
                raise IOError(f'Invalid flow file: {flow_path}')
            else:
                if header != 'PIEH':
                    raise IOError(f'Invalid flow file: {flow_path}, header does not contain PIEH')
            w = np.fromfile(f, np.int32, 1).squeeze()
            h = np.fromfile(f, np.int32, 1).squeeze()
            flow = np.fromfile(f, np.float32, w * h * 2).reshape((h, w, 2))
    return flow.astype(np.float32)

def img_rotate(img, angle, center=None, scale=1.0):
    """Rotate image.

    Args:
        img (ndarray): Image to be rotated.
        angle (float): Rotation angle in degrees. Positive values mean
            counter-clockwise rotation.
        center (tuple[int]): Rotation center. If the center is None,
            initialize it as the center of the image. Default: None.
        scale (float): Isotropic scale factor. Default: 1.0.
    """
    h, w = img.shape[:2]
    if center is None:
        center = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, scale)
    rotated_img = cv2.warpAffine(img, matrix, (w, h))
    return rotated_img

def load_img(filepath):
    return cv2.cvtColor(cv2.imread(filepath), cv2.COLOR_BGR2RGB)

def load_img16(filepath):
    return cv2.cvtColor(cv2.imread(filepath, -1), cv2.COLOR_BGR2RGB)

def save_img(filepath, img):
    cv2.imwrite(filepath, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))

def load_img(filepath):
    return cv2.cvtColor(cv2.imread(filepath), cv2.COLOR_BGR2RGB)

def save_img(filepath, img):
    cv2.imwrite(filepath, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))

def load_gray_img(filepath):
    return np.expand_dims(cv2.imread(filepath, cv2.IMREAD_GRAYSCALE), axis=2)

def save_gray_img(filepath, img):
    cv2.imwrite(filepath, img)

def load_img(filepath):
    return cv2.cvtColor(cv2.imread(filepath), cv2.COLOR_BGR2RGB)

def save_img(filepath, img):
    cv2.imwrite(filepath, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))

def load_gray_img(filepath):
    return np.expand_dims(cv2.imread(filepath, cv2.IMREAD_GRAYSCALE), axis=2)

def save_gray_img(filepath, img):
    cv2.imwrite(filepath, img)

