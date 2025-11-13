# Cluster 41

def inherits_from(child, parent_name):
    if inspect.isclass(child):
        return parent_name in [c.__name__ for c in inspect.getmro(child)[1:]]
    return False

