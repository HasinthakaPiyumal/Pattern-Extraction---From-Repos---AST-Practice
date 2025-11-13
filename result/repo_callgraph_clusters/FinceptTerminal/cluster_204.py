# Cluster 204

class WrapperFactory:
    """Factory for creating provider wrappers"""

    @staticmethod
    def create_imf() -> IMFWrapper:
        return IMFWrapper()

    @staticmethod
    def get_available_providers() -> List[str]:
        return ['imf', 'alpha_vantage']

@staticmethod
def create_imf() -> IMFWrapper:
    return IMFWrapper()

