# Cluster 3

def load_openml_list(dids, filter_for_nan=False, num_feats=100, min_samples=100, max_samples=400, multiclass=True, max_num_classes=10, shuffled=True, return_capped=False):
    """Load a list of openml datasets and return the data in the correct format."""
    datasets = []
    openml_list = openml.datasets.list_datasets(dids)
    print(f'Number of datasets: {len(openml_list)}')
    datalist = pd.DataFrame.from_dict(openml_list, orient='index')
    if filter_for_nan:
        datalist = datalist[datalist['NumberOfInstancesWithMissingValues'] == 0]
        print(f'Number of datasets after Nan and feature number filtering: {len(datalist)}')
    for ds in datalist.index:
        modifications = {'samples_capped': False, 'classes_capped': False, 'feats_capped': False}
        entry = datalist.loc[ds]
        print('Loading', entry['name'], entry.did, '..')
        if entry['NumberOfClasses'] == 0.0:
            raise Exception('Regression not supported')
        else:
            X, y, categorical_feats, attribute_names, description = get_openml_classification(int(entry.did), max_samples, multiclass=multiclass, shuffled=shuffled)
        if X is None:
            continue
        if X.shape[1] > num_feats:
            if return_capped:
                X = X[:, 0:num_feats]
                categorical_feats = [c for c in categorical_feats if c < num_feats]
                modifications['feats_capped'] = True
            else:
                print('Too many features')
                continue
        if X.shape[0] == max_samples:
            modifications['samples_capped'] = True
        if X.shape[0] < min_samples:
            print(f'Too few samples left')
            continue
        if len(np.unique(y)) > max_num_classes:
            if return_capped:
                X = X[y < np.unique(y)[10]]
                y = y[y < np.unique(y)[10]]
                modifications['classes_capped'] = True
            else:
                print(f'Too many classes')
                continue
        datasets += [[entry['name'], X, y, categorical_feats, attribute_names, modifications, description]]
    return (datasets, datalist)

def get_X_y(df_train, target_name):
    y = torch.tensor(df_train[target_name].astype(int).to_numpy())
    x = torch.tensor(df_train.drop(target_name, axis=1).to_numpy())
    return (x, y)

def get_df(X, y):
    df = pd.DataFrame(data=np.concatenate([X, np.expand_dims(y, -1)], -1), columns=ds[4])
    cat_features = ds[3]
    for c in cat_features:
        if len(np.unique(df.iloc[:, c])) > 50:
            cat_features.remove(c)
            continue
        df[df.columns[c]] = df[df.columns[c]].astype('int32')
    return df.infer_objects()

def postprocess_datasets(cc_test_datasets_multiclass):
    for ds in cc_test_datasets_multiclass:
        dataset_down_size = {'balance-scale': 0.2, 'breast-w': 0.1, 'tic-tac-toe': 0.1}
        p = dataset_down_size.get(ds[0], 1.0)
        if p < 1.0:
            print(f'Downsampling {ds[0]} to {p * 100}% of samples')
        df = pd.DataFrame(np.concatenate([ds[1], ds[2][:, np.newaxis]], 1)).infer_objects()
        if ds[0].startswith('kaggle'):
            df = df.dropna()
        df.loc[:, df.dtypes == object] = df.loc[:, df.dtypes == object].fillna('')
        l = len(df)
        l = min(l, 2000)
        df = df.sample(frac=1)
        ds[1] = df.values[0:int(p * l), :-1]
        ds[2] = df.values[0:int(p * l), -1]
    return cc_test_datasets_multiclass

def auc_metric(target, pred, multi_class='ovo', numpy=False):
    lib = np if numpy else torch
    try:
        if not numpy:
            target = torch.tensor(target) if not torch.is_tensor(target) else target
            pred = torch.tensor(pred) if not torch.is_tensor(pred) else pred
        if len(lib.unique(target)) > 2:
            if not numpy:
                return torch.tensor(roc_auc_score(target, pred, multi_class=multi_class))
            return roc_auc_score(target, pred, multi_class=multi_class)
        else:
            if len(pred.shape) == 2:
                pred = pred[:, 1]
            if not numpy:
                return torch.tensor(roc_auc_score(target, pred))
            return roc_auc_score(target, pred)
    except ValueError as e:
        print(e)
        return np.nan if numpy else torch.tensor(np.nan)

def accuracy_metric(target, pred):
    target = torch.tensor(target) if not torch.is_tensor(target) else target
    pred = torch.tensor(pred) if not torch.is_tensor(pred) else pred
    if len(torch.unique(target)) > 2:
        return torch.tensor(accuracy_score(target, torch.argmax(pred, -1)))
    else:
        return torch.tensor(accuracy_score(target, pred[:, 1] > 0.5))

