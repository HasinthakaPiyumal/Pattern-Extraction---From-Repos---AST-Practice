# Cluster 9

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

@staticmethod
def _did_towers_have_same_optimizer_calls():
    graph_state = TowerOptimizer._graph_state()
    return graph_state.did_towers_have_same_optimizer_calls()

def _get_loss_towers(model_fn, mode, features, labels, params, config, devices, local_ps_devices, loss_reduction, name_scope_pattern=_DEFAULT_NAME_SCOPE_PATTERN):
    """Replicate the loss computation across devices."""
    tower_specs = []
    model_fn_args = util.fn_args(model_fn)
    optional_params = {}
    if 'params' in model_fn_args:
        optional_params['params'] = copy.deepcopy(params)
    if 'config' in model_fn_args:
        optional_params['config'] = copy.deepcopy(config)
    round_robin_strategy = device_setter_lib._RoundRobinStrategy(num_tasks=len(local_ps_devices))
    TowerOptimizer._graph_state().set_reduction_across_towers(loss_reduction, len(devices))
    for i, device in enumerate(devices):
        is_the_first_tower = i == 0
        device_setter = _local_device_setter(worker_device=device, ps_devices=local_ps_devices, ps_strategy=round_robin_strategy)
        name_scope = name_scope_pattern
        if is_the_first_tower:
            name_scope = ''
        with variable_scope.variable_scope('', reuse=not is_the_first_tower) as var_scope:
            with ops_lib.name_scope(name_scope.format(i)) as name_scope:
                with TowerOptimizer._graph_state().tower(tower_id=i, var_scope=var_scope, name_scope=name_scope):
                    with ops_lib.device(device_setter):
                        labels_shard = None
                        if labels:
                            labels_shard = labels[i]
                        tower_spec = model_fn(mode=mode, features=features[i], labels=labels_shard, **optional_params)
                        if tower_spec.train_op is not None and len(devices) > 1 and (not TowerOptimizer.has_been_used()):
                            raise ValueError('Please wrap optimizers with TowerOptimizer in order to use replicate_model_fn with multiple `devices`.')
                        tower_spec = _scale_tower_loss(tower_spec, loss_reduction, number_of_towers=len(devices))
                        tower_specs.append(tower_spec)
    if not TowerOptimizer._did_towers_have_same_optimizer_calls():
        raise ValueError('Each invocation of model_fn was supposed to make the same optimizer calls.')
    TowerOptimizer._clear_graph_state()
    return tower_specs

def _scale_tower_loss(tower_spec, loss_reduction, number_of_towers):
    """Produce an EstimatorSpec with approproriately scaled loss."""
    if tower_spec.loss is None:
        return tower_spec
    estimator_spec = _asdict(tower_spec)
    estimator_spec['loss'] = _scale_loss(tower_spec.loss, loss_reduction, number_of_towers)
    return model_fn_lib.EstimatorSpec(**estimator_spec)

def _train_spec(tower_specs, train_op, aggregation_device, aggregated_loss_name='loss'):
    """Populate replicated EstimatorSpec for `GraphKeys.TRAIN`."""
    estimator_spec = _asdict(tower_specs[-1])
    estimator_spec['mode'] = model_fn_lib.ModeKeys.TRAIN
    estimator_spec['train_op'] = train_op
    estimator_spec['loss'] = _compute_sum_on_device([spec.loss for spec in tower_specs], aggregation_device, aggregated_loss_name)
    return model_fn_lib.EstimatorSpec(**estimator_spec)

def _eval_spec(tower_specs, aggregation_device, aggregated_loss_name='loss'):
    """Populate replicated EstimatorSpec for `GraphKeys.EVAL`."""
    estimator_spec = _asdict(tower_specs[0])
    estimator_spec['mode'] = model_fn_lib.ModeKeys.EVAL
    estimator_spec['loss'] = _compute_sum_on_device([spec.loss for spec in tower_specs], aggregation_device, aggregated_loss_name)
    update_ops = []
    for tower_spec in tower_specs:
        for name, (_, update_op) in six.iteritems(tower_spec.eval_metric_ops):
            update_ops.append(update_op)
    with ops_lib.control_dependencies(update_ops):
        reduced_update_op = _reduce_metric_variables(len(tower_specs))
    eval_metric_ops = {}
    for name, (metric_tensor, _) in six.iteritems(tower_specs[0].eval_metric_ops):
        eval_metric_ops[name] = (metric_tensor, reduced_update_op)
    estimator_spec['eval_metric_ops'] = eval_metric_ops
    return model_fn_lib.EstimatorSpec(**estimator_spec)

def _predict_spec(tower_specs, aggregation_device):
    """Populate replicated EstimatorSpec for `GraphKeys.PREDICT`."""
    estimator_spec = _asdict(tower_specs[0])
    estimator_spec['mode'] = model_fn_lib.ModeKeys.PREDICT
    with ops_lib.device(aggregation_device):
        estimator_spec['predictions'] = _concat_tensor_dicts(*[tower_spec.predictions for tower_spec in tower_specs])
        export_outputs_dict = _dict_concat(*[tower_spec.export_outputs for tower_spec in tower_specs])
        export_outputs = {}
        for name, export_output_list in six.iteritems(export_outputs_dict):
            if isinstance(export_output_list[0], export_output_lib.PredictOutput):
                export_outputs[name] = export_output_lib.PredictOutput(outputs=_concat_tensor_dicts(*[export_output.outputs for export_output in export_output_list]))
            elif isinstance(export_output_list[0], export_output_lib.RegressionOutput):
                export_outputs[name] = export_output_lib.RegressionOutput(value=array_ops.concat([export_output.value for export_output in export_output_list], axis=0))
            elif isinstance(export_output_list[0], export_output_lib.ClassificationOutput):
                scores = None
                if export_output_list[0].scores is not None:
                    scores = array_ops.concat([export_output.scores for export_output in export_output_list], axis=0)
                classes = None
                if export_output_list[0].classes is not None:
                    classes = array_ops.stack([export_output.classes for export_output in export_output_list], axis=0)
                export_outputs[name] = export_output_lib.ClassificationOutput(scores=scores, classes=classes)
    estimator_spec['export_outputs'] = export_outputs
    return model_fn_lib.EstimatorSpec(**estimator_spec)

def _concat_tensor_dicts(*tensor_dicts):
    return {name: array_ops.concat(tensors, axis=0, name=name) for name, tensors in six.iteritems(_dict_concat(*tensor_dicts))}

def _dict_concat(*dicts):
    list_dict = {}
    for d in dicts:
        if d is None:
            continue
        for k, v in six.iteritems(d):
            list_dict.setdefault(k, []).append(v)
    return list_dict

