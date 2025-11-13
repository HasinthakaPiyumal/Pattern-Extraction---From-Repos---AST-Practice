# Cluster 30

class Compose(object):

    def __init__(self, cfg=None):
        self.cfg = cfg if cfg is not None else []
        self.transforms = []
        for t_cfg in self.cfg:
            self.transforms.append(TRANSFORMS.build(t_cfg))

    def __call__(self, data_dict):
        for t in self.transforms:
            data_dict = t(data_dict)
        return data_dict

def __call__(self, data_dict):
    for t in self.transforms:
        data_dict = t(data_dict)
    return data_dict

