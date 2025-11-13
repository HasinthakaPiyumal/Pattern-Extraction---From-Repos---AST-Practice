# Cluster 7

class SamplingProbabilityCorrection(tf.keras.layers.Layer):
    """Sampling probability correction."""

    def call(self, logits: tf.Tensor, candidate_sampling_probability: tf.Tensor) -> tf.Tensor:
        """Corrects the input logits to account for candidate sampling probability."""
        return logits - tf.math.log(candidate_sampling_probability)

def call(self, logits: tf.Tensor, candidate_sampling_probability: tf.Tensor) -> tf.Tensor:
    """Corrects the input logits to account for candidate sampling probability."""
    return logits - tf.math.log(candidate_sampling_probability)

