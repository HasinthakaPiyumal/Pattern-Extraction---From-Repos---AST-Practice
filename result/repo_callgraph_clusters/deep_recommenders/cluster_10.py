# Cluster 10

@tf.keras.utils.register_keras_serializable()
class LayerNormalization(Layer):

    def __init__(self, epsilon=1e-08, **kwargs):
        self._epsilon = epsilon
        super(LayerNormalization, self).__init__(**kwargs)

    def build(self, input_shape):
        self.beta = self.add_weight(shape=(input_shape[-1],), initializer='zero', name='beta')
        self.gamma = self.add_weight(shape=(input_shape[-1],), initializer='one', name='gamma')
        super(LayerNormalization, self).build(input_shape)

    def call(self, inputs, **kwargs):
        mean, variance = tf.nn.moments(inputs, [-1], keepdims=True)
        normalized = (inputs - mean) / (variance + self._epsilon) ** 0.5
        outputs = self.gamma * normalized + self.beta
        return outputs

    def compute_output_shape(self, input_shape):
        return input_shape

def call(self, inputs, **kwargs):
    mean, variance = tf.nn.moments(inputs, [-1], keepdims=True)
    normalized = (inputs - mean) / (variance + self._epsilon) ** 0.5
    outputs = self.gamma * normalized + self.beta
    return outputs

