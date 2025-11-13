# Cluster 10

def convert_categorical_to_integer_f(column: pd.Series, mapping: Optional[Dict[int, str]]=None) -> pd.Series:
    """
    Converts a categorical column to integer values using the given mapping.

    Parameters:
    column (pandas.Series): The column to convert.
    mapping (Dict[int, str], optional): The mapping to use for the conversion. Defaults to None.

    Returns:
    pandas.Series: The converted column.
    """
    if mapping is not None:
        if column.dtype.name == 'category':
            column = column.cat.add_categories([-1])
        return column.map(mapping).fillna(-1).astype(int)
    return column

def split_target_column(df: pd.DataFrame, target: Optional[str]) -> Tuple[pd.DataFrame, Optional[pd.Series]]:
    """
    Splits the given dataframe into the feature dataframe and the target column.

    Parameters:
    df (pandas.DataFrame): The dataframe to split.
    target (str, optional): The name of the target column. Defaults to None.

    Returns:
    Tuple[pandas.DataFrame, Optional[pandas.Series]]: The feature dataframe and the target column (if it exists).
    """
    return (df[[c for c in df.columns if c != target]], df[target].astype(int) if target and target in df.columns else None)

def extend_using_autofeat(df_train, df_test, target_train):
    """
    Extends the given training and test dataframes with additional features using autofeat.

    Parameters:
    df_train (pandas.DataFrame): The training dataframe.
    df_test (pandas.DataFrame): The test dataframe.
    target_train (pandas.Series): The target variable for the training dataframe.

    Returns:
    pandas.DataFrame: The new training dataframe with added features.
    pandas.DataFrame: The new test dataframe with added features.
    """
    from autofeat import FeatureSelector, AutoFeatRegressor, AutoFeatClassifier
    from sklearn.preprocessing import OrdinalEncoder
    encoder = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
    for col in df_train.columns:
        if df_train[col].dtype == 'object' or df_train[col].dtype.name == 'category':
            df_train[col] = df_train[col].astype(str)
            df_test[col] = df_test[col].astype(str)
            df_train[col] = encoder.fit_transform(df_train[[col]]).ravel()
            df_test[col] = encoder.transform(df_test[[col]]).ravel()
            df_train[col] = df_train[col].astype(float)
            df_test[col] = df_test[col].astype(float)
    df_train = df_train.fillna(-1)
    df_test = df_test.fillna(-1)
    classifier = AutoFeatClassifier(verbose=1, feateng_steps=1)
    df_train = classifier.fit_transform(df_train, target_train.astype('int'))
    df_test = classifier.transform(df_test)
    return (df_train, df_test)

