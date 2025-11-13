# Cluster 87

class ChromaDBVectorStore(VectorStore):

    def __init__(self, index_name: str, index_path: str) -> None:
        self._client = get_chromadb_client(index_path)
        self._collection_name = index_name

    def create(self, vector_dim: int):
        self._client.create_collection(name=self._collection_name, metadata={'hnsw:construction_ef': vector_dim, 'hnsw:space': 'cosine'})

    def add(self, payload: List[FeaturePayload]):
        ids = [str(row.id) for row in payload]
        embeddings = [row.embedding.reshape(-1).tolist() for row in payload]
        self._client.get_collection(self._collection_name).add(ids=ids, embeddings=embeddings)

    def delete(self) -> None:
        self._client.delete_collection(name=self._collection_name)

    def query(self, query: VectorIndexQuery) -> VectorIndexQueryResult:
        response = self._client.get_collection(self._collection_name).query(query_embeddings=query.embedding.reshape(-1).tolist(), n_results=query.top_k)
        distances, ids = ([], [])
        if 'ids' in response:
            for id in response['ids'][0]:
                ids.append(int(id))
            for distance in response['distances'][0]:
                distances.append(distance)
        return VectorIndexQueryResult(distances, ids)

def delete(self) -> None:
    self._client.delete_collection(name=self._collection_name)

class QdrantVectorStore(VectorStore):

    def __init__(self, index_name: str, index_db: str) -> None:
        self._client = get_qdrant_client(index_db)
        self._collection_name = index_name

    def create(self, vector_dim: int):
        from qdrant_client.models import Distance, VectorParams
        self._client.recreate_collection(collection_name=self._collection_name, vectors_config=VectorParams(size=vector_dim, distance=Distance.COSINE))

    def add(self, payload: List[FeaturePayload]):
        from qdrant_client.models import Batch
        ids = [int(row.id) for row in payload]
        embeddings = [row.embedding.reshape(-1).tolist() for row in payload]
        self._client.upsert(collection_name=self._collection_name, points=Batch.construct(ids=ids, vectors=embeddings))

    def delete(self) -> None:
        self._client.delete_collection(collection_name=self._collection_name)

    def query(self, query: VectorIndexQuery) -> VectorIndexQueryResult:
        response = self._client.search(collection_name=self._collection_name, query_vector=query.embedding.reshape(-1).tolist(), limit=query.top_k)
        distances, ids = ([], [])
        for point in response:
            distances.append(point.score)
            ids.append(int(point.id))
        return VectorIndexQueryResult(distances, ids)

def delete(self) -> None:
    self._client.delete_collection(collection_name=self._collection_name)

