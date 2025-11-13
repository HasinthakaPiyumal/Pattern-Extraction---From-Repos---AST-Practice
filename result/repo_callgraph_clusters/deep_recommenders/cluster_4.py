# Cluster 4

class TopK(tf.keras.Model, abc.ABC):
    """TopK layer 接口
    注意，必须实现两个方法
    1、index: 创建索引
    2、call: 检索索引
    """

    def __init__(self, k: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._k = k

    @abc.abstractmethod
    def index(self, candidates: Union[tf.Tensor, tf.data.Dataset], identifiers: Optional[Union[tf.Tensor, tf.data.Dataset]]=None) -> 'TopK':
        """创建索引 
        args:
            candidates: 候选 embeddings
            identifiers: 候选 embeddings对应标识 (Opt)
        returns:
            Self.
        """
        raise NotImplementedError('Implementers must provide `index` method.')

    @abc.abstractmethod
    def call(self, queries: Union[tf.Tensor, Dict[Text, tf.Tensor]], k: Optional[int]=None, **kwargs) -> Tuple[tf.Tensor, tf.Tensor]:
        """检索索引
        args:
            queries: queries embeddings,
            k: 返回候选个数
        returns:
            Tuple(top k candidates scores, top k candidates indentifiers)
        """
        raise NotImplementedError()

    @tf.function
    def query_with_exclusions(self, queries: Union[tf.Tensor, Dict[Text, tf.Tensor]], exclusions: tf.Tensor, k: Optional[int]=None) -> Tuple[tf.Tensor, tf.Tensor]:
        """检索索引并过滤exclusions
        Args:
            queries: queries embeddings,
            exclusions: candidates identifiers. 从TopK的候选集中过滤指定的item.
            k: 返回候选个数
        Returns:
            Tuple(top k candidates scores, top k candidates indetifiers)
        """
        k = k if k is not None else self._k
        adjusted_k = k + exclusions.shape[1]
        scores, identifiers = self(queries=queries, k=adjusted_k)
        return _exclude(scores, identifiers, exclusions, adjusted_k)

    def _reset_tf_function_cache(self):
        """Resets the tf.function cache."""
        if hasattr(self.query_with_exclusions, 'python_function'):
            self.query_with_exclusions = tf.function(self.query_with_exclusions.python_function)

def __init__(self, k: int, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._k = k

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

def __init__(self, k: int=10, query_model: Optional[tf.keras.Model]=None, handle_incomplete_batches: bool=True, num_parallel_calls: int=tf.data.experimental.AUTOTUNE, sorted_order: bool=True, *args, **kwargs):
    super().__init__(k, *args, **kwargs)
    self._query_model = query_model
    self._handle_incomplete_batches = handle_incomplete_batches
    self._num_parallel_calls = num_parallel_calls
    self._sorted_order = sorted_order
    self._candidates = None
    self._identifiers = None
    self._counter = self.add_weight('counter', dtype=tf.int32, trainable=False)

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

def __init__(self, k: int=10, query_model: Optional[tf.keras.Model]=None, *args, **kwargs):
    super().__init__(k, *args, **kwargs)
    self._query_model = query_model

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

class FactorizedTopK(tf.keras.layers.Layer):
    """ Metric for a retrieval model. """

    def __init__(self, candidates: Union[TopK, tf.data.Dataset], metrics: Optional[Sequence[tf.keras.metrics.Metric]]=None, k: int=100, name: Text='factorized_top_k', **kwargs):
        super(FactorizedTopK, self).__init__(name=name, **kwargs)
        if metrics is None:
            metrics = [tf.keras.metrics.TopKCategoricalAccuracy(k=n, name=f'{self.name}/top_{n}_categorical_accuracy') for n in [1, 5, 10, 50, 100]]
        if isinstance(candidates, tf.data.Dataset):
            candidates = Streaming(k=k).index(candidates)
        self._candidates = candidates
        self._metrics = metrics
        self._k = k

    def update_state(self, query_embeddings: tf.Tensor, true_candidate_embeddings: tf.Tensor) -> tf.Operation:
        """Update metric"""
        positive_scores = tf.reduce_sum(query_embeddings * true_candidate_embeddings, axis=1, keepdims=True)
        top_k_predictions, _ = self._candidates(query_embeddings, k=self._k)
        y_true = tf.concat([tf.ones(tf.shape(positive_scores)), tf.zeros_like(top_k_predictions)], axis=1)
        y_pred = tf.concat([positive_scores, top_k_predictions], axis=1)
        update_ops = []
        for metric in self._metrics:
            update_ops.append(metric.update_state(y_true=y_true, y_pred=y_pred))
        return tf.group(update_ops)

    def reset_states(self) -> None:
        """Resets the metrics."""
        for metric in self.metrics:
            metric.reset_states()

    def result(self) -> List[tf.Tensor]:
        """Returns a list of metric results."""
        return [metric.result() for metric in self.metrics]

def __init__(self, candidates: Union[TopK, tf.data.Dataset], metrics: Optional[Sequence[tf.keras.metrics.Metric]]=None, k: int=100, name: Text='factorized_top_k', **kwargs):
    super(FactorizedTopK, self).__init__(name=name, **kwargs)
    if metrics is None:
        metrics = [tf.keras.metrics.TopKCategoricalAccuracy(k=n, name=f'{self.name}/top_{n}_categorical_accuracy') for n in [1, 5, 10, 50, 100]]
    if isinstance(candidates, tf.data.Dataset):
        candidates = Streaming(k=k).index(candidates)
    self._candidates = candidates
    self._metrics = metrics
    self._k = k

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

def get_config(self):
    config = {'units': self._units, 'use_bias': self._use_bias, 'activation': tf.keras.activations.serialize(self._kernel_activation), 'kernel_initializer': tf.keras.initializers.serialize(self._kernel_initializer), 'kernel_regularizer': tf.keras.regularizers.serialize(self._kernel_regularizer), 'bias_initializer': tf.keras.initializers.serialize(self._bias_initializer), 'bias_regularizer': tf.keras.regularizers.serialize(self._bias_regularizer)}
    base_config = super(GCN, self).get_config()
    return {**base_config, **config}

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

def __init__(self, num_hard_negatives: int, **kwargs):
    super(HardNegativeMining, self).__init__(**kwargs)
    self._num_hard_negatives = num_hard_negatives

class Retrieval(tf.keras.layers.Layer):
    """检索任务"""

    def __init__(self, loss: Optional[tf.keras.losses.Loss]=None, metrics: Optional[FactorizedTopK]=None, temperature: Optional[float]=None, num_hard_negatives: Optional[int]=None, **kwargs):
        super(Retrieval, self).__init__(**kwargs)
        self._loss = tf.keras.losses.CategoricalCrossentropy(from_logits=True, reduction=tf.keras.losses.Reduction.SUM) if loss is None else loss
        self._factorized_metrics = metrics
        self._temperature = temperature
        self._num_hard_negatives = num_hard_negatives

    @property
    def factorized_metrics(self) -> Optional[FactorizedTopK]:
        """The metrics object used to compute retrieval metrics."""
        return self._factorized_metrics

    @factorized_metrics.setter
    def factorized_metrics(self, value: Optional[FactorizedTopK]) -> None:
        """Sets factorized metrics."""
        self._factorized_metrics = value

    def call(self, query_embeddings: tf.Tensor, candidate_embeddings: tf.Tensor, sample_weight: Optional[tf.Tensor]=None, candidate_sampling_probability: Optional[tf.Tensor]=None, candidate_ids: Optional[tf.Tensor]=None, compute_metrics: bool=True) -> tf.Tensor:
        """Compute loss and metrics"""
        scores = tf.matmul(query_embeddings, candidate_embeddings, transpose_b=True)
        num_queries = tf.shape(scores)[0]
        num_candidates = tf.shape(scores)[1]
        labels = tf.eye(num_queries, num_candidates)
        if candidate_sampling_probability is not None:
            scores = deep_recommenders.keras.layers.embedding.loss.SamplingProbablityCorrection()(scores, candidate_sampling_probability)
        if candidate_ids is not None:
            scores = deep_recommenders.keras.layers.embedding.loss.RemoveAccidentalNegative()(scores, labels, candidate_ids)
        if self._num_hard_negatives is not None:
            scores, labels = deep_recommenders.keras.layers.embedding.loss.HardNegativeMining(self._num_hard_negatives)(scores, labels)
        if self._temperature is not None:
            scores = scores / self._temperature
        loss = self._loss(y_true=labels, y_pred=scores, sample_weight=sample_weight)
        if compute_metrics is False:
            return loss
        if not self._factorized_metrics:
            return loss
        update_op = self._factorized_metrics.update_state(query_embeddings, candidate_embeddings)
        with tf.control_dependencies([update_op]):
            return tf.identity(loss)

def __init__(self, loss: Optional[tf.keras.losses.Loss]=None, metrics: Optional[FactorizedTopK]=None, temperature: Optional[float]=None, num_hard_negatives: Optional[int]=None, **kwargs):
    super(Retrieval, self).__init__(**kwargs)
    self._loss = tf.keras.losses.CategoricalCrossentropy(from_logits=True, reduction=tf.keras.losses.Reduction.SUM) if loss is None else loss
    self._factorized_metrics = metrics
    self._temperature = temperature
    self._num_hard_negatives = num_hard_negatives

class DeepFM(tf.keras.Model):

    def __init__(self, indicator_columns, embedding_columns, dnn_units_size, dnn_activation='relu', **kwargs):
        super(DeepFM, self).__init__(**kwargs)
        self._indicator_columns = indicator_columns
        self._embedding_columns = embedding_columns
        self._dnn_units_size = dnn_units_size
        self._dnn_activation = dnn_activation
        self._sparse_features_layer = tf.keras.layers.DenseFeatures(self._indicator_columns)
        self._embedding_features_layer = {c.categorical_column.key: tf.keras.layers.DenseFeatures(c) for c in self._embedding_columns}
        self._fm = FM()
        self._dnn = tf.keras.Sequential([tf.keras.layers.Dense(units, activation=self._dnn_activation) for units in self._dnn_units_size] + [tf.keras.layers.Dense(1)])

    def call(self, inputs, **kwargs):
        sparse_features = self._sparse_features_layer(inputs)
        embeddings = []
        for column_name, column_input in inputs.items():
            dense_features = self._embedding_features_layer.get(column_name)
            if dense_features is not None:
                embedding = dense_features({column_name: column_input})
                embeddings.append(embedding)
        stack_embeddings = tf.stack(embeddings, axis=1)
        concat_embeddings = tf.concat(embeddings, axis=1)
        outputs = self._fm(sparse_features, stack_embeddings) + self._dnn(concat_embeddings)
        return tf.keras.activations.sigmoid(outputs)

    def get_config(self):
        config = {'dnn_units_size': self._dnn_units_size, 'dnn_activation': self._dnn_activation}
        base_config = super(DeepFM, self).get_config()
        return {**base_config, **config}

def __init__(self, indicator_columns, embedding_columns, dnn_units_size, dnn_activation='relu', **kwargs):
    super(DeepFM, self).__init__(**kwargs)
    self._indicator_columns = indicator_columns
    self._embedding_columns = embedding_columns
    self._dnn_units_size = dnn_units_size
    self._dnn_activation = dnn_activation
    self._sparse_features_layer = tf.keras.layers.DenseFeatures(self._indicator_columns)
    self._embedding_features_layer = {c.categorical_column.key: tf.keras.layers.DenseFeatures(c) for c in self._embedding_columns}
    self._fm = FM()
    self._dnn = tf.keras.Sequential([tf.keras.layers.Dense(units, activation=self._dnn_activation) for units in self._dnn_units_size] + [tf.keras.layers.Dense(1)])

def get_config(self):
    config = {'dnn_units_size': self._dnn_units_size, 'dnn_activation': self._dnn_activation}
    base_config = super(DeepFM, self).get_config()
    return {**base_config, **config}

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

def __init__(self, **kwargs):
    super(FM, self).__init__(**kwargs)

class FactorizationMachine(tf.keras.Model):

    def __init__(self, indicator_columns, embedding_columns, **kwargs):
        super(FactorizationMachine, self).__init__(**kwargs)
        self._indicator_columns = indicator_columns
        self._embedding_columns = embedding_columns
        self._sparse_features_layer = tf.keras.layers.DenseFeatures(self._indicator_columns)
        self._embedding_features_layer = {c.categorical_column.key: tf.keras.layers.DenseFeatures(c) for c in self._embedding_columns}
        self._kernel = FM()

    def call(self, inputs, training=None, mask=None):
        sparse_features = self._sparse_features_layer(inputs)
        embeddings = []
        for column_name, column_input in inputs.items():
            dense_features = self._embedding_features_layer.get(column_name)
            if dense_features is not None:
                embedding = dense_features({column_name: column_input})
                embeddings.append(embedding)
        stack_embeddings = tf.stack(embeddings, axis=1)
        outputs = self._kernel(sparse_features, stack_embeddings)
        return tf.nn.sigmoid(outputs)

    def get_config(self):
        config = {'indicator_columns': self._indicator_columns, 'embedding_columns': self._embedding_columns}
        base_config = super(FactorizationMachine, self).get_config()
        return {**base_config, **config}

def __init__(self, indicator_columns, embedding_columns, **kwargs):
    super(FactorizationMachine, self).__init__(**kwargs)
    self._indicator_columns = indicator_columns
    self._embedding_columns = embedding_columns
    self._sparse_features_layer = tf.keras.layers.DenseFeatures(self._indicator_columns)
    self._embedding_features_layer = {c.categorical_column.key: tf.keras.layers.DenseFeatures(c) for c in self._embedding_columns}
    self._kernel = FM()

def get_config(self):
    config = {'indicator_columns': self._indicator_columns, 'embedding_columns': self._embedding_columns}
    base_config = super(FactorizationMachine, self).get_config()
    return {**base_config, **config}

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

def get_config(self):
    config = {'projection_dim': self._projection_dim, 'diag_scale': self._diag_scale, 'use_bias': self._use_bias, 'kernel_init': tf.keras.initializers.serialize(self._kernel_init), 'kernel_regu': tf.keras.regularizers.serialize(self._kernel_regu), 'bias_init': tf.keras.initializers.serialize(self._bias_init), 'bias_regu': tf.keras.regularizers.serialize(self._bias_regu)}
    base_config = super(Cross, self).get_config()
    return {**base_config, **config}

@tf.keras.utils.register_keras_serializable()
class ActivationUnit(tf.keras.layers.Layer):

    def __init__(self, units, interacter=None, use_bias=True, activation='relu', kernel_init='truncated_normal', kernel_regu=None, bias_init='zeros', bias_regu=None, **kwargs):
        super(ActivationUnit, self).__init__(**kwargs)
        self._kernel_units = units
        self._interacter = interacter
        self._use_bias = use_bias
        if isinstance(activation, tf.keras.layers.Layer):
            self._kernel_activation = activation
        elif isinstance(activation, str):
            self._kernel_activation = tf.keras.activations.get(activation)
        else:
            self._kernel_activation = None
        self._kernel_init = tf.keras.initializers.get(kernel_init)
        self._kernel_regu = tf.keras.regularizers.get(kernel_regu)
        self._bias_init = tf.keras.initializers.get(bias_init)
        self._bias_regu = tf.keras.regularizers.get(bias_regu)

    def build(self, input_shape):
        self.dense_kernel = tf.keras.layers.Dense(self._kernel_units, activation=self._kernel_activation, use_bias=self._use_bias, kernel_initializer=self._kernel_init, kernel_regularizer=self._kernel_regu, bias_initializer=self._bias_init, bias_regularizer=self._bias_regu)
        self.dense_output = tf.keras.layers.Dense(1, activation=None, use_bias=self._use_bias, kernel_initializer=self._kernel_init, kernel_regularizer=self._kernel_regu, bias_initializer=self._bias_init, bias_regularizer=self._bias_regu)
        self.built = True

    def call(self, x_embeddings, y_embeddings=None, **kwargs):
        if y_embeddings is None:
            y_embeddings = x_embeddings
        x = tf.concat([x_embeddings, y_embeddings], axis=1)
        if self._interacter is not None:
            x = tf.concat([x, self._interacter([x_embeddings, y_embeddings])], axis=1)
        x = self.dense_kernel(x)
        return self.dense_output(x)

    def get_config(self):
        config = {'units': self._kernel_units, 'interacter': self._interacter, 'use_bias': self._use_bias, 'activation': tf.keras.activations.serialize(self._kernel_activation), 'kernel_init': tf.keras.initializers.serialize(self._kernel_init), 'kernel_regu': tf.keras.regularizers.serialize(self._kernel_regu), 'bias_init': tf.keras.initializers.serialize(self._bias_init), 'bias_regu': tf.keras.regularizers.serialize(self._bias_regu)}
        base_config = super(ActivationUnit, self).get_config()
        return {**base_config, **config}

def __init__(self, units, interacter=None, use_bias=True, activation='relu', kernel_init='truncated_normal', kernel_regu=None, bias_init='zeros', bias_regu=None, **kwargs):
    super(ActivationUnit, self).__init__(**kwargs)
    self._kernel_units = units
    self._interacter = interacter
    self._use_bias = use_bias
    if isinstance(activation, tf.keras.layers.Layer):
        self._kernel_activation = activation
    elif isinstance(activation, str):
        self._kernel_activation = tf.keras.activations.get(activation)
    else:
        self._kernel_activation = None
    self._kernel_init = tf.keras.initializers.get(kernel_init)
    self._kernel_regu = tf.keras.regularizers.get(kernel_regu)
    self._bias_init = tf.keras.initializers.get(bias_init)
    self._bias_regu = tf.keras.regularizers.get(bias_regu)

def get_config(self):
    config = {'units': self._kernel_units, 'interacter': self._interacter, 'use_bias': self._use_bias, 'activation': tf.keras.activations.serialize(self._kernel_activation), 'kernel_init': tf.keras.initializers.serialize(self._kernel_init), 'kernel_regu': tf.keras.regularizers.serialize(self._kernel_regu), 'bias_init': tf.keras.initializers.serialize(self._bias_init), 'bias_regu': tf.keras.regularizers.serialize(self._bias_regu)}
    base_config = super(ActivationUnit, self).get_config()
    return {**base_config, **config}

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

def __init__(self, epsilon: float=1e-08, alpha_initializer='zeros', alpha_regularizer=None, **kwargs):
    super(Dice, self).__init__(**kwargs)
    self._epsilon = epsilon
    self._alpha_initializer = alpha_initializer
    self._alpha_regularizer = alpha_regularizer

def get_config(self):
    config = {'epsilon': self._epsilon, 'alpha_initializer': tf.keras.initializers.serialize(self._alpha_initializer), 'alpha_regularizer': tf.keras.regularizers.serialize(self._alpha_regularizer)}
    base_config = super(Dice, self).get_config()
    return {**base_config, **config}

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

def get_config(self):
    config = {'feature_map': self._feature_map, 'use_bias': self._use_bias, 'activation': tf.keras.activations.serialize(self._activation), 'kernel_init': tf.keras.initializers.serialize(self._kernel_init), 'kernel_regu': tf.keras.regularizers.serialize(self._kernel_regu), 'bias_init': tf.keras.initializers.serialize(self._bias_init), 'bias_regu': tf.keras.regularizers.serialize(self._bias_regu)}
    base_config = super(CIN, self).get_config()
    return {**base_config, **config}

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

def __init__(self, model_dim, **kwargs):
    self._model_dim = model_dim
    super(PositionEncoding, self).__init__(**kwargs)

@tf.keras.utils.register_keras_serializable()
class Add(Layer):

    def __init__(self, **kwargs):
        super(Add, self).__init__(**kwargs)

    def call(self, inputs, **kwargs):
        input_a, input_b = inputs
        return input_a + input_b

    def compute_output_shape(self, input_shape):
        return input_shape[0]

def __init__(self, **kwargs):
    super(Add, self).__init__(**kwargs)

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

def __init__(self, epsilon=1e-08, **kwargs):
    self._epsilon = epsilon
    super(LayerNormalization, self).__init__(**kwargs)

def build(self, input_shape):
    self.beta = self.add_weight(shape=(input_shape[-1],), initializer='zero', name='beta')
    self.gamma = self.add_weight(shape=(input_shape[-1],), initializer='one', name='gamma')
    super(LayerNormalization, self).build(input_shape)

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

def get_config(self):
    config = {'vocab_size': self._vocab_size, 'model_dim': self._model_dim, 'n_heads': self._n_heads, 'encoder_stack': self._encoder_stack, 'decoder_stack': self._decoder_stack, 'feed_forward_size': self._feed_forward_size, 'dropout_rate': self._dropout_rate}
    base_config = super(Transformer, self).get_config()
    return {**base_config, **config}

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

def __init__(self, model_dim, step_num=0, warmup_steps=4000, verbose=False):
    self._model_dim = model_dim
    self._step_num = step_num
    self._warmup_steps = warmup_steps
    self.verbose = verbose
    super(Noam, self).__init__()

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

def __init__(self, vocab_size, model_dim, **kwargs):
    self._vocab_size = vocab_size
    self._model_dim = model_dim
    super(Embedding, self).__init__(**kwargs)

def build(self, input_shape):
    self.embeddings = self.add_weight(shape=(self._vocab_size, self._model_dim), initializer='glorot_uniform', name='embeddings')
    super(Embedding, self).build(input_shape)

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

def __init__(self, masking=True, future=False, dropout_rate=0.0, **kwargs):
    self._masking = masking
    self._future = future
    self._dropout_rate = dropout_rate
    self._masking_num = -2 ** 32 + 1
    super(ScaledDotProductAttention, self).__init__(**kwargs)

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

class MovielensRanking(MovieLens):

    def __init__(self, epochs: int=10, batch_size: int=1024, buffer_size: int=1024, train_size: float=0.8, *args, **kwargs):
        super(MovielensRanking, self).__init__(*args, **kwargs)
        self._epochs = epochs
        self._batch_size = batch_size
        self._buffer_size = buffer_size
        self._train_size = train_size

    @property
    def train_steps(self):
        num_train_ratings = self.num_ratings * self._epochs * self._train_size
        return int(num_train_ratings // self._batch_size)

    @property
    def train_steps_per_epoch(self):
        num_train_ratings = self.num_ratings * self._train_size
        return int(num_train_ratings // self._batch_size)

    @property
    def test_steps(self):
        return self.num_ratings // self._batch_size - self.train_steps_per_epoch

    @property
    def training_input_fn(self):
        return self.input_fn().take(self.train_steps)

    @property
    def testing_input_fn(self):
        return self.input_fn().skip(self.train_steps).take(self.test_steps)

    def input_fn(self):
        dataset = self.dataset(self._epochs, self._batch_size)
        dataset = dataset.map(lambda x, y: ({'user_id': x['UserID'], 'user_gender': x['Gender'], 'user_age': x['Age'], 'user_occupation': x['Occupation'], 'movie_id': x['MovieID'], 'movie_genres': x['Genres']}, tf.expand_dims(tf.where(y > 3, tf.ones_like(y, dtype=tf.float32), tf.zeros_like(y, dtype=tf.float32)), axis=1)))
        dataset = dataset.prefetch(self._buffer_size)
        return dataset

def __init__(self, epochs: int=10, batch_size: int=1024, buffer_size: int=1024, train_size: float=0.8, *args, **kwargs):
    super(MovielensRanking, self).__init__(*args, **kwargs)
    self._epochs = epochs
    self._batch_size = batch_size
    self._buffer_size = buffer_size
    self._train_size = train_size

