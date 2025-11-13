# Cluster 15

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

def build_model():
    x = tf.keras.layers.Input(shape=(5,))
    y = tf.keras.layers.Input(shape=(5,))
    interacter = tf.keras.layers.Subtract()
    activation_unit = din.ActivationUnit(10, interacter=interacter)
    outputs = activation_unit(x, y)
    return tf.keras.Model([x, y], outputs)

class TestFactorizedTopK(tf.test.TestCase, parameterized.TestCase):

    def test_take_long_axis(self):
        arr = tf.constant([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
        indices = tf.constant([[0, 1], [2, 1]])
        out = factorized_top_k._take_long_axis(arr, indices)
        expected_out = tf.constant([[0.1, 0.2], [0.6, 0.5]])
        self.evaluate(tf.compat.v1.global_variables_initializer())
        self.assertAllClose(out, expected_out)

    def test_exclude(self):
        scores = tf.constant([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
        identifiers = tf.constant([[0, 1, 2], [3, 4, 5]])
        exclude = tf.constant([[1, 2], [3, 5]])
        k = 1
        x, y = factorized_top_k._exclude(scores, identifiers, exclude, k)
        expected_x = tf.constant([[0.1], [0.5]])
        expected_y = tf.constant([[0], [4]])
        self.evaluate(tf.compat.v1.global_variables_initializer())
        self.assertAllClose((x, y), (expected_x, expected_y))

    @parameterized.parameters(np.str, np.float32, np.float64, np.int32, np.int64)
    def test_faiss(self, identifier_dtype):
        num_candidates, num_queries = (5000, 4)
        rng = np.random.RandomState(42)
        candidates = rng.normal(size=(num_candidates, 4)).astype(np.float32)
        query = rng.normal(size=(num_queries, 4)).astype(np.float32)
        candidate_names = np.arange(num_candidates).astype(identifier_dtype)
        faiss_topk = factorized_top_k.Faiss(k=10)
        faiss_topk.index(candidates, candidate_names)
        for _ in range(100):
            pre_serialization_results = faiss_topk(query[:2])
        path = os.path.join(self.get_temp_dir(), 'query_model')
        faiss_topk.save(path, options=tf.saved_model.SaveOptions(namespace_whitelist=['Faiss']))
        loaded = tf.keras.models.load_model(path)
        for _ in range(100):
            post_serialization_results = loaded(tf.constant(query[:2]))
        self.assertAllEqual(post_serialization_results, pre_serialization_results)

    @parameterized.parameters(np.float32, np.float64)
    def test_faiss_with_no_identifiers(self, candidate_dtype):
        """ 测试构建无唯一标识索引 """
        num_candidates = 5000
        candidates = np.random.normal(size=(num_candidates, 4)).astype(candidate_dtype)
        faiss_topk = factorized_top_k.Faiss(k=10)
        faiss_topk.index(candidates, identifiers=None)
        self.evaluate(tf.compat.v1.global_variables_initializer())
        self.assertAllClose(num_candidates, faiss_topk._searcher.ntotal)

    @parameterized.parameters(np.str, np.float32, np.float64, np.int32, np.int64)
    def test_faiss_with_dataset(self, identifier_dtype):
        num_candidates = 5000
        candidates = tf.data.Dataset.from_tensor_slices(np.random.normal(size=(num_candidates, 4)).astype(np.float32))
        identifiers = tf.data.Dataset.from_tensor_slices(np.arange(num_candidates).astype(identifier_dtype))
        faiss_topk = factorized_top_k.Faiss(k=10)
        faiss_topk.index(candidates.batch(100), identifiers=identifiers)
        self.evaluate(tf.compat.v1.global_variables_initializer())
        self.assertAllClose(num_candidates, faiss_topk._searcher.ntotal)

    @parameterized.parameters(factorized_top_k.Streaming, factorized_top_k.BruteForce, factorized_top_k.Faiss, None)
    def test_factorized_topk_metrics(self, top_k_layer):
        rng = np.random.RandomState(42)
        num_candidates, num_queries, embedding_dim = (100, 10, 4)
        candidates = rng.normal(size=(num_candidates, embedding_dim)).astype(np.float32)
        queries = rng.normal(size=(num_queries, embedding_dim)).astype(np.float32)
        true_candidates = rng.normal(size=(num_queries, embedding_dim)).astype(np.float32)
        positive_scores = (queries * true_candidates).sum(axis=1, keepdims=True)
        candidate_scores = queries @ candidates.T
        all_scores = np.concatenate([positive_scores, candidate_scores], axis=1)
        ks = [1, 5, 10, 50]
        candidates = tf.data.Dataset.from_tensor_slices(candidates).batch(32)
        if top_k_layer is not None:
            candidates = top_k_layer().index(candidates)
        metric = FactorizedTopK(candidates=candidates, metrics=[tf.keras.metrics.TopKCategoricalAccuracy(k=x, name=f'top_{x}_categorical_accuracy') for x in ks], k=max(ks))
        metric.update_state(query_embeddings=queries, true_candidate_embeddings=true_candidates)
        for k, metric_value in zip(ks, metric.result()):
            in_top_k = tf.math.in_top_k(targets=np.zeros(num_queries).astype(np.int32), predictions=all_scores, k=k)
            self.assertAllClose(metric_value, in_top_k.numpy().mean())

def test_take_long_axis(self):
    arr = tf.constant([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
    indices = tf.constant([[0, 1], [2, 1]])
    out = factorized_top_k._take_long_axis(arr, indices)
    expected_out = tf.constant([[0.1, 0.2], [0.6, 0.5]])
    self.evaluate(tf.compat.v1.global_variables_initializer())
    self.assertAllClose(out, expected_out)

def test_exclude(self):
    scores = tf.constant([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
    identifiers = tf.constant([[0, 1, 2], [3, 4, 5]])
    exclude = tf.constant([[1, 2], [3, 5]])
    k = 1
    x, y = factorized_top_k._exclude(scores, identifiers, exclude, k)
    expected_x = tf.constant([[0.1], [0.5]])
    expected_y = tf.constant([[0], [4]])
    self.evaluate(tf.compat.v1.global_variables_initializer())
    self.assertAllClose((x, y), (expected_x, expected_y))

@parameterized.parameters(np.str, np.float32, np.float64, np.int32, np.int64)
def test_faiss(self, identifier_dtype):
    num_candidates, num_queries = (5000, 4)
    rng = np.random.RandomState(42)
    candidates = rng.normal(size=(num_candidates, 4)).astype(np.float32)
    query = rng.normal(size=(num_queries, 4)).astype(np.float32)
    candidate_names = np.arange(num_candidates).astype(identifier_dtype)
    faiss_topk = factorized_top_k.Faiss(k=10)
    faiss_topk.index(candidates, candidate_names)
    for _ in range(100):
        pre_serialization_results = faiss_topk(query[:2])
    path = os.path.join(self.get_temp_dir(), 'query_model')
    faiss_topk.save(path, options=tf.saved_model.SaveOptions(namespace_whitelist=['Faiss']))
    loaded = tf.keras.models.load_model(path)
    for _ in range(100):
        post_serialization_results = loaded(tf.constant(query[:2]))
    self.assertAllEqual(post_serialization_results, pre_serialization_results)

@parameterized.parameters(np.float32, np.float64)
def test_faiss_with_no_identifiers(self, candidate_dtype):
    """ 测试构建无唯一标识索引 """
    num_candidates = 5000
    candidates = np.random.normal(size=(num_candidates, 4)).astype(candidate_dtype)
    faiss_topk = factorized_top_k.Faiss(k=10)
    faiss_topk.index(candidates, identifiers=None)
    self.evaluate(tf.compat.v1.global_variables_initializer())
    self.assertAllClose(num_candidates, faiss_topk._searcher.ntotal)

@parameterized.parameters(np.str, np.float32, np.float64, np.int32, np.int64)
def test_faiss_with_dataset(self, identifier_dtype):
    num_candidates = 5000
    candidates = tf.data.Dataset.from_tensor_slices(np.random.normal(size=(num_candidates, 4)).astype(np.float32))
    identifiers = tf.data.Dataset.from_tensor_slices(np.arange(num_candidates).astype(identifier_dtype))
    faiss_topk = factorized_top_k.Faiss(k=10)
    faiss_topk.index(candidates.batch(100), identifiers=identifiers)
    self.evaluate(tf.compat.v1.global_variables_initializer())
    self.assertAllClose(num_candidates, faiss_topk._searcher.ntotal)

@parameterized.parameters(factorized_top_k.Streaming, factorized_top_k.BruteForce, factorized_top_k.Faiss, None)
def test_factorized_topk_metrics(self, top_k_layer):
    rng = np.random.RandomState(42)
    num_candidates, num_queries, embedding_dim = (100, 10, 4)
    candidates = rng.normal(size=(num_candidates, embedding_dim)).astype(np.float32)
    queries = rng.normal(size=(num_queries, embedding_dim)).astype(np.float32)
    true_candidates = rng.normal(size=(num_queries, embedding_dim)).astype(np.float32)
    positive_scores = (queries * true_candidates).sum(axis=1, keepdims=True)
    candidate_scores = queries @ candidates.T
    all_scores = np.concatenate([positive_scores, candidate_scores], axis=1)
    ks = [1, 5, 10, 50]
    candidates = tf.data.Dataset.from_tensor_slices(candidates).batch(32)
    if top_k_layer is not None:
        candidates = top_k_layer().index(candidates)
    metric = FactorizedTopK(candidates=candidates, metrics=[tf.keras.metrics.TopKCategoricalAccuracy(k=x, name=f'top_{x}_categorical_accuracy') for x in ks], k=max(ks))
    metric.update_state(query_embeddings=queries, true_candidate_embeddings=true_candidates)
    for k, metric_value in zip(ks, metric.result()):
        in_top_k = tf.math.in_top_k(targets=np.zeros(num_queries).astype(np.int32), predictions=all_scores, k=k)
        self.assertAllClose(metric_value, in_top_k.numpy().mean())

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

def test_fm_layer(self):
    sparse_inputs = np.random.randint(0, 2, size=(10, 10)).astype(np.float32)
    embedding_inputs = np.random.normal(size=(10, 5, 5)).astype(np.float32)
    x_sum = np.sum(embedding_inputs, axis=1)
    x_square_sum = np.sum(np.power(embedding_inputs, 2), axis=1)
    expected_outputs = 0.5 * np.sum(np.power(x_sum, 2) - x_square_sum, axis=1, keepdims=True)
    outputs = FM()(sparse_inputs, embedding_inputs)
    self.assertAllClose(outputs, expected_outputs)

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

def test_cross_full_matrix(self):
    x0 = np.asarray([[0.1, 0.2, 0.3]]).astype(np.float32)
    x = np.asarray([[0.4, 0.5, 0.6]]).astype(np.float32)
    cross = Cross(projection_dim=None, kernel_init='ones')
    output = cross(x0, x)
    self.evaluate(tf.compat.v1.global_variables_initializer())
    self.assertAllClose(np.asarray([[0.55, 0.8, 1.05]]), output)

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

class TestSBCNM(tf.test.TestCase, parameterized.TestCase):

    @parameterized.parameters(3, 5, 10, 15)
    def test_hard_negative_mining(self, num_hard_negatives):
        logits_shape = (2, 20)
        rng = np.random.RandomState(42)
        logits = rng.uniform(size=logits_shape).astype(np.float32)
        labels = rng.permutation(np.eye(*logits_shape).T).T.astype(np.float32)
        out_logits, out_labels = sbcnm.HardNegativeMining(num_hard_negatives)(logits, labels)
        self.assertEqual(out_logits.shape[-1], num_hard_negatives + 1)
        self.assertAllClose(tf.reduce_sum(out_logits * out_labels, axis=-1), tf.reduce_sum(logits * labels, axis=-1))
        logits = logits + labels * 1000.0
        out_logits, out_labels = sbcnm.HardNegativeMining(num_hard_negatives)(logits, labels)
        out_logits, out_labels = (out_logits.numpy(), out_labels.numpy())
        self.assertAllClose(np.sort(logits, axis=1)[:, -num_hard_negatives - 1:], np.sort(out_logits))

    def test_remove_accidental_negative(self):
        logits_shape = (2, 4)
        rng = np.random.RandomState(42)
        logits = rng.uniform(size=logits_shape).astype(np.float32)
        labels = rng.permutation(np.eye(*logits_shape).T).T.astype(np.float32)
        identifiers = rng.randint(0, 3, size=logits_shape[-1])
        out_logits = sbcnm.RemoveAccidentalNegative()(logits, labels, identifiers)
        self.assertAllClose(tf.reduce_sum(out_logits * labels, axis=1), tf.reduce_sum(logits * labels, axis=1))

@parameterized.parameters(3, 5, 10, 15)
def test_hard_negative_mining(self, num_hard_negatives):
    logits_shape = (2, 20)
    rng = np.random.RandomState(42)
    logits = rng.uniform(size=logits_shape).astype(np.float32)
    labels = rng.permutation(np.eye(*logits_shape).T).T.astype(np.float32)
    out_logits, out_labels = sbcnm.HardNegativeMining(num_hard_negatives)(logits, labels)
    self.assertEqual(out_logits.shape[-1], num_hard_negatives + 1)
    self.assertAllClose(tf.reduce_sum(out_logits * out_labels, axis=-1), tf.reduce_sum(logits * labels, axis=-1))
    logits = logits + labels * 1000.0
    out_logits, out_labels = sbcnm.HardNegativeMining(num_hard_negatives)(logits, labels)
    out_logits, out_labels = (out_logits.numpy(), out_labels.numpy())
    self.assertAllClose(np.sort(logits, axis=1)[:, -num_hard_negatives - 1:], np.sort(out_logits))

def test_remove_accidental_negative(self):
    logits_shape = (2, 4)
    rng = np.random.RandomState(42)
    logits = rng.uniform(size=logits_shape).astype(np.float32)
    labels = rng.permutation(np.eye(*logits_shape).T).T.astype(np.float32)
    identifiers = rng.randint(0, 3, size=logits_shape[-1])
    out_logits = sbcnm.RemoveAccidentalNegative()(logits, labels, identifiers)
    self.assertAllClose(tf.reduce_sum(out_logits * labels, axis=1), tf.reduce_sum(logits * labels, axis=1))

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

def result(self) -> List[tf.Tensor]:
    """Returns a list of metric results."""
    return [metric.result() for metric in self.metrics]

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

def synthetic_data(num_examples, example_dim=100, c=0.3, p=0.8, m=5):
    mu1 = np.random.normal(size=example_dim)
    mu1 = (mu1 - np.mean(mu1)) / (np.std(mu1) * np.sqrt(example_dim))
    mu2 = np.random.normal(size=example_dim)
    mu2 -= mu2.dot(mu1) * mu1
    mu2 /= np.linalg.norm(mu2)
    w1 = c * mu1
    w2 = c * (p * mu1 + np.sqrt(1.0 - p ** 2) * mu2)
    alpha = np.random.normal(size=m)
    beta = np.random.normal(size=m)
    examples = np.random.normal(size=(num_examples, example_dim))
    w1x = np.matmul(examples, w1)
    w2x = np.matmul(examples, w2)
    sin1, sin2 = (0.0, 0.0)
    for i in range(m):
        sin1 += np.sin(alpha[i] * w1x + beta[i])
        sin2 += np.sin(alpha[i] * w2x + beta[i])
    y1 = w1x + sin1 + np.random.normal(size=num_examples, scale=0.01)
    y2 = w2x + sin2 + np.random.normal(size=num_examples, scale=0.01)
    return (examples.astype(np.float32), (y1.astype(np.float32), y2.astype(np.float32)))

