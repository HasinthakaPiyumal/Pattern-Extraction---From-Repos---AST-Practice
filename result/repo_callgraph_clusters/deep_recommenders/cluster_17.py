# Cluster 17

@contextlib.contextmanager
def _wrap_batch_too_small_error(k: int):
    """ Candidate batch too small error """
    try:
        yield
    except tf.errors.InvalidArgumentError as e:
        error_msg = str(e)
        if 'input must have at least k columns' in error_msg:
            raise ValueError('Tried to retrieve k={k} top items, but candidate batch too small.To resolve this, 1. increase batch-size, 2. set `drop_remainder`=True, 3. set `handle_incomplete_batches`=True in constructor.'.format(k=k))

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

def _search(queries, k):
    queries = tf.make_ndarray(tf.make_tensor_proto(queries))
    if self._normalize is True:
        faiss.normalize_L2(queries)
    self._searcher.nprobe = self._nprobe
    distances, indices = self._searcher.search(queries, int(k))
    return (distances, indices)

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

def on_epoch_begin(self, epoch, logs=None):
    if self.verbose:
        lrate = K.get_value(self.model.optimizer.lr)
        print(f'epoch {epoch} lr: {lrate}')

def on_epoch_end(self, epoch, logs=None):
    logs = logs or {}
    logs['lr'] = K.get_value(self.model.optimizer.lr)

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

def _download_and_unzip(filename='ml-1m.zip'):
    import requests
    import zipfile
    url = 'https://files.grouplens.org/datasets/movielens/ml-1m.zip'
    r = requests.get(url)
    with open(filename, 'wb') as f:
        f.write(r.content)
    f = zipfile.ZipFile(filename)
    f.extractall()

def _data_shard(filename, num_shards=4):
    cmd = 'wc -l < {}'.format(filename)
    cmd_res = os.popen(cmd)
    total_lines = int(cmd_res.read().strip())
    block_lines = total_lines // num_shards
    num_lines, num_shard = (0, 0)
    with open(filename, 'r', encoding='unicode_escape') as f:
        for line in f:
            if num_lines % block_lines == 0:
                if num_shard < num_shards:
                    _f = open(filename + str(num_shard), 'w')
                num_shard += 1
            _f.write(line)
            num_lines += 1

def _shuffle_data(filename):
    shuffled_filename = f'{filename}.shuffled'
    with open(filename, 'r') as f:
        lines = f.readlines()
    random.shuffle(lines)
    with open(shuffled_filename, 'w') as f:
        f.writelines(lines)
    return shuffled_filename

def _load_data(filename, columns):
    data = {}
    with open(filename, 'r', encoding='unicode_escape') as f:
        for line in f:
            ls = line.strip('\n').split('::')
            data[ls[0]] = dict(zip(columns[1:], ls[1:]))
    return data

def serialize_tfrecords(tfrecords_fn, datadir='ml-1m', download=False):
    if download is True:
        print('Downloading MovieLens-1M dataset ...')
        _download_and_unzip(datadir + '.zip')
    users_data = _load_data(datadir + '/users.dat', columns=['UserID', 'Gender', 'Age', 'Occupation', 'Zip-code'])
    movies_data = _load_data(datadir + '/movies.dat', columns=['MovieID', 'Title', 'Genres'])
    ratings_columns = ['UserID', 'MovieID', 'Rating', 'Timestamp']
    writer = tf.io.TFRecordWriter(tfrecords_fn)
    shuffled_filename = _shuffle_data(datadir + '/ratings.dat')
    f = open(shuffled_filename, 'r', encoding='unicode_escape')
    for line in f:
        ls = line.strip().split('::')
        rating = dict(zip(ratings_columns, ls))
        rating.update(users_data.get(ls[0]))
        rating.update(movies_data.get(ls[1]))
        for c in ['Age', 'Occupation', 'Rating', 'Timestamp']:
            rating[c] = int(rating[c])
        for c in ['UserID', 'MovieID', 'Gender', 'Zip-code', 'Title']:
            rating[c] = rating[c].encode('utf-8')
        rating['Genres'] = [x.encode('utf-8') for x in rating['Genres'].split('|')]
        serialized = _serialize_example(rating)
        writer.write(serialized)
    writer.close()
    f.close()

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
def train_steps(self):
    num_train_ratings = self.num_ratings * self._epochs * self._train_size
    return int(num_train_ratings // self._batch_size)

@property
def train_steps_per_epoch(self):
    num_train_ratings = self.num_ratings * self._train_size
    return int(num_train_ratings // self._batch_size)

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

def _parse_example(features, labels):
    feature_columns = tf.split(features, self._example_dim, axis=1)
    features = {'C{}'.format(i): col for i, col in enumerate(feature_columns)}
    labels = {'labels{}'.format(i): lab for i, lab in enumerate(labels)}
    return (features, labels)

