# Cluster 45

def get_all_synthesizers():
    return {name: globals()[name] for name in __all__}

