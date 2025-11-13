# Cluster 15

class AllAugmentationTransform:

    def __init__(self, resize_param=None, rotation_param=None, flip_param=None, crop_param=None, jitter_param=None):
        self.transforms = []
        self.select = SelectRandomFrames()
        self.transforms.append(self.select)
        if flip_param is not None:
            self.transforms.append(RandomFlip(**flip_param))
        if rotation_param is not None:
            self.transforms.append(RandomRotation(**rotation_param))
        if resize_param is not None:
            self.transforms.append(RandomResize(**resize_param))
        if crop_param is not None:
            self.transforms.append(RandomCrop(**crop_param))
        if jitter_param is not None:
            self.transforms.append(ColorJitter(**jitter_param))
        self.transforms.append(SplitSourceDriving())

    def __call__(self, clip):
        for t in self.transforms:
            clip = t(clip)
        return clip

def __call__(self, clip):
    for t in self.transforms:
        clip = t(clip)
    return clip

