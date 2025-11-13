# Cluster 20

def build_columns():
    return [tf.feature_column.numeric_column('C{}'.format(i)) for i in range(EXAMPLE_DIM)]

class TestMixtureOfExperts(tf.test.TestCase, parameterized.TestCase):

    @parameterized.parameters(32, 64, 128, 512)
    def test_mmoe(self, batch_size):

        def build_columns():
            return [tf.feature_column.numeric_column('C{}'.format(i)) for i in range(100)]
        columns = build_columns()
        model = MMoE(columns, num_tasks=2, num_experts=2, task_hidden_units=[32, 10], expert_hidden_units=[64, 32])
        dataset = SyntheticForMultiTask(5000)
        with self.session() as sess:
            iterator = tf.data.make_one_shot_iterator(dataset.input_fn(batch_size=batch_size))
            x, y = iterator.get_next()
            y_pred = model(x)
            sess.run(tf.global_variables_initializer())
            a = sess.run(y_pred[0])
            b = sess.run(y_pred[1])
            self.assertAllEqual(len(y_pred), 2)
            self.assertAllEqual(a.shape, (batch_size, 1))
            self.assertAllEqual(b.shape, (batch_size, 1))

def build_columns():
    return [tf.feature_column.numeric_column('C{}'.format(i)) for i in range(100)]

class TestESMM(tf.test.TestCase, parameterized.TestCase):

    @parameterized.parameters(32, 64, 128, 512)
    def test_mmoe(self, batch_size):

        def build_columns():
            return [tf.feature_column.numeric_column('C{}'.format(i)) for i in range(100)]
        columns = build_columns()
        model = ESMM(columns, hidden_units=[32, 10])
        dataset = SyntheticForMultiTask(5000)
        with self.session() as sess:
            iterator = tf.data.make_one_shot_iterator(dataset.input_fn(batch_size=batch_size))
            x, y = iterator.get_next()
            p_cvr, p_ctr, p_ctcvr = model(x)
            sess.run(tf.global_variables_initializer())
            p_cvr = sess.run(p_cvr)
            p_ctr = sess.run(p_ctr)
            p_ctcvr = sess.run(p_ctcvr)
            self.assertAllEqual(p_cvr.shape, (batch_size, 1))
            self.assertAllEqual(p_ctr.shape, (batch_size, 1))
            self.assertAllEqual(p_ctcvr.shape, (batch_size, 1))

def build_columns():
    return [tf.feature_column.numeric_column('C{}'.format(i)) for i in range(100)]

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

class Faiss(TopK):
    """(Facebook)Faiss retrieval index for a factorized retrieval model"""

    def __init__(self, k: int=10, query_model: Optional[tf.keras.Model]=None, nlist: Optional[int]=1, nprobe: Optional[int]=1, normalize: bool=False, *args, **kwargs):
        super().__init__(k, *args, **kwargs)
        self._query_model = query_model
        self._nlist = nlist
        self._nprobe = nprobe
        self._normalize = normalize

        def build_searcher(candidates: Union[np.ndarray, tf.Tensor], identifiers: Optional[Union[np.ndarray, tf.Tensor]]=None) -> Union[faiss.swigfaiss.IndexIDMap, faiss.swigfaiss.IndexIVFFlat]:
            if isinstance(candidates, tf.Tensor):
                candidates = candidates.numpy()
            if candidates.dtype != 'float32':
                candidates = candidates.astype(np.float32)
            d = candidates.shape[1]
            quantizer = faiss.IndexFlatIP(d)
            index = faiss.IndexIVFFlat(quantizer, d, self._nlist, faiss.METRIC_INNER_PRODUCT)
            if self._normalize is True:
                faiss.normalize_L2(candidates)
            index.train(candidates)
            if identifiers is not None:
                if isinstance(identifiers, tf.Tensor):
                    identifiers = identifiers.numpy()
                if identifiers.dtype != np.int64:
                    try:
                        identifiers = identifiers.astype(np.int64)
                    except:
                        raise ValueError('`identifiers` dtype must be `int64`.Got `dtype` = {}'.format(identifiers.dtype))
                index.add_with_ids(candidates, identifiers)
            else:
                index.add(candidates)
            return index
        self._build_searcher = build_searcher
        self._searcher = None
        self._identifiers = None

    def index(self, candidates: Union[tf.Tensor, tf.data.Dataset], identifiers: Optional[Union[tf.Tensor, tf.data.Dataset]]=None) -> 'Faiss':
        if isinstance(candidates, tf.data.Dataset):
            candidates = tf.concat(list(candidates), axis=0)
        if identifiers is None:
            identifiers = tf.range(candidates.shape[0])
        if isinstance(identifiers, tf.data.Dataset):
            identifiers = tf.concat(list(identifiers), axis=0)
        if tf.rank(candidates) != 2:
            raise ValueError('`candidates` ndim should be 2. Got `ndim` = {}'.format(tf.rank(candidates)))
        if identifiers.dtype not in ('int8', 'int16', 'int32', 'int64'):
            self._searcher = self._build_searcher(candidates, identifiers=None)
            identifiers_initial_value = tf.zeros((), dtype=identifiers.dtype)
            self._identifiers = self.add_weight(name='identifiers', dtype=identifiers.dtype, shape=identifiers.shape, initializer=tf.keras.initializers.Constant(value=identifiers_initial_value), trainable=False)
            self._identifiers.assign(identifiers)
        else:
            self._searcher = self._build_searcher(candidates, identifiers=identifiers)
        self._reset_tf_function_cache()
        return self

    def call(self, queries: Union[tf.Tensor, Dict[Text, tf.Tensor]], k: Optional[int]=None) -> Tuple[tf.Tensor, tf.Tensor]:
        k = k if k is not None else self._k
        if self._searcher is None:
            raise ValueError('The `index` method must be called first to create the retrieval index.')
        if self._query_model is not None:
            queries = self._query_model(queries)
        if not isinstance(queries, tf.Tensor):
            raise ValueError(f'Queries must be a tensor, got {type(queries)}.')

        def _search(queries, k):
            queries = tf.make_ndarray(tf.make_tensor_proto(queries))
            if self._normalize is True:
                faiss.normalize_L2(queries)
            self._searcher.nprobe = self._nprobe
            distances, indices = self._searcher.search(queries, int(k))
            return (distances, indices)
        distances, indices = tf.py_function(_search, [queries, k], [tf.float32, tf.int32])
        if self._identifiers is None:
            return (distances, indices)
        return (distances, tf.gather(self._identifiers, indices))

def index(self, candidates: Union[tf.Tensor, tf.data.Dataset], identifiers: Optional[Union[tf.Tensor, tf.data.Dataset]]=None) -> 'Faiss':
    if isinstance(candidates, tf.data.Dataset):
        candidates = tf.concat(list(candidates), axis=0)
    if identifiers is None:
        identifiers = tf.range(candidates.shape[0])
    if isinstance(identifiers, tf.data.Dataset):
        identifiers = tf.concat(list(identifiers), axis=0)
    if tf.rank(candidates) != 2:
        raise ValueError('`candidates` ndim should be 2. Got `ndim` = {}'.format(tf.rank(candidates)))
    if identifiers.dtype not in ('int8', 'int16', 'int32', 'int64'):
        self._searcher = self._build_searcher(candidates, identifiers=None)
        identifiers_initial_value = tf.zeros((), dtype=identifiers.dtype)
        self._identifiers = self.add_weight(name='identifiers', dtype=identifiers.dtype, shape=identifiers.shape, initializer=tf.keras.initializers.Constant(value=identifiers_initial_value), trainable=False)
        self._identifiers.assign(identifiers)
    else:
        self._searcher = self._build_searcher(candidates, identifiers=identifiers)
    self._reset_tf_function_cache()
    return self

def call(self, queries: Union[tf.Tensor, Dict[Text, tf.Tensor]], k: Optional[int]=None) -> Tuple[tf.Tensor, tf.Tensor]:
    k = k if k is not None else self._k
    if self._searcher is None:
        raise ValueError('The `index` method must be called first to create the retrieval index.')
    if self._query_model is not None:
        queries = self._query_model(queries)
    if not isinstance(queries, tf.Tensor):
        raise ValueError(f'Queries must be a tensor, got {type(queries)}.')

    def _search(queries, k):
        queries = tf.make_ndarray(tf.make_tensor_proto(queries))
        if self._normalize is True:
            faiss.normalize_L2(queries)
        self._searcher.nprobe = self._nprobe
        distances, indices = self._searcher.search(queries, int(k))
        return (distances, indices)
    distances, indices = tf.py_function(_search, [queries, k], [tf.float32, tf.int32])
    if self._identifiers is None:
        return (distances, indices)
    return (distances, tf.gather(self._identifiers, indices))

@tf.keras.utils.register_keras_serializable()
class FM(tf.keras.layers.Layer):
    """ Factorization Machine """

    def __init__(self, **kwargs):
        super(FM, self).__init__(**kwargs)

    def build(self, input_shape):
        self._linear = tf.keras.layers.Dense(units=1, kernel_initializer='zeros', name='linear')
        self.built = True

    def call(self, sparse_inputs, embedding_inputs=None, **kwargs):
        if embedding_inputs is None:
            return self._linear(sparse_inputs)
        x_sum = tf.reduce_sum(embedding_inputs, axis=1)
        x_square_sum = tf.reduce_sum(tf.pow(embedding_inputs, 2), axis=1)
        interaction = 0.5 * tf.reduce_sum(tf.subtract(tf.pow(x_sum, 2), x_square_sum), axis=1, keepdims=True)
        return self._linear(sparse_inputs) + interaction

def call(self, sparse_inputs, embedding_inputs=None, **kwargs):
    if embedding_inputs is None:
        return self._linear(sparse_inputs)
    x_sum = tf.reduce_sum(embedding_inputs, axis=1)
    x_square_sum = tf.reduce_sum(tf.pow(embedding_inputs, 2), axis=1)
    interaction = 0.5 * tf.reduce_sum(tf.subtract(tf.pow(x_sum, 2), x_square_sum), axis=1, keepdims=True)
    return self._linear(sparse_inputs) + interaction

@tf.keras.utils.register_keras_serializable()
class Cross(tf.keras.layers.Layer):
    """ Cross net in Deep & Cross Network (DCN) """

    def __init__(self, projection_dim: Optional[int]=None, diag_scale: Optional[float]=0.0, use_bias: bool=True, kernel_init: Union[Text, tf.keras.initializers.Initializer]='truncated_normal', kernel_regu: Union[Text, None, tf.keras.regularizers.Regularizer]=None, bias_init: Union[Text, tf.keras.initializers.Initializer]='zeros', bias_regu: Union[Text, None, tf.keras.regularizers.Regularizer]=None, **kwargs):
        super(Cross, self).__init__(**kwargs)
        self._projection_dim = projection_dim
        self._diag_scale = diag_scale
        self._use_bias = use_bias
        self._kernel_init = tf.keras.initializers.get(kernel_init)
        self._kernel_regu = tf.keras.regularizers.get(kernel_regu)
        self._bias_init = tf.keras.initializers.get(bias_init)
        self._bias_regu = tf.keras.regularizers.get(bias_regu)
        assert self._diag_scale >= 0, ValueError('diag scale must be non-negative, got {}'.format(self._diag_scale))

    def build(self, input_shape):
        last_dim = input_shape[-1]
        if self._projection_dim is None:
            self._dense = tf.keras.layers.Dense(last_dim, kernel_initializer=self._kernel_init, kernel_regularizer=self._kernel_regu, bias_initializer=self._bias_init, bias_regularizer=self._bias_regu, use_bias=self._use_bias)
        else:
            if self._projection_dim < 0 or self._projection_dim > last_dim / 2:
                raise ValueError('`projection_dim` should be smaller than last_dim / 2 to improve the model efficiency, and should be positive. Got `projection_dim` {}, and last dimension of input {}'.format(self._projection_dim, last_dim))
            self._dense_u = tf.keras.layers.Dense(self._projection_dim, kernel_initializer=self._kernel_init, kernel_regularizer=self._kernel_regu, use_bias=False)
            self._dense_v = tf.keras.layers.Dense(last_dim, kernel_initializer=self._kernel_init, bias_initializer=self._bias_init, kernel_regularizer=self._kernel_regu, bias_regularizer=self._bias_regu, use_bias=self._use_bias)
        super(Cross, self).build(input_shape)

    def call(self, x0, x=None, **kwargs):
        if x is None:
            x = x0
        if x0.shape[-1] != x.shape[-1]:
            raise ValueError('`x0` and `x` dim mismatch. Got `x0` dim = {} and `x` dim = {}'.format(x0.shape[-1], x.shape[-1]))
        if self._projection_dim is None:
            prod_output = self._dense(x)
        else:
            prod_output = self._dense_v(self._dense_u(x))
        if self._diag_scale:
            prod_output = prod_output + self._diag_scale * x
        return x0 * prod_output + x

    def get_config(self):
        config = {'projection_dim': self._projection_dim, 'diag_scale': self._diag_scale, 'use_bias': self._use_bias, 'kernel_init': tf.keras.initializers.serialize(self._kernel_init), 'kernel_regu': tf.keras.regularizers.serialize(self._kernel_regu), 'bias_init': tf.keras.initializers.serialize(self._bias_init), 'bias_regu': tf.keras.regularizers.serialize(self._bias_regu)}
        base_config = super(Cross, self).get_config()
        return {**base_config, **config}

def call(self, x0, x=None, **kwargs):
    if x is None:
        x = x0
    if x0.shape[-1] != x.shape[-1]:
        raise ValueError('`x0` and `x` dim mismatch. Got `x0` dim = {} and `x` dim = {}'.format(x0.shape[-1], x.shape[-1]))
    if self._projection_dim is None:
        prod_output = self._dense(x)
    else:
        prod_output = self._dense_v(self._dense_u(x))
    if self._diag_scale:
        prod_output = prod_output + self._diag_scale * x
    return x0 * prod_output + x

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

@tf.keras.utils.register_keras_serializable()
class PositionEncoding(Layer):

    def __init__(self, model_dim, **kwargs):
        self._model_dim = model_dim
        super(PositionEncoding, self).__init__(**kwargs)

    def call(self, inputs, **kwargs):
        seq_length = inputs.shape[1]
        position_encodings = np.zeros((seq_length, self._model_dim))
        for pos in range(seq_length):
            for i in range(self._model_dim):
                position_encodings[pos, i] = pos / np.power(10000, (i - i % 2) / self._model_dim)
        position_encodings[:, 0::2] = np.sin(position_encodings[:, 0::2])
        position_encodings[:, 1::2] = np.cos(position_encodings[:, 1::2])
        position_encodings = K.cast(position_encodings, 'float32')
        return position_encodings

    def compute_output_shape(self, input_shape):
        return input_shape

def call(self, inputs, **kwargs):
    seq_length = inputs.shape[1]
    position_encodings = np.zeros((seq_length, self._model_dim))
    for pos in range(seq_length):
        for i in range(self._model_dim):
            position_encodings[pos, i] = pos / np.power(10000, (i - i % 2) / self._model_dim)
    position_encodings[:, 0::2] = np.sin(position_encodings[:, 0::2])
    position_encodings[:, 1::2] = np.cos(position_encodings[:, 1::2])
    position_encodings = K.cast(position_encodings, 'float32')
    return position_encodings

def fm(x):
    """
    Second order interaction in Factorization Machine
    :param x:
        type: tf.Tensor
        shape: (batch_size, num_features, embedding_dim)
    :return: tf.Tensor
    """
    if x.shape.rank != 3:
        raise ValueError('The rank of `x` should be 3. Got rank = {}.'.format(x.shape.rank))
    sum_square = tf.square(tf.reduce_sum(x, axis=1))
    square_sum = tf.reduce_sum(tf.square(x), axis=1)
    return 0.5 * tf.reduce_sum(tf.subtract(sum_square, square_sum), axis=1, keepdims=True)

class Cora(object):

    def __init__(self, extract_path='.'):
        self._download_url = 'https://linqs-data.soe.ucsc.edu/public/lbc/cora.tgz'
        self._extract_path = extract_path
        self._cora_path = os.path.join(extract_path, 'cora')
        self._cora_cites = os.path.join(self._cora_path, 'cora.cites')
        self._cora_content = os.path.join(self._cora_path, 'cora.content')
        if not os.path.exists(self._cora_cites) or not os.path.exists(self._cora_content):
            self._download()
        self._cora_classes = ['Case_Based', 'Genetic_Algorithms', 'Neural_Networks', 'Probabilistic_Methods', 'Reinforcement_Learning', 'Rule_Learning', 'Theory']

    @property
    def num_classes(self):
        return len(self._cora_classes)

    def _download(self, filename='cora.tgz'):
        import requests
        import tarfile
        r = requests.get(self._download_url)
        with open(filename, 'wb') as f:
            f.write(r.content)
        tarobj = tarfile.open(filename, 'r:gz')
        for tarinfo in tarobj:
            tarobj.extract(tarinfo.name, self._extract_path)
        tarobj.close()

    def load_content(self, normalize=True):
        content = np.genfromtxt(self._cora_content, dtype=np.str)
        ids, features, labels = (content[:, 0], content[:, 1:-1], content[:, -1])
        features = sp.csr_matrix(features, dtype=np.float32)
        if normalize is True:
            features /= features.sum(axis=1).reshape(-1, 1)
        return (ids, features, labels)

    def build_graph(self, nodes):
        idx_map = {int(j): i for i, j in enumerate(nodes)}
        edges_unordered = np.genfromtxt(self._cora_cites, dtype=np.int32)
        edges = np.array(list(map(idx_map.get, edges_unordered.flatten())), dtype=np.int32).reshape(edges_unordered.shape)
        graph = sp.coo_matrix((np.ones(edges.shape[0]), (edges[:, 0], edges[:, 1])), shape=(nodes.shape[0], nodes.shape[0]), dtype=np.float32)
        graph += graph.T - sp.diags(graph.diagonal())
        return graph

    @staticmethod
    def spectral_graph(graph):
        graph = graph + sp.eye(graph.shape[0])
        d = sp.diags(np.power(np.array(graph.sum(1)), -0.5).flatten(), 0)
        spectral_graph = graph.dot(d).transpose().dot(d).tocsr()
        return spectral_graph

    def sample_train_nodes(self, labels, num_per_class=20):
        train_nodes = []
        for cls in self._cora_classes:
            cls_index = np.where(labels == cls)[0]
            cls_sample = np.random.choice(cls_index, num_per_class, replace=False)
            train_nodes += cls_sample.tolist()
        return train_nodes

    def encode_labels(self, labels):
        labels_map = {}
        num_classes = len(self._cora_classes)
        for i, cls in enumerate(self._cora_classes):
            cls_label = np.zeros(shape=(num_classes,))
            cls_label[i] = 1.0
            labels_map[cls] = cls_label
        encoded_labels = list(map(labels_map.get, labels))
        return np.array(encoded_labels, dtype=np.int32)

    def split_labels(self, labels, num_valid_nodes=500):
        num_nodes = labels.shape[0]
        all_index = np.arange(num_nodes)
        train_index = self.sample_train_nodes(labels)
        valid_index = list(set(all_index) - set(train_index))
        valid_index, test_index = (valid_index[:num_valid_nodes], valid_index[num_valid_nodes:])
        encoded_labels = self.encode_labels(labels)

        def _sample_mask(index_ls):
            mask = np.zeros(num_nodes)
            mask[index_ls] = 1
            return np.array(mask, dtype=np.bool)

        def _get_labels(index_ls):
            _labels = np.zeros(encoded_labels.shape, dtype=np.int32)
            _labels[index_ls] = encoded_labels[index_ls]
            _mask = _sample_mask(index_ls)
            return (_labels, _mask)
        train_labels, train_mask = _get_labels(train_index)
        valid_labels, valid_mask = _get_labels(valid_index)
        test_labels, test_mask = _get_labels(test_index)
        return ((train_labels, train_mask), (valid_labels, valid_mask), (test_labels, test_mask))

def load_content(self, normalize=True):
    content = np.genfromtxt(self._cora_content, dtype=np.str)
    ids, features, labels = (content[:, 0], content[:, 1:-1], content[:, -1])
    features = sp.csr_matrix(features, dtype=np.float32)
    if normalize is True:
        features /= features.sum(axis=1).reshape(-1, 1)
    return (ids, features, labels)

def build_graph(self, nodes):
    idx_map = {int(j): i for i, j in enumerate(nodes)}
    edges_unordered = np.genfromtxt(self._cora_cites, dtype=np.int32)
    edges = np.array(list(map(idx_map.get, edges_unordered.flatten())), dtype=np.int32).reshape(edges_unordered.shape)
    graph = sp.coo_matrix((np.ones(edges.shape[0]), (edges[:, 0], edges[:, 1])), shape=(nodes.shape[0], nodes.shape[0]), dtype=np.float32)
    graph += graph.T - sp.diags(graph.diagonal())
    return graph

@staticmethod
def spectral_graph(graph):
    graph = graph + sp.eye(graph.shape[0])
    d = sp.diags(np.power(np.array(graph.sum(1)), -0.5).flatten(), 0)
    spectral_graph = graph.dot(d).transpose().dot(d).tocsr()
    return spectral_graph

def encode_labels(self, labels):
    labels_map = {}
    num_classes = len(self._cora_classes)
    for i, cls in enumerate(self._cora_classes):
        cls_label = np.zeros(shape=(num_classes,))
        cls_label[i] = 1.0
        labels_map[cls] = cls_label
    encoded_labels = list(map(labels_map.get, labels))
    return np.array(encoded_labels, dtype=np.int32)

def split_labels(self, labels, num_valid_nodes=500):
    num_nodes = labels.shape[0]
    all_index = np.arange(num_nodes)
    train_index = self.sample_train_nodes(labels)
    valid_index = list(set(all_index) - set(train_index))
    valid_index, test_index = (valid_index[:num_valid_nodes], valid_index[num_valid_nodes:])
    encoded_labels = self.encode_labels(labels)

    def _sample_mask(index_ls):
        mask = np.zeros(num_nodes)
        mask[index_ls] = 1
        return np.array(mask, dtype=np.bool)

    def _get_labels(index_ls):
        _labels = np.zeros(encoded_labels.shape, dtype=np.int32)
        _labels[index_ls] = encoded_labels[index_ls]
        _mask = _sample_mask(index_ls)
        return (_labels, _mask)
    train_labels, train_mask = _get_labels(train_index)
    valid_labels, valid_mask = _get_labels(valid_index)
    test_labels, test_mask = _get_labels(test_index)
    return ((train_labels, train_mask), (valid_labels, valid_mask), (test_labels, test_mask))

def _sample_mask(index_ls):
    mask = np.zeros(num_nodes)
    mask[index_ls] = 1
    return np.array(mask, dtype=np.bool)

def _get_labels(index_ls):
    _labels = np.zeros(encoded_labels.shape, dtype=np.int32)
    _labels[index_ls] = encoded_labels[index_ls]
    _mask = _sample_mask(index_ls)
    return (_labels, _mask)

