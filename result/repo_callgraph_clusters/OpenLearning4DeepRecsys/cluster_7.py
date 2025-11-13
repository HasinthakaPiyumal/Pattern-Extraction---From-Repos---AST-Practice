# Cluster 7

def pre_build_data_cache(infile, outfile, feature_cnt, batch_size):
    wt = open(outfile, 'wb')
    for labels, features in load_data_from_file_batching(infile, batch_size):
        input_in_sp = prepare_data_4_sp(labels, features, feature_cnt)
        pickle.dump(input_in_sp, wt)
    wt.close()

def pre_build_data_cache(infile, outfile, batch_size):
    wt = open(outfile, 'wb')
    for labels, features, qids, docids in load_data_from_file_batching(infile, batch_size):
        input_in_sp = prepare_data_4_sp(labels, features, FEATURE_COUNT)
        pickle.dump((input_in_sp, qids, docids), wt)
    wt.close()

def grid_search_params():
    dataset = data_reader.sparse_data_repos(10000, 10005)
    dataset.load_trainging_ratings('data/userbook_unique_compactid_train.txt')
    dataset.load_test_ratings('data/userbook_unique_compactid_valid.txt')
    dataset.load_eval_ratings('data/userbook_unique_compactid_test.txt')
    log_file = 'logs/BMF_book.csv'
    wt = open(log_file, 'w')
    rank = 16
    lambs = [3e-05, 5e-05, 0.0001]
    batch_sizes = [500]
    n_eopch = 2000
    lrs = [0.1]
    init_values = [0.01]
    mu = np.asarray(dataset.training_ratings_score, dtype=np.float32).mean()
    wt.write('rank,lr,lamb,mu,n_eopch,batch_size,best_train_rmse,best_test_rmse,best_eval_rmse,best_epoch,init_value,minutes\n')
    for lamb in lambs:
        for lr in lrs:
            for init_value in init_values:
                for batch_size in batch_sizes:
                    run_with_parameter(dataset, rank, lr, lamb, mu, n_eopch, batch_size, wt, init_value)
    wt.close()

def grid_search(infile, logfile):
    params = {'cf_dim': 16, 'user_attr_rank': 16, 'item_attr_rank': 16, 'layer_sizes': [16, 8], 'lr': 0.1, 'lamb': 0.001, 'mu': 4.0, 'n_eopch': 2000, 'batch_size': 500, 'init_value ': 0.01}
    dataset = data_reader.movie_lens_data_repos(infile)
    wt = open(logfile, 'w')
    lambs = [0.001, 0.0001, 0.0005, 0.005]
    lrs = [0.1, 0.05]
    layer_sizes_list = [[16], [16, 8]]
    init_values = [0.01, 0.1]
    mu = dataset.training_ratings_score.mean()
    for lamb in lambs:
        for lr in lrs:
            for init_value in init_values:
                for layer_sizes in layer_sizes_list:
                    params['lamb'] = lamb
                    params['lr'] = lr
                    params['init_value'] = init_value
                    params['layer_sizes'] = layer_sizes
                    params['mu'] = mu
                    run_with_parameters(dataset, params, wt)
                    run_with_parameters(dataset, params, wt)
    wt.close()

def evaluate_model(sess, model, dataset, topk):
    hits, ndcgs = ([], [])
    for u, i in dataset.testPosSet:
        hit, ndcg = evaluate_one_case(u, i, dataset.testPair2NegList, sess, model, topk)
        hits.append(hit)
        ndcgs.append(ndcg)
    return (np.asarray(hits).mean(), np.asarray(ndcgs).mean())

