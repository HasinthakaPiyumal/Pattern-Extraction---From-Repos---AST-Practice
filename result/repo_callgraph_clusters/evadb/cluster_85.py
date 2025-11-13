# Cluster 85

class PineconeVectorStore(VectorStore):

    def __init__(self, index_name: str, **kwargs) -> None:
        try_to_import_pinecone_client()
        global _pinecone_init_done
        self._index_name = index_name.strip().lower()
        self._api_key = kwargs.get('PINECONE_API_KEY')
        if not self._api_key:
            self._api_key = os.environ.get('PINECONE_API_KEY')
        assert self._api_key, 'Please set your `PINECONE_API_KEY` using set command or environment variable (PINECONE_KEY). It can be found at Pinecone Dashboard > API Keys > Value'
        self._environment = kwargs.get('PINECONE_ENV')
        if not self._environment:
            self._environment = os.environ.get('PINECONE_ENV')
        assert self._environment, 'Please set your `PINECONE_ENV` or environment variable (PINECONE_ENV). It can be found Pinecone Dashboard > API Keys > Environment.'
        if not _pinecone_init_done:
            import pinecone
            pinecone.init(api_key=self._api_key, environment=self._environment)
            _pinecone_init_done = True
        self._client = None

    def create(self, vector_dim: int):
        import pinecone
        pinecone.create_index(self._index_name, dimension=vector_dim, metric='cosine')
        logger.warning(f'Created index {self._index_name}. Please note that Pinecone is eventually consistent, hence any additions to the Vector Index may not get immediately reflected in queries.')
        self._client = pinecone.Index(self._index_name)

    def add(self, payload: List[FeaturePayload]):
        self._client.upsert(vectors=[{'id': str(row.id), 'values': row.embedding.reshape(-1).tolist()} for row in payload])

    def delete(self) -> None:
        import pinecone
        pinecone.delete_index(self._index_name)

    def query(self, query: VectorIndexQuery) -> VectorIndexQueryResult:
        import pinecone
        if not self._client:
            self._client = pinecone.Index(self._index_name)
        response = self._client.query(top_k=query.top_k, vector=query.embedding.reshape(-1).tolist())
        distances, ids = ([], [])
        for row in response['matches']:
            distances.append(row['score'])
            ids.append(int(row['id']))
        return VectorIndexQueryResult(distances, ids)

def delete(self) -> None:
    import pinecone
    pinecone.delete_index(self._index_name)

