# Cluster 35

class ArxivSearchTool(Tool):
    """Tool for searching papers on arXiv."""
    name: str = 'arxiv_search'
    description: str = 'Search for academic papers on arXiv using queries or paper IDs'
    inputs: Dict[str, Dict[str, str]] = {'search_query': {'type': 'string', 'description': "Search query (e.g., 'all:machine learning', 'cat:cs.AI', 'au:smith')"}, 'id_list': {'type': 'array', 'description': "List of arXiv IDs to retrieve (e.g., ['1706.03762', '1810.04805'])"}, 'max_results': {'type': 'integer', 'description': 'Maximum number of results to return (default: 10)'}, 'start': {'type': 'integer', 'description': 'Starting index for pagination (default: 0)'}}
    required: Optional[List[str]] = []

    def __init__(self, arxiv_base: ArxivBase=None):
        super().__init__()
        self.arxiv_base = arxiv_base

    def __call__(self, search_query: str=None, id_list: list=None, max_results: int=10, start: int=0) -> Dict[str, Any]:
        """
        Search arXiv for papers.
        
        Args:
            search_query: Search query string
            id_list: List of arXiv IDs
            max_results: Maximum results to return
            start: Starting index for pagination
            
        Returns:
            Dictionary with search results
        """
        if not search_query and (not id_list):
            return {'success': False, 'error': 'Either search_query or id_list must be provided'}
        return self.arxiv_base.search_arxiv(search_query=search_query, id_list=id_list, start=start, max_results=max_results)

def __call__(self, search_query: str=None, id_list: list=None, max_results: int=10, start: int=0) -> Dict[str, Any]:
    """
        Search arXiv for papers.
        
        Args:
            search_query: Search query string
            id_list: List of arXiv IDs
            max_results: Maximum results to return
            start: Starting index for pagination
            
        Returns:
            Dictionary with search results
        """
    if not search_query and (not id_list):
        return {'success': False, 'error': 'Either search_query or id_list must be provided'}
    return self.arxiv_base.search_arxiv(search_query=search_query, id_list=id_list, start=start, max_results=max_results)

