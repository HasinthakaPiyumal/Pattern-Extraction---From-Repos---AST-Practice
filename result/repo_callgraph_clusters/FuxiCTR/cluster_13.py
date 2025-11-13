# Cluster 13

class WideDeep(BaseModel):

    def __init__(self, feature_map, model_id='WideDeep', wide_learning_rate=0.001, deep_learning_rate=0.001, embedding_dim=10, hidden_units=[64, 64, 64], hidden_activations='ReLU', net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(WideDeep, self).__init__(feature_map, model_id=model_id, **kwargs)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim, embedding_regularizer=embedding_regularizer)
        self.lr_layer = LogisticRegression(feature_map, use_bias=True, regularizer=embedding_regularizer)
        self.emb_out_dim = feature_map.sum_emb_out_dim()
        self.mlp = MLP_Block(input_dim=self.emb_out_dim, output_dim=1, hidden_units=hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm, regularizer=net_regularizer)
        self.compile(kwargs['loss'], wide_learning_rate, deep_learning_rate, kwargs['deep_optimizer'])

    def compile(self, loss='bce', wide_lr=0.0001, deep_lr=0.001, deep_optimizer='adam'):
        super(BaseModel, self).compile(optimizer=[optimizers.Ftrl(learning_rate=wide_lr, l1_regularization_strength=0.1), get_optimizer(deep_optimizer, deep_lr)], loss=get_loss(loss))

    def lr_decay(self, factor=0.1, min_lr=1e-06):
        self.optimizer[1].learning_rate = max(self.optimizer[1].learning_rate * factor, min_lr)
        return self.optimizer[1].lr.numpy()

    @tf.function
    def train_step(self, batch_data):
        with tf.GradientTape(persistent=True) as tape:
            loss = self.get_total_loss(batch_data)
            wide_prefix = 'logistic'
            wide_variables = [var for var in self.trainable_variables if wide_prefix in var.name]
            wide_grads = tape.gradient(loss, wide_variables)
            wide_grads, _ = tf.clip_by_global_norm(wide_grads, self._max_gradient_norm)
            self.optimizer[0].apply_gradients(zip(wide_grads, wide_variables))
            deep_variables = [var for var in self.trainable_variables if wide_prefix not in var.name]
            deep_grads = tape.gradient(loss, deep_variables)
            deep_grads, _ = tf.clip_by_global_norm(deep_grads, self._max_gradient_norm)
            self.optimizer[1].apply_gradients(zip(deep_grads, deep_variables))
        return loss

    def call(self, inputs, training=False):
        X = self.get_inputs(inputs)
        y_pred = self.lr_layer(X)
        feature_emb = self.embedding_layer(X)
        y_pred += self.mlp(tf.reshape(feature_emb, [-1, self.emb_out_dim]))
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

def lr_decay(self, factor=0.1, min_lr=1e-06):
    self.optimizer[1].learning_rate = max(self.optimizer[1].learning_rate * factor, min_lr)
    return self.optimizer[1].lr.numpy()

class Tokenizer(object):

    def __init__(self, max_features=None, na_value='', min_freq=1, splitter=None, remap=True, lower=False, max_len=0, padding='pre'):
        self._max_features = max_features
        self._na_value = na_value
        self._min_freq = min_freq
        self._lower = lower
        self._splitter = splitter
        self.vocab = dict()
        self.max_len = max_len
        self.padding = padding
        self.remap = remap

    def fit_on_texts(self, series):
        max_len = 0
        word_counts = Counter()
        with ProcessPoolExecutor(max_workers=mp.cpu_count() // 2) as executor:
            chunk_size = 1000000
            tasks = []
            for idx in range(0, len(series), chunk_size):
                data_chunk = series.iloc[idx:idx + chunk_size]
                tasks.append(executor.submit(count_tokens, data_chunk, self._splitter))
            for future in tqdm(as_completed(tasks), total=len(tasks)):
                chunk_word_counts, chunk_max_len = future.result()
                word_counts.update(chunk_word_counts)
                max_len = max(max_len, chunk_max_len)
        if self.max_len == 0:
            self.max_len = max_len
        self.build_vocab(word_counts)

    def build_vocab(self, word_counts):
        word_counts = word_counts.most_common()
        if self._max_features:
            word_counts = word_counts[0:self._max_features]
        words = []
        for token, count in word_counts:
            if count >= self._min_freq:
                if token != self._na_value:
                    words.append(token.lower() if self._lower else token)
            else:
                break
        if self.remap:
            self.vocab = dict(((token, idx) for idx, token in enumerate(words, 1)))
        else:
            self.vocab = dict(((token, int(token)) for token in words))
        self.vocab['__PAD__'] = 0
        self.vocab['__OOV__'] = self.vocab_size()

    def merge_vocab(self, shared_tokenizer):
        if self.remap:
            new_words = 0
            for word in self.vocab.keys():
                if word not in shared_tokenizer.vocab:
                    shared_tokenizer.vocab[word] = shared_tokenizer.vocab['__OOV__'] + new_words
                    new_words += 1
        else:
            shared_tokenizer.vocab.update(self.vocab)
        vocab_size = shared_tokenizer.vocab_size()
        if shared_tokenizer.vocab['__OOV__'] != vocab_size - 1 or shared_tokenizer.vocab['__OOV__'] != len(shared_tokenizer.vocab) - 1:
            shared_tokenizer.vocab['__OOV__'] = vocab_size
        self.vocab = shared_tokenizer.vocab
        return shared_tokenizer

    def vocab_size(self):
        return max(self.vocab.values()) + 1

    def update_vocab(self, word_list):
        new_words = 0
        for word in word_list:
            if word not in self.vocab:
                self.vocab[word] = self.vocab.get('__OOV__', 0) + new_words
                new_words += 1
        if new_words > 0:
            self.vocab['__OOV__'] = self.vocab_size()

    def encode_meta(self, series):
        word_counts = dict(series.value_counts())
        if len(self.vocab) == 0:
            self.build_vocab(word_counts)
        else:
            self.update_vocab(word_counts.keys())
        series = series.map(lambda x: self.vocab.get(x, self.vocab['__OOV__']))
        return series.values

    def encode_category(self, series):
        series = series.map(lambda x: self.vocab.get(x, self.vocab['__OOV__']))
        return series.values

    def encode_sequence(self, series):
        series = series.map(lambda text: [self.vocab.get(x, self.vocab['__OOV__']) if x != self._na_value else self.vocab['__PAD__'] for x in text.split(self._splitter)])
        seqs = pad_sequences(series.to_list(), maxlen=self.max_len, value=self.vocab['__PAD__'], padding=self.padding, truncating=self.padding)
        return seqs.tolist()

    def load_pretrained_vocab(self, feature_dtype, pretrain_path, expand_vocab=True):
        keys = load_pretrain_emb(pretrain_path, keys=['key'])
        keys = keys.astype(feature_dtype)
        if expand_vocab:
            vocab_size = self.vocab_size()
            for word in keys:
                if word not in self.vocab:
                    self.vocab[word] = vocab_size
                    vocab_size += 1

def fit_on_texts(self, series):
    max_len = 0
    word_counts = Counter()
    with ProcessPoolExecutor(max_workers=mp.cpu_count() // 2) as executor:
        chunk_size = 1000000
        tasks = []
        for idx in range(0, len(series), chunk_size):
            data_chunk = series.iloc[idx:idx + chunk_size]
            tasks.append(executor.submit(count_tokens, data_chunk, self._splitter))
        for future in tqdm(as_completed(tasks), total=len(tasks)):
            chunk_word_counts, chunk_max_len = future.result()
            word_counts.update(chunk_word_counts)
            max_len = max(max_len, chunk_max_len)
    if self.max_len == 0:
        self.max_len = max_len
    self.build_vocab(word_counts)

def vocab_size(self):
    return max(self.vocab.values()) + 1

def encode_meta(self, series):
    word_counts = dict(series.value_counts())
    if len(self.vocab) == 0:
        self.build_vocab(word_counts)
    else:
        self.update_vocab(word_counts.keys())
    series = series.map(lambda x: self.vocab.get(x, self.vocab['__OOV__']))
    return series.values

def encode_category(self, series):
    series = series.map(lambda x: self.vocab.get(x, self.vocab['__OOV__']))
    return series.values

def encode_sequence(self, series):
    series = series.map(lambda text: [self.vocab.get(x, self.vocab['__OOV__']) if x != self._na_value else self.vocab['__PAD__'] for x in text.split(self._splitter)])
    seqs = pad_sequences(series.to_list(), maxlen=self.max_len, value=self.vocab['__PAD__'], padding=self.padding, truncating=self.padding)
    return seqs.tolist()

def count_tokens(series, splitter=None):
    max_len = 0
    if splitter is not None:
        series = series.map(lambda text: text.split(splitter))
        max_len = series.str.len().max()
        word_counts = series.explode().value_counts()
    else:
        word_counts = series.value_counts()
    return (dict(word_counts), max_len)

class FeatureProcessor(object):

    def __init__(self, feature_cols=[], label_col=[], dataset_id=None, data_root='../data/', **kwargs):
        logging.info('Set up feature processor...')
        self.data_dir = os.path.join(data_root, dataset_id)
        self.pickle_file = os.path.join(self.data_dir, 'feature_processor.pkl')
        self.json_file = os.path.join(self.data_dir, 'feature_map.json')
        self.vocab_file = os.path.join(self.data_dir, 'feature_vocab.json')
        self.feature_cols = self._complete_feature_cols(feature_cols)
        self.label_cols = label_col if type(label_col) == list else [label_col]
        self.feature_map = FeatureMap(dataset_id, self.data_dir)
        self.feature_map.labels = [col['name'] for col in self.label_cols]
        self.feature_map.group_id = kwargs.get('group_id', None)
        self.dtype_dict = dict(((feat['name'], eval(feat['dtype']) if type(feat['dtype']) == str else feat['dtype']) for feat in self.feature_cols + self.label_cols))
        self.processor_dict = dict()

    def _complete_feature_cols(self, feature_cols):
        full_feature_cols = []
        for col in feature_cols:
            name_or_namelist = col['name']
            if isinstance(name_or_namelist, list):
                for _name in name_or_namelist:
                    _col = col.copy()
                    _col['name'] = _name
                    full_feature_cols.append(_col)
            else:
                full_feature_cols.append(col)
        return full_feature_cols

    def read_data(self, data_path, data_format='csv', sep=',', n_rows=None, **kwargs):
        if not data_path.endswith(data_format):
            data_path = os.path.join(data_path, f'*.{data_format}')
        logging.info('Reading files: ' + data_path)
        file_names = sorted(glob.glob(data_path))
        assert len(file_names) > 0, f'Invalid data path: {data_path}'
        if data_format == 'csv':
            dfs = [pl.scan_csv(source=file_name, separator=sep, dtypes=self.dtype_dict, low_memory=False, n_rows=n_rows) for file_name in file_names]
            ddf = pl.concat(dfs)
        elif data_format == 'parquet':
            dfs = [pl.scan_parquet(source=file_name, low_memory=False, n_rows=n_rows) for file_name in file_names]
            ddf = pl.concat(dfs)
        else:
            NotImplementedError(f'data_format={data_format} not supported.')
        return ddf

    def preprocess(self, ddf):
        logging.info('Preprocess feature columns...')
        all_cols = self.label_cols + self.feature_cols[::-1]
        col_names = ddf.columns
        for col in all_cols:
            name = col['name']
            fill_na = None
            if col['dtype'] in ['str', str]:
                fill_na = col.get('fill_na', '')
            elif col['dtype'] in ['int', int]:
                fill_na = col.get('fill_na', 0)
            elif col['dtype'] in ['float', float]:
                fill_na = col.get('fill_na', 0.0)
            col_exist = name in col_names
            if fill_na is not None and col_exist:
                ddf = ddf.with_columns(pl.col(name).fill_null(fill_na))
            if col.get('preprocess'):
                preprocess_args = re.split('\\(|\\)', col['preprocess'])
                preprocess_fn = getattr(self, preprocess_args[0])
                if len(preprocess_args) == 1:
                    preprocess_args = [name]
                else:
                    preprocess_args = preprocess_args[1:-1]
                ddf = ddf.with_columns(preprocess_fn(*preprocess_args).alias(name).cast(self.dtype_dict[name]))
            if fill_na is not None and (not col_exist):
                ddf = ddf.with_columns(pl.col(name).fill_null(fill_na))
            if col.get('type') == 'sequence' and isinstance(ddf.select(name).dtypes[0], pl.List):
                ddf = ddf.with_columns(pl.col(name).apply(lambda x: '^'.join(map(str, x))))
        active_cols = [col['name'] for col in all_cols if col.get('active') != False]
        ddf = ddf.select(active_cols)
        return ddf

    def fit(self, train_ddf, min_categr_count=1, num_buckets=10, rebuild_dataset=True, **kwargs):
        logging.info('Fit feature processor...')
        self.rebuild_dataset = rebuild_dataset
        for col in self.feature_cols:
            name = col['name']
            if col['active']:
                logging.info('Processing column: {}'.format(col))
                col_series = train_ddf.select(name).collect().to_series().to_pandas() if self.rebuild_dataset else None
                if col['type'] == 'meta':
                    self.fit_meta_col(col)
                elif col['type'] == 'numeric':
                    self.fit_numeric_col(col, col_series)
                elif col['type'] == 'embedding':
                    self.fit_embedding_col(col)
                elif col['type'] == 'categorical':
                    self.fit_categorical_col(col, col_series, min_categr_count=min_categr_count, num_buckets=num_buckets)
                elif col['type'] == 'sequence':
                    self.fit_sequence_col(col, col_series, min_categr_count=min_categr_count)
                else:
                    raise NotImplementedError('feature type={}'.format(col['type']))
        os.makedirs(self.data_dir, exist_ok=True)
        for col in self.feature_cols:
            name = col['name']
            if 'pretrained_emb' in col:
                logging.info('Loading pretrained embedding: ' + name)
                if 'pretrain_dim' in col:
                    self.feature_map.features[name]['pretrain_dim'] = col['pretrain_dim']
                ext = Path(col['pretrained_emb']).suffix
                shutil.copy(col['pretrained_emb'], os.path.join(self.data_dir, 'pretrained_{}{}'.format(name, ext)))
                self.feature_map.features[name]['pretrained_emb'] = 'pretrained_{}{}'.format(name, ext)
                self.feature_map.features[name]['freeze_emb'] = col.get('freeze_emb', True)
                self.feature_map.features[name]['pretrain_usage'] = col.get('pretrain_usage', 'init')
                tokenizer = self.processor_dict[name + '::tokenizer']
                tokenizer.load_pretrained_vocab(self.dtype_dict[name], col['pretrained_emb'])
                self.processor_dict[name + '::tokenizer'] = tokenizer
                self.feature_map.features[name]['vocab_size'] = tokenizer.vocab_size()
        for name, spec in self.feature_map.features.items():
            if spec['type'] == 'numeric':
                self.feature_map.total_features += 1
            elif spec['type'] in ['categorical', 'sequence']:
                if 'share_embedding' in spec:
                    tokenizer = self.processor_dict[name + '::tokenizer']
                    tokenizer.vocab = self.processor_dict[spec['share_embedding'] + '::tokenizer'].vocab
                    self.processor_dict[name + '::tokenizer'] = tokenizer
                    self.feature_map.features[name].update({'oov_idx': tokenizer.vocab['__OOV__'], 'vocab_size': tokenizer.vocab_size()})
                else:
                    self.feature_map.total_features += self.feature_map.features[name]['vocab_size']
                if 'pretrained_emb' not in spec:
                    del self.feature_map.features[name]['oov_idx']
        self.feature_map.num_fields = self.feature_map.get_num_fields()
        self.feature_map.set_column_index()
        self.feature_map.save(self.json_file)
        self.save_pickle(self.pickle_file)
        self.save_vocab(self.vocab_file)
        logging.info('Set feature processor done.')

    def fit_meta_col(self, col):
        name = col['name']
        feature_type = col['type']
        self.feature_map.features[name] = {'type': feature_type}
        if col.get('remap', True):
            tokenizer = Tokenizer(min_freq=1, remap=True)
            self.processor_dict[name + '::tokenizer'] = tokenizer

    def fit_numeric_col(self, col, col_series):
        name = col['name']
        feature_type = col['type']
        feature_source = col.get('source', '')
        self.feature_map.features[name] = {'source': feature_source, 'type': feature_type}
        if 'feature_encoder' in col:
            self.feature_map.features[name]['feature_encoder'] = col['feature_encoder']
        if 'embedding_dim' in col:
            self.feature_map.features[name]['embedding_dim'] = col['embedding_dim']
        if 'normalizer' in col:
            normalizer = Normalizer(col['normalizer'])
            if self.rebuild_dataset:
                normalizer.fit(col_series.dropna().values)
            self.processor_dict[name + '::normalizer'] = normalizer

    def fit_embedding_col(self, col):
        name = col['name']
        feature_type = col['type']
        feature_source = col.get('source', '')
        self.feature_map.features[name] = {'source': feature_source, 'type': feature_type}
        if 'feature_encoder' in col:
            self.feature_map.features[name]['feature_encoder'] = col['feature_encoder']
        if 'embedding_dim' in col:
            self.feature_map.features[name]['embedding_dim'] = col['embedding_dim']
        if 'pretrain_dim' in col:
            self.feature_map.features[name]['pretrain_dim'] = col['pretrain_dim']

    def fit_categorical_col(self, col, col_series, min_categr_count=1, num_buckets=10):
        name = col['name']
        feature_type = col['type']
        feature_source = col.get('source', '')
        min_categr_count = col.get('min_categr_count', min_categr_count)
        self.feature_map.features[name] = {'source': feature_source, 'type': feature_type}
        if 'feature_encoder' in col:
            self.feature_map.features[name]['feature_encoder'] = col['feature_encoder']
        if 'embedding_dim' in col:
            self.feature_map.features[name]['embedding_dim'] = col['embedding_dim']
        if 'emb_output_dim' in col:
            self.feature_map.features[name]['emb_output_dim'] = col['emb_output_dim']
        if 'category_processor' not in col:
            tokenizer = Tokenizer(min_freq=min_categr_count, na_value=col.get('fill_na', ''), remap=col.get('remap', True))
            if self.rebuild_dataset:
                tokenizer.fit_on_texts(col_series)
            elif 'vocab_size' in col:
                tokenizer.update_vocab(range(col['vocab_size'] - 1))
            else:
                raise ValueError(f'{name}: vocab_size is required when rebuild_dataset=False')
            if 'share_embedding' in col:
                self.feature_map.features[name]['share_embedding'] = col['share_embedding']
                tknzr_name = col['share_embedding'] + '::tokenizer'
                self.processor_dict[tknzr_name] = tokenizer.merge_vocab(self.processor_dict[tknzr_name])
                self.feature_map.features[col['share_embedding']].update({'oov_idx': self.processor_dict[tknzr_name].vocab['__OOV__'], 'vocab_size': self.processor_dict[tknzr_name].vocab_size()})
            self.processor_dict[name + '::tokenizer'] = tokenizer
            self.feature_map.features[name].update({'padding_idx': 0, 'oov_idx': tokenizer.vocab['__OOV__'], 'vocab_size': tokenizer.vocab_size()})
        else:
            category_processor = col['category_processor']
            self.feature_map.features[name]['category_processor'] = category_processor
            if category_processor == 'quantile_bucket':
                num_buckets = col.get('num_buckets', num_buckets)
                qtf = sklearn_preprocess.QuantileTransformer(n_quantiles=num_buckets + 1)
                if self.rebuild_dataset:
                    qtf.fit(col_series.values)
                    boundaries = qtf.quantiles_[1:-1]
                    self.processor_dict[name + '::boundaries'] = boundaries
                self.feature_map.features[name]['vocab_size'] = num_buckets
            elif category_processor == 'hash_bucket':
                num_buckets = col.get('num_buckets', num_buckets)
                self.feature_map.features[name]['vocab_size'] = num_buckets
                self.processor_dict[name + '::num_buckets'] = num_buckets
            else:
                raise NotImplementedError('category_processor={} not supported.'.format(category_processor))

    def fit_sequence_col(self, col, col_series, min_categr_count=1):
        name = col['name']
        feature_type = col['type']
        feature_source = col.get('source', '')
        min_categr_count = col.get('min_categr_count', min_categr_count)
        self.feature_map.features[name] = {'source': feature_source, 'type': feature_type}
        feature_encoder = col.get('feature_encoder', 'layers.MaskedAveragePooling()')
        if feature_encoder not in [None, 'null', 'None', 'none']:
            self.feature_map.features[name]['feature_encoder'] = feature_encoder
        if 'embedding_dim' in col:
            self.feature_map.features[name]['embedding_dim'] = col['embedding_dim']
        if 'emb_output_dim' in col:
            self.feature_map.features[name]['emb_output_dim'] = col['emb_output_dim']
        splitter = col.get('splitter', '^')
        na_value = col.get('fill_na', '')
        max_len = col.get('max_len', 0)
        padding = col.get('padding', 'post')
        tokenizer = Tokenizer(min_freq=min_categr_count, splitter=splitter, na_value=na_value, max_len=max_len, padding=padding, remap=col.get('remap', True))
        if self.rebuild_dataset:
            tokenizer.fit_on_texts(col_series)
        elif 'vocab_size' in col:
            tokenizer.update_vocab(range(col['vocab_size'] - 1))
        else:
            raise ValueError(f'{name}: vocab_size is required when rebuild_dataset=False')
        if 'share_embedding' in col:
            self.feature_map.features[name]['share_embedding'] = col['share_embedding']
            tknzr_name = col['share_embedding'] + '::tokenizer'
            self.processor_dict[tknzr_name] = tokenizer.merge_vocab(self.processor_dict[tknzr_name])
            self.feature_map.features[col['share_embedding']].update({'oov_idx': self.processor_dict[tknzr_name].vocab['__OOV__'], 'vocab_size': self.processor_dict[tknzr_name].vocab_size()})
        self.processor_dict[name + '::tokenizer'] = tokenizer
        self.feature_map.features[name].update({'padding_idx': 0, 'oov_idx': tokenizer.vocab['__OOV__'], 'max_len': tokenizer.max_len, 'vocab_size': tokenizer.vocab_size()})

    def transform(self, ddf):
        logging.info('Transform feature columns to IDs...')
        for feature, feature_spec in self.feature_map.features.items():
            if feature in ddf.columns:
                feature_type = feature_spec['type']
                col_series = ddf[feature]
                if feature_type == 'meta':
                    if feature + '::tokenizer' in self.processor_dict:
                        tokenizer = self.processor_dict[feature + '::tokenizer']
                        ddf[feature] = tokenizer.encode_meta(col_series)
                        self.processor_dict[feature + '::tokenizer'] = tokenizer
                elif feature_type == 'numeric':
                    normalizer = self.processor_dict.get(feature + '::normalizer')
                    if normalizer:
                        ddf[feature] = normalizer.transform(col_series.values)
                elif feature_type == 'categorical':
                    category_processor = feature_spec.get('category_processor')
                    if category_processor is None:
                        ddf[feature] = self.processor_dict.get(feature + '::tokenizer').encode_category(col_series)
                    elif category_processor == 'numeric_bucket':
                        raise NotImplementedError
                    elif category_processor == 'hash_bucket':
                        raise NotImplementedError
                elif feature_type == 'sequence':
                    ddf[feature] = self.processor_dict.get(feature + '::tokenizer').encode_sequence(col_series)
                elif feature_type == 'embedding':
                    continue
                else:
                    raise NotImplementedError
        return ddf

    def load_pickle(self, pickle_file=None):
        """ Load feature processor from cache """
        if pickle_file is None:
            pickle_file = self.pickle_file
        logging.info('Load feature_processor from pickle: ' + pickle_file)
        if os.path.exists(pickle_file):
            pickled_feature_processor = pickle.load(open(pickle_file, 'rb'))
            if pickled_feature_processor.feature_map.dataset_id == self.feature_map.dataset_id:
                return pickled_feature_processor
        raise IOError('pickle_file={} not valid.'.format(pickle_file))

    def save_pickle(self, pickle_file):
        logging.info('Pickle feature_encode: ' + pickle_file)
        pickle.dump(self, open(pickle_file, 'wb'))

    def save_vocab(self, vocab_file):
        logging.info('Save feature_vocab to json: ' + vocab_file)
        vocab = dict()
        for feature, spec in self.feature_map.features.items():
            if spec['type'] in ['categorical', 'sequence']:
                vocab[feature] = OrderedDict(sorted(self.processor_dict[feature + '::tokenizer'].vocab.items(), key=lambda x: x[1]))
        with open(vocab_file, 'w') as fd:
            fd.write(json.dumps(vocab, indent=4))

    def copy_from(self, src_col):
        return pl.col(src_col)

def preprocess(self, ddf):
    logging.info('Preprocess feature columns...')
    all_cols = self.label_cols + self.feature_cols[::-1]
    col_names = ddf.columns
    for col in all_cols:
        name = col['name']
        fill_na = None
        if col['dtype'] in ['str', str]:
            fill_na = col.get('fill_na', '')
        elif col['dtype'] in ['int', int]:
            fill_na = col.get('fill_na', 0)
        elif col['dtype'] in ['float', float]:
            fill_na = col.get('fill_na', 0.0)
        col_exist = name in col_names
        if fill_na is not None and col_exist:
            ddf = ddf.with_columns(pl.col(name).fill_null(fill_na))
        if col.get('preprocess'):
            preprocess_args = re.split('\\(|\\)', col['preprocess'])
            preprocess_fn = getattr(self, preprocess_args[0])
            if len(preprocess_args) == 1:
                preprocess_args = [name]
            else:
                preprocess_args = preprocess_args[1:-1]
            ddf = ddf.with_columns(preprocess_fn(*preprocess_args).alias(name).cast(self.dtype_dict[name]))
        if fill_na is not None and (not col_exist):
            ddf = ddf.with_columns(pl.col(name).fill_null(fill_na))
        if col.get('type') == 'sequence' and isinstance(ddf.select(name).dtypes[0], pl.List):
            ddf = ddf.with_columns(pl.col(name).apply(lambda x: '^'.join(map(str, x))))
    active_cols = [col['name'] for col in all_cols if col.get('active') != False]
    ddf = ddf.select(active_cols)
    return ddf

def copy_from(self, src_col):
    return pl.col(src_col)

class CustomizedFeatureProcessor(FeatureProcessor):

    def convert_weekday(self, col_name=None):

        def _convert_weekday(timestamp):
            dt = date(int('20' + timestamp[0:2]), int(timestamp[2:4]), int(timestamp[4:6]))
            return int(dt.strftime('%w'))
        return pl.col('hour').apply(_convert_weekday)

    def convert_weekend(self, col_name=None):

        def _convert_weekend(timestamp):
            dt = date(int('20' + timestamp[0:2]), int(timestamp[2:4]), int(timestamp[4:6]))
            return 1 if dt.strftime('%w') in ['6', '0'] else 0
        return pl.col('hour').apply(_convert_weekend)

    def convert_hour(self, col_name=None):
        return pl.col('hour').apply(lambda x: int(x[6:8]))

def convert_weekday(self, col_name=None):

    def _convert_weekday(timestamp):
        dt = date(int('20' + timestamp[0:2]), int(timestamp[2:4]), int(timestamp[4:6]))
        return int(dt.strftime('%w'))
    return pl.col('hour').apply(_convert_weekday)

def convert_weekend(self, col_name=None):

    def _convert_weekend(timestamp):
        dt = date(int('20' + timestamp[0:2]), int(timestamp[2:4]), int(timestamp[4:6]))
        return 1 if dt.strftime('%w') in ['6', '0'] else 0
    return pl.col('hour').apply(_convert_weekend)

def convert_hour(self, col_name=None):
    return pl.col('hour').apply(lambda x: int(x[6:8]))

class CustomizedFeatureProcessor(FeatureProcessor):

    def convert_to_bucket(self, col_name):

        def _convert_to_bucket(value):
            if value > 2:
                value = int(np.floor(np.log(value) ** 2))
            else:
                value = int(value)
            return value
        return pl.col(col_name).apply(_convert_to_bucket).cast(pl.Int32)

def convert_to_bucket(self, col_name):

    def _convert_to_bucket(value):
        if value > 2:
            value = int(np.floor(np.log(value) ** 2))
        else:
            value = int(value)
        return value
    return pl.col(col_name).apply(_convert_to_bucket).cast(pl.Int32)

class CustomizedFeatureProcessor(FeatureProcessor):

    def extract_country_code(self, col_name):
        return pl.col(col_name).apply(lambda isrc: isrc[0:2] if not pl.is_null(isrc) else '')

    def bucketize_age(self, col_name):

        def _bucketize(age):
            if pl.is_null(age):
                return ''
            else:
                age = float(age)
                if age < 1 or age > 95:
                    return ''
                elif age <= 10:
                    return '1'
                elif age <= 20:
                    return '2'
                elif age <= 30:
                    return '3'
                elif age <= 40:
                    return '4'
                elif age <= 50:
                    return '5'
                elif age <= 60:
                    return '6'
                else:
                    return '7'
        return pl.col(col_name).apply(_bucketize)

def extract_country_code(self, col_name):
    return pl.col(col_name).apply(lambda isrc: isrc[0:2] if not pl.is_null(isrc) else '')

def _bucketize(age):
    if pl.is_null(age):
        return ''
    else:
        age = float(age)
        if age < 1 or age > 95:
            return ''
        elif age <= 10:
            return '1'
        elif age <= 20:
            return '2'
        elif age <= 30:
            return '3'
        elif age <= 40:
            return '4'
        elif age <= 50:
            return '5'
        elif age <= 60:
            return '6'
        else:
            return '7'

def bucketize_age(self, col_name):

    def _bucketize(age):
        if pl.is_null(age):
            return ''
        else:
            age = float(age)
            if age < 1 or age > 95:
                return ''
            elif age <= 10:
                return '1'
            elif age <= 20:
                return '2'
            elif age <= 30:
                return '3'
            elif age <= 40:
                return '4'
            elif age <= 50:
                return '5'
            elif age <= 60:
                return '6'
            else:
                return '7'
    return pl.col(col_name).apply(_bucketize)

class TFRecordDataLoader(object):

    def __init__(self, feature_map, stage='both', train_data=None, valid_data=None, test_data=None, batch_size=32, shuffle=True, drop_remainder=False, **kwargs):
        logging.info('Loading data...')
        self.stage = stage
        self.train_data = train_data
        self.valid_data = valid_data
        self.test_data = test_data
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.drop_remainder = drop_remainder
        self.schema = dict()
        for feat, feat_spec in feature_map.features.items():
            if feat_spec['type'] == 'numeric':
                self.schema[feat] = tf.io.FixedLenFeature(dtype=tf.float32, shape=1)
            elif feat_spec['type'] in ['categorical', 'meta']:
                self.schema[feat] = tf.io.FixedLenFeature(dtype=tf.int64, shape=1)
            elif feat_spec['type'] == 'sequence':
                self.schema[feat] = tf.io.FixedLenFeature(dtype=tf.int64, shape=feat_spec['max_len'])
        for label in feature_map.labels:
            self.schema[label] = tf.io.FixedLenFeature(dtype=tf.float32, shape=1)

    def input_fn(self, filenames, batch_size=32, shuffle=True):

        def parse_example(example):
            example_dict = tf.io.parse_single_example(example, features=self.schema)
            return example_dict
        dataset = tf.data.TFRecordDataset(filenames).map(parse_example, num_parallel_calls=1)
        dataset = dataset.prefetch(buffer_size=1).batch(batch_size, drop_remainder=self.drop_remainder)
        if shuffle:
            dataset = dataset.shuffle(batch_size * 10)
        return dataset

    def make_iterator(self):
        if self.stage == 'train':
            logging.info('Loading train and validation data done.')
            return (self.input_fn(self.train_data, batch_size=self.batch_size, shuffle=self.shuffle), self.input_fn(self.valid_data, batch_size=self.batch_size, shuffle=False))
        elif self.stage == 'test':
            logging.info('Loading test data done.')
            return self.input_fn(self.test_data, batch_size=self.batch_size, shuffle=False)
        else:
            logging.info('Loading data done.')
            return (self.input_fn(self.train_data, batch_size=self.batch_size, shuffle=self.shuffle), self.input_fn(self.valid_data, batch_size=self.batch_size, shuffle=False), self.input_fn(self.test_data, batch_size=self.batch_size, shuffle=False))

def input_fn(self, filenames, batch_size=32, shuffle=True):

    def parse_example(example):
        example_dict = tf.io.parse_single_example(example, features=self.schema)
        return example_dict
    dataset = tf.data.TFRecordDataset(filenames).map(parse_example, num_parallel_calls=1)
    dataset = dataset.prefetch(buffer_size=1).batch(batch_size, drop_remainder=self.drop_remainder)
    if shuffle:
        dataset = dataset.shuffle(batch_size * 10)
    return dataset

class BaseModel(Model):

    def __init__(self, feature_map, model_id='BaseModel', task='binary_classification', monitor='AUC', save_best_only=True, monitor_mode='max', early_stop_patience=2, eval_steps=None, reduce_lr_on_plateau=True, **kwargs):
        super(BaseModel, self).__init__()
        self.valid_gen = None
        self._monitor_mode = monitor_mode
        self._monitor = Monitor(kv=monitor)
        self._early_stop_patience = early_stop_patience
        self._eval_steps = eval_steps
        self._save_best_only = save_best_only
        self._verbose = kwargs['verbose']
        self._reduce_lr_on_plateau = reduce_lr_on_plateau
        self.feature_map = feature_map
        self.output_activation = self.get_output_activation(task)
        self.model_id = model_id
        self.model_dir = os.path.join(kwargs['model_root'], feature_map.dataset_id)
        self.checkpoint = os.path.abspath(os.path.join(self.model_dir, self.model_id + '.model'))
        self.validation_metrics = kwargs['metrics']

    def compile(self, optimizer, loss, lr):
        self.optimizer = get_optimizer(optimizer, lr)
        self.loss_fn = get_loss(loss)

    def add_loss(self, inputs):
        return_dict = self(inputs, training=True)
        y_true = self.get_labels(inputs)
        loss = self.loss_fn(return_dict['y_pred'], y_true)
        return loss

    def compute_loss(self, inputs):
        total_loss = self.add_loss(inputs) + sum(self.losses)
        return total_loss

    def get_inputs(self, inputs, feature_source=None):
        if feature_source and type(feature_source) == str:
            feature_source = [feature_source]
        X_dict = dict()
        for feature, spec in self.feature_map.features.items():
            if feature_source is not None and spec['source'] not in feature_source:
                continue
            if spec['type'] == 'meta':
                continue
            X_dict[feature] = inputs[feature]
        return X_dict

    def get_labels(self, inputs):
        """ assert len(labels) == 1, "Please override get_labels() when using multiple labels!"
        """
        labels = self.feature_map.labels
        y = inputs[labels[0]]
        return y

    def get_group_id(self, inputs):
        return inputs[self.feature_map.group_id]

    def lr_decay(self, factor=0.1, min_lr=1e-06):
        self.optimizer.learning_rate = max(self.optimizer.learning_rate * factor, min_lr)
        return self.optimizer.lr.numpy()

    def fit(self, data_generator, epochs=1, validation_data=None, max_gradient_norm=10.0, **kwargs):
        self.valid_gen = validation_data
        self._max_gradient_norm = max_gradient_norm
        self._best_metric = np.Inf if self._monitor_mode == 'min' else -np.Inf
        self._stopping_steps = 0
        self._stop_training = False
        self._total_steps = 0
        self._batch_index = 0
        self._epoch_index = 0
        logging.info('************ Epoch=1 start ************')
        for epoch in range(epochs):
            self._epoch_index = epoch
            self.train_epoch(data_generator)
            if self._stop_training:
                break
            else:
                logging.info('************ Epoch={} end ************'.format(self._epoch_index + 1))
        logging.info('Training finished.')
        logging.info('Load best model: {}'.format(self.checkpoint))
        self.load_weights(self.checkpoint)

    def train_epoch(self, data_generator):
        self._batch_index = 0
        train_loss = 0
        if self._verbose == 0:
            batch_iterator = data_generator
        else:
            batch_iterator = tqdm(data_generator, disable=False, file=sys.stdout)
        for batch_index, batch_data in enumerate(batch_iterator):
            self._batch_index = batch_index
            self._total_steps += 1
            loss = self.train_step(batch_data)
            train_loss += loss.numpy()
            if self._eval_steps is not None and self._total_steps % self._eval_steps == 0:
                logging.info('Train loss: {:.6f}'.format(train_loss / self._eval_steps))
                train_loss = 0
                self.eval_step()
            if self._stop_training:
                break
        if self._eval_steps is None:
            logging.info('Train loss: {:.6f}'.format(train_loss / (self._batch_index + 1)))
            self.eval_step()

    @tf.function
    def train_step(self, batch_data):
        with tf.GradientTape() as tape:
            loss = self.compute_loss(batch_data)
            grads = tape.gradient(loss, self.trainable_variables)
            grads, _ = tf.clip_by_global_norm(grads, self._max_gradient_norm)
            self.optimizer.apply_gradients(zip(grads, self.trainable_variables))
        return loss

    def eval_step(self):
        logging.info('Evaluation @epoch {} - batch {}: '.format(self._epoch_index + 1, self._batch_index + 1))
        val_logs = self.evaluate(self.valid_gen, metrics=self._monitor.get_metrics())
        self.checkpoint_and_earlystop(val_logs)

    def checkpoint_and_earlystop(self, logs, min_delta=1e-06):
        monitor_value = self._monitor.get_value(logs)
        if self._monitor_mode == 'min' and monitor_value > self._best_metric - min_delta or (self._monitor_mode == 'max' and monitor_value < self._best_metric + min_delta):
            self._stopping_steps += 1
            logging.info('Monitor({})={:.6f} STOP!'.format(self._monitor_mode, monitor_value))
            if self._reduce_lr_on_plateau:
                current_lr = self.lr_decay()
                logging.info('Reduce learning rate on plateau: {:.6f}'.format(current_lr))
        else:
            self._stopping_steps = 0
            self._best_metric = monitor_value
            if self._save_best_only:
                logging.info('Save best model: monitor({})={:.6f}'.format(self._monitor_mode, monitor_value))
                self.save_weights(self.checkpoint)
        if self._stopping_steps >= self._early_stop_patience:
            self._stop_training = True
            logging.info('********* Epoch=={} early stop *********'.format(self._epoch_index + 1))
        if not self._save_best_only:
            self.save_weights(self.checkpoint)

    def evaluate(self, data_generator, metrics=None):
        y_pred = []
        y_true = []
        group_id = []
        if self._verbose > 0:
            data_generator = tqdm(data_generator, disable=False, file=sys.stdout)
        for batch_data in data_generator:
            return_dict = self(batch_data, training=True)
            y_pred.extend(return_dict['y_pred'].numpy().reshape(-1))
            y_true.extend(self.get_labels(batch_data).numpy().reshape(-1))
            if self.feature_map.group_id is not None:
                group_id.extend(self.get_group_id(batch_data).numpy().reshape(-1))
        y_pred = np.array(y_pred, np.float64)
        y_true = np.array(y_true, np.float64)
        group_id = np.array(group_id) if len(group_id) > 0 else None
        if metrics is not None:
            val_logs = self.evaluate_metrics(y_true, y_pred, metrics, group_id)
        else:
            val_logs = self.evaluate_metrics(y_true, y_pred, self.validation_metrics, group_id)
        logging.info('[Metrics] ' + ' - '.join(('{}: {:.6f}'.format(k, v) for k, v in val_logs.items())))
        return val_logs

    def evaluate_metrics(self, y_true, y_pred, metrics, group_id=None):
        return evaluate_metrics(y_true, y_pred, metrics, group_id)

    def get_output_activation(self, task):
        if task == 'binary_classification':
            return tf.keras.layers.Activation('sigmoid')
        elif task == 'regression':
            return tf.identity
        else:
            raise NotImplementedError('task={} is not supported.'.format(task))

def lr_decay(self, factor=0.1, min_lr=1e-06):
    self.optimizer.learning_rate = max(self.optimizer.learning_rate * factor, min_lr)
    return self.optimizer.lr.numpy()

class ParquetIterDataPipe(IterDataPipe):

    def __init__(self, data_blocks, feature_map):
        self.feature_map = feature_map
        self.data_blocks = data_blocks

    def load_data(self, data_path):
        df = pd.read_parquet(data_path)
        all_cols = list(self.feature_map.features.keys()) + self.feature_map.labels
        data_arrays = []
        for col in all_cols:
            if df[col].dtype == 'object':
                array = np.array(df[col].to_list())
            else:
                array = df[col].to_numpy()
            data_arrays.append(array)
        return np.column_stack(data_arrays)

    def read_block(self, data_block):
        darray = self.load_data(data_block)
        for idx in range(darray.shape[0]):
            yield darray[idx, :]

    def __iter__(self):
        worker_info = get_worker_info()
        if worker_info is None:
            block_list = self.data_blocks
        else:
            block_list = [block for idx, block in enumerate(self.data_blocks) if idx % worker_info.num_workers == worker_info.id]
        return chain.from_iterable(map(self.read_block, block_list))

def __iter__(self):
    worker_info = get_worker_info()
    if worker_info is None:
        block_list = self.data_blocks
    else:
        block_list = [block for idx, block in enumerate(self.data_blocks) if idx % worker_info.num_workers == worker_info.id]
    return chain.from_iterable(map(self.read_block, block_list))

class NpzIterDataPipe(IterDataPipe):

    def __init__(self, data_blocks, feature_map):
        self.feature_map = feature_map
        self.data_blocks = data_blocks

    def load_data(self, data_path):
        data_dict = np.load(data_path)
        all_cols = list(self.feature_map.features.keys()) + self.feature_map.labels
        data_arrays = [data_dict[col] for col in all_cols]
        return np.column_stack(data_arrays)

    def read_block(self, data_block):
        darray = self.load_data(data_block)
        for idx in range(darray.shape[0]):
            yield darray[idx, :]

    def __iter__(self):
        worker_info = get_worker_info()
        if worker_info is None:
            block_list = self.data_blocks
        else:
            block_list = [block for idx, block in enumerate(self.data_blocks) if idx % worker_info.num_workers == worker_info.id]
        return chain.from_iterable(map(self.read_block, block_list))

def __iter__(self):
    worker_info = get_worker_info()
    if worker_info is None:
        block_list = self.data_blocks
    else:
        block_list = [block for idx, block in enumerate(self.data_blocks) if idx % worker_info.num_workers == worker_info.id]
    return chain.from_iterable(map(self.read_block, block_list))

class BilinearInteraction(nn.Module):

    def __init__(self, num_fields, embedding_dim, bilinear_type='field_interaction'):
        super(BilinearInteraction, self).__init__()
        self.bilinear_type = bilinear_type
        self.interact_dim = int(num_fields * (num_fields - 1) / 2)
        if self.bilinear_type == 'field_all':
            self.bilinear_W = nn.Parameter(torch.Tensor(embedding_dim, embedding_dim))
        elif self.bilinear_type == 'field_each':
            self.bilinear_W = nn.Parameter(torch.Tensor(num_fields, embedding_dim, embedding_dim))
        elif self.bilinear_type == 'field_interaction':
            self.bilinear_W = nn.Parameter(torch.Tensor(self.interact_dim, embedding_dim, embedding_dim))
        else:
            raise NotImplementedError
        self.init_weights()

    def init_weights(self):
        nn.init.xavier_normal_(self.bilinear_W)

    def forward(self, feature_emb):
        feature_emb_list = torch.split(feature_emb, 1, dim=1)
        if self.bilinear_type == 'field_all':
            bilinear_list = [torch.matmul(v_i, self.bilinear_W) * v_j for v_i, v_j in combinations(feature_emb_list, 2)]
        elif self.bilinear_type == 'field_each':
            bilinear_W_list = torch.split(self.bilinear_W, 1, dim=0)
            bilinear_list = [torch.matmul(feature_emb_list[i], bilinear_W_list[i]) * feature_emb_list[j] for i, j in combinations(range(len(feature_emb_list)), 2)]
        elif self.bilinear_type == 'field_interaction':
            bilinear_W_list = torch.split(self.bilinear_W, 1, dim=0)
            bilinear_list = [torch.matmul(v[0], bilinear_W_list[i]) * v[1] for i, v in enumerate(combinations(feature_emb_list, 2))]
        return torch.cat(bilinear_list, dim=1)

def forward(self, feature_emb):
    feature_emb_list = torch.split(feature_emb, 1, dim=1)
    if self.bilinear_type == 'field_all':
        bilinear_list = [torch.matmul(v_i, self.bilinear_W) * v_j for v_i, v_j in combinations(feature_emb_list, 2)]
    elif self.bilinear_type == 'field_each':
        bilinear_W_list = torch.split(self.bilinear_W, 1, dim=0)
        bilinear_list = [torch.matmul(feature_emb_list[i], bilinear_W_list[i]) * feature_emb_list[j] for i, j in combinations(range(len(feature_emb_list)), 2)]
    elif self.bilinear_type == 'field_interaction':
        bilinear_W_list = torch.split(self.bilinear_W, 1, dim=0)
        bilinear_list = [torch.matmul(v[0], bilinear_W_list[i]) * v[1] for i, v in enumerate(combinations(feature_emb_list, 2))]
    return torch.cat(bilinear_list, dim=1)

class BaseModel(nn.Module):

    def __init__(self, feature_map, model_id='BaseModel', task='binary_classification', gpu=-1, monitor='AUC', save_best_only=True, monitor_mode='max', early_stop_patience=2, eval_steps=None, embedding_regularizer=None, net_regularizer=None, reduce_lr_on_plateau=True, **kwargs):
        super(BaseModel, self).__init__()
        self.device = get_device(gpu)
        self._monitor = Monitor(kv=monitor)
        self._monitor_mode = monitor_mode
        self._early_stop_patience = early_stop_patience
        self._eval_steps = eval_steps
        self._save_best_only = save_best_only
        self._embedding_regularizer = embedding_regularizer
        self._net_regularizer = net_regularizer
        self._reduce_lr_on_plateau = reduce_lr_on_plateau
        self._verbose = kwargs['verbose']
        self.feature_map = feature_map
        self.output_activation = self.get_output_activation(task)
        self.model_id = model_id
        self.model_dir = os.path.join(kwargs['model_root'], feature_map.dataset_id)
        self.checkpoint = os.path.abspath(os.path.join(self.model_dir, self.model_id + '.model'))
        self.validation_metrics = kwargs['metrics']

    def compile(self, optimizer, loss, lr):
        self.optimizer = get_optimizer(optimizer, self.parameters(), lr)
        self.loss_fn = get_loss(loss)

    def regularization_loss(self):
        reg_term = 0
        if self._embedding_regularizer or self._net_regularizer:
            emb_reg = get_regularizer(self._embedding_regularizer)
            net_reg = get_regularizer(self._net_regularizer)
            emb_params = set()
            for m_name, module in self.named_modules():
                if type(module) == FeatureEmbeddingDict:
                    for p_name, param in module.named_parameters():
                        if param.requires_grad:
                            emb_params.add('.'.join([m_name, p_name]))
                            for emb_p, emb_lambda in emb_reg:
                                reg_term += emb_lambda / emb_p * torch.norm(param, emb_p) ** emb_p
            for name, param in self.named_parameters():
                if param.requires_grad:
                    if name not in emb_params:
                        for net_p, net_lambda in net_reg:
                            reg_term += net_lambda / net_p * torch.norm(param, net_p) ** net_p
        return reg_term

    def add_loss(self, return_dict, y_true):
        loss = self.loss_fn(return_dict['y_pred'], y_true, reduction='mean')
        return loss

    def compute_loss(self, return_dict, y_true):
        loss = self.add_loss(return_dict, y_true) + self.regularization_loss()
        return loss

    def reset_parameters(self):

        def default_reset_params(m):
            if type(m) in [nn.Linear, nn.Conv1d]:
                nn.init.xavier_normal_(m.weight)
                if m.bias is not None:
                    m.bias.data.fill_(0)

        def custom_reset_params(m):
            if hasattr(m, 'init_weights'):
                m.init_weights()
        self.apply(default_reset_params)
        self.apply(custom_reset_params)

    def get_inputs(self, inputs, feature_source=None):
        X_dict = dict()
        for feature in inputs.keys():
            if feature in self.feature_map.labels:
                continue
            spec = self.feature_map.features[feature]
            if spec['type'] == 'meta':
                continue
            if feature_source and not_in_whitelist(spec['source'], feature_source):
                continue
            X_dict[feature] = inputs[feature].to(self.device)
        return X_dict

    def get_labels(self, inputs):
        """ Please override get_labels() when using multiple labels!
        """
        labels = self.feature_map.labels
        y = inputs[labels[0]].to(self.device)
        return y.float().view(-1, 1)

    def get_group_id(self, inputs):
        return inputs[self.feature_map.group_id]

    def model_to_device(self):
        self.to(device=self.device)

    def lr_decay(self, factor=0.1, min_lr=1e-06):
        for param_group in self.optimizer.param_groups:
            reduced_lr = max(param_group['lr'] * factor, min_lr)
            param_group['lr'] = reduced_lr
        return reduced_lr

    def fit(self, data_generator, epochs=1, validation_data=None, max_gradient_norm=10.0, **kwargs):
        self.valid_gen = validation_data
        self._max_gradient_norm = max_gradient_norm
        self._best_metric = np.Inf if self._monitor_mode == 'min' else -np.Inf
        self._stopping_steps = 0
        self._steps_per_epoch = len(data_generator)
        self._stop_training = False
        self._total_steps = 0
        self._batch_index = 0
        self._epoch_index = 0
        if self._eval_steps is None:
            self._eval_steps = self._steps_per_epoch
        logging.info('Start training: {} batches/epoch'.format(self._steps_per_epoch))
        logging.info('************ Epoch=1 start ************')
        for epoch in range(epochs):
            self._epoch_index = epoch
            self.train_epoch(data_generator)
            if self._stop_training:
                break
            else:
                logging.info('************ Epoch={} end ************'.format(self._epoch_index + 1))
        logging.info('Training finished.')
        logging.info('Load best model: {}'.format(self.checkpoint))
        self.load_weights(self.checkpoint)

    def checkpoint_and_earlystop(self, logs, min_delta=1e-06):
        monitor_value = self._monitor.get_value(logs)
        if self._monitor_mode == 'min' and monitor_value > self._best_metric - min_delta or (self._monitor_mode == 'max' and monitor_value < self._best_metric + min_delta):
            self._stopping_steps += 1
            logging.info('Monitor({})={:.6f} STOP!'.format(self._monitor_mode, monitor_value))
            if self._reduce_lr_on_plateau:
                current_lr = self.lr_decay()
                logging.info('Reduce learning rate on plateau: {:.6f}'.format(current_lr))
        else:
            self._stopping_steps = 0
            self._best_metric = monitor_value
            if self._save_best_only:
                logging.info('Save best model: monitor({})={:.6f}'.format(self._monitor_mode, monitor_value))
                self.save_weights(self.checkpoint)
        if self._stopping_steps >= self._early_stop_patience:
            self._stop_training = True
            logging.info('********* Epoch={} early stop *********'.format(self._epoch_index + 1))
        if not self._save_best_only:
            self.save_weights(self.checkpoint)

    def eval_step(self):
        logging.info('Evaluation @epoch {} - batch {}: '.format(self._epoch_index + 1, self._batch_index + 1))
        val_logs = self.evaluate(self.valid_gen, metrics=self._monitor.get_metrics())
        self.checkpoint_and_earlystop(val_logs)
        self.train()

    def train_step(self, batch_data):
        self.optimizer.zero_grad()
        return_dict = self.forward(batch_data)
        y_true = self.get_labels(batch_data)
        loss = self.compute_loss(return_dict, y_true)
        loss.backward()
        nn.utils.clip_grad_norm_(self.parameters(), self._max_gradient_norm)
        self.optimizer.step()
        return loss

    def train_epoch(self, data_generator):
        self._batch_index = 0
        train_loss = 0
        self.train()
        if self._verbose == 0:
            batch_iterator = data_generator
        else:
            batch_iterator = tqdm(data_generator, disable=False, file=sys.stdout)
        for batch_index, batch_data in enumerate(batch_iterator):
            self._batch_index = batch_index
            self._total_steps += 1
            loss = self.train_step(batch_data)
            train_loss += loss.item()
            if self._total_steps % self._eval_steps == 0:
                logging.info('Train loss: {:.6f}'.format(train_loss / self._eval_steps))
                train_loss = 0
                self.eval_step()
            if self._stop_training:
                break

    def evaluate(self, data_generator, metrics=None):
        self.eval()
        with torch.no_grad():
            y_pred = []
            y_true = []
            group_id = []
            if self._verbose > 0:
                data_generator = tqdm(data_generator, disable=False, file=sys.stdout)
            for batch_data in data_generator:
                return_dict = self.forward(batch_data)
                y_pred.extend(return_dict['y_pred'].data.cpu().numpy().reshape(-1))
                y_true.extend(self.get_labels(batch_data).data.cpu().numpy().reshape(-1))
                if self.feature_map.group_id is not None:
                    group_id.extend(self.get_group_id(batch_data).numpy().reshape(-1))
            y_pred = np.array(y_pred, np.float64)
            y_true = np.array(y_true, np.float64)
            group_id = np.array(group_id) if len(group_id) > 0 else None
            if metrics is not None:
                val_logs = self.evaluate_metrics(y_true, y_pred, metrics, group_id)
            else:
                val_logs = self.evaluate_metrics(y_true, y_pred, self.validation_metrics, group_id)
            logging.info('[Metrics] ' + ' - '.join(('{}: {:.6f}'.format(k, v) for k, v in val_logs.items())))
            return val_logs

    def predict(self, data_generator):
        self.eval()
        with torch.no_grad():
            y_pred = []
            if self._verbose > 0:
                data_generator = tqdm(data_generator, disable=False, file=sys.stdout)
            for batch_data in data_generator:
                return_dict = self.forward(batch_data)
                y_pred.extend(return_dict['y_pred'].data.cpu().numpy().reshape(-1))
            y_pred = np.array(y_pred, np.float64)
            return y_pred

    def evaluate_metrics(self, y_true, y_pred, metrics, group_id=None):
        return evaluate_metrics(y_true, y_pred, metrics, group_id)

    def save_weights(self, checkpoint):
        torch.save(self.state_dict(), checkpoint)

    def load_weights(self, checkpoint):
        self.to(self.device)
        state_dict = torch.load(checkpoint, map_location='cpu')
        self.load_state_dict(state_dict)

    def get_output_activation(self, task):
        if task == 'binary_classification':
            return nn.Sigmoid()
        elif task == 'regression':
            return nn.Identity()
        else:
            raise NotImplementedError('task={} is not supported.'.format(task))

    def count_parameters(self, count_embedding=True):
        total_params = 0
        for name, param in self.named_parameters():
            if not count_embedding and 'embedding' in name:
                continue
            if param.requires_grad:
                total_params += param.numel()
        logging.info('Total number of parameters: {}.'.format(total_params))

def reset_parameters(self):

    def default_reset_params(m):
        if type(m) in [nn.Linear, nn.Conv1d]:
            nn.init.xavier_normal_(m.weight)
            if m.bias is not None:
                m.bias.data.fill_(0)

    def custom_reset_params(m):
        if hasattr(m, 'init_weights'):
            m.init_weights()
    self.apply(default_reset_params)
    self.apply(custom_reset_params)

def lr_decay(self, factor=0.1, min_lr=1e-06):
    for param_group in self.optimizer.param_groups:
        reduced_lr = max(param_group['lr'] * factor, min_lr)
        param_group['lr'] = reduced_lr
    return reduced_lr

class CustomizedFeatureProcessor(FeatureProcessor):
    """
    This is a demo for implementing customized feature processing functions.

    In the config/example7_config/dataset_config.yaml file, the 'convert_weekday' and 'convert_hour'
    processors are called. Hence, it is necessary to implement the two functions by inheriting from
    'fuxictr.preprocess.FeatureProcessor'. Some concrete examples can be found in 'fuxictr.datasets'.

    Each processor function ONLY accepts one argument: col_name, and returns an expression based on 
    polars. We use polars instead of pandas for speedup.
    """

    def convert_weekday(self, col_name=None):

        def _convert_weekday(timestamp):
            dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            return int(dt.strftime('%w'))
        return pl.col('time_stamp').apply(_convert_weekday)

    def convert_hour(self, col_name=None):

        def _convert_hour(timestamp):
            dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            return int(dt.hour)
        return pl.col('time_stamp').apply(_convert_hour)

def convert_weekday(self, col_name=None):

    def _convert_weekday(timestamp):
        dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        return int(dt.strftime('%w'))
    return pl.col('time_stamp').apply(_convert_weekday)

def convert_hour(self, col_name=None):

    def _convert_hour(timestamp):
        dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        return int(dt.hour)
    return pl.col('time_stamp').apply(_convert_hour)

