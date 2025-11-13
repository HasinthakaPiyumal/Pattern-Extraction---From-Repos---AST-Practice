# Cluster 5

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

def call(self, x_embeddings, y_embeddings=None, **kwargs):
    if y_embeddings is None:
        y_embeddings = x_embeddings
    x = tf.concat([x_embeddings, y_embeddings], axis=1)
    if self._interacter is not None:
        x = tf.concat([x, self._interacter([x_embeddings, y_embeddings])], axis=1)
    x = self.dense_kernel(x)
    return self.dense_output(x)

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

def call(self, features):
    fm = FM(self._indicator_columns, self._embedding_columns)
    fm_outputs = fm(features)
    concat_embeddings = tf.concat(fm.embeddings, axis=1)
    dnn_outputs = dnn(concat_embeddings, self._dnn_hidden_units + [1], activation=self._dnn_activation, batch_normalization=self._dnn_batch_norm, dropout=self._dnn_dropout, **self._dnn_kwargs)
    return tf.nn.sigmoid(fm_outputs + dnn_outputs)

