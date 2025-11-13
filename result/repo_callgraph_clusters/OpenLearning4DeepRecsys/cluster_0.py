# Cluster 0

class movie_lens_data_repos:

    def __init__(self, file):
        with codecs.open(file, 'rb') as f:
            train, validate, test, user_content, item_content = pickle.load(f)
        train = train.reindex(np.random.permutation(train.index))
        self.training_ratings_user = train.loc[:, 'user']
        self.training_ratings_item = train.loc[:, 'item']
        self.training_ratings_score = train.loc[:, 'rate']
        self.test_ratings_user = validate.loc[:, 'user']
        self.test_ratings_item = validate.loc[:, 'item']
        self.test_ratings_score = validate.loc[:, 'rate']
        self.eval_ratings_user = test.loc[:, 'user']
        self.eval_ratings_item = test.loc[:, 'item']
        self.eval_ratings_score = test.loc[:, 'rate']
        self.n_user = max([self.training_ratings_user.max(), self.test_ratings_user.max(), self.eval_ratings_user.max()]) + 1
        self.n_item = max([self.training_ratings_item.max(), self.test_ratings_item.max(), self.eval_ratings_item.max()]) + 1
        self.n_user_attr, self.n_item_attr = (user_content.shape[1], item_content.shape[1])
        print('n_user=%d n_item=%d n_user_attr=%d n_item_attr=%d' % (self.n_user, self.n_item, self.n_user_attr, self.n_item_attr))
        self.user_attr = self.BuildAttributeFromSPMatrix(user_content, self.n_user, self.n_user_attr)
        self.item_attr = self.BuildAttributeFromSPMatrix(item_content, self.n_item, self.n_item_attr)

    def BuildAttributeFromSPMatrix(self, sp_matrix, n, m):
        res = []
        for _ in range(n):
            res.append([])
        row, col, value = find(sp_matrix)
        for r, c, v in zip(row, col, value):
            res[r].append([c, float(v)])
        return res

def __init__(self, file):
    with codecs.open(file, 'rb') as f:
        train, validate, test, user_content, item_content = pickle.load(f)
    train = train.reindex(np.random.permutation(train.index))
    self.training_ratings_user = train.loc[:, 'user']
    self.training_ratings_item = train.loc[:, 'item']
    self.training_ratings_score = train.loc[:, 'rate']
    self.test_ratings_user = validate.loc[:, 'user']
    self.test_ratings_item = validate.loc[:, 'item']
    self.test_ratings_score = validate.loc[:, 'rate']
    self.eval_ratings_user = test.loc[:, 'user']
    self.eval_ratings_item = test.loc[:, 'item']
    self.eval_ratings_score = test.loc[:, 'rate']
    self.n_user = max([self.training_ratings_user.max(), self.test_ratings_user.max(), self.eval_ratings_user.max()]) + 1
    self.n_item = max([self.training_ratings_item.max(), self.test_ratings_item.max(), self.eval_ratings_item.max()]) + 1
    self.n_user_attr, self.n_item_attr = (user_content.shape[1], item_content.shape[1])
    print('n_user=%d n_item=%d n_user_attr=%d n_item_attr=%d' % (self.n_user, self.n_item, self.n_user_attr, self.n_item_attr))
    self.user_attr = self.BuildAttributeFromSPMatrix(user_content, self.n_user, self.n_user_attr)
    self.item_attr = self.BuildAttributeFromSPMatrix(item_content, self.n_item, self.n_item_attr)

def load_data_cache(filename):
    with open(filename, 'rb') as f:
        while True:
            try:
                yield pickle.load(f)
            except EOFError:
                break

def load_data_cache(filename):
    with open(filename, 'rb') as f:
        while True:
            try:
                yield pickle.load(f)
            except EOFError:
                break

