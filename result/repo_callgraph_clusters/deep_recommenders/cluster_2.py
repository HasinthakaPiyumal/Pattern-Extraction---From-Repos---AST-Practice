# Cluster 2

def export_saved_model(estimator, export_path):
    indicator_columns, embedding_columns = build_columns()
    columns = indicator_columns + embedding_columns
    feature_spec = tf.feature_column.make_parse_example_spec(columns)
    example_input_fn = tf.estimator.export.build_parsing_serving_input_receiver_fn(feature_spec)
    estimator.export_saved_model(export_path, example_input_fn)

class TestFM(tf.test.TestCase):

    def test_fm(self):
        inputs = tf.random_normal(shape=(10, 2, 3))
        with self.session() as sess:
            y = fm(inputs)
            init = tf.global_variables_initializer()
            sess.run(init)
            pred = sess.run(y)
            self.assertAllEqual(pred.shape, (10, 1))

def test_fm(self):
    inputs = tf.random_normal(shape=(10, 2, 3))
    with self.session() as sess:
        y = fm(inputs)
        init = tf.global_variables_initializer()
        sess.run(init)
        pred = sess.run(y)
        self.assertAllEqual(pred.shape, (10, 1))

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

class TestSyntheticForMultiTask(tf.test.TestCase, parameterized.TestCase):

    @parameterized.parameters(16, 64, 256, 1024)
    def test_input_fn(self, dim):
        synthetic = SyntheticForMultiTask(1000, example_dim=dim)
        dataset = synthetic.input_fn()
        for features, labels in dataset.take(1):
            self.assertAllEqual(len(features.keys()), dim)
            self.assertAllEqual(len(labels.keys()), 2)

    @parameterized.parameters(16, 64, 256, 512)
    def test_batch_size(self, batch_size):
        synthetic = SyntheticForMultiTask(1000)
        dataset = synthetic.input_fn(batch_size=batch_size)
        for features, labels in dataset.take(1):
            self.assertAllEqual(features['C0'].shape, (batch_size, 1))

@parameterized.parameters(16, 64, 256, 1024)
def test_input_fn(self, dim):
    synthetic = SyntheticForMultiTask(1000, example_dim=dim)
    dataset = synthetic.input_fn()
    for features, labels in dataset.take(1):
        self.assertAllEqual(len(features.keys()), dim)
        self.assertAllEqual(len(labels.keys()), 2)

@parameterized.parameters(16, 64, 256, 512)
def test_batch_size(self, batch_size):
    synthetic = SyntheticForMultiTask(1000)
    dataset = synthetic.input_fn(batch_size=batch_size)
    for features, labels in dataset.take(1):
        self.assertAllEqual(features['C0'].shape, (batch_size, 1))

class TestMovieLens(tf.test.TestCase, parameterized.TestCase):

    @parameterized.parameters(16, 64, 256, 1024)
    def test_batch(self, batch_size):
        movielens = MovieLens()
        dataset = movielens.dataset(batch_size=batch_size)
        for x, y in dataset.take(1):
            self.assertAllEqual(x['UserID'].shape, (batch_size,))
            self.assertAllEqual(y.shape, (batch_size,))

    @parameterized.parameters(1, 2, 3)
    def test_repeat(self, epochs):
        movielens = MovieLens()
        dataset = movielens.dataset(epochs, 2048)
        steps = 0
        for _ in dataset:
            steps += 1
        expect_steps = movielens.num_ratings * epochs // 2048 + 1
        self.assertAllEqual(steps, expect_steps)

    def test_map(self):
        movielens = MovieLens()
        dataset = movielens.dataset()
        dataset = dataset.map(lambda _, y: tf.where(y > 3, tf.ones_like(y), tf.zeros_like(y)))
        for y in dataset.take(1):
            self.assertLess(tf.reduce_sum(y), 256)

@parameterized.parameters(16, 64, 256, 1024)
def test_batch(self, batch_size):
    movielens = MovieLens()
    dataset = movielens.dataset(batch_size=batch_size)
    for x, y in dataset.take(1):
        self.assertAllEqual(x['UserID'].shape, (batch_size,))
        self.assertAllEqual(y.shape, (batch_size,))

@parameterized.parameters(1, 2, 3)
def test_repeat(self, epochs):
    movielens = MovieLens()
    dataset = movielens.dataset(epochs, 2048)
    steps = 0
    for _ in dataset:
        steps += 1
    expect_steps = movielens.num_ratings * epochs // 2048 + 1
    self.assertAllEqual(steps, expect_steps)

def test_map(self):
    movielens = MovieLens()
    dataset = movielens.dataset()
    dataset = dataset.map(lambda _, y: tf.where(y > 3, tf.ones_like(y), tf.zeros_like(y)))
    for y in dataset.take(1):
        self.assertLess(tf.reduce_sum(y), 256)

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

def call(self, inputs, **kwargs):
    inputs_mean = tf.math.reduce_mean(inputs, axis=1, keepdims=True)
    inputs_var = tf.math.reduce_std(inputs, axis=1, keepdims=True)
    p = tf.nn.sigmoid((inputs - inputs_mean) / tf.sqrt(inputs_var + self._epsilon))
    x = self.prelu(inputs)
    outputs = tf.where(x > 0, x=p * x, y=(1 - p) * x)
    return outputs

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

def sample_train_nodes(self, labels, num_per_class=20):
    train_nodes = []
    for cls in self._cora_classes:
        cls_index = np.where(labels == cls)[0]
        cls_sample = np.random.choice(cls_index, num_per_class, replace=False)
        train_nodes += cls_sample.tolist()
    return train_nodes

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

class SyntheticForMultiTask(object):

    def __init__(self, num_examples, example_dim=100, c=0.3, p=0.8, m=5):
        self._num_examples = num_examples
        self._example_dim = example_dim
        self._c = c
        self._p = p
        self._m = m

    def input_fn(self, epochs=1, batch_size=512, buffer_size=512):
        synthetic = synthetic_data(self._num_examples, self._example_dim, c=self._c, p=self._p, m=self._m)

        def _parse_example(features, labels):
            feature_columns = tf.split(features, self._example_dim, axis=1)
            features = {'C{}'.format(i): col for i, col in enumerate(feature_columns)}
            labels = {'labels{}'.format(i): lab for i, lab in enumerate(labels)}
            return (features, labels)
        dataset = tf.data.Dataset.from_tensor_slices(synthetic)
        dataset = dataset.repeat(epochs)
        dataset = dataset.batch(batch_size)
        dataset = dataset.map(_parse_example, num_parallel_calls=-1)
        dataset = dataset.prefetch(buffer_size)
        return dataset

def input_fn(self, epochs=1, batch_size=512, buffer_size=512):
    synthetic = synthetic_data(self._num_examples, self._example_dim, c=self._c, p=self._p, m=self._m)

    def _parse_example(features, labels):
        feature_columns = tf.split(features, self._example_dim, axis=1)
        features = {'C{}'.format(i): col for i, col in enumerate(feature_columns)}
        labels = {'labels{}'.format(i): lab for i, lab in enumerate(labels)}
        return (features, labels)
    dataset = tf.data.Dataset.from_tensor_slices(synthetic)
    dataset = dataset.repeat(epochs)
    dataset = dataset.batch(batch_size)
    dataset = dataset.map(_parse_example, num_parallel_calls=-1)
    dataset = dataset.prefetch(buffer_size)
    return dataset

