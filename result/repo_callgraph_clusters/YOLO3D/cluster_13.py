# Cluster 13

def box_candidates(box1, box2, wh_thr=2, ar_thr=100, area_thr=0.1, eps=1e-16):
    w1, h1 = (box1[2] - box1[0], box1[3] - box1[1])
    w2, h2 = (box2[2] - box2[0], box2[3] - box2[1])
    ar = np.maximum(w2 / (h2 + eps), h2 / (w2 + eps))
    return (w2 > wh_thr) & (h2 > wh_thr) & (w2 * h2 / (w1 * h1 + eps) > area_thr) & (ar < ar_thr)

def exif_transpose(image):
    """
    Transpose a PIL image accordingly if it has an EXIF Orientation tag.
    Inplace version of https://github.com/python-pillow/Pillow/blob/master/src/PIL/ImageOps.py exif_transpose()

    :param image: The image to transpose.
    :return: An image.
    """
    exif = image.getexif()
    orientation = exif.get(274, 1)
    if orientation > 1:
        method = {2: Image.FLIP_LEFT_RIGHT, 3: Image.ROTATE_180, 4: Image.FLIP_TOP_BOTTOM, 5: Image.TRANSPOSE, 6: Image.ROTATE_270, 7: Image.TRANSVERSE, 8: Image.ROTATE_90}.get(orientation)
        if method is not None:
            image = image.transpose(method)
            del exif[274]
            image.info['exif'] = exif.tobytes()
    return image

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

def check_imshow():
    try:
        assert not is_docker(), 'cv2.imshow() is disabled in Docker environments'
        assert not is_colab(), 'cv2.imshow() is disabled in Google Colab environments'
        cv2.imshow('test', np.zeros((1, 1, 3)))
        cv2.waitKey(1)
        cv2.destroyAllWindows()
        cv2.waitKey(1)
        return True
    except Exception as e:
        print(f'WARNING: Environment does not support cv2.imshow() or PIL Image.show() image displays\n{e}')
        return False

def make_divisible(x, divisor):
    if isinstance(divisor, torch.Tensor):
        divisor = int(divisor.max())
    return math.ceil(x / divisor) * divisor

def bbox_ioa(box1, box2, eps=1e-07):
    """ Returns the intersection over box2 area given box1, box2. Boxes are x1y1x2y2
    box1:       np.array of shape(4)
    box2:       np.array of shape(nx4)
    returns:    np.array of shape(n)
    """
    box2 = box2.transpose()
    b1_x1, b1_y1, b1_x2, b1_y2 = (box1[0], box1[1], box1[2], box1[3])
    b2_x1, b2_y1, b2_x2, b2_y2 = (box2[0], box2[1], box2[2], box2[3])
    inter_area = (np.minimum(b1_x2, b2_x2) - np.maximum(b1_x1, b2_x1)).clip(0) * (np.minimum(b1_y2, b2_y2) - np.maximum(b1_y1, b2_y1)).clip(0)
    box2_area = (b2_x2 - b2_x1) * (b2_y2 - b2_y1) + eps
    return inter_area / box2_area

def scale_img(img, ratio=1.0, same_shape=False, gs=32):
    if ratio == 1.0:
        return img
    else:
        h, w = img.shape[2:]
        s = (int(h * ratio), int(w * ratio))
        img = F.interpolate(img, size=s, mode='bilinear', align_corners=False)
        if not same_shape:
            h, w = (math.ceil(x * ratio / gs) * gs for x in (h, w))
        return F.pad(img, [0, w - s[1], 0, h - s[0]], value=0.447)

class Detect(nn.Module):
    stride = None
    onnx_dynamic = False

    def __init__(self, nc=80, anchors=(), ch=(), inplace=True):
        super().__init__()
        self.nc = nc
        self.no = nc + 5
        self.nl = len(anchors)
        self.na = len(anchors[0]) // 2
        self.grid = [torch.zeros(1)] * self.nl
        self.anchor_grid = [torch.zeros(1)] * self.nl
        self.register_buffer('anchors', torch.tensor(anchors).float().view(self.nl, -1, 2))
        self.m = nn.ModuleList((nn.Conv2d(x, self.no * self.na, 1) for x in ch))
        self.inplace = inplace

    def forward(self, x):
        z = []
        for i in range(self.nl):
            x[i] = self.m[i](x[i])
            bs, _, ny, nx = x[i].shape
            x[i] = x[i].view(bs, self.na, self.no, ny, nx).permute(0, 1, 3, 4, 2).contiguous()
            if not self.training:
                if self.onnx_dynamic or self.grid[i].shape[2:4] != x[i].shape[2:4]:
                    self.grid[i], self.anchor_grid[i] = self._make_grid(nx, ny, i)
                y = x[i].sigmoid()
                if self.inplace:
                    y[..., 0:2] = (y[..., 0:2] * 2 - 0.5 + self.grid[i]) * self.stride[i]
                    y[..., 2:4] = (y[..., 2:4] * 2) ** 2 * self.anchor_grid[i]
                else:
                    xy = (y[..., 0:2] * 2 - 0.5 + self.grid[i]) * self.stride[i]
                    wh = (y[..., 2:4] * 2) ** 2 * self.anchor_grid[i]
                    y = torch.cat((xy, wh, y[..., 4:]), -1)
                z.append(y.view(bs, -1, self.no))
        return x if self.training else (torch.cat(z, 1), x)

    def _make_grid(self, nx=20, ny=20, i=0):
        d = self.anchors[i].device
        if check_version(torch.__version__, '1.10.0'):
            yv, xv = torch.meshgrid([torch.arange(ny, device=d), torch.arange(nx, device=d)], indexing='ij')
        else:
            yv, xv = torch.meshgrid([torch.arange(ny, device=d), torch.arange(nx, device=d)])
        grid = torch.stack((xv, yv), 2).expand((1, self.na, ny, nx, 2)).float()
        anchor_grid = (self.anchors[i].clone() * self.stride[i]).view((1, self.na, 1, 1, 2)).expand((1, self.na, ny, nx, 2)).float()
        return (grid, anchor_grid)

def _make_grid(self, nx=20, ny=20, i=0):
    d = self.anchors[i].device
    if check_version(torch.__version__, '1.10.0'):
        yv, xv = torch.meshgrid([torch.arange(ny, device=d), torch.arange(nx, device=d)], indexing='ij')
    else:
        yv, xv = torch.meshgrid([torch.arange(ny, device=d), torch.arange(nx, device=d)])
    grid = torch.stack((xv, yv), 2).expand((1, self.na, ny, nx, 2)).float()
    anchor_grid = (self.anchors[i].clone() * self.stride[i]).view((1, self.na, 1, 1, 2)).expand((1, self.na, ny, nx, 2)).float()
    return (grid, anchor_grid)

class TFPad(keras.layers.Layer):

    def __init__(self, pad):
        super().__init__()
        self.pad = tf.constant([[0, 0], [pad, pad], [pad, pad], [0, 0]])

    def call(self, inputs):
        return tf.pad(inputs, self.pad, mode='constant', constant_values=0)

def call(self, inputs):
    return tf.pad(inputs, self.pad, mode='constant', constant_values=0)

class TFDetect(keras.layers.Layer):

    def __init__(self, nc=80, anchors=(), ch=(), imgsz=(640, 640), w=None):
        super().__init__()
        self.stride = tf.convert_to_tensor(w.stride.numpy(), dtype=tf.float32)
        self.nc = nc
        self.no = nc + 5
        self.nl = len(anchors)
        self.na = len(anchors[0]) // 2
        self.grid = [tf.zeros(1)] * self.nl
        self.anchors = tf.convert_to_tensor(w.anchors.numpy(), dtype=tf.float32)
        self.anchor_grid = tf.reshape(self.anchors * tf.reshape(self.stride, [self.nl, 1, 1]), [self.nl, 1, -1, 1, 2])
        self.m = [TFConv2d(x, self.no * self.na, 1, w=w.m[i]) for i, x in enumerate(ch)]
        self.training = False
        self.imgsz = imgsz
        for i in range(self.nl):
            ny, nx = (self.imgsz[0] // self.stride[i], self.imgsz[1] // self.stride[i])
            self.grid[i] = self._make_grid(nx, ny)

    def call(self, inputs):
        z = []
        x = []
        for i in range(self.nl):
            x.append(self.m[i](inputs[i]))
            ny, nx = (self.imgsz[0] // self.stride[i], self.imgsz[1] // self.stride[i])
            x[i] = tf.transpose(tf.reshape(x[i], [-1, ny * nx, self.na, self.no]), [0, 2, 1, 3])
            if not self.training:
                y = tf.sigmoid(x[i])
                xy = (y[..., 0:2] * 2 - 0.5 + self.grid[i]) * self.stride[i]
                wh = (y[..., 2:4] * 2) ** 2 * self.anchor_grid[i]
                xy /= tf.constant([[self.imgsz[1], self.imgsz[0]]], dtype=tf.float32)
                wh /= tf.constant([[self.imgsz[1], self.imgsz[0]]], dtype=tf.float32)
                y = tf.concat([xy, wh, y[..., 4:]], -1)
                z.append(tf.reshape(y, [-1, self.na * ny * nx, self.no]))
        return x if self.training else (tf.concat(z, 1), x)

    @staticmethod
    def _make_grid(nx=20, ny=20):
        xv, yv = tf.meshgrid(tf.range(nx), tf.range(ny))
        return tf.cast(tf.reshape(tf.stack([xv, yv], 2), [1, 1, ny * nx, 2]), dtype=tf.float32)

@staticmethod
def _make_grid(nx=20, ny=20):
    xv, yv = tf.meshgrid(tf.range(nx), tf.range(ny))
    return tf.cast(tf.reshape(tf.stack([xv, yv], 2), [1, 1, ny * nx, 2]), dtype=tf.float32)

class AgnosticNMS(keras.layers.Layer):

    def call(self, input, topk_all, iou_thres, conf_thres):
        return tf.map_fn(lambda x: self._nms(x, topk_all, iou_thres, conf_thres), input, fn_output_signature=(tf.float32, tf.float32, tf.float32, tf.int32), name='agnostic_nms')

    @staticmethod
    def _nms(x, topk_all=100, iou_thres=0.45, conf_thres=0.25):
        boxes, classes, scores = x
        class_inds = tf.cast(tf.argmax(classes, axis=-1), tf.float32)
        scores_inp = tf.reduce_max(scores, -1)
        selected_inds = tf.image.non_max_suppression(boxes, scores_inp, max_output_size=topk_all, iou_threshold=iou_thres, score_threshold=conf_thres)
        selected_boxes = tf.gather(boxes, selected_inds)
        padded_boxes = tf.pad(selected_boxes, paddings=[[0, topk_all - tf.shape(selected_boxes)[0]], [0, 0]], mode='CONSTANT', constant_values=0.0)
        selected_scores = tf.gather(scores_inp, selected_inds)
        padded_scores = tf.pad(selected_scores, paddings=[[0, topk_all - tf.shape(selected_boxes)[0]]], mode='CONSTANT', constant_values=-1.0)
        selected_classes = tf.gather(class_inds, selected_inds)
        padded_classes = tf.pad(selected_classes, paddings=[[0, topk_all - tf.shape(selected_boxes)[0]]], mode='CONSTANT', constant_values=-1.0)
        valid_detections = tf.shape(selected_inds)[0]
        return (padded_boxes, padded_scores, padded_classes, valid_detections)

@staticmethod
def _nms(x, topk_all=100, iou_thres=0.45, conf_thres=0.25):
    boxes, classes, scores = x
    class_inds = tf.cast(tf.argmax(classes, axis=-1), tf.float32)
    scores_inp = tf.reduce_max(scores, -1)
    selected_inds = tf.image.non_max_suppression(boxes, scores_inp, max_output_size=topk_all, iou_threshold=iou_thres, score_threshold=conf_thres)
    selected_boxes = tf.gather(boxes, selected_inds)
    padded_boxes = tf.pad(selected_boxes, paddings=[[0, topk_all - tf.shape(selected_boxes)[0]], [0, 0]], mode='CONSTANT', constant_values=0.0)
    selected_scores = tf.gather(scores_inp, selected_inds)
    padded_scores = tf.pad(selected_scores, paddings=[[0, topk_all - tf.shape(selected_boxes)[0]]], mode='CONSTANT', constant_values=-1.0)
    selected_classes = tf.gather(class_inds, selected_inds)
    padded_classes = tf.pad(selected_classes, paddings=[[0, topk_all - tf.shape(selected_boxes)[0]]], mode='CONSTANT', constant_values=-1.0)
    valid_detections = tf.shape(selected_inds)[0]
    return (padded_boxes, padded_scores, padded_classes, valid_detections)

class AutoShape(nn.Module):
    conf = 0.25
    iou = 0.45
    agnostic = False
    multi_label = False
    classes = None
    max_det = 1000
    amp = False

    def __init__(self, model):
        super().__init__()
        LOGGER.info('Adding AutoShape... ')
        copy_attr(self, model, include=('yaml', 'nc', 'hyp', 'names', 'stride', 'abc'), exclude=())
        self.dmb = isinstance(model, DetectMultiBackend)
        self.pt = not self.dmb or model.pt
        self.model = model.eval()

    def _apply(self, fn):
        self = super()._apply(fn)
        if self.pt:
            m = self.model.model.model[-1] if self.dmb else self.model.model[-1]
            m.stride = fn(m.stride)
            m.grid = list(map(fn, m.grid))
            if isinstance(m.anchor_grid, list):
                m.anchor_grid = list(map(fn, m.anchor_grid))
        return self

    @torch.no_grad()
    def forward(self, imgs, size=640, augment=False, profile=False):
        t = [time_sync()]
        p = next(self.model.parameters()) if self.pt else torch.zeros(1)
        autocast = self.amp and p.device.type != 'cpu'
        if isinstance(imgs, torch.Tensor):
            with amp.autocast(enabled=autocast):
                return self.model(imgs.to(p.device).type_as(p), augment, profile)
        n, imgs = (len(imgs), imgs) if isinstance(imgs, list) else (1, [imgs])
        shape0, shape1, files = ([], [], [])
        for i, im in enumerate(imgs):
            f = f'image{i}'
            if isinstance(im, (str, Path)):
                im, f = (Image.open(requests.get(im, stream=True).raw if str(im).startswith('http') else im), im)
                im = np.asarray(exif_transpose(im))
            elif isinstance(im, Image.Image):
                im, f = (np.asarray(exif_transpose(im)), getattr(im, 'filename', f) or f)
            files.append(Path(f).with_suffix('.jpg').name)
            if im.shape[0] < 5:
                im = im.transpose((1, 2, 0))
            im = im[..., :3] if im.ndim == 3 else np.tile(im[..., None], 3)
            s = im.shape[:2]
            shape0.append(s)
            g = size / max(s)
            shape1.append([y * g for y in s])
            imgs[i] = im if im.data.contiguous else np.ascontiguousarray(im)
        shape1 = [make_divisible(x, self.stride) for x in np.stack(shape1, 0).max(0)]
        x = [letterbox(im, new_shape=shape1 if self.pt else size, auto=False)[0] for im in imgs]
        x = np.stack(x, 0) if n > 1 else x[0][None]
        x = np.ascontiguousarray(x.transpose((0, 3, 1, 2)))
        x = torch.from_numpy(x).to(p.device).type_as(p) / 255
        t.append(time_sync())
        with amp.autocast(enabled=autocast):
            y = self.model(x, augment, profile)
            t.append(time_sync())
            y = non_max_suppression(y if self.dmb else y[0], self.conf, iou_thres=self.iou, classes=self.classes, agnostic=self.agnostic, multi_label=self.multi_label, max_det=self.max_det)
            for i in range(n):
                scale_coords(shape1, y[i][:, :4], shape0[i])
            t.append(time_sync())
            return Detections(imgs, y, files, t, self.names, x.shape)

@torch.no_grad()
def forward(self, imgs, size=640, augment=False, profile=False):
    t = [time_sync()]
    p = next(self.model.parameters()) if self.pt else torch.zeros(1)
    autocast = self.amp and p.device.type != 'cpu'
    if isinstance(imgs, torch.Tensor):
        with amp.autocast(enabled=autocast):
            return self.model(imgs.to(p.device).type_as(p), augment, profile)
    n, imgs = (len(imgs), imgs) if isinstance(imgs, list) else (1, [imgs])
    shape0, shape1, files = ([], [], [])
    for i, im in enumerate(imgs):
        f = f'image{i}'
        if isinstance(im, (str, Path)):
            im, f = (Image.open(requests.get(im, stream=True).raw if str(im).startswith('http') else im), im)
            im = np.asarray(exif_transpose(im))
        elif isinstance(im, Image.Image):
            im, f = (np.asarray(exif_transpose(im)), getattr(im, 'filename', f) or f)
        files.append(Path(f).with_suffix('.jpg').name)
        if im.shape[0] < 5:
            im = im.transpose((1, 2, 0))
        im = im[..., :3] if im.ndim == 3 else np.tile(im[..., None], 3)
        s = im.shape[:2]
        shape0.append(s)
        g = size / max(s)
        shape1.append([y * g for y in s])
        imgs[i] = im if im.data.contiguous else np.ascontiguousarray(im)
    shape1 = [make_divisible(x, self.stride) for x in np.stack(shape1, 0).max(0)]
    x = [letterbox(im, new_shape=shape1 if self.pt else size, auto=False)[0] for im in imgs]
    x = np.stack(x, 0) if n > 1 else x[0][None]
    x = np.ascontiguousarray(x.transpose((0, 3, 1, 2)))
    x = torch.from_numpy(x).to(p.device).type_as(p) / 255
    t.append(time_sync())
    with amp.autocast(enabled=autocast):
        y = self.model(x, augment, profile)
        t.append(time_sync())
        y = non_max_suppression(y if self.dmb else y[0], self.conf, iou_thres=self.iou, classes=self.classes, agnostic=self.agnostic, multi_label=self.multi_label, max_det=self.max_det)
        for i in range(n):
            scale_coords(shape1, y[i][:, :4], shape0[i])
        t.append(time_sync())
        return Detections(imgs, y, files, t, self.names, x.shape)

class Detections:

    def __init__(self, imgs, pred, files, times=(0, 0, 0, 0), names=None, shape=None):
        super().__init__()
        d = pred[0].device
        gn = [torch.tensor([*(im.shape[i] for i in [1, 0, 1, 0]), 1, 1], device=d) for im in imgs]
        self.imgs = imgs
        self.pred = pred
        self.names = names
        self.files = files
        self.times = times
        self.xyxy = pred
        self.xywh = [xyxy2xywh(x) for x in pred]
        self.xyxyn = [x / g for x, g in zip(self.xyxy, gn)]
        self.xywhn = [x / g for x, g in zip(self.xywh, gn)]
        self.n = len(self.pred)
        self.t = tuple(((times[i + 1] - times[i]) * 1000 / self.n for i in range(3)))
        self.s = shape

    def display(self, pprint=False, show=False, save=False, crop=False, render=False, save_dir=Path('')):
        crops = []
        for i, (im, pred) in enumerate(zip(self.imgs, self.pred)):
            s = f'image {i + 1}/{len(self.pred)}: {im.shape[0]}x{im.shape[1]} '
            if pred.shape[0]:
                for c in pred[:, -1].unique():
                    n = (pred[:, -1] == c).sum()
                    s += f'{n} {self.names[int(c)]}{'s' * (n > 1)}, '
                if show or save or render or crop:
                    annotator = Annotator(im, example=str(self.names))
                    for *box, conf, cls in reversed(pred):
                        label = f'{self.names[int(cls)]} {conf:.2f}'
                        if crop:
                            file = save_dir / 'crops' / self.names[int(cls)] / self.files[i] if save else None
                            crops.append({'box': box, 'conf': conf, 'cls': cls, 'label': label, 'im': save_one_box(box, im, file=file, save=save)})
                        else:
                            annotator.box_label(box, label, color=colors(cls))
                    im = annotator.im
            else:
                s += '(no detections)'
            im = Image.fromarray(im.astype(np.uint8)) if isinstance(im, np.ndarray) else im
            if pprint:
                LOGGER.info(s.rstrip(', '))
            if show:
                im.show(self.files[i])
            if save:
                f = self.files[i]
                im.save(save_dir / f)
                if i == self.n - 1:
                    LOGGER.info(f'Saved {self.n} image{'s' * (self.n > 1)} to {colorstr('bold', save_dir)}')
            if render:
                self.imgs[i] = np.asarray(im)
        if crop:
            if save:
                LOGGER.info(f'Saved results to {save_dir}\n')
            return crops

    def print(self):
        self.display(pprint=True)
        LOGGER.info(f'Speed: %.1fms pre-process, %.1fms inference, %.1fms NMS per image at shape {tuple(self.s)}' % self.t)

    def show(self):
        self.display(show=True)

    def save(self, save_dir='runs/detect/exp'):
        save_dir = increment_path(save_dir, exist_ok=save_dir != 'runs/detect/exp', mkdir=True)
        self.display(save=True, save_dir=save_dir)

    def crop(self, save=True, save_dir='runs/detect/exp'):
        save_dir = increment_path(save_dir, exist_ok=save_dir != 'runs/detect/exp', mkdir=True) if save else None
        return self.display(crop=True, save=save, save_dir=save_dir)

    def render(self):
        self.display(render=True)
        return self.imgs

    def pandas(self):
        new = copy(self)
        ca = ('xmin', 'ymin', 'xmax', 'ymax', 'confidence', 'class', 'name')
        cb = ('xcenter', 'ycenter', 'width', 'height', 'confidence', 'class', 'name')
        for k, c in zip(['xyxy', 'xyxyn', 'xywh', 'xywhn'], [ca, ca, cb, cb]):
            a = [[x[:5] + [int(x[5]), self.names[int(x[5])]] for x in x.tolist()] for x in getattr(self, k)]
            setattr(new, k, [pd.DataFrame(x, columns=c) for x in a])
        return new

    def tolist(self):
        r = range(self.n)
        x = [Detections([self.imgs[i]], [self.pred[i]], [self.files[i]], self.times, self.names, self.s) for i in r]
        return x

    def __len__(self):
        return self.n

def tolist(self):
    r = range(self.n)
    x = [Detections([self.imgs[i]], [self.pred[i]], [self.files[i]], self.times, self.names, self.s) for i in r]
    return x

