# Cluster 19

class SWAMovingAverage(object):
    """Maintains moving averages of variables by employing an exponential decay.

  When training a model, it is often beneficial to maintain moving averages of
  the trained parameters.  Evaluations that use averaged parameters sometimes
  produce significantly better results than the final trained values.

  The `apply()` method adds shadow copies of trained variables and add ops that
  maintain a moving average of the trained variables in their shadow copies.
  It is used when building the training model.  The ops that maintain moving
  averages are typically run after each training step.
  The `average()` and `average_name()` methods give access to the shadow
  variables and their names.  They are useful when building an evaluation
  model, or when restoring a model from a checkpoint file.  They help use the
  moving averages in place of the last trained values for evaluations.

  The moving averages are computed using exponential decay.  You specify the
  decay value when creating the `ExponentialMovingAverage` object.  The shadow
  variables are initialized with the same initial values as the trained
  variables.  When you run the ops to maintain the moving averages, each
  shadow variable is updated with the formula:

    `shadow_variable -= (1 - decay) * (shadow_variable - variable)`

  This is mathematically equivalent to the classic formula below, but the use
  of an `assign_sub` op (the `"-="` in the formula) allows concurrent lockless
  updates to the variables:

    `shadow_variable = decay * shadow_variable + (1 - decay) * variable`

  Reasonable values for `decay` are close to 1.0, typically in the
  multiple-nines range: 0.999, 0.9999, etc.

  Example usage when creating a training model:

  ```python
  # Create variables.
  var0 = tf.Variable(...)
  var1 = tf.Variable(...)
  # ... use the variables to build a training model...
  ...
  # Create an op that applies the optimizer.  This is what we usually
  # would use as a training op.
  opt_op = opt.minimize(my_loss, [var0, var1])

  # Create an ExponentialMovingAverage object
  ema = tf.train.ExponentialMovingAverage(decay=0.9999)

  with tf.control_dependencies([opt_op]):
      # Create the shadow variables, and add ops to maintain moving averages
      # of var0 and var1. This also creates an op that will update the moving
      # averages after each training step.  This is what we will use in place
      # of the usual training op.
      training_op = ema.apply([var0, var1])

  ...train the model by running training_op...
  ```

  There are two ways to use the moving averages for evaluations:

  *  Build a model that uses the shadow variables instead of the variables.
     For this, use the `average()` method which returns the shadow variable
     for a given variable.
  *  Build a model normally but load the checkpoint files to evaluate by using
     the shadow variable names.  For this use the `average_name()` method.  See
     the @{tf.train.Saver} for more
     information on restoring saved variables.

  Example of restoring the shadow variable values:

  ```python
  # Create a Saver that loads variables from their saved shadow values.
  shadow_var0_name = ema.average_name(var0)
  shadow_var1_name = ema.average_name(var1)
  saver = tf.train.Saver({shadow_var0_name: var0, shadow_var1_name: var1})
  saver.restore(...checkpoint filename...)
  # var0 and var1 now hold the moving average values
  ```
  """

    def __init__(self, num_updates, zero_debias=False, name='SWAMovingAverage'):
        """Creates a new ExponentialMovingAverage object.

    The `apply()` method has to be called to create shadow variables and add
    ops to maintain moving averages.

    The optional `num_updates` parameter allows one to tweak the decay rate
    dynamically. It is typical to pass the count of training steps, usually
    kept in a variable that is incremented at each step, in which case the
    decay rate is lower at the start of training.  This makes moving averages
    move faster.  If passed, the actual decay rate used is:

      `num_updates / (1 + num_updates)`

    Args:
      decay: Float.  The decay to use.
      num_updates: Optional count of number of updates applied to variables.
      zero_debias: If `True`, zero debias moving-averages that are initialized
        with tensors.
      name: String. Optional prefix name to use for the name of ops added in
        `apply()`.
    """
        self._num_updates = num_updates
        self._zero_debias = zero_debias
        self._name = name
        self._averages = {}

    def apply(self, var_list=None):
        """Maintains moving averages of variables.

    `var_list` must be a list of `Variable` or `Tensor` objects.  This method
    creates shadow variables for all elements of `var_list`.  Shadow variables
    for `Variable` objects are initialized to the variable's initial value.
    They will be added to the `GraphKeys.MOVING_AVERAGE_VARIABLES` collection.
    For `Tensor` objects, the shadow variables are initialized to 0 and zero
    debiased (see docstring in `assign_moving_average` for more details).

    shadow variables are created with `trainable=False` and added to the
    `GraphKeys.ALL_VARIABLES` collection.  They will be returned by calls to
    `tf.global_variables()`.

    Returns an op that updates all shadow variables as described above.

    Note that `apply()` can be called multiple times with different lists of
    variables.

    Args:
      var_list: A list of Variable or Tensor objects. The variables
        and Tensors must be of types float16, float32, or float64.

    Returns:
      An Operation that updates the moving averages.

    Raises:
      TypeError: If the arguments are not all float16, float32, or float64.
      ValueError: If the moving average of one of the variables is already
        being computed.
    """
        if var_list is None:
            var_list = variables.trainable_variables()
        zero_debias_true = set()
        for var in var_list:
            if var.dtype.base_dtype not in [dtypes.float16, dtypes.float32, dtypes.float64]:
                raise TypeError('The variables must be half, float, or double: %s' % var.name)
            if var in self._averages:
                raise ValueError('Moving average already computed for: %s' % var.name)
            with ops.init_scope():
                if isinstance(var, variables.Variable):
                    avg = slot_creator.create_slot(var, var.initialized_value(), self._name, colocate_with_primary=True)
                    ops.add_to_collection(ops.GraphKeys.MOVING_AVERAGE_VARIABLES, var)
                else:
                    avg = slot_creator.create_zeros_slot(var, self._name, colocate_with_primary=var.op.type in ['Variable', 'VariableV2', 'VarHandleOp'])
                    if self._zero_debias:
                        zero_debias_true.add(avg)
            self._averages[var] = avg
        with ops.name_scope(self._name) as scope:
            num_updates = math_ops.cast(self._num_updates, dtypes.float32, name='num_updates')
            decay = num_updates / (1.0 + num_updates)
            decay = array_ops.identity(decay, name='decay')
            updates = []
            for var in var_list:
                zero_debias = self._averages[var] in zero_debias_true
                updates.append(assign_moving_average(self._averages[var], var, decay, zero_debias=zero_debias))
            return control_flow_ops.group(*updates, name=scope)

    def average(self, var):
        """Returns the `Variable` holding the average of `var`.

    Args:
      var: A `Variable` object.

    Returns:
      A `Variable` object or `None` if the moving average of `var`
      is not maintained.
    """
        return self._averages.get(var, None)

    def average_name(self, var):
        """Returns the name of the `Variable` holding the average for `var`.

    The typical scenario for `ExponentialMovingAverage` is to compute moving
    averages of variables during training, and restore the variables from the
    computed moving averages during evaluations.

    To restore variables, you have to know the name of the shadow variables.
    That name and the original variable can then be passed to a `Saver()` object
    to restore the variable from the moving average value with:
      `saver = tf.train.Saver({ema.average_name(var): var})`

    `average_name()` can be called whether or not `apply()` has been called.

    Args:
      var: A `Variable` object.

    Returns:
      A string: The name of the variable that will be used or was used
      by the `ExponentialMovingAverage class` to hold the moving average of
      `var`.
    """
        if var in self._averages:
            return self._averages[var].op.name
        return ops.get_default_graph().unique_name(var.op.name + '/' + self._name, mark_as_used=False)

    def variables_to_restore(self, moving_avg_variables=None):
        """Returns a map of names to `Variables` to restore.

    If a variable has a moving average, use the moving average variable name as
    the restore name; otherwise, use the variable name.

    For example,

    ```python
      variables_to_restore = ema.variables_to_restore()
      saver = tf.train.Saver(variables_to_restore)
    ```

    Below is an example of such mapping:

    ```
      conv/batchnorm/gamma/ExponentialMovingAverage: conv/batchnorm/gamma,
      conv_4/conv2d_params/ExponentialMovingAverage: conv_4/conv2d_params,
      global_step: global_step
    ```
    Args:
      moving_avg_variables: a list of variables that require to use of the
        moving variable name to be restored. If None, it will default to
        variables.moving_average_variables() + variables.trainable_variables()

    Returns:
      A map from restore_names to variables. The restore_name can be the
      moving_average version of the variable name if it exist, or the original
      variable name.
    """
        name_map = {}
        if moving_avg_variables is None:
            moving_avg_variables = variables.trainable_variables()
            moving_avg_variables += variables.moving_average_variables()
        moving_avg_variables = set(moving_avg_variables)
        for v in moving_avg_variables:
            name_map[self.average_name(v)] = v
        moving_avg_variable_names = set([v.name for v in moving_avg_variables])
        for v in list(set(variables.global_variables())):
            if v.name not in moving_avg_variable_names and v.op.name not in name_map:
                name_map[v.op.name] = v
        return name_map

def average(self, var):
    """Returns the `Variable` holding the average of `var`.

    Args:
      var: A `Variable` object.

    Returns:
      A `Variable` object or `None` if the moving average of `var`
      is not maintained.
    """
    return self._averages.get(var, None)

def _process_image(filename):
    image_data = tf.gfile.FastGFile(filename, 'rb').read()
    return (image_data, misc.imread(filename).shape)

def test_dataset():
    filename_queue = tf.train.string_input_producer(['/media/rs/0E06CD1706CD0127/Kapok/Chi/Datasets/tfrecords/blouse_0000.tfrecord'], num_epochs=None)
    reader = tf.TFRecordReader()
    _, serialized_example = reader.read(filename_queue)
    features = tf.parse_single_example(serialized_example, features={'image/height': tf.FixedLenFeature([1], tf.int64), 'image/width': tf.FixedLenFeature([1], tf.int64), 'image/channels': tf.FixedLenFeature([1], tf.int64), 'image/classid': tf.FixedLenFeature([1], tf.int64), 'image/keypoint/x': tf.VarLenFeature(dtype=tf.int64), 'image/keypoint/y': tf.VarLenFeature(dtype=tf.int64), 'image/keypoint/v': tf.VarLenFeature(dtype=tf.int64), 'image/keypoint/id': tf.VarLenFeature(dtype=tf.int64), 'image/keypoint/gid': tf.VarLenFeature(dtype=tf.int64), 'image/format': tf.FixedLenFeature([], tf.string, default_value='jpeg'), 'image/filename': tf.FixedLenFeature([], tf.string, default_value=''), 'image/encoded': tf.FixedLenFeature([], tf.string, default_value='')})
    sess = tf.Session()
    init = tf.initialize_all_variables()
    sess.run(init)
    tf.train.start_queue_runners(sess=sess)
    eval_features = sess.run(features)
    eval_features = sess.run(features)
    eval_features = sess.run(features)
    eval_features = sess.run(features)
    eval_features = sess.run(features)
    eval_features = sess.run(features)
    print('image/height', eval_features['image/height'])
    print('image/width', eval_features['image/width'])
    print('image/channels', eval_features['image/channels'])
    print('image/classid', eval_features['image/classid'])
    print('image/keypoint/x', eval_features['image/keypoint/x'])
    print('image/keypoint/y', eval_features['image/keypoint/y'])
    print('image/keypoint/v', eval_features['image/keypoint/v'])
    print('image/keypoint/id', eval_features['image/keypoint/id'])
    print('image/keypoint/gid', eval_features['image/keypoint/gid'])
    print('image/format', eval_features['image/format'])
    print('image/filename', eval_features['image/filename'].decode('utf8'))

def slim_get_split(dataset_dir, image_preprocessing_fn, batch_size, num_readers, num_preprocessing_threads, num_epochs=None, is_training=True, category='blouse', file_pattern='{}_????', reader=None, return_keypoints=False):
    if reader is None:
        reader = tf.TFRecordReader
    num_joints = config.class_num_joints[category]
    suffix = '.tfrecord' if is_training else '_val.tfrecord'
    file_pattern = file_pattern.format(category) + suffix
    keys_to_features = {'image/encoded': tf.FixedLenFeature((), tf.string, default_value=''), 'image/filename': tf.FixedLenFeature((), tf.string, default_value=''), 'image/format': tf.FixedLenFeature((), tf.string, default_value='jpeg'), 'image/height': tf.FixedLenFeature([1], tf.int64), 'image/width': tf.FixedLenFeature([1], tf.int64), 'image/channels': tf.FixedLenFeature([1], tf.int64), 'image/classid': tf.FixedLenFeature([1], tf.int64), 'image/keypoint/x': tf.VarLenFeature(dtype=tf.int64), 'image/keypoint/y': tf.VarLenFeature(dtype=tf.int64), 'image/keypoint/v': tf.VarLenFeature(dtype=tf.int64), 'image/keypoint/id': tf.VarLenFeature(dtype=tf.int64), 'image/keypoint/gid': tf.VarLenFeature(dtype=tf.int64)}
    items_to_handlers = {'image': slim.tfexample_decoder.Image('image/encoded', 'image/format'), 'height': slim.tfexample_decoder.Tensor('image/height'), 'width': slim.tfexample_decoder.Tensor('image/width'), 'channels': slim.tfexample_decoder.Tensor('image/channels'), 'classid': slim.tfexample_decoder.Tensor('image/classid'), 'keypoint/x': slim.tfexample_decoder.Tensor('image/keypoint/x'), 'keypoint/y': slim.tfexample_decoder.Tensor('image/keypoint/y'), 'keypoint/v': slim.tfexample_decoder.Tensor('image/keypoint/v'), 'keypoint/id': slim.tfexample_decoder.Tensor('image/keypoint/id'), 'keypoint/gid': slim.tfexample_decoder.Tensor('image/keypoint/gid')}
    decoder = slim.tfexample_decoder.TFExampleDecoder(keys_to_features, items_to_handlers)
    input_source = os.path.join(dataset_dir, file_pattern)
    dataset = slim.dataset.Dataset(data_sources=input_source, reader=reader, decoder=decoder, num_samples=config.split_size[category]['train' if is_training else 'val'], items_to_descriptions=None, num_classes=num_joints, labels_to_names=None)
    with tf.name_scope('dataset_data_provider'):
        provider = slim.dataset_data_provider.DatasetDataProvider(dataset, num_readers=num_readers, common_queue_capacity=32 * batch_size, common_queue_min=8 * batch_size, shuffle=True, num_epochs=num_epochs)
    [org_image, height, width, channels, classid, key_x, key_y, key_v, key_id, key_gid] = provider.get(['image', 'height', 'width', 'channels', 'classid', 'keypoint/x', 'keypoint/y', 'keypoint/v', 'keypoint/id', 'keypoint/gid'])
    gather_ind = config.class2global_ind_map[category]
    key_x, key_y, key_v, key_id, key_gid = (tf.gather(key_x, gather_ind), tf.gather(key_y, gather_ind), tf.gather(key_v, gather_ind), tf.gather(key_id, gather_ind), tf.gather(key_gid, gather_ind))
    shape = tf.stack([height, width, channels], axis=0)
    if not return_keypoints:
        image, targets, new_key_v, isvalid, norm_value = image_preprocessing_fn(org_image, classid, shape, key_x, key_y, key_v)
        batch_list = [image, shape, classid, targets, new_key_v, isvalid, norm_value]
    else:
        image, targets, new_key_x, new_key_y, new_key_v, isvalid, norm_value = image_preprocessing_fn(org_image, classid, shape, key_x, key_y, key_v)
        batch_list = [image, shape, classid, targets, new_key_x, new_key_y, new_key_v, isvalid, norm_value]
    batch_input = tf.train.batch(batch_list, dynamic_pad=False, batch_size=batch_size, allow_smaller_final_batch=True, num_threads=num_preprocessing_threads, capacity=64 * batch_size)
    return batch_input

def slim_test_get_split(dataset_dir, image_preprocessing_fn, num_readers, num_preprocessing_threads, category='blouse', file_pattern='{}_*.tfrecord', reader=None, dynamic_pad=False):
    if reader is None:
        reader = tf.TFRecordReader
    num_joints = config.class_num_joints[category]
    file_pattern = file_pattern.format(category)
    keys_to_features = {'image/encoded': tf.FixedLenFeature((), tf.string, default_value=''), 'image/filename': tf.FixedLenFeature((), tf.string, default_value=''), 'image/format': tf.FixedLenFeature((), tf.string, default_value='jpeg'), 'image/height': tf.FixedLenFeature([1], tf.int64), 'image/width': tf.FixedLenFeature([1], tf.int64), 'image/channels': tf.FixedLenFeature([1], tf.int64), 'image/classid': tf.FixedLenFeature([1], tf.int64)}
    items_to_handlers = {'image': slim.tfexample_decoder.Image('image/encoded', 'image/format'), 'height': slim.tfexample_decoder.Tensor('image/height'), 'width': slim.tfexample_decoder.Tensor('image/width'), 'channels': slim.tfexample_decoder.Tensor('image/channels'), 'classid': slim.tfexample_decoder.Tensor('image/classid'), 'filename': slim.tfexample_decoder.Tensor('image/filename')}
    decoder = slim.tfexample_decoder.TFExampleDecoder(keys_to_features, items_to_handlers)
    input_source = os.path.join(dataset_dir, file_pattern)
    dataset = slim.dataset.Dataset(data_sources=input_source, reader=reader, decoder=decoder, num_samples=config.split_size[category]['test'], items_to_descriptions=None, num_classes=num_joints, labels_to_names=None)
    with tf.name_scope('dataset_data_provider'):
        provider = slim.dataset_data_provider.DatasetDataProvider(dataset, num_readers=num_readers, common_queue_capacity=32, common_queue_min=8, shuffle=False, num_epochs=1)
    [org_image, height, width, channels, classid, filename] = provider.get(['image', 'height', 'width', 'channels', 'classid', 'filename'])
    shape = tf.stack([height, width, channels], axis=0)
    if image_preprocessing_fn is not None:
        image, shape, offsets = image_preprocessing_fn(org_image, filename, shape)
    else:
        image = org_image
        offsets = tf.constant([0, 0], tf.int64)
    batch_input = tf.train.batch([image, shape, filename, classid, offsets], dynamic_pad=dynamic_pad, batch_size=1, allow_smaller_final_batch=True, num_threads=num_preprocessing_threads, capacity=64)
    return batch_input

def get_dataset_mean_std():
    all_sub_dirs = []
    for split in config.SPLITS:
        if 'test' not in split:
            for cat in config.CATEGORIES:
                all_sub_dirs.append(os.path.join(config.DATA_DIR, split, 'Images', cat))
    all_image_nums = 0
    means = [0.0, 0.0, 0.0]
    stds = [0.0, 0.0, 0.0]
    for dirs in all_sub_dirs:
        all_images = tf.gfile.Glob(os.path.join(dirs, '*.jpg'))
        for image in all_images:
            np_image = imread(image, mode='RGB')
            if len(np_image.shape) < 3 or np_image.shape[-1] != 3:
                continue
            all_image_nums += 1
            means[0] += np.mean(np_image[:, :, 0]) / 10000.0
            means[1] += np.mean(np_image[:, :, 1]) / 10000.0
            means[2] += np.mean(np_image[:, :, 2]) / 10000.0
            stds[0] += np.std(np_image[:, :, 0]) / 10000.0
            stds[1] += np.std(np_image[:, :, 1]) / 10000.0
            stds[2] += np.std(np_image[:, :, 2]) / 10000.0
        print([_ * 10000.0 / all_image_nums for _ in means])
        print([_ * 10000.0 / all_image_nums for _ in stds])
    print([_ * 10000.0 / all_image_nums for _ in means])
    print([_ * 10000.0 / all_image_nums for _ in stds])
    print(all_image_nums)

