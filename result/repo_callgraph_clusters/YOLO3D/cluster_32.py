# Cluster 32

class TFUpsample(keras.layers.Layer):

    def __init__(self, size, scale_factor, mode, w=None):
        super().__init__()
        assert scale_factor == 2, 'scale_factor must be 2'
        self.upsample = lambda x: tf.image.resize(x, (x.shape[1] * 2, x.shape[2] * 2), method=mode)

    def call(self, inputs):
        return self.upsample(inputs)

def call(self, inputs):
    return self.upsample(inputs)

