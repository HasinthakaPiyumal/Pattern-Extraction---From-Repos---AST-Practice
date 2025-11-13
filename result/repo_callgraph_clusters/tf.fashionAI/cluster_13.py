# Cluster 13

def parse_comma_list(args):
    return [float(s.strip()) for s in args.split(',')]

def main(_):
    os.environ['TF_ENABLE_WINOGRAD_NONFUSED'] = '1'
    gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=FLAGS.gpu_memory_fraction)
    sess_config = tf.ConfigProto(allow_soft_placement=True, log_device_placement=False, intra_op_parallelism_threads=FLAGS.num_cpu_threads, inter_op_parallelism_threads=FLAGS.num_cpu_threads, gpu_options=gpu_options)
    run_config = tf.estimator.RunConfig().replace(save_checkpoints_secs=FLAGS.save_checkpoints_secs).replace(save_checkpoints_steps=None).replace(save_summary_steps=FLAGS.save_summary_steps).replace(keep_checkpoint_max=5).replace(tf_random_seed=FLAGS.tf_random_seed).replace(log_step_count_steps=FLAGS.log_every_n_steps).replace(session_config=sess_config)
    if FLAGS.seq_train:
        detail_params = {'all': {'model_dir': os.path.join(FLAGS.model_dir, 'all'), 'train_epochs': 6, 'epochs_per_eval': 4, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '3, 4', 'model_scope': 'all', 'checkpoint_path': None, 'checkpoint_model_scope': '', 'checkpoint_exclude_scopes': '', 'ignore_missing_vars': True}, 'blouse': {'model_dir': os.path.join(FLAGS.model_dir, 'blouse'), 'train_epochs': 50, 'epochs_per_eval': 30, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '15, 30', 'model_scope': 'blouse', 'checkpoint_path': os.path.join(FLAGS.model_dir, 'all'), 'checkpoint_model_scope': 'all', 'checkpoint_exclude_scopes': 'blouse/additional_layer, blouse/feature_pyramid/conv_heatmap, blouse/global_net/conv_heatmap', 'ignore_missing_vars': True}, 'dress': {'model_dir': os.path.join(FLAGS.model_dir, 'dress'), 'train_epochs': 50, 'epochs_per_eval': 30, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '15, 30', 'model_scope': 'dress', 'checkpoint_path': os.path.join(FLAGS.model_dir, 'all'), 'checkpoint_model_scope': 'all', 'checkpoint_exclude_scopes': 'dress/additional_layer, dress/feature_pyramid/conv_heatmap, dress/global_net/conv_heatmap', 'ignore_missing_vars': True}, 'outwear': {'model_dir': os.path.join(FLAGS.model_dir, 'outwear'), 'train_epochs': 50, 'epochs_per_eval': 30, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '15, 30', 'model_scope': 'outwear', 'checkpoint_path': os.path.join(FLAGS.model_dir, 'all'), 'checkpoint_model_scope': 'all', 'checkpoint_exclude_scopes': 'outwear/additional_layer, outwear/feature_pyramid/conv_heatmap, outwear/global_net/conv_heatmap', 'ignore_missing_vars': True}, 'skirt': {'model_dir': os.path.join(FLAGS.model_dir, 'skirt'), 'train_epochs': 50, 'epochs_per_eval': 30, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '15, 30', 'model_scope': 'skirt', 'checkpoint_path': os.path.join(FLAGS.model_dir, 'all'), 'checkpoint_model_scope': 'all', 'checkpoint_exclude_scopes': 'skirt/additional_layer, skirt/feature_pyramid/conv_heatmap, skirt/global_net/conv_heatmap', 'ignore_missing_vars': True}, 'trousers': {'model_dir': os.path.join(FLAGS.model_dir, 'trousers'), 'train_epochs': 50, 'epochs_per_eval': 30, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '15, 30', 'model_scope': 'trousers', 'checkpoint_path': os.path.join(FLAGS.model_dir, 'all'), 'checkpoint_model_scope': 'all', 'checkpoint_exclude_scopes': 'trousers/additional_layer, trousers/feature_pyramid/conv_heatmap, trousers/global_net/conv_heatmap', 'ignore_missing_vars': True}}
    else:
        detail_params = {'blouse': {'model_dir': os.path.join(FLAGS.model_dir, 'blouse'), 'train_epochs': 28, 'epochs_per_eval': 7, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '10, 20', 'model_scope': 'blouse', 'checkpoint_path': os.path.join(FLAGS.data_dir, FLAGS.cloud_checkpoint_path) if FLAGS.run_on_cloud else FLAGS.checkpoint_path, 'checkpoint_model_scope': '', 'checkpoint_exclude_scopes': 'blouse/additional_layer, blouse/feature_pyramid, blouse/global_net', 'ignore_missing_vars': True}, 'dress': {'model_dir': os.path.join(FLAGS.model_dir, 'dress'), 'train_epochs': 28, 'epochs_per_eval': 7, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '10, 20', 'model_scope': 'dress', 'checkpoint_path': os.path.join(FLAGS.data_dir, FLAGS.cloud_checkpoint_path) if FLAGS.run_on_cloud else FLAGS.checkpoint_path, 'checkpoint_model_scope': '', 'checkpoint_exclude_scopes': 'dress/additional_layer, dress/feature_pyramid, dress/global_net', 'ignore_missing_vars': True}, 'outwear': {'model_dir': os.path.join(FLAGS.model_dir, 'outwear'), 'train_epochs': 28, 'epochs_per_eval': 7, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '10, 20', 'model_scope': 'outwear', 'checkpoint_path': os.path.join(FLAGS.data_dir, FLAGS.cloud_checkpoint_path) if FLAGS.run_on_cloud else FLAGS.checkpoint_path, 'checkpoint_model_scope': '', 'checkpoint_exclude_scopes': 'outwear/additional_layer, outwear/feature_pyramid, outwear/global_net', 'ignore_missing_vars': True}, 'skirt': {'model_dir': os.path.join(FLAGS.model_dir, 'skirt'), 'train_epochs': 28, 'epochs_per_eval': 7, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '10, 20', 'model_scope': 'skirt', 'checkpoint_path': os.path.join(FLAGS.data_dir, FLAGS.cloud_checkpoint_path) if FLAGS.run_on_cloud else FLAGS.checkpoint_path, 'checkpoint_model_scope': '', 'checkpoint_exclude_scopes': 'skirt/additional_layer, skirt/feature_pyramid, skirt/global_net', 'ignore_missing_vars': True}, 'trousers': {'model_dir': os.path.join(FLAGS.model_dir, 'trousers'), 'train_epochs': 28, 'epochs_per_eval': 7, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '10, 20', 'model_scope': 'trousers', 'checkpoint_path': os.path.join(FLAGS.data_dir, FLAGS.cloud_checkpoint_path) if FLAGS.run_on_cloud else FLAGS.checkpoint_path, 'checkpoint_model_scope': '', 'checkpoint_exclude_scopes': 'trousers/additional_layer, trousers/feature_pyramid, trousers/global_net', 'ignore_missing_vars': True}}
    model_to_train = [s.strip() for s in FLAGS.model_to_train.split(',')]
    for m in model_to_train:
        sub_loop(keypoint_model_fn, m, detail_params[m]['model_dir'], run_config, detail_params[m]['train_epochs'], detail_params[m]['epochs_per_eval'], detail_params[m]['lr_decay_factors'], detail_params[m]['decay_boundaries'], detail_params[m]['checkpoint_path'], detail_params[m]['checkpoint_exclude_scopes'], detail_params[m]['checkpoint_model_scope'], detail_params[m]['ignore_missing_vars'])

def parse_comma_list(args):
    return [float(s.strip()) for s in args.split(',')]

def main(_):
    os.environ['TF_ENABLE_WINOGRAD_NONFUSED'] = '1'
    gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=FLAGS.gpu_memory_fraction)
    sess_config = tf.ConfigProto(allow_soft_placement=True, log_device_placement=False, intra_op_parallelism_threads=FLAGS.num_cpu_threads, inter_op_parallelism_threads=FLAGS.num_cpu_threads, gpu_options=gpu_options)
    run_config = tf.estimator.RunConfig().replace(save_checkpoints_secs=FLAGS.save_checkpoints_secs).replace(save_checkpoints_steps=None).replace(save_summary_steps=FLAGS.save_summary_steps).replace(keep_checkpoint_max=5).replace(tf_random_seed=FLAGS.tf_random_seed).replace(log_step_count_steps=FLAGS.log_every_n_steps).replace(session_config=sess_config)
    if FLAGS.seq_train:
        detail_params = {'all': {'model_dir': os.path.join(FLAGS.model_dir, 'all'), 'train_epochs': 6, 'epochs_per_eval': 4, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '3, 4', 'model_scope': 'all', 'checkpoint_path': None, 'checkpoint_model_scope': '', 'checkpoint_exclude_scopes': '', 'ignore_missing_vars': True}, 'blouse': {'model_dir': os.path.join(FLAGS.model_dir, 'blouse'), 'train_epochs': 50, 'epochs_per_eval': 30, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '15, 30', 'model_scope': 'blouse', 'checkpoint_path': os.path.join(FLAGS.model_dir, 'all'), 'checkpoint_model_scope': 'all', 'checkpoint_exclude_scopes': 'blouse/feature_pyramid/conv_heatmap, blouse/global_net/conv_heatmap', 'ignore_missing_vars': True}, 'dress': {'model_dir': os.path.join(FLAGS.model_dir, 'dress'), 'train_epochs': 50, 'epochs_per_eval': 30, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '15, 30', 'model_scope': 'dress', 'checkpoint_path': os.path.join(FLAGS.model_dir, 'all'), 'checkpoint_model_scope': 'all', 'checkpoint_exclude_scopes': 'dress/feature_pyramid/conv_heatmap, dress/global_net/conv_heatmap', 'ignore_missing_vars': True}, 'outwear': {'model_dir': os.path.join(FLAGS.model_dir, 'outwear'), 'train_epochs': 50, 'epochs_per_eval': 30, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '15, 30', 'model_scope': 'outwear', 'checkpoint_path': os.path.join(FLAGS.model_dir, 'all'), 'checkpoint_model_scope': 'all', 'checkpoint_exclude_scopes': 'outwear/feature_pyramid/conv_heatmap, outwear/global_net/conv_heatmap', 'ignore_missing_vars': True}, 'skirt': {'model_dir': os.path.join(FLAGS.model_dir, 'skirt'), 'train_epochs': 50, 'epochs_per_eval': 30, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '15, 30', 'model_scope': 'skirt', 'checkpoint_path': os.path.join(FLAGS.model_dir, 'all'), 'checkpoint_model_scope': 'all', 'checkpoint_exclude_scopes': 'skirt/feature_pyramid/conv_heatmap, skirt/global_net/conv_heatmap', 'ignore_missing_vars': True}, 'trousers': {'model_dir': os.path.join(FLAGS.model_dir, 'trousers'), 'train_epochs': 50, 'epochs_per_eval': 30, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '15, 30', 'model_scope': 'trousers', 'checkpoint_path': os.path.join(FLAGS.model_dir, 'all'), 'checkpoint_model_scope': 'all', 'checkpoint_exclude_scopes': 'trousers/feature_pyramid/conv_heatmap, trousers/global_net/conv_heatmap', 'ignore_missing_vars': True}}
    else:
        detail_params = {'blouse': {'model_dir': os.path.join(FLAGS.model_dir, 'blouse'), 'train_epochs': 28, 'epochs_per_eval': 7, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '10, 20', 'model_scope': 'blouse', 'checkpoint_path': os.path.join(FLAGS.data_dir, FLAGS.cloud_checkpoint_path) if FLAGS.run_on_cloud else FLAGS.checkpoint_path, 'checkpoint_model_scope': '', 'checkpoint_exclude_scopes': 'blouse/feature_pyramid, blouse/global_net', 'ignore_missing_vars': True}, 'dress': {'model_dir': os.path.join(FLAGS.model_dir, 'dress'), 'train_epochs': 28, 'epochs_per_eval': 7, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '10, 20', 'model_scope': 'dress', 'checkpoint_path': os.path.join(FLAGS.data_dir, FLAGS.cloud_checkpoint_path) if FLAGS.run_on_cloud else FLAGS.checkpoint_path, 'checkpoint_model_scope': '', 'checkpoint_exclude_scopes': 'dress/feature_pyramid, dress/global_net', 'ignore_missing_vars': True}, 'outwear': {'model_dir': os.path.join(FLAGS.model_dir, 'outwear'), 'train_epochs': 28, 'epochs_per_eval': 7, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '10, 20', 'model_scope': 'outwear', 'checkpoint_path': os.path.join(FLAGS.data_dir, FLAGS.cloud_checkpoint_path) if FLAGS.run_on_cloud else FLAGS.checkpoint_path, 'checkpoint_model_scope': '', 'checkpoint_exclude_scopes': 'outwear/feature_pyramid, outwear/global_net', 'ignore_missing_vars': True}, 'skirt': {'model_dir': os.path.join(FLAGS.model_dir, 'skirt'), 'train_epochs': 28, 'epochs_per_eval': 7, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '10, 20', 'model_scope': 'skirt', 'checkpoint_path': os.path.join(FLAGS.data_dir, FLAGS.cloud_checkpoint_path) if FLAGS.run_on_cloud else FLAGS.checkpoint_path, 'checkpoint_model_scope': '', 'checkpoint_exclude_scopes': 'skirt/feature_pyramid, skirt/global_net', 'ignore_missing_vars': True}, 'trousers': {'model_dir': os.path.join(FLAGS.model_dir, 'trousers'), 'train_epochs': 28, 'epochs_per_eval': 7, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '10, 20', 'model_scope': 'trousers', 'checkpoint_path': os.path.join(FLAGS.data_dir, FLAGS.cloud_checkpoint_path) if FLAGS.run_on_cloud else FLAGS.checkpoint_path, 'checkpoint_model_scope': '', 'checkpoint_exclude_scopes': 'trousers/feature_pyramid, trousers/global_net', 'ignore_missing_vars': True}}
    model_to_train = [s.strip() for s in FLAGS.model_to_train.split(',')]
    for m in model_to_train:
        sub_loop(keypoint_model_fn, m, detail_params[m]['model_dir'], run_config, detail_params[m]['train_epochs'], detail_params[m]['epochs_per_eval'], detail_params[m]['lr_decay_factors'], detail_params[m]['decay_boundaries'], detail_params[m]['checkpoint_path'], detail_params[m]['checkpoint_exclude_scopes'], detail_params[m]['checkpoint_model_scope'], detail_params[m]['ignore_missing_vars'])

def parse_comma_list(args):
    return [float(s.strip()) for s in args.split(',')]

def main(_):
    os.environ['TF_ENABLE_WINOGRAD_NONFUSED'] = '1'
    gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=FLAGS.gpu_memory_fraction)
    sess_config = tf.ConfigProto(allow_soft_placement=True, log_device_placement=False, intra_op_parallelism_threads=FLAGS.num_cpu_threads, inter_op_parallelism_threads=FLAGS.num_cpu_threads, gpu_options=gpu_options)
    run_config = tf.estimator.RunConfig().replace(save_checkpoints_secs=None).replace(save_checkpoints_steps=None).replace(save_summary_steps=FLAGS.save_summary_steps).replace(keep_checkpoint_max=5).replace(tf_random_seed=FLAGS.tf_random_seed).replace(log_step_count_steps=FLAGS.log_every_n_steps).replace(session_config=sess_config)
    model_to_eval = [s.strip() for s in FLAGS.model_to_eval.split(',')]
    full_model_dir = os.path.join(FLAGS.model_dir, all_models[FLAGS.backbone.strip()]['logs_sub_dir'])
    for m in model_to_eval:
        if m == '':
            continue
        pred_results = eval_each(keypoint_model_fn, os.path.join(full_model_dir, m), m, run_config)
        df = pd.DataFrame(columns=['image_id', 'image_category'] + config.all_keys)
        cur_record = 0
        gloabl2local_ind = dict(zip(config.class2global_ind_map[m], list(range(len(config.class2global_ind_map[m])))))
        for pred_item in pred_results:
            temp_list = []
            index = 0
            x = pred_item['pred_x'].tolist()
            y = pred_item['pred_y'].tolist()
            filename = pred_item['file_name'].decode('utf8')
            for ind in list(range(config.class_num_joints['*'])):
                if ind in gloabl2local_ind:
                    temp_list.append('{}_{}_1'.format(round(x[gloabl2local_ind[ind]]), round(y[gloabl2local_ind[ind]])))
                else:
                    temp_list.append('-1_-1_-1')
            df.loc[cur_record] = [filename, m] + temp_list
            cur_record = cur_record + 1
        df.to_csv('./{}_{}.csv'.format(FLAGS.backbone.strip(), m), encoding='utf-8', index=False)
    df_list = [pd.read_csv('./{}_{}.csv'.format(FLAGS.backbone.strip(), model_to_eval[0]), encoding='utf-8')]
    for m in model_to_eval[1:]:
        if m == '':
            continue
        df_list.append(pd.read_csv('./{}_{}.csv'.format(FLAGS.backbone.strip(), m), encoding='utf-8'))
    time_stamps = int(time.time())
    pd.concat(df_list, ignore_index=True).to_csv('./{}_sub_{}.csv'.format(FLAGS.backbone.strip(), time_stamps), encoding='utf-8', index=False)
    if FLAGS.run_on_cloud:
        tf.gfile.Copy('./{}_sub_{}.csv'.format(FLAGS.backbone.strip(), time_stamps), os.path.join(full_model_dir, '{}_sub_{}.csv'.format(FLAGS.backbone.strip(), time_stamps)), overwrite=True)

def parse_comma_list(args):
    return [float(s.strip()) for s in args.split(',')]

def parse_str_comma_list(args):
    return [s.strip() for s in args.split(',')]

def parse_comma_list(args):
    return [float(s.strip()) for s in args.split(',')]

def main(_):
    os.environ['TF_ENABLE_WINOGRAD_NONFUSED'] = '1'
    gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=FLAGS.gpu_memory_fraction)
    sess_config = tf.ConfigProto(allow_soft_placement=True, log_device_placement=False, intra_op_parallelism_threads=FLAGS.num_cpu_threads, inter_op_parallelism_threads=FLAGS.num_cpu_threads, gpu_options=gpu_options)
    run_config = tf.estimator.RunConfig().replace(save_checkpoints_secs=FLAGS.save_checkpoints_secs).replace(save_checkpoints_steps=None).replace(save_summary_steps=FLAGS.save_summary_steps).replace(keep_checkpoint_max=5).replace(tf_random_seed=FLAGS.tf_random_seed).replace(log_step_count_steps=FLAGS.log_every_n_steps).replace(session_config=sess_config)
    if FLAGS.seq_train:
        detail_params = {'all': {'model_dir': os.path.join(FLAGS.model_dir, 'all'), 'train_epochs': 6, 'epochs_per_eval': 4, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '3, 4', 'model_scope': 'all', 'checkpoint_path': None, 'checkpoint_model_scope': '', 'checkpoint_exclude_scopes': '', 'ignore_missing_vars': True}, 'blouse': {'model_dir': os.path.join(FLAGS.model_dir, 'blouse'), 'train_epochs': 50, 'epochs_per_eval': 30, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '15, 30', 'model_scope': 'blouse', 'checkpoint_path': os.path.join(FLAGS.model_dir, 'all'), 'checkpoint_model_scope': 'all', 'checkpoint_exclude_scopes': 'blouse/hg_heatmap', 'ignore_missing_vars': True}, 'dress': {'model_dir': os.path.join(FLAGS.model_dir, 'dress'), 'train_epochs': 50, 'epochs_per_eval': 30, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '15, 30', 'model_scope': 'dress', 'checkpoint_path': os.path.join(FLAGS.model_dir, 'all'), 'checkpoint_model_scope': 'all', 'checkpoint_exclude_scopes': 'dress/hg_heatmap', 'ignore_missing_vars': True}, 'outwear': {'model_dir': os.path.join(FLAGS.model_dir, 'outwear'), 'train_epochs': 50, 'epochs_per_eval': 30, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '15, 30', 'model_scope': 'outwear', 'checkpoint_path': os.path.join(FLAGS.model_dir, 'all'), 'checkpoint_model_scope': 'all', 'checkpoint_exclude_scopes': 'outwear/hg_heatmap', 'ignore_missing_vars': True}, 'skirt': {'model_dir': os.path.join(FLAGS.model_dir, 'skirt'), 'train_epochs': 50, 'epochs_per_eval': 30, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '15, 30', 'model_scope': 'skirt', 'checkpoint_path': os.path.join(FLAGS.model_dir, 'all'), 'checkpoint_model_scope': 'all', 'checkpoint_exclude_scopes': 'skirt/hg_heatmap', 'ignore_missing_vars': True}, 'trousers': {'model_dir': os.path.join(FLAGS.model_dir, 'trousers'), 'train_epochs': 50, 'epochs_per_eval': 30, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '15, 30', 'model_scope': 'trousers', 'checkpoint_path': os.path.join(FLAGS.model_dir, 'all'), 'checkpoint_model_scope': 'all', 'checkpoint_exclude_scopes': 'trousers/hg_heatmap', 'ignore_missing_vars': True}}
    else:
        detail_params = {'blouse': {'model_dir': os.path.join(FLAGS.model_dir, 'blouse'), 'train_epochs': 40, 'epochs_per_eval': 15, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '10, 20', 'model_scope': 'blouse', 'checkpoint_path': None, 'checkpoint_model_scope': '', 'checkpoint_exclude_scopes': '', 'ignore_missing_vars': True}, 'dress': {'model_dir': os.path.join(FLAGS.model_dir, 'dress'), 'train_epochs': 40, 'epochs_per_eval': 15, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '10, 20', 'model_scope': 'dress', 'checkpoint_path': None, 'checkpoint_model_scope': '', 'checkpoint_exclude_scopes': '', 'ignore_missing_vars': True}, 'outwear': {'model_dir': os.path.join(FLAGS.model_dir, 'outwear'), 'train_epochs': 40, 'epochs_per_eval': 15, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '10, 20', 'model_scope': 'outwear', 'checkpoint_path': None, 'checkpoint_model_scope': '', 'checkpoint_exclude_scopes': '', 'ignore_missing_vars': True}, 'skirt': {'model_dir': os.path.join(FLAGS.model_dir, 'skirt'), 'train_epochs': 40, 'epochs_per_eval': 15, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '10, 20', 'model_scope': 'skirt', 'checkpoint_path': None, 'checkpoint_model_scope': '', 'checkpoint_exclude_scopes': '', 'ignore_missing_vars': True}, 'trousers': {'model_dir': os.path.join(FLAGS.model_dir, 'trousers'), 'train_epochs': 40, 'epochs_per_eval': 15, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '10, 20', 'model_scope': 'trousers', 'checkpoint_path': None, 'checkpoint_model_scope': '', 'checkpoint_exclude_scopes': '', 'ignore_missing_vars': True}}
    model_to_train = [s.strip() for s in FLAGS.model_to_train.split(',')]
    for m in model_to_train:
        sub_loop(keypoint_model_fn, m, detail_params[m]['model_dir'], run_config, detail_params[m]['train_epochs'], detail_params[m]['epochs_per_eval'], detail_params[m]['lr_decay_factors'], detail_params[m]['decay_boundaries'], detail_params[m]['checkpoint_path'], detail_params[m]['checkpoint_exclude_scopes'], detail_params[m]['checkpoint_model_scope'], detail_params[m]['ignore_missing_vars'])

def parse_comma_list(args):
    return [float(s.strip()) for s in args.split(',')]

def main(_):
    os.environ['TF_ENABLE_WINOGRAD_NONFUSED'] = '1'
    gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=FLAGS.gpu_memory_fraction)
    sess_config = tf.ConfigProto(allow_soft_placement=True, log_device_placement=False, intra_op_parallelism_threads=FLAGS.num_cpu_threads, inter_op_parallelism_threads=FLAGS.num_cpu_threads, gpu_options=gpu_options)
    run_config = tf.estimator.RunConfig().replace(save_checkpoints_secs=FLAGS.save_checkpoints_secs).replace(save_checkpoints_steps=None).replace(save_summary_steps=FLAGS.save_summary_steps).replace(keep_checkpoint_max=5).replace(tf_random_seed=FLAGS.tf_random_seed).replace(log_step_count_steps=FLAGS.log_every_n_steps).replace(session_config=sess_config)
    if FLAGS.seq_train:
        detail_params = {'all': {'model_dir': os.path.join(FLAGS.model_dir, 'all'), 'train_epochs': 6, 'epochs_per_eval': 4, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '3, 4', 'model_scope': 'all', 'checkpoint_path': None, 'checkpoint_model_scope': '', 'checkpoint_exclude_scopes': '', 'ignore_missing_vars': True}, 'blouse': {'model_dir': os.path.join(FLAGS.model_dir, 'blouse'), 'train_epochs': 50, 'epochs_per_eval': 30, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '15, 30', 'model_scope': 'blouse', 'checkpoint_path': os.path.join(FLAGS.model_dir, 'all'), 'checkpoint_model_scope': 'all', 'checkpoint_exclude_scopes': 'blouse/additional_layer, blouse/feature_pyramid/conv_heatmap, blouse/global_net/conv_heatmap', 'ignore_missing_vars': True}, 'dress': {'model_dir': os.path.join(FLAGS.model_dir, 'dress'), 'train_epochs': 50, 'epochs_per_eval': 30, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '15, 30', 'model_scope': 'dress', 'checkpoint_path': os.path.join(FLAGS.model_dir, 'all'), 'checkpoint_model_scope': 'all', 'checkpoint_exclude_scopes': 'dress/additional_layer, dress/feature_pyramid/conv_heatmap, dress/global_net/conv_heatmap', 'ignore_missing_vars': True}, 'outwear': {'model_dir': os.path.join(FLAGS.model_dir, 'outwear'), 'train_epochs': 50, 'epochs_per_eval': 30, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '15, 30', 'model_scope': 'outwear', 'checkpoint_path': os.path.join(FLAGS.model_dir, 'all'), 'checkpoint_model_scope': 'all', 'checkpoint_exclude_scopes': 'outwear/additional_layer, outwear/feature_pyramid/conv_heatmap, outwear/global_net/conv_heatmap', 'ignore_missing_vars': True}, 'skirt': {'model_dir': os.path.join(FLAGS.model_dir, 'skirt'), 'train_epochs': 50, 'epochs_per_eval': 30, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '15, 30', 'model_scope': 'skirt', 'checkpoint_path': os.path.join(FLAGS.model_dir, 'all'), 'checkpoint_model_scope': 'all', 'checkpoint_exclude_scopes': 'skirt/additional_layer, skirt/feature_pyramid/conv_heatmap, skirt/global_net/conv_heatmap', 'ignore_missing_vars': True}, 'trousers': {'model_dir': os.path.join(FLAGS.model_dir, 'trousers'), 'train_epochs': 50, 'epochs_per_eval': 30, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '15, 30', 'model_scope': 'trousers', 'checkpoint_path': os.path.join(FLAGS.model_dir, 'all'), 'checkpoint_model_scope': 'all', 'checkpoint_exclude_scopes': 'trousers/additional_layer, trousers/feature_pyramid/conv_heatmap, trousers/global_net/conv_heatmap', 'ignore_missing_vars': True}}
    else:
        detail_params = {'blouse': {'model_dir': os.path.join(FLAGS.model_dir, 'blouse'), 'train_epochs': 28, 'epochs_per_eval': 7, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '10, 20', 'model_scope': 'blouse', 'checkpoint_path': os.path.join(FLAGS.data_dir, FLAGS.cloud_checkpoint_path) if FLAGS.run_on_cloud else FLAGS.checkpoint_path, 'checkpoint_model_scope': '', 'checkpoint_exclude_scopes': 'blouse/additional_layer, blouse/feature_pyramid, blouse/global_net', 'ignore_missing_vars': True}, 'dress': {'model_dir': os.path.join(FLAGS.model_dir, 'dress'), 'train_epochs': 28, 'epochs_per_eval': 7, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '10, 20', 'model_scope': 'dress', 'checkpoint_path': os.path.join(FLAGS.data_dir, FLAGS.cloud_checkpoint_path) if FLAGS.run_on_cloud else FLAGS.checkpoint_path, 'checkpoint_model_scope': '', 'checkpoint_exclude_scopes': 'dress/additional_layer, dress/feature_pyramid, dress/global_net', 'ignore_missing_vars': True}, 'outwear': {'model_dir': os.path.join(FLAGS.model_dir, 'outwear'), 'train_epochs': 28, 'epochs_per_eval': 7, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '10, 20', 'model_scope': 'outwear', 'checkpoint_path': os.path.join(FLAGS.data_dir, FLAGS.cloud_checkpoint_path) if FLAGS.run_on_cloud else FLAGS.checkpoint_path, 'checkpoint_model_scope': '', 'checkpoint_exclude_scopes': 'outwear/additional_layer, outwear/feature_pyramid, outwear/global_net', 'ignore_missing_vars': True}, 'skirt': {'model_dir': os.path.join(FLAGS.model_dir, 'skirt'), 'train_epochs': 28, 'epochs_per_eval': 7, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '10, 20', 'model_scope': 'skirt', 'checkpoint_path': os.path.join(FLAGS.data_dir, FLAGS.cloud_checkpoint_path) if FLAGS.run_on_cloud else FLAGS.checkpoint_path, 'checkpoint_model_scope': '', 'checkpoint_exclude_scopes': 'skirt/additional_layer, skirt/feature_pyramid, skirt/global_net', 'ignore_missing_vars': True}, 'trousers': {'model_dir': os.path.join(FLAGS.model_dir, 'trousers'), 'train_epochs': 28, 'epochs_per_eval': 7, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '10, 20', 'model_scope': 'trousers', 'checkpoint_path': os.path.join(FLAGS.data_dir, FLAGS.cloud_checkpoint_path) if FLAGS.run_on_cloud else FLAGS.checkpoint_path, 'checkpoint_model_scope': '', 'checkpoint_exclude_scopes': 'trousers/additional_layer, trousers/feature_pyramid, trousers/global_net', 'ignore_missing_vars': True}}
    model_to_train = [s.strip() for s in FLAGS.model_to_train.split(',')]
    for m in model_to_train:
        sub_loop(keypoint_model_fn, m, detail_params[m]['model_dir'], run_config, detail_params[m]['train_epochs'], detail_params[m]['epochs_per_eval'], detail_params[m]['lr_decay_factors'], detail_params[m]['decay_boundaries'], detail_params[m]['checkpoint_path'], detail_params[m]['checkpoint_exclude_scopes'], detail_params[m]['checkpoint_model_scope'], detail_params[m]['ignore_missing_vars'])

def convert_train(output_dir, val_per=0.015, all_splits=config.SPLITS, file_idx_start=0):
    class_hist = {'blouse': 0, 'dress': 0, 'outwear': 0, 'skirt': 0, 'trousers': 0}
    start_file_idx = {'blouse': 5, 'dress': 3, 'outwear': 4, 'skirt': 4, 'trousers': 4}
    for cat in config.CATEGORIES:
        total_examples = 0
        sys.stdout.write('\nprocessing category: {}...'.format(cat))
        sys.stdout.flush()
        file_idx = file_idx_start
        record_idx = 0
        tf_filename = os.path.join(output_dir, '%s_%04d.tfrecord' % (cat, file_idx))
        tfrecord_writer = tf.python_io.TFRecordWriter(tf_filename)
        tf_val_filename = os.path.join(output_dir, '%s_%04d_val.tfrecord' % (cat, 0))
        val_tfrecord_writer = tf.python_io.TFRecordWriter(tf_val_filename)
        this_key_map = keymap_factory[cat]
        for split in all_splits:
            if 'test' in split:
                continue
            sys.stdout.write('\nprocessing split: {}...\n'.format(split))
            sys.stdout.flush()
            split_path = os.path.join(config.DATA_DIR, split)
            anna_root = os.path.join(split_path, 'Annotations')
            anna_file = os.path.join(anna_root, os.listdir(anna_root)[0])
            anna_pd = pd.read_csv(anna_file)
            anna_pd = anna_pd.sample(frac=1, random_state=RANDOM_SEED).reset_index(drop=True)
            this_nums = len(anna_pd.index)
            total_examples += this_nums
            all_columns_name = list(anna_pd.columns)
            all_columns_name = sorted([s.strip() for s in all_columns_name[2:]])
            for index, row in anna_pd.iterrows():
                sys.stdout.write('\r>> Converting image %d/%d' % (index + 1, this_nums))
                sys.stdout.flush()
                category = row['image_category']
                if not cat in category:
                    continue
                class_hist[category] += 1
                image_file = row['image_id']
                full_file_path = os.path.join(split_path, image_file)
                class_id = config.category2ind[category]
                keypoint_x = []
                keypoint_y = []
                keypoint_v = []
                keypoint_id = []
                keypoint_global_id = []
                for keys in config.all_keys:
                    if keys in this_key_map:
                        keypoint_id.append(this_key_map[keys])
                    else:
                        keypoint_id.append(-1)
                    keypoint_global_id.append(config.key2ind[keys] - 1)
                    keypoint_info = row[keys].strip().split('_')
                    keypoint_x.append(int(keypoint_info[0]))
                    keypoint_y.append(int(keypoint_info[1]))
                    keypoint_v.append(int(keypoint_info[2]))
                if np.random.random_sample() > val_per:
                    _add_to_tfrecord(tfrecord_writer, full_file_path, image_file, class_id, keypoint_x, keypoint_y, keypoint_v, keypoint_id, keypoint_global_id)
                else:
                    _add_to_tfrecord(val_tfrecord_writer, full_file_path, image_file, class_id, keypoint_x, keypoint_y, keypoint_v, keypoint_id, keypoint_global_id)
                record_idx += 1
                if record_idx > SAMPLES_PER_FILES:
                    record_idx = 0
                    file_idx += 1
                    tf_filename = os.path.join(output_dir, '%s_%04d.tfrecord' % (cat, file_idx))
                    tfrecord_writer.flush()
                    tfrecord_writer.close()
                    tfrecord_writer = tf.python_io.TFRecordWriter(tf_filename)
        val_tfrecord_writer.flush()
        val_tfrecord_writer.close()
    print('\nFinished converting the whole dataset!')
    print(class_hist, total_examples)
    return (class_hist, total_examples)

def convert_test(output_dir, splits=config.SPLITS):
    class_hist = {'blouse': 0, 'dress': 0, 'outwear': 0, 'skirt': 0, 'trousers': 0}
    for cat in config.CATEGORIES:
        total_examples = 0
        sys.stdout.write('\nprocessing category: {}...'.format(cat))
        sys.stdout.flush()
        file_idx = 0
        record_idx = 0
        tf_filename = os.path.join(output_dir, '%s_%04d.tfrecord' % (cat, file_idx))
        tfrecord_writer = tf.python_io.TFRecordWriter(tf_filename)
        this_key_map = keymap_factory[cat]
        for split in splits:
            if 'train' in split:
                continue
            sys.stdout.write('\nprocessing split: {}...\n'.format(split))
            sys.stdout.flush()
            split_path = os.path.join(config.DATA_DIR, split)
            anna_file = os.path.join(split_path, 'test.csv')
            anna_pd = pd.read_csv(anna_file)
            this_nums = len(anna_pd.index)
            total_examples += this_nums
            for index, row in anna_pd.iterrows():
                sys.stdout.write('\r>> Converting image %d/%d' % (index + 1, this_nums))
                sys.stdout.flush()
                category = row['image_category']
                if not cat in category:
                    continue
                class_hist[category] += 1
                image_file = row['image_id']
                full_file_path = os.path.join(split_path, image_file)
                class_id = config.category2ind[category]
                _test_add_to_tfrecord(tfrecord_writer, full_file_path, image_file, class_id)
                record_idx += 1
                if record_idx > SAMPLES_PER_FILES:
                    record_idx = 0
                    file_idx += 1
                    tf_filename = os.path.join(output_dir, '%s_%04d.tfrecord' % (cat, file_idx))
                    tfrecord_writer.flush()
                    tfrecord_writer.close()
                    tfrecord_writer = tf.python_io.TFRecordWriter(tf_filename)
    print('\nFinished converting the whole test dataset!')
    print(class_hist, total_examples)
    return (class_hist, total_examples)

def parse_comma_list(args):
    return [float(s.strip()) for s in args.split(',')]

def mean_ensemble():
    all_test_items = {}
    for sub_file in ensemble_subs:
        sub_file_path = os.path.join(subs_dir, sub_file)
        df = pd.read_csv(sub_file_path, header=0)
        all_predict = df.values.tolist()
        for records in all_predict:
            file_id = records[0]
            preds = records[1:]
            if file_id in all_test_items:
                all_test_items[file_id].append(preds)
            else:
                all_test_items[file_id] = [preds]
    cur_record = 0
    df = pd.DataFrame(columns=['image_id', 'image_category'] + config.all_keys)
    num_keypoints_plus = len(config.all_keys) + 1
    for k, v in all_test_items.items():
        temp_list = []
        len_pred = len(v) * 1.0
        for pred_ind in range(1, num_keypoints_plus):
            pred_x, pred_y, pred_v = (0.0, 0.0, 1)
            if v[0][pred_ind].strip() == '-1_-1_-1':
                temp_list.append('-1_-1_-1')
                continue
            for _pred in v:
                _pred_x, _pred_y, _pred_v = _pred[pred_ind].strip().split('_')
                _pred_x, _pred_y, _pred_v = (float(_pred_x), float(_pred_y), int(_pred_v))
                pred_x = pred_x + _pred_x / len_pred
                pred_y = pred_y + _pred_y / len_pred
            temp_list.append('{}_{}_{}'.format(round(pred_x), round(pred_y), pred_v))
        df.loc[cur_record] = [k, v[0][0]] + temp_list
        cur_record = cur_record + 1
    df.sort_values('image_id').to_csv(os.path.join(subs_dir, 'ensmeble.csv'), encoding='utf-8', index=False)

def parse_comma_list(args):
    return [float(s.strip()) for s in args.split(',')]

def parse_comma_list(args):
    return [float(s.strip()) for s in args.split(',')]

def main(_):
    os.environ['TF_ENABLE_WINOGRAD_NONFUSED'] = '1'
    gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=FLAGS.gpu_memory_fraction)
    sess_config = tf.ConfigProto(allow_soft_placement=True, log_device_placement=False, intra_op_parallelism_threads=FLAGS.num_cpu_threads, inter_op_parallelism_threads=FLAGS.num_cpu_threads, gpu_options=gpu_options)
    run_config = tf.estimator.RunConfig().replace(save_checkpoints_secs=FLAGS.save_checkpoints_secs).replace(save_checkpoints_steps=None).replace(save_summary_steps=FLAGS.save_summary_steps).replace(keep_checkpoint_max=5).replace(tf_random_seed=FLAGS.tf_random_seed).replace(log_step_count_steps=FLAGS.log_every_n_steps).replace(session_config=sess_config)
    if FLAGS.seq_train:
        detail_params = {'all': {'model_dir': os.path.join(FLAGS.model_dir, 'all'), 'train_epochs': 6, 'epochs_per_eval': 4, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '3, 4', 'model_scope': 'all', 'checkpoint_path': None, 'checkpoint_model_scope': '', 'checkpoint_exclude_scopes': '', 'ignore_missing_vars': True}, 'blouse': {'model_dir': os.path.join(FLAGS.model_dir, 'blouse'), 'train_epochs': 50, 'epochs_per_eval': 30, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '15, 30', 'model_scope': 'blouse', 'checkpoint_path': os.path.join(FLAGS.model_dir, 'all'), 'checkpoint_model_scope': 'all', 'checkpoint_exclude_scopes': 'blouse/feature_pyramid/conv_heatmap, blouse/global_net/conv_heatmap', 'ignore_missing_vars': True}, 'dress': {'model_dir': os.path.join(FLAGS.model_dir, 'dress'), 'train_epochs': 50, 'epochs_per_eval': 30, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '15, 30', 'model_scope': 'dress', 'checkpoint_path': os.path.join(FLAGS.model_dir, 'all'), 'checkpoint_model_scope': 'all', 'checkpoint_exclude_scopes': 'dress/feature_pyramid/conv_heatmap, dress/global_net/conv_heatmap', 'ignore_missing_vars': True}, 'outwear': {'model_dir': os.path.join(FLAGS.model_dir, 'outwear'), 'train_epochs': 50, 'epochs_per_eval': 30, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '15, 30', 'model_scope': 'outwear', 'checkpoint_path': os.path.join(FLAGS.model_dir, 'all'), 'checkpoint_model_scope': 'all', 'checkpoint_exclude_scopes': 'outwear/feature_pyramid/conv_heatmap, outwear/global_net/conv_heatmap', 'ignore_missing_vars': True}, 'skirt': {'model_dir': os.path.join(FLAGS.model_dir, 'skirt'), 'train_epochs': 50, 'epochs_per_eval': 30, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '15, 30', 'model_scope': 'skirt', 'checkpoint_path': os.path.join(FLAGS.model_dir, 'all'), 'checkpoint_model_scope': 'all', 'checkpoint_exclude_scopes': 'skirt/feature_pyramid/conv_heatmap, skirt/global_net/conv_heatmap', 'ignore_missing_vars': True}, 'trousers': {'model_dir': os.path.join(FLAGS.model_dir, 'trousers'), 'train_epochs': 50, 'epochs_per_eval': 30, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '15, 30', 'model_scope': 'trousers', 'checkpoint_path': os.path.join(FLAGS.model_dir, 'all'), 'checkpoint_model_scope': 'all', 'checkpoint_exclude_scopes': 'trousers/feature_pyramid/conv_heatmap, trousers/global_net/conv_heatmap', 'ignore_missing_vars': True}}
    else:
        detail_params = {'blouse': {'model_dir': os.path.join(FLAGS.model_dir, 'blouse'), 'train_epochs': 28, 'epochs_per_eval': 7, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '10, 20', 'model_scope': 'blouse', 'checkpoint_path': os.path.join(FLAGS.data_dir, FLAGS.backbone) if FLAGS.run_on_cloud else os.path.join(FLAGS.checkpoint_path, FLAGS.backbone), 'checkpoint_model_scope': '', 'checkpoint_exclude_scopes': 'blouse/feature_pyramid, blouse/global_net', 'ignore_missing_vars': True}, 'dress': {'model_dir': os.path.join(FLAGS.model_dir, 'dress'), 'train_epochs': 28, 'epochs_per_eval': 7, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '10, 20', 'model_scope': 'dress', 'checkpoint_path': os.path.join(FLAGS.data_dir, FLAGS.backbone) if FLAGS.run_on_cloud else os.path.join(FLAGS.checkpoint_path, FLAGS.backbone), 'checkpoint_model_scope': '', 'checkpoint_exclude_scopes': 'dress/feature_pyramid, dress/global_net', 'ignore_missing_vars': True}, 'outwear': {'model_dir': os.path.join(FLAGS.model_dir, 'outwear'), 'train_epochs': 28, 'epochs_per_eval': 7, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '10, 20', 'model_scope': 'outwear', 'checkpoint_path': os.path.join(FLAGS.data_dir, FLAGS.backbone) if FLAGS.run_on_cloud else os.path.join(FLAGS.checkpoint_path, FLAGS.backbone), 'checkpoint_model_scope': '', 'checkpoint_exclude_scopes': 'outwear/feature_pyramid, outwear/global_net', 'ignore_missing_vars': True}, 'skirt': {'model_dir': os.path.join(FLAGS.model_dir, 'skirt'), 'train_epochs': 28, 'epochs_per_eval': 7, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '10, 20', 'model_scope': 'skirt', 'checkpoint_path': os.path.join(FLAGS.data_dir, FLAGS.backbone) if FLAGS.run_on_cloud else os.path.join(FLAGS.checkpoint_path, FLAGS.backbone), 'checkpoint_model_scope': '', 'checkpoint_exclude_scopes': 'skirt/feature_pyramid, skirt/global_net', 'ignore_missing_vars': True}, 'trousers': {'model_dir': os.path.join(FLAGS.model_dir, 'trousers'), 'train_epochs': 28, 'epochs_per_eval': 7, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '10, 20', 'model_scope': 'trousers', 'checkpoint_path': os.path.join(FLAGS.data_dir, FLAGS.backbone) if FLAGS.run_on_cloud else os.path.join(FLAGS.checkpoint_path, FLAGS.backbone), 'checkpoint_model_scope': '', 'checkpoint_exclude_scopes': 'trousers/feature_pyramid, trousers/global_net', 'ignore_missing_vars': True}}
    model_to_train = [s.strip() for s in FLAGS.model_to_train.split(',')]
    for m in model_to_train:
        sub_loop(keypoint_model_fn, m, detail_params[m]['model_dir'], run_config, detail_params[m]['train_epochs'], detail_params[m]['epochs_per_eval'], detail_params[m]['lr_decay_factors'], detail_params[m]['decay_boundaries'], detail_params[m]['checkpoint_path'], detail_params[m]['checkpoint_exclude_scopes'], detail_params[m]['checkpoint_model_scope'], detail_params[m]['ignore_missing_vars'])

def parse_comma_list(args):
    return [float(s.strip()) for s in args.split(',')]

def main(_):
    os.environ['TF_ENABLE_WINOGRAD_NONFUSED'] = '1'
    gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=FLAGS.gpu_memory_fraction)
    sess_config = tf.ConfigProto(allow_soft_placement=True, log_device_placement=False, intra_op_parallelism_threads=FLAGS.num_cpu_threads, inter_op_parallelism_threads=FLAGS.num_cpu_threads, gpu_options=gpu_options)
    run_config = tf.estimator.RunConfig().replace(save_checkpoints_secs=None).replace(save_checkpoints_steps=None).replace(save_summary_steps=FLAGS.save_summary_steps).replace(keep_checkpoint_max=5).replace(tf_random_seed=FLAGS.tf_random_seed).replace(log_step_count_steps=FLAGS.log_every_n_steps).replace(session_config=sess_config)
    model_to_eval = [s.strip() for s in FLAGS.model_to_eval.split(',')]
    for m in model_to_eval:
        if m == '':
            continue
        pred_results = eval_each(keypoint_model_fn, os.path.join(FLAGS.model_dir, m), m, run_config)
        df = pd.DataFrame(columns=['image_id', 'image_category'] + config.all_keys)
        cur_record = 0
        gloabl2local_ind = dict(zip(config.class2global_ind_map[m], list(range(len(config.class2global_ind_map[m])))))
        for pred_item in pred_results:
            temp_list = []
            index = 0
            x = pred_item['pred_x'].tolist()
            y = pred_item['pred_y'].tolist()
            filename = pred_item['file_name'].decode('utf8')
            for ind in list(range(config.class_num_joints['*'])):
                if ind in gloabl2local_ind:
                    temp_list.append('{}_{}_1'.format(round(x[gloabl2local_ind[ind]]), round(y[gloabl2local_ind[ind]])))
                else:
                    temp_list.append('-1_-1_-1')
            df.loc[cur_record] = [filename, m] + temp_list
            cur_record = cur_record + 1
        df.to_csv('./{}.csv'.format(m), encoding='utf-8', index=False)
    df_list = [pd.read_csv('./{}.csv'.format(model_to_eval[0]), encoding='utf-8')]
    for m in model_to_eval[1:]:
        if m == '':
            continue
        df_list.append(pd.read_csv('./{}.csv'.format(m), encoding='utf-8'))
    pd.concat(df_list, ignore_index=True).to_csv('./sub.csv', encoding='utf-8', index=False)
    if FLAGS.run_on_cloud:
        tf.gfile.Copy('./sub.csv', os.path.join(FLAGS.model_dir, 'sub.csv'), overwrite=True)

def parse_comma_list(args):
    return [float(s.strip()) for s in args.split(',')]

def main(_):
    os.environ['TF_ENABLE_WINOGRAD_NONFUSED'] = '1'
    gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=FLAGS.gpu_memory_fraction)
    sess_config = tf.ConfigProto(allow_soft_placement=True, log_device_placement=False, intra_op_parallelism_threads=FLAGS.num_cpu_threads, inter_op_parallelism_threads=FLAGS.num_cpu_threads, gpu_options=gpu_options)
    run_config = tf.estimator.RunConfig().replace(save_checkpoints_secs=FLAGS.save_checkpoints_secs).replace(save_checkpoints_steps=None).replace(save_summary_steps=FLAGS.save_summary_steps).replace(keep_checkpoint_max=5).replace(tf_random_seed=FLAGS.tf_random_seed).replace(log_step_count_steps=FLAGS.log_every_n_steps).replace(session_config=sess_config)
    full_model_dir = os.path.join(FLAGS.model_dir, all_models[FLAGS.backbone.strip()]['logs_sub_dir'])
    checkpoint_model_dir = os.path.join(FLAGS.model_dir, all_models[FLAGS.backbone.strip()]['checkpoint_root'])
    detail_params = {'blouse': {'model_dir': os.path.join(full_model_dir, 'blouse'), 'train_epochs': FLAGS.train_epochs, 'model_scope': 'blouse', 'high_learning_rate': FLAGS.high_learning_rate, 'low_learning_rate': FLAGS.low_learning_rate, 'checkpoint_path': os.path.join(checkpoint_model_dir, 'blouse')}, 'dress': {'model_dir': os.path.join(full_model_dir, 'dress'), 'train_epochs': FLAGS.train_epochs, 'model_scope': 'dress', 'high_learning_rate': FLAGS.high_learning_rate, 'low_learning_rate': FLAGS.low_learning_rate, 'checkpoint_path': os.path.join(checkpoint_model_dir, 'dress')}, 'outwear': {'model_dir': os.path.join(full_model_dir, 'outwear'), 'train_epochs': FLAGS.train_epochs, 'model_scope': 'outwear', 'high_learning_rate': FLAGS.high_learning_rate, 'low_learning_rate': FLAGS.low_learning_rate, 'checkpoint_path': os.path.join(checkpoint_model_dir, 'outwear')}, 'skirt': {'model_dir': os.path.join(full_model_dir, 'skirt'), 'train_epochs': FLAGS.train_epochs, 'model_scope': 'skirt', 'high_learning_rate': FLAGS.high_learning_rate, 'low_learning_rate': FLAGS.low_learning_rate, 'checkpoint_path': os.path.join(checkpoint_model_dir, 'skirt')}, 'trousers': {'model_dir': os.path.join(full_model_dir, 'trousers'), 'train_epochs': FLAGS.train_epochs, 'high_learning_rate': FLAGS.high_learning_rate, 'low_learning_rate': FLAGS.low_learning_rate, 'model_scope': 'trousers', 'checkpoint_path': os.path.join(checkpoint_model_dir, 'trousers')}}
    model_to_train = [s.strip() for s in FLAGS.model_to_train.split(',')]
    for m in model_to_train:
        sub_loop(keypoint_model_fn, m, detail_params[m]['model_dir'], run_config, detail_params[m]['train_epochs'], detail_params[m]['high_learning_rate'], detail_params[m]['low_learning_rate'], detail_params[m]['checkpoint_path'])

def parse_comma_list(args):
    return [float(s.strip()) for s in args.split(',')]

def main(_):
    os.environ['TF_ENABLE_WINOGRAD_NONFUSED'] = '1'
    gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=FLAGS.gpu_memory_fraction)
    sess_config = tf.ConfigProto(allow_soft_placement=True, log_device_placement=False, intra_op_parallelism_threads=FLAGS.num_cpu_threads, inter_op_parallelism_threads=FLAGS.num_cpu_threads, gpu_options=gpu_options)
    run_config = tf.estimator.RunConfig().replace(save_checkpoints_secs=None).replace(save_checkpoints_steps=FLAGS.save_checkpoints_steps).replace(save_summary_steps=FLAGS.save_summary_steps).replace(keep_checkpoint_max=5).replace(tf_random_seed=FLAGS.tf_random_seed).replace(log_step_count_steps=FLAGS.log_every_n_steps).replace(session_config=sess_config)
    num_gpus = validate_batch_size_for_multi_gpu(FLAGS.batch_size)
    full_model_dir = FLAGS.model_dir if FLAGS.run_on_cloud else FLAGS.model_dir
    detail_params = {'blouse': {'model_dir': os.path.join(full_model_dir, 'blouse'), 'train_epochs': 30, 'epochs_per_eval': 30, 'lr_decay_factors': '1, 0.5, 0.1, 0.01', 'decay_boundaries': '15, 20, 28', 'model_scope': 'blouse', 'checkpoint_path': os.path.join(FLAGS.data_dir, FLAGS.cloud_checkpoint_path) if FLAGS.run_on_cloud else FLAGS.checkpoint_path, 'checkpoint_model_scope': '', 'checkpoint_exclude_scopes': 'blouse/additional_layer', 'ignore_missing_vars': True}, 'dress': {'model_dir': os.path.join(full_model_dir, 'dress'), 'train_epochs': 30, 'epochs_per_eval': 30, 'lr_decay_factors': '1, 0.5, 0.1, 0.01', 'decay_boundaries': '15, 20, 28', 'model_scope': 'dress', 'checkpoint_path': os.path.join(FLAGS.data_dir, FLAGS.cloud_checkpoint_path) if FLAGS.run_on_cloud else FLAGS.checkpoint_path, 'checkpoint_model_scope': '', 'checkpoint_exclude_scopes': 'dress/additional_layer', 'ignore_missing_vars': True}, 'outwear': {'model_dir': os.path.join(full_model_dir, 'outwear'), 'train_epochs': 30, 'epochs_per_eval': 30, 'lr_decay_factors': '1, 0.5, 0.1, 0.01', 'decay_boundaries': '15, 20, 28', 'model_scope': 'outwear', 'checkpoint_path': os.path.join(FLAGS.data_dir, FLAGS.cloud_checkpoint_path) if FLAGS.run_on_cloud else FLAGS.checkpoint_path, 'checkpoint_model_scope': '', 'checkpoint_exclude_scopes': 'outwear/additional_layer', 'ignore_missing_vars': True}, 'skirt': {'model_dir': os.path.join(full_model_dir, 'skirt'), 'train_epochs': 30, 'epochs_per_eval': 30, 'lr_decay_factors': '1, 0.5, 0.1, 0.01', 'decay_boundaries': '15, 20, 28', 'model_scope': 'skirt', 'checkpoint_path': os.path.join(FLAGS.data_dir, FLAGS.cloud_checkpoint_path) if FLAGS.run_on_cloud else FLAGS.checkpoint_path, 'checkpoint_model_scope': '', 'checkpoint_exclude_scopes': 'skirt/additional_layer', 'ignore_missing_vars': True}, 'trousers': {'model_dir': os.path.join(full_model_dir, 'trousers'), 'train_epochs': 30, 'epochs_per_eval': 30, 'lr_decay_factors': '1, 0.5, 0.1, 0.01', 'decay_boundaries': '15, 20, 28', 'model_scope': 'trousers', 'checkpoint_path': os.path.join(FLAGS.data_dir, FLAGS.cloud_checkpoint_path) if FLAGS.run_on_cloud else FLAGS.checkpoint_path, 'checkpoint_model_scope': '', 'checkpoint_exclude_scopes': 'trousers/additional_layer', 'ignore_missing_vars': True}}
    model_to_train = [s.strip() for s in FLAGS.model_to_train.split(',')]
    for m in model_to_train:
        sub_loop(keypoint_model_fn, m, detail_params[m]['model_dir'], run_config, detail_params[m]['train_epochs'], detail_params[m]['epochs_per_eval'], detail_params[m]['lr_decay_factors'], detail_params[m]['decay_boundaries'], detail_params[m]['checkpoint_path'], detail_params[m]['checkpoint_exclude_scopes'], detail_params[m]['checkpoint_model_scope'], detail_params[m]['ignore_missing_vars'])

def print_tensors_in_checkpoint_file(file_name, tensor_name, all_tensors):
    try:
        reader = pywrap_tensorflow.NewCheckpointReader(file_name)
        if all_tensors:
            var_to_shape_map = reader.get_variable_to_shape_map()
            for key in var_to_shape_map:
                print('tensor_name: ', key)
                print(reader.get_tensor(key))
        elif not tensor_name:
            print(reader.debug_string().decode('utf-8'))
        else:
            print('tensor_name: ', tensor_name)
            print(reader.get_tensor(tensor_name))
    except Exception as e:
        print(str(e))
        if 'corrupted compressed block contents' in str(e):
            print("It's likely that your checkpoint file has been compressed with SNAPPY.")

def print_all_tensors_name(file_name):
    try:
        reader = pywrap_tensorflow.NewCheckpointReader(file_name)
        var_to_shape_map = reader.get_variable_to_shape_map()
        for key in var_to_shape_map:
            print(key)
    except Exception as e:
        print(str(e))
        if 'corrupted compressed block contents' in str(e):
            print("It's likely that your checkpoint file has been compressed with SNAPPY.")

def parse_comma_list(args):
    return [float(s.strip()) for s in args.split(',')]

def main(_):
    os.environ['TF_ENABLE_WINOGRAD_NONFUSED'] = '1'
    gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=FLAGS.gpu_memory_fraction)
    sess_config = tf.ConfigProto(allow_soft_placement=True, log_device_placement=False, intra_op_parallelism_threads=FLAGS.num_cpu_threads, inter_op_parallelism_threads=FLAGS.num_cpu_threads, gpu_options=gpu_options)
    run_config = tf.estimator.RunConfig().replace(save_checkpoints_secs=None).replace(save_checkpoints_steps=None).replace(save_summary_steps=FLAGS.save_summary_steps).replace(keep_checkpoint_max=5).replace(tf_random_seed=FLAGS.tf_random_seed).replace(log_step_count_steps=FLAGS.log_every_n_steps).replace(session_config=sess_config)
    model_to_eval = [s.strip() for s in FLAGS.model_to_eval.split(',')]
    full_model_dir = os.path.join(FLAGS.model_dir, all_models[FLAGS.backbone.strip()]['logs_sub_dir'])
    for m in model_to_eval:
        if m == '':
            continue
        pred_results = eval_each(keypoint_model_fn, os.path.join(full_model_dir, m), m, run_config)
        df = pd.DataFrame(columns=['image_id', 'image_category'] + config.all_keys)
        cur_record = 0
        gloabl2local_ind = dict(zip(config.class2global_ind_map[m], list(range(len(config.class2global_ind_map[m])))))
        for pred_item in pred_results:
            temp_list = []
            index = 0
            x = pred_item['pred_x'].tolist()
            y = pred_item['pred_y'].tolist()
            filename = pred_item['file_name'].decode('utf8')
            for ind in list(range(config.class_num_joints['*'])):
                if ind in gloabl2local_ind:
                    temp_list.append('{}_{}_1'.format(round(x[gloabl2local_ind[ind]]), round(y[gloabl2local_ind[ind]])))
                else:
                    temp_list.append('-1_-1_-1')
            df.loc[cur_record] = [filename, m] + temp_list
            cur_record = cur_record + 1
        df.to_csv('./{}_{}.csv'.format(FLAGS.backbone.strip(), m), encoding='utf-8', index=False)
    df_list = [pd.read_csv('./{}_{}.csv'.format(FLAGS.backbone.strip(), model_to_eval[0]), encoding='utf-8')]
    for m in model_to_eval[1:]:
        if m == '':
            continue
        df_list.append(pd.read_csv('./{}_{}.csv'.format(FLAGS.backbone.strip(), m), encoding='utf-8'))
    pd.concat(df_list, ignore_index=True).to_csv('./{}_sub.csv'.format(FLAGS.backbone.strip()), encoding='utf-8', index=False)
    if FLAGS.run_on_cloud:
        tf.gfile.Copy('./{}_sub.csv'.format(FLAGS.backbone.strip()), os.path.join(full_model_dir, '{}_sub.csv'.format(FLAGS.backbone.strip())), overwrite=True)

def run():
    if args.prediction.strip() == '' or args.gt.strip() == '':
        parser.error('Must specify the file path of the prediction and ground truth.')
    pred_df = pd.read_csv(args.prediction, encoding='utf-8')
    gt_df = pd.read_csv(args.gt, encoding='utf-8').set_index('image_id')
    num_v = 0.0
    sum_dist = 0.0
    for index, row in pred_df.iterrows():
        gt = gt_df.loc[row['image_id']]
        img_cat = gt['image_category']
        gt_points = {}
        pred_points = {}
        for kp in cfg.all_keys:
            pred_kp = row[kp].strip().split('_')
            gt_kp = gt[kp].strip().split('_')
            pred_points[kp] = [int(_) for _ in pred_kp]
            gt_points[kp] = [int(_) for _ in gt_kp]
        lnorm_name, rnorm_name = cfg.normalize_point_name[img_cat]
        lnorm, rnorm = (gt_points[lnorm_name][:-1], gt_points[rnorm_name][:-1])
        norm_value = math.pow(math.pow(lnorm[0] - rnorm[0], 2.0) + math.pow(lnorm[1] - rnorm[1], 2.0), 0.5)
        for kp in cfg.all_keys:
            if gt_points[kp][-1] == -1 or norm_value < 0.001:
                continue
            num_v += 1.0
            dist = math.pow(math.pow(pred_points[kp][0] - gt_points[kp][0], 2.0) + math.pow(pred_points[kp][1] - gt_points[kp][1], 2.0), 0.5)
            sum_dist += dist / norm_value
    sum_dist = sum_dist / num_v
    print(sum_dist)

def run_by_cat():
    if args.prediction.strip() == '' or args.gt.strip() == '':
        parser.error('Must specify the file path of the prediction and ground truth.')
    pred_df = pd.read_csv(args.prediction, encoding='utf-8')
    gt_df = pd.read_csv(args.gt, encoding='utf-8').set_index('image_id')
    for cat_ in cfg.CATEGORIES:
        num_v = 0.0
        sum_dist = 0.0
        for index, row in pred_df.iterrows():
            gt = gt_df.loc[row['image_id']]
            img_cat = gt['image_category']
            if cat_ not in img_cat:
                continue
            gt_points = {}
            pred_points = {}
            for kp in cfg.all_keys:
                pred_kp = row[kp].strip().split('_')
                gt_kp = gt[kp].strip().split('_')
                pred_points[kp] = [int(_) for _ in pred_kp]
                gt_points[kp] = [int(_) for _ in gt_kp]
            lnorm_name, rnorm_name = cfg.normalize_point_name[img_cat]
            lnorm, rnorm = (gt_points[lnorm_name][:-1], gt_points[rnorm_name][:-1])
            norm_value = math.pow(math.pow(lnorm[0] - rnorm[0], 2.0) + math.pow(lnorm[1] - rnorm[1], 2.0), 0.5)
            for kp in cfg.all_keys:
                if gt_points[kp][-1] == -1 or norm_value < 0.001:
                    continue
                num_v += 1.0
                dist = math.pow(math.pow(pred_points[kp][0] - gt_points[kp][0], 2.0) + math.pow(pred_points[kp][1] - gt_points[kp][1], 2.0), 0.5)
                sum_dist += dist / norm_value
        sum_dist = sum_dist / num_v
        print('{}:'.format(cat_), sum_dist)

def parse_comma_list(args):
    return [float(s.strip()) for s in args.split(',')]

def main(_):
    os.environ['TF_ENABLE_WINOGRAD_NONFUSED'] = '1'
    gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=FLAGS.gpu_memory_fraction)
    sess_config = tf.ConfigProto(allow_soft_placement=True, log_device_placement=False, intra_op_parallelism_threads=FLAGS.num_cpu_threads, inter_op_parallelism_threads=FLAGS.num_cpu_threads, gpu_options=gpu_options)
    run_config = tf.estimator.RunConfig().replace(save_checkpoints_secs=None).replace(save_checkpoints_steps=FLAGS.save_checkpoints_steps).replace(save_summary_steps=FLAGS.save_summary_steps).replace(keep_checkpoint_max=5).replace(tf_random_seed=FLAGS.tf_random_seed).replace(log_step_count_steps=FLAGS.log_every_n_steps).replace(session_config=sess_config)
    num_gpus = validate_batch_size_for_multi_gpu(FLAGS.batch_size)
    full_model_dir = FLAGS.model_dir if FLAGS.run_on_cloud else FLAGS.model_dir.format(FLAGS.backbone.strip())
    detail_params = {'blouse': {'model_dir': os.path.join(full_model_dir, 'blouse'), 'train_epochs': 25, 'epochs_per_eval': 5, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '15, 20', 'model_scope': 'blouse', 'checkpoint_path': os.path.join(FLAGS.data_dir, FLAGS.cloud_checkpoint_path.format(FLAGS.net_depth)) if FLAGS.run_on_cloud else FLAGS.checkpoint_path.format(FLAGS.net_depth), 'checkpoint_model_scope': '', 'checkpoint_exclude_scopes': 'blouse/additional_layer, blouse/feature_pyramid, blouse/global_net', 'ignore_missing_vars': True}, 'dress': {'model_dir': os.path.join(full_model_dir, 'dress'), 'train_epochs': 25, 'epochs_per_eval': 5, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '15, 20', 'model_scope': 'dress', 'checkpoint_path': os.path.join(FLAGS.data_dir, FLAGS.cloud_checkpoint_path.format(FLAGS.net_depth)) if FLAGS.run_on_cloud else FLAGS.checkpoint_path.format(FLAGS.net_depth), 'checkpoint_model_scope': '', 'checkpoint_exclude_scopes': 'dress/additional_layer, dress/feature_pyramid, dress/global_net', 'ignore_missing_vars': True}, 'outwear': {'model_dir': os.path.join(full_model_dir, 'outwear'), 'train_epochs': 25, 'epochs_per_eval': 5, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '15, 20', 'model_scope': 'outwear', 'checkpoint_path': os.path.join(FLAGS.data_dir, FLAGS.cloud_checkpoint_path.format(FLAGS.net_depth)) if FLAGS.run_on_cloud else FLAGS.checkpoint_path.format(FLAGS.net_depth), 'checkpoint_model_scope': '', 'checkpoint_exclude_scopes': 'outwear/additional_layer, outwear/feature_pyramid, outwear/global_net', 'ignore_missing_vars': True}, 'skirt': {'model_dir': os.path.join(full_model_dir, 'skirt'), 'train_epochs': 25, 'epochs_per_eval': 5, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '15, 20', 'model_scope': 'skirt', 'checkpoint_path': os.path.join(FLAGS.data_dir, FLAGS.cloud_checkpoint_path.format(FLAGS.net_depth)) if FLAGS.run_on_cloud else FLAGS.checkpoint_path.format(FLAGS.net_depth), 'checkpoint_model_scope': '', 'checkpoint_exclude_scopes': 'skirt/additional_layer, skirt/feature_pyramid, skirt/global_net', 'ignore_missing_vars': True}, 'trousers': {'model_dir': os.path.join(full_model_dir, 'trousers'), 'train_epochs': 25, 'epochs_per_eval': 5, 'lr_decay_factors': '1, 0.5, 0.1', 'decay_boundaries': '15, 20', 'model_scope': 'trousers', 'checkpoint_path': os.path.join(FLAGS.data_dir, FLAGS.cloud_checkpoint_path.format(FLAGS.net_depth)) if FLAGS.run_on_cloud else FLAGS.checkpoint_path.format(FLAGS.net_depth), 'checkpoint_model_scope': '', 'checkpoint_exclude_scopes': 'trousers/additional_layer, trousers/feature_pyramid, trousers/global_net', 'ignore_missing_vars': True}}
    model_to_train = [s.strip() for s in FLAGS.model_to_train.split(',')]
    for m in model_to_train:
        sub_loop(keypoint_model_fn, m, detail_params[m]['model_dir'], run_config, detail_params[m]['train_epochs'], detail_params[m]['epochs_per_eval'], detail_params[m]['lr_decay_factors'], detail_params[m]['decay_boundaries'], detail_params[m]['checkpoint_path'], detail_params[m]['checkpoint_exclude_scopes'], detail_params[m]['checkpoint_model_scope'], detail_params[m]['ignore_missing_vars'])

