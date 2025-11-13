# Cluster 34

def is_valid_identifier(key: str) -> bool:
    return key.isidentifier() and (not keyword.iskeyword(key))

