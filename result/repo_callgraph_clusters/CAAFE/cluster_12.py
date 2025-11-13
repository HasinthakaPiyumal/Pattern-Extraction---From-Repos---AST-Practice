# Cluster 12

def load_all_data():
    cc_test_datasets_multiclass, cc_test_datasets_multiclass_df = load_openml_list(benchmark_ids, multiclass=True, shuffled=True, filter_for_nan=False, max_samples=10000, num_feats=25, return_capped=False)
    cc_test_datasets_multiclass += load_kaggle()
    return postprocess_datasets(cc_test_datasets_multiclass)

