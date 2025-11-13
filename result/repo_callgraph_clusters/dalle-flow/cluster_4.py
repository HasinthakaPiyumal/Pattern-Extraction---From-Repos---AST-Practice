# Cluster 4

class ClipSegmentation(Executor):
    model = None
    transformation = None

    def __init__(self, cache_path: str | Path, weights_url: str=WEIGHT_URL_DEFAULT, **kwargs):
        super().__init__(**kwargs)
        if '~' in str(Path(cache_path)):
            cache_path = Path(cache_path).expanduser()
        weights_path = Path('/')
        if Path(cache_path).is_dir():
            weights_path = Path(cache_path) / WEIGHT_ZIP_FILE_NAME
        else:
            weights_path = Path.home() / WEIGHT_ZIP_FILE_NAME
        if not weights_path.is_file():
            response = urlopen(weights_url)
            weights_bytes = response.read()
            with open(weights_path, 'wb') as w_f:
                w_f.write(weights_bytes)
        shutil.unpack_archive(weights_path, Path(cache_path).resolve())
        model = CLIPDensePredT(version='ViT-B/16', reduce_dim=64)
        model.eval()
        model.load_state_dict(torch.load(f'{cache_path}/{WEIGHT_FOLDER_NAME}/rd64-uni.pth', map_location=torch.device('cuda')), strict=False)
        self.model = model
        self.transformation = self.default_transformation()

    @staticmethod
    def document_to_pil(doc: Document) -> Image:
        uri_data = urlopen(doc.uri)
        return Image.open(BytesIO(uri_data.read()))

    @staticmethod
    def default_transformation() -> transforms.Compose:
        return transforms.Compose([transforms.ToTensor(), transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]), transforms.Resize((512, 512))])

    @requests(on='/segment')
    def segment(self, docs: DocumentArray, parameters: Dict, **kwargs):
        """
        Parameters for CLIP segmentation:

        Document.text: Prompt for segmentation.
        @parameters.adaptive_thresh_block_size: Adaptive thresholding blocksize,
          as integer.
        @parameters.adaptive_thresh_c: Adaptive thresholding c value, as float.
        @parameters.binary_thresh_strength: Strength of binary thresholding,
          lower = more promiscuous.
        @parameters.thresholding_type: Type of thresholding, default binary
          method.
        """
        request_time = time.time()
        invert = parameters.get('invert', False)
        try:
            thresholding_type = parameters.get('thresholding_type', THRESHOLDING_METHODS.BINARY.value)
            thresholding_type = THRESHOLDING_METHODS(thresholding_type)
        except ValueError:
            thresholding_type = THRESHOLDING_METHODS.BINARY
        adaptive_thresh_block_size = None
        adaptive_thresh_c = None
        binary_thresh_strength = None
        if thresholding_type == THRESHOLDING_METHODS.BINARY:
            binary_thresh_strength = parameters.get('binary_thresh_strength', THRESHOLD_BINARY_DEFAULT_STRENGTH_VALUE)
            try:
                binary_thresh_strength = int(binary_thresh_strength)
            except Exception:
                pass
            if not isinstance(binary_thresh_strength, int):
                binary_thresh_strength = THRESHOLD_BINARY_DEFAULT_STRENGTH_VALUE
        if thresholding_type == THRESHOLDING_METHODS.ADAPTIVE_MEAN or thresholding_type == THRESHOLDING_METHODS.ADAPTIVE_GAUSSIAN:
            adaptive_thresh_block_size = parameters.get('adaptive_thresh_block_size', THRESHOLD_ADAPTIVE_DEFAULT_BLOCK_SIZE)
            try:
                adaptive_thresh_block_size = int(adaptive_thresh_block_size)
            except Exception:
                pass
            if not isinstance(adaptive_thresh_block_size, int):
                adaptive_thresh_block_size = THRESHOLD_ADAPTIVE_DEFAULT_BLOCK_SIZE
            if adaptive_thresh_block_size % 2 != 1:
                adaptive_thresh_block_size -= 1
            adaptive_thresh_c = parameters.get('adaptive_thresh_c', THRESHOLD_ADAPTIVE_DEFAULT_C)
            if not isinstance(adaptive_thresh_c, float):
                adaptive_thresh_c = THRESHOLD_ADAPTIVE_DEFAULT_C
        with torch.no_grad():
            for doc in docs:
                prompts = [doc.text]
                image_in = self.document_to_pil(doc)
                image_in = image_in.convert('RGB')
                image_unsqueezed = self.transformation(image_in).unsqueeze(0)
                mask_preds = self.model(image_unsqueezed.repeat(1, 1, 1, 1), prompts)[0]
                sigmoidy = torch.sigmoid(mask_preds[0][0]).cpu().detach().numpy()
                mask_as_arr = (sigmoidy * 255 / np.max(sigmoidy)).astype('uint8')
                image_mask_init = Image.fromarray(mask_as_arr)
                mask_cv = cv2.cvtColor(np.array(image_mask_init), cv2.COLOR_RGB2BGR)
                gray_image = cv2.cvtColor(mask_cv, cv2.COLOR_BGR2GRAY)
                bw_image = gray_image
                if thresholding_type == THRESHOLDING_METHODS.BINARY:
                    _, bw_image = cv2.threshold(gray_image, binary_thresh_strength, 255, cv2.THRESH_BINARY)
                if thresholding_type == THRESHOLDING_METHODS.ADAPTIVE_MEAN or thresholding_type == THRESHOLDING_METHODS.ADAPTIVE_GAUSSIAN:
                    a_method = cv2.ADAPTIVE_THRESH_MEAN_C
                    if thresholding_type == THRESHOLDING_METHODS.ADAPTIVE_GAUSSIAN:
                        a_method = cv2.ADAPTIVE_THRESH_GAUSSIAN_C
                    bw_image = cv2.adaptiveThreshold(gray_image, 255, a_method, cv2.THRESH_BINARY, adaptive_thresh_block_size, adaptive_thresh_c)
                cv2.cvtColor(bw_image, cv2.COLOR_BGR2RGB)
                image_mask = Image.fromarray(bw_image).convert('L').resize(image_in.size, Image.NEAREST)
                if not invert:
                    image_mask = ImageOps.invert(image_mask)
                image_rgba = image_in.copy()
                image_rgba.putalpha(image_mask)
                buffered = BytesIO()
                image_rgba.save(buffered, format='PNG')
                _d = Document(blob=buffered.getvalue(), mime_type='image/png', tags={'request': {'api': 'segment', 'adaptive_thresh_block_size': adaptive_thresh_block_size, 'adaptive_thresh_c': adaptive_thresh_c, 'binary_thresh_strength': binary_thresh_strength, 'invert': invert, 'thresholding_type': thresholding_type.value}, 'text': doc.text, 'generator': 'clipseg', 'request_time': request_time, 'created_time': time.time()}).convert_blob_to_datauri()
                _d.text = doc.text
                doc.matches.append(_d)

def __init__(self, cache_path: str | Path, weights_url: str=WEIGHT_URL_DEFAULT, **kwargs):
    super().__init__(**kwargs)
    if '~' in str(Path(cache_path)):
        cache_path = Path(cache_path).expanduser()
    weights_path = Path('/')
    if Path(cache_path).is_dir():
        weights_path = Path(cache_path) / WEIGHT_ZIP_FILE_NAME
    else:
        weights_path = Path.home() / WEIGHT_ZIP_FILE_NAME
    if not weights_path.is_file():
        response = urlopen(weights_url)
        weights_bytes = response.read()
        with open(weights_path, 'wb') as w_f:
            w_f.write(weights_bytes)
    shutil.unpack_archive(weights_path, Path(cache_path).resolve())
    model = CLIPDensePredT(version='ViT-B/16', reduce_dim=64)
    model.eval()
    model.load_state_dict(torch.load(f'{cache_path}/{WEIGHT_FOLDER_NAME}/rd64-uni.pth', map_location=torch.device('cuda')), strict=False)
    self.model = model
    self.transformation = self.default_transformation()

class SwinIRUpscaler(Executor):

    def __init__(self, swinir_path: str, **kwargs):
        super().__init__(**kwargs)
        self.swinir_path = swinir_path
        self.input_path = f'{swinir_path}/input/'
        self.output_path = f'{swinir_path}/results/swinir_real_sr_x4_large/'
        self.failover = 0
        self.swin_ir_kwargs = {'task': 'real_sr', 'scale': 4, 'model_path': f'{self.swinir_path}/model_zoo/swinir/003_realSR_BSRGAN_DFOWMFC_s64w8_SwinIR-L_x4_GAN.pth', 'save_dir': self.output_path}
        args_str = ';'.join((f'--{k};{str(v)}' for k, v in self.swin_ir_kwargs.items())) + ';--large_model'
        self.swin_ir_args = args_str.split(';')
        self.swin_ir_model = get_model(self.swin_ir_args[:])

    def _upscale(self, d: Document):
        self.logger.info(f'upscaling [{d.text}]...')
        input_path = os.path.join(self.input_path, f'{d.id}/')
        Path(input_path).mkdir(parents=True, exist_ok=True)
        Path(self.output_path).mkdir(parents=True, exist_ok=True)
        d.save_uri_to_file(os.path.join(input_path, f'{d.id}.png'))
        swin_ir_main([*self.swin_ir_args, '--folder_lq', input_path], self.swin_ir_model)
        d.uri = os.path.join(self.output_path, f'{d.id}_SwinIR.png')
        d.convert_uri_to_datauri()
        d.tags['upscaled'] = True
        d.tags.update({**self.swin_ir_kwargs, 'folder_lq': input_path})
        self.logger.info('cleaning...')
        shutil.rmtree(input_path, ignore_errors=True)
        for f in glob.glob(f'{self.output_path}/{d.id}*.png'):
            if os.path.isfile(f):
                os.remove(f)
        self.logger.info('done!')
        torch.cuda.empty_cache()

    @requests(on='/upscale')
    async def upscale(self, docs: DocumentArray, **kwargs):
        for d in docs.find({'$and': [{'tags__upscaled': {'$exists': False}}, {'tags__generator': {'$exists': True}}]}):
            self._upscale(d)
            d.blob = None
            d.embedding = None

def __init__(self, swinir_path: str, **kwargs):
    super().__init__(**kwargs)
    self.swinir_path = swinir_path
    self.input_path = f'{swinir_path}/input/'
    self.output_path = f'{swinir_path}/results/swinir_real_sr_x4_large/'
    self.failover = 0
    self.swin_ir_kwargs = {'task': 'real_sr', 'scale': 4, 'model_path': f'{self.swinir_path}/model_zoo/swinir/003_realSR_BSRGAN_DFOWMFC_s64w8_SwinIR-L_x4_GAN.pth', 'save_dir': self.output_path}
    args_str = ';'.join((f'--{k};{str(v)}' for k, v in self.swin_ir_kwargs.items())) + ';--large_model'
    self.swin_ir_args = args_str.split(';')
    self.swin_ir_model = get_model(self.swin_ir_args[:])

class RealESRGANUpscaler(Executor):
    """
    This is a module that provides access to the RealESRGAN models and API which
    upscale images and video. It also supports using GFPGAN to fix faces within
    photographic images.

    The module source code is available at:
    https://github.com/xinntao/Real-ESRGAN

    All models that are included in the config.yml file will be available for
    upscaling.
    """
    cache_path: Union[str, Path] = ''
    gfpgan_weights_path: Union[str, Path] = ''
    models_to_load: List[str] = []
    pre_pad = 10
    tile = 0
    tile_pad = 10
    use_half = True

    def __init__(self, cache_path: Union[str, Path], models_to_load: List[str], pre_pad: int=10, tile: int=0, tile_pad: int=10, use_half: bool=True, **kwargs):
        """
        Args:

        cache_path: path to the cache directory.
        models_to_load: list[str], list of the models to load into memory.

        tile (int): As too large images result in the out of GPU memory issue,
          so this tile option will first crop input images into tiles, and
          then process each of them. Finally, they will be merged into one
          image.
          0 denotes for do not use tile. Default: 0.
        tile_pad (int): The pad size for each tile, to remove border artifacts.
          Default: 10.
        pre_pad (int): Pad the input images to avoid border artifacts.
          Default: 10.
        half (float): Whether to use half precision during inference.
          Default: True.
        """
        super().__init__(**kwargs)
        if '~' in str(Path(cache_path)):
            cache_path = Path(cache_path).expanduser()
        gfpgan_weights_path = Path.home() / str(GFPGAN_MODEL_NAME + '.pth')
        if Path(cache_path).is_dir():
            gfpgan_weights_path = Path(cache_path) / str(GFPGAN_MODEL_NAME + '.pth')
        if not gfpgan_weights_path.is_file():
            gfpgan_weights_dir = Path.home()
            gfpgan_weights_path = Path.home() / str(GFPGAN_MODEL_NAME + '.pth')
            gfpgan_weights_path = load_file_from_url(url=GFPGAN_MODEL_URL, model_dir=str(gfpgan_weights_dir.absolute()), progress=True, file_name=None)
        self.cache_path = cache_path
        self.gfpgan_weights_path = gfpgan_weights_path
        self.models_to_load = models_to_load
        self.pre_pad = pre_pad
        self.tile = tile
        self.tile_pad = tile_pad
        self.use_half = use_half

    def load_model(self) -> Dict[str, Any]:
        """
        return a dictionary organized as:
        {
        model_name: {
            'name': str,
            'netscale': int, (scaling strength eg 4=4x)
            'model': initialized RealESRGAN model,
            'model_face_fix': initialized GFPGAN model, [optional, non-anime only]
        }
        """

        def gfpgan_wrapper(model_upscaler: Any, outscale: int):
            return GFPGANer(model_path=str(self.gfpgan_weights_path.absolute()) if isinstance(self.gfpgan_weights_path, Path) else self.gfpgan_weights_path, upscale=outscale, arch='clean', channel_multiplier=2, bg_upsampler=model_upscaler)
        resrgan_models: Dict[str, Any] = {}
        for model_name in self.models_to_load:
            model_type = None
            try:
                model_type = RESRGAN_MODELS(model_name)
            except ValueError:
                raise ValueError(f"Unknown model name '{model_name}', " + 'please ensure all models in models_to_load configuration ' + 'option are valid')
            model = None
            netscale = 4
            file_url = []
            if model_type == RESRGAN_MODELS.RealESRGAN_x4plus:
                model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
                netscale = 4
                file_url = ['https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth']
            if model_type == RESRGAN_MODELS.RealESRNet_x4plus:
                model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
                netscale = 4
                file_url = ['https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.1/RealESRNet_x4plus.pth']
            if model_type == RESRGAN_MODELS.RealESRGAN_x4plus_anime_6B:
                model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=6, num_grow_ch=32, scale=4)
                netscale = 4
                file_url = ['https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth']
            if model_type == RESRGAN_MODELS.RealESRGAN_x2plus:
                model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=2)
                netscale = 2
                file_url = ['https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth']
            if model_type == RESRGAN_MODELS.RealESR_animevideov3:
                model = SRVGGNetCompact(num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=16, upscale=4, act_type='prelu')
                netscale = 4
                file_url = ['https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-animevideov3.pth']
            if model_type == RESRGAN_MODELS.RealESR_general_x4v3:
                model = SRVGGNetCompact(num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=32, upscale=4, act_type='prelu')
                netscale = 4
                file_url = ['https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-wdn-x4v3.pth', 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth']
            weights_path = Path.home() / str(model_name + '.pth')
            if Path(self.cache_path).is_dir():
                weights_path = Path(self.cache_path) / str(model_name + '.pth')
            if not weights_path.is_file():
                weights_dir = Path.home()
                weights_path = Path.home() / str(model_name + '.pth')
                for url in file_url:
                    weights_path = load_file_from_url(url=url, model_dir=str(weights_dir.absolute()), progress=True, file_name=None)
            upsampler = RealESRGANer(scale=netscale, model_path=str(weights_path.absolute()) if isinstance(weights_path, Path) else weights_path, model=model, tile=self.tile, tile_pad=self.tile_pad, pre_pad=self.pre_pad, half=self.use_half)
            model_face_fix = None
            if model_type != RESRGAN_MODELS.RealESRGAN_x4plus_anime_6B:
                model_face_fix = gfpgan_wrapper(upsampler, netscale)
            resrgan_models[model_name] = {'name': model_name, 'netscale': netscale, 'model': upsampler, 'model_face_fix': model_face_fix}
        return resrgan_models

    def document_to_pil(self, doc):
        uri_data = urlopen(doc.uri)
        return Image.open(BytesIO(uri_data.read()))

    @requests(on='/realesrgan')
    def realesrgan(self, docs: DocumentArray, parameters: Dict, **kwargs):
        """
        Upscale using RealESRGAN, with or without face fix.

        @parameters.face_enhance: Whether or not to attempt to fix a human face.
          Not applicable to anime model. bool.
        @parameters.model_name: Which model to use, see RESRGAN_MODELS enum.
          str.
        """
        request_time = time.time()
        resrgan_models = self.load_model()
        face_enhance = parameters.get('face_enhance', False)
        model_name = parameters.get('model_name', list(resrgan_models.values())[0]['name'])
        for doc in docs:
            img = self.document_to_pil(doc)
            img_arr = np.asarray(img)
            img_arr = cv2.cvtColor(img_arr, cv2.COLOR_RGB2BGR)
            model_dict = resrgan_models.get(model_name, None)
            if model_dict is None:
                raise ValueError(f'Unknown RealESRGAN upscaler specified: {model_name}')
            upsampler = model_dict.get('model', None)
            face_enhancer = model_dict.get('model_face_fix', None)
            if face_enhance is True and face_enhancer is not None:
                _, _, output = face_enhancer.enhance(img_arr, has_aligned=False, only_center_face=False, paste_back=True)
            else:
                output, _ = upsampler.enhance(img_arr, model_dict['netscale'])
            output = cv2.cvtColor(output, cv2.COLOR_BGR2RGB)
            image_big = Image.fromarray(output)
            buffered = BytesIO()
            image_big.save(buffered, format='PNG')
            _d = Document(blob=buffered.getvalue(), mime_type='image/png', tags={'request': {'api': 'realesrgan', 'face_enhance': face_enhance, 'model_name': model_name}, 'text': doc.text, 'generator': 'realesrgan', 'request_time': request_time, 'created_time': time.time()}).convert_blob_to_datauri()
            _d.text = doc.text
            doc.matches.append(_d)
        torch.cuda.empty_cache()

def __init__(self, cache_path: Union[str, Path], models_to_load: List[str], pre_pad: int=10, tile: int=0, tile_pad: int=10, use_half: bool=True, **kwargs):
    """
        Args:

        cache_path: path to the cache directory.
        models_to_load: list[str], list of the models to load into memory.

        tile (int): As too large images result in the out of GPU memory issue,
          so this tile option will first crop input images into tiles, and
          then process each of them. Finally, they will be merged into one
          image.
          0 denotes for do not use tile. Default: 0.
        tile_pad (int): The pad size for each tile, to remove border artifacts.
          Default: 10.
        pre_pad (int): Pad the input images to avoid border artifacts.
          Default: 10.
        half (float): Whether to use half precision during inference.
          Default: True.
        """
    super().__init__(**kwargs)
    if '~' in str(Path(cache_path)):
        cache_path = Path(cache_path).expanduser()
    gfpgan_weights_path = Path.home() / str(GFPGAN_MODEL_NAME + '.pth')
    if Path(cache_path).is_dir():
        gfpgan_weights_path = Path(cache_path) / str(GFPGAN_MODEL_NAME + '.pth')
    if not gfpgan_weights_path.is_file():
        gfpgan_weights_dir = Path.home()
        gfpgan_weights_path = Path.home() / str(GFPGAN_MODEL_NAME + '.pth')
        gfpgan_weights_path = load_file_from_url(url=GFPGAN_MODEL_URL, model_dir=str(gfpgan_weights_dir.absolute()), progress=True, file_name=None)
    self.cache_path = cache_path
    self.gfpgan_weights_path = gfpgan_weights_path
    self.models_to_load = models_to_load
    self.pre_pad = pre_pad
    self.tile = tile
    self.tile_pad = tile_pad
    self.use_half = use_half

def gfpgan_wrapper(model_upscaler: Any, outscale: int):
    return GFPGANer(model_path=str(self.gfpgan_weights_path.absolute()) if isinstance(self.gfpgan_weights_path, Path) else self.gfpgan_weights_path, upscale=outscale, arch='clean', channel_multiplier=2, bg_upsampler=model_upscaler)

def load_model(self) -> Dict[str, Any]:
    """
        return a dictionary organized as:
        {
        model_name: {
            'name': str,
            'netscale': int, (scaling strength eg 4=4x)
            'model': initialized RealESRGAN model,
            'model_face_fix': initialized GFPGAN model, [optional, non-anime only]
        }
        """

    def gfpgan_wrapper(model_upscaler: Any, outscale: int):
        return GFPGANer(model_path=str(self.gfpgan_weights_path.absolute()) if isinstance(self.gfpgan_weights_path, Path) else self.gfpgan_weights_path, upscale=outscale, arch='clean', channel_multiplier=2, bg_upsampler=model_upscaler)
    resrgan_models: Dict[str, Any] = {}
    for model_name in self.models_to_load:
        model_type = None
        try:
            model_type = RESRGAN_MODELS(model_name)
        except ValueError:
            raise ValueError(f"Unknown model name '{model_name}', " + 'please ensure all models in models_to_load configuration ' + 'option are valid')
        model = None
        netscale = 4
        file_url = []
        if model_type == RESRGAN_MODELS.RealESRGAN_x4plus:
            model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
            netscale = 4
            file_url = ['https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth']
        if model_type == RESRGAN_MODELS.RealESRNet_x4plus:
            model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
            netscale = 4
            file_url = ['https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.1/RealESRNet_x4plus.pth']
        if model_type == RESRGAN_MODELS.RealESRGAN_x4plus_anime_6B:
            model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=6, num_grow_ch=32, scale=4)
            netscale = 4
            file_url = ['https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth']
        if model_type == RESRGAN_MODELS.RealESRGAN_x2plus:
            model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=2)
            netscale = 2
            file_url = ['https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth']
        if model_type == RESRGAN_MODELS.RealESR_animevideov3:
            model = SRVGGNetCompact(num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=16, upscale=4, act_type='prelu')
            netscale = 4
            file_url = ['https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-animevideov3.pth']
        if model_type == RESRGAN_MODELS.RealESR_general_x4v3:
            model = SRVGGNetCompact(num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=32, upscale=4, act_type='prelu')
            netscale = 4
            file_url = ['https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-wdn-x4v3.pth', 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth']
        weights_path = Path.home() / str(model_name + '.pth')
        if Path(self.cache_path).is_dir():
            weights_path = Path(self.cache_path) / str(model_name + '.pth')
        if not weights_path.is_file():
            weights_dir = Path.home()
            weights_path = Path.home() / str(model_name + '.pth')
            for url in file_url:
                weights_path = load_file_from_url(url=url, model_dir=str(weights_dir.absolute()), progress=True, file_name=None)
        upsampler = RealESRGANer(scale=netscale, model_path=str(weights_path.absolute()) if isinstance(weights_path, Path) else weights_path, model=model, tile=self.tile, tile_pad=self.tile_pad, pre_pad=self.pre_pad, half=self.use_half)
        model_face_fix = None
        if model_type != RESRGAN_MODELS.RealESRGAN_x4plus_anime_6B:
            model_face_fix = gfpgan_wrapper(upsampler, netscale)
        resrgan_models[model_name] = {'name': model_name, 'netscale': netscale, 'model': upsampler, 'model_face_fix': model_face_fix}
    return resrgan_models

class StableDiffusionGenerator(Executor):
    """
    Executor generator for all stable diffusion API paths.
    """
    batch_size = 4
    stable_diffusion_module = None

    def __init__(self, batch_size: int=4, height: int=512, max_n_subprompts=8, max_resolution=589824, n_iter: int=1, use_half: bool=False, weights_path='', width: int=512, config_path: Optional[str]=None, **kwargs):
        """
        @batch_size: The number of images to create at the same time. It only
          slightly speeds up inference while dramatically increasing memory
          usage.
        @height: Default height of image in pixels.
        @max_n_subprompts: Maximum number of subprompts you can add to an image
          in the denoising step. More subprompts = slower denoising.
        @max_resolution: The maximum resolution for images in pixels, to keep
          your GPU from OOMing in server applications.
        @n_iter: Default number of iterations for the sampler.
        @use_half: Sample with FP16 instead of FP32. Saves some memory for
          approximately the same results.
        @weights_path: Location of the Stable Diffusion weights checkpoint file.
        @width: Default width of image in pixels.
        @config_path: Location for the YAML configuration file for the model.
        """
        super().__init__(**kwargs)
        self.batch_size = batch_size
        self.stable_diffusion_module = StableDiffusionInference(checkpoint_loc=weights_path, height=height, max_n_subprompts=max_n_subprompts, max_resolution=max_resolution, n_iter=n_iter, use_half=use_half, width=width, config_loc=config_path)

    def _h_and_w_from_parameters(self, parameters, opt):
        height = parameters.get('height', opt.height)
        if height is not None:
            height = int(height)
        else:
            height = opt.height
        width = parameters.get('width', opt.width)
        if width is not None:
            width = int(width)
        else:
            width = opt.width
        return (height, width)

    @requests(on='/')
    def txt2img(self, docs: DocumentArray, parameters: Dict, **kwargs):
        request_time = time.time()
        opt = self.stable_diffusion_module.opt
        sampler = parameters.get('sampler', 'k_lms')
        if sampler not in K_DIFF_SAMPLERS:
            raise ValueError(f'sampler must be in {K_DIFF_SAMPLERS}, got {sampler}')
        scale = parameters.get('scale', opt.scale)
        noiser = parameters.get('noiser', None)
        num_images = max(1, min(8, int(parameters.get('num_images', 1))))
        seed = int(parameters.get('seed', randint(0, 2 ** 32 - 1)))
        steps = min(int(parameters.get('steps', opt.ddim_steps)), MAX_STEPS)
        height, width = self._h_and_w_from_parameters(parameters, opt)
        n_samples = self.batch_size
        n_iter = opt.n_iter
        if num_images < n_samples:
            n_samples = num_images
        if num_images // n_samples > n_iter:
            n_iter = num_images // n_samples
        for d in docs:
            batch_size = n_samples
            prompt = d.text
            assert prompt is not None
            self.logger.info(f'stable diffusion start {num_images} images, prompt "{prompt}"...')
            for i in trange(n_iter, desc='Sampling'):
                samples, extra_data = self.stable_diffusion_module.sample(prompt, batch_size, sampler, seed + i, steps, height=height, noiser=noiser, scale=scale, width=width)
                conditioning, images = itemgetter('conditioning', 'images')(extra_data)
                image_conditioning = None
                if isinstance(conditioning, dict):
                    image_conditioning = conditioning['c_concat']
                    conditioning = conditioning['c_crossattn']
                for img in images:
                    buffered = BytesIO()
                    img.save(buffered, format='PNG')
                    samples_buffer = BytesIO()
                    torch.save(samples, samples_buffer)
                    samples_buffer.seek(0)
                    if image_conditioning is not None:
                        image_conditioning_buffer = BytesIO()
                        torch.save(image_conditioning, image_conditioning_buffer)
                        image_conditioning_buffer.seek(0)
                    _d = Document(embedding=conditioning, blob=buffered.getvalue(), mime_type='image/png', tags={'latent_repr': base64.b64encode(samples_buffer.getvalue()).decode(), 'image_conditioning': base64.b64encode(image_conditioning_buffer.getvalue()).decode() if image_conditioning is not None else None, 'request': {'api': 'txt2img', 'height': height, 'noiser': noiser, 'num_images': num_images, 'sampler': sampler, 'scale': scale, 'seed': seed, 'steps': steps, 'width': width}, 'text': prompt, 'generator': 'stable-diffusion', 'request_time': request_time, 'created_time': time.time()}).convert_blob_to_datauri()
                    _d.text = prompt
                    d.matches.append(_d)
                torch.cuda.empty_cache()

    @requests(on='/stablediffuse')
    def stablediffuse(self, docs: DocumentArray, parameters: Dict, **kwargs):
        """
        Called "img2img" in the scripts of the stable-diffusion repo.
        """
        request_time = time.time()
        opt = self.stable_diffusion_module.opt
        latentless = parameters.get('latentless', False)
        noiser = parameters.get('noiser', None)
        num_images = max(1, min(8, int(parameters.get('num_images', 1))))
        prompt_override = parameters.get('prompt', None)
        sampler = parameters.get('sampler', 'k_lms')
        scale = parameters.get('scale', opt.scale)
        seed = int(parameters.get('seed', randint(0, 2 ** 32 - 1)))
        strength = parameters.get('strength', 0.75)
        if sampler not in K_DIFF_SAMPLERS:
            raise ValueError(f'sampler must be in {K_DIFF_SAMPLERS}, got {sampler}')
        steps = min(int(parameters.get('steps', opt.ddim_steps)), MAX_STEPS)
        n_samples = self.batch_size
        n_iter = opt.n_iter
        if num_images < n_samples:
            n_samples = num_images
        if num_images // n_samples > n_iter:
            n_iter = num_images // n_samples
        assert 0.0 < strength < 1.0, 'can only work with strength in (0.0, 1.0)'
        for d in docs:
            batch_size = n_samples
            prompt = d.text
            if prompt_override is not None:
                prompt = prompt_override
            assert prompt is not None
            for i in trange(n_iter, desc='Sampling'):
                samples, extra_data = self.stable_diffusion_module.sample(prompt, batch_size, sampler, seed + i, steps, init_pil_image=document_to_pil(d), init_pil_image_as_random_latent=latentless, noiser=noiser, scale=scale, strength=strength)
                conditioning, images = itemgetter('conditioning', 'images')(extra_data)
                image_conditioning = None
                if isinstance(conditioning, dict):
                    image_conditioning = conditioning['c_concat']
                    conditioning = conditioning['c_crossattn']
                for img in images:
                    buffered = BytesIO()
                    img.save(buffered, format='PNG')
                    samples_buffer = BytesIO()
                    torch.save(samples, samples_buffer)
                    samples_buffer.seek(0)
                    if image_conditioning is not None:
                        image_conditioning_buffer = BytesIO()
                        torch.save(image_conditioning, image_conditioning_buffer)
                        image_conditioning_buffer.seek(0)
                    _d = Document(embedding=conditioning, blob=buffered.getvalue(), mime_type='image/png', tags={'latent_repr': base64.b64encode(samples_buffer.getvalue()).decode(), 'image_conditioning': base64.b64encode(image_conditioning_buffer.getvalue()).decode() if image_conditioning is not None else None, 'request': {'api': 'stablediffuse', 'latentless': latentless, 'noiser': noiser, 'num_images': num_images, 'sampler': sampler, 'scale': scale, 'seed': seed, 'steps': steps, 'strength': strength}, 'text': prompt, 'generator': 'stable-diffusion', 'request_time': request_time, 'created_time': time.time()}).convert_blob_to_datauri()
                    _d.text = prompt
                    d.matches.append(_d)
                torch.cuda.empty_cache()

    @requests(on='/stableinterpolate')
    def stableinterpolate(self, docs: DocumentArray, parameters: Dict, **kwargs):
        """
        Create a series of images that are interpolations between two prompts.
        """
        request_time = time.time()
        opt = self.stable_diffusion_module.opt
        noiser = parameters.get('noiser', None)
        num_images = max(1, min(16, int(parameters.get('num_images', 1))))
        resample_prior = parameters.get('resample_prior', True)
        sampler = parameters.get('sampler', 'k_lms')
        scale = parameters.get('scale', opt.scale)
        seed = int(parameters.get('seed', randint(0, 2 ** 32 - 1)))
        strength = parameters.get('strength', 0.75)
        if sampler not in K_DIFF_SAMPLERS:
            raise ValueError(f'sampler must be in {K_DIFF_SAMPLERS}, got {sampler}')
        steps = min(int(parameters.get('steps', opt.ddim_steps)), MAX_STEPS)
        height, width = self._h_and_w_from_parameters(parameters, opt)
        assert 0.5 <= strength <= 1.0, 'can only work with strength in [0.5, 1.0]'
        for d in docs:
            batch_size = 1
            prompt = d.text
            assert prompt is not None
            prompts = prompt.split('|')
            conditioning_start, unconditioning, weighted_subprompts_start, _ = self.stable_diffusion_module.compute_conditioning_and_weights(prompts[0].strip(), batch_size)
            conditioning_end, _, weighted_subprompts_end, _ = self.stable_diffusion_module.compute_conditioning_and_weights(prompts[1].strip(), batch_size)
            assert len(weighted_subprompts_start) == len(weighted_subprompts_end), 'Weighted subprompts for interpolation must be equal in number'
            to_iterate = list(enumerate(np.linspace(0, 1, num_images)))
            samples_last = None
            for i, percent in to_iterate:
                c = None
                if i < 1:
                    c = conditioning_start
                elif i == len(to_iterate) - 1:
                    c = conditioning_end
                else:
                    c = conditioning_start.clone().detach()
                    for embedding_i, _ in enumerate(conditioning_start):
                        c[embedding_i] = slerp(percent, conditioning_start[embedding_i], conditioning_end[embedding_i])
                weighted_subprompts = combine_weighted_subprompts(percent, weighted_subprompts_start, weighted_subprompts_end)
                image = None
                if i == 0 or not resample_prior:
                    samples_last, extra_data = self.stable_diffusion_module.sample(prompt, batch_size, sampler, seed, steps, conditioning=c, height=height, noiser=noiser, prompt_concept_injection_required=False, scale=scale, weighted_subprompts=weighted_subprompts, width=width, unconditioning=unconditioning)
                    image, = itemgetter('images')(extra_data)
                else:
                    samples_last, extra_data = self.stable_diffusion_module.sample(prompt, batch_size, sampler, seed + i, steps, conditioning=c, height=height, init_latent=samples_last, noiser=noiser, prompt_concept_injection_required=False, scale=scale, strength=strength, weighted_subprompts=weighted_subprompts, width=width, unconditioning=unconditioning)
                    image, = itemgetter('images')(extra_data)
                torch.cuda.empty_cache()
                buffered = BytesIO()
                image.save(buffered, format='PNG')
                samples_buffer = BytesIO()
                torch.save(samples_last, samples_buffer)
                samples_buffer.seek(0)
                image_conditioning = None
                if isinstance(c, dict):
                    image_conditioning = c['c_concat']
                    c = c['c_crossattn']
                if image_conditioning is not None:
                    image_conditioning_buffer = BytesIO()
                    torch.save(image_conditioning, image_conditioning_buffer)
                    image_conditioning_buffer.seek(0)
                _d = Document(embedding=c, blob=buffered.getvalue(), mime_type='image/png', tags={'latent_repr': base64.b64encode(samples_buffer.getvalue()).decode(), 'image_conditioning': base64.b64encode(image_conditioning_buffer.getvalue()).decode() if image_conditioning is not None else None, 'request': {'api': 'stableinterpolate', 'height': height, 'noiser': noiser, 'num_images': num_images, 'resample_prior': resample_prior, 'sampler': sampler, 'scale': scale, 'seed': seed, 'steps': steps, 'strength': strength, 'width': width}, 'text': prompt, 'percent': percent, 'generator': 'stable-diffusion', 'request_time': request_time, 'created_time': time.time()}).convert_blob_to_datauri()
                _d.text = prompt
                d.matches.append(_d)

def __init__(self, batch_size: int=4, height: int=512, max_n_subprompts=8, max_resolution=589824, n_iter: int=1, use_half: bool=False, weights_path='', width: int=512, config_path: Optional[str]=None, **kwargs):
    """
        @batch_size: The number of images to create at the same time. It only
          slightly speeds up inference while dramatically increasing memory
          usage.
        @height: Default height of image in pixels.
        @max_n_subprompts: Maximum number of subprompts you can add to an image
          in the denoising step. More subprompts = slower denoising.
        @max_resolution: The maximum resolution for images in pixels, to keep
          your GPU from OOMing in server applications.
        @n_iter: Default number of iterations for the sampler.
        @use_half: Sample with FP16 instead of FP32. Saves some memory for
          approximately the same results.
        @weights_path: Location of the Stable Diffusion weights checkpoint file.
        @width: Default width of image in pixels.
        @config_path: Location for the YAML configuration file for the model.
        """
    super().__init__(**kwargs)
    self.batch_size = batch_size
    self.stable_diffusion_module = StableDiffusionInference(checkpoint_loc=weights_path, height=height, max_n_subprompts=max_n_subprompts, max_resolution=max_resolution, n_iter=n_iter, use_half=use_half, width=width, config_loc=config_path)

