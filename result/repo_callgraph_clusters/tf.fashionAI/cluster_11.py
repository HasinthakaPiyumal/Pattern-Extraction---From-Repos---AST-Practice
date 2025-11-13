# Cluster 11

def input_pipeline(is_training=True, model_scope=FLAGS.model_scope, num_epochs=FLAGS.epochs_per_eval):
    if 'all' in model_scope:
        lnorm_table = tf.contrib.lookup.HashTable(tf.contrib.lookup.KeyValueTensorInitializer(tf.constant(config.global_norm_key, dtype=tf.int64), tf.constant(config.global_norm_lvalues, dtype=tf.int64)), 0)
        rnorm_table = tf.contrib.lookup.HashTable(tf.contrib.lookup.KeyValueTensorInitializer(tf.constant(config.global_norm_key, dtype=tf.int64), tf.constant(config.global_norm_rvalues, dtype=tf.int64)), 1)
    else:
        lnorm_table = tf.contrib.lookup.HashTable(tf.contrib.lookup.KeyValueTensorInitializer(tf.constant(config.local_norm_key, dtype=tf.int64), tf.constant(config.local_norm_lvalues, dtype=tf.int64)), 0)
        rnorm_table = tf.contrib.lookup.HashTable(tf.contrib.lookup.KeyValueTensorInitializer(tf.constant(config.local_norm_key, dtype=tf.int64), tf.constant(config.local_norm_rvalues, dtype=tf.int64)), 1)
    preprocessing_fn = lambda org_image, classid, shape, key_x, key_y, key_v: preprocessing.preprocess_image(org_image, classid, shape, FLAGS.train_image_size, FLAGS.train_image_size, key_x, key_y, key_v, (lnorm_table, rnorm_table), is_training=is_training, data_format='NCHW' if FLAGS.data_format == 'channels_first' else 'NHWC', category=model_scope if 'all' not in model_scope else '*', bbox_border=FLAGS.bbox_border, heatmap_sigma=FLAGS.heatmap_sigma, heatmap_size=FLAGS.heatmap_size)
    images, shape, classid, targets, key_v, isvalid, norm_value = dataset.slim_get_split(FLAGS.data_dir, preprocessing_fn, FLAGS.batch_size, FLAGS.num_readers, FLAGS.num_preprocessing_threads, num_epochs=num_epochs, is_training=is_training, file_pattern=FLAGS.dataset_name, category=model_scope if 'all' not in model_scope else '*', reader=None)
    return (images, {'targets': targets, 'key_v': key_v, 'shape': shape, 'classid': classid, 'isvalid': isvalid, 'norm_value': norm_value})

def input_pipeline(is_training=True, model_scope=FLAGS.model_scope, num_epochs=FLAGS.epochs_per_eval):
    if 'all' in model_scope:
        lnorm_table = tf.contrib.lookup.HashTable(tf.contrib.lookup.KeyValueTensorInitializer(tf.constant(config.global_norm_key, dtype=tf.int64), tf.constant(config.global_norm_lvalues, dtype=tf.int64)), 0)
        rnorm_table = tf.contrib.lookup.HashTable(tf.contrib.lookup.KeyValueTensorInitializer(tf.constant(config.global_norm_key, dtype=tf.int64), tf.constant(config.global_norm_rvalues, dtype=tf.int64)), 1)
    else:
        lnorm_table = tf.contrib.lookup.HashTable(tf.contrib.lookup.KeyValueTensorInitializer(tf.constant(config.local_norm_key, dtype=tf.int64), tf.constant(config.local_norm_lvalues, dtype=tf.int64)), 0)
        rnorm_table = tf.contrib.lookup.HashTable(tf.contrib.lookup.KeyValueTensorInitializer(tf.constant(config.local_norm_key, dtype=tf.int64), tf.constant(config.local_norm_rvalues, dtype=tf.int64)), 1)
    preprocessing_fn = lambda org_image, classid, shape, key_x, key_y, key_v: preprocessing.preprocess_image(org_image, classid, shape, FLAGS.train_image_size, FLAGS.train_image_size, key_x, key_y, key_v, (lnorm_table, rnorm_table), is_training=is_training, data_format='NCHW' if FLAGS.data_format == 'channels_first' else 'NHWC', category=model_scope if 'all' not in model_scope else '*', bbox_border=FLAGS.bbox_border, heatmap_sigma=FLAGS.heatmap_sigma, heatmap_size=FLAGS.heatmap_size)
    images, shape, classid, targets, key_v, isvalid, norm_value = dataset.slim_get_split(FLAGS.data_dir, preprocessing_fn, FLAGS.batch_size, FLAGS.num_readers, FLAGS.num_preprocessing_threads, num_epochs=num_epochs, is_training=is_training, file_pattern=FLAGS.dataset_name, category=model_scope if 'all' not in model_scope else '*', reader=None)
    return (images, {'targets': targets, 'key_v': key_v, 'shape': shape, 'classid': classid, 'isvalid': isvalid, 'norm_value': norm_value})

def input_pipeline(is_training=True, model_scope=FLAGS.model_scope, num_epochs=FLAGS.epochs_per_eval):
    if 'all' in model_scope:
        lnorm_table = tf.contrib.lookup.HashTable(tf.contrib.lookup.KeyValueTensorInitializer(tf.constant(config.global_norm_key, dtype=tf.int64), tf.constant(config.global_norm_lvalues, dtype=tf.int64)), 0)
        rnorm_table = tf.contrib.lookup.HashTable(tf.contrib.lookup.KeyValueTensorInitializer(tf.constant(config.global_norm_key, dtype=tf.int64), tf.constant(config.global_norm_rvalues, dtype=tf.int64)), 1)
    else:
        lnorm_table = tf.contrib.lookup.HashTable(tf.contrib.lookup.KeyValueTensorInitializer(tf.constant(config.local_norm_key, dtype=tf.int64), tf.constant(config.local_norm_lvalues, dtype=tf.int64)), 0)
        rnorm_table = tf.contrib.lookup.HashTable(tf.contrib.lookup.KeyValueTensorInitializer(tf.constant(config.local_norm_key, dtype=tf.int64), tf.constant(config.local_norm_rvalues, dtype=tf.int64)), 1)
    preprocessing_fn = lambda org_image, classid, shape, key_x, key_y, key_v: preprocessing.preprocess_image(org_image, classid, shape, FLAGS.train_image_size, FLAGS.train_image_size, key_x, key_y, key_v, (lnorm_table, rnorm_table), is_training=is_training, data_format='NCHW' if FLAGS.data_format == 'channels_first' else 'NHWC', category=model_scope if 'all' not in model_scope else '*', bbox_border=FLAGS.bbox_border, heatmap_sigma=FLAGS.heatmap_sigma, heatmap_size=FLAGS.heatmap_size)
    images, shape, classid, targets, key_v, isvalid, norm_value = dataset.slim_get_split(FLAGS.data_dir, preprocessing_fn, FLAGS.batch_size, FLAGS.num_readers, FLAGS.num_preprocessing_threads, num_epochs=num_epochs, is_training=is_training, file_pattern=FLAGS.dataset_name, category=model_scope if 'all' not in model_scope else '*', reader=None)
    return (images, {'targets': targets, 'key_v': key_v, 'shape': shape, 'classid': classid, 'isvalid': isvalid, 'norm_value': norm_value})

def input_pipeline(is_training=True, model_scope=FLAGS.model_scope, num_epochs=FLAGS.epochs_per_eval):
    if 'all' in model_scope:
        lnorm_table = tf.contrib.lookup.HashTable(tf.contrib.lookup.KeyValueTensorInitializer(tf.constant(config.global_norm_key, dtype=tf.int64), tf.constant(config.global_norm_lvalues, dtype=tf.int64)), 0)
        rnorm_table = tf.contrib.lookup.HashTable(tf.contrib.lookup.KeyValueTensorInitializer(tf.constant(config.global_norm_key, dtype=tf.int64), tf.constant(config.global_norm_rvalues, dtype=tf.int64)), 1)
    else:
        lnorm_table = tf.contrib.lookup.HashTable(tf.contrib.lookup.KeyValueTensorInitializer(tf.constant(config.local_norm_key, dtype=tf.int64), tf.constant(config.local_norm_lvalues, dtype=tf.int64)), 0)
        rnorm_table = tf.contrib.lookup.HashTable(tf.contrib.lookup.KeyValueTensorInitializer(tf.constant(config.local_norm_key, dtype=tf.int64), tf.constant(config.local_norm_rvalues, dtype=tf.int64)), 1)
    preprocessing_fn = lambda org_image, classid, shape, key_x, key_y, key_v: preprocessing.preprocess_image(org_image, classid, shape, FLAGS.train_image_size, FLAGS.train_image_size, key_x, key_y, key_v, (lnorm_table, rnorm_table), is_training=is_training, data_format='NCHW' if FLAGS.data_format == 'channels_first' else 'NHWC', category=model_scope if 'all' not in model_scope else '*', bbox_border=FLAGS.bbox_border, heatmap_sigma=FLAGS.heatmap_sigma, heatmap_size=FLAGS.heatmap_size)
    images, shape, classid, targets, key_v, isvalid, norm_value = dataset.slim_get_split(FLAGS.data_dir, preprocessing_fn, FLAGS.batch_size, FLAGS.num_readers, FLAGS.num_preprocessing_threads, num_epochs=num_epochs, is_training=is_training, file_pattern=FLAGS.dataset_name, category=model_scope if 'all' not in model_scope else '*', reader=None)
    return (images, {'targets': targets, 'key_v': key_v, 'shape': shape, 'classid': classid, 'isvalid': isvalid, 'norm_value': norm_value})

def input_pipeline(is_training=True, num_epochs=FLAGS.epochs_per_eval):
    if 'all' in FLAGS.model_scope:
        lnorm_table = tf.contrib.lookup.HashTable(tf.contrib.lookup.KeyValueTensorInitializer(tf.constant(config.global_norm_key, dtype=tf.int64), tf.constant(config.global_norm_lvalues, dtype=tf.int64)), 0)
        rnorm_table = tf.contrib.lookup.HashTable(tf.contrib.lookup.KeyValueTensorInitializer(tf.constant(config.global_norm_key, dtype=tf.int64), tf.constant(config.global_norm_rvalues, dtype=tf.int64)), 1)
    else:
        lnorm_table = tf.contrib.lookup.HashTable(tf.contrib.lookup.KeyValueTensorInitializer(tf.constant(config.local_norm_key, dtype=tf.int64), tf.constant(config.local_norm_lvalues, dtype=tf.int64)), 0)
        rnorm_table = tf.contrib.lookup.HashTable(tf.contrib.lookup.KeyValueTensorInitializer(tf.constant(config.local_norm_key, dtype=tf.int64), tf.constant(config.local_norm_rvalues, dtype=tf.int64)), 1)
    preprocessing_fn = lambda org_image, classid, shape, key_x, key_y, key_v: preprocessing.preprocess_image(org_image, classid, shape, FLAGS.train_image_size, FLAGS.train_image_size, key_x, key_y, key_v, (lnorm_table, rnorm_table), is_training=is_training, data_format='NCHW' if FLAGS.data_format == 'channels_first' else 'NHWC', category=FLAGS.model_scope if 'all' not in FLAGS.model_scope else '*', bbox_border=FLAGS.bbox_border, heatmap_sigma=FLAGS.heatmap_sigma, heatmap_size=FLAGS.heatmap_size)
    images, shape, classid, targets, key_v, isvalid, norm_value = dataset.slim_get_split(FLAGS.data_dir, preprocessing_fn, FLAGS.batch_size, FLAGS.num_readers, FLAGS.num_preprocessing_threads, num_epochs=num_epochs, is_training=is_training, file_pattern=FLAGS.dataset_name, category=FLAGS.model_scope if 'all' not in FLAGS.model_scope else '*', reader=None)
    return (images, {'targets': targets, 'key_v': key_v, 'shape': shape, 'classid': classid, 'isvalid': isvalid, 'norm_value': norm_value})

def input_pipeline(is_training=True, model_scope=FLAGS.model_scope, num_epochs=FLAGS.epochs_per_eval):
    if 'all' in model_scope:
        lnorm_table = tf.contrib.lookup.HashTable(tf.contrib.lookup.KeyValueTensorInitializer(tf.constant(config.global_norm_key, dtype=tf.int64), tf.constant(config.global_norm_lvalues, dtype=tf.int64)), 0)
        rnorm_table = tf.contrib.lookup.HashTable(tf.contrib.lookup.KeyValueTensorInitializer(tf.constant(config.global_norm_key, dtype=tf.int64), tf.constant(config.global_norm_rvalues, dtype=tf.int64)), 1)
    else:
        lnorm_table = tf.contrib.lookup.HashTable(tf.contrib.lookup.KeyValueTensorInitializer(tf.constant(config.local_norm_key, dtype=tf.int64), tf.constant(config.local_norm_lvalues, dtype=tf.int64)), 0)
        rnorm_table = tf.contrib.lookup.HashTable(tf.contrib.lookup.KeyValueTensorInitializer(tf.constant(config.local_norm_key, dtype=tf.int64), tf.constant(config.local_norm_rvalues, dtype=tf.int64)), 1)
    preprocessing_fn = lambda org_image, classid, shape, key_x, key_y, key_v: preprocessing.preprocess_image(org_image, classid, shape, FLAGS.train_image_size, FLAGS.train_image_size, key_x, key_y, key_v, (lnorm_table, rnorm_table), is_training=is_training, data_format='NCHW' if FLAGS.data_format == 'channels_first' else 'NHWC', category=model_scope if 'all' not in model_scope else '*', bbox_border=FLAGS.bbox_border, heatmap_sigma=FLAGS.heatmap_sigma, heatmap_size=FLAGS.heatmap_size)
    images, shape, classid, targets, key_v, isvalid, norm_value = dataset.slim_get_split(FLAGS.data_dir, preprocessing_fn, FLAGS.xt_batch_size if 'seresnext50' in FLAGS.backbone else FLAGS.batch_size, FLAGS.num_readers, FLAGS.num_preprocessing_threads, num_epochs=num_epochs, is_training=is_training, file_pattern=FLAGS.dataset_name, category=model_scope if 'all' not in model_scope else '*', reader=None)
    return (images, {'targets': targets, 'key_v': key_v, 'shape': shape, 'classid': classid, 'isvalid': isvalid, 'norm_value': norm_value})

def input_pipeline(is_training=True, model_scope=FLAGS.model_scope, num_epochs=FLAGS.train_epochs):
    if 'all' in model_scope:
        lnorm_table = tf.contrib.lookup.HashTable(tf.contrib.lookup.KeyValueTensorInitializer(tf.constant(config.global_norm_key, dtype=tf.int64), tf.constant(config.global_norm_lvalues, dtype=tf.int64)), 0)
        rnorm_table = tf.contrib.lookup.HashTable(tf.contrib.lookup.KeyValueTensorInitializer(tf.constant(config.global_norm_key, dtype=tf.int64), tf.constant(config.global_norm_rvalues, dtype=tf.int64)), 1)
    else:
        lnorm_table = tf.contrib.lookup.HashTable(tf.contrib.lookup.KeyValueTensorInitializer(tf.constant(config.local_norm_key, dtype=tf.int64), tf.constant(config.local_norm_lvalues, dtype=tf.int64)), 0)
        rnorm_table = tf.contrib.lookup.HashTable(tf.contrib.lookup.KeyValueTensorInitializer(tf.constant(config.local_norm_key, dtype=tf.int64), tf.constant(config.local_norm_rvalues, dtype=tf.int64)), 1)
    preprocessing_fn = lambda org_image, classid, shape, key_x, key_y, key_v: preprocessing.preprocess_image(org_image, classid, shape, FLAGS.train_image_size, FLAGS.train_image_size, key_x, key_y, key_v, (lnorm_table, rnorm_table), is_training=is_training, data_format='NCHW' if FLAGS.data_format == 'channels_first' else 'NHWC', category=model_scope if 'all' not in model_scope else '*', bbox_border=FLAGS.bbox_border, heatmap_sigma=FLAGS.heatmap_sigma, heatmap_size=FLAGS.heatmap_size)
    images, shape, classid, targets, key_v, isvalid, norm_value = dataset.slim_get_split(FLAGS.data_dir, preprocessing_fn, FLAGS.batch_size, FLAGS.num_readers, FLAGS.num_preprocessing_threads, num_epochs=num_epochs, is_training=is_training, file_pattern=FLAGS.dataset_name, category=model_scope if 'all' not in model_scope else '*', reader=None)
    return (images, {'targets': targets, 'key_v': key_v, 'shape': shape, 'classid': classid, 'isvalid': isvalid, 'norm_value': norm_value})

def input_pipeline(is_training=True, model_scope=FLAGS.model_scope, num_epochs=None):
    if 'all' in model_scope:
        lnorm_table = tf.contrib.lookup.HashTable(tf.contrib.lookup.KeyValueTensorInitializer(tf.constant(config.global_norm_key, dtype=tf.int64), tf.constant(config.global_norm_lvalues, dtype=tf.int64)), 0)
        rnorm_table = tf.contrib.lookup.HashTable(tf.contrib.lookup.KeyValueTensorInitializer(tf.constant(config.global_norm_key, dtype=tf.int64), tf.constant(config.global_norm_rvalues, dtype=tf.int64)), 1)
    else:
        lnorm_table = tf.contrib.lookup.HashTable(tf.contrib.lookup.KeyValueTensorInitializer(tf.constant(config.local_norm_key, dtype=tf.int64), tf.constant(config.local_norm_lvalues, dtype=tf.int64)), 0)
        rnorm_table = tf.contrib.lookup.HashTable(tf.contrib.lookup.KeyValueTensorInitializer(tf.constant(config.local_norm_key, dtype=tf.int64), tf.constant(config.local_norm_rvalues, dtype=tf.int64)), 1)
    preprocessing_fn = lambda org_image, classid, shape, key_x, key_y, key_v: preprocessing.preprocess_image(org_image, classid, shape, FLAGS.train_image_size, FLAGS.train_image_size, key_x, key_y, key_v, (lnorm_table, rnorm_table), is_training=is_training, data_format='NCHW' if FLAGS.data_format == 'channels_first' else 'NHWC', category=model_scope if 'all' not in model_scope else '*', bbox_border=FLAGS.bbox_border, heatmap_sigma=FLAGS.heatmap_sigma, heatmap_size=FLAGS.heatmap_size)
    images, shape, classid, targets, key_v, isvalid, norm_value = dataset.slim_get_split(FLAGS.data_dir, preprocessing_fn, FLAGS.batch_size, FLAGS.num_readers, FLAGS.num_preprocessing_threads, num_epochs=num_epochs, is_training=is_training, file_pattern=FLAGS.dataset_name, category=model_scope if 'all' not in model_scope else '*', reader=None)
    return (images, {'targets': targets, 'key_v': key_v, 'shape': shape, 'classid': classid, 'isvalid': isvalid, 'norm_value': norm_value})

def input_pipeline(is_training=True, model_scope=FLAGS.model_scope, num_epochs=None):
    if 'all' in model_scope:
        lnorm_table = tf.contrib.lookup.HashTable(tf.contrib.lookup.KeyValueTensorInitializer(tf.constant(config.global_norm_key, dtype=tf.int64), tf.constant(config.global_norm_lvalues, dtype=tf.int64)), 0)
        rnorm_table = tf.contrib.lookup.HashTable(tf.contrib.lookup.KeyValueTensorInitializer(tf.constant(config.global_norm_key, dtype=tf.int64), tf.constant(config.global_norm_rvalues, dtype=tf.int64)), 1)
    else:
        lnorm_table = tf.contrib.lookup.HashTable(tf.contrib.lookup.KeyValueTensorInitializer(tf.constant(config.local_norm_key, dtype=tf.int64), tf.constant(config.local_norm_lvalues, dtype=tf.int64)), 0)
        rnorm_table = tf.contrib.lookup.HashTable(tf.contrib.lookup.KeyValueTensorInitializer(tf.constant(config.local_norm_key, dtype=tf.int64), tf.constant(config.local_norm_rvalues, dtype=tf.int64)), 1)
    preprocessing_fn = lambda org_image, classid, shape, key_x, key_y, key_v: preprocessing.preprocess_image(org_image, classid, shape, FLAGS.train_image_size, FLAGS.train_image_size, key_x, key_y, key_v, (lnorm_table, rnorm_table), is_training=is_training, data_format='NCHW' if FLAGS.data_format == 'channels_first' else 'NHWC', category=model_scope if 'all' not in model_scope else '*', bbox_border=FLAGS.bbox_border, heatmap_sigma=FLAGS.heatmap_sigma, heatmap_size=FLAGS.heatmap_size)
    images, shape, classid, targets, key_v, isvalid, norm_value = dataset.slim_get_split(FLAGS.data_dir, preprocessing_fn, FLAGS.batch_size, FLAGS.num_readers, FLAGS.num_preprocessing_threads, num_epochs=num_epochs, is_training=is_training, file_pattern=FLAGS.dataset_name, category=model_scope if 'all' not in model_scope else '*', reader=None)
    return (images, {'targets': targets, 'key_v': key_v, 'shape': shape, 'classid': classid, 'isvalid': isvalid, 'norm_value': norm_value})

