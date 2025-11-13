# Cluster 6

def refactor_openml_description(description):
    """Refactor the description of an openml dataset to remove the irrelevant parts."""
    splits = re.split('\n', description)
    blacklist = ['Please cite', 'Author', 'Source', 'Author:', 'Source:', 'Please cite:']
    sel = ~np.array([np.array([blacklist_ in splits[i] for blacklist_ in blacklist]).any() for i in range(len(splits))])
    description = str.join('\n', np.array(splits)[sel].tolist())
    splits = re.split('###', description)
    blacklist = ['Relevant Papers']
    sel = ~np.array([np.array([blacklist_ in splits[i] for blacklist_ in blacklist]).any() for i in range(len(splits))])
    description = str.join('\n\n', np.array(splits)[sel].tolist())
    return description

