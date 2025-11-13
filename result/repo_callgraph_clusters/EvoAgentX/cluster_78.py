# Cluster 78

class ModelRegistry:

    def __init__(self):
        self.models = {}
        self.model_configs = {}

    def register(self, key: str, model_cls, config_cls):
        if key in self.models:
            raise ValueError(f"model name '{key}' is already registered!")
        self.models[key] = model_cls
        self.model_configs[key] = config_cls

    def key_error_message(self, key: str):
        error_message = f'`{key}` is not a registered model name. Currently availabel model names: {self.get_model_names()}. If `{key}` is a customized model, you should use @register_model({key}) to register the model.'
        return error_message

    def get_model(self, key: str):
        model = self.models.get(key, None)
        if model is None:
            raise KeyError(self.key_error_message(key))
        return model

    def get_model_config(self, key: str):
        config = self.model_configs.get(key, None)
        if config is None:
            raise KeyError(self.key_error_message(key))
        return config

    def get_model_names(self):
        return list(self.models.keys())

def key_error_message(self, key: str):
    error_message = f'`{key}` is not a registered model name. Currently availabel model names: {self.get_model_names()}. If `{key}` is a customized model, you should use @register_model({key}) to register the model.'
    return error_message

