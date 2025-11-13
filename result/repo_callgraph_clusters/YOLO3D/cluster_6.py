# Cluster 6

def main(opt):
    detect3d(reg_weights=opt.reg_weights, model_select=opt.model_select, source=opt.source, calib_file=opt.calib_file, show_result=opt.show_result, save_result=opt.save_result, output_path=opt.output_path)

@app.route('/')
def start_page():
    print('Start')
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    FILENAME = {}
    image = request.files['image']
    image.save('static/image_eval.png')
    if 'image' in request.files:
        detect = True
        detect3d(reg_weights='weights/epoch_10.pkl', model_select='resnet', source='static', calib_file='eval/camera_cal/calib_cam_to_cam.txt', save_result=True, show_result=False, output_path='static/')
        with open('static/000.png', 'rb') as image_file:
            img_encode = base64.b64encode(image_file.read())
            to_send = 'data:image/png;base64, ' + str(img_encode, 'utf-8')
    else:
        detect = False
    return render_template('index.html', init=True, detect=detect, image_to_show=to_send)

def rotation_matrix(yaw, pitch=0, roll=0):
    tx = roll
    ty = yaw
    tz = pitch
    Rx = np.array([[1, 0, 0], [0, np.cos(tx), -np.sin(tx)], [0, np.sin(tx), np.cos(tx)]])
    Ry = np.array([[np.cos(ty), 0, np.sin(ty)], [0, 1, 0], [-np.sin(ty), 0, np.cos(ty)]])
    Rz = np.array([[np.cos(tz), -np.sin(tz), 0], [np.sin(tz), np.cos(tz), 0], [0, 0, 1]])
    return Ry.reshape([3, 3])

def get_P(calib_file):
    """
    Get matrix P_rect_02 (camera 2 RGB)
    and transform to 3 x 4 matrix
    """
    for line in open(calib_file):
        if 'P_rect_02' in line:
            cam_P = line.strip().split(' ')
            cam_P = np.asarray([float(cam_P) for cam_P in cam_P[1:]])
            matrix = np.zeros((3, 4))
            matrix = cam_P.reshape((3, 4))
            return matrix

def get_calibration_cam_to_image(cab_f):
    for line in open(cab_f):
        if 'P2:' in line:
            cam_to_img = line.strip().split(' ')
            cam_to_img = np.asarray([float(number) for number in cam_to_img[1:]])
            cam_to_img = np.reshape(cam_to_img, (3, 4))
            return cam_to_img
    file_not_found(cab_f)

def get_R0(cab_f):
    for line in open(cab_f):
        if 'R0_rect:' in line:
            R0 = line.strip().split(' ')
            R0 = np.asarray([float(number) for number in R0[1:]])
            R0 = np.reshape(R0, (3, 3))
            R0_rect = np.zeros([4, 4])
            R0_rect[3, 3] = 1
            R0_rect[:3, :3] = R0
            return R0_rect

def get_tr_to_velo(cab_f):
    for line in open(cab_f):
        if 'Tr_velo_to_cam:' in line:
            Tr = line.strip().split(' ')
            Tr = np.asarray([float(number) for number in Tr[1:]])
            Tr = np.reshape(Tr, (3, 4))
            Tr_to_velo = np.zeros([4, 4])
            Tr_to_velo[3, 3] = 1
            Tr_to_velo[:3, :4] = Tr
            return Tr_to_velo

def print_results(k, verbose=True):
    k = k[np.argsort(k.prod(1))]
    x, best = metric(k, wh0)
    bpr, aat = ((best > thr).float().mean(), (x > thr).float().mean() * n)
    s = f'{PREFIX}thr={thr:.2f}: {bpr:.4f} best possible recall, {aat:.2f} anchors past thr\n{PREFIX}n={n}, img_size={img_size}, metric_all={x.mean():.3f}/{best.mean():.3f}-mean/best, past_thr={x[x > thr].mean():.3f}-mean: '
    for i, x in enumerate(k):
        s += '%i,%i, ' % (round(x[0]), round(x[1]))
    if verbose:
        LOGGER.info(s[:-2])
    return k

def copy_paste(im, labels, segments, p=0.5):
    n = len(segments)
    if p and n:
        h, w, c = im.shape
        im_new = np.zeros(im.shape, np.uint8)
        for j in random.sample(range(n), k=round(p * n)):
            l, s = (labels[j], segments[j])
            box = (w - l[3], l[2], w - l[1], l[4])
            ioa = bbox_ioa(box, labels[:, 1:5])
            if (ioa < 0.3).all():
                labels = np.concatenate((labels, [[l[0], *box]]), 0)
                segments.append(np.concatenate((w - s[:, 0:1], s[:, 1:2]), 1))
                cv2.drawContours(im_new, [segments[j].astype(np.int32)], -1, (255, 255, 255), cv2.FILLED)
        result = cv2.bitwise_and(src1=im, src2=im_new)
        result = cv2.flip(result, 1)
        i = result > 0
        im[i] = result[i]
    return (im, labels, segments)

class Annotator:
    if RANK in (-1, 0):
        check_font()

    def __init__(self, im, line_width=None, font_size=None, font='Arial.ttf', pil=False, example='abc'):
        assert im.data.contiguous, 'Image not contiguous. Apply np.ascontiguousarray(im) to Annotator() input images.'
        self.pil = pil or not is_ascii(example) or is_chinese(example)
        if self.pil:
            self.im = im if isinstance(im, Image.Image) else Image.fromarray(im)
            self.draw = ImageDraw.Draw(self.im)
            self.font = check_font(font='Arial.Unicode.ttf' if is_chinese(example) else font, size=font_size or max(round(sum(self.im.size) / 2 * 0.035), 12))
        else:
            self.im = im
        self.lw = line_width or max(round(sum(im.shape) / 2 * 0.003), 2)

    def box_label(self, box, label='', color=(128, 128, 128), txt_color=(255, 255, 255)):
        if self.pil or not is_ascii(label):
            self.draw.rectangle(box, width=self.lw, outline=color)
            if label:
                w, h = self.font.getsize(label)
                outside = box[1] - h >= 0
                self.draw.rectangle([box[0], box[1] - h if outside else box[1], box[0] + w + 1, box[1] + 1 if outside else box[1] + h + 1], fill=color)
                self.draw.text((box[0], box[1] - h if outside else box[1]), label, fill=txt_color, font=self.font)
        else:
            p1, p2 = ((int(box[0]), int(box[1])), (int(box[2]), int(box[3])))
            cv2.rectangle(self.im, p1, p2, color, thickness=self.lw, lineType=cv2.LINE_AA)
            if label:
                tf = max(self.lw - 1, 1)
                w, h = cv2.getTextSize(label, 0, fontScale=self.lw / 3, thickness=tf)[0]
                outside = p1[1] - h - 3 >= 0
                p2 = (p1[0] + w, p1[1] - h - 3 if outside else p1[1] + h + 3)
                cv2.rectangle(self.im, p1, p2, color, -1, cv2.LINE_AA)
                cv2.putText(self.im, label, (p1[0], p1[1] - 2 if outside else p1[1] + h + 2), 0, self.lw / 3, txt_color, thickness=tf, lineType=cv2.LINE_AA)

    def rectangle(self, xy, fill=None, outline=None, width=1):
        self.draw.rectangle(xy, fill, outline, width)

    def text(self, xy, text, txt_color=(255, 255, 255)):
        w, h = self.font.getsize(text)
        self.draw.text((xy[0], xy[1] - h + 1), text, fill=txt_color, font=self.font)

    def result(self):
        return np.asarray(self.im)

def result(self):
    return np.asarray(self.im)

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

def new_video(self, path):
    self.frame = 0
    self.cap = cv2.VideoCapture(path)
    self.frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

class LoadWebcam:

    def __init__(self, pipe='0', img_size=640, stride=32):
        self.img_size = img_size
        self.stride = stride
        self.pipe = eval(pipe) if pipe.isnumeric() else pipe
        self.cap = cv2.VideoCapture(self.pipe)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)

    def __iter__(self):
        self.count = -1
        return self

    def __next__(self):
        self.count += 1
        if cv2.waitKey(1) == ord('q'):
            self.cap.release()
            cv2.destroyAllWindows()
            raise StopIteration
        ret_val, img0 = self.cap.read()
        img0 = cv2.flip(img0, 1)
        assert ret_val, f'Camera Error {self.pipe}'
        img_path = 'webcam.jpg'
        s = f'webcam {self.count}: '
        img = letterbox(img0, self.img_size, stride=self.stride)[0]
        img = img.transpose((2, 0, 1))[::-1]
        img = np.ascontiguousarray(img)
        return (img_path, img, img0, None, s)

    def __len__(self):
        return 0

def __init__(self, pipe='0', img_size=640, stride=32):
    self.img_size = img_size
    self.stride = stride
    self.pipe = eval(pipe) if pipe.isnumeric() else pipe
    self.cap = cv2.VideoCapture(self.pipe)
    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)

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

def extract_boxes(path='../datasets/coco128'):
    path = Path(path)
    shutil.rmtree(path / 'classifier') if (path / 'classifier').is_dir() else None
    files = list(path.rglob('*.*'))
    n = len(files)
    for im_file in tqdm(files, total=n):
        if im_file.suffix[1:] in IMG_FORMATS:
            im = cv2.imread(str(im_file))[..., ::-1]
            h, w = im.shape[:2]
            lb_file = Path(img2label_paths([str(im_file)])[0])
            if Path(lb_file).exists():
                with open(lb_file) as f:
                    lb = np.array([x.split() for x in f.read().strip().splitlines()], dtype=np.float32)
                for j, x in enumerate(lb):
                    c = int(x[0])
                    f = path / 'classifier' / f'{c}' / f'{path.stem}_{im_file.stem}_{j}.jpg'
                    if not f.parent.is_dir():
                        f.parent.mkdir(parents=True)
                    b = x[1:] * [w, h, w, h]
                    b[2:] = b[2:] * 1.2 + 3
                    b = xywh2xyxy(b.reshape(-1, 4)).ravel().astype(np.int)
                    b[[0, 2]] = np.clip(b[[0, 2]], 0, w)
                    b[[1, 3]] = np.clip(b[[1, 3]], 0, h)
                    assert cv2.imwrite(str(f), im[b[1]:b[3], b[0]:b[2]]), f'box failure in {f}'

def verify_image_label(args):
    im_file, lb_file, prefix = args
    nm, nf, ne, nc, msg, segments = (0, 0, 0, 0, '', [])
    try:
        im = Image.open(im_file)
        im.verify()
        shape = exif_size(im)
        assert (shape[0] > 9) & (shape[1] > 9), f'image size {shape} <10 pixels'
        assert im.format.lower() in IMG_FORMATS, f'invalid image format {im.format}'
        if im.format.lower() in ('jpg', 'jpeg'):
            with open(im_file, 'rb') as f:
                f.seek(-2, 2)
                if f.read() != b'\xff\xd9':
                    ImageOps.exif_transpose(Image.open(im_file)).save(im_file, 'JPEG', subsampling=0, quality=100)
                    msg = f'{prefix}WARNING: {im_file}: corrupt JPEG restored and saved'
        if os.path.isfile(lb_file):
            nf = 1
            with open(lb_file) as f:
                l = [x.split() for x in f.read().strip().splitlines() if len(x)]
                if any([len(x) > 8 for x in l]):
                    classes = np.array([x[0] for x in l], dtype=np.float32)
                    segments = [np.array(x[1:], dtype=np.float32).reshape(-1, 2) for x in l]
                    l = np.concatenate((classes.reshape(-1, 1), segments2boxes(segments)), 1)
                l = np.array(l, dtype=np.float32)
            nl = len(l)
            if nl:
                assert l.shape[1] == 5, f'labels require 5 columns, {l.shape[1]} columns detected'
                assert (l >= 0).all(), f'negative label values {l[l < 0]}'
                assert (l[:, 1:] <= 1).all(), f'non-normalized or out of bounds coordinates {l[:, 1:][l[:, 1:] > 1]}'
                _, i = np.unique(l, axis=0, return_index=True)
                if len(i) < nl:
                    l = l[i]
                    if segments:
                        segments = segments[i]
                    msg = f'{prefix}WARNING: {im_file}: {nl - len(i)} duplicate labels removed'
            else:
                ne = 1
                l = np.zeros((0, 5), dtype=np.float32)
        else:
            nm = 1
            l = np.zeros((0, 5), dtype=np.float32)
        return (im_file, l, shape, segments, nm, nf, ne, nc, msg)
    except Exception as e:
        nc = 1
        msg = f'{prefix}WARNING: {im_file}: ignoring corrupt image/label: {e}'
        return [None, None, None, None, nm, nf, ne, nc, msg]

def round_labels(labels):
    return [[int(c), *(round(x, 4) for x in points)] for c, *points in labels]

def get_token(cookie='./cookie'):
    with open(cookie) as f:
        for line in f:
            if 'download' in line:
                return line.split()[-1]
    return ''

def check_version(current='0.0.0', minimum='0.0.0', name='version ', pinned=False, hard=False, verbose=False):
    current, minimum = (pkg.parse_version(x) for x in (current, minimum))
    result = current == minimum if pinned else current >= minimum
    s = f'{name}{minimum} required by YOLOv5, but {name}{current} is currently installed'
    if hard:
        assert result, s
    if verbose and (not result):
        LOGGER.warning(s)
    return result

def segment2box(segment, width=640, height=640):
    x, y = segment.T
    inside = (x >= 0) & (y >= 0) & (x <= width) & (y <= height)
    x, y = (x[inside], y[inside])
    return np.array([x.min(), y.min(), x.max(), y.max()]) if any(x) else np.zeros((1, 4))

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

def __init__(self, nc, conf=0.25, iou_thres=0.45):
    self.matrix = np.zeros((nc + 1, nc + 1))
    self.nc = nc
    self.conf = conf
    self.iou_thres = iou_thres

class EarlyStopping:

    def __init__(self, patience=30):
        self.best_fitness = 0.0
        self.best_epoch = 0
        self.patience = patience or float('inf')
        self.possible_stop = False

    def __call__(self, epoch, fitness):
        if fitness >= self.best_fitness:
            self.best_epoch = epoch
            self.best_fitness = fitness
        delta = epoch - self.best_epoch
        self.possible_stop = delta >= self.patience - 1
        stop = delta >= self.patience
        if stop:
            LOGGER.info(f'Stopping training early as no improvement observed in last {self.patience} epochs. Best results observed at epoch {self.best_epoch}, best model saved as best.pt.\nTo update EarlyStopping(patience={self.patience}) pass a new patience value, i.e. `python train.py --patience 300` or use `--patience 0` to disable EarlyStopping.')
        return stop

def __init__(self, patience=30):
    self.best_fitness = 0.0
    self.best_epoch = 0
    self.patience = patience or float('inf')
    self.possible_stop = False

@app.route(DETECTION_URL, methods=['POST'])
def predict():
    if not request.method == 'POST':
        return
    if request.files.get('image'):
        image_file = request.files['image']
        image_bytes = image_file.read()
        img = Image.open(io.BytesIO(image_bytes))
        results = model(img, size=640)
        return results.pandas().xyxy[0].to_json(orient='records')

def generate_bins(bins):
    angle_bins = np.zeros(bins)
    interval = 2 * np.pi / bins
    for i in range(1, bins):
        angle_bins[i] = i * interval
    angle_bins += interval / 2
    return angle_bins

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

def load_items_from_file(self):
    f = open(self.filename, 'r')
    dimension_map = json.load(f)
    for class_ in dimension_map:
        dimension_map[class_]['total'] = np.asarray(dimension_map[class_]['total'])
    self.dimension_map = dimension_map

def generate_bins(bins):
    angle_bins = np.zeros(bins)
    interval = 2 * np.pi / bins
    for i in range(1, bins):
        angle_bins[i] = i * interval
    angle_bins += interval / 2
    return angle_bins

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

