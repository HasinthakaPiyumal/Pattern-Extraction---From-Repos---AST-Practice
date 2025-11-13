# Cluster 14

def input_pipeline(model_scope=FLAGS.model_scope):
    preprocessing_fn = lambda org_image, file_name, shape: preprocessing.preprocess_for_test_raw_output(org_image, file_name, shape, FLAGS.train_image_size, FLAGS.train_image_size, data_format='NCHW' if FLAGS.data_format == 'channels_first' else 'NHWC', bbox_border=FLAGS.bbox_border, heatmap_sigma=FLAGS.heatmap_sigma, heatmap_size=FLAGS.heatmap_size)
    images, shape, file_name, classid, offsets = dataset.slim_test_get_split(FLAGS.data_dir, None, FLAGS.num_readers, FLAGS.num_preprocessing_threads, file_pattern=FLAGS.dataset_name, category=model_scope if 'all' not in model_scope else '*', reader=None, dynamic_pad=True)
    return {'images': images, 'shape': shape, 'classid': classid, 'file_name': file_name, 'pred_offsets': offsets}

def input_pipeline(model_scope=FLAGS.model_scope):
    preprocessing_fn = lambda org_image, file_name, shape: preprocessing.preprocess_for_test_raw_output(org_image, file_name, shape, FLAGS.train_image_size, FLAGS.train_image_size, data_format='NCHW' if FLAGS.data_format == 'channels_first' else 'NHWC', bbox_border=FLAGS.bbox_border, heatmap_sigma=FLAGS.heatmap_sigma, heatmap_size=FLAGS.heatmap_size)
    images, shape, file_name, classid, offsets = dataset.slim_test_get_split(FLAGS.data_dir, None, FLAGS.num_readers, FLAGS.num_preprocessing_threads, file_pattern=FLAGS.dataset_name, category=model_scope if 'all' not in model_scope else '*', reader=None, dynamic_pad=True)
    return {'images': images, 'shape': shape, 'classid': classid, 'file_name': file_name, 'pred_offsets': offsets}

def input_pipeline(model_scope=FLAGS.model_scope):
    preprocessing_fn = lambda org_image, file_name, shape: preprocessing.preprocess_for_test_raw_output(org_image, file_name, shape, FLAGS.train_image_size, FLAGS.train_image_size, data_format='NCHW' if FLAGS.data_format == 'channels_first' else 'NHWC', bbox_border=FLAGS.bbox_border, heatmap_sigma=FLAGS.heatmap_sigma, heatmap_size=FLAGS.heatmap_size)
    images, shape, file_name, classid, offsets = dataset.slim_test_get_split(FLAGS.data_dir, None, FLAGS.num_readers, FLAGS.num_preprocessing_threads, file_pattern=FLAGS.dataset_name, category=model_scope if 'all' not in model_scope else '*', reader=None, dynamic_pad=True)
    return {'images': images, 'shape': shape, 'classid': classid, 'file_name': file_name, 'pred_offsets': offsets}

