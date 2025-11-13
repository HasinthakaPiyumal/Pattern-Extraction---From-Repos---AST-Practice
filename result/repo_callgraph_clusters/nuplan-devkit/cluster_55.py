# Cluster 55

def get_async_s3_session(profile_name: Optional[str]=None, aws_access_key_id: Optional[str]=None, aws_secret_access_key: Optional[str]=None, force_new: bool=False) -> aioboto3.Session:
    """
    Get synchronous boto3 session.
    :param profile_name: Optional profile name to authenticate with.
    :param aws_access_key_id: Optional access key to authenticate with.
    :param aws_secret_access_key: Optional secret access key to authenticate with.
    :param force_new: If true, ignore any cached  session and get a new one.
                      Any existing cached session will be overwritten.
    :return: Session object.
    """
    global G_ASYNC_SESSION
    if not force_new and G_ASYNC_SESSION is not None:
        return G_ASYNC_SESSION

    def _set_async_session_func(session: aioboto3.Session) -> None:
        global G_ASYNC_SESSION
        G_ASYNC_SESSION = session

    def _create_session_func(**kwargs: Any) -> aioboto3.Session:
        return aioboto3.Session(**kwargs)
    return _get_session_internal(profile_name, aws_access_key_id, aws_secret_access_key, _create_session_func, _set_async_session_func)

def _get_sync_session(profile_name: Optional[str]=None, aws_access_key_id: Optional[str]=None, aws_secret_access_key: Optional[str]=None, force_new: bool=False) -> boto3.Session:
    """
    Get synchronous boto3 session.
    :param profile_name: Optional profile name to authenticate with.
    :param aws_access_key_id: Optional access key to authenticate with.
    :param aws_secret_access_key: Optional secret access key to authenticate with.
    :param force_new: If true, ignore any cached session and get a new one.
                      Any existing cached session will be overwritten.
    :return: Session object.
    """
    global G_SYNC_SESSION
    if not force_new and G_SYNC_SESSION is not None:
        return G_SYNC_SESSION

    def _set_sync_session_func(session: boto3.Session) -> None:
        global G_SYNC_SESSION
        G_SYNC_SESSION = session

    def _create_session_func(**kwargs: Any) -> aioboto3.Session:
        return boto3.Session(**kwargs)
    return _get_session_internal(profile_name, aws_access_key_id, aws_secret_access_key, _create_session_func, _set_sync_session_func)

