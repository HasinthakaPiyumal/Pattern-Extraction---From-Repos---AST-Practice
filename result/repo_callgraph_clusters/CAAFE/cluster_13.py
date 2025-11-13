# Cluster 13

def extend_using_dfs(df_train: pd.DataFrame, df_test: pd.DataFrame, target_train: pd.Series) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Extends the given training and test dataframes with additional features using deep feature synthesis.

    Parameters:
    df_train (pandas.DataFrame): The training dataframe.
    df_test (pandas.DataFrame): The test dataframe.
    target_train (pandas.Series): The target variable for the training dataframe.

    Returns:
    Tuple[pandas.DataFrame, pandas.DataFrame]: The new training dataframe with added features and the new test dataframe with added features.
    """
    import featuretools as ft
    es = ft.EntitySet(id='Test')
    es = es.add_dataframe(dataframe_name='data', dataframe=pd.concat([df_train, df_test]), index='index')
    feature_matrix, feature_defs = ft.dfs(entityset=es, target_dataframe_name='data', trans_primitives=['add_numeric', 'multiply_numeric'])
    df_train, df_test = (feature_matrix.iloc[:len(df_train), :].reset_index(drop=True), feature_matrix.iloc[len(df_train):, :].reset_index(drop=True))
    return (df_train, df_test)

