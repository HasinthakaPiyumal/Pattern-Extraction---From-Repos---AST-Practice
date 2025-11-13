# Cluster 4

def weighted_moving_average(value, decay, weight, truediv=True, collections=None, name=None):
    """Compute the weighted moving average of `value`.

  Conceptually, the weighted moving average is:
    `moving_average(value * weight) / moving_average(weight)`,
  where a moving average updates by the rule
    `new_value = decay * old_value + (1 - decay) * update`
  Internally, this Op keeps moving average variables of both `value * weight`
  and `weight`.

  Args:
    value: A numeric `Tensor`.
    decay: A float `Tensor` or float value.  The moving average decay.
    weight:  `Tensor` that keeps the current value of a weight.
      Shape should be able to multiply `value`.
    truediv:  Boolean, if `True`, dividing by `moving_average(weight)` is
      floating point division.  If `False`, use division implied by dtypes.
    collections:  List of graph collections keys to add the internal variables
      `value * weight` and `weight` to.
      Defaults to `[GraphKeys.GLOBAL_VARIABLES]`.
    name: Optional name of the returned operation.
      Defaults to "WeightedMovingAvg".

  Returns:
    An Operation that updates and returns the weighted moving average.
  """
    if collections is None:
        collections = [ops.GraphKeys.GLOBAL_VARIABLES]
    with variable_scope.variable_scope(name, 'WeightedMovingAvg', [value, weight, decay]) as scope:
        value_x_weight_var = variable_scope.get_variable('value_x_weight', shape=value.get_shape(), dtype=value.dtype, initializer=init_ops.zeros_initializer(), trainable=False, collections=collections)
        weight_var = variable_scope.get_variable('weight', shape=weight.get_shape(), dtype=weight.dtype, initializer=init_ops.zeros_initializer(), trainable=False, collections=collections)
        numerator = assign_moving_average(value_x_weight_var, value * weight, decay, zero_debias=False)
        denominator = assign_moving_average(weight_var, weight, decay, zero_debias=False)
        if truediv:
            return math_ops.truediv(numerator, denominator, name=scope.name)
        else:
            return math_ops.div(numerator, denominator, name=scope.name)

def _scale_loss(loss, loss_reduction, number_of_towers):
    """If needed, scale down the loss for averaging loss by summing."""
    if loss is None:
        return None
    if number_of_towers == 1:
        return loss
    if loss_reduction != losses.Reduction.SUM:
        return math_ops.div(loss, 1.0 * number_of_towers, name='averaged_loss')
    else:
        return loss

def batch_norm(inputs, training, data_format, name=None):
    """Performs a batch normalization using a standard set of parameters."""
    return tf.layers.batch_normalization(inputs=inputs, axis=1 if data_format == 'channels_first' else 3, momentum=_BATCH_NORM_DECAY, epsilon=_BATCH_NORM_EPSILON, center=True, scale=True, training=training, name=name, fused=_USE_FUSED_BN)

def fixed_padding(inputs, kernel_size, data_format):
    """Pads the input along the spatial dimensions independently of input size.

    Args:
      inputs: A tensor of size [batch, channels, height_in, width_in] or
        [batch, height_in, width_in, channels] depending on data_format.
      kernel_size: The kernel to be used in the conv2d or max_pool2d operation.
                   Should be a positive integer.
      data_format: The input format ('channels_last' or 'channels_first').

    Returns:
      A tensor with the same format as the input with the data either intact
      (if kernel_size == 1) or padded (if kernel_size > 1).
    """
    pad_total = kernel_size - 1
    pad_beg = pad_total // 2
    pad_end = pad_total - pad_beg
    if data_format == 'channels_first':
        padded_inputs = tf.pad(inputs, [[0, 0], [0, 0], [pad_beg, pad_end], [pad_beg, pad_end]])
    else:
        padded_inputs = tf.pad(inputs, [[0, 0], [pad_beg, pad_end], [pad_beg, pad_end], [0, 0]])
    return padded_inputs

def conv2d_fixed_padding(inputs, filters, kernel_size, strides, data_format, kernel_initializer=tf.glorot_uniform_initializer, name=None):
    """Strided 2-D convolution with explicit padding."""
    if strides > 1:
        inputs = fixed_padding(inputs, kernel_size, data_format)
    return tf.layers.conv2d(inputs=inputs, filters=filters, kernel_size=kernel_size, strides=strides, padding='SAME' if strides == 1 else 'VALID', use_bias=False, kernel_initializer=kernel_initializer(), data_format=data_format, name=name)

def wrapper_initlizer(shape, dtype=None, partition_info=None):
    return constant_xavier_initializer(shape, 32, dtype)

def se_next_bottleneck_block(inputs, input_filters, name_prefix, is_training, group, data_format='channels_last', need_reduce=True, is_root=False, reduced_scale=16):
    bn_axis = -1 if data_format == 'channels_last' else 1
    strides_to_use = 1
    residuals = inputs
    if need_reduce:
        strides_to_use = 1 if is_root else 2
        proj_mapping = tf.layers.conv2d(inputs, input_filters, (1, 1), use_bias=False, name=name_prefix + '_1x1_proj', strides=(strides_to_use, strides_to_use), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
        residuals = tf.layers.batch_normalization(proj_mapping, momentum=_BATCH_NORM_DECAY, name=name_prefix + '_1x1_proj/bn', axis=bn_axis, epsilon=_BATCH_NORM_EPSILON, training=is_training, reuse=None, fused=_USE_FUSED_BN)
    reduced_inputs = tf.layers.conv2d(inputs, input_filters // 2, (1, 1), use_bias=False, name=name_prefix + '_1x1_reduce', strides=(1, 1), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
    reduced_inputs_bn = tf.layers.batch_normalization(reduced_inputs, momentum=_BATCH_NORM_DECAY, name=name_prefix + '_1x1_reduce/bn', axis=bn_axis, epsilon=_BATCH_NORM_EPSILON, training=is_training, reuse=None, fused=_USE_FUSED_BN)
    reduced_inputs_relu = tf.nn.relu(reduced_inputs_bn, name=name_prefix + '_1x1_reduce/relu')
    if data_format == 'channels_first':
        reduced_inputs_relu = tf.pad(reduced_inputs_relu, paddings=[[0, 0], [0, 0], [1, 1], [1, 1]])
        weight_shape = [3, 3, reduced_inputs_relu.get_shape().as_list()[1] // group, input_filters // 2]
        if is_training:
            weight_ = tf.Variable(constant_xavier_initializer(weight_shape, group=group, dtype=tf.float32), trainable=is_training, name=name_prefix + '_3x3/kernel')
        else:
            weight_ = tf.get_variable(name_prefix + '_3x3/kernel', shape=weight_shape, initializer=wrapper_initlizer, trainable=is_training)
        weight_groups = tf.split(weight_, num_or_size_splits=group, axis=-1, name=name_prefix + '_weight_split')
        xs = tf.split(reduced_inputs_relu, num_or_size_splits=group, axis=1, name=name_prefix + '_inputs_split')
    else:
        reduced_inputs_relu = tf.pad(reduced_inputs_relu, paddings=[[0, 0], [1, 1], [1, 1], [0, 0]])
        weight_shape = [3, 3, reduced_inputs_relu.get_shape().as_list()[-1] // group, input_filters // 2]
        if is_training:
            weight_ = tf.Variable(constant_xavier_initializer(weight_shape, group=group, dtype=tf.float32), trainable=is_training, name=name_prefix + '_3x3/kernel')
        else:
            weight_ = tf.get_variable(name_prefix + '_3x3/kernel', shape=weight_shape, initializer=wrapper_initlizer, trainable=is_training)
        weight_groups = tf.split(weight_, num_or_size_splits=group, axis=-1, name=name_prefix + '_weight_split')
        xs = tf.split(reduced_inputs_relu, num_or_size_splits=group, axis=-1, name=name_prefix + '_inputs_split')
    convolved = [tf.nn.convolution(x, weight, padding='VALID', strides=[strides_to_use, strides_to_use], name=name_prefix + '_group_conv', data_format='NCHW' if data_format == 'channels_first' else 'NHWC') for x, weight in zip(xs, weight_groups)]
    if data_format == 'channels_first':
        conv3_inputs = tf.concat(convolved, axis=1, name=name_prefix + '_concat')
    else:
        conv3_inputs = tf.concat(convolved, axis=-1, name=name_prefix + '_concat')
    conv3_inputs_bn = tf.layers.batch_normalization(conv3_inputs, momentum=_BATCH_NORM_DECAY, name=name_prefix + '_3x3/bn', axis=bn_axis, epsilon=_BATCH_NORM_EPSILON, training=is_training, reuse=None, fused=_USE_FUSED_BN)
    conv3_inputs_relu = tf.nn.relu(conv3_inputs_bn, name=name_prefix + '_3x3/relu')
    increase_inputs = tf.layers.conv2d(conv3_inputs_relu, input_filters, (1, 1), use_bias=False, name=name_prefix + '_1x1_increase', strides=(1, 1), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
    increase_inputs_bn = tf.layers.batch_normalization(increase_inputs, momentum=_BATCH_NORM_DECAY, name=name_prefix + '_1x1_increase/bn', axis=bn_axis, epsilon=_BATCH_NORM_EPSILON, training=is_training, reuse=None, fused=_USE_FUSED_BN)
    if data_format == 'channels_first':
        pooled_inputs = tf.reduce_mean(increase_inputs_bn, [2, 3], name=name_prefix + '_global_pool', keep_dims=True)
    else:
        pooled_inputs = tf.reduce_mean(increase_inputs_bn, [1, 2], name=name_prefix + '_global_pool', keep_dims=True)
    down_inputs = tf.layers.conv2d(pooled_inputs, input_filters // reduced_scale, (1, 1), use_bias=True, name=name_prefix + '_1x1_down', strides=(1, 1), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
    down_inputs_relu = tf.nn.relu(down_inputs, name=name_prefix + '_1x1_down/relu')
    up_inputs = tf.layers.conv2d(down_inputs_relu, input_filters, (1, 1), use_bias=True, name=name_prefix + '_1x1_up', strides=(1, 1), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
    prob_outputs = tf.nn.sigmoid(up_inputs, name=name_prefix + '_prob')
    rescaled_feat = tf.multiply(prob_outputs, increase_inputs_bn, name=name_prefix + '_mul')
    pre_act = tf.add(residuals, rescaled_feat, name=name_prefix + '_add')
    return tf.nn.relu(pre_act, name=name_prefix + '/relu')

def sext_cpn_backbone(input_image, istraining, data_format, net_depth=50, group=32):
    bn_axis = -1 if data_format == 'channels_last' else 1
    if data_format == 'channels_last':
        image_channels = tf.unstack(input_image, axis=-1)
        swaped_input_image = tf.stack([image_channels[2], image_channels[1], image_channels[0]], axis=-1)
    else:
        image_channels = tf.unstack(input_image, axis=1)
        swaped_input_image = tf.stack([image_channels[2], image_channels[1], image_channels[0]], axis=1)
    if net_depth not in [50, 101]:
        raise TypeError('Only ResNeXt50 or ResNeXt101 is supprted now.')
    input_depth = [256, 512, 1024, 2048]
    num_units = [3, 4, 6, 3] if net_depth == 50 else [3, 4, 23, 3]
    block_name_prefix = ['conv2_{}', 'conv3_{}', 'conv4_{}', 'conv5_{}']
    if data_format == 'channels_first':
        swaped_input_image = tf.pad(swaped_input_image, paddings=[[0, 0], [0, 0], [3, 3], [3, 3]])
    else:
        swaped_input_image = tf.pad(swaped_input_image, paddings=[[0, 0], [3, 3], [3, 3], [0, 0]])
    inputs_features = tf.layers.conv2d(swaped_input_image, input_depth[0] // 4, (7, 7), use_bias=False, name='conv1/7x7_s2', strides=(2, 2), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
    inputs_features = tf.layers.batch_normalization(inputs_features, momentum=_BATCH_NORM_DECAY, name='conv1/7x7_s2/bn', axis=bn_axis, epsilon=_BATCH_NORM_EPSILON, training=istraining, reuse=None, fused=_USE_FUSED_BN)
    inputs_features = tf.nn.relu(inputs_features, name='conv1/relu_7x7_s2')
    inputs_features = tf.layers.max_pooling2d(inputs_features, [3, 3], [2, 2], padding='same', data_format=data_format, name='pool1/3x3_s2')
    end_points = []
    is_root = True
    for ind, num_unit in enumerate(num_units):
        need_reduce = True
        for unit_index in range(1, num_unit + 1):
            inputs_features = se_next_bottleneck_block(inputs_features, input_depth[ind], block_name_prefix[ind].format(unit_index), is_training=istraining, group=group, data_format=data_format, need_reduce=need_reduce, is_root=is_root)
            need_reduce = False
            is_root = False
        end_points.append(inputs_features)
    return end_points

def se_bottleneck_block(inputs, input_filters, name_prefix, is_training, data_format='channels_last', need_reduce=True, is_root=False, reduced_scale=16):
    bn_axis = -1 if data_format == 'channels_last' else 1
    strides_to_use = 1
    residuals = inputs
    if need_reduce:
        strides_to_use = 1 if is_root else 2
        proj_mapping = tf.layers.conv2d(inputs, input_filters * 2, (1, 1), use_bias=False, name=name_prefix + '_1x1_proj', strides=(strides_to_use, strides_to_use), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
        residuals = tf.layers.batch_normalization(proj_mapping, momentum=_BATCH_NORM_DECAY, name=name_prefix + '_1x1_proj/bn', axis=bn_axis, epsilon=_BATCH_NORM_EPSILON, training=is_training, reuse=None, fused=_USE_FUSED_BN)
    reduced_inputs = tf.layers.conv2d(inputs, input_filters / 2, (1, 1), use_bias=False, name=name_prefix + '_1x1_reduce', strides=(strides_to_use, strides_to_use), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
    reduced_inputs_bn = tf.layers.batch_normalization(reduced_inputs, momentum=_BATCH_NORM_DECAY, name=name_prefix + '_1x1_reduce/bn', axis=bn_axis, epsilon=_BATCH_NORM_EPSILON, training=is_training, reuse=None, fused=_USE_FUSED_BN)
    reduced_inputs_relu = tf.nn.relu(reduced_inputs_bn, name=name_prefix + '_1x1_reduce/relu')
    conv3_inputs = tf.layers.conv2d(reduced_inputs_relu, input_filters / 2, (3, 3), use_bias=False, name=name_prefix + '_3x3', strides=(1, 1), padding='same', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
    conv3_inputs_bn = tf.layers.batch_normalization(conv3_inputs, momentum=_BATCH_NORM_DECAY, name=name_prefix + '_3x3/bn', axis=bn_axis, epsilon=_BATCH_NORM_EPSILON, training=is_training, reuse=None, fused=_USE_FUSED_BN)
    conv3_inputs_relu = tf.nn.relu(conv3_inputs_bn, name=name_prefix + '_3x3/relu')
    increase_inputs = tf.layers.conv2d(conv3_inputs_relu, input_filters * 2, (1, 1), use_bias=False, name=name_prefix + '_1x1_increase', strides=(1, 1), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
    increase_inputs_bn = tf.layers.batch_normalization(increase_inputs, momentum=_BATCH_NORM_DECAY, name=name_prefix + '_1x1_increase/bn', axis=bn_axis, epsilon=_BATCH_NORM_EPSILON, training=is_training, reuse=None, fused=_USE_FUSED_BN)
    if data_format == 'channels_first':
        pooled_inputs = tf.reduce_mean(increase_inputs_bn, [2, 3], name=name_prefix + '_global_pool', keep_dims=True)
    else:
        pooled_inputs = tf.reduce_mean(increase_inputs_bn, [1, 2], name=name_prefix + '_global_pool', keep_dims=True)
    down_inputs = tf.layers.conv2d(pooled_inputs, input_filters * 2 // reduced_scale, (1, 1), use_bias=True, name=name_prefix + '_1x1_down', strides=(1, 1), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
    down_inputs_relu = tf.nn.relu(down_inputs, name=name_prefix + '_1x1_down/relu')
    up_inputs = tf.layers.conv2d(down_inputs_relu, input_filters * 2, (1, 1), use_bias=True, name=name_prefix + '_1x1_up', strides=(1, 1), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
    prob_outputs = tf.nn.sigmoid(up_inputs, name=name_prefix + '_prob')
    rescaled_feat = tf.multiply(prob_outputs, increase_inputs_bn, name=name_prefix + '_mul')
    pre_act = tf.add(residuals, rescaled_feat, name=name_prefix + '_add')
    return tf.nn.relu(pre_act, name=name_prefix + '/relu')

def se_cpn_backbone(input_image, istraining, data_format):
    bn_axis = -1 if data_format == 'channels_last' else 1
    if data_format == 'channels_last':
        image_channels = tf.unstack(input_image, axis=-1)
        swaped_input_image = tf.stack([image_channels[2], image_channels[1], image_channels[0]], axis=-1)
    else:
        image_channels = tf.unstack(input_image, axis=1)
        swaped_input_image = tf.stack([image_channels[2], image_channels[1], image_channels[0]], axis=1)
    input_depth = [128, 256, 512, 1024]
    num_units = [3, 4, 6, 3]
    block_name_prefix = ['conv2_{}', 'conv3_{}', 'conv4_{}', 'conv5_{}']
    if data_format == 'channels_first':
        swaped_input_image = tf.pad(swaped_input_image, paddings=[[0, 0], [0, 0], [3, 3], [3, 3]])
    else:
        swaped_input_image = tf.pad(swaped_input_image, paddings=[[0, 0], [3, 3], [3, 3], [0, 0]])
    inputs_features = tf.layers.conv2d(swaped_input_image, input_depth[0] // 2, (7, 7), use_bias=False, name='conv1/7x7_s2', strides=(2, 2), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
    inputs_features = tf.layers.batch_normalization(inputs_features, momentum=_BATCH_NORM_DECAY, name='conv1/7x7_s2/bn', axis=bn_axis, epsilon=_BATCH_NORM_EPSILON, training=istraining, reuse=None, fused=_USE_FUSED_BN)
    inputs_features = tf.nn.relu(inputs_features, name='conv1/relu_7x7_s2')
    inputs_features = tf.layers.max_pooling2d(inputs_features, [3, 3], [2, 2], padding='same', data_format=data_format, name='pool1/3x3_s2')
    end_points = []
    is_root = True
    for ind, num_unit in enumerate(num_units):
        need_reduce = True
        for unit_index in range(1, num_unit + 1):
            inputs_features = se_bottleneck_block(inputs_features, input_depth[ind], block_name_prefix[ind].format(unit_index), is_training=istraining, data_format=data_format, need_reduce=need_reduce, is_root=is_root)
            need_reduce = False
            is_root = False
        end_points.append(inputs_features)
    return end_points

def global_net_sext_bottleneck_block(inputs, input_filters, is_training, data_format, need_reduce=False, name_prefix=None, group=32, reduced_scale=16):
    with tf.variable_scope(name_prefix, 'global_net_sext_bottleneck_block', values=[inputs]):
        bn_axis = -1 if data_format == 'channels_last' else 1
        residuals = inputs
        if need_reduce:
            proj_mapping = tf.layers.conv2d(inputs, input_filters * 2, (1, 1), use_bias=False, name=name_prefix + '_1x1_proj', strides=(1, 1), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
            residuals = tf.layers.batch_normalization(proj_mapping, momentum=_BATCH_NORM_DECAY, name=name_prefix + '_1x1_proj/bn', axis=bn_axis, epsilon=_BATCH_NORM_EPSILON, training=is_training, reuse=None, fused=_USE_FUSED_BN)
        reduced_inputs = tf.layers.conv2d(inputs, input_filters, (1, 1), use_bias=False, name=name_prefix + '_1x1_reduce', strides=(1, 1), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
        reduced_inputs_bn = tf.layers.batch_normalization(reduced_inputs, momentum=_BATCH_NORM_DECAY, name=name_prefix + '_1x1_reduce/bn', axis=bn_axis, epsilon=_BATCH_NORM_EPSILON, training=is_training, reuse=None, fused=_USE_FUSED_BN)
        reduced_inputs_relu = tf.nn.relu(reduced_inputs_bn, name=name_prefix + '_1x1_reduce/relu')
        if data_format == 'channels_first':
            reduced_inputs_relu = tf.pad(reduced_inputs_relu, paddings=[[0, 0], [0, 0], [1, 1], [1, 1]])
            weight_shape = [3, 3, reduced_inputs_relu.get_shape().as_list()[1] // group, input_filters]
            if is_training:
                weight_ = tf.Variable(constant_xavier_initializer(weight_shape, group=group, dtype=tf.float32), trainable=is_training, name=name_prefix + '_3x3/kernel')
            else:
                weight_ = tf.get_variable(name_prefix + '_3x3/kernel', shape=weight_shape, initializer=wrapper_initlizer, trainable=is_training)
            weight_groups = tf.split(weight_, num_or_size_splits=group, axis=-1, name=name_prefix + '_weight_split')
            xs = tf.split(reduced_inputs_relu, num_or_size_splits=group, axis=1, name=name_prefix + '_inputs_split')
        else:
            reduced_inputs_relu = tf.pad(reduced_inputs_relu, paddings=[[0, 0], [1, 1], [1, 1], [0, 0]])
            weight_shape = [3, 3, reduced_inputs_relu.get_shape().as_list()[-1] // group, input_filters]
            if is_training:
                weight_ = tf.Variable(constant_xavier_initializer(weight_shape, group=group, dtype=tf.float32), trainable=is_training, name=name_prefix + '_3x3/kernel')
            else:
                weight_ = tf.get_variable(name_prefix + '_3x3/kernel', shape=weight_shape, initializer=wrapper_initlizer, trainable=is_training)
            weight_groups = tf.split(weight_, num_or_size_splits=group, axis=-1, name=name_prefix + '_weight_split')
            xs = tf.split(reduced_inputs_relu, num_or_size_splits=group, axis=-1, name=name_prefix + '_inputs_split')
        convolved = [tf.nn.convolution(x, weight, padding='VALID', strides=[1, 1], name=name_prefix + '_group_conv', data_format='NCHW' if data_format == 'channels_first' else 'NHWC') for x, weight in zip(xs, weight_groups)]
        if data_format == 'channels_first':
            conv3_inputs = tf.concat(convolved, axis=1, name=name_prefix + '_concat')
        else:
            conv3_inputs = tf.concat(convolved, axis=-1, name=name_prefix + '_concat')
        conv3_inputs_bn = tf.layers.batch_normalization(conv3_inputs, momentum=_BATCH_NORM_DECAY, name=name_prefix + '_3x3/bn', axis=bn_axis, epsilon=_BATCH_NORM_EPSILON, training=is_training, reuse=None, fused=_USE_FUSED_BN)
        conv3_inputs_relu = tf.nn.relu(conv3_inputs_bn, name=name_prefix + '_3x3/relu')
        increase_inputs = tf.layers.conv2d(conv3_inputs_relu, input_filters * 2, (1, 1), use_bias=False, name=name_prefix + '_1x1_increase', strides=(1, 1), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
        increase_inputs_bn = tf.layers.batch_normalization(increase_inputs, momentum=_BATCH_NORM_DECAY, name=name_prefix + '_1x1_increase/bn', axis=bn_axis, epsilon=_BATCH_NORM_EPSILON, training=is_training, reuse=None, fused=_USE_FUSED_BN)
        if data_format == 'channels_first':
            pooled_inputs = tf.reduce_mean(increase_inputs_bn, [2, 3], name=name_prefix + '_global_pool', keep_dims=True)
        else:
            pooled_inputs = tf.reduce_mean(increase_inputs_bn, [1, 2], name=name_prefix + '_global_pool', keep_dims=True)
        down_inputs = tf.layers.conv2d(pooled_inputs, input_filters * 2 // reduced_scale, (1, 1), use_bias=True, name=name_prefix + '_1x1_down', strides=(1, 1), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
        down_inputs_relu = tf.nn.relu(down_inputs, name=name_prefix + '_1x1_down/relu')
        up_inputs = tf.layers.conv2d(down_inputs_relu, input_filters * 2, (1, 1), use_bias=True, name=name_prefix + '_1x1_up', strides=(1, 1), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
        prob_outputs = tf.nn.sigmoid(up_inputs, name=name_prefix + '_prob')
        rescaled_feat = tf.multiply(prob_outputs, increase_inputs_bn, name=name_prefix + '_mul')
        pre_act = tf.add(residuals, rescaled_feat, name=name_prefix + '_add')
        return tf.nn.relu(pre_act, name=name_prefix + '/relu')

def batch_norm(inputs, training, data_format, name=None):
    """Performs a batch normalization using a standard set of parameters."""
    return tf.layers.batch_normalization(inputs=inputs, axis=1 if data_format == 'channels_first' else 3, momentum=_BATCH_NORM_DECAY, epsilon=_BATCH_NORM_EPSILON, center=True, scale=True, training=training, name=name, fused=_USE_FUSED_BN)

def fixed_padding(inputs, kernel_size, data_format):
    """Pads the input along the spatial dimensions independently of input size.

    Args:
      inputs: A tensor of size [batch, channels, height_in, width_in] or
        [batch, height_in, width_in, channels] depending on data_format.
      kernel_size: The kernel to be used in the conv2d or max_pool2d operation.
                   Should be a positive integer.
      data_format: The input format ('channels_last' or 'channels_first').

    Returns:
      A tensor with the same format as the input with the data either intact
      (if kernel_size == 1) or padded (if kernel_size > 1).
    """
    pad_total = kernel_size - 1
    pad_beg = pad_total // 2
    pad_end = pad_total - pad_beg
    if data_format == 'channels_first':
        padded_inputs = tf.pad(inputs, [[0, 0], [0, 0], [pad_beg, pad_end], [pad_beg, pad_end]])
    else:
        padded_inputs = tf.pad(inputs, [[0, 0], [pad_beg, pad_end], [pad_beg, pad_end], [0, 0]])
    return padded_inputs

def conv2d_fixed_padding(inputs, filters, kernel_size, strides, data_format, kernel_initializer=tf.glorot_uniform_initializer, name=None):
    """Strided 2-D convolution with explicit padding."""
    if strides > 1:
        inputs = fixed_padding(inputs, kernel_size, data_format)
    return tf.layers.conv2d(inputs=inputs, filters=filters, kernel_size=kernel_size, strides=strides, padding='SAME' if strides == 1 else 'VALID', use_bias=False, kernel_initializer=kernel_initializer(), data_format=data_format, name=name)

def batch_norm(inputs, training, data_format, name=None):
    """Performs a batch normalization using a standard set of parameters."""
    return tf.layers.batch_normalization(inputs=inputs, axis=1 if data_format == 'channels_first' else 3, momentum=_BATCH_NORM_DECAY, epsilon=_BATCH_NORM_EPSILON, center=True, scale=True, training=training, name=name, fused=_USE_FUSED_BN)

def fixed_padding(inputs, kernel_size, data_format):
    """Pads the input along the spatial dimensions independently of input size.

    Args:
      inputs: A tensor of size [batch, channels, height_in, width_in] or
        [batch, height_in, width_in, channels] depending on data_format.
      kernel_size: The kernel to be used in the conv2d or max_pool2d operation.
                   Should be a positive integer.
      data_format: The input format ('channels_last' or 'channels_first').

    Returns:
      A tensor with the same format as the input with the data either intact
      (if kernel_size == 1) or padded (if kernel_size > 1).
    """
    pad_total = kernel_size - 1
    pad_beg = pad_total // 2
    pad_end = pad_total - pad_beg
    if data_format == 'channels_first':
        padded_inputs = tf.pad(inputs, [[0, 0], [0, 0], [pad_beg, pad_end], [pad_beg, pad_end]])
    else:
        padded_inputs = tf.pad(inputs, [[0, 0], [pad_beg, pad_end], [pad_beg, pad_end], [0, 0]])
    return padded_inputs

def conv2d_fixed_padding(inputs, filters, kernel_size, strides, data_format, kernel_initializer=tf.glorot_uniform_initializer, name=None):
    """Strided 2-D convolution with explicit padding."""
    if strides > 1:
        inputs = fixed_padding(inputs, kernel_size, data_format)
    return tf.layers.conv2d(inputs=inputs, filters=filters, kernel_size=kernel_size, strides=strides, padding='SAME' if strides == 1 else 'VALID', use_bias=False, kernel_initializer=kernel_initializer(), data_format=data_format, name=name)

def wrapper_initlizer(shape, dtype=None, partition_info=None):
    return constant_xavier_initializer(shape, 32, dtype)

def se_next_bottleneck_block(inputs, input_filters, name_prefix, is_training, group, data_format='channels_last', need_reduce=True, is_root=False, reduced_scale=16):
    bn_axis = -1 if data_format == 'channels_last' else 1
    strides_to_use = 1
    residuals = inputs
    if need_reduce:
        strides_to_use = 1 if is_root else 2
        proj_mapping = tf.layers.conv2d(inputs, input_filters, (1, 1), use_bias=False, name=name_prefix + '_1x1_proj', strides=(strides_to_use, strides_to_use), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
        residuals = tf.layers.batch_normalization(proj_mapping, momentum=_BATCH_NORM_DECAY, name=name_prefix + '_1x1_proj/bn', axis=bn_axis, epsilon=_BATCH_NORM_EPSILON, training=is_training, reuse=None, fused=_USE_FUSED_BN)
    reduced_inputs = tf.layers.conv2d(inputs, input_filters // 2, (1, 1), use_bias=False, name=name_prefix + '_1x1_reduce', strides=(1, 1), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
    reduced_inputs_bn = tf.layers.batch_normalization(reduced_inputs, momentum=_BATCH_NORM_DECAY, name=name_prefix + '_1x1_reduce/bn', axis=bn_axis, epsilon=_BATCH_NORM_EPSILON, training=is_training, reuse=None, fused=_USE_FUSED_BN)
    reduced_inputs_relu = tf.nn.relu(reduced_inputs_bn, name=name_prefix + '_1x1_reduce/relu')
    if data_format == 'channels_first':
        reduced_inputs_relu = tf.pad(reduced_inputs_relu, paddings=[[0, 0], [0, 0], [1, 1], [1, 1]])
        weight_shape = [3, 3, reduced_inputs_relu.get_shape().as_list()[1] // group, input_filters // 2]
        if is_training:
            weight_ = tf.Variable(constant_xavier_initializer(weight_shape, group=group, dtype=tf.float32), trainable=is_training, name=name_prefix + '_3x3/kernel')
        else:
            weight_ = tf.get_variable(name_prefix + '_3x3/kernel', shape=weight_shape, initializer=wrapper_initlizer, trainable=is_training)
        weight_groups = tf.split(weight_, num_or_size_splits=group, axis=-1, name=name_prefix + '_weight_split')
        xs = tf.split(reduced_inputs_relu, num_or_size_splits=group, axis=1, name=name_prefix + '_inputs_split')
    else:
        reduced_inputs_relu = tf.pad(reduced_inputs_relu, paddings=[[0, 0], [1, 1], [1, 1], [0, 0]])
        weight_shape = [3, 3, reduced_inputs_relu.get_shape().as_list()[-1] // group, input_filters // 2]
        if is_training:
            weight_ = tf.Variable(constant_xavier_initializer(weight_shape, group=group, dtype=tf.float32), trainable=is_training, name=name_prefix + '_3x3/kernel')
        else:
            weight_ = tf.get_variable(name_prefix + '_3x3/kernel', shape=weight_shape, initializer=wrapper_initlizer, trainable=is_training)
        weight_groups = tf.split(weight_, num_or_size_splits=group, axis=-1, name=name_prefix + '_weight_split')
        xs = tf.split(reduced_inputs_relu, num_or_size_splits=group, axis=-1, name=name_prefix + '_inputs_split')
    convolved = [tf.nn.convolution(x, weight, padding='VALID', strides=[strides_to_use, strides_to_use], name=name_prefix + '_group_conv', data_format='NCHW' if data_format == 'channels_first' else 'NHWC') for x, weight in zip(xs, weight_groups)]
    if data_format == 'channels_first':
        conv3_inputs = tf.concat(convolved, axis=1, name=name_prefix + '_concat')
    else:
        conv3_inputs = tf.concat(convolved, axis=-1, name=name_prefix + '_concat')
    conv3_inputs_bn = tf.layers.batch_normalization(conv3_inputs, momentum=_BATCH_NORM_DECAY, name=name_prefix + '_3x3/bn', axis=bn_axis, epsilon=_BATCH_NORM_EPSILON, training=is_training, reuse=None, fused=_USE_FUSED_BN)
    conv3_inputs_relu = tf.nn.relu(conv3_inputs_bn, name=name_prefix + '_3x3/relu')
    increase_inputs = tf.layers.conv2d(conv3_inputs_relu, input_filters, (1, 1), use_bias=False, name=name_prefix + '_1x1_increase', strides=(1, 1), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
    increase_inputs_bn = tf.layers.batch_normalization(increase_inputs, momentum=_BATCH_NORM_DECAY, name=name_prefix + '_1x1_increase/bn', axis=bn_axis, epsilon=_BATCH_NORM_EPSILON, training=is_training, reuse=None, fused=_USE_FUSED_BN)
    if data_format == 'channels_first':
        pooled_inputs = tf.reduce_mean(increase_inputs_bn, [2, 3], name=name_prefix + '_global_pool', keep_dims=True)
    else:
        pooled_inputs = tf.reduce_mean(increase_inputs_bn, [1, 2], name=name_prefix + '_global_pool', keep_dims=True)
    down_inputs = tf.layers.conv2d(pooled_inputs, input_filters // reduced_scale, (1, 1), use_bias=True, name=name_prefix + '_1x1_down', strides=(1, 1), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
    down_inputs_relu = tf.nn.relu(down_inputs, name=name_prefix + '_1x1_down/relu')
    up_inputs = tf.layers.conv2d(down_inputs_relu, input_filters, (1, 1), use_bias=True, name=name_prefix + '_1x1_up', strides=(1, 1), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
    prob_outputs = tf.nn.sigmoid(up_inputs, name=name_prefix + '_prob')
    rescaled_feat = tf.multiply(prob_outputs, increase_inputs_bn, name=name_prefix + '_mul')
    pre_act = tf.add(residuals, rescaled_feat, name=name_prefix + '_add')
    return tf.nn.relu(pre_act, name=name_prefix + '/relu')

def dilated_se_next_bottleneck_block(inputs, input_filters, name_prefix, is_training, group, data_format='channels_last', need_reduce=True, reduced_scale=16):
    bn_axis = -1 if data_format == 'channels_last' else 1
    residuals = inputs
    if need_reduce:
        proj_mapping = tf.layers.conv2d(inputs, input_filters, (1, 1), use_bias=False, name=name_prefix + '_1x1_proj', strides=(1, 1), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
        residuals = tf.layers.batch_normalization(proj_mapping, momentum=_BATCH_NORM_DECAY, name=name_prefix + '_1x1_proj/bn', axis=bn_axis, epsilon=_BATCH_NORM_EPSILON, training=is_training, reuse=None, fused=_USE_FUSED_BN)
    reduced_inputs = tf.layers.conv2d(inputs, input_filters // 2, (1, 1), use_bias=False, name=name_prefix + '_1x1_reduce', strides=(1, 1), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
    reduced_inputs_bn = tf.layers.batch_normalization(reduced_inputs, momentum=_BATCH_NORM_DECAY, name=name_prefix + '_1x1_reduce/bn', axis=bn_axis, epsilon=_BATCH_NORM_EPSILON, training=is_training, reuse=None, fused=_USE_FUSED_BN)
    reduced_inputs_relu = tf.nn.relu(reduced_inputs_bn, name=name_prefix + '_1x1_reduce/relu')
    if data_format == 'channels_first':
        weight_shape = [3, 3, reduced_inputs_relu.get_shape().as_list()[1] // group, input_filters // 2]
        if is_training:
            weight_ = tf.Variable(constant_xavier_initializer(weight_shape, group=group, dtype=tf.float32), trainable=is_training, name=name_prefix + '_3x3/kernel')
        else:
            weight_ = tf.get_variable(name_prefix + '_3x3/kernel', shape=weight_shape, initializer=wrapper_initlizer, trainable=is_training)
        weight_groups = tf.split(weight_, num_or_size_splits=group, axis=-1, name=name_prefix + '_weight_split')
        xs = tf.split(reduced_inputs_relu, num_or_size_splits=group, axis=1, name=name_prefix + '_inputs_split')
    else:
        weight_shape = [3, 3, reduced_inputs_relu.get_shape().as_list()[-1] // group, input_filters // 2]
        if is_training:
            weight_ = tf.Variable(constant_xavier_initializer(weight_shape, group=group, dtype=tf.float32), trainable=is_training, name=name_prefix + '_3x3/kernel')
        else:
            weight_ = tf.get_variable(name_prefix + '_3x3/kernel', shape=weight_shape, initializer=wrapper_initlizer, trainable=is_training)
        weight_groups = tf.split(weight_, num_or_size_splits=group, axis=-1, name=name_prefix + '_weight_split')
        xs = tf.split(reduced_inputs_relu, num_or_size_splits=group, axis=-1, name=name_prefix + '_inputs_split')
    convolved = [tf.nn.convolution(x, weight, padding='SAME', strides=[1, 1], dilation_rate=[2, 2], name=name_prefix + '_group_conv', data_format='NCHW' if data_format == 'channels_first' else 'NHWC') for x, weight in zip(xs, weight_groups)]
    if data_format == 'channels_first':
        conv3_inputs = tf.concat(convolved, axis=1, name=name_prefix + '_concat')
    else:
        conv3_inputs = tf.concat(convolved, axis=-1, name=name_prefix + '_concat')
    conv3_inputs_bn = tf.layers.batch_normalization(conv3_inputs, momentum=_BATCH_NORM_DECAY, name=name_prefix + '_3x3/bn', axis=bn_axis, epsilon=_BATCH_NORM_EPSILON, training=is_training, reuse=None, fused=_USE_FUSED_BN)
    conv3_inputs_relu = tf.nn.relu(conv3_inputs_bn, name=name_prefix + '_3x3/relu')
    increase_inputs = tf.layers.conv2d(conv3_inputs_relu, input_filters, (1, 1), use_bias=False, name=name_prefix + '_1x1_increase', strides=(1, 1), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
    increase_inputs_bn = tf.layers.batch_normalization(increase_inputs, momentum=_BATCH_NORM_DECAY, name=name_prefix + '_1x1_increase/bn', axis=bn_axis, epsilon=_BATCH_NORM_EPSILON, training=is_training, reuse=None, fused=_USE_FUSED_BN)
    if data_format == 'channels_first':
        pooled_inputs = tf.reduce_mean(increase_inputs_bn, [2, 3], name=name_prefix + '_global_pool', keep_dims=True)
    else:
        pooled_inputs = tf.reduce_mean(increase_inputs_bn, [1, 2], name=name_prefix + '_global_pool', keep_dims=True)
    down_inputs = tf.layers.conv2d(pooled_inputs, input_filters // reduced_scale, (1, 1), use_bias=True, name=name_prefix + '_1x1_down', strides=(1, 1), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
    down_inputs_relu = tf.nn.relu(down_inputs, name=name_prefix + '_1x1_down/relu')
    up_inputs = tf.layers.conv2d(down_inputs_relu, input_filters, (1, 1), use_bias=True, name=name_prefix + '_1x1_up', strides=(1, 1), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
    prob_outputs = tf.nn.sigmoid(up_inputs, name=name_prefix + '_prob')
    rescaled_feat = tf.multiply(prob_outputs, increase_inputs_bn, name=name_prefix + '_mul')
    pre_act = tf.add(residuals, rescaled_feat, name=name_prefix + '_add')
    return tf.nn.relu(pre_act, name=name_prefix + '/relu')

def sext_backbone(input_image, istraining, data_format, net_depth=101, group=32):
    bn_axis = -1 if data_format == 'channels_last' else 1
    if data_format == 'channels_last':
        image_channels = tf.unstack(input_image, axis=-1)
        swaped_input_image = tf.stack([image_channels[2], image_channels[1], image_channels[0]], axis=-1)
    else:
        image_channels = tf.unstack(input_image, axis=1)
        swaped_input_image = tf.stack([image_channels[2], image_channels[1], image_channels[0]], axis=1)
    if net_depth not in [50, 101]:
        raise TypeError('Only ResNeXt50 or ResNeXt101 is supprted now.')
    input_depth = [256, 512, 1024]
    num_units = [3, 4, 6] if net_depth == 50 else [3, 4, 23]
    block_name_prefix = ['conv2_{}', 'conv3_{}', 'conv4_{}']
    if data_format == 'channels_first':
        swaped_input_image = tf.pad(swaped_input_image, paddings=[[0, 0], [0, 0], [3, 3], [3, 3]])
    else:
        swaped_input_image = tf.pad(swaped_input_image, paddings=[[0, 0], [3, 3], [3, 3], [0, 0]])
    inputs_features = tf.layers.conv2d(swaped_input_image, input_depth[0] // 4, (7, 7), use_bias=False, name='conv1/7x7_s2', strides=(2, 2), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
    inputs_features = tf.layers.batch_normalization(inputs_features, momentum=_BATCH_NORM_DECAY, name='conv1/7x7_s2/bn', axis=bn_axis, epsilon=_BATCH_NORM_EPSILON, training=istraining, reuse=None, fused=_USE_FUSED_BN)
    inputs_features = tf.nn.relu(inputs_features, name='conv1/relu_7x7_s2')
    inputs_features = tf.layers.max_pooling2d(inputs_features, [3, 3], [2, 2], padding='same', data_format=data_format, name='pool1/3x3_s2')
    end_points = []
    is_root = True
    for ind, num_unit in enumerate(num_units):
        need_reduce = True
        for unit_index in range(1, num_unit + 1):
            inputs_features = se_next_bottleneck_block(inputs_features, input_depth[ind], block_name_prefix[ind].format(unit_index), is_training=istraining, group=group, data_format=data_format, need_reduce=need_reduce, is_root=is_root)
            need_reduce = False
            is_root = False
        end_points.append(inputs_features)
    need_reduce = True
    for unit_index in range(1, 4):
        inputs_features = dilated_se_next_bottleneck_block(inputs_features, 2048, 'conv5_{}'.format(unit_index), is_training=istraining, group=group, data_format=data_format, need_reduce=need_reduce)
        need_reduce = False
    end_points.append(inputs_features)
    return end_points

def simple_net(inputs, output_channals, heatmap_size, istraining, data_format, net_depth=101):
    end_points = sext_backbone(inputs, istraining, data_format, net_depth=net_depth)
    bn_axis = -1 if data_format == 'channels_last' else 1
    with tf.variable_scope('additional_layer', 'additional_layer', values=end_points, reuse=None):
        inputs_features = tf.layers.conv2d_transpose(end_points[-1], 256, 4, strides=(2, 2), padding='same', data_format=data_format, activation=None, use_bias=False, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=None, kernel_regularizer=None, bias_regularizer=None, activity_regularizer=None, kernel_constraint=None, bias_constraint=None, trainable=istraining, name='deconv_1', reuse=None)
        inputs_features = tf.layers.batch_normalization(inputs_features, momentum=_BATCH_NORM_DECAY, name='deconv_1_bn', axis=bn_axis, epsilon=_BATCH_NORM_EPSILON, training=istraining, reuse=None, fused=_USE_FUSED_BN)
        inputs_features = tf.nn.relu(inputs_features, name='deconv_1_relu')
        inputs_features = tf.layers.conv2d_transpose(inputs_features, 256, 4, strides=(2, 2), padding='same', data_format=data_format, activation=None, use_bias=False, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=None, kernel_regularizer=None, bias_regularizer=None, activity_regularizer=None, kernel_constraint=None, bias_constraint=None, trainable=istraining, name='deconv_2', reuse=None)
        inputs_features = tf.layers.batch_normalization(inputs_features, momentum=_BATCH_NORM_DECAY, name='deconv_2_bn', axis=bn_axis, epsilon=_BATCH_NORM_EPSILON, training=istraining, reuse=None, fused=_USE_FUSED_BN)
        inputs_features = tf.nn.relu(inputs_features, name='deconv_2_relu')
        inputs_features = tf.layers.conv2d_transpose(inputs_features, 256, 4, strides=(2, 2), padding='same', data_format=data_format, activation=None, use_bias=False, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=None, kernel_regularizer=None, bias_regularizer=None, activity_regularizer=None, kernel_constraint=None, bias_constraint=None, trainable=istraining, name='deconv_3', reuse=None)
        inputs_features = tf.layers.batch_normalization(inputs_features, momentum=_BATCH_NORM_DECAY, name='deconv_3_bn', axis=bn_axis, epsilon=_BATCH_NORM_EPSILON, training=istraining, reuse=None, fused=_USE_FUSED_BN)
        inputs_features = tf.nn.relu(inputs_features, name='deconv_3_relu')
        heatmap = tf.layers.conv2d(inputs=inputs_features, filters=output_channals, kernel_size=1, strides=1, padding='same', use_bias=True, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer(), data_format=data_format, name='heatmap_1x1')
        return [heatmap]

def batch_norm(inputs, is_training, data_format, name=None):
    """Performs a batch normalization followed by a ReLU."""
    with tf.variable_scope(name, 'batch_norm', values=[inputs]):
        inputs = tf.layers.batch_normalization(inputs=inputs, axis=1 if data_format == 'channels_first' else 3, momentum=_BATCH_NORM_DECAY, epsilon=_BATCH_NORM_EPSILON, center=True, scale=True, training=is_training, fused=_USE_FUSED_BN, name='batch_normalization')
        return inputs

def fixed_padding(inputs, kernel_size, data_format):
    with tf.variable_scope('fixed_padding', values=[inputs]):
        pad_total = kernel_size - 1
        pad_beg = pad_total // 2
        pad_end = pad_total - pad_beg
        if data_format == 'channels_first':
            padded_inputs = tf.pad(inputs, [[0, 0], [0, 0], [pad_beg, pad_end], [pad_beg, pad_end]], name='padding')
        else:
            padded_inputs = tf.pad(inputs, [[0, 0], [pad_beg, pad_end], [pad_beg, pad_end], [0, 0]], name='padding')
        return padded_inputs

def conv2d_fixed_padding(inputs, filters, kernel_size, strides, data_format, kernel_initializer=conv_bn_initializer_to_use, name=None):
    """Strided 2-D convolution with explicit padding."""
    with tf.variable_scope(name, 'fix_padding_conv', values=[inputs]):
        if strides > 1:
            inputs = fixed_padding(inputs, kernel_size, data_format)
        return tf.layers.conv2d(inputs=inputs, filters=filters, kernel_size=kernel_size, strides=strides, padding='same' if strides == 1 else 'valid', use_bias=False, kernel_initializer=kernel_initializer(), data_format=data_format, name='conv2d')

def batch_norm(inputs, training, data_format, name=None):
    """Performs a batch normalization using a standard set of parameters."""
    return tf.layers.batch_normalization(inputs=inputs, axis=1 if data_format == 'channels_first' else 3, momentum=_BATCH_NORM_DECAY, epsilon=_BATCH_NORM_EPSILON, center=True, scale=True, training=training, name=name, fused=_USE_FUSED_BN)

def fixed_padding(inputs, kernel_size, data_format):
    """Pads the input along the spatial dimensions independently of input size.

    Args:
      inputs: A tensor of size [batch, channels, height_in, width_in] or
        [batch, height_in, width_in, channels] depending on data_format.
      kernel_size: The kernel to be used in the conv2d or max_pool2d operation.
                   Should be a positive integer.
      data_format: The input format ('channels_last' or 'channels_first').

    Returns:
      A tensor with the same format as the input with the data either intact
      (if kernel_size == 1) or padded (if kernel_size > 1).
    """
    pad_total = kernel_size - 1
    pad_beg = pad_total // 2
    pad_end = pad_total - pad_beg
    if data_format == 'channels_first':
        padded_inputs = tf.pad(inputs, [[0, 0], [0, 0], [pad_beg, pad_end], [pad_beg, pad_end]])
    else:
        padded_inputs = tf.pad(inputs, [[0, 0], [pad_beg, pad_end], [pad_beg, pad_end], [0, 0]])
    return padded_inputs

def conv2d_fixed_padding(inputs, filters, kernel_size, strides, data_format, kernel_initializer=tf.glorot_uniform_initializer, name=None):
    """Strided 2-D convolution with explicit padding."""
    if strides > 1:
        inputs = fixed_padding(inputs, kernel_size, data_format)
    return tf.layers.conv2d(inputs=inputs, filters=filters, kernel_size=kernel_size, strides=strides, padding='SAME' if strides == 1 else 'VALID', use_bias=False, kernel_initializer=kernel_initializer(), data_format=data_format, name=name)

def batch_norm(inputs, training, data_format, name=None):
    """Performs a batch normalization using a standard set of parameters."""
    return tf.layers.batch_normalization(inputs=inputs, axis=1 if data_format == 'channels_first' else 3, momentum=_BATCH_NORM_DECAY, epsilon=_BATCH_NORM_EPSILON, center=True, scale=True, training=training, name=name, fused=_USE_FUSED_BN)

def fixed_padding(inputs, kernel_size, data_format):
    """Pads the input along the spatial dimensions independently of input size.

    Args:
      inputs: A tensor of size [batch, channels, height_in, width_in] or
        [batch, height_in, width_in, channels] depending on data_format.
      kernel_size: The kernel to be used in the conv2d or max_pool2d operation.
                   Should be a positive integer.
      data_format: The input format ('channels_last' or 'channels_first').

    Returns:
      A tensor with the same format as the input with the data either intact
      (if kernel_size == 1) or padded (if kernel_size > 1).
    """
    pad_total = kernel_size - 1
    pad_beg = pad_total // 2
    pad_end = pad_total - pad_beg
    if data_format == 'channels_first':
        padded_inputs = tf.pad(inputs, [[0, 0], [0, 0], [pad_beg, pad_end], [pad_beg, pad_end]])
    else:
        padded_inputs = tf.pad(inputs, [[0, 0], [pad_beg, pad_end], [pad_beg, pad_end], [0, 0]])
    return padded_inputs

def conv2d_fixed_padding(inputs, filters, kernel_size, strides, data_format, kernel_initializer=tf.glorot_uniform_initializer, name=None):
    """Strided 2-D convolution with explicit padding."""
    if strides > 1:
        inputs = fixed_padding(inputs, kernel_size, data_format)
    return tf.layers.conv2d(inputs=inputs, filters=filters, kernel_size=kernel_size, strides=strides, padding='SAME' if strides == 1 else 'VALID', use_bias=False, kernel_initializer=kernel_initializer(), data_format=data_format, name=name)

def wrapper_initlizer(shape, dtype=None, partition_info=None):
    return constant_xavier_initializer(shape, 32, dtype)

def se_next_bottleneck_block(inputs, input_filters, name_prefix, is_training, group, data_format='channels_last', need_reduce=True, is_root=False, reduced_scale=16):
    bn_axis = -1 if data_format == 'channels_last' else 1
    strides_to_use = 1
    residuals = inputs
    if need_reduce:
        strides_to_use = 1 if is_root else 2
        proj_mapping = tf.layers.conv2d(inputs, input_filters, (1, 1), use_bias=False, name=name_prefix + '_1x1_proj', strides=(strides_to_use, strides_to_use), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
        residuals = tf.layers.batch_normalization(proj_mapping, momentum=_BATCH_NORM_DECAY, name=name_prefix + '_1x1_proj/bn', axis=bn_axis, epsilon=_BATCH_NORM_EPSILON, training=is_training, reuse=None, fused=_USE_FUSED_BN)
    reduced_inputs = tf.layers.conv2d(inputs, input_filters // 2, (1, 1), use_bias=False, name=name_prefix + '_1x1_reduce', strides=(1, 1), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
    reduced_inputs_bn = tf.layers.batch_normalization(reduced_inputs, momentum=_BATCH_NORM_DECAY, name=name_prefix + '_1x1_reduce/bn', axis=bn_axis, epsilon=_BATCH_NORM_EPSILON, training=is_training, reuse=None, fused=_USE_FUSED_BN)
    reduced_inputs_relu = tf.nn.relu(reduced_inputs_bn, name=name_prefix + '_1x1_reduce/relu')
    if data_format == 'channels_first':
        reduced_inputs_relu = tf.pad(reduced_inputs_relu, paddings=[[0, 0], [0, 0], [1, 1], [1, 1]])
        weight_shape = [3, 3, reduced_inputs_relu.get_shape().as_list()[1] // group, input_filters // 2]
        if is_training:
            weight_ = tf.Variable(constant_xavier_initializer(weight_shape, group=group, dtype=tf.float32), trainable=is_training, name=name_prefix + '_3x3/kernel')
        else:
            weight_ = tf.get_variable(name_prefix + '_3x3/kernel', shape=weight_shape, initializer=wrapper_initlizer, trainable=is_training)
        weight_groups = tf.split(weight_, num_or_size_splits=group, axis=-1, name=name_prefix + '_weight_split')
        xs = tf.split(reduced_inputs_relu, num_or_size_splits=group, axis=1, name=name_prefix + '_inputs_split')
    else:
        reduced_inputs_relu = tf.pad(reduced_inputs_relu, paddings=[[0, 0], [1, 1], [1, 1], [0, 0]])
        weight_shape = [3, 3, reduced_inputs_relu.get_shape().as_list()[-1] // group, input_filters // 2]
        if is_training:
            weight_ = tf.Variable(constant_xavier_initializer(weight_shape, group=group, dtype=tf.float32), trainable=is_training, name=name_prefix + '_3x3/kernel')
        else:
            weight_ = tf.get_variable(name_prefix + '_3x3/kernel', shape=weight_shape, initializer=wrapper_initlizer, trainable=is_training)
        weight_groups = tf.split(weight_, num_or_size_splits=group, axis=-1, name=name_prefix + '_weight_split')
        xs = tf.split(reduced_inputs_relu, num_or_size_splits=group, axis=-1, name=name_prefix + '_inputs_split')
    convolved = [tf.nn.convolution(x, weight, padding='VALID', strides=[strides_to_use, strides_to_use], name=name_prefix + '_group_conv', data_format='NCHW' if data_format == 'channels_first' else 'NHWC') for x, weight in zip(xs, weight_groups)]
    if data_format == 'channels_first':
        conv3_inputs = tf.concat(convolved, axis=1, name=name_prefix + '_concat')
    else:
        conv3_inputs = tf.concat(convolved, axis=-1, name=name_prefix + '_concat')
    conv3_inputs_bn = tf.layers.batch_normalization(conv3_inputs, momentum=_BATCH_NORM_DECAY, name=name_prefix + '_3x3/bn', axis=bn_axis, epsilon=_BATCH_NORM_EPSILON, training=is_training, reuse=None, fused=_USE_FUSED_BN)
    conv3_inputs_relu = tf.nn.relu(conv3_inputs_bn, name=name_prefix + '_3x3/relu')
    increase_inputs = tf.layers.conv2d(conv3_inputs_relu, input_filters, (1, 1), use_bias=False, name=name_prefix + '_1x1_increase', strides=(1, 1), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
    increase_inputs_bn = tf.layers.batch_normalization(increase_inputs, momentum=_BATCH_NORM_DECAY, name=name_prefix + '_1x1_increase/bn', axis=bn_axis, epsilon=_BATCH_NORM_EPSILON, training=is_training, reuse=None, fused=_USE_FUSED_BN)
    if data_format == 'channels_first':
        pooled_inputs = tf.reduce_mean(increase_inputs_bn, [2, 3], name=name_prefix + '_global_pool', keep_dims=True)
    else:
        pooled_inputs = tf.reduce_mean(increase_inputs_bn, [1, 2], name=name_prefix + '_global_pool', keep_dims=True)
    down_inputs = tf.layers.conv2d(pooled_inputs, input_filters // reduced_scale, (1, 1), use_bias=True, name=name_prefix + '_1x1_down', strides=(1, 1), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
    down_inputs_relu = tf.nn.relu(down_inputs, name=name_prefix + '_1x1_down/relu')
    up_inputs = tf.layers.conv2d(down_inputs_relu, input_filters, (1, 1), use_bias=True, name=name_prefix + '_1x1_up', strides=(1, 1), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
    prob_outputs = tf.nn.sigmoid(up_inputs, name=name_prefix + '_prob')
    rescaled_feat = tf.multiply(prob_outputs, increase_inputs_bn, name=name_prefix + '_mul')
    pre_act = tf.add(residuals, rescaled_feat, name=name_prefix + '_add')
    return tf.nn.relu(pre_act, name=name_prefix + '/relu')

def dilated_se_next_bottleneck_block(inputs, input_filters, name_prefix, is_training, group, data_format='channels_last', need_reduce=True, reduced_scale=16):
    bn_axis = -1 if data_format == 'channels_last' else 1
    residuals = inputs
    if need_reduce:
        proj_mapping = tf.layers.conv2d(inputs, input_filters, (1, 1), use_bias=False, name=name_prefix + '_1x1_proj', strides=(1, 1), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
        residuals = tf.layers.batch_normalization(proj_mapping, momentum=_BATCH_NORM_DECAY, name=name_prefix + '_1x1_proj/bn', axis=bn_axis, epsilon=_BATCH_NORM_EPSILON, training=is_training, reuse=None, fused=_USE_FUSED_BN)
    reduced_inputs = tf.layers.conv2d(inputs, input_filters // 2, (1, 1), use_bias=False, name=name_prefix + '_1x1_reduce', strides=(1, 1), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
    reduced_inputs_bn = tf.layers.batch_normalization(reduced_inputs, momentum=_BATCH_NORM_DECAY, name=name_prefix + '_1x1_reduce/bn', axis=bn_axis, epsilon=_BATCH_NORM_EPSILON, training=is_training, reuse=None, fused=_USE_FUSED_BN)
    reduced_inputs_relu = tf.nn.relu(reduced_inputs_bn, name=name_prefix + '_1x1_reduce/relu')
    if data_format == 'channels_first':
        weight_shape = [3, 3, reduced_inputs_relu.get_shape().as_list()[1] // group, input_filters // 2]
        if is_training:
            weight_ = tf.Variable(constant_xavier_initializer(weight_shape, group=group, dtype=tf.float32), trainable=is_training, name=name_prefix + '_3x3/kernel')
        else:
            weight_ = tf.get_variable(name_prefix + '_3x3/kernel', shape=weight_shape, initializer=wrapper_initlizer, trainable=is_training)
        weight_groups = tf.split(weight_, num_or_size_splits=group, axis=-1, name=name_prefix + '_weight_split')
        xs = tf.split(reduced_inputs_relu, num_or_size_splits=group, axis=1, name=name_prefix + '_inputs_split')
    else:
        weight_shape = [3, 3, reduced_inputs_relu.get_shape().as_list()[-1] // group, input_filters // 2]
        if is_training:
            weight_ = tf.Variable(constant_xavier_initializer(weight_shape, group=group, dtype=tf.float32), trainable=is_training, name=name_prefix + '_3x3/kernel')
        else:
            weight_ = tf.get_variable(name_prefix + '_3x3/kernel', shape=weight_shape, initializer=wrapper_initlizer, trainable=is_training)
        weight_groups = tf.split(weight_, num_or_size_splits=group, axis=-1, name=name_prefix + '_weight_split')
        xs = tf.split(reduced_inputs_relu, num_or_size_splits=group, axis=-1, name=name_prefix + '_inputs_split')
    convolved = [tf.nn.convolution(x, weight, padding='SAME', strides=[1, 1], dilation_rate=[2, 2], name=name_prefix + '_group_conv', data_format='NCHW' if data_format == 'channels_first' else 'NHWC') for x, weight in zip(xs, weight_groups)]
    if data_format == 'channels_first':
        conv3_inputs = tf.concat(convolved, axis=1, name=name_prefix + '_concat')
    else:
        conv3_inputs = tf.concat(convolved, axis=-1, name=name_prefix + '_concat')
    conv3_inputs_bn = tf.layers.batch_normalization(conv3_inputs, momentum=_BATCH_NORM_DECAY, name=name_prefix + '_3x3/bn', axis=bn_axis, epsilon=_BATCH_NORM_EPSILON, training=is_training, reuse=None, fused=_USE_FUSED_BN)
    conv3_inputs_relu = tf.nn.relu(conv3_inputs_bn, name=name_prefix + '_3x3/relu')
    increase_inputs = tf.layers.conv2d(conv3_inputs_relu, input_filters, (1, 1), use_bias=False, name=name_prefix + '_1x1_increase', strides=(1, 1), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
    increase_inputs_bn = tf.layers.batch_normalization(increase_inputs, momentum=_BATCH_NORM_DECAY, name=name_prefix + '_1x1_increase/bn', axis=bn_axis, epsilon=_BATCH_NORM_EPSILON, training=is_training, reuse=None, fused=_USE_FUSED_BN)
    if data_format == 'channels_first':
        pooled_inputs = tf.reduce_mean(increase_inputs_bn, [2, 3], name=name_prefix + '_global_pool', keep_dims=True)
    else:
        pooled_inputs = tf.reduce_mean(increase_inputs_bn, [1, 2], name=name_prefix + '_global_pool', keep_dims=True)
    down_inputs = tf.layers.conv2d(pooled_inputs, input_filters // reduced_scale, (1, 1), use_bias=True, name=name_prefix + '_1x1_down', strides=(1, 1), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
    down_inputs_relu = tf.nn.relu(down_inputs, name=name_prefix + '_1x1_down/relu')
    up_inputs = tf.layers.conv2d(down_inputs_relu, input_filters, (1, 1), use_bias=True, name=name_prefix + '_1x1_up', strides=(1, 1), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
    prob_outputs = tf.nn.sigmoid(up_inputs, name=name_prefix + '_prob')
    rescaled_feat = tf.multiply(prob_outputs, increase_inputs_bn, name=name_prefix + '_mul')
    pre_act = tf.add(residuals, rescaled_feat, name=name_prefix + '_add')
    return tf.nn.relu(pre_act, name=name_prefix + '/relu')

def sext_cpn_backbone(input_image, istraining, data_format, net_depth=50, group=32):
    bn_axis = -1 if data_format == 'channels_last' else 1
    if data_format == 'channels_last':
        image_channels = tf.unstack(input_image, axis=-1)
        swaped_input_image = tf.stack([image_channels[2], image_channels[1], image_channels[0]], axis=-1)
    else:
        image_channels = tf.unstack(input_image, axis=1)
        swaped_input_image = tf.stack([image_channels[2], image_channels[1], image_channels[0]], axis=1)
    if net_depth not in [50, 101]:
        raise TypeError('Only ResNeXt50 or ResNeXt101 is supprted now.')
    input_depth = [256, 512, 1024]
    num_units = [3, 4, 6] if net_depth == 50 else [3, 4, 23]
    block_name_prefix = ['conv2_{}', 'conv3_{}', 'conv4_{}']
    if data_format == 'channels_first':
        swaped_input_image = tf.pad(swaped_input_image, paddings=[[0, 0], [0, 0], [3, 3], [3, 3]])
    else:
        swaped_input_image = tf.pad(swaped_input_image, paddings=[[0, 0], [3, 3], [3, 3], [0, 0]])
    inputs_features = tf.layers.conv2d(swaped_input_image, input_depth[0] // 4, (7, 7), use_bias=False, name='conv1/7x7_s2', strides=(2, 2), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
    inputs_features = tf.layers.batch_normalization(inputs_features, momentum=_BATCH_NORM_DECAY, name='conv1/7x7_s2/bn', axis=bn_axis, epsilon=_BATCH_NORM_EPSILON, training=istraining, reuse=None, fused=_USE_FUSED_BN)
    inputs_features = tf.nn.relu(inputs_features, name='conv1/relu_7x7_s2')
    inputs_features = tf.layers.max_pooling2d(inputs_features, [3, 3], [2, 2], padding='same', data_format=data_format, name='pool1/3x3_s2')
    end_points = []
    is_root = True
    for ind, num_unit in enumerate(num_units):
        need_reduce = True
        for unit_index in range(1, num_unit + 1):
            inputs_features = se_next_bottleneck_block(inputs_features, input_depth[ind], block_name_prefix[ind].format(unit_index), is_training=istraining, group=group, data_format=data_format, need_reduce=need_reduce, is_root=is_root)
            need_reduce = False
            is_root = False
        end_points.append(inputs_features)
    with tf.variable_scope('additional_layer', 'additional_layer', values=[inputs_features], reuse=None):
        need_reduce = True
        for unit_index in range(1, 4):
            inputs_features = dilated_se_next_bottleneck_block(inputs_features, 1024, 'conv5_{}'.format(unit_index), is_training=istraining, group=group, data_format=data_format, need_reduce=need_reduce)
            need_reduce = False
        end_points.append(inputs_features)
        need_reduce = True
        for unit_index in range(1, 4):
            inputs_features = dilated_se_next_bottleneck_block(inputs_features, 1024, 'conv6_{}'.format(unit_index), is_training=istraining, group=group, data_format=data_format, need_reduce=need_reduce)
            need_reduce = False
        end_points.append(inputs_features)
    return end_points[1:]

def global_net_sext_bottleneck_block(inputs, input_filters, is_training, data_format, need_reduce=False, name_prefix=None, group=32, reduced_scale=16):
    with tf.variable_scope(name_prefix, 'global_net_sext_bottleneck_block', values=[inputs]):
        bn_axis = -1 if data_format == 'channels_last' else 1
        residuals = inputs
        if need_reduce:
            proj_mapping = tf.layers.conv2d(inputs, input_filters * 2, (1, 1), use_bias=False, name=name_prefix + '_1x1_proj', strides=(1, 1), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
            residuals = tf.layers.batch_normalization(proj_mapping, momentum=_BATCH_NORM_DECAY, name=name_prefix + '_1x1_proj/bn', axis=bn_axis, epsilon=_BATCH_NORM_EPSILON, training=is_training, reuse=None, fused=_USE_FUSED_BN)
        reduced_inputs = tf.layers.conv2d(inputs, input_filters, (1, 1), use_bias=False, name=name_prefix + '_1x1_reduce', strides=(1, 1), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
        reduced_inputs_bn = tf.layers.batch_normalization(reduced_inputs, momentum=_BATCH_NORM_DECAY, name=name_prefix + '_1x1_reduce/bn', axis=bn_axis, epsilon=_BATCH_NORM_EPSILON, training=is_training, reuse=None, fused=_USE_FUSED_BN)
        reduced_inputs_relu = tf.nn.relu(reduced_inputs_bn, name=name_prefix + '_1x1_reduce/relu')
        if data_format == 'channels_first':
            reduced_inputs_relu = tf.pad(reduced_inputs_relu, paddings=[[0, 0], [0, 0], [1, 1], [1, 1]])
            weight_shape = [3, 3, reduced_inputs_relu.get_shape().as_list()[1] // group, input_filters]
            if is_training:
                weight_ = tf.Variable(constant_xavier_initializer(weight_shape, group=group, dtype=tf.float32), trainable=is_training, name=name_prefix + '_3x3/kernel')
            else:
                weight_ = tf.get_variable(name_prefix + '_3x3/kernel', shape=weight_shape, initializer=wrapper_initlizer, trainable=is_training)
            weight_groups = tf.split(weight_, num_or_size_splits=group, axis=-1, name=name_prefix + '_weight_split')
            xs = tf.split(reduced_inputs_relu, num_or_size_splits=group, axis=1, name=name_prefix + '_inputs_split')
        else:
            reduced_inputs_relu = tf.pad(reduced_inputs_relu, paddings=[[0, 0], [1, 1], [1, 1], [0, 0]])
            weight_shape = [3, 3, reduced_inputs_relu.get_shape().as_list()[-1] // group, input_filters]
            if is_training:
                weight_ = tf.Variable(constant_xavier_initializer(weight_shape, group=group, dtype=tf.float32), trainable=is_training, name=name_prefix + '_3x3/kernel')
            else:
                weight_ = tf.get_variable(name_prefix + '_3x3/kernel', shape=weight_shape, initializer=wrapper_initlizer, trainable=is_training)
            weight_groups = tf.split(weight_, num_or_size_splits=group, axis=-1, name=name_prefix + '_weight_split')
            xs = tf.split(reduced_inputs_relu, num_or_size_splits=group, axis=-1, name=name_prefix + '_inputs_split')
        convolved = [tf.nn.convolution(x, weight, padding='VALID', strides=[1, 1], name=name_prefix + '_group_conv', data_format='NCHW' if data_format == 'channels_first' else 'NHWC') for x, weight in zip(xs, weight_groups)]
        if data_format == 'channels_first':
            conv3_inputs = tf.concat(convolved, axis=1, name=name_prefix + '_concat')
        else:
            conv3_inputs = tf.concat(convolved, axis=-1, name=name_prefix + '_concat')
        conv3_inputs_bn = tf.layers.batch_normalization(conv3_inputs, momentum=_BATCH_NORM_DECAY, name=name_prefix + '_3x3/bn', axis=bn_axis, epsilon=_BATCH_NORM_EPSILON, training=is_training, reuse=None, fused=_USE_FUSED_BN)
        conv3_inputs_relu = tf.nn.relu(conv3_inputs_bn, name=name_prefix + '_3x3/relu')
        increase_inputs = tf.layers.conv2d(conv3_inputs_relu, input_filters * 2, (1, 1), use_bias=False, name=name_prefix + '_1x1_increase', strides=(1, 1), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
        increase_inputs_bn = tf.layers.batch_normalization(increase_inputs, momentum=_BATCH_NORM_DECAY, name=name_prefix + '_1x1_increase/bn', axis=bn_axis, epsilon=_BATCH_NORM_EPSILON, training=is_training, reuse=None, fused=_USE_FUSED_BN)
        if data_format == 'channels_first':
            pooled_inputs = tf.reduce_mean(increase_inputs_bn, [2, 3], name=name_prefix + '_global_pool', keep_dims=True)
        else:
            pooled_inputs = tf.reduce_mean(increase_inputs_bn, [1, 2], name=name_prefix + '_global_pool', keep_dims=True)
        down_inputs = tf.layers.conv2d(pooled_inputs, input_filters * 2 // reduced_scale, (1, 1), use_bias=True, name=name_prefix + '_1x1_down', strides=(1, 1), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
        down_inputs_relu = tf.nn.relu(down_inputs, name=name_prefix + '_1x1_down/relu')
        up_inputs = tf.layers.conv2d(down_inputs_relu, input_filters * 2, (1, 1), use_bias=True, name=name_prefix + '_1x1_up', strides=(1, 1), padding='valid', data_format=data_format, activation=None, kernel_initializer=tf.contrib.layers.xavier_initializer(), bias_initializer=tf.zeros_initializer())
        prob_outputs = tf.nn.sigmoid(up_inputs, name=name_prefix + '_prob')
        rescaled_feat = tf.multiply(prob_outputs, increase_inputs_bn, name=name_prefix + '_mul')
        pre_act = tf.add(residuals, rescaled_feat, name=name_prefix + '_add')
        return tf.nn.relu(pre_act, name=name_prefix + '/relu')

def _mean_image_subtraction(image, means):
    """Subtracts the given means from each image channel.

  For example:
    means = [123.68, 116.779, 103.939]
    image = _mean_image_subtraction(image, means)

  Note that the rank of `image` must be known.

  Args:
    image: a tensor of size [height, width, C].
    means: a C-vector of values to subtract from each channel.

  Returns:
    the centered image.

  Raises:
    ValueError: If the rank of `image` is unknown, if `image` has a rank other
      than three or if the number of channels in `image` doesn't match the
      number of values in `means`.
  """
    if image.get_shape().ndims != 3:
        raise ValueError('Input must be of size [height, width, C>0]')
    num_channels = image.get_shape().as_list()[-1]
    if len(means) != num_channels:
        raise ValueError('len(means) must match the number of channels')
    channels = tf.split(axis=2, num_or_size_splits=num_channels, value=image)
    for i in range(num_channels):
        channels[i] -= means[i]
    return tf.concat(axis=2, values=channels)

def unwhiten_image(image):
    means = [_R_MEAN, _G_MEAN, _B_MEAN]
    num_channels = image.get_shape().as_list()[-1]
    channels = tf.split(axis=2, num_or_size_splits=num_channels, value=image)
    for i in range(num_channels):
        channels[i] += means[i]
    return tf.concat(axis=2, values=channels)

def draw_labelmap(x, y, heatmap_sigma, heatmap_size):
    heatmap, isvalid = tf.map_fn(lambda pt: tf.py_func(np_draw_labelmap, [pt, heatmap_sigma, heatmap_size], [tf.float32, tf.int64], stateful=True), tf.stack([x, y], axis=-1), dtype=[tf.float32, tf.int64], parallel_iterations=10, back_prop=False, swap_memory=False, infer_shape=True)
    heatmap.set_shape([x.get_shape().as_list()[0], heatmap_size, heatmap_size])
    isvalid.set_shape([x.get_shape().as_list()[0]])
    return (heatmap, isvalid)

def _decode_crop_and_flip(image_buffer, bbox, num_channels):
    """Crops the given image to a random part of the image, and randomly flips.

  We use the fused decode_and_crop op, which performs better than the two ops
  used separately in series, but note that this requires that the image be
  passed in as an un-decoded string Tensor.

  Args:
    image_buffer: scalar string Tensor representing the raw JPEG image buffer.
    bbox: 3-D float Tensor of bounding boxes arranged [1, num_boxes, coords]
      where each coordinate is [0, 1) and the coordinates are arranged as
      [ymin, xmin, ymax, xmax].
    num_channels: Integer depth of the image buffer for decoding.

  Returns:
    3-D tensor with cropped image.

  """
    sample_distorted_bounding_box = tf.image.sample_distorted_bounding_box(tf.image.extract_jpeg_shape(image_buffer), bounding_boxes=bbox, min_object_covered=0.1, aspect_ratio_range=[0.75, 1.33], area_range=[0.05, 1.0], max_attempts=100, use_image_if_no_bounding_boxes=True)
    bbox_begin, bbox_size, _ = sample_distorted_bounding_box
    offset_y, offset_x, _ = tf.unstack(bbox_begin)
    target_height, target_width, _ = tf.unstack(bbox_size)
    crop_window = tf.stack([offset_y, offset_x, target_height, target_width])
    cropped = tf.image.decode_and_crop_jpeg(image_buffer, crop_window, channels=num_channels)
    cropped = tf.image.random_flip_left_right(cropped)
    return cropped

