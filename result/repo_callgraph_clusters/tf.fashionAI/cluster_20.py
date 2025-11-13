# Cluster 20

def _convert_to_example(image_data, shape, image_file, class_id, keypoint_x, keypoint_y, keypoint_v, keypoint_id, keypoint_global_id):
    image_format = b'JPEG'
    example = tf.train.Example(features=tf.train.Features(feature={'image/height': int64_feature(shape[0]), 'image/width': int64_feature(shape[1]), 'image/channels': int64_feature(shape[2]), 'image/classid': int64_feature(class_id), 'image/keypoint/x': int64_feature(keypoint_x), 'image/keypoint/y': int64_feature(keypoint_y), 'image/keypoint/v': int64_feature(keypoint_v), 'image/keypoint/id': int64_feature(keypoint_id), 'image/keypoint/gid': int64_feature(keypoint_global_id), 'image/format': bytes_feature(image_format), 'image/filename': bytes_feature(image_file.encode('utf8')), 'image/encoded': bytes_feature(image_data)}))
    return example

def _add_to_tfrecord(tfrecord_writer, image_path, image_file, class_id, keypoint_x, keypoint_y, keypoint_v, keypoint_id, keypoint_global_id):
    image_data, shape = _process_image(image_path)
    example = _convert_to_example(image_data, shape, image_file, class_id, keypoint_x, keypoint_y, keypoint_v, keypoint_id, keypoint_global_id)
    tfrecord_writer.write(example.SerializeToString())

def _test_add_to_tfrecord(tfrecord_writer, image_path, image_file, class_id):
    image_data, shape = _process_image(image_path)
    image_format = b'JPEG'
    example = tf.train.Example(features=tf.train.Features(feature={'image/height': int64_feature(shape[0]), 'image/width': int64_feature(shape[1]), 'image/channels': int64_feature(shape[2]), 'image/classid': int64_feature(class_id), 'image/format': bytes_feature(image_format), 'image/filename': bytes_feature(image_file.encode('utf8')), 'image/encoded': bytes_feature(image_data)}))
    tfrecord_writer.write(example.SerializeToString())

