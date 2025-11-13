# Cluster 11

def load_dataset(vocab_size, max_len):
    (x_train, y_train), (x_test, y_test) = tf.keras.datasets.imdb.load_data(maxlen=max_len, num_words=vocab_size)
    x_train = tf.keras.preprocessing.sequence.pad_sequences(x_train, maxlen=max_len)
    x_test = tf.keras.preprocessing.sequence.pad_sequences(x_test, maxlen=max_len)
    x_train_masks = tf.equal(x_train, 0)
    x_test_masks = tf.equal(x_test, 0)
    y_train = tf.keras.utils.to_categorical(y_train)
    y_test = tf.keras.utils.to_categorical(y_test)
    return ((x_train, x_train_masks, y_train), (x_test, x_test_masks, y_test))

def _take_long_axis(arr: tf.Tensor, indices: tf.Tensor) -> tf.Tensor:
    """从原始数据arr中，根据indices指定的下标，取出元素
    Args:
        arr: 原始数据，2D
        indices: 下标，2D
    Returns:
        根据下标取出的数据，2D
    """
    row_indices = tf.tile(tf.expand_dims(tf.range(tf.shape(indices)[0]), 1), [1, tf.shape(indices)[1]])
    gather_indices = tf.concat([tf.reshape(row_indices, (-1, 1)), tf.reshape(indices, (-1, 1))], axis=1)
    return tf.reshape(tf.gather_nd(arr, gather_indices), tf.shape(indices))

def _exclude(scores: tf.Tensor, identifiers: tf.Tensor, exclude: tf.Tensor, k: int) -> Tuple[tf.Tensor, tf.Tensor]:
    """从TopK中的items移除指定的候选item
    Args:
        scores: candidate scores. 2D
        identifiers: candidate identifiers. 2D
        exclude: identifiers to exclude. 2D
        k: 返回候选个数
    Returns:
        Tuple(top k candidates scores, top k candidates indentifiers)   
    """
    indents = tf.expand_dims(identifiers, -1)
    exclude = tf.expand_dims(exclude, 1)
    isin = tf.math.reduce_any(tf.math.equal(indents, exclude), -1)
    adjusted_scores = scores - tf.cast(isin, tf.float32) * 100000.0
    k = tf.math.minimum(k, tf.shape(scores)[1])
    _, indices = tf.math.top_k(adjusted_scores, k=k)
    return (_take_long_axis(scores, indices), _take_long_axis(identifiers, indices))

class Streaming(TopK):
    """Retrieves top k scoring items and identifiers from large dataset."""

    def __init__(self, k: int=10, query_model: Optional[tf.keras.Model]=None, handle_incomplete_batches: bool=True, num_parallel_calls: int=tf.data.experimental.AUTOTUNE, sorted_order: bool=True, *args, **kwargs):
        super().__init__(k, *args, **kwargs)
        self._query_model = query_model
        self._handle_incomplete_batches = handle_incomplete_batches
        self._num_parallel_calls = num_parallel_calls
        self._sorted_order = sorted_order
        self._candidates = None
        self._identifiers = None
        self._counter = self.add_weight('counter', dtype=tf.int32, trainable=False)

    def index(self, candidates: tf.data.Dataset, identifiers: Optional[tf.data.Dataset]=None, **kwargs) -> 'Streaming':
        """构建索引
        Args:
            candidates: 候选embeddings的Dataset
            identifiers: 候选 embeddings对应标识的Dataset(Opt)
        Returns:
            Self.
        """
        self._candidates = candidates
        self._identifiers = identifiers
        return self

    def call(self, queries: Union[tf.Tensor, Dict[Text, tf.Tensor]], k: Optional[int]=None, **kwargs) -> Tuple[tf.Tensor, tf.Tensor]:
        """检索索引
        args:
            queries: queries embeddings,
            k: 返回候选个数
        returns:
            Tuple(top k candidates scores, top k candidates identifiers)
        """
        k = k if k is not None else self._k
        if self._candidates is None:
            raise ValueError('The `index` method must be called first to create the retrieval index.')
        if self._query_model is not None:
            queries = self._query_model(queries)
        self._counter.assign(0)

        def top_scores(candidate_index: tf.Tensor, candidate_batch: tf.Tensor) -> Tuple[tf.Tensor, tf.Tensor]:
            """计算一个batch的候选集中的topK的scores和indices"""
            scores = tf.matmul(queries, candidate_batch, transpose_b=True)
            if self._handle_incomplete_batches is True:
                k_ = tf.math.minimum(k, tf.shape(scores)[1])
            else:
                k_ = k
            scores, indices = tf.math.top_k(scores, k=k_, sorted=self._sorted_order)
            return (scores, tf.gather(candidate_index, indices))

        def top_k(state: Tuple[tf.Tensor, tf.Tensor], x: Tuple[tf.Tensor, tf.Tensor]) -> Tuple[tf.Tensor, tf.Tensor]:
            """Reduction function.
            合并现在的topk和新的topk，重新从中选出topk
            """
            state_scores, state_indices = state
            x_scores, x_indices = x
            joined_scores = tf.concat([state_scores, x_scores], axis=1)
            joined_indices = tf.concat([state_indices, x_indices], axis=1)
            if self._handle_incomplete_batches is True:
                k_ = tf.math.minimum(k, tf.shape(joined_scores)[1])
            else:
                k_ = k
            scores, indices = tf.math.top_k(joined_scores, k=k_, sorted=self._sorted_order)
            return (scores, tf.gather(joined_indices, indices, batch_dims=1))
        if self._identifiers is not None:
            index_dtype = self._identifiers.element_spec.dtype
        else:
            index_dtype = tf.int32
        initial_state = (tf.zeros((tf.shape(queries)[0], 0), dtype=tf.float32), tf.zeros((tf.shape(queries)[0], 0), dtype=index_dtype))

        def enumerate_rows(batch: tf.Tensor) -> Tuple[tf.Tensor, tf.Tensor]:
            """Enumerates rows in each batch using a total element counter."""
            starting_counter = self._counter.read_value()
            end_counter = self._counter.assign_add(tf.shape(batch)[0])
            return (tf.range(starting_counter, end_counter), batch)
        if self._identifiers is not None:
            dataset = tf.data.Dataset.zip((self._identifiers, self._candidates))
        else:
            dataset = self._candidates.map(enumerate_rows)
        with _wrap_batch_too_small_error(k):
            result = dataset.map(top_scores, num_parallel_calls=self._num_parallel_calls).reduce(initial_state, top_k)
        return result

def top_scores(candidate_index: tf.Tensor, candidate_batch: tf.Tensor) -> Tuple[tf.Tensor, tf.Tensor]:
    """计算一个batch的候选集中的topK的scores和indices"""
    scores = tf.matmul(queries, candidate_batch, transpose_b=True)
    if self._handle_incomplete_batches is True:
        k_ = tf.math.minimum(k, tf.shape(scores)[1])
    else:
        k_ = k
    scores, indices = tf.math.top_k(scores, k=k_, sorted=self._sorted_order)
    return (scores, tf.gather(candidate_index, indices))

def top_k(state: Tuple[tf.Tensor, tf.Tensor], x: Tuple[tf.Tensor, tf.Tensor]) -> Tuple[tf.Tensor, tf.Tensor]:
    """Reduction function.
            合并现在的topk和新的topk，重新从中选出topk
            """
    state_scores, state_indices = state
    x_scores, x_indices = x
    joined_scores = tf.concat([state_scores, x_scores], axis=1)
    joined_indices = tf.concat([state_indices, x_indices], axis=1)
    if self._handle_incomplete_batches is True:
        k_ = tf.math.minimum(k, tf.shape(joined_scores)[1])
    else:
        k_ = k
    scores, indices = tf.math.top_k(joined_scores, k=k_, sorted=self._sorted_order)
    return (scores, tf.gather(joined_indices, indices, batch_dims=1))

def enumerate_rows(batch: tf.Tensor) -> Tuple[tf.Tensor, tf.Tensor]:
    """Enumerates rows in each batch using a total element counter."""
    starting_counter = self._counter.read_value()
    end_counter = self._counter.assign_add(tf.shape(batch)[0])
    return (tf.range(starting_counter, end_counter), batch)

class BruteForce(TopK):
    """暴力检索"""

    def __init__(self, k: int=10, query_model: Optional[tf.keras.Model]=None, *args, **kwargs):
        super().__init__(k, *args, **kwargs)
        self._query_model = query_model

    def index(self, candidates: Union[tf.Tensor, tf.data.Dataset], identifiers: Optional[Union[tf.Tensor, tf.data.Dataset]]=None) -> 'BruteForce':
        if isinstance(candidates, tf.data.Dataset):
            candidates = tf.concat(list(candidates), axis=0)
        if identifiers is None:
            identifiers = tf.range(candidates.shape[0])
        if isinstance(identifiers, tf.data.Dataset):
            identifiers = tf.concat(list(identifiers), axis=0)
        if tf.rank(candidates) != 2:
            raise ValueError('`candidates` ndim should be 2. Got `ndim` = {}'.format(tf.rank(candidates)))
        self._candidates = self.add_weight(name='candidates', dtype=candidates.dtype, shape=candidates.shape, initializer=tf.keras.initializers.Zeros(), trainable=False)
        identifiers_initial_value = tf.zeros((), dtype=identifiers.dtype)
        self._identifiers = self.add_weight(name='identifiers', dtype=identifiers.dtype, shape=identifiers.shape, initializer=tf.keras.initializers.Constant(value=identifiers_initial_value), trainable=False)
        self._candidates.assign(candidates)
        self._identifiers.assign(identifiers)
        self._reset_tf_function_cache()
        return self

    def call(self, queries: Union[tf.Tensor, Dict[Text, tf.Tensor]], k: Optional[int]=None, **kwargs) -> Tuple[tf.Tensor, tf.Tensor]:
        k = k if k is not None else self._k
        if self._candidates is None:
            raise ValueError('The `index` method must be called first to create the retrieval index.')
        if self._query_model is not None:
            queries = self._query_model(queries)
        scores = tf.matmul(queries, self._candidates, transpose_b=True)
        scores, indices = tf.math.top_k(scores, k=k)
        return (scores, tf.gather(self._identifiers, indices))

def call(self, queries: Union[tf.Tensor, Dict[Text, tf.Tensor]], k: Optional[int]=None, **kwargs) -> Tuple[tf.Tensor, tf.Tensor]:
    k = k if k is not None else self._k
    if self._candidates is None:
        raise ValueError('The `index` method must be called first to create the retrieval index.')
    if self._query_model is not None:
        queries = self._query_model(queries)
    scores = tf.matmul(queries, self._candidates, transpose_b=True)
    scores, indices = tf.math.top_k(scores, k=k)
    return (scores, tf.gather(self._identifiers, indices))

@tf.keras.utils.register_keras_serializable()
class GCN(tf.keras.layers.Layer):

    def __init__(self, units: int, residual=False, use_bias=False, activation='relu', kernel_initializer='truncated_normal', kernel_regularizer=None, bias_initializer='zeros', bias_regularizer=None, **kwargs):
        super().__init__(**kwargs)
        self._units = units
        self._residual = residual
        self._use_bias = use_bias
        self._kernel_initializer = tf.keras.initializers.get(kernel_initializer)
        self._kernel_regularizer = tf.keras.regularizers.get(kernel_regularizer)
        self._bias_initializer = tf.keras.initializers.get(bias_initializer)
        self._bias_regularizer = tf.keras.regularizers.get(bias_regularizer)
        self._kernel_activation = tf.keras.activations.get(activation)

    def build(self, input_shape):
        self._kernel = tf.keras.layers.Dense(self._units, activation=self._kernel_activation, kernel_initializer=self._kernel_initializer, kernel_regularizer=self._kernel_regularizer, bias_initializer=self._bias_initializer, bias_regularizer=self._bias_regularizer, use_bias=self._use_bias)
        self.built = True

    def call(self, features, adj, **kwargs):
        if isinstance(adj, tf.SparseTensor):
            agg_embeddings = tf.sparse.sparse_dense_matmul(adj, features)
        else:
            agg_embeddings = tf.linalg.matmul(adj, features)
        outputs = self._kernel(agg_embeddings)
        if self._residual is True:
            outputs += features
        return outputs

    def get_config(self):
        config = {'units': self._units, 'use_bias': self._use_bias, 'activation': tf.keras.activations.serialize(self._kernel_activation), 'kernel_initializer': tf.keras.initializers.serialize(self._kernel_initializer), 'kernel_regularizer': tf.keras.regularizers.serialize(self._kernel_regularizer), 'bias_initializer': tf.keras.initializers.serialize(self._bias_initializer), 'bias_regularizer': tf.keras.regularizers.serialize(self._bias_regularizer)}
        base_config = super(GCN, self).get_config()
        return {**base_config, **config}

def call(self, features, adj, **kwargs):
    if isinstance(adj, tf.SparseTensor):
        agg_embeddings = tf.sparse.sparse_dense_matmul(adj, features)
    else:
        agg_embeddings = tf.linalg.matmul(adj, features)
    outputs = self._kernel(agg_embeddings)
    if self._residual is True:
        outputs += features
    return outputs

def _gather_elements_along_row(data: tf.Tensor, column_indices: tf.Tensor) -> tf.Tensor:
    """与factorized_top_k中_take_long_axis相同"""
    with tf.control_dependencies([tf.assert_equal(tf.shape(data)[0], tf.shape(column_indices)[0])]):
        num_row = tf.shape(data)[0]
        num_column = tf.shape(data)[1]
        num_gathered = tf.shape(column_indices)[1]
        row_indices = tf.tile(tf.expand_dims(tf.range(num_row), -1), [1, num_gathered])
        flat_data = tf.reshape(data, [-1])
        flat_indices = tf.reshape(row_indices * num_column + column_indices, [-1])
        return tf.reshape(tf.gather(flat_data, flat_indices), [num_row, num_gathered])

class HardNegativeMining(tf.keras.layers.Layer):
    """Hard Negative"""

    def __init__(self, num_hard_negatives: int, **kwargs):
        super(HardNegativeMining, self).__init__(**kwargs)
        self._num_hard_negatives = num_hard_negatives

    def call(self, logits: tf.Tensor, labels: tf.Tensor) -> Tuple[tf.Tensor, tf.Tensor]:
        num_sampled = tf.minimum(self._num_hard_negatives + 1, tf.shape(logits)[1])
        _, indices = tf.nn.top_k(logits + labels * MAX_FLOAT, k=num_sampled, sorted=False)
        logits = _gather_elements_along_row(logits, indices)
        labels = _gather_elements_along_row(labels, indices)
        return (logits, labels)

def call(self, logits: tf.Tensor, labels: tf.Tensor) -> Tuple[tf.Tensor, tf.Tensor]:
    num_sampled = tf.minimum(self._num_hard_negatives + 1, tf.shape(logits)[1])
    _, indices = tf.nn.top_k(logits + labels * MAX_FLOAT, k=num_sampled, sorted=False)
    logits = _gather_elements_along_row(logits, indices)
    labels = _gather_elements_along_row(labels, indices)
    return (logits, labels)

class RemoveAccidentalNegative(tf.keras.layers.Layer):

    def call(self, logits: tf.Tensor, labels: tf.Tensor, identifiers: tf.Tensor) -> tf.Tensor:
        """Zeros logits of accidental negatives
        Args:
            logits: [batch_size, num_candidates] 2D tensor
            labels: [batch_size, num_candidates] one-hot 2D tensor
            identifiers: [num_candidates] candidates identifiers tensor
        Returns:
            logits: Modified logits.
        """
        identifiers = tf.expand_dims(identifiers, 1)
        positive_indices = tf.math.argmax(labels, axis=1)
        positive_identifier = tf.gather(identifiers, positive_indices)
        duplicate = tf.equal(positive_identifier, tf.transpose(identifiers))
        duplicate = tf.cast(duplicate, labels.dtype)
        duplicate = duplicate - labels
        return logits + duplicate * MIN_FLOAT

def call(self, logits: tf.Tensor, labels: tf.Tensor, identifiers: tf.Tensor) -> tf.Tensor:
    """Zeros logits of accidental negatives
        Args:
            logits: [batch_size, num_candidates] 2D tensor
            labels: [batch_size, num_candidates] one-hot 2D tensor
            identifiers: [num_candidates] candidates identifiers tensor
        Returns:
            logits: Modified logits.
        """
    identifiers = tf.expand_dims(identifiers, 1)
    positive_indices = tf.math.argmax(labels, axis=1)
    positive_identifier = tf.gather(identifiers, positive_indices)
    duplicate = tf.equal(positive_identifier, tf.transpose(identifiers))
    duplicate = tf.cast(duplicate, labels.dtype)
    duplicate = duplicate - labels
    return logits + duplicate * MIN_FLOAT

@tf.keras.utils.register_keras_serializable()
class CIN(tf.keras.layers.Layer):
    """ Compressed Interaction Network in xDeepFM """

    def __init__(self, feature_map: Optional[int]=3, use_bias: bool=False, activation: Union[Text, None, tf.keras.layers.Layer]='sigmoid', kernel_init: Union[Text, tf.keras.initializers.Initializer]='truncated_normal', kernel_regu: Union[Text, None, tf.keras.regularizers.Regularizer]=None, bias_init: Union[Text, tf.keras.initializers.Initializer]='zeros', bias_regu: Union[Text, None, tf.keras.regularizers.Regularizer]=None, **kwargs):
        super(CIN, self).__init__(**kwargs)
        self._feature_map = feature_map
        self._use_bias = use_bias
        if isinstance(activation, tf.keras.layers.Layer):
            self._activation = activation
        elif isinstance(activation, str):
            self._activation = tf.keras.activations.get(activation)
        else:
            self._activation = None
        self._kernel_init = tf.keras.initializers.get(kernel_init)
        self._kernel_regu = tf.keras.regularizers.get(kernel_regu)
        self._bias_init = tf.keras.initializers.get(bias_init)
        self._bias_regu = tf.keras.regularizers.get(bias_regu)

    def build(self, input_shape):
        if not isinstance(input_shape, tuple):
            raise ValueError("`CIN` layer's inputs type should be `tuple`.Got `CIN` layer's inputs type = `{}`".format(type(input_shape)))
        if len(input_shape) != 2:
            raise ValueError('`CIN` Layer inputs tuple length should be 2.Got `length` = {}'.format(len(input_shape)))
        x0_shape, x_shape = input_shape
        self._x0_fields = x0_shape[1]
        self._x_fields = x_shape[1]
        self._kernel = self.add_weight(shape=(1, self._x0_fields * self._x_fields, self._feature_map), initializer=self._kernel_init, regularizer=self._kernel_regu, trainable=True, name='kernel')
        if self._use_bias is True:
            self._bias = self.add_weight(shape=(self._feature_map,), initializer=self._bias_init, regularizer=self._bias_regu, trainable=True, name='bias')
        self.built = True

    def call(self, inputs: Tuple[tf.Tensor, tf.Tensor], **kwargs):
        x0, x = inputs
        if tf.keras.backend.ndim(x0) != 3 or tf.keras.backend.ndim(x) != 3:
            raise ValueError('`x0` and `x` dim should be 3.Got `x0` dim = {}, `x` dim = {}'.format(tf.keras.backend.ndim(x0), tf.keras.backend.ndim(x)))
        field_dim = x0.shape[-1]
        x0 = tf.split(x0, field_dim, axis=-1)
        x = tf.split(x, field_dim, axis=-1)
        outer = tf.matmul(x0, x, transpose_b=True)
        outer = tf.reshape(outer, shape=[field_dim, -1, self._x0_fields * self._x_fields])
        outer = tf.transpose(outer, perm=[1, 0, 2])
        conv_out = tf.nn.conv1d(outer, self._kernel, stride=1, padding='VALID')
        if self._use_bias is True:
            conv_out = tf.nn.bias_add(conv_out, self._bias)
        outputs = self._activation(conv_out)
        return tf.transpose(outputs, perm=[0, 2, 1])

    def get_config(self):
        config = {'feature_map': self._feature_map, 'use_bias': self._use_bias, 'activation': tf.keras.activations.serialize(self._activation), 'kernel_init': tf.keras.initializers.serialize(self._kernel_init), 'kernel_regu': tf.keras.regularizers.serialize(self._kernel_regu), 'bias_init': tf.keras.initializers.serialize(self._bias_init), 'bias_regu': tf.keras.regularizers.serialize(self._bias_regu)}
        base_config = super(CIN, self).get_config()
        return {**base_config, **config}

def call(self, inputs: Tuple[tf.Tensor, tf.Tensor], **kwargs):
    x0, x = inputs
    if tf.keras.backend.ndim(x0) != 3 or tf.keras.backend.ndim(x) != 3:
        raise ValueError('`x0` and `x` dim should be 3.Got `x0` dim = {}, `x` dim = {}'.format(tf.keras.backend.ndim(x0), tf.keras.backend.ndim(x)))
    field_dim = x0.shape[-1]
    x0 = tf.split(x0, field_dim, axis=-1)
    x = tf.split(x, field_dim, axis=-1)
    outer = tf.matmul(x0, x, transpose_b=True)
    outer = tf.reshape(outer, shape=[field_dim, -1, self._x0_fields * self._x_fields])
    outer = tf.transpose(outer, perm=[1, 0, 2])
    conv_out = tf.nn.conv1d(outer, self._kernel, stride=1, padding='VALID')
    if self._use_bias is True:
        conv_out = tf.nn.bias_add(conv_out, self._bias)
    outputs = self._activation(conv_out)
    return tf.transpose(outputs, perm=[0, 2, 1])

@tf.keras.utils.register_keras_serializable()
class PositionWiseFeedForward(Layer):

    def __init__(self, model_dim, inner_dim, trainable=True, **kwargs):
        self._model_dim = model_dim
        self._inner_dim = inner_dim
        self._trainable = trainable
        super(PositionWiseFeedForward, self).__init__(**kwargs)

    def build(self, input_shape):
        self.weights_inner = self.add_weight(shape=(input_shape[-1], self._inner_dim), initializer='glorot_uniform', trainable=self._trainable, name='weights_inner')
        self.weights_out = self.add_weight(shape=(self._inner_dim, self._model_dim), initializer='glorot_uniform', trainable=self._trainable, name='weights_out')
        self.bias_inner = self.add_weight(shape=(self._inner_dim,), initializer='uniform', trainable=self._trainable, name='bias_inner')
        self.bias_out = self.add_weight(shape=(self._model_dim,), initializer='uniform', trainable=self._trainable, name='bias_out')
        super(PositionWiseFeedForward, self).build(input_shape)

    def call(self, inputs, **kwargs):
        if K.dtype(inputs) != 'float32':
            inputs = K.cast(inputs, 'float32')
        inner_out = K.relu(K.dot(inputs, self.weights_inner) + self.bias_inner)
        outputs = K.dot(inner_out, self.weights_out) + self.bias_out
        return outputs

    def compute_output_shape(self, input_shape):
        return self._model_dim

def call(self, inputs, **kwargs):
    if K.dtype(inputs) != 'float32':
        inputs = K.cast(inputs, 'float32')
    inner_out = K.relu(K.dot(inputs, self.weights_inner) + self.bias_inner)
    outputs = K.dot(inner_out, self.weights_out) + self.bias_out
    return outputs

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

class Noam(Callback):

    def __init__(self, model_dim, step_num=0, warmup_steps=4000, verbose=False):
        self._model_dim = model_dim
        self._step_num = step_num
        self._warmup_steps = warmup_steps
        self.verbose = verbose
        super(Noam, self).__init__()

    def on_train_begin(self, logs=None):
        logs = logs or {}
        init_lr = self._model_dim ** (-0.5) * self._warmup_steps ** (-1.5)
        K.set_value(self.model.optimizer.lr, init_lr)

    def on_batch_end(self, epoch, logs=None):
        logs = logs or {}
        self._step_num += 1
        lrate = self._model_dim ** (-0.5) * K.minimum(self._step_num ** (-0.5), self._step_num * self._warmup_steps ** (-1.5))
        K.set_value(self.model.optimizer.lr, lrate)

    def on_epoch_begin(self, epoch, logs=None):
        if self.verbose:
            lrate = K.get_value(self.model.optimizer.lr)
            print(f'epoch {epoch} lr: {lrate}')

    def on_epoch_end(self, epoch, logs=None):
        logs = logs or {}
        logs['lr'] = K.get_value(self.model.optimizer.lr)

def on_train_begin(self, logs=None):
    logs = logs or {}
    init_lr = self._model_dim ** (-0.5) * self._warmup_steps ** (-1.5)
    K.set_value(self.model.optimizer.lr, init_lr)

def on_batch_end(self, epoch, logs=None):
    logs = logs or {}
    self._step_num += 1
    lrate = self._model_dim ** (-0.5) * K.minimum(self._step_num ** (-0.5), self._step_num * self._warmup_steps ** (-1.5))
    K.set_value(self.model.optimizer.lr, lrate)

@tf.keras.utils.register_keras_serializable()
class Embedding(tf.keras.layers.Layer):

    def __init__(self, vocab_size, model_dim, **kwargs):
        self._vocab_size = vocab_size
        self._model_dim = model_dim
        super(Embedding, self).__init__(**kwargs)

    def build(self, input_shape):
        self.embeddings = self.add_weight(shape=(self._vocab_size, self._model_dim), initializer='glorot_uniform', name='embeddings')
        super(Embedding, self).build(input_shape)

    def call(self, inputs, **kwargs):
        if K.dtype(inputs) != 'int32':
            inputs = K.cast(inputs, 'int32')
        embeddings = K.gather(self.embeddings, inputs)
        embeddings *= self._model_dim ** 0.5
        return embeddings

    def compute_output_shape(self, input_shape):
        return input_shape + (self._model_dim,)

def call(self, inputs, **kwargs):
    if K.dtype(inputs) != 'int32':
        inputs = K.cast(inputs, 'int32')
    embeddings = K.gather(self.embeddings, inputs)
    embeddings *= self._model_dim ** 0.5
    return embeddings

@tf.keras.utils.register_keras_serializable()
class ScaledDotProductAttention(tf.keras.layers.Layer):

    def __init__(self, masking=True, future=False, dropout_rate=0.0, **kwargs):
        self._masking = masking
        self._future = future
        self._dropout_rate = dropout_rate
        self._masking_num = -2 ** 32 + 1
        super(ScaledDotProductAttention, self).__init__(**kwargs)

    def mask(self, inputs, masks):
        masks = K.cast(masks, 'float32')
        masks = K.tile(masks, [K.shape(inputs)[0] // K.shape(masks)[0], 1])
        masks = K.expand_dims(masks, 1)
        outputs = inputs + masks * self._masking_num
        return outputs

    def future_mask(self, inputs):
        diag_vals = tf.ones_like(inputs[0, :, :])
        tril = tf.linalg.LinearOperatorLowerTriangular(diag_vals).to_dense()
        future_masks = tf.tile(tf.expand_dims(tril, 0), [tf.shape(inputs)[0], 1, 1])
        paddings = tf.ones_like(future_masks) * self._masking_num
        outputs = tf.where(tf.equal(future_masks, 0), paddings, inputs)
        return outputs

    def call(self, inputs, **kwargs):
        if self._masking:
            assert len(inputs) == 4, 'inputs should be set [queries, keys, values, masks].'
            queries, keys, values, masks = inputs
        else:
            assert len(inputs) == 3, 'inputs should be set [queries, keys, values].'
            queries, keys, values = inputs
        if K.dtype(queries) != 'float32':
            queries = K.cast(queries, 'float32')
        if K.dtype(keys) != 'float32':
            keys = K.cast(keys, 'float32')
        if K.dtype(values) != 'float32':
            values = K.cast(values, 'float32')
        matmul = K.batch_dot(queries, tf.transpose(keys, [0, 2, 1]))
        scaled_matmul = matmul / int(queries.shape[-1]) ** 0.5
        if self._masking:
            scaled_matmul = self.mask(scaled_matmul, masks)
        if self._future:
            scaled_matmul = self.future_mask(scaled_matmul)
        softmax_out = K.softmax(scaled_matmul)
        out = K.dropout(softmax_out, self._dropout_rate)
        outputs = K.batch_dot(out, values)
        return outputs

    def compute_output_shape(self, input_shape):
        return input_shape

def mask(self, inputs, masks):
    masks = K.cast(masks, 'float32')
    masks = K.tile(masks, [K.shape(inputs)[0] // K.shape(masks)[0], 1])
    masks = K.expand_dims(masks, 1)
    outputs = inputs + masks * self._masking_num
    return outputs

def future_mask(self, inputs):
    diag_vals = tf.ones_like(inputs[0, :, :])
    tril = tf.linalg.LinearOperatorLowerTriangular(diag_vals).to_dense()
    future_masks = tf.tile(tf.expand_dims(tril, 0), [tf.shape(inputs)[0], 1, 1])
    paddings = tf.ones_like(future_masks) * self._masking_num
    outputs = tf.where(tf.equal(future_masks, 0), paddings, inputs)
    return outputs

def call(self, inputs, **kwargs):
    if self._masking:
        assert len(inputs) == 4, 'inputs should be set [queries, keys, values, masks].'
        queries, keys, values, masks = inputs
    else:
        assert len(inputs) == 3, 'inputs should be set [queries, keys, values].'
        queries, keys, values = inputs
    if K.dtype(queries) != 'float32':
        queries = K.cast(queries, 'float32')
    if K.dtype(keys) != 'float32':
        keys = K.cast(keys, 'float32')
    if K.dtype(values) != 'float32':
        values = K.cast(values, 'float32')
    matmul = K.batch_dot(queries, tf.transpose(keys, [0, 2, 1]))
    scaled_matmul = matmul / int(queries.shape[-1]) ** 0.5
    if self._masking:
        scaled_matmul = self.mask(scaled_matmul, masks)
    if self._future:
        scaled_matmul = self.future_mask(scaled_matmul)
    softmax_out = K.softmax(scaled_matmul)
    out = K.dropout(softmax_out, self._dropout_rate)
    outputs = K.batch_dot(out, values)
    return outputs

@tf.keras.utils.register_keras_serializable()
class MultiHeadAttention(tf.keras.layers.Layer):

    def __init__(self, n_heads, head_dim, dropout_rate=0.1, masking=True, future=False, trainable=True, **kwargs):
        self._n_heads = n_heads
        self._head_dim = head_dim
        self._dropout_rate = dropout_rate
        self._masking = masking
        self._future = future
        self._trainable = trainable
        super(MultiHeadAttention, self).__init__(**kwargs)

    def build(self, input_shape):
        self._weights_queries = self.add_weight(shape=(input_shape[0][-1], self._n_heads * self._head_dim), initializer='glorot_uniform', trainable=self._trainable, name='weights_queries')
        self._weights_keys = self.add_weight(shape=(input_shape[1][-1], self._n_heads * self._head_dim), initializer='glorot_uniform', trainable=self._trainable, name='weights_keys')
        self._weights_values = self.add_weight(shape=(input_shape[2][-1], self._n_heads * self._head_dim), initializer='glorot_uniform', trainable=self._trainable, name='weights_values')
        super(MultiHeadAttention, self).build(input_shape)

    def call(self, inputs, **kwargs):
        if self._masking:
            assert len(inputs) == 4, 'inputs should be set [queries, keys, values, masks].'
            queries, keys, values, masks = inputs
        else:
            assert len(inputs) == 3, 'inputs should be set [queries, keys, values].'
            queries, keys, values = inputs
        queries_linear = K.dot(queries, self._weights_queries)
        keys_linear = K.dot(keys, self._weights_keys)
        values_linear = K.dot(values, self._weights_values)
        queries_multi_heads = tf.concat(tf.split(queries_linear, self._n_heads, axis=2), axis=0)
        keys_multi_heads = tf.concat(tf.split(keys_linear, self._n_heads, axis=2), axis=0)
        values_multi_heads = tf.concat(tf.split(values_linear, self._n_heads, axis=2), axis=0)
        if self._masking:
            att_inputs = [queries_multi_heads, keys_multi_heads, values_multi_heads, masks]
        else:
            att_inputs = [queries_multi_heads, keys_multi_heads, values_multi_heads]
        attention = ScaledDotProductAttention(masking=self._masking, future=self._future, dropout_rate=self._dropout_rate)
        att_out = attention(att_inputs)
        outputs = tf.concat(tf.split(att_out, self._n_heads, axis=0), axis=2)
        return outputs

    def compute_output_shape(self, input_shape):
        return input_shape

def call(self, inputs, **kwargs):
    if self._masking:
        assert len(inputs) == 4, 'inputs should be set [queries, keys, values, masks].'
        queries, keys, values, masks = inputs
    else:
        assert len(inputs) == 3, 'inputs should be set [queries, keys, values].'
        queries, keys, values = inputs
    queries_linear = K.dot(queries, self._weights_queries)
    keys_linear = K.dot(keys, self._weights_keys)
    values_linear = K.dot(values, self._weights_values)
    queries_multi_heads = tf.concat(tf.split(queries_linear, self._n_heads, axis=2), axis=0)
    keys_multi_heads = tf.concat(tf.split(keys_linear, self._n_heads, axis=2), axis=0)
    values_multi_heads = tf.concat(tf.split(values_linear, self._n_heads, axis=2), axis=0)
    if self._masking:
        att_inputs = [queries_multi_heads, keys_multi_heads, values_multi_heads, masks]
    else:
        att_inputs = [queries_multi_heads, keys_multi_heads, values_multi_heads]
    attention = ScaledDotProductAttention(masking=self._masking, future=self._future, dropout_rate=self._dropout_rate)
    att_out = attention(att_inputs)
    outputs = tf.concat(tf.split(att_out, self._n_heads, axis=0), axis=2)
    return outputs

class MMoE(object):

    def __init__(self, feature_columns, num_tasks, num_experts, expert_hidden_units, task_hidden_units, task_hidden_activation=tf.nn.relu, task_batch_normalization=False, task_dropout=None, expert_hidden_activation=tf.nn.relu, expert_batch_normalization=False, expert_dropout=None):
        self._columns = feature_columns
        self._num_tasks = num_tasks
        self._num_experts = num_experts
        self._expert_hidden_units = expert_hidden_units
        self._task_hidden_units = task_hidden_units
        self._task_hidden_activation = task_hidden_activation
        self._task_batch_norm = task_batch_normalization
        self._task_dropout = task_dropout
        self._expert_hidden_activation = expert_hidden_activation
        self._expert_batch_norm = expert_batch_normalization
        self._expert_dropout = expert_dropout

    def __call__(self, *args, **kwargs):
        return self.call(*args, **kwargs)

    def gating_network(self, inputs):
        """
        Gating network: y = SoftMax(W * inputs)
        """
        x = tf.layers.dense(inputs, units=self._num_experts, use_bias=False)
        return tf.nn.softmax(x)

    def call(self, features):
        inputs = tf.feature_column.input_layer(features, self._columns)
        with tf.variable_scope('mixture_of_experts'):
            experts_outputs = []
            for _ in range(self._num_experts):
                x = dnn(inputs, self._expert_hidden_units, activation=self._expert_hidden_activation, batch_normalization=self._expert_batch_norm, dropout=self._expert_dropout)
                experts_outputs.append(x)
            moe_outputs = tf.stack(experts_outputs, axis=1)
        with tf.variable_scope('multi_gate'):
            mg_outputs = []
            for _ in range(self._num_experts):
                gate = self.gating_network(inputs)
                gate = tf.expand_dims(gate, axis=1)
                output = tf.linalg.matmul(gate, moe_outputs)
                mg_outputs.append(tf.squeeze(output, axis=1))
        outputs = []
        for idx in range(self._num_tasks):
            with tf.variable_scope('task{}'.format(idx)):
                x = dnn(mg_outputs[idx], self._task_hidden_units + [1], activation=self._task_hidden_activation, batch_normalization=self._task_batch_norm, dropout=self._task_dropout)
                outputs.append(x)
        return outputs

def gating_network(self, inputs):
    """
        Gating network: y = SoftMax(W * inputs)
        """
    x = tf.layers.dense(inputs, units=self._num_experts, use_bias=False)
    return tf.nn.softmax(x)

def dnn(inputs, hidden_units, activation=tf.nn.relu, batch_normalization=False, dropout=None, **kwargs):
    x = inputs
    for units in hidden_units[:-1]:
        x = tf.layers.dense(x, units, activation, **kwargs)
        if batch_normalization is True:
            x = tf.nn.batch_normalization(x)
        if dropout is not None:
            x = tf.nn.dropout(x, rate=dropout)
    outputs = tf.layers.dense(x, hidden_units[-1], **kwargs)
    return outputs

