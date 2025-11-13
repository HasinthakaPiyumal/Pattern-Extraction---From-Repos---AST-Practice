# Cluster 22

class Callbacks:
    """"
    Handles all registered callbacks for YOLOv5 Hooks
    """

    def __init__(self):
        self._callbacks = {'on_pretrain_routine_start': [], 'on_pretrain_routine_end': [], 'on_train_start': [], 'on_train_epoch_start': [], 'on_train_batch_start': [], 'optimizer_step': [], 'on_before_zero_grad': [], 'on_train_batch_end': [], 'on_train_epoch_end': [], 'on_val_start': [], 'on_val_batch_start': [], 'on_val_image_end': [], 'on_val_batch_end': [], 'on_val_end': [], 'on_fit_epoch_end': [], 'on_model_save': [], 'on_train_end': [], 'on_params_update': [], 'teardown': []}

    def register_action(self, hook, name='', callback=None):
        """
        Register a new action to a callback hook

        Args:
            hook        The callback hook name to register the action to
            name        The name of the action for later reference
            callback    The callback to fire
        """
        assert hook in self._callbacks, f"hook '{hook}' not found in callbacks {self._callbacks}"
        assert callable(callback), f"callback '{callback}' is not callable"
        self._callbacks[hook].append({'name': name, 'callback': callback})

    def get_registered_actions(self, hook=None):
        """"
        Returns all the registered actions by callback hook

        Args:
            hook The name of the hook to check, defaults to all
        """
        if hook:
            return self._callbacks[hook]
        else:
            return self._callbacks

    def run(self, hook, *args, **kwargs):
        """
        Loop through the registered actions and fire all callbacks

        Args:
            hook The name of the hook to check, defaults to all
            args Arguments to receive from YOLOv5
            kwargs Keyword Arguments to receive from YOLOv5
        """
        assert hook in self._callbacks, f"hook '{hook}' not found in callbacks {self._callbacks}"
        for logger in self._callbacks[hook]:
            logger['callback'](*args, **kwargs)

def register_action(self, hook, name='', callback=None):
    """
        Register a new action to a callback hook

        Args:
            hook        The callback hook name to register the action to
            name        The name of the action for later reference
            callback    The callback to fire
        """
    assert hook in self._callbacks, f"hook '{hook}' not found in callbacks {self._callbacks}"
    assert callable(callback), f"callback '{callback}' is not callable"
    self._callbacks[hook].append({'name': name, 'callback': callback})

def methods(instance):
    return [f for f in dir(instance) if callable(getattr(instance, f)) and (not f.startswith('__'))]

def is_parallel(model):
    return type(model) in (nn.parallel.DataParallel, nn.parallel.DistributedDataParallel)

def initialize_weights(model):
    for m in model.modules():
        t = type(m)
        if t is nn.Conv2d:
            pass
        elif t is nn.BatchNorm2d:
            m.eps = 0.001
            m.momentum = 0.03
        elif t in [nn.Hardswish, nn.LeakyReLU, nn.ReLU, nn.ReLU6, nn.SiLU]:
            m.inplace = True

def copy_attr(a, b, include=(), exclude=()):
    for k, v in b.__dict__.items():
        if len(include) and k not in include or k.startswith('_') or k in exclude:
            continue
        else:
            setattr(a, k, v)

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

def fuse(self):
    LOGGER.info('Fusing layers... ')
    for m in self.model.modules():
        if isinstance(m, (Conv, DWConv)) and hasattr(m, 'bn'):
            m.conv = fuse_conv_and_bn(m.conv, m.bn)
            delattr(m, 'bn')
            m.forward = m.forward_fuse
    self.info()
    return self

def attempt_load(weights, map_location=None, inplace=True, fuse=True):
    from models.yolo import Detect, Model
    model = Ensemble()
    for w in weights if isinstance(weights, list) else [weights]:
        ckpt = torch.load(attempt_download(w), map_location=map_location)
        if fuse:
            model.append(ckpt['ema' if ckpt.get('ema') else 'model'].float().fuse().eval())
        else:
            model.append(ckpt['ema' if ckpt.get('ema') else 'model'].float().eval())
    for m in model.modules():
        if type(m) in [nn.Hardswish, nn.LeakyReLU, nn.ReLU, nn.ReLU6, nn.SiLU, Detect, Model]:
            m.inplace = inplace
            if type(m) is Detect:
                if not isinstance(m.anchor_grid, list):
                    delattr(m, 'anchor_grid')
                    setattr(m, 'anchor_grid', [torch.zeros(1)] * m.nl)
        elif type(m) is Conv:
            m._non_persistent_buffers_set = set()
    if len(model) == 1:
        return model[-1]
    else:
        print(f'Ensemble created with {weights}\n')
        for k in ['names']:
            setattr(model, k, getattr(model[-1], k))
        model.stride = model[torch.argmax(torch.tensor([m.stride.max() for m in model])).int()].stride
        return model

class DetectMultiBackend(nn.Module):

    def __init__(self, weights='yolov5s.pt', device=None, dnn=False, data=None):
        from models.experimental import attempt_download, attempt_load
        super().__init__()
        w = str(weights[0] if isinstance(weights, list) else weights)
        suffix = Path(w).suffix.lower()
        suffixes = ['.pt', '.torchscript', '.onnx', '.engine', '.tflite', '.pb', '', '.mlmodel', '.xml']
        check_suffix(w, suffixes)
        pt, jit, onnx, engine, tflite, pb, saved_model, coreml, xml = (suffix == x for x in suffixes)
        stride, names = (64, [f'class{i}' for i in range(1000)])
        w = attempt_download(w)
        if data:
            with open(data, errors='ignore') as f:
                names = yaml.safe_load(f)['names']
        if pt:
            model = attempt_load(weights if isinstance(weights, list) else w, map_location=device)
            stride = int(model.stride.max())
            names = model.module.names if hasattr(model, 'module') else model.names
            self.model = model
        elif jit:
            LOGGER.info(f'Loading {w} for TorchScript inference...')
            extra_files = {'config.txt': ''}
            model = torch.jit.load(w, _extra_files=extra_files)
            if extra_files['config.txt']:
                d = json.loads(extra_files['config.txt'])
                stride, names = (int(d['stride']), d['names'])
        elif dnn:
            LOGGER.info(f'Loading {w} for ONNX OpenCV DNN inference...')
            check_requirements(('opencv-python>=4.5.4',))
            net = cv2.dnn.readNetFromONNX(w)
        elif onnx:
            LOGGER.info(f'Loading {w} for ONNX Runtime inference...')
            cuda = torch.cuda.is_available()
            check_requirements(('onnx', 'onnxruntime-gpu' if cuda else 'onnxruntime'))
            import onnxruntime
            providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if cuda else ['CPUExecutionProvider']
            session = onnxruntime.InferenceSession(w, providers=providers)
        elif xml:
            LOGGER.info(f'Loading {w} for OpenVINO inference...')
            check_requirements(('openvino-dev',))
            import openvino.inference_engine as ie
            core = ie.IECore()
            network = core.read_network(model=w, weights=Path(w).with_suffix('.bin'))
            executable_network = core.load_network(network, device_name='CPU', num_requests=1)
        elif engine:
            LOGGER.info(f'Loading {w} for TensorRT inference...')
            import tensorrt as trt
            check_version(trt.__version__, '7.0.0', hard=True)
            Binding = namedtuple('Binding', ('name', 'dtype', 'shape', 'data', 'ptr'))
            logger = trt.Logger(trt.Logger.INFO)
            with open(w, 'rb') as f, trt.Runtime(logger) as runtime:
                model = runtime.deserialize_cuda_engine(f.read())
            bindings = OrderedDict()
            for index in range(model.num_bindings):
                name = model.get_binding_name(index)
                dtype = trt.nptype(model.get_binding_dtype(index))
                shape = tuple(model.get_binding_shape(index))
                data = torch.from_numpy(np.empty(shape, dtype=np.dtype(dtype))).to(device)
                bindings[name] = Binding(name, dtype, shape, data, int(data.data_ptr()))
            binding_addrs = OrderedDict(((n, d.ptr) for n, d in bindings.items()))
            context = model.create_execution_context()
            batch_size = bindings['images'].shape[0]
        elif coreml:
            LOGGER.info(f'Loading {w} for CoreML inference...')
            import coremltools as ct
            model = ct.models.MLModel(w)
        elif saved_model:
            LOGGER.info(f'Loading {w} for TensorFlow SavedModel inference...')
            import tensorflow as tf
            model = tf.keras.models.load_model(w)
        elif pb:
            LOGGER.info(f'Loading {w} for TensorFlow GraphDef inference...')
            import tensorflow as tf

            def wrap_frozen_graph(gd, inputs, outputs):
                x = tf.compat.v1.wrap_function(lambda: tf.compat.v1.import_graph_def(gd, name=''), [])
                return x.prune(tf.nest.map_structure(x.graph.as_graph_element, inputs), tf.nest.map_structure(x.graph.as_graph_element, outputs))
            graph_def = tf.Graph().as_graph_def()
            graph_def.ParseFromString(open(w, 'rb').read())
            frozen_func = wrap_frozen_graph(gd=graph_def, inputs='x:0', outputs='Identity:0')
        elif tflite:
            if 'edgetpu' in w.lower():
                LOGGER.info(f'Loading {w} for TensorFlow Lite Edge TPU inference...')
                import tflite_runtime.interpreter as tfli
                delegate = {'Linux': 'libedgetpu.so.1', 'Darwin': 'libedgetpu.1.dylib', 'Windows': 'edgetpu.dll'}[platform.system()]
                interpreter = tfli.Interpreter(model_path=w, experimental_delegates=[tfli.load_delegate(delegate)])
            else:
                LOGGER.info(f'Loading {w} for TensorFlow Lite inference...')
                import tensorflow as tf
                interpreter = tf.lite.Interpreter(model_path=w)
            interpreter.allocate_tensors()
            input_details = interpreter.get_input_details()
            output_details = interpreter.get_output_details()
        self.__dict__.update(locals())

    def forward(self, im, augment=False, visualize=False, val=False):
        b, ch, h, w = im.shape
        if self.pt or self.jit:
            y = self.model(im) if self.jit else self.model(im, augment=augment, visualize=visualize)
            return y if val else y[0]
        elif self.dnn:
            im = im.cpu().numpy()
            self.net.setInput(im)
            y = self.net.forward()
        elif self.onnx:
            im = im.cpu().numpy()
            y = self.session.run([self.session.get_outputs()[0].name], {self.session.get_inputs()[0].name: im})[0]
        elif self.xml:
            im = im.cpu().numpy()
            desc = self.ie.TensorDesc(precision='FP32', dims=im.shape, layout='NCHW')
            request = self.executable_network.requests[0]
            request.set_blob(blob_name='images', blob=self.ie.Blob(desc, im))
            request.infer()
            y = request.output_blobs['output'].buffer
        elif self.engine:
            assert im.shape == self.bindings['images'].shape, (im.shape, self.bindings['images'].shape)
            self.binding_addrs['images'] = int(im.data_ptr())
            self.context.execute_v2(list(self.binding_addrs.values()))
            y = self.bindings['output'].data
        elif self.coreml:
            im = im.permute(0, 2, 3, 1).cpu().numpy()
            im = Image.fromarray((im[0] * 255).astype('uint8'))
            y = self.model.predict({'image': im})
            if 'confidence' in y:
                box = xywh2xyxy(y['coordinates'] * [[w, h, w, h]])
                conf, cls = (y['confidence'].max(1), y['confidence'].argmax(1).astype(np.float))
                y = np.concatenate((box, conf.reshape(-1, 1), cls.reshape(-1, 1)), 1)
            else:
                y = y[list(y)[-1]]
        else:
            im = im.permute(0, 2, 3, 1).cpu().numpy()
            if self.saved_model:
                y = self.model(im, training=False).numpy()
            elif self.pb:
                y = self.frozen_func(x=self.tf.constant(im)).numpy()
            elif self.tflite:
                input, output = (self.input_details[0], self.output_details[0])
                int8 = input['dtype'] == np.uint8
                if int8:
                    scale, zero_point = input['quantization']
                    im = (im / scale + zero_point).astype(np.uint8)
                self.interpreter.set_tensor(input['index'], im)
                self.interpreter.invoke()
                y = self.interpreter.get_tensor(output['index'])
                if int8:
                    scale, zero_point = output['quantization']
                    y = (y.astype(np.float32) - zero_point) * scale
            y[..., 0] *= w
            y[..., 1] *= h
            y[..., 2] *= w
            y[..., 3] *= h
        y = torch.tensor(y) if isinstance(y, np.ndarray) else y
        return (y, []) if val else y

    def warmup(self, imgsz=(1, 3, 640, 640), half=False):
        if self.pt or self.jit or self.onnx or self.engine:
            if isinstance(self.device, torch.device) and self.device.type != 'cpu':
                im = torch.zeros(*imgsz).to(self.device).type(torch.half if half else torch.float)
                self.forward(im)

def __init__(self, weights='yolov5s.pt', device=None, dnn=False, data=None):
    from models.experimental import attempt_download, attempt_load
    super().__init__()
    w = str(weights[0] if isinstance(weights, list) else weights)
    suffix = Path(w).suffix.lower()
    suffixes = ['.pt', '.torchscript', '.onnx', '.engine', '.tflite', '.pb', '', '.mlmodel', '.xml']
    check_suffix(w, suffixes)
    pt, jit, onnx, engine, tflite, pb, saved_model, coreml, xml = (suffix == x for x in suffixes)
    stride, names = (64, [f'class{i}' for i in range(1000)])
    w = attempt_download(w)
    if data:
        with open(data, errors='ignore') as f:
            names = yaml.safe_load(f)['names']
    if pt:
        model = attempt_load(weights if isinstance(weights, list) else w, map_location=device)
        stride = int(model.stride.max())
        names = model.module.names if hasattr(model, 'module') else model.names
        self.model = model
    elif jit:
        LOGGER.info(f'Loading {w} for TorchScript inference...')
        extra_files = {'config.txt': ''}
        model = torch.jit.load(w, _extra_files=extra_files)
        if extra_files['config.txt']:
            d = json.loads(extra_files['config.txt'])
            stride, names = (int(d['stride']), d['names'])
    elif dnn:
        LOGGER.info(f'Loading {w} for ONNX OpenCV DNN inference...')
        check_requirements(('opencv-python>=4.5.4',))
        net = cv2.dnn.readNetFromONNX(w)
    elif onnx:
        LOGGER.info(f'Loading {w} for ONNX Runtime inference...')
        cuda = torch.cuda.is_available()
        check_requirements(('onnx', 'onnxruntime-gpu' if cuda else 'onnxruntime'))
        import onnxruntime
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if cuda else ['CPUExecutionProvider']
        session = onnxruntime.InferenceSession(w, providers=providers)
    elif xml:
        LOGGER.info(f'Loading {w} for OpenVINO inference...')
        check_requirements(('openvino-dev',))
        import openvino.inference_engine as ie
        core = ie.IECore()
        network = core.read_network(model=w, weights=Path(w).with_suffix('.bin'))
        executable_network = core.load_network(network, device_name='CPU', num_requests=1)
    elif engine:
        LOGGER.info(f'Loading {w} for TensorRT inference...')
        import tensorrt as trt
        check_version(trt.__version__, '7.0.0', hard=True)
        Binding = namedtuple('Binding', ('name', 'dtype', 'shape', 'data', 'ptr'))
        logger = trt.Logger(trt.Logger.INFO)
        with open(w, 'rb') as f, trt.Runtime(logger) as runtime:
            model = runtime.deserialize_cuda_engine(f.read())
        bindings = OrderedDict()
        for index in range(model.num_bindings):
            name = model.get_binding_name(index)
            dtype = trt.nptype(model.get_binding_dtype(index))
            shape = tuple(model.get_binding_shape(index))
            data = torch.from_numpy(np.empty(shape, dtype=np.dtype(dtype))).to(device)
            bindings[name] = Binding(name, dtype, shape, data, int(data.data_ptr()))
        binding_addrs = OrderedDict(((n, d.ptr) for n, d in bindings.items()))
        context = model.create_execution_context()
        batch_size = bindings['images'].shape[0]
    elif coreml:
        LOGGER.info(f'Loading {w} for CoreML inference...')
        import coremltools as ct
        model = ct.models.MLModel(w)
    elif saved_model:
        LOGGER.info(f'Loading {w} for TensorFlow SavedModel inference...')
        import tensorflow as tf
        model = tf.keras.models.load_model(w)
    elif pb:
        LOGGER.info(f'Loading {w} for TensorFlow GraphDef inference...')
        import tensorflow as tf

        def wrap_frozen_graph(gd, inputs, outputs):
            x = tf.compat.v1.wrap_function(lambda: tf.compat.v1.import_graph_def(gd, name=''), [])
            return x.prune(tf.nest.map_structure(x.graph.as_graph_element, inputs), tf.nest.map_structure(x.graph.as_graph_element, outputs))
        graph_def = tf.Graph().as_graph_def()
        graph_def.ParseFromString(open(w, 'rb').read())
        frozen_func = wrap_frozen_graph(gd=graph_def, inputs='x:0', outputs='Identity:0')
    elif tflite:
        if 'edgetpu' in w.lower():
            LOGGER.info(f'Loading {w} for TensorFlow Lite Edge TPU inference...')
            import tflite_runtime.interpreter as tfli
            delegate = {'Linux': 'libedgetpu.so.1', 'Darwin': 'libedgetpu.1.dylib', 'Windows': 'edgetpu.dll'}[platform.system()]
            interpreter = tfli.Interpreter(model_path=w, experimental_delegates=[tfli.load_delegate(delegate)])
        else:
            LOGGER.info(f'Loading {w} for TensorFlow Lite inference...')
            import tensorflow as tf
            interpreter = tf.lite.Interpreter(model_path=w)
        interpreter.allocate_tensors()
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
    self.__dict__.update(locals())

def warmup(self, imgsz=(1, 3, 640, 640), half=False):
    if self.pt or self.jit or self.onnx or self.engine:
        if isinstance(self.device, torch.device) and self.device.type != 'cpu':
            im = torch.zeros(*imgsz).to(self.device).type(torch.half if half else torch.float)
            self.forward(im)

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

def pandas(self):
    new = copy(self)
    ca = ('xmin', 'ymin', 'xmax', 'ymax', 'confidence', 'class', 'name')
    cb = ('xcenter', 'ycenter', 'width', 'height', 'confidence', 'class', 'name')
    for k, c in zip(['xyxy', 'xyxyn', 'xywh', 'xywhn'], [ca, ca, cb, cb]):
        a = [[x[:5] + [int(x[5]), self.names[int(x[5])]] for x in x.tolist()] for x in getattr(self, k)]
        setattr(new, k, [pd.DataFrame(x, columns=c) for x in a])
    return new

