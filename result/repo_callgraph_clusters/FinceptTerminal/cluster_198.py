# Cluster 198

def build_dynamic_call(wrapper: AlphaVantageWrapper, data_type: str):
    """Creates a dynamic callable for specific data type"""
    return lambda **kwargs: wrapper.execute_query(data_type, **kwargs)

def build_dynamic_call(wrapper: IMFWrapper, data_type: str):
    """Creates a dynamic callable for specific data type"""
    return lambda **kwargs: wrapper.execute_query(data_type, **kwargs)

