# Cluster 36

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

def wrap_frozen_graph(gd, inputs, outputs):
    x = tf.compat.v1.wrap_function(lambda: tf.compat.v1.import_graph_def(gd, name=''), [])
    return x.prune(tf.nest.map_structure(x.graph.as_graph_element, inputs), tf.nest.map_structure(x.graph.as_graph_element, outputs))

