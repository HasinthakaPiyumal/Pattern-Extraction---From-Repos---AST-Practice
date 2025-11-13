# Cluster 2

def assign_moving_average(variable, value, decay, zero_debias=True, name=None):
    """Compute the moving average of a variable.

  The moving average of 'variable' updated with 'value' is:
    variable * decay + value * (1 - decay)

  The returned Operation sets 'variable' to the newly computed moving average.

  The new value of 'variable' can be set with the 'AssignSub' op as:
     variable -= (1 - decay) * (variable - value)

  Since variables that are initialized to a `0` value will be `0` biased,
  `zero_debias` optionally enables scaling by the mathematically correct
  debiasing factor of
    1 - decay ** num_updates
  See `ADAM: A Method for Stochastic Optimization` Section 3 for more details
  (https://arxiv.org/abs/1412.6980).

  The names of the debias shadow variables, by default, include both the scope
  they were created in and the scope of the variables they debias. They are also
  given a uniqifying-suffix.

  E.g.:

  ```
    with tf.variable_scope('scope1'):
      with tf.variable_scope('scope2'):
        var = tf.get_variable('foo')
        tf.assign_moving_average(var, 0.0, 1.0)
        tf.assign_moving_average(var, 0.0, 0.9)

    # var.name: 'scope1/scope2/foo'
    # shadow var names: 'scope1/scope2/scope1/scope2/foo/biased'
    #                   'scope1/scope2/scope1/scope2/foo/biased_1'
  ```

  Args:
    variable: A Variable.
    value: A tensor with the same shape as 'variable'.
    decay: A float Tensor or float value.  The moving average decay.
    zero_debias: A python bool. If true, assume the variable is 0-initialized
      and unbias it, as in https://arxiv.org/abs/1412.6980. See docstring in
      `_zero_debias` for more details.
    name: Optional name of the returned operation.

  Returns:
    A reference to the input 'variable' tensor with the newly computed
    moving average.
  """
    with ops.name_scope(name, 'AssignMovingAvg', [variable, value, decay]) as scope:
        with ops.colocate_with(variable):
            decay = ops.convert_to_tensor(1.0 - decay, name='decay')
            if decay.dtype != variable.dtype.base_dtype:
                decay = math_ops.cast(decay, variable.dtype.base_dtype)
            if zero_debias:
                update_delta = _zero_debias(variable, value, decay)
            else:
                update_delta = (variable - value) * decay
            return state_ops.assign_sub(variable, update_delta, name=scope)

def _zero_debias(unbiased_var, value, decay):
    """Compute the delta required for a debiased Variable.

  All exponential moving averages initialized with Tensors are initialized to 0,
  and therefore are biased to 0. Variables initialized to 0 and used as EMAs are
  similarly biased. This function creates the debias updated amount according to
  a scale factor, as in https://arxiv.org/abs/1412.6980.

  To demonstrate the bias the results from 0-initialization, take an EMA that
  was initialized to `0` with decay `b`. After `t` timesteps of seeing the
  constant `c`, the variable have the following value:

  ```
    EMA = 0*b^(t) + c*(1 - b)*b^(t-1) + c*(1 - b)*b^(t-2) + ...
        = c*(1 - b^t)
  ```

  To have the true value `c`, we would divide by the scale factor `1 - b^t`.

  In order to perform debiasing, we use two shadow variables. One keeps track of
  the biased estimate, and the other keeps track of the number of updates that
  have occurred.

  Args:
    unbiased_var: A Variable representing the current value of the unbiased EMA.
    value: A Tensor representing the most recent value.
    decay: A Tensor representing `1-decay` for the EMA.

  Returns:
    The amount that the unbiased variable should be updated. Computing this
    tensor will also update the shadow variables appropriately.
  """
    with variable_scope.variable_scope(unbiased_var.op.name, values=[unbiased_var, value, decay]) as scope:
        with ops.colocate_with(unbiased_var):
            with ops.init_scope():
                biased_initializer = init_ops.zeros_initializer(dtype=unbiased_var.dtype)(unbiased_var.get_shape())
                local_step_initializer = init_ops.zeros_initializer()

            def _maybe_get_unique(name):
                """Get name for a unique variable, if not `reuse=True`."""
                if variable_scope.get_variable_scope().reuse:
                    return name
                vs_vars = [x.op.name for x in variable_scope.get_variable_scope().global_variables()]
                full_name = variable_scope.get_variable_scope().name + '/' + name
                if full_name not in vs_vars:
                    return name
                idx = 1
                while full_name + '_%d' % idx in vs_vars:
                    idx += 1
                return name + '_%d' % idx
            biased_var = variable_scope.get_variable(_maybe_get_unique('biased'), initializer=biased_initializer, trainable=False)
            local_step = variable_scope.get_variable(_maybe_get_unique('local_step'), shape=[], dtype=unbiased_var.dtype, initializer=local_step_initializer, trainable=False)
            update_biased = state_ops.assign_sub(biased_var, (biased_var - value) * decay, name=scope.name)
            update_local_step = local_step.assign_add(1)
            with ops.control_dependencies([update_biased, update_local_step]):
                unbiased_ema_delta = unbiased_var - biased_var.read_value() / (1 - math_ops.pow(1.0 - decay, local_step.read_value()))
            return unbiased_ema_delta

def _model_variable_getter(getter, name, shape=None, dtype=None, initializer=None, regularizer=None, trainable=True, collections=None, caching_device=None, partitioner=None, rename=None, use_resource=None, **_):
    """Getter that uses model_variable for compatibility with core layers."""
    short_name = name.split('/')[-1]
    if rename and short_name in rename:
        name_components = name.split('/')
        name_components[-1] = rename[short_name]
        name = '/'.join(name_components)
    return variables.model_variable(name, shape=shape, dtype=dtype, initializer=initializer, regularizer=regularizer, collections=collections, trainable=trainable, caching_device=caching_device, partitioner=partitioner, custom_getter=getter, use_resource=use_resource)

def depth_conv2d(inputs, kernel_size, stride=1, channel_multiplier=1, padding='SAME', data_format=DATA_FORMAT_NHWC, rate=1, activation_fn=nn.relu, normalizer_fn=None, normalizer_params=None, weights_initializer=initializers.xavier_initializer(), weights_regularizer=None, biases_initializer=init_ops.zeros_initializer(), biases_regularizer=None, reuse=None, variables_collections=None, outputs_collections=None, trainable=True, scope=None):
    if data_format not in (DATA_FORMAT_NCHW, DATA_FORMAT_NHWC):
        raise ValueError('data_format has to be either NCHW or NHWC.')
    layer_variable_getter = _build_variable_getter({'bias': 'biases', 'depthwise_kernel': 'depthwise_weights'})
    with variable_scope.variable_scope(scope, 'SeparableConv2d', [inputs], reuse=reuse, custom_getter=layer_variable_getter) as sc:
        inputs = ops.convert_to_tensor(inputs)
        df = 'channels_first' if data_format and data_format.startswith('NC') else 'channels_last'
        dtype = inputs.dtype.base_dtype
        kernel_h, kernel_w = utils.two_element_tuple(kernel_size)
        stride_h, stride_w = utils.two_element_tuple(stride)
        num_filters_in = utils.channel_dimension(inputs.get_shape(), df, min_rank=4)
        weights_collections = utils.get_variable_collections(variables_collections, 'weights')
        depthwise_shape = [kernel_h, kernel_w, num_filters_in, channel_multiplier]
        depthwise_weights = variables.model_variable('depthwise_weights', shape=depthwise_shape, dtype=dtype, initializer=weights_initializer, regularizer=weights_regularizer, trainable=trainable, collections=weights_collections)
        strides = [1, 1, stride_h, stride_w] if data_format.startswith('NC') else [1, stride_h, stride_w, 1]
        outputs = nn.depthwise_conv2d(inputs, depthwise_weights, strides, padding, rate=utils.two_element_tuple(rate), data_format=data_format)
        num_outputs = num_filters_in
        if normalizer_fn is not None:
            normalizer_params = normalizer_params or {}
            outputs = normalizer_fn(outputs, **normalizer_params)
        elif biases_initializer is not None:
            biases_collections = utils.get_variable_collections(variables_collections, 'biases')
            biases = variables.model_variable('biases', shape=[num_outputs], dtype=dtype, initializer=biases_initializer, regularizer=biases_regularizer, trainable=trainable, collections=biases_collections)
            outputs = nn.bias_add(outputs, biases, data_format=data_format)
        if activation_fn is not None:
            outputs = activation_fn(outputs)
        return utils.collect_named_outputs(outputs_collections, sc.name, outputs)

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

def get_latest_gradients_from_all_towers(self):
    """Get gradients across towers for the last called optimizer."""
    grads_and_vars = []
    index_of_last_gradients = len(self._collected_grads_and_vars[self._current_tower_index]) - 1
    for tower_id in range(self._current_tower_index + 1):
        grads_and_vars.extend(self._collected_grads_and_vars[tower_id][index_of_last_gradients])
    return grads_and_vars

def ensure_divisible_by_shards(sequence):
    batch_size = ops_lib.convert_to_tensor(sequence).get_shape()[0]
    if batch_size % number_of_shards != 0:
        raise ValueError('Batch size {} needs to be divisible by the number of GPUs, which is {}.'.format(batch_size, number_of_shards))

def constant_xavier_initializer(shape, group, dtype=tf.float32, uniform=True):
    """Initializer function."""
    if not dtype.is_floating:
        raise TypeError('Cannot create initializer for non-floating point type.')
    if shape:
        fan_in = float(shape[-2]) if len(shape) > 1 else float(shape[-1])
        fan_out = float(shape[-1]) / group
    else:
        fan_in = 1.0
        fan_out = 1.0
    for dim in shape[:-2]:
        fan_in *= float(dim)
        fan_out *= float(dim)
    n = (fan_in + fan_out) / 2.0
    if uniform:
        limit = math.sqrt(3.0 * 1.0 / n)
        return tf.random_uniform(shape, -limit, limit, dtype, seed=None)
    else:
        trunc_stddev = math.sqrt(1.3 * 1.0 / n)
        return tf.truncated_normal(shape, 0.0, trunc_stddev, dtype, seed=None)

def constant_xavier_initializer(shape, group, dtype=tf.float32, uniform=True):
    """Initializer function."""
    if not dtype.is_floating:
        raise TypeError('Cannot create initializer for non-floating point type.')
    if shape:
        fan_in = float(shape[-2]) if len(shape) > 1 else float(shape[-1])
        fan_out = float(shape[-1]) / group
    else:
        fan_in = 1.0
        fan_out = 1.0
    for dim in shape[:-2]:
        fan_in *= float(dim)
        fan_out *= float(dim)
    n = (fan_in + fan_out) / 2.0
    if uniform:
        limit = math.sqrt(3.0 * 1.0 / n)
        return tf.random_uniform(shape, -limit, limit, dtype, seed=None)
    else:
        trunc_stddev = math.sqrt(1.3 * 1.0 / n)
        return tf.truncated_normal(shape, 0.0, trunc_stddev, dtype, seed=None)

def constant_xavier_initializer(shape, group, dtype=tf.float32, uniform=True):
    """Initializer function."""
    if not dtype.is_floating:
        raise TypeError('Cannot create initializer for non-floating point type.')
    if shape:
        fan_in = float(shape[-2]) if len(shape) > 1 else float(shape[-1])
        fan_out = float(shape[-1]) / group
    else:
        fan_in = 1.0
        fan_out = 1.0
    for dim in shape[:-2]:
        fan_in *= float(dim)
        fan_out *= float(dim)
    n = (fan_in + fan_out) / 2.0
    if uniform:
        limit = math.sqrt(3.0 * 1.0 / n)
        return tf.random_uniform(shape, -limit, limit, dtype, seed=None)
    else:
        trunc_stddev = math.sqrt(1.3 * 1.0 / n)
        return tf.truncated_normal(shape, 0.0, trunc_stddev, dtype, seed=None)

def apply_with_random_selector(x, func, num_cases):
    """Computes func(x, sel), with sel sampled from [0...num_cases-1].

  Args:
    x: input Tensor.
    func: Python function to apply.
    num_cases: Python int32, number of cases to sample sel from.

  Returns:
    The result of func(x, sel), where func receives the value of the
    selector as a python integer, but sel is sampled dynamically.
  """
    sel = tf.random_uniform([], maxval=num_cases, dtype=tf.int32)
    return control_flow_ops.merge([func(control_flow_ops.switch(x, tf.equal(sel, case))[1], case) for case in range(num_cases)])[0]

def _crop(image, offset_height, offset_width, crop_height, crop_width):
    """Crops the given image using the provided offsets and sizes.

  Note that the method doesn't assume we know the input image size but it does
  assume we know the input image rank.

  Args:
    image: an image of shape [height, width, channels].
    offset_height: a scalar tensor indicating the height offset.
    offset_width: a scalar tensor indicating the width offset.
    crop_height: the height of the cropped image.
    crop_width: the width of the cropped image.

  Returns:
    the cropped (and resized) image.

  Raises:
    InvalidArgumentError: if the rank is not 3 or if the image dimensions are
      less than the crop size.
  """
    original_shape = tf.shape(image)
    rank_assertion = tf.Assert(tf.equal(tf.rank(image), 3), ['Rank of image must be equal to 3.'])
    with tf.control_dependencies([rank_assertion]):
        cropped_shape = tf.stack([crop_height, crop_width, original_shape[2]])
    size_assertion = tf.Assert(tf.logical_and(tf.greater_equal(original_shape[0], crop_height), tf.greater_equal(original_shape[1], crop_width)), ['Crop size greater than the image size.'])
    offsets = tf.to_int32(tf.stack([offset_height, offset_width, 0]))
    with tf.control_dependencies([size_assertion]):
        image = tf.slice(image, offsets, cropped_shape)
    return tf.reshape(image, cropped_shape)

def _random_crop(image_list, crop_height, crop_width):
    """Crops the given list of images.

  The function applies the same crop to each image in the list. This can be
  effectively applied when there are multiple image inputs of the same
  dimension such as:

    image, depths, normals = _random_crop([image, depths, normals], 120, 150)

  Args:
    image_list: a list of image tensors of the same dimension but possibly
      varying channel.
    crop_height: the new height.
    crop_width: the new width.

  Returns:
    the image_list with cropped images.

  Raises:
    ValueError: if there are multiple image inputs provided with different size
      or the images are smaller than the crop dimensions.
  """
    if not image_list:
        raise ValueError('Empty image_list.')
    rank_assertions = []
    for i in range(len(image_list)):
        image_rank = tf.rank(image_list[i])
        rank_assert = tf.Assert(tf.equal(image_rank, 3), ['Wrong rank for tensor  %s [expected] [actual]', image_list[i].name, 3, image_rank])
        rank_assertions.append(rank_assert)
    with tf.control_dependencies([rank_assertions[0]]):
        image_shape = tf.shape(image_list[0])
    image_height = image_shape[0]
    image_width = image_shape[1]
    crop_size_assert = tf.Assert(tf.logical_and(tf.greater_equal(image_height, crop_height), tf.greater_equal(image_width, crop_width)), ['Crop size greater than the image size.'])
    asserts = [rank_assertions[0], crop_size_assert]
    for i in range(1, len(image_list)):
        image = image_list[i]
        asserts.append(rank_assertions[i])
        with tf.control_dependencies([rank_assertions[i]]):
            shape = tf.shape(image)
        height = shape[0]
        width = shape[1]
        height_assert = tf.Assert(tf.equal(height, image_height), ['Wrong height for tensor %s [expected][actual]', image.name, height, image_height])
        width_assert = tf.Assert(tf.equal(width, image_width), ['Wrong width for tensor %s [expected][actual]', image.name, width, image_width])
        asserts.extend([height_assert, width_assert])
    with tf.control_dependencies(asserts):
        max_offset_height = tf.reshape(image_height - crop_height + 1, [])
    with tf.control_dependencies(asserts):
        max_offset_width = tf.reshape(image_width - crop_width + 1, [])
    offset_height = tf.random_uniform([], maxval=max_offset_height, dtype=tf.int32)
    offset_width = tf.random_uniform([], maxval=max_offset_width, dtype=tf.int32)
    return [_crop(image, offset_height, offset_width, crop_height, crop_width) for image in image_list]

def get_projective_transforms(angles, image_height, image_width, x, y, name=None):
    """Returns projective transform(s) for the given angle(s).
  Args:
    angles: A scalar angle to rotate all images by, or (for batches of images)
        a vector with an angle to rotate each image in the batch. The rank must
        be statically known (the shape is not `TensorShape(None)`.
    image_height: Height of the image(s) to be transformed.
    image_width: Width of the image(s) to be transformed.
  Returns:
    A tensor of shape (num_images, 8). Projective transforms which can be given
      to `tf.contrib.image.transform`.
  """
    with tf.name_scope(name, 'get_projective_transforms'):
        angle_or_angles = tf.convert_to_tensor(angles, name='angles', dtype=tf.float32)
        if len(angle_or_angles.get_shape()) == 0:
            angles = angle_or_angles[None]
        elif len(angle_or_angles.get_shape()) == 1:
            angles = angle_or_angles
        else:
            raise TypeError('Angles should have rank 0 or 1.')
        valid_x = tf.boolean_mask(x, x > 0.0)
        valid_y = tf.boolean_mask(y, y > 0.0)
        min_x = tf.reduce_min(valid_x, axis=-1)
        max_x = tf.reduce_max(valid_x, axis=-1)
        min_y = tf.reduce_min(valid_y, axis=-1)
        max_y = tf.reduce_max(valid_y, axis=-1)
        center_x = (min_x + max_x) / 2.0
        center_y = (min_y + max_y) / 2.0
        x_offset = center_x - (tf.cos(angles) * image_width / 2.0 - tf.sin(angles) * image_height / 2.0)
        y_offset = center_y - (tf.sin(angles) * image_width / 2.0 + tf.cos(angles) * image_height / 2.0)
        num_angles = tf.shape(angles)[0]
        return tf.concat(values=[tf.cos(angles)[:, None], -tf.sin(angles)[:, None], x_offset[:, None], tf.sin(angles)[:, None], tf.cos(angles)[:, None], y_offset[:, None], tf.zeros((num_angles, 2), tf.float32)], axis=1)

def rotate_all(images, angles, x, y, interpolation='NEAREST'):
    """Rotate image(s) by the passed angle(s) in radians.
  Args:
    images: A tensor of shape (num_images, num_rows, num_columns, num_channels)
       (NHWC), (num_rows, num_columns, num_channels) (HWC), or
       (num_rows, num_columns) (HW).
    angles: A scalar angle to rotate all images by, or (if images has rank 4)
       a vector of length num_images, with an angle for each image in the batch.
    interpolation: Interpolation mode. Supported values: "NEAREST", "BILINEAR".
  Returns:
    Image(s) with the same type and shape as `images`, rotated by the given
    angle(s). Empty space due to the rotation will be filled with zeros.
  Raises:
    TypeError: If `image` is an invalid type.
  """
    image_or_images = tf.convert_to_tensor(images, name='images')
    if len(image_or_images.get_shape()) == 2:
        images = image_or_images[None, :, :, None]
    elif len(image_or_images.get_shape()) == 3:
        images = image_or_images[None, :, :, :]
    elif len(image_or_images.get_shape()) == 4:
        images = image_or_images
    else:
        raise TypeError('Images should have rank between 2 and 4.')
    image_height = tf.cast(tf.shape(images)[1], tf.float32)[None]
    image_width = tf.cast(tf.shape(images)[2], tf.float32)[None]
    rotate_matrix = get_projective_transforms(angles, image_height, image_width, x, y)
    flaten_rotate_matrix = tf.squeeze(rotate_matrix)
    a0, a1, a2, b0, b1, b2 = (flaten_rotate_matrix[0], flaten_rotate_matrix[1], flaten_rotate_matrix[2], flaten_rotate_matrix[3], flaten_rotate_matrix[4], flaten_rotate_matrix[5])
    normalizor = a1 * b0 - a0 * b1 + 1e-08
    new_x = -(b1 * x - a1 * y - b1 * a2 + a1 * b2) / normalizor
    new_y = (b0 * x - a0 * y - a2 * b0 + a0 * b2) / normalizor
    output = tf.contrib.image.transform(images, rotate_matrix, interpolation=interpolation)
    if len(image_or_images.get_shape()) == 2:
        return (output[0, :, :, 0], new_x, new_y)
    elif len(image_or_images.get_shape()) == 3:
        return (output[0, :, :, :], new_x, new_y)
    else:
        return (output, new_x, new_y)

