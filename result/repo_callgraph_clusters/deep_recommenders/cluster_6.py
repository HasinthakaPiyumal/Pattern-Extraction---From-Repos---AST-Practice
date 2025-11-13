# Cluster 6

def main():
    movielens = MovielensRanking()
    indicator_columns, embedding_columns = build_columns()
    model = DeepFM(indicator_columns, embedding_columns, dnn_units_size=[256, 32])
    model.compile(loss=tf.keras.losses.binary_crossentropy, optimizer=tf.keras.optimizers.Adam(), metrics=[tf.keras.metrics.AUC(), tf.keras.metrics.Precision(), tf.keras.metrics.Recall()])
    model.fit(movielens.training_input_fn, epochs=10, steps_per_epoch=movielens.train_steps_per_epoch, validation_data=movielens.testing_input_fn, validation_steps=movielens.test_steps, callbacks=[tf.keras.callbacks.EarlyStopping(patience=3)])

def train_model():
    cora = Cora()
    ids, features, labels = cora.load_content()
    graph = cora.build_graph(ids)
    spectral_graph = cora.spectral_graph(graph)
    cora.sample_train_nodes(labels)
    train, valid, test = cora.split_labels(labels)

    def build_model():
        g = tf.keras.layers.Input(shape=(None,))
        feats = tf.keras.layers.Input(shape=(features.shape[-1],))
        x = GCN(32)(feats, g)
        outputs = GCN(cora.num_classes, activation='softmax')(x, g)
        return tf.keras.Model([g, feats], outputs)
    model = build_model()
    model.compile(optimizer=tf.keras.optimizers.Adam(0.01), loss='categorical_crossentropy', weighted_metrics=['acc'])
    train_labels, train_mask = train
    valid_labels, valid_mask = valid
    test_labels, test_mask = test
    batch_size = graph.shape[0]
    model.fit([spectral_graph, features], train_labels, sample_weight=train_mask, validation_data=([spectral_graph, features], valid_labels, valid_mask), batch_size=batch_size, epochs=200, shuffle=False, verbose=2, callbacks=[tf.keras.callbacks.EarlyStopping(patience=3)])
    eval_results = model.evaluate([spectral_graph, features], test_labels, sample_weight=test_mask, batch_size=batch_size, verbose=0)
    print('Test Loss: {:.4f}'.format(eval_results[0]))
    print('Test Accuracy: {:.4f}'.format(eval_results[1]))

def train_model(vocab_size=5000, max_len=128, batch_size=128, epochs=10):
    train, test = load_dataset(vocab_size, max_len)
    x_train, x_train_masks, y_train = train
    x_test, x_test_masks, y_test = test
    model = build_model(vocab_size, max_len)
    model.compile(optimizer=tf.keras.optimizers.Adam(beta_1=0.9, beta_2=0.98, epsilon=1e-09), loss='categorical_crossentropy', metrics=['accuracy'])
    es = tf.keras.callbacks.EarlyStopping(patience=3)
    model.fit([x_train, x_train_masks], y_train, batch_size=batch_size, epochs=epochs, validation_split=0.2, callbacks=[es])
    test_metrics = model.evaluate([x_test, x_test_masks], y_test, batch_size=batch_size, verbose=0)
    print('loss on Test: %.4f' % test_metrics[0])
    print('accu on Test: %.4f' % test_metrics[1])

class TestDIN(tf.test.TestCase, parameterized.TestCase):

    def test_activation_unit_noiteract(self):
        x = np.random.normal(size=(3, 5))
        y = np.random.normal(size=(3, 5))
        activation_unit = din.ActivationUnit(10, kernel_init='ones')
        outputs = activation_unit(x, y)
        dense = tf.keras.layers.Dense(10, activation='relu', kernel_initializer='ones')
        expected_outputs = tf.math.reduce_sum(dense(np.concatenate([x, y], axis=1)), axis=1, keepdims=True)
        self.evaluate(tf.compat.v1.global_variables_initializer())
        self.assertAllClose(outputs, expected_outputs)

    def test_activation_unit_iteract(self):
        x = np.random.normal(size=(3, 5))
        y = np.random.normal(size=(3, 5))
        interacter = tf.keras.layers.Subtract()
        activation_unit = din.ActivationUnit(10, interacter=interacter, kernel_init='ones')
        outputs = activation_unit(x, y)
        dense = tf.keras.layers.Dense(10, activation='relu', kernel_initializer='ones')
        expected_outputs = tf.math.reduce_sum(dense(np.concatenate([x, y, x - y], axis=1)), axis=1, keepdims=True)
        self.evaluate(tf.compat.v1.global_variables_initializer())
        self.assertAllClose(outputs, expected_outputs)

    @parameterized.parameters(1e-07, 1e-08, 1e-09, 1e-10)
    def test_dice(self, epsilon):
        inputs = np.asarray([[-0.2, -0.1, 0.1, 0.2]]).astype(np.float32)
        outputs = din.Dice(epsilon=epsilon)(inputs)
        p = (inputs - inputs.mean()) / np.math.sqrt(inputs.std() + epsilon)
        p = 1 / (1 + np.exp(-p))
        x = tf.where(inputs > 0, x=inputs, y=tf.zeros_like(inputs))
        expected_outputs = tf.where(x > 0, x=p * x, y=(1 - p) * x)
        self.evaluate(tf.compat.v1.global_variables_initializer())
        self.assertAllClose(outputs, expected_outputs)

    def test_din(self):

        def build_model():
            x = tf.keras.layers.Input(shape=(5,))
            y = tf.keras.layers.Input(shape=(5,))
            interacter = tf.keras.layers.Subtract()
            activation_unit = din.ActivationUnit(10, interacter=interacter)
            outputs = activation_unit(x, y)
            return tf.keras.Model([x, y], outputs)
        x_embeddings = np.random.normal(size=(10, 5))
        y_embeddings = np.random.normal(size=(10, 5))
        labels = np.random.normal(size=(10,))
        model = build_model()
        model.compile(loss='mse')
        model.fit([x_embeddings, y_embeddings], labels, verbose=0)
        model_pred = model.predict([x_embeddings, y_embeddings])
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'din_model')
            model.save(path, options=tf.saved_model.SaveOptions(namespace_whitelist=['din']))
            loaded_model = tf.keras.models.load_model(path)
            loaded_pred = loaded_model.predict([x_embeddings, y_embeddings])
        self.assertAllEqual(model_pred, loaded_pred)

def test_din(self):

    def build_model():
        x = tf.keras.layers.Input(shape=(5,))
        y = tf.keras.layers.Input(shape=(5,))
        interacter = tf.keras.layers.Subtract()
        activation_unit = din.ActivationUnit(10, interacter=interacter)
        outputs = activation_unit(x, y)
        return tf.keras.Model([x, y], outputs)
    x_embeddings = np.random.normal(size=(10, 5))
    y_embeddings = np.random.normal(size=(10, 5))
    labels = np.random.normal(size=(10,))
    model = build_model()
    model.compile(loss='mse')
    model.fit([x_embeddings, y_embeddings], labels, verbose=0)
    model_pred = model.predict([x_embeddings, y_embeddings])
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, 'din_model')
        model.save(path, options=tf.saved_model.SaveOptions(namespace_whitelist=['din']))
        loaded_model = tf.keras.models.load_model(path)
        loaded_pred = loaded_model.predict([x_embeddings, y_embeddings])
    self.assertAllEqual(model_pred, loaded_pred)

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

class TestDeepFM(tf.test.TestCase):

    def test_model_train(self):

        def build_columns():
            user_id = tf.feature_column.categorical_column_with_hash_bucket('user_id', 100)
            movie_id = tf.feature_column.categorical_column_with_hash_bucket('movie_id', 100)
            base_columns = [user_id, movie_id]
            _indicator_columns = [tf.feature_column.indicator_column(c) for c in base_columns]
            _embedding_columns = [tf.feature_column.embedding_column(c, dimension=16) for c in base_columns]
            return (_indicator_columns, _embedding_columns)
        indicator_columns, embedding_columns = build_columns()
        model = DeepFM(indicator_columns, embedding_columns, dnn_units_size=[10, 5])
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

def test_model_train(self):

    def build_columns():
        user_id = tf.feature_column.categorical_column_with_hash_bucket('user_id', 100)
        movie_id = tf.feature_column.categorical_column_with_hash_bucket('movie_id', 100)
        base_columns = [user_id, movie_id]
        _indicator_columns = [tf.feature_column.indicator_column(c) for c in base_columns]
        _embedding_columns = [tf.feature_column.embedding_column(c, dimension=16) for c in base_columns]
        return (_indicator_columns, _embedding_columns)
    indicator_columns, embedding_columns = build_columns()
    model = DeepFM(indicator_columns, embedding_columns, dnn_units_size=[10, 5])
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

class MovieLens(object):

    def __init__(self, filename='movielens.tfrecords'):
        self._filename = os.path.join(os.path.dirname(__file__), filename)
        self._columns = ['UserID', 'MovieID', 'Rating', 'Timestamp', 'Gender', 'Age', 'Occupation', 'Zip-code', 'Title', 'Genres']
        self.num_ratings = 1000209
        self.num_users = 6040
        self.num_movies = 3952
        self.gender_vocab = ['F', 'M']
        self.age_vocab = [1, 18, 25, 35, 45, 50, 56]
        self.occupation_vocab = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
        self.genres_vocab = ['Action', 'Adventure', 'Animation', "Children's", 'Comedy', 'Crime', 'Documentary', 'Drama', 'Fantasy', 'Film-Noir', 'Horror', 'Musical', 'Mystery', 'Romance', 'Sci-Fi', 'Thriller', 'War', 'Western']

    def dataset(self, epochs=1, batch_size=256):

        def _parse_example(serialized_example):
            features = {}
            for c in ['Age', 'Occupation', 'Rating', 'Timestamp']:
                features[c] = tf.io.FixedLenFeature([], tf.int64)
            for c in ['UserID', 'MovieID', 'Gender', 'Zip-code', 'Title']:
                features[c] = tf.io.FixedLenFeature([], tf.string)
            features['Genres'] = tf.io.VarLenFeature(tf.string)
            example = tf.io.parse_example(serialized_example, features)
            ratings = example.pop('Rating')
            return (example, ratings)
        ds = tf.data.TFRecordDataset(self._filename)
        ds = ds.repeat(epochs)
        ds = ds.batch(batch_size)
        ds = ds.map(_parse_example, num_parallel_calls=-1)
        return ds

def __init__(self, filename='movielens.tfrecords'):
    self._filename = os.path.join(os.path.dirname(__file__), filename)
    self._columns = ['UserID', 'MovieID', 'Rating', 'Timestamp', 'Gender', 'Age', 'Occupation', 'Zip-code', 'Title', 'Genres']
    self.num_ratings = 1000209
    self.num_users = 6040
    self.num_movies = 3952
    self.gender_vocab = ['F', 'M']
    self.age_vocab = [1, 18, 25, 35, 45, 50, 56]
    self.occupation_vocab = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
    self.genres_vocab = ['Action', 'Adventure', 'Animation', "Children's", 'Comedy', 'Crime', 'Documentary', 'Drama', 'Fantasy', 'Film-Noir', 'Horror', 'Musical', 'Mystery', 'Romance', 'Sci-Fi', 'Thriller', 'War', 'Western']

