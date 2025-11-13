# Cluster 24

def create_env(env_name, custom_cfg={}, **kwargs):
    """
    env_name choice in ['st_v0', 'sp_v0']
    """
    cfg = importlib.import_module('gobigger.configs.{}'.format(env_name))
    cfg = eval('cfg.{}'.format(env_name))
    cfg = deep_merge_dicts(cfg, custom_cfg)
    if env_name.startswith('st'):
        return create_env_st(cfg, **kwargs)
    elif env_name.startswith('sp'):
        return create_env_sp(cfg, **kwargs)
    else:
        raise NotImplementedError

def create_env_custom(type, cfg=None, **kwargs):
    if type == 'st':
        return create_env_st(cfg, **kwargs)
    elif type == 'sp':
        return create_env_sp(cfg, **kwargs)
    else:
        raise NotImplementedError

