# Cluster 1

def model_fn(features, labels, mode, params):
    indicator_columns, embedding_columns = build_columns()
    fnn = FNN(indicator_columns, embedding_columns, params['warm_up_from_fm'], [64, 32])
    outputs = fnn(features)
    predictions = {'predictions': outputs}
    if mode == tf.estimator.ModeKeys.PREDICT:
        return tf.estimator.EstimatorSpec(mode, predictions=predictions)
    loss = tf.losses.log_loss(labels, outputs)
    metrics = {'auc': tf.metrics.auc(labels, outputs)}
    if mode == tf.estimator.ModeKeys.EVAL:
        return tf.estimator.EstimatorSpec(mode, loss=loss, eval_metric_ops=metrics)
    optimizer = tf.train.AdamOptimizer(learning_rate=0.01)
    train_op = optimizer.minimize(loss=loss, global_step=tf.train.get_global_step())
    return tf.estimator.EstimatorSpec(mode, loss=loss, train_op=train_op)

def model_fn(features, labels, mode):
    indicator_columns, embedding_columns = build_columns()
    outputs = FM(indicator_columns, embedding_columns)(features)
    predictions = {'predictions': outputs}
    if mode == tf.estimator.ModeKeys.PREDICT:
        return tf.estimator.EstimatorSpec(mode, predictions=predictions)
    loss = tf.losses.sigmoid_cross_entropy(labels, outputs)
    metrics = {'auc': tf.metrics.auc(labels, tf.nn.sigmoid(outputs))}
    if mode == tf.estimator.ModeKeys.EVAL:
        return tf.estimator.EstimatorSpec(mode, loss=loss, eval_metric_ops=metrics)
    optimizer = tf.train.AdamOptimizer(learning_rate=0.01)
    train_op = optimizer.minimize(loss=loss, global_step=tf.train.get_global_step())
    return tf.estimator.EstimatorSpec(mode, loss=loss, train_op=train_op)

def model_fn(features, labels, mode):
    indicator_columns, embedding_columns = build_columns()
    outputs = DeepFM(indicator_columns, embedding_columns, [64, 32])(features)
    predictions = {'predictions': outputs}
    if mode == tf.estimator.ModeKeys.PREDICT:
        return tf.estimator.EstimatorSpec(mode, predictions=predictions)
    loss = tf.losses.log_loss(labels, outputs)
    metrics = {'auc': tf.metrics.auc(labels, outputs)}
    if mode == tf.estimator.ModeKeys.EVAL:
        return tf.estimator.EstimatorSpec(mode, loss=loss, eval_metric_ops=metrics)
    optimizer = tf.train.AdamOptimizer(learning_rate=0.01)
    train_op = optimizer.minimize(loss=loss, global_step=tf.train.get_global_step())
    return tf.estimator.EstimatorSpec(mode, loss=loss, train_op=train_op)

def model_fn(features, labels, mode):
    indicator_columns, embedding_columns = build_columns()
    crossed_product_columns = cross_product_transformation()
    outputs = WDL(indicator_columns + crossed_product_columns, embedding_columns, [64, 16])(features)
    predictions = {'predictions': outputs}
    if mode == tf.estimator.ModeKeys.PREDICT:
        return tf.estimator.EstimatorSpec(mode, predictions=predictions)
    loss = tf.losses.log_loss(labels, outputs)
    metrics = {'auc': tf.metrics.auc(labels, outputs)}
    if mode == tf.estimator.ModeKeys.EVAL:
        return tf.estimator.EstimatorSpec(mode, loss=loss, eval_metric_ops=metrics)
    wide_variables = tf.get_collection(tf.GraphKeys.MODEL_VARIABLES, 'wide')
    wide_optimizer = tf.train.FtrlOptimizer(0.01, l1_regularization_strength=0.5)
    wide_train_op = wide_optimizer.minimize(loss=loss, global_step=tf.train.get_global_step(), var_list=wide_variables)
    deep_variables = tf.get_collection(tf.GraphKeys.MODEL_VARIABLES, 'deep')
    deep_optimizer = tf.train.AdamOptimizer(0.01)
    deep_train_op = deep_optimizer.minimize(loss=loss, global_step=tf.train.get_global_step(), var_list=deep_variables)
    update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
    train_op = tf.group(update_ops, wide_train_op, deep_train_op)
    return tf.estimator.EstimatorSpec(mode, loss=loss, train_op=train_op)

def model_fn(features, labels, mode):
    columns = build_columns()
    outputs = MMoE(columns, num_tasks=2, num_experts=2, task_hidden_units=[32, 10], expert_hidden_units=[64, 32])(features)
    predictions = {'predictions0': outputs[0], 'predictions1': outputs[1]}
    if mode == tf.estimator.ModeKeys.PREDICT:
        return tf.estimator.EstimatorSpec(mode, predictions=predictions)
    labels0 = tf.expand_dims(labels['labels0'], axis=1)
    labels1 = tf.expand_dims(labels['labels1'], axis=1)
    loss0 = tf.losses.mean_squared_error(labels=labels0, predictions=outputs[0])
    loss1 = tf.losses.mean_squared_error(labels=labels1, predictions=outputs[1])
    total_loss = loss0 + loss1
    tf.summary.scalar('task0_loss', loss0)
    tf.summary.scalar('task1_loss', loss1)
    tf.summary.scalar('total_loss', total_loss)
    metrics = {'task0_mse': tf.metrics.mean_squared_error(labels0, outputs[0]), 'task1_mse': tf.metrics.mean_squared_error(labels1, outputs[1])}
    if mode == tf.estimator.ModeKeys.EVAL:
        return tf.estimator.EstimatorSpec(mode, loss=total_loss, eval_metric_ops=metrics)
    optimizer = tf.train.AdamOptimizer(learning_rate=0.01)
    train_op = tf.group(optimizer.minimize(loss=loss0, global_step=tf.train.get_global_step()), optimizer.minimize(loss=loss1, global_step=tf.train.get_global_step()))
    return tf.estimator.EstimatorSpec(mode, loss=total_loss, train_op=train_op)

class FactorizedTopK(tf.keras.layers.Layer):
    """ Metric for a retrieval model. """

    def __init__(self, candidates: Union[TopK, tf.data.Dataset], metrics: Optional[Sequence[tf.keras.metrics.Metric]]=None, k: int=100, name: Text='factorized_top_k', **kwargs):
        super(FactorizedTopK, self).__init__(name=name, **kwargs)
        if metrics is None:
            metrics = [tf.keras.metrics.TopKCategoricalAccuracy(k=n, name=f'{self.name}/top_{n}_categorical_accuracy') for n in [1, 5, 10, 50, 100]]
        if isinstance(candidates, tf.data.Dataset):
            candidates = Streaming(k=k).index(candidates)
        self._candidates = candidates
        self._metrics = metrics
        self._k = k

    def update_state(self, query_embeddings: tf.Tensor, true_candidate_embeddings: tf.Tensor) -> tf.Operation:
        """Update metric"""
        positive_scores = tf.reduce_sum(query_embeddings * true_candidate_embeddings, axis=1, keepdims=True)
        top_k_predictions, _ = self._candidates(query_embeddings, k=self._k)
        y_true = tf.concat([tf.ones(tf.shape(positive_scores)), tf.zeros_like(top_k_predictions)], axis=1)
        y_pred = tf.concat([positive_scores, top_k_predictions], axis=1)
        update_ops = []
        for metric in self._metrics:
            update_ops.append(metric.update_state(y_true=y_true, y_pred=y_pred))
        return tf.group(update_ops)

    def reset_states(self) -> None:
        """Resets the metrics."""
        for metric in self.metrics:
            metric.reset_states()

    def result(self) -> List[tf.Tensor]:
        """Returns a list of metric results."""
        return [metric.result() for metric in self.metrics]

def update_state(self, query_embeddings: tf.Tensor, true_candidate_embeddings: tf.Tensor) -> tf.Operation:
    """Update metric"""
    positive_scores = tf.reduce_sum(query_embeddings * true_candidate_embeddings, axis=1, keepdims=True)
    top_k_predictions, _ = self._candidates(query_embeddings, k=self._k)
    y_true = tf.concat([tf.ones(tf.shape(positive_scores)), tf.zeros_like(top_k_predictions)], axis=1)
    y_pred = tf.concat([positive_scores, top_k_predictions], axis=1)
    update_ops = []
    for metric in self._metrics:
        update_ops.append(metric.update_state(y_true=y_true, y_pred=y_pred))
    return tf.group(update_ops)

