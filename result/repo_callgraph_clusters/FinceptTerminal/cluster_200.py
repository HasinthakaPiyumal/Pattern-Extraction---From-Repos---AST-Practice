# Cluster 200

class WrapperFactory:
    """Factory for creating provider wrappers"""

    @staticmethod
    def create_alpha_vantage(api_key: str) -> AlphaVantageWrapper:
        return AlphaVantageWrapper(api_key)

    @staticmethod
    def get_available_providers() -> List[str]:
        return ['alpha_vantage']

@staticmethod
def create_alpha_vantage(api_key: str) -> AlphaVantageWrapper:
    return AlphaVantageWrapper(api_key)

