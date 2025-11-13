# Cluster 1

def evaluate_dataset_helper_extend_df(df_train, df_test, ds, prompt_id, seed, code_overwrite=None):
    target_train = df_train[ds[4][-1]]
    target_test = df_test[ds[4][-1]]
    df_train = df_train.drop(columns=[ds[4][-1]])
    df_test = df_test.drop(columns=[ds[4][-1]])
    if prompt_id == 'dfs':
        df_train, df_test = extend_using_dfs(df_train, df_test, target_train)
    elif prompt_id == 'autofeat':
        df_train, df_test = extend_using_autofeat(df_train, df_test, target_train)
    elif prompt_id == 'v4' or prompt_id == 'v3':
        df_train, df_test = extend_using_caafe(df_train, df_test, ds, seed, prompt_id, code_overwrite=code_overwrite)
    elif prompt_id == 'v4+dfs' or prompt_id == 'v3+dfs':
        df_train, df_test = extend_using_caafe(df_train, df_test, ds, seed, prompt_id[0:2])
        df_train, df_test = extend_using_dfs(df_train, df_test, target_train)
    elif prompt_id == 'v4+autofeat' or prompt_id == 'v3+autofeat':
        df_train, df_test = extend_using_caafe(df_train, df_test, ds, seed, prompt_id[0:2])
        df_train, df_test = extend_using_autofeat(df_train, df_test, target_train)
    df_train[ds[4][-1]] = target_train
    df_test[ds[4][-1]] = target_test
    ds[3] = []
    ds[2] = []
    return (ds, df_train, df_test)

class CAAFEClassifier(BaseEstimator, ClassifierMixin):
    """
    A classifier that uses the CAAFE algorithm to generate features and a base classifier to make predictions.

    Parameters:
    base_classifier (object, optional): The base classifier to use. If None, a default TabPFNClassifier will be used. Defaults to None.
    optimization_metric (str, optional): The metric to optimize during feature generation. Can be 'accuracy' or 'auc'. Defaults to 'accuracy'.
    iterations (int, optional): The number of iterations to run the CAAFE algorithm. Defaults to 10.
    llm_model (str, optional): The LLM model to use for generating features. Defaults to 'gpt-3.5-turbo'.
    n_splits (int, optional): The number of cross-validation splits to use during feature generation. Defaults to 10.
    n_repeats (int, optional): The number of times to repeat the cross-validation during feature generation. Defaults to 2.
    """

    def __init__(self, base_classifier: Optional[object]=None, optimization_metric: str='accuracy', iterations: int=10, llm_model: str='gpt-3.5-turbo', n_splits: int=10, n_repeats: int=2) -> None:
        self.base_classifier = base_classifier
        if self.base_classifier is None:
            from tabpfn.scripts.transformer_prediction_interface import TabPFNClassifier
            import torch
            from functools import partial
            self.base_classifier = TabPFNClassifier(N_ensemble_configurations=16, device='cuda' if torch.cuda.is_available() else 'cpu')
            self.base_classifier.fit = partial(self.base_classifier.fit, overwrite_warning=True)
        self.llm_model = llm_model
        self.iterations = iterations
        self.optimization_metric = optimization_metric
        self.n_splits = n_splits
        self.n_repeats = n_repeats

    def fit_pandas(self, df, dataset_description, target_column_name, **kwargs):
        """
        Fit the classifier to a pandas DataFrame.

        Parameters:
        df (pandas.DataFrame): The DataFrame to fit the classifier to.
        dataset_description (str): A description of the dataset.
        target_column_name (str): The name of the target column in the DataFrame.
        **kwargs: Additional keyword arguments to pass to the base classifier's fit method.
        """
        feature_columns = list(df.drop(columns=[target_column_name]).columns)
        X, y = (df.drop(columns=[target_column_name]).values, df[target_column_name].values)
        return self.fit(X, y, dataset_description, feature_columns, target_column_name, **kwargs)

    def fit(self, X, y, dataset_description, feature_names, target_name, disable_caafe=False):
        """
        Fit the model to the training data.

        Parameters:
        -----------
        X : np.ndarray
            The training data features.
        y : np.ndarray
            The training data target values.
        dataset_description : str
            A description of the dataset.
        feature_names : List[str]
            The names of the features in the dataset.
        target_name : str
            The name of the target variable in the dataset.
        disable_caafe : bool, optional
            Whether to disable the CAAFE algorithm, by default False.
        """
        self.dataset_description = dataset_description
        self.feature_names = list(feature_names)
        self.target_name = target_name
        self.X_ = X
        self.y_ = y
        if X.shape[0] > 3000 and self.base_classifier.__class__.__name__ == 'TabPFNClassifier':
            print('WARNING: TabPFN may take a long time to run on large datasets. Consider using alternatives (e.g. RandomForestClassifier)')
        elif X.shape[0] > 10000 and self.base_classifier.__class__.__name__ == 'TabPFNClassifier':
            print('WARNING: CAAFE may take a long time to run on large datasets.')
        ds = ['dataset', X, y, [], self.feature_names + [target_name], {}, dataset_description]
        df_train = pd.DataFrame(X, columns=self.feature_names)
        df_train[target_name] = y
        if disable_caafe:
            self.code = ''
        else:
            self.code, prompt, messages = generate_features(ds, df_train, model=self.llm_model, iterative=self.iterations, metric_used=auc_metric, iterative_method=self.base_classifier, display_method='markdown', n_splits=self.n_splits, n_repeats=self.n_repeats)
        df_train = run_llm_code(self.code, df_train)
        df_train, _, self.mappings = make_datasets_numeric(df_train, df_test=None, target_column=target_name, return_mappings=True)
        df_train, y = split_target_column(df_train, target_name)
        X, y = (df_train.values, y.values.astype(int))
        self.classes_ = unique_labels(y)
        self.base_classifier.fit(X, y)
        return self

    def predict_preprocess(self, X):
        """
        Helper functions for preprocessing the data before making predictions.

        Parameters:
        X (pandas.DataFrame): The DataFrame to make predictions on.

        Returns:
        numpy.ndarray: The preprocessed input data.
        """
        if type(X) != pd.DataFrame:
            X = pd.DataFrame(X, columns=self.X_.columns)
        X, _ = split_target_column(X, self.target_name)
        X = run_llm_code(self.code, X)
        X = make_dataset_numeric(X, mappings=self.mappings)
        X = X.values
        return X

    def predict_proba(self, X):
        X = self.predict_preprocess(X)
        return self.base_classifier.predict_proba(X)

    def predict(self, X):
        X = self.predict_preprocess(X)
        return self.base_classifier.predict(X)

def fit_pandas(self, df, dataset_description, target_column_name, **kwargs):
    """
        Fit the classifier to a pandas DataFrame.

        Parameters:
        df (pandas.DataFrame): The DataFrame to fit the classifier to.
        dataset_description (str): A description of the dataset.
        target_column_name (str): The name of the target column in the DataFrame.
        **kwargs: Additional keyword arguments to pass to the base classifier's fit method.
        """
    feature_columns = list(df.drop(columns=[target_column_name]).columns)
    X, y = (df.drop(columns=[target_column_name]).values, df[target_column_name].values)
    return self.fit(X, y, dataset_description, feature_columns, target_column_name, **kwargs)

def fit(self, X, y, dataset_description, feature_names, target_name, disable_caafe=False):
    """
        Fit the model to the training data.

        Parameters:
        -----------
        X : np.ndarray
            The training data features.
        y : np.ndarray
            The training data target values.
        dataset_description : str
            A description of the dataset.
        feature_names : List[str]
            The names of the features in the dataset.
        target_name : str
            The name of the target variable in the dataset.
        disable_caafe : bool, optional
            Whether to disable the CAAFE algorithm, by default False.
        """
    self.dataset_description = dataset_description
    self.feature_names = list(feature_names)
    self.target_name = target_name
    self.X_ = X
    self.y_ = y
    if X.shape[0] > 3000 and self.base_classifier.__class__.__name__ == 'TabPFNClassifier':
        print('WARNING: TabPFN may take a long time to run on large datasets. Consider using alternatives (e.g. RandomForestClassifier)')
    elif X.shape[0] > 10000 and self.base_classifier.__class__.__name__ == 'TabPFNClassifier':
        print('WARNING: CAAFE may take a long time to run on large datasets.')
    ds = ['dataset', X, y, [], self.feature_names + [target_name], {}, dataset_description]
    df_train = pd.DataFrame(X, columns=self.feature_names)
    df_train[target_name] = y
    if disable_caafe:
        self.code = ''
    else:
        self.code, prompt, messages = generate_features(ds, df_train, model=self.llm_model, iterative=self.iterations, metric_used=auc_metric, iterative_method=self.base_classifier, display_method='markdown', n_splits=self.n_splits, n_repeats=self.n_repeats)
    df_train = run_llm_code(self.code, df_train)
    df_train, _, self.mappings = make_datasets_numeric(df_train, df_test=None, target_column=target_name, return_mappings=True)
    df_train, y = split_target_column(df_train, target_name)
    X, y = (df_train.values, y.values.astype(int))
    self.classes_ = unique_labels(y)
    self.base_classifier.fit(X, y)
    return self

def predict_preprocess(self, X):
    """
        Helper functions for preprocessing the data before making predictions.

        Parameters:
        X (pandas.DataFrame): The DataFrame to make predictions on.

        Returns:
        numpy.ndarray: The preprocessed input data.
        """
    if type(X) != pd.DataFrame:
        X = pd.DataFrame(X, columns=self.X_.columns)
    X, _ = split_target_column(X, self.target_name)
    X = run_llm_code(self.code, X)
    X = make_dataset_numeric(X, mappings=self.mappings)
    X = X.values
    return X

def predict_proba(self, X):
    X = self.predict_preprocess(X)
    return self.base_classifier.predict_proba(X)

def predict(self, X):
    X = self.predict_preprocess(X)
    return self.base_classifier.predict(X)

def evaluate_dataset(df_train: pd.DataFrame, df_test: pd.DataFrame, prompt_id, name, method, metric_used, target_name, max_time=300, seed=0):
    df_train, df_test = (copy.deepcopy(df_train), copy.deepcopy(df_test))
    df_train, _, mappings = make_datasets_numeric(df_train, None, target_name, return_mappings=True)
    df_test = make_dataset_numeric(df_test, mappings=mappings)
    if df_test is not None:
        test_x, test_y = get_X_y(df_test, target_name=target_name)
    x, y = get_X_y(df_train, target_name=target_name)
    feature_names = list(df_train.drop(target_name, axis=1).columns)
    np.random.seed(0)
    if method == 'autogluon' or method == 'autosklearn2':
        if method == 'autogluon':
            from tabpfn.scripts.tabular_baselines import autogluon_metric
            clf = autogluon_metric
        elif method == 'autosklearn2':
            from tabpfn.scripts.tabular_baselines import autosklearn2_metric
            clf = autosklearn2_metric
        metric, ys, res = clf(x, y, test_x, test_y, feature_names, metric_used, max_time=max_time)
    elif type(method) == str:
        if method == 'gp':
            from tabpfn.scripts.tabular_baselines import gp_metric
            clf = gp_metric
        elif method == 'knn':
            from tabpfn.scripts.tabular_baselines import knn_metric
            clf = knn_metric
        elif method == 'xgb':
            from tabpfn.scripts.tabular_baselines import xgb_metric
            clf = xgb_metric
        elif method == 'catboost':
            from tabpfn.scripts.tabular_baselines import catboost_metric
            clf = catboost_metric
        elif method == 'random_forest':
            from tabpfn.scripts.tabular_baselines import random_forest_metric
            clf = random_forest_metric
        elif method == 'logistic':
            from tabpfn.scripts.tabular_baselines import logistic_metric
            clf = logistic_metric
        metric, ys, res = clf(x, y, test_x, test_y, [], metric_used, max_time=max_time, no_tune={})
    elif isinstance(method, BaseEstimator):
        method.fit(X=x, y=y.long())
        ys = method.predict_proba(test_x)
    else:
        metric, ys, res = method(x, y, test_x, test_y, [], metric_used)
    acc = tabpfn.scripts.tabular_metrics.accuracy_metric(test_y, ys)
    roc = tabpfn.scripts.tabular_metrics.auc_metric(test_y, ys)
    method_str = method if type(method) == str else 'transformer'
    return {'acc': float(acc.numpy()), 'roc': float(roc.numpy()), 'prompt': prompt_id, 'seed': seed, 'name': name, 'size': len(df_train), 'method': method_str, 'max_time': max_time, 'feats': x.shape[-1]}

