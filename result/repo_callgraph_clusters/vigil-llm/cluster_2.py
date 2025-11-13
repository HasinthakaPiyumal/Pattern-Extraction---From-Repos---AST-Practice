# Cluster 2

def cosine_similarity(embedding1: List, embedding2: List) -> float:
    """ Get cosine similarity between two embeddings """
    product = np.dot(embedding1, embedding2)
    norm = np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
    return product / norm

