# Cluster 22

class LoRAManager:
    """LoRA manager with enhanced error handling and caching"""

    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.loaded_adapters = {}
        self.adapter_names = {}

    def _get_adapter_name(self, adapter_id: str) -> str:
        """Create a valid adapter name from adapter_id."""
        if adapter_id in self.adapter_names:
            return self.adapter_names[adapter_id]
        name = adapter_id.replace('.', '_').replace('-', '_')
        name = ''.join((c if c.isalnum() or c == '_' else '' for c in name))
        if name[0].isdigit():
            name = f'adapter_{name}'
        self.adapter_names[adapter_id] = name
        return name

    def validate_adapter(self, adapter_id: str) -> bool:
        """Validate if adapter exists and is compatible"""
        try:
            config = PeftConfig.from_pretrained(adapter_id, trust_remote_code=True, token=os.getenv('HF_TOKEN'))
            return True
        except Exception as e:
            logger.error(f'Error validating adapter {adapter_id}: {str(e)}')
            return False

    def load_adapter(self, base_model: PreTrainedModel, adapter_id: str) -> PreTrainedModel:
        """Load a LoRA adapter with enhanced caching"""
        model_key = base_model.config._name_or_path

        def _load_adapter():
            logger.info(f'Loading LoRA adapter: {adapter_id}')
            if not self.validate_adapter(adapter_id):
                error_msg = f'Adapter {adapter_id} not found or is not compatible'
                logger.error(error_msg)
                raise ValueError(error_msg)
            try:
                adapter_name = self._get_adapter_name(adapter_id)
                config = PeftConfig.from_pretrained(adapter_id, trust_remote_code=True, token=os.getenv('HF_TOKEN'))
                model = base_model
                model.add_adapter(config, adapter_name=adapter_name)
                if model not in self.loaded_adapters:
                    self.loaded_adapters[model] = []
                if adapter_id not in self.loaded_adapters[model]:
                    self.loaded_adapters[model].append(adapter_id)
                return model
            except Exception as e:
                error_msg = f'Failed to load adapter {adapter_id}: {str(e)}'
                logger.error(error_msg)
                raise RuntimeError(error_msg) from e
        return self.cache_manager.get_or_load_adapter(model_key, adapter_id, _load_adapter)

    def set_active_adapter(self, model: PeftModel, adapter_id: str=None) -> bool:
        """Set a specific adapter as active with error handling"""
        if not isinstance(model, PeftModel):
            logger.warning('Model is not a PeftModel, cannot set active adapter')
            return False
        available_adapters = self.loaded_adapters.get(model, [])
        if not available_adapters:
            logger.warning('No adapters loaded in model')
            return False
        if adapter_id is None:
            adapter_id = available_adapters[-1]
        if adapter_id in available_adapters:
            try:
                model.set_adapter(self._get_adapter_name(adapter_id))
                logger.info(f'Successfully set active adapter to: {adapter_id}')
                return True
            except Exception as e:
                logger.error(f'Error setting adapter {adapter_id}: {str(e)}')
                return False
        else:
            logger.warning(f'Requested adapter {adapter_id} not loaded. Available adapters: {available_adapters}')
            return False

def load_adapter(self, base_model: PreTrainedModel, adapter_id: str) -> PreTrainedModel:
    """Load a LoRA adapter with enhanced caching"""
    model_key = base_model.config._name_or_path

    def _load_adapter():
        logger.info(f'Loading LoRA adapter: {adapter_id}')
        if not self.validate_adapter(adapter_id):
            error_msg = f'Adapter {adapter_id} not found or is not compatible'
            logger.error(error_msg)
            raise ValueError(error_msg)
        try:
            adapter_name = self._get_adapter_name(adapter_id)
            config = PeftConfig.from_pretrained(adapter_id, trust_remote_code=True, token=os.getenv('HF_TOKEN'))
            model = base_model
            model.add_adapter(config, adapter_name=adapter_name)
            if model not in self.loaded_adapters:
                self.loaded_adapters[model] = []
            if adapter_id not in self.loaded_adapters[model]:
                self.loaded_adapters[model].append(adapter_id)
            return model
        except Exception as e:
            error_msg = f'Failed to load adapter {adapter_id}: {str(e)}'
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    return self.cache_manager.get_or_load_adapter(model_key, adapter_id, _load_adapter)

