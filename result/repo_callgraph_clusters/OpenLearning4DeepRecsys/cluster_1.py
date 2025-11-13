# Cluster 1

class sparse_data_repos:

    def __init__(self, n_user, n_item, n_user_attr=0, n_item_attr=0):
        self.n_user = n_user
        self.n_item = n_item
        self.n_user_attr = n_user_attr
        self.n_item_attr = n_item_attr
        self.user_attr = []
        self.item_attr = []
        self.training_ratings_user = []
        self.training_ratings_item = []
        self.training_ratings_item02 = []
        self.training_ratings_score = []
        self.test_ratings_user = []
        self.test_ratings_item = []
        self.test_ratings_item02 = []
        self.test_ratings_score = []
        self.eval_ratings_user = []
        self.eval_ratings_item = []
        self.eval_ratings_score = []

    def load_user_attributes(self, infile, spliter='\t'):
        self.load_attributes(self.user_attr, self.n_user, self.n_user_attr, infile, spliter)

    def load_item_attributes(self, infile, spliter='\t'):
        self.load_attributes(self.item_attr, self.n_item, self.n_item_attr, infile, spliter)

    def load_attributes(self, res, n, m, infile, spliter):
        del res[:]
        for i in range(n):
            res.append([])
        with open(infile, 'r') as rd:
            while True:
                line = rd.readline()
                if not line:
                    break
                words = line.replace('\r\n', '').replace('\n', '').split(spliter)
                uid = int(words[0])
                for i in range(len(words) - 1):
                    tokens = words[i + 1].split(':')
                    res[uid].append([int(tokens[0]), float(tokens[1])])

    def load_trainging_ratings(self, infile, spliter='\t'):
        self.load_rating_file(infile, self.training_ratings_user, self.training_ratings_item, self.training_ratings_score, spliter)

    def load_test_ratings(self, infile, spliter='\t'):
        self.load_rating_file(infile, self.test_ratings_user, self.test_ratings_item, self.test_ratings_score, spliter)

    def load_eval_ratings(self, infile, spliter='\t'):
        self.load_rating_file(infile, self.eval_ratings_user, self.eval_ratings_item, self.eval_ratings_score, spliter)

    def load_rating_file(self, infile, rating_user, rating_item, rating_score, spliter):
        del rating_user[:]
        del rating_item[:]
        del rating_score[:]
        with open(infile, 'r') as rd:
            while True:
                line = rd.readline()
                if not line:
                    break
                words = line.replace('\r\n', '').replace('\n', '').split(spliter)
                rating_user.append(int(words[0]))
                rating_item.append(int(words[1]))
                rating_score.append(float(words[2]))

    def load_trainging_pairwise_ratings(self, infile, spliter='\t'):
        self.load_pairwise_rating_file(infile, self.training_ratings_user, self.training_ratings_item, self.training_ratings_item02, self.training_ratings_score, spliter)

    def load_test_pairwise_ratings(self, infile, spliter='\t'):
        self.load_pairwise_rating_file(infile, self.test_ratings_user, self.test_ratings_item, self.test_ratings_item02, self.test_ratings_score, spliter)

    def load_pairwise_rating_file(self, infile, rating_user, rating_item01, rating_item02, rating_score, spliter):
        del rating_user[:]
        del rating_item01[:]
        del rating_item02[:]
        del rating_score[:]
        with open(infile, 'r') as rd:
            while True:
                line = rd.readline()
                if not line:
                    break
                words = line.replace('\r\n', '').replace('\n', '').split(spliter)
                rating_user.append(int(words[0]))
                rating_item01.append(int(words[1]))
                rating_item02.append(int(words[2]))
                rating_score.append(float(words[3]))

def load_attributes(self, res, n, m, infile, spliter):
    del res[:]
    for i in range(n):
        res.append([])
    with open(infile, 'r') as rd:
        while True:
            line = rd.readline()
            if not line:
                break
            words = line.replace('\r\n', '').replace('\n', '').split(spliter)
            uid = int(words[0])
            for i in range(len(words) - 1):
                tokens = words[i + 1].split(':')
                res[uid].append([int(tokens[0]), float(tokens[1])])

def load_rating_file(self, infile, rating_user, rating_item, rating_score, spliter):
    del rating_user[:]
    del rating_item[:]
    del rating_score[:]
    with open(infile, 'r') as rd:
        while True:
            line = rd.readline()
            if not line:
                break
            words = line.replace('\r\n', '').replace('\n', '').split(spliter)
            rating_user.append(int(words[0]))
            rating_item.append(int(words[1]))
            rating_score.append(float(words[2]))

def load_pairwise_rating_file(self, infile, rating_user, rating_item01, rating_item02, rating_score, spliter):
    del rating_user[:]
    del rating_item01[:]
    del rating_item02[:]
    del rating_score[:]
    with open(infile, 'r') as rd:
        while True:
            line = rd.readline()
            if not line:
                break
            words = line.replace('\r\n', '').replace('\n', '').split(spliter)
            rating_user.append(int(words[0]))
            rating_item01.append(int(words[1]))
            rating_item02.append(int(words[2]))
            rating_score.append(float(words[3]))

class dense_data_repos:

    def __init__(self, n_user, n_item, n_user_attr=0, n_item_attr=0):
        self.n_user = n_user
        self.n_item = n_item
        self.n_user_attr = n_user_attr
        self.n_item_attr = n_item_attr
        self.user_attr = []
        self.item_attr = []
        self.training_ratings = []
        self.test_ratings = []

    def load_user_attributes(self, infile, spliter='\t'):
        self.load_attributes(self.user_attr, self.n_user, self.n_user_attr, infile, spliter)

    def load_item_attributes(self, infile, spliter='\t'):
        self.load_attributes(self.item_attr, self.n_item, self.n_item_attr, infile, spliter)

    def load_attributes(self, res, n, m, infile, spliter):
        del res[:]
        for i in range(n):
            res.append([0.0] * m)
        with open(infile, 'r') as rd:
            while True:
                line = rd.readline()
                if not line:
                    break
                words = line.replace('\r\n', '').replace('\n', '').split(spliter)
                uid = int(words[0])
                for i in range(len(words) - 1):
                    tokens = words[i + 1].split(':')
                    res[uid][int(tokens[0])] = float(tokens[1])

    def load_trainging_ratings(self, infile, spliter='\t'):
        self.load_rating_file(infile, self.training_ratings, spliter)

    def load_test_ratings(self, infile, spliter='\t'):
        self.load_rating_file(infile, self.test_ratings, spliter)

    def load_rating_file(self, infile, rating_list, spliter):
        del rating_list[:]
        with open(infile, 'r') as rd:
            while True:
                line = rd.readline()
                if not line:
                    break
                words = line.replace('\r\n', '').replace('\n', '').split(spliter)
                rating_list.append([int(words[0]), int(words[1]), float(words[2])])

def load_attributes(self, res, n, m, infile, spliter):
    del res[:]
    for i in range(n):
        res.append([0.0] * m)
    with open(infile, 'r') as rd:
        while True:
            line = rd.readline()
            if not line:
                break
            words = line.replace('\r\n', '').replace('\n', '').split(spliter)
            uid = int(words[0])
            for i in range(len(words) - 1):
                tokens = words[i + 1].split(':')
                res[uid][int(tokens[0])] = float(tokens[1])

def load_rating_file(self, infile, rating_list, spliter):
    del rating_list[:]
    with open(infile, 'r') as rd:
        while True:
            line = rd.readline()
            if not line:
                break
            words = line.replace('\r\n', '').replace('\n', '').split(spliter)
            rating_list.append([int(words[0]), int(words[1]), float(words[2])])

def load_rating_tsv(filename):
    """
	res: [ [uid,iid,score], ... ]
	"""
    res = []
    with open(filename, 'r') as rd:
        while True:
            line = rd.readline()
            if not line:
                break
            words = line.replace('\r\n', '').replace('\n', '').split('\t')
            res.append([words[0], words[1], float(words[2])])
    return res

def load_content_tsv(filename):
    """
	res: dict --> uid : [ [tag,value], ...]
	"""
    res = {}
    with open(filename, 'r') as rd:
        while True:
            line = rd.readline()
            if not line:
                break
            words = line.replace('\r\n', '').replace('\n', '').split('\t')
            res[words[0]] = []
            for i in range(len(words) - 1):
                tokens = words[i + 1].split(':')
                res[words[0]].append([tokens[0], float(tokens[1])])
    return res

def load_data_from_file_batching(file, batch_size):
    labels = []
    features = []
    cnt = 0
    with open(file, 'r') as rd:
        while True:
            line = rd.readline()
            if not line:
                break
            cnt += 1
            if '#' in line:
                punc_idx = line.index('#')
            else:
                punc_idx = len(line)
            label = float(line[0:1])
            if label > 1:
                label = 1
            feature_line = line[2:punc_idx]
            words = feature_line.split(' ')
            cur_feature_list = []
            for word in words:
                if not word:
                    continue
                tokens = word.split(':')
                if len(tokens[1]) <= 0:
                    tokens[1] = '0'
                cur_feature_list.append([int(tokens[0]) - 1, float(tokens[1])])
            features.append(cur_feature_list)
            labels.append(label)
            if cnt == batch_size:
                yield (labels, features)
                labels = []
                features = []
                cnt = 0
    if cnt > 0:
        yield (labels, features)

def prepare_data_4_sp(labels, features, dim):
    instance_cnt = len(labels)
    indices = []
    values = []
    values_2 = []
    shape = [instance_cnt, dim]
    feature_indices = []
    for i in range(instance_cnt):
        m = len(features[i])
        for j in range(m):
            indices.append([i, features[i][j][0]])
            values.append(features[i][j][1])
            values_2.append(features[i][j][1] * features[i][j][1])
            feature_indices.append(features[i][j][0])
    res = {}
    res['indices'] = np.asarray(indices, dtype=np.int64)
    res['values'] = np.asarray(values, dtype=np.float32)
    res['values2'] = np.asarray(values_2, dtype=np.float32)
    res['shape'] = np.asarray(shape, dtype=np.int64)
    res['labels'] = np.asarray([[label] for label in labels], dtype=np.float32)
    res['feature_indices'] = np.asarray(feature_indices, dtype=np.int64)
    return res

def load_data_from_file_batching(file, batch_size):
    labels = []
    features = []
    qids = []
    docids = []
    cnt = 0
    with open(file, 'r') as rd:
        while True:
            line = rd.readline().strip()
            if not line:
                break
            cnt += 1
            if '#' in line:
                punc_idx = line.index('#')
            else:
                punc_idx = len(line)
            before_comment_line = line[:punc_idx].strip()
            after_comment_line = line[punc_idx + 1:].strip()
            cols = before_comment_line.split()
            label = float(cols[0])
            if label > 0:
                label = 1
            else:
                label = 0
            words = []
            for col in cols[1:]:
                if col.startswith('qid:'):
                    qids.append(col)
                else:
                    words.append(col)
            cur_feature_list = []
            for word in words:
                if not word:
                    continue
                tokens = word.split(':')
                if len(tokens[2]) <= 0:
                    tokens[2] = '0'
                cur_feature_list.append([int(tokens[0]) - 1, int(tokens[1]) - 1, float(tokens[2])])
            features.append(cur_feature_list)
            labels.append(label)
            if len(after_comment_line) > 0:
                docids.append(after_comment_line)
            if len(qids) < len(labels):
                qids.append('qid:fake')
            if cnt == batch_size:
                yield (labels, features, qids, docids)
                labels = []
                features = []
                qids = []
                docids = []
                cnt = 0
    if cnt > 0:
        yield (labels, features, qids, docids)

def prepare_data_4_sp(labels, features, dim):
    instance_cnt = len(labels)
    indices = []
    values = []
    values_2 = []
    shape = [instance_cnt, dim]
    field2feature_indices = []
    field2feature_values = []
    field2feature_weights = []
    filed2feature_shape = [instance_cnt * FIELD_COUNT, -1]
    lastidx = 0
    for i in range(instance_cnt):
        m = len(features[i])
        field2features_dic = {}
        for j in range(m):
            indices.append([i, features[i][j][1]])
            values.append(features[i][j][2])
            values_2.append(features[i][j][2] * features[i][j][2])
            if features[i][j][0] not in field2features_dic:
                field2features_dic[features[i][j][0]] = 0
            else:
                field2features_dic[features[i][j][0]] += 1
            cur_idx = i * FIELD_COUNT + features[i][j][0]
            if lastidx < cur_idx:
                lastidx = cur_idx
            field2feature_indices.append([i * FIELD_COUNT + features[i][j][0], field2features_dic[features[i][j][0]]])
            field2feature_values.append(features[i][j][1])
            field2feature_weights.append(features[i][j][2])
            if filed2feature_shape[1] < field2features_dic[features[i][j][0]]:
                filed2feature_shape[1] = field2features_dic[features[i][j][0]]
    filed2feature_shape[1] += 1
    sorted_index = sorted(range(len(field2feature_indices)), key=lambda k: (field2feature_indices[k][0], field2feature_indices[k][1]))
    res = {}
    res['indices'] = np.asarray(indices, dtype=np.int64)
    res['values'] = np.asarray(values, dtype=np.float32)
    res['values2'] = np.asarray(values_2, dtype=np.float32)
    res['shape'] = np.asarray(shape, dtype=np.int64)
    res['labels'] = np.asarray([[label] for label in labels], dtype=np.float32)
    res['field2feature_indices'] = np.asarray(field2feature_indices, dtype=np.int64)[sorted_index]
    res['field2feature_values'] = np.asarray(field2feature_values, dtype=np.int64)[sorted_index]
    res['field2feature_weights'] = np.asarray(field2feature_weights, dtype=np.float32)[sorted_index]
    res['filed2feature_shape'] = np.asarray(filed2feature_shape, dtype=np.int64)
    return res

def compose_vector_for_sparse_tensor(entity2attr_list):
    indices = []
    indices_values = []
    weight_values = []
    N = len(entity2attr_list)
    for i in range(N):
        if len(entity2attr_list[i]) > 0:
            cnt = 0
            for attr_pair in entity2attr_list[i]:
                indices.append([i, cnt])
                indices_values.append(attr_pair[0])
                weight_values.append(attr_pair[1])
                cnt += 1
        else:
            indices.append([i, 0])
            indices_values.append(0)
            weight_values.append(0)
    return (indices, indices_values, weight_values)

class ImpDataset(object):

    def __init__(self, path):
        self.trainPosSet, self.num_users, self.num_items = self.load_rating_file_as_set(path + 'train.tsv')
        self.testPosSet, _, _ = self.load_rating_file_as_set(path + 'test.tsv')
        self.testPair2NegList = self.load_negative_file_as_dict(path + 'test.negative.tsv')

    def load_rating_file_as_set(self, filename):
        num_users, num_items = (0, 0)
        res = set()
        with open(filename, 'r') as rd:
            while True:
                line = rd.readline()
                if not line:
                    break
                words = line.strip().split('\t')
                u, i = (int(words[0]), int(words[1]))
                num_users = max(num_users, u)
                num_items = max(num_items, i)
                key = (u, i)
                if key not in res:
                    res.add(key)
        return (res, num_users + 1, num_items + 1)

    def load_negative_file_as_dict(self, filename):
        res = dict()
        with open(filename, 'r') as rd:
            while True:
                line = rd.readline()
                if not line:
                    break
                words = line.strip().split('\t')
                key = eval(words[0])
                if key in res:
                    continue
                res[key] = [int(i) for i in words[1:]]
                res[key].append(key[1])
                res[key] = np.asarray(res[key], dtype=np.int32)
                np.random.shuffle(res[key])
        return res

    def make_training_instances(self, neg_k):
        user_input, item_input, labels = ([], [], [])
        for u, i in self.trainPosSet:
            user_input.append(u)
            item_input.append(i)
            labels.append(1.0)
            for _ in range(neg_k):
                j = np.random.randint(self.num_items)
                while (u, j) in self.trainPosSet:
                    j = np.random.randint(self.num_items)
                user_input.append(u)
                item_input.append(j)
                labels.append(0.0)
        num_inst = len(user_input)
        user_input, item_input, labels = (np.asarray(user_input, np.int32), np.asarray(item_input, np.int32), np.asarray(labels, np.float32))
        indices = np.arange(num_inst)
        np.random.shuffle(indices)
        return (user_input[indices], item_input[indices], labels[indices], num_inst)

def load_rating_file_as_set(self, filename):
    num_users, num_items = (0, 0)
    res = set()
    with open(filename, 'r') as rd:
        while True:
            line = rd.readline()
            if not line:
                break
            words = line.strip().split('\t')
            u, i = (int(words[0]), int(words[1]))
            num_users = max(num_users, u)
            num_items = max(num_items, i)
            key = (u, i)
            if key not in res:
                res.add(key)
    return (res, num_users + 1, num_items + 1)

def load_negative_file_as_dict(self, filename):
    res = dict()
    with open(filename, 'r') as rd:
        while True:
            line = rd.readline()
            if not line:
                break
            words = line.strip().split('\t')
            key = eval(words[0])
            if key in res:
                continue
            res[key] = [int(i) for i in words[1:]]
            res[key].append(key[1])
            res[key] = np.asarray(res[key], dtype=np.int32)
            np.random.shuffle(res[key])
    return res

def make_training_instances(self, neg_k):
    user_input, item_input, labels = ([], [], [])
    for u, i in self.trainPosSet:
        user_input.append(u)
        item_input.append(i)
        labels.append(1.0)
        for _ in range(neg_k):
            j = np.random.randint(self.num_items)
            while (u, j) in self.trainPosSet:
                j = np.random.randint(self.num_items)
            user_input.append(u)
            item_input.append(j)
            labels.append(0.0)
    num_inst = len(user_input)
    user_input, item_input, labels = (np.asarray(user_input, np.int32), np.asarray(item_input, np.int32), np.asarray(labels, np.float32))
    indices = np.arange(num_inst)
    np.random.shuffle(indices)
    return (user_input[indices], item_input[indices], labels[indices], num_inst)

def getNDCG(items, iid):
    for i in range(len(items)):
        if items[i] == iid:
            return math.log(2) / math.log(i + 2)
    return 0.0

