# Cluster 7

@describe
def count_params(model, mode='trainable'):
    """ count all parameters of a tensorflow graph
    """
    if mode == 'all':
        num = np.sum([np.product([xi.value for xi in x.get_shape()]) for x in model.var_op])
    elif mode == 'trainable':
        num = np.sum([np.product([xi.value for xi in x.get_shape()]) for x in model.var_trainable_op])
    else:
        raise TypeError('mode should be all or trainable.')
    print('number of ' + mode + ' parameters: ' + str(num))
    return num

def batch_norm(x, is_training=True):
    """ Batch normalization.
    """
    with tf.variable_scope('BatchNorm'):
        inputs_shape = x.get_shape()
        axis = list(range(len(inputs_shape) - 1))
        param_shape = inputs_shape[-1:]
        beta = tf.get_variable('beta', param_shape, initializer=tf.constant_initializer(0.0))
        gamma = tf.get_variable('gamma', param_shape, initializer=tf.constant_initializer(1.0))
        batch_mean, batch_var = tf.nn.moments(x, axis)
        ema = tf.train.ExponentialMovingAverage(decay=0.5)

        def mean_var_with_update():
            ema_apply_op = ema.apply([batch_mean, batch_var])
            with tf.control_dependencies([ema_apply_op]):
                return (tf.identity(batch_mean), tf.identity(batch_var))
        mean, var = tf.cond(is_training, mean_var_with_update, lambda: (ema.average(batch_mean), ema.average(batch_var)))
        normed = tf.nn.batch_normalization(x, mean, var, beta, gamma, 0.001)
    return normed

def dropout(x, keep_prob, is_training):
    """ Apply dropout to a tensor
    """
    return tf.contrib.layers.dropout(x, keep_prob=keep_prob, is_training=is_training)

def build_multi_dynamic_brnn(args, maxTimeSteps, inputX, cell_fn, seqLengths, time_major=True):
    hid_input = inputX
    for i in range(args.num_layer):
        scope = 'DBRNN_' + str(i + 1)
        forward_cell = cell_fn(args.num_hidden, activation=args.activation)
        backward_cell = cell_fn(args.num_hidden, activation=args.activation)
        outputs, output_states = bidirectional_dynamic_rnn(forward_cell, backward_cell, inputs=hid_input, dtype=tf.float32, sequence_length=seqLengths, time_major=True, scope=scope)
        output_fw, output_bw = outputs
        output_state_fw, output_state_bw = output_states
        output_fb = tf.concat([output_fw, output_bw], 2)
        shape = output_fb.get_shape().as_list()
        output_fb = tf.reshape(output_fb, [shape[0], shape[1], 2, int(shape[2] / 2)])
        hidden = tf.reduce_sum(output_fb, 2)
        hidden = dropout(hidden, args.keep_prob, args.mode == 'train')
        if i != args.num_layer - 1:
            hid_input = hidden
        else:
            outputXrs = tf.reshape(hidden, [-1, args.num_hidden])
            output_list = tf.split(outputXrs, maxTimeSteps, 0)
            fbHrs = [tf.reshape(t, [args.batch_size, args.num_hidden]) for t in output_list]
    return fbHrs

def routing(u, next_num_channels, next_num_capsules, next_output_vector_len, num_iter, scope=None):
    """ Routing algorithm for capsules of two adjacent layers
    size of u: [batch_size, channels, num_capsules, output_vector_len]
    size of w: [batch_size, channels, num_capsules, next_channels, next_num_capsules, vec_len, next_vec_len]
    """
    scope = scope or 'routing'
    shape = u.get_shape()
    u = tf.reshape(u, [shape[0], shape[1], shape[2], 1, 1, shape[3], 1])
    u_ij = tf.tile(u, [1, 1, 1, next_num_channels, next_num_capsules, 1, 1])
    with tf.variable_scope(scope):
        w_shape = [1, shape[1], shape[2], next_num_channels, next_num_capsules, shape[3], next_output_vector_len]
        w = tf.get_variable('w', shape=w_shape, dtype=tf.float32)
        w = tf.tile(w, [shape[0], 1, 1, 1, 1, 1, 1])
        u_hat = tf.matmul(w, u_ij, transpose_a=True)
        u_hat = tf.reshape(u_hat, [shape[0], shape[1] * shape[2], -1, next_output_vector_len, 1])
        u_hat_without_backprop = tf.stop_gradient(u_hat, 'u_hat_without_backprop')
        b_ij = tf.constant(np.zeros([shape[0], shape[1] * shape[2], next_num_channels * next_num_capsules, 1, 1]), dtype=tf.float32)
        c_ij = tf.nn.softmax(b_ij, dim=2)
        for r in range(num_iter):
            if r != num_iter - 1:
                s_j = tf.reduce_sum(tf.multiply(c_ij, u_hat_without_backprop), axis=1, keep_dims=True)
                v_j = squashing(s_j)
                v_j = tf.tile(v_j, [1, shape[1] * shape[2], 1, 1, 1])
                b_ij = b_ij + tf.matmul(u_hat, v_j, transpose_a=True)
            else:
                s_j = tf.reduce_sum(tf.multiply(c_ij, u_hat), axis=1, keep_dims=True)
                v_j = squashing(s_j)
    return v_j

class CapsuleLayer(object):
    """ Capsule layer based on convolutional neural network
    """

    def __init__(self, num_capsules, num_channels, output_vector_len, layer_type='conv', vars_scope=None):
        self._num_capsules = num_capsules
        self._num_channels = num_channels
        self._output_vector_len = output_vector_len
        self._layer_type = layer_type
        self._vars_scope = vars_scope or 'capsule_layer'

    @property
    def num_capsules(self):
        return self._num_capsules

    @property
    def output_vector_len(self):
        return self._output_vector_len

    def __call__(self, inputX, kernel_size, strides, num_iter, with_routing=True, padding='VALID'):
        input_shape = inputX.get_shape()
        with tf.variable_scope(self._vars_scope) as scope:
            if self._layer_type == 'conv':
                kernel = tf.get_variable('conv_kernel', shape=[kernel_size[0], kernel_size[1], input_shape[-1], self._num_channels * self._num_capsules * self._output_vector_len], dtype=tf.float32)
                conv_output = tf.nn.conv2d(inputX, kernel, strides, padding)
                shape1 = conv_output.get_shape()
                capsule_output = tf.reshape(conv_output, [shape1[0], 1, -1, self._output_vector_len, 1])
                if with_routing:
                    capsule_output = routing(capsule_output, self._num_channels, self._num_capsules, self._output_vector_len, num_iter, scope)
                capsule_output = squashing(capsule_output)
                capsule_output = tf.reshape(capsule_output, [input_shape[0], self._num_capsules, self._output_vector_len, self._num_channels])
            elif self._layer_type == 'dnn':
                inputX = tf.reshape(inputX, [input_shape[0], 1, input_shape[1] * input_shape[3], input_shape[2], 1])
                capsule_output = routing(inputX, self._num_channels, self._num_capsules, self._output_vector_len, num_iter, scope)
                capsule_output = squashing(capsule_output)
                capsule_output = tf.squeeze(capsule_output, axis=[1, 4])
            else:
                capsule_output = None
        return capsule_output

def __call__(self, inputX, kernel_size, strides, num_iter, with_routing=True, padding='VALID'):
    input_shape = inputX.get_shape()
    with tf.variable_scope(self._vars_scope) as scope:
        if self._layer_type == 'conv':
            kernel = tf.get_variable('conv_kernel', shape=[kernel_size[0], kernel_size[1], input_shape[-1], self._num_channels * self._num_capsules * self._output_vector_len], dtype=tf.float32)
            conv_output = tf.nn.conv2d(inputX, kernel, strides, padding)
            shape1 = conv_output.get_shape()
            capsule_output = tf.reshape(conv_output, [shape1[0], 1, -1, self._output_vector_len, 1])
            if with_routing:
                capsule_output = routing(capsule_output, self._num_channels, self._num_capsules, self._output_vector_len, num_iter, scope)
            capsule_output = squashing(capsule_output)
            capsule_output = tf.reshape(capsule_output, [input_shape[0], self._num_capsules, self._output_vector_len, self._num_channels])
        elif self._layer_type == 'dnn':
            inputX = tf.reshape(inputX, [input_shape[0], 1, input_shape[1] * input_shape[3], input_shape[2], 1])
            capsule_output = routing(inputX, self._num_channels, self._num_capsules, self._output_vector_len, num_iter, scope)
            capsule_output = squashing(capsule_output)
            capsule_output = tf.squeeze(capsule_output, axis=[1, 4])
        else:
            capsule_output = None
    return capsule_output

def build_deepSpeech2(args, maxTimeSteps, inputX, cell_fn, seqLengths, time_major=True):
    """ Parameters:

          maxTimeSteps: maximum time steps of input spectrogram power
          inputX: spectrogram power of audios, [batch, freq_bin, time_len, in_channels]
          seqLengths: lengths of samples in a mini-batch
    """
    layer1_filter = tf.get_variable('layer1_filter', shape=(41, 11, 1, 32), dtype=tf.float32)
    layer1_stride = [1, 2, 2, 1]
    layer2_filter = tf.get_variable('layer2_filter', shape=(21, 11, 32, 32), dtype=tf.float32)
    layer2_stride = [1, 2, 1, 1]
    layer3_filter = tf.get_variable('layer3_filter', shape=(21, 11, 32, 96), dtype=tf.float32)
    layer3_stride = [1, 2, 1, 1]
    layer1 = tf.nn.conv2d(inputX, layer1_filter, layer1_stride, padding='SAME')
    layer1 = tf.layers.batch_normalization(layer1, training=args.is_training)
    layer1 = tf.contrib.layers.dropout(layer1, keep_prob=args.keep_prob[0], is_training=args.is_training)
    layer2 = tf.nn.conv2d(layer1, layer2_filter, layer2_stride, padding='SAME')
    layer2 = tf.layers.batch_normalization(layer2, training=args.isTraining)
    layer2 = tf.contrib.layers.dropout(layer2, keep_prob=args.keep_prob[1], is_training=args.is_training)
    layer3 = tf.nn.conv2d(layer2, layer3_filter, layer3_stride, padding='SAME')
    layer3 = tf.layers.batch_normalization(layer3, training=args.isTraining)
    layer3 = tf.contrib.layers.dropout(layer3, keep_prob=args.keep_prob[2], is_training=args.is_training)
    layer4_cell = cell_fn(args.num_hidden, activation=args.activation)
    layer4 = tf.nn.dynamic_rnn(layer4_cell, layer3, sequence_length=seqLengths, time_major=True)
    layer4 = tf.layers.batch_normalization(layer4, training=args.isTraining)
    layer4 = tf.contrib.layers.dropout(layer4, keep_prob=args.keep_prob[3], is_training=args.is_training)
    layer5_cell = cell_fn(args.num_hidden, activation=args.activation)
    layer5 = tf.nn.dynamic_rnn(layer5_cell, layer4, sequence_length=seqLengths, time_major=True)
    layer5 = tf.layers.batch_normalization(layer5, training=args.isTraining)
    layer5 = tf.contrib.layers.dropout(layer5, keep_prob=args.keep_prob[4], is_training=args.is_training)
    layer6_cell = cell_fn(args.num_hidden, activation=args.activation)
    layer6 = tf.nn.dynamic_rnn(layer6_cell, layer5, sequence_length=seqLengths, time_major=True)
    layer6 = tf.layers.batch_normalization(layer6, training=args.isTraining)
    layer6 = tf.contrib.layers.dropout(layer6, keep_prob=args.keep_prob[5], is_training=args.is_training)
    layer7_cell = cell_fn(args.num_hidden, activation=args.activation)
    layer7 = tf.nn.dynamic_rnn(layer7_cell, layer6, sequence_length=seqLengths, time_major=True)
    layer7 = tf.layers.batch_normalization(layer7, training=args.isTraining)
    layer7 = tf.contrib.layers.dropout(layer7, keep_prob=args.keep_prob[6], is_training=args.is_training)
    layer_fc = tf.layers.dense(layer7, args.num_hidden_fc)
    return layer_fc

