# Cluster 9

class GLID3Diffusion(Executor):

    def __init__(self, glid3_path: str, steps: int=100, **kwargs):
        super().__init__(**kwargs)
        os.environ['GLID_MODEL_PATH'] = glid3_path
        os.environ['GLID3_STEPS'] = str(steps)
        self.diffusion_steps = steps
        from dalle_flow_glid3.model import static_args
        from dalle_flow_glid3.blank_encoding import generate_blank_embeddings
        assert static_args
        self.logger.info('Generating blank embeddings')
        with open(os.path.join(os.path.dirname(__file__), 'clip_blank_encoding.json')) as f:
            self.blank_bert_embedding, self.blank_clip_embedding = generate_blank_embeddings('a', json.load(f))

    def run_glid3(self, d: Document, text: str, skip_rate: float, num_images: int):
        request_time = time.time()
        with tempfile.NamedTemporaryFile(suffix='.png') as f_in:
            self.logger.info(f'diffusion [{text}] ...')
            from dalle_flow_glid3.cli_parser import parser
            kw = {'init_image': f_in.name if d.uri else None, 'skip_timesteps': int(self.diffusion_steps * skip_rate) if d.uri else 0, 'steps': self.diffusion_steps, 'batch_size': num_images, 'num_batches': 1, 'text': f'"{text}"', 'output_path': d.id}
            kw_str_list = []
            for k, v in kw.items():
                if v is not None:
                    kw_str_list.extend([f'--{k}', str(v)])
            if d.uri:
                d.save_uri_to_file(f_in.name)
            from dalle_flow_glid3.sample import do_run
            args = parser.parse_args(kw_str_list)
            do_run(args, d.embedding, self.blank_bert_embedding, self.blank_clip_embedding)
            kw.update({'generator': 'GLID3-XL', 'request_time': request_time, 'created_time': time.time()})
            for f in glob.glob(f'{args.output_path}/*.png'):
                _d = Document(uri=f, text=d.text, tags=kw).convert_uri_to_datauri()
                d.matches.append(_d)
            shutil.rmtree(args.output_path, ignore_errors=True)
            self.logger.info(f'done with [{text}]!')

    @requests(on='/')
    def diffusion(self, docs: DocumentArray, parameters: Dict, **kwargs):
        skip_rate = float(parameters.get('skip_rate', 0.5))
        num_images = max(1, min(9, int(parameters.get('num_images', 1))))
        for d in docs:
            self.run_glid3(d, d.text, skip_rate=skip_rate, num_images=num_images)

def run_glid3(self, d: Document, text: str, skip_rate: float, num_images: int):
    request_time = time.time()
    with tempfile.NamedTemporaryFile(suffix='.png') as f_in:
        self.logger.info(f'diffusion [{text}] ...')
        from dalle_flow_glid3.cli_parser import parser
        kw = {'init_image': f_in.name if d.uri else None, 'skip_timesteps': int(self.diffusion_steps * skip_rate) if d.uri else 0, 'steps': self.diffusion_steps, 'batch_size': num_images, 'num_batches': 1, 'text': f'"{text}"', 'output_path': d.id}
        kw_str_list = []
        for k, v in kw.items():
            if v is not None:
                kw_str_list.extend([f'--{k}', str(v)])
        if d.uri:
            d.save_uri_to_file(f_in.name)
        from dalle_flow_glid3.sample import do_run
        args = parser.parse_args(kw_str_list)
        do_run(args, d.embedding, self.blank_bert_embedding, self.blank_clip_embedding)
        kw.update({'generator': 'GLID3-XL', 'request_time': request_time, 'created_time': time.time()})
        for f in glob.glob(f'{args.output_path}/*.png'):
            _d = Document(uri=f, text=d.text, tags=kw).convert_uri_to_datauri()
            d.matches.append(_d)
        shutil.rmtree(args.output_path, ignore_errors=True)
        self.logger.info(f'done with [{text}]!')

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

