# Cluster 12

class MLP(BaseModel):

    def __init__(self, args, num_users, num_items):
        BaseModel.__init__(self, args, num_users, num_items)
        self.layers = eval(args.layers)
        self.lambda_layers = eval(args.reg_layers)

    def build_core_model(self, user_indices, item_indices):
        init_value = self.init_stddev
        emb_user = tf.Variable(tf.truncated_normal([self.num_users, self.layers[0] // 2], stddev=init_value / math.sqrt(float(self.layers[0] // 2)), mean=0), name='user_embedding', dtype=tf.float32)
        emb_item = tf.Variable(tf.truncated_normal([self.num_items, self.layers[0] // 2], stddev=init_value / math.sqrt(float(self.layers[0] // 2)), mean=0), name='item_embedding', dtype=tf.float32)
        user_feature = tf.nn.embedding_lookup(emb_user, user_indices, name='user_feature')
        item_feature = tf.nn.embedding_lookup(emb_item, item_indices, name='item_feature')
        hidden_layers = [tf.concat([user_feature, item_feature], 1)]
        model_params = [emb_user, emb_item]
        for i in range(1, len(self.layers)):
            w_hidden_layer = tf.Variable(tf.truncated_normal([self.layers[i - 1], self.layers[i]], stddev=init_value, mean=0), name='w_hidden_' + str(i), dtype=tf.float32)
            b_hidden_layer = tf.Variable(tf.truncated_normal([self.layers[i]], stddev=init_value * 0.1, mean=0), name='b_hidden_' + str(i), dtype=tf.float32)
            cur_layer = tf.nn.xw_plus_b(hidden_layers[-1], w_hidden_layer, b_hidden_layer)
            cur_layer = tf.nn.relu(cur_layer)
            hidden_layers.append(cur_layer)
            model_params.append(w_hidden_layer)
            model_params.append(b_hidden_layer)
        return (hidden_layers[-1], self.layers[-1], model_params)

    def build_model(self, user_indices=None, item_indices=None):
        if not user_indices:
            user_indices = tf.placeholder(tf.int32, [None])
        self.user_indices = user_indices
        if not item_indices:
            item_indices = tf.placeholder(tf.int32, [None])
        self.item_indices = item_indices
        self.ratings = tf.placeholder(tf.float32, [None])
        model_vector, model_len, model_params = self.build_core_model(user_indices, item_indices)
        self.output, self.loss, self.error, self.raw_error, self.train_step = self.build_train_model(model_vector, model_len, self.ratings, model_params)

def __init__(self, args, num_users, num_items):
    BaseModel.__init__(self, args, num_users, num_items)
    self.layers = eval(args.layers)
    self.lambda_layers = eval(args.reg_layers)

class NeuMF(BaseModel):

    def __init__(self, args, num_users, num_items):
        BaseModel.__init__(self, args, num_users, num_items)
        self.layers = eval(args.layers)
        self.lambda_layers = eval(args.reg_layers)
        self.num_factors = args.num_factors
        self.model_GMF = GMF(args, num_users, num_items)
        self.model_MLP = MLP(args, num_users, num_items)

    def build_core_model(self, user_indices, item_indices):
        vector_GMF, len_GMF, params_GMF = self.model_GMF.build_core_model(user_indices, item_indices)
        vector_MLP, len_MLP, params_MLP = self.model_MLP.build_core_model(user_indices, item_indices)
        model_vector = tf.concat([vector_GMF, vector_MLP], 1)
        model_len = len_GMF + len_MLP
        model_params = []
        model_params.extend(params_GMF)
        model_params.extend(params_MLP)
        return (model_vector, model_len, model_params)

    def build_model(self, user_indices=None, item_indices=None):
        if not user_indices:
            user_indices = tf.placeholder(tf.int32, [None])
        self.user_indices = user_indices
        if not item_indices:
            item_indices = tf.placeholder(tf.int32, [None])
        self.item_indices = item_indices
        self.ratings = tf.placeholder(tf.float32, [None])
        model_vector, model_len, model_params = self.build_core_model(user_indices, item_indices)
        self.output, self.loss, self.error, self.raw_error, self.train_step = self.build_train_model(model_vector, model_len, self.ratings, model_params)

def __init__(self, args, num_users, num_items):
    BaseModel.__init__(self, args, num_users, num_items)
    self.layers = eval(args.layers)
    self.lambda_layers = eval(args.reg_layers)
    self.num_factors = args.num_factors
    self.model_GMF = GMF(args, num_users, num_items)
    self.model_MLP = MLP(args, num_users, num_items)

class GMF(BaseModel):

    def __init__(self, args, num_users, num_items):
        BaseModel.__init__(self, args, num_users, num_items)
        self.num_factors = args.num_factors

    def build_core_model(self, user_indices, item_indices):
        init_value = self.init_stddev
        emb_user = tf.Variable(tf.truncated_normal([self.num_users, self.num_factors], stddev=init_value / math.sqrt(float(self.num_factors)), mean=0), name='user_embedding', dtype=tf.float32)
        emb_item = tf.Variable(tf.truncated_normal([self.num_items, self.num_factors], stddev=init_value / math.sqrt(float(self.num_factors)), mean=0), name='item_embedding', dtype=tf.float32)
        emb_user_bias = tf.concat([emb_user, tf.ones((self.num_users, 1), dtype=tf.float32) * 0.1], 1, name='user_embedding_bias')
        emb_item_bias = tf.concat([tf.ones((self.num_items, 1), dtype=tf.float32) * 0.1, emb_item], 1, name='item_embedding_bias')
        user_feature = tf.nn.embedding_lookup(emb_user_bias, user_indices, name='user_feature')
        item_feature = tf.nn.embedding_lookup(emb_item_bias, item_indices, name='item_feature')
        product_vector = tf.multiply(user_feature, item_feature)
        model_params = [emb_user, emb_item]
        return (product_vector, self.num_factors + 1, model_params)

    def build_model(self, user_indices=None, item_indices=None):
        if not user_indices:
            user_indices = tf.placeholder(tf.int32, [None])
        self.user_indices = user_indices
        if not item_indices:
            item_indices = tf.placeholder(tf.int32, [None])
        self.item_indices = item_indices
        self.ratings = tf.placeholder(tf.float32, [None])
        model_vector, model_len, model_params = self.build_core_model(user_indices, item_indices)
        self.output, self.loss, self.error, self.raw_error, self.train_step = self.build_train_model(model_vector, model_len, self.ratings, model_params)

def __init__(self, args, num_users, num_items):
    BaseModel.__init__(self, args, num_users, num_items)
    self.num_factors = args.num_factors

