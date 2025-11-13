# Cluster 51

def register_tiny_vit_model(fn):
    """Register a TinyViT model
    It is a wrapper of `register_model` with loading the pretrained checkpoint.
    """

    def fn_wrapper(pretrained=False, **kwargs):
        model = fn()
        if pretrained:
            model_name = fn.__name__
            assert model_name in _provided_checkpoints, f'Sorry that the checkpoint `{model_name}` is not provided yet.'
            url = _checkpoint_url_format.format(_provided_checkpoints[model_name])
            checkpoint = torch.hub.load_state_dict_from_url(url=url, map_location='cpu', check_hash=False)
            model.load_state_dict(checkpoint['model'])
        return model
    fn_wrapper.__name__ = fn.__name__
    return register_model(fn_wrapper)

