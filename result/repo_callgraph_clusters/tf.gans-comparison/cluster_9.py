# Cluster 9

def num_examples_from_tfrecords(tfrecords_list):
    num_examples = 0
    for path in tfrecords_list:
        num_examples += sum((1 for _ in tf.python_io.tf_record_iterator(path)))
    return num_examples

