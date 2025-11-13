# Cluster 20

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

def imfrombytes(content, flag='color', float32=False):
    """Read an image from bytes.

    Args:
        content (bytes): Image bytes got from files or other streams.
        flag (str): Flags specifying the color type of a loaded image,
            candidates are `color`, `grayscale` and `unchanged`.
        float32 (bool): Whether to change to float32., If True, will also norm
            to [0, 1]. Default: False.

    Returns:
        ndarray: Loaded image array.
    """
    img_np = np.frombuffer(content, np.uint8)
    imread_flags = {'color': cv2.IMREAD_COLOR, 'grayscale': cv2.IMREAD_GRAYSCALE, 'unchanged': cv2.IMREAD_UNCHANGED}
    if img_np is None:
        raise Exception('None .. !!!')
    img = cv2.imdecode(img_np, imread_flags[flag])
    if float32:
        img = img.astype(np.float32) / 255.0
    return img

def imfrombytesDP(content, flag='color', float32=False):
    """Read an image from bytes.

    Args:
        content (bytes): Image bytes got from files or other streams.
        flag (str): Flags specifying the color type of a loaded image,
            candidates are `color`, `grayscale` and `unchanged`.
        float32 (bool): Whether to change to float32., If True, will also norm
            to [0, 1]. Default: False.

    Returns:
        ndarray: Loaded image array.
    """
    img_np = np.frombuffer(content, np.uint8)
    if img_np is None:
        raise Exception('None .. !!!')
    img = cv2.imdecode(img_np, cv2.IMREAD_UNCHANGED)
    if float32:
        img = img.astype(np.float32) / 65535.0
    return img

class FileClient(object):
    """A general file client to access files in different backend.

    The client loads a file or text in a specified backend from its path
    and return it as a binary file. it can also register other backend
    accessor with a given name and backend class.

    Attributes:
        backend (str): The storage backend type. Options are "disk",
            "memcached" and "lmdb".
        client (:obj:`BaseStorageBackend`): The backend object.
    """
    _backends = {'disk': HardDiskBackend, 'memcached': MemcachedBackend, 'lmdb': LmdbBackend}

    def __init__(self, backend='disk', **kwargs):
        if backend not in self._backends:
            raise ValueError(f'Backend {backend} is not supported. Currently supported ones are {list(self._backends.keys())}')
        self.backend = backend
        self.client = self._backends[backend](**kwargs)

    def get(self, filepath, client_key='default'):
        if self.backend == 'lmdb':
            return self.client.get(filepath, client_key)
        else:
            return self.client.get(filepath)

    def get_text(self, filepath):
        return self.client.get_text(filepath)

def get(self, filepath, client_key='default'):
    if self.backend == 'lmdb':
        return self.client.get(filepath, client_key)
    else:
        return self.client.get(filepath)

def download_file_from_google_drive(file_id, save_path):
    """Download files from google drive.

    Ref:
    https://stackoverflow.com/questions/25010369/wget-curl-large-file-from-google-drive  # noqa E501

    Args:
        file_id (str): File id.
        save_path (str): Save path.
    """
    session = requests.Session()
    URL = 'https://docs.google.com/uc?export=download'
    params = {'id': file_id}
    response = session.get(URL, params=params, stream=True)
    token = get_confirm_token(response)
    if token:
        params['confirm'] = token
        response = session.get(URL, params=params, stream=True)
    response_file_size = session.get(URL, params=params, stream=True, headers={'Range': 'bytes=0-2'})
    if 'Content-Range' in response_file_size.headers:
        file_size = int(response_file_size.headers['Content-Range'].split('/')[1])
    else:
        file_size = None
    save_response_content(response, save_path, file_size)

class Dataset_PairedImage(data.Dataset):
    """Paired image dataset for image restoration.

    Read LQ (Low Quality, e.g. LR (Low Resolution), blurry, noisy, etc) and
    GT image pairs.

    There are three modes:
    1. 'lmdb': Use lmdb files.
        If opt['io_backend'] == lmdb.
    2. 'meta_info_file': Use meta information file to generate paths.
        If opt['io_backend'] != lmdb and opt['meta_info_file'] is not None.
    3. 'folder': Scan folders to generate paths.
        The rest.

    Args:
        opt (dict): Config for train datasets. It contains the following keys:
            dataroot_gt (str): Data root path for gt.
            dataroot_lq (str): Data root path for lq.
            meta_info_file (str): Path for meta information file.
            io_backend (dict): IO backend type and other kwarg.
            filename_tmpl (str): Template for each filename. Note that the
                template excludes the file extension. Default: '{}'.
            gt_size (int): Cropped patched size for gt patches.
            geometric_augs (bool): Use geometric augmentations.

            scale (bool): Scale, which will be added automatically.
            phase (str): 'train' or 'val'.
    """

    def __init__(self, opt):
        super(Dataset_PairedImage, self).__init__()
        self.opt = opt
        self.file_client = None
        self.io_backend_opt = opt['io_backend']
        self.mean = opt['mean'] if 'mean' in opt else None
        self.std = opt['std'] if 'std' in opt else None
        self.gt_folder, self.lq_folder = (opt['dataroot_gt'], opt['dataroot_lq'])
        if 'filename_tmpl' in opt:
            self.filename_tmpl = opt['filename_tmpl']
        else:
            self.filename_tmpl = '{}'
        if self.io_backend_opt['type'] == 'lmdb':
            self.io_backend_opt['db_paths'] = [self.lq_folder, self.gt_folder]
            self.io_backend_opt['client_keys'] = ['lq', 'gt']
            self.paths = paired_paths_from_lmdb([self.lq_folder, self.gt_folder], ['lq', 'gt'])
        elif 'meta_info_file' in self.opt and self.opt['meta_info_file'] is not None:
            self.paths = paired_paths_from_meta_info_file([self.lq_folder, self.gt_folder], ['lq', 'gt'], self.opt['meta_info_file'], self.filename_tmpl)
        else:
            self.paths = paired_paths_from_folder([self.lq_folder, self.gt_folder], ['lq', 'gt'], self.filename_tmpl)
        if self.opt['phase'] == 'train':
            self.geometric_augs = opt['geometric_augs']

    def __getitem__(self, index):
        if self.file_client is None:
            self.file_client = FileClient(self.io_backend_opt.pop('type'), **self.io_backend_opt)
        scale = self.opt['scale']
        index = index % len(self.paths)
        gt_path = self.paths[index]['gt_path']
        img_bytes = self.file_client.get(gt_path, 'gt')
        try:
            img_gt = imfrombytes(img_bytes, float32=True)
        except:
            raise Exception('gt path {} not working'.format(gt_path))
        lq_path = self.paths[index]['lq_path']
        img_bytes = self.file_client.get(lq_path, 'lq')
        try:
            img_lq = imfrombytes(img_bytes, float32=True)
        except:
            raise Exception('lq path {} not working'.format(lq_path))
        if self.opt['phase'] == 'train':
            gt_size = self.opt['gt_size']
            img_gt, img_lq = padding(img_gt, img_lq, gt_size)
            img_gt, img_lq = paired_random_crop(img_gt, img_lq, gt_size, scale, gt_path)
            if self.geometric_augs:
                img_gt, img_lq = random_augmentation(img_gt, img_lq)
        img_gt, img_lq = img2tensor([img_gt, img_lq], bgr2rgb=True, float32=True)
        if self.mean is not None or self.std is not None:
            normalize(img_lq, self.mean, self.std, inplace=True)
            normalize(img_gt, self.mean, self.std, inplace=True)
        return {'lq': img_lq, 'gt': img_gt, 'lq_path': lq_path, 'gt_path': gt_path}

    def __len__(self):
        return len(self.paths)

def __getitem__(self, index):
    if self.file_client is None:
        self.file_client = FileClient(self.io_backend_opt.pop('type'), **self.io_backend_opt)
    scale = self.opt['scale']
    index = index % len(self.paths)
    gt_path = self.paths[index]['gt_path']
    img_bytes = self.file_client.get(gt_path, 'gt')
    try:
        img_gt = imfrombytes(img_bytes, float32=True)
    except:
        raise Exception('gt path {} not working'.format(gt_path))
    lq_path = self.paths[index]['lq_path']
    img_bytes = self.file_client.get(lq_path, 'lq')
    try:
        img_lq = imfrombytes(img_bytes, float32=True)
    except:
        raise Exception('lq path {} not working'.format(lq_path))
    if self.opt['phase'] == 'train':
        gt_size = self.opt['gt_size']
        img_gt, img_lq = padding(img_gt, img_lq, gt_size)
        img_gt, img_lq = paired_random_crop(img_gt, img_lq, gt_size, scale, gt_path)
        if self.geometric_augs:
            img_gt, img_lq = random_augmentation(img_gt, img_lq)
    img_gt, img_lq = img2tensor([img_gt, img_lq], bgr2rgb=True, float32=True)
    if self.mean is not None or self.std is not None:
        normalize(img_lq, self.mean, self.std, inplace=True)
        normalize(img_gt, self.mean, self.std, inplace=True)
    return {'lq': img_lq, 'gt': img_gt, 'lq_path': lq_path, 'gt_path': gt_path}

class Dataset_GaussianDenoising(data.Dataset):
    """Paired image dataset for image restoration.

    Read LQ (Low Quality, e.g. LR (Low Resolution), blurry, noisy, etc) and
    GT image pairs.

    There are three modes:
    1. 'lmdb': Use lmdb files.
        If opt['io_backend'] == lmdb.
    2. 'meta_info_file': Use meta information file to generate paths.
        If opt['io_backend'] != lmdb and opt['meta_info_file'] is not None.
    3. 'folder': Scan folders to generate paths.
        The rest.

    Args:
        opt (dict): Config for train datasets. It contains the following keys:
            dataroot_gt (str): Data root path for gt.
            meta_info_file (str): Path for meta information file.
            io_backend (dict): IO backend type and other kwarg.
            gt_size (int): Cropped patched size for gt patches.
            use_flip (bool): Use horizontal flips.
            use_rot (bool): Use rotation (use vertical flip and transposing h
                and w for implementation).

            scale (bool): Scale, which will be added automatically.
            phase (str): 'train' or 'val'.
    """

    def __init__(self, opt):
        super(Dataset_GaussianDenoising, self).__init__()
        self.opt = opt
        if self.opt['phase'] == 'train':
            self.sigma_type = opt['sigma_type']
            self.sigma_range = opt['sigma_range']
            assert self.sigma_type in ['constant', 'random', 'choice']
        else:
            self.sigma_test = opt['sigma_test']
        self.in_ch = opt['in_ch']
        self.file_client = None
        self.io_backend_opt = opt['io_backend']
        self.mean = opt['mean'] if 'mean' in opt else None
        self.std = opt['std'] if 'std' in opt else None
        self.gt_folder = opt['dataroot_gt']
        if self.io_backend_opt['type'] == 'lmdb':
            self.io_backend_opt['db_paths'] = [self.gt_folder]
            self.io_backend_opt['client_keys'] = ['gt']
            self.paths = paths_from_lmdb(self.gt_folder)
        elif 'meta_info_file' in self.opt:
            with open(self.opt['meta_info_file'], 'r') as fin:
                self.paths = [osp.join(self.gt_folder, line.split(' ')[0]) for line in fin]
        else:
            self.paths = sorted(list(scandir(self.gt_folder, full_path=True)))
        if self.opt['phase'] == 'train':
            self.geometric_augs = self.opt['geometric_augs']

    def __getitem__(self, index):
        if self.file_client is None:
            self.file_client = FileClient(self.io_backend_opt.pop('type'), **self.io_backend_opt)
        scale = self.opt['scale']
        index = index % len(self.paths)
        gt_path = self.paths[index]['gt_path']
        img_bytes = self.file_client.get(gt_path, 'gt')
        if self.in_ch == 3:
            try:
                img_gt = imfrombytes(img_bytes, float32=True)
            except:
                raise Exception('gt path {} not working'.format(gt_path))
            img_gt = cv2.cvtColor(img_gt, cv2.COLOR_BGR2RGB)
        else:
            try:
                img_gt = imfrombytes(img_bytes, flag='grayscale', float32=True)
            except:
                raise Exception('gt path {} not working'.format(gt_path))
            img_gt = np.expand_dims(img_gt, axis=2)
        img_lq = img_gt.copy()
        if self.opt['phase'] == 'train':
            gt_size = self.opt['gt_size']
            img_gt, img_lq = padding(img_gt, img_lq, gt_size)
            img_gt, img_lq = paired_random_crop(img_gt, img_lq, gt_size, scale, gt_path)
            if self.geometric_augs:
                img_gt, img_lq = random_augmentation(img_gt, img_lq)
            img_gt, img_lq = img2tensor([img_gt, img_lq], bgr2rgb=False, float32=True)
            if self.sigma_type == 'constant':
                sigma_value = self.sigma_range
            elif self.sigma_type == 'random':
                sigma_value = random.uniform(self.sigma_range[0], self.sigma_range[1])
            elif self.sigma_type == 'choice':
                sigma_value = random.choice(self.sigma_range)
            noise_level = torch.FloatTensor([sigma_value]) / 255.0
            noise = torch.randn(img_lq.size()).mul_(noise_level).float()
            img_lq.add_(noise)
        else:
            np.random.seed(seed=0)
            img_lq += np.random.normal(0, self.sigma_test / 255.0, img_lq.shape)
            img_gt, img_lq = img2tensor([img_gt, img_lq], bgr2rgb=False, float32=True)
        return {'lq': img_lq, 'gt': img_gt, 'lq_path': gt_path, 'gt_path': gt_path}

    def __len__(self):
        return len(self.paths)

def __getitem__(self, index):
    if self.file_client is None:
        self.file_client = FileClient(self.io_backend_opt.pop('type'), **self.io_backend_opt)
    scale = self.opt['scale']
    index = index % len(self.paths)
    gt_path = self.paths[index]['gt_path']
    img_bytes = self.file_client.get(gt_path, 'gt')
    if self.in_ch == 3:
        try:
            img_gt = imfrombytes(img_bytes, float32=True)
        except:
            raise Exception('gt path {} not working'.format(gt_path))
        img_gt = cv2.cvtColor(img_gt, cv2.COLOR_BGR2RGB)
    else:
        try:
            img_gt = imfrombytes(img_bytes, flag='grayscale', float32=True)
        except:
            raise Exception('gt path {} not working'.format(gt_path))
        img_gt = np.expand_dims(img_gt, axis=2)
    img_lq = img_gt.copy()
    if self.opt['phase'] == 'train':
        gt_size = self.opt['gt_size']
        img_gt, img_lq = padding(img_gt, img_lq, gt_size)
        img_gt, img_lq = paired_random_crop(img_gt, img_lq, gt_size, scale, gt_path)
        if self.geometric_augs:
            img_gt, img_lq = random_augmentation(img_gt, img_lq)
        img_gt, img_lq = img2tensor([img_gt, img_lq], bgr2rgb=False, float32=True)
        if self.sigma_type == 'constant':
            sigma_value = self.sigma_range
        elif self.sigma_type == 'random':
            sigma_value = random.uniform(self.sigma_range[0], self.sigma_range[1])
        elif self.sigma_type == 'choice':
            sigma_value = random.choice(self.sigma_range)
        noise_level = torch.FloatTensor([sigma_value]) / 255.0
        noise = torch.randn(img_lq.size()).mul_(noise_level).float()
        img_lq.add_(noise)
    else:
        np.random.seed(seed=0)
        img_lq += np.random.normal(0, self.sigma_test / 255.0, img_lq.shape)
        img_gt, img_lq = img2tensor([img_gt, img_lq], bgr2rgb=False, float32=True)
    return {'lq': img_lq, 'gt': img_gt, 'lq_path': gt_path, 'gt_path': gt_path}

class Dataset_DefocusDeblur_DualPixel_16bit(data.Dataset):

    def __init__(self, opt):
        super(Dataset_DefocusDeblur_DualPixel_16bit, self).__init__()
        self.opt = opt
        self.file_client = None
        self.io_backend_opt = opt['io_backend']
        self.mean = opt['mean'] if 'mean' in opt else None
        self.std = opt['std'] if 'std' in opt else None
        self.gt_folder, self.lqL_folder, self.lqR_folder = (opt['dataroot_gt'], opt['dataroot_lqL'], opt['dataroot_lqR'])
        if 'filename_tmpl' in opt:
            self.filename_tmpl = opt['filename_tmpl']
        else:
            self.filename_tmpl = '{}'
        self.paths = paired_DP_paths_from_folder([self.lqL_folder, self.lqR_folder, self.gt_folder], ['lqL', 'lqR', 'gt'], self.filename_tmpl)
        if self.opt['phase'] == 'train':
            self.geometric_augs = self.opt['geometric_augs']

    def __getitem__(self, index):
        if self.file_client is None:
            self.file_client = FileClient(self.io_backend_opt.pop('type'), **self.io_backend_opt)
        scale = self.opt['scale']
        index = index % len(self.paths)
        gt_path = self.paths[index]['gt_path']
        img_bytes = self.file_client.get(gt_path, 'gt')
        try:
            img_gt = imfrombytesDP(img_bytes, float32=True)
        except:
            raise Exception('gt path {} not working'.format(gt_path))
        lqL_path = self.paths[index]['lqL_path']
        img_bytes = self.file_client.get(lqL_path, 'lqL')
        try:
            img_lqL = imfrombytesDP(img_bytes, float32=True)
        except:
            raise Exception('lqL path {} not working'.format(lqL_path))
        lqR_path = self.paths[index]['lqR_path']
        img_bytes = self.file_client.get(lqR_path, 'lqR')
        try:
            img_lqR = imfrombytesDP(img_bytes, float32=True)
        except:
            raise Exception('lqR path {} not working'.format(lqR_path))
        if self.opt['phase'] == 'train':
            gt_size = self.opt['gt_size']
            img_lqL, img_lqR, img_gt = padding_DP(img_lqL, img_lqR, img_gt, gt_size)
            img_lqL, img_lqR, img_gt = paired_random_crop_DP(img_lqL, img_lqR, img_gt, gt_size, scale, gt_path)
            if self.geometric_augs:
                img_lqL, img_lqR, img_gt = random_augmentation(img_lqL, img_lqR, img_gt)
        img_lqL, img_lqR, img_gt = img2tensor([img_lqL, img_lqR, img_gt], bgr2rgb=True, float32=True)
        if self.mean is not None or self.std is not None:
            normalize(img_lqL, self.mean, self.std, inplace=True)
            normalize(img_lqR, self.mean, self.std, inplace=True)
            normalize(img_gt, self.mean, self.std, inplace=True)
        img_lq = torch.cat([img_lqL, img_lqR], 0)
        return {'lq': img_lq, 'gt': img_gt, 'lq_path': lqL_path, 'gt_path': gt_path}

    def __len__(self):
        return len(self.paths)

def __getitem__(self, index):
    if self.file_client is None:
        self.file_client = FileClient(self.io_backend_opt.pop('type'), **self.io_backend_opt)
    scale = self.opt['scale']
    index = index % len(self.paths)
    gt_path = self.paths[index]['gt_path']
    img_bytes = self.file_client.get(gt_path, 'gt')
    try:
        img_gt = imfrombytesDP(img_bytes, float32=True)
    except:
        raise Exception('gt path {} not working'.format(gt_path))
    lqL_path = self.paths[index]['lqL_path']
    img_bytes = self.file_client.get(lqL_path, 'lqL')
    try:
        img_lqL = imfrombytesDP(img_bytes, float32=True)
    except:
        raise Exception('lqL path {} not working'.format(lqL_path))
    lqR_path = self.paths[index]['lqR_path']
    img_bytes = self.file_client.get(lqR_path, 'lqR')
    try:
        img_lqR = imfrombytesDP(img_bytes, float32=True)
    except:
        raise Exception('lqR path {} not working'.format(lqR_path))
    if self.opt['phase'] == 'train':
        gt_size = self.opt['gt_size']
        img_lqL, img_lqR, img_gt = padding_DP(img_lqL, img_lqR, img_gt, gt_size)
        img_lqL, img_lqR, img_gt = paired_random_crop_DP(img_lqL, img_lqR, img_gt, gt_size, scale, gt_path)
        if self.geometric_augs:
            img_lqL, img_lqR, img_gt = random_augmentation(img_lqL, img_lqR, img_gt)
    img_lqL, img_lqR, img_gt = img2tensor([img_lqL, img_lqR, img_gt], bgr2rgb=True, float32=True)
    if self.mean is not None or self.std is not None:
        normalize(img_lqL, self.mean, self.std, inplace=True)
        normalize(img_lqR, self.mean, self.std, inplace=True)
        normalize(img_gt, self.mean, self.std, inplace=True)
    img_lq = torch.cat([img_lqL, img_lqR], 0)
    return {'lq': img_lq, 'gt': img_gt, 'lq_path': lqL_path, 'gt_path': gt_path}

class PrefetchGenerator(threading.Thread):
    """A general prefetch generator.

    Ref:
    https://stackoverflow.com/questions/7323664/python-generator-pre-fetch

    Args:
        generator: Python generator.
        num_prefetch_queue (int): Number of prefetch queue.
    """

    def __init__(self, generator, num_prefetch_queue):
        threading.Thread.__init__(self)
        self.queue = Queue.Queue(num_prefetch_queue)
        self.generator = generator
        self.daemon = True
        self.start()

    def run(self):
        for item in self.generator:
            self.queue.put(item)
        self.queue.put(None)

    def __next__(self):
        next_item = self.queue.get()
        if next_item is None:
            raise StopIteration
        return next_item

    def __iter__(self):
        return self

def __next__(self):
    next_item = self.queue.get()
    if next_item is None:
        raise StopIteration
    return next_item

class SingleImageDataset(data.Dataset):
    """Read only lq images in the test phase.

    Read LQ (Low Quality, e.g. LR (Low Resolution), blurry, noisy, etc).

    There are two modes:
    1. 'meta_info_file': Use meta information file to generate paths.
    2. 'folder': Scan folders to generate paths.

    Args:
        opt (dict): Config for train datasets. It contains the following keys:
            dataroot_lq (str): Data root path for lq.
            meta_info_file (str): Path for meta information file.
            io_backend (dict): IO backend type and other kwarg.
    """

    def __init__(self, opt):
        super(SingleImageDataset, self).__init__()
        self.opt = opt
        self.file_client = None
        self.io_backend_opt = opt['io_backend']
        self.mean = opt['mean'] if 'mean' in opt else None
        self.std = opt['std'] if 'std' in opt else None
        self.lq_folder = opt['dataroot_lq']
        if self.io_backend_opt['type'] == 'lmdb':
            self.io_backend_opt['db_paths'] = [self.lq_folder]
            self.io_backend_opt['client_keys'] = ['lq']
            self.paths = paths_from_lmdb(self.lq_folder)
        elif 'meta_info_file' in self.opt:
            with open(self.opt['meta_info_file'], 'r') as fin:
                self.paths = [osp.join(self.lq_folder, line.split(' ')[0]) for line in fin]
        else:
            self.paths = sorted(list(scandir(self.lq_folder, full_path=True)))

    def __getitem__(self, index):
        if self.file_client is None:
            self.file_client = FileClient(self.io_backend_opt.pop('type'), **self.io_backend_opt)
        lq_path = self.paths[index]
        img_bytes = self.file_client.get(lq_path, 'lq')
        img_lq = imfrombytes(img_bytes, float32=True)
        img_lq = img2tensor(img_lq, bgr2rgb=True, float32=True)
        if self.mean is not None or self.std is not None:
            normalize(img_lq, self.mean, self.std, inplace=True)
        return {'lq': img_lq, 'lq_path': lq_path}

    def __len__(self):
        return len(self.paths)

def __getitem__(self, index):
    if self.file_client is None:
        self.file_client = FileClient(self.io_backend_opt.pop('type'), **self.io_backend_opt)
    lq_path = self.paths[index]
    img_bytes = self.file_client.get(lq_path, 'lq')
    img_lq = imfrombytes(img_bytes, float32=True)
    img_lq = img2tensor(img_lq, bgr2rgb=True, float32=True)
    if self.mean is not None or self.std is not None:
        normalize(img_lq, self.mean, self.std, inplace=True)
    return {'lq': img_lq, 'lq_path': lq_path}

class REDSDataset(data.Dataset):
    """REDS dataset for training.

    The keys are generated from a meta info txt file.
    basicsr/data/meta_info/meta_info_REDS_GT.txt

    Each line contains:
    1. subfolder (clip) name; 2. frame number; 3. image shape, seperated by
    a white space.
    Examples:
    000 100 (720,1280,3)
    001 100 (720,1280,3)
    ...

    Key examples: "000/00000000"
    GT (gt): Ground-Truth;
    LQ (lq): Low-Quality, e.g., low-resolution/blurry/noisy/compressed frames.

    Args:
        opt (dict): Config for train dataset. It contains the following keys:
            dataroot_gt (str): Data root path for gt.
            dataroot_lq (str): Data root path for lq.
            dataroot_flow (str, optional): Data root path for flow.
            meta_info_file (str): Path for meta information file.
            val_partition (str): Validation partition types. 'REDS4' or
                'official'.
            io_backend (dict): IO backend type and other kwarg.

            num_frame (int): Window size for input frames.
            gt_size (int): Cropped patched size for gt patches.
            interval_list (list): Interval list for temporal augmentation.
            random_reverse (bool): Random reverse input frames.
            use_flip (bool): Use horizontal flips.
            use_rot (bool): Use rotation (use vertical flip and transposing h
                and w for implementation).

            scale (bool): Scale, which will be added automatically.
    """

    def __init__(self, opt):
        super(REDSDataset, self).__init__()
        self.opt = opt
        self.gt_root, self.lq_root = (Path(opt['dataroot_gt']), Path(opt['dataroot_lq']))
        self.flow_root = Path(opt['dataroot_flow']) if opt['dataroot_flow'] is not None else None
        assert opt['num_frame'] % 2 == 1, f'num_frame should be odd number, but got {opt['num_frame']}'
        self.num_frame = opt['num_frame']
        self.num_half_frames = opt['num_frame'] // 2
        self.keys = []
        with open(opt['meta_info_file'], 'r') as fin:
            for line in fin:
                folder, frame_num, _ = line.split(' ')
                self.keys.extend([f'{folder}/{i:08d}' for i in range(int(frame_num))])
        if opt['val_partition'] == 'REDS4':
            val_partition = ['000', '011', '015', '020']
        elif opt['val_partition'] == 'official':
            val_partition = [f'{v:03d}' for v in range(240, 270)]
        else:
            raise ValueError(f"Wrong validation partition {opt['val_partition']}.Supported ones are ['official', 'REDS4'].")
        self.keys = [v for v in self.keys if v.split('/')[0] not in val_partition]
        self.file_client = None
        self.io_backend_opt = opt['io_backend']
        self.is_lmdb = False
        if self.io_backend_opt['type'] == 'lmdb':
            self.is_lmdb = True
            if self.flow_root is not None:
                self.io_backend_opt['db_paths'] = [self.lq_root, self.gt_root, self.flow_root]
                self.io_backend_opt['client_keys'] = ['lq', 'gt', 'flow']
            else:
                self.io_backend_opt['db_paths'] = [self.lq_root, self.gt_root]
                self.io_backend_opt['client_keys'] = ['lq', 'gt']
        self.interval_list = opt['interval_list']
        self.random_reverse = opt['random_reverse']
        interval_str = ','.join((str(x) for x in opt['interval_list']))
        logger = get_root_logger()
        logger.info(f'Temporal augmentation interval list: [{interval_str}]; random reverse is {self.random_reverse}.')

    def __getitem__(self, index):
        if self.file_client is None:
            self.file_client = FileClient(self.io_backend_opt.pop('type'), **self.io_backend_opt)
        scale = self.opt['scale']
        gt_size = self.opt['gt_size']
        key = self.keys[index]
        clip_name, frame_name = key.split('/')
        center_frame_idx = int(frame_name)
        interval = random.choice(self.interval_list)
        start_frame_idx = center_frame_idx - self.num_half_frames * interval
        end_frame_idx = center_frame_idx + self.num_half_frames * interval
        while start_frame_idx < 0 or end_frame_idx > 99:
            center_frame_idx = random.randint(0, 99)
            start_frame_idx = center_frame_idx - self.num_half_frames * interval
            end_frame_idx = center_frame_idx + self.num_half_frames * interval
        frame_name = f'{center_frame_idx:08d}'
        neighbor_list = list(range(center_frame_idx - self.num_half_frames * interval, center_frame_idx + self.num_half_frames * interval + 1, interval))
        if self.random_reverse and random.random() < 0.5:
            neighbor_list.reverse()
        assert len(neighbor_list) == self.num_frame, f'Wrong length of neighbor list: {len(neighbor_list)}'
        if self.is_lmdb:
            img_gt_path = f'{clip_name}/{frame_name}'
        else:
            img_gt_path = self.gt_root / clip_name / f'{frame_name}.png'
        img_bytes = self.file_client.get(img_gt_path, 'gt')
        img_gt = imfrombytes(img_bytes, float32=True)
        img_lqs = []
        for neighbor in neighbor_list:
            if self.is_lmdb:
                img_lq_path = f'{clip_name}/{neighbor:08d}'
            else:
                img_lq_path = self.lq_root / clip_name / f'{neighbor:08d}.png'
            img_bytes = self.file_client.get(img_lq_path, 'lq')
            img_lq = imfrombytes(img_bytes, float32=True)
            img_lqs.append(img_lq)
        if self.flow_root is not None:
            img_flows = []
            for i in range(self.num_half_frames, 0, -1):
                if self.is_lmdb:
                    flow_path = f'{clip_name}/{frame_name}_p{i}'
                else:
                    flow_path = self.flow_root / clip_name / f'{frame_name}_p{i}.png'
                img_bytes = self.file_client.get(flow_path, 'flow')
                cat_flow = imfrombytes(img_bytes, flag='grayscale', float32=False)
                dx, dy = np.split(cat_flow, 2, axis=0)
                flow = dequantize_flow(dx, dy, max_val=20, denorm=False)
                img_flows.append(flow)
            for i in range(1, self.num_half_frames + 1):
                if self.is_lmdb:
                    flow_path = f'{clip_name}/{frame_name}_n{i}'
                else:
                    flow_path = self.flow_root / clip_name / f'{frame_name}_n{i}.png'
                img_bytes = self.file_client.get(flow_path, 'flow')
                cat_flow = imfrombytes(img_bytes, flag='grayscale', float32=False)
                dx, dy = np.split(cat_flow, 2, axis=0)
                flow = dequantize_flow(dx, dy, max_val=20, denorm=False)
                img_flows.append(flow)
            img_lqs.extend(img_flows)
        img_gt, img_lqs = paired_random_crop(img_gt, img_lqs, gt_size, scale, img_gt_path)
        if self.flow_root is not None:
            img_lqs, img_flows = (img_lqs[:self.num_frame], img_lqs[self.num_frame:])
        img_lqs.append(img_gt)
        if self.flow_root is not None:
            img_results, img_flows = augment(img_lqs, self.opt['use_flip'], self.opt['use_rot'], img_flows)
        else:
            img_results = augment(img_lqs, self.opt['use_flip'], self.opt['use_rot'])
        img_results = img2tensor(img_results)
        img_lqs = torch.stack(img_results[0:-1], dim=0)
        img_gt = img_results[-1]
        if self.flow_root is not None:
            img_flows = img2tensor(img_flows)
            img_flows.insert(self.num_half_frames, torch.zeros_like(img_flows[0]))
            img_flows = torch.stack(img_flows, dim=0)
        if self.flow_root is not None:
            return {'lq': img_lqs, 'flow': img_flows, 'gt': img_gt, 'key': key}
        else:
            return {'lq': img_lqs, 'gt': img_gt, 'key': key}

    def __len__(self):
        return len(self.keys)

def __getitem__(self, index):
    if self.file_client is None:
        self.file_client = FileClient(self.io_backend_opt.pop('type'), **self.io_backend_opt)
    scale = self.opt['scale']
    gt_size = self.opt['gt_size']
    key = self.keys[index]
    clip_name, frame_name = key.split('/')
    center_frame_idx = int(frame_name)
    interval = random.choice(self.interval_list)
    start_frame_idx = center_frame_idx - self.num_half_frames * interval
    end_frame_idx = center_frame_idx + self.num_half_frames * interval
    while start_frame_idx < 0 or end_frame_idx > 99:
        center_frame_idx = random.randint(0, 99)
        start_frame_idx = center_frame_idx - self.num_half_frames * interval
        end_frame_idx = center_frame_idx + self.num_half_frames * interval
    frame_name = f'{center_frame_idx:08d}'
    neighbor_list = list(range(center_frame_idx - self.num_half_frames * interval, center_frame_idx + self.num_half_frames * interval + 1, interval))
    if self.random_reverse and random.random() < 0.5:
        neighbor_list.reverse()
    assert len(neighbor_list) == self.num_frame, f'Wrong length of neighbor list: {len(neighbor_list)}'
    if self.is_lmdb:
        img_gt_path = f'{clip_name}/{frame_name}'
    else:
        img_gt_path = self.gt_root / clip_name / f'{frame_name}.png'
    img_bytes = self.file_client.get(img_gt_path, 'gt')
    img_gt = imfrombytes(img_bytes, float32=True)
    img_lqs = []
    for neighbor in neighbor_list:
        if self.is_lmdb:
            img_lq_path = f'{clip_name}/{neighbor:08d}'
        else:
            img_lq_path = self.lq_root / clip_name / f'{neighbor:08d}.png'
        img_bytes = self.file_client.get(img_lq_path, 'lq')
        img_lq = imfrombytes(img_bytes, float32=True)
        img_lqs.append(img_lq)
    if self.flow_root is not None:
        img_flows = []
        for i in range(self.num_half_frames, 0, -1):
            if self.is_lmdb:
                flow_path = f'{clip_name}/{frame_name}_p{i}'
            else:
                flow_path = self.flow_root / clip_name / f'{frame_name}_p{i}.png'
            img_bytes = self.file_client.get(flow_path, 'flow')
            cat_flow = imfrombytes(img_bytes, flag='grayscale', float32=False)
            dx, dy = np.split(cat_flow, 2, axis=0)
            flow = dequantize_flow(dx, dy, max_val=20, denorm=False)
            img_flows.append(flow)
        for i in range(1, self.num_half_frames + 1):
            if self.is_lmdb:
                flow_path = f'{clip_name}/{frame_name}_n{i}'
            else:
                flow_path = self.flow_root / clip_name / f'{frame_name}_n{i}.png'
            img_bytes = self.file_client.get(flow_path, 'flow')
            cat_flow = imfrombytes(img_bytes, flag='grayscale', float32=False)
            dx, dy = np.split(cat_flow, 2, axis=0)
            flow = dequantize_flow(dx, dy, max_val=20, denorm=False)
            img_flows.append(flow)
        img_lqs.extend(img_flows)
    img_gt, img_lqs = paired_random_crop(img_gt, img_lqs, gt_size, scale, img_gt_path)
    if self.flow_root is not None:
        img_lqs, img_flows = (img_lqs[:self.num_frame], img_lqs[self.num_frame:])
    img_lqs.append(img_gt)
    if self.flow_root is not None:
        img_results, img_flows = augment(img_lqs, self.opt['use_flip'], self.opt['use_rot'], img_flows)
    else:
        img_results = augment(img_lqs, self.opt['use_flip'], self.opt['use_rot'])
    img_results = img2tensor(img_results)
    img_lqs = torch.stack(img_results[0:-1], dim=0)
    img_gt = img_results[-1]
    if self.flow_root is not None:
        img_flows = img2tensor(img_flows)
        img_flows.insert(self.num_half_frames, torch.zeros_like(img_flows[0]))
        img_flows = torch.stack(img_flows, dim=0)
    if self.flow_root is not None:
        return {'lq': img_lqs, 'flow': img_flows, 'gt': img_gt, 'key': key}
    else:
        return {'lq': img_lqs, 'gt': img_gt, 'key': key}

def read_img_seq(path, require_mod_crop=False, scale=1):
    """Read a sequence of images from a given folder path.

    Args:
        path (list[str] | str): List of image paths or image folder path.
        require_mod_crop (bool): Require mod crop for each image.
            Default: False.
        scale (int): Scale factor for mod_crop. Default: 1.

    Returns:
        Tensor: size (t, c, h, w), RGB, [0, 1].
    """
    if isinstance(path, list):
        img_paths = path
    else:
        img_paths = sorted(list(scandir(path, full_path=True)))
    imgs = [cv2.imread(v).astype(np.float32) / 255.0 for v in img_paths]
    if require_mod_crop:
        imgs = [mod_crop(img, scale) for img in imgs]
    imgs = img2tensor(imgs, bgr2rgb=True, float32=True)
    imgs = torch.stack(imgs, dim=0)
    return imgs

class FFHQDataset(data.Dataset):
    """FFHQ dataset for StyleGAN.

    Args:
        opt (dict): Config for train datasets. It contains the following keys:
            dataroot_gt (str): Data root path for gt.
            io_backend (dict): IO backend type and other kwarg.
            mean (list | tuple): Image mean.
            std (list | tuple): Image std.
            use_hflip (bool): Whether to horizontally flip.

    """

    def __init__(self, opt):
        super(FFHQDataset, self).__init__()
        self.opt = opt
        self.file_client = None
        self.io_backend_opt = opt['io_backend']
        self.gt_folder = opt['dataroot_gt']
        self.mean = opt['mean']
        self.std = opt['std']
        if self.io_backend_opt['type'] == 'lmdb':
            self.io_backend_opt['db_paths'] = self.gt_folder
            if not self.gt_folder.endswith('.lmdb'):
                raise ValueError(f"'dataroot_gt' should end with '.lmdb', but received {self.gt_folder}")
            with open(osp.join(self.gt_folder, 'meta_info.txt')) as fin:
                self.paths = [line.split('.')[0] for line in fin]
        else:
            self.paths = [osp.join(self.gt_folder, f'{v:08d}.png') for v in range(70000)]

    def __getitem__(self, index):
        if self.file_client is None:
            self.file_client = FileClient(self.io_backend_opt.pop('type'), **self.io_backend_opt)
        gt_path = self.paths[index]
        img_bytes = self.file_client.get(gt_path)
        img_gt = imfrombytes(img_bytes, float32=True)
        img_gt = augment(img_gt, hflip=self.opt['use_hflip'], rotation=False)
        img_gt = img2tensor(img_gt, bgr2rgb=True, float32=True)
        normalize(img_gt, self.mean, self.std, inplace=True)
        return {'gt': img_gt, 'gt_path': gt_path}

    def __len__(self):
        return len(self.paths)

def __getitem__(self, index):
    if self.file_client is None:
        self.file_client = FileClient(self.io_backend_opt.pop('type'), **self.io_backend_opt)
    gt_path = self.paths[index]
    img_bytes = self.file_client.get(gt_path)
    img_gt = imfrombytes(img_bytes, float32=True)
    img_gt = augment(img_gt, hflip=self.opt['use_hflip'], rotation=False)
    img_gt = img2tensor(img_gt, bgr2rgb=True, float32=True)
    normalize(img_gt, self.mean, self.std, inplace=True)
    return {'gt': img_gt, 'gt_path': gt_path}

def augment(imgs, hflip=True, rotation=True, flows=None, return_status=False):
    """Augment: horizontal flips OR rotate (0, 90, 180, 270 degrees).

    We use vertical flip and transpose for rotation implementation.
    All the images in the list use the same augmentation.

    Args:
        imgs (list[ndarray] | ndarray): Images to be augmented. If the input
            is an ndarray, it will be transformed to a list.
        hflip (bool): Horizontal flip. Default: True.
        rotation (bool): Ratotation. Default: True.
        flows (list[ndarray]: Flows to be augmented. If the input is an
            ndarray, it will be transformed to a list.
            Dimension is (h, w, 2). Default: None.
        return_status (bool): Return the status of flip and rotation.
            Default: False.

    Returns:
        list[ndarray] | ndarray: Augmented images and flows. If returned
            results only have one element, just return ndarray.

    """
    hflip = hflip and random.random() < 0.5
    vflip = rotation and random.random() < 0.5
    rot90 = rotation and random.random() < 0.5

    def _augment(img):
        if hflip:
            cv2.flip(img, 1, img)
        if vflip:
            cv2.flip(img, 0, img)
        if rot90:
            img = img.transpose(1, 0, 2)
        return img

    def _augment_flow(flow):
        if hflip:
            cv2.flip(flow, 1, flow)
            flow[:, :, 0] *= -1
        if vflip:
            cv2.flip(flow, 0, flow)
            flow[:, :, 1] *= -1
        if rot90:
            flow = flow.transpose(1, 0, 2)
            flow = flow[:, :, [1, 0]]
        return flow
    if not isinstance(imgs, list):
        imgs = [imgs]
    imgs = [_augment(img) for img in imgs]
    if len(imgs) == 1:
        imgs = imgs[0]
    if flows is not None:
        if not isinstance(flows, list):
            flows = [flows]
        flows = [_augment_flow(flow) for flow in flows]
        if len(flows) == 1:
            flows = flows[0]
        return (imgs, flows)
    elif return_status:
        return (imgs, (hflip, vflip, rot90))
    else:
        return imgs

def data_augmentation(image, mode):
    """
    Performs data augmentation of the input image
    Input:
        image: a cv2 (OpenCV) image
        mode: int. Choice of transformation to apply to the image
                0 - no transformation
                1 - flip up and down
                2 - rotate counterwise 90 degree
                3 - rotate 90 degree and flip up and down
                4 - rotate 180 degree
                5 - rotate 180 degree and flip
                6 - rotate 270 degree
                7 - rotate 270 degree and flip
    """
    if mode == 0:
        out = image
    elif mode == 1:
        out = np.flipud(image)
    elif mode == 2:
        out = np.rot90(image)
    elif mode == 3:
        out = np.rot90(image)
        out = np.flipud(out)
    elif mode == 4:
        out = np.rot90(image, k=2)
    elif mode == 5:
        out = np.rot90(image, k=2)
        out = np.flipud(out)
    elif mode == 6:
        out = np.rot90(image, k=3)
    elif mode == 7:
        out = np.rot90(image, k=3)
        out = np.flipud(out)
    else:
        raise Exception('Invalid choice of image transformation')
    return out

class Vimeo90KDataset(data.Dataset):
    """Vimeo90K dataset for training.

    The keys are generated from a meta info txt file.
    basicsr/data/meta_info/meta_info_Vimeo90K_train_GT.txt

    Each line contains:
    1. clip name; 2. frame number; 3. image shape, seperated by a white space.
    Examples:
        00001/0001 7 (256,448,3)
        00001/0002 7 (256,448,3)

    Key examples: "00001/0001"
    GT (gt): Ground-Truth;
    LQ (lq): Low-Quality, e.g., low-resolution/blurry/noisy/compressed frames.

    The neighboring frame list for different num_frame:
    num_frame | frame list
             1 | 4
             3 | 3,4,5
             5 | 2,3,4,5,6
             7 | 1,2,3,4,5,6,7

    Args:
        opt (dict): Config for train dataset. It contains the following keys:
            dataroot_gt (str): Data root path for gt.
            dataroot_lq (str): Data root path for lq.
            meta_info_file (str): Path for meta information file.
            io_backend (dict): IO backend type and other kwarg.

            num_frame (int): Window size for input frames.
            gt_size (int): Cropped patched size for gt patches.
            random_reverse (bool): Random reverse input frames.
            use_flip (bool): Use horizontal flips.
            use_rot (bool): Use rotation (use vertical flip and transposing h
                and w for implementation).

            scale (bool): Scale, which will be added automatically.
    """

    def __init__(self, opt):
        super(Vimeo90KDataset, self).__init__()
        self.opt = opt
        self.gt_root, self.lq_root = (Path(opt['dataroot_gt']), Path(opt['dataroot_lq']))
        with open(opt['meta_info_file'], 'r') as fin:
            self.keys = [line.split(' ')[0] for line in fin]
        self.file_client = None
        self.io_backend_opt = opt['io_backend']
        self.is_lmdb = False
        if self.io_backend_opt['type'] == 'lmdb':
            self.is_lmdb = True
            self.io_backend_opt['db_paths'] = [self.lq_root, self.gt_root]
            self.io_backend_opt['client_keys'] = ['lq', 'gt']
        self.neighbor_list = [i + (9 - opt['num_frame']) // 2 for i in range(opt['num_frame'])]
        self.random_reverse = opt['random_reverse']
        logger = get_root_logger()
        logger.info(f'Random reverse is {self.random_reverse}.')

    def __getitem__(self, index):
        if self.file_client is None:
            self.file_client = FileClient(self.io_backend_opt.pop('type'), **self.io_backend_opt)
        if self.random_reverse and random.random() < 0.5:
            self.neighbor_list.reverse()
        scale = self.opt['scale']
        gt_size = self.opt['gt_size']
        key = self.keys[index]
        clip, seq = key.split('/')
        if self.is_lmdb:
            img_gt_path = f'{key}/im4'
        else:
            img_gt_path = self.gt_root / clip / seq / 'im4.png'
        img_bytes = self.file_client.get(img_gt_path, 'gt')
        img_gt = imfrombytes(img_bytes, float32=True)
        img_lqs = []
        for neighbor in self.neighbor_list:
            if self.is_lmdb:
                img_lq_path = f'{clip}/{seq}/im{neighbor}'
            else:
                img_lq_path = self.lq_root / clip / seq / f'im{neighbor}.png'
            img_bytes = self.file_client.get(img_lq_path, 'lq')
            img_lq = imfrombytes(img_bytes, float32=True)
            img_lqs.append(img_lq)
        img_gt, img_lqs = paired_random_crop(img_gt, img_lqs, gt_size, scale, img_gt_path)
        img_lqs.append(img_gt)
        img_results = augment(img_lqs, self.opt['use_flip'], self.opt['use_rot'])
        img_results = img2tensor(img_results)
        img_lqs = torch.stack(img_results[0:-1], dim=0)
        img_gt = img_results[-1]
        return {'lq': img_lqs, 'gt': img_gt, 'key': key}

    def __len__(self):
        return len(self.keys)

def __getitem__(self, index):
    if self.file_client is None:
        self.file_client = FileClient(self.io_backend_opt.pop('type'), **self.io_backend_opt)
    if self.random_reverse and random.random() < 0.5:
        self.neighbor_list.reverse()
    scale = self.opt['scale']
    gt_size = self.opt['gt_size']
    key = self.keys[index]
    clip, seq = key.split('/')
    if self.is_lmdb:
        img_gt_path = f'{key}/im4'
    else:
        img_gt_path = self.gt_root / clip / seq / 'im4.png'
    img_bytes = self.file_client.get(img_gt_path, 'gt')
    img_gt = imfrombytes(img_bytes, float32=True)
    img_lqs = []
    for neighbor in self.neighbor_list:
        if self.is_lmdb:
            img_lq_path = f'{clip}/{seq}/im{neighbor}'
        else:
            img_lq_path = self.lq_root / clip / seq / f'im{neighbor}.png'
        img_bytes = self.file_client.get(img_lq_path, 'lq')
        img_lq = imfrombytes(img_bytes, float32=True)
        img_lqs.append(img_lq)
    img_gt, img_lqs = paired_random_crop(img_gt, img_lqs, gt_size, scale, img_gt_path)
    img_lqs.append(img_gt)
    img_results = augment(img_lqs, self.opt['use_flip'], self.opt['use_rot'])
    img_results = img2tensor(img_results)
    img_lqs = torch.stack(img_results[0:-1], dim=0)
    img_gt = img_results[-1]
    return {'lq': img_lqs, 'gt': img_gt, 'key': key}

def define_network(opt):
    network_type = opt.pop('type')
    net = dynamic_instantiation(_arch_modules, network_type, opt)
    return net

