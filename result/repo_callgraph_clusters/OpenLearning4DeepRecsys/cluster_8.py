# Cluster 8

def single_run(feature_cnt, field_cnt, params):
    print(params)
    pre_build_data_cache_if_need(params['train_file'], feature_cnt, params['batch_size'])
    pre_build_data_cache_if_need(params['test_file'], feature_cnt, params['batch_size'])
    params['train_file'] = params['train_file'].replace('.csv', '.pkl').replace('.txt', '.pkl')
    params['test_file'] = params['test_file'].replace('.csv', '.pkl').replace('.txt', '.pkl')
    print('start single_run')
    tf.reset_default_graph()
    n_epoch = params['n_epoch']
    batch_size = params['batch_size']
    _indices = tf.placeholder(tf.int64, shape=[None, 2], name='raw_indices')
    _values = tf.placeholder(tf.float32, shape=[None], name='raw_values')
    _values2 = tf.placeholder(tf.float32, shape=[None], name='raw_values_square')
    _shape = tf.placeholder(tf.int64, shape=[2], name='raw_shape')
    _y = tf.placeholder(tf.float32, shape=[None, 1], name='Y')
    _ind = tf.placeholder(tf.int64, shape=[None])
    _keep_probs = tf.placeholder(tf.float32, shape=[len(params['keep_probs'])], name='dropout_keep_probability')
    train_step, loss, error, preds, merged_summary, tmp = build_model(_indices, _values, _values2, _shape, _y, _ind, _keep_probs, feature_cnt, field_cnt, params)
    saver = tf.train.Saver()
    sess = tf.Session()
    init = tf.global_variables_initializer()
    sess.run(init)
    log_writer = tf.summary.FileWriter(params['log_path'], graph=sess.graph)
    glo_ite = 0
    for eopch in range(n_epoch):
        iteration = -1
        start = clock()
        time_load_data, time_sess = (0, 0)
        time_cp02 = clock()
        train_loss_per_epoch = 0
        for training_input_in_sp in load_data_cache(params['train_file']):
            time_cp01 = clock()
            time_load_data += time_cp01 - time_cp02
            iteration += 1
            glo_ite += 1
            _, cur_loss, summary, _tmp = sess.run([train_step, loss, merged_summary, tmp], feed_dict={_indices: training_input_in_sp['indices'], _values: training_input_in_sp['values'], _shape: training_input_in_sp['shape'], _y: training_input_in_sp['labels'], _values2: training_input_in_sp['values2'], _ind: training_input_in_sp['feature_indices'], _keep_probs: np.asarray(params['keep_probs'])})
            time_cp02 = clock()
            time_sess += time_cp02 - time_cp01
            train_loss_per_epoch += cur_loss
            log_writer.add_summary(summary, glo_ite)
        end = clock()
        if eopch % 5 == 0:
            model_path = params['model_path'] + '/' + str(params['layer_sizes']).replace(':', '_') + str(params['reg_w_linear']).replace(':', '_')
            os.makedirs(model_path, exist_ok=True)
            saver.save(sess, model_path, global_step=eopch)
            auc = predict_test_file(preds, sess, params['test_file'], feature_cnt, _indices, _values, _shape, _y, _values2, _ind, _keep_probs, eopch, batch_size, 'test', model_path, params['output_predictions'], params)
            print('auc is ', auc, ', at epoch  ', eopch, ', time is {0:.4f} min'.format((end - start) / 60.0), ', train_loss is {0:.2f}'.format(train_loss_per_epoch))
    log_writer.close()

def pre_build_data_cache_if_need(infile, feature_cnt, batch_size):
    outfile = infile.replace('.csv', '.pkl').replace('.txt', '.pkl')
    if not os.path.isfile(outfile):
        print('pre_build_data_cache for ', infile)
        pre_build_data_cache(infile, outfile, feature_cnt, batch_size)
        print('pre_build_data_cache finished.')

def run():
    print('begin running')
    field_cnt = 46
    feature_cnt = 46
    params = {'reg_w_linear': 0.0001, 'reg_w_fm': 0.0001, 'reg_w_nn': 0.0001, 'reg_w_l1': 0.0001, 'init_value': 0.1, 'layer_sizes': [10, 5], 'keep_probs': [0.7, 0.7], 'activations': ['tanh', 'tanh'], 'eta': 0.1, 'n_epoch': 5000, 'batch_size': 50, 'dim': 8, 'model_path': 'models', 'log_path': 'logs/' + datetime.utcnow().strftime('%Y-%m-%d_%H_%M_%S'), 'train_file': 'data/S1_4.txt', 'test_file': 'data/S5.txt', 'output_predictions': False, 'is_use_fm_part': True, 'is_use_dnn_part': True, 'learning_rate': 0.01, 'loss': 'log_loss', 'optimizer': 'sgd'}
    single_run(feature_cnt, field_cnt, params)

def single_run(params):
    logger.info('\n\n')
    logger.info(params)
    logger.info('\n\n')
    pre_build_data_cache_if_need(params['train_file'], params['batch_size'], params['clean_cache'] if 'clean_cache' in params else False)
    pre_build_data_cache_if_need(params['test_file'], params['batch_size'], params['clean_cache'] if 'clean_cache' in params else False)
    params['train_file'] = params['train_file'].replace('.csv', '.pkl').replace('.txt', '.pkl')
    params['test_file'] = params['test_file'].replace('.csv', '.pkl').replace('.txt', '.pkl')
    print('start single_run')
    tf.reset_default_graph()
    n_epoch = params['n_epoch']
    batch_size = params['batch_size']
    _indices = tf.placeholder(tf.int64, shape=[None, 2], name='raw_indices')
    _values = tf.placeholder(tf.float32, shape=[None], name='raw_values')
    _values2 = tf.placeholder(tf.float32, shape=[None], name='raw_values_square')
    _shape = tf.placeholder(tf.int64, shape=[2], name='raw_shape')
    _field2feature_indices = tf.placeholder(tf.int64, shape=[None, 2], name='field2feature_indices')
    _field2feature_values = tf.placeholder(tf.int64, shape=[None], name='field2feature_values')
    _field2feature_weights = tf.placeholder(tf.float32, shape=[None], name='field2feature_weights')
    _field2feature_shape = tf.placeholder(tf.int64, shape=[2], name='field2feature_shape')
    _y = tf.placeholder(tf.float32, shape=[None, 1], name='Y')
    train_step, loss, error, preds, tmp = build_model(_indices, _values, _values2, _shape, _field2feature_indices, _field2feature_values, _field2feature_weights, _field2feature_shape, _y, params)
    saver = tf.train.Saver()
    sess = tf.Session()
    init = tf.global_variables_initializer()
    sess.run(init)
    glo_ite = 0
    last_best_auc = None
    max_stop_grow_torrelence = 50
    stop_grow_cnt = 0
    start = clock()
    for eopch in range(n_epoch):
        iteration = -1
        time_load_data, time_sess = (0, 0)
        time_cp02 = clock()
        train_loss_per_epoch = 0
        for training_input_in_sp, qids, docids in load_data_cache(params['train_file']):
            time_cp01 = clock()
            time_load_data += time_cp01 - time_cp02
            iteration += 1
            glo_ite += 1
            _, cur_loss = sess.run([train_step, loss], feed_dict={_indices: training_input_in_sp['indices'], _values: training_input_in_sp['values'], _shape: training_input_in_sp['shape'], _y: training_input_in_sp['labels'], _values2: training_input_in_sp['values2'], _field2feature_indices: training_input_in_sp['field2feature_indices'], _field2feature_values: training_input_in_sp['field2feature_values'], _field2feature_weights: training_input_in_sp['field2feature_weights'], _field2feature_shape: training_input_in_sp['filed2feature_shape']})
            time_cp02 = clock()
            time_sess += time_cp02 - time_cp01
            train_loss_per_epoch += cur_loss
        end = clock()
        if eopch % 1 == 0:
            model_path = params['model_path'] + '/' + str(params['layer_sizes']).replace(':', '_') + str(params['reg_w_linear']).replace(':', '_')
            os.makedirs(model_path, exist_ok=True)
            saver.save(sess, model_path, global_step=eopch)
            metrics = predict_test_file(preds, sess, params['test_file'], _indices, _values, _shape, _y, _values2, _field2feature_indices, _field2feature_values, _field2feature_weights, _field2feature_shape, eopch, batch_size, 'test', model_path, params['output_predictions'], params)
            metrics_strs = []
            auc = 0
            for metric_name in metrics:
                metrics_strs.append('{0} is {1:.5f}'.format(metric_name, metrics[metric_name]))
                if metric_name == 'global_auc':
                    auc = metrics[metric_name]
            if last_best_auc is None or auc > last_best_auc:
                last_best_auc = auc
                stop_grow_cnt = 0
            else:
                stop_grow_cnt += 1
            res_str = ' ,'.join(metrics_strs) + ', at epoch {0:d}, time is {1:.4f} min, train_loss is {2:.2f}'.format(eopch, (end - start) / 60.0, train_loss_per_epoch)
            logger.info(res_str)
            start = clock()
            if stop_grow_cnt > max_stop_grow_torrelence:
                break

def pre_build_data_cache_if_need(infile, batch_size, rebuild_cache):
    outfile = infile.replace('.csv', '.pkl').replace('.txt', '.pkl')
    if not os.path.isfile(outfile) or rebuild_cache:
        print('pre_build_data_cache for ', infile)
        pre_build_data_cache(infile, outfile, batch_size)
        print('pre_build_data_cache finished.')

def run():
    print('begin running')
    params = {'reg_w_linear': 0.0001, 'reg_w_fm': 0.0001, 'reg_w_nn': 0.0001, 'reg_w_l1': 0.0001, 'init_value': 0.001, 'layer_sizes': [100, 500], 'activations': ['relu', 'tanh'], 'eta': 0.1, 'n_epoch': 5000, 'batch_size': 256, 'dim': 15, 'model_path': 'models', 'train_file': 'data/demodata.fieldwise.txt', 'test_file': 'data/demodata.fieldwise.txt', 'output_predictions': False, 'is_use_fm_part': True, 'is_use_dnn_part': True, 'multi_level_num': 1, 'learning_rate': 0.0001, 'loss': 'log_loss', 'optimizer': 'adam', 'clean_cache': True, 'metrics': [{'name': 'global_auc'}]}
    grid_search(params)

def grid_search(params):
    single_run(params)
    "\n    for i in range(0,5):      \n        params['dim'] = pow(2,i)    \n        \n        for _ in range(3):\n            single_run(  params)\n    "

def run_with_parameter(dataset, rank, lr, lamb, mu, n_eopch, batch_size, wt, init_value):
    start = clock()
    tf.reset_default_graph()
    best_train_rmse, best_test_rmse, best_eval_rmse, best_eopch_idx = single_run(dataset, rank, dataset.n_user, dataset.n_item, lr, lamb, mu, n_eopch, batch_size, True, init_value)
    end = clock()
    wt.write('%d,%f,%f,%f,%d,%d,%f,%f,%f,%d,%f,%f\n' % (rank, lr, lamb, mu, n_eopch, batch_size, best_train_rmse, best_test_rmse, best_eval_rmse, best_eopch_idx, init_value, (end - start) / 60))
    wt.flush()

def single_run(dataset, rank, user_cnt, item_cnt, lr, lamb, mu, n_eopch, batch_size, is_eval_on, init_value):
    user_indices = tf.placeholder(tf.int32, [None])
    item_indices = tf.placeholder(tf.int32, [None])
    ratings = tf.placeholder(tf.float32, [None])
    train_step, square_error, loss, merged_summary = build_model(user_indices, item_indices, rank, ratings, user_cnt, item_cnt, lr, lamb, mu, init_value)
    sess = tf.Session()
    init = tf.global_variables_initializer()
    sess.run(init)
    train_writer = tf.summary.FileWriter('logs', sess.graph)
    n_instances = len(dataset.training_ratings_user)
    best_train_rmse, best_test_rmse, best_eval_rmse = (-1, -1, -1)
    best_eopch_idx = -1
    for ite in range(n_eopch):
        start = clock()
        for i in range(n_instances // batch_size):
            start_idx = i * batch_size
            end_idx = start_idx + batch_size
            cur_user_indices, cur_item_indices, cur_label = (dataset.training_ratings_user[start_idx:end_idx], dataset.training_ratings_item[start_idx:end_idx], dataset.training_ratings_score[start_idx:end_idx])
            sess.run(train_step, {user_indices: cur_user_indices, item_indices: cur_item_indices, ratings: cur_label})
        error_traing = sess.run(square_error, {user_indices: dataset.training_ratings_user, item_indices: dataset.training_ratings_item, ratings: dataset.training_ratings_score})
        error_test = sess.run(square_error, {user_indices: dataset.test_ratings_user, item_indices: dataset.test_ratings_item, ratings: dataset.test_ratings_score})
        if is_eval_on:
            error_eval = sess.run(square_error, {user_indices: dataset.eval_ratings_user, item_indices: dataset.eval_ratings_item, ratings: dataset.eval_ratings_score})
        else:
            error_eval = -1
        if best_test_rmse < 0 or best_test_rmse > error_test:
            best_train_rmse, best_test_rmse, best_eval_rmse = (error_traing, error_test, error_eval)
            best_eopch_idx = ite
        elif ite - best_eopch_idx > 10:
            break
        loss_traing = sess.run(loss, {user_indices: dataset.training_ratings_user, item_indices: dataset.training_ratings_item, ratings: dataset.training_ratings_score})
        summary = sess.run(merged_summary, {user_indices: dataset.training_ratings_user, item_indices: dataset.training_ratings_item, ratings: dataset.training_ratings_score})
        train_writer.add_summary(summary, ite)
        end = clock()
        print('Iteration %d  RMSE(train): %f  RMSE(test): %f   RMSE(eval): %f   LOSS(train): %f  minutes: %f' % (ite, error_traing, error_test, error_eval, loss_traing, (end - start) / 60))
    train_writer.close()
    return (best_train_rmse, best_test_rmse, best_eval_rmse, best_eopch_idx)

def run_with_parameters(dataset, params, wt):
    start = clock()
    tf.reset_default_graph()
    best_train_rmse, best_test_rmse, best_eval_rmse, best_eopch_idx = single_run(dataset, params)
    end = clock()
    wt.write('%f,%f,%f,%d,%f,%s\n' % (best_train_rmse, best_test_rmse, best_eval_rmse, best_eopch_idx, (end - start) / 60, str(params)))
    wt.flush()

def single_run(args, dataset):
    model = NeuMF(args, dataset.num_users, dataset.num_items)
    model.build_model()
    sess = tf.Session()
    init = tf.global_variables_initializer()
    sess.run(init)
    t1 = time()
    ahit, andcg = evaluate_model(sess, model, dataset, args.topk)
    best_hr, best_ndcg, best_iter = (ahit, andcg, -1)
    print('Init: HR = %.4f, NDCG = %.4f\t [%.1f s]' % (ahit, andcg, time() - t1))
    for epoch in range(args.epochs):
        t1 = time()
        train_users, train_items, train_labels, num_inst = dataset.make_training_instances(args.num_neg_inst)
        loss_per_epoch, error_per_epoch = (0, 0)
        for ite in range((num_inst - 1) // args.batch_size + 1):
            start_idx = ite * args.batch_size
            end_idx = min((ite + 1) * args.batch_size, num_inst)
            cur_user_indices, cur_item_indices, cur_label = (train_users[start_idx:end_idx], train_items[start_idx:end_idx], train_labels[start_idx:end_idx])
            _, loss, error = sess.run([model.train_step, model.loss, model.raw_error], {model.user_indices: cur_user_indices, model.item_indices: cur_item_indices, model.ratings: cur_label})
            loss_per_epoch += loss
            error_per_epoch += error
        error_per_epoch /= num_inst
        t2 = time()
        if epoch % args.verbose == 0:
            ahit, andcg = evaluate_model(sess, model, dataset, args.topk)
            print('epoch %d   \t[%.1f s]: HR= %.4f\tNDCG= %.4f\tloss= %.4f\terror= %.4f\t[%.1f s]' % (epoch, t2 - t1, ahit, andcg, loss_per_epoch, error_per_epoch, time() - t2))
            if ahit > best_hr:
                best_hr = ahit
                best_iter = epoch
            if andcg > best_ndcg:
                best_ndcg = andcg
    print('End. Best Epoch %d:  HR = %.4f, NDCG = %.4f. ' % (best_iter, best_hr, best_ndcg))

