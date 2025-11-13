# Cluster 12

def wrap_env(env: gym.Env) -> gym.Env:
    """
            :param env:
            :return:
            """
    for wrapper_class, kwargs in zip(wrapper_classes, wrapper_kwargs):
        env = wrapper_class(env, **kwargs)
    return env

