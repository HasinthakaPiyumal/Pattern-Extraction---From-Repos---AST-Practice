# Cluster 21

class ModelManager:

    def __init__(self, cache_manager: CacheManager, device_manager: DeviceManager):
        self.cache_manager = cache_manager
        self.device_manager = device_manager

    def quantize_model(self, model):
        """Quantize model to 4-bit precision using bitsandbytes"""

        def _replace_linear_layers(module):
            for name, child in module.named_children():
                if isinstance(child, torch.nn.Linear):
                    setattr(module, name, bnb.nn.Linear4bit(child.in_features, child.out_features, bias=child.bias is not None, compute_dtype=torch.float16))
                else:
                    _replace_linear_layers(child)
        _replace_linear_layers(model)
        return model

    def load_base_model(self, model_id: str, quantize: bool=True) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:

        def _load_model():
            logger.info(f'Loading base model: {model_id}')
            device = self.device_manager.get_optimal_device()
            logger.info(f'Using device: {device}')
            tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True, token=os.getenv('HF_TOKEN'))
            model_kwargs = {'trust_remote_code': True, 'device_map': 'auto' if 'cuda' in device else device}
            if 'cuda' in device:
                compute_capability = torch.cuda.get_device_capability(0)
                if compute_capability[0] >= 8:
                    model_kwargs['torch_dtype'] = torch.bfloat16
                elif compute_capability[0] >= 7:
                    model_kwargs['torch_dtype'] = torch.float16
                try:
                    import flash_attn
                    has_flash_attn = True
                    logger.info('Flash Attention 2 is available')
                    model_kwargs['attn_implementation'] = 'flash_attention_2'
                except ImportError:
                    has_flash_attn = False
                    logger.info('Flash Attention 2 is not installed - falling back to default attention')
            elif 'mps' in device:
                if 'gemma' in model_id.lower():
                    model_kwargs['torch_dtype'] = torch.float32
                    logger.info('Using MPS device with float32 for Gemma model (float16 causes NaN)')
                else:
                    model_kwargs['torch_dtype'] = torch.float16
                    logger.info('Using MPS device with float16 precision')
            elif hasattr(torch.cpu, 'has_fp16') and torch.cpu.has_fp16:
                model_kwargs['torch_dtype'] = torch.float16
                logger.info('Using CPU device with float16 precision')
            else:
                model_kwargs['torch_dtype'] = torch.float32
                logger.info('Using CPU device with float32 precision - FP16 not supported')
            try:
                model = AutoModelForCausalLM.from_pretrained(model_id, token=os.getenv('HF_TOKEN'), **model_kwargs)
            except Exception as e:
                if 'attn_implementation' in model_kwargs:
                    logger.warning(f'Failed to load model with Flash Attention: {e}')
                    logger.info('Retrying without Flash Attention...')
                    model_kwargs.pop('attn_implementation')
                    model = AutoModelForCausalLM.from_pretrained(model_id, token=os.getenv('HF_TOKEN'), **model_kwargs)
                elif model_kwargs['torch_dtype'] == torch.float16:
                    logger.warning(f'Failed to load model with FP16: {e}')
                    logger.info('Falling back to FP32...')
                    model_kwargs['torch_dtype'] = torch.float32
                    model = AutoModelForCausalLM.from_pretrained(model_id, token=os.getenv('HF_TOKEN'), **model_kwargs)
            logger.info(f'Model loaded successfully with dtype: {model_kwargs['torch_dtype']}')
            if quantize and 'cuda' in device and (model_kwargs['torch_dtype'] == torch.float32):
                model = self.quantize_model(model)
            return (model, tokenizer)
        return self.cache_manager.get_or_load_model(model_id, _load_model)

def _replace_linear_layers(module):
    for name, child in module.named_children():
        if isinstance(child, torch.nn.Linear):
            setattr(module, name, bnb.nn.Linear4bit(child.in_features, child.out_features, bias=child.bias is not None, compute_dtype=torch.float16))
        else:
            _replace_linear_layers(child)

def quantize_model(self, model):
    """Quantize model to 4-bit precision using bitsandbytes"""

    def _replace_linear_layers(module):
        for name, child in module.named_children():
            if isinstance(child, torch.nn.Linear):
                setattr(module, name, bnb.nn.Linear4bit(child.in_features, child.out_features, bias=child.bias is not None, compute_dtype=torch.float16))
            else:
                _replace_linear_layers(child)
    _replace_linear_layers(model)
    return model

