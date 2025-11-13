# Cluster 6

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

def int64_feature(value):
    if not isinstance(value, list):
        value = [value]
    return tf.train.Feature(int64_list=tf.train.Int64List(value=value))

def float_feature(value):
    if not isinstance(value, list):
        value = [value]
    return tf.train.Feature(float_list=tf.train.FloatList(value=value))

def bytes_feature(value):
    if not isinstance(value, list):
        value = [value]
    return tf.train.Feature(bytes_list=tf.train.BytesList(value=value))

def _replicate_model_fn_with_mode(model_fn, loss_reduction, devices=None, mode=_VariableDistributionMode.SHARED_LOCAL_PARAMETER_SERVER):
    """A version of `replicate_model_fn` that allows to specify a `mode`."""
    if loss_reduction == losses.Reduction.NONE:
        raise ValueError('Tower losses need to be reduced in some way, yet {} reduction is specified.'.format(loss_reduction))
    if not devices:
        devices = _get_local_devices('GPU') or _get_local_devices('CPU')
    is_a_single_gpu_case = len(devices) == 1 and 'GPU' in devices[0]
    consolidation_device = devices[0] if is_a_single_gpu_case else '/CPU:0'
    ps_devices = [consolidation_device]
    if mode == _VariableDistributionMode.SHARED_ROUND_ROBIN:
        ps_devices = devices
    tf_logging.info('Replicating the `model_fn` across {}.  Variables are going to be placed on {}.  Consolidation device is going to be {}.'.format(devices, ps_devices, consolidation_device))

    def single_device_model_fn(features, labels, mode, params=None, config=None):
        """`model_fn` on a single device without reduction overhead."""
        return _get_loss_towers(model_fn=model_fn, mode=mode, features=[features], labels=[labels], params=params, loss_reduction=loss_reduction, config=config, devices=devices, local_ps_devices=ps_devices)[0]

    def replicated_model_fn(features, labels, mode, params=None, config=None):
        """Replicated version of `model_fn` to be used instead."""
        feature_shards, label_shards = _split_batch(features, labels, len(devices), device=consolidation_device)
        tower_specs = _get_loss_towers(model_fn=model_fn, mode=mode, features=feature_shards, labels=label_shards, params=params, loss_reduction=loss_reduction, config=config, devices=devices, local_ps_devices=ps_devices)
        if mode == model_fn_lib.ModeKeys.TRAIN:
            train_op = _minimize_towers(tower_specs)
            return _train_spec(tower_specs, train_op, aggregation_device=consolidation_device)
        elif mode == model_fn_lib.ModeKeys.EVAL:
            return _eval_spec(tower_specs, aggregation_device=consolidation_device)
        elif mode == model_fn_lib.ModeKeys.PREDICT:
            return _predict_spec(tower_specs, aggregation_device=consolidation_device)
    if len(devices) == 1:
        return single_device_model_fn
    else:
        return replicated_model_fn

def split_dictionary(dictionary):
    """Split a dictionary into shards."""
    shards = [{} for _ in range(number_of_shards)]
    for name, tensor in six.iteritems(dictionary):
        if isinstance(tensor, sparse_tensor.SparseTensor):
            for i, shard in enumerate(sparse_ops.sparse_split(sp_input=tensor, num_split=number_of_shards, axis=0)):
                shards[i][name] = shard
        else:
            ensure_divisible_by_shards(tensor)
            for i, shard in enumerate(array_ops.split(tensor, number_of_shards)):
                shards[i][name] = shard
    return shards

def _split_batch(features, labels, number_of_shards, device):
    """Split input features and labes into batches."""

    def ensure_divisible_by_shards(sequence):
        batch_size = ops_lib.convert_to_tensor(sequence).get_shape()[0]
        if batch_size % number_of_shards != 0:
            raise ValueError('Batch size {} needs to be divisible by the number of GPUs, which is {}.'.format(batch_size, number_of_shards))

    def split_dictionary(dictionary):
        """Split a dictionary into shards."""
        shards = [{} for _ in range(number_of_shards)]
        for name, tensor in six.iteritems(dictionary):
            if isinstance(tensor, sparse_tensor.SparseTensor):
                for i, shard in enumerate(sparse_ops.sparse_split(sp_input=tensor, num_split=number_of_shards, axis=0)):
                    shards[i][name] = shard
            else:
                ensure_divisible_by_shards(tensor)
                for i, shard in enumerate(array_ops.split(tensor, number_of_shards)):
                    shards[i][name] = shard
        return shards
    with ops_lib.name_scope('split_inputs'):
        with ops_lib.device(device):
            if isinstance(features, dict):
                feature_shards = split_dictionary(features)
            else:
                ensure_divisible_by_shards(features)
                feature_shards = array_ops.split(features, number_of_shards)
            if labels is None:
                label_shards = None
            elif isinstance(labels, dict):
                label_shards = split_dictionary(labels)
            else:
                ensure_divisible_by_shards(labels)
                label_shards = array_ops.split(labels, number_of_shards)
    return (feature_shards, label_shards)

def local_device_chooser(op):
    current_device = framework_device.DeviceSpec.from_string(op.device or '')
    node_def = op if isinstance(op, node_def_pb2.NodeDef) else op.node_def
    if node_def.op in ps_ops:
        ps_device_spec = framework_device.DeviceSpec.from_string('{}'.format(ps_devices[ps_strategy(op)]))
        ps_device_spec.merge_from(current_device)
        return ps_device_spec.to_string()
    else:
        worker_device_spec = framework_device.DeviceSpec.from_string(worker_device or '')
        worker_device_spec.merge_from(current_device)
        return worker_device_spec.to_string()

def _compute_sum_on_device(values, device, name=None):
    with ops_lib.device(device):
        if isinstance(values[0], ops_lib.IndexedSlices):
            if name:
                raise ValueError('The name {} is not expected to be given to IndexedSlices {}'.format(name, values))
            values_concat = array_ops.concat([v.values for v in values], axis=0)
            indices_concat = array_ops.concat([v.indices for v in values], axis=0)
            return ops_lib.IndexedSlices(values_concat, indices_concat, values[0].dense_shape)
        else:
            return math_ops.add_n(values, name=name)

def _extract_tensors(tensors_and_vars):
    tensors = []
    for tensor_and_var in tensors_and_vars:
        tensor, _ = tensor_and_var
        if isinstance(tensor, ops_lib.IndexedSlices):
            tensors.append(tensor.values)
        else:
            tensors.append(tensor)
    return tensors

def get_init_fn_for_scaffold(flags):
    flags_checkpoint_path = flags.checkpoint_path
    if tf.train.latest_checkpoint(flags.model_dir):
        tf.logging.info('Ignoring --checkpoint_path because a checkpoint already exists in %s' % flags.model_dir)
        return None
    if flags_checkpoint_path is None:
        return None
    exclusions = []
    if flags.checkpoint_exclude_scopes:
        exclusions = [scope.strip() for scope in flags.checkpoint_exclude_scopes.split(',')]
    variables_to_restore = []
    for var in tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES):
        excluded = False
        for exclusion in exclusions:
            if var.op.name.startswith(exclusion):
                excluded = True
                break
        if not excluded:
            variables_to_restore.append(var)
    if flags.checkpoint_model_scope is not None:
        if flags.checkpoint_model_scope.strip() == '':
            variables_to_restore = {var.op.name.replace(flags.model_scope + '/', flags.checkpoint_model_scope): var for var in variables_to_restore}
        else:
            variables_to_restore = {var.op.name.replace(flags.model_scope, flags.checkpoint_model_scope): var for var in variables_to_restore}
    if tf.gfile.IsDirectory(flags_checkpoint_path):
        checkpoint_path = tf.train.latest_checkpoint(flags_checkpoint_path)
    else:
        checkpoint_path = flags_checkpoint_path
    tf.logging.info('Fine-tuning from %s. Ignoring missing vars: %s' % (checkpoint_path, flags.ignore_missing_vars))
    if not variables_to_restore:
        raise ValueError('variables_to_restore cannot be empty')
    if flags.ignore_missing_vars:
        reader = tf.train.NewCheckpointReader(checkpoint_path)
        if isinstance(variables_to_restore, dict):
            var_dict = variables_to_restore
        else:
            var_dict = {var.op.name: var for var in variables_to_restore}
        available_vars = {}
        for var in var_dict:
            if reader.has_tensor(var):
                available_vars[var] = var_dict[var]
            else:
                tf.logging.warning('Variable %s missing in checkpoint %s', var, checkpoint_path)
        variables_to_restore = available_vars
    if variables_to_restore:
        saver = tf.train.Saver(variables_to_restore, reshape=False)
        saver.build()

        def callback(scaffold, session):
            saver.restore(session, checkpoint_path)
        return callback
    else:
        tf.logging.warning('No Variables to restore')
        return None

def get_latest_checkpoint_for_evaluate(flags):
    flags_checkpoint_path = flags.checkpoint_path
    if tf.train.latest_checkpoint(flags.model_dir):
        tf.logging.info('Ignoring --checkpoint_path because a checkpoint already exists in %s' % flags.model_dir)
        return None
    if tf.gfile.IsDirectory(flags_checkpoint_path):
        checkpoint_path = tf.train.latest_checkpoint(flags_checkpoint_path)
    else:
        checkpoint_path = flags_checkpoint_path
    tf.logging.info('Restore from %s.' % checkpoint_path)
    return checkpoint_path

def get_init_fn_for_scaffold_(checkpoint_path, model_dir, checkpoint_exclude_scopes, model_scope, checkpoint_model_scope, ignore_missing_vars, use_v1=False):
    flags_checkpoint_path = checkpoint_path
    if tf.train.latest_checkpoint(model_dir):
        tf.logging.info('Ignoring --checkpoint_path because a checkpoint already exists in %s' % model_dir)
        return None
    if flags_checkpoint_path is None:
        return None
    exclusions = []
    if checkpoint_exclude_scopes:
        exclusions = [scope.strip() for scope in checkpoint_exclude_scopes.split(',')]
    variables_to_restore = []
    for var in tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES):
        excluded = False
        for exclusion in exclusions:
            if var.op.name.startswith(exclusion):
                excluded = True
                break
        if not excluded:
            variables_to_restore.append(var)
    if checkpoint_model_scope is not None:
        if checkpoint_model_scope.strip() == '':
            variables_to_restore = {var.op.name.replace(model_scope + '/', checkpoint_model_scope): var for var in variables_to_restore}
        else:
            variables_to_restore = {var.op.name.replace(model_scope, checkpoint_model_scope): var for var in variables_to_restore}
    if tf.gfile.IsDirectory(flags_checkpoint_path):
        checkpoint_path = tf.train.latest_checkpoint(flags_checkpoint_path)
    else:
        checkpoint_path = flags_checkpoint_path
    tf.logging.info('Fine-tuning from %s. Ignoring missing vars: %s' % (checkpoint_path, ignore_missing_vars))
    if not variables_to_restore:
        raise ValueError('variables_to_restore cannot be empty')
    if ignore_missing_vars:
        reader = tf.train.NewCheckpointReader(checkpoint_path)
        if isinstance(variables_to_restore, dict):
            var_dict = variables_to_restore
        else:
            var_dict = {var.op.name: var for var in variables_to_restore}
        available_vars = {}
        for var in var_dict:
            if reader.has_tensor(var):
                available_vars[var] = var_dict[var]
            else:
                tf.logging.warning('Variable %s missing in checkpoint %s', var, checkpoint_path)
        variables_to_restore = available_vars
    if variables_to_restore:
        saver = tf.train.Saver(variables_to_restore, reshape=False, write_version=tf.train.SaverDef.V1 if use_v1 else tf.train.SaverDef.V2)
        saver.build()

        def callback(scaffold, session):
            saver.restore(session, checkpoint_path)
        return callback
    else:
        tf.logging.warning('No Variables to restore')
        return None

def get_raw_init_fn_for_scaffold(checkpoint_path, model_dir, use_v1=False):
    flags_checkpoint_path = checkpoint_path
    if tf.train.latest_checkpoint(model_dir):
        tf.logging.info('Ignoring --checkpoint_path because a checkpoint already exists in %s' % model_dir)
        return None
    if flags_checkpoint_path is None:
        return None
    variables_to_restore = []
    for var in tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES):
        variables_to_restore.append(var)
    if tf.gfile.IsDirectory(flags_checkpoint_path):
        checkpoint_path = tf.train.latest_checkpoint(flags_checkpoint_path)
    else:
        checkpoint_path = flags_checkpoint_path
    tf.logging.info('Fine-tuning from %s. Ignoring missing vars: %s' % (checkpoint_path, True))
    if not variables_to_restore:
        raise ValueError('variables_to_restore cannot be empty')
    reader = tf.train.NewCheckpointReader(checkpoint_path)
    if isinstance(variables_to_restore, dict):
        var_dict = variables_to_restore
    else:
        var_dict = {var.op.name: var for var in variables_to_restore}
    available_vars = {}
    for var in var_dict:
        if reader.has_tensor(var):
            available_vars[var] = var_dict[var]
        else:
            tf.logging.warning('Variable %s missing in checkpoint %s', var, checkpoint_path)
    variables_to_restore = available_vars
    if variables_to_restore:
        saver = tf.train.Saver(variables_to_restore, reshape=False, write_version=tf.train.SaverDef.V1 if use_v1 else tf.train.SaverDef.V2)
        saver.build()

        def callback(scaffold, session):
            saver.restore(session, checkpoint_path)
        return callback
    else:
        tf.logging.warning('No Variables to restore')
        return None

def swa_get_init_fn_for_scaffold(checkpoint_path, model_dir, variables_to_restore, ema, use_v1=False):
    flags_checkpoint_path = checkpoint_path
    if tf.train.latest_checkpoint(model_dir):
        tf.logging.info('Ignoring --checkpoint_path because a checkpoint already exists in %s' % model_dir)
        return None
    if flags_checkpoint_path is None:
        return None
    if tf.gfile.IsDirectory(flags_checkpoint_path):
        checkpoint_path = tf.train.latest_checkpoint(flags_checkpoint_path)
    else:
        checkpoint_path = flags_checkpoint_path
    tf.logging.info('Fine-tuning from %s. Ignoring missing vars: %s' % (checkpoint_path, True))
    if not variables_to_restore:
        raise ValueError('variables_to_restore cannot be empty')
    reader = tf.train.NewCheckpointReader(checkpoint_path)
    if isinstance(variables_to_restore, dict):
        var_dict = variables_to_restore
    else:
        var_dict = {var.op.name: var for var in variables_to_restore}
    available_vars = {}
    for var in var_dict:
        if reader.has_tensor(var):
            available_vars[ema.average_name(var_dict[var])] = var_dict[var]
        else:
            tf.logging.warning('Variable %s missing in checkpoint %s', var, checkpoint_path)
    variables_to_restore = available_vars
    if variables_to_restore:
        saver = tf.train.Saver(variables_to_restore, reshape=False, write_version=tf.train.SaverDef.V1 if use_v1 else tf.train.SaverDef.V2)
        saver.build()

        def callback(scaffold, session):
            saver.restore(session, checkpoint_path)
        return callback
    else:
        tf.logging.warning('No Variables to restore')
        return None

def get_latest_checkpoint_for_evaluate_(checkpoint_path, model_dir):
    flags_checkpoint_path = checkpoint_path
    if tf.train.latest_checkpoint(model_dir):
        tf.logging.info('Ignoring --checkpoint_path because a checkpoint already exists in %s' % model_dir)
        return None
    if tf.gfile.IsDirectory(flags_checkpoint_path):
        checkpoint_path = tf.train.latest_checkpoint(flags_checkpoint_path)
    else:
        checkpoint_path = flags_checkpoint_path
    tf.logging.info('Restore from %s.' % checkpoint_path)
    return checkpoint_path

def distort_color(image, color_ordering=0, fast_mode=True, scope=None):
    """Distort the color of a Tensor image.

  Each color distortion is non-commutative and thus ordering of the color ops
  matters. Ideally we would randomly permute the ordering of the color ops.
  Rather then adding that level of complication, we select a distinct ordering
  of color ops for each preprocessing thread.

  Args:
    image: 3-D Tensor containing single image in [0, 1].
    color_ordering: Python int, a type of distortion (valid values: 0-3).
    fast_mode: Avoids slower ops (random_hue and random_contrast)
    scope: Optional scope for name_scope.
  Returns:
    3-D Tensor color-distorted image on range [0, 1]
  Raises:
    ValueError: if color_ordering not in [0, 3]
  """
    with tf.name_scope(scope, 'distort_color', [image]):
        if fast_mode:
            if color_ordering == 0:
                image = tf.image.random_brightness(image, max_delta=32.0 / 255.0)
                image = tf.image.random_saturation(image, lower=0.5, upper=1.5)
            else:
                image = tf.image.random_saturation(image, lower=0.5, upper=1.5)
                image = tf.image.random_brightness(image, max_delta=32.0 / 255.0)
        elif color_ordering == 0:
            image = tf.image.random_brightness(image, max_delta=32.0 / 255.0)
            image = tf.image.random_saturation(image, lower=0.5, upper=1.5)
            image = tf.image.random_hue(image, max_delta=0.2)
            image = tf.image.random_contrast(image, lower=0.5, upper=1.5)
        elif color_ordering == 1:
            image = tf.image.random_saturation(image, lower=0.5, upper=1.5)
            image = tf.image.random_brightness(image, max_delta=32.0 / 255.0)
            image = tf.image.random_contrast(image, lower=0.5, upper=1.5)
            image = tf.image.random_hue(image, max_delta=0.2)
        elif color_ordering == 2:
            image = tf.image.random_contrast(image, lower=0.5, upper=1.5)
            image = tf.image.random_hue(image, max_delta=0.2)
            image = tf.image.random_brightness(image, max_delta=32.0 / 255.0)
            image = tf.image.random_saturation(image, lower=0.5, upper=1.5)
        elif color_ordering == 3:
            image = tf.image.random_hue(image, max_delta=0.2)
            image = tf.image.random_saturation(image, lower=0.5, upper=1.5)
            image = tf.image.random_contrast(image, lower=0.5, upper=1.5)
            image = tf.image.random_brightness(image, max_delta=32.0 / 255.0)
        else:
            raise ValueError('color_ordering must be in [0, 3]')
        return tf.clip_by_value(image, 0.0, 1.0)

def distort_color_v0(image, color_ordering=0, fast_mode=True, scope=None):
    """Distort the color of a Tensor image.

  Each color distortion is non-commutative and thus ordering of the color ops
  matters. Ideally we would randomly permute the ordering of the color ops.
  Rather then adding that level of complication, we select a distinct ordering
  of color ops for each preprocessing thread.

  Args:
    image: 3-D Tensor containing single image in [0, 1].
    color_ordering: Python int, a type of distortion (valid values: 0-3).
    fast_mode: Avoids slower ops (random_hue and random_contrast)
    scope: Optional scope for name_scope.
  Returns:
    3-D Tensor color-distorted image on range [0, 1]
  Raises:
    ValueError: if color_ordering not in [0, 3]
  """
    with tf.name_scope(scope, 'distort_color', [image]):
        if fast_mode:
            if color_ordering == 0:
                image = tf.image.random_brightness(image, max_delta=32.0)
                image = tf.image.random_saturation(image, lower=0.5, upper=1.5)
            else:
                image = tf.image.random_saturation(image, lower=0.5, upper=1.5)
                image = tf.image.random_brightness(image, max_delta=32.0)
        elif color_ordering == 0:
            image = tf.image.random_brightness(image, max_delta=32.0)
            image = tf.image.random_saturation(image, lower=0.5, upper=1.5)
            image = tf.image.random_hue(image, max_delta=0.2)
            image = tf.image.random_contrast(image, lower=0.5, upper=1.5)
        elif color_ordering == 1:
            image = tf.image.random_saturation(image, lower=0.5, upper=1.5)
            image = tf.image.random_brightness(image, max_delta=32.0)
            image = tf.image.random_contrast(image, lower=0.5, upper=1.5)
            image = tf.image.random_hue(image, max_delta=0.2)
        elif color_ordering == 2:
            image = tf.image.random_contrast(image, lower=0.5, upper=1.5)
            image = tf.image.random_hue(image, max_delta=0.2)
            image = tf.image.random_brightness(image, max_delta=32.0)
            image = tf.image.random_saturation(image, lower=0.5, upper=1.5)
        elif color_ordering == 3:
            image = tf.image.random_hue(image, max_delta=0.2)
            image = tf.image.random_saturation(image, lower=0.5, upper=1.5)
            image = tf.image.random_contrast(image, lower=0.5, upper=1.5)
            image = tf.image.random_brightness(image, max_delta=32.0)
        else:
            raise ValueError('color_ordering must be in [0, 3]')
        return tf.clip_by_value(image, 0.0, 255.0)

def _mean_image_subtraction(image, means, num_channels):
    """Subtracts the given means from each image channel.

  For example:
    means = [123.68, 116.779, 103.939]
    image = _mean_image_subtraction(image, means)

  Note that the rank of `image` must be known.

  Args:
    image: a tensor of size [height, width, C].
    means: a C-vector of values to subtract from each channel.
    num_channels: number of color channels in the image that will be distorted.

  Returns:
    the centered image.

  Raises:
    ValueError: If the rank of `image` is unknown, if `image` has a rank other
      than three or if the number of channels in `image` doesn't match the
      number of values in `means`.
  """
    if image.get_shape().ndims != 3:
        raise ValueError('Input must be of size [height, width, C>0]')
    if len(means) != num_channels:
        raise ValueError('len(means) must match the number of channels')
    means = tf.expand_dims(tf.expand_dims(means, 0), 0)
    return image - means

