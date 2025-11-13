# Cluster 3

def get_keypoint(image, targets, predictions, heatmap_size, height, width, category, clip_at_zero=True, data_format='channels_last', name=None):
    predictions = tf.reshape(predictions, [1, -1, heatmap_size * heatmap_size])
    pred_max = tf.reduce_max(predictions, axis=-1)
    pred_indices = tf.argmax(predictions, axis=-1)
    pred_x, pred_y = (tf.cast(tf.floormod(pred_indices, heatmap_size), tf.float32), tf.cast(tf.floordiv(pred_indices, heatmap_size), tf.float32))
    width, height = (tf.cast(width, tf.float32), tf.cast(height, tf.float32))
    pred_x, pred_y = (pred_x * width / tf.cast(heatmap_size, tf.float32), pred_y * height / tf.cast(heatmap_size, tf.float32))
    if clip_at_zero:
        pred_x, pred_y = (pred_x * tf.cast(pred_max > 0, tf.float32), pred_y * tf.cast(pred_max > 0, tf.float32))
        pred_x = pred_x * tf.cast(pred_max > 0, tf.float32) + tf.cast(pred_max <= 0, tf.float32) * (width / 2.0)
        pred_y = pred_y * tf.cast(pred_max > 0, tf.float32) + tf.cast(pred_max <= 0, tf.float32) * (height / 2.0)
    if config.PRED_DEBUG:
        pred_indices_ = tf.squeeze(pred_indices)
        image_ = tf.squeeze(image) * 255.0
        pred_heatmap = tf.one_hot(pred_indices_, heatmap_size * heatmap_size, on_value=1.0, off_value=0.0, axis=-1, dtype=tf.float32)
        pred_heatmap = tf.reshape(pred_heatmap, [-1, heatmap_size, heatmap_size])
        if data_format == 'channels_first':
            image_ = tf.transpose(image_, perm=(1, 2, 0))
        save_image_op = tf.py_func(save_image_with_heatmap, [image_, height, width, heatmap_size, tf.reshape(pred_heatmap * 255.0, [-1, heatmap_size, heatmap_size]), tf.reshape(predictions, [-1, heatmap_size, heatmap_size]), config.left_right_group_map[category][0], config.left_right_group_map[category][1], config.left_right_group_map[category][2]], tf.int64, stateful=True)
        with tf.control_dependencies([save_image_op]):
            pred_x, pred_y = (pred_x * 1.0, pred_y * 1.0)
    return (pred_x, pred_y)

def keypoint_model_fn(features, labels, mode, params):
    targets = labels['targets']
    shape = labels['shape']
    classid = labels['classid']
    key_v = labels['key_v']
    isvalid = labels['isvalid']
    norm_value = labels['norm_value']
    cur_batch_size = tf.shape(features)[0]
    with tf.variable_scope(params['model_scope'], default_name=None, values=[features], reuse=tf.AUTO_REUSE):
        pred_outputs = cpn.cascaded_pyramid_net(features, config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], params['heatmap_size'], mode == tf.estimator.ModeKeys.TRAIN, params['data_format'])
    if params['data_format'] == 'channels_last':
        pred_outputs = [tf.transpose(pred_outputs[ind], [0, 3, 1, 2], name='outputs_trans_{}'.format(ind)) for ind in list(range(len(pred_outputs)))]
    score_map = pred_outputs[-1]
    pred_x, pred_y = get_keypoint(features, targets, score_map, params['heatmap_size'], params['train_image_size'], params['train_image_size'], params['model_scope'] if 'all' not in params['model_scope'] else '*', clip_at_zero=True, data_format=params['data_format'])
    targets = 255.0 * targets
    blur_list = [1.0, 1.37, 1.73, 2.4, None]
    targets_list = []
    for sigma in blur_list:
        if sigma is None:
            targets_list.append(targets)
        else:
            targets_list.append(gaussian_blur(targets, config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], sigma, params['data_format'], 'blur_{}'.format(sigma)))
    ne_mertric = mertric.normalized_error(targets, score_map, norm_value, key_v, isvalid, cur_batch_size, config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], params['heatmap_size'], params['train_image_size'])
    all_visible = tf.expand_dims(tf.expand_dims(tf.cast(tf.logical_and(key_v > 0, isvalid > 0), tf.float32), axis=-1), axis=-1)
    targets_list = [targets_list[ind] * all_visible for ind in list(range(len(targets_list)))]
    pred_outputs = [pred_outputs[ind] * all_visible for ind in list(range(len(pred_outputs)))]
    sq_diff = tf.reduce_sum(tf.squared_difference(targets, pred_outputs[-1]), axis=-1)
    last_pred_mse = tf.metrics.mean_absolute_error(sq_diff, tf.zeros_like(sq_diff), name='last_pred_mse')
    metrics = {'normalized_error': ne_mertric, 'last_pred_mse': last_pred_mse}
    predictions = {'normalized_error': ne_mertric[1]}
    ne_mertric = tf.identity(ne_mertric[1], name='ne_mertric')
    base_learning_rate = params['learning_rate']
    mse_loss_list = []
    if params['use_ohkm']:
        base_learning_rate = 1.0 * base_learning_rate
        for pred_ind in list(range(len(pred_outputs) - 1)):
            mse_loss_list.append(0.5 * tf.losses.mean_squared_error(targets_list[pred_ind], pred_outputs[pred_ind], weights=1.0 / tf.cast(cur_batch_size, tf.float32), scope='loss_{}'.format(pred_ind), loss_collection=None, reduction=tf.losses.Reduction.MEAN))
        temp_loss = tf.reduce_mean(tf.reshape(tf.losses.mean_squared_error(targets_list[-1], pred_outputs[-1], weights=1.0, loss_collection=None, reduction=tf.losses.Reduction.NONE), [cur_batch_size, config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], -1]), axis=-1)
        num_topk = config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'] // 2
        gather_col = tf.nn.top_k(temp_loss, k=num_topk, sorted=True)[1]
        gather_row = tf.reshape(tf.tile(tf.reshape(tf.range(cur_batch_size), [-1, 1]), [1, num_topk]), [-1, 1])
        gather_indcies = tf.stop_gradient(tf.stack([gather_row, tf.reshape(gather_col, [-1, 1])], axis=-1))
        select_targets = tf.gather_nd(targets_list[-1], gather_indcies)
        select_heatmap = tf.gather_nd(pred_outputs[-1], gather_indcies)
        mse_loss_list.append(tf.losses.mean_squared_error(select_targets, select_heatmap, weights=1.0 / tf.cast(cur_batch_size, tf.float32), scope='loss_{}'.format(len(pred_outputs) - 1), loss_collection=None, reduction=tf.losses.Reduction.MEAN))
    else:
        for pred_ind in list(range(len(pred_outputs))):
            mse_loss_list.append(tf.losses.mean_squared_error(targets_list[pred_ind], pred_outputs[pred_ind], weights=1.0 / tf.cast(cur_batch_size, tf.float32), scope='loss_{}'.format(pred_ind), loss_collection=None, reduction=tf.losses.Reduction.MEAN))
    mse_loss = tf.multiply(params['mse_weight'], tf.add_n(mse_loss_list), name='mse_loss')
    tf.summary.scalar('mse', mse_loss)
    tf.losses.add_loss(mse_loss)
    loss = mse_loss + params['weight_decay'] * tf.add_n([tf.nn.l2_loss(v) for v in tf.trainable_variables() if 'batch_normalization' not in v.name])
    total_loss = tf.identity(loss, name='total_loss')
    tf.summary.scalar('loss', total_loss)
    if mode == tf.estimator.ModeKeys.EVAL:
        return tf.estimator.EstimatorSpec(mode=mode, loss=loss, predictions=predictions, eval_metric_ops=metrics)
    if mode == tf.estimator.ModeKeys.TRAIN:
        global_step = tf.train.get_or_create_global_step()
        lr_values = [params['warmup_learning_rate']] + [base_learning_rate * decay for decay in params['lr_decay_factors']]
        learning_rate = tf.train.piecewise_constant(tf.cast(global_step, tf.int32), [params['warmup_steps']] + [int(float(ep) * params['steps_per_epoch']) for ep in params['decay_boundaries']], lr_values)
        truncated_learning_rate = tf.maximum(learning_rate, tf.constant(params['end_learning_rate'], dtype=learning_rate.dtype), name='learning_rate')
        tf.summary.scalar('lr', truncated_learning_rate)
        optimizer = tf.train.MomentumOptimizer(learning_rate=truncated_learning_rate, momentum=params['momentum'])
        update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
        with tf.control_dependencies(update_ops):
            train_op = optimizer.minimize(loss, global_step)
    else:
        train_op = None
    return tf.estimator.EstimatorSpec(mode=mode, predictions=predictions, loss=loss, train_op=train_op, eval_metric_ops=metrics, scaffold=tf.train.Scaffold(init_fn=train_helper.get_init_fn_for_scaffold_(params['checkpoint_path'], params['model_dir'], params['checkpoint_exclude_scopes'], params['model_scope'], params['checkpoint_model_scope'], params['ignore_missing_vars'])))

def get_keypoint(image, targets, predictions, heatmap_size, height, width, category, clip_at_zero=True, data_format='channels_last', name=None):
    predictions = tf.reshape(predictions, [1, -1, heatmap_size * heatmap_size])
    pred_max = tf.reduce_max(predictions, axis=-1)
    pred_indices = tf.argmax(predictions, axis=-1)
    pred_x, pred_y = (tf.cast(tf.floormod(pred_indices, heatmap_size), tf.float32), tf.cast(tf.floordiv(pred_indices, heatmap_size), tf.float32))
    width, height = (tf.cast(width, tf.float32), tf.cast(height, tf.float32))
    pred_x, pred_y = (pred_x * width / tf.cast(heatmap_size, tf.float32), pred_y * height / tf.cast(heatmap_size, tf.float32))
    if clip_at_zero:
        pred_x, pred_y = (pred_x * tf.cast(pred_max > 0, tf.float32), pred_y * tf.cast(pred_max > 0, tf.float32))
        pred_x = pred_x * tf.cast(pred_max > 0, tf.float32) + tf.cast(pred_max <= 0, tf.float32) * (width / 2.0)
        pred_y = pred_y * tf.cast(pred_max > 0, tf.float32) + tf.cast(pred_max <= 0, tf.float32) * (height / 2.0)
    if config.PRED_DEBUG:
        pred_indices_ = tf.squeeze(pred_indices)
        image_ = tf.squeeze(image) * 255.0
        pred_heatmap = tf.one_hot(pred_indices_, heatmap_size * heatmap_size, on_value=1.0, off_value=0.0, axis=-1, dtype=tf.float32)
        pred_heatmap = tf.reshape(pred_heatmap, [-1, heatmap_size, heatmap_size])
        if data_format == 'channels_first':
            image_ = tf.transpose(image_, perm=(1, 2, 0))
        save_image_op = tf.py_func(save_image_with_heatmap, [image_, height, width, heatmap_size, tf.reshape(pred_heatmap * 255.0, [-1, heatmap_size, heatmap_size]), tf.reshape(predictions, [-1, heatmap_size, heatmap_size]), config.left_right_group_map[category][0], config.left_right_group_map[category][1], config.left_right_group_map[category][2]], tf.int64, stateful=True)
        with tf.control_dependencies([save_image_op]):
            pred_x, pred_y = (pred_x * 1.0, pred_y * 1.0)
    return (pred_x, pred_y)

def keypoint_model_fn(features, labels, mode, params):
    targets = labels['targets']
    shape = labels['shape']
    classid = labels['classid']
    key_v = labels['key_v']
    isvalid = labels['isvalid']
    norm_value = labels['norm_value']
    cur_batch_size = tf.shape(features)[0]
    with tf.variable_scope(params['model_scope'], default_name=None, values=[features], reuse=tf.AUTO_REUSE):
        pred_outputs = cpn.cascaded_pyramid_net(features, config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], params['heatmap_size'], mode == tf.estimator.ModeKeys.TRAIN, params['data_format'])
    if params['data_format'] == 'channels_last':
        pred_outputs = [tf.transpose(pred_outputs[ind], [0, 3, 1, 2], name='outputs_trans_{}'.format(ind)) for ind in list(range(len(pred_outputs)))]
    score_map = pred_outputs[-1]
    pred_x, pred_y = get_keypoint(features, targets, score_map, params['heatmap_size'], params['train_image_size'], params['train_image_size'], params['model_scope'] if 'all' not in params['model_scope'] else '*', clip_at_zero=True, data_format=params['data_format'])
    targets = 255.0 * targets
    blur_list = [1.0, 1.37, 1.73, 2.4, None]
    targets_list = []
    for sigma in blur_list:
        if sigma is None:
            targets_list.append(targets)
        else:
            targets_list.append(gaussian_blur(targets, config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], sigma, params['data_format'], 'blur_{}'.format(sigma)))
    ne_mertric = mertric.normalized_error(targets, score_map, norm_value, key_v, isvalid, cur_batch_size, config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], params['heatmap_size'], params['train_image_size'])
    all_visible = tf.expand_dims(tf.expand_dims(tf.cast(tf.logical_and(key_v > 0, isvalid > 0), tf.float32), axis=-1), axis=-1)
    targets_list = [targets_list[ind] * all_visible for ind in list(range(len(targets_list)))]
    pred_outputs = [pred_outputs[ind] * all_visible for ind in list(range(len(pred_outputs)))]
    sq_diff = tf.reduce_sum(tf.squared_difference(targets, pred_outputs[-1]), axis=-1)
    last_pred_mse = tf.metrics.mean_absolute_error(sq_diff, tf.zeros_like(sq_diff), name='last_pred_mse')
    metrics = {'normalized_error': ne_mertric, 'last_pred_mse': last_pred_mse}
    predictions = {'normalized_error': ne_mertric[1]}
    ne_mertric = tf.identity(ne_mertric[1], name='ne_mertric')
    base_learning_rate = params['learning_rate']
    mse_loss_list = []
    if params['use_ohkm']:
        base_learning_rate = 1.0 * base_learning_rate
        for pred_ind in list(range(len(pred_outputs) - 1)):
            mse_loss_list.append(0.5 * tf.losses.mean_squared_error(targets_list[pred_ind], pred_outputs[pred_ind], weights=1.0 / tf.cast(cur_batch_size, tf.float32), scope='loss_{}'.format(pred_ind), loss_collection=None, reduction=tf.losses.Reduction.MEAN))
        temp_loss = tf.reduce_mean(tf.reshape(tf.losses.mean_squared_error(targets_list[-1], pred_outputs[-1], weights=1.0, loss_collection=None, reduction=tf.losses.Reduction.NONE), [cur_batch_size, config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], -1]), axis=-1)
        num_topk = config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'] // 2
        gather_col = tf.nn.top_k(temp_loss, k=num_topk, sorted=True)[1]
        gather_row = tf.reshape(tf.tile(tf.reshape(tf.range(cur_batch_size), [-1, 1]), [1, num_topk]), [-1, 1])
        gather_indcies = tf.stop_gradient(tf.stack([gather_row, tf.reshape(gather_col, [-1, 1])], axis=-1))
        select_targets = tf.gather_nd(targets_list[-1], gather_indcies)
        select_heatmap = tf.gather_nd(pred_outputs[-1], gather_indcies)
        mse_loss_list.append(tf.losses.mean_squared_error(select_targets, select_heatmap, weights=1.0 / tf.cast(cur_batch_size, tf.float32), scope='loss_{}'.format(len(pred_outputs) - 1), loss_collection=None, reduction=tf.losses.Reduction.MEAN))
    else:
        for pred_ind in list(range(len(pred_outputs))):
            mse_loss_list.append(tf.losses.mean_squared_error(targets_list[pred_ind], pred_outputs[pred_ind], weights=1.0 / tf.cast(cur_batch_size, tf.float32), scope='loss_{}'.format(pred_ind), loss_collection=None, reduction=tf.losses.Reduction.MEAN))
    mse_loss = tf.multiply(params['mse_weight'], tf.add_n(mse_loss_list), name='mse_loss')
    tf.summary.scalar('mse', mse_loss)
    tf.losses.add_loss(mse_loss)
    loss = mse_loss + params['weight_decay'] * tf.add_n([tf.nn.l2_loss(v) for v in tf.trainable_variables() if 'batch_normalization' not in v.name])
    total_loss = tf.identity(loss, name='total_loss')
    tf.summary.scalar('loss', total_loss)
    if mode == tf.estimator.ModeKeys.EVAL:
        return tf.estimator.EstimatorSpec(mode=mode, loss=loss, predictions=predictions, eval_metric_ops=metrics)
    if mode == tf.estimator.ModeKeys.TRAIN:
        global_step = tf.train.get_or_create_global_step()
        lr_values = [params['warmup_learning_rate']] + [base_learning_rate * decay for decay in params['lr_decay_factors']]
        learning_rate = tf.train.piecewise_constant(tf.cast(global_step, tf.int32), [params['warmup_steps']] + [int(float(ep) * params['steps_per_epoch']) for ep in params['decay_boundaries']], lr_values)
        truncated_learning_rate = tf.maximum(learning_rate, tf.constant(params['end_learning_rate'], dtype=learning_rate.dtype), name='learning_rate')
        tf.summary.scalar('lr', truncated_learning_rate)
        optimizer = tf.train.MomentumOptimizer(learning_rate=truncated_learning_rate, momentum=params['momentum'])
        update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
        with tf.control_dependencies(update_ops):
            train_op = optimizer.minimize(loss, global_step)
    else:
        train_op = None
    return tf.estimator.EstimatorSpec(mode=mode, predictions=predictions, loss=loss, train_op=train_op, eval_metric_ops=metrics, scaffold=tf.train.Scaffold(init_fn=train_helper.get_init_fn_for_scaffold_(params['checkpoint_path'], params['model_dir'], params['checkpoint_exclude_scopes'], params['model_scope'], params['checkpoint_model_scope'], params['ignore_missing_vars'])))

def get_keypoint(image, predictions, heatmap_size, height, width, category, clip_at_zero=False, data_format='channels_last', name=None):
    predictions = tf.reshape(predictions, [1, -1, heatmap_size * heatmap_size])
    pred_max = tf.reduce_max(predictions, axis=-1)
    pred_max_indices = tf.argmax(predictions, axis=-1)
    pred_max_x, pred_max_y = (tf.cast(tf.floormod(pred_max_indices, heatmap_size), tf.float32), tf.cast(tf.floordiv(pred_max_indices, heatmap_size), tf.float32))
    mask_predictions = predictions * tf.one_hot(pred_max_indices, heatmap_size * heatmap_size, on_value=0.0, off_value=1.0, dtype=tf.float32)
    pred_next_max = tf.reduce_max(mask_predictions, axis=-1)
    pred_next_max_indices = tf.argmax(mask_predictions, axis=-1)
    pred_next_max_x, pred_next_max_y = (tf.cast(tf.floormod(pred_next_max_indices, heatmap_size), tf.float32), tf.cast(tf.floordiv(pred_next_max_indices, heatmap_size), tf.float32))
    dist = tf.pow(tf.pow(pred_next_max_x - pred_max_x, 2.0) + tf.pow(pred_next_max_y - pred_max_y, 2.0), 0.5)
    pred_x = tf.where(dist < 0.001, pred_max_x, pred_max_x + (pred_next_max_x - pred_max_x) * 0.25 / dist)
    pred_y = tf.where(dist < 0.001, pred_max_y, pred_max_y + (pred_next_max_y - pred_max_y) * 0.25 / dist)
    pred_indices_ = tf.squeeze(tf.cast(pred_x, tf.int64) + tf.cast(pred_y, tf.int64) * heatmap_size)
    width, height = (tf.cast(width, tf.float32), tf.cast(height, tf.float32))
    width_ratio, height_ratio = (width / tf.cast(heatmap_size, tf.float32), height / tf.cast(heatmap_size, tf.float32))
    pred_x, pred_y = (pred_x * width_ratio, pred_y * height_ratio)
    if clip_at_zero:
        pred_x, pred_y = (pred_x * tf.cast(pred_max > 0, tf.float32), pred_y * tf.cast(pred_max > 0, tf.float32))
        pred_x = pred_x * tf.cast(pred_max > 0, tf.float32) + tf.cast(pred_max <= 0, tf.float32) * (width / 2.0)
        pred_y = pred_y * tf.cast(pred_max > 0, tf.float32) + tf.cast(pred_max <= 0, tf.float32) * (height / 2.0)
    if config.PRED_DEBUG:
        image_ = tf.squeeze(image) * 255.0
        pred_heatmap = tf.one_hot(pred_indices_, heatmap_size * heatmap_size, on_value=255, off_value=0, axis=-1, dtype=tf.int32)
        pred_heatmap = tf.reshape(pred_heatmap, [-1, heatmap_size, heatmap_size])
        if data_format == 'channels_first':
            image_ = tf.transpose(image_, perm=(1, 2, 0))
        save_image_op = tf.py_func(save_image_with_heatmap, [image_, height, width, heatmap_size, pred_heatmap, tf.reshape(predictions, [-1, heatmap_size, heatmap_size]), config.left_right_group_map[category][0], config.left_right_group_map[category][1], config.left_right_group_map[category][2]], tf.int64, stateful=True)
        with tf.control_dependencies([save_image_op]):
            pred_x, pred_y = (pred_x * 1.0, pred_y * 1.0)
    return (pred_x, pred_y)

def keypoint_model_fn(features, labels, mode, params):
    shape = features['shape']
    classid = features['classid']
    file_name = features['file_name']
    features = features['images']
    file_name = tf.identity(file_name, name='current_file')
    image = preprocessing.preprocess_for_test_raw_output(features, params['train_image_size'], params['train_image_size'], data_format='NCHW' if FLAGS.data_format == 'channels_first' else 'NHWC', scope='first_stage')
    if not params['flip_on_test']:
        with tf.variable_scope(params['model_scope'], default_name=None, values=[image], reuse=tf.AUTO_REUSE):
            pred_outputs = backbone_(image, config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], params['heatmap_size'], mode == tf.estimator.ModeKeys.TRAIN, params['data_format'])
        if params['data_format'] == 'channels_last':
            pred_outputs = [tf.transpose(pred_outputs[ind], [0, 3, 1, 2], name='outputs_trans_{}'.format(ind)) for ind in list(range(len(pred_outputs)))]
        pred_x_first_stage, pred_y_first_stage = get_keypoint(image, pred_outputs[-1], params['heatmap_size'], shape[0][0], shape[0][1], params['model_scope'] if 'all' not in params['model_scope'] else '*', clip_at_zero=False, data_format=params['data_format'])
    else:
        if params['data_format'] == 'channels_last':
            double_features = tf.reshape(tf.stack([image, tf.map_fn(tf.image.flip_left_right, image, back_prop=False)], axis=1), [-1, params['train_image_size'], params['train_image_size'], 3])
        else:
            double_features = tf.reshape(tf.stack([image, tf.transpose(tf.map_fn(tf.image.flip_left_right, tf.transpose(image, [0, 2, 3, 1], name='nchw2nhwc'), back_prop=False), [0, 3, 1, 2], name='nhwc2nchw')], axis=1), [-1, 3, params['train_image_size'], params['train_image_size']])
        num_joints = config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*']
        with tf.variable_scope(params['model_scope'], default_name=None, values=[double_features], reuse=tf.AUTO_REUSE):
            pred_outputs = backbone_(double_features, config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], params['heatmap_size'], mode == tf.estimator.ModeKeys.TRAIN, params['data_format'])
        if params['data_format'] == 'channels_last':
            pred_outputs = [tf.transpose(pred_outputs[ind], [0, 3, 1, 2], name='outputs_trans_{}'.format(ind)) for ind in list(range(len(pred_outputs)))]
        row_indices = tf.tile(tf.reshape(tf.stack([tf.range(0, tf.shape(double_features)[0], delta=2), tf.range(1, tf.shape(double_features)[0], delta=2)], axis=0), [-1, 1]), [1, num_joints])
        col_indices = tf.reshape(tf.tile(tf.reshape(tf.stack([tf.range(num_joints), tf.constant(config.left_right_remap[params['model_scope'] if 'all' not in params['model_scope'] else '*'])], axis=0), [2, -1]), [1, tf.shape(features)[0]]), [-1, num_joints])
        flip_indices = tf.stack([row_indices, col_indices], axis=-1)
        pred_outputs = [tf.gather_nd(pred_outputs[ind], flip_indices, name='gather_nd_{}'.format(ind)) for ind in list(range(len(pred_outputs)))]

        def cond_flip(heatmap_ind):
            return tf.cond(heatmap_ind[1] < tf.shape(features)[0], lambda: heatmap_ind[0], lambda: tf.transpose(tf.image.flip_left_right(tf.transpose(heatmap_ind[0], [1, 2, 0], name='pred_nchw2nhwc')), [2, 0, 1], name='pred_nhwc2nchw'))
        pred_outputs = [tf.map_fn(cond_flip, [pred_outputs[ind], tf.range(tf.shape(double_features)[0])], dtype=tf.float32, parallel_iterations=10, back_prop=True, swap_memory=False, infer_shape=True, name='map_fn_{}'.format(ind)) for ind in list(range(len(pred_outputs)))]
        pred_outputs = [tf.split(_, 2) for _ in pred_outputs]
        pred_outputs_1 = [_[0] for _ in pred_outputs]
        pred_outputs_2 = [_[1] for _ in pred_outputs]
        pred_x_first_stage1, pred_y_first_stage1 = get_keypoint(image, pred_outputs_1[-1], params['heatmap_size'], shape[0][0], shape[0][1], params['model_scope'] if 'all' not in params['model_scope'] else '*', clip_at_zero=False, data_format=params['data_format'])
        pred_x_first_stage2, pred_y_first_stage2 = get_keypoint(image, pred_outputs_2[-1], params['heatmap_size'], shape[0][0], shape[0][1], params['model_scope'] if 'all' not in params['model_scope'] else '*', clip_at_zero=False, data_format=params['data_format'])
        dist = tf.pow(tf.pow(pred_x_first_stage1 - pred_x_first_stage2, 2.0) + tf.pow(pred_y_first_stage1 - pred_y_first_stage2, 2.0), 0.5)
        pred_x_first_stage = tf.where(dist < 0.001, pred_x_first_stage1, pred_x_first_stage1 + (pred_x_first_stage2 - pred_x_first_stage1) * 0.25 / dist)
        pred_y_first_stage = tf.where(dist < 0.001, pred_y_first_stage1, pred_y_first_stage1 + (pred_y_first_stage2 - pred_y_first_stage1) * 0.25 / dist)
    xmin = tf.cast(tf.reduce_min(pred_x_first_stage), tf.int64)
    xmax = tf.cast(tf.reduce_max(pred_x_first_stage), tf.int64)
    ymin = tf.cast(tf.reduce_min(pred_y_first_stage), tf.int64)
    ymax = tf.cast(tf.reduce_max(pred_y_first_stage), tf.int64)
    xmin, ymin, xmax, ymax = (xmin - 100, ymin - 80, xmax + 100, ymax + 80)
    xmin = tf.clip_by_value(xmin, 0, shape[0][1][0] - 1)
    ymin = tf.clip_by_value(ymin, 0, shape[0][0][0] - 1)
    xmax = tf.clip_by_value(xmax, 0, shape[0][1][0] - 1)
    ymax = tf.clip_by_value(ymax, 0, shape[0][0][0] - 1)
    bbox_h = ymax - ymin
    bbox_w = xmax - xmin
    areas = bbox_h * bbox_w
    offsets = tf.stack([xmin, ymin], axis=0)
    crop_shape = tf.stack([bbox_h, bbox_w, shape[0][2][0]], axis=0)
    ymin, xmin, bbox_h, bbox_w = (tf.cast(ymin, tf.int32), tf.cast(xmin, tf.int32), tf.cast(bbox_h, tf.int32), tf.cast(bbox_w, tf.int32))
    single_image = tf.squeeze(features, [0])
    crop_image = tf.image.crop_to_bounding_box(single_image, ymin, xmin, bbox_h, bbox_w)
    crop_image = tf.expand_dims(crop_image, 0)
    image, shape, offsets = tf.cond(areas > 0, lambda: (crop_image, crop_shape, offsets), lambda: (features, shape, tf.constant([0, 0], tf.int64)))
    offsets.set_shape([2])
    offsets = tf.to_float(offsets)
    shape = tf.reshape(shape, [1, 3])
    image = preprocessing.preprocess_for_test_raw_output(image, params['train_image_size'], params['train_image_size'], data_format='NCHW' if FLAGS.data_format == 'channels_first' else 'NHWC', scope='second_stage')
    if not params['flip_on_test']:
        with tf.variable_scope(params['model_scope'], default_name=None, values=[image], reuse=True):
            pred_outputs = backbone_(image, config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], params['heatmap_size'], mode == tf.estimator.ModeKeys.TRAIN, params['data_format'])
        with tf.name_scope('refine_prediction'):
            if params['data_format'] == 'channels_last':
                pred_outputs = [tf.transpose(pred_outputs[ind], [0, 3, 1, 2], name='outputs_trans_{}'.format(ind)) for ind in list(range(len(pred_outputs)))]
            pred_x, pred_y = get_keypoint(image, pred_outputs[-1], params['heatmap_size'], shape[0][0], shape[0][1], params['model_scope'] if 'all' not in params['model_scope'] else '*', clip_at_zero=False, data_format=params['data_format'])
    else:
        with tf.name_scope('refine_prediction'):
            if params['data_format'] == 'channels_last':
                double_features = tf.reshape(tf.stack([image, tf.map_fn(tf.image.flip_left_right, image, back_prop=False)], axis=1), [-1, params['train_image_size'], params['train_image_size'], 3])
            else:
                double_features = tf.reshape(tf.stack([image, tf.transpose(tf.map_fn(tf.image.flip_left_right, tf.transpose(image, [0, 2, 3, 1], name='nchw2nhwc'), back_prop=False), [0, 3, 1, 2], name='nhwc2nchw')], axis=1), [-1, 3, params['train_image_size'], params['train_image_size']])
        num_joints = config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*']
        with tf.variable_scope(params['model_scope'], default_name=None, values=[double_features], reuse=True):
            pred_outputs = backbone_(double_features, config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], params['heatmap_size'], mode == tf.estimator.ModeKeys.TRAIN, params['data_format'])
        with tf.name_scope('refine_prediction'):
            if params['data_format'] == 'channels_last':
                pred_outputs = [tf.transpose(pred_outputs[ind], [0, 3, 1, 2], name='outputs_trans_{}'.format(ind)) for ind in list(range(len(pred_outputs)))]
            row_indices = tf.tile(tf.reshape(tf.stack([tf.range(0, tf.shape(double_features)[0], delta=2), tf.range(1, tf.shape(double_features)[0], delta=2)], axis=0), [-1, 1]), [1, num_joints])
            col_indices = tf.reshape(tf.tile(tf.reshape(tf.stack([tf.range(num_joints), tf.constant(config.left_right_remap[params['model_scope'] if 'all' not in params['model_scope'] else '*'])], axis=0), [2, -1]), [1, tf.shape(features)[0]]), [-1, num_joints])
            flip_indices = tf.stack([row_indices, col_indices], axis=-1)
            pred_outputs = [tf.gather_nd(pred_outputs[ind], flip_indices, name='gather_nd_{}'.format(ind)) for ind in list(range(len(pred_outputs)))]

            def cond_flip(heatmap_ind):
                return tf.cond(heatmap_ind[1] < tf.shape(features)[0], lambda: heatmap_ind[0], lambda: tf.transpose(tf.image.flip_left_right(tf.transpose(heatmap_ind[0], [1, 2, 0], name='pred_nchw2nhwc')), [2, 0, 1], name='pred_nhwc2nchw'))
            pred_outputs = [tf.map_fn(cond_flip, [pred_outputs[ind], tf.range(tf.shape(double_features)[0])], dtype=tf.float32, parallel_iterations=10, back_prop=True, swap_memory=False, infer_shape=True, name='map_fn_{}'.format(ind)) for ind in list(range(len(pred_outputs)))]
            pred_outputs = [tf.split(_, 2) for _ in pred_outputs]
            pred_outputs_1 = [_[0] for _ in pred_outputs]
            pred_outputs_2 = [_[1] for _ in pred_outputs]
            pred_x_first_stage1, pred_y_first_stage1 = get_keypoint(image, pred_outputs_1[-1], params['heatmap_size'], shape[0][0], shape[0][1], params['model_scope'] if 'all' not in params['model_scope'] else '*', clip_at_zero=False, data_format=params['data_format'])
            pred_x_first_stage2, pred_y_first_stage2 = get_keypoint(image, pred_outputs_2[-1], params['heatmap_size'], shape[0][0], shape[0][1], params['model_scope'] if 'all' not in params['model_scope'] else '*', clip_at_zero=False, data_format=params['data_format'])
            dist = tf.pow(tf.pow(pred_x_first_stage1 - pred_x_first_stage2, 2.0) + tf.pow(pred_y_first_stage1 - pred_y_first_stage2, 2.0), 0.5)
            pred_x = tf.where(dist < 0.001, pred_x_first_stage1, pred_x_first_stage1 + (pred_x_first_stage2 - pred_x_first_stage1) * 0.25 / dist)
            pred_y = tf.where(dist < 0.001, pred_y_first_stage1, pred_y_first_stage1 + (pred_y_first_stage2 - pred_y_first_stage1) * 0.25 / dist)
    predictions = {'pred_x': pred_x + offsets[0], 'pred_y': pred_y + offsets[1], 'file_name': file_name}
    if mode == tf.estimator.ModeKeys.PREDICT:
        return tf.estimator.EstimatorSpec(mode=mode, predictions=predictions, loss=None, train_op=None)
    else:
        raise ValueError('Only "PREDICT" mode is supported.')

def get_keypoint(image, targets, predictions, heatmap_size, height, width, category, clip_at_zero=True, data_format='channels_last', name=None):
    predictions = tf.reshape(predictions, [1, -1, heatmap_size * heatmap_size])
    pred_max = tf.reduce_max(predictions, axis=-1)
    pred_indices = tf.argmax(predictions, axis=-1)
    pred_x, pred_y = (tf.cast(tf.floormod(pred_indices, heatmap_size), tf.float32), tf.cast(tf.floordiv(pred_indices, heatmap_size), tf.float32))
    width, height = (tf.cast(width, tf.float32), tf.cast(height, tf.float32))
    pred_x, pred_y = (pred_x * width / tf.cast(heatmap_size, tf.float32), pred_y * height / tf.cast(heatmap_size, tf.float32))
    if clip_at_zero:
        pred_x, pred_y = (pred_x * tf.cast(pred_max > 0, tf.float32), pred_y * tf.cast(pred_max > 0, tf.float32))
        pred_x = pred_x * tf.cast(pred_max > 0, tf.float32) + tf.cast(pred_max <= 0, tf.float32) * (width / 2.0)
        pred_y = pred_y * tf.cast(pred_max > 0, tf.float32) + tf.cast(pred_max <= 0, tf.float32) * (height / 2.0)
    if config.PRED_DEBUG:
        pred_indices_ = tf.squeeze(pred_indices)
        image_ = tf.squeeze(image) * 255.0
        pred_heatmap = tf.one_hot(pred_indices_, heatmap_size * heatmap_size, on_value=1.0, off_value=0.0, axis=-1, dtype=tf.float32)
        pred_heatmap = tf.reshape(pred_heatmap, [-1, heatmap_size, heatmap_size])
        if data_format == 'channels_first':
            image_ = tf.transpose(image_, perm=(1, 2, 0))
        save_image_op = tf.py_func(save_image_with_heatmap, [image_, height, width, heatmap_size, tf.reshape(pred_heatmap * 255.0, [-1, heatmap_size, heatmap_size]), tf.reshape(predictions, [-1, heatmap_size, heatmap_size]), config.left_right_group_map[category][0], config.left_right_group_map[category][1], config.left_right_group_map[category][2]], tf.int64, stateful=True)
        with tf.control_dependencies([save_image_op]):
            pred_x, pred_y = (pred_x * 1.0, pred_y * 1.0)
    return (pred_x, pred_y)

def keypoint_model_fn(features, labels, mode, params):
    targets = labels['targets']
    shape = labels['shape']
    classid = labels['classid']
    key_v = labels['key_v']
    isvalid = labels['isvalid']
    norm_value = labels['norm_value']
    cur_batch_size = tf.shape(features)[0]
    with tf.variable_scope(params['model_scope'], default_name=None, values=[features], reuse=tf.AUTO_REUSE):
        pred_outputs = hg.create_model(features, params['num_stacks'], params['feats_channals'], config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], params['num_modules'], mode == tf.estimator.ModeKeys.TRAIN, params['data_format'])
    if params['data_format'] == 'channels_last':
        pred_outputs = [tf.transpose(pred_outputs[ind], [0, 3, 1, 2], name='outputs_trans_{}'.format(ind)) for ind in list(range(len(pred_outputs)))]
    score_map = pred_outputs[-1]
    pred_x, pred_y = get_keypoint(features, targets, score_map, params['heatmap_size'], params['train_image_size'], params['train_image_size'], params['model_scope'] if 'all' not in params['model_scope'] else '*', clip_at_zero=True, data_format=params['data_format'])
    targets = 255.0 * targets
    ne_mertric = mertric.normalized_error(targets, score_map, norm_value, key_v, isvalid, cur_batch_size, config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], params['heatmap_size'], params['train_image_size'])
    all_visible = tf.expand_dims(tf.expand_dims(tf.cast(tf.logical_and(key_v > 0, isvalid > 0), tf.float32), axis=-1), axis=-1)
    targets = targets * all_visible
    pred_outputs = [pred_outputs[ind] * all_visible for ind in list(range(len(pred_outputs)))]
    sq_diff = tf.reduce_sum(tf.squared_difference(targets, pred_outputs[-1]), axis=-1)
    last_pred_mse = tf.metrics.mean_absolute_error(sq_diff, tf.zeros_like(sq_diff), name='last_pred_mse')
    metrics = {'normalized_error': ne_mertric, 'last_pred_mse': last_pred_mse}
    predictions = {'normalized_error': ne_mertric[1]}
    ne_mertric = tf.identity(ne_mertric[1], name='ne_mertric')
    base_learning_rate = params['learning_rate']
    mse_loss_list = []
    if params['use_ohkm']:
        base_learning_rate = 1.5 * base_learning_rate
        for pred_ind in list(range(len(pred_outputs) - 1)):
            mse_loss_list.append(0.6 * tf.losses.mean_squared_error(targets, pred_outputs[pred_ind], weights=1.0 / tf.cast(cur_batch_size, tf.float32), scope='loss_{}'.format(pred_ind), loss_collection=None, reduction=tf.losses.Reduction.MEAN))
        temp_loss = tf.reduce_mean(tf.reshape(tf.losses.mean_squared_error(targets, pred_outputs[-1], weights=1.0, loss_collection=None, reduction=tf.losses.Reduction.NONE), [cur_batch_size, config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], -1]), axis=-1)
        num_topk = config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'] // 2
        gather_col = tf.nn.top_k(temp_loss, k=num_topk, sorted=True)[1]
        gather_row = tf.reshape(tf.tile(tf.reshape(tf.range(cur_batch_size), [-1, 1]), [1, num_topk]), [-1, 1])
        gather_indcies = tf.stop_gradient(tf.stack([gather_row, tf.reshape(gather_col, [-1, 1])], axis=-1))
        select_targets = tf.gather_nd(targets, gather_indcies)
        select_heatmap = tf.gather_nd(pred_outputs[-1], gather_indcies)
        mse_loss_list.append(tf.losses.mean_squared_error(select_targets, select_heatmap, weights=1.0 / tf.cast(cur_batch_size, tf.float32), scope='loss_{}'.format(len(pred_outputs) - 1), loss_collection=None, reduction=tf.losses.Reduction.MEAN))
    else:
        for pred_ind in list(range(len(pred_outputs))):
            mse_loss_list.append(tf.losses.mean_squared_error(targets, pred_outputs[pred_ind], weights=1.0 / tf.cast(cur_batch_size, tf.float32), scope='loss_{}'.format(pred_ind), loss_collection=None, reduction=tf.losses.Reduction.MEAN))
    mse_loss = tf.multiply(params['mse_weight'], tf.add_n(mse_loss_list), name='mse_loss')
    tf.summary.scalar('mse', mse_loss)
    tf.losses.add_loss(mse_loss)
    loss = mse_loss + params['weight_decay'] * tf.add_n([tf.nn.l2_loss(v) for v in tf.trainable_variables() if 'batch_normalization' not in v.name])
    total_loss = tf.identity(loss, name='total_loss')
    tf.summary.scalar('loss', total_loss)
    if mode == tf.estimator.ModeKeys.EVAL:
        return tf.estimator.EstimatorSpec(mode=mode, loss=loss, predictions=predictions, eval_metric_ops=metrics)
    if mode == tf.estimator.ModeKeys.TRAIN:
        global_step = tf.train.get_or_create_global_step()
        lr_values = [params['warmup_learning_rate']] + [base_learning_rate * decay for decay in params['lr_decay_factors']]
        learning_rate = tf.train.piecewise_constant(tf.cast(global_step, tf.int32), [params['warmup_steps']] + [int(float(ep) * params['steps_per_epoch']) for ep in params['decay_boundaries']], lr_values)
        truncated_learning_rate = tf.maximum(learning_rate, tf.constant(params['end_learning_rate'], dtype=learning_rate.dtype), name='learning_rate')
        tf.summary.scalar('lr', truncated_learning_rate)
        optimizer = tf.train.MomentumOptimizer(learning_rate=truncated_learning_rate, momentum=params['momentum'])
        update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
        with tf.control_dependencies(update_ops):
            train_op = optimizer.minimize(loss, global_step)
    else:
        train_op = None
    return tf.estimator.EstimatorSpec(mode=mode, predictions=predictions, loss=loss, train_op=train_op, eval_metric_ops=metrics, scaffold=tf.train.Scaffold(init_fn=train_helper.get_init_fn_for_scaffold_(params['checkpoint_path'], params['model_dir'], params['checkpoint_exclude_scopes'], params['model_scope'], params['checkpoint_model_scope'], params['ignore_missing_vars'])))

def get_keypoint(image, targets, predictions, heatmap_size, height, width, category, clip_at_zero=True, data_format='channels_last', name=None):
    predictions = tf.reshape(predictions, [1, -1, heatmap_size * heatmap_size])
    pred_max = tf.reduce_max(predictions, axis=-1)
    pred_indices = tf.argmax(predictions, axis=-1)
    pred_x, pred_y = (tf.cast(tf.floormod(pred_indices, heatmap_size), tf.float32), tf.cast(tf.floordiv(pred_indices, heatmap_size), tf.float32))
    width, height = (tf.cast(width, tf.float32), tf.cast(height, tf.float32))
    pred_x, pred_y = (pred_x * width / tf.cast(heatmap_size, tf.float32), pred_y * height / tf.cast(heatmap_size, tf.float32))
    if clip_at_zero:
        pred_x, pred_y = (pred_x * tf.cast(pred_max > 0, tf.float32), pred_y * tf.cast(pred_max > 0, tf.float32))
        pred_x = pred_x * tf.cast(pred_max > 0, tf.float32) + tf.cast(pred_max <= 0, tf.float32) * (width / 2.0)
        pred_y = pred_y * tf.cast(pred_max > 0, tf.float32) + tf.cast(pred_max <= 0, tf.float32) * (height / 2.0)
    if config.PRED_DEBUG:
        pred_indices_ = tf.squeeze(pred_indices)
        image_ = tf.squeeze(image) * 255.0
        pred_heatmap = tf.one_hot(pred_indices_, heatmap_size * heatmap_size, on_value=1.0, off_value=0.0, axis=-1, dtype=tf.float32)
        pred_heatmap = tf.reshape(pred_heatmap, [-1, heatmap_size, heatmap_size])
        if data_format == 'channels_first':
            image_ = tf.transpose(image_, perm=(1, 2, 0))
        save_image_op = tf.py_func(save_image_with_heatmap, [image_, height, width, heatmap_size, tf.reshape(pred_heatmap * 255.0, [-1, heatmap_size, heatmap_size]), tf.reshape(predictions, [-1, heatmap_size, heatmap_size]), config.left_right_group_map[category][0], config.left_right_group_map[category][1], config.left_right_group_map[category][2]], tf.int64, stateful=True)
        with tf.control_dependencies([save_image_op]):
            pred_x, pred_y = (pred_x * 1.0, pred_y * 1.0)
    return (pred_x, pred_y)

def keypoint_model_fn(features, labels, mode, params):
    targets = labels['targets']
    shape = labels['shape']
    classid = labels['classid']
    key_v = labels['key_v']
    isvalid = labels['isvalid']
    norm_value = labels['norm_value']
    cur_batch_size = tf.shape(features)[0]
    with tf.variable_scope(params['model_scope'], default_name=None, values=[features], reuse=tf.AUTO_REUSE):
        pred_outputs = cpn.cascaded_pyramid_net(features, config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], params['heatmap_size'], mode == tf.estimator.ModeKeys.TRAIN, params['data_format'])
    if params['data_format'] == 'channels_last':
        pred_outputs = [tf.transpose(pred_outputs[ind], [0, 3, 1, 2], name='outputs_trans_{}'.format(ind)) for ind in list(range(len(pred_outputs)))]
    score_map = pred_outputs[-1]
    pred_x, pred_y = get_keypoint(features, targets, score_map, params['heatmap_size'], params['train_image_size'], params['train_image_size'], params['model_scope'] if 'all' not in params['model_scope'] else '*', clip_at_zero=True, data_format=params['data_format'])
    targets = 255.0 * targets
    blur_list = [1.0, 1.37, 1.73, 2.4, None]
    targets_list = []
    for sigma in blur_list:
        if sigma is None:
            targets_list.append(targets)
        else:
            targets_list.append(gaussian_blur(targets, config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], sigma, params['data_format'], 'blur_{}'.format(sigma)))
    ne_mertric = mertric.normalized_error(targets, score_map, norm_value, key_v, isvalid, cur_batch_size, config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], params['heatmap_size'], params['train_image_size'])
    all_visible = tf.expand_dims(tf.expand_dims(tf.cast(tf.logical_and(key_v > 0, isvalid > 0), tf.float32), axis=-1), axis=-1)
    targets_list = [targets_list[ind] * all_visible for ind in list(range(len(targets_list)))]
    pred_outputs = [pred_outputs[ind] * all_visible for ind in list(range(len(pred_outputs)))]
    sq_diff = tf.reduce_sum(tf.squared_difference(targets, pred_outputs[-1]), axis=-1)
    last_pred_mse = tf.metrics.mean_absolute_error(sq_diff, tf.zeros_like(sq_diff), name='last_pred_mse')
    metrics = {'normalized_error': ne_mertric, 'last_pred_mse': last_pred_mse}
    predictions = {'normalized_error': ne_mertric[1]}
    ne_mertric = tf.identity(ne_mertric[1], name='ne_mertric')
    base_learning_rate = params['learning_rate']
    mse_loss_list = []
    if params['use_ohkm']:
        base_learning_rate = 1.0 * base_learning_rate
        for pred_ind in list(range(len(pred_outputs) - 1)):
            mse_loss_list.append(0.5 * tf.losses.mean_squared_error(targets_list[pred_ind], pred_outputs[pred_ind], weights=1.0 / tf.cast(cur_batch_size, tf.float32), scope='loss_{}'.format(pred_ind), loss_collection=None, reduction=tf.losses.Reduction.MEAN))
        temp_loss = tf.reduce_mean(tf.reshape(tf.losses.mean_squared_error(targets_list[-1], pred_outputs[-1], weights=1.0, loss_collection=None, reduction=tf.losses.Reduction.NONE), [cur_batch_size, config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], -1]), axis=-1)
        num_topk = config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'] // 2
        gather_col = tf.nn.top_k(temp_loss, k=num_topk, sorted=True)[1]
        gather_row = tf.reshape(tf.tile(tf.reshape(tf.range(cur_batch_size), [-1, 1]), [1, num_topk]), [-1, 1])
        gather_indcies = tf.stop_gradient(tf.stack([gather_row, tf.reshape(gather_col, [-1, 1])], axis=-1))
        select_targets = tf.gather_nd(targets_list[-1], gather_indcies)
        select_heatmap = tf.gather_nd(pred_outputs[-1], gather_indcies)
        mse_loss_list.append(tf.losses.mean_squared_error(select_targets, select_heatmap, weights=1.0 / tf.cast(cur_batch_size, tf.float32), scope='loss_{}'.format(len(pred_outputs) - 1), loss_collection=None, reduction=tf.losses.Reduction.MEAN))
    else:
        for pred_ind in list(range(len(pred_outputs))):
            mse_loss_list.append(tf.losses.mean_squared_error(targets_list[pred_ind], pred_outputs[pred_ind], weights=1.0 / tf.cast(cur_batch_size, tf.float32), scope='loss_{}'.format(pred_ind), loss_collection=None, reduction=tf.losses.Reduction.MEAN))
    mse_loss = tf.multiply(params['mse_weight'], tf.add_n(mse_loss_list), name='mse_loss')
    tf.summary.scalar('mse', mse_loss)
    tf.losses.add_loss(mse_loss)
    loss = mse_loss + params['weight_decay'] * tf.add_n([tf.nn.l2_loss(v) for v in tf.trainable_variables() if 'batch_normalization' not in v.name])
    total_loss = tf.identity(loss, name='total_loss')
    tf.summary.scalar('loss', total_loss)
    if mode == tf.estimator.ModeKeys.EVAL:
        return tf.estimator.EstimatorSpec(mode=mode, loss=loss, predictions=predictions, eval_metric_ops=metrics)
    if mode == tf.estimator.ModeKeys.TRAIN:
        global_step = tf.train.get_or_create_global_step()
        lr_values = [params['warmup_learning_rate']] + [base_learning_rate * decay for decay in params['lr_decay_factors']]
        learning_rate = tf.train.piecewise_constant(tf.cast(global_step, tf.int32), [params['warmup_steps']] + [int(float(ep) * params['steps_per_epoch']) for ep in params['decay_boundaries']], lr_values)
        truncated_learning_rate = tf.maximum(learning_rate, tf.constant(params['end_learning_rate'], dtype=learning_rate.dtype), name='learning_rate')
        tf.summary.scalar('lr', truncated_learning_rate)
        optimizer = tf.train.MomentumOptimizer(learning_rate=truncated_learning_rate, momentum=params['momentum'])
        update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
        with tf.control_dependencies(update_ops):
            train_op = optimizer.minimize(loss, global_step)
    else:
        train_op = None
    return tf.estimator.EstimatorSpec(mode=mode, predictions=predictions, loss=loss, train_op=train_op, eval_metric_ops=metrics, scaffold=tf.train.Scaffold(init_fn=train_helper.get_init_fn_for_scaffold_(params['checkpoint_path'], params['model_dir'], params['checkpoint_exclude_scopes'], params['model_scope'], params['checkpoint_model_scope'], params['ignore_missing_vars'])))

def get_keypoint(image, targets, predictions, heatmap_size, height, width, category, clip_at_zero=True, data_format='channels_last', name=None):
    predictions = tf.reshape(predictions, [1, -1, heatmap_size * heatmap_size])
    pred_max = tf.reduce_max(predictions, axis=-1)
    pred_indices = tf.argmax(predictions, axis=-1)
    pred_x, pred_y = (tf.cast(tf.floormod(pred_indices, heatmap_size), tf.float32), tf.cast(tf.floordiv(pred_indices, heatmap_size), tf.float32))
    width, height = (tf.cast(width, tf.float32), tf.cast(height, tf.float32))
    pred_x, pred_y = (pred_x * width / tf.cast(heatmap_size, tf.float32), pred_y * height / tf.cast(heatmap_size, tf.float32))
    if clip_at_zero:
        pred_x, pred_y = (pred_x * tf.cast(pred_max > 0, tf.float32), pred_y * tf.cast(pred_max > 0, tf.float32))
        pred_x = pred_x * tf.cast(pred_max > 0, tf.float32) + tf.cast(pred_max <= 0, tf.float32) * (width / 2.0)
        pred_y = pred_y * tf.cast(pred_max > 0, tf.float32) + tf.cast(pred_max <= 0, tf.float32) * (height / 2.0)
    if config.PRED_DEBUG:
        pred_indices_ = tf.squeeze(pred_indices)
        image_ = tf.squeeze(image) * 255.0
        pred_heatmap = tf.one_hot(pred_indices_, heatmap_size * heatmap_size, on_value=255, off_value=0, axis=-1, dtype=tf.int32)
        pred_heatmap = tf.reshape(pred_heatmap, [-1, heatmap_size, heatmap_size])
        if data_format == 'channels_first':
            image_ = tf.transpose(image_, perm=(1, 2, 0))
        save_image_op = tf.py_func(save_image_with_heatmap, [image_, height, width, heatmap_size, tf.reshape(targets * 255.0, [-1, heatmap_size, heatmap_size]), tf.reshape(predictions, [-1, heatmap_size, heatmap_size]), config.left_right_group_map[category][0], config.left_right_group_map[category][1], config.left_right_group_map[category][2]], tf.int64, stateful=True)
        with tf.control_dependencies([save_image_op]):
            pred_x, pred_y = (pred_x * 1.0, pred_y * 1.0)
    return (pred_x, pred_y)

def keypoint_model_fn(features, labels, mode, params):
    targets = labels['targets']
    shape = labels['shape']
    classid = labels['classid']
    key_v = labels['key_v']
    isvalid = labels['isvalid']
    norm_value = labels['norm_value']
    cur_batch_size = tf.shape(features)[0]
    with tf.variable_scope(params['model_scope'], default_name=None, values=[features], reuse=tf.AUTO_REUSE):
        pred_outputs = hg.create_model(features, params['num_stacks'], params['feats_channals'], config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], params['num_modules'], mode == tf.estimator.ModeKeys.TRAIN, params['data_format'])
    if params['data_format'] == 'channels_last':
        pred_outputs = [tf.transpose(pred_outputs[ind], [0, 3, 1, 2], name='outputs_trans_{}'.format(ind)) for ind in list(range(len(pred_outputs)))]
    score_map = pred_outputs[-1]
    pred_x, pred_y = get_keypoint(features, targets, score_map, params['heatmap_size'], params['train_image_size'], params['train_image_size'], params['model_scope'] if 'all' not in params['model_scope'] else '*', clip_at_zero=True, data_format=params['data_format'])
    targets = 255.0 * targets
    ne_mertric = mertric.normalized_error(targets, score_map, norm_value, key_v, isvalid, cur_batch_size, config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], params['heatmap_size'], params['train_image_size'])
    all_visible = tf.logical_and(key_v > 0, isvalid > 0)
    targets = tf.boolean_mask(targets, all_visible)
    pred_outputs = [tf.boolean_mask(pred_outputs[ind], all_visible, name='boolean_mask_{}'.format(ind)) for ind in list(range(len(pred_outputs)))]
    sq_diff = tf.reduce_sum(tf.squared_difference(targets, pred_outputs[-1]), axis=-1)
    last_pred_mse = tf.metrics.mean_absolute_error(sq_diff, tf.zeros_like(sq_diff), name='last_pred_mse')
    metrics = {'normalized_error': ne_mertric, 'last_pred_mse': last_pred_mse}
    predictions = {'normalized_error': ne_mertric[1]}
    ne_mertric = tf.identity(ne_mertric[1], name='ne_mertric')
    mse_loss_list = []
    for pred_ind in list(range(len(pred_outputs))):
        mse_loss_list.append(tf.losses.mean_squared_error(targets, pred_outputs[pred_ind], weights=1.0 / tf.cast(cur_batch_size, tf.float32), scope='loss_{}'.format(pred_ind), loss_collection=None, reduction=tf.losses.Reduction.MEAN))
    mse_loss = tf.multiply(params['mse_weight'], tf.add_n(mse_loss_list), name='mse_loss')
    tf.summary.scalar('mse', mse_loss)
    tf.losses.add_loss(mse_loss)
    loss = mse_loss + params['weight_decay'] * tf.add_n([tf.nn.l2_loss(v) for v in tf.trainable_variables() if 'batch_normalization' not in v.name])
    total_loss = tf.identity(loss, name='total_loss')
    tf.summary.scalar('loss', total_loss)
    if mode == tf.estimator.ModeKeys.EVAL:
        return tf.estimator.EstimatorSpec(mode=mode, loss=loss, predictions=predictions, eval_metric_ops=metrics)
    if mode == tf.estimator.ModeKeys.TRAIN:
        global_step = tf.train.get_or_create_global_step()
        lr_values = [params['warmup_learning_rate']] + [params['learning_rate'] * decay for decay in params['lr_decay_factors']]
        learning_rate = tf.train.piecewise_constant(tf.cast(global_step, tf.int32), [params['warmup_steps']] + [int(float(ep) * params['steps_per_epoch']) for ep in params['decay_boundaries']], lr_values)
        truncated_learning_rate = tf.maximum(learning_rate, tf.constant(params['end_learning_rate'], dtype=learning_rate.dtype), name='learning_rate')
        tf.summary.scalar('lr', truncated_learning_rate)
        optimizer = tf.train.MomentumOptimizer(learning_rate=truncated_learning_rate, momentum=params['momentum'])
        update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
        with tf.control_dependencies(update_ops):
            train_op = optimizer.minimize(loss, global_step)
    else:
        train_op = None
    return tf.estimator.EstimatorSpec(mode=mode, predictions=predictions, loss=loss, train_op=train_op, eval_metric_ops=metrics, scaffold=tf.train.Scaffold(init_fn=train_helper.get_init_fn_for_scaffold(FLAGS)))

def get_keypoint(image, targets, predictions, heatmap_size, height, width, category, clip_at_zero=True, data_format='channels_last', name=None):
    predictions = tf.reshape(predictions, [1, -1, heatmap_size * heatmap_size])
    pred_max = tf.reduce_max(predictions, axis=-1)
    pred_indices = tf.argmax(predictions, axis=-1)
    pred_x, pred_y = (tf.cast(tf.floormod(pred_indices, heatmap_size), tf.float32), tf.cast(tf.floordiv(pred_indices, heatmap_size), tf.float32))
    width, height = (tf.cast(width, tf.float32), tf.cast(height, tf.float32))
    pred_x, pred_y = (pred_x * width / tf.cast(heatmap_size, tf.float32), pred_y * height / tf.cast(heatmap_size, tf.float32))
    if clip_at_zero:
        pred_x, pred_y = (pred_x * tf.cast(pred_max > 0, tf.float32), pred_y * tf.cast(pred_max > 0, tf.float32))
        pred_x = pred_x * tf.cast(pred_max > 0, tf.float32) + tf.cast(pred_max <= 0, tf.float32) * (width / 2.0)
        pred_y = pred_y * tf.cast(pred_max > 0, tf.float32) + tf.cast(pred_max <= 0, tf.float32) * (height / 2.0)
    if config.PRED_DEBUG:
        pred_indices_ = tf.squeeze(pred_indices)
        image_ = tf.squeeze(image) * 255.0
        pred_heatmap = tf.one_hot(pred_indices_, heatmap_size * heatmap_size, on_value=1.0, off_value=0.0, axis=-1, dtype=tf.float32)
        pred_heatmap = tf.reshape(pred_heatmap, [-1, heatmap_size, heatmap_size])
        if data_format == 'channels_first':
            image_ = tf.transpose(image_, perm=(1, 2, 0))
        save_image_op = tf.py_func(save_image_with_heatmap, [image_, height, width, heatmap_size, tf.reshape(pred_heatmap * 255.0, [-1, heatmap_size, heatmap_size]), tf.reshape(predictions, [-1, heatmap_size, heatmap_size]), config.left_right_group_map[category][0], config.left_right_group_map[category][1], config.left_right_group_map[category][2]], tf.int64, stateful=True)
        with tf.control_dependencies([save_image_op]):
            pred_x, pred_y = (pred_x * 1.0, pred_y * 1.0)
    return (pred_x, pred_y)

def keypoint_model_fn(features, labels, mode, params):
    targets = labels['targets']
    shape = labels['shape']
    classid = labels['classid']
    key_v = labels['key_v']
    isvalid = labels['isvalid']
    norm_value = labels['norm_value']
    cur_batch_size = tf.shape(features)[0]
    with tf.variable_scope(params['model_scope'], default_name=None, values=[features], reuse=tf.AUTO_REUSE):
        pred_outputs = cpn_backbone(features, config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], params['heatmap_size'], mode == tf.estimator.ModeKeys.TRAIN, params['data_format'])
    if params['data_format'] == 'channels_last':
        pred_outputs = [tf.transpose(pred_outputs[ind], [0, 3, 1, 2], name='outputs_trans_{}'.format(ind)) for ind in list(range(len(pred_outputs)))]
    score_map = pred_outputs[-1]
    pred_x, pred_y = get_keypoint(features, targets, score_map, params['heatmap_size'], params['train_image_size'], params['train_image_size'], params['model_scope'] if 'all' not in params['model_scope'] else '*', clip_at_zero=True, data_format=params['data_format'])
    targets = 255.0 * targets
    blur_list = [1.0, 1.37, 1.73, 2.4, None]
    targets_list = []
    for sigma in blur_list:
        if sigma is None:
            targets_list.append(targets)
        else:
            targets_list.append(gaussian_blur(targets, config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], sigma, params['data_format'], 'blur_{}'.format(sigma)))
    ne_mertric = mertric.normalized_error(targets, score_map, norm_value, key_v, isvalid, cur_batch_size, config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], params['heatmap_size'], params['train_image_size'])
    all_visible = tf.expand_dims(tf.expand_dims(tf.cast(tf.logical_and(key_v > 0, isvalid > 0), tf.float32), axis=-1), axis=-1)
    targets_list = [targets_list[ind] * all_visible for ind in list(range(len(targets_list)))]
    pred_outputs = [pred_outputs[ind] * all_visible for ind in list(range(len(pred_outputs)))]
    sq_diff = tf.reduce_sum(tf.squared_difference(targets, pred_outputs[-1]), axis=-1)
    last_pred_mse = tf.metrics.mean_absolute_error(sq_diff, tf.zeros_like(sq_diff), name='last_pred_mse')
    metrics = {'normalized_error': ne_mertric, 'last_pred_mse': last_pred_mse}
    predictions = {'normalized_error': ne_mertric[1]}
    ne_mertric = tf.identity(ne_mertric[1], name='ne_mertric')
    base_learning_rate = params['learning_rate']
    mse_loss_list = []
    if params['use_ohkm']:
        base_learning_rate = 1.0 * base_learning_rate
        for pred_ind in list(range(len(pred_outputs) - 1)):
            mse_loss_list.append(0.5 * tf.losses.mean_squared_error(targets_list[pred_ind], pred_outputs[pred_ind], weights=1.0 / tf.cast(cur_batch_size, tf.float32), scope='loss_{}'.format(pred_ind), loss_collection=None, reduction=tf.losses.Reduction.MEAN))
        temp_loss = tf.reduce_mean(tf.reshape(tf.losses.mean_squared_error(targets_list[-1], pred_outputs[-1], weights=1.0, loss_collection=None, reduction=tf.losses.Reduction.NONE), [cur_batch_size, config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], -1]), axis=-1)
        num_topk = config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'] // 2
        gather_col = tf.nn.top_k(temp_loss, k=num_topk, sorted=True)[1]
        gather_row = tf.reshape(tf.tile(tf.reshape(tf.range(cur_batch_size), [-1, 1]), [1, num_topk]), [-1, 1])
        gather_indcies = tf.stop_gradient(tf.stack([gather_row, tf.reshape(gather_col, [-1, 1])], axis=-1))
        select_targets = tf.gather_nd(targets_list[-1], gather_indcies)
        select_heatmap = tf.gather_nd(pred_outputs[-1], gather_indcies)
        mse_loss_list.append(tf.losses.mean_squared_error(select_targets, select_heatmap, weights=1.0 / tf.cast(cur_batch_size, tf.float32), scope='loss_{}'.format(len(pred_outputs) - 1), loss_collection=None, reduction=tf.losses.Reduction.MEAN))
    else:
        for pred_ind in list(range(len(pred_outputs))):
            mse_loss_list.append(tf.losses.mean_squared_error(targets_list[pred_ind], pred_outputs[pred_ind], weights=1.0 / tf.cast(cur_batch_size, tf.float32), scope='loss_{}'.format(pred_ind), loss_collection=None, reduction=tf.losses.Reduction.MEAN))
    mse_loss = tf.multiply(params['mse_weight'], tf.add_n(mse_loss_list), name='mse_loss')
    tf.summary.scalar('mse', mse_loss)
    tf.losses.add_loss(mse_loss)
    loss = mse_loss + params['weight_decay'] * tf.add_n([tf.nn.l2_loss(v) for v in tf.trainable_variables() if 'batch_normalization' not in v.name])
    total_loss = tf.identity(loss, name='total_loss')
    tf.summary.scalar('loss', total_loss)
    if mode == tf.estimator.ModeKeys.EVAL:
        return tf.estimator.EstimatorSpec(mode=mode, loss=loss, predictions=predictions, eval_metric_ops=metrics)
    if mode == tf.estimator.ModeKeys.TRAIN:
        global_step = tf.train.get_or_create_global_step()
        lr_values = [params['warmup_learning_rate']] + [base_learning_rate * decay for decay in params['lr_decay_factors']]
        learning_rate = tf.train.piecewise_constant(tf.cast(global_step, tf.int32), [params['warmup_steps']] + [int(float(ep) * params['steps_per_epoch']) for ep in params['decay_boundaries']], lr_values)
        truncated_learning_rate = tf.maximum(learning_rate, tf.constant(params['end_learning_rate'], dtype=learning_rate.dtype), name='learning_rate')
        tf.summary.scalar('lr', truncated_learning_rate)
        optimizer = tf.train.MomentumOptimizer(learning_rate=truncated_learning_rate, momentum=params['momentum'])
        update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
        with tf.control_dependencies(update_ops):
            train_op = optimizer.minimize(loss, global_step)
    else:
        train_op = None
    return tf.estimator.EstimatorSpec(mode=mode, predictions=predictions, loss=loss, train_op=train_op, eval_metric_ops=metrics, scaffold=tf.train.Scaffold(init_fn=train_helper.get_init_fn_for_scaffold_(params['checkpoint_path'], params['model_dir'], params['checkpoint_exclude_scopes'], params['model_scope'], params['checkpoint_model_scope'], params['ignore_missing_vars'])))

def get_keypoint(image, predictions, heatmap_size, height, width, category, clip_at_zero=True, data_format='channels_last', name=None):
    predictions = tf.reshape(predictions, [1, -1, heatmap_size * heatmap_size])
    pred_max = tf.reduce_max(predictions, axis=-1)
    pred_max_indices = tf.argmax(predictions, axis=-1)
    pred_max_x, pred_max_y = (tf.cast(tf.floormod(pred_max_indices, heatmap_size), tf.float32), tf.cast(tf.floordiv(pred_max_indices, heatmap_size), tf.float32))
    mask_predictions = predictions * tf.one_hot(pred_max_indices, heatmap_size * heatmap_size, on_value=0.0, off_value=1.0, dtype=tf.float32)
    pred_next_max = tf.reduce_max(mask_predictions, axis=-1)
    pred_next_max_indices = tf.argmax(mask_predictions, axis=-1)
    pred_next_max_x, pred_next_max_y = (tf.cast(tf.floormod(pred_next_max_indices, heatmap_size), tf.float32), tf.cast(tf.floordiv(pred_next_max_indices, heatmap_size), tf.float32))
    dist = tf.pow(tf.pow(pred_next_max_x - pred_max_x, 2.0) + tf.pow(pred_next_max_y - pred_max_y, 2.0), 0.5)
    pred_x = tf.where(dist < 0.001, pred_max_x, pred_max_x + (pred_next_max_x - pred_max_x) * 0.25 / dist)
    pred_y = tf.where(dist < 0.001, pred_max_y, pred_max_y + (pred_next_max_y - pred_max_y) * 0.25 / dist)
    pred_indices_ = tf.squeeze(tf.cast(pred_x, tf.int64) + tf.cast(pred_y, tf.int64) * heatmap_size)
    width, height = (tf.cast(width, tf.float32), tf.cast(height, tf.float32))
    width_ratio, height_ratio = (width / tf.cast(heatmap_size, tf.float32), height / tf.cast(heatmap_size, tf.float32))
    pred_x, pred_y = (pred_x * width_ratio, pred_y * height_ratio)
    if clip_at_zero:
        pred_x, pred_y = (pred_x * tf.cast(pred_max > 0, tf.float32), pred_y * tf.cast(pred_max > 0, tf.float32))
        pred_x = pred_x * tf.cast(pred_max > 0, tf.float32) + tf.cast(pred_max <= 0, tf.float32) * (width / 2.0)
        pred_y = pred_y * tf.cast(pred_max > 0, tf.float32) + tf.cast(pred_max <= 0, tf.float32) * (height / 2.0)
    if config.PRED_DEBUG:
        image_ = tf.squeeze(image) * 255.0
        pred_heatmap = tf.one_hot(pred_indices_, heatmap_size * heatmap_size, on_value=255, off_value=0, axis=-1, dtype=tf.int32)
        pred_heatmap = tf.reshape(pred_heatmap, [-1, heatmap_size, heatmap_size])
        if data_format == 'channels_first':
            image_ = tf.transpose(image_, perm=(1, 2, 0))
        save_image_op = tf.py_func(save_image_with_heatmap, [image_, height, width, heatmap_size, pred_heatmap, tf.reshape(predictions, [-1, heatmap_size, heatmap_size]), config.left_right_group_map[category][0], config.left_right_group_map[category][1], config.left_right_group_map[category][2]], tf.int64, stateful=True)
        with tf.control_dependencies([save_image_op]):
            pred_x, pred_y = (pred_x * 1.0, pred_y * 1.0)
    return (pred_x, pred_y)

def get_keypoint_v0(image, predictions, heatmap_size, height, width, category, clip_at_zero=True, data_format='channels_last', name=None):
    predictions = tf.reshape(predictions, [1, -1, heatmap_size * heatmap_size])
    pred_max = tf.reduce_max(predictions, axis=-1)
    pred_indices = tf.argmax(predictions, axis=-1)
    pred_x, pred_y = (tf.cast(tf.floormod(pred_indices, heatmap_size), tf.float32), tf.cast(tf.floordiv(pred_indices, heatmap_size), tf.float32))
    width, height = (tf.cast(width, tf.float32), tf.cast(height, tf.float32))
    pred_x, pred_y = (pred_x * width / tf.cast(heatmap_size, tf.float32), pred_y * height / tf.cast(heatmap_size, tf.float32))
    if clip_at_zero:
        pred_x, pred_y = (pred_x * tf.cast(pred_max > 0, tf.float32), pred_y * tf.cast(pred_max > 0, tf.float32))
        pred_x = pred_x * tf.cast(pred_max > 0, tf.float32) + tf.cast(pred_max <= 0, tf.float32) * (width / 2.0)
        pred_y = pred_y * tf.cast(pred_max > 0, tf.float32) + tf.cast(pred_max <= 0, tf.float32) * (height / 2.0)
    if config.PRED_DEBUG:
        pred_indices_ = tf.squeeze(pred_indices)
        image_ = tf.squeeze(image) * 255.0
        pred_heatmap = tf.one_hot(pred_indices_, heatmap_size * heatmap_size, on_value=255, off_value=0, axis=-1, dtype=tf.int32)
        pred_heatmap = tf.reshape(pred_heatmap, [-1, heatmap_size, heatmap_size])
        if data_format == 'channels_first':
            image_ = tf.transpose(image_, perm=(1, 2, 0))
        save_image_op = tf.py_func(save_image_with_heatmap, [image_, height, width, heatmap_size, pred_heatmap, tf.reshape(predictions, [-1, heatmap_size, heatmap_size]), config.left_right_group_map[category][0], config.left_right_group_map[category][1], config.left_right_group_map[category][2]], tf.int64, stateful=True)
        with tf.control_dependencies([save_image_op]):
            pred_x, pred_y = (pred_x * 1.0, pred_y * 1.0)
    return (pred_x, pred_y)

def keypoint_model_fn(features, labels, mode, params):
    shape = features['shape']
    classid = features['classid']
    pred_offsets = tf.to_float(features['pred_offsets'])
    file_name = features['file_name']
    features = features['images']
    file_name = tf.identity(file_name, name='current_file')
    image = preprocessing.preprocess_for_test_raw_output(features, params['train_image_size'], params['train_image_size'], data_format='NCHW' if FLAGS.data_format == 'channels_first' else 'NHWC', scope='first_stage')
    if not params['flip_on_test']:
        with tf.variable_scope(params['model_scope'], default_name=None, values=[image], reuse=tf.AUTO_REUSE):
            pred_outputs = hg.create_model(image, params['num_stacks'], params['feats_channals'], config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], params['num_modules'], mode == tf.estimator.ModeKeys.TRAIN, params['data_format'])
        if params['data_format'] == 'channels_last':
            pred_outputs = [tf.transpose(pred_outputs[ind], [0, 3, 1, 2], name='outputs_trans_{}'.format(ind)) for ind in list(range(len(pred_outputs)))]
        pred_x_first_stage, pred_y_first_stage = get_keypoint(image, pred_outputs[-1], params['heatmap_size'], shape[0][0], shape[0][1], params['model_scope'] if 'all' not in params['model_scope'] else '*', clip_at_zero=True, data_format=params['data_format'])
    else:
        if params['data_format'] == 'channels_last':
            double_features = tf.reshape(tf.stack([image, tf.map_fn(tf.image.flip_left_right, image, back_prop=False)], axis=1), [-1, params['train_image_size'], params['train_image_size'], 3])
        else:
            double_features = tf.reshape(tf.stack([image, tf.transpose(tf.map_fn(tf.image.flip_left_right, tf.transpose(image, [0, 2, 3, 1], name='nchw2nhwc'), back_prop=False), [0, 3, 1, 2], name='nhwc2nchw')], axis=1), [-1, 3, params['train_image_size'], params['train_image_size']])
        num_joints = config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*']
        with tf.variable_scope(params['model_scope'], default_name=None, values=[double_features], reuse=tf.AUTO_REUSE):
            pred_outputs = hg.create_model(double_features, params['num_stacks'], params['feats_channals'], config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], params['num_modules'], mode == tf.estimator.ModeKeys.TRAIN, params['data_format'])
        if params['data_format'] == 'channels_last':
            pred_outputs = [tf.transpose(pred_outputs[ind], [0, 3, 1, 2], name='outputs_trans_{}'.format(ind)) for ind in list(range(len(pred_outputs)))]
        row_indices = tf.tile(tf.reshape(tf.stack([tf.range(0, tf.shape(double_features)[0], delta=2), tf.range(1, tf.shape(double_features)[0], delta=2)], axis=0), [-1, 1]), [1, num_joints])
        col_indices = tf.reshape(tf.tile(tf.reshape(tf.stack([tf.range(num_joints), tf.constant(config.left_right_remap[params['model_scope'] if 'all' not in params['model_scope'] else '*'])], axis=0), [2, -1]), [1, tf.shape(features)[0]]), [-1, num_joints])
        flip_indices = tf.stack([row_indices, col_indices], axis=-1)
        pred_outputs = [tf.gather_nd(pred_outputs[ind], flip_indices, name='gather_nd_{}'.format(ind)) for ind in list(range(len(pred_outputs)))]

        def cond_flip(heatmap_ind):
            return tf.cond(heatmap_ind[1] < tf.shape(features)[0], lambda: heatmap_ind[0], lambda: tf.transpose(tf.image.flip_left_right(tf.transpose(heatmap_ind[0], [1, 2, 0], name='pred_nchw2nhwc')), [2, 0, 1], name='pred_nhwc2nchw'))
        pred_outputs = [tf.map_fn(cond_flip, [pred_outputs[ind], tf.range(tf.shape(double_features)[0])], dtype=tf.float32, parallel_iterations=10, back_prop=True, swap_memory=False, infer_shape=True, name='map_fn_{}'.format(ind)) for ind in list(range(len(pred_outputs)))]
        pred_outputs = [tf.split(_, 2) for _ in pred_outputs]
        pred_outputs_1 = [_[0] for _ in pred_outputs]
        pred_outputs_2 = [_[1] for _ in pred_outputs]
        pred_x_first_stage1, pred_y_first_stage1 = get_keypoint(image, pred_outputs_1[-1], params['heatmap_size'], shape[0][0], shape[0][1], params['model_scope'] if 'all' not in params['model_scope'] else '*', clip_at_zero=True, data_format=params['data_format'])
        pred_x_first_stage2, pred_y_first_stage2 = get_keypoint(image, pred_outputs_2[-1], params['heatmap_size'], shape[0][0], shape[0][1], params['model_scope'] if 'all' not in params['model_scope'] else '*', clip_at_zero=True, data_format=params['data_format'])
        dist = tf.pow(tf.pow(pred_x_first_stage1 - pred_x_first_stage2, 2.0) + tf.pow(pred_y_first_stage1 - pred_y_first_stage2, 2.0), 0.5)
        pred_x_first_stage = tf.where(dist < 0.001, pred_x_first_stage1, pred_x_first_stage1 + (pred_x_first_stage2 - pred_x_first_stage1) * 0.25 / dist)
        pred_y_first_stage = tf.where(dist < 0.001, pred_y_first_stage1, pred_y_first_stage1 + (pred_y_first_stage2 - pred_y_first_stage1) * 0.25 / dist)
    xmin = tf.cast(tf.reduce_min(pred_x_first_stage), tf.int64)
    xmax = tf.cast(tf.reduce_max(pred_x_first_stage), tf.int64)
    ymin = tf.cast(tf.reduce_min(pred_y_first_stage), tf.int64)
    ymax = tf.cast(tf.reduce_max(pred_y_first_stage), tf.int64)
    xmin, ymin, xmax, ymax = (xmin - 100, ymin - 80, xmax + 100, ymax + 80)
    xmin = tf.clip_by_value(xmin, 0, shape[0][1][0] - 1)
    ymin = tf.clip_by_value(ymin, 0, shape[0][0][0] - 1)
    xmax = tf.clip_by_value(xmax, 0, shape[0][1][0] - 1)
    ymax = tf.clip_by_value(ymax, 0, shape[0][0][0] - 1)
    bbox_h = ymax - ymin
    bbox_w = xmax - xmin
    areas = bbox_h * bbox_w
    offsets = tf.stack([xmin, ymin], axis=0)
    crop_shape = tf.stack([bbox_h, bbox_w, shape[0][2][0]], axis=0)
    ymin, xmin, bbox_h, bbox_w = (tf.cast(ymin, tf.int32), tf.cast(xmin, tf.int32), tf.cast(bbox_h, tf.int32), tf.cast(bbox_w, tf.int32))
    single_image = tf.squeeze(features, [0])
    crop_image = tf.image.crop_to_bounding_box(single_image, ymin, xmin, bbox_h, bbox_w)
    crop_image = tf.expand_dims(crop_image, 0)
    image, shape, offsets = tf.cond(areas > 0, lambda: (crop_image, crop_shape, offsets), lambda: (features, shape, tf.constant([0, 0], tf.int64)))
    offsets.set_shape([2])
    offsets = tf.to_float(offsets)
    shape = tf.reshape(shape, [1, 3])
    image = preprocessing.preprocess_for_test_raw_output(image, params['train_image_size'], params['train_image_size'], data_format='NCHW' if FLAGS.data_format == 'channels_first' else 'NHWC', scope='second_stage')
    if not params['flip_on_test']:
        with tf.variable_scope(params['model_scope'], default_name=None, values=[image], reuse=True):
            pred_outputs = hg.create_model(image, params['num_stacks'], params['feats_channals'], config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], params['num_modules'], mode == tf.estimator.ModeKeys.TRAIN, params['data_format'])
        with tf.name_scope('refine_prediction'):
            if params['data_format'] == 'channels_last':
                pred_outputs = [tf.transpose(pred_outputs[ind], [0, 3, 1, 2], name='outputs_trans_{}'.format(ind)) for ind in list(range(len(pred_outputs)))]
            pred_x, pred_y = get_keypoint(image, pred_outputs[-1], params['heatmap_size'], shape[0][0], shape[0][1], params['model_scope'] if 'all' not in params['model_scope'] else '*', clip_at_zero=True, data_format=params['data_format'])
    else:
        with tf.name_scope('refine_prediction'):
            if params['data_format'] == 'channels_last':
                double_features = tf.reshape(tf.stack([image, tf.map_fn(tf.image.flip_left_right, image, back_prop=False)], axis=1), [-1, params['train_image_size'], params['train_image_size'], 3])
            else:
                double_features = tf.reshape(tf.stack([image, tf.transpose(tf.map_fn(tf.image.flip_left_right, tf.transpose(image, [0, 2, 3, 1], name='nchw2nhwc'), back_prop=False), [0, 3, 1, 2], name='nhwc2nchw')], axis=1), [-1, 3, params['train_image_size'], params['train_image_size']])
        num_joints = config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*']
        with tf.variable_scope(params['model_scope'], default_name=None, values=[double_features], reuse=True):
            pred_outputs = hg.create_model(double_features, params['num_stacks'], params['feats_channals'], config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], params['num_modules'], mode == tf.estimator.ModeKeys.TRAIN, params['data_format'])
        with tf.name_scope('refine_prediction'):
            if params['data_format'] == 'channels_last':
                pred_outputs = [tf.transpose(pred_outputs[ind], [0, 3, 1, 2], name='outputs_trans_{}'.format(ind)) for ind in list(range(len(pred_outputs)))]
            row_indices = tf.tile(tf.reshape(tf.stack([tf.range(0, tf.shape(double_features)[0], delta=2), tf.range(1, tf.shape(double_features)[0], delta=2)], axis=0), [-1, 1]), [1, num_joints])
            col_indices = tf.reshape(tf.tile(tf.reshape(tf.stack([tf.range(num_joints), tf.constant(config.left_right_remap[params['model_scope'] if 'all' not in params['model_scope'] else '*'])], axis=0), [2, -1]), [1, tf.shape(features)[0]]), [-1, num_joints])
            flip_indices = tf.stack([row_indices, col_indices], axis=-1)
            pred_outputs = [tf.gather_nd(pred_outputs[ind], flip_indices, name='gather_nd_{}'.format(ind)) for ind in list(range(len(pred_outputs)))]

            def cond_flip(heatmap_ind):
                return tf.cond(heatmap_ind[1] < tf.shape(features)[0], lambda: heatmap_ind[0], lambda: tf.transpose(tf.image.flip_left_right(tf.transpose(heatmap_ind[0], [1, 2, 0], name='pred_nchw2nhwc')), [2, 0, 1], name='pred_nhwc2nchw'))
            pred_outputs = [tf.map_fn(cond_flip, [pred_outputs[ind], tf.range(tf.shape(double_features)[0])], dtype=tf.float32, parallel_iterations=10, back_prop=True, swap_memory=False, infer_shape=True, name='map_fn_{}'.format(ind)) for ind in list(range(len(pred_outputs)))]
            pred_outputs = [tf.split(_, 2) for _ in pred_outputs]
            pred_outputs_1 = [_[0] for _ in pred_outputs]
            pred_outputs_2 = [_[1] for _ in pred_outputs]
            pred_x_first_stage1, pred_y_first_stage1 = get_keypoint(image, pred_outputs_1[-1], params['heatmap_size'], shape[0][0], shape[0][1], params['model_scope'] if 'all' not in params['model_scope'] else '*', clip_at_zero=True, data_format=params['data_format'])
            pred_x_first_stage2, pred_y_first_stage2 = get_keypoint(image, pred_outputs_2[-1], params['heatmap_size'], shape[0][0], shape[0][1], params['model_scope'] if 'all' not in params['model_scope'] else '*', clip_at_zero=True, data_format=params['data_format'])
            dist = tf.pow(tf.pow(pred_x_first_stage1 - pred_x_first_stage2, 2.0) + tf.pow(pred_y_first_stage1 - pred_y_first_stage2, 2.0), 0.5)
            pred_x = tf.where(dist < 0.001, pred_x_first_stage1, pred_x_first_stage1 + (pred_x_first_stage2 - pred_x_first_stage1) * 0.25 / dist)
            pred_y = tf.where(dist < 0.001, pred_y_first_stage1, pred_y_first_stage1 + (pred_y_first_stage2 - pred_y_first_stage1) * 0.25 / dist)
    predictions = {'pred_x': pred_x + offsets[0], 'pred_y': pred_y + offsets[1], 'file_name': file_name}
    if mode == tf.estimator.ModeKeys.PREDICT:
        return tf.estimator.EstimatorSpec(mode=mode, predictions=predictions, loss=None, train_op=None)
    else:
        raise ValueError('Only "PREDICT" mode is supported.')

def get_keypoint(image, targets, predictions, heatmap_size, height, width, category, clip_at_zero=True, data_format='channels_last', name=None):
    predictions = tf.reshape(predictions, [1, -1, heatmap_size * heatmap_size])
    pred_max = tf.reduce_max(predictions, axis=-1)
    pred_indices = tf.argmax(predictions, axis=-1)
    pred_x, pred_y = (tf.cast(tf.floormod(pred_indices, heatmap_size), tf.float32), tf.cast(tf.floordiv(pred_indices, heatmap_size), tf.float32))
    width, height = (tf.cast(width, tf.float32), tf.cast(height, tf.float32))
    pred_x, pred_y = (pred_x * width / tf.cast(heatmap_size, tf.float32), pred_y * height / tf.cast(heatmap_size, tf.float32))
    if clip_at_zero:
        pred_x, pred_y = (pred_x * tf.cast(pred_max > 0, tf.float32), pred_y * tf.cast(pred_max > 0, tf.float32))
        pred_x = pred_x * tf.cast(pred_max > 0, tf.float32) + tf.cast(pred_max <= 0, tf.float32) * (width / 2.0)
        pred_y = pred_y * tf.cast(pred_max > 0, tf.float32) + tf.cast(pred_max <= 0, tf.float32) * (height / 2.0)
    if config.PRED_DEBUG:
        pred_indices_ = tf.squeeze(pred_indices)
        image_ = tf.squeeze(image) * 255.0
        pred_heatmap = tf.one_hot(pred_indices_, heatmap_size * heatmap_size, on_value=1.0, off_value=0.0, axis=-1, dtype=tf.float32)
        pred_heatmap = tf.reshape(pred_heatmap, [-1, heatmap_size, heatmap_size])
        if data_format == 'channels_first':
            image_ = tf.transpose(image_, perm=(1, 2, 0))
        save_image_op = tf.py_func(save_image_with_heatmap, [image_, height, width, heatmap_size, tf.reshape(pred_heatmap * 255.0, [-1, heatmap_size, heatmap_size]), tf.reshape(predictions, [-1, heatmap_size, heatmap_size]), config.left_right_group_map[category][0], config.left_right_group_map[category][1], config.left_right_group_map[category][2]], tf.int64, stateful=True)
        with tf.control_dependencies([save_image_op]):
            pred_x, pred_y = (pred_x * 1.0, pred_y * 1.0)
    return (pred_x, pred_y)

def keypoint_model_fn(features, labels, mode, params):
    targets = labels['targets']
    shape = labels['shape']
    classid = labels['classid']
    key_v = labels['key_v']
    isvalid = labels['isvalid']
    norm_value = labels['norm_value']
    cur_batch_size = tf.shape(features)[0]
    with tf.variable_scope(params['model_scope'], default_name=None, values=[features], reuse=tf.AUTO_REUSE):
        pred_outputs = backbone_(features, config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], params['heatmap_size'], mode == tf.estimator.ModeKeys.TRAIN, params['data_format'])
    if params['data_format'] == 'channels_last':
        pred_outputs = [tf.transpose(pred_outputs[ind], [0, 3, 1, 2], name='outputs_trans_{}'.format(ind)) for ind in list(range(len(pred_outputs)))]
    score_map = pred_outputs[-1]
    pred_x, pred_y = get_keypoint(features, targets, score_map, params['heatmap_size'], params['train_image_size'], params['train_image_size'], params['model_scope'] if 'all' not in params['model_scope'] else '*', clip_at_zero=True, data_format=params['data_format'])
    targets = 255.0 * targets
    blur_list = [1.0, 1.37, 1.73, 2.4, None]
    targets_list = []
    for sigma in blur_list:
        if sigma is None:
            targets_list.append(targets)
        else:
            targets_list.append(gaussian_blur(targets, config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], sigma, params['data_format'], 'blur_{}'.format(sigma)))
    ne_mertric = mertric.normalized_error(targets, score_map, norm_value, key_v, isvalid, cur_batch_size, config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], params['heatmap_size'], params['train_image_size'])
    all_visible = tf.expand_dims(tf.expand_dims(tf.cast(tf.logical_and(key_v > 0, isvalid > 0), tf.float32), axis=-1), axis=-1)
    targets_list = [targets_list[ind] * all_visible for ind in list(range(len(targets_list)))]
    pred_outputs = [pred_outputs[ind] * all_visible for ind in list(range(len(pred_outputs)))]
    sq_diff = tf.reduce_sum(tf.squared_difference(targets, pred_outputs[-1]), axis=-1)
    last_pred_mse = tf.metrics.mean_absolute_error(sq_diff, tf.zeros_like(sq_diff), name='last_pred_mse')
    metrics = {'normalized_error': ne_mertric, 'last_pred_mse': last_pred_mse}
    predictions = {'normalized_error': ne_mertric[1]}
    ne_mertric = tf.identity(ne_mertric[1], name='ne_mertric')
    mse_loss_list = []
    if params['use_ohkm']:
        for pred_ind in list(range(len(pred_outputs) - 1)):
            mse_loss_list.append(0.5 * tf.losses.mean_squared_error(targets_list[pred_ind], pred_outputs[pred_ind], weights=1.0 / tf.cast(cur_batch_size, tf.float32), scope='loss_{}'.format(pred_ind), loss_collection=None, reduction=tf.losses.Reduction.MEAN))
        temp_loss = tf.reduce_mean(tf.reshape(tf.losses.mean_squared_error(targets_list[-1], pred_outputs[-1], weights=1.0, loss_collection=None, reduction=tf.losses.Reduction.NONE), [cur_batch_size, config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], -1]), axis=-1)
        num_topk = config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'] // 2
        gather_col = tf.nn.top_k(temp_loss, k=num_topk, sorted=True)[1]
        gather_row = tf.reshape(tf.tile(tf.reshape(tf.range(cur_batch_size), [-1, 1]), [1, num_topk]), [-1, 1])
        gather_indcies = tf.stop_gradient(tf.stack([gather_row, tf.reshape(gather_col, [-1, 1])], axis=-1))
        select_targets = tf.gather_nd(targets_list[-1], gather_indcies)
        select_heatmap = tf.gather_nd(pred_outputs[-1], gather_indcies)
        mse_loss_list.append(tf.losses.mean_squared_error(select_targets, select_heatmap, weights=1.0 / tf.cast(cur_batch_size, tf.float32), scope='loss_{}'.format(len(pred_outputs) - 1), loss_collection=None, reduction=tf.losses.Reduction.MEAN))
    else:
        for pred_ind in list(range(len(pred_outputs))):
            mse_loss_list.append(tf.losses.mean_squared_error(targets_list[pred_ind], pred_outputs[pred_ind], weights=1.0 / tf.cast(cur_batch_size, tf.float32), scope='loss_{}'.format(pred_ind), loss_collection=None, reduction=tf.losses.Reduction.MEAN))
    mse_loss = tf.multiply(params['mse_weight'], tf.add_n(mse_loss_list), name='mse_loss')
    tf.summary.scalar('mse', mse_loss)
    tf.losses.add_loss(mse_loss)
    loss = mse_loss + params['weight_decay'] * tf.add_n([tf.nn.l2_loss(v) for v in tf.trainable_variables() if 'batch_normalization' not in v.name])
    total_loss = tf.identity(loss, name='total_loss')
    tf.summary.scalar('loss', total_loss)
    if mode == tf.estimator.ModeKeys.EVAL:
        return tf.estimator.EstimatorSpec(mode=mode, loss=loss, predictions=predictions, eval_metric_ops=metrics)
    if mode == tf.estimator.ModeKeys.TRAIN:
        global_step = tf.train.get_or_create_global_step()
        if not params['dummy_train']:
            step_remainder = tf.floormod(global_step - 1, params['steps_per_epoch'])
            range_scale = tf.to_float(step_remainder + 1) / tf.to_float(params['steps_per_epoch'])
            learning_rate = tf.add((1 - range_scale) * params['high_learning_rate'], range_scale * params['low_learning_rate'], name='learning_rate')
            tf.summary.scalar('lr', learning_rate)
            should_update = tf.equal(step_remainder, params['steps_per_epoch'] - 2)
            optimizer = tf.train.MomentumOptimizer(learning_rate=learning_rate, momentum=params['momentum'])
            update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
            with tf.control_dependencies(update_ops):
                opt_op = optimizer.minimize(loss, global_step)
            variables_to_train = []
            for var in tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES):
                variables_to_train.append(var)
            ema = swa_moving_average.SWAMovingAverage(tf.floordiv(global_step, params['steps_per_epoch']))
            with tf.control_dependencies([opt_op]):
                train_op = tf.cond(should_update, lambda: ema.apply(variables_to_train), lambda: tf.no_op())
            _init_fn = train_helper.get_raw_init_fn_for_scaffold(params['checkpoint_path'], params['model_dir'])
        else:
            learning_rate = tf.constant(0.0, name='learning_rate')
            tf.summary.scalar('lr', learning_rate)
            optimizer = tf.train.MomentumOptimizer(learning_rate=learning_rate, momentum=0.0)
            variables_to_train = []
            for var in tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES):
                variables_to_train.append(var)
            ema = swa_moving_average.SWAMovingAverage(tf.floordiv(global_step, params['steps_per_epoch']))
            update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
            with tf.control_dependencies(update_ops):
                train_op = optimizer.minimize(loss, global_step)
            _init_fn = train_helper.swa_get_init_fn_for_scaffold(params['checkpoint_path'], params['model_dir'], variables_to_train, ema)
    else:
        train_op = None
    return tf.estimator.EstimatorSpec(mode=mode, predictions=predictions, loss=loss, train_op=train_op, eval_metric_ops=metrics, scaffold=tf.train.Scaffold(init_fn=_init_fn, saver=None))

def get_keypoint(image, targets, predictions, heatmap_size, height, width, category, clip_at_zero=True, data_format='channels_last', name=None):
    predictions = tf.reshape(predictions, [1, -1, heatmap_size * heatmap_size])
    pred_max = tf.reduce_max(predictions, axis=-1)
    pred_indices = tf.argmax(predictions, axis=-1)
    pred_x, pred_y = (tf.cast(tf.floormod(pred_indices, heatmap_size), tf.float32), tf.cast(tf.floordiv(pred_indices, heatmap_size), tf.float32))
    width, height = (tf.cast(width, tf.float32), tf.cast(height, tf.float32))
    pred_x, pred_y = (pred_x * width / tf.cast(heatmap_size, tf.float32), pred_y * height / tf.cast(heatmap_size, tf.float32))
    if clip_at_zero:
        pred_x, pred_y = (pred_x * tf.cast(pred_max > 0, tf.float32), pred_y * tf.cast(pred_max > 0, tf.float32))
        pred_x = pred_x * tf.cast(pred_max > 0, tf.float32) + tf.cast(pred_max <= 0, tf.float32) * (width / 2.0)
        pred_y = pred_y * tf.cast(pred_max > 0, tf.float32) + tf.cast(pred_max <= 0, tf.float32) * (height / 2.0)
    if config.PRED_DEBUG:
        pred_indices_ = tf.squeeze(pred_indices)
        image_ = tf.squeeze(image) * 255.0
        pred_heatmap = tf.one_hot(pred_indices_, heatmap_size * heatmap_size, on_value=1.0, off_value=0.0, axis=-1, dtype=tf.float32)
        pred_heatmap = tf.reshape(pred_heatmap, [-1, heatmap_size, heatmap_size])
        if data_format == 'channels_first':
            image_ = tf.transpose(image_, perm=(1, 2, 0))
        save_image_op = tf.py_func(save_image_with_heatmap, [image_, height, width, heatmap_size, tf.reshape(pred_heatmap * 255.0, [-1, heatmap_size, heatmap_size]), tf.reshape(predictions, [-1, heatmap_size, heatmap_size]), config.left_right_group_map[category][0], config.left_right_group_map[category][1], config.left_right_group_map[category][2]], tf.int64, stateful=True)
        with tf.control_dependencies([save_image_op]):
            pred_x, pred_y = (pred_x * 1.0, pred_y * 1.0)
    return (pred_x, pred_y)

def keypoint_model_fn(features, labels, mode, params):
    targets = labels['targets']
    shape = labels['shape']
    classid = labels['classid']
    key_v = labels['key_v']
    isvalid = labels['isvalid']
    norm_value = labels['norm_value']
    cur_batch_size = tf.shape(features)[0]
    with tf.variable_scope(params['model_scope'], default_name=None, values=[features], reuse=tf.AUTO_REUSE):
        pred_outputs = simple_xt.simple_net(features, config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], params['heatmap_size'], mode == tf.estimator.ModeKeys.TRAIN, params['data_format'])[0]
    if params['data_format'] == 'channels_last':
        pred_outputs = tf.transpose(pred_outputs, [0, 3, 1, 2], name='outputs_trans')
    score_map = pred_outputs
    pred_x, pred_y = get_keypoint(features, targets, score_map, params['heatmap_size'], params['train_image_size'], params['train_image_size'], params['model_scope'] if 'all' not in params['model_scope'] else '*', clip_at_zero=True, data_format=params['data_format'])
    targets = 255.0 * targets
    ne_mertric = mertric.normalized_error(targets, score_map, norm_value, key_v, isvalid, cur_batch_size, config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], params['heatmap_size'], params['train_image_size'])
    all_visible = tf.expand_dims(tf.expand_dims(tf.cast(tf.logical_and(key_v > 0, isvalid > 0), tf.float32), axis=-1), axis=-1)
    targets = targets * all_visible
    pred_outputs = pred_outputs * all_visible
    sq_diff = tf.reduce_sum(tf.squared_difference(targets, pred_outputs), axis=-1)
    last_pred_mse = tf.metrics.mean_absolute_error(sq_diff, tf.zeros_like(sq_diff), name='last_pred_mse')
    metrics = {'normalized_error': ne_mertric, 'last_pred_mse': last_pred_mse}
    predictions = {'normalized_error': ne_mertric[1]}
    ne_mertric = tf.identity(ne_mertric[1], name='ne_mertric')
    base_learning_rate = params['learning_rate']
    mse_loss_list = []
    if params['use_ohkm']:
        base_learning_rate = 1.0 * base_learning_rate
        temp_loss = tf.reduce_mean(tf.reshape(tf.losses.mean_squared_error(targets, pred_outputs, weights=1.0, loss_collection=None, reduction=tf.losses.Reduction.NONE), [cur_batch_size, config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], -1]), axis=-1)
        num_topk = config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'] // 2
        gather_col = tf.nn.top_k(temp_loss, k=num_topk, sorted=True)[1]
        gather_row = tf.reshape(tf.tile(tf.reshape(tf.range(cur_batch_size), [-1, 1]), [1, num_topk]), [-1, 1])
        gather_indcies = tf.stop_gradient(tf.stack([gather_row, tf.reshape(gather_col, [-1, 1])], axis=-1))
        select_targets = tf.gather_nd(targets, gather_indcies)
        select_heatmap = tf.gather_nd(pred_outputs, gather_indcies)
        mse_loss_list.append(tf.losses.mean_squared_error(select_targets, select_heatmap, weights=1.0 / tf.cast(cur_batch_size, tf.float32), scope='loss', loss_collection=None, reduction=tf.losses.Reduction.MEAN))
    else:
        mse_loss_list.append(tf.losses.mean_squared_error(targets, pred_outputs, weights=1.0 / tf.cast(cur_batch_size, tf.float32), scope='loss', loss_collection=None, reduction=tf.losses.Reduction.MEAN))
    mse_loss = tf.multiply(params['mse_weight'], tf.add_n(mse_loss_list), name='mse_loss')
    tf.summary.scalar('mse', mse_loss)
    tf.losses.add_loss(mse_loss)
    loss = mse_loss + params['weight_decay'] * tf.add_n([tf.nn.l2_loss(v) for v in tf.trainable_variables() if 'batch_normalization' not in v.name])
    total_loss = tf.identity(loss, name='total_loss')
    tf.summary.scalar('loss', total_loss)
    if mode == tf.estimator.ModeKeys.EVAL:
        return tf.estimator.EstimatorSpec(mode=mode, loss=loss, predictions=predictions, eval_metric_ops=metrics)
    if mode == tf.estimator.ModeKeys.TRAIN:
        global_step = tf.train.get_or_create_global_step()
        lr_values = [params['warmup_learning_rate']] + [base_learning_rate * decay for decay in params['lr_decay_factors']]
        learning_rate = tf.train.piecewise_constant(tf.cast(global_step, tf.int32), [params['warmup_steps']] + [int(float(ep) * params['steps_per_epoch']) for ep in params['decay_boundaries']], lr_values)
        truncated_learning_rate = tf.maximum(learning_rate, tf.constant(params['end_learning_rate'], dtype=learning_rate.dtype), name='learning_rate')
        tf.summary.scalar('lr', truncated_learning_rate)
        optimizer = tf.train.MomentumOptimizer(learning_rate=truncated_learning_rate, momentum=params['momentum'])
        optimizer = tf_replicate_model_fn.TowerOptimizer(optimizer)
        update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
        with tf.control_dependencies(update_ops):
            train_op = optimizer.minimize(loss, global_step)
    else:
        train_op = None
    return tf.estimator.EstimatorSpec(mode=mode, predictions=predictions, loss=loss, train_op=train_op, eval_metric_ops=metrics, scaffold=tf.train.Scaffold(init_fn=train_helper.get_init_fn_for_scaffold_(params['checkpoint_path'], params['model_dir'], params['checkpoint_exclude_scopes'], params['model_scope'], params['checkpoint_model_scope'], params['ignore_missing_vars'])))

def get_keypoint(image, predictions, heatmap_size, height, width, category, clip_at_zero=False, data_format='channels_last', name=None):
    predictions = tf.reshape(predictions, [1, -1, heatmap_size * heatmap_size])
    pred_max = tf.reduce_max(predictions, axis=-1)
    pred_max_indices = tf.argmax(predictions, axis=-1)
    pred_max_x, pred_max_y = (tf.cast(tf.floormod(pred_max_indices, heatmap_size), tf.float32), tf.cast(tf.floordiv(pred_max_indices, heatmap_size), tf.float32))
    mask_predictions = predictions * tf.one_hot(pred_max_indices, heatmap_size * heatmap_size, on_value=0.0, off_value=1.0, dtype=tf.float32)
    pred_next_max = tf.reduce_max(mask_predictions, axis=-1)
    pred_next_max_indices = tf.argmax(mask_predictions, axis=-1)
    pred_next_max_x, pred_next_max_y = (tf.cast(tf.floormod(pred_next_max_indices, heatmap_size), tf.float32), tf.cast(tf.floordiv(pred_next_max_indices, heatmap_size), tf.float32))
    dist = tf.pow(tf.pow(pred_next_max_x - pred_max_x, 2.0) + tf.pow(pred_next_max_y - pred_max_y, 2.0), 0.5)
    pred_x = tf.where(dist < 0.001, pred_max_x, pred_max_x + (pred_next_max_x - pred_max_x) * 0.25 / dist)
    pred_y = tf.where(dist < 0.001, pred_max_y, pred_max_y + (pred_next_max_y - pred_max_y) * 0.25 / dist)
    pred_indices_ = tf.squeeze(tf.cast(pred_x, tf.int64) + tf.cast(pred_y, tf.int64) * heatmap_size)
    width, height = (tf.cast(width, tf.float32), tf.cast(height, tf.float32))
    width_ratio, height_ratio = (width / tf.cast(heatmap_size, tf.float32), height / tf.cast(heatmap_size, tf.float32))
    pred_x, pred_y = (pred_x * width_ratio, pred_y * height_ratio)
    if clip_at_zero:
        pred_x, pred_y = (pred_x * tf.cast(pred_max > 0, tf.float32), pred_y * tf.cast(pred_max > 0, tf.float32))
        pred_x = pred_x * tf.cast(pred_max > 0, tf.float32) + tf.cast(pred_max <= 0, tf.float32) * (width / 2.0)
        pred_y = pred_y * tf.cast(pred_max > 0, tf.float32) + tf.cast(pred_max <= 0, tf.float32) * (height / 2.0)
    if config.PRED_DEBUG:
        image_ = tf.squeeze(image) * 255.0
        pred_heatmap = tf.one_hot(pred_indices_, heatmap_size * heatmap_size, on_value=255, off_value=0, axis=-1, dtype=tf.int32)
        pred_heatmap = tf.reshape(pred_heatmap, [-1, heatmap_size, heatmap_size])
        if data_format == 'channels_first':
            image_ = tf.transpose(image_, perm=(1, 2, 0))
        save_image_op = tf.py_func(save_image_with_heatmap, [image_, height, width, heatmap_size, pred_heatmap, tf.reshape(predictions, [-1, heatmap_size, heatmap_size]), config.left_right_group_map[category][0], config.left_right_group_map[category][1], config.left_right_group_map[category][2]], tf.int64, stateful=True)
        with tf.control_dependencies([save_image_op]):
            pred_x, pred_y = (pred_x * 1.0, pred_y * 1.0)
    return (pred_x, pred_y)

def keypoint_model_fn(features, labels, mode, params):
    shape = features['shape']
    classid = features['classid']
    file_name = features['file_name']
    features = features['images']
    file_name = tf.identity(file_name, name='current_file')
    image = preprocessing.preprocess_for_test_raw_output(features, params['train_image_size'], params['train_image_size'], data_format='NCHW' if FLAGS.data_format == 'channels_first' else 'NHWC', scope='first_stage')
    if not params['flip_on_test']:
        with tf.variable_scope(params['model_scope'], default_name=None, values=[image], reuse=tf.AUTO_REUSE):
            pred_outputs = backbone_(image, config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], params['heatmap_size'], mode == tf.estimator.ModeKeys.TRAIN, params['data_format'])
        if params['data_format'] == 'channels_last':
            pred_outputs = [tf.transpose(pred_outputs[ind], [0, 3, 1, 2], name='outputs_trans_{}'.format(ind)) for ind in list(range(len(pred_outputs)))]
        pred_x, pred_y = get_keypoint(image, pred_outputs[-1], params['heatmap_size'], shape[0][0], shape[0][1], params['model_scope'] if 'all' not in params['model_scope'] else '*', clip_at_zero=False, data_format=params['data_format'])
    else:
        if params['data_format'] == 'channels_last':
            double_features = tf.reshape(tf.stack([image, tf.map_fn(tf.image.flip_left_right, image, back_prop=False)], axis=1), [-1, params['train_image_size'], params['train_image_size'], 3])
        else:
            double_features = tf.reshape(tf.stack([image, tf.transpose(tf.map_fn(tf.image.flip_left_right, tf.transpose(image, [0, 2, 3, 1], name='nchw2nhwc'), back_prop=False), [0, 3, 1, 2], name='nhwc2nchw')], axis=1), [-1, 3, params['train_image_size'], params['train_image_size']])
        num_joints = config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*']
        with tf.variable_scope(params['model_scope'], default_name=None, values=[double_features], reuse=tf.AUTO_REUSE):
            pred_outputs = backbone_(double_features, config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], params['heatmap_size'], mode == tf.estimator.ModeKeys.TRAIN, params['data_format'])
        if params['data_format'] == 'channels_last':
            pred_outputs = [tf.transpose(pred_outputs[ind], [0, 3, 1, 2], name='outputs_trans_{}'.format(ind)) for ind in list(range(len(pred_outputs)))]
        row_indices = tf.tile(tf.reshape(tf.stack([tf.range(0, tf.shape(double_features)[0], delta=2), tf.range(1, tf.shape(double_features)[0], delta=2)], axis=0), [-1, 1]), [1, num_joints])
        col_indices = tf.reshape(tf.tile(tf.reshape(tf.stack([tf.range(num_joints), tf.constant(config.left_right_remap[params['model_scope'] if 'all' not in params['model_scope'] else '*'])], axis=0), [2, -1]), [1, tf.shape(features)[0]]), [-1, num_joints])
        flip_indices = tf.stack([row_indices, col_indices], axis=-1)
        pred_outputs = [tf.gather_nd(pred_outputs[ind], flip_indices, name='gather_nd_{}'.format(ind)) for ind in list(range(len(pred_outputs)))]

        def cond_flip(heatmap_ind):
            return tf.cond(heatmap_ind[1] < tf.shape(features)[0], lambda: heatmap_ind[0], lambda: tf.transpose(tf.image.flip_left_right(tf.transpose(heatmap_ind[0], [1, 2, 0], name='pred_nchw2nhwc')), [2, 0, 1], name='pred_nhwc2nchw'))
        pred_outputs = [tf.map_fn(cond_flip, [pred_outputs[ind], tf.range(tf.shape(double_features)[0])], dtype=tf.float32, parallel_iterations=10, back_prop=True, swap_memory=False, infer_shape=True, name='map_fn_{}'.format(ind)) for ind in list(range(len(pred_outputs)))]
        pred_outputs = [tf.split(_, 2) for _ in pred_outputs]
        pred_outputs_1 = [_[0] for _ in pred_outputs]
        pred_outputs_2 = [_[1] for _ in pred_outputs]
        pred_x_first_stage1, pred_y_first_stage1 = get_keypoint(image, pred_outputs_1[-1], params['heatmap_size'], shape[0][0], shape[0][1], params['model_scope'] if 'all' not in params['model_scope'] else '*', clip_at_zero=False, data_format=params['data_format'])
        pred_x_first_stage2, pred_y_first_stage2 = get_keypoint(image, pred_outputs_2[-1], params['heatmap_size'], shape[0][0], shape[0][1], params['model_scope'] if 'all' not in params['model_scope'] else '*', clip_at_zero=False, data_format=params['data_format'])
        dist = tf.pow(tf.pow(pred_x_first_stage1 - pred_x_first_stage2, 2.0) + tf.pow(pred_y_first_stage1 - pred_y_first_stage2, 2.0), 0.5)
        pred_x = tf.where(dist < 0.001, pred_x_first_stage1, pred_x_first_stage1 + (pred_x_first_stage2 - pred_x_first_stage1) * 0.25 / dist)
        pred_y = tf.where(dist < 0.001, pred_y_first_stage1, pred_y_first_stage1 + (pred_y_first_stage2 - pred_y_first_stage1) * 0.25 / dist)
    predictions = {'pred_x': pred_x, 'pred_y': pred_y, 'file_name': file_name}
    if mode == tf.estimator.ModeKeys.PREDICT:
        return tf.estimator.EstimatorSpec(mode=mode, predictions=predictions, loss=None, train_op=None)
    else:
        raise ValueError('Only "PREDICT" mode is supported.')

def get_keypoint(image, targets, predictions, heatmap_size, height, width, category, clip_at_zero=True, data_format='channels_last', name=None):
    predictions = tf.reshape(predictions, [1, -1, heatmap_size * heatmap_size])
    pred_max = tf.reduce_max(predictions, axis=-1)
    pred_indices = tf.argmax(predictions, axis=-1)
    pred_x, pred_y = (tf.cast(tf.floormod(pred_indices, heatmap_size), tf.float32), tf.cast(tf.floordiv(pred_indices, heatmap_size), tf.float32))
    width, height = (tf.cast(width, tf.float32), tf.cast(height, tf.float32))
    pred_x, pred_y = (pred_x * width / tf.cast(heatmap_size, tf.float32), pred_y * height / tf.cast(heatmap_size, tf.float32))
    if clip_at_zero:
        pred_x, pred_y = (pred_x * tf.cast(pred_max > 0, tf.float32), pred_y * tf.cast(pred_max > 0, tf.float32))
        pred_x = pred_x * tf.cast(pred_max > 0, tf.float32) + tf.cast(pred_max <= 0, tf.float32) * (width / 2.0)
        pred_y = pred_y * tf.cast(pred_max > 0, tf.float32) + tf.cast(pred_max <= 0, tf.float32) * (height / 2.0)
    if config.PRED_DEBUG:
        pred_indices_ = tf.squeeze(pred_indices)
        image_ = tf.squeeze(image) * 255.0
        pred_heatmap = tf.one_hot(pred_indices_, heatmap_size * heatmap_size, on_value=1.0, off_value=0.0, axis=-1, dtype=tf.float32)
        pred_heatmap = tf.reshape(pred_heatmap, [-1, heatmap_size, heatmap_size])
        if data_format == 'channels_first':
            image_ = tf.transpose(image_, perm=(1, 2, 0))
        save_image_op = tf.py_func(save_image_with_heatmap, [image_, height, width, heatmap_size, tf.reshape(pred_heatmap * 255.0, [-1, heatmap_size, heatmap_size]), tf.reshape(predictions, [-1, heatmap_size, heatmap_size]), config.left_right_group_map[category][0], config.left_right_group_map[category][1], config.left_right_group_map[category][2]], tf.int64, stateful=True)
        with tf.control_dependencies([save_image_op]):
            pred_x, pred_y = (pred_x * 1.0, pred_y * 1.0)
    return (pred_x, pred_y)

def keypoint_model_fn(features, labels, mode, params):
    targets = labels['targets']
    shape = labels['shape']
    classid = labels['classid']
    key_v = labels['key_v']
    isvalid = labels['isvalid']
    norm_value = labels['norm_value']
    cur_batch_size = tf.shape(features)[0]
    with tf.variable_scope(params['model_scope'], default_name=None, values=[features], reuse=tf.AUTO_REUSE):
        pred_outputs = backbone_(features, config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], params['heatmap_size'], mode == tf.estimator.ModeKeys.TRAIN, params['data_format'], net_depth=params['net_depth'])
    if params['data_format'] == 'channels_last':
        pred_outputs = [tf.transpose(pred_outputs[ind], [0, 3, 1, 2], name='outputs_trans_{}'.format(ind)) for ind in list(range(len(pred_outputs)))]
    score_map = pred_outputs[-1]
    pred_x, pred_y = get_keypoint(features, targets, score_map, params['heatmap_size'], params['train_image_size'], params['train_image_size'], params['model_scope'] if 'all' not in params['model_scope'] else '*', clip_at_zero=True, data_format=params['data_format'])
    targets = 255.0 * targets
    blur_list = [1.0, 1.37, 1.73, 2.4, None]
    targets_list = []
    for sigma in blur_list:
        if sigma is None:
            targets_list.append(targets)
        else:
            targets_list.append(gaussian_blur(targets, config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], sigma, params['data_format'], 'blur_{}'.format(sigma)))
    ne_mertric = mertric.normalized_error(targets, score_map, norm_value, key_v, isvalid, cur_batch_size, config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], params['heatmap_size'], params['train_image_size'])
    all_visible = tf.expand_dims(tf.expand_dims(tf.cast(tf.logical_and(key_v > 0, isvalid > 0), tf.float32), axis=-1), axis=-1)
    targets_list = [targets_list[ind] * all_visible for ind in list(range(len(targets_list)))]
    pred_outputs = [pred_outputs[ind] * all_visible for ind in list(range(len(pred_outputs)))]
    sq_diff = tf.reduce_sum(tf.squared_difference(targets, pred_outputs[-1]), axis=-1)
    last_pred_mse = tf.metrics.mean_absolute_error(sq_diff, tf.zeros_like(sq_diff), name='last_pred_mse')
    metrics = {'normalized_error': ne_mertric, 'last_pred_mse': last_pred_mse}
    predictions = {'normalized_error': ne_mertric[1]}
    ne_mertric = tf.identity(ne_mertric[1], name='ne_mertric')
    base_learning_rate = params['learning_rate']
    mse_loss_list = []
    if params['use_ohkm']:
        base_learning_rate = 1.0 * base_learning_rate
        for pred_ind in list(range(len(pred_outputs) - 1)):
            mse_loss_list.append(0.5 * tf.losses.mean_squared_error(targets_list[pred_ind], pred_outputs[pred_ind], weights=1.0 / tf.cast(cur_batch_size, tf.float32), scope='loss_{}'.format(pred_ind), loss_collection=None, reduction=tf.losses.Reduction.MEAN))
        temp_loss = tf.reduce_mean(tf.reshape(tf.losses.mean_squared_error(targets_list[-1], pred_outputs[-1], weights=1.0, loss_collection=None, reduction=tf.losses.Reduction.NONE), [cur_batch_size, config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'], -1]), axis=-1)
        num_topk = config.class_num_joints[params['model_scope'] if 'all' not in params['model_scope'] else '*'] // 2
        gather_col = tf.nn.top_k(temp_loss, k=num_topk, sorted=True)[1]
        gather_row = tf.reshape(tf.tile(tf.reshape(tf.range(cur_batch_size), [-1, 1]), [1, num_topk]), [-1, 1])
        gather_indcies = tf.stop_gradient(tf.stack([gather_row, tf.reshape(gather_col, [-1, 1])], axis=-1))
        select_targets = tf.gather_nd(targets_list[-1], gather_indcies)
        select_heatmap = tf.gather_nd(pred_outputs[-1], gather_indcies)
        mse_loss_list.append(tf.losses.mean_squared_error(select_targets, select_heatmap, weights=1.0 / tf.cast(cur_batch_size, tf.float32), scope='loss_{}'.format(len(pred_outputs) - 1), loss_collection=None, reduction=tf.losses.Reduction.MEAN))
    else:
        for pred_ind in list(range(len(pred_outputs))):
            mse_loss_list.append(tf.losses.mean_squared_error(targets_list[pred_ind], pred_outputs[pred_ind], weights=1.0 / tf.cast(cur_batch_size, tf.float32), scope='loss_{}'.format(pred_ind), loss_collection=None, reduction=tf.losses.Reduction.MEAN))
    mse_loss = tf.multiply(params['mse_weight'], tf.add_n(mse_loss_list), name='mse_loss')
    tf.summary.scalar('mse', mse_loss)
    tf.losses.add_loss(mse_loss)
    loss = mse_loss + params['weight_decay'] * tf.add_n([tf.nn.l2_loss(v) for v in tf.trainable_variables() if 'batch_normalization' not in v.name])
    total_loss = tf.identity(loss, name='total_loss')
    tf.summary.scalar('loss', total_loss)
    if mode == tf.estimator.ModeKeys.EVAL:
        return tf.estimator.EstimatorSpec(mode=mode, loss=loss, predictions=predictions, eval_metric_ops=metrics)
    if mode == tf.estimator.ModeKeys.TRAIN:
        global_step = tf.train.get_or_create_global_step()
        lr_values = [params['warmup_learning_rate']] + [base_learning_rate * decay for decay in params['lr_decay_factors']]
        learning_rate = tf.train.piecewise_constant(tf.cast(global_step, tf.int32), [params['warmup_steps']] + [int(float(ep) * params['steps_per_epoch']) for ep in params['decay_boundaries']], lr_values)
        truncated_learning_rate = tf.maximum(learning_rate, tf.constant(params['end_learning_rate'], dtype=learning_rate.dtype), name='learning_rate')
        tf.summary.scalar('lr', truncated_learning_rate)
        optimizer = tf.train.MomentumOptimizer(learning_rate=truncated_learning_rate, momentum=params['momentum'])
        optimizer = tf_replicate_model_fn.TowerOptimizer(optimizer)
        update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
        with tf.control_dependencies(update_ops):
            train_op = optimizer.minimize(loss, global_step)
    else:
        train_op = None
    return tf.estimator.EstimatorSpec(mode=mode, predictions=predictions, loss=loss, train_op=train_op, eval_metric_ops=metrics, scaffold=tf.train.Scaffold(init_fn=train_helper.get_init_fn_for_scaffold_(params['checkpoint_path'], params['model_dir'], params['checkpoint_exclude_scopes'], params['model_scope'], params['checkpoint_model_scope'], params['ignore_missing_vars'])))

def _safe_div(numerator, denominator, name):
    """Divides two tensors element-wise, returning 0 if the denominator is <= 0.

  Args:
    numerator: A real `Tensor`.
    denominator: A real `Tensor`, with dtype matching `numerator`.
    name: Name for the returned op.

  Returns:
    0 if `denominator` <= 0, else `numerator` / `denominator`
  """
    t = math_ops.truediv(numerator, denominator)
    zero = array_ops.zeros_like(t, dtype=denominator.dtype)
    condition = math_ops.greater(denominator, zero)
    zero = math_ops.cast(zero, t.dtype)
    return array_ops.where(condition, t, zero, name=name)

def normalized_error(targets, predictions, norm_value, visible, isvalid, bacth_size, num_keypoint, heatmap_size, train_image_size, clip_at_zero=True, name=None):
    with variable_scope.variable_scope(name, 'normalized_error', (targets, predictions, norm_value, visible, isvalid, bacth_size, num_keypoint, train_image_size, heatmap_size)):
        total = metric_variable([], dtypes.float32, name='total')
        count = metric_variable([], dtypes.float32, name='count')
        targets, predictions = (tf.reshape(targets, [bacth_size, num_keypoint, -1]), tf.reshape(predictions, [bacth_size, num_keypoint, -1]))
        pred_max = tf.reduce_max(predictions, axis=-1)
        pred_indices = tf.argmax(predictions, axis=-1)
        pred_x, pred_y = (tf.floormod(pred_indices, heatmap_size) * train_image_size / heatmap_size, tf.floordiv(pred_indices, heatmap_size) * train_image_size / heatmap_size)
        pred_x, pred_y = (tf.cast(pred_x, tf.float32), tf.cast(pred_y, tf.float32))
        if clip_at_zero:
            pred_x, pred_y = (pred_x * tf.cast(pred_max > 0, tf.float32), pred_y * tf.cast(pred_max > 0, tf.float32))
        gt_indices = tf.argmax(targets, axis=-1)
        gt_x, gt_y = (tf.floormod(gt_indices, heatmap_size) * train_image_size / heatmap_size, tf.floordiv(gt_indices, heatmap_size) * train_image_size / heatmap_size)
        gt_x, gt_y = (tf.cast(gt_x, tf.float32), tf.cast(gt_y, tf.float32))
        dist = _safe_div(tf.pow(tf.pow(gt_x - pred_x, 2.0) + tf.pow(gt_y - pred_y, 2.0), 0.5), tf.expand_dims(norm_value, -1), 'norm_dist')
        dist = tf.boolean_mask(dist, tf.logical_and(visible > 0, isvalid > 0))
        update_total_op = state_ops.assign(total, math_ops.reduce_sum(dist))
        update_count_op = state_ops.assign(count, tf.cast(tf.shape(dist)[0], tf.float32))
        mean_t = _safe_div(total, count, 'value')
        update_op = _safe_div(update_total_op, update_count_op, 'update_op')
        return (mean_t, update_op)

def rotate_augum(image, shape, fkey_x, fkey_y, bbox_border):
    x_mask = fkey_x > 0.0
    y_mask = fkey_y > 0.0
    bak_fkey_x, bak_fkey_y, bak_image = (fkey_x / tf.cast(shape[1], tf.float32), fkey_y / tf.cast(shape[0], tf.float32), image)
    image, fkey_x, fkey_y = tf.cond(tf.random_uniform([1], minval=0.0, maxval=1.0, dtype=tf.float32)[0] < 0.4, lambda: rotate_all(image, tf.random_uniform([1], minval=-3.14 / 6.0, maxval=3.14 / 6.0, dtype=tf.float32)[0], fkey_x, fkey_y), lambda: (image, fkey_x, fkey_y))
    fkey_x, fkey_y = (fkey_x / tf.cast(shape[1], tf.float32), fkey_y / tf.cast(shape[0], tf.float32))
    x_mask_ = tf.logical_and(fkey_x > 0.0, fkey_x < 1.0)
    y_mask_ = tf.logical_and(fkey_y > 0.0, fkey_y < 1.0)
    x_mask = tf.logical_and(x_mask, x_mask_)
    y_mask = tf.logical_and(y_mask, y_mask_)
    fkey_x = fkey_x * tf.cast(x_mask, tf.float32) + (tf.cast(x_mask, tf.float32) - 1.0)
    fkey_y = fkey_y * tf.cast(y_mask, tf.float32) + (tf.cast(y_mask, tf.float32) - 1.0)
    new_image, new_fkey_x, new_fkey_y = tf.cond(tf.count_nonzero(tf.logical_and(x_mask, y_mask)) > 0, lambda: (image, fkey_x, fkey_y), lambda: (bak_image, bak_fkey_x, bak_fkey_y))
    valid_x = tf.boolean_mask(new_fkey_x, new_fkey_x > 0.0)
    valid_y = tf.boolean_mask(new_fkey_y, new_fkey_y > 0.0)
    min_x = tf.maximum(tf.reduce_min(valid_x, axis=-1) - bbox_border / tf.cast(shape[0], tf.float32), 0.0)
    max_x = tf.minimum(tf.reduce_max(valid_x, axis=-1) + bbox_border / tf.cast(shape[0], tf.float32), 1.0)
    min_y = tf.maximum(tf.reduce_min(valid_y, axis=-1) - bbox_border / tf.cast(shape[1], tf.float32), 0.0)
    max_y = tf.minimum(tf.reduce_max(valid_y, axis=-1) + bbox_border / tf.cast(shape[1], tf.float32), 1.0)
    return (new_image, new_fkey_x, new_fkey_y, tf.reshape(tf.stack([min_y, min_x, max_y, max_x], axis=-1), [1, 1, 4]))

def _smallest_size_at_least(height, width, resize_min):
    """Computes new shape with the smallest side equal to `smallest_side`.

  Computes new shape with the smallest side equal to `smallest_side` while
  preserving the original aspect ratio.

  Args:
    height: an int32 scalar tensor indicating the current height.
    width: an int32 scalar tensor indicating the current width.
    resize_min: A python integer or scalar `Tensor` indicating the size of
      the smallest side after resize.

  Returns:
    new_height: an int32 scalar tensor indicating the new height.
    new_width: an int32 scalar tensor indicating the new width.
  """
    resize_min = tf.cast(resize_min, tf.float32)
    height, width = (tf.cast(height, tf.float32), tf.cast(width, tf.float32))
    smaller_dim = tf.minimum(height, width)
    scale_ratio = resize_min / smaller_dim
    new_height = tf.cast(height * scale_ratio, tf.int32)
    new_width = tf.cast(width * scale_ratio, tf.int32)
    return (new_height, new_width)

