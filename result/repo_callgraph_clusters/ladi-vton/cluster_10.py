# Cluster 10

class VGGLoss(nn.Module):
    """
    VGG loss module.
    """

    def __init__(self, gpu=None):
        super(VGGLoss, self).__init__()
        self.vgg = VGG19().eval()
        if gpu:
            self.vgg = self.vgg.cuda(gpu)
        self.criterion = nn.L1Loss()
        self.weights = [1.0 / 32, 1.0 / 16, 1.0 / 8, 1.0 / 4, 1.0]
        self.register_buffer('mean', torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1))
        self.register_buffer('std', torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1))
        self.resize = Resize(256, antialias=True)

    def forward(self, x, y):
        x = self.resize(x)
        y = self.resize(y)
        x = (x + 1) / 2
        y = (y + 1) / 2
        x = (x - self.mean) / self.std
        y = (y - self.mean) / self.std
        x_vgg, y_vgg = (self.vgg(x), self.vgg(y))
        loss = 0
        for i in range(len(x_vgg)):
            loss += self.weights[i] * self.criterion(x_vgg[i], y_vgg[i].detach())
        return loss

def __init__(self, gpu=None):
    super(VGGLoss, self).__init__()
    self.vgg = VGG19().eval()
    if gpu:
        self.vgg = self.vgg.cuda(gpu)
    self.criterion = nn.L1Loss()
    self.weights = [1.0 / 32, 1.0 / 16, 1.0 / 8, 1.0 / 4, 1.0]
    self.register_buffer('mean', torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1))
    self.register_buffer('std', torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1))
    self.resize = Resize(256, antialias=True)

def kpoint_to_heatmap(kpoint, shape, sigma):
    """Converts a 2D keypoint to a gaussian heatmap

    Parameters
    ----------
    kpoint: np.array
        2D coordinates of keypoint [x, y].
    shape: tuple
        Heatmap dimension (HxW).
    sigma: float
        Variance value of the gaussian.

    Returns
    -------
    heatmap: np.array
        A gaussian heatmap HxW.
    """
    map_h = shape[0]
    map_w = shape[1]
    if np.any(kpoint > 0):
        x, y = kpoint
        xy_grid = np.mgrid[:map_w, :map_h].transpose(2, 1, 0)
        heatmap = np.exp(-np.sum((xy_grid - (x, y)) ** 2, axis=-1) / sigma ** 2)
        heatmap /= heatmap.max() + np.finfo('float32').eps
    else:
        heatmap = np.zeros((map_h, map_w))
    return torch.Tensor(heatmap)

class VectorQuantizer(nn.Module):
    """
    Improved version over VectorQuantizer, can be used as a drop-in replacement. Mostly avoids costly matrix
    multiplications and allows for post-hoc remapping of indices.
    """

    def __init__(self, n_e, vq_embed_dim, beta, remap=None, unknown_index='random', sane_index_shape=False, legacy=True):
        super().__init__()
        self.n_e = n_e
        self.vq_embed_dim = vq_embed_dim
        self.beta = beta
        self.legacy = legacy
        self.embedding = nn.Embedding(self.n_e, self.vq_embed_dim)
        self.embedding.weight.data.uniform_(-1.0 / self.n_e, 1.0 / self.n_e)
        self.remap = remap
        if self.remap is not None:
            self.register_buffer('used', torch.tensor(np.load(self.remap)))
            self.re_embed = self.used.shape[0]
            self.unknown_index = unknown_index
            if self.unknown_index == 'extra':
                self.unknown_index = self.re_embed
                self.re_embed = self.re_embed + 1
            print(f'Remapping {self.n_e} indices to {self.re_embed} indices. Using {self.unknown_index} for unknown indices.')
        else:
            self.re_embed = n_e
        self.sane_index_shape = sane_index_shape

    def remap_to_used(self, inds):
        ishape = inds.shape
        assert len(ishape) > 1
        inds = inds.reshape(ishape[0], -1)
        used = self.used.to(inds)
        match = (inds[:, :, None] == used[None, None, ...]).long()
        new = match.argmax(-1)
        unknown = match.sum(2) < 1
        if self.unknown_index == 'random':
            new[unknown] = torch.randint(0, self.re_embed, size=new[unknown].shape).to(device=new.device)
        else:
            new[unknown] = self.unknown_index
        return new.reshape(ishape)

    def unmap_to_all(self, inds):
        ishape = inds.shape
        assert len(ishape) > 1
        inds = inds.reshape(ishape[0], -1)
        used = self.used.to(inds)
        if self.re_embed > self.used.shape[0]:
            inds[inds >= self.used.shape[0]] = 0
        back = torch.gather(used[None, :][inds.shape[0] * [0], :], 1, inds)
        return back.reshape(ishape)

    def forward(self, z):
        z = z.permute(0, 2, 3, 1).contiguous()
        z_flattened = z.view(-1, self.vq_embed_dim)
        min_encoding_indices = torch.argmin(torch.cdist(z_flattened, self.embedding.weight), dim=1)
        z_q = self.embedding(min_encoding_indices).view(z.shape)
        perplexity = None
        min_encodings = None
        if not self.legacy:
            loss = self.beta * torch.mean((z_q.detach() - z) ** 2) + torch.mean((z_q - z.detach()) ** 2)
        else:
            loss = torch.mean((z_q.detach() - z) ** 2) + self.beta * torch.mean((z_q - z.detach()) ** 2)
        z_q = z + (z_q - z).detach()
        z_q = z_q.permute(0, 3, 1, 2).contiguous()
        if self.remap is not None:
            min_encoding_indices = min_encoding_indices.reshape(z.shape[0], -1)
            min_encoding_indices = self.remap_to_used(min_encoding_indices)
            min_encoding_indices = min_encoding_indices.reshape(-1, 1)
        if self.sane_index_shape:
            min_encoding_indices = min_encoding_indices.reshape(z_q.shape[0], z_q.shape[2], z_q.shape[3])
        return (z_q, loss, (perplexity, min_encodings, min_encoding_indices))

    def get_codebook_entry(self, indices, shape):
        if self.remap is not None:
            indices = indices.reshape(shape[0], -1)
            indices = self.unmap_to_all(indices)
            indices = indices.reshape(-1)
        z_q = self.embedding(indices)
        if shape is not None:
            z_q = z_q.view(shape)
            z_q = z_q.permute(0, 3, 1, 2).contiguous()
        return z_q

def __init__(self, n_e, vq_embed_dim, beta, remap=None, unknown_index='random', sane_index_shape=False, legacy=True):
    super().__init__()
    self.n_e = n_e
    self.vq_embed_dim = vq_embed_dim
    self.beta = beta
    self.legacy = legacy
    self.embedding = nn.Embedding(self.n_e, self.vq_embed_dim)
    self.embedding.weight.data.uniform_(-1.0 / self.n_e, 1.0 / self.n_e)
    self.remap = remap
    if self.remap is not None:
        self.register_buffer('used', torch.tensor(np.load(self.remap)))
        self.re_embed = self.used.shape[0]
        self.unknown_index = unknown_index
        if self.unknown_index == 'extra':
            self.unknown_index = self.re_embed
            self.re_embed = self.re_embed + 1
        print(f'Remapping {self.n_e} indices to {self.re_embed} indices. Using {self.unknown_index} for unknown indices.')
    else:
        self.re_embed = n_e
    self.sane_index_shape = sane_index_shape

class DiagonalGaussianDistribution(object):

    def __init__(self, parameters, deterministic=False):
        self.parameters = parameters
        self.mean, self.logvar = torch.chunk(parameters, 2, dim=1)
        self.logvar = torch.clamp(self.logvar, -30.0, 20.0)
        self.deterministic = deterministic
        self.std = torch.exp(0.5 * self.logvar)
        self.var = torch.exp(self.logvar)
        if self.deterministic:
            self.var = self.std = torch.zeros_like(self.mean, device=self.parameters.device, dtype=self.parameters.dtype)

    def sample(self, generator: Optional[torch.Generator]=None) -> torch.FloatTensor:
        sample = randn_tensor(self.mean.shape, generator=generator, device=self.parameters.device, dtype=self.parameters.dtype)
        x = self.mean + self.std * sample
        return x

    def kl(self, other=None):
        if self.deterministic:
            return torch.Tensor([0.0])
        elif other is None:
            return 0.5 * torch.sum(torch.pow(self.mean, 2) + self.var - 1.0 - self.logvar, dim=[1, 2, 3])
        else:
            return 0.5 * torch.sum(torch.pow(self.mean - other.mean, 2) / other.var + self.var / other.var - 1.0 - self.logvar + other.logvar, dim=[1, 2, 3])

    def nll(self, sample, dims=[1, 2, 3]):
        if self.deterministic:
            return torch.Tensor([0.0])
        logtwopi = np.log(2.0 * np.pi)
        return 0.5 * torch.sum(logtwopi + self.logvar + torch.pow(sample - self.mean, 2) / self.var, dim=dims)

    def mode(self):
        return self.mean

def kl(self, other=None):
    if self.deterministic:
        return torch.Tensor([0.0])
    elif other is None:
        return 0.5 * torch.sum(torch.pow(self.mean, 2) + self.var - 1.0 - self.logvar, dim=[1, 2, 3])
    else:
        return 0.5 * torch.sum(torch.pow(self.mean - other.mean, 2) / other.var + self.var / other.var - 1.0 - self.logvar + other.logvar, dim=[1, 2, 3])

def nll(self, sample, dims=[1, 2, 3]):
    if self.deterministic:
        return torch.Tensor([0.0])
    logtwopi = np.log(2.0 * np.pi)
    return 0.5 * torch.sum(logtwopi + self.logvar + torch.pow(sample - self.mean, 2) / self.var, dim=dims)

class FeatureL2Norm(torch.nn.Module):

    def __init__(self):
        super(FeatureL2Norm, self).__init__()

    def forward(self, feature):
        epsilon = 1e-06
        norm = torch.pow(torch.sum(torch.pow(feature, 2), 1) + epsilon, 0.5).unsqueeze(1).expand_as(feature)
        return torch.div(feature, norm)

def forward(self, feature):
    epsilon = 1e-06
    norm = torch.pow(torch.sum(torch.pow(feature, 2), 1) + epsilon, 0.5).unsqueeze(1).expand_as(feature)
    return torch.div(feature, norm)

class BoundedGridLocNet(nn.Module):

    def __init__(self, grid_height, grid_width, target_control_points, n_layers):
        super(BoundedGridLocNet, self).__init__()
        self.regression = FeatureRegression(output_dim=grid_height * grid_width * 2)
        bias = torch.from_numpy(np.arctanh(target_control_points.numpy()))
        bias = bias.view(-1)
        self.regression.linear.bias.data.copy_(bias)
        self.regression.linear.weight.data.zero_()

    def forward(self, x):
        batch_size = x.size(0)
        points = self.regression(x)
        coor = points.view(batch_size, -1, 2)
        row = self.get_row(coor, 5)
        col = self.get_col(coor, 5)
        rg_loss = sum(self.grad_row(coor, 5))
        cg_loss = sum(self.grad_col(coor, 5))
        rg_loss = torch.max(rg_loss, torch.tensor(0.02).cuda())
        cg_loss = torch.max(cg_loss, torch.tensor(0.02).cuda())
        rx, ry, cx, cy = (torch.tensor(0.08).cuda(), torch.tensor(0.08).cuda(), torch.tensor(0.08).cuda(), torch.tensor(0.08).cuda())
        row_x, row_y = (row[:, :, 0], row[:, :, 1])
        col_x, col_y = (col[:, :, 0], col[:, :, 1])
        rx_loss = torch.max(rx, row_x).mean()
        ry_loss = torch.max(ry, row_y).mean()
        cx_loss = torch.max(cx, col_x).mean()
        cy_loss = torch.max(cy, col_y).mean()
        return (coor, rx_loss, ry_loss, cx_loss, cy_loss, rg_loss, cg_loss)

    def get_row(self, coor, num):
        sec_dic = []
        for j in range(num):
            sum = 0
            buffer = 0
            flag = False
            max = -1
            for i in range(num - 1):
                differ = (coor[:, j * num + i + 1, :] - coor[:, j * num + i, :]) ** 2
                if not flag:
                    second_dif = 0
                    flag = True
                else:
                    second_dif = torch.abs(differ - buffer)
                    sec_dic.append(second_dif)
                buffer = differ
                sum += second_dif
        return torch.stack(sec_dic, dim=1)

    def get_col(self, coor, num):
        sec_dic = []
        for i in range(num):
            sum = 0
            buffer = 0
            flag = False
            max = -1
            for j in range(num - 1):
                differ = (coor[:, (j + 1) * num + i, :] - coor[:, j * num + i, :]) ** 2
                if not flag:
                    second_dif = 0
                    flag = True
                else:
                    second_dif = torch.abs(differ - buffer)
                    sec_dic.append(second_dif)
                buffer = differ
                sum += second_dif
        return torch.stack(sec_dic, dim=1)

    def grad_row(self, coor, num):
        sec_term = []
        for j in range(num):
            for i in range(1, num - 1):
                x0, y0 = coor[:, j * num + i - 1, :][0]
                x1, y1 = coor[:, j * num + i + 0, :][0]
                x2, y2 = coor[:, j * num + i + 1, :][0]
                grad = torch.abs((y1 - y0) * (x1 - x2) - (y1 - y2) * (x1 - x0))
                sec_term.append(grad)
        return sec_term

    def grad_col(self, coor, num):
        sec_term = []
        for i in range(num):
            for j in range(1, num - 1):
                x0, y0 = coor[:, (j - 1) * num + i, :][0]
                x1, y1 = coor[:, j * num + i, :][0]
                x2, y2 = coor[:, (j + 1) * num + i, :][0]
                grad = torch.abs((y1 - y0) * (x1 - x2) - (y1 - y2) * (x1 - x0))
                sec_term.append(grad)
        return sec_term

def forward(self, x):
    batch_size = x.size(0)
    points = self.regression(x)
    coor = points.view(batch_size, -1, 2)
    row = self.get_row(coor, 5)
    col = self.get_col(coor, 5)
    rg_loss = sum(self.grad_row(coor, 5))
    cg_loss = sum(self.grad_col(coor, 5))
    rg_loss = torch.max(rg_loss, torch.tensor(0.02).cuda())
    cg_loss = torch.max(cg_loss, torch.tensor(0.02).cuda())
    rx, ry, cx, cy = (torch.tensor(0.08).cuda(), torch.tensor(0.08).cuda(), torch.tensor(0.08).cuda(), torch.tensor(0.08).cuda())
    row_x, row_y = (row[:, :, 0], row[:, :, 1])
    col_x, col_y = (col[:, :, 0], col[:, :, 1])
    rx_loss = torch.max(rx, row_x).mean()
    ry_loss = torch.max(ry, row_y).mean()
    cx_loss = torch.max(cx, col_x).mean()
    cy_loss = torch.max(cy, col_y).mean()
    return (coor, rx_loss, ry_loss, cx_loss, cy_loss, rg_loss, cg_loss)

