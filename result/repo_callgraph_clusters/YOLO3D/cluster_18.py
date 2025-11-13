# Cluster 18

@torch.no_grad()
def detect2d(weights, source, data, imgsz, device, classes):
    bbox_list = []
    source = str(source)
    device = select_device(device)
    model = DetectMultiBackend(weights, device=device, dnn=False, data=data)
    stride, names, pt, jit, onnx, engine = (model.stride, model.names, model.pt, model.jit, model.onnx, model.engine)
    imgsz = check_img_size(imgsz, s=stride)
    dataset = LoadImages(source, img_size=imgsz, stride=stride, auto=pt)
    model.warmup(imgsz=(1, 3, *imgsz), half=False)
    dt, seen = ([0.0, 0.0, 0.0], 0)
    for path, im, im0s, vid_cap, s in dataset:
        t1 = time_sync()
        im = torch.from_numpy(im).to(device)
        im = im.float()
        im /= 255
        if len(im.shape) == 3:
            im = im[None]
        t2 = time_sync()
        dt[0] += t2 - t1
        pred = model(im, augment=False, visualize=False)
        t3 = time_sync()
        dt[1] += t3 - t2
        pred = non_max_suppression(prediction=pred, classes=classes)
        dt[2] += time_sync() - t3
        for i, det in enumerate(pred):
            seen += 1
            p, im0, frame = (path, im0s.copy(), getattr(dataset, 'frame', 0))
            p = Path(p)
            s += '%gx%g ' % im.shape[2:]
            if len(det):
                for c in det[:, -1].unique():
                    n = (det[:, -1] == c).sum()
                    s += f'{n} {names[int(c)]}{'s' * (n > 1)}, '
                for *xyxy, conf, cls in reversed(det):
                    xyxy_ = torch.tensor(xyxy).view(1, 4).view(-1).tolist()
                    xyxy_ = [int(x) for x in xyxy_]
                    top_left, bottom_right = ((xyxy_[0], xyxy_[1]), (xyxy_[2], xyxy_[3]))
                    bbox = [top_left, bottom_right]
                    c = int(cls)
                    label = names[c]
                    bbox_list.append(Bbox(bbox, label))
            LOGGER.info(f'{s}Done. ({t3 - t2:.3f}s)')
    t = tuple((x / seen * 1000.0 for x in dt))
    LOGGER.info(f'Speed: %.1fms pre-process, %.1fms inference, %.1fms NMS per image at shape {(1, 3, *imgsz)}' % t)
    return bbox_list

def create_corners(dimension, location=None, R=None):
    dx = dimension[2] / 2
    dy = dimension[0] / 2
    dz = dimension[1] / 2
    x_corners = []
    y_corners = []
    z_corners = []
    for i in [1, -1]:
        for j in [1, -1]:
            for k in [1, -1]:
                x_corners.append(dx * i)
                y_corners.append(dy * j)
                z_corners.append(dz * k)
    corners = [x_corners, y_corners, z_corners]
    if R is not None:
        corners = np.dot(R, corners)
    if location is not None:
        for i, loc in enumerate(location):
            corners[i, :] = corners[i, :] + loc
    final_corners = []
    for i in range(8):
        final_corners.append([corners[0][i], corners[1][i], corners[2][i]])
    return final_corners

def calc_location(dimension, proj_matrix, box_2d, alpha, theta_ray):
    orient = alpha + theta_ray
    R = rotation_matrix(orient)
    xmin = box_2d[0][0]
    ymin = box_2d[0][1]
    xmax = box_2d[1][0]
    ymax = box_2d[1][1]
    box_corners = [xmin, ymin, xmax, ymax]
    constraints = []
    left_constraints = []
    right_constraints = []
    top_constraints = []
    bottom_constraints = []
    dx = dimension[2] / 2
    dy = dimension[0] / 2
    dz = dimension[1] / 2
    left_mult = 1
    right_mult = -1
    if alpha < np.deg2rad(92) and alpha > np.deg2rad(88):
        left_mult = 1
        right_mult = 1
    elif alpha < np.deg2rad(-88) and alpha > np.deg2rad(-92):
        left_mult = -1
        right_mult = -1
    elif alpha < np.deg2rad(90) and alpha > -np.deg2rad(90):
        left_mult = -1
        right_mult = 1
    switch_mult = -1
    if alpha > 0:
        switch_mult = 1
    for i in (-1, 1):
        left_constraints.append([left_mult * dx, i * dy, -switch_mult * dz])
    for i in (-1, 1):
        right_constraints.append([right_mult * dx, i * dy, switch_mult * dz])
    for i in (-1, 1):
        for j in (-1, 1):
            top_constraints.append([i * dx, -dy, j * dz])
    for i in (-1, 1):
        for j in (-1, 1):
            bottom_constraints.append([i * dx, dy, j * dz])
    for left in left_constraints:
        for top in top_constraints:
            for right in right_constraints:
                for bottom in bottom_constraints:
                    constraints.append([left, top, right, bottom])
    constraints = filter(lambda x: len(x) == len(set((tuple(i) for i in x))), constraints)
    pre_M = np.zeros([4, 4])
    for i in range(0, 4):
        pre_M[i][i] = 1
    best_loc = None
    best_error = [1000000000.0]
    best_X = None
    count = 0
    for constraint in constraints:
        Xa = constraint[0]
        Xb = constraint[1]
        Xc = constraint[2]
        Xd = constraint[3]
        X_array = [Xa, Xb, Xc, Xd]
        Ma = np.copy(pre_M)
        Mb = np.copy(pre_M)
        Mc = np.copy(pre_M)
        Md = np.copy(pre_M)
        M_array = [Ma, Mb, Mc, Md]
        A = np.zeros([4, 3], dtype=np.float)
        b = np.zeros([4, 1])
        indicies = [0, 1, 0, 1]
        for row, index in enumerate(indicies):
            X = X_array[row]
            M = M_array[row]
            RX = np.dot(R, X)
            M[:3, 3] = RX.reshape(3)
            M = np.dot(proj_matrix, M)
            A[row, :] = M[index, :3] - box_corners[row] * M[2, :3]
            b[row] = box_corners[row] * M[2, 3] - M[index, 3]
        loc, error, rank, s = np.linalg.lstsq(A, b, rcond=None)
        if error < best_error:
            count += 1
            best_loc = loc
            best_error = error
            best_X = X_array
    best_loc = [best_loc[0][0], best_loc[1][0], best_loc[2][0]]
    return (best_loc, best_X)

def project_3d_pt(pt, cam_to_img, calib_file=None):
    if calib_file is not None:
        cam_to_img = get_calibration_cam_to_image(calib_file)
        R0_rect = get_R0(calib_file)
        Tr_velo_to_cam = get_tr_to_velo(calib_file)
    point = np.array(pt)
    point = np.append(point, 1)
    point = np.dot(cam_to_img, point)
    point = point[:2] / point[2]
    point = point.astype(np.int16)
    return point

def plot_3d_pts(img, pts, center, calib_file=None, cam_to_img=None, relative=False, constraint_idx=None):
    if calib_file is not None:
        cam_to_img = get_calibration_cam_to_image(calib_file)
    for pt in pts:
        if relative:
            pt = [i + center[j] for j, i in enumerate(pt)]
        point = project_3d_pt(pt, cam_to_img)
        color = cv_colors.RED.value
        if constraint_idx is not None:
            color = constraint_to_color(constraint_idx)
        cv2.circle(img, (point[0], point[1]), 3, color, thickness=-1)

def plot_3d_box(img, cam_to_img, ry, dimension, center):
    R = rotation_matrix(ry)
    corners = create_corners(dimension, location=center, R=R)
    box_3d = []
    for corner in corners:
        point = project_3d_pt(corner, cam_to_img)
        point[0] = int(point[0] * 1242 / 640)
        point[1] = int(point[1] * 375 / 224)
        box_3d.append(point)
    cv2.line(img, (box_3d[0][0], box_3d[0][1]), (box_3d[2][0], box_3d[2][1]), cv_colors.GREEN.value, 2)
    cv2.line(img, (box_3d[4][0], box_3d[4][1]), (box_3d[6][0], box_3d[6][1]), cv_colors.GREEN.value, 2)
    cv2.line(img, (box_3d[0][0], box_3d[0][1]), (box_3d[4][0], box_3d[4][1]), cv_colors.GREEN.value, 2)
    cv2.line(img, (box_3d[2][0], box_3d[2][1]), (box_3d[6][0], box_3d[6][1]), cv_colors.GREEN.value, 2)
    cv2.line(img, (box_3d[1][0], box_3d[1][1]), (box_3d[3][0], box_3d[3][1]), cv_colors.GREEN.value, 2)
    cv2.line(img, (box_3d[1][0], box_3d[1][1]), (box_3d[5][0], box_3d[5][1]), cv_colors.GREEN.value, 2)
    cv2.line(img, (box_3d[7][0], box_3d[7][1]), (box_3d[3][0], box_3d[3][1]), cv_colors.GREEN.value, 2)
    cv2.line(img, (box_3d[7][0], box_3d[7][1]), (box_3d[5][0], box_3d[5][1]), cv_colors.GREEN.value, 2)
    for i in range(0, 7, 2):
        cv2.line(img, (box_3d[i][0], box_3d[i][1]), (box_3d[i + 1][0], box_3d[i + 1][1]), cv_colors.GREEN.value, 2)
    frame = np.zeros_like(img, np.uint8)
    cv2.fillPoly(frame, np.array([[[box_3d[0]], [box_3d[1]], [box_3d[3]], [box_3d[2]]]], dtype=np.int32), cv_colors.BLUE.value)
    alpha = 0.5
    mask = frame.astype(bool)
    img[mask] = cv2.addWeighted(img, alpha, frame, 1 - alpha, 0)[mask]

def plot_2d_box(img, box_2d):
    pt1, pt2, pt3, pt4 = create_2d_box(box_2d)
    cv2.line(img, pt1, pt2, cv_colors.BLUE.value, 2)
    cv2.line(img, pt2, pt3, cv_colors.BLUE.value, 2)
    cv2.line(img, pt3, pt4, cv_colors.BLUE.value, 2)
    cv2.line(img, pt4, pt1, cv_colors.BLUE.value, 2)

def replicate(im, labels):
    h, w = im.shape[:2]
    boxes = labels[:, 1:].astype(int)
    x1, y1, x2, y2 = boxes.T
    s = (x2 - x1 + (y2 - y1)) / 2
    for i in s.argsort()[:round(s.size * 0.5)]:
        x1b, y1b, x2b, y2b = boxes[i]
        bh, bw = (y2b - y1b, x2b - x1b)
        yc, xc = (int(random.uniform(0, h - bh)), int(random.uniform(0, w - bw)))
        x1a, y1a, x2a, y2a = [xc, yc, xc + bw, yc + bh]
        im[y1a:y2a, x1a:x2a] = im[y1b:y2b, x1b:x2b]
        labels = np.append(labels, [[labels[i, 0], x1a, y1a, x2a, y2a]], axis=0)
    return (im, labels)

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

@staticmethod
def hex2rgb(h):
    return tuple((int(h[1 + i:1 + i + 2], 16) for i in (0, 2, 4)))

def output_to_target(output):
    targets = []
    for i, o in enumerate(output):
        for *box, conf, cls in o.cpu().numpy():
            targets.append([i, cls, *list(*xyxy2xywh(np.array(box)[None])), conf])
    return np.array(targets)

def plot_images(images, targets, paths=None, fname='images.jpg', names=None, max_size=1920, max_subplots=16):
    if isinstance(images, torch.Tensor):
        images = images.cpu().float().numpy()
    if isinstance(targets, torch.Tensor):
        targets = targets.cpu().numpy()
    if np.max(images[0]) <= 1:
        images *= 255
    bs, _, h, w = images.shape
    bs = min(bs, max_subplots)
    ns = np.ceil(bs ** 0.5)
    mosaic = np.full((int(ns * h), int(ns * w), 3), 255, dtype=np.uint8)
    for i, im in enumerate(images):
        if i == max_subplots:
            break
        x, y = (int(w * (i // ns)), int(h * (i % ns)))
        im = im.transpose(1, 2, 0)
        mosaic[y:y + h, x:x + w, :] = im
    scale = max_size / ns / max(h, w)
    if scale < 1:
        h = math.ceil(scale * h)
        w = math.ceil(scale * w)
        mosaic = cv2.resize(mosaic, tuple((int(x * ns) for x in (w, h))))
    fs = int((h + w) * ns * 0.01)
    annotator = Annotator(mosaic, line_width=round(fs / 10), font_size=fs, pil=True)
    for i in range(i + 1):
        x, y = (int(w * (i // ns)), int(h * (i % ns)))
        annotator.rectangle([x, y, x + w, y + h], None, (255, 255, 255), width=2)
        if paths:
            annotator.text((x + 5, y + 5 + h), text=Path(paths[i]).name[:40], txt_color=(220, 220, 220))
        if len(targets) > 0:
            ti = targets[targets[:, 0] == i]
            boxes = xywh2xyxy(ti[:, 2:6]).T
            classes = ti[:, 1].astype('int')
            labels = ti.shape[1] == 6
            conf = None if labels else ti[:, 6]
            if boxes.shape[1]:
                if boxes.max() <= 1.01:
                    boxes[[0, 2]] *= w
                    boxes[[1, 3]] *= h
                elif scale < 1:
                    boxes *= scale
            boxes[[0, 2]] += x
            boxes[[1, 3]] += y
            for j, box in enumerate(boxes.T.tolist()):
                cls = classes[j]
                color = colors(cls)
                cls = names[cls] if names else cls
                if labels or conf[j] > 0.25:
                    label = f'{cls}' if labels else f'{cls} {conf[j]:.1f}'
                    annotator.box_label(box, label, color=color)
    annotator.im.save(fname)

def print_args(name, opt):
    LOGGER.info(colorstr(f'{name}: ') + ', '.join((f'{k}={v}' for k, v in vars(opt).items())))

def ap_per_class(tp, conf, pred_cls, target_cls, plot=False, save_dir='.', names=(), eps=1e-16):
    """ Compute the average precision, given the recall and precision curves.
    Source: https://github.com/rafaelpadilla/Object-Detection-Metrics.
    # Arguments
        tp:  True positives (nparray, nx1 or nx10).
        conf:  Objectness value from 0-1 (nparray).
        pred_cls:  Predicted object classes (nparray).
        target_cls:  True object classes (nparray).
        plot:  Plot precision-recall curve at mAP@0.5
        save_dir:  Plot save directory
    # Returns
        The average precision as computed in py-faster-rcnn.
    """
    i = np.argsort(-conf)
    tp, conf, pred_cls = (tp[i], conf[i], pred_cls[i])
    unique_classes, nt = np.unique(target_cls, return_counts=True)
    nc = unique_classes.shape[0]
    px, py = (np.linspace(0, 1, 1000), [])
    ap, p, r = (np.zeros((nc, tp.shape[1])), np.zeros((nc, 1000)), np.zeros((nc, 1000)))
    for ci, c in enumerate(unique_classes):
        i = pred_cls == c
        n_l = nt[ci]
        n_p = i.sum()
        if n_p == 0 or n_l == 0:
            continue
        else:
            fpc = (1 - tp[i]).cumsum(0)
            tpc = tp[i].cumsum(0)
            recall = tpc / (n_l + eps)
            r[ci] = np.interp(-px, -conf[i], recall[:, 0], left=0)
            precision = tpc / (tpc + fpc)
            p[ci] = np.interp(-px, -conf[i], precision[:, 0], left=1)
            for j in range(tp.shape[1]):
                ap[ci, j], mpre, mrec = compute_ap(recall[:, j], precision[:, j])
                if plot and j == 0:
                    py.append(np.interp(px, mrec, mpre))
    f1 = 2 * p * r / (p + r + eps)
    names = [v for k, v in names.items() if k in unique_classes]
    names = {i: v for i, v in enumerate(names)}
    if plot:
        plot_pr_curve(px, py, ap, Path(save_dir) / 'PR_curve.png', names)
        plot_mc_curve(px, f1, Path(save_dir) / 'F1_curve.png', names, ylabel='F1')
        plot_mc_curve(px, p, Path(save_dir) / 'P_curve.png', names, ylabel='Precision')
        plot_mc_curve(px, r, Path(save_dir) / 'R_curve.png', names, ylabel='Recall')
    i = f1.mean(0).argmax()
    p, r, f1 = (p[:, i], r[:, i], f1[:, i])
    tp = (r * nt).round()
    fp = (tp / (p + eps) - tp).round()
    return (tp, fp, p, r, f1, ap, unique_classes.astype('int32'))

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

def find_modules(model, mclass=nn.Conv2d):
    return [i for i, m in enumerate(model.module_list) if isinstance(m, mclass)]

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

class TFModel:

    def __init__(self, cfg='yolov5s.yaml', ch=3, nc=None, model=None, imgsz=(640, 640)):
        super().__init__()
        if isinstance(cfg, dict):
            self.yaml = cfg
        else:
            import yaml
            self.yaml_file = Path(cfg).name
            with open(cfg) as f:
                self.yaml = yaml.load(f, Loader=yaml.FullLoader)
        if nc and nc != self.yaml['nc']:
            LOGGER.info(f'Overriding {cfg} nc={self.yaml['nc']} with nc={nc}')
            self.yaml['nc'] = nc
        self.model, self.savelist = parse_model(deepcopy(self.yaml), ch=[ch], model=model, imgsz=imgsz)

    def predict(self, inputs, tf_nms=False, agnostic_nms=False, topk_per_class=100, topk_all=100, iou_thres=0.45, conf_thres=0.25):
        y = []
        x = inputs
        for i, m in enumerate(self.model.layers):
            if m.f != -1:
                x = y[m.f] if isinstance(m.f, int) else [x if j == -1 else y[j] for j in m.f]
            x = m(x)
            y.append(x if m.i in self.savelist else None)
        if tf_nms:
            boxes = self._xywh2xyxy(x[0][..., :4])
            probs = x[0][:, :, 4:5]
            classes = x[0][:, :, 5:]
            scores = probs * classes
            if agnostic_nms:
                nms = AgnosticNMS()((boxes, classes, scores), topk_all, iou_thres, conf_thres)
                return (nms, x[1])
            else:
                boxes = tf.expand_dims(boxes, 2)
                nms = tf.image.combined_non_max_suppression(boxes, scores, topk_per_class, topk_all, iou_thres, conf_thres, clip_boxes=False)
                return (nms, x[1])
        return x[0]

    @staticmethod
    def _xywh2xyxy(xywh):
        x, y, w, h = tf.split(xywh, num_or_size_splits=4, axis=-1)
        return tf.concat([x - w / 2, y - h / 2, x + w / 2, y + h / 2], axis=-1)

def predict(self, inputs, tf_nms=False, agnostic_nms=False, topk_per_class=100, topk_all=100, iou_thres=0.45, conf_thres=0.25):
    y = []
    x = inputs
    for i, m in enumerate(self.model.layers):
        if m.f != -1:
            x = y[m.f] if isinstance(m.f, int) else [x if j == -1 else y[j] for j in m.f]
        x = m(x)
        y.append(x if m.i in self.savelist else None)
    if tf_nms:
        boxes = self._xywh2xyxy(x[0][..., :4])
        probs = x[0][:, :, 4:5]
        classes = x[0][:, :, 5:]
        scores = probs * classes
        if agnostic_nms:
            nms = AgnosticNMS()((boxes, classes, scores), topk_all, iou_thres, conf_thres)
            return (nms, x[1])
        else:
            boxes = tf.expand_dims(boxes, 2)
            nms = tf.image.combined_non_max_suppression(boxes, scores, topk_per_class, topk_all, iou_thres, conf_thres, clip_boxes=False)
            return (nms, x[1])
    return x[0]

def representative_dataset_gen(dataset, ncalib=100):
    for n, (path, img, im0s, vid_cap, string) in enumerate(dataset):
        input = np.transpose(img, [1, 2, 0])
        input = np.expand_dims(input, axis=0).astype(np.float32)
        input /= 255
        yield [input]
        if n >= ncalib:
            break

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

