# Cluster 1

def gaussian_blur(inputs, inputs_filters, sigma, data_format, name=None):
    with tf.name_scope(name, 'gaussian_blur', [inputs]):
        data_format_ = 'NHWC' if data_format == 'channels_last' else 'NCHW'
        if data_format_ == 'NHWC':
            inputs = tf.transpose(inputs, [0, 2, 3, 1])
        ksize = int(6 * sigma + 1.0)
        x = tf.expand_dims(tf.range(ksize, delta=1, dtype=tf.float32), axis=1)
        y = tf.transpose(x, [1, 0])
        kernel_matrix = tf.exp(-((x - ksize / 2.0) ** 2 + (y - ksize / 2.0) ** 2) / (2 * sigma ** 2))
        kernel_filter = tf.reshape(kernel_matrix, [ksize, ksize, 1, 1])
        kernel_filter = tf.tile(kernel_filter, [1, 1, inputs_filters, 1])
        outputs = tf.nn.depthwise_conv2d(inputs, kernel_filter, strides=[1, 1, 1, 1], padding='SAME', data_format=data_format_, name='blur')
        if data_format_ == 'NHWC':
            outputs = tf.transpose(outputs, [0, 3, 1, 2])
        return outputs

def gaussian_blur(inputs, inputs_filters, sigma, data_format, name=None):
    with tf.name_scope(name, 'gaussian_blur', [inputs]):
        data_format_ = 'NHWC' if data_format == 'channels_last' else 'NCHW'
        if data_format_ == 'NHWC':
            inputs = tf.transpose(inputs, [0, 2, 3, 1])
        ksize = int(6 * sigma + 1.0)
        x = tf.expand_dims(tf.range(ksize, delta=1, dtype=tf.float32), axis=1)
        y = tf.transpose(x, [1, 0])
        kernel_matrix = tf.exp(-((x - ksize / 2.0) ** 2 + (y - ksize / 2.0) ** 2) / (2 * sigma ** 2))
        kernel_filter = tf.reshape(kernel_matrix, [ksize, ksize, 1, 1])
        kernel_filter = tf.tile(kernel_filter, [1, 1, inputs_filters, 1])
        outputs = tf.nn.depthwise_conv2d(inputs, kernel_filter, strides=[1, 1, 1, 1], padding='SAME', data_format=data_format_, name='blur')
        if data_format_ == 'NHWC':
            outputs = tf.transpose(outputs, [0, 3, 1, 2])
        return outputs

def cond_flip(heatmap_ind):
    return tf.cond(heatmap_ind[1] < tf.shape(features)[0], lambda: heatmap_ind[0], lambda: tf.transpose(tf.image.flip_left_right(tf.transpose(heatmap_ind[0], [1, 2, 0], name='pred_nchw2nhwc')), [2, 0, 1], name='pred_nhwc2nchw'))

def gaussian_blur(inputs, inputs_filters, sigma, data_format, name=None):
    with tf.name_scope(name, 'gaussian_blur', [inputs]):
        data_format_ = 'NHWC' if data_format == 'channels_last' else 'NCHW'
        if data_format_ == 'NHWC':
            inputs = tf.transpose(inputs, [0, 2, 3, 1])
        ksize = int(6 * sigma + 1.0)
        x = tf.expand_dims(tf.range(ksize, delta=1, dtype=tf.float32), axis=1)
        y = tf.transpose(x, [1, 0])
        kernel_matrix = tf.exp(-((x - ksize / 2.0) ** 2 + (y - ksize / 2.0) ** 2) / (2 * sigma ** 2))
        kernel_filter = tf.reshape(kernel_matrix, [ksize, ksize, 1, 1])
        kernel_filter = tf.tile(kernel_filter, [1, 1, inputs_filters, 1])
        outputs = tf.nn.depthwise_conv2d(inputs, kernel_filter, strides=[1, 1, 1, 1], padding='SAME', data_format=data_format_, name='blur')
        if data_format_ == 'NHWC':
            outputs = tf.transpose(outputs, [0, 3, 1, 2])
        return outputs

def gaussian_blur(inputs, inputs_filters, sigma, data_format, name=None):
    with tf.name_scope(name, 'gaussian_blur', [inputs]):
        data_format_ = 'NHWC' if data_format == 'channels_last' else 'NCHW'
        if data_format_ == 'NHWC':
            inputs = tf.transpose(inputs, [0, 2, 3, 1])
        ksize = int(6 * sigma + 1.0)
        x = tf.expand_dims(tf.range(ksize, delta=1, dtype=tf.float32), axis=1)
        y = tf.transpose(x, [1, 0])
        kernel_matrix = tf.exp(-((x - ksize / 2.0) ** 2 + (y - ksize / 2.0) ** 2) / (2 * sigma ** 2))
        kernel_filter = tf.reshape(kernel_matrix, [ksize, ksize, 1, 1])
        kernel_filter = tf.tile(kernel_filter, [1, 1, inputs_filters, 1])
        outputs = tf.nn.depthwise_conv2d(inputs, kernel_filter, strides=[1, 1, 1, 1], padding='SAME', data_format=data_format_, name='blur')
        if data_format_ == 'NHWC':
            outputs = tf.transpose(outputs, [0, 3, 1, 2])
        return outputs

def gaussian_blur(inputs, inputs_filters, sigma, data_format, name=None):
    with tf.name_scope(name, 'gaussian_blur', [inputs]):
        data_format_ = 'NHWC' if data_format == 'channels_last' else 'NCHW'
        if data_format_ == 'NHWC':
            inputs = tf.transpose(inputs, [0, 2, 3, 1])
        ksize = int(6 * sigma + 1.0)
        x = tf.expand_dims(tf.range(ksize, delta=1, dtype=tf.float32), axis=1)
        y = tf.transpose(x, [1, 0])
        kernel_matrix = tf.exp(-((x - ksize / 2.0) ** 2 + (y - ksize / 2.0) ** 2) / (2 * sigma ** 2))
        kernel_filter = tf.reshape(kernel_matrix, [ksize, ksize, 1, 1])
        kernel_filter = tf.tile(kernel_filter, [1, 1, inputs_filters, 1])
        outputs = tf.nn.depthwise_conv2d(inputs, kernel_filter, strides=[1, 1, 1, 1], padding='SAME', data_format=data_format_, name='blur')
        if data_format_ == 'NHWC':
            outputs = tf.transpose(outputs, [0, 3, 1, 2])
        return outputs

def cond_flip(heatmap_ind):
    return tf.cond(heatmap_ind[1] < tf.shape(features)[0], lambda: heatmap_ind[0], lambda: tf.transpose(tf.image.flip_left_right(tf.transpose(heatmap_ind[0], [1, 2, 0], name='pred_nchw2nhwc')), [2, 0, 1], name='pred_nhwc2nchw'))

def gaussian_blur(inputs, inputs_filters, sigma, data_format, name=None):
    with tf.name_scope(name, 'gaussian_blur', [inputs]):
        data_format_ = 'NHWC' if data_format == 'channels_last' else 'NCHW'
        if data_format_ == 'NHWC':
            inputs = tf.transpose(inputs, [0, 2, 3, 1])
        ksize = int(6 * sigma + 1.0)
        x = tf.expand_dims(tf.range(ksize, delta=1, dtype=tf.float32), axis=1)
        y = tf.transpose(x, [1, 0])
        kernel_matrix = tf.exp(-((x - ksize / 2.0) ** 2 + (y - ksize / 2.0) ** 2) / (2 * sigma ** 2))
        kernel_filter = tf.reshape(kernel_matrix, [ksize, ksize, 1, 1])
        kernel_filter = tf.tile(kernel_filter, [1, 1, inputs_filters, 1])
        outputs = tf.nn.depthwise_conv2d(inputs, kernel_filter, strides=[1, 1, 1, 1], padding='SAME', data_format=data_format_, name='blur')
        if data_format_ == 'NHWC':
            outputs = tf.transpose(outputs, [0, 3, 1, 2])
        return outputs

def gaussian_blur(inputs, inputs_filters, sigma, data_format, name=None):
    with tf.name_scope(name, 'gaussian_blur', [inputs]):
        data_format_ = 'NHWC' if data_format == 'channels_last' else 'NCHW'
        if data_format_ == 'NHWC':
            inputs = tf.transpose(inputs, [0, 2, 3, 1])
        ksize = int(6 * sigma + 1.0)
        x = tf.expand_dims(tf.range(ksize, delta=1, dtype=tf.float32), axis=1)
        y = tf.transpose(x, [1, 0])
        kernel_matrix = tf.exp(-((x - ksize / 2.0) ** 2 + (y - ksize / 2.0) ** 2) / (2 * sigma ** 2))
        kernel_filter = tf.reshape(kernel_matrix, [ksize, ksize, 1, 1])
        kernel_filter = tf.tile(kernel_filter, [1, 1, inputs_filters, 1])
        outputs = tf.nn.depthwise_conv2d(inputs, kernel_filter, strides=[1, 1, 1, 1], padding='SAME', data_format=data_format_, name='blur')
        if data_format_ == 'NHWC':
            outputs = tf.transpose(outputs, [0, 3, 1, 2])
        return outputs

def cond_flip(heatmap_ind):
    return tf.cond(heatmap_ind[1] < tf.shape(features)[0], lambda: heatmap_ind[0], lambda: tf.transpose(tf.image.flip_left_right(tf.transpose(heatmap_ind[0], [1, 2, 0], name='pred_nchw2nhwc')), [2, 0, 1], name='pred_nhwc2nchw'))

def gaussian_blur(inputs, inputs_filters, sigma, data_format, name=None):
    with tf.name_scope(name, 'gaussian_blur', [inputs]):
        data_format_ = 'NHWC' if data_format == 'channels_last' else 'NCHW'
        if data_format_ == 'NHWC':
            inputs = tf.transpose(inputs, [0, 2, 3, 1])
        ksize = int(6 * sigma + 1.0)
        x = tf.expand_dims(tf.range(ksize, delta=1, dtype=tf.float32), axis=1)
        y = tf.transpose(x, [1, 0])
        kernel_matrix = tf.exp(-((x - ksize / 2.0) ** 2 + (y - ksize / 2.0) ** 2) / (2 * sigma ** 2))
        kernel_filter = tf.reshape(kernel_matrix, [ksize, ksize, 1, 1])
        kernel_filter = tf.tile(kernel_filter, [1, 1, inputs_filters, 1])
        outputs = tf.nn.depthwise_conv2d(inputs, kernel_filter, strides=[1, 1, 1, 1], padding='SAME', data_format=data_format_, name='blur')
        if data_format_ == 'NHWC':
            outputs = tf.transpose(outputs, [0, 3, 1, 2])
        return outputs

def block_layer(inputs, filters, bottleneck, block_fn, blocks, strides, training, name, data_format):
    """Creates one layer of blocks for the ResNet model.

    Args:
      inputs: A tensor of size [batch, channels, height_in, width_in] or
        [batch, height_in, width_in, channels] depending on data_format.
      filters: The number of filters for the first convolution of the layer.
      bottleneck: Is the block created a bottleneck block.
      block_fn: The block to use within the model, either `building_block` or
        `bottleneck_block`.
      blocks: The number of blocks contained in the layer.
      strides: The stride to use for the first convolution of the layer. If
        greater than 1, this layer will ultimately downsample the input.
      training: Either True or False, whether we are currently training the
        model. Needed for batch norm.
      name: A string name for the tensor output of the block layer.
      data_format: The input format ('channels_last' or 'channels_first').

    Returns:
      The output tensor of the block layer.
    """
    filters_out = filters * 4 if bottleneck else filters

    def projection_shortcut(inputs):
        return conv2d_fixed_padding(inputs=inputs, filters=filters_out, kernel_size=1, strides=strides, data_format=data_format)
    inputs = block_fn(inputs, filters, training, projection_shortcut, strides, data_format)
    for _ in range(1, blocks):
        inputs = block_fn(inputs, filters, training, None, 1, data_format)
    return tf.identity(inputs, name)

def block_layer(inputs, filters, bottleneck, block_fn, blocks, strides, training, name, data_format):
    """Creates one layer of blocks for the ResNet model.

    Args:
      inputs: A tensor of size [batch, channels, height_in, width_in] or
        [batch, height_in, width_in, channels] depending on data_format.
      filters: The number of filters for the first convolution of the layer.
      bottleneck: Is the block created a bottleneck block.
      block_fn: The block to use within the model, either `building_block` or
        `bottleneck_block`.
      blocks: The number of blocks contained in the layer.
      strides: The stride to use for the first convolution of the layer. If
        greater than 1, this layer will ultimately downsample the input.
      training: Either True or False, whether we are currently training the
        model. Needed for batch norm.
      name: A string name for the tensor output of the block layer.
      data_format: The input format ('channels_last' or 'channels_first').

    Returns:
      The output tensor of the block layer.
    """
    filters_out = filters * 4 if bottleneck else filters

    def projection_shortcut(inputs):
        return conv2d_fixed_padding(inputs=inputs, filters=filters_out, kernel_size=1, strides=strides, data_format=data_format)
    inputs = block_fn(inputs, filters, training, projection_shortcut, strides, data_format)
    for _ in range(1, blocks):
        inputs = block_fn(inputs, filters, training, None, 1, data_format)
    return tf.identity(inputs, name)

def dilated_block_layer(inputs, filters, bottleneck, block_fn, blocks, training, name, data_format):
    filters_out = filters * 4 if bottleneck else filters

    def projection_shortcut(inputs):
        return conv2d_fixed_padding(inputs=inputs, filters=filters_out, kernel_size=1, strides=1, data_format=data_format)
    inputs = block_fn(inputs, filters, training, projection_shortcut, data_format)
    for _ in range(1, blocks):
        inputs = block_fn(inputs, filters, training, None, data_format)
    return tf.identity(inputs, name)

def dozen_bottleneck_blocks(inputs, in_filters, out_filters, num_modules, is_training, data_format, name=None):
    for m in range(num_modules):
        inputs = bottleneck_block(inputs, in_filters, out_filters, is_training, data_format, name=None if name is None else name.format(m))
    return inputs

def block_layer(inputs, filters, bottleneck, block_fn, blocks, strides, training, name, data_format):
    """Creates one layer of blocks for the ResNet model.

    Args:
      inputs: A tensor of size [batch, channels, height_in, width_in] or
        [batch, height_in, width_in, channels] depending on data_format.
      filters: The number of filters for the first convolution of the layer.
      bottleneck: Is the block created a bottleneck block.
      block_fn: The block to use within the model, either `building_block` or
        `bottleneck_block`.
      blocks: The number of blocks contained in the layer.
      strides: The stride to use for the first convolution of the layer. If
        greater than 1, this layer will ultimately downsample the input.
      training: Either True or False, whether we are currently training the
        model. Needed for batch norm.
      name: A string name for the tensor output of the block layer.
      data_format: The input format ('channels_last' or 'channels_first').

    Returns:
      The output tensor of the block layer.
    """
    filters_out = filters * 4 if bottleneck else filters

    def projection_shortcut(inputs):
        return conv2d_fixed_padding(inputs=inputs, filters=filters_out, kernel_size=1, strides=strides, data_format=data_format)
    inputs = block_fn(inputs, filters, training, projection_shortcut, strides, data_format)
    for _ in range(1, blocks):
        inputs = block_fn(inputs, filters, training, None, 1, data_format)
    return tf.identity(inputs, name)

def _smallest_size_at_least(height, width, smallest_side):
    """Computes new shape with the smallest side equal to `smallest_side`.

  Computes new shape with the smallest side equal to `smallest_side` while
  preserving the original aspect ratio.

  Args:
    height: an int32 scalar tensor indicating the current height.
    width: an int32 scalar tensor indicating the current width.
    smallest_side: A python integer or scalar `Tensor` indicating the size of
      the smallest side after resize.

  Returns:
    new_height: an int32 scalar tensor indicating the new height.
    new_width: and int32 scalar tensor indicating the new width.
  """
    smallest_side = tf.convert_to_tensor(smallest_side, dtype=tf.int32)
    height = tf.to_float(height)
    width = tf.to_float(width)
    smallest_side = tf.to_float(smallest_side)
    scale = tf.cond(tf.greater(height, width), lambda: smallest_side / width, lambda: smallest_side / height)
    new_height = tf.to_int32(tf.rint(height * scale))
    new_width = tf.to_int32(tf.rint(width * scale))
    return (new_height, new_width)

def preprocess_for_train(image, classid, shape, output_height, output_width, key_x, key_y, key_v, norm_table, data_format, category, bbox_border, heatmap_sigma, heatmap_size, return_keypoints=False, resize_side_min=_RESIZE_SIDE_MIN, resize_side_max=_RESIZE_SIDE_MAX, fast_mode=False, scope=None, add_image_summaries=True):
    """Preprocesses the given image for training.

  Note that the actual resizing scale is sampled from
    [`resize_size_min`, `resize_size_max`].

  Args:
    image: A `Tensor` representing an image of arbitrary size.
    output_height: The height of the image after preprocessing.
    output_width: The width of the image after preprocessing.
    resize_side_min: The lower bound for the smallest side of the image for
      aspect-preserving resizing.
    resize_side_max: The upper bound for the smallest side of the image for
      aspect-preserving resizing.

  Returns:
    A preprocessed image.
  """
    with tf.name_scope(scope, 'vgg_distort_image', [image, output_height, output_width]):
        orig_dtype = image.dtype
        if orig_dtype != tf.float32:
            image = tf.image.convert_image_dtype(image, dtype=tf.float32)
        num_distort_cases = 1 if fast_mode else 4
        distorted_image = apply_with_random_selector(image, lambda x, ordering: distort_color(x, ordering, fast_mode), num_cases=num_distort_cases)
        distorted_image = tf.to_float(tf.image.convert_image_dtype(distorted_image, orig_dtype, saturate=True))
        if add_image_summaries:
            tf.summary.image('color_distorted_image', tf.cast(tf.expand_dims(distorted_image, 0), tf.uint8))
        normarlized_image = _mean_image_subtraction(distorted_image, [_R_MEAN, _G_MEAN, _B_MEAN])
        fkey_x, fkey_y = (tf.cast(key_x, tf.float32), tf.cast(key_y, tf.float32))
        image, fkey_x, fkey_y, bbox = rotate_augum(normarlized_image, shape, fkey_x, fkey_y, bbox_border)
        distorted_image, distorted_bbox = distorted_bounding_box_crop(image, bbox)
        distorted_bbox = tf.squeeze(distorted_bbox)
        fkey_x = fkey_x - distorted_bbox[1]
        fkey_y = fkey_y - distorted_bbox[0]
        outside_x = fkey_x >= distorted_bbox[3]
        outside_y = fkey_y >= distorted_bbox[2]
        fkey_x = fkey_x - tf.cast(outside_x, tf.float32)
        fkey_y = fkey_y - tf.cast(outside_y, tf.float32)
        fkey_x = fkey_x / (distorted_bbox[3] - distorted_bbox[1])
        fkey_y = fkey_y / (distorted_bbox[2] - distorted_bbox[0])
        distorted_image.set_shape([None, None, 3])
        if add_image_summaries:
            tf.summary.image('cropped_image', tf.expand_dims(distorted_image, 0))
        num_resize_cases = 1 if fast_mode else 4
        distorted_image = apply_with_random_selector(distorted_image, lambda x, method: tf.image.resize_images(x, [output_height, output_width], method), num_cases=num_resize_cases)
        distorted_image.set_shape([output_height, output_width, 3])
        ikey_x = tf.cast(tf.round(fkey_x * heatmap_size), tf.int64)
        ikey_y = tf.cast(tf.round(fkey_y * heatmap_size), tf.int64)
        gather_ind = config.left_right_remap[category]
        if add_image_summaries:
            tf.summary.image('cropped_resized_image', tf.expand_dims(distorted_image, 0))
        distorted_image, new_key_x, new_key_y, new_key_v = tf.cond(tf.random_uniform([1], minval=0.0, maxval=1.0, dtype=tf.float32)[0] < 0.5, lambda: (tf.image.flip_left_right(distorted_image), heatmap_size - tf.gather(ikey_x, gather_ind), tf.gather(ikey_y, gather_ind), tf.gather(key_v, gather_ind)), lambda: (distorted_image, ikey_x, ikey_y, key_v))
        targets, isvalid = draw_labelmap(new_key_x, new_key_y, heatmap_sigma, heatmap_size)
        norm_gather_ind = tf.stack([norm_table[0].lookup(classid), norm_table[1].lookup(classid)], axis=-1)
        scale_x_ = tf.cast(output_width, tf.float32) / tf.cast(shape[1], tf.float32)
        scale_y_ = tf.cast(output_height, tf.float32) / tf.cast(shape[0], tf.float32)
        scale_x = tf.cast(output_width, tf.float32) / tf.cast(heatmap_size, tf.float32)
        scale_y = tf.cast(output_height, tf.float32) / tf.cast(heatmap_size, tf.float32)
        norm_x, norm_y = tf.cond(tf.reduce_sum(tf.gather(isvalid, norm_gather_ind)) < 2, lambda: (tf.cast(tf.gather(key_x, norm_gather_ind), tf.float32) * scale_x_, tf.cast(tf.gather(key_y, norm_gather_ind), tf.float32) * scale_y_), lambda: (tf.cast(tf.gather(new_key_x, norm_gather_ind), tf.float32) * scale_x, tf.cast(tf.gather(new_key_y, norm_gather_ind), tf.float32) * scale_y))
        norm_x, norm_y = (tf.squeeze(norm_x), tf.squeeze(norm_y))
        norm_value = tf.pow(tf.pow(norm_x[0] - norm_x[1], 2.0) + tf.pow(norm_y[0] - norm_y[1], 2.0), 0.5)
        if config.DEBUG:
            save_image_op = tf.py_func(save_image_with_heatmap, [unwhiten_image(distorted_image), targets, config.left_right_group_map[category][0], config.left_right_group_map[category][1], config.left_right_group_map[category][2], [output_height, output_width], heatmap_size], tf.int64, stateful=True)
            with tf.control_dependencies([save_image_op]):
                distorted_image = distorted_image / 255.0
        else:
            distorted_image = distorted_image / 255.0
        if data_format == 'NCHW':
            distorted_image = tf.transpose(distorted_image, perm=(2, 0, 1))
        if not return_keypoints:
            return (distorted_image, targets, new_key_v, isvalid, norm_value)
        else:
            return (distorted_image, targets, new_key_x, new_key_y, new_key_v, isvalid, norm_value)

def preprocess_for_train_v0(image, classid, shape, output_height, output_width, key_x, key_y, key_v, norm_table, data_format, category, bbox_border, heatmap_sigma, heatmap_size, return_keypoints=False, resize_side_min=_RESIZE_SIDE_MIN, resize_side_max=_RESIZE_SIDE_MAX, fast_mode=True, scope=None, add_image_summaries=True):
    """Preprocesses the given image for training.

  Note that the actual resizing scale is sampled from
    [`resize_size_min`, `resize_size_max`].

  Args:
    image: A `Tensor` representing an image of arbitrary size.
    output_height: The height of the image after preprocessing.
    output_width: The width of the image after preprocessing.
    resize_side_min: The lower bound for the smallest side of the image for
      aspect-preserving resizing.
    resize_side_max: The upper bound for the smallest side of the image for
      aspect-preserving resizing.

  Returns:
    A preprocessed image.
  """
    with tf.name_scope(scope, 'vgg_distort_image', [image, output_height, output_width]):
        fkey_x, fkey_y = (tf.cast(key_x, tf.float32), tf.cast(key_y, tf.float32))
        image, fkey_x, fkey_y, bbox = rotate_augum(image, shape, fkey_x, fkey_y, bbox_border)
        distorted_image, distorted_bbox = distorted_bounding_box_crop(image, bbox)
        distorted_bbox = tf.squeeze(distorted_bbox)
        fkey_x = fkey_x - distorted_bbox[1]
        fkey_y = fkey_y - distorted_bbox[0]
        outside_x = fkey_x >= distorted_bbox[3]
        outside_y = fkey_y >= distorted_bbox[2]
        fkey_x = fkey_x - tf.cast(outside_x, tf.float32)
        fkey_y = fkey_y - tf.cast(outside_y, tf.float32)
        fkey_x = fkey_x / (distorted_bbox[3] - distorted_bbox[1])
        fkey_y = fkey_y / (distorted_bbox[2] - distorted_bbox[0])
        distorted_image.set_shape([None, None, 3])
        if add_image_summaries:
            tf.summary.image('cropped_image', tf.expand_dims(distorted_image, 0))
        num_resize_cases = 1 if fast_mode else 4
        distorted_image = apply_with_random_selector(distorted_image, lambda x, method: tf.image.resize_images(x, [output_height, output_width], method), num_cases=num_resize_cases)
        distorted_image.set_shape([output_height, output_width, 3])
        ikey_x = tf.cast(tf.round(fkey_x * heatmap_size), tf.int64)
        ikey_y = tf.cast(tf.round(fkey_y * heatmap_size), tf.int64)
        gather_ind = config.left_right_remap[category]
        if add_image_summaries:
            tf.summary.image('cropped_resized_image', tf.expand_dims(distorted_image, 0))
        distorted_image, new_key_x, new_key_y, new_key_v = tf.cond(tf.random_uniform([1], minval=0.0, maxval=1.0, dtype=tf.float32)[0] < 0.5, lambda: (tf.image.flip_left_right(distorted_image), heatmap_size - tf.gather(ikey_x, gather_ind), tf.gather(ikey_y, gather_ind), tf.gather(key_v, gather_ind)), lambda: (distorted_image, ikey_x, ikey_y, key_v))
        distorted_image = tf.to_float(distorted_image)
        num_distort_cases = 1 if fast_mode else 4
        distorted_image = apply_with_random_selector(distorted_image, lambda x, ordering: distort_color_v0(x, ordering, fast_mode), num_cases=num_distort_cases)
        if add_image_summaries:
            tf.summary.image('final_distorted_image', tf.cast(tf.expand_dims(distorted_image, 0), tf.uint8))
        targets, isvalid = draw_labelmap(new_key_x, new_key_y, heatmap_sigma, heatmap_size)
        norm_gather_ind = tf.stack([norm_table[0].lookup(classid), norm_table[1].lookup(classid)], axis=-1)
        scale_x_ = tf.cast(output_width, tf.float32) / tf.cast(shape[1], tf.float32)
        scale_y_ = tf.cast(output_height, tf.float32) / tf.cast(shape[0], tf.float32)
        scale_x = tf.cast(output_width, tf.float32) / tf.cast(heatmap_size, tf.float32)
        scale_y = tf.cast(output_height, tf.float32) / tf.cast(heatmap_size, tf.float32)
        norm_x, norm_y = tf.cond(tf.reduce_sum(tf.gather(isvalid, norm_gather_ind)) < 2, lambda: (tf.cast(tf.gather(key_x, norm_gather_ind), tf.float32) * scale_x_, tf.cast(tf.gather(key_y, norm_gather_ind), tf.float32) * scale_y_), lambda: (tf.cast(tf.gather(new_key_x, norm_gather_ind), tf.float32) * scale_x, tf.cast(tf.gather(new_key_y, norm_gather_ind), tf.float32) * scale_y))
        norm_x, norm_y = (tf.squeeze(norm_x), tf.squeeze(norm_y))
        norm_value = tf.pow(tf.pow(norm_x[0] - norm_x[1], 2.0) + tf.pow(norm_y[0] - norm_y[1], 2.0), 0.5)
        if config.DEBUG:
            save_image_op = tf.py_func(save_image_with_heatmap, [distorted_image, targets, config.left_right_group_map[category][0], config.left_right_group_map[category][1], config.left_right_group_map[category][2], [output_height, output_width], heatmap_size], tf.int64, stateful=True)
            with tf.control_dependencies([save_image_op]):
                normarlized_image = _mean_image_subtraction(distorted_image, [_R_MEAN, _G_MEAN, _B_MEAN])
        else:
            normarlized_image = _mean_image_subtraction(distorted_image, [_R_MEAN, _G_MEAN, _B_MEAN])
        if data_format == 'NCHW':
            normarlized_image = tf.transpose(normarlized_image, perm=(2, 0, 1))
        return (normarlized_image / 255.0, targets, new_key_v, isvalid, norm_value)

def preprocess_for_eval(image, classid, shape, output_height, output_width, key_x, key_y, key_v, norm_table, data_format, category, bbox_border, heatmap_sigma, heatmap_size, resize_side, scope=None):
    """Preprocesses the given image for evaluation.

  Args:
    image: A `Tensor` representing an image of arbitrary size.
    output_height: The height of the image after preprocessing.
    output_width: The width of the image after preprocessing.
    resize_side: The smallest side of the image for aspect-preserving resizing.

  Returns:
    A preprocessed image.
  """
    with tf.name_scope(scope, 'vgg_eval_image', [image, output_height, output_width]):
        fkey_x, fkey_y = (tf.cast(key_x, tf.float32) / tf.cast(shape[1], tf.float32), tf.cast(key_y, tf.float32) / tf.cast(shape[0], tf.float32))
        image = tf.expand_dims(image, 0)
        image = tf.image.resize_bilinear(image, [output_height, output_width], align_corners=False)
        image = tf.squeeze(image, [0])
        image.set_shape([output_height, output_width, 3])
        image = tf.to_float(image)
        ikey_x = tf.cast(tf.round(fkey_x * heatmap_size), tf.int64)
        ikey_y = tf.cast(tf.round(fkey_y * heatmap_size), tf.int64)
        targets, isvalid = draw_labelmap(ikey_x, ikey_y, heatmap_sigma, heatmap_size)
        norm_gather_ind = tf.stack([norm_table[0].lookup(classid), norm_table[1].lookup(classid)], axis=-1)
        key_x = tf.cast(tf.round(fkey_x * output_width), tf.int64)
        key_y = tf.cast(tf.round(fkey_y * output_height), tf.int64)
        norm_x, norm_y = (tf.cast(tf.gather(key_x, norm_gather_ind), tf.float32), tf.cast(tf.gather(key_y, norm_gather_ind), tf.float32))
        norm_x, norm_y = (tf.squeeze(norm_x), tf.squeeze(norm_y))
        norm_value = tf.pow(tf.pow(norm_x[0] - norm_x[1], 2.0) + tf.pow(norm_y[0] - norm_y[1], 2.0), 0.5)
        if config.DEBUG:
            save_image_op = tf.py_func(save_image_with_heatmap, [image, targets, config.left_right_group_map[category][0], config.left_right_group_map[category][1], config.left_right_group_map[category][2], [output_height, output_width], heatmap_size], tf.int64, stateful=True)
            with tf.control_dependencies([save_image_op]):
                normarlized_image = _mean_image_subtraction(image, [_R_MEAN, _G_MEAN, _B_MEAN])
        else:
            normarlized_image = _mean_image_subtraction(image, [_R_MEAN, _G_MEAN, _B_MEAN])
        if data_format == 'NCHW':
            normarlized_image = tf.transpose(normarlized_image, perm=(2, 0, 1))
        return (normarlized_image / 255.0, targets, key_v, isvalid, norm_value)

def preprocess_for_test_v0(image, shape, output_height, output_width, data_format='NCHW', bbox_border=25.0, heatmap_sigma=1.0, heatmap_size=64, scope=None):
    """Preprocesses the given image for evaluation.

  Args:
    image: A `Tensor` representing an image of arbitrary size.
    output_height: The height of the image after preprocessing.
    output_width: The width of the image after preprocessing.

  Returns:
    A preprocessed image.
  """
    with tf.name_scope(scope, 'vgg_test_image', [image, output_height, output_width]):
        image = tf.expand_dims(image, 0)
        image = tf.image.resize_bilinear(image, [output_height, output_width], align_corners=False)
        image = tf.squeeze(image, [0])
        image.set_shape([output_height, output_width, 3])
        image = tf.to_float(image)
        normarlized_image = _mean_image_subtraction(image, [_R_MEAN, _G_MEAN, _B_MEAN])
        if data_format == 'NCHW':
            normarlized_image = tf.transpose(normarlized_image, perm=(2, 0, 1))
        return normarlized_image / 255.0

def preprocess_for_test(image, file_name, shape, output_height, output_width, data_format='NCHW', bbox_border=25.0, heatmap_sigma=1.0, heatmap_size=64, pred_df=None, scope=None):
    """Preprocesses the given image for evaluation.

  Args:
    image: A `Tensor` representing an image of arbitrary size.
    output_height: The height of the image after preprocessing.
    output_width: The width of the image after preprocessing.

  Returns:
    A preprocessed image.
  """
    with tf.name_scope(scope, 'vgg_test_image', [image, output_height, output_width]):
        if pred_df is not None:
            xmin, ymin, xmax, ymax = [table_.lookup(file_name) for table_ in pred_df]
            height, width, channals = tf.unstack(shape, axis=0)
            xmin, ymin, xmax, ymax = (xmin - 100, ymin - 80, xmax + 100, ymax + 80)
            xmin, ymin, xmax, ymax = (tf.clip_by_value(xmin, 0, width[0] - 1), tf.clip_by_value(ymin, 0, height[0] - 1), tf.clip_by_value(xmax, 0, width[0] - 1), tf.clip_by_value(ymax, 0, height[0] - 1))
            bbox_h = ymax - ymin
            bbox_w = xmax - xmin
            areas = bbox_h * bbox_w
            offsets = tf.stack([xmin, ymin], axis=0)
            crop_shape = tf.stack([bbox_h, bbox_w, channals[0]], axis=0)
            ymin, xmin, bbox_h, bbox_w = (tf.cast(ymin, tf.int32), tf.cast(xmin, tf.int32), tf.cast(bbox_h, tf.int32), tf.cast(bbox_w, tf.int32))
            crop_image = tf.image.crop_to_bounding_box(image, ymin, xmin, bbox_h, bbox_w)
            image, shape, offsets = tf.cond(areas > 0, lambda: (crop_image, crop_shape, offsets), lambda: (image, shape, tf.constant([0, 0], tf.int64)))
            offsets.set_shape([2])
            shape.set_shape([3])
        else:
            offsets = tf.constant([0, 0], tf.int64)
        image = tf.expand_dims(image, 0)
        image = tf.image.resize_bilinear(image, [output_height, output_width], align_corners=False)
        image = tf.squeeze(image, [0])
        image.set_shape([output_height, output_width, 3])
        if config.DEBUG:
            save_image_op = tf.py_func(_save_image, [image], tf.int64, stateful=True)
            image = tf.Print(image, [save_image_op])
        image = tf.to_float(image)
        normarlized_image = _mean_image_subtraction(image, [_R_MEAN, _G_MEAN, _B_MEAN])
        if data_format == 'NCHW':
            normarlized_image = tf.transpose(normarlized_image, perm=(2, 0, 1))
        return (normarlized_image / 255.0, shape, offsets)

def preprocess_for_test_raw_output(image, output_height, output_width, data_format='NCHW', scope=None):
    """Preprocesses the given image for evaluation.

  Args:
    image: A `Tensor` representing an image of arbitrary size.
    output_height: The height of the image after preprocessing.
    output_width: The width of the image after preprocessing.

  Returns:
    A preprocessed image.
  """
    with tf.name_scope(scope, 'vgg_test_image_raw_output', [image, output_height, output_width]):
        image = tf.image.resize_bilinear(image, [output_height, output_width], align_corners=False)
        image = tf.squeeze(image, [0])
        image.set_shape([output_height, output_width, 3])
        if config.DEBUG:
            save_image_op = tf.py_func(_save_image, [image], tf.int64, stateful=True)
            image = tf.Print(image, [save_image_op])
        image = tf.to_float(image)
        normarlized_image = _mean_image_subtraction(image, [_R_MEAN, _G_MEAN, _B_MEAN])
        if data_format == 'NCHW':
            normarlized_image = tf.transpose(normarlized_image, perm=(2, 0, 1))
        return tf.expand_dims(normarlized_image / 255.0, 0)

def _aspect_preserving_resize(image, resize_min):
    """Resize images preserving the original aspect ratio.

  Args:
    image: A 3-D image `Tensor`.
    resize_min: A python integer or scalar `Tensor` indicating the size of
      the smallest side after resize.

  Returns:
    resized_image: A 3-D tensor containing the resized image.
  """
    shape = tf.shape(image)
    height, width = (shape[0], shape[1])
    new_height, new_width = _smallest_size_at_least(height, width, resize_min)
    return _resize_image(image, new_height, new_width)

def _resize_image(image, height, width):
    """Simple wrapper around tf.resize_images.

  This is primarily to make sure we use the same `ResizeMethod` and other
  details each time.

  Args:
    image: A 3-D image `Tensor`.
    height: The target height for the resized image.
    width: The target width for the resized image.

  Returns:
    resized_image: A 3-D tensor containing the resized image. The first two
      dimensions have the shape [height, width].
  """
    return tf.image.resize_images(image, [height, width], method=tf.image.ResizeMethod.BILINEAR, align_corners=False)

def preprocess_image(image_buffer, bbox, output_height, output_width, num_channels, is_training=False):
    """Preprocesses the given image.

  Preprocessing includes decoding, cropping, and resizing for both training
  and eval images. Training preprocessing, however, introduces some random
  distortion of the image to improve accuracy.

  Args:
    image_buffer: scalar string Tensor representing the raw JPEG image buffer.
    bbox: 3-D float Tensor of bounding boxes arranged [1, num_boxes, coords]
      where each coordinate is [0, 1) and the coordinates are arranged as
      [ymin, xmin, ymax, xmax].
    output_height: The height of the image after preprocessing.
    output_width: The width of the image after preprocessing.
    num_channels: Integer depth of the image buffer for decoding.
    is_training: `True` if we're preprocessing the image for training and
      `False` otherwise.

  Returns:
    A preprocessed image.
  """
    if is_training:
        image = _decode_crop_and_flip(image_buffer, bbox, num_channels)
        image = _resize_image(image, output_height, output_width)
    else:
        image = tf.image.decode_jpeg(image_buffer, channels=num_channels)
        image = _aspect_preserving_resize(image, _RESIZE_MIN)
        image = _central_crop(image, output_height, output_width)
    image.set_shape([output_height, output_width, num_channels])
    return _mean_image_subtraction(image, _CHANNEL_MEANS, num_channels)

