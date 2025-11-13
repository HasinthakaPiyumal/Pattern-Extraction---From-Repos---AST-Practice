# Cluster 0

def build_columns():
    movielens = MovielensRanking()
    user_id = tf.feature_column.categorical_column_with_hash_bucket('user_id', movielens.num_users)
    user_gender = tf.feature_column.categorical_column_with_vocabulary_list('user_gender', movielens.gender_vocab)
    user_age = tf.feature_column.categorical_column_with_vocabulary_list('user_age', movielens.age_vocab)
    user_occupation = tf.feature_column.categorical_column_with_vocabulary_list('user_occupation', movielens.occupation_vocab)
    movie_id = tf.feature_column.categorical_column_with_hash_bucket('movie_id', movielens.num_movies)
    movie_genres = tf.feature_column.categorical_column_with_vocabulary_list('movie_genres', movielens.gender_vocab)
    base_columns = [user_id, user_gender, user_age, user_occupation, movie_id, movie_genres]
    indicator_columns = [tf.feature_column.indicator_column(c) for c in base_columns]
    embedding_columns = [tf.feature_column.embedding_column(c, dimension=16) for c in base_columns]
    return (indicator_columns, embedding_columns)

def main():
    tf.logging.set_verbosity(tf.logging.INFO)
    estimator = build_estimator({'warm_up_from_fm': 'FM'})
    early_stop_hook = tf.estimator.experimental.stop_if_no_decrease_hook(estimator, 'loss', 1000)
    movielens = MovielensRanking()
    train_spec = tf.estimator.TrainSpec(lambda: movielens.training_input_fn, max_steps=None, hooks=[early_stop_hook])
    eval_spec = tf.estimator.EvalSpec(lambda: movielens.testing_input_fn, steps=None, start_delay_secs=0, throttle_secs=0)
    tf.estimator.train_and_evaluate(estimator, train_spec, eval_spec)

def build_columns():
    movielens = MovielensRanking()
    user_id = tf.feature_column.categorical_column_with_hash_bucket('user_id', movielens.num_users)
    user_gender = tf.feature_column.categorical_column_with_vocabulary_list('user_gender', movielens.gender_vocab)
    user_age = tf.feature_column.categorical_column_with_vocabulary_list('user_age', movielens.age_vocab)
    user_occupation = tf.feature_column.categorical_column_with_vocabulary_list('user_occupation', movielens.occupation_vocab)
    movie_id = tf.feature_column.categorical_column_with_hash_bucket('movie_id', movielens.num_movies)
    movie_genres = tf.feature_column.categorical_column_with_vocabulary_list('movie_genres', movielens.gender_vocab)
    base_columns = [user_id, user_gender, user_age, user_occupation, movie_id, movie_genres]
    indicator_columns = [tf.feature_column.indicator_column(c) for c in base_columns]
    embedding_columns = [tf.feature_column.embedding_column(c, dimension=16) for c in base_columns]
    return (indicator_columns, embedding_columns)

def main():
    tf.logging.set_verbosity(tf.logging.INFO)
    estimator = build_estimator()
    early_stop_hook = tf.estimator.experimental.stop_if_no_decrease_hook(estimator, 'loss', 1000)
    movielens = MovielensRanking()
    train_spec = tf.estimator.TrainSpec(lambda: movielens.training_input_fn, max_steps=None, hooks=[early_stop_hook])
    eval_spec = tf.estimator.EvalSpec(lambda: movielens.testing_input_fn, steps=None, start_delay_secs=0, throttle_secs=0)
    tf.estimator.train_and_evaluate(estimator, train_spec, eval_spec)

def build_columns():
    movielens = MovielensRanking()
    user_id = tf.feature_column.categorical_column_with_hash_bucket('user_id', movielens.num_users)
    user_gender = tf.feature_column.categorical_column_with_vocabulary_list('user_gender', movielens.gender_vocab)
    user_age = tf.feature_column.categorical_column_with_vocabulary_list('user_age', movielens.age_vocab)
    user_occupation = tf.feature_column.categorical_column_with_vocabulary_list('user_occupation', movielens.occupation_vocab)
    movie_id = tf.feature_column.categorical_column_with_hash_bucket('movie_id', movielens.num_movies)
    movie_genres = tf.feature_column.categorical_column_with_vocabulary_list('movie_genres', movielens.gender_vocab)
    base_columns = [user_id, user_gender, user_age, user_occupation, movie_id, movie_genres]
    indicator_columns = [tf.feature_column.indicator_column(c) for c in base_columns]
    embedding_columns = [tf.feature_column.embedding_column(c, dimension=16) for c in base_columns]
    return (indicator_columns, embedding_columns)

def build_columns():
    movielens = MovielensRanking()
    user_id = tf.feature_column.categorical_column_with_hash_bucket('user_id', movielens.num_users)
    user_gender = tf.feature_column.categorical_column_with_vocabulary_list('user_gender', movielens.gender_vocab)
    user_age = tf.feature_column.categorical_column_with_vocabulary_list('user_age', movielens.age_vocab)
    user_occupation = tf.feature_column.categorical_column_with_vocabulary_list('user_occupation', movielens.occupation_vocab)
    movie_id = tf.feature_column.categorical_column_with_hash_bucket('movie_id', movielens.num_movies)
    movie_genres = tf.feature_column.categorical_column_with_vocabulary_list('movie_genres', movielens.gender_vocab)
    base_columns = [user_id, user_gender, user_age, user_occupation, movie_id, movie_genres]
    indicator_columns = [tf.feature_column.indicator_column(c) for c in base_columns]
    embedding_columns = [tf.feature_column.embedding_column(c, dimension=16) for c in base_columns]
    return (indicator_columns, embedding_columns)

def main():
    tf.logging.set_verbosity(tf.logging.INFO)
    estimator = build_estimator()
    early_stop_hook = tf.estimator.experimental.stop_if_no_decrease_hook(estimator, 'loss', 1000)
    movielens = MovielensRanking()
    train_spec = tf.estimator.TrainSpec(lambda: movielens.training_input_fn, max_steps=None, hooks=[early_stop_hook])
    eval_spec = tf.estimator.EvalSpec(lambda: movielens.testing_input_fn, steps=None, start_delay_secs=0, throttle_secs=0)
    tf.estimator.train_and_evaluate(estimator, train_spec, eval_spec)

def build_columns():
    movielens = MovielensRanking()
    user_id = tf.feature_column.categorical_column_with_hash_bucket('user_id', movielens.num_users)
    user_gender = tf.feature_column.categorical_column_with_vocabulary_list('user_gender', movielens.gender_vocab)
    user_age = tf.feature_column.categorical_column_with_vocabulary_list('user_age', movielens.age_vocab)
    user_occupation = tf.feature_column.categorical_column_with_vocabulary_list('user_occupation', movielens.occupation_vocab)
    movie_id = tf.feature_column.categorical_column_with_hash_bucket('movie_id', movielens.num_movies)
    movie_genres = tf.feature_column.categorical_column_with_vocabulary_list('movie_genres', movielens.gender_vocab)
    base_columns = [user_id, user_gender, user_age, user_occupation, movie_id, movie_genres]
    indicator_columns = [tf.feature_column.indicator_column(c) for c in base_columns]
    embedding_columns = [tf.feature_column.embedding_column(c, dimension=16) for c in base_columns]
    return (indicator_columns, embedding_columns)

def cross_product_transformation():
    crossed_columns = [tf.feature_column.crossed_column(['user_gender', 'user_age'], 14), tf.feature_column.crossed_column(['user_gender', 'user_occupation'], 40), tf.feature_column.crossed_column(['user_age', 'user_occupation'], 140)]
    crossed_product_columns = [tf.feature_column.indicator_column(c) for c in crossed_columns]
    return crossed_product_columns

def main():
    tf.logging.set_verbosity(tf.logging.INFO)
    estimator = build_estimator()
    early_stop_hook = tf.estimator.experimental.stop_if_no_decrease_hook(estimator, 'loss', 1000)
    movielens = MovielensRanking()
    train_spec = tf.estimator.TrainSpec(lambda: movielens.training_input_fn, max_steps=None, hooks=[early_stop_hook])
    eval_spec = tf.estimator.EvalSpec(lambda: movielens.testing_input_fn, steps=None, start_delay_secs=0, throttle_secs=0)
    tf.estimator.train_and_evaluate(estimator, train_spec, eval_spec)

def main():
    tf.logging.set_verbosity(tf.logging.INFO)
    estimator = build_estimator()
    early_stop_hook = tf.estimator.experimental.stop_if_no_decrease_hook(estimator, 'loss', 1000)
    synthetic = SyntheticForMultiTask(512 * 1000, example_dim=EXAMPLE_DIM)
    train_spec = tf.estimator.TrainSpec(lambda: synthetic.input_fn().take(800), max_steps=None, hooks=[early_stop_hook])
    eval_spec = tf.estimator.EvalSpec(lambda: synthetic.input_fn().skip(800).take(200), steps=None, start_delay_secs=60, throttle_secs=60)
    tf.estimator.train_and_evaluate(estimator, train_spec, eval_spec)

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

def build_columns():
    user_id = tf.feature_column.categorical_column_with_hash_bucket('user_id', 100)
    movie_id = tf.feature_column.categorical_column_with_hash_bucket('movie_id', 100)
    base_columns = [user_id, movie_id]
    _indicator_columns = [tf.feature_column.indicator_column(c) for c in base_columns]
    _embedding_columns = [tf.feature_column.embedding_column(c, dimension=16) for c in base_columns]
    return (_indicator_columns, _embedding_columns)

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

def build_columns():
    user_id = tf.feature_column.categorical_column_with_hash_bucket('user_id', 100)
    movie_id = tf.feature_column.categorical_column_with_hash_bucket('movie_id', 100)
    base_columns = [user_id, movie_id]
    _indicator_columns = [tf.feature_column.indicator_column(c) for c in base_columns]
    _embedding_columns = [tf.feature_column.embedding_column(c, dimension=16) for c in base_columns]
    return (_indicator_columns, _embedding_columns)

