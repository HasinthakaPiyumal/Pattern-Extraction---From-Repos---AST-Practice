# Cluster 10

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

class TowerOptimizer(optimizer_lib.Optimizer):
    """Gathers gradients from all towers and reduces them in the last one."""
    COLLECTION_FOR_GRAPH_STATES = 'replicate_model_fn_graph_states'

    def __init__(self, optimizer_or_optimizer_fn):
        """Wrap an existing optimizer for gathering gradients across towers.

    Each invocation of model_fn has to call the same optimizers in the same
    order.

    Multiple optimizers that use the same or different losses are supported.

    If TowerOptimizer is used but `replicate_model_fn` isn't, then no
    aggregation will happen.  All calls will simply be forwarded to the
    underlying optimizer. The behavior is similar if there is only one tower.

    If TowerOptimizer is used together with SyncReplicasOptimizer that wraps
    the user's optimizer, then it's the SyncReplicasOptimizer that needs to be
    wrapped with TowerOptimizer.

    Args:
      optimizer_or_optimizer_fn: an instance of optimizer to wrap.  That
        instance is going to be used for optimizer-specific logic.  This can
        also be a no-argument function that returns such an optimizer instance.
    """
        self._optimizer_or_optimizer_fn = optimizer_or_optimizer_fn

    @staticmethod
    def has_been_used():
        return TowerOptimizer._graph_state().has_tower_optimizer_been_used

    def get_slot(self, *args, **kwargs):
        return self._get_optimizer().get_slot(*args, **kwargs)

    def get_slot_names(self, *args, **kwargs):
        return self._get_optimizer().get_slot_names(*args, **kwargs)

    def get_name(self, *args, **kwargs):
        return self._get_optimizer().get_name(*args, **kwargs)

    def variables(self, *args, **kwargs):
        return self._get_optimizer().variables(*args, **kwargs)

    def compute_gradients(self, loss, *args, **kwargs):
        """Compute gradients, but first, if needed, scale the loss."""
        loss = _scale_loss(loss, self._graph_state().loss_reduction, self._graph_state().number_of_towers)
        return self._get_optimizer().compute_gradients(loss, *args, **kwargs)

    def apply_gradients(self, grads_and_vars, global_step=None, **kwargs):
        """Collect gradients updates to apply them with the last tower."""
        if self._graph_state().number_of_towers == 1:
            return self._get_optimizer().apply_gradients(grads_and_vars, global_step, **kwargs)
        self._graph_state().collect_gradients(grads_and_vars)
        if not self._graph_state().is_the_last_tower:
            with ops_lib.control_dependencies(_extract_tensors(grads_and_vars)):
                return self._construct_no_op_train_op()
        else:
            var_scope, name_scope = self._graph_state().scopes_of_the_first_tower
            with variable_scope.variable_scope(var_scope):
                with ops_lib.name_scope(name_scope):
                    return self._apply_gathered_gradients(global_step, **kwargs)

    def _apply_gathered_gradients(self, global_step, **kwargs):
        graph_state = self._graph_state()
        optimizer = self._get_optimizer()
        grad_lists = {}
        for grad, var in graph_state.get_latest_gradients_from_all_towers():
            if grad is not None:
                grad_lists.setdefault(var, []).append(grad)
        aggregated_grads = []
        with ops_lib.name_scope('gradient_aggregating'):
            for var, grads in six.iteritems(grad_lists):
                grad = _compute_sum_on_device(grads, var.device)
                aggregated_grads.append((grad, var))
        return optimizer.apply_gradients(aggregated_grads, global_step=global_step, **kwargs)

    def _get_optimizer(self):
        if callable(self._optimizer_or_optimizer_fn):
            self._optimizer_or_optimizer_fn = self._optimizer_or_optimizer_fn()
        self._graph_state().has_tower_optimizer_been_used = True
        return self._optimizer_or_optimizer_fn

    def _construct_no_op_train_op(self):
        return control_flow_ops.no_op(name='train_op_placeholder')

    @staticmethod
    def _graph_state():
        graph_states = ops_lib.get_default_graph().get_collection_ref(TowerOptimizer.COLLECTION_FOR_GRAPH_STATES)
        if not graph_states:
            graph_states.append(TowerOptimizer._PerGraphState())
        return graph_states[-1]

    @staticmethod
    def _did_towers_have_same_optimizer_calls():
        graph_state = TowerOptimizer._graph_state()
        return graph_state.did_towers_have_same_optimizer_calls()

    @staticmethod
    def _clear_graph_state():
        ops_lib.get_default_graph().clear_collection(TowerOptimizer.COLLECTION_FOR_GRAPH_STATES)

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

@staticmethod
def _graph_state():
    graph_states = ops_lib.get_default_graph().get_collection_ref(TowerOptimizer.COLLECTION_FOR_GRAPH_STATES)
    if not graph_states:
        graph_states.append(TowerOptimizer._PerGraphState())
    return graph_states[-1]

@staticmethod
def _clear_graph_state():
    ops_lib.get_default_graph().clear_collection(TowerOptimizer.COLLECTION_FOR_GRAPH_STATES)

