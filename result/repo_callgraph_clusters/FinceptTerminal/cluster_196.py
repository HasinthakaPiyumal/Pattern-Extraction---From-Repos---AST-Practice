# Cluster 196

def create_client(api_key: str) -> FinnhubClient:
    """Factory function to create a Finnhub client"""
    return FinnhubClient(api_key)

