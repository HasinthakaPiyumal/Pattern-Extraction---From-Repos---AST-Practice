# Cluster 14

def dynamic_upload_to(instance, filename):
    if instance.storage_type == 'FAISS':
        return upload_to_faiss(instance, filename)
    else:
        return upload_to_pinecone(instance, filename)

