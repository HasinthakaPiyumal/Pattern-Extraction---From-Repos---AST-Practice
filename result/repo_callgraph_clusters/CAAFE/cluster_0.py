# Cluster 0

def generate_and_save_feats(i, seed=0, iterative_method=None, iterations=10):
    if iterative_method is None:
        iterative_method = tabpfn
    ds = cc_test_datasets_multiclass[i]
    ds, df_train, df_test, df_train_old, df_test_old = get_data_split(ds, seed)
    code, prompt, messages = generate_features(ds, df_train, just_print_prompt=False, model=model, iterative=iterations, metric_used=metric_used, iterative_method=iterative_method, display_method='print')
    data_dir = os.environ.get('DATA_DIR', 'data/')
    f = open(f'{data_dir}/generated_code/{ds[0]}_{prompt_id}_{seed}_prompt.txt', 'w')
    f.write(prompt)
    f.close()
    f = open(f'{data_dir}/generated_code/{ds[0]}_{prompt_id}_{seed}_code.txt', 'w')
    f.write(code)
    f.close()

def load_result(all_results, ds, seed, method, prompt_id='v2'):
    """Evaluates a dataframe with and without feature extension."""
    method_str = method if type(method) == str else 'transformer'
    data_dir = os.environ.get('DATA_DIR', 'data/')
    path = f'{data_dir}/evaluations/result_{ds[0]}_{prompt_id}_{seed}_{method_str}.txt'
    try:
        f = open(path, 'rb')
        r = pickle.load(f)
        f.close()
        r['failed'] = False
        all_results[f'{ds[0]}_{prompt_id}_{str(seed)}_{method_str}'] = r
        return r
    except Exception as e:
        try:
            path = f'{data_dir}/evaluations/result_{ds[0]}__{seed}_{method_str}.txt'
            f = open(path, 'rb')
            r = pickle.load(f)
            f.close()
            r['prompt'] = prompt_id
            r['failed'] = True
            all_results[f'{ds[0]}_{prompt_id}_{str(seed)}_{method_str}'] = r
            print(f'Could not load result for {ds[0]}_{prompt_id}_{str(seed)}_{method_str} {path}. BL loaded')
            return r
        except Exception as e:
            print(f'[WARN] Could not load baseline result for {ds[0]}_{prompt_id}_{str(seed)}_{method_str} {path}')
            return None

def evaluate_dataset_with_and_without_cafe(ds, seed, methods, metric_used, prompt_id='v2', max_time=300, overwrite=False):
    """Evaluates a dataframe with and without feature extension."""
    ds, df_train, df_test, df_train_old, df_test_old = get_data_split(ds, seed)
    ds, df_train, df_test = evaluate_dataset_helper_extend_df(df_train, df_test, ds, prompt_id, seed)
    print('SHAPE BEFORE', df_train_old.shape, 'AFTER', df_train.shape)
    for method in methods:
        method_str = method if type(method) == str else 'transformer'
        data_dir = os.environ.get('DATA_DIR', 'data/')
        path = f'{data_dir}/evaluations/result_{ds[0]}_{prompt_id}_{seed}_{method_str}.txt'
        if os.path.exists(path) and (not overwrite):
            print(f'Skipping {path}')
            continue
        print(ds[0], method_str, prompt_id, seed)
        r = evaluate_dataset(df_train=df_train, df_test=df_test, prompt_id=prompt_id, name=ds[0], method=method, metric_used=metric_used, max_time=max_time, seed=seed, target_name=ds[4][-1])
        f = open(path, 'wb')
        pickle.dump(r, f)
        f.close()

def make_dataset_numeric(df: pd.DataFrame, mappings: Dict[str, Dict[int, str]]) -> pd.DataFrame:
    """
    Converts the categorical columns in the given dataframe to integer values using the given mappings.

    Parameters:
    df (pandas.DataFrame): The dataframe to convert.
    mappings (Dict[str, Dict[int, str]]): The mappings to use for the conversion.

    Returns:
    pandas.DataFrame: The converted dataframe.
    """
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.apply(lambda col: convert_categorical_to_integer_f(col, mapping=mappings.get(col.name)), axis=0)
    df = df.astype(float)
    return df

def get_data_split(ds, seed):

    def get_df(X, y):
        df = pd.DataFrame(data=np.concatenate([X, np.expand_dims(y, -1)], -1), columns=ds[4])
        cat_features = ds[3]
        for c in cat_features:
            if len(np.unique(df.iloc[:, c])) > 50:
                cat_features.remove(c)
                continue
            df[df.columns[c]] = df[df.columns[c]].astype('int32')
        return df.infer_objects()
    ds = copy.deepcopy(ds)
    X = ds[1].numpy() if type(ds[1]) == torch.Tensor else ds[1]
    y = ds[2].numpy() if type(ds[2]) == torch.Tensor else ds[2]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=seed)
    df_train = get_df(X_train, y_train)
    df_test = get_df(X_test, y_test)
    df_train.iloc[:, -1] = df_train.iloc[:, -1].astype('category')
    df_test.iloc[:, -1] = df_test.iloc[:, -1].astype('category')
    df_test_old = copy.deepcopy(df_test)
    df_train_old = copy.deepcopy(df_train)
    data_dir = os.environ.get('DATA_DIR', 'data/')
    source = '' if ds[0].startswith('kaggle') else 'openml_'
    path = f'{data_dir}/dataset_descriptions/{source}{ds[0]}.txt'
    try:
        with open(path) as f:
            ds[-1] = f.read()
    except:
        print(f'Using initial description (tried reading {path})')
    return (ds, df_train, df_test, df_train_old, df_test_old)

def load_kaggle():
    cc_test_datasets_multiclass = []
    for name in kaggle_dataset_ids:
        try:
            df_all = pd.read_csv(f'datasets_kaggle/{name[0]}/{name[1]}.csv')
            df_train, df_test = train_test_split(df_all, test_size=0.25, random_state=0)
            ds = ['kaggle_' + name[0], df_all.copy().drop(columns=[name[2]], inplace=False).values, df_all[name[2]].values, [], df_train.copy().drop(columns=[name[2]], inplace=False).columns.tolist() + [name[2]], '']
            data_dir = os.environ.get('DATA_DIR', 'data/')
            path = f'{data_dir}/dataset_descriptions/kaggle_{name[0]}.txt'
            try:
                with open(path) as f:
                    ds[-1] = f.read()
            except:
                print('Using initial description')
            cc_test_datasets_multiclass += [ds]
        except:
            print(f'{name[0]} at datasets_kaggle/{name[0]}/{name[1]}.csv not found, skipping...')
    for name in kaggle_competition_ids:
        try:
            df_all = pd.read_csv(f'datasets_kaggle/{name}/train.csv')
            df_train, df_test = train_test_split(df_all, test_size=0.25, random_state=0)
            ds = ['kaggle_' + name, df_all[df_all.columns[:-1]].values, df_all[df_all.columns[-1]].values, [], df_train.columns.tolist(), '']
            path = f'dataset_descriptions/kaggle_{name}.txt'
            try:
                with open(path) as f:
                    ds[-1] = f.read()
            except:
                print('Using initial description')
            cc_test_datasets_multiclass += [ds]
        except:
            print(f'{name} at datasets_kaggle/{name}/train.csv not found, skipping...')
    return cc_test_datasets_multiclass

def extend_using_caafe(df_train, df_test, ds, seed, prompt_id, code_overwrite=None):
    if code_overwrite:
        code = code_overwrite
    else:
        data_dir = os.environ.get('DATA_DIR', 'data/')
        f = open(f'{data_dir}/generated_code/{ds[0]}_{prompt_id}_{seed}_code.txt', 'r')
        code = f.read()
        f.close()
    df_train = run_llm_code(code, df_train, convert_categorical_to_integer=not ds[0].startswith('kaggle'))
    df_test = run_llm_code(code, df_test, convert_categorical_to_integer=not ds[0].startswith('kaggle'))
    return (df_train, df_test)

