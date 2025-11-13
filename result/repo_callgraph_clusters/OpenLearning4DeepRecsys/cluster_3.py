# Cluster 3

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

def BuildAttributeFromSPMatrix(self, sp_matrix, n, m):
    res = []
    for _ in range(n):
        res.append([])
    row, col, value = find(sp_matrix)
    for r, c, v in zip(row, col, value):
        res[r].append([c, float(v)])
    return res

def predict_test_file(preds, sess, test_file, feature_cnt, _indices, _values, _shape, _y, _values2, _ind, _keep_probs, epoch, batch_size, tag, path, output_prediction=True, params=None):
    if output_prediction:
        wt = open(path + '/deepFM_pred_' + tag + str(epoch) + '.txt', 'w')
    gt_scores = []
    pred_scores = []
    for test_input_in_sp in load_data_cache(test_file):
        predictios = sess.run(preds, feed_dict={_indices: test_input_in_sp['indices'], _values: test_input_in_sp['values'], _shape: test_input_in_sp['shape'], _y: test_input_in_sp['labels'], _values2: test_input_in_sp['values2'], _ind: test_input_in_sp['feature_indices'], _keep_probs: np.ones_like(params['keep_probs'])}).reshape(-1).tolist()
        if output_prediction:
            for gt, preded in zip(test_input_in_sp['labels'].reshape(-1).tolist(), predictios):
                wt.write('{0:d},{1:f}\n'.format(int(gt), preded))
                gt_scores.append(gt)
                pred_scores.append(preded)
        else:
            gt_scores.extend(test_input_in_sp['labels'].reshape(-1).tolist())
            pred_scores.extend(predictios)
    auc = roc_auc_score(np.asarray(gt_scores), np.asarray(pred_scores))
    if output_prediction:
        wt.close()
    return auc

def predict_test_file(preds, sess, test_file, _indices, _values, _shape, _y, _values2, _field2feature_indices, _field2feature_values, _field2feature_weights, _field2feature_shape, epoch, batch_size, tag, path, output_prediction, params):
    if output_prediction:
        wt = open(path + '/deepFM_pred_' + tag + str(epoch) + '.txt', 'w')
    gt_scores = []
    pred_scores = []
    query2res = {}
    for test_input_in_sp, qids, docids in load_data_cache(test_file):
        predictios = sess.run(preds, feed_dict={_indices: test_input_in_sp['indices'], _values: test_input_in_sp['values'], _shape: test_input_in_sp['shape'], _y: test_input_in_sp['labels'], _values2: test_input_in_sp['values2'], _field2feature_indices: test_input_in_sp['field2feature_indices'], _field2feature_values: test_input_in_sp['field2feature_values'], _field2feature_weights: test_input_in_sp['field2feature_weights'], _field2feature_shape: test_input_in_sp['filed2feature_shape']}).reshape(-1).tolist()
        if output_prediction:
            for gt, preded, qid in zip(test_input_in_sp['labels'].reshape(-1).tolist(), predictios, qids):
                wt.write('{0:d},{1:f}\n'.format(int(gt), preded))
                gt_scores.append(gt)
                pred_scores.append(preded)
        else:
            for gt, preded, qid in zip(test_input_in_sp['labels'].reshape(-1).tolist(), predictios, qids):
                if qid not in query2res:
                    query2res[qid] = []
                query2res[qid].append([gt, preded])
    metrics = compute_metric(query2res, params)
    if output_prediction:
        wt.close()
    return metrics

def compute_metric(query2res, params):
    result = {}
    for m in params['metrics']:
        if 'global_auc' in m['name']:
            gt_scores = []
            pred_scores = []
            for qid in query2res:
                gt_scores.extend([x[0] for x in query2res[qid]])
                pred_scores.extend([x[1] for x in query2res[qid]])
            result['global_auc'] = roc_auc_score(np.asarray(gt_scores), np.asarray(pred_scores))
        elif 'individual_auc' in m['name']:
            aucs = []
            for qid in query2res:
                gt_scores = np.asarray([x[0] for x in query2res[qid]])
                if gt_scores.min() > 0 or gt_scores.max() < 1:
                    continue
                pred_scores = [x[1] for x in query2res[qid]]
                aucs.append(roc_auc_score(gt_scores, np.asarray(pred_scores)))
            result['individual_auc'] = np.asarray(aucs).mean()
        elif 'precision' in m['name']:
            precisions = []
            for qid in query2res:
                k = min(m['k'], len(query2res[qid]))
                gt_scores = np.asarray([x[0] for x in query2res[qid]])
                pred_scores = np.asarray([x[1] for x in query2res[qid]])
                precision = gt_scores[np.argsort(pred_scores)[::-1][:k]].mean()
                precisions.append(precision)
            result['precision_at_' + str(m['k'])] = np.asarray(precisions).mean()
    return result

def evaluate_one_case(u, i, key2candidates, sess, model, topk):
    key = (u, i)
    assert key in key2candidates
    items = key2candidates[key]
    users = np.full(len(items), key[0], dtype=np.int32)
    predictions = sess.run(model.output, {model.user_indices: users, model.item_indices: items})
    k = min(topk, len(items))
    sorted_idx = np.argsort(predictions)[::-1]
    selected_items = items[sorted_idx[0:k]]
    ndcg = getNDCG(selected_items, i)
    hit = getHitRatio(selected_items, i)
    return (hit, ndcg)

class NeuMF(BaseModel):

    def __init__(self, args, num_users, num_items):
        BaseModel.__init__(self, args, num_users, num_items)
        self.layers = eval(args.layers)
        self.lambda_layers = eval(args.reg_layers)
        self.num_factors = args.num_factors
        self.model_GMF = GMF(args, num_users, num_items)
        self.model_MLP = MLP(args, num_users, num_items)

    def build_core_model(self, user_indices, item_indices):
        vector_GMF, len_GMF, params_GMF = self.model_GMF.build_core_model(user_indices, item_indices)
        vector_MLP, len_MLP, params_MLP = self.model_MLP.build_core_model(user_indices, item_indices)
        model_vector = tf.concat([vector_GMF, vector_MLP], 1)
        model_len = len_GMF + len_MLP
        model_params = []
        model_params.extend(params_GMF)
        model_params.extend(params_MLP)
        return (model_vector, model_len, model_params)

    def build_model(self, user_indices=None, item_indices=None):
        if not user_indices:
            user_indices = tf.placeholder(tf.int32, [None])
        self.user_indices = user_indices
        if not item_indices:
            item_indices = tf.placeholder(tf.int32, [None])
        self.item_indices = item_indices
        self.ratings = tf.placeholder(tf.float32, [None])
        model_vector, model_len, model_params = self.build_core_model(user_indices, item_indices)
        self.output, self.loss, self.error, self.raw_error, self.train_step = self.build_train_model(model_vector, model_len, self.ratings, model_params)

def build_core_model(self, user_indices, item_indices):
    vector_GMF, len_GMF, params_GMF = self.model_GMF.build_core_model(user_indices, item_indices)
    vector_MLP, len_MLP, params_MLP = self.model_MLP.build_core_model(user_indices, item_indices)
    model_vector = tf.concat([vector_GMF, vector_MLP], 1)
    model_len = len_GMF + len_MLP
    model_params = []
    model_params.extend(params_GMF)
    model_params.extend(params_MLP)
    return (model_vector, model_len, model_params)

