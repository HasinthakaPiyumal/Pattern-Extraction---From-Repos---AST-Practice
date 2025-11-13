# Cluster 62

class Query(BaseModule):
    """Represents a retrieval query."""
    query_str: str = Field(description='The query string.')
    top_k: Optional[int] = Field(default=None, description='Number of top results to retrieve.')
    custom_embedding_strs: Optional[List[str]] = Field(default=None, description='The List to store additional strings need to be embed with the query.')
    similarity_cutoff: Optional[float] = Field(default=None, description='Minimum similarity score.')
    keyword_filters: Optional[List[str]] = Field(default=None, description='Keywords to filter results.')
    metadata_filters: Optional[Dict[str, Any]] = Field(default=None, description='Additional metadata filters.')

    @property
    def embedding_strs(self) -> List[str]:
        """Use custom embedding strs if specified, otherwise use query str."""
        if self.custom_embedding_strs is None:
            if len(self.query_str) == 0:
                return []
            return [self.query_str]
        else:
            return self.custom_embedding_strs

    def to_QueryBundle(self):
        return QueryBundle(query_str=self.query_str, custom_embedding_strs=self.custom_embedding_strs)

def to_QueryBundle(self):
    return QueryBundle(query_str=self.query_str, custom_embedding_strs=self.custom_embedding_strs)

