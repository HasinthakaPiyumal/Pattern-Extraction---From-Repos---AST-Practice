# Cluster 7

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

@staticmethod
def document_to_pil(doc: Document) -> Image:
    uri_data = urlopen(doc.uri)
    return Image.open(BytesIO(uri_data.read()))

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

def document_to_pil(self, doc):
    uri_data = urlopen(doc.uri)
    return Image.open(BytesIO(uri_data.read()))

class WaifuUpscaler(Executor):

    def __init__(self, waifu_url: str, top_k: int=3, **kwargs):
        super().__init__(**kwargs)
        print('downloading...')
        resp = urlopen(waifu_url)
        zipfile = ZipFile(BytesIO(resp.read()))
        bin_path = './waifu-bin'
        zipfile.extractall(bin_path)
        print('complete')
        self.waifu_path = os.path.realpath(f'{bin_path}/waifu2x-ncnn-vulkan-20220419-ubuntu/waifu2x-ncnn-vulkan')
        self.top_k = top_k
        st = os.stat(self.waifu_path)
        os.chmod(self.waifu_path, st.st_mode | stat.S_IEXEC)
        print(self.waifu_path)

    def _upscale(self, d: Document):
        with tempfile.NamedTemporaryFile(suffix='.png') as f_in, tempfile.NamedTemporaryFile(suffix='.png') as f_out:
            d.save_uri_to_file(f_in.name)
            print(subprocess.getoutput(f'{self.waifu_path} -i {f_in.name} -o {f_out.name} -s 4 -n 0 -g -1'))
            print(f'{f_in.name} done')
            d.uri = f_out.name
            d.convert_uri_to_datauri()
            d.blob = None
            d.tags['upscaled'] = 'true'
        return d

    @requests(on='/upscale')
    async def upscale(self, docs: DocumentArray, **kwargs):
        docs.apply(self._upscale)

def __init__(self, waifu_url: str, top_k: int=3, **kwargs):
    super().__init__(**kwargs)
    print('downloading...')
    resp = urlopen(waifu_url)
    zipfile = ZipFile(BytesIO(resp.read()))
    bin_path = './waifu-bin'
    zipfile.extractall(bin_path)
    print('complete')
    self.waifu_path = os.path.realpath(f'{bin_path}/waifu2x-ncnn-vulkan-20220419-ubuntu/waifu2x-ncnn-vulkan')
    self.top_k = top_k
    st = os.stat(self.waifu_path)
    os.chmod(self.waifu_path, st.st_mode | stat.S_IEXEC)
    print(self.waifu_path)

def document_to_pil(doc):
    uri_data = urlopen(doc.uri)
    return Image.open(BytesIO(uri_data.read()))

