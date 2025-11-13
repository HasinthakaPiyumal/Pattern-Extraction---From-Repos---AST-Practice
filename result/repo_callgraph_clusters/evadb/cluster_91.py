# Cluster 91

class FaissVectorStore(VectorStore):

    def __init__(self, index_name: str, index_path: str) -> None:
        try_to_import_faiss()
        self._index_name = index_name
        self._index_path = index_path
        self._index = None
        import faiss
        self._existing_id_set = set([])
        if self._index is None and os.path.exists(self._index_path):
            self._index = faiss.read_index(self._index_path)
            for i in range(self._index.ntotal):
                self._existing_id_set.add(self._index.id_map.at(i))

    def create(self, vector_dim: int):
        import faiss
        self._index = faiss.IndexIDMap2(faiss.IndexHNSWFlat(vector_dim, 32))

    def add(self, payload: List[FeaturePayload]):
        assert self._index is not None, 'Please create an index before adding features.'
        for row in payload:
            embedding = np.array(row.embedding, dtype='float32')
            if len(embedding.shape) != 2:
                embedding = embedding.reshape(1, -1)
            if row.id not in self._existing_id_set:
                self._index.add_with_ids(embedding, np.array([row.id]))

    def persist(self):
        assert self._index is not None, 'Please create an index before calling persist.'
        import faiss
        faiss.write_index(self._index, self._index_path)

    def query(self, query: VectorIndexQuery) -> VectorIndexQueryResult:
        assert self._index is not None, 'Cannot query as index does not exists.'
        embedding = np.array(query.embedding, dtype='float32')
        if len(embedding.shape) != 2:
            embedding = embedding.reshape(1, -1)
        dists, indices = self._index.search(embedding, query.top_k)
        distances, ids = ([], [])
        for dis, idx in zip(dists[0], indices[0]):
            distances.append(dis)
            ids.append(idx)
        return VectorIndexQueryResult(distances, ids)

    def delete(self):
        index_path = Path(self._index_path)
        if index_path.exists():
            index_path.unlink()

def create(self, vector_dim: int):
    import faiss
    self._index = faiss.IndexIDMap2(faiss.IndexHNSWFlat(vector_dim, 32))

