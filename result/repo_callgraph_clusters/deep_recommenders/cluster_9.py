# Cluster 9

@tf.keras.utils.register_keras_serializable()
class Dice(tf.keras.layers.Layer):

    def __init__(self, epsilon: float=1e-08, alpha_initializer='zeros', alpha_regularizer=None, **kwargs):
        super(Dice, self).__init__(**kwargs)
        self._epsilon = epsilon
        self._alpha_initializer = alpha_initializer
        self._alpha_regularizer = alpha_regularizer

    def build(self, input_shape):
        self.prelu = tf.keras.layers.PReLU(alpha_initializer=self._alpha_initializer, alpha_regularizer=self._alpha_regularizer)
        self.built = True

    def call(self, inputs, **kwargs):
        inputs_mean = tf.math.reduce_mean(inputs, axis=1, keepdims=True)
        inputs_var = tf.math.reduce_std(inputs, axis=1, keepdims=True)
        p = tf.nn.sigmoid((inputs - inputs_mean) / tf.sqrt(inputs_var + self._epsilon))
        x = self.prelu(inputs)
        outputs = tf.where(x > 0, x=p * x, y=(1 - p) * x)
        return outputs

    def get_config(self):
        config = {'epsilon': self._epsilon, 'alpha_initializer': tf.keras.initializers.serialize(self._alpha_initializer), 'alpha_regularizer': tf.keras.regularizers.serialize(self._alpha_regularizer)}
        base_config = super(Dice, self).get_config()
        return {**base_config, **config}

def build(self, input_shape):
    self.prelu = tf.keras.layers.PReLU(alpha_initializer=self._alpha_initializer, alpha_regularizer=self._alpha_regularizer)
    self.built = True

