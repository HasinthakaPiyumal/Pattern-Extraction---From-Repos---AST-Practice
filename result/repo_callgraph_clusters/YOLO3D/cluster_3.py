# Cluster 3

def autobatch(model, imgsz=640, fraction=0.9, batch_size=16):
    prefix = colorstr('AutoBatch: ')
    LOGGER.info(f'{prefix}Computing optimal batch size for --imgsz {imgsz}')
    device = next(model.parameters()).device
    if device.type == 'cpu':
        LOGGER.info(f'{prefix}CUDA not detected, using default CPU batch-size {batch_size}')
        return batch_size
    d = str(device).upper()
    properties = torch.cuda.get_device_properties(device)
    t = properties.total_memory / 1024 ** 3
    r = torch.cuda.memory_reserved(device) / 1024 ** 3
    a = torch.cuda.memory_allocated(device) / 1024 ** 3
    f = t - (r + a)
    LOGGER.info(f'{prefix}{d} ({properties.name}) {t:.2f}G total, {r:.2f}G reserved, {a:.2f}G allocated, {f:.2f}G free')
    batch_sizes = [1, 2, 4, 8, 16]
    try:
        img = [torch.zeros(b, 3, imgsz, imgsz) for b in batch_sizes]
        y = profile(img, model, n=3, device=device)
    except Exception as e:
        LOGGER.warning(f'{prefix}{e}')
    y = [x[2] for x in y if x]
    batch_sizes = batch_sizes[:len(y)]
    p = np.polyfit(batch_sizes, y, deg=1)
    b = int((f * fraction - p[1]) / p[0])
    LOGGER.info(f'{prefix}Using batch-size {b} for {d} {t * fraction:.2f}G/{t:.2f}G ({fraction * 100:.0f}%)')
    return b

def check_img_size(imgsz, s=32, floor=0):
    if isinstance(imgsz, int):
        new_size = max(make_divisible(imgsz, int(s)), floor)
    else:
        new_size = [max(make_divisible(x, int(s)), floor) for x in imgsz]
    if new_size != imgsz:
        print(f'WARNING: --img-size {imgsz} must be multiple of max stride {s}, updating to {new_size}')
    return new_size

def xyxy2xywh(x):
    y = x.clone() if isinstance(x, torch.Tensor) else np.copy(x)
    y[:, 0] = (x[:, 0] + x[:, 2]) / 2
    y[:, 1] = (x[:, 1] + x[:, 3]) / 2
    y[:, 2] = x[:, 2] - x[:, 0]
    y[:, 3] = x[:, 3] - x[:, 1]
    return y

def xywh2xyxy(x):
    y = x.clone() if isinstance(x, torch.Tensor) else np.copy(x)
    y[:, 0] = x[:, 0] - x[:, 2] / 2
    y[:, 1] = x[:, 1] - x[:, 3] / 2
    y[:, 2] = x[:, 0] + x[:, 2] / 2
    y[:, 3] = x[:, 1] + x[:, 3] / 2
    return y

def xywhn2xyxy(x, w=640, h=640, padw=0, padh=0):
    y = x.clone() if isinstance(x, torch.Tensor) else np.copy(x)
    y[:, 0] = w * (x[:, 0] - x[:, 2] / 2) + padw
    y[:, 1] = h * (x[:, 1] - x[:, 3] / 2) + padh
    y[:, 2] = w * (x[:, 0] + x[:, 2] / 2) + padw
    y[:, 3] = h * (x[:, 1] + x[:, 3] / 2) + padh
    return y

def xyxy2xywhn(x, w=640, h=640, clip=False, eps=0.0):
    if clip:
        clip_coords(x, (h - eps, w - eps))
    y = x.clone() if isinstance(x, torch.Tensor) else np.copy(x)
    y[:, 0] = (x[:, 0] + x[:, 2]) / 2 / w
    y[:, 1] = (x[:, 1] + x[:, 3]) / 2 / h
    y[:, 2] = (x[:, 2] - x[:, 0]) / w
    y[:, 3] = (x[:, 3] - x[:, 1]) / h
    return y

def xyn2xy(x, w=640, h=640, padw=0, padh=0):
    y = x.clone() if isinstance(x, torch.Tensor) else np.copy(x)
    y[:, 0] = w * x[:, 0] + padw
    y[:, 1] = h * x[:, 1] + padh
    return y

def fitness(x):
    w = [0.0, 0.0, 0.1, 0.9]
    return (x[:, :4] * w).sum(1)

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

def tp_fp(self):
    tp = self.matrix.diagonal()
    fp = self.matrix.sum(1) - tp
    return (tp[:-1], fp[:-1])

def profile(input, ops, n=10, device=None):
    results = []
    device = device or select_device()
    print(f'{'Params':>12s}{'GFLOPs':>12s}{'GPU_mem (GB)':>14s}{'forward (ms)':>14s}{'backward (ms)':>14s}{'input':>24s}{'output':>24s}')
    for x in input if isinstance(input, list) else [input]:
        x = x.to(device)
        x.requires_grad = True
        for m in ops if isinstance(ops, list) else [ops]:
            m = m.to(device) if hasattr(m, 'to') else m
            m = m.half() if hasattr(m, 'half') and isinstance(x, torch.Tensor) and (x.dtype is torch.float16) else m
            tf, tb, t = (0, 0, [0, 0, 0])
            try:
                flops = thop.profile(m, inputs=(x,), verbose=False)[0] / 1000000000.0 * 2
            except:
                flops = 0
            try:
                for _ in range(n):
                    t[0] = time_sync()
                    y = m(x)
                    t[1] = time_sync()
                    try:
                        _ = (sum((yi.sum() for yi in y)) if isinstance(y, list) else y).sum().backward()
                        t[2] = time_sync()
                    except Exception as e:
                        t[2] = float('nan')
                    tf += (t[1] - t[0]) * 1000 / n
                    tb += (t[2] - t[1]) * 1000 / n
                mem = torch.cuda.memory_reserved() / 1000000000.0 if torch.cuda.is_available() else 0
                s_in = tuple(x.shape) if isinstance(x, torch.Tensor) else 'list'
                s_out = tuple(y.shape) if isinstance(y, torch.Tensor) else 'list'
                p = sum(list((x.numel() for x in m.parameters()))) if isinstance(m, nn.Module) else 0
                print(f'{p:12}{flops:12.4g}{mem:>14.3f}{tf:14.4g}{tb:14.4g}{str(s_in):>24s}{str(s_out):>24s}')
                results.append([p, flops, mem, tf, tb, s_in, s_out])
            except Exception as e:
                print(e)
                results.append(None)
            torch.cuda.empty_cache()
    return results

def sparsity(model):
    a, b = (0, 0)
    for p in model.parameters():
        a += p.numel()
        b += (p == 0).sum()
    return b / a

def prune(model, amount=0.3):
    import torch.nn.utils.prune as prune
    print('Pruning model... ', end='')
    for name, m in model.named_modules():
        if isinstance(m, nn.Conv2d):
            prune.l1_unstructured(m, name='weight', amount=amount)
            prune.remove(m, 'weight')
    print(' %.3g global sparsity' % sparsity(model))

def fuse_conv_and_bn(conv, bn):
    fusedconv = nn.Conv2d(conv.in_channels, conv.out_channels, kernel_size=conv.kernel_size, stride=conv.stride, padding=conv.padding, groups=conv.groups, bias=True).requires_grad_(False).to(conv.weight.device)
    w_conv = conv.weight.clone().view(conv.out_channels, -1)
    w_bn = torch.diag(bn.weight.div(torch.sqrt(bn.eps + bn.running_var)))
    fusedconv.weight.copy_(torch.mm(w_bn, w_conv).view(fusedconv.weight.shape))
    b_conv = torch.zeros(conv.weight.size(0), device=conv.weight.device) if conv.bias is None else conv.bias
    b_bn = bn.bias - bn.weight.mul(bn.running_mean).div(torch.sqrt(bn.running_var + bn.eps))
    fusedconv.bias.copy_(torch.mm(w_bn, b_conv.reshape(-1, 1)).reshape(-1) + b_bn)
    return fusedconv

class ModelEMA:
    """ Model Exponential Moving Average from https://github.com/rwightman/pytorch-image-models
    Keep a moving average of everything in the model state_dict (parameters and buffers).
    This is intended to allow functionality like
    https://www.tensorflow.org/api_docs/python/tf/train/ExponentialMovingAverage
    A smoothed version of the weights is necessary for some training schemes to perform well.
    This class is sensitive where it is initialized in the sequence of model init,
    GPU assignment and distributed training wrappers.
    """

    def __init__(self, model, decay=0.9999, updates=0):
        self.ema = deepcopy(model.module if is_parallel(model) else model).eval()
        self.updates = updates
        self.decay = lambda x: decay * (1 - math.exp(-x / 2000))
        for p in self.ema.parameters():
            p.requires_grad_(False)

    def update(self, model):
        with torch.no_grad():
            self.updates += 1
            d = self.decay(self.updates)
            msd = model.module.state_dict() if is_parallel(model) else model.state_dict()
            for k, v in self.ema.state_dict().items():
                if v.dtype.is_floating_point:
                    v *= d
                    v += (1 - d) * msd[k].detach()

    def update_attr(self, model, include=(), exclude=('process_group', 'reducer')):
        copy_attr(self.ema, model, include, exclude)

def __init__(self, model, decay=0.9999, updates=0):
    self.ema = deepcopy(model.module if is_parallel(model) else model).eval()
    self.updates = updates
    self.decay = lambda x: decay * (1 - math.exp(-x / 2000))
    for p in self.ema.parameters():
        p.requires_grad_(False)

class SiLU(nn.Module):

    @staticmethod
    def forward(x):
        return x * torch.sigmoid(x)

@staticmethod
def forward(x):
    return x * torch.sigmoid(x)

class Mish(nn.Module):

    @staticmethod
    def forward(x):
        return x * F.softplus(x).tanh()

@staticmethod
def forward(x):
    return x * F.softplus(x).tanh()

class F(torch.autograd.Function):

    @staticmethod
    def forward(ctx, x):
        ctx.save_for_backward(x)
        return x.mul(torch.tanh(F.softplus(x)))

    @staticmethod
    def backward(ctx, grad_output):
        x = ctx.saved_tensors[0]
        sx = torch.sigmoid(x)
        fx = F.softplus(x).tanh()
        return grad_output * (fx + x * sx * (1 - fx * fx))

@staticmethod
def forward(ctx, x):
    ctx.save_for_backward(x)
    return x.mul(torch.tanh(F.softplus(x)))

@staticmethod
def backward(ctx, grad_output):
    x = ctx.saved_tensors[0]
    sx = torch.sigmoid(x)
    fx = F.softplus(x).tanh()
    return grad_output * (fx + x * sx * (1 - fx * fx))

class AconC(nn.Module):
    """ ACON activation (activate or not).
    AconC: (p1*x-p2*x) * sigmoid(beta*(p1*x-p2*x)) + p2*x, beta is a learnable parameter
    according to "Activate or Not: Learning Customized Activation" <https://arxiv.org/pdf/2009.04759.pdf>.
    """

    def __init__(self, c1):
        super().__init__()
        self.p1 = nn.Parameter(torch.randn(1, c1, 1, 1))
        self.p2 = nn.Parameter(torch.randn(1, c1, 1, 1))
        self.beta = nn.Parameter(torch.ones(1, c1, 1, 1))

    def forward(self, x):
        dpx = (self.p1 - self.p2) * x
        return dpx * torch.sigmoid(self.beta * dpx) + self.p2 * x

def forward(self, x):
    dpx = (self.p1 - self.p2) * x
    return dpx * torch.sigmoid(self.beta * dpx) + self.p2 * x

class BCEBlurWithLogitsLoss(nn.Module):

    def __init__(self, alpha=0.05):
        super().__init__()
        self.loss_fcn = nn.BCEWithLogitsLoss(reduction='none')
        self.alpha = alpha

    def forward(self, pred, true):
        loss = self.loss_fcn(pred, true)
        pred = torch.sigmoid(pred)
        dx = pred - true
        alpha_factor = 1 - torch.exp((dx - 1) / (self.alpha + 0.0001))
        loss *= alpha_factor
        return loss.mean()

def forward(self, pred, true):
    loss = self.loss_fcn(pred, true)
    pred = torch.sigmoid(pred)
    dx = pred - true
    alpha_factor = 1 - torch.exp((dx - 1) / (self.alpha + 0.0001))
    loss *= alpha_factor
    return loss.mean()

class FocalLoss(nn.Module):

    def __init__(self, loss_fcn, gamma=1.5, alpha=0.25):
        super().__init__()
        self.loss_fcn = loss_fcn
        self.gamma = gamma
        self.alpha = alpha
        self.reduction = loss_fcn.reduction
        self.loss_fcn.reduction = 'none'

    def forward(self, pred, true):
        loss = self.loss_fcn(pred, true)
        pred_prob = torch.sigmoid(pred)
        p_t = true * pred_prob + (1 - true) * (1 - pred_prob)
        alpha_factor = true * self.alpha + (1 - true) * (1 - self.alpha)
        modulating_factor = (1.0 - p_t) ** self.gamma
        loss *= alpha_factor * modulating_factor
        if self.reduction == 'mean':
            return loss.mean()
        elif self.reduction == 'sum':
            return loss.sum()
        else:
            return loss

def forward(self, pred, true):
    loss = self.loss_fcn(pred, true)
    pred_prob = torch.sigmoid(pred)
    p_t = true * pred_prob + (1 - true) * (1 - pred_prob)
    alpha_factor = true * self.alpha + (1 - true) * (1 - self.alpha)
    modulating_factor = (1.0 - p_t) ** self.gamma
    loss *= alpha_factor * modulating_factor
    if self.reduction == 'mean':
        return loss.mean()
    elif self.reduction == 'sum':
        return loss.sum()
    else:
        return loss

class QFocalLoss(nn.Module):

    def __init__(self, loss_fcn, gamma=1.5, alpha=0.25):
        super().__init__()
        self.loss_fcn = loss_fcn
        self.gamma = gamma
        self.alpha = alpha
        self.reduction = loss_fcn.reduction
        self.loss_fcn.reduction = 'none'

    def forward(self, pred, true):
        loss = self.loss_fcn(pred, true)
        pred_prob = torch.sigmoid(pred)
        alpha_factor = true * self.alpha + (1 - true) * (1 - self.alpha)
        modulating_factor = torch.abs(true - pred_prob) ** self.gamma
        loss *= alpha_factor * modulating_factor
        if self.reduction == 'mean':
            return loss.mean()
        elif self.reduction == 'sum':
            return loss.sum()
        else:
            return loss

def forward(self, pred, true):
    loss = self.loss_fcn(pred, true)
    pred_prob = torch.sigmoid(pred)
    alpha_factor = true * self.alpha + (1 - true) * (1 - self.alpha)
    modulating_factor = torch.abs(true - pred_prob) ** self.gamma
    loss *= alpha_factor * modulating_factor
    if self.reduction == 'mean':
        return loss.mean()
    elif self.reduction == 'sum':
        return loss.sum()
    else:
        return loss

class DetectedObject:
    """
    Processing image for NN input
    """

    def __init__(self, img, detection_class, box_2d, proj_matrix, label=None):
        if isinstance(proj_matrix, str):
            proj_matrix = get_P(proj_matrix)
        self.proj_matrix = proj_matrix
        self.theta_ray = self.calc_theta_ray(img, box_2d, proj_matrix)
        self.img = self.format_img(img, box_2d)
        self.label = label
        self.detection_class = detection_class

    def calc_theta_ray(self, img, box_2d, proj_matrix):
        """
        Calculate global angle of object, see paper
        """
        width = img.shape[1]
        fovx = 2 * np.arctan(width / (2 * proj_matrix[0][0]))
        center = (box_2d[1][0] + box_2d[0][0]) / 2
        dx = center - width / 2
        mult = 1
        if dx < 0:
            mult = -1
        dx = abs(dx)
        angle = np.arctan(2 * dx * np.tan(fovx / 2) / width)
        angle = angle * mult
        return angle

    def format_img(self, img, box_2d):
        normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        process = transforms.Compose([transforms.ToTensor(), normalize])
        pt1, pt2 = (box_2d[0], box_2d[1])
        crop = img[pt1[1]:pt2[1] + 1, pt1[0]:pt2[0] + 1]
        crop = cv2.resize(crop, (224, 224), interpolation=cv2.INTER_CUBIC)
        batch = process(crop)
        return batch

def __init__(self, img, detection_class, box_2d, proj_matrix, label=None):
    if isinstance(proj_matrix, str):
        proj_matrix = get_P(proj_matrix)
    self.proj_matrix = proj_matrix
    self.theta_ray = self.calc_theta_ray(img, box_2d, proj_matrix)
    self.img = self.format_img(img, box_2d)
    self.label = label
    self.detection_class = detection_class

def calc_theta_ray(self, img, box_2d, proj_matrix):
    """
        Calculate global angle of object, see paper
        """
    width = img.shape[1]
    fovx = 2 * np.arctan(width / (2 * proj_matrix[0][0]))
    center = (box_2d[1][0] + box_2d[0][0]) / 2
    dx = center - width / 2
    mult = 1
    if dx < 0:
        mult = -1
    dx = abs(dx)
    angle = np.arctan(2 * dx * np.tan(fovx / 2) / width)
    angle = angle * mult
    return angle

class NumpyEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

def default(self, obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return json.JSONEncoder.default(self, obj)

class DetectedObject:
    """
    Processing image for NN input
    """

    def __init__(self, img, detection_class, box_2d, proj_matrix, label=None):
        if isinstance(proj_matrix, str):
            proj_matrix = get_P(proj_matrix)
        self.proj_matrix = proj_matrix
        self.theta_ray = self.calc_theta_ray(img, box_2d, proj_matrix)
        self.img = self.format_img(img, box_2d)
        self.label = label
        self.detection_class = detection_class

    def calc_theta_ray(self, img, box_2d, proj_matrix):
        """
        Calculate global angle of object, see paper
        """
        width = img.shape[1]
        fovx = 2 * np.arctan(width / (2 * proj_matrix[0][0]))
        center = (box_2d[1][0] + box_2d[0][0]) / 2
        dx = center - width / 2
        mult = 1
        if dx < 0:
            mult = -1
        dx = abs(dx)
        angle = np.arctan(2 * dx * np.tan(fovx / 2) / width)
        angle = angle * mult
        return angle

    def format_img(self, img, box_2d):
        normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        process = transforms.Compose([transforms.ToTensor(), normalize])
        pt1, pt2 = (box_2d[0], box_2d[1])
        crop = img[pt1[1]:pt2[1] + 1, pt1[0]:pt2[0] + 1]
        crop = cv2.resize(crop, (224, 224), interpolation=cv2.INTER_CUBIC)
        batch = process(crop)
        return batch

def __init__(self, img, detection_class, box_2d, proj_matrix, label=None):
    if isinstance(proj_matrix, str):
        proj_matrix = get_P(proj_matrix)
    self.proj_matrix = proj_matrix
    self.theta_ray = self.calc_theta_ray(img, box_2d, proj_matrix)
    self.img = self.format_img(img, box_2d)
    self.label = label
    self.detection_class = detection_class

def calc_theta_ray(self, img, box_2d, proj_matrix):
    """
        Calculate global angle of object, see paper
        """
    width = img.shape[1]
    fovx = 2 * np.arctan(width / (2 * proj_matrix[0][0]))
    center = (box_2d[1][0] + box_2d[0][0]) / 2
    dx = center - width / 2
    mult = 1
    if dx < 0:
        mult = -1
    dx = abs(dx)
    angle = np.arctan(2 * dx * np.tan(fovx / 2) / width)
    angle = angle * mult
    return angle

class Model(pl.LightningModule):

    def __init__(self, model_select='resnet18', bins=2, w=0.4, lr=0.0001, alpha=0.6):
        super(Model, self).__init__()
        self.save_hyperparameters()
        self.bins = bins
        self.w = w
        self.learning_rate = lr
        self.alpha = alpha
        self.conf_loss_func = nn.CrossEntropyLoss()
        self.dim_loss_func = nn.MSELoss()
        self.orient_loss_func = OrientationLoss
        self.model = model_factory(model_select)[0]
        self.in_features = model_factory(model_select)[1]
        self.orientation = nn.Sequential(nn.Linear(self.in_features, 256), nn.ReLU(True), nn.Dropout(), nn.Linear(256, 256), nn.ReLU(True), nn.Dropout(), nn.Linear(256, bins * 2))
        self.confidence = nn.Sequential(nn.Linear(self.in_features, 256), nn.ReLU(True), nn.Dropout(), nn.Linear(256, 256), nn.ReLU(True), nn.Dropout(), nn.Linear(256, bins))
        self.dimension = nn.Sequential(nn.Linear(self.in_features, 512), nn.ReLU(True), nn.Dropout(), nn.Linear(512, 512), nn.ReLU(True), nn.Dropout(), nn.Linear(512, 3))

    def forward(self, x):
        x = self.model(x)
        x = x.view(-1, self.in_features)
        orientation = self.orientation(x)
        orientation = orientation.view(-1, self.bins, 2)
        orientation = F.normalize(orientation, dim=2)
        confidence = self.confidence(x)
        dimension = self.dimension(x)
        return (orientation, confidence, dimension)

    def training_step(self, batch, batch_idx):
        x, labels = batch
        x = x.float()
        truth_orient = labels['Orientation'].float()
        truth_conf = labels['Confidence'].float()
        truth_dim = labels['Dimensions'].float()
        [orient, conf, dim] = self(x)
        orient_loss = self.orient_loss_func(orient, truth_orient, truth_conf)
        dim_loss = self.dim_loss_func(dim, truth_dim)
        truth_conf = torch.max(truth_conf, dim=1)[1]
        conf_loss = self.conf_loss_func(conf, truth_conf)
        loss_theta = conf_loss + self.w * orient_loss
        loss = self.alpha * dim_loss + loss_theta
        self.log('train_loss', loss)
        return {'loss': loss}

    def validation_step(self, batch, batch_idx):
        """
        In validation_step we use batch and batch_idx from validation data
        """
        results = self.training_step(batch, batch_idx)
        return results

    def validation_epoch_end(self, val_step_outputs):
        avg_val_loss = torch.tensor([x['loss'] for x in val_step_outputs]).mean()
        self.log('val_loss', avg_val_loss)
        return {'val_loss': avg_val_loss}

    def configure_optimizers(self):
        optimizer = torch.optim.SGD(self.parameters(), lr=self.learning_rate, momentum=0.9)
        return optimizer

def configure_optimizers(self):
    optimizer = torch.optim.SGD(self.parameters(), lr=self.learning_rate, momentum=0.9)
    return optimizer

class Model(nn.Module):

    def __init__(self, cfg='yolov5s.yaml', ch=3, nc=None, anchors=None):
        super().__init__()
        if isinstance(cfg, dict):
            self.yaml = cfg
        else:
            import yaml
            self.yaml_file = Path(cfg).name
            with open(cfg, encoding='ascii', errors='ignore') as f:
                self.yaml = yaml.safe_load(f)
        ch = self.yaml['ch'] = self.yaml.get('ch', ch)
        if nc and nc != self.yaml['nc']:
            LOGGER.info(f'Overriding model.yaml nc={self.yaml['nc']} with nc={nc}')
            self.yaml['nc'] = nc
        if anchors:
            LOGGER.info(f'Overriding model.yaml anchors with anchors={anchors}')
            self.yaml['anchors'] = round(anchors)
        self.model, self.save = parse_model(deepcopy(self.yaml), ch=[ch])
        self.names = [str(i) for i in range(self.yaml['nc'])]
        self.inplace = self.yaml.get('inplace', True)
        m = self.model[-1]
        if isinstance(m, Detect):
            s = 256
            m.inplace = self.inplace
            m.stride = torch.tensor([s / x.shape[-2] for x in self.forward(torch.zeros(1, ch, s, s))])
            m.anchors /= m.stride.view(-1, 1, 1)
            check_anchor_order(m)
            self.stride = m.stride
            self._initialize_biases()
        initialize_weights(self)
        self.info()
        LOGGER.info('')

    def forward(self, x, augment=False, profile=False, visualize=False):
        if augment:
            return self._forward_augment(x)
        return self._forward_once(x, profile, visualize)

    def _forward_augment(self, x):
        img_size = x.shape[-2:]
        s = [1, 0.83, 0.67]
        f = [None, 3, None]
        y = []
        for si, fi in zip(s, f):
            xi = scale_img(x.flip(fi) if fi else x, si, gs=int(self.stride.max()))
            yi = self._forward_once(xi)[0]
            yi = self._descale_pred(yi, fi, si, img_size)
            y.append(yi)
        y = self._clip_augmented(y)
        return (torch.cat(y, 1), None)

    def _forward_once(self, x, profile=False, visualize=False):
        y, dt = ([], [])
        for m in self.model:
            if m.f != -1:
                x = y[m.f] if isinstance(m.f, int) else [x if j == -1 else y[j] for j in m.f]
            if profile:
                self._profile_one_layer(m, x, dt)
            x = m(x)
            y.append(x if m.i in self.save else None)
            if visualize:
                feature_visualization(x, m.type, m.i, save_dir=visualize)
        return x

    def _descale_pred(self, p, flips, scale, img_size):
        if self.inplace:
            p[..., :4] /= scale
            if flips == 2:
                p[..., 1] = img_size[0] - p[..., 1]
            elif flips == 3:
                p[..., 0] = img_size[1] - p[..., 0]
        else:
            x, y, wh = (p[..., 0:1] / scale, p[..., 1:2] / scale, p[..., 2:4] / scale)
            if flips == 2:
                y = img_size[0] - y
            elif flips == 3:
                x = img_size[1] - x
            p = torch.cat((x, y, wh, p[..., 4:]), -1)
        return p

    def _clip_augmented(self, y):
        nl = self.model[-1].nl
        g = sum((4 ** x for x in range(nl)))
        e = 1
        i = y[0].shape[1] // g * sum((4 ** x for x in range(e)))
        y[0] = y[0][:, :-i]
        i = y[-1].shape[1] // g * sum((4 ** (nl - 1 - x) for x in range(e)))
        y[-1] = y[-1][:, i:]
        return y

    def _profile_one_layer(self, m, x, dt):
        c = isinstance(m, Detect)
        o = thop.profile(m, inputs=(x.copy() if c else x,), verbose=False)[0] / 1000000000.0 * 2 if thop else 0
        t = time_sync()
        for _ in range(10):
            m(x.copy() if c else x)
        dt.append((time_sync() - t) * 100)
        if m == self.model[0]:
            LOGGER.info(f'{'time (ms)':>10s} {'GFLOPs':>10s} {'params':>10s}  {'module'}')
        LOGGER.info(f'{dt[-1]:10.2f} {o:10.2f} {m.np:10.0f}  {m.type}')
        if c:
            LOGGER.info(f'{sum(dt):10.2f} {'-':>10s} {'-':>10s}  Total')

    def _initialize_biases(self, cf=None):
        m = self.model[-1]
        for mi, s in zip(m.m, m.stride):
            b = mi.bias.view(m.na, -1)
            b.data[:, 4] += math.log(8 / (640 / s) ** 2)
            b.data[:, 5:] += math.log(0.6 / (m.nc - 0.999999)) if cf is None else torch.log(cf / cf.sum())
            mi.bias = torch.nn.Parameter(b.view(-1), requires_grad=True)

    def _print_biases(self):
        m = self.model[-1]
        for mi in m.m:
            b = mi.bias.detach().view(m.na, -1).T
            LOGGER.info(('%6g Conv2d.bias:' + '%10.3g' * 6) % (mi.weight.shape[1], *b[:5].mean(1).tolist(), b[5:].mean()))

    def fuse(self):
        LOGGER.info('Fusing layers... ')
        for m in self.model.modules():
            if isinstance(m, (Conv, DWConv)) and hasattr(m, 'bn'):
                m.conv = fuse_conv_and_bn(m.conv, m.bn)
                delattr(m, 'bn')
                m.forward = m.forward_fuse
        self.info()
        return self

    def info(self, verbose=False, img_size=640):
        model_info(self, verbose, img_size)

    def _apply(self, fn):
        self = super()._apply(fn)
        m = self.model[-1]
        if isinstance(m, Detect):
            m.stride = fn(m.stride)
            m.grid = list(map(fn, m.grid))
            if isinstance(m.anchor_grid, list):
                m.anchor_grid = list(map(fn, m.anchor_grid))
        return self

def _forward_once(self, x, profile=False, visualize=False):
    y, dt = ([], [])
    for m in self.model:
        if m.f != -1:
            x = y[m.f] if isinstance(m.f, int) else [x if j == -1 else y[j] for j in m.f]
        if profile:
            self._profile_one_layer(m, x, dt)
        x = m(x)
        y.append(x if m.i in self.save else None)
        if visualize:
            feature_visualization(x, m.type, m.i, save_dir=visualize)
    return x

def _clip_augmented(self, y):
    nl = self.model[-1].nl
    g = sum((4 ** x for x in range(nl)))
    e = 1
    i = y[0].shape[1] // g * sum((4 ** x for x in range(e)))
    y[0] = y[0][:, :-i]
    i = y[-1].shape[1] // g * sum((4 ** (nl - 1 - x) for x in range(e)))
    y[-1] = y[-1][:, i:]
    return y

def _profile_one_layer(self, m, x, dt):
    c = isinstance(m, Detect)
    o = thop.profile(m, inputs=(x.copy() if c else x,), verbose=False)[0] / 1000000000.0 * 2 if thop else 0
    t = time_sync()
    for _ in range(10):
        m(x.copy() if c else x)
    dt.append((time_sync() - t) * 100)
    if m == self.model[0]:
        LOGGER.info(f'{'time (ms)':>10s} {'GFLOPs':>10s} {'params':>10s}  {'module'}')
    LOGGER.info(f'{dt[-1]:10.2f} {o:10.2f} {m.np:10.0f}  {m.type}')
    if c:
        LOGGER.info(f'{sum(dt):10.2f} {'-':>10s} {'-':>10s}  Total')

def _apply(self, fn):
    self = super()._apply(fn)
    m = self.model[-1]
    if isinstance(m, Detect):
        m.stride = fn(m.stride)
        m.grid = list(map(fn, m.grid))
        if isinstance(m.anchor_grid, list):
            m.anchor_grid = list(map(fn, m.anchor_grid))
    return self

def parse_model(d, ch):
    LOGGER.info(f'\n{'':>3}{'from':>18}{'n':>3}{'params':>10}  {'module':<40}{'arguments':<30}')
    anchors, nc, gd, gw = (d['anchors'], d['nc'], d['depth_multiple'], d['width_multiple'])
    na = len(anchors[0]) // 2 if isinstance(anchors, list) else anchors
    no = na * (nc + 5)
    layers, save, c2 = ([], [], ch[-1])
    for i, (f, n, m, args) in enumerate(d['backbone'] + d['head']):
        m = eval(m) if isinstance(m, str) else m
        for j, a in enumerate(args):
            try:
                args[j] = eval(a) if isinstance(a, str) else a
            except NameError:
                pass
        n = n_ = max(round(n * gd), 1) if n > 1 else n
        if m in [Conv, GhostConv, Bottleneck, GhostBottleneck, SPP, SPPF, DWConv, MixConv2d, Focus, CrossConv, BottleneckCSP, C3, C3TR, C3SPP, C3Ghost]:
            c1, c2 = (ch[f], args[0])
            if c2 != no:
                c2 = make_divisible(c2 * gw, 8)
            args = [c1, c2, *args[1:]]
            if m in [BottleneckCSP, C3, C3TR, C3Ghost]:
                args.insert(2, n)
                n = 1
        elif m is nn.BatchNorm2d:
            args = [ch[f]]
        elif m is Concat:
            c2 = sum((ch[x] for x in f))
        elif m is Detect:
            args.append([ch[x] for x in f])
            if isinstance(args[1], int):
                args[1] = [list(range(args[1] * 2))] * len(f)
        elif m is Contract:
            c2 = ch[f] * args[0] ** 2
        elif m is Expand:
            c2 = ch[f] // args[0] ** 2
        else:
            c2 = ch[f]
        m_ = nn.Sequential(*(m(*args) for _ in range(n))) if n > 1 else m(*args)
        t = str(m)[8:-2].replace('__main__.', '')
        np = sum((x.numel() for x in m_.parameters()))
        m_.i, m_.f, m_.type, m_.np = (i, f, t, np)
        LOGGER.info(f'{i:>3}{str(f):>18}{n_:>3}{np:10.0f}  {t:<40}{str(args):<30}')
        save.extend((x % i for x in ([f] if isinstance(f, int) else f) if x != -1))
        layers.append(m_)
        if i == 0:
            ch = []
        ch.append(c2)
    return (nn.Sequential(*layers), sorted(save))

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

def parse_model(d, ch, model, imgsz):
    LOGGER.info(f'\n{'':>3}{'from':>18}{'n':>3}{'params':>10}  {'module':<40}{'arguments':<30}')
    anchors, nc, gd, gw = (d['anchors'], d['nc'], d['depth_multiple'], d['width_multiple'])
    na = len(anchors[0]) // 2 if isinstance(anchors, list) else anchors
    no = na * (nc + 5)
    layers, save, c2 = ([], [], ch[-1])
    for i, (f, n, m, args) in enumerate(d['backbone'] + d['head']):
        m_str = m
        m = eval(m) if isinstance(m, str) else m
        for j, a in enumerate(args):
            try:
                args[j] = eval(a) if isinstance(a, str) else a
            except NameError:
                pass
        n = max(round(n * gd), 1) if n > 1 else n
        if m in [nn.Conv2d, Conv, Bottleneck, SPP, SPPF, DWConv, MixConv2d, Focus, CrossConv, BottleneckCSP, C3]:
            c1, c2 = (ch[f], args[0])
            c2 = make_divisible(c2 * gw, 8) if c2 != no else c2
            args = [c1, c2, *args[1:]]
            if m in [BottleneckCSP, C3]:
                args.insert(2, n)
                n = 1
        elif m is nn.BatchNorm2d:
            args = [ch[f]]
        elif m is Concat:
            c2 = sum((ch[-1 if x == -1 else x + 1] for x in f))
        elif m is Detect:
            args.append([ch[x + 1] for x in f])
            if isinstance(args[1], int):
                args[1] = [list(range(args[1] * 2))] * len(f)
            args.append(imgsz)
        else:
            c2 = ch[f]
        tf_m = eval('TF' + m_str.replace('nn.', ''))
        m_ = keras.Sequential([tf_m(*args, w=model.model[i][j]) for j in range(n)]) if n > 1 else tf_m(*args, w=model.model[i])
        torch_m_ = nn.Sequential(*(m(*args) for _ in range(n))) if n > 1 else m(*args)
        t = str(m)[8:-2].replace('__main__.', '')
        np = sum((x.numel() for x in torch_m_.parameters()))
        m_.i, m_.f, m_.type, m_.np = (i, f, t, np)
        LOGGER.info(f'{i:>3}{str(f):>18}{str(n):>3}{np:>10}  {t:<40}{str(args):<30}')
        save.extend((x % i for x in ([f] if isinstance(f, int) else f) if x != -1))
        layers.append(m_)
        ch.append(c2)
    return (keras.Sequential(layers), sorted(save))

class Sum(nn.Module):

    def __init__(self, n, weight=False):
        super().__init__()
        self.weight = weight
        self.iter = range(n - 1)
        if weight:
            self.w = nn.Parameter(-torch.arange(1.0, n) / 2, requires_grad=True)

    def forward(self, x):
        y = x[0]
        if self.weight:
            w = torch.sigmoid(self.w) * 2
            for i in self.iter:
                y = y + x[i + 1] * w[i]
        else:
            for i in self.iter:
                y = y + x[i + 1]
        return y

def forward(self, x):
    y = x[0]
    if self.weight:
        w = torch.sigmoid(self.w) * 2
        for i in self.iter:
            y = y + x[i + 1] * w[i]
    else:
        for i in self.iter:
            y = y + x[i + 1]
    return y

def autopad(k, p=None):
    if p is None:
        p = k // 2 if isinstance(k, int) else [x // 2 for x in k]
    return p

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

def _apply(self, fn):
    self = super()._apply(fn)
    if self.pt:
        m = self.model.model.model[-1] if self.dmb else self.model.model[-1]
        m.stride = fn(m.stride)
        m.grid = list(map(fn, m.grid))
        if isinstance(m.anchor_grid, list):
            m.anchor_grid = list(map(fn, m.anchor_grid))
    return self

