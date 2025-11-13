# Cluster 2

def parse_opt():
    parser = argparse.ArgumentParser(description='Regressor Model Training')
    parser.add_argument('--epochs', type=int, default=10, help='Number of epochs')
    parser.add_argument('--batch_size', type=int, default=32, help='Number of batch size')
    parser.add_argument('--alpha', type=float, default=0.6, help='Aplha default=0.6 DONT CHANGE')
    parser.add_argument('--w', type=float, default=0.4, help='w DONT CHANGE')
    parser.add_argument('--num_workers', type=int, default=2, help='Total # workers, for colab & kaggle use 2')
    parser.add_argument('--lr', type=float, default=0.0001, help='Learning rate')
    parser.add_argument('--save_epoch', type=int, default=10, help='Save model every # epochs')
    parser.add_argument('--train_path', type=str, default=ROOT / 'dataset/KITTI/training', help='Training path KITTI')
    parser.add_argument('--model_path', type=str, default=ROOT / 'weights', help='Weights path, for load and save model')
    parser.add_argument('--select_model', type=str, default='resnet18', help='Model selection: {resnet18, vgg11}')
    parser.add_argument('--api_key', type=str, default='', help='API key for comet.ml')
    opt = parser.parse_args()
    return opt

def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--weights', nargs='+', type=str, default=ROOT / 'yolov5s.pt', help='model path(s)')
    parser.add_argument('--source', type=str, default=ROOT / 'eval/image_2', help='file/dir/URL/glob, 0 for webcam')
    parser.add_argument('--data', type=str, default=ROOT / 'data/coco128.yaml', help='(optional) dataset.yaml path')
    parser.add_argument('--imgsz', '--img', '--img-size', nargs='+', type=int, default=[640], help='inference size h,w')
    parser.add_argument('--device', default='', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
    parser.add_argument('--classes', default=[0, 2, 3, 5], nargs='+', type=int, help='filter by class: --classes 0, or --classes 0 2 3')
    parser.add_argument('--reg_weights', type=str, default='weights/epoch_10.pkl', help='Regressor model weights')
    parser.add_argument('--model_select', type=str, default='resnet', help='Regressor model list: resnet, vgg, eff')
    parser.add_argument('--calib_file', type=str, default=ROOT / 'eval/camera_cal/calib_cam_to_cam.txt', help='Calibration file or path')
    parser.add_argument('--show_result', action='store_true', help='Show Results with imshow')
    parser.add_argument('--save_result', action='store_true', help='Save result')
    parser.add_argument('--output_path', type=str, default=ROOT / 'output', help='Save output pat')
    opt = parser.parse_args()
    opt.imgsz *= 2 if len(opt.imgsz) == 1 else 1
    print_args(FILE.stem, opt)
    return opt

def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--weights', nargs='+', type=str, default=ROOT / 'yolov5s.pt', help='model path(s)')
    parser.add_argument('--source', type=str, default=ROOT / 'eval/image_2', help='file/dir/URL/glob, 0 for webcam')
    parser.add_argument('--data', type=str, default=ROOT / 'data/coco128.yaml', help='(optional) dataset.yaml path')
    parser.add_argument('--imgsz', '--img', '--img-size', nargs='+', type=int, default=[640], help='inference size h,w')
    parser.add_argument('--device', default='', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
    parser.add_argument('--classes', default=[0, 2, 3, 5], nargs='+', type=int, help='filter by class: --classes 0, or --classes 0 2 3')
    parser.add_argument('--reg_weights', type=str, default='weights/epoch_10.pkl', help='Regressor model weights')
    parser.add_argument('--model_select', type=str, default='resnet', help='Regressor model list: resnet, vgg, eff')
    parser.add_argument('--calib_file', type=str, default=ROOT / 'eval/camera_cal/calib_cam_to_cam.txt', help='Calibration file or path')
    parser.add_argument('--show_result', action='store_true', help='Show Results with imshow')
    parser.add_argument('--save_result', action='store_true', help='Save result')
    parser.add_argument('--output_path', type=str, default=ROOT / 'output', help='Save output pat')
    opt = parser.parse_args()
    opt.imgsz *= 2 if len(opt.imgsz) == 1 else 1
    return opt

def parse_opt():
    parser = argparse.ArgumentParser(description='Regressor Model Training')
    parser.add_argument('--train_path', type=str, default=ROOT / 'dataset_dummy/training', help='Training path KITTI')
    parser.add_argument('--checkpoint_path', type=str, default=ROOT / 'weights/checkpoint', help='Checkpoint directory')
    parser.add_argument('--model_select', type=str, default='resnet18', help='Model selection: {resnet18, vgg11}')
    parser.add_argument('--epochs', type=int, default=10, help='Number of epochs')
    parser.add_argument('--batch_size', type=int, default=32, help='Number of batch size')
    parser.add_argument('--num_workers', type=int, default=2, help='Total # workers, for colab & kaggle use 2')
    parser.add_argument('--gpu', type=int, default=0, help='Numbers of GPU, default=1')
    parser.add_argument('--val_split', type=float, default=0.2, help='Validation split percentage')
    parser.add_argument('--model_path', type=str, default=ROOT / 'weights', help='Weights path, for load and save model')
    parser.add_argument('--api_key', type=str, default='', help='API key for comet.ml')
    opt = parser.parse_args()
    return opt

class Colors:

    def __init__(self):
        hex = ('FF3838', 'FF9D97', 'FF701F', 'FFB21D', 'CFD231', '48F90A', '92CC17', '3DDB86', '1A9334', '00D4BB', '2C99A8', '00C2FF', '344593', '6473FF', '0018EC', '8438FF', '520085', 'CB38FF', 'FF95C8', 'FF37C7')
        self.palette = [self.hex2rgb('#' + c) for c in hex]
        self.n = len(self.palette)

    def __call__(self, i, bgr=False):
        c = self.palette[int(i) % self.n]
        return (c[2], c[1], c[0]) if bgr else c

    @staticmethod
    def hex2rgb(h):
        return tuple((int(h[1 + i:1 + i + 2], 16) for i in (0, 2, 4)))

def __init__(self):
    hex = ('FF3838', 'FF9D97', 'FF701F', 'FFB21D', 'CFD231', '48F90A', '92CC17', '3DDB86', '1A9334', '00D4BB', '2C99A8', '00C2FF', '344593', '6473FF', '0018EC', '8438FF', '520085', 'CB38FF', 'FF95C8', 'FF37C7')
    self.palette = [self.hex2rgb('#' + c) for c in hex]
    self.n = len(self.palette)

class InfiniteDataLoader(dataloader.DataLoader):
    """ Dataloader that reuses workers

    Uses same syntax as vanilla DataLoader
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        object.__setattr__(self, 'batch_sampler', _RepeatSampler(self.batch_sampler))
        self.iterator = super().__iter__()

    def __len__(self):
        return len(self.batch_sampler.sampler)

    def __iter__(self):
        for i in range(len(self)):
            yield next(self.iterator)

def __len__(self):
    return len(self.batch_sampler.sampler)

def __iter__(self):
    for i in range(len(self)):
        yield next(self.iterator)

class LoadStreams:

    def __init__(self, sources='streams.txt', img_size=640, stride=32, auto=True):
        self.mode = 'stream'
        self.img_size = img_size
        self.stride = stride
        if os.path.isfile(sources):
            with open(sources) as f:
                sources = [x.strip() for x in f.read().strip().splitlines() if len(x.strip())]
        else:
            sources = [sources]
        n = len(sources)
        self.imgs, self.fps, self.frames, self.threads = ([None] * n, [0] * n, [0] * n, [None] * n)
        self.sources = [clean_str(x) for x in sources]
        self.auto = auto
        for i, s in enumerate(sources):
            st = f'{i + 1}/{n}: {s}... '
            if 'youtube.com/' in s or 'youtu.be/' in s:
                check_requirements(('pafy', 'youtube_dl'))
                import pafy
                s = pafy.new(s).getbest(preftype='mp4').url
            s = eval(s) if s.isnumeric() else s
            cap = cv2.VideoCapture(s)
            assert cap.isOpened(), f'{st}Failed to open {s}'
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.fps[i] = max(cap.get(cv2.CAP_PROP_FPS) % 100, 0) or 30.0
            self.frames[i] = max(int(cap.get(cv2.CAP_PROP_FRAME_COUNT)), 0) or float('inf')
            _, self.imgs[i] = cap.read()
            self.threads[i] = Thread(target=self.update, args=[i, cap, s], daemon=True)
            LOGGER.info(f'{st} Success ({self.frames[i]} frames {w}x{h} at {self.fps[i]:.2f} FPS)')
            self.threads[i].start()
        LOGGER.info('')
        s = np.stack([letterbox(x, self.img_size, stride=self.stride, auto=self.auto)[0].shape for x in self.imgs])
        self.rect = np.unique(s, axis=0).shape[0] == 1
        if not self.rect:
            LOGGER.warning('WARNING: Stream shapes differ. For optimal performance supply similarly-shaped streams.')

    def update(self, i, cap, stream):
        n, f, read = (0, self.frames[i], 1)
        while cap.isOpened() and n < f:
            n += 1
            cap.grab()
            if n % read == 0:
                success, im = cap.retrieve()
                if success:
                    self.imgs[i] = im
                else:
                    LOGGER.warning('WARNING: Video stream unresponsive, please check your IP camera connection.')
                    self.imgs[i] = np.zeros_like(self.imgs[i])
                    cap.open(stream)
            time.sleep(1 / self.fps[i])

    def __iter__(self):
        self.count = -1
        return self

    def __next__(self):
        self.count += 1
        if not all((x.is_alive() for x in self.threads)) or cv2.waitKey(1) == ord('q'):
            cv2.destroyAllWindows()
            raise StopIteration
        img0 = self.imgs.copy()
        img = [letterbox(x, self.img_size, stride=self.stride, auto=self.rect and self.auto)[0] for x in img0]
        img = np.stack(img, 0)
        img = img[..., ::-1].transpose((0, 3, 1, 2))
        img = np.ascontiguousarray(img)
        return (self.sources, img, img0, None, '')

    def __len__(self):
        return len(self.sources)

def __len__(self):
    return len(self.sources)

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

def __len__(self):
    return len(self.img_files)

def check_suffix(file='yolov5s.pt', suffix=('.pt',), msg=''):
    if file and suffix:
        if isinstance(suffix, str):
            suffix = [suffix]
        for f in file if isinstance(file, (list, tuple)) else [file]:
            s = Path(f).suffix.lower()
            if len(s):
                assert s in suffix, f'{msg}{f} acceptable suffix is {suffix}'

def remove_prefix(from_string, prefix=WANDB_ARTIFACT_PREFIX):
    return from_string[len(prefix):]

class Dataset(data.Dataset):

    def __init__(self, path, bins=2, overlap=0.1):
        self.top_img_path = path + '/image_2/'
        self.top_label_path = path + '/label_2/'
        self.top_calib_path = path + '/calib/'
        self.global_calib = path + '/calib_cam_to_cam.txt'
        self.proj_matrix = get_P(self.global_calib)
        self.ids = [x.split('.')[0] for x in sorted(os.listdir(self.top_calib_path))]
        self.num_images = len(self.ids)
        self.bins = bins
        self.angle_bins = generate_bins(self.bins)
        self.interval = 2 * np.pi / self.bins
        self.overlap = overlap
        self.bin_ranges = []
        for i in range(0, bins):
            self.bin_ranges.append(((i * self.interval - overlap) % (2 * np.pi), (i * self.interval + self.interval + overlap) % (2 * np.pi)))
        class_list = ['Car', 'Van', 'Truck', 'Pedestrian', 'Person_sitting', 'Cyclist', 'Tram', 'Misc']
        self.averages = ClassAverages(class_list)
        self.object_list = self.get_objects(self.ids)
        self.labels = {}
        last_id = ''
        for obj in self.object_list:
            id = obj[0]
            line_num = obj[1]
            label = self.get_label(id, line_num)
            if id != last_id:
                self.labels[id] = {}
                last_id = id
            self.labels[id][str(line_num)] = label
        self.curr_id = ''
        self.curr_img = None

    def __getitem__(self, index):
        id = self.object_list[index][0]
        line_num = self.object_list[index][1]
        if id != self.curr_id:
            self.curr_id = id
            self.curr_img = cv2.imread(self.top_img_path + f'{id}.png')
        label = self.labels[id][str(line_num)]
        obj = DetectedObject(self.curr_img, label['Class'], label['Box_2D'], self.proj_matrix, label=label)
        return (obj.img, label)

    def __len__(self):
        return len(self.object_list)

    def get_objects(self, ids):
        """
        Get objects parameter from labels, like dimension and class name
        """
        objects = []
        for id in ids:
            with open(self.top_label_path + f'{id}.txt') as file:
                for line_num, line in enumerate(file):
                    line = line[:-1].split(' ')
                    obj_class = line[0]
                    if obj_class == 'DontCare':
                        continue
                    dimension = np.array([float(line[8]), float(line[9]), float(line[10])], dtype=np.double)
                    self.averages.add_item(obj_class, dimension)
                    objects.append((id, line_num))
        self.averages.dump_to_file()
        return objects

    def get_label(self, id, line_num):
        lines = open(self.top_label_path + f'{id}.txt').read().splitlines()
        label = self.format_label(lines[line_num])
        return label

    def get_bin(self, angle):
        bin_idxs = []

        def is_between(min, max, angle):
            max = max - min if max - min > 0 else max - min + 2 * np.pi
            angle = angle - min if angle - min > 0 else angle - min + 2 * np.pi
            return angle < max
        for bin_idx, bin_range in enumerate(self.bin_ranges):
            if is_between(bin_range[0], bin_range[1], angle):
                bin_idxs.append(bin_idx)
        return bin_idxs

    def format_label(self, line):
        line = line[:-1].split(' ')
        Class = line[0]
        for i in range(1, len(line)):
            line[i] = float(line[i])
        Alpha = line[3]
        Ry = line[14]
        top_left = (int(round(line[4])), int(round(line[5])))
        bottom_right = (int(round(line[6])), int(round(line[7])))
        Box_2D = [top_left, bottom_right]
        Dimension = np.array([line[8], line[9], line[10]], dtype=np.double)
        Dimension -= self.averages.get_item(Class)
        Location = [line[11], line[12], line[13]]
        Location[1] -= Dimension[0] / 2
        Orientation = np.zeros((self.bins, 2))
        Confidence = np.zeros(self.bins)
        angle = Alpha + np.pi
        bin_idxs = self.get_bin(angle)
        for bin_idx in bin_idxs:
            angle_diff = angle - self.angle_bins[bin_idx]
            Orientation[bin_idx, :] = np.array([np.cos(angle_diff), np.sin(angle_diff)])
            Confidence[bin_idx] = 1
        label = {'Class': Class, 'Box_2D': Box_2D, 'Dimensions': Dimension, 'Alpha': Alpha, 'Orientation': Orientation, 'Confidence': Confidence}
        return label

def __len__(self):
    return len(self.object_list)

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

def recognized_class(self, class_):
    return class_.lower() in self.dimension_map

class KITTIDataModule(pl.LightningDataModule):

    def __init__(self, dataset_path='/dataset/KITTI/training', batch_size=32, num_workers=2, val_split=0.1):
        super(KITTIDataModule, self).__init__()
        self.dataset_path = dataset_path
        self.val_split = val_split
        self.train_split = 1.0 - self.val_split
        self.params = {'batch_size': batch_size, 'shuffle': True, 'num_workers': num_workers}

    def setup(self, stage=None):
        """
        Split dataset to training dan validation
        """
        self.KITTI = Dataset(path=self.dataset_path)
        self.dataset_size = len(self.KITTI)
        self.train_size = round(self.train_split * self.dataset_size)
        self.val_size = self.dataset_size - self.train_size
        self.KITTI_train, self.KITTI_val = random_split(self.KITTI, [self.train_size, self.val_size])

    def train_dataloader(self):
        train_loader = DataLoader(self.KITTI_train, **self.params)
        return train_loader

    def val_dataloader(self):
        val_loader = DataLoader(self.KITTI_val, batch_size=self.params['batch_size'], shuffle=False, num_workers=self.params['num_workers'])
        return val_loader

def setup(self, stage=None):
    """
        Split dataset to training dan validation
        """
    self.KITTI = Dataset(path=self.dataset_path)
    self.dataset_size = len(self.KITTI)
    self.train_size = round(self.train_split * self.dataset_size)
    self.val_size = self.dataset_size - self.train_size
    self.KITTI_train, self.KITTI_val = random_split(self.KITTI, [self.train_size, self.val_size])

class Dataset(data.Dataset):

    def __init__(self, path, bins=2, overlap=0.1):
        self.top_img_path = path + '/image_2/'
        self.top_label_path = path + '/label_2/'
        self.top_calib_path = path + '/calib/'
        self.global_calib = path + '/calib_cam_to_cam.txt'
        self.proj_matrix = get_P(self.global_calib)
        self.ids = [x.split('.')[0] for x in sorted(os.listdir(self.top_calib_path))]
        self.num_images = len(self.ids)
        self.bins = bins
        self.angle_bins = generate_bins(self.bins)
        self.interval = 2 * np.pi / bins
        self.overlap = overlap
        self.bin_ranges = []
        for i in range(0, bins):
            self.bin_ranges.append(((i * self.interval - overlap) % (2 * np.pi), (i * self.interval + self.interval + overlap) % (2 * np.pi)))
        class_list = ['Car', 'Van', 'Truck', 'Pedestrian', 'Person_sitting', 'Cyclist', 'Tram', 'Misc']
        self.averages = ClassAverages(class_list)
        self.object_list = self.get_objects(self.ids)
        self.labels = {}
        last_id = ''
        for obj in self.object_list:
            id = obj[0]
            line_num = obj[1]
            label = self.get_label(id, line_num)
            if id != last_id:
                self.labels[id] = {}
                last_id = id
            self.labels[id][str(line_num)] = label
        self.curr_id = ''
        self.curr_img = None

    def __getitem__(self, index):
        id = self.object_list[index][0]
        line_num = self.object_list[index][1]
        if id != self.curr_id:
            self.curr_id = id
            self.curr_img = cv2.imread(self.top_img_path + f'{id}.png')
        label = self.labels[id][str(line_num)]
        obj = DetectedObject(self.curr_img, label['Class'], label['Box_2D'], self.proj_matrix, label=label)
        return (obj.img, label)

    def __len__(self):
        return len(self.object_list)

    def get_objects(self, ids):
        """
        Get objects parameter from labels, like dimension and class name
        """
        objects = []
        for id in ids:
            with open(self.top_label_path + f'{id}.txt') as file:
                for line_num, line in enumerate(file):
                    line = line[:-1].split(' ')
                    obj_class = line[0]
                    if obj_class == 'DontCare':
                        continue
                    dimension = np.array([float(line[8]), float(line[9]), float(line[10])], dtype=np.double)
                    self.averages.add_item(obj_class, dimension)
                    objects.append((id, line_num))
        self.averages.dump_to_file()
        return objects

    def get_label(self, id, line_num):
        lines = open(self.top_label_path + f'{id}.txt').read().splitlines()
        label = self.format_label(lines[line_num])
        return label

    def get_bin(self, angle):
        bin_idxs = []

        def is_between(min, max, angle):
            max = max - min if max - min > 0 else max - min + 2 * np.pi
            angle = angle - min if angle - min > 0 else angle - min + 2 * np.pi
            return angle < max
        for bin_idx, bin_range in enumerate(self.bin_ranges):
            if is_between(bin_range[0], bin_range[1], angle):
                bin_idxs.append(bin_idx)
        return bin_idxs

    def format_label(self, line):
        line = line[:-1].split(' ')
        Class = line[0]
        for i in range(1, len(line)):
            line[i] = float(line[i])
        Alpha = line[3]
        Ry = line[14]
        top_left = (int(round(line[4])), int(round(line[5])))
        bottom_right = (int(round(line[6])), int(round(line[7])))
        Box_2D = [top_left, bottom_right]
        Dimension = np.array([line[8], line[9], line[10]], dtype=np.double)
        Dimension -= self.averages.get_item(Class)
        Location = [line[11], line[12], line[13]]
        Location[1] -= Dimension[0] / 2
        Orientation = np.zeros((self.bins, 2))
        Confidence = np.zeros(self.bins)
        angle = Alpha + np.pi
        bin_idxs = self.get_bin(angle)
        for bin_idx in bin_idxs:
            angle_diff = angle - self.angle_bins[bin_idx]
            Orientation[bin_idx, :] = np.array([np.cos(angle_diff), np.sin(angle_diff)])
            Confidence[bin_idx] = 1
        label = {'Class': Class, 'Box_2D': Box_2D, 'Dimensions': Dimension, 'Alpha': Alpha, 'Orientation': Orientation, 'Confidence': Confidence}
        return label

def __len__(self):
    return len(self.object_list)

def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--weights', type=str, default=ROOT / 'yolov5s.pt', help='weights path')
    parser.add_argument('--imgsz', '--img', '--img-size', nargs='+', type=int, default=[640], help='inference size h,w')
    parser.add_argument('--batch-size', type=int, default=1, help='batch size')
    parser.add_argument('--dynamic', action='store_true', help='dynamic batch size')
    opt = parser.parse_args()
    opt.imgsz *= 2 if len(opt.imgsz) == 1 else 1
    print_args(FILE.stem, opt)
    return opt

