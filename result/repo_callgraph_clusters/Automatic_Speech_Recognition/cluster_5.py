# Cluster 5

def get_edit_distance(hyp_arr, truth_arr, normalize, level):
    """ calculate edit distance
    This is very universal, both for cha-level and phn-level
    """
    graph = tf.Graph()
    with graph.as_default():
        truth = tf.sparse_placeholder(tf.int32)
        hyp = tf.sparse_placeholder(tf.int32)
        editDist = tf.reduce_sum(tf.edit_distance(hyp, truth, normalize=normalize))
    with tf.Session(graph=graph) as session:
        truthTest = list_to_sparse_tensor(truth_arr, level)
        hypTest = list_to_sparse_tensor(hyp_arr, level)
        feedDict = {truth: truthTest, hyp: hypTest}
        dist = session.run(editDist, feed_dict=feedDict)
    return dist

def list_dirs(mfcc_dir, label_dir):
    mfcc_dirs = glob(mfcc_dir)
    label_dirs = glob(label_dir)
    for mfcc, label in zip(mfcc_dirs, label_dirs):
        yield (mfcc, label)

def get_edit_distance(hyp_arr, truth_arr, mode='train'):
    """ calculate edit distance
    """
    graph = tf.Graph()
    with graph.as_default():
        truth = tf.sparse_placeholder(tf.int32)
        hyp = tf.sparse_placeholder(tf.int32)
        editDist = tf.edit_distance(hyp, truth, normalize=True)
    with tf.Session(graph=graph) as session:
        truthTest = list_to_sparse_tensor(truth_arr, mode)
        hypTest = list_to_sparse_tensor(hyp_arr, mode)
        feedDict = {truth: truthTest, hyp: hypTest}
        dist = session.run(editDist, feed_dict=feedDict)
    return dist

def spectrum_power(frames, NFFT):
    """Calculate power spectrum for every frame after FFT.
    Args:
        frames: 2-D frames array calculated by audio2frame(...).
        NFFT:FFT size
    Returns:
        Power spectrum: PS = magnitude^2/NFFT
    """
    return 1.0 / NFFT * numpy.square(spectrum_magnitude(frames, NFFT))

class DBiRNN(object):

    def __init__(self, args, maxTimeSteps):
        self.args = args
        self.maxTimeSteps = maxTimeSteps
        if args.layerNormalization is True:
            if args.rnncell == 'rnn':
                self.cell_fn = lnBasicRNNCell
            elif args.rnncell == 'gru':
                self.cell_fn = lnGRUCell
            elif args.rnncell == 'lstm':
                self.cell_fn = lnBasicLSTMCell
            else:
                raise Exception('rnncell type not supported: {}'.format(args.rnncell))
        elif args.rnncell == 'rnn':
            self.cell_fn = tf.contrib.rnn.BasicRNNCell
        elif args.rnncell == 'gru':
            self.cell_fn = tf.contrib.rnn.GRUCell
        elif args.rnncell == 'lstm':
            self.cell_fn = tf.contrib.rnn.BasicLSTMCell
        else:
            raise Exception('rnncell type not supported: {}'.format(args.rnncell))
        self.build_graph(args, maxTimeSteps)

    @describe
    def build_graph(self, args, maxTimeSteps):
        self.graph = tf.Graph()
        with self.graph.as_default():
            self.inputX = tf.placeholder(tf.float32, shape=(maxTimeSteps, args.batch_size, args.num_feature))
            inputXrs = tf.reshape(self.inputX, [-1, args.num_feature])
            self.inputList = tf.split(inputXrs, maxTimeSteps, 0)
            self.targetIxs = tf.placeholder(tf.int64)
            self.targetVals = tf.placeholder(tf.int32)
            self.targetShape = tf.placeholder(tf.int64)
            self.targetY = tf.SparseTensor(self.targetIxs, self.targetVals, self.targetShape)
            self.seqLengths = tf.placeholder(tf.int32, shape=args.batch_size)
            self.config = {'name': args.model, 'rnncell': self.cell_fn, 'num_layer': args.num_layer, 'num_hidden': args.num_hidden, 'num_class': args.num_class, 'activation': args.activation, 'optimizer': args.optimizer, 'learning rate': args.learning_rate, 'keep prob': args.keep_prob, 'batch size': args.batch_size}
            fbHrs = build_multi_dynamic_brnn(self.args, maxTimeSteps, self.inputX, self.cell_fn, self.seqLengths)
            with tf.name_scope('fc-layer'):
                with tf.variable_scope('fc'):
                    weightsClasses = tf.Variable(tf.truncated_normal([args.num_hidden, args.num_class], name='weightsClasses'))
                    biasesClasses = tf.Variable(tf.zeros([args.num_class]), name='biasesClasses')
                    logits = [tf.matmul(t, weightsClasses) + biasesClasses for t in fbHrs]
            logits3d = tf.stack(logits)
            self.loss = tf.reduce_mean(tf.nn.ctc_loss(self.targetY, logits3d, self.seqLengths))
            self.var_op = tf.global_variables()
            self.var_trainable_op = tf.trainable_variables()
            if args.grad_clip == -1:
                self.optimizer = tf.train.AdamOptimizer(args.learning_rate).minimize(self.loss)
            else:
                grads, _ = tf.clip_by_global_norm(tf.gradients(self.loss, self.var_trainable_op), args.grad_clip)
                opti = tf.train.AdamOptimizer(args.learning_rate)
                self.optimizer = opti.apply_gradients(zip(grads, self.var_trainable_op))
            self.predictions = tf.to_int32(tf.nn.ctc_beam_search_decoder(logits3d, self.seqLengths, merge_repeated=False)[0][0])
            if args.level == 'cha':
                self.errorRate = tf.reduce_sum(tf.edit_distance(self.predictions, self.targetY, normalize=True))
            self.initial_op = tf.global_variables_initializer()
            self.saver = tf.train.Saver(tf.global_variables(), max_to_keep=5, keep_checkpoint_every_n_hours=1)

@describe
def build_graph(self, args, maxTimeSteps):
    self.graph = tf.Graph()
    with self.graph.as_default():
        self.inputX = tf.placeholder(tf.float32, shape=(maxTimeSteps, args.batch_size, args.num_feature))
        inputXrs = tf.reshape(self.inputX, [-1, args.num_feature])
        self.inputList = tf.split(inputXrs, maxTimeSteps, 0)
        self.targetIxs = tf.placeholder(tf.int64)
        self.targetVals = tf.placeholder(tf.int32)
        self.targetShape = tf.placeholder(tf.int64)
        self.targetY = tf.SparseTensor(self.targetIxs, self.targetVals, self.targetShape)
        self.seqLengths = tf.placeholder(tf.int32, shape=args.batch_size)
        self.config = {'name': args.model, 'rnncell': self.cell_fn, 'num_layer': args.num_layer, 'num_hidden': args.num_hidden, 'num_class': args.num_class, 'activation': args.activation, 'optimizer': args.optimizer, 'learning rate': args.learning_rate, 'keep prob': args.keep_prob, 'batch size': args.batch_size}
        fbHrs = build_multi_dynamic_brnn(self.args, maxTimeSteps, self.inputX, self.cell_fn, self.seqLengths)
        with tf.name_scope('fc-layer'):
            with tf.variable_scope('fc'):
                weightsClasses = tf.Variable(tf.truncated_normal([args.num_hidden, args.num_class], name='weightsClasses'))
                biasesClasses = tf.Variable(tf.zeros([args.num_class]), name='biasesClasses')
                logits = [tf.matmul(t, weightsClasses) + biasesClasses for t in fbHrs]
        logits3d = tf.stack(logits)
        self.loss = tf.reduce_mean(tf.nn.ctc_loss(self.targetY, logits3d, self.seqLengths))
        self.var_op = tf.global_variables()
        self.var_trainable_op = tf.trainable_variables()
        if args.grad_clip == -1:
            self.optimizer = tf.train.AdamOptimizer(args.learning_rate).minimize(self.loss)
        else:
            grads, _ = tf.clip_by_global_norm(tf.gradients(self.loss, self.var_trainable_op), args.grad_clip)
            opti = tf.train.AdamOptimizer(args.learning_rate)
            self.optimizer = opti.apply_gradients(zip(grads, self.var_trainable_op))
        self.predictions = tf.to_int32(tf.nn.ctc_beam_search_decoder(logits3d, self.seqLengths, merge_repeated=False)[0][0])
        if args.level == 'cha':
            self.errorRate = tf.reduce_sum(tf.edit_distance(self.predictions, self.targetY, normalize=True))
        self.initial_op = tf.global_variables_initializer()
        self.saver = tf.train.Saver(tf.global_variables(), max_to_keep=5, keep_checkpoint_every_n_hours=1)

def squashing(s):
    """ Squashing function for normalization
    size of s: [batch_size, 1, next_channels*next_num_capsules, next_output_vector_len, 1]
    size of v: [batch_size, 1, next_channels*next_num_capsules, next_output_vector_len, 1]
    """
    assert s.dtype == tf.float32
    squared_s = tf.reduce_sum(tf.square(s), axis=2, keep_dims=True)
    normed_s = tf.norm(s, axis=2, keep_dims=True)
    v = squared_s / (1 + squared_s) / normed_s * s
    assert v.get_shape() == s.get_shape()
    return v

class CapsuleNetwork(object):

    def __init__(self, args, maxTimeSteps):
        self.args = args
        self.maxTimeSteps = maxTimeSteps
        self.build_graph(self.args, self.maxTimeSteps)

    def build_graph(self, args, maxTimeSteps):
        self.maxTimeSteps = maxTimeSteps
        self.inputX = tf.placeholder(tf.float32, shape=[maxTimeSteps, args.batch_size, args.num_feature])
        self.targetIxs = tf.placeholder(tf.int64)
        self.targetVals = tf.placeholder(tf.int32)
        self.targetShape = tf.placeholder(tf.int64)
        self.targetY = tf.SparseTensor(self.targetIxs, self.targetVals, self.targetShape)
        self.seqLengths = tf.placeholder(tf.int32, shape=args.batch_size)
        self.config = {'name': args.model, 'num_layer': args.num_layer, 'num_hidden': args.num_hidden, 'num_class': args.num_class, 'activation': args.activation, 'optimizer': args.optimizer, 'learning rate': args.learning_rate, 'keep prob': args.keep_prob, 'batch size': args.batch_size}
        inputX = tf.reshape(self.inputX, [args.batch_size, maxTimeSteps, args.num_feature, 1])
        print(inputX.get_shape())
        with tf.variable_scope('layer_conv1'):
            kernel = tf.get_variable('kernel', shape=[3, 3, 1, 16], dtype=tf.float32)
            conv1 = tf.nn.conv2d(inputX, kernel, (1, 1, 1, 1), padding='VALID')
        print(conv1.get_shape())
        output = conv1
        for layer_id in range(args.num_layer):
            vars_scope = 'capsule_cnn_layer_' + str(layer_id + 1)
            capLayer = CapsuleLayer(4, 8, 2, layer_type='conv', vars_scope=vars_scope)
            output = capLayer(output, [2, 2], (1, 1, 1, 1), args.num_iter)
            print(output.get_shape())
        vars_scope = 'capsule_dnn_layer'
        capLayer = CapsuleLayer(8, 16, args.num_classes, layer_type='dnn', vars_scope=vars_scope)
        logits3d = capLayer(output, [3, 3], (1, 1, 1, 1), args.num_iter)
        logits3d = tf.transpose(logits3d, perm=[1, 0, 2])
        self.loss = tf.reduce_mean(tf.nn.ctc_loss(self.targetY, logits3d, self.seqLengths))
        self.var_op = tf.global_variables()
        self.var_trainable_op = tf.trainable_variables()
        if args.grad_clip == -1:
            self.optimizer = tf.train.AdamOptimizer(args.learning_rate).minimize(self.loss)
        else:
            grads, _ = tf.clip_by_global_norm(tf.gradients(self.loss, self.var_trainable_op), args.grad_clip)
            opti = tf.train.AdamOptimizer(args.learning_rate)
            self.optimizer = opti.apply_gradients(zip(grads, self.var_trainable_op))
        self.predictions = tf.to_int32(tf.nn.ctc_beam_search_decoder(logits3d, self.seqLengths, merge_repeated=False)[0][0])
        if args.level == 'cha':
            self.errorRate = tf.reduce_sum(tf.edit_distance(self.predictions, self.targetY, normalize=True))
        self.initial_op = tf.global_variables_initializer()
        self.saver = tf.train.Saver(tf.global_variables(), max_to_keep=5, keep_checkpoint_every_n_hours=1)

def build_graph(self, args, maxTimeSteps):
    self.maxTimeSteps = maxTimeSteps
    self.inputX = tf.placeholder(tf.float32, shape=[maxTimeSteps, args.batch_size, args.num_feature])
    self.targetIxs = tf.placeholder(tf.int64)
    self.targetVals = tf.placeholder(tf.int32)
    self.targetShape = tf.placeholder(tf.int64)
    self.targetY = tf.SparseTensor(self.targetIxs, self.targetVals, self.targetShape)
    self.seqLengths = tf.placeholder(tf.int32, shape=args.batch_size)
    self.config = {'name': args.model, 'num_layer': args.num_layer, 'num_hidden': args.num_hidden, 'num_class': args.num_class, 'activation': args.activation, 'optimizer': args.optimizer, 'learning rate': args.learning_rate, 'keep prob': args.keep_prob, 'batch size': args.batch_size}
    inputX = tf.reshape(self.inputX, [args.batch_size, maxTimeSteps, args.num_feature, 1])
    print(inputX.get_shape())
    with tf.variable_scope('layer_conv1'):
        kernel = tf.get_variable('kernel', shape=[3, 3, 1, 16], dtype=tf.float32)
        conv1 = tf.nn.conv2d(inputX, kernel, (1, 1, 1, 1), padding='VALID')
    print(conv1.get_shape())
    output = conv1
    for layer_id in range(args.num_layer):
        vars_scope = 'capsule_cnn_layer_' + str(layer_id + 1)
        capLayer = CapsuleLayer(4, 8, 2, layer_type='conv', vars_scope=vars_scope)
        output = capLayer(output, [2, 2], (1, 1, 1, 1), args.num_iter)
        print(output.get_shape())
    vars_scope = 'capsule_dnn_layer'
    capLayer = CapsuleLayer(8, 16, args.num_classes, layer_type='dnn', vars_scope=vars_scope)
    logits3d = capLayer(output, [3, 3], (1, 1, 1, 1), args.num_iter)
    logits3d = tf.transpose(logits3d, perm=[1, 0, 2])
    self.loss = tf.reduce_mean(tf.nn.ctc_loss(self.targetY, logits3d, self.seqLengths))
    self.var_op = tf.global_variables()
    self.var_trainable_op = tf.trainable_variables()
    if args.grad_clip == -1:
        self.optimizer = tf.train.AdamOptimizer(args.learning_rate).minimize(self.loss)
    else:
        grads, _ = tf.clip_by_global_norm(tf.gradients(self.loss, self.var_trainable_op), args.grad_clip)
        opti = tf.train.AdamOptimizer(args.learning_rate)
        self.optimizer = opti.apply_gradients(zip(grads, self.var_trainable_op))
    self.predictions = tf.to_int32(tf.nn.ctc_beam_search_decoder(logits3d, self.seqLengths, merge_repeated=False)[0][0])
    if args.level == 'cha':
        self.errorRate = tf.reduce_sum(tf.edit_distance(self.predictions, self.targetY, normalize=True))
    self.initial_op = tf.global_variables_initializer()
    self.saver = tf.train.Saver(tf.global_variables(), max_to_keep=5, keep_checkpoint_every_n_hours=1)

class DeepSpeech2(object):

    def __init__(self, args, maxTimeSteps):
        self.args = args
        self.maxTimeSteps = maxTimeSteps
        if args.layerNormalization is True:
            if args.rnncell == 'rnn':
                self.cell_fn = lnBasicRNNCell
            elif args.rnncell == 'gru':
                self.cell_fn = lnGRUCell
            elif args.rnncell == 'lstm':
                self.cell_fn = lnBasicLSTMCell
            else:
                raise Exception('rnncell type not supported: {}'.format(args.rnncell))
        elif args.rnncell == 'rnn':
            self.cell_fn = tf.contrib.rnn.BasicRNNCell
        elif args.rnncell == 'gru':
            self.cell_fn = tf.contrib.rnn.GRUCell
        elif args.rnncell == 'lstm':
            self.cell_fn = tf.contrib.rnn.BasicLSTMCell
        else:
            raise Exception('rnncell type not supported: {}'.format(args.rnncell))
        self.build_graph(args, maxTimeSteps)

    @describe
    def build_graph(self, args, maxTimeSteps):
        self.graph = tf.Graph()
        with self.graph.as_default():
            self.inputX = tf.placeholder(tf.float32, shape=(maxTimeSteps, args.batch_size, args.num_feature))
            inputXrs = tf.reshape(self.inputX, [args.batch_size, args.num_feature, maxTimeSteps, 1])
            self.targetIxs = tf.placeholder(tf.int64)
            self.targetVals = tf.placeholder(tf.int32)
            self.targetShape = tf.placeholder(tf.int64)
            self.targetY = tf.SparseTensor(self.targetIxs, self.targetVals, self.targetShape)
            self.seqLengths = tf.placeholder(tf.int32, shape=args.batch_size)
            self.config = {'name': args.model, 'rnncell': self.cell_fn, 'num_layer': args.num_layer, 'num_hidden': args.num_hidden, 'num_class': args.num_class, 'activation': args.activation, 'optimizer': args.optimizer, 'learning rate': args.learning_rate, 'keep prob': args.keep_prob, 'batch size': args.batch_size}
            output_fc = build_deepSpeech2(self.args, maxTimeSteps, self.inputX, self.cell_fn, self.seqLengths)
            self.loss = tf.reduce_mean(tf.nn.ctc_loss(self.targetY, output_fc, self.seqLengths))
            self.var_op = tf.global_variables()
            self.var_trainable_op = tf.trainable_variables()
            if args.grad_clip == -1:
                self.optimizer = tf.train.AdamOptimizer(args.learning_rate).minimize(self.loss)
            else:
                grads, _ = tf.clip_by_global_norm(tf.gradients(self.loss, self.var_trainable_op), args.grad_clip)
                opti = tf.train.AdamOptimizer(args.learning_rate)
                self.optimizer = opti.apply_gradients(zip(grads, self.var_trainable_op))
            self.predictions = tf.to_int32(tf.nn.ctc_beam_search_decoder(output_fc, self.seqLengths, merge_repeated=False)[0][0])
            if args.level == 'cha':
                self.errorRate = tf.reduce_sum(tf.edit_distance(self.predictions, self.targetY, normalize=True))
            self.initial_op = tf.global_variables_initializer()
            self.saver = tf.train.Saver(tf.global_variables(), max_to_keep=5, keep_checkpoint_every_n_hours=1)

@describe
def build_graph(self, args, maxTimeSteps):
    self.graph = tf.Graph()
    with self.graph.as_default():
        self.inputX = tf.placeholder(tf.float32, shape=(maxTimeSteps, args.batch_size, args.num_feature))
        inputXrs = tf.reshape(self.inputX, [args.batch_size, args.num_feature, maxTimeSteps, 1])
        self.targetIxs = tf.placeholder(tf.int64)
        self.targetVals = tf.placeholder(tf.int32)
        self.targetShape = tf.placeholder(tf.int64)
        self.targetY = tf.SparseTensor(self.targetIxs, self.targetVals, self.targetShape)
        self.seqLengths = tf.placeholder(tf.int32, shape=args.batch_size)
        self.config = {'name': args.model, 'rnncell': self.cell_fn, 'num_layer': args.num_layer, 'num_hidden': args.num_hidden, 'num_class': args.num_class, 'activation': args.activation, 'optimizer': args.optimizer, 'learning rate': args.learning_rate, 'keep prob': args.keep_prob, 'batch size': args.batch_size}
        output_fc = build_deepSpeech2(self.args, maxTimeSteps, self.inputX, self.cell_fn, self.seqLengths)
        self.loss = tf.reduce_mean(tf.nn.ctc_loss(self.targetY, output_fc, self.seqLengths))
        self.var_op = tf.global_variables()
        self.var_trainable_op = tf.trainable_variables()
        if args.grad_clip == -1:
            self.optimizer = tf.train.AdamOptimizer(args.learning_rate).minimize(self.loss)
        else:
            grads, _ = tf.clip_by_global_norm(tf.gradients(self.loss, self.var_trainable_op), args.grad_clip)
            opti = tf.train.AdamOptimizer(args.learning_rate)
            self.optimizer = opti.apply_gradients(zip(grads, self.var_trainable_op))
        self.predictions = tf.to_int32(tf.nn.ctc_beam_search_decoder(output_fc, self.seqLengths, merge_repeated=False)[0][0])
        if args.level == 'cha':
            self.errorRate = tf.reduce_sum(tf.edit_distance(self.predictions, self.targetY, normalize=True))
        self.initial_op = tf.global_variables_initializer()
        self.saver = tf.train.Saver(tf.global_variables(), max_to_keep=5, keep_checkpoint_every_n_hours=1)

