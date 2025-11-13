# Cluster 12

def train(epochs=10, batch_size=32, alpha=0.6, w=0.4, num_workers=2, lr=0.0001, save_epoch=10, train_path=ROOT / 'dataset/KITTI/training', model_path=ROOT / 'weights/', select_model='resnet18', api_key=''):
    train_path = str(train_path)
    model_path = str(model_path)
    print('[INFO] Loading dataset...')
    dataset = Dataset(train_path)
    hyper_params = {'epochs': epochs, 'batch_size': batch_size, 'w': w, 'num_workers': num_workers, 'lr': lr, 'shuffle': True}
    experiment = Experiment(api_key, project_name='YOLO3D')
    experiment.log_parameters(hyper_params)
    data_gen = data.DataLoader(dataset, batch_size=hyper_params['batch_size'], shuffle=hyper_params['shuffle'], num_workers=hyper_params['num_workers'])
    base_model = model_factory[select_model]
    model = regressor_factory[select_model](model=base_model).cuda()
    opt_SGD = torch.optim.SGD(model.parameters(), lr=hyper_params['lr'], momentum=0.9)
    conf_loss_func = nn.CrossEntropyLoss().cuda()
    dim_loss_func = nn.MSELoss().cuda()
    orient_loss_func = OrientationLoss
    latest_model = None
    first_epoch = 1
    if not os.path.isdir(model_path):
        os.mkdir(model_path)
    else:
        try:
            latest_model = [x for x in sorted(os.listdir(model_path)) if x.endswith('.pkl')][-1]
        except:
            pass
    if latest_model is not None:
        checkpoint = torch.load(model_path + latest_model)
        model.load_state_dict(checkpoint['model_state_dict'])
        opt_SGD.load_state_dict(checkpoint['optimizer_state_dict'])
        first_epoch = checkpoint['epoch']
        loss = checkpoint['loss']
        print(f'[INFO] Using previous model {latest_model} at {first_epoch} epochs')
        print('[INFO] Resuming training...')
    total_num_batches = int(len(dataset) / hyper_params['batch_size'])
    with experiment.train():
        for epoch in range(first_epoch, int(hyper_params['epochs']) + 1):
            curr_batch = 0
            passes = 0
            with tqdm(data_gen, unit='batch') as tepoch:
                for local_batch, local_labels in tepoch:
                    tepoch.set_description(f'Epoch {epoch}')
                    truth_orient = local_labels['Orientation'].float().cuda()
                    truth_conf = local_labels['Confidence'].float().cuda()
                    truth_dim = local_labels['Dimensions'].float().cuda()
                    local_batch = local_batch.float().cuda()
                    [orient, conf, dim] = model(local_batch)
                    orient_loss = orient_loss_func(orient, truth_orient, truth_conf)
                    dim_loss = dim_loss_func(dim, truth_dim)
                    truth_conf = torch.max(truth_conf, dim=1)[1]
                    conf_loss = conf_loss_func(conf, truth_conf)
                    loss_theta = conf_loss + w * orient_loss
                    loss = alpha * dim_loss + loss_theta
                    writer.add_scalar('Loss/train', loss, epoch)
                    experiment.log_metric('Loss/train', loss, epoch=epoch)
                    opt_SGD.zero_grad()
                    loss.backward()
                    opt_SGD.step()
                    tepoch.set_postfix(loss=loss.item())
            if epoch % save_epoch == 0:
                model_name = os.path.join(model_path, f'{select_model}_epoch_{epoch}.pkl')
                torch.save({'epoch': epoch, 'model_state_dict': model.state_dict(), 'optimizer_state_dict': opt_SGD.state_dict(), 'loss': loss}, model_name)
                print(f'[INFO] Saving weights as {model_name}')
    writer.flush()
    writer.close()

def detect3d(reg_weights, model_select, source, calib_file, show_result, save_result, output_path):
    imgs_path = sorted(glob.glob(str(source) + '/*'))
    calib = str(calib_file)
    base_model = model_factory[model_select]
    regressor = regressor_factory[model_select](model=base_model).cuda()
    checkpoint = torch.load(reg_weights)
    regressor.load_state_dict(checkpoint['model_state_dict'])
    regressor.eval()
    averages = ClassAverages.ClassAverages()
    angle_bins = generate_bins(2)
    for i, img_path in enumerate(imgs_path):
        img = cv2.imread(img_path)
        dets = detect2d(weights='yolov5s.pt', source=img_path, data='data/coco128.yaml', imgsz=[640, 640], device=0, classes=[0, 2, 3, 5])
        for det in dets:
            if not averages.recognized_class(det.detected_class):
                continue
            try:
                detectedObject = DetectedObject(img, det.detected_class, det.box_2d, calib)
            except:
                continue
            theta_ray = detectedObject.theta_ray
            input_img = detectedObject.img
            proj_matrix = detectedObject.proj_matrix
            box_2d = det.box_2d
            detected_class = det.detected_class
            input_tensor = torch.zeros([1, 3, 224, 224]).cuda()
            input_tensor[0, :, :, :] = input_img
            [orient, conf, dim] = regressor(input_tensor)
            orient = orient.cpu().data.numpy()[0, :, :]
            conf = conf.cpu().data.numpy()[0, :]
            dim = dim.cpu().data.numpy()[0, :]
            dim += averages.get_item(detected_class)
            argmax = np.argmax(conf)
            orient = orient[argmax, :]
            cos = orient[0]
            sin = orient[1]
            alpha = np.arctan2(sin, cos)
            alpha += angle_bins[argmax]
            alpha -= np.pi
            plot3d(img, proj_matrix, box_2d, dim, alpha, theta_ray)
        if show_result:
            cv2.imshow('3d detection', img)
            cv2.waitKey(0)
        if save_result and output_path is not None:
            try:
                os.mkdir(output_path)
            except:
                pass
            cv2.imwrite(f'{output_path}/{i:03d}.png', img)

def train(train_path=ROOT / 'dataset/KITTI/training', checkpoint_path=ROOT / 'weights/checkpoints', model_select='resnet18', epochs=10, batch_size=32, num_workers=2, gpu=1, val_split=0.1, model_path=ROOT / 'weights/', api_key=''):
    comet_logger = CometLogger(api_key=api_key, project_name='YOLO3D')
    checkpoint_callback = ModelCheckpoint(monitor='val_loss', dirpath=checkpoint_path, filename='model_{epoch:02d}_{val_loss:.2f}', save_top_k=3, mode='min')
    trainer = Trainer(logger=comet_logger, callbacks=[checkpoint_callback], gpus=gpu, min_epochs=1, max_epochs=epochs)
    model = Model(model_select=model_select)
    try:
        latest_model = [x for x in sorted(os.listdir(model_path)) if x.endswith('.pkl')][-1]
    except:
        latest_model = None
    if latest_model is not None:
        model.load_from_checkpoint(latest_model)
        print(f'[INFO] Use previous model {latest_model}')
    dataset = KITTIDataModule(dataset_path=train_path, batch_size=batch_size, num_workers=num_workers, val_split=val_split)
    trainer.fit(model=model, datamodule=dataset)

def de_parallel(model):
    return model.module if is_parallel(model) else model

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

def update(self, model):
    with torch.no_grad():
        self.updates += 1
        d = self.decay(self.updates)
        msd = model.module.state_dict() if is_parallel(model) else model.state_dict()
        for k, v in self.ema.state_dict().items():
            if v.dtype.is_floating_point:
                v *= d
                v += (1 - d) * msd[k].detach()

class ComputeLoss:

    def __init__(self, model, autobalance=False):
        self.sort_obj_iou = False
        device = next(model.parameters()).device
        h = model.hyp
        BCEcls = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([h['cls_pw']], device=device))
        BCEobj = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([h['obj_pw']], device=device))
        self.cp, self.cn = smooth_BCE(eps=h.get('label_smoothing', 0.0))
        g = h['fl_gamma']
        if g > 0:
            BCEcls, BCEobj = (FocalLoss(BCEcls, g), FocalLoss(BCEobj, g))
        det = model.module.model[-1] if is_parallel(model) else model.model[-1]
        self.balance = {3: [4.0, 1.0, 0.4]}.get(det.nl, [4.0, 1.0, 0.25, 0.06, 0.02])
        self.ssi = list(det.stride).index(16) if autobalance else 0
        self.BCEcls, self.BCEobj, self.gr, self.hyp, self.autobalance = (BCEcls, BCEobj, 1.0, h, autobalance)
        for k in ('na', 'nc', 'nl', 'anchors'):
            setattr(self, k, getattr(det, k))

    def __call__(self, p, targets):
        device = targets.device
        lcls, lbox, lobj = (torch.zeros(1, device=device), torch.zeros(1, device=device), torch.zeros(1, device=device))
        tcls, tbox, indices, anchors = self.build_targets(p, targets)
        for i, pi in enumerate(p):
            b, a, gj, gi = indices[i]
            tobj = torch.zeros_like(pi[..., 0], device=device)
            n = b.shape[0]
            if n:
                ps = pi[b, a, gj, gi]
                pxy = ps[:, :2].sigmoid() * 2 - 0.5
                pwh = (ps[:, 2:4].sigmoid() * 2) ** 2 * anchors[i]
                pbox = torch.cat((pxy, pwh), 1)
                iou = bbox_iou(pbox.T, tbox[i], x1y1x2y2=False, CIoU=True)
                lbox += (1.0 - iou).mean()
                score_iou = iou.detach().clamp(0).type(tobj.dtype)
                if self.sort_obj_iou:
                    sort_id = torch.argsort(score_iou)
                    b, a, gj, gi, score_iou = (b[sort_id], a[sort_id], gj[sort_id], gi[sort_id], score_iou[sort_id])
                tobj[b, a, gj, gi] = 1.0 - self.gr + self.gr * score_iou
                if self.nc > 1:
                    t = torch.full_like(ps[:, 5:], self.cn, device=device)
                    t[range(n), tcls[i]] = self.cp
                    lcls += self.BCEcls(ps[:, 5:], t)
            obji = self.BCEobj(pi[..., 4], tobj)
            lobj += obji * self.balance[i]
            if self.autobalance:
                self.balance[i] = self.balance[i] * 0.9999 + 0.0001 / obji.detach().item()
        if self.autobalance:
            self.balance = [x / self.balance[self.ssi] for x in self.balance]
        lbox *= self.hyp['box']
        lobj *= self.hyp['obj']
        lcls *= self.hyp['cls']
        bs = tobj.shape[0]
        return ((lbox + lobj + lcls) * bs, torch.cat((lbox, lobj, lcls)).detach())

    def build_targets(self, p, targets):
        na, nt = (self.na, targets.shape[0])
        tcls, tbox, indices, anch = ([], [], [], [])
        gain = torch.ones(7, device=targets.device)
        ai = torch.arange(na, device=targets.device).float().view(na, 1).repeat(1, nt)
        targets = torch.cat((targets.repeat(na, 1, 1), ai[:, :, None]), 2)
        g = 0.5
        off = torch.tensor([[0, 0], [1, 0], [0, 1], [-1, 0], [0, -1]], device=targets.device).float() * g
        for i in range(self.nl):
            anchors = self.anchors[i]
            gain[2:6] = torch.tensor(p[i].shape)[[3, 2, 3, 2]]
            t = targets * gain
            if nt:
                r = t[:, :, 4:6] / anchors[:, None]
                j = torch.max(r, 1 / r).max(2)[0] < self.hyp['anchor_t']
                t = t[j]
                gxy = t[:, 2:4]
                gxi = gain[[2, 3]] - gxy
                j, k = ((gxy % 1 < g) & (gxy > 1)).T
                l, m = ((gxi % 1 < g) & (gxi > 1)).T
                j = torch.stack((torch.ones_like(j), j, k, l, m))
                t = t.repeat((5, 1, 1))[j]
                offsets = (torch.zeros_like(gxy)[None] + off[:, None])[j]
            else:
                t = targets[0]
                offsets = 0
            b, c = t[:, :2].long().T
            gxy = t[:, 2:4]
            gwh = t[:, 4:6]
            gij = (gxy - offsets).long()
            gi, gj = gij.T
            a = t[:, 6].long()
            indices.append((b, a, gj.clamp_(0, gain[3] - 1), gi.clamp_(0, gain[2] - 1)))
            tbox.append(torch.cat((gxy - gij, gwh), 1))
            anch.append(anchors[a])
            tcls.append(c)
        return (tcls, tbox, indices, anch)

def __call__(self, p, targets):
    device = targets.device
    lcls, lbox, lobj = (torch.zeros(1, device=device), torch.zeros(1, device=device), torch.zeros(1, device=device))
    tcls, tbox, indices, anchors = self.build_targets(p, targets)
    for i, pi in enumerate(p):
        b, a, gj, gi = indices[i]
        tobj = torch.zeros_like(pi[..., 0], device=device)
        n = b.shape[0]
        if n:
            ps = pi[b, a, gj, gi]
            pxy = ps[:, :2].sigmoid() * 2 - 0.5
            pwh = (ps[:, 2:4].sigmoid() * 2) ** 2 * anchors[i]
            pbox = torch.cat((pxy, pwh), 1)
            iou = bbox_iou(pbox.T, tbox[i], x1y1x2y2=False, CIoU=True)
            lbox += (1.0 - iou).mean()
            score_iou = iou.detach().clamp(0).type(tobj.dtype)
            if self.sort_obj_iou:
                sort_id = torch.argsort(score_iou)
                b, a, gj, gi, score_iou = (b[sort_id], a[sort_id], gj[sort_id], gi[sort_id], score_iou[sort_id])
            tobj[b, a, gj, gi] = 1.0 - self.gr + self.gr * score_iou
            if self.nc > 1:
                t = torch.full_like(ps[:, 5:], self.cn, device=device)
                t[range(n), tcls[i]] = self.cp
                lcls += self.BCEcls(ps[:, 5:], t)
        obji = self.BCEobj(pi[..., 4], tobj)
        lobj += obji * self.balance[i]
        if self.autobalance:
            self.balance[i] = self.balance[i] * 0.9999 + 0.0001 / obji.detach().item()
    if self.autobalance:
        self.balance = [x / self.balance[self.ssi] for x in self.balance]
    lbox *= self.hyp['box']
    lobj *= self.hyp['obj']
    lcls *= self.hyp['cls']
    bs = tobj.shape[0]
    return ((lbox + lobj + lcls) * bs, torch.cat((lbox, lobj, lcls)).detach())

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

def train_dataloader(self):
    train_loader = DataLoader(self.KITTI_train, **self.params)
    return train_loader

def val_dataloader(self):
    val_loader = DataLoader(self.KITTI_val, batch_size=self.params['batch_size'], shuffle=False, num_workers=self.params['num_workers'])
    return val_loader

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

def _print_biases(self):
    m = self.model[-1]
    for mi in m.m:
        b = mi.bias.detach().view(m.na, -1).T
        LOGGER.info(('%6g Conv2d.bias:' + '%10.3g' * 6) % (mi.weight.shape[1], *b[:5].mean(1).tolist(), b[5:].mean()))

