# Cluster 0

def file_not_found(filename):
    print("\nError! Can't read calibration file, does %s exist?" % filename)
    exit()

def check_font(font='Arial.ttf', size=10):
    font = Path(font)
    font = font if font.exists() else CONFIG_DIR / font.name
    try:
        return ImageFont.truetype(str(font) if font.exists() else font.name, size)
    except Exception as e:
        url = 'https://ultralytics.com/assets/' + font.name
        print(f'Downloading {url} to {font}...')
        torch.hub.download_url_to_file(url, str(font), progress=False)
        try:
            return ImageFont.truetype(str(font), size)
        except TypeError:
            check_requirements('Pillow>=8.4.0')

def get_hash(paths):
    size = sum((os.path.getsize(p) for p in paths if os.path.exists(p)))
    h = hashlib.md5(str(size).encode())
    h.update(''.join(paths).encode())
    return h.hexdigest()

class LoadImages:

    def __init__(self, path, img_size=640, stride=32, auto=True):
        p = str(Path(path).resolve())
        if '*' in p:
            files = sorted(glob.glob(p, recursive=True))
        elif os.path.isdir(p):
            files = sorted(glob.glob(os.path.join(p, '*.*')))
        elif os.path.isfile(p):
            files = [p]
        else:
            raise Exception(f'ERROR: {p} does not exist')
        images = [x for x in files if x.split('.')[-1].lower() in IMG_FORMATS]
        videos = [x for x in files if x.split('.')[-1].lower() in VID_FORMATS]
        ni, nv = (len(images), len(videos))
        self.img_size = img_size
        self.stride = stride
        self.files = images + videos
        self.nf = ni + nv
        self.video_flag = [False] * ni + [True] * nv
        self.mode = 'image'
        self.auto = auto
        if any(videos):
            self.new_video(videos[0])
        else:
            self.cap = None
        assert self.nf > 0, f'No images or videos found in {p}. Supported formats are:\nimages: {IMG_FORMATS}\nvideos: {VID_FORMATS}'

    def __iter__(self):
        self.count = 0
        return self

    def __next__(self):
        if self.count == self.nf:
            raise StopIteration
        path = self.files[self.count]
        if self.video_flag[self.count]:
            self.mode = 'video'
            ret_val, img0 = self.cap.read()
            while not ret_val:
                self.count += 1
                self.cap.release()
                if self.count == self.nf:
                    raise StopIteration
                else:
                    path = self.files[self.count]
                    self.new_video(path)
                    ret_val, img0 = self.cap.read()
            self.frame += 1
            s = f'video {self.count + 1}/{self.nf} ({self.frame}/{self.frames}) {path}: '
        else:
            self.count += 1
            img0 = cv2.imread(path)
            assert img0 is not None, f'Image Not Found {path}'
            s = f'image {self.count}/{self.nf} {path}: '
        img = letterbox(img0, self.img_size, stride=self.stride, auto=self.auto)[0]
        img = img.transpose((2, 0, 1))[::-1]
        img = np.ascontiguousarray(img)
        return (path, img, img0, self.cap, s)

    def new_video(self, path):
        self.frame = 0
        self.cap = cv2.VideoCapture(path)
        self.frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

    def __len__(self):
        return self.nf

def __init__(self, path, img_size=640, stride=32, auto=True):
    p = str(Path(path).resolve())
    if '*' in p:
        files = sorted(glob.glob(p, recursive=True))
    elif os.path.isdir(p):
        files = sorted(glob.glob(os.path.join(p, '*.*')))
    elif os.path.isfile(p):
        files = [p]
    else:
        raise Exception(f'ERROR: {p} does not exist')
    images = [x for x in files if x.split('.')[-1].lower() in IMG_FORMATS]
    videos = [x for x in files if x.split('.')[-1].lower() in VID_FORMATS]
    ni, nv = (len(images), len(videos))
    self.img_size = img_size
    self.stride = stride
    self.files = images + videos
    self.nf = ni + nv
    self.video_flag = [False] * ni + [True] * nv
    self.mode = 'image'
    self.auto = auto
    if any(videos):
        self.new_video(videos[0])
    else:
        self.cap = None
    assert self.nf > 0, f'No images or videos found in {p}. Supported formats are:\nimages: {IMG_FORMATS}\nvideos: {VID_FORMATS}'

def img2label_paths(img_paths):
    sa, sb = (os.sep + 'images' + os.sep, os.sep + 'labels' + os.sep)
    return [sb.join(x.rsplit(sa, 1)).rsplit('.', 1)[0] + '.txt' for x in img_paths]

class LoadImagesAndLabels(Dataset):
    cache_version = 0.6

    def __init__(self, path, img_size=640, batch_size=16, augment=False, hyp=None, rect=False, image_weights=False, cache_images=False, single_cls=False, stride=32, pad=0.0, prefix=''):
        self.img_size = img_size
        self.augment = augment
        self.hyp = hyp
        self.image_weights = image_weights
        self.rect = False if image_weights else rect
        self.mosaic = self.augment and (not self.rect)
        self.mosaic_border = [-img_size // 2, -img_size // 2]
        self.stride = stride
        self.path = path
        self.albumentations = Albumentations() if augment else None
        try:
            f = []
            for p in path if isinstance(path, list) else [path]:
                p = Path(p)
                if p.is_dir():
                    f += glob.glob(str(p / '**' / '*.*'), recursive=True)
                elif p.is_file():
                    with open(p) as t:
                        t = t.read().strip().splitlines()
                        parent = str(p.parent) + os.sep
                        f += [x.replace('./', parent) if x.startswith('./') else x for x in t]
                else:
                    raise Exception(f'{prefix}{p} does not exist')
            self.img_files = sorted((x.replace('/', os.sep) for x in f if x.split('.')[-1].lower() in IMG_FORMATS))
            assert self.img_files, f'{prefix}No images found'
        except Exception as e:
            raise Exception(f'{prefix}Error loading data from {path}: {e}\nSee {HELP_URL}')
        self.label_files = img2label_paths(self.img_files)
        cache_path = (p if p.is_file() else Path(self.label_files[0]).parent).with_suffix('.cache')
        try:
            cache, exists = (np.load(cache_path, allow_pickle=True).item(), True)
            assert cache['version'] == self.cache_version
            assert cache['hash'] == get_hash(self.label_files + self.img_files)
        except:
            cache, exists = (self.cache_labels(cache_path, prefix), False)
        nf, nm, ne, nc, n = cache.pop('results')
        if exists:
            d = f"Scanning '{cache_path}' images and labels... {nf} found, {nm} missing, {ne} empty, {nc} corrupted"
            tqdm(None, desc=prefix + d, total=n, initial=n)
            if cache['msgs']:
                LOGGER.info('\n'.join(cache['msgs']))
        assert nf > 0 or not augment, f'{prefix}No labels in {cache_path}. Can not train without labels. See {HELP_URL}'
        [cache.pop(k) for k in ('hash', 'version', 'msgs')]
        labels, shapes, self.segments = zip(*cache.values())
        self.labels = list(labels)
        self.shapes = np.array(shapes, dtype=np.float64)
        self.img_files = list(cache.keys())
        self.label_files = img2label_paths(cache.keys())
        n = len(shapes)
        bi = np.floor(np.arange(n) / batch_size).astype(np.int)
        nb = bi[-1] + 1
        self.batch = bi
        self.n = n
        self.indices = range(n)
        include_class = []
        include_class_array = np.array(include_class).reshape(1, -1)
        for i, (label, segment) in enumerate(zip(self.labels, self.segments)):
            if include_class:
                j = (label[:, 0:1] == include_class_array).any(1)
                self.labels[i] = label[j]
                if segment:
                    self.segments[i] = segment[j]
            if single_cls:
                self.labels[i][:, 0] = 0
                if segment:
                    self.segments[i][:, 0] = 0
        if self.rect:
            s = self.shapes
            ar = s[:, 1] / s[:, 0]
            irect = ar.argsort()
            self.img_files = [self.img_files[i] for i in irect]
            self.label_files = [self.label_files[i] for i in irect]
            self.labels = [self.labels[i] for i in irect]
            self.shapes = s[irect]
            ar = ar[irect]
            shapes = [[1, 1]] * nb
            for i in range(nb):
                ari = ar[bi == i]
                mini, maxi = (ari.min(), ari.max())
                if maxi < 1:
                    shapes[i] = [maxi, 1]
                elif mini > 1:
                    shapes[i] = [1, 1 / mini]
            self.batch_shapes = np.ceil(np.array(shapes) * img_size / stride + pad).astype(np.int) * stride
        self.imgs, self.img_npy = ([None] * n, [None] * n)
        if cache_images:
            if cache_images == 'disk':
                self.im_cache_dir = Path(Path(self.img_files[0]).parent.as_posix() + '_npy')
                self.img_npy = [self.im_cache_dir / Path(f).with_suffix('.npy').name for f in self.img_files]
                self.im_cache_dir.mkdir(parents=True, exist_ok=True)
            gb = 0
            self.img_hw0, self.img_hw = ([None] * n, [None] * n)
            results = ThreadPool(NUM_THREADS).imap(lambda x: load_image(*x), zip(repeat(self), range(n)))
            pbar = tqdm(enumerate(results), total=n)
            for i, x in pbar:
                if cache_images == 'disk':
                    if not self.img_npy[i].exists():
                        np.save(self.img_npy[i].as_posix(), x[0])
                    gb += self.img_npy[i].stat().st_size
                else:
                    self.imgs[i], self.img_hw0[i], self.img_hw[i] = x
                    gb += self.imgs[i].nbytes
                pbar.desc = f'{prefix}Caching images ({gb / 1000000000.0:.1f}GB {cache_images})'
            pbar.close()

    def cache_labels(self, path=Path('./labels.cache'), prefix=''):
        x = {}
        nm, nf, ne, nc, msgs = (0, 0, 0, 0, [])
        desc = f"{prefix}Scanning '{path.parent / path.stem}' images and labels..."
        with Pool(NUM_THREADS) as pool:
            pbar = tqdm(pool.imap(verify_image_label, zip(self.img_files, self.label_files, repeat(prefix))), desc=desc, total=len(self.img_files))
            for im_file, l, shape, segments, nm_f, nf_f, ne_f, nc_f, msg in pbar:
                nm += nm_f
                nf += nf_f
                ne += ne_f
                nc += nc_f
                if im_file:
                    x[im_file] = [l, shape, segments]
                if msg:
                    msgs.append(msg)
                pbar.desc = f'{desc}{nf} found, {nm} missing, {ne} empty, {nc} corrupted'
        pbar.close()
        if msgs:
            LOGGER.info('\n'.join(msgs))
        if nf == 0:
            LOGGER.warning(f'{prefix}WARNING: No labels found in {path}. See {HELP_URL}')
        x['hash'] = get_hash(self.label_files + self.img_files)
        x['results'] = (nf, nm, ne, nc, len(self.img_files))
        x['msgs'] = msgs
        x['version'] = self.cache_version
        try:
            np.save(path, x)
            path.with_suffix('.cache.npy').rename(path)
            LOGGER.info(f'{prefix}New cache created: {path}')
        except Exception as e:
            LOGGER.warning(f'{prefix}WARNING: Cache directory {path.parent} is not writeable: {e}')
        return x

    def __len__(self):
        return len(self.img_files)

    def __getitem__(self, index):
        index = self.indices[index]
        hyp = self.hyp
        mosaic = self.mosaic and random.random() < hyp['mosaic']
        if mosaic:
            img, labels = load_mosaic(self, index)
            shapes = None
            if random.random() < hyp['mixup']:
                img, labels = mixup(img, labels, *load_mosaic(self, random.randint(0, self.n - 1)))
        else:
            img, (h0, w0), (h, w) = load_image(self, index)
            shape = self.batch_shapes[self.batch[index]] if self.rect else self.img_size
            img, ratio, pad = letterbox(img, shape, auto=False, scaleup=self.augment)
            shapes = ((h0, w0), ((h / h0, w / w0), pad))
            labels = self.labels[index].copy()
            if labels.size:
                labels[:, 1:] = xywhn2xyxy(labels[:, 1:], ratio[0] * w, ratio[1] * h, padw=pad[0], padh=pad[1])
            if self.augment:
                img, labels = random_perspective(img, labels, degrees=hyp['degrees'], translate=hyp['translate'], scale=hyp['scale'], shear=hyp['shear'], perspective=hyp['perspective'])
        nl = len(labels)
        if nl:
            labels[:, 1:5] = xyxy2xywhn(labels[:, 1:5], w=img.shape[1], h=img.shape[0], clip=True, eps=0.001)
        if self.augment:
            img, labels = self.albumentations(img, labels)
            nl = len(labels)
            augment_hsv(img, hgain=hyp['hsv_h'], sgain=hyp['hsv_s'], vgain=hyp['hsv_v'])
            if random.random() < hyp['flipud']:
                img = np.flipud(img)
                if nl:
                    labels[:, 2] = 1 - labels[:, 2]
            if random.random() < hyp['fliplr']:
                img = np.fliplr(img)
                if nl:
                    labels[:, 1] = 1 - labels[:, 1]
        labels_out = torch.zeros((nl, 6))
        if nl:
            labels_out[:, 1:] = torch.from_numpy(labels)
        img = img.transpose((2, 0, 1))[::-1]
        img = np.ascontiguousarray(img)
        return (torch.from_numpy(img), labels_out, self.img_files[index], shapes)

    @staticmethod
    def collate_fn(batch):
        img, label, path, shapes = zip(*batch)
        for i, l in enumerate(label):
            l[:, 0] = i
        return (torch.stack(img, 0), torch.cat(label, 0), path, shapes)

    @staticmethod
    def collate_fn4(batch):
        img, label, path, shapes = zip(*batch)
        n = len(shapes) // 4
        img4, label4, path4, shapes4 = ([], [], path[:n], shapes[:n])
        ho = torch.tensor([[0.0, 0, 0, 1, 0, 0]])
        wo = torch.tensor([[0.0, 0, 1, 0, 0, 0]])
        s = torch.tensor([[1, 1, 0.5, 0.5, 0.5, 0.5]])
        for i in range(n):
            i *= 4
            if random.random() < 0.5:
                im = F.interpolate(img[i].unsqueeze(0).float(), scale_factor=2.0, mode='bilinear', align_corners=False)[0].type(img[i].type())
                l = label[i]
            else:
                im = torch.cat((torch.cat((img[i], img[i + 1]), 1), torch.cat((img[i + 2], img[i + 3]), 1)), 2)
                l = torch.cat((label[i], label[i + 1] + ho, label[i + 2] + wo, label[i + 3] + ho + wo), 0) * s
            img4.append(im)
            label4.append(l)
        for i, l in enumerate(label4):
            l[:, 0] = i
        return (torch.stack(img4, 0), torch.cat(label4, 0), path4, shapes4)

def __init__(self, path, img_size=640, batch_size=16, augment=False, hyp=None, rect=False, image_weights=False, cache_images=False, single_cls=False, stride=32, pad=0.0, prefix=''):
    self.img_size = img_size
    self.augment = augment
    self.hyp = hyp
    self.image_weights = image_weights
    self.rect = False if image_weights else rect
    self.mosaic = self.augment and (not self.rect)
    self.mosaic_border = [-img_size // 2, -img_size // 2]
    self.stride = stride
    self.path = path
    self.albumentations = Albumentations() if augment else None
    try:
        f = []
        for p in path if isinstance(path, list) else [path]:
            p = Path(p)
            if p.is_dir():
                f += glob.glob(str(p / '**' / '*.*'), recursive=True)
            elif p.is_file():
                with open(p) as t:
                    t = t.read().strip().splitlines()
                    parent = str(p.parent) + os.sep
                    f += [x.replace('./', parent) if x.startswith('./') else x for x in t]
            else:
                raise Exception(f'{prefix}{p} does not exist')
        self.img_files = sorted((x.replace('/', os.sep) for x in f if x.split('.')[-1].lower() in IMG_FORMATS))
        assert self.img_files, f'{prefix}No images found'
    except Exception as e:
        raise Exception(f'{prefix}Error loading data from {path}: {e}\nSee {HELP_URL}')
    self.label_files = img2label_paths(self.img_files)
    cache_path = (p if p.is_file() else Path(self.label_files[0]).parent).with_suffix('.cache')
    try:
        cache, exists = (np.load(cache_path, allow_pickle=True).item(), True)
        assert cache['version'] == self.cache_version
        assert cache['hash'] == get_hash(self.label_files + self.img_files)
    except:
        cache, exists = (self.cache_labels(cache_path, prefix), False)
    nf, nm, ne, nc, n = cache.pop('results')
    if exists:
        d = f"Scanning '{cache_path}' images and labels... {nf} found, {nm} missing, {ne} empty, {nc} corrupted"
        tqdm(None, desc=prefix + d, total=n, initial=n)
        if cache['msgs']:
            LOGGER.info('\n'.join(cache['msgs']))
    assert nf > 0 or not augment, f'{prefix}No labels in {cache_path}. Can not train without labels. See {HELP_URL}'
    [cache.pop(k) for k in ('hash', 'version', 'msgs')]
    labels, shapes, self.segments = zip(*cache.values())
    self.labels = list(labels)
    self.shapes = np.array(shapes, dtype=np.float64)
    self.img_files = list(cache.keys())
    self.label_files = img2label_paths(cache.keys())
    n = len(shapes)
    bi = np.floor(np.arange(n) / batch_size).astype(np.int)
    nb = bi[-1] + 1
    self.batch = bi
    self.n = n
    self.indices = range(n)
    include_class = []
    include_class_array = np.array(include_class).reshape(1, -1)
    for i, (label, segment) in enumerate(zip(self.labels, self.segments)):
        if include_class:
            j = (label[:, 0:1] == include_class_array).any(1)
            self.labels[i] = label[j]
            if segment:
                self.segments[i] = segment[j]
        if single_cls:
            self.labels[i][:, 0] = 0
            if segment:
                self.segments[i][:, 0] = 0
    if self.rect:
        s = self.shapes
        ar = s[:, 1] / s[:, 0]
        irect = ar.argsort()
        self.img_files = [self.img_files[i] for i in irect]
        self.label_files = [self.label_files[i] for i in irect]
        self.labels = [self.labels[i] for i in irect]
        self.shapes = s[irect]
        ar = ar[irect]
        shapes = [[1, 1]] * nb
        for i in range(nb):
            ari = ar[bi == i]
            mini, maxi = (ari.min(), ari.max())
            if maxi < 1:
                shapes[i] = [maxi, 1]
            elif mini > 1:
                shapes[i] = [1, 1 / mini]
        self.batch_shapes = np.ceil(np.array(shapes) * img_size / stride + pad).astype(np.int) * stride
    self.imgs, self.img_npy = ([None] * n, [None] * n)
    if cache_images:
        if cache_images == 'disk':
            self.im_cache_dir = Path(Path(self.img_files[0]).parent.as_posix() + '_npy')
            self.img_npy = [self.im_cache_dir / Path(f).with_suffix('.npy').name for f in self.img_files]
            self.im_cache_dir.mkdir(parents=True, exist_ok=True)
        gb = 0
        self.img_hw0, self.img_hw = ([None] * n, [None] * n)
        results = ThreadPool(NUM_THREADS).imap(lambda x: load_image(*x), zip(repeat(self), range(n)))
        pbar = tqdm(enumerate(results), total=n)
        for i, x in pbar:
            if cache_images == 'disk':
                if not self.img_npy[i].exists():
                    np.save(self.img_npy[i].as_posix(), x[0])
                gb += self.img_npy[i].stat().st_size
            else:
                self.imgs[i], self.img_hw0[i], self.img_hw[i] = x
                gb += self.imgs[i].nbytes
            pbar.desc = f'{prefix}Caching images ({gb / 1000000000.0:.1f}GB {cache_images})'
        pbar.close()

def cache_labels(self, path=Path('./labels.cache'), prefix=''):
    x = {}
    nm, nf, ne, nc, msgs = (0, 0, 0, 0, [])
    desc = f"{prefix}Scanning '{path.parent / path.stem}' images and labels..."
    with Pool(NUM_THREADS) as pool:
        pbar = tqdm(pool.imap(verify_image_label, zip(self.img_files, self.label_files, repeat(prefix))), desc=desc, total=len(self.img_files))
        for im_file, l, shape, segments, nm_f, nf_f, ne_f, nc_f, msg in pbar:
            nm += nm_f
            nf += nf_f
            ne += ne_f
            nc += nc_f
            if im_file:
                x[im_file] = [l, shape, segments]
            if msg:
                msgs.append(msg)
            pbar.desc = f'{desc}{nf} found, {nm} missing, {ne} empty, {nc} corrupted'
    pbar.close()
    if msgs:
        LOGGER.info('\n'.join(msgs))
    if nf == 0:
        LOGGER.warning(f'{prefix}WARNING: No labels found in {path}. See {HELP_URL}')
    x['hash'] = get_hash(self.label_files + self.img_files)
    x['results'] = (nf, nm, ne, nc, len(self.img_files))
    x['msgs'] = msgs
    x['version'] = self.cache_version
    try:
        np.save(path, x)
        path.with_suffix('.cache.npy').rename(path)
        LOGGER.info(f'{prefix}New cache created: {path}')
    except Exception as e:
        LOGGER.warning(f'{prefix}WARNING: Cache directory {path.parent} is not writeable: {e}')
    return x

def flatten_recursive(path='../datasets/coco128'):
    new_path = Path(path + '_flat')
    create_folder(new_path)
    for file in tqdm(glob.glob(str(Path(path)) + '/**/*.*', recursive=True)):
        shutil.copyfile(file, new_path / Path(file).name)

def autosplit(path='../datasets/coco128/images', weights=(0.9, 0.1, 0.0), annotated_only=False):
    """ Autosplit a dataset into train/val/test splits and save path/autosplit_*.txt files
    Usage: from utils.datasets import *; autosplit()
    Arguments
        path:            Path to images directory
        weights:         Train, val, test weights (list, tuple)
        annotated_only:  Only use images with an annotated txt file
    """
    path = Path(path)
    files = sorted((x for x in path.rglob('*.*') if x.suffix[1:].lower() in IMG_FORMATS))
    n = len(files)
    random.seed(0)
    indices = random.choices([0, 1, 2], weights=weights, k=n)
    txt = ['autosplit_train.txt', 'autosplit_val.txt', 'autosplit_test.txt']
    [(path.parent / x).unlink(missing_ok=True) for x in txt]
    print(f'Autosplitting images from {path}' + ', using *.txt labeled images only' * annotated_only)
    for i, img in tqdm(zip(indices, files), total=n):
        if not annotated_only or Path(img2label_paths([str(img)])[0]).exists():
            with open(path.parent / txt[i], 'a') as f:
                f.write('./' + img.relative_to(path.parent).as_posix() + '\n')

def unzip(path):
    if str(path).endswith('.zip'):
        assert Path(path).is_file(), f'Error unzipping {path}, file not found'
        ZipFile(path).extractall(path=path.parent)
        dir = path.with_suffix('')
        return (True, str(dir), next(dir.rglob('*.yaml')))
    else:
        return (False, None, path)

def hub_ops(f, max_dim=1920):
    f_new = im_dir / Path(f).name
    try:
        im = Image.open(f)
        r = max_dim / max(im.height, im.width)
        if r < 1.0:
            im = im.resize((int(im.width * r), int(im.height * r)))
        im.save(f_new, 'JPEG', quality=75, optimize=True)
    except Exception as e:
        print(f'WARNING: HUB ops PIL failure {f}: {e}')
        im = cv2.imread(f)
        im_height, im_width = im.shape[:2]
        r = max_dim / max(im_height, im_width)
        if r < 1.0:
            im = cv2.resize(im, (int(im_width * r), int(im_height * r)), interpolation=cv2.INTER_AREA)
        cv2.imwrite(str(f_new), im)

def dataset_stats(path='coco128.yaml', autodownload=False, verbose=False, profile=False, hub=False):
    """ Return dataset statistics dictionary with images and instances counts per split per class
    To run in parent directory: export PYTHONPATH="$PWD/yolov5"
    Usage1: from utils.datasets import *; dataset_stats('coco128.yaml', autodownload=True)
    Usage2: from utils.datasets import *; dataset_stats('../datasets/coco128_with_yaml.zip')
    Arguments
        path:           Path to data.yaml or data.zip (with data.yaml inside data.zip)
        autodownload:   Attempt to download dataset if not found locally
        verbose:        Print stats dictionary
    """

    def round_labels(labels):
        return [[int(c), *(round(x, 4) for x in points)] for c, *points in labels]

    def unzip(path):
        if str(path).endswith('.zip'):
            assert Path(path).is_file(), f'Error unzipping {path}, file not found'
            ZipFile(path).extractall(path=path.parent)
            dir = path.with_suffix('')
            return (True, str(dir), next(dir.rglob('*.yaml')))
        else:
            return (False, None, path)

    def hub_ops(f, max_dim=1920):
        f_new = im_dir / Path(f).name
        try:
            im = Image.open(f)
            r = max_dim / max(im.height, im.width)
            if r < 1.0:
                im = im.resize((int(im.width * r), int(im.height * r)))
            im.save(f_new, 'JPEG', quality=75, optimize=True)
        except Exception as e:
            print(f'WARNING: HUB ops PIL failure {f}: {e}')
            im = cv2.imread(f)
            im_height, im_width = im.shape[:2]
            r = max_dim / max(im_height, im_width)
            if r < 1.0:
                im = cv2.resize(im, (int(im_width * r), int(im_height * r)), interpolation=cv2.INTER_AREA)
            cv2.imwrite(str(f_new), im)
    zipped, data_dir, yaml_path = unzip(Path(path))
    with open(check_yaml(yaml_path), errors='ignore') as f:
        data = yaml.safe_load(f)
        if zipped:
            data['path'] = data_dir
    check_dataset(data, autodownload)
    hub_dir = Path(data['path'] + ('-hub' if hub else ''))
    stats = {'nc': data['nc'], 'names': data['names']}
    for split in ('train', 'val', 'test'):
        if data.get(split) is None:
            stats[split] = None
            continue
        x = []
        dataset = LoadImagesAndLabels(data[split])
        for label in tqdm(dataset.labels, total=dataset.n, desc='Statistics'):
            x.append(np.bincount(label[:, 0].astype(int), minlength=data['nc']))
        x = np.array(x)
        stats[split] = {'instance_stats': {'total': int(x.sum()), 'per_class': x.sum(0).tolist()}, 'image_stats': {'total': dataset.n, 'unlabelled': int(np.all(x == 0, 1).sum()), 'per_class': (x > 0).sum(0).tolist()}, 'labels': [{str(Path(k).name): round_labels(v.tolist())} for k, v in zip(dataset.img_files, dataset.labels)]}
        if hub:
            im_dir = hub_dir / 'images'
            im_dir.mkdir(parents=True, exist_ok=True)
            for _ in tqdm(ThreadPool(NUM_THREADS).imap(hub_ops, dataset.img_files), total=dataset.n, desc='HUB Ops'):
                pass
    stats_path = hub_dir / 'stats.json'
    if profile:
        for _ in range(1):
            file = stats_path.with_suffix('.npy')
            t1 = time.time()
            np.save(file, stats)
            t2 = time.time()
            x = np.load(file, allow_pickle=True)
            print(f'stats.npy times: {time.time() - t2:.3f}s read, {t2 - t1:.3f}s write')
            file = stats_path.with_suffix('.json')
            t1 = time.time()
            with open(file, 'w') as f:
                json.dump(stats, f)
            t2 = time.time()
            with open(file) as f:
                x = json.load(f)
            print(f'stats.json times: {time.time() - t2:.3f}s read, {t2 - t1:.3f}s write')
    if hub:
        print(f'Saving {stats_path.resolve()}...')
        with open(stats_path, 'w') as f:
            json.dump(stats, f)
    if verbose:
        print(json.dumps(stats, indent=2, sort_keys=False))
    return stats

def gsutil_getsize(url=''):
    s = subprocess.check_output(f'gsutil du {url}', shell=True).decode('utf-8')
    return eval(s.split(' ')[0]) if len(s) else 0

def safe_download(file, url, url2=None, min_bytes=1.0, error_msg=''):
    file = Path(file)
    assert_msg = f"Downloaded file '{file}' does not exist or size is < min_bytes={min_bytes}"
    try:
        print(f'Downloading {url} to {file}...')
        torch.hub.download_url_to_file(url, str(file))
        assert file.exists() and file.stat().st_size > min_bytes, assert_msg
    except Exception as e:
        file.unlink(missing_ok=True)
        print(f'ERROR: {e}\nRe-attempting {url2 or url} to {file}...')
        os.system(f"curl -L '{url2 or url}' -o '{file}' --retry 3 -C -")
    finally:
        if not file.exists() or file.stat().st_size < min_bytes:
            file.unlink(missing_ok=True)
            print(f'ERROR: {assert_msg}\n{error_msg}')
        print('')

def attempt_download(file, repo='ultralytics/yolov5'):
    file = Path(str(file).strip().replace("'", ''))
    if not file.exists():
        name = Path(urllib.parse.unquote(str(file))).name
        if str(file).startswith(('http:/', 'https:/')):
            url = str(file).replace(':/', '://')
            file = name.split('?')[0]
            if Path(file).is_file():
                print(f'Found {url} locally at {file}')
            else:
                safe_download(file=file, url=url, min_bytes=100000.0)
            return file
        file.parent.mkdir(parents=True, exist_ok=True)
        try:
            response = requests.get(f'https://api.github.com/repos/{repo}/releases/latest').json()
            assets = [x['name'] for x in response['assets']]
            tag = response['tag_name']
        except:
            assets = ['yolov5n.pt', 'yolov5s.pt', 'yolov5m.pt', 'yolov5l.pt', 'yolov5x.pt', 'yolov5n6.pt', 'yolov5s6.pt', 'yolov5m6.pt', 'yolov5l6.pt', 'yolov5x6.pt']
            try:
                tag = subprocess.check_output('git tag', shell=True, stderr=subprocess.STDOUT).decode().split()[-1]
            except:
                tag = 'v6.0'
        if name in assets:
            safe_download(file, url=f'https://github.com/{repo}/releases/download/{tag}/{name}', min_bytes=100000.0, error_msg=f'{file} missing, try downloading from https://github.com/{repo}/releases/')
    return str(file)

def gdrive_download(id='16TiPfZj7htmTyhntwcZyEEAejOUxuT6m', file='tmp.zip'):
    t = time.time()
    file = Path(file)
    cookie = Path('cookie')
    print(f'Downloading https://drive.google.com/uc?export=download&id={id} as {file}... ', end='')
    file.unlink(missing_ok=True)
    cookie.unlink(missing_ok=True)
    out = 'NUL' if platform.system() == 'Windows' else '/dev/null'
    os.system(f'curl -c ./cookie -s -L "drive.google.com/uc?export=download&id={id}" > {out}')
    if os.path.exists('cookie'):
        s = f'curl -Lb ./cookie "drive.google.com/uc?export=download&confirm={get_token()}&id={id}" -o {file}'
    else:
        s = f'curl -s -L -o {file} "drive.google.com/uc?export=download&id={id}"'
    r = os.system(s)
    cookie.unlink(missing_ok=True)
    if r != 0:
        file.unlink(missing_ok=True)
        print('Download error ')
        return r
    if file.suffix == '.zip':
        print('unzipping... ', end='')
        ZipFile(file).extractall(path=file.parent)
        file.unlink()
    print(f'Done ({time.time() - t:.1f}s)')
    return r

class Profile(contextlib.ContextDecorator):

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, type, value, traceback):
        print(f'Profile results: {time.time() - self.start:.5f}s')

def __enter__(self):
    self.start = time.time()

def __exit__(self, type, value, traceback):
    print(f'Profile results: {time.time() - self.start:.5f}s')

class WorkingDirectory(contextlib.ContextDecorator):

    def __init__(self, new_dir):
        self.dir = new_dir
        self.cwd = Path.cwd().resolve()

    def __enter__(self):
        os.chdir(self.dir)

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self.cwd)

def __init__(self, new_dir):
    self.dir = new_dir
    self.cwd = Path.cwd().resolve()

def handler(*args, **kwargs):
    try:
        func(*args, **kwargs)
    except Exception as e:
        print(e)

def init_seeds(seed=0):
    import torch.backends.cudnn as cudnn
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    cudnn.benchmark, cudnn.deterministic = (False, True) if seed == 0 else (True, False)

def get_latest_run(search_dir='.'):
    last_list = glob.glob(f'{search_dir}/**/last*.pt', recursive=True)
    return max(last_list, key=os.path.getctime) if last_list else ''

def user_config_dir(dir='Ultralytics', env_var='YOLOV5_CONFIG_DIR'):
    env = os.getenv(env_var)
    if env:
        path = Path(env)
    else:
        cfg = {'Windows': 'AppData/Roaming', 'Linux': '.config', 'Darwin': 'Library/Application Support'}
        path = Path.home() / cfg.get(platform.system(), '')
        path = (path if is_writeable(path) else Path('/tmp')) / dir
    path.mkdir(exist_ok=True)
    return path

def is_writeable(dir, test=False):
    if test:
        file = Path(dir) / 'tmp.txt'
        try:
            with open(file, 'w'):
                pass
            file.unlink()
            return True
        except OSError:
            return False
    else:
        return os.access(dir, os.R_OK)

def is_docker():
    return Path('/workspace').exists()

def is_pip():
    return 'site-packages' in Path(__file__).resolve().parts

def is_ascii(s=''):
    s = str(s)
    return len(s.encode().decode('ascii', 'ignore')) == len(s)

def is_chinese(s='人工智能'):
    return re.search('[一-鿿]', s)

def emojis(str=''):
    return str.encode().decode('ascii', 'ignore') if platform.system() == 'Windows' else str

def file_size(path):
    path = Path(path)
    if path.is_file():
        return path.stat().st_size / 1000000.0
    elif path.is_dir():
        return sum((f.stat().st_size for f in path.glob('**/*') if f.is_file())) / 1000000.0
    else:
        return 0.0

@try_except
@WorkingDirectory(ROOT)
def check_git_status():
    msg = ', for updates see https://github.com/ultralytics/yolov5'
    print(colorstr('github: '), end='')
    assert Path('.git').exists(), 'skipping check (not a git repository)' + msg
    assert not is_docker(), 'skipping check (Docker image)' + msg
    assert check_online(), 'skipping check (offline)' + msg
    cmd = 'git fetch && git config --get remote.origin.url'
    url = check_output(cmd, shell=True, timeout=5).decode().strip().rstrip('.git')
    branch = check_output('git rev-parse --abbrev-ref HEAD', shell=True).decode().strip()
    n = int(check_output(f'git rev-list {branch}..origin/master --count', shell=True))
    if n > 0:
        s = f'⚠️ YOLOv5 is out of date by {n} commit{'s' * (n > 1)}. Use `git pull` or `git clone {url}` to update.'
    else:
        s = f'up to date with {url} ✅'
    print(emojis(s))

@try_except
def check_requirements(requirements=ROOT / 'requirements.txt', exclude=(), install=True):
    prefix = colorstr('red', 'bold', 'requirements:')
    check_python()
    if isinstance(requirements, (str, Path)):
        file = Path(requirements)
        assert file.exists(), f'{prefix} {file.resolve()} not found, check failed.'
        with file.open() as f:
            requirements = [f'{x.name}{x.specifier}' for x in pkg.parse_requirements(f) if x.name not in exclude]
    else:
        requirements = [x for x in requirements if x not in exclude]
    n = 0
    for r in requirements:
        try:
            pkg.require(r)
        except Exception as e:
            s = f'{prefix} {r} not found and is required by YOLOv5'
            if install:
                print(f'{s}, attempting auto-update...')
                try:
                    assert check_online(), f"'pip install {r}' skipped (offline)"
                    print(check_output(f"pip install '{r}'", shell=True).decode())
                    n += 1
                except Exception as e:
                    print(f'{prefix} {e}')
            else:
                print(f'{s}. Please install and rerun your command.')
    if n:
        source = file.resolve() if 'file' in locals() else requirements
        s = f'{prefix} {n} package{'s' * (n > 1)} updated per {source}\n{prefix} ⚠️ {colorstr('bold', 'Restart runtime or rerun command for updates to take effect')}\n'
        print(emojis(s))

def check_yaml(file, suffix=('.yaml', '.yml')):
    return check_file(file, suffix)

def check_file(file, suffix=''):
    check_suffix(file, suffix)
    file = str(file)
    if Path(file).is_file() or file == '':
        return file
    elif file.startswith(('http:/', 'https:/')):
        url = str(Path(file)).replace(':/', '://')
        file = Path(urllib.parse.unquote(file).split('?')[0]).name
        if Path(file).is_file():
            print(f'Found {url} locally at {file}')
        else:
            print(f'Downloading {url} to {file}...')
            torch.hub.download_url_to_file(url, file)
            assert Path(file).exists() and Path(file).stat().st_size > 0, f'File download failed: {url}'
        return file
    else:
        files = []
        for d in ('data', 'models', 'utils'):
            files.extend(glob.glob(str(ROOT / d / '**' / file), recursive=True))
        assert len(files), f'File not found: {file}'
        assert len(files) == 1, f"Multiple files match '{file}', specify exact path: {files}"
        return files[0]

def check_dataset(data, autodownload=True):
    extract_dir = ''
    if isinstance(data, (str, Path)) and str(data).endswith('.zip'):
        download(data, dir='../datasets', unzip=True, delete=False, curl=False, threads=1)
        data = next((Path('../datasets') / Path(data).stem).rglob('*.yaml'))
        extract_dir, autodownload = (data.parent, False)
    if isinstance(data, (str, Path)):
        with open(data, errors='ignore') as f:
            data = yaml.safe_load(f)
    path = extract_dir or Path(data.get('path') or '')
    for k in ('train', 'val', 'test'):
        if data.get(k):
            data[k] = str(path / data[k]) if isinstance(data[k], str) else [str(path / x) for x in data[k]]
    assert 'nc' in data, "Dataset 'nc' key missing."
    if 'names' not in data:
        data['names'] = [f'class{i}' for i in range(data['nc'])]
    train, val, test, s = (data.get(x) for x in ('train', 'val', 'test', 'download'))
    if val:
        val = [Path(x).resolve() for x in (val if isinstance(val, list) else [val])]
        if not all((x.exists() for x in val)):
            print('\nWARNING: Dataset not found, nonexistent paths: %s' % [str(x) for x in val if not x.exists()])
            if s and autodownload:
                root = path.parent if 'path' in data else '..'
                if s.startswith('http') and s.endswith('.zip'):
                    f = Path(s).name
                    print(f'Downloading {s} to {f}...')
                    torch.hub.download_url_to_file(s, f)
                    Path(root).mkdir(parents=True, exist_ok=True)
                    ZipFile(f).extractall(path=root)
                    Path(f).unlink()
                    r = None
                elif s.startswith('bash '):
                    print(f'Running {s} ...')
                    r = os.system(s)
                else:
                    r = exec(s, {'yaml': data})
                print(f'Dataset autodownload {(f'success, saved to {root}' if r in (0, None) else 'failure')}\n')
            else:
                raise Exception('Dataset not found.')
    return data

def url2file(url):
    url = str(Path(url)).replace(':/', '://')
    file = Path(urllib.parse.unquote(url)).name.split('?')[0]
    return file

def download_one(url, dir):
    f = dir / Path(url).name
    if Path(url).is_file():
        Path(url).rename(f)
    elif not f.exists():
        print(f'Downloading {url} to {f}...')
        if curl:
            os.system(f"curl -L '{url}' -o '{f}' --retry 9 -C -")
        else:
            torch.hub.download_url_to_file(url, f, progress=True)
    if unzip and f.suffix in ('.zip', '.gz'):
        print(f'Unzipping {f}...')
        if f.suffix == '.zip':
            ZipFile(f).extractall(path=dir)
        elif f.suffix == '.gz':
            os.system(f'tar xfz {f} --directory {f.parent}')
        if delete:
            f.unlink()

def download(url, dir='.', unzip=True, delete=True, curl=False, threads=1):

    def download_one(url, dir):
        f = dir / Path(url).name
        if Path(url).is_file():
            Path(url).rename(f)
        elif not f.exists():
            print(f'Downloading {url} to {f}...')
            if curl:
                os.system(f"curl -L '{url}' -o '{f}' --retry 9 -C -")
            else:
                torch.hub.download_url_to_file(url, f, progress=True)
        if unzip and f.suffix in ('.zip', '.gz'):
            print(f'Unzipping {f}...')
            if f.suffix == '.zip':
                ZipFile(f).extractall(path=dir)
            elif f.suffix == '.gz':
                os.system(f'tar xfz {f} --directory {f.parent}')
            if delete:
                f.unlink()
    dir = Path(dir)
    dir.mkdir(parents=True, exist_ok=True)
    if threads > 1:
        pool = ThreadPool(threads)
        pool.imap(lambda x: download_one(*x), zip(url, repeat(dir)))
        pool.close()
        pool.join()
    else:
        for u in [url] if isinstance(url, (str, Path)) else url:
            download_one(u, dir)

def colorstr(*input):
    *args, string = input if len(input) > 1 else ('blue', 'bold', input[0])
    colors = {'black': '\x1b[30m', 'red': '\x1b[31m', 'green': '\x1b[32m', 'yellow': '\x1b[33m', 'blue': '\x1b[34m', 'magenta': '\x1b[35m', 'cyan': '\x1b[36m', 'white': '\x1b[37m', 'bright_black': '\x1b[90m', 'bright_red': '\x1b[91m', 'bright_green': '\x1b[92m', 'bright_yellow': '\x1b[93m', 'bright_blue': '\x1b[94m', 'bright_magenta': '\x1b[95m', 'bright_cyan': '\x1b[96m', 'bright_white': '\x1b[97m', 'end': '\x1b[0m', 'bold': '\x1b[1m', 'underline': '\x1b[4m'}
    return ''.join((colors[x] for x in args)) + f'{string}' + colors['end']

def strip_optimizer(f='best.pt', s=''):
    x = torch.load(f, map_location=torch.device('cpu'))
    if x.get('ema'):
        x['model'] = x['ema']
    for k in ('optimizer', 'best_fitness', 'wandb_id', 'ema', 'updates'):
        x[k] = None
    x['epoch'] = -1
    x['model'].half()
    for p in x['model'].parameters():
        p.requires_grad = False
    torch.save(x, s or f)
    mb = os.path.getsize(s or f) / 1000000.0
    print(f'Optimizer stripped from {f},{(' saved as %s,' % s if s else '')} {mb:.1f}MB')

def print_mutation(results, hyp, save_dir, bucket):
    evolve_csv, results_csv, evolve_yaml = (save_dir / 'evolve.csv', save_dir / 'results.csv', save_dir / 'hyp_evolve.yaml')
    keys = ('metrics/precision', 'metrics/recall', 'metrics/mAP_0.5', 'metrics/mAP_0.5:0.95', 'val/box_loss', 'val/obj_loss', 'val/cls_loss') + tuple(hyp.keys())
    keys = tuple((x.strip() for x in keys))
    vals = results + tuple(hyp.values())
    n = len(keys)
    if bucket:
        url = f'gs://{bucket}/evolve.csv'
        if gsutil_getsize(url) > (os.path.getsize(evolve_csv) if os.path.exists(evolve_csv) else 0):
            os.system(f'gsutil cp {url} {save_dir}')
    s = '' if evolve_csv.exists() else ('%20s,' * n % keys).rstrip(',') + '\n'
    with open(evolve_csv, 'a') as f:
        f.write(s + ('%20.5g,' * n % vals).rstrip(',') + '\n')
    print(colorstr('evolve: ') + ', '.join((f'{x.strip():>20s}' for x in keys)))
    print(colorstr('evolve: ') + ', '.join((f'{x:20.5g}' for x in vals)), end='\n\n\n')
    with open(evolve_yaml, 'w') as f:
        data = pd.read_csv(evolve_csv)
        data = data.rename(columns=lambda x: x.strip())
        i = np.argmax(fitness(data.values[:, :7]))
        f.write('# YOLOv5 Hyperparameter Evolution Results\n' + f'# Best generation: {i}\n' + f'# Last generation: {len(data) - 1}\n' + '# ' + ', '.join((f'{x.strip():>20s}' for x in keys[:7])) + '\n' + '# ' + ', '.join((f'{x:>20.5g}' for x in data.values[i, :7])) + '\n\n')
        yaml.safe_dump(hyp, f, sort_keys=False)
    if bucket:
        os.system(f'gsutil cp {evolve_csv} {evolve_yaml} gs://{bucket}')

def increment_path(path, exist_ok=False, sep='', mkdir=False):
    path = Path(path)
    if path.exists() and (not exist_ok):
        path, suffix = (path.with_suffix(''), path.suffix) if path.is_file() else (path, '')
        dirs = glob.glob(f'{path}{sep}*')
        matches = [re.search(f'%s{sep}(\\d+)' % path.stem, d) for d in dirs]
        i = [int(m.groups()[0]) for m in matches if m]
        n = max(i) + 1 if i else 2
        path = Path(f'{path}{sep}{n}{suffix}')
    if mkdir:
        path.mkdir(parents=True, exist_ok=True)
    return path

class ConfusionMatrix:

    def __init__(self, nc, conf=0.25, iou_thres=0.45):
        self.matrix = np.zeros((nc + 1, nc + 1))
        self.nc = nc
        self.conf = conf
        self.iou_thres = iou_thres

    def process_batch(self, detections, labels):
        """
        Return intersection-over-union (Jaccard index) of boxes.
        Both sets of boxes are expected to be in (x1, y1, x2, y2) format.
        Arguments:
            detections (Array[N, 6]), x1, y1, x2, y2, conf, class
            labels (Array[M, 5]), class, x1, y1, x2, y2
        Returns:
            None, updates confusion matrix accordingly
        """
        detections = detections[detections[:, 4] > self.conf]
        gt_classes = labels[:, 0].int()
        detection_classes = detections[:, 5].int()
        iou = box_iou(labels[:, 1:], detections[:, :4])
        x = torch.where(iou > self.iou_thres)
        if x[0].shape[0]:
            matches = torch.cat((torch.stack(x, 1), iou[x[0], x[1]][:, None]), 1).cpu().numpy()
            if x[0].shape[0] > 1:
                matches = matches[matches[:, 2].argsort()[::-1]]
                matches = matches[np.unique(matches[:, 1], return_index=True)[1]]
                matches = matches[matches[:, 2].argsort()[::-1]]
                matches = matches[np.unique(matches[:, 0], return_index=True)[1]]
        else:
            matches = np.zeros((0, 3))
        n = matches.shape[0] > 0
        m0, m1, _ = matches.transpose().astype(np.int16)
        for i, gc in enumerate(gt_classes):
            j = m0 == i
            if n and sum(j) == 1:
                self.matrix[detection_classes[m1[j]], gc] += 1
            else:
                self.matrix[self.nc, gc] += 1
        if n:
            for i, dc in enumerate(detection_classes):
                if not any(m1 == i):
                    self.matrix[dc, self.nc] += 1

    def matrix(self):
        return self.matrix

    def tp_fp(self):
        tp = self.matrix.diagonal()
        fp = self.matrix.sum(1) - tp
        return (tp[:-1], fp[:-1])

    def plot(self, normalize=True, save_dir='', names=()):
        try:
            import seaborn as sn
            array = self.matrix / (self.matrix.sum(0).reshape(1, -1) + 1e-06 if normalize else 1)
            array[array < 0.005] = np.nan
            fig = plt.figure(figsize=(12, 9), tight_layout=True)
            sn.set(font_scale=1.0 if self.nc < 50 else 0.8)
            labels = 0 < len(names) < 99 and len(names) == self.nc
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                sn.heatmap(array, annot=self.nc < 30, annot_kws={'size': 8}, cmap='Blues', fmt='.2f', square=True, xticklabels=names + ['background FP'] if labels else 'auto', yticklabels=names + ['background FN'] if labels else 'auto').set_facecolor((1, 1, 1))
            fig.axes[0].set_xlabel('True')
            fig.axes[0].set_ylabel('Predicted')
            fig.savefig(Path(save_dir) / 'confusion_matrix.png', dpi=250)
            plt.close()
        except Exception as e:
            print(f'WARNING: ConfusionMatrix plot failure: {e}')

    def print(self):
        for i in range(self.nc + 1):
            print(' '.join(map(str, self.matrix[i])))

def print(self):
    for i in range(self.nc + 1):
        print(' '.join(map(str, self.matrix[i])))

def date_modified(path=__file__):
    t = datetime.datetime.fromtimestamp(Path(path).stat().st_mtime)
    return f'{t.year}-{t.month}-{t.day}'

def git_describe(path=Path(__file__).parent):
    s = f'git -C {path} describe --tags --long --always'
    try:
        return subprocess.check_output(s, shell=True, stderr=subprocess.STDOUT).decode()[:-1]
    except subprocess.CalledProcessError as e:
        return ''

def select_device(device='', batch_size=0, newline=True):
    s = f'YOLOv5 🚀 {git_describe() or date_modified()} torch {torch.__version__} '
    device = str(device).strip().lower().replace('cuda:', '')
    cpu = device == 'cpu'
    if cpu:
        os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
    elif device:
        os.environ['CUDA_VISIBLE_DEVICES'] = device
        assert torch.cuda.is_available(), f'CUDA unavailable, invalid device {device} requested'
    cuda = not cpu and torch.cuda.is_available()
    if cuda:
        devices = device.split(',') if device else '0'
        n = len(devices)
        if n > 1 and batch_size > 0:
            assert batch_size % n == 0, f'batch-size {batch_size} not multiple of GPU count {n}'
        space = ' ' * (len(s) + 1)
        for i, d in enumerate(devices):
            p = torch.cuda.get_device_properties(i)
            s += f'{('' if i == 0 else space)}CUDA:{d} ({p.name}, {p.total_memory / 1024 ** 2:.0f}MiB)\n'
    else:
        s += 'CPU\n'
    if not newline:
        s = s.rstrip()
    LOGGER.info(s.encode().decode('ascii', 'ignore') if platform.system() == 'Windows' else s)
    return torch.device('cuda:0' if cuda else 'cpu')

def time_sync():
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    return time.time()

def model_info(model, verbose=False, img_size=640):
    n_p = sum((x.numel() for x in model.parameters()))
    n_g = sum((x.numel() for x in model.parameters() if x.requires_grad))
    if verbose:
        print(f'{'layer':>5} {'name':>40} {'gradient':>9} {'parameters':>12} {'shape':>20} {'mu':>10} {'sigma':>10}')
        for i, (name, p) in enumerate(model.named_parameters()):
            name = name.replace('module_list.', '')
            print('%5g %40s %9s %12g %20s %10.3g %10.3g' % (i, name, p.requires_grad, p.numel(), list(p.shape), p.mean(), p.std()))
    try:
        from thop import profile
        stride = max(int(model.stride.max()), 32) if hasattr(model, 'stride') else 32
        img = torch.zeros((1, model.yaml.get('ch', 3), stride, stride), device=next(model.parameters()).device)
        flops = profile(deepcopy(model), inputs=(img,), verbose=False)[0] / 1000000000.0 * 2
        img_size = img_size if isinstance(img_size, list) else [img_size, img_size]
        fs = ', %.1f GFLOPs' % (flops * img_size[0] / stride * img_size[1] / stride)
    except (ImportError, Exception):
        fs = ''
    LOGGER.info(f'Model Summary: {len(list(model.modules()))} layers, {n_p} parameters, {n_g} gradients{fs}')

class Loggers:

    def __init__(self, save_dir=None, weights=None, opt=None, hyp=None, logger=None, include=LOGGERS):
        self.save_dir = save_dir
        self.weights = weights
        self.opt = opt
        self.hyp = hyp
        self.logger = logger
        self.include = include
        self.keys = ['train/box_loss', 'train/obj_loss', 'train/cls_loss', 'metrics/precision', 'metrics/recall', 'metrics/mAP_0.5', 'metrics/mAP_0.5:0.95', 'val/box_loss', 'val/obj_loss', 'val/cls_loss', 'x/lr0', 'x/lr1', 'x/lr2']
        self.best_keys = ['best/epoch', 'best/precision', 'best/recall', 'best/mAP_0.5', 'best/mAP_0.5:0.95']
        for k in LOGGERS:
            setattr(self, k, None)
        self.csv = True
        if not wandb:
            prefix = colorstr('Weights & Biases: ')
            s = f"{prefix}run 'pip install wandb' to automatically track and visualize YOLOv5 🚀 runs (RECOMMENDED)"
            print(emojis(s))
        s = self.save_dir
        if 'tb' in self.include and (not self.opt.evolve):
            prefix = colorstr('TensorBoard: ')
            self.logger.info(f"{prefix}Start with 'tensorboard --logdir {s.parent}', view at http://localhost:6006/")
            self.tb = SummaryWriter(str(s))
        if wandb and 'wandb' in self.include:
            wandb_artifact_resume = isinstance(self.opt.resume, str) and self.opt.resume.startswith('wandb-artifact://')
            run_id = torch.load(self.weights).get('wandb_id') if self.opt.resume and (not wandb_artifact_resume) else None
            self.opt.hyp = self.hyp
            self.wandb = WandbLogger(self.opt, run_id)
        else:
            self.wandb = None

    def on_pretrain_routine_end(self):
        paths = self.save_dir.glob('*labels*.jpg')
        if self.wandb:
            self.wandb.log({'Labels': [wandb.Image(str(x), caption=x.name) for x in paths]})

    def on_train_batch_end(self, ni, model, imgs, targets, paths, plots, sync_bn):
        if plots:
            if ni == 0:
                if not sync_bn:
                    with warnings.catch_warnings():
                        warnings.simplefilter('ignore')
                        self.tb.add_graph(torch.jit.trace(de_parallel(model), imgs[0:1], strict=False), [])
            if ni < 3:
                f = self.save_dir / f'train_batch{ni}.jpg'
                Thread(target=plot_images, args=(imgs, targets, paths, f), daemon=True).start()
            if self.wandb and ni == 10:
                files = sorted(self.save_dir.glob('train*.jpg'))
                self.wandb.log({'Mosaics': [wandb.Image(str(f), caption=f.name) for f in files if f.exists()]})

    def on_train_epoch_end(self, epoch):
        if self.wandb:
            self.wandb.current_epoch = epoch + 1

    def on_val_image_end(self, pred, predn, path, names, im):
        if self.wandb:
            self.wandb.val_one_image(pred, predn, path, names, im)

    def on_val_end(self):
        if self.wandb:
            files = sorted(self.save_dir.glob('val*.jpg'))
            self.wandb.log({'Validation': [wandb.Image(str(f), caption=f.name) for f in files]})

    def on_fit_epoch_end(self, vals, epoch, best_fitness, fi):
        x = {k: v for k, v in zip(self.keys, vals)}
        if self.csv:
            file = self.save_dir / 'results.csv'
            n = len(x) + 1
            s = '' if file.exists() else ('%20s,' * n % tuple(['epoch'] + self.keys)).rstrip(',') + '\n'
            with open(file, 'a') as f:
                f.write(s + ('%20.5g,' * n % tuple([epoch] + vals)).rstrip(',') + '\n')
        if self.tb:
            for k, v in x.items():
                self.tb.add_scalar(k, v, epoch)
        if self.wandb:
            if best_fitness == fi:
                best_results = [epoch] + vals[3:7]
                for i, name in enumerate(self.best_keys):
                    self.wandb.wandb_run.summary[name] = best_results[i]
            self.wandb.log(x)
            self.wandb.end_epoch(best_result=best_fitness == fi)

    def on_model_save(self, last, epoch, final_epoch, best_fitness, fi):
        if self.wandb:
            if ((epoch + 1) % self.opt.save_period == 0 and (not final_epoch)) and self.opt.save_period != -1:
                self.wandb.log_model(last.parent, self.opt, epoch, fi, best_model=best_fitness == fi)

    def on_train_end(self, last, best, plots, epoch, results):
        if plots:
            plot_results(file=self.save_dir / 'results.csv')
        files = ['results.png', 'confusion_matrix.png', *(f'{x}_curve.png' for x in ('F1', 'PR', 'P', 'R'))]
        files = [self.save_dir / f for f in files if (self.save_dir / f).exists()]
        if self.tb:
            import cv2
            for f in files:
                self.tb.add_image(f.stem, cv2.imread(str(f))[..., ::-1], epoch, dataformats='HWC')
        if self.wandb:
            self.wandb.log({k: v for k, v in zip(self.keys[3:10], results)})
            self.wandb.log({'Results': [wandb.Image(str(f), caption=f.name) for f in files]})
            if not self.opt.evolve:
                wandb.log_artifact(str(best if best.exists() else last), type='model', name='run_' + self.wandb.wandb_run.id + '_model', aliases=['latest', 'best', 'stripped'])
                self.wandb.finish_run()
            else:
                self.wandb.finish_run()
                self.wandb = WandbLogger(self.opt)

    def on_params_update(self, params):
        if self.wandb:
            self.wandb.wandb_run.config.update(params, allow_val_change=True)

def __init__(self, save_dir=None, weights=None, opt=None, hyp=None, logger=None, include=LOGGERS):
    self.save_dir = save_dir
    self.weights = weights
    self.opt = opt
    self.hyp = hyp
    self.logger = logger
    self.include = include
    self.keys = ['train/box_loss', 'train/obj_loss', 'train/cls_loss', 'metrics/precision', 'metrics/recall', 'metrics/mAP_0.5', 'metrics/mAP_0.5:0.95', 'val/box_loss', 'val/obj_loss', 'val/cls_loss', 'x/lr0', 'x/lr1', 'x/lr2']
    self.best_keys = ['best/epoch', 'best/precision', 'best/recall', 'best/mAP_0.5', 'best/mAP_0.5:0.95']
    for k in LOGGERS:
        setattr(self, k, None)
    self.csv = True
    if not wandb:
        prefix = colorstr('Weights & Biases: ')
        s = f"{prefix}run 'pip install wandb' to automatically track and visualize YOLOv5 🚀 runs (RECOMMENDED)"
        print(emojis(s))
    s = self.save_dir
    if 'tb' in self.include and (not self.opt.evolve):
        prefix = colorstr('TensorBoard: ')
        self.logger.info(f"{prefix}Start with 'tensorboard --logdir {s.parent}', view at http://localhost:6006/")
        self.tb = SummaryWriter(str(s))
    if wandb and 'wandb' in self.include:
        wandb_artifact_resume = isinstance(self.opt.resume, str) and self.opt.resume.startswith('wandb-artifact://')
        run_id = torch.load(self.weights).get('wandb_id') if self.opt.resume and (not wandb_artifact_resume) else None
        self.opt.hyp = self.hyp
        self.wandb = WandbLogger(self.opt, run_id)
    else:
        self.wandb = None

def on_pretrain_routine_end(self):
    paths = self.save_dir.glob('*labels*.jpg')
    if self.wandb:
        self.wandb.log({'Labels': [wandb.Image(str(x), caption=x.name) for x in paths]})

def on_val_end(self):
    if self.wandb:
        files = sorted(self.save_dir.glob('val*.jpg'))
        self.wandb.log({'Validation': [wandb.Image(str(f), caption=f.name) for f in files]})

def check_wandb_config_file(data_config_file):
    wandb_config = '_wandb.'.join(data_config_file.rsplit('.', 1))
    if Path(wandb_config).is_file():
        return wandb_config
    return data_config_file

def check_wandb_dataset(data_file):
    is_trainset_wandb_artifact = False
    is_valset_wandb_artifact = False
    if check_file(data_file) and data_file.endswith('.yaml'):
        with open(data_file, errors='ignore') as f:
            data_dict = yaml.safe_load(f)
        is_trainset_wandb_artifact = isinstance(data_dict['train'], str) and data_dict['train'].startswith(WANDB_ARTIFACT_PREFIX)
        is_valset_wandb_artifact = isinstance(data_dict['val'], str) and data_dict['val'].startswith(WANDB_ARTIFACT_PREFIX)
    if is_trainset_wandb_artifact or is_valset_wandb_artifact:
        return data_dict
    else:
        return check_dataset(data_file)

def get_run_info(run_path):
    run_path = Path(remove_prefix(run_path, WANDB_ARTIFACT_PREFIX))
    run_id = run_path.stem
    project = run_path.parent.stem
    entity = run_path.parent.parent.stem
    model_artifact_name = 'run_' + run_id + '_model'
    return (entity, project, run_id, model_artifact_name)

def check_wandb_resume(opt):
    process_wandb_config_ddp_mode(opt) if RANK not in [-1, 0] else None
    if isinstance(opt.resume, str):
        if opt.resume.startswith(WANDB_ARTIFACT_PREFIX):
            if RANK not in [-1, 0]:
                entity, project, run_id, model_artifact_name = get_run_info(opt.resume)
                api = wandb.Api()
                artifact = api.artifact(entity + '/' + project + '/' + model_artifact_name + ':latest')
                modeldir = artifact.download()
                opt.weights = str(Path(modeldir) / 'last.pt')
            return True
    return None

def process_wandb_config_ddp_mode(opt):
    with open(check_file(opt.data), errors='ignore') as f:
        data_dict = yaml.safe_load(f)
    train_dir, val_dir = (None, None)
    if isinstance(data_dict['train'], str) and data_dict['train'].startswith(WANDB_ARTIFACT_PREFIX):
        api = wandb.Api()
        train_artifact = api.artifact(remove_prefix(data_dict['train']) + ':' + opt.artifact_alias)
        train_dir = train_artifact.download()
        train_path = Path(train_dir) / 'data/images/'
        data_dict['train'] = str(train_path)
    if isinstance(data_dict['val'], str) and data_dict['val'].startswith(WANDB_ARTIFACT_PREFIX):
        api = wandb.Api()
        val_artifact = api.artifact(remove_prefix(data_dict['val']) + ':' + opt.artifact_alias)
        val_dir = val_artifact.download()
        val_path = Path(val_dir) / 'data/images/'
        data_dict['val'] = str(val_path)
    if train_dir or val_dir:
        ddp_data_path = str(Path(val_dir) / 'wandb_local_data.yaml')
        with open(ddp_data_path, 'w') as f:
            yaml.safe_dump(data_dict, f)
        opt.data = ddp_data_path

class WandbLogger:
    """Log training runs, datasets, models, and predictions to Weights & Biases.

    This logger sends information to W&B at wandb.ai. By default, this information
    includes hyperparameters, system configuration and metrics, model metrics,
    and basic data metrics and analyses.

    By providing additional command line arguments to train.py, datasets,
    models and predictions can also be logged.

    For more on how this logger is used, see the Weights & Biases documentation:
    https://docs.wandb.com/guides/integrations/yolov5
    """

    def __init__(self, opt, run_id=None, job_type='Training'):
        """
        - Initialize WandbLogger instance
        - Upload dataset if opt.upload_dataset is True
        - Setup trainig processes if job_type is 'Training'

        arguments:
        opt (namespace) -- Commandline arguments for this run
        run_id (str) -- Run ID of W&B run to be resumed
        job_type (str) -- To set the job_type for this run

       """
        self.job_type = job_type
        self.wandb, self.wandb_run = (wandb, None if not wandb else wandb.run)
        self.val_artifact, self.train_artifact = (None, None)
        self.train_artifact_path, self.val_artifact_path = (None, None)
        self.result_artifact = None
        self.val_table, self.result_table = (None, None)
        self.bbox_media_panel_images = []
        self.val_table_path_map = None
        self.max_imgs_to_log = 16
        self.wandb_artifact_data_dict = None
        self.data_dict = None
        if isinstance(opt.resume, str):
            if opt.resume.startswith(WANDB_ARTIFACT_PREFIX):
                entity, project, run_id, model_artifact_name = get_run_info(opt.resume)
                model_artifact_name = WANDB_ARTIFACT_PREFIX + model_artifact_name
                assert wandb, 'install wandb to resume wandb runs'
                self.wandb_run = wandb.init(id=run_id, project=project, entity=entity, resume='allow', allow_val_change=True)
                opt.resume = model_artifact_name
        elif self.wandb:
            self.wandb_run = wandb.init(config=opt, resume='allow', project='YOLOv5' if opt.project == 'runs/train' else Path(opt.project).stem, entity=opt.entity, name=opt.name if opt.name != 'exp' else None, job_type=job_type, id=run_id, allow_val_change=True) if not wandb.run else wandb.run
        if self.wandb_run:
            if self.job_type == 'Training':
                if opt.upload_dataset:
                    if not opt.resume:
                        self.wandb_artifact_data_dict = self.check_and_upload_dataset(opt)
                if opt.resume:
                    if isinstance(opt.resume, str) and opt.resume.startswith(WANDB_ARTIFACT_PREFIX):
                        self.data_dict = dict(self.wandb_run.config.data_dict)
                    else:
                        self.data_dict = check_wandb_dataset(opt.data)
                else:
                    self.data_dict = check_wandb_dataset(opt.data)
                    self.wandb_artifact_data_dict = self.wandb_artifact_data_dict or self.data_dict
                    self.wandb_run.config.update({'data_dict': self.wandb_artifact_data_dict}, allow_val_change=True)
                self.setup_training(opt)
            if self.job_type == 'Dataset Creation':
                self.wandb_run.config.update({'upload_dataset': True})
                self.data_dict = self.check_and_upload_dataset(opt)

    def check_and_upload_dataset(self, opt):
        """
        Check if the dataset format is compatible and upload it as W&B artifact

        arguments:
        opt (namespace)-- Commandline arguments for current run

        returns:
        Updated dataset info dictionary where local dataset paths are replaced by WAND_ARFACT_PREFIX links.
        """
        assert wandb, 'Install wandb to upload dataset'
        config_path = self.log_dataset_artifact(opt.data, opt.single_cls, 'YOLOv5' if opt.project == 'runs/train' else Path(opt.project).stem)
        with open(config_path, errors='ignore') as f:
            wandb_data_dict = yaml.safe_load(f)
        return wandb_data_dict

    def setup_training(self, opt):
        """
        Setup the necessary processes for training YOLO models:
          - Attempt to download model checkpoint and dataset artifacts if opt.resume stats with WANDB_ARTIFACT_PREFIX
          - Update data_dict, to contain info of previous run if resumed and the paths of dataset artifact if downloaded
          - Setup log_dict, initialize bbox_interval

        arguments:
        opt (namespace) -- commandline arguments for this run

        """
        self.log_dict, self.current_epoch = ({}, 0)
        self.bbox_interval = opt.bbox_interval
        if isinstance(opt.resume, str):
            modeldir, _ = self.download_model_artifact(opt)
            if modeldir:
                self.weights = Path(modeldir) / 'last.pt'
                config = self.wandb_run.config
                opt.weights, opt.save_period, opt.batch_size, opt.bbox_interval, opt.epochs, opt.hyp = (str(self.weights), config.save_period, config.batch_size, config.bbox_interval, config.epochs, config.hyp)
        data_dict = self.data_dict
        if self.val_artifact is None:
            self.train_artifact_path, self.train_artifact = self.download_dataset_artifact(data_dict.get('train'), opt.artifact_alias)
            self.val_artifact_path, self.val_artifact = self.download_dataset_artifact(data_dict.get('val'), opt.artifact_alias)
        if self.train_artifact_path is not None:
            train_path = Path(self.train_artifact_path) / 'data/images/'
            data_dict['train'] = str(train_path)
        if self.val_artifact_path is not None:
            val_path = Path(self.val_artifact_path) / 'data/images/'
            data_dict['val'] = str(val_path)
        if self.val_artifact is not None:
            self.result_artifact = wandb.Artifact('run_' + wandb.run.id + '_progress', 'evaluation')
            columns = ['epoch', 'id', 'ground truth', 'prediction']
            columns.extend(self.data_dict['names'])
            self.result_table = wandb.Table(columns)
            self.val_table = self.val_artifact.get('val')
            if self.val_table_path_map is None:
                self.map_val_table_path()
        if opt.bbox_interval == -1:
            self.bbox_interval = opt.bbox_interval = opt.epochs // 10 if opt.epochs > 10 else 1
        train_from_artifact = self.train_artifact_path is not None and self.val_artifact_path is not None
        if train_from_artifact:
            self.data_dict = data_dict

    def download_dataset_artifact(self, path, alias):
        """
        download the model checkpoint artifact if the path starts with WANDB_ARTIFACT_PREFIX

        arguments:
        path -- path of the dataset to be used for training
        alias (str)-- alias of the artifact to be download/used for training

        returns:
        (str, wandb.Artifact) -- path of the downladed dataset and it's corresponding artifact object if dataset
        is found otherwise returns (None, None)
        """
        if isinstance(path, str) and path.startswith(WANDB_ARTIFACT_PREFIX):
            artifact_path = Path(remove_prefix(path, WANDB_ARTIFACT_PREFIX) + ':' + alias)
            dataset_artifact = wandb.use_artifact(artifact_path.as_posix().replace('\\', '/'))
            assert dataset_artifact is not None, "'Error: W&B dataset artifact doesn't exist'"
            datadir = dataset_artifact.download()
            return (datadir, dataset_artifact)
        return (None, None)

    def download_model_artifact(self, opt):
        """
        download the model checkpoint artifact if the resume path starts with WANDB_ARTIFACT_PREFIX

        arguments:
        opt (namespace) -- Commandline arguments for this run
        """
        if opt.resume.startswith(WANDB_ARTIFACT_PREFIX):
            model_artifact = wandb.use_artifact(remove_prefix(opt.resume, WANDB_ARTIFACT_PREFIX) + ':latest')
            assert model_artifact is not None, "Error: W&B model artifact doesn't exist"
            modeldir = model_artifact.download()
            epochs_trained = model_artifact.metadata.get('epochs_trained')
            total_epochs = model_artifact.metadata.get('total_epochs')
            is_finished = total_epochs is None
            assert not is_finished, 'training is finished, can only resume incomplete runs.'
            return (modeldir, model_artifact)
        return (None, None)

    def log_model(self, path, opt, epoch, fitness_score, best_model=False):
        """
        Log the model checkpoint as W&B artifact

        arguments:
        path (Path)   -- Path of directory containing the checkpoints
        opt (namespace) -- Command line arguments for this run
        epoch (int)  -- Current epoch number
        fitness_score (float) -- fitness score for current epoch
        best_model (boolean) -- Boolean representing if the current checkpoint is the best yet.
        """
        model_artifact = wandb.Artifact('run_' + wandb.run.id + '_model', type='model', metadata={'original_url': str(path), 'epochs_trained': epoch + 1, 'save period': opt.save_period, 'project': opt.project, 'total_epochs': opt.epochs, 'fitness_score': fitness_score})
        model_artifact.add_file(str(path / 'last.pt'), name='last.pt')
        wandb.log_artifact(model_artifact, aliases=['latest', 'last', 'epoch ' + str(self.current_epoch), 'best' if best_model else ''])
        LOGGER.info(f'Saving model artifact on epoch {epoch + 1}')

    def log_dataset_artifact(self, data_file, single_cls, project, overwrite_config=False):
        """
        Log the dataset as W&B artifact and return the new data file with W&B links

        arguments:
        data_file (str) -- the .yaml file with information about the dataset like - path, classes etc.
        single_class (boolean)  -- train multi-class data as single-class
        project (str) -- project name. Used to construct the artifact path
        overwrite_config (boolean) -- overwrites the data.yaml file if set to true otherwise creates a new
        file with _wandb postfix. Eg -> data_wandb.yaml

        returns:
        the new .yaml file with artifact links. it can be used to start training directly from artifacts
        """
        upload_dataset = self.wandb_run.config.upload_dataset
        log_val_only = isinstance(upload_dataset, str) and upload_dataset == 'val'
        self.data_dict = check_dataset(data_file)
        data = dict(self.data_dict)
        nc, names = (1, ['item']) if single_cls else (int(data['nc']), data['names'])
        names = {k: v for k, v in enumerate(names)}
        if not log_val_only:
            self.train_artifact = self.create_dataset_table(LoadImagesAndLabels(data['train'], rect=True, batch_size=1), names, name='train') if data.get('train') else None
            if data.get('train'):
                data['train'] = WANDB_ARTIFACT_PREFIX + str(Path(project) / 'train')
        self.val_artifact = self.create_dataset_table(LoadImagesAndLabels(data['val'], rect=True, batch_size=1), names, name='val') if data.get('val') else None
        if data.get('val'):
            data['val'] = WANDB_ARTIFACT_PREFIX + str(Path(project) / 'val')
        path = Path(data_file)
        if not log_val_only:
            path = (path.stem if overwrite_config else path.stem + '_wandb') + '.yaml'
            path = Path('data') / path
            data.pop('download', None)
            data.pop('path', None)
            with open(path, 'w') as f:
                yaml.safe_dump(data, f)
                LOGGER.info(f'Created dataset config file {path}')
        if self.job_type == 'Training':
            if not log_val_only:
                self.wandb_run.log_artifact(self.train_artifact)
            self.wandb_run.use_artifact(self.val_artifact)
            self.val_artifact.wait()
            self.val_table = self.val_artifact.get('val')
            self.map_val_table_path()
        else:
            self.wandb_run.log_artifact(self.train_artifact)
            self.wandb_run.log_artifact(self.val_artifact)
        return path

    def map_val_table_path(self):
        """
        Map the validation dataset Table like name of file -> it's id in the W&B Table.
        Useful for - referencing artifacts for evaluation.
        """
        self.val_table_path_map = {}
        LOGGER.info('Mapping dataset')
        for i, data in enumerate(tqdm(self.val_table.data)):
            self.val_table_path_map[data[3]] = data[0]

    def create_dataset_table(self, dataset: LoadImagesAndLabels, class_to_id: Dict[int, str], name: str='dataset'):
        """
        Create and return W&B artifact containing W&B Table of the dataset.

        arguments:
        dataset -- instance of LoadImagesAndLabels class used to iterate over the data to build Table
        class_to_id -- hash map that maps class ids to labels
        name -- name of the artifact

        returns:
        dataset artifact to be logged or used
        """
        artifact = wandb.Artifact(name=name, type='dataset')
        img_files = tqdm([dataset.path]) if isinstance(dataset.path, str) and Path(dataset.path).is_dir() else None
        img_files = tqdm(dataset.img_files) if not img_files else img_files
        for img_file in img_files:
            if Path(img_file).is_dir():
                artifact.add_dir(img_file, name='data/images')
                labels_path = 'labels'.join(dataset.path.rsplit('images', 1))
                artifact.add_dir(labels_path, name='data/labels')
            else:
                artifact.add_file(img_file, name='data/images/' + Path(img_file).name)
                label_file = Path(img2label_paths([img_file])[0])
                artifact.add_file(str(label_file), name='data/labels/' + label_file.name) if label_file.exists() else None
        table = wandb.Table(columns=['id', 'train_image', 'Classes', 'name'])
        class_set = wandb.Classes([{'id': id, 'name': name} for id, name in class_to_id.items()])
        for si, (img, labels, paths, shapes) in enumerate(tqdm(dataset)):
            box_data, img_classes = ([], {})
            for cls, *xywh in labels[:, 1:].tolist():
                cls = int(cls)
                box_data.append({'position': {'middle': [xywh[0], xywh[1]], 'width': xywh[2], 'height': xywh[3]}, 'class_id': cls, 'box_caption': '%s' % class_to_id[cls]})
                img_classes[cls] = class_to_id[cls]
            boxes = {'ground_truth': {'box_data': box_data, 'class_labels': class_to_id}}
            table.add_data(si, wandb.Image(paths, classes=class_set, boxes=boxes), list(img_classes.values()), Path(paths).name)
        artifact.add(table, name)
        return artifact

    def log_training_progress(self, predn, path, names):
        """
        Build evaluation Table. Uses reference from validation dataset table.

        arguments:
        predn (list): list of predictions in the native space in the format - [xmin, ymin, xmax, ymax, confidence, class]
        path (str): local path of the current evaluation image
        names (dict(int, str)): hash map that maps class ids to labels
        """
        class_set = wandb.Classes([{'id': id, 'name': name} for id, name in names.items()])
        box_data = []
        avg_conf_per_class = [0] * len(self.data_dict['names'])
        pred_class_count = {}
        for *xyxy, conf, cls in predn.tolist():
            if conf >= 0.25:
                cls = int(cls)
                box_data.append({'position': {'minX': xyxy[0], 'minY': xyxy[1], 'maxX': xyxy[2], 'maxY': xyxy[3]}, 'class_id': cls, 'box_caption': f'{names[cls]} {conf:.3f}', 'scores': {'class_score': conf}, 'domain': 'pixel'})
                avg_conf_per_class[cls] += conf
                if cls in pred_class_count:
                    pred_class_count[cls] += 1
                else:
                    pred_class_count[cls] = 1
        for pred_class in pred_class_count.keys():
            avg_conf_per_class[pred_class] = avg_conf_per_class[pred_class] / pred_class_count[pred_class]
        boxes = {'predictions': {'box_data': box_data, 'class_labels': names}}
        id = self.val_table_path_map[Path(path).name]
        self.result_table.add_data(self.current_epoch, id, self.val_table.data[id][1], wandb.Image(self.val_table.data[id][1], boxes=boxes, classes=class_set), *avg_conf_per_class)

    def val_one_image(self, pred, predn, path, names, im):
        """
        Log validation data for one image. updates the result Table if validation dataset is uploaded and log bbox media panel

        arguments:
        pred (list): list of scaled predictions in the format - [xmin, ymin, xmax, ymax, confidence, class]
        predn (list): list of predictions in the native space - [xmin, ymin, xmax, ymax, confidence, class]
        path (str): local path of the current evaluation image
        """
        if self.val_table and self.result_table:
            self.log_training_progress(predn, path, names)
        if len(self.bbox_media_panel_images) < self.max_imgs_to_log and self.current_epoch > 0:
            if self.current_epoch % self.bbox_interval == 0:
                box_data = [{'position': {'minX': xyxy[0], 'minY': xyxy[1], 'maxX': xyxy[2], 'maxY': xyxy[3]}, 'class_id': int(cls), 'box_caption': f'{names[cls]} {conf:.3f}', 'scores': {'class_score': conf}, 'domain': 'pixel'} for *xyxy, conf, cls in pred.tolist()]
                boxes = {'predictions': {'box_data': box_data, 'class_labels': names}}
                self.bbox_media_panel_images.append(wandb.Image(im, boxes=boxes, caption=path.name))

    def log(self, log_dict):
        """
        save the metrics to the logging dictionary

        arguments:
        log_dict (Dict) -- metrics/media to be logged in current step
        """
        if self.wandb_run:
            for key, value in log_dict.items():
                self.log_dict[key] = value

    def end_epoch(self, best_result=False):
        """
        commit the log_dict, model artifacts and Tables to W&B and flush the log_dict.

        arguments:
        best_result (boolean): Boolean representing if the result of this evaluation is best or not
        """
        if self.wandb_run:
            with all_logging_disabled():
                if self.bbox_media_panel_images:
                    self.log_dict['BoundingBoxDebugger'] = self.bbox_media_panel_images
                try:
                    wandb.log(self.log_dict)
                except BaseException as e:
                    LOGGER.info(f'An error occurred in wandb logger. The training will proceed without interruption. More info\n{e}')
                    self.wandb_run.finish()
                    self.wandb_run = None
                self.log_dict = {}
                self.bbox_media_panel_images = []
            if self.result_artifact:
                self.result_artifact.add(self.result_table, 'result')
                wandb.log_artifact(self.result_artifact, aliases=['latest', 'last', 'epoch ' + str(self.current_epoch), 'best' if best_result else ''])
                wandb.log({'evaluation': self.result_table})
                columns = ['epoch', 'id', 'ground truth', 'prediction']
                columns.extend(self.data_dict['names'])
                self.result_table = wandb.Table(columns)
                self.result_artifact = wandb.Artifact('run_' + wandb.run.id + '_progress', 'evaluation')

    def finish_run(self):
        """
        Log metrics if any and finish the current W&B run
        """
        if self.wandb_run:
            if self.log_dict:
                with all_logging_disabled():
                    wandb.log(self.log_dict)
            wandb.run.finish()

def check_and_upload_dataset(self, opt):
    """
        Check if the dataset format is compatible and upload it as W&B artifact

        arguments:
        opt (namespace)-- Commandline arguments for current run

        returns:
        Updated dataset info dictionary where local dataset paths are replaced by WAND_ARFACT_PREFIX links.
        """
    assert wandb, 'Install wandb to upload dataset'
    config_path = self.log_dataset_artifact(opt.data, opt.single_cls, 'YOLOv5' if opt.project == 'runs/train' else Path(opt.project).stem)
    with open(config_path, errors='ignore') as f:
        wandb_data_dict = yaml.safe_load(f)
    return wandb_data_dict

def download_dataset_artifact(self, path, alias):
    """
        download the model checkpoint artifact if the path starts with WANDB_ARTIFACT_PREFIX

        arguments:
        path -- path of the dataset to be used for training
        alias (str)-- alias of the artifact to be download/used for training

        returns:
        (str, wandb.Artifact) -- path of the downladed dataset and it's corresponding artifact object if dataset
        is found otherwise returns (None, None)
        """
    if isinstance(path, str) and path.startswith(WANDB_ARTIFACT_PREFIX):
        artifact_path = Path(remove_prefix(path, WANDB_ARTIFACT_PREFIX) + ':' + alias)
        dataset_artifact = wandb.use_artifact(artifact_path.as_posix().replace('\\', '/'))
        assert dataset_artifact is not None, "'Error: W&B dataset artifact doesn't exist'"
        datadir = dataset_artifact.download()
        return (datadir, dataset_artifact)
    return (None, None)

def download_model_artifact(self, opt):
    """
        download the model checkpoint artifact if the resume path starts with WANDB_ARTIFACT_PREFIX

        arguments:
        opt (namespace) -- Commandline arguments for this run
        """
    if opt.resume.startswith(WANDB_ARTIFACT_PREFIX):
        model_artifact = wandb.use_artifact(remove_prefix(opt.resume, WANDB_ARTIFACT_PREFIX) + ':latest')
        assert model_artifact is not None, "Error: W&B model artifact doesn't exist"
        modeldir = model_artifact.download()
        epochs_trained = model_artifact.metadata.get('epochs_trained')
        total_epochs = model_artifact.metadata.get('total_epochs')
        is_finished = total_epochs is None
        assert not is_finished, 'training is finished, can only resume incomplete runs.'
        return (modeldir, model_artifact)
    return (None, None)

def log_dataset_artifact(self, data_file, single_cls, project, overwrite_config=False):
    """
        Log the dataset as W&B artifact and return the new data file with W&B links

        arguments:
        data_file (str) -- the .yaml file with information about the dataset like - path, classes etc.
        single_class (boolean)  -- train multi-class data as single-class
        project (str) -- project name. Used to construct the artifact path
        overwrite_config (boolean) -- overwrites the data.yaml file if set to true otherwise creates a new
        file with _wandb postfix. Eg -> data_wandb.yaml

        returns:
        the new .yaml file with artifact links. it can be used to start training directly from artifacts
        """
    upload_dataset = self.wandb_run.config.upload_dataset
    log_val_only = isinstance(upload_dataset, str) and upload_dataset == 'val'
    self.data_dict = check_dataset(data_file)
    data = dict(self.data_dict)
    nc, names = (1, ['item']) if single_cls else (int(data['nc']), data['names'])
    names = {k: v for k, v in enumerate(names)}
    if not log_val_only:
        self.train_artifact = self.create_dataset_table(LoadImagesAndLabels(data['train'], rect=True, batch_size=1), names, name='train') if data.get('train') else None
        if data.get('train'):
            data['train'] = WANDB_ARTIFACT_PREFIX + str(Path(project) / 'train')
    self.val_artifact = self.create_dataset_table(LoadImagesAndLabels(data['val'], rect=True, batch_size=1), names, name='val') if data.get('val') else None
    if data.get('val'):
        data['val'] = WANDB_ARTIFACT_PREFIX + str(Path(project) / 'val')
    path = Path(data_file)
    if not log_val_only:
        path = (path.stem if overwrite_config else path.stem + '_wandb') + '.yaml'
        path = Path('data') / path
        data.pop('download', None)
        data.pop('path', None)
        with open(path, 'w') as f:
            yaml.safe_dump(data, f)
            LOGGER.info(f'Created dataset config file {path}')
    if self.job_type == 'Training':
        if not log_val_only:
            self.wandb_run.log_artifact(self.train_artifact)
        self.wandb_run.use_artifact(self.val_artifact)
        self.val_artifact.wait()
        self.val_table = self.val_artifact.get('val')
        self.map_val_table_path()
    else:
        self.wandb_run.log_artifact(self.train_artifact)
        self.wandb_run.log_artifact(self.val_artifact)
    return path

def map_val_table_path(self):
    """
        Map the validation dataset Table like name of file -> it's id in the W&B Table.
        Useful for - referencing artifacts for evaluation.
        """
    self.val_table_path_map = {}
    LOGGER.info('Mapping dataset')
    for i, data in enumerate(tqdm(self.val_table.data)):
        self.val_table_path_map[data[3]] = data[0]

def get_weights(weights):
    weights_list = {'resnet': '1Bw4gUsRBxy8XZDGchPJ_URQjbHItikjw', 'resnet18': '1k_v1RrDO6da_NDhBtMZL5c0QSogCmiRn', 'vgg11': '1vZcB-NaPUCovVA-pH-g-3NNJuUA948ni'}
    url = f'https://drive.google.com/uc?id={weights_list[weights]}'
    output = f'./{weights}.pkl'
    gdown.download(url, output, quiet=False)

class ClassAverages:

    def __init__(self, classes=[]):
        self.dimension_map = {}
        self.filename = os.path.abspath(os.path.dirname(__file__)) + '/class_averages.txt'
        if len(classes) == 0:
            self.load_items_from_file()
        for detection_class in classes:
            class_ = detection_class.lower()
            if class_ in self.dimension_map.keys():
                continue
            self.dimension_map[class_] = {}
            self.dimension_map[class_]['count'] = 0
            self.dimension_map[class_]['total'] = np.zeros(3, dtype=np.double)

    def add_item(self, class_, dimension):
        class_ = class_.lower()
        self.dimension_map[class_]['count'] += 1
        self.dimension_map[class_]['total'] += dimension

    def get_item(self, class_):
        class_ = class_.lower()
        return self.dimension_map[class_]['total'] / self.dimension_map[class_]['count']

    def dump_to_file(self):
        f = open(self.filename, 'w')
        f.write(json.dumps(self.dimension_map, cls=NumpyEncoder))
        f.close()

    def load_items_from_file(self):
        f = open(self.filename, 'r')
        dimension_map = json.load(f)
        for class_ in dimension_map:
            dimension_map[class_]['total'] = np.asarray(dimension_map[class_]['total'])
        self.dimension_map = dimension_map

    def recognized_class(self, class_):
        return class_.lower() in self.dimension_map

def dump_to_file(self):
    f = open(self.filename, 'w')
    f.write(json.dumps(self.dimension_map, cls=NumpyEncoder))
    f.close()

