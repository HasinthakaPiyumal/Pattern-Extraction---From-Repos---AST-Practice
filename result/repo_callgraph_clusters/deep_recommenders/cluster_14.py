# Cluster 14

def _serialize_example(feature):
    serialize_feature = {}
    for c in ['Age', 'Occupation', 'Rating', 'Timestamp']:
        serialize_feature[c] = tf.train.Feature(int64_list=tf.train.Int64List(value=[feature[c]]))
    for c in ['UserID', 'MovieID', 'Gender', 'Zip-code', 'Title']:
        serialize_feature[c] = tf.train.Feature(bytes_list=tf.train.BytesList(value=[feature[c]]))
    serialize_feature['Genres'] = tf.train.Feature(bytes_list=tf.train.BytesList(value=feature['Genres']))
    example_proto = tf.train.Example(features=tf.train.Features(feature=serialize_feature))
    return example_proto.SerializeToString()

