# Cluster 83

class MilvusVectorStore(VectorStore):

    def __init__(self, index_name: str, **kwargs) -> None:
        self._milvus_uri = kwargs.get('MILVUS_URI')
        if not self._milvus_uri:
            self._milvus_uri = os.environ.get('MILVUS_URI')
        assert self._milvus_uri, 'Please set your Milvus URI in evadb.yml file (third_party, MILVUS_URI) or environment variable (MILVUS_URI).'
        self._milvus_user = kwargs.get('MILVUS_USER')
        if not self._milvus_user:
            self._milvus_user = os.environ.get('MILVUS_USER', '')
        self._milvus_password = kwargs.get('MILVUS_PASSWORD')
        if not self._milvus_password:
            self._milvus_password = os.environ.get('MILVUS_PASSWORD', '')
        self._milvus_db_name = kwargs.get('MILVUS_DB_NAME')
        if not self._milvus_db_name:
            self._milvus_db_name = os.environ.get('MILVUS_DB_NAME', '')
        self._milvus_token = kwargs.get('MILVUS_TOKEN')
        if not self._milvus_token:
            self._milvus_token = os.environ.get('MILVUS_TOKEN', '')
        self._client = get_milvus_client(milvus_uri=self._milvus_uri, milvus_user=self._milvus_user, milvus_password=self._milvus_password, milvus_db_name=self._milvus_db_name, milvus_token=self._milvus_token)
        self._collection_name = index_name

    def create(self, vector_dim: int):
        if self._collection_name in self._client.list_collections():
            self._client.drop_collection(self._collection_name)
        self._client.create_collection(collection_name=self._collection_name, dimension=vector_dim, metric_type='COSINE')

    def add(self, payload: List[FeaturePayload]):
        milvus_data = [{'id': feature_payload.id, 'vector': feature_payload.embedding.reshape(-1).tolist()} for feature_payload in payload]
        ids = [feature_payload.id for feature_payload in payload]
        self._client.delete(collection_name=self._collection_name, pks=ids)
        self._client.insert(collection_name=self._collection_name, data=milvus_data)

    def persist(self):
        self._client.flush(self._collection_name)

    def delete(self) -> None:
        self._client.drop_collection(collection_name=self._collection_name)

    def query(self, query: VectorIndexQuery) -> VectorIndexQueryResult:
        response = self._client.search(collection_name=self._collection_name, data=[query.embedding.reshape(-1).tolist()], limit=query.top_k)[0]
        distances, ids = ([], [])
        for result in response:
            distances.append(result['distance'])
            ids.append(result['id'])
        return VectorIndexQueryResult(distances, ids)

def create(self, vector_dim: int):
    if self._collection_name in self._client.list_collections():
        self._client.drop_collection(self._collection_name)
    self._client.create_collection(collection_name=self._collection_name, dimension=vector_dim, metric_type='COSINE')

def delete(self) -> None:
    self._client.drop_collection(collection_name=self._collection_name)

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

def create(self, vector_dim: int):
    self._client.create_collection(name=self._collection_name, metadata={'hnsw:construction_ef': vector_dim, 'hnsw:space': 'cosine'})

