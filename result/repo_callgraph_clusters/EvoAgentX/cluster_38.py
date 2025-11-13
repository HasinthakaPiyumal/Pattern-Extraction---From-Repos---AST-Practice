# Cluster 38

class RSSFetchTool(Tool):
    """Tool for fetching and parsing RSS feeds."""
    name: str = 'rss_fetch'
    description: str = 'Fetch and parse RSS feeds from URLs to get latest articles and updates. Use reasonable limits (10-20 entries) unless you specifically need more for comprehensive analysis.'
    inputs: Dict[str, Dict[str, str]] = {'feed_url': {'type': 'string', 'description': 'URL of the RSS feed to fetch'}, 'max_entries': {'type': 'integer', 'description': 'Maximum number of entries to return. Recommended: 10-20 for most use cases, higher only if comprehensive analysis is needed (default: 10)'}, 'fetch_webpage_content': {'type': 'boolean', 'description': 'Whether to fetch and extract content from article webpages. Note: This significantly increases processing time (default: true)'}}
    required: Optional[List[str]] = ['feed_url']

    def __init__(self, rss_base: RSSBase=None):
        super().__init__()
        self.rss_base = rss_base or RSSBase()

    def __call__(self, feed_url: str, max_entries: int=10, fetch_webpage_content: bool=True) -> Dict[str, Any]:
        """
        Fetch and parse an RSS feed.
        
        Args:
            feed_url: URL of the RSS feed
            max_entries: Maximum number of entries to return (default: 10)
            fetch_webpage_content: Whether to fetch and extract content from article webpages
            
        Returns:
            Dictionary with parsed feed information
        """
        return self.rss_base.fetch_rss_feed(feed_url, max_entries, fetch_webpage_content)

def __call__(self, feed_url: str, max_entries: int=10, fetch_webpage_content: bool=True) -> Dict[str, Any]:
    """
        Fetch and parse an RSS feed.
        
        Args:
            feed_url: URL of the RSS feed
            max_entries: Maximum number of entries to return (default: 10)
            fetch_webpage_content: Whether to fetch and extract content from article webpages
            
        Returns:
            Dictionary with parsed feed information
        """
    return self.rss_base.fetch_rss_feed(feed_url, max_entries, fetch_webpage_content)

