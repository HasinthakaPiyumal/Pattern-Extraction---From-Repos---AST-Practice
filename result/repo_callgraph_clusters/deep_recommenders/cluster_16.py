# Cluster 16

class MovieLens(object):

    def __init__(self, filename='movielens.tfrecords'):
        self._filename = os.path.join(os.path.dirname(__file__), filename)
        self._columns = ['UserID', 'MovieID', 'Rating', 'Timestamp', 'Gender', 'Age', 'Occupation', 'Zip-code', 'Title', 'Genres']
        self.num_ratings = 1000209
        self.num_users = 6040
        self.num_movies = 3952
        self.gender_vocab = ['F', 'M']
        self.age_vocab = [1, 18, 25, 35, 45, 50, 56]
        self.occupation_vocab = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
        self.genres_vocab = ['Action', 'Adventure', 'Animation', "Children's", 'Comedy', 'Crime', 'Documentary', 'Drama', 'Fantasy', 'Film-Noir', 'Horror', 'Musical', 'Mystery', 'Romance', 'Sci-Fi', 'Thriller', 'War', 'Western']

    def dataset(self, epochs=1, batch_size=256):

        def _parse_example(serialized_example):
            features = {}
            for c in ['Age', 'Occupation', 'Rating', 'Timestamp']:
                features[c] = tf.io.FixedLenFeature([], tf.int64)
            for c in ['UserID', 'MovieID', 'Gender', 'Zip-code', 'Title']:
                features[c] = tf.io.FixedLenFeature([], tf.string)
            features['Genres'] = tf.io.VarLenFeature(tf.string)
            example = tf.io.parse_example(serialized_example, features)
            ratings = example.pop('Rating')
            return (example, ratings)
        ds = tf.data.TFRecordDataset(self._filename)
        ds = ds.repeat(epochs)
        ds = ds.batch(batch_size)
        ds = ds.map(_parse_example, num_parallel_calls=-1)
        return ds

def _parse_example(serialized_example):
    features = {}
    for c in ['Age', 'Occupation', 'Rating', 'Timestamp']:
        features[c] = tf.io.FixedLenFeature([], tf.int64)
    for c in ['UserID', 'MovieID', 'Gender', 'Zip-code', 'Title']:
        features[c] = tf.io.FixedLenFeature([], tf.string)
    features['Genres'] = tf.io.VarLenFeature(tf.string)
    example = tf.io.parse_example(serialized_example, features)
    ratings = example.pop('Rating')
    return (example, ratings)

