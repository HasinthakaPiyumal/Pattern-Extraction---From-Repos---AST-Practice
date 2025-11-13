# Cluster 8

def similarity(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio() * 100

