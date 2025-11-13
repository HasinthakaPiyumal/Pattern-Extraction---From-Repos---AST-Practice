# Cluster 52

def is_milvus_available() -> bool:
    try:
        try_to_import_milvus_client()
        return True
    except ValueError:
        return False

def get_milvus_client(milvus_uri: str, milvus_user: str, milvus_password: str, milvus_db_name: str, milvus_token: str):
    global _milvus_client_instance
    if _milvus_client_instance is None:
        try_to_import_milvus_client()
        import pymilvus
        _milvus_client_instance = pymilvus.MilvusClient(uri=milvus_uri, user=milvus_user, password=milvus_password, db_name=milvus_db_name, token=milvus_token)
    return _milvus_client_instance

