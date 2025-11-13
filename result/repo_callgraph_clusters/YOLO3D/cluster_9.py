# Cluster 9

def set_logging(name=None, verbose=True):
    for h in logging.root.handlers:
        logging.root.removeHandler(h)
    rank = int(os.getenv('RANK', -1))
    logging.basicConfig(format='%(message)s', level=logging.INFO if verbose and rank in (-1, 0) else logging.WARNING)
    return logging.getLogger(name)

