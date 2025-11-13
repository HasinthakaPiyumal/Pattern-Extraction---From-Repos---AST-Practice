# Cluster 50

def is_qdrant_available() -> bool:
    try:
        try_to_import_qdrant_client()
        return True
    except ValueError:
        return False

def get_qdrant_client(path: str):
    global _qdrant_client_instance
    if _qdrant_client_instance is None:
        try_to_import_qdrant_client()
        import qdrant_client
        _qdrant_client_instance = qdrant_client.QdrantClient(path=path)
    return _qdrant_client_instance

