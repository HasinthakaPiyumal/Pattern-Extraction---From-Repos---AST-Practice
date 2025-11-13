# Cluster 78

class IAAAffine2(DualIAATransform):
    """Place a regular grid of points on the input and randomly move the neighbourhood of these point around
    via affine transformations.

    Note: This class introduce interpolation artifacts to mask if it has values other than {0;1}

    Args:
        p (float): probability of applying the transform. Default: 0.5.

    Targets:
        image, mask
    """

    def __init__(self, scale=(0.7, 1.3), translate_percent=None, translate_px=None, rotate=0.0, shear=(-0.1, 0.1), order=1, cval=0, mode='reflect', always_apply=False, p=0.5):
        super(IAAAffine2, self).__init__(always_apply, p)
        self.scale = dict(x=scale, y=scale)
        self.translate_percent = to_tuple(translate_percent, 0)
        self.translate_px = to_tuple(translate_px, 0)
        self.rotate = to_tuple(rotate)
        self.shear = dict(x=shear, y=shear)
        self.order = order
        self.cval = cval
        self.mode = mode

    @property
    def processor(self):
        return iaa.Affine(self.scale, self.translate_percent, self.translate_px, self.rotate, self.shear, self.order, self.cval, self.mode)

    def get_transform_init_args_names(self):
        return ('scale', 'translate_percent', 'translate_px', 'rotate', 'shear', 'order', 'cval', 'mode')

@property
def processor(self):
    return iaa.Affine(self.scale, self.translate_percent, self.translate_px, self.rotate, self.shear, self.order, self.cval, self.mode)

