# Cluster 10

def build_model(_indices, _values, _values2, _shape, _y, _ind, keep_probs, feature_cnt, field_cnt, params):
    eta = tf.constant(params['eta'])
    _x = tf.SparseTensor(_indices, _values, _shape)
    _xx = tf.SparseTensor(_indices, _values2, _shape)
    model_params = []
    tmp = []
    init_value = params['init_value']
    dim = params['dim']
    layer_sizes = params['layer_sizes']
    w_linear = tf.Variable(tf.truncated_normal([feature_cnt, 1], stddev=init_value, mean=0), name='w_linear', dtype=tf.float32)
    bias = tf.Variable(tf.truncated_normal([1], stddev=init_value, mean=0), name='bias')
    model_params.append(bias)
    model_params.append(w_linear)
    preds = bias
    preds += tf.sparse_tensor_dense_matmul(_x, w_linear, name='contr_from_linear')
    w_fm = tf.Variable(tf.truncated_normal([feature_cnt, dim], stddev=init_value / math.sqrt(float(dim)), mean=0), name='w_fm', dtype=tf.float32)
    model_params.append(w_fm)
    if params['is_use_fm_part']:
        preds = preds + 0.5 * tf.reduce_sum(tf.pow(tf.sparse_tensor_dense_matmul(_x, w_fm), 2) - tf.sparse_tensor_dense_matmul(_xx, tf.pow(w_fm, 2)), 1, keep_dims=True)
    if params['is_use_dnn_part']:
        w_fm_nn_input = tf.reshape(tf.gather(w_fm, _ind) * tf.expand_dims(_values, 1), [-1, field_cnt * dim])
        print(w_fm_nn_input.shape)
        hidden_nn_layers = []
        hidden_nn_layers.append(w_fm_nn_input)
        last_layer_size = field_cnt * dim
        layer_idx = 0
        w_nn_params = []
        b_nn_params = []
        for layer_size in layer_sizes:
            cur_w_nn_layer = tf.Variable(tf.truncated_normal([last_layer_size, layer_size], stddev=init_value / math.sqrt(float(10)), mean=0), name='w_nn_layer' + str(layer_idx), dtype=tf.float32)
            cur_b_nn_layer = tf.Variable(tf.truncated_normal([layer_size], stddev=init_value, mean=0), name='b_nn_layer' + str(layer_idx))
            cur_hidden_nn_layer = tf.nn.xw_plus_b(hidden_nn_layers[layer_idx], cur_w_nn_layer, cur_b_nn_layer)
            cur_hidden_nn_layer = tf.nn.dropout(cur_hidden_nn_layer, keep_probs[layer_idx])
            if params['activations'][layer_idx] == 'tanh':
                cur_hidden_nn_layer = tf.nn.tanh(cur_hidden_nn_layer)
            elif params['activations'][layer_idx] == 'sigmoid':
                cur_hidden_nn_layer = tf.nn.sigmoid(cur_hidden_nn_layer)
            elif params['activations'][layer_idx] == 'relu':
                cur_hidden_nn_layer = tf.nn.relu(cur_hidden_nn_layer)
            hidden_nn_layers.append(cur_hidden_nn_layer)
            layer_idx += 1
            last_layer_size = layer_size
            model_params.append(cur_w_nn_layer)
            model_params.append(cur_b_nn_layer)
            w_nn_params.append(cur_w_nn_layer)
            b_nn_params.append(cur_b_nn_layer)
        w_nn_output = tf.Variable(tf.truncated_normal([last_layer_size, 1], stddev=init_value, mean=0), name='w_nn_output', dtype=tf.float32)
        nn_output = tf.matmul(hidden_nn_layers[-1], w_nn_output)
        model_params.append(w_nn_output)
        w_nn_params.append(w_nn_output)
        preds += nn_output
    if params['loss'] == 'cross_entropy_loss':
        error = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits=tf.reshape(preds, [-1]), labels=tf.reshape(_y, [-1])))
    elif params['loss'] == 'square_loss':
        preds = tf.sigmoid(preds)
        error = tf.reduce_mean(tf.squared_difference(preds, _y))
    elif params['loss'] == 'log_loss':
        preds = tf.sigmoid(preds)
        error = tf.reduce_mean(tf.losses.log_loss(predictions=preds, labels=_y))
    lambda_w_linear = tf.constant(params['reg_w_linear'], name='lambda_w_linear')
    lambda_w_fm = tf.constant(params['reg_w_fm'], name='lambda_w_fm')
    lambda_w_nn = tf.constant(params['reg_w_nn'], name='lambda_nn_fm')
    lambda_w_l1 = tf.constant(params['reg_w_l1'], name='lambda_w_l1')
    l2_norm = tf.multiply(lambda_w_linear, tf.reduce_sum(tf.pow(w_linear, 2)))
    l2_norm += tf.multiply(lambda_w_l1, tf.reduce_sum(tf.abs(w_linear)))
    if params['is_use_fm_part'] or params['is_use_dnn_part']:
        l2_norm += tf.multiply(lambda_w_fm, tf.reduce_sum(tf.pow(w_fm, 2)))
    if params['is_use_dnn_part']:
        for i in range(len(w_nn_params)):
            l2_norm += tf.multiply(lambda_w_nn, tf.reduce_sum(tf.pow(w_nn_params[i], 2)))
        for i in range(len(b_nn_params)):
            l2_norm += tf.multiply(lambda_w_nn, tf.reduce_sum(tf.pow(b_nn_params[i], 2)))
    loss = tf.add(error, l2_norm)
    if params['optimizer'] == 'adadelta':
        train_step = tf.train.AdadeltaOptimizer(eta).minimize(loss, var_list=model_params)
    elif params['optimizer'] == 'sgd':
        train_step = tf.train.GradientDescentOptimizer(params['learning_rate']).minimize(loss, var_list=model_params)
    elif params['optimizer'] == 'adam':
        train_step = tf.train.AdamOptimizer(params['learning_rate']).minimize(loss, var_list=model_params)
    elif params['optimizer'] == 'ftrl':
        train_step = tf.train.FtrlOptimizer(params['learning_rate']).minimize(loss, var_list=model_params)
    else:
        train_step = tf.train.GradientDescentOptimizer(params['learning_rate']).minimize(loss, var_list=model_params)
    tf.summary.scalar('square_error', error)
    tf.summary.scalar('loss', loss)
    tf.summary.histogram('linear_weights_hist', w_linear)
    if params['is_use_fm_part']:
        tf.summary.histogram('fm_weights_hist', w_fm)
    if params['is_use_dnn_part']:
        for idx in range(len(w_nn_params)):
            tf.summary.histogram('nn_layer' + str(idx) + '_weights', w_nn_params[idx])
    merged_summary = tf.summary.merge_all()
    return (train_step, loss, error, preds, merged_summary, tmp)

def build_model(_indices, _values, _values2, _shape, _field2feature_indices, _field2feature_values, _field2feature_weights, _field2feature_shape, _y, params):
    eta = tf.constant(params['eta'])
    _x = tf.SparseTensor(_indices, _values, _shape)
    _xx = tf.SparseTensor(_indices, _values2, _shape)
    model_params = []
    tmp = []
    init_value = params['init_value']
    dim = params['dim']
    layer_sizes = params['layer_sizes']
    w_linear = tf.Variable(tf.truncated_normal([FEATURE_COUNT, 1], stddev=init_value, mean=0), name='w_linear', dtype=tf.float32)
    bias = tf.Variable(tf.truncated_normal([1], stddev=init_value, mean=0), name='bias')
    model_params.append(bias)
    model_params.append(w_linear)
    preds = bias
    preds += tf.sparse_tensor_dense_matmul(_x, w_linear, name='contr_from_linear')
    w_fm = tf.Variable(tf.truncated_normal([FEATURE_COUNT, dim], stddev=init_value / math.sqrt(float(dim)), mean=0), name='w_fm', dtype=tf.float32)
    model_params.append(w_fm)
    if params['is_use_fm_part']:
        preds = preds + 0.5 * tf.reduce_sum(tf.pow(tf.sparse_tensor_dense_matmul(_x, w_fm), 2) - tf.sparse_tensor_dense_matmul(_xx, tf.pow(w_fm, 2)), 1, keep_dims=True)
    w_nn_params = []
    b_nn_params = []
    if params['is_use_dnn_part']:
        w_fm_sparseIndexs = tf.SparseTensor(_field2feature_indices, _field2feature_values, _field2feature_shape)
        w_fm_sparseWeights = tf.SparseTensor(_field2feature_indices, _field2feature_weights, _field2feature_shape)
        w_fm_nn_input_orgin = tf.nn.embedding_lookup_sparse(w_fm, w_fm_sparseIndexs, w_fm_sparseWeights, combiner='sum')
        w_fm_nn_input = tf.reshape(w_fm_nn_input_orgin, [-1, dim * FIELD_COUNT])
        hidden_nn_layers = []
        hidden_nn_layers.append(w_fm_nn_input)
        last_layer_size = FIELD_COUNT * dim
        layer_idx = 0
        for layer_size in layer_sizes:
            cur_w_nn_layer = tf.Variable(tf.truncated_normal([last_layer_size, layer_size], stddev=init_value / math.sqrt(float(10)), mean=0), name='w_nn_layer' + str(layer_idx), dtype=tf.float32)
            cur_b_nn_layer = tf.Variable(tf.truncated_normal([layer_size], stddev=init_value, mean=0), name='b_nn_layer' + str(layer_idx))
            cur_hidden_nn_layer = tf.nn.xw_plus_b(hidden_nn_layers[layer_idx], cur_w_nn_layer, cur_b_nn_layer)
            if params['activations'][layer_idx] == 'tanh':
                cur_hidden_nn_layer = tf.nn.tanh(cur_hidden_nn_layer)
            elif params['activations'][layer_idx] == 'sigmoid':
                cur_hidden_nn_layer = tf.nn.sigmoid(cur_hidden_nn_layer)
            elif params['activations'][layer_idx] == 'relu':
                cur_hidden_nn_layer = tf.nn.relu(cur_hidden_nn_layer)
            hidden_nn_layers.append(cur_hidden_nn_layer)
            layer_idx += 1
            last_layer_size = layer_size
            model_params.append(cur_w_nn_layer)
            model_params.append(cur_b_nn_layer)
            w_nn_params.append(cur_w_nn_layer)
            b_nn_params.append(cur_b_nn_layer)
        w_nn_output = tf.Variable(tf.truncated_normal([last_layer_size, 1], stddev=init_value, mean=0), name='w_nn_output', dtype=tf.float32)
        nn_output = tf.matmul(hidden_nn_layers[-1], w_nn_output)
        model_params.append(w_nn_output)
        w_nn_params.append(w_nn_output)
        preds += nn_output
    if params['loss'] == 'cross_entropy_loss':
        error = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits=tf.reshape(preds, [-1]), labels=tf.reshape(_y, [-1])))
    elif params['loss'] == 'square_loss':
        preds = tf.sigmoid(preds)
        error = tf.reduce_mean(tf.squared_difference(preds, _y))
    elif params['loss'] == 'log_loss':
        preds = tf.sigmoid(preds)
        error = tf.reduce_mean(tf.losses.log_loss(predictions=preds, labels=_y))
    lambda_w_linear = tf.constant(params['reg_w_linear'], name='lambda_w_linear')
    lambda_w_fm = tf.constant(params['reg_w_fm'], name='lambda_w_fm')
    lambda_w_nn = tf.constant(params['reg_w_nn'], name='lambda_nn_fm')
    lambda_w_l1 = tf.constant(params['reg_w_l1'], name='lambda_w_l1')
    l2_norm = tf.multiply(lambda_w_linear, tf.reduce_sum(tf.pow(w_linear, 2)))
    l2_norm += tf.multiply(lambda_w_l1, tf.reduce_sum(tf.abs(w_linear)))
    if params['is_use_fm_part'] or params['is_use_dnn_part'] or params['is_multi_level']:
        l2_norm += lambda_w_fm * tf.nn.l2_loss(w_fm)
    if params['is_use_dnn_part'] or params['is_multi_level']:
        for i in range(len(w_nn_params)):
            l2_norm += lambda_w_nn * tf.nn.l2_loss(w_nn_params[i])
        for i in range(len(b_nn_params)):
            l2_norm += lambda_w_nn * tf.nn.l2_loss(b_nn_params[i])
    loss = tf.add(error, l2_norm)
    if params['optimizer'] == 'adadelta':
        train_step = tf.train.AdadeltaOptimizer(eta).minimize(loss, var_list=model_params)
    elif params['optimizer'] == 'sgd':
        train_step = tf.train.GradientDescentOptimizer(params['learning_rate']).minimize(loss, var_list=model_params)
    elif params['optimizer'] == 'adam':
        train_step = tf.train.AdamOptimizer(params['learning_rate']).minimize(loss, var_list=model_params)
    elif params['optimizer'] == 'ftrl':
        train_step = tf.train.FtrlOptimizer(params['learning_rate']).minimize(loss, var_list=model_params)
    else:
        train_step = tf.train.GradientDescentOptimizer(params['learning_rate']).minimize(loss, var_list=model_params)
    return (train_step, loss, error, preds, tmp)

def build_model(user_indices, item_indices, rank, ratings, user_cnt, item_cnt, lr, lamb, mu, init_value):
    W_user = tf.Variable(tf.truncated_normal([user_cnt, rank], stddev=init_value / math.sqrt(float(rank)), mean=0), name='user_embedding', dtype=tf.float32)
    W_item = tf.Variable(tf.truncated_normal([item_cnt, rank], stddev=init_value / math.sqrt(float(rank)), mean=0), name='item_embedding', dtype=tf.float32)
    W_user_bias = tf.concat([W_user, tf.ones((user_cnt, 1), dtype=tf.float32)], 1, name='user_embedding_bias')
    W_item_bias = tf.concat([tf.ones((item_cnt, 1), dtype=tf.float32), W_item], 1, name='item_embedding_bias')
    user_feature = tf.nn.embedding_lookup(W_user_bias, user_indices, name='user_feature')
    item_feature = tf.nn.embedding_lookup(W_item_bias, item_indices, name='item_feature')
    preds = tf.add(tf.reduce_sum(tf.multiply(user_feature, item_feature), 1), mu)
    square_error = tf.sqrt(tf.reduce_mean(tf.squared_difference(preds, ratings)))
    loss = square_error + lamb * (tf.reduce_mean(tf.nn.l2_loss(W_user)) + tf.reduce_mean(tf.nn.l2_loss(W_item)))
    tf.summary.scalar('square_error', square_error)
    tf.summary.scalar('loss', loss)
    merged_summary = tf.summary.merge_all()
    train_step = tf.train.GradientDescentOptimizer(lr).minimize(loss)
    return (train_step, square_error, loss, merged_summary)

def single_run(dataset, params):
    cf_dim, user_attr_rank, item_attr_rank, layer_sizes, lr, lamb, mu, n_eopch, batch_size, init_value = (params['cf_dim'], params['user_attr_rank'], params['item_attr_rank'], params['layer_sizes'], params['lr'], params['lamb'], params['mu'], params['n_eopch'], params['batch_size'], params['init_value'])
    user_cnt, user_attr_cnt = (dataset.n_user, dataset.n_user_attr)
    item_cnt, item_attr_cnt = (dataset.n_item, dataset.n_item_attr)
    W_user = tf.Variable(tf.truncated_normal([user_cnt, cf_dim], stddev=init_value / math.sqrt(float(cf_dim)), mean=0), name='user_cf_embedding', dtype=tf.float32)
    W_item = tf.Variable(tf.truncated_normal([item_cnt, cf_dim], stddev=init_value / math.sqrt(float(cf_dim)), mean=0), name='item_cf_embedding', dtype=tf.float32)
    W_user_bias = tf.concat([W_user, tf.ones((user_cnt, 1), dtype=tf.float32)], 1, name='user_cf_embedding_bias')
    W_item_bias = tf.concat([tf.ones((item_cnt, 1), dtype=tf.float32), W_item], 1, name='item_cf_embedding_bias')
    user_attr_indices, user_attr_indices_values, user_attr_indices_weights = compose_vector_for_sparse_tensor(dataset.user_attr)
    item_attr_indices, item_attr_indices_values, item_attr_indices_weights = compose_vector_for_sparse_tensor(dataset.item_attr)
    user_sp_ids = tf.SparseTensor(indices=user_attr_indices, values=user_attr_indices_values, dense_shape=[user_cnt, user_attr_cnt])
    user_sp_weights = tf.SparseTensor(indices=user_attr_indices, values=user_attr_indices_weights, dense_shape=[user_cnt, user_attr_cnt])
    item_sp_ids = tf.SparseTensor(indices=item_attr_indices, values=item_attr_indices_values, dense_shape=[item_cnt, item_attr_cnt])
    item_sp_weights = tf.SparseTensor(indices=item_attr_indices, values=item_attr_indices_weights, dense_shape=[item_cnt, item_attr_cnt])
    W_user_attr = tf.Variable(tf.truncated_normal([user_attr_cnt, user_attr_rank], stddev=init_value / math.sqrt(float(user_attr_rank)), mean=0), name='user_attr_embedding', dtype=tf.float32)
    W_item_attr = tf.Variable(tf.truncated_normal([item_attr_cnt, item_attr_rank], stddev=init_value / math.sqrt(float(item_attr_rank)), mean=0), name='item_attr_embedding', dtype=tf.float32)
    user_embeddings = tf.nn.embedding_lookup_sparse(W_user_attr, user_sp_ids, user_sp_weights, name='user_embeddings', combiner='sum')
    item_embeddings = tf.nn.embedding_lookup_sparse(W_item_attr, item_sp_ids, item_sp_weights, name='item_embeddings', combiner='sum')
    user_indices = tf.placeholder(tf.int32, [None])
    item_indices = tf.placeholder(tf.int32, [None])
    ratings = tf.placeholder(tf.float32, [None])
    user_cf_feature = tf.nn.embedding_lookup(W_user_bias, user_indices, name='user_feature')
    item_cf_feature = tf.nn.embedding_lookup(W_item_bias, item_indices, name='item_feature')
    user_attr_feature = tf.nn.embedding_lookup(user_embeddings, user_indices, name='user_feature')
    item_attr_feature = tf.nn.embedding_lookup(item_embeddings, item_indices, name='item_feature')
    train_step, square_error, loss, merged_summary = build_model(user_cf_feature, user_attr_feature, user_attr_rank, item_cf_feature, item_attr_feature, item_attr_rank, ratings, layer_sizes, W_user, W_item, W_user_attr, W_item_attr, lamb, lr, mu)
    sess = tf.Session()
    init = tf.global_variables_initializer()
    sess.run(init)
    train_writer = tf.summary.FileWriter('\\\\mlsdata\\e$\\Users\\v-lianji\\DeepRecsys\\Test\\logs', sess.graph)
    n_instances = len(dataset.training_ratings_user)
    best_train_rmse, best_test_rmse, best_eval_rmse = (-1, -1, -1)
    best_eopch_idx = -1
    for ite in range(n_eopch):
        start = clock()
        for i in range(n_instances // batch_size):
            start_idx = i * batch_size
            end_idx = start_idx + batch_size
            cur_user_indices, cur_item_indices, cur_label = (dataset.training_ratings_user[start_idx:end_idx], dataset.training_ratings_item[start_idx:end_idx], dataset.training_ratings_score[start_idx:end_idx])
            sess.run(train_step, {user_indices: cur_user_indices, item_indices: cur_item_indices, ratings: cur_label})
        error_traing = sess.run(square_error, {user_indices: dataset.training_ratings_user, item_indices: dataset.training_ratings_item, ratings: dataset.training_ratings_score})
        error_test = sess.run(square_error, {user_indices: dataset.test_ratings_user, item_indices: dataset.test_ratings_item, ratings: dataset.test_ratings_score})
        error_eval = sess.run(square_error, {user_indices: dataset.eval_ratings_user, item_indices: dataset.eval_ratings_item, ratings: dataset.eval_ratings_score})
        loss_traing = sess.run(loss, {user_indices: dataset.training_ratings_user, item_indices: dataset.training_ratings_item, ratings: dataset.training_ratings_score})
        summary = sess.run(merged_summary, {user_indices: dataset.training_ratings_user, item_indices: dataset.training_ratings_item, ratings: dataset.training_ratings_score})
        train_writer.add_summary(summary, ite)
        end = clock()
        print('Iteration %d  RMSE(train): %f  RMSE(test): %f   RMSE(eval): %f   LOSS(train): %f  minutes: %f' % (ite, error_traing, error_test, error_eval, loss_traing, (end - start) / 60))
        if best_test_rmse < 0 or best_test_rmse > error_test:
            best_train_rmse, best_test_rmse, best_eval_rmse = (error_traing, error_test, error_eval)
            best_eopch_idx = ite
        elif ite - best_eopch_idx > 10:
            break
    train_writer.close()
    return (best_train_rmse, best_test_rmse, best_eval_rmse, best_eopch_idx)

def build_model(user_cf_feature, user_attr_feature, user_attr_rank, item_cf_feature, item_attr_feature, item_attr_rank, ratings, layer_size, W_user, W_item, W_user_attr, W_item_attr, lamb, lr, mu):
    layer_cnt = len(layer_size)
    hiddens_user = []
    hiddens_item = []
    hiddens_user.append(user_attr_feature)
    hiddens_item.append(item_attr_feature)
    b_user_list = []
    b_item_list = []
    W_user_list = []
    W_item_list = []
    for i in range(layer_cnt):
        with tf.name_scope('layer_' + str(i)):
            b_user_list.append(tf.Variable(tf.truncated_normal([layer_size[i]]), name='user_bias'))
            b_item_list.append(tf.Variable(tf.truncated_normal([layer_size[i]]), name='item_bias'))
            if i == 0:
                W_user_list.append(tf.Variable(tf.truncated_normal([user_attr_rank, layer_size[i]], stddev=1 / math.sqrt(float(layer_size[i])), mean=0), name='W_user'))
                W_item_list.append(tf.Variable(tf.truncated_normal([item_attr_rank, layer_size[i]], stddev=1 / math.sqrt(float(layer_size[i])), mean=0), name='W_item'))
                user_middle = tf.matmul(user_attr_feature, W_user_list[i]) + b_user_list[i]
                item_middle = tf.matmul(item_attr_feature, W_item_list[i]) + b_item_list[i]
            else:
                W_user_list.append(tf.Variable(tf.truncated_normal([layer_size[i - 1], layer_size[i]], stddev=1 / math.sqrt(float(layer_size[i])), mean=0), name='W_user'))
                W_item_list.append(tf.Variable(tf.truncated_normal([layer_size[i - 1], layer_size[i]], stddev=1 / math.sqrt(float(layer_size[i])), mean=0), name='W_item'))
                user_middle = tf.matmul(hiddens_user[i], W_user_list[i]) + b_user_list[i]
                item_middle = tf.matmul(hiddens_item[i], W_item_list[i]) + b_item_list[i]
            hiddens_user.append(tf.identity(user_middle, name='factor_user'))
            hiddens_item.append(tf.identity(item_middle, name='factor_item'))
    factor_user = hiddens_user[layer_cnt]
    factor_item = hiddens_item[layer_cnt]
    preds = tf.reduce_sum(tf.multiply(user_cf_feature, item_cf_feature), 1) + tf.reduce_sum(tf.multiply(factor_user, factor_item), 1) + mu
    square_error = tf.sqrt(tf.reduce_mean(tf.squared_difference(preds, ratings)))
    loss = square_error
    for i in range(layer_cnt):
        loss = loss + lamb * (tf.reduce_mean(tf.nn.l2_loss(W_user)) + tf.reduce_mean(tf.nn.l2_loss(W_item)) + tf.reduce_mean(tf.nn.l2_loss(W_user_attr)) + tf.reduce_mean(tf.nn.l2_loss(W_item_attr)) + tf.reduce_mean(tf.nn.l2_loss(W_user_list[i])) + tf.reduce_mean(tf.nn.l2_loss(W_item_list[i])) + tf.reduce_mean(tf.nn.l2_loss(b_user_list[i])) + tf.reduce_mean(tf.nn.l2_loss(b_item_list[i])))
    tf.summary.scalar('square_error', square_error)
    tf.summary.scalar('loss', loss)
    merged_summary = tf.summary.merge_all()
    train_step = tf.train.GradientDescentOptimizer(lr).minimize(loss)
    return (train_step, square_error, loss, merged_summary)

class BaseModel(object):

    def __init__(self, args, num_users, num_items):
        self.num_users, self.num_items = (num_users, num_items)
        self.lr = args.lr
        self.learner = args.learner
        self.init_stddev = args.init_stddev
        self.loss = args.loss
        self.lambda_id_emb = args.reg_id_embedding
        self.lambda_others = args.reg_others
        self.eta = args.eta

    def build_train_model(self, model_vector, model_len, ratings, model_params):
        init_value = self.init_stddev
        w_output = tf.Variable(tf.truncated_normal([model_len, 1], stddev=init_value, mean=0), name='w_output', dtype=tf.float32)
        b_output = tf.Variable(tf.truncated_normal([1], stddev=init_value * 0.01, mean=0), name='b_output', dtype=tf.float32)
        model_params.append(w_output)
        model_params.append(b_output)
        raw_predictions = tf.nn.xw_plus_b(model_vector, w_output, b_output, name='output')
        output = tf.reshape(tf.sigmoid(raw_predictions), [-1])
        with tf.name_scope('error'):
            type_of_loss = self.loss
            if type_of_loss == 'cross_entropy_loss':
                raw_error = tf.nn.sigmoid_cross_entropy_with_logits(logits=tf.reshape(raw_predictions, [-1]), labels=tf.reshape(self.ratings, [-1]))
                error = tf.reduce_mean(raw_error, name='error/cross_entropy_loss')
            elif type_of_loss == 'square_loss' or type_of_loss == 'rmse':
                raw_error = tf.squared_difference(output, ratings, name='error/squared_diff')
                error = tf.reduce_mean(raw_error, name='error/mean_squared_diff')
            elif type_of_loss == 'log_loss':
                raw_error = tf.losses.log_loss(predictions=output, labels=ratings)
                error = tf.reduce_mean(raw_error, name='error/mean_log_loss')
            l2_norm = 0
            for par in model_params:
                l2_norm += tf.nn.l2_loss(par) * self.lambda_others
            '\n            l2_norm += tf.nn.l2_loss(emb_user) * self.lambda_id_emb\n            l2_norm += tf.nn.l2_loss(emb_item) * self.lambda_id_emb\n            l2_norm += tf.nn.l2_loss(w_output) * self.lambda_others\n            l2_norm += tf.nn.l2_loss(b_output) * self.lambda_others\n            '
            loss = error + l2_norm
        update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
        with tf.control_dependencies(update_ops):
            type_of_opt = self.learner
            if type_of_opt == 'adadelta':
                train_step = tf.train.AdadeltaOptimizer(self.eta).minimize(loss, var_list=model_params)
            elif type_of_opt == 'sgd':
                train_step = tf.train.GradientDescentOptimizer(self.lr).minimize(loss, var_list=model_params)
            elif type_of_opt == 'adam':
                train_step = tf.train.AdamOptimizer(self.lr).minimize(loss, var_list=model_params)
            elif type_of_opt == 'ftrl':
                train_step = tf.train.FtrlOptimizer(self.lr).minimize(loss, var_list=model_params)
            else:
                train_step = tf.train.GradientDescentOptimizer(self.lr).minimize(loss, var_list=model_params)
        return (output, loss, error, raw_error, train_step)

def build_train_model(self, model_vector, model_len, ratings, model_params):
    init_value = self.init_stddev
    w_output = tf.Variable(tf.truncated_normal([model_len, 1], stddev=init_value, mean=0), name='w_output', dtype=tf.float32)
    b_output = tf.Variable(tf.truncated_normal([1], stddev=init_value * 0.01, mean=0), name='b_output', dtype=tf.float32)
    model_params.append(w_output)
    model_params.append(b_output)
    raw_predictions = tf.nn.xw_plus_b(model_vector, w_output, b_output, name='output')
    output = tf.reshape(tf.sigmoid(raw_predictions), [-1])
    with tf.name_scope('error'):
        type_of_loss = self.loss
        if type_of_loss == 'cross_entropy_loss':
            raw_error = tf.nn.sigmoid_cross_entropy_with_logits(logits=tf.reshape(raw_predictions, [-1]), labels=tf.reshape(self.ratings, [-1]))
            error = tf.reduce_mean(raw_error, name='error/cross_entropy_loss')
        elif type_of_loss == 'square_loss' or type_of_loss == 'rmse':
            raw_error = tf.squared_difference(output, ratings, name='error/squared_diff')
            error = tf.reduce_mean(raw_error, name='error/mean_squared_diff')
        elif type_of_loss == 'log_loss':
            raw_error = tf.losses.log_loss(predictions=output, labels=ratings)
            error = tf.reduce_mean(raw_error, name='error/mean_log_loss')
        l2_norm = 0
        for par in model_params:
            l2_norm += tf.nn.l2_loss(par) * self.lambda_others
        '\n            l2_norm += tf.nn.l2_loss(emb_user) * self.lambda_id_emb\n            l2_norm += tf.nn.l2_loss(emb_item) * self.lambda_id_emb\n            l2_norm += tf.nn.l2_loss(w_output) * self.lambda_others\n            l2_norm += tf.nn.l2_loss(b_output) * self.lambda_others\n            '
        loss = error + l2_norm
    update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
    with tf.control_dependencies(update_ops):
        type_of_opt = self.learner
        if type_of_opt == 'adadelta':
            train_step = tf.train.AdadeltaOptimizer(self.eta).minimize(loss, var_list=model_params)
        elif type_of_opt == 'sgd':
            train_step = tf.train.GradientDescentOptimizer(self.lr).minimize(loss, var_list=model_params)
        elif type_of_opt == 'adam':
            train_step = tf.train.AdamOptimizer(self.lr).minimize(loss, var_list=model_params)
        elif type_of_opt == 'ftrl':
            train_step = tf.train.FtrlOptimizer(self.lr).minimize(loss, var_list=model_params)
        else:
            train_step = tf.train.GradientDescentOptimizer(self.lr).minimize(loss, var_list=model_params)
    return (output, loss, error, raw_error, train_step)

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

