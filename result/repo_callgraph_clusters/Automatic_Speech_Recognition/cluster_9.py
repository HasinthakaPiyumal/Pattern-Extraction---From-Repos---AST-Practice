# Cluster 9

def mean_var_with_update():
    ema_apply_op = ema.apply([batch_mean, batch_var])
    with tf.control_dependencies([ema_apply_op]):
        return (tf.identity(batch_mean), tf.identity(batch_var))

