# Cluster 4

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

def __call__(self, i, bgr=False):
    c = self.palette[int(i) % self.n]
    return (c[2], c[1], c[0]) if bgr else c

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

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    object.__setattr__(self, 'batch_sampler', _RepeatSampler(self.batch_sampler))
    self.iterator = super().__iter__()

class Timeout(contextlib.ContextDecorator):

    def __init__(self, seconds, *, timeout_msg='', suppress_timeout_errors=True):
        self.seconds = int(seconds)
        self.timeout_message = timeout_msg
        self.suppress = bool(suppress_timeout_errors)

    def _timeout_handler(self, signum, frame):
        raise TimeoutError(self.timeout_message)

    def __enter__(self):
        signal.signal(signal.SIGALRM, self._timeout_handler)
        signal.alarm(self.seconds)

    def __exit__(self, exc_type, exc_val, exc_tb):
        signal.alarm(0)
        if self.suppress and exc_type is TimeoutError:
            return True

def __init__(self, seconds, *, timeout_msg='', suppress_timeout_errors=True):
    self.seconds = int(seconds)
    self.timeout_message = timeout_msg
    self.suppress = bool(suppress_timeout_errors)

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

def update_attr(self, model, include=(), exclude=('process_group', 'reducer')):
    copy_attr(self.ema, model, include, exclude)

class FReLU(nn.Module):

    def __init__(self, c1, k=3):
        super().__init__()
        self.conv = nn.Conv2d(c1, c1, k, 1, 1, groups=c1, bias=False)
        self.bn = nn.BatchNorm2d(c1)

    def forward(self, x):
        return torch.max(x, self.bn(self.conv(x)))

def __init__(self, c1, k=3):
    super().__init__()
    self.conv = nn.Conv2d(c1, c1, k, 1, 1, groups=c1, bias=False)
    self.bn = nn.BatchNorm2d(c1)

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

def __init__(self, c1):
    super().__init__()
    self.p1 = nn.Parameter(torch.randn(1, c1, 1, 1))
    self.p2 = nn.Parameter(torch.randn(1, c1, 1, 1))
    self.beta = nn.Parameter(torch.ones(1, c1, 1, 1))

class MetaAconC(nn.Module):
    """ ACON activation (activate or not).
    MetaAconC: (p1*x-p2*x) * sigmoid(beta*(p1*x-p2*x)) + p2*x, beta is generated by a small network
    according to "Activate or Not: Learning Customized Activation" <https://arxiv.org/pdf/2009.04759.pdf>.
    """

    def __init__(self, c1, k=1, s=1, r=16):
        super().__init__()
        c2 = max(r, c1 // r)
        self.p1 = nn.Parameter(torch.randn(1, c1, 1, 1))
        self.p2 = nn.Parameter(torch.randn(1, c1, 1, 1))
        self.fc1 = nn.Conv2d(c1, c2, k, s, bias=True)
        self.fc2 = nn.Conv2d(c2, c1, k, s, bias=True)

    def forward(self, x):
        y = x.mean(dim=2, keepdims=True).mean(dim=3, keepdims=True)
        beta = torch.sigmoid(self.fc2(self.fc1(y)))
        dpx = (self.p1 - self.p2) * x
        return dpx * torch.sigmoid(beta * dpx) + self.p2 * x

def __init__(self, c1, k=1, s=1, r=16):
    super().__init__()
    c2 = max(r, c1 // r)
    self.p1 = nn.Parameter(torch.randn(1, c1, 1, 1))
    self.p2 = nn.Parameter(torch.randn(1, c1, 1, 1))
    self.fc1 = nn.Conv2d(c1, c2, k, s, bias=True)
    self.fc2 = nn.Conv2d(c2, c1, k, s, bias=True)

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

def __init__(self, alpha=0.05):
    super().__init__()
    self.loss_fcn = nn.BCEWithLogitsLoss(reduction='none')
    self.alpha = alpha

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

def __init__(self, loss_fcn, gamma=1.5, alpha=0.25):
    super().__init__()
    self.loss_fcn = loss_fcn
    self.gamma = gamma
    self.alpha = alpha
    self.reduction = loss_fcn.reduction
    self.loss_fcn.reduction = 'none'

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

def __init__(self, loss_fcn, gamma=1.5, alpha=0.25):
    super().__init__()
    self.loss_fcn = loss_fcn
    self.gamma = gamma
    self.alpha = alpha
    self.reduction = loss_fcn.reduction
    self.loss_fcn.reduction = 'none'

class ResNet(nn.Module):

    def __init__(self, model=None, bins=2, w=0.4):
        super(ResNet, self).__init__()
        self.bins = bins
        self.w = w
        model.fc = nn.Linear(512, 512)
        self.model = model
        self.orientation = nn.Sequential(nn.Linear(512, 256), nn.ReLU(True), nn.Dropout(), nn.Linear(256, 256), nn.ReLU(True), nn.Dropout(), nn.Linear(256, bins * 2))
        self.confidence = nn.Sequential(nn.Linear(512, 256), nn.ReLU(True), nn.Dropout(), nn.Linear(256, 256), nn.ReLU(True), nn.Dropout(), nn.Linear(256, bins))
        self.dimension = nn.Sequential(nn.Linear(512, 256), nn.ReLU(True), nn.Dropout(), nn.Linear(256, 256), nn.ReLU(True), nn.Dropout(), nn.Linear(256, 3))

    def forward(self, x):
        x = self.model(x)
        x = x.view(-1, 512)
        orientation = self.orientation(x)
        orientation = orientation.view(-1, self.bins, 2)
        orientation = F.normalize(orientation, dim=2)
        confidence = self.confidence(x)
        dimension = self.dimension(x)
        return (orientation, confidence, dimension)

def __init__(self, model=None, bins=2, w=0.4):
    super(ResNet, self).__init__()
    self.bins = bins
    self.w = w
    model.fc = nn.Linear(512, 512)
    self.model = model
    self.orientation = nn.Sequential(nn.Linear(512, 256), nn.ReLU(True), nn.Dropout(), nn.Linear(256, 256), nn.ReLU(True), nn.Dropout(), nn.Linear(256, bins * 2))
    self.confidence = nn.Sequential(nn.Linear(512, 256), nn.ReLU(True), nn.Dropout(), nn.Linear(256, 256), nn.ReLU(True), nn.Dropout(), nn.Linear(256, bins))
    self.dimension = nn.Sequential(nn.Linear(512, 256), nn.ReLU(True), nn.Dropout(), nn.Linear(256, 256), nn.ReLU(True), nn.Dropout(), nn.Linear(256, 3))

class ResNet18(nn.Module):

    def __init__(self, model=None, bins=2, w=0.4):
        super(ResNet18, self).__init__()
        self.bins = bins
        self.w = w
        self.model = nn.Sequential(*list(model.children())[:-2])
        self.orientation = nn.Sequential(nn.Linear(512 * 7 * 7, 256), nn.ReLU(True), nn.Dropout(), nn.Linear(256, 256), nn.ReLU(True), nn.Dropout(), nn.Linear(256, bins * 2))
        self.confidence = nn.Sequential(nn.Linear(512 * 7 * 7, 256), nn.ReLU(True), nn.Dropout(), nn.Linear(256, bins))
        self.dimension = nn.Sequential(nn.Linear(512 * 7 * 7, 512), nn.ReLU(True), nn.Dropout(), nn.Linear(512, 512), nn.ReLU(True), nn.Dropout(), nn.Linear(512, 3))

    def forward(self, x):
        x = self.model(x)
        x = x.view(-1, 512 * 7 * 7)
        orientation = self.orientation(x)
        orientation = orientation.view(-1, self.bins, 2)
        orientation = F.normalize(orientation, dim=2)
        confidence = self.confidence(x)
        dimension = self.dimension(x)
        return (orientation, confidence, dimension)

def __init__(self, model=None, bins=2, w=0.4):
    super(ResNet18, self).__init__()
    self.bins = bins
    self.w = w
    self.model = nn.Sequential(*list(model.children())[:-2])
    self.orientation = nn.Sequential(nn.Linear(512 * 7 * 7, 256), nn.ReLU(True), nn.Dropout(), nn.Linear(256, 256), nn.ReLU(True), nn.Dropout(), nn.Linear(256, bins * 2))
    self.confidence = nn.Sequential(nn.Linear(512 * 7 * 7, 256), nn.ReLU(True), nn.Dropout(), nn.Linear(256, bins))
    self.dimension = nn.Sequential(nn.Linear(512 * 7 * 7, 512), nn.ReLU(True), nn.Dropout(), nn.Linear(512, 512), nn.ReLU(True), nn.Dropout(), nn.Linear(512, 3))

class VGG11(nn.Module):

    def __init__(self, model=None, bins=2, w=0.4):
        super(VGG11, self).__init__()
        self.bins = bins
        self.w = w
        self.model = model.features
        self.orientation = nn.Sequential(nn.Linear(512 * 7 * 7, 256), nn.ReLU(True), nn.Dropout(), nn.Linear(256, 256), nn.ReLU(True), nn.Dropout(), nn.Linear(256, bins * 2))
        self.confidence = nn.Sequential(nn.Linear(512 * 7 * 7, 256), nn.ReLU(True), nn.Dropout(), nn.Linear(256, 256), nn.ReLU(True), nn.Dropout(), nn.Linear(256, bins))
        self.dimension = nn.Sequential(nn.Linear(512 * 7 * 7, 256), nn.ReLU(True), nn.Dropout(), nn.Linear(256, 256), nn.ReLU(True), nn.Dropout(), nn.Linear(256, 3))

    def forward(self, x):
        x = self.model(x)
        x = x.view(-1, 512 * 7 * 7)
        orientation = self.orientation(x)
        orientation = orientation.view(-1, self.bins, 2)
        orientation = F.normalize(orientation, dim=2)
        confidence = self.confidence(x)
        dimension = self.dimension(x)
        return (orientation, confidence, dimension)

def __init__(self, model=None, bins=2, w=0.4):
    super(VGG11, self).__init__()
    self.bins = bins
    self.w = w
    self.model = model.features
    self.orientation = nn.Sequential(nn.Linear(512 * 7 * 7, 256), nn.ReLU(True), nn.Dropout(), nn.Linear(256, 256), nn.ReLU(True), nn.Dropout(), nn.Linear(256, bins * 2))
    self.confidence = nn.Sequential(nn.Linear(512 * 7 * 7, 256), nn.ReLU(True), nn.Dropout(), nn.Linear(256, 256), nn.ReLU(True), nn.Dropout(), nn.Linear(256, bins))
    self.dimension = nn.Sequential(nn.Linear(512 * 7 * 7, 256), nn.ReLU(True), nn.Dropout(), nn.Linear(256, 256), nn.ReLU(True), nn.Dropout(), nn.Linear(256, 3))

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

def __init__(self, dataset_path='/dataset/KITTI/training', batch_size=32, num_workers=2, val_split=0.1):
    super(KITTIDataModule, self).__init__()
    self.dataset_path = dataset_path
    self.val_split = val_split
    self.train_split = 1.0 - self.val_split
    self.params = {'batch_size': batch_size, 'shuffle': True, 'num_workers': num_workers}

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

def model_factory(model_select):
    resnet = models.resnet18(pretrained=True)
    resnet.fc = nn.Linear(512, 512)
    resnet18 = models.resnet18(pretrained=True)
    resnet18 = nn.Sequential(*list(resnet18.children())[:-2])
    vgg11 = models.vgg11(pretrained=True)
    vgg11 = vgg11.features
    model = {'resnet': [resnet, 512], 'resnet18': [resnet18, 512 * 7 * 7], 'vgg11': [vgg11, 512 * 7 * 7]}
    return model[model_select]

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

class TFBN(keras.layers.Layer):

    def __init__(self, w=None):
        super().__init__()
        self.bn = keras.layers.BatchNormalization(beta_initializer=keras.initializers.Constant(w.bias.numpy()), gamma_initializer=keras.initializers.Constant(w.weight.numpy()), moving_mean_initializer=keras.initializers.Constant(w.running_mean.numpy()), moving_variance_initializer=keras.initializers.Constant(w.running_var.numpy()), epsilon=w.eps)

    def call(self, inputs):
        return self.bn(inputs)

def __init__(self, w=None):
    super().__init__()
    self.bn = keras.layers.BatchNormalization(beta_initializer=keras.initializers.Constant(w.bias.numpy()), gamma_initializer=keras.initializers.Constant(w.weight.numpy()), moving_mean_initializer=keras.initializers.Constant(w.running_mean.numpy()), moving_variance_initializer=keras.initializers.Constant(w.running_var.numpy()), epsilon=w.eps)

class TFPad(keras.layers.Layer):

    def __init__(self, pad):
        super().__init__()
        self.pad = tf.constant([[0, 0], [pad, pad], [pad, pad], [0, 0]])

    def call(self, inputs):
        return tf.pad(inputs, self.pad, mode='constant', constant_values=0)

def __init__(self, pad):
    super().__init__()
    self.pad = tf.constant([[0, 0], [pad, pad], [pad, pad], [0, 0]])

class TFConv(keras.layers.Layer):

    def __init__(self, c1, c2, k=1, s=1, p=None, g=1, act=True, w=None):
        super().__init__()
        assert g == 1, "TF v2.2 Conv2D does not support 'groups' argument"
        assert isinstance(k, int), 'Convolution with multiple kernels are not allowed.'
        conv = keras.layers.Conv2D(c2, k, s, 'SAME' if s == 1 else 'VALID', use_bias=False if hasattr(w, 'bn') else True, kernel_initializer=keras.initializers.Constant(w.conv.weight.permute(2, 3, 1, 0).numpy()), bias_initializer='zeros' if hasattr(w, 'bn') else keras.initializers.Constant(w.conv.bias.numpy()))
        self.conv = conv if s == 1 else keras.Sequential([TFPad(autopad(k, p)), conv])
        self.bn = TFBN(w.bn) if hasattr(w, 'bn') else tf.identity
        if isinstance(w.act, nn.LeakyReLU):
            self.act = (lambda x: keras.activations.relu(x, alpha=0.1)) if act else tf.identity
        elif isinstance(w.act, nn.Hardswish):
            self.act = (lambda x: x * tf.nn.relu6(x + 3) * 0.166666667) if act else tf.identity
        elif isinstance(w.act, (nn.SiLU, SiLU)):
            self.act = (lambda x: keras.activations.swish(x)) if act else tf.identity
        else:
            raise Exception(f'no matching TensorFlow activation found for {w.act}')

    def call(self, inputs):
        return self.act(self.bn(self.conv(inputs)))

def __init__(self, c1, c2, k=1, s=1, p=None, g=1, act=True, w=None):
    super().__init__()
    assert g == 1, "TF v2.2 Conv2D does not support 'groups' argument"
    assert isinstance(k, int), 'Convolution with multiple kernels are not allowed.'
    conv = keras.layers.Conv2D(c2, k, s, 'SAME' if s == 1 else 'VALID', use_bias=False if hasattr(w, 'bn') else True, kernel_initializer=keras.initializers.Constant(w.conv.weight.permute(2, 3, 1, 0).numpy()), bias_initializer='zeros' if hasattr(w, 'bn') else keras.initializers.Constant(w.conv.bias.numpy()))
    self.conv = conv if s == 1 else keras.Sequential([TFPad(autopad(k, p)), conv])
    self.bn = TFBN(w.bn) if hasattr(w, 'bn') else tf.identity
    if isinstance(w.act, nn.LeakyReLU):
        self.act = (lambda x: keras.activations.relu(x, alpha=0.1)) if act else tf.identity
    elif isinstance(w.act, nn.Hardswish):
        self.act = (lambda x: x * tf.nn.relu6(x + 3) * 0.166666667) if act else tf.identity
    elif isinstance(w.act, (nn.SiLU, SiLU)):
        self.act = (lambda x: keras.activations.swish(x)) if act else tf.identity
    else:
        raise Exception(f'no matching TensorFlow activation found for {w.act}')

class TFFocus(keras.layers.Layer):

    def __init__(self, c1, c2, k=1, s=1, p=None, g=1, act=True, w=None):
        super().__init__()
        self.conv = TFConv(c1 * 4, c2, k, s, p, g, act, w.conv)

    def call(self, inputs):
        return self.conv(tf.concat([inputs[:, ::2, ::2, :], inputs[:, 1::2, ::2, :], inputs[:, ::2, 1::2, :], inputs[:, 1::2, 1::2, :]], 3))

def __init__(self, c1, c2, k=1, s=1, p=None, g=1, act=True, w=None):
    super().__init__()
    self.conv = TFConv(c1 * 4, c2, k, s, p, g, act, w.conv)

class TFBottleneck(keras.layers.Layer):

    def __init__(self, c1, c2, shortcut=True, g=1, e=0.5, w=None):
        super().__init__()
        c_ = int(c2 * e)
        self.cv1 = TFConv(c1, c_, 1, 1, w=w.cv1)
        self.cv2 = TFConv(c_, c2, 3, 1, g=g, w=w.cv2)
        self.add = shortcut and c1 == c2

    def call(self, inputs):
        return inputs + self.cv2(self.cv1(inputs)) if self.add else self.cv2(self.cv1(inputs))

def __init__(self, c1, c2, shortcut=True, g=1, e=0.5, w=None):
    super().__init__()
    c_ = int(c2 * e)
    self.cv1 = TFConv(c1, c_, 1, 1, w=w.cv1)
    self.cv2 = TFConv(c_, c2, 3, 1, g=g, w=w.cv2)
    self.add = shortcut and c1 == c2

class TFConv2d(keras.layers.Layer):

    def __init__(self, c1, c2, k, s=1, g=1, bias=True, w=None):
        super().__init__()
        assert g == 1, "TF v2.2 Conv2D does not support 'groups' argument"
        self.conv = keras.layers.Conv2D(c2, k, s, 'VALID', use_bias=bias, kernel_initializer=keras.initializers.Constant(w.weight.permute(2, 3, 1, 0).numpy()), bias_initializer=keras.initializers.Constant(w.bias.numpy()) if bias else None)

    def call(self, inputs):
        return self.conv(inputs)

def __init__(self, c1, c2, k, s=1, g=1, bias=True, w=None):
    super().__init__()
    assert g == 1, "TF v2.2 Conv2D does not support 'groups' argument"
    self.conv = keras.layers.Conv2D(c2, k, s, 'VALID', use_bias=bias, kernel_initializer=keras.initializers.Constant(w.weight.permute(2, 3, 1, 0).numpy()), bias_initializer=keras.initializers.Constant(w.bias.numpy()) if bias else None)

class TFBottleneckCSP(keras.layers.Layer):

    def __init__(self, c1, c2, n=1, shortcut=True, g=1, e=0.5, w=None):
        super().__init__()
        c_ = int(c2 * e)
        self.cv1 = TFConv(c1, c_, 1, 1, w=w.cv1)
        self.cv2 = TFConv2d(c1, c_, 1, 1, bias=False, w=w.cv2)
        self.cv3 = TFConv2d(c_, c_, 1, 1, bias=False, w=w.cv3)
        self.cv4 = TFConv(2 * c_, c2, 1, 1, w=w.cv4)
        self.bn = TFBN(w.bn)
        self.act = lambda x: keras.activations.relu(x, alpha=0.1)
        self.m = keras.Sequential([TFBottleneck(c_, c_, shortcut, g, e=1.0, w=w.m[j]) for j in range(n)])

    def call(self, inputs):
        y1 = self.cv3(self.m(self.cv1(inputs)))
        y2 = self.cv2(inputs)
        return self.cv4(self.act(self.bn(tf.concat((y1, y2), axis=3))))

def __init__(self, c1, c2, n=1, shortcut=True, g=1, e=0.5, w=None):
    super().__init__()
    c_ = int(c2 * e)
    self.cv1 = TFConv(c1, c_, 1, 1, w=w.cv1)
    self.cv2 = TFConv2d(c1, c_, 1, 1, bias=False, w=w.cv2)
    self.cv3 = TFConv2d(c_, c_, 1, 1, bias=False, w=w.cv3)
    self.cv4 = TFConv(2 * c_, c2, 1, 1, w=w.cv4)
    self.bn = TFBN(w.bn)
    self.act = lambda x: keras.activations.relu(x, alpha=0.1)
    self.m = keras.Sequential([TFBottleneck(c_, c_, shortcut, g, e=1.0, w=w.m[j]) for j in range(n)])

class TFC3(keras.layers.Layer):

    def __init__(self, c1, c2, n=1, shortcut=True, g=1, e=0.5, w=None):
        super().__init__()
        c_ = int(c2 * e)
        self.cv1 = TFConv(c1, c_, 1, 1, w=w.cv1)
        self.cv2 = TFConv(c1, c_, 1, 1, w=w.cv2)
        self.cv3 = TFConv(2 * c_, c2, 1, 1, w=w.cv3)
        self.m = keras.Sequential([TFBottleneck(c_, c_, shortcut, g, e=1.0, w=w.m[j]) for j in range(n)])

    def call(self, inputs):
        return self.cv3(tf.concat((self.m(self.cv1(inputs)), self.cv2(inputs)), axis=3))

def __init__(self, c1, c2, n=1, shortcut=True, g=1, e=0.5, w=None):
    super().__init__()
    c_ = int(c2 * e)
    self.cv1 = TFConv(c1, c_, 1, 1, w=w.cv1)
    self.cv2 = TFConv(c1, c_, 1, 1, w=w.cv2)
    self.cv3 = TFConv(2 * c_, c2, 1, 1, w=w.cv3)
    self.m = keras.Sequential([TFBottleneck(c_, c_, shortcut, g, e=1.0, w=w.m[j]) for j in range(n)])

class TFSPP(keras.layers.Layer):

    def __init__(self, c1, c2, k=(5, 9, 13), w=None):
        super().__init__()
        c_ = c1 // 2
        self.cv1 = TFConv(c1, c_, 1, 1, w=w.cv1)
        self.cv2 = TFConv(c_ * (len(k) + 1), c2, 1, 1, w=w.cv2)
        self.m = [keras.layers.MaxPool2D(pool_size=x, strides=1, padding='SAME') for x in k]

    def call(self, inputs):
        x = self.cv1(inputs)
        return self.cv2(tf.concat([x] + [m(x) for m in self.m], 3))

def __init__(self, c1, c2, k=(5, 9, 13), w=None):
    super().__init__()
    c_ = c1 // 2
    self.cv1 = TFConv(c1, c_, 1, 1, w=w.cv1)
    self.cv2 = TFConv(c_ * (len(k) + 1), c2, 1, 1, w=w.cv2)
    self.m = [keras.layers.MaxPool2D(pool_size=x, strides=1, padding='SAME') for x in k]

class TFSPPF(keras.layers.Layer):

    def __init__(self, c1, c2, k=5, w=None):
        super().__init__()
        c_ = c1 // 2
        self.cv1 = TFConv(c1, c_, 1, 1, w=w.cv1)
        self.cv2 = TFConv(c_ * 4, c2, 1, 1, w=w.cv2)
        self.m = keras.layers.MaxPool2D(pool_size=k, strides=1, padding='SAME')

    def call(self, inputs):
        x = self.cv1(inputs)
        y1 = self.m(x)
        y2 = self.m(y1)
        return self.cv2(tf.concat([x, y1, y2, self.m(y2)], 3))

def __init__(self, c1, c2, k=5, w=None):
    super().__init__()
    c_ = c1 // 2
    self.cv1 = TFConv(c1, c_, 1, 1, w=w.cv1)
    self.cv2 = TFConv(c_ * 4, c2, 1, 1, w=w.cv2)
    self.m = keras.layers.MaxPool2D(pool_size=k, strides=1, padding='SAME')

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

class TFUpsample(keras.layers.Layer):

    def __init__(self, size, scale_factor, mode, w=None):
        super().__init__()
        assert scale_factor == 2, 'scale_factor must be 2'
        self.upsample = lambda x: tf.image.resize(x, (x.shape[1] * 2, x.shape[2] * 2), method=mode)

    def call(self, inputs):
        return self.upsample(inputs)

def __init__(self, size, scale_factor, mode, w=None):
    super().__init__()
    assert scale_factor == 2, 'scale_factor must be 2'
    self.upsample = lambda x: tf.image.resize(x, (x.shape[1] * 2, x.shape[2] * 2), method=mode)

class TFConcat(keras.layers.Layer):

    def __init__(self, dimension=1, w=None):
        super().__init__()
        assert dimension == 1, 'convert only NCHW to NHWC concat'
        self.d = 3

    def call(self, inputs):
        return tf.concat(inputs, self.d)

def __init__(self, dimension=1, w=None):
    super().__init__()
    assert dimension == 1, 'convert only NCHW to NHWC concat'
    self.d = 3

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

class CrossConv(nn.Module):

    def __init__(self, c1, c2, k=3, s=1, g=1, e=1.0, shortcut=False):
        super().__init__()
        c_ = int(c2 * e)
        self.cv1 = Conv(c1, c_, (1, k), (1, s))
        self.cv2 = Conv(c_, c2, (k, 1), (s, 1), g=g)
        self.add = shortcut and c1 == c2

    def forward(self, x):
        return x + self.cv2(self.cv1(x)) if self.add else self.cv2(self.cv1(x))

def __init__(self, c1, c2, k=3, s=1, g=1, e=1.0, shortcut=False):
    super().__init__()
    c_ = int(c2 * e)
    self.cv1 = Conv(c1, c_, (1, k), (1, s))
    self.cv2 = Conv(c_, c2, (k, 1), (s, 1), g=g)
    self.add = shortcut and c1 == c2

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

def __init__(self, n, weight=False):
    super().__init__()
    self.weight = weight
    self.iter = range(n - 1)
    if weight:
        self.w = nn.Parameter(-torch.arange(1.0, n) / 2, requires_grad=True)

class MixConv2d(nn.Module):

    def __init__(self, c1, c2, k=(1, 3), s=1, equal_ch=True):
        super().__init__()
        n = len(k)
        if equal_ch:
            i = torch.linspace(0, n - 1e-06, c2).floor()
            c_ = [(i == g).sum() for g in range(n)]
        else:
            b = [c2] + [0] * n
            a = np.eye(n + 1, n, k=-1)
            a -= np.roll(a, 1, axis=1)
            a *= np.array(k) ** 2
            a[0] = 1
            c_ = np.linalg.lstsq(a, b, rcond=None)[0].round()
        self.m = nn.ModuleList([nn.Conv2d(c1, int(c_), k, s, k // 2, groups=math.gcd(c1, int(c_)), bias=False) for k, c_ in zip(k, c_)])
        self.bn = nn.BatchNorm2d(c2)
        self.act = nn.SiLU()

    def forward(self, x):
        return self.act(self.bn(torch.cat([m(x) for m in self.m], 1)))

def __init__(self, c1, c2, k=(1, 3), s=1, equal_ch=True):
    super().__init__()
    n = len(k)
    if equal_ch:
        i = torch.linspace(0, n - 1e-06, c2).floor()
        c_ = [(i == g).sum() for g in range(n)]
    else:
        b = [c2] + [0] * n
        a = np.eye(n + 1, n, k=-1)
        a -= np.roll(a, 1, axis=1)
        a *= np.array(k) ** 2
        a[0] = 1
        c_ = np.linalg.lstsq(a, b, rcond=None)[0].round()
    self.m = nn.ModuleList([nn.Conv2d(c1, int(c_), k, s, k // 2, groups=math.gcd(c1, int(c_)), bias=False) for k, c_ in zip(k, c_)])
    self.bn = nn.BatchNorm2d(c2)
    self.act = nn.SiLU()

class Ensemble(nn.ModuleList):

    def __init__(self):
        super().__init__()

    def forward(self, x, augment=False, profile=False, visualize=False):
        y = []
        for module in self:
            y.append(module(x, augment, profile, visualize)[0])
        y = torch.cat(y, 1)
        return (y, None)

def __init__(self):
    super().__init__()

class Conv(nn.Module):

    def __init__(self, c1, c2, k=1, s=1, p=None, g=1, act=True):
        super().__init__()
        self.conv = nn.Conv2d(c1, c2, k, s, autopad(k, p), groups=g, bias=False)
        self.bn = nn.BatchNorm2d(c2)
        self.act = nn.SiLU() if act is True else act if isinstance(act, nn.Module) else nn.Identity()

    def forward(self, x):
        return self.act(self.bn(self.conv(x)))

    def forward_fuse(self, x):
        return self.act(self.conv(x))

def __init__(self, c1, c2, k=1, s=1, p=None, g=1, act=True):
    super().__init__()
    self.conv = nn.Conv2d(c1, c2, k, s, autopad(k, p), groups=g, bias=False)
    self.bn = nn.BatchNorm2d(c2)
    self.act = nn.SiLU() if act is True else act if isinstance(act, nn.Module) else nn.Identity()

class DWConv(Conv):

    def __init__(self, c1, c2, k=1, s=1, act=True):
        super().__init__(c1, c2, k, s, g=math.gcd(c1, c2), act=act)

def __init__(self, c1, c2, k=1, s=1, act=True):
    super().__init__(c1, c2, k, s, g=math.gcd(c1, c2), act=act)

class TransformerLayer(nn.Module):

    def __init__(self, c, num_heads):
        super().__init__()
        self.q = nn.Linear(c, c, bias=False)
        self.k = nn.Linear(c, c, bias=False)
        self.v = nn.Linear(c, c, bias=False)
        self.ma = nn.MultiheadAttention(embed_dim=c, num_heads=num_heads)
        self.fc1 = nn.Linear(c, c, bias=False)
        self.fc2 = nn.Linear(c, c, bias=False)

    def forward(self, x):
        x = self.ma(self.q(x), self.k(x), self.v(x))[0] + x
        x = self.fc2(self.fc1(x)) + x
        return x

def __init__(self, c, num_heads):
    super().__init__()
    self.q = nn.Linear(c, c, bias=False)
    self.k = nn.Linear(c, c, bias=False)
    self.v = nn.Linear(c, c, bias=False)
    self.ma = nn.MultiheadAttention(embed_dim=c, num_heads=num_heads)
    self.fc1 = nn.Linear(c, c, bias=False)
    self.fc2 = nn.Linear(c, c, bias=False)

class TransformerBlock(nn.Module):

    def __init__(self, c1, c2, num_heads, num_layers):
        super().__init__()
        self.conv = None
        if c1 != c2:
            self.conv = Conv(c1, c2)
        self.linear = nn.Linear(c2, c2)
        self.tr = nn.Sequential(*(TransformerLayer(c2, num_heads) for _ in range(num_layers)))
        self.c2 = c2

    def forward(self, x):
        if self.conv is not None:
            x = self.conv(x)
        b, _, w, h = x.shape
        p = x.flatten(2).permute(2, 0, 1)
        return self.tr(p + self.linear(p)).permute(1, 2, 0).reshape(b, self.c2, w, h)

def __init__(self, c1, c2, num_heads, num_layers):
    super().__init__()
    self.conv = None
    if c1 != c2:
        self.conv = Conv(c1, c2)
    self.linear = nn.Linear(c2, c2)
    self.tr = nn.Sequential(*(TransformerLayer(c2, num_heads) for _ in range(num_layers)))
    self.c2 = c2

class Bottleneck(nn.Module):

    def __init__(self, c1, c2, shortcut=True, g=1, e=0.5):
        super().__init__()
        c_ = int(c2 * e)
        self.cv1 = Conv(c1, c_, 1, 1)
        self.cv2 = Conv(c_, c2, 3, 1, g=g)
        self.add = shortcut and c1 == c2

    def forward(self, x):
        return x + self.cv2(self.cv1(x)) if self.add else self.cv2(self.cv1(x))

def __init__(self, c1, c2, shortcut=True, g=1, e=0.5):
    super().__init__()
    c_ = int(c2 * e)
    self.cv1 = Conv(c1, c_, 1, 1)
    self.cv2 = Conv(c_, c2, 3, 1, g=g)
    self.add = shortcut and c1 == c2

class BottleneckCSP(nn.Module):

    def __init__(self, c1, c2, n=1, shortcut=True, g=1, e=0.5):
        super().__init__()
        c_ = int(c2 * e)
        self.cv1 = Conv(c1, c_, 1, 1)
        self.cv2 = nn.Conv2d(c1, c_, 1, 1, bias=False)
        self.cv3 = nn.Conv2d(c_, c_, 1, 1, bias=False)
        self.cv4 = Conv(2 * c_, c2, 1, 1)
        self.bn = nn.BatchNorm2d(2 * c_)
        self.act = nn.SiLU()
        self.m = nn.Sequential(*(Bottleneck(c_, c_, shortcut, g, e=1.0) for _ in range(n)))

    def forward(self, x):
        y1 = self.cv3(self.m(self.cv1(x)))
        y2 = self.cv2(x)
        return self.cv4(self.act(self.bn(torch.cat((y1, y2), dim=1))))

def __init__(self, c1, c2, n=1, shortcut=True, g=1, e=0.5):
    super().__init__()
    c_ = int(c2 * e)
    self.cv1 = Conv(c1, c_, 1, 1)
    self.cv2 = nn.Conv2d(c1, c_, 1, 1, bias=False)
    self.cv3 = nn.Conv2d(c_, c_, 1, 1, bias=False)
    self.cv4 = Conv(2 * c_, c2, 1, 1)
    self.bn = nn.BatchNorm2d(2 * c_)
    self.act = nn.SiLU()
    self.m = nn.Sequential(*(Bottleneck(c_, c_, shortcut, g, e=1.0) for _ in range(n)))

class C3(nn.Module):

    def __init__(self, c1, c2, n=1, shortcut=True, g=1, e=0.5):
        super().__init__()
        c_ = int(c2 * e)
        self.cv1 = Conv(c1, c_, 1, 1)
        self.cv2 = Conv(c1, c_, 1, 1)
        self.cv3 = Conv(2 * c_, c2, 1)
        self.m = nn.Sequential(*(Bottleneck(c_, c_, shortcut, g, e=1.0) for _ in range(n)))

    def forward(self, x):
        return self.cv3(torch.cat((self.m(self.cv1(x)), self.cv2(x)), dim=1))

def __init__(self, c1, c2, n=1, shortcut=True, g=1, e=0.5):
    super().__init__()
    c_ = int(c2 * e)
    self.cv1 = Conv(c1, c_, 1, 1)
    self.cv2 = Conv(c1, c_, 1, 1)
    self.cv3 = Conv(2 * c_, c2, 1)
    self.m = nn.Sequential(*(Bottleneck(c_, c_, shortcut, g, e=1.0) for _ in range(n)))

class C3TR(C3):

    def __init__(self, c1, c2, n=1, shortcut=True, g=1, e=0.5):
        super().__init__(c1, c2, n, shortcut, g, e)
        c_ = int(c2 * e)
        self.m = TransformerBlock(c_, c_, 4, n)

def __init__(self, c1, c2, n=1, shortcut=True, g=1, e=0.5):
    super().__init__(c1, c2, n, shortcut, g, e)
    c_ = int(c2 * e)
    self.m = TransformerBlock(c_, c_, 4, n)

class C3SPP(C3):

    def __init__(self, c1, c2, k=(5, 9, 13), n=1, shortcut=True, g=1, e=0.5):
        super().__init__(c1, c2, n, shortcut, g, e)
        c_ = int(c2 * e)
        self.m = SPP(c_, c_, k)

def __init__(self, c1, c2, k=(5, 9, 13), n=1, shortcut=True, g=1, e=0.5):
    super().__init__(c1, c2, n, shortcut, g, e)
    c_ = int(c2 * e)
    self.m = SPP(c_, c_, k)

class C3Ghost(C3):

    def __init__(self, c1, c2, n=1, shortcut=True, g=1, e=0.5):
        super().__init__(c1, c2, n, shortcut, g, e)
        c_ = int(c2 * e)
        self.m = nn.Sequential(*(GhostBottleneck(c_, c_) for _ in range(n)))

def __init__(self, c1, c2, n=1, shortcut=True, g=1, e=0.5):
    super().__init__(c1, c2, n, shortcut, g, e)
    c_ = int(c2 * e)
    self.m = nn.Sequential(*(GhostBottleneck(c_, c_) for _ in range(n)))

class SPP(nn.Module):

    def __init__(self, c1, c2, k=(5, 9, 13)):
        super().__init__()
        c_ = c1 // 2
        self.cv1 = Conv(c1, c_, 1, 1)
        self.cv2 = Conv(c_ * (len(k) + 1), c2, 1, 1)
        self.m = nn.ModuleList([nn.MaxPool2d(kernel_size=x, stride=1, padding=x // 2) for x in k])

    def forward(self, x):
        x = self.cv1(x)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            return self.cv2(torch.cat([x] + [m(x) for m in self.m], 1))

def __init__(self, c1, c2, k=(5, 9, 13)):
    super().__init__()
    c_ = c1 // 2
    self.cv1 = Conv(c1, c_, 1, 1)
    self.cv2 = Conv(c_ * (len(k) + 1), c2, 1, 1)
    self.m = nn.ModuleList([nn.MaxPool2d(kernel_size=x, stride=1, padding=x // 2) for x in k])

class SPPF(nn.Module):

    def __init__(self, c1, c2, k=5):
        super().__init__()
        c_ = c1 // 2
        self.cv1 = Conv(c1, c_, 1, 1)
        self.cv2 = Conv(c_ * 4, c2, 1, 1)
        self.m = nn.MaxPool2d(kernel_size=k, stride=1, padding=k // 2)

    def forward(self, x):
        x = self.cv1(x)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            y1 = self.m(x)
            y2 = self.m(y1)
            return self.cv2(torch.cat([x, y1, y2, self.m(y2)], 1))

def __init__(self, c1, c2, k=5):
    super().__init__()
    c_ = c1 // 2
    self.cv1 = Conv(c1, c_, 1, 1)
    self.cv2 = Conv(c_ * 4, c2, 1, 1)
    self.m = nn.MaxPool2d(kernel_size=k, stride=1, padding=k // 2)

class Focus(nn.Module):

    def __init__(self, c1, c2, k=1, s=1, p=None, g=1, act=True):
        super().__init__()
        self.conv = Conv(c1 * 4, c2, k, s, p, g, act)

    def forward(self, x):
        return self.conv(torch.cat([x[..., ::2, ::2], x[..., 1::2, ::2], x[..., ::2, 1::2], x[..., 1::2, 1::2]], 1))

def __init__(self, c1, c2, k=1, s=1, p=None, g=1, act=True):
    super().__init__()
    self.conv = Conv(c1 * 4, c2, k, s, p, g, act)

class GhostConv(nn.Module):

    def __init__(self, c1, c2, k=1, s=1, g=1, act=True):
        super().__init__()
        c_ = c2 // 2
        self.cv1 = Conv(c1, c_, k, s, None, g, act)
        self.cv2 = Conv(c_, c_, 5, 1, None, c_, act)

    def forward(self, x):
        y = self.cv1(x)
        return torch.cat([y, self.cv2(y)], 1)

def __init__(self, c1, c2, k=1, s=1, g=1, act=True):
    super().__init__()
    c_ = c2 // 2
    self.cv1 = Conv(c1, c_, k, s, None, g, act)
    self.cv2 = Conv(c_, c_, 5, 1, None, c_, act)

class GhostBottleneck(nn.Module):

    def __init__(self, c1, c2, k=3, s=1):
        super().__init__()
        c_ = c2 // 2
        self.conv = nn.Sequential(GhostConv(c1, c_, 1, 1), DWConv(c_, c_, k, s, act=False) if s == 2 else nn.Identity(), GhostConv(c_, c2, 1, 1, act=False))
        self.shortcut = nn.Sequential(DWConv(c1, c1, k, s, act=False), Conv(c1, c2, 1, 1, act=False)) if s == 2 else nn.Identity()

    def forward(self, x):
        return self.conv(x) + self.shortcut(x)

def __init__(self, c1, c2, k=3, s=1):
    super().__init__()
    c_ = c2 // 2
    self.conv = nn.Sequential(GhostConv(c1, c_, 1, 1), DWConv(c_, c_, k, s, act=False) if s == 2 else nn.Identity(), GhostConv(c_, c2, 1, 1, act=False))
    self.shortcut = nn.Sequential(DWConv(c1, c1, k, s, act=False), Conv(c1, c2, 1, 1, act=False)) if s == 2 else nn.Identity()

class Contract(nn.Module):

    def __init__(self, gain=2):
        super().__init__()
        self.gain = gain

    def forward(self, x):
        b, c, h, w = x.size()
        s = self.gain
        x = x.view(b, c, h // s, s, w // s, s)
        x = x.permute(0, 3, 5, 1, 2, 4).contiguous()
        return x.view(b, c * s * s, h // s, w // s)

def __init__(self, gain=2):
    super().__init__()
    self.gain = gain

class Expand(nn.Module):

    def __init__(self, gain=2):
        super().__init__()
        self.gain = gain

    def forward(self, x):
        b, c, h, w = x.size()
        s = self.gain
        x = x.view(b, s, s, c // s ** 2, h, w)
        x = x.permute(0, 3, 4, 1, 5, 2).contiguous()
        return x.view(b, c // s ** 2, h * s, w * s)

def __init__(self, gain=2):
    super().__init__()
    self.gain = gain

class Concat(nn.Module):

    def __init__(self, dimension=1):
        super().__init__()
        self.d = dimension

    def forward(self, x):
        return torch.cat(x, self.d)

def __init__(self, dimension=1):
    super().__init__()
    self.d = dimension

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

def __init__(self, model):
    super().__init__()
    LOGGER.info('Adding AutoShape... ')
    copy_attr(self, model, include=('yaml', 'nc', 'hyp', 'names', 'stride', 'abc'), exclude=())
    self.dmb = isinstance(model, DetectMultiBackend)
    self.pt = not self.dmb or model.pt
    self.model = model.eval()

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

class Classify(nn.Module):

    def __init__(self, c1, c2, k=1, s=1, p=None, g=1):
        super().__init__()
        self.aap = nn.AdaptiveAvgPool2d(1)
        self.conv = nn.Conv2d(c1, c2, k, s, autopad(k, p), groups=g)
        self.flat = nn.Flatten()

    def forward(self, x):
        z = torch.cat([self.aap(y) for y in (x if isinstance(x, list) else [x])], 1)
        return self.flat(self.conv(z))

def __init__(self, c1, c2, k=1, s=1, p=None, g=1):
    super().__init__()
    self.aap = nn.AdaptiveAvgPool2d(1)
    self.conv = nn.Conv2d(c1, c2, k, s, autopad(k, p), groups=g)
    self.flat = nn.Flatten()

