# Cluster 77

class RandomSuperresMaskGenerator:

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __call__(self, img, iter_i=None):
        return make_random_superres_mask(img.shape[1:], **self.kwargs)

def __call__(self, img, iter_i=None):
    return make_random_superres_mask(img.shape[1:], **self.kwargs)

