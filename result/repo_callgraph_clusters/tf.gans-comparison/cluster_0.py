# Cluster 0

def _bytes_features(value):
    return tf.train.Feature(bytes_list=tf.train.BytesList(value=value))

def _int64_features(value):
    return tf.train.Feature(int64_list=tf.train.Int64List(value=value))

