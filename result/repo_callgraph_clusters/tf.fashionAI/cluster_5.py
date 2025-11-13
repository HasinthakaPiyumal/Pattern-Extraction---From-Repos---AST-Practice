# Cluster 5

class _PerGraphState(object):
    """Gradient reduction related state of a Tensorflow graph."""

    def __init__(self):
        self._collected_grads_and_vars = defaultdict(list)
        self._current_tower_index = 0
        self._number_of_towers = 1
        self._loss_reduction = None
        self._variable_scope = None
        self._name_scope = None
        self._has_tower_optimizer_been_used = False

    def collect_gradients(self, grads_and_vars):
        self._collected_grads_and_vars[self._current_tower_index].append(grads_and_vars)

    def get_latest_gradients_from_all_towers(self):
        """Get gradients across towers for the last called optimizer."""
        grads_and_vars = []
        index_of_last_gradients = len(self._collected_grads_and_vars[self._current_tower_index]) - 1
        for tower_id in range(self._current_tower_index + 1):
            grads_and_vars.extend(self._collected_grads_and_vars[tower_id][index_of_last_gradients])
        return grads_and_vars

    def set_reduction_across_towers(self, loss_reduction, number_of_towers):
        self._loss_reduction = loss_reduction
        self._number_of_towers = number_of_towers

    @contextmanager
    def tower(self, tower_id, var_scope, name_scope):
        if tower_id == 0:
            self._variable_scope = var_scope
            self._name_scope = name_scope
        self._current_tower_index = tower_id
        yield

    @property
    def scopes_of_the_first_tower(self):
        return (self._variable_scope, self._name_scope)

    @property
    def is_the_last_tower(self):
        return self._current_tower_index == self._number_of_towers - 1

    @property
    def number_of_towers(self):
        return self._number_of_towers

    @property
    def loss_reduction(self):
        return self._loss_reduction

    @property
    def has_tower_optimizer_been_used(self):
        return self._has_tower_optimizer_been_used

    @has_tower_optimizer_been_used.setter
    def has_tower_optimizer_been_used(self, value):
        self._has_tower_optimizer_been_used = value

    def did_towers_have_same_optimizer_calls(self):
        total_number_of_grads = sum([len(grads) for _, grads in six.iteritems(self._collected_grads_and_vars)])
        return total_number_of_grads % self._number_of_towers == 0

def collect_gradients(self, grads_and_vars):
    self._collected_grads_and_vars[self._current_tower_index].append(grads_and_vars)

def _bottleneck_block_v1(inputs, filters, training, projection_shortcut, strides, data_format):
    """A single block for ResNet v1, with a bottleneck.

    Similar to _building_block_v1(), except using the "bottleneck" blocks
    described in:
      Convolution then batch normalization then ReLU as described by:
        Deep Residual Learning for Image Recognition
        https://arxiv.org/pdf/1512.03385.pdf
        by Kaiming He, Xiangyu Zhang, Shaoqing Ren, and Jian Sun, Dec 2015.

    Args:
      inputs: A tensor of size [batch, channels, height_in, width_in] or
        [batch, height_in, width_in, channels] depending on data_format.
      filters: The number of filters for the convolutions.
      training: A Boolean for whether the model is in training or inference
        mode. Needed for batch normalization.
      projection_shortcut: The function to use for projection shortcuts
        (typically a 1x1 convolution when downsampling the input).
      strides: The block's stride. If greater than 1, this block will ultimately
        downsample the input.
      data_format: The input format ('channels_last' or 'channels_first').

    Returns:
      The output tensor of the block; shape should match inputs.
    """
    shortcut = inputs
    if projection_shortcut is not None:
        shortcut = projection_shortcut(inputs)
        shortcut = batch_norm(inputs=shortcut, training=training, data_format=data_format)
    inputs = conv2d_fixed_padding(inputs=inputs, filters=filters, kernel_size=1, strides=1, data_format=data_format)
    inputs = batch_norm(inputs, training, data_format)
    inputs = tf.nn.relu(inputs)
    inputs = conv2d_fixed_padding(inputs=inputs, filters=filters, kernel_size=3, strides=strides, data_format=data_format)
    inputs = batch_norm(inputs, training, data_format)
    inputs = tf.nn.relu(inputs)
    inputs = conv2d_fixed_padding(inputs=inputs, filters=4 * filters, kernel_size=1, strides=1, data_format=data_format)
    inputs = batch_norm(inputs, training, data_format)
    inputs += shortcut
    inputs = tf.nn.relu(inputs)
    return inputs

def projection_shortcut(inputs):
    return conv2d_fixed_padding(inputs=inputs, filters=256, kernel_size=1, strides=1, data_format=data_format, name='shortcut')

def global_net_bottleneck_block(inputs, filters, istraining, data_format, projection_shortcut=None, name=None):
    with tf.variable_scope(name, 'global_net_bottleneck', values=[inputs]):
        shortcut = inputs
        if projection_shortcut is not None:
            shortcut = projection_shortcut(inputs)
            shortcut = batch_norm(inputs=shortcut, training=istraining, data_format=data_format, name='batch_normalization_shortcut')
        inputs = conv2d_fixed_padding(inputs=inputs, filters=filters, kernel_size=1, strides=1, data_format=data_format, name='1x1_down')
        inputs = batch_norm(inputs, istraining, data_format, name='batch_normalization_1')
        inputs = tf.nn.relu(inputs, name='relu1')
        inputs = conv2d_fixed_padding(inputs=inputs, filters=filters, kernel_size=3, strides=1, data_format=data_format, name='3x3_conv')
        inputs = batch_norm(inputs, istraining, data_format, name='batch_normalization_2')
        inputs = tf.nn.relu(inputs, name='relu2')
        inputs = conv2d_fixed_padding(inputs=inputs, filters=2 * filters, kernel_size=1, strides=1, data_format=data_format, name='1x1_up')
        inputs = batch_norm(inputs, istraining, data_format, name='batch_normalization_3')
        inputs += shortcut
        inputs = tf.nn.relu(inputs, name='relu3')
        return inputs

def cascaded_pyramid_net(inputs, output_channals, heatmap_size, istraining, data_format):
    end_points = se_cpn_backbone(inputs, istraining, data_format)
    pyramid_len = len(end_points)
    up_sampling = None
    pyramid_heatmaps = []
    pyramid_laterals = []
    with tf.variable_scope('feature_pyramid', 'feature_pyramid', values=end_points):
        for ind, pyramid in enumerate(reversed(end_points)):
            inputs = conv2d_fixed_padding(inputs=pyramid, filters=256, kernel_size=1, strides=1, data_format=data_format, kernel_initializer=tf.glorot_uniform_initializer, name='1x1_conv1_p{}'.format(pyramid_len - ind))
            lateral = tf.nn.relu(inputs, name='relu1_p{}'.format(pyramid_len - ind))
            if up_sampling is not None:
                if data_format == 'channels_first':
                    up_sampling = tf.transpose(up_sampling, [0, 2, 3, 1], name='trans_p{}'.format(pyramid_len - ind))
                up_sampling = tf.image.resize_bilinear(up_sampling, tf.shape(up_sampling)[-3:-1] * 2, name='upsample_p{}'.format(pyramid_len - ind))
                if data_format == 'channels_first':
                    up_sampling = tf.transpose(up_sampling, [0, 3, 1, 2], name='trans_inv_p{}'.format(pyramid_len - ind))
                up_sampling = conv2d_fixed_padding(inputs=up_sampling, filters=256, kernel_size=1, strides=1, data_format=data_format, kernel_initializer=tf.glorot_uniform_initializer, name='up_conv_p{}'.format(pyramid_len - ind))
                up_sampling = lateral + up_sampling
                lateral = up_sampling
            else:
                up_sampling = lateral
            pyramid_laterals.append(lateral)
            lateral = conv2d_fixed_padding(inputs=lateral, filters=256, kernel_size=1, strides=1, data_format=data_format, kernel_initializer=tf.glorot_uniform_initializer, name='1x1_conv2_p{}'.format(pyramid_len - ind))
            lateral = tf.nn.relu(lateral, name='relu2_p{}'.format(pyramid_len - ind))
            outputs = conv2d_fixed_padding(inputs=lateral, filters=output_channals, kernel_size=3, strides=1, data_format=data_format, kernel_initializer=tf.glorot_uniform_initializer, name='conv_heatmap_p{}'.format(pyramid_len - ind))
            if data_format == 'channels_first':
                outputs = tf.transpose(outputs, [0, 2, 3, 1], name='output_trans_p{}'.format(pyramid_len - ind))
            outputs = tf.image.resize_bilinear(outputs, [heatmap_size, heatmap_size], name='heatmap_p{}'.format(pyramid_len - ind))
            if data_format == 'channels_first':
                outputs = tf.transpose(outputs, [0, 3, 1, 2], name='heatmap_trans_inv_p{}'.format(pyramid_len - ind))
            pyramid_heatmaps.append(outputs)
    with tf.variable_scope('global_net', 'global_net', values=pyramid_laterals):
        global_pyramids = []
        for ind, lateral in enumerate(pyramid_laterals):
            inputs = lateral
            for bottleneck_ind in range(pyramid_len - ind - 1):
                inputs = global_net_bottleneck_block(inputs, 128, istraining, data_format, name='global_net_bottleneck_{}_p{}'.format(bottleneck_ind, pyramid_len - ind))
            if data_format == 'channels_first':
                outputs = tf.transpose(inputs, [0, 2, 3, 1], name='global_output_trans_p{}'.format(pyramid_len - ind))
            else:
                outputs = inputs
            outputs = tf.image.resize_bilinear(outputs, [heatmap_size, heatmap_size], name='global_heatmap_p{}'.format(pyramid_len - ind))
            if data_format == 'channels_first':
                outputs = tf.transpose(outputs, [0, 3, 1, 2], name='global_heatmap_trans_inv_p{}'.format(pyramid_len - ind))
            global_pyramids.append(outputs)
        concat_pyramids = tf.concat(global_pyramids, 1 if data_format == 'channels_first' else 3, name='concat')

        def projection_shortcut(inputs):
            return conv2d_fixed_padding(inputs=inputs, filters=256, kernel_size=1, strides=1, data_format=data_format, name='shortcut')
        outputs = global_net_bottleneck_block(concat_pyramids, 128, istraining, data_format, projection_shortcut=projection_shortcut, name='global_concat_bottleneck')
        outputs = conv2d_fixed_padding(inputs=outputs, filters=output_channals, kernel_size=3, strides=1, data_format=data_format, kernel_initializer=tf.glorot_uniform_initializer, name='conv_heatmap')
    return pyramid_heatmaps + [outputs]

def xt_cascaded_pyramid_net(inputs, output_channals, heatmap_size, istraining, data_format, net_depth=50):
    end_points = sext_cpn_backbone(inputs, istraining, data_format, net_depth=net_depth)
    pyramid_len = len(end_points)
    up_sampling = None
    pyramid_heatmaps = []
    pyramid_laterals = []
    with tf.variable_scope('feature_pyramid', 'feature_pyramid', values=end_points):
        for ind, pyramid in enumerate(reversed(end_points)):
            inputs = conv2d_fixed_padding(inputs=pyramid, filters=256, kernel_size=1, strides=1, data_format=data_format, kernel_initializer=tf.glorot_uniform_initializer, name='1x1_conv1_p{}'.format(pyramid_len - ind))
            lateral = tf.nn.relu(inputs, name='relu1_p{}'.format(pyramid_len - ind))
            if up_sampling is not None:
                if data_format == 'channels_first':
                    up_sampling = tf.transpose(up_sampling, [0, 2, 3, 1], name='trans_p{}'.format(pyramid_len - ind))
                up_sampling = tf.image.resize_bilinear(up_sampling, tf.shape(up_sampling)[-3:-1] * 2, name='upsample_p{}'.format(pyramid_len - ind))
                if data_format == 'channels_first':
                    up_sampling = tf.transpose(up_sampling, [0, 3, 1, 2], name='trans_inv_p{}'.format(pyramid_len - ind))
                up_sampling = conv2d_fixed_padding(inputs=up_sampling, filters=256, kernel_size=1, strides=1, data_format=data_format, kernel_initializer=tf.glorot_uniform_initializer, name='up_conv_p{}'.format(pyramid_len - ind))
                up_sampling = lateral + up_sampling
                lateral = up_sampling
            else:
                up_sampling = lateral
            pyramid_laterals.append(lateral)
            lateral = conv2d_fixed_padding(inputs=lateral, filters=256, kernel_size=1, strides=1, data_format=data_format, kernel_initializer=tf.glorot_uniform_initializer, name='1x1_conv2_p{}'.format(pyramid_len - ind))
            lateral = tf.nn.relu(lateral, name='relu2_p{}'.format(pyramid_len - ind))
            outputs = conv2d_fixed_padding(inputs=lateral, filters=output_channals, kernel_size=3, strides=1, data_format=data_format, kernel_initializer=tf.glorot_uniform_initializer, name='conv_heatmap_p{}'.format(pyramid_len - ind))
            if data_format == 'channels_first':
                outputs = tf.transpose(outputs, [0, 2, 3, 1], name='output_trans_p{}'.format(pyramid_len - ind))
            outputs = tf.image.resize_bilinear(outputs, [heatmap_size, heatmap_size], name='heatmap_p{}'.format(pyramid_len - ind))
            if data_format == 'channels_first':
                outputs = tf.transpose(outputs, [0, 3, 1, 2], name='heatmap_trans_inv_p{}'.format(pyramid_len - ind))
            pyramid_heatmaps.append(outputs)
    with tf.variable_scope('global_net', 'global_net', values=pyramid_laterals):
        global_pyramids = []
        for ind, lateral in enumerate(pyramid_laterals):
            inputs = lateral
            for bottleneck_ind in range(pyramid_len - ind - 1):
                inputs = global_net_bottleneck_block(inputs, 128, istraining, data_format, name='global_net_bottleneck_{}_p{}'.format(bottleneck_ind, pyramid_len - ind))
            if data_format == 'channels_first':
                outputs = tf.transpose(inputs, [0, 2, 3, 1], name='global_output_trans_p{}'.format(pyramid_len - ind))
            else:
                outputs = inputs
            outputs = tf.image.resize_bilinear(outputs, [heatmap_size, heatmap_size], name='global_heatmap_p{}'.format(pyramid_len - ind))
            if data_format == 'channels_first':
                outputs = tf.transpose(outputs, [0, 3, 1, 2], name='global_heatmap_trans_inv_p{}'.format(pyramid_len - ind))
            global_pyramids.append(outputs)
        concat_pyramids = tf.concat(global_pyramids, 1 if data_format == 'channels_first' else 3, name='concat')

        def projection_shortcut(inputs):
            return conv2d_fixed_padding(inputs=inputs, filters=256, kernel_size=1, strides=1, data_format=data_format, name='shortcut')
        outputs = global_net_bottleneck_block(concat_pyramids, 128, istraining, data_format, projection_shortcut=projection_shortcut, name='global_concat_bottleneck')
        outputs = conv2d_fixed_padding(inputs=outputs, filters=output_channals, kernel_size=3, strides=1, data_format=data_format, kernel_initializer=tf.glorot_uniform_initializer, name='conv_heatmap')
    return pyramid_heatmaps + [outputs]

def head_xt_cascaded_pyramid_net(inputs, output_channals, heatmap_size, istraining, data_format):
    end_points = sext_cpn_backbone(inputs, istraining, data_format)
    pyramid_len = len(end_points)
    up_sampling = None
    pyramid_heatmaps = []
    pyramid_laterals = []
    with tf.variable_scope('feature_pyramid', 'feature_pyramid', values=end_points):
        for ind, pyramid in enumerate(reversed(end_points)):
            inputs = conv2d_fixed_padding(inputs=pyramid, filters=256, kernel_size=1, strides=1, data_format=data_format, kernel_initializer=tf.glorot_uniform_initializer, name='1x1_conv1_p{}'.format(pyramid_len - ind))
            lateral = tf.nn.relu(inputs, name='relu1_p{}'.format(pyramid_len - ind))
            if up_sampling is not None:
                if data_format == 'channels_first':
                    up_sampling = tf.transpose(up_sampling, [0, 2, 3, 1], name='trans_p{}'.format(pyramid_len - ind))
                up_sampling = tf.image.resize_bilinear(up_sampling, tf.shape(up_sampling)[-3:-1] * 2, name='upsample_p{}'.format(pyramid_len - ind))
                if data_format == 'channels_first':
                    up_sampling = tf.transpose(up_sampling, [0, 3, 1, 2], name='trans_inv_p{}'.format(pyramid_len - ind))
                up_sampling = conv2d_fixed_padding(inputs=up_sampling, filters=256, kernel_size=1, strides=1, data_format=data_format, kernel_initializer=tf.glorot_uniform_initializer, name='up_conv_p{}'.format(pyramid_len - ind))
                up_sampling = lateral + up_sampling
                lateral = up_sampling
            else:
                up_sampling = lateral
            pyramid_laterals.append(lateral)
            lateral = conv2d_fixed_padding(inputs=lateral, filters=256, kernel_size=1, strides=1, data_format=data_format, kernel_initializer=tf.glorot_uniform_initializer, name='1x1_conv2_p{}'.format(pyramid_len - ind))
            lateral = tf.nn.relu(lateral, name='relu2_p{}'.format(pyramid_len - ind))
            outputs = conv2d_fixed_padding(inputs=lateral, filters=output_channals, kernel_size=3, strides=1, data_format=data_format, kernel_initializer=tf.glorot_uniform_initializer, name='conv_heatmap_p{}'.format(pyramid_len - ind))
            if data_format == 'channels_first':
                outputs = tf.transpose(outputs, [0, 2, 3, 1], name='output_trans_p{}'.format(pyramid_len - ind))
            outputs = tf.image.resize_bilinear(outputs, [heatmap_size, heatmap_size], name='heatmap_p{}'.format(pyramid_len - ind))
            if data_format == 'channels_first':
                outputs = tf.transpose(outputs, [0, 3, 1, 2], name='heatmap_trans_inv_p{}'.format(pyramid_len - ind))
            pyramid_heatmaps.append(outputs)
    with tf.variable_scope('global_net', 'global_net', values=pyramid_laterals):
        global_pyramids = []
        for ind, lateral in enumerate(pyramid_laterals):
            inputs = lateral
            for bottleneck_ind in range(pyramid_len - ind - 1):
                inputs = global_net_sext_bottleneck_block(inputs, 128, istraining, data_format, name_prefix='global_net_bottleneck_{}_p{}'.format(bottleneck_ind, pyramid_len - ind))
            if data_format == 'channels_first':
                outputs = tf.transpose(inputs, [0, 2, 3, 1], name='global_output_trans_p{}'.format(pyramid_len - ind))
            else:
                outputs = inputs
            outputs = tf.image.resize_bilinear(outputs, [heatmap_size, heatmap_size], name='global_heatmap_p{}'.format(pyramid_len - ind))
            if data_format == 'channels_first':
                outputs = tf.transpose(outputs, [0, 3, 1, 2], name='global_heatmap_trans_inv_p{}'.format(pyramid_len - ind))
            global_pyramids.append(outputs)
        concat_pyramids = tf.concat(global_pyramids, 1 if data_format == 'channels_first' else 3, name='concat')
        outputs = global_net_sext_bottleneck_block(concat_pyramids, 128, istraining, data_format, need_reduce=True, name_prefix='global_concat_bottleneck')
        outputs = conv2d_fixed_padding(inputs=outputs, filters=output_channals, kernel_size=3, strides=1, data_format=data_format, kernel_initializer=tf.glorot_uniform_initializer, name='conv_heatmap')
    return pyramid_heatmaps + [outputs]

def _bottleneck_block_v1(inputs, filters, training, projection_shortcut, strides, data_format):
    """A single block for ResNet v1, with a bottleneck.

    Similar to _building_block_v1(), except using the "bottleneck" blocks
    described in:
      Convolution then batch normalization then ReLU as described by:
        Deep Residual Learning for Image Recognition
        https://arxiv.org/pdf/1512.03385.pdf
        by Kaiming He, Xiangyu Zhang, Shaoqing Ren, and Jian Sun, Dec 2015.

    Args:
      inputs: A tensor of size [batch, channels, height_in, width_in] or
        [batch, height_in, width_in, channels] depending on data_format.
      filters: The number of filters for the convolutions.
      training: A Boolean for whether the model is in training or inference
        mode. Needed for batch normalization.
      projection_shortcut: The function to use for projection shortcuts
        (typically a 1x1 convolution when downsampling the input).
      strides: The block's stride. If greater than 1, this block will ultimately
        downsample the input.
      data_format: The input format ('channels_last' or 'channels_first').

    Returns:
      The output tensor of the block; shape should match inputs.
    """
    shortcut = inputs
    if projection_shortcut is not None:
        shortcut = projection_shortcut(inputs)
        shortcut = batch_norm(inputs=shortcut, training=training, data_format=data_format)
    inputs = conv2d_fixed_padding(inputs=inputs, filters=filters, kernel_size=1, strides=1, data_format=data_format)
    inputs = batch_norm(inputs, training, data_format)
    inputs = tf.nn.relu(inputs)
    inputs = conv2d_fixed_padding(inputs=inputs, filters=filters, kernel_size=3, strides=strides, data_format=data_format)
    inputs = batch_norm(inputs, training, data_format)
    inputs = tf.nn.relu(inputs)
    inputs = conv2d_fixed_padding(inputs=inputs, filters=4 * filters, kernel_size=1, strides=1, data_format=data_format)
    inputs = batch_norm(inputs, training, data_format)
    inputs += shortcut
    inputs = tf.nn.relu(inputs)
    return inputs

def projection_shortcut(inputs):
    return conv2d_fixed_padding(inputs=inputs, filters=256, kernel_size=1, strides=1, data_format=data_format, name='shortcut')

def _dilated_bottleneck_block_v1(inputs, filters, training, projection_shortcut, data_format):
    shortcut = inputs
    if projection_shortcut is not None:
        shortcut = projection_shortcut(inputs)
        shortcut = batch_norm(inputs=shortcut, training=training, data_format=data_format)
    inputs = conv2d_fixed_padding(inputs=inputs, filters=filters, kernel_size=1, strides=1, data_format=data_format)
    inputs = batch_norm(inputs, training, data_format)
    inputs = tf.nn.relu(inputs)
    inputs = tf.layers.conv2d(inputs=inputs, filters=filters, kernel_size=3, strides=1, dilation_rate=(2, 2), padding='SAME', use_bias=False, kernel_initializer=tf.glorot_uniform_initializer(), data_format=data_format, name=None)
    inputs = batch_norm(inputs, training, data_format)
    inputs = tf.nn.relu(inputs)
    inputs = conv2d_fixed_padding(inputs=inputs, filters=4 * filters, kernel_size=1, strides=1, data_format=data_format)
    inputs = batch_norm(inputs, training, data_format)
    inputs += shortcut
    inputs = tf.nn.relu(inputs)
    return inputs

def detnet_cpn_backbone(inputs, istraining, data_format):
    block_strides = [1, 2, 2]
    inputs = conv2d_fixed_padding(inputs=inputs, filters=64, kernel_size=7, strides=2, data_format=data_format, kernel_initializer=tf.glorot_uniform_initializer)
    inputs = tf.identity(inputs, 'initial_conv')
    inputs = tf.layers.max_pooling2d(inputs=inputs, pool_size=3, strides=2, padding='SAME', data_format=data_format)
    inputs = tf.identity(inputs, 'initial_max_pool')
    end_points = []
    for i, num_blocks in enumerate([3, 4, 6]):
        num_filters = 64 * 2 ** i
        inputs = block_layer(inputs=inputs, filters=num_filters, bottleneck=True, block_fn=_bottleneck_block_v1, blocks=num_blocks, strides=block_strides[i], training=istraining, name='block_layer{}'.format(i + 1), data_format=data_format)
        end_points.append(inputs)
    with tf.variable_scope('additional_layer', 'additional_layer', values=[inputs]):
        inputs = dilated_block_layer(inputs=inputs, filters=256, bottleneck=True, block_fn=_dilated_bottleneck_block_v1, blocks=3, training=istraining, name='block_layer{}'.format(4), data_format=data_format)
        end_points.append(inputs)
        inputs = dilated_block_layer(inputs=inputs, filters=256, bottleneck=True, block_fn=_dilated_bottleneck_block_v1, blocks=3, training=istraining, name='block_layer{}'.format(5), data_format=data_format)
        end_points.append(inputs)
    return end_points[1:]

def global_net_bottleneck_block(inputs, filters, istraining, data_format, projection_shortcut=None, name=None):
    with tf.variable_scope(name, 'global_net_bottleneck', values=[inputs]):
        shortcut = inputs
        if projection_shortcut is not None:
            shortcut = projection_shortcut(inputs)
            shortcut = batch_norm(inputs=shortcut, training=istraining, data_format=data_format, name='batch_normalization_shortcut')
        inputs = conv2d_fixed_padding(inputs=inputs, filters=filters, kernel_size=1, strides=1, data_format=data_format, name='1x1_down')
        inputs = batch_norm(inputs, istraining, data_format, name='batch_normalization_1')
        inputs = tf.nn.relu(inputs, name='relu1')
        inputs = conv2d_fixed_padding(inputs=inputs, filters=filters, kernel_size=3, strides=1, data_format=data_format, name='3x3_conv')
        inputs = batch_norm(inputs, istraining, data_format, name='batch_normalization_2')
        inputs = tf.nn.relu(inputs, name='relu2')
        inputs = conv2d_fixed_padding(inputs=inputs, filters=2 * filters, kernel_size=1, strides=1, data_format=data_format, name='1x1_up')
        inputs = batch_norm(inputs, istraining, data_format, name='batch_normalization_3')
        inputs += shortcut
        inputs = tf.nn.relu(inputs, name='relu3')
        return inputs

def cascaded_pyramid_net(inputs, output_channals, heatmap_size, istraining, data_format):
    end_points = detnet_cpn_backbone(inputs, istraining, data_format)
    pyramid_len = len(end_points)
    up_sampling = None
    pyramid_heatmaps = []
    pyramid_laterals = []
    with tf.variable_scope('feature_pyramid', 'feature_pyramid', values=end_points):
        for ind, pyramid in enumerate(reversed(end_points)):
            inputs = conv2d_fixed_padding(inputs=pyramid, filters=256, kernel_size=1, strides=1, data_format=data_format, kernel_initializer=tf.glorot_uniform_initializer, name='1x1_conv1_p{}'.format(pyramid_len - ind + 1))
            lateral = tf.nn.relu(inputs, name='relu1_p{}'.format(pyramid_len - ind + 1))
            if up_sampling is not None:
                if ind > pyramid_len - 2:
                    if data_format == 'channels_first':
                        up_sampling = tf.transpose(up_sampling, [0, 2, 3, 1], name='trans_p{}'.format(pyramid_len - ind + 1))
                    up_sampling = tf.image.resize_bilinear(up_sampling, tf.shape(up_sampling)[-3:-1] * 2, name='upsample_p{}'.format(pyramid_len - ind + 1))
                    if data_format == 'channels_first':
                        up_sampling = tf.transpose(up_sampling, [0, 3, 1, 2], name='trans_inv_p{}'.format(pyramid_len - ind + 1))
                    up_sampling = conv2d_fixed_padding(inputs=up_sampling, filters=256, kernel_size=1, strides=1, data_format=data_format, kernel_initializer=tf.glorot_uniform_initializer, name='up_conv_p{}'.format(pyramid_len - ind + 1))
                up_sampling = lateral + up_sampling
                lateral = up_sampling
            else:
                up_sampling = lateral
            pyramid_laterals.append(lateral)
            lateral = conv2d_fixed_padding(inputs=lateral, filters=256, kernel_size=1, strides=1, data_format=data_format, kernel_initializer=tf.glorot_uniform_initializer, name='1x1_conv2_p{}'.format(pyramid_len - ind + 1))
            lateral = tf.nn.relu(lateral, name='relu2_p{}'.format(pyramid_len - ind + 1))
            outputs = conv2d_fixed_padding(inputs=lateral, filters=output_channals, kernel_size=3, strides=1, data_format=data_format, kernel_initializer=tf.glorot_uniform_initializer, name='conv_heatmap_p{}'.format(pyramid_len - ind + 1))
            if data_format == 'channels_first':
                outputs = tf.transpose(outputs, [0, 2, 3, 1], name='output_trans_p{}'.format(pyramid_len - ind + 1))
            outputs = tf.image.resize_bilinear(outputs, [heatmap_size, heatmap_size], name='heatmap_p{}'.format(pyramid_len - ind + 1))
            if data_format == 'channels_first':
                outputs = tf.transpose(outputs, [0, 3, 1, 2], name='heatmap_trans_inv_p{}'.format(pyramid_len - ind + 1))
            pyramid_heatmaps.append(outputs)
    with tf.variable_scope('global_net', 'global_net', values=pyramid_laterals):
        global_pyramids = []
        for ind, lateral in enumerate(pyramid_laterals):
            inputs = lateral
            for bottleneck_ind in range(pyramid_len - ind - 1):
                inputs = global_net_bottleneck_block(inputs, 128, istraining, data_format, name='global_net_bottleneck_{}_p{}'.format(bottleneck_ind, pyramid_len - ind))
            if data_format == 'channels_first':
                outputs = tf.transpose(inputs, [0, 2, 3, 1], name='global_output_trans_p{}'.format(pyramid_len - ind))
            else:
                outputs = inputs
            outputs = tf.image.resize_bilinear(outputs, [heatmap_size, heatmap_size], name='global_heatmap_p{}'.format(pyramid_len - ind))
            if data_format == 'channels_first':
                outputs = tf.transpose(outputs, [0, 3, 1, 2], name='global_heatmap_trans_inv_p{}'.format(pyramid_len - ind))
            global_pyramids.append(outputs)
        concat_pyramids = tf.concat(global_pyramids, 1 if data_format == 'channels_first' else 3, name='concat')

        def projection_shortcut(inputs):
            return conv2d_fixed_padding(inputs=inputs, filters=256, kernel_size=1, strides=1, data_format=data_format, name='shortcut')
        outputs = global_net_bottleneck_block(concat_pyramids, 128, istraining, data_format, projection_shortcut=projection_shortcut, name='global_concat_bottleneck')
        outputs = conv2d_fixed_padding(inputs=outputs, filters=output_channals, kernel_size=3, strides=1, data_format=data_format, kernel_initializer=tf.glorot_uniform_initializer, name='conv_heatmap')
    return pyramid_heatmaps + [outputs]

def batch_norm_relu(inputs, is_training, data_format, name=None):
    """Performs a batch normalization followed by a ReLU."""
    with tf.variable_scope(name, 'batch_norm_relu', values=[inputs]):
        inputs = tf.layers.batch_normalization(inputs=inputs, axis=1 if data_format == 'channels_first' else 3, momentum=_BATCH_NORM_DECAY, epsilon=_BATCH_NORM_EPSILON, center=True, scale=True, training=is_training, fused=_USE_FUSED_BN, name='batch_normalization')
        inputs = tf.nn.relu(inputs, name='relu')
        return inputs

def bottleneck_block_v2(inputs, in_filters, out_filters, is_training, data_format, name=None):
    with tf.variable_scope(name, 'bottleneck_block', values=[inputs]):
        shortcut = inputs
        inputs = batch_norm_relu(inputs, is_training, data_format, name='bn_relu_1')
        if in_filters != out_filters:
            shortcut = conv2d_fixed_padding(inputs=inputs, filters=out_filters, kernel_size=1, strides=1, data_format=data_format, name='skip')
        inputs = conv2d_fixed_padding(inputs=inputs, filters=out_filters // 2, kernel_size=1, strides=1, data_format=data_format, name='1x1_down')
        inputs = batch_norm_relu(inputs, is_training, data_format, name='bn_relu_2')
        inputs = conv2d_fixed_padding(inputs=inputs, filters=out_filters // 2, kernel_size=3, strides=1, data_format=data_format, name='3x3_conv')
        inputs = batch_norm_relu(inputs, is_training, data_format, name='bn_relu_3')
        inputs = conv2d_fixed_padding(inputs=inputs, filters=out_filters, kernel_size=1, strides=1, data_format=data_format, name='1x1_up')
        return tf.add(inputs, shortcut, name='elem_add')

def bottleneck_block_v1(inputs, in_filters, out_filters, is_training, data_format, name=None):
    with tf.variable_scope(name, 'bottleneck_block_v1', values=[inputs]):
        shortcut = inputs
        if in_filters != out_filters:
            shortcut = conv2d_fixed_padding(inputs=shortcut, filters=out_filters, kernel_size=1, strides=1, data_format=data_format, name='skip')
            shortcut = batch_norm(shortcut, is_training, data_format, name='skip_bn')
        inputs = conv2d_fixed_padding(inputs=inputs, filters=out_filters // 2, kernel_size=1, strides=1, data_format=data_format, name='1x1_down')
        inputs = batch_norm_relu(inputs, is_training, data_format, name='bn_relu_1')
        inputs = conv2d_fixed_padding(inputs=inputs, filters=out_filters // 2, kernel_size=3, strides=1, data_format=data_format, name='3x3_conv')
        inputs = batch_norm_relu(inputs, is_training, data_format, name='bn_relu_2')
        inputs = conv2d_fixed_padding(inputs=inputs, filters=out_filters, kernel_size=1, strides=1, data_format=data_format, name='1x1_up')
        inputs = batch_norm(inputs, is_training, data_format, name='up_bn')
        return tf.nn.relu(tf.add(inputs, shortcut, name='elem_add'), name='relu')

def hourglass(inputs, filters, is_training, data_format, deep_index=1, num_modules=1, name=None):
    with tf.variable_scope(name, 'hourglass_unit', values=[inputs]):
        upchannal1 = dozen_bottleneck_blocks(inputs, filters, filters, num_modules, is_training, data_format, name='up_{}')
        downchannal1 = tf.layers.max_pooling2d(inputs=inputs, pool_size=2, strides=2, padding='valid', data_format=data_format, name='down_pool')
        downchannal1 = dozen_bottleneck_blocks(downchannal1, filters, filters, num_modules, is_training, data_format, name='down1_{}')
        if deep_index > 1:
            downchannal2 = hourglass(downchannal1, filters, is_training, data_format, deep_index=deep_index - 1, num_modules=num_modules, name='inner_{}'.format(deep_index))
        else:
            downchannal2 = dozen_bottleneck_blocks(downchannal1, filters, filters, num_modules, is_training, data_format, name='down2_{}')
        downchannal3 = dozen_bottleneck_blocks(downchannal2, filters, filters, num_modules, is_training, data_format, name='down3_{}')
        if data_format == 'channels_first':
            downchannal3 = tf.transpose(downchannal3, [0, 2, 3, 1], name='trans')
        input_shape = tf.shape(downchannal3)[-3:-1] * 2
        upchannal2 = tf.image.resize_bilinear(downchannal3, input_shape, name='resize')
        if data_format == 'channels_first':
            upchannal2 = tf.transpose(upchannal2, [0, 3, 1, 2], name='trans_inv')
        return tf.add(upchannal1, upchannal2, name='elem_add')

def create_model(inputs, num_stack, feat_channals, output_channals, num_modules, is_training, data_format):
    with tf.variable_scope('precede', values=[inputs]):
        inputs = conv2d_fixed_padding(inputs=inputs, filters=64, kernel_size=7, strides=2, data_format=data_format, kernel_initializer=conv_bn_initializer_to_use, name='conv_7x7')
        inputs = batch_norm_relu(inputs, is_training, data_format, name='inputs_bn')
        inputs = bottleneck_block(inputs, 64, 128, is_training, data_format, name='residual1')
        inputs = tf.layers.max_pooling2d(inputs=inputs, pool_size=2, strides=2, padding='valid', data_format=data_format, name='pool')
        inputs = bottleneck_block(inputs, 128, 128, is_training, data_format, name='residual2')
        inputs = bottleneck_block(inputs, 128, feat_channals, is_training, data_format, name='residual3')
    hg_inputs = inputs
    outputs_list = []
    for stack_index in range(num_stack):
        hg = hourglass(hg_inputs, feat_channals, is_training, data_format, deep_index=4, num_modules=num_modules, name='stack_{}/hg'.format(stack_index))
        hg = dozen_bottleneck_blocks(hg, feat_channals, feat_channals, num_modules, is_training, data_format, name='stack_{}/'.format(stack_index) + 'output_{}')
        output_scores = conv2d_fixed_padding(inputs=hg, filters=feat_channals, kernel_size=1, strides=1, data_format=data_format, name='stack_{}/output_1x1'.format(stack_index))
        output_scores = batch_norm_relu(output_scores, is_training, data_format, name='stack_{}/output_bn'.format(stack_index))
        heatmap = tf.layers.conv2d(inputs=output_scores, filters=output_channals, kernel_size=1, strides=1, padding='same', use_bias=True, activation=None, kernel_initializer=initializer_to_use(), bias_initializer=tf.zeros_initializer(), data_format=data_format, name='hg_heatmap/stack_{}/heatmap_1x1'.format(stack_index))
        outputs_list.append(heatmap)
        if stack_index < num_stack - 1:
            output_scores_ = tf.layers.conv2d(inputs=output_scores, filters=feat_channals, kernel_size=1, strides=1, padding='same', use_bias=True, activation=None, kernel_initializer=initializer_to_use(), bias_initializer=tf.zeros_initializer(), data_format=data_format, name='stack_{}/remap_outputs'.format(stack_index))
            heatmap_ = tf.layers.conv2d(inputs=heatmap, filters=feat_channals, kernel_size=1, strides=1, padding='same', use_bias=True, activation=None, kernel_initializer=initializer_to_use(), bias_initializer=tf.zeros_initializer(), data_format=data_format, name='hg_heatmap/stack_{}/remap_heatmap'.format(stack_index))
            fused_heatmap = tf.add(output_scores_, heatmap_, 'stack_{}/fused_heatmap'.format(stack_index))
            hg_inputs = tf.add(hg_inputs, fused_heatmap, 'stack_{}/next_inputs'.format(stack_index))
    return outputs_list

def _bottleneck_block_v1(inputs, filters, training, projection_shortcut, strides, data_format):
    """A single block for ResNet v1, with a bottleneck.

    Similar to _building_block_v1(), except using the "bottleneck" blocks
    described in:
      Convolution then batch normalization then ReLU as described by:
        Deep Residual Learning for Image Recognition
        https://arxiv.org/pdf/1512.03385.pdf
        by Kaiming He, Xiangyu Zhang, Shaoqing Ren, and Jian Sun, Dec 2015.

    Args:
      inputs: A tensor of size [batch, channels, height_in, width_in] or
        [batch, height_in, width_in, channels] depending on data_format.
      filters: The number of filters for the convolutions.
      training: A Boolean for whether the model is in training or inference
        mode. Needed for batch normalization.
      projection_shortcut: The function to use for projection shortcuts
        (typically a 1x1 convolution when downsampling the input).
      strides: The block's stride. If greater than 1, this block will ultimately
        downsample the input.
      data_format: The input format ('channels_last' or 'channels_first').

    Returns:
      The output tensor of the block; shape should match inputs.
    """
    shortcut = inputs
    if projection_shortcut is not None:
        shortcut = projection_shortcut(inputs)
        shortcut = batch_norm(inputs=shortcut, training=training, data_format=data_format)
    inputs = conv2d_fixed_padding(inputs=inputs, filters=filters, kernel_size=1, strides=1, data_format=data_format)
    inputs = batch_norm(inputs, training, data_format)
    inputs = tf.nn.relu(inputs)
    inputs = conv2d_fixed_padding(inputs=inputs, filters=filters, kernel_size=3, strides=strides, data_format=data_format)
    inputs = batch_norm(inputs, training, data_format)
    inputs = tf.nn.relu(inputs)
    inputs = conv2d_fixed_padding(inputs=inputs, filters=4 * filters, kernel_size=1, strides=1, data_format=data_format)
    inputs = batch_norm(inputs, training, data_format)
    inputs += shortcut
    inputs = tf.nn.relu(inputs)
    return inputs

def projection_shortcut(inputs):
    return conv2d_fixed_padding(inputs=inputs, filters=256, kernel_size=1, strides=1, data_format=data_format, name='shortcut')

def cpn_backbone(inputs, istraining, data_format):
    block_strides = [1, 2, 2, 2]
    inputs = conv2d_fixed_padding(inputs=inputs, filters=64, kernel_size=7, strides=2, data_format=data_format, kernel_initializer=tf.glorot_uniform_initializer)
    inputs = tf.identity(inputs, 'initial_conv')
    inputs = tf.layers.max_pooling2d(inputs=inputs, pool_size=3, strides=2, padding='SAME', data_format=data_format)
    inputs = tf.identity(inputs, 'initial_max_pool')
    end_points = []
    for i, num_blocks in enumerate([3, 4, 6, 3]):
        num_filters = 64 * 2 ** i
        inputs = block_layer(inputs=inputs, filters=num_filters, bottleneck=True, block_fn=_bottleneck_block_v1, blocks=num_blocks, strides=block_strides[i], training=istraining, name='block_layer{}'.format(i + 1), data_format=data_format)
        end_points.append(inputs)
    return end_points

def global_net_bottleneck_block(inputs, filters, istraining, data_format, projection_shortcut=None, name=None):
    with tf.variable_scope(name, 'global_net_bottleneck', values=[inputs]):
        shortcut = inputs
        if projection_shortcut is not None:
            shortcut = projection_shortcut(inputs)
            shortcut = batch_norm(inputs=shortcut, training=istraining, data_format=data_format, name='batch_normalization_shortcut')
        inputs = conv2d_fixed_padding(inputs=inputs, filters=filters, kernel_size=1, strides=1, data_format=data_format, name='1x1_down')
        inputs = batch_norm(inputs, istraining, data_format, name='batch_normalization_1')
        inputs = tf.nn.relu(inputs, name='relu1')
        inputs = conv2d_fixed_padding(inputs=inputs, filters=filters, kernel_size=3, strides=1, data_format=data_format, name='3x3_conv')
        inputs = batch_norm(inputs, istraining, data_format, name='batch_normalization_2')
        inputs = tf.nn.relu(inputs, name='relu2')
        inputs = conv2d_fixed_padding(inputs=inputs, filters=2 * filters, kernel_size=1, strides=1, data_format=data_format, name='1x1_up')
        inputs = batch_norm(inputs, istraining, data_format, name='batch_normalization_3')
        inputs += shortcut
        inputs = tf.nn.relu(inputs, name='relu3')
        return inputs

def cascaded_pyramid_net(inputs, output_channals, heatmap_size, istraining, data_format):
    end_points = cpn_backbone(inputs, istraining, data_format)
    pyramid_len = len(end_points)
    up_sampling = None
    pyramid_heatmaps = []
    pyramid_laterals = []
    with tf.variable_scope('feature_pyramid', 'feature_pyramid', values=end_points):
        for ind, pyramid in enumerate(reversed(end_points)):
            inputs = conv2d_fixed_padding(inputs=pyramid, filters=256, kernel_size=1, strides=1, data_format=data_format, kernel_initializer=tf.glorot_uniform_initializer, name='1x1_conv1_p{}'.format(pyramid_len - ind))
            lateral = tf.nn.relu(inputs, name='relu1_p{}'.format(pyramid_len - ind))
            if up_sampling is not None:
                if data_format == 'channels_first':
                    up_sampling = tf.transpose(up_sampling, [0, 2, 3, 1], name='trans_p{}'.format(pyramid_len - ind))
                up_sampling = tf.image.resize_bilinear(up_sampling, tf.shape(up_sampling)[-3:-1] * 2, name='upsample_p{}'.format(pyramid_len - ind))
                if data_format == 'channels_first':
                    up_sampling = tf.transpose(up_sampling, [0, 3, 1, 2], name='trans_inv_p{}'.format(pyramid_len - ind))
                up_sampling = conv2d_fixed_padding(inputs=up_sampling, filters=256, kernel_size=1, strides=1, data_format=data_format, kernel_initializer=tf.glorot_uniform_initializer, name='up_conv_p{}'.format(pyramid_len - ind))
                up_sampling = lateral + up_sampling
                lateral = up_sampling
            else:
                up_sampling = lateral
            pyramid_laterals.append(lateral)
            lateral = conv2d_fixed_padding(inputs=lateral, filters=256, kernel_size=1, strides=1, data_format=data_format, kernel_initializer=tf.glorot_uniform_initializer, name='1x1_conv2_p{}'.format(pyramid_len - ind))
            lateral = tf.nn.relu(lateral, name='relu2_p{}'.format(pyramid_len - ind))
            outputs = conv2d_fixed_padding(inputs=lateral, filters=output_channals, kernel_size=3, strides=1, data_format=data_format, kernel_initializer=tf.glorot_uniform_initializer, name='conv_heatmap_p{}'.format(pyramid_len - ind))
            if data_format == 'channels_first':
                outputs = tf.transpose(outputs, [0, 2, 3, 1], name='output_trans_p{}'.format(pyramid_len - ind))
            outputs = tf.image.resize_bilinear(outputs, [heatmap_size, heatmap_size], name='heatmap_p{}'.format(pyramid_len - ind))
            if data_format == 'channels_first':
                outputs = tf.transpose(outputs, [0, 3, 1, 2], name='heatmap_trans_inv_p{}'.format(pyramid_len - ind))
            pyramid_heatmaps.append(outputs)
    with tf.variable_scope('global_net', 'global_net', values=pyramid_laterals):
        global_pyramids = []
        for ind, lateral in enumerate(pyramid_laterals):
            inputs = lateral
            for bottleneck_ind in range(pyramid_len - ind - 1):
                inputs = global_net_bottleneck_block(inputs, 128, istraining, data_format, name='global_net_bottleneck_{}_p{}'.format(bottleneck_ind, pyramid_len - ind))
            if data_format == 'channels_first':
                outputs = tf.transpose(inputs, [0, 2, 3, 1], name='global_output_trans_p{}'.format(pyramid_len - ind))
            else:
                outputs = inputs
            outputs = tf.image.resize_bilinear(outputs, [heatmap_size, heatmap_size], name='global_heatmap_p{}'.format(pyramid_len - ind))
            if data_format == 'channels_first':
                outputs = tf.transpose(outputs, [0, 3, 1, 2], name='global_heatmap_trans_inv_p{}'.format(pyramid_len - ind))
            global_pyramids.append(outputs)
        concat_pyramids = tf.concat(global_pyramids, 1 if data_format == 'channels_first' else 3, name='concat')

        def projection_shortcut(inputs):
            return conv2d_fixed_padding(inputs=inputs, filters=256, kernel_size=1, strides=1, data_format=data_format, name='shortcut')
        outputs = global_net_bottleneck_block(concat_pyramids, 128, istraining, data_format, projection_shortcut=projection_shortcut, name='global_concat_bottleneck')
        outputs = conv2d_fixed_padding(inputs=outputs, filters=output_channals, kernel_size=3, strides=1, data_format=data_format, kernel_initializer=tf.glorot_uniform_initializer, name='conv_heatmap')
    return pyramid_heatmaps + [outputs]

def global_net_bottleneck_block(inputs, filters, istraining, data_format, projection_shortcut=None, name=None):
    with tf.variable_scope(name, 'global_net_bottleneck', values=[inputs]):
        shortcut = inputs
        if projection_shortcut is not None:
            shortcut = projection_shortcut(inputs)
            shortcut = batch_norm(inputs=shortcut, training=istraining, data_format=data_format, name='batch_normalization_shortcut')
        inputs = conv2d_fixed_padding(inputs=inputs, filters=filters, kernel_size=1, strides=1, data_format=data_format, name='1x1_down')
        inputs = batch_norm(inputs, istraining, data_format, name='batch_normalization_1')
        inputs = tf.nn.relu(inputs, name='relu1')
        inputs = conv2d_fixed_padding(inputs=inputs, filters=filters, kernel_size=3, strides=1, data_format=data_format, name='3x3_conv')
        inputs = batch_norm(inputs, istraining, data_format, name='batch_normalization_2')
        inputs = tf.nn.relu(inputs, name='relu2')
        inputs = conv2d_fixed_padding(inputs=inputs, filters=2 * filters, kernel_size=1, strides=1, data_format=data_format, name='1x1_up')
        inputs = batch_norm(inputs, istraining, data_format, name='batch_normalization_3')
        inputs += shortcut
        inputs = tf.nn.relu(inputs, name='relu3')
        return inputs

def cascaded_pyramid_net(inputs, output_channals, heatmap_size, istraining, data_format, net_depth=50):
    end_points = sext_cpn_backbone(inputs, istraining, data_format, net_depth=net_depth)
    pyramid_len = len(end_points)
    up_sampling = None
    pyramid_heatmaps = []
    pyramid_laterals = []
    with tf.variable_scope('feature_pyramid', 'feature_pyramid', values=end_points):
        for ind, pyramid in enumerate(reversed(end_points)):
            inputs = conv2d_fixed_padding(inputs=pyramid, filters=256, kernel_size=1, strides=1, data_format=data_format, kernel_initializer=tf.glorot_uniform_initializer, name='1x1_conv1_p{}'.format(pyramid_len - ind + 1))
            lateral = tf.nn.relu(inputs, name='relu1_p{}'.format(pyramid_len - ind + 1))
            if up_sampling is not None:
                if ind > pyramid_len - 2:
                    if data_format == 'channels_first':
                        up_sampling = tf.transpose(up_sampling, [0, 2, 3, 1], name='trans_p{}'.format(pyramid_len - ind + 1))
                    up_sampling = tf.image.resize_bilinear(up_sampling, tf.shape(up_sampling)[-3:-1] * 2, name='upsample_p{}'.format(pyramid_len - ind + 1))
                    if data_format == 'channels_first':
                        up_sampling = tf.transpose(up_sampling, [0, 3, 1, 2], name='trans_inv_p{}'.format(pyramid_len - ind + 1))
                    up_sampling = conv2d_fixed_padding(inputs=up_sampling, filters=256, kernel_size=1, strides=1, data_format=data_format, kernel_initializer=tf.glorot_uniform_initializer, name='up_conv_p{}'.format(pyramid_len - ind + 1))
                up_sampling = lateral + up_sampling
                lateral = up_sampling
            else:
                up_sampling = lateral
            pyramid_laterals.append(lateral)
            lateral = conv2d_fixed_padding(inputs=lateral, filters=256, kernel_size=1, strides=1, data_format=data_format, kernel_initializer=tf.glorot_uniform_initializer, name='1x1_conv2_p{}'.format(pyramid_len - ind + 1))
            lateral = tf.nn.relu(lateral, name='relu2_p{}'.format(pyramid_len - ind + 1))
            outputs = conv2d_fixed_padding(inputs=lateral, filters=output_channals, kernel_size=3, strides=1, data_format=data_format, kernel_initializer=tf.glorot_uniform_initializer, name='conv_heatmap_p{}'.format(pyramid_len - ind + 1))
            if data_format == 'channels_first':
                outputs = tf.transpose(outputs, [0, 2, 3, 1], name='output_trans_p{}'.format(pyramid_len - ind + 1))
            outputs = tf.image.resize_bilinear(outputs, [heatmap_size, heatmap_size], name='heatmap_p{}'.format(pyramid_len - ind + 1))
            if data_format == 'channels_first':
                outputs = tf.transpose(outputs, [0, 3, 1, 2], name='heatmap_trans_inv_p{}'.format(pyramid_len - ind + 1))
            pyramid_heatmaps.append(outputs)
    with tf.variable_scope('global_net', 'global_net', values=pyramid_laterals):
        global_pyramids = []
        for ind, lateral in enumerate(pyramid_laterals):
            inputs = lateral
            for bottleneck_ind in range(pyramid_len - ind - 1):
                inputs = global_net_bottleneck_block(inputs, 128, istraining, data_format, name='global_net_bottleneck_{}_p{}'.format(bottleneck_ind, pyramid_len - ind))
            if data_format == 'channels_first':
                outputs = tf.transpose(inputs, [0, 2, 3, 1], name='global_output_trans_p{}'.format(pyramid_len - ind))
            else:
                outputs = inputs
            outputs = tf.image.resize_bilinear(outputs, [heatmap_size, heatmap_size], name='global_heatmap_p{}'.format(pyramid_len - ind))
            if data_format == 'channels_first':
                outputs = tf.transpose(outputs, [0, 3, 1, 2], name='global_heatmap_trans_inv_p{}'.format(pyramid_len - ind))
            global_pyramids.append(outputs)
        concat_pyramids = tf.concat(global_pyramids, 1 if data_format == 'channels_first' else 3, name='concat')

        def projection_shortcut(inputs):
            return conv2d_fixed_padding(inputs=inputs, filters=256, kernel_size=1, strides=1, data_format=data_format, name='shortcut')
        outputs = global_net_bottleneck_block(concat_pyramids, 128, istraining, data_format, projection_shortcut=projection_shortcut, name='global_concat_bottleneck')
        outputs = conv2d_fixed_padding(inputs=outputs, filters=output_channals, kernel_size=3, strides=1, data_format=data_format, kernel_initializer=tf.glorot_uniform_initializer, name='conv_heatmap')
    return pyramid_heatmaps + [outputs]

def projection_shortcut(inputs):
    return conv2d_fixed_padding(inputs=inputs, filters=256, kernel_size=1, strides=1, data_format=data_format, name='shortcut')

def head_xt_cascaded_pyramid_net(inputs, output_channals, heatmap_size, istraining, data_format):
    end_points = sext_cpn_backbone(inputs, istraining, data_format)
    pyramid_len = len(end_points)
    up_sampling = None
    pyramid_heatmaps = []
    pyramid_laterals = []
    with tf.variable_scope('feature_pyramid', 'feature_pyramid', values=end_points):
        for ind, pyramid in enumerate(reversed(end_points)):
            inputs = conv2d_fixed_padding(inputs=pyramid, filters=256, kernel_size=1, strides=1, data_format=data_format, kernel_initializer=tf.glorot_uniform_initializer, name='1x1_conv1_p{}'.format(pyramid_len - ind + 1))
            lateral = tf.nn.relu(inputs, name='relu1_p{}'.format(pyramid_len - ind + 1))
            if up_sampling is not None:
                if ind > pyramid_len - 2:
                    if data_format == 'channels_first':
                        up_sampling = tf.transpose(up_sampling, [0, 2, 3, 1], name='trans_p{}'.format(pyramid_len - ind + 1))
                    up_sampling = tf.image.resize_bilinear(up_sampling, tf.shape(up_sampling)[-3:-1] * 2, name='upsample_p{}'.format(pyramid_len - ind + 1))
                    if data_format == 'channels_first':
                        up_sampling = tf.transpose(up_sampling, [0, 3, 1, 2], name='trans_inv_p{}'.format(pyramid_len - ind + 1))
                    up_sampling = conv2d_fixed_padding(inputs=up_sampling, filters=256, kernel_size=1, strides=1, data_format=data_format, kernel_initializer=tf.glorot_uniform_initializer, name='up_conv_p{}'.format(pyramid_len - ind + 1))
                up_sampling = lateral + up_sampling
                lateral = up_sampling
            else:
                up_sampling = lateral
            pyramid_laterals.append(lateral)
            lateral = conv2d_fixed_padding(inputs=lateral, filters=256, kernel_size=1, strides=1, data_format=data_format, kernel_initializer=tf.glorot_uniform_initializer, name='1x1_conv2_p{}'.format(pyramid_len - ind + 1))
            lateral = tf.nn.relu(lateral, name='relu2_p{}'.format(pyramid_len - ind + 1))
            outputs = conv2d_fixed_padding(inputs=lateral, filters=output_channals, kernel_size=3, strides=1, data_format=data_format, kernel_initializer=tf.glorot_uniform_initializer, name='conv_heatmap_p{}'.format(pyramid_len - ind + 1))
            if data_format == 'channels_first':
                outputs = tf.transpose(outputs, [0, 2, 3, 1], name='output_trans_p{}'.format(pyramid_len - ind + 1))
            outputs = tf.image.resize_bilinear(outputs, [heatmap_size, heatmap_size], name='heatmap_p{}'.format(pyramid_len - ind + 1))
            if data_format == 'channels_first':
                outputs = tf.transpose(outputs, [0, 3, 1, 2], name='heatmap_trans_inv_p{}'.format(pyramid_len - ind + 1))
            pyramid_heatmaps.append(outputs)
    with tf.variable_scope('global_net', 'global_net', values=pyramid_laterals):
        global_pyramids = []
        for ind, lateral in enumerate(pyramid_laterals):
            inputs = lateral
            for bottleneck_ind in range(pyramid_len - ind - 1):
                inputs = global_net_sext_bottleneck_block(inputs, 128, istraining, data_format, name_prefix='global_net_bottleneck_{}_p{}'.format(bottleneck_ind, pyramid_len - ind))
            if data_format == 'channels_first':
                outputs = tf.transpose(inputs, [0, 2, 3, 1], name='global_output_trans_p{}'.format(pyramid_len - ind))
            else:
                outputs = inputs
            outputs = tf.image.resize_bilinear(outputs, [heatmap_size, heatmap_size], name='global_heatmap_p{}'.format(pyramid_len - ind))
            if data_format == 'channels_first':
                outputs = tf.transpose(outputs, [0, 3, 1, 2], name='global_heatmap_trans_inv_p{}'.format(pyramid_len - ind))
            global_pyramids.append(outputs)
        concat_pyramids = tf.concat(global_pyramids, 1 if data_format == 'channels_first' else 3, name='concat')
        outputs = global_net_sext_bottleneck_block(concat_pyramids, 128, istraining, data_format, need_reduce=True, name_prefix='global_concat_bottleneck')
        outputs = conv2d_fixed_padding(inputs=outputs, filters=output_channals, kernel_size=3, strides=1, data_format=data_format, kernel_initializer=tf.glorot_uniform_initializer, name='conv_heatmap')
    return pyramid_heatmaps + [outputs]

def _central_crop(image_list, crop_height, crop_width):
    """Performs central crops of the given image list.

  Args:
    image_list: a list of image tensors of the same dimension but possibly
      varying channel.
    crop_height: the height of the image following the crop.
    crop_width: the width of the image following the crop.

  Returns:
    the list of cropped images.
  """
    outputs = []
    for image in image_list:
        image_height = tf.shape(image)[0]
        image_width = tf.shape(image)[1]
        offset_height = (image_height - crop_height) / 2
        offset_width = (image_width - crop_width) / 2
        outputs.append(_crop(image, offset_height, offset_width, crop_height, crop_width))
    return outputs

def _aspect_preserving_resize(image, smallest_side):
    """Resize images preserving the original aspect ratio.

  Args:
    image: A 3-D image `Tensor`.
    smallest_side: A python integer or scalar `Tensor` indicating the size of
      the smallest side after resize.

  Returns:
    resized_image: A 3-D tensor containing the resized image.
  """
    smallest_side = tf.convert_to_tensor(smallest_side, dtype=tf.int32)
    shape = tf.shape(image)
    height = shape[0]
    width = shape[1]
    new_height, new_width = _smallest_size_at_least(height, width, smallest_side)
    image = tf.expand_dims(image, 0)
    resized_image = tf.image.resize_bilinear(image, [new_height, new_width], align_corners=False)
    resized_image = tf.squeeze(resized_image)
    resized_image.set_shape([None, None, 3])
    return resized_image

def distorted_bounding_box_crop(image, bbox, min_object_covered=1.0, aspect_ratio_range=(0.75, 1.33), area_range=(0.45, 1.0), max_attempts=100, scope=None):
    """Generates cropped_image using a one of the bboxes randomly distorted.

  See `tf.image.sample_distorted_bounding_box` for more documentation.

  Args:
    image: 3-D Tensor of image (it will be converted to floats in [0, 1]).
    bbox: 3-D float Tensor of bounding boxes arranged [1, num_boxes, coords]
      where each coordinate is [0, 1) and the coordinates are arranged
      as [ymin, xmin, ymax, xmax]. If num_boxes is 0 then it would use the whole
      image.
    min_object_covered: An optional `float`. Defaults to `0.1`. The cropped
      area of the image must contain at least this fraction of any bounding box
      supplied.
    aspect_ratio_range: An optional list of `floats`. The cropped area of the
      image must have an aspect ratio = width / height within this range.
    area_range: An optional list of `floats`. The cropped area of the image
      must contain a fraction of the supplied image within in this range.
    max_attempts: An optional `int`. Number of attempts at generating a cropped
      region of the image of the specified constraints. After `max_attempts`
      failures, return the entire image.
    scope: Optional scope for name_scope.
  Returns:
    A tuple, a 3-D Tensor cropped_image and the distorted bbox
  """
    with tf.name_scope(scope, 'distorted_bounding_box_crop', [image, bbox]):
        sample_distorted_bounding_box = tf.image.sample_distorted_bounding_box(tf.shape(image), bounding_boxes=bbox, min_object_covered=min_object_covered, aspect_ratio_range=aspect_ratio_range, area_range=area_range, max_attempts=max_attempts, use_image_if_no_bounding_boxes=True)
        bbox_begin, bbox_size, distort_bbox = sample_distorted_bounding_box
        cropped_image = tf.slice(image, bbox_begin, bbox_size)
        return (cropped_image, distort_bbox)

def _central_crop(image, crop_height, crop_width):
    """Performs central crops of the given image list.

  Args:
    image: a 3-D image tensor
    crop_height: the height of the image following the crop.
    crop_width: the width of the image following the crop.

  Returns:
    3-D tensor with cropped image.
  """
    shape = tf.shape(image)
    height, width = (shape[0], shape[1])
    amount_to_be_cropped_h = height - crop_height
    crop_top = amount_to_be_cropped_h // 2
    amount_to_be_cropped_w = width - crop_width
    crop_left = amount_to_be_cropped_w // 2
    return tf.slice(image, [crop_top, crop_left, 0], [crop_height, crop_width, -1])

