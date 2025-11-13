# Cluster 12

@tf.keras.utils.register_keras_serializable()
class Transformer(Layer):

    def __init__(self, vocab_size, model_dim, n_heads=8, encoder_stack=6, decoder_stack=6, feed_forward_size=2048, dropout_rate=0.1, **kwargs):
        self._vocab_size = vocab_size
        self._model_dim = model_dim
        self._n_heads = n_heads
        self._encoder_stack = encoder_stack
        self._decoder_stack = decoder_stack
        self._feed_forward_size = feed_forward_size
        self._dropout_rate = dropout_rate
        super(Transformer, self).__init__(**kwargs)

    def build(self, input_shape):
        self.embeddings = self.add_weight(shape=(self._vocab_size, self._model_dim), initializer='glorot_uniform', trainable=True, name='embeddings')
        self.EncoderPositionEncoding = PositionEncoding(self._model_dim)
        self.EncoderMultiHeadAttentions = [MultiHeadAttention(self._n_heads, self._model_dim // self._n_heads) for _ in range(self._encoder_stack)]
        self.EncoderLayerNorms0 = [LayerNormalization() for _ in range(self._encoder_stack)]
        self.EncoderPositionWiseFeedForwards = [PositionWiseFeedForward(self._model_dim, self._feed_forward_size) for _ in range(self._encoder_stack)]
        self.EncoderLayerNorms1 = [LayerNormalization() for _ in range(self._encoder_stack)]
        self.DecoderPositionEncoding = PositionEncoding(self._model_dim)
        self.DecoderMultiHeadAttentions0 = [MultiHeadAttention(self._n_heads, self._model_dim // self._n_heads, future=True) for _ in range(self._decoder_stack)]
        self.DecoderLayerNorms0 = [LayerNormalization() for _ in range(self._decoder_stack)]
        self.DecoderMultiHeadAttentions1 = [MultiHeadAttention(self._n_heads, self._model_dim // self._n_heads) for _ in range(self._decoder_stack)]
        self.DecoderLayerNorms1 = [LayerNormalization() for _ in range(self._decoder_stack)]
        self.DecoderPositionWiseFeedForwards = [PositionWiseFeedForward(self._model_dim, self._feed_forward_size) for _ in range(self._decoder_stack)]
        self.DecoderLayerNorms2 = [LayerNormalization() for _ in range(self._decoder_stack)]
        super(Transformer, self).build(input_shape)

    def encoder(self, inputs):
        if K.dtype(inputs) != 'int32':
            inputs = K.cast(inputs, 'int32')
        masks = K.equal(inputs, 0)
        embeddings = K.gather(self.embeddings, inputs)
        embeddings *= self._model_dim ** 0.5
        position_encodings = self.EncoderPositionEncoding(embeddings)
        encodings = embeddings + position_encodings
        encodings = K.dropout(encodings, self._dropout_rate)
        for i in range(self._encoder_stack):
            attention = self.EncoderMultiHeadAttentions[i]
            attention_input = [encodings, encodings, encodings, masks]
            attention_out = attention(attention_input)
            attention_out += encodings
            attention_out = self.EncoderLayerNorms0[i](attention_out)
            ff = self.EncoderPositionWiseFeedForwards[i]
            ff_out = ff(attention_out)
            ff_out += attention_out
            encodings = self.EncoderLayerNorms1[i](ff_out)
        return (encodings, masks)

    def decoder(self, inputs):
        decoder_inputs, encoder_encodings, encoder_masks = inputs
        if K.dtype(decoder_inputs) != 'int32':
            decoder_inputs = K.cast(decoder_inputs, 'int32')
        decoder_masks = K.equal(decoder_inputs, 0)
        embeddings = K.gather(self.embeddings, decoder_inputs)
        embeddings *= self._model_dim ** 0.5
        position_encodings = self.DecoderPositionEncoding(embeddings)
        encodings = embeddings + position_encodings
        encodings = K.dropout(encodings, self._dropout_rate)
        for i in range(self._decoder_stack):
            masked_attention = self.DecoderMultiHeadAttentions0[i]
            masked_attention_input = [encodings, encodings, encodings, decoder_masks]
            masked_attention_out = masked_attention(masked_attention_input)
            masked_attention_out += encodings
            masked_attention_out = self.DecoderLayerNorms0[i](masked_attention_out)
            attention = self.DecoderMultiHeadAttentions1[i]
            attention_input = [masked_attention_out, encoder_encodings, encoder_encodings, encoder_masks]
            attention_out = attention(attention_input)
            attention_out += masked_attention_out
            attention_out = self.DecoderLayerNorms1[i](attention_out)
            ff = self.DecoderPositionWiseFeedForwards[i]
            ff_out = ff(attention_out)
            ff_out += attention_out
            encodings = self.DecoderLayerNorms2[i](ff_out)
        linear_projection = K.dot(encodings, K.transpose(self.embeddings))
        outputs = K.softmax(linear_projection)
        return outputs

    def call(self, encoder_inputs, decoder_inputs, **kwargs):
        encoder_encodings, encoder_masks = self.encoder(encoder_inputs)
        encoder_outputs = self.decoder([decoder_inputs, encoder_encodings, encoder_masks])
        return encoder_outputs

    def compute_output_shape(self, input_shape):
        return (input_shape[0][0], input_shape[0][1], self._vocab_size)

    def get_config(self):
        config = {'vocab_size': self._vocab_size, 'model_dim': self._model_dim, 'n_heads': self._n_heads, 'encoder_stack': self._encoder_stack, 'decoder_stack': self._decoder_stack, 'feed_forward_size': self._feed_forward_size, 'dropout_rate': self._dropout_rate}
        base_config = super(Transformer, self).get_config()
        return {**base_config, **config}

def call(self, encoder_inputs, decoder_inputs, **kwargs):
    encoder_encodings, encoder_masks = self.encoder(encoder_inputs)
    encoder_outputs = self.decoder([decoder_inputs, encoder_encodings, encoder_masks])
    return encoder_outputs

