# Cluster 13

class ESMM(object):

    def __init__(self, feature_columns, hidden_units, activation=tf.nn.relu, batch_normalization=False, dropout=None, **kwargs):
        self._columns = feature_columns
        self._hidden_units = hidden_units
        self._activation = activation
        self._batch_norm = batch_normalization
        self._dropout = dropout
        self._configs = kwargs

    def __call__(self, *args, **kwargs):
        return self.call(*args, **kwargs)

    def call(self, features):
        dnn_inputs = tf.feature_column.input_layer(features, self._columns)
        with tf.variable_scope('pCVR'):
            cvr = dnn(dnn_inputs, self._hidden_units + [1], activation=self._activation, batch_normalization=self._batch_norm, dropout=self._dropout, **self._configs)
            p_cvr = tf.nn.sigmoid(cvr)
        with tf.variable_scope('pCTR'):
            ctr = dnn(dnn_inputs, self._hidden_units + [1], activation=self._activation, batch_normalization=self._batch_norm, dropout=self._dropout, **self._configs)
            p_ctr = tf.nn.sigmoid(ctr)
        p_ctcvr = tf.math.multiply(p_ctr, p_cvr)
        return (p_cvr, p_ctr, p_ctcvr)

def __call__(self, *args, **kwargs):
    return self.call(*args, **kwargs)

class MMoE(object):

    def __init__(self, feature_columns, num_tasks, num_experts, expert_hidden_units, task_hidden_units, task_hidden_activation=tf.nn.relu, task_batch_normalization=False, task_dropout=None, expert_hidden_activation=tf.nn.relu, expert_batch_normalization=False, expert_dropout=None):
        self._columns = feature_columns
        self._num_tasks = num_tasks
        self._num_experts = num_experts
        self._expert_hidden_units = expert_hidden_units
        self._task_hidden_units = task_hidden_units
        self._task_hidden_activation = task_hidden_activation
        self._task_batch_norm = task_batch_normalization
        self._task_dropout = task_dropout
        self._expert_hidden_activation = expert_hidden_activation
        self._expert_batch_norm = expert_batch_normalization
        self._expert_dropout = expert_dropout

    def __call__(self, *args, **kwargs):
        return self.call(*args, **kwargs)

    def gating_network(self, inputs):
        """
        Gating network: y = SoftMax(W * inputs)
        """
        x = tf.layers.dense(inputs, units=self._num_experts, use_bias=False)
        return tf.nn.softmax(x)

    def call(self, features):
        inputs = tf.feature_column.input_layer(features, self._columns)
        with tf.variable_scope('mixture_of_experts'):
            experts_outputs = []
            for _ in range(self._num_experts):
                x = dnn(inputs, self._expert_hidden_units, activation=self._expert_hidden_activation, batch_normalization=self._expert_batch_norm, dropout=self._expert_dropout)
                experts_outputs.append(x)
            moe_outputs = tf.stack(experts_outputs, axis=1)
        with tf.variable_scope('multi_gate'):
            mg_outputs = []
            for _ in range(self._num_experts):
                gate = self.gating_network(inputs)
                gate = tf.expand_dims(gate, axis=1)
                output = tf.linalg.matmul(gate, moe_outputs)
                mg_outputs.append(tf.squeeze(output, axis=1))
        outputs = []
        for idx in range(self._num_tasks):
            with tf.variable_scope('task{}'.format(idx)):
                x = dnn(mg_outputs[idx], self._task_hidden_units + [1], activation=self._task_hidden_activation, batch_normalization=self._task_batch_norm, dropout=self._task_dropout)
                outputs.append(x)
        return outputs

def __call__(self, *args, **kwargs):
    return self.call(*args, **kwargs)

class FM(object):
    """
    Factorization Machine
    """

    def __init__(self, indicator_columns, embedding_columns):
        self._indicator_columns = indicator_columns
        self._embedding_columns = embedding_columns

    def __call__(self, *args, **kwargs):
        return self.call(*args, **kwargs)

    def call(self, features):
        with tf.variable_scope('linear'):
            linear_outputs = tf.feature_column.linear_model(features, self._indicator_columns)
        with tf.variable_scope('factorized'):
            self.embeddings = []
            for embedding_column in self._embedding_columns:
                feature_name = embedding_column.name.replace('_embedding', '')
                feature = {feature_name: features.get(feature_name)}
                embedding = tf.feature_column.input_layer(feature, embedding_column)
                self.embeddings.append(embedding)
            stack_embeddings = tf.stack(self.embeddings, axis=1)
            factorized_outputs = fm(stack_embeddings)
        return linear_outputs + factorized_outputs

def __call__(self, *args, **kwargs):
    return self.call(*args, **kwargs)

class FNN(object):

    def __init__(self, indicator_columns, embedding_columns, warmup_from_fm, dnn_units, dnn_activation=tf.nn.relu, dnn_batch_normalization=False, dnn_dropout=None, **dnn_kwargs):
        self._indicator_columns = indicator_columns
        self._embedding_columns = embedding_columns
        self._warmup_from_fm = warmup_from_fm
        self._dnn_hidden_units = dnn_units
        self._dnn_activation = dnn_activation
        self._dnn_batch_norm = dnn_batch_normalization
        self._dnn_dropout = dnn_dropout
        self._dnn_kwargs = dnn_kwargs

    def __call__(self, *args, **kwargs):
        return self.call(*args, **kwargs)

    def warm_up(self):
        with tf.Session(graph=tf.Graph()) as sess:
            tf.saved_model.load(sess, ['serve'], self._warmup_from_fm)
            linear_variables = tf.get_collection(tf.GraphKeys.MODEL_VARIABLES, 'linear')
            linear_variables = {var.name.split('/')[2].replace('_indicator', '') if 'bias' not in var.name else 'bias': sess.run(var) for var in linear_variables}
            factorized_variables = tf.get_collection(tf.GraphKeys.MODEL_VARIABLES, 'factorized')
            factorized_variables = {var.name.split('/')[2].replace('_embedding', ''): sess.run(var) for var in factorized_variables}
            return (linear_variables, factorized_variables)

    def call(self, features):
        linear_variables, factorized_variables = self.warm_up()
        weights = []
        for indicator_column in self._indicator_columns:
            feature_name = indicator_column.categorical_column.key
            feature = {feature_name: features.get(feature_name)}
            sparse = tf.feature_column.input_layer(feature, indicator_column)
            weights_initializer = tf.constant_initializer(linear_variables.get(feature_name))
            weight = tf.layers.dense(sparse, units=1, use_bias=False, kernel_initializer=weights_initializer)
            weights.append(weight)
        concat_weights = tf.concat(weights, axis=1)
        embeddings = []
        for embedding_column in self._embedding_columns:
            feature_name = embedding_column.categorical_column.key
            feature = {feature_name: features.get(feature_name)}
            embedding_column = tf.feature_column.embedding_column(embedding_column.categorical_column, embedding_column.dimension, initializer=tf.constant_initializer(factorized_variables.get(feature_name)))
            embedding = tf.feature_column.input_layer(feature, embedding_column)
            embeddings.append(embedding)
        concat_embeddings = tf.concat(embeddings, axis=1)
        bias = tf.expand_dims(linear_variables.get('bias'), axis=0)
        bias = tf.tile(bias, [tf.shape(concat_weights)[0], 1])
        dnn_inputs = tf.concat([bias, concat_weights, concat_embeddings], axis=1)
        outputs = dnn(dnn_inputs, self._dnn_hidden_units + [1], activation=self._dnn_activation, batch_normalization=self._dnn_batch_norm, dropout=self._dnn_dropout, **self._dnn_kwargs)
        return tf.nn.sigmoid(outputs)

def __call__(self, *args, **kwargs):
    return self.call(*args, **kwargs)

class WDL(object):

    def __init__(self, indicator_columns, embedding_columns, dnn_units, dnn_activation=tf.nn.relu, dnn_batch_normalization=False, dnn_dropout=None, **dnn_kwargs):
        self._indicator_columns = indicator_columns
        self._embedding_columns = embedding_columns
        self._dnn_hidden_units = dnn_units
        self._dnn_activation = dnn_activation
        self._dnn_batch_norm = dnn_batch_normalization
        self._dnn_dropout = dnn_dropout
        self._dnn_kwargs = dnn_kwargs

    def __call__(self, *args, **kwargs):
        return self.call(*args, **kwargs)

    def call(self, features):
        with tf.variable_scope('wide'):
            linear_outputs = tf.feature_column.linear_model(features, self._indicator_columns)
        with tf.variable_scope('deep'):
            embeddings = []
            for embedding_column in self._embedding_columns:
                feature_name = embedding_column.name.replace('_embedding', '')
                feature = {feature_name: features.get(feature_name)}
                embedding = tf.feature_column.input_layer(feature, embedding_column)
                embeddings.append(embedding)
            concat_embeddings = tf.concat(embeddings, axis=1)
            dnn_outputs = dnn(concat_embeddings, self._dnn_hidden_units + [1], activation=self._dnn_activation, batch_normalization=self._dnn_batch_norm, dropout=self._dnn_dropout, **self._dnn_kwargs)
        return tf.nn.sigmoid(linear_outputs + dnn_outputs)

def __call__(self, *args, **kwargs):
    return self.call(*args, **kwargs)

class DeepFM(object):

    def __init__(self, indicator_columns, embedding_columns, dnn_units, dnn_activation=tf.nn.relu, dnn_batch_normalization=False, dnn_dropout=None, **dnn_kwargs):
        self._indicator_columns = indicator_columns
        self._embedding_columns = embedding_columns
        self._dnn_hidden_units = dnn_units
        self._dnn_activation = dnn_activation
        self._dnn_batch_norm = dnn_batch_normalization
        self._dnn_dropout = dnn_dropout
        self._dnn_kwargs = dnn_kwargs

    def __call__(self, *args, **kwargs):
        return self.call(*args, **kwargs)

    def call(self, features):
        fm = FM(self._indicator_columns, self._embedding_columns)
        fm_outputs = fm(features)
        concat_embeddings = tf.concat(fm.embeddings, axis=1)
        dnn_outputs = dnn(concat_embeddings, self._dnn_hidden_units + [1], activation=self._dnn_activation, batch_normalization=self._dnn_batch_norm, dropout=self._dnn_dropout, **self._dnn_kwargs)
        return tf.nn.sigmoid(fm_outputs + dnn_outputs)

def __call__(self, *args, **kwargs):
    return self.call(*args, **kwargs)

