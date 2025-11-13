# Cluster 51

def is_chromadb_available() -> bool:
    try:
        try_to_import_chromadb_client()
        return True
    except ValueError:
        return False

def get_chromadb_client(index_path: str):
    global _chromadb_client_instance
    if _chromadb_client_instance is None:
        try_to_import_chromadb_client()
        import chromadb
        _chromadb_client_instance = chromadb.PersistentClient(path=index_path)
    return _chromadb_client_instance

