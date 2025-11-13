# Cluster 40

class FaissListTool(Tool):
    """Tool for listing available corpora in the FAISS vector database."""
    name: str = 'faiss_list'
    description: str = 'List all available corpora and their metadata in the FAISS vector database. This tool takes no parameters.'
    inputs: Dict[str, Dict[str, Any]] = {}
    required: Optional[List[str]] = []

    def __init__(self, faiss_database: FaissDatabase=None):
        super().__init__()
        self.faiss_database = faiss_database

    def __call__(self) -> Dict[str, Any]:
        """Execute the list operation."""
        return self.faiss_database.list_corpora()

def __call__(self) -> Dict[str, Any]:
    """Execute the list operation."""
    return self.faiss_database.list_corpora()

