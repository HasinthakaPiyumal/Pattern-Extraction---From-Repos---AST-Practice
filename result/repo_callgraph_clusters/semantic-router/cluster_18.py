# Cluster 18

def add_coloured_handler(logger):
    """Add a coloured handler to the logger."""
    formatter = CustomFormatter()
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger

