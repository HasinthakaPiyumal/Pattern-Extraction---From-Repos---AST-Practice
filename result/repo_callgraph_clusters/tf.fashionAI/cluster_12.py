# Cluster 12

def sub_loop(model_fn, model_scope, model_dir, run_config, train_epochs, epochs_per_eval, lr_decay_factors, decay_boundaries, checkpoint_path=None, checkpoint_exclude_scopes='', checkpoint_model_scope='', ignore_missing_vars=True):
    steps_per_epoch = config.split_size[model_scope if 'all' not in model_scope else '*']['train'] // FLAGS.batch_size
    fashionAI = tf.estimator.Estimator(model_fn=model_fn, model_dir=model_dir, config=run_config, params={'checkpoint_path': checkpoint_path, 'model_dir': model_dir, 'checkpoint_exclude_scopes': checkpoint_exclude_scopes, 'model_scope': model_scope, 'checkpoint_model_scope': checkpoint_model_scope, 'ignore_missing_vars': ignore_missing_vars, 'train_image_size': FLAGS.train_image_size, 'heatmap_size': FLAGS.heatmap_size, 'data_format': FLAGS.data_format, 'steps_per_epoch': steps_per_epoch, 'use_ohkm': FLAGS.use_ohkm, 'batch_size': FLAGS.batch_size, 'weight_decay': FLAGS.weight_decay, 'mse_weight': FLAGS.mse_weight, 'momentum': FLAGS.momentum, 'learning_rate': FLAGS.learning_rate, 'end_learning_rate': FLAGS.end_learning_rate, 'warmup_learning_rate': FLAGS.warmup_learning_rate, 'warmup_steps': FLAGS.warmup_steps, 'decay_boundaries': parse_comma_list(decay_boundaries), 'lr_decay_factors': parse_comma_list(lr_decay_factors)})
    tf.gfile.MakeDirs(model_dir)
    tf.logging.info('Starting to train model {}.'.format(model_scope))
    for _ in range(train_epochs // epochs_per_eval):
        tensors_to_log = {'lr': 'learning_rate', 'loss': 'total_loss', 'mse': 'mse_loss', 'ne': 'ne_mertric'}
        logging_hook = tf.train.LoggingTensorHook(tensors=tensors_to_log, every_n_iter=FLAGS.log_every_n_steps, formatter=lambda dicts: '{}:'.format(model_scope) + ', '.join(['%s=%.6f' % (k, v) for k, v in dicts.items()]))
        tf.logging.info('Starting a training cycle.')
        fashionAI.train(input_fn=lambda: input_pipeline(True, model_scope, epochs_per_eval), hooks=[logging_hook], max_steps=steps_per_epoch * train_epochs)
        tf.logging.info('Starting to evaluate.')
        eval_results = fashionAI.evaluate(input_fn=lambda: input_pipeline(False, model_scope, 1))
        tf.logging.info(eval_results)
    tf.logging.info('Finished model {}.'.format(model_scope))

def sub_loop(model_fn, model_scope, model_dir, run_config, train_epochs, epochs_per_eval, lr_decay_factors, decay_boundaries, checkpoint_path=None, checkpoint_exclude_scopes='', checkpoint_model_scope='', ignore_missing_vars=True):
    steps_per_epoch = config.split_size[model_scope if 'all' not in model_scope else '*']['train'] // FLAGS.batch_size
    fashionAI = tf.estimator.Estimator(model_fn=model_fn, model_dir=model_dir, config=run_config, params={'checkpoint_path': checkpoint_path, 'model_dir': model_dir, 'checkpoint_exclude_scopes': checkpoint_exclude_scopes, 'model_scope': model_scope, 'checkpoint_model_scope': checkpoint_model_scope, 'ignore_missing_vars': ignore_missing_vars, 'train_image_size': FLAGS.train_image_size, 'heatmap_size': FLAGS.heatmap_size, 'data_format': FLAGS.data_format, 'steps_per_epoch': steps_per_epoch, 'use_ohkm': FLAGS.use_ohkm, 'batch_size': FLAGS.batch_size, 'weight_decay': FLAGS.weight_decay, 'mse_weight': FLAGS.mse_weight, 'momentum': FLAGS.momentum, 'learning_rate': FLAGS.learning_rate, 'end_learning_rate': FLAGS.end_learning_rate, 'warmup_learning_rate': FLAGS.warmup_learning_rate, 'warmup_steps': FLAGS.warmup_steps, 'decay_boundaries': parse_comma_list(decay_boundaries), 'lr_decay_factors': parse_comma_list(lr_decay_factors)})
    tf.gfile.MakeDirs(model_dir)
    tf.logging.info('Starting to train model {}.'.format(model_scope))
    for _ in range(train_epochs // epochs_per_eval):
        tensors_to_log = {'lr': 'learning_rate', 'loss': 'total_loss', 'mse': 'mse_loss', 'ne': 'ne_mertric'}
        logging_hook = tf.train.LoggingTensorHook(tensors=tensors_to_log, every_n_iter=FLAGS.log_every_n_steps, formatter=lambda dicts: '{}:'.format(model_scope) + ', '.join(['%s=%.6f' % (k, v) for k, v in dicts.items()]))
        tf.logging.info('Starting a training cycle.')
        fashionAI.train(input_fn=lambda: input_pipeline(True, model_scope, epochs_per_eval), hooks=[logging_hook], max_steps=steps_per_epoch * train_epochs)
        tf.logging.info('Starting to evaluate.')
        eval_results = fashionAI.evaluate(input_fn=lambda: input_pipeline(False, model_scope, 1))
        tf.logging.info(eval_results)
    tf.logging.info('Finished model {}.'.format(model_scope))

def eval_each(model_fn, model_dir, model_scope, run_config):
    fashionAI = tf.estimator.Estimator(model_fn=model_fn, model_dir=model_dir, config=run_config, params={'train_image_size': FLAGS.train_image_size, 'heatmap_size': FLAGS.heatmap_size, 'data_format': FLAGS.data_format, 'model_scope': model_scope, 'flip_on_test': FLAGS.flip_on_test})
    tensors_to_log = {'cur_file': 'current_file'}
    logging_hook = tf.train.LoggingTensorHook(tensors=tensors_to_log, every_n_iter=FLAGS.log_every_n_steps, formatter=lambda dicts: ', '.join(['%s=%s' % (k, v) for k, v in dicts.items()]))
    tf.logging.info('Starting to predict model {}.'.format(model_scope))
    pred_results = fashionAI.predict(input_fn=lambda: input_pipeline(model_scope), hooks=[logging_hook], checkpoint_path=train_helper.get_latest_checkpoint_for_evaluate_(model_dir, model_dir))
    return list(pred_results)

def main(_):
    import subprocess
    import copy
    all_category = parse_str_comma_list(FLAGS.model_to_train)
    for cat in all_category:
        tf.gfile.MakeDirs(os.path.join(FLAGS.model_dir, cat))
    for cat in all_category:
        temp_params = copy.deepcopy(total_params)
        for k, v in total_params.items():
            if k[2:] in detail_params[cat]:
                temp_params[k] = detail_params[cat][k[2:]]
        params_str = []
        for k, v in temp_params.items():
            if v is not None:
                params_str.append(k)
                params_str.append(str(v))
        print('params send: ', params_str)
        train_process = subprocess.Popen(['python', './train_subnet.py'] + params_str, stdout=subprocess.PIPE, cwd=os.getcwd())
        output, _ = train_process.communicate()
        print(output)

def sub_loop(model_fn, model_scope, model_dir, run_config, train_epochs, epochs_per_eval, lr_decay_factors, decay_boundaries, checkpoint_path=None, checkpoint_exclude_scopes='', checkpoint_model_scope='', ignore_missing_vars=True):
    steps_per_epoch = config.split_size[model_scope if 'all' not in model_scope else '*']['train'] // FLAGS.batch_size
    fashionAI = tf.estimator.Estimator(model_fn=model_fn, model_dir=model_dir, config=run_config, params={'checkpoint_path': checkpoint_path, 'model_dir': model_dir, 'checkpoint_exclude_scopes': checkpoint_exclude_scopes, 'model_scope': model_scope, 'checkpoint_model_scope': checkpoint_model_scope, 'ignore_missing_vars': ignore_missing_vars, 'train_image_size': FLAGS.train_image_size, 'heatmap_size': FLAGS.heatmap_size, 'feats_channals': FLAGS.feats_channals, 'num_stacks': FLAGS.num_stacks, 'num_modules': FLAGS.num_modules, 'data_format': FLAGS.data_format, 'steps_per_epoch': steps_per_epoch, 'batch_size': FLAGS.batch_size, 'use_ohkm': FLAGS.use_ohkm, 'weight_decay': FLAGS.weight_decay, 'mse_weight': FLAGS.mse_weight, 'momentum': FLAGS.momentum, 'learning_rate': FLAGS.learning_rate, 'end_learning_rate': FLAGS.end_learning_rate, 'warmup_learning_rate': FLAGS.warmup_learning_rate, 'warmup_steps': FLAGS.warmup_steps, 'decay_boundaries': parse_comma_list(decay_boundaries), 'lr_decay_factors': parse_comma_list(lr_decay_factors)})
    tf.gfile.MakeDirs(model_dir)
    tf.logging.info('Starting to train model {}.'.format(model_scope))
    for _ in range(train_epochs // epochs_per_eval):
        tensors_to_log = {'lr': 'learning_rate', 'loss': 'total_loss', 'mse': 'mse_loss', 'ne': 'ne_mertric'}
        logging_hook = tf.train.LoggingTensorHook(tensors=tensors_to_log, every_n_iter=FLAGS.log_every_n_steps, formatter=lambda dicts: '{}:'.format(model_scope) + ', '.join(['%s=%.6f' % (k, v) for k, v in dicts.items()]))
        tf.logging.info('Starting a training cycle.')
        fashionAI.train(input_fn=lambda: input_pipeline(True, model_scope, epochs_per_eval), hooks=[logging_hook], max_steps=steps_per_epoch * train_epochs)
        tf.logging.info('Starting to evaluate.')
        eval_results = fashionAI.evaluate(input_fn=lambda: input_pipeline(False, model_scope, 1))
        tf.logging.info(eval_results)
    tf.logging.info('Finished model {}.'.format(model_scope))

def sub_loop(model_fn, model_scope, model_dir, run_config, train_epochs, epochs_per_eval, lr_decay_factors, decay_boundaries, checkpoint_path=None, checkpoint_exclude_scopes='', checkpoint_model_scope='', ignore_missing_vars=True):
    steps_per_epoch = config.split_size[model_scope if 'all' not in model_scope else '*']['train'] // FLAGS.batch_size
    fashionAI = tf.estimator.Estimator(model_fn=model_fn, model_dir=model_dir, config=run_config, params={'checkpoint_path': checkpoint_path, 'model_dir': model_dir, 'checkpoint_exclude_scopes': checkpoint_exclude_scopes, 'model_scope': model_scope, 'checkpoint_model_scope': checkpoint_model_scope, 'ignore_missing_vars': ignore_missing_vars, 'train_image_size': FLAGS.train_image_size, 'heatmap_size': FLAGS.heatmap_size, 'data_format': FLAGS.data_format, 'steps_per_epoch': steps_per_epoch, 'use_ohkm': FLAGS.use_ohkm, 'batch_size': FLAGS.batch_size, 'weight_decay': FLAGS.weight_decay, 'mse_weight': FLAGS.mse_weight, 'momentum': FLAGS.momentum, 'learning_rate': FLAGS.learning_rate, 'end_learning_rate': FLAGS.end_learning_rate, 'warmup_learning_rate': FLAGS.warmup_learning_rate, 'warmup_steps': FLAGS.warmup_steps, 'decay_boundaries': parse_comma_list(decay_boundaries), 'lr_decay_factors': parse_comma_list(lr_decay_factors)})
    tf.gfile.MakeDirs(model_dir)
    tf.logging.info('Starting to train model {}.'.format(model_scope))
    for _ in range(train_epochs // epochs_per_eval):
        tensors_to_log = {'lr': 'learning_rate', 'loss': 'total_loss', 'mse': 'mse_loss', 'ne': 'ne_mertric'}
        logging_hook = tf.train.LoggingTensorHook(tensors=tensors_to_log, every_n_iter=FLAGS.log_every_n_steps, formatter=lambda dicts: '{}:'.format(model_scope) + ', '.join(['%s=%.6f' % (k, v) for k, v in dicts.items()]))
        tf.logging.info('Starting a training cycle.')
        fashionAI.train(input_fn=lambda: input_pipeline(True, model_scope, epochs_per_eval), hooks=[logging_hook], max_steps=steps_per_epoch * train_epochs)
        tf.logging.info('Starting to evaluate.')
        eval_results = fashionAI.evaluate(input_fn=lambda: input_pipeline(False, model_scope, 1))
        tf.logging.info(eval_results)
    tf.logging.info('Finished model {}.'.format(model_scope))

def count_split_examples(split_path, file_pattern=''):
    num_samples = 0
    tfrecords_to_count = [os.path.join(split_path, file) for file in os.listdir(split_path) if file_pattern in file]
    opts = tf.python_io.TFRecordOptions(tf.python_io.TFRecordCompressionType.ZLIB)
    for tfrecord_file in tfrecords_to_count:
        for record in tf.python_io.tf_record_iterator(tfrecord_file):
            num_samples += 1
    return num_samples

def main(_):
    os.environ['TF_ENABLE_WINOGRAD_NONFUSED'] = '1'
    gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=FLAGS.gpu_memory_fraction)
    sess_config = tf.ConfigProto(allow_soft_placement=True, log_device_placement=False, intra_op_parallelism_threads=FLAGS.num_cpu_threads, inter_op_parallelism_threads=FLAGS.num_cpu_threads, gpu_options=gpu_options)
    run_config = tf.estimator.RunConfig().replace(save_checkpoints_secs=FLAGS.save_checkpoints_secs).replace(save_checkpoints_steps=None).replace(save_summary_steps=FLAGS.save_summary_steps).replace(keep_checkpoint_max=5).replace(tf_random_seed=FLAGS.tf_random_seed).replace(log_step_count_steps=FLAGS.log_every_n_steps).replace(session_config=sess_config)
    fashionAI = tf.estimator.Estimator(model_fn=keypoint_model_fn, model_dir=FLAGS.model_dir, config=run_config, params={'train_image_size': FLAGS.train_image_size, 'heatmap_size': FLAGS.heatmap_size, 'feats_channals': FLAGS.feats_channals, 'num_stacks': FLAGS.num_stacks, 'num_modules': FLAGS.num_modules, 'data_format': FLAGS.data_format, 'model_scope': FLAGS.model_scope, 'steps_per_epoch': config.split_size[FLAGS.model_scope if 'all' not in FLAGS.model_scope else '*']['train'] // FLAGS.batch_size, 'batch_size': FLAGS.batch_size, 'weight_decay': FLAGS.weight_decay, 'mse_weight': FLAGS.mse_weight, 'momentum': FLAGS.momentum, 'learning_rate': FLAGS.learning_rate, 'end_learning_rate': FLAGS.end_learning_rate, 'warmup_learning_rate': FLAGS.warmup_learning_rate, 'warmup_steps': FLAGS.warmup_steps, 'decay_boundaries': parse_comma_list(FLAGS.decay_boundaries), 'lr_decay_factors': parse_comma_list(FLAGS.lr_decay_factors)})
    if not FLAGS.run_on_cloud:
        tf.logging.info('params recv: %s', FLAGS.flag_values_dict())
    tf.gfile.MakeDirs(FLAGS.model_dir)
    for _ in range(FLAGS.train_epochs // FLAGS.epochs_per_eval):
        tensors_to_log = {'lr': 'learning_rate', 'loss': 'total_loss', 'mse': 'mse_loss', 'ne': 'ne_mertric'}
        logging_hook = tf.train.LoggingTensorHook(tensors=tensors_to_log, every_n_iter=FLAGS.log_every_n_steps, formatter=lambda dicts: ', '.join(['%s=%.7f' % (k, v) for k, v in dicts.items()]))
        tf.logging.info('Starting a training cycle.')
        fashionAI.train(input_fn=lambda: input_pipeline(True), hooks=[logging_hook])
        tf.logging.info('Starting to evaluate.')
        eval_results = fashionAI.evaluate(input_fn=lambda: input_pipeline(False, 1))
        tf.logging.info(eval_results)

def sub_loop(model_fn, model_scope, model_dir, run_config, train_epochs, epochs_per_eval, lr_decay_factors, decay_boundaries, checkpoint_path=None, checkpoint_exclude_scopes='', checkpoint_model_scope='', ignore_missing_vars=True):
    steps_per_epoch = config.split_size[model_scope if 'all' not in model_scope else '*']['train'] // (FLAGS.xt_batch_size if 'seresnext50' in FLAGS.backbone else FLAGS.batch_size)
    fashionAI = tf.estimator.Estimator(model_fn=model_fn, model_dir=model_dir, config=run_config, params={'checkpoint_path': checkpoint_path, 'model_dir': model_dir, 'checkpoint_exclude_scopes': checkpoint_exclude_scopes, 'model_scope': model_scope, 'checkpoint_model_scope': checkpoint_model_scope, 'ignore_missing_vars': ignore_missing_vars, 'train_image_size': FLAGS.train_image_size, 'heatmap_size': FLAGS.heatmap_size, 'data_format': FLAGS.data_format, 'steps_per_epoch': steps_per_epoch, 'use_ohkm': FLAGS.use_ohkm, 'batch_size': FLAGS.xt_batch_size if 'seresnext50' in FLAGS.backbone else FLAGS.batch_size, 'weight_decay': FLAGS.weight_decay, 'mse_weight': FLAGS.mse_weight, 'momentum': FLAGS.momentum, 'learning_rate': FLAGS.learning_rate, 'end_learning_rate': FLAGS.end_learning_rate, 'warmup_learning_rate': FLAGS.warmup_learning_rate, 'warmup_steps': FLAGS.warmup_steps, 'decay_boundaries': parse_comma_list(decay_boundaries), 'lr_decay_factors': parse_comma_list(lr_decay_factors)})
    tf.gfile.MakeDirs(model_dir)
    tf.logging.info('Starting to train model {}.'.format(model_scope))
    for _ in range(train_epochs // epochs_per_eval):
        tensors_to_log = {'lr': 'learning_rate', 'loss': 'total_loss', 'mse': 'mse_loss', 'ne': 'ne_mertric'}
        logging_hook = tf.train.LoggingTensorHook(tensors=tensors_to_log, every_n_iter=FLAGS.log_every_n_steps, formatter=lambda dicts: '{}:'.format(model_scope) + ', '.join(['%s=%.6f' % (k, v) for k, v in dicts.items()]))
        tf.logging.info('Starting a training cycle.')
        fashionAI.train(input_fn=lambda: input_pipeline(True, model_scope, epochs_per_eval), hooks=[logging_hook], max_steps=steps_per_epoch * train_epochs)
        tf.logging.info('Starting to evaluate.')
        eval_results = fashionAI.evaluate(input_fn=lambda: input_pipeline(False, model_scope, 1))
        tf.logging.info(eval_results)
    tf.logging.info('Finished model {}.'.format(model_scope))

def eval_each(model_fn, model_dir, model_scope, run_config):
    fashionAI = tf.estimator.Estimator(model_fn=model_fn, model_dir=model_dir, config=run_config, params={'train_image_size': FLAGS.train_image_size, 'heatmap_size': FLAGS.heatmap_size, 'feats_channals': FLAGS.feats_channals, 'num_stacks': FLAGS.num_stacks, 'num_modules': FLAGS.num_modules, 'data_format': FLAGS.data_format, 'model_scope': model_scope, 'flip_on_test': FLAGS.flip_on_test})
    tensors_to_log = {'cur_file': 'current_file'}
    logging_hook = tf.train.LoggingTensorHook(tensors=tensors_to_log, every_n_iter=FLAGS.log_every_n_steps, formatter=lambda dicts: ', '.join(['%s=%s' % (k, v) for k, v in dicts.items()]))
    tf.logging.info('Starting to predict model {}.'.format(model_scope))
    pred_results = fashionAI.predict(input_fn=lambda: input_pipeline(model_scope), hooks=[logging_hook], checkpoint_path=train_helper.get_latest_checkpoint_for_evaluate_(model_dir, model_dir))
    return list(pred_results)

def sub_loop(model_fn, model_scope, model_dir, run_config, train_epochs, high_learning_rate, low_learning_rate, checkpoint_path=None):
    steps_per_epoch = config.split_size[model_scope if 'all' not in model_scope else '*']['train'] // FLAGS.batch_size
    fashionAI = tf.estimator.Estimator(model_fn=model_fn, model_dir=model_dir, config=run_config, params={'checkpoint_path': checkpoint_path, 'model_dir': model_dir, 'model_scope': model_scope, 'train_image_size': FLAGS.train_image_size, 'heatmap_size': FLAGS.heatmap_size, 'data_format': FLAGS.data_format, 'steps_per_epoch': steps_per_epoch, 'use_ohkm': FLAGS.use_ohkm, 'batch_size': FLAGS.batch_size, 'weight_decay': FLAGS.weight_decay, 'mse_weight': FLAGS.mse_weight, 'momentum': FLAGS.momentum, 'dummy_train': FLAGS.dummy_train, 'high_learning_rate': high_learning_rate, 'low_learning_rate': low_learning_rate})
    tf.gfile.MakeDirs(model_dir)
    tf.logging.info('Starting to train model {}.'.format(model_scope))
    tensors_to_log = {'lr': 'learning_rate', 'loss': 'total_loss', 'mse': 'mse_loss', 'ne': 'ne_mertric'}
    logging_hook = tf.train.LoggingTensorHook(tensors=tensors_to_log, every_n_iter=FLAGS.log_every_n_steps, formatter=lambda dicts: '{}:'.format(model_scope) + ', '.join(['%s=%.6f' % (k, v) for k, v in dicts.items()]))
    tf.logging.info('Starting a training cycle.')
    fashionAI.train(input_fn=lambda: input_pipeline(True, model_scope, train_epochs), hooks=[logging_hook], max_steps=steps_per_epoch * (train_epochs + 1 if FLAGS.dummy_train else train_epochs))
    tf.logging.info('Finished model {}.'.format(model_scope))

def sub_loop(model_fn, model_scope, model_dir, run_config, train_epochs, epochs_per_eval, lr_decay_factors, decay_boundaries, checkpoint_path=None, checkpoint_exclude_scopes='', checkpoint_model_scope='', ignore_missing_vars=True):
    steps_per_epoch = config.split_size[model_scope if 'all' not in model_scope else '*']['train'] // FLAGS.batch_size
    _replicate_model_fn = tf_replicate_model_fn.replicate_model_fn(model_fn, loss_reduction=tf.losses.Reduction.MEAN)
    fashionAI = tf.estimator.Estimator(model_fn=_replicate_model_fn, model_dir=model_dir, config=run_config.replace(save_checkpoints_steps=2 * steps_per_epoch), params={'checkpoint_path': checkpoint_path, 'model_dir': model_dir, 'checkpoint_exclude_scopes': checkpoint_exclude_scopes, 'model_scope': model_scope, 'checkpoint_model_scope': checkpoint_model_scope, 'ignore_missing_vars': ignore_missing_vars, 'train_image_size': FLAGS.train_image_size, 'heatmap_size': FLAGS.heatmap_size, 'data_format': FLAGS.data_format, 'steps_per_epoch': steps_per_epoch, 'use_ohkm': FLAGS.use_ohkm, 'batch_size': FLAGS.batch_size, 'weight_decay': FLAGS.weight_decay, 'mse_weight': FLAGS.mse_weight, 'momentum': FLAGS.momentum, 'learning_rate': FLAGS.learning_rate, 'end_learning_rate': FLAGS.end_learning_rate, 'warmup_learning_rate': FLAGS.warmup_learning_rate, 'warmup_steps': FLAGS.warmup_steps, 'decay_boundaries': parse_comma_list(decay_boundaries), 'lr_decay_factors': parse_comma_list(lr_decay_factors)})
    tf.gfile.MakeDirs(model_dir)
    tf.logging.info('Starting to train model {}.'.format(model_scope))
    for _ in range(train_epochs // epochs_per_eval):
        tensors_to_log = {'lr': 'learning_rate', 'loss': 'total_loss', 'mse': 'mse_loss', 'ne': 'ne_mertric'}
        logging_hook = tf.train.LoggingTensorHook(tensors=tensors_to_log, every_n_iter=FLAGS.log_every_n_steps, formatter=lambda dicts: '{}:'.format(model_scope) + ', '.join(['%s=%.6f' % (k, v) for k, v in dicts.items()]))
        tf.logging.info('Starting a training cycle.')
        fashionAI.train(input_fn=lambda: input_pipeline(True, model_scope, epochs_per_eval), hooks=[logging_hook], max_steps=steps_per_epoch * train_epochs)
        tf.logging.info('Starting to evaluate.')
        eval_results = fashionAI.evaluate(input_fn=lambda: input_pipeline(False, model_scope, 1))
        tf.logging.info(eval_results)
    tf.logging.info('Finished model {}.'.format(model_scope))

def eval_each(model_fn, model_dir, model_scope, run_config):
    fashionAI = tf.estimator.Estimator(model_fn=model_fn, model_dir=model_dir, config=run_config, params={'train_image_size': FLAGS.train_image_size, 'heatmap_size': FLAGS.heatmap_size, 'data_format': FLAGS.data_format, 'model_scope': model_scope, 'flip_on_test': FLAGS.flip_on_test})
    tensors_to_log = {'cur_file': 'current_file'}
    logging_hook = tf.train.LoggingTensorHook(tensors=tensors_to_log, every_n_iter=FLAGS.log_every_n_steps, formatter=lambda dicts: ', '.join(['%s=%s' % (k, v) for k, v in dicts.items()]))
    tf.logging.info('Starting to predict model {}.'.format(model_scope))
    pred_results = fashionAI.predict(input_fn=lambda: input_pipeline(model_scope), hooks=[logging_hook], checkpoint_path=train_helper.get_latest_checkpoint_for_evaluate_(model_dir, model_dir))
    return list(pred_results)

def sub_loop(model_fn, model_scope, model_dir, run_config, train_epochs, epochs_per_eval, lr_decay_factors, decay_boundaries, checkpoint_path=None, checkpoint_exclude_scopes='', checkpoint_model_scope='', ignore_missing_vars=True):
    steps_per_epoch = config.split_size[model_scope if 'all' not in model_scope else '*']['train'] // FLAGS.batch_size
    _replicate_model_fn = tf_replicate_model_fn.replicate_model_fn(model_fn, loss_reduction=tf.losses.Reduction.MEAN)
    fashionAI = tf.estimator.Estimator(model_fn=_replicate_model_fn, model_dir=model_dir, config=run_config.replace(save_checkpoints_steps=2 * steps_per_epoch), params={'checkpoint_path': checkpoint_path, 'model_dir': model_dir, 'checkpoint_exclude_scopes': checkpoint_exclude_scopes, 'model_scope': model_scope, 'checkpoint_model_scope': checkpoint_model_scope, 'ignore_missing_vars': ignore_missing_vars, 'net_depth': FLAGS.net_depth, 'train_image_size': FLAGS.train_image_size, 'heatmap_size': FLAGS.heatmap_size, 'data_format': FLAGS.data_format, 'steps_per_epoch': steps_per_epoch, 'use_ohkm': FLAGS.use_ohkm, 'batch_size': FLAGS.batch_size, 'weight_decay': FLAGS.weight_decay, 'mse_weight': FLAGS.mse_weight, 'momentum': FLAGS.momentum, 'learning_rate': FLAGS.learning_rate, 'end_learning_rate': FLAGS.end_learning_rate, 'warmup_learning_rate': FLAGS.warmup_learning_rate, 'warmup_steps': FLAGS.warmup_steps, 'decay_boundaries': parse_comma_list(decay_boundaries), 'lr_decay_factors': parse_comma_list(lr_decay_factors)})
    tf.gfile.MakeDirs(model_dir)
    tf.logging.info('Starting to train model {}.'.format(model_scope))
    for _ in range(train_epochs // epochs_per_eval):
        tensors_to_log = {'lr': 'learning_rate', 'loss': 'total_loss', 'mse': 'mse_loss', 'ne': 'ne_mertric'}
        logging_hook = tf.train.LoggingTensorHook(tensors=tensors_to_log, every_n_iter=FLAGS.log_every_n_steps, formatter=lambda dicts: '{}:'.format(model_scope) + ', '.join(['%s=%.6f' % (k, v) for k, v in dicts.items()]))
        tf.logging.info('Starting a training cycle.')
        fashionAI.train(input_fn=lambda: input_pipeline(True, model_scope, epochs_per_eval), hooks=[logging_hook], max_steps=steps_per_epoch * train_epochs)
        tf.logging.info('Starting to evaluate.')
        eval_results = fashionAI.evaluate(input_fn=lambda: input_pipeline(False, model_scope, 1))
        tf.logging.info(eval_results)
    tf.logging.info('Finished model {}.'.format(model_scope))

def count_split_examples(split_path, category='tfrecord', file_prefix='.tfrecord'):
    num_samples = 0
    tfrecords_to_count = [os.path.join(split_path, file) for file in os.listdir(split_path) if file_prefix in file]
    opts = tf.python_io.TFRecordOptions(tf.python_io.TFRecordCompressionType.ZLIB)
    for tfrecord_file in tfrecords_to_count:
        if category not in tfrecord_file:
            continue
        for record in tf.python_io.tf_record_iterator(tfrecord_file):
            num_samples += 1
    return num_samples

