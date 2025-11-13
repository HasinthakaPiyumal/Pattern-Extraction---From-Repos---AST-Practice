# Cluster 202

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

