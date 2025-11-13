# Cluster 8

def build_model():
    g = tf.keras.layers.Input(shape=(None,))
    feats = tf.keras.layers.Input(shape=(features.shape[-1],))
    x = GCN(32)(feats, g)
    outputs = GCN(cora.num_classes, activation='softmax')(x, g)
    return tf.keras.Model([g, feats], outputs)

def get_embeddings(model, graph, features):
    input_layer, output_layer = (model.input, model.layers[-1].output)
    embedding_model = tf.keras.Model(input_layer, output_layer)
    embeddings = embedding_model.predict([graph, features], batch_size=graph.shape[0])
    return embeddings

def build_model(vocab_size, max_len, model_dim=8, n_heads=2, encoder_stack=2, decoder_stack=2, ff_size=50):
    encoder_inputs = tf.keras.Input(shape=(max_len,), name='encoder_inputs')
    decoder_inputs = tf.keras.Input(shape=(max_len,), name='decoder_inputs')
    outputs = Transformer(vocab_size, model_dim, n_heads=n_heads, encoder_stack=encoder_stack, decoder_stack=decoder_stack, feed_forward_size=ff_size)(encoder_inputs, decoder_inputs)
    outputs = tf.keras.layers.GlobalAveragePooling1D()(outputs)
    outputs = tf.keras.layers.Dense(2, activation='softmax')(outputs)
    return tf.keras.Model(inputs=[encoder_inputs, decoder_inputs], outputs=outputs)

class TestGCN(tf.test.TestCase, parameterized.TestCase):

    def test_gcn_adj_sparse_matrix(self):
        adj = np.asarray([[0, 1, 0], [1, 0, 0], [0, 1, 1]]).astype(np.float32)
        embeddings = np.asarray([[0.1, 0.2, 0.3, 0.0], [0.4, 0.5, 0.6, 0.0], [0.7, 0.8, 0.9, 0.0]]).astype(np.float32)
        W = np.ones(shape=(4, 2))
        agg_embeddings = adj @ embeddings
        dense_outputs = agg_embeddings @ W
        expect_outputs = tf.nn.relu(dense_outputs)
        coo = sp.sparse.coo_matrix(adj)
        indices = np.mat([coo.row, coo.col]).transpose()
        sparse_adj = tf.SparseTensor(indices, coo.data, coo.shape)
        outputs = GCN(2, kernel_initializer='ones')(embeddings, sparse_adj)
        self.evaluate(tf.compat.v1.global_variables_initializer())
        self.assertAllClose(outputs, expect_outputs)

    def test_gcn_adj_full_matrix(self):
        adj = np.asarray([[0, 1, 0], [1, 0, 0], [0, 1, 1]]).astype(np.float32)
        embeddings = np.asarray([[0.1, 0.2, 0.3, 0.0], [0.4, 0.5, 0.6, 0.0], [0.7, 0.8, 0.9, 0.0]]).astype(np.float32)
        W = np.ones(shape=(4, 2))
        agg_embeddings = adj @ embeddings
        dense_outputs = agg_embeddings @ W
        expect_outputs = tf.nn.relu(dense_outputs)
        outputs = GCN(2, kernel_initializer='ones')(embeddings, adj)
        self.evaluate(tf.compat.v1.global_variables_initializer())
        self.assertAllClose(outputs, expect_outputs)

    @parameterized.parameters((8, 4), (16, 8), (32, 16))
    def test_gcn_train(self, num_nodes, embeddings_dim):

        def get_model():
            adj = tf.keras.layers.Input(shape=(num_nodes,), sparse=True)
            embeddings = tf.keras.layers.Input(shape=(embeddings_dim,))
            x = GCN(16)(embeddings, adj)
            x = GCN(16)(x, adj)
            outputs = GCN(2, activation='softmax')(x, adj)
            return tf.keras.Model([adj, embeddings], outputs)
        np.random.seed(42)
        adj = sp.sparse.random(num_nodes, num_nodes).tocsr()
        adj.sort_indices()
        embeddings = np.random.normal(size=(num_nodes, embeddings_dim)).astype(np.float32)
        targets = np.random.randint(2, size=num_nodes).astype(np.float32)
        targets = np.stack([targets, 1 - targets], axis=1)
        model = get_model()
        model.compile(optimizer=tf.keras.optimizers.Adam(0.01), loss='categorical_crossentropy')
        model.fit(x=[adj, embeddings], y=targets, batch_size=num_nodes, verbose=0, shuffle=False)
        model_pred = model.predict([adj, embeddings])
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'gcn')
            model.save(path, options=tf.saved_model.SaveOptions(namespace_whitelist=['GCN']))
            loaded_model = tf.keras.models.load_model(path)
            loaded_pred = loaded_model.predict([adj, embeddings], batch_size=num_nodes)
        for model_layer, loaded_layer in zip(model.layers, loaded_model.layers):
            assert model_layer.get_config() == loaded_layer.get_config()
        self.assertAllEqual(model_pred, loaded_pred)

def get_model():
    adj = tf.keras.layers.Input(shape=(num_nodes,), sparse=True)
    embeddings = tf.keras.layers.Input(shape=(embeddings_dim,))
    x = GCN(16)(embeddings, adj)
    x = GCN(16)(x, adj)
    outputs = GCN(2, activation='softmax')(x, adj)
    return tf.keras.Model([adj, embeddings], outputs)

class TestFM(tf.test.TestCase):

    def test_fm_layer(self):
        sparse_inputs = np.random.randint(0, 2, size=(10, 10)).astype(np.float32)
        embedding_inputs = np.random.normal(size=(10, 5, 5)).astype(np.float32)
        x_sum = np.sum(embedding_inputs, axis=1)
        x_square_sum = np.sum(np.power(embedding_inputs, 2), axis=1)
        expected_outputs = 0.5 * np.sum(np.power(x_sum, 2) - x_square_sum, axis=1, keepdims=True)
        outputs = FM()(sparse_inputs, embedding_inputs)
        self.assertAllClose(outputs, expected_outputs)

    def test_fm_layer_train(self):

        def get_model():
            sparse_inputs = tf.keras.layers.Input(shape=(10,))
            embedding_inputs = tf.keras.layers.Input(shape=(5, 5))
            x = FM()(sparse_inputs, embedding_inputs)
            logits = tf.keras.layers.Dense(1)(x)
            return tf.keras.Model([sparse_inputs, embedding_inputs], logits)
        model = get_model()
        random_sparse_inputs = np.random.randint(0, 2, size=(10, 10))
        random_embedding_inputs = np.random.uniform(size=(10, 5, 5))
        random_outputs = np.random.uniform(size=(10,))
        model.compile(loss='mse')
        model.fit([random_sparse_inputs, random_embedding_inputs], random_outputs, verbose=0)

    def test_fm_layer_save(self):

        def get_model():
            sparse_inputs = tf.keras.layers.Input(shape=(10,))
            embedding_inputs = tf.keras.layers.Input(shape=(5, 5))
            x = FM()(sparse_inputs, embedding_inputs)
            logits = tf.keras.layers.Dense(1)(x)
            return tf.keras.Model([sparse_inputs, embedding_inputs], logits)
        model = get_model()
        random_sparse_inputs = np.random.randint(0, 2, size=(10, 10))
        random_embedding_inputs = np.random.uniform(size=(10, 5, 5))
        model_pred = model.predict([random_sparse_inputs, random_embedding_inputs])
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'fm')
            model.save(path, options=tf.saved_model.SaveOptions(namespace_whitelist=['FM']))
            loaded_model = tf.keras.models.load_model(path)
            loaded_pred = loaded_model.predict([random_sparse_inputs, random_embedding_inputs])
        for model_layer, loaded_layer in zip(model.layers, loaded_model.layers):
            assert model_layer.get_config() == loaded_layer.get_config()
        self.assertAllEqual(model_pred, loaded_pred)

    def test_model(self):

        def build_columns():
            user_id = tf.feature_column.categorical_column_with_hash_bucket('user_id', 100)
            movie_id = tf.feature_column.categorical_column_with_hash_bucket('movie_id', 100)
            base_columns = [user_id, movie_id]
            _indicator_columns = [tf.feature_column.indicator_column(c) for c in base_columns]
            _embedding_columns = [tf.feature_column.embedding_column(c, dimension=16) for c in base_columns]
            return (_indicator_columns, _embedding_columns)
        indicator_columns, embedding_columns = build_columns()
        model = FactorizationMachine(indicator_columns, embedding_columns)
        model.compile(loss=tf.keras.losses.binary_crossentropy, optimizer=tf.keras.optimizers.Adam())
        dataset = tf.data.Dataset.from_tensor_slices(({'user_id': [['1']] * 1000, 'movie_id': [['2']] * 1000}, np.random.randint(0, 1, size=(1000, 1))))
        model.fit(dataset, steps_per_epoch=100, verbose=-1)
        test_data = {'user_id': np.asarray([['1'], ['2']]), 'movie_id': np.asarray([['1'], ['2']])}
        model_pred = model.predict(test_data)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'FM')
            model.save(path)
            loaded_model = tf.keras.models.load_model(path)
            loaded_pred = loaded_model.predict(test_data)
        for model_layer, loaded_layer in zip(model.layers, loaded_model.layers):
            assert model_layer.get_config() == loaded_layer.get_config()
        self.assertAllEqual(model_pred, loaded_pred)

def get_model():
    sparse_inputs = tf.keras.layers.Input(shape=(10,))
    embedding_inputs = tf.keras.layers.Input(shape=(5, 5))
    x = FM()(sparse_inputs, embedding_inputs)
    logits = tf.keras.layers.Dense(1)(x)
    return tf.keras.Model([sparse_inputs, embedding_inputs], logits)

class TestDCN(tf.test.TestCase):

    def test_cross_full_matrix(self):
        x0 = np.asarray([[0.1, 0.2, 0.3]]).astype(np.float32)
        x = np.asarray([[0.4, 0.5, 0.6]]).astype(np.float32)
        cross = Cross(projection_dim=None, kernel_init='ones')
        output = cross(x0, x)
        self.evaluate(tf.compat.v1.global_variables_initializer())
        self.assertAllClose(np.asarray([[0.55, 0.8, 1.05]]), output)

    def test_cross_save_model(self):

        def get_model():
            x0 = tf.keras.layers.Input(shape=(13,))
            x1 = Cross(projection_dim=None)(x0, x0)
            x2 = Cross(projection_dim=None)(x0, x1)
            logits = tf.keras.layers.Dense(units=1)(x2)
            return tf.keras.Model(x0, logits)
        model = get_model()
        random_input = np.random.uniform(size=(10, 13))
        model_pred = model.predict(random_input)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'dcn_model')
            model.save(path)
            loaded_model = tf.keras.models.load_model(path)
            loaded_pred = loaded_model.predict(random_input)
        for i in range(len(model.layers)):
            assert model.layers[i].get_config() == loaded_model.layers[i].get_config()
        self.assertAllClose(model_pred, loaded_pred)

def get_model():
    x0 = tf.keras.layers.Input(shape=(13,))
    x1 = Cross(projection_dim=None)(x0, x0)
    x2 = Cross(projection_dim=None)(x0, x1)
    logits = tf.keras.layers.Dense(units=1)(x2)
    return tf.keras.Model(x0, logits)

class TestXDeepFM(tf.test.TestCase):

    def test_invalid_inputs_type(self):
        """ 测试输入类型 """
        with self.assertRaisesRegexp(ValueError, "`CIN` layer's inputs type should be `tuple`."):
            inputs = np.random.normal(size=(2, 3, 5)).astype(np.float32)
            CIN(feature_map=3)(inputs)

    def test_invalid_inputs_ndim(self):
        """ 测试输入维度 """
        with self.assertRaisesRegexp(ValueError, '`x0` and `x` dim should be 3.'):
            inputs = np.random.normal(size=(2, 15)).astype(np.float32)
            CIN(feature_map=3)((inputs, inputs))

    def test_outputs(self):
        """ 测试输出是否正确 """
        x0 = np.asarray([[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]]).astype(np.float32)
        x = np.asarray([[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]]).astype(np.float32)
        outputs = CIN(feature_map=2, activation='relu', kernel_init='ones')((x0, x))
        expect_outputs = np.asarray([[[0.25, 0.49, 0.81], [0.25, 0.49, 0.81]]]).astype(np.float32)
        self.evaluate(tf.compat.v1.global_variables_initializer())
        self.assertAllClose(outputs, expect_outputs)

    def test_bias(self):
        """ 测试bias """
        x0 = np.asarray([[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]]).astype(np.float32)
        x = np.asarray([[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]]).astype(np.float32)
        outputs = CIN(feature_map=2, use_bias=True, activation='relu', kernel_init='ones', bias_init='ones')((x0, x))
        expect_outputs = np.asarray([[[1.25, 1.49, 1.81], [1.25, 1.49, 1.81]]]).astype(np.float32)
        self.evaluate(tf.compat.v1.global_variables_initializer())
        self.assertAllClose(outputs, expect_outputs)

    def test_train_model(self):
        """ 测试模型训练 """

        def get_model():
            x0 = tf.keras.layers.Input(shape=(12, 10))
            x = CIN(feature_map=3)((x0, x0))
            x = CIN(feature_map=3)((x0, x))
            x = tf.keras.layers.Flatten()(x)
            outputs = tf.keras.layers.Dense(1)(x)
            model = tf.keras.Model(x0, outputs)
            return model
        x0 = np.random.uniform(size=(10, 12, 10))
        y = np.random.uniform(size=(10,))
        model = get_model()
        model.compile(loss='mse')
        model.fit(x0, y, verbose=0)

    def test_save_model(self):
        """ 测试模型保存 """

        def get_model():
            x0 = tf.keras.layers.Input(shape=(12, 10))
            x = CIN(feature_map=3)((x0, x0))
            x = CIN(feature_map=3)((x0, x))
            x = tf.keras.layers.Flatten()(x)
            logits = tf.keras.layers.Dense(1)(x)
            model = tf.keras.Model(x0, logits)
            return model
        x0 = np.random.uniform(size=(10, 12, 10))
        model = get_model()
        model_pred = model.predict(x0)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'xDeepFM')
            model.save(path, options=tf.saved_model.SaveOptions(namespace_whitelist=['xDeepFm']))
            loaded_model = tf.keras.models.load_model(path)
            loaded_pred = loaded_model.predict(x0)
        for model_layer, loaded_layer in zip(model.layers, loaded_model.layers):
            assert model_layer.get_config() == loaded_layer.get_config()
        self.assertAllEqual(model_pred, loaded_pred)

def get_model():
    x0 = tf.keras.layers.Input(shape=(12, 10))
    x = CIN(feature_map=3)((x0, x0))
    x = CIN(feature_map=3)((x0, x))
    x = tf.keras.layers.Flatten()(x)
    logits = tf.keras.layers.Dense(1)(x)
    model = tf.keras.Model(x0, logits)
    return model

class TestTransformer(tf.test.TestCase):

    def test_save_model(self):

        def get_model():
            encoder_inputs = tf.keras.Input(shape=(256,), name='encoder_inputs')
            decoder_inputs = tf.keras.Input(shape=(256,), name='decoder_inputs')
            outputs = Transformer(5000, model_dim=8, n_heads=2, encoder_stack=2, decoder_stack=2, feed_forward_size=50)(encoder_inputs, decoder_inputs)
            outputs = tf.keras.layers.GlobalAveragePooling1D()(outputs)
            outputs = tf.keras.layers.Dense(1, activation='sigmoid')(outputs)
            return tf.keras.Model(inputs=[encoder_inputs, decoder_inputs], outputs=outputs)
        model = get_model()
        encoder_random_input = np.random.randint(size=(10, 256), low=0, high=5000)
        decoder_random_input = np.random.randint(size=(10, 256), low=0, high=5000)
        model_pred = model.predict([encoder_random_input, decoder_random_input])
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'transformer_model')
            model.save(path)
            loaded_model = tf.keras.models.load_model(path)
            loaded_pred = loaded_model.predict([encoder_random_input, decoder_random_input])
        for i in range(len(model.layers)):
            assert model.layers[i].get_config() == loaded_model.layers[i].get_config()
        self.assertAllClose(model_pred, loaded_pred)

def get_model():
    encoder_inputs = tf.keras.Input(shape=(256,), name='encoder_inputs')
    decoder_inputs = tf.keras.Input(shape=(256,), name='decoder_inputs')
    outputs = Transformer(5000, model_dim=8, n_heads=2, encoder_stack=2, decoder_stack=2, feed_forward_size=50)(encoder_inputs, decoder_inputs)
    outputs = tf.keras.layers.GlobalAveragePooling1D()(outputs)
    outputs = tf.keras.layers.Dense(1, activation='sigmoid')(outputs)
    return tf.keras.Model(inputs=[encoder_inputs, decoder_inputs], outputs=outputs)

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

def build(self, input_shape):
    self._kernel = tf.keras.layers.Dense(self._units, activation=self._kernel_activation, kernel_initializer=self._kernel_initializer, kernel_regularizer=self._kernel_regularizer, bias_initializer=self._bias_initializer, bias_regularizer=self._bias_regularizer, use_bias=self._use_bias)
    self.built = True

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

def build(self, input_shape):
    self._linear = tf.keras.layers.Dense(units=1, kernel_initializer='zeros', name='linear')
    self.built = True

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

def build(self, input_shape):
    self.dense_kernel = tf.keras.layers.Dense(self._kernel_units, activation=self._kernel_activation, use_bias=self._use_bias, kernel_initializer=self._kernel_init, kernel_regularizer=self._kernel_regu, bias_initializer=self._bias_init, bias_regularizer=self._bias_regu)
    self.dense_output = tf.keras.layers.Dense(1, activation=None, use_bias=self._use_bias, kernel_initializer=self._kernel_init, kernel_regularizer=self._kernel_regu, bias_initializer=self._bias_init, bias_regularizer=self._bias_regu)
    self.built = True

