# Cluster 11

def get_random_seed():
    seed = os.getpid() + int(datetime.now().strftime('%S%f')) + int.from_bytes(os.urandom(2), 'big')
    return seed

