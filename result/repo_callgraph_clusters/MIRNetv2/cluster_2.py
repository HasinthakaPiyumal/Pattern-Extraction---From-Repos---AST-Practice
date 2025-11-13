# Cluster 2

def get_hash():
    if os.path.exists('.git'):
        sha = get_git_hash()[:7]
    elif os.path.exists(version_file):
        try:
            from basicsr.version import __version__
            sha = __version__.split('+')[-1]
        except ImportError:
            raise ImportError('Unable to get git version')
    else:
        sha = 'unknown'
    return sha

def write_version_py():
    content = "# GENERATED VERSION FILE\n# TIME: {}\n__version__ = '{}'\nshort_version = '{}'\nversion_info = ({})\n"
    sha = get_hash()
    with open('VERSION', 'r') as f:
        SHORT_VERSION = f.read().strip()
    VERSION_INFO = ', '.join([x if x.isdigit() else f'"{x}"' for x in SHORT_VERSION.split('.')])
    VERSION = SHORT_VERSION + '+' + sha
    version_file_str = content.format(time.asctime(), VERSION, SHORT_VERSION, VERSION_INFO)
    with open(version_file, 'w') as f:
        f.write(version_file_str)

def get_version():
    with open(version_file, 'r') as f:
        exec(compile(f.read(), version_file, 'exec'))
    return locals()['__version__']

def get_weights_and_parameters(task, parameters):
    if task == 'real_denoising':
        weights = os.path.join('Real_Denoising', 'pretrained_models', 'real_denoising.pth')
        if not os.path.exists(weights):
            os.system('wget https://github.com/swz30/MIRNetv2/releases/download/v1.0.0/real_denoising.pth -P Real_Denoising/pretrained_models/')
    elif task == 'super_resolution':
        weights = os.path.join('Super_Resolution', 'pretrained_models', 'sr_x4.pth')
        parameters['scale'] = 4
        if not os.path.exists(weights):
            os.system('wget https://github.com/swz30/MIRNetv2/releases/download/v1.0.0/sr_x4.pth -P Super_Resolution/pretrained_models/')
    elif task == 'contrast_enhancement':
        weights = os.path.join('Enhancement', 'pretrained_models', 'enhancement_fivek.pth')
        if not os.path.exists(weights):
            os.system('wget https://github.com/swz30/MIRNetv2/releases/download/v1.0.0/enhancement_fivek.pth -P Enhancement/pretrained_models/')
    elif task == 'lowlight_enhancement':
        weights = os.path.join('Enhancement', 'pretrained_models', 'enhancement_lol.pth')
        if not os.path.exists(weights):
            os.system('wget https://github.com/swz30/MIRNetv2/releases/download/v1.0.0/enhancement_lol.pth -P Enhancement/pretrained_models/')
    return (weights, parameters)

def train_files(file_):
    lr_file, hr_file = file_
    filename = os.path.splitext(os.path.split(lr_file)[-1])[0]
    lr_img = cv2.imread(lr_file)
    hr_img = cv2.imread(hr_file)
    num_patch = 0
    w, h = lr_img.shape[:2]
    if w > p_max and h > p_max:
        w1 = list(np.arange(0, w - patch_size, patch_size - overlap, dtype=np.int))
        h1 = list(np.arange(0, h - patch_size, patch_size - overlap, dtype=np.int))
        w1.append(w - patch_size)
        h1.append(h - patch_size)
        for i in w1:
            for j in h1:
                num_patch += 1
                lr_patch = lr_img[i:i + patch_size, j:j + patch_size, :]
                hr_patch = hr_img[i:i + patch_size, j:j + patch_size, :]
                lr_savename = os.path.join(lr_tar, filename + '-' + str(num_patch) + '.png')
                hr_savename = os.path.join(hr_tar, filename + '-' + str(num_patch) + '.png')
                cv2.imwrite(lr_savename, lr_patch)
                cv2.imwrite(hr_savename, hr_patch)
    else:
        lr_savename = os.path.join(lr_tar, filename + '.png')
        hr_savename = os.path.join(hr_tar, filename + '.png')
        cv2.imwrite(lr_savename, lr_img)
        cv2.imwrite(hr_savename, hr_img)

def parse(opt_path, is_train=True):
    """Parse option file.

    Args:
        opt_path (str): Option file path.
        is_train (str): Indicate whether in training or not. Default: True.

    Returns:
        (dict): Options.
    """
    with open(opt_path, mode='r') as f:
        Loader, _ = ordered_yaml()
        opt = yaml.load(f, Loader=Loader)
    opt['is_train'] = is_train
    for phase, dataset in opt['datasets'].items():
        phase = phase.split('_')[0]
        dataset['phase'] = phase
        if 'scale' in opt:
            dataset['scale'] = opt['scale']
        if dataset.get('dataroot_gt') is not None:
            dataset['dataroot_gt'] = osp.expanduser(dataset['dataroot_gt'])
        if dataset.get('dataroot_lq') is not None:
            dataset['dataroot_lq'] = osp.expanduser(dataset['dataroot_lq'])
    for key, val in opt['path'].items():
        if val is not None and ('resume_state' in key or 'pretrain_network' in key):
            opt['path'][key] = osp.expanduser(val)
    opt['path']['root'] = osp.abspath(osp.join(__file__, osp.pardir, osp.pardir, osp.pardir))
    if is_train:
        experiments_root = osp.join(opt['path']['root'], 'experiments', opt['name'])
        opt['path']['experiments_root'] = experiments_root
        opt['path']['models'] = osp.join(experiments_root, 'models')
        opt['path']['training_states'] = osp.join(experiments_root, 'training_states')
        opt['path']['log'] = experiments_root
        opt['path']['visualization'] = osp.join(experiments_root, 'visualization')
        if 'debug' in opt['name']:
            if 'val' in opt:
                opt['val']['val_freq'] = 8
            opt['logger']['print_freq'] = 1
            opt['logger']['save_checkpoint_freq'] = 8
    else:
        results_root = osp.join(opt['path']['root'], 'results', opt['name'])
        opt['path']['results_root'] = results_root
        opt['path']['log'] = results_root
        opt['path']['visualization'] = osp.join(results_root, 'visualization')
    return opt

class MemcachedBackend(BaseStorageBackend):
    """Memcached storage backend.

    Attributes:
        server_list_cfg (str): Config file for memcached server list.
        client_cfg (str): Config file for memcached client.
        sys_path (str | None): Additional path to be appended to `sys.path`.
            Default: None.
    """

    def __init__(self, server_list_cfg, client_cfg, sys_path=None):
        if sys_path is not None:
            import sys
            sys.path.append(sys_path)
        try:
            import mc
        except ImportError:
            raise ImportError('Please install memcached to enable MemcachedBackend.')
        self.server_list_cfg = server_list_cfg
        self.client_cfg = client_cfg
        self._client = mc.MemcachedClient.GetInstance(self.server_list_cfg, self.client_cfg)
        self._mc_buffer = mc.pyvector()

    def get(self, filepath):
        filepath = str(filepath)
        import mc
        self._client.Get(filepath, self._mc_buffer)
        value_buf = mc.ConvertBuffer(self._mc_buffer)
        return value_buf

    def get_text(self, filepath):
        raise NotImplementedError

def get(self, filepath):
    filepath = str(filepath)
    import mc
    self._client.Get(filepath, self._mc_buffer)
    value_buf = mc.ConvertBuffer(self._mc_buffer)
    return value_buf

class HardDiskBackend(BaseStorageBackend):
    """Raw hard disks storage backend."""

    def get(self, filepath):
        filepath = str(filepath)
        with open(filepath, 'rb') as f:
            value_buf = f.read()
        return value_buf

    def get_text(self, filepath):
        filepath = str(filepath)
        with open(filepath, 'r') as f:
            value_buf = f.read()
        return value_buf

def get(self, filepath):
    filepath = str(filepath)
    with open(filepath, 'rb') as f:
        value_buf = f.read()
    return value_buf

def get_text(self, filepath):
    filepath = str(filepath)
    with open(filepath, 'r') as f:
        value_buf = f.read()
    return value_buf

class LmdbBackend(BaseStorageBackend):
    """Lmdb storage backend.

    Args:
        db_paths (str | list[str]): Lmdb database paths.
        client_keys (str | list[str]): Lmdb client keys. Default: 'default'.
        readonly (bool, optional): Lmdb environment parameter. If True,
            disallow any write operations. Default: True.
        lock (bool, optional): Lmdb environment parameter. If False, when
            concurrent access occurs, do not lock the database. Default: False.
        readahead (bool, optional): Lmdb environment parameter. If False,
            disable the OS filesystem readahead mechanism, which may improve
            random read performance when a database is larger than RAM.
            Default: False.

    Attributes:
        db_paths (list): Lmdb database path.
        _client (list): A list of several lmdb envs.
    """

    def __init__(self, db_paths, client_keys='default', readonly=True, lock=False, readahead=False, **kwargs):
        try:
            import lmdb
        except ImportError:
            raise ImportError('Please install lmdb to enable LmdbBackend.')
        if isinstance(client_keys, str):
            client_keys = [client_keys]
        if isinstance(db_paths, list):
            self.db_paths = [str(v) for v in db_paths]
        elif isinstance(db_paths, str):
            self.db_paths = [str(db_paths)]
        assert len(client_keys) == len(self.db_paths), f'client_keys and db_paths should have the same length, but received {len(client_keys)} and {len(self.db_paths)}.'
        self._client = {}
        for client, path in zip(client_keys, self.db_paths):
            self._client[client] = lmdb.open(path, readonly=readonly, lock=lock, readahead=readahead, map_size=8 * 1024 * 10485760, **kwargs)

    def get(self, filepath, client_key):
        """Get values according to the filepath from one lmdb named client_key.

        Args:
            filepath (str | obj:`Path`): Here, filepath is the lmdb key.
            client_key (str): Used for distinguishing differnet lmdb envs.
        """
        filepath = str(filepath)
        assert client_key in self._client, f'client_key {client_key} is not in lmdb clients.'
        client = self._client[client_key]
        with client.begin(write=False) as txn:
            value_buf = txn.get(filepath.encode('ascii'))
        return value_buf

    def get_text(self, filepath):
        raise NotImplementedError

def __init__(self, db_paths, client_keys='default', readonly=True, lock=False, readahead=False, **kwargs):
    try:
        import lmdb
    except ImportError:
        raise ImportError('Please install lmdb to enable LmdbBackend.')
    if isinstance(client_keys, str):
        client_keys = [client_keys]
    if isinstance(db_paths, list):
        self.db_paths = [str(v) for v in db_paths]
    elif isinstance(db_paths, str):
        self.db_paths = [str(db_paths)]
    assert len(client_keys) == len(self.db_paths), f'client_keys and db_paths should have the same length, but received {len(client_keys)} and {len(self.db_paths)}.'
    self._client = {}
    for client, path in zip(client_keys, self.db_paths):
        self._client[client] = lmdb.open(path, readonly=readonly, lock=lock, readahead=readahead, map_size=8 * 1024 * 10485760, **kwargs)

class LmdbMaker:
    """LMDB Maker.

    Args:
        lmdb_path (str): Lmdb save path.
        map_size (int): Map size for lmdb env. Default: 1024 ** 4, 1TB.
        batch (int): After processing batch images, lmdb commits.
            Default: 5000.
        compress_level (int): Compress level when encoding images. Default: 1.
    """

    def __init__(self, lmdb_path, map_size=1024 ** 4, batch=5000, compress_level=1):
        if not lmdb_path.endswith('.lmdb'):
            raise ValueError("lmdb_path must end with '.lmdb'.")
        if osp.exists(lmdb_path):
            print(f'Folder {lmdb_path} already exists. Exit.')
            sys.exit(1)
        self.lmdb_path = lmdb_path
        self.batch = batch
        self.compress_level = compress_level
        self.env = lmdb.open(lmdb_path, map_size=map_size)
        self.txn = self.env.begin(write=True)
        self.txt_file = open(osp.join(lmdb_path, 'meta_info.txt'), 'w')
        self.counter = 0

    def put(self, img_byte, key, img_shape):
        self.counter += 1
        key_byte = key.encode('ascii')
        self.txn.put(key_byte, img_byte)
        h, w, c = img_shape
        self.txt_file.write(f'{key}.png ({h},{w},{c}) {self.compress_level}\n')
        if self.counter % self.batch == 0:
            self.txn.commit()
            self.txn = self.env.begin(write=True)

    def close(self):
        self.txn.commit()
        self.env.close()
        self.txt_file.close()

def __init__(self, lmdb_path, map_size=1024 ** 4, batch=5000, compress_level=1):
    if not lmdb_path.endswith('.lmdb'):
        raise ValueError("lmdb_path must end with '.lmdb'.")
    if osp.exists(lmdb_path):
        print(f'Folder {lmdb_path} already exists. Exit.')
        sys.exit(1)
    self.lmdb_path = lmdb_path
    self.batch = batch
    self.compress_level = compress_level
    self.env = lmdb.open(lmdb_path, map_size=map_size)
    self.txn = self.env.begin(write=True)
    self.txt_file = open(osp.join(lmdb_path, 'meta_info.txt'), 'w')
    self.counter = 0

def prepare_keys(folder_path, suffix='png'):
    """Prepare image path list and keys for DIV2K dataset.

    Args:
        folder_path (str): Folder path.

    Returns:
        list[str]: Image path list.
        list[str]: Key list.
    """
    print('Reading image path list ...')
    img_path_list = sorted(list(scandir(folder_path, suffix=suffix, recursive=False)))
    keys = [img_path.split('.{}'.format(suffix))[0] for img_path in sorted(img_path_list)]
    return (img_path_list, keys)

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

def paired_paths_from_lmdb(folders, keys):
    """Generate paired paths from lmdb files.

    Contents of lmdb. Taking the `lq.lmdb` for example, the file structure is:

    lq.lmdb
    ├── data.mdb
    ├── lock.mdb
    ├── meta_info.txt

    The data.mdb and lock.mdb are standard lmdb files and you can refer to
    https://lmdb.readthedocs.io/en/release/ for more details.

    The meta_info.txt is a specified txt file to record the meta information
    of our datasets. It will be automatically created when preparing
    datasets by our provided dataset tools.
    Each line in the txt file records
    1)image name (with extension),
    2)image shape,
    3)compression level, separated by a white space.
    Example: `baboon.png (120,125,3) 1`

    We use the image name without extension as the lmdb key.
    Note that we use the same key for the corresponding lq and gt images.

    Args:
        folders (list[str]): A list of folder path. The order of list should
            be [input_folder, gt_folder].
        keys (list[str]): A list of keys identifying folders. The order should
            be in consistent with folders, e.g., ['lq', 'gt'].
            Note that this key is different from lmdb keys.

    Returns:
        list[str]: Returned path list.
    """
    assert len(folders) == 2, f'The len of folders should be 2 with [input_folder, gt_folder]. But got {len(folders)}'
    assert len(keys) == 2, f'The len of keys should be 2 with [input_key, gt_key]. But got {len(keys)}'
    input_folder, gt_folder = folders
    input_key, gt_key = keys
    if not (input_folder.endswith('.lmdb') and gt_folder.endswith('.lmdb')):
        raise ValueError(f'{input_key} folder and {gt_key} folder should both in lmdb formats. But received {input_key}: {input_folder}; {gt_key}: {gt_folder}')
    with open(osp.join(input_folder, 'meta_info.txt')) as fin:
        input_lmdb_keys = [line.split('.')[0] for line in fin]
    with open(osp.join(gt_folder, 'meta_info.txt')) as fin:
        gt_lmdb_keys = [line.split('.')[0] for line in fin]
    if set(input_lmdb_keys) != set(gt_lmdb_keys):
        raise ValueError(f'Keys in {input_key}_folder and {gt_key}_folder are different.')
    else:
        paths = []
        for lmdb_key in sorted(input_lmdb_keys):
            paths.append(dict([(f'{input_key}_path', lmdb_key), (f'{gt_key}_path', lmdb_key)]))
        return paths

def paired_paths_from_meta_info_file(folders, keys, meta_info_file, filename_tmpl):
    """Generate paired paths from an meta information file.

    Each line in the meta information file contains the image names and
    image shape (usually for gt), separated by a white space.

    Example of an meta information file:
    ```
    0001_s001.png (480,480,3)
    0001_s002.png (480,480,3)
    ```

    Args:
        folders (list[str]): A list of folder path. The order of list should
            be [input_folder, gt_folder].
        keys (list[str]): A list of keys identifying folders. The order should
            be in consistent with folders, e.g., ['lq', 'gt'].
        meta_info_file (str): Path to the meta information file.
        filename_tmpl (str): Template for each filename. Note that the
            template excludes the file extension. Usually the filename_tmpl is
            for files in the input folder.

    Returns:
        list[str]: Returned path list.
    """
    assert len(folders) == 2, f'The len of folders should be 2 with [input_folder, gt_folder]. But got {len(folders)}'
    assert len(keys) == 2, f'The len of keys should be 2 with [input_key, gt_key]. But got {len(keys)}'
    input_folder, gt_folder = folders
    input_key, gt_key = keys
    with open(meta_info_file, 'r') as fin:
        gt_names = [line.split(' ')[0] for line in fin]
    paths = []
    for gt_name in gt_names:
        basename, ext = osp.splitext(osp.basename(gt_name))
        input_name = f'{filename_tmpl.format(basename)}{ext}'
        input_path = osp.join(input_folder, input_name)
        gt_path = osp.join(gt_folder, gt_name)
        paths.append(dict([(f'{input_key}_path', input_path), (f'{gt_key}_path', gt_path)]))
    return paths

def paired_paths_from_folder(folders, keys, filename_tmpl):
    """Generate paired paths from folders.

    Args:
        folders (list[str]): A list of folder path. The order of list should
            be [input_folder, gt_folder].
        keys (list[str]): A list of keys identifying folders. The order should
            be in consistent with folders, e.g., ['lq', 'gt'].
        filename_tmpl (str): Template for each filename. Note that the
            template excludes the file extension. Usually the filename_tmpl is
            for files in the input folder.

    Returns:
        list[str]: Returned path list.
    """
    assert len(folders) == 2, f'The len of folders should be 2 with [input_folder, gt_folder]. But got {len(folders)}'
    assert len(keys) == 2, f'The len of keys should be 2 with [input_key, gt_key]. But got {len(keys)}'
    input_folder, gt_folder = folders
    input_key, gt_key = keys
    input_paths = list(scandir(input_folder))
    gt_paths = list(scandir(gt_folder))
    assert len(input_paths) == len(gt_paths), f'{input_key} and {gt_key} datasets have different number of images: {len(input_paths)}, {len(gt_paths)}.'
    paths = []
    for idx in range(len(gt_paths)):
        gt_path = gt_paths[idx]
        basename, ext = osp.splitext(osp.basename(gt_path))
        input_path = input_paths[idx]
        basename_input, ext_input = osp.splitext(osp.basename(input_path))
        input_name = f'{filename_tmpl.format(basename)}{ext_input}'
        input_path = osp.join(input_folder, input_name)
        assert input_name in input_paths, f'{input_name} is not in {input_key}_paths.'
        gt_path = osp.join(gt_folder, gt_path)
        paths.append(dict([(f'{input_key}_path', input_path), (f'{gt_key}_path', gt_path)]))
    return paths

def paired_DP_paths_from_folder(folders, keys, filename_tmpl):
    """Generate paired paths from folders.

    Args:
        folders (list[str]): A list of folder path. The order of list should
            be [input_folder, gt_folder].
        keys (list[str]): A list of keys identifying folders. The order should
            be in consistent with folders, e.g., ['lq', 'gt'].
        filename_tmpl (str): Template for each filename. Note that the
            template excludes the file extension. Usually the filename_tmpl is
            for files in the input folder.

    Returns:
        list[str]: Returned path list.
    """
    assert len(folders) == 3, f'The len of folders should be 3 with [inputL_folder, inputR_folder, gt_folder]. But got {len(folders)}'
    assert len(keys) == 3, f'The len of keys should be 2 with [inputL_key, inputR_key, gt_key]. But got {len(keys)}'
    inputL_folder, inputR_folder, gt_folder = folders
    inputL_key, inputR_key, gt_key = keys
    inputL_paths = list(scandir(inputL_folder))
    inputR_paths = list(scandir(inputR_folder))
    gt_paths = list(scandir(gt_folder))
    assert len(inputL_paths) == len(inputR_paths) == len(gt_paths), f'{inputL_key} and {inputR_key} and {gt_key} datasets have different number of images: {len(inputL_paths)}, {len(inputR_paths)}, {len(gt_paths)}.'
    paths = []
    for idx in range(len(gt_paths)):
        gt_path = gt_paths[idx]
        basename, ext = osp.splitext(osp.basename(gt_path))
        inputL_path = inputL_paths[idx]
        basename_input, ext_input = osp.splitext(osp.basename(inputL_path))
        inputL_name = f'{filename_tmpl.format(basename)}{ext_input}'
        inputL_path = osp.join(inputL_folder, inputL_name)
        assert inputL_name in inputL_paths, f'{inputL_name} is not in {inputL_key}_paths.'
        inputR_path = inputR_paths[idx]
        basename_input, ext_input = osp.splitext(osp.basename(inputR_path))
        inputR_name = f'{filename_tmpl.format(basename)}{ext_input}'
        inputR_path = osp.join(inputR_folder, inputR_name)
        assert inputR_name in inputR_paths, f'{inputR_name} is not in {inputR_key}_paths.'
        gt_path = osp.join(gt_folder, gt_path)
        paths.append(dict([(f'{inputL_key}_path', inputL_path), (f'{inputR_key}_path', inputR_path), (f'{gt_key}_path', gt_path)]))
    return paths

def paths_from_folder(folder):
    """Generate paths from folder.

    Args:
        folder (str): Folder path.

    Returns:
        list[str]: Returned path list.
    """
    paths = list(scandir(folder))
    paths = [osp.join(folder, path) for path in paths]
    return paths

def paths_from_lmdb(folder):
    """Generate paths from lmdb.

    Args:
        folder (str): Folder path.

    Returns:
        list[str]: Returned path list.
    """
    if not folder.endswith('.lmdb'):
        raise ValueError(f'Folder {folder}folder should in lmdb format.')
    with open(osp.join(folder, 'meta_info.txt')) as fin:
        paths = [line.split('.')[0] for line in fin]
    return paths

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

class VideoTestDataset(data.Dataset):
    """Video test dataset.

    Supported datasets: Vid4, REDS4, REDSofficial.
    More generally, it supports testing dataset with following structures:

    dataroot
    ├── subfolder1
        ├── frame000
        ├── frame001
        ├── ...
    ├── subfolder1
        ├── frame000
        ├── frame001
        ├── ...
    ├── ...

    For testing datasets, there is no need to prepare LMDB files.

    Args:
        opt (dict): Config for train dataset. It contains the following keys:
            dataroot_gt (str): Data root path for gt.
            dataroot_lq (str): Data root path for lq.
            io_backend (dict): IO backend type and other kwarg.
            cache_data (bool): Whether to cache testing datasets.
            name (str): Dataset name.
            meta_info_file (str): The path to the file storing the list of test
                folders. If not provided, all the folders in the dataroot will
                be used.
            num_frame (int): Window size for input frames.
            padding (str): Padding mode.
    """

    def __init__(self, opt):
        super(VideoTestDataset, self).__init__()
        self.opt = opt
        self.cache_data = opt['cache_data']
        self.gt_root, self.lq_root = (opt['dataroot_gt'], opt['dataroot_lq'])
        self.data_info = {'lq_path': [], 'gt_path': [], 'folder': [], 'idx': [], 'border': []}
        self.file_client = None
        self.io_backend_opt = opt['io_backend']
        assert self.io_backend_opt['type'] != 'lmdb', 'No need to use lmdb during validation/test.'
        logger = get_root_logger()
        logger.info(f'Generate data info for VideoTestDataset - {opt['name']}')
        self.imgs_lq, self.imgs_gt = ({}, {})
        if 'meta_info_file' in opt:
            with open(opt['meta_info_file'], 'r') as fin:
                subfolders = [line.split(' ')[0] for line in fin]
                subfolders_lq = [osp.join(self.lq_root, key) for key in subfolders]
                subfolders_gt = [osp.join(self.gt_root, key) for key in subfolders]
        else:
            subfolders_lq = sorted(glob.glob(osp.join(self.lq_root, '*')))
            subfolders_gt = sorted(glob.glob(osp.join(self.gt_root, '*')))
        if opt['name'].lower() in ['vid4', 'reds4', 'redsofficial']:
            for subfolder_lq, subfolder_gt in zip(subfolders_lq, subfolders_gt):
                subfolder_name = osp.basename(subfolder_lq)
                img_paths_lq = sorted(list(scandir(subfolder_lq, full_path=True)))
                img_paths_gt = sorted(list(scandir(subfolder_gt, full_path=True)))
                max_idx = len(img_paths_lq)
                assert max_idx == len(img_paths_gt), f'Different number of images in lq ({max_idx}) and gt folders ({len(img_paths_gt)})'
                self.data_info['lq_path'].extend(img_paths_lq)
                self.data_info['gt_path'].extend(img_paths_gt)
                self.data_info['folder'].extend([subfolder_name] * max_idx)
                for i in range(max_idx):
                    self.data_info['idx'].append(f'{i}/{max_idx}')
                border_l = [0] * max_idx
                for i in range(self.opt['num_frame'] // 2):
                    border_l[i] = 1
                    border_l[max_idx - i - 1] = 1
                self.data_info['border'].extend(border_l)
                if self.cache_data:
                    logger.info(f'Cache {subfolder_name} for VideoTestDataset...')
                    self.imgs_lq[subfolder_name] = read_img_seq(img_paths_lq)
                    self.imgs_gt[subfolder_name] = read_img_seq(img_paths_gt)
                else:
                    self.imgs_lq[subfolder_name] = img_paths_lq
                    self.imgs_gt[subfolder_name] = img_paths_gt
        else:
            raise ValueError(f'Non-supported video test dataset: {type(opt['name'])}')

    def __getitem__(self, index):
        folder = self.data_info['folder'][index]
        idx, max_idx = self.data_info['idx'][index].split('/')
        idx, max_idx = (int(idx), int(max_idx))
        border = self.data_info['border'][index]
        lq_path = self.data_info['lq_path'][index]
        select_idx = generate_frame_indices(idx, max_idx, self.opt['num_frame'], padding=self.opt['padding'])
        if self.cache_data:
            imgs_lq = self.imgs_lq[folder].index_select(0, torch.LongTensor(select_idx))
            img_gt = self.imgs_gt[folder][idx]
        else:
            img_paths_lq = [self.imgs_lq[folder][i] for i in select_idx]
            imgs_lq = read_img_seq(img_paths_lq)
            img_gt = read_img_seq([self.imgs_gt[folder][idx]])
            img_gt.squeeze_(0)
        return {'lq': imgs_lq, 'gt': img_gt, 'folder': folder, 'idx': self.data_info['idx'][index], 'border': border, 'lq_path': lq_path}

    def __len__(self):
        return len(self.data_info['gt_path'])

def __init__(self, opt):
    super(VideoTestDataset, self).__init__()
    self.opt = opt
    self.cache_data = opt['cache_data']
    self.gt_root, self.lq_root = (opt['dataroot_gt'], opt['dataroot_lq'])
    self.data_info = {'lq_path': [], 'gt_path': [], 'folder': [], 'idx': [], 'border': []}
    self.file_client = None
    self.io_backend_opt = opt['io_backend']
    assert self.io_backend_opt['type'] != 'lmdb', 'No need to use lmdb during validation/test.'
    logger = get_root_logger()
    logger.info(f'Generate data info for VideoTestDataset - {opt['name']}')
    self.imgs_lq, self.imgs_gt = ({}, {})
    if 'meta_info_file' in opt:
        with open(opt['meta_info_file'], 'r') as fin:
            subfolders = [line.split(' ')[0] for line in fin]
            subfolders_lq = [osp.join(self.lq_root, key) for key in subfolders]
            subfolders_gt = [osp.join(self.gt_root, key) for key in subfolders]
    else:
        subfolders_lq = sorted(glob.glob(osp.join(self.lq_root, '*')))
        subfolders_gt = sorted(glob.glob(osp.join(self.gt_root, '*')))
    if opt['name'].lower() in ['vid4', 'reds4', 'redsofficial']:
        for subfolder_lq, subfolder_gt in zip(subfolders_lq, subfolders_gt):
            subfolder_name = osp.basename(subfolder_lq)
            img_paths_lq = sorted(list(scandir(subfolder_lq, full_path=True)))
            img_paths_gt = sorted(list(scandir(subfolder_gt, full_path=True)))
            max_idx = len(img_paths_lq)
            assert max_idx == len(img_paths_gt), f'Different number of images in lq ({max_idx}) and gt folders ({len(img_paths_gt)})'
            self.data_info['lq_path'].extend(img_paths_lq)
            self.data_info['gt_path'].extend(img_paths_gt)
            self.data_info['folder'].extend([subfolder_name] * max_idx)
            for i in range(max_idx):
                self.data_info['idx'].append(f'{i}/{max_idx}')
            border_l = [0] * max_idx
            for i in range(self.opt['num_frame'] // 2):
                border_l[i] = 1
                border_l[max_idx - i - 1] = 1
            self.data_info['border'].extend(border_l)
            if self.cache_data:
                logger.info(f'Cache {subfolder_name} for VideoTestDataset...')
                self.imgs_lq[subfolder_name] = read_img_seq(img_paths_lq)
                self.imgs_gt[subfolder_name] = read_img_seq(img_paths_gt)
            else:
                self.imgs_lq[subfolder_name] = img_paths_lq
                self.imgs_gt[subfolder_name] = img_paths_gt
    else:
        raise ValueError(f'Non-supported video test dataset: {type(opt['name'])}')

class BaseModel:
    """Base model."""

    def __init__(self, opt):
        self.opt = opt
        self.device = torch.device('cuda' if opt['num_gpu'] != 0 else 'cpu')
        self.is_train = opt['is_train']
        self.schedulers = []
        self.optimizers = []

    def feed_data(self, data):
        pass

    def optimize_parameters(self):
        pass

    def get_current_visuals(self):
        pass

    def save(self, epoch, current_iter):
        """Save networks and training state."""
        pass

    def validation(self, dataloader, current_iter, tb_logger, save_img=False, rgb2bgr=True, use_image=True):
        """Validation function.

        Args:
            dataloader (torch.utils.data.DataLoader): Validation dataloader.
            current_iter (int): Current iteration.
            tb_logger (tensorboard logger): Tensorboard logger.
            save_img (bool): Whether to save images. Default: False.
            rgb2bgr (bool): Whether to save images using rgb2bgr. Default: True
            use_image (bool): Whether to use saved images to compute metrics (PSNR, SSIM), if not, then use data directly from network' output. Default: True
        """
        if self.opt['dist']:
            return self.dist_validation(dataloader, current_iter, tb_logger, save_img, rgb2bgr, use_image)
        else:
            return self.nondist_validation(dataloader, current_iter, tb_logger, save_img, rgb2bgr, use_image)

    def model_ema(self, decay=0.999):
        net_g = self.get_bare_model(self.net_g)
        net_g_params = dict(net_g.named_parameters())
        net_g_ema_params = dict(self.net_g_ema.named_parameters())
        for k in net_g_ema_params.keys():
            net_g_ema_params[k].data.mul_(decay).add_(net_g_params[k].data, alpha=1 - decay)

    def get_current_log(self):
        return self.log_dict

    def model_to_device(self, net):
        """Model to device. It also warps models with DistributedDataParallel
        or DataParallel.

        Args:
            net (nn.Module)
        """
        net = net.to(self.device)
        if self.opt['dist']:
            find_unused_parameters = self.opt.get('find_unused_parameters', False)
            net = DistributedDataParallel(net, device_ids=[torch.cuda.current_device()], find_unused_parameters=find_unused_parameters)
        elif self.opt['num_gpu'] > 1:
            net = DataParallel(net)
        return net

    def setup_schedulers(self):
        """Set up schedulers."""
        train_opt = self.opt['train']
        scheduler_type = train_opt['scheduler'].pop('type')
        if scheduler_type in ['MultiStepLR', 'MultiStepRestartLR']:
            for optimizer in self.optimizers:
                self.schedulers.append(lr_scheduler.MultiStepRestartLR(optimizer, **train_opt['scheduler']))
        elif scheduler_type == 'CosineAnnealingRestartLR':
            for optimizer in self.optimizers:
                self.schedulers.append(lr_scheduler.CosineAnnealingRestartLR(optimizer, **train_opt['scheduler']))
        elif scheduler_type == 'CosineAnnealingWarmupRestarts':
            for optimizer in self.optimizers:
                self.schedulers.append(lr_scheduler.CosineAnnealingWarmupRestarts(optimizer, **train_opt['scheduler']))
        elif scheduler_type == 'CosineAnnealingRestartCyclicLR':
            for optimizer in self.optimizers:
                self.schedulers.append(lr_scheduler.CosineAnnealingRestartCyclicLR(optimizer, **train_opt['scheduler']))
        elif scheduler_type == 'TrueCosineAnnealingLR':
            print('..', 'cosineannealingLR')
            for optimizer in self.optimizers:
                self.schedulers.append(torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, **train_opt['scheduler']))
        elif scheduler_type == 'CosineAnnealingLRWithRestart':
            print('..', 'CosineAnnealingLR_With_Restart')
            for optimizer in self.optimizers:
                self.schedulers.append(lr_scheduler.CosineAnnealingLRWithRestart(optimizer, **train_opt['scheduler']))
        elif scheduler_type == 'LinearLR':
            for optimizer in self.optimizers:
                self.schedulers.append(lr_scheduler.LinearLR(optimizer, train_opt['total_iter']))
        elif scheduler_type == 'VibrateLR':
            for optimizer in self.optimizers:
                self.schedulers.append(lr_scheduler.VibrateLR(optimizer, train_opt['total_iter']))
        else:
            raise NotImplementedError(f'Scheduler {scheduler_type} is not implemented yet.')

    def get_bare_model(self, net):
        """Get bare model, especially under wrapping with
        DistributedDataParallel or DataParallel.
        """
        if isinstance(net, (DataParallel, DistributedDataParallel)):
            net = net.module
        return net

    @master_only
    def print_network(self, net):
        """Print the str and parameter number of a network.

        Args:
            net (nn.Module)
        """
        if isinstance(net, (DataParallel, DistributedDataParallel)):
            net_cls_str = f'{net.__class__.__name__} - {net.module.__class__.__name__}'
        else:
            net_cls_str = f'{net.__class__.__name__}'
        net = self.get_bare_model(net)
        net_str = str(net)
        net_params = sum(map(lambda x: x.numel(), net.parameters()))
        logger.info(f'Network: {net_cls_str}, with parameters: {net_params:,d}')
        logger.info(net_str)

    def _set_lr(self, lr_groups_l):
        """Set learning rate for warmup.

        Args:
            lr_groups_l (list): List for lr_groups, each for an optimizer.
        """
        for optimizer, lr_groups in zip(self.optimizers, lr_groups_l):
            for param_group, lr in zip(optimizer.param_groups, lr_groups):
                param_group['lr'] = lr

    def _get_init_lr(self):
        """Get the initial lr, which is set by the scheduler.
        """
        init_lr_groups_l = []
        for optimizer in self.optimizers:
            init_lr_groups_l.append([v['initial_lr'] for v in optimizer.param_groups])
        return init_lr_groups_l

    def update_learning_rate(self, current_iter, warmup_iter=-1):
        """Update learning rate.

        Args:
            current_iter (int): Current iteration.
            warmup_iter (int)： Warmup iter numbers. -1 for no warmup.
                Default： -1.
        """
        if current_iter > 1:
            for scheduler in self.schedulers:
                scheduler.step()
        if current_iter < warmup_iter:
            init_lr_g_l = self._get_init_lr()
            warm_up_lr_l = []
            for init_lr_g in init_lr_g_l:
                warm_up_lr_l.append([v / warmup_iter * current_iter for v in init_lr_g])
            self._set_lr(warm_up_lr_l)

    def get_current_learning_rate(self):
        return [param_group['lr'] for param_group in self.optimizers[0].param_groups]

    @master_only
    def save_network(self, net, net_label, current_iter, param_key='params'):
        """Save networks.

        Args:
            net (nn.Module | list[nn.Module]): Network(s) to be saved.
            net_label (str): Network label.
            current_iter (int): Current iter number.
            param_key (str | list[str]): The parameter key(s) to save network.
                Default: 'params'.
        """
        if current_iter == -1:
            current_iter = 'latest'
        save_filename = f'{net_label}_{current_iter}.pth'
        save_path = os.path.join(self.opt['path']['models'], save_filename)
        net = net if isinstance(net, list) else [net]
        param_key = param_key if isinstance(param_key, list) else [param_key]
        assert len(net) == len(param_key), 'The lengths of net and param_key should be the same.'
        save_dict = {}
        for net_, param_key_ in zip(net, param_key):
            net_ = self.get_bare_model(net_)
            state_dict = net_.state_dict()
            for key, param in state_dict.items():
                if key.startswith('module.'):
                    key = key[7:]
                state_dict[key] = param.cpu()
            save_dict[param_key_] = state_dict
        torch.save(save_dict, save_path)

    def _print_different_keys_loading(self, crt_net, load_net, strict=True):
        """Print keys with differnet name or different size when loading models.

        1. Print keys with differnet names.
        2. If strict=False, print the same key but with different tensor size.
            It also ignore these keys with different sizes (not load).

        Args:
            crt_net (torch model): Current network.
            load_net (dict): Loaded network.
            strict (bool): Whether strictly loaded. Default: True.
        """
        crt_net = self.get_bare_model(crt_net)
        crt_net = crt_net.state_dict()
        crt_net_keys = set(crt_net.keys())
        load_net_keys = set(load_net.keys())
        if crt_net_keys != load_net_keys:
            logger.warning('Current net - loaded net:')
            for v in sorted(list(crt_net_keys - load_net_keys)):
                logger.warning(f'  {v}')
            logger.warning('Loaded net - current net:')
            for v in sorted(list(load_net_keys - crt_net_keys)):
                logger.warning(f'  {v}')
        if not strict:
            common_keys = crt_net_keys & load_net_keys
            for k in common_keys:
                if crt_net[k].size() != load_net[k].size():
                    logger.warning(f'Size different, ignore [{k}]: crt_net: {crt_net[k].shape}; load_net: {load_net[k].shape}')
                    load_net[k + '.ignore'] = load_net.pop(k)

    def load_network(self, net, load_path, strict=True, param_key='params'):
        """Load network.

        Args:
            load_path (str): The path of networks to be loaded.
            net (nn.Module): Network.
            strict (bool): Whether strictly loaded.
            param_key (str): The parameter key of loaded network. If set to
                None, use the root 'path'.
                Default: 'params'.
        """
        net = self.get_bare_model(net)
        logger.info(f'Loading {net.__class__.__name__} model from {load_path}.')
        load_net = torch.load(load_path, map_location=lambda storage, loc: storage)
        if param_key is not None:
            if param_key not in load_net and 'params' in load_net:
                param_key = 'params'
                logger.info('Loading: params_ema does not exist, use params.')
            load_net = load_net[param_key]
        print(' load net keys', load_net.keys)
        for k, v in deepcopy(load_net).items():
            if k.startswith('module.'):
                load_net[k[7:]] = v
                load_net.pop(k)
        self._print_different_keys_loading(net, load_net, strict)
        net.load_state_dict(load_net, strict=strict)

    @master_only
    def save_training_state(self, epoch, current_iter):
        """Save training states during training, which will be used for
        resuming.

        Args:
            epoch (int): Current epoch.
            current_iter (int): Current iteration.
        """
        if current_iter != -1:
            state = {'epoch': epoch, 'iter': current_iter, 'optimizers': [], 'schedulers': []}
            for o in self.optimizers:
                state['optimizers'].append(o.state_dict())
            for s in self.schedulers:
                state['schedulers'].append(s.state_dict())
            save_filename = f'{current_iter}.state'
            save_path = os.path.join(self.opt['path']['training_states'], save_filename)
            torch.save(state, save_path)

    def resume_training(self, resume_state):
        """Reload the optimizers and schedulers for resumed training.

        Args:
            resume_state (dict): Resume state.
        """
        resume_optimizers = resume_state['optimizers']
        resume_schedulers = resume_state['schedulers']
        assert len(resume_optimizers) == len(self.optimizers), 'Wrong lengths of optimizers'
        assert len(resume_schedulers) == len(self.schedulers), 'Wrong lengths of schedulers'
        for i, o in enumerate(resume_optimizers):
            self.optimizers[i].load_state_dict(o)
        for i, s in enumerate(resume_schedulers):
            self.schedulers[i].load_state_dict(s)

    def reduce_loss_dict(self, loss_dict):
        """reduce loss dict.

        In distributed training, it averages the losses among different GPUs .

        Args:
            loss_dict (OrderedDict): Loss dict.
        """
        with torch.no_grad():
            if self.opt['dist']:
                keys = []
                losses = []
                for name, value in loss_dict.items():
                    keys.append(name)
                    losses.append(value)
                losses = torch.stack(losses, 0)
                torch.distributed.reduce(losses, dst=0)
                if self.opt['rank'] == 0:
                    losses /= self.opt['world_size']
                loss_dict = {key: loss for key, loss in zip(keys, losses)}
            log_dict = OrderedDict()
            for name, value in loss_dict.items():
                log_dict[name] = value.mean().item()
            return log_dict

def _set_lr(self, lr_groups_l):
    """Set learning rate for warmup.

        Args:
            lr_groups_l (list): List for lr_groups, each for an optimizer.
        """
    for optimizer, lr_groups in zip(self.optimizers, lr_groups_l):
        for param_group, lr in zip(optimizer.param_groups, lr_groups):
            param_group['lr'] = lr

def train_files(file_):
    lrL_file, lrR_file, lrC_file, hrC_file = file_
    filename = os.path.splitext(os.path.split(lrC_file)[-1])[0]
    lrL_img = cv2.imread(lrL_file, -1)
    lrR_img = cv2.imread(lrR_file, -1)
    lrC_img = cv2.imread(lrC_file, -1)
    hrC_img = cv2.imread(hrC_file, -1)
    lrC_patches, hrC_patches, lrL_patches, lrR_patches = slice_stride(lrC_img, hrC_img, lrL_img, lrR_img)
    lrC_patches, hrC_patches, lrL_patches, lrR_patches = filter_patch_sharpness(lrC_patches, hrC_patches, lrL_patches, lrR_patches)
    num_patch = 0
    for lrC_patch, hrC_patch, lrL_patch, lrR_patch in zip(lrC_patches, hrC_patches, lrL_patches, lrR_patches):
        num_patch += 1
        lrL_savename = os.path.join(lrL_tar, filename + '-' + str(num_patch) + '.png')
        lrR_savename = os.path.join(lrR_tar, filename + '-' + str(num_patch) + '.png')
        lrC_savename = os.path.join(lrC_tar, filename + '-' + str(num_patch) + '.png')
        hrC_savename = os.path.join(hrC_tar, filename + '-' + str(num_patch) + '.png')
        cv2.imwrite(lrL_savename, lrL_patch)
        cv2.imwrite(lrR_savename, lrR_patch)
        cv2.imwrite(lrC_savename, lrC_patch)
        cv2.imwrite(hrC_savename, hrC_patch)

def val_files(file_):
    lrL_file, lrR_file, lrC_file, hrC_file = file_
    filename = os.path.splitext(os.path.split(lrC_file)[-1])[0]
    lrL_savename = os.path.join(lrL_tar, filename + '.png')
    lrR_savename = os.path.join(lrR_tar, filename + '.png')
    lrC_savename = os.path.join(lrC_tar, filename + '.png')
    hrC_savename = os.path.join(hrC_tar, filename + '.png')
    lrL_img = cv2.imread(lrL_file, -1)
    lrR_img = cv2.imread(lrR_file, -1)
    lrC_img = cv2.imread(lrC_file, -1)
    hrC_img = cv2.imread(hrC_file, -1)
    w, h = lrC_img.shape[:2]
    i = (w - val_patch_size) // 2
    j = (h - val_patch_size) // 2
    lrL_patch = lrL_img[i:i + val_patch_size, j:j + val_patch_size, :]
    lrR_patch = lrR_img[i:i + val_patch_size, j:j + val_patch_size, :]
    lrC_patch = lrC_img[i:i + val_patch_size, j:j + val_patch_size, :]
    hrC_patch = hrC_img[i:i + val_patch_size, j:j + val_patch_size, :]
    cv2.imwrite(lrL_savename, lrL_patch)
    cv2.imwrite(lrR_savename, lrR_patch)
    cv2.imwrite(lrC_savename, lrC_patch)
    cv2.imwrite(hrC_savename, hrC_patch)

def train_files(file_):
    lr_file, hr_file = file_
    filename = os.path.splitext(os.path.split(lr_file)[-1])[0]
    lr_img = cv2.imread(lr_file)
    hr_img = cv2.imread(hr_file)
    num_patch = 0
    w, h = lr_img.shape[:2]
    if w > p_max and h > p_max:
        w1 = list(np.arange(0, w - patch_size, patch_size - overlap, dtype=int))
        h1 = list(np.arange(0, h - patch_size, patch_size - overlap, dtype=int))
        w1.append(w - patch_size)
        h1.append(h - patch_size)
        for i in w1:
            for j in h1:
                num_patch += 1
                lr_patch = lr_img[i:i + patch_size, j:j + patch_size, :]
                hr_patch = hr_img[i:i + patch_size, j:j + patch_size, :]
                lr_savename = os.path.join(lr_tar, filename + '-' + str(num_patch) + '.png')
                hr_savename = os.path.join(hr_tar, filename + '-' + str(num_patch) + '.png')
                cv2.imwrite(lr_savename, lr_patch)
                cv2.imwrite(hr_savename, hr_patch)
    else:
        lr_savename = os.path.join(lr_tar, filename + '.png')
        hr_savename = os.path.join(hr_tar, filename + '.png')
        cv2.imwrite(lr_savename, lr_img)
        cv2.imwrite(hr_savename, hr_img)

def save_files(file_):
    lr_file, hr_file = file_
    filename = os.path.splitext(os.path.split(lr_file)[-1])[0]
    lr_img = cv2.imread(lr_file)
    hr_img = cv2.imread(hr_file)
    num_patch = 0
    w, h = lr_img.shape[:2]
    if w > p_max and h > p_max:
        w1 = list(np.arange(0, w - patch_size, patch_size - overlap, dtype=np.int))
        h1 = list(np.arange(0, h - patch_size, patch_size - overlap, dtype=np.int))
        w1.append(w - patch_size)
        h1.append(h - patch_size)
        for i in w1:
            for j in h1:
                num_patch += 1
                lr_patch = lr_img[i:i + patch_size, j:j + patch_size, :]
                hr_patch = hr_img[i:i + patch_size, j:j + patch_size, :]
                lr_savename = os.path.join(lr_tar, filename + '-' + str(num_patch) + '.png')
                hr_savename = os.path.join(hr_tar, filename + '-' + str(num_patch) + '.png')
                cv2.imwrite(lr_savename, lr_patch)
                cv2.imwrite(hr_savename, hr_patch)
    else:
        lr_savename = os.path.join(lr_tar, filename + '.png')
        hr_savename = os.path.join(hr_tar, filename + '.png')
        cv2.imwrite(lr_savename, lr_img)
        cv2.imwrite(hr_savename, hr_img)

