# Cluster 8

def create_mappings(df_train: pd.DataFrame) -> Dict[str, Dict[int, str]]:
    """
    Creates a dictionary of mappings for categorical columns in the given dataframe.

    Parameters:
    df_train (pandas.DataFrame): The dataframe to create mappings for.

    Returns:
    Dict[str, Dict[int, str]]: A dictionary of mappings for categorical columns in the dataframe.
    """
    mappings = {}
    for col in df_train.columns:
        if df_train[col].dtype.name == 'category' or df_train[col].dtype.name == 'object':
            mappings[col] = {v: i for i, v in enumerate(df_train[col].astype('category').cat.categories)}
    return mappings

def make_datasets_numeric(df_train: pd.DataFrame, df_test: Optional[pd.DataFrame], target_column: str, return_mappings: Optional[bool]=False) -> Tuple[pd.DataFrame, Optional[pd.DataFrame], Optional[Dict[str, Dict[int, str]]]]:
    """
    Converts the categorical columns in the given training and test dataframes to integer values using mappings created from the training dataframe.

    Parameters:
    df_train (pandas.DataFrame): The training dataframe to convert.
    df_test (pandas.DataFrame, optional): The test dataframe to convert. Defaults to None.
    target_column (str): The name of the target column.
    return_mappings (bool, optional): Whether to return the mappings used for the conversion. Defaults to False.

    Returns:
    Tuple[pandas.DataFrame, Optional[pandas.DataFrame], Optional[Dict[str, Dict[int, str]]]]: The converted training dataframe, the converted test dataframe (if it exists), and the mappings used for the conversion (if `return_mappings` is True).
    """
    df_train = copy.deepcopy(df_train)
    df_train = df_train.infer_objects()
    if df_test is not None:
        df_test = copy.deepcopy(df_test)
        df_test = df_test.infer_objects()
    mappings = create_mappings(df_train)
    non_target = [c for c in df_train.columns if c != target_column]
    df_train[non_target] = make_dataset_numeric(df_train[non_target], mappings)
    if df_test is not None:
        df_test[non_target] = make_dataset_numeric(df_test[non_target], mappings)
    if return_mappings:
        return (df_train, df_test, mappings)
    return (df_train, df_test)

def run_llm_code(code: str, df: pd.DataFrame, convert_categorical_to_integer: Optional[bool]=True, fill_na: Optional[bool]=True) -> pd.DataFrame:
    """
    Executes the given code on the given dataframe and returns the resulting dataframe.

    Parameters:
    code (str): The code to execute.
    df (pandas.DataFrame): The dataframe to execute the code on.
    convert_categorical_to_integer (bool, optional): Whether to convert categorical columns to integer values. Defaults to True.
    fill_na (bool, optional): Whether to fill NaN values in object columns with empty strings. Defaults to True.

    Returns:
    pandas.DataFrame: The resulting dataframe after executing the code.
    """
    try:
        loc = {}
        df = copy.deepcopy(df)
        if fill_na and False:
            df.loc[:, df.dtypes == object] = df.loc[:, df.dtypes == object].fillna('')
        if convert_categorical_to_integer and False:
            df = df.apply(convert_categorical_to_integer_f)
        access_scope = {'df': df, 'pd': pd, 'np': np}
        parsed = ast.parse(code)
        check_ast(parsed)
        exec(compile(parsed, filename='<ast>', mode='exec'), access_scope, loc)
        df = copy.deepcopy(df)
    except Exception as e:
        print('Code could not be executed', e)
        raise e
    return df

def get_leave_one_out_importance(df_train, df_test, ds, method, metric_used, max_time=30):
    """Get the importance of each feature for a dataset by dropping it in the training and prediction."""
    res_base = evaluate_dataset(ds, df_train, df_test, prompt_id='', name=ds[0], method=method, metric_used=metric_used, max_time=max_time)
    importances = {}
    for feat_idx, feat in enumerate(set(df_train.columns)):
        if feat == ds[4][-1]:
            continue
        df_train_ = df_train.copy().drop(feat, axis=1)
        df_test_ = df_test.copy().drop(feat, axis=1)
        ds_ = copy.deepcopy(ds)
        res = evaluate_dataset(ds_, df_train_, df_test_, prompt_id='', name=ds[0], method=method, metric_used=metric_used, max_time=max_time)
        importances[feat] = (round(res_base['roc'] - res['roc'], 3),)
    return importances

